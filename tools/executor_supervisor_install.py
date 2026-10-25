"""Install, verify and remove the executor supervisor system service (Route 3 executor OC, production package).

    python -m tools.executor_supervisor_install install
    python -m tools.executor_supervisor_install verify
    python -m tools.executor_supervisor_install verify-ready
    python -m tools.executor_supervisor_install remove

The repository unit ``infra/executor/freedom-blades-executor-supervisor.service`` is installed as a **root-owned system
unit** in ``/etc/systemd/system`` and enabled in the **system manager only** (``multi-user.target``). It runs as
``User=freedom-executor``: the process is unprivileged, but its fragment, command, restart behavior and lifecycle belong to
PID 1 and root, so the account cannot shadow, replace, reload or control it through its own user manager. The account's
lingering user manager keeps owning only the separate transient invocation services. Nothing here can be redirected by
argument or environment: the account (``freedom-executor``), every path and every command are fixed.

Privilege is verified, never edited. The account, its group, non-login shell, lingering (so the user manager outlives any
session) and the sudoers entry are provisioned by an administrator; ``install`` refuses unless they are exactly:

* the account exists, is not root, has a non-login shell, an owned home directory and a primary group of the same name;
* ``/var/lib/systemd/linger/<account>`` exists;
* ``sudo -l -U <account>`` lists exactly one command, whose run-as is ``root`` (or ``root : root``) and nothing wider (not
  ``ALL``, another user or group, or a list), whose only tag is ``NOPASSWD``, and which is the fixed SA-2 ``stop`` vector;
* the code the service runs is root-owned and not writable by the account, by group or by others, with no symlink
  where none is expected: every directory from ``/`` to the fixed code root, the ``adapters``/``application`` trees
  (symlinks refused, enumeration bounded *while it happens*), the venv (``pyvenv.cfg``, the interpreter's complete link
  chain and its ``home``, ``site-packages`` and its ``.pth`` files, the whole ``jeepney`` tree) and the repository service
  fragment itself;
* no system-manager unit of the same name shadows the installed one; and
* no preceding user-service candidate is installed (``/etc/systemd/user``): two persistent supervisors would mean two
  ownership stores, so a detected legacy installation is refused (``legacy-user-service``) until the documented cleanup.

``install`` writes (or atomically upgrades a recognized, differing) fragment, enables it and runs a **checked**
``daemon-reload`` of the system manager, verifying that the manager loaded exactly that fragment; a failed reload fails the
installation and an upgrade restores the previous fragment. Restoration is never assumed: the restored bytes, their loading
by the manager, enablement and the unit state are checked, and anything that cannot be restored and confirmed exits
``recovery-incomplete`` (15), never as a restored or removed result; this includes a manager command that times out or cannot run
(enablement is restored in both directions: a unit that was disabled is disabled again) and an enablement that cannot be observed
strictly: only an absent wants link is "disabled", only the expected link is "enabled", and an I/O error, foreign object or
unexpected target refuses before anything changes (``enablement-unavailable``, 13) or, once something changed, is ``recovery-incomplete``. It does not start the service. ``verify`` checks the
installation, and ``verify-ready`` additionally requires the system manager to be running the supervisor as the
account's uid with its socket present and its state directory private. ``remove`` asks the running supervisor to
**drain** (root-only maintenance request): the supervisor closes admission under its own admission lock, for the rest of
its life, and acknowledges only if nothing is recorded, damaged, adopted or loaded as an invocation unit. The drain
connection is held open across the stop; if it is lost, if any check is inconclusive, or if stopping, disabling,
unlinking or reloading fails, removal is refused or reported failed and a persistent owner (the drained one restarted, the
fragment restored) is left behind and verified; if that cannot be confirmed the result is ``recovery-incomplete``. ``remove`` refuses a running or listening supervisor whose fragment is absent (``owner-without-fragment``): the manager's
in-memory copy would not survive a reboot. It then stops and disables the service, unlinks only a recognized fragment and reloads
the manager. It never touches the account, lingering or sudoers. Diagnostics are fixed words.
"""

from __future__ import annotations

import argparse
import errno
import grp
import os
import pwd
import re
import select
import socket
import stat
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from adapters.executor.protocol import (
    DIRECTORY_NAME, DRAIN_EMPTY, DRAIN_PENDING, DRAIN_REQUEST, GREETING, RUNTIME_ROOT, SOCKET_NAME, STATE_ROOT, peer_uid,
)

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_REFUSED = 10  # not root, bad source, or a prerequisite (account, linger, sudoers, code trust) is wrong
EXIT_CONFLICT = 11  # the destination exists and is not the recognized fragment, is shadowed, a legacy user service exists, or a
#                     supervisor runs with no fragment (``owner-without-fragment``)
EXIT_VERIFY_FAILED = 12
EXIT_IO = 13  # a write, a manager operation (enable, stop, disable, daemon-reload) or the fragment replacement failed
EXIT_PENDING = 14  # remove refused: an invocation is owned, or the drain could not be confirmed
EXIT_RECOVERY = 15  # an operation failed AND putting back the earlier fragment/owner could not be completed and verified

ACTIVE_STATES = frozenset({"active", "reloading", "inactive", "failed", "activating", "deactivating", "maintenance", "refreshing"})
ACCOUNT = "freedom-executor"
UNIT = "freedom-blades-executor-supervisor.service"
SOURCE_RELATIVE = Path("infra") / "executor" / UNIT
MAX_BYTES = 8192
UNIT_DIR = "/etc/systemd/system"
WANTS_DIR = "/etc/systemd/system/multi-user.target.wants"
LINGER_DIR = "/var/lib/systemd/linger"
#: Every system-manager load path on the supported host.  The installed fragment occupies ``UNIT_DIR``;
#: a same-named unit anywhere else is a shadow.  Name-specific drop-ins in any path are refused too.
SYSTEM_UNIT_PATHS = (
    "/etc/systemd/system.control", "/run/systemd/system.control", "/run/systemd/transient",
    "/run/systemd/generator.early", UNIT_DIR, "/etc/systemd/system.attached", "/run/systemd/system",
    "/run/systemd/system.attached", "/run/systemd/generator", "/usr/local/lib/systemd/system",
    "/usr/lib/systemd/system", "/run/systemd/generator.late",
)
SHADOWS = tuple(path for path in SYSTEM_UNIT_PATHS if path != UNIT_DIR)
#: A unit's drop-ins live in ``<name>.d`` and in every dash-truncated prefix directory (``freedom-blades-.service.d``).
DROPIN_NAMES = (f"{UNIT}.d", "freedom-blades-executor-.service.d", "freedom-blades-.service.d", "freedom-.service.d")
DROPIN_DIRS = SYSTEM_UNIT_PATHS
#: What the preceding (never accepted, never deployed) user-service candidate left in the global user configuration.
LEGACY_USER = ("/etc/systemd/user", "/etc/systemd/user/default.target.wants")
#: Present in every fragment this installer writes: the only thing that lets a *differing* root-owned fragment be upgraded.
MARKER = b"# Managed-By: tools.executor_supervisor_install\n"
CODE_ROOT = "/opt/freedom-blades/platform"
CODE_TREES = ("adapters", "application")
VENV = "/opt/freedom-blades/runtime/venv-web"
INTERPRETER = f"{VENV}/bin/python"
DEPENDENCY_TREES = ("jeepney",)  # imported from site-packages by the supervisor; walked in full
MAX_WALK = 20_000
MAX_LINKS = 16
MAX_DEPTH = 32
DRAIN_SECONDS = 30.0
NOLOGIN = ("/usr/sbin/nologin", "/sbin/nologin", "/bin/false", "/usr/bin/false")
SA2 = "/usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py stop"
#: One line of ``sudo -l``: ``(<run-as>) <TAG>: ... <command>``. Only the run-as and tags are judged here; the command is
#: compared byte for byte afterwards.
_SUDO_RULE = re.compile(r"\((?P<runas>[^()]*)\)\s+(?P<tags>(?:[A-Za-z_]+:\s+)*)(?P<cmd>\S.*)")
#: The only run-as the documented rule has: root as the user, root (the default) as the group. ``ALL``, a list, another
#: user or group, ``#uid`` and ``%group`` selections are all wider and refuse.
_SUDO_RUNAS = ("root", "root : root")
_SUDO_TAGS = ("NOPASSWD",)
STATE_NAME = DIRECTORY_NAME

Runner = Callable[[Sequence[str]], "tuple[int, str]"]
CURRENT, ABSENT, STALE, FOREIGN = "current", "absent", "stale", "foreign"


SAFE_PATH = "/usr/sbin:/usr/bin:/sbin:/bin"  # root's helpers are found here and nowhere else: the caller's PATH is never consulted


def _run(argv: Sequence[str]) -> tuple[int, str]:
    executable = next((f"{d}/{argv[0]}" for d in SAFE_PATH.split(":") if os.access(f"{d}/{argv[0]}", os.X_OK)), None)
    if executable is None:
        raise FileNotFoundError(argv[0])
    done = subprocess.run([executable, *argv[1:]], capture_output=True, text=True, timeout=60, check=False,
                          env={"PATH": SAFE_PATH, "LANG": "C"})
    return done.returncode, done.stdout


class Failure(Exception):
    def __init__(self, code: int, word: str) -> None:
        super().__init__(word)
        self.code, self.word = code, word


class SupervisorAbsent(Exception):
    """Nothing listens on the supervisor socket (absent, or refusing connections)."""


class DrainSession:
    """One root-to-supervisor maintenance connection. Held open until ``close`` so that its loss is observable."""

    def __init__(self, path: str, uid: int, *, seconds: float = DRAIN_SECONDS) -> None:
        self._conn: socket.socket | None = None
        try:
            info = os.lstat(path)
        except (FileNotFoundError, NotADirectoryError):
            raise SupervisorAbsent from None
        except OSError:
            raise Failure(EXIT_PENDING, "drain-unconfirmed") from None
        if not stat.S_ISSOCK(info.st_mode) or info.st_uid != uid:
            raise Failure(EXIT_PENDING, "drain-unconfirmed")
        conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        conn.settimeout(seconds)
        try:
            conn.connect(path)
        except OSError as error:
            conn.close()
            if error.errno in (errno.ENOENT, errno.ECONNREFUSED):
                raise SupervisorAbsent from None
            raise Failure(EXIT_PENDING, "drain-unconfirmed") from None
        self._conn = conn
        try:
            if peer_uid(conn) != uid or _read_exact(conn, len(GREETING)) != GREETING:
                raise Failure(EXIT_PENDING, "drain-unconfirmed")
        except OSError:
            self.close()
            raise Failure(EXIT_PENDING, "drain-unconfirmed") from None
        except BaseException:
            self.close()
            raise

    def request(self) -> bool:
        """``True`` only for the exact ``drain empty`` answer; ``False`` for ``drain pending``; anything else fails closed."""
        assert self._conn is not None
        try:
            self._conn.sendall(DRAIN_REQUEST)
            answer = _read_exact(self._conn, max(len(DRAIN_EMPTY), len(DRAIN_PENDING)), until=b"\n")
        except OSError:
            raise Failure(EXIT_PENDING, "drain-unconfirmed") from None
        if answer == DRAIN_EMPTY:
            return True
        if answer == DRAIN_PENDING:
            return False
        raise Failure(EXIT_PENDING, "drain-unconfirmed")

    def alive(self) -> bool:
        if self._conn is None:
            return False
        try:
            if not select.select([self._conn], [], [], 0)[0]:
                return True
            return self._conn.recv(1, socket.MSG_PEEK) != b""
        except OSError:
            return False

    def close(self) -> None:
        conn, self._conn = self._conn, None
        if conn is not None:
            conn.close()


def _read_exact(conn: socket.socket, limit: int, *, until: bytes | None = None) -> bytes:
    data = b""
    while len(data) < limit:
        chunk = conn.recv(1 if until else limit - len(data))
        if not chunk:
            break
        data += chunk
        if until and data.endswith(until):
            break
    return data


class _Io:
    """The reads and writes whose short or failed completion must be survivable; a seam for failure injection."""

    def read(self, fd: int, size: int) -> bytes:
        return os.read(fd, size)

    def write(self, fd: int, data: bytes) -> int:
        return os.write(fd, data)


class Installer:
    def __init__(self, repo: Path, *, root: str = "/", run: Runner = _run, euid: Callable[[], int] = os.geteuid,
                 getpwnam=pwd.getpwnam, getgrnam=grp.getgrnam, trusted: tuple[int, int] = (0, 0), io: _Io | None = None,
                 drain: Callable[[str, int], DrainSession] = DrainSession) -> None:
        self._repo, self._root, self._run, self._euid, self._pw, self._gr = repo, root, run, euid, getpwnam, getgrnam
        self._owner, self._group = trusted  # root:root in production; a seam only for tests that cannot be root
        self._io, self._drain = io or _Io(), drain
        self._account_uid = -1

    # --- fixed paths (re-rooted only by tests) ---------------------------------

    def _p(self, absolute: str) -> str:
        return os.path.join(self._root, absolute.lstrip("/")) if self._root != "/" else absolute

    @property
    def _dest(self) -> str:
        return self._p(f"{UNIT_DIR}/{UNIT}")

    # --- complete reads and writes -------------------------------------------------

    def _read_all(self, fd: int, size: int, failure: Failure) -> bytes:
        """Exactly ``size`` bytes then EOF; a short read, a growing file or an error is a refusal."""
        data = b""
        try:
            while len(data) < size:
                chunk = self._io.read(fd, size - len(data))
                if not chunk:
                    raise failure
                data += chunk
            if self._io.read(fd, 1):
                raise failure
        except OSError:
            raise failure from None
        return data

    def _write_all(self, fd: int, data: bytes) -> None:
        view = memoryview(data)
        while view:
            written = self._io.write(fd, bytes(view))
            if written <= 0:
                raise OSError(errno.EIO, "short write made no progress")
            view = view[written:]

    # --- trust: owner, type and write modes of every traversed object ---------------

    def _trusted(self, info: os.stat_result) -> bool:
        """Owned by the trusted owner (never the account) and not writable by group or others. A link has no mode of its own."""
        if info.st_uid != self._owner or info.st_uid == self._account_uid:
            return False
        return stat.S_ISLNK(info.st_mode) or not info.st_mode & 0o022

    def _require(self, info: os.stat_result, word: str = "code-writable") -> None:
        if not self._trusted(info):
            raise Failure(EXIT_REFUSED, word)

    def _resolve(self, path: str, *, links: bool) -> str:
        """The real path of ``path`` with every traversed directory, link and target judged; escapes and loops refuse.

        ``links=False`` refuses any link at all. ``..`` is only followed lexically inside a link target, from a
        directory that has itself been resolved (so it is a real parent, never a link).
        """
        base = os.path.normpath(self._p("/"))
        relative = os.path.relpath(path, base)
        if relative == ".." or relative.startswith("../"):
            raise Failure(EXIT_REFUSED, "code-untrusted")
        try:
            self._require(os.lstat(base))
        except OSError:
            raise Failure(EXIT_REFUSED, "code-missing") from None
        current, pending, followed = base, [part for part in relative.split("/") if part not in ("", ".")], 0
        while pending:
            name = pending.pop(0)
            if name == "..":
                if current == base:
                    raise Failure(EXIT_REFUSED, "code-untrusted")
                current = os.path.dirname(current)
                continue
            if name == ".":
                continue
            candidate = os.path.join(current, name)
            try:
                info = os.lstat(candidate)
            except OSError:
                raise Failure(EXIT_REFUSED, "code-missing") from None
            self._require(info)
            if stat.S_ISLNK(info.st_mode):
                followed += 1
                if not links or followed > MAX_LINKS:
                    raise Failure(EXIT_REFUSED, "code-symlink")
                try:
                    target = os.readlink(candidate)
                except OSError:
                    raise Failure(EXIT_REFUSED, "code-missing") from None
                if target.startswith("/"):
                    current = base  # an absolute target is absolute within the (possibly re-rooted) filesystem
                pending = [part for part in target.split("/") if part not in ("", ".")] + pending
                continue
            if pending and not stat.S_ISDIR(info.st_mode):
                raise Failure(EXIT_REFUSED, "code-untrusted")
            current = candidate
        return current

    def _names(self, source: int | str, budget: list[int]) -> list[str]:
        """The entry names of one directory, drawn from the iterator one at a time against the shared ``budget``.

        The entry that exceeds the budget is the last one ever drawn (``code-too-large``): nothing is materialized,
        sorted or sampled past the bound, so the retained list is never longer than the budget that was left.
        """
        names: list[str] = []
        try:
            with os.scandir(source) as entries:
                for entry in entries:
                    budget[0] -= 1
                    if budget[0] < 0:
                        raise Failure(EXIT_REFUSED, "code-too-large")
                    names.append(entry.name)
        except OSError:
            raise Failure(EXIT_REFUSED, "code-missing") from None
        return names

    def _walk(self, directory: str, budget: list[int]) -> None:
        """A bounded, descriptor-based walk that follows nothing: every entry must be a trusted directory or file."""
        try:
            dfd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        except OSError:
            raise Failure(EXIT_REFUSED, "code-symlink") from None
        try:
            self._walk_fd(dfd, budget, 0)
        finally:
            os.close(dfd)

    def _walk_fd(self, dfd: int, budget: list[int], depth: int) -> None:
        if depth > MAX_DEPTH:
            raise Failure(EXIT_REFUSED, "code-too-large")
        self._require(os.fstat(dfd))
        for name in self._names(dfd, budget):
            try:
                info = os.stat(name, dir_fd=dfd, follow_symlinks=False)
            except OSError:
                raise Failure(EXIT_REFUSED, "code-missing") from None
            if stat.S_ISLNK(info.st_mode):
                raise Failure(EXIT_REFUSED, "code-symlink")
            self._require(info)
            if stat.S_ISDIR(info.st_mode):
                try:
                    child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=dfd)
                except OSError:
                    raise Failure(EXIT_REFUSED, "code-symlink") from None
                try:
                    opened = os.fstat(child)
                    if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
                        raise Failure(EXIT_REFUSED, "code-untrusted")
                    self._walk_fd(child, budget, depth + 1)
                finally:
                    os.close(child)
            elif not stat.S_ISREG(info.st_mode):
                raise Failure(EXIT_REFUSED, "code-untrusted")

    def _code_trust(self, entry) -> None:
        """Nothing the service imports or executes may be changed by the account (or by group/others)."""
        self._account_uid = entry.pw_uid
        budget = [MAX_WALK]  # one budget for every enumeration below: the trees, the interpreter's siblings, site-packages
        root = self._resolve(self._p(CODE_ROOT), links=True)
        for tree in CODE_TREES:
            self._walk(self._resolve(os.path.join(root, tree), links=False), budget)
        venv = self._resolve(self._p(VENV), links=True)
        config = self._resolve(os.path.join(venv, "pyvenv.cfg"), links=False)
        self._interpreter(venv, config, budget)
        site = self._site_packages(venv, budget)
        names = sorted(self._names(site, budget))  # bounded already: sorting never sees more than the budget allowed
        for name in names:  # the directory's own entries (``.pth`` files run at start-up); never a link
            try:
                self._require(os.lstat(os.path.join(site, name)))
            except OSError:
                raise Failure(EXIT_REFUSED, "code-missing") from None
            if os.path.islink(os.path.join(site, name)):
                raise Failure(EXIT_REFUSED, "code-symlink")
        for name in DEPENDENCY_TREES:
            if name not in names:
                raise Failure(EXIT_REFUSED, "code-missing")
            self._walk(self._resolve(os.path.join(site, name), links=False), budget)

    def _interpreter(self, venv: str, config: str, budget: list[int]) -> None:
        self._resolve(os.path.join(venv, "bin", "python"), links=True)  # the complete link chain, every target judged
        home = None
        try:
            fd = os.open(config, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        except OSError:
            raise Failure(EXIT_REFUSED, "code-missing") from None
        try:
            info = os.fstat(fd)
            self._require(info)
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES:
                raise Failure(EXIT_REFUSED, "code-untrusted")
            text = self._read_all(fd, info.st_size, Failure(EXIT_REFUSED, "code-untrusted")).decode("utf-8", "replace")
        finally:
            os.close(fd)
        for line in text.splitlines():
            key, _, value = line.partition("=")
            if key.strip() == "home":
                home = value.strip()
        if not home or not home.startswith("/"):
            raise Failure(EXIT_REFUSED, "code-untrusted")
        resolved = self._resolve(self._p(home) if self._root != "/" else home, links=True)
        libraries = os.path.join(os.path.dirname(resolved), "lib")  # the standard library the interpreter imports from
        try:
            siblings = self._names(libraries, budget)
        except Failure as failure:
            if failure.word != "code-missing":
                raise
            siblings = []
        for name in sorted(item for item in siblings if item.startswith("python3")):
            self._resolve(os.path.join(libraries, name), links=True)

    def _site_packages(self, venv: str, budget: list[int]) -> str:
        lib = self._resolve(os.path.join(venv, "lib"), links=False)
        versions = sorted(name for name in self._names(lib, budget) if name.startswith("python3"))
        if len(versions) != 1:
            raise Failure(EXIT_REFUSED, "code-missing")
        return self._resolve(os.path.join(lib, versions[0], "site-packages"), links=False)

    # --- the repository fragment ------------------------------------------------------

    def _source(self) -> bytes:
        """The repository's service fragment, taken only from a root-owned, non-writable, link-free path."""
        path = self._repo / SOURCE_RELATIVE
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
        if b"ExecStart=" not in data or data.count(b"\n") < 3 or MARKER not in data.splitlines(keepends=True):
            raise Failure(EXIT_REFUSED, "source-invalid")
        return data

    # --- prerequisites: verified, never edited -----------------------------------

    def _account(self):
        try:
            entry = self._pw(ACCOUNT)
        except KeyError:
            raise Failure(EXIT_REFUSED, "account-missing") from None
        if entry.pw_uid == 0 or entry.pw_shell not in NOLOGIN:
            raise Failure(EXIT_REFUSED, "account-unsuitable")
        try:  # the unit's ``Group=`` is the account's own primary group, by name
            if self._gr(ACCOUNT).gr_gid != entry.pw_gid:
                raise Failure(EXIT_REFUSED, "account-unsuitable")
        except KeyError:
            raise Failure(EXIT_REFUSED, "account-unsuitable") from None
        try:
            home = os.lstat(self._p(entry.pw_dir))
        except OSError:
            raise Failure(EXIT_REFUSED, "account-home") from None
        if not stat.S_ISDIR(home.st_mode) or home.st_uid != entry.pw_uid:
            raise Failure(EXIT_REFUSED, "account-home")
        self._account_uid = entry.pw_uid
        return entry

    def _linger(self) -> None:
        try:
            info = os.lstat(self._p(f"{LINGER_DIR}/{ACCOUNT}"))
        except OSError:
            raise Failure(EXIT_REFUSED, "linger-off") from None
        if not stat.S_ISREG(info.st_mode):
            raise Failure(EXIT_REFUSED, "linger-off")

    def _sudoers(self) -> None:
        code, out = self._run(["sudo", "-n", "-l", "-U", ACCOUNT])
        if code != 0:
            raise Failure(EXIT_REFUSED, "sudoers-unreadable")
        commands = []
        in_list = False
        for line in out.splitlines():
            if "may run the following commands" in line:
                in_list = True
            elif in_list and line.strip():
                commands.append(line.strip())
        if len(commands) != 1:
            raise Failure(EXIT_REFUSED, "sudoers-not-exact")
        match = _SUDO_RULE.fullmatch(commands[0])
        if match is None or match["cmd"].strip() != SA2:
            raise Failure(EXIT_REFUSED, "sudoers-not-exact")
        runas = re.sub(r"\s*:\s*", " : ", match["runas"].strip())
        tags = tuple(tag.rstrip(":") for tag in match["tags"].split())
        if runas not in _SUDO_RUNAS or tags != _SUDO_TAGS:
            raise Failure(EXIT_REFUSED, "sudoers-not-exact")

    def _exists(self, path: str) -> bool:
        try:
            os.lstat(self._p(path))
        except FileNotFoundError:
            return False
        return True

    def _shadows(self) -> None:
        """No other system-manager location may hold (or modify) a unit of the installed name."""
        candidates = [f"{d}/{UNIT}" for d in SHADOWS] + [f"{d}/{name}" for d in DROPIN_DIRS for name in DROPIN_NAMES]
        candidates += [f"{UNIT_DIR}/{UNIT}.wants", f"{UNIT_DIR}/{UNIT}.requires", f"/run/systemd/system/{UNIT}.wants"]
        if any(self._exists(candidate) for candidate in candidates):
            raise Failure(EXIT_CONFLICT, "shadowed")

    def _legacy(self) -> None:
        """The inactive user-service candidate: never beside the system service (two stores would mean two owners)."""
        if any(self._exists(f"{directory}/{UNIT}{suffix}") for directory in LEGACY_USER for suffix in ("", ".d", ".wants")):
            raise Failure(EXIT_CONFLICT, "legacy-user-service")

    def _prerequisites(self):
        if self._euid() != self._owner:
            raise Failure(EXIT_REFUSED, "not-root")
        entry = self._account()
        self._linger()
        self._sudoers()
        self._code_trust(entry)
        self._legacy()
        self._shadows()
        return entry

    # --- the installed fragment ---------------------------------------------------

    def _current(self, expected: bytes) -> tuple[str, bytes]:
        """``(CURRENT | ABSENT | STALE | FOREIGN, bytes)``.

        ``CURRENT``: identical root-owned 0644 regular file. ``STALE``: the same kind of file, carrying this installer's
        marker but different bytes (an earlier revision: upgradable, with its bytes kept for restoration). ``FOREIGN``:
        anything else is there, and is never touched.
        """
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

    def _enabled(self) -> bool:
        try:
            return os.readlink(self._p(f"{WANTS_DIR}/{UNIT}")) in (f"{UNIT_DIR}/{UNIT}", f"../{UNIT}")
        except OSError:
            return False

    def _observed_enabled(self) -> bool:
        """Enablement as *observed*: only a genuinely absent link is disabled, only the expected link is enabled.

        An I/O or permission error, a non-link object, a malformed link or an unexpected target is never ``False``: it
        raises, so an unknown enablement can be neither recorded, compared nor "restored" as though it were disabled.
        (``_enabled`` stays the lenient existence check of the verification and removal paths.)
        """
        try:
            target = os.readlink(self._p(f"{WANTS_DIR}/{UNIT}"))
        except FileNotFoundError:
            return False
        except OSError:
            raise Failure(EXIT_IO, "enablement-unavailable") from None
        if target in (f"{UNIT_DIR}/{UNIT}", f"../{UNIT}"):
            return True
        raise Failure(EXIT_IO, "enablement-unavailable")

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
        """Write the fragment root-owned ``0644``: a fresh name is linked (fails if it exists), an upgrade is an atomic rename."""
        dfd = self._directory()
        temporary = f".{UNIT}.tmp-{os.getpid()}"
        try:
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o644, dir_fd=dfd)
            try:
                os.fchmod(fd, 0o644)
                self._write_all(fd, data)
                os.fsync(fd)
            finally:
                os.close(fd)
            if replace:
                os.rename(temporary, UNIT, src_dir_fd=dfd, dst_dir_fd=dfd)
            else:
                os.link(temporary, UNIT, src_dir_fd=dfd, dst_dir_fd=dfd, follow_symlinks=False)
            os.fsync(dfd)
        except OSError:
            raise Failure(EXIT_IO, "install-failed") from None
        finally:
            try:
                os.unlink(temporary, dir_fd=dfd)
            except OSError:
                pass
            os.close(dfd)

    # --- the system manager: reload and verify, never assume ------------------------------

    def _show(self, *properties: str) -> dict[str, str]:
        code, out = self._run(["systemctl", "show", UNIT, *(f"-p{name}" for name in properties)])
        if code != 0:
            return {}
        return dict(line.split("=", 1) for line in out.splitlines() if "=" in line)

    def _loaded(self, *, present: bool, restored: bool = False) -> bool:
        """The system manager's own claim: it has loaded exactly the installed fragment (``present``) or no unit at all.

        ``restored`` is for putting an *earlier* fragment back: it may legitimately carry a different ``Environment=`` than this
        revision, so only where the configuration came from is judged (path, no drop-in, nothing pending) and that it runs as
        the dedicated account; a freshly installed fragment is judged on everything.
        """
        shown = self._show("LoadState", "FragmentPath", "NeedDaemonReload", "DropInPaths", "User", "Group", "Environment")
        if shown.get("NeedDaemonReload") != "no":
            return False
        if present:
            return (
                shown.get("LoadState") == "loaded"
                and shown.get("FragmentPath") == f"{UNIT_DIR}/{UNIT}"
                and shown.get("DropInPaths") == ""
                and shown.get("User") == ACCOUNT
                and shown.get("Group") == ACCOUNT
                and (restored or shown.get("Environment") == "PATH=/usr/bin:/bin")
            )
        return shown.get("LoadState") == "not-found" and not shown.get("FragmentPath")

    def _reload(self, *, present: bool, restored: bool = False) -> None:
        """``daemon-reload`` of the system manager, and proof that it took: a failure never counts as success."""
        code, _ = self._run(["systemctl", "daemon-reload"])
        if code != 0 or not self._loaded(present=present, restored=restored):
            raise Failure(EXIT_IO, "reload-failed")

    def _state(self) -> str:
        return self._show("ActiveState").get("ActiveState", "")

    def _observed_state(self) -> str:
        """The manager's own, successfully observed ``ActiveState``; an unavailable or unrecognized answer is never a value.

        A non-zero result, a missing or empty property, or a word the manager does not define raises, so two failed
        observations can never compare equal to each other or to a real state.
        """
        shown = self._show("ActiveState")
        state = shown.get("ActiveState")
        if state not in ACTIVE_STATES:
            raise Failure(EXIT_IO, "state-unavailable")
        return state

    def _owner_running(self) -> bool:
        shown = self._show("ActiveState", "MainPID")
        return shown.get("ActiveState") == "active" and shown.get("MainPID", "").isdigit() and int(shown["MainPID"]) > 0

    def _upgrade_intact(self, previous: bytes, *, enabled: bool, state: str) -> bool:
        """The earlier fragment, loaded as before, with enablement and unit state as before. Any doubt is ``False``."""
        try:
            return (self._current(previous)[0] == CURRENT and self._loaded(present=True, restored=True)
                    and self._observed_enabled() == enabled and self._observed_state() == state)
        except (Failure, OSError, subprocess.SubprocessError):
            return False

    def _restore_upgrade(self, previous: bytes, *, enabled: bool, state: str) -> None:
        """Put the earlier fragment back and prove it: bytes on disk, loaded by the manager, enablement and unit state as before.

        Enablement is restored in both directions: a unit that was disabled before the attempt is disabled again, one that was
        enabled is enabled again, and the resulting link is checked. Only this installer's own marked fragment is ever
        replaced (a foreign object is left alone); any step that fails, raises or cannot be confirmed is
        ``recovery-incomplete``, never a restoration.
        """
        try:
            if self._current(previous)[0] != CURRENT:
                if self._current(b"")[0] != STALE:  # marked and root-owned 0644: the fragment this call wrote, nothing foreign
                    raise Failure(EXIT_RECOVERY, "recovery-incomplete")
                self._place(previous, replace=True)
            self._reload(present=True, restored=True)
            if self._observed_enabled() != enabled:
                code, _ = self._run(["systemctl", "enable" if enabled else "disable", UNIT])
                if code != 0:  # the manager's own verdict counts as well as the link it left behind
                    raise Failure(EXIT_RECOVERY, "recovery-incomplete")
            if (self._current(previous)[0] != CURRENT or self._observed_enabled() != enabled or self._observed_state() != state
                    or not self._loaded(present=True, restored=True)):
                raise Failure(EXIT_RECOVERY, "recovery-incomplete")
        except (Failure, OSError, subprocess.SubprocessError):
            raise Failure(EXIT_RECOVERY, "recovery-incomplete") from None

    def install(self) -> str:
        data = self._source()
        self._prerequisites()
        kind, previous = self._current(data)
        if kind == FOREIGN:
            raise Failure(EXIT_CONFLICT, "destination-conflict")
        # An upgrade can only be put back to a state that was actually observed: refuse before touching anything otherwise.
        enabled = self._observed_enabled()
        state = self._observed_state() if kind == STALE else ""
        try:
            if kind != CURRENT:
                self._place(data, replace=kind == STALE)
            if not self._observed_enabled():
                code, _ = self._run(["systemctl", "enable", UNIT])
                if code != 0 or not self._observed_enabled():
                    raise Failure(EXIT_IO, "enable-failed")
            self._reload(present=True)
        except BaseException as error:
            # An upgrade that could not be completed (a typed failure, a manager timeout or OS error, or an interruption)
            # leaves the earlier, working fragment loaded, enabled and running as before, or says it could not.  A restoration
            # that succeeds re-raises the original error, whatever it was: nothing here claims a safe state it did not prove.
            if kind == STALE and not self._upgrade_intact(previous, enabled=enabled, state=state):
                try:
                    self._restore_upgrade(previous, enabled=enabled, state=state)
                except Failure as failure:  # even an interruption must not hide state that could not be put back
                    raise failure from error
            raise
        return "installed"

    def verify(self, *, ready: bool = False) -> str:
        data = self._source()
        entry = self._prerequisites()
        if self._current(data)[0] != CURRENT:
            raise Failure(EXIT_VERIFY_FAILED, "not-installed")
        if not self._enabled():
            raise Failure(EXIT_VERIFY_FAILED, "not-enabled")
        if not self._loaded(present=True):
            raise Failure(EXIT_VERIFY_FAILED, "manager-stale")
        if not ready:
            return "installed"
        self._ready(entry)
        return "ready"

    def _as_account(self, entry, *argv: str) -> tuple[int, str]:
        """The account's own user manager: the only thing it is asked about is the transient invocation units."""
        runtime = f"/run/user/{entry.pw_uid}"
        return self._run(["runuser", "-u", ACCOUNT, "--", "env", f"XDG_RUNTIME_DIR={runtime}",
                          f"DBUS_SESSION_BUS_ADDRESS=unix:path={runtime}/bus", *argv])

    def _ready(self, entry) -> None:
        code, out = self._run(["systemctl", "show", f"user@{entry.pw_uid}.service", "-pActiveState", "--value"])
        if code != 0 or out.strip() != "active":
            raise Failure(EXIT_VERIFY_FAILED, "manager-not-running")
        shown = self._show("ActiveState", "MainPID")
        if shown.get("ActiveState") != "active" or not shown.get("MainPID", "").isdigit() or int(shown["MainPID"]) == 0:
            raise Failure(EXIT_VERIFY_FAILED, "supervisor-not-ready")
        try:
            process = os.lstat(self._p(f"/proc/{int(shown['MainPID'])}"))
            sock = os.lstat(self._p(f"{RUNTIME_ROOT}/{SOCKET_NAME}"))
            state = os.lstat(self._p(f"{STATE_ROOT}/invocations"))
        except OSError:
            raise Failure(EXIT_VERIFY_FAILED, "supervisor-not-ready") from None
        if process.st_uid != entry.pw_uid:  # the one persistent supervisor is the dedicated, unprivileged account's process
            raise Failure(EXIT_VERIFY_FAILED, "supervisor-not-ready")
        if not stat.S_ISSOCK(sock.st_mode) or sock.st_uid != entry.pw_uid:
            raise Failure(EXIT_VERIFY_FAILED, "supervisor-not-ready")
        if not stat.S_ISDIR(state.st_mode) or state.st_uid != entry.pw_uid or stat.S_IMODE(state.st_mode) != 0o700:
            raise Failure(EXIT_VERIFY_FAILED, "state-untrusted")

    # --- removal: only through the supervisor's drain -----------------------------------

    def _manager_active(self, entry) -> bool:
        code, out = self._run(["systemctl", "show", f"user@{entry.pw_uid}.service", "-pActiveState", "--value"])
        state = out.strip()
        if code != 0 or state not in ("active", "inactive"):
            raise Failure(EXIT_PENDING, "drain-unconfirmed")
        return state == "active"

    def _require_empty(self, entry, *, manager: bool) -> None:
        """The installer's own view, taken only while admission is closed: no record, no entry, no loaded invocation unit."""
        state = self._p(f"{STATE_ROOT}/invocations")
        try:
            if os.listdir(state):
                raise Failure(EXIT_PENDING, "invocation-pending")
        except FileNotFoundError:
            pass
        except OSError:
            raise Failure(EXIT_PENDING, "invocation-pending") from None
        if not manager:
            return  # no user manager runs, so no transient unit can exist
        code, out = self._as_account(entry, "systemctl", "--user", "list-units", "--all", "--plain", "--no-legend",
                                     "freedom-executor-stop-*")
        if code != 0 or out.strip():
            raise Failure(EXIT_PENDING, "invocation-pending")

    def _drained(self, entry) -> DrainSession | None:
        """The held drain session once the supervisor affirms emptiness; ``None`` when no supervisor can be admitting."""
        try:
            session = self._drain(self._p(f"{RUNTIME_ROOT}/{SOCKET_NAME}"), entry.pw_uid)
        except SupervisorAbsent:
            if self._state() != "inactive":  # a unit that is starting, restarting or whose state is unknown, may admit
                raise Failure(EXIT_PENDING, "drain-unconfirmed") from None
            return None
        try:
            if not session.request():
                raise Failure(EXIT_PENDING, "invocation-pending")
        except BaseException:
            session.close()
            if not self._restart():  # whatever the supervisor made of the request, it must not stay drained
                raise Failure(EXIT_RECOVERY, "recovery-incomplete") from None
            raise
        return session

    def _restart(self) -> bool:
        """Restart the unit; ``True`` only when the manager then reports it running with a main process."""
        try:
            self._run(["systemctl", "reset-failed", UNIT])  # repeated refusals must not trip the start-rate limit
            self._run(["systemctl", "restart", UNIT])
            return self._owner_running()
        except (OSError, subprocess.SubprocessError):
            return False  # a manager that cannot be asked has not restarted anything

    def _recover(self, original: bytes | None, *, unlinked: bool, drained: bool) -> None:
        """Leave a persistent owner behind and prove it, or say that this could not be done (``recovery-incomplete``).

        The fragment goes back (when it was unlinked) without replacing anything that has appeared in its place, is enabled,
        is loaded by the manager exactly as installed, and the unit runs again. ``original`` is ``None`` when there was no
        fragment to begin with: no persistent owner can be re-established from that state, so nothing is claimed. A supervisor
        that was nevertheless drained or stopped is restarted if possible, but the result is always ``recovery-incomplete``:
        a running copy the manager merely holds in memory would not survive a reboot.
        """
        if original is None:
            if drained:
                self._restart()
                raise Failure(EXIT_RECOVERY, "recovery-incomplete")
            return
        try:
            if unlinked:
                self._place(original, replace=False)
            if self._current(original)[0] != CURRENT:
                raise Failure(EXIT_RECOVERY, "recovery-incomplete")
            if not self._enabled():
                self._run(["systemctl", "enable", UNIT])
            self._reload(present=True, restored=True)
            if not self._enabled() or not self._restart() or self._current(original)[0] != CURRENT:
                raise Failure(EXIT_RECOVERY, "recovery-incomplete")
        except (Failure, OSError, subprocess.SubprocessError):
            raise Failure(EXIT_RECOVERY, "recovery-incomplete") from None

    def _refuse_unowned(self, entry) -> None:
        """No fragment is installed: a supervisor still running or listening is owned only by the manager's memory.

        Draining and stopping it would lose an owner that no fragment or enablement would bring back, so the removal is refused
        before anything changes. The operator response is ``install`` (which restores the fragment and enablement without
        touching the running supervisor) and then ``remove``.
        """
        state = self._show("ActiveState").get("ActiveState")
        if state is None:
            raise Failure(EXIT_PENDING, "drain-unconfirmed")
        if state != "inactive":
            raise Failure(EXIT_CONFLICT, "owner-without-fragment")
        try:
            probe = self._drain(self._p(f"{RUNTIME_ROOT}/{SOCKET_NAME}"), entry.pw_uid)
        except SupervisorAbsent:
            return
        probe.close()  # connected, greeted, never asked to drain
        raise Failure(EXIT_CONFLICT, "owner-without-fragment")

    def remove(self) -> str:
        data = self._source()
        if self._euid() != self._owner:
            raise Failure(EXIT_REFUSED, "not-root")
        entry = self._account()
        kind, previous = self._current(data)
        if kind == FOREIGN:
            raise Failure(EXIT_CONFLICT, "destination-conflict")
        manager = self._manager_active(entry)
        if kind == ABSENT:
            self._refuse_unowned(entry)
        session = self._drained(entry)
        stopped, unlinked = False, False
        try:
            self._require_empty(entry, manager=manager)
            if session is not None and not session.alive():
                raise Failure(EXIT_PENDING, "drain-lost")
            stopped = True
            self._run(["systemctl", "stop", UNIT])  # "not loaded" (already removed) is a non-zero exit too
            if self._state() != "inactive":  # the claim is the manager's own ActiveState, not an exit code
                raise Failure(EXIT_IO, "stop-failed")
            self._require_empty(entry, manager=manager)  # nothing appeared across the stop (a restarted supervisor included)
            if self._enabled():
                self._run(["systemctl", "disable", UNIT])
                if self._enabled():
                    raise Failure(EXIT_IO, "disable-failed")
            if kind != ABSENT:
                try:
                    os.unlink(self._dest)
                except OSError:
                    raise Failure(EXIT_IO, "remove-failed") from None
                unlinked = True
            self._reload(present=False)
        except BaseException as error:
            if stopped or session is not None:  # a drained supervisor refuses stops until restarted: leave it recoverable
                try:
                    self._recover(previous if kind != ABSENT else None, unlinked=unlinked, drained=session is not None)
                except Failure as failure:
                    if isinstance(error, Exception):
                        raise failure from error
                    raise
            raise
        finally:
            if session is not None:
                session.close()
        return "removed"


def main(argv: Sequence[str] | None = None, *, installer: Installer | None = None) -> int:
    parser = argparse.ArgumentParser(prog="executor_supervisor_install", add_help=False)
    parser.add_argument("action", choices=("install", "verify", "verify-ready", "remove"))
    try:
        args = parser.parse_args(list(sys.argv[1:] if argv is None else argv))
    except SystemExit:
        print("executor-supervisor usage", file=sys.stderr)
        return EXIT_USAGE
    tool = installer or Installer(Path(__file__).resolve().parents[1])
    try:
        word = {"install": tool.install, "verify": tool.verify, "verify-ready": lambda: tool.verify(ready=True),
                "remove": tool.remove}[args.action]()
    except Failure as failure:
        print(f"executor-supervisor {failure.word}", file=sys.stderr)
        return failure.code
    except (OSError, subprocess.SubprocessError):
        print("executor-supervisor io-error", file=sys.stderr)
        return EXIT_IO
    print(f"executor-supervisor {word}")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
