"""Install, verify and remove the RP-11 capture unit as a root-owned system unit (reusable installer; no shipped fragment).

    python -m tools.rp11_capture_unit_install install
    python -m tools.rp11_capture_unit_install verify
    python -m tools.rp11_capture_unit_install remove

This is the capture-unit counterpart of ``tools.executor_supervisor_install`` and keeps its patterns: fixed unit name and
paths (nothing can be redirected by argument or environment), a trust chain verified and never edited, atomic
replacement of a *managed* fragment, a **checked** ``daemon-reload`` whose result is read back from the system manager,
restoration that is proven rather than assumed, and fixed diagnostic words. Exit statuses are the supervisor installer's.

**No production fragment is shipped and no unit policy is invented here.** The fragment is a validation *input*: the
default source ``infra/rp11/rp11-capture-pass-a.service`` does not exist, so the command line refuses with
``source-missing`` until an explicitly reviewed production fragment is added by a maintainer. What this installer does
require of any fragment, because the accepted design fixes it:

* exactly one ``ExecStartPre=`` and it is the approved consume vector
  ``ExecStartPre=+/usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py consume``
  (read back from the manager as ``ExecStartPreEx``: that path, that argv, flag ``privileged``, nothing else);
* exactly one ``ExecStart=`` (its content is not judged here) and a **finite** ``TimeoutStartSec=`` (one positive value;
  ``infinity``, ``0``, an empty value and ``TimeoutSec=`` are refused; the manager must report the same finite value).
  The duration is not chosen here: ``UnitSpec.max_start_timeout_seconds`` may bound it;
* no ``[Install]`` section: the unit is never enabled, it is started only by an authorized operator ``start``;
* every ``UnitSpec.required_directives`` entry (sandbox directives; empty here, supplied by the reviewed production
  fragment's spec) present in ``[Service]`` and never overridden, and every ``UnitSpec.required_properties`` entry
  reported by the manager exactly.

Trust: the RP-11 artifact tree and the interpreter are root-owned and not writable by group or others with no symlink
where none is expected (every directory from ``/``, the whole artifact tree walked with the supervisor installer's
bounded descriptor walk, the interpreter's complete link chain); the repository fragment is a root-owned, link-free,
non-writable file. No system-manager location other than ``/etc/systemd/system`` may hold the unit, a drop-in or a
``.wants``/``.requires`` link for it, and the manager's ``DropInPaths`` must be empty.

``install`` places (or atomically upgrades a recognized, differing) fragment and runs a checked ``daemon-reload`` whose
outcome is verified against the manager (loaded path, no drop-in, nothing pending, exact consume vector, finite timeout,
not enabled). It never starts, stops or enables the unit, and it refuses to change anything while the unit is
``active``/``activating``/``deactivating``/``reloading`` (a capture pass is never disturbed). A failed upgrade restores
the earlier fragment and proves it (bytes, manager load, unit state); a failed *first* installation takes the fragment
back out and proves the manager no longer holds the unit; whatever cannot be confirmed exits ``recovery-incomplete`` (15).
``verify`` checks the installation and the manager's view. ``remove`` unlinks only a recognized (marked) fragment of an
idle unit and reloads the manager; it never touches the account, linger, sudoers, Polkit, the artifact or any evidence.
"""

from __future__ import annotations

import argparse
import math
import os
import re
import stat
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from adapters.systemd.manager import ROLE_ARTIFACT, ROLE_INTERPRETER
from tools.executor_supervisor_install import (
    EXIT_CONFLICT, EXIT_IO, EXIT_OK, EXIT_PENDING, EXIT_RECOVERY, EXIT_REFUSED, EXIT_USAGE, EXIT_VERIFY_FAILED, MAX_BYTES,
    SYSTEM_UNIT_PATHS, UNIT_DIR, Failure, Installer as _SupervisorInstaller, Runner, _Io, _run,
)

__all__ = ["CONSUME_VECTOR", "DEFAULT_SPEC", "Installer", "UnitSpec", "main"]

CURRENT, ABSENT, STALE, FOREIGN = "current", "absent", "stale", "foreign"
IDLE_STATES = frozenset({"inactive", "failed"})
KNOWN_STATES = frozenset({"active", "reloading", "inactive", "failed", "activating", "deactivating", "maintenance", "refreshing"})
#: The only approved consume step: PID 1 runs it as root (``+``) before ``ExecStart=``; nothing else may be an ``ExecStartPre``.
CONSUME_VECTOR = (ROLE_INTERPRETER, "-I", "-S", ROLE_ARTIFACT, "consume")
MARKER = b"# Managed-By: tools.rp11_capture_unit_install\n"
UNIT_NAME = "rp11-capture-pass-a.service"
#: ``UnitFileState`` values of a unit that is neither enabled nor linked (a unit without ``[Install]`` is ``static``).
NOT_ENABLED = frozenset({"static", "disabled"})
LINK_DIRS = (UNIT_DIR, "/run/systemd/system")
_SECONDS = {"us": 1e-6, "usec": 1e-6, "ms": 1e-3, "msec": 1e-3, "": 1.0, "s": 1.0, "sec": 1.0, "second": 1.0, "seconds": 1.0,
            "m": 60.0, "min": 60.0, "minute": 60.0, "minutes": 60.0, "h": 3600.0, "hr": 3600.0, "hour": 3600.0, "hours": 3600.0}
_TIMEOUT = re.compile(r"(\d+(?:\.\d+)?)\s*([a-z]*)")
_SHOWN_SPAN = re.compile(r"(\d+(?:\.\d+)?)(us|ms|s|min|h|d|w)")
_SHOWN_UNITS = {"us": 1e-6, "ms": 1e-3, "s": 1.0, "min": 60.0, "h": 3600.0, "d": 86400.0, "w": 604800.0}


@dataclass(frozen=True)
class UnitSpec:
    """Everything that identifies one capture unit and what a fragment must satisfy: validation inputs, not policy.

    The privileged ``ExecStartPre`` consume vector is deliberately not a field: judging and read-back always use ``CONSUME_VECTOR``.
    """

    unit: str = UNIT_NAME
    source_relative: Path = Path("infra") / "rp11" / UNIT_NAME
    #: ``Key=Value`` lines required in ``[Service]`` (sandbox directives); none are assumed by this installer.
    required_directives: tuple[str, ...] = ()
    #: manager properties that must read back exactly (for example ``User``); none are assumed.
    required_properties: Mapping[str, str] = field(default_factory=dict)
    #: optional upper bound for ``TimeoutStartSec``; the duration itself is never chosen here.
    max_start_timeout_seconds: float | None = None

    def __post_init__(self) -> None:
        bound = self.max_start_timeout_seconds
        if bound is not None and not (math.isfinite(bound) and bound > 0):
            raise ValueError("the optional start-timeout bound must be a finite positive number of seconds")
        if not re.fullmatch(r"[A-Za-z0-9@:_.\\-]+\.service", self.unit) or "/" in self.unit:
            raise ValueError("unit must be a plain service name")
        for item in self.required_directives:
            if "=" not in item or item.split("=", 1)[0].strip() in ("ExecStartPre", "TimeoutStartSec", "ExecStart", "TimeoutSec"):
                raise ValueError("required directives are sandbox settings, not the vector, ExecStart or the timeout")


DEFAULT_SPEC = UnitSpec()


def _timeout_seconds(value: str) -> float | None:
    """One positive, finite duration as a unit file writes it (``90``, ``30s``, ``2min``); anything else is ``None``."""
    match = _TIMEOUT.fullmatch(value.strip().lower())
    if match is None or match[2] not in _SECONDS:
        return None
    try:
        seconds = float(match[1]) * _SECONDS[match[2]]
    except (OverflowError, ValueError):
        return None
    return seconds if math.isfinite(seconds) and seconds > 0 else None


def _shown_seconds(value: str) -> float | None:
    """The manager's printed ``TimeoutStartUSec`` (``1min 30s``); ``infinity``, ``0`` and anything unparsable are ``None``."""
    text = value.strip()
    if not text or text in ("infinity", "0"):
        return None
    total, rest = 0.0, text
    while rest:
        match = _SHOWN_SPAN.match(rest.lstrip())
        if match is None:
            return None
        try:
            total += float(match[1]) * _SHOWN_UNITS[match[2]]
        except (OverflowError, ValueError):
            return None
        if not math.isfinite(total):
            return None
        rest = rest.lstrip()[match.end():]
    return total if math.isfinite(total) and total > 0 else None


class Installer:
    # The generic trust machinery is the supervisor installer's own, taken by name so that nothing supervisor-specific
    # (its unit, account or enablement) can be inherited by accident.
    _p = _SupervisorInstaller._p
    _read_all = _SupervisorInstaller._read_all
    _write_all = _SupervisorInstaller._write_all
    _trusted = _SupervisorInstaller._trusted
    _require = _SupervisorInstaller._require
    _resolve = _SupervisorInstaller._resolve
    _names = _SupervisorInstaller._names
    _walk = _SupervisorInstaller._walk
    _walk_fd = _SupervisorInstaller._walk_fd
    _exists = _SupervisorInstaller._exists

    def __init__(self, repo: Path, *, spec: UnitSpec = DEFAULT_SPEC, root: str = "/", run: Runner = _run,
                 euid: Callable[[], int] = os.geteuid, trusted: tuple[int, int] = (0, 0), io: _Io | None = None) -> None:
        self._repo, self._spec, self._root, self._run, self._euid = repo, spec, root, run, euid
        self._owner, self._group = trusted  # root:root in production; a seam only for tests that cannot be root
        self._io = io or _Io()
        self._account_uid = -1  # there is no service account to distrust: every object must be root's
        self._seconds: float | None = None  # the finite TimeoutStartSec of the fragment this call is working with

    @property
    def _unit(self) -> str:
        return self._spec.unit

    @property
    def _dest(self) -> str:
        return self._p(f"{UNIT_DIR}/{self._unit}")

    # --- the fragment: a validation input, judged here, never invented --------------------------------

    def _source(self) -> bytes:
        path = self._repo / self._spec.source_relative
        self._resolve(os.path.abspath(path), links=False)
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        except OSError:
            raise Failure(EXIT_REFUSED, "source-missing") from None
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES or info.st_nlink != 1:
                raise Failure(EXIT_REFUSED, "source-invalid")
            if info.st_uid != self._owner or info.st_mode & 0o022:
                raise Failure(EXIT_REFUSED, "source-untrusted")
            data = self._read_all(fd, info.st_size, Failure(EXIT_REFUSED, "source-invalid"))
        finally:
            os.close(fd)
        self._seconds = self._judge(data)
        return data

    def _judge(self, data: bytes) -> float:
        """The fragment's own content against the fixed requirements; returns its finite start timeout in seconds."""
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            raise Failure(EXIT_REFUSED, "source-invalid") from None
        if MARKER not in data.splitlines(keepends=True) or "\0" in text:
            raise Failure(EXIT_REFUSED, "source-invalid")
        entries: list[tuple[str, str, str]] = []  # (section, key, value) in file order
        section = ""
        for raw in text.splitlines():
            line = raw.strip()
            if not line or line[0] in "#;":
                continue
            if raw.rstrip().endswith("\\"):
                raise Failure(EXIT_REFUSED, "fragment-continuation")  # a continued line can hide a directive
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1]
                continue
            key, sep, value = line.partition("=")
            if not sep or not section or not key.strip():
                raise Failure(EXIT_REFUSED, "source-invalid")
            entries.append((section, key.strip(), value.strip()))
        if any(name == "Install" for name, *_ in entries) or "[Install]" in (line.strip() for line in text.splitlines()):
            raise Failure(EXIT_REFUSED, "fragment-install-section")
        service = [(key, value) for name, key, value in entries if name == "Service"]
        if any(key in ("ExecStartPre", "ExecStartPreEx") for name, key, _ in entries if name != "Service"):
            raise Failure(EXIT_REFUSED, "fragment-consume-vector")
        pre = [value for key, value in service if key == "ExecStartPre"]
        if pre != ["+" + " ".join(CONSUME_VECTOR)]:
            raise Failure(EXIT_REFUSED, "fragment-consume-vector")
        starts = [value for key, value in service if key == "ExecStart"]
        if len(starts) != 1 or not starts[0]:
            raise Failure(EXIT_REFUSED, "fragment-exec-start")
        if any(key == "TimeoutSec" for key, _ in service):
            raise Failure(EXIT_REFUSED, "fragment-timeout")  # sets the start timeout too: only the explicit directive is accepted
        timeouts = [value for key, value in service if key == "TimeoutStartSec"]
        seconds = _timeout_seconds(timeouts[0]) if len(timeouts) == 1 else None
        if seconds is None or (self._spec.max_start_timeout_seconds is not None and seconds > self._spec.max_start_timeout_seconds):
            raise Failure(EXIT_REFUSED, "fragment-timeout")
        for wanted in self._spec.required_directives:
            key, _, value = wanted.partition("=")
            values = [item for name, item in service if name == key.strip()]
            if not values or any(item != value.strip() for item in values):
                raise Failure(EXIT_REFUSED, "fragment-directive")
        return seconds

    # --- prerequisites: verified, never edited -------------------------------------------------------

    def _artifact_trust(self) -> None:
        """The program PID 1 runs as root: its tree and interpreter must not be changeable by anyone but root."""
        budget = [20_000]
        artifact = self._resolve(self._p(ROLE_ARTIFACT), links=False)
        if not stat.S_ISREG(os.lstat(artifact).st_mode):
            raise Failure(EXIT_REFUSED, "code-untrusted")
        self._walk(os.path.dirname(artifact), budget)
        interpreter = self._resolve(self._p(ROLE_INTERPRETER), links=True)  # every link of the chain, every target, judged
        if not stat.S_ISREG(os.lstat(interpreter).st_mode):
            raise Failure(EXIT_REFUSED, "code-untrusted")

    def _dropin_names(self) -> list[str]:
        stem = self._unit.removesuffix(".service")
        parts = stem.split("-")
        names = [f"{self._unit}.d"] + [f"{'-'.join(parts[:i])}-.service.d" for i in range(len(parts) - 1, 0, -1)]
        return names

    def _shadows(self) -> None:
        """No other system-manager location holds, modifies or links a unit of this name; nothing enables it."""
        shadow_dirs = [path for path in SYSTEM_UNIT_PATHS if path != UNIT_DIR]
        candidates = [f"{d}/{self._unit}" for d in shadow_dirs]
        candidates += [f"{d}/{name}" for d in SYSTEM_UNIT_PATHS for name in self._dropin_names()]
        candidates += [f"{d}/{self._unit}{suffix}" for d in LINK_DIRS for suffix in (".wants", ".requires")]
        if any(self._exists(candidate) for candidate in candidates):
            raise Failure(EXIT_CONFLICT, "shadowed")
        for directory in LINK_DIRS:  # a ``*.wants``/``*.requires`` link anywhere would start a capture pass without an operator
            try:
                names = [n for n in os.listdir(self._p(directory)) if n.endswith((".wants", ".requires"))]
            except FileNotFoundError:
                continue
            except OSError:
                raise Failure(EXIT_REFUSED, "unit-dir") from None
            if any(self._exists(f"{directory}/{name}/{self._unit}") for name in names):
                raise Failure(EXIT_CONFLICT, "enabled-link")

    def _prerequisites(self) -> None:
        if self._euid() != self._owner:
            raise Failure(EXIT_REFUSED, "not-root")
        self._artifact_trust()
        self._shadows()

    # --- the installed fragment ----------------------------------------------------------------------

    def _current(self, expected: bytes) -> tuple[str, bytes]:
        """``(CURRENT | ABSENT | STALE | FOREIGN, bytes)``: identical / missing / marked but different / anything else."""
        try:
            fd = os.open(self._dest, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
        except FileNotFoundError:
            return ABSENT, b""
        except OSError:
            return FOREIGN, b""
        try:
            info = os.fstat(fd)
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != self._owner or info.st_gid != self._group
                    or stat.S_IMODE(info.st_mode) != 0o644 or info.st_nlink != 1 or info.st_size > MAX_BYTES):
                return FOREIGN, b""
            try:
                data = self._read_all(fd, info.st_size, Failure(EXIT_CONFLICT, "destination-conflict"))
            except Failure:
                return FOREIGN, b""
            if data == expected:
                return CURRENT, data
            return (STALE, data) if MARKER in data.splitlines(keepends=True) else (FOREIGN, b"")
        finally:
            os.close(fd)

    def _directory(self) -> int:
        try:
            fd = os.open(self._p(UNIT_DIR), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        except OSError:
            raise Failure(EXIT_REFUSED, "unit-dir") from None
        info = os.fstat(fd)
        if info.st_uid != self._owner or info.st_mode & 0o022:
            os.close(fd)
            raise Failure(EXIT_REFUSED, "unit-dir")
        return fd

    def _place(self, data: bytes, *, replace: bool) -> None:
        """Root-owned ``0644``: a fresh name is linked (fails if it exists), an upgrade is an atomic rename."""
        dfd = self._directory()
        temporary = f".{self._unit}.tmp-{os.getpid()}"
        try:
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o644, dir_fd=dfd)
            try:
                os.fchmod(fd, 0o644)
                self._write_all(fd, data)
                os.fsync(fd)
            finally:
                os.close(fd)
            if replace:
                os.rename(temporary, self._unit, src_dir_fd=dfd, dst_dir_fd=dfd)
            else:
                os.link(temporary, self._unit, src_dir_fd=dfd, dst_dir_fd=dfd, follow_symlinks=False)
            os.fsync(dfd)
        except OSError:
            raise Failure(EXIT_IO, "install-failed") from None
        finally:
            try:
                os.unlink(temporary, dir_fd=dfd)
            except OSError:
                pass
            os.close(dfd)

    def _unlink(self) -> None:
        try:
            os.unlink(self._dest)
        except OSError:
            raise Failure(EXIT_IO, "remove-failed") from None

    # --- the system manager: reload and verify, never assume ----------------------------------------------

    def _pairs(self, *properties: str) -> list[tuple[str, str]]:
        code, out = self._run(["systemctl", "show", self._unit, *(f"-p{name}" for name in properties)])
        if code != 0:
            return []
        return [(k, v) for k, _, v in (line.partition("=") for line in out.splitlines()) if _ == "="]

    def _show(self, *properties: str) -> dict[str, str]:
        return dict(self._pairs(*properties))

    def _consume_read_back(self, pairs: list[tuple[str, str]]) -> bool:
        """``ExecStartPreEx`` is exactly one entry: the approved path and argv, flagged ``privileged`` and nothing else."""
        entries = [value for key, value in pairs if key == "ExecStartPreEx"]
        if len(entries) != 1 or entries[0].count("{") != 1 or entries[0].count("}") != 1:
            return False
        body = entries[0].strip()
        if not (body.startswith("{") and body.endswith("}")):
            return False
        fields = dict(part.strip().split("=", 1) for part in body[1:-1].split(" ; ") if "=" in part)
        vector = CONSUME_VECTOR
        return (fields.get("path") == vector[0] and fields.get("argv[]") == " ".join(vector)
                and fields.get("flags", "").split() == ["privileged"])

    def _loaded(self, *, present: bool, restored: bool = False) -> bool:
        """The manager's own claim: it holds exactly the installed fragment (``present``) or no unit at all.

        ``restored`` (putting an *earlier* marked fragment back) judges where the configuration came from, the consume
        vector and that the start timeout is finite; a fresh fragment is judged on every requirement, including the
        required properties and the exact timeout it declares.
        """
        names = ("LoadState", "FragmentPath", "NeedDaemonReload", "DropInPaths", "UnitFileState", "TimeoutStartUSec",
                 "ExecStartPreEx", *self._spec.required_properties)
        pairs = self._pairs(*names)
        shown = dict(pairs)
        if shown.get("NeedDaemonReload") != "no":
            return False
        if not present:
            return shown.get("LoadState") == "not-found" and not shown.get("FragmentPath")
        shown_seconds = _shown_seconds(shown.get("TimeoutStartUSec", ""))
        if (shown.get("LoadState") != "loaded" or shown.get("FragmentPath") != f"{UNIT_DIR}/{self._unit}"
                or shown.get("DropInPaths") != "" or shown.get("UnitFileState") not in NOT_ENABLED
                or shown_seconds is None or not self._consume_read_back(pairs)):
            return False
        if restored:
            return True
        return (self._seconds is not None and abs(shown_seconds - self._seconds) < 1e-3
                and all(shown.get(key) == value for key, value in self._spec.required_properties.items()))

    def _reload(self, *, present: bool, restored: bool = False) -> None:
        code, _ = self._run(["systemctl", "daemon-reload"])
        if code != 0 or not self._loaded(present=present, restored=restored):
            raise Failure(EXIT_IO, "reload-failed")

    def _observed_state(self) -> str:
        """The manager's successfully observed ``ActiveState``; an unavailable or unrecognized answer is never a value."""
        state = self._show("ActiveState").get("ActiveState")
        if state not in KNOWN_STATES:
            raise Failure(EXIT_IO, "state-unavailable")
        return state

    def _require_idle(self) -> str:
        state = self._observed_state()
        if state not in IDLE_STATES:
            raise Failure(EXIT_PENDING, "capture-active")  # a capture pass (or its start) is never disturbed
        return state

    # --- recovery: proven, or ``recovery-incomplete`` ----------------------------------------------------------

    def _upgrade_intact(self, previous: bytes, *, state: str) -> bool:
        try:
            return (self._current(previous)[0] == CURRENT and self._loaded(present=True, restored=True)
                    and self._observed_state() == state)
        except (Failure, OSError, subprocess.SubprocessError):
            return False

    def _restore_upgrade(self, previous: bytes, *, state: str) -> None:
        """Put the earlier marked fragment back and prove it: bytes, the manager's load, unit state. Anything else is incomplete."""
        try:
            if self._current(previous)[0] != CURRENT:
                if self._current(b"")[0] != STALE:  # marked and root-owned 0644: what this call wrote, nothing foreign
                    raise Failure(EXIT_RECOVERY, "recovery-incomplete")
                self._place(previous, replace=True)
            self._reload(present=True, restored=True)
            if self._current(previous)[0] != CURRENT or self._observed_state() != state or not self._loaded(present=True, restored=True):
                raise Failure(EXIT_RECOVERY, "recovery-incomplete")
        except (Failure, OSError, subprocess.SubprocessError):
            raise Failure(EXIT_RECOVERY, "recovery-incomplete") from None

    def _withdraw_fresh(self) -> None:
        """A first installation that could not be completed: take our marked fragment out again and prove the manager forgot it."""
        try:
            kind = self._current(b"")[0]
            if kind == FOREIGN:
                raise Failure(EXIT_RECOVERY, "recovery-incomplete")
            if kind == STALE:
                self._unlink()
            self._reload(present=False)
            if self._current(b"")[0] != ABSENT or not self._loaded(present=False):
                raise Failure(EXIT_RECOVERY, "recovery-incomplete")
        except (Failure, OSError, subprocess.SubprocessError):
            raise Failure(EXIT_RECOVERY, "recovery-incomplete") from None

    def _recover_removal(self, original: bytes, *, unlinked: bool) -> None:
        """A removal that failed: the recognized fragment goes back (never over something that has appeared) and is proven."""
        try:
            if unlinked:
                self._place(original, replace=False)
            if self._current(original)[0] != CURRENT:
                raise Failure(EXIT_RECOVERY, "recovery-incomplete")
            self._reload(present=True, restored=True)
            if self._current(original)[0] != CURRENT:
                raise Failure(EXIT_RECOVERY, "recovery-incomplete")
        except (Failure, OSError, subprocess.SubprocessError):
            raise Failure(EXIT_RECOVERY, "recovery-incomplete") from None

    # --- operations ---------------------------------------------------------------------------------------

    def install(self) -> str:
        data = self._source()
        self._prerequisites()
        kind, previous = self._current(data)
        if kind == FOREIGN:
            raise Failure(EXIT_CONFLICT, "destination-conflict")
        state = self._observed_state()  # an upgrade can only be put back to a state that was actually observed
        if kind == CURRENT and self._loaded(present=True):
            return "installed"  # idempotent: nothing to write, nothing to reload
        if state not in IDLE_STATES:
            raise Failure(EXIT_PENDING, "capture-active")
        try:
            if kind != CURRENT:
                self._place(data, replace=kind == STALE)
            self._reload(present=True)
        except BaseException as error:
            # Never leave the manager holding something that was not proven: an upgrade goes back to the earlier fragment,
            # a first installation is withdrawn. A restoration that succeeds re-raises the original error.
            try:
                if kind == STALE and not self._upgrade_intact(previous, state=state):
                    self._restore_upgrade(previous, state=state)
                elif kind == ABSENT:
                    self._withdraw_fresh()
            except Failure as failure:  # even an interruption must not hide state that could not be put back
                raise failure from error
            raise
        return "installed"

    def verify(self) -> str:
        data = self._source()
        self._prerequisites()
        if self._current(data)[0] != CURRENT:
            raise Failure(EXIT_VERIFY_FAILED, "not-installed")
        if not self._loaded(present=True):
            raise Failure(EXIT_VERIFY_FAILED, "manager-stale")
        return "installed"

    def remove(self) -> str:
        if self._euid() != self._owner:
            raise Failure(EXIT_REFUSED, "not-root")
        self._shadows()
        kind, previous = self._current(b"")  # recognized by its marker alone: removal needs no repository fragment
        if kind == FOREIGN:
            raise Failure(EXIT_CONFLICT, "destination-conflict")
        self._require_idle()
        if kind == ABSENT:
            if not self._loaded(present=False):
                self._reload(present=False)  # a manager that still holds a unit with no fragment is brought back in line
            return "removed"
        unlinked = False
        try:
            self._unlink()
            unlinked = True
            self._reload(present=False)
        except BaseException as error:
            try:
                self._recover_removal(previous, unlinked=unlinked)
            except Failure as failure:
                if isinstance(error, Exception):
                    raise failure from error
                raise
            raise
        return "removed"


def main(argv: Sequence[str] | None = None, *, installer: Installer | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rp11_capture_unit_install", add_help=False)
    parser.add_argument("action", choices=("install", "verify", "remove"))
    try:
        args = parser.parse_args(list(sys.argv[1:] if argv is None else argv))
    except SystemExit:
        print("rp11-capture-unit usage", file=sys.stderr)
        return EXIT_USAGE
    tool = installer or Installer(Path(__file__).resolve().parents[1])
    try:
        word = {"install": tool.install, "verify": tool.verify, "remove": tool.remove}[args.action]()
    except Failure as failure:
        print(f"rp11-capture-unit {failure.word}", file=sys.stderr)
        return failure.code
    except (OSError, subprocess.SubprocessError):
        print("rp11-capture-unit io-error", file=sys.stderr)
        return EXIT_IO
    print(f"rp11-capture-unit {word}")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
