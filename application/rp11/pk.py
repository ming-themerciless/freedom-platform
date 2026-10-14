"""PK/2: the authorization series (H-PK2.1 … H-PK2.7) over DI-5 and DI-6.

Per call, in order: create one subject (DI-6, the only child a role creates),
build its identity from ``/proc`` (``SubjectSource``), ask Polkit (DI-5) as root
without interaction for ``manage-units`` on the capture unit with the series
verb, then settle the subject under SN (one SIGKILL, reap or abandon). Calls
start at offsets 0, 250, 500, 1,000, 2,000, 3,000, 4,000 ms and then every
2,000 ms; none starts after ``pk_op_ms``.

The series result is ``authorized``, ``not-authorized`` or ``unconfirmed``
(``only-errors``, ``still-authorized``, ``not-seen`` or ``interrupted``). A
caller with a stop flag (the holder, SG-4) passes ``stop_requested``: it is
read before every call and at every sliced wake-up, and a set flag ends the
series ``unconfirmed``/``interrupted`` after the current subject is settled. An ``error`` never
ends a series and never becomes a decision. ``unconfirmed`` fails closed at
every use. PK starts, stops and changes nothing.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from application.unit_control import (
    ControlError,
    ControlOk,
    PolkitAuthority,
    PolkitAuthorized,
    PolkitNotAuthorized,
    SubjectSource,
    UnitVerb,
)

from .authority import Operator, Params
from .sn import MAX_CHILD_ENTRIES, ChildHandle, HandleState, SignalContract

PROCEDURE = "pk-root/2"
_FIRST_OFFSETS = (0, 250, 500, 1_000, 2_000, 3_000, 4_000)
_LATER_STEP = 2_000


def schedule(op_ms: int) -> tuple[int, ...]:
    offsets = [o for o in _FIRST_OFFSETS if o < op_ms]
    nxt = _FIRST_OFFSETS[-1] + _LATER_STEP
    while nxt < op_ms:
        offsets.append(nxt)
        nxt += _LATER_STEP
    return tuple(offsets)


class PkMode(str, Enum):
    SEEK_NOT_AUTHORIZED = "seek-not-authorized"
    SEEK_AUTHORIZED = "seek-authorized"
    FIRST_DECISIVE = "first-decisive"


class PkOutcome(str, Enum):
    AUTHORIZED = "authorized"
    NOT_AUTHORIZED = "not-authorized"
    UNCONFIRMED = "unconfirmed"


class SubjectLauncher(Protocol):
    def spawn(self, operator: Operator) -> ChildHandle | ControlError:
        """Create one subject with the operator's credentials in its own session."""
        ...


class Clock(Protocol):
    def monotonic_ms(self) -> int: ...

    def sleep_ms(self, ms: int) -> None: ...


@dataclass
class PkResult:
    mode: PkMode
    verb: UnitVerb
    outcome: PkOutcome
    reason: str
    calls: int = 0
    errors: list[str] = field(default_factory=list)
    children: list[dict] = field(default_factory=list)
    overflow: int = 0
    elapsed_ms: int = 0

    @property
    def abandoned(self) -> int:
        return sum(1 for c in self.children if c["abandoned"])

    def signal_counts(self) -> dict[str, int]:
        counts = {"sent": 0, "esrch": 0, "failed": 0, "not_sent": 0}
        for child in self.children:
            for send in child["sends"]:
                result = send["result"]
                if result == "sent":
                    counts["sent"] += 1
                elif result == "esrch":
                    counts["esrch"] += 1
                elif result.startswith("not-sent"):
                    counts["not_sent"] += 1
                else:
                    counts["failed"] += 1
        return counts


def unconfirmed_without_subject(mode: PkMode, verb: UnitVerb) -> PkResult:
    """No subject can be built (no operator): the series cannot decide anything."""
    return PkResult(mode, verb, PkOutcome.UNCONFIRMED, "only-errors")


class PkSeries:
    def __init__(
        self,
        *,
        launcher: SubjectLauncher,
        subjects: SubjectSource,
        authority: PolkitAuthority,
        contract: SignalContract,
        clock: Clock,
        params: Params,
    ) -> None:
        self._launcher = launcher
        self._subjects = subjects
        self._authority = authority
        self._contract = contract
        self._clock = clock
        self._params = params

    def run(
        self,
        operator: Operator,
        verb: UnitVerb,
        mode: PkMode,
        *,
        stop_requested: Callable[[], bool] | None = None,
    ) -> PkResult:
        result = PkResult(mode, verb, PkOutcome.UNCONFIRMED, "only-errors")
        stopped = stop_requested or (lambda: False)
        start = self._clock.monotonic_ms()
        seen: set[PkOutcome] = set()
        interrupted = False
        for offset in schedule(self._params.pk_op_ms):
            waited = self._wait_until(start + offset, start + self._params.pk_op_ms, stopped)
            if waited is None:
                interrupted = True
                break
            if not waited:
                break
            decision = self._one_call(operator, verb, result)
            result.calls += 1
            if decision is None:
                continue
            seen.add(decision)
            if _decisive(mode, decision):
                result.outcome, result.reason = decision, "decided"
                break
        if result.outcome is PkOutcome.UNCONFIRMED:
            result.reason = "interrupted" if interrupted else _unconfirmed_reason(mode, seen)
        result.elapsed_ms = max(0, self._clock.monotonic_ms() - start)
        return result

    def _wait_until(self, target_ms: int, end_ms: int, stopped: Callable[[], bool]) -> bool | None:
        """Sliced sleep to ``target_ms``; False if the series window has closed,
        ``None`` if the stop flag is set (read before the call and at every wake-up)."""
        while True:
            if stopped():
                return None
            now = self._clock.monotonic_ms()
            if now >= end_ms:
                return False
            if now >= target_ms:
                return True
            self._clock.sleep_ms(min(self._params.slice_ms, target_ms - now))

    def _one_call(self, operator: Operator, verb: UnitVerb, result: PkResult) -> PkOutcome | None:
        handle = self._launcher.spawn(operator)
        if isinstance(handle, ControlError):
            result.errors.append(f"spawn:{handle.kind}")
            return None
        try:
            decision = self._decide(operator, verb, handle, result)
        finally:
            self._contract.settle_pk_subject(handle)
            self._record_child(result, handle)
        return decision

    def _decide(
        self, operator: Operator, verb: UnitVerb, handle: ChildHandle, result: PkResult
    ) -> PkOutcome | None:
        if not handle.ready:
            result.errors.append("spawn:not-ready")
            return None
        subject = self._subjects.subject_for_pid(handle.pid)
        if not isinstance(subject, ControlOk):
            result.errors.append(f"subject:{getattr(subject, 'kind', 'error')}")
            return None
        identity = subject.value
        if identity.uid != operator.uid:
            # Credentials were not applied: polkitd would decide for another account.
            result.errors.append("subject:uid-mismatch")
            return None
        if handle.start_ticks is not None and identity.start_time != handle.start_ticks:
            result.errors.append("subject:replaced")
            return None
        answer = self._authority.check(identity, verb)
        if isinstance(answer, PolkitAuthorized):
            return PkOutcome.AUTHORIZED
        if isinstance(answer, PolkitNotAuthorized):
            return PkOutcome.NOT_AUTHORIZED
        result.errors.append(f"polkit:{getattr(answer, 'kind', 'error')}")
        return None

    @staticmethod
    def _record_child(result: PkResult, handle: ChildHandle | None) -> None:
        if handle is None:
            return
        if handle.state is HandleState.RUNNING:
            handle.anomalies.append("unsettled")
        if len(result.children) < MAX_CHILD_ENTRIES:
            result.children.append(handle.entry())
        else:
            result.overflow += 1


def _decisive(mode: PkMode, decision: PkOutcome) -> bool:
    if mode is PkMode.SEEK_NOT_AUTHORIZED:
        return decision is PkOutcome.NOT_AUTHORIZED
    if mode is PkMode.SEEK_AUTHORIZED:
        return decision is PkOutcome.AUTHORIZED
    return True


def _unconfirmed_reason(mode: PkMode, seen: set[PkOutcome]) -> str:
    if not seen:
        return "only-errors"
    if mode is PkMode.SEEK_NOT_AUTHORIZED:
        return "still-authorized"
    return "not-seen"
