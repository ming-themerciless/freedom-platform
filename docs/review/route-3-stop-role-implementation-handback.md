# Handback — Route 3 static `stop` role (SA-2)

Date: 2026-10-15 · Implemented by Claude · Status: **accepted by Peter Duscha
for continued non-production development on 2026-10-16 after independent Codex
re-review found no blocking issue.** Production/staging: unchanged and unauthorized.

## Delivered behavior

The controlled artifact accepts a fifth fixed vector, with no operand:

```text
/usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py stop
```

`rp11_h1.parse_role_argv` accepts only `["stop"]`; every extra token, option,
alias, case/whitespace variant or unit name returns `None` (exit 64) before any
bus is opened. `adapters/rp11/stop.py::run_stop` builds the manager adapter and
`application/rp11/stop.py::StopProcedure` makes **one** `stop_capture_unit()`
(DI-S) call. The caller supplies no unit, mode, bus or argument; the accepted
adapter still issues only `StopUnit(rp11-capture-pass-a.service, "fail")`.

| DI-S result | Role result | Exit | stderr |
|---|---|---|---|
| `ControlOk(StopCompletion(STOPPED, JobCompletion(fixed unit, /org/freedesktop/systemd1/job/<ASCII digits>)))` | stopped | 0 | `rp11-stop stopped` |
| `ControlRefused(reason)` (`not-loaded`, `invalid-request`, `not-authorized`, `exists`) | refused | 20 | `rp11-stop refused <reason>` |
| `ControlError`, pre-send | error | 21 | `rp11-stop error effect-not-sent` |
| `ControlError`, post-send, **or any malformed `ControlOk`** | error | 22 | `rp11-stop error effect-not-confirmed` |
| exception / unknown result type | internal error | 70 | `rp11-stop internal-error` |

No retry, child, signal, record, wait or additional read; no unit-state, journal
or capture-root access (OC-1..OC-3 and `start-pre` exclusion stay with the
executor). A completed `done` stop is `stopped` whether the unit was active,
inactive or failed; there is no `already-stopped` result and the observed state
never changes the result. Output never contains exception text, D-Bus detail,
paths or environment values.

**Environment (H-FI.1).** `stop` reads no environment variable. `__main__`
selects `first_image_controls(reads_environment=False)` from
`sys.argv[1:2] in (["start"], ["stop"])` alone; the environment is still emptied
and all other first-image checks and artifact-integrity checks are unchanged.
`hold`, `deact … stop-post` and `backstop` still refuse bad/duplicate
`INVOCATION_ID` with 64.

## Files

New: `application/rp11/stop.py`, `adapters/rp11/stop.py`,
`tests/test_rp11_stop.py`, `tests/systemd_integration/test_route3_stop_host.py`.
Changed: `infra/rp11-h1/{rp11_h1.py,rp11_roles.py,build.py}` (both new modules in
the exact source manifest; up-front import), `tests/test_rp11_h1_artifact.py`,
`tests/systemd_integration/test_route3_host.py`,
`tests/web/test_p3_4_static_assets.py` (two exact paths added to the
enumerated allowlist; nothing loosened), and the current-state docs (handover,
status, active delivery plan, review README). `application/unit_control.py` and
the manager adapter are untouched.

## Requirement → test

- Exact vector, rejection before any bus: `test_entry_accepts_exactly_the_five_role_vectors`,
  `test_entry_rejects_every_other_vector` (stop variants),
  `test_an_extra_or_alternate_stop_token_is_refused_before_any_role_runs`; host
  `test_an_extra_operand_is_refused_before_any_manager_call`.
- No environment read (malformed, oversized, raw duplicate `envp`, well-formed):
  `test_no_environment_value_can_change_a_valid_stop`,
  `test_a_genuinely_duplicated_invocation_id_cannot_affect_a_valid_stop`,
  `test_a_valid_stop_never_calls_the_environment_reading_helper`; provenance roles
  unchanged (existing tests); host `test_hostile_environment_entries_…`.
- One call/no retry, every refusal, error, exception, unknown result, safe
  output, exit map: `tests/test_rp11_stop.py`.
- Malformed success (`ControlOk(None)`, bare `JobCompletion`, non-`StopCompletion`,
  wrong/str/None outcome, wrong/None unit, missing completion, empty/short/no-id/
  non-digit/Arabic-digit/newline/arbitrary/None path): 19 parametrized cases, each
  one call, exit 22, fixed line.
- No DI-1 read, record/journal/process/environment access: source-level test over
  both new modules.
- Real host (`sudo -n` as `ubuntu`): active → stopped; connector sees exactly one
  `StopUnit(rp11-capture-pass-a.service, "fail")`; loaded-inactive and failed →
  stopped; not-loaded → exit 20 `refused not-loaded` with no stop job listed (no
  claim about transient stubs); unauthorized (no sudo) → exit 20
  `refused not-authorized`, same `InvocationID`/`MainPID`, no job; post-send
  deadline on the real manager → exit 22, exactly one `StopUnit` sent, unit really
  stopped yet the result stays 22; extra operands → 64, unit untouched; hostile
  and 1.2 MB environment → stopped.

## Commands and results

Final tree synced with the documented secret-excluding rsync to
`/opt/freedom-blades/platform` on `oracle-test`.

1. `cd /opt/freedom-blades/platform && /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/test_rp11_stop.py tests/test_rp11_start.py tests/test_rp11_h1_artifact.py tests/test_systemd_unit_control.py`
   — exit 0, **700 passed, 2 skipped** (`RLIMIT_NOFILE` above 1048583; hard limit
   524288).
2. `sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_RP11_WHEEL=/home/ubuntu/jeepney-0.9.0-py3-none-any.whl /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/systemd_integration/test_route3_stop_host.py`
   — exit 0, **9 passed** (53 s), fresh artifact from the pinned wheel. (A first
   run failed one assertion of mine — a journal "Stopping" count that systemd
   does not attribute to the invocation; replaced by the connector-level
   one-`StopUnit` proof.)
3. Same command over `tests/systemd_integration` — exit 0, **128 passed, 2
   skipped** (602 s). Skips: the two fresh-reboot proofs
   (`FREEDOM_TMPFILES_BOOT_PROOF=1`). This is the previous 119 plus the 9 SA-2 tests.
4. `… -m pytest -q -rfEs tests/web/test_p3_4_static_assets.py` — **109 passed, 2
   failed**: `test_the_discovery_enumerates_untracked_files_rather_than_directories`
   and `test_every_evidence_harness_source_in_the_tree_is_declared` (five
   undeclared `tools/phase_5_0_evidence/*` files). Same figures as the baseline
   recorded in the SA-1 handback for a clean `a447558`; not re-run on the baseline
   in this session.
5. Bot suite, `PATH='/usr/lib/postgresql/16/bin:/usr/bin:/bin'`
   `TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'`
   `… -m pytest -q -rs tests/test_*.py` — **6 failed, 6225 passed, 20 skipped, 39
   errors** (two runs, identical counts). All 45 are in `tests/test_r5_runner.py`
   (5 failed, 39 errors) and `tests/test_sheet_bootstrap_boundary.py` (1 failed),
   files this work does not touch. **Verified baseline:** a clean `git archive`
   of `a447558` on the host gives the same **6 failed, 39 errors** for those two
   files (39 passed). Skips are the `RP11_LAUNCH_BUILD_ROOT` launch-toolchain
   cases (not provisioned). Left alone.
6. Web suite, serially after the bot suite, same environment, `tests/web` —
   **2 failed, 2890 passed, 80 skipped** (666 s). The skip count is the documented
   80 (54 + 26 matrix-cell skips), not the database-skipped figure. The 2 failures
   are the two static-asset tests in item 4 (the module is part of `tests/web`).
7. Foundry: `node --test foundry-module/tests/*.test.mjs` — **171 passed, 0 failed**.
8. Local: `python3 -m py_compile` over every touched Python path — exit 0.
   `git diff --check` — exit 0. Local venv run of items 1 and 4 (including
   `test_rp11_stop.py`): 809 passed, 2 skipped, 2 failed (the same two).

## Host cleanup (verified after the root runs)

No `rp11*` unit or process; no `/usr/local/libexec/freedom-blades-rp11`,
`/var/lib/freedom-blades-rp11`, `/run/polkit-1`, `/var/tmp/rp11-act-*`; the
baseline comparison directory and bot log were removed; no SA-2 evidence or log
remains. `polkit.service` active. The six pre-existing `/var/tmp/p5-r5-rp11-h0*`
directories were left untouched.

## Effects and risks

No deployment, migration, schema or recovery change; the role is inactive
outside `oracle-test` and nothing in bot/web/worker imports it. Unchanged risks:
the `sudo` preamble environment is unclosed (EX-1; the role ignores it); the
unconfirmed path was injected at the bus connector, not by faulting the installed
binary; the executor must establish OC-1..OC-3 and exclude `start-pre` before
calling SA-2; the transient inspection-failure decision and the final
independent production security review remain mandatory before any activation.

## Recommendation

Accept SA-2 for continued non-production development after independent Codex
review; no blocker is named.

---

# Remediation — malformed `ControlRefused` reason (2026-10-16)

Status: **remediated uncommitted candidate, independent Codex re-review pending —
not accepted.** Production/staging unchanged and unauthorized.

## Finding and disposition

`StopProcedure.run()` rendered `result.reason.value` for any `ControlRefused`, so a
boundary double with an arbitrary `.reason` object exposing
`.value = "/sensitive/caller/value"` exited 20 and printed it. **Fixed.** A
`ControlRefused` is now accepted only when `reason` is an actual `RefusalReason`;
anything else raises at the SA-2 application boundary and takes the existing fixed
internal-error path (exit 70, exactly `rp11-stop internal-error`). The malformed value
is never stringified, inspected or converted by value. The manager adapter, SA-1 and
the other accepted roles are untouched.

## Regressions (written first; leak reproduced)

`test_a_malformed_refusal_reason_is_internal_error_without_output_or_retry`, four cases:
object with sensitive `.value`, plain string `"not-loaded"`, foreign enum with a valid
spelling, `None`. Each asserts one `stop_capture_unit()` call, exit 70, stderr exactly
`rp11-stop internal-error\n`, empty stdout, and the sensitive value absent. Before the
fix the object and foreign-enum cases failed (the string and `None` cases already
failed closed by exception); after it all pass. The existing parametrized test over
every real `RefusalReason` still passes (exit 20, existing fixed line, one call).

Files: `application/rp11/stop.py` (import `RefusalReason`, one `isinstance` check),
`tests/test_rp11_stop.py`; current-state docs (handover, status, active delivery plan,
review README) updated to "remediated, Codex re-review pending".

## Commands and results (final tree, synced with the documented rsync)

All on `oracle-test`, `cd /opt/freedom-blades/platform`, interpreter
`/opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs`.

1. `… tests/test_rp11_stop.py tests/test_rp11_start.py tests/test_rp11_h1_artifact.py tests/test_systemd_unit_control.py` — exit 0, **704 passed, 2 skipped** (`RLIMIT_NOFILE` above 1048583; hard 524288). (700 before + 4 new.)
2. `sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_RP11_WHEEL=/home/ubuntu/jeepney-0.9.0-py3-none-any.whl … tests/systemd_integration/test_route3_stop_host.py` — exit 0, **9 passed** (50 s).
3. Same environment over `tests/systemd_integration`, serially — exit 0, **128 passed, 2 skipped** (617 s). Skips: the two fresh-reboot proofs (`FREEDOM_TMPFILES_BOOT_PROOF=1`).
4. `… tests/web/test_p3_4_static_assets.py` — **109 passed, 2 failed**: `test_the_discovery_enumerates_untracked_files_rather_than_directories` and `test_every_evidence_harness_source_in_the_tree_is_declared`. Same two as the baseline recorded in the earlier sections of this handback and the SA-1 handback for clean `a447558`; not re-run on the baseline in this session, not repaired.
5. Local `python3 -m py_compile` over the touched Python paths — exit 0. `git diff --check` — exit 0. Local `venv-web` run of `tests/test_rp11_stop.py` — 43 passed.

The full bot, web and Foundry suites were not re-run: the change is confined to one
SA-2 application module and its test, with no shared production, bot, web, worker or
Foundry surface touched.

## Host cleanup (verified after the root runs)

No `rp11*` unit or process; no `/usr/local/libexec/freedom-blades-rp11`,
`/var/lib/freedom-blades-rp11`, `/run/polkit-1`, `/var/tmp/rp11-act-*`; no RP-11 Polkit
rule; no SA-2 evidence/log. `polkit.service` active. The six
`/var/tmp/p5-r5-rp11-h0*` directories are intact. `/tmp/rp11-wheel/` (a copy of the
pinned Jeepney wheel from 2026-10-15) remains; it is not a unit, artifact, store or
evidence path.

## Remaining risks

Unchanged from the section above: unclosed `sudo` preamble environment (EX-1);
unconfirmed path injected at the bus connector; executor must establish OC-1..OC-3 and
exclude `start-pre`; the transient inspection-failure decision and final independent
production security review remain mandatory before any activation. SA-1 has a similar
local rendering shape and was deliberately not changed here.

## Recommendation

Accept SA-2 for continued non-production development after independent Codex re-review;
no blocker is named.

# Second remediation — spoofable unit equality and malformed error certainty (2026-10-16)

Status: **twice-remediated uncommitted candidate, independent Codex re-review pending — not
accepted.** Production/staging unchanged and unauthorized.

## Findings and dispositions

1. **Spoofable capture-unit equality → exit 0. Fixed.** `_is_stop_of_the_capture_unit`
   compared `completion.unit == CAPTURE_UNIT` on an unvalidated object. It now requires
   `type(value) is StopCompletion`, `outcome is StopOutcome.STOPPED`,
   `type(completion) is JobCompletion`, and exact `str` for both `unit` and `job_path`
   *before* any comparison; only then `unit == CAPTURE_UNIT` (both operands exact `str`) and
   the ASCII `fullmatch`. Subclasses, lookalikes and `str` subclasses are rejected without
   invoking any of their hooks. Any failure is the existing exit 22 `effect-not-confirmed`.
2. **Malformed `ControlError` certainty. Fixed.** New `_is_well_formed_error` requires
   `type(result) is ControlError` with exact `str` `kind`, exact `str` `detail` and exact
   `bool` `effect_not_confirmed`; otherwise `StopProcedure.run` raises and the existing fixed
   path returns exit 70, `rp11-stop internal-error`. No field is `bool()`-ed, stringified or
   rendered. The composition-root guard was not changed. Valid `False`/`True` keep exit 21/22.

Files: `application/rp11/stop.py`, `tests/test_rp11_stop.py`; current-state docs (handover,
status, active delivery plan, review README). Manager adapter, SA-1 and the other accepted
roles untouched.

## Regressions (written first)

Before the fix 19 of the new cases failed (every spoofed-success case and every malformed
error case: equality-true object, raising `__eq__`, `str` subclasses, `StopCompletion`/
`JobCompletion` subclasses, certainty `None`/0/1/""/"yes"/raising `__bool__`, bad `kind`/
`detail`, `ControlError` subclass). They now assert one DI-S call, no hook invoked,
no supplied value or exception text in output, and exit 22 (success spoofs) or exit 70
(malformed errors) with the fixed line and empty stdout; both real booleans retain 21/22.
The valid completion and the earlier malformed-refusal cases remain green.

## Commands and results (`oracle-test`, `cd /opt/freedom-blades/platform`, documented rsync)

1. `/opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/test_rp11_stop.py tests/test_rp11_start.py tests/test_rp11_h1_artifact.py tests/test_systemd_unit_control.py`
   — exit 0, **725 passed, 2 skipped** (`RLIMIT_NOFILE` above 1048583; hard 524288).
2. `sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_RP11_WHEEL=/home/ubuntu/jeepney-0.9.0-py3-none-any.whl /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/systemd_integration/test_route3_stop_host.py`
   — **9 passed** (51 s) on the re-run. The first run had **1 failed, 8 passed**: the
   `systemctl list-jobs` empty-queue assertion at `test_route3_stop_host.py:64` in
   `test_an_active_capture_unit_receives_one_stop_and_the_role_returns_stopped`. That test
   passed alone and in the re-run; I did not diagnose the cause. A host-timing flake is my
   inference, not an established fact.
3. Same environment over `tests/systemd_integration`, serially — exit 0, **128 passed, 2
   skipped** (620 s); skips are the two `FREEDOM_TMPFILES_BOOT_PROOF=1` reboot proofs.
4. `… -m pytest -q -rfEs tests/web/test_p3_4_static_assets.py` — **109 passed, 2 failed**
   (`test_the_discovery_enumerates_untracked_files_rather_than_directories`,
   `test_every_evidence_harness_source_in_the_tree_is_declared`): the established baseline
   recorded above; not repaired, not re-run on a clean baseline this session.
5. Local `python3 -m py_compile` over the touched Python paths — exit 0; `git diff --check`
   — exit 0; local `venv-web` run of `tests/test_rp11_stop.py` — 64 passed.

The code under test was unchanged after the host runs; only docs were edited afterwards.
Full bot/web/Foundry suites not re-run: no shared production, bot, web, worker or Foundry
surface changed.

## Host cleanup (verified after the root runs)

No `rp11*` unit or process; no `/usr/local/libexec/freedom-blades-rp11`,
`/var/lib/freedom-blades-rp11`, `/run/polkit-1`, `/var/tmp/rp11-act-*`; no RP-11 Polkit
rule in `/etc/polkit-1/rules.d`; no SA-2 evidence/log. `polkit.service` active. The six
`/var/tmp/p5-r5-rp11-h0*` directories are intact.

## Remaining risks

Unchanged: EX-1 `sudo` preamble environment; unconfirmed path injected at the bus
connector; executor must establish OC-1..OC-3 and exclude `start-pre`; the transient
inspection-failure decision and final independent production security review remain
mandatory before activation. SA-1 has a similar local rendering shape and was not changed.

## Recommendation

Accept SA-2 for continued non-production development after independent Codex re-review;
no blocker is named.

## Host-verification remediation (r3, 2026-10-16)

**Defect.** Two real-host tests ended with `systemctl list-jobs --no-legend` stripped `== ""`,
a host-global empty-queue claim. Codex reproduced the failure with an unrelated
`445262 apt-daily.service start running`; the SA-2 result and all capture-unit assertions had
passed. A test-scope defect, not a runtime failure.

**Correction** (test-only, `tests/systemd_integration/test_route3_stop_host.py`): a local
`unit_jobs(unit=UNIT)` helper parses `list-jobs` rows and matches the unit column exactly
(`row.split()[1] == unit`). It replaces the global assertion in the active-success and
authorization-denial tests, the substring check in the not-loaded test, and the identical
global assertion in the extra-operand test (same defect, same file). All result, exit-code,
state-preservation and one-`StopUnit` assertions are unchanged. No production module touched.

**Deliberate unrelated-job proof** (on `oracle-test`, trap-cleaned script run via `ssh oracle-test 'bash -s'`):
`systemd-run --unit=fb-r3-proof-unrelated --service-type=oneshot --no-block /usr/bin/sleep 240`.
Before the tests: `450389 fb-r3-proof-unrelated.service start running`. Both corrected tests ran
(`pytest -q -rfEs` on the two node IDs, as root with `FREEDOM_RP11_WHEEL`): **2 passed in 11.96 s,
0 skips**; the job was still `running` after them. Cleanup trap stopped/reset the unit:
`LoadState=not-found`, `ActiveState=inactive`, `list-jobs` empty. This is distinct from the
earlier incidental `apt-daily.service` observation.

**Final-tree checks** (`/opt/freedom-blades/platform`, after the documented rsync):
1. Root, full module, fresh artifact from the pinned wheel:
   `sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_RP11_WHEEL=/home/ubuntu/jeepney-0.9.0-py3-none-any.whl /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/systemd_integration/test_route3_stop_host.py`
   — exit 0, **9 passed**, 0 failed/errors, 0 skipped (51.79 s).
2. `PATH=/usr/lib/postgresql/16/bin:/usr/bin:/bin TEST_DATABASE_URL=postgresql+psycopg:///freedom_test /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/test_rp11_stop.py tests/test_rp11_start.py tests/test_rp11_h1_artifact.py tests/test_systemd_unit_control.py`
   — exit 0, **725 passed, 2 skipped**, 0 failed/errors. Skips: `tests/test_rp11_h1_artifact.py:956`
   ×2, "cannot raise RLIMIT_NOFILE above 1048583 (hard 524288, nr_open 2147483584)".
3. `python3 -m py_compile tests/systemd_integration/test_route3_stop_host.py` — exit 0.
4. `git diff --check` — exit 0.

Broader suites not re-run: only a test file changed; the code under test is unchanged.

**Host cleanup (verified).** Proof unit absent, no queued job (`list-jobs` empty); no `rp11*`
unit or process; no RP-11 Polkit rule, `/run/polkit-1`, artifact, store, `/var/tmp/rp11-act-*`
or `/run/rp11-*`; `/usr/local/libexec` is `root:root 755`; the six `/var/tmp/p5-r5-rp11-h0*`
paths intact; `polkit.service` active.

**Remaining risks:** unchanged from above (EX-1 preamble, bus-connector unconfirmed path,
OC-1..OC-3, transient inspection-failure decision, final independent production security review).

**Recommendation:** accept SA-2 for continued non-production development after independent
Codex re-review; no blocker is named.

## Maintainer acceptance — 2026-10-16

Peter Duscha accepts static SA-2 `stop` through DI-S for continued
non-production development. The acceptance includes the refusal-diagnostic and
typed-result remediations and the test-only host-job assertion correction.
Independent Codex re-review found no blocking issue and independently confirmed
the deliberate unrelated-job proof and the complete nine-test SA-2 host module.

This acceptance assigns no later Package 5.0 slice and authorizes no production
or staging activation. The transient inspection-failure decision and final
independent production security review remain mandatory before activation.
