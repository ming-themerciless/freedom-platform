# RP-11 G11/G12 implementation — handback (2026-11-21)

Scope: the two accepted decisions of the [Pass A entry contract](rp11-pass-a-entry-contract-proposal.md) §0,
implemented and tested locally for `oracle-test`. **Nothing here accepts G1–G10, runs Pass A, rebuilds, installs
or activates SA-2, or touches production or staging.** The safety sentinel (G8) is not amended.

**Review status (updated 2026-11-21):** independent Codex review of the G11/G12 code and tests passed with no remaining blocking findings. Codex-run post-remediation results (local Python 3.14.4 `venv-web`; not `oracle-test`, not canonical suites): `tests/test_rp11_entry.py tests/test_rp11_entry_artifact.py tests/test_rp11_h1_artifact.py tests/test_rp11_capture_unit_install.py tests/test_rp11_capture_unit_install_cleanup.py` 520 passed, 2 skipped (`RLIMIT_NOFILE` cannot be raised above hard limit 524288); `tests/phase_5_0_evidence/test_rp11_capture.py tests/phase_5_0_evidence/test_rp11_retention.py tests/test_rp11_cleanup.py` 696 passed, 0 skipped. These supersede the author-run figures below. See the [entry-bootstrap handback](rp11-entry-bootstrap-g11-g12-handback.md).

**Progress (2026-11-22): G11 start-time binding implemented, inert and unwired.** `tools/phase_5_0_evidence/execution/start_binding.py` provides `require_start_binding(activation_id, invocation_id, consume_journal_bytes)`: pure and read-only (no filesystem, process, network or environment access; no capture session, no command), it reuses `application.rp11.journal` (`parse_journal`, `JournalKind.CONSUME`, `consume_run`), `validate_activation_id` and `require_invocation_id`, and refuses an invalid journal, a torn tail, a malformed or missing `run-start`, a foreign activation or run, an invalid ID or an `invocation_id` mismatch with a fixed reason code only (no ID or journal bytes). It validates the journal records supplied and the invocation pairing; it deliberately does not establish lifecycle completion or require terminal `run-end`, so its caller must rely on successful consume `ExecStartPre` sequencing. Its 4 MiB input cap matches `ACT_FIRST_READ_BYTES`. It is added to `build.ENTRY_SOURCES` (closure tests take it as a second root); `rp11_entry.main` is unchanged and does not import or call it, so the entry stays inert and `create_capture_session`/`StreamCaptureLauncher` stay unwired. New focused unit tests: `tests/test_rp11_start_binding.py`. **Codex source review found and Claude remediated the overstated lifecycle docstring and 1 MiB cap; follow-up source review found no remaining blocking findings.** Syntax parsing and `git diff --check` pass.

**Focused `oracle-test` verification (2026-11-22):** after the documented secret-excluding rsync sync, ran as root with Python 3.14.4 `venv-web` and a root-owned basetemp under `/root`:
`tests/test_rp11_start_binding.py tests/test_rp11_entry.py tests/test_rp11_entry_artifact.py tests/test_rp11_h1_artifact.py` — **421 passed, 3 skipped** in 53.21s. Pytest reported: “root-owned objects are accepted for every required owner”; “as root the test tree is root-owned”; and “as root this tree (not root-owned) is refused; see the test above.” The first attempt used pytest's default `/tmp` basetemp and yielded 272 passed, 2 failed, 150 setup errors because the artifact builder correctly rejected `/tmp` as an unsafe root build parent; rerunning with `--basetemp=/root/rp11-g11-tests-20261122` passed. That generated 3.4 MiB pytest directory was removed after the run. This was source/unit testing only: no SA-2 build, systemd operation, production test or operational Pass A. No source was acquired from the canonical GitHub remote. G1, G4 and G8 are unchanged. The "pairing is not implemented" risk below is superseded only for the check itself, not for its use by the entry.

Exact invocation:

```text
ssh oracle-test "cd /opt/freedom-blades/platform && sudo -n /opt/freedom-blades/runtime/venv-web/bin/python -m pytest -q -rs -o tmp_path_retention_policy=failed --basetemp=/root/rp11-g11-tests-20261122 tests/test_rp11_start_binding.py tests/test_rp11_entry.py tests/test_rp11_entry_artifact.py tests/test_rp11_h1_artifact.py"
```

## Delivered

**(A) G11, `INVOCATION_ID` provenance.**
- `capture_contract.py`: `INDEX_SCHEMA` `/2`→`/3`, `BINDING_FORMAT` `/1`→`/2`. `IndexState` gains `invocation_id`
  (after `tool_sha256`), serialized and parsed under exact keys; `HandbackBinding` gains `invocation_id` (second
  field, eight-key block). New `require_invocation_id` / `INVOCATION_ID_PATTERN`: `str`, `fullmatch` of
  `[0-9a-f]{32}`, so no uppercase, newline, whitespace, dash or non-string. A test keeps the pattern equal to
  `rp11_launch.INVOCATION_ID_GRAMMAR`. `CaptureRecord` and `RECORD_SCHEMA` are unchanged (golden key test).
- `capture_mechanism.py`: `GenesisRequest.invocation_id` is validated in `__post_init__`, **before any root is
  created**. Genesis, every open state, the final state and `binding()` carry it.
- `retention_check.py`: X-4 (`verify_final_state`, `RetentionCheck`) requires the final state and every chain
  state to equal the expected value; B0-RA takes it from the binding, so a binding that differs from the final
  state's stops. Chain states re-linked by digest but differing stop as `chain-inconsistent`.
- Old schemas: exact-schema readers, no migration, no dual reader (`/2` index and `/1` binding are refused:
  `schema-mismatch` / `malformed-binding`).
- Callers updated: `rp11_fixtures.py`, `test_rp11_capture.py`, `test_rp11_retention.py`. No other constructor,
  parser or serializer exists (searched `tools/`, `tests/`, `infra/`, `application/`).

**(B) G12, fixed SA-2 loading substrate.**
- `infra/rp11-h1/rp11_entry.py` (new): `run --pass A` only. Same first-image controls and tree check as
  `rp11_h1.py` (copied; AST-equality tests keep them equal), with two deliberate differences: root ownership is
  required **whatever the caller's uid** (the entry runs non-root; `rp11_h1.py` skips the check for non-root), and
  `INVOCATION_ID` must be present exactly once and well formed (else 64). The tree check runs before `lib/`
  is appended after the stdlib; no bytecode; the one import is `capture_mechanism`, which must load from `lib/`.
  It then prints "not implemented" and **exits 69**. It calls no mechanism function, starts no process or
  connection, and touches no capture root.
- `build.py`: new `ENTRY_SOURCES` (the 16-file closure: 15 under `tools/`+`application/idempotency.py`, with
  package `__init__`s, no third-party), copied into `lib/`, and `rp11_entry.py` placed beside `rp11_h1.py`.
  The existing `SOURCES` and its test are unchanged.

## Tests (new/changed)

`tests/phase_5_0_evidence/test_rp11_capture.py` and `test_rp11_retention.py` (G11: genesis/all states/binding carry
the value; 12 malformed values refused at request, state, parse and binding, with no root created; old/new schema
refusal; record golden; digest chain binds the field; binding, final-state and re-chained-state mismatch stop X-4/B0-RA)
and new `tests/test_rp11_entry_artifact.py` (G12: closure equals AST closure both ways; built tree contents and modes;
shared checks equal; inert by AST and by audit hook; hostile `PYTHONPATH`, cwd and stray sibling package never
imported, `sys.path` = stdlib + `lib` last; bad `INVOCATION_ID`/argv refused with nothing loaded; tampered
mode/dir/symlink/FIFO/stray/owner refused with 77 before any import; a non-root-owned bundle refused end to end).

## Results (local host, Python 3.14.4 venv-web, user `foundry`, no `TEST_DATABASE_URL`)

- `test_rp11_capture.py test_rp11_retention.py test_rp11_h1_artifact.py test_rp11_entry_artifact.py`:
  **767 passed, 2 skipped** (the two `RLIMIT_NOFILE` cases, reason printed).
- Wider, to find collateral breakage: `tests/phase_5_0_evidence tests/test_rp11_h1_artifact.py
  tests/test_rp11_entry_artifact.py tests/test_route3_release_record.py tests/test_provisioning_plan.py
  tests/test_rp11_capture_unit_install*.py`: **4326 passed, 1 failed, 221 skipped** (root/oracle-test-only skips).
- The one failure, `test_route3_release_record.py::test_the_read_only_verifications_also_run_the_whole_gate[S2.1]`
  (libc6 payload drift / `user@995.service` mutation log), fails deterministically in isolation. It reads no file I
  changed, and the runbook and `test_provisioning_plan.py` are uncommitted-modified by earlier work, but I could not
  compare against a clean HEAD (worktree creation failed on a read-only `.git`). **Not claimed pre-existing**; it
  needs the check on `oracle-test`.
- Not run: `oracle-test` suites, real-systemd test (contract §3 item 5g), the root-owned positive path of the entry.

## Remaining / risks

- **Review manifest and concrete plan are stale.** `capture_contract.py`, `capture_mechanism.py` and
  `retention_check.py` changed, so their pinned digests in `phase-5-0-evidence-harness-review-manifest.json` and
  `RP11_SOURCES`/tool digest no longer match; no test fails on it. I did not regenerate them (generator command not in
  the repo docs; version bump). Regenerate before any pin.
- **Updated 2026-11-22:** the inert entry's root-owned bootstrap path and the pure
  `INVOCATION_ID`↔consume `run-start` pairing check were exercised by the focused
  root run on `oracle-test` (421 passed, 3 expected identity-specific skips).
  The operational Pass A path is still absent. The pure pairing check is at
  `tools/phase_5_0_evidence/execution/start_binding.py`, included as a second
  `ENTRY_SOURCES` root, and remains unwired because the entry is inert. It
  checks pairing, not lifecycle completion. No canonical-remote source
  acquisition occurred. G1/OP1 and A-2 authorization boundaries remain
  unchanged.
- SA-2 tree digest changes at the next build (unauthorized). Independent review of the entry and tree checks is
  required before any rebuild, install or activation.
- A parallel writer added `tests/test_rp11_entry.py` (untracked, not mine, 349-test run passes with it). It overlaps
  `test_rp11_entry_artifact.py`; consolidate before commit. Unrelated workspace changes are untouched.

## Changed files

Modified: `tools/phase_5_0_evidence/capture_contract.py`, `execution/capture_mechanism.py`,
`execution/retention_check.py`, `infra/rp11-h1/build.py`, `tests/phase_5_0_evidence/rp11_fixtures.py`,
`test_rp11_capture.py`, `test_rp11_retention.py`. New: `infra/rp11-h1/rp11_entry.py`,
`tests/test_rp11_entry_artifact.py`, this handback.
