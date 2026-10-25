"""Non-root adapters and entry point of the executor interruption slice (OS-6).

Runs as the unprivileged operator. Nothing here is caller-controlled but the validated
activation id: the unit, the journal path, the ``sudo`` executable and the whole SA-2
argv are fixed, and the child gets an emptied environment.

* ``LocalConsumeJournalReader`` — the fixed ``<id>-consume-evidence/journal``, opened
  descriptor-first without following a link, bounded, and checked on the opened object.
* ``SudoStopInvoker`` — a client of the persistent supervisor (``adapters.executor.supervisor``),
  which alone admits, launches, owns and settles the one ``sudo -n … rp11_h1.py stop`` invocation
  as a transient service of the dedicated account's systemd user manager. The executor creates and holds no process;
  once its request is sent, every outcome is either a settled result or a durable record owned by
  the supervisor that keeps blocking further stops until the boundary is empty.
"""

from __future__ import annotations

import errno
import os
import signal
import socket
import stat
import sys
import time
from collections.abc import Callable

from adapters.executor.protocol import GREETING, PROTOCOL_REQUEST, SOCKET_PATH, peer_uid
from adapters.executor.vector import CHILD_ENV, STOP_ARGV, SUDO
from adapters.systemd.bus import BusConnection
from adapters.systemd.manager import SystemdManagerAdapter
from application.executor.interrupt import (
    MAX_JOURNAL_BYTES,
    ConsumeJournalReader,
    InterruptProcedure,
    InterruptResult,
    PrivilegedStop,
    StopInvoker,
    UnitObserver,
)
from application.rp11.paths import ActivationPaths, Layout
from application.unit_control import ControlSpecError, validate_activation_id

from adapters.rp11.fsops import _FILE_FLAGS, _read_capped, close_quietly, open_dir

EX_USAGE = 64
EX_INTERNAL = 70

CLIENT_DEADLINE_SECONDS = 180.0  # the supervisor's own bounded cycle is shorter; past it the invocation is owned, not awaited
CONNECT_SECONDS = 5.0
MAX_REPLY_BYTES = 64


def _file_state(info: os.stat_result) -> tuple:
    """Everything about the journal object that must not change during one observation."""
    return (info.st_mode, info.st_dev, info.st_ino, info.st_uid, info.st_gid, info.st_nlink, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns)


def _dir_state(info: os.stat_result) -> tuple:
    return (info.st_mode, info.st_dev, info.st_ino, info.st_uid, info.st_gid)


class LocalConsumeJournalReader:
    """``ConsumeJournalReader``: root-owned ``0755`` directory, root-owned ``0644`` journal.

    One bounded observation: the opened object, the name ``journal`` and the evidence directory
    are each shown, after the single read, to be the same acceptable object they were before it.
    Any difference (replacement, unlink/relink, link, owner/mode/type change, timestamps, size) is
    ``None``; the bytes are never accepted merely because they still parse.
    """

    def __init__(self, layout: Layout | None = None) -> None:
        self._layout = layout or Layout()

    def _acceptable_dir(self, info: os.stat_result) -> bool:
        owner = self._layout.owner
        return (
            stat.S_ISDIR(info.st_mode)
            and (info.st_uid, info.st_gid) == (owner.uid, owner.gid)
            and stat.S_IMODE(info.st_mode) == 0o755
        )

    def _acceptable_file(self, info: os.stat_result) -> bool:
        owner = self._layout.owner
        return (
            stat.S_ISREG(info.st_mode)
            and (info.st_uid, info.st_gid) == (owner.uid, owner.gid)
            and stat.S_IMODE(info.st_mode) == 0o644
            and info.st_nlink == 1
            and info.st_size <= MAX_JOURNAL_BYTES
        )

    def read_consume_journal(self, activation_id: str) -> bytes | None:
        directory = ActivationPaths(self._layout, activation_id).consume_dir
        try:
            dfd = open_dir(directory)
        except OSError:
            return None
        try:
            dinfo = os.fstat(dfd)
            if not self._acceptable_dir(dinfo):
                return None
            fd = os.open("journal", _FILE_FLAGS, dir_fd=dfd)
            try:
                info = os.fstat(fd)
                if not self._acceptable_file(info):
                    return None
                data = _read_capped(fd, info.st_size)
                if len(data) != info.st_size:
                    return None  # short read or growth
                if _file_state(os.fstat(fd)) != _file_state(info):
                    return None  # the opened object changed under the read
                # The name must still identify this very object (no replacement, unlink or relink).
                named = os.stat("journal", dir_fd=dfd, follow_symlinks=False)
                if _file_state(named) != _file_state(info):
                    return None
            finally:
                close_quietly(fd)
            # The directory, held and re-resolved from the fixed path without following a link.
            if _dir_state(os.fstat(dfd)) != _dir_state(dinfo):
                return None
            again = open_dir(directory)
            try:
                now = os.fstat(again)
            finally:
                close_quietly(again)
            if _dir_state(now) != _dir_state(dinfo) or not self._acceptable_dir(now):
                return None
            return data
        except OSError:
            return None
        finally:
            close_quietly(dfd)


class SudoStopInvoker:
    """Ask the persistent supervisor to run the fixed SA-2 vector once; never launch or hold a process.

    The executor is a client. Admission, the durable ownership record, the single
    ``StartTransientUnit`` and the settlement of the invocation unit all belong to the supervisor
    (``adapters.executor.supervisor``), which is already running, owns every admitted invocation
    through the systemd user manager and keeps blocking orchestration until the boundary is empty.
    Nothing here can create a process, so no timeout, signal or exception can leave one unowned:
    once the request is sent, whatever the supervisor did is covered by its durable record.

    Before the request is sent nothing exists: an absent, stopped, starting or stale supervisor
    (no socket, a refused connection, a socket of another owner, a peer of another uid, a wrong
    greeting) is ``NOT_SENT``. After it is sent, a reply other than an exact result token, a lost
    connection, a timeout and an interruption are ``HANDED_OFF``: the supervisor owns the outcome
    and is never asked again. SA-2 is never retried.
    """

    def __init__(
        self,
        *,
        socket_path: str | None = None,
        deadline_seconds: float = CLIENT_DEADLINE_SECONDS,
        uid: int | None = None,
        connect: Callable[[str, float], socket.socket] | None = None,
    ) -> None:
        self._uid = os.getuid() if uid is None else uid
        self._path = socket_path or SOCKET_PATH
        self._deadline = deadline_seconds
        self._connect = connect or _connect

    def invoke_stop(self) -> PrivilegedStop:
        try:
            conn = self._connect(self._path, self._uid)
        except OSError:
            return PrivilegedStop.NOT_SENT  # no supervisor to own an invocation: nothing is launched
        # The phase boundary.  It is set immediately before ``sendall`` is entered, because from then on
        # some or all of the request may have crossed: every exceptional exit at or after it (an OSError,
        # an interruption, SystemExit, a failing reply, close or context exit) is owned and uncertain.
        # Before it, nothing was sent, so an OSError is NOT_SENT and any other exception is not ours to hide.
        written = False
        try:
            with conn:
                try:
                    conn.settimeout(CONNECT_SECONDS)
                    if peer_uid(conn) != self._uid or _read_exactly(conn, len(GREETING)) != GREETING:
                        return PrivilegedStop.NOT_SENT  # not a ready supervisor of this user: nothing was sent
                except OSError:
                    return PrivilegedStop.NOT_SENT  # the request write was never attempted
                written = True
                conn.sendall(PROTOCOL_REQUEST)  # cannot say how many bytes crossed if it fails
                conn.settimeout(self._deadline)
                return self._reply(conn)
        except BaseException as error:
            if written:
                return PrivilegedStop.HANDED_OFF  # never retried, reconnected or asked again
            if isinstance(error, OSError):
                return PrivilegedStop.NOT_SENT  # a failure closing the connection of a request never written
            raise

    def _reply(self, conn: socket.socket) -> PrivilegedStop:
        end = time.monotonic() + self._deadline
        data = b""
        try:
            while not data.endswith(b"\n") and len(data) < MAX_REPLY_BYTES:
                conn.settimeout(max(0.001, end - time.monotonic()))
                chunk = conn.recv(MAX_REPLY_BYTES - len(data))
                if not chunk:
                    break
                data += chunk
        except OSError:
            return PrivilegedStop.HANDED_OFF  # timed out or reset: the supervisor owns whatever was admitted
        for outcome in _REPLIES:
            if data == f"result {outcome.value}\n".encode("ascii"):
                return outcome
        return PrivilegedStop.HANDED_OFF  # sent but not answered in the exact protocol: owned, never success


_REPLIES = tuple(PrivilegedStop)


def _read_exactly(conn: socket.socket, size: int) -> bytes:
    data = b""
    while len(data) < size:
        chunk = conn.recv(size - len(data))
        if not chunk:
            break
        data += chunk
    return data


def _connect(path: str, uid: int) -> socket.socket:
    """Connect to the supervisor's socket only if it is a socket owned by this user (no link, no other owner)."""
    info = os.lstat(path)
    if not stat.S_ISSOCK(info.st_mode) or info.st_uid != uid:
        raise OSError(errno.ENOTSOCK, "supervisor socket")
    conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        conn.settimeout(CONNECT_SECONDS)
        conn.connect(path)
    except BaseException:
        conn.close()
        raise
    return conn


def build_interrupt(
    *,
    units: UnitObserver | None = None,
    journals: ConsumeJournalReader | None = None,
    stop: StopInvoker | None = None,
    connector: Callable[[], BusConnection] | None = None,
) -> InterruptProcedure:
    if units is None:
        if connector is None:
            from adapters.systemd.jeepney_bus import connect_system_bus

            connector = connect_system_bus
        units = SystemdManagerAdapter(connector)
    return InterruptProcedure(units, journals or LocalConsumeJournalReader(), stop or SudoStopInvoker())


def _terminate_as_interrupt(signum, frame) -> None:  # noqa: ARG001
    raise KeyboardInterrupt


def run_interrupt(argv: list[str], **ports) -> int:
    """``interrupt <activation-id>``; the id is the only operand."""
    if len(argv) != 1:
        print("rp11-interrupt usage", file=sys.stderr)
        return EX_USAGE
    try:
        activation_id = validate_activation_id(argv[0])
    except ControlSpecError:
        print("rp11-interrupt usage", file=sys.stderr)
        return EX_USAGE
    try:
        previous = signal.signal(signal.SIGTERM, _terminate_as_interrupt)
    except ValueError:  # not the main thread
        previous = None
    try:
        outcome: InterruptResult = build_interrupt(**ports).run(activation_id)
    except KeyboardInterrupt:  # SIGTERM/SIGINT before the outcome is known: fail closed
        print("rp11-interrupt error interrupted", file=sys.stderr)
        return 22
    except Exception:  # noqa: BLE001 - fixed, value-free failure at the outer boundary
        print("rp11-interrupt internal-error", file=sys.stderr)
        return EX_INTERNAL
    finally:
        if previous is not None:
            signal.signal(signal.SIGTERM, previous)
    print(outcome.line, file=sys.stderr)
    return outcome.exit_code


def main() -> int:
    return run_interrupt(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
