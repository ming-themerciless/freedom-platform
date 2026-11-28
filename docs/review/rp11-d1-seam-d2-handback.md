# RP-11 D-1 continuation seam and D-2 labels — handback for Codex review

**Date:** 2026-11-28 · **Implementer:** Claude · **State:** implemented, **not run**,
awaiting Codex tests and manifest regeneration. Nothing is wired. Manifest **v40**
bytes are not generated yet.

## Structural-guard remediation — 2026-11-28 (latest)

**Codex's focused run of the review-remediated version: 1237 passed, 2 failed.**
Both failures were the unchanged guard
`test_no_module_looks_a_symbol_up_by_name`, which rejected `getattr` in
`execution/capture_store.py` and `execution/pass_a.py`. The guard was not edited.

Source changed after that run, and **these bytes have not been run**:

* `capture_store.py`: the post-read comparison uses a new `_unchanged_metadata`
  tuple naming the same eight fields explicitly; access time stays excluded.
* `pass_a.py`: `continuation.covers` and `.permits` are accessed directly. A missing
  attribute is still `malformed-continuation`; the other conditions and the default
  `None` are unchanged, and an error raised inside `covers` still propagates. One
  nuance: both attributes are now looked up before either is tested for callability.

The 1237/2 figure does not describe the current bytes. No pin or generated artifact
was edited; Codex generates them from these final sources.

## Codex review remediation — 2026-11-28 (supersedes the text below where they differ)

**State: edited, checked by reading only, NOT run.** Codex's run of **749 passed**
was of the version **before** this review and says nothing about the current bytes.
No figure is claimed for the corrected version. In this session the pytest run was
refused for lack of approval; the manifest generator was therefore not attempted.
No digest or pin was written or changed.

**Finding 1 — a swapped directory was accepted.** Now refused.

* `CaptureRootStore` keeps the ancestor identities seen at X-1 and the identity of
  the root and each fixed subdirectory. No extra filesystem call is made at X-1.
* New `verify_bindings`: walks from `/`, `lstat`s each component no-follow relative
  to the proven descriptor, and opens an ancestor only after its entry matched
  (then `fstat`s it). The root and subdirectories are `lstat`ed, never opened, and
  must be directories with the bound identity, mode `0700` and the owner. Nothing
  is listed. Ancestors are bound by identity and type only, not mode.
* `admitted_evidence` runs it before the first retained open (`D1:bind-before`) and
  after the last read (`D1:bind-after`). The new
  `verify_evidence_bindings` (`D1:bind-judged`) runs after the continuation permits,
  so a swap during judgement stops before the next act (`evidence-unverified`).
* `read_stream` now compares, after the read, both `fstat` and a no-follow `lstat`
  of the exact name with the `fstat` taken before it (device, inode, mode, owner,
  link count, size, mtime, ctime).
* The old test `test_a_swapped_stream_directory_is_not_read`, which asserted
  acceptance, is replaced by refusals: replaced, symlinked, removed and re-moded
  bindings (ancestor, root, every subdirectory), changes to the stream during its
  read, directory replacement during the read and during judgement. All are driven
  by hooks, not threads.

**Finding 2 — no memory bound.** `MAX_EVIDENCE_STREAM_BYTES = 512 KiB` per stream
(1 MiB per act), equal to the plan's largest class bound (a test holds them equal).
An oversized record is refused with `evidence-oversized` before any filesystem
call of the read-back. Capture and the no-continuation path are not limited.

**Residual limits, for review.**

* The checks are point-in-time. A swap that is made and undone between two checks,
  or made after `D1:bind-judged`, is not seen by this seam.
* **X-4 is unchanged.** After a binding refusal the one stop transition still runs;
  X-3 writes through the held descriptors and the existing X-4 verifier then opens
  the capture root **by path**, read-only, and so may list a replacement tree. The
  "no replacement or unadmitted open" property above holds for the evidence
  read-back, not for X-4. Changing X-4 was not done.
* The without-continuation path makes no new calls.

The "swapped directory is not read" statement under D-1 item 1 and the "four `D1:`
stages" and test description below describe the earlier version. The v40 note in
`review_manifest.py` was extended; v40 was never generated, so the number stays.
`capture_store.py`, `capture_mechanism.py` and `pass_a.py` changed again, so any
digest derived from the earlier bytes is stale. Codex: run the commands below, then
generate. No host, build, grant, `run_pass_a`, commit or push occurred; there is
still no operational caller.

## Read this first

* **Claude executed no Python in this session.** The permission mode refused every
  pytest run and the manifest generator, and there is no approval surface. No test
  figure is claimed. Everything below was checked by reading only, except one
  `sha256sum` of `journal.py`.
* **The tree is deliberately inconsistent until the generator is run.** Five covered
  sources changed and `MANIFEST_VERSION` is now `40`, but the checked-in manifest
  JSON, concrete plan and every pin derived from them still say v39. The manifest
  and pin consistency tests will fail until the steps under "Commands for Codex".
  No hand-written digest or generated artifact was substituted.
* **This is not a pass pin and not an acceptance.** The v40 digests, once derived,
  are review input only. G6's `capture_tool_sha256` and SA-2 `tree_sha256` no longer
  describe this tree (below).

## D-2 — four host-status acts are AUTH-READ

`pass_a_plan.py`: A1-29, A1-30, A1-Z-29 and A1-Z-30 lost their `AUTH-DBREAD` label;
every step is now `AUTH-READ` (A0: 6 acts, A1: 43). The unused `auth` parameter of
the step helper is gone; the field stays a label and nothing enforces it (B-4 is
**not** closed). No argv, environment, class, timeout or exit changed. The docstring's
stale "version 38" now says 40.

## D-1 — the seam, and what it does

Opt-in and inert: nothing in the repository supplies a continuation. With none,
`run_pass_a` behaves as in v39 and issues no read-back (a test asserts the `D1:`
stages and `read` never occur).

1. **Trusted extraction.** `CaptureSession.admitted_evidence()` takes no argument,
   so no name, path or sequence comes from a caller. It requires an `OPEN` session
   and at least one admitted act, and covers only the **latest** admitted act. It
   re-verifies the admitting open state and the record under both names (inode,
   link count 2, owner, mode, size, bytes: the existing `_verify_name`), then reads
   each stream through the **directory descriptor held since X-1**, open no-follow,
   and requires the P-1 inode, link count 1, `0600`, owner, the record's size and
   SHA-256. Bytes returned are bytes digested. No path join, no symlink follow, no
   listing, no unadmitted name. A swapped directory is not read. A failure raises
   `StoreFailure` and leaves the session open for the one stop transition; an
   interruption marks it interrupted.
2. **Value.** `capture_contract.AdmittedEvidence` (pass id, `INVOCATION_ID`, seq,
   record, record digest, admitting state digest, stdout, stderr). A plain value;
   its provenance is its producer.
3. **Seam.** `pass_a.ActContinuation` (`covers`, `permits`) and
   `run_pass_a(..., continuation=None)`. `covers` must return exactly `True` for the
   exact plan **before any effect**, else `PassAPlanRefused("malformed-continuation")`,
   so a truncated plan cannot end `completed`. After an act whose exit the existing
   policy accepted, evidence is read back and `permits` must return exactly `True`;
   otherwise `session.stop` runs once, **before the next act and also after the last
   one**: `evidence-unverified` (read-back failed, the continuation is not called) or
   `continuation-refused`. The exit policy is judged first and is unchanged.
4. **Adapter.** `EvaluationContinuation` in `tools/rp11_pass_a_expectations.py`
   (still outside the manifest and the SA-2 tree) feeds `AdmittedEvidence` to
   `evaluate_act` in plan order, checks invocation id, pass id, sequence and planned
   argv, keeps first readings for the A1-Z comparison, is single-use, and permits
   nothing after a refusal. Nothing imports it from operational code.

## Tests (written, not run)

`tests/test_rp11_pass_a_continuation.py`, without importing or calling `run_pass_a`:
the seam goes through `pass_a._drive` and `_validated_plan` over capture sessions in
pytest temporary directories with a scripted launcher that starts no process. It
covers: AUTH labels; evidence bytes, digests, chain linkage; only admitted names
opened and no writes; refusal before an act and after the end; eight tamperings
(replace, symlink, same-size rewrite, append, mode, extra link, removal, FIFO) of each
of stdout, stderr, record and state; a swapped stream directory; a failure and an
interruption at each of the four `D1:` stages; refusal at each point and for any
non-`True` answer, including the last act; exit decided before the continuation;
evidence changed between admission and read-back; the five `covers` refusals; and by
syntax that `run_pass_a` forwards `continuation` to both steps. With the adapter: a
full 49-act synthetic pass established from read-back bytes, five material mismatches
that stop at their act with no later act, no reviewed `ENOENT` form, a wrong
invocation id, plan coverage and single use, stale evidence and refusal stickiness.
Edited existing tests: the parameter-set assertion in `test_rp11_pass_a.py` and the
version assertion in `test_r16_remediation.py`; `rp11_fixtures.FaultFilesystem` gained
`read`.

Not exercised, because it needs `run_pass_a`: the one-line forwarding itself (only
syntax-checked) and the generic handler when `permits` raises (the existing handler
for a raising exit policy is the same path).

## Covered-source change (manifest v40)

Changed: `capture_contract.py`, `execution/capture_store.py`,
`execution/capture_mechanism.py`, `execution/pass_a.py`, `execution/pass_a_plan.py`,
and `review_manifest.py` (version `40` and its note). Membership stays 66.

* The first three are `rp11-capture-tool/1` sources and the first four are in the
  SA-2 tree, so **G6's capture-tool and tree digests are superseded for this tree**.
  The candidate's §2 carry-over inference ("SA-2 input bytes unchanged") no longer
  holds. New non-installing reference builds are needed and are not authorized by
  this work; none ran.
* **A-6 carries forward unchanged.** `journal.py` is untouched (`83a3dc77…6b0d`
  confirmed). The v39 acceptance was for that classifier digest.
* Recorded as historical, not edited: the G6, G9 and earlier dated records.

## Commands for Codex

Focused, no database, none calls `run_pass_a` (the four tests in
`test_rp11_pass_a_plan.py` that do, and most of `test_rp11_pass_a.py`, are left out):

```text
env -u TEST_DATABASE_URL PYTHONDONTWRITEBYTECODE=1 \
  /opt/freedom-blades/platform/venv-web/bin/python -m pytest -q -rs -p no:cacheprovider \
  tests/test_rp11_pass_a_continuation.py tests/test_rp11_pass_a_expectations.py \
  tests/phase_5_0_evidence/test_rp11_capture.py tests/phase_5_0_evidence/test_rp11_retention.py \
  tests/phase_5_0_evidence/test_no_execution.py tests/web/test_p3_4_static_assets.py \
  tests/test_rp11_entry.py tests/test_rp11_entry_artifact.py tests/test_rp11_h1_artifact.py
env -u TEST_DATABASE_URL PYTHONDONTWRITEBYTECODE=1 \
  /opt/freedom-blades/platform/venv-web/bin/python -m pytest -q -rs -p no:cacheprovider \
  tests/test_rp11_pass_a.py -k "no_default or contains_no_operational or reaches_nothing or one_stop_transition or imports_only_modules or unknown_plan_refusal"
env -u TEST_DATABASE_URL PYTHONDONTWRITEBYTECODE=1 \
  /opt/freedom-blades/platform/venv-web/bin/python -m pytest -q -rs -p no:cacheprovider \
  tests/test_rp11_pass_a_plan.py -k "not (completes_with_one_finalization or failure_at_any_step or unexpected_status or outlives_its_class)"
```

Manifest regeneration (run to two scratch paths first and require identical bytes,
then to the final paths):

```text
cd /opt/freedom-blades/platform && /opt/freedom-blades/platform/venv-web/bin/python -B \
  -m tools.phase_5_0_evidence.execution.cli \
  --manifest-out docs/review/phase-5-0-evidence-harness-review-manifest.json \
  --render docs/review/phase-5-0-evidence-harness-concrete-plan.md
```

Then re-derive, from the bytes, every place that carries the v39 values (counted
by search): the operational prompt §4.3 and status block (4), the R5 assignment's
pin tables, appendices A to C, S1.8 and §13 (11), `tools/r5_runner/blocks/s01.sh` (5),
`s04c.sh` (2), `s04d.sh` (4), `s11.sh` (4), `r5run.py`'s `PINS`, and
`tests/test_r5_runner.py` (2), plus the candidate's §3 table. Do not label any of it
a pass pin. Then the focused suites above and the manifest and R5 runner suites.

## Remaining gaps

* The evaluator, its `Expectations` source (B-3) and the real `ENOENT` form are
  still not in the manifest, `ENTRY_SOURCES` or the SA-2 tree, and nothing builds a
  continuation. B-7 and M-2 stay open until that wiring is reviewed.
* Only the latest act is re-read in-pass; earlier acts rely on X-4 at the end.
* `admitted_evidence` is the only producer of trustworthy evidence. A hand-made
  `AdmittedEvidence` is not distinguishable by value.
* The entry, session factory and plan assembly are unchanged and inert; no real
  capture, SA-2 build, host contact, acquisition, AUTH/A2, service, staging,
  production, secret, commit or push occurred.

## Independent Codex disposition — 2026-11-28

The bounded v40 slice passed independent review after remediation. The
current-namespace guard refuses a replaced ancestor, capture root or fixed
subdirectory, including changes during read-back or judgment. Stream reads
are bounded to the plan's 512 KiB maximum per stream. Claude removed both
dynamic attribute lookups rejected by the existing structural guard.
The read-back decision reflects the checked instant. X-4 remains the
separate final integrity verification of the whole chain.

Final local, database-free verification on the current source:

* Evidence package, runner pins, continuation, evaluator and static scope:
  **4,915 passed**, zero failures or skips.
* Pass A structural and signature selection: **7 passed**, 52 deselected.
* Pass A plan selection: **87 passed**, 23 deselected.

Two scratch generations matched each other and the checked-in v40 manifest
and plan byte for byte. The dry run reported `executable: False`. The R5 pin
tests passed with the re-derived resource and runner identities.

| Review identity | SHA-256 |
|---|---|
| v40 aggregate | `2e6d5a1da67007c541728e01aeaa62097c9b5eddb5c1008d912ee6c4cfb7babd` |
| Manifest JSON | `4254369f0678700e345dcfd9f1c239d9db054aa4537f2b89b2b86e353353faf7` |
| Concrete plan | `a17b4b0f100c9be9dea36d6599810a746413b90805edfc9483b5f724cb32eb12` |
| Capture-tool source candidate | `76afe186ff1854610e381deb7e3d9730bd653c998dfb2f2792262832272b3daf` |

These are review inputs. The earlier G6 build and tree digest apply to
`2afca20`. No v40 build was performed. The exact classifier bytes are unchanged
and remain covered by A-6. The operational entry is still inert. The next
repository work is the reviewed evaluator/config composition and authority
binding. The real target diagnostic, a new reference build and later admission
and execution each retain their applicable scope and authorization.
