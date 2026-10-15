"""CL: the shared activation cleanup (inventory §4.16), for ``stop-post`` and ``backstop``.

Order (R8 §5.7, §8.1): CL-G; CL-0 (lock to λ, attempt directory, journal,
``run-start``, the held ``cl-g`` line); CL-1; CL-2; CL-3; CL-4; CL-5; CL-5b
(``grant.id`` and K last); CL-6; CL-7. Grant-priority mode GP-R3 replaces the
evidence of every later step when a journal create, append or flush fails.

Invariants this module keeps, each covered by a test:

* CL-G runs first: before the authority files, the lock, any ``ext4`` access,
  any spawn and any Polkit call; it only reads ``grant.id`` and the rule on
  tmpfs and removes an A1-intact rule.
* Only an object that is A1-intact against a durable identity, and A1-intact
  again on a descriptor immediately before removal, is removed. A0, damaged,
  foreign, unverified and other-boot objects are kept and reported.
* An activation rule whose inspection failed (a lookup, ``fstat``, content read or
  attribute listing) is neither damaged nor foreign nor intact: it is
  ``present-uninspected-unremoved`` (GRR ``kept-uninspected``), kept, and it can
  still authorize the operator, so a record that states it never lets BS-3 disarm
  the backstop timer.
* An existing ``act`` record is never rewritten, and its digest is chained into a
  deactivation record only after it parses canonically, validates and names this
  activation (attempt 0); otherwise CL-7 is ``record-unpublished``.
* K without an identity line (the holder ended before its ACT journal existed)
  is S0 only if it is exactly the empty root ``0700`` K that AM-0 creates; it is
  kept, reported and does not block ``st1-verified``. Every other K is A0.
* Every removal outside GP-R3 is write-ahead: ``remove-intent`` is durable
  before ``unlinkat``, ``removed`` after it.
* ``st1-verified`` requires every class to be clean, Polkit *not authorized*
  for the operator (the CL-4 series), the recomputed baseline equal to the H-1
  record's, the capture unit not active and the record published. A missing or
  malformed fact can only make the outcome worse.
"""

from __future__ import annotations

import errno as errno_module
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from application.unit_control import (
    CAPTURE_UNIT,
    ControlOk,
    UnitControl,
    UnitProperty,
    UnitVerb,
)

from . import baseline as baseline_module
from .attribution import (
    FORBIDDEN_XATTRS,
    Attribution,
    Identity,
    ObjectKind,
    Observed,
    Owner,
    classify,
    classify_file,
)
from .authority import AUTHORITY_LIMIT, Authority, AuthorityError, Params, load_authority
from .canonical import ABSENT, CanonicalError, canonical_bytes, parse_canonical
from .evidence import INVALID_ACT, ActEvidence, PriorRemovals, act_evidence
from .journal import JournalKind, ParsedJournal, attempt_run, consume_run, parse_journal
from .paths import MAX_ATTEMPTS, ActivationPaths
from .pk import PROCEDURE, PkMode, PkOutcome, PkResult, PkSeries, unconfirmed_without_subject
from .ports import (
    ActivationFs,
    AttemptStore,
    BaselineSource,
    EvidenceSink,
    EvidenceWriteError,
    HostFacts,
    JournalSource,
    LockMode,
    LockPort,
    LockState,
    RecordStore,
    Removal,
    RemovalOutcome,
)
from .records import SCHEMA, validate_record

ACTIVE_STATES = frozenset({"active", "activating", "deactivating", "reloading"})
RULE_OK = frozenset(
    {"removed-verified", "never-linked", "removed-earlier", "absent-before-removal", "cleared-by-boot"}
)
PASS_OK = frozenset({"removed", "never-linked", "removed-earlier", "absent-before-removal", "cleared-by-boot"})
DIR_OK = frozenset(
    {
        "removed",
        "never-created",
        "removed-earlier",
        "absent-before-removal",
        "cleared-by-boot",
        "pre-existing-kept",
        "s0-kept",
    }
)
RULE_UNINSPECTED = "present-uninspected-unremoved"
GRANT_ID_MAX_BYTES = 4_096
K_S0 = "s0-kept"


class Trigger(str, Enum):
    STOP_POST = "stop-post"
    BACKSTOP = "backstop"


class GrrOutcome(str, Enum):
    REMOVED = "removed"
    ABSENT = "absent"
    KEPT_DAMAGED = "kept-damaged"
    KEPT_FOREIGN = "kept-foreign"
    KEPT_UNINSPECTED = "kept-uninspected"  # present; inspection did not establish what it is
    UNREMOVABLE = "unremovable"
    IDENTITY_UNAVAILABLE = "identity-unavailable"


class Terminal(str, Enum):
    """The accepted terminal classes and the narrower fail-closed ones. Exit codes
    are this implementation's choice (Q4-2): only ``st1-verified`` exits 0."""

    ST1_VERIFIED = "st1-verified"
    HARD_STOP = "hard-stop"
    UNIT_STILL_ACTIVE = "unit-still-active"
    RECORD_UNPUBLISHED = "record-unpublished"
    EVIDENCE_UNWRITABLE = "evidence-unwritable"
    CONCURRENT_DEACT = "concurrent-deact"

    @property
    def exit_code(self) -> int:
        return {
            Terminal.ST1_VERIFIED: 0,
            Terminal.HARD_STOP: 1,
            Terminal.UNIT_STILL_ACTIVE: 2,
            Terminal.RECORD_UNPUBLISHED: 3,
            Terminal.EVIDENCE_UNWRITABLE: 4,
            Terminal.CONCURRENT_DEACT: 5,
        }[self]


@dataclass(frozen=True)
class Invocation:
    """What the first image established: validated operands and provenance."""

    activation_id: str
    a2_sha256: str
    trigger: Trigger
    parent_pid: int
    invocation_id: str  # 32 lowercase hex or "absent"; diagnostic only
    # The holder's state as this role knows it: ``deactivating`` for its own
    # ExecStopPost; for ``backstop`` the BS-1 observation (inactive/failed/not-loaded).
    holder_state: str = "deactivating"

    @property
    def holder_invocation_id(self) -> str:
        """Only ``stop-post`` runs inside the holder's invocation; a backstop
        firing's ``INVOCATION_ID`` is its own service's, never the holder's."""
        return self.invocation_id if self.trigger is Trigger.STOP_POST else ABSENT


@dataclass
class CleanupOutcome:
    terminal: Terminal
    k: int | None
    rule_class: str
    pass_class: str
    dir_classes: list[str]
    pk_outcome: str
    failure: str
    record: dict | None = None
    record_sha256: str | None = None

    def diagnostic(self, activation_id: str) -> str:
        """One fixed line for the system journal: classes and tokens, no values.

        Under GP-R3 it is the accepted GP-7 literal (H-DIAG.1)."""
        dirs = ",".join(self.dir_classes) or "none"
        if self.terminal is Terminal.EVIDENCE_UNWRITABLE:
            return (
                f"rp11-cl grant-priority {activation_id} rule={self.rule_class} "
                f"pk={self.pk_outcome} pass_config={self.pass_class} dirs={dirs}"
            )
        return (
            f"rp11-cl {self.terminal.value} {activation_id} k={self.k or 'absent'} "
            f"rule={self.rule_class} pk={self.pk_outcome} pass_config={self.pass_class} "
            f"dirs={','.join(self.dir_classes) or 'none'} failure={self.failure}"
        )


class Services(Protocol):
    """Collaborators whose deadlines come from the H-1 parameters."""

    def units(self, params: Params) -> UnitControl: ...

    def pk(self, params: Params) -> PkSeries: ...

    def baseline(self, params: Params) -> BaselineSource: ...


@dataclass
class _Ports:
    fs: ActivationFs
    journals: JournalSource
    attempts: AttemptStore
    records: RecordStore
    lock: LockPort
    host: HostFacts
    services: Services


@dataclass
class _State:
    """Everything one run learns. Written by the steps, read by CL-6/CL-7."""

    start_utc: str = ABSENT
    boot_at_start: str | None = None
    grr: GrrOutcome = GrrOutcome.IDENTITY_UNAVAILABLE
    grr_errno: int = 0
    grant_identity: Identity | None = None
    grant_boot_ok: bool = False
    authority: Authority | None = None
    authority_failure: str = ""
    params: Params = field(default_factory=Params)
    lock: LockState | None = None
    k: int | None = None
    sink: EvidenceSink | None = None
    gp: str = ""  # GP-R3 entry ("E-a", "E-b", "E-c"), empty while journaled
    rule_removal_durable: bool = False
    act_parsed: ParsedJournal | None = None
    act: ActEvidence = INVALID_ACT
    earlier: list[tuple[str, ParsedJournal | None]] = field(default_factory=list)
    consume: ParsedJournal | None = None
    prior: PriorRemovals = field(default_factory=PriorRemovals)
    same_boot: bool = False
    run_fstype: str | None = None
    capture: dict | None = None
    rule_class: str = ABSENT
    rule_identity: Identity | None = None
    rule_removed_here: bool = False
    grant_removed_utc: str = ABSENT
    conflict: bool = False
    pk: PkResult | None = None
    pass_class: str = ABSENT
    pass_identity: Identity | None = None
    directories: list[dict] = field(default_factory=list)
    grant_id_class: str = ABSENT
    s0: list[str] = field(default_factory=list)
    residual: list[dict] = field(default_factory=list)
    st1_checks: dict[str, bool] = field(default_factory=dict)
    baseline_observed: str = ABSENT
    baseline_difference: str = ABSENT
    unit_at_end: str = ABSENT
    failures: list[tuple[str, str]] = field(default_factory=list)


class CleanupProcedure:
    def __init__(
        self,
        invocation: Invocation,
        paths: ActivationPaths,
        *,
        fs: ActivationFs,
        journals: JournalSource,
        attempts: AttemptStore,
        records: RecordStore,
        lock: LockPort,
        host: HostFacts,
        services: Services,
        tool_sha256: str = ABSENT,
        attempt: int | None = None,
    ) -> None:
        if invocation.activation_id != paths.activation_id:
            raise ValueError("paths belong to another activation")
        if attempt is not None:
            paths.attempt_dir(attempt)  # 1 … 99, else ValueError
        # A caller that already decided k (the backstop bound, BS-4) pins it: CL-0
        # then owns exactly that attempt or none (``concurrent-deact``).
        self._attempt = attempt
        self._inv = invocation
        self._paths = paths
        self._owner = paths.layout.owner
        self._p = _Ports(fs, journals, attempts, records, lock, host, services)
        self._units: UnitControl | None = None
        self._tool_sha256 = tool_sha256
        self._s = _State()

    # ------------------------------------------------------------------
    # public
    # ------------------------------------------------------------------

    def run(self) -> CleanupOutcome:
        s = self._s
        s.start_utc = self._p.host.utc_now()
        s.boot_at_start = self._p.host.boot_id()
        if s.boot_at_start is None:
            self._fail("CL-0", "observation-failed")
        self._cl_g()
        self._read_authority()
        self._units = self._p.services.units(s.params)
        try:
            early = self._cl_0()
            if early is not None:
                return early
            self._cl_1()
            self._cl_2()
            self._cl_3()
            self._cl_4()
            self._cl_5()
            self._cl_5b()
            self._cl_6()
            return self._cl_7()
        finally:
            self._p.lock.release()

    # ------------------------------------------------------------------
    # CL-G — grant removal by grant.id, before anything slower
    # ------------------------------------------------------------------

    def _cl_g(self) -> None:
        s = self._s
        identity = self._grant_identity()
        if identity is None:
            s.grr = GrrOutcome.IDENTITY_UNAVAILABLE
            return
        s.grant_identity = identity
        removal = self._p.fs.remove(
            self._paths.rule, identity, directory=False, before_unlink=lambda _o: None
        )
        s.grr, s.grr_errno = grr_outcome(removal)
        if s.grr is GrrOutcome.REMOVED:
            s.grant_removed_utc = self._p.host.utc_now()

    def _grant_identity(self) -> Identity | None:
        """GRR-1: ``grant.id`` as a root-only ``0600`` file holding one canonical line."""
        data = self._p.fs.read_root_file(
            self._paths.grant_id, max_bytes=GRANT_ID_MAX_BYTES, mode=0o600
        )
        if data is None:
            return None
        try:
            doc = parse_canonical(data)
        except CanonicalError:
            return None
        keys = {"path", "dev", "ino", "sha256", "size", "mode", "uid", "gid", "boot_id"}
        if type(doc) is not dict or set(doc) != keys:
            return None
        ints = ("dev", "ino", "size", "mode", "uid", "gid")
        if any(type(doc[name]) is not int or doc[name] < 0 for name in ints):
            return None
        if (
            doc["path"] != self._paths.rule
            or doc["mode"] != 0o644
            or (doc["uid"], doc["gid"]) != (self._owner.uid, self._owner.gid)
            or type(doc["sha256"]) is not str
            or len(doc["sha256"]) != 64
        ):
            return None
        # /run is boot-scoped: an identity written in another boot names nothing now.
        if doc["boot_id"] != self._s.boot_at_start:
            return None
        self._s.grant_boot_ok = True
        return Identity(
            path=doc["path"],
            kind=ObjectKind.FILE,
            dev=doc["dev"],
            ino=doc["ino"],
            mode=doc["mode"],
            sha256=doc["sha256"],
            size=doc["size"],
        )

    # ------------------------------------------------------------------
    # authority: A-2 then H-1, after CL-G (they live on ext4)
    # ------------------------------------------------------------------

    def _read_authority(self) -> None:
        s = self._s
        try:
            s.authority = load_authority(
                self._p.fs,
                self._paths,
                a2_sha256=self._inv.a2_sha256,
                activation_id=self._inv.activation_id,
            )
            s.params = s.authority.h1.params
        except AuthorityError as exc:
            s.authority = None
            s.authority_failure = str(exc)
            self._fail("CL-1", "invalid-authority")

    # ------------------------------------------------------------------
    # CL-0 — lock, attempt directory, journal, run-start, cl-g line
    # ------------------------------------------------------------------

    def _cl_0(self) -> CleanupOutcome | None:
        s = self._s
        s.lock = self._p.lock.acquire(s.params.lock_wait_ms)
        names = self._p.fs.list_prefixed(self._paths.layout.var_tmp, self._paths.attempt_prefix)
        if names is None:
            self._enter_gp("E-a")
            return None
        k = len(names) + 1
        if self._attempt is not None and k != self._attempt:
            return self._concurrent()  # another attempt took a name since k was decided
        if k > MAX_ATTEMPTS:
            self._fail("CL-0", "evidence-unwritable")
            self._enter_gp("E-a")
            return None
        s.k = k
        try:
            s.sink = self._p.attempts.create(k)
        except FileExistsError:
            return self._concurrent()
        except EvidenceWriteError:
            self._enter_gp("E-a")
            return None
        lock_object = s.lock.object
        self._append(
            "run-start",
            {
                "trigger": self._inv.trigger.value,
                "boot_id": s.boot_at_start or "00000000-0000-0000-0000-000000000000",
                "holder_state": self._inv.holder_state,
                "lock": {
                    "object": identity_doc(lock_object),
                    "mode": s.lock.mode.value,
                    "wait_ms": s.lock.wait_ms,
                },
                "helper": {"role": self._inv.trigger.value, "tool_sha256": self._tool_sha256},
                "provenance": {
                    "parent_pid": self._inv.parent_pid,
                    "invocation_id": self._inv.invocation_id,
                },
            },
            entry="E-a",
        )
        self._append("cl-g", {"outcome": s.grr.value, "errno": s.grr_errno}, entry="E-b")
        return None

    def _concurrent(self) -> CleanupOutcome:
        """EEXIST: another attempt owns k. Act on nothing further (CL-G already ran)."""
        return CleanupOutcome(
            terminal=Terminal.CONCURRENT_DEACT,
            k=None,
            rule_class=ABSENT,
            pass_class=ABSENT,
            dir_classes=[],
            pk_outcome=ABSENT,
            failure="concurrent-deact",
        )

    # ------------------------------------------------------------------
    # CL-1 — journals and boot scoping
    # ------------------------------------------------------------------

    def _cl_1(self) -> None:
        s = self._s
        cap = s.params.journal_max_bytes
        operator_uid = s.authority.h1.operator.uid if s.authority else None
        act_data = (
            self._p.journals.read_journal(
                self._paths.act_dir, max_bytes=cap, dir_uid=operator_uid, dir_mode=0o700
            )
            if operator_uid is not None
            else None
        )
        if act_data is not None:
            s.act_parsed = parse_journal(act_data, kind=JournalKind.ACT, run=self._inv.activation_id)
        evidence = act_evidence(s.act_parsed)
        if evidence.valid and s.authority is not None:
            pins = s.authority.pins
            if (
                evidence.a2_sha256 != pins.sha256
                or evidence.pass_config_sha256 != pins.pass_config_sha256
                or evidence.staged_rule_sha256 != pins.staged_rule_sha256
                or evidence.boot_id != pins.boot_id
            ):
                evidence = INVALID_ACT
        elif s.authority is None:
            evidence = INVALID_ACT
        if not evidence.valid:
            self._fail("CL-1", "invalid-journal")
        s.act = evidence
        upto = (s.k or MAX_ATTEMPTS + 1) - 1
        for j in range(1, upto + 1):
            data = self._p.journals.read_journal(
                self._paths.attempt_dir(j), max_bytes=cap, dir_uid=self._owner.uid, dir_mode=0o755
            )
            parsed = (
                parse_journal(
                    data, kind=JournalKind.ATTEMPT, run=attempt_run(self._inv.activation_id, j)
                )
                if data is not None
                else None
            )
            s.earlier.append((self._paths.attempt_dir(j), parsed))
        data = self._p.journals.read_journal(
            self._paths.consume_dir, max_bytes=cap, dir_uid=self._owner.uid, dir_mode=0o755
        )
        if data is not None:
            s.consume = parse_journal(
                data, kind=JournalKind.CONSUME, run=consume_run(self._inv.activation_id)
            )
        s.prior = PriorRemovals.from_journals(
            [p for _d, p in s.earlier if p is not None] + ([s.consume] if s.consume else [])
        )
        s.run_fstype = self._p.host.run_fstype()
        s.same_boot = evidence.valid and evidence.boot_id == s.boot_at_start

    # ------------------------------------------------------------------
    # CL-2 — capture-unit state
    # ------------------------------------------------------------------

    def _cl_2(self) -> None:
        s = self._s
        read = self._units.read_unit(
            CAPTURE_UNIT,
            (UnitProperty.ACTIVE_STATE, UnitProperty.INACTIVE_ENTER_TIMESTAMP_MONOTONIC),
        )
        if isinstance(read, ControlOk):
            s.capture = {
                "active_state": str(read.value[UnitProperty.ACTIVE_STATE]),
                "inactive_enter_us": int(read.value[UnitProperty.INACTIVE_ENTER_TIMESTAMP_MONOTONIC]),
            }
            if s.capture["active_state"] in ACTIVE_STATES:
                self._fail("CL-2", "unit-still-active")
        else:
            s.capture = None
            self._fail("CL-2", "observation-failed")

    # ------------------------------------------------------------------
    # CL-3 — the rule
    # ------------------------------------------------------------------

    def _rule_journal_identity(self) -> Identity | None:
        s = self._s
        if not s.same_boot:
            return None
        identity = s.act.file(self._paths.rule)
        if identity is None or self._paths.rule not in s.act.grant_paths:
            return None
        if identity.sha256 != s.act.staged_rule_sha256:
            return None
        return identity

    def _cl_3(self) -> None:
        s = self._s
        journal_identity = self._rule_journal_identity()
        s.rule_identity = s.grant_identity or journal_identity
        if s.grant_identity and journal_identity:
            s.conflict = (
                s.grant_identity.dev,
                s.grant_identity.ino,
                s.grant_identity.sha256,
            ) != (journal_identity.dev, journal_identity.ino, journal_identity.sha256)
        if s.grr is GrrOutcome.REMOVED:
            s.rule_class = "removed-earlier"
            return
        if s.grr is GrrOutcome.KEPT_DAMAGED:
            s.rule_class = "present-damaged-unremoved"
            return
        if s.grr is GrrOutcome.KEPT_FOREIGN:
            s.rule_class = "present-foreign-unremoved"
            return
        if s.grr is GrrOutcome.KEPT_UNINSPECTED:
            s.rule_class = RULE_UNINSPECTED
            return
        if s.grr is GrrOutcome.UNREMOVABLE:
            s.rule_class = "grant-unremovable"
            return
        if s.grr is GrrOutcome.ABSENT:
            s.rule_class = self._absent_class(self._paths.rule, s.rule_identity, rule=True)
            return
        # identity-unavailable: the accepted journal-based removal (G-R1).
        observed = self._p.fs.observe(self._paths.rule)
        if observed is None:
            s.rule_class = self._absent_class(self._paths.rule, journal_identity, rule=True)
            return
        attribution = self._attribute(journal_identity, observed)
        if attribution is not Attribution.A1_INTACT:
            s.rule_class = _kept_class(attribution, rule=True)
            return
        removal = self._remove(self._paths.rule, journal_identity, directory=False)
        if removal.outcome is RemovalOutcome.REMOVED:
            s.rule_removed_here = True
            s.grant_removed_utc = self._p.host.utc_now()
            s.rule_removal_durable = self._append(
                "removed", {"path": self._paths.rule}, entry="E-b"
            )
            s.rule_class = "removed-unconfirmed"  # CL-4 decides
        elif removal.outcome is RemovalOutcome.ABSENT:
            s.rule_class = "absent-before-removal"
        elif removal.outcome is RemovalOutcome.UNREMOVABLE:
            s.rule_class = "grant-unremovable"
            self._append("remove-failed", {"path": self._paths.rule, "errno": removal.errno}, entry="E-b")
        else:
            s.rule_class = _kept_class(removal.attribution, rule=True)

    def _absent_class(self, path: str, identity: Identity | None, *, rule: bool = False) -> str:
        s = self._s
        if path in s.prior.paths or (rule and s.same_boot and s.act.igr_removed):
            return "removed-earlier"
        if s.act.valid and not s.same_boot and s.run_fstype == "tmpfs" and self._act_any(path):
            return "cleared-by-boot"
        if identity is not None or self._act_any(path) is not None:
            return "absent-before-removal"
        return "never-linked"

    def _act_any(self, path: str) -> Identity | None:
        """The ``ACT`` journal's identity for ``path`` in whatever boot it was written."""
        act = self._s.act
        if act.lock is not None and act.lock.path == path:
            return act.lock
        return act.file(path) or act.directory(path)

    # ------------------------------------------------------------------
    # CL-4 — the rule is gone and Polkit says *not authorized*
    # ------------------------------------------------------------------

    def _cl_4(self) -> None:
        s = self._s
        absent_now = self._p.fs.observe(self._paths.rule) is None
        if s.authority is None:
            s.pk = unconfirmed_without_subject(PkMode.SEEK_NOT_AUTHORIZED, UnitVerb.START)
        else:
            series = self._p.services.pk(s.params)
            s.pk = series.run(s.authority.h1.operator, UnitVerb.START, PkMode.SEEK_NOT_AUTHORIZED)
        for child in s.pk.children:
            self._append("child", {"entry": child}, entry="E-c")
        not_authorized = s.pk.outcome is PkOutcome.NOT_AUTHORIZED
        if s.rule_removed_here:
            verified = (
                s.rule_removal_durable
                and not s.gp
                and absent_now
                and not_authorized
                and s.act.positive_control
            )
            s.rule_class = "removed-verified" if verified else "removed-unconfirmed"
        if not not_authorized:
            self._fail("CL-4", "grant-unconfirmed")
        self._append(
            "grant-check",
            {
                "verb": "start",
                "mode": s.pk.mode.value,
                "outcome": s.pk.outcome.value,
                "reason": s.pk.reason,
                "calls": s.pk.calls,
            },
            entry="E-c",
        )
        self._append(
            "classified", {"object": "rule", "path": self._paths.rule, "class": s.rule_class}, entry="E-c"
        )

    # ------------------------------------------------------------------
    # CL-5 — pass-a.json
    # ------------------------------------------------------------------

    def _cl_5(self) -> None:
        s = self._s
        path = self._paths.pass_config
        identity = s.act.file(path) if s.same_boot else None
        if identity is not None and (
            s.authority is None or identity.sha256 != s.authority.pins.pass_config_sha256
        ):
            identity = None
        s.pass_identity = identity
        s.pass_class = self._remove_attributed_file(path, identity, removed="removed")
        self._append("classified", {"object": "pass-config", "path": path, "class": s.pass_class}, entry="E-c")

    def _remove_attributed_file(self, path: str, identity: Identity | None, *, removed: str) -> str:
        observed = self._p.fs.observe(path)
        if observed is None:
            return self._absent_class(path, identity)
        attribution = self._attribute(identity, observed)
        if attribution is not Attribution.A1_INTACT:
            return _kept_class(attribution)
        removal = self._remove(path, identity, directory=False)
        return self._removal_class(path, removal, removed=removed, not_found="absent-before-removal")

    def _removal_class(self, path: str, removal: Removal, *, removed: str, not_found: str) -> str:
        if removal.outcome is RemovalOutcome.REMOVED:
            self._append("removed", {"path": path}, entry="E-c")
            return removed
        if removal.outcome is RemovalOutcome.ABSENT:
            return not_found
        if removal.outcome is RemovalOutcome.UNREMOVABLE:
            self._append("remove-failed", {"path": path, "errno": removal.errno}, entry="E-c")
            return "unremovable"
        if (
            removal.attribution is Attribution.A1_INTACT
            and removal.observed is not None
            and removal.observed.empty is False
        ):
            return "present-nonempty-unremoved"
        return _kept_class(removal.attribution)

    # ------------------------------------------------------------------
    # CL-5b — tree P's top, tree R, grant.id, K (last)
    # ------------------------------------------------------------------

    def _cl_5b(self) -> None:
        s = self._s
        self._remove_directory("tree-p", self._paths.tree_p)
        tree_r = [t for t in s.act.trees if t.tag == "r" and t.linked] if s.same_boot else []
        if tree_r:
            for identity in reversed(tree_r[-1].directories):
                self._remove_directory("tree-r", identity.path)
        else:
            observed = self._p.fs.observe(self._paths.rules_dir)
            if observed is not None:
                s.directories.append(
                    {"role": "rules-dir", "path": self._paths.rules_dir, "class": "pre-existing-kept"}
                )
        for parent, temp in s.act.temp_names() if s.act.valid else ():
            temp_path = f"{parent.rstrip('/')}/{temp}"
            if self._p.fs.observe(temp_path) is not None:
                s.s0.append(temp_path)
        grant_id_identity = s.act.file(self._paths.grant_id) if s.same_boot else None
        s.grant_id_class = self._remove_attributed_file(
            self._paths.grant_id, grant_id_identity, removed="removed"
        )
        lock_identity = self._lock_identity()
        if lock_identity is None and self._k_is_s0():
            # RT2.AM0.8, H-CL.5b.2, R8 LD-1: K left before the ACT journal existed
            # has no identity line; it is S0 — reported, kept, cleared at the boot.
            s.s0.append(self._paths.lock_dir)
            s.directories.append({"role": "lock-dir", "path": self._paths.lock_dir, "class": K_S0})
            self._append(
                "classified",
                {"object": "lock-dir", "path": self._paths.lock_dir, "class": K_S0},
                entry="E-c",
            )
            return
        self._remove_directory("lock-dir", self._paths.lock_dir, identity=lock_identity)

    def _k_is_s0(self) -> bool:
        """K is S0 only when no identity line for it can exist and it is exactly what
        AM-0 (ii) creates: the ACT journal absent (never created — not unreadable,
        not invalid), the pinned boot, ``/run`` on tmpfs, and K a root ``0700``
        directory with two links, empty (so no ``grant.id``), no ACL or capability
        attribute, and the very inode CL-0 holds locked. Anything else stays A0."""
        s = self._s
        if (
            s.authority is None
            or s.act_parsed is not None
            or s.run_fstype != "tmpfs"
            or s.boot_at_start != s.authority.pins.boot_id
            or s.lock is None
            or s.lock.mode is not LockMode.HELD
            or s.lock.object is None
            or self._p.fs.observe(f"{self._paths.act_dir}/journal") is not None
        ):
            return False
        return _k_s0_shape(self._p.fs.observe(self._paths.lock_dir, list_dir=True), s.lock.object, self._owner)

    def _lock_identity(self) -> Identity | None:
        s = self._s
        lock = s.act.lock if s.same_boot else None
        if lock is None or lock.path != self._paths.lock_dir:
            return None
        return lock

    def _remove_directory(self, role: str, path: str, identity: Identity | None = None) -> None:
        s = self._s
        if identity is None and role != "lock-dir":
            identity = s.act.directory(path) if s.same_boot else None
        observed = self._p.fs.observe(path, list_dir=True)
        if observed is None:
            klass = self._absent_class(path, identity)
            klass = "never-created" if klass == "never-linked" else klass
        else:
            attribution = self._attribute(identity, observed)
            if attribution is not Attribution.A1_INTACT:
                klass = _kept_class(attribution)
            elif observed.empty is not True:
                klass = "present-nonempty-unremoved"
            else:
                removal = self._remove(path, identity, directory=True)
                klass = self._removal_class(
                    path, removal, removed="removed", not_found="absent-before-removal"
                )
        s.directories.append({"role": role, "path": path, "class": klass})
        self._append("classified", {"object": role, "path": path, "class": klass}, entry="E-c")

    # ------------------------------------------------------------------
    # CL-6 — verify ST-1
    # ------------------------------------------------------------------

    def _cl_6(self) -> None:
        s = self._s
        fs = self._p.fs
        checks = s.st1_checks
        checks["rule-absent"] = fs.observe(self._paths.rule) is None
        checks["pass-config-absent"] = fs.observe(self._paths.pass_config) is None
        checks["tree-p-absent"] = fs.observe(self._paths.tree_p) is None
        created_rules_dir = any(d["role"] == "tree-r" for d in s.directories)
        rules_dir = fs.observe(self._paths.rules_dir)
        # Absent if ACT created it; otherwise, if present, still a root-only directory.
        checks["rules-dir-as-at-ap0"] = (rules_dir is None) if created_rules_dir else (
            rules_dir is None
            or (
                rules_dir.kind is ObjectKind.DIR
                and rules_dir.uid == self._owner.uid
                and not rules_dir.mode & 0o022
            )
        )
        # Absent, or still the very S0 K classified at CL-5b (re-observed, not assumed).
        checks["lock-dir-absent-or-s0"] = fs.observe(self._paths.lock_dir) is None or (
            any(d["role"] == "lock-dir" and d["class"] == K_S0 for d in s.directories)
            and s.lock is not None
            and _k_s0_shape(fs.observe(self._paths.lock_dir, list_dir=True), s.lock.object, self._owner)
        )
        checks["pk-not-authorized"] = s.pk is not None and s.pk.outcome is PkOutcome.NOT_AUTHORIZED
        if s.authority is not None:
            h1 = s.authority.h1
            equal, observed, difference = baseline_module.compare(
                h1.baseline_sha256, h1.baseline, self._p.services.baseline(s.params).recompute()
            )
            s.baseline_observed, s.baseline_difference = observed, difference
            checks["baseline-equal"] = equal
        else:
            checks["baseline-equal"] = False
        read = self._units.read_unit(CAPTURE_UNIT, (UnitProperty.ACTIVE_STATE,))
        if isinstance(read, ControlOk):
            s.unit_at_end = str(read.value[UnitProperty.ACTIVE_STATE])
            checks["capture-unit-not-active"] = s.unit_at_end in {"inactive", "failed"}
            if s.unit_at_end in ACTIVE_STATES:
                self._fail("CL-6", "unit-still-active")
        else:
            checks["capture-unit-not-active"] = False
            self._fail("CL-6", "observation-failed")

    # ------------------------------------------------------------------
    # outcome and CL-7 — records, run-end
    # ------------------------------------------------------------------

    def _verified(self) -> bool:
        s = self._s
        return (
            s.rule_class in RULE_OK
            and s.pk is not None
            and s.pk.outcome is PkOutcome.NOT_AUTHORIZED
            and s.pass_class in PASS_OK
            and s.grant_id_class in PASS_OK
            and all(d["class"] in DIR_OK for d in s.directories)
            and all(s.st1_checks.values())
            and bool(s.st1_checks)
            and s.lock is not None
            and not s.gp
        )

    def _cl_7(self) -> CleanupOutcome:
        s = self._s
        self._collect_residual()
        verified = self._verified()
        if not verified and not s.failures:
            self._fail("CL-6", "st1-not-verified")
        if s.gp:
            self._fail("CL-0", "evidence-unwritable")
            return self._finish(Terminal.EVIDENCE_UNWRITABLE)
        record_sha = None
        try:
            act_sha = self._ensure_act_record()
            record = self._deact_record(verified, act_sha)
            data = canonical_bytes(record)
            published = self._p.records.publish(self._paths.deact_record_name(s.k), data, s.sink)
            record_sha = published.sha256
        except (OSError, EvidenceWriteError, ValueError):
            self._fail("CL-7", "record-unpublished")
            self._append("run-end", {"outcome": "record-unpublished"}, entry="E-c")
            return self._finish(Terminal.RECORD_UNPUBLISHED)
        terminal = Terminal.ST1_VERIFIED if verified else (
            Terminal.UNIT_STILL_ACTIVE
            if any(c == "unit-still-active" for _s, c in s.failures)
            else Terminal.HARD_STOP
        )
        self._append("run-end", {"outcome": terminal.value}, entry="E-c")
        outcome = self._finish(terminal)
        outcome.record, outcome.record_sha256 = record, record_sha
        return outcome

    def _finish(self, terminal: Terminal) -> CleanupOutcome:
        s = self._s
        return CleanupOutcome(
            terminal=terminal,
            k=s.k,
            rule_class=s.rule_class,
            pass_class=s.pass_class,
            dir_classes=[d["class"] for d in s.directories],
            pk_outcome=s.pk.outcome.value if s.pk else ABSENT,
            failure=s.failures[0][1] if s.failures else "none",
        )

    def _collect_residual(self) -> None:
        s = self._s
        kept = []
        for path, klass in (
            (self._paths.rule, s.rule_class),
            (self._paths.pass_config, s.pass_class),
            (self._paths.grant_id, s.grant_id_class),
            *((d["path"], d["class"]) for d in s.directories),
        ):
            if klass.startswith("present-") or klass in {"unremovable", "grant-unremovable"}:
                kept.append((path, klass))
        kept += [(path, "s0") for path in s.s0]
        for path, klass in kept:
            observed = self._p.fs.observe(path)
            if observed is None:
                continue
            s.residual.append({"path": path, "class": klass, **observed.facts()})
        if s.residual and not any(c == "residual" for _s, c in s.failures):
            if any(r["class"] != "s0" for r in s.residual):
                self._fail("CL-6", "residual")

    def _ensure_act_record(self) -> str:
        """CL-7: if no ``act`` record exists, publish one with outcome ``failed``.

        An existing record is immutable and is never replaced, but its digest is
        linked only after it is read back through the guarded store, parsed
        canonically and validated as this activation's ``act`` record (attempt 0,
        the same A-2). Anything else raises ``ValueError``: CL-7 is then
        ``record-unpublished`` and no deactivation record chains to those bytes."""
        name = self._paths.act_record_name()
        existing = self._p.records.read(name)
        if existing is not None:
            self._require_act_record(existing)
            return hashlib.sha256(existing).hexdigest()
        record = self._base_record(kind="act", attempt=0, outcome="failed")
        record["failure"] = {"step": "CL-7", "class": "act-unconfirmed"}
        validate_record(record)
        return self._p.records.publish(name, canonical_bytes(record), self._s.sink).sha256

    def _require_act_record(self, data: bytes) -> None:
        doc = parse_canonical(data)  # CanonicalError is a ValueError
        validate_record(doc)  # RecordSchemaError is a ValueError
        if (
            doc["kind"] != "act"
            or doc["attempt"] != 0
            or doc["activation_id"] != self._inv.activation_id
            or doc["authority"]["a2_sha256"] != self._inv.a2_sha256
        ):
            raise ValueError("the existing act record belongs to another activation or attempt")

    def _deact_record(self, verified: bool, act_sha256: str) -> dict:
        s = self._s
        record = self._base_record(
            kind="deact", attempt=s.k, outcome="st1-verified" if verified else "hard-stop"
        )
        record["act_record_sha256"] = act_sha256
        if not verified:
            step, klass = s.failures[0]
            record["failure"] = {"step": step, "class": klass}
        own_sha, own_len = s.sink.prefix()
        record["journals"].append(
            {"path": f"{self._paths.attempt_dir(s.k)}/journal", "sha256": own_sha, "length": own_len}
        )
        validate_record(record)
        return record

    def _base_record(self, *, kind: str, attempt: int, outcome: str) -> dict:
        s = self._s
        auth = s.authority
        pk = s.pk
        lock = s.lock
        return {
            "schema": SCHEMA,
            "kind": kind,
            "activation_id": self._inv.activation_id,
            "attempt": attempt,
            "trigger": self._inv.trigger.value,
            "authority": {
                "a2_path": self._paths.a2_file(self._inv.a2_sha256),
                "a2_sha256": self._inv.a2_sha256,
            },
            "authority_limit": AUTHORITY_LIMIT,
            "h1_record": {"record_id": auth.h1.record_id, "sha256": auth.h1.sha256}
            if auth
            else ABSENT,
            "h2_record_sha256": ABSENT,
            "boot": {
                "pinned": auth.pins.boot_id if auth else ABSENT,
                "act_boot": s.act.boot_id if s.act.valid else ABSENT,
                "observed_at_start": s.boot_at_start or ABSENT,
                "observed_at_end": self._p.host.boot_id() or ABSENT,
                "run_fstype": s.run_fstype or ABSENT,
            },
            "pass_config": {
                "path": self._paths.pass_config,
                "sha256_pinned": auth.pins.pass_config_sha256 if auth else ABSENT,
                "identity": identity_doc(s.pass_identity),
                "class": s.pass_class,
            },
            "staged_rule": {"sha256": auth.pins.staged_rule_sha256 if auth else ABSENT},
            "active_rule": {
                "path": self._paths.rule,
                "sha256_expected": auth.pins.staged_rule_sha256 if auth else ABSENT,
                "identity": identity_doc(s.rule_identity),
                "class": s.rule_class,
            },
            "grant_check": {
                "procedure": PROCEDURE,
                "authorized_at_act": "authorized" if s.act.positive_control else ABSENT,
                "after_cleanup": pk.outcome.value if pk else ABSENT,
            },
            "unit": {
                "active_state_at_start": s.capture["active_state"] if s.capture else ABSENT,
                "active_state_at_end": s.unit_at_end,
            },
            "lease": dict(auth.pins.lease) if auth else ABSENT,
            "holder": {
                "unit": f"{self._inv.activation_id}.service",
                "invocation_id": self._inv.holder_invocation_id,
                "active_state_at_start": self._inv.holder_state,
                "result": ABSENT,
                "hold_end_reason": s.act.hold_end_reason,
            },
            "consume": self._consume_doc(),
            "directories": list(s.directories),
            "lock": {
                "object": identity_doc(lock.object if lock else None),
                "mode": lock.mode.value if lock else LockMode.ABSENT.value,
                "wait_ms": lock.wait_ms if lock else 0,
            },
            "grant_identity": {
                "source": "grant.id" if s.grant_identity else ("journal" if s.rule_identity else ABSENT),
                "conflict": s.conflict,
                "cl_g": s.grr.value,
                "grant_id_class": s.grant_id_class,
            },
            "pk": {
                "procedure": PROCEDURE,
                "mode": pk.mode.value if pk else ABSENT,
                "op_ms": s.params.pk_op_ms,
                "call_ms": s.params.pk_call_ms,
                "reap_grace_ms": s.params.reap_grace_ms,
                "calls": pk.calls if pk else 0,
                "abandoned": pk.abandoned if pk else 0,
                "signals": pk.signal_counts() if pk else {"sent": 0, "esrch": 0, "failed": 0, "not_sent": 0},
                "elapsed_ms": pk.elapsed_ms if pk else 0,
                "outcome": pk.outcome.value if pk else ABSENT,
                "reason": pk.reason if pk else ABSENT,
            },
            "children": {
                "entries": list(pk.children) if pk else [],
                "overflow": pk.overflow if pk else 0,
            },
            "release": {
                "first_rung": _first_rung(s),
                "igr": "removed" if s.act.valid and s.act.igr_removed else ABSENT,
            },
            "capture": dict(s.capture) if s.capture else ABSENT,
            "helper": {
                "role": self._inv.trigger.value,
                "image_sha256": [self._tool_sha256] if self._tool_sha256 != ABSENT else [],
                "tool_sha256": self._tool_sha256,
            },
            "params": {**s.params.to_doc(), "sizing": "necessary-conditions-met"},
            "st1": {
                "verified": outcome == "st1-verified",
                "baseline_sha256_observed": s.baseline_observed,
                "first_difference": s.baseline_difference,
                "checks": dict(s.st1_checks),
            },
            "journals": self._journal_list(),
            "act_record_sha256": ABSENT,
            "outcome": outcome,
            "failure": ABSENT,
            "residual": list(s.residual),
            "evidence_mode": "journaled",
            "time": {
                "start_utc": s.start_utc,
                "end_utc": self._p.host.utc_now(),
                "grant_linked_utc": ABSENT,
                "grant_removed_utc": s.grant_removed_utc,
            },
        }

    def _journal_list(self) -> list[dict]:
        s = self._s
        entries = []
        if s.act_parsed is not None:
            entries.append(
                {"path": f"{self._paths.act_dir}/journal", "sha256": s.act_parsed.sha256, "length": s.act_parsed.length}
            )
        for directory, parsed in s.earlier:
            if parsed is not None:
                entries.append({"path": f"{directory}/journal", "sha256": parsed.sha256, "length": parsed.length})
        if s.consume is not None:
            entries.append(
                {"path": f"{self._paths.consume_dir}/journal", "sha256": s.consume.sha256, "length": s.consume.length}
            )
        return entries

    def _consume_doc(self) -> dict:
        """H-CL.2.2: the attempt's ``consume`` class (diagnostic; not an ST-1 input)."""
        s = self._s
        tau = s.capture["inactive_enter_us"] if s.capture else None
        tau0 = s.act.capture_tau0 if s.act.valid else None
        if s.consume is not None and s.consume.valid:
            ops = {line.op for line in s.consume.lines}
            outcome = (
                "consumed" if "consumed" in ops else "failed" if "consume-failed" in ops else "incomplete"
            )
            return {"class": "claimed", "outcome": outcome}
        if s.consume is not None:
            return {"class": "claimed", "outcome": "unjournaled"}
        if tau is None or tau0 is None:
            return {"class": "indeterminate", "outcome": ABSENT}
        if tau == tau0 and s.act.hold_end_reason not in {"start-before-hold", "start-failed-before-exec"}:
            return {"class": "none", "outcome": ABSENT}
        if tau == 0:
            return {"class": "indeterminate", "outcome": ABSENT}
        return {"class": "unidentified", "outcome": ABSENT}

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _attribute(self, identity: Identity | None, observed: Observed) -> Attribution:
        if identity is not None and identity.kind is ObjectKind.FILE:
            return classify_file(identity, observed, self._owner)
        return classify(identity, observed, self._owner)

    def _remove(self, path: str, identity: Identity | None, *, directory: bool) -> Removal:
        assert identity is not None  # only A1-intact objects reach here

        def write_ahead(observed: Observed) -> None:
            self._append(
                "remove-intent",
                {
                    "path": path,
                    "dev": observed.dev,
                    "ino": observed.ino,
                    "sha256": observed.sha256 or ABSENT,
                },
                entry="E-b" if path == self._paths.rule else "E-c",
            )

        return self._p.fs.remove(path, identity, directory=directory, before_unlink=write_ahead)

    def _append(self, op: str, fields: dict, *, entry: str) -> bool:
        """Append and flush; on failure enter GP-R3 and report False. In GP nothing is written."""
        s = self._s
        if s.gp or s.sink is None:
            return False
        try:
            s.sink.append(op, fields)
        except EvidenceWriteError:
            self._enter_gp(entry)
            return False
        return True

    def _enter_gp(self, entry: str) -> None:
        s = self._s
        if not s.gp:
            s.gp = entry

    def _fail(self, step: str, klass: str) -> None:
        self._s.failures.append((step, klass))


def grr_outcome(removal: Removal) -> tuple[GrrOutcome, int]:
    if removal.outcome is RemovalOutcome.REMOVED:
        return GrrOutcome.REMOVED, 0
    if removal.outcome is RemovalOutcome.ABSENT:
        return GrrOutcome.ABSENT, 0
    if removal.outcome is RemovalOutcome.UNREMOVABLE:
        return GrrOutcome.UNREMOVABLE, removal.errno or errno_module.EIO
    if removal.attribution is Attribution.UNINSPECTED:
        return GrrOutcome.KEPT_UNINSPECTED, 0
    if removal.attribution is Attribution.A1_DAMAGED:
        return GrrOutcome.KEPT_DAMAGED, 0
    return GrrOutcome.KEPT_FOREIGN, 0


def _k_s0_shape(observed: Observed | None, locked: Identity | None, owner: Owner) -> bool:
    """The structural half of the S0 test for K (LD-1, RT2.AM0.8 … .9)."""
    return (
        observed is not None
        and locked is not None
        and observed.kind is ObjectKind.DIR
        and (observed.dev, observed.ino) == (locked.dev, locked.ino)
        and (observed.uid, observed.gid) == (owner.uid, owner.gid)
        and observed.mode == 0o700
        and observed.nlink == 2
        and observed.empty is True
        and not any(
            name in FORBIDDEN_XATTRS or name.startswith("system.posix_acl_") or name == "unlistable"
            for name in observed.xattr_names
        )
    )


def _kept_class(attribution: Attribution | None, *, rule: bool = False) -> str:
    """The ``present-*-unremoved`` class of a kept object. Only the activation rule
    keeps ``UNINSPECTED`` as its own class (it may still authorize the operator);
    any other object keeps its accepted A1-damaged class."""
    if attribution is Attribution.UNINSPECTED and rule:
        return RULE_UNINSPECTED
    if attribution is Attribution.A1_DAMAGED or attribution is Attribution.UNINSPECTED:
        return "present-damaged-unremoved"
    return "present-foreign-unremoved"


def identity_doc(identity: Identity | None) -> dict | str:
    if identity is None:
        return ABSENT
    return {"path": identity.path, "dev": identity.dev, "ino": identity.ino}


def _first_rung(s: _State) -> str:
    if s.act.valid and s.act.igr_removed:
        return "igr"
    if s.grr is GrrOutcome.REMOVED:
        return "cl-g"
    if s.rule_removed_here:
        return "stop-post"
    return ABSENT
