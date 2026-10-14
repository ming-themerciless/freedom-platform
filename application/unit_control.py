"""Application-owned boundary for the Route 3 manager/Polkit interface intents.

Seven narrow intents, no more (interface contract §2): DI-1 unit-state read,
DI-2 create holder unit, DI-3 create backstop timer and service, DI-4 disarm
backstop timer, DI-5 Polkit decision, DI-6 authorization subject and DI-S stop
of exactly ``rp11-capture-pass-a.service``.

This module owns the vocabulary callers see: the request value objects, the
three-way result (``ControlOk`` / ``ControlRefused`` / ``ControlError``) and the
protocols an adapter must satisfy. It contains no D-Bus, ``/proc`` or systemd
detail. It is deliberately not a generic unit-management API: every name that
reaches the manager is derived here from a validated activation id or is the one
fixed capture unit, and no request can name an executable, a role or an argument:
the adapter derives the three accepted role commands from validated identifiers.

The adapter is inactive in production configuration; nothing imports it from a
runtime path.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, Protocol, TypeVar

T = TypeVar("T")

CAPTURE_UNIT = "rp11-capture-pass-a.service"

# Accepted RT1.CQ0.5 grammar. Anything else is not an activation id.
_ACTIVATION_ID = re.compile(r"^rp11-act-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$")

# The A-2 identity carried by every role command: lowercase hex SHA-256.
_SHA256 = re.compile(r"^[0-9a-f]{64}$")

MAX_SECONDS = 7 * 24 * 3600


class ControlSpecError(ValueError):
    """A request value object was constructed with an invalid field."""


def validate_activation_id(activation_id: str) -> str:
    if not isinstance(activation_id, str) or not _ACTIVATION_ID.fullmatch(activation_id):
        raise ControlSpecError("activation id does not match the accepted grammar")
    return activation_id


def validate_sha256(value: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ControlSpecError("artifact identity must be a lowercase hex SHA-256")
    return value


def holder_unit_name(activation_id: str) -> str:
    return f"{validate_activation_id(activation_id)}.service"


def backstop_timer_name(activation_id: str) -> str:
    return f"{validate_activation_id(activation_id)}-backstop.timer"


def backstop_service_name(activation_id: str) -> str:
    return f"{validate_activation_id(activation_id)}-backstop.service"


_BACKSTOP_UNIT = re.compile(
    r"^(rp11-act-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8})(-backstop\.(timer|service)|\.service)$"
)


def validate_unit_name(unit: str) -> str:
    """Admit only the capture unit and units derived from a valid activation id."""
    if unit == CAPTURE_UNIT or (isinstance(unit, str) and _BACKSTOP_UNIT.fullmatch(unit)):
        return unit
    raise ControlSpecError("unit name is not one of the permitted Route 3 units")


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------


class RefusalReason(str, Enum):
    EXISTS = "exists"
    INVALID_REQUEST = "invalid-request"
    NOT_AUTHORIZED = "not-authorized"
    NOT_LOADED = "not-loaded"


@dataclass(frozen=True)
class ControlOk(Generic[T]):
    value: T


@dataclass(frozen=True)
class ControlRefused:
    reason: RefusalReason


@dataclass(frozen=True)
class ControlError:
    """Anything not a proven success or a narrow, pre-mutation refusal.

    ``effect_not_confirmed`` is true for every error reported after a mutating
    call was sent: the request may or may not have had its effect, and the caller
    must not retry silently. It is false only for failures raised before any
    mutating call left the process.
    """

    kind: str
    detail: str = ""
    effect_not_confirmed: bool = False

    def __str__(self) -> str:
        text = f"error({self.kind})"
        if self.effect_not_confirmed:
            text += ": effect not confirmed"
        return text


ControlResult = ControlOk[T] | ControlRefused | ControlError


# ---------------------------------------------------------------------------
# Request value objects
# ---------------------------------------------------------------------------


def _seconds(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= MAX_SECONDS:
        raise ControlSpecError(f"{name} must be an integer 1..{MAX_SECONDS}")
    return value


@dataclass(frozen=True)
class HolderSpec:
    """DI-2: the transient holder ``<id>.service`` (SA1.OP.2).

    Carries only the values the accepted literal leaves variable. The adapter
    derives both commands from them — ``ExecStart`` is the ``hold`` role and
    ``ExecStopPost`` the ``deact … stop-post`` role of the controlled artifact —
    so no executable, role or argument can be chosen by a caller.
    """

    activation_id: str
    artifact_sha256: str
    runtime_max_seconds: int
    timeout_stop_seconds: int

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> HolderSpec:
        validate_activation_id(self.activation_id)
        validate_sha256(self.artifact_sha256)
        _seconds("runtime_max_seconds", self.runtime_max_seconds)
        _seconds("timeout_stop_seconds", self.timeout_stop_seconds)
        return self

    @property
    def unit_name(self) -> str:
        return holder_unit_name(self.activation_id)


@dataclass(frozen=True)
class BackstopSpec:
    """DI-3: ``<id>-backstop.timer`` plus ``<id>-backstop.service`` (RT2.AK1.2).

    ``interval_seconds`` is R (``OnActiveSec`` and ``OnUnitActiveSec``);
    ``runtime_max_seconds`` is S_b and ``timeout_stop_seconds`` is S. D-10: the
    backstop service never carries ``TimeoutStartUSec``. Its ``ExecStart`` is the
    ``backstop`` role, derived by the adapter from the two identifiers.
    """

    activation_id: str
    artifact_sha256: str
    interval_seconds: int
    runtime_max_seconds: int
    timeout_stop_seconds: int

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> BackstopSpec:
        validate_activation_id(self.activation_id)
        validate_sha256(self.artifact_sha256)
        _seconds("interval_seconds", self.interval_seconds)
        _seconds("runtime_max_seconds", self.runtime_max_seconds)
        _seconds("timeout_stop_seconds", self.timeout_stop_seconds)
        return self

    @property
    def timer_name(self) -> str:
        return backstop_timer_name(self.activation_id)

    @property
    def service_name(self) -> str:
        return backstop_service_name(self.activation_id)


class UnitProperty(str, Enum):
    """The eight DI-1 properties (§3.1). No other property is readable."""

    ACTIVE_STATE = "ActiveState"
    INVOCATION_ID = "InvocationID"
    INACTIVE_ENTER_TIMESTAMP_MONOTONIC = "InactiveEnterTimestampMonotonic"
    JOB = "Job"
    LOAD_STATE = "LoadState"
    RESULT = "Result"
    EXEC_MAIN_START_TIMESTAMP_MONOTONIC = "ExecMainStartTimestampMonotonic"
    TIMEOUT_START_USEC = "TimeoutStartUSec"


# Typed values: ``str`` (state strings; ``InvocationID`` as lowercase hex, empty
# when null), ``int`` (timestamps and USec; ``Job`` as the job id, 0 for none).
PropertyValue = str | int
UnitProperties = Mapping[UnitProperty, PropertyValue]


@dataclass(frozen=True)
class JobCompletion:
    """A mutating call whose ``JobRemoved`` result was ``done``.

    ``observed`` is the post-completion state read — diagnostic context only. It
    is never the basis of the result and is ``None`` when the read failed.
    """

    job_path: str
    unit: str
    observed: UnitProperties | None = field(default=None, compare=False)


@dataclass(frozen=True)
class TimerObservation:
    """DI-3 post-completion read of the backstop timer (D-4 O-C).

    ``active_state`` and ``load_state`` are the timer's ``Unit`` properties,
    ``triggers`` its ``Unit.Triggers`` and ``unit`` its ``Timer.Unit``: both
    should name the auxiliary backstop service. Diagnostic only.
    """

    active_state: str
    load_state: str
    triggers: tuple[str, ...]
    unit: str


@dataclass(frozen=True)
class BackstopCompletion:
    """DI-3 whose timer start job ended ``done``.

    ``observed`` never decides the result and is ``None`` when the read failed.
    """

    job_path: str
    timer: str
    observed: TimerObservation | None = field(default=None, compare=False)


class StopOutcome(str, Enum):
    # A completed stop is not claimed to be causal: the same ``done`` is reported
    # for stopping an active unit and for the no-op on an inactive one (IO-1).
    STOPPED = "stopped"


@dataclass(frozen=True)
class StopCompletion:
    outcome: StopOutcome
    completion: JobCompletion


# ---------------------------------------------------------------------------
# DI-5 / DI-6
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProcessSubject:
    """``unix-process`` Polkit subject (DI-6).

    Identified by PID, ``/proc/<pid>/stat`` field 22 and real uid. Known residual
    (A-13.4): this is not race-free process identity.
    """

    pid: int
    start_time: int
    uid: int

    def __post_init__(self) -> None:
        # Exact ints only: ``True``, ``1.0`` or an int subclass would be encoded
        # as something other than the value the caller appears to have meant.
        for name in ("pid", "start_time", "uid"):
            if type(getattr(self, name)) is not int:
                raise ControlSpecError(f"{name} must be an int")
        if not 1 <= self.pid <= 0xFFFFFFFF:
            raise ControlSpecError("pid outside D-Bus uint32")
        if not 1 <= self.start_time <= 0xFFFFFFFFFFFFFFFF:
            raise ControlSpecError("start time outside 1..uint64")
        if not 0 <= self.uid <= 0x7FFFFFFF:
            raise ControlSpecError("uid outside D-Bus int32")


class UnitVerb(str, Enum):
    START = "start"
    STOP = "stop"


@dataclass(frozen=True)
class PolkitAuthorized:
    pass


@dataclass(frozen=True)
class PolkitNotAuthorized:
    """Denial or challenge. A challenge is never an error and never authorized."""

    challenge: bool = False


PolkitOutcome = PolkitAuthorized | PolkitNotAuthorized | ControlError


# ---------------------------------------------------------------------------
# Protocols the adapter satisfies
# ---------------------------------------------------------------------------


class UnitControl(Protocol):
    def read_unit(
        self, unit: str, properties: tuple[UnitProperty, ...]
    ) -> ControlResult[UnitProperties]: ...

    def create_holder(self, spec: HolderSpec) -> ControlResult[JobCompletion]: ...

    def create_backstop(self, spec: BackstopSpec) -> ControlResult[BackstopCompletion]: ...

    def disarm_backstop(self, activation_id: str) -> ControlResult[StopCompletion]: ...

    def stop_capture_unit(self) -> ControlResult[StopCompletion]: ...


class PolkitAuthority(Protocol):
    def check(self, subject: ProcessSubject, verb: UnitVerb) -> PolkitOutcome: ...


class SubjectSource(Protocol):
    def subject_for_pid(self, pid: int) -> ControlResult[ProcessSubject]: ...
