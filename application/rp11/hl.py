"""HL: the hold loop's observation and terminal predicate (RT2.HL.2 … RT2.HL.4).

Pure. The holder builds an ``Observation`` every Δ (``poll_ms``) and asks
``terminal_reason`` for the first matching reason, in the accepted order of
design §4.2.5-R5 (g) (OS-5, amended reasons):

``pass-ended`` · ``pass-failed-early`` · ``start-failed-before-exec`` ·
``capture-unloaded`` · ``start-window-expired``

``observation-failed`` is not a predicate: it is what a failed or unparsable
observation means, decided by the caller. HL never removes anything because of
a reason; the reason only ends the activation (OS-5, under the lock on K).

Facts used, and nothing else:

* ``capture_root`` — whether the capture root ``c`` named in ``pass-a.json``
  exists (a no-follow name lookup only; HL never lists, opens or changes ``c``);
* the capture unit's ``ActiveState``, ``InvocationID`` (empty when null),
  ``InactiveEnterTimestampMonotonic`` (τ), ``Job`` and
  ``ExecMainStartTimestampMonotonic`` from one DI-1 read;
* ``claim`` — whether the consume evidence directory exists (OS-2), and
  ``consumed`` / ``consumed_invocation`` from its journal when it parses.
"""

from __future__ import annotations

from dataclasses import dataclass

from .canonical import ABSENT

NOT_ACTIVE = frozenset({"inactive", "failed"})
BUSY = frozenset({"activating", "active", "deactivating", "reloading"})


@dataclass(frozen=True)
class CaptureBaseline:
    """a₀, i₀ and τ₀ as AM-0 recorded them (``run-start.capture``)."""

    active_state: str
    invocation_id: str  # "" when null
    tau: int


@dataclass(frozen=True)
class Observation:
    active_state: str
    invocation_id: str  # "" when null
    tau: int
    job: int
    exec_main_start_us: int
    capture_root: bool
    claim: bool
    consumed: bool = False
    consumed_invocation: str = ""

    def doc(self) -> dict:
        """The ``hold-end`` / ``pass-observed`` fields: states and flags, no paths."""
        return {
            "active_state": self.active_state,
            "invocation_id": self.invocation_id or ABSENT,
            "inactive_enter_us": self.tau,
            "job": self.job,
            "exec_main_start_us": self.exec_main_start_us,
            "capture_root": self.capture_root,
            "claim": self.claim,
            "consumed": self.consumed,
        }


def terminal_reason(
    obs: Observation,
    base: CaptureBaseline,
    *,
    window_expired: bool,
    active_invocations: frozenset[str],
) -> str | None:
    """The first matching reason, or ``None`` while the activation continues.

    ``active_invocations`` are the ``InvocationID`` values HL has seen while the
    capture unit was ``active`` since ACT PASS (evidence that ``ExecStart=`` was
    forked in that attempt)."""
    ended = obs.active_state in NOT_ACTIVE
    if obs.capture_root and ended:
        return "pass-ended"
    forked = obs.exec_main_start_us != 0 or (
        obs.consumed_invocation != "" and obs.consumed_invocation in active_invocations
    )
    if obs.consumed and not obs.capture_root and ended and forked:
        return "pass-failed-early"
    if not obs.capture_root and ended and (
        obs.tau not in (base.tau, 0)
        or (obs.invocation_id != "" and obs.invocation_id != base.invocation_id)
        or obs.claim
    ):
        return "start-failed-before-exec"
    if (
        not obs.capture_root
        and not obs.claim
        and obs.active_state == "inactive"
        and obs.tau == 0 != base.tau
        and obs.invocation_id in ("", base.invocation_id)
    ):
        return "capture-unloaded"
    if (
        window_expired
        and not obs.capture_root
        and not obs.claim
        and obs.tau == base.tau
        and ended
        and obs.job == 0
    ):
        return "start-window-expired"
    return None
