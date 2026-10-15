"""RT-4 ``backstop``: BS-1 … BS-4 over the shared cleanup, on temporary trees.

As in ``tests/test_rp11_cleanup.py`` every activation path lives under
``tmp_path`` and the test user stands in for root. The filesystem adapters, the
record store, the backstop lock/terminal journal and the cleanup engine are the
real ones; systemd and Polkit are fakes, and for the DI-1/DI-4 boundary also the
real ``SystemdManagerAdapter`` over a scripted bus. The disposable host runs the
same role through PID 1 (``tests/systemd_integration/test_route3_backstop_host.py``).

Row coverage (inventory §5.4, ``RT4.*``) is named in each section header.
"""

from __future__ import annotations

import json
import os
import re
import sys
import threading
from pathlib import Path

import pytest

sys.dont_write_bytecode = True

from adapters.rp11 import backstop as backstop_root  # noqa: E402
from adapters.rp11 import stop_post as stop_post_root  # noqa: E402
from adapters.rp11.backstop import build_backstop, run_backstop  # noqa: E402
from adapters.rp11.fsops import (  # noqa: E402
    UNREACHABLE,
    LocalActivationFs,
    LocalBackstopGuard,
    LocalRecordStore,
)
from adapters.rp11.stop_post import build_procedure  # noqa: E402
from adapters.systemd.bus import BusDisconnected, BusError, BusReply, BusTimeout  # noqa: E402
from adapters.systemd.manager import SystemdManagerAdapter  # noqa: E402
from application.rp11.attribution import Owner  # noqa: E402
from application.rp11.authority import AuthorityError, Params  # noqa: E402
from application.rp11.backstop import (  # noqa: E402
    A1_INTACT_KEPT,
    BackstopProcedure,
    Branch,
    BsTerminal,
    branch_for_record,
    exact_attempts,
    hard_stop_permits_disarm,
    is_backstop_attempt,
)
from application.rp11.canonical import canonical_bytes, parse_canonical  # noqa: E402
from application.rp11.cleanup import GrrOutcome, Terminal  # noqa: E402
from application.rp11.journal import GENESIS, JournalKind, attempt_run, serialize_line  # noqa: E402
from application.rp11.paths import ActivationPaths, Layout  # noqa: E402
from application.rp11.pk import PkOutcome  # noqa: E402
from application.rp11.ports import GuardMode  # noqa: E402
from application.rp11.records import RULE_CLASSES, RecordSchemaError, validate_record  # noqa: E402
from application.unit_control import (  # noqa: E402
    CAPTURE_UNIT,
    ControlError,
    ControlOk,
    ControlRefused,
    JobCompletion,
    RefusalReason,
    StopCompletion,
    StopOutcome,
    UnitProperty,
    backstop_timer_name,
    holder_unit_name,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rp11_fixtures import ActivationFixture  # noqa: E402
from test_rp11_cleanup import (  # noqa: E402
    BOOT,
    Crash,
    Events,
    FailingIO,
    FakeBaseline,
    FakeClock,
    FakePk,
    GRR_FAULTS,
    CloseFault,
    InspectionFault,
    close_fault,  # noqa: F401  (fixture)
    RecordingFs,
    _baseline,
)
from test_systemd_unit_control import FakeConnection, job_reply, props_handler, removed  # noqa: E402

ACT_ID = "rp11-act-20261013T101500Z-0a1b2c3d"
OTHER_ID = "rp11-act-20261013T101500Z-ffffffff"
INV = "0123456789abcdef0123456789abcdef"
HOLDER = holder_unit_name(ACT_ID)
TIMER = backstop_timer_name(ACT_ID)
JOB = "/org/freedesktop/systemd1/job/77"
STOPPED = ControlOk(StopCompletion(StopOutcome.STOPPED, JobCompletion(JOB, TIMER)))

pytestmark = pytest.mark.skipif(os.geteuid() == 0, reason="the local tree tests run unprivileged")


# ---------------------------------------------------------------------------
# fixtures and fakes
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _umask():
    previous = os.umask(0o022)
    yield
    os.umask(previous)


@pytest.fixture
def layout(tmp_path: Path) -> Layout:
    for d in ("run", "var_tmp", "tool"):
        (tmp_path / d).mkdir(mode=0o755)
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
    )


def make_fx(layout: Layout, *, backstop_max: int = 20, activation_id: str = ACT_ID) -> ActivationFixture:
    import pwd

    fixture = ActivationFixture(
        layout,
        activation_id,
        BOOT,
        _baseline(),
        operator_user=pwd.getpwuid(os.getuid()).pw_name,
        params=Params(pk_op_ms=5_000, lock_wait_ms=1_000, backstop_max=backstop_max),
    )
    fixture.write_authority()
    return fixture


@pytest.fixture
def fx(layout: Layout) -> ActivationFixture:
    return make_fx(layout)


class Units:
    """DI-1 and DI-4 fake. Records every unit it is asked about."""

    def __init__(self, events: Events | None = None, *, holder="inactive", capture="inactive", disarm=STOPPED):
        self.events = events if events is not None else Events()
        self.holder = holder
        self.capture = capture
        self.disarm = disarm
        self.reads: list[str] = []
        self.disarms: list[str] = []
        self.lock = threading.Lock()

    def read_unit(self, unit, props):
        with self.lock:
            self.reads.append(unit)
        self.events.mark(f"di1:{unit}")
        if unit == HOLDER:
            if isinstance(self.holder, str):
                return ControlOk({UnitProperty.ACTIVE_STATE: self.holder})
            return self.holder
        if unit == CAPTURE_UNIT:
            values = {UnitProperty.ACTIVE_STATE: self.capture, UnitProperty.INACTIVE_ENTER_TIMESTAMP_MONOTONIC: 0}
            return ControlOk({p: values[p] for p in props})
        raise AssertionError(f"read of an unexpected unit {unit}")

    def disarm_backstop(self, activation_id):
        with self.lock:
            self.disarms.append(activation_id)
        self.events.mark("di4")
        return self.disarm


class Services:
    def __init__(self, units: Units, *, pk=None, baseline="same"):
        self._units = units
        self._pk = pk or FakePk(units.events)
        self._baseline = FakeBaseline(units.events, _baseline() if baseline == "same" else baseline)

    def units(self, params):
        return self._units

    def pk(self, params):
        return self._pk

    def baseline(self, params):
        return self._baseline


def fire(layout: Layout, a2: str, units: Units, **services_kw):
    proc = build_backstop(
        ACT_ID, a2, invocation_id=INV, parent_pid=4242, layout=layout,
        services=Services(units, **services_kw), clock=FakeClock(),
    )
    return proc.run()


def stop_post(layout: Layout, fx: ActivationFixture, *, pk=PkOutcome.NOT_AUTHORIZED, units: Units | None = None):
    """A completed RT-3 attempt: the record a backstop firing later decides on."""
    units = units or Units()
    proc = build_procedure(
        ACT_ID, fx.a2_sha256, invocation_id=INV, parent_pid=1, layout=layout,
        services=Services(units, pk=FakePk(units.events, outcome=pk)), clock=FakeClock(),
    )
    return proc.run()


def attempt_dirs(layout: Layout, activation_id: str = ACT_ID) -> list[str]:
    return sorted(p.name for p in Path(layout.var_tmp).glob(f"{activation_id}-deact-*"))


def records(layout: Layout) -> list[str]:
    d = Path(layout.store, "activation")
    return sorted(p.name for p in d.iterdir()) if d.exists() else []


def record_doc(layout: Layout, k: int) -> dict:
    doc = parse_canonical(Path(layout.store, f"activation/{ACT_ID}.deact-{k}.json").read_bytes())
    validate_record(doc)
    return doc


def put_record(layout: Layout, name: str, data: bytes, mode: int = 0o444) -> Path:
    path = Path(layout.store, "activation", name)
    path.write_bytes(data)
    os.chmod(path, mode)
    return path


def make_attempt(layout: Layout, k: int, *, trigger: str | None = "backstop", activation_id: str = ACT_ID) -> Path:
    """An earlier attempt directory; ``trigger=None`` leaves it without a journal."""
    d = Path(layout.var_tmp, f"{activation_id}-deact-{k}-evidence")
    d.mkdir(mode=0o755)
    os.chmod(d, 0o755)
    if trigger is not None:
        line = serialize_line(
            JournalKind.ATTEMPT, seq=1, prev=GENESIS, run=attempt_run(activation_id, k), op="run-start",
            fields={
                "trigger": trigger,
                "boot_id": BOOT,
                "holder_state": "inactive",
                "lock": {"object": "absent", "mode": "absent", "wait_ms": 0},
                "helper": {"role": trigger, "tool_sha256": "absent"},
                "provenance": {"parent_pid": 1, "invocation_id": "absent"},
            },
        )
        (d / "journal").write_bytes(line)
        os.chmod(d / "journal", 0o644)
    return d


def terminal_lines(layout: Layout) -> list[dict]:
    path = Path(layout.store, "backstop", f"{ACT_ID}.journal")
    return [json.loads(line) for line in path.read_bytes().splitlines()] if path.exists() else []


class Explode:
    """Any attribute access fails: proves a branch touched nothing."""

    def __init__(self, name: str):
        self._name = name

    def __getattr__(self, attr):
        raise AssertionError(f"{self._name}.{attr} must not be used on this branch")


def never(*_a, **_k):
    raise AssertionError("this branch must not reach the bound or CL")


def bare(layout: Layout, units, **ports) -> BackstopProcedure:
    defaults = dict(
        records=Explode("records"), fs=Explode("fs"), journals=Explode("journals"), guard=Explode("guard"),
        limits=never, cleanup=never, grant_check=never,
    )
    defaults.update(ports)
    return BackstopProcedure(ActivationPaths(layout, ACT_ID), units=units, **defaults)


# ---------------------------------------------------------------------------
# parameters: backstop_max in the H-1 authority (RT4.BS4.1)
# ---------------------------------------------------------------------------


def test_backstop_max_defaults_to_20_and_is_part_of_the_closed_params():
    assert Params().backstop_max == 20
    assert "backstop_max" in Params().to_doc()
    doc = Params().to_doc()
    del doc["backstop_max"]
    with pytest.raises(AuthorityError):
        Params.from_doc(doc)


@pytest.mark.parametrize("value,ok", [(1, True), (20, True), (99, True), (0, False), (100, False), (True, False), ("5", False)])
def test_backstop_max_accepts_only_1_to_99(value, ok):
    doc = {**Params().to_doc(), "backstop_max": value}
    if ok:
        assert Params.from_doc(doc).backstop_max == value
    else:
        with pytest.raises(AuthorityError):
            Params.from_doc(doc)


def test_the_bound_comes_from_h1_never_from_the_environment(layout, monkeypatch):
    fx = make_fx(layout, backstop_max=1)
    fx.activate()
    monkeypatch.setenv("backstop_max", "99")
    make_attempt(layout, 1)
    units = Units()
    out = fire(layout, fx.a2_sha256, units)
    assert out.terminal is BsTerminal.BOUND_REACHED


# ---------------------------------------------------------------------------
# BS-1 — holder ownership (RT4.BS1.1, RT4.BS.1)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("state", ["activating", "active", "deactivating", "reloading"])
def test_a_holder_that_owns_the_activation_exits_0_having_touched_nothing(layout, state):
    units = Units(holder=state)
    out = bare(layout, units).run()
    assert out.terminal is BsTerminal.HOLDER_ACTIVE and out.exit_code == 0
    assert units.reads == [HOLDER] and units.disarms == []
    assert out.lines == [f"rp11-bs holder-active {ACT_ID} state={state}"]
    assert not Path(layout.store).exists() and attempt_dirs(layout) == []


@pytest.mark.parametrize(
    "result",
    [
        ControlError("timeout"),
        ControlError("disconnected"),
        ControlError("invalid-reply", "unexpected reply for ActiveState"),
        ControlError("org.freedesktop.systemd1.NoSuchUnit", "no unit"),
        ControlError("org.freedesktop.DBus.Error.UnknownObject"),
        ControlError("connect-failed"),
        ControlRefused(RefusalReason.NOT_AUTHORIZED),
        ControlRefused(RefusalReason.INVALID_REQUEST),
        ControlOk({UnitProperty.ACTIVE_STATE: "maintenance"}),
        ControlOk({UnitProperty.ACTIVE_STATE: "refreshing"}),
        ControlOk({UnitProperty.ACTIVE_STATE: ""}),
        ControlOk({UnitProperty.ACTIVE_STATE: 0}),
        ControlOk({}),
        ControlOk(None),
    ],
)
def test_a_holder_read_that_is_not_a_known_state_fails_closed_without_any_access(layout, result):
    units = Units(holder=result)
    out = bare(layout, units).run()
    assert out.terminal is BsTerminal.HOLDER_UNOBSERVED and out.exit_code == 10
    assert units.disarms == [] and units.reads == [HOLDER]
    assert re.fullmatch(rf"rp11-bs holder-unobserved {ACT_ID} read=(error|refused|unexpected-state)", out.lines[0])
    assert not Path(layout.store).exists() and attempt_dirs(layout) == []


@pytest.mark.parametrize(
    "result,state",
    [("inactive", "inactive"), ("failed", "failed"), (ControlRefused(RefusalReason.NOT_LOADED), "not-loaded")],
)
def test_a_holder_that_is_gone_or_not_loaded_continues_to_bs2(layout, fx, result, state):
    fx.activate()
    units = Units(holder=result)
    out = fire(layout, fx.a2_sha256, units)
    assert out.terminal is BsTerminal.CLEANUP and out.cleanup.terminal is Terminal.ST1_VERIFIED
    run_start = json.loads(Path(layout.var_tmp, f"{ACT_ID}-deact-1-evidence/journal").read_bytes().splitlines()[0])
    assert run_start["trigger"] == "backstop" and run_start["holder_state"] == state
    assert record_doc(layout, 1)["holder"]["active_state_at_start"] == state


class BusUnits:
    """The real manager adapter over a scripted bus, for DI-1 and DI-4."""

    def __init__(self, *, active_state="inactive", get=None, stop=None, signals=()):
        self.conns: list[FakeConnection] = []
        self._get = get if get is not None else props_handler({"ActiveState": ("s", active_state)})
        self._stop = stop
        self._signals = signals

    def connect(self):
        conn = FakeConnection({"Get": self._get, "StopUnit": self._stop}, signals=list(self._signals))
        self.conns.append(conn)
        return conn

    def adapter(self) -> SystemdManagerAdapter:
        return SystemdManagerAdapter(self.connect)

    def calls(self, member: str):
        return [c for conn in self.conns for c in conn.calls if c.member == member]


@pytest.mark.parametrize(
    "get",
    [BusTimeout("t"), BusDisconnected("gone"), BusReply("v", (("u", 1),)), BusReply("s", ("x",)),
     BusError("org.freedesktop.DBus.Error.NoReply", "x"), BusError("org.freedesktop.DBus.Error.AccessDenied", "x")],
)
def test_bs1_through_the_real_adapter_never_reads_an_error_as_inactive(layout, get):
    bus = BusUnits(get=get)
    out = bare(layout, bus.adapter()).run()
    assert out.terminal is BsTerminal.HOLDER_UNOBSERVED and bus.calls("StopUnit") == []
    (read,) = bus.calls("Get")
    assert read.path.endswith("/rp11_2dact_2d20261013T101500Z_2d0a1b2c3d_2eservice")
    assert read.body == ("org.freedesktop.systemd1.Unit", "ActiveState")


# ---------------------------------------------------------------------------
# BS-2 / BS-3 — the latest record (RT4.BS2.1, RT4.BS2.2, RT4.BS3.1)
# ---------------------------------------------------------------------------


def test_no_record_continues_to_bs4(layout, fx):
    fx.activate()
    units = Units()
    out = fire(layout, fx.a2_sha256, units)
    assert out.terminal is BsTerminal.CLEANUP and units.disarms == []
    assert out.lines[0] == f"rp11-bs cleanup {ACT_ID} k=1 trigger=backstop lock=held terminal=st1-verified"
    assert out.lines[1].startswith(f"rp11-cl st1-verified {ACT_ID} k=1 ")


def test_a_valid_latest_st1_verified_record_disarms_once_and_exits_0(layout, fx):
    fx.activate()
    assert stop_post(layout, fx).terminal is Terminal.ST1_VERIFIED
    before = attempt_dirs(layout), records(layout)
    units = Units()
    out = fire(layout, fx.a2_sha256, units)
    assert out.terminal is BsTerminal.DISARMED and out.exit_code == 0
    assert units.disarms == [ACT_ID] and out.disarm_calls == 1
    assert out.lines == [f"rp11-bs disarmed {ACT_ID} branch=bs-2 k=1 disarm=stopped"]
    assert (attempt_dirs(layout), records(layout)) == before  # no attempt, journal or record
    assert units.reads == [HOLDER]  # no CL: the capture unit is never read


def _unconfirmed_hard_stop(layout, fx) -> dict:
    """The rule is gone and nothing else is left, but Polkit's effect was never confirmed."""
    fx.activate()
    out = stop_post(layout, fx, pk=PkOutcome.UNCONFIRMED)
    assert out.terminal is Terminal.HARD_STOP
    return record_doc(layout, 1)


def _safe_hard_stop(layout, fx, *, activate: bool = True) -> dict:
    """A genuine hard-stop: a foreign replacement of the rule is kept (never removed), no
    A1-intact object remains and Polkit positively reports ``not-authorized``."""
    if activate:
        fx.activate()
    _replace_with_same_bytes(fx.paths.rule)
    out = stop_post(layout, fx, pk=PkOutcome.NOT_AUTHORIZED)
    assert out.terminal is Terminal.HARD_STOP
    return record_doc(layout, 1)


def test_a_qualifying_hard_stop_disarms_at_bs3(layout, fx):
    doc = _safe_hard_stop(layout, fx)
    assert doc["active_rule"]["class"] == "present-foreign-unremoved"
    assert [r["class"] for r in doc["residual"]] == ["present-foreign-unremoved"]
    assert doc["grant_check"]["after_cleanup"] == doc["pk"]["outcome"] == "not-authorized"
    units = Units()
    out = fire(layout, fx.a2_sha256, units)
    assert out.terminal is BsTerminal.DISARMED and units.disarms == [ACT_ID]
    assert out.lines == [f"rp11-bs disarmed {ACT_ID} branch=bs-3 k=1 disarm=stopped"]


def test_a_hard_stop_with_an_a1_intact_object_left_runs_cl_again(layout, fx):
    fx.activate()
    planted = Path(fx.paths.tree_p, "planted")  # tree P stays A1-intact but nonempty
    planted.write_text("x")
    assert stop_post(layout, fx).terminal is Terminal.HARD_STOP
    assert any(r["class"] == "present-nonempty-unremoved" for r in record_doc(layout, 1)["residual"])
    units = Units()
    out = fire(layout, fx.a2_sha256, units)
    assert out.terminal is BsTerminal.CLEANUP and units.disarms == []
    assert record_doc(layout, 2)["trigger"] == "backstop"


# the unconfirmed-Polkit hard-stop is never BS-3 (re-review finding 1) --------------


def test_a_removed_rule_with_unconfirmed_polkit_takes_bs4_and_never_disarms(layout, fx):
    doc = _unconfirmed_hard_stop(layout, fx)
    assert doc["active_rule"]["class"] == "removed-earlier" and doc["residual"] == []
    assert doc["grant_check"]["after_cleanup"] == doc["pk"]["outcome"] == "unconfirmed"
    assert hard_stop_permits_disarm(doc) is False
    units = Units()
    out = fire(layout, fx.a2_sha256, units)  # Polkit now answers not-authorized
    assert out.terminal is BsTerminal.CLEANUP and out.cleanup.k == 2 and units.disarms == []
    assert record_doc(layout, 2)["trigger"] == "backstop"
    # the later cleanup established not-authorized: the normal BS-2 disarm works again
    last = Units()
    done = fire(layout, fx.a2_sha256, last)
    assert done.terminal is BsTerminal.DISARMED and last.disarms == [ACT_ID]
    assert done.lines == [f"rp11-bs disarmed {ACT_ID} branch=bs-2 k=2 disarm=stopped"]


@pytest.mark.parametrize("pk", [PkOutcome.UNCONFIRMED, PkOutcome.AUTHORIZED])
def test_persistently_unconfirmed_polkit_never_calls_di4_and_stays_bounded(layout, pk):
    fx = make_fx(layout, backstop_max=3)
    fx.activate()
    assert stop_post(layout, fx, pk=PkOutcome.UNCONFIRMED).terminal is Terminal.HARD_STOP
    seen = Units()
    codes = [fire(layout, fx.a2_sha256, seen, pk=FakePk(seen.events, outcome=pk)).exit_code for _ in range(6)]
    assert seen.disarms == []
    # the stop-post attempt is not counted: B = 3 backstop attempts, then withheld terminals
    assert codes == [1, 1, 1, 12, 12, 12]
    assert len(attempt_dirs(layout)) == 4
    assert {t["disarm"] for t in terminal_lines(layout)} == {"withheld"}


@pytest.mark.parametrize("after", ["authorized", "unconfirmed", "absent", "Not-Authorized", None, 0, True])
@pytest.mark.parametrize("pk_value", ["not-authorized", "unconfirmed"])
def test_bs3_requires_positive_not_authorized_in_both_fields_for_every_rule_class(hard_doc, after, pk_value):
    for rule in sorted(RULE_CLASSES - {"removed-unconfirmed", "grant-unremovable", "present-uninspected-unremoved"}):
        doc = json.loads(json.dumps(hard_doc))
        doc["active_rule"]["class"] = rule
        doc["grant_check"]["after_cleanup"] = after
        doc["pk"]["outcome"] = pk_value
        assert hard_stop_permits_disarm(doc) is False, (rule, after, pk_value)


@pytest.mark.parametrize("drop", ["grant_check", "pk", "after_cleanup", "outcome"])
def test_bs3_a_missing_authorization_fact_is_not_proof(hard_doc, drop):
    doc = json.loads(json.dumps(hard_doc))
    if drop == "grant_check":
        del doc["grant_check"]
    elif drop == "pk":
        del doc["pk"]
    elif drop == "after_cleanup":
        del doc["grant_check"]["after_cleanup"]
    else:
        del doc["pk"]["outcome"]
    assert hard_stop_permits_disarm(doc) is False


# pure BS-3 predicate ------------------------------------------------------------


@pytest.fixture
def hard_doc(layout, fx) -> dict:
    return _safe_hard_stop(layout, fx)


@pytest.mark.parametrize("rule", sorted(RULE_CLASSES | {"absent", "something-else"}))
def test_bs3_rule_class_predicate(hard_doc, rule):
    doc = json.loads(json.dumps(hard_doc))
    doc["active_rule"]["class"] = rule
    expected = rule in RULE_CLASSES and rule not in {
        "removed-unconfirmed", "grant-unremovable", "present-uninspected-unremoved"
    }
    assert hard_stop_permits_disarm(doc) is expected


@pytest.mark.parametrize(
    "where", ["residual", "directory", "pass", "grant_id"],
)
@pytest.mark.parametrize("klass", sorted(A1_INTACT_KEPT))
def test_bs3_any_a1_intact_object_left_blocks_the_disarm(hard_doc, where, klass):
    doc = json.loads(json.dumps(hard_doc))
    if where == "residual":
        doc["residual"].append({"path": "/run/x", "class": klass})
    elif where == "directory":
        doc["directories"].append({"role": "tree-p", "path": "/run/x", "class": klass})
    elif where == "pass":
        doc["pass_config"]["class"] = klass
    else:
        doc["grant_identity"]["grant_id_class"] = klass
    assert hard_stop_permits_disarm(doc) is False


@pytest.mark.parametrize(
    "klass", ["present-damaged-unremoved", "present-foreign-unremoved", "s0", "removed", "pre-existing-kept"]
)
def test_bs3_damaged_foreign_and_unattributed_leftovers_do_not_block(hard_doc, klass):
    doc = json.loads(json.dumps(hard_doc))
    doc["residual"].append({"path": "/run/x", "class": klass})
    assert hard_stop_permits_disarm(doc) is True


@pytest.mark.parametrize("mutate", [
    lambda d: d["pass_config"].__setitem__("class", "absent"),
    lambda d: d["grant_identity"].__setitem__("grant_id_class", "absent"),
    lambda d: d["residual"].append({"path": "/run/x", "class": "unstated"}),
    lambda d: d["directories"].append(
        {"role": "tree-p", "path": "/run/x", "class": "unstated"}
    ),
    lambda d: d.__delitem__("residual"),
    lambda d: d["directories"].append("not-an-object"),
])
def test_bs3_an_unstated_or_malformed_class_is_not_proof(hard_doc, mutate):
    doc = json.loads(json.dumps(hard_doc))
    mutate(doc)
    assert hard_stop_permits_disarm(doc) is False


# the latest record only; never a fallback ----------------------------------------


def _st1_then(layout, fx, name: str, data: bytes, mode: int = 0o444):
    fx.activate()
    assert stop_post(layout, fx).terminal is Terminal.ST1_VERIFIED  # an older success, deact-1
    put_record(layout, name, data, mode)


def as_attempt(doc: dict, k: int) -> dict:
    """The same record as attempt ``k``: the attempt number and its own journal path."""
    journals = [dict(j) for j in doc["journals"]]
    journals[-1]["path"] = journals[-1]["path"].replace(
        f"-deact-{doc['attempt']}-evidence", f"-deact-{k}-evidence"
    )
    return {**doc, "attempt": k, "journals": journals}


@pytest.mark.parametrize("field", ["pk-unconfirmed", "after-cleanup-unconfirmed"])
def test_a_canonical_contradictory_greatest_record_never_lets_an_older_one_decide(layout, fx, field):
    """deact-1 is a verified success; deact-2 is canonical but claims two Polkit results."""
    fx.activate()
    assert stop_post(layout, fx).terminal is Terminal.ST1_VERIFIED
    doc = as_attempt(parse_canonical(_valid_bytes(layout)), 2)
    assert doc["grant_check"]["after_cleanup"] == doc["pk"]["outcome"] == "not-authorized"
    if field == "pk-unconfirmed":
        doc["pk"]["outcome"] = "unconfirmed"
    else:
        doc["grant_check"]["after_cleanup"] = "unconfirmed"
    with pytest.raises(RecordSchemaError):
        validate_record(doc)
    put_record(layout, f"{ACT_ID}.deact-2.json", canonical_bytes(doc))
    units = Units()
    out = fire(layout, fx.a2_sha256, units)
    assert units.disarms == [] and out.terminal is not BsTerminal.DISARMED
    assert out.terminal is BsTerminal.CLEANUP  # the contradictory record is BS-4; the older success is ignored


def _valid_bytes(layout) -> bytes:
    return Path(layout.store, f"activation/{ACT_ID}.deact-1.json").read_bytes()


@pytest.mark.parametrize(
    "case",
    ["non-canonical", "torn", "oversized", "empty", "wrong-mode", "foreign-group", "symlinked",
     "hard-linked", "other-activation", "attempt-mismatch", "schema-invalid", "act-kind", "directory"],
)
def test_a_bad_latest_record_never_falls_back_to_an_older_success(layout, fx, case):
    fx.activate()
    assert stop_post(layout, fx).terminal is Terminal.ST1_VERIFIED
    good = _valid_bytes(layout)
    doc = parse_canonical(good)
    name = f"{ACT_ID}.deact-2.json"
    target = Path(layout.store, "activation", name)
    owner = layout.owner
    if case == "non-canonical":
        put_record(layout, name, json.dumps(doc, indent=1).encode() + b"\n")
    elif case == "torn":
        put_record(layout, name, good[: len(good) // 2])
    elif case == "oversized":
        put_record(layout, name, good[:-1] + b" " * (1 << 20) + b"\n")
    elif case == "empty":
        put_record(layout, name, b"")
    elif case == "wrong-mode":
        put_record(layout, name, canonical_bytes({**doc, "attempt": 2}), 0o644)
    elif case == "foreign-group":
        owner = Owner(os.getuid(), os.getgid() + 1)
        put_record(layout, name, canonical_bytes({**doc, "attempt": 2}))
    elif case == "symlinked":
        target.symlink_to(Path(layout.store, f"activation/{ACT_ID}.deact-1.json"))
    elif case == "hard-linked":
        os.link(Path(layout.store, f"activation/{ACT_ID}.deact-1.json"), target)
    elif case == "other-activation":
        put_record(layout, name, canonical_bytes({**doc, "attempt": 2, "activation_id": OTHER_ID}))
    elif case == "attempt-mismatch":
        put_record(layout, name, good)  # deact-1's bytes under the name deact-2
    elif case == "schema-invalid":
        put_record(layout, name, canonical_bytes({**doc, "attempt": 2, "outcome": "st1-maybe"}))
    elif case == "act-kind":
        put_record(layout, name, canonical_bytes({**doc, "attempt": 2, "kind": "act"}))
    elif case == "directory":
        target.mkdir()
    store = LocalRecordStore(ActivationPaths(layout, ACT_ID).record_dir, owner)
    assert store.deact_attempts(ACT_ID)[-1] == 2
    data = store.read(name)
    assert branch_for_record(data, activation_id=ACT_ID, k=2) is Branch.BS4
    if case == "foreign-group":
        return  # the firing's store trusts the test user; the adapter refusal is what is pinned
    units = Units()
    out = fire(layout, fx.a2_sha256, units)
    assert units.disarms == [] and out.terminal is BsTerminal.CLEANUP
    assert out.cleanup.k == 2  # BS-4 ran CL; no older record decided


def test_a_replaced_record_with_valid_bytes_of_this_attempt_is_indistinguishable_by_design(layout, fx):
    """Only root can write the record directory: a root-made, valid record for this
    activation and attempt is a record. The store's own guards are what is pinned."""
    fx.activate()
    stop_post(layout, fx)
    doc = parse_canonical(_valid_bytes(layout))
    put_record(layout, f"{ACT_ID}.deact-2.json", canonical_bytes(as_attempt(doc, 2)))
    assert branch_for_record(
        LocalRecordStore(ActivationPaths(layout, ACT_ID).record_dir, layout.owner).read(f"{ACT_ID}.deact-2.json"),
        activation_id=ACT_ID, k=2,
    ) is Branch.BS2


def test_the_greatest_attempt_decides_even_when_an_older_one_succeeded(layout, fx):
    fx.activate()
    assert stop_post(layout, fx).terminal is Terminal.ST1_VERIFIED  # deact-1 st1-verified
    doc = parse_canonical(_valid_bytes(layout))
    hard = {**as_attempt(doc, 3), "outcome": "hard-stop", "failure": {"step": "CL-6", "class": "residual"},
            "st1": {**doc["st1"], "verified": False},
            "residual": [{**{k: 0 for k in ("uid", "gid", "mode", "size", "dev", "ino", "nlink")},
                          "path": "/run/x", "class": "unremovable", "type": "file", "xattr_names": [],
                          "sha256": "unreadable"}]}
    validate_record(hard)
    put_record(layout, f"{ACT_ID}.deact-3.json", canonical_bytes(hard))
    units = Units()
    out = fire(layout, fx.a2_sha256, units)
    assert units.disarms == [] and out.terminal is BsTerminal.CLEANUP


@pytest.mark.parametrize("error", [KeyError("x"), TypeError("x"), AttributeError("x"), IndexError("x"), AssertionError("x"),
                                   RecursionError("x"), ValueError("x"), OSError("x")])
def test_branch_for_record_is_defensively_fail_closed_if_the_validator_ever_leaks(layout, fx, monkeypatch, error):
    """Defence in depth: whatever escapes the validator, a record is BS-4 and never an exception."""
    fx.activate()
    assert stop_post(layout, fx).terminal is Terminal.ST1_VERIFIED
    good = _valid_bytes(layout)
    assert branch_for_record(good, activation_id=ACT_ID, k=1) is Branch.BS2

    def leaking(_doc):
        raise error

    monkeypatch.setattr("application.rp11.backstop.validate_record", leaking)
    assert branch_for_record(good, activation_id=ACT_ID, k=1) is Branch.BS4


NESTED_BREAKS = {
    "authority-absent": lambda d: d.__setitem__("authority", "absent"),
    "pk-absent": lambda d: d.__setitem__("pk", "absent"),
    "grant-identity-absent": lambda d: d.__setitem__("grant_identity", "absent"),
    "active-rule-incomplete": lambda d: d.__setitem__("active_rule", {"class": "removed-verified"}),
    "pass-config-incomplete": lambda d: d.__setitem__("pass_config", {"class": "removed"}),
    "children-not-a-list": lambda d: d["children"].__setitem__("entries", {}),
    "check-missing": lambda d: d["st1"]["checks"].pop("baseline-equal"),
    "journal-entry-short": lambda d: d["journals"][-1].pop("length"),
    "directories-of-strings": lambda d: d.__setitem__("directories", ["tree-p"]),
    "params-of-a-list": lambda d: d.__setitem__("params", []),
}


@pytest.mark.parametrize("case", sorted(NESTED_BREAKS))
def test_a_nested_malformed_latest_record_never_lets_the_older_success_decide(layout, fx, case):
    """The greatest attempt decides: a canonical latest record that is malformed *inside*
    is BS-4 (CL again), never BS-2 and never the older verified record's BS-2."""
    fx.activate()
    assert stop_post(layout, fx).terminal is Terminal.ST1_VERIFIED  # deact-1, valid, st1-verified
    doc = as_attempt(parse_canonical(_valid_bytes(layout)), 2)
    NESTED_BREAKS[case](doc)
    with pytest.raises(RecordSchemaError):
        validate_record(doc)
    put_record(layout, f"{ACT_ID}.deact-2.json", canonical_bytes(doc))
    units = Units()
    out = fire(layout, fx.a2_sha256, units)
    assert units.disarms == [] and out.terminal is BsTerminal.CLEANUP  # CL ran (its record name is taken)
    assert out.cleanup.k == 2 and out.cleanup.terminal is Terminal.RECORD_UNPUBLISHED


@pytest.mark.parametrize("junk", [
    f"{OTHER_ID}.deact-9.json", f"{ACT_ID}.deact-0.json", f"{ACT_ID}.deact-01.json", f"{ACT_ID}.deact-100.json",
    f"{ACT_ID}.deact-2.json.tmp", f".{ACT_ID}.deact-2.json", f"{ACT_ID}.act.json.bak", f"{ACT_ID}.deact-x.json",
])
def test_irrelevant_names_are_not_attempts(layout, fx, junk):
    fx.activate()
    stop_post(layout, fx)
    put_record(layout, junk, b"{}\n")
    store = LocalRecordStore(ActivationPaths(layout, ACT_ID).record_dir, layout.owner)
    assert store.deact_attempts(ACT_ID) == (1,)
    out = fire(layout, fx.a2_sha256, Units())
    assert out.terminal is BsTerminal.DISARMED


def test_record_enumeration_is_bounded_and_fails_closed(layout, fx, monkeypatch):
    fx.activate()
    stop_post(layout, fx)
    store = LocalRecordStore(ActivationPaths(layout, ACT_ID).record_dir, layout.owner)
    monkeypatch.setattr("adapters.rp11.fsops._MAX_RECORD_ENTRIES", 1)
    assert store.deact_attempts(ACT_ID) is None
    assert fire(layout, fx.a2_sha256, Units()).terminal is BsTerminal.CLEANUP  # BS-4, not a disarm


def test_an_unlistable_or_symlinked_record_directory_is_not_a_disarm(layout, fx):
    fx.activate()
    stop_post(layout, fx)
    rec = Path(layout.store, "activation")
    os.rename(rec, Path(layout.store, "real-activation"))
    rec.symlink_to(Path(layout.store, "real-activation"))
    store = LocalRecordStore(str(rec), layout.owner)
    assert store.deact_attempts(ACT_ID) is None
    os.chmod(Path(layout.store, "real-activation"), 0o775)
    assert LocalRecordStore(str(Path(layout.store, "real-activation")), layout.owner).deact_attempts(ACT_ID) is None


# ---------------------------------------------------------------------------
# DI-4 at all three call sites (RT4.BS2.2, RT4.BS3.1, RT4.BS4.2; Q6-6/Q6-7 default)
# ---------------------------------------------------------------------------

DISARM_RESULTS = [
    (STOPPED, "stopped", True),
    (ControlRefused(RefusalReason.NOT_LOADED), "not-loaded", True),
    (ControlError("timeout", effect_not_confirmed=True), "unconfirmed", False),
    (ControlError("disconnected", effect_not_confirmed=True), "unconfirmed", False),
    (ControlError("invalid-reply", "lost reply", effect_not_confirmed=True), "unconfirmed", False),
    (ControlError("completion-timeout", effect_not_confirmed=True), "unconfirmed", False),
    (ControlError("job-result", effect_not_confirmed=True), "unconfirmed", False),
    (ControlError("connect-failed"), "error", False),
    (ControlError("subscribe-failed"), "error", False),
    (ControlRefused(RefusalReason.NOT_AUTHORIZED), "refused", False),
    (ControlRefused(RefusalReason.INVALID_REQUEST), "refused", False),
]


@pytest.mark.parametrize("site", ["bs-2", "bs-3"])
@pytest.mark.parametrize("result,klass,confirmed", DISARM_RESULTS)
def test_bs2_and_bs3_disarm_fail_closed_without_retry_cl_or_record(layout, fx, site, result, klass, confirmed):
    if site == "bs-2":
        fx.activate()
        stop_post(layout, fx, pk=PkOutcome.NOT_AUTHORIZED)
    else:
        _safe_hard_stop(layout, fx)
    before = attempt_dirs(layout), records(layout)
    units = Units(disarm=result)
    out = fire(layout, fx.a2_sha256, units)
    assert units.disarms == [ACT_ID]  # exactly one call, this activation's timer
    assert (attempt_dirs(layout), records(layout)) == before
    assert CAPTURE_UNIT not in units.reads  # CL never ran
    if confirmed:
        assert out.terminal is BsTerminal.DISARMED and out.exit_code == 0
    else:
        assert out.terminal is BsTerminal.DISARM_UNCONFIRMED and out.exit_code == 11
        assert "stopped" not in out.lines[0]
    assert out.lines == [f"rp11-bs {out.terminal.value} {ACT_ID} branch={site} k=1 disarm={klass}"]


@pytest.mark.parametrize("result,klass,_confirmed", DISARM_RESULTS)
def test_the_terminal_disarm_is_one_call_one_line_and_never_success(layout, result, klass, _confirmed):
    fx = make_fx(layout, backstop_max=2)
    fx.activate()
    os.unlink(fx.paths.rule)  # the rule path is observed absent: the bound may disarm
    make_attempt(layout, 1)
    make_attempt(layout, 2)
    units = Units(disarm=result)
    out = fire(layout, fx.a2_sha256, units)
    assert out.terminal is BsTerminal.BOUND_REACHED and out.exit_code == 12
    assert units.disarms == [ACT_ID] and CAPTURE_UNIT not in units.reads
    assert terminal_lines(layout) == [
        {"schema": "rp11-backstop-terminal/1", "op": "backstop-terminal", "activation_id": ACT_ID,
         "reason": "backstop-max", "disarm": klass}
    ]
    assert out.lines == [f"rp11-bs bound-reached {ACT_ID} reason=backstop-max disarm={klass}"]
    assert records(layout) == [] and attempt_dirs(layout) == [f"{ACT_ID}-deact-1-evidence", f"{ACT_ID}-deact-2-evidence"]
    assert not os.path.lexists(fx.paths.rule)  # unchanged: nothing entered CL, not even CL-G


@pytest.mark.parametrize("site", ["bs-2", "bs-3", "bs-4"])
@pytest.mark.parametrize(
    "stop,signals,klass",
    [
        (job_reply(JOB), [removed(job=JOB, unit=TIMER)], "stopped"),
        (BusError("org.freedesktop.systemd1.NoSuchUnit", "not loaded"), [], "not-loaded"),
        (BusTimeout("no reply"), [], "unconfirmed"),
        (BusDisconnected("gone"), [], "unconfirmed"),
        (BusReply("s", ("lost",)), [], "unconfirmed"),  # the job path never arrived
        (job_reply(JOB), [], "unconfirmed"),  # no JobRemoved before the deadline
        (job_reply(JOB), [removed(job="/org/freedesktop/systemd1/job/1", unit=TIMER)], "unconfirmed"),
        (job_reply(JOB), [removed(job=JOB, unit=TIMER, result="canceled")], "unconfirmed"),
        (BusError("org.freedesktop.DBus.Error.AccessDenied", "no"), [], "refused"),
    ],
)
def test_all_three_sites_through_the_real_adapter(layout, site, stop, signals, klass):
    """BS-2, BS-3 and the BS-4 terminal disarm each send exactly one StopUnit for
    this activation's derived timer, in mode ``fail``, and never retry."""
    fx = make_fx(layout, backstop_max=1)
    fx.activate()
    if site == "bs-4":
        os.unlink(fx.paths.rule)  # absent rule path: the bound may disarm
        make_attempt(layout, 1)
    else:
        if site == "bs-2":
            stop_post(layout, fx, pk=PkOutcome.NOT_AUTHORIZED)
        else:
            _safe_hard_stop(layout, fx, activate=False)
    before = attempt_dirs(layout), records(layout)
    bus = BusUnits(stop=stop, signals=signals)
    paths = ActivationPaths(layout, ACT_ID)
    out = BackstopProcedure(
        paths,
        units=bus.adapter(),
        records=LocalRecordStore(paths.record_dir, layout.owner),
        fs=LocalActivationFs(layout.owner),
        journals=LocalActivationFs(layout.owner),
        guard=LocalBackstopGuard(layout.store, ACT_ID, layout.owner),
        limits=lambda: (1, 1 << 20),
        cleanup=never,
        grant_check=lambda: PkOutcome.NOT_AUTHORIZED,
    ).run()
    (call,) = bus.calls("StopUnit")
    assert call.body == (TIMER, "fail")
    holder_reads = [c for c in bus.calls("Get") if "_2eservice" in c.path]
    assert [c.body for c in holder_reads] == [("org.freedesktop.systemd1.Unit", "ActiveState")]
    assert all(c.path.endswith(("_2eservice", "_2dbackstop_2etimer")) for c in bus.calls("Get"))
    assert f"disarm={klass}" in out.lines[0]
    assert (attempt_dirs(layout), records(layout)) == before
    if site == "bs-4":
        assert out.exit_code == 12 and terminal_lines(layout)[0]["disarm"] == klass
    else:
        assert out.exit_code == (0 if klass in {"stopped", "not-loaded"} else 11)


# ---------------------------------------------------------------------------
# BS-4 — the bound: B-1, B, B+1 and k = 99 / 100 (RT4.BS4.1, RT4.BS4.2, RT4.CL0)
# ---------------------------------------------------------------------------


def test_b_minus_1_backstop_attempts_still_enter_cl_and_b_then_stops(layout):
    fx = make_fx(layout, backstop_max=3)
    fx.activate()
    make_attempt(layout, 1)
    make_attempt(layout, 2)  # B-1 = 2 earlier backstop firings ran CL
    Path(fx.paths.tree_p, "planted").write_text("x")  # every CL hard-stops: BS-2/3 never end it
    units = Units()
    out = fire(layout, fx.a2_sha256, units)
    assert out.terminal is BsTerminal.CLEANUP and out.cleanup.k == 3 and out.exit_code == 1  # the B-th
    assert record_doc(layout, 3)["trigger"] == "backstop"
    # firing B+1: three backstop attempts exist -> terminal; and again for B+2
    for n in (1, 2):
        units = Units()
        out = fire(layout, fx.a2_sha256, units)
        assert out.terminal is BsTerminal.BOUND_REACHED and units.disarms == [ACT_ID]
        assert len(terminal_lines(layout)) == n
    assert attempt_dirs(layout) == [f"{ACT_ID}-deact-{k}-evidence" for k in (1, 2, 3)]


def test_successive_firings_terminate_at_b(layout):
    """Real firings only: each hard-stops (a planted file keeps tree P nonempty),
    exactly B enter CL, then every later firing is terminal."""
    fx = make_fx(layout, backstop_max=4)
    fx.activate()
    Path(fx.paths.tree_p, "planted").write_text("x")
    codes = []
    for _ in range(7):
        codes.append(fire(layout, fx.a2_sha256, Units()).exit_code)
    assert codes == [1, 1, 1, 1, 12, 12, 12]
    assert len(attempt_dirs(layout)) == 4 and len(terminal_lines(layout)) == 3
    assert {record_doc(layout, k)["trigger"] for k in range(1, 5)} == {"backstop"}


def test_stop_post_attempts_do_not_count_against_b(layout):
    fx = make_fx(layout, backstop_max=1)
    fx.activate()
    make_attempt(layout, 1, trigger="stop-post")
    make_attempt(layout, 2, trigger="stop-post")
    out = fire(layout, fx.a2_sha256, Units())
    assert out.terminal is BsTerminal.CLEANUP and out.cleanup.k == 3


@pytest.mark.parametrize("variant", ["no-journal", "empty", "torn", "garbage", "other-run", "bad-trigger-field"])
def test_an_attempt_not_provably_another_trigger_counts_against_b(layout, variant):
    fx = make_fx(layout, backstop_max=1)
    fx.activate()
    d = make_attempt(layout, 1, trigger=None if variant == "no-journal" else "stop-post")
    journal = d / "journal"
    if variant == "empty":
        journal.write_bytes(b"")
    elif variant == "torn":
        journal.write_bytes(journal.read_bytes()[:-5])
    elif variant == "garbage":
        journal.write_bytes(b"not json\n")
    elif variant == "other-run":
        journal.write_bytes(journal.read_bytes().replace(b"deact-1", b"deact-7"))
    elif variant == "bad-trigger-field":
        journal.write_bytes(journal.read_bytes().replace(b'"trigger":"stop-post"', b'"trigger":"Stop Post"'))
    assert fire(layout, fx.a2_sha256, Units()).terminal is BsTerminal.BOUND_REACHED


def test_prospective_k_99_enters_cl_and_k_100_is_terminal(layout):
    fx = make_fx(layout, backstop_max=99)
    fx.activate()
    for k in range(1, 99):
        make_attempt(layout, k, trigger="stop-post")
    Path(fx.paths.tree_p, "planted").write_text("x")  # hard-stop: BS-2 cannot end it
    out = fire(layout, fx.a2_sha256, Units())
    assert out.terminal is BsTerminal.CLEANUP and out.cleanup.k == 99
    assert record_doc(layout, 99)["attempt"] == 99
    units = Units()
    out = fire(layout, fx.a2_sha256, units)  # 99 attempts exist: k would be 100
    assert out.terminal is BsTerminal.BOUND_REACHED and units.disarms == [ACT_ID]
    assert terminal_lines(layout)[-1]["reason"] == "attempt-limit"
    assert not Path(layout.var_tmp, f"{ACT_ID}-deact-100-evidence").exists()


def test_squatted_prefix_names_move_k_toward_the_limit_like_cl0(layout):
    fx = make_fx(layout, backstop_max=99)
    fx.activate()
    for k in range(1, 98):
        make_attempt(layout, k, trigger="stop-post")
    Path(layout.var_tmp, f"{ACT_ID}-deact-squat").mkdir()
    Path(layout.var_tmp, f"{ACT_ID}-deact-also").mkdir()
    out = fire(layout, fx.a2_sha256, Units())
    assert out.terminal is BsTerminal.BOUND_REACHED and terminal_lines(layout)[-1]["reason"] == "attempt-limit"
    assert exact_attempts(tuple(attempt_dirs(layout)), ACT_ID) == tuple(range(1, 98))


def test_unlistable_attempts_never_enter_cl_nor_disarm(layout, fx):
    fx.activate()
    os.chmod(layout.var_tmp, 0o000)
    try:
        units = Units()
        out = fire(layout, fx.a2_sha256, units)
    finally:
        os.chmod(layout.var_tmp, 0o755)
    assert out.terminal is BsTerminal.ATTEMPTS_UNOBSERVABLE and out.exit_code == 15
    assert units.disarms == [] and os.path.exists(fx.paths.rule)


# terminal line durability -------------------------------------------------------


def _guard_with(monkeypatch, io):
    original = backstop_root.LocalBackstopGuard
    monkeypatch.setattr(backstop_root, "LocalBackstopGuard", lambda *a, **k: original(*a, io=io, **k))


@pytest.mark.parametrize("io", [
    lambda: FailingIO(fail_write_at=1),  # short write
    lambda: FailingIO(fail_fsync_at=3),  # the line's fsync (store fsync, dir fsync, line)
])
def test_a_terminal_line_that_is_not_durable_exits_13_with_no_record_or_cl(layout, monkeypatch, io):
    fx = make_fx(layout, backstop_max=1)
    fx.activate()
    os.unlink(fx.paths.rule)
    make_attempt(layout, 1)
    _guard_with(monkeypatch, io())
    units = Units()
    out = fire(layout, fx.a2_sha256, units)
    assert out.terminal is BsTerminal.TERMINAL_UNWRITABLE and out.exit_code == 13
    assert units.disarms == [ACT_ID] and records(layout) == [] and CAPTURE_UNIT not in units.reads
    assert out.lines == [f"rp11-bs terminal-unwritable {ACT_ID} reason=backstop-max disarm=stopped"]


def test_a_terminal_journal_at_its_cap_is_not_extended(layout, monkeypatch):
    fx = make_fx(layout, backstop_max=1)
    fx.activate()
    make_attempt(layout, 1)
    monkeypatch.setattr("adapters.rp11.fsops._MAX_TERMINAL_BYTES", 10)
    out = fire(layout, fx.a2_sha256, Units())
    assert out.terminal is BsTerminal.TERMINAL_UNWRITABLE
    assert Path(layout.store, "backstop", f"{ACT_ID}.journal").read_bytes() == b""


@pytest.mark.parametrize("damage", ["store-writable", "dir-mode", "journal-mode", "journal-symlink", "journal-hardlink"])
def test_an_untrustworthy_terminal_journal_is_unavailable_never_written(layout, damage):
    fx = make_fx(layout, backstop_max=1)
    fx.activate()
    os.unlink(fx.paths.rule)
    make_attempt(layout, 1)
    bdir = Path(layout.store, "backstop")
    bdir.mkdir(mode=0o755)
    journal = bdir / f"{ACT_ID}.journal"
    if damage == "store-writable":
        os.chmod(layout.store, 0o775)
    elif damage == "dir-mode":
        os.chmod(bdir, 0o700)
    elif damage == "journal-mode":
        journal.write_bytes(b"")
        os.chmod(journal, 0o666)
    elif damage == "journal-symlink":
        (bdir / "elsewhere").write_bytes(b"")
        journal.symlink_to(bdir / "elsewhere")
    elif damage == "journal-hardlink":
        journal.write_bytes(b"")
        os.chmod(journal, 0o644)
        os.link(journal, bdir / "second-name")
    guard = LocalBackstopGuard(layout.store, ACT_ID, layout.owner)
    assert guard.acquire() is GuardMode.UNAVAILABLE
    units = Units()
    out = fire(layout, fx.a2_sha256, units)
    assert out.terminal is BsTerminal.TERMINAL_UNWRITABLE and units.disarms == [ACT_ID]
    for path in bdir.iterdir():
        assert not path.is_file() or path.is_symlink() or path.read_bytes() == b""


def test_the_terminal_journal_and_its_directory_are_created_root_only(layout):
    fx = make_fx(layout, backstop_max=1)
    fx.activate()
    make_attempt(layout, 1)
    fire(layout, fx.a2_sha256, Units())
    bdir = Path(layout.store, "backstop")
    assert bdir.stat().st_mode & 0o7777 == 0o755
    journal = bdir / f"{ACT_ID}.journal"
    assert journal.stat().st_mode & 0o7777 == 0o644 and journal.stat().st_nlink == 1
    line = journal.read_bytes()
    assert line == canonical_bytes(parse_canonical(line)) and len(line) < 256
    assert layout.run not in line.decode() and INV not in line.decode()


# ---------------------------------------------------------------------------
# shared CL with trigger backstop (RT4.CLG … RT4.CLOUT)
# ---------------------------------------------------------------------------


def test_backstop_cl_reaches_st1_verified_with_its_own_trigger(layout, fx):
    fx.activate()
    events = Events()
    units = Units(events)
    out = fire(layout, fx.a2_sha256, units)
    assert out.exit_code == 0 and out.cleanup.terminal is Terminal.ST1_VERIFIED
    doc = record_doc(layout, 1)
    assert doc["trigger"] == "backstop" and doc["helper"]["role"] == "backstop"
    assert doc["holder"]["invocation_id"] == "absent"  # a firing's INVOCATION_ID is not the holder's
    assert doc["release"]["first_rung"] == "cl-g" and doc["params"]["backstop_max"] == 20
    lines = Path(layout.var_tmp, f"{ACT_ID}-deact-1-evidence/journal").read_bytes().splitlines()
    first, second = json.loads(lines[0]), json.loads(lines[1])
    assert first["op"] == "run-start" and second["op"] == "cl-g"
    assert first["provenance"] == {"parent_pid": 4242, "invocation_id": INV}
    # CL-G stays the first cleanup act: no ext4 attempt before the grant removal
    assert units.reads[0] == HOLDER and units.disarms == []
    for path in (fx.paths.rule, fx.paths.pass_config, fx.paths.tree_p, fx.paths.grant_id, fx.paths.lock_dir):
        assert not os.path.lexists(path)
    # the next firing finds the record and disarms
    nxt = Units()
    assert fire(layout, fx.a2_sha256, nxt).terminal is BsTerminal.DISARMED and nxt.disarms == [ACT_ID]


def test_backstop_cl_hard_stop_and_grant_priority(layout, monkeypatch):
    fx = make_fx(layout)
    fx.activate()
    with open(fx.paths.pass_config, "r+b") as handle:
        handle.write(b"X")
    out = fire(layout, fx.a2_sha256, Units())
    assert out.exit_code == 1 and record_doc(layout, 1)["pass_config"]["class"] == "present-damaged-unremoved"
    assert not os.path.lexists(fx.paths.rule)
    # GP-R3: the second firing's journal breaks on its first line
    original = stop_post_root.LocalAttemptStore
    monkeypatch.setattr(stop_post_root, "LocalAttemptStore", lambda **kw: original(**kw, io=FailingIO(fail_write_at=1)))
    out = fire(layout, fx.a2_sha256, Units())
    assert out.exit_code == 4
    assert out.lines[1].startswith(f"rp11-cl grant-priority {ACT_ID} rule=")
    assert record_doc(layout, 1) and not Path(layout.store, f"activation/{ACT_ID}.deact-2.json").exists()


@pytest.mark.parametrize("call,_attribution,grr", GRR_FAULTS)
def test_backstop_cl_g_survives_a_persistent_grant_inspection_failure(layout, fx, monkeypatch, call, _attribution, grr):
    """RT4.CLG: a failed inspection of the grant is a closed CL-G outcome
    (``kept-uninspected``): the firing completes CL and records its attempt, the
    grant stays and still has its recovery owner. The next firings do not take BS-3
    (no DI-4) while the failure lasts, and the first one after it clears removes
    the grant, verifies non-authorization, and the following one disarms at BS-2."""
    fx.activate()
    info = os.stat(fx.paths.rule)
    fault = InspectionFault(monkeypatch, fx.paths.rule, call)
    units = Units()
    out = fire(layout, fx.a2_sha256, units)
    assert fault.hits >= 1
    assert out.terminal is BsTerminal.CLEANUP and out.exit_code == 1 and units.disarms == []
    assert out.cleanup.terminal is Terminal.HARD_STOP
    assert grr is GrrOutcome.KEPT_UNINSPECTED
    assert out.lines[0] == f"rp11-bs cleanup {ACT_ID} k=1 trigger=backstop lock=held terminal=hard-stop"
    doc = record_doc(layout, 1)
    assert doc["trigger"] == "backstop" and doc["outcome"] == "hard-stop" and not doc["st1"]["verified"]
    assert doc["grant_identity"]["cl_g"] == "kept-uninspected"
    assert doc["active_rule"]["class"] == "present-uninspected-unremoved"
    assert any(r["path"] == fx.paths.rule and r["class"] == "present-uninspected-unremoved" for r in doc["residual"])
    assert hard_stop_permits_disarm(doc) is False
    lines = Path(layout.var_tmp, f"{ACT_ID}-deact-1-evidence/journal").read_bytes().splitlines()
    assert [json.loads(x)["op"] for x in lines[:2]] == ["run-start", "cl-g"] and json.loads(lines[-1])["op"] == "run-end"
    fault.active = False
    assert os.lstat(fx.paths.rule).st_ino == info.st_ino  # kept, untouched
    fault.active = True
    # the failure persists: the next firing is not BS-3, calls no DI-4 and runs CL again
    nxt = Units()
    again = fire(layout, fx.a2_sha256, nxt)
    assert again.terminal is BsTerminal.CLEANUP and nxt.disarms == [] and again.cleanup.k == 2
    assert record_doc(layout, 2)["active_rule"]["class"] == "present-uninspected-unremoved"
    assert os.lstat(fx.paths.rule).st_ino == info.st_ino
    # the failure clears: the next automatic firing re-inspects, removes and verifies
    fault.active = False
    healed = Units()
    third = fire(layout, fx.a2_sha256, healed)
    assert third.terminal is BsTerminal.CLEANUP and third.cleanup.terminal is Terminal.ST1_VERIFIED
    assert healed.disarms == [] and not os.path.lexists(fx.paths.rule)
    # grant.id went with the first attempt's CL-5b: the journal identity (G-R1) removes it now
    assert record_doc(layout, 3)["active_rule"]["class"] == "removed-verified"
    # ... and only now does the normal verified path disarm the timer (BS-2)
    last = Units()
    done = fire(layout, fx.a2_sha256, last)
    assert done.terminal is BsTerminal.DISARMED and last.disarms == [ACT_ID]
    assert done.lines == [f"rp11-bs disarmed {ACT_ID} branch=bs-2 k=3 disarm=stopped"]
    assert attempt_dirs(layout) == [f"{ACT_ID}-deact-{k}-evidence" for k in (1, 2, 3)]


@pytest.mark.parametrize("call", ["read", "fstat"])
def test_persistent_uncertainty_through_backstop_max_never_disarms_the_owner(layout, monkeypatch, call):
    """The bound ends *attempts*, not the recovery owner of a grant that may still
    authorize: no DI-4, a terminal line per firing with ``disarm=withheld``, a
    non-zero exit, and no attempt directory beyond B."""
    fx = make_fx(layout, backstop_max=2)
    fx.activate()
    info = os.stat(fx.paths.rule)
    fault = InspectionFault(monkeypatch, fx.paths.rule, call)
    seen = Units()
    for k in (1, 2):
        out = fire(layout, fx.a2_sha256, seen)
        assert out.terminal is BsTerminal.CLEANUP and out.cleanup.k == k
    for n in (1, 2, 3):
        out = fire(layout, fx.a2_sha256, seen)
        assert out.terminal is BsTerminal.BOUND_REACHED and out.exit_code == 12
        assert out.lines == [f"rp11-bs bound-reached {ACT_ID} reason=backstop-max disarm=withheld"]
        assert len(terminal_lines(layout)) == n
    assert seen.disarms == [] and CAPTURE_UNIT in seen.reads
    assert terminal_lines(layout)[-1] == {
        "schema": "rp11-backstop-terminal/1", "op": "backstop-terminal", "activation_id": ACT_ID,
        "reason": "backstop-max", "disarm": "withheld",
    }
    assert attempt_dirs(layout) == [f"{ACT_ID}-deact-{k}-evidence" for k in (1, 2)]
    fault.active = False
    assert os.lstat(fx.paths.rule).st_ino == info.st_ino and Path(fx.paths.rule).read_bytes() == fx.rule_bytes


def test_the_attempt_limit_never_disarms_a_present_rule(layout, fx):
    fx.activate()
    for k in range(1, 100):
        make_attempt(layout, k, trigger="stop-post")
    units = Units()
    out = fire(layout, fx.a2_sha256, units)
    assert out.terminal is BsTerminal.BOUND_REACHED and out.exit_code == 12 and units.disarms == []
    assert out.lines == [f"rp11-bs bound-reached {ACT_ID} reason=attempt-limit disarm=withheld"]
    assert CAPTURE_UNIT not in units.reads and len(attempt_dirs(layout)) == 99 and os.path.exists(fx.paths.rule)


class _FsWithRule:
    """Only ``list_prefixed`` and ``observe``: what the bound reads."""

    def __init__(self, rule):
        self.rule = rule

    def list_prefixed(self, directory, prefix):
        return tuple(f"{ACT_ID}-deact-{k}-evidence" for k in range(1, 100))

    def observe(self, path, *, list_dir=False):
        return self.rule


@pytest.mark.parametrize("rule,disarmed", [(None, True), (UNREACHABLE, False)])
def test_the_bound_disarms_only_for_a_rule_path_observed_absent(layout, rule, disarmed):
    class Journals:
        def read_journal(self, *a, **k):
            return None

    class Guard:
        def acquire(self):
            return GuardMode.HELD

        def release(self):
            pass

        def append_terminal(self, fields):
            self.fields = fields

    class NoRecords:
        def deact_attempts(self, _activation_id):
            return ()

    units, guard = Units(), Guard()
    result = bare(
        layout, units, records=NoRecords(), fs=_FsWithRule(rule), journals=Journals(), guard=guard,
        limits=lambda: (20, 1 << 20), grant_check=lambda: PkOutcome.NOT_AUTHORIZED,
    ).run()
    assert result.terminal is BsTerminal.BOUND_REACHED
    assert units.disarms == ([ACT_ID] if disarmed else [])
    assert guard.fields["disarm"] == ("stopped" if disarmed else "withheld")


# the bound proves non-authorization; pathname absence is not proof (re-review finding 2) ----


def _bound_fixture(layout, reason: str):
    """Rule path absent, and the bound reached for ``reason``; returns (fx, units)."""
    if reason == "backstop-max":
        fx = make_fx(layout, backstop_max=2)
        fx.activate()
        make_attempt(layout, 1)
        make_attempt(layout, 2)
    else:
        fx = make_fx(layout, backstop_max=99)
        fx.activate()
        for k in range(1, 100):
            make_attempt(layout, k, trigger="stop-post")
    os.unlink(fx.paths.rule)
    return fx


@pytest.mark.parametrize("reason", ["backstop-max", "attempt-limit"])
@pytest.mark.parametrize("pk", [PkOutcome.UNCONFIRMED, PkOutcome.AUTHORIZED])
def test_the_bound_with_an_absent_rule_withholds_unless_polkit_says_not_authorized(layout, reason, pk):
    fx = _bound_fixture(layout, reason)
    before = attempt_dirs(layout), records(layout)
    units = Units()
    for n in (1, 2, 3):  # persistent: every firing is withheld, none creates anything
        out = fire(layout, fx.a2_sha256, units, pk=FakePk(units.events, outcome=pk))
        assert out.terminal is BsTerminal.BOUND_REACHED and out.exit_code == 12
        assert out.lines == [f"rp11-bs bound-reached {ACT_ID} reason={reason} disarm=withheld"]
        assert len(terminal_lines(layout)) == n
    assert units.disarms == [] and (attempt_dirs(layout), records(layout)) == before
    assert terminal_lines(layout)[-1]["disarm"] == "withheld"


@pytest.mark.parametrize("reason", ["backstop-max", "attempt-limit"])
def test_the_bound_with_an_absent_rule_and_not_authorized_disarms_exactly_once(layout, reason):
    fx = _bound_fixture(layout, reason)
    units = Units()
    pk = FakePk(units.events)
    out = fire(layout, fx.a2_sha256, units, pk=pk)
    assert out.terminal is BsTerminal.BOUND_REACHED and units.disarms == [ACT_ID] and pk.calls == 1
    assert out.lines == [f"rp11-bs bound-reached {ACT_ID} reason={reason} disarm=stopped"]
    assert terminal_lines(layout)[-1]["disarm"] == "stopped"


class _BoundFs(_FsWithRule):
    pass


@pytest.mark.parametrize(
    "check",
    [lambda: PkOutcome.UNCONFIRMED, lambda: PkOutcome.AUTHORIZED, lambda: "not-authorized", lambda: None,
     lambda: (_ for _ in ()).throw(RuntimeError("unavailable")),
     lambda: (_ for _ in ()).throw(OSError("polkit gone"))],
    ids=["unconfirmed", "authorized", "malformed-string", "none", "raises", "oserror"],
)
def test_the_terminal_check_must_return_the_not_authorized_member(layout, check):
    class Journals:
        def read_journal(self, *a, **k):
            return None

    class Guard:
        def acquire(self):
            return GuardMode.HELD

        def release(self):
            pass

        def append_terminal(self, fields):
            self.fields = fields

    class NoRecords:
        def deact_attempts(self, _activation_id):
            return ()

    units, guard = Units(), Guard()
    result = bare(
        layout, units, records=NoRecords(), fs=_BoundFs(None), journals=Journals(), guard=guard,
        limits=lambda: (20, 1 << 20), grant_check=check,
    ).run()
    assert result.terminal is BsTerminal.BOUND_REACHED and units.disarms == []
    assert guard.fields["disarm"] == "withheld"


@pytest.mark.parametrize("what", ["no-authority", "wrong-a2", "pk-raises"])
def test_the_adapter_check_is_unconfirmed_without_a_valid_authority_or_series(layout, monkeypatch, what):
    fx = _bound_fixture(layout, "attempt-limit")  # the default bound is not read from a bad authority
    a2 = fx.a2_sha256
    units = Units()
    kw = {}
    if what == "no-authority":
        for p in Path(layout.store).rglob("a2/*.json"):
            p.unlink()
    elif what == "wrong-a2":
        a2 = "0" * 64
    else:
        class Raises:
            def run(self, *a, **k):
                raise RuntimeError("series failed")

        kw["pk"] = Raises()
    out = fire(layout, a2, units, **kw)
    assert out.terminal is BsTerminal.BOUND_REACHED and units.disarms == []
    assert terminal_lines(layout)[-1]["disarm"] == "withheld"


def _replace_with_same_bytes(path: str) -> None:
    fresh = path + ".new"
    Path(fresh).write_bytes(Path(path).read_bytes())
    os.chmod(fresh, 0o644)
    os.rename(fresh, path)


def test_a_foreign_replacement_that_is_not_authorized_keeps_the_accepted_bs3(layout, fx):
    """A positively foreign rule is never removed. With Polkit *not authorized* the
    timer is disarmed as before (retrying could remove nothing)."""
    fx.activate()
    _replace_with_same_bytes(fx.paths.rule)
    ino = os.stat(fx.paths.rule).st_ino
    assert stop_post(layout, fx, pk=PkOutcome.NOT_AUTHORIZED).terminal is Terminal.HARD_STOP
    doc = record_doc(layout, 1)
    assert doc["active_rule"]["class"] == "present-foreign-unremoved" and hard_stop_permits_disarm(doc) is True
    units = Units()
    out = fire(layout, fx.a2_sha256, units)
    assert out.terminal is BsTerminal.DISARMED and units.disarms == [ACT_ID]
    assert out.lines == [f"rp11-bs disarmed {ACT_ID} branch=bs-3 k=1 disarm=stopped"]
    assert os.stat(fx.paths.rule).st_ino == ino  # never removed to make the timer stop


@pytest.mark.parametrize("change", ["foreign", "damaged"])
@pytest.mark.parametrize("pk", [PkOutcome.AUTHORIZED, PkOutcome.UNCONFIRMED])
def test_a_kept_rule_that_may_still_authorize_keeps_its_recovery_owner(layout, fx, change, pk):
    fx.activate()
    if change == "foreign":
        _replace_with_same_bytes(fx.paths.rule)
    else:
        os.chmod(fx.paths.rule, 0o664)
    ino = os.stat(fx.paths.rule).st_ino
    assert stop_post(layout, fx, pk=pk).terminal is Terminal.HARD_STOP
    doc = record_doc(layout, 1)
    assert doc["active_rule"]["class"] == f"present-{change}-unremoved"
    # a seek-not-authorized series that still sees the grant is ``unconfirmed``, never ``authorized``
    assert doc["grant_check"]["after_cleanup"] == "unconfirmed" and hard_stop_permits_disarm(doc) is False
    units = Units()
    out = fire(layout, fx.a2_sha256, units, pk=FakePk(units.events, outcome=pk))
    assert out.terminal is BsTerminal.CLEANUP and units.disarms == [] and out.cleanup.k == 2
    assert os.stat(fx.paths.rule).st_ino == ino and os.path.exists(fx.paths.rule)


@pytest.mark.parametrize("role", CloseFault.ROLES)
@pytest.mark.parametrize("shape", CloseFault.SHAPES)
def test_backstop_cl_g_survives_a_descriptor_close_error_on_the_grant(layout, fx, close_fault, role, shape):
    """RT4.CLG: a close error is not a crash; the firing records its CL-G outcome
    (the grant removed), verifies, and the next firing disarms at BS-2."""
    fx.activate()
    fault = close_fault(fx.paths.rule, role, shape)
    units = Units()
    out = fire(layout, fx.a2_sha256, units)
    assert fault.hits >= 1
    assert out.terminal is BsTerminal.CLEANUP and out.cleanup.terminal is Terminal.ST1_VERIFIED, out
    doc = record_doc(layout, 1)
    assert doc["trigger"] == "backstop" and doc["grant_identity"]["cl_g"] == "removed"
    assert not os.path.lexists(fx.paths.rule)
    lines = Path(layout.var_tmp, f"{ACT_ID}-deact-1-evidence/journal").read_bytes().splitlines()
    assert [json.loads(x)["op"] for x in lines[:2]] == ["run-start", "cl-g"] and json.loads(lines[-1])["op"] == "run-end"
    fault.active = False
    assert fire(layout, fx.a2_sha256, Units()).terminal is BsTerminal.DISARMED


@pytest.mark.parametrize("role", CloseFault.ROLES)
def test_backstop_cl_g_keeps_a_damaged_grant_through_a_close_error_and_the_bs3_rule(layout, fx, close_fault, role):
    fx.activate()
    os.chmod(fx.paths.rule, 0o664)
    info = os.stat(fx.paths.rule)
    fault = close_fault(fx.paths.rule, role)
    units = Units()
    out = fire(layout, fx.a2_sha256, units)
    assert fault.hits >= 1
    assert out.terminal is BsTerminal.CLEANUP and out.cleanup.terminal is Terminal.HARD_STOP and units.disarms == []
    assert record_doc(layout, 1)["grant_identity"]["cl_g"] == "kept-damaged"
    assert os.lstat(fx.paths.rule).st_ino == info.st_ino
    nxt = Units()
    again = fire(layout, fx.a2_sha256, nxt)
    assert again.terminal is BsTerminal.DISARMED and nxt.disarms == [ACT_ID]


@pytest.mark.parametrize(
    "crash,k",
    [("unlink:50-freedom-blades-rp11.rules", 1), (f"read-journal:{ACT_ID}-act-evidence", 2),
     ("unlink:pass-a.json", 2), ("unlink:grant.id", 2)],
)
def test_an_interrupted_backstop_cl_is_recovered_by_the_next_firing(layout, fx, monkeypatch, crash, k):
    """IM-B: a firing dies inside CL (CL-G, CL-1, CL-5, CL-5b); the next firing's CL
    finishes the activation and the one after that disarms at BS-2."""
    fx.activate()
    events = Events()
    original = stop_post_root.LocalActivationFs
    monkeypatch.setattr(stop_post_root, "LocalActivationFs", lambda owner: RecordingFs(owner, events, crash))
    with pytest.raises(Crash):
        fire(layout, fx.a2_sha256, Units())
    assert not Path(layout.store, f"activation/{ACT_ID}.deact-1.json").exists()
    # the guard's flock died with the process image: a fresh firing is not "busy"
    monkeypatch.setattr(stop_post_root, "LocalActivationFs", original)
    out = fire(layout, fx.a2_sha256, Units())
    assert out.cleanup is not None and out.cleanup.terminal is Terminal.ST1_VERIFIED and out.cleanup.k == k
    if k == 2:
        assert any(j["path"].endswith("deact-1-evidence/journal") for j in record_doc(layout, 2)["journals"])
    assert fire(layout, fx.a2_sha256, Units()).terminal is BsTerminal.DISARMED


# ---------------------------------------------------------------------------
# concurrency, attempt and publication races (RT4.BS.1, RT4.CL0)
# ---------------------------------------------------------------------------


def test_a_firing_while_another_holds_the_backstop_lock_does_not_enter_cl(layout, fx):
    fx.activate()
    guard = LocalBackstopGuard(layout.store, ACT_ID, layout.owner)
    assert guard.acquire() is GuardMode.HELD
    try:
        units = Units()
        out = fire(layout, fx.a2_sha256, units)
    finally:
        guard.release()
    assert out.terminal is BsTerminal.CONCURRENT_BACKSTOP and out.exit_code == 14
    assert units.disarms == [] and attempt_dirs(layout) == [] and os.path.exists(fx.paths.rule)


def test_losing_the_attempt_race_re_observes_and_takes_only_a_valid_branch(layout, fx, monkeypatch):
    """A stop-post takes attempt k between the bound decision and CL-0: CL owns
    nothing (concurrent-deact). The firing re-observes: the winner's record is the
    latest valid st1-verified one, so this firing disarms (one DI-4)."""
    fx.activate()
    original = backstop_root.build_procedure

    def racing(*a, **kw):
        assert stop_post(layout, fx).terminal is Terminal.ST1_VERIFIED  # the winner: deact-1
        return original(*a, **kw)

    monkeypatch.setattr(backstop_root, "build_procedure", racing)
    units = Units()
    out = fire(layout, fx.a2_sha256, units)
    assert out.cleanup.terminal is Terminal.CONCURRENT_DEACT
    assert out.terminal is BsTerminal.DISARMED and units.disarms == [ACT_ID]
    assert out.lines == [f"rp11-bs disarmed {ACT_ID} branch=bs-2 k=1 disarm=stopped", out.cleanup.diagnostic(ACT_ID)]
    assert out.lines[1].startswith(f"rp11-cl concurrent-deact {ACT_ID} k=absent ")
    assert attempt_dirs(layout) == [f"{ACT_ID}-deact-1-evidence"] and records(layout) == [f"{ACT_ID}.act.json", f"{ACT_ID}.deact-1.json"]


def test_losing_the_race_without_a_valid_branch_exits_concurrent(layout, fx, monkeypatch):
    fx.activate()
    original = backstop_root.build_procedure

    def racing(*a, **kw):
        Path(layout.var_tmp, f"{ACT_ID}-deact-1-evidence").mkdir()  # taken, no record yet
        return original(*a, **kw)

    monkeypatch.setattr(backstop_root, "build_procedure", racing)
    units = Units()
    out = fire(layout, fx.a2_sha256, units)
    assert out.terminal is BsTerminal.CLEANUP and out.exit_code == 5
    assert units.disarms == [] and records(layout) == []


def test_a_publication_collision_never_promotes_an_older_record(layout, fx, monkeypatch):
    """Record name already taken by a foreign object: record-unpublished; the
    re-observation finds no valid latest record and does not disarm."""
    fx.activate()
    Path(layout.store, "activation").mkdir(exist_ok=True)
    put_record(layout, f"{ACT_ID}.deact-1.json", b"squatted\n")
    os.chmod(Path(layout.store, "activation", f"{ACT_ID}.deact-1.json"), 0o644)
    units = Units()
    out = fire(layout, fx.a2_sha256, units)
    assert out.cleanup.terminal is Terminal.RECORD_UNPUBLISHED and out.exit_code == 3
    assert units.disarms == []


def test_simultaneous_firings_never_exceed_b_or_touch_another_activation(layout):
    fx = make_fx(layout, backstop_max=2)
    other = make_fx(layout, activation_id=OTHER_ID)
    fx.activate()
    make_attempt(layout, 1)  # B-1 already used
    make_attempt(layout, 1, activation_id=OTHER_ID)
    other_before = {p: p.stat().st_mtime_ns for p in Path(layout.var_tmp).glob(f"{OTHER_ID}-*")}
    barrier = threading.Barrier(6)
    results, all_units = [], []

    def one():
        units = Units()
        all_units.append(units)
        barrier.wait()
        results.append(fire(layout, fx.a2_sha256, units))

    threads = [threading.Thread(target=one) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(60)
    assert len(results) == 6
    entered = [r for r in results if r.cleanup is not None and r.cleanup.k is not None]
    assert len(entered) == 1 and entered[0].cleanup.k == 2  # exactly the B-th, once
    assert len([d for d in attempt_dirs(layout) if exact_attempts((d,), ACT_ID)]) <= 2  # never above B
    assert {r.terminal for r in results} <= {
        BsTerminal.CLEANUP, BsTerminal.CONCURRENT_BACKSTOP, BsTerminal.BOUND_REACHED, BsTerminal.DISARMED
    }
    for units in all_units:
        assert set(units.reads) <= {HOLDER, CAPTURE_UNIT} and set(units.disarms) <= {ACT_ID}
    assert {p: p.stat().st_mtime_ns for p in Path(layout.var_tmp).glob(f"{OTHER_ID}-*")} == other_before
    assert not Path(layout.store, "backstop", f"{OTHER_ID}.journal").exists()
    assert os.path.exists(other.paths.a2_file(other.a2_sha256))


def test_the_backstop_lock_serializes_two_processes(layout, fx):
    """``flock`` is per open file description: a second open in another process is busy."""
    fx.activate()
    guard = LocalBackstopGuard(layout.store, ACT_ID, layout.owner)
    assert guard.acquire() is GuardMode.HELD
    pid = os.fork()
    if pid == 0:  # pragma: no cover - child
        other = LocalBackstopGuard(layout.store, ACT_ID, layout.owner)
        os._exit(0 if other.acquire() is GuardMode.BUSY else 1)
    _, status = os.waitpid(pid, 0)
    guard.release()
    assert os.waitstatus_to_exitcode(status) == 0
    assert LocalBackstopGuard(layout.store, ACT_ID, layout.owner).acquire() is GuardMode.HELD


# ---------------------------------------------------------------------------
# pure helpers, output, composition root
# ---------------------------------------------------------------------------


def test_exact_attempt_names():
    names = (f"{ACT_ID}-deact-1-evidence", f"{ACT_ID}-deact-09-evidence", f"{ACT_ID}-deact-100-evidence",
             f"{ACT_ID}-deact-0-evidence", f"{ACT_ID}-deact-12-evidence.x", f"{OTHER_ID}-deact-3-evidence",
             f"{ACT_ID}-deact-99-evidence")
    assert exact_attempts(names, ACT_ID) == (1, 99)


def test_is_backstop_attempt_reads_only_a_well_formed_first_line(layout):
    d = make_attempt(layout, 1, trigger="stop-post")
    data = (d / "journal").read_bytes()
    assert is_backstop_attempt(data, activation_id=ACT_ID, k=1) is False
    assert is_backstop_attempt(data, activation_id=ACT_ID, k=2) is True
    assert is_backstop_attempt(data + b'{"torn', activation_id=ACT_ID, k=1) is False  # later lines irrelevant
    assert is_backstop_attempt(None, activation_id=ACT_ID, k=1) is True


def test_every_line_is_fixed_bounded_and_value_free(layout, fx):
    fx.activate()
    seen = []
    for units in (Units(holder="active"), Units(holder=ControlError("timeout", "secret /etc/shadow"))):
        seen += bare(layout, units).run().lines
    seen += fire(layout, fx.a2_sha256, Units()).lines
    seen += fire(layout, fx.a2_sha256, Units(disarm=ControlError("timeout", "detail /run/x", effect_not_confirmed=True))).lines
    for line in seen:
        assert re.fullmatch(r"rp11-(bs|cl) [A-Za-z0-9 =,._-]+", line), line
        assert len(line) < 400 and "/" not in line and "secret" not in line and "detail" not in line


def test_an_unexpected_exception_exits_70_without_a_traceback(monkeypatch, capsys, layout):
    def boom(*a, **k):
        raise ValueError("secret-content /etc/shadow")

    monkeypatch.setattr(backstop_root, "build_backstop", boom)
    assert run_backstop(ACT_ID, "a" * 64, invocation_id="absent", parent_pid=1, layout=layout, connector=lambda: None) == 70
    assert capsys.readouterr().err == f"rp11-bs internal-error {ACT_ID} ValueError\n"


def test_the_composition_root_prints_the_lines_and_returns_the_exit(monkeypatch, capsys, layout, fx):
    fx.activate()
    units = Units(holder="failed")
    monkeypatch.setattr(stop_post_root.StopPostServices, "units", lambda self, params: units)
    monkeypatch.setattr(stop_post_root.StopPostServices, "pk", lambda self, params: FakePk(units.events))
    monkeypatch.setattr(stop_post_root.StopPostServices, "baseline", lambda self, params: FakeBaseline(units.events, _baseline()))
    code = run_backstop(ACT_ID, fx.a2_sha256, invocation_id=INV, parent_pid=7, layout=layout, connector=lambda: None)
    err = capsys.readouterr().err.splitlines()
    assert code == 0 and len(err) == 2
    assert err[0].startswith(f"rp11-bs cleanup {ACT_ID} k=1 trigger=backstop")
    assert err[1].startswith(f"rp11-cl st1-verified {ACT_ID} k=1 ")


def test_disarm_is_issued_at_most_once_per_firing(layout):
    proc = bare(layout, Units())
    proc._disarm()
    with pytest.raises(AssertionError):
        proc._disarm()


def test_bs_never_names_the_holder_or_capture_unit_in_a_mutation():
    import ast

    source = (Path(__file__).resolve().parent.parent / "application/rp11/backstop.py").read_text()
    calls = {n.func.attr for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert not calls & {"create_holder", "create_backstop", "stop_capture_unit", "kill", "killpg"}
    assert "disarm_backstop" in calls
