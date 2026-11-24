"""RP-11 Pass A capture entry (``rp11_entry.py run --pass A``): G8 composition staged, run path unavailable.

    /usr/bin/python3.14 -I -S <artifact>/rp11_entry.py run --pass A

This is the module-loading substrate the accepted G12 decision calls for, plus the
one reviewed G8 composition site. It lives beside ``rp11_h1.py`` in the one SA-2
artifact and loads from the same root-owned ``lib/``, by the same rules
(``rp11_h1.py`` docstring):

* ``-I -S`` leaves only the standard library on ``sys.path``: no script
  directory, no working directory, no ``PYTHONPATH``, no site, no ``.pth``.
* The inherited environment is untrusted. The one fact taken from it is systemd's
  ``INVOCATION_ID``, read from the process's initial environment, which must hold
  it exactly once as 32 lowercase hex digits (else 64); the environment is then
  emptied. Nothing else is read.
* Before ``lib/`` reaches ``sys.path`` or anything is imported from the artifact,
  every directory from ``/`` to the artifact and every object inside it must be a
  real directory or regular file, **owned by root**, not group or other
  writable (else 77). Unlike ``rp11_h1.py`` this is checked **whatever the
  caller's uid**: the entry runs as a non-root service identity, and an
  unchecked tree would be code that identity could replace.
* ``lib/`` is **appended** after the standard library, so it cannot shadow a
  stdlib module; no bytecode is written; the imports happen once, up front, and
  every artifact module must be loaded from ``lib/`` (else 70).

The dependency closure is the fixed ``ENTRY_SOURCES`` of ``build.py``; a test
computes the closure of this file by AST and keeps the two equal.

**G8 composition staged; the run path is unavailable.** ``build_pass_a_session`` is
the one reviewed arming/session construction site: given a ``GenesisRequest`` it
returns ``create_capture_session`` over ``PosixCaptureFilesystem``,
``StreamCaptureLauncher(armed=True)`` and ``SystemUtcClock`` (and the mechanism's
default read-only verifier). It is **not reachable** from ``main`` or ``entry``:
nothing calls it, ``run_pass_a`` is neither imported by name nor called, and the
capture root, activation id, act list, consume journal, exit policy, child
environment, stream bounds and timeouts (G2-G7, A-2) are not supplied anywhere. After the imports the entry
still reports that the run is not implemented and exits 69, starting no process,
opening no connection and touching no capture root. The shared first-image and tree
checks below are byte-for-byte the ones in ``rp11_h1.py`` (an AST-equality test
keeps them equal), because both files run before any artifact code can be imported.

Exit status: 64 malformed arguments or ``INVOCATION_ID``, 69 the run is not
implemented, 70 import failure, 71 descriptors not proved closed, 77 unsafe
artifact ownership, mode or type.
"""

import os
import signal
import stat
import sys

EX_USAGE = 64
EX_UNAVAILABLE = 69
EX_SOFTWARE = 70
EX_OSERR = 71
EX_NOPERM = 77

ACCEPTED_ARGV = ["run", "--pass", "A"]

_MAX_ENVIRON = 1 << 20
_OWN_FDS = "/proc/self/fd"
_HEX = frozenset("0123456789abcdef")
_WRITABLE_BY_OTHERS = stat.S_IWGRP | stat.S_IWOTH
_MAX_TREE_ENTRIES = 1000  # the real artifact has about 110

#: The modules the entry loads; their closure is ``build.ENTRY_SOURCES``.
_LOADED = "tools.phase_5_0_evidence.execution.capture_mechanism"
_PASS_A = "tools.phase_5_0_evidence.execution.pass_a"


def _required_owner():
    """The uid every artifact object must have: root, whoever runs the entry."""
    return 0

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

def _initial_environment():
    """The block PID 1 passed to ``execve`` (duplicates included), capped.

    ``None`` if ``/proc/self/environ`` cannot be read completely: the normalized
    ``os.environ`` cannot show a duplicate ``INVOCATION_ID``, so there is no fallback."""
    try:
        fd = os.open("/proc/self/environ", os.O_RDONLY | os.O_CLOEXEC)
    except OSError:
        return None
    try:
        chunks, total = [], 0
        while total <= _MAX_ENVIRON:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        return b"".join(chunks)[: _MAX_ENVIRON + 1]
    except OSError:
        return None
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


def first_image_controls():
    """Descriptors, ``INVOCATION_ID``, environment, signals, umask, cwd.

    Returns the validated ``INVOCATION_ID`` or an exit status to refuse with."""
    for fd in (0, 1, 2):
        try:
            os.fstat(fd)
        except OSError:
            return EX_OSERR
    environ = _initial_environment()
    invocation_id = (
        invocation_id_from(environ) if environ is not None and len(environ) <= _MAX_ENVIRON else None
    )
    if invocation_id in (None, "absent"):
        print("rp11_entry: INVOCATION_ID must be present exactly once, 32 lowercase hex", file=sys.stderr)
        return EX_USAGE
    os.environ.clear()
    if not close_descriptors_from_3():
        print("rp11_entry: inherited descriptors could not be closed", file=sys.stderr)
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
    return invocation_id


def build_pass_a_session(request):
    """G8: the one reviewed arming/session construction site (``request``: ``GenesisRequest``).

    Composes the exact production parts and creates the pass's capture root (X-1).
    Nothing in this module calls it; the imports are local so they run only on a
    call, after the artifact tree has been checked and ``lib/`` is on ``sys.path``.
    """
    from tools.phase_5_0_evidence.execution.boundary import StreamCaptureLauncher
    from tools.phase_5_0_evidence.execution.capture_mechanism import SystemUtcClock, create_capture_session
    from tools.phase_5_0_evidence.execution.capture_store import PosixCaptureFilesystem

    return create_capture_session(
        request,
        filesystem=PosixCaptureFilesystem(),
        launcher=StreamCaptureLauncher(armed=True),
        clock=SystemUtcClock(),
    )


def main(argv):
    sys.dont_write_bytecode = True
    if argv != ACCEPTED_ARGV:
        print("rp11_entry: not the accepted vector (run --pass A)", file=sys.stderr)
        return EX_USAGE
    # abspath, not realpath: a symlink anywhere on the way must be seen, not followed.
    here = os.path.dirname(os.path.abspath(__file__))
    owner = _required_owner()
    problem = _ancestors_problem(here, owner) or _tree_problem(here, owner)
    if problem:
        print(f"rp11_entry: artifact is not root-owned and protected: {problem}", file=sys.stderr)
        return EX_NOPERM
    lib = os.path.join(here, "lib")
    if lib not in sys.path:
        sys.path.append(lib)
    try:
        import tools.phase_5_0_evidence.execution.capture_mechanism as mechanism
        import tools.phase_5_0_evidence.execution.pass_a  # noqa: F401  loaded, never called
    except ImportError as exc:
        print(f"rp11_entry: import failed: {exc}", file=sys.stderr)
        return EX_SOFTWARE
    origin = os.path.abspath(getattr(mechanism, "__file__", "") or "")
    if os.path.commonpath([origin, lib]) != lib:
        print("rp11_entry: the capture module did not load from the artifact", file=sys.stderr)
        return EX_SOFTWARE
    if not close_descriptors_from_3():
        print("rp11_entry: descriptors opened by the artifact's imports could not be closed", file=sys.stderr)
        return EX_OSERR
    print("rp11_entry: the capture run is not implemented in this build", file=sys.stderr)
    return EX_UNAVAILABLE


def entry():
    controls = first_image_controls()
    if isinstance(controls, int):
        return controls
    return main(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(entry())
