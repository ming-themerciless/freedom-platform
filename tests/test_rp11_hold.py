"""RT-2 ``hold``: ACT, ``hold-start``, HL and IGR on temporary trees.

As in ``tests/test_rp11_cleanup.py`` every activation path lives under
``tmp_path`` and the test user stands in for root (and for the operator who
owns the ACT directory). The filesystem adapters (PF, PT, K, the ACT journal,
the record store) and the cleanup engine are the real ones; systemd (DI-1,
DI-3), Polkit (the PK/2 series) and the baseline are fakes, and for DI-3 also
the real ``SystemdManagerAdapter`` over a scripted bus. The disposable host runs
the same role through PID 1 (``tests/systemd_integration/test_route3_hold_host.py``).

Recovery is proved by running the real stop-post cleanup over whatever the
holder left (``recover``), as PID 1 would through ``ExecStopPost``.

Row coverage (inventory §5.2, ``RT2.*``) is named in each section header.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import pwd
import signal
import stat
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

sys.dont_write_bytecode = True

from adapters.rp11.fsops import FileIO, LocalActivationFs, LocalHostFacts, LocalRecordStore  # noqa: E402
from adapters.rp11.holdfs import LocalActivationLock, LocalHoldHost, LocalPublisher  # noqa: E402
from adapters.systemd import manager as manager_module  # noqa: E402
from adapters.systemd.bus import BusDisconnected, BusError, BusReply, BusTimeout  # noqa: E402
from adapters.systemd.manager import SystemdManagerAdapter  # noqa: E402
from application.rp11.attribution import Owner  # noqa: E402
from application.rp11.authority import PASS_SCHEMA, AuthorityError, Params  # noqa: E402
from application.rp11.canonical import canonical_bytes, parse_canonical  # noqa: E402
from application.rp11.cleanup import Terminal  # noqa: E402
from application.rp11.evidence import act_evidence  # noqa: E402
from application.rp11.hl import CaptureBaseline, Observation, terminal_reason  # noqa: E402
from application.rp11.hold import (  # noqa: E402
    HoldEnd,
    HoldInvocation,
    HoldProcedure,
    StopFlag,
)
from application.rp11.journal import JournalKind, consume_run, parse_journal, serialize_line  # noqa: E402
from application.rp11.journal import GENESIS  # noqa: E402
from application.rp11.journal import ACT_RUN_END_OUTCOMES, JournalSchemaError  # noqa: E402
from application.rp11 import authority as authority_module  # noqa: E402
from application.rp11 import journal as journal_module  # noqa: E402
from application.rp11.paths import ActivationPaths, Layout  # noqa: E402
from application.rp11.pk import PkMode, PkOutcome, PkResult  # noqa: E402
from application.rp11.sn import ChildHandle, HandleState  # noqa: E402
from application.rp11.ports import GuardMode  # noqa: E402
from application.rp11.records import validate_record  # noqa: E402
from application.unit_control import (  # noqa: E402
    CAPTURE_UNIT,
    BackstopCompletion,
    ControlError,
    ControlOk,
    ControlRefused,
    RefusalReason,
    UnitProperty,
    UnitVerb,
    backstop_service_name,
    backstop_timer_name,
    holder_unit_name,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rp11_fixtures import H2_RECORD_SHA256, IMAGE_SHA256, LEASE, ActivationFixture  # noqa: E402
from test_rp11_cleanup import (  # noqa: E402
    BOOT,
    GRR_FAULTS,
    CloseFault,
    Events,
    FailingIO,
    FakeClock,
    FakePk,
    InspectionFault,
    _baseline,
    close_fault,  # noqa: F401  (fixture)
    procedure,
)
from test_rp11_cleanup import FakeServices as ClFakeServices  # noqa: E402
from test_systemd_unit_control import FakeConnection, job_reply, props_handler, removed  # noqa: E402

ACT_ID = "rp11-act-20261013T101500Z-0a1b2c3d"
INV = "0123456789abcdef0123456789abcdef"
TIMER = backstop_timer_name(ACT_ID)
HOLDER = holder_unit_name(ACT_ID)
PROC_ROOT = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.skipif(os.geteuid() == 0, reason="the local tree tests run unprivileged")


@pytest.fixture(autouse=True)
def _umask():
    previous = os.umask(0o022)
    yield
    os.umask(previous)


@pytest.fixture
def layout(tmp_path: Path) -> Layout:
    return make_layout(tmp_path)


def make_layout(tmp_path: Path) -> Layout:
    for d in ("run", "var_tmp", "tool", "etc", "share/a", "share/b"):
        (tmp_path / d).mkdir(mode=0o755, parents=True)
    (tmp_path / "boot_id").write_text(BOOT + "\n")
    (tmp_path / "mountinfo").write_text(
        f"25 1 0:23 / {tmp_path / 'run'} rw,nosuid shared:5 - tmpfs tmpfs rw\n"
    )
    tool = tmp_path / "tool/rp11_h1.py"
    tool.write_text("# entry\n")
    os.chmod(tool, 0o644)
    return Layout(
        run=str(tmp_path / "run"),
        var_tmp=str(tmp_path / "var_tmp"),
        store=str(tmp_path / "store"),
        owner=Owner(os.getuid(), os.getgid()),
        tool=str(tool),
        boot_id_file=str(tmp_path / "boot_id"),
        mountinfo=str(tmp_path / "mountinfo"),
        etc_config=str(tmp_path / "etc/freedom-blades-rp11"),
        other_rules_dirs=(str(tmp_path / "etc"), str(tmp_path / "share/a"), str(tmp_path / "share/b")),
    )


# ---------------------------------------------------------------------------
# fakes
# ---------------------------------------------------------------------------


class HoldUnits:
    """DI-1 and DI-3 for one activation. ``timeline`` mutates the capture unit
    once the fake clock reaches a time; ``on_read`` may return an error."""

    def __init__(self, clock: FakeClock) -> None:
        self.clock = clock
        self.capture = {
            UnitProperty.ACTIVE_STATE: "inactive",
            UnitProperty.INVOCATION_ID: "",
            UnitProperty.INACTIVE_ENTER_TIMESTAMP_MONOTONIC: 0,
            UnitProperty.JOB: 0,
            UnitProperty.EXEC_MAIN_START_TIMESTAMP_MONOTONIC: 0,
            UnitProperty.LOAD_STATE: "not-found",
        }
        self.load = {HOLDER: "loaded", TIMER: "not-found", backstop_service_name(ACT_ID): "not-found"}
        self.timer_state = "inactive"
        self.backstop_result = None
        self.creates: list = []
        self.reads: list[tuple[str, tuple]] = []
        self.timeline: list[tuple[int, object]] = []
        self.on_read = None

    def read_unit(self, unit, props):
        self.reads.append((unit, tuple(props)))
        for item in list(self.timeline):
            at, change = item
            if self.clock.now >= at:
                self.timeline.remove(item)
                change(self)
        if self.on_read is not None:
            result = self.on_read(unit, props, len(self.reads))
            if result is not None:
                return result
        if unit == CAPTURE_UNIT:
            return ControlOk({p: self.capture[p] for p in props})
        values = {UnitProperty.LOAD_STATE: self.load[unit]}
        if unit == TIMER:
            values[UnitProperty.ACTIVE_STATE] = self.timer_state
        return ControlOk({p: values[p] for p in props})

    def create_backstop(self, spec):
        self.creates.append(spec)
        if self.backstop_result is not None:
            return self.backstop_result
        self.load[TIMER] = self.load[backstop_service_name(ACT_ID)] = "loaded"
        self.timer_state = "active"
        return ControlOk(BackstopCompletion("/org/freedesktop/systemd1/job/9", TIMER))

    def mutating(self) -> int:
        return len(self.creates)


class HoldPk:
    """PK/2 per verb; ``during`` runs inside a series (e.g. setting the stop flag)."""

    def __init__(self) -> None:
        self.results = {
            UnitVerb.START: (PkOutcome.AUTHORIZED, "decided"),
            UnitVerb.STOP: (PkOutcome.NOT_AUTHORIZED, "decided"),
        }
        self.calls: list[tuple] = []
        self.during = None

    def run(self, operator, verb, mode, *, stop_requested=None):
        self.calls.append((verb, mode))
        if self.during is not None:
            self.during(verb)
        outcome, reason = self.results[verb]
        if stop_requested is not None and stop_requested():
            outcome, reason = PkOutcome.UNCONFIRMED, "interrupted"
        if mode is PkMode.SEEK_NOT_AUTHORIZED:  # a series in this mode never answers "authorized"
            if outcome is PkOutcome.AUTHORIZED:
                outcome, reason = PkOutcome.UNCONFIRMED, "still-authorized"
            elif outcome is PkOutcome.UNCONFIRMED and reason == "decided":
                reason = "only-errors"
        child = ChildHandle(
            pid=4242, pgid=4242, start_ticks=100, created_ms=0, deadline_ms=1_000, s0_ran=True,
            grace_deadline_ms=1, state=HandleState.REAPED,
            sends=[{"signal": "SIGKILL", "result": "sent", "offset_ms": 0, "late": False}],
        ).entry()
        return PkResult(mode, verb, outcome, reason, calls=1, children=[child])


class Baseline:
    def __init__(self, value):
        self.value = value

    def recompute(self):
        if isinstance(self.value, BaseException):
            raise self.value
        return self.value


class Services:
    def __init__(self, units, pk, baseline) -> None:
        self._units, self._pk, self._baseline = units, pk, baseline

    def units(self, params):
        return self._units

    def pk(self, params):
        return self._pk

    def baseline(self, params):
        return self._baseline


class HoldClock(FakeClock):
    def __init__(self) -> None:
        super().__init__()
        self.on_sleep = None

    def monotonic_us(self):
        return self.now * 1000

    def sleep_ms(self, ms):
        super().sleep_ms(ms)
        if self.on_sleep is not None:
            self.on_sleep(self.now)


class CountingFlag:
    """A stop flag that becomes set at its ``at``-th read (``None``: never)."""

    def __init__(self, at: int | None = None) -> None:
        self.at = at
        self.reads = 0
        self.forced = False

    def __call__(self) -> bool:
        self.reads += 1
        return self.forced or (self.at is not None and self.reads >= self.at)


class World:
    """One synthetic activation prepared as AP-0 … SA-1 would leave it."""

    def __init__(self, layout: Layout, tmp_path: Path, *, rules_dir: bool = True, lease: dict | None = None) -> None:
        me = pwd.getpwuid(os.getuid())
        self.layout = layout
        self.tmp = tmp_path
        self.paths = ActivationPaths(layout, ACT_ID)
        self.capture_root = str(tmp_path / "capture")
        self.fx = ActivationFixture(
            layout,
            ACT_ID,
            BOOT,
            _baseline(),
            operator_user=me.pw_name,
            params=Params(pk_op_ms=5_000, lock_wait_ms=1_000),
            pass_doc={"schema": PASS_SCHEMA, "capture_root": self.capture_root, "pass": "a"},
        )
        self.lease = dict(lease or LEASE)
        self.a2 = self.fx.write_authority(lease=self.lease)
        act = Path(self.paths.act_dir)
        act.mkdir(mode=0o700)
        os.chmod(act, 0o700)
        if rules_dir:
            Path(self.paths.rules_dir).mkdir(mode=0o755, parents=True)
            os.chmod(self.paths.polkit_run_dir, 0o755)
        self.clock = HoldClock()
        self.units = HoldUnits(self.clock)
        self.pk = HoldPk()
        self.baseline = Baseline(_baseline())
        self.flag = CountingFlag()
        self.io = FileIO()
        self.publish_io = FileIO()
        self.record_io = FileIO()
        self.publisher = None
        self.lock = None
        self.fs = LocalActivationFs(layout.owner)

    def procedure(self) -> HoldProcedure:
        self.lock = self.lock or LocalActivationLock(self.paths.lock_dir, self.layout.owner)
        return HoldProcedure(
            HoldInvocation(ACT_ID, self.a2, INV, 1),
            self.paths,
            fs=self.fs,
            journals=self.fs,
            host_fs=LocalHoldHost(self.layout.owner, io=self.io),
            publisher=self.publisher or LocalPublisher(self.layout.owner, io=self.publish_io),
            records=LocalRecordStore(self.paths.record_dir, self.layout.owner, io=self.record_io),
            lock=self.lock,
            host=LocalHostFacts(boot_id_file=self.layout.boot_id_file, mountinfo=self.layout.mountinfo, run=self.layout.run),
            services=Services(self.units, self.pk, self.baseline),
            clock=self.clock,
            flag=self.flag,
        )

    def run(self):
        self.proc = self.procedure()
        return self.proc.run()

    # a pass that ends with its capture root (the normal end) -------------------

    def script_pass(self, *, start_ms: int = 1_000, end_ms: int = 2_000, invocation: str = "ab" * 16) -> None:
        def started(units):
            units.capture.update({
                UnitProperty.ACTIVE_STATE: "active",
                UnitProperty.INVOCATION_ID: invocation,
                UnitProperty.EXEC_MAIN_START_TIMESTAMP_MONOTONIC: 5,
            })
            os.mkdir(self.capture_root)

        def ended(units):
            units.capture.update({
                UnitProperty.ACTIVE_STATE: "inactive",
                UnitProperty.INACTIVE_ENTER_TIMESTAMP_MONOTONIC: 7_000,
            })

        base = self.clock.now
        self.units.timeline += [(base + start_ms, started), (base + end_ms, ended)]

    # evidence -------------------------------------------------------------------

    def journal(self):
        data = (Path(self.paths.act_dir) / "journal").read_bytes()
        return parse_journal(data, kind=JournalKind.ACT, run=ACT_ID)

    def ops(self) -> list[str]:
        return [line.op for line in self.journal().lines]

    def act_record(self) -> dict | None:
        path = Path(self.paths.record_dir) / f"{ACT_ID}.act.json"
        return parse_canonical(path.read_bytes()) if path.exists() else None

    def rule_present(self) -> bool:
        return os.path.lexists(self.paths.rule)

    def recover(self, pk_outcome=PkOutcome.NOT_AUTHORIZED):
        """PID 1's ExecStopPost: the real stop-post cleanup over what the holder left."""
        events = Events()
        services = ClFakeServices(events, pk=FakePk(events, outcome=pk_outcome))
        proc, _ = procedure(self.layout, self.fx, events=events, services=services)
        return proc.run()


@pytest.fixture
def world(layout, tmp_path) -> World:
    return World(layout, tmp_path)


def ended_normally(world: World):
    world.script_pass()
    return world.run()


# ---------------------------------------------------------------------------
# HL terminal predicate (RT2.HL.4) — table
# ---------------------------------------------------------------------------

BASE = CaptureBaseline("inactive", "11" * 16, 500)


def obs(**kw) -> Observation:
    values = dict(active_state="inactive", invocation_id="11" * 16, tau=500, job=0, exec_main_start_us=0,
                  capture_root=False, claim=False, consumed=False, consumed_invocation="")
    values.update(kw)
    return Observation(**values)


@pytest.mark.parametrize(
    "observation,expired,active,expected",
    [
        (obs(), False, (), None),
        (obs(), True, (), "start-window-expired"),
        (obs(job=3), True, (), None),
        (obs(capture_root=True), False, (), "pass-ended"),
        (obs(capture_root=True, active_state="failed"), False, (), "pass-ended"),
        (obs(capture_root=True, active_state="active"), True, (), None),
        (obs(active_state="active", invocation_id="22" * 16), True, (), None),
        (obs(active_state="activating"), True, (), None),
        (obs(active_state="deactivating", capture_root=True), False, (), None),
        (obs(consumed=True, claim=True, tau=900, exec_main_start_us=4), False, (), "pass-failed-early"),
        (obs(consumed=True, claim=True, tau=900, consumed_invocation="22" * 16), False, ("22" * 16,), "pass-failed-early"),
        (obs(consumed=True, claim=True, tau=900, consumed_invocation="22" * 16), False, (), "start-failed-before-exec"),
        (obs(tau=900), False, (), "start-failed-before-exec"),
        (obs(invocation_id="33" * 16, active_state="failed"), False, (), "start-failed-before-exec"),
        (obs(claim=True), False, (), "start-failed-before-exec"),
        (obs(tau=0), False, (), "capture-unloaded"),
        (obs(tau=0, invocation_id=""), False, (), "capture-unloaded"),
        (obs(tau=0, active_state="failed"), False, (), None),
        (obs(tau=900), True, (), "start-failed-before-exec"),
    ],
)
def test_hl_terminal_reasons_in_the_accepted_order(observation, expired, active, expected):
    assert terminal_reason(observation, BASE, window_expired=expired, active_invocations=frozenset(active)) == expected


def test_a_never_loaded_capture_unit_ends_only_by_the_window():
    base = CaptureBaseline("inactive", "", 0)
    quiet = obs(invocation_id="", tau=0)
    assert terminal_reason(quiet, base, window_expired=False, active_invocations=frozenset()) is None
    assert terminal_reason(quiet, base, window_expired=True, active_invocations=frozenset()) == "start-window-expired"


def test_exit_codes_are_pinned():
    assert {e.value: e.exit_code for e in HoldEnd} == {
        "hold-ended": 0, "invalid-authority": 20, "precondition": 21, "lock-object": 22,
        "capture-baseline-unstable": 23, "capture-busy-at-act": 24, "evidence-unwritable": 25,
        "backstop-unconfirmed": 26, "publication-failed": 27, "grant-not-seen": 28,
        "stop-control-unconfirmed": 29, "stop-control-authorized": 30, "verification-failed": 31,
        "act-record-unpublished": 32, "start-before-hold": 33, "observation-failed": 34,
        "interrupted": 35,
    }


# ---------------------------------------------------------------------------
# the complete holder: ACT PASS, hold-start, HL, IGR; then stop-post (RT2 all rows)
# ---------------------------------------------------------------------------


def test_a_complete_activation_ends_by_hl_removes_its_grant_and_stop_post_verifies(world):
    outcome = ended_normally(world)
    assert (outcome.end, outcome.detail, outcome.exit_code) == (HoldEnd.HOLD_ENDED, "pass-ended", 0)
    assert outcome.act_pass and outcome.igr == "removed"
    assert world.proc.igr_state == "done"
    assert not world.rule_present()
    ops = world.ops()
    assert ops[:3] == ["run-start", "backstop-intent", "backstop-armed"]
    # the order of the accepted steps
    grant_intent = next(i for i, line in enumerate(world.journal().lines) if line.op == "file-intent" and line.fields["grant"])
    assert ops.index("tree-linked") < grant_intent < ops.index("grant-check")
    for earlier, later in [
        ("backstop-armed", "tree-intent"),
        ("grant-check", "hold-start"),
        ("hold-start", "pass-observed"),
        ("pass-observed", "hold-end"),
        ("hold-end", "igr"),
    ]:
        assert ops.index(earlier) < ops.index(later), (earlier, later)
    assert ops[-2:] == ["igr", "run-end"]
    assert world.journal().ops("run-end")[0].fields == {"outcome": "hold-ended"}
    lines = world.journal().lines
    start = lines[0].fields
    assert start["holder_invocation_id"] == INV and start["lock"]["object"]["path"] == world.paths.lock_dir
    assert start["capture"]["bsp_retries"] == 0 and start["lease"] == world.lease
    armed = world.journal().ops("backstop-armed")[0].fields
    assert armed == {"timer": TIMER, "period_s": 60, "max": 20, "runtime_s": 120}
    checks = [line.fields for line in world.journal().ops("grant-check")]
    assert [(c["verb"], c["mode"], c["outcome"]) for c in checks] == [
        ("start", "seek-authorized", "authorized"),
        ("stop", "first-decisive", "not-authorized"),
    ]
    assert world.journal().ops("hold-end")[0].fields["observation"]["capture_root"] is True
    # the act record: ACT PASS
    record = world.act_record()
    validate_record(record)
    assert record["outcome"] == "activated" and record["trigger"] == "act"
    info = os.lstat(Path(world.paths.record_dir) / f"{ACT_ID}.act.json")
    assert stat.S_IMODE(info.st_mode) == 0o444
    # exactly one DI-3 call, with the accepted parameters
    (spec,) = world.units.creates
    assert (spec.interval_seconds, spec.runtime_max_seconds, spec.timeout_stop_seconds) == (60, 120, 120)
    assert spec.artifact_sha256 == world.a2
    # ExecStopPost: the cleanup attributes everything the holder built
    evidence = act_evidence(world.journal())
    assert evidence.valid and evidence.igr_removed and evidence.positive_control
    assert evidence.hold_end_reason == "pass-ended"
    cl = world.recover()
    assert cl.terminal is Terminal.ST1_VERIFIED, cl.diagnostic(ACT_ID)
    assert cl.rule_class == "removed-earlier" and cl.pass_class == "removed"
    for path in (world.paths.tree_p, world.paths.lock_dir):
        assert not os.path.lexists(path)


def test_published_objects_have_their_accepted_identity_and_grant_id_names_the_rule(world):
    seen = {}

    def snapshot(verb):
        if verb is UnitVerb.START:
            p = world.paths
            seen.update({path: os.lstat(path) for path in (p.tree_p, p.pass_config, p.rule, p.grant_id, p.lock_dir)})
            seen["grant.id"] = parse_canonical(Path(p.grant_id).read_bytes())
            seen["pass"] = Path(p.pass_config).read_bytes()

    world.pk.during = snapshot
    ended_normally(world)
    p = world.paths
    modes = {path: stat.S_IMODE(seen[path].st_mode) for path in (p.tree_p, p.pass_config, p.rule, p.grant_id, p.lock_dir)}
    assert modes == {p.tree_p: 0o755, p.pass_config: 0o644, p.rule: 0o644, p.grant_id: 0o600, p.lock_dir: 0o700}
    assert seen["pass"] == canonical_bytes(world.fx.pass_doc)  # the quoted document, no field edited
    grant = seen["grant.id"]
    rule = seen[p.rule]
    assert (grant["path"], grant["dev"], grant["ino"], grant["boot_id"]) == (p.rule, rule.st_dev, rule.st_ino, BOOT)
    assert grant["sha256"] == hashlib.sha256(world.fx.rule_bytes).hexdigest()


def test_igr_runs_exactly_once_and_a_second_call_is_a_no_op(world):
    world.script_pass()
    proc = world.procedure()
    removals = []
    original = world.fs.remove

    def counting(*a, **kw):
        removals.append(a[0])
        return original(*a, **kw)

    world.fs.remove = counting
    proc.run()
    proc._igr()
    assert removals == [world.paths.rule] and world.ops().count("igr") == 1


# ---------------------------------------------------------------------------
# AM-0 (RT2.AM0.1 … RT2.AM0.6): authority and re-checks; nothing is created
# ---------------------------------------------------------------------------


def assert_nothing_created(world: World):
    p = world.paths
    for path in (p.lock_dir, p.tree_p, p.rule, p.grant_id, f"{p.act_dir}/journal"):
        assert not os.path.lexists(path), path
    assert world.units.creates == []


def test_a2_digest_mismatch_and_missing_authority_exit_before_any_state(world):
    world.a2 = "f" * 64
    outcome = world.run()
    assert (outcome.end, outcome.exit_code, outcome.igr) == (HoldEnd.INVALID_AUTHORITY, 20, "absent")
    assert_nothing_created(world)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda doc: doc.update(pass_config={**doc["pass_config"], "pass": "b"}),
        lambda doc: doc.update(pass_config={"schema": "other", "capture_root": "/x"}),
        lambda doc: doc["pass_config"].update(capture_root="relative"),
        lambda doc: doc["pass_config"].update(capture_root="/a/../b"),
        lambda doc: doc.update(staged_rule={"dev": 1}),
        lambda doc: doc["lease"].pop("bs_runtime_s"),
        lambda doc: doc["lease"].update(bs_runtime_s=59),
        lambda doc: doc["lease"].update(poll_ms=10),
        lambda doc: doc.update(extra=1),
    ],
)
def test_a2_content_outside_its_grammar_is_invalid_authority(world, mutate):
    path = Path(world.paths.a2_file(world.a2))
    doc = parse_canonical(path.read_bytes())
    mutate(doc)
    data = canonical_bytes(doc)
    world.a2 = hashlib.sha256(data).hexdigest()
    target = Path(world.paths.a2_file(world.a2))
    target.write_bytes(data)
    os.chmod(target, 0o444)
    outcome = world.run()
    assert outcome.end is HoldEnd.INVALID_AUTHORITY
    assert_nothing_created(world)


def test_an_oversized_pass_document_is_refused():
    with pytest.raises(AuthorityError):
        from application.rp11.authority import _pass_document

        doc = {"schema": PASS_SCHEMA, "capture_root": "/x", "pad": "a" * 70_000}
        _pass_document(doc, hashlib.sha256(canonical_bytes(doc)).hexdigest())


def test_another_boot_is_a_precondition_failure(world):
    Path(world.layout.boot_id_file).write_text("99999999-2222-3333-4444-555555555555\n")
    outcome = world.run()
    assert (outcome.end, outcome.detail) == (HoldEnd.PRECONDITION, "boot")
    assert_nothing_created(world)


def test_run_not_on_tmpfs_is_a_precondition_failure(world):
    Path(world.layout.mountinfo).write_text(f"25 1 0:23 / {world.layout.run} rw - ext4 /dev/x rw\n")
    assert (world.run().detail) == "run-not-tmpfs"
    assert_nothing_created(world)


@pytest.mark.parametrize("target", ["run", "polkit", "rules"])
@pytest.mark.parametrize("problem", ["writable", "symlink"])
def test_unsafe_parents_are_refused(world, target, problem):
    path = {"run": world.layout.run, "polkit": world.paths.polkit_run_dir, "rules": world.paths.rules_dir}[target]
    if problem == "writable":
        os.chmod(path, 0o777)
    else:
        os.rename(path, path + ".real")
        os.symlink(path + ".real", path)
    outcome = world.run()
    assert (outcome.end, outcome.detail) == (HoldEnd.PRECONDITION, "parent")
    if target != "run":
        assert_nothing_created(world)


def test_an_acl_on_a_parent_is_refused(world, monkeypatch):
    import adapters.rp11.holdfs as holdfs

    monkeypatch.setattr(holdfs, "_xattr_names", lambda fd: ("system.posix_acl_access",))
    outcome = world.run()
    assert (outcome.end, outcome.detail) == (HoldEnd.PRECONDITION, "parent")


@pytest.mark.parametrize(
    "which",
    ["tree_p", "rule", "etc_config", "lock_dir", "capture_root", "nextroot", "other0", "other2", "symlink-rule"],
)
def test_every_absence_condition_is_rechecked(world, which):
    p = world.paths
    target = {
        "tree_p": p.tree_p,
        "rule": p.rule,
        "etc_config": world.layout.etc_config,
        "lock_dir": p.lock_dir,
        "capture_root": world.capture_root,
        "nextroot": p.nextroot,
        "other0": f"{world.layout.other_rules_dirs[0]}/50-freedom-blades-rp11.rules",
        "other2": f"{world.layout.other_rules_dirs[2]}/50-freedom-blades-rp11.rules",
        "symlink-rule": p.rule,
    }[which]
    if which == "symlink-rule":
        os.symlink("/nonexistent", target)
    else:
        Path(target).mkdir()
    before = sorted(os.listdir(world.layout.run))
    outcome = world.run()
    assert (outcome.end, outcome.detail, outcome.exit_code) == (HoldEnd.PRECONDITION, "present", 21)
    assert sorted(os.listdir(world.layout.run)) == before  # nothing created, nothing removed
    assert world.units.creates == []


@pytest.mark.parametrize(
    "unit,value",
    [
        (HOLDER, "not-found"),
        (TIMER, "loaded"),
        (backstop_service_name(ACT_ID), "masked"),
        (TIMER, ControlError("timeout")),
        (HOLDER, ControlRefused(RefusalReason.NOT_LOADED)),
    ],
)
def test_the_three_load_state_reads(world, unit, value):
    if isinstance(value, str):
        world.units.load[unit] = value
    else:
        world.units.on_read = lambda u, props, n: value if u == unit else None
    outcome = world.run()
    assert outcome.end is HoldEnd.PRECONDITION
    assert outcome.detail == ("unit-state" if isinstance(value, str) else "unit-unobserved")
    assert_nothing_created(world)


# ---------------------------------------------------------------------------
# K, BSP and the capture baseline (RT2.AM0.8 … RT2.AM0.14, RT2.AM0.17)
# ---------------------------------------------------------------------------


def test_k_is_created_exclusively_and_locked_until_hold_start(world):
    held = []

    def probe(verb):
        fd = os.open(world.paths.lock_dir, os.O_RDONLY | os.O_DIRECTORY)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            held.append(False)
        except BlockingIOError:
            held.append(True)
        finally:
            os.close(fd)

    world.pk.during = probe
    ended_normally(world)
    assert held == [True, True]  # held through AV-1
    # after hold-start the lock is free (HL takes it only to decide)
    fd = os.open(world.paths.lock_dir, os.O_RDONLY | os.O_DIRECTORY)
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    os.close(fd)


def test_a_k_that_cannot_be_locked_is_lock_object(world, monkeypatch):
    import adapters.rp11.holdfs as holdfs

    def busy(fd, op):
        raise BlockingIOError(11, "EWOULDBLOCK")

    monkeypatch.setattr(holdfs.fcntl, "flock", busy)
    outcome = world.run()
    assert (outcome.end, outcome.exit_code) == (HoldEnd.LOCK_OBJECT, 22)
    assert os.path.isdir(world.paths.lock_dir)  # S0, left for CL / the boot
    assert not os.path.lexists(f"{world.paths.act_dir}/journal")


def test_a_k_collision_between_recheck_and_creation_is_lock_object(world):
    original = world.fs.observe

    def squat(path, **kw):
        result = original(path, **kw)
        if path == world.paths.nextroot:  # the last absence check
            os.mkdir(world.paths.lock_dir, 0o700)
        return result

    world.fs.observe = squat
    assert world.run().end is HoldEnd.LOCK_OBJECT


# ---------------------------------------------------------------------------
# K before the ACT journal: the flag after K (RT2.SG1.3), class S0 (RT2.AM0.8,
# H-CL.5b.2, R8 LD-1) — reported, kept, cleared by the boot, never blocking —
# and every other K still A0: kept, unremoved, hard-stop.
# ---------------------------------------------------------------------------


def k_exists_flag(world: World):
    """The stop flag, set from the first read after K exists."""
    return lambda: os.path.isdir(world.paths.lock_dir)


def assert_only_an_empty_k(world: World):
    p = world.paths
    assert os.path.isdir(p.lock_dir) and os.listdir(p.lock_dir) == []
    assert stat.S_IMODE(os.lstat(p.lock_dir).st_mode) == 0o700
    for path in (p.tree_p, p.rule, p.grant_id, f"{p.act_dir}/journal"):
        assert not os.path.lexists(path), path
    assert world.units.creates == [] and world.act_record() is None


def assert_s0_recovery(world: World):
    """Same-boot stop-post over an S0 K: st1-verified, K kept and reported as S0."""
    k = os.lstat(world.paths.lock_dir)
    cl = world.recover()
    assert cl.terminal is Terminal.ST1_VERIFIED, cl.diagnostic(ACT_ID)
    after = os.lstat(world.paths.lock_dir)  # kept: the same inode, untouched
    assert (after.st_dev, after.st_ino, stat.S_IMODE(after.st_mode)) == (k.st_dev, k.st_ino, 0o700)
    record = cl.record
    validate_record(record)
    assert record["outcome"] == "st1-verified" and record["st1"]["checks"]["lock-dir-absent-or-s0"]
    assert record["directories"][-1] == {"role": "lock-dir", "path": world.paths.lock_dir, "class": "s0-kept"}
    (residual,) = record["residual"]
    assert (residual["path"], residual["class"], residual["type"]) == (world.paths.lock_dir, "s0", "dir")
    assert residual["ino"] == k.st_ino
    attempt = Path(world.layout.var_tmp, f"{ACT_ID}-deact-1-evidence/journal").read_bytes()
    lines = [json.loads(line) for line in attempt.splitlines()]
    assert {"op": "classified", "object": "lock-dir", "path": world.paths.lock_dir, "class": "s0-kept"}.items() <= {
        **next(line for line in lines if line.get("object") == "lock-dir"),
    }.items()
    assert not any(line["op"] == "remove-intent" and line.get("path") == world.paths.lock_dir for line in lines)
    # the backstop reads this record as BS-2 (disarm), so recovery is not blocked by K
    from application.rp11.backstop import Branch, branch_for_record

    data = (Path(world.paths.record_dir) / f"{ACT_ID}.deact-1.json").read_bytes()
    assert branch_for_record(data, activation_id=ACT_ID, k=1) is Branch.BS2
    return cl


def test_a_stop_right_after_k_is_created_ends_before_the_baseline(world):
    world.flag = k_exists_flag(world)
    outcome = world.run()
    assert (outcome.end, outcome.step, outcome.exit_code, outcome.igr) == (HoldEnd.INTERRUPTED, "AM-0", 35, "absent")
    assert not outcome.act_pass
    assert [u for u, _ in world.units.reads if u == CAPTURE_UNIT] == []  # BSP never began
    assert_only_an_empty_k(world)
    fd = os.open(world.paths.lock_dir, os.O_RDONLY | os.O_DIRECTORY)  # the holder released K
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    finally:
        os.close(fd)
    assert_s0_recovery(world)


def test_a_holder_killed_between_k_and_the_journal_leaves_an_s0_k(world):
    """A real crash (SIGKILL in BSP's first read: no ``finally``, no IGR)."""

    def die(unit, props, n):
        if unit == CAPTURE_UNIT:
            os.kill(os.getpid(), signal.SIGKILL)

    world.units.on_read = die
    pid = os.fork()
    if pid == 0:  # pragma: no cover - the killed holder
        try:
            world.run()
        finally:
            os._exit(99)
    _, status = os.waitpid(pid, 0)
    assert os.WIFSIGNALED(status) and os.WTERMSIG(status) == signal.SIGKILL
    assert_only_an_empty_k(world)
    assert_s0_recovery(world)


def _act_dir_not_0700(world):
    os.chmod(world.paths.act_dir, 0o750)


def _capture_unstable(world):
    def on_read(unit, props, n):
        if unit == CAPTURE_UNIT:
            values = dict(world.units.capture)
            values[UnitProperty.INACTIVE_ENTER_TIMESTAMP_MONOTONIC] = world.clock.now * 1000 + 10
            return ControlOk({p: values[p] for p in props})
        return None

    world.units.on_read = on_read


@pytest.mark.parametrize(
    "fail,end",
    [
        (lambda w: setattr(w.units, "on_read", lambda u, p, n: ControlError("timeout") if u == CAPTURE_UNIT else None),
         HoldEnd.OBSERVATION_FAILED),
        (_capture_unstable, HoldEnd.CAPTURE_BASELINE_UNSTABLE),
        (lambda w: w.units.capture.update({UnitProperty.JOB: 12}), HoldEnd.CAPTURE_BUSY_AT_ACT),
        (_act_dir_not_0700, HoldEnd.EVIDENCE_UNWRITABLE),
    ],
    ids=["capture-read-error", "baseline-unstable", "capture-busy", "act-journal-uncreatable"],
)
def test_every_failure_before_the_journal_leaves_an_s0_k_that_recovery_verifies(world, fail, end):
    fail(world)
    outcome = world.run()
    assert (outcome.end, outcome.step, outcome.igr) == (end, "AM-0", "absent")
    assert_only_an_empty_k(world)
    if end is HoldEnd.EVIDENCE_UNWRITABLE:
        os.chmod(world.paths.act_dir, 0o700)  # the cleanup reads the ACT directory as AP-1 made it
    assert_s0_recovery(world)


def test_a_k_that_could_not_be_locked_is_s0_for_the_cleanup(world, monkeypatch):
    import adapters.rp11.holdfs as holdfs

    with monkeypatch.context() as m:
        m.setattr(holdfs.fcntl, "flock", lambda fd, op: (_ for _ in ()).throw(BlockingIOError(11, "EWOULDBLOCK")))
        outcome = world.run()
    assert (outcome.end, outcome.exit_code) == (HoldEnd.LOCK_OBJECT, 22)
    assert_only_an_empty_k(world)
    assert_s0_recovery(world)


def _k_with(entry):
    def mutate(world):
        Path(world.paths.lock_dir, entry).write_bytes(b"x")
    return mutate


def _k_replaced_by(kind):
    def mutate(world):
        k = world.paths.lock_dir
        os.rmdir(k)
        if kind == "file":
            fd = os.open(k, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
        elif kind == "symlink":
            target = world.tmp / "k-elsewhere"
            target.mkdir(mode=0o700)
            os.symlink(target, k)
    return mutate


def _k_mode(mode):
    return lambda world: os.chmod(world.paths.lock_dir, mode)


def _k_garbage_journal(world):
    fd = os.open(f"{world.paths.act_dir}/journal", os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    os.write(fd, b"not a journal\n")
    os.close(fd)


def _k_empty_journal(world):
    fd = os.open(f"{world.paths.act_dir}/journal", os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    os.close(fd)


def _k_other_boot(world):
    Path(world.layout.boot_id_file).write_text("ffffffff-ffff-4fff-8fff-ffffffffffff\n")


def _k_run_not_tmpfs(world):
    Path(world.layout.mountinfo).write_text(f"25 1 0:23 / {world.layout.run} rw shared:5 - ext4 /dev/sda1 rw\n")


@pytest.mark.parametrize(
    "mutate",
    [
        _k_with("grant.id"),
        _k_with("other"),
        _k_mode(0o755),
        _k_mode(0o500),
        _k_replaced_by("file"),
        _k_replaced_by("symlink"),
        _k_garbage_journal,
        _k_empty_journal,
        _k_other_boot,
        _k_run_not_tmpfs,
    ],
    ids=[
        "holds-grant-id", "non-empty", "mode-0755", "mode-0500", "a-file", "a-symlink",
        "invalid-journal", "empty-journal", "other-boot", "run-not-tmpfs",
    ],
)
def test_a_k_that_is_not_exactly_the_pre_journal_k_stays_a0_and_hard_stops(world, mutate):
    world.flag = k_exists_flag(world)
    assert world.run().end is HoldEnd.INTERRUPTED
    mutate(world)
    before = os.lstat(world.paths.lock_dir)
    cl = world.recover()
    assert cl.terminal is Terminal.HARD_STOP, cl.diagnostic(ACT_ID)
    after = os.lstat(world.paths.lock_dir)  # unremoved: the same object is still there
    assert (after.st_ino, after.st_mode) == (before.st_ino, before.st_mode)
    record = cl.record
    validate_record(record)
    lock_dir = [d for d in record["directories"] if d["role"] == "lock-dir"]
    assert lock_dir and lock_dir[0]["class"] not in ("s0-kept", "removed")
    assert not record["st1"]["checks"].get("lock-dir-absent-or-s0", False)
    assert "s0" not in [r["class"] for r in record["residual"] if r["path"] == world.paths.lock_dir]


def test_a_k_replaced_after_the_cleanup_locked_it_is_not_s0(world, monkeypatch):
    from test_rp11_cleanup import RecordingLock

    world.flag = k_exists_flag(world)
    world.run()
    original = RecordingLock.acquire
    replaced = {}

    def acquire_then_replace(self, deadline_ms):
        state = original(self, deadline_ms)
        k = world.paths.lock_dir
        os.mkdir(f"{k}.new", 0o700)
        os.chmod(f"{k}.new", 0o700)
        os.rename(f"{k}.new", k)  # an empty root 0700 directory, but another inode
        replaced["ino"] = os.lstat(k).st_ino
        return state

    monkeypatch.setattr(RecordingLock, "acquire", acquire_then_replace)
    cl = world.recover()
    assert cl.terminal is Terminal.HARD_STOP, cl.diagnostic(ACT_ID)
    assert os.lstat(world.paths.lock_dir).st_ino == replaced["ino"]  # kept
    assert cl.record["directories"][-1]["class"] == "present-foreign-unremoved"


def test_a_k_locked_by_someone_else_is_not_s0(world):
    world.flag = k_exists_flag(world)
    world.run()
    fd = os.open(world.paths.lock_dir, os.O_RDONLY | os.O_DIRECTORY)
    fcntl.flock(fd, fcntl.LOCK_EX)
    try:
        cl = world.recover()
    finally:
        os.close(fd)
    assert cl.record["lock"]["mode"] == "degraded"
    assert cl.terminal is Terminal.HARD_STOP and os.path.isdir(world.paths.lock_dir)


@pytest.mark.parametrize(
    "change",
    [
        {"xattr_names": ("system.posix_acl_access",)},
        {"xattr_names": ("system.posix_acl_default",)},
        {"xattr_names": ("security.capability",)},
        {"xattr_names": ("unlistable",)},
        {"nlink": 3},
        {"uid": 12345},
        {"gid": 12345},
        {"mode": 0o1700},
        {"empty": None},
        {"ino": 99},
        {"kind": "file"},
    ],
)
def test_the_s0_shape_of_k_is_exact(change):
    from application.rp11.attribution import Identity, ObjectKind, Observed
    from application.rp11.cleanup import _k_s0_shape

    owner = Owner(0, 0)
    locked = Identity("/run/k", ObjectKind.DIR, 1, 7, 0o700)
    good = dict(kind=ObjectKind.DIR, dev=1, ino=7, uid=0, gid=0, mode=0o700, nlink=2, size=40, empty=True,
                xattr_names=("user.note",))
    assert _k_s0_shape(Observed(**good), locked, owner)
    if change.get("kind") == "file":
        change = {"kind": ObjectKind.FILE}
    assert not _k_s0_shape(Observed(**{**good, **change}), locked, owner)
    assert not _k_s0_shape(None, locked, owner) and not _k_s0_shape(Observed(**good), None, owner)


@pytest.mark.parametrize("unstable_reads,expected", [(0, 0), (1, 1), (5, 5)])
def test_bsp_retries_within_five(world, unstable_reads, expected):
    calls = {"n": 0}

    def on_read(unit, props, n):
        if unit == CAPTURE_UNIT and UnitProperty.JOB in props and UnitProperty.EXEC_MAIN_START_TIMESTAMP_MONOTONIC not in props:
            calls["n"] += 1
            if calls["n"] <= unstable_reads:
                values = dict(world.units.capture)
                values[UnitProperty.INACTIVE_ENTER_TIMESTAMP_MONOTONIC] = world.clock.now * 1000 + 10
                return ControlOk({p: values[p] for p in props})
        return None

    world.units.on_read = on_read
    ended_normally(world)
    assert world.journal().lines[0].fields["capture"]["bsp_retries"] == expected


def test_six_unstable_reads_are_capture_baseline_unstable(world):
    sleeps = []
    world.clock.on_sleep = sleeps.append

    def on_read(unit, props, n):
        if unit == CAPTURE_UNIT:
            values = dict(world.units.capture)
            values[UnitProperty.INACTIVE_ENTER_TIMESTAMP_MONOTONIC] = world.clock.now * 1000 + 10
            return ControlOk({p: values[p] for p in props})
        return None

    world.units.on_read = on_read
    outcome = world.run()
    assert (outcome.end, outcome.exit_code) == (HoldEnd.CAPTURE_BASELINE_UNSTABLE, 23)
    assert len([u for u, _ in world.units.reads if u == CAPTURE_UNIT]) == 6
    assert len(sleeps) == 5 and not os.path.lexists(f"{world.paths.act_dir}/journal")


@pytest.mark.parametrize("error", [ControlError("timeout"), ControlError("disconnected"), ControlRefused(RefusalReason.NOT_LOADED)])
def test_a_capture_read_error_is_never_a_baseline(world, error):
    world.units.on_read = lambda u, props, n: error if u == CAPTURE_UNIT else None
    outcome = world.run()
    assert (outcome.end, outcome.step) == (HoldEnd.OBSERVATION_FAILED, "AM-0")
    assert not os.path.lexists(f"{world.paths.act_dir}/journal")


@pytest.mark.parametrize("state,job", [("active", 0), ("activating", 0), ("deactivating", 0), ("reloading", 0), ("inactive", 12), ("failed", 3)])
def test_a_busy_capture_unit_is_capture_busy_at_act(world, state, job):
    world.units.capture[UnitProperty.ACTIVE_STATE] = state
    world.units.capture[UnitProperty.JOB] = job
    outcome = world.run()
    assert (outcome.end, outcome.exit_code) == (HoldEnd.CAPTURE_BUSY_AT_ACT, 24)
    assert not os.path.lexists(f"{world.paths.act_dir}/journal")


@pytest.mark.parametrize("problem", ["mode", "missing", "journal-exists", "symlink", "owner"])
def test_the_act_directory_must_be_the_operators_0700_directory(world, problem, monkeypatch):
    act = Path(world.paths.act_dir)
    if problem == "mode":
        os.chmod(act, 0o755)
    elif problem == "missing":
        act.rmdir()
    elif problem == "journal-exists":
        (act / "journal").write_text("squat\n")
    elif problem == "symlink":
        act.rename(act.with_name("elsewhere"))
        act.symlink_to(act.with_name("elsewhere"))
    else:
        import application.rp11.authority as authority

        real = authority.Operator.from_baseline
        monkeypatch.setattr(
            authority.Operator, "from_baseline",
            classmethod(lambda cls, b: authority.Operator(**{**real(b).__dict__, "uid": os.getuid() + 1})),
        )
    outcome = world.run()
    assert (outcome.end, outcome.exit_code) == (HoldEnd.EVIDENCE_UNWRITABLE, 25)
    assert world.units.creates == []


# ---------------------------------------------------------------------------
# AK-1 and DI-3 (RT2.AK1.1 … RT2.AK1.4): one send, never retried
# ---------------------------------------------------------------------------


def test_backstop_intent_is_durable_before_the_single_di3_call(world):
    seen = []
    original = world.units.create_backstop

    def create(spec):
        seen.append([line.op for line in world.journal().lines])
        return original(spec)

    world.units.create_backstop = create
    ended_normally(world)
    assert seen == [["run-start", "backstop-intent"]]


@pytest.mark.parametrize(
    "result,detail",
    [
        (ControlError("timeout", effect_not_confirmed=True), "effect-unknown"),
        (ControlError("disconnected", effect_not_confirmed=True), "effect-unknown"),
        (ControlError("org.freedesktop.systemd1.UnitExists", effect_not_confirmed=True), "effect-unknown"),
        (ControlError("job-result", effect_not_confirmed=True), "effect-unknown"),
        (ControlError("connect-failed"), "not-created"),
        (ControlError("unsafe-artifact"), "not-created"),
        (ControlRefused(RefusalReason.NOT_AUTHORIZED), "not-created"),
    ],
)
def test_an_unconfirmed_or_refused_di3_fails_closed_without_retry(world, result, detail):
    world.units.backstop_result = result
    outcome = world.run()
    assert (outcome.end, outcome.detail, outcome.exit_code) == (HoldEnd.BACKSTOP_UNCONFIRMED, detail, 26)
    assert len(world.units.creates) == 1
    assert world.ops() == ["run-start", "backstop-intent", "igr", "run-end"]
    assert world.journal().lines[-1].fields == {"outcome": "backstop-unconfirmed"}
    assert not os.path.lexists(world.paths.tree_p) and not world.rule_present()
    cl = world.recover()
    assert cl.terminal is Terminal.ST1_VERIFIED, cl.diagnostic(ACT_ID)


@pytest.mark.parametrize("state", ["inactive", "failed", ControlError("timeout")])
def test_a_timer_that_is_not_active_after_di3_fails_closed(world, state):
    original = world.units.create_backstop

    def create(spec):
        result = original(spec)
        if isinstance(state, str):
            world.units.timer_state = state
        else:
            world.units.on_read = lambda u, props, n: state if u == TIMER else None
        return result

    world.units.create_backstop = create
    outcome = world.run()
    assert (outcome.end, outcome.detail) == (HoldEnd.BACKSTOP_UNCONFIRMED, "timer-not-active")
    assert "backstop-armed" not in world.ops()


@pytest.mark.parametrize(
    "mode",
    ["done", "exists", "timeout", "disconnect", "lost-reply", "late", "failed-job"],
)
def test_di3_through_the_real_adapter_over_a_scripted_bus(world, monkeypatch, mode):
    """Late completion, a lost reply and ``UnitExists`` are each one send and an
    unconfirmed effect; only a matching ``done`` arms the backstop."""
    monkeypatch.setattr(manager_module, "_role_runtime_problem", lambda: None)
    timer_signal = removed(job="/org/freedesktop/systemd1/job/4242", unit=TIMER)
    handlers = {
        "done": {"StartTransientUnit": job_reply()},
        "exists": {"StartTransientUnit": BusError("org.freedesktop.systemd1.UnitExists", "exists")},
        "timeout": {"StartTransientUnit": BusTimeout("t")},
        "disconnect": {"StartTransientUnit": BusDisconnected("d")},
        "lost-reply": {"StartTransientUnit": BusReply("", ())},
        "late": {"StartTransientUnit": job_reply()},
        "failed-job": {"StartTransientUnit": job_reply()},
    }[mode]
    signals = {"done": [timer_signal], "late": [], "failed-job": [removed(job="/org/freedesktop/systemd1/job/4242", unit=TIMER, result="failed")]}.get(mode, [])
    conn = FakeConnection(handlers, signals=signals)
    adapter = SystemdManagerAdapter(lambda: conn)
    sends = []

    def create(spec):
        result = adapter.create_backstop(spec)
        sends.append([c.member for c in conn.calls].count("StartTransientUnit"))
        if isinstance(result, ControlOk):
            world.units.timer_state = "active"
        return result

    world.units.create_backstop = create
    outcome = world.run()
    assert sends == [1]
    if mode == "done":
        assert (outcome.end, outcome.detail, outcome.act_pass) == (HoldEnd.HOLD_ENDED, "start-window-expired", True)
    else:
        assert (outcome.end, outcome.detail) == (HoldEnd.BACKSTOP_UNCONFIRMED, "effect-unknown")


# ---------------------------------------------------------------------------
# PF / PT / AM-1G / AM-2 (RT2.AM1.*, RT2.AM1R.1, RT2.AM1G.*, RT2.AM2.*)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("tag", ["p", "r"])
def test_a_squatted_temporary_name_is_preexisting_path(layout, tmp_path, tag):
    world = World(layout, tmp_path, rules_dir=(tag != "r"))
    parent = world.layout.run
    Path(parent, f".rp11-{ACT_ID}-{tag}.tmp").mkdir()
    outcome = world.run()
    assert (outcome.end, outcome.detail, outcome.exit_code) == (HoldEnd.PUBLICATION_FAILED, "preexisting-path", 27)
    assert not world.rule_present()
    cl = world.recover()
    assert cl.terminal is Terminal.ST1_VERIFIED, cl.diagnostic(ACT_ID)
    assert os.path.isdir(Path(parent, f".rp11-{ACT_ID}-{tag}.tmp"))  # S0/A0: kept


def test_tree_r_is_built_when_the_rules_directory_is_absent_and_removed_by_cl(layout, tmp_path):
    world = World(layout, tmp_path, rules_dir=False)
    outcome = ended_normally(world)
    assert outcome.end is HoldEnd.HOLD_ENDED
    trees = [line.fields for line in world.journal().ops("tree-intent")]
    assert [(t["tag"], t["top"]) for t in trees] == [("p", "freedom-blades-rp11"), ("r", "polkit-1")]
    cl = world.recover()
    assert cl.terminal is Terminal.ST1_VERIFIED, cl.diagnostic(ACT_ID)
    assert not os.path.lexists(world.paths.polkit_run_dir)


def test_tree_r_tops_at_rules_d_when_polkit_1_exists(layout, tmp_path):
    world = World(layout, tmp_path, rules_dir=False)
    os.mkdir(world.paths.polkit_run_dir, 0o755)
    ended_normally(world)
    trees = [line.fields for line in world.journal().ops("tree-intent")]
    assert (trees[1]["parent"], trees[1]["top"]) == (world.paths.polkit_run_dir, "rules.d")
    assert world.recover().terminal is Terminal.ST1_VERIFIED
    assert os.path.isdir(world.paths.polkit_run_dir) and not os.path.lexists(world.paths.rules_dir)


def test_the_seal_records_the_inventory_and_the_rename_never_replaces(world, monkeypatch):
    import adapters.rp11.holdfs as holdfs

    original = holdfs.renameat2_noreplace

    def squat_then_rename(old_fd, old, new_fd, new):
        os.mkdir(new, dir_fd=new_fd)
        return original(old_fd, old, new_fd, new)

    monkeypatch.setattr(holdfs, "renameat2_noreplace", squat_then_rename)
    outcome = world.run()
    assert (outcome.end, outcome.detail) == (HoldEnd.PUBLICATION_FAILED, "preexisting-path")
    assert "tree-sealed" in world.ops() and "tree-linked" not in world.ops()
    assert os.path.isdir(Path(world.layout.run, f".rp11-{ACT_ID}-p.tmp"))  # the tree stays under its temp name
    cl = world.recover()
    assert os.path.isdir(world.paths.tree_p)  # A0: the squatter is kept
    assert cl.terminal is Terminal.HARD_STOP


def test_rename_without_noreplace_support_refuses(world, monkeypatch):
    import adapters.rp11.holdfs as holdfs

    def unsupported(*a):
        raise OSError(22, "EINVAL")

    monkeypatch.setattr(holdfs, "renameat2_noreplace", unsupported)
    assert world.run().detail == "rename-unsupported"


@pytest.mark.parametrize("problem", ["digest", "inode", "mode", "missing", "symlink"])
def test_the_staged_rule_must_match_its_pins(world, problem):
    staged = Path(world.paths.staged_rule)
    if problem == "digest":
        os.chmod(staged, 0o644)
        staged.write_bytes(staged.read_bytes().replace(b"synthetic", b"syntheticX"))
        os.chmod(staged, 0o444)
    elif problem == "inode":
        replacement = staged.with_name("replacement")
        replacement.write_bytes(staged.read_bytes())
        os.chmod(replacement, 0o444)
        os.rename(replacement, staged)  # same bytes and mode, another inode
    elif problem == "mode":
        os.chmod(staged, 0o666)
    elif problem == "missing":
        staged.unlink()
    else:
        data = staged.read_bytes()
        staged.unlink()
        other = staged.with_name("other")
        other.write_bytes(data)
        os.symlink(other, staged)
    outcome = world.run()
    assert (outcome.end, outcome.step, outcome.detail) == (HoldEnd.VERIFICATION_FAILED, "AM-1G", "staged-rule")
    assert not world.rule_present() and outcome.igr == "absent"


def test_grant_id_is_durable_before_the_link(world):
    order = []

    class Spy(LocalPublisher):
        def prepare(self, *a, **kw):
            prepared = super().prepare(*a, **kw)
            link = prepared.link

            def spied():
                order.append(("link", os.path.exists(world.paths.grant_id)))
                link()

            prepared.link = spied
            return prepared

    world.publisher = Spy(world.layout.owner)
    ended_normally(world)
    assert ("link", True) in order


def test_a_rule_that_appears_before_the_link_is_foreign_and_kept(world):
    class Squat(LocalPublisher):
        def prepare(self, directory, name, *a, **kw):
            prepared = super().prepare(directory, name, *a, **kw)
            if name == "50-freedom-blades-rp11.rules":
                link = prepared.link

                def squatted():
                    Path(directory, name).write_text("// foreign\n")
                    link()

                prepared.link = squatted
            return prepared

    world.publisher = Squat(world.layout.owner)
    outcome = world.run()
    assert (outcome.end, outcome.step, outcome.detail) == (HoldEnd.PUBLICATION_FAILED, "AM-2", "foreign-rule")
    assert outcome.igr == "kept-foreign"
    assert Path(world.paths.rule).read_text() == "// foreign\n"
    cl = world.recover()
    assert cl.rule_class == "present-foreign-unremoved" and cl.terminal is Terminal.HARD_STOP
    assert Path(world.paths.rule).read_text() == "// foreign\n"


@pytest.mark.parametrize("at", ["before-link", "after-link"])
def test_the_stop_flag_immediately_before_and_after_the_link(world, at):
    class Flagging(LocalPublisher):
        def prepare(self, directory, name, *a, **kw):
            prepared = super().prepare(directory, name, *a, **kw)
            if name == "50-freedom-blades-rp11.rules":
                link = prepared.link
                if at == "before-link":
                    world.flag.forced = True  # set by a handler after AM-1G
                else:
                    def then_flag():
                        link()
                        world.flag.forced = True
                    prepared.link = then_flag
            return prepared

    world.publisher = Flagging(world.layout.owner)
    outcome = world.run()
    assert (outcome.end, outcome.step) == (HoldEnd.INTERRUPTED, "AM-2")
    assert outcome.igr == ("absent" if at == "before-link" else "removed")
    assert not world.rule_present()
    rule_linked = [
        line for line in world.journal().ops("file-linked")
        if line.fields["name"] == "50-freedom-blades-rp11.rules"
    ]
    assert rule_linked == []  # PF-8 never ran: the flag ended the body first
    cl = world.recover()
    assert cl.terminal is Terminal.ST1_VERIFIED, cl.diagnostic(ACT_ID)
    # an identity line exists either way; only IGR's line says it was removed
    assert cl.rule_class == ("absent-before-removal" if at == "before-link" else "removed-earlier")


# ---------------------------------------------------------------------------
# journal / PF / PT write and flush failures at every point (RT2.AM0.16, H-JRN.6, H-PF, H-PT)
# ---------------------------------------------------------------------------


def _count_io(world_factory) -> tuple[int, int]:
    world = world_factory()
    io = FailingIO()
    world.io = io
    ended_normally(world)
    return io.writes, io.fsyncs


@pytest.mark.parametrize("kind", ["write", "fsync"])
def test_every_act_journal_failure_point_fails_closed_and_recovers(layout, tmp_path, kind):
    """Each journal append is one write and one flush. Failing each in turn: the
    holder stops (25, or a later step's class), the grant never survives, and
    stop-post completes from what is durable."""
    counter = World(layout, tmp_path / "count")  # noqa: F841 - counts on a separate tree
    total_writes, total_fsyncs = 0, 0
    probe = World(_sub_layout(layout, tmp_path / "probe"), tmp_path / "probe")
    io = FailingIO()
    probe.io = io
    ended_normally(probe)
    total = io.writes if kind == "write" else io.fsyncs
    assert total >= 20
    for n in range(1, total + 1):
        base = tmp_path / f"{kind}-{n}"
        w = World(_sub_layout(layout, base), base)
        w.io = FailingIO(**({"fail_write_at": n} if kind == "write" else {"fail_fsync_at": n}))
        w.script_pass()
        outcome = w.run()
        assert outcome.exit_code != 0 or outcome.end is HoldEnd.HOLD_ENDED, (n, outcome)
        assert not w.rule_present(), (n, outcome)
        cl = w.recover()
        assert cl.terminal in (Terminal.ST1_VERIFIED, Terminal.HARD_STOP), (n, cl.diagnostic(ACT_ID))
        assert not w.rule_present()
        if outcome.end is not HoldEnd.HOLD_ENDED:
            assert outcome.end in (HoldEnd.EVIDENCE_UNWRITABLE, HoldEnd.ACT_RECORD_UNPUBLISHED, HoldEnd.PUBLICATION_FAILED), (n, outcome)
        else:  # only the two best-effort lines after the grant is decided: igr, run-end
            assert n >= total - 1, (n, total)


class RaisingIO(FailingIO):
    """PF-5 completes a short write by writing the rest; an error is a failure."""

    def write(self, fd, data):
        self.writes += 1
        if self.writes == self.fail_write_at:
            raise OSError(28, "ENOSPC")
        return os.write(fd, data)


def test_a_short_pf_write_is_completed_by_the_write_loop(world):
    world.publish_io = FailingIO(fail_write_at=1)
    world.script_pass()
    assert world.run().end is HoldEnd.HOLD_ENDED
    assert Path(world.paths.record_dir, f"{ACT_ID}.act.json").exists()


@pytest.mark.parametrize("kind", ["write", "fsync"])
def test_every_pf_and_pt_content_failure_point_fails_closed(layout, tmp_path, kind):
    probe = World(_sub_layout(layout, tmp_path / "probe"), tmp_path / "probe")
    io = RaisingIO()
    probe.publish_io = io
    ended_normally(probe)
    total = io.writes if kind == "write" else io.fsyncs
    assert total >= 3
    for n in range(1, total + 1):
        base = tmp_path / f"{kind}-{n}"
        w = World(_sub_layout(layout, base), base)
        w.publish_io = RaisingIO(**({"fail_write_at": n} if kind == "write" else {"fail_fsync_at": n}))
        outcome = w.run()
        assert outcome.end in (HoldEnd.PUBLICATION_FAILED, HoldEnd.VERIFICATION_FAILED), (n, outcome)
        assert not w.rule_present()
        cl = w.recover()
        assert cl.terminal in (Terminal.ST1_VERIFIED, Terminal.HARD_STOP), (n, cl.diagnostic(ACT_ID))
        assert not w.rule_present()


def _sub_layout(layout: Layout, base: Path) -> Layout:
    for d in ("run", "var_tmp", "tool", "etc", "share/a", "share/b"):
        (base / d).mkdir(mode=0o755, parents=True, exist_ok=True)
    (base / "boot_id").write_text(BOOT + "\n")
    (base / "mountinfo").write_text(f"25 1 0:23 / {base / 'run'} rw shared:5 - tmpfs tmpfs rw\n")
    (base / "tool/rp11_h1.py").write_text("# entry\n")
    return Layout(
        run=str(base / "run"),
        var_tmp=str(base / "var_tmp"),
        store=str(base / "store"),
        owner=layout.owner,
        tool=str(base / "tool/rp11_h1.py"),
        boot_id_file=str(base / "boot_id"),
        mountinfo=str(base / "mountinfo"),
        etc_config=str(base / "etc/freedom-blades-rp11"),
        other_rules_dirs=(str(base / "etc"), str(base / "share/a"), str(base / "share/b")),
    )


# ---------------------------------------------------------------------------
# stop flags at every boundary and every sliced wait (RT2.SG1.3, IM-A)
# ---------------------------------------------------------------------------


def test_the_stop_flag_at_every_read_point_ends_with_igr_and_recovers(layout, tmp_path):
    probe = World(_sub_layout(layout, tmp_path / "probe"), tmp_path / "probe")
    ended_normally(probe)
    reads = probe.flag.reads
    assert reads >= 25
    seen_steps = set()
    k_only_reads = []
    for n in range(1, reads + 1):
        base = tmp_path / f"flag-{n}"
        w = World(_sub_layout(layout, base), base)
        w.flag = CountingFlag(at=n)
        w.script_pass()
        outcome = w.run()
        assert (outcome.end, outcome.exit_code) == (HoldEnd.INTERRUPTED, 35), (n, outcome)
        seen_steps.add(outcome.step)
        assert w.proc.igr_state == "done"
        assert not w.rule_present(), n
        s0_k = False
        if os.path.lexists(f"{w.paths.act_dir}/journal"):
            assert w.ops().count("igr") == 1 and "hold-end" not in w.ops()
        elif os.path.lexists(w.paths.lock_dir):
            # Between K's creation and the ACT journal: K has no identity line, so
            # it is S0 (RT2.AM0.8): kept, reported, not blocking; the boot clears it.
            assert os.listdir(w.paths.lock_dir) == []
            s0_k = True
            k_only_reads.append(n)
        cl = w.recover()
        assert cl.terminal is Terminal.ST1_VERIFIED, (n, cl.diagnostic(ACT_ID))
        if s0_k:
            assert os.path.isdir(w.paths.lock_dir)
            assert cl.record["residual"][0]["path"] == w.paths.lock_dir
            assert [r["class"] for r in cl.record["residual"]] == ["s0"]
        else:
            assert not os.path.lexists(w.paths.lock_dir) and cl.record["residual"] == []
    assert {"AM-0", "AK-1", "AM-1", "AM-1R", "AM-1G", "AM-2", "AV-1", "AM-3", "hold-start", "HL"} <= seen_steps
    # RT2.SG1.3: one read between K's creation and BSP, one after BSP (before the journal).
    assert len(k_only_reads) == 2 and k_only_reads[1] == k_only_reads[0] + 1


def test_a_flag_during_the_pk_series_ends_it_interrupted(world):
    def set_flag(verb):
        if verb is UnitVerb.START:
            world.flag.forced = True

    world.pk.during = set_flag
    outcome = world.run()
    assert (outcome.end, outcome.step, outcome.igr) == (HoldEnd.INTERRUPTED, "AV-1", "removed")
    check = world.journal().ops("grant-check")[0].fields
    assert (check["outcome"], check["reason"]) == ("unconfirmed", "interrupted")
    assert world.recover().terminal is Terminal.ST1_VERIFIED


def test_the_pk_series_reads_the_flag_at_each_wake_up_and_settles_its_subject():
    from test_rp11_pk_sn import OPERATOR, Authority, Launcher, Ops, Subjects

    from application.rp11.pk import PkMode, PkSeries
    from application.rp11.sn import SignalContract
    from application.unit_control import ProcessSubject

    clock = Ops(reap_after=0)
    launcher = Launcher(clock)
    pk = PkSeries(
        launcher=launcher,
        subjects=Subjects(lambda pid: ControlOk(ProcessSubject(pid, 77, OPERATOR.uid))),
        authority=Authority([ControlError("timeout")]),
        contract=SignalContract(clock, grace_ms=2_000, slice_ms=100),
        clock=clock,
        params=Params(pk_op_ms=5_000, pk_call_ms=1_000),
    )
    flag = CountingFlag(at=4)
    result = pk.run(OPERATOR, UnitVerb.START, PkMode.SEEK_AUTHORIZED, stop_requested=flag)
    assert (result.outcome, result.reason) == (PkOutcome.UNCONFIRMED, "interrupted")
    assert all(h.state.value in ("reaped", "abandoned") for h in launcher.spawned)
    assert len(launcher.spawned) == result.calls >= 1


# ---------------------------------------------------------------------------
# AV-1 (RT2.AV1.1 … RT2.AV1.4)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "start,stop,end",
    [
        ((PkOutcome.UNCONFIRMED, "only-errors"), None, HoldEnd.GRANT_NOT_SEEN),
        ((PkOutcome.UNCONFIRMED, "not-seen"), None, HoldEnd.GRANT_NOT_SEEN),
        ((PkOutcome.NOT_AUTHORIZED, "decided"), None, HoldEnd.GRANT_NOT_SEEN),
        ((PkOutcome.AUTHORIZED, "decided"), (PkOutcome.AUTHORIZED, "decided"), HoldEnd.STOP_CONTROL_AUTHORIZED),
        ((PkOutcome.AUTHORIZED, "decided"), (PkOutcome.UNCONFIRMED, "only-errors"), HoldEnd.STOP_CONTROL_UNCONFIRMED),
    ],
)
def test_av1_controls_fail_closed_and_cl_runs_rule_first(world, start, stop, end):
    world.pk.results[UnitVerb.START] = start
    if stop:
        world.pk.results[UnitVerb.STOP] = stop
    outcome = world.run()
    assert (outcome.end, outcome.step, outcome.act_pass, outcome.igr) == (end, "AV-1", False, "removed")
    assert world.act_record() is None
    assert not world.rule_present()
    assert len(world.pk.calls) == (1 if stop is None else 2)
    cl = world.recover()
    assert cl.terminal is Terminal.ST1_VERIFIED, cl.diagnostic(ACT_ID)
    record = parse_canonical((Path(world.paths.record_dir) / f"{ACT_ID}.act.json").read_bytes())
    assert record["outcome"] == "failed"  # written by CL-7, never by the holder


def test_cleanup_preserves_the_holders_activated_act_record_and_links_its_digest(world):
    """CL-7 over a real ``activated`` ACT record: valid for this activation, kept
    byte for byte, its digest the deactivation record's ``act_record_sha256``."""
    outcome = ended_normally(world)
    assert outcome.act_pass
    path = Path(world.paths.record_dir) / f"{ACT_ID}.act.json"
    kept = path.read_bytes()
    validate_record(parse_canonical(kept))
    assert world.act_record()["outcome"] == "activated"
    cl = world.recover()
    assert cl.terminal is Terminal.ST1_VERIFIED, cl.diagnostic(ACT_ID)
    assert path.read_bytes() == kept
    assert cl.record["act_record_sha256"] == hashlib.sha256(kept).hexdigest()


def test_a_baseline_difference_fails_av1_before_any_polkit_call(world):
    changed = _baseline()
    changed["packages"] = [["systemd", "261", "amd64"]]
    world.baseline = Baseline(changed)
    outcome = world.run()
    assert (outcome.end, outcome.detail) == (HoldEnd.VERIFICATION_FAILED, "baseline")
    assert world.pk.calls == [] and not world.rule_present()


@pytest.mark.parametrize("which", ["pass", "rule"])
def test_a_published_file_damaged_before_av1_fails_closed(world, which):
    class Damaging(LocalPublisher):
        def publish_tree(self, parent, top, *a, **kw):
            result = super().publish_tree(parent, top, *a, **kw)
            if which == "pass" and top == "freedom-blades-rp11":
                os.chmod(world.paths.pass_config, 0o664)
            return result

        def prepare(self, directory, name, *a, **kw):
            prepared = super().prepare(directory, name, *a, **kw)
            if which == "rule" and name == "50-freedom-blades-rp11.rules":
                commit = prepared.commit

                def then_damage(sink):
                    commit(sink)
                    os.chmod(world.paths.rule, 0o664)

                prepared.commit = then_damage
            return prepared

    world.publisher = Damaging(world.layout.owner)
    outcome = world.run()
    assert (outcome.end, outcome.step, outcome.detail) == (HoldEnd.VERIFICATION_FAILED, "AV-1", "published-file")
    assert world.pk.calls == []
    assert outcome.igr == ("kept-damaged" if which == "rule" else "removed")
    cl = world.recover()
    assert cl.terminal is Terminal.HARD_STOP
    if which == "rule":
        assert cl.rule_class == "present-damaged-unremoved" and world.rule_present()
    else:
        assert cl.pass_class == "present-damaged-unremoved" and not world.rule_present()


# ---------------------------------------------------------------------------
# AM-3 (RT2.AM3.1): ACT PASS only by the durable record
# ---------------------------------------------------------------------------


def test_an_act_record_collision_is_not_act_pass(world):
    Path(world.paths.record_dir).mkdir(parents=True, exist_ok=True)
    squat = Path(world.paths.record_dir) / f"{ACT_ID}.act.json"
    squat.write_text("{}\n")
    os.chmod(squat, 0o444)
    outcome = world.run()
    assert (outcome.end, outcome.detail, outcome.act_pass, outcome.igr) == (
        HoldEnd.ACT_RECORD_UNPUBLISHED, "collision", False, "removed")
    assert "hold-start" not in world.ops()
    assert not world.rule_present()
    cl = world.recover()
    # the squatting object is not this activation's act record: CL-7 neither rewrites
    # it nor chains a deactivation record to it (it fails closed as record-unpublished)
    assert cl.terminal is Terminal.RECORD_UNPUBLISHED
    assert squat.read_text() == "{}\n"
    assert not (Path(world.paths.record_dir) / f"{ACT_ID}.deact-1.json").exists()


def test_a_record_publication_failure_is_not_act_pass(world):
    world.record_io = FailingIO(fail_fsync_at=1)
    outcome = world.run()
    assert (outcome.end, outcome.act_pass) == (HoldEnd.ACT_RECORD_UNPUBLISHED, False)
    assert not world.rule_present()
    assert world.recover().terminal is Terminal.ST1_VERIFIED


def test_act_pass_never_precedes_durable_verification(world):
    ended_normally(world)
    ops = world.ops()
    record_intent = max(i for i, op in enumerate(ops) if op == "file-intent")
    assert ops.index("grant-check") < record_intent
    assert ops.index("file-linked", record_intent) < ops.index("hold-start")


# ---------------------------------------------------------------------------
# hold-start (RT2.HS.*) and OS-7
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "change",
    [
        {UnitProperty.INACTIVE_ENTER_TIMESTAMP_MONOTONIC: 900},
        {UnitProperty.ACTIVE_STATE: "activating"},
        {UnitProperty.ACTIVE_STATE: "active"},
        {UnitProperty.JOB: 5},
    ],
)
def test_a_start_before_hold_start_ends_the_activation(world, change):
    def start_now(verb):
        if verb is UnitVerb.STOP:
            world.units.capture.update(change)

    world.pk.during = start_now
    outcome = world.run()
    assert (outcome.end, outcome.exit_code, outcome.act_pass) == (HoldEnd.START_BEFORE_HOLD, 33, True)
    ends = world.journal().ops("hold-end")
    assert [e.fields["reason"] for e in ends] == ["start-before-hold"] and "hold-start" not in world.ops()
    assert not world.rule_present()
    cl = world.recover()
    assert cl.terminal in (Terminal.ST1_VERIFIED, Terminal.UNIT_STILL_ACTIVE)


def test_a_failed_hold_start_read_is_observation_failed(world):
    def failing(verb):
        if verb is UnitVerb.STOP:
            world.units.on_read = lambda u, props, n: ControlError("timeout") if u == CAPTURE_UNIT else None

    world.pk.during = failing
    outcome = world.run()
    assert (outcome.end, outcome.step) == (HoldEnd.OBSERVATION_FAILED, "hold-start")
    assert world.journal().ops("hold-end")[0].fields == {"reason": "observation-failed", "observation": "absent"}


# ---------------------------------------------------------------------------
# HL (RT2.HL.1 … RT2.HL.9)
# ---------------------------------------------------------------------------


def test_hl_polls_every_delta_and_journals_only_changes(world):
    world.script_pass(start_ms=2_000, end_ms=4_000)
    world.run()
    observed = [line.fields for line in world.journal().ops("pass-observed")]
    assert [o["active_state"] for o in observed] == ["active", "inactive"]
    polls = [u for u, props in world.units.reads if u == CAPTURE_UNIT and UnitProperty.EXEC_MAIN_START_TIMESTAMP_MONOTONIC in props]
    assert len(polls) >= 8  # every 500 ms for ~4 s, plus the decision re-read


def test_hl_window_expiry_without_a_start(world):
    outcome = world.run()
    assert (outcome.end, outcome.detail, outcome.exit_code) == (HoldEnd.HOLD_ENDED, "start-window-expired", 0)
    assert world.clock.now - 1_000_000 >= 60_000
    assert world.recover().terminal is Terminal.ST1_VERIFIED


def test_hl_observation_failure_fails_closed(world):
    world.units.timeline.append((world.clock.now + 3_000, lambda u: setattr(u, "on_read", lambda unit, p, n: ControlError("timeout") if unit == CAPTURE_UNIT else None)))
    outcome = world.run()
    assert (outcome.end, outcome.exit_code, outcome.igr) == (HoldEnd.OBSERVATION_FAILED, 34, "removed")
    assert world.journal().ops("hold-end")[0].fields["reason"] == "observation-failed"


def test_hl_does_not_end_while_a_consume_holds_k_and_decides_under_it(world):
    holder = {}

    def grab(units):
        fd = os.open(world.paths.lock_dir, os.O_RDONLY | os.O_DIRECTORY)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        holder["fd"] = fd

    def release(units):
        os.close(holder.pop("fd"))

    world.script_pass(start_ms=1_000, end_ms=2_000)
    world.units.timeline += [(world.clock.now + 1_500, grab), (world.clock.now + 6_000, release)]
    outcome = world.run()
    assert outcome.detail == "pass-ended"
    assert world.clock.now >= 1_000_000 + 6_000  # it kept observing while K was held


def test_hl_rereads_under_the_lock_and_continues_if_the_reason_vanished(world):
    seen = {"n": 0}

    def flicker(unit, props, n):
        if unit == CAPTURE_UNIT and UnitProperty.EXEC_MAIN_START_TIMESTAMP_MONOTONIC in props:
            seen["n"] += 1
            if seen["n"] == 3:  # one unlocked observation shows a failed foreign start
                values = dict(world.units.capture)
                values[UnitProperty.INACTIVE_ENTER_TIMESTAMP_MONOTONIC] = 900
                return ControlOk({p: values[p] for p in props})
        return None

    world.units.on_read = flicker
    world.script_pass(start_ms=5_000, end_ms=6_000)
    outcome = world.run()
    assert outcome.detail == "pass-ended"


def test_hl_pass_failed_early_needs_a_consumed_line(world):
    consume = Path(world.paths.consume_dir)

    def consumed_and_failed(units):
        consume.mkdir(mode=0o755)
        lines, prev = [], GENESIS
        for seq, (op, fields) in enumerate(
            [("run-start", {"boot_id": BOOT, "invocation_id": "cd" * 16}), ("consumed", {})], start=1
        ):
            line = serialize_line(JournalKind.CONSUME, seq=seq, prev=prev, run=consume_run(ACT_ID), op=op, fields=fields)
            lines.append(line)
            prev = hashlib.sha256(line).hexdigest()
        (consume / "journal").write_bytes(b"".join(lines))
        os.chmod(consume / "journal", 0o644)
        units.capture.update({
            UnitProperty.ACTIVE_STATE: "failed",
            UnitProperty.INVOCATION_ID: "cd" * 16,
            UnitProperty.INACTIVE_ENTER_TIMESTAMP_MONOTONIC: 900,
            UnitProperty.EXEC_MAIN_START_TIMESTAMP_MONOTONIC: 33,
        })

    world.units.timeline.append((world.clock.now + 1_000, consumed_and_failed))
    outcome = world.run()
    assert outcome.detail == "pass-failed-early"


def test_hl_capture_unloaded(world):
    world.units.capture[UnitProperty.INACTIVE_ENTER_TIMESTAMP_MONOTONIC] = 400
    world.units.timeline.append((world.clock.now + 1_000, lambda u: u.capture.update({UnitProperty.INACTIVE_ENTER_TIMESTAMP_MONOTONIC: 0})))
    assert world.run().detail == "capture-unloaded"


def test_hl_with_k_unusable_ends_observation_failed(world):
    def replace_k(units):
        os.rename(world.paths.lock_dir, world.paths.lock_dir + ".gone")
        os.mkdir(world.paths.lock_dir, 0o700)

    world.script_pass(start_ms=1_000, end_ms=2_000)
    world.units.timeline.append((world.clock.now + 1_500, replace_k))
    outcome = world.run()
    assert (outcome.end, outcome.detail) == (HoldEnd.OBSERVATION_FAILED, "observation-failed")
    assert not world.rule_present()


def test_hl_concurrent_stop_during_a_running_pass(world):
    world.script_pass(start_ms=1_000, end_ms=60_000)
    world.units.timeline.append((world.clock.now + 3_000, lambda u: setattr(world.flag, "forced", True)))
    outcome = world.run()
    assert (outcome.end, outcome.step, outcome.igr) == (HoldEnd.INTERRUPTED, "HL", "removed")
    assert "hold-end" not in world.ops()
    cl = world.recover()  # the capture unit is still active: never better than unit-still-active
    assert cl.terminal in (Terminal.ST1_VERIFIED, Terminal.UNIT_STILL_ACTIVE)


# ---------------------------------------------------------------------------
# IGR / GRR (RT2.IGR.1 … RT2.IGR.5)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("damage", ["content", "mode", "replaced", "hardlink"])
def test_igr_never_removes_a_damaged_or_foreign_grant(world, damage):
    def tamper(units):
        rule = Path(world.paths.rule)
        if damage == "content":
            os.chmod(rule, 0o644)
            with open(rule, "ab") as handle:
                handle.write(b"// x\n")
        elif damage == "mode":
            os.chmod(rule, 0o664)
        elif damage == "replaced":
            replacement = rule.with_name("replacement")
            replacement.write_bytes(rule.read_bytes())
            os.chmod(replacement, 0o644)
            os.rename(replacement, rule)  # same bytes and mode, another inode
        else:
            os.link(rule, world.tmp / "extra-link")

    world.script_pass()
    world.units.timeline.append((world.clock.now + 500, tamper))
    outcome = world.run()
    expected = "kept-foreign" if damage == "replaced" else "kept-damaged"
    assert outcome.igr == expected and world.rule_present()
    assert world.journal().ops("igr")[0].fields["outcome"] == expected


def test_an_unremovable_grant_is_reported_and_left_to_cl(world):
    def lock_dir(units):
        os.chmod(world.paths.rules_dir, 0o555)

    world.script_pass()
    world.units.timeline.append((world.clock.now + 500, lock_dir))
    outcome = world.run()
    assert outcome.igr == "unremovable" and world.rule_present()
    os.chmod(world.paths.rules_dir, 0o755)
    cl = world.recover()
    assert cl.terminal is Terminal.ST1_VERIFIED, cl.diagnostic(ACT_ID)
    assert not world.rule_present()


def test_an_unexpected_exception_still_runs_igr_once(world):
    world.baseline = Baseline(RuntimeError("boom"))
    proc = world.procedure()
    with pytest.raises(RuntimeError):
        proc.run()
    assert proc.igr_state == "done" and not world.rule_present()
    assert world.ops()[-2:] == ["igr", "run-end"]
    assert world.journal().lines[-1].fields == {"outcome": "internal-error"}


def test_igr_still_removes_when_the_journal_is_broken(world):
    """The ``igr`` line is best effort: a broken journal never keeps the grant."""
    world.script_pass()
    world.pk.during = lambda verb: setattr(world.io, "fail_write_at", world.io.writes + 1) if verb is UnitVerb.STOP else None
    world.io = FailingIO()
    outcome = world.run()
    assert (outcome.end, outcome.igr) == (HoldEnd.EVIDENCE_UNWRITABLE, "removed")
    assert not world.rule_present() and "igr" not in world.ops()


# ---------------------------------------------------------------------------
# Review remediation 3: run-start (RT2.AM0.1, RT2.AM0.16), igr identity
# (RT2.IGR.2 … .3) and run-end placement (RT2.AM3.2)
# ---------------------------------------------------------------------------


def _snapshot_grant(world: World) -> dict:
    """K's identity and ``grant.id`` as AV-1 sees them (the holder's in-memory identity)."""
    seen: dict = {}

    def snap(verb):
        if verb is UnitVerb.START:
            k = os.lstat(world.paths.lock_dir)
            seen["k"] = {"path": world.paths.lock_dir, "dev": k.st_dev, "ino": k.st_ino}
            grant = parse_canonical(Path(world.paths.grant_id).read_bytes())
            seen["grant"] = {key: grant[key] for key in ("path", "dev", "ino", "sha256", "size", "mode")}

    world.pk.during = snap
    return seen


def test_run_start_is_exactly_the_complete_am0_16_line(world):
    seen = _snapshot_grant(world)
    ended_normally(world)
    tool = hashlib.sha256(b"# entry\n").hexdigest()
    h1 = Path(world.paths.h1_file(f"{ACT_ID}-h1")).read_bytes()
    expected = {
        "a2_sha256": world.a2,
        "h1_record_sha256": hashlib.sha256(h1).hexdigest(),
        "h2_record_sha256": H2_RECORD_SHA256,
        "boot_id": BOOT,
        "pass_config_sha256": hashlib.sha256(canonical_bytes(world.fx.pass_doc)).hexdigest(),
        "staged_rule_sha256": hashlib.sha256(world.fx.rule_bytes).hexdigest(),
        "tool_sha256": tool,
        "holder_invocation_id": INV,
        "lease": world.lease,
        "lock": {"object": seen["k"], "mode": "held", "wait_ms": 0},
        "capture": {
            "active_state": "inactive",
            "invocation_id": "absent",
            "inactive_enter_us": 0,
            "m_a_us": 1_000_000_000,
            "bsp_retries": 0,
        },
        "helper": {"role": "hold", "image_sha256": list(IMAGE_SHA256), "tool_sha256": tool},
        "params": world.fx.params.to_doc(),
    }
    first = world.journal().lines[0]
    assert first.raw == serialize_line(
        JournalKind.ACT, seq=1, prev=GENESIS, run=ACT_ID, op="run-start", fields=expected
    )
    # the act record carries the same authority, helper and lock values
    record = world.act_record()
    assert record["h2_record_sha256"] == H2_RECORD_SHA256
    assert record["helper"] == expected["helper"] and record["lock"] == expected["lock"]


def _valid_start() -> dict:
    return {
        "a2_sha256": "a" * 64,
        "h1_record_sha256": "b" * 64,
        "h2_record_sha256": "e" * 64,
        "boot_id": BOOT,
        "pass_config_sha256": "c" * 64,
        "staged_rule_sha256": "d" * 64,
        "tool_sha256": "f" * 64,
        "holder_invocation_id": INV,
        "lease": {"lease_s": 900},
        "lock": {"object": {"path": "/run/k", "dev": 1, "ino": 2}, "mode": "held", "wait_ms": 0},
        "capture": {"active_state": "inactive", "invocation_id": "absent", "inactive_enter_us": 0, "m_a_us": 1, "bsp_retries": 0},
        "helper": {"role": "hold", "image_sha256": ["9" * 64], "tool_sha256": "f" * 64},
        "params": {"pk_op_ms": 5000},
    }


def _drop(key):
    return lambda f: f.pop(key)


def _set(path, value):
    def apply(f):
        target = f
        for part in path[:-1]:
            target = target[part]
        target[path[-1]] = value
    return apply


@pytest.mark.parametrize(
    "mutate",
    [
        _drop("h2_record_sha256"),
        _drop("helper"),
        _drop("lock"),
        _drop("tool_sha256"),
        _set(("h2_record_sha256",), "absent"),
        _set(("h2_record_sha256",), "E" * 64),
        _set(("tool_sha256",), "absent"),
        _set(("lock",), {"path": "/run/k", "dev": 1, "ino": 2}),  # the reduced envelope
        _set(("lock",), "absent"),
        _set(("lock", "object"), "absent"),
        _set(("lock", "mode"), "degraded"),
        _set(("lock", "wait_ms"), -1),
        _set(("lock", "extra"), 1),
        _set(("helper", "role"), "stop-post"),
        _set(("helper", "image_sha256"), []),
        _set(("helper", "image_sha256"), ["9" * 64, "9" * 64]),
        _set(("helper", "image_sha256"), ["9" * 63]),
        _set(("helper", "image_sha256"), [f"{i:064x}" for i in range(17)]),
        _set(("helper", "tool_sha256"), "0" * 64),  # differs from tool_sha256
        _set(("helper", "extra"), 1),
        _set(("extra",), 1),
    ],
)
def test_a_run_start_outside_the_complete_grammar_is_refused_and_invalid(mutate):
    fields = _valid_start()
    serialize_line(JournalKind.ACT, seq=1, prev=GENESIS, run=ACT_ID, op="run-start", fields=fields)
    mutate(fields)
    with pytest.raises(JournalSchemaError):
        serialize_line(JournalKind.ACT, seq=1, prev=GENESIS, run=ACT_ID, op="run-start", fields=fields)
    line = canonical_bytes({**fields, "seq": 1, "prev": GENESIS, "run": ACT_ID, "op": "run-start"})
    parsed = parse_journal(line, kind=JournalKind.ACT, run=ACT_ID)
    assert not parsed.valid
    assert not act_evidence(parsed).valid  # cleanup attributes nothing on its authority


@pytest.mark.parametrize(
    "fields",
    [
        {"outcome": "removed"},  # the reduced line
        {"outcome": "removed", "identity": "absent"},  # removal claimed without an identity
        {"outcome": "identity-unavailable", "identity": "absent"},
        {"outcome": "gone", "identity": "absent"},
        {"outcome": "absent", "identity": {"path": "/run/r", "dev": 1, "ino": 2}},
        {"outcome": "absent", "identity": {"path": "/run/r", "dev": 1, "ino": 2, "sha256": "a" * 64, "size": 1, "mode": 0o644, "x": 1}},
        {"outcome": "absent", "identity": "absent", "errno": 0},
    ],
)
def test_an_igr_line_outside_its_grammar_is_refused(fields):
    with pytest.raises(JournalSchemaError):
        serialize_line(JournalKind.ACT, seq=2, prev=GENESIS, run=ACT_ID, op="igr", fields=fields)


@pytest.mark.parametrize("outcome", ["ok", "st1-verified", "hold", ""])
def test_an_act_run_end_outside_its_vocabulary_is_refused(outcome):
    with pytest.raises(JournalSchemaError):
        serialize_line(JournalKind.ACT, seq=2, prev=GENESIS, run=ACT_ID, op="run-end", fields={"outcome": outcome})


def test_the_run_end_vocabulary_is_every_end_class_plus_internal_error():
    assert ACT_RUN_END_OUTCOMES == {e.value for e in HoldEnd} | {"internal-error"}
    assert journal_module.MAX_IMAGES == authority_module.MAX_IMAGES


@pytest.mark.parametrize(
    "mutate",
    [
        lambda doc: doc.pop("h2_record_sha256"),
        lambda doc: doc.update(h2_record_sha256="absent"),
        lambda doc: doc.pop("helper"),
        lambda doc: doc["helper"].pop("tool_sha256"),
        lambda doc: doc["helper"].update(tool_sha256="x" * 64),
        lambda doc: doc["helper"].update(image_sha256=[]),
        lambda doc: doc["helper"].update(image_sha256=["9" * 64, "9" * 64]),
        lambda doc: doc["helper"].update(image_sha256="9" * 64),
        lambda doc: doc["helper"].update(role="hold"),
        lambda doc: doc.update(schema="rp11-a2/2"),
    ],
)
def test_a2_v3_helper_and_h2_pins_outside_their_grammar_are_invalid_authority(world, mutate):
    path = Path(world.paths.a2_file(world.a2))
    doc = parse_canonical(path.read_bytes())
    mutate(doc)
    data = canonical_bytes(doc)
    world.a2 = hashlib.sha256(data).hexdigest()
    target = Path(world.paths.a2_file(world.a2))
    target.write_bytes(data)
    os.chmod(target, 0o444)
    outcome = world.run()
    assert (outcome.end, outcome.detail) == (HoldEnd.INVALID_AUTHORITY, "a2-h1")
    assert_nothing_created(world)


@pytest.mark.parametrize("problem", ["other-bytes", "missing", "mode-0664", "symlink"])
def test_a_tool_that_does_not_hash_to_a2s_pin_is_invalid_authority(world, problem):
    tool = Path(world.layout.tool)
    if problem == "other-bytes":
        os.chmod(tool, 0o644)
        tool.write_text("# another entry\n")
    elif problem == "missing":
        tool.unlink()
    elif problem == "mode-0664":
        os.chmod(tool, 0o664)
    else:
        real = tool.with_name("real.py")
        os.rename(tool, real)
        os.symlink(real, tool)
    outcome = world.run()
    assert (outcome.end, outcome.detail, outcome.exit_code) == (HoldEnd.INVALID_AUTHORITY, "tool", 20)
    assert_nothing_created(world)


@pytest.mark.parametrize("damage", [None, "content", "mode", "replaced", "hardlink", "unremovable"])
def test_igr_records_the_exact_in_memory_identity_for_every_removal_outcome(world, damage):
    seen = _snapshot_grant(world)

    def tamper(units):
        rule = Path(world.paths.rule)
        if damage == "content":
            with open(rule, "ab") as handle:
                handle.write(b"// x\n")
        elif damage == "mode":
            os.chmod(rule, 0o664)
        elif damage == "replaced":
            replacement = rule.with_name("replacement")
            replacement.write_bytes(rule.read_bytes())
            os.chmod(replacement, 0o644)
            os.rename(replacement, rule)
        elif damage == "hardlink":
            os.link(rule, world.tmp / "extra-link")
        elif damage == "unremovable":
            os.chmod(world.paths.rules_dir, 0o555)

    world.script_pass()
    if damage is not None:
        world.units.timeline.append((world.clock.now + 500, tamper))
    outcome = world.run()
    expected = {
        None: "removed", "content": "kept-damaged", "mode": "kept-damaged", "replaced": "kept-foreign",
        "hardlink": "kept-damaged", "unremovable": "unremovable",
    }[damage]
    (igr,) = world.journal().ops("igr")
    assert igr.fields == {"outcome": expected, "identity": seen["grant"]}
    assert outcome.igr == expected and world.rule_present() == (damage is not None)
    # cleanup counts only a removal of the identity it journaled as the grant
    assert act_evidence(world.journal()).igr_removed == (damage is None)
    if damage == "unremovable":
        os.chmod(world.paths.rules_dir, 0o755)


def test_igr_before_am1g_records_explicit_absence(world):
    world.units.backstop_result = ControlError("timeout", effect_not_confirmed=True)
    world.run()
    assert world.journal().ops("igr")[0].fields == {"outcome": "absent", "identity": "absent"}


def test_igr_after_am1g_but_before_the_link_records_the_unlinked_identity(world):
    seen = {}

    class Flagging(LocalPublisher):
        def prepare(self, directory, name, *a, **kw):
            prepared = super().prepare(directory, name, *a, **kw)
            if name == "50-freedom-blades-rp11.rules":
                seen["grant"] = {
                    "path": prepared.identity.path, "dev": prepared.identity.dev, "ino": prepared.identity.ino,
                    "sha256": prepared.identity.sha256, "size": prepared.identity.size, "mode": prepared.identity.mode,
                }
                world.flag.forced = True
            return prepared

    world.publisher = Flagging(world.layout.owner)
    assert world.run().end is HoldEnd.INTERRUPTED
    assert world.journal().ops("igr")[0].fields == {"outcome": "absent", "identity": seen["grant"]}
    assert not act_evidence(world.journal()).igr_removed


def test_an_igr_identity_naming_another_object_is_not_counted_by_cleanup(world):
    """A valid-grammar ``igr`` whose identity is not the journaled grant claims nothing."""
    ended_normally(world)
    data = (Path(world.paths.act_dir) / "journal").read_bytes()
    lines = data.splitlines(keepends=True)
    index = next(i for i, raw in enumerate(lines) if b'"op":"igr"' in raw)
    rebuilt, prev = [], GENESIS
    for i, raw in enumerate(lines):
        entry = parse_canonical(raw)
        fields = {k: v for k, v in entry.items() if k not in ("seq", "prev", "run", "op")}
        if i == index:
            fields["identity"] = {**fields["identity"], "ino": fields["identity"]["ino"] + 1}
        line = serialize_line(JournalKind.ACT, seq=i + 1, prev=prev, run=ACT_ID, op=entry["op"], fields=fields)
        rebuilt.append(line)
        prev = hashlib.sha256(line).hexdigest()
    parsed = parse_journal(b"".join(rebuilt), kind=JournalKind.ACT, run=ACT_ID)
    assert parsed.valid and not act_evidence(parsed).igr_removed


class EventIO(FileIO):
    """The ACT journal's io: records each line's ``op`` (and the rule's presence) in ``events``."""

    def __init__(self, events: list, rule: str, *, fail_op: str | None = None, how: str = "write"):
        self.events, self.rule, self.fail_op, self.how = events, rule, fail_op, how
        self._failing = False

    def write(self, fd, data):
        op = parse_canonical(data)["op"] if data.endswith(b"\n") else "?"
        self.events.append(op)
        if op == "igr":
            self.events.append("rule-present" if os.path.lexists(self.rule) else "rule-gone")
        if op == self.fail_op:
            if self.how == "write":
                return os.write(fd, data[: len(data) // 2])
            self._failing = True
        return super().write(fd, data)

    def fsync(self, fd):
        if self._failing:
            self._failing = False
            raise OSError(5, "EIO")
        super().fsync(fd)


def _instrument(world: World, events: list, **io_kw) -> None:
    world.io = EventIO(events, world.paths.rule, **io_kw)

    class Lock(LocalActivationLock):
        def release(self):
            events.append("K-release")
            return super().release()

    world.lock = Lock(world.paths.lock_dir, world.layout.owner)
    original = world.fs.remove

    def grr(*a, **kw):
        events.append("grr")
        return original(*a, **kw)

    world.fs.remove = grr


def _tail(events: list) -> list:
    """The events from the last line before IGR's decision (``hold-end`` or earlier)."""
    start = max(i for i, e in enumerate(events) if e not in ("grr", "igr", "rule-gone", "rule-present", "run-end", "K-release"))
    return events[start:]


@pytest.mark.parametrize(
    "case,expected,run_end",
    [
        ("normal", ["hold-end", "K-release", "grr", "igr", "rule-gone", "run-end"], "hold-ended"),
        ("hl-observation-failed", ["hold-end", "K-release", "grr", "igr", "rule-gone", "run-end"], "observation-failed"),
        ("start-before-hold", ["hold-end", "grr", "igr", "rule-gone", "run-end", "K-release"], "start-before-hold"),
        ("hold-start-observation-failed", ["hold-end", "grr", "igr", "rule-gone", "run-end", "K-release"], "observation-failed"),
        ("interrupted-in-hl", ["pass-observed", "grr", "igr", "rule-gone", "run-end"], "interrupted"),
        ("interrupted-in-av1", ["grant-check", "grr", "igr", "rule-gone", "run-end", "K-release"], "interrupted"),
        ("unexpected-exception", ["file-linked", "grr", "igr", "rule-gone", "run-end", "K-release"], "internal-error"),
    ],
)
def test_the_order_of_hold_end_k_release_igr_and_run_end_on_every_end(world, case, expected, run_end):
    events: list = []
    _instrument(world, events)
    if case == "normal":
        world.script_pass()
    elif case == "hl-observation-failed":
        world.units.timeline.append((world.clock.now + 3_000, lambda u: setattr(u, "on_read", lambda unit, p, n: ControlError("timeout") if unit == CAPTURE_UNIT else None)))
    elif case == "start-before-hold":
        world.pk.during = lambda verb: world.units.capture.update({UnitProperty.JOB: 5}) if verb is UnitVerb.STOP else None
    elif case == "hold-start-observation-failed":
        def failing(verb):
            if verb is UnitVerb.STOP:
                world.units.on_read = lambda u, props, n: ControlError("timeout") if u == CAPTURE_UNIT else None
        world.pk.during = failing
    elif case == "interrupted-in-hl":
        world.script_pass(start_ms=1_000, end_ms=60_000)
        world.units.timeline.append((world.clock.now + 3_000, lambda u: setattr(world.flag, "forced", True)))
    elif case == "interrupted-in-av1":
        world.pk.during = lambda verb: setattr(world.flag, "forced", True) if verb is UnitVerb.STOP else None
    else:
        world.baseline = Baseline(RuntimeError("boom"))
    proc = world.procedure()
    if case == "unexpected-exception":
        with pytest.raises(RuntimeError):
            proc.run()
    else:
        proc.run()
    assert _tail(events) == expected, events
    assert events.count("grr") == 1 and events.count("igr") == 1 and events.count("run-end") == 1
    assert world.journal().lines[-1].op == "run-end"
    assert world.journal().lines[-1].fields == {"outcome": run_end}
    assert not world.rule_present()
    cl = world.recover()
    assert cl.terminal in (Terminal.ST1_VERIFIED, Terminal.UNIT_STILL_ACTIVE), cl.diagnostic(ACT_ID)


@pytest.mark.parametrize("how", ["write", "fsync"])
@pytest.mark.parametrize("fail_op", ["igr", "run-end"])
def test_a_failed_igr_or_run_end_line_never_keeps_the_grant_or_changes_the_end(world, how, fail_op):
    events: list = []
    seen = _snapshot_grant(world)
    _instrument(world, events, fail_op=fail_op, how=how)
    world.script_pass()
    proc = world.procedure()
    outcome = proc.run()
    proc._igr()  # the exactly-once latch holds after a failed line too
    assert (outcome.end, outcome.exit_code, outcome.igr) == (HoldEnd.HOLD_ENDED, 0, "removed")
    assert events.count("grr") == 1 and "rule-gone" in events and not world.rule_present()
    assert events.index("grr") < events.index("igr")  # removed before its evidence write
    parsed = world.journal()
    assert parsed.valid
    ops = [line.op for line in parsed.lines]
    if fail_op == "igr" and how == "write":
        assert ops[-1] == "hold-end" and parsed.torn_tail and "run-end" not in events
    elif fail_op == "igr":
        # written but not flushed: the journal stops accepting lines, so no run-end
        assert ops[-1] == "igr" and parsed.ops("igr")[0].fields["identity"] == seen["grant"]
        assert "run-end" not in events
    elif how == "write":
        assert ops[-1] == "igr" and parsed.torn_tail
    else:
        assert ops[-2:] == ["igr", "run-end"]
    cl = world.recover()
    assert cl.terminal is Terminal.ST1_VERIFIED, cl.diagnostic(ACT_ID)


def test_no_igr_or_run_end_exists_without_the_act_journal(world):
    world.units.on_read = lambda u, props, n: ControlError("timeout") if u == CAPTURE_UNIT else None
    outcome = world.run()
    assert (outcome.end, outcome.step) == (HoldEnd.OBSERVATION_FAILED, "AM-0")
    assert not os.path.lexists(f"{world.paths.act_dir}/journal") and outcome.igr == "absent"


# ---------------------------------------------------------------------------
# GRR remediation: an inspection failure inside the real adapter during IGR
# (RT2.IGR.2 … .3, H-GRR.5, H-GRR.8)
# ---------------------------------------------------------------------------


def _fault_during_grr(world: World, monkeypatch, call: str) -> InspectionFault:
    """The fault is armed only inside IGR's ``remove`` (AV-1 reads the same rule)."""
    fault = InspectionFault(monkeypatch, world.paths.rule, call, active=False)
    inner = world.fs.remove

    def remove(*a, **kw):
        fault.active = True
        try:
            return inner(*a, **kw)
        finally:
            fault.active = False

    world.fs.remove = remove
    return fault


@pytest.mark.parametrize(
    "case,tail,end",
    [
        ("normal", ["hold-end", "K-release", "grr", "igr", "rule-present", "run-end"], (HoldEnd.HOLD_ENDED, 0, "hold-ended")),
        ("interrupted-in-av1", ["grant-check", "grr", "igr", "rule-present", "run-end", "K-release"], (HoldEnd.INTERRUPTED, 35, "interrupted")),
    ],
)
@pytest.mark.parametrize("call,_attribution,grr", GRR_FAULTS)
def test_igr_survives_a_failed_grant_inspection_and_keeps_its_order(world, monkeypatch, case, tail, end, call, _attribution, grr):
    events: list = []
    seen = _snapshot_grant(world)
    _instrument(world, events)
    fault = _fault_during_grr(world, monkeypatch, call)
    if case == "normal":
        world.script_pass()
    else:
        snap = world.pk.during

        def during(verb):
            snap(verb)
            if verb is UnitVerb.STOP:
                world.flag.forced = True

        world.pk.during = during
    proc = world.procedure()
    outcome = proc.run()
    assert fault.hits >= 1
    assert proc.igr_state == "done" and outcome.igr == grr.value
    assert (outcome.end, outcome.exit_code) == end[:2]
    assert _tail(events) == tail, events
    parsed = world.journal()
    assert parsed.valid and parsed.lines[-1].op == "run-end" and parsed.lines[-1].fields == {"outcome": end[2]}
    (igr,) = parsed.ops("igr")
    assert igr.fields == {"outcome": grr.value, "identity": seen["grant"]}
    assert not act_evidence(parsed).igr_removed
    # kept: the very grant, untouched
    assert world.rule_present() and os.lstat(world.paths.rule).st_ino == seen["grant"]["ino"]
    proc._igr()
    assert events.count("grr") == 1  # the latch held
    cl = world.recover()  # the failure has cleared: stop-post's CL-G removes the grant
    assert cl.terminal is Terminal.ST1_VERIFIED, cl.diagnostic(ACT_ID)
    assert not world.rule_present()


def _close_fault_during_grr(world: World, close_fault, role: str, shape: str) -> CloseFault:
    """Armed only inside IGR's ``remove``, like ``_fault_during_grr``."""
    fault = close_fault(world.paths.rule, role, shape, active=False)
    inner = world.fs.remove

    def remove(*a, **kw):
        fault.active = True
        try:
            return inner(*a, **kw)
        finally:
            fault.active = False

    world.fs.remove = remove
    return fault


@pytest.mark.parametrize(
    "case,tail,end",
    [
        ("normal", ["hold-end", "K-release", "grr", "igr", "rule-gone", "run-end"], (HoldEnd.HOLD_ENDED, 0, "hold-ended")),
        ("interrupted-in-av1", ["grant-check", "grr", "igr", "rule-gone", "run-end", "K-release"], (HoldEnd.INTERRUPTED, 35, "interrupted")),
    ],
)
@pytest.mark.parametrize("role", CloseFault.ROLES)
@pytest.mark.parametrize("shape", CloseFault.SHAPES)
def test_igr_survives_a_descriptor_close_error_and_keeps_its_order(world, close_fault, case, tail, end, role, shape):
    events: list = []
    seen = _snapshot_grant(world)
    _instrument(world, events)
    fault = _close_fault_during_grr(world, close_fault, role, shape)
    if case == "normal":
        world.script_pass()
    else:
        snap = world.pk.during

        def during(verb):
            snap(verb)
            if verb is UnitVerb.STOP:
                world.flag.forced = True

        world.pk.during = during
    proc = world.procedure()
    outcome = proc.run()
    assert fault.hits >= 1 and fault.never_retried()
    assert proc.igr_state == "done" and outcome.igr == "removed"
    assert (outcome.end, outcome.exit_code) == end[:2]
    assert _tail(events) == tail, events
    parsed = world.journal()
    assert parsed.valid and parsed.lines[-1].op == "run-end" and parsed.lines[-1].fields == {"outcome": end[2]}
    (igr,) = parsed.ops("igr")
    assert igr.fields == {"outcome": "removed", "identity": seen["grant"]}
    assert not world.rule_present()


# ---------------------------------------------------------------------------
# SG-1 (RT2.SG1.1, RT2.SG1.2) and the subject's dispositions — in a child process
# ---------------------------------------------------------------------------


def _python(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(script)],
        capture_output=True,
        text=True,
        cwd=str(PROC_ROOT),
        env={"PYTHONPATH": str(PROC_ROOT), "PYTHONDONTWRITEBYTECODE": "1"},
        timeout=60,
    )


def test_sg1_handlers_only_set_the_flag_and_a_second_signal_changes_nothing():
    proc = _python(
        """
        import os, signal, json
        from adapters.rp11.hold import STOP_SIGNALS, install_stop_handlers
        from application.rp11.hold import StopFlag
        flag = StopFlag()
        install_stop_handlers(flag)
        out = {"before": flag.requested}
        os.kill(os.getpid(), signal.SIGTERM)
        out["after_one"] = flag.requested
        os.kill(os.getpid(), signal.SIGTERM)
        os.kill(os.getpid(), signal.SIGALRM)
        out["after_three"] = flag.requested
        out["pipe_ignored"] = signal.getsignal(signal.SIGPIPE) == signal.SIG_IGN
        out["chld_default"] = signal.getsignal(signal.SIGCHLD) == signal.SIG_DFL
        out["mask"] = sorted(int(s) for s in signal.pthread_sigmask(signal.SIG_BLOCK, []))
        out["handled"] = sorted(int(s) for s in STOP_SIGNALS)
        print(json.dumps(out))
        """
    )
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert out["before"] is False and out["after_one"] is True and out["after_three"] is True
    assert out["pipe_ignored"] and out["chld_default"] and out["mask"] == []
    assert out["handled"] == sorted(int(s) for s in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT, signal.SIGUSR1, signal.SIGUSR2, signal.SIGALRM))


def test_the_subject_forked_under_sg1_has_default_dispositions_and_self_limits():
    """A fork inherits the holder's handlers; the subject must reset them so its
    ``alarm(60)`` and every signal end it (H-PROC.1)."""
    proc = _python(
        """
        import json, os, pwd, grp, signal, time
        from adapters.rp11.hold import install_stop_handlers
        from adapters.rp11.process import ForkSubjectLauncher, LinuxProcessOps, SystemClock
        from application.rp11.authority import Operator
        from application.rp11.hold import StopFlag
        install_stop_handlers(StopFlag())
        me = pwd.getpwuid(os.getuid())
        groups = sorted(set(os.getgroups()) | {me.pw_gid})
        operator = Operator(me.pw_name, me.pw_uid, me.pw_gid, tuple(groups))
        handle = ForkSubjectLauncher(LinuxProcessOps(SystemClock()), ready_ms=5000).spawn(operator)
        status = open(f"/proc/{handle.pid}/status").read()
        caught = int([l for l in status.splitlines() if l.startswith("SigCgt:")][0].split()[1], 16)
        ignored = int([l for l in status.splitlines() if l.startswith("SigIgn:")][0].split()[1], 16)
        os.kill(handle.pid, signal.SIGALRM)
        deadline = time.monotonic() + 5
        died = None
        while time.monotonic() < deadline:
            pid, st = os.waitpid(handle.pid, os.WNOHANG)
            if pid:
                died = os.WTERMSIG(st) if os.WIFSIGNALED(st) else -1
                break
            time.sleep(0.05)
        print(json.dumps({"ready": handle.ready, "caught": caught, "ignored": ignored, "died": died}))
        """
    )
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert out["ready"] is True
    for signum in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGUSR1):
        assert not out["caught"] & (1 << (signum - 1)), signum
    assert not out["ignored"] & (1 << (signal.SIGPIPE - 1))
    assert out["died"] == signal.SIGALRM


def test_run_hold_installs_sg1_before_reading_anything(monkeypatch, tmp_path):
    proc = _python(
        f"""
        import signal, sys
        import adapters.rp11.hold as hold
        order = []
        real_install = hold.install_stop_handlers
        def install(flag):
            order.append("sg1")
            real_install(flag)
        hold.install_stop_handlers = install
        def build(*a, **kw):
            order.append("build")
            raise OSError("stop here")
        hold.build_hold = build
        code = hold.run_hold("{ACT_ID}", "{'a' * 64}", invocation_id="absent", parent_pid=1, connector=lambda: None)
        print(order, code)
        """
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "['sg1', 'build'] 70"
    assert proc.stderr.strip() == f"rp11-hold internal-error {ACT_ID} OSError"


# ---------------------------------------------------------------------------
# the K adapter on its own (H-LK)
# ---------------------------------------------------------------------------


def test_the_k_adapter_try_once_states(tmp_path):
    owner = Owner(os.getuid(), os.getgid())
    run = tmp_path / "run"
    run.mkdir()
    lock = LocalActivationLock(str(run / "k"), owner)
    lock.create()
    assert lock.try_once() is GuardMode.HELD  # already held by this process
    lock.release()
    other = os.open(run / "k", os.O_RDONLY | os.O_DIRECTORY)
    fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert lock.try_once() is GuardMode.BUSY
    os.close(other)
    assert lock.try_once() is GuardMode.HELD
    lock.release()
    os.rename(run / "k", run / "k.old")
    assert lock.try_once() is GuardMode.UNAVAILABLE
    os.mkdir(run / "k", 0o700)  # a replacement K is not the one AM-0 created
    assert lock.try_once() is GuardMode.UNAVAILABLE
