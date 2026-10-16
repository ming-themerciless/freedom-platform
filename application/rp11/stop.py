"""SA-2: stop the fixed capture unit through the narrow DI-S boundary."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from application.unit_control import (
    CAPTURE_UNIT,
    ControlError,
    ControlOk,
    ControlRefused,
    JobCompletion,
    RefusalReason,
    StopCompletion,
    StopOutcome,
    UnitControl,
)

#: The accepted systemd job object-path shape (ASCII digits only; ``fullmatch``).
_JOB_PATH = re.compile(r"/org/freedesktop/systemd1/job/[0-9]+")


def _is_stop_of_the_capture_unit(value: object) -> bool:
    """True only for a structurally valid ``StopCompletion`` of the fixed capture unit.

    Exact types and exact ``str`` fields are required *before* any comparison, so a
    caller-controlled ``__eq__``/``__bool__`` or subclass attribute is never invoked.
    """
    if type(value) is not StopCompletion or value.outcome is not StopOutcome.STOPPED:
        return False
    completion = value.completion
    if type(completion) is not JobCompletion:
        return False
    unit, job_path = completion.unit, completion.job_path
    return (
        type(unit) is str
        and type(job_path) is str
        and unit == CAPTURE_UNIT
        and _JOB_PATH.fullmatch(job_path) is not None
    )


def _is_well_formed_error(value: object) -> bool:
    """True only for an exact ``ControlError`` whose fields have their declared exact types."""
    return (
        type(value) is ControlError
        and type(value.kind) is str
        and type(value.detail) is str
        and type(value.effect_not_confirmed) is bool
    )


class StopEnd(str, Enum):
    STOPPED = "stopped"
    REFUSED = "refused"
    ERROR = "error"


@dataclass(frozen=True)
class StopResult:
    end: StopEnd
    detail: str = ""
    effect_not_confirmed: bool = False

    @property
    def exit_code(self) -> int:
        if self.end is StopEnd.STOPPED:
            return 0
        if self.end is StopEnd.REFUSED:
            return 20
        return 22 if self.effect_not_confirmed else 21


class StopProcedure:
    """One DI-S call, with no retry after any result or exception.

    The executor has already established OC-1..OC-3; nothing is read here.
    """

    def __init__(self, units: UnitControl) -> None:
        self._units = units

    def run(self) -> StopResult:
        result = self._units.stop_capture_unit()
        if isinstance(result, ControlOk):
            if _is_stop_of_the_capture_unit(result.value):
                return StopResult(StopEnd.STOPPED)
            # The one call was made; a malformed success is not proof of effect.
            return StopResult(StopEnd.ERROR, "malformed-success", effect_not_confirmed=True)
        if isinstance(result, ControlRefused):
            if not isinstance(result.reason, RefusalReason):
                # Malformed boundary data is never echoed and never a typed refusal.
                raise TypeError("DI-S returned a malformed refusal")
            return StopResult(StopEnd.REFUSED, result.reason.value)
        if isinstance(result, ControlError):
            if not _is_well_formed_error(result):
                # Malformed certainty must never select exit 21 or 22 and is never evaluated.
                raise TypeError("DI-S returned a malformed error")
            return StopResult(StopEnd.ERROR, result.kind, result.effect_not_confirmed)
        raise TypeError("DI-S returned an unknown result")
