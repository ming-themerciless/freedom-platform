"""RT-2 ``hold``: ACT, ``hold-start``, HL and IGR (inventory §5.2).

The holder is the main process of ``<id>.service`` (created by SA-1). Its body,
in order, each step behind a stop-flag check (SG-4):

* **AM-0** — A-2 by the operand's digest, then H-1 (``load_authority``); (i) the
  boot, ``/run`` on tmpfs, its parents, every absence condition, the three
  unit ``LoadState`` reads and ``/run/nextroot``; (ii) K created exclusively and
  locked once; (iii) the capture-unit baseline under BSP; (iv) the ``ACT``
  journal and ``run-start``.
* **AK-1** — ``backstop-intent`` durable before the single DI-3 call; the timer
  must then read ``active``; ``backstop-armed``.
* **AM-1 / AM-1R** — tree P (``pass-a.json``) and, only if the rules directory
  is absent, tree R, by protocol PT.
* **AM-1G / AM-2** — the staged rule by its pinned ``(dev, ino)`` and digest;
  PF-1 … PF-5 for the rule; ``grant.id`` naming that unnamed inode published in
  K; the flag immediately before and after PF-6, the link that makes the grant
  live; PF-7 … PF-9.
* **AV-1** — both files re-verified, the baseline recomputed equal to H-1's,
  Polkit *authorized* for ``start`` (seek-authorized) and *not authorized* for
  ``stop`` (first-decisive) for the operator's subject.
* **AM-3** — the ``act`` record (outcome ``activated``) by PF: its durable
  commit is ACT PASS. Nothing earlier is.
* **hold-start** — the capture unit re-read under K: unchanged τ₀, not active,
  no job (else OS-7 ``start-before-hold``); ``hold-start`` durable; K closed.
* **HL** — every Δ observe; on a terminal reason decide under K (OS-5):
  ``hold-end`` durable, K closed, return.

**IGR** runs exactly once from ``run``'s ``finally`` on every catchable end —
return, an ``_End`` or any exception — and nowhere else: GRR with the in-memory
grant identity (no lock, no spawn, no Polkit, no ``ext4`` read), then a
best-effort ``igr {outcome, identity}`` line. Then, from the same ``finally``,
the best-effort ``run-end {outcome}`` (RT2.AM3.2) and the release of K if it is
still held. The process returns and PID 1 runs ``ExecStopPost`` (the
implemented stop-post cleanup).

Reversible choices pinned by ``tests/test_rp11_hold.py``:

* AM-0's three ``LoadState`` reads: both backstop units ``not-found``; the
  holder's own unit ``loaded`` (the literal AP-0 condition cannot hold for the
  unit that is running this process). The non-operative ``RT2.AM0.7`` gap row
  (unterminated activation of the H-1 record) is **not** implemented.
* A rules directory absent at AM-0 is admitted and built as tree R (PO-11
  (f)(ii)); polkitd 127 does not watch a directory created after it started,
  so AV-1's positive control then fails closed (``grant-not-seen``). The holder
  never restarts or reloads Polkit.
* ``grant.id`` is published by PF into K (so cleanup can attribute it).
* ``run-start``'s authority values come from A-2 (``rp11-a2/3``): ``h2_record_sha256``
  and ``helper.image_sha256`` as quoted; ``tool_sha256`` only after the installed
  tool (``Layout.tool``, root-owned ``0644``) hashed to A-2's pin, else
  ``invalid-authority`` at AM-0 (``detail=tool``). ``lock`` is
  ``{object K, mode held, wait_ms 0}``: one non-blocking attempt.
* ``run-end`` placement (RT2.AM3.2, open in the accepted text): the holder's
  last ACT line, after IGR, best effort, with the end class as ``outcome``
  (``hold-ended`` only after HL's normal end; ``internal-error`` for an
  unexpected exception). Order on each end: HL ``hold-end`` → K released →
  ``igr`` → ``run-end``; at ``hold-start`` (``hold-end`` under K) and every
  earlier end with K held: [``hold-end``] → ``igr`` → ``run-end`` → K
  released. No ``run-end`` (nor ``igr``) exists without the ACT journal, and a
  failed ``run-end`` changes neither the grant nor the end class.
* Exit codes: 0 HL's normal end; 20 … 35 one per fail-closed class
  (``HoldEnd``); 70 an unexpected exception (composition root).
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from application.unit_control import (
    CAPTURE_UNIT,
    BackstopSpec,
    ControlError,
    ControlOk,
    UnitControl,
    UnitProperty,
    UnitVerb,
    backstop_service_name,
    backstop_timer_name,
    holder_unit_name,
)

from . import baseline as baseline_module
from .attribution import Attribution, Identity, classify
from .authority import AUTHORITY_LIMIT, Authority, AuthorityError, load_authority
from .canonical import ABSENT, canonical_bytes
from .cleanup import GrrOutcome, Services, grr_outcome, identity_doc
from .hl import NOT_ACTIVE, CaptureBaseline, Observation, terminal_reason
from .journal import JournalKind, consume_run, parse_journal
from .paths import GRANT_ID_NAME, PASS_NAME, RULE_NAME, ActivationPaths
from .pk import PROCEDURE, PkMode, PkOutcome, PkResult
from .ports import (
    ActivationFs,
    ActivationLock,
    EvidenceSink,
    EvidenceWriteError,
    GuardMode,
    HoldHost,
    HostFacts,
    JournalSource,
    LockObjectError,
    PreparedFile,
    PublishError,
    Publisher,
    RecordStore,
    TreeMember,
)
from .records import SCHEMA, validate_record
from .sn import MAX_CHILD_ENTRIES

BSP_RETRIES = 5  # class C (R8 §6.4)
BSP_WAIT_MS = 2
STAGED_RULE_MAX_BYTES = 65_536
TOOL_MAX_BYTES = 1 << 20
INTERNAL_ERROR = "internal-error"  # run-end's outcome after an unexpected exception
_CAPTURE_PROPS = (
    UnitProperty.ACTIVE_STATE,
    UnitProperty.INVOCATION_ID,
    UnitProperty.INACTIVE_ENTER_TIMESTAMP_MONOTONIC,
    UnitProperty.JOB,
)
_HL_PROPS = _CAPTURE_PROPS + (UnitProperty.EXEC_MAIN_START_TIMESTAMP_MONOTONIC,)


class HoldEnd(str, Enum):
    HOLD_ENDED = "hold-ended"
    INVALID_AUTHORITY = "invalid-authority"
    PRECONDITION = "precondition"
    LOCK_OBJECT = "lock-object"
    CAPTURE_BASELINE_UNSTABLE = "capture-baseline-unstable"
    CAPTURE_BUSY_AT_ACT = "capture-busy-at-act"
    EVIDENCE_UNWRITABLE = "evidence-unwritable"
    BACKSTOP_UNCONFIRMED = "backstop-unconfirmed"
    PUBLICATION_FAILED = "publication-failed"
    GRANT_NOT_SEEN = "grant-not-seen"
    STOP_CONTROL_UNCONFIRMED = "stop-control-unconfirmed"
    STOP_CONTROL_AUTHORIZED = "stop-control-authorized"
    VERIFICATION_FAILED = "verification-failed"
    ACT_RECORD_UNPUBLISHED = "act-record-unpublished"
    START_BEFORE_HOLD = "start-before-hold"
    OBSERVATION_FAILED = "observation-failed"
    INTERRUPTED = "interrupted"

    @property
    def exit_code(self) -> int:
        return 0 if self is HoldEnd.HOLD_ENDED else 20 + list(HoldEnd).index(self) - 1


@dataclass
class HoldOutcome:
    end: HoldEnd
    step: str
    detail: str
    igr: str = ABSENT
    act_pass: bool = False

    @property
    def exit_code(self) -> int:
        return self.end.exit_code

    def line(self, activation_id: str) -> str:
        """One bounded diagnostic line: tokens only, no value, path or content."""
        return (
            f"rp11-hold {self.end.value} {activation_id} step={self.step} "
            f"detail={self.detail} act_pass={'yes' if self.act_pass else 'no'} igr={self.igr}"
        )


@dataclass(frozen=True)
class HoldInvocation:
    activation_id: str
    a2_sha256: str
    invocation_id: str  # the holder's own INVOCATION_ID or "absent" (RT2.FI.1)
    parent_pid: int


class StopFlag:
    """``stop_requested`` (SG-1): the handlers only set it; the main thread reads it."""

    def __init__(self) -> None:
        self.requested = False

    def set(self) -> None:
        self.requested = True

    def __call__(self) -> bool:
        return self.requested


class HoldClock(Protocol):
    def monotonic_ms(self) -> int: ...

    def monotonic_us(self) -> int:
        """CLOCK_MONOTONIC floored to microseconds (BSP's ``m_a``)."""
        ...

    def sleep_ms(self, ms: int) -> None: ...


class _End(Exception):
    def __init__(self, end: HoldEnd, step: str, detail: str = "none") -> None:
        super().__init__(end.value)
        self.end, self.step, self.detail = end, step, detail


@dataclass
class _State:
    start_utc: str = ABSENT
    boot: str = ""
    authority: Authority | None = None
    rules_dir_preexisting: bool = False
    k: Identity | None = None
    k_held: bool = False
    capture0: CaptureBaseline | None = None
    m_a_us: int = 0
    bsp_retries: int = 0
    sink: EvidenceSink | None = None
    pass_identity: Identity | None = None
    rule_identity: Identity | None = None
    grant: Identity | None = None  # the in-memory grant identity (= grant.id)
    grant_linked_utc: str = ABSENT
    baseline_observed: str = ABSENT
    pk_start: PkResult | None = None
    pk_stop: PkResult | None = None
    act_pass: bool = False
    act_pass_ms: int = 0
    igr_state: str = "idle"  # IGR-0 latch: idle, running, done
    igr: str = ABSENT
    children: list[dict] = field(default_factory=list)
    overflow: int = 0


class HoldProcedure:
    def __init__(
        self,
        invocation: HoldInvocation,
        paths: ActivationPaths,
        *,
        fs: ActivationFs,
        journals: JournalSource,
        host_fs: HoldHost,
        publisher: Publisher,
        records: RecordStore,
        lock: ActivationLock,
        host: HostFacts,
        services: Services,
        clock: HoldClock,
        flag: Callable[[], bool],
    ) -> None:
        if invocation.activation_id != paths.activation_id:
            raise ValueError("paths belong to another activation")
        self._inv = invocation
        self._paths = paths
        self._owner = paths.layout.owner
        self._fs = fs
        self._journals = journals
        self._host_fs = host_fs
        self._publisher = publisher
        self._records = records
        self._lock = lock
        self._host = host
        self._services = services
        self._clock = clock
        self._flag = flag
        self._units: UnitControl | None = None
        self._s = _State()

    # ------------------------------------------------------------------
    # public
    # ------------------------------------------------------------------

    def run(self) -> HoldOutcome:
        """The body inside one ``finally``: IGR runs once on every catchable end."""
        outcome: HoldOutcome | None = None
        try:
            outcome = self._body()
        except _End as end:
            outcome = HoldOutcome(end.end, end.step, end.detail)
        finally:
            self._igr()
            self._run_end(outcome.end.value if outcome is not None else INTERNAL_ERROR)
            self._release_k()
        outcome.igr = self._s.igr
        outcome.act_pass = self._s.act_pass
        return outcome

    @property
    def igr_state(self) -> str:
        return self._s.igr_state

    # ------------------------------------------------------------------
    # the body
    # ------------------------------------------------------------------

    def _body(self) -> HoldOutcome:
        self._s.start_utc = self._host.utc_now()
        self._check("AM-0")
        self._read_authority()
        self._check("AM-0")
        self._recheck()
        self._check("AM-0")
        self._create_k()
        self._check("AM-0")  # K exists, no journal yet: an end here leaves an S0 K
        self._capture_baseline()
        self._check("AM-0")
        self._open_journal()
        self._check("AK-1")
        self._arm_backstop()
        self._check("AM-1")
        self._tree_p()
        self._check("AM-1R")
        self._tree_r()
        self._check("AM-1G")
        self._publish_rule()
        self._check("AV-1")
        self._verify()
        self._check("AM-3")
        self._act_record()
        self._check("hold-start")
        self._hold_start()
        return self._hold_loop()

    # AM-0 ------------------------------------------------------------------

    def _read_authority(self) -> None:
        try:
            self._s.authority = load_authority(
                self._fs,
                self._paths,
                a2_sha256=self._inv.a2_sha256,
                activation_id=self._inv.activation_id,
            )
        except AuthorityError:
            raise _End(HoldEnd.INVALID_AUTHORITY, "AM-0", "a2-h1") from None
        tool = self._fs.read_root_file(self._paths.layout.tool, max_bytes=TOOL_MAX_BYTES, mode=0o644)
        if tool is None or hashlib.sha256(tool).hexdigest() != self._s.authority.pins.tool_sha256:
            raise _End(HoldEnd.INVALID_AUTHORITY, "AM-0", "tool")
        self._units = self._services.units(self._s.authority.h1.params)

    def _recheck(self) -> None:
        """AM-0 (i): boot, ``/run`` on tmpfs and its parents, absence, units, nextroot."""
        s, p = self._s, self._paths
        pins = s.authority.pins
        boot = self._host.boot_id()
        if boot is None or boot != pins.boot_id:
            raise _End(HoldEnd.PRECONDITION, "AM-0", "boot")
        s.boot = boot
        if self._host.run_fstype() != "tmpfs":
            raise _End(HoldEnd.PRECONDITION, "AM-0", "run-not-tmpfs")
        if self._host_fs.directory_problem(p.layout.run) is not None:
            raise _End(HoldEnd.PRECONDITION, "AM-0", "parent")
        for directory in (p.polkit_run_dir, p.rules_dir):
            if self._host_fs.directory_problem(directory) not in (None, "absent"):
                raise _End(HoldEnd.PRECONDITION, "AM-0", "parent")
        s.rules_dir_preexisting = self._host_fs.directory_problem(p.rules_dir) is None
        must_be_absent = (
            p.tree_p,
            p.rule,
            p.layout.etc_config,
            p.lock_dir,
            pins.capture_root,
            p.nextroot,
            *(f"{d}/{RULE_NAME}" for d in p.layout.other_rules_dirs),
        )
        for path in must_be_absent:
            if self._fs.observe(path) is not None:
                raise _End(HoldEnd.PRECONDITION, "AM-0", "present")
        expected = (
            (holder_unit_name(self._inv.activation_id), "loaded"),
            (backstop_timer_name(self._inv.activation_id), "not-found"),
            (backstop_service_name(self._inv.activation_id), "not-found"),
        )
        for unit, state in expected:
            read = self._units.read_unit(unit, (UnitProperty.LOAD_STATE,))
            if not isinstance(read, ControlOk):
                raise _End(HoldEnd.PRECONDITION, "AM-0", "unit-unobserved")
            if read.value[UnitProperty.LOAD_STATE] != state:
                raise _End(HoldEnd.PRECONDITION, "AM-0", "unit-state")

    def _create_k(self) -> None:
        try:
            self._s.k = self._lock.create()
        except LockObjectError:
            raise _End(HoldEnd.LOCK_OBJECT, "AM-0") from None
        self._s.k_held = True

    def _capture_baseline(self) -> None:
        """AM-0 (iii) BSP: ``m_a`` before each read, τ₀ < ``m_a`` within five 2-ms
        retries; a read that does not complete is an error, never a baseline."""
        s = self._s
        while True:
            m_a = self._clock.monotonic_us()
            read = self._units.read_unit(CAPTURE_UNIT, _CAPTURE_PROPS)
            if not isinstance(read, ControlOk):
                raise _End(HoldEnd.OBSERVATION_FAILED, "AM-0", "capture-unobserved")
            values = read.value
            tau0 = int(values[UnitProperty.INACTIVE_ENTER_TIMESTAMP_MONOTONIC])
            if tau0 < m_a:
                break
            if s.bsp_retries >= BSP_RETRIES:
                raise _End(HoldEnd.CAPTURE_BASELINE_UNSTABLE, "AM-0")
            s.bsp_retries += 1
            self._sleep_until(self._clock.monotonic_ms() + BSP_WAIT_MS, "AM-0")
        state = str(values[UnitProperty.ACTIVE_STATE])
        if state not in NOT_ACTIVE or int(values[UnitProperty.JOB]) != 0:
            raise _End(HoldEnd.CAPTURE_BUSY_AT_ACT, "AM-0")
        s.m_a_us = m_a
        s.capture0 = CaptureBaseline(state, str(values[UnitProperty.INVOCATION_ID]), tau0)

    def _open_journal(self) -> None:
        s = self._s
        auth = s.authority
        try:
            s.sink = self._host_fs.create_act_journal(
                self._paths.act_dir,
                operator_uid=auth.h1.operator.uid,
                run=self._inv.activation_id,
            )
        except EvidenceWriteError:
            raise _End(HoldEnd.EVIDENCE_UNWRITABLE, "AM-0", "act-journal") from None
        c = s.capture0
        pins = auth.pins
        self._append(
            "run-start",
            {
                "a2_sha256": self._inv.a2_sha256,
                "h1_record_sha256": auth.h1.sha256,
                "h2_record_sha256": pins.h2_record_sha256,
                "boot_id": s.boot,
                "pass_config_sha256": pins.pass_config_sha256,
                "staged_rule_sha256": pins.staged_rule_sha256,
                "lock": self._lock_doc(),
                "capture": {
                    "active_state": c.active_state,
                    "invocation_id": c.invocation_id or ABSENT,
                    "inactive_enter_us": c.tau,
                    "m_a_us": s.m_a_us,
                    "bsp_retries": s.bsp_retries,
                },
                "holder_invocation_id": self._inv.invocation_id,
                "tool_sha256": pins.tool_sha256,
                "helper": self._helper_doc(),
                "lease": dict(pins.lease),
                "params": auth.h1.params.to_doc(),
            },
            "AM-0",
        )

    def _lock_doc(self) -> dict:
        """K as the holder holds it: created and locked by one non-blocking attempt."""
        return {"object": identity_doc(self._s.k), "mode": "held", "wait_ms": 0}

    def _helper_doc(self) -> dict:
        pins = self._s.authority.pins
        return {"role": "hold", "image_sha256": list(pins.image_sha256), "tool_sha256": pins.tool_sha256}

    # AK-1 ------------------------------------------------------------------

    def _arm_backstop(self) -> None:
        """``backstop-intent`` durable, then exactly one DI-3 call, never retried."""
        pins = self._s.authority.pins
        params = self._s.authority.h1.params
        timer = backstop_timer_name(self._inv.activation_id)
        self._append("backstop-intent", {"timer": timer}, "AK-1")
        spec = BackstopSpec(
            activation_id=self._inv.activation_id,
            artifact_sha256=self._inv.a2_sha256,
            interval_seconds=pins.lease["backstop_period_s"],
            runtime_max_seconds=pins.lease["bs_runtime_s"],
            timeout_stop_seconds=pins.lease["stop_timeout_s"],
        )
        result = self._units.create_backstop(spec)
        if not isinstance(result, ControlOk):
            unknown = isinstance(result, ControlError) and result.effect_not_confirmed
            raise _End(HoldEnd.BACKSTOP_UNCONFIRMED, "AK-1", "effect-unknown" if unknown else "not-created")
        read = self._units.read_unit(timer, (UnitProperty.ACTIVE_STATE,))
        if not isinstance(read, ControlOk) or read.value[UnitProperty.ACTIVE_STATE] != "active":
            raise _End(HoldEnd.BACKSTOP_UNCONFIRMED, "AK-1", "timer-not-active")
        self._append(
            "backstop-armed",
            {
                "timer": timer,
                "period_s": pins.lease["backstop_period_s"],
                "max": params.backstop_max,
                "runtime_s": pins.lease["bs_runtime_s"],
            },
            "AK-1",
        )

    # AM-1, AM-1R -------------------------------------------------------------

    def _tree_p(self) -> None:
        pins = self._s.authority.pins
        data = pins.pass_bytes
        if hashlib.sha256(data).hexdigest() != pins.pass_config_sha256:  # AM-1.2
            raise _End(HoldEnd.VERIFICATION_FAILED, "AM-1", "pass-config")
        p = self._paths
        top = p.tree_p.rsplit("/", 1)[1]
        identities = self._publish_tree(
            "AM-1",
            p.layout.run,
            top,
            "p",
            (TreeMember(".", 0o755), TreeMember(PASS_NAME, 0o644, data)),
        )
        self._s.pass_identity = next(i for i in identities if i.path == p.pass_config)

    def _tree_r(self) -> None:
        """Only if ``/run/polkit-1/rules.d`` was absent: its first absent component."""
        p = self._paths
        if self._s.rules_dir_preexisting:
            return
        if self._fs.observe(p.polkit_run_dir) is None:
            parent, top = p.layout.run, "polkit-1"
            members = (TreeMember(".", 0o755), TreeMember("rules.d", 0o755))
        else:
            parent, top = p.polkit_run_dir, "rules.d"
            members = (TreeMember(".", 0o755),)
        self._publish_tree("AM-1R", parent, top, "r", members)

    def _publish_tree(self, step, parent, top, tag, members) -> tuple[Identity, ...]:
        temp = f".rp11-{self._inv.activation_id}-{tag}.tmp"
        try:
            return self._publisher.publish_tree(parent, top, temp, tag, members, self._s.sink)
        except PublishError as exc:
            raise _End(HoldEnd.PUBLICATION_FAILED, step, exc.kind) from None
        except EvidenceWriteError:
            raise _End(HoldEnd.EVIDENCE_UNWRITABLE, step) from None

    # AM-1G, AM-2 --------------------------------------------------------------

    def _publish_rule(self) -> None:
        s, p = self._s, self._paths
        pins = s.authority.pins
        data = self._host_fs.read_staged(
            p.staged_rule,
            dev=pins.staged_rule_dev,
            ino=pins.staged_rule_ino,
            max_bytes=STAGED_RULE_MAX_BYTES,
        )
        if data is None or hashlib.sha256(data).hexdigest() != pins.staged_rule_sha256:
            raise _End(HoldEnd.VERIFICATION_FAILED, "AM-1G", "staged-rule")
        prepared: PreparedFile | None = None
        try:
            try:
                prepared = self._publisher.prepare(
                    p.rules_dir, RULE_NAME, data, 0o644, grant=True, sink=s.sink
                )
                rule = prepared.identity
                self._publish_grant_id(rule)
            except PublishError as exc:
                raise _End(HoldEnd.PUBLICATION_FAILED, "AM-1G", exc.kind) from None
            except EvidenceWriteError:
                raise _End(HoldEnd.EVIDENCE_UNWRITABLE, "AM-1G") from None
            # From here IGR knows the identity of the inode that may become the grant.
            s.grant = rule
            self._check("AM-2")  # immediately before the link (SG-4)
            try:
                prepared.link()  # PF-6: the grant is live from here (G1)
            except PublishError as exc:
                raise _End(HoldEnd.PUBLICATION_FAILED, "AM-2", exc.kind) from None
            self._check("AM-2")  # the very next statement after the link
            s.grant_linked_utc = self._host.utc_now()
            try:
                prepared.commit(s.sink)  # PF-7, PF-8, PF-9
            except PublishError as exc:
                raise _End(HoldEnd.VERIFICATION_FAILED, "AM-2", exc.kind) from None
            except EvidenceWriteError:
                raise _End(HoldEnd.EVIDENCE_UNWRITABLE, "AM-2") from None
            s.rule_identity = rule
        finally:
            if prepared is not None:
                prepared.discard()

    def _publish_grant_id(self, rule: Identity) -> None:
        """AM-1G.3: ``K/grant.id`` names the unnamed inode PF-6 will link."""
        line = canonical_bytes(
            {
                "path": rule.path,
                "dev": rule.dev,
                "ino": rule.ino,
                "sha256": rule.sha256,
                "size": rule.size,
                "mode": rule.mode,
                "uid": self._owner.uid,
                "gid": self._owner.gid,
                "boot_id": self._s.boot,
            }
        )
        self._publisher.publish(
            self._paths.lock_dir, GRANT_ID_NAME, line, 0o600, grant=False, sink=self._s.sink
        )

    # AV-1 -------------------------------------------------------------------

    def _verify(self) -> None:
        s = self._s
        for identity in (s.pass_identity, s.rule_identity):
            observed = self._fs.observe(identity.path)
            if classify(identity, observed, self._owner) is not Attribution.A1_INTACT:
                raise _End(HoldEnd.VERIFICATION_FAILED, "AV-1", "published-file")
        h1 = s.authority.h1
        equal, observed_sha, _difference = baseline_module.compare(
            h1.baseline_sha256, h1.baseline, self._services.baseline(h1.params).recompute()
        )
        s.baseline_observed = observed_sha
        if not equal:
            raise _End(HoldEnd.VERIFICATION_FAILED, "AV-1", "baseline")
        self._check("AV-1")
        s.pk_start = self._pk(UnitVerb.START, PkMode.SEEK_AUTHORIZED)
        if s.pk_start.outcome is not PkOutcome.AUTHORIZED:
            raise _End(HoldEnd.GRANT_NOT_SEEN, "AV-1", s.pk_start.reason)
        self._check("AV-1")
        s.pk_stop = self._pk(UnitVerb.STOP, PkMode.FIRST_DECISIVE)
        if s.pk_stop.outcome is PkOutcome.AUTHORIZED:
            raise _End(HoldEnd.STOP_CONTROL_AUTHORIZED, "AV-1")
        if s.pk_stop.outcome is not PkOutcome.NOT_AUTHORIZED:
            raise _End(HoldEnd.STOP_CONTROL_UNCONFIRMED, "AV-1", s.pk_stop.reason)

    def _pk(self, verb: UnitVerb, mode: PkMode) -> PkResult:
        """One PK/2 series; its subjects and decision are journaled before use."""
        s = self._s
        h1 = s.authority.h1
        result = self._services.pk(h1.params).run(h1.operator, verb, mode, stop_requested=self._flag)
        for child in result.children:
            if len(s.children) < MAX_CHILD_ENTRIES:
                s.children.append(child)
            else:
                s.overflow += 1
            self._append("child", {"entry": child}, "AV-1")
        s.overflow += result.overflow
        self._append(
            "grant-check",
            {
                "verb": verb.value,
                "mode": mode.value,
                "outcome": result.outcome.value,
                "reason": result.reason,
                "calls": result.calls,
            },
            "AV-1",
        )
        if result.reason == "interrupted":
            raise _End(HoldEnd.INTERRUPTED, "AV-1")
        return result

    # AM-3 -------------------------------------------------------------------

    def _act_record(self) -> None:
        """The ``act`` record by PF; its durable commit is ACT PASS."""
        s = self._s
        record = self._act_record_doc()
        validate_record(record)
        try:
            self._records.publish(self._paths.act_record_name(), canonical_bytes(record), s.sink)
        except FileExistsError:
            raise _End(HoldEnd.ACT_RECORD_UNPUBLISHED, "AM-3", "collision") from None
        except (OSError, EvidenceWriteError, ValueError):
            raise _End(HoldEnd.ACT_RECORD_UNPUBLISHED, "AM-3", "publication") from None
        s.act_pass = True
        s.act_pass_ms = self._clock.monotonic_ms()

    def _act_record_doc(self) -> dict:
        s, p = self._s, self._paths
        auth = s.authority
        pins, h1 = auth.pins, auth.h1
        pk = s.pk_start
        c = s.capture0
        sha, length = s.sink.prefix()  # the journal up to the line before file-intent
        return {
            "schema": SCHEMA,
            "kind": "act",
            "activation_id": self._inv.activation_id,
            "attempt": 0,
            "trigger": "act",
            "authority": {"a2_path": p.a2_file(self._inv.a2_sha256), "a2_sha256": self._inv.a2_sha256},
            "authority_limit": AUTHORITY_LIMIT,
            "h1_record": {"record_id": h1.record_id, "sha256": h1.sha256},
            "h2_record_sha256": pins.h2_record_sha256,
            "boot": {
                "pinned": pins.boot_id,
                "act_boot": s.boot,
                "observed_at_start": s.boot,
                "observed_at_end": self._host.boot_id() or ABSENT,
                "run_fstype": "tmpfs",
            },
            "pass_config": {
                "path": p.pass_config,
                "sha256_pinned": pins.pass_config_sha256,
                "identity": identity_doc(s.pass_identity),
                "class": ABSENT,
            },
            "staged_rule": {"sha256": pins.staged_rule_sha256},
            "active_rule": {
                "path": p.rule,
                "sha256_expected": pins.staged_rule_sha256,
                "identity": identity_doc(s.rule_identity),
                "class": ABSENT,
            },
            "grant_check": {
                "procedure": PROCEDURE,
                "authorized_at_act": "authorized",
                "stop_control": s.pk_stop.outcome.value,
                "after_cleanup": ABSENT,
            },
            "unit": {"active_state_at_start": c.active_state, "active_state_at_end": ABSENT},
            "lease": dict(pins.lease),
            "holder": {
                "unit": holder_unit_name(self._inv.activation_id),
                "invocation_id": self._inv.invocation_id,
                "active_state_at_start": "active",
                "result": ABSENT,
                "hold_end_reason": ABSENT,
            },
            "consume": {"class": ABSENT, "outcome": ABSENT},
            "directories": [],
            "lock": self._lock_doc(),
            "grant_identity": {
                "source": "grant.id",
                "conflict": False,
                "cl_g": ABSENT,
                "grant_id_class": ABSENT,
            },
            "pk": {
                "procedure": PROCEDURE,
                "mode": pk.mode.value,
                "op_ms": h1.params.pk_op_ms,
                "call_ms": h1.params.pk_call_ms,
                "reap_grace_ms": h1.params.reap_grace_ms,
                "calls": pk.calls,
                "abandoned": pk.abandoned,
                "signals": pk.signal_counts(),
                "elapsed_ms": pk.elapsed_ms,
                "outcome": pk.outcome.value,
                "reason": pk.reason,
            },
            "children": {"entries": list(s.children), "overflow": s.overflow},
            "release": {"first_rung": ABSENT, "igr": ABSENT},
            "capture": {
                "active_state": c.active_state,
                "invocation_id": c.invocation_id or ABSENT,
                "inactive_enter_us": c.tau,
            },
            "helper": self._helper_doc(),
            "params": {**h1.params.to_doc(), "sizing": "necessary-conditions-met"},
            "st1": {
                "verified": False,
                "baseline_sha256_observed": s.baseline_observed,
                "first_difference": ABSENT,
                "checks": {},
            },
            "journals": [{"path": f"{p.act_dir}/journal", "sha256": sha, "length": length}],
            "act_record_sha256": ABSENT,
            "outcome": "activated",
            "failure": ABSENT,
            "residual": [],
            "evidence_mode": "journaled",
            "time": {
                "start_utc": s.start_utc,
                "end_utc": self._host.utc_now(),
                "grant_linked_utc": s.grant_linked_utc,
                "grant_removed_utc": ABSENT,
            },
        }

    # hold-start -------------------------------------------------------------

    def _hold_start(self) -> None:
        """OS-1/OS-7 under K: no start has begun or ended since AM-0."""
        c = self._s.capture0
        obs = self._observe()
        if obs is None:
            self._hold_end("observation-failed", None, "hold-start")
            raise _End(HoldEnd.OBSERVATION_FAILED, "hold-start")
        if obs.active_state not in NOT_ACTIVE or obs.job != 0 or obs.tau != c.tau:
            self._hold_end("start-before-hold", obs, "hold-start")
            raise _End(HoldEnd.START_BEFORE_HOLD, "hold-start")
        self._append(
            "hold-start",
            {"capture": {"active_state": obs.active_state, "inactive_enter_us": obs.tau}},
            "hold-start",
        )
        self._release_k()  # AR-2: K closed once hold-start is durable

    # HL ---------------------------------------------------------------------

    def _hold_loop(self) -> HoldOutcome:
        s = self._s
        pins = s.authority.pins
        poll_ms = pins.lease["poll_ms"]
        window_ms = pins.lease["start_window_s"] * 1000
        base = s.capture0
        previous = (base.active_state, base.invocation_id)
        active: set[str] = set()
        next_poll = s.act_pass_ms + poll_ms
        while True:
            self._sleep_until(next_poll, "HL")
            next_poll = max(next_poll + poll_ms, self._clock.monotonic_ms())
            obs = self._observe()
            if obs is not None:
                if obs.active_state == "active" and obs.invocation_id:
                    active.add(obs.invocation_id)
                if (obs.active_state, obs.invocation_id) != previous:
                    previous = (obs.active_state, obs.invocation_id)
                    self._append(
                        "pass-observed",
                        {"active_state": obs.active_state, "invocation_id": obs.invocation_id or ABSENT},
                        "HL",
                    )
            expired = self._clock.monotonic_ms() - s.act_pass_ms >= window_ms
            if self._reason(obs, expired, active) is None:
                continue
            # OS-5: decide under K, or keep observing while a consume holds it.
            mode = self._lock.try_once()
            if mode is GuardMode.BUSY:
                continue
            if mode is GuardMode.HELD:
                s.k_held = True
                obs = self._observe()
                expired = self._clock.monotonic_ms() - s.act_pass_ms >= window_ms
                reason = self._reason(obs, expired, active)
                if reason is None:
                    self._release_k()
                    continue
            else:
                obs, reason = None, "observation-failed"  # K unusable (H-LK.1)
            self._hold_end(reason, obs, "HL")
            self._release_k()  # LD-4: after hold-end is durable, before the exit
            if reason == "observation-failed":
                return HoldOutcome(HoldEnd.OBSERVATION_FAILED, "HL", reason)
            return HoldOutcome(HoldEnd.HOLD_ENDED, "HL", reason)

    def _reason(self, obs: Observation | None, expired: bool, active: set[str]) -> str | None:
        if obs is None:
            return "observation-failed"
        return terminal_reason(
            obs, self._s.capture0, window_expired=expired, active_invocations=frozenset(active)
        )

    def _observe(self) -> Observation | None:
        """DI-1 of the capture unit, the capture root by name, the claim and its journal.
        Any read that fails or does not parse is ``None`` (``observation-failed``)."""
        read = self._units.read_unit(CAPTURE_UNIT, _HL_PROPS)
        if not isinstance(read, ControlOk):
            return None
        v = read.value
        root = self._host_fs.exists(self._s.authority.pins.capture_root)
        claim = self._host_fs.exists(self._paths.consume_dir)
        if root is None or claim is None:
            return None
        consumed, consumed_invocation = False, ""
        if claim:
            data = self._journals.read_journal(
                self._paths.consume_dir,
                max_bytes=self._s.authority.h1.params.journal_max_bytes,
                dir_uid=self._owner.uid,
                dir_mode=0o755,
            )
            if data is not None:
                parsed = parse_journal(
                    data, kind=JournalKind.CONSUME, run=consume_run(self._inv.activation_id)
                )
                if parsed.valid:
                    consumed = bool(parsed.ops("consumed"))
                    invocation = parsed.lines[0].fields["invocation_id"]
                    consumed_invocation = "" if invocation == ABSENT else invocation
        return Observation(
            active_state=str(v[UnitProperty.ACTIVE_STATE]),
            invocation_id=str(v[UnitProperty.INVOCATION_ID]),
            tau=int(v[UnitProperty.INACTIVE_ENTER_TIMESTAMP_MONOTONIC]),
            job=int(v[UnitProperty.JOB]),
            exec_main_start_us=int(v[UnitProperty.EXEC_MAIN_START_TIMESTAMP_MONOTONIC]),
            capture_root=root,
            claim=claim,
            consumed=consumed,
            consumed_invocation=consumed_invocation,
        )

    def _hold_end(self, reason: str, obs: Observation | None, step: str) -> None:
        self._append(
            "hold-end", {"reason": reason, "observation": obs.doc() if obs else ABSENT}, step
        )

    # IGR --------------------------------------------------------------------

    def _igr(self) -> None:
        """IGR-0 … IGR-3: GRR with the in-memory identity, then a best-effort line.
        Nothing else: no lock, no spawn, no signal, no Polkit, no other object."""
        s = self._s
        if s.igr_state != "idle":
            return
        s.igr_state = "running"
        if s.grant is None:
            outcome = GrrOutcome.ABSENT  # AM-2 never reached: no rule of ours exists
        else:
            removal = self._fs.remove(
                self._paths.rule, s.grant, directory=False, before_unlink=lambda _o: None
            )
            outcome, _errno = grr_outcome(removal)
        s.igr = outcome.value
        s.igr_state = "done"
        if s.sink is not None:
            try:
                s.sink.append("igr", {"outcome": outcome.value, "identity": grant_identity_doc(s.grant)})
            except EvidenceWriteError:
                pass  # IGR-2 is best effort; the grant is already decided

    def _run_end(self, outcome: str) -> None:
        """RT2.AM3.2: the last ACT line, after IGR; best effort like ``igr``."""
        if self._s.sink is None:
            return
        try:
            self._s.sink.append("run-end", {"outcome": outcome})
        except EvidenceWriteError:
            pass  # the end class and the grant are already decided

    # helpers ----------------------------------------------------------------

    def _check(self, step: str) -> None:
        if self._flag():
            raise _End(HoldEnd.INTERRUPTED, step)

    def _sleep_until(self, deadline_ms: int, step: str) -> None:
        """Sliced wait (≤ ``slice_ms``), the flag read at every wake-up."""
        slice_ms = self._s.authority.h1.params.slice_ms
        while True:
            self._check(step)
            now = self._clock.monotonic_ms()
            if now >= deadline_ms:
                return
            self._clock.sleep_ms(min(slice_ms, deadline_ms - now))

    def _append(self, op: str, fields: dict, step: str) -> None:
        try:
            self._s.sink.append(op, fields)
        except EvidenceWriteError:
            raise _End(HoldEnd.EVIDENCE_UNWRITABLE, step) from None

    def _release_k(self) -> None:
        if self._s.k_held:
            self._lock.release()
            self._s.k_held = False


def grant_identity_doc(grant: Identity | None) -> dict | str:
    """``igr.identity``: the in-memory identity GRR used, or ``"absent"`` before AM-1G."""
    if grant is None:
        return ABSENT
    return {
        "path": grant.path,
        "dev": grant.dev,
        "ino": grant.ino,
        "sha256": grant.sha256,
        "size": grant.size,
        "mode": grant.mode,
    }
