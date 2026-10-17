# Claude remediation prompt — Route 3 `consume` review findings

Date: 2026-10-17
Authority: baseline v1.9, the active implementation-first delivery plan, and
the independent Codex review of the uncommitted RT-1 candidate
Mode: one bounded remediation and verification cycle on `oracle-test`; no
production or staging activation

## Assignment

Remediate the two blocking findings from the independent review of the
uncommitted RT-1 `consume` candidate:

1. a journal write or flush failure while recording an already-selected
   failure can bypass the required grant-priority path; and
2. an unexpected exception during CQ-5 can silently run the PK/2 authorization
   series a second time.

Add regressions that reproduce both defects before fixing them, make the
smallest fail-closed correction, rerun the required checks on the final tree,
and update the existing consume handback in place.

Do not return another plan or research package. Do not implement RT-5
`attest`, the non-root executor, OC-1/OC-2/OC-3, a production capture-unit
installer, migration/cutover work, production or staging activation, or
unrelated cleanup. Preserve all unrelated working-tree changes. Do not commit
or push.

The accepted manager/Polkit adapter, cleanup engine, `stop-post`, `backstop`,
`hold`, `start` and `stop` roles are not reopened. Do not weaken their
attribution, validation, artifact, authorization, result or test boundaries to
make this remediation pass.

## Read before editing

1. `.agents/AGENTS.md` in full.
2. `docs/implementation-plan.md`: reading map, §§0, 12 Phase 5.0, 13, 14, 16
   and 20.
3. `docs/review/Handover information`.
4. `docs/project-management/active-delivery-plan.md`.
5. `docs/operations/disposable-test-server.md`.
6. `docs/review/route-3-consume-role-implementation-claude-prompt.md` and
   `docs/review/route-3-consume-role-implementation-handback.md`.
7. The operation inventory §§3 RT-1, 4.4, 4.11, 5.1, 6 RT-1, 7, 8.1, 10.3
   and the RT-1 rows of §§11–12, especially `H-JRN.6`, `H-JRN.7`,
   `RT1.CQ3.9`, `RT1.CQ5.2`, `RT1.CQ6.1` and `RT1.CQ7.1`.
8. The interface contract §§3.0, 3.5 and 3.6, including the three-way Polkit
   result and no-retry/abandonment discipline.
9. `application/rp11/consume.py`, `adapters/rp11/consume.py`, the consume
   tests, and the complete current diff from accepted commit `7bdc930`.

Historical WP closure labels are not current development gates. Their
accepted RT-1, H-JRN, H-PK2, DI-5, DI-6 and H-SN requirements remain
implementation inputs.

## Blocking finding 1 — evidence failure bypasses grant priority

`ConsumeProcedure._failed()` currently ignores the Boolean results of both
best-effort appends:

```python
self._append("consume-failed", {"step": step.lower(), "class": klass})
self._append("run-end", {"outcome": "failed"})
return ConsumeOutcome(end, step, klass)
```

When either append or flush fails, `_append()` marks the journal unusable, but
`_failed()` returns the original CQ-3/CQ-4/CQ-5 result without entering
grant-priority processing. For example, an independently false CQ-4
`capture-root` precondition combined with failure of the fourth journal write
currently returns `consume-precondition`, reports `pk=absent`, and leaves only
`run-start`, `remove-intent` and `removed` in the journal. The required
in-memory negative-authorization check never runs.

Once the claim exists, **every** journal append or flush failure must enter the
accepted grant-priority form, including a failure while writing
`consume-failed` or its terminal `run-end`. The corrected behavior must:

- preserve the already selected non-zero result only while its failure
  evidence remains writable;
- on either failure-record append/flush failure, return the stable
  `consume-evidence-unwritable` result with a closed step/class diagnostic;
- write no later line after the journal becomes unusable;
- classify and remove only a grant provable from the ACT identity and pinned
  authority digest, without weakening the existing removal guard;
- if the attributable rule is absent after that processing and no PK/2 series
  has yet been attempted, run CQ-5's negative-authorization series exactly
  once with its result held only in memory;
- never continue or return to CQ-4; and
- always return non-zero, close K, retain the one-shot claim and never create a
  `consumed` line.

Do not turn an absent pathname into authorization proof. A damaged, foreign,
uninspected, unprovable or unremovable rule still cannot be claimed removed,
and a PK/2 error or authorization result still cannot become success.

Add focused write and flush fault-injection regressions for at least:

1. a CQ-3 failure whose `consume-failed` append or flush fails;
2. a CQ-4 failure whose `consume-failed` append or flush fails;
3. a CQ-5 non-decisive result whose `consume-failed` append or flush fails;
4. failure of the failure path's terminal `run-end` after a durable
   `consume-failed` line; and
5. the distinction between a case where PK/2 has not yet been attempted and a
   CQ-5 case where it already has.

For every case prove the exact non-zero end, journal prefix, rule residual,
PK/2 call count, absence of `consumed`, K release, retained claim and absence
of any resumed CQ-4 work.

## Blocking finding 2 — an unexpected CQ-5 exception retries PK/2

`_run_pk()` assigns `state.pk` only after `series.run(...)` returns. If that
call raises unexpectedly, the broad exception handler in `run()` invokes
`_grant_priority()`. Because `state.pk` is still `None`, `_grant_priority()`
calls `_run_pk()` again. The reviewed candidate was reproduced with
`series_runs == 2`.

The correction must distinguish **attempted** from **completed with a typed
result**. Mark the PK/2 series as attempted before entering it, or use an
equally explicit state transition. Grant-priority processing may start PK/2
only when no prior series was attempted. It must never retry after an
exception, typed error, unconfirmed result, interruption or abandonment.

An unexpected exception during CQ-5 must:

- remain a non-zero internal failure;
- leave the already removed grant absent;
- attempt exactly one PK/2 series total;
- start no replacement authorization subject or schedule;
- never append `consumed` or return 0;
- close K and retain the claim; and
- produce the fixed value-safe internal diagnostic required by the assignment,
  without falsely labelling every unexpected exception as CQ-3 or rendering
  exception text, paths, D-Bus detail, file content or environment values.

Preserve the existing grant-priority behavior before CQ-5: if an unexpected
exception occurs after the chain is trustworthy and before any PK/2 attempt,
the safely attributable grant is removed and one in-memory negative check may
run. This is one attempt, not a retry.

Add regressions for at least:

1. an exception raised from inside the first PK/2 series, proving exactly one
   series invocation and no second subject/schedule;
2. a typed `unconfirmed` result, proving it is not retried;
3. a grant-priority entry before CQ-5, proving one in-memory series may still
   run when none was previously attempted; and
4. the exact fixed internal diagnostic through the real `run_consume()` outer
   boundary, with no secret or exception-value leakage.

Do not catch default-terminating signals as ordinary exceptions and do not add
a signal handler to RT-1. The existing interruption and PID-1 timeout contract
remains unchanged.

## Required verification

All test levels remain authorized on `oracle-test`. Use synthetic data and the
documented secret-excluding synchronization command. Do not touch production,
staging, real secrets or player data.

Run on the final tree, at minimum:

1. the new regressions plus `tests/test_rp11_consume.py`,
   `tests/test_rp11_h1_artifact.py`, `tests/test_rp11_hold.py`,
   `tests/test_rp11_cleanup.py`, `tests/test_rp11_backstop.py`,
   `tests/test_rp11_records.py`, `tests/test_rp11_pk_sn.py`,
   `tests/test_rp11_start.py`, `tests/test_rp11_stop.py` and
   `tests/test_systemd_unit_control.py`;
2. `tests/systemd_integration/test_route3_consume_host.py` as root with a fresh
   controlled artifact built from the pinned Jeepney wheel;
3. the complete `tests/systemd_integration` suite serially;
4. `tests/web/test_p3_4_static_assets.py`, reporting the established unrelated
   baseline failures rather than hiding or repairing them;
5. the documented bot and web suites serially with
   `TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'`, confirming that
   the web skip count remains 80 rather than a false-green database-skipped
   count;
6. the Foundry Node suite;
7. Python compilation over every touched Python path; and
8. `git diff --check`.

Record exact copy-pastable commands, working directories, exit statuses,
pass/fail/error/skip counts and every skip reason. Do not cite pre-remediation
figures as final-tree evidence. Do not call a failure pre-existing unless it
is compared with a recorded applicable baseline or freshly reproduced against
the accepted base. Never run the bot and web suites in parallel because they
share the disposable database.

After root tests, verify separately that no RP-11 unit, process, Polkit rule,
artifact, staging/store path, test unit, new `/var/tmp/rp11-act-*` path,
consume evidence or test log remains; `polkit.service` is active; and the six
pre-existing `/var/tmp/p5-r5-rp11-h0*` directories remain untouched.

## Acceptance criteria

- Every post-claim journal append or flush failure, including while recording
  another failure, enters grant-priority processing and returns
  `consume-evidence-unwritable` without false durable evidence.
- Grant priority runs the negative authorization series in memory exactly once
  when appropriate and never treats pathname absence as its result.
- PK/2 is attempted at most once across every normal, error, exception and
  grant-priority path.
- An exception from inside PK/2 cannot start a second series, subject or
  schedule and cannot produce `consumed` or exit 0.
- Unexpected exceptions use the fixed value-safe internal diagnostic and are
  not all misreported as CQ-3.
- K closes, the claim remains the same-boot barrier, and the existing cleanup
  path recovers every tested residual.
- Existing CQ-0 through CQ-7 ordering, attribution, manager comparisons,
  negative authorization, artifact integrity and accepted role behavior remain
  intact.
- The disposable host is clean and production/staging remain unchanged.

## Handback and current-state update

Append one concise review-remediation section to
`docs/review/route-3-consume-role-implementation-handback.md`; do not create a
new handback. Include:

- both review findings and their exact dispositions;
- the new state used to prevent a PK/2 retry;
- the failure-record write/flush matrix and exact observed outcomes;
- principal files changed;
- exact final-tree commands and results, including failures and skips;
- host cleanup state;
- unchanged remaining production risks; and
- one recommendation: accept RT-1 for continued non-production development or
  remediate one specifically named remaining blocker.

Update the concise current-state documents only enough to say that this
remediation was returned for independent Codex re-review. Do not record Peter's
acceptance or start the next slice. Return the complete uncommitted candidate
for independent Codex re-review.
