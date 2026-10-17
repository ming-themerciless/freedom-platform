"""RT-1 ``consume``: CQ-0 … CQ-7, the ``ExecStartPre=+`` role (inventory §5.1).

PID 1 runs it inside the fixed capture unit's start job. It receives nothing from
the requester; its only environment fact is its own ``INVOCATION_ID`` (provenance).
It consumes one accepted activation grant before ``ExecStart=`` may run, and
returns 0 only after ``consumed`` and ``run-end`` are durable.

Order, each step reached only if the one before succeeded:

* **CQ-0** identify the activation from the fixed ``pass-a.json`` (nothing created);
* **CQ-1** try K once, never wait (nothing created);
* **CQ-2** create ``<id>-consume-evidence`` — the same-boot one-shot barrier — its
  journal and ``run-start``, flushed journal → claim directory → ``/var/tmp``;
* **CQ-3** parse the ACT journal and the A-2/H-1 chain, remove the A1-intact live
  rule write-ahead (``remove-intent`` → ``unlinkat`` → ``removed``);
* **CQ-4** re-prove the preconditions, including both DI-1 reads;
* **CQ-5** the rule name is absent and PK/2 (seek-not-authorized, verb ``start``)
  says *not authorized*; ``grant-check`` is appended;
* **CQ-6/CQ-7** ``consumed`` then ``run-end``, release K, exit 0.

**Grant priority.** Once the claim exists, or when it could not be made, a failure
to write evidence reduces what is claimed and never keeps a removable live grant:
the rule is classified and removed from the ACT identity and the pinned authority
digest alone, no line that cannot be made durable is written, PK/2 runs with its
result held in memory, CQ-4 is never reached and the attempt always fails.

Reversible choices pinned by ``tests/test_rp11_consume.py``:

* the A-2 digest is taken from the ACT journal's ``run-start`` (RT-1 has no
  operand) but is trusted only through the root-owned A-2 → H-1 chain: A-2 is
  selected by that digest, names this activation and pins the same pass-config,
  staged-rule and boot facts, and the ACT directory must belong to H-1's operator;
* the staged-rule digest is A-2's pin (never a journal field alone);
* ``pass-a.json`` must carry ``activation_id`` (CQ-0) and the pinned document
  must name the same activation (CQ-4);
* the ACT journal is first read under the largest cap H-1 may set
  (``journal_max_bytes`` 4 MiB) and then held to H-1's own value;
* exit codes: 0 only for complete CQ-7; 21 unidentified, 22 busy, 23 repeated,
  24 claim-failed, 25 evidence-unwritable, 26 precondition, 27 failed, 70 an
  unexpected exception.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from application.unit_control import (
    CAPTURE_UNIT,
    ControlOk,
    ControlSpecError,
    UnitProperty,
    UnitVerb,
    holder_unit_name,
    validate_activation_id,
)

from .attribution import Attribution, classify_file
from .authority import Authority, AuthorityError, load_authority
from .canonical import ABSENT, CanonicalError, canonical_bytes, parse_canonical
from .cleanup import Services
from .evidence import ActEvidence, act_evidence
from .journal import JournalKind, ParsedJournal, consume_run, parse_journal
from .paths import ActivationPaths, Layout
from .pk import PkMode, PkOutcome, PkResult
from .ports import (
    ActivationFs,
    EvidenceSink,
    EvidenceWriteError,
    HoldHost,
    HostFacts,
    LockMode,
    LockPort,
    LockState,
    RecordStore,
    RemovalOutcome,
)
from .records import validate_record

PASS_MAX_BYTES = 65_536
#: The largest ``journal_max_bytes`` H-1 may set; used before H-1 can be read.
ACT_FIRST_READ_BYTES = 4_194_304
INVOCATION_ABSENT = ABSENT


class ConsumeEnd(str, Enum):
    CONSUMED = "consumed"
    UNIDENTIFIED = "consume-unidentified"
    BUSY = "consume-busy"
    REPEATED = "consume-repeated"
    CLAIM_FAILED = "consume-claim-failed"
    EVIDENCE_UNWRITABLE = "consume-evidence-unwritable"
    PRECONDITION = "consume-precondition"
    FAILED = "consume-failed"
    INTERNAL = "consume-internal-error"

    @property
    def exit_code(self) -> int:
        return {
            ConsumeEnd.CONSUMED: 0,
            ConsumeEnd.UNIDENTIFIED: 21,
            ConsumeEnd.BUSY: 22,
            ConsumeEnd.REPEATED: 23,
            ConsumeEnd.CLAIM_FAILED: 24,
            ConsumeEnd.EVIDENCE_UNWRITABLE: 25,
            ConsumeEnd.PRECONDITION: 26,
            ConsumeEnd.FAILED: 27,
            ConsumeEnd.INTERNAL: 70,
        }[self]


@dataclass
class ConsumeOutcome:
    end: ConsumeEnd
    step: str = "none"
    klass: str = "none"
    activation_id: str = "unidentified"
    pk: str = ABSENT  # the CQ-5 series result, also when held in memory only

    @property
    def exit_code(self) -> int:
        return self.end.exit_code

    def line(self) -> str:
        """One bounded diagnostic line: closed tokens and the validated activation id."""
        return (
            f"rp11-consume {self.end.value} {self.activation_id} "
            f"step={self.step} class={self.klass} pk={self.pk}"
        )


# --- ports -------------------------------------------------------------------------


@dataclass(frozen=True)
class PassRead:
    """``pass-a.json`` read through one no-follow descriptor (CQ-0, CQ-4)."""

    data: bytes
    dev: int
    ino: int


@dataclass(frozen=True)
class ActJournalRead:
    data: bytes
    dir_uid: int  # owner of the ACT directory; must be H-1's operator


class ConsumeHost(Protocol):
    def read_pass_config(self, path: str, *, max_bytes: int) -> PassRead | None:
        """Parent opened component by component without following a link; the file
        regular, root-owned, ``0644``, one link, within the cap; read once."""
        ...

    def read_act_journal(self, directory: str, *, max_bytes: int) -> ActJournalRead | None:
        """``<directory>/journal`` (root-owned ``0644`` regular, one link, within the
        cap) of a ``0700`` directory, with the directory's owner."""
        ...


class ClaimExists(Exception):
    """``EEXIST`` at the barrier: a claim was made earlier in this boot."""


class ClaimNotMade(Exception):
    """The barrier was not created (``/var/tmp`` unusable or any other error)."""


class ClaimEvidenceFailure(Exception):
    """The barrier exists but its directory or journal could not be made."""


class Claim(Protocol):
    """The made claim: journal exclusively created ``0644`` in a ``0755`` directory."""

    @property
    def identity(self) -> tuple[int, int]: ...

    @property
    def sink(self) -> EvidenceSink: ...

    def flush_directories(self) -> None:
        """Flush the claim directory, then ``/var/tmp`` (``EvidenceWriteError``)."""
        ...

    def close(self) -> None: ...


class ClaimStore(Protocol):
    def create(self) -> Claim:
        """``<id>-consume-evidence`` as a root ``0700`` directory, no replace: the
        barrier. ``ClaimExists`` for ``EEXIST`` (nothing else is opened),
        ``ClaimNotMade`` before the barrier, ``ClaimEvidenceFailure`` after it."""
        ...


@dataclass
class ConsumePorts:
    """Everything that depends on the validated activation id."""

    fs: ActivationFs
    records: RecordStore
    lock: LockPort
    claims: ClaimStore
    host_fs: HoldHost
    host: HostFacts
    consume_host: ConsumeHost
    services: Services
    tool_sha256: str = ABSENT


# --- state -------------------------------------------------------------------------


class _Fail(Exception):
    def __init__(self, step: str, klass: str) -> None:
        super().__init__(f"{step} {klass}")
        self.step, self.klass = step, klass


@dataclass(frozen=True)
class _Chain:
    authority: Authority
    parsed: ParsedJournal
    act: ActEvidence


@dataclass
class _State:
    activation_id: str = ""
    paths: ActivationPaths | None = None
    ports: ConsumePorts | None = None
    pass_read: PassRead | None = None
    claim: Claim | None = None
    act_read: ActJournalRead | None = None
    chain: _Chain | None = None
    lock_state: LockState | None = None
    gp: bool = False  # the journal accepts no further line: grant-priority form
    removed_here: bool = False
    pk: PkResult | None = None
    pk_attempted: bool = False  # set before the series is entered: never retried, whatever it does
    step: str = "CQ-1"  # the stage being executed, for the fixed internal diagnostic


class ConsumeProcedure:
    def __init__(
        self,
        layout: Layout,
        *,
        invocation_id: str,
        ports_for: Callable[[ActivationPaths], ConsumePorts],
        pass_host: ConsumeHost,
    ) -> None:
        self._layout = layout
        self._invocation_id = invocation_id
        self._ports_for = ports_for
        self._pass_host = pass_host
        self._s = _State()

    # ------------------------------------------------------------------
    # public
    # ------------------------------------------------------------------

    def run(self) -> ConsumeOutcome:
        s = self._s
        activation_id = self._identify()
        if activation_id is None:
            return ConsumeOutcome(ConsumeEnd.UNIDENTIFIED, "CQ-0", "pass-config")
        s.activation_id = activation_id
        s.paths = ActivationPaths(self._layout, activation_id)
        s.ports = self._ports_for(s.paths)
        try:
            lock = self._take_k()
            if isinstance(lock, ConsumeOutcome):
                lock.activation_id = activation_id
                return lock
            try:
                outcome = self._claimed()
            except Exception:  # noqa: BLE001 - fail closed; the grant is still removed
                outcome = self._grant_priority(ConsumeEnd.INTERNAL, s.step, "unexpected")
            outcome.activation_id = activation_id
            if s.pk is not None:
                outcome.pk = s.pk.outcome.value
            return outcome
        finally:
            s.ports.lock.release()  # CQ-7: K is closed on every return and exception
            if s.claim is not None:
                s.claim.close()

    # ------------------------------------------------------------------
    # CQ-0 / CQ-1
    # ------------------------------------------------------------------

    def _identify(self) -> str | None:
        """CQ-0: only a valid ``activation_id`` is parsed; anything else creates nothing."""
        read = self._pass_host.read_pass_config(self._layout.pass_config, max_bytes=PASS_MAX_BYTES)
        if read is None:
            return None
        try:
            doc = parse_canonical(read.data)
            if type(doc) is not dict:
                return None
            activation_id = validate_activation_id(doc.get("activation_id"))
        except (CanonicalError, ControlSpecError):
            return None
        self._s.pass_read = read
        return activation_id

    def _take_k(self) -> LockState | ConsumeOutcome:
        """CQ-1: one non-blocking attempt; never wait, scan, signal or kill the holder."""
        state = self._s.ports.lock.acquire(0)
        if state.mode is LockMode.ABSENT or state.object is None:
            return self._done(ConsumeEnd.UNIDENTIFIED, "CQ-1", "k-unusable")
        if state.mode is not LockMode.HELD:
            return self._done(ConsumeEnd.BUSY, "CQ-1", "k-held")
        self._s.lock_state = state
        return state

    # ------------------------------------------------------------------
    # CQ-2 .. CQ-7
    # ------------------------------------------------------------------

    def _claimed(self) -> ConsumeOutcome:
        s = self._s
        s.step = "CQ-2"
        try:
            s.claim = s.ports.claims.create()
        except ClaimExists:
            return self._done(ConsumeEnd.REPEATED, "CQ-2", "claim-exists")
        except ClaimNotMade:
            return self._grant_priority(ConsumeEnd.CLAIM_FAILED, "CQ-2", "claim-not-made")
        except ClaimEvidenceFailure:
            return self._grant_priority(ConsumeEnd.EVIDENCE_UNWRITABLE, "CQ-2", "claim-evidence")
        if not self._run_start():
            return self._grant_priority(ConsumeEnd.EVIDENCE_UNWRITABLE, "CQ-2", "run-start")
        try:
            s.step = "CQ-3"
            chain = self._load_chain()
            s.chain = chain
            self._cq3(chain)
        except _Fail as failure:
            return self._failed(ConsumeEnd.FAILED, failure.step, failure.klass)
        if s.gp:
            return self._grant_priority(ConsumeEnd.EVIDENCE_UNWRITABLE, "CQ-3", "evidence")
        try:
            s.step = "CQ-4"
            tau0 = self._cq4(chain)
            s.step = "CQ-5"
            pk = self._cq5(chain)
        except _Fail as failure:
            end = ConsumeEnd.PRECONDITION if failure.step == "CQ-4" else ConsumeEnd.FAILED
            return self._failed(end, failure.step, failure.klass)
        if s.gp:
            return self._grant_priority(ConsumeEnd.EVIDENCE_UNWRITABLE, "CQ-5", "evidence")
        s.step = "CQ-6"
        if not self._append("consumed", {"pk_status": pk.outcome.value, "inactive_enter_us": tau0}):
            return self._grant_priority(ConsumeEnd.EVIDENCE_UNWRITABLE, "CQ-6", "consumed")
        s.step = "CQ-7"
        if not self._append("run-end", {"outcome": "consumed"}):
            # ``consumed`` is durable but the attempt is not complete: PID 1 must not
            # execute ExecStart=. The grant is already removed.
            return self._done(ConsumeEnd.EVIDENCE_UNWRITABLE, "CQ-7", "run-end")
        return self._done(ConsumeEnd.CONSUMED)

    def _run_start(self) -> bool:
        """CQ-2 (continued): ACT journal digest, boot, ``run-start``, then the flushes."""
        s = self._s
        ports = s.ports
        act = self._read_act()
        boot = ports.host.boot_id()
        if act is None or boot is None:
            return False
        lock = s.lock_state.object
        fields = {
            "invocation_id": self._invocation_id,
            "boot_id": boot,
            "claim": {"dev": s.claim.identity[0], "ino": s.claim.identity[1]},
            "act_journal": {"sha256": hashlib.sha256(act.data).hexdigest(), "length": len(act.data)},
            "lock": {
                "object": {"path": lock.path, "dev": lock.dev, "ino": lock.ino},
                "mode": "held",
                "wait_ms": 0,
            },
            "helper": {"role": "consume", "tool_sha256": ports.tool_sha256},
        }
        if not self._append("run-start", fields):
            return False
        try:
            s.claim.flush_directories()
        except EvidenceWriteError:
            s.gp = True
            return False
        return True

    def _read_act(self) -> ActJournalRead | None:
        s = self._s
        if s.act_read is None:
            s.act_read = s.ports.consume_host.read_act_journal(
                s.paths.act_dir, max_bytes=ACT_FIRST_READ_BYTES
            )
        return s.act_read

    # CQ-3 --------------------------------------------------------------------

    def _load_chain(self) -> _Chain:
        """Parse the ACT journal and the authority chain (H-JRN.8/9); same boot."""
        s = self._s
        ports, paths = s.ports, s.paths
        read = self._read_act()
        if read is None:
            raise _Fail("CQ-3", "act-journal")
        parsed = parse_journal(read.data, kind=JournalKind.ACT, run=s.activation_id)
        if not parsed.valid:
            raise _Fail("CQ-3", "invalid-journal")
        try:
            authority = load_authority(
                ports.fs,
                paths,
                a2_sha256=parsed.lines[0].fields["a2_sha256"],
                activation_id=s.activation_id,
            )
        except AuthorityError:
            raise _Fail("CQ-3", "invalid-authority") from None
        pins = authority.pins
        if read.dir_uid != authority.h1.operator.uid or len(read.data) > authority.h1.params.journal_max_bytes:
            raise _Fail("CQ-3", "invalid-journal")
        act = act_evidence(parsed)
        if (
            act.a2_sha256 != pins.sha256
            or act.pass_config_sha256 != pins.pass_config_sha256
            or act.staged_rule_sha256 != pins.staged_rule_sha256
            or act.boot_id != pins.boot_id
        ):
            raise _Fail("CQ-3", "invalid-authority")
        if ports.host.boot_id() != pins.boot_id:
            raise _Fail("CQ-3", "boot")
        return _Chain(authority, parsed, act)

    def _cq3(self, chain: _Chain) -> None:
        klass = self._remove_grant(chain)
        if klass != "removed" and not self._s.gp:
            raise _Fail("CQ-3", klass)

    def _remove_grant(self, chain: _Chain) -> str:
        """CQ-3 / grant-priority removal. Only an A1-intact rule is removed, from the
        ACT identity and A-2's staged-rule digest; every other result is a class."""
        s = self._s
        fs, paths = s.ports.fs, s.paths
        rule = paths.rule
        identity = chain.act.file(rule)
        if (
            identity is None
            or rule not in chain.act.grant_paths
            or identity.sha256 != chain.authority.pins.staged_rule_sha256
        ):
            return "unprovable"
        observed = fs.observe(rule)
        if observed is None:
            return "absent"
        attribution = classify_file(identity, observed, self._layout.owner)
        if attribution is not Attribution.A1_INTACT:
            return _kept_class(attribution)

        def write_ahead(seen) -> None:
            self._append(
                "remove-intent",
                {"path": rule, "dev": seen.dev, "ino": seen.ino, "sha256": seen.sha256 or ABSENT},
            )

        removal = fs.remove(rule, identity, directory=False, before_unlink=write_ahead)
        if removal.outcome is RemovalOutcome.REMOVED:
            s.removed_here = True
            self._append("removed", {"path": rule})
            return "removed"
        if removal.outcome is RemovalOutcome.ABSENT:
            return "absent"
        if removal.outcome is RemovalOutcome.UNREMOVABLE:
            self._append("remove-failed", {"path": rule, "errno": removal.errno})
            return "unremovable"
        return _kept_class(removal.attribution)

    # CQ-4 --------------------------------------------------------------------

    def _cq4(self, chain: _Chain) -> int:
        """Re-prove the preconditions under the lock, after the grant is gone. Every
        read error or mismatch fails closed; a satisfied read is not evidence of absence."""
        s = self._s
        ports, paths, pins = s.ports, s.paths, chain.authority.pins
        owner = self._layout.owner

        again = ports.consume_host.read_pass_config(paths.pass_config, max_bytes=PASS_MAX_BYTES)
        first = s.pass_read
        identity = chain.act.file(paths.pass_config)
        observed = ports.fs.observe(paths.pass_config)
        if (
            again is None
            or (again.dev, again.ino) != (first.dev, first.ino)
            or again.data != first.data
            or hashlib.sha256(again.data).hexdigest() != pins.pass_config_sha256
            or again.data != pins.pass_bytes
            or pins.pass_config.get("activation_id") != s.activation_id
            or identity is None
            or identity.sha256 != pins.pass_config_sha256
            or classify_file(identity, observed, owner) is not Attribution.A1_INTACT
            or (observed.dev, observed.ino) != (first.dev, first.ino)
        ):
            raise _Fail("CQ-4", "pass-config")
        if ports.host.boot_id() != pins.boot_id:
            raise _Fail("CQ-4", "boot")
        self._require_activated_record(pins.sha256)
        tau0 = self._hold_started(chain)
        attempts = ports.fs.list_prefixed(self._layout.var_tmp, paths.attempt_prefix)
        deact = ports.records.deact_attempts(s.activation_id)
        if attempts != () or deact != ():
            raise _Fail("CQ-4", "deactivation-evidence")
        if ports.host_fs.exists(pins.capture_root) is not False:
            raise _Fail("CQ-4", "capture-root")
        units = ports.services.units(chain.authority.h1.params)
        self._holder_active(units, chain)
        self._capture_activating(units, tau0)
        return tau0

    def _require_activated_record(self, a2_sha256: str) -> None:
        data = self._s.ports.records.read(self._s.paths.act_record_name())
        try:
            doc = parse_canonical(data) if data is not None else None
            if doc is None:
                raise ValueError
            validate_record(doc)
            ok = (
                doc["kind"] == "act"
                and doc["attempt"] == 0
                and doc["activation_id"] == self._s.activation_id
                and doc["authority"]["a2_sha256"] == a2_sha256
                and doc["outcome"] == "activated"
            )
        except (CanonicalError, ValueError, KeyError, TypeError):
            ok = False
        if not ok:
            raise _Fail("CQ-4", "act-record")

    def _hold_started(self, chain: _Chain) -> int:
        """A fresh read of the ACT journal: ``hold-start`` and no ``hold-end``."""
        s = self._s
        read = s.ports.consume_host.read_act_journal(s.paths.act_dir, max_bytes=ACT_FIRST_READ_BYTES)
        if read is None or read.dir_uid != chain.authority.h1.operator.uid:
            raise _Fail("CQ-4", "act-journal")
        if len(read.data) > chain.authority.h1.params.journal_max_bytes:
            raise _Fail("CQ-4", "act-journal")
        parsed = parse_journal(read.data, kind=JournalKind.ACT, run=s.activation_id)
        if not parsed.valid or parsed.lines[0].fields != chain.parsed.lines[0].fields:
            raise _Fail("CQ-4", "act-journal")
        starts, ends = parsed.ops("hold-start"), parsed.ops("hold-end")
        if len(starts) != 1 or ends:
            raise _Fail("CQ-4", "hold")
        return starts[0].fields["capture"]["inactive_enter_us"]

    def _holder_active(self, units, chain: _Chain) -> None:
        """OS-4: the holder is ``active`` with the journaled invocation id."""
        read = units.read_unit(
            holder_unit_name(self._s.activation_id),
            (UnitProperty.ACTIVE_STATE, UnitProperty.INVOCATION_ID),
        )
        journaled = chain.act.holder_invocation_id
        if (
            not isinstance(read, ControlOk)
            or journaled == ABSENT
            or str(read.value[UnitProperty.ACTIVE_STATE]) != "active"
            or str(read.value[UnitProperty.INVOCATION_ID]) != journaled
        ):
            raise _Fail("CQ-4", "holder")

    def _capture_activating(self, units, tau0: int) -> None:
        """OS-1: the capture unit is ``activating`` with RT-1's own invocation id and
        the journaled inactive-enter timestamp. Without a real id nothing can match."""
        read = units.read_unit(
            CAPTURE_UNIT,
            (
                UnitProperty.ACTIVE_STATE,
                UnitProperty.INVOCATION_ID,
                UnitProperty.INACTIVE_ENTER_TIMESTAMP_MONOTONIC,
            ),
        )
        if (
            not isinstance(read, ControlOk)
            or self._invocation_id == INVOCATION_ABSENT
            or str(read.value[UnitProperty.ACTIVE_STATE]) != "activating"
            or str(read.value[UnitProperty.INVOCATION_ID]) != self._invocation_id
            or int(read.value[UnitProperty.INACTIVE_ENTER_TIMESTAMP_MONOTONIC]) != tau0
        ):
            raise _Fail("CQ-4", "capture")

    # CQ-5 --------------------------------------------------------------------

    def _cq5(self, chain: _Chain) -> PkResult:
        s = self._s
        if s.ports.fs.observe(s.paths.rule) is not None:
            raise _Fail("CQ-5", "removed-unconfirmed")
        pk = self._run_pk(chain)
        for child in pk.children:
            self._append("child", {"entry": child})
        self._append(
            "grant-check",
            {
                "verb": "start",
                "mode": pk.mode.value,
                "outcome": pk.outcome.value,
                "reason": pk.reason,
                "calls": pk.calls,
            },
        )
        if s.gp:
            return pk  # the caller turns an unwritable journal into the grant-priority end
        if pk.outcome is not PkOutcome.NOT_AUTHORIZED:
            raise _Fail("CQ-5", "removed-unconfirmed")
        return pk

    def _run_pk(self, chain: _Chain) -> PkResult:
        self._s.pk_attempted = True  # an exception, error or abandonment inside the series is still an attempt
        series = self._s.ports.services.pk(chain.authority.h1.params)
        self._s.pk = series.run(chain.authority.h1.operator, UnitVerb.START, PkMode.SEEK_NOT_AUTHORIZED)
        return self._s.pk

    # ------------------------------------------------------------------
    # endings
    # ------------------------------------------------------------------

    def _done(self, end: ConsumeEnd, step: str = "none", klass: str = "none") -> ConsumeOutcome:
        return ConsumeOutcome(end, step, klass)

    def _failed(self, end: ConsumeEnd, step: str, klass: str) -> ConsumeOutcome:
        """A failure with a journal: ``consume-failed`` then ``run-end``. The selected
        result stands only while both lines are written and flushed; if either is not,
        the journal is unusable and the accepted grant-priority form decides the end."""
        if not self._append("consume-failed", {"step": step.lower(), "class": klass}):
            return self._grant_priority(ConsumeEnd.EVIDENCE_UNWRITABLE, step, "evidence")
        if not self._append("run-end", {"outcome": "failed"}):
            return self._grant_priority(ConsumeEnd.EVIDENCE_UNWRITABLE, step, "run-end")
        return ConsumeOutcome(end, step, klass)

    def _grant_priority(self, end: ConsumeEnd, step: str, klass: str) -> ConsumeOutcome:
        """The accepted grant-priority form: remove what is provably ours, write no
        line, hold the PK/2 result in memory, never reach CQ-4, always fail."""
        s = self._s
        s.gp = True
        try:
            chain = s.chain or self._load_chain()
            s.chain = chain
            if not s.removed_here:
                self._remove_grant(chain)
            if not s.pk_attempted and s.ports.fs.observe(s.paths.rule) is None:
                self._run_pk(chain)
        except Exception:  # noqa: BLE001 - nothing here can turn a failure into success
            pass
        return ConsumeOutcome(end, step, klass)

    def _append(self, op: str, fields: dict) -> bool:
        """Append and flush; on failure the journal is unusable and nothing more is written."""
        s = self._s
        if s.gp or s.claim is None:
            return False
        try:
            s.claim.sink.append(op, fields)
        except EvidenceWriteError:
            s.gp = True
            return False
        return True


def _kept_class(attribution: Attribution | None) -> str:
    if attribution is Attribution.UNINSPECTED:
        return "uninspected"
    if attribution is Attribution.A1_DAMAGED:
        return "damaged"
    return "foreign"

