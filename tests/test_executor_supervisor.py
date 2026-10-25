"""Executor OS-6: durable ownership before launch, and the persistent supervisor that keeps it.

A deterministic world models the systemd user manager (transient units, typed state), the
kernel's cgroups (``populated``, ``cgroup.kill``, tasks in uninterruptible sleep that ignore it
until their I/O is released) and time. No sleeps: the supervisor's ``sleep`` advances the world.
Real unix sockets exercise the client/server protocol; the real-manager behavior is proved on
``oracle-test`` (``tests/systemd_integration/test_executor_supervisor_host.py``).
"""

from __future__ import annotations

import errno
import os
import socket
import threading
import time

import pytest

from adapters.executor.interrupt import SudoStopInvoker
from adapters.executor.ownership import (
    BOUND,
    CLEANUP,
    PREPARED,
    START_SENT,
    FileOps,
    OwnershipStore,
    Record,
    StoreError,
)
from adapters.executor.protocol import GREETING, PROTOCOL_REQUEST
from adapters.executor.supervisor import Core, Server, Timing
from adapters.executor.usermanager import AmbiguousStart, ManagerUnavailable, StartRefused, UnitView
from adapters.executor.vector import CHILD_ENV, STOP_ARGV, SUDO
from application.executor.interrupt import PrivilegedStop

BOOT = "11111111-2222-3333-4444-555555555555"
OTHER_BOOT = "99999999-2222-3333-4444-555555555555"
TIMING = Timing(wait=2.0, term_grace=1.0, descendants=1.0, kill_reap=1.0, kill_rounds=3, bind=3.0, clear=2.0,
                start_resolve=1.0, poll=0.1, recovery_interval=0.5)
CG_BASE = "/user.slice/user-1.slice/user@1.service/app.slice/"


class Crash(BaseException):
    """The supervisor process dying at an exact point (not an Exception: nothing may catch it)."""


class Proc:
    def __init__(self, world, dies_at=None, unkillable=False, status=0):
        self.world, self.dies_at, self.unkillable, self.status = world, dies_at, unkillable, status
        self.killed = self.terminated = False

    @property
    def alive(self) -> bool:
        if self.unkillable:
            return not self.world.released
        if self.killed or self.terminated:
            return False
        return self.dies_at is None or self.world.now < self.dies_at


class Unit:
    def __init__(self, world, name, main, extra):
        self.name, self.main, self.procs = name, main, [main, *extra]
        self.invocation = f"{world.next_id:032x}"
        self.cgroup = CG_BASE + name
        self.cgroup_id = world.next_id
        self.created = world.now
        self.stop_requested = False
        world.next_id += 1

    def populated(self) -> bool:
        return any(proc.alive for proc in self.procs)


class World:
    def __init__(self):
        self.now, self.released, self.next_id = 0.0, False, 5000
        self.units: dict[str, Unit] = {}
        self.unrelated: dict[str, tuple[int, Proc]] = {}
        self.starts = 0
        self.start_calls = 0
        self.kills: list[str] = []
        self.unrelated_kills: list[str] = []
        self.boot = BOOT
        # scenario for the next unit
        self.main_runs, self.main_status, self.main_unkillable = 0.3, 0, False
        self.extra_procs: list[dict] = []
        self.activating_for = 0.2
        self.prestart_for = 0.0  # a created unit that is loaded and `inactive/dead` with no InvocationID yet
        # faults
        self.ready_error = False
        self.unit_error = lambda: False
        self.units_error = lambda: False
        self.populated_error = lambda: False
        self.kill_error = lambda: False
        self.start_mode = "ok"
        self.gate: threading.Event | None = None
        self.reached_gate = threading.Event()

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds

    def release(self) -> None:
        self.released = True

    def plant_unrelated(self, name: str) -> str:
        path = CG_BASE + name
        self.unrelated[path] = (self.next_id, Proc(self))
        self.next_id += 1
        return path

    def live_units(self) -> list[Unit]:
        return [unit for unit in self.units.values() if unit.populated()]

    def create(self, name: str) -> None:
        main = Proc(self, dies_at=self.now + self.main_runs, unkillable=self.main_unkillable, status=self.main_status)
        extra = [Proc(self, dies_at=None if spec.get("forever") else self.now + spec.get("lives", 0.5),
                      unkillable=spec.get("unkillable", False)) for spec in self.extra_procs]
        self.units[name] = Unit(self, name, main, extra)


class Manager:
    def __init__(self, world: World):
        self.w = world

    def ready(self):
        if self.w.ready_error:
            raise ManagerUnavailable("down")

    def invocation_units(self):
        if self.w.units_error():
            raise ManagerUnavailable("list-units")
        return tuple(sorted(self.w.units))

    def start_transient(self, name, argv, *, executable, environment):
        w = self.w
        w.last_start = (name, argv, executable, environment)
        w.start_calls += 1
        if w.gate is not None:
            w.reached_gate.set()
            w.gate.wait(10)
        if w.start_mode == "refuse":
            raise StartRefused("org.freedesktop.systemd1.UnitExists")
        if w.start_mode == "lost-before":
            raise AmbiguousStart("BusTimeout")
        if w.start_mode == "crash-before":
            raise Crash
        w.starts += 1
        w.create(name)
        if w.start_mode == "lost-after":
            raise AmbiguousStart("BusTimeout")
        if w.start_mode == "crash-after":
            raise Crash

    def unit(self, name):
        w = self.w
        if w.unit_error():
            raise ManagerUnavailable("get-unit")
        unit = w.units.get(name)
        if unit is None:
            return None
        if unit.stop_requested and not unit.populated():
            del w.units[name]
            return None
        if w.now - unit.created < w.prestart_for:
            return UnitView(load_state="loaded", active_state="inactive", sub_state="dead", invocation_id="", control_group=unit.cgroup,
                            main_pid=4242, exec_main_code=0, exec_main_status=0, result="success")
        main_dead = not unit.main.alive
        if main_dead:
            code, status = (2, 15) if unit.main.terminated else (2, 9) if unit.main.killed else (1, unit.main.status)
        else:
            code, status = 0, 0
        activating = w.now - unit.created < w.activating_for and not main_dead
        failed = main_dead and (code, status) != (1, 0)
        active = "activating" if activating else "deactivating" if unit.stop_requested else "failed" if failed else "active"
        return UnitView(
            load_state="loaded", active_state=active, sub_state="start" if activating else "exited" if main_dead else "running",
            invocation_id=unit.invocation, control_group="" if activating or not unit.populated() else unit.cgroup,
            main_pid=0 if main_dead else 4242, exec_main_code=code, exec_main_status=status, result="exit-code" if failed else "success",
        )

    def stop(self, name):
        unit = self.w.units.get(name)
        if unit is not None:
            unit.stop_requested = True
            if not unit.main.unkillable:
                unit.main.terminated = True

    def reset_failed(self, name):
        unit = self.w.units.get(name)
        if unit is not None and not unit.populated():
            unit.stop_requested = True


class Cgroups:
    def __init__(self, world: World):
        self.w = world

    def _unit(self, relative):
        return next((u for u in self.w.units.values() if u.cgroup == relative and u.populated()), None)

    def identity(self, relative):
        unit = self._unit(relative)
        return unit.cgroup_id if unit else (self.w.unrelated[relative][0] if relative in self.w.unrelated else None)

    def populated(self, relative, identity):
        if self.w.populated_error():
            raise OSError(errno.EIO, "events")
        unit = self._unit(relative)
        if unit is not None and unit.cgroup_id == identity:
            return True
        return relative in self.w.unrelated and self.w.unrelated[relative][0] == identity

    def kill(self, relative, identity):
        if self.w.kill_error():
            raise OSError(errno.EPERM, "kill")
        unit = self._unit(relative)
        if unit is not None and unit.cgroup_id == identity:
            self.w.kills.append(relative)
            for proc in unit.procs:
                proc.killed = True
        elif relative in self.w.unrelated and self.w.unrelated[relative][0] == identity:
            self.w.unrelated_kills.append(relative)


@pytest.fixture
def world():
    return World()


@pytest.fixture
def directory(tmp_path):
    path = tmp_path / "state"
    path.mkdir(mode=0o700)
    return path


def build(world, directory, *, ops=None, boot=None, started=True, **kwargs) -> Core:
    store = OwnershipStore(str(directory), ops=ops)
    core = Core(store, Manager(world), Cgroups(world), boot_id=boot or (lambda: world.boot), clock=world.clock,
                sleep=world.sleep, timing=kwargs.pop("timing", TIMING), spawn=lambda fn: fn(), **kwargs)
    if started:
        core.startup()
    return core


def records(directory) -> list[Record]:
    return list(OwnershipStore(str(directory)).listing().records)


def assert_owned_or_settled(world, directory):
    """The invariant: every unit with a live member has a durable record (a persistent owner), or none exists."""
    on_disk = {record.unit for record in records(directory)}
    for unit in world.live_units():
        assert unit.name in on_disk, f"{unit.name} is running and nobody durably owns it"


def clean(world, directory):
    assert world.units == {} and records(directory) == [] and not OwnershipStore(str(directory)).listing().blocking


# --- 4/14: normal results, ownership cleared only after settlement ------------------------------


@pytest.mark.parametrize(
    "status,expected",
    [(0, PrivilegedStop.STOPPED), (20, PrivilegedStop.REFUSED), (21, PrivilegedStop.NOT_SENT),
     (22, PrivilegedStop.NOT_CONFIRMED), (1, PrivilegedStop.NOT_CONFIRMED), (255, PrivilegedStop.NOT_CONFIRMED)],
)
def test_exit_statuses_keep_the_typed_mapping_and_clean_settlement_leaves_nothing(world, directory, status, expected):
    world.main_status = status
    assert build(world, directory).handle_stop() is expected
    clean(world, directory)
    assert world.starts == 1


def test_ownership_is_cleared_only_after_the_boundary_is_empty(world, directory):
    world.extra_procs = [{"lives": 0.8}]  # a late descendant outlives sudo
    seen = []
    core = build(world, directory)
    original = core._store.remove
    core._store.remove = lambda record: (seen.append(len(world.live_units())), original(record))[1]
    assert core.handle_stop() is PrivilegedStop.STOPPED
    assert seen == [0]  # the record was removed when nothing was running, and not before
    clean(world, directory)


def test_signal_death_and_a_member_that_had_to_be_killed_are_never_success(world, directory):
    world.extra_procs = [{"forever": True}]  # a descendant that never exits by itself
    assert build(world, directory).handle_stop() is PrivilegedStop.NOT_CONFIRMED
    assert world.kills and world.unrelated_kills == []
    clean(world, directory)


def test_a_late_descendant_that_exits_by_itself_is_waited_for(world, directory):
    world.extra_procs = [{"lives": 0.6}]
    result = build(world, directory).handle_stop()
    assert result is PrivilegedStop.STOPPED and world.kills == []
    clean(world, directory)


def test_timeout_stops_then_kills_and_is_never_success(world, directory):
    world.main_runs = 1_000.0
    assert build(world, directory).handle_stop() is PrivilegedStop.NOT_CONFIRMED
    clean(world, directory)


def test_a_main_process_ignoring_the_manager_stop_is_ended_through_the_recorded_cgroup(world, directory):
    world.main_runs = 1_000.0
    world.extra_procs = [{"forever": True}]
    assert build(world, directory).handle_stop() is PrivilegedStop.NOT_CONFIRMED
    assert len(world.kills) >= 1
    clean(world, directory)


def test_a_unit_that_is_created_but_not_yet_started_is_waited_for_not_handed_off(world, directory):
    world.prestart_for = 0.6  # the manager shows the new unit `inactive/dead`, already forked, with an empty InvocationID
    core = build(world, directory)
    assert core.handle_stop() is PrivilegedStop.STOPPED  # settled in line, not left to recovery
    clean(world, directory)
    assert world.starts == 1


def test_a_unit_that_never_starts_is_left_owned_and_unresolved_not_bound_to_an_empty_identity(world, directory):
    world.prestart_for = 1_000.0
    core = build(world, directory)
    assert core.handle_stop() is PrivilegedStop.HANDED_OFF
    (record,) = records(directory)
    assert record.state == START_SENT and record.invocation_id == ""  # never a bound record without the manager's identity
    assert core.handle_stop() is PrivilegedStop.BLOCKED and world.starts == 1


def test_the_launch_is_the_fixed_vector_with_the_fixed_environment(world, directory):
    build(world, directory).handle_stop()
    name, argv, executable, environment = world.last_start
    assert name.startswith("freedom-executor-stop-") and name.endswith(".service")
    assert argv == STOP_ARGV == (
        "sudo", "-n", "/usr/bin/python3.14", "-I", "-S", "/usr/local/libexec/freedom-blades-rp11/rp11_h1.py", "stop")
    assert executable == SUDO == "/usr/bin/sudo" and environment == ("PATH=/usr/bin:/bin",) and CHILD_ENV == {"PATH": "/usr/bin:/bin"}


# --- 1/2: nothing is launched unless ownership is established first ------------------------------


def test_not_ready_supervisor_admits_nothing(world, directory):
    core = build(world, directory, started=False)
    assert core.handle_stop() is PrivilegedStop.NOT_SENT and world.starts == 0


def test_a_manager_that_is_down_or_not_running_refuses_before_any_record(world, directory):
    core = build(world, directory)
    world.ready_error = True
    assert core.handle_stop() is PrivilegedStop.NOT_SENT
    assert world.starts == 0 and records(directory) == []
    with pytest.raises(ManagerUnavailable):
        build(world, directory, started=True)  # startup refuses to become ready


def test_startup_refuses_to_become_ready_without_a_writable_trusted_state(world, tmp_path):
    with pytest.raises(StoreError):
        build(world, tmp_path / "absent" / "nested")
    loose = tmp_path / "loose"
    loose.mkdir(mode=0o755)
    loose.chmod(0o755)
    with pytest.raises(StoreError):
        build(world, loose)


@pytest.mark.parametrize("failing", ["create", "write", "zero-write", "fsync", "rename"])
def test_unavailable_state_storage_refuses_before_launch(world, directory, failing):
    class Broken(FileOps):
        armed = False

        def create(self, name, dir_fd):
            if self.armed and failing == "create":
                raise OSError(errno.ENOSPC, "full")
            return super().create(name, dir_fd)

        def write(self, fd, data):
            if self.armed and failing == "write":
                raise OSError(errno.ENOSPC, "full")
            if self.armed and failing == "zero-write":
                return 0
            return super().write(fd, data)

        def fsync(self, fd):
            if self.armed and failing == "fsync":
                raise OSError(errno.EIO, "io")
            super().fsync(fd)

        def rename(self, source, target, dir_fd):
            if self.armed and failing == "rename":
                raise OSError(errno.EIO, "io")
            super().rename(source, target, dir_fd)

    ops = Broken()
    core = build(world, directory, ops=ops)
    ops.armed = True
    assert core.handle_stop() is PrivilegedStop.NOT_SENT
    assert world.starts == 0 and world.units == {} and records(directory) == []


def test_a_directory_that_changes_hands_after_ready_blocks_and_launches_nothing(world, directory):
    core = build(world, directory)
    directory.chmod(0o755)  # no longer the private directory that was checked at startup
    assert core.handle_stop() is PrivilegedStop.BLOCKED
    assert world.starts == 0


def test_a_directory_that_disappears_after_ready_blocks_and_launches_nothing(world, directory):
    core = build(world, directory)
    directory.rmdir()
    assert core.handle_stop() is PrivilegedStop.BLOCKED
    assert world.starts == 0


def test_a_failed_start_sent_write_refuses_and_nothing_is_launched(world, directory):
    class FailSecond(FileOps):
        puts = 0

        def rename(self, source, target, dir_fd):
            self.puts += 1
            if self.puts == 2:
                raise OSError(errno.EIO, "io")
            super().rename(source, target, dir_fd)

    assert build(world, directory, ops=FailSecond()).handle_stop() is PrivilegedStop.NOT_SENT
    assert world.starts == 0 and records(directory) == []


def test_the_prepared_record_is_durable_before_the_unit_is_even_looked_up(world, directory):
    core = build(world, directory)
    observed = []
    original = core._manager.unit
    core._manager.unit = lambda name: (observed.append([(r.state, r.unit) for r in records(directory)]), original(name))[1]
    core.handle_stop()
    assert observed[0] == [(PREPARED, observed[0][0][1])] and observed[0][0][1].startswith("freedom-executor-stop-")


def test_start_sent_is_durable_before_the_call_and_names_the_deterministic_unit(world, directory):
    seen = []
    manager = Manager(world)
    original = manager.start_transient

    def spy(name, argv, **kw):
        seen.append([(r.state, r.unit) for r in records(directory)])
        return original(name, argv, **kw)

    core = build(world, directory)
    core._manager.start_transient = spy
    core.handle_stop()
    (record_view,) = seen
    assert [state for state, _ in record_view] == [START_SENT] and record_view[0][1] == world.last_start[0]


def test_a_refused_start_call_clears_its_own_record_and_launches_nothing(world, directory):
    world.start_mode = "refuse"
    assert build(world, directory).handle_stop() is PrivilegedStop.NOT_SENT
    clean(world, directory)
    assert world.starts == 0


def test_a_record_blocks_every_later_admission_until_cleared(world, directory):
    core = build(world, directory)
    OwnershipStore(str(directory)).put(Record.fresh(BOOT))
    assert core.handle_stop() is PrivilegedStop.BLOCKED and world.starts == 0


# --- 3: the launch race ----------------------------------------------------------------------------


def test_recovery_running_during_the_launch_race_does_not_clear_the_prepared_record(world, directory):
    core = build(world, directory)
    passes = []
    original = core._manager.unit

    def with_recovery(name):
        passes.append((core.recover_once(), [r.state for r in records(directory)]))
        return original(name)

    core._manager.unit = with_recovery
    core.handle_stop()
    assert passes[0] == (1, [PREPARED])  # still blocking, still there, not adopted, not cleared
    assert world.starts == 1


def test_recovery_during_the_call_does_not_adopt_a_record_a_live_request_drives(world, directory):
    core = build(world, directory)
    original = core._manager.start_transient
    seen = []

    def during(name, argv, **kw):
        seen.append(core.recover_once())
        return original(name, argv, **kw)

    core._manager.start_transient = during
    core.handle_stop()
    assert seen == [1] and world.starts == 1
    clean(world, directory)


# --- 5/6/7: every post-launch path settles or stays owned ----------------------------------------


def stuck(world):
    """A privileged member in uninterruptible sleep: it ignores ``cgroup.kill`` until the I/O is released."""
    world.extra_procs = [{"unkillable": True}]


def test_an_unkillable_member_is_handed_off_with_a_durable_record_already_owning_it(world, directory):
    stuck(world)
    core = build(world, directory)
    assert core.handle_stop() is PrivilegedStop.HANDED_OFF
    (record,) = records(directory)
    assert record.state in (BOUND, CLEANUP) and record.cgroup and world.live_units()
    assert core.handle_stop() is PrivilegedStop.BLOCKED and world.starts == 1


def test_late_release_lets_recovery_clear_exactly_the_empty_boundary(world, directory):
    stuck(world)
    core = build(world, directory)
    core.handle_stop()
    assert core.recover_once() == 1 and records(directory) and world.live_units()  # still held, still blocked
    world.release()
    assert core.recover_once() == 1  # the adoption settles it
    assert core.recover_once() == 0
    clean(world, directory)
    assert world.starts == 1 and world.unrelated_kills == []


@pytest.mark.parametrize("point", ["bind-write", "cleanup-write", "remove"])
def test_state_write_failures_after_launch_never_lose_ownership(world, directory, point):
    stuck(world)

    class Late(FileOps):
        puts = 0
        armed = False

        def rename(self, source, target, dir_fd):
            self.puts += 1
            if self.armed and point in ("bind-write", "cleanup-write") and self.puts >= (3 if point == "bind-write" else 4):
                raise OSError(errno.EIO, "io")
            super().rename(source, target, dir_fd)

        def unlink(self, name, dir_fd):
            if self.armed and point == "remove":
                raise OSError(errno.EIO, "io")
            super().unlink(name, dir_fd)

    ops = Late()
    ops.armed = True
    core = build(world, directory, ops=ops)
    result = core.handle_stop()
    assert result is PrivilegedStop.HANDED_OFF
    assert_owned_or_settled(world, directory)
    assert core.handle_stop() is PrivilegedStop.BLOCKED
    world.release()
    ops.armed = False
    for _ in range(3):
        core.recover_once()
    clean(world, directory)


def test_a_failing_remove_after_settlement_keeps_the_block_and_recovery_finishes_it(world, directory):
    class NoUnlink(FileOps):
        broken = True

        def unlink(self, name, dir_fd):
            if self.broken:
                raise OSError(errno.EIO, "io")
            super().unlink(name, dir_fd)

    ops = NoUnlink()
    core = build(world, directory, ops=ops)
    assert core.handle_stop() is PrivilegedStop.HANDED_OFF  # settled, but the clearance is not durable: still owned
    assert records(directory) and core.handle_stop() is PrivilegedStop.BLOCKED
    ops.broken = False
    assert core.recover_once() == 1 and core.recover_once() == 0
    clean(world, directory)


@pytest.mark.parametrize("fault", ["unit", "populated", "kill"])
def test_every_settlement_observation_and_kill_failure_retains_ownership_and_the_block(world, directory, fault):
    stuck(world)
    world.extra_procs = [{"forever": True}, {"unkillable": True}]
    core = build(world, directory)
    if fault == "unit":
        world.unit_error = lambda: world.now > 0.45  # after the bind
    if fault == "populated":
        world.populated_error = lambda: True
    if fault == "kill":
        world.kill_error = lambda: True
    assert core.handle_stop() is PrivilegedStop.HANDED_OFF
    assert_owned_or_settled(world, directory)
    assert core.handle_stop() is PrivilegedStop.BLOCKED
    world.unit_error = world.populated_error = world.kill_error = lambda: False
    world.release()
    for _ in range(4):
        core.recover_once()
    clean(world, directory)


def test_an_ordinary_exception_during_settlement_propagates_only_with_the_member_owned(world, directory):
    stuck(world)
    core = build(world, directory)
    calls = []
    original = core._manager.unit

    def explode(name):
        calls.append(name)
        if len(calls) > 4:
            raise RuntimeError("unexpected")
        return original(name)

    core._manager.unit = explode
    with pytest.raises(RuntimeError):
        core.handle_stop()
    assert_owned_or_settled(world, directory) and world.live_units()
    assert core.handle_stop() is PrivilegedStop.BLOCKED


@pytest.mark.parametrize("fault", ["create", "write", "fsync", "rename", "unlink"])
def test_an_exception_plus_an_unkillable_member_plus_any_persistence_failure_never_leaves_it_unowned(world, directory, fault):
    stuck(world)

    class Everything(FileOps):
        armed = False

        def _maybe(self, kind):
            if self.armed and fault == kind:
                raise OSError(errno.EIO, "io")

        def create(self, name, dir_fd):
            self._maybe("create")
            return super().create(name, dir_fd)

        def write(self, fd, data):
            self._maybe("write")
            return super().write(fd, data)

        def fsync(self, fd):
            self._maybe("fsync")
            super().fsync(fd)

        def rename(self, source, target, dir_fd):
            self._maybe("rename")
            super().rename(source, target, dir_fd)

        def unlink(self, name, dir_fd):
            self._maybe("unlink")
            super().unlink(name, dir_fd)

    ops = Everything()
    core = build(world, directory, ops=ops)
    calls = []
    original = core._manager.unit

    def arm_then_explode(name):
        calls.append(1)
        if len(calls) == 3:  # after the bind: persistence now fails and an exception follows
            ops.armed = True
        if len(calls) > 6:
            raise RuntimeError("unexpected")
        return original(name)

    core._manager.unit = arm_then_explode
    with pytest.raises(RuntimeError):
        core.handle_stop()
    assert_owned_or_settled(world, directory) and world.live_units()


# --- 8: the executor dies after admission -----------------------------------------------------------


def serve(core, tmp_path):
    path = str(tmp_path / "supervisor.sock")
    server = Server(core, path)
    server.bind()
    stop = threading.Event()
    thread = threading.Thread(target=server.serve, args=(stop,), daemon=True)
    thread.start()
    return path, server, stop, thread


def conversation(path, *, kill_after_request=False, read_result=True) -> str | None:
    conn = socket.socket(socket.AF_UNIX)
    conn.settimeout(10)
    conn.connect(path)
    assert conn.recv(len(GREETING)) == GREETING
    conn.sendall(PROTOCOL_REQUEST)
    if kill_after_request:
        conn.close()
        return None
    reply = b""
    while read_result and not reply.endswith(b"\n"):
        chunk = conn.recv(64)
        if not chunk:
            break
        reply += chunk
    conn.close()
    return reply.decode()


def test_executor_sigkill_after_admission_leaves_the_owner_able_to_recover_and_blocks_a_second_call(world, directory, tmp_path):
    world.gate = threading.Event()
    core = build(world, directory)
    path, server, stop, thread = serve(core, tmp_path)
    try:
        conn = socket.socket(socket.AF_UNIX)
        conn.settimeout(10)
        conn.connect(path)
        assert conn.recv(len(GREETING)) == GREETING
        conn.sendall(PROTOCOL_REQUEST)
        assert world.reached_gate.wait(10)  # admitted: the start call is in flight
        assert [r.state for r in records(directory)] == [START_SENT]
        conn.close()  # the executor is SIGKILLed here
        assert conversation(path) == "result blocked\n"  # a second executor is refused while the first is in flight
        world.gate.set()
        for _ in range(500):
            if not records(directory):
                break
            threading.Event().wait(0.01)
    finally:
        stop.set()
        thread.join(5)
        server.close()
    clean(world, directory)
    assert world.starts == 1  # SA-2 ran once, and was not retried


def test_the_client_that_vanished_before_the_start_aborts_the_launch(world, directory, tmp_path):
    world.gate = threading.Event()
    core = build(world, directory)
    seen = []
    core._manager.unit = (lambda original: lambda name: (seen.append(name), original(name))[1])(core._manager.unit)
    # Hang the request in the unit lookup; the peer disappears; the supervisor must not start anything.
    release = threading.Event()
    reached = threading.Event()
    original = core._manager.unit

    def hold(name):
        reached.set()
        release.wait(10)
        return original(name)

    core._manager.unit = hold
    path, server, stop, thread = serve(core, tmp_path)
    try:
        conversation(path, kill_after_request=True)
        assert reached.wait(10)
        threading.Event().wait(0.05)
        release.set()
        for _ in range(500):
            if not records(directory):
                break
            threading.Event().wait(0.01)
    finally:
        stop.set()
        thread.join(5)
        server.close()
    assert world.starts == 0 and records(directory) == []


# --- 9: supervisor death and restart while a member is in uninterruptible sleep -----------------


def test_supervisor_restart_keeps_containment_state_and_the_block_until_the_io_is_released(world, directory):
    stuck(world)
    first = build(world, directory)
    assert first.handle_stop() is PrivilegedStop.HANDED_OFF
    before = (records(directory), [u.name for u in world.live_units()])
    second = build(world, directory)  # the restarted supervisor: a new process over the same state and manager
    assert second.handle_stop() is PrivilegedStop.BLOCKED
    for _ in range(3):
        assert second.recover_once() == 1
        assert (records(directory), [u.name for u in world.live_units()])[1] == before[1] and records(directory)
    assert second.handle_stop() is PrivilegedStop.BLOCKED and world.starts == 1
    world.release()
    assert second.recover_once() == 1
    assert second.recover_once() == 0
    clean(world, directory)
    assert world.starts == 1


def test_a_bound_live_invocation_is_adopted_by_a_restarted_supervisor_and_settled(world, directory):
    world.main_runs = 5.0
    first = build(world, directory)
    original = first._settle
    first._settle = lambda record: (_ for _ in ()).throw(Crash)  # the supervisor dies right after binding
    with pytest.raises(Crash):
        first.handle_stop()
    (record,) = records(directory)
    assert record.state == BOUND and world.live_units()
    second = build(world, directory)
    assert second.handle_stop() is PrivilegedStop.BLOCKED
    assert second.recover_once() == 1
    clean(world, directory)
    assert world.starts == 1


# --- 10: crashes before, during and after StartTransientUnit -----------------------------------------


def test_crash_before_start_sent_clears_by_name_and_never_launches(world, directory):
    first = build(world, directory)
    original = first._store.put
    calls = []

    def crash_on_second(record):
        calls.append(record.state)
        if record.state == START_SENT:
            raise Crash
        return original(record)

    first._store.put = crash_on_second
    with pytest.raises(Crash):
        first.handle_stop()
    assert [r.state for r in records(directory)] == [PREPARED]
    second = build(world, directory)
    assert second.handle_stop() is PrivilegedStop.BLOCKED
    assert second.recover_once() == 1  # a prepared record, no unit: the call was never sent
    clean(world, directory)
    assert world.starts == 0


def test_crash_before_the_call_leaves_a_start_sent_record_that_only_a_new_boot_clears(world, directory):
    world.start_mode = "crash-before"
    with pytest.raises(Crash):
        build(world, directory).handle_stop()
    assert [r.state for r in records(directory)] == [START_SENT]
    world.start_mode = "ok"
    second = build(world, directory)
    for _ in range(40):  # far beyond every former resolution deadline, with the unit absent on every read
        world.now += 10.0
        assert second.recover_once() == 1
        assert [r.state for r in records(directory)] == [START_SENT] and second.handle_stop() is PrivilegedStop.BLOCKED
    assert world.starts == 0 and world.start_calls == 1  # the start was never re-sent
    world.boot = OTHER_BOOT  # a reboot: the old boot's request and cgroup cannot survive
    assert build(world, directory).recover_once() == 0
    clean(world, directory)
    assert world.starts == 0 and world.start_calls == 1


@pytest.mark.parametrize("mode", ["crash-after", "lost-after"])
def test_crash_during_or_after_the_call_resolves_the_deterministic_unit_with_exactly_one_launch(world, directory, mode):
    world.start_mode = mode
    first = build(world, directory)
    if mode == "crash-after":
        with pytest.raises(Crash):
            first.handle_stop()
        assert [r.state for r in records(directory)] == [START_SENT] and world.starts == 1
        second = build(world, directory)
        assert second.handle_stop() is PrivilegedStop.BLOCKED
        second.recover_once()
    else:
        assert first.handle_stop() is PrivilegedStop.STOPPED  # the reply was lost; the unit was found by name and settled
    clean(world, directory)
    assert world.starts == 1


def test_an_acknowledged_start_whose_binding_was_never_recorded_is_resolved_by_name(world, directory):
    world.main_runs = 5.0
    first = build(world, directory)
    original = first._store.put

    def crash_on_bound(record):
        if record.state == BOUND:
            raise Crash
        return original(record)

    first._store.put = crash_on_bound
    with pytest.raises(Crash):
        first.handle_stop()
    assert [r.state for r in records(directory)] == [START_SENT] and world.live_units()
    second = build(world, directory)
    second.recover_once()
    clean(world, directory)
    assert world.starts == 1


def test_a_lost_start_reply_with_no_unit_stays_owned_and_is_never_resent(world, directory):
    world.start_mode = "lost-before"
    core = build(world, directory)
    assert core.handle_stop() is PrivilegedStop.HANDED_OFF  # unresolved, not "never started"
    assert [r.state for r in records(directory)] == [START_SENT]
    for _ in range(40):
        world.now += 10.0
        assert core.recover_once() == 1
    assert core.handle_stop() is PrivilegedStop.BLOCKED
    assert world.starts == 0 and world.start_calls == 1


def test_a_refused_start_is_definite_and_still_clears_immediately(world, directory):
    world.start_mode = "refuse"
    assert build(world, directory).handle_stop() is PrivilegedStop.NOT_SENT
    clean(world, directory)


def test_a_delayed_unit_appearing_long_after_is_adopted_and_settled_exactly_once(world, directory):
    world.start_mode = "crash-before"
    with pytest.raises(Crash):
        build(world, directory).handle_stop()
    (record,) = records(directory)
    world.start_mode = "ok"
    second = build(world, directory)
    for _ in range(40):
        world.now += 10.0
        assert second.recover_once() == 1
    world.starts += 1  # the queued request finally lands: the manager creates the deterministic unit
    world.create(record.unit)
    world.main_runs = 0.3
    assert second.recover_once() == 1  # adopted
    assert second.recover_once() == 0
    clean(world, directory)
    assert world.starts == 1 and world.start_calls == 1  # settled once; StartTransientUnit was never issued again
    assert second.handle_stop() is PrivilegedStop.STOPPED  # the block ended with the settlement, and only then
    assert world.start_calls == 2


def test_a_prepared_record_with_affirmative_absence_still_clears_and_start_sent_clears_on_a_new_boot(world, directory):
    store = OwnershipStore(str(directory))
    store.put(Record.fresh(BOOT))  # prepared: the start-sent commit never happened, so the call cannot have been issued
    core = build(world, directory)
    assert core.recover_once() == 1 and records(directory) == []
    store.put(Record.fresh(OTHER_BOOT).to(START_SENT))  # an old boot's ambiguous request is gone with that boot
    assert core.recover_once() == 0 and records(directory) == []
    assert world.starts == 0 and world.start_calls == 0


# --- 11: concurrency ----------------------------------------------------------------------------


def test_two_concurrent_executor_calls_launch_at_most_one_invocation(world, directory, tmp_path):
    world.gate = threading.Event()
    core = build(world, directory)
    path, server, stop, thread = serve(core, tmp_path)
    results = []

    def call():
        results.append(conversation(path))

    try:
        first = threading.Thread(target=call)
        first.start()
        assert world.reached_gate.wait(10)
        others = [threading.Thread(target=call) for _ in range(5)]
        for item in others:
            item.start()
        for item in others:
            item.join(10)
        world.gate.set()
        first.join(10)
    finally:
        stop.set()
        thread.join(5)
        server.close()
    assert sorted(results) == ["result blocked\n"] * 5 + ["result stopped\n"] and world.starts == 1
    clean(world, directory)


# --- 12: damaged, planted, replaced, renamed, stale records ---------------------------------------------


def write_raw(directory, name, data, mode=0o600):
    path = directory / name
    path.write_bytes(data)
    path.chmod(mode)


def test_malformed_planted_renamed_and_link_entries_block_and_are_never_cleared_or_acted_on(world, directory, tmp_path):
    victim = world.plant_unrelated("victim.service")
    forged = Record.fresh(BOOT).to(BOUND, invocation_id="ab" * 16, cgroup=victim, cgroup_id=world.unrelated[victim][0])
    write_raw(directory, forged.filename, forged.encode())  # a cgroup that is not this unit's: not a record at all
    other = Record.fresh(BOOT)
    write_raw(directory, f"rec-{other.nonce}.json", other.encode())  # a record under any name but the one slot
    write_raw(directory, "rec-" + "1" * 32 + ".json", b"not json")
    os.symlink(tmp_path, directory / ("rec-" + "2" * 32 + ".json"))
    core = build(world, directory)
    for _ in range(3):
        assert core.recover_once() == 4
    assert core.handle_stop() is PrivilegedStop.BLOCKED
    assert world.unrelated_kills == [] and world.starts == 0 and len(os.listdir(directory)) == 4


def test_a_stale_record_for_a_cgroup_that_is_gone_or_reused_clears_without_killing_anything(world, directory):
    victim = world.plant_unrelated("victim.service")
    stale = Record.fresh(BOOT)
    reused = stale.to(BOUND, invocation_id="cd" * 16, cgroup=CG_BASE + stale.unit, cgroup_id=424242)
    OwnershipStore(str(directory)).put(reused)
    world.unrelated[CG_BASE + stale.unit] = (777, Proc(world))  # another cgroup now lives at that path (different identity)
    core = build(world, directory)
    core.recover_once()
    assert records(directory) == [] and world.unrelated_kills == [] and world.kills == []
    assert victim in world.unrelated


def test_a_prepared_record_replacing_a_live_binding_still_leaves_the_invocation_owned_and_settled(world, directory):
    stuck(world)
    first = build(world, directory)
    first.handle_stop()
    (record,) = records(directory)
    OwnershipStore(str(directory)).put(Record(record.nonce, record.boot))  # rolled back to `prepared`
    second = build(world, directory)
    assert second.recover_once() == 1 and world.live_units() and records(directory)  # not cleared as "never sent"
    world.release()
    second.recover_once()
    second.recover_once()
    clean(world, directory)


def test_a_binding_with_another_invocation_id_is_never_judged_empty_or_killed(world, directory):
    stuck(world)
    first = build(world, directory)
    first.handle_stop()
    (record,) = records(directory)
    OwnershipStore(str(directory)).put(record.to(BOUND, invocation_id="ee" * 16))
    kills_before = len(world.kills)
    second = build(world, directory)
    for _ in range(3):
        second.recover_once()
    assert records(directory) and world.live_units() and len(world.kills) == kills_before
    world.release()
    assert second.handle_stop() is PrivilegedStop.BLOCKED


def test_records_of_another_boot_are_cleared_by_the_reboot_and_only_then(world, directory):
    stuck(world)
    first = build(world, directory)
    first.handle_stop()
    assert records(directory)
    same_boot = build(world, directory)
    same_boot.recover_once()
    assert records(directory)  # the same boot: disappearance is not assumed
    world.units.clear()  # a reboot ends every unit and cgroup
    world.boot = OTHER_BOOT
    rebooted = build(world, directory)
    assert rebooted.recover_once() == 0
    assert records(directory) == []


def test_a_record_with_an_absent_unit_and_cgroup_on_the_same_boot_is_empty_only_by_that_evidence(world, directory):
    base = Record.fresh(BOOT)
    stale = base.to(BOUND, invocation_id="cd" * 16, cgroup=CG_BASE + base.unit, cgroup_id=5)
    OwnershipStore(str(directory)).put(stale)
    core = build(world, directory)
    world.unit_error = lambda: True  # the manager cannot answer: not evidence of anything
    assert core.recover_once() == 1 and records(directory)
    world.unit_error = lambda: False
    assert core.recover_once() == 1 and records(directory) == []  # the affirmative answer (no unit, no cgroup) clears it
    assert core.recover_once() == 0


# --- 13: bounded work ------------------------------------------------------------------------------------


def test_junk_flood_is_bounded_blocks_and_does_not_starve_the_real_invocation(world, directory):
    stuck(world)
    first = build(world, directory)
    first.handle_stop()
    for index in range(500):
        write_raw(directory, f"junk-{index}", b"x")
    second = build(world, directory)
    assert second.recover_once() >= 501
    world.release()
    second.recover_once()
    second.recover_once()
    assert [r for r in records(directory)] == [] and len(os.listdir(directory)) == 500  # the real one finished; junk still blocks
    assert second.handle_stop() is PrivilegedStop.BLOCKED


def test_junk_beyond_the_entry_limit_created_before_the_real_record_cannot_hide_or_starve_it(world, directory):
    from adapters.executor.ownership import MAX_ENTRIES

    for index in range(3 * MAX_ENTRIES):  # created first: a scan that stops at the limit would never reach the record
        write_raw(directory, f"a-{index:05d}", b"x")
    world.main_runs = 5.0
    record = Record.fresh(BOOT).to(START_SENT)
    OwnershipStore(str(directory)).put(record)
    world.starts += 1
    world.create(record.unit)  # the real invocation exists and is owned by the slot
    core = build(world, directory)
    assert core.handle_stop() is PrivilegedStop.BLOCKED
    core.recover_once()
    world.now += 6.0
    core.recover_once()
    assert records(directory) == [] and world.live_units() == []  # driven to a clear boundary on every pass, despite the flood
    assert core.recover_once() >= 4096  # the junk (bounded at the scan limit) keeps blocking admission
    assert core.handle_stop() is PrivilegedStop.BLOCKED and world.start_calls == 0


def test_malformed_and_overflow_state_blocks_admission_but_the_real_invocation_still_gets_cleanup(world, directory):
    from adapters.executor.ownership import MAX_ENTRIES

    stuck(world)
    first = build(world, directory)
    assert first.handle_stop() is PrivilegedStop.HANDED_OFF
    write_raw(directory, "rec-" + "3" * 32 + ".json", b"garbage")
    write_raw(directory, "notes", b"x")
    for index in range(MAX_ENTRIES + 50):
        write_raw(directory, f"z-{index:05d}", b"x")
    second = build(world, directory)
    assert second.recover_once() >= 2 and second.handle_stop() is PrivilegedStop.BLOCKED
    world.release()
    second.recover_once()
    second.recover_once()
    assert records(directory) == [] and world.live_units() == []  # the invocation got its cleanup
    assert second.handle_stop() is PrivilegedStop.BLOCKED and world.start_calls == 1  # the damage still blocks, nothing launched


def test_recovery_reads_a_bounded_number_of_names_and_never_opens_junk(world, directory, monkeypatch):
    from adapters.executor.ownership import MAX_ENTRIES

    for index in range(2 * MAX_ENTRIES):
        write_raw(directory, f"j-{index:05d}", b"x")
    core = build(world, directory)
    opened = []
    real = os.open
    monkeypatch.setattr(os, "open", lambda *a, **k: (opened.append(a[0]), real(*a, **k))[1])
    core.recover_once()
    assert not [name for name in opened if isinstance(name, str) and name.startswith("j-")]
    assert len(opened) <= 4


# --- the socket protocol: absent, stopped, starting, stale, malformed owners -------------------------------


def invoker(path, **kw):
    return SudoStopInvoker(socket_path=path, deadline_seconds=kw.pop("deadline_seconds", 5.0), **kw)


def test_absent_owner_refuses_without_connecting(tmp_path):
    assert invoker(str(tmp_path / "none.sock")).invoke_stop() is PrivilegedStop.NOT_SENT


def test_stale_socket_file_with_no_listener_refuses(tmp_path):
    path = str(tmp_path / "stale.sock")
    sock = socket.socket(socket.AF_UNIX)
    sock.bind(path)
    sock.close()  # the file stays, nobody listens
    assert os.path.exists(path) and invoker(path).invoke_stop() is PrivilegedStop.NOT_SENT


def test_a_regular_file_or_a_foreign_owner_is_not_a_supervisor(tmp_path):
    plain = tmp_path / "plain"
    plain.write_text("x")
    assert invoker(str(plain)).invoke_stop() is PrivilegedStop.NOT_SENT
    other = invoker(str(tmp_path / "x.sock"), uid=os.getuid() + 1)
    assert other.invoke_stop() is PrivilegedStop.NOT_SENT


def listener(tmp_path, behaviour):
    path = str(tmp_path / "fake.sock")
    sock = socket.socket(socket.AF_UNIX)
    sock.bind(path)
    sock.listen(1)

    def run():
        conn, _ = sock.accept()
        behaviour(conn)
        conn.close()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return path, sock, thread


def read_exact_request(conn, timeout=5.0):
    """Hold exactly the complete fixed request followed by EOF: stream sockets keep no message boundaries.

    A single ``recv`` may legally return exactly ``len(PROTOCOL_REQUEST)`` bytes and leave a surplus queued, so
    absence of surplus is proved by the test client's half-close (a test-only framing, not production client
    behaviour): read until EOF, retaining no more than ``len(PROTOCOL_REQUEST) + 1`` bytes. Short input, wrong
    input, surplus and timeout all fail; the caller may publish "the peer holds the whole line" only afterwards.
    """
    want = len(PROTOCOL_REQUEST)
    deadline = time.monotonic() + timeout
    got = b""
    while True:
        conn.settimeout(max(deadline - time.monotonic(), 0.001))
        chunk = conn.recv(want + 1 - len(got))  # never retains more than one byte beyond the request
        if not chunk:
            break
        got += chunk
        if len(got) > want or not PROTOCOL_REQUEST.startswith(got):
            raise AssertionError(f"request {got!r} is not the fixed request (surplus or wrong value)")
    if got != PROTOCOL_REQUEST:
        raise AssertionError(f"EOF after {len(got)} of {want} request bytes")
    return got


def exact_request_peer(seen, errors, crossed, then=None):
    """Peer behaviour: greet, read the complete request, only then publish ``crossed``."""

    def peer(conn):
        try:
            conn.sendall(GREETING)
            seen.append(read_exact_request(conn))
        except BaseException as exc:  # reported to the test thread, never swallowed
            errors.append(exc)
            return
        crossed.set()
        if then is not None:
            then()

    return peer


def test_the_exact_request_reader_accumulates_prefixes_and_rejects_every_other_shape():
    def feed(chunks, close=True):
        a, b = socket.socketpair()
        try:
            for chunk in chunks:
                a.sendall(chunk)
            if close:
                a.shutdown(socket.SHUT_WR)
            return read_exact_request(b, timeout=0.5)
        finally:
            a.close()
            b.close()

    assert feed([PROTOCOL_REQUEST[:2], PROTOCOL_REQUEST[2:5], PROTOCOL_REQUEST[5:]]) == PROTOCOL_REQUEST
    for bad in ([PROTOCOL_REQUEST[:-1]], [PROTOCOL_REQUEST + b"x"], [b"x" * len(PROTOCOL_REQUEST)]):
        with pytest.raises(AssertionError):
            feed(bad)
    with pytest.raises(OSError):  # timeout: no EOF, no further bytes
        feed([PROTOCOL_REQUEST[:3]], close=False)


def test_the_exact_request_reader_rejects_a_surplus_delivered_in_a_separate_read():
    """The legal stream shape a single-recv reader missed: the exact request first, a surplus byte queued behind it."""

    class OneRequestPerRead:
        def __init__(self, conn):
            self._conn = conn

        def settimeout(self, seconds):
            self._conn.settimeout(seconds)

        def recv(self, size):
            return self._conn.recv(min(size, len(PROTOCOL_REQUEST)))

    a, b = socket.socketpair()
    try:
        a.sendall(PROTOCOL_REQUEST)
        a.sendall(b"x")
        a.shutdown(socket.SHUT_WR)
        with pytest.raises(AssertionError, match="surplus"):
            read_exact_request(OneRequestPerRead(b), timeout=0.5)
    finally:
        a.close()
        b.close()


def test_a_peer_that_does_not_greet_exactly_receives_no_request(tmp_path):
    received = []

    def silent(conn):
        conn.settimeout(0.5)
        try:
            received.append(conn.recv(64))
        except OSError:
            received.append(b"")

    path, sock, thread = listener(tmp_path, lambda c: (c.sendall(b"hello\n"), silent(c)))
    assert invoker(path).invoke_stop() is PrivilegedStop.NOT_SENT
    thread.join(5)
    sock.close()
    assert received == [b""]


def test_a_greeted_request_with_a_malformed_or_missing_answer_is_owned_not_success(tmp_path):
    for answer in (b"result stopped", b"result bogus\n", b"", b"result  stopped\n", b"x" * 200):
        path, sock, thread = listener(
            tmp_path, lambda c, a=answer: (c.sendall(GREETING), c.recv(64), c.sendall(a)))
        assert invoker(path).invoke_stop() is PrivilegedStop.HANDED_OFF
        thread.join(5)
        sock.close()
        os.unlink(path)


def test_a_request_write_error_is_owned_because_the_complete_line_may_have_crossed(monkeypatch):
    class AmbiguousWrite:
        def __init__(self):
            self.greeting = GREETING
            self.write_attempted = False

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return None

        def settimeout(self, _seconds):
            pass

        def recv(self, size, *_flags):
            data, self.greeting = self.greeting[:size], self.greeting[size:]
            return data

        def sendall(self, data):
            assert data == PROTOCOL_REQUEST
            self.write_attempted = True
            raise BrokenPipeError

    conn = AmbiguousWrite()
    monkeypatch.setattr("adapters.executor.interrupt.peer_uid", lambda _conn: os.getuid())
    outcome = SudoStopInvoker(connect=lambda *_: conn).invoke_stop()
    assert conn.write_attempted and outcome is PrivilegedStop.HANDED_OFF


@pytest.mark.parametrize("failure", ["connect", "peer", "greeting-read", "wrong-greeting"])
def test_a_failure_before_the_request_write_is_not_sent_and_never_writes(monkeypatch, failure):
    class Conn:
        def __init__(self):
            self.sent = []

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return None

        def settimeout(self, _seconds):
            pass

        def recv(self, size, *_flags):
            if failure == "greeting-read":
                raise ConnectionResetError
            return (b"x" * size) if failure == "wrong-greeting" else GREETING[:size]

        def sendall(self, data):
            self.sent.append(data)

    conn = Conn()

    def connect(*_):
        if failure == "connect":
            raise FileNotFoundError
        return conn

    monkeypatch.setattr("adapters.executor.interrupt.peer_uid",
                        lambda _conn: os.getuid() + 1 if failure == "peer" else os.getuid())
    assert SudoStopInvoker(connect=connect).invoke_stop() is PrivilegedStop.NOT_SENT
    assert conn.sent == []


def test_a_request_write_after_the_complete_line_crossed_is_owned_never_retryable(tmp_path):
    """The peer holds the whole line, then the local write reports an error: still HANDED_OFF."""
    seen, errors, crossed = [], [], threading.Event()
    path, sock, thread = listener(tmp_path, exact_request_peer(seen, errors, crossed))
    real = socket.socket.sendall
    calls, order, injected = [], [], []

    def sendall_then_fail(self, data, *args):
        real(self, data, *args)
        if data == PROTOCOL_REQUEST:
            self.shutdown(socket.SHUT_WR)  # test-only framing: lets the peer prove EOF after the exact request
            calls.append(data)
            order.append(crossed.wait(5))  # True only once the peer holds the complete line
            injected.append(BrokenPipeError)
            raise BrokenPipeError  # always injected, whatever the wait returned

    from unittest import mock

    try:
        with mock.patch.object(socket.socket, "sendall", sendall_then_fail):
            outcome = invoker(path).invoke_stop()
    finally:
        thread.join(5)
        sock.close()
    assert errors == [] and order == [True] and injected == [BrokenPipeError] and not thread.is_alive()
    assert seen == [PROTOCOL_REQUEST] and calls == [PROTOCOL_REQUEST] and outcome is PrivilegedStop.HANDED_OFF


class ScriptedConn:
    """A controlled connection: a greeting, then a scripted failure at one named phase."""

    def __init__(self, *, send=None, recv_reply=None, enter=None, exit_=None, reply=b""):
        self.greeting = GREETING
        self.reply = reply
        self.script = {"send": send, "reply": recv_reply, "exit": exit_}
        self.sent = []
        self.closed = 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.closed += 1
        if self.script["exit"] is not None:
            raise self.script["exit"]

    def settimeout(self, _seconds):
        return None

    def recv(self, size, *_flags):
        if self.greeting:
            data, self.greeting = self.greeting[:size], self.greeting[size:]
            return data
        if self.script["reply"] is not None:
            raise self.script["reply"]
        data, self.reply = self.reply[:size], self.reply[size:]
        return data

    def sendall(self, data):
        self.sent.append(data)
        if self.script["send"] is not None:
            raise self.script["send"]


def scripted_stop(monkeypatch, **script):
    conn = ScriptedConn(**script)
    connects = []
    monkeypatch.setattr("adapters.executor.interrupt.peer_uid", lambda _conn: os.getuid())
    outcome = SudoStopInvoker(connect=lambda *a: (connects.append(a), conn)[1]).invoke_stop()
    return outcome, conn, connects


@pytest.mark.parametrize("interruption", [KeyboardInterrupt, SystemExit, GeneratorExit, ValueError, OSError])
def test_an_interruption_from_sendall_before_its_extent_is_knowable_is_owned(monkeypatch, interruption):
    outcome, conn, connects = scripted_stop(monkeypatch, send=interruption())
    assert outcome is PrivilegedStop.HANDED_OFF
    assert conn.sent == [PROTOCOL_REQUEST] and len(connects) == 1
    assert conn.closed == 1


@pytest.mark.parametrize("interruption", [KeyboardInterrupt, SystemExit, BrokenPipeError])
def test_an_interruption_while_waiting_for_the_reply_is_owned(monkeypatch, interruption):
    outcome, conn, connects = scripted_stop(monkeypatch, recv_reply=interruption())
    assert outcome is PrivilegedStop.HANDED_OFF
    assert conn.sent == [PROTOCOL_REQUEST] and len(connects) == 1


@pytest.mark.parametrize("failure", [KeyboardInterrupt(), SystemExit(), OSError(errno.EIO, "close")])
@pytest.mark.parametrize("reply", [b"", b"result stopped\n", b"garbage"])
def test_a_connection_context_failure_after_the_write_is_owned_even_after_an_exact_result(
        monkeypatch, failure, reply):
    outcome, conn, connects = scripted_stop(monkeypatch, exit_=failure, reply=reply)
    assert outcome is PrivilegedStop.HANDED_OFF
    assert conn.sent == [PROTOCOL_REQUEST] and len(connects) == 1


def test_an_exact_result_without_a_later_boundary_failure_keeps_its_typed_result(monkeypatch):
    for token, expected in ((o.value, o) for o in PrivilegedStop):
        outcome, conn, _ = scripted_stop(monkeypatch, reply=f"result {token}\n".encode())
        assert outcome is expected and conn.sent == [PROTOCOL_REQUEST]


@pytest.mark.parametrize("interruption", [KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("phase", ["greeting", "peer"])
def test_an_interruption_before_the_write_is_not_swallowed_and_writes_nothing(monkeypatch, interruption, phase):
    conn = ScriptedConn()
    conn.greeting = b""
    if phase == "greeting":
        conn.script["reply"] = interruption()

    def peer(_conn):
        if phase == "peer":
            raise interruption()
        return os.getuid()

    monkeypatch.setattr("adapters.executor.interrupt.peer_uid", peer)
    with pytest.raises(interruption):
        SudoStopInvoker(connect=lambda *_: conn).invoke_stop()
    assert conn.sent == [] and conn.closed == 1


def test_a_failure_closing_a_connection_that_was_never_written_to_is_not_sent(monkeypatch):
    conn = ScriptedConn(exit_=OSError(errno.EIO, "close"))
    conn.greeting = b"x" * len(GREETING)
    monkeypatch.setattr("adapters.executor.interrupt.peer_uid", lambda _conn: os.getuid())
    assert SudoStopInvoker(connect=lambda *_: conn).invoke_stop() is PrivilegedStop.NOT_SENT
    assert conn.sent == []


def test_a_keyboard_interrupt_after_the_complete_line_crossed_is_owned_never_retryable(tmp_path):
    """Real socket: the peer holds the whole request before the local interruption is reported."""
    seen, errors, crossed = [], [], threading.Event()
    path, sock, thread = listener(tmp_path, exact_request_peer(seen, errors, crossed))
    real = socket.socket.sendall
    calls, order = [], []

    def sendall_then_interrupt(self, data, *args):
        real(self, data, *args)
        if data == PROTOCOL_REQUEST:
            self.shutdown(socket.SHUT_WR)  # test-only framing: lets the peer prove EOF after the exact request
            calls.append(data)
            order.append(crossed.wait(5))  # True only once the peer holds the complete line
            raise KeyboardInterrupt

    from unittest import mock

    try:
        with mock.patch.object(socket.socket, "sendall", sendall_then_interrupt):
            outcome = invoker(path).invoke_stop()
    finally:
        thread.join(5)
        sock.close()
    assert errors == [] and order == [True] and not thread.is_alive()
    assert seen == [PROTOCOL_REQUEST] and calls == [PROTOCOL_REQUEST] and outcome is PrivilegedStop.HANDED_OFF


def test_a_keyboard_interrupt_while_the_supervisor_has_the_request_and_no_reply_is_owned(tmp_path):
    """Real socket: the peer holds the complete request and the answer when the local wait is interrupted."""
    seen, errors, crossed, release = [], [], threading.Event(), threading.Event()
    path, sock, thread = listener(tmp_path, exact_request_peer(seen, errors, crossed, lambda: release.wait(10)))
    real_recv, real_sendall = socket.socket.recv, socket.socket.sendall
    waits, replying = [], []

    def sendall_wait(self, data, *args):
        real_sendall(self, data, *args)
        if data == PROTOCOL_REQUEST:
            self.shutdown(socket.SHUT_WR)  # test-only framing: lets the peer prove EOF after the exact request
            waits.append(crossed.wait(5))  # the reply wait starts only once the peer holds the whole line

    def recv_then_interrupt(self, size, *args):
        if not crossed.is_set():
            return real_recv(self, size, *args)  # the greeting
        replying.append(size)
        raise KeyboardInterrupt

    from unittest import mock

    try:
        with mock.patch.object(socket.socket, "sendall", sendall_wait), \
                mock.patch.object(socket.socket, "recv", recv_then_interrupt):
            outcome = invoker(path).invoke_stop()
    finally:
        release.set()
        thread.join(5)
        sock.close()
    assert errors == [] and waits == [True] and not thread.is_alive()
    assert seen == [PROTOCOL_REQUEST] and len(replying) == 1 and outcome is PrivilegedStop.HANDED_OFF


def test_a_client_deadline_is_an_owned_hand_off_never_success(tmp_path):
    gate = threading.Event()
    path, sock, thread = listener(tmp_path, lambda c: (c.sendall(GREETING), c.recv(64), gate.wait(10)))
    assert invoker(path, deadline_seconds=0.3).invoke_stop() is PrivilegedStop.HANDED_OFF
    gate.set()
    thread.join(5)
    sock.close()


def test_every_defined_result_token_round_trips(world, directory, tmp_path):
    core = build(world, directory)
    path, server, stop, thread = serve(core, tmp_path)
    try:
        assert invoker(path).invoke_stop() is PrivilegedStop.STOPPED
        world.main_status = 20
        assert invoker(path).invoke_stop() is PrivilegedStop.REFUSED
        core.ready = False  # the owner is starting or stopping: it greets nobody
        assert invoker(path).invoke_stop() is PrivilegedStop.NOT_SENT
    finally:
        stop.set()
        thread.join(5)
        server.close()
    assert world.starts == 2


def test_a_server_with_a_foreign_owned_stale_path_does_not_unlink_it(world, directory, tmp_path):
    victim = tmp_path / "supervisor.sock"
    victim.write_text("not a socket")
    with pytest.raises(OSError):
        Server(build(world, directory), str(victim)).bind()
    assert victim.read_text() == "not a socket"


def test_an_unexpected_fault_in_a_request_handler_still_leaves_a_durable_record(world, directory, tmp_path):
    stuck(world)
    core = build(world, directory)
    original = core._manager.unit
    count = []

    def explode(name):
        count.append(1)
        if len(count) > 4:
            raise RuntimeError("bug")
        return original(name)

    core._manager.unit = explode
    path, server, stop, thread = serve(core, tmp_path)
    try:
        assert invoker(path).invoke_stop() is PrivilegedStop.HANDED_OFF  # no reply: owned, never success
    finally:
        stop.set()
        thread.join(5)
        server.close()
    assert_owned_or_settled(world, directory) and world.live_units()


# --- the service loop: readiness before the socket ---------------------------------------------------------


def test_the_socket_exists_only_after_the_owner_is_ready(world, directory, tmp_path):
    from adapters.executor.supervisor import run

    path = str(tmp_path / "supervisor.sock")
    core = build(world, directory, started=False)
    world.ready_error = True  # the user manager is not running: the owner must not become ready or listen
    with pytest.raises(ManagerUnavailable):
        run(core, Server(core, path), threading.Event())
    assert not os.path.exists(path) and not core.ready

    world.ready_error = False
    stop = threading.Event()
    done = []
    thread = threading.Thread(target=lambda: done.append(run(core, Server(core, path), stop)))
    thread.start()
    try:
        for _ in range(500):
            if os.path.exists(path):
                break
            threading.Event().wait(0.01)
        assert core.ready and os.path.exists(path)
        assert invoker(path).invoke_stop() is PrivilegedStop.STOPPED
    finally:
        stop.set()
        thread.join(10)
    assert done == [0] and not os.path.exists(path)  # a clean stop leaves no socket for a stale client


def test_ready_is_published_only_after_the_serving_worker_runs_and_an_immediate_client_is_served(world, directory, tmp_path, monkeypatch):
    from adapters.executor import supervisor

    path = str(tmp_path / "supervisor.sock")
    core = build(world, directory, started=False)
    server = Server(core, path)
    seen = {}

    def ready(message):
        if message != b"READY=1":
            return
        workers = [t for t in threading.enumerate() if getattr(t, "_target", None) == server.serve]
        seen["worker_alive"] = bool(workers) and all(t.is_alive() for t in workers)
        seen["socket_listening"] = os.path.exists(path)
        seen["outcome"] = invoker(path).invoke_stop()  # the client that arrives at the instant of readiness

    monkeypatch.setattr(supervisor, "notify", ready)
    stop = threading.Event()
    done = []
    thread = threading.Thread(target=lambda: done.append(supervisor.run(core, server, stop)))
    thread.start()
    try:
        for _ in range(1000):
            if "outcome" in seen:
                break
            threading.Event().wait(0.01)
    finally:
        stop.set()
        thread.join(10)
    assert seen == {"worker_alive": True, "socket_listening": True, "outcome": PrivilegedStop.STOPPED}
    assert done == [0]


def test_a_serving_worker_that_dies_after_ready_ends_the_service_nonzero(world, directory, tmp_path, monkeypatch):
    from adapters.executor import supervisor

    core = build(world, directory, started=False)
    server = Server(core, str(tmp_path / "supervisor.sock"))
    monkeypatch.setattr(server, "serve", lambda _stop: None)  # the accept loop is gone as soon as it starts
    monkeypatch.setattr(supervisor, "notify", lambda _message: None)
    assert supervisor.run(core, server, threading.Event()) == 70


# --- maintenance drain: atomic with admission ------------------------------------------------------------

from adapters.executor.protocol import DRAIN_EMPTY, DRAIN_PENDING, DRAIN_REQUEST  # noqa: E402

ME = os.getuid()


def drain_conversation(path, request=DRAIN_REQUEST, *, hold=False):
    """(greeting seen, answer, still-open connection or None)."""
    conn = socket.socket(socket.AF_UNIX)
    conn.settimeout(10)
    conn.connect(path)
    greeted = conn.recv(len(GREETING))
    try:
        conn.sendall(request)
        answer = conn.recv(64)
    except OSError:  # the peer hung up on us
        answer = b""
    if hold:
        return greeted, answer, conn
    conn.close()
    return greeted, answer, None


def test_drain_closes_admission_for_good_and_answers_empty_only_when_nothing_exists(world, directory):
    core = build(world, directory)
    assert core.drain() is True
    assert core.handle_stop() is PrivilegedStop.NOT_SENT  # refused before a record or a launch
    assert records(directory) == [] and world.start_calls == 0 and os.listdir(directory) == []
    assert core.drain() is True  # idempotent


@pytest.mark.parametrize("damage", ["record", "damaged", "units", "units-unreadable", "manager-down", "listing-unreadable", "adopter", "not-ready"])
def test_drain_refuses_removal_on_any_record_damage_unit_or_doubt_and_still_closes_admission(world, directory, damage):
    core = build(world, directory)
    if damage == "record":
        OwnershipStore(str(directory)).put(Record.fresh(BOOT))
    elif damage == "damaged":
        write_raw(directory, "stray", b"x")
    elif damage == "units":
        world.units["freedom-executor-stop-0123456789abcdef.service"] = None  # a loaded matching unit, no record
    elif damage == "units-unreadable":
        world.units_error = lambda: True
    elif damage == "manager-down":
        world.ready_error = True
    elif damage == "listing-unreadable":
        os.chmod(directory, 0o755)  # untrusted directory
    elif damage == "adopter":
        core._mark("a" * 32)
    elif damage == "not-ready":
        core.ready = False
    assert core.drain() is False
    if damage != "not-ready":
        core.ready = True
        os.chmod(directory, 0o700)
        for fixed in (lambda: setattr(world, "units_error", lambda: False), lambda: setattr(world, "ready_error", False)):
            fixed()
        assert core.handle_stop() is PrivilegedStop.NOT_SENT and world.start_calls == 0  # an inconclusive drain never reopens admission


def test_a_stop_admitted_before_the_drain_is_seen_by_it_and_the_drain_cannot_acknowledge(world, directory):
    """Barrier at the admission boundary: the stop holds the admission lock with its record not yet written."""
    core = build(world, directory)
    inside, release = threading.Event(), threading.Event()
    original = core._store.put
    launch_release = threading.Event()
    world.gate = launch_release

    def gated(record):
        inside.set()
        assert release.wait(10)
        return original(record)

    core._store.put = gated
    results = {}
    stopper = threading.Thread(target=lambda: results.setdefault("stop", core.handle_stop()))
    stopper.start()
    assert inside.wait(10)  # the request is between its listing and its record, holding admission
    drainer = threading.Thread(target=lambda: results.setdefault("drain", core.drain()))
    drainer.start()
    drainer.join(0.3)
    assert drainer.is_alive() and "drain" not in results  # the drain waits for admission; it cannot ack past it
    release.set()
    assert world.reached_gate.wait(10)  # the durable record exists and the admitted launch is held
    drainer.join(10)
    assert results["drain"] is False  # the drain saw the record (or the adopter): never an acknowledgment
    launch_release.set()
    stopper.join(10)
    assert results["stop"] is PrivilegedStop.STOPPED  # the admitted invocation ran to a settlement under the owner
    assert world.start_calls == 1


def test_a_stop_racing_the_drain_is_refused_before_any_launch_never_admitted_after_the_ack(world, directory):
    core = build(world, directory)
    inside, release = threading.Event(), threading.Event()
    original = core._store.listing

    def gated():
        inside.set()
        assert release.wait(10)
        return original()

    core._store.listing = gated
    results = {}
    drainer = threading.Thread(target=lambda: results.setdefault("drain", core.drain()))
    drainer.start()
    assert inside.wait(10)  # the drain holds admission and is mid-check
    stopper = threading.Thread(target=lambda: results.setdefault("stop", core.handle_stop()))
    stopper.start()
    stopper.join(0.3)
    assert stopper.is_alive() and "stop" not in results  # blocked on the admission lock, nothing recorded
    assert os.listdir(directory) == [] and world.start_calls == 0
    release.set()
    drainer.join(10)
    stopper.join(10)
    assert results["drain"] is True and results["stop"] is PrivilegedStop.NOT_SENT
    assert world.start_calls == 0 and records(directory) == []  # no launch after (or before) the acknowledgment
    assert world.units == {}


def test_drain_does_not_stop_or_touch_an_owned_invocation(world, directory):
    stuck(world)
    core = build(world, directory)
    assert core.handle_stop() is PrivilegedStop.HANDED_OFF
    kills = len(world.kills)
    assert core.drain() is False
    assert records(directory) and world.live_units() and len(world.kills) == kills


def test_the_server_accepts_drain_only_from_the_maintenance_peer_and_stop_only_from_the_executor(world, directory, tmp_path):
    # (executor uid, maintenance uid, request, greeted, answer prefix, drained afterwards). The test process is uid ME.
    cases = [
        (ME, ME + 1, PROTOCOL_REQUEST, GREETING, b"result ", False),  # the executor asks to stop: served
        (ME + 1, ME, DRAIN_REQUEST, GREETING, DRAIN_EMPTY, True),  # the maintenance peer asks to drain: served
        (ME + 1, ME, PROTOCOL_REQUEST, GREETING, b"", False),  # the maintenance peer cannot stop
        (ME, ME + 1, DRAIN_REQUEST, GREETING, b"", False),  # the executor cannot drain
        (ME, ME, DRAIN_REQUEST, GREETING, b"", False),  # one uid is never both
        (ME + 1, ME + 2, DRAIN_REQUEST, b"", b"", False),  # a stranger gets no greeting at all
        (ME + 1, ME + 2, PROTOCOL_REQUEST, b"", b"", False),
    ]
    for index, (executor, maintenance, request, greeting, prefix, drained) in enumerate(cases):
        core = build(world, directory)
        path = str(tmp_path / f"s{index}.sock")
        server = Server(core, path, uid=executor, maintenance_uid=maintenance)
        server.bind()
        stop = threading.Event()
        threading.Thread(target=server.serve, args=(stop,), daemon=True).start()
        try:
            greeted, answer, _ = drain_conversation(path, request)
        finally:
            stop.set()
            server.close()
        assert greeted == greeting, index
        assert (answer.startswith(prefix) if prefix else answer == b""), (index, answer)
        assert core._draining is drained, index
        assert records(directory) == [] or index == 0


def test_a_pending_drain_answers_pending_and_the_connection_is_held_until_the_server_closes(world, directory, tmp_path):
    OwnershipStore(str(directory)).put(Record.fresh(BOOT))
    core = build(world, directory)
    server = Server(core, str(tmp_path / "s.sock"), uid=ME + 1, maintenance_uid=ME)
    server.bind()
    stop = threading.Event()
    threading.Thread(target=server.serve, args=(stop,), daemon=True).start()
    greeted, answer, conn = drain_conversation(str(tmp_path / "s.sock"), hold=True)
    try:
        assert greeted == GREETING and answer == DRAIN_PENDING
        conn.settimeout(0.3)
        with pytest.raises(TimeoutError):
            conn.recv(1)  # held open: silence, not EOF
        stop.set()
        server.close()
        conn.settimeout(10)
        assert conn.recv(1) == b""  # the supervisor going away is visible to the maintainer as EOF
    finally:
        conn.close()


# --- recovery must never delete an admission's in-flight temporary --------------------------------------


def test_recovery_between_an_admissions_temp_write_and_its_rename_does_not_refuse_the_admission(world, directory):
    """Found on the real host as an intermittent NOT_SENT: recovery unlinked the ``.tmp-*`` file a ``put`` was about to rename."""
    holder = {}

    class RecoveryInTheWindow(FileOps):
        def rename(self, source, target, dir_fd):
            if "core" in holder and not holder.get("fired"):
                holder["fired"] = True
                holder["core"].recover_once()  # the periodic pass lands exactly between the temp write and the rename
            super().rename(source, target, dir_fd)

    core = build(world, directory, ops=RecoveryInTheWindow())
    holder["core"] = core
    assert core.handle_stop() is PrivilegedStop.STOPPED  # admitted and settled, not refused before any record
    assert holder["fired"] and world.start_calls == 1
    clean(world, directory)


def test_a_stale_temporary_left_by_a_crash_is_still_removed_by_recovery_and_a_fresh_one_is_not(world, directory):
    import time

    stale, fresh = directory / ".tmp-0123456789abcdef", directory / ".tmp-fedcba9876543210"
    for path in (stale, fresh):
        path.write_bytes(b"partial")
        path.chmod(0o600)
    os.utime(stale, (time.time() - 3600, time.time() - 3600))
    core = build(world, directory)
    core.recover_once()
    assert not stale.exists() and fresh.exists()  # only a leftover old enough to be no live write's temporary
    assert not OwnershipStore(str(directory)).listing().blocking  # temporaries never block
