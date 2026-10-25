"""The persistent supervisor that owns every admitted SA-2 invocation (OS-6, third remediation).

A restartable, root-controlled **system** service running as the dedicated unprivileged account
(``infra/executor/freedom-blades-executor-supervisor.service``) is the admission and recovery
worker; the account's systemd **user manager** is the kernel owner. Each invocation runs as a
separate transient user service (``adapters.executor.usermanager``), so the supervisor can die and
restart while PID 1 and the user manager keep a populated invocation unit.

Order, for the one invocation a request may create:

1. exclusive admission: no record, no damaged entry, a readable and writable state directory,
   a running manager;
2. ``prepared`` record (nonce, boot identity, deterministic unit name) durably committed;
3. the unit name is confirmed unused, then ``start-sent`` is durably committed;
4. ``StartTransientUnit`` is sent. This is the only process-creating operation, and it is sent
   at most once: after a crash at any point the replacement resolves the unit *by name* and
   never repeats the call;
5. the acknowledged unit is bound (``InvocationID``, cgroup identity) and settled: ``sudo``
   reaped with its typed status captured, the unit's cgroup shown empty (``cgroup.events``,
   ``cgroup.kill`` on that exact recorded cgroup when it is not), the unit removed;
6. only then is the record removed. Until then every later request is ``BLOCKED``.

An ambiguous same-boot ``start-sent`` record (the call may have escaped) is never cleared on elapsed
time: only a later-appearing unit (adopted and settled once) or a changed boot identity ends it. Only
``prepared`` (the call provably was never issued) or a definite manager refusal clears without a unit.

Recovery (``recover_once``) re-reads the active record, adopts it when no live request drives it and
repeats only containment cleanup. It never launches SA-2, never signals by number, name or command
line, and never consults the capture unit.

Maintenance (``drain``, root only): under the admission lock it closes admission for the life of the
process and answers whether nothing is recorded, damaged, adopted or loaded as an invocation unit.
"""

from __future__ import annotations

import errno
import os
import select
import signal
import socket
import stat
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from adapters.executor.ownership import (
    BOUND,
    CLEANUP,
    PREPARED,
    START_SENT,
    OwnershipStore,
    Record,
    StoreError,
    _valid_cgroup,
)
from adapters.executor.usermanager import (
    AmbiguousStart,
    BusUserManager,
    ManagerUnavailable,
    StartRefused,
    UnitView,
    UserManager,
)
from adapters.executor.protocol import (
    DRAIN_EMPTY,
    DRAIN_PENDING,
    DRAIN_REQUEST,
    GREETING,
    MAX_REQUEST_BYTES,
    PROTOCOL_REQUEST,
    SOCKET_NAME,
    peer_uid,
)
from adapters.executor.vector import CHILD_ENV, STOP_ARGV, SUDO
from application.executor.interrupt import PrivilegedStop

CGROUP_ROOT = "/sys/fs/cgroup"
BOOT_ID = "/proc/sys/kernel/random/boot_id"
MAX_CONNECTIONS = 16
MAX_ADOPTERS = 8
_ABSENT = object()


@dataclass(frozen=True)
class Timing:
    wait: float = 60.0  # DI-S completion deadline is 30 s; sudo and start-up add little
    term_grace: float = 10.0
    descendants: float = 10.0  # after ``sudo`` is gone, how long its privileged descendants get to exit on their own
    kill_reap: float = 10.0
    kill_rounds: int = 3
    bind: float = 30.0
    clear: float = 10.0
    start_resolve: float = 5.0  # how long a unit whose creation the manager *acknowledged* may stay invisible
    poll: float = 0.25
    recovery_interval: float = 5.0


class Cgroups(Protocol):
    def identity(self, relative: str) -> int | None:
        """The cgroup's id (directory inode), or ``None`` when it does not exist."""

    def populated(self, relative: str, identity: int) -> bool:
        """``cgroup.events`` ``populated``. A cgroup that is gone, or is no longer that very cgroup, is empty. ``OSError``: unknown."""

    def kill(self, relative: str, identity: int) -> None:
        """``cgroup.kill`` on exactly that cgroup; nothing when it is gone or is another cgroup."""


class KernelCgroups:
    def __init__(self, root: str = CGROUP_ROOT) -> None:
        self._root = root

    def _open(self, relative: str, identity: int | None) -> int | None:
        if not _valid_cgroup(relative, relative.rsplit("/", 1)[-1]) or relative == "":
            raise OSError(errno.EINVAL, "cgroup path")
        try:
            fd = os.open(self._root + relative, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        except FileNotFoundError:
            return None
        try:
            if identity is not None and os.fstat(fd).st_ino != identity:
                os.close(fd)
                return None  # the recorded cgroup is gone; this is another one
        except BaseException:
            os.close(fd)
            raise
        return fd

    def identity(self, relative: str) -> int | None:
        fd = self._open(relative, None)
        if fd is None:
            return None
        try:
            return os.fstat(fd).st_ino
        finally:
            os.close(fd)

    def populated(self, relative: str, identity: int) -> bool:
        fd = self._open(relative, identity)
        if fd is None:
            return False
        try:
            events = os.open("cgroup.events", os.O_RDONLY | os.O_CLOEXEC, dir_fd=fd)
            try:
                text = os.pread(events, 256, 0).decode("ascii", "replace")
            finally:
                os.close(events)
        except FileNotFoundError:
            return False
        finally:
            os.close(fd)
        for line in text.splitlines():
            if line.startswith("populated "):
                return line.split()[1] != "0"
        raise OSError(errno.EIO, "cgroup.events has no populated line")

    def kill(self, relative: str, identity: int) -> None:
        fd = self._open(relative, identity)
        if fd is None:
            return
        try:
            handle = os.open("cgroup.kill", os.O_WRONLY | os.O_CLOEXEC, dir_fd=fd)
            try:
                os.write(handle, b"1")
            finally:
                os.close(handle)
        except FileNotFoundError:
            pass
        finally:
            os.close(fd)


def read_boot_id() -> str:
    with open(BOOT_ID, encoding="ascii") as handle:
        return handle.read().strip()


class Core:
    """Admission, launch, settlement and recovery. Pure policy over four injected ports."""

    def __init__(
        self,
        store: OwnershipStore,
        manager: UserManager,
        cgroups: Cgroups,
        *,
        boot_id: Callable[[], str] = read_boot_id,
        clock: Callable[[], float] = time.monotonic,
        wall: Callable[[], float] = time.time,
        sleep: Callable[[float], None] = time.sleep,
        timing: Timing = Timing(),
        spawn: Callable[[Callable[[], None]], None] | None = None,
        argv: tuple[str, ...] = STOP_ARGV,
        executable: str = SUDO,
    ) -> None:
        self._argv, self._executable = argv, executable  # the fixed vector; a seam only for the host proofs' stand-in member
        self._store, self._manager, self._cgroups = store, manager, cgroups
        self._boot, self._clock, self._wall, self._sleep, self._t = boot_id, clock, wall, sleep, timing
        self._spawn = spawn or _thread
        self._admission = threading.Lock()
        self._active: set[str] = set()
        self._guard = threading.Lock()
        self._draining = False
        self.ready = False

    @property
    def recovery_interval(self) -> float:
        return self._t.recovery_interval

    # --- readiness -----------------------------------------------------------

    def startup(self) -> None:
        """Establish readiness: a trusted writable state directory, a running manager, records re-read."""
        self._store.create_directory()
        self._store.check_writable()
        self._manager.ready()
        self._store.listing()
        self.ready = True

    # --- maintenance -----------------------------------------------------------

    def drain(self) -> bool:
        """Close admission for the life of this process; ``True`` only if nothing is owned, recorded or loaded.

        Takes the admission lock, so no request is between its listing and its record: after this returns, a
        stop either holds a durable record that the answer saw, or is refused before anything is written.
        """
        if not self.ready:
            return False
        with self._admission:
            self._draining = True  # unconditional and permanent: an inconclusive answer must not reopen admission
            try:
                if self._store.listing().blocking:
                    return False
                self._manager.ready()
                with self._guard:
                    if self._active:
                        return False
                return not self._manager.invocation_units()
            except (StoreError, ManagerUnavailable, OSError):
                return False

    # --- one request ------------------------------------------------------------

    def handle_stop(self, alive: Callable[[], bool] = lambda: True) -> PrivilegedStop:
        if not self.ready:
            return PrivilegedStop.NOT_SENT
        with self._admission:  # one admitted invocation at most, until its record is durably removed
            if self._draining:
                return PrivilegedStop.NOT_SENT  # maintenance closed admission; nothing was recorded or launched
            try:
                if self._store.listing().blocking:
                    return PrivilegedStop.BLOCKED
            except StoreError:
                return PrivilegedStop.BLOCKED  # unreadable ownership state is a block, never an empty one
            try:
                self._manager.ready()
                record = Record.fresh(self._boot())
                self._store.put(record)  # durable before anything can be launched
            except (StoreError, ManagerUnavailable, OSError):
                return PrivilegedStop.NOT_SENT
            self._mark(record.nonce)
        try:
            return self._admitted(record, alive)
        finally:
            self._unmark(record.nonce)

    def _admitted(self, record: Record, alive: Callable[[], bool]) -> PrivilegedStop:
        try:
            if self._manager.unit(record.unit) is not None:
                return PrivilegedStop.BLOCKED  # the fresh name is in use: leave the record, recovery adopts it
        except ManagerUnavailable:
            return self._never_started(record)
        if not alive():
            return self._never_started(record)
        try:
            self._store.put(record.to(START_SENT))  # durable *before* the call: after this the call may exist
        except StoreError:
            return self._never_started(record)
        record = record.to(START_SENT)
        acknowledged = False
        try:
            self._manager.start_transient(
                record.unit, self._argv, executable=self._executable, environment=tuple(f"{k}={v}" for k, v in CHILD_ENV.items())
            )
            acknowledged = True
        except StartRefused:
            return self._never_started(record)  # an ERROR reply: no unit was created
        except (AmbiguousStart, ManagerUnavailable):
            pass  # resolved below by name; the call is never sent again
        return self._bind_and_settle(record, acknowledged)

    def _never_started(self, record: Record) -> PrivilegedStop:
        try:
            self._store.remove(record)
        except StoreError:
            pass  # still a `prepared`/`start-sent` record: it blocks, and recovery clears it by name
        return PrivilegedStop.NOT_SENT

    def _bind_and_settle(self, record: Record, acknowledged: bool) -> PrivilegedStop:
        bound = self._bind(record, acknowledged)
        if bound is None:
            return PrivilegedStop.HANDED_OFF  # unresolved: the record stays, recovery resolves it by name
        if bound is _ABSENT:  # acknowledged, then gone: it leaves no cgroup, nothing is running, the result is unknown
            return PrivilegedStop.NOT_CONFIRMED if self._clear(record) else PrivilegedStop.HANDED_OFF
        return self._settle(bound)

    # --- binding, settlement -----------------------------------------------------

    def _view(self, name: str):
        try:
            return self._manager.unit(name)
        except ManagerUnavailable:
            return _UNKNOWN

    def _bind(self, record: Record, acknowledged: bool = False):
        """The bound record; ``None`` when unresolved in time.

        ``_ABSENT`` only when the manager *acknowledged* creating the unit and then shows none: absence of a unit
        whose creation was never acknowledged is not evidence that a queued request cannot still create it.
        """
        started = self._clock()
        while True:
            view = self._view(record.unit)
            if view is None:
                if acknowledged and self._clock() - started >= self._t.start_resolve:
                    return _ABSENT
            elif view is not _UNKNOWN and len(view.invocation_id) == 32 and (view.active_state != "activating" or view.control_group):
                # A freshly created unit can be loaded, `inactive/dead` and already forked, with no InvocationID yet:
                # there is nothing to bind until the manager has started it, so keep looking (bounded by ``bind``).
                return self._bound(record, view)
            if self._clock() - started >= self._t.bind:
                return None
            self._sleep(self._t.poll)

    def _bound(self, record: Record, view: UnitView) -> Record | None:
        cgroup, identity = "", 0
        if view.control_group:
            try:
                found = self._cgroups.identity(view.control_group)
            except OSError:
                return None
            if found is not None:
                cgroup, identity = view.control_group, found
        if len(view.invocation_id) != 32 or not _valid_cgroup(cgroup, record.unit):
            return None
        bound = record.to(BOUND, invocation_id=view.invocation_id, cgroup=cgroup, cgroup_id=identity)
        self._persist(bound)  # a failed write leaves the older, still-resolvable record on disk
        return bound

    def _persist(self, record: Record) -> None:
        try:
            self._store.put(record)
        except StoreError:
            pass

    def _empty(self, record: Record) -> bool | None:
        """``True`` only on affirmative evidence the recorded boundary is empty; ``None``: cannot tell."""
        view = self._view(record.unit)
        if view is _UNKNOWN:
            return None
        if view is not None:
            if view.invocation_id != record.invocation_id:
                return None  # another invocation under our name: never ours to judge or kill
            if view.control_group != record.cgroup and view.control_group:
                return None
        if record.cgroup == "":
            return True
        try:
            return not self._cgroups.populated(record.cgroup, record.cgroup_id)
        except OSError:
            return None

    def _wait_until(self, seconds: float, done: Callable[[], bool]) -> bool:
        end = self._clock() + seconds
        while True:
            if done():
                return True
            if self._clock() >= end:
                return False
            self._sleep(self._t.poll)

    def _settle(self, record: Record) -> PrivilegedStop:
        """Drive a bound invocation to a clear boundary; ``HANDED_OFF`` when the kernel does not show it empty in time."""
        forced, status = False, None
        end = self._clock() + self._t.wait
        while True:
            view = self._view(record.unit)
            if view is None or (view is not _UNKNOWN and view.main_exited):
                status = None if view is None else (view.exec_main_code, view.exec_main_status)
                break
            if self._clock() >= end:
                forced = True
                break
            self._sleep(self._t.poll)
        if forced:
            record = self._cleanup_state(record)
            try:
                self._manager.stop(record.unit)  # the manager relays SIGTERM to ``sudo``, which relays it on
            except ManagerUnavailable:
                pass
            self._wait_until(self._t.term_grace, lambda: self._main_gone(record))
        elif not self._wait_until(self._t.descendants, lambda: self._empty(record) is True):
            forced = True
        if self._empty(record) is not True:
            record = self._cleanup_state(record)
            for _ in range(self._t.kill_rounds):
                self._kill(record)
                if self._wait_until(self._t.kill_reap, lambda: self._empty(record) is True):
                    break
            else:
                return PrivilegedStop.HANDED_OFF
            forced = True
        if not self._clear(record):
            return PrivilegedStop.HANDED_OFF
        return PrivilegedStop.NOT_CONFIRMED if forced else _mapped(status)

    def _main_gone(self, record: Record) -> bool:
        view = self._view(record.unit)
        return view is None or (view is not _UNKNOWN and view.main_exited)

    def _cleanup_state(self, record: Record) -> Record:
        if record.state == CLEANUP:
            return record
        cleaning = record.to(CLEANUP)
        self._persist(cleaning)
        return cleaning

    def _kill(self, record: Record) -> None:
        if record.cgroup == "":
            return
        view = self._view(record.unit)
        if view is not None and view is not _UNKNOWN and (
            view.invocation_id != record.invocation_id or view.control_group not in ("", record.cgroup)
        ):
            return  # another invocation under our name: the recorded boundary is not verified, so it is not signalled
        try:
            self._cgroups.kill(record.cgroup, record.cgroup_id)
        except OSError:
            pass  # the next observation decides

    def _clear(self, record: Record) -> bool:
        """Remove the unit, then the record: the terminal clearance, only on an empty, removed boundary."""
        if self._empty(record) is not True:
            return False

        def removed() -> bool:
            try:
                self._manager.stop(record.unit)
                self._manager.reset_failed(record.unit)
            except ManagerUnavailable:
                return False
            return self._view(record.unit) is None

        if not self._wait_until(self._t.clear, removed):
            return False
        try:
            self._store.remove(record)
        except StoreError:
            return False
        return True

    # --- recovery ----------------------------------------------------------------

    def recover_once(self) -> int:
        """One bounded pass. Returns the entries still blocking. Never launches; adopts what nobody drives."""
        try:
            listing = self._store.listing()
        except StoreError:
            return 1
        for name in listing.stray_temporaries[:16]:
            try:
                self._store.remove_stale_temporary(name, self._wall())  # never an admission's in-flight temporary
            except StoreError:
                pass
        still = len(listing.damaged)
        try:
            boot = self._boot()
        except OSError:
            return still + len(listing.records)
        adopters = 0
        # Live invocations first, so records still waiting to be resolved can never starve one.
        for record in sorted(listing.records, key=lambda item: (item.state in (PREPARED, START_SENT), item.nonce)):
            if self._is_active(record.nonce):
                adopters += 1
                still += 1
            elif record.boot != boot:
                # A reboot ends every cgroup: this boot's identity differs, so nothing recorded can still exist.
                try:
                    self._store.remove(record)
                except StoreError:
                    still += 1
            elif adopters < MAX_ADOPTERS:
                adopters += 1
                still += 1
                self._adopt(record)
            else:
                still += 1
        return still

    def _adopt(self, record: Record) -> None:
        if not self._mark(record.nonce):
            return

        def run() -> None:
            try:
                self._drive_adopted(record)
            except Exception:  # noqa: BLE001 - the record stays; the next pass adopts it again
                pass
            finally:
                self._unmark(record.nonce)

        self._spawn(run)

    def _drive_adopted(self, record: Record) -> None:
        if record.state in (PREPARED, START_SENT):
            view = self._view(record.unit)
            if view is _UNKNOWN:
                return
            if view is None:
                if record.state == PREPARED:
                    self._never_started(record)  # start-sent was never committed, so the call was never issued
                return  # start-sent: the call may be queued; only a unit appearing or a new boot ends it
            bound = self._bind(record)
            if bound is None or bound is _ABSENT:
                return
            record = bound
        self._settle(record)

    # --- active set ------------------------------------------------------------

    def _mark(self, nonce: str) -> bool:
        with self._guard:
            if nonce in self._active:
                return False
            self._active.add(nonce)
            return True

    def _unmark(self, nonce: str) -> None:
        with self._guard:
            self._active.discard(nonce)

    def _is_active(self, nonce: str) -> bool:
        with self._guard:
            return nonce in self._active


class _Unknown:
    pass


_UNKNOWN = _Unknown()


def _mapped(status: tuple[int, int] | None) -> PrivilegedStop:
    """The exit status of ``sudo``: 0 stopped, 20 refused, 21 not sent; everything else is never success."""
    if status == (1, 0):
        return PrivilegedStop.STOPPED
    if status == (1, 20):
        return PrivilegedStop.REFUSED
    if status == (1, 21):
        return PrivilegedStop.NOT_SENT
    return PrivilegedStop.NOT_CONFIRMED  # 22, a signal death, an unexpected status, or a status never captured


def _thread(work: Callable[[], None]) -> None:
    threading.Thread(target=work, daemon=True).start()


# --- the socket service ------------------------------------------------------------


def _client_alive(conn: socket.socket) -> bool:
    """``False`` once the peer has hung up (EOF is readable and peeks as empty); never blocks."""
    try:
        if not select.select([conn], [], [], 0)[0]:
            return True
        return conn.recv(1, socket.MSG_PEEK) != b""
    except OSError:
        return False


class Server:
    HOLD_SECONDS = 300.0  # how long a drain connection is held open after its answer (the maintainer's liveness signal)

    def __init__(self, core: Core, path: str, *, uid: int | None = None, maintenance_uid: int = 0) -> None:
        self._core, self._path = core, path
        self._uid = os.getuid() if uid is None else uid
        self._maintenance_uid = maintenance_uid
        self._listener: socket.socket | None = None
        self._connections = 0
        self._lock = threading.Lock()
        self._closed = threading.Event()

    def bind(self) -> None:
        try:
            info = os.lstat(self._path)
        except FileNotFoundError:
            info = None
        if info is not None:
            if not stat.S_ISSOCK(info.st_mode) or info.st_uid != self._uid:
                raise OSError(errno.EEXIST, "not our socket")
            os.unlink(self._path)  # stale: nothing listens (the lock is held)
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        listener.bind(self._path)
        os.chmod(self._path, 0o600)
        listener.listen(8)
        listener.settimeout(0.5)
        self._listener = listener

    def serve(self, stop: threading.Event) -> None:
        assert self._listener is not None
        while not stop.is_set():
            try:
                conn, _ = self._listener.accept()
            except TimeoutError:
                continue
            except OSError:
                break
            with self._lock:
                busy = self._connections >= MAX_CONNECTIONS
                if not busy:
                    self._connections += 1
            if busy:
                conn.close()
                continue
            threading.Thread(target=self._handle, args=(conn,), daemon=True).start()

    def close(self) -> None:
        self._closed.set()
        if self._listener is not None:
            self._listener.close()
        try:
            os.unlink(self._path)
        except OSError:
            pass

    def _handle(self, conn: socket.socket) -> None:
        try:
            with conn:
                conn.settimeout(5.0)
                uid = peer_uid(conn)
                if uid not in (self._uid, self._maintenance_uid) or not self._core.ready:
                    return
                conn.sendall(GREETING)
                request = _read_line(conn, MAX_REQUEST_BYTES)
                if request == PROTOCOL_REQUEST and uid == self._uid:
                    self._stop(conn)
                elif request == DRAIN_REQUEST and uid == self._maintenance_uid and uid != self._uid:
                    self._drain(conn)
        except Exception:  # noqa: BLE001 - a handler fault never takes the service down; the record decides
            pass
        finally:
            with self._lock:
                self._connections -= 1

    def _stop(self, conn: socket.socket) -> None:
        outcome = self._core.handle_stop(alive=lambda: _client_alive(conn))
        try:
            conn.sendall(f"result {outcome.value}\n".encode("ascii"))
        except OSError:
            pass  # the client is gone; the invocation is settled or owned either way

    def _drain(self, conn: socket.socket) -> None:
        empty = self._core.drain()
        conn.sendall(DRAIN_EMPTY if empty else DRAIN_PENDING)
        # Admission stays closed for the life of the process. The connection stays open for as long as this
        # process serves, so the maintainer sees EOF if the supervisor is lost before systemd stops it.
        conn.settimeout(None)
        deadline = time.monotonic() + self.HOLD_SECONDS
        while not self._closed.is_set() and time.monotonic() < deadline and _client_alive(conn):
            self._closed.wait(0.5)


def _read_line(conn: socket.socket, limit: int) -> bytes:
    data = b""
    while len(data) < limit and not data.endswith(b"\n"):
        chunk = conn.recv(limit - len(data))
        if not chunk:
            break
        data += chunk
    return data


def notify(message: bytes) -> None:
    target = os.environ.get("NOTIFY_SOCKET", "")
    if not target or target[0] not in "/@":
        return
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
        sock.connect("\0" + target[1:] if target[0] == "@" else target)
        sock.send(message)


def run(core: Core, server: Server, stop: threading.Event) -> int:
    """Prepare state/manager/recovery, bind and start the server, and only then publish READY."""
    core.startup()
    core.recover_once()
    server.bind()
    thread = threading.Thread(target=server.serve, args=(stop,), daemon=True)
    thread.start()
    # The service is ready only after the accept loop has been started.  The listening socket
    # exists slightly earlier, but its pathname alone is not the readiness boundary.
    notify(b"READY=1")
    try:
        while not stop.is_set():
            if not thread.is_alive():
                return 70  # nobody accepts any more: exit so systemd restarts a viable owner instead of trusting READY
            core.recover_once()
            stop.wait(core.recovery_interval)
    finally:
        notify(b"STOPPING=1")
        server.close()
    return 0


def main(*, argv: tuple[str, ...] = STOP_ARGV, executable: str = SUDO, timing: Timing = Timing()) -> int:
    """The service entry. The keyword seams exist only for the host proofs' stand-in member and timings."""
    import fcntl

    state, runtime = os.environ.get("STATE_DIRECTORY", ""), os.environ.get("RUNTIME_DIRECTORY", "")
    if not state.startswith("/") or not runtime.startswith("/") or ":" in state or ":" in runtime:
        print("rp11-executor-supervisor: no state/runtime directory", file=sys.stderr)
        return 78
    uid = os.getuid()
    if uid == 0:
        print("rp11-executor-supervisor: refusing to run as root", file=sys.stderr)
        return 78
    lock = os.open(os.path.join(runtime, "supervisor.lock"), os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("rp11-executor-supervisor: another supervisor holds the lock", file=sys.stderr)
        return 75
    from adapters.executor.userbus import connect_user_bus

    core = Core(
        OwnershipStore(os.path.join(state, "invocations"), uid=uid),
        BusUserManager(lambda: connect_user_bus(uid)),
        KernelCgroups(),
        timing=timing,
        argv=argv,
        executable=executable,
    )
    server = Server(core, os.path.join(runtime, SOCKET_NAME), uid=uid)
    stop = threading.Event()
    for signum in (signal.SIGTERM, signal.SIGINT):
        signal.signal(signum, lambda *_: stop.set())
    try:
        return run(core, server, stop)
    except (StoreError, ManagerUnavailable, OSError) as error:
        print(f"rp11-executor-supervisor: not ready ({type(error).__name__})", file=sys.stderr)
        return 69


if __name__ == "__main__":
    raise SystemExit(main())
