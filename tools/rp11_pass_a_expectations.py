"""RP-11 Pass A material expected results (decision D1): pure, fail-closed evaluation.

**Review precursor. Not wired, not covered, not authority.** Nothing operational
imports this module. It is outside the review manifest's covered package and
outside the SA-2 build closure, so changing it moves no digest or pin.
``EvaluationContinuation`` fits ``pass_a``'s opt-in continuation seam, but nothing
constructs it outside tests. Wiring it (with the manifest and the artifact) is a
later, separately reviewed step.

It starts no process, opens no file, contacts no host and reads no clock. It
judges values the caller already holds: the admitted capture record of one act,
the digest under which that record was admitted, and the two complete stream
byte strings.

Rules:

* Only ``MATCH`` and ``RECORDED`` let a pass continue. ``MISMATCH`` (the
  evidence contradicts the expectation or cannot be trusted) and
  ``UNESTABLISHED`` (there is no evidence, or no reviewed form to judge it by)
  both stop it. There is no third way to succeed.
* Evidence is judged only after it is bound: admitted, record digest equal,
  stream sizes and digests equal to the record's, and pass id, step, sequence
  and argv equal to the plan's.
* Every expected value is a required input with no default. None is taken from
  the evidence it judges. Mappings are copied at construction and are read-only.
* The ``ENOENT`` diagnostic for the run root has no reviewed form yet. It may
  be passed as ``None``; A1-19 is then ``UNESTABLISHED`` and the pass stops. A
  supplied form must fit one narrow single-line grammar. That grammar is
  synthetic: it is not an observation of the target's ``stat``.

What the caller must guarantee, because this module cannot check it (through
``EvaluationContinuation``, the first point rests on the evidence having come from
the current session's ``admitted_evidence``):

* The admitted record digest comes from a trusted admission made by the
  **current invocation**. ``CaptureRecord`` has no per-record ``InvocationID``,
  so equal pass id, step, sequence and argv do not show which invocation wrote a
  record. A future integration must bind the digest to the current chain.
* The planned argv comes from the reviewed, pinned plan. This module checks the
  step ids and their order, not that the argv are the reviewed ones.

Not covered here, by design: X-3, X-4 and the finalization result (the capture
mechanism owns them), authority and start checks, the capture-tool digest check
(A0-08), and any observation the plan does not make (see the candidate's D4
record). A matching evaluation is not a completed pass.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Callable, Mapping, Sequence

from .phase_5_0_evidence.capture_contract import (
    AdmittedEvidence,
    CaptureRecord,
    require_invocation_id,
    sha256_hex,
)

_SURVEY_AGAIN = ("19", "21", "23a", "23b", "23c", "23d", "23e", "23f", "23g", "24")

#: The default plan's 49 acts in order. A test holds this equal to the plan. The
#: A1-C steps (A1-11, A1-12) are not supported while RP-10 is unmet.
STEP_IDS: tuple[str, ...] = (
    "A0-02a", "A0-02b", "A0-03", "A0-04", "A0-05", "A1-S2",
    "A1-01", "A1-02", "A1-03", "A1-04", "A1-05", "A1-06", "A1-07", "A1-08",
    "A1-09", "A1-10", "A1-13", "A1-16", "A1-17", "A1-18",
    "A1-19", "A1-20", "A1-21",
    "A1-23a", "A1-23b", "A1-23c", "A1-23d", "A1-23e", "A1-23f", "A1-23g",
    "A1-24", "A1-25", "A1-26", "A1-27", "A1-28", "A1-29", "A1-30",
    *(f"A1-Z-{suffix}" for suffix in _SURVEY_AGAIN),
    "A1-Z-29", "A1-Z-30",
)

#: Each final-survey act and the earlier act its complete result must equal.
FINAL_SURVEY_PAIRS: Mapping[str, str] = {
    f"A1-Z-{suffix}": f"A1-{suffix}" for suffix in (*_SURVEY_AGAIN, "29", "30")
}

#: The five A1-S2 sources, as the path suffix each ``sha256sum`` operand must have.
SOURCE_PIN_NAMES: tuple[str, ...] = (
    "journal.py",
    "unit_sandbox.py",
    "execution/case_program.py",
    "execution/cli.py",
    "reservation.py",
)

DRY_RUN_HEADER = "DRY RUN — nothing was executed."
#: The dry-run fields the old draft pins. Other printed lines are not pinned.
DRY_RUN_FIELDS: tuple[str, ...] = (
    "steps planned",
    "mutations declared",
    "cleanup steps derived",
    "unresolved conflicts",
    "unconfirmed facts",
    "review manifest digest",
    "executable",
)

_ABSENT_IDENTITY_STEPS = frozenset(
    f"{prefix}23{letter}" for prefix in ("A1-", "A1-Z-") for letter in "abcdefg"
)
_RUN_ROOT_STEPS = frozenset({"A1-19", "A1-Z-19"})
#: Observations with no material expected value: kept for the record, never compared
#: to a pin. The first set must print something other than whitespace; the second may
#: legitimately be empty.
_RECORDED_NONEMPTY = frozenset({"A1-09", "A1-10", "A1-17", "A1-18", "A1-25", "A1-26"})
_RECORDED_MAY_BE_EMPTY = frozenset({"A1-27", "A1-28"})

_SHA256 = re.compile(r"[0-9a-f]{64}")
_COMMIT = re.compile(r"[0-9a-f]{40}")
_BOOT_ID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
#: The only shapes a supplied ``ENOENT`` form may have: one line, one program name,
#: one verb, one quoted path, the ``ENOENT`` reason and nothing else. Synthetic, not
#: reviewed against the target; a different real shape needs a reviewed change here.
_ENOENT_FORM = re.compile(
    rb"(?:stat|/usr/bin/stat): cannot (?:stat|statx) "
    rb"'(/[A-Za-z0-9._/-]+)': No such file or directory\n"
)


class Outcome(str, Enum):
    MATCH = "match"
    #: Bound, accepted exit, readable; no material expected value exists for it.
    RECORDED = "recorded"
    MISMATCH = "mismatch"
    UNESTABLISHED = "unestablished"


class ExpectationRefused(ValueError):
    """The expected values or the plan are malformed; nothing was evaluated."""


def _single_line(value: object) -> bool:
    return isinstance(value, str) and bool(value) and "\n" not in value and "\r" not in value


@dataclass(frozen=True, slots=True, kw_only=True)
class Expectations:
    """Every externally fixed value. All are required; none has a default."""

    pass_id: str
    pinned_commit: str
    prompt_sha256: str
    manifest_json_sha256: str
    concrete_plan_sha256: str
    source_sha256: Mapping[str, str]
    #: ``DRY_RUN_FIELDS`` name to the exact text after ``": "``.
    dry_run: Mapping[str, str]
    nodename: str
    kernel_release: str
    machine: str
    os_pretty_name: str
    var_lib_source: str
    var_lib_fstype: str
    #: The complete stderr of the planned ``stat`` of an absent run root, or ``None``
    #: while no reviewed, pinned form exists.
    run_root_enoent_stderr: bytes | None

    def __post_init__(self) -> None:
        # Snapshot before validating, so what is checked is what is later compared.
        for name in ("source_sha256", "dry_run"):
            supplied = getattr(self, name)
            if not isinstance(supplied, Mapping):
                raise ExpectationRefused(name)
            object.__setattr__(self, name, MappingProxyType(dict(supplied)))
        digests = (self.prompt_sha256, self.manifest_json_sha256, self.concrete_plan_sha256)
        texts = (
            self.pass_id, self.nodename, self.kernel_release, self.machine,
            self.os_pretty_name, self.var_lib_source, self.var_lib_fstype,
        )
        if not (isinstance(self.pinned_commit, str) and _COMMIT.fullmatch(self.pinned_commit)):
            raise ExpectationRefused("pinned_commit")
        if set(self.source_sha256) != set(SOURCE_PIN_NAMES):
            raise ExpectationRefused("source_sha256")
        for digest in (*digests, *self.source_sha256.values()):
            if not (isinstance(digest, str) and _SHA256.fullmatch(digest)):
                raise ExpectationRefused("sha256")
        if set(self.dry_run) != set(DRY_RUN_FIELDS) or not all(
            _single_line(v) for v in self.dry_run.values()
        ):
            raise ExpectationRefused("dry_run")
        if not _SHA256.fullmatch(self.dry_run["review manifest digest"]):
            raise ExpectationRefused("dry_run")
        if self.dry_run["executable"] != "False":
            raise ExpectationRefused("dry_run")
        if not all(_single_line(text) for text in texts):
            raise ExpectationRefused("text")
        form = self.run_root_enoent_stderr
        if form is not None and not (isinstance(form, bytes) and _ENOENT_FORM.fullmatch(form)):
            raise ExpectationRefused("run_root_enoent_stderr")


@dataclass(frozen=True, slots=True)
class PlannedAct:
    step_id: str
    argv: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ActEvidence:
    """What the caller holds about one act. ``admitted_record_sha256`` must come from
    a trusted admission by the current invocation (the act outcome or the index of
    the current chain), never from ``record``. This module cannot verify that."""

    admitted: bool
    admitted_record_sha256: str | None
    record: CaptureRecord | None
    stdout: bytes | None
    stderr: bytes | None


@dataclass(frozen=True, slots=True)
class Verdict:
    step_id: str
    outcome: Outcome
    #: A fixed code; never captured content.
    reason: str
    #: Citation of the judged evidence; ``None`` when it could not be bound.
    capture_seq: int | None = None
    record_sha256: str | None = None
    stdout_sha256: str | None = None
    stderr_sha256: str | None = None

    @property
    def permits_continuation(self) -> bool:
        return self.outcome in (Outcome.MATCH, Outcome.RECORDED)


@dataclass(frozen=True, slots=True)
class Evaluation:
    verdicts: tuple[Verdict, ...]

    @property
    def established(self) -> bool:
        """Every planned act, once, in order, permits continuation."""
        return tuple(v.step_id for v in self.verdicts) == STEP_IDS and all(
            v.permits_continuation for v in self.verdicts
        )

    @property
    def first_failure(self) -> Verdict | None:
        return next((v for v in self.verdicts if not v.permits_continuation), None)


class _Mismatch(Exception):
    pass


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise _Mismatch(reason)


def _lines(data: bytes) -> list[str]:
    """Complete newline-terminated UTF-8 lines; anything else is unreadable."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise _Mismatch("unreadable-output") from None
    _require(text.endswith("\n") and "\r" not in text and "\0" not in text, "unreadable-output")
    return text[:-1].split("\n")


def _one_line(data: bytes) -> str:
    lines = _lines(data)
    _require(len(lines) == 1, "line-count")
    return lines[0]


def _exactly(data: bytes, expected: str) -> None:
    _require(data == (expected + "\n").encode("utf-8"), "value")


def _digest_listing(data: bytes, argv: tuple[str, ...], expected: Sequence[tuple[str, str]]) -> None:
    """``sha256sum`` output for exactly the planned operands, ``expected`` by path suffix."""
    operands = argv[1:]
    _require(len(operands) == len(expected), "planned-operands")
    for operand, (suffix, _) in zip(operands, expected):
        _require(operand.endswith("/" + suffix), "planned-operands")
    wanted = [f"{digest}  {operand}" for operand, (_, digest) in zip(operands, expected)]
    _require(_lines(data) == wanted, "digest")


def _dry_run(data: bytes, expected: Mapping[str, str]) -> None:
    lines = _lines(data)
    _require(lines[0] == DRY_RUN_HEADER and lines.count(DRY_RUN_HEADER) == 1, "dry-run-header")
    for name in DRY_RUN_FIELDS:
        pattern = re.compile(rf"  {re.escape(name)} *: (.*)")
        values = [m.group(1) for line in lines if (m := pattern.fullmatch(line))]
        _require(len(values) == 1, "dry-run-field-count")
        _require(values[0] == expected[name], "dry-run-value")


def _tool_listing(data: bytes, argv: tuple[str, ...]) -> None:
    """A1-16: ``%n %U:%G %a`` for each planned tool: root-owned, not group/world writable."""
    paths = argv[2:]
    lines = _lines(data)
    _require(bool(paths) and len(lines) == len(paths), "line-count")
    for line, path in zip(lines, paths):
        match = re.fullmatch(rf"{re.escape(path)} root:root ([0-7]{{3,4}})", line)
        _require(match is not None, "owner-or-name")
        _require(int(match.group(1), 8) & 0o022 == 0, "writable")


#: V3, V12, V4, V5 of the old draft. V9 (``laboratory/runs``) is not observed by the plan.
_SURVEYED = (
    "root:root 644 regular file",
    "root:root 755 directory",
    "root:freedomlab 750 directory",
    "root:root 700 directory",
)


def _surveyed_paths(data: bytes, argv: tuple[str, ...]) -> None:
    paths = argv[2:]
    _require(len(paths) == len(_SURVEYED), "planned-operands")
    _require(_lines(data) == [f"{p} {state}" for p, state in zip(paths, _SURVEYED)], "value")


def _lab_group(data: bytes) -> None:
    fields = _one_line(data).split(":")
    _require(len(fields) == 4 and fields[0] == "freedomlab" and fields[2].isdigit(), "group-entry")
    _require("ubuntu" in fields[3].split(","), "member")


def _mount(data: bytes, source: str, fstype: str) -> None:
    fields = _one_line(data).split()
    _require(len(fields) == 3 and fields[:2] == [source, fstype], "mount")
    _require(fields[2].split(",")[0] == "rw", "mount-not-rw")


def _clusters(data: bytes) -> None:
    fields = _one_line(data).split()
    _require(len(fields) >= 4 and fields[:4] == ["18", "main", "5432", "online"], "cluster")


def _match(pattern: str, data: bytes) -> None:
    _require(re.fullmatch(pattern, _one_line(data)) is not None, "form")


_Check = Callable[[bytes, tuple[str, ...], Expectations], None]

_STDOUT_CHECKS: Mapping[str, _Check] = {
    "A0-02a": lambda out, argv, e: _exactly(out, e.pinned_commit),
    "A0-02b": lambda out, argv, e: _require(out == b"", "dirty-checkout"),
    "A0-03": lambda out, argv, e: _digest_listing(
        out, argv, [("phase-5-0-p5-r5-operational-evidence-authorization-prompt.md", e.prompt_sha256)]
    ),
    "A0-04": lambda out, argv, e: _digest_listing(
        out,
        argv,
        [
            ("phase-5-0-evidence-harness-review-manifest.json", e.manifest_json_sha256),
            ("phase-5-0-evidence-harness-concrete-plan.md", e.concrete_plan_sha256),
        ],
    ),
    "A0-05": lambda out, argv, e: _dry_run(out, e.dry_run),
    "A1-S2": lambda out, argv, e: _digest_listing(
        out, argv, [(name, e.source_sha256[name]) for name in SOURCE_PIN_NAMES]
    ),
    "A1-01": lambda out, argv, e: _exactly(out, e.nodename),
    "A1-02": lambda out, argv, e: _exactly(out, e.kernel_release),
    "A1-03": lambda out, argv, e: _exactly(out, e.machine),
    "A1-04": lambda out, argv, e: _exactly(out, f'PRETTY_NAME="{e.os_pretty_name}"'),
    "A1-05": lambda out, argv, e: _require(_BOOT_ID.fullmatch(_one_line(out)) is not None, "form"),
    "A1-06": lambda out, argv, e: _match(r"[0-9a-f]{64}  /etc/machine-id", out),
    "A1-07": lambda out, argv, e: _mount(out, e.var_lib_source, e.var_lib_fstype),
    "A1-08": lambda out, argv, e: _exactly(out, "fs.protected_hardlinks = 1"),
    "A1-13": lambda out, argv, e: _match(r"\(3, 14, [0-9]+\) 1 1", out),
    "A1-16": lambda out, argv, e: _tool_listing(out, argv),
    "A1-20": lambda out, argv, e: _lab_group(out),
    **{f"{p}21": lambda out, argv, e: _surveyed_paths(out, argv) for p in ("A1-", "A1-Z-")},
    **{f"{p}24": lambda out, argv, e: _exactly(out, "LoadState=not-found") for p in ("A1-", "A1-Z-")},
    **{f"{p}29": lambda out, argv, e: _exactly(out, "active") for p in ("A1-", "A1-Z-")},
    **{f"{p}30": lambda out, argv, e: _clusters(out) for p in ("A1-", "A1-Z-")},
}


def _accepted_status(step_id: str) -> int:
    if step_id in _RUN_ROOT_STEPS:
        return 1
    return 2 if step_id in _ABSENT_IDENTITY_STEPS else 0


def _binding_problem(
    expectations: Expectations, planned: PlannedAct, capture_seq: int, evidence: ActEvidence
) -> tuple[Outcome, str] | None:
    """Why ``evidence`` cannot be judged at all, or ``None`` when it is bound."""
    record = evidence.record
    if (
        evidence.admitted is not True
        or evidence.admitted_record_sha256 is None
        or not isinstance(record, CaptureRecord)
    ):
        return Outcome.UNESTABLISHED, "not-admitted"
    if not isinstance(evidence.stdout, bytes) or not isinstance(evidence.stderr, bytes):
        return Outcome.UNESTABLISHED, "stream-missing"
    if sha256_hex(record.to_bytes()) != evidence.admitted_record_sha256:
        return Outcome.MISMATCH, "record-digest"
    for data, binding in ((evidence.stdout, record.stdout), (evidence.stderr, record.stderr)):
        if len(data) != binding.size or sha256_hex(data) != binding.sha256:
            return Outcome.MISMATCH, "stream-digest"
    if (
        record.pass_id != expectations.pass_id
        or record.step_or_case_id != planned.step_id
        or record.capture_seq != capture_seq
        or record.argv != planned.argv
    ):
        return Outcome.MISMATCH, "record-not-the-planned-act"
    return None


def _validated_plan(plan: Sequence[PlannedAct]) -> tuple[PlannedAct, ...]:
    acts = tuple(plan)
    if tuple(a.step_id for a in acts) != STEP_IDS or not all(
        isinstance(a.argv, tuple) and a.argv for a in acts
    ):
        raise ExpectationRefused("plan")
    return acts


def evaluate_act(
    expectations: Expectations,
    plan: Sequence[PlannedAct],
    index: int,
    evidence: ActEvidence | None,
    earlier: Mapping[str, ActEvidence],
) -> Verdict:
    """Judge the act at ``plan[index]``. ``earlier`` holds prior acts' evidence by step
    id; a final-survey act needs its first reading there and re-judges it."""
    acts = _validated_plan(plan)
    if type(index) is not int or not 0 <= index < len(acts):
        raise ExpectationRefused("index")
    planned = acts[index]
    step = planned.step_id
    if evidence is None:
        return Verdict(step, Outcome.UNESTABLISHED, "no-evidence")
    problem = _binding_problem(expectations, planned, index + 1, evidence)
    if problem is not None:
        return Verdict(step, *problem)
    record = evidence.record
    assert record is not None and evidence.stdout is not None and evidence.stderr is not None

    def verdict(outcome: Outcome, reason: str) -> Verdict:
        return Verdict(
            step, outcome, reason, record.capture_seq, evidence.admitted_record_sha256,
            record.stdout.sha256, record.stderr.sha256,
        )

    if record.exit.kind != "status" or record.exit.value != _accepted_status(step):
        return verdict(Outcome.MISMATCH, "exit")
    stdout, stderr = evidence.stdout, evidence.stderr
    try:
        if step in _RUN_ROOT_STEPS:
            # Each reading stands alone: exit 1 by itself never establishes absence.
            _require(stdout == b"", "unexpected-stdout")
            form = expectations.run_root_enoent_stderr
            if form is None:
                return verdict(Outcome.UNESTABLISHED, "no-reviewed-enoent-form")
            shape = _ENOENT_FORM.fullmatch(form)
            assert shape is not None  # enforced when ``expectations`` was constructed
            _require(shape.group(1) == planned.argv[-1].encode(), "enoent-form-names-another-path")
            _require(stderr == form, "not-the-enoent-diagnostic")
        else:
            _require(stderr == b"", "unexpected-stderr")
            if step in _ABSENT_IDENTITY_STEPS:
                _require(stdout == b"", "unexpected-stdout")
            elif step in _RECORDED_MAY_BE_EMPTY:
                if stdout:
                    _lines(stdout)
                return verdict(Outcome.RECORDED, "no-material-expectation")
            elif step in _RECORDED_NONEMPTY:
                _require(any(line.strip() for line in _lines(stdout)), "blank-output")
                return verdict(Outcome.RECORDED, "no-material-expectation")
            else:
                _STDOUT_CHECKS[step](stdout, planned.argv, expectations)
    except _Mismatch as mismatch:
        return verdict(Outcome.MISMATCH, str(mismatch))

    first_step = FINAL_SURVEY_PAIRS.get(step)
    if first_step is not None:
        first = evaluate_act(
            expectations, acts, STEP_IDS.index(first_step), earlier.get(first_step), earlier
        )
        if not first.permits_continuation:
            return verdict(Outcome.UNESTABLISHED, "first-reading-not-established")
        reading = earlier[first_step]
        assert reading.record is not None
        if (reading.record.exit, reading.stdout, reading.stderr) != (record.exit, stdout, stderr):
            return verdict(Outcome.MISMATCH, "final-survey-differs")
    return verdict(Outcome.MATCH, "expected")


def evaluate_pass(
    expectations: Expectations,
    plan: Sequence[PlannedAct],
    evidence: Sequence[ActEvidence],
) -> Evaluation:
    """Judge ``evidence`` in plan order, stopping at the first act that does not permit
    continuation, as the pass itself must. Too little evidence is ``UNESTABLISHED``;
    surplus evidence is refused."""
    acts = _validated_plan(plan)
    supplied = tuple(evidence)
    if len(supplied) > len(acts):
        raise ExpectationRefused("surplus-evidence")
    verdicts: list[Verdict] = []
    earlier: dict[str, ActEvidence] = {}
    for index, planned in enumerate(acts):
        item = supplied[index] if index < len(supplied) else None
        result = evaluate_act(expectations, acts, index, item, earlier)
        verdicts.append(result)
        if not result.permits_continuation:
            break
        assert item is not None
        earlier[planned.step_id] = item
    return Evaluation(tuple(verdicts))


class EvaluationContinuation:
    """``pass_a``'s continuation seam over ``evaluate_act``: one pass, one use.

    Acts are judged strictly in plan order. Evidence of another invocation, pass,
    sequence or planned act is refused. After the first refusal nothing is permitted
    again. The act request is read by attribute, so this module imports nothing from
    the execution tier.
    """

    def __init__(
        self, expectations: Expectations, plan: Sequence[PlannedAct], *, invocation_id: str
    ) -> None:
        self._expectations = expectations
        self._plan = _validated_plan(plan)
        self._invocation_id = require_invocation_id(invocation_id)
        self._earlier: dict[str, ActEvidence] = {}
        self._verdicts: list[Verdict] = []

    @property
    def evaluation(self) -> Evaluation:
        """Every verdict so far; ``established`` only after all planned acts permitted."""
        return Evaluation(tuple(self._verdicts))

    def covers(self, acts) -> bool:
        """The run's acts are exactly the judged plan, and nothing was judged yet."""
        return not self._verdicts and [(a.step_or_case_id, a.argv) for a in acts] == [
            (p.step_id, p.argv) for p in self._plan
        ]

    def permits(self, request, evidence) -> bool:
        index = len(self._verdicts)
        if index >= len(self._plan) or (index and not self._verdicts[-1].permits_continuation):
            return False
        planned = self._plan[index]
        if not (
            isinstance(evidence, AdmittedEvidence)
            and evidence.invocation_id == self._invocation_id
            and evidence.pass_id == self._expectations.pass_id
            and evidence.capture_seq == index + 1
            and (request.step_or_case_id, request.argv) == (planned.step_id, planned.argv)
        ):
            self._verdicts.append(Verdict(planned.step_id, Outcome.MISMATCH, "not-the-current-act"))
            return False
        item = ActEvidence(
            True, evidence.record_sha256, evidence.record, evidence.stdout, evidence.stderr
        )
        verdict = evaluate_act(self._expectations, self._plan, index, item, self._earlier)
        self._verdicts.append(verdict)
        if verdict.permits_continuation and planned.step_id in FINAL_SURVEY_PAIRS.values():
            self._earlier[planned.step_id] = item
        return verdict.permits_continuation


__all__ = [
    "DRY_RUN_FIELDS",
    "DRY_RUN_HEADER",
    "FINAL_SURVEY_PAIRS",
    "SOURCE_PIN_NAMES",
    "STEP_IDS",
    "ActEvidence",
    "Evaluation",
    "EvaluationContinuation",
    "ExpectationRefused",
    "Expectations",
    "Outcome",
    "PlannedAct",
    "Verdict",
    "evaluate_act",
    "evaluate_pass",
]
