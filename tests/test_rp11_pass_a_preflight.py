"""RP-11 Pass A config/authority binding, on synthetic records only.

Pure: no process, host, capture session or ``run_pass_a``. Every record, name,
digest and instant is invented. **None is an approval, grant or attestation.**
"""

from __future__ import annotations

import ast
import dataclasses
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from application.rp11.authority import AUTHORITY_LIMIT, A2Pins
from application.rp11.canonical import canonical_bytes
from tests.test_rp11_pass_a_expectations import DRY_RUN, ENOENT, EXPECTED, run
from tools import rp11_pass_a_preflight as F
from tools.phase_5_0_evidence.capture_contract import sha256_hex
from tools.phase_5_0_evidence.execution import pass_a_plan as P

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "tools/rp11_pass_a_preflight.py"

PLAN = P.build_pass_a_plan()
OWNER, REVIEWER, OPERATOR, ACTOR = "Synthetic Owner", "Synthetic Reviewer", "Synthetic Operator", "Synthetic Actor"
ACTIVATION = "rp11-act-20270101T100000Z-0123abcd"
OTHER_ACTIVATION = "rp11-act-20270101T100000Z-ffffffff"
NOW = datetime(2027, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
WINDOW = {"not_before": "2027-01-01T11:00:00Z", "not_after": "2027-01-01T14:00:00Z"}
A6_RECORD = f"synthetic A-6 stand-in for {'4' * 64}\n".encode()
TOOL, TREE = "5e" * 32, "7e" * 32

PINS = {
    "prompt_sha256": EXPECTED.prompt_sha256,
    "manifest_json_sha256": EXPECTED.manifest_json_sha256,
    "concrete_plan_sha256": EXPECTED.concrete_plan_sha256,
    "reviewed_digest": DRY_RUN["review manifest digest"],
    "capture_tool_sha256": TOOL,
    "sa2_tree_sha256": TREE,
    "plan_identity_sha256": F.snapshot_plan(PLAN).identity,
}


def base_config() -> dict:
    return {
        "schema": "rp11-pass-a/1",
        "activation_id": ACTIVATION,
        "pass_id": P.PASS_ID,
        "capture_root": P.CAPTURE_ROOT_A,
        "host": "oracle-test",
        "operator": OPERATOR,
        "pinned_commit": EXPECTED.pinned_commit,
        "window": dict(WINDOW),
        "bands": ["A0", "A1"],
        "pins": dict(PINS),
        "expectations": {
            **{name: getattr(EXPECTED, name) for name in (
                "nodename", "kernel_release", "machine", "os_pretty_name",
                "var_lib_source", "var_lib_fstype",
            )},
            "source_sha256": dict(EXPECTED.source_sha256),
            "dry_run": dict(DRY_RUN),
            "run_root_enoent_stderr": ENOENT.decode(),
        },
    }


def document(name: str, body: dict) -> bytes:
    tag = F._DOCUMENTS[name][0]
    return f"# Synthetic {name} — not a record\n\n```{tag}\n".encode() + canonical_bytes(body) + b"```\n"


def machine(config: dict, activation: str = ACTIVATION) -> dict:
    return {
        "schema": "rp11-a2/3",
        "activation_id": activation,
        "h1_record_id": "synthetic-h1",
        "h1_record_sha256": "1a" * 32,
        "h2_record_sha256": "2a" * 32,
        "helper": {"image_sha256": ["3a" * 32], "tool_sha256": "4a" * 32},
        "boot_id": "00000000-0000-0000-0000-000000000000",
        "pass_config": config,
        "pass_config_sha256": sha256_hex(canonical_bytes(config)),
        "staged_rule": {"dev": 1, "ino": 2},
        "staged_rule_sha256": "5a" * 32,
        "lease": {
            "start_window_s": 600, "lease_s": 3600, "poll_ms": 500,
            "stop_timeout_s": 120, "backstop_period_s": 60, "bs_runtime_s": 120,
        },
        "authority_limit": AUTHORITY_LIMIT,
    }


def build(**edits):
    """One consistent synthetic record set.

    ``edits[name](body)`` changes a record before it is serialized; every later
    reference and external pin is then recomputed from the changed bytes, so a
    refusal shows that the *value* was refused, not merely a stale digest. A-1 and
    A-2 keep the reviewed (unedited) pins and expected values."""
    edit = lambda name, body: (edits.get(name, lambda _b: None)(body), body)[1]
    reviewed = base_config()
    reviewed_digest = F.expectations_digest(reviewed)
    config = edit("pass_config", base_config())
    raw = {"pass_config": canonical_bytes(config), "a6_record": A6_RECORD}
    raw["machine_a2"] = canonical_bytes(edit("machine_a2", machine(config)))
    sha = lambda name: sha256_hex(raw[name])

    def put(name: str, body: dict) -> None:
        raw[name] = document(name, edit(name, {"schema": F._DOCUMENTS[name][1], **body}))

    put("a1", {
        "outcome": "accept", "reviewer": REVIEWER, "reviewed_utc": "2027-01-01T08:00:00Z",
        "pinned_commit": reviewed["pinned_commit"], "pins": dict(PINS),
        "expectations_sha256": reviewed_digest,
    })
    where = {"host": "oracle-test", "destination": P.SOURCE_CHECKOUT, "pinned_commit": reviewed["pinned_commit"]}
    put("acquisition_auth", {
        "decision": "grant", "granted_by": OWNER, "granted_utc": "2027-01-01T08:10:00Z", "actor": ACTOR, **where,
    })
    put("acquisition_result", {
        "authorization_sha256": sha("acquisition_auth"), "actor": ACTOR,
        "completed_utc": "2027-01-01T08:20:00Z", "checkout_clean": True, "detached": True, **where,
    })
    put("written_a2", {
        "decision": "grant", "granted_by": OWNER, "granted_utc": "2027-01-01T09:00:00Z",
        "pass_id": P.PASS_ID, "activation_id": ACTIVATION, "operator": OPERATOR, "host": "oracle-test",
        "capture_root": P.CAPTURE_ROOT_A, "window": dict(WINDOW),
        "pinned_commit": reviewed["pinned_commit"], "pins": dict(PINS),
        "expectations_sha256": reviewed_digest, "pass_config_sha256": sha("pass_config"),
        "auth_read": {"A0": "grant", "A1": "grant"}, "a1_sha256": sha("a1"),
        "a6_record_sha256": sha("a6_record"), "acquisition_auth_sha256": sha("acquisition_auth"),
        "acquisition_result_sha256": sha("acquisition_result"),
    })
    put("a5", {
        "attestor": OWNER, "attested_utc": "2027-01-01T09:30:00Z", "host": "oracle-test",
        "statement": F.A5_STATEMENT, "written_a2_sha256": sha("written_a2"),
    })
    put("execution_auth", {
        "decision": "grant", "granted_by": OWNER, "granted_utc": "2027-01-01T10:00:00Z",
        "operator": OPERATOR, "pass_id": P.PASS_ID, "activation_id": ACTIVATION, "window": dict(WINDOW),
        "written_a2_sha256": sha("written_a2"), "machine_a2_sha256": sha("machine_a2"),
        "pass_config_sha256": sha("pass_config"), "a5_sha256": sha("a5"),
    })
    trust = F.TrustRoot(
        acceptance_authority=OWNER, independent_reviewer=REVIEWER, operator=OPERATOR,
        activation_id=ACTIVATION, pinned_commit=reviewed["pinned_commit"],
        capture_tool_sha256=TOOL, sa2_tree_sha256=TREE, a6_journal_sha256="4" * 64,
        **{f"{name}_sha256": sha256_hex(data) for name, data in raw.items()},
    )
    return F.Records(**raw), trust


def bind(records, trust, plan=PLAN, now=NOW):
    return F.bind_records(records, trust, plan, now=now)


def refused(reason: str, record: str, records, trust, **kwargs) -> None:
    with pytest.raises(F.PreflightRefused) as caught:
        bind(records, trust, **kwargs)
    assert (caught.value.reason, caught.value.record) == (reason, record)


def replaced(records, trust, name: str, data: bytes):
    """``records`` with one input swapped and its external pin moved to match."""
    return (
        dataclasses.replace(records, **{name: data}),
        dataclasses.replace(trust, **{f"{name}_sha256": sha256_hex(data)}),
    )


def setting(*path, value):
    def apply(body: dict) -> None:
        for key in path[:-1]:
            body = body[key]
        body[path[-1]] = value

    return apply


# --- the agreeing set ------------------------------------------------------------------


def test_a_consistent_set_yields_expectations_the_evaluator_accepts() -> None:
    records, trust = build()
    bound = bind(records, trust)
    assert bound.expectations == EXPECTED
    assert run(expected=bound.expectations).established
    assert [(a.step_id, a.argv) for a in bound.planned_acts] == [(s.step_id, s.argv) for s in PLAN.steps]
    assert bound.pass_config_sha256 == sha256_hex(records.pass_config)
    assert A2Pins.parse(
        records.machine_a2, operand_sha256=bound.machine_a2_sha256, activation_id=ACTIVATION
    ).pass_bytes == records.pass_config


def test_the_result_makes_no_authorization_claim() -> None:
    names = {f.name for f in dataclasses.fields(F.BoundRecords)}
    assert not any(word in name for name in names for word in ("authorized", "permitted", "may_", "start"))


def test_the_held_constants_and_bands_agree_with_the_plan() -> None:
    assert (F.PASS_ID, F.CAPTURE_ROOT, F.SOURCE_CHECKOUT) == (P.PASS_ID, P.CAPTURE_ROOT_A, P.SOURCE_CHECKOUT)
    assert F.EXECUTION_IDENTITY == P.CAPTURE_IDENTITY.name
    assert (len(F.A0_BAND), len(F.A1_BAND)) == (6, 43)
    assert set(F.A0_BAND) | set(F.A1_BAND) == {s.step_id for s in PLAN.steps}


def test_the_config_embeds_no_later_record_digest() -> None:
    records, trust = build()
    for item in dataclasses.fields(records):
        if item.name != "pass_config":
            assert getattr(trust, f"{item.name}_sha256").encode() not in records.pass_config, item.name


# --- external pins, presence, bounds ---------------------------------------------------

INPUTS = tuple(f.name for f in dataclasses.fields(F.Records))


@pytest.mark.parametrize("name", INPUTS)
def test_every_input_is_required_pinned_and_bounded(name: str) -> None:
    records, trust = build()
    for missing in (b"", None, "text"):
        refused("missing", name, dataclasses.replace(records, **{name: missing}), trust)
    refused("digest", name, dataclasses.replace(records, **{name: getattr(records, name) + b"\n"}), trust)
    refused("digest", name, records, dataclasses.replace(trust, **{f"{name}_sha256": "0" * 64}))
    refused("oversized", name, *replaced(records, trust, name, b"x" * 65_537))


def test_one_document_cannot_serve_as_two_records() -> None:
    records, trust = build()
    refused("not-distinct", "records", *replaced(records, trust, "execution_auth", records.written_a2))


def test_no_trust_value_is_optional_or_malformed() -> None:
    _, trust = build()
    for item in dataclasses.fields(F.TrustRoot):
        assert item.default is dataclasses.MISSING and item.default_factory is dataclasses.MISSING
        if item.name.endswith("_sha256") or item.name == "pinned_commit":
            with pytest.raises(F.PreflightRefused):
                dataclasses.replace(trust, **{item.name: "HEAD"})


# --- parser: duplicates, canonical form, blocks ----------------------------------------


def _bad_json(good: bytes) -> list[bytes]:
    body = good[:-1]
    return [
        body,  # no final LF
        good.replace(b'{"', b'{ "', 1),
        body[:-1] + b',"schema":"x"}\n',  # duplicate key
        body[:-1] + b',"z":1.5}\n',
        body[:-1] + b',"z":null}\n',
        body[:-1] + b',"z":NaN}\n',
        b"[" * 2000 + b"]" * 2000 + b"\n",
        b'{"z":' + b"9" * 6000 + b"}\n",
        good + good,
    ]


@pytest.mark.parametrize("case", range(9))
def test_a_pinned_but_non_canonical_config_is_refused(case: int) -> None:
    records, trust = build()
    data = _bad_json(records.pass_config)[case]
    refused("not-canonical", "pass_config", *replaced(records, trust, "pass_config", data))


@pytest.mark.parametrize("name", tuple(F._DOCUMENTS))
def test_each_written_record_holds_exactly_one_canonical_closed_block(name: str) -> None:
    records, trust = build()
    good = getattr(records, name)
    tag = F._DOCUMENTS[name][0].encode()
    head, _, tail = good.partition(b"```" + tag + b"\n")
    line = tail.split(b"\n")[0]
    block = b"```" + tag + b"\n" + line + b"\n```\n"
    for data in (
        head,  # none
        good + block,  # two
        good + b"  ~~~rp11-other\n",  # a second, differently written one
        good.replace(b"```" + tag, b"```rp11-other"),
        good.replace(b"\n", b"\r\n"),
        head + b"```" + tag + b"\n" + line + b"\n",  # unterminated
        head + b"```" + tag + b"\n" + line + b"\n" + line + b"\n```\n",
        b"\xff" + good,
    ):
        refused("block", name, *replaced(records, trust, name, data))
    spaced = head + b"```" + tag + b"\n" + line.replace(b'{"', b'{ "', 1) + b"\n```\n"
    refused("not-canonical", name, *replaced(records, trust, name, spaced))
    duplicated = head + b"```" + tag + b"\n" + line[:-1] + b',"schema":"x"}\n```\n'
    refused("not-canonical", name, *replaced(records, trust, name, duplicated))


@pytest.mark.parametrize("name", ("pass_config", *F._DOCUMENTS))
def test_keys_and_schema_are_closed(name: str) -> None:
    refused("keys", name, *build(**{name: lambda body: body.update(extra="x")}))
    refused("keys", name, *build(**{name: lambda body: body.pop(next(k for k in body if k != "schema"))}))
    refused("schema", name, *build(**{name: setting("schema", value="rp11-other/1")}))


# --- well-formed wrong values, consistently re-pinned ----------------------------------

WRONG = "ab" * 32

CASES = [
    ("pass_config", setting("operator", value="Another Person"), "operator", "pass_config"),
    ("pass_config", setting("activation_id", value=OTHER_ACTIVATION), "activation", "pass_config"),
    ("pass_config", setting("pass_id", value="C-P5.0-R5-OP1-B"), "scope", "pass_config"),
    ("pass_config", setting("capture_root", value=P.CAPTURE_ROOT_B), "scope", "pass_config"),
    ("pass_config", setting("host", value="production"), "scope", "pass_config"),
    ("pass_config", setting("bands", value=["A0"]), "scope", "pass_config"),
    ("pass_config", setting("pinned_commit", value="b" * 40), "commit", "pass_config"),
    ("pass_config", setting("pins", "capture_tool_sha256", value=WRONG), "pins", "pass_config"),
    ("pass_config", setting("pins", "sa2_tree_sha256", value=WRONG), "pins", "pass_config"),
    ("pass_config", setting("pins", "plan_identity_sha256", value=WRONG), "plan", "pass_config"),
    ("pass_config", setting("pins", "reviewed_digest", value=WRONG), "pins", "pass_config"),
    ("pass_config", setting("pins", "prompt_sha256", value=WRONG), "pins", "a1"),
    ("pass_config", setting("expectations", "nodename", value="other"), "expectations", "a1"),
    ("pass_config", setting("expectations", "nodename", value=""), "expectations", "pass_config"),
    ("pass_config", setting("expectations", "source_sha256", "journal.py", value=WRONG), "a6", "pass_config"),
    ("pass_config", setting("expectations", "run_root_enoent_stderr", value="absent"), "enoent-form", "pass_config"),
    ("pass_config", setting("expectations", "run_root_enoent_stderr",
                            value="stat: cannot stat '/elsewhere': No such file or directory\n"),
     "enoent-form", "pass_config"),
    ("a1", setting("outcome", value="reject"), "decision", "a1"),
    ("a1", setting("reviewer", value=OPERATOR), "reviewer", "a1"),
    ("a1", setting("pinned_commit", value="b" * 40), "commit", "a1"),
    ("a1", setting("pins", "plan_identity_sha256", value=WRONG), "pins", "a1"),
    ("a1", setting("expectations_sha256", value=WRONG), "expectations", "a1"),
    ("acquisition_auth", setting("decision", value="refuse"), "decision", "acquisition_auth"),
    ("acquisition_auth", setting("granted_by", value=OPERATOR), "authority", "acquisition_auth"),
    ("acquisition_auth", setting("destination", value="/opt/elsewhere"), "scope", "acquisition_auth"),
    ("acquisition_auth", setting("pinned_commit", value="b" * 40), "commit", "acquisition_auth"),
    ("acquisition_result", setting("actor", value="Another Person"), "authority", "acquisition_result"),
    ("acquisition_result", setting("authorization_sha256", value=WRONG), "chain", "acquisition_result"),
    ("acquisition_result", setting("checkout_clean", value=1), "decision", "acquisition_result"),
    ("acquisition_result", setting("detached", value=False), "decision", "acquisition_result"),
    ("written_a2", setting("decision", value="refuse"), "decision", "written_a2"),
    ("written_a2", setting("granted_by", value=OPERATOR), "authority", "written_a2"),
    ("written_a2", setting("operator", value="Another Person"), "operator", "written_a2"),
    ("written_a2", setting("activation_id", value=OTHER_ACTIVATION), "activation", "written_a2"),
    ("written_a2", setting("capture_root", value=P.CAPTURE_ROOT_B), "scope", "written_a2"),
    ("written_a2", setting("auth_read", "A0", value="refuse"), "auth-read", "written_a2"),
    ("written_a2", setting("auth_read", "A1", value="refuse"), "auth-read", "written_a2"),
    ("written_a2", setting("auth_read", value={"A0": "grant"}), "auth-read", "written_a2"),
    ("written_a2", setting("auth_read", value={"A0": "grant", "A1": "grant", "DB": "grant"}),
     "auth-read", "written_a2"),
    ("written_a2", setting("pinned_commit", value="b" * 40), "commit", "written_a2"),
    ("written_a2", setting("pins", "sa2_tree_sha256", value=WRONG), "pins", "written_a2"),
    ("written_a2", setting("expectations_sha256", value=WRONG), "expectations", "written_a2"),
    ("written_a2", setting("window", "not_after", value="2027-01-02T14:00:00Z"), "window", "written_a2"),
    *(
        ("written_a2", setting(key, value=WRONG), "chain", "written_a2")
        for key in (
            "pass_config_sha256", "a1_sha256", "a6_record_sha256",
            "acquisition_auth_sha256", "acquisition_result_sha256",
        )
    ),
    ("a5", setting("attestor", value=OPERATOR), "authority", "a5"),
    ("a5", setting("statement", value="oracle-test is probably fine."), "decision", "a5"),
    ("a5", setting("written_a2_sha256", value=WRONG), "chain", "a5"),
    ("execution_auth", setting("decision", value="refuse"), "decision", "execution_auth"),
    ("execution_auth", setting("granted_by", value=OPERATOR), "authority", "execution_auth"),
    ("execution_auth", setting("operator", value="Another Person"), "operator", "execution_auth"),
    ("execution_auth", setting("activation_id", value=OTHER_ACTIVATION), "activation", "execution_auth"),
    ("execution_auth", setting("window", "not_before", value="2027-01-01T00:00:00Z"), "window", "execution_auth"),
    *(
        ("execution_auth", setting(key, value=WRONG), "chain", "execution_auth")
        for key in ("written_a2_sha256", "machine_a2_sha256", "pass_config_sha256", "a5_sha256")
    ),
]


@pytest.mark.parametrize(("name", "change", "reason", "record"), CASES)
def test_a_well_formed_wrong_value_is_refused(name, change, reason, record) -> None:
    refused(reason, record, *build(**{name: change}))


@pytest.mark.parametrize(
    ("change", "reason", "record"),
    [
        ({"operator": "Another Person"}, "operator", "pass_config"),
        ({"activation_id": OTHER_ACTIVATION}, "activation", "pass_config"),
        ({"pinned_commit": "b" * 40}, "commit", "pass_config"),
        ({"capture_tool_sha256": WRONG}, "pins", "pass_config"),
        ({"sa2_tree_sha256": WRONG}, "pins", "pass_config"),
        ({"a6_journal_sha256": WRONG}, "a6", "pass_config"),
        ({"independent_reviewer": OWNER}, "reviewer", "trust"),
        ({"independent_reviewer": OPERATOR}, "reviewer", "trust"),
        ({"operator": "capture"}, "operator", "trust"),
        ({"acceptance_authority": "Another Person"}, "authority", "acquisition_auth"),
    ],
)
def test_agreeing_records_cannot_override_the_trust_root(change, reason, record) -> None:
    records, trust = build()
    refused(reason, record, records, dataclasses.replace(trust, **change))


# --- the machine A-2 -------------------------------------------------------------------


@pytest.mark.parametrize(
    "change",
    [
        setting("schema", value="rp11-a2/4"),
        setting("activation_id", value=OTHER_ACTIVATION),
        setting("authority_limit", value="none"),
        lambda body: body.update(written_a2_sha256=WRONG),
        lambda body: body.update(
            pass_config={**body["pass_config"], "operator": "Another Person"},
            pass_config_sha256=sha256_hex(
                canonical_bytes({**body["pass_config"], "operator": "Another Person"})
            ),
        ),
    ],
)
def test_a_differing_machine_a2_is_refused(change) -> None:
    refused("machine-a2", "machine_a2", *build(machine_a2=change))


def test_records_of_two_activations_do_not_mix() -> None:
    records, trust = build()
    other, _ = build(machine_a2=setting("boot_id", value="11111111-1111-1111-1111-111111111111"))
    # A second, valid machine file for the same config is not the one the execution
    # authority named.
    refused("chain", "execution_auth", *replaced(records, trust, "machine_a2", other.machine_a2))
    # An A-5 made for another written A-2, then an A-5 the execution authority did not name.
    later, _ = build(written_a2=setting("granted_utc", value="2027-01-01T09:00:01Z"))
    refused("chain", "a5", *replaced(records, trust, "written_a2", later.written_a2))
    other_a5, _ = build(a5=setting("attested_utc", value="2027-01-01T09:30:01Z"))
    refused("chain", "execution_auth", *replaced(records, trust, "a5", other_a5.a5))


def test_an_a6_record_that_does_not_name_the_classifier_is_refused() -> None:
    records, trust = build()
    refused("a6", "a6_record", *replaced(records, trust, "a6_record", b"another record\n"))


# --- the plan --------------------------------------------------------------------------


def _with_step(index: int, **changes):
    steps = list(PLAN.steps)
    steps[index] = dataclasses.replace(steps[index], **changes)
    return dataclasses.replace(PLAN, steps=tuple(steps))


@pytest.mark.parametrize(
    "plan",
    [
        dataclasses.replace(PLAN, steps=PLAN.steps[:-1]),
        dataclasses.replace(PLAN, steps=PLAN.steps[1:]),
        dataclasses.replace(PLAN, steps=PLAN.steps[:6]),
        dataclasses.replace(PLAN, steps=(PLAN.steps[1], PLAN.steps[0], *PLAN.steps[2:])),
        P.build_pass_a_plan(include_corroboration=True),
        _with_step(0, auth_row="AUTH-DBREAD"),
    ],
    ids=["no-last", "no-first", "a0-only", "reordered", "corroborated", "auth-row"],
)
def test_a_truncated_or_reshaped_plan_is_refused(plan) -> None:
    records, trust = build()
    with pytest.raises(F.PreflightRefused) as caught:
        bind(records, trust, plan=plan)
    assert caught.value.reason == "plan"


@pytest.mark.parametrize(
    "plan",
    [
        _with_step(0, argv=("/usr/bin/true",)),
        _with_step(0, accepted_exits=(0, 1)),
        _with_step(0, environment="plain"),
        _with_step(0, command_class="T-dry"),
        P.build_pass_a_plan(classes=P.BASE_CLASSES),
    ],
    ids=["argv", "exits", "environment", "class", "timeouts"],
)
def test_any_change_to_what_a_child_does_changes_the_plan_identity(plan) -> None:
    assert F.snapshot_plan(plan).identity != PINS["plan_identity_sha256"]
    records, trust = build()
    refused("plan", "pass_config", records, trust, plan=plan)


TRUE_BOUND = PLAN.whole_pass_bound_seconds
#: The first instant at which a duration one second short of the true one still fits.
TOO_LATE = datetime(2027, 1, 1, 14, 0, 0, tzinfo=timezone.utc) - timedelta(seconds=TRUE_BOUND - 1)


def _with_duration(*answers):
    """A ``PassAPlan`` subclass with identical steps and acts whose duration property
    gives ``answers`` in turn, then repeats the last. Returns it and its read log."""
    reads: list[object] = []

    class Restated(P.PassAPlan):
        @property
        def whole_pass_bound_seconds(self):
            reads.append(answers[min(len(reads), len(answers) - 1)])
            return reads[-1]

    return Restated(PLAN.steps, PLAN.classes), reads


@pytest.mark.parametrize(
    "value",
    [0, 0.0, -1.0, 1.0, float("nan"), float("inf"), 1e308, True, None, "2548", TRUE_BOUND + 0.0001],
)
def test_an_invalid_whole_pass_duration_is_refused(value) -> None:
    records, trust = build()
    refused("plan", "duration", records, trust, plan=_with_duration(value)[0])


@pytest.mark.parametrize("value", [TRUE_BOUND - 1, TRUE_BOUND + 1, 10**30])
def test_a_changed_duration_changes_the_plan_identity(value) -> None:
    plan = _with_duration(value)[0]
    assert plan.acts() == PLAN.acts()
    assert F.snapshot_plan(plan).identity != PINS["plan_identity_sha256"]
    records, trust = build()
    refused("plan", "pass_config", records, trust, plan=plan)


def test_a_restated_duration_cannot_buy_a_late_start() -> None:
    records, trust = build()
    refused("window", "now", records, trust, now=TOO_LATE)
    refused("plan", "duration", records, trust, plan=_with_duration(0)[0], now=TOO_LATE)
    refused("plan", "pass_config", records, trust, plan=_with_duration(TRUE_BOUND - 1)[0], now=TOO_LATE)


def test_the_duration_is_read_once_and_the_window_uses_that_reading() -> None:
    records, trust = build()
    plan, reads = _with_duration(TRUE_BOUND, 0)
    refused("window", "now", records, trust, plan=plan, now=TOO_LATE)
    assert reads == [TRUE_BOUND]
    plan, reads = _with_duration(TRUE_BOUND, 0)
    assert bind(records, trust, plan=plan).whole_pass_bound_ms == TRUE_BOUND * 1000
    assert reads == [TRUE_BOUND]


def test_the_result_carries_the_whole_act_policy_immutably() -> None:
    records, trust = build()
    bound = bind(records, trust)
    assert bound.whole_pass_bound_ms == TRUE_BOUND * 1000
    for act, step, request in zip(bound.acts, PLAN.steps, PLAN.acts(), strict=True):
        assert (act.step_id, act.command_class, act.auth_row) == (step.step_id, step.command_class, step.auth_row)
        assert (act.argv, act.accepted_exits) == (step.argv, step.accepted_exits)
        assert dict(act.environment) == dict(request.environment)
        assert act.stream_bound_bytes == request.stream_bound_bytes
        assert (act.timeout_ms, act.drain_ms) == (request.timeout_seconds * 1000, request.drain_seconds * 1000)
        hash(act)  # every field is an immutable value
    with pytest.raises(dataclasses.FrozenInstanceError):
        bound.acts[0].timeout_ms = 1


# --- time ------------------------------------------------------------------------------

START = datetime(2027, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
LAST = datetime(2027, 1, 1, 14, 0, 0, tzinfo=timezone.utc) - timedelta(seconds=PLAN.whole_pass_bound_seconds)


def test_the_window_admits_its_first_instant_and_the_last_that_still_fits_the_bound() -> None:
    records, trust = build()
    assert bind(records, trust, now=START).not_before == START
    bind(records, trust, now=LAST)
    for now in (START - timedelta(microseconds=1), LAST + timedelta(microseconds=1)):
        refused("window", "now", records, trust, now=now)


def test_only_an_aware_utc_instant_is_accepted() -> None:
    records, trust = build()
    for now in (NOW.replace(tzinfo=None), NOW.astimezone(timezone(timedelta(hours=1))), "2027-01-01T12:00:00Z"):
        refused("instant", "now", records, trust, now=now)


@pytest.mark.parametrize(
    ("name", "key", "value", "record"),
    [
        ("acquisition_auth", "granted_utc", "2027-01-01T07:59:59Z", "acquisition_auth"),
        ("acquisition_result", "completed_utc", "2027-01-01T08:09:59Z", "acquisition_result"),
        ("written_a2", "granted_utc", "2027-01-01T08:19:59Z", "written_a2"),
        ("a5", "attested_utc", "2027-01-01T08:59:59Z", "a5"),
        ("execution_auth", "granted_utc", "2027-01-01T09:29:59Z", "execution_auth"),
        ("execution_auth", "granted_utc", "2027-01-01T12:00:01Z", "execution_auth"),
    ],
)
def test_records_out_of_stage_order_or_from_the_future_are_refused(name, key, value, record) -> None:
    refused("order", record, *build(**{name: setting(key, value=value)}))


@pytest.mark.parametrize("value", ["2027-01-01", "2027-02-30T00:00:00Z", "2027-01-01T08:00:00+00:00", 5])
def test_a_malformed_instant_is_refused(value) -> None:
    refused("value", "a1", *build(a1=setting("reviewed_utc", value=value)))


def test_an_empty_or_inverted_window_is_refused() -> None:
    for end in (WINDOW["not_before"], "2027-01-01T10:00:00Z"):
        refused("window", "pass_config", *build(pass_config=setting("window", "not_after", value=end)))


# --- containment -----------------------------------------------------------------------


def test_the_module_is_pure_and_nothing_imports_it() -> None:
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    imported = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    imported |= {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    assert imported == {
        "__future__", "math", "re", "dataclasses", "datetime",
        "application.rp11.authority", "application.rp11.canonical",
        "phase_5_0_evidence.capture_contract", "rp11_pass_a_expectations",
    }
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    attributes = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert not (names | attributes) & {
        "open", "exec", "eval", "__import__", "environ", "run_pass_a", "load_authority",
        "create_capture_session", "StreamCaptureLauncher",
    }
    # The instant is an argument; the module reads no clock.
    assert not attributes & {"now", "utcnow", "today"}
    for relative in ("infra", "tools", "application", "adapters", "domain"):
        for path in (ROOT / relative).rglob("*.py"):
            if path != MODULE and "__pycache__" not in path.parts:
                assert "rp11_pass_a_preflight" not in path.read_text(encoding="utf-8"), path
