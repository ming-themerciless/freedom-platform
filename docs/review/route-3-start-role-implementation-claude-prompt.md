# Claude implementation prompt — Route 3 static `start` role

Date: 2026-10-15
Authority: Peter Duscha, baseline v1.9 and the active implementation-first
delivery plan
Reviewer after handback: Codex

## Assignment

Implement SA-1, the first real non-production Package 5.0 consumer of the
accepted Route 3 boundary, as this exact controlled-artifact vector:

```text
/usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py \
  start <activation_id> <a2_sha256> <lease_seconds> <stop_timeout_seconds>
```

The role validates its fixed operands, creates the accepted `HolderSpec`, makes
the single DI-2 `create_holder` call and returns that call's result. Keep the
implementation inactive outside `oracle-test`. Do not implement SA-2 `stop`, a
Package 5.0 coordinator, consume/attest, production activation, migration work
or unrelated cleanup. Do not commit or push.

## Current working-tree warning

The working tree contains an **uncommitted Codex-authored SA-1 draft** produced
while Codex mistakenly acted as implementer. It is not Claude's work, is not
reviewed, is not accepted and creates no design authority. Treat every current
SA-1 code, test, handback and current-state edit as untrusted draft material.
Independently compare it with the accepted contracts, replace or simplify it as
needed, and take ownership only of the final bytes you return.

The last accepted commit is `a447558` (`Complete and accept Route 3 safety
prerequisite`). Do not erase unrelated maintainer changes. The known
uncommitted SA-1 draft paths are visible in `git status`; the new implementation
prompt itself and the active-handover assignment are reviewer-owned and must be
preserved.

## Required reading

Before planning or editing, read completely:

1. `.agents/AGENTS.md`;
2. the implementation-plan reading map, §§0, 12, 16 and 20;
3. `docs/review/Handover information`;
4. `docs/project-management/active-delivery-plan.md`;
5. `docs/operations/disposable-test-server.md`;
6. `docs/review/route-3-manager-polkit-implementation-handback.md`;
7. the completed stop-post, backstop and hold handbacks;
8. operation inventory §§4.1, 5.6, 6 SA-1, 7, 8.1 and applicable §12 rows;
9. interface contract §§3.0 and 3.2; and
10. the current SA-1 draft and its diff from `a447558`.

Historical WP gates do not block implementation under baseline v1.9, but their
accepted SA-1 and DI-2 requirements remain implementation inputs.

## Blocking defect already identified by the reviewer

Do not return the draft unchanged. It violates `H-FI.1` and `SA1.FI.1`:

- `start` must read **no environment variable**;
- the shared entry currently calls `_initial_environment()`, reads
  `/proc/self/environ` and parses `INVOCATION_ID` before it knows the role.

Give `start` the role-appropriate first-image path. It must still check file
descriptors 0/1/2, close every descriptor at or above 3, reset resettable signal
dispositions and the signal mask, set the fixed umask and working directory,
and perform the accepted artifact-integrity checks. No environment value may
select, reject or otherwise affect a valid `start` invocation. Preserve the
existing INVOCATION_ID behavior of every implemented unit-started role that
consumes that provenance.

Add a regression test that fails if a valid `start` invocation calls the
environment-reading helper at all. Also prove malformed, duplicate and
oversized `INVOCATION_ID` inputs cannot change the valid `start` result while
they remain refused for roles that consume that provenance.

## Required behavior

- Accept only the exact `start` vector above. Validate the activation-id grammar,
  lowercase SHA-256 and both positive bounded durations before opening the bus
  or performing any state operation. Reject extra operands, alternate spellings,
  leading-zero duration aliases and out-of-range values.
- Construct only `HolderSpec`. The caller must not choose a unit name,
  executable, command vector, systemd property, job mode, bus or arbitrary
  argument.
- Invoke DI-2 exactly once. Never retry `refused`, `error`, timeout,
  disconnect, lost reply, malformed reply, exception, abandonment or an
  `effect not confirmed` outcome.
- Preserve the accepted DI-2 three-way result. In particular,
  `UnitExists` is `refused(exists)`; post-send uncertainty is an error with
  `effect not confirmed`; neither becomes success.
- Rely on the accepted manager adapter to derive exactly one transient
  `<activation_id>.service` with `Type=exec`, `Restart=no`,
  `OOMScoreAdjust=-1000`, the two validated durations, the fixed `hold`
  `ExecStart` and fixed `deact … stop-post` `ExecStopPost`. Add no environment,
  user, scope, terminal, wait, collect or auxiliary unit.
- The role creates no child, sends no signal, writes no record and performs no
  executor-side activation wait. It returns one bounded, value-safe result to
  the executor. Arbitrary exception or transport detail must not reach output.
- Preserve the three accepted PID-1 vectors and their behavior. Include every
  new module in the controlled artifact's exact source manifest and retain the
  root-owned/no-symlink/non-writable artifact checks.
- Do not weaken the manager/Polkit boundary, scope guard, tmpfiles prerequisite,
  production gates or existing tests to make the slice pass.

## Tests and disposable-host proof

Use focused fake-boundary tests to cover success, every typed refusal/error
class, invalid results, safe diagnostics, exact one-call/no-retry behavior,
pre-send exception and unconfirmed post-send outcomes. Include adversarial
operand-type and grammar cases and the role-specific environment regression
above.

On `oracle-test`:

1. build a fresh root-owned controlled artifact from the hash-pinned wheel;
2. invoke the exact SA-1 vector through the accepted `sudo -n` launch preamble
   as the executor identity, not only as an already-root test process;
3. prove the resulting unit properties and exact `hold`/`stop-post` vectors;
4. exercise success, loaded-name refusal, authorization refusal and at least one
   unconfirmed manager outcome with proof of one send/no retry;
5. run a complete real holder lifecycle through cleanup/recovery;
6. rerun the existing manager/artifact and hold host suites; and
7. leave no RP-11 unit, process, rule, artifact, staging directory or test
   evidence behind, with `polkit.service` active.

Run the focused repository suites affected by the slice, the production-file
scope guard, Python compilation and `git diff --check`. Expand to the documented
bot/web/Foundry comparisons in proportion to actual shared-surface changes.
Report exact commands, pass/fail/skip counts and every skip; do not hide or fix
unrelated baseline failures.

## Documentation and handback

Correct the uncommitted current-state documentation so it accurately says
Claude implemented the candidate and Codex review is pending. Do not record a
maintainer decision or acceptance that has not happened. Update the concise
`docs/review/route-3-start-role-implementation-handback.md` with:

- delivered behavior and exact files;
- SA-1/H-FI/DI-2 requirement-to-test coverage;
- the environment defect and its correction;
- exact focused and real-host results;
- host cleanup state;
- remaining production risks; and
- one recommendation: accept, remediate a concrete blocker, or replace the
  approach.

Return the implementation for independent Codex review. Production and staging
must remain unchanged. The transient inspection-failure decision and final
production security review remain mandatory before any production activation.
