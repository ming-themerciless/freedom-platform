"""RP-11 Pass A config/authority binding: do the pinned records describe one same pass?

**Review precursor. Not wired, not covered, not authority.** Nothing operational
imports this module. It is outside the review manifest's covered package and
outside the SA-2 build closure. A successful return means only that the supplied
bytes match the supplied pins and agree with each other at the supplied instant.
**It does not authorize a start**, acquisition or any host act, and it is not
A-1, A-2, A-5 or an AUTH grant.

It is pure: it reads no file, clock, environment or process. Every byte string,
the plan and the instant are arguments.

Plan snapshot
    The plan object is read once, by ``snapshot_plan``, into immutable values: every
    act's policy and the whole-pass duration. The reviewed plan identity, the window
    check and the returned result all come from that one snapshot. **A later wiring
    must build its act requests, exit policy and duration from ``BoundRecords`` and
    must not reuse the caller's plan object or its methods** (``acts``,
    ``exit_policy``, ``whole_pass_bound_seconds``): those are not bound.

What two digests do not say
    * A-6: finding the classifier digest inside the pinned record is a consistency
      check only. That the record's *subject* is that classifier and its
      *disposition* is acceptance is authenticated by external review metadata,
      which whoever builds ``TrustRoot`` vouches for; a record that rejects the
      digest also contains it.
    * ``capture_tool_sha256`` is the capture-tool *source* digest. The machine
      A-2's ``helper.tool_sha256`` is its own, existing artifact field (the
      installed helper tool the holder hashes). Neither stands for the other and
      they are not compared here.

Trust root
    A digest shows identical bytes, never who wrote them. ``TrustRoot`` is where
    authorship enters: whoever builds it vouches that each record digest, name,
    commit and artifact digest in it was obtained from the person entitled to fix
    it, by a channel independent of the records themselves. No value in it may be
    computed from the bytes it is meant to check. This module cannot verify that.
    The machine A-2 additionally keeps its existing trust (root-owned ``0444``
    file selected by operand, chained to H-1), which the consume role checks and
    this module does not replace.

Digest chain (acyclic; no record embeds the digest of a later one)::

    pass-a.json ◀─ machine A-2 (quotes it, schema rp11-a2/3, unchanged)
         ▲
    A-1 ◀─ acquisition authorization ◀─ acquisition result
     ▲                 ▲                        ▲
     └──────────── written A-2 (also pins pass-a.json and A-6)
                       ▲
                      A-5
                       ▲
    execution authorization (pins written A-2, machine A-2, A-5, pass-a.json)

``pass-a.json`` therefore holds no record digest. The machine A-2 is bound to the
written grant by the execution authorization, which names both digests, so the
accepted ``rp11-a2/3`` schema and consume semantics do not change. The machine
file alone grants nothing here: without the written A-2 it is refused.

Record format
    ``pass-a.json`` and the machine A-2 are canonical JSON. A written record is a
    UTF-8, LF-only document holding **exactly one** fenced block whose tag starts
    ``rp11-``; the block is one canonical JSON line. The pin covers the whole
    document, so the structured fields are the signed text, not a transcription.
    Prose is not interpreted: a document that withdraws its own grant in prose is
    not detected (revocation and supersession are A-3, outside this module).
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, fields
from datetime import datetime, timedelta, timezone

from application.rp11.authority import A2Pins, AuthorityError
from application.rp11.canonical import CanonicalError, canonical_bytes, parse_canonical

from .phase_5_0_evidence.capture_contract import sha256_hex
from .rp11_pass_a_expectations import (
    STEP_IDS,
    ExpectationRefused,
    Expectations,
    PlannedAct,
)

#: Held equal to the plan module by a test; this module does not import the plan.
PASS_ID = "C-P5.0-R5-OP1-A"
CAPTURE_ROOT = "/var/lib/fb-rp11/capture-a"
SOURCE_CHECKOUT = "/opt/freedom-blades/rp11-source"
HOST = "oracle-test"
#: The execution identity is never the named operator.
EXECUTION_IDENTITY = "capture"

CONFIG_SCHEMA = "rp11-pass-a/1"
PLAN_IDENTITY_SCHEMA = "rp11-plan-identity/2"

A0_BAND: tuple[str, ...] = ("A0-02a", "A0-02b", "A0-03", "A0-04", "A0-05", "A1-S2")
A1_BAND: tuple[str, ...] = tuple(s for s in STEP_IDS if s not in A0_BAND)
BANDS = ("A0", "A1")

A5_STATEMENT = "oracle-test holds no production data and no production credential."

MAX_CONFIG_BYTES = 65_536
MAX_DOCUMENT_BYTES = 65_536

_HEX64 = re.compile(r"[0-9a-f]{64}")
_COMMIT = re.compile(r"[0-9a-f]{40}")
_NAME = re.compile(r"[A-Za-z][A-Za-z0-9 ._-]{0,63}")
_UTC = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
_FENCE = re.compile(r"\s*(```|~~~)\s*rp11-")

_PIN_KEYS = (
    "prompt_sha256",
    "manifest_json_sha256",
    "concrete_plan_sha256",
    "reviewed_digest",
    "capture_tool_sha256",
    "sa2_tree_sha256",
    "plan_identity_sha256",
)
_HOST_FACTS = (
    "nodename",
    "kernel_release",
    "machine",
    "os_pretty_name",
    "var_lib_source",
    "var_lib_fstype",
)
_EXPECTATION_KEYS = (*_HOST_FACTS, "source_sha256", "dry_run", "run_root_enoent_stderr")
_CONFIG_KEYS = (
    "schema", "activation_id", "pass_id", "capture_root", "host", "operator",
    "pinned_commit", "window", "bands", "pins", "expectations",
)
#: Record name to (fence tag, schema, closed keys).
_DOCUMENTS = {
    "a1": ("rp11-a1", "rp11-a1/1", (
        "schema", "outcome", "reviewer", "reviewed_utc", "pinned_commit", "pins",
        "expectations_sha256",
    )),
    "acquisition_auth": ("rp11-acquire-auth", "rp11-acquire-auth/1", (
        "schema", "decision", "granted_by", "granted_utc", "actor", "host", "destination",
        "pinned_commit",
    )),
    "acquisition_result": ("rp11-acquire-result", "rp11-acquire-result/1", (
        "schema", "authorization_sha256", "actor", "host", "destination", "pinned_commit",
        "completed_utc", "checkout_clean", "detached",
    )),
    "written_a2": ("rp11-written-a2", "rp11-written-a2/1", (
        "schema", "decision", "granted_by", "granted_utc", "pass_id", "activation_id",
        "operator", "host", "capture_root", "window", "pinned_commit", "pins",
        "expectations_sha256", "pass_config_sha256", "auth_read", "a1_sha256",
        "a6_record_sha256", "acquisition_auth_sha256", "acquisition_result_sha256",
    )),
    "a5": ("rp11-a5", "rp11-a5/1", (
        "schema", "attestor", "attested_utc", "host", "statement", "written_a2_sha256",
    )),
    "execution_auth": ("rp11-exec-auth", "rp11-exec-auth/1", (
        "schema", "decision", "granted_by", "granted_utc", "operator", "pass_id",
        "activation_id", "window", "written_a2_sha256", "machine_a2_sha256",
        "pass_config_sha256", "a5_sha256",
    )),
}


class PreflightRefused(ValueError):
    """The records do not bind. ``reason`` is a fixed, content-free code and
    ``record`` names the input it was found in."""

    REASONS = frozenset({
        "trust-root", "instant", "missing", "oversized", "digest", "not-distinct",
        "block", "not-canonical", "keys", "schema", "value", "decision", "authority",
        "operator", "reviewer", "scope", "activation", "commit", "pins", "plan",
        "expectations", "enoent-form", "auth-read", "window", "order", "chain",
        "machine-a2", "a6",
    })

    def __init__(self, reason: str, record: str) -> None:
        if reason not in self.REASONS:
            raise ValueError("unknown preflight refusal")
        self.reason = reason
        self.record = record
        super().__init__(f"{reason}: {record}")


def _require(condition: bool, reason: str, record: str) -> None:
    if not condition:
        raise PreflightRefused(reason, record)


@dataclass(frozen=True, slots=True, kw_only=True)
class Records:
    """The exact bytes of every input. All are required."""

    pass_config: bytes
    machine_a2: bytes
    a1: bytes
    a6_record: bytes
    acquisition_auth: bytes
    acquisition_result: bytes
    written_a2: bytes
    a5: bytes
    execution_auth: bytes


@dataclass(frozen=True, slots=True, kw_only=True)
class TrustRoot:
    """Values fixed outside the records (module docstring). None has a default."""

    acceptance_authority: str
    independent_reviewer: str
    #: Who is actually going to start the pass.
    operator: str
    activation_id: str
    pinned_commit: str
    capture_tool_sha256: str
    sa2_tree_sha256: str
    #: The classifier digest the A-6 record accepted.
    a6_journal_sha256: str
    pass_config_sha256: str
    machine_a2_sha256: str
    a1_sha256: str
    a6_record_sha256: str
    acquisition_auth_sha256: str
    acquisition_result_sha256: str
    written_a2_sha256: str
    a5_sha256: str
    execution_auth_sha256: str

    def __post_init__(self) -> None:
        names = (self.acceptance_authority, self.independent_reviewer, self.operator)
        _require(
            all(type(n) is str and _NAME.fullmatch(n) for n in names), "trust-root", "names"
        )
        _require(type(self.activation_id) is str, "trust-root", "activation_id")
        _require(
            type(self.pinned_commit) is str and _COMMIT.fullmatch(self.pinned_commit) is not None,
            "trust-root", "pinned_commit",
        )
        for item in fields(self):
            if item.name.endswith("_sha256"):
                value = getattr(self, item.name)
                _require(
                    type(value) is str and _HEX64.fullmatch(value) is not None,
                    "trust-root", item.name,
                )


@dataclass(frozen=True, slots=True, kw_only=True)
class BoundAct:
    """The complete policy of one act, as plain immutable values."""

    step_id: str
    command_class: str
    auth_row: str
    argv: tuple[str, ...]
    #: Name and value pairs, sorted by name. The child gets exactly these.
    environment: tuple[tuple[str, str], ...]
    stream_bound_bytes: int
    timeout_ms: int
    drain_ms: int
    accepted_exits: tuple[int, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class PlanSnapshot:
    """One reading of a plan. ``identity`` is the digest of the other two fields
    together with the pass id, capture root and source checkout."""

    identity: str
    acts: tuple[BoundAct, ...]
    whole_pass_bound_ms: int


@dataclass(frozen=True, slots=True)
class BoundRecords:
    """What the agreeing records fix. **Not a start authorization.**"""

    expectations: Expectations
    #: The plan's step ids and argv, as judged by the evaluator.
    planned_acts: tuple[PlannedAct, ...]
    #: The bound act policy and duration. The only ones a later wiring may use.
    acts: tuple[BoundAct, ...]
    whole_pass_bound_ms: int
    activation_id: str
    operator: str
    pinned_commit: str
    not_before: datetime
    not_after: datetime
    pass_config_sha256: str
    expectations_sha256: str
    plan_identity_sha256: str
    machine_a2_sha256: str
    written_a2_sha256: str
    execution_auth_sha256: str


# --- plan snapshot ---------------------------------------------------------------------


def _milliseconds(seconds: object) -> int:
    """A positive, finite, whole number of milliseconds, or a refusal."""
    _require(type(seconds) in (int, float), "plan", "duration")
    value = seconds * 1000
    _require(
        (type(value) is int or math.isfinite(value)) and value > 0 and value == int(value),
        "plan", "duration",
    )
    return int(value)


def _strings(values) -> tuple[str, ...]:
    items = tuple(values)
    _require(all(type(v) is str for v in items), "plan", "acts")
    return items


def _bound_act(step, request) -> BoundAct:
    step_id, command_class, auth_row = _strings(
        (step.step_id, step.command_class, step.auth_row)
    )
    argv = _strings(step.argv)
    _require(
        (request.step_or_case_id, _strings(request.argv)) == (step_id, argv), "plan", "acts"
    )
    exits = tuple(step.accepted_exits)
    stream_bound = request.stream_bound_bytes
    _require(
        all(type(c) is int for c in exits) and type(stream_bound) is int, "plan", "acts"
    )
    environment = dict(request.environment)
    names = sorted(_strings(environment))
    _strings(environment.values())
    return BoundAct(
        step_id=step_id,
        command_class=command_class,
        auth_row=auth_row,
        argv=argv,
        environment=tuple((name, environment[name]) for name in names),
        stream_bound_bytes=stream_bound,
        timeout_ms=_milliseconds(request.timeout_seconds),
        drain_ms=_milliseconds(request.drain_seconds),
        accepted_exits=exits,
    )


def snapshot_plan(plan) -> PlanSnapshot:
    """Read ``plan`` once: everything it makes a child do, and its whole-pass duration.

    ``plan`` is a ``PassAPlan``. Only the exact default step sequence is accepted, so
    a truncated, reordered or extended plan is refused before any digest compare. The
    caller's type is not trusted: whatever it answers here is what is digested."""
    steps = tuple(plan.steps)
    requests = tuple(plan.acts())
    _require(len(steps) == len(requests) == len(STEP_IDS), "plan", "steps")
    acts = tuple(_bound_act(step, request) for step, request in zip(steps, requests))
    _require(tuple(a.step_id for a in acts) == STEP_IDS, "plan", "steps")
    _require(all(a.auth_row == "AUTH-READ" for a in acts), "plan", "auth_row")
    whole = _milliseconds(plan.whole_pass_bound_seconds)
    # No stated duration may be shorter than the deadlines it has to contain.
    _require(whole >= sum(a.timeout_ms + a.drain_ms for a in acts), "plan", "duration")
    document = {
        "schema": PLAN_IDENTITY_SCHEMA,
        "pass_id": PASS_ID,
        "capture_root": CAPTURE_ROOT,
        "source_checkout": SOURCE_CHECKOUT,
        "whole_pass_bound_ms": whole,
        "acts": [
            {
                "step_id": a.step_id,
                "command_class": a.command_class,
                "auth_row": a.auth_row,
                "accepted_exits": list(a.accepted_exits),
                "argv": list(a.argv),
                "environment": dict(a.environment),
                "stream_bound_bytes": a.stream_bound_bytes,
                "timeout_ms": a.timeout_ms,
                "drain_ms": a.drain_ms,
            }
            for a in acts
        ],
    }
    return PlanSnapshot(
        identity=sha256_hex(canonical_bytes(document)), acts=acts, whole_pass_bound_ms=whole
    )


# --- expectations ----------------------------------------------------------------------


def expectations_digest(config: dict) -> str:
    """The digest of every value the evaluator will compare, taken from a pass config.

    It is independent of activation, operator and window, so A-1 can accept it before
    those are chosen."""
    pins = config["pins"]
    return sha256_hex(canonical_bytes({
        "pass_id": config["pass_id"],
        "pinned_commit": config["pinned_commit"],
        "prompt_sha256": pins["prompt_sha256"],
        "manifest_json_sha256": pins["manifest_json_sha256"],
        "concrete_plan_sha256": pins["concrete_plan_sha256"],
        **config["expectations"],
    }))


def _expectations(config: dict, acts: tuple[PlannedAct, ...]) -> Expectations:
    values = config["expectations"]
    pins = config["pins"]
    form = values["run_root_enoent_stderr"]
    # "absent" is canonical JSON's missing value. A pass without a reviewed form is
    # certain to stop at A1-19 and consume its capture root, so it is refused here.
    _require(type(form) is str and form != "absent" and form.isascii(), "enoent-form", "pass_config")
    try:
        expected = Expectations(
            pass_id=config["pass_id"],
            pinned_commit=config["pinned_commit"],
            prompt_sha256=pins["prompt_sha256"],
            manifest_json_sha256=pins["manifest_json_sha256"],
            concrete_plan_sha256=pins["concrete_plan_sha256"],
            source_sha256=values["source_sha256"],
            dry_run=values["dry_run"],
            run_root_enoent_stderr=form.encode("ascii"),
            **{name: values[name] for name in _HOST_FACTS},
        )
    except ExpectationRefused:
        raise PreflightRefused("expectations", "pass_config") from None
    run_root = next(a.argv[-1] for a in acts if a.step_id == "A1-19")
    _require(f"'{run_root}'" in form, "enoent-form", "pass_config")
    _require(expected.dry_run["review manifest digest"] == pins["reviewed_digest"], "pins", "pass_config")
    return expected


# --- parsing ---------------------------------------------------------------------------


def _closed(document: object, keys: tuple[str, ...], record: str) -> dict:
    _require(type(document) is dict and set(document) == set(keys), "keys", record)
    return document


def _canonical(data: bytes, record: str) -> object:
    try:
        return parse_canonical(data)
    except CanonicalError:
        raise PreflightRefused("not-canonical", record) from None


def _block(data: bytes, record: str) -> dict:
    tag, schema, keys = _DOCUMENTS[record]
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise PreflightRefused("block", record) from None
    _require("\r" not in text and "\0" not in text, "block", record)
    lines = text.split("\n")
    openings = [i for i, line in enumerate(lines) if _FENCE.match(line)]
    _require(len(openings) == 1, "block", record)
    start = openings[0]
    _require(
        lines[start] == f"```{tag}" and start + 2 < len(lines) and lines[start + 2] == "```",
        "block", record,
    )
    line = lines[start + 1]
    _require(line.isascii(), "not-canonical", record)
    document = _closed(_canonical(line.encode("ascii") + b"\n", record), keys, record)
    _require(document["schema"] == schema, "schema", record)
    return document


def _instant(value: object, record: str) -> datetime:
    _require(type(value) is str and _UTC.fullmatch(value) is not None, "value", record)
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        raise PreflightRefused("value", record) from None


def _name(value: object, record: str) -> str:
    _require(type(value) is str and _NAME.fullmatch(value) is not None, "value", record)
    return value


def _window(value: object, record: str) -> tuple[datetime, datetime]:
    window = _closed(value, ("not_before", "not_after"), record)
    not_before = _instant(window["not_before"], record)
    not_after = _instant(window["not_after"], record)
    _require(not_before < not_after, "window", record)
    return not_before, not_after


def _pins(value: object, record: str) -> dict:
    pins = _closed(value, _PIN_KEYS, record)
    _require(
        all(type(v) is str and _HEX64.fullmatch(v) is not None for v in pins.values()),
        "value", record,
    )
    return pins


def _verified(records: Records, trust: TrustRoot) -> None:
    """Every input present, bounded, distinct and equal to its external pin."""
    digests: list[str] = []
    for item in fields(records):
        name = item.name
        data = getattr(records, name)
        _require(type(data) is bytes and len(data) > 0, "missing", name)
        limit = MAX_CONFIG_BYTES if name == "pass_config" else MAX_DOCUMENT_BYTES
        _require(len(data) <= limit, "oversized", name)
        digest = sha256_hex(data)
        _require(digest == getattr(trust, f"{name}_sha256"), "digest", name)
        digests.append(digest)
    _require(len(set(digests)) == len(digests), "not-distinct", "records")


def _config(data: bytes, trust: TrustRoot) -> dict:
    record = "pass_config"
    config = _closed(_canonical(data, record), _CONFIG_KEYS, record)
    _require(config["schema"] == CONFIG_SCHEMA, "schema", record)
    _require(config["pass_id"] == PASS_ID, "scope", record)
    _require(config["capture_root"] == CAPTURE_ROOT, "scope", record)
    _require(config["host"] == HOST, "scope", record)
    _require(config["bands"] == list(BANDS), "scope", record)
    _require(config["activation_id"] == trust.activation_id, "activation", record)
    _require(config["operator"] == trust.operator, "operator", record)
    _require(config["pinned_commit"] == trust.pinned_commit, "commit", record)
    pins = _pins(config["pins"], record)
    _require(pins["capture_tool_sha256"] == trust.capture_tool_sha256, "pins", record)
    _require(pins["sa2_tree_sha256"] == trust.sa2_tree_sha256, "pins", record)
    _closed(config["expectations"], _EXPECTATION_KEYS, record)
    _window(config["window"], record)
    return config


def _machine_a2(records: Records, trust: TrustRoot) -> None:
    """The existing ``rp11-a2/3`` parser, then equality with the pinned config bytes."""
    try:
        pins = A2Pins.parse(
            records.machine_a2,
            operand_sha256=trust.machine_a2_sha256,
            activation_id=trust.activation_id,
        )
    except (AuthorityError, CanonicalError):
        raise PreflightRefused("machine-a2", "machine_a2") from None
    _require(
        pins.pass_config_sha256 == trust.pass_config_sha256
        and pins.pass_bytes == records.pass_config,
        "machine-a2", "machine_a2",
    )


def bind_records(records: Records, trust: TrustRoot, plan, *, now: datetime) -> BoundRecords:
    """Return what the records jointly fix, or raise ``PreflightRefused``.

    ``now`` must be an aware UTC instant. The window admits it only if the snapshot's
    whole-pass duration also ends inside the window. ``plan`` is read once and must
    not be used again (module docstring)."""
    _require(type(records) is Records, "missing", "records")
    _require(type(trust) is TrustRoot, "trust-root", "trust")
    _require(
        isinstance(now, datetime) and now.utcoffset() == timedelta(0), "instant", "now"
    )
    owner, reviewer, operator = (
        trust.acceptance_authority, trust.independent_reviewer, trust.operator
    )
    _require(reviewer not in (owner, operator), "reviewer", "trust")
    _require(operator != EXECUTION_IDENTITY, "operator", "trust")
    _verified(records, trust)

    config = _config(records.pass_config, trust)
    _machine_a2(records, trust)
    snapshot = snapshot_plan(plan)
    identity = snapshot.identity
    _require(config["pins"]["plan_identity_sha256"] == identity, "plan", "pass_config")
    acts = tuple(PlannedAct(a.step_id, a.argv) for a in snapshot.acts)
    expected = _expectations(config, acts)
    expected_digest = expectations_digest(config)
    journal = trust.a6_journal_sha256
    _require(expected.source_sha256["journal.py"] == journal, "a6", "pass_config")
    _require(journal.encode("ascii") in records.a6_record, "a6", "a6_record")

    docs = {name: _block(getattr(records, name), name) for name in _DOCUMENTS}
    a1, grant, result = docs["a1"], docs["acquisition_auth"], docs["acquisition_result"]
    a2, a5, execution = docs["written_a2"], docs["a5"], docs["execution_auth"]

    # A-1: independent acceptance of the commit, pins, plan and expected values.
    _require(a1["outcome"] == "accept", "decision", "a1")
    _require(a1["reviewer"] == reviewer, "reviewer", "a1")
    _require(a1["pinned_commit"] == trust.pinned_commit, "commit", "a1")
    _require(_pins(a1["pins"], "a1") == config["pins"], "pins", "a1")
    _require(a1["expectations_sha256"] == expected_digest, "expectations", "a1")

    # Acquisition: its own authority and its own result; neither grants execution.
    _require(grant["decision"] == "grant", "decision", "acquisition_auth")
    _require(grant["granted_by"] == owner, "authority", "acquisition_auth")
    actor = _name(grant["actor"], "acquisition_auth")
    for name, doc in (("acquisition_auth", grant), ("acquisition_result", result)):
        _require(doc["host"] == HOST and doc["destination"] == SOURCE_CHECKOUT, "scope", name)
        _require(doc["pinned_commit"] == trust.pinned_commit, "commit", name)
    _require(result["actor"] == actor, "authority", "acquisition_result")
    _require(
        result["authorization_sha256"] == trust.acquisition_auth_sha256,
        "chain", "acquisition_result",
    )
    _require(
        result["checkout_clean"] is True and result["detached"] is True,
        "decision", "acquisition_result",
    )

    # Written A-2: the grant, for exactly this config.
    _require(a2["decision"] == "grant", "decision", "written_a2")
    _require(a2["granted_by"] == owner, "authority", "written_a2")
    _require(a2["operator"] == operator, "operator", "written_a2")
    _require(a2["activation_id"] == trust.activation_id, "activation", "written_a2")
    for key in ("pass_id", "host", "capture_root"):
        _require(a2[key] == config[key], "scope", "written_a2")
    _require(
        a2["auth_read"] == {band: "grant" for band in BANDS}, "auth-read", "written_a2"
    )
    _require(a2["pinned_commit"] == trust.pinned_commit, "commit", "written_a2")
    _require(_pins(a2["pins"], "written_a2") == config["pins"], "pins", "written_a2")
    _require(a2["expectations_sha256"] == expected_digest, "expectations", "written_a2")
    _require(a2["window"] == config["window"], "window", "written_a2")
    for key in (
        "pass_config_sha256", "a1_sha256", "a6_record_sha256",
        "acquisition_auth_sha256", "acquisition_result_sha256",
    ):
        _require(a2[key] == getattr(trust, key), "chain", "written_a2")

    # A-5: the attestation, for this A-2.
    _require(a5["attestor"] == owner, "authority", "a5")
    _require(a5["host"] == HOST, "scope", "a5")
    _require(a5["statement"] == A5_STATEMENT, "decision", "a5")
    _require(a5["written_a2_sha256"] == trust.written_a2_sha256, "chain", "a5")

    # Execution authority: separate decision; binds the machine file to the grant.
    _require(execution["decision"] == "grant", "decision", "execution_auth")
    _require(execution["granted_by"] == owner, "authority", "execution_auth")
    _require(execution["operator"] == operator, "operator", "execution_auth")
    _require(execution["activation_id"] == trust.activation_id, "activation", "execution_auth")
    _require(execution["pass_id"] == PASS_ID, "scope", "execution_auth")
    _require(execution["window"] == config["window"], "window", "execution_auth")
    for key in ("written_a2_sha256", "machine_a2_sha256", "pass_config_sha256", "a5_sha256"):
        _require(execution[key] == getattr(trust, key), "chain", "execution_auth")

    # Time. Record order follows the candidate's stages; none may be in the future.
    ordered = (
        ("a1", a1["reviewed_utc"]),
        ("acquisition_auth", grant["granted_utc"]),
        ("acquisition_result", result["completed_utc"]),
        ("written_a2", a2["granted_utc"]),
        ("a5", a5["attested_utc"]),
        ("execution_auth", execution["granted_utc"]),
    )
    previous = None
    for name, value in ordered:
        instant = _instant(value, name)
        _require((previous is None or previous <= instant) and instant <= now, "order", name)
        previous = instant
    not_before, not_after = _window(config["window"], "pass_config")
    # Integer microseconds: exact at the edge, and no duration can overflow.
    remaining_us = (not_after - now) // timedelta(microseconds=1)
    _require(
        not_before <= now and snapshot.whole_pass_bound_ms * 1000 <= remaining_us,
        "window", "now",
    )

    return BoundRecords(
        expectations=expected,
        planned_acts=acts,
        acts=snapshot.acts,
        whole_pass_bound_ms=snapshot.whole_pass_bound_ms,
        activation_id=trust.activation_id,
        operator=operator,
        pinned_commit=trust.pinned_commit,
        not_before=not_before,
        not_after=not_after,
        pass_config_sha256=trust.pass_config_sha256,
        expectations_sha256=expected_digest,
        plan_identity_sha256=identity,
        machine_a2_sha256=trust.machine_a2_sha256,
        written_a2_sha256=trust.written_a2_sha256,
        execution_auth_sha256=trust.execution_auth_sha256,
    )


__all__ = [
    "A0_BAND",
    "A1_BAND",
    "A5_STATEMENT",
    "BoundAct",
    "BoundRecords",
    "PlanSnapshot",
    "PreflightRefused",
    "Records",
    "TrustRoot",
    "bind_records",
    "expectations_digest",
    "snapshot_plan",
]
