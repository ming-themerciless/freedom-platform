"""C-P5.0-R5-R1, part A — the journal classifier against §2.13.5b and §2.13.6.

The P5.0-R5 reconciliation (handback §3.13) found four contradictions between
`journal.py` and the controlling design, and found that the tests passed *with*
them because they encoded the harness's own table. So the oracle here is
**transcribed from the package plan**, row by row, and never read off
`journal.FAULT_REFUSALS`:

* the step and writer code come from §2.13.5b's V-W table (W1 … W16);
* the coordinator code is C-a's *"matching `J-xx` row"* (§2.13.5b), except a
  torn tail, which J-02's C column and C-e count as one unresolved entry — `J-20`;
* where a V-W step names several codes (W7, W14), §2.13.6's rows decide which:
  J-03 (`open` → `ENOENT`), J-11 (replaced inode), J-12 (`EACCES`/`EIO`); and
  J-07, J-08, J-09, J-10, J-18, J-21 for the chain.

Against the pre-remediation module every one of the four contradictions fails
here: a replaced inode was `SW-J04`, cross-generation was `SW-J09`, a missing
`current` was `SW-J17` with coordinator `J-16`, and a stale deployment beside a
broken chain was `CORRUPT`.
"""
from __future__ import annotations

import dataclasses

import pytest

from tools.phase_5_0_evidence import journal
from tools.phase_5_0_evidence.journal import (
    ArtifactRead,
    ChainRecord,
    FlagRead,
    JournalFault,
    JournalObservation,
    N5_0_21_FREE_BYTES,
    SealBody,
    classify_generation_state,
    modelled_fault_coverage,
    validate_generation,
)
from tools.phase_5_0_evidence.errors import ObservationRefused
from tools.phase_5_0_evidence.records import Status

SEAL = SealBody(
    generation_id="000001",
    binding_format_version=1,
    seal_body_digest="sbd",
    genesis_record_digest="genesis",
    journal_device=66,
    journal_inode=1234,
    journal_uid=990,
    journal_gid=991,
    journal_mode=0o640,
    host_machine_id="mid",
    writer_deployment_digest="dep",
    probe_report_digest="probe",
    source_manifest_digest="sm",
    predecessor_close_digest=None,
)


def record(seq: int, *, prev: str, kind: str = "dispatch", **overrides) -> ChainRecord:
    base = dict(
        format_known=True,
        generation_id="000001",
        seq=seq,
        prev_hash=prev,
        record_hash=f"h{seq}",
        hash_verifies=True,
        at=1_000 + seq,
        kind=kind,
    )
    base.update(overrides)
    return ChainRecord(**base)


GENESIS = record(0, prev="sbd", kind="genesis")
STARTUP = record(1, prev="h0", kind="startup")
DISPATCH = record(2, prev="h1")
OUTCOME = record(3, prev="h2", kind="outcome")
CHAIN = (GENESIS, STARTUP, DISPATCH, OUTCOME)


def healthy(**overrides) -> JournalObservation:
    base = dict(
        current_target="000001.journal",
        seal_read=ArtifactRead.OK,
        seal_format_supported=True,
        binding_length_exact=True,
        probe_report_digest="probe",
        probe_report_admissible=True,
        derived_genesis_digest="genesis",
        seal_immutable=FlagRead.PRESENT,
        journal_read=ArtifactRead.OK,
        journal_device=66,
        journal_inode=1234,
        journal_uid=990,
        journal_gid=991,
        journal_mode=0o640,
        append_flag=FlagRead.PRESENT,
        machine_id="mid",
        deployment_digest="dep",
        deployed_source_manifest_digest="sm",
        provenance_valid=True,
        filesystem_read_only=False,
        free_bytes=N5_0_21_FREE_BYTES,
        record_zero_digest="genesis",
        records=CHAIN,
        torn_tail=False,
    )
    base.update(overrides)
    return JournalObservation(**base)


def chain_with(index: int, **overrides) -> tuple[ChainRecord, ...]:
    records = list(CHAIN)
    records[index] = dataclasses.replace(records[index], **overrides)
    return tuple(records)


# ---------------------------------------------------------------------------
# The oracle: (case, overrides, V-W step, writer code, coordinator code), each
# row transcribed from the package plan and cited.
# ---------------------------------------------------------------------------

ORACLE = [
    # W1 / J-03: "a `current` symlink that does not resolve to a well-formed name".
    ("current-absent", {"current_target": None}, "W1", "SW-J03", "J-03"),
    ("current-malformed", {"current_target": "../x.journal"}, "W1", "SW-J03", "J-03"),
    # W2 / J-17: the seal missing or unreadable. W2's refusal column is SW-J17.
    ("seal-missing", {"seal_read": ArtifactRead.ENOENT}, "W2", "SW-J17", "J-17"),
    ("seal-eacces", {"seal_read": ArtifactRead.EACCES}, "W2", "SW-J17", "J-17"),
    ("seal-eio", {"seal_read": ArtifactRead.EIO}, "W2", "SW-J17", "J-17"),
    # W3 / J-24: unknown format, short binding or a trailing byte (F-12).
    ("seal-format", {"seal_format_supported": False}, "W3", "SW-J24", "J-24"),
    ("binding-trailing-byte", {"binding_length_exact": False}, "W3", "SW-J24", "J-24"),
    # W4 / J-25: probe report altered or not a pass (F-8).
    ("probe-digest", {"probe_report_digest": "other"}, "W4", "SW-J25", "J-25"),
    ("probe-not-a-pass", {"probe_report_admissible": False}, "W4", "SW-J25", "J-25"),
    # W5 / J-24: derived genesis != BND.genesis_record_digest (F-1a, F-9).
    ("genesis-derivation", {"derived_genesis_digest": "other", "record_zero_digest": "other"},
     "W5", "SW-J24", "J-24"),
    # W6 / J-17: the seal is mutable.
    ("seal-mutable", {"seal_immutable": FlagRead.ABSENT}, "W6", "SW-J17", "J-17"),
    ("seal-flags-unsupported", {"seal_immutable": FlagRead.UNSUPPORTED}, "W6", "SW-J17", "J-17"),
    # W7 / J-03: the journal file is missing (open -> ENOENT).
    ("journal-missing", {"journal_read": ArtifactRead.ENOENT, "journal_device": None,
                         "journal_inode": None}, "W7", "SW-J03", "J-03"),
    # W7 / J-12: unreadable file.
    ("journal-eacces", {"journal_read": ArtifactRead.EACCES, "journal_device": None,
                        "journal_inode": None}, "W7", "SW-J12", "J-12"),
    ("journal-eio", {"journal_read": ArtifactRead.EIO, "journal_device": None,
                     "journal_inode": None}, "W7", "SW-J12", "J-12"),
    # W7 / J-11: replaced inode (F-5, F-10, F-11). This is contradiction C-1.
    ("inode-replaced", {"journal_inode": 9999}, "W7", "SW-J11", "J-11"),
    ("device-replaced", {"journal_device": 67}, "W7", "SW-J11", "J-11"),
    # W8 / J-05: owner, group or mode.
    ("mode", {"journal_mode": 0o660}, "W8", "SW-J05", "J-05"),
    ("owner", {"journal_uid": 0}, "W8", "SW-J05", "J-05"),
    ("group", {"journal_gid": 0}, "W8", "SW-J05", "J-05"),
    # W9 / J-06: +a absent, or ENOTTY/EOPNOTSUPP.
    ("append-absent", {"append_flag": FlagRead.ABSENT}, "W9", "SW-J06", "J-06"),
    ("append-unsupported", {"append_flag": FlagRead.UNSUPPORTED}, "W9", "SW-J06", "J-06"),
    # W10 / J-23: unforged host change (F-7 a).
    ("host", {"machine_id": "other"}, "W10", "SW-J23", "J-23"),
    # W11 / J-22: stale deployment (F-6).
    ("deployment-stale", {"deployment_digest": "other"}, "W11", "SW-J22", "J-22"),
    # W11a / J-27 then J-26.
    ("source-manifest", {"deployed_source_manifest_digest": "other"}, "W11a", "SW-J27", "J-27"),
    ("provenance", {"provenance_valid": False}, "W11a", "SW-J26", "J-26"),
    # W12 / J-13.
    ("free-space", {"free_bytes": N5_0_21_FREE_BYTES - 1}, "W12", "SW-J13", "J-13"),
    ("read-only", {"filesystem_read_only": True}, "W12", "SW-J13", "J-13"),
    # W13 / J-04: empty, or record 0 not the derived genesis (F-2).
    ("empty", {"records": (), "record_zero_digest": None}, "W13", "SW-J04", "J-04"),
    ("genesis-record", {"record_zero_digest": "other"}, "W13", "SW-J04", "J-04"),
    # W14: each chain defect under its own row.
    ("malformed", {"records": chain_with(2, format_known=False)}, "W14", "SW-J07", "J-07"),
    ("cross-generation", {"records": chain_with(2, generation_id="000002")},
     "W14", "SW-J18", "J-18"),  # contradiction C-2
    ("duplicate-seq", {"records": chain_with(2, seq=1)}, "W14", "SW-J10", "J-10"),
    ("sequence-gap", {"records": chain_with(3, seq=5)}, "W14", "SW-J08", "J-08"),
    ("prev-hash", {"records": chain_with(2, prev_hash="h0")}, "W14", "SW-J09", "J-09"),
    ("record-hash", {"records": chain_with(2, hash_verifies=False)}, "W14", "SW-J09", "J-09"),
    ("timestamp", {"records": chain_with(3, at=0)}, "W14", "SW-J21", "J-21"),
    # W15 / J-02: torn tail; the coordinator counts it as unresolved (J-20).
    ("torn-tail", {"torn_tail": True}, "W15", "SW-J02", "J-20"),
    # W16 / J-19.
    ("sealed", {"records": chain_with(3, kind="seal")}, "W16", "SW-J19", "J-19"),
]


@pytest.mark.parametrize(
    "overrides, step, writer, coordinator",
    [row[1:] for row in ORACLE],
    ids=[row[0] for row in ORACLE],
)
def test_each_fault_refuses_at_its_step_with_its_own_codes(overrides, step, writer, coordinator) -> None:
    verdict = validate_generation(SEAL, healthy(**overrides))
    assert verdict.step is not None and verdict.step.value == step
    assert verdict.writer_refusal == writer
    assert verdict.coordinator_refusal == coordinator
    assert verdict.coordinator_records_clear_evidence is False


#: The fault each case must be diagnosed as, and its §2.13.6 row, stated here so
#: that two causes sharing a step and both codes (a missing and an unreadable
#: seal) cannot be exchanged unnoticed. The row equals the coordinator code except
#: for the torn tail, whose condition is J-02.
CAUSES = {
    "current-absent": ("CURRENT_UNRESOLVED", "J-03"),
    "current-malformed": ("CURRENT_UNRESOLVED", "J-03"),
    "seal-missing": ("SEAL_MISSING", "J-17"),
    "seal-eacces": ("SEAL_UNREADABLE", "J-17"),
    "seal-eio": ("SEAL_UNREADABLE", "J-17"),
    "seal-format": ("SEAL_STRUCTURE", "J-24"),
    "binding-trailing-byte": ("SEAL_STRUCTURE", "J-24"),
    "probe-digest": ("PROBE_REPORT", "J-25"),
    "probe-not-a-pass": ("PROBE_REPORT", "J-25"),
    "genesis-derivation": ("GENESIS_DERIVATION", "J-24"),
    "seal-mutable": ("SEAL_MUTABLE", "J-17"),
    "seal-flags-unsupported": ("SEAL_MUTABLE", "J-17"),
    "journal-missing": ("JOURNAL_MISSING", "J-03"),
    "journal-eacces": ("JOURNAL_UNREADABLE", "J-12"),
    "journal-eio": ("JOURNAL_UNREADABLE", "J-12"),
    "inode-replaced": ("INODE_REPLACED", "J-11"),
    "device-replaced": ("INODE_REPLACED", "J-11"),
    "mode": ("OWNER_OR_MODE", "J-05"),
    "owner": ("OWNER_OR_MODE", "J-05"),
    "group": ("OWNER_OR_MODE", "J-05"),
    "append-absent": ("APPEND_FLAG_ABSENT", "J-06"),
    "append-unsupported": ("APPEND_FLAG_ABSENT", "J-06"),
    "host": ("HOST_MISMATCH", "J-23"),
    "deployment-stale": ("DEPLOYMENT_STALE", "J-22"),
    "source-manifest": ("SOURCE_MANIFEST_MISMATCH", "J-27"),
    "provenance": ("PROVENANCE_INVALID", "J-26"),
    "free-space": ("FILESYSTEM_FULL_OR_READ_ONLY", "J-13"),
    "read-only": ("FILESYSTEM_FULL_OR_READ_ONLY", "J-13"),
    "empty": ("EMPTY_JOURNAL", "J-04"),
    "genesis-record": ("GENESIS_RECORD_MISMATCH", "J-04"),
    "malformed": ("MALFORMED_RECORD", "J-07"),
    "cross-generation": ("CROSS_GENERATION", "J-18"),
    "duplicate-seq": ("DUPLICATE_SEQUENCE", "J-10"),
    "sequence-gap": ("SEQUENCE_GAP", "J-08"),
    "prev-hash": ("CHAIN_BROKEN", "J-09"),
    "record-hash": ("CHAIN_BROKEN", "J-09"),
    "timestamp": ("NON_MONOTONIC_TIME", "J-21"),
    "torn-tail": ("TORN_TAIL", "J-02"),
    "sealed": ("GENERATION_SEALED", "J-19"),
}


@pytest.mark.parametrize("case", [row[0] for row in ORACLE])
def test_each_fault_is_diagnosed_as_its_own_cause_under_its_own_row(case) -> None:
    overrides = next(row[1] for row in ORACLE if row[0] == case)
    name, design_row = CAUSES[case]
    assert validate_generation(SEAL, healthy(**overrides)).fault is JournalFault[name]
    assert journal.FAULT_REFUSALS[JournalFault[name]].row == design_row


def test_the_oracle_exercises_every_modelled_fault() -> None:
    """Every `JournalFault` has an independently stated expectation above."""
    assert set(CAUSES) == {row[0] for row in ORACLE}
    assert {name for name, _ in CAUSES.values()} == {fault.name for fault in JournalFault}


def test_the_free_space_floor_is_n5_0_21() -> None:
    """N5.0-21 is 1 GiB (§8.3), stated here rather than read from the module."""
    assert validate_generation(SEAL, healthy(free_bytes=1_073_741_824)).fault is None
    refused = validate_generation(SEAL, healthy(free_bytes=1_073_741_823))
    assert refused.writer_refusal == "SW-J13"


def test_the_healthy_generation_passes_v_w_and_is_still_not_clear_evidence() -> None:
    verdict = validate_generation(SEAL, healthy())
    assert verdict.fault is None and verdict.writer_refusal is None
    assert verdict.coordinator_refusal is None
    # C-b ... C-f need PostgreSQL; "C-a would not refuse" is not clear evidence.
    assert verdict.coordinator_records_clear_evidence is False


# ---------------------------------------------------------------------------
# The four named contradictions, one test each
# ---------------------------------------------------------------------------


def test_c1_a_replaced_inode_is_w7_sw_j11_and_not_corruption() -> None:
    verdict = validate_generation(SEAL, healthy(journal_inode=9999))
    assert (verdict.step.value, verdict.writer_refusal, verdict.coordinator_refusal) == (
        "W7", "SW-J11", "J-11",
    )
    assert verdict.writer_refusal != "SW-J04"


def test_c2_cross_generation_is_sw_j18_and_not_the_chain_rewrite_code() -> None:
    verdict = validate_generation(SEAL, healthy(records=chain_with(1, generation_id="000009")))
    assert (verdict.writer_refusal, verdict.coordinator_refusal) == ("SW-J18", "J-18")
    assert verdict.writer_refusal != "SW-J09"


@pytest.mark.parametrize(
    "overrides, writer, coordinator",
    [
        ({"current_target": None}, "SW-J03", "J-03"),
        ({"journal_read": ArtifactRead.ENOENT, "journal_device": None, "journal_inode": None},
         "SW-J03", "J-03"),
        ({"seal_read": ArtifactRead.ENOENT}, "SW-J17", "J-17"),
        ({"journal_mode": 0o644}, "SW-J05", "J-05"),
        ({"append_flag": FlagRead.ABSENT}, "SW-J06", "J-06"),
        ({"journal_read": ArtifactRead.EACCES, "journal_device": None, "journal_inode": None},
         "SW-J12", "J-12"),
        ({"derived_genesis_digest": "x", "record_zero_digest": "x"}, "SW-J24", "J-24"),
    ],
    ids=["current", "journal", "seal", "owner-mode", "append", "unreadable", "seal-corrupt"],
)
def test_c3_missing_owner_mode_append_unreadable_and_seal_corruption_stay_distinct(
    overrides, writer, coordinator
) -> None:
    verdict = validate_generation(SEAL, healthy(**overrides))
    assert (verdict.writer_refusal, verdict.coordinator_refusal) == (writer, coordinator)
    # Pre-remediation, the coordinator side of every "missing" was J-16.
    assert verdict.coordinator_refusal != "J-16"


#: Combined faults, each resolved by V-W's order (§2.13.5b): the earlier step's
#: code wins. Pre-remediation, the first row was `CORRUPT`.
PRECEDENCE = [
    ("stale-deployment-before-broken-chain",
     {"deployment_digest": "other", "records": chain_with(2, prev_hash="x")}, "SW-J22"),
    ("stale-deployment-before-empty-journal",
     {"deployment_digest": "other", "records": (), "record_zero_digest": None}, "SW-J22"),
    ("stale-deployment-before-cross-generation",
     {"deployment_digest": "other", "records": chain_with(1, generation_id="000002")}, "SW-J22"),
    ("host-before-deployment", {"machine_id": "x", "deployment_digest": "x"}, "SW-J23"),
    ("replaced-inode-before-owner-mode", {"journal_inode": 1, "journal_mode": 0o600}, "SW-J11"),
    ("replaced-inode-before-append-flag",
     {"journal_inode": 1, "append_flag": FlagRead.ABSENT}, "SW-J11"),
    ("seal-missing-before-journal-missing",
     {"seal_read": ArtifactRead.ENOENT, "journal_read": ArtifactRead.ENOENT,
      "journal_device": None, "journal_inode": None}, "SW-J17"),
    ("current-before-everything",
     {"current_target": None, "seal_read": ArtifactRead.ENOENT, "journal_inode": 1}, "SW-J03"),
    ("seal-structure-before-genesis-derivation",
     {"seal_format_supported": False, "derived_genesis_digest": "x"}, "SW-J24"),
    ("probe-before-seal-mutable",
     {"probe_report_admissible": False, "seal_immutable": FlagRead.ABSENT}, "SW-J25"),
    ("seal-mutable-before-journal-unreadable",
     {"seal_immutable": FlagRead.ABSENT, "journal_read": ArtifactRead.EIO,
      "journal_device": None, "journal_inode": None}, "SW-J17"),
    ("filesystem-before-empty",
     {"free_bytes": 0, "records": (), "record_zero_digest": None}, "SW-J13"),
    ("source-manifest-before-provenance",
     {"deployed_source_manifest_digest": "x", "provenance_valid": False}, "SW-J27"),
    ("generation-check-before-chain-on-one-record",
     {"records": chain_with(2, generation_id="000002", prev_hash="x")}, "SW-J18"),
    ("earlier-record-first",
     {"records": chain_with(3, generation_id="000002")[:2]
      + (dataclasses.replace(DISPATCH, prev_hash="x"),)
      + (dataclasses.replace(OUTCOME, generation_id="000002"),)}, "SW-J09"),
    ("chain-before-torn-tail", {"records": chain_with(2, hash_verifies=False),
                                "torn_tail": True}, "SW-J09"),
    ("torn-tail-before-sealed", {"records": chain_with(3, kind="seal"),
                                 "torn_tail": True}, "SW-J02"),
]


@pytest.mark.parametrize(
    "overrides, writer", [row[1:] for row in PRECEDENCE], ids=[row[0] for row in PRECEDENCE]
)
def test_c4_combined_faults_follow_the_writers_w1_to_w16_order(overrides, writer) -> None:
    assert validate_generation(SEAL, healthy(**overrides)).writer_refusal == writer


#: §2.13.5b's V-W table, top to bottom, read-only steps only.
PLAN_ORDER = (
    "W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8",
    "W9", "W10", "W11", "W11a", "W12", "W13", "W14", "W15", "W16",
)

#: Every two oracle faults at different steps that can be present at once (their
#: overrides touch different readings), earlier step first.
STEP_PAIRS = [
    (earlier, later)
    for earlier in ORACLE
    for later in ORACLE
    if PLAN_ORDER.index(earlier[2]) < PLAN_ORDER.index(later[2])
    and not set(earlier[1]) & set(later[1])
]


def test_c4_the_pairwise_matrix_covers_every_adjacent_step_boundary() -> None:
    covered = {(earlier[2], later[2]) for earlier, later in STEP_PAIRS}
    assert set(zip(PLAN_ORDER, PLAN_ORDER[1:])) <= covered


@pytest.mark.parametrize(
    "earlier, later", STEP_PAIRS, ids=[f"{a[0]}-over-{b[0]}" for a, b in STEP_PAIRS]
)
def test_c4_of_two_faults_the_earlier_step_refuses(earlier, later) -> None:
    case, overrides, step, writer, coordinator = earlier
    verdict = validate_generation(SEAL, healthy(**{**later[1], **overrides}))
    assert (verdict.fault.name, verdict.step.value, verdict.writer_refusal) == (
        CAUSES[case][0], step, writer,
    )
    # A torn tail beside a later fault leaves the coordinator code open: J-02's
    # C column and C-e say J-20, but C-a would first have to pass W16. Not
    # asserted until the design rules on it.
    if case != "torn-tail":
        assert verdict.coordinator_refusal == coordinator


#: One record's W14 checks in the order the step lists them: format_version,
#: generation_id, seq, prev_hash / record_hash, at.
W14_CHECKS = (
    ("format", {"format_known": False}, "SW-J07"),
    ("generation", {"generation_id": "000002"}, "SW-J18"),
    ("sequence", {"seq": 1}, "SW-J10"),
    ("sequence", {"seq": 7}, "SW-J08"),
    ("chain", {"prev_hash": "x"}, "SW-J09"),
    ("chain", {"hash_verifies": False}, "SW-J09"),
    ("time", {"at": 0}, "SW-J21"),
)

W14_PAIRS = [
    (earlier, later)
    for i, earlier in enumerate(W14_CHECKS)
    for later in W14_CHECKS[i + 1:]
    if earlier[0] != later[0]
]


@pytest.mark.parametrize(
    "earlier, later", W14_PAIRS, ids=[f"{a[2]}-over-{b[2]}" for a, b in W14_PAIRS]
)
def test_c4_within_one_record_w14_refuses_in_its_listed_order(earlier, later) -> None:
    observation = healthy(records=chain_with(2, **earlier[1], **later[1]))
    assert validate_generation(SEAL, observation).writer_refusal == earlier[2]


# ---------------------------------------------------------------------------
# The evidence record
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("row", ORACLE, ids=[row[0] for row in ORACLE])
def test_a_case_expecting_its_own_fault_passes_and_names_both_refusals(row) -> None:
    case, overrides, _, writer, coordinator = row
    fault = JournalFault[CAUSES[case][0]]
    evidence = classify_generation_state(
        case_id=f"JNL-{row[0]}", seal=SEAL, observation=healthy(**overrides),
        expected_fault=fault,
    )
    assert evidence.status is Status.PASSED
    assert evidence.detail["writer_refusal"] == writer
    assert evidence.detail["coordinator_refusal"] == coordinator
    assert evidence.detail["coordinator_records_clear_evidence"] is False


@pytest.mark.parametrize(
    "overrides, expected",
    [
        # JNL-38 (F-5) observed SW-J11: a case that expected the old mapping fails.
        ({"journal_inode": 9999}, JournalFault.GENESIS_RECORD_MISMATCH),
        # Same code, different cause: an empty journal is not a rewritten record 0.
        ({"records": (), "record_zero_digest": None}, JournalFault.GENESIS_RECORD_MISMATCH),
        # Same step, different code: unreadable is not missing.
        ({"journal_read": ArtifactRead.EACCES, "journal_device": None, "journal_inode": None},
         JournalFault.JOURNAL_MISSING),
        # A healthy observation where a refusal was expected.
        ({}, JournalFault.INODE_REPLACED),
    ],
    ids=["inode-as-genesis", "empty-as-genesis", "unreadable-as-missing", "healthy-as-refusal"],
)
def test_a_case_that_refuses_for_the_wrong_reason_fails(overrides, expected) -> None:
    evidence = classify_generation_state(
        case_id="JNL-x", seal=SEAL, observation=healthy(**overrides), expected_fault=expected,
    )
    assert evidence.status is Status.FAILED


#: **G9-R1.** What W7 and W8 compare on an opened journal.
OPENED_JOURNAL_FIELDS = (
    "journal_device", "journal_inode", "journal_uid", "journal_gid", "journal_mode",
)


@pytest.mark.parametrize("field", OPENED_JOURNAL_FIELDS)
def test_an_opened_journal_must_carry_every_fstat_field(field) -> None:
    with pytest.raises(ObservationRefused, match=field):
        healthy(**{field: None})
    with pytest.raises(ObservationRefused, match=field):
        dataclasses.replace(healthy(), **{field: None})


@pytest.mark.parametrize(
    "expected", [None, *JournalFault], ids=lambda f: "no-refusal" if f is None else f.value
)
@pytest.mark.parametrize("field", OPENED_JOURNAL_FIELDS)
def test_an_unobserved_fstat_field_yields_no_evidence_record(field, expected) -> None:
    """**G9-R1.** An unread value is not a wrong value: before the guard, an
    unread owner, group or mode classified as J-05 and a case expecting
    `OWNER_OR_MODE` recorded `passed`. No expectation may obtain any record."""
    with pytest.raises(ObservationRefused):
        classify_generation_state(
            case_id="JNL-x", seal=SEAL, observation=healthy(**{field: None}),
            expected_fault=expected,
        )


@pytest.mark.parametrize(
    "read, fault",
    [
        (ArtifactRead.ENOENT, JournalFault.JOURNAL_MISSING),
        (ArtifactRead.EACCES, JournalFault.JOURNAL_UNREADABLE),
        (ArtifactRead.EIO, JournalFault.JOURNAL_UNREADABLE),
    ],
    ids=["ENOENT", "EACCES", "EIO"],
)
def test_a_journal_that_was_not_opened_needs_no_fstat_fields(read, fault) -> None:
    observation = healthy(journal_read=read, **dict.fromkeys(OPENED_JOURNAL_FIELDS))
    assert validate_generation(SEAL, observation).fault is fault


@pytest.mark.parametrize("field", ["journal_uid", "journal_gid", "journal_mode"])
def test_a_zero_owner_group_or_mode_is_observed_and_compared(field) -> None:
    """uid 0, gid 0 and mode 0 are readings, not absences."""
    verdict = validate_generation(SEAL, healthy(**{field: 0}))
    assert verdict.fault is JournalFault.OWNER_OR_MODE


def test_record_zero_digest_is_present_exactly_when_record_zero_was_read() -> None:
    with pytest.raises(ObservationRefused):
        healthy(records=(), record_zero_digest="genesis")
    with pytest.raises(ObservationRefused):
        healthy(record_zero_digest=None)


# ---------------------------------------------------------------------------
# Coverage, narrowed and renamed (C-P5.0-R5-R1 A.3; S-9)
# ---------------------------------------------------------------------------


def _passing_records():
    records = []
    for name, overrides, *_ in ORACLE:
        observation = healthy(**overrides)
        records.append(
            classify_generation_state(
                case_id=f"JNL-{name}", seal=SEAL, observation=observation,
                expected_fault=JournalFault[CAUSES[name][0]],
            )
        )
    return records


def test_coverage_names_its_subset_and_is_not_a_closure() -> None:
    covered, message = modelled_fault_coverage(_passing_records())
    assert covered
    assert "not of the journal band" in message
    assert "P5.0-R5 remains Blocking" in message


def test_coverage_is_false_while_a_fault_is_unobserved() -> None:
    records = [r for r in _passing_records() if not r.case_id.endswith("inode-replaced")
               and not r.case_id.endswith("device-replaced")]
    covered, message = modelled_fault_coverage(records)
    assert not covered and "inode_replaced" in message


def test_a_failed_case_does_not_count_toward_coverage() -> None:
    wrong = classify_generation_state(
        case_id="JNL-38", seal=SEAL, observation=healthy(journal_inode=9999),
        expected_fault=JournalFault.EMPTY_JOURNAL,
    )
    assert wrong.status is Status.FAILED
    records = [r for r in _passing_records() if "replaced" not in r.case_id] + [wrong]
    covered, _ = modelled_fault_coverage(records)
    assert not covered


def test_the_overclaiming_names_are_gone() -> None:
    assert not hasattr(journal, "p5_0_r5_evidence_complete")
    assert not hasattr(journal, "GenerationCondition")
    assert "five refusals P5.0-R5 needs" not in (journal.__doc__ or "")
    assert "not** \"the refusals P5.0-R5 needs evidence for\"" in (journal.__doc__ or "")
