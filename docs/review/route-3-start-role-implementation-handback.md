# Handback — Route 3 static `start` role (SA-1)

Date: 2026-10-15 · Implemented by Claude · Status: **accepted by Peter Duscha
for continued non-production development on 2026-10-15** · Production/staging:
unchanged

The acceptance follows independent Codex re-review of the second remediation,
which found no blocking issue. It releases static SA-2 `stop` as the next
implementation slice; it does not assign an implementer or authorize production
or staging activation.

## Delivered behavior

The controlled artifact accepts a fourth fixed vector:

```text
/usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py \
  start <activation_id> <a2_sha256> <lease_seconds> <stop_timeout_seconds>
```

`rp11_h1.parse_role_argv` accepts only that shape (activation-id grammar,
lowercase SHA-256, durations `[1-9][0-9]{0,5}`, lease `61..86400` and stop timeout `60..600`;
no leading zeros, extra operands or alternate spellings) before any bus or state
operation. `adapters/rp11/start.py` builds only a `HolderSpec`;
`application/rp11/start.py` makes one DI-2 `create_holder` call and maps
`ControlOk` → exit 0, `ControlRefused` → 20, `ControlError` → 21
(pre-send) or 22 (`effect not confirmed`). Anything else, or any exception,
is `internal-error` (70). Output is fixed, value-safe text on stderr
(`rp11-start started | refused <reason> | error effect-(not-)confirmed|sent`).
No retry, child, signal, record or wait. The manager adapter still derives the
unit, properties and both PID-1 vectors. Existing `hold`, `stop-post` and
`backstop` vectors and their `INVOCATION_ID` handling are unchanged.

## Environment defect and correction (H-FI.1 / SA1.FI.1)

The Codex draft ran the shared `first_image_controls()`, which read
`/proc/self/environ` and parsed `INVOCATION_ID` before the role was known, so a
malformed/duplicate/oversized value could reject a valid `start`.
`first_image_controls(reads_environment=True)` now takes `False` for `start`,
selected from `sys.argv[1:2] == ["start"]` alone in `__main__`. On that path
`_initial_environment`/`invocation_id_from` are never called; the environment is
still emptied, fds 0–2 checked, fds ≥ 3 closed (verified), signals/mask reset,
umask 022, cwd `/`, and the artifact-integrity checks run unchanged. I also
removed a duplicated `_SECONDS` line in the draft.

## Files

New: `application/rp11/start.py`, `adapters/rp11/start.py`,
`tests/test_rp11_start.py`, `tests/systemd_integration/test_route3_start_host.py`.
Changed: `infra/rp11-h1/{build.py,rp11_h1.py,rp11_roles.py}`,
`application/unit_control.py` (docstring), `tests/test_rp11_h1_artifact.py`,
`tests/test_systemd_unit_control.py`, `tests/web/test_p3_4_static_assets.py`,
`tests/systemd_integration/{test_route3_host.py,test_route3_hold_host.py}`, and
current-state docs (status, active plan, implementation plan, decision/RAID
registers, review README). The active handover and the prompt were not edited.
Both new modules are in the artifact's exact source manifest.

## Requirement → test

- Grammar/bounds/aliases: `test_rp11_h1_artifact.py` parametrized
  accept/reject lists; host `test_artifact_rejects_a_vector_the_adapter_would_never_build`.
- Invalid operand types, no bus opened: `test_invalid_operands_are_refused_before_the_bus_is_opened`.
- One call/no retry, every refusal reason, error classes, unknown result,
  exception, safe diagnostics: `tests/test_rp11_start.py`.
- No environment read: `test_a_valid_start_never_calls_the_environment_reading_helper`,
  `test_no_environment_value_can_change_a_valid_start` (malformed, uppercase,
  short, empty, >1 MiB, well-formed, none), `test_only_the_start_vector_selects_…`.
  The same bad values still refuse `deact`/`hold`/`backstop` with 64.
- Real host (`sudo -n` as `ubuntu`): exact unit properties and `hold`/`stop-post`
  vectors; `refused exists` with first holder untouched; unauthorized (no sudo)
  refused with nothing created; post-send timeout on the real manager → 22,
  exactly one `StartTransientUnit` sent, unit exists, a later start is
  `refused exists`; full lifecycle (ACT → HL → IGR → stop-post → backstop)
  through the role in `test_hold_activates_the_operator_starts_the_pass_…`.

## Results

Local (repo host, `venv-web`): rp11/start/artifact/systemd tests + scope guard
2508 passed, 18 skipped (launch-toolchain not provisioned), 2 failed — see below.

`oracle-test`, fresh hash-pinned artifact, root:
- `tests/systemd_integration/test_route3_start_host.py`: **4 passed**.
- `tests/systemd_integration` (manager/artifact, stop-post, backstop, hold,
  tmpfiles, start): **119 passed, 2 skipped** (547 s). The skips are the two
  fresh-reboot proofs (`FREEDOM_TMPFILES_BOOT_PROOF=1`) already done for the
  tmpfiles slice.
- `test_rp11_h1_artifact.py`, `test_rp11_start.py`, `test_systemd_unit_control.py`,
  `tests/web/test_p3_4_static_assets.py`: **672 passed, 2 skipped, 2 failed**; the
  skips are the root-only RLIMIT cases (hard limit 524288).
- Compile and `git diff --check`: clean.

**Two failures, both in `test_p3_4_static_assets.py`** and identical locally and
on the host: `test_the_discovery_enumerates_untracked_files_rather_than_directories`
("no untracked directory in this tree") and
`test_every_evidence_harness_source_in_the_tree_is_declared` (four undeclared
`tools/phase_5_0_evidence/*` files). They concern evidence-harness sources I did
not touch. I did not run them against the pre-change tree, so "pre-existing" is
my inference, not a verified baseline; I left them alone. The scope-guard tests
for the new production files pass. I did not run the full bot/web/Foundry
comparisons: shared surface is limited to the artifact, a docstring and the
guard enumeration.

## Host cleanup

After the runs: no `rp11*` unit, process, artifact directory, store or
`/run/polkit-1`; `polkit.service` active. Old `/var/tmp/p5-r5-rp11-h0*` evidence
directories pre-date this work and were left alone.

## Remaining risks

- The `sudo` preamble passes its environment unclosed (accepted EX-1 limit); the
  role ignores it.
- The unconfirmed path was injected at the bus connector in-process (as the
  accepted adapter suite does), not by faulting the installed binary.
- The transient inspection-failure decision and final production security review
  remain mandatory before any activation.

## Recommendation

Superseded by the remediation section below. Not accepted; SA-2 remains deferred
until the independent re-review and Peter's acceptance.

## Remediation of the independent review (2026-10-15)

Status: **candidate, uncommitted, awaiting independent Codex re-review — not
accepted.** No maintainer acceptance is recorded.

| # | Finding | Disposition |
|---|---|---|
| 1 | Durations accepted anything in 1..604800 | Fixed. Reproduced first: `parse_role_argv(["start", ACT, A2, "604800", "1"])` returned a role tuple. |
| 2 | Host denial test accepted a pre-send error | Fixed. Now requires exit 20 and `rp11-start refused not-authorized`. |
| 3 | "Duplicate" `INVOCATION_ID` was a mapping assignment | Fixed. Raw `execve` with two entries, end to end. |

**Files.** `application/rp11/start.py` (new `validate_start_durations`),
`adapters/rp11/start.py` (calls it first, inside the existing outer `try`),
`infra/rp11-h1/rp11_h1.py` (`parse_role_argv` calls it), and tests in
`tests/test_rp11_start.py`, `tests/test_rp11_h1_artifact.py`,
`tests/systemd_integration/test_route3_start_host.py`. `HolderSpec`,
`BackstopSpec` and `_seconds` in `application/unit_control.py` are untouched, so
the backstop contract is neither widened nor narrowed.

**Duration rules.** `lease_seconds` 61..86400; `stop_timeout_seconds` 60..600;
canonical ASCII decimal only (`[1-9][0-9]{0,5}`, full match). `start_window_s <
lease_s` is not re-derived (owned by the coordinator). Refused before the bus is
opened or any DI-2 call. Boundary tests: leases 61/86400 accepted; 0, 1, 60,
86401, 604800 refused; stop timeouts 60/600 accepted; 0, 1, 59, 601, 604800
refused; plus `604800/1`, leading zeros, Arabic-Indic digits, sign, whitespace,
trailing newline, hex, exponent, empty. Refused vectors assert no connector call
and no `create_holder` call.

**Raw duplicate environment.** A test-only harness (`python -I -c`, `ctypes`
`execve`) passes an explicit `envp` of `INVOCATION_ID=aaa…`, `PATH=…`,
`INVOCATION_ID=bbb…`. One test proves via `/bin/cat /proc/self/environ` that both
entries arrive. For `start`, the result, state and stderr equal the
empty-environment control; `invocation_id=absent`; environment empty after
first-image controls. `hold`, `deact … stop-post` and `backstop` each exit 64
with `malformed or duplicate INVOCATION_ID` before the role runs. Mutation check:
forcing `reads_environment=True` makes the start test fail. The direct
`_initial_environment` regression is kept. No production dependency added.

**Authorization refusal.** On `oracle-test` the unprivileged exact artifact
invocation returned exit 20 and `rp11-start refused not-authorized`; no unit or
job was created. No fixture change was needed. Fake-boundary pre-send connector
and subscription errors stay as `effect-not-sent` cases in `tests/test_rp11_start.py`.

**Final-tree commands and results** (synced with the documented secret-excluding
rsync; `/opt/freedom-blades/platform` on `oracle-test`).

1. `cd /opt/freedom-blades/platform && /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/test_rp11_start.py tests/test_rp11_h1_artifact.py tests/test_systemd_unit_control.py tests/web/test_p3_4_static_assets.py`
   — **728 passed, 2 skipped, 2 failed.** Skips: 2× `RLIMIT_NOFILE` above
   1048583 (hard 524288). Failures: `test_p3_4_static_assets.py::test_the_discovery_enumerates_untracked_files_rather_than_directories`
   and `::test_every_evidence_harness_source_in_the_tree_is_declared` (five
   undeclared `tools/phase_5_0_evidence/*` files). **Verified against baseline:**
   a clean worktree of `a447558` fails the same two tests (109 passed, 2 failed,
   run locally with the repo `venv-web`). Not caused by this work; left alone.
2. `sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_RP11_WHEEL=/home/ubuntu/jeepney-0.9.0-py3-none-any.whl /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/systemd_integration`
   — exit 0, **119 passed, 2 skipped** (554 s), fresh artifact from the pinned
   wheel. This covers `test_route3_start_host.py` (4 passed when run alone,
   24 s) and the manager/artifact, `stop-post`, `backstop`, `hold` and tmpfiles
   suites. Skips: the two fresh-reboot proofs (`FREEDOM_TMPFILES_BOOT_PROOF=1`).
3. Local: `venv-web/bin/python -m pytest -q tests/test_rp11_start.py tests/test_rp11_h1_artifact.py` — 197 passed, 2 skipped (same RLIMIT reason) before the final
   test additions; the same files are in command 1.
4. `python -m compileall` over the touched trees: exit 0. `git diff --check`: exit 0.

The production-file scope guard is the `test_p3_4_static_assets.py` module in
command 1 (apart from the two baseline failures above). The full bot, web and
Foundry suites were **not** run: shared production validation
(`application/unit_control.py`) did not change in this remediation.

**Host cleanup.** After the root runs: no `rp11*` unit or process, no
`/run/polkit-1`, `/var/tmp/rp11-act-*`, `/var/lib/freedom-blades-rp11` or
`/usr/local/libexec/freedom-blades-rp11`; `polkit.service` active. Pre-existing
`/var/tmp/p5-r5-rp11-h0*` directories were left. `/var/tmp/sa1-root.log` is the
root-run log.

**Remaining production risks.** The `sudo` preamble passes its environment
unclosed (accepted EX-1 limit; the role ignores it). The unconfirmed path is
injected at the bus connector, not by faulting the installed binary. The
`start_window_s < lease_s` relation must be enforced by the coordinator. The
transient inspection-failure decision and final production security review remain
mandatory before activation.

**Recommendation.** Accept SA-1 for continued non-production development after
the independent re-review; no named blocker remains.

## Second remediation — 2026-10-15 (malformed `ControlOk` false success)

**Finding and disposition.** `StartProcedure.run()` promoted any `ControlOk` to
`started`, so `ControlOk(None)` printed `rp11-start started` and exited 0. Fixed:
success now requires a `JobCompletion` whose `unit == spec.unit_name` and whose
`job_path` fully matches `/org/freedesktop/systemd1/job/[0-9]+` (ASCII digits,
`fullmatch`; the shape the accepted adapter emits). Anything else after the one
DI-2 call is `StartOutcome(ERROR, "malformed-success", effect_not_confirmed=True)`:
no retry, exit 22, fixed line `rp11-start error effect-not-confirmed`, no value,
unit or path in output (the error detail is never printed). Validation is local
to `application/rp11/start.py`; the manager adapter and `unit_control.py` are
unchanged.

**Regressions (written first; all 11 failed before the fix).** In
`tests/test_rp11_start.py`: `ControlOk(None)`; non-`JobCompletion` object (with
matching `unit`/`job_path` attributes); other unit; empty, short (`/job/1`),
id-less, non-digit, Arabic-Indic digit, trailing-newline and `None` paths; `None`
unit. Each asserts one `create_holder` call, exit 22 and the fixed line. The valid
case uses the real job-path shape and asserts one call, `started`, exit 0. Earlier
fixtures that used `"/job/1"` now use the real shape.

**Principal files.** `application/rp11/start.py`, `tests/test_rp11_start.py`,
`docs/review/Handover information`, this handback.

**Final-tree commands and results** (rsync per the documented secret-excluding
command; `oracle-test`, `/opt/freedom-blades/platform`).

1. `/opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/test_rp11_start.py tests/test_rp11_h1_artifact.py tests/test_systemd_unit_control.py`
   — exit 0, **631 passed, 2 skipped, 0 failed**. Skips: 2× `RLIMIT_NOFILE` above
   1048583 (hard 524288).
2. `sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_RP11_WHEEL=/home/ubuntu/jeepney-0.9.0-py3-none-any.whl /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/systemd_integration/test_route3_start_host.py`
   — exit 0, **4 passed** (23.8 s), fresh artifact from the pinned wheel.
3. Same command over `tests/systemd_integration` — exit 0, **119 passed, 2 skipped**
   (539 s). Skips: the two fresh-reboot proofs (`FREEDOM_TMPFILES_BOOT_PROOF=1`).
4. `… -m pytest -q -rfEs tests/web/test_p3_4_static_assets.py` — exit 1, **109
   passed, 2 failed**: `test_the_discovery_enumerates_untracked_files_rather_than_directories`
   and `test_every_evidence_harness_source_in_the_tree_is_declared` (five
   undeclared `tools/phase_5_0_evidence/*` files). Identical to the baseline
   comparison against `a447558` recorded in the first remediation (109 passed,
   2 failed); not caused by this work.
5. Local, repo root: `python3 -m py_compile` over every touched Python path
   (`application/rp11/start.py`, `adapters/rp11/start.py`, `application/unit_control.py`,
   the touched tests and `infra/rp11-h1/*.py`) — exit 0. `git diff --check` — exit 0.

The full bot, web and Foundry suites were not run: no shared production boundary
or bot/web/worker/Foundry surface changed.

**Active handover at remediation return.** It then stated that the first remediation was complete, the
re-review found this one blocker, the second remediation is in progress/returned,
SA-1 is unaccepted and SA-2 deferred pending re-review and Peter's acceptance.
Activation gates are unchanged; no acceptance is recorded.

**Host cleanup (verified after the root runs).** No `rp11*` unit or process; no
RP-11 Polkit rule (`/run/polkit-1`, `/etc/polkit-1/rules.d`), artifact
(`/usr/local/libexec/freedom-blades-rp11`), staging/store
(`/var/lib/freedom-blades-rp11`) or `/var/tmp/rp11-act-*`. **Removed
`/var/tmp/sa1-root.log` and confirmed it absent.** The pre-existing
`/var/tmp/p5-r5-rp11-h0*` directories (six) were left. `polkit.service` active.
Production and staging untouched.

**Remaining production risks (unchanged).** The `sudo` preamble environment is
unclosed (accepted EX-1 limit). The unconfirmed path is injected at the bus
connector. `start_window_s < lease_s` must be enforced by the coordinator. The
transient inspection-failure decision and final production security review remain
mandatory before activation.

**Recommendation.** Accept SA-1 for continued non-production development after
independent re-review; no named blocker remains.

## Acceptance

Peter Duscha accepted SA-1 for continued non-production development on
2026-10-15 after independent Codex re-review found no blocking issue. The
acceptance supersedes the remediation-return status and recommendation above.
The reviewer independently reproduced the final-tree results on `oracle-test`:
631 focused tests passed with 2 expected RLIMIT skips; the SA-1 host module
passed 4 tests; and the complete Route 3 systemd integration suite passed 119
tests with 2 expected fresh-reboot-proof skips. The scope guard reproduced its
documented unrelated baseline of 109 passed and 2 failed. Compilation,
`git diff --check`, and host cleanup checks passed.

Production and staging activation remain unauthorized. The transient
inspection-failure decision and final independent production security review
remain mandatory before activation.
