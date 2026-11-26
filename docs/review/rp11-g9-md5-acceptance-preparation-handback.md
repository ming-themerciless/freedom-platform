# RP-11 G9 — A-6 / MD-5 acceptance preparation handback — 2026-11-26

**This is preparation evidence only. It is not A-6 acceptance, not MD-5
acceptance, and not a review disposition.** The author prepared it; Codex is the
independent reviewer and makes the acceptance decision. G9/A-6 stays **open**.
No Codex acceptance record was written, and no current-state pointer was changed.

**Updated 2026-11-26 for Codex finding G9-R1 (Blocking for A-6).** F-2 is now
**remediated** (§5). `journal.py` changed, so the A-6 subject digest, the review
manifest (now **version 39**) and every dependent pin moved. Version 39 is
generated and tested; it is **not reviewed, committed or published**.

A-6 requires a durable, dated, independent record naming the C-1 … C-4
corrections and the `journal.py` digest it accepts
([authorization prompt](phase-5-0-p5-r5-operational-evidence-authorization-prompt.md),
§4 rows MD-5 and A-6; A0-09). This document is not that record and must not be
used as `⟨MI.md5_disposition⟩`.

## 1. Exact subject

Base commit (`HEAD`, branch `docs/platform-plan`):
`e776c986880b6754f6d192076d8fc58bec276489`, plus the uncommitted changes in §5.

| Item | Value now | Before (v38 / `HEAD`) |
|---|---|---|
| **`journal.py` SHA-256 (A-6 subject)** | `83a3dc77b32b6c4fca2de47defa6a57dff494c02060095a014fc35bc2a4f6b0d` | `b9ecf08c87ad0928e8d31436fd3ab1e5f0a4442ae451c80364ef09cbea93d0a9` |
| `journal.py` Git blob (worktree) / bytes | `cd36754107387ada22a302ef2cc1b270f7fa48c8` / 36049 | `04f1e6536dad98404dab4f3afe9547d0895ff645` / 35609 |
| review-manifest version | `39` | `38` |
| aggregate review-manifest digest | `92a59795a840a5f9b5548e25d0a5711cc39a02a4f682ba3beaad0f31ee9587cc` | `2a7564bb…2e1ca9` |
| manifest JSON (377690 bytes) | `7efe11d080fc1d6374ad5ff0748b81a1c1815999aa9e15a79a067bbb0a2673a2` | `4fa1c2b1…ca8d` |
| concrete plan (178764 bytes) | `a45c9c5ef6a3f7c531e337037b2b521638ca54164af2a2bf4ea738205b72e984` | `d827b755…d617` |
| `review_manifest.py` (82001 bytes) | `b7601a450278cddda5cbd014e205f225ac0799107b21a904d3877ef96b519492` | `f18d8fdf…3879`, 81359 bytes |
| `blocks/s01.sh` (11516) | `057bef68019135191b26a08b76f6f79334941f86720a110e3f17f2375b208d17` | `e9be1ab0…b2ca` |
| `blocks/s04c.sh` (4420) | `edaa1641cc0b5cb568e67ee08c3e18199728d6f1807fe2f5715c73d5388768be` | `6a65f597…d7f3` |
| `blocks/s04d.sh` (8708) | `2a33f831b652d5906b77a9fe216cdb82da4702335cb99cea33bc7bade1acb536` | `918d01cb…2f79` |
| `blocks/s11.sh` (10066) | `3944170aebb712466155159358012701cef2adfce8d9d18dd05e0c50c0f92d07` | `6229421e…5370` |
| `tests/test_r5_runner.py` (37271) | `416baa4818910059d9a3b1b1567ae0889928bbef0405fc102215cfb6bff2a62e` | `efa4ab46…a886`, 36986 |
| `tools/r5_runner/r5run.py` (59100) | `593dbb32d213100a92e23f4ff447c5ca209170e4907d2255a300364e82334282` | `869f71d2…53d2`, 58905 |
| classifier test file | `29f7a538d0df6f0610d6fa63c73bb71b796f3f1117d641e7a42793f02bbc9aaf` | `5f2cd600…c246` |
| controlling design `phase-5-0-package-plan.md` (unchanged) | `c9caad64a85a8e47540cfe720a37f83277a55db369739a1b66fa98c7850a0916` | same |
| `capture_tool_sha256` (recomputed; unchanged) | `f831d38c884822cd261b2da2c99da3d4958474d21eee2691b3e5e08028ea5134` | same |

## 2. Audit result

On reading against §2.13.5b (V-W, V-C) and §2.13.6, the C-1 … C-4 corrections
are implemented. The audit found two other things:

* **F-1 (test defect, fixed).** The tests did not independently establish
  precedence or fault identity.
* **F-2 (source gap; Codex G9-R1; fixed, awaiting re-review).** An incomplete
  observation could produce a passing `J-05` case.

One related residual, **G9-N1**, is reported in §6 and is not fixed.

## 3. Design-to-code and design-to-test mapping

Definitions: reconciliation handback
[§3.13](phase-5-0-p5-r5-evidence-reconciliation-handback.md). Code is
`journal.py`; all checks are in `_diagnose()` (line 399) and the refusal codes
in `FAULT_REFUSALS`. Tests are in
`tests/phase_5_0_evidence/test_r5_r1_journal_classifier.py`; "oracle" means the
hand-transcribed `ORACLE` plus `CAUSES` tables, which do not read
`FAULT_REFUSALS`.

### C-1 — replaced inode

| Case | Design | Code | Writer / coordinator | Tests |
|---|---|---|---|---|
| journal inode differs from `BND` | W7; J-11; F-11 | 421–427, `INODE_REPLACED` | `SW-J11` / `J-11` | `test_c1_…`; oracle `inode-replaced` |
| journal device differs from `BND` | W7; J-11; F-10 | same | `SW-J11` / `J-11` | oracle `device-replaced` |
| a case expecting the old corruption mapping fails | stop condition 10h | `classify_generation_state` | — | `…refuses_for_the_wrong_reason_fails[inode-as-genesis]` |

### C-2 — cross-generation record

| Case | Design | Code | Writer / coordinator | Tests |
|---|---|---|---|---|
| record's `generation_id` differs from `SB` | W14; J-18 | 457–473, `CROSS_GENERATION` | `SW-J18` / `J-18` (not `SW-J09`) | `test_c2_…`; oracle `cross-generation` |

### C-3 — missing artifacts, distinct conditions, coordinator J-rows

| Case | Design | Code | Writer / coordinator | Oracle cases |
|---|---|---|---|---|
| `current` absent or malformed | W1; J-03 | 401–403 | `SW-J03` / `J-03` | `current-absent`, `current-malformed` |
| seal absent | W2; J-17 | 404–406 | `SW-J17` / `J-17` | `seal-missing` |
| seal unreadable | W2; J-17 / J-12 (reading R-a) | 407–408 | `SW-J17` / `J-17` | `seal-eacces`, `seal-eio` |
| seal structure | W3; J-24 | 409–411 | `SW-J24` / `J-24` | `seal-format`, `binding-trailing-byte` |
| probe report | W4; J-25 | 412–414 | `SW-J25` / `J-25` | `probe-digest`, `probe-not-a-pass` |
| genesis derivation | W5; J-24 | 415–417 | `SW-J24` / `J-24` | `genesis-derivation` |
| seal mutable or flags unsupported | W6; J-17 | 418–420 | `SW-J17` / `J-17` | `seal-mutable`, `seal-flags-unsupported` |
| journal absent | W7; J-03 | 422–423 | `SW-J03` / `J-03` | `journal-missing` |
| journal unreadable | W7; J-12 | 424–425 | `SW-J12` / `J-12` | `journal-eacces`, `journal-eio` |
| owner, group, mode | W8; J-05 | 428–434 | `SW-J05` / `J-05` | `owner`, `group`, `mode` (incompleteness: §5) |
| `+a` absent or unsupported | W9; J-06 | 435–437 | `SW-J06` / `J-06` | `append-absent`, `append-unsupported` |

`test_c3_…` additionally asserts the seven distinctions §3.13 named and that
none reports the old coordinator `J-16`.

Adjacent steps the same replacement added, with the same oracle treatment: W10
`SW-J23`/`J-23`; W11 `SW-J22`/`J-22`; W11a `SW-J27`/`J-27` then `SW-J26`/`J-26`;
W12 `SW-J13`/`J-13`; W13 `SW-J04`/`J-04`; W14 `SW-J07`, `J08`, `J09`, `J10`,
`J21`; W15 `SW-J02`/`J-20` (reading R-b); W16 `SW-J19`/`J-19`.

### C-4 — precedence is the writer's order

| Case | Design | Tests |
|---|---|---|
| stale deployment beside a broken chain is `SW-J22` (the named contradiction) | W11 before W14 | `test_c4_combined_faults…[stale-deployment-before-broken-chain]` |
| other named combinations (17 rows) | V-W order | `PRECEDENCE` |
| every composable pair of oracle faults at different steps (679 pairs), covering all 16 adjacent boundaries W1 → W16 | V-W table order, restated as `PLAN_ORDER` | `test_c4_of_two_faults_the_earlier_step_refuses`; `…covers_every_adjacent_step_boundary` |
| order of checks on one record (19 pairs) | W14's listed order (reading R-d) | `test_c4_within_one_record_w14…` |
| W11a: manifest before provenance | W11a text | `PRECEDENCE[source-manifest-before-provenance]` |
| earliest defective record wins | "walk the chain" | `PRECEDENCE[earlier-record-first]` |

For a torn tail beside a later fault, only the fault, step and writer code are
asserted (R-b).

## 4. F-1 — test remediation

**Method.** `journal.py` was mutated **in memory only** and the classifier test
file run against each mutant.

* **Before:** 15 of 26 mutants survived. Survivors: swaps of adjacent step
  blocks W2/W3, W3/W4, W4/W5, W5/W6, W8/W9, W9/W10, W11/W11a, W11a/W12; the
  record-0 comparison moved after W14; four swaps of adjacent W14 checks;
  exchanging `SEAL_MISSING` with `SEAL_UNREADABLE`; a wrong §2.13.6 `row` on the
  torn tail; and halving the free-space floor.
* **Causes.** Only some adjacent boundaries had a combined case. The oracle
  asserted step and codes but not the fault member or row. Two tests took
  `expected_fault` from `validate_generation()` itself, so expected equalled
  observed by construction. The N5.0-21 boundary was read from the module.
* **Changes (tests only, 739 added collected cases):** the independent `CAUSES`
  table (fault member and row); both self-derived expectations now use it; a
  literal 1 GiB boundary test; the pairwise step matrix; the W14 matrix.
* **After:** all 26 mutants fail the file. The same unmutated source passes.

This run predates the G9-R1 guard and was **not repeated** afterwards. The guard
is in `__post_init__`; it does not touch `_diagnose()`.

The 26 mutants: swap each adjacent pair of `_diagnose` step blocks (15; W13/W14
excluded as a block swap because W14 depends on W13's non-empty guard); move the
record-0 comparison below W14 (1); swap each adjacent pair of the six W14 `if`
blocks (5); exchange `SEAL_MISSING`/`SEAL_UNREADABLE` and
`EMPTY_JOURNAL`/`GENESIS_RECORD_MISMATCH` (2); change the torn-tail `row` (1);
`<` to `<=` on free bytes, and halve the floor (2). The driver was a temporary
script outside the repository and is not retained.

## 5. F-2 / G9-R1 — remediated

**Defect.** With `journal_read=OK` and `journal_uid`, `journal_gid` or
`journal_mode` set to `None`, `validate_generation()` returned `SW-J05`/`J-05`
and `classify_generation_state(expected_fault=OWNER_OR_MODE)` recorded `passed`.

**Fix.** `JournalObservation.__post_init__` now raises `ObservationRefused` when
the journal was opened and any of `journal_device`, `journal_inode`,
`journal_uid`, `journal_gid` or `journal_mode` is `None`. The message names the
unobserved fields. Consequences:

* no observation object exists, so neither `validate_generation()` nor
  `classify_generation_state()` can be handed one, and no record of any status
  is produced. This includes cases whose expected fault is an earlier V-W step;
* `0` is still a reading (uid 0, gid 0, mode 0 compare and refuse as `J-05`);
* a journal that was not opened (`ENOENT`, `EACCES`, `EIO`) still needs none of
  the five fields and classifies as before;
* no V-W step, precedence, refusal code or fault mapping changed.

**Regression tests**, written first. Against the unfixed source the classifier
file gave **89 failed, 916 passed**; with the guard, **1005 passed**.

* `test_an_opened_journal_must_carry_every_fstat_field` (5; construction and
  `dataclasses.replace`);
* `test_an_unobserved_fstat_field_yields_no_evidence_record` (5 fields × every
  `JournalFault` and "no refusal");
* `test_a_journal_that_was_not_opened_needs_no_fstat_fields` (3);
* `test_a_zero_owner_group_or_mode_is_observed_and_compared` (3).
* `test_an_opened_journal_must_carry_its_inode` is replaced by the first of these.

**Re-derivation (version 39).**

| File | Change |
|---|---|
| `tools/phase_5_0_evidence/journal.py` | the guard |
| `tools/phase_5_0_evidence/review_manifest.py` | `MANIFEST_VERSION` 38 → 39 and its history note |
| `…-review-manifest.json`, `…-concrete-plan.md` | regenerated by the dry-run generator, twice, byte-identical. Only the version, two source digests and the plan's digest line moved |
| operational authorization prompt | G1 status note, §4.3 heading and history, `PIN.manifest_version`, `reviewed_digest`, `manifest_json_sha256`, `concrete_plan_sha256`, `journal_py`. The other four `PIN.*_py` rows were rechecked against bytes |
| R5 rebuild assignment | G1 note, §3.1, §3.2, §3.5, §6 S1.8 text and expected output, command line, Appendices A–C |
| `tools/r5_runner/blocks/s01.sh`, `s04c.sh`, `s04d.sh`, `s11.sh` | embedded digests and lengths; S1.8 tuple in `s01.sh` |
| `tools/r5_runner/r5run.py` | `PINS`; plus the fix below |
| `tests/test_r5_runner.py` | S1.8 amendment tuple and comment; one new test |
| `tests/phase_5_0_evidence/test_r16_remediation.py` | version assertion 39 and comment |

**One further fix in the runner (review it separately).** `render_body()` selected
the S1.8 result line for the handback excerpt by the literal prefix `"30 "`, the
manifest version of an earlier tree. From version 31 on, the §3 excerpt would
omit that line (the §6 transcripts still carry it; no pass/fail gate used it). It
is now `MANIFEST_RESULT_PREFIX = "39 "`, and
`test_the_handback_excerpt_selects_the_s18_line_of_the_pinned_manifest_version`
ties it to the amendment tuple.

**Not changed, deliberately.** Dated history keeps its v38 values: earlier
handbacks (including the plan and G6 handbacks), `change-log.md`, `status.md`,
`implementation-plan.md`, `Handover information` and the Pass A entry contract.
Their "now v38" sentences describe the published tree and will need a v39 record
once Codex dispositions this change. The docstring of the covered
`execution/pass_a_plan.py` (line 53) still says "(version 38)"; it is not a pin,
and editing it would move a second covered source.

## 6. Design readings and limitations for the reviewer

None of these was changed. R-a and R-b were disclosed by the R1 handback; no
ruling on them was found.

* **R-a.** An unreadable seal is named by both J-12 and J-17. The model follows
  W2: `J-17`.
* **R-b.** Torn tail: writer `SW-J02`, coordinator `J-20` (J-02 C column, C-e).
  C-a's "matching row" could instead mean `J-02`. **Also:** if C-a defers the
  torn tail to C-e, a torn tail on a sealed generation should refuse first at
  C-a/W16 as `J-19`, but the model reports `J-20`. The design needs a ruling.
* **R-c.** For J-22, J-23, J-25 and J-27 the §2.13.6 C column cites C-d; the
  model records the C-a refusal. C-b … C-f are not modelled.
* **R-d.** W14 lists its checks in one sentence. Treating that order as
  precedence is a reading; the refusal column does not state an order.
* **R-e (new).** J-19 is titled "a dispatch after a `seal` record", but its
  detection and W16 test only the **last** record's kind. A `seal` record in
  mid-chain followed by other records gets **no refusal** from the model. This
  follows V-W and looks like a design question.
* **G9-N1 (new; same shape as F-2; not fixed).** Fields annotated non-Optional
  are not checked at run time. A producer that violates the annotation with
  `None` can still obtain a `passed` record: confirmed for `torn_tail` and
  `filesystem_read_only` (read as "no refusal"), and for `machine_id` and
  `provenance_valid` (read as that fault). Most other such fields likewise
  classify `None` as their step's fault; `free_bytes` raises `TypeError` and
  `records` is refused. `ChainRecord` and `SealBody` have no run-time checks
  either (not probed). G9-R1 named the five fields the type admits as `None`, so
  this was left alone. **Codex to say whether A-6 needs it**; deciding before
  publication avoids another manifest version.
* **L-1.** The `probe_report_admissible` description omits W4's
  `PR.writer_deployment_digest == SB.writer_deployment_digest` condition. A
  future producer must include it.
* **L-2.** `record_zero_digest` is compared with `derived_genesis_digest`; the
  design specifies byte-for-byte equality of record 0. A producer must compute
  both over the same bytes.
* **L-3.** `journal_read` covers open and read together. A read error met later
  in the walk has no separate step.
* **L-4.** W17/W18, C-b … C-f, J-01, J-14, J-15, J-16, J-20 (other than a torn
  tail) and J-28 are not modelled. A "no refusal" verdict is never clear
  evidence.
* **L-5.** The model takes typed facts. No reader of a real journal exists, so
  nothing here is host or production evidence.

## 7. Provenance and history

| Date | Event |
|---|---|
| 2026-09-23 | Reconciliation §3.13 records C-1 … C-4 against the earlier five-condition classifier |
| 2026-09-23 | [C-P5.0-R5-R1](phase-5-0-p5-r5-r1-classifier-and-stage4-remediation-handback.md) replaces it (repository only, uncommitted at the time) |
| 2026-09-23 | [MD-5](project-review-2026-09-23-p5-r5-md5-classifier-prerequisite.md): Peter requires correction **and independent review** before any band is executable. It accepts the prerequisite, not the correction |
| 2026-09-23 | R2, R3 and R4 handbacks follow (S4-3 work); no `journal.py` entry was found in them. [R3](project-review-2026-09-23-p5-r5-r3-acceptance.md) and [R4](project-review-2026-09-23-p5-r5-r4-acceptance.md) acceptances close other findings only |
| 2026-09-27 | Commit `c9ee66d` first records the current `journal.py` bytes |
| 2026-11-25/26 | Same bytes at `575218e` (v38), `2afca20` (G6) and `HEAD` |
| 2026-11-26 | Codex G9-R1; guard added, new bytes `83a3dc77…6b0d`, manifest v39 (uncommitted) |

Earlier commits of the file: `5b0d1f2` (`c6ee3317…`), `2fb1d6f` (`9678c5a2…`).

**Gap.** The R1 handback records no `journal.py` digest, and its v18 manifest is
not in the commits inspected, so byte identity between R1's return and `c9ee66d`
is **not established**. A-6 should therefore accept the current digest in §1 after its
own review, not by reference to R1. No explicit independent acceptance of
C-1 … C-4 was found: the prompt's A-6 row records the same, later "accepted
mappings" wording is not an acceptance record, and the change-log row for R1
still says *"Not approved"*.

## 8. Commands and results

Repository host only. `/opt/freedom-blades/runtime/venv-web/bin/python` (Python
3.14.4, pytest 9.2.0), each run as
`env -u TEST_DATABASE_URL PYTHONDONTWRITEBYTECODE=1 … -m pytest -q -rs -p no:cacheprovider`.
These figures are for the version-39 working tree.

| Run | Result |
|---|---|
| classifier file, new tests, **before** the guard | **89 failed**, 916 passed, exit 1 (expected) |
| classifier file, after the guard | **1005 passed** |
| A0-06 pair (classifier, `test_r5_r1_stage4_s4_3.py`) | **1055 passed**, 0 skipped, exit 0 |
| `tests/phase_5_0_evidence` | **4363 passed**, 0 failed, 0 skipped, exit 0 |
| `tests/test_r5_runner.py` | **80 passed**, exit 0 |
| `tests/test_rp11_*.py` (24 modules) | **3213 passed, 21 skipped**, exit 0 |
| `tests/web/test_p3_4_static_assets.py` (change-declaration guard) | **112 passed**, exit 0 |
| `tests/test_systemd_unit_control.py` | **417 passed, 1 skipped**, exit 0 |
| generator, `python -m tools.phase_5_0_evidence.execution.cli --manifest-out … --render …` (no `--execute`) | before the edit it reproduced v38 byte for byte; after, two identical runs; checked-in files equal a third run |
| dry-run figures | unchanged: 138 steps, 43 mutations, 47 cleanup steps, 4 unresolved (C-7, C-S4-3), `executable False` |
| `git diff --check` | clean |

Skips, `test_rp11_*` (21): 16 need `RP11_LAUNCH_BUILD_ROOT` (cc1.v determinism
and toolchain tests), 2 cannot raise `RLIMIT_NOFILE`, 2 are opt-in host
measurements, 1 needs real root. The one `test_systemd_unit_control.py` skip: no
root-owned `env` executable on this host.

**Not run:** `oracle-test`; the canonical bot, web and Node suites; any R5 block
or the runner itself; any SA-2 build, so G6's `tree_sha256` was **not**
re-observed. No changed file is in `build.SOURCES`, `ENTRY_SOURCES` or
`RP11_SOURCES`, nothing under `infra/` changed, and `capture_tool_sha256`
recomputes to the accepted value.

## 9. Boundaries, effects and next action

`run_pass_a` was not called. No A-2/AUTH grant, SA-2 build or install, service
action, host contact, staging or production action occurred, and no secret was
read. Nothing was committed or pushed. No deployment, migration or data effect.
Rollback is reverting the files in §5, the classifier test and this handback
together; a partial revert leaves the pins inconsistent.

**Publication cost.** `journal.py` is covered, so the published and re-acquired
v38 tree (`575218e`) is no longer a tree a pass may pin. After review, version 39
needs a commit, maintainer publication, re-acquisition on `oracle-test` and
remote re-validation. A-6 and any pass pin that successor commit.

**Next action:** Codex re-reviews G9-R1, the version-39 re-derivation, the runner
prefix fix and the F-1 tests; rules on G9-N1 and readings R-a … R-e (none was
resolved here); and, if satisfied, writes its own dated A-6 record naming
C-1 … C-4 and the `journal.py` digest in §1. G9/A-6 stays open until then; G10
and `run_pass_a` remain separately gated.
