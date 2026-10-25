# Claude remediation prompt — Route 3 executor ownership and package correction (review 4)

> **Historical assignment; requirement 4 was superseded on 2026-10-21.** The
> PATH-only observation remains a regression target, but exact environment
> equality cannot be atomic across the manager query and `StartTransientUnit`
> and is not an authorization invariant. See the
> [sixth correction](route-3-executor-oc-implementation-handback.md#sixth-executor-review-correction-2026-10-21).
> The fixed sudoers/SA-2 argv, Python `-I -S` and the root-owned `stop` artifact's
> no-environment-read path are the current privileged boundary.

Date: 2026-10-19
Authority: Peter Duscha's direct instruction to implement the independent Codex
review recommendations, baseline v1.9, and the approved persistent-ownership
architecture
Reviewer after handback: Codex
Mode: one bounded implementation and disposable-host proof cycle; no production
or staging installation or activation

## Assignment

Correct the remaining Route 3 executor ownership defects and the inactive
production-package defects identified by independent Codex review. Keep the
selected architecture: a persistent supervisor under the systemd user manager,
one separate transient service per admitted invocation, a durable ownership
record before launch, and the exact fixed SA-2 vector.

This is a focused correction, not an architectural restart and not another
research/proof chain. Update the existing executor handback in place. Do not
create another handback, commit or push.

The focused final-tree executor and installer suite independently reported
**318 passed** on `oracle-test`. Those passing tests do not cover the blocking
races and trust-boundary gaps below.

## Governing context

Before editing, read and follow:

1. `.agents/AGENTS.md` completely;
2. the implementation-plan reading map and §§0, 12 Phase 5.0, 13, 14, 16 and
   20;
3. `docs/review/Handover information`;
4. `docs/project-management/active-delivery-plan.md`;
5. `docs/operations/disposable-test-server.md`;
6. the original executor prompt, completion prompt, all three preceding
   remediation prompts and the complete current executor handback;
7. all files under `application/executor/`, `adapters/executor/` and
   `infra/executor/`, the installer, provisioning runbook, all executor tests,
   the current diff and production-file scope guards; and
8. the accepted SA-2 implementation and its exact privileged vector.

The working tree is the implementation base. Preserve unrelated maintainer
changes and every accepted Route 3 role. Historical WP labels are not gates.

Peter's direct instruction for this remediation authorizes corrections to the
inactive supervisor package, installer and runbook described below. It does not
authorize installation or activation in production or staging, changes to the
account/linger/sudoers state of either environment, a broader sudo command, the
full coordinator, scheduler, start orchestration, automatic attestation,
migration/cutover, RB-1, grants, rewards or game-data behavior.

## Fixed boundaries

The privileged vector remains exactly:

```text
sudo -n /usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py stop
```

SA-2 remains one-shot. Recovery never launches or retries SA-2 and never uses
later capture-unit state to promote uncertainty. The user manager creates the
process directly in its uniquely named transient service. Preserve the fixed
capture unit, exact OC-1/OC-2/OC-3 gate, consume-journal validation, stable
diagnostics and CX-3/Lemma R6 behavior.

## Required corrections

### 1. Never clear an ambiguous same-boot start on elapsed time

`start-sent` means the `StartTransientUnit` request may have escaped. Current
recovery clears that record when the deterministic unit name remains absent for
`start_resolve` seconds. Elapsed time is not affirmative evidence that a queued
or delayed request cannot subsequently create the unit.

- A same-boot `start-sent` record whose unit is absent must remain durable and
  blocking unless an exact manager/kernel fact proves that this particular
  request cannot later create the unit.
- Do not use a timeout, repeated absence reads or process observation as that
  proof.
- If no such conclusive same-boot fact is available through the selected API,
  retain the block until reboot. The already-approved changed-boot rule may
  clear it because the old boot's request and cgroup cannot survive.
- A `prepared` record may still clear after affirmative unit absence because
  the start-sent commit did not occur and the call therefore could not have
  been issued.
- Never resend `StartTransientUnit`.

Availability loss after a crash in the narrow `start-sent`-before-call window
is an accepted fail-closed consequence for this slice; do not trade ownership
safety for a same-boot timeout heuristic.

### 2. Make the live record impossible to starve behind directory pressure

Current `listing()` truncates arbitrary `scandir()` order before sorting, so
more than `MAX_ENTRIES` earlier junk entries can hide the real record forever.
Replace that design with a directly addressable active-ownership slot or an
equally strong bounded design.

The preferred small design is one fixed active-record name because admission
already permits only one invocation. The nonce, boot identity, deterministic
unit name and bound containment identity remain inside the descriptor-safe,
durably replaced record. Malformed or extra entries continue to block
admission, but they must never prevent recovery from reading and driving the
real active record on every pass. Preserve bounded CPU, memory and record size.

Do not solve this by performing an unbounded full-directory scan on every pass.

### 3. Make installer removal atomic with admission

The installer currently checks records and transient units, then stops the
supervisor in a separate operation. A request can be admitted between the
check and stop, leaving a record and invocation without a persistent recovery
worker.

Add a narrow maintenance/drain operation owned by the supervisor:

- authenticate the maintenance peer exactly (root for the installer; normal
  stop clients remain the dedicated executor uid);
- acquire the same admission serialization used by `handle_stop`;
- enter a drain state that refuses all later stop admission;
- while admission remains closed, affirmatively establish that there is no
  ownership record, damaged/unreadable state, active adopter or matching
  transient invocation unit;
- acknowledge safe removal only in that state; and
- keep admission drained until systemd stops the supervisor.

If the connection is lost, any check is inconclusive or stopping/disabling/
unlinking fails, fail closed without claiming successful removal. An installer
must never infer safety from its own racy filesystem and `list-units` snapshots.
Installation remains inactive; do not make `install` start the service.

### 4. Enforce and prove the exact invocation environment

The transient invocation must receive exactly `PATH=/usr/bin:/bin`. Reading the
user manager's `Environment` property and unsetting only those names is
insufficient: systemd also injects variables such as `INVOCATION_ID`,
`SYSTEMD_EXEC_PID`, `MANAGERPID` and memory-pressure variables.

Use `UnsetEnvironment` or another systemd-native property that does not alter
the fixed `ExecStart` vector to remove every manager-inherited and
systemd-generated variable other than the fixed `PATH`. Keep the executable
and argv unchanged; do not insert `env`, a shell or another wrapper into
`ExecStart`.

Add a real-host stand-in probe which records its environment from the actual
transient invocation unit and asserts exact equality with the one fixed PATH
entry. Do not weaken the contract to an undocumented allowlist in this
remediation. If systemd 259 cannot express the exact environment without
changing the fixed vector, stop and identify that one concrete authority
decision instead of silently accepting extra variables.

### 5. Close production code-trust gaps

The installer/runbook claim that imported code, symlink targets and
dependencies are root-owned and not writable by the executor account, group or
others must be true in code.

- Reject symlinks anywhere in the imported `adapters/` and `application/`
  trees unless the implementation descriptor-safely resolves and validates the
  complete target chain. Rejecting them is preferred for this bounded slice.
- Validate the service interpreter's complete path chain and the dependency
  tree it imports from the venv, including `jeepney`; a trusted interpreter
  executable with writable `site-packages` is not sufficient.
- Validate every traversed directory and file for owner, type and write modes,
  without following an untrusted link or escaping the fixed roots.
- Preserve bounded traversal. If the dependency tree exceeds the bound, refuse
  with a stable diagnostic rather than sampling it.
- Apply the same trust checks to the repository service fragment before root
  installs it.
- Check all source/destination reads and writes for completeness, including
  short reads and short writes, and retain the no-overwrite/durable-directory
  behavior.

Update the runbook so its claims exactly match the enforced checks.

### 6. Reconcile current authority text

The current plan/handover still says no production installer is assigned,
while the handback records Peter's later production-package direction. Make the
smallest current-state documentation correction needed to record that this
inactive package and its remediation were directly assigned. Do not record
acceptance, authorize activation, assign a successor slice or rewrite
historical review evidence.

## Required regressions

Add deterministic tests which fail on the current candidate and prove at
least:

1. a same-boot `start-sent` record plus repeated unit absence remains blocking
   beyond every former resolution deadline;
2. a delayed unit appearing after that interval is adopted and settled exactly
   once, with no second `StartTransientUnit` call;
3. a `prepared` record with affirmative absence still clears safely, and a
   changed-boot record clears under the approved reboot rule;
4. more than the entry limit of junk created before the real ownership record
   cannot hide or starve that record, while work and memory remain bounded;
5. malformed and overflow state blocks admission but does not prevent the real
   invocation from receiving cleanup work;
6. concurrent removal and a stop request cannot produce a launch after the
   drain acknowledgment or stop the owner while an invocation is admitted;
7. lost drain replies, wrong peer uid, supervisor restart during drain,
   unreadable state and matching-unit observation failures all refuse removal;
8. install remains inactive and failed/partial removal leaves a recoverable
   supervisor configuration;
9. the real transient member environment is exactly
   `PATH=/usr/bin:/bin` and contains no manager- or systemd-generated extras;
10. symlinks in either imported code tree, writable symlink targets, writable
    dependency files/directories, a writable or linked service fragment, short
    reads and short writes all refuse before installation changes state;
11. a fully root-owned fixed tree, interpreter, dependencies and fragment still
    install, verify, become ready and remove through the drain protocol; and
12. all preceding ownership, restart, cgroup-identity, status mapping,
    concurrency, OC gate, journal-integrity, fixed-vector, one-shot,
    unrelated-unit and stable-diagnostic regressions remain unchanged.

For concurrency tests, use barriers at the actual admission/drain boundary;
tests that merely run the calls sequentially do not establish the claim.

## Disposable-host proof

Use synthetic data and the canonical secret-excluding synchronization. All
system-level work is limited to `oracle-test`. Record and restore the original
linger, user-unit, account, sudoers, runtime, service, filesystem ownership and
host-cleanliness state.

On the final code, prove through the real systemd 259 user manager:

- an ambiguous same-boot record stays blocking beyond the former timeout and a
  delayed deterministic unit is adopted without a duplicate launch;
- directory pressure cannot starve the real record;
- the actual transient invocation environment contains exactly the fixed PATH;
- removal drains admission, refuses under a pending invocation, and succeeds
  only after affirmative emptiness;
- a request racing removal is either admitted under the persistent owner or
  refused before launch, never launched into an ownership gap;
- supervisor restart with a live contained member retains the record, block
  and eventual recovery; and
- install/verify/verify-ready/remove operate against the root-owned test
  package with the exact sudo vector and no broader privilege.

Do not reinstall or enable anything in production or staging.

## Verification

On the final synchronized tree run:

- all executor ownership, user-manager, supervisor, interrupt and installer
  tests;
- both executor host modules and the new environment/removal race proofs;
- focused accepted `stop`, `consume`, `attest`, manager, artifact and
  unit-control regressions;
- the complete `tests/systemd_integration` suite serially;
- the canonical bot and web suites serially with the documented PostgreSQL
  environment and exact skip reporting, followed by Foundry;
- compilation, guard tests, configured static checks and `git diff --check`;
  and
- a final host-cleanliness inspection.

Report reliable pass/fail/error/skip counts. Do not call a failure pre-existing
without a meaningful accepted-baseline comparison. Exact commands are needed
for the environment, drain/removal race, privilege, restart and reboot proofs
where invocation details affect the claim.

## Acceptance criteria

Recommend acceptance only if all are true:

1. no ambiguous same-boot launch state is cleared on elapsed time;
2. bounded hostile directory pressure cannot starve a real invocation;
3. removal cannot close the persistent-owner service while admission or
   recovery may own an invocation;
4. the real transient process receives exactly the fixed environment and exact
   SA-2 vector;
5. installed executable code, dependencies and the unit fragment satisfy the
   claimed root-owned, non-writable trust boundary;
6. every earlier persistent-ownership and OC invariant remains proved;
7. governing current-state text accurately records the inactive package's
   authority while production/staging activation remains prohibited; and
8. the real-host proof and final cleanliness check pass.

If a criterion cannot be met without broadening privilege, changing the fixed
vector, weakening ownership, or selecting a different deployment architecture,
stop on that exact authority decision. Do not substitute another timeout,
best-effort result, manual cleanup instruction or acceptance recommendation.

## Handback

Update only
`docs/review/route-3-executor-oc-implementation-handback.md`. Replace or extend
its current production-package/review-request material with one concise
**Fourth executor review remediation** section containing:

- behavior corrected and exact files changed;
- ownership, bounded-recovery, drain and code-trust invariants;
- material final-tree tests and real-host results, including every failure,
  error and skip;
- the exact environment observed in the real transient unit;
- final host-cleanliness state;
- remaining production risks and deployment decisions; and
- one recommendation: accept for continued non-production development only if
  every criterion above is proved, otherwise keep the slice blocked on the
  precise remaining issue.

Do not record Peter's acceptance, assign another implementation slice, or
authorize production/staging installation or activation.
