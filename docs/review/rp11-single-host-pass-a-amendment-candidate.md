# CANDIDATE — REVIEW ONLY — NOT AUTHORIZED — RP-11 single-host Pass A normative delta

> **INERT. DO NOT EXECUTE.** This document grants nothing. It is not A-1, A-2,
> A-5, an AUTH grant, source-acquisition authority or execution authority. It
> changes no code, pin, command or other document. Every "shall" below is
> **proposed** text. It takes effect only if reviewed and accepted, and no
> sentence here may be read as a command to run.

**Drafter:** Claude · **Date:** 2026-11-27 · **For:** independent Codex review
**Amends (proposed):** [C-P5.0-R5-OP1 draft](phase-5-0-p5-r5-operational-evidence-authorization-prompt.md)
("the old draft"), Pass A only.
**Inputs:** [entry-contract proposal](rp11-pass-a-entry-contract-proposal.md),
`tools/phase_5_0_evidence/execution/pass_a_plan.py` and `pass_a.py`, their tests,
`infra/rp11-h1/rp11_entry.py` and `build.py`,
[G6 handback](rp11-g6-preparation-handback.md),
[G9 / A-6 disposition](rp11-g9-md5-independent-acceptance.md).

**Update 2026-11-28:** Peter approved Codex's recommendations on D-1 … D-10.
[§14](#14-owner-policy-decisions--2026-11-28) records them and governs where
§§1–13 still say "proposed", "recommended" or "open" about those decisions.
§§1–13 are kept as drafted and reviewed. The document remains inert and grants
nothing.

**Result in one line:** the v39 plan can be described as a single-host contract,
but **Pass A is not admissible and cannot be run**. It also does not yet enforce
several obligations of the old draft (§10).

## 1. Scope and precedence

1. Pass A only. **Pass B is excluded entirely**: Bands B0–B7, B0-RA,
   `capture-b` use, RP-1 … RP-9 and RP-12, AUTH-V7, -HARNESS, -DB, -PRODUCERS,
   -RR and -REBOOT. Nothing here amends or satisfies any of them.
2. If accepted, this delta replaces for Pass A: old §4.2 (Pass A rows), §4.3
   (pin roles), §5, §6, and the host-role wording of §9, §13 and §14. Old §10
   (items 1–2 and 9–10), §11.1, §11.3, §12 and §15 continue to apply, reading
   "repository host" as `oracle-test`. Old §9.5 continues as amended in §6.3.
3. Pass A evidence is disposable-host feasibility evidence. It says nothing
   about production. Production and staging have no role.
4. Accepted decisions carried unchanged: G4 topology and paths, G5 identity
   `capture`, G7 timeout policy, G11 provenance, G12 loading. G1 stays
   **accepted for review only**.

## 2. Commit and evidence identities

Four different things. None substitutes for another.

| Identity | Value | What it establishes | What it does not |
|---|---|---|---|
| **G6 reference** | commit `2afca2098625a3e09b05d3f51918c82ccebeb543` (manifest v38) | two byte-identical non-installing SA-2 builds; `tree_sha256` `824c973907f9b954651973796bdc37633cb7fa931a1a56cd9aca1e66e62bdaca`; `capture_tool_sha256` `f831d38c884822cd261b2da2c99da3d4958474d21eee2691b3e5e08028ea5134` | no install; no v39 build; not the pass's commit |
| **Tested / A-6 commit** | `7373fd405c719f63927eac7c2fc9b87a82d6dbb4` (manifest v39) | the canonical suites and publication recorded in the G9 disposition; A-6 for `journal.py` `83a3dc77…6b0d` | not A-1; not a pass authorization; does not contain this candidate or the G9 record |
| **Recording successor** | `22be617` (`HEAD` when drafted) | documentation of the G9 result. `git diff 7373fd4 22be617` lists six documentation files only | no suite run, publication or acquisition is claimed for it here |
| **Candidate clean commit** `⟨MI.pinned_commit⟩` | **does not exist** | to be created after this delta and its blockers are resolved, then reviewed (A-1), published and acquired | may not be filled with any of the three above by default |

**Carry-over, an inference from `git diff 2afca20 7373fd4`, not a rebuild.** The
only changed files under `tools/` outside `tools/r5_runner/` are `journal.py`
(the harness classifier) and `review_manifest.py`. Neither is in `build.py`'s
`SOURCES`, `ENTRY_SOURCES` or `RP11_SOURCES`, and nothing under `infra/`,
`application/` or `adapters/` changed. The G6 SA-2 input bytes are therefore
unchanged at `7373fd4`. Any change made to close §10 can end that, and then
requires new reference builds and review.

## 3. Digest roles

Values were recomputed from the working tree at drafting unless marked.
A digest shows identical bytes, never that the bytes are acceptable.

| Pin | Value | Role | Compared by | When |
|---|---|---|---|---|
| `PIN.prompt_sha256` | **unresolved.** The old draft is currently `e80d9d8c…e5448c`; that is not an accepted value | binds A-1 and A-2 to exact contract bytes | A0-03 (see mismatch M-1) | review, then in-pass |
| `PIN.reviewed_digest_A` | v39 `92a59795a840a5f9b5548e25d0a5711cc39a02a4f682ba3beaad0f31ee9587cc` (candidate, from the old draft and G9; not recomputed) | the 66 covered sources | A0-05 output | in-pass |
| `PIN.manifest_json_sha256` | `7efe11d080fc1d6374ad5ff0748b81a1c1815999aa9e15a79a067bbb0a2673a2` | manifest file | A0-04 | in-pass |
| `PIN.concrete_plan_sha256` | `a45c9c5ef6a3f7c531e337037b2b521638ca54164af2a2bf4ea738205b72e984` | rendered harness plan | A0-04 | in-pass |
| `PIN.journal_py` | `83a3dc77b32b6c4fca2de47defa6a57dff494c02060095a014fc35bc2a4f6b0d` | A-6 subject | A1-S2 | in-pass |
| `PIN.unit_sandbox_py` | `edd360fbd01aaded56ee29bdf61af5cb9ae0882d0f990ad8f4e620fd8fc7a92c` | source identity | A1-S2 | in-pass |
| `PIN.case_program_py` | `bfd5ee20e927e70a8adcd18d4dd39e7e6c2aa89354ff708be63fc44c7fbc70dd` | source identity | A1-S2 | in-pass |
| `PIN.cli_py` | `485f960f1dee97feaef4a6c1f8e002c27262a427db470cd91c5dd36f057cb4d1` | source identity | A1-S2 | in-pass |
| `PIN.reservation_py` | `aa37107590755a6307b79bea7e37b1cca45e44709f99a54f1e390e09dc52340b` | source identity | A1-S2 | in-pass |
| `PIN.capture_tool_sha256` | proposed `f831d38c…5134` (G6; not recomputed) | the seven RP-11 sources; recorded in every index state | **nothing today** (B-5) | must precede X-1 |
| SA-2 `tree_sha256` | G6 `824c9739…bdaca` (not recomputed) | the whole installed artifact, which is what executes | the G6 review gate | before and after any install |
| `pass_config_sha256` | **unresolved**; no config exists | `pass-a.json` bytes | consume role, then the entry | start |
| machine `a2_sha256` | **unresolved** | the `rp11-a2/3` file (see D-5) | consume role | start |
| `PIN.pass_a_plan_py` (proposed, new) | `0b691f238606fb7eb237511c7f08510598f7f67ff3f772eaf63520485d4f67e3` | the command policy. Covered by the manifest; **not** in the SA-2 tree (B-2) | reviewed digest only | review |

`pass_a.py` is currently `e1fccf88…6cfa36`. It is in both the manifest and the
SA-2 tree.

`PIN.capture_tool_sha256` and `tree_sha256` are supplied from outside. Neither
may be copied from the run it is meant to check.

## 4. Admission

Stages are ordered. A later stage never repairs an earlier one.

### 4.1 Pre-acquisition (no pass exists, nothing is captured)

| # | Requirement | State |
|---|---|---|
| P-A1 | Policy decisions of §9 recorded | open |
| P-A2 | Implementation blockers of §10 closed, reviewed and tested | open |
| P-A3 | Exact clean commit created and published by the maintainer | absent |
| P-A4 | **A-1** (§4.5) against that commit and the contract bytes | absent |
| P-A5 | A separate source-acquisition authorization naming commit, actor, host and destination `/opt/freedom-blades/rp11-source` (proposed row **AUTH-ACQUIRE**, §5) | absent |

Earlier acquisitions of other commits are history and authorize nothing new.

### 4.2 Acquisition and post-acquisition record (still outside the pass)

Fetch from the canonical public remote only; detached checkout of
`⟨MI.pinned_commit⟩`; no credential, no rsync or copy from any other tree.
Record the commit, empty porcelain status, object check, manifest, plan,
contract and source digests, and the checkout's ownership and modes. `capture`
must be able to read it and not write it. This record does not replace the
in-pass checks; the checkout is re-checked there.

### 4.3 Pre-start (after A-2, A-5 and execution authorization, before the unit starts)

* A-1, A-2, A-5, A-6 (`MI.md5_disposition` = the G9 record, for the digest it
  names) and the applicable AUTH grants are referenced (replaces A0-09). A1-C
  is recorded `not_run (RP-10 unmet)`.
* Current-state records show nothing that supersedes or narrows this contract
  (A-3, replaces A0-01; see D-6).
* No `TEST_DATABASE_URL` or other operator variable can reach a child (replaces
  A0-07; the plan's closed environments provide this).
* The installed SA-2 tree matches the reviewed `tree_sha256`; the capture-tool
  bytes match `PIN.capture_tool_sha256`.
* `capture` conforms to `CAPTURE_IDENTITY`; `/var/lib/fb-rp11` conforms to
  `PARENT_CONTRACT` (`root:capture` 0770); `capture-a` is **absent**.
* No suite, rehearsal or other activity runs on `oracle-test` in the window.
* The current time is inside `MI.pass_a_window_utc`.

**Checks.** The bullets above verify state and change nothing. A check that
needs host access needs its own authority; none is granted here. A failed check
blocks the start and does not permit correcting the state.

**Provisioning (separately gated).** Creating or changing the account, parent,
unit or installed artifact is not a pre-start check. It needs its own
authorization; **no** Pass A AUTH row covers it.

### 4.4 Start and in-pass

1. The unit's consume pre-step succeeds; the entry validates the activation id
   and requires `INVOCATION_ID` to equal the consume `run-start`'s. A binding
   refusal creates nothing and issues no command.
2. X-1 creates `capture-a` exclusively and publishes genesis. This is the
   capability test. Without durable genesis no command runs.
3. The 49 planned acts of §6, in plan order, one at a time.

**Ordering change from the old draft, to be accepted explicitly:** A0-02 … A0-05
ran before X-1 and were not captured. In v39 they are captured acts after
genesis. A pin mismatch therefore consumes `capture-a` and the pass.

### 4.5 Owner and reviewer placeholders (all unfilled)

| Input | Placeholder |
|---|---|
| **Acquisition authorization** (P-A5): its own record, made before acquisition and so before A-2 | decision `⟨ACQ.decision⟩`; date `⟨ACQ.date⟩`; record `⟨ACQ.record_path⟩` / `⟨ACQ.record_sha256⟩`; actor `⟨ACQ.actor⟩`; commit `⟨MI.pinned_commit⟩`; host and destination as P-A5 |
| **A-1** — independent acceptance of exact bytes and clean commit | reviewer `⟨A1.reviewer⟩`; date `⟨A1.date⟩`; record `⟨A1.record_path⟩`; contract SHA-256 `⟨PIN.prompt_sha256⟩`; commit `⟨MI.pinned_commit⟩`; reviewed digest `⟨PIN.reviewed_digest_A⟩`; tool `⟨PIN.capture_tool_sha256⟩`; tree `⟨PIN.sa2_tree_sha256⟩`; outcome `⟨A1.outcome⟩` |
| **A-2** — Peter's dated written authorization | date `⟨A2.date⟩`; record `⟨A2.record_path⟩` / `⟨A2.record_sha256⟩`; operator `⟨MI.operator⟩`; window `⟨MI.pass_a_window_utc⟩`; root `⟨MI.capture_root_A⟩`; activation `⟨MI.activation_id⟩`; config `⟨MI.pass_config_sha256⟩`; reference to the prior acquisition decision `⟨ACQ.record_path⟩` / `⟨ACQ.record_sha256⟩` and its §4.2 result record `⟨ACQ.result_record_path⟩` / `⟨ACQ.result_record_sha256⟩`; AUTH-READ band A0 `⟨grant/refuse⟩`; AUTH-READ band A1 `⟨grant/refuse⟩`; AUTH-DBREAD `⟨grant/refuse/retired by D-2⟩` |
| **A-5** — attestation by Peter as Operations Owner and Data Owner, dated on or after A-2 | "`oracle-test` holds no production data and no production credential." date `⟨A5.date⟩`; record `⟨A5.record_path⟩`; signature `⟨A5.attestor⟩`. No secrets scan or content inspection establishes it |
| **Execution authorization**: distinct from A-2 | decision `⟨EXEC.decision⟩`; date `⟨EXEC.date⟩`; record `⟨EXEC.record_path⟩` / `⟨EXEC.record_sha256⟩`; operator `⟨MI.operator⟩`; activation `⟨MI.activation_id⟩`; window `⟨MI.pass_a_window_utc⟩` |

A-2 is mandatory. The execution authorization is a separate decision. Under the
current boundary **neither A-2 alone nor execution authorization alone
suffices**: a start needs both, as well as every other admission requirement of
this section. A-2 only references the acquisition decision and result; it does
not grant, renew or backdate acquisition.

## 5. Proposed AUTH dispositions and bands

Proposals only. **Every row is ungranted.**

| Row | Proposed disposition | Band and extent |
|---|---|---|
| **AUTH-SYNC** | **Retire.** The production-origin `rsync` is withdrawn. Do not reuse the name for acquisition | none |
| **AUTH-ACQUIRE** (new) | One fetch and detached checkout of the exact commit (§4.2), once, outside the pass, not through the capture mechanism. Decided in its own earlier record (§4.5), never as a grant inside A-2 | pre-pass |
| **AUTH-READ** | **Redefine:** local, unprivileged, read-only child processes launched by the reviewed entry as `capture`, with the plan's exact argv and environment. No `sudo`, no `ssh` | **A0** (6 acts: A0-02a, 02b, 03, 04, 05, A1-S2). **A1** (39 acts: 10 host, 4 tool, 11 laboratory, 4 quiescence, 10 final survey) |
| **AUTH-DBREAD** | **Retire for Pass A (recommended, D-2).** The remaining steps (`systemctl is-active postgresql@18-main`, `pg_lsclusters`) open no database session. Folding their 4 acts into AUTH-READ gives A1 43 acts | **A1-D** (4 acts: A1-29, 30, A1-Z-29, A1-Z-30) if retained |

A0 includes executing the checkout's harness dry run (A0-05) as `capture`. A
grant must say so.

If AUTH-DBREAD is retained it **cannot be refused independently today**: the
default plan always contains its four acts and nothing filters or enforces
`auth_row` (B-4). A refusal would then have to stop the whole pass.

Local capture writes (X-1 … X-3) are authorized by A-2 itself, only under
`capture-a`. Intended host changes of Pass A become: the capture root and its
contents, the unit's own run-time and consume evidence objects as the reviewed
activation procedure defines them (D-5), and incidental logs. The old
`rsync --delete` change is gone.

## 6. Mapping old obligations to the fixed v39 local plan

The authority for argv, environment, class and accepted exit is
`pass_a_plan.build_pass_a_plan()` at the reviewed digest, with
`include_corroboration=False`: 49 acts. Prose here never overrides those bytes.
Each act is a local child with no shell.

### 6.1 Steps

"Expected" is the old draft's obligation. **The plan checks exit status only**;
"expected" is not evaluated in the pass (M-2).

| Old | v39 act(s) | Accepted exit | Expected (to be preserved) | Disposition / mismatch |
|---|---|---|---|---|
| A0-01 | none | — | current records name the contract | pre-start (§4.3). Not in plan or `WITHDRAWN_STEPS` |
| A0-02 | A0-02a, A0-02b | 0 | `HEAD` = pinned commit; empty status | path is now `rp11-source`; `git` environment |
| A0-03 | A0-03 | 0 | `PIN.prompt_sha256` | **M-1** |
| A0-04 | A0-04 | 0 | two file digests | mapped |
| A0-05 | A0-05 | 0 | dry run, every `PIN.dry_run` figure, reviewed digest, `executable : False` | `env -u …` replaced by the `python` environment; flags `-B -P -m` |
| A0-06 | none | — | 0 failed, 0 skipped | withdrawn. Relies on the pinned commit's suite evidence, which must then name that commit |
| A0-07 | none | — | statement | closed environments |
| A0-08 | X-1 | — | tool digest match; root absent; genesis | root creation mapped; **tool-digest check absent** (B-5) |
| A0-09 | none | — | A-6 and RP-10 references | pre-start |
| A1-00 | none | — | sync once | withdrawn; §4.2 |
| A1-S1 | none (A0-05) | — | identical to A0-05 | duplicate on one host |
| A1-S2 | A1-S2 | 0 | five source pins | mapped |
| A1-01 … 03 | same | 0 | `Test`; `7.0.0-1015-oracle`; `x86_64` | values unchecked |
| A1-04 … 07 | same | 0 | OS name; boot id; machine-id digest; mount | values unchecked |
| A1-08, 09 | same | 0 | `= 1`; free bytes recorded | `/usr/sbin/sysctl` |
| A1-10 | A1-10 | 0 | recorded | adds `--no-pager` |
| A1-11, 12 | excluded | — | corroboration | **A1-C `not_run (RP-10 unmet)`** |
| A1-14, 15 | none | — | corroboration | withdrawn (`sudo`); also A1-C, also `not_run` |
| A1-13 | A1-13 | 0 | 3.14; flags `1 1` | the old draft's note that the harness says `3.12` is stale |
| A1-16 | A1-16 | 0 | `root:root`, not group/world-writable | **M-3: `/usr/bin/chattr` operand is gone** |
| A1-17, 18 | same | 0 | recorded | mapped |
| A1-19 | A1-19 | 1 | `R` does not resolve, **established as `ENOENT`** | argv and exit mapped; **absence not established by them** (M-2, D-1) |
| A1-20 | A1-20 | 0 | member `ubuntu` | membership unchecked |
| A1-21 | A1-21 | 0 | owner, mode, type of five paths | **M-4: four paths; `laboratory/runs` (V9) is gone** |
| A1-22 | none | — | V7 `lifecycle.json` absent | withdrawn: absence cannot be told from denial |
| A1-23 (seven) | A1-23a … g | 2 | all absent | mapped |
| A1-24 | A1-24 | 0 | `LoadState=not-found` | exit 0 also when loaded; value unchecked |
| A1-25 … 28 | same | 0 | baselines | **M-5** observer effect |
| A1-29, 30 | same | 0 | `active`; only `18/main` | see §5 |
| A1-31 … 33 | none | — | database/role absent; `pg_hba`/`pg_ident` digests | withdrawn (`sudo`). **No database catalog or configuration baseline is produced** |
| A1-Z | A1-Z-19, -21, -23a … g, -24, -29, -30 | as first reading | equal to the earlier value | equality unchecked; A1-Z-19 needs its own `ENOENT` evaluation (M-2, D-1); inherits M-4 and the A1-22 and A1-31 … 33 losses |

**Mismatches**

* **M-1.** `_PROMPT` in the plan hashes the **old draft** file. This candidate is
  a separate file, so A0-03 would not bind it. Either fold the accepted delta
  into that file, or change the plan (a covered source, so a new manifest).
* **M-2.** `exit_policy` receives only the request and the exit. A wrong
  nodename, pin, dirty status, changed dry run, loaded unit or changed final
  survey with the expected status does **not** stop the pass, and it can end
  `completed`. This contradicts old §11.2 and A-4 (D-1).
  **A1-19 and A1-Z-19:** the accepted exit 1 does not distinguish `ENOENT` from
  `EACCES` or any other `stat` failure. Absence of `R` is **not** accepted from
  the exit status, and equal exit statuses in the two acts show nothing more.
  Each act must be evaluated separately on its own captured output: exit 1,
  empty stdout, and a complete stderr that exactly matches a reviewed, pinned
  `ENOENT` diagnostic for `R`. `EACCES`, any other error, additional or
  incomplete output, or an unrecognized form leaves absence unestablished. The
  pinned form must be backed by evidence from the target's `stat` implementation
  under the plan's argv and environment; none is recorded in the material read.
* **M-3, M-4.** Two observations were dropped without a `WITHDRAWN_STEPS` entry,
  although the module says none disappears silently. The reason for M-3 was not
  found in the material read.
* **M-5.** Capture host and target are one. Process, service and session
  listings will include the pass's own unit and processes. The expected set must
  be named. The checkout, parent, root and `capture` account are not surveyed.
* **M-6.** The old draft still states the two-host form, "A-6 unmet", manifest
  v36 for the token line and pending reviews. `pass_a_plan.py`'s docstring says
  manifest version 38 although the manifest is v39. Editorial, but correcting a
  covered source moves digests.
* **M-7.** Pass B prerequisites that expected A1-22 and A1-31 … 33 from Pass A
  cannot be met by this plan. Recorded only; Pass B is excluded.

### 6.2 Environments, timeouts and bounds

| Class | Per-command timeout | Per-stream bound |
|---|---|---|
| T-local | 44 s | 64 KiB |
| T-dry | 161 s | 512 KiB |
| T-read | 30 s | 256 KiB |

Environments: `plain`, `git`, `python`, `systemd`, complete and non-inherited;
base `PATH=/usr/bin`, `LC_ALL=C`, `LANG=C`. Drain 5 s per act. Allowances:
genesis 30 s, per act 10 s, finalization 112 s. Default whole-pass bound
**2548 s**. The 2638 s figure includes A1-C and does not apply. Only the
per-command timeout and drain are enforced deadlines; the allowances and the
bound are derived worst-case figures that no manager enforces. The measurements
were taken against `b279de1`, not the future commit.

### 6.3 Capture requirements (old §9.5 and RP-11)

| Old requirement | Proposed single-host reading |
|---|---|
| Repository-host capture root; "no file created on `oracle-test`" (RP-11, C-6, §12) | the root is `/var/lib/fb-rp11/capture-a` on `oracle-test`. No capture file is written anywhere else. The checkout, parent, root, account and unit are expected objects, excluded by name from "no target change" claims |
| Operator's account owns files (C-7) | owner is `capture`; directories 0700, files 0600 |
| `ssh` command string recorded (C-1) | the exact local argv vector is recorded |
| Client clock (C-4) | `oracle-test` `CLOCK_REALTIME`; capture and target share one clock |
| Guard analysis of the §5 `rsync` (C-11) | replaced: every planned argv, rendered, is admitted by `guard-secrets.py` (an existing test; not run for this draft). Hooks do not run inside a systemd service, so this is a review property. No equivalent `guard-git.py` assertion was found for the two `git` acts |
| Pinned child environment (RP-11, G3) | the four plan environments; behaviour under the unit sandbox is unobserved |
| C-2, C-3, C-5, C-8, C-10, C-12 … C-15, §9.5.1 … §9.5.4 | unchanged, reading "repository host" as `oracle-test` and "remote command" as "child command" |

## 7. Capture, stop and handback

### 7.1 Stop rules

1. Any capture or durability failure, command timeout, stream over its bound,
   incomplete stream, start failure, unaccepted exit, signal exit, guard or
   permission refusal, or (after D-1) value mismatch ends the pass.
2. Order: no further command; **at most one** X-3 attempt, only with durable
   genesis and no interruption; behavioural seal; X-4 on the bytes present.
3. An act that was not admitted leaves unadmitted residue: retained, listed by
   exact relative name and type, never completed, renamed, deleted, digested
   into evidence or re-run. A timed-out child may have run.
4. An act with an admitted record but an unaccepted exit stays admitted
   evidence; the final state is `stopped`.
5. No retry, resume, continuation or reuse of `capture-a`, not even read-only
   commands. A further attempt needs a new written authorization and a decision
   on the retained root.
6. Interruption (kill, reboot, mechanism termination): no X-3, before or after
   recovery. **Proposed:** SIGTERM and `systemctl stop` are interruptions. The
   entry resets signals to default and installs no handler, which matches this.
   Entry-contract proposal §5 item 5 reads otherwise and must be reconciled
   (D-7).
7. The entry exits zero only when every act was admitted and accepted, X-3
   succeeded and X-4 is `valid`. Binding refusal, no genesis, stop and
   incomplete finalization are each non-zero.

### 7.2 Handback

* Path: `docs/review/phase-5-0-p5-r5-op1-a-preflight-handback.md`; evidence class
  FEASIBILITY.
* If X-1 created the root: exactly one `rp11-capture-binding/2` block with the
  eight lines of old §14 in order (`format`, `pass_id` =
  `C-P5.0-R5-OP1-A`, `invocation_id`, `capture_root`, `x3_outcome`,
  `x4_validity`, `final_state`, `capture_index_sha256`). Otherwise no block.
* Also: A-1, A-2, A-5, A-6 references; AUTH grants as given; operator; commit
  and the §3 digests; X-1 result; X-3 and X-4; admitted records with
  `capture_seq`, record digest, argv, times, exit and stream digests; every
  unadmitted object; expected versus observed for every §6.1 row; `not_run` with
  reason for A1-C and each withdrawn step; refusals and deviations; what the
  pass does not establish (old §15).
* Safe excerpts only (old §12). Raw streams are never committed.
* The root is retained unmodified until Codex's review and a maintainer
  disposition. Who may read it is D-9.
* The entry writes no handback prose. How the binding block leaves the process
  is B-6.
* A completed Pass A does not close P5.0-R5, satisfy any Pass B prerequisite by
  itself, or authorize anything further.

## 8. Roles

Under a systemd-run entry the operator no longer issues each command. Proposed:
`MI.operator` performs only the separately authorized pre-start checks and the
single start, reads the outcome and writes the handback. `capture` is the
execution identity, not the operator. Codex reviews before and after and does
not operate. Peter alone grants.

## 9. Unresolved policy decisions

| ID | Decision (owner: Peter unless noted) | Drafter's recommendation |
|---|---|---|
| D-1 | Are expected values enforced in the pass, or judged afterwards? | Enforce in-pass, at least identity (A-4), clean pinned commit, every digest, dry run, `R`/identity/unit absence and A1-Z equality. For `R` (A1-19, A1-Z-19), evaluate captured stdout and stderr by the M-2 rule, not the exit alone; anything but evidenced `ENOENT` stops the pass. Judging afterwards weakens stop-on-mismatch and needs explicit acceptance; it must apply the same rule to the admitted records, cite `capture_seq` and record and stream digests, and otherwise report absence as not established |
| D-2 | AUTH names and bands (§5) | Retire AUTH-SYNC and, for Pass A, AUTH-DBREAD; add AUTH-ACQUIRE |
| D-3 | Who acquires source, as which account, and does a new commit need a new grant? | one named actor per exact commit; yes |
| D-4 | Accept the lost observations (A0-06, A1-14/15, A1-22, A1-31 … 33, V9, `chattr`)? | accept the `sudo` withdrawals for Pass A with named residual gaps; restore `chattr` or record why not; record V9 as withdrawn |
| D-5 | How does Peter's written A-2 relate to the machine `rp11-a2/3` file, H-1 record, activation lease and hold that the consume role requires? Do they apply to this one-host feasibility pass? | state it explicitly: the machine file quotes the written grant and never substitutes for it |
| D-6 | A-3 needs current records to name the contract digest, while those records and later A-1/A-2 records are tracked files. Which tree holds them relative to the clean pinned commit? | records may live in a documentation-only successor; the pass pins the implementation commit and the record digests |
| D-7 | SIGTERM semantics (§7.1 item 6) | interruption, no X-3 |
| D-8 | Who starts the unit under the separate execution authorization (§4.5)? | the named operator |
| D-9 | Who may read the `capture`-owned 0700 root for handback and review, and by what authority? | a separate read-only, root-assisted grant, listed in A-2 |
| D-10 | Does a stop leave `capture-a` permanently retained, and what root would a later attempt use? Do not use `capture-b` | decide before the first start |

## 10. Operational implementation blockers

Observed in repository source at `22be617`. None is fixed by this document.

| ID | Blocker |
|---|---|
| B-1 | The run path ends at exit 69. `run_pass_a` has no caller and `build_pass_a_session` is unreachable |
| B-2 | `pass_a_plan.py` is not in `ENTRY_SOURCES`, and a test requires that nothing imports it. The installed artifact could not load the policy. Wiring changes the SA-2 tree digest and the safety tests |
| B-3 | No complete `pass-a.json` contract or entry loader for this pass: authority records, grants, window and pins. Of the document's content, the existing checks read for this draft require the `rp11-pass-a/1` schema, an absolute `capture_root` and a matching `activation_id`; other keys are opaque to them |
| B-4 | `auth_row` is dropped from `ActRequest`; no grant is enforced and no band can be excluded. Admission acts carry the default `AUTH-READ` label |
| B-5 | No A0-08 check compares the running capture-tool bytes with the external pin. `tool_sha256` is only recorded |
| B-6 | No code emits or durably hands over the binding block and result; no process exit mapping for `PassAResult` |
| B-7 | Expected output values and A1-Z equality are not evaluated; `exit_policy` receives no stdout or stderr, so A1-19 and A1-Z-19 cannot tell `ENOENT` from another failure, and no pinned, evidenced `ENOENT` form exists in the material read (M-2) |
| B-8 | No capture unit fragment. The launcher and entry install path is not complete; no SA-2 artifact is installed; sandbox, `TimeoutStartSec` and real launcher-to-entry InvocationID pairing are unproven |
| B-9 | The activation prerequisites of D-5 are not prepared or verified for this pass |
| B-10 | No window enforcement and no pre-start check implementation (§4.3) |
| B-11 | A0-03 binds the old file (M-1) |
| B-12 | No exact clean candidate commit; no A-1, A-2, A-5, AUTH grant or execution authority |

## 11. What review of this candidate would not do

It would not accept any command for execution, close G10, satisfy A-1 (which
needs exact final bytes and a clean commit), change A-6's scope, satisfy RP-10,
or authorize acquisition, build, install, service action, `run_pass_a`, or any
host access.

## 12. Drafting method and verification

Repository reading, `git log`/`diff`, and `sha256sum` of tracked files only. No
host was contacted; no test, suite, dry run, build or operational command was
run; no secret file was read. Statements about hosts, suite results, G6 digests
and provisioned objects are taken from the cited records and were not
re-observed. The act counts come from reading the plan source and match its
test's stated 49; the test was not executed.

## 13. Independent review — 2026-11-27

Codex reviewed the candidate against the v39 plan, entry and dated G6/G9
records. The candidate is ready for owner review of the policy choices in §9.
A-1 remains pending on the final contract and implementation.

Claude resolved two review findings: A-2 now references the separately
authorized prior acquisition, and the two run-root checks require evidence
of absence rather than accepting exit 1 alone. Codex independently derived
49 acts (45 labelled AUTH-READ, four labelled AUTH-DBREAD), a five-second
drain and a 2,548-second bound from the inert plan. Six targeted plan tests
passed. These checks executed no Pass A acts.

The next decision is whether to adopt the single-host authorization model
and retain in-pass stop-on-mismatch. Those choices determine the entry and
evidence checks to implement before exact-byte A-1 review. The written
grant and its machine representation also need an explicit binding decision.

## 14. Owner policy decisions — 2026-11-28

Peter approved Codex's recommendations on 2026-11-28. Recorded by Claude from the
instruction that relayed the approval. This is **policy only**: it is not A-1,
A-2, A-5, an AUTH grant, acquisition authority or execution authority, and every
AUTH row stays ungranted. §14 changes the candidate's bytes, so the 2026-11-27
review in §13 does not cover them.

| ID | Decision | Implementation details still undecided |
|---|---|---|
| D-1 | Material expected results are enforced **in the pass**, fail closed. During development a mismatch leads to Claude remediation and Codex re-review without stopping for approval. In an actual pass a mismatch stops the pass and preserves the evidence; no retry | see §14.1 |
| D-2 | Retire AUTH-SYNC, and AUTH-DBREAD for Pass A. The four cluster host-status reads (A1-29, A1-30, A1-Z-29, A1-Z-30) move to AUTH-READ. AUTH-ACQUIRE is a separate authorization. AUTH-READ is therefore A0: 6 acts, A1: 43 acts | `pass_a_plan.py` still labels the four acts `AUTH-DBREAD`; changing it moves the manifest. Grant representation and enforcement (B-4) |
| D-3 | A named actor acquires one exact commit under a separate grant for that commit | actor, account and grant record format |
| D-4 | Omitted observations and gaps are documented. `chattr` or `laboratory/runs` is restored only if required and possible without wider privileges. The A0-06 suite evidence is bound to the exact commit | see §14.2; the form of the commit-bound suite record |
| D-5 | The machine A-2 is bound to the written grant by digest, with matching operator, scope, window and pins. The existing consume guard prerequisites stay. The machine file is never a substitute grant | schema change to `rp11-a2/3` or a companion record; where the match is checked |
| D-6 | A record-only successor commit is allowed. The implementation digest and the decision digests are distinct | how "record-only" is verified; digest field names |
| D-7 | SIGTERM is an interruption: evidence is preserved and no X-3 is attempted | reconciling entry-contract proposal §5 item 5; test under the real unit |
| D-8 | The named operator holds a separate execution authority | its record format |
| D-9 | Reading the retained root needs a named, read-only evidence grant with a named mechanism | reader, mechanism, extent |
| D-10 | The stopped or completed root is retained. Any new attempt needs a separately authorized, distinct root; **never `capture-b`** | the later root's name; the plan fixes `capture-a` and would need a reviewed change |

### 14.1 D-1 precursor (review only, not wired)

`tools/rp11_pass_a_expectations.py` with
`tests/test_rp11_pass_a_expectations.py`. It is pure, judges admitted records and
stream bytes, and covers the pin, identity, exit, absence and A1-Z comparisons of
§6.1 for the 49-act default plan. It is outside the covered manifest and the SA-2
tree; no existing covered source or pin changed. **B-7 is not closed**, and
M-2 is not closed: nothing calls it.

Open before integration:

* No reviewed, pinned `ENOENT` form exists. It is a required input that may be
  `None`, and then A1-19 stops the pass. The form must be evidenced from the
  target's `stat` under the plan's argv and environment. The grammar a supplied
  form must fit is synthetic and may need a reviewed change to match it.
* `CaptureRecord` has no per-record `InvocationID`. Integration must take the
  admitted digest from the current invocation's chain, and the planned argv from
  the reviewed, pinned plan.
* Every expected value is a required input. Where each comes from (reviewed
  config, bound by which digest) is B-3.
* Output formats of the other gates are the draft's expectations read against the
  planned argv. They are tested only on synthetic text and have not been compared
  with admitted records from the target. A wrong format stops; it cannot pass.
* A1-09, A1-10, A1-17, A1-18 and A1-25 … A1-28 are recorded, not compared. The
  M-5 expected process and service set is not defined.
* `pass_a.ExitPolicy` receives no streams. Integration needs a reviewed way to
  read the admitted act's record and stream bytes, a distinct stop reason, the
  manifest membership change, `ENTRY_SOURCES`, and new reference builds.
* The X-3 / X-4 result is not part of the evaluation.

### 14.2 D-4 omitted observations and gaps

| Observation | Disposition | Gap that remains |
|---|---|---|
| `/usr/bin/chattr` (A1-16, M-3) | **not restored**: `plan.RETIRED_EXECUTABLES` retires it and no harness step may name it, so Pass A does not require it | its owner and mode are not observed |
| `laboratory/runs` (V9, A1-21, M-4) | **not restored**: its parent is expected `root:freedomlab 0750` and `capture` has no supplementary group, so by those modes the `stat` would be refused. This is an inference, not observed | V9's owner, mode and existence are unknown to Pass A |
| A0-06 classifier tests | withdrawn from the pass; replaced by suite evidence that names the exact pinned commit | no such record exists, because no candidate commit exists |
| A1-14, A1-15 | withdrawn (`sudo`); A1-C also `not_run` | no launched-process status or bounding set |
| A1-22 | withdrawn | V7 `lifecycle.json` absence not established |
| A1-31 … A1-33 | withdrawn (`sudo`) | no database or role absence, no `pg_hba` / `pg_ident` baseline |
| Checkout, parent, root, `capture` account (M-5) | not surveyed by the plan | covered only by the separately authorized pre-start checks |

A Pass B prerequisite that needs one of these cannot be met from this Pass A
(M-7).

### 14.3 Implementation slice — 2026-11-28 (reviewed; amends §14.1)

Codex independently reviewed the source and observed 5,009 passing checks
across three local selections. The [handback](rp11-d1-seam-d2-handback.md)
records exact results and current v40 review digests.

* **D-2 (plan labels):** the four cluster host-status acts are `AUTH-READ` in
  `pass_a_plan.py`; A0 has 6 acts and A1 43. Nothing enforces the label (B-4 open).
* **D-1 (continuation):** `run_pass_a` takes an optional `continuation`, default
  none, which nothing supplies. After an accepted exit, the open session re-reads
  the latest admitted act through its held descriptors and checks identity, size
  and digest; the continuation must then return exactly `True` or the pass stops
  before the next act, including after the last. This closes the byte-supply item
  of §14.1 (*"a reviewed way to read the admitted act's record and stream bytes"*,
  *"bind the admitted digest to the current chain"*) **at the repository level
  only**. B-7 and M-2 stay open: the evaluator is still outside the manifest and the
  SA-2 tree, the `ENOENT` form and the expected values (B-3) are still absent.
* **Manifest v40:** the deterministic generation and downstream pins passed.
  The v40 aggregate is `2e6d5a1da67007c541728e01aeaa62097c9b5eddb5c1008d912ee6c4cfb7babd`.
  The G6 values in §§2–3 bind the earlier reference build and the carry-over
  inference only covers v39. A-6 is unchanged (`journal.py` `83a3dc77…6b0d`).
  The v40 source candidate uses the review digests in the handback. The final
  contract and clean commit for a pass remain unresolved.
