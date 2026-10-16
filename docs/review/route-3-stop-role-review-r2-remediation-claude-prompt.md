# Claude remediation prompt — Route 3 static `stop` typed-result hardening

Date: 2026-10-16
Authority: baseline v1.9, the active implementation-first delivery plan, and
the independent Codex re-review of the remediated uncommitted SA-2 candidate
Mode: one bounded remediation and verification cycle on `oracle-test`; no
production or staging activation

## Assignment

Remediate the two blocking typed-result findings from independent Codex
re-review of the uncommitted SA-2 static `stop` candidate:

1. a malformed apparent success can spoof equality with the fixed capture-unit
   name and be promoted to exit 0; and
2. a malformed `ControlError.effect_not_confirmed` value can be downgraded to
   the pre-send exit or raise outside the fixed-diagnostic guard.

Write regressions that reproduce both defects before changing behavior. Make
the smallest fail-closed correction at the SA-2 application boundary, rerun the
required checks on the final tree, and append the result to the existing SA-2
handback.

Do not create another plan, review record or handback. Do not implement a
Package 5.0 coordinator, executor OC-1/OC-2/OC-3 checks, `consume`, `attest`,
migration work, production activation or unrelated cleanup. Preserve unrelated
working-tree changes. Do not commit or push.

The accepted Route 3 manager/Polkit adapter, SA-1 `start`, and the accepted
`hold`, `stop-post` and `backstop` roles are not reopened. Do not alter their
behavior, shared result value objects, manager mapping, artifact checks,
authorization boundary or tests merely to make an SA-2 boundary double pass.
Keep this correction inside `application/rp11/stop.py`,
`adapters/rp11/stop.py` only if the safe outer boundary genuinely requires it,
and focused SA-2 tests unless executable evidence proves a narrower correction
is impossible.

## Read before editing

1. `.agents/AGENTS.md` in full.
2. `docs/implementation-plan.md`: reading map, §§0, 12 Phase 5.0, 13, 14, 16
   and 20.
3. `docs/review/Handover information`.
4. `docs/project-management/active-delivery-plan.md`.
5. `docs/operations/disposable-test-server.md`.
6. `docs/review/route-3-stop-role-implementation-claude-prompt.md`,
   `docs/review/route-3-stop-role-review-remediation-claude-prompt.md`, and
   `docs/review/route-3-stop-role-implementation-handback.md`.
7. Operation inventory §§4.1, 5.7, 6 SA-2, 7 and 8.1, especially
   `SA2.OP.2` and `SA2.OP.3`.
8. Interface contract §§3.0 and 3.7, especially D-3, D-4, D-9, IO-1 and
   IO-2.
9. `application/rp11/stop.py`, `adapters/rp11/stop.py`,
   `application/unit_control.py`, the relevant tests, and the complete current
   diff from accepted commit `a447558`.

Historical WP closure labels are not current development gates. Their accepted
SA-2 and DI-S requirements remain implementation inputs.

## Blocking finding 1 — spoofable capture-unit equality becomes success

`_is_stop_of_the_capture_unit()` currently checks:

```python
isinstance(completion, JobCompletion)
and completion.unit == CAPTURE_UNIT
```

The dataclass type annotations are not runtime validation. A boundary double
can return an actual `JobCompletion` whose `unit` is an arbitrary object with
an `__eq__` method that returns `True`. The current code invokes that
caller-controlled equality and accepts the result as the exact fixed unit. The
independent review reproduced one DI-S call returning exit 0 and
`rp11-stop stopped` for such a payload.

This violates the assignment: apparent success is untrusted boundary data and
is valid only for a structurally valid `StopCompletion` containing a
structurally valid `JobCompletion` for exactly the literal string
`rp11-capture-pass-a.service` and the accepted ASCII job path. A malformed
success after the one call is `effect-not-confirmed`, exit 22, never stopped.

Reproduce and retain the equality-spoof case as a regression before fixing it.
Then validate the complete success structure before comparing values. At
minimum:

- accept only the actual expected `StopCompletion` and `JobCompletion`
  boundary types, not lookalikes or subclasses with overridden attributes;
- require `outcome is StopOutcome.STOPPED`;
- require the unit field to be an exact `str` before comparing it with
  `CAPTURE_UNIT`, so caller-controlled equality is never invoked; and
- require the job path to be an exact string matching the existing ASCII-only
  full-path expression.

Do not stringify, normalize or coerce a malformed unit or path. Do not compare
an unvalidated object with the fixed string in either operand order. Do not
change the manager adapter: its real completion already uses the exact value
objects and strings.

Add focused regressions for at least:

1. a unit object whose `__eq__` returns `True`, proving it is exit 22 rather
   than exit 0 and that its equality hook is not needed to decide the result;
2. a sensitive or raising equality hook, proving no exception text or supplied
   value reaches output;
3. a `str` subclass with overridden equality;
4. subclassed or otherwise overridden `StopCompletion` and `JobCompletion`
   payloads if exact boundary types are the chosen validation; and
5. the real exact completion, which remains one call, exit 0 and exactly
   `rp11-stop stopped`.

Every malformed-success case must prove exactly one `stop_capture_unit()` call,
no retry or follow-up observation, exit 22, empty stdout and exactly
`rp11-stop error effect-not-confirmed\n` on stderr.

## Blocking finding 2 — malformed error certainty escapes or is downgraded

`StopProcedure.run()` currently copies `result.effect_not_confirmed` into a
`StopResult` without runtime validation. `run_stop()` evaluates it while
rendering and again through `outcome.exit_code`, after its `try` block.

Two concrete failures follow:

- `ControlError(..., effect_not_confirmed=None)` is treated as false and
  incorrectly becomes `effect-not-sent`, exit 21; and
- an arbitrary object whose `__bool__` raises can raise outside the
  fixed-diagnostic guard, allowing its caller-controlled exception text to
  reach the interpreter traceback instead of returning exit 70 and exactly
  `rp11-stop internal-error`.

A malformed outer result is not a valid typed error merely because it is an
instance of `ControlError`. Reproduce both cases before fixing them. Validate
the complete `ControlError` structure at the SA-2 application boundary before
copying any field into `StopResult`: the outer boundary type and its `kind`,
`detail` and `effect_not_confirmed` fields must have their declared exact
runtime types, especially an exact `bool` for certainty. Do not call `bool()`
on, stringify, log or otherwise interpret a malformed field. A malformed
`ControlError` is an unexpected result and must take the existing fixed
internal-error path: exit 70 and exactly `rp11-stop internal-error`.

It is acceptable to extend the composition root's exception guard only if
needed after the application boundary has been made structurally strict; do
not use a broad outer catch as a substitute for validating the typed result.
Valid `ControlError(..., False)` and `ControlError(..., True)` must preserve
their existing exit 21/22 mappings and fixed diagnostics.

Add focused regressions for at least:

1. `None`, `0`, `1`, a falsey string and a truthy string as the certainty
   field;
2. an arbitrary certainty object whose `__bool__` raises with sensitive text;
3. malformed `kind` and `detail` fields if complete structural validation is
   applied;
4. a foreign/subclassed result object if exact `ControlError` is required; and
5. both real boolean values, retaining the accepted mappings.

Each malformed case must prove one DI-S call, no retry, exit 70, empty stdout,
exactly `rp11-stop internal-error\n` on stderr, and absence of every supplied
value and exception message from output. No malformed field may turn an
uncertain effect into exit 21.

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
   SA-2 module is packaged into the shared controlled artifact;
4. `tests/web/test_p3_4_static_assets.py`, reporting the established unrelated
   baseline failures without hiding or repairing them;
5. Python compilation over every touched Python path; and
6. `git diff --check`.

The documented full bot, web and Foundry suites are not required solely for
this local SA-2 validation correction. Run them if the remediation changes a
shared production boundary or any bot, web, worker or Foundry surface.

For every check, record the exact copy-pastable command, working directory,
exit status, pass/fail/error/skip counts and every skip reason. Do not cite a
pre-fix or intermediate count as final-tree evidence. Do not call a failure
pre-existing without the baseline comparison already recorded in the handback
or a fresh comparison against the relevant baseline.

After root tests, verify separately that:

- no RP-11 unit or process remains;
- no RP-11 Polkit rule, artifact, staging directory or store remains;
- no `/var/tmp/rp11-act-*` path or SA-2 evidence/log remains;
- the unrelated `/var/tmp/p5-r5-rp11-h0*` paths were not removed; and
- `polkit.service` is active.

## Acceptance criteria

- No object can satisfy the fixed unit check through caller-controlled
  equality, subclass behavior, coercion or another non-string value.
- Every malformed apparent success makes exactly one DI-S call and returns
  exit 22 with only the fixed `effect-not-confirmed` diagnostic.
- No malformed `ControlError` field is evaluated, coerced, rendered or allowed
  to select exit 21 or 22; every malformed typed-error payload returns exit 70
  with only the fixed internal-error diagnostic.
- Valid exact `ControlError` values preserve exit 21 for proven pre-send and
  exit 22 for post-send/unconfirmed errors.
- The valid exact stop completion remains exactly one call, exit 0 and
  `rp11-stop stopped`.
- The earlier malformed-refusal remediation remains green: only actual
  `RefusalReason` members receive exit 20 and all malformed reasons receive the
  fixed exit-70 path.
- Existing exact-vector, no-environment-read, artifact-integrity and Route 3
  lifecycle behavior remains green relative to the established baseline.
- Current-state documents describe a twice-remediated candidate pending
  independent Codex re-review without claiming acceptance.
- The disposable host is clean and production/staging remain unchanged.

## Handback update

Append one concise second-remediation section to
`docs/review/route-3-stop-role-implementation-handback.md`; do not create a new
handback. Include:

- both typed-result findings and their exact dispositions;
- the pre-fix reproductions and retained regressions;
- the exact validation boundary and why no malformed value is evaluated;
- principal files changed;
- exact final-tree commands and results, including failures and skips;
- final host cleanup state;
- unchanged remaining production risks; and
- one recommendation: accept SA-2 for continued non-production development or
  remediate one specifically named remaining blocker.

Update only the current-state documents needed to say that the second bounded
remediation is complete and independent Codex re-review is pending. Do not
record Peter's acceptance or any production/staging authorization that has not
happened.

Return the uncommitted candidate for independent Codex re-review. Production
and staging activation remain unauthorized; the transient inspection-failure
decision and final independent production security review remain mandatory
before any activation.
