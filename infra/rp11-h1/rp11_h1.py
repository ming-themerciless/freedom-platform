"""RP-11 H-1 role entry point, run by PID 1 as the controlled artifact.

    /usr/bin/python3.14 -I -S <artifact>/rp11_h1.py hold <id> <a2>
    /usr/bin/python3.14 -I -S <artifact>/rp11_h1.py deact <id> <a2> stop-post
    /usr/bin/python3.14 -I -S <artifact>/rp11_h1.py backstop <id> <a2>
    /usr/bin/python3.14 -I -S <artifact>/rp11_h1.py start <id> <a2> <lease-s> <stop-timeout-s>
    /usr/bin/python3.14 -I -S <artifact>/rp11_h1.py stop

These are the only five argument vectors (RT-2, RT-3, RT-4, SA-1 and SA-2); the
systemd adapter builds the three PID-1 vectors, the SA-1 role consumes DI-2 to
create the holder and the SA-2 role, which takes no operand, consumes DI-S. ``-I`` keeps the script directory and the
environment out of ``sys.path``, and ``-S`` skips site initialization, so the
artifact names its one import directory, ``lib/`` beside this file, itself. That
directory holds the Route 3 adapter and its hash-verified D-Bus client
(``infra/rp11-h1/build.py``). It is appended after the standard library so it
can never shadow a stdlib module.

When running as root, before ``lib/`` reaches ``sys.path`` or anything is
imported from the artifact, every object that could supply code to it must be
root-only: each directory from ``/`` down to the artifact, and every directory
and file inside it — the entry point, the application boundary, the adapter,
the role module, jeepney and its distribution metadata — must be a real
directory or regular file (no symlinks, no other types), owned by root and not
writable by group or others. Bytecode is never written, so no ``__pycache__``
is created as a side effect.

This check cannot protect against this file itself having been modified. That is
closed outside it: the adapter refuses to create a unit that runs this file
unless it and every directory above it are root-only (``adapters/systemd/
artifact.py``), and ``build.py`` installs the tree in that state.

First-image controls (H-FI, RH-1 … RH-3) run before anything else when the
file is executed: descriptors 0–2 must be open (else 71); every descriptor ≥ 3
is closed, found by listing ``/proc/self/fd`` rather than up to any limit, and
the closing is verified by a second listing (else 71); every resettable signal disposition is reset and the mask cleared;
``umask`` is ``022`` and the working directory ``/``. The inherited environment
is untrusted: the only fact taken from it, by the unit-started roles, is systemd's
``INVOCATION_ID`` (as provenance, diagnostic only), read from the process's own initial environment,
which must hold it at most once and as 32 lowercase hex digits (else 64); the
environment is then emptied. The ``start`` and ``stop`` roles read no environment variable at
all (H-FI.1). Nothing else here starts a process.

Exit status: 64 malformed arguments or environment selection, 70 import
failure, 71 a closed standard descriptor or a descriptor ≥ 3 not proved closed, 77 unsafe artifact ownership, mode or
type, otherwise the role's own status.
"""

import os
import re
import signal
import stat
import sys

EX_USAGE = 64
EX_SOFTWARE = 70
EX_OSERR = 71
EX_NOPERM = 77

_MAX_ENVIRON = 1 << 20
_OWN_FDS = "/proc/self/fd"
_HEX = frozenset("0123456789abcdef")
_SECONDS = re.compile(r"[1-9][0-9]{0,5}")


def invocation_id_from(environ: bytes):
    """``INVOCATION_ID`` from a NUL-separated environment block.

    ``"absent"`` if not set; ``None`` if set more than once or malformed."""
    values = [
        entry[len(b"INVOCATION_ID=") :]
        for entry in environ.split(b"\0")
        if entry.startswith(b"INVOCATION_ID=")
    ]
    if not values:
        return "absent"
    if len(values) != 1:
        return None
    try:
        value = values[0].decode("ascii")
    except UnicodeDecodeError:
        return None
    if len(value) != 32 or not set(value) <= _HEX:
        return None
    return value


def _initial_environment() -> bytes:
    """The block PID 1 passed to ``execve`` (duplicates included), capped."""
    try:
        fd = os.open("/proc/self/environ", os.O_RDONLY | os.O_CLOEXEC)
    except OSError:
        return b"\0".join(k + b"=" + v for k, v in os.environb.items())
    try:
        chunks, total = [], 0
        while total <= _MAX_ENVIRON:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        return b"".join(chunks)[: _MAX_ENVIRON + 1]
    finally:
        os.close(fd)


def _listed_descriptors():
    # The listing opens one descriptor of its own; it is closed again on return.
    return [int(name) for name in os.listdir(_OWN_FDS)]


def _is_open(fd):
    try:
        os.get_inheritable(fd)  # fcntl(F_GETFD): EBADF once closed
    except OSError:
        return False
    return True


def close_descriptors_from_3():
    """H-FI.3: close every descriptor ≥ 3, whatever its number; ``False`` if not proved.

    The kernel's list of open descriptors is enumerated, so no upper bound is
    assumed: not ``SC_OPEN_MAX``/``RLIMIT_NOFILE`` (which may have been lowered
    below a descriptor that is already open, or raised up to ``fs.nr_open``)
    and not a constant. A second listing must show nothing else open. Without
    the listing nothing is proved (fail closed). Kept here rather than imported
    from ``lib/``: it runs before the artifact tree has been checked.
    """
    try:
        for fd in _listed_descriptors():
            if fd >= 3:
                try:
                    os.close(fd)
                except OSError:
                    pass  # the listing's own descriptor, already closed
        return not [fd for fd in _listed_descriptors() if fd >= 3 and _is_open(fd)]
    except (OSError, ValueError):
        return False


def first_image_controls(reads_environment=True):
    """RH-1 … RH-3. Returns the provenance dict, or an exit status to refuse with.

    ``reads_environment`` is ``False`` for the static ``start`` and ``stop`` roles
    (H-FI.1, SA1.FI.1): they read no environment variable, so no value can select, refuse or
    otherwise affect it. The environment is still emptied.
    """
    for fd in (0, 1, 2):
        try:
            os.fstat(fd)
        except OSError:
            return EX_OSERR
    invocation_id = "absent"
    if reads_environment:
        environ = _initial_environment()
        invocation_id = invocation_id_from(environ) if len(environ) <= _MAX_ENVIRON else None
        if invocation_id is None:
            print("rp11_h1: malformed or duplicate INVOCATION_ID", file=sys.stderr)
            return EX_USAGE
    os.environ.clear()
    if not close_descriptors_from_3():
        print("rp11_h1: inherited descriptors could not be closed", file=sys.stderr)
        return EX_OSERR
    for signum in signal.valid_signals():
        if signum in (signal.SIGKILL, signal.SIGSTOP):
            continue
        try:
            signal.signal(signum, signal.SIG_DFL)
        except (OSError, ValueError, RuntimeError):
            pass  # not resettable from Python (reserved real-time signals)
    signal.pthread_sigmask(signal.SIG_SETMASK, set())
    os.umask(0o022)
    os.chdir("/")
    return {"invocation_id": invocation_id, "parent_pid": os.getppid()}

_WRITABLE_BY_OTHERS = stat.S_IWGRP | stat.S_IWOTH
_MAX_TREE_ENTRIES = 1000  # the real artifact has about 50


def _required_owner():
    """The uid every artifact object must have, or ``None`` when not run as root."""
    return 0 if os.geteuid() == 0 else None


def _object_problem(path, info, owner, directory):
    if stat.S_ISLNK(info.st_mode):
        return f"{path} is a symlink"
    if directory and not stat.S_ISDIR(info.st_mode):
        return f"{path} is not a directory"
    if not directory and not stat.S_ISREG(info.st_mode):
        return f"{path} is not a regular file or directory"
    if info.st_uid not in (0, owner):
        return f"{path}: owner uid {info.st_uid}"
    if info.st_mode & _WRITABLE_BY_OTHERS:
        return f"{path} is group or other writable"
    return None


def _lstat_problem(path, owner, directory):
    try:
        info = os.lstat(path)
    except OSError as exc:
        return f"{path}: {exc.strerror or exc}"
    return _object_problem(path, info, owner, directory)


def _ancestors_problem(directory, owner):
    """Check ``directory`` and every directory above it, nearest first."""
    current = directory
    while True:
        problem = _lstat_problem(current, owner, True)
        if problem:
            return problem
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def _tree_problem(directory, owner):
    """Check every object below ``directory`` without following any symlink."""
    problem = _lstat_problem(os.path.join(directory, "lib"), owner, True)
    if problem:
        return problem
    seen = 0
    pending = [directory]
    while pending:
        current = pending.pop()
        try:
            with os.scandir(current) as entries:
                listed = list(entries)
        except OSError as exc:
            return f"{current}: {exc.strerror or exc}"
        for entry in listed:
            seen += 1
            if seen > _MAX_TREE_ENTRIES:
                return f"more than {_MAX_TREE_ENTRIES} entries"
            try:
                info = entry.stat(follow_symlinks=False)
            except OSError as exc:
                return f"{entry.path}: {exc.strerror or exc}"
            is_dir = stat.S_ISDIR(info.st_mode)
            problem = _object_problem(entry.path, info, owner, is_dir)
            if problem:
                return problem
            if is_dir:
                pending.append(entry.path)
    return None


def parse_role_argv(argv: list[str]) -> tuple[str, str, str, tuple[int, ...]] | None:
    """The accepted role and its validated operands, or ``None``.

    Uses the application boundary's own validators, so the grammar here and in
    the adapter cannot drift apart.
    """
    from application.unit_control import ControlSpecError, validate_activation_id, validate_sha256

    extra = ()
    if len(argv) == 3 and argv[0] in ("hold", "backstop"):
        role = argv[0]
    elif len(argv) == 4 and argv[0] == "deact" and argv[3] == "stop-post":
        role = "stop-post"
    elif argv == ["stop"]:
        return "stop", "", "", ()
    elif len(argv) == 5 and argv[0] == "start" and all(_SECONDS.fullmatch(v) for v in argv[3:]):
        role = "start"
        extra = (int(argv[3]), int(argv[4]))
    else:
        return None
    try:
        activation_id = validate_activation_id(argv[1])
        artifact_sha256 = validate_sha256(argv[2])
        if role == "start":
            from application.rp11.start import validate_start_durations
            from application.unit_control import HolderSpec

            validate_start_durations(*extra)
            HolderSpec(activation_id, artifact_sha256, *extra)
        return role, activation_id, artifact_sha256, extra
    except ControlSpecError:
        return None


def main(argv: list[str], provenance=None) -> int:
    sys.dont_write_bytecode = True
    provenance = provenance or {"invocation_id": "absent", "parent_pid": os.getppid()}
    # abspath, not realpath: a symlink anywhere on the way must be seen, not followed.
    here = os.path.dirname(os.path.abspath(__file__))
    owner = _required_owner()
    if owner is not None:
        problem = _ancestors_problem(here, owner) or _tree_problem(here, owner)
        if problem:
            print(f"rp11_h1: artifact is not root-owned and protected: {problem}", file=sys.stderr)
            return EX_NOPERM
    lib = os.path.join(here, "lib")
    if lib not in sys.path:
        sys.path.append(lib)
    try:
        # Import the whole adapter and its client up front: a missing or broken
        # dependency fails here, before any role starts.
        import adapters.systemd.jeepney_bus  # noqa: F401
        import adapters.systemd.manager  # noqa: F401
        import adapters.systemd.polkit  # noqa: F401
        import adapters.systemd.subject  # noqa: F401
        import adapters.rp11.stop_post  # noqa: F401
        import adapters.rp11.backstop  # noqa: F401
        import adapters.rp11.hold  # noqa: F401
        import adapters.rp11.start  # noqa: F401
        import adapters.rp11.stop  # noqa: F401
        import jeepney
        import rp11_roles
    except ImportError as exc:
        print(f"rp11_h1: import failed: {exc}", file=sys.stderr)
        return EX_SOFTWARE
    parsed = parse_role_argv(argv)
    if parsed is None:
        print("rp11_h1: not an accepted role vector", file=sys.stderr)
        return EX_USAGE
    role, activation_id, artifact_sha256, extra = parsed
    version = ".".join(str(n) for n in sys.version_info[:3])
    print(
        f"rp11_h1: role={role} runtime=ok python={version} "
        f"isolated={sys.flags.isolated} no_site={sys.flags.no_site} "
        f"jeepney={jeepney.__version__}",
        file=sys.stderr,
    )
    return rp11_roles.run(role, activation_id, artifact_sha256, *extra, **provenance)


if __name__ == "__main__":
    # The role is chosen by argv alone, before anything is imported: ``start`` is
    # the roles that must not read the environment are ``start`` and ``stop``.
    _controls = first_image_controls(reads_environment=sys.argv[1:2] not in (["start"], ["stop"]))
    if isinstance(_controls, int):
        sys.exit(_controls)
    sys.exit(main(sys.argv[1:], _controls))
