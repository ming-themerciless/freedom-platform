# Claude remediation prompt — Route 3 GRR exception safety

Date: 2026-10-14
Authority: baseline v1.9, active handover and delivery plan, and the independent
Codex review after the Route 3 `hold` remediation
Mode: one bounded implementation and verification cycle on the disposable host;
no production or staging activation

## Assignment

Remediate the remaining blocking Route 3 finding: the concrete filesystem
adapter can raise during grant re-verification, although the accepted GRR
contract says that GRR never raises. The same adapter path is used by inline
IGR, stop-post CL-G and backstop CL-G, so a persistent inspection error can
currently abort every automatic recovery rung while a Polkit grant remains.

Add regression tests that fail for the defect, implement the smallest
fail-closed correction, run the required checks on `oracle-test`, and update
the existing hold handback in place. Do not create another handback, prompt,
proof chain or contract reinterpretation. Do not commit or push.

Do not add a production caller, installer, `consume`, `attest`, static
`start`/`stop`, or any production/staging activation. Preserve unrelated
working-tree changes and all already-remediated `run-start`, `igr`, `run-end`,
descriptor-isolation and pre-journal K/S0 behavior.

## Read before editing

1. `.agents/AGENTS.md` in full.
2. `docs/implementation-plan.md`: reading map, §§0, 12 Phase 5.0, 13, 14, 16
   and 20.
3. `docs/review/Handover information`.
4. `docs/project-management/active-delivery-plan.md`.
5. `docs/operations/disposable-test-server.md`.
6. `docs/review/route-3-hold-role-implementation-claude-prompt.md`,
   `docs/review/route-3-hold-role-review-remediation-claude-prompt.md` and
   `docs/review/route-3-hold-role-implementation-handback.md`.
7. From the operation inventory, `H-GR1.1` through `H-GR1.7`, `H-GRR.1`
   through `H-GRR.8`, `H-CL.G.1` through `H-CL.G.2`, and `RT2.IGR.1`
   through `RT2.IGR.4`.

Historical closure labels are not development gates. The accepted non-GAP
operation rows above remain the behavior contract for this slice.

## Blocking finding

`adapters/rp11/fsops.py::LocalActivationFs.remove()` opens the target and then
calls `describe_fd()` without converting inspection failures into a typed
`Removal` result. `describe_fd()` can raise while performing `fstat`, the
bounded content read/hash, or directory inspection. The alternate
`observe_at()` path after an open failure can reach the same uncaught
inspection operations.

The consequences are wider than one missing journal line:

- `application/rp11/hold.py::_igr()` leaves its latch at `running`; its
  `finally` sequence does not reach `igr`, `run-end` or the explicit K release;
- `application/rp11/cleanup.py::_cl_g()` is called before the cleanup
  procedure's guarded body, so stop-post or backstop can escape before CL-0
  through CL-7; and
- if the inspection failure persists, every automatic rung can repeat the
  exception while the already-loaded grant remains present.

That contradicts `H-GRR.5`, `H-GRR.8` and `RT2.IGR.2`, which require GRR to
return one of its closed outcomes and never raise.

## Required fix

Make the real filesystem adapter convert every target-inspection failure that
can occur during GRR re-verification into a conservative, typed non-removal
result. The resulting GRR class must be one of the accepted closed outcomes,
must never claim removal, and must leave the object untouched.

Keep these boundaries explicit:

- Catch failures from opening/observing/re-verifying the target, including
  `fstat`, bounded read/hash, extended-attribute inspection and directory
  listing where applicable.
- Do not broaden removal authority. An unreadable or incompletely observed
  object is never `A1_INTACT` and is never unlinked.
- Preserve the distinction between `kept-damaged`, `kept-foreign`, `absent`
  and `unremovable`; choose the most conservative existing class supported by
  the facts actually established and pin that choice in tests.
- Do not catch or translate exceptions raised by `before_unlink`. Normal CL
  G-R1 relies on that callback for its durable write-ahead line, and an
  evidence-write failure must still enter the existing GP-R3 path rather than
  being mislabeled as a filesystem mismatch.
- Preserve `ENOENT` as `absent`, unlink errors as `unremovable {errno}`, and
  ignored parent-directory flush errors exactly as the accepted contract
  states.
- Keep GRR free of locks, spawns, signals, authorization calls, network work
  and ext4 evidence writes.
- Do not solve the issue only by wrapping `_igr()` or `_cl_g()` in a broad
  exception handler. The filesystem boundary itself must honor its typed
  `Removal` protocol so all GRR callers receive the same behavior.

If a narrow supporting helper is useful, keep it inside the adapter and test
it through `LocalActivationFs.remove()` rather than duplicating recovery logic
in the holder and cleanup procedures.

## Required regression tests

Add tests at the concrete adapter boundary and at all three recovery callers.
At minimum prove:

1. A failure during rule content read/hash re-verification returns a
   conservative mismatch result, does not raise and leaves the rule in place.
2. A failure during `fstat` or equivalent descriptor inspection behaves the
   same way.
3. A failure in the fallback observation path after the final open fails also
   returns a typed non-removal result rather than escaping.
4. Inline IGR reaches `done`, records the selected kept outcome and exact
   in-memory identity when its ACT journal remains writable, then emits
   `run-end` and releases K in the already-selected order.
5. Stop-post CL-G continues into CL-0 through CL-7 after the same injected
   inspection failure, keeps the grant, reports a hard-stop/residual result and
   does not claim `st1-verified`.
6. Backstop CL-G has the same behavior and retains its existing retry/disarm
   rules; it must not crash before recording its attempt outcome.
7. A `before_unlink` `EvidenceWriteError` still propagates into the existing
   GP-R3 handling. The remediation must not turn it into `kept-*` or allow an
   unlink without its required write-ahead evidence.
8. Existing absent, damaged, foreign, removed and unlink-unremovable cases keep
   their current outcomes.

Use deterministic failure injection around the concrete adapter operations;
do not require a genuinely damaged filesystem. Mutation-test the fix by
temporarily restoring the uncaught inspection path, show that the new tests
fail, then revert the mutation and confirm the working tree is restored.

## Required verification

All test levels remain authorized on `oracle-test`; use only synthetic data.
Synchronize with the documented secret-excluding command and run, in order:

1. focused filesystem, hold, cleanup and backstop suites;
2. the complete Route 3 root systemd integration suite with the pinned Jeepney
   wheel;
3. the complete bot suite;
4. the complete web suite with exported
   `TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'`, confirming the
   database-enabled skip count;
5. the complete Foundry Node suite;
6. `.claude/hooks/test_guards.py`;
7. `git diff --check`, `compileall`, and every configured formatter, linter or
   type checker, or explicitly state that none is configured.

Run bot and web serially with the documented PostgreSQL 16 `PATH` and
`/opt/freedom-blades/runtime/venv-web` interpreter. A targeted rerun may
diagnose a failure but is not final regression evidence. Compare exact
failures, errors and skips with the established baseline; do not weaken tests
or repair unrelated baseline failures.

After root tests, verify that no holder/backstop unit, process, Polkit rule,
capture unit, Route 3 `/run` object, temporary artifact or new evidence remains
and that `polkit.service` is active.

## Acceptance criteria

- No inspection or re-verification failure supported by the concrete
  filesystem boundary escapes GRR.
- IGR, stop-post CL-G and backstop CL-G each receive a closed typed outcome and
  retain their required ordering and recovery behavior.
- No unreadable, partially observed, damaged, foreign or replaced object is
  removed.
- `before_unlink` evidence failures retain the existing G-R1/GP-R3 semantics.
- Focused and real-PID-1 tests pass, and the final-tree bot, web and Foundry
  suites introduce no regression relative to the accepted baseline.
- No production/staging state, real secret or player data is touched.

## Handback update

Update `docs/review/route-3-hold-role-implementation-handback.md` in place with
one concise current remediation section. Include the finding and disposition,
principal files changed, the selected typed outcome for each injected
inspection failure, exact final-tree commands/results, mutation-test result,
real-host cleanup confirmation, remaining production risks, and one
recommendation: accept the complete role series or remediate one named
blocker. Correct any superseded acceptance claim so the handback has one
unambiguous current recommendation.
