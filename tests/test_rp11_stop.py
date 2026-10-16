"""SA-2: the static ``stop`` role makes exactly one DI-S call and returns its typed result."""

from __future__ import annotations

from enum import Enum

import pytest

from adapters.rp11.stop import EX_INTERNAL, run_stop
from application.rp11.stop import StopEnd, StopProcedure
from application.unit_control import (
    CAPTURE_UNIT,
    ControlError,
    ControlOk,
    ControlRefused,
    JobCompletion,
    RefusalReason,
    StopCompletion,
    StopOutcome,
)

JOB = "/org/freedesktop/systemd1/job/1234"
VALID = ControlOk(StopCompletion(StopOutcome.STOPPED, JobCompletion(JOB, CAPTURE_UNIT)))


class Units:
    """Records every call; any other boundary method would be an AttributeError."""

    def __init__(self, result=None, error: Exception | None = None):
        self.result, self.error, self.calls = result, error, 0

    def stop_capture_unit(self):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


def test_stop_makes_exactly_one_dis_call_and_returns_stopped(capsys):
    units = Units(VALID)
    assert run_stop(units=units) == 0
    assert capsys.readouterr().err == "rp11-stop stopped\n"
    assert units.calls == 1


def test_procedure_maps_the_valid_completion_to_stopped():
    outcome = StopProcedure(Units(VALID)).run()
    assert outcome.end is StopEnd.STOPPED and outcome.exit_code == 0


@pytest.mark.parametrize("reason", list(RefusalReason))
def test_every_typed_refusal_is_reported_by_value_and_not_retried(reason, capsys):
    units = Units(ControlRefused(reason))
    assert run_stop(units=units) == 20
    assert capsys.readouterr().err == f"rp11-stop refused {reason.value}\n"
    assert units.calls == 1


def test_unconfirmed_error_is_exit_22_with_a_fixed_line_and_no_retry(capsys):
    units = Units(ControlError("arbitrary-adapter-detail", "secret-looking-detail", True))
    assert run_stop(units=units) == 22
    assert capsys.readouterr().err == "rp11-stop error effect-not-confirmed\n"
    assert units.calls == 1


@pytest.mark.parametrize("kind", ["connect", "subscribe", "timeout", "disconnect", "reply-lost", "job-failed"])
def test_pre_send_and_post_send_errors_are_distinguished_and_never_retried(kind, capsys):
    pre = Units(ControlError(kind, "/run/dbus/secret", False))
    assert run_stop(units=pre) == 21
    assert capsys.readouterr().err == "rp11-stop error effect-not-sent\n"
    post = Units(ControlError(kind, "/run/dbus/secret", True))
    assert run_stop(units=post) == 22
    assert capsys.readouterr().err == "rp11-stop error effect-not-confirmed\n"
    assert pre.calls == post.calls == 1


def test_an_exception_is_internal_error_without_text_or_retry(capsys):
    units = Units(error=RuntimeError("must not be printed /secret"))
    assert run_stop(units=units) == EX_INTERNAL == 70
    assert capsys.readouterr().err == "rp11-stop internal-error\n"
    assert units.calls == 1


def test_an_unknown_result_fails_closed_without_retry(capsys):
    units = Units(object())
    assert run_stop(units=units) == EX_INTERNAL
    assert capsys.readouterr().err == "rp11-stop internal-error\n"
    assert units.calls == 1


def test_an_unusable_manager_boundary_is_a_typed_pre_send_error_without_detail(capsys):
    def connector():
        raise OSError("/run/dbus/secret-path")

    assert run_stop(connector=connector) == 21
    assert capsys.readouterr().err == "rp11-stop error effect-not-sent\n"


def test_run_stop_accepts_no_caller_selected_target():
    import inspect

    assert set(inspect.signature(run_stop).parameters) == {"units", "connector"}


# A malformed apparent success is boundary data, never ``stopped`` (the SA-1 lesson).
OK_COMPLETION = JobCompletion(JOB, CAPTURE_UNIT)


class _OtherCompletion:
    unit = CAPTURE_UNIT
    job_path = JOB


class _OtherStop:
    outcome = StopOutcome.STOPPED
    completion = OK_COMPLETION


def _stop(completion, outcome=StopOutcome.STOPPED):
    return ControlOk(StopCompletion(outcome, completion))


MALFORMED_SUCCESS = [
    pytest.param(ControlOk(None), id="none"),
    pytest.param(ControlOk("stopped"), id="string"),
    pytest.param(ControlOk(OK_COMPLETION), id="bare-jobcompletion"),
    pytest.param(ControlOk(_OtherStop()), id="non-stopcompletion"),
    pytest.param(_stop(None), id="missing-completion"),
    pytest.param(_stop(_OtherCompletion()), id="non-jobcompletion"),
    pytest.param(_stop(OK_COMPLETION, outcome="stopped"), id="outcome-is-a-string"),
    pytest.param(_stop(OK_COMPLETION, outcome=None), id="outcome-none"),
    pytest.param(_stop(JobCompletion(JOB, "rp11-act-20261015T120000Z-0123abcd.service")), id="other-unit"),
    pytest.param(_stop(JobCompletion(JOB, "ssh.service")), id="arbitrary-unit"),
    pytest.param(_stop(JobCompletion(JOB, None)), id="unit-none"),
    pytest.param(_stop(JobCompletion("", CAPTURE_UNIT)), id="empty-path"),
    pytest.param(_stop(JobCompletion("/job/1", CAPTURE_UNIT)), id="short-path"),
    pytest.param(_stop(JobCompletion("/org/freedesktop/systemd1/job/", CAPTURE_UNIT)), id="no-id"),
    pytest.param(_stop(JobCompletion("/org/freedesktop/systemd1/job/12x", CAPTURE_UNIT)), id="non-digit"),
    pytest.param(_stop(JobCompletion("/org/freedesktop/systemd1/job/١", CAPTURE_UNIT)), id="arabic-digit"),
    pytest.param(_stop(JobCompletion(JOB + "\n", CAPTURE_UNIT)), id="trailing-newline"),
    pytest.param(_stop(JobCompletion("/etc/passwd", CAPTURE_UNIT)), id="arbitrary-path"),
    pytest.param(_stop(JobCompletion(None, CAPTURE_UNIT)), id="path-none"),
]


@pytest.mark.parametrize("result", MALFORMED_SUCCESS)
def test_a_malformed_success_payload_is_effect_not_confirmed_without_retry(result, capsys):
    units = Units(result)
    assert run_stop(units=units) == 22
    err = capsys.readouterr().err
    assert err == "rp11-stop error effect-not-confirmed\n"
    assert units.calls == 1


SENSITIVE = "/sensitive/caller/value"


class _ForeignReason(Enum):
    NOT_LOADED = "not-loaded"


class _Reasonish:
    value = SENSITIVE


MALFORMED_REFUSAL = [
    pytest.param(_Reasonish(), id="object-with-sensitive-value"),
    pytest.param("not-loaded", id="plain-string-equal-to-valid-spelling"),
    pytest.param(_ForeignReason.NOT_LOADED, id="foreign-enum-with-valid-spelling"),
    pytest.param(None, id="none"),
]


@pytest.mark.parametrize("reason", MALFORMED_REFUSAL)
def test_a_malformed_refusal_reason_is_internal_error_without_output_or_retry(reason, capsys):
    units = Units(ControlRefused(reason))
    assert run_stop(units=units) == EX_INTERNAL == 70
    captured = capsys.readouterr()
    assert captured.err == "rp11-stop internal-error\n"
    assert captured.out == ""
    assert SENSITIVE not in captured.err + captured.out
    assert units.calls == 1


def test_a_valid_completion_for_the_fixed_capture_unit_is_stopped(capsys):
    units = Units(VALID)
    assert run_stop(units=units) == 0
    assert capsys.readouterr().err == "rp11-stop stopped\n"
    assert units.calls == 1


def test_the_observed_state_never_changes_the_result(capsys):
    """A completed stop is ``stopped`` whether the unit was active, inactive or failed."""
    for observed in (None, {"ActiveState": "inactive"}, {"ActiveState": "failed"}, {"ActiveState": "active"}):
        units = Units(ControlOk(StopCompletion(StopOutcome.STOPPED, JobCompletion(JOB, CAPTURE_UNIT, observed))))
        assert run_stop(units=units) == 0
        assert capsys.readouterr().err == "rp11-stop stopped\n"


def test_the_role_reads_no_state_and_creates_nothing():
    """No DI-1 read, journal/record access, child, signal or wait at the application boundary."""
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    for name in ("application/rp11/stop.py", "adapters/rp11/stop.py"):
        source = (root / name).read_text()
        for forbidden in (
            "read_unit", "create_holder", "create_backstop", "disarm_backstop", "subprocess", "os.kill",
            "signal", "time.sleep", "open(", "Path(", "os.environ", "getenv", "journal", "records",
        ):
            assert not re.search(re.escape(forbidden), source), (name, forbidden)


# ---- second remediation: spoofable equality and malformed error certainty ----------------


class _AlwaysEqual:
    """Compares equal to anything; its hook must never decide the result."""

    hook_calls = 0

    def __eq__(self, other):
        type(self).hook_calls += 1
        return True

    __hash__ = None


class _SensitiveEq:
    def __eq__(self, other):
        raise RuntimeError(SENSITIVE)

    __hash__ = None


class _StrSubclassEq(str):
    def __eq__(self, other):
        return True

    __hash__ = str.__hash__


class _StopSub(StopCompletion):
    pass


class _JobSub(JobCompletion):
    pass


def _unit_spoof(unit):
    return _stop(JobCompletion(JOB, unit))


SPOOFED_SUCCESS = [
    pytest.param(_unit_spoof(_AlwaysEqual()), id="eq-true-object"),
    pytest.param(_unit_spoof(_SensitiveEq()), id="raising-eq-object"),
    pytest.param(_unit_spoof(_StrSubclassEq(CAPTURE_UNIT)), id="str-subclass-correct-value"),
    pytest.param(_unit_spoof(_StrSubclassEq("other.service")), id="str-subclass-eq-true"),
    pytest.param(ControlOk(_StopSub(StopOutcome.STOPPED, OK_COMPLETION)), id="stopcompletion-subclass"),
    pytest.param(_stop(_JobSub(JOB, CAPTURE_UNIT)), id="jobcompletion-subclass"),
    pytest.param(_stop(JobCompletion(_StrSubclassEq(JOB), CAPTURE_UNIT)), id="path-str-subclass"),
]


@pytest.mark.parametrize("result", SPOOFED_SUCCESS)
def test_a_spoofed_success_is_effect_not_confirmed_and_its_hooks_are_not_needed(result, capsys):
    _AlwaysEqual.hook_calls = 0
    units = Units(result)
    assert run_stop(units=units) == 22
    captured = capsys.readouterr()
    assert captured.err == "rp11-stop error effect-not-confirmed\n"
    assert captured.out == ""
    assert SENSITIVE not in captured.err
    assert _AlwaysEqual.hook_calls == 0
    assert units.calls == 1


class _BoolRaises:
    def __bool__(self):
        raise RuntimeError(SENSITIVE)


class _ErrSub(ControlError):
    pass


def _err(kind="job-failed", detail="", certainty=False):
    return ControlError(kind, detail, certainty)


MALFORMED_ERROR = [
    pytest.param(_err(certainty=None), id="certainty-none"),
    pytest.param(_err(certainty=0), id="certainty-0"),
    pytest.param(_err(certainty=1), id="certainty-1"),
    pytest.param(_err(certainty=""), id="certainty-falsey-string"),
    pytest.param(_err(certainty="yes"), id="certainty-truthy-string"),
    pytest.param(_err(certainty=_BoolRaises()), id="certainty-raising-bool"),
    pytest.param(_err(kind=None), id="kind-none"),
    pytest.param(_err(kind=SENSITIVE.encode()), id="kind-bytes"),
    pytest.param(_err(kind=_StrSubclassEq("job-failed")), id="kind-str-subclass"),
    pytest.param(_err(detail=None), id="detail-none"),
    pytest.param(_err(detail=_BoolRaises()), id="detail-object"),
    pytest.param(_ErrSub("job-failed", "", True), id="controlerror-subclass"),
]


@pytest.mark.parametrize("result", MALFORMED_ERROR)
def test_a_malformed_error_is_internal_error_without_output_or_retry(result, capsys):
    units = Units(result)
    assert run_stop(units=units) == EX_INTERNAL == 70
    captured = capsys.readouterr()
    assert captured.err == "rp11-stop internal-error\n"
    assert captured.out == ""
    assert SENSITIVE not in captured.err + captured.out
    assert units.calls == 1


@pytest.mark.parametrize(("certainty", "code", "line"), [
    (False, 21, "effect-not-sent"),
    (True, 22, "effect-not-confirmed"),
])
def test_exact_boolean_certainty_keeps_its_accepted_mapping(certainty, code, line, capsys):
    units = Units(_err(certainty=certainty))
    assert run_stop(units=units) == code
    assert capsys.readouterr().err == f"rp11-stop error {line}\n"
    assert units.calls == 1
