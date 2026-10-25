"""Non-root executor OS-6: interrupt the capture pass under OC-1/OC-2/OC-3 (CX-3).

One validated activation id in; the route is *available* only while one observation
shows all of

* **OC-1** the fixed capture unit's exact ``ActiveState`` is ``active``;
* **OC-2** its exact, non-empty ``InvocationID`` equals the consume journal's
  ``run-start.invocation_id``;
* **OC-3** that journal is valid, untorn and is exactly the complete successful history the
  production RT-1 ``consume`` emits (``is_successful_consume_history``), ending in the one
  terminal ``run-end {outcome: consumed}``.

Only then is the accepted static SA-2 ``stop`` role invoked, once. Every other state is
*unavailable*: no privileged child, no unit or filesystem mutation, no retry. Unavailable
is never converted into cleanup, finalization or attestation (CX-3: the pass continues).

The read and the stop need not be atomic (Lemma R6): after OC-1..OC-3 were validly
observed the durable one-shot claim has crossed SB-1, so a stop that lands late is
harmless. There is therefore exactly one read of each input and no second look, and a
later observation is never permission to retry.

Boundary values are evidence only when they are the exact accepted types: subclasses,
coercions and objects with their own equality or truthiness are never consulted.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from application.unit_control import (
    CAPTURE_UNIT,
    ControlError,
    ControlOk,
    ControlRefused,
    UnitProperty,
    validate_activation_id,
)

from application.rp11.journal import JournalKind, consume_run, parse_journal
from application.rp11.pk import PkMode, PkOutcome

_INVOCATION = re.compile(r"[0-9a-f]{32}")
#: The largest journal evidence the reader may return: the existing terminal-journal volume.
MAX_JOURNAL_BYTES = 65_536
_OBSERVED = (UnitProperty.ACTIVE_STATE, UnitProperty.INVOCATION_ID)


class InterruptEnd(str, Enum):
    INTERRUPTED = "interrupted"
    UNAVAILABLE = "unavailable"
    REFUSED = "refused"
    ERROR = "error"


@dataclass(frozen=True)
class InterruptResult:
    """A closed outcome with a stable, value-free ``reason`` token."""

    end: InterruptEnd
    reason: str = ""
    effect_not_confirmed: bool = False

    @property
    def exit_code(self) -> int:
        if self.end is InterruptEnd.INTERRUPTED:
            return 0
        if self.end is InterruptEnd.UNAVAILABLE:
            return 30
        if self.end is InterruptEnd.REFUSED:
            return 20
        return 22 if self.effect_not_confirmed else 21

    @property
    def line(self) -> str:
        text = f"rp11-interrupt {self.end.value}"
        if self.reason:
            text += f" {self.reason}"
        return text


class PrivilegedStop(Enum):
    """What the one SA-2 invocation is known to have done (its exit status, nothing else)."""

    STOPPED = "stopped"
    REFUSED = "refused"
    NOT_SENT = "not-sent"
    NOT_CONFIRMED = "not-confirmed"
    HANDED_OFF = "handed-off"  # not shown settled, but a durable record gives the contained invocation to the persistent supervisor
    BLOCKED = "blocked"  # not launched: an earlier invocation (or unreadable ownership state) is not yet cleared


class UnitObserver(Protocol):
    def read_unit(self, unit: str, properties: tuple[UnitProperty, ...]): ...


class ConsumeJournalReader(Protocol):
    def read_consume_journal(self, activation_id: str) -> bytes | None:
        """The fixed journal's bytes, or ``None`` when it is not safely readable evidence."""
        ...


class StopInvoker(Protocol):
    def invoke_stop(self) -> PrivilegedStop:
        """Run SA-2 once. Never retries; an exception means the outcome is unknown."""
        ...


def is_successful_consume_history(lines) -> bool:
    """True only for the complete trace ``ConsumeProcedure`` emits on success (CQ-3 .. CQ-7).

    ``run-start``; the write-ahead grant removal ``remove-intent`` then ``removed`` (the only
    CQ-3 path that reaches CQ-4; ``absent`` and every kept class fail first); the CQ-5 series'
    zero or more ordered ``child`` records; the one ``grant-check`` (verb ``start``, mode
    ``seek-not-authorized``, outcome ``not-authorized``, the only outcome CQ-5 accepts);
    ``consumed`` carrying that same outcome; and the terminal ``run-end {outcome: consumed}``.
    Nothing else may appear, and nothing may follow ``consumed`` but that ``run-end``.
    """
    ops = [line.op for line in lines]
    head, tail = ["run-start", "remove-intent", "removed"], ["grant-check", "consumed", "run-end"]
    if len(ops) < len(head) + len(tail) or ops[: len(head)] != head or ops[-len(tail) :] != tail:
        return False
    if any(op != "child" for op in ops[len(head) : -len(tail)]):
        return False
    intent, removed = lines[1].fields, lines[2].fields
    check, consumed, end = lines[-3].fields, lines[-2].fields, lines[-1].fields
    return (
        intent["path"] == removed["path"]
        and check["verb"] == "start"
        and check["mode"] == PkMode.SEEK_NOT_AUTHORIZED.value
        and check["outcome"] == PkOutcome.NOT_AUTHORIZED.value
        and consumed["pk_status"] == PkOutcome.NOT_AUTHORIZED.value
        and end["outcome"] == "consumed"
    )


def _unavailable(reason: str) -> InterruptResult:
    return InterruptResult(InterruptEnd.UNAVAILABLE, reason)


class InterruptProcedure:
    def __init__(self, units: UnitObserver, journals: ConsumeJournalReader, stop: StopInvoker) -> None:
        self._units = units
        self._journals = journals
        self._stop = stop

    def run(self, activation_id: str) -> InterruptResult:
        validate_activation_id(activation_id)  # before any I/O; raises ControlSpecError
        observed = self._observe_unit()
        if isinstance(observed, InterruptResult):
            return observed
        invocation_id = observed
        refusal = self._check_journal(activation_id, invocation_id)
        if refusal is not None:
            return refusal
        return self._interrupt()

    # --- OC-1 / OC-2 (unit side) ---------------------------------------------

    def _observe_unit(self) -> str | InterruptResult:
        try:
            result = self._units.read_unit(CAPTURE_UNIT, _OBSERVED)
        except Exception:  # noqa: BLE001 - an unreadable unit is unavailability, never evidence
            return _unavailable("unit-read-error")
        if type(result) is ControlRefused:
            return _unavailable("unit-read-refused")
        if type(result) is ControlError:
            return _unavailable("unit-read-error")
        if type(result) is not ControlOk or type(result.value) is not dict:
            return _unavailable("unit-read-malformed")
        values = result.value
        if len(values) != 2 or any(type(key) is not UnitProperty for key in values):
            return _unavailable("unit-read-malformed")
        state = values.get(UnitProperty.ACTIVE_STATE)
        invocation = values.get(UnitProperty.INVOCATION_ID)
        if type(state) is not str or type(invocation) is not str:
            return _unavailable("unit-read-malformed")
        if state != "active":
            return _unavailable("not-active")
        if _INVOCATION.fullmatch(invocation) is None:
            return _unavailable("invocation-invalid")
        return invocation

    # --- OC-3 and the OC-2 match (journal side) ------------------------------

    def _check_journal(self, activation_id: str, invocation_id: str) -> InterruptResult | None:
        try:
            data = self._journals.read_consume_journal(activation_id)
        except Exception:  # noqa: BLE001
            return _unavailable("journal-error")
        if type(data) is not bytes or len(data) > MAX_JOURNAL_BYTES:
            return _unavailable("journal-unavailable")
        parsed = parse_journal(data, kind=JournalKind.CONSUME, run=consume_run(activation_id))
        if not parsed.valid:
            return _unavailable("journal-invalid")
        if parsed.torn_tail:
            return _unavailable("journal-torn")
        lines = parsed.lines
        if lines[0].op != "run-start":  # the parser pins this; kept as the explicit contract
            return _unavailable("journal-invalid")
        if lines[0].fields["invocation_id"] != invocation_id:
            return _unavailable("invocation-mismatch")
        ops = [line.op for line in lines]
        if "consume-failed" in ops:
            return _unavailable("consume-failed")
        if ops.count("consumed") != 1:
            return _unavailable("not-consumed")
        if ops.count("run-end") != 1 or ops[-1] != "run-end" or ops.index("consumed") > ops.index("run-end"):
            return _unavailable("journal-incomplete")
        if lines[-1].fields["outcome"] != "consumed":
            return _unavailable("journal-incomplete")
        if not is_successful_consume_history(lines):
            return _unavailable("journal-history")
        return None

    # --- SA-2, exactly once --------------------------------------------------

    def _interrupt(self) -> InterruptResult:
        try:
            outcome = self._stop.invoke_stop()
        except Exception:  # noqa: BLE001 - the one call may have been made: never retried
            return InterruptResult(InterruptEnd.ERROR, "stop-unknown", effect_not_confirmed=True)
        if outcome is PrivilegedStop.STOPPED:
            return InterruptResult(InterruptEnd.INTERRUPTED)
        if outcome is PrivilegedStop.REFUSED:
            return InterruptResult(InterruptEnd.REFUSED, "stop-refused")
        if outcome is PrivilegedStop.NOT_SENT:
            return InterruptResult(InterruptEnd.ERROR, "stop-not-sent")
        if outcome is PrivilegedStop.BLOCKED:
            return InterruptResult(InterruptEnd.ERROR, "stop-blocked")
        if outcome is PrivilegedStop.HANDED_OFF:
            return InterruptResult(InterruptEnd.ERROR, "stop-handed-off", effect_not_confirmed=True)
        return InterruptResult(InterruptEnd.ERROR, "stop-not-confirmed", effect_not_confirmed=True)
