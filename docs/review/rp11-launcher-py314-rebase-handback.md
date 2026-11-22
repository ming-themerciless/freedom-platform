# RP-11 launcher Python 3.14 rebase — implementation handback (launcher slice and regenerated manifest complete; Codex independent review passed)

**Date:** 2026-11-21 · Scope: launcher/contract slice only, per the accepted
[capture service design proposal](rp11-capture-service-design-proposal.md) §4
step 1. No production or staging action. No commit.

## Delivered

- `infra/rp11-launch/launch.c`: both `execve` literals changed from
  `/usr/bin/python3.12` to `/usr/bin/python3.14`.
- `tools/phase_5_0_evidence/rp11_launch.py`: `EXECVE_PATH` and `EXECVE_ARGV[0]`
  changed to `/usr/bin/python3.14`; argv still ends in
  `/usr/local/libexec/freedom-blades-rp11/rp11_entry.py run --pass A` (blocker 3).
- **Real build available.** The gated R-1/R-2 build of this tree was run on
  `oracle-test` from a fresh signed snapshot by the maintainer's side; it passed
  and the build-root manifest matched. Its products were copied byte-for-byte to
  `tools/_codex-work/rp11-py314-build-out/` (input only; left in place for Codex
  review; not part of the delivered tree). I did not run the build myself and
  have no transcript of its exact invocation. The canonical one is the
  `build.sh` header: `/usr/bin/env -i LC_ALL=C PATH=/usr/bin SOURCE_DATE_EPOCH=0
  TZ=UTC0 /bin/sh infra/rp11-launch/build.sh build-out` as the first process in
  the verified build root.
- What the artifacts show (checked with `sha256sum`/`grep` only):
  `cc1.v` is byte-identical to the committed baseline fixture
  (`e99cee65…`, 5305 bytes), and `rp11-launch.map` is unchanged
  (`5a8b0580…`). Image, listing and `launch.s` changed, as expected for a
  `.rodata`-only edit; the rebuilt `.rodata` contains `/usr/bin/python3.14`.
- Updated from the actual artifacts (copied or hashed, nothing typed by hand):
  - `infra/rp11-launch/rp11-launch.x86_64.listing` (copy; sha256 `49810822…`
    equals the build output).
  - `infra/rp11-launch/expected.sha256`: image `7e2b7bde…`, listing
    `49810822…`, map `5a8b0580…` (unchanged), `launch.s` `3d65779e…`.
  - `rp11_launch.py`: `EXPECTED_IMAGE_SHA256`, `EXPECTED_LISTING_SHA256`,
    `EXPECTED_LAUNCH_S_SHA256` set to the same values.

## Verification

1. **XD (decoder agreement) — attributed to Codex.** Codex ran the existing
   decoder on the rebuilt image and listing: verdict `pass`, 332 instructions,
   no failures, stream SHA `e1354c29…8baa8edbf8e0` (equal to the committed
   `AGREED_STREAM_SHA256`, `rp11_launch.py:216`), image `7e2b7bde…c67e`,
   listing `49810822…cdfc9`. No constant changed. I did not run XD myself.
2. **Manifest and concrete plan regenerated.** The canonical generator command
   **was run successfully in Claude's prior turn**; it printed
   `DRY RUN — nothing was executed` and regenerated the review manifest and the
   concrete plan. The manifest is `manifest_version` **32**
   (`review_manifest.py`, `MANIFEST_VERSION = 32`, with its version-32
   commentary), digest
   `318b9a18765a73c243993548fb2f3df51ecdc705f3002145cbdc401c9737e15a`, and
   carries the new image/listing/`launch.s` digests (`49810822…`, `3d65779e…`).
   The concrete plan's only change is the review-manifest digest line
   (`448f2805…` → `318b9a18…`). (An earlier revision of this handback said the
   run was not observed; that was wrong and is corrected here.)
3. **Test pin.** `tests/phase_5_0_evidence/test_r16_remediation.py` expected
   version moved 31 → 32 with a concise version-32 commentary entry. This is the
   intentional generated-manifest bump; no semantic assertion was changed or
   weakened.
4. **Claude local focused run.** `/opt/freedom-blades/runtime/venv-web/bin/python -m
   pytest -q tests/test_rp11_launch_source.py tests/test_rp11_launch_gate.py
   tests/phase_5_0_evidence` → **4080 passed**, no skips (`-rs`). Toolchain tests
   needing the build root were not run locally.
5. **Codex on `oracle-test`, dedicated launcher tests** (source, gate,
   toolchain, cc1 determinism): **713 passed**.
6. **Codex on `oracle-test`, broader launcher + Phase 5 run:** **4092 passed,
   4 failed, 0 skipped observed.** All four failures are safety-sentinel tests
   unrelated to the launcher: `test_lab_call_graph.py`,
   `test_lab_implementation.py`, `test_lab_integration.py` and
   `test_lab_live_authority.py`. Each refuses to run because a **pre-existing**
   `/run/freedom-blades/laboratory.lock` exists. Codex read metadata only: an
   empty regular file `root:freedomlab` 0660 in a directory `root:freedomlab`
   0750, timestamps 2026-11-08; no process and no matching systemd unit was
   found; **no host state was changed.** Disposition: the sentinels are correct
   and are not relaxed, and the pre-existing lock is not deleted by this slice.
   The four failures are an `oracle-test` environment condition, not a launcher
   regression; the lock's fate is a maintainer decision.

## Not done

- **Runner/entrypoint not implemented, SA-2 build not changed.** `rp11_entry.py`
  does not exist; `infra/rp11-h1/build.py` and `ROUTE3_SA2_TREE_SHA256` are
  untouched. Missing contract before it can be written: the exact Pass A step
  list and the role vectors it composes; capture outputs, evidence paths and the
  `run-start`/`INVOCATION_ID` pairing the `consume` role expects; per-child-command
  deadlines and timeout finalization (no whole-service runtime bound is claimed);
  and the open production service identity.
- No commit made. Product requirements, RP-11 wiring and PO-9/PO-14 unchanged.

## Entrypoint source audit (2026-11-21, read-only) — result: NOT derivable; no code written

Sources searched: `execution/capture_mechanism.py` (module docstring, API),
`capture_contract.py`, `plan.py`, `execution/boundary.py` (`StreamCaptureLauncher`),
`infra/rp11-h1/rp11_h1.py`, `application/rp11/consume.py`,
`adapters/rp11/consume.py`, the active handover, the design proposal, the
capture-mechanism review
`project-review-2026-09-28-p5-r5-rp11-capture-mechanism.md`, the Pass A
section (§6, §9.5) of the P5.0-R5 authorization prompt, and the `rp11_entry`
design in the C-11 launcher-contract proposal (§ file table, line ~2072). No
`rp11_entry.py`, no `run --pass A` implementation and no `run-start` pairing
consumer exists in code. No entry module or test was added; SA-2 build,
fragment, activation and host state are untouched.

| # | Missing behavior | What the sources say | Verdict |
|---|---|---|---|
| 1 | **Exact Pass A command sequence** | Authorization prompt §6 (A0-xx/A1-xx) is an operator runbook: local `git`/`sha256sum`/pytest, then `rsync --delete` and `ssh oracle-test "…"` steps, with `⟨MI.*⟩`/`⟨PIN.*⟩` placeholders (`MI.pinned_commit`, `MI.capture_root_A`, `PIN.capture_tool_sha256`) the prompt itself marks "not admissible: RP-11 and the A-6 and MI inputs are unmet". `plan.is_executable` is `False`. Nothing maps this to the unattended service `run --pass A`, and an ssh/rsync-to-`oracle-test` pass from a production service is itself unaddressed (identity, keys, network). | missing |
| 2 | **Capture filenames, index and finalization** | Specified (`capture_contract.py` layout table; `CaptureSession`: X-1 genesis, P-1…P-8, X-2, one X-3, X-4; `HandbackBinding`). But the mechanism "is not wired": no code constructs a session outside tests, and the 2026-09-28 review of it is **changes requested**, not accepted (RP11-I1-1 publication contract, RP11-I1-2 reproducibility), with C-11 routing, pinned launcher environment, §14 binding block and tool-digest scope still open. Where `MI.capture_root_A` and the tool digest come from at run time is unspecified. | specified but unaccepted; inputs missing |
| 3 | **`consume` / `run-start` pairing** | `run-start` is the first line of the ACT journal, written by `consume` (CQ-2) into `<var_tmp>/<id>-consume-evidence`; `consume` takes only `INVOCATION_ID`. No source says what the entry must read from, write to or compare against it (the C-11 entry design says only that it checks `INVOCATION_ID` and parent PID 1 and reads `/etc/freedom-blades-rp11/pass-a.json`). Whether the main process's `INVOCATION_ID` equals the pre-step's, and how capture evidence is bound to the consume record, is unstated. | missing |
| 4 | **Child timeout behavior** | `ActRequest` and `ProcessLauncher.launch` carry **no timeout parameter**; `StreamCaptureLauncher` takes only a drain time and a byte bound. The proposal §4 requires an explicit per-child deadline plus one finalization attempt, and says the design stays "not ready" otherwise. No per-act deadline values, exit-outcome mapping or timeout-finalization test exists. | missing |
| 5 | **Service identity and environment** | Production identity open (proposal §3/§8). `rp11-entry-env/1` and the C-11 launcher environment are Python 3.12/`ubuntu` era text, not re-accepted for 3.14. | open |

Conclusion: stopping per instruction. A byte-exact `rp11_entry.py` would require
inventing the step list, input sourcing and timeout semantics, which the
proposal explicitly forbids. Needed from the maintainer before the entry slice:
a re-based, accepted Pass A step list with its inputs (rows 1, 5), the consume
pairing rule (row 3), per-command deadlines and a finalization-on-timeout rule
extending `ActRequest` (row 4), and a decision on the unaccepted capture
mechanism review findings (row 2).

## Independent review outcome (Codex, 2026-11-21): passed, no blocking findings

Codex verified: source and contract both use `/usr/bin/python3.14`; the
regenerated manifest is version 32 and carries the same constants; the committed
`expected.sha256` values match the build hashes recorded above; the listing
rodata is 3.14; `git diff --check` is clean; the dedicated `oracle-test` suite
previously passed 713. The broad suite was 4092 passed with 4 environment
sentinel failures caused by the pre-existing `/run/freedom-blades/laboratory.lock`
(not removed or changed by Codex); these are not launcher defects.

Limitations preserved: the entrypoint contract is unresolved; no entrypoint, no
SA-2 fragment and no production step exists or is authorized; no production or
staging action was taken.

## Next action

The runner/entrypoint slice, once the blockers in the audit table above are
settled by the maintainer.

## Remediation: raw initial environment, fail-closed (Codex blocking finding, 2026-11-21)

Defect: `_initial_environment()` in `infra/rp11-h1/rp11_entry.py` fell back to the
normalized `os.environb` when `/proc/self/environ` could not be opened. That
mapping cannot show a duplicated `INVOCATION_ID`, so a valid-looking value could be
accepted where the contract requires exactly one raw occurrence.

Fix: `_initial_environment()` now returns `None` when the raw block cannot be
opened or read completely (open or read `OSError`); there is no mapping fallback.
`first_image_controls()` treats `None` like an oversize block: it refuses with
status 64 before `os.environ.clear()`. The same change is made to the byte-identical
shared function and caller in `infra/rp11-h1/rp11_h1.py`, which carried the same
defect and is held equal by `test_the_shared_first_image_and_tree_checks_equal_rp11_h1s`.
Note `rp11_h1.py` is therefore modified: any installed-host artifact hash or
evidence that pins it must be rebuilt before reuse.

Tests added to `tests/test_rp11_entry.py`: an unreadable `/proc/self/environ` with a
valid mapped `INVOCATION_ID` is refused (entry and role modules), the environment is
not cleared, and a failing `read` yields `None`.

Results (repo `venv-web`, local, serial):
* `tests/test_rp11_entry_artifact.py`, `test_rp11_entry.py`, `test_rp11_h1_artifact.py`,
  `test_rp11_capture_unit_install.py`, `test_rp11_capture_unit_install_cleanup.py`:
  514 passed, 2 skipped (RLIMIT_NOFILE cannot be raised above the hard limit).
* `tests/phase_5_0_evidence/test_rp11_capture.py`, `test_rp11_retention.py`,
  `tests/test_rp11_cleanup.py`: 696 passed.
* Not run: the full suite and `oracle-test`. No production or staging action taken.
