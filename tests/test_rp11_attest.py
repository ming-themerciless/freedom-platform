"""RT-5 ``deact … attest``: RT5.PRE and the shared cleanup under trigger ``attest``.

The cleanup engine, its filesystem adapters and the A-2/H-1 chain are the real ones on
temporary trees (fixtures shared with ``test_rp11_cleanup``); systemd, Polkit and the
baseline are injected fakes, real on the disposable host
(``tests/systemd_integration/test_route3_attest_host.py``). The first-image vector and
environment rows (RT5.FI) are in ``test_rp11_h1_artifact.py``.

Row coverage is named in each test's docstring: RT5.PRE (the precondition), RT5.CL
(the reused engine), RT5.ID (identity and journal grammar), RT5.OUT (exits and lines).
"""

from __future__ import annotations

import hashlib
import itertools
import json
import os
import re
import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_rp11_cleanup import (  # noqa: E402,F401  (fixtures are used by name)
    ACT_ID,
    BOOT,
    OTHER_BOOT,
    Crash,
    Events,
    FailingIO,
    FakeBaseline,
    FakeClock,
    FakePk,
    FakeServices,
    FakeUnits,
    _umask,
    attempt_journal,
    fx,
    layout,
    ops,
    paths,
    procedure,
    record,
)

import adapters.rp11.attest as attest_root  # noqa: E402
from adapters.rp11.attest import build_attest, run_attest  # noqa: E402
from adapters.rp11.fsops import LocalActivationFs  # noqa: E402
from application.rp11.attest import (  # noqa: E402
    EXIT_OWNER_ACTIVE,
    EXIT_UNESTABLISHED,
    GONE,
    OWNS,
    AttestEnd,
    AttestProcedure,
)
from application.rp11.backstop import is_backstop_attempt  # noqa: E402
from application.rp11.canonical import parse_canonical  # noqa: E402
from application.rp11.cleanup import CleanupOutcome, Invocation, Terminal, Trigger  # noqa: E402
from application.rp11.journal import GENESIS, JournalKind, JournalSchemaError, check_fields, parse_journal  # noqa: E402
from application.rp11.pk import PkOutcome  # noqa: E402
from application.rp11.records import validate_record  # noqa: E402
from application.unit_control import (  # noqa: E402
    ControlError,
    ControlOk,
    ControlRefused,
    ControlSpecError,
    RefusalReason,
    UnitProperty,
)

pytestmark = pytest.mark.skipif(os.geteuid() == 0, reason="the local tree tests run unprivileged")


@pytest.fixture(autouse=True)
def _close_the_evidence_descriptors_a_run_leaves_open(tmp_path):
    """The shared engine's evidence sink keeps its journal descriptor open until the process
    ends (a no-op for a role that exits). The focused Route 3 set already sits just under the
    default 1024-descriptor limit, so this module closes what its own runs opened under its
    own ``tmp_path`` and nothing else."""
    before = set(os.listdir("/proc/self/fd"))
    yield
    root = str(tmp_path.parent)
    for name in sorted(set(os.listdir("/proc/self/fd")) - before, key=int):
        try:
            if os.readlink(f"/proc/self/fd/{name}").startswith(root):
                os.close(int(name))
        except OSError:
            pass

A2 = "a" * 64
NAMES = {
    "holder": f"{ACT_ID}.service",
    "timer": f"{ACT_ID}-backstop.timer",
    "service": f"{ACT_ID}-backstop.service",
}
ROLES = tuple(NAMES)
ACTIVE = ControlOk({UnitProperty.ACTIVE_STATE: "inactive"})


def state(value) -> ControlOk:
    return ControlOk({UnitProperty.ACTIVE_STATE: value})


NOT_LOADED = ControlRefused(RefusalReason.NOT_LOADED)
BLOCKING = sorted(OWNS)
PERMITTED = {"inactive": state("inactive"), "failed": state("failed"), "not-found": NOT_LOADED}


class PreUnits:
    """The three RT5.PRE reads by unit name; every other read is the capture unit's (CL-2)."""

    def __init__(self, events: Events, answers: dict | None = None, inner=None):
        self.events = events
        self.answers = {role: state("inactive") for role in ROLES} | (answers or {})
        self.inner = inner or FakeUnits(events)
        self.reads: list[tuple[str, tuple]] = []

    def read_unit(self, unit, props):
        for role, name in NAMES.items():
            if unit == name:
                self.events.mark(f"pre:{role}")
                self.reads.append((unit, tuple(props)))
                answer = self.answers[role]
                if isinstance(answer, BaseException):
                    raise answer
                return answer
        return self.inner.read_unit(unit, props)


class Cleanups:
    """Records each cleanup the procedure starts; never touches a tree."""

    def __init__(self):
        self.calls: list[str] = []

    def __call__(self, holder_state: str) -> CleanupOutcome:
        self.calls.append(holder_state)
        return CleanupOutcome(Terminal.ST1_VERIFIED, 1, "removed-earlier", "removed", ["removed"], "not-authorized", "absent")


def pre(answers: dict | None = None, activation_id: str = ACT_ID):
    events = Events()
    units = PreUnits(events, answers)
    cleanups = Cleanups()
    return AttestProcedure(activation_id, units, cleanups), units, cleanups, events


# ---------------------------------------------------------------------------
# RT5.PRE — the precondition
# ---------------------------------------------------------------------------


def test_the_three_reads_are_exactly_the_derived_names_active_state_only_and_in_order():
    """RT5.PRE.1: three ``ActiveState`` reads, holder, timer, service; no other property."""
    procedure_, units, cleanups, _ = pre()
    outcome = procedure_.run()
    assert outcome.end is AttestEnd.CLEANUP and outcome.exit_code == 0
    assert units.reads == [(NAMES[r], (UnitProperty.ACTIVE_STATE,)) for r in ROLES]
    assert cleanups.calls == ["inactive"]


@pytest.mark.parametrize("states", list(itertools.product(PERMITTED, repeat=3)))
def test_inactive_failed_and_not_found_never_block_in_any_combination(states):
    """RT5.PRE.3: every permitted state on every unit, independently."""
    procedure_, units, cleanups, _ = pre(dict(zip(ROLES, (PERMITTED[s] for s in states))))
    assert procedure_.run().end is AttestEnd.CLEANUP
    assert len(units.reads) == 3 and cleanups.calls == [states[0]]  # the holder's own answer


@pytest.mark.parametrize("blocking", BLOCKING)
@pytest.mark.parametrize("role", ROLES)
def test_a_live_owner_in_any_unit_refuses_before_cleanup(role, blocking):
    """RT5.PRE.2: ``activating``/``active``/``deactivating``/``reloading`` on any one unit;
    the others permitting. The reads stop at the first unit that decides."""
    procedure_, units, cleanups, events = pre({role: state(blocking)})
    outcome = procedure_.run()
    assert outcome.end is AttestEnd.OWNER_ACTIVE and outcome.exit_code == EXIT_OWNER_ACTIVE == 30
    assert outcome.line == f"rp11-attest owner-active {ACT_ID} unit={role} state={blocking}"
    assert [u for u, _ in units.reads] == [NAMES[r] for r in ROLES[: ROLES.index(role) + 1]]
    assert cleanups.calls == [] and outcome.cleanup is None


def test_an_owner_is_found_whatever_the_other_units_say():
    """A satisfied read is never evidence about another unit."""
    answers = {"holder": NOT_LOADED, "timer": state("failed"), "service": state("active")}
    procedure_, units, cleanups, _ = pre(answers)
    assert procedure_.run().end is AttestEnd.OWNER_ACTIVE and len(units.reads) == 3 and not cleanups.calls


class _Str(str):
    pass


UNESTABLISHED = {
    "timeout": (ControlError("timeout"), "error"),
    "disconnected": (ControlError("disconnected"), "error"),
    "invalid-reply": (ControlError("invalid-reply", "unexpected reply for ActiveState"), "error"),
    "unknown-error": (ControlError("org.freedesktop.DBus.Error.UnknownObject", "x"), "error"),
    "refused-exists": (ControlRefused(RefusalReason.EXISTS), "refused"),
    "refused-not-authorized": (ControlRefused(RefusalReason.NOT_AUTHORIZED), "refused"),
    "refused-invalid": (ControlRefused(RefusalReason.INVALID_REQUEST), "refused"),
    "not-a-result": (object(), "error"),
    "none": (None, "error"),
    "value-not-a-mapping": (ControlOk("active"), "malformed"),
    "empty-mapping": (ControlOk({}), "malformed"),
    "other-property": (ControlOk({UnitProperty.LOAD_STATE: "loaded"}), "malformed"),
    "state-none": (state(None), "malformed"),
    "state-int": (state(1), "malformed"),
    "state-bytes": (state(b"inactive"), "malformed"),
    "state-bool": (state(True), "malformed"),
    "state-str-subclass": (state(_Str("inactive")), "malformed"),
    "maintenance": (state("maintenance"), "unsupported"),
    "refreshing": (state("refreshing"), "unsupported"),
    "empty-state": (state(""), "unsupported"),
    "upper-case": (state("INACTIVE"), "unsupported"),
    "padded": (state("inactive "), "unsupported"),
    "newline": (state("inactive\n"), "unsupported"),
    "unknown-state": (state("exploding"), "unsupported"),
}


@pytest.mark.parametrize("case", sorted(UNESTABLISHED))
@pytest.mark.parametrize("role", ROLES)
def test_an_unestablished_precondition_fails_closed_before_cleanup(role, case):
    """RT5.PRE.4: a transport failure, malformed reply, unexpected refusal or an unlisted
    state on any unit refuses; the line names the unit and a closed token, never a value."""
    answer, token = UNESTABLISHED[case]
    procedure_, units, cleanups, _ = pre({role: answer})
    outcome = procedure_.run()
    assert outcome.end is AttestEnd.UNESTABLISHED and outcome.exit_code == EXIT_UNESTABLISHED == 31
    assert outcome.line == f"rp11-attest precondition-unestablished {ACT_ID} unit={role} read={token}"
    assert [u for u, _ in units.reads] == [NAMES[r] for r in ROLES[: ROLES.index(role) + 1]]
    assert cleanups.calls == []


@pytest.mark.parametrize("role", ROLES)
def test_an_exception_from_a_read_propagates_and_cleanup_never_starts(role):
    procedure_, _, cleanups, _ = pre({role: RuntimeError("secret /etc/shadow")})
    with pytest.raises(RuntimeError):
        procedure_.run()
    assert cleanups.calls == []


def test_the_exit_codes_are_distinct_from_every_cleanup_terminal_and_other_role():
    cleanup_codes = {t.exit_code for t in Terminal}
    assert cleanup_codes == {0, 1, 2, 3, 4, 5}
    assert {EXIT_OWNER_ACTIVE, EXIT_UNESTABLISHED}.isdisjoint(cleanup_codes | {64, 69, 70, 71, 77, 10, 11, 12, 13, 14, 15, 20, 21, 22})


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "rp11-capture-pass-a.service",
        f"{ACT_ID}.service",
        f"{ACT_ID}-backstop.timer",
        f"{ACT_ID};x",
        f"{ACT_ID}\n",
        f"{ACT_ID} ",
        f"../{ACT_ID}",
        f"{ACT_ID}/../x",
        ACT_ID.upper(),
        ACT_ID[:-1],
        ACT_ID + "0",
        None,
        7,
    ],
)
def test_no_unit_name_comes_from_the_caller(bad):
    """RT5.PRE.5: only a valid activation id derives names; nothing else is read."""
    events = Events()
    units = PreUnits(events)
    with pytest.raises(ControlSpecError):
        AttestProcedure(bad, units, Cleanups())
    assert units.reads == []


def test_another_activations_units_are_never_read():
    other = "rp11-act-20261014T101500Z-ffffffff"
    events = Events()
    units = PreUnits(events)
    seen: list[str] = []
    units.inner = type("Inner", (), {"read_unit": lambda self, unit, props: seen.append(unit) or state("inactive")})()
    # The fixture answers only ACT_ID's names; a procedure for ``other`` reads only ``other``'s.
    AttestProcedure(other, units, Cleanups()).run()
    assert seen == [f"{other}.service", f"{other}-backstop.timer", f"{other}-backstop.service"]
    assert all(other in name for name in seen)
    assert not any(ACT_ID in name for name in seen)


def test_a_blocked_or_unestablished_precondition_makes_no_start_stop_or_reset_request():
    class Strict:
        def __init__(self):
            self.reads = 0

        def read_unit(self, unit, props):
            self.reads += 1
            return state("active")

        def __getattr__(self, name):  # any mutating DI is a failure
            raise AssertionError(f"unexpected unit-control call {name}")

    strict = Strict()
    assert AttestProcedure(ACT_ID, strict, Cleanups()).run().end is AttestEnd.OWNER_ACTIVE
    assert strict.reads == 1


def test_the_admitted_state_sets_are_closed_and_disjoint():
    """Reversible choice (documented in the module): the sets are pinned, not coerced."""
    assert OWNS == {"activating", "active", "deactivating", "reloading"}
    assert GONE == {"inactive", "failed"}
    assert OWNS.isdisjoint(GONE)


# ---------------------------------------------------------------------------
# a refusal changes nothing (real trees)
# ---------------------------------------------------------------------------


class ReadCounter:
    def __init__(self, monkeypatch):
        self.reads: list[str] = []
        real = LocalActivationFs.read_root_file

        def counted(fs, path, **kw):
            self.reads.append(os.path.basename(path))
            return real(fs, path, **kw)

        monkeypatch.setattr(LocalActivationFs, "read_root_file", counted)


def tree_snapshot(layout) -> dict[str, tuple]:
    found = {}
    for root in (layout.run, layout.var_tmp, layout.store):
        for dirpath, dirnames, filenames in os.walk(root):
            for name in dirnames + filenames:
                p = os.path.join(dirpath, name)
                info = os.lstat(p)
                found[p] = (info.st_mode, info.st_ino, info.st_size, info.st_mtime_ns)
    return found


@pytest.mark.parametrize(
    "answers,exit_code",
    [
        ({"holder": state("active")}, 30),
        ({"timer": state("activating")}, 30),
        ({"service": state("deactivating")}, 30),
        ({"service": state("reloading")}, 30),
        ({"holder": ControlError("timeout")}, 31),
        ({"timer": state("maintenance")}, 31),
        ({"service": ControlOk({})}, 31),
    ],
)
def test_a_refusal_creates_reads_removes_and_asks_nothing(fx, layout, monkeypatch, answers, exit_code, capsys):
    """RT5.PRE.2/.4/.6: no attempt directory, journal or record; the grant stays; no authority
    or evidence file is read; no lock; no Polkit call; no capture-unit read."""
    fx.activate()
    before = tree_snapshot(layout)
    counter = ReadCounter(monkeypatch)
    events = Events()
    pk = FakePk(events)
    units = PreUnits(events, answers)
    services = FakeServices(events, units=units, pk=pk)
    result = build_attest(ACT_ID, fx.a2_sha256, layout=layout, services=services, clock=FakeClock()).run()
    assert result.exit_code == exit_code and result.cleanup is None
    assert tree_snapshot(layout) == before
    assert os.path.lexists(paths(layout).rule)  # CL-G never ran
    assert counter.reads == [] and pk.calls == 0
    assert "lock" not in events and "di1" not in events and "pk" not in events
    assert not list(Path(layout.var_tmp).glob(f"{ACT_ID}-deact-*"))
    assert not list(Path(layout.store, "activation").glob("*.deact-*"))


def test_the_composition_root_prints_one_bounded_line_and_returns_the_refusal(fx, layout, capsys):
    fx.activate()
    events = Events()
    services = FakeServices(events, units=PreUnits(events, {"timer": state("active")}))
    code = _run_root(layout, fx, services)
    assert code == 30
    assert capsys.readouterr().err == f"rp11-attest owner-active {ACT_ID} unit=timer state=active\n"


def _run_root(layout, fx, services, **kw):
    original = attest_root.StopPostServices
    try:
        attest_root.StopPostServices = lambda connector, clock: services
        return run_attest(ACT_ID, fx.a2_sha256, layout=layout, connector=lambda: None, **kw)
    finally:
        attest_root.StopPostServices = original


# ---------------------------------------------------------------------------
# RT5.CL — the reused engine with trigger ``attest``
# ---------------------------------------------------------------------------


def attest_cl(layout, fx, *, answers=None, services=None, **kw):
    """RT5.PRE in front of the recording cleanup of ``test_rp11_cleanup`` with trigger ``attest``."""
    events = kw.pop("events", None) or Events()
    pre_units = PreUnits(events, answers, inner=getattr(services, "_units", None))
    services = services or FakeServices(events)
    services._units = pre_units
    holder = {}

    def cleanup(holder_state):
        holder["state"] = holder_state
        proc, _ = procedure(
            layout, fx, events=events, services=services, trigger=Trigger.ATTEST, holder_state=holder_state, **kw
        )
        return proc.run()

    outcome = AttestProcedure(ACT_ID, pre_units, cleanup).run()
    return outcome, events, holder


def test_same_boot_cleanup_reaches_st1_verified_with_the_attest_trigger(fx, layout):
    """RT5.CL.1/.2: CL-G first, ordinary CL-0 … CL-7, exit 0; the published evidence names
    ``attest`` and carries no provenance."""
    fx.activate()
    outcome, events, holder = attest_cl(layout, fx)
    assert outcome.end is AttestEnd.CLEANUP and outcome.exit_code == 0
    assert outcome.cleanup.terminal is Terminal.ST1_VERIFIED and holder["state"] == "inactive"
    assert re.fullmatch(rf"rp11-cl st1-verified {ACT_ID} k=1 rule=\S+ pk=not-authorized .*", outcome.line)
    p = paths(layout)
    for path in (p.rule, p.pass_config, p.tree_p, p.grant_id, p.lock_dir):
        assert not os.path.lexists(path)
    doc = record(layout, 1)
    assert doc["trigger"] == "attest" and doc["helper"]["role"] == "attest" and doc["outcome"] == "st1-verified"
    assert doc["holder"]["invocation_id"] == "absent" and doc["holder"]["active_state_at_start"] == "inactive"
    assert doc["pk"]["mode"] == "seek-not-authorized" and doc["pk"]["outcome"] == "not-authorized"
    assert doc["grant_check"]["after_cleanup"] == "not-authorized"
    assert ops(layout, 1)[:2] == ["run-start", "cl-g"] and ops(layout, 1)[-1] == "run-end"
    # CL-G is the first cleanup act and Polkit is asked once.
    assert events.index("pre:service") < events.index("lock") and events.count("pk") == 1


def test_the_attest_journal_carries_no_provenance_and_parses_under_the_refined_grammar(fx, layout):
    """RT5.ID.1: ``run-start`` has no ``provenance`` key at all (not dummy ``0``/``absent``)."""
    fx.activate()
    attest_cl(layout, fx)
    first = attempt_journal(layout, 1)[0]
    assert first["trigger"] == "attest" and first["helper"]["role"] == "attest"
    assert "provenance" not in first and first["holder_state"] == "inactive"
    data = Path(layout.var_tmp, f"{ACT_ID}-deact-1-evidence/journal").read_bytes()
    assert b"parent_pid" not in data and b"provenance" not in data
    parsed = parse_journal(data, kind=JournalKind.ATTEMPT, run=f"{ACT_ID}-deact-1")
    assert parsed.valid


def _run_start(trigger: str, role: str, *, with_provenance: bool, **over) -> dict:  # noqa: D401
    fields = {
        "trigger": trigger,
        "boot_id": BOOT,
        "holder_state": "inactive",
        "lock": {"object": "absent", "mode": "absent", "wait_ms": 0},
        "helper": {"role": role, "tool_sha256": "absent"},
    }
    if with_provenance:
        fields["provenance"] = {"parent_pid": 1, "invocation_id": "absent"}
    return fields | over


@pytest.mark.parametrize(
    "fields,valid",
    [
        (_run_start("attest", "attest", with_provenance=False), True),
        (_run_start("stop-post", "stop-post", with_provenance=True), True),
        (_run_start("backstop", "backstop", with_provenance=True), True),
        # old shape: attest with the dummy provenance the unit-started shapes carry
        (_run_start("attest", "attest", with_provenance=True), False),
        (_run_start("attest", "attest", with_provenance=True, provenance_extra=1), False),
        # the unit-started shapes without provenance
        (_run_start("stop-post", "stop-post", with_provenance=False), False),
        (_run_start("backstop", "backstop", with_provenance=False), False),
        # hybrids: trigger and helper role disagree about attest
        (_run_start("attest", "stop-post", with_provenance=False), False),
        (_run_start("stop-post", "attest", with_provenance=True), False),
        (_run_start("backstop", "attest", with_provenance=False), False),
        (_run_start("attest", "backstop", with_provenance=True), False),
        # a partial or malformed provenance object under the other triggers
        (_run_start("stop-post", "stop-post", with_provenance=True, provenance={"parent_pid": 1}), False),
        (_run_start("attest", "attest", with_provenance=False, holder_state="Inactive"), False),
    ],
)
def test_the_attempt_run_start_grammar_is_closed_per_trigger(fields, valid):
    """RT5.ID.1: exactly the accepted shapes; old or hybrid ``attest`` shapes are invalid."""
    if valid:
        check_fields(JournalKind.ATTEMPT, "run-start", fields)
    else:
        with pytest.raises(JournalSchemaError):
            check_fields(JournalKind.ATTEMPT, "run-start", fields)


def test_provenance_belongs_to_the_unit_started_triggers_only():
    for trigger in (Trigger.STOP_POST, Trigger.BACKSTOP):
        with pytest.raises(ValueError):
            Invocation(ACT_ID, A2, trigger, None, None)
        with pytest.raises(ValueError):
            Invocation(ACT_ID, A2, trigger, 1, None)
        Invocation(ACT_ID, A2, trigger, 1, "absent")
    with pytest.raises(ValueError):
        Invocation(ACT_ID, A2, Trigger.ATTEST, 1, "absent")
    with pytest.raises(ValueError):
        Invocation(ACT_ID, A2, Trigger.ATTEST, 1, None)
    assert Invocation(ACT_ID, A2, Trigger.ATTEST, None, None).holder_invocation_id == "absent"


def test_a_hard_stop_damaged_object_is_kept_and_reported(fx, layout):
    """RT5.CL.3: a damaged A1 rule is never removed and never becomes success."""
    fx.activate(grant_id=False)
    Path(paths(layout).rule).write_bytes(b"tampered\n")
    outcome, *_ = attest_cl(layout, fx)
    assert outcome.exit_code == 1 and outcome.cleanup.terminal is Terminal.HARD_STOP
    assert os.path.exists(paths(layout).rule) and outcome.cleanup.rule_class == "present-damaged-unremoved"
    assert record(layout, 1)["trigger"] == "attest" and record(layout, 1)["st1"]["verified"] is False


def test_a_foreign_object_is_kept_and_reported(fx, layout):
    fx.activate()
    pass_config = Path(paths(layout).pass_config)
    replacement = pass_config.with_name("replacement")
    replacement.write_bytes(b"{}\n")
    os.chmod(replacement, 0o644)
    os.replace(replacement, pass_config)  # a different inode: foreign, not merely damaged
    outcome, *_ = attest_cl(layout, fx)
    assert outcome.exit_code == 1 and outcome.cleanup.pass_class == "present-foreign-unremoved"
    assert pass_config.read_bytes() == b"{}\n"


def test_a_concurrent_attempt_owning_k_is_exit_5_and_acts_on_nothing_further(fx, layout, monkeypatch):
    fx.activate()
    original = LocalActivationFs.list_prefixed
    monkeypatch.setattr(LocalActivationFs, "list_prefixed", lambda self, d, p: ())
    Path(layout.var_tmp, f"{ACT_ID}-deact-1-evidence").mkdir()
    outcome, events, _ = attest_cl(layout, fx)
    monkeypatch.setattr(LocalActivationFs, "list_prefixed", original)
    assert outcome.exit_code == 5 and outcome.cleanup.terminal is Terminal.CONCURRENT_DEACT
    assert events.count("pk") == 0 and os.path.exists(paths(layout).pass_config)
    assert not list(Path(layout.store, "activation").glob("*.deact-*"))


def test_an_unremovable_grant_is_grant_unremovable_and_exit_1(fx, layout):
    fx.activate(grant_id=False)
    os.chmod(os.path.dirname(paths(layout).rule), 0o555)
    try:
        outcome, *_ = attest_cl(layout, fx)
    finally:
        os.chmod(os.path.dirname(paths(layout).rule), 0o755)
    assert outcome.exit_code == 1 and outcome.cleanup.rule_class in {"grant-unremovable", "present-uninspected-unremoved"}
    assert os.path.exists(paths(layout).rule)


@pytest.mark.parametrize("state_value", ["active", "activating", "deactivating", "reloading"])
def test_an_active_capture_unit_is_unit_still_active_exit_2(fx, layout, state_value):
    fx.activate()
    events = Events()
    services = FakeServices(events, units=FakeUnits(events, (state_value,)))
    outcome, *_ = attest_cl(layout, fx, services=services, events=events)
    assert outcome.exit_code == 2 and outcome.cleanup.terminal is Terminal.UNIT_STILL_ACTIVE


def test_a_manager_error_in_the_capture_read_never_verifies(fx, layout):
    fx.activate()
    events = Events()
    units = FakeUnits(events, error=True)
    outcome, *_ = attest_cl(layout, fx, services=FakeServices(events, units=units), events=events)
    assert outcome.exit_code == 1 and outcome.cleanup.failure == "observation-failed"


def test_an_attempt_directory_failure_enters_grant_priority_mode_and_exits_4(fx, layout):
    """GP-R3: the attempt names are exhausted; the attributable grant is removed, nothing is claimed."""
    fx.activate()
    for k in range(1, 100):
        Path(layout.var_tmp, f"{ACT_ID}-deact-{k}-evidence").mkdir()
    outcome, *_ = attest_cl(layout, fx)
    assert outcome.exit_code == 4 and outcome.cleanup.terminal is Terminal.EVIDENCE_UNWRITABLE
    assert outcome.line.startswith(f"rp11-cl grant-priority {ACT_ID} ")
    assert not os.path.lexists(paths(layout).rule)
    assert not list(Path(layout.store, "activation").glob("*.deact-*"))


@pytest.mark.parametrize(
    "io",
    [
        lambda: FailingIO(fail_write_at=1),
        lambda: FailingIO(fail_fsync_at=4),
        lambda: FailingIO(fail_write_at=4),
        lambda: FailingIO(fail_fsync_at=9),
    ],
)
def test_a_journal_write_or_flush_failure_is_grant_priority_and_never_success(fx, layout, io):
    fx.activate(grant_id=False)
    outcome, *_ = attest_cl(layout, fx, io=io())
    assert outcome.exit_code == 4 and not os.path.lexists(paths(layout).rule)
    assert not list(Path(layout.store, "activation").glob("*.deact-*"))
    again, *_ = attest_cl(layout, fx)  # explicit later recovery
    assert again.exit_code == 0 and record(layout, 2)["trigger"] == "attest"


def test_a_record_collision_is_exit_3_and_the_record_is_never_replaced(fx, layout):
    fx.activate()
    Path(layout.store, "activation").mkdir(exist_ok=True)
    squat = Path(layout.store, f"activation/{ACT_ID}.deact-1.json")
    squat.write_text("{}\n")
    os.chmod(squat, 0o444)
    outcome, *_ = attest_cl(layout, fx)
    assert outcome.exit_code == 3 and squat.read_text() == "{}\n"
    assert attest_cl(layout, fx)[0].exit_code == 0


def test_a_failed_record_flush_is_exit_3(fx, layout):
    fx.activate()
    outcome, *_ = attest_cl(layout, fx, record_io=FailingIO(fail_fsync_at=1))
    assert outcome.exit_code == 3 and not Path(layout.store, f"activation/{ACT_ID}.deact-1.json").exists()


# --- CL-4: negative authorization -------------------------------------------


class RealPk:
    """The real PK/2 series (``application.rp11.pk``) over scripted DI-5/DI-6 answers, counted."""

    def __init__(self, answers, *, subjects=None, launcher_kw=None, ops=None):
        import test_rp11_pk_sn as pks

        self.series_runs = 0
        self.ops = ops or pks.Ops(reap_after=0)
        self.launcher = pks.Launcher(self.ops, **(launcher_kw or {}))
        self.authority = pks.Authority(answers)
        from application.unit_control import ProcessSubject

        self.subjects = subjects or pks.Subjects(lambda pid: ControlOk(ProcessSubject(pid, 77, os.getuid())))

    def run(self, operator, verb, mode):
        from application.rp11.authority import Params
        from application.rp11.pk import PkSeries
        from application.rp11.sn import SignalContract

        self.series_runs += 1
        return PkSeries(
            launcher=self.launcher,
            subjects=self.subjects,
            authority=self.authority,
            contract=SignalContract(self.ops, grace_ms=2_000, slice_ms=100),
            clock=self.ops,
            params=Params(pk_op_ms=5_000, pk_call_ms=1_000),
        ).run(operator, verb, mode)


def _polkit(name):
    from application.unit_control import PolkitAuthorized, PolkitNotAuthorized

    return {
        "authorized": [PolkitAuthorized()],
        "denied": [PolkitNotAuthorized()],
        "challenge": [PolkitNotAuthorized(challenge=True)],
        "timeout": [ControlError("timeout")],
        "malformed-reply": [ControlError("invalid-reply")],
        "transport-error": [ControlError("disconnected")],
        "polkit-error": [ControlError("org.freedesktop.PolicyKit1.Error.Failed")],
    }[name]


def _subject_error(pid):
    return ControlError("proc-replaced")


def _subject_replaced(pid):
    from application.unit_control import ProcessSubject

    return ControlOk(ProcessSubject(pid, 78, os.getuid()))  # another start time than the child's


@pytest.mark.parametrize(
    "series_kw,reason",
    [
        ({"answers": _polkit("authorized")}, "still-authorized"),
        ({"answers": _polkit("timeout")}, "only-errors"),
        ({"answers": _polkit("malformed-reply")}, "only-errors"),
        ({"answers": _polkit("transport-error")}, "only-errors"),
        ({"answers": _polkit("polkit-error")}, "only-errors"),
        ({"answers": _polkit("denied"), "subjects": "error"}, "only-errors"),  # subject error
        ({"answers": _polkit("denied"), "subjects": "replaced"}, "only-errors"),  # replaced subject
        ({"answers": _polkit("denied"), "launcher_kw": {"fail": True}}, "only-errors"),  # no subject
        ({"answers": _polkit("denied"), "launcher_kw": {"ready": False}}, "only-errors"),  # not ready
    ],
)
def test_nothing_but_a_positive_not_authorized_verifies(fx, layout, series_kw, reason):
    """RT5.CL.4: authorized, timeout, malformed reply, transport error, subject error,
    replaced subject and no subject are never success; one series, never retried by CL, and
    every child it created is settled or recorded."""
    import test_rp11_pk_sn as pks

    fx.activate(grant_id=False)
    series_kw = dict(series_kw)
    subjects = series_kw.pop("subjects", None)
    if subjects == "error":
        series_kw["subjects"] = pks.Subjects(_subject_error)
    elif subjects == "replaced":
        series_kw["subjects"] = pks.Subjects(_subject_replaced)
    events = Events()
    pk = RealPk(**series_kw)
    outcome, *_ = attest_cl(layout, fx, services=FakeServices(events, pk=pk), events=events)
    assert outcome.exit_code == 1 and pk.series_runs == 1
    doc = record(layout, 1)
    assert doc["st1"]["verified"] is False and doc["pk"]["outcome"] == "unconfirmed"
    assert doc["pk"]["reason"] == reason and doc["st1"]["checks"]["pk-not-authorized"] is False
    assert doc["grant_check"]["after_cleanup"] == "unconfirmed"
    assert outcome.cleanup.rule_class == "removed-unconfirmed" and outcome.cleanup.failure == "grant-unconfirmed"
    from application.rp11.sn import HandleState

    assert all(h.state is HandleState.REAPED for h in pk.launcher.spawned)


@pytest.mark.parametrize("answer", ["denied", "challenge"])
def test_a_denial_or_a_challenge_is_the_positive_not_authorized(fx, layout, answer):
    fx.activate(grant_id=False)
    events = Events()
    pk = RealPk(_polkit(answer))
    outcome, *_ = attest_cl(layout, fx, services=FakeServices(events, pk=pk), events=events)
    assert outcome.exit_code == 0 and pk.series_runs == 1
    assert record(layout, 1)["pk"]["outcome"] == "not-authorized"


def test_an_interrupted_series_is_never_success(fx, layout):
    fx.activate(grant_id=False)
    events = Events()
    pk = FakePk(events, PkOutcome.UNCONFIRMED, "interrupted")
    outcome, *_ = attest_cl(layout, fx, services=FakeServices(events, pk=pk), events=events)
    assert outcome.exit_code == 1 and pk.calls == 1 and record(layout, 1)["pk"]["reason"] == "interrupted"


def test_a_baseline_mismatch_is_never_success(fx, layout):
    fx.activate()
    events = Events()
    services = FakeServices(events, baseline={"host": {"nodename": "other"}})
    outcome, *_ = attest_cl(layout, fx, services=services, events=events)
    assert outcome.exit_code == 1 and record(layout, 1)["st1"]["verified"] is False


# --- later boot ----------------------------------------------------------------


def reboot(layout, fx, *, boot=OTHER_BOOT, keep=()):
    """A kernel boot: every ``/run`` object of the activation is gone, the boot id differs."""
    p = paths(layout)
    for path in (p.rule, p.pass_config, p.grant_id):
        if path not in keep and os.path.lexists(path):
            os.unlink(path)
    for path in (p.tree_p, p.lock_dir):
        if path not in keep and os.path.isdir(path):
            os.rmdir(path) if not os.listdir(path) else None
    Path(layout.boot_id_file).write_text(boot + "\n")


def clear_run_objects(layout, fx):
    import shutil

    p = paths(layout)
    for path in (p.rule, p.pass_config, p.grant_id):
        if os.path.lexists(path):
            os.unlink(path)
    for path in (p.tree_p, p.lock_dir):
        if os.path.lexists(path):
            shutil.rmtree(path)


def test_a_later_boot_records_cleared_by_boot_and_reaches_st1_only_with_cl4_and_cl6(fx, layout):
    """RT5.CL.5: different boot ids, ``/run`` tmpfs, a valid old identity line, ENOENT."""
    fx.activate()
    clear_run_objects(layout, fx)
    Path(layout.boot_id_file).write_text(OTHER_BOOT + "\n")
    events = Events()
    pk = FakePk(events)
    outcome, *_ = attest_cl(layout, fx, services=FakeServices(events, pk=pk), events=events)
    assert outcome.exit_code == 0 and pk.calls == 1
    assert outcome.cleanup.rule_class == "cleared-by-boot" and outcome.cleanup.pass_class == "cleared-by-boot"
    doc = record(layout, 1)
    assert doc["st1"]["verified"] and doc["pk"]["outcome"] == "not-authorized"
    assert doc["boot"]["act_boot"] == BOOT and doc["boot"]["observed_at_start"] == OTHER_BOOT
    assert doc["boot"]["run_fstype"] == "tmpfs" and doc["trigger"] == "attest"
    assert all(d["class"] in {"cleared-by-boot", "pre-existing-kept"} for d in doc["directories"])
    assert doc["active_rule"]["class"] == "cleared-by-boot"


def test_cleared_by_boot_never_verifies_without_a_positive_not_authorized(fx, layout):
    fx.activate()
    clear_run_objects(layout, fx)
    Path(layout.boot_id_file).write_text(OTHER_BOOT + "\n")
    events = Events()
    pk = FakePk(events, PkOutcome.UNCONFIRMED, "only-errors")
    outcome, *_ = attest_cl(layout, fx, services=FakeServices(events, pk=pk), events=events)
    assert outcome.exit_code == 1 and outcome.cleanup.rule_class == "cleared-by-boot"
    assert record(layout, 1)["st1"]["verified"] is False


def test_the_same_boot_never_records_cleared_by_boot(fx, layout):
    fx.activate()
    clear_run_objects(layout, fx)  # gone, but the boot id is the activation's
    outcome, *_ = attest_cl(layout, fx)
    assert outcome.cleanup.rule_class != "cleared-by-boot" and outcome.cleanup.pass_class != "cleared-by-boot"
    assert "cleared-by-boot" not in json.dumps(record(layout, 1))


def _no_cleared_by_boot(layout, outcome):
    assert "cleared-by-boot" not in {outcome.cleanup.rule_class, outcome.cleanup.pass_class}
    assert "cleared-by-boot" not in json.dumps(record(layout, outcome.cleanup.k))


def _hard_stop(layout, outcome, *, failure="st1-not-verified"):
    """RT-5 fail-closed: non-zero, hard-stop, no ``st1-verified`` claim anywhere."""
    assert outcome.exit_code == 1 and outcome.cleanup.terminal is Terminal.HARD_STOP
    doc = record(layout, outcome.cleanup.k)
    assert doc["outcome"] == "hard-stop" and doc["st1"]["verified"] is False
    assert doc["failure"]["class"] == failure
    assert "st1-verified" not in json.dumps(doc["st1"]) and doc["st1"]["verified"] is False
    assert not outcome.line.startswith("rp11-cl st1-verified")


def test_a_non_tmpfs_run_is_not_cleared_by_boot(fx, layout):
    """The four conditions are all required; an ext4 ``/run`` leaves the engine's ordinary
    ``absent-before-removal`` class, never ``cleared-by-boot``."""
    fx.activate()
    clear_run_objects(layout, fx)
    Path(layout.boot_id_file).write_text(OTHER_BOOT + "\n")
    Path(layout.mountinfo).write_text(f"25 1 0:23 / {layout.run} rw - ext4 /dev/x rw\n")
    outcome, *_ = attest_cl(layout, fx)
    _no_cleared_by_boot(layout, outcome)
    assert outcome.cleanup.rule_class == "absent-before-removal"
    assert record(layout, 1)["boot"]["run_fstype"] == "ext4"
    _hard_stop(layout, outcome)


def test_a_missing_run_mount_fact_is_not_cleared_by_boot(fx, layout):
    fx.activate()
    clear_run_objects(layout, fx)
    Path(layout.boot_id_file).write_text(OTHER_BOOT + "\n")
    Path(layout.mountinfo).write_text("")
    outcome, *_ = attest_cl(layout, fx)
    _no_cleared_by_boot(layout, outcome)
    assert record(layout, 1)["boot"]["run_fstype"] == "absent"
    _hard_stop(layout, outcome)


def test_a_missing_old_identity_line_is_not_cleared_by_boot(fx, layout):
    fx.activate()
    clear_run_objects(layout, fx)
    Path(layout.boot_id_file).write_text(OTHER_BOOT + "\n")
    Path(layout.var_tmp, f"{ACT_ID}-act-evidence/journal").unlink()
    outcome, *_ = attest_cl(layout, fx)
    _no_cleared_by_boot(layout, outcome)
    assert outcome.cleanup.rule_class == "never-linked"  # no identity line: nothing was ever linked
    _hard_stop(layout, outcome, failure="invalid-journal")


def test_an_unreadable_boot_id_never_clears_anything(fx, layout):
    fx.activate()
    clear_run_objects(layout, fx)
    Path(layout.boot_id_file).write_text("not-a-boot-id\n")
    outcome, *_ = attest_cl(layout, fx)
    assert outcome.exit_code != 0 or "cleared-by-boot" not in json.dumps(record(layout, outcome.cleanup.k))


def test_a_present_old_pathname_in_a_later_boot_is_kept_and_removes_nothing(fx, layout):
    """RT5 removes nothing merely because the boot changed: every object found is A0."""
    fx.activate()
    p = paths(layout)
    clear_run_objects(layout, fx)
    os.makedirs(os.path.dirname(p.pass_config), mode=0o755)
    Path(p.pass_config).write_bytes(fx.pass_bytes)  # planted, same bytes, new boot
    Path(layout.boot_id_file).write_text(OTHER_BOOT + "\n")
    outcome, *_ = attest_cl(layout, fx)
    assert outcome.exit_code == 1 and outcome.cleanup.pass_class == "present-foreign-unremoved"
    assert Path(p.pass_config).read_bytes() == fx.pass_bytes
    assert record(layout, 1)["st1"]["verified"] is False


def test_a_planted_rule_in_a_later_boot_is_kept_and_never_removed(fx, layout):
    fx.activate()
    p = paths(layout)
    clear_run_objects(layout, fx)
    os.makedirs(os.path.dirname(p.rule), exist_ok=True)
    Path(p.rule).write_bytes(fx.rule_bytes)
    Path(layout.boot_id_file).write_text(OTHER_BOOT + "\n")
    outcome, *_ = attest_cl(layout, fx)
    assert outcome.exit_code == 1 and os.path.exists(p.rule)
    assert outcome.cleanup.rule_class in {"present-foreign-unremoved", "present-damaged-unremoved"}


def test_a_later_boot_with_a_baseline_mismatch_is_not_st1(fx, layout):
    fx.activate()
    clear_run_objects(layout, fx)
    Path(layout.boot_id_file).write_text(OTHER_BOOT + "\n")
    events = Events()
    outcome, *_ = attest_cl(
        layout, fx, services=FakeServices(events, baseline={"host": {"nodename": "x"}}), events=events
    )
    assert outcome.exit_code == 1 and outcome.cleanup.rule_class == "cleared-by-boot"
    assert record(layout, 1)["st1"]["verified"] is False


# --- attempts ----------------------------------------------------------------


def test_attempt_numbers_share_one_sequence_and_attest_is_not_a_backstop_attempt(fx, layout):
    """RT5.CL.6: stop-post, backstop and attest attempts count together; only a backstop
    trigger counts against the backstop bound; no record is overwritten."""
    fx.activate()
    first, _ = procedure(layout, fx)  # stop-post, k=1
    assert first.run().k == 1
    events = Events()
    proc, _ = procedure(layout, fx, trigger=Trigger.ATTEST, holder_state="failed")  # attest, k=2
    assert proc.run().k == 2
    # a hand-built backstop attempt takes k=3 through the same engine
    from application.rp11.cleanup import CleanupProcedure  # noqa: F401

    backstop_proc, _ = procedure(layout, fx)
    backstop_proc._inv = Invocation(ACT_ID, fx.a2_sha256, Trigger.BACKSTOP, 1, "absent", holder_state="inactive")
    assert backstop_proc.run().k == 3
    again, _ = procedure(layout, fx, trigger=Trigger.ATTEST, holder_state="not-found")
    assert again.run().k == 4

    def is_bs(k):
        return is_backstop_attempt(
            Path(layout.var_tmp, f"{ACT_ID}-deact-{k}-evidence/journal").read_bytes(), activation_id=ACT_ID, k=k
        )

    assert [is_bs(k) for k in (1, 2, 3, 4)] == [False, False, True, False]
    names = sorted(os.listdir(Path(layout.store, "activation")))
    assert names == [f"{ACT_ID}.act.json"] + [f"{ACT_ID}.deact-{k}.json" for k in (1, 2, 3, 4)]
    assert [record(layout, k)["trigger"] for k in (1, 2, 3, 4)] == ["stop-post", "attest", "backstop", "attest"]
    assert record(layout, 2)["holder"]["active_state_at_start"] == "failed"
    assert record(layout, 4)["holder"]["active_state_at_start"] == "not-found"
    for k in (1, 2, 3, 4):
        validate_record(parse_canonical(Path(layout.store, f"activation/{ACT_ID}.deact-{k}.json").read_bytes()))


# --- interruption ---------------------------------------------------------------


@pytest.mark.parametrize(
    "crash,point",
    [
        ("pre:service", "PRE"),
        ("unlink:50-freedom-blades-rp11.rules", "CL-G before unlink"),
        ("removed:50-freedom-blades-rp11.rules", "CL-G after unlink"),
        ("after-attempt-dir", "journal creation"),
        ("read-journal:" + f"{ACT_ID}-act-evidence", "CL-1"),
        ("unlink:pass-a.json", "removal"),
        ("removed:pass-a.json", "removal"),
        ("removed:freedom-blades-rp11", "removal"),
        ("removed:grant.id", "removal"),
    ],
)
def test_default_signal_interruption_leaves_no_false_record_and_is_recovered_explicitly(fx, layout, crash, point):
    """RT5.OUT.4: no handler is installed, so an interruption is a process death. It leaves
    no terminal record or ``run-end``; a later explicit attest finishes the cleanup."""
    fx.activate()
    events = Events()
    if crash == "pre:service":

        class Dying(PreUnits):
            def read_unit(self, unit, props):
                if unit == NAMES["service"]:
                    raise Crash(point)
                return super().read_unit(unit, props)

        dying = Dying(events)
        with pytest.raises(Crash):
            AttestProcedure(ACT_ID, dying, Cleanups()).run()
        assert not list(Path(layout.var_tmp).glob(f"{ACT_ID}-deact-*"))
    else:
        def cleanup(holder_state):
            proc, _ = procedure(layout, fx, events=events, crash=crash, trigger=Trigger.ATTEST, holder_state=holder_state)
            return proc.run()

        with pytest.raises(Crash):
            AttestProcedure(ACT_ID, PreUnits(events), cleanup).run()
        assert not list(Path(layout.store, "activation").glob("*.deact-*")), point
        journals = list(Path(layout.var_tmp).glob(f"{ACT_ID}-deact-1-evidence/journal"))
        assert all(b'"op":"run-end"' not in j.read_bytes() for j in journals), point
    outcome, *_ = attest_cl(layout, fx)
    assert outcome.exit_code == 0, (point, outcome.line)
    assert record(layout, outcome.cleanup.k)["trigger"] == "attest"
    p = paths(layout)
    for path in (p.rule, p.pass_config, p.tree_p, p.grant_id, p.lock_dir):
        assert not os.path.lexists(path), (point, path)


def test_an_interruption_in_the_polkit_series_is_recovered(fx, layout):
    fx.activate()

    class DyingPk(FakePk):
        def run(self, *a):
            raise Crash("L4")

    events = Events()
    with pytest.raises(Crash):
        attest_cl(layout, fx, services=FakeServices(events, pk=DyingPk(events)), events=events)
    assert not list(Path(layout.store, "activation").glob("*.deact-*"))
    assert attest_cl(layout, fx)[0].exit_code == 0


def test_an_interruption_in_publication_is_recovered(fx, layout):
    fx.activate()

    class DyingBaseline(FakeBaseline):
        def recompute(self):
            raise Crash("L7")

    events = Events()
    services = FakeServices(events)
    services._baseline = DyingBaseline(events, None)
    with pytest.raises(Crash):
        attest_cl(layout, fx, services=services, events=events)
    outcome, *_ = attest_cl(layout, fx)
    assert outcome.exit_code == 0 and outcome.cleanup.k == 2
    assert "run-end" not in ops(layout, 1) and "run-end" in ops(layout, 2)


def test_no_signal_handler_is_installed_by_the_role_modules():
    root = Path(__file__).resolve().parent.parent
    for name in ("application/rp11/attest.py", "adapters/rp11/attest.py"):
        source = (root / name).read_text()
        assert "signal" not in source and "atexit" not in source, name


# ---------------------------------------------------------------------------
# RT5.OUT — result, exit map and diagnostics
# ---------------------------------------------------------------------------


def test_the_composition_root_runs_the_real_adapters_to_exit_0(fx, layout, capsys):
    fx.activate()
    events = Events()
    code = _run_root(layout, fx, FakeServices(events, units=PreUnits(events)))
    assert code == 0
    err = capsys.readouterr().err
    assert err.count("\n") == 1 and err.startswith(f"rp11-cl st1-verified {ACT_ID} k=1 ")
    assert layout.run not in err and len(err) < 400
    assert record(layout, 1)["trigger"] == "attest"


@pytest.mark.parametrize(
    "fail",
    [
        lambda *a, **k: (_ for _ in ()).throw(ValueError("secret-content /etc/shadow /run/x")),
    ],
)
def test_an_unexpected_exception_exits_70_with_one_fixed_line(monkeypatch, capsys, layout, fail):
    monkeypatch.setattr(attest_root, "build_attest", fail)
    code = run_attest(ACT_ID, A2, layout=layout, connector=lambda: None)
    assert code == 70
    assert capsys.readouterr().err == f"rp11-attest internal-error {ACT_ID} ValueError\n"


def test_an_unexpected_exception_during_the_reads_is_70_and_starts_no_cleanup(fx, layout, capsys, monkeypatch):
    fx.activate()
    built = []
    monkeypatch.setattr(attest_root, "build_procedure", lambda *a, **k: built.append(1))
    events = Events()
    code = _run_root(layout, fx, FakeServices(events, units=PreUnits(events, {"timer": RuntimeError("/etc/shadow")})))
    assert code == 70 and built == []
    assert capsys.readouterr().err == f"rp11-attest internal-error {ACT_ID} RuntimeError\n"


def test_an_invalid_activation_is_never_echoed(capsys, layout):
    assert run_attest("../etc/shadow\n", A2, layout=layout, connector=lambda: None) == 70
    err = capsys.readouterr().err
    assert err == "rp11-attest internal-error invalid-activation ControlSpecError\n"


def test_every_terminal_has_a_distinct_nonzero_exit_except_success(fx, layout):
    assert sorted(t.exit_code for t in Terminal) == [0, 1, 2, 3, 4, 5]
    assert [t for t in Terminal if t.exit_code == 0] == [Terminal.ST1_VERIFIED]


def test_no_exit_zero_without_st1_verified_across_the_whole_matrix(fx, layout):
    """The only path to 0 is a complete ``st1-verified`` cleanup."""
    fx.activate()
    for answers in ({"holder": state("active")}, {"timer": ControlError("timeout")}):
        assert pre(answers)[0].run().exit_code != 0
    outcome, *_ = attest_cl(layout, fx, services=FakeServices(Events(), pk=FakePk(Events(), PkOutcome.UNCONFIRMED)))
    assert outcome.exit_code != 0


# ---------------------------------------------------------------------------
# preservation of the accepted roles
# ---------------------------------------------------------------------------


def test_the_accepted_stop_post_shape_is_unchanged(fx, layout):
    fx.activate()
    proc, _ = procedure(layout, fx)
    assert proc.run().terminal is Terminal.ST1_VERIFIED
    first = attempt_journal(layout, 1)[0]
    assert first["trigger"] == "stop-post" and first["provenance"] == {
        "parent_pid": 4242,
        "invocation_id": "0123456789abcdef0123456789abcdef",
    }
    assert first["helper"]["role"] == "stop-post"
    assert record(layout, 1)["holder"]["invocation_id"] == "0123456789abcdef0123456789abcdef"


def test_the_new_modules_start_no_process_and_read_no_environment():
    root = Path(__file__).resolve().parent.parent
    for name in ("application/rp11/attest.py", "adapters/rp11/attest.py"):
        source = (root / name).read_text()
        for needle in ("os.environ", "getenv", "subprocess", "os.system", "os.exec", "os.fork", "os.kill", "INVOCATION_ID"):
            assert needle not in source.replace("``INVOCATION_ID``", ""), (name, needle)
    assert GENESIS  # imported for the grammar tests above


# --- RT-5 review remediation: missing boot evidence is never success -----------


def _changed_boot(layout, fx):
    import shutil

    fx.activate()
    clear_run_objects(layout, fx)
    if not fx.rules_dir_preexists:  # tree R was the activation's: a boot clears it too
        shutil.rmtree(paths(layout).polkit_run_dir, ignore_errors=True)
    Path(layout.boot_id_file).write_text(OTHER_BOOT + "\n")


def _act_journal(layout) -> Path:
    return Path(layout.var_tmp, f"{ACT_ID}-act-evidence/journal")


def test_a_changed_boot_with_the_act_evidence_directory_missing_is_a_hard_stop(fx, layout):
    import shutil

    _changed_boot(layout, fx)
    shutil.rmtree(_act_journal(layout).parent)
    outcome, *_ = attest_cl(layout, fx)
    _no_cleared_by_boot(layout, outcome)
    _hard_stop(layout, outcome, failure="invalid-journal")


def test_an_incomplete_old_act_journal_without_the_grant_identity_is_a_hard_stop(fx, layout):
    """A valid prefix that never named the rule/pass/grant.id cannot prove their clearance."""
    _changed_boot(layout, fx)
    journal = _act_journal(layout)
    lines = journal.read_bytes().splitlines(keepends=True)
    journal.write_bytes(b"".join(lines[:2]))
    outcome, *_ = attest_cl(layout, fx)
    assert outcome.cleanup.rule_class == "never-linked"
    _hard_stop(layout, outcome)


def test_a_malformed_or_digest_mismatched_old_act_journal_is_a_hard_stop(fx, layout):
    _changed_boot(layout, fx)
    journal = _act_journal(layout)
    data = bytearray(journal.read_bytes())
    data[len(data) // 2] ^= 0x01
    journal.write_bytes(bytes(data))
    outcome, *_ = attest_cl(layout, fx)
    _no_cleared_by_boot(layout, outcome)
    _hard_stop(layout, outcome, failure="invalid-journal")


def test_a_same_boot_with_the_act_evidence_missing_is_a_hard_stop(fx, layout):
    fx.activate()
    clear_run_objects(layout, fx)
    _act_journal(layout).unlink()
    outcome, *_ = attest_cl(layout, fx)
    _hard_stop(layout, outcome, failure="invalid-journal")


@pytest.mark.parametrize("damage", ["missing", "non-tmpfs", "no-mount-fact"])
def test_positive_pk_and_baseline_never_repair_missing_attribution_evidence(fx, layout, damage):
    _changed_boot(layout, fx)
    if damage == "missing":
        _act_journal(layout).unlink()
    elif damage == "non-tmpfs":
        Path(layout.mountinfo).write_text(f"25 1 0:23 / {layout.run} rw - ext4 /dev/x rw\n")
    else:
        Path(layout.mountinfo).write_text("")
    events = Events()
    pk = FakePk(events)  # real not-authorized, matching baseline (fake default)
    outcome, *_ = attest_cl(layout, fx, services=FakeServices(events, pk=pk), events=events)
    assert pk.calls == 1 and outcome.cleanup.pk_outcome == "not-authorized"
    doc = record(layout, outcome.cleanup.k)
    assert doc["st1"]["checks"]["pk-not-authorized"] and doc["st1"]["checks"]["baseline-equal"]
    _hard_stop(layout, outcome, failure="invalid-journal" if damage == "missing" else "st1-not-verified")


# --- second review remediation: a linked tree's missing directory identity -----


def _drop_dir_identities(layout, drop: set[tuple[str, str]]) -> None:
    """Rebuild the ACT journal through the production serializer without the named
    ``dir-identity`` lines, ``(tree tag, rel)``; ``seq`` stays contiguous and ``prev`` chains."""
    from application.rp11.journal import serialize_line

    journal = _act_journal(layout)
    parsed = parse_journal(journal.read_bytes(), kind=JournalKind.ACT, run=ACT_ID)
    assert parsed.valid
    tag, out, prev = None, [], GENESIS
    for line in parsed.lines:
        if line.op == "tree-intent":
            tag = line.fields["tag"]
        if line.op == "dir-identity" and (tag, line.fields["rel"]) in drop:
            continue
        raw = serialize_line(
            JournalKind.ACT, seq=len(out) + 1, prev=prev, run=ACT_ID, op=line.op, fields=line.fields
        )
        out.append(raw)
        prev = hashlib.sha256(raw).hexdigest()
    assert len(out) == len(parsed.lines) - len(drop)
    journal.write_bytes(b"".join(out))


def _attest_positive_pk(layout, fx):
    events = Events()
    pk = FakePk(events)  # real not-authorized, matching baseline (fake default)
    outcome, *_ = attest_cl(layout, fx, services=FakeServices(events, pk=pk), events=events)
    return outcome, pk


@pytest.mark.parametrize(
    "tag,rel,preexists",
    [("p", ".", True), ("r", ".", False), ("r", "rules.d", False)],
    ids=["tree-p-top", "tree-r-top", "tree-r-rules.d"],
)
def test_a_changed_boot_with_a_linked_trees_directory_identity_missing_is_a_hard_stop(
    fx, layout, tag, rel, preexists
):
    fx.rules_dir_preexists = preexists
    _changed_boot(layout, fx)
    _drop_dir_identities(layout, {(tag, rel)})
    outcome, pk = _attest_positive_pk(layout, fx)
    assert pk.calls == 1 and outcome.cleanup.pk_outcome == "not-authorized"
    doc = record(layout, outcome.cleanup.k)
    assert doc["st1"]["checks"]["pk-not-authorized"] and doc["st1"]["checks"]["baseline-equal"]
    assert all(doc["st1"]["checks"].values())  # the observed state is clean: only attribution is missing
    _hard_stop(layout, outcome)


def test_the_exact_changed_boot_tree_p_case_leaves_the_other_objects_cleared_by_boot(fx, layout):
    _changed_boot(layout, fx)
    _drop_dir_identities(layout, {("p", ".")})
    outcome, _ = _attest_positive_pk(layout, fx)
    assert outcome.cleanup.rule_class == "cleared-by-boot" and outcome.cleanup.pass_class == "cleared-by-boot"
    classes = {d["role"]: d["class"] for d in record(layout, 1)["directories"]}
    assert classes["tree-p"] == "never-created" and classes["lock-dir"] == "cleared-by-boot"
    _hard_stop(layout, outcome)


def test_a_changed_boot_with_every_directory_identity_present_still_succeeds_with_tree_r(fx, layout):
    fx.rules_dir_preexists = False
    _changed_boot(layout, fx)
    outcome, pk = _attest_positive_pk(layout, fx)
    assert outcome.exit_code == 0 and pk.calls == 1
    doc = record(layout, 1)
    assert doc["st1"]["verified"] and doc["outcome"] == "st1-verified"
    classes = [d["class"] for d in doc["directories"]]
    assert classes and set(classes) == {"cleared-by-boot"}


def test_a_genuinely_pre_existing_rules_directory_remains_permitted_after_a_boot_change(fx, layout):
    _changed_boot(layout, fx)  # the fixture default: no tree R in the journal
    outcome, _ = _attest_positive_pk(layout, fx)
    assert outcome.exit_code == 0
    classes = {d["role"]: d["class"] for d in record(layout, 1)["directories"]}
    assert classes["rules-dir"] == "pre-existing-kept" and classes["tree-p"] == "cleared-by-boot"


def test_a_durable_prior_removal_still_covers_a_directory_without_a_journaled_identity(fx, layout):
    """Attempt 1 (same boot) removes tree P under its identity and journals ``removed``;
    after a boot change an attest attempt may rely on that fact for that exact path."""
    fx.activate()
    first, *_ = attest_cl(layout, fx)
    assert first.exit_code == 0
    _drop_dir_identities(layout, {("p", ".")})
    Path(layout.boot_id_file).write_text(OTHER_BOOT + "\n")
    outcome, _ = _attest_positive_pk(layout, fx)
    classes = {d["role"]: d["class"] for d in record(layout, outcome.cleanup.k)["directories"]}
    assert classes["tree-p"] == "removed-earlier"
    assert outcome.exit_code == 0 and outcome.cleanup.k == 2


@pytest.mark.parametrize("trigger", [Trigger.STOP_POST, Trigger.BACKSTOP])
def test_the_rule_is_attest_scoped_stop_post_and_backstop_are_unchanged(fx, layout, trigger):
    _changed_boot(layout, fx)
    _drop_dir_identities(layout, {("p", ".")})
    proc, _ = procedure(layout, fx, trigger=trigger)
    assert proc.run().terminal is Terminal.ST1_VERIFIED  # as accepted before RT-5


# --- third review remediation: tree P is mandatory activation evidence ---------


def _rewrite_act(layout, edit) -> None:
    """Rebuild the ACT journal through the production serializer after ``edit`` maps the
    parsed ``[(op, fields)]`` to a new list; ``seq`` stays contiguous and ``prev`` chains,
    so the result is canonically valid and only semantically different."""
    import copy

    from application.rp11.journal import serialize_line

    journal = _act_journal(layout)
    parsed = parse_journal(journal.read_bytes(), kind=JournalKind.ACT, run=ACT_ID)
    assert parsed.valid
    lines = edit([(line.op, copy.deepcopy(dict(line.fields))) for line in parsed.lines])
    out, prev = [], GENESIS
    for op, fields in lines:
        raw = serialize_line(JournalKind.ACT, seq=len(out) + 1, prev=prev, run=ACT_ID, op=op, fields=fields)
        out.append(raw)
        prev = hashlib.sha256(raw).hexdigest()
    journal.write_bytes(b"".join(out))
    assert parse_journal(journal.read_bytes(), kind=JournalKind.ACT, run=ACT_ID).valid


def _tree_p_indexes(lines, op):
    """Indexes of the tree-P ``op`` lines (tree-intent tag ``p`` and what follows it)."""
    tag, found = None, []
    for i, (name, fields) in enumerate(lines):
        if name == "tree-intent":
            tag = fields["tag"]
        if name == op and tag == "p":
            found.append(i)
    return found


def _drop_tree_p(op):
    def edit(lines):
        (index,) = _tree_p_indexes(lines, op)
        return lines[:index] + lines[index + 1 :]

    return edit


def _closed_hard_stop(layout, outcome):
    assert outcome.exit_code == 1
    assert outcome.cleanup.terminal is Terminal.HARD_STOP
    assert outcome.cleanup.failure == "st1-not-verified"
    doc = record(layout, outcome.cleanup.k)
    assert doc["st1"]["verified"] is False and doc["outcome"] != "st1-verified"
    journal = Path(layout.var_tmp, f"{ACT_ID}-cl-attempts/{outcome.cleanup.k}/journal")
    if journal.exists():
        assert b"st1-verified" not in journal.read_bytes()


@pytest.mark.parametrize("op", ["tree-intent", "tree-linked"])
def test_a_changed_boot_without_the_tree_p_intent_or_link_is_a_hard_stop(fx, layout, op):
    """Positive PK/2 and an equal baseline cannot repair a missing mandatory tree fact;
    the pre-fix candidate classified tree P ``never-created`` and published success."""
    _changed_boot(layout, fx)
    _rewrite_act(layout, _drop_tree_p(op))
    outcome, pk = _attest_positive_pk(layout, fx)
    assert pk.calls == 1 and outcome.cleanup.pk_outcome == "not-authorized"
    doc = record(layout, outcome.cleanup.k)
    assert doc["st1"]["checks"]["pk-not-authorized"] and doc["st1"]["checks"]["baseline-equal"]
    assert {d["role"]: d["class"] for d in doc["directories"]}["tree-p"] == "never-created"
    _closed_hard_stop(layout, outcome)


def _edit_tree_p_intent(change):
    def edit(lines):
        (index,) = _tree_p_indexes(lines, "tree-intent")[:1]
        op, fields = lines[index]
        change(fields)
        lines[index] = (op, fields)
        return lines

    return edit


def _edit_tree_p_link(change):
    def edit(lines):
        (index,) = _tree_p_indexes(lines, "tree-linked")
        op, fields = lines[index]
        change(fields)
        lines[index] = (op, fields)
        return lines

    return edit


def _duplicate(op):
    def edit(lines):
        (index,) = _tree_p_indexes(lines, op)
        return lines[: index + 1] + [lines[index]] + lines[index + 1 :]

    return edit


def _link_before_identity(lines):
    (link,) = _tree_p_indexes(lines, "tree-linked")
    (ident,) = _tree_p_indexes(lines, "dir-identity")
    lines[link], lines[ident] = lines[ident], lines[link]
    return lines


def _twin_intent(lines):
    """A second, empty-looking tree-P intent after the real history: not a convenient entry."""
    (index,) = _tree_p_indexes(lines, "tree-intent")
    return lines + [lines[index]]


def _extra_identity(*, after):
    def edit(lines):
        (index,) = _tree_p_indexes(lines, "dir-identity")
        extra = ("dir-identity", {"rel": "not-declared", "dev": 1, "ino": 2})
        at = index + 1 if after else index
        return lines[:at] + [extra] + lines[at:]

    return edit


def _replace_identity(rel):
    def edit(lines):
        (index,) = _tree_p_indexes(lines, "dir-identity")
        lines[index] = ("dir-identity", {**lines[index][1], "rel": rel})
        return lines

    return edit


def _reorder_identities(lines):
    """Two declared directories whose identities arrive in the wrong order."""
    (intent,) = _tree_p_indexes(lines, "tree-intent")[:1]
    (ident,) = _tree_p_indexes(lines, "dir-identity")
    lines[intent][1]["members"].insert(1, {"rel": "sub", "kind": "dir", "mode": 0o755})
    sub = ("dir-identity", {"rel": "sub", "dev": 1, "ino": 2})
    return lines[:ident] + [sub, lines[ident]] + lines[ident + 1 :]


_TREE_P_DAMAGE = {
    "wrong-parent": _edit_tree_p_intent(lambda f: f.update(parent="/var/tmp")),
    "wrong-top": _edit_tree_p_intent(lambda f: f.update(top="other-top")),
    "wrong-tag": _edit_tree_p_intent(lambda f: f.update(tag="x")),
    "wrong-temp": _edit_tree_p_intent(lambda f: f.update(temp=".rp11-other.tmp")),
    "extra-directory": _edit_tree_p_intent(
        lambda f: f["members"].append({"rel": "extra", "kind": "dir", "mode": 0o755})
    ),
    "wrong-mode": _edit_tree_p_intent(lambda f: f["members"][0].update(mode=0o777)),
    "wrong-file-member": _edit_tree_p_intent(lambda f: f["members"][1].update(rel="other.json")),
    "file-wrong-mode": _edit_tree_p_intent(lambda f: f["members"][1].update(mode=0o600)),
    "file-wrong-sha256": _edit_tree_p_intent(lambda f: f["members"][1].update(sha256="ab" * 32)),
    "file-wrong-size": _edit_tree_p_intent(lambda f: f["members"][1].update(size=f["members"][1]["size"] + 1)),
    "duplicate-top-member": _edit_tree_p_intent(lambda f: f["members"].insert(1, dict(f["members"][0]))),
    "duplicate-file-member": _edit_tree_p_intent(lambda f: f["members"].append(dict(f["members"][1]))),
    "conflicting-duplicate-directory": _edit_tree_p_intent(
        lambda f: f["members"].insert(1, {**f["members"][0], "mode": 0o700})
    ),
    "undeclared-identity-after": _extra_identity(after=True),
    "undeclared-identity-before": _extra_identity(after=False),
    "missing-identity-with-extra": _replace_identity("not-declared"),
    "reordered-identities": _reorder_identities,
    "link-wrong-top": _edit_tree_p_link(lambda f: f.update(top="other-top")),
    "link-wrong-parent": _edit_tree_p_link(lambda f: f.update(parent="/var/tmp")),
    "duplicate-link": _duplicate("tree-linked"),
    "duplicate-identity": _duplicate("dir-identity"),
    "duplicate-intent": _duplicate("tree-intent"),
    "twin-intent-after": _twin_intent,
    "link-before-identity": _link_before_identity,
}


@pytest.mark.parametrize("damage", sorted(_TREE_P_DAMAGE))
def test_a_changed_boot_with_an_inexact_tree_p_history_is_a_hard_stop(fx, layout, damage):
    _changed_boot(layout, fx)
    _rewrite_act(layout, _TREE_P_DAMAGE[damage])
    outcome, pk = _attest_positive_pk(layout, fx)
    assert pk.calls == 1 and outcome.cleanup.pk_outcome == "not-authorized"
    _closed_hard_stop(layout, outcome)


@pytest.mark.parametrize("op", ["tree-intent", "tree-linked"])
def test_the_tree_p_rule_is_attest_scoped_for_stop_post_and_backstop(fx, layout, op):
    _changed_boot(layout, fx)
    _rewrite_act(layout, _drop_tree_p(op))
    for trigger in (Trigger.STOP_POST, Trigger.BACKSTOP):
        proc, _ = procedure(layout, fx, trigger=trigger)
        assert proc.run().terminal is Terminal.ST1_VERIFIED  # as accepted before RT-5


def test_a_prior_removal_does_not_replace_a_missing_tree_p_intent(fx, layout):
    fx.activate()
    first, *_ = attest_cl(layout, fx)
    assert first.exit_code == 0
    _rewrite_act(layout, _drop_tree_p("tree-intent"))
    Path(layout.boot_id_file).write_text(OTHER_BOOT + "\n")
    outcome, _ = _attest_positive_pk(layout, fx)
    assert outcome.exit_code == 1


def _tree_evidence(**changes):
    from application.rp11.evidence import TreeEvidence

    members = ((".", "dir", 0o755), ("sub", "dir", 0o755), ("f.json", "file", 0o644, "ab" * 32, 3))
    base = dict(
        parent="/run", top="t", temp=".tmp", tag="p", linked=True, directories=(),
        members=members, links=1, identity_rels=(".", "sub"),
    )
    return TreeEvidence(**{**base, **changes}), members


@pytest.mark.parametrize(
    ("rels", "exact"),
    [
        ((".", "sub"), True),
        ((".",), True),  # a missing identity is judged by prior removal, not by shape
        ((), True),
        (("sub", "."), False),  # reordered
        ((".", ".", "sub"), False),  # duplicated
        ((".", "sub", "sub"), False),
        ((".", "nope", "sub"), False),  # undeclared
        (("nope",), False),
    ],
)
def test_identity_lines_may_only_be_missing_never_duplicated_undeclared_or_reordered(rels, exact):
    tree, members = _tree_evidence(identity_rels=rels)
    got = tree.is_exactly(parent="/run", top="t", temp=".tmp", tag="p", members=members)
    assert got is exact
