# Claude remediation prompt — Route 3 executor OC lifecycle completion (review 2)

Date: 2026-10-19
Authority: Peter Duscha's request for a bounded remediation prompt, baseline
v1.9, the active implementation-first delivery plan, and independent Codex
re-review of the uncommitted executor OC candidate
Mode: one bounded implementation-or-authority-stop cycle; disposable-server
testing authorized; no production or staging activation

## Assignment

Resolve the one remaining blocking finding in the Route 3 non-root executor OC
slice:

> After a successful privileged launch, `SudoStopInvoker` can return
> `PrivilegedStop.UNSETTLED`, or propagate an ordinary exception, while an
> invocation member remains alive.

The current private delegated-cgroup design materially improves containment,
but it does not satisfy the accepted lifecycle invariant. In particular:

- `_supervise()` returns `UNSETTLED` when `_settlement()` cannot establish an
  empty child and cgroup boundary;
- `_after_settling()` likewise returns `UNSETTLED`;
- the two `BaseException` paths call `_settle()` but ignore its false result
  before re-raising;
- `invoke_stop()` then closes the supervision scope; and
- `test_a_descendant_that_survives_term_and_every_kill_round_is_unsettled_not_hidden`
  explicitly asserts that the invoker returned while the straggler remained.

That behavior contradicts the preceding remediation's acceptance criterion:
no path may return or propagate an ordinary exception after a successful
privileged launch while any invocation member remains. The alternative allowed
by that criterion is an explicit authority stop without a completion or
acceptance claim.

Do not broaden this assignment into the full coordinator, scheduler, start
orchestration, automatic attestation, production installer, sudoers policy,
migration/cutover work, or production/staging activation. Do not commit or
push.

## Governing context

Before editing, read and follow:

1. `.agents/AGENTS.md` completely;
2. the implementation-plan reading map and §§0, 12 Phase 5.0, 13, 14, 16 and
   20;
3. `docs/review/Handover information`;
4. `docs/project-management/active-delivery-plan.md`;
5. `docs/operations/disposable-test-server.md`;
6. the original executor prompt, completion prompt, first remediation prompt
   and complete current handback;
7. `application/executor/interrupt.py`, both executor adapters, all executor
   tests and the current diff; and
8. the accepted SA-2 implementation and its fixed privileged vector.

Preserve the accepted manager/Polkit adapter and the accepted `start`, `stop`,
`consume`, `attest`, `hold`, `stop-post` and `backstop` roles. Preserve the
corrected consume-journal name and metadata validation. Historical WP closure
labels are not development gates.

## Required disposition

Choose exactly one of the following based on executable evidence. Do not claim
both.

### A. Complete the lifecycle invariant within the current authority

Implement this only if the exact fixed boundary can satisfy every condition:

1. After any successful launch, no normal result and no propagated ordinary
   exception leaves the invoker until the kernel affirmatively establishes
   both `ECHILD` and an empty invocation containment boundary.
2. Timeout, `SIGTERM`, `SIGINT`, repeated signals, direct-child exit,
   reparenting, late descendants, a lost launch handle, process-count pressure
   and settlement I/O errors cannot abandon a member.
3. No unrelated process is identified, signalled, reaped or accepted from a
   numeric PID, process name, command line or stale `/proc` observation.
4. SA-2 is attempted at most once. Uncertainty is never retried or promoted to
   success, and later unit state is not consulted.
5. Resource use and the ordinary successful path remain bounded and prompt.
6. The fixed privileged vector remains exactly:

   ```text
   sudo -n /usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py stop
   ```

Deleting or renaming `UNSETTLED` is not a correction. Returning another error,
closing the scope, or re-raising while a member remains is not settlement.
Waiting forever, broad process killing, suppressing termination indefinitely,
or adding a broader privileged command is also not permitted.

If disposition A is achieved, remove regressions that endorse return with a
live member and replace them with tests proving every post-launch exit path has
affirmative empty-boundary evidence. Include ordinary-exception and settlement-
failure injection, not just expected timeout and signal paths.

### B. Stop on the required authority decision

Use this disposition if a member can remain after the bounded `cgroup.kill`
rounds—for example, a task in uninterruptible sleep—or if any other kernel case
prevents bounded affirmative settlement under the exact boundary.

Do not change production code merely to produce a different token. Do not
recommend acceptance of the executor slice. Append a concise authority-stop
section to the existing handback that states:

1. the exact kernel and credential reason bounded disappearance cannot be
   guaranteed;
2. why the current `UNSETTLED` return violates the accepted lifecycle
   invariant even though it is fail-closed about SA-2's result;
3. the smallest proposed ownership change—normally a persistent
   systemd/coordinator-owned scope that retains the invocation, blocks further
   orchestration and continues recovery until the boundary is empty;
4. whether that proposal changes the lifecycle invariant from “the executor
   returns only after settlement” to “the executor may hand an unsettled but
   kernel-contained invocation to a persistent owner”;
5. its security, authorization, availability, resource and recovery effects;
6. the focused disposable-host tests needed to prove containment, handoff,
   restart recovery, no duplicate SA-2 invocation and eventual cleanup; and
7. the exact maintainer decision required before implementing that ownership
   change.

The full coordinator remains out of scope until Peter explicitly approves the
changed ownership contract. A design suggestion is not authority to implement
it.

## Required regressions for disposition A

If and only if disposition A is technically achieved, cover at least:

1. normal statuses 0, 20, 21, 22, unexpected status and signal death;
2. timeout, `SIGTERM`, `SIGINT` and repeated signals;
3. descendants present before termination and created during the termination
   race;
4. a direct child gone before discovery while a descendant remains;
5. an initially termination-ignoring privileged descendant;
6. a lost launch handle and an ordinary exception after child creation;
7. failures from every settlement observation or kill operation;
8. process-count/resource-cap pressure;
9. inconsistent identity evidence and unrelated-process isolation; and
10. scope-unavailable and pre-existing-child refusal before launch.

Every post-launch case must assert that the child view is `ECHILD`, the
containment boundary is empty, no invocation process remains and SA-2 was not
retried. A test that removes a survivor after the invoker returns proves the
defect, not the correction.

Retain all OC-1/OC-2/OC-3, CX-3, Lemma R6, fixed unit, fixed argv/environment,
journal-integrity and stable-diagnostic regressions.

## Verification

All test levels remain authorized on `oracle-test`; production and staging do
not. Use synthetic data and the documented secret-excluding synchronization.

For disposition A, run on the final synchronized tree:

- the complete executor application/adapter/supervision tests inside the
  delegated unprivileged service;
- the complete executor host module through the real
  `ubuntu -> sudo -n -> SA-2` boundary;
- focused accepted `stop`, `consume`, `attest`, manager, artifact and
  unit-control regressions;
- the complete `tests/systemd_integration` suite serially;
- the documented bot and web suites serially with the required database
  environment and web skip count, followed by Foundry;
- compilation, guards, configured static checks and `git diff --check`; and
- a separate final host-cleanliness inspection.

Report reliable pass/fail/error/skip counts and compare any claimed existing
failure to the accepted baseline. The final cleanliness check must include
processes and delegated cgroups as well as the existing RP-11 artifact, unit,
Polkit, evidence and `/var/tmp` checks.

For disposition B, run only the focused deterministic and disposable-host
experiments necessary to establish the kernel limitation and confirm that the
already-correct OC gate and journal remediation remain unchanged. Do not rerun
unrelated full suites merely to manufacture a green count.

## Acceptance criteria

The result is reviewable only when one of these is true:

- **Disposition A:** every post-launch return and propagated ordinary exception
  has affirmative kernel evidence that no invocation member remains, with the
  required executable regressions; or
- **Disposition B:** the handback clearly keeps the slice blocked and asks one
  precise maintainer question about transferring unsettled-invocation
  ownership to a persistent supervisor/coordinator.

In either case, SA-2 remains one-shot, uncertainty is never promoted, journal
validation remains fixed, accepted roles are unchanged, production/staging are
untouched, and no real secret or player data is used.

## Handback

Update the existing
`docs/review/route-3-executor-oc-implementation-handback.md` in place with one
concise **Second executor review remediation** section. Do not create another
handback.

State:

- whether disposition A or B was taken and why;
- the exact code and tests changed, if any;
- material final-tree results and skips;
- host-cleanliness state;
- remaining production risks; and
- exactly one recommendation: accept for continued non-production development
  only if disposition A is fully proved, otherwise keep the slice blocked on
  the named authority decision.

Do not record Peter's acceptance, assign a successor slice, or authorize a
production installer or activation.
