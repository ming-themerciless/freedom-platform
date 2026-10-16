"""SA-1: create the validated Route 3 holder through the narrow DI-2 boundary."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from application.unit_control import (
    ControlError,
    ControlOk,
    ControlRefused,
    ControlSpecError,
    HolderSpec,
    JobCompletion,
    UnitControl,
)


#: SA1.OP.1..3: the absolute holder-duration ranges knowable from the four fixed
#: operands. ``start_window_s < lease_s`` is owned by the authority that holds
#: both values and is not re-derived here. Deliberately not the shared
#: ``HolderSpec`` bound (1..604800), which the backstop fields also use.
LEASE_SECONDS = (61, 86400)
STOP_TIMEOUT_SECONDS = (60, 600)


def validate_start_durations(lease_seconds: int, stop_timeout_seconds: int) -> None:
    """Refuse a duration outside the controlled holder contract (``ControlSpecError``)."""
    for name, value, (low, high) in (
        ("lease_seconds", lease_seconds, LEASE_SECONDS),
        ("stop_timeout_seconds", stop_timeout_seconds, STOP_TIMEOUT_SECONDS),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
            raise ControlSpecError(f"{name} must be an integer {low}..{high}")


#: The accepted systemd job object-path shape (ASCII digits only; ``fullmatch``).
_JOB_PATH = re.compile(r"/org/freedesktop/systemd1/job/[0-9]+")


def _is_completion_for(value: object, spec: HolderSpec) -> bool:
    """True only for a structurally valid ``JobCompletion`` of the requested holder."""
    return (
        isinstance(value, JobCompletion)
        and value.unit == spec.unit_name
        and isinstance(value.job_path, str)
        and _JOB_PATH.fullmatch(value.job_path) is not None
    )


class StartEnd(str, Enum):
    STARTED = "started"
    REFUSED = "refused"
    ERROR = "error"


@dataclass(frozen=True)
class StartOutcome:
    end: StartEnd
    detail: str = ""
    effect_not_confirmed: bool = False

    @property
    def exit_code(self) -> int:
        if self.end is StartEnd.STARTED:
            return 0
        if self.end is StartEnd.REFUSED:
            return 20
        return 22 if self.effect_not_confirmed else 21


class StartProcedure:
    """One DI-2 call, with no retry after any result or exception."""

    def __init__(self, units: UnitControl) -> None:
        self._units = units

    def run(self, spec: HolderSpec) -> StartOutcome:
        result = self._units.create_holder(spec)
        if isinstance(result, ControlOk):
            if _is_completion_for(result.value, spec):
                return StartOutcome(StartEnd.STARTED)
            # The one call was made; a malformed success is not proof of effect.
            return StartOutcome(StartEnd.ERROR, "malformed-success", effect_not_confirmed=True)
        if isinstance(result, ControlRefused):
            return StartOutcome(StartEnd.REFUSED, result.reason.value)
        if isinstance(result, ControlError):
            return StartOutcome(StartEnd.ERROR, result.kind, result.effect_not_confirmed)
        raise TypeError("DI-2 returned an unknown result")
