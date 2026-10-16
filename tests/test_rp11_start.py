from __future__ import annotations

from adapters.rp11.start import EX_INTERNAL, run_start
from application.rp11.start import StartEnd, StartProcedure
from application.unit_control import (
    ControlError,
    ControlOk,
    ControlRefused,
    HolderSpec,
    JobCompletion,
    RefusalReason,
)

ACT = "rp11-act-20261015T120000Z-0123abcd"
A2 = "a" * 64
SPEC = HolderSpec(ACT, A2, 900, 60)
JOB = "/org/freedesktop/systemd1/job/1234"


class Units:
    def __init__(self, result=None, error: Exception | None = None):
        self.result, self.error, self.calls = result, error, []

    def create_holder(self, spec):
        self.calls.append(spec)
        if self.error:
            raise self.error
        return self.result


def test_start_makes_exactly_one_di2_call_and_returns_started():
    units = Units(ControlOk(JobCompletion(JOB, SPEC.unit_name)))
    outcome = StartProcedure(units).run(SPEC)
    assert outcome.end is StartEnd.STARTED and outcome.exit_code == 0
    assert units.calls == [SPEC]


def test_refusal_is_typed_and_never_retried():
    units = Units(ControlRefused(RefusalReason.EXISTS))
    outcome = StartProcedure(units).run(SPEC)
    assert (outcome.end, outcome.detail, outcome.exit_code) == (StartEnd.REFUSED, "exists", 20)
    assert units.calls == [SPEC]


def test_unconfirmed_error_is_typed_and_never_retried():
    units = Units(ControlError("reply-lost", effect_not_confirmed=True))
    outcome = StartProcedure(units).run(SPEC)
    assert (outcome.end, outcome.effect_not_confirmed, outcome.exit_code) == (StartEnd.ERROR, True, 22)
    assert units.calls == [SPEC]


def test_composition_root_uses_fixed_safe_diagnostics(capsys):
    units = Units(ControlError("arbitrary-adapter-detail", "secret-looking-detail", True))
    assert run_start(ACT, A2, 900, 60, units=units) == 22
    assert capsys.readouterr().err == "rp11-start error effect-not-confirmed\n"


def test_composition_root_reports_only_the_typed_refusal(capsys):
    units = Units(ControlRefused(RefusalReason.EXISTS))
    assert run_start(ACT, A2, 900, 60, units=units) == 20
    assert capsys.readouterr().err == "rp11-start refused exists\n"


def test_composition_root_maps_pre_send_error_and_exception_without_retry(capsys):
    units = Units(ControlError("connect", effect_not_confirmed=False))
    assert run_start(ACT, A2, 900, 60, units=units) == 21
    assert capsys.readouterr().err == "rp11-start error effect-not-sent\n"
    broken = Units(error=RuntimeError("must not be printed"))
    assert run_start(ACT, A2, 900, 60, units=broken) == EX_INTERNAL
    assert capsys.readouterr().err == "rp11-start internal-error\n"
    assert broken.calls == [SPEC]


def test_unknown_di2_result_fails_closed_without_retry(capsys):
    units = Units(object())
    assert run_start(ACT, A2, 900, 60, units=units) == EX_INTERNAL
    assert capsys.readouterr().err == "rp11-start internal-error\n"
    assert units.calls == [SPEC]


import pytest

from application.unit_control import ControlSpecError


@pytest.mark.parametrize(
    "operands",
    [
        ("rp11-act-x", A2, 900, 60),
        (ACT, A2.upper(), 900, 60),
        (ACT, A2, 0, 60),
        (ACT, A2, 900, 604801),
        (ACT, A2, True, 60),
        (ACT, A2, "900", 60),
        (ACT, A2, 900.0, 60),
        (ACT, A2, None, 60),
        (ACT, None, 900, 60),
    ],
)
def test_invalid_operands_are_refused_before_the_bus_is_opened(operands, capsys):
    opened = []
    assert run_start(*operands, connector=lambda: opened.append(1)) == EX_INTERNAL
    assert opened == []
    assert capsys.readouterr().err == "rp11-start internal-error\n"
    with pytest.raises(ControlSpecError):
        HolderSpec(*operands)


@pytest.mark.parametrize("reason", list(RefusalReason))
def test_every_typed_refusal_is_reported_by_value_and_not_retried(reason, capsys):
    units = Units(ControlRefused(reason))
    assert run_start(ACT, A2, 900, 60, units=units) == 20
    assert capsys.readouterr().err == f"rp11-start refused {reason.value}\n"
    assert units.calls == [SPEC]


def test_an_unusable_manager_boundary_is_a_typed_pre_send_error_without_detail(capsys):
    def connector():
        raise OSError("/run/dbus/secret-path")

    assert run_start(ACT, A2, 900, 60, connector=connector) == 21
    assert capsys.readouterr().err == "rp11-start error effect-not-sent\n"


# Review finding 1: the role enforces the holder-duration contract itself.
LEASE_OK, LEASE_BAD = (61, 86400), (0, 1, 60, 86401, 604800)
STOP_OK, STOP_BAD = (60, 600), (0, 1, 59, 601, 604800)


@pytest.mark.parametrize("lease,stop", [(61, 60), (86400, 600), (900, 60), (61, 600), (86400, 60)])
def test_both_ends_of_each_holder_duration_range_are_accepted(lease, stop):
    units = Units(ControlOk(JobCompletion(JOB, SPEC.unit_name)))
    assert run_start(ACT, A2, lease, stop, units=units) == 0
    assert [(c.runtime_max_seconds, c.timeout_stop_seconds) for c in units.calls] == [(lease, stop)]


@pytest.mark.parametrize(
    "lease,stop",
    [(v, 60) for v in LEASE_BAD] + [(900, v) for v in STOP_BAD] + [(604800, 1), (1, 604800)],
)
def test_a_duration_outside_the_holder_contract_opens_no_bus_and_creates_no_unit(lease, stop, capsys):
    opened, units = [], Units(ControlOk(JobCompletion(JOB, SPEC.unit_name)))
    assert run_start(ACT, A2, lease, stop, units=units, connector=lambda: opened.append(1)) == EX_INTERNAL
    assert opened == [] and units.calls == []
    assert capsys.readouterr().err == "rp11-start internal-error\n"


# Second review: a malformed apparent success must never become ``started``.
class _Other:
    unit = SPEC.unit_name
    job_path = JOB


MALFORMED_SUCCESS = [
    pytest.param(ControlOk(None), id="none"),
    pytest.param(ControlOk(_Other()), id="non-jobcompletion"),
    pytest.param(ControlOk(JobCompletion(JOB, "rp11-act-other.service")), id="other-unit"),
    pytest.param(ControlOk(JobCompletion("", SPEC.unit_name)), id="empty-path"),
    pytest.param(ControlOk(JobCompletion("/job/1", SPEC.unit_name)), id="short-path"),
    pytest.param(ControlOk(JobCompletion("/org/freedesktop/systemd1/job/", SPEC.unit_name)), id="no-id"),
    pytest.param(ControlOk(JobCompletion("/org/freedesktop/systemd1/job/12x", SPEC.unit_name)), id="non-digit"),
    pytest.param(ControlOk(JobCompletion("/org/freedesktop/systemd1/job/\u0661", SPEC.unit_name)), id="arabic-digit"),
    pytest.param(ControlOk(JobCompletion(JOB + "\n", SPEC.unit_name)), id="trailing-newline"),
    pytest.param(ControlOk(JobCompletion(None, SPEC.unit_name)), id="path-none"),
    pytest.param(ControlOk(JobCompletion(JOB, None)), id="unit-none"),
]


@pytest.mark.parametrize("result", MALFORMED_SUCCESS)
def test_a_malformed_success_payload_is_effect_not_confirmed_without_retry(result, capsys):
    units = Units(result)
    assert run_start(ACT, A2, 900, 60, units=units) == 22
    assert capsys.readouterr().err == "rp11-start error effect-not-confirmed\n"
    assert units.calls == [SPEC]


def test_a_valid_completion_for_the_requested_holder_is_started(capsys):
    units = Units(ControlOk(JobCompletion(JOB, SPEC.unit_name)))
    assert run_start(ACT, A2, 900, 60, units=units) == 0
    assert capsys.readouterr().err == "rp11-start started\n"
    assert units.calls == [SPEC]
