"""RP-11 Pass A orchestration: bind the start, drive a finite plan, finalize once.

This composes two existing pieces and adds one rule between them:

1. ``start_binding.require_start_binding`` proves the service ``INVOCATION_ID``
   equals the consume ``run-start``'s, **before** any capture root exists;
2. an **injected** ``SessionFactory`` performs X-1 (it is called only after the binding
   succeeded), and each caller-supplied ``ActRequest`` goes through
   ``CaptureSession.run_act`` in order;
3. the first failure ends the pass: nothing after it is issued.

This module neither imports nor calls the mechanism's session constructor, and there
is **no default factory**: what creates a capture root, which filesystem, launcher and
clock it uses, and when, is decided by whoever composes the pass, not here.

Every ending that has a session ends it through the mechanism's own single stop
transition, so the pass makes **exactly one** X-3 attempt:

* an act the mechanism could not admit (including ``command-timeout``) is stopped
  by ``run_act`` itself; this module reads that outcome and calls nothing more;
* an admitted act whose exit the injected ``exit_policy`` does not accept, calls
  ``session.stop`` once;
* a plan that runs to its end calls ``session.complete`` once;
* a root with no durable genesis calls ``session.stop`` once, which the mechanism
  answers with its ``not-made`` outcome (nothing is written);
* an unexpected ``Exception`` while the session is still open attempts
  ``session.stop`` once and is then re-raised, so it is never swallowed. The
  **original** error is the one that propagates: if that single stop attempt itself
  raises an ``Exception``, the secondary failure is not allowed to replace it (it is
  recorded as a note carrying only its type name).

Not handled, by design: ``CaptureInterrupted`` is a ``BaseException`` and
propagates untouched, because after an interruption the mechanism forbids any
further call, including an X-3 attempt (C-15). That includes an interruption raised
by the stop attempt in the handler above: it supersedes the original error, which
stays reachable as its ``__context__``. A binding refusal has no session and nothing
to finalize, so it is returned as a result before the factory, and so any
filesystem, launcher or clock call.

**Policy-neutral.** This module contains no command, path, activation or pass
identifier, stream bound, timeout, environment, identity, sandbox or unit policy.
Every one arrives through the arguments: the plan's ``ActRequest`` values carry
their own argv, environment, bounds and timeouts; ``GenesisRequest`` carries the
root, pass id and ``INVOCATION_ID``; ``exit_policy`` says which exits are
acceptable; ``session_factory`` is what turns the genesis request into a session.
There is deliberately no default exit policy: whether a non-zero exit ends the pass
is the Pass A plan's decision, not this module's.

**Opt-in continuation seam (decision D1).** A caller may supply an
``ActContinuation``. Without one the pass behaves exactly as it did before the seam
existed. With one:

* it must say, before any effect, that it covers exactly this plan, or the plan is
  refused;
* after each admitted act whose exit ``exit_policy`` accepted, the session re-reads
  that act's evidence from its own admitted chain (``admitted_evidence``) and the
  continuation judges it; only a return of exactly ``True`` lets the pass go on,
  including from the last act to completion;
* evidence that cannot be re-verified, or is not permitted, ends the pass through the
  same single stop transition, before the next act;
* after a permit, the capture root and its subdirectories must still name the held
  directories, or the pass ends the same way.

The seam judges nothing itself and holds no expected value. Nothing in the
repository passes a continuation to a pass.

**Packaged and imported, not invoked.** Since approved G8, ``rp11_entry.main``
imports this module so that it sits inside the protected artifact closure, and
``build.ENTRY_SOURCES`` lists it, so the closure test forces the two to agree.
Nothing calls ``run_pass_a`` or supplies a session factory: no policy value
(command, path, pass identifier, bound, timeout, environment or exit policy) is
passed in, and the executable path remains exit 69. Nothing here starts a process
itself, and nothing here arms a launcher or constructs a session.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Protocol, Sequence

from ..capture_contract import (
    X3_SUCCEEDED,
    X4_VALID,
    AdmittedEvidence,
    ExitOutcome,
    HandbackBinding,
)
from ..errors import HarnessError
from .capture_mechanism import (
    ActFailure,
    ActOutcome,
    ActRequest,
    CaptureSession,
    FinalizationOutcome,
    GenesisRequest,
    SessionState,
)
from .capture_store import StoreFailure
from .start_binding import StartBindingRefused, require_start_binding

#: Decides, for one admitted act, whether its recorded exit lets the pass go on.
#: Only a return of exactly ``True`` continues; anything else stops the pass.
ExitPolicy = Callable[[ActRequest, ExitOutcome], bool]

#: Performs X-1 for the given request and returns the resulting session (``OPEN``,
#: or ``NO_GENESIS`` when the root could not be made durable). It is called at most
#: once, and only after ``require_start_binding`` succeeded. It may raise; whatever
#: it raises propagates, because no session exists to finalize.
SessionFactory = Callable[[GenesisRequest], CaptureSession]


class ActContinuation(Protocol):
    """The opt-in judgement of each admitted act's evidence (decision D1)."""

    def covers(self, plan: tuple[ActRequest, ...]) -> bool:
        """Exactly ``True`` only if every act of ``plan``, and no other, will be judged."""

    def permits(self, request: ActRequest, evidence: AdmittedEvidence) -> bool:
        """Exactly ``True`` lets the pass go on after this act."""


#: Stop reasons this module itself assigns (they match the capture contract's
#: ``REASON`` grammar). An act failure's reason is the mechanism's classification.
REASON_NO_DURABLE_GENESIS = "no-durable-genesis"
REASON_UNACCEPTABLE_EXIT = "unacceptable-exit"
REASON_UNEXPECTED_ERROR = "orchestrator-error"
#: Only with a continuation: the admitted evidence did not re-verify, or was refused.
REASON_EVIDENCE_UNVERIFIED = "evidence-unverified"
REASON_CONTINUATION_REFUSED = "continuation-refused"
#: Note attached to the original error when its one stop attempt also failed.
NOTE_STOP_ATTEMPT_FAILED = "orchestrator-stop-attempt-failed"


class PassAPlanRefused(HarnessError):
    """The plan or its collaborators are malformed.

    Raised before the binding check and before the factory is called, so nothing was
    touched, except for ``malformed-session``: the factory had already run, and its
    own effects are its own. ``reason`` is a fixed code. It never carries plan content."""

    REASONS = frozenset(
        {
            "empty-plan",
            "malformed-plan",
            "malformed-request",
            "malformed-policy",
            "malformed-factory",
            "malformed-continuation",
            "malformed-session",
        }
    )

    def __init__(self, reason: str) -> None:
        if reason not in self.REASONS:
            raise ValueError("unknown plan refusal")
        self.reason = reason
        super().__init__(reason)


class PassAStatus(str, Enum):
    #: Every act admitted, X-3 succeeded and X-4 is ``valid``.
    COMPLETED = "completed"
    #: An act failed or its exit was not accepted; the pass was stopped.
    STOPPED = "stopped"
    #: X-1 left no durable genesis; no command ran.
    NO_GENESIS = "no-genesis"
    #: The start could not be paired with the consume journal; nothing was created.
    BINDING_REFUSED = "binding-refused"
    #: Every act was admitted, but X-3 failed or X-4 is not ``valid``.
    FINALIZATION_INCOMPLETE = "finalization-incomplete"


@dataclass(frozen=True, slots=True)
class PassAResult:
    status: PassAStatus
    #: ``None`` only for ``COMPLETED``. Otherwise a fixed, content-free code.
    reason: str | None
    #: Every ``run_act`` outcome, in order, including the failing one.
    outcomes: tuple[ActOutcome, ...]
    #: The mechanism's failure for the act that stopped the pass, if that was why.
    failure: ActFailure | None
    #: ``None`` only for ``BINDING_REFUSED``, which has no session to finalize.
    finalization: FinalizationOutcome | None
    #: The handback block; ``None`` only for ``BINDING_REFUSED``.
    binding: HandbackBinding | None

    @property
    def completed(self) -> bool:
        return self.status is PassAStatus.COMPLETED


def run_pass_a(
    *,
    activation_id: str,
    consume_journal: bytes,
    genesis: GenesisRequest,
    acts: Sequence[ActRequest],
    exit_policy: ExitPolicy,
    session_factory: SessionFactory,
    continuation: ActContinuation | None = None,
) -> PassAResult:
    """Run one pass's finite plan, stop at the first failure, finalize exactly once.

    The ``INVOCATION_ID`` paired against ``consume_journal`` is
    ``genesis.invocation_id``, the same value the capture index will record, so the
    two cannot disagree. ``session_factory`` is called with ``genesis`` only after
    that pairing succeeded. Raises ``PassAPlanRefused`` for a malformed plan, policy
    or factory before any effect; every other raise is described in the module
    docstring."""
    plan = _validated_plan(acts, exit_policy, genesis, session_factory, continuation)
    try:
        require_start_binding(activation_id, genesis.invocation_id, consume_journal)
    except StartBindingRefused as refusal:
        return PassAResult(PassAStatus.BINDING_REFUSED, refusal.reason, (), None, None, None)

    session = session_factory(genesis)
    if not isinstance(session, CaptureSession):
        raise PassAPlanRefused("malformed-session")
    if session.state not in (SessionState.OPEN, SessionState.NO_GENESIS):
        # The factory contract is OPEN or NO_GENESIS; a sealed or interrupted session
        # is a malformed collaborator, refused here with no further call on it.
        raise PassAPlanRefused("malformed-session")
    if session.state is SessionState.NO_GENESIS:
        finalization = session.stop(reason=REASON_NO_DURABLE_GENESIS)
        return PassAResult(
            PassAStatus.NO_GENESIS,
            REASON_NO_DURABLE_GENESIS,
            (),
            None,
            finalization,
            session.binding(),
        )
    try:
        return _drive(session, plan, exit_policy, continuation)
    except Exception as original:
        # ``CaptureInterrupted`` is a ``BaseException`` and never reaches here. A
        # session that is still open gets its one X-3 attempt; a sealed one has had it.
        if session.state is SessionState.OPEN:
            _stop_without_masking(session, original)
        raise


def _stop_without_masking(session: CaptureSession, original: Exception) -> None:
    """The one stop attempt for an unexpected error; it never replaces that error.

    A failure of the stop attempt is attached to ``original`` as a note that names
    only the secondary error's type, and the caller's bare ``raise`` then propagates
    ``original`` itself. A ``BaseException`` (``CaptureInterrupted``) is not caught
    here: it must propagate (C-15)."""
    try:
        session.stop(reason=REASON_UNEXPECTED_ERROR)
    except Exception as secondary:
        original.add_note(f"{NOTE_STOP_ATTEMPT_FAILED} {type(secondary).__name__}")


def _validated_plan(
    acts: Sequence[ActRequest],
    exit_policy: ExitPolicy,
    genesis: GenesisRequest,
    session_factory: SessionFactory,
    continuation: ActContinuation | None = None,
) -> tuple[ActRequest, ...]:
    """A private snapshot of the plan, or a refusal, before any effect.

    Only a ``tuple`` or ``list`` is accepted: an iterator or generator is not a
    finite sequence the caller has already fixed, and a list is copied so the
    caller cannot change it mid-pass. Argv, bounds and timeouts are not judged
    here; the mechanism judges them (and stops the pass) on the act itself."""
    if not isinstance(genesis, GenesisRequest):
        raise PassAPlanRefused("malformed-request")
    if type(acts) not in (tuple, list):
        raise PassAPlanRefused("malformed-plan")
    plan = tuple(acts)
    if not plan:
        raise PassAPlanRefused("empty-plan")
    if not all(type(request) is ActRequest for request in plan):
        raise PassAPlanRefused("malformed-plan")
    if not callable(exit_policy):
        raise PassAPlanRefused("malformed-policy")
    if not callable(session_factory):
        raise PassAPlanRefused("malformed-factory")
    if continuation is not None:
        # Only the two lookups are guarded: an error raised inside ``covers`` propagates.
        try:
            covers, permits = continuation.covers, continuation.permits
        except AttributeError:
            raise PassAPlanRefused("malformed-continuation") from None
        if not (callable(covers) and callable(permits) and covers(plan) is True):
            raise PassAPlanRefused("malformed-continuation")
    return plan


def _continuation_stop_reason(
    session: CaptureSession, request: ActRequest, continuation: ActContinuation
) -> str | None:
    """Why the pass must stop after this admitted act, or ``None`` to go on."""
    try:
        evidence = session.admitted_evidence()
    except StoreFailure:
        return REASON_EVIDENCE_UNVERIFIED
    if continuation.permits(request, evidence) is not True:
        return REASON_CONTINUATION_REFUSED
    try:
        session.verify_evidence_bindings()
    except StoreFailure:
        return REASON_EVIDENCE_UNVERIFIED
    return None


def _drive(
    session: CaptureSession,
    plan: tuple[ActRequest, ...],
    exit_policy: ExitPolicy,
    continuation: ActContinuation | None = None,
) -> PassAResult:
    outcomes: list[ActOutcome] = []
    for request in plan:
        outcome = session.run_act(request)
        outcomes.append(outcome)
        if outcome.failure is not None or not outcome.admitted:
            # ``run_act`` has already taken the one stop transition for this act.
            assert outcome.stop is not None
            assert outcome.failure is not None
            return _ended(
                session, PassAStatus.STOPPED, outcome.failure.classification, outcomes,
                outcome.failure, outcome.stop,
            )
        assert outcome.exit is not None
        if exit_policy(request, outcome.exit) is not True:
            finalization = session.stop(
                reason=REASON_UNACCEPTABLE_EXIT, step_or_case_id=request.step_or_case_id
            )
            return _ended(
                session, PassAStatus.STOPPED, REASON_UNACCEPTABLE_EXIT, outcomes, None, finalization
            )
        if continuation is None:
            continue
        reason = _continuation_stop_reason(session, request, continuation)
        if reason is not None:
            finalization = session.stop(reason=reason, step_or_case_id=request.step_or_case_id)
            return _ended(session, PassAStatus.STOPPED, reason, outcomes, None, finalization)
    finalization = session.complete()
    if finalization.x3_outcome == X3_SUCCEEDED and finalization.x4_validity == X4_VALID:
        return _ended(session, PassAStatus.COMPLETED, None, outcomes, None, finalization)
    reason = (
        finalization.x3_failure_classification
        if finalization.x3_outcome != X3_SUCCEEDED
        else finalization.x4_reason
    )
    return _ended(
        session, PassAStatus.FINALIZATION_INCOMPLETE, reason, outcomes, None, finalization
    )


def _ended(
    session: CaptureSession,
    status: PassAStatus,
    reason: str | None,
    outcomes: list[ActOutcome],
    failure: ActFailure | None,
    finalization: FinalizationOutcome,
) -> PassAResult:
    return PassAResult(
        status, reason, tuple(outcomes), failure, finalization, session.binding()
    )


__all__ = [
    "REASON_CONTINUATION_REFUSED",
    "REASON_EVIDENCE_UNVERIFIED",
    "REASON_NO_DURABLE_GENESIS",
    "REASON_UNACCEPTABLE_EXIT",
    "REASON_UNEXPECTED_ERROR",
    "ActContinuation",
    "ExitPolicy",
    "NOTE_STOP_ATTEMPT_FAILED",
    "PassAPlanRefused",
    "PassAResult",
    "PassAStatus",
    "SessionFactory",
    "run_pass_a",
]
