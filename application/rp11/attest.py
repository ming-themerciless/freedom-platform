"""RT-5: ``attest``, the interactive root recovery role (inventory §3 RT-5, §6 RT-5).

``attest`` runs the shared cleanup (``application.rp11.cleanup``, trigger ``attest``)
only after proving that no holder or backstop unit still owns the activation.

RT5.PRE reads ``ActiveState`` of exactly three units derived from the validated
activation id, in this order, and stops at the first one that does not permit cleanup:

* the holder ``<id>.service``;
* the backstop timer ``<id>-backstop.timer``;
* the backstop service ``<id>-backstop.service``.

``inactive``, ``failed`` and a typed *not loaded* refusal permit it. ``activating``,
``active``, ``deactivating`` and ``reloading`` mean a live owner: ``owner-active``.
Everything else (a timeout, a disconnect, a malformed or partial reply, an unknown
error, an unexpected refusal, a state outside both sets such as ``maintenance`` or
``refreshing``) is ``precondition-unestablished``. Both end the role before CL-G:
nothing is created, read from the evidence or authority files, removed or sent to
Polkit, and no unit is started, stopped or reset. The reads are sequential, not an
atomic manager snapshot, and a satisfied read says nothing about another unit.

*Reversible choice:* a state outside both sets fails closed rather than being coerced
to either. A newer systemd that adds a state therefore refuses attestation until the
set below is extended deliberately.

Exit status: the cleanup's own (0 only for ``st1-verified``, 1 … 5 otherwise);
``owner-active`` 30; ``precondition-unestablished`` 31; an unexpected exception 70
(composition root).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from application.unit_control import (
    ControlOk,
    ControlRefused,
    RefusalReason,
    UnitControl,
    UnitProperty,
    backstop_service_name,
    backstop_timer_name,
    holder_unit_name,
    validate_activation_id,
)

from .cleanup import CleanupOutcome

OWNS = frozenset({"activating", "active", "deactivating", "reloading"})
GONE = frozenset({"inactive", "failed"})
NOT_FOUND = "not-found"

EXIT_OWNER_ACTIVE = 30
EXIT_UNESTABLISHED = 31


class AttestEnd(str, Enum):
    OWNER_ACTIVE = "owner-active"
    UNESTABLISHED = "precondition-unestablished"
    CLEANUP = "cleanup"


@dataclass(frozen=True)
class AttestOutcome:
    end: AttestEnd
    line: str
    exit_code: int
    cleanup: CleanupOutcome | None = None


class AttestProcedure:
    """RT5.PRE, then one run of the shared cleanup.

    ``cleanup(holder_state)`` runs the engine once with trigger ``attest``; the holder
    state it receives is the manager's own answer for the holder (``inactive``,
    ``failed`` or ``not-found``), the only observed fact the engine's fields take.
    """

    def __init__(
        self,
        activation_id: str,
        units: UnitControl,
        cleanup: Callable[[str], CleanupOutcome],
    ) -> None:
        self._id = validate_activation_id(activation_id)
        self._units = units
        self._cleanup = cleanup

    def run(self) -> AttestOutcome:
        holder_state = ""
        for role, unit in self._owners():
            state = self._state(unit)
            if state in OWNS:
                return self._refused(AttestEnd.OWNER_ACTIVE, role, f"state={state}", EXIT_OWNER_ACTIVE)
            if state not in GONE and state != NOT_FOUND:
                return self._refused(AttestEnd.UNESTABLISHED, role, f"read={state}", EXIT_UNESTABLISHED)
            holder_state = holder_state or state
        outcome = self._cleanup(holder_state)
        return AttestOutcome(
            AttestEnd.CLEANUP, outcome.diagnostic(self._id), outcome.terminal.exit_code, outcome
        )

    def _owners(self) -> tuple[tuple[str, str], ...]:
        return (
            ("holder", holder_unit_name(self._id)),
            ("timer", backstop_timer_name(self._id)),
            ("service", backstop_service_name(self._id)),
        )

    def _state(self, unit: str) -> str:
        """A permitted or owning ``ActiveState``, ``not-found``, or a closed failure token
        (``error``, ``refused``, ``malformed``, ``unsupported``) that never echoes a value."""
        read = self._units.read_unit(unit, (UnitProperty.ACTIVE_STATE,))
        if isinstance(read, ControlRefused):
            return NOT_FOUND if read.reason is RefusalReason.NOT_LOADED else "refused"
        if not isinstance(read, ControlOk):
            return "error"
        value = read.value
        if not hasattr(value, "get"):
            return "malformed"
        state = value.get(UnitProperty.ACTIVE_STATE)
        if type(state) is not str:
            return "malformed"
        return state if state in OWNS | GONE else "unsupported"

    def _refused(self, end: AttestEnd, role: str, detail: str, exit_code: int) -> AttestOutcome:
        return AttestOutcome(end, f"rp11-attest {end.value} {self._id} unit={role} {detail}", exit_code)
