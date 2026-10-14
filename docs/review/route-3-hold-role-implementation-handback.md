# Handback — Route 3 role slice 3: `hold`

Date: 2026-10-13 · Authority: baseline v1.9, active handover, [prompt](route-3-hold-role-implementation-claude-prompt.md).

**Accepted by Peter Duscha on 2026-10-14.** This acceptance closes the complete
inactive Route 3 role series for continued development, including the final GRR
descriptor-close remediation described below. It does not authorize production
or staging activation; the three pre-activation requirements in the current
result remain open.

## Current result — GRR descriptor-close safety — 2026-10-14

This section is the current result for the complete tree. It supersedes the acceptance claim, suite figures and recommendation of the "GRR exception safety" section and every section below it. [Prompt](route-3-hold-role-grr-close-remediation-claude-prompt.md).

**Finding (blocking):** unguarded `os.close()` calls in `adapters/rp11/fsops.py` could raise out of an otherwise handled GRR operation and override its typed result: the target descriptor in `observe_at()` and `remove()`, the parent descriptor in `observe()`, `remove()` and `read_root_file()`, and the target descriptor in `read_root_file()`. Inline IGR then stopped at `running`, with no `igr`, `run-end` or explicit K release. **Disposition: fixed at the adapter boundary.** `_igr()` and `_cl_g()` are unchanged.

**Change** (`adapters/rp11/fsops.py` only): a new `close_quietly(fd)` calls `os.close` once, swallows `OSError`, and never retries (after `EINTR`/`EIO` the descriptor's state is unknown and its number may be reused). It replaces every close on `open_dir` (ancestor close and unwind close), `observe_at`, `observe`, `remove` (target and parent), `read_root_file`, `list_prefixed` and `read_journal`. Journal, record, lock and backstop-guard closes are outside GRR and unchanged.

**Typed outcomes.** A close failure never alters the verdict already selected:

* after complete re-verification the existing attribution and removal decision continue, so `removed` is reported only if `unlink`/`rmdir` succeeded;
* after a mismatch the mismatch (damaged `A1-damaged`, foreign `A0`) is kept and the object is untouched;
* a parent close preserves `absent`, `mismatch`, `unremovable {errno}` and `removed` exactly;
* `observe_at()` returns the observation it had established;
* `read_root_file()` still returns valid `grant.id` bytes, and an earlier read failure is still `None`;
* `before_unlink` is outside the handling: its `EvidenceWriteError` still propagates to GP-R3 and nothing is unlinked.

**Regression tests (+57).** The `CloseFault` injector and `close_fault` fixture in `tests/test_rp11_cleanup.py` fail `os.close` on a target or parent descriptor in two shapes: `closed` (really closed, then `EIO`) and `unknown` (`EIO`, descriptor left open, closed afterwards by the fixture). Single-operation tests also assert that no descriptor number was closed twice.

* Adapter: `test_a_close_error_after_reverification_keeps_the_removal`, `…_after_a_directory_reverification_…`, `…_after_a_mismatch_keeps_the_mismatch_and_the_object` (damaged, foreign), `test_a_parent_close_error_preserves_each_terminal_result` (absent, mismatch, unremovable, removed), `test_a_write_ahead_failure_still_propagates_through_a_close_error`, `test_observe_never_raises_for_a_close_error`, `test_a_close_error_keeps_a_valid_grant_id_and_an_inspection_failure_stays_unavailable`, `test_a_close_error_on_a_traversed_ancestor_does_not_change_the_result`, `test_a_close_error_while_open_dir_unwinds_keeps_the_original_failure`, `test_neighbouring_readers_are_not_overridden_by_a_close_error`.
* Stop-post CL-G: `test_stop_post_cl_g_survives_a_close_error_on_the_grant[4]` reaches `st1-verified`, and the journal runs `run-start`, `cl-g` … `run-end`.
* Inline IGR: `tests/test_rp11_hold.py::test_igr_survives_a_descriptor_close_error_and_keeps_its_order[2 roles × 2 shapes × normal, interrupted-in-AV-1]`. The latch reaches `done`, `igr {removed, identity}` and `run-end` are exact, and the order `hold-end → K released → GRR → igr → run-end` (or the AV-1 order, exit 35) is kept.
* Backstop CL-G: `tests/test_rp11_backstop.py::test_backstop_cl_g_survives_a_descriptor_close_error_on_the_grant[4]` (verified, then BS-2 disarm) and `…_keeps_a_damaged_grant_through_a_close_error_and_the_bs3_rule[2]` (hard-stop, then BS-3 disarm, unchanged).
* The existing GRR inspection-failure matrix is unchanged and green.

**Mutation tests** (local; each reverted, `cmp` confirmed the restored file byte for byte):

* Restoring the unguarded `os.close` at each of the 11 corrected sites, one at a time, made at least one new test fail every time.
* With every corrected site restored at once, **57 tests fail**, which is all of the new tests. The earlier inspection-failure tests still pass.

**Commands and results, final tree.** All runs were on `oracle-test` after the documented secret-excluding `rsync`. They used `/opt/freedom-blades/runtime/venv-web/bin/python`, ran serially, and the bot and web run was launched through a wrapper that resets SIGHUP/SIGINT/SIGQUIT (pytest showed `SigIgn 0x1001000`).

* Focused (`-B -m pytest -q -rfEs -p no:cacheprovider` on the cleanup, hold, backstop, pk_sn, unit-control, h1-artifact, artifact-store and launch gate/source suites): **2022 passed, 2 skipped** (the two root-only 2²⁰+7 descriptor cases).
* Root (`sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_RP11_WHEEL=…/jeepney-0.9.0-py3-none-any.whl … tests/systemd_integration`, root's default `PATH` with `/usr/sbin`): **101 passed** (8 min 14 s).
* Bot (`tests/test_*.py`, with `PATH` and `TEST_DATABASE_URL` exported): **6 failed, 5417 passed, 20 skipped, 39 errors** (17 min 52 s). The failing and error IDs are identical to the baseline (`test_r5_runner.py` 5 F + 39 E, `test_sheet_bootstrap_boundary.py` 1 F), and the skips are the baseline 20. 5417 = 5360 + 57.
* Web (`tests/web`, `TEST_DATABASE_URL=postgresql+psycopg:///freedom_test`): **1 failed, 2891 passed, 80 skipped** (11 min 11 s). The skip count is the correct 80, and the one failure is the baseline `test_p3_4_static_assets.py::test_every_evidence_harness_source_in_the_tree_is_declared`.
* Foundry Node: **171 passed, 0 failed**.
* `python3 .claude/hooks/test_guards.py`: 40 cases (26 refused, 14 allowed), all pass.
* `git diff --check` is clean, with no trailing whitespace in the changed untracked files. `compileall` is clean. No formatter, linter or type checker is configured. No kernel `Out of memory` entries appeared.

**Real-host cleanup** (separate commands after the root run): there is no `rp11` unit, holder, backstop or rotate/`caddy` process. Nothing under `/run` is named `rp11`, and `/run/polkit-1`, `/var/lib/freedom-blades-rp11`, `/etc/freedom-blades-rp11` and `/var/tmp/rp11-*` do not exist. `/usr/local/libexec` is empty and `root:root 0755`, `/etc/polkit-1/rules.d` is empty, and `polkit.service` is active. This work's logs, scripts and `/tmp/pytest-of-ubuntu` were removed. The earlier `p5-*` `/var/tmp` directories were not created by this work and were left alone.

**Remaining production risks:** unchanged from the "GRR exception safety" section's list (the `tmpfiles.d` Polkit ordering and reboot proof, a transient inspection failure reading as damaged or foreign, and the carried items). One addition: a failed close is now silent by design. It leaves at worst a leaked descriptor in a short-lived root process, which the exit releases.

**Recommendation: accept the complete role series.** No target- or parent-descriptor close failure reachable through GRR escapes the adapter or overrides its typed result, nothing is retried, and IGR, stop-post CL-G and backstop CL-G keep their ordering and recovery. The final-tree suites match the baseline. The pre-activation requirements stand: the `tmpfiles.d` installer with reboot proof, a decision on the transient-failure risk, and the independent security review.

## Current result — GRR exception safety — 2026-10-14

This section is the current result for the complete tree. It supersedes the suite figures, risk list and recommendation of every section below, including review 3. [Prompt](route-3-hold-role-grr-remediation-claude-prompt.md).

**Finding (blocking):** `LocalActivationFs.remove()` called `describe_fd()` without converting inspection failures, and its fallback `observe_at()` could raise too. An `fstat`, content-read, or `lstat` error escaped GRR (contrary to `H-GRR.5`, `H-GRR.8` and `RT2.IGR.2`). This left IGR's latch at `running` with no `igr`, `run-end` or explicit K release, and made stop-post/backstop CL-G crash before CL-0. An unlistable attribute list was worse: the object was treated as A1-intact and **unlinked**. **Disposition: fixed at the adapter boundary**, so every GRR caller gets the same typed `Removal`. `_igr()` and `_cl_g()` are unchanged and have no broad handler.

**Change** (`adapters/rp11/fsops.py` only):

* `remove()`: a failed `fstat` on the re-verification descriptor ⇒ `MISMATCH` A0. The verdict comes from a new `_reverified()`, which downgrades an otherwise A1-intact object whose attribute names were `UNLISTABLE` to A1-damaged. `before_unlink` is still called outside every new handler, so its exceptions propagate untranslated and nothing is unlinked. `ENOENT` ⇒ `absent`, an unlink error ⇒ `unremovable {errno}` and an ignored parent flush error ⇒ `removed` are unchanged.
* `describe_fd()`: a failed bounded read/hash leaves `sha256=None`, and a failed directory listing leaves `empty=None` (this is the `observe` protocol's documented "unreadable content gives `sha256=None`"). Only `fstat` can still raise.
* `observe_at()`: a non-`ENOENT` `lstat` error ⇒ `UNREACHABLE` (present, never attributable). An `fstat` error after the open ⇒ the `lstat` facts with no digest. It never raises `OSError`. This keeps a persistent failure from crashing CL-6 after CL-G. It also affects PF-9/PT-10, where a read failure now becomes a typed `mismatch` (publication-failed) instead of an unexpected exception (70). Both outcomes fail closed.
* `read_root_file()`: any `fstat`/read error ⇒ `None`. For GRR-1 that is `identity-unavailable` (`H-GRR.1`).
* GRR still takes no lock and makes no spawn, signal, authorization, network or ext4 write (`H-GRR.6`).

**Selected typed outcome per injected failure** (pinned by `GRR_FAULTS` in `tests/test_rp11_cleanup.py`):

| Injected failure on the target | Facts established | `Removal` | GRR / CL-3 class |
|---|---|---|---|
| bounded content read / hash | type, `(dev, ino)`, metadata | `MISMATCH` A1-damaged | `kept-damaged` / `present-damaged-unremoved` |
| extended-attribute listing | type, `(dev, ino)`, content | `MISMATCH` A1-damaged | `kept-damaged` / `present-damaged-unremoved` |
| `fstat` of the opened descriptor | none | `MISMATCH` A0 | `kept-foreign` / `present-foreign-unremoved` |
| final `open` fails, then fallback `lstat` fails | none | `MISMATCH` A0 | `kept-foreign` / `present-foreign-unremoved` |
| directory listing (CL-5b only) | type, `(dev, ino)` | `MISMATCH` A1-damaged | `present-damaged-unremoved` |
| `grant.id` `fstat`/read (GRR-1) | — | — | `identity-unavailable` |

The object is never unlinked and never claimed removed in any of these cases.

**Regression tests (+39).** The `InspectionFault` injector in `tests/test_rp11_cleanup.py` fails exactly one `os` call (`fstat`, `read`, `listxattr`, `listdir`, or `open`+`lstat` for the fallback) on one target, inside the real adapter.

* Adapter, `tests/test_rp11_cleanup.py` section "GRR remediation":
  * `test_a_failed_target_inspection_is_a_typed_non_removal[4]`
  * `test_a_failed_directory_inspection_keeps_the_directory[4]`
  * `test_observe_never_raises_for_a_failed_inspection[4]`
  * `test_a_failed_grant_id_read_is_identity_unavailable[2]`
  * `test_the_unfaulted_adapter_still_removes_both_kinds`
  * `test_the_accepted_removal_outcomes_are_unchanged[absent, parent-absent, damaged, foreign, unremovable (EACCES 13), parent-flush-fails]`
  * `test_a_failing_write_ahead_propagates_and_nothing_is_unlinked` (`EvidenceWriteError` from `before_unlink`)
  * `test_a_failed_remove_intent_still_enters_grant_priority_not_a_kept_class` (GP-R3, rule `removed-unconfirmed`)
* Inline IGR: `tests/test_rp11_hold.py::test_igr_survives_a_failed_grant_inspection_and_keeps_its_order[4 faults × normal, interrupted-in-AV-1]`. Each case asserts:
  * latch `done`, and `igr {outcome, identity}` equals the selected class and the exact in-memory `grant.id` identity;
  * the order `hold-end → K released → GRR → igr → run-end` (normal, exit 0) or `GRR → igr → run-end → K released` (AV-1, exit 35);
  * the same inode is kept and cleanup does not count it as `igr removed`;
  * a second `_igr()` call is a no-op;
  * after the failure clears, stop-post reaches `st1-verified`.
* Stop-post CL-G: `test_stop_post_cl_g_survives_a_persistent_grant_inspection_failure[4]`. With the failure persisting through the whole attempt:
  * the journal is `run-start`, `cl-g {class}` … `run-end` (CL-0 … CL-7 ran) and `pass-a.json` is removed;
  * the record is `hard-stop`, not `st1-verified`, with `first_rung absent` and the rule both as `active_rule` and as a residual;
  * the grant is kept, and the next attempt verifies once the failure clears.
* Backstop CL-G: `tests/test_rp11_backstop.py::test_backstop_cl_g_survives_a_persistent_grant_inspection_failure[4]`. The firing completes CL and records `deact-1` (exit 1, `terminal=hard-stop`, no disarm). The next firing applies the unchanged BS-3 rule: one disarm, no second CL.

**Mutation tests** (local, each reverted; `cmp` confirmed the restored file byte for byte):

| Mutation | Result |
|---|---|
| Original `fsops.py` restored (the uncaught paths) | **29 of the 39 new tests fail**: every fault case at the adapter and all three callers. The 10 that pass are the "unchanged outcome", write-ahead and GP-R3 tests, which pass on both trees by design |
| Only the `fstat` guard in `remove()` removed | 6 fail |
| Only the `UNLISTABLE` downgrade removed | 6 fail. The object was unlinked |

**Commands and results, final tree.** All runs were on `oracle-test` after the documented secret-excluding `rsync` (its `--delete` removed remote-only `.codex/` and `.aws/` directories that are not in this workspace). They used `/opt/freedom-blades/runtime/venv-web/bin/python` and ran serially. Bot and web used `PATH=/usr/lib/postgresql/16/bin:/usr/bin:/bin` with `TEST_DATABASE_URL=postgresql+psycopg:///freedom_test` exported, and were launched through a wrapper that resets SIGHUP/SIGINT/SIGQUIT; pytest showed `SigIgn 0x1001000`.

* Focused (`… -m pytest -q -rfEs -p no:cacheprovider tests/test_rp11_hold.py tests/test_rp11_backstop.py tests/test_rp11_cleanup.py tests/test_rp11_pk_sn.py tests/test_rp11_h1_artifact.py tests/test_systemd_unit_control.py`): **1174 passed, 2 skipped**, the same on the host and locally. The skips are the two root-only 2²⁰+7 descriptor cases.
* Root (`sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_RP11_WHEEL=/tmp/rp11-wheel/jeepney-0.9.0-py3-none-any.whl …/python -B -m pytest -q -rfEs -p no:cacheprovider tests/systemd_integration`): **101 passed** (8 min 31 s).
* Bot (`tests/test_*.py`): **6 failed, 5360 passed, 20 skipped, 39 errors** (19 min 57 s).
  * The failed and error IDs are identical to the baseline: `test_r5_runner.py` 5 F + 39 E, and `test_sheet_bootstrap_boundary.py::test_the_legacy_sheets_connector_still_exposes_read_and_write`.
  * The 20 skips are the baseline 20.
  * 5360 passed = 5321 + the 39 new tests.
* Web (`tests/web`, after the bot suite): **1 failed, 2891 passed, 80 skipped** (10 min 9 s).
  * This is identical to the baseline: the one failure is `test_p3_4_static_assets.py::test_every_evidence_harness_source_in_the_tree_is_declared`, and the 80 skips are the correct ones (54 + 26 matrix cells).
  * **Disclosed and not evidence:** the first web run, launched straight after the bot suite, was OOM-killed at 12 % (exit 137; kernel `Out of memory` at 10:26). After this work's `/tmp/pytest-of-ubuntu` (110 MB on the tmpfs `/tmp`) was removed, the complete suite was rerun alone. Foundry (above) ran after the killed run.
* Foundry (`node --test foundry-module/tests/*.test.mjs`): **171 passed, 0 failed**.
* `python3 .claude/hooks/test_guards.py`: 40 cases (26 refused, 14 allowed), all pass.
* `git diff --check` is clean, with no trailing whitespace in the changed untracked files. `compileall` of `adapters application tests infra` is clean (bytecode written to scratch). No formatter, linter or type checker is configured.

**Real-host cleanup** (separate commands after the root run):

* There is no `rp11*` unit or unit file and no holder, rotate or `caddy` stub process.
* Nothing under `/run` is named `rp11`.
* None of these exist: `/run/polkit-1`, `/run/nextroot`, `/var/lib/freedom-blades-rp11`, `/etc/freedom-blades-rp11`.
* There is no `/var/tmp/rp11-*` from this work.
* `/usr/local/libexec` is empty and `root:root 0755`, and `/etc/polkit-1/rules.d` is empty.
* `polkit.service` is active and the capture unit is `not-found`.
* This work's run scripts and logs (`/var/tmp/grr-*`) and pytest temps were removed.
* Left untouched (not created by this work): the `p5-*` directories in `/var/tmp`, `/tmp/jpvenv`, and an idle polling `bash` loop from an earlier session.

**Remaining production risks** (these replace review 3's list):

1. **The Polkit directory ordering is unsolved for production.** The `tmpfiles.d` entry still has to be installed and proved across a real reboot before activation.
2. **A transient inspection failure now reads as damaged or foreign.** GRR then keeps an intact grant, and CL-3 classes it `present-*-unremoved`. Under the unchanged BS-3 rule (damaged or foreign leftovers do not block the disarm), the backstop disarms after that hard-stop record. The grant then stays live until CP, the boot or `attest`, and the record reports it as a residual. This is fail-closed for removal but not for exposure. Making it retryable would mean a new class or a BS-3 change, which is a decision for Peter and was not made here.
3. A manager re-exec or DI-1 failure during HL ends the activation (`observation-failed`).
4. The `act` record can read `activated` after a late PF-8/PF-9 failure (CQ-4 still refuses).
5. The `consume` class is diagnostic.
6. A-2 v3's `image_sha256`/`h2_record_sha256` are quoted pins, not re-derived.
7. `igr`/`run-end` are best effort.
8. Carried from earlier remediations: the S0/A0 K edge cases, the `/proc/self/fd` dependency, PID/start-time subject identity, operator-writable ACT/`/var/tmp`, no `consume`/CP, and `renameat2` through `ctypes`.

**Recommendation: accept the complete role series.** No inspection failure at the concrete boundary escapes GRR. IGR, stop-post CL-G and backstop CL-G each receive a closed outcome and keep their ordering and recovery, and no unreadable or partially observed object is removed. Focused and real-PID-1 tests pass, and the final-tree suites match the baseline. Before production activation, three things are still required: the `tmpfiles.d` installer with reboot proof, Peter's decision on risk 2, and the independent security review.

## Final remediation — review 3 — 2026-10-13

**Superseded** for suite figures, risks and recommendation by [Current result — GRR exception safety](#current-result--grr-exception-safety--2026-10-14); its findings and representations remain in force. [Prompt](route-3-hold-role-review-remediation-claude-prompt.md).

| # | Finding | Disposition |
|---|---|---|
| 1 | ACT `run-start` was reduced: no `h2_record_sha256` or `helper`, and `lock` was a bare identity (`RT2.AM0.16`) | **Fixed.** One closed grammar (the reduced line is now invalid, not accepted alongside); emitted line pinned byte for byte |
| 2 | `igr` had no `identity` (`RT2.IGR.3`); no `run-end` (`RT2.AM3.2`) | **Fixed.** `igr {outcome, identity}`; `run-end` implemented with a chosen placement. The sources do not conflict, so there is no maintainer question |
| 3 | The last full bot run had five failures outside the baseline, and the complete suite was not rerun | **Resolved, cause found.** The four `test_rotate_test_gate_script.py` SIGINT failures came from the way the suites were launched: from a detached `&` job, SIGINT is ignored and stays ignored across `exec`. The tests' group SIGINT was then ignored, they timed out after 30 s, and they left orphaned `rotate-test-gate.sh` sessions (eight were still running on the host from the previous runs). The backup-drill failure came from the `freedom_test` state left by the OOM-killed run. The complete suites were rerun with SIGINT at its default disposition and match the baseline exactly |

**Selected representations** (reversible; recorded in `application/rp11/{authority,journal,hold}.py` and pinned by tests):

* **Authority.** A-2 is now `rp11-a2/3` and adds `h2_record_sha256` and `helper {image_sha256[1…16 distinct], tool_sha256}`: the "tool and image digests" that `RT2.AM0.1` lists among A-2's pins. Before recording `tool_sha256`, AM-0 requires the installed `Layout.tool` (root-owned, `0644`, read no-follow) to hash to A-2's pin; otherwise the end is `invalid-authority` (20, `detail=tool`) before any state. `image_sha256` and `h2_record_sha256` are taken from A-2 alone, and nothing comes from the environment. The `act` record now carries the same `h2_record_sha256`, `helper` and `lock` (it previously had `h2 absent` and `image_sha256 = [tool]`).
* **`run-start`** is exactly `{a2_sha256, h1_record_sha256, h2_record_sha256, boot_id, pass_config_sha256, staged_rule_sha256, tool_sha256, holder_invocation_id, lease, lock {object {path, dev, ino}, mode "held", wait_ms 0}, capture {active_state, invocation_id, inactive_enter_us, m_a_us, bsp_retries}, helper {role "hold", image_sha256[], tool_sha256}, params}`. A line is refused if `helper.tool_sha256` differs from `tool_sha256`. `lock.mode` can only be `held` because the holder writes `run-start` only after its one non-blocking lock of K succeeded.
* **IGR identity.** `igr {outcome ∈ removed|absent|kept-damaged|kept-foreign|unremovable, identity}`. `identity` is the in-memory identity GRR used, `{path, dev, ino, sha256, size, mode}`, or the repository's explicit absence `"absent"` when AM-1G never produced one. A line is refused if the identity is `"absent"` and the outcome is anything but `absent`. Removal still comes first; the line is written afterwards, best effort, and nothing re-opens a path. Cleanup now counts `igr removed` (which classes the rule `removed-earlier`) only when `identity` equals the grant identity journaled earlier. This narrows attribution and never widens what cleanup may remove.
* **`run-end`** is the holder's last ACT line. It is written best effort from the same `finally`, after IGR. `outcome` is the end class (`hold-ended` only after HL's normal end, the 16 fail-closed classes, or `internal-error` for an unexpected exception), so it never claims success for an incomplete activation. A failed `run-end` changes neither the grant nor the exit code. There is no `igr` or `run-end` without an ACT journal. `hold-end` remains HL's complete-end line. Pinned orders:

| End | Order |
|---|---|
| HL normal, HL `observation-failed` | `hold-end` → K released → GRR → `igr` → `run-end` |
| `start-before-hold`, `observation-failed` at hold-start | `hold-end` (under K) → GRR → `igr` → `run-end` → K released |
| `interrupted` in HL (K not held) | GRR → `igr` → `run-end` |
| `interrupted` in AV-1, unexpected exception, any other end with K held | GRR → `igr` → `run-end` → K released |
| `SIGKILL` | none (CL-G recovers, as before) |

**Principal files:** `application/rp11/authority.py` (A-2 v3), `journal.py` (`run-start`, `igr`, `run-end` grammars, cross-field rules), `evidence.py` (the new `lock` envelope; `igr` identity matching), `hold.py` (tool check, `run-start`, `act` record, IGR identity, `run-end`), `adapters/rp11/hold.py` (no longer hashes the tool itself), `tests/rp11_fixtures.py`, `tests/test_rp11_hold.py` (+69 tests, 255 in total), `tests/test_rp11_cleanup.py`, `tests/systemd_integration/test_route3_hold_host.py` (PID-1 assertions for the new lines).

**Regression tests** (`tests/test_rp11_hold.py`, section "Review remediation 3"): exact first-line bytes of `run-start`; 21 malformed, missing and extra `run-start` variants, each refused on write and making the journal invalid with no cleanup attribution; 10 A-2 v3 grammar cases and 4 tool-pin cases (`invalid-authority`, nothing created); `igr` identity for removed, kept-damaged ×3, kept-foreign and unremovable (each equal to `grant.id`), explicit absence before AM-1G, and the unlinked identity when the flag stops the run before the link; 7 malformed `igr` and 4 malformed `run-end` lines; a forged identity is not counted by cleanup; the order on 7 end classes, with the rule shown absent at the moment `igr` is written; `igr` or `run-end` failing by write or flush leaves the grant removed, the exit at 0, the IGR latch intact and stop-post `st1-verified`. **Mutation checks** (each applied, run, then reverted; byte equality confirmed): the reduced lock envelope fails 241 and errors 34; no `h2`/`helper` fails 240 and errors 34; `igr` without identity fails 11; cleanup ignoring the identity fails 1; no `run-end` fails 18; `run-end` before IGR fails 20; K released before `run-end` fails 4; no tool check fails 4; an evidence write before GRR's removal fails 17.

**Commands and results, final tree** (`oracle-test`; synced by the documented secret-excluding `rsync`; serial; `PATH=/usr/lib/postgresql/16/bin:/usr/bin:/bin`, `TEST_DATABASE_URL=postgresql+psycopg:///freedom_test` exported, `/opt/freedom-blades/runtime/venv-web/bin/python`):

* Clean start: the eight orphaned rotate sessions above were stopped, and nothing else; this work's `/tmp/pytest-of-ubuntu` and `/tmp/pytest-of-root` were removed; `freedom_test` was dropped and recreated (`dropdb`/`createdb`).
* Focused (`… -m pytest -q -rfEs -p no:cacheprovider tests/test_rp11_hold.py tests/test_rp11_backstop.py tests/test_rp11_cleanup.py tests/test_rp11_pk_sn.py tests/test_rp11_h1_artifact.py tests/test_systemd_unit_control.py`): **1135 passed, 2 skipped** on the host and locally. The two skips are the root-only 2²⁰+7 descriptor cases.
* Root (`sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_RP11_WHEEL=/tmp/rp11-wheel/jeepney-0.9.0-py3-none-any.whl …/python -B -m pytest -q -rfEs -p no:cacheprovider tests/systemd_integration`): **101 passed** (8 min 2 s). Under real PID 1 this run also asserts the complete `run-start` key set and values (the A-2 pins, the installed tool's digest, K's real `(dev, ino)`), `igr.identity` equal to the live `grant.id`, and `run-end` as the last line (`hold-ended`, `grant-not-seen`, `interrupted` ×3, absent after `SIGKILL`).
* Bot (`… -m pytest -q -rfEs -p no:cacheprovider tests/test_*.py`): **6 failed, 5321 passed, 20 skipped, 39 errors** (14 min 45 s). The failed and error IDs are **identical** to the established baseline (`test_r5_runner.py` 5 F + 39 E, `test_sheet_bootstrap_boundary.py::test_the_legacy_sheets_connector_still_exposes_read_and_write`). Skips: the baseline 18 (16 `rp11-launch` toolchain, 2 backup "found none") plus the 2 root-only 2²⁰+7 cases from remediation 2. The four rotate SIGINT tests pass. Passes +69 = the new tests.
* Web (`tests/web`, after the bot suite): **1 failed, 2891 passed, 80 skipped** (12 min 10 s), identical to the baseline: `test_p3_4_static_assets.py::test_every_evidence_harness_source_in_the_tree_is_declared` and the correct 80 skips (54 + 26 matrix cells).
* Foundry (`node --test foundry-module/tests/*.test.mjs`): **171 passed, 0 failed**.
* **Disclosed and not evidence:** a first complete sequence on the same tree was launched with SIGINT ignored (`SigIgn 0x7`): bot **10 failed**, 5315 passed, 22 skipped, 39 errors. These were the baseline set plus the same four rotate SIGINT failures, which left four new orphaned sessions; I stopped them. That run also had 4 backup "found none" skips instead of 2, because the freshly recreated database held no runtime-role table grants until a web run had added them. Web (1 F, 2891 passed, 80 skipped) and Foundry (171) matched. The final sequence above was launched through a wrapper that resets SIGHUP/SIGINT/SIGQUIT to their defaults before `exec`; the pytest process recorded `SigIgn 0x1001000`, i.e. only CPython's own SIGPIPE/SIGXFSZ. No OOM kill occurred (kernel count unchanged).
* `python3 .claude/hooks/test_guards.py`: 40 cases (26 refused, 14 allowed), all pass. `git diff --check` clean, no trailing whitespace in the changed untracked files, `compileall` clean (bytecode written to scratch). No formatter, linter or type checker is configured.
* After the suites ran I edited only this handback. No test reads `docs/review/`.

**Real-host cleanup** (checked by separate commands after the root run and again at the end): no `rp11*` unit or unit file; no holder, rotate or `caddy` stub process; nothing under `/run` named `rp11`; no `/run/polkit-1`, `/run/nextroot`, `/var/lib/freedom-blades-rp11`, `/etc/freedom-blades-rp11` or `/run/systemd/system/rp11-*`; `/usr/local/libexec` empty, `root:root 0755`; `/etc/polkit-1/rules.d` empty; `polkit.service` active; capture unit `not-found`; no root-owned file in the repository newer than the run; this work's logs, run scripts and pytest temps removed. Left untouched (not created by this work): the `p5-*` evidence directories in `/var/tmp`, `/tmp/jpvenv` and an idle `bash` polling loop from an earlier session.

**Remaining production risks:**

1. **Polkit directory ordering is unsolved for production.** With polkitd 127 the holder works only if `/run/polkit-1/rules.d` existed when polkitd started; otherwise AV-1 fails closed every time. The accepted `tmpfiles.d` entry is not installed or reboot-proved, and it is required before activation.
2. **A manager re-exec, or any DI-1 failure, during HL ends the activation** (`observation-failed`). This is safe, but an operator pass that has not started yet loses its activation.
3. **The `act` record after a late PF failure:** if PF-8 or PF-9 of the `act` record fails after its link, the record says `activated` although the holder ended 32 before `hold-start`. CQ-4 still refuses (there is no `hold-start`), and the `deact` record shows the outcome.
4. **The `consume` class is diagnostic** and can read `none` after a real pass (PO-21 (k)/(s)).
5. **A-2 v3's `helper.image_sha256` and `h2_record_sha256` are quoted pins that the holder does not re-derive.** Only the tool digest is checked against the installed file, and no installer writes A-2 yet. The cleanup roles' `deact` records still record their own `helper.image_sha256` as `[tool digest]` (RT-3/RT-4, not changed here).
6. **`run-end` and `igr` are best effort.** A kill or failed write leaves them missing, and cleanup never relies on either for removal.
7. Carried: the empty-journal K stays A0 and an empty K placed by another root process is S0 (remediation 1); `/proc/self/fd` is required (remediation 2); PID/start-time subject identity (A-13.4); the ACT directory and `/var/tmp` are operator-writable (OH-D-6); no `consume`/CP; `renameat2` is called through `ctypes`.

**Recommendation: accept the complete role series.** All three findings are closed with executable evidence. `run-start`, `igr` and `run-end` now implement `RT2.AM0.16`, `RT2.IGR.3` and `RT2.AM3.2`, and parsing and cleanup stay fail closed. Focused and real-PID-1 tests pass, and the final-tree bot, web and Foundry suites match the baseline exactly. Two things remain before production activation: the `tmpfiles.d` installer with real-reboot proof (risk 1), and the independent security review.

## Review remediation — 2026-10-13

The independent review of this slice raised two findings. Both are fixed; nothing else changed.

| Finding | Remediation | Executable evidence |
|---|---|---|
| **1 (blocking)** `H-PROC.3`: the DI-6 subject closed descriptors only below a fixed `65_536`, so a valid inheritable descriptor (e.g. 70,000 under the holder's hard `LimitNOFILE` 524,288) survived | `adapters/rp11/process.py`: new `close_inherited_descriptors(keep=)` lists `/proc/self/fd` (the kernel's own list of open descriptors), closes every one ≥ 3 except the readiness pipe, then lists again and raises if any other descriptor is still open. No numeric bound is used — not a constant, not `RLIMIT_NOFILE` (which can be lowered below an already-open descriptor, or raised to `fs.nr_open`, 2,147,483,584 on `oracle-test`), and there is no `RLIM_INFINITY` case. An unreadable listing or a survivor raises in the child, which then exits 127 without the readiness byte (fail closed: `ready=False`, the subject is still settled by SN). `_MAX_FD` is removed. Order and everything else in `_child` are unchanged: dispositions, `setsid`, credentials and their check, `chdir("/")`, then the close, `alarm(60)`, the byte, `pause()` | `tests/test_rp11_pk_sn.py`: `test_a_descriptor_above_65535_is_not_inherited_by_the_ready_subject` (soft limit raised, inheritable fd 70,000, real fork subject ⇒ `/proc/<pid>/fd` exactly `0 1 2`), `test_a_descriptor_above_the_current_soft_limit_is_not_inherited` (fd 70,000 open, soft limit then lowered to 1,024 ⇒ still `0 1 2`), `test_a_subject_that_cannot_list_its_descriptors_never_reports_ready`, `test_a_descriptor_that_survives_closing_is_an_error`. Limits are restored by a context manager on every exit (skip and failure included) and the restore is asserted. Root host: `test_route3_hold_host.py::test_the_di6_subject_inherits_no_descriptor_above_65535_under_pid1` (a transient PID 1 service with the holder's default limits; fd 70,000; credentials changed to `ubuntu`; raised and lowered-below soft limit ⇒ ready, `0 1 2`, `Uid` = `ubuntu` ×4, cwd `/`, own session, reaped) |
| **2 (important)** `RT2.SG1.3` / `RT2.AM0.8`: no flag check between K's creation and BSP; a K left before the ACT journal was classed `present-foreign-unremoved` and hard-stopped cleanup | `application/rp11/hold.py`: `self._check("AM-0")` immediately after `_create_k()` and before `_capture_baseline()`. `application/rp11/cleanup.py` CL-5b: when no K identity line exists, K is **S0** (`s0-kept`: reported, kept, cleared by the boot, not blocking; R8 LD-1, `H-CL.5b.2`) only if **all** hold: valid authority; the ACT journal **absent** (never created — an unreadable, invalid, truncated or empty journal does not qualify; `H-GR1.1` keeps those A0); the pinned boot; `/run` on tmpfs; CL-0 holds K's lock (`held`) and K is still that very `(dev, ino)`; K a directory, owner root (the layout owner), mode exactly `0700`, two links, empty (so no `grant.id`), no ACL/capability xattr and listable xattrs. K is never removed by this path. CL-6's check is now `lock-dir-absent-or-s0` and re-observes K against the same predicate. `records.py`: `s0-kept` added to the directory classes (BS-3 treats it as non-A1-intact, like other kept non-attributable objects). Every other K keeps the previous A0 behaviour: kept, unremoved, `hard-stop` | `tests/test_rp11_hold.py` (new section "K before the ACT journal"): `test_a_stop_right_after_k_is_created_ends_before_the_baseline` (35 at AM-0, no capture read at all, K released, then stop-post `st1-verified` with K kept), `test_a_holder_killed_between_k_and_the_journal_leaves_an_s0_k` (real `SIGKILL` in BSP's first read: no `finally`, no IGR), `test_every_failure_before_the_journal_leaves_an_s0_k_that_recovery_verifies[capture-read-error, baseline-unstable, capture-busy, act-journal-uncreatable]`, `test_a_k_that_could_not_be_locked_is_s0_for_the_cleanup`; fail-closed: `test_a_k_that_is_not_exactly_the_pre_journal_k_stays_a0_and_hard_stops[holds-grant-id, non-empty, mode-0755, mode-0500, a-file, a-symlink, invalid-journal, empty-journal, other-boot, run-not-tmpfs]`, `test_a_k_replaced_after_the_cleanup_locked_it_is_not_s0` (empty root `0700` dir, other inode), `test_a_k_locked_by_someone_else_is_not_s0` (lock `degraded`), `test_the_s0_shape_of_k_is_exact[11]` (ACL ×2, capability, unlistable xattrs, nlink, uid, gid, mode, unlisted, inode, type). Each S0 recovery asserts: same inode kept, record validates, `directories[-1]` `s0-kept`, one residual `{class s0, type dir}`, a `classified` line and no `remove-intent` for K, and the backstop reads the record as BS-2. **Changed:** `test_the_stop_flag_at_every_read_point_ends_with_igr_and_recovers` no longer expects `HARD_STOP` + residual for the K-only reads: it now expects `st1-verified` with K kept as the only residual `s0`, and asserts exactly two consecutive flag reads between K and the journal (one was the defect) |

**Mutation checks (run locally, then reverted; `diff` confirmed the restore):** removing the new flag check fails 2 tests; disabling S0 fails 8; making S0 accept any present K fails all 12 fail-closed tests; restoring `closerange(…, 65_536)` fails 3 PK/SN tests; a `getrlimit`-bounded close instead fails the lowered-limit and no-listing tests.

Suite figures recorded here for this remediation's tree are superseded; the current results are in [Current result](#current-result--grr-exception-safety--2026-10-14).

**Remaining risks from this remediation:**

* An empty, structurally exact K placed by **another root process** between AM-0's absence check and the holder's `mkdir` (the `lock-object` collision case) is indistinguishable from the holder's own pre-journal K and is classed S0: kept and reported, never removed, not blocking. It holds no grant and is cleared by the boot. This follows the accepted text ("a K without an identity line is S0"); a stricter rule would need a decision.
* The window between the ACT journal's exclusive creation and `run-start`'s flush still leaves an **empty journal**; that K stays A0 and hard-stops (test `[empty-journal]`). The accepted text names S0 for a K "before the journal"; I did not extend it to an existing but empty journal, because `H-GR1.1` makes an invalid journal A0.
* ~~Not in scope, noted: the first image's own RH close is bounded by the soft limit at start~~ — **closed by review remediation 2 below**.

## Review remediation 2 — first-image descriptor isolation (`H-FI.3`) — 2026-10-13

The remaining blocking finding: `first_image_controls()` closed descriptors with `os.closerange(3, max(min(SC_OPEN_MAX, 2**20), 4))`. A descriptor above the start-time soft limit (opened under a higher limit, which was then lowered) or above `2**20` (`fs.nr_open` is 2,147,483,584 on `oracle-test`) reached the role and the holder. `H-FI.3` requires that **every** descriptor ≥ 3 be closed before the first state operation. Remediation 1's DI-6 subject fix and its pre-journal K/S0 handling are unchanged.

| Change | Executable evidence |
|---|---|
| `infra/rp11-h1/rp11_h1.py`: new `close_descriptors_from_3()` lists `/proc/self/fd`, closes every descriptor ≥ 3, lists again and returns `False` if any is still open. No numeric bound is used: not `SC_OPEN_MAX`/`RLIMIT_NOFILE` and not a constant. If the listing is unreadable or a descriptor survives, `first_image_controls()` returns **71** (`EX_OSERR`, "inherited descriptors could not be closed") before any role, import from `lib/` or state operation, so it fails closed. It is the same method as remediation 1's `close_inherited_descriptors`, but it is written inline rather than imported, because the first image runs before `lib/` is on `sys.path` and before the root-ownership check of the tree. Control order is unchanged (0–2 check, INVOCATION_ID, environment cleared, close, signals, `umask`, `chdir`). The module docstring now documents 71 for this case | `tests/test_rp11_h1_artifact.py`: `test_a_high_inherited_descriptor_never_reaches_the_role[raised/lowered-below × 70000/2**20+7]` (the built image runs the exact `-I -S` vector; the role's own `/proc/self/fd` listing shows no descriptor ≥ 3; the soft limit is lowered to 1,024 in the child before `exec`; the original limits are restored and asserted on every exit), `test_an_image_that_cannot_list_its_descriptors_is_refused`, `test_a_descriptor_that_survives_closing_is_refused`, `test_the_close_leaves_only_the_standard_descriptors`, `test_a_refused_close_runs_no_role` (71, the role never runs). The probe role now lists every open descriptor instead of scanning 3–63. Root host, `tests/systemd_integration/test_route3_host.py::test_the_first_image_closes_inherited_descriptors_above_any_limit_under_pid1[raised, lowered-below]`: a transient root unit opens 70,000 and 2²⁰+7 (hard limit raised to 2²⁰+8; soft limit 2²⁰+8 or 1,024) and `exec`s the adapter's exact `hold` vector in place (double roles, so the holder stays running). The live holder's table (fd, target, flags) must equal that of a control holder that inherited nothing, and it holds neither number |

**Note:** a running holder legitimately holds one descriptor ≥ 3: `libffi`, `O_CLOEXEC`, opened by its own `ctypes` import (`renameat2`) **after** the controls. That is why the host test compares against a control holder instead of expecting exactly `0 1 2`. The first host run used the naive assertion, failed on exactly this descriptor, and was corrected; it was identified with `/proc/<pid>/fd` and `fdinfo`.

**Mutation checks (then reverted; `diff` confirmed the restore):** restoring the old bounded `closerange` fails 4 local artifact tests (lowered-below 70,000; no listing; survivor; 71 end to end). On `oracle-test` under PID 1 it fails both host cases: with the soft limit raised, 2²⁰+7 survived; lowered, both 70,000 and 2²⁰+7 survived.

Suite figures recorded here for this remediation's tree (including its five bot failures outside the baseline) are superseded; the cause and the current results are in [Current result](#current-result--grr-exception-safety--2026-10-14).

**Remaining risk:** without a readable `/proc/self/fd`, and also when the soft limit is lowered so far that every number below it is in use and the listing cannot open its own descriptor, every role refuses with 71. This is deliberate (fail closed). The production units run with `/proc` mounted.

## Behavior delivered

`/usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py hold <id> <a2>` now
runs RT-2. All three role vectors perform their real behavior on `oracle-test`. No production caller,
installer, `consume`, `attest`, static `start`/`stop` or activation was added; the roles remain
inactive in production.

* **SG-1** (`adapters/rp11/hold.py`): the role's first act, before the A-2 read: one flag-only
  handler for `SIGTERM SIGINT SIGHUP SIGQUIT SIGUSR1 SIGUSR2 SIGALRM`, `SIGPIPE` ignored, `SIGCHLD`
  default, no mask. The main thread reads the flag at every step boundary, immediately before and
  after the rule's link, at every `slice_ms` wake-up of every wait and inside the PK/2 series
  (new `stop_requested`, result `unconfirmed`/`interrupted` after the current subject is settled).
* **AM-0**: A-2 by the operand digest → H-1 → the installed tool's digest equal to A-2's pin; boot id; `/run` on tmpfs; `/run`, `/run/polkit-1`,
  `/run/polkit-1/rules.d` root-owned directories without group/other write or ACL name; absence of
  tree P, the rule, `/etc/freedom-blades-rp11`, K, the capture root, `/run/nextroot` and the rule
  basename in the three other rules directories; the three `LoadState` reads; K created
  exclusively (`0700`, empty, no forbidden xattr) and `flock`ed once; BSP (`m_a` from
  `CLOCK_MONOTONIC` in µs before each read, at most five 2-ms retries, a read error is never a
  baseline, `capture-busy-at-act`); the ACT journal created exclusively in the operator's `0700`
  directory and `run-start`.
* **AK-1**: `backstop-intent` durable, exactly one DI-3 through `SystemdManagerAdapter`
  (`R`, `S_b`, `S` from A-2), any non-`ok` result ends 26 with no retry (`effect-unknown` when the
  adapter says the effect is unconfirmed), the timer must read `active` through DI-1,
  `backstop-armed {timer, period_s, max, runtime_s}`.
* **AM-1/AM-1R/AM-1G/AM-2** (`adapters/rp11/holdfs.py`): PT for tree P (`pass-a.json` =
  `canonical_bytes` of the A-2-quoted document) and, only when the rules directory is absent, tree R
  at its first absent component; PT seals, then `renameat2(RENAME_NOREPLACE)` (via `ctypes`
  against the loaded libc; no replacing fallback). The staged rule is read once through a no-follow
  descriptor matching A-2's `(dev, ino)` and digest; PF-1 … PF-5 for the rule; `grant.id` naming
  that unnamed inode published by PF in K; flag; PF-6 link (never replacing: `EEXIST` ⇒ the object
  is A0 and kept); flag; PF-7 … PF-9.
* **AV-1**: both published files re-verified, the baseline recomputed equal to H-1's, PK/2
  seek-authorized `start` then first-decisive `stop` for the operator's DI-6 subject; every subject
  and both decisions journaled before use; `grant-not-seen`, `stop-control-authorized`,
  `stop-control-unconfirmed` fail closed.
* **AM-3**: the `act` record (`outcome activated`) by PF into the record store; only its durable
  publication sets ACT PASS. **hold-start** re-reads the capture unit under K (τ = τ₀, not active,
  no job, else OS-7 `start-before-hold`), appends `hold-start`, then closes K.
* **HL** (`application/rp11/hl.py`, pure): every Δ, DI-1 plus a no-follow lookup of the capture root
  and the claim (and the consume journal); `pass-observed` only on change; the amended reasons in
  the accepted order; a terminal reason is acted on only after one non-blocking K attempt (busy ⇒
  keep observing) and a re-observation under K; `hold-end {reason, observation}` durable, K closed.
* **IGR**: exactly once from `run()`'s `finally` on every catchable end (return, `_End`, or any
  exception): GRR with the in-memory identity, then a best-effort `igr {outcome, identity}` line;
  it never removes a damaged, foreign or replaced object. Then, from the same `finally`, the
  best-effort `run-end {outcome}` and the release of K if still held. The process then returns and
  PID 1 runs the implemented stop-post.
* **Subject fix (shared)**: the DI-6 subject is forked from the holder, so it inherited the flag-only
  `SIGALRM` handler and its `alarm(60)` self-limit would not have ended it. `_child` now restores the
  default disposition of the SG-1 set and `SIGPIPE` first (`adapters/rp11/process.py`; host-tested).

Output: one line `rp11-hold <class> <id> step=<s> detail=<token> act_pass=<yes|no> igr=<outcome>`;
an unexpected exception is `rp11-hold internal-error <id> <Class>` after IGR, exit 70.

**Reversible choices (pinned by tests, recorded in the modules):**

* A-2 schema `rp11-a2/3`: the quoted `pass_config` document (canonical, ≤ 65,536 B, schema
  `rp11-pass-a/1`, absolute `capture_root`, other keys opaque), `staged_rule {dev, ino}` (path fixed
  at `<store>/staged/<id>.rules`), lease `bs_runtime_s` (S_b, 60 … 600), `h2_record_sha256` and
  `helper {image_sha256[1…16 distinct], tool_sha256}`. ACT `run-start` is exactly RT2.AM0.16 (see
  the final remediation); `hold-start {capture}`; `hold-end {reason, observation}`;
  `backstop-armed {…, max, runtime_s}`; `igr {outcome, identity}`; `run-end {outcome}`. Cleanup
  parses all of it.
* AM-0's `LoadState` triple: backstop timer and service `not-found`, the holder's own unit `loaded`
  (the literal AP-0 condition cannot hold for the unit running the holder). The gap row
  `RT2.AM0.7` is **not implemented**. A rules directory absent at AM-0 is admitted (tree R).
* `grant.id` is published by PF (so cleanup can attribute and remove it). `hold-end` is HL's
  complete-end line, and no `hold-end` is written for a flag-ended HL. `run-end` is the holder's
  last ACT line, after IGR (placement and vocabulary in the final remediation).
* Exit codes 0 (HL end) and 20 … 35, one per class: `invalid-authority` 20, `precondition` 21,
  `lock-object` 22, `capture-baseline-unstable` 23, `capture-busy-at-act` 24,
  `evidence-unwritable` 25, `backstop-unconfirmed` 26, `publication-failed` 27, `grant-not-seen`
  28, `stop-control-unconfirmed` 29, `stop-control-authorized` 30, `verification-failed` 31,
  `act-record-unpublished` 32, `start-before-hold` 33, `observation-failed` 34, `interrupted` 35.

## Principal files

New: `application/rp11/{hl,hold}.py`, `adapters/rp11/{hold,holdfs}.py`, `tests/test_rp11_hold.py`,
`tests/systemd_integration/test_route3_hold_host.py`, this handback.
Changed: `application/rp11/{authority,journal,evidence,paths,pk,ports,cleanup}.py` (A-2 v3, ACT fields,
`staged_rule`/`nextroot`/`etc_config`/`other_rules_dirs`, PK stop flag, holder ports, public
`grr_outcome`/`identity_doc`), `adapters/rp11/process.py` (subject dispositions, `monotonic_us`),
`infra/rp11-h1/{rp11_roles,rp11_h1,build}.py` (`hold` dispatch, up-front import, four modules in
`SOURCES`), `tests/rp11_fixtures.py` (A-2 v2, staged rule, new ACT fields), `tests/test_rp11_cleanup.py`
(ACT line helper), `tests/test_rp11_h1_artifact.py` (`hold` dispatch replaces "hold refuses 69"),
`tests/systemd_integration/{test_route3_host,test_route3_stop_post_host,test_route3_backstop_host}.py`
(a holder without A-2 now ends 20; one whose activation is pre-built ends 21 at AM-0),
`tests/web/test_p3_4_static_assets.py` (scope allowlist += the four modules).
No dependency, migration, configuration or `.env.example` change.

## RT-2 row → evidence

H = `tests/test_rp11_hold.py` (255 tests); P = `tests/systemd_integration/test_route3_hold_host.py`
(14, PID 1); A = `tests/test_rp11_h1_artifact.py`; R = `tests/systemd_integration/test_route3_host.py`.

| Row | Executable evidence |
|---|---|
| RT2.FI.1 | A first-image tests, `test_entry_accepts_exactly_the_three_role_vectors`, `test_hold_runs_its_composition_root_with_the_provenance`, `test_the_entry_imports_the_hold_root_up_front`; R `test_exact_role_vector_runs_isolated…[hold]` (empty env ⇒ 20), `test_pid1_executes_the_exact_holder_and_stop_post_vectors`; P every test (PID 1, exact vector; `holder.invocation_id` recorded) |
| H-FI.3 (first image) | A `test_a_high_inherited_descriptor_never_reaches_the_role[4]`, `…cannot_list_its_descriptors…`, `…survives_closing…`, `…close_leaves_only_the_standard_descriptors`, `test_a_refused_close_runs_no_role`; R `test_the_first_image_closes_inherited_descriptors_above_any_limit_under_pid1[2]` (remediation 2) |
| RT2.SG1.1–2 | H `test_sg1_handlers_only_set_the_flag_and_a_second_signal_changes_nothing` (child process: flag only, second signal, `SIGPIPE` ignored, `SIGCHLD` default, empty mask), `test_run_hold_installs_sg1_before_reading_anything`, `test_the_subject_forked_under_sg1_has_default_dispositions_and_self_limits`; P `test_sigterm_during_av1…[1,2]` (two back-to-back signals ⇒ one IGR) |
| RT2.SG1.3 | H `test_the_stop_flag_at_every_read_point_ends_with_igr_and_recovers` (every flag read of a complete run, all ten step labels, each ⇒ 35, IGR once, no grant, stop-post recovers; two reads between K and the journal), `test_a_stop_right_after_k_is_created_ends_before_the_baseline` (remediation), `…immediately_before_and_after_the_link[2]`, `test_a_flag_during_the_pk_series_ends_it_interrupted`, `test_the_pk_series_reads_the_flag_at_each_wake_up_and_settles_its_subject`, `test_hl_concurrent_stop_during_a_running_pass`; P SIGTERM in AV-1, stop job in HL |
| RT2.AM0.1 | H `test_a2_digest_mismatch…`, `test_a2_content_outside_its_grammar_is_invalid_authority[9]`, `test_a2_v3_helper_and_h2_pins_outside_their_grammar_are_invalid_authority[10]`, `test_a_tool_that_does_not_hash_to_a2s_pin_is_invalid_authority[4]`, `test_an_oversized_pass_document_is_refused`; R `[hold]` |
| RT2.AM0.2–3 | H `test_another_boot…`, `test_run_not_on_tmpfs…`, `test_unsafe_parents_are_refused[6]` (writable, symlink × three parents), `test_an_acl_on_a_parent_is_refused` |
| RT2.AM0.4, .6 | H `test_every_absence_condition_is_rechecked[9]` (incl. a dangling symlink and `/run/nextroot`); P `test_a_second_activation_is_refused_and_leaves_the_first_intact` |
| RT2.AM0.5 | H `test_the_three_load_state_reads[5]`; P `test_a_preloaded_backstop_name_stops_at_am0` |
| RT2.AM0.7 | gap row: deliberately no operation (module docstring) |
| RT2.AM0.8–10, .17 | H (remediation, S0 consequence of .8) the "K before the ACT journal" section listed above; `test_k_is_created_exclusively_and_locked_until_hold_start`, `test_a_k_that_cannot_be_locked_is_lock_object`, `test_a_k_collision_between_recheck_and_creation_is_lock_object`, `test_the_k_adapter_try_once_states` |
| RT2.AM0.11–14 | H `test_bsp_retries_within_five[0,1,5]`, `test_six_unstable_reads_are_capture_baseline_unstable` (6 reads, 5 sliced waits), `test_a_capture_read_error_is_never_a_baseline[3]`, `test_a_busy_capture_unit_is_capture_busy_at_act[6]` |
| RT2.AM0.15–16 | H `test_the_act_directory_must_be_the_operators_0700_directory[5]`, `test_run_start_is_exactly_the_complete_am0_16_line` (exact first-line bytes), `test_a_run_start_outside_the_complete_grammar_is_refused_and_invalid[21]`, `test_every_act_journal_failure_point_fails_closed_and_recovers[write,fsync]` (every journal write and flush of a complete run: each ends non-zero — except a failure of one of the two final best-effort lines, `igr` or `run-end`, which leaves the normal HL end — no grant survives, stop-post recovers); P success test (complete key set, A-2/tool values, K's real identity) |
| RT2.AK1.1–4 | H `test_backstop_intent_is_durable_before_the_single_di3_call`, `test_an_unconfirmed_or_refused_di3_fails_closed_without_retry[7]`, `test_di3_through_the_real_adapter_over_a_scripted_bus[7]` (done, `UnitExists`, timeout, disconnect, lost reply, late completion, failed job — one send each), `test_a_timer_that_is_not_active_after_di3_fails_closed[3]`; adapter `test_create_backstop_request_shape` (exact properties); P timer created `active`, fires, disarms |
| RT2.AM1.*, AM1R.1 | H complete run, `test_published_objects_have_their_accepted_identity_and_grant_id_names_the_rule`, `test_a_squatted_temporary_name_is_preexisting_path[p,r]`, `test_the_seal_records_the_inventory_and_the_rename_never_replaces`, `test_rename_without_noreplace_support_refuses`, `test_tree_r_is_built…`, `test_tree_r_tops_at_rules_d…`, `test_every_pf_and_pt_content_failure_point_fails_closed[write,fsync]`, `test_a_short_pf_write_is_completed_by_the_write_loop`; P late-directory test (real tree R) |
| RT2.AM1G.1–3 | H `test_the_staged_rule_must_match_its_pins[5]`, `test_grant_id_is_durable_before_the_link`, identity test |
| RT2.AM2.1–6 | H `test_the_stop_flag_immediately_before_and_after_the_link[2]`, `test_a_rule_that_appears_before_the_link_is_foreign_and_kept`, failure sweeps |
| RT2.AV1.1–2 | H `test_a_published_file_damaged_before_av1_fails_closed[pass,rule]`, `test_a_baseline_difference_fails_av1_before_any_polkit_call`; P real baseline equal |
| RT2.AV1.3–4 | H `test_av1_controls_fail_closed_and_cl_runs_rule_first[5]`; P real positive (authorized) and negative (not authorized) controls; `test_a_rules_directory_created_after_polkit_started_fails_closed_at_av1` (28, Polkit `MainPID` unchanged) |
| RT2.AM3.1 | H `test_an_act_record_collision_is_not_act_pass`, `test_a_record_publication_failure_is_not_act_pass`, `test_act_pass_never_precedes_durable_verification`; P `act` record `root:root 0444` `activated`; failed ACT ⇒ CL-7 writes `act` `failed` |
| RT2.AM3.2 | H `test_the_order_of_hold_end_k_release_igr_and_run_end_on_every_end[7]`, `test_an_act_run_end_outside_its_vocabulary_is_refused[4]`, `test_the_run_end_vocabulary_is_every_end_class_plus_internal_error`, `test_a_failed_igr_or_run_end_line_never_keeps_the_grant_or_changes_the_end[4]`, `test_no_igr_or_run_end_exists_without_the_act_journal`; P success (`hold-ended`), late rules directory (`grant-not-seen`), SIGTERM in AV-1 and stop job in HL (`interrupted`), SIGKILL (none) |
| RT2.HS.1–3 | H `test_a_start_before_hold_start_ends_the_activation[4]`, `test_a_failed_hold_start_read_is_observation_failed`, K-held test; P `test_a_start_before_hold_start_ends_the_activation` |
| RT2.HL.1–9 | H `test_hl_terminal_reasons_in_the_accepted_order[19]`, `test_a_never_loaded_capture_unit_ends_only_by_the_window`, `test_hl_polls_every_delta_and_journals_only_changes`, `…window_expiry…`, `…observation_failure…`, `test_hl_does_not_end_while_a_consume_holds_k_and_decides_under_it`, `…rereads_under_the_lock…`, `…pass_failed_early…`, `…capture_unloaded`, `…with_k_unusable…`; P operator start ⇒ `pass-ended` |
| RT2.HL.10 | P `test_lease_expiry_with_a_running_pass_then_backstop_disarm` (`RuntimeMaxSec`=L ⇒ IGR ⇒ stop-post `unit-still-active` ⇒ BS-3 disarm) |
| RT2.IGR.1–5 | H `test_igr_runs_exactly_once_and_a_second_call_is_a_no_op`, `test_an_unexpected_exception_still_runs_igr_once`, `test_igr_never_removes_a_damaged_or_foreign_grant[4]`, `test_an_unremovable_grant_is_reported_and_left_to_cl`, `test_igr_still_removes_when_the_journal_is_broken`, `test_igr_records_the_exact_in_memory_identity_for_every_removal_outcome[6]`, `test_igr_before_am1g_records_explicit_absence`, `test_igr_after_am1g_but_before_the_link_records_the_unlinked_identity`, `test_an_igr_line_outside_its_grammar_is_refused[7]`, `test_an_igr_identity_naming_another_object_is_not_counted_by_cleanup`, `test_a_failed_igr_or_run_end_line_never_keeps_the_grant_or_changes_the_end[4]`; P `test_a_damaged_grant_is_never_removed`, success (`igr.identity` = live `grant.id`), SIGKILL (no IGR ⇒ CL-G) |
| H-PROC.3 (DI-6 subject) | PK/SN `test_a_descriptor_above_65535_is_not_inherited_by_the_ready_subject`, `…above_the_current_soft_limit…`, `…cannot_list_its_descriptors…`, `…survives_closing_is_an_error`; P `test_the_di6_subject_inherits_no_descriptor_above_65535_under_pid1` (remediation) |
| RT2.END.1, SN.1 | P every test: PID 1 runs the exact stop-post after the holder; `test_holder_and_stop_post_killed_then_the_backstop_recovers`; no `rp11_h1.py` process after SIGTERM in AV-1 or at teardown |

## Commands and results

The figures this section recorded for the slice's first tree are superseded. The current
final-tree commands and results are in [Current result](#current-result--grr-exception-safety--2026-10-14).

## Real-host interruption and recovery outcomes

All on `oracle-test` through PID 1 with the production artifact built fresh from the pinned wheel
(every object `root:root`, not group/other writable), synthetic A-2/H-1/pass/rule, a disposable
capture unit in `/run/systemd/system`:

* **Success:** ACT PASS (`act` record `activated`, real positive *authorized* and negative *not
  authorized*, every subject reaped), the backstop timer `active`; `ubuntu` — no sudo, no agent —
  starts `rp11-capture-pass-a.service` under the live grant; HL `pass-ended`; IGR `removed`;
  stop-post `st1-verified` (`first_rung igr`, rule `removed-earlier`); a second `ubuntu` start is
  refused; the backstop's first firing disarms its own timer (BS-2), no second attempt; Polkit's
  `MainPID` unchanged.
* **Late rules directory:** Polkit started without `/run/polkit-1`; the holder builds tree R; AV-1's
  real positive control stays unconfirmed ⇒ `grant-not-seen` (28), IGR `removed`, stop-post removes
  tree R and the rule and verifies; the `act` record is `failed` (CL-7).
* **Signals:** one or two back-to-back `SIGTERM`s in AV-1 ⇒ `interrupted` (35) with exactly one
  `igr`; a stop job in HL ⇒ 35 and no `hold-end`; `SIGKILL` after `hold-start` ⇒ no IGR, stop-post
  CL-G removes the grant (`first_rung cl-g`).
* **Hard cleanup:** holder `SIGKILL`ed, then its stop-post `SIGKILL`ed in CL-4 (a foreign rule kept
  the series running) ⇒ no record; the holder's backstop runs attempt 2 (`trigger backstop`) to
  `st1-verified` and then disarms.
* **Lease expiry:** a running pass at L = 61 s ⇒ PID 1's SIGTERM ⇒ IGR `removed` ⇒ stop-post
  `unit-still-active` (2) ⇒ after the pass is stopped the backstop disarms at BS-3.
* **Duplicate activation:** a second activation with the first live stops at AM-0 (`present`, 21)
  touching nothing; its stop-post keeps every object of the first (nothing attributable) and
  hard-stops; the first's grant and holder are intact; a second holder of the same id is refused
  `exists`.
* **Manager/Polkit restart:** after `daemon-reexec` and a Polkit restart in HL either the pass ends
  normally or (observed in one full run) an HL DI-1 read meets the re-executing manager and the
  activation ends `observation-failed` (34) with IGR `removed` — both verified by stop-post.
* **Damaged grant:** the live rule `chmod 0664` ⇒ IGR `kept-damaged`, stop-post
  `present-damaged-unremoved`, the object kept. **Start before `hold-start`** ⇒ OS-7 (33).
  **Pre-loaded backstop name** ⇒ AM-0 `unit-state` (21), no K, no journal.

## Cleanup

After each root run: no `rp11-*` unit, no `rp11_h1.py` process, nothing under `/run` named `rp11`,
no `/run/polkit-1`, no `/run/nextroot`, no `/var/tmp/rp11-*`, no `/var/lib/freedom-blades-rp11`, no
`/run/systemd/system/rp11-*` and the capture unit `not-found`, `/usr/local/libexec` empty and
`root:root 0755`, `/etc/polkit-1/rules.d` empty, `polkit.service` active. The module fixtures assert
this and it was re-checked by hand. The development copy `/opt/freedom-blades/platform-hold` was
removed. No real secret or player data was used.

## Remaining production risks and recommendation

Both are stated once, for the current tree, in
[Current result](#current-result--grr-exception-safety--2026-10-14).
