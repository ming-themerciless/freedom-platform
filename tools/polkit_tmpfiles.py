"""Install, verify and remove the Route 3 Polkit ``tmpfiles.d`` prerequisite.

    python -m tools.polkit_tmpfiles install
    python -m tools.polkit_tmpfiles verify
    python -m tools.polkit_tmpfiles remove

The repository fragment ``infra/tmpfiles.d/freedom-blades-rp11-polkit-rules.conf``
makes ``systemd-tmpfiles-setup`` create ``/run/polkit-1`` and
``/run/polkit-1/rules.d`` (``root:root 0755``) before ``polkit.service`` starts.
polkitd watches only the rules directories that exist when it starts, so the
directory must exist at boot; nothing here (or in the Route 3 role) restarts or
reloads Polkit, and creating the directory on a running host proves nothing about
the running polkitd. ``verify`` therefore reports the boot ordering explicitly.

The destination is the package-owned ``/usr/lib/tmpfiles.d`` layer (Ubuntu's own
``polkit-tmpfiles.conf`` lives there); ``/etc/tmpfiles.d`` is the administrator
override layer and is deliberately not used. No path can be changed by argument
or environment. Installation never overwrites: the new file is written, flushed
and linked into place with ``link(2)``, which fails if the name exists, so the
destination is either absent or complete. Removal unlinks only a destination that
is byte-for-byte and metadata-for-metadata the repository fragment (plus any
same-inode ``.<fragment>.tmp-<pid>`` alias of it), and never
touches ``/run``: the empty runtime directories are returned to their prior state
by the next boot.

Effective configuration. systemd uses a same-named file in ``/etc/tmpfiles.d``,
``/run/tmpfiles.d`` or ``/usr/local/lib/tmpfiles.d`` *instead of* the package file
(a symlink to ``/dev/null`` is the standard way to disable it). These fixed
locations are inspected with ``lstat`` only, never read or followed; any object
there makes ``install`` and ``verify`` fail, and ``remove`` leaves it untouched
and says it still shadows the fragment.

Race-safe deletion. Every mutating action takes a bounded ``flock`` on the
(already validated, root-owned) destination directory, so this tool's invocations
are serialized with no lock file to go stale; the kernel drops it on any exit.
Linux has no conditional unlink, so a deletion first renames the name to a
quarantine name with ``renameat2(RENAME_NOREPLACE)``, then confirms by ``lstat`` that
it is the very inode that was recognized: only then is it unlinked. A different
object is renamed back (no-overwrite) and the action fails with
``destination-changed``; if it cannot be put back it stays under the quarantine
name (``quarantine-retained``) and later runs refuse until an operator resolves it.
Residual window: a *privileged* actor that swaps the quarantine name itself between
the ``lstat`` and the ``unlink`` is not detected; the name is private to one run.

Diagnostics are fixed words; no file content, path from the host or traceback is
printed.
"""

from __future__ import annotations

import argparse
import ctypes
import fcntl
import os
import re
import signal
import stat
import subprocess
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_REFUSED = 10  # source invalid, not root, or unsafe destination directory
EXIT_CONFLICT = 11  # the destination exists and is not the recognized fragment, or is shadowed/changed
EXIT_VERIFY_FAILED = 12
EXIT_IO = 13
EXIT_INTERRUPTED = 130

FRAGMENT_NAME = "freedom-blades-rp11-polkit-rules.conf"
SOURCE_RELATIVE = Path("infra") / "tmpfiles.d" / FRAGMENT_NAME
MAX_FRAGMENT_BYTES = 4096
FRAGMENT_MODE = 0o644
#: (type, path, mode, user, group, age) — the whole content this slice may own.
EXPECTED_ENTRIES = (
    ("d", "/run/polkit-1", "0755", "root", "root", "-"),
    ("d", "/run/polkit-1/rules.d", "0755", "root", "root", "-"),
)
#: Higher-priority same-name locations of the supported host, highest first (tmpfiles.d(5)).
OVERRIDE_DIRS = ("/etc/tmpfiles.d", "/run/tmpfiles.d", "/usr/local/lib/tmpfiles.d")
LOCK_TIMEOUT_S = 5.0
_LOCK_POLL_S = 0.05
RUNTIME_DIRS = ("polkit-1", "polkit-1/rules.d")
RUNTIME_MODE = 0o755
SYSTEMCTL = "/usr/bin/systemctl"
_SHOW_TIMEOUT_S = 10


class Refused(Exception):
    def __init__(self, code: str, exit_code: int) -> None:
        super().__init__(code)
        self.code = code
        self.exit_code = exit_code


@dataclass(frozen=True)
class Config:
    """The few fixed locations. Production uses the defaults; tests build their own."""

    source: Path = Path(__file__).resolve().parent.parent / SOURCE_RELATIVE
    dest_dir: str = "/usr/lib/tmpfiles.d"
    run: str = "/run"
    boot_id_file: str = "/proc/sys/kernel/random/boot_id"
    uid: int = 0
    gid: int = 0
    require_root: bool = True
    override_dirs: tuple[str, ...] = OVERRIDE_DIRS
    lock_timeout_s: float = LOCK_TIMEOUT_S


# ---------------------------------------------------------------------------
# the source fragment
# ---------------------------------------------------------------------------


def parse_fragment(data: bytes) -> tuple[tuple[str, ...], ...]:
    """The entries of a fragment, or ``Refused``: comments and blank lines only
    besides exactly ``EXPECTED_ENTRIES`` in order."""
    if not data or len(data) > MAX_FRAGMENT_BYTES or not data.endswith(b"\n"):
        raise Refused("source-malformed", EXIT_REFUSED)
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError:
        raise Refused("source-malformed", EXIT_REFUSED) from None
    if "\r" in text or "\0" in text or "\t" in text:
        raise Refused("source-malformed", EXIT_REFUSED)
    entries = []
    for line in text.split("\n")[:-1]:
        if not line.strip() or line.startswith("#"):
            continue
        entries.append(tuple(line.split(" ")))
    if tuple(entries) != EXPECTED_ENTRIES:
        raise Refused("source-entries-unexpected", EXIT_REFUSED)
    return tuple(entries)


def load_source(config: Config) -> bytes:
    try:
        fd = os.open(config.source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    except OSError:
        raise Refused("source-unreadable", EXIT_REFUSED) from None
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_FRAGMENT_BYTES:
            raise Refused("source-malformed", EXIT_REFUSED)
        data = os.read(fd, MAX_FRAGMENT_BYTES + 1)
    except OSError:
        raise Refused("source-unreadable", EXIT_REFUSED) from None
    finally:
        os.close(fd)
    parse_fragment(data)
    return data


# ---------------------------------------------------------------------------
# filesystem seam (tests inject short writes and failed flushes here)
# ---------------------------------------------------------------------------


class Fs:
    def open_dir(self, path: str) -> int:
        return os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)

    def lstat_at(self, dir_fd: int, name: str) -> os.stat_result:
        return os.stat(name, dir_fd=dir_fd, follow_symlinks=False)

    def open_read_at(self, dir_fd: int, name: str) -> int:
        return os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=dir_fd)

    def create_at(self, dir_fd: int, name: str) -> int:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
        return os.open(name, flags, 0o600, dir_fd=dir_fd)

    def write(self, fd: int, data: bytes) -> int:
        return os.write(fd, data)

    def fsync(self, fd: int) -> None:
        os.fsync(fd)

    def fchown(self, fd: int, uid: int, gid: int) -> None:
        os.fchown(fd, uid, gid)

    def fchmod(self, fd: int, mode: int) -> None:
        os.fchmod(fd, mode)

    def link_at(self, dir_fd: int, source: str, dest: str) -> None:
        os.link(source, dest, src_dir_fd=dir_fd, dst_dir_fd=dir_fd, follow_symlinks=False)

    def list_names(self, dir_fd: int) -> list[str]:
        return os.listdir(dir_fd)

    def unlink_at(self, dir_fd: int, name: str) -> None:
        os.unlink(name, dir_fd=dir_fd)

    def rename_noreplace(self, dir_fd: int, source: str, dest: str) -> None:
        """``renameat2(RENAME_NOREPLACE)`` inside one directory: atomic, never overwrites."""
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.renameat2(dir_fd, os.fsencode(source), dir_fd, os.fsencode(dest), _RENAME_NOREPLACE) != 0:
            code = ctypes.get_errno()
            raise OSError(code, os.strerror(code))

    def flock_nb(self, dir_fd: int) -> None:
        fcntl.flock(dir_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def close(self, fd: int) -> None:
        os.close(fd)


_RENAME_NOREPLACE = 1


def _close_quietly(fs: Fs, fd: int) -> None:
    try:
        fs.close(fd)
    except OSError:
        pass


def _write_all(fs: Fs, fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        written = fs.write(fd, bytes(view))
        if written <= 0:
            raise OSError("short write")
        view = view[written:]


# ---------------------------------------------------------------------------
# the destination
# ---------------------------------------------------------------------------

ABSENT = "absent"
RECOGNIZED = "recognized"
ALIASED = "aliased"  # recognized bytes/metadata plus exactly attributable temporary hard links
CONFLICT = "conflict"

_TEMP_NAME = re.compile(rf"^\.{re.escape(FRAGMENT_NAME)}\.tmp-[0-9]+$")
_QUARANTINE_NAME = re.compile(rf"^\.{re.escape(FRAGMENT_NAME)}\.del-[0-9]+$")
Ident = tuple[int, int]  # (st_dev, st_ino)


def _aliases(fs: Fs, dir_fd: int, public: os.stat_result) -> list[str]:
    """Installer-pattern temporary names that are the same inode as the public name.

    Only the installer's own ``.<fragment>.tmp-<pid>`` pattern is considered, and only a
    regular file that is the very same inode counts; anything else is left alone."""
    found = []
    for name in fs.list_names(dir_fd):
        if not _TEMP_NAME.match(name):
            continue
        try:
            info = fs.lstat_at(dir_fd, name)
        except OSError:
            continue
        if stat.S_ISREG(info.st_mode) and (info.st_dev, info.st_ino) == (public.st_dev, public.st_ino):
            found.append(name)
    return sorted(found)


def _inspect(fs: Fs, dir_fd: int, config: Config, expected: bytes,
             pin: list[int] | None = None) -> tuple[str, list[str], Ident | None]:
    """``(state, aliases, identity)``. If ``pin`` is given, the recognized file's descriptor is
    appended to it and left open: while it is open the inode number cannot be reused, so
    ``identity`` stays a sound handle for a later deletion. ``RECOGNIZED``: regular, owner, mode, bytes match and one link.
    ``ALIASED``: the same, and every extra hard link is an installer temporary name in this
    directory (``aliases``). Any unexplained extra link is ``CONFLICT``."""
    try:
        before = fs.lstat_at(dir_fd, FRAGMENT_NAME)
    except FileNotFoundError:
        return ABSENT, [], None
    if not stat.S_ISREG(before.st_mode):
        return CONFLICT, [], None
    if (before.st_uid, before.st_gid) != (config.uid, config.gid) or stat.S_IMODE(before.st_mode) != FRAGMENT_MODE:
        return CONFLICT, [], None
    if before.st_size != len(expected):
        return CONFLICT, [], None
    try:
        fd = fs.open_read_at(dir_fd, FRAGMENT_NAME)
    except OSError:
        return CONFLICT, [], None
    keep = False
    try:
        info = os.fstat(fd)
        if (info.st_dev, info.st_ino) != (before.st_dev, before.st_ino):
            return CONFLICT, [], None
        if os.read(fd, len(expected) + 1) != expected:
            return CONFLICT, [], None
        if pin is not None:
            pin.append(fd)
            keep = True
    except OSError:
        return CONFLICT, [], None
    finally:
        if not keep:
            _close_quietly(fs, fd)
    ident = (info.st_dev, info.st_ino)
    if info.st_nlink == 1:
        return RECOGNIZED, [], ident
    try:
        aliases = _aliases(fs, dir_fd, info)
    except OSError:
        return CONFLICT, [], None
    if aliases and len(aliases) == info.st_nlink - 1:
        return ALIASED, aliases, ident
    return CONFLICT, [], None


def _restore(fs: Fs, dir_fd: int, quarantine: str, name: str) -> None:
    try:
        fs.rename_noreplace(dir_fd, quarantine, name)
    except FileNotFoundError:
        return  # nothing left to put back
    except KeyboardInterrupt:
        raise Refused("quarantine-retained", EXIT_INTERRUPTED) from None
    except OSError:
        raise Refused("quarantine-retained", EXIT_IO) from None
    try:
        fs.fsync(dir_fd)
    except KeyboardInterrupt:
        raise Refused("restore-durability-uncertain", EXIT_INTERRUPTED) from None
    except OSError:
        raise Refused("restore-durability-uncertain", EXIT_IO) from None


def _retire(fs: Fs, dir_fd: int, name: str, ident: Ident) -> None:
    """Unlink ``name`` only if it is still the regular file ``ident``.

    Quarantine, confirm, then unlink. Anything other than ``ident`` is put back and
    reported (``destination-changed``); an ordinary I/O failure or an interruption puts
    the object back and re-raises. If it cannot be put back it stays under its
    quarantine name (``quarantine-retained``). Callers hold the directory lock."""
    quarantine = f".{FRAGMENT_NAME}.del-{os.getpid()}"
    fs.rename_noreplace(dir_fd, name, quarantine)  # fails, changing nothing, if it vanished
    try:
        info = fs.lstat_at(dir_fd, quarantine)
        if stat.S_ISREG(info.st_mode) and (info.st_dev, info.st_ino) == ident:
            fs.unlink_at(dir_fd, quarantine)
            return
    except BaseException:
        _restore(fs, dir_fd, quarantine, name)
        raise
    _restore(fs, dir_fd, quarantine, name)
    raise Refused("destination-changed", EXIT_CONFLICT)


def _drop_aliases(fs: Fs, dir_fd: int, aliases: list[str], ident: Ident) -> None:
    for name in aliases:
        _retire(fs, dir_fd, name, ident)
    fs.fsync(dir_fd)


def _lock(fs: Fs, dir_fd: int, config: Config) -> None:
    """Exclusive ``flock`` on the destination directory, waiting at most ``lock_timeout_s``.
    Released when the descriptor is closed, including on a crash."""
    deadline = time.monotonic() + config.lock_timeout_s
    while True:
        try:
            fs.flock_nb(dir_fd)
            return
        except BlockingIOError:
            if time.monotonic() >= deadline:
                raise Refused("lock-busy", EXIT_IO) from None
            time.sleep(_LOCK_POLL_S)
        except OSError:
            raise Refused("lock-failed", EXIT_IO) from None


def _has_quarantine_residue(fs: Fs, dir_fd: int) -> bool:
    return any(_QUARANTINE_NAME.match(name) for name in fs.list_names(dir_fd))


def _shadowed(fs: Fs, config: Config) -> bool:
    """True if any higher-priority layer holds *any* object under the fragment's name, or
    cannot be shown to be free of one. Nothing is read, followed or printed."""
    for path in config.override_dirs:
        try:
            layer_fd = fs.open_dir(path)
        except FileNotFoundError:
            continue
        except OSError:
            return True
        try:
            fs.lstat_at(layer_fd, FRAGMENT_NAME)
        except FileNotFoundError:
            continue
        except OSError:
            return True
        finally:
            _close_quietly(fs, layer_fd)
        return True
    return False


def _ensure_effective(fs: Fs, config: Config) -> None:
    if _shadowed(fs, config):
        raise Refused("override-shadows-fragment", EXIT_CONFLICT)


def _open_dest_dir(fs: Fs, config: Config) -> int:
    if config.require_root and os.geteuid() != 0:
        raise Refused("not-root", EXIT_REFUSED)
    try:
        fd = fs.open_dir(config.dest_dir)
    except OSError:
        raise Refused("destination-directory-unusable", EXIT_REFUSED) from None
    info = os.fstat(fd)
    if (info.st_uid, info.st_gid) != (config.uid, config.gid) or info.st_mode & 0o022:
        _close_quietly(fs, fd)
        raise Refused("destination-directory-unsafe", EXIT_REFUSED)
    return fd


def install(config: Config, fs: Fs | None = None) -> str:
    fs = fs or Fs()
    data = load_source(config)  # validate the repository source before changing the host
    dir_fd = _open_dest_dir(fs, config)
    temp = f".{FRAGMENT_NAME}.tmp-{os.getpid()}"
    temp_ident: Ident | None = None
    pins: list[int] = []  # descriptors keeping the inodes we act on allocated (no number reuse)
    try:
        _lock(fs, dir_fd, config)
        if _has_quarantine_residue(fs, dir_fd):
            raise Refused("quarantine-residue", EXIT_CONFLICT)
        _ensure_effective(fs, config)
        state, aliases, ident = _inspect(fs, dir_fd, config, data, pins)
        if state == RECOGNIZED:
            _ensure_effective(fs, config)
            return "already-installed"
        if state == CONFLICT:
            raise Refused("destination-conflict", EXIT_CONFLICT)
        if state == ALIASED and ident is not None:  # a complete fragment whose temporary name was left behind
            try:
                _drop_aliases(fs, dir_fd, aliases, ident)
            except OSError:
                raise Refused("alias-recovery-failed", EXIT_IO) from None
            if _inspect(fs, dir_fd, config, data)[0] != RECOGNIZED:
                raise Refused("destination-conflict", EXIT_CONFLICT)
            _ensure_effective(fs, config)
            return "alias-recovered"
        cleanup_failed = False
        try:
            fd = fs.create_at(dir_fd, temp)
            pins.append(fd)
            made = os.fstat(fd)
            temp_ident = (made.st_dev, made.st_ino)
            fs.fchown(fd, config.uid, config.gid)
            fs.fchmod(fd, FRAGMENT_MODE)
            _write_all(fs, fd, data)
            fs.fsync(fd)
            fs.link_at(dir_fd, temp, FRAGMENT_NAME)  # fails if the name now exists
        except FileExistsError:
            raise Refused("destination-conflict", EXIT_CONFLICT) from None
        except OSError:
            raise Refused("install-failed", EXIT_IO) from None
        finally:
            if temp_ident is not None:  # only ever the inode this run created
                try:
                    _retire(fs, dir_fd, temp, temp_ident)
                except (OSError, Refused):
                    cleanup_failed = True
        if cleanup_failed:  # reached only after publication: both names are the same inode
            raise Refused("install-cleanup-failed", EXIT_IO)
        try:
            fs.fsync(dir_fd)
        except OSError:
            raise Refused("install-failed", EXIT_IO) from None
        _ensure_effective(fs, config)
        return "installed"
    finally:
        for pinned in pins:
            _close_quietly(fs, pinned)
        _close_quietly(fs, dir_fd)


def remove(config: Config, fs: Fs | None = None) -> str:
    fs = fs or Fs()
    data = load_source(config)
    dir_fd = _open_dest_dir(fs, config)
    pins: list[int] = []
    try:
        _lock(fs, dir_fd, config)
        if _has_quarantine_residue(fs, dir_fd):
            raise Refused("quarantine-residue", EXIT_CONFLICT)
        state, aliases, ident = _inspect(fs, dir_fd, config, data, pins)
        if state == ABSENT:
            return "already-absent"
        if state == CONFLICT or ident is None:
            raise Refused("destination-retained", EXIT_CONFLICT)
        try:
            for name in aliases:  # exactly attributed same-inode temporary names only
                _retire(fs, dir_fd, name, ident)
            _retire(fs, dir_fd, FRAGMENT_NAME, ident)
            fs.fsync(dir_fd)
        except OSError:
            raise Refused("remove-failed", EXIT_IO) from None
        return "removed"
    finally:
        for pinned in pins:
            _close_quietly(fs, pinned)
        _close_quietly(fs, dir_fd)


# ---------------------------------------------------------------------------
# verification
# ---------------------------------------------------------------------------


class SystemdFacts:
    """Read-only unit properties. The only verb is ``show``."""

    def show(self, unit: str, props: Sequence[str]) -> dict[str, str]:
        argv = [SYSTEMCTL, "show", unit, *(f"--property={p}" for p in props)]
        done = subprocess.run(  # noqa: S603 - fixed argv, no shell
            argv, capture_output=True, text=True, timeout=_SHOW_TIMEOUT_S, check=False, env={"LANG": "C"}
        )
        if done.returncode != 0:
            raise OSError("systemctl show failed")
        return dict(line.split("=", 1) for line in done.stdout.splitlines() if "=" in line)


def _runtime_dir_ok(config: Config, relative: str) -> bool:
    try:
        info = os.lstat(f"{config.run}/{relative}")
    except OSError:
        return False
    return (
        stat.S_ISDIR(info.st_mode)
        and (info.st_uid, info.st_gid) == (config.uid, config.gid)
        and stat.S_IMODE(info.st_mode) == RUNTIME_MODE
    )


def _micros(props: dict[str, str], key: str) -> int | None:
    value = props.get(key, "")
    return int(value) if value.isdigit() else None


def verify(config: Config, fs: Fs | None = None, systemd: SystemdFacts | None = None,
           uptime: Callable[[], float] | None = None) -> list[tuple[str, bool]]:
    """Ordered ``(check, passed)`` pairs; the caller fails if any is ``False``."""
    fs = fs or Fs()
    systemd = systemd or SystemdFacts()
    checks: list[tuple[str, bool]] = []
    try:
        data = load_source(config)
        source_ok = True
    except Refused:
        data, source_ok = b"", False
    checks.append(("source", source_ok))

    installed, aliased, mtime, residue_free = False, False, 0.0, False
    try:
        dir_fd = fs.open_dir(config.dest_dir)
    except OSError:
        dir_fd = -1
    if dir_fd >= 0:
        try:
            residue_free = not _has_quarantine_residue(fs, dir_fd)
            state = _inspect(fs, dir_fd, config, data)[0] if source_ok else CONFLICT
            installed, aliased = state == RECOGNIZED, state == ALIASED
            if installed:
                mtime = fs.lstat_at(dir_fd, FRAGMENT_NAME).st_mtime
        except OSError:
            installed = False
        finally:
            _close_quietly(fs, dir_fd)
    checks.append(("fragment", installed))
    checks.append(("fragment-no-temporary-alias", not aliased))
    checks.append(("no-quarantine-residue", residue_free))
    checks.append(("no-higher-priority-override", not _shadowed(fs, config)))

    for relative in RUNTIME_DIRS:
        checks.append((f"runtime-dir {config.run}/{relative}", _runtime_dir_ok(config, relative)))

    try:
        boot_id = Path(config.boot_id_file).read_text(encoding="ascii").strip()
        boot_ok = len(boot_id) == 36
    except (OSError, UnicodeDecodeError):
        boot_ok = False
    checks.append(("boot-id", boot_ok))

    try:
        polkit = systemd.show("polkit.service", ("ActiveState", "MainPID", "ExecMainStartTimestampMonotonic", "After"))
        setup = systemd.show("systemd-tmpfiles-setup.service", ("Result", "ExecMainExitTimestampMonotonic"))
    except (OSError, subprocess.SubprocessError):
        polkit, setup = {}, {}
    active = polkit.get("ActiveState") == "active" and polkit.get("MainPID", "0") not in ("", "0")
    checks.append(("polkit-active", active))
    ordered_declared = "systemd-tmpfiles-setup.service" in polkit.get("After", "").split()
    checks.append(("polkit-ordered-after-tmpfiles-setup", ordered_declared))
    started, finished = _micros(polkit, "ExecMainStartTimestampMonotonic"), _micros(setup, "ExecMainExitTimestampMonotonic")
    ran_first = (
        setup.get("Result") == "success" and started is not None and finished is not None
        and 0 < finished <= started
    )
    checks.append(("tmpfiles-setup-finished-before-polkit-start", ran_first))
    # The fragment must have been on disk before this boot for the boot to have honoured it.
    boot_started = time.time() - (uptime() if uptime else time.clock_gettime(time.CLOCK_BOOTTIME))
    checks.append(("fragment-predates-boot", installed and mtime < boot_started))
    return checks


# ---------------------------------------------------------------------------
# command line
# ---------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None, config: Config | None = None, fs: Fs | None = None,
         systemd: SystemdFacts | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.polkit_tmpfiles")
    parser.add_argument("action", choices=("install", "verify", "remove"))
    args = parser.parse_args(argv)
    config = config or Config()
    if args.action != "verify":
        signal.signal(signal.SIGTERM, signal.default_int_handler)  # unwind through the temp-file cleanup
    try:
        if args.action == "verify":
            results = verify(config, fs, systemd)
            for name, passed in results:
                print(f"{'ok  ' if passed else 'FAIL'} {name}")
            failed = any(not passed for _, passed in results)
            print("verify: FAILED" if failed else "verify: ok")
            return EXIT_VERIFY_FAILED if failed else EXIT_OK
        outcome = install(config, fs) if args.action == "install" else remove(config, fs)
        shadowed = args.action == "remove" and _shadowed(fs or Fs(), config)
    except Refused as refusal:
        print(f"refused: {refusal.code}", file=sys.stderr)
        return refusal.exit_code
    except KeyboardInterrupt:
        print("error: interrupted", file=sys.stderr)
        return EXIT_INTERRUPTED
    except Exception:  # noqa: BLE001 - fixed diagnostic only; never a traceback
        print("error: unexpected-failure", file=sys.stderr)
        return EXIT_IO
    print(f"{args.action}: {outcome}")
    if args.action == "remove" and outcome == "removed":
        print("note: /run/polkit-1 is left in place until the next boot")
    if shadowed:
        print("note: a higher-priority tmpfiles.d object with the same name still shadows the fragment; left untouched")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
