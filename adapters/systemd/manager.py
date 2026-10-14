"""systemd manager adapter: DI-1, DI-2, DI-3, DI-4 and DI-S over the system bus.

Implements ``application.unit_control.UnitControl``. Decisions pinned here (all
reversible, each covered by a test):

* one fresh bus connection per operation — closing it drops the ``Subscribe()``
  reference and the signal match, so a lost connection never leaves state behind;
* the ``JobRemoved`` match and ``Manager.Subscribe()`` are installed before any
  mutating call (D-4), narrowed to the expected unit by ``arg2``;
* job mode is ``"fail"`` for every mutation: never replace or flush a queued job
  that belongs to someone else, so a conflict surfaces as an error;
* a mutating call is sent at most once. Any outcome after sending that is not a
  proven ``done`` is ``error`` with ``effect_not_confirmed``; nothing retries;
* a completed stop is ``stopped`` — ``already-stopped`` is not claimed because
  ``JobRemoved done`` cannot distinguish it (IO-1);
* the holder and backstop commands are built here, never taken from a caller:
  ``ROLE_INTERPRETER -I -S ROLE_ARTIFACT`` followed by exactly the ``hold``,
  ``deact … stop-post`` or ``backstop`` role tail of RT-2/RT-3/RT-4, and the
  complete vector is checked against that shape before the bus is opened;
* before a unit that runs that vector is created, the interpreter and the entry
  point must be root-only (``artifact``); otherwise ``error(unsafe-artifact)``
  and no bus call;
* only ``AccessDenied`` / ``InteractiveAuthorizationRequired`` (all four calls),
  ``NoSuchUnit`` (stop calls), ``UnitExists`` (DI-2) and, for stop calls only,
  ``InvalidArgs`` are refusals. ``InvalidArgs`` on a create call can be raised
  after the unit is made transient (A-05.12), so it stays an error until a
  supported contract proves otherwise.
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import TypeVar

from application.unit_control import (
    CAPTURE_UNIT,
    BackstopCompletion,
    BackstopSpec,
    ControlError,
    ControlOk,
    ControlRefused,
    ControlResult,
    ControlSpecError,
    HolderSpec,
    JobCompletion,
    RefusalReason,
    StopCompletion,
    StopOutcome,
    TimerObservation,
    UnitProperties,
    UnitProperty,
    backstop_timer_name,
    backstop_service_name,
    holder_unit_name,
    validate_unit_name,
)

from . import artifact
from .bus import (
    BusConnection,
    BusConnector,
    BusDisconnected,
    BusError,
    BusProtocolError,
    BusReply,
    BusRequest,
    BusTimeout,
    SignalWatch,
    Variant,
)

SYSTEMD = "org.freedesktop.systemd1"
MANAGER_PATH = "/org/freedesktop/systemd1"
MANAGER_IFACE = "org.freedesktop.systemd1.Manager"
UNIT_IFACE = "org.freedesktop.systemd1.Unit"
SERVICE_IFACE = "org.freedesktop.systemd1.Service"
TIMER_IFACE = "org.freedesktop.systemd1.Timer"
PROPERTIES_IFACE = "org.freedesktop.DBus.Properties"
_JOB_PATH_PREFIX = "/org/freedesktop/systemd1/job/"

JOB_MODE = "fail"  # StartTransientUnit and StopUnit; pinned by tests.

# The controlled role runtime (RT-2, RT-3, RT-4). The distribution interpreter,
# root-owned, run isolated (-I) and without site initialization (-S); the
# artifact carries its own D-Bus client (infra/rp11-h1). Not configurable.
ROLE_INTERPRETER = "/usr/bin/python3.14"
ROLE_ARTIFACT = "/usr/local/libexec/freedom-blades-rp11/rp11_h1.py"
_ROLE_FLAGS = ("-I", "-S")

_Observed = TypeVar("_Observed")

_AUTH_REFUSALS = frozenset(
    {
        "org.freedesktop.DBus.Error.AccessDenied",
        "org.freedesktop.DBus.Error.InteractiveAuthorizationRequired",
    }
)
_NO_SUCH_UNIT = "org.freedesktop.systemd1.NoSuchUnit"
_UNIT_EXISTS = "org.freedesktop.systemd1.UnitExists"
_INVALID_ARGS = "org.freedesktop.DBus.Error.InvalidArgs"
_ALREADY_SUBSCRIBED = "org.freedesktop.systemd1.AlreadySubscribed"

# name -> (interface, expected wire signature)
_PROPERTY_WIRE: dict[UnitProperty, tuple[str, str]] = {
    UnitProperty.ACTIVE_STATE: (UNIT_IFACE, "s"),
    UnitProperty.INVOCATION_ID: (UNIT_IFACE, "ay"),
    UnitProperty.INACTIVE_ENTER_TIMESTAMP_MONOTONIC: (UNIT_IFACE, "t"),
    UnitProperty.JOB: (UNIT_IFACE, "(uo)"),
    UnitProperty.LOAD_STATE: (UNIT_IFACE, "s"),
    UnitProperty.RESULT: (SERVICE_IFACE, "s"),
    UnitProperty.EXEC_MAIN_START_TIMESTAMP_MONOTONIC: (SERVICE_IFACE, "t"),
    UnitProperty.TIMEOUT_START_USEC: (SERVICE_IFACE, "t"),
}

_OBSERVE_HOLDER = (
    UnitProperty.ACTIVE_STATE,
    UnitProperty.JOB,
    UnitProperty.RESULT,
    UnitProperty.INVOCATION_ID,
)
_OBSERVE_TIMER = (UnitProperty.ACTIVE_STATE, UnitProperty.LOAD_STATE)
_OBSERVE_TIMER_LINK = (
    # (interface, property, signature) for TimerObservation, in field order.
    (UNIT_IFACE, "ActiveState", "s"),
    (UNIT_IFACE, "LoadState", "s"),
    (UNIT_IFACE, "Triggers", "as"),
    (TIMER_IFACE, "Unit", "s"),
)
_OBSERVE_STOPPED_SERVICE = (
    UnitProperty.ACTIVE_STATE,
    UnitProperty.RESULT,
    UnitProperty.INVOCATION_ID,
)


@dataclass(frozen=True)
class Deadlines:
    """Bounded client deadlines. ``call`` bounds each bus round trip;
    ``completion`` bounds the wait for ``JobRemoved`` after the reply."""

    call_seconds: float = 10.0
    completion_seconds: float = 30.0

    def __post_init__(self) -> None:
        for name in ("call_seconds", "completion_seconds"):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not 0 < value <= 600
            ):
                raise ValueError(f"{name} must be a number in (0, 600]")


def unit_object_path(unit: str) -> str:
    """Client-computed unit object path (``bus_label_escape``, A-02.1)."""
    if not unit:
        return MANAGER_PATH + "/unit/_"
    out = []
    for index, byte in enumerate(unit.encode("utf-8")):
        char = chr(byte)
        if (char.isascii() and char.isalpha()) or (char.isdigit() and index > 0):
            out.append(char)
        else:
            out.append(f"_{byte:02x}")
    return MANAGER_PATH + "/unit/" + "".join(out)


# --- role commands ---------------------------------------------------------


class _Role(str, Enum):
    HOLD = "hold"
    STOP_POST = "stop-post"
    BACKSTOP = "backstop"


@dataclass(frozen=True)
class _RoleCommand:
    """One ``a(sasb)`` element. Private: built only by ``_role_command``."""

    path: str
    argv: tuple[str, ...]


_ACTIVATION_TOKEN = re.compile(r"rp11-act-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}")
_SHA256_TOKEN = re.compile(r"[0-9a-f]{64}")


def _role_tail(role: _Role, activation_id: str, artifact_sha256: str) -> tuple[str, ...]:
    if role is _Role.HOLD:
        return ("hold", activation_id, artifact_sha256)
    if role is _Role.STOP_POST:
        return ("deact", activation_id, artifact_sha256, "stop-post")
    return ("backstop", activation_id, artifact_sha256)


def _role_command(role: _Role, activation_id: str, artifact_sha256: str) -> _RoleCommand:
    prefix = (ROLE_INTERPRETER, *_ROLE_FLAGS, ROLE_ARTIFACT)
    return _RoleCommand(ROLE_INTERPRETER, prefix + _role_tail(role, activation_id, artifact_sha256))


def _check_role_command(command: _RoleCommand, role: _Role) -> None:
    """Refuse anything but the exact vector for ``role``; raises ``ControlSpecError``."""
    if type(command) is not _RoleCommand or type(command.argv) is not tuple:
        raise ControlSpecError("role command has the wrong type")
    argv = command.argv
    if command.path != ROLE_INTERPRETER or argv[:4] != (
        ROLE_INTERPRETER,
        *_ROLE_FLAGS,
        ROLE_ARTIFACT,
    ):
        raise ControlSpecError("role command does not run the controlled artifact")
    if len(argv) < 7 or not all(type(a) is str for a in argv):
        raise ControlSpecError("role command has a malformed argument list")
    activation_id, artifact_sha256 = argv[5], argv[6]
    if not _ACTIVATION_TOKEN.fullmatch(activation_id) or not _SHA256_TOKEN.fullmatch(
        artifact_sha256
    ):
        raise ControlSpecError("role command operands are malformed")
    if argv[4:] != _role_tail(role, activation_id, artifact_sha256):
        raise ControlSpecError(f"role command is not the {role.value} role")


def _role_runtime_problem() -> str | None:
    """Why PID 1 must not be asked to run the role vector, or ``None``.

    The entry point cannot vouch for itself, so this independent check (see
    ``artifact``) runs before any unit that executes it is created.
    """
    for path in (ROLE_INTERPRETER, ROLE_ARTIFACT):
        problem = artifact.unsafe_root_path(path)
        if problem:
            return problem
    return None


def _checked_holder(spec: HolderSpec) -> tuple[str, _RoleCommand, _RoleCommand]:
    """Revalidate (a frozen dataclass can still be forced) and build both commands."""
    if type(spec) is not HolderSpec:
        raise ControlSpecError("holder request must be a HolderSpec")
    HolderSpec.validate(spec)  # not spec.validate: an instance attribute could shadow it
    start = _role_command(_Role.HOLD, spec.activation_id, spec.artifact_sha256)
    stop_post = _role_command(_Role.STOP_POST, spec.activation_id, spec.artifact_sha256)
    _check_role_command(start, _Role.HOLD)
    _check_role_command(stop_post, _Role.STOP_POST)
    return holder_unit_name(spec.activation_id), start, stop_post


def _checked_backstop(spec: BackstopSpec) -> tuple[str, str, _RoleCommand]:
    if type(spec) is not BackstopSpec:
        raise ControlSpecError("backstop request must be a BackstopSpec")
    BackstopSpec.validate(spec)
    start = _role_command(_Role.BACKSTOP, spec.activation_id, spec.artifact_sha256)
    _check_role_command(start, _Role.BACKSTOP)
    return (
        backstop_timer_name(spec.activation_id),
        backstop_service_name(spec.activation_id),
        start,
    )


# --- value encodings -------------------------------------------------------


def _exec(command: _RoleCommand) -> Variant:
    return Variant("a(sasb)", [(command.path, list(command.argv), False)])


def _usec(seconds: int) -> Variant:
    return Variant("t", seconds * 1_000_000)


def _holder_properties(
    spec: HolderSpec, start: _RoleCommand, stop_post: _RoleCommand
) -> list:
    return [
        ("Type", Variant("s", "exec")),
        ("Restart", Variant("s", "no")),
        ("OOMScoreAdjust", Variant("i", -1000)),
        ("RuntimeMaxUSec", _usec(spec.runtime_max_seconds)),
        ("TimeoutStopUSec", _usec(spec.timeout_stop_seconds)),
        ("ExecStopPost", _exec(stop_post)),
        ("ExecStart", _exec(start)),
    ]


def _backstop_timer_properties(spec: BackstopSpec) -> list:
    interval = spec.interval_seconds * 1_000_000
    return [
        ("TimersMonotonic", Variant("a(st)", [("OnActiveSec", interval)])),
        ("TimersMonotonic", Variant("a(st)", [("OnUnitActiveSec", interval)])),
        ("AccuracyUSec", Variant("t", 1_000_000)),
    ]


def _backstop_service_properties(spec: BackstopSpec, start: _RoleCommand) -> list:
    # D-10: no TimeoutStartUSec.
    return [
        ("Type", Variant("s", "exec")),
        ("Restart", Variant("s", "no")),
        ("OOMScoreAdjust", Variant("i", -1000)),
        ("RuntimeMaxUSec", _usec(spec.runtime_max_seconds)),
        ("TimeoutStopUSec", _usec(spec.timeout_stop_seconds)),
        ("ExecStart", _exec(start)),
    ]


# --- the adapter -----------------------------------------------------------


class SystemdManagerAdapter:
    def __init__(
        self,
        connector: BusConnector,
        *,
        deadlines: Deadlines | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._connector = connector
        self._deadlines = deadlines or Deadlines()
        self._clock = clock

    # DI-1 --------------------------------------------------------------

    def read_unit(
        self, unit: str, properties: tuple[UnitProperty, ...]
    ) -> ControlResult[UnitProperties]:
        try:
            validate_unit_name(unit)
            wanted = tuple(UnitProperty(p) for p in properties)
            if not wanted or len(set(wanted)) != len(wanted):
                raise ControlSpecError("property list must be non-empty and unique")
        except (ControlSpecError, ValueError) as exc:
            return ControlError("invalid-request", str(exc))
        connection = self._open()
        if isinstance(connection, ControlError):
            return connection
        try:
            return self._read(connection, unit, wanted)
        finally:
            connection.close()

    def _read(
        self, connection: BusConnection, unit: str, wanted: tuple[UnitProperty, ...]
    ) -> ControlResult[UnitProperties]:
        values: dict[UnitProperty, str | int] = {}
        for prop in wanted:
            interface, signature = _PROPERTY_WIRE[prop]
            decoded = self._get(connection, unit, interface, prop.value, signature)
            if isinstance(decoded, ControlError):
                return decoded
            values[prop] = decoded
        return ControlOk(values)

    def _get(
        self, connection: BusConnection, unit: str, interface: str, name: str, signature: str
    ):
        """One strictly decoded ``Properties.Get``; a ``ControlError`` on any failure."""
        try:
            reply = connection.call(
                BusRequest(
                    SYSTEMD,
                    unit_object_path(unit),
                    PROPERTIES_IFACE,
                    "Get",
                    "ss",
                    (interface, name),
                ),
                timeout=self._deadlines.call_seconds,
            )
        except BusError as exc:
            # D-3: a read has no refusal case; UnknownProperty means the
            # manager did not report it, which is a stop for the caller.
            return ControlError(exc.name, exc.message)
        except (BusTimeout, BusDisconnected, BusProtocolError) as exc:
            return ControlError(_transport_kind(exc), str(exc))
        decoded = _decode_value(signature, reply)
        if decoded is None:
            return ControlError("invalid-reply", f"unexpected reply for {name}")
        return decoded

    # DI-2 --------------------------------------------------------------

    def create_holder(self, spec: HolderSpec) -> ControlResult[JobCompletion]:
        try:
            unit, start, stop_post = _checked_holder(spec)
        except (ControlSpecError, AttributeError, TypeError) as exc:
            return ControlError("invalid-request", str(exc))
        unsafe = _role_runtime_problem()
        if unsafe:
            return ControlError("unsafe-artifact", unsafe)
        request = BusRequest(
            SYSTEMD,
            MANAGER_PATH,
            MANAGER_IFACE,
            "StartTransientUnit",
            "ssa(sv)a(sa(sv))",
            (unit, JOB_MODE, _holder_properties(spec, start, stop_post), []),
        )
        result = self._mutate(
            request,
            unit=unit,
            observe=lambda c: self._observe(c, unit, _OBSERVE_HOLDER),
            refusals={_UNIT_EXISTS: RefusalReason.EXISTS},
        )
        if isinstance(result, ControlOk):
            job_path, observed = result.value
            return ControlOk(JobCompletion(job_path, unit, observed))
        return result

    # DI-3 --------------------------------------------------------------

    def create_backstop(self, spec: BackstopSpec) -> ControlResult[BackstopCompletion]:
        try:
            timer, service, start = _checked_backstop(spec)
        except (ControlSpecError, AttributeError, TypeError) as exc:
            return ControlError("invalid-request", str(exc))
        unsafe = _role_runtime_problem()
        if unsafe:
            return ControlError("unsafe-artifact", unsafe)
        aux = [(service, _backstop_service_properties(spec, start))]
        request = BusRequest(
            SYSTEMD,
            MANAGER_PATH,
            MANAGER_IFACE,
            "StartTransientUnit",
            "ssa(sv)a(sa(sv))",
            (timer, JOB_MODE, _backstop_timer_properties(spec), aux),
        )
        # D-3 names UnitExists for DI-2 only; for DI-3 it stays an error.
        result = self._mutate(
            request, unit=timer, observe=lambda c: self._observe_timer(c, timer), refusals={}
        )
        if isinstance(result, ControlOk):
            job_path, observed = result.value
            return ControlOk(BackstopCompletion(job_path, timer, observed))
        return result

    # DI-4 / DI-S ---------------------------------------------------------

    def disarm_backstop(self, activation_id: str) -> ControlResult[StopCompletion]:
        try:
            unit = backstop_timer_name(activation_id)
        except ControlSpecError as exc:
            return ControlError("invalid-request", str(exc))
        return self._stop(unit, _OBSERVE_TIMER)

    def stop_capture_unit(self) -> ControlResult[StopCompletion]:
        return self._stop(CAPTURE_UNIT, _OBSERVE_STOPPED_SERVICE)

    def _stop(self, unit: str, observe: tuple[UnitProperty, ...]) -> ControlResult[StopCompletion]:
        request = BusRequest(
            SYSTEMD, MANAGER_PATH, MANAGER_IFACE, "StopUnit", "ss", (unit, JOB_MODE)
        )
        result = self._mutate(
            request,
            unit=unit,
            observe=lambda c: self._observe(c, unit, observe),
            refusals={
                _NO_SUCH_UNIT: RefusalReason.NOT_LOADED,
                # The stop path validates name and mode before any job exists, and
                # the mode is fixed in code, so InvalidArgs is a pre-mutation refusal.
                _INVALID_ARGS: RefusalReason.INVALID_REQUEST,
            },
        )
        if isinstance(result, ControlOk):
            job_path, observed = result.value
            completion = JobCompletion(job_path, unit, observed)
            return ControlOk(StopCompletion(StopOutcome.STOPPED, completion))
        return result

    # shared mutating flow --------------------------------------------------

    def _mutate(
        self,
        request: BusRequest,
        *,
        unit: str,
        observe: Callable[[BusConnection], _Observed],
        refusals: dict[str, RefusalReason],
    ) -> ControlResult[tuple[str, _Observed]]:
        """Send ``request`` once; on a proven ``done`` return ``(job path, observe())``."""
        connection = self._open()
        if isinstance(connection, ControlError):
            return connection
        try:
            watch_or_error = self._prepare(connection, unit)
            if isinstance(watch_or_error, ControlError):
                return watch_or_error
            watch = watch_or_error

            # From here the mutating call is sent exactly once.
            try:
                reply = connection.call(request, timeout=self._deadlines.call_seconds)
            except BusError as exc:
                return self._classify_call_error(exc, refusals)
            except (BusTimeout, BusDisconnected, BusProtocolError) as exc:
                return _unconfirmed(_transport_kind(exc), str(exc))

            job_path = _job_path(reply)
            if job_path is None:
                return _unconfirmed("invalid-reply", "mutating call reply was not a job path")

            outcome = self._await_job(watch, job_path, unit)
            if isinstance(outcome, ControlError):
                return outcome
            return ControlOk((job_path, observe(connection)))
        finally:
            connection.close()

    def _open(self) -> BusConnection | ControlError:
        try:
            return self._connector()
        except (BusDisconnected, BusProtocolError, BusTimeout, BusError, OSError) as exc:
            return ControlError("connect-failed", str(exc))

    def _prepare(self, connection: BusConnection, unit: str) -> SignalWatch | ControlError:
        """Match + Subscribe before the mutating call. Failure here is pre-mutation."""
        try:
            watch = connection.watch_signals(
                sender=SYSTEMD,
                path=MANAGER_PATH,
                interface=MANAGER_IFACE,
                member="JobRemoved",
                arg2=unit,
            )
        except (BusError, BusTimeout, BusDisconnected, BusProtocolError) as exc:
            return ControlError("subscribe-failed", f"signal match: {exc}")
        try:
            connection.call(
                BusRequest(SYSTEMD, MANAGER_PATH, MANAGER_IFACE, "Subscribe"),
                timeout=self._deadlines.call_seconds,
            )
        except BusError as exc:
            if exc.name != _ALREADY_SUBSCRIBED:
                return ControlError("subscribe-failed", str(exc))
        except (BusTimeout, BusDisconnected, BusProtocolError) as exc:
            return ControlError("subscribe-failed", str(exc))
        return watch

    def _classify_call_error(
        self, exc: BusError, refusals: dict[str, RefusalReason]
    ) -> ControlRefused | ControlError:
        if exc.name in _AUTH_REFUSALS:
            return ControlRefused(RefusalReason.NOT_AUTHORIZED)
        reason = refusals.get(exc.name)
        if reason is not None:
            return ControlRefused(reason)
        return _unconfirmed(exc.name, exc.message)

    def _await_job(
        self, watch: SignalWatch, job_path: str, unit: str
    ) -> ControlOk[str] | ControlError:
        deadline = self._clock() + self._deadlines.completion_seconds
        while True:
            remaining = deadline - self._clock()
            if remaining <= 0:
                return _unconfirmed("completion-timeout", "no JobRemoved before the deadline")
            try:
                signal = watch.next(timeout=remaining)
            except BusTimeout:
                return _unconfirmed("completion-timeout", "no JobRemoved before the deadline")
            except (BusDisconnected, BusProtocolError, BusError) as exc:
                return _unconfirmed(_transport_kind(exc), str(exc))
            if signal.member != "JobRemoved" or signal.interface != MANAGER_IFACE:
                continue
            body = signal.body
            if (
                signal.signature != "uoss"
                or len(body) != 4
                or not isinstance(body[1], str)
                or not isinstance(body[2], str)
                or not isinstance(body[3], str)
            ):
                return _unconfirmed("invalid-reply", "unparsable JobRemoved")
            if body[1] != job_path or body[2] != unit:
                continue
            if body[3] != "done":
                return _unconfirmed("job-result", f"job result {body[3]!r}")
            return ControlOk(body[3])

    def _observe(
        self, connection: BusConnection, unit: str, props: tuple[UnitProperty, ...]
    ) -> UnitProperties | None:
        """Diagnostic only: never changes the outcome, failure yields ``None``."""
        result = self._read(connection, unit, props)
        return result.value if isinstance(result, ControlOk) else None

    def _observe_timer(self, connection: BusConnection, timer: str) -> TimerObservation | None:
        """DI-3 O-C: the timer's state and its trigger link. Diagnostic only;
        any failed or malformed read yields ``None``, never a changed result."""
        values = []
        for interface, name, signature in _OBSERVE_TIMER_LINK:
            value = self._get(connection, timer, interface, name, signature)
            if isinstance(value, ControlError):
                return None
            values.append(value)
        return TimerObservation(*values)


# --- helpers ---------------------------------------------------------------


def _transport_kind(exc: Exception) -> str:
    if isinstance(exc, BusTimeout):
        return "timeout"
    if isinstance(exc, BusDisconnected):
        return "disconnected"
    if isinstance(exc, BusError):
        return exc.name
    return "invalid-reply"


def _unconfirmed(kind: str, detail: str = "") -> ControlError:
    return ControlError(kind, detail, effect_not_confirmed=True)


def _job_path(reply: BusReply) -> str | None:
    if reply.signature != "o" or len(reply.body) != 1:
        return None
    path = reply.body[0]
    if not isinstance(path, str) or not path.startswith(_JOB_PATH_PREFIX):
        return None
    if not path[len(_JOB_PATH_PREFIX) :].isdigit():
        return None
    return path


def _decode_value(signature: str, reply: BusReply):
    """Strictly decode one ``Properties.Get`` reply; ``None`` if malformed."""
    if reply.signature != "v" or len(reply.body) != 1:
        return None
    variant = reply.body[0]
    if not (isinstance(variant, tuple) and len(variant) == 2):
        return None
    got_signature, value = variant
    if got_signature != signature:
        return None
    if signature == "s":
        return value if isinstance(value, str) else None
    if signature == "t":
        return (
            value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None
        )
    if signature == "as":
        if not isinstance(value, (list, tuple)) or not all(isinstance(v, str) for v in value):
            return None
        return tuple(value)
    if signature == "ay":
        if not isinstance(value, (bytes, bytearray)) or len(value) not in (0, 16):
            return None
        return bytes(value).hex()
    if signature == "(uo)":
        if not (isinstance(value, tuple) and len(value) == 2):
            return None
        job_id, job_path = value
        if not isinstance(job_id, int) or not isinstance(job_path, str):
            return None
        return job_id
    return None
