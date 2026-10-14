# LIT-FULL WP-3 contract integration — handback

Work ID `C-P5.0-R5-RP11-H1-OH-S3-RT3-WP3-CI1-20261012-26` · executor Claude · independent
reviewer after return Codex · decision owner Peter Duscha · UTC date 2026-10-12 (execution
started 07:55:36Z; the contract, snapshots and pointers were written between 07:56Z and 08:07Z;
this handback followed)

**Terminal state: `PASS`.** Normal return state:

**WP-3 CONTRACT INTEGRATION RETURNED — INDEPENDENT CODEX REVIEW PENDING**

`PASS` means the two deliverables, the four return snapshots, the four archive rows and the four
pointer updates are complete and consistent. It does **not** accept the integrated contract and
does **not** authorize WP-4. The accepted WP-3 `HARD STOP` remains in force until independent
Codex review and Peter's later gate decision replace it. Only D-1 … D-6, D-9 and D-10 are
decided; D-7, D-8 and D-11 … D-14 are not; Q6-6 and Q6-7 are not answered; no Q3 question is
closed.

Deliverables: the cumulatively corrected
[interface contract](phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-interface-contract.md) and this
handback. Authority: the
[accepted prompt](phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-contract-integration-claude-prompt.md)
and its
[acceptance and activation](project-review-2026-10-12-p5-r5-rp11-h1-oh-s3-lit-full-wp3-contract-integration-acceptance-and-claude-activation.md).

## 1. Pre-edit reading ledger

**All required reading was completed before the first deliverable edit.** "Completely" was read
as first byte to end of file in this execution; no prior read, search result, excerpt, synopsis
or memory was relied on. The identities below were taken from the working tree before the first
edit (line, byte and SHA-256 are of the whole file even where only named portions were required).
The first deliverable edit (installing the corrected contract) followed the reading, the identity
checks and the creation of the four snapshots. The prompt's two fixed identities were checked
before any integration work and match exactly.

| # | Item | Lines | Bytes | SHA-256 | Portion read |
|---:|---|---:|---:|---|---|
| 1 | `.agents/AGENTS.md` | 700 | 36,014 | `87bab4ab8d67e308af0c59b99c8604235ee84d75cfa12448458b1a04cc88390a` | completely (1–700) |
| 2 | `docs/implementation-plan.md` (pre-edit) | 2,600 | 127,942 | `1a50bdb89b83127318e238582bf50b962dfa150e18d8f419c2c972b2eea0e877` | reading map and §0 (1–184); §3 (267–288); §5 (353–408); §12.0 (1190–1212); the complete section headed `Phase 5 — Existing automation migration` (1634–1926, heading to the line before `### Phase 6`); §13 (2112–2216); §16 (2395–2492); §17 (2493–2513); §20 (2559–2600, to end of file) |
| 3 | `docs/review/Handover information` (pre-edit) | 30 | 2,001 | `31c771509eba112f9307de02561862a1283bc1d5dcd8a58aebc0f5b7d9eaecba` | completely |
| 4 | `docs/operations/disposable-test-server.md` (pre-edit) | 323 | 15,283 | `c9d8d636cc51158a02c8d527af880b96a44518cd3c2425b1391a84832ac006a4` | the active restriction banner (lines 1–35; 2,519 bytes; `6f77e3b675dfe87251f4c7691a0b07e9395efdf26e86fea547c0c9be9a6f3402`) and the lines that follow it through line 80 |
| 5 | `phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-interface-contract.md` (pre-integration) | 469 | 50,599 | `b766c10f2c28ac2d32a7dc7ee4ab2c92a3cf80d67fd70f345a9f0dd7ba92c888` | completely |
| 6 | `…-wp3-source-completion-record.md` | 1,758 | 240,533 | `4c2a1b76a72002de77ca885ba248f086c302b5e9aebebd117cfa90b8989a1049` | completely (1–1758, read in eight consecutive ranges) |
| 7 | `…-wp3-source-completion-r2-remediation-handback.md` | 234 | 25,781 | `263cd8d638d233a82240052629be521a1eb0d000149d248c25d71ceb33f5a873` | completely |
| 8 | `project-review-2026-10-11-…-source-completion-r2-remediation.md` | 56 | 2,572 | `9d7f6c6aff0fcf4478ecf715820801357a8a6ad8a7c6b5f15d376e5581b791d5` | completely |
| 9 | `project-review-2026-10-11-…-source-completion-r2-remediation-acceptance.md` | 43 | 2,844 | `2be83d66fda0779315e5f8b4be51c637154f6dc45301fff1b7519e1d9cbe7024` | completely |
| 10 | `project-review-2026-10-11-…-source-completion-evidence-acceptance-and-contract-integration-direction.md` | 57 | 3,093 | `a7af48d1b6ee3a500d33d96e87944e26ac2a031d936bf930a7c149318778da0c` | completely |
| 11 | `…-wp3-contract-integration-claude-prompt.md` | 358 | 18,188 | `894470357ed0fa1ed6c0fba251c471a9e549b7412068b1c1009984580ea91fce` | completely |
| 12 | `project-review-2026-10-12-…-contract-integration-acceptance-and-claude-activation.md` | 74 | 3,795 | `19eff0574a49e5f7364b3f4e2c1268cb22dc10b317f327a4c94638d2c7ca91fa` | completely |

Preconditions: the activation record exists, identifies the prompt by 358 lines, 18,188 bytes and
SHA-256 `894470357ed0fa1ed6c0fba251c471a9e549b7412068b1c1009984580ea91fce`, adopts D-1 … D-6, D-9
and D-10 and appoints Claude — and the prompt's own `wc`/`sha256sum` equals those values. The
source-completion record equals its fixed identity (1,758 / 240,533 / `4c2a1b76…1049`); the
pre-integration contract equals its fixed identity (469 / 50,599 / `b766c10f…c888`). **No identity
mismatch; no `HARD STOP` precondition fired.**

Read-only repository searches **outside** the required list, made to test one request-shape
question before writing (they are not substitutes for required reading): a case-insensitive
search of the WP-2 operation inventory and of the one-host design record for `job-mode` /
`job_mode` / `--job` (0 matches in each), and a `sed` print of inventory lines 457, 531, 583 and
595 (rows `RT2.AK1.2`, `RT4.BS2.2`, `SA1.OP.2`, `SA2.OP.2`). Read-only `git show HEAD:<contract>`
supplied the unchanged pre-integration contract text for mechanical copying; its SHA-256 equals
row 5.

## 2. Contract identity

| | Lines | Bytes | SHA-256 |
|---|---:|---:|---|
| Pre-integration (R1 revision, unchanged in Git `HEAD`) | 469 | 50,599 | `b766c10f2c28ac2d32a7dc7ee4ab2c92a3cf80d67fd70f345a9f0dd7ba92c888` |
| **Post-integration** | **1,450** | **120,552** | **`dacf9f23d2027a7c9a6ac9555e787ab9c3b084903893972314d0b964590b744d`** |

**This handback** does not hash itself (the established self-identity convention): its line
count, byte count and SHA-256 are given in the chat return, taken after it was last edited.

## 3. D-1 … D-14 disposition

| Id | Disposition in this run | Where recorded | Class |
|---|---|---|---|
| D-1 | **Recorded as adopted** — system message bus for DI-1 … DI-5 and DI-S; no private manager socket; installed broker/version/policy is residual R-01.1, not an assumed fact | contract §3.0.1, §11.2 | `DEC` |
| D-2 | **Recorded as adopted** — P-10.1 shape S-A (`unix-process {pid u, start-time t, uid i}`, `manage-units`, details exactly `unit`+`verb`, flags 0, empty cancellation id) | §3.5, §11.2 | `DEC` |
| D-3 | **Recorded as adopted** — P-04.1 with only the defined refusal cases; every other outcome `error(kind)`, mutating interfaces `effect not confirmed`, no silent retry | §3.0.2, §11.2 | `DEC` |
| D-4 | **Recorded as adopted** — O-C: match + `Subscribe()` first, accept `JobRemoved` for the returned path and expected unit, post-completion state read is observation only | §3.0.3, §11.2 | `DEC` |
| D-5 | **Recorded as adopted** — PID/start-time/uid subject, not pidfd; A-13.4 preserved prominently as a Route 3 readiness risk to be carried to WP-4 | §3.6, §11.2 | `DEC` |
| D-6 | **Recorded as adopted** — P-11.1 mapping `(true,false)` authorized, `(false,*)` not-authorized, `(true,true)` `error(invalid-reply)` | §3.5, §11.2 | `DEC` |
| D-7 | **Not decided** — stays with Q3-9 / Q6-2 | §3.8, §11.3 | — |
| D-8 | **Not decided** — stays with Q6-6; D-3's `effect not confirmed` is not a Q6-6 answer | §3.0.5, §11.3 | — |
| D-9 | **Recorded as adopted** — `ok(already-stopped)` for loaded inactive/failed + `JobRemoved … done`; `refused(not-loaded)` for `NoSuchUnit`; DI-4 and DI-S | §3.4, §3.7, §11.2 | `DEC` |
| D-10 | **Recorded as adopted** — the DI-3 backstop service has no `TimeoutStartUSec`; resolves only the D R2 (f) literal for this contract | §3.3, §11.2 | `DEC` |
| D-11 | **Not decided** (Q3-11) | §3.9, §11.3 | — |
| D-12 | **Not decided** (Q3-11, Q6-3) | §3.9, §11.3 | — |
| D-13 | **Not decided** (Q3-11) | §3.9, §11.3 | — |
| D-14 | **Not decided** (Q3-11) | §3.9, §11.3 | — |

## 4. Section-level change ledger

The complete 43-row ledger, with old and new locations and the verbatim former `HARD STOP`
wording, is contract §12. Summary by new section:

| New section | Relation to the R1 revision |
|---|---|
| Title, header, terminal summary | replaced (former `HARD STOP` wording quoted in §12.2) |
| §1 scope, hierarchy, classes, version boundary | updated; adds Peter's decisions, the source record (fixed identity) and the classes `ASF`, `DEC`, `PSC`, `IO` |
| §2 roster and 41-site mapping | **unchanged** (mechanically copied) |
| §3 intro, §3.0.1 – §3.0.5 | replaced the "common supported facts" and §3.0; transport (D-1), result discipline (D-3), completion (D-4), cancellation, `effect not confirmed` boundary |
| §3.1 – §3.7 | each DI section rewritten to the request/response/encoding/completion/cancellation/failure form, with source-record identifiers |
| §3.8, §3.9 | updated; Q3-9 open, Q3-11 fail-closed retained |
| §4.1 | C-01 … C-34 retained; C-23 amended; C-33/C-34 "used in" re-pointed |
| §4.2 | new: every source-record identifier relied on |
| §5 | replaced; before/after Q3 table |
| §6 | replaced the `UF` registry: §6.1 disposition, §6.2 residual and observation register, §6.3 `IO-1` … `IO-4` |
| §7 | replaced; WP-4 input table |
| §8, §8.1 | updated; §8.2 **unchanged** |
| §9, §10 | updated; stop-rule result replaced by the integration result |
| §11 | new: decision register D-1 … D-14 |
| §12, §13 | new: change register; return state |

## 5. Q3 closure and readiness — before and after

| Q3 | Before (R1 contract) | **After integration** | Open items kept visible |
|---|---|---|---|
| Q3-1 | Not closed (UF-01, 02, 03, 04) | **Closure-ready** (D-1, D-3, D-4(3)) | D-7 (Q3-9/Q6-2); Q4-7; R-01.1, R-03.1 |
| Q3-2 | Not closed (UF-01, 04, 05, 06, 07) | **Closure-ready** (D-1, D-3, D-4) | D-8/Q6-6; Q4-7; IO-2, IO-3, IO-4 |
| Q3-3 | Not closed (UF-01, 04, 05, 06, 07, 08) | **Closure-ready** (D-1, D-3, D-4, D-10) | Q6-6; Q4-7; BS-RM / OH-S2b |
| Q3-4 | Not closed (UF-01, 04, 05, 09) | **Closure-ready** (D-1, D-3, D-4, D-9) | Q6-6 (BS-2, BS-3); **Q6-7 (BS-4)**; IO-1, IO-2 |
| Q3-5 | Not closed (UF-01, 04, 10, 11) | **Closure-ready** (D-1, D-2, D-3, D-6) | Q4-7; R-10.1; R-11.1 |
| Q3-6 | Not closed (UF-10, 12, 13) | **Closure-ready** (D-2, D-5) | **A-13.4**; Q4-1, Q4-8; Q6-4; R-M.1 |
| Q3-7 | Not closed (UF-01, 04, 05, 09) | **Closure-ready** (D-1, D-3, D-4, D-9) | Q6-6 (is DI-S inside SN-10?); IO-1, IO-2 |
| Q3-9 | Not closed (UF-03, UF-14) | **Open — not closure-ready** | R-03.1; D-7; Q6-2 |
| Q3-11 | Closed as fail-closed record (`PO3-11.1`) | **Fail-closed record retained**; no mechanism adopted | D-11 … D-14; Q6-3 |

**No Q3 question is closed.** "Closure-ready" is the source record §6 sense (all facts supported;
only adopted decisions remain) and is not an acceptance.

## 6. Retained residual and open-question register

* **Residuals preserved with their exact statements and owners** (contract §6.2): R-01.1, R-01.2,
  R-02.1, R-03.1, R-03.2, R-04.1, R-04.2, R-05.1, R-05.2, R-05.3, R-06.1, R-06.2, R-07.1 …
  R-07.3, R-08.1 (resolved for the LIT-FULL DI-3 contract only, by D-10), R-09.1, R-09.2, R-10.1,
  R-10.2, R-11.1, R-12.1, R-12.2, R-13.1, R-13.2, R-13.3, R-14.1, R-15.1, R-15.2, R-16.1, R-16.2,
  R-17.1 … R-17.3, R-18.1, R-18.2 and **R-M.1** (carried unchanged; limited provenance basis;
  not archive-chain authentication; stated at the contract header, §3.6, §3.9, §6.2).
* **Observations O-1 … O-6 and the two accepted-record editorial observations** (O-1 and O-4 /
  R-14.1) preserved; no erratum written.
* **Fully open decisions:** D-7, D-8, D-11, D-12, D-13, D-14. **Unanswered:** Q6-6, Q6-7.
  **Later-package inputs, not decided:** Q4-1, Q4-5, Q4-7, Q4-8, Q4-11, Q6-2, Q6-3, Q6-4, BC-2
  (WP-9), the BS-RM citation obligation (OH-S2b).
* **Integration observations disclosed, not filled** (contract §6.3):
  **IO-1** — the evidence does not say how `already-stopped` is discriminated from an active
  stop when both end `JobRemoved … done`; **IO-2** — no accepted record or adopted decision
  selects the job-mode string for `StartTransientUnit` or `StopUnit` (the reference client's
  `fail` for `systemd-run` is tier `R`; no default is recorded for `systemctl stop`; the accepted
  literals pass no `--job-mode`); **IO-3** — D-3 names `UnitExists` for DI-2 only (DI-3 therefore
  maps it to `error(kind)`), and "InvalidArgs before mutation" is evidenced for the mode check
  and, via the proposal P-05.2, for the name/type check, while property-walk errors come after
  the unit is made transient; **IO-4** — D-4 is silent on a failure of the match or `Subscribe()`
  before the mutating call (D-3's catch-all applies).

## 7. Files created, changed and unchanged

**Created (5):**

| File | Lines | Bytes | SHA-256 |
|---|---:|---:|---|
| `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-contract-integration-handback.md` | this file | | not self-referential (chat return) |
| `docs/review/Handover-information-through-2026-10-12-lit-full-wp3-contract-integration-authorization.md` | 30 | 2,001 | `31c771509eba112f9307de02561862a1283bc1d5dcd8a58aebc0f5b7d9eaecba` |
| `docs/project-management/status-through-2026-10-12-lit-full-wp3-contract-integration-authorization.md` | 39 | 2,371 | `0d22020969293f216006c4481bbcacb4f527d5d01d7592969714852e51fe7799` |
| `docs/implementation-plan-through-2026-10-12-lit-full-wp3-contract-integration-authorization.md` (§20, heading to EOF) | 42 | 2,718 | `6c15653fd1d61b8aa7aed91aef23d536a7cc6d7b992a9d9238d7e33cb6c96f98` |
| `docs/operations/disposable-test-server-through-2026-10-12-lit-full-wp3-contract-integration-authorization.md` (banner lines 1–35) | 35 | 2,519 | `6f77e3b675dfe87251f4c7691a0b07e9395efdf26e86fea547c0c9be9a6f3402` |

Each snapshot was confirmed byte-identical
to the pre-return canonical content it preserves (`cmp` for the two whole-file snapshots; `sed`
line ranges compared with `cmp` for the other two), **before** any pointer or contract edit.
Never overwritten. The plan and disposable-server documents were also checked in reverse: the
snapshot concatenated with the unchanged remainder reproduces the recorded pre-edit SHA-256
exactly (`1a50bdb89b83127318e238582bf50b962dfa150e18d8f419c2c972b2eea0e877` and
`c9d8d636cc51158a02c8d527af880b96a44518cd3c2425b1391a84832ac006a4`), proving that only the intended block changed.

**Changed (9):**

| File | Change | Lines | Bytes | SHA-256 (post) |
|---|---|---:|---:|---|
| `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-interface-contract.md` | cumulative in-place correction (§2) | 1,450 | 120,552 | `dacf9f23d2027a7c9a6ac9555e787ab9c3b084903893972314d0b964590b744d` |
| `docs/review/Handover information` | pointer reconciled | 39 | 2,600 | `67968c49b66f47a32c04a8faa7988d27439e44e76f4e82460947462108007d9a` |
| `docs/project-management/status.md` | pointer reconciled | 48 | 2,980 | `bb5a1176d4f4c62b19a912cf38917adccbbf135495fd4c4cb64db7c6cb190c3d` |
| `docs/implementation-plan.md` | §20 current-state block and links only | 2,609 | 128,550 | `a407887526bb34cb96c102db6cb86b02228ce2a787dacca2043964777dc603ea` |
| `docs/operations/disposable-test-server.md` | banner lines 1–35 only | 329 | 15,648 | `3ffb1f55fe541bb2566cee03e6cb7860c70e725703291b8046de8f2a083a908d` |
| `docs/review/handover-archive/README.md` | one row added | 88 | 27,197 | `b08aceac93fe05c4e17d689a90d71584258a7180556f9697c41397b3d75279a7` |
| `docs/project-management/status-archive/README.md` | one row added | 87 | 24,672 | `ea87c868955b2a89ce233c57cc329019a5179ad3105be3f3280aae76506511e5` |
| `docs/implementation-plan-archive/README.md` | one row added | 74 | 23,862 | `8d23ade87e0ee27ad8d4d0562402c1e212d58123a565f1b942c5c22ab4de23f7` |
| `docs/operations/disposable-test-server-archive/README.md` | one row added | 75 | 24,293 | `9eed2447f1951ba1283d325d630e504e26066ba5fca4f2001ac0ec9abc2b5399` |

The four new archive rows carry the SHA-256 of the corresponding snapshot (table above). All four
pointers link this handback and agree on the exact normal return state, preserve the boundary and
the prohibitions, and state that the accepted WP-3 `HARD STOP` remains in force.

**All other paths stayed unchanged.** A `git status --short` taken before the first edit and one
taken at the end differ by exactly one added modified path (the contract) and five added
untracked paths (four snapshots, this handback). Every other file — including the other review
records, prompts, handbacks and earlier snapshots that were already modified or untracked at the
start — was not touched. The eight tracked files that were already modified before this run
(four pointers, four archive indexes) were changed only as listed above. No historical prompt, handback, review,
acceptance or snapshot was rewritten. R5 and H-0G retained paths untouched.

## 8. Checks performed and exact results

Repository-static checks only:

| Check | Result |
|---|---|
| `wc -l -c` and `sha256sum` of all twelve required items before the first edit | recorded in §1; the prompt, the source record and the pre-integration contract equal their fixed identities |
| Same for every deliverable, snapshot, pointer and archive index after the edits | recorded in §2 and §7 |
| Snapshot byte identity (`cmp`) and reverse reconstruction of the plan and the disposable-server document | all four `cmp` identical; both reconstructed SHA-256 values equal the recorded pre-edit values |
| Markdown table shape, whole contract | 22 tables, 0 irregular rows (every row has the header's column count, escaped pipes honoured) |
| Trailing whitespace / tab characters in the contract | 0 |
| Citation-identifier comparison against the accepted source-completion record | 183 distinct identifiers (`A-nn.n`, `P-nn.n`, `R-nn.n`, `R-M.1`, `O-n`) in the contract; **0 unresolved** against the record; **0 record identifiers uncited** |
| Exact searches in the contract: `D-1` … `D-14` | all fourteen present (counts 44, 17, 70, 42, 14, 24, 21, 14, 32, 22, 15, 6, 6, 19); every line mentioning D-7, D-8 or D-11 … D-14 with "adopt" says none adopted or undecided |
| Exact searches in the contract: `Q3-1` … `Q3-7`, `Q3-9`, `Q3-11` | all present (68, 11, 11, 18, 31, 33, 25, 39, 40) |
| Exact searches in the contract | `Q6-6` 42, `Q6-7` 26, `UF-` 91, `PSC` 26, `HARD STOP` 17 (all in the header statement of the accepted stop, §10, §12 and its verbatim quotation), `TimeoutStart` 11, `pidfd` 14, `effect not confirmed` 16, `R-M.1` 17. No residual statement of the former `UF`-stop remains outside §12.2 (searches for "cannot be closed", "must be supplied", "conditional on", "expanded" find only the change-register descriptions of the old text) |
| Repository-relative link targets of the contract, the four pointers, the four archive indexes and this handback | see §9 (run after this file existed) |
| `git diff --check` | see §9 |
| `git status --short`, `git diff --stat` (read-only) | see §9 |

## 9. Final static checks (run after this handback was written)

| Check | Result |
|---|---|
| Repository-relative link targets (every `](path)` link, resolved from each file's directory) in the contract (4 links), this handback (3), `Handover information` (6), `status.md` (7), `implementation-plan.md` (16), `disposable-test-server.md` (8) and the four archive indexes (72, 71, 64, 63) | **0 broken** in all ten files |
| Markdown table shape: this handback; the four archive indexes | 8 tables / 0 irregular rows; 1 table each / 0 irregular rows |
| Trailing whitespace or tab characters: this handback, the four snapshots, the contract | none |
| `git diff --check` | clean (no output, exit 0) for the tracked files; the untracked files were covered by the whitespace scan above |
| `git status --short` (read-only) | 26 entries. Against the entry list taken before the first edit it differs by exactly one added ` M` path (the contract) and five added `??` paths (the four snapshots and this handback) |
| `git diff --stat` (read-only, against `HEAD`) | 9 tracked files; 1,394 insertions, 360 deletions in total. The total includes the working-tree changes that existed before this run (they are not separable by `--stat`); this run changed the contract, the four pointers and the four archive indexes (one row each) |

## 10. Checks deliberately not performed

* No test, build, formatter, linter, type checker, hook or application code was run, including
  `python3 .claude/hooks/test_guards.py` and the `run-suites` procedure. **No suite figure is
  claimed.** This assignment changes documentation only.
* No network access, SSH, `oracle-test`, production, staging, Foundry, database or
  retained-evidence access; no secret or credential file read; no host-installation, package,
  `/etc`, `/proc` or `/sys` inspection; no source retrieval.
* **The primary sources were not re-read or re-verified.** The source record's `ASF`/`MD` rows
  were integrated on the strength of its acceptance, not independently re-derived; the Ubuntu
  archive chain, the kernel delta and every `A-` citation were not re-checked, and `R-M.1` is
  not resolved.
* The `SF`/`DR` citations C-01 … C-34 of the R1 contract were retained; they were **not**
  re-verified in this run against R2, R8, D or the WP-2 inventory, which are not on the required
  reading list. Only the four inventory rows and the two `job-mode` searches in §1 touched those
  records.
* No semantic review of the whole contract by an independent party; that is Codex's step.

## 11. Prohibited operations — confirmation

No prohibited operation occurred. In particular: no network; no SSH or `oracle-test`; no
production, staging, Foundry, database or retained-evidence access; no secrets or credentials; no
host-installation, package, `/etc`, `/proc` or `/sys` inspection; no application, configuration,
infrastructure or launcher edit; no source retrieval; no implementation; no package installation;
no service or database operation; no test, build, formatter or hook; no cleanup outside files
created by this assignment; no activation or rollback; **no commit and no push**; the R5 and H-0G
retained paths were not touched; no later work package (WP-4 … WP-7) was prepared; no
history-rewriting or default-branch Git action. Working files for assembling and checking the
contract were kept in the session scratchpad directory outside the repository; they are not
deliverables and were not deleted. Read-only Git inspection (`git status`, `git diff --stat`,
`git diff --check`, `git show HEAD:<contract>`) was used. The invocation was the exact text of the
activation record.

## 12. Proposed reviewer focus for Codex

1. Does every adopted decision appear exactly as fixed in the prompt (D-1 … D-6, D-9, D-10), with
   no substitution or expansion, and are D-7, D-8, D-11 … D-14 untouched?
2. Are `ASF`, `PSC`, `MD`, residual and observation classifications preserved — in particular,
   is no `PSC` or unavailable mechanism now described as a source fact?
3. Are Q3-1 … Q3-7 "closure-ready" supportable given **IO-1 … IO-4**, and given that Q3-1 carries
   R-03.1 and R-01.1 as visible residuals? Is any IO a missing WP-3 interface fact rather than a
   WP-4 parameter?
4. Is `refused(invalid-request)` for the name/type `InvalidArgs` of `StartTransientUnit`
   (IO-3(b)) supported by the source order, and is the DI-3 `UnitExists` → `error(kind)`
   reading (IO-3(a)) the right reading of D-3?
5. Is the word "closure-ready" kept clearly distinct from "closed" and from acceptance everywhere,
   and does the header keep the accepted `HARD STOP` in force until the gate decision?
6. Is `R-M.1` visible wherever A-12.3 or A-15.2 is integrated and never described as
   archive-chain authentication? Is A-13.4 prominent in §3.6 and §11.2?
7. Do the four pointers, the four snapshots and the four archive rows agree with the return
   state and with each other?

## 13. Current state

**WP-3 CONTRACT INTEGRATION RETURNED — INDEPENDENT CODEX REVIEW PENDING.**
No agent may treat this return as acceptance or as authority for WP-4.
