# RP-11 G9 / A-6 — independent MD-5 classifier acceptance

**Reviewer:** Codex · **Date:** 2026-11-27

Codex independently accepts the C-1 through C-4 classifier corrections for A-6
at implementation commit `7373fd405c719f63927eac7c2fc9b87a82d6dbb4`.
The accepted `tools/phase_5_0_evidence/journal.py` SHA-256 is
`83a3dc77b32b6c4fca2de47defa6a57dff494c02060095a014fc35bc2a4f6b0d`.
Use this record as the candidate `MI.md5_disposition` reference when the
single-host Pass A authorization prompt is amended. The prerequisite and review
scope come from [MD-5](project-review-2026-09-23-p5-r5-md5-classifier-prerequisite.md).

## Disposition

I compared the cases in [reconciliation §3.13](phase-5-0-p5-r5-evidence-reconciliation-handback.md#313-the-two-contradictions-stated-exactly)
with package-plan §§2.13.5b and 2.13.6, then traced the classifier branches,
refusal mappings and tests.

| Correction | Independently verified behavior |
|---|---|
| C-1 | Journal device or inode mismatch refuses at W7 as `SW-J11` / `J-11`. |
| C-2 | A cross-generation record refuses at W14 as `SW-J18` / `J-18`. |
| C-3 | An unresolved current link or missing journal maps to `J-03`. Missing seal, mismatched owner/group/mode, missing append flag and unreadable journal map separately to `J-17`, `J-05`, `J-06` and `J-12`. A successful-open observation missing any of the five W7/W8 metadata fields raises `ObservationRefused` at construction. Zero values remain observations. |
| C-4 | W11 wins over W13/W14 when stale deployment and chain faults coexist, yielding `SW-J22` / `J-22`. Tests use design-derived expectations and exercise every adjacent modeled step boundary with compatible fault combinations. |

G9-R1 is closed. The guard prevents an unobserved W8 value from counting as an
observed mismatch and producing a passing evidence record. The tests cover
all five metadata fields, preserve the missing and unreadable journal
classifications, and assert fault identity independently of classifier output.

G9-N1 is outside this acceptance. The model trusts the declared types of
other inputs. A future producer must validate observations at its input
boundary before it can supply evidence. The design readings R-a through R-e
remain documented for that later review, including the coordinator treatment
of a torn tail on a sealed chain and a seal followed by more records.
The scope is the C-1 through C-4 harness classifier corrections only.
[Claude preparation and remediation handback](rp11-g9-md5-acceptance-preparation-handback.md)

## Independent validation

Manifest v39 aggregate
`92a59795a840a5f9b5548e25d0a5711cc39a02a4f682ba3beaad0f31ee9587cc`.
The generated manifest and plan matched a fresh dry-run serialization byte
for byte. The dry run reported `executable: False`. The runner and draft
prompt pins match v39. Publication was verified against the canonical branch
and the same commit was fetched and checked out detached on `oracle-test`.
The checkout was clean and `git fsck --no-dangling` passed. The classifier,
manifest JSON and concrete-plan file hashes on `oracle-test` matched the
v39 pins. The two G6 reference builds remain recorded at `2afca20`.

| Check | Result |
|---|---|
| Independent local evidence, runner, static guards and unit control | 4,972 passed, 1 skip for root-owned `env`, 27.21 s |
| Disposable host classifier, S4-3, runner pins and static guards | 1,247 passed, 0 skipped, 12.92 s |
| Disposable host broader focused suite | 4,969 passed, 4 failed, 293.79 s |
| Canonical bot suite | 8,488 passed, 281 skipped, 6 warnings, 2,254.20 s |
| Canonical web suite | 2,894 passed, 80 skipped, 1,137 warnings, 1,066.98 s |
| Canonical Foundry Node suite | 171 passed, 0 failed, 0 skipped, 6,293.477441 ms |

The canonical suites ran serially on the detached v39 commit using the
disposable-server runbook. Both Python suites used PostgreSQL 18 and
`freedom_test`. All three suites exited zero. The detached checkout was
clean after Node completed.

The four broader focused failures are the same absence assertions for the
pre-existing `/run/freedom-blades/laboratory.lock` reproduced against the
earlier baseline in the [Pass A plan handback](rp11-pass-a-plan-handback.md).
The sentinel stayed in place. The focused G9 checks ran as unit tests outside
Pass A.

## Pass A admission

RP-10 remains open. A1-C is `not_run (RP-10 unmet)` until a digest-pinned
target-fact statement and its independent verification exist.
G10 requires the amended single-host prompt to resolve the remaining design
and contract prerequisites and define the applicable AUTH rows. A-1 then
requires independent review of its exact bytes and clean pinned commit.
Peter must record a dated A-2 authorization naming the operator, attesting
under A-5 that the target holds no production data or credentials, and
specifying each applicable AUTH grant and band. Actual `run_pass_a`
also requires a reviewed operational entry and explicit execution authority.
G1 stays accepted for review only.
[Pass A entry contract](rp11-pass-a-entry-contract-proposal.md#6-decisions-and-gates--each-separate)
