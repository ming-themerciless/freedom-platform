# Claude remediation prompt — Route 3 static `start` false-success finding

Date: 2026-10-15
Authority: baseline v1.9, the active implementation-first delivery plan, and
the independent Codex re-review of the remediated SA-1 candidate
Mode: one bounded remediation and verification cycle on `oracle-test`; no
production or staging activation

## Assignment

Remediate the one blocking finding from the independent re-review of the
uncommitted SA-1 static `start` candidate: a malformed success payload from
DI-2 is currently promoted to `started`. Add a regression that demonstrates
the false success first, make the smallest fail-closed correction, rerun the
required checks on the final tree, and update the existing SA-1 handback in
place.

Also correct the active handover's stale description of the assignment and
finish the disposable-host cleanup described below. These are bounded
current-state and cleanup corrections, not new implementation scope.

Do not create another plan, review record or handback. Do not implement SA-2
`stop`, a Package 5.0 coordinator, `consume`, `attest`, migration work,
production activation or unrelated cleanup. Preserve unrelated working-tree
changes. Do not commit or push.

The accepted Route 3 manager/Polkit adapter and the `hold`, `stop-post` and
`backstop` roles are not reopened. Do not weaken their validation, artifact
checks, authorization boundary, result discipline or tests.

## Read before editing

1. `.agents/AGENTS.md` in full.
2. `docs/implementation-plan.md`: reading map, §§0, 12 Phase 5.0, 13, 14, 16
   and 20.
3. `docs/review/Handover information`.
4. `docs/project-management/active-delivery-plan.md`.
5. `docs/operations/disposable-test-server.md`.
6. `docs/review/route-3-start-role-implementation-claude-prompt.md`,
   `docs/review/route-3-start-role-review-remediation-claude-prompt.md` and
   `docs/review/route-3-start-role-implementation-handback.md`.
7. Operation inventory §§5.6 and 6 SA-1, especially `SA1.OP.2` and
   `SA1.OP.3`.
8. Interface contract §§3.0 and 3.2, especially the three-way result,
   malformed-reply and `effect not confirmed` rules.
9. `application/rp11/start.py`, `adapters/rp11/start.py`,
   `application/unit_control.py`, the relevant tests, and the full current diff
   from accepted commit `a447558`.

Historical WP closure labels are not current development gates. Their accepted
SA-1 and DI-2 requirements remain implementation inputs.

## Blocking finding — malformed `ControlOk` becomes success

`StartProcedure.run()` currently treats the outer `ControlOk` class alone as
proof of success:

```python
if isinstance(result, ControlOk):
    return StartOutcome(StartEnd.STARTED)
```

The value carried by that result is never checked. A boundary double returning
`ControlOk(None)` therefore makes `run_start(...)` print
`rp11-start started` and exit 0. The existing unknown-result regression covers
only an object outside the three result classes and does not cover a malformed
payload inside the success class.

Reproduce and retain this exact case as a regression before fixing it. Then
make SA-1 accept success only when DI-2 returns a structurally valid
`JobCompletion` for the requested holder. At minimum:

- the value must be a `JobCompletion`, not `None` or another object;
- its `unit` must equal `spec.unit_name`; and
- its `job_path` must have the accepted systemd job-object-path shape rather
  than being empty or arbitrary.

A malformed apparent success occurs after the one DI-2 call. It must fail
closed, must never print `started`, must never exit 0, and must never cause a
retry. Preserve the conservative mutation discipline: report the existing
fixed `effect-not-confirmed` error and exit 22 rather than asserting that the
call was not sent. Do not expose the malformed value, exception text, unit
name, job path or transport detail in output.

Add focused tests for at least:

1. `ControlOk(None)`;
2. `ControlOk` carrying a non-`JobCompletion` object;
3. a `JobCompletion` naming a different unit;
4. empty and malformed job paths; and
5. the valid completion path, using the real accepted job-path shape.

Each invalid case must prove exactly one `create_holder` call, no retry, exit
22 and the fixed line `rp11-start error effect-not-confirmed`. Keep the existing
typed refusal, typed error, exception, operand, duration and environment tests
green. Do not change the accepted manager adapter merely to make a fake result
look valid; keep the validation local to the SA-1 application boundary unless
a smaller equally isolated value-object correction is demonstrably safer.

## Current-state and cleanup corrections

Update `docs/review/Handover information` so the canonical entry point no
longer describes the original Codex draft and its single environment defect as
the current assignment. State only the current facts: Claude's SA-1 candidate
has completed the first remediation, the independent re-review found this one
false-success blocker, this bounded remediation is in progress or returned,
SA-1 remains unaccepted, and SA-2 remains deferred pending re-review and Peter's
acceptance. Do not record acceptance or a maintainer decision that has not
happened. Keep the current production-activation gates unchanged.

The previous handback records `/var/tmp/sa1-root.log` as still present even
though the assignment required no test evidence from this work to remain.
After capturing the final result, remove that one known SA-1 log from the
disposable host and verify it is absent. Do not remove the pre-existing
`/var/tmp/p5-r5-rp11-h0*` evidence directories or any unrelated file.

## Required verification

All test levels remain authorized on `oracle-test`. Use synthetic data and the
documented secret-excluding synchronization command. Do not touch production,
staging, real secrets or player data.

Run on the final tree, at minimum:

1. `tests/test_rp11_start.py`, `tests/test_rp11_h1_artifact.py` and
   `tests/test_systemd_unit_control.py`;
2. `tests/systemd_integration/test_route3_start_host.py` as root with a fresh
   controlled artifact built from the pinned Jeepney wheel;
3. the complete `tests/systemd_integration` suite, because the changed SA-1
   application module is packaged into the artifact used by the lifecycle;
4. `tests/web/test_p3_4_static_assets.py`, reporting the established unrelated
   baseline failures without hiding them;
5. Python compilation over the exact touched Python paths; and
6. `git diff --check`.

The documented full bot, web and Foundry suites are not required solely for a
local SA-1 result-validation correction. Run them if the remediation changes a
shared production boundary or any bot, web, worker or Foundry surface.

For every check, record the exact copy-pastable command, working directory,
exit status, pass/fail/error/skip counts and each skip reason. Do not cite a
pre-fix or intermediate count as final-tree evidence. Do not call a failure
pre-existing without an actual baseline comparison already recorded in the
handback or a fresh comparison against `a447558`.

After the root tests, verify separately that:

- no RP-11 unit or process remains;
- no RP-11 Polkit rule, artifact, staging directory or store remains;
- no `/var/tmp/rp11-act-*` path remains;
- `/var/tmp/sa1-root.log` is absent;
- the unrelated `/var/tmp/p5-r5-rp11-h0*` paths were not removed; and
- `polkit.service` is active.

## Acceptance criteria

- No malformed `ControlOk` payload can become `started` or exit 0.
- A valid `JobCompletion` for the requested holder still produces exactly one
  DI-2 call, `rp11-start started` and exit 0.
- Every malformed apparent success is one call, no retry, exit 22 and
  `rp11-start error effect-not-confirmed`, with no value leakage.
- The earlier duration, authorization-refusal and raw duplicate-environment
  remediations remain intact.
- Existing PID-1 vectors, artifact integrity checks and the complete Route 3
  lifecycle remain green relative to the established baseline.
- The active handover accurately describes the current pending-remediation or
  pending-re-review state without claiming acceptance.
- The disposable host is clean, including removal of the SA-1 root-run log,
  and production/staging remain unchanged.

## Handback update

Append one concise second-remediation section to
`docs/review/route-3-start-role-implementation-handback.md`; do not create a new
handback. Include:

- the false-success finding and its exact disposition;
- the regression cases and chosen validation boundary;
- principal files changed;
- exact final-tree commands and results, including failures and skips;
- the corrected active-handover state;
- final host cleanup, explicitly including the removed SA-1 log;
- unchanged remaining production risks; and
- one recommendation: accept SA-1 for continued non-production development or
  remediate one specifically named remaining blocker.

Return the uncommitted candidate for independent Codex re-review. SA-1 remains
unaccepted and SA-2 remains deferred until that re-review and Peter's explicit
acceptance.
