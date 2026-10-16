# Claude remediation prompt — Route 3 static `stop` refusal-diagnostic finding

Date: 2026-10-16
Authority: baseline v1.9, the active implementation-first delivery plan, and
the independent Codex review of the uncommitted SA-2 candidate
Mode: one bounded remediation and verification cycle on `oracle-test`; no
production or staging activation

## Assignment

Remediate the one blocking finding from the independent review of the
uncommitted SA-2 static `stop` candidate: a malformed `ControlRefused` payload
can inject its `.value` into stderr and still return the typed-refusal exit
status. Add regressions that demonstrate the leak first, make the smallest
fail-closed correction, rerun the required checks on the final tree, and update
the existing SA-2 handback in place.

Do not create another plan, review record or handback. Do not implement a
Package 5.0 coordinator, executor OC-1/OC-2/OC-3 checks, `consume`, `attest`,
migration work, production activation or unrelated cleanup. Preserve unrelated
working-tree changes. Do not commit or push.

The accepted Route 3 manager/Polkit adapter, SA-1 `start`, and the accepted
`hold`, `stop-post` and `backstop` roles are not reopened by this remediation.
Do not alter their behavior or weaken their validation, artifact checks,
authorization boundary, result discipline or tests. Although SA-1 has a
similar local rendering shape, changing it is outside this bounded SA-2
remediation.

## Read before editing

1. `.agents/AGENTS.md` in full.
2. `docs/implementation-plan.md`: reading map, §§0, 12 Phase 5.0, 13, 14, 16
   and 20.
3. `docs/review/Handover information`.
4. `docs/project-management/active-delivery-plan.md`.
5. `docs/operations/disposable-test-server.md`.
6. `docs/review/route-3-stop-role-implementation-claude-prompt.md` and
   `docs/review/route-3-stop-role-implementation-handback.md`.
7. Operation inventory §§5.7 and 6 SA-2, especially `SA2.OP.2` and
   `SA2.OP.3`.
8. Interface contract §§3.0 and 3.7, especially D-3, D-4, D-9, IO-1 and
   IO-2.
9. `application/rp11/stop.py`, `adapters/rp11/stop.py`,
   `application/unit_control.py`, the relevant tests, and the complete current
   diff from accepted commit `a447558`.

Historical WP closure labels are not current development gates. Their accepted
SA-2 and DI-S requirements remain implementation inputs.

## Blocking finding — malformed refusal data reaches stderr

`StopProcedure.run()` currently accepts the outer result class without
validating the refusal reason:

```python
if isinstance(result, ControlRefused):
    return StopResult(StopEnd.REFUSED, result.reason.value)
```

`run_stop()` later prints `outcome.detail`. A boundary double returning a
`ControlRefused` whose `reason` is an arbitrary object with
`.value = "/sensitive/caller/value"` therefore exits 20 and prints:

```text
rp11-stop refused /sensitive/caller/value
```

This contradicts the assignment's fixed, value-safe diagnostic requirement:
output must reveal no D-Bus detail, object path, environment value or other
caller-controlled value. A malformed refusal is not a typed refusal merely
because its outer dataclass has the expected name. It is an unexpected result
and must take the fixed internal-error path: exit 70 and exactly
`rp11-stop internal-error` on stderr.

Reproduce and retain the leaking case as a regression before fixing it. Then
make the smallest correction at the SA-2 application boundary. Accept a
`ControlRefused` only when its `reason` is an actual `RefusalReason`; preserve
the fixed rendering of every valid member (`exists`, `invalid-request`,
`not-authorized`, and `not-loaded`). Reject a string with the same spelling, a
foreign enum, `None`, and an arbitrary object exposing a sensitive `.value`.

Do not stringify, echo, log or otherwise inspect a malformed value in a
diagnostic. Do not convert it to a valid refusal by value. Do not change the
manager adapter merely to make a fake boundary result valid. The DI-S call has
already occurred, so every regression must also prove exactly one call and no
retry; the role itself must perform no follow-up observation.

Add focused tests for at least:

1. an arbitrary object with a sensitive `.value` attribute;
2. a plain string equal to a valid refusal spelling;
3. a foreign enum carrying a valid refusal spelling;
4. `None`; and
5. every real `RefusalReason`, which must retain exit 20 and its existing fixed
   diagnostic.

Each malformed case must prove one `stop_capture_unit()` call, no retry, exit
70, exactly `rp11-stop internal-error`, and absence of the supplied value from
stdout and stderr. Keep all malformed-`ControlOk`, typed-error, exception,
argument, environment and real-host tests green.

## Required verification

All test levels remain authorized on `oracle-test`. Use synthetic data and the
documented secret-excluding synchronization command. Do not touch production,
staging, real secrets or player data.

Run on the final tree, at minimum:

1. `tests/test_rp11_stop.py`, `tests/test_rp11_start.py`,
   `tests/test_rp11_h1_artifact.py` and `tests/test_systemd_unit_control.py`;
2. `tests/systemd_integration/test_route3_stop_host.py` as root with a fresh
   controlled artifact built from the pinned Jeepney wheel;
3. the complete `tests/systemd_integration` suite serially, because the changed
   SA-2 application module is packaged into the shared controlled artifact;
4. `tests/web/test_p3_4_static_assets.py`, reporting the established unrelated
   baseline failures without hiding or repairing them;
5. Python compilation over every touched Python path; and
6. `git diff --check`.

The documented full bot, web and Foundry suites are not required solely for
this local SA-2 result-validation correction. Run them if the remediation
changes a shared production boundary or any bot, web, worker or Foundry
surface.

For every check, record the exact copy-pastable command, working directory,
exit status, pass/fail/error/skip counts and every skip reason. Do not cite a
pre-fix or intermediate count as final-tree evidence. Do not call a failure
pre-existing without the baseline comparison already recorded in the handback
or a fresh comparison against the relevant baseline.

After the root tests, verify separately that:

- no RP-11 unit or process remains;
- no RP-11 Polkit rule, artifact, staging directory or store remains;
- no `/var/tmp/rp11-act-*` path or SA-2 evidence/log remains;
- the unrelated `/var/tmp/p5-r5-rp11-h0*` paths were not removed; and
- `polkit.service` is active.

## Acceptance criteria

- No malformed `ControlRefused` reason can become a typed refusal, exit 20 or
  reach output.
- Every malformed refusal case makes exactly one DI-S call, performs no retry
  or follow-up observation, and returns exit 70 with only the fixed
  `rp11-stop internal-error` diagnostic.
- Every actual `RefusalReason` retains its existing fixed exit-20 result and
  diagnostic.
- The valid stop completion remains exactly one call, `rp11-stop stopped` and
  exit 0; malformed apparent successes remain exit 22
  `effect-not-confirmed`.
- Existing exact-vector, no-environment-read, artifact-integrity and Route 3
  lifecycle behavior remains green relative to the established baseline.
- The active current-state documents describe a remediated candidate pending
  independent Codex re-review without claiming acceptance.
- The disposable host is clean and production/staging remain unchanged.

## Handback update

Append one concise remediation section to
`docs/review/route-3-stop-role-implementation-handback.md`; do not create a new
handback. Include:

- the refusal-diagnostic finding and its exact disposition;
- the malformed-reason regressions and chosen validation boundary;
- principal files changed;
- exact final-tree commands and results, including failures and skips;
- final host cleanup state;
- unchanged remaining production risks; and
- one recommendation: accept SA-2 for continued non-production development or
  remediate one specifically named remaining blocker.

Update only the current-state documents needed to say that the bounded
remediation is complete and independent Codex re-review is pending. Do not
record Peter's acceptance or any production/staging authorization that has not
happened.

Return the uncommitted candidate for independent Codex re-review. Production
and staging activation remain unauthorized; the transient inspection-failure
decision and final independent production security review remain mandatory
before any activation.
