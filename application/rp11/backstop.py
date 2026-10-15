"""RT-4 ``backstop``: BS-1 … BS-4 over the shared cleanup (inventory §5.4).

Each firing of ``<id>-backstop.service`` runs, in order:

* **BS-1** — DI-1 read of the holder's ``ActiveState`` only. ``activating``,
  ``active``, ``deactivating``, ``reloading``: the holder (or its
  ``ExecStopPost``) owns the activation; exit 0 having touched nothing.
  ``inactive``, ``failed`` and a typed not-loaded refusal continue. Anything
  else — an error, a timeout, an unexpected state or refusal — exits non-zero
  having touched nothing. An error is never read as ``inactive``.
* **BS-2 / BS-3** — the greatest exact ``<id>.deact-<k>.json`` record only. If it
  is a valid ``st1-verified`` record, or a valid ``hard-stop`` record that
  ``hard_stop_permits_disarm``, call DI-4 once for this activation's own timer.
  A malformed, unreadable or mismatched latest record never lets an older one
  decide: the firing continues to BS-4. No firing disarms the last automatic
  recovery owner of a *possibly live* grant: BS-3 requires a positive
  non-authorization (for every rule class) and no uninspected or A1-intact rule,
  and the BS-4 bound (below) disarms only once the rule path is observed absent
  *and* a bounded Polkit series positively reports ``not-authorized``.
* **BS-4** — under the per-activation backstop lock, decide the prospective
  attempt ``k`` by CL-0's own rule (1 + the ``<id>-deact-`` names) and count the
  backstop attempts among the exact attempt names. Below the bound, run the
  shared ``CleanupProcedure`` once with trigger ``backstop`` and ``k`` pinned.
  At the bound (``backstop_max`` backstop attempts, or ``k`` > 99) do not enter
  CL: one terminal journal line and exit non-zero. DI-4 is called once only if the
  rule path is observed absent and Polkit then says ``not-authorized``; a rule that is
  present, whose path cannot be observed, or whose absence Polkit does not confirm
  may still authorize the operator, so the timer is kept as the owner
  (``disarm=withheld``) and fires again at its own rate, bounded in resources by
  the terminal journal's size cap and creating no attempt directory.

DI-4 is issued at most once per firing. Any DI-4 result other than ``ok`` or the
pre-mutation ``refused(not-loaded)`` is never retried, never followed by CL or a
record and never reported as a stopped timer. BS never starts, stops or signals
the holder or the capture unit (``RT4.BS.1``).

Reversible choices (pinned by ``tests/test_rp11_backstop.py``):

* backstop attempts are attempt directories whose journal's first line is a
  well-formed ``run-start`` with trigger ``backstop`` **or** that cannot be shown
  to be another trigger's (no/unreadable/torn journal): unknown counts against B;
* the lock and terminal journal is ``<store>/backstop/<id>.journal`` (root,
  ``0644``; directory ``0755``). If it cannot be opened the firing continues
  unlocked, relying on CL-0's exclusive attempt directory and the pinned ``k``;
  if another firing holds it, this one does not enter CL;
* exit codes: 0 holder active or confirmed disarm; CL's own 0 … 5 for BS-4;
  10 holder unobserved; 11 disarm unconfirmed; 12 bound reached (line written);
  13 terminal line unwritable; 14 concurrent backstop; 15 attempts unobservable.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

from application.unit_control import (
    ControlError,
    ControlOk,
    ControlRefused,
    RefusalReason,
    UnitControl,
    UnitProperty,
    holder_unit_name,
)

from .canonical import CanonicalError, parse_canonical
from .cleanup import CleanupOutcome, Terminal
from .journal import JournalKind, JournalSchemaError, attempt_run, check_fields
from .paths import MAX_ATTEMPTS, ActivationPaths
from .pk import PkOutcome
from .ports import ActivationFs, BackstopGuard, GuardMode, JournalSource, RecordStore
from .records import (
    DIR_CLASSES,
    PASS_CLASSES,
    RESIDUAL_CLASSES,
    RULE_CLASSES,
    RecordSchemaError,
    validate_record,
)

HOLDER_OWNS = frozenset({"activating", "active", "deactivating", "reloading"})
HOLDER_GONE = frozenset({"inactive", "failed"})

# Classes of an object that was A1-intact but stayed (it could still be removed) or
# that was not inspected completely (it may be the intact, authorizing grant).
UNINSPECTED = "present-uninspected-unremoved"
A1_INTACT_KEPT = frozenset(
    {"unremovable", "grant-unremovable", "present-nonempty-unremoved", UNINSPECTED}
)
RULE_BLOCKS_DISARM = frozenset({"removed-unconfirmed", "grant-unremovable", UNINSPECTED})
GRANT_UNINSPECTED = "kept-uninspected"
NOT_AUTHORIZED = PkOutcome.NOT_AUTHORIZED.value

TERMINAL_SCHEMA = "rp11-backstop-terminal/1"
NON_BACKSTOP_TRIGGERS = frozenset({"stop-post", "attest"})


class BsTerminal(str, Enum):
    HOLDER_ACTIVE = "holder-active"
    DISARMED = "disarmed"
    CLEANUP = "cleanup"
    HOLDER_UNOBSERVED = "holder-unobserved"
    DISARM_UNCONFIRMED = "disarm-unconfirmed"
    BOUND_REACHED = "bound-reached"
    TERMINAL_UNWRITABLE = "terminal-unwritable"
    CONCURRENT_BACKSTOP = "concurrent-backstop"
    ATTEMPTS_UNOBSERVABLE = "attempts-unobservable"


_EXIT = {
    BsTerminal.HOLDER_ACTIVE: 0,
    BsTerminal.DISARMED: 0,
    BsTerminal.HOLDER_UNOBSERVED: 10,
    BsTerminal.DISARM_UNCONFIRMED: 11,
    BsTerminal.BOUND_REACHED: 12,
    BsTerminal.TERMINAL_UNWRITABLE: 13,
    BsTerminal.CONCURRENT_BACKSTOP: 14,
    BsTerminal.ATTEMPTS_UNOBSERVABLE: 15,
}


class Branch(str, Enum):
    BS2 = "bs-2"
    BS3 = "bs-3"
    BS4 = "bs-4"


class BoundReason(str, Enum):
    ATTEMPT_LIMIT = "attempt-limit"  # prospective k > 99
    BACKSTOP_MAX = "backstop-max"  # B backstop attempts exist


DISARM_WITHHELD = "withheld"  # the timer stays: a rule that may authorize is still present


def disarm_class(result) -> str:
    """The typed DI-4 outcome as a token: never a claim beyond what was confirmed."""
    if isinstance(result, ControlOk):
        return "stopped"
    if isinstance(result, ControlRefused):
        return "not-loaded" if result.reason is RefusalReason.NOT_LOADED else "refused"
    if isinstance(result, ControlError) and result.effect_not_confirmed:
        return "unconfirmed"
    return "error"


# ---------------------------------------------------------------------------
# BS-2 / BS-3 — pure decisions on the latest record
# ---------------------------------------------------------------------------


def hard_stop_permits_disarm(doc: dict) -> bool:
    """BS-3: the record's own classes prove no A1-intact activation object remains,
    the rule is not ``removed-unconfirmed``, ``grant-unremovable`` or uninspected,
    and — for *every* rule class — Polkit positively reported ``not-authorized``
    after the cleanup (``grant_check.after_cleanup`` and ``pk.outcome`` both).

    A class the record does not state (``absent`` or outside its enumeration) is
    not proof, so it blocks the disarm. A rule's absence or successful removal is
    not proof either: ``authorized``, ``unconfirmed``, absent or any other result
    leaves a possibly live grant and its recovery owner. A kept damaged or foreign
    rule does not block by itself, but needs the same positive result."""
    try:
        rule = doc["active_rule"]["class"]
        pass_class = doc["pass_config"]["class"]
        grant_id_class = doc["grant_identity"]["grant_id_class"]
        grr_class = doc["grant_identity"]["cl_g"]
        after_cleanup = doc["grant_check"]["after_cleanup"]
        pk_outcome = doc["pk"]["outcome"]
        directory_classes = [entry["class"] for entry in doc["directories"]]
        residual_classes = [entry["class"] for entry in doc["residual"]]
    except (KeyError, TypeError):
        return False
    if rule not in RULE_CLASSES or rule in RULE_BLOCKS_DISARM:
        return False
    if grr_class == GRANT_UNINSPECTED:
        return False
    if after_cleanup != NOT_AUTHORIZED or pk_outcome != NOT_AUTHORIZED:
        return False  # a rule's absence or removal is never proof: Polkit must say so
    if pass_class not in PASS_CLASSES:
        return False
    if grant_id_class not in PASS_CLASSES:
        return False
    if any(klass not in DIR_CLASSES for klass in directory_classes):
        return False
    if any(klass not in RESIDUAL_CLASSES for klass in residual_classes):
        return False
    classes = [pass_class, grant_id_class, *directory_classes, *residual_classes]
    return not any(type(c) is not str or c in A1_INTACT_KEPT for c in classes)


def branch_for_record(data: bytes | None, *, activation_id: str, k: int) -> Branch:
    """BS-2/BS-3 for the bytes of the greatest record ``deact-<k>``. Anything
    unreadable, non-canonical, invalid or naming another activation/attempt is BS-4."""
    if data is None:
        return Branch.BS4
    try:
        doc = parse_canonical(data)
        validate_record(doc)
        if doc["kind"] != "deact" or doc["activation_id"] != activation_id or doc["attempt"] != k:
            return Branch.BS4
        if doc["outcome"] == "st1-verified":
            return Branch.BS2
        if doc["outcome"] == "hard-stop" and hard_stop_permits_disarm(doc):
            return Branch.BS3
    except (CanonicalError, RecordSchemaError):
        return Branch.BS4
    except Exception:  # noqa: BLE001 - defence in depth: a record that escapes the validator is BS-4
        return Branch.BS4
    return Branch.BS4


# ---------------------------------------------------------------------------
# BS-4 — the bound
# ---------------------------------------------------------------------------


def exact_attempts(names: tuple[str, ...], activation_id: str) -> tuple[int, ...]:
    pattern = re.compile(re.escape(activation_id) + r"-deact-([1-9][0-9]?)-evidence")
    found = []
    for name in names:
        match = pattern.fullmatch(name)
        if match:
            found.append(int(match.group(1)))
    return tuple(sorted(found))


def is_backstop_attempt(data: bytes | None, *, activation_id: str, k: int) -> bool:
    """True unless the journal's first line is a well-formed ``run-start`` of
    this attempt naming a non-backstop trigger (unknown counts against B)."""
    if data is None:
        return True
    first, newline, _rest = data.partition(b"\n")
    if not newline:
        return True
    try:
        entry = parse_canonical(first + b"\n")
    except CanonicalError:
        return True
    if type(entry) is not dict:
        return True
    fields = {name: value for name, value in entry.items() if name not in {"seq", "prev", "run", "op"}}
    if entry.get("seq") != 1 or entry.get("op") != "run-start" or entry.get("run") != attempt_run(activation_id, k):
        return True
    try:
        check_fields(JournalKind.ATTEMPT, "run-start", fields)
    except JournalSchemaError:
        return True
    return fields["trigger"] not in NON_BACKSTOP_TRIGGERS


# ---------------------------------------------------------------------------
# the procedure
# ---------------------------------------------------------------------------


@dataclass
class BackstopOutcome:
    terminal: BsTerminal
    lines: list[str] = field(default_factory=list)
    cleanup: CleanupOutcome | None = None
    disarm_calls: int = 0

    @property
    def exit_code(self) -> int:
        if self.terminal is BsTerminal.CLEANUP:
            assert self.cleanup is not None
            return self.cleanup.terminal.exit_code
        return _EXIT[self.terminal]


class BackstopProcedure:
    """One firing. ``limits`` returns ``(backstop_max, journal_max_bytes)`` from the
    H-1 parameters (defaults if the authority is invalid; never from a caller);
    ``cleanup(k, holder_state)`` runs the shared CL once with ``k`` pinned."""

    def __init__(
        self,
        paths: ActivationPaths,
        *,
        units: UnitControl,
        records: RecordStore,
        fs: ActivationFs,
        journals: JournalSource,
        guard: BackstopGuard,
        limits: Callable[[], tuple[int, int]],
        cleanup: Callable[[int, str], CleanupOutcome],
        grant_check: Callable[[], PkOutcome],
    ) -> None:
        self._paths = paths
        self._id = paths.activation_id
        self._units = units
        self._records = records
        self._fs = fs
        self._journals = journals
        self._guard = guard
        self._limits = limits
        self._cleanup = cleanup
        self._grant_check = grant_check
        self._disarms = 0

    def run(self) -> BackstopOutcome:
        holder_state = self._bs1()
        if isinstance(holder_state, BackstopOutcome):
            return holder_state
        decided = self._bs2_bs3()
        if decided is not None:
            return decided
        mode = self._guard.acquire()
        try:
            if mode is GuardMode.BUSY:
                return self._done(BsTerminal.CONCURRENT_BACKSTOP, "")
            return self._bs4(holder_state, mode)
        finally:
            self._guard.release()

    # BS-1 -------------------------------------------------------------------

    def _bs1(self) -> str | BackstopOutcome:
        read = self._units.read_unit(holder_unit_name(self._id), (UnitProperty.ACTIVE_STATE,))
        if isinstance(read, ControlRefused) and read.reason is RefusalReason.NOT_LOADED:
            return "not-loaded"
        if isinstance(read, ControlOk):
            state = read.value.get(UnitProperty.ACTIVE_STATE) if hasattr(read.value, "get") else None
            if type(state) is str and state in HOLDER_OWNS:
                return self._done(BsTerminal.HOLDER_ACTIVE, f"state={state}")
            if type(state) is str and state in HOLDER_GONE:
                return state
            return self._done(BsTerminal.HOLDER_UNOBSERVED, "read=unexpected-state")
        kind = "refused" if isinstance(read, ControlRefused) else "error"
        return self._done(BsTerminal.HOLDER_UNOBSERVED, f"read={kind}")

    # BS-2 / BS-3 ---------------------------------------------------------------

    def _bs2_bs3(self) -> BackstopOutcome | None:
        attempts = self._records.deact_attempts(self._id)
        if not attempts:
            return None
        k = attempts[-1]
        data = self._records.read(self._paths.deact_record_name(k))
        branch = branch_for_record(data, activation_id=self._id, k=k)
        if branch is Branch.BS4:
            return None
        result = self._disarm()
        outcome = disarm_class(result)
        detail = f"branch={branch.value} k={k} disarm={outcome}"
        if outcome in {"stopped", "not-loaded"}:
            return self._done(BsTerminal.DISARMED, detail)
        return self._done(BsTerminal.DISARM_UNCONFIRMED, detail)

    # BS-4 ---------------------------------------------------------------------

    def _bs4(self, holder_state: str, mode: GuardMode) -> BackstopOutcome:
        backstop_max, journal_cap = self._limits()
        names = self._fs.list_prefixed(self._paths.layout.var_tmp, self._paths.attempt_prefix)
        if names is None:
            return self._done(BsTerminal.ATTEMPTS_UNOBSERVABLE, "")
        k = len(names) + 1  # CL-0's own rule: every <id>-deact- name moves k
        backstop = sum(
            is_backstop_attempt(
                self._journals.read_journal(
                    self._paths.attempt_dir(j),
                    max_bytes=journal_cap,
                    dir_uid=self._paths.layout.owner.uid,
                    dir_mode=0o755,
                ),
                activation_id=self._id,
                k=j,
            )
            for j in exact_attempts(names, self._id)
        )
        if k > MAX_ATTEMPTS:
            return self._terminal(BoundReason.ATTEMPT_LIMIT, mode)
        if backstop >= backstop_max:
            return self._terminal(BoundReason.BACKSTOP_MAX, mode)
        outcome = self._cleanup(k, holder_state)
        if outcome.terminal in (Terminal.CONCURRENT_DEACT, Terminal.RECORD_UNPUBLISHED):
            # Lost an attempt or publication race: re-observe once and take only a
            # branch the same validation admits (never an older record's).
            decided = self._bs2_bs3()
            if decided is not None:
                decided.cleanup = outcome
                decided.lines.append(outcome.diagnostic(self._id))
                return decided
        result = BackstopOutcome(BsTerminal.CLEANUP, cleanup=outcome, disarm_calls=self._disarms)
        result.lines.append(
            f"rp11-bs cleanup {self._id} k={k} trigger=backstop lock={mode.value} "
            f"terminal={outcome.terminal.value}"
        )
        result.lines.append(outcome.diagnostic(self._id))
        return result

    def _terminal(self, reason: BoundReason, mode: GuardMode) -> BackstopOutcome:
        # The bound stops *attempts*, not the recovery owner of a live grant: the timer
        # is disarmed only when the rule path is observed absent *and* a bounded Polkit
        # series then positively reports ``not-authorized``. Absence of the path alone
        # proves nothing (Polkit may still have the rule's effect loaded).
        if self._fs.observe(self._paths.rule) is None and self._not_authorized():
            outcome = disarm_class(self._disarm())
        else:
            outcome = DISARM_WITHHELD
        fields = {
            "schema": TERMINAL_SCHEMA,
            "op": "backstop-terminal",
            "activation_id": self._id,
            "reason": reason.value,
            "disarm": outcome,
        }
        detail = f"reason={reason.value} disarm={outcome}"
        if mode is not GuardMode.HELD:
            return self._done(BsTerminal.TERMINAL_UNWRITABLE, detail)
        try:
            self._guard.append_terminal(fields)
        except Exception:  # noqa: BLE001 - any failure: no line claimed, still non-zero
            return self._done(BsTerminal.TERMINAL_UNWRITABLE, detail)
        return self._done(BsTerminal.BOUND_REACHED, detail)

    # helpers ------------------------------------------------------------------

    def _not_authorized(self) -> bool:
        """One bounded ``seek-not-authorized`` series; anything but a positive
        ``not-authorized`` (an error, a raise, a malformed result) is not one."""
        try:
            return self._grant_check() is PkOutcome.NOT_AUTHORIZED
        except Exception:  # noqa: BLE001 - an unreadable authorization state is never "not authorized"
            return False

    def _disarm(self):
        """DI-4 for this activation's own derived timer, at most once per firing."""
        if self._disarms:
            raise AssertionError("DI-4 is issued at most once per firing")
        self._disarms += 1
        return self._units.disarm_backstop(self._id)

    def _done(self, terminal: BsTerminal, detail: str) -> BackstopOutcome:
        line = f"rp11-bs {terminal.value} {self._id}" + (f" {detail}" if detail else "")
        return BackstopOutcome(terminal, [line], disarm_calls=self._disarms)
