"""Executor OS-6: OC-1/OC-2/OC-3 gate SA-2 ``stop``, invoked once or not at all (CX-3, Lemma R6)."""

from __future__ import annotations

import os

import pytest

from adapters.executor.interrupt import (
    CHILD_ENV,
    EX_INTERNAL,
    EX_USAGE,
    STOP_ARGV,
    SUDO,
    LocalConsumeJournalReader,
    run_interrupt,
)
from application.rp11.attribution import Owner
from application.executor.interrupt import (
    MAX_JOURNAL_BYTES,
    InterruptEnd,
    InterruptProcedure,
    PrivilegedStop,
)
from application.rp11.journal import GENESIS, JournalKind, consume_run, serialize_line
from application.rp11.paths import ActivationPaths, Layout
from application.unit_control import (
    CAPTURE_UNIT,
    ControlError,
    ControlOk,
    ControlRefused,
    ControlSpecError,
    RefusalReason,
    UnitProperty,
)

ACT = "rp11-act-20261018T120000Z-0123abcd"
OTHER_ACT = "rp11-act-20261018T120000Z-ffffabcd"
INV = "a" * 32
OTHER_INV = "b" * 32
H64 = "c" * 64
AS, IV = UnitProperty.ACTIVE_STATE, UnitProperty.INVOCATION_ID


def run_start(invocation: str = INV, **over) -> dict:
    fields = {
        "invocation_id": invocation,
        "boot_id": "11111111-2222-3333-4444-555555555555",
        "claim": {"dev": 1, "ino": 2},
        "act_journal": {"sha256": H64, "length": 10},
        "lock": {"object": {"path": "/run/x", "dev": 1, "ino": 3}, "mode": "held", "wait_ms": 0},
        "helper": {"role": "consume", "tool_sha256": H64},
    }
    fields.update(over)
    return fields


REMOVE_INTENT = ("remove-intent", {"path": "/run/r", "dev": 1, "ino": 4, "sha256": H64})
REMOVED = ("removed", {"path": "/run/r"})
GRANT_CHECK = ("grant-check", {"verb": "start", "mode": "seek-not-authorized", "outcome": "not-authorized",
                               "reason": "not-authorized", "calls": 1})
CONSUMED = ("consumed", {"pk_status": "not-authorized", "inactive_enter_us": 5})
RUN_END = ("run-end", {"outcome": "consumed"})
CHILD = ("child", {"entry": {"a": 1}})
# What ``ConsumeProcedure`` emits on success: CQ-2, CQ-3, CQ-5 (children, grant-check), CQ-6, CQ-7.
GOOD = [("run-start", run_start()), REMOVE_INTENT, REMOVED, GRANT_CHECK, CONSUMED, RUN_END]


def journal(entries, run: str | None = None) -> bytes:
    out, prev = b"", GENESIS
    import hashlib

    for seq, (op, fields) in enumerate(entries, start=1):
        line = serialize_line(JournalKind.CONSUME, seq=seq, prev=prev, run=run or consume_run(ACT), op=op, fields=fields)
        out += line
        prev = hashlib.sha256(line).hexdigest()
    return out


_DEFAULT = object()


class Units:
    def __init__(self, result=_DEFAULT, error=None):
        self.result = ControlOk({AS: "active", IV: INV}) if result is _DEFAULT else result
        self.error, self.calls = error, []

    def read_unit(self, unit, properties):
        self.calls.append((unit, properties))
        if self.error:
            raise self.error
        return self.result


class Journals:
    def __init__(self, data=None, error=None):
        self.data = journal(GOOD) if data is None else data
        self.error, self.calls = error, []

    def read_consume_journal(self, activation_id):
        self.calls.append(activation_id)
        if self.error:
            raise self.error
        return self.data


class Stop:
    def __init__(self, outcome=PrivilegedStop.STOPPED, error=None):
        self.outcome, self.error, self.calls = outcome, error, 0

    def invoke_stop(self):
        self.calls += 1
        if self.error:
            raise self.error
        return self.outcome


def attempt(units=None, journals=None, stop=None, activation=ACT):
    units, journals, stop = units or Units(), journals or Journals(), stop or Stop()
    result = InterruptProcedure(units, journals, stop).run(activation)
    return result, units, journals, stop


def assert_unavailable(result, reason, stop):
    assert (result.end, result.reason) == (InterruptEnd.UNAVAILABLE, reason)
    assert result.exit_code == 30 and not result.effect_not_confirmed
    assert stop.calls == 0


# --- success -----------------------------------------------------------------


def test_exact_oc1_oc2_oc3_invokes_sa2_once_and_returns_interrupted():
    result, units, journals, stop = attempt()
    assert (result.end, result.exit_code, result.line) == (InterruptEnd.INTERRUPTED, 0, "rp11-interrupt interrupted")
    assert stop.calls == 1
    # exactly the two accepted properties of the one fixed unit; one read of each input
    assert units.calls == [(CAPTURE_UNIT, (AS, IV))] and journals.calls == [ACT]


def test_stale_read_control_one_read_one_stop_and_no_retry_whatever_follows():
    """Lemma R6: the claim crossed SB-1 once OC-1..3 were observed; nothing re-reads or retries."""
    for outcome in PrivilegedStop:
        result, units, journals, stop = attempt(stop=Stop(outcome))
        assert stop.calls == 1 and len(units.calls) == 1 and len(journals.calls) == 1


# --- OC-1 / OC-2 unit side -----------------------------------------------------


@pytest.mark.parametrize(
    "state", ["activating", "reloading", "deactivating", "inactive", "failed", "maintenance", "refreshing",
              "start-pre", "start", "start-post", "", "Active", "active ", "unknown", "\x00"],
)
def test_every_state_other_than_exact_active_is_unavailable(state):
    result, units, journals, stop = attempt(units=Units(ControlOk({AS: state, IV: INV})))
    assert_unavailable(result, "not-active", stop)
    assert journals.calls == []  # nothing further is read or touched


class Hostile(str):
    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False

    __hash__ = str.__hash__


class HostileInt(int):
    def __bool__(self):
        return True


class HostileDict(dict):
    def __len__(self):
        return 2


class HostileOk(ControlOk):
    pass


class HostileRefused(ControlRefused):
    pass


@pytest.mark.parametrize(
    "result",
    [
        ControlOk({AS: Hostile("anything"), IV: INV}),
        ControlOk({AS: "active", IV: Hostile("x")}),
        ControlOk({AS: 1, IV: INV}),
        ControlOk({AS: "active", IV: 5}),
        ControlOk({AS: "active", IV: None}),
        ControlOk({AS: HostileInt(1), IV: INV}),
        ControlOk({AS: "active"}),
        ControlOk({AS: "active", IV: INV, UnitProperty.JOB: 0}),
        ControlOk({"ActiveState": "active", "InvocationID": INV}),
        ControlOk(HostileDict({AS: "active", IV: INV})),
        ControlOk([("ActiveState", "active")]),
        ControlOk(None),
        HostileOk({AS: "active", IV: INV}),
        HostileRefused(RefusalReason.NOT_LOADED),
        object(),
        None,
        "active",
        True,
    ],
)
def test_wrong_type_subclass_and_hostile_boundary_values_never_manufacture_availability(result):
    outcome, _, journals, stop = attempt(units=Units(result))
    assert outcome.end is InterruptEnd.UNAVAILABLE and outcome.reason.startswith("unit-read-")
    assert stop.calls == 0 and journals.calls == []


@pytest.mark.parametrize("inv", ["", "A" * 32, "a" * 31, "a" * 33, "g" * 32, "a" * 32 + "\n", "absent", " " + "a" * 31])
def test_empty_or_malformed_unit_invocation_id_is_unavailable(inv):
    result, _, journals, stop = attempt(units=Units(ControlOk({AS: "active", IV: inv})))
    assert_unavailable(result, "invocation-invalid", stop)
    assert journals.calls == []


def test_unit_read_refusal_error_and_exception_are_unavailable_without_privilege():
    for res, reason in [
        (ControlRefused(RefusalReason.NOT_LOADED), "unit-read-refused"),
        (ControlError("bus", "secret detail", False), "unit-read-error"),
        (ControlError("bus", "x", True), "unit-read-error"),
    ]:
        result, _, journals, stop = attempt(units=Units(res))
        assert_unavailable(result, reason, stop)
    result, _, _, stop = attempt(units=Units(error=RuntimeError("boom /secret/path")))
    assert_unavailable(result, "unit-read-error", stop)
    assert "secret" not in result.line


# --- OC-2 / OC-3 journal side ---------------------------------------------------


def with_ops(*entries) -> bytes:
    return journal(list(entries))


RS = ("run-start", run_start())
FAILED = ("consume-failed", {"step": "cq-5", "class": "pk"})
FAILED_END = ("run-end", {"outcome": "failed"})
HEAD = [RS, REMOVE_INTENT, REMOVED]
TAIL = [GRANT_CHECK, CONSUMED, RUN_END]

JOURNAL_CASES = {
    "invocation-mismatch": journal([("run-start", run_start(OTHER_INV)), *GOOD[1:]]),
    "invocation-absent": journal([("run-start", run_start("absent")), *GOOD[1:]]),
    "not-consumed": journal([RS, RUN_END]),
    "not-consumed-only-start": journal([RS]),
    "consume-failed": journal([RS, FAILED, FAILED_END]),
    "consume-failed-hybrid": journal([RS, FAILED, CONSUMED, RUN_END]),
    "consume-failed-after": journal([RS, CONSUMED, FAILED, RUN_END]),
    "duplicate-consumed": journal([RS, CONSUMED, CONSUMED, RUN_END]),
    "consumed-without-run-end": journal([RS, CONSUMED]),
    "run-end-before-consumed": journal([RS, RUN_END, CONSUMED]),
    "duplicate-run-end": journal([*GOOD, RUN_END]),
    "trailing-line": journal([*GOOD, CHILD]),
    "failed-terminal": journal([RS, CONSUMED, FAILED_END]),
}


@pytest.mark.parametrize("name", sorted(JOURNAL_CASES))
def test_non_production_or_incomplete_consume_histories_are_unavailable(name):
    result, units, _, stop = attempt(journals=Journals(JOURNAL_CASES[name]))
    assert result.end is InterruptEnd.UNAVAILABLE and result.exit_code == 30
    assert stop.calls == 0 and len(units.calls) == 1


def _hist(*parts):
    return journal([part for group in parts for part in (group if isinstance(group, list) else [group])])


HISTORY_NEGATIVES = {
    # canonical, chained, valid lines that ``ConsumeProcedure`` can never emit on success
    "late-child": [RS, CONSUMED, CHILD, RUN_END],
    "late-remove-intent": [RS, CONSUMED, REMOVE_INTENT, RUN_END],
    "late-grant-check": [RS, CONSUMED, GRANT_CHECK, RUN_END],
    "late-removed": [*HEAD[:2], GRANT_CHECK, CONSUMED, REMOVED, RUN_END],
    "consumed-before-removal-and-check": [RS, CONSUMED, RUN_END],
    "consumed-before-authorization-evidence": [*HEAD, CONSUMED, RUN_END],
    "consumed-before-removal": [RS, GRANT_CHECK, CONSUMED, RUN_END],
    "no-remove-intent": [RS, REMOVED, GRANT_CHECK, CONSUMED, RUN_END],
    "no-removed": [RS, REMOVE_INTENT, GRANT_CHECK, CONSUMED, RUN_END],
    "reordered-removal": [RS, REMOVED, REMOVE_INTENT, GRANT_CHECK, CONSUMED, RUN_END],
    "duplicate-remove-intent": [RS, REMOVE_INTENT, REMOVE_INTENT, REMOVED, GRANT_CHECK, CONSUMED, RUN_END],
    "duplicate-removed": [*HEAD, REMOVED, GRANT_CHECK, CONSUMED, RUN_END],
    "removed-another-path": [RS, REMOVE_INTENT, ("removed", {"path": "/run/other"}), GRANT_CHECK, CONSUMED, RUN_END],
    "remove-failed-hybrid": [RS, REMOVE_INTENT, ("remove-failed", {"path": "/run/r", "errno": 1}), REMOVED,
                             GRANT_CHECK, CONSUMED, RUN_END],
    "no-grant-check": [*HEAD, CONSUMED, RUN_END],
    "duplicate-grant-check": [*HEAD, GRANT_CHECK, GRANT_CHECK, CONSUMED, RUN_END],
    "grant-check-before-removal": [RS, GRANT_CHECK, REMOVE_INTENT, REMOVED, CONSUMED, RUN_END],
    "grant-check-between-removal": [RS, REMOVE_INTENT, GRANT_CHECK, REMOVED, CONSUMED, RUN_END],
    "child-before-removal": [RS, CHILD, REMOVE_INTENT, REMOVED, GRANT_CHECK, CONSUMED, RUN_END],
    "child-between-removal": [RS, REMOVE_INTENT, CHILD, REMOVED, GRANT_CHECK, CONSUMED, RUN_END],
    "child-after-grant-check": [*HEAD, GRANT_CHECK, CHILD, CONSUMED, RUN_END],
    "child-after-consumed": [*HEAD, GRANT_CHECK, CONSUMED, CHILD, RUN_END],
    "child-after-run-end": [*GOOD, CHILD],
    "operation-between-consumed-and-run-end": [*HEAD, GRANT_CHECK, CONSUMED, ("removed", {"path": "/run/r"}), RUN_END],
    "second-run-end": [*GOOD, RUN_END],
    "check-authorized": [*HEAD, ("grant-check", {**GRANT_CHECK[1], "outcome": "authorized"}), CONSUMED, RUN_END],
    "check-unconfirmed": [*HEAD, ("grant-check", {**GRANT_CHECK[1], "outcome": "unconfirmed"}), CONSUMED, RUN_END],
    "check-wrong-verb": [*HEAD, ("grant-check", {**GRANT_CHECK[1], "verb": "stop"}), CONSUMED, RUN_END],
    "check-wrong-mode": [*HEAD, ("grant-check", {**GRANT_CHECK[1], "mode": "seek-authorized"}), CONSUMED, RUN_END],
    "consumed-disagrees-with-check": [*HEAD, GRANT_CHECK,
                                      ("consumed", {"pk_status": "authorized", "inactive_enter_us": 5}), RUN_END],
    "failure-line-mixed-in": [*HEAD, GRANT_CHECK, FAILED, CONSUMED, RUN_END],
    "failure-after-consumed": [*HEAD, GRANT_CHECK, CONSUMED, FAILED, RUN_END],
    "failed-terminal-outcome": [*HEAD, GRANT_CHECK, CONSUMED, FAILED_END],
    "failed-terminal-after-failure": [*HEAD, GRANT_CHECK, FAILED, FAILED_END],
}


@pytest.mark.parametrize("name", sorted(HISTORY_NEGATIVES))
def test_valid_line_histories_the_production_consume_cannot_emit_launch_nothing(name):
    result, units, journals, stop = attempt(journals=Journals(journal(HISTORY_NEGATIVES[name])))
    assert result.end is InterruptEnd.UNAVAILABLE and result.exit_code == 30 and not result.effect_not_confirmed
    assert stop.calls == 0 and len(units.calls) == 1 and len(journals.calls) == 1  # no retry, no second look


@pytest.mark.parametrize("reason,entries", [
    ("journal-history", [*HEAD, GRANT_CHECK, CONSUMED, ("removed", {"path": "/run/r"}), RUN_END]),
    ("journal-history", [RS, CONSUMED, CHILD, RUN_END]),
    ("not-consumed", [*HEAD, GRANT_CHECK, RUN_END]),
    ("consume-failed", [*HEAD, GRANT_CHECK, FAILED, CONSUMED, RUN_END]),
])
def test_history_rejections_carry_stable_value_free_reasons(reason, entries):
    result, _, _, stop = attempt(journals=Journals(journal(entries)))
    assert_unavailable(result, reason, stop)


@pytest.mark.parametrize("children", [0, 1, 2, 5])
def test_zero_one_and_many_ordered_child_records_are_the_complete_success_history(children):
    kids = [("child", {"entry": {"n": n}}) for n in range(children)]
    result, units, journals, stop = attempt(journals=Journals(journal([*HEAD, *kids, *TAIL])))
    assert (result.end, result.exit_code) == (InterruptEnd.INTERRUPTED, 0) and stop.calls == 1
    assert len(units.calls) == 1 and len(journals.calls) == 1


def test_the_exact_history_helper_is_the_production_consume_sequence():
    """The accepted history is the one ``ConsumeProcedure`` appends; no other op is in its vocabulary."""
    from application.executor.interrupt import is_successful_consume_history
    from application.rp11.journal import parse_journal

    parsed = parse_journal(journal(GOOD), kind=JournalKind.CONSUME, run=consume_run(ACT))
    assert is_successful_consume_history(parsed.lines)
    assert not is_successful_consume_history(parse_journal(journal(GOOD[:-1]), kind=JournalKind.CONSUME, run=consume_run(ACT)).lines)


def test_specific_reasons_for_the_oc2_and_oc3_failures():
    cases = {"invocation-mismatch": "invocation-mismatch", "invocation-absent": "invocation-mismatch",
             "not-consumed": "not-consumed", "consume-failed": "consume-failed",
             "duplicate-consumed": "not-consumed", "consumed-without-run-end": "journal-incomplete",
             "failed-terminal": "journal-incomplete"}
    for name, reason in cases.items():
        result, _, _, stop = attempt(journals=Journals(JOURNAL_CASES[name]))
        assert_unavailable(result, reason, stop)


def test_torn_tail_after_a_complete_history_is_unavailable():
    result, _, _, stop = attempt(journals=Journals(journal(GOOD) + b'{"seq":6,"op":"ch'))
    assert_unavailable(result, "journal-torn", stop)


def test_torn_consumed_line_is_unavailable_not_evidence():
    data = journal(GOOD[:-1])
    result, _, _, stop = attempt(journals=Journals(data[:-5]))
    assert result.end is InterruptEnd.UNAVAILABLE and stop.calls == 0


def test_malformed_wrongly_chained_wrong_run_and_hybrid_run_start_are_invalid():
    good = journal(GOOD).split(b"\n")
    malformed = b"not json\n" + b"\n".join(good[1:])
    chained = b"\n".join([good[0], good[2], good[1], *good[3:]])
    wrong_run = journal(GOOD, run=consume_run(OTHER_ACT))
    dup_start = journal([RS, RS, *GOOD[1:]])
    late_start = journal([REMOVE_INTENT, RS, *GOOD[2:]])
    extra_field = journal(GOOD).replace(b'"op":"consumed"', b'"op":"consumed","x":1')
    for data in (malformed, chained, wrong_run, dup_start, late_start, extra_field, b"", b"\n", b"{}\n"):
        result, _, _, stop = attempt(journals=Journals(data))
        assert_unavailable(result, "journal-invalid", stop)


def test_oversized_journal_text_is_unavailable_even_if_a_reader_returned_it():
    result, _, _, stop = attempt(journals=Journals(journal(GOOD) + b"x" * MAX_JOURNAL_BYTES))
    assert_unavailable(result, "journal-unavailable", stop)


@pytest.mark.parametrize("value", [None, "text", bytearray(b"x"), memoryview(b"x"), 5])
def test_non_bytes_reader_result_is_unavailable(value):
    result, _, _, stop = attempt(journals=Journals(data=value) if value is not None else Journals(data=b"") )
    assert result.end is InterruptEnd.UNAVAILABLE and stop.calls == 0


def test_reader_none_and_exception_are_unavailable():
    class NoJournal(Journals):
        def read_consume_journal(self, activation_id):
            self.calls.append(activation_id)

    j = NoJournal()
    result, _, _, stop = attempt(journals=j)
    assert_unavailable(result, "journal-unavailable", stop)
    result, _, _, stop = attempt(journals=Journals(error=OSError("/secret/path")))
    assert_unavailable(result, "journal-error", stop)
    assert "secret" not in result.line


# --- SA-2 uncertainty -----------------------------------------------------------


@pytest.mark.parametrize(
    "outcome,end,code,reason,unconfirmed",
    [
        (PrivilegedStop.STOPPED, InterruptEnd.INTERRUPTED, 0, "", False),
        (PrivilegedStop.REFUSED, InterruptEnd.REFUSED, 20, "stop-refused", False),
        (PrivilegedStop.NOT_SENT, InterruptEnd.ERROR, 21, "stop-not-sent", False),
        (PrivilegedStop.NOT_CONFIRMED, InterruptEnd.ERROR, 22, "stop-not-confirmed", True),
    ],
)
def test_sa2_certainty_is_preserved_and_one_call_only(outcome, end, code, reason, unconfirmed):
    result, _, _, stop = attempt(stop=Stop(outcome))
    assert (result.end, result.exit_code, result.reason, result.effect_not_confirmed) == (end, code, reason, unconfirmed)
    assert stop.calls == 1


def test_unexpected_sa2_exception_is_effect_not_confirmed_without_retry_or_leak():
    result, _, _, stop = attempt(stop=Stop(error=RuntimeError("secret detail")))
    assert (result.end, result.exit_code, result.effect_not_confirmed) == (InterruptEnd.ERROR, 22, True)
    assert stop.calls == 1 and "secret" not in result.line


def test_a_malformed_invoker_result_is_not_success():
    result, _, _, stop = attempt(stop=Stop(outcome="stopped"))
    assert (result.end, result.exit_code) == (InterruptEnd.ERROR, 22) and stop.calls == 1


# --- activation id ----------------------------------------------------------------


@pytest.mark.parametrize("bad", ["", "x", ACT + "\n", ACT + "-x", "../" + ACT, ACT.upper(), None, 5, b"x", "rp11-capture-pass-a.service"])
def test_invalid_activation_ids_are_refused_before_any_io(bad):
    units, journals, stop = Units(), Journals(), Stop()
    with pytest.raises(ControlSpecError):
        InterruptProcedure(units, journals, stop).run(bad)
    assert (units.calls, journals.calls, stop.calls) == ([], [], 0)


# --- entry point ------------------------------------------------------------------


def test_entry_maps_results_to_one_bounded_line_and_exit_status(capsys):
    cases = [
        (dict(), 0, "rp11-interrupt interrupted\n"),
        (dict(units=Units(ControlOk({AS: "activating", IV: INV}))), 30, "rp11-interrupt unavailable not-active\n"),
        (dict(stop=Stop(PrivilegedStop.REFUSED)), 20, "rp11-interrupt refused stop-refused\n"),
        (dict(stop=Stop(PrivilegedStop.NOT_SENT)), 21, "rp11-interrupt error stop-not-sent\n"),
        (dict(stop=Stop(PrivilegedStop.NOT_CONFIRMED)), 22, "rp11-interrupt error stop-not-confirmed\n"),
    ]
    for ports, code, line in cases:
        ports.setdefault("units", Units())
        ports.setdefault("journals", Journals())
        ports.setdefault("stop", Stop())
        assert run_interrupt([ACT], **ports) == code
        assert capsys.readouterr().err == line


@pytest.mark.parametrize("argv", [[], [ACT, "extra"], ["--stop"], ["x"], [ACT + "\n"], ["rp11-capture-pass-a.service"]])
def test_entry_accepts_exactly_one_valid_activation_operand(argv, capsys):
    units, journals, stop = Units(), Journals(), Stop()
    assert run_interrupt(argv, units=units, journals=journals, stop=stop) == EX_USAGE
    assert capsys.readouterr().err == "rp11-interrupt usage\n"
    assert (units.calls, journals.calls, stop.calls) == ([], [], 0)


def test_entry_internal_error_is_one_fixed_value_free_line(capsys, monkeypatch):
    Odd = type("Boom_/secret/path_" + "x" * 300 + "\u202e", (Exception,), {})

    def explode(self, activation_id):
        raise Odd("token=SECRET /var/lib/private")

    monkeypatch.setattr(InterruptProcedure, "run", explode)
    assert run_interrupt([ACT], units=Units(), journals=Journals(), stop=Stop()) == EX_INTERNAL == 70
    err = capsys.readouterr().err
    assert err == "rp11-interrupt internal-error\n"
    assert "Boom" not in err and "secret" not in err.lower() and len(err) < 64


def test_entry_interruption_and_unexpected_unit_failure_lines(capsys):
    class Boom(Stop):
        def invoke_stop(self):
            raise KeyboardInterrupt

    assert run_interrupt([ACT], units=Units(), journals=Journals(), stop=Boom()) == 22
    assert capsys.readouterr().err == "rp11-interrupt error interrupted\n"
    bad_units = Units()
    bad_units.read_unit = lambda *a: (_ for _ in ()).throw(SystemError("x"))
    assert run_interrupt([ACT], units=bad_units, journals=Journals(), stop=Stop()) == 30


# --- fixed privileged vector --------------------------------------------------------


def test_the_privileged_vector_is_the_exact_accepted_one():
    assert STOP_ARGV == (
        "sudo", "-n", "/usr/bin/python3.14", "-I", "-S",
        "/usr/local/libexec/freedom-blades-rp11/rp11_h1.py", "stop",
    )
    assert SUDO == "/usr/bin/sudo" and CHILD_ENV == {"PATH": "/usr/bin:/bin"}
    assert EX_INTERNAL == 70


def test_handed_off_is_effect_not_confirmed_and_never_a_success():
    result, _, _, stop = attempt(stop=Stop(PrivilegedStop.HANDED_OFF))
    assert (result.end, result.exit_code, result.reason, result.effect_not_confirmed) == (
        InterruptEnd.ERROR, 22, "stop-handed-off", True)
    assert result.line == "rp11-interrupt error stop-handed-off" and stop.calls == 1


def test_blocked_is_not_sent_and_names_itself():
    result, _, _, stop = attempt(stop=Stop(PrivilegedStop.BLOCKED))
    assert (result.end, result.exit_code, result.reason, result.effect_not_confirmed) == (
        InterruptEnd.ERROR, 21, "stop-blocked", False)


def test_there_is_no_unsettled_incident_token_left():
    assert {outcome.name for outcome in PrivilegedStop} == {
        "STOPPED", "REFUSED", "NOT_SENT", "NOT_CONFIRMED", "HANDED_OFF", "BLOCKED"}


# --- journal reader -------------------------------------------------------------------


def layout_for(tmp_path) -> Layout:
    var_tmp = tmp_path / "vt"
    var_tmp.mkdir(exist_ok=True)
    return Layout(var_tmp=str(var_tmp), owner=Owner(os.getuid(), os.getgid()))


def stage(tmp_path, data: bytes | None = None, *, dir_mode=0o755, file_mode=0o644) -> tuple[Layout, str]:
    layout = layout_for(tmp_path)
    directory = ActivationPaths(layout, ACT).consume_dir
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, "journal")
    with open(path, "wb") as handle:
        handle.write(journal(GOOD) if data is None else data)
    os.chmod(path, file_mode)
    os.chmod(directory, dir_mode)
    return layout, path


def test_reader_returns_the_exact_bytes_of_the_accepted_object(tmp_path):
    layout, _ = stage(tmp_path)
    assert LocalConsumeJournalReader(layout).read_consume_journal(ACT) == journal(GOOD)
    result = InterruptProcedure(Units(), LocalConsumeJournalReader(layout), Stop()).run(ACT)
    assert result.end is InterruptEnd.INTERRUPTED


def test_reader_rejects_every_wrong_object(tmp_path):
    layout, path = stage(tmp_path)
    directory = os.path.dirname(path)
    reader = LocalConsumeJournalReader(layout)
    # wrong modes
    os.chmod(path, 0o664)
    assert reader.read_consume_journal(ACT) is None
    os.chmod(path, 0o600)
    assert reader.read_consume_journal(ACT) is None
    os.chmod(path, 0o644)
    os.chmod(directory, 0o700)
    assert reader.read_consume_journal(ACT) is None
    os.chmod(directory, 0o775)
    assert reader.read_consume_journal(ACT) is None
    os.chmod(directory, 0o755)
    assert reader.read_consume_journal(ACT) == journal(GOOD)
    # wrong owner expectation
    wrong = Layout(var_tmp=layout.var_tmp, owner=Owner(os.getuid() + 1, os.getgid()))
    assert LocalConsumeJournalReader(wrong).read_consume_journal(ACT) is None
    # hard link
    os.link(path, path + ".link")
    assert reader.read_consume_journal(ACT) is None
    os.unlink(path + ".link")
    # absent journal / absent directory / other activation
    assert reader.read_consume_journal(OTHER_ACT) is None
    os.unlink(path)
    assert reader.read_consume_journal(ACT) is None


def test_reader_does_not_follow_symlinks_or_accept_non_regular_objects(tmp_path):
    layout, path = stage(tmp_path)
    directory = os.path.dirname(path)
    reader = LocalConsumeJournalReader(layout)
    real = os.path.join(layout.var_tmp, "real-journal")
    os.rename(path, real)
    os.symlink(real, path)
    assert reader.read_consume_journal(ACT) is None
    os.unlink(path)
    os.mkfifo(path, 0o644)
    assert reader.read_consume_journal(ACT) is None
    os.unlink(path)
    os.mkdir(path, 0o755)
    assert reader.read_consume_journal(ACT) is None
    os.rmdir(path)
    # the evidence directory itself a symlink
    moved = directory + "-moved"
    os.rename(directory, moved)
    os.symlink(moved, directory)
    assert reader.read_consume_journal(ACT) is None


def test_reader_rejects_oversized_evidence_without_reading_it(tmp_path):
    layout, path = stage(tmp_path, b"x" * (MAX_JOURNAL_BYTES + 1))
    assert LocalConsumeJournalReader(layout).read_consume_journal(ACT) is None
    with open(path, "wb") as handle:
        handle.write(b"x" * MAX_JOURNAL_BYTES)
    assert LocalConsumeJournalReader(layout).read_consume_journal(ACT) == b"x" * MAX_JOURNAL_BYTES


def test_reader_treats_growth_during_the_read_as_unavailable(tmp_path, monkeypatch):
    layout, path = stage(tmp_path)
    import adapters.executor.interrupt as module

    real = module._read_capped

    def growing(fd, size):
        data = real(fd, size)
        with open(path, "ab") as handle:
            handle.write(b"more")
        return data

    monkeypatch.setattr(module, "_read_capped", growing)
    assert LocalConsumeJournalReader(layout).read_consume_journal(ACT) is None


def test_reader_treats_a_short_read_as_unavailable(tmp_path, monkeypatch):
    layout, _ = stage(tmp_path)
    import adapters.executor.interrupt as module

    monkeypatch.setattr(module, "_read_capped", lambda fd, size: b"short")
    assert LocalConsumeJournalReader(layout).read_consume_journal(ACT) is None


def test_reader_treats_a_directory_replaced_during_the_read_as_unavailable(tmp_path, monkeypatch):
    layout, path = stage(tmp_path)
    directory = os.path.dirname(path)
    import adapters.executor.interrupt as module

    real = module._read_capped

    def swap(fd, size):
        data = real(fd, size)
        os.rename(directory, directory + "-old")
        os.makedirs(directory)
        return data

    monkeypatch.setattr(module, "_read_capped", swap)
    assert LocalConsumeJournalReader(layout).read_consume_journal(ACT) is None


def test_reader_io_error_is_unavailable(tmp_path, monkeypatch):
    layout, _ = stage(tmp_path)
    import adapters.executor.interrupt as module

    def boom(fd, size):
        raise OSError(5, "EIO")

    monkeypatch.setattr(module, "_read_capped", boom)
    assert LocalConsumeJournalReader(layout).read_consume_journal(ACT) is None


def test_reader_rejects_an_invalid_activation_before_touching_the_filesystem(tmp_path):
    reader = LocalConsumeJournalReader(layout_for(tmp_path))
    with pytest.raises(ControlSpecError):
        reader.read_consume_journal("../etc")


def test_full_stack_with_the_real_reader_unavailable_cases_never_stop(tmp_path):
    cases = {
        "missing": None,
        "torn": journal(GOOD) + b"{",
        "no-consumed": journal([RS, RUN_END]),
        "mismatch": journal([("run-start", run_start(OTHER_INV)), *GOOD[1:]]),
    }
    for name, data in cases.items():
        sub = tmp_path / name
        sub.mkdir()
        layout = layout_for(sub)
        if data is not None:
            stage(sub, data)
        stop = Stop()
        result = InterruptProcedure(Units(), LocalConsumeJournalReader(layout), stop).run(ACT)
        assert result.end is InterruptEnd.UNAVAILABLE and stop.calls == 0, name
        if data is not None:
            path = os.path.join(ActivationPaths(layout, ACT).consume_dir, "journal")
            assert open(path, "rb").read() == data  # evidence untouched


# --- journal reader: the name and the metadata are revalidated after the read ------------


def _fds() -> set[str]:
    return set(os.listdir("/proc/self/fd"))


def _during_read(monkeypatch, mutate):
    """Run ``mutate`` once the journal bytes were read, before the reader's final checks."""
    import adapters.executor.interrupt as module

    real = module._read_capped

    def read_then_mutate(fd, size):
        data = real(fd, size)
        mutate()
        return data

    monkeypatch.setattr(module, "_read_capped", read_then_mutate)


def _replace_atomically(path: str) -> None:
    other = path + ".new"
    with open(other, "wb") as handle:
        handle.write(open(path, "rb").read())  # same size, same bytes, same owner
    os.chmod(other, 0o644)
    os.rename(other, path)


def _rewrite_in_place(path: str) -> None:
    size = os.stat(path).st_size
    with open(path, "r+b") as handle:
        handle.write(b"Z" * size)
    stamp = os.stat(path).st_mtime_ns
    os.utime(path, ns=(stamp, stamp + 1_000_000_000))  # the clock is coarse: make the change visible


def _hard_link(path: str) -> None:
    os.link(path, path + ".link")


def _unlink(path: str) -> None:
    os.unlink(path)


def _rename_away(path: str) -> None:
    os.rename(path, path + ".moved")


def _unlink_and_recreate(path: str) -> None:
    data = open(path, "rb").read()
    os.unlink(path)
    with open(path, "wb") as handle:
        handle.write(data)
    os.chmod(path, 0o644)


def _replace_with_symlink(path: str) -> None:
    os.rename(path, path + ".moved")
    os.symlink(path + ".moved", path)


FILE_DAMAGE = {
    "atomic-replacement": _replace_atomically,
    "unlink": _unlink,
    "rename-away": _rename_away,
    "unlink-and-recreate": _unlink_and_recreate,
    "replaced-by-symlink": _replace_with_symlink,
    "file-mode": lambda path: os.chmod(path, 0o600),
    "file-mode-widened": lambda path: os.chmod(path, 0o664),
    "hard-link-created": _hard_link,
    "same-size-in-place-rewrite": _rewrite_in_place,
}


@pytest.mark.parametrize("damage", sorted(FILE_DAMAGE))
def test_reader_rejects_the_journal_object_or_name_changing_during_the_read(tmp_path, monkeypatch, damage):
    layout, path = stage(tmp_path)
    _during_read(monkeypatch, lambda: FILE_DAMAGE[damage](path))
    before = _fds()
    assert LocalConsumeJournalReader(layout).read_consume_journal(ACT) is None
    assert _fds() == before  # every descriptor closed on the failure path


@pytest.mark.parametrize("mode", [0o700, 0o775, 0o555])
def test_reader_rejects_the_evidence_directory_mode_changing_during_the_read(tmp_path, monkeypatch, mode):
    layout, path = stage(tmp_path)
    directory = os.path.dirname(path)
    _during_read(monkeypatch, lambda: os.chmod(directory, mode))
    before = _fds()
    try:
        assert LocalConsumeJournalReader(layout).read_consume_journal(ACT) is None
    finally:
        os.chmod(directory, 0o755)
    assert _fds() == before


def test_reader_rejects_a_directory_renamed_or_replaced_by_a_link_while_the_file_is_unchanged(tmp_path, monkeypatch):
    layout, path = stage(tmp_path)
    directory = os.path.dirname(path)

    def swap():
        os.rename(directory, directory + "-moved")
        os.symlink(directory + "-moved", directory)  # the open file is untouched and still acceptable

    _during_read(monkeypatch, swap)
    assert LocalConsumeJournalReader(layout).read_consume_journal(ACT) is None


def test_reader_rejects_a_directory_replaced_by_one_holding_an_identical_journal(tmp_path, monkeypatch):
    layout, path = stage(tmp_path)
    directory = os.path.dirname(path)
    data = open(path, "rb").read()

    def swap():
        os.rename(directory, directory + "-old")
        os.mkdir(directory, 0o755)
        with open(path, "wb") as handle:
            handle.write(data)
        os.chmod(path, 0o644)

    _during_read(monkeypatch, swap)
    assert LocalConsumeJournalReader(layout).read_consume_journal(ACT) is None


def test_reader_without_interference_closes_everything_and_returns_the_bytes(tmp_path):
    layout, _ = stage(tmp_path)
    before = _fds()
    assert LocalConsumeJournalReader(layout).read_consume_journal(ACT) == journal(GOOD)
    assert _fds() == before


@pytest.mark.parametrize("damage", ["atomic-replacement", "file-mode", "unlink", "same-size-in-place-rewrite"])
def test_full_stack_a_damaged_observation_launches_nothing_and_changes_nothing(tmp_path, monkeypatch, damage):
    layout, path = stage(tmp_path)
    _during_read(monkeypatch, lambda: FILE_DAMAGE[damage](path))
    units, stop = Units(), Stop()
    journals = LocalConsumeJournalReader(layout)
    result = InterruptProcedure(units, journals, stop).run(ACT)
    assert (result.end, result.reason) == (InterruptEnd.UNAVAILABLE, "journal-unavailable")
    assert result.exit_code == 30 and stop.calls == 0 and len(units.calls) == 1
