# Claude remediation prompt — Route 3 executor package boundary correction (review 5)

> **Historical assignment; the exact-environment sentence in requirement 1 was
> superseded on 2026-10-21.** Environment minimization and the PATH-only host
> observation remain defense in depth, not an atomic authorization invariant.
> The [sixth correction](route-3-executor-oc-implementation-handback.md#sixth-executor-review-correction-2026-10-21)
> defines the current boundary and also extends loaded-unit verification to
> effective drop-ins, identity and configured environment.

Date: 2026-10-20
Authority: Peter Duscha's direct instruction to implement the independent Codex
review recommendations and select the root-controlled system-service packaging
described below, under baseline v1.9
Reviewer after handback: Codex
Mode: one bounded implementation and disposable-host proof cycle; no production
or staging installation or activation

## Assignment

Correct the five remaining Route 3 executor package defects identified by
independent Codex review. Keep the accepted executor behavior and ownership
protocol: one persistent unprivileged supervisor, one separate transient user
service per admitted invocation, durable ownership before launch, one-shot SA-2,
and the exact fixed privileged vector.

Change only the supervisor's persistent deployment wrapper: install it as a
root-owned **system service** running with `User=freedom-executor` and
`Group=freedom-executor`. The dedicated account's lingering systemd user manager
continues to own the per-invocation transient services. The supervisor still
runs unprivileged and reaches that user manager through its fixed bus/runtime
boundary; do not move transient invocations into the system manager.

This explicit selection replaces the unaccepted globally enabled user-service
wrapper. It is a bounded, reversible deployment correction, not a redesign of
the executor protocol and not another research/proof chain. Update the existing
executor handback in place. Do not create another handback, commit or push.

The focused final-tree executor and installer suite independently reported
**435 passed** on `oracle-test`. Those tests do not cover the five defects below.

## Governing context

Before editing, read and follow:

1. `.agents/AGENTS.md` completely;
2. the implementation-plan reading map and §§0, 3, 5, 12 Phase 5.0, 13, 14,
   16 and 20;
3. `docs/review/Handover information`;
4. `docs/project-management/active-delivery-plan.md`;
5. `docs/operations/disposable-test-server.md`;
6. the original executor prompt, completion prompt, all preceding executor
   remediation prompts and the complete current executor handback;
7. all files under `application/executor/`, `adapters/executor/` and
   `infra/executor/`, the installer, provisioning runbook, all executor tests,
   the current diff and production-file scope guards; and
8. the accepted SA-2 implementation and its exact privileged vector.

The working tree is the implementation base. Preserve unrelated maintainer
changes and every accepted Route 3 role. Historical WP labels are not gates.

Peter's direct instruction authorizes this inactive package correction and the
current-state documentation changes necessary to record it. It does not
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
later capture-unit state to promote uncertainty. The dedicated user manager
creates each invocation process directly in its uniquely named transient user
service. Preserve the fixed capture unit, exact OC-1/OC-2/OC-3 gate,
consume-journal validation, durable slot and drain protocol, stable diagnostics
and CX-3/Lemma R6 behavior.

Do not weaken root ownership of installed code, the system unit or its
dependencies. Do not give the service account authority to edit, enable,
disable, reload or replace the persistent supervisor service.

## Required corrections

### 1. Ignore account- or manager-controlled Python configuration

The current supervisor command uses Python `-s`, which still honors
`PYTHONPATH`, `PYTHONHOME` and other `PYTHON*` variables. That permits imported
modules to be redirected outside the validated root-owned tree.

- Start the supervisor interpreter with `-E -s`. Keep the absolute interpreter
  path and module entry point otherwise unchanged.
- Give the system service a deterministic minimal environment needed by the
  supervisor. Do not depend on an inherited manager or account environment.
- Prove with hostile `PYTHONPATH`, `PYTHONHOME`, `PYTHONUSERBASE` and another
  relevant Python variable that the real service imports only the validated
  root-owned code and dependency tree.
- Keep the transient invocation environment exactly `PATH=/usr/bin:/bin`; this
  correction must not weaken the already-proved invocation environment.

### 2. Replace the shadowable user-service wrapper with one system service

A root-owned fragment in `/etc/systemd/user` is not a root-controlled service
when the dedicated account owns a higher-precedence user-unit directory. A
point-in-time shadow check cannot prevent the account from creating a shadow
later. `ConditionUser=` in the original fragment is not sufficient because a
replacement fragment can omit it.

- Install the persistent supervisor fragment in `/etc/systemd/system` and run
  it as `User=freedom-executor`, `Group=freedom-executor`.
- Keep its code, interpreter, fragment and dependency trust checks root-owned
  and non-writable by the service account, its group or others.
- Keep the account non-login and lingering so its user manager is available for
  the transient invocation services. Preserve fail-closed retry/startup behavior
  while that user manager or bus is not ready.
- Use only the system manager to enable, start, stop, disable, reload and inspect
  the persistent supervisor. The service account must not be able to replace or
  control it through its user manager.
- A malicious same-named fragment created under the account's writable user
  configuration after installation must have no effect on the persistent
  supervisor's fragment, command, PID or restart behavior.
- Ensure the persistent service and its socket/state behavior still satisfy the
  existing root-maintenance and executor-peer authentication contract.

Do not solve this by making the dedicated account's whole home tree root-owned,
by relying on repeated shadow scans, or by retaining two persistent supervisor
units.

### 3. Reload and verify the manager that owns the installed fragment

The existing installer reloads the system manager even though it installs a
user fragment. With the corrected topology, make the manager operations
internally consistent and checked.

- After every install, upgrade, restore or unlink of the system fragment, run
  and verify the system manager's `daemon-reload`.
- Treat a reload failure as an install/removal failure. Preserve or restore a
  recoverable root-owned fragment and report a stable failure; never claim
  success while the manager may retain stale configuration.
- An upgrade must demonstrably load the new fragment before the service is
  considered ready.
- Removal remains atomic with supervisor admission: drain first, stop the
  system service while the drain connection proves that owner is still the one
  being stopped, recheck emptiness, then disable/unlink/reload. Any partial
  failure must leave a recoverable persistent owner or a safely restorable
  root-owned configuration.
- Account for safe migration from this repository's preceding inactive
  user-service candidate. Never allow the old user supervisor and the new
  system supervisor to run concurrently. Because that candidate was not
  accepted or deployed, it is acceptable to refuse a detected legacy install
  with one stable diagnostic and documented cleanup procedure rather than
  invent a risky automatic migration.

### 4. Make every code-trust traversal bounded while enumerating

The current walker materializes a complete directory before applying
`MAX_WALK`; the `site-packages` path similarly sorts a complete name list.
Those are unbounded allocations even though later validation has a count limit.

- Consume directory iterators incrementally with a shared remaining-entry
  budget and at most one extra entry to detect overflow.
- Apply the same bound before materialization or sorting in every trust walk,
  including `site-packages`, imported code trees, interpreter/dependency trees
  and any helper reached by them.
- Preserve descriptor-relative, no-follow, owner/type/mode/depth checks and the
  stable `code-too-large` refusal.
- Do not sample an oversized tree, silently omit entries or trade the memory
  bound for an unbounded sort.

### 5. Scope enablement to the one persistent service

`systemctl --global enable` activates the current user unit for every user's
manager. The earlier host drill actually started an unwanted supervisor for
`ubuntu`.

- Remove all global user enablement from install, verification and removal.
- Enable only the root-owned system service in the system manager.
- Assert that no global or per-user `default.target.wants` link is created for
  the supervisor and that another active or lingering user's manager never
  starts it.
- Verify there is exactly one persistent supervisor, running as the dedicated
  uid, while transient invocation units remain in that uid's user manager.
- Update the runbook so it no longer describes or accepts global user-unit
  activation or post-install shadowing as a residual risk.

### 6. Reconcile current authority text

Make the smallest current-state documentation update needed to record Peter's
selection of the inactive root-controlled system-service wrapper. Clarify that
the dedicated user manager still owns transient invocation services. Update
the implementation plan, active delivery plan, active handover, status and the
existing decision/change records only where their current statements would
otherwise be false or ambiguous.

Do not record acceptance, authorize production/staging activation, assign a
successor slice or rewrite historical review evidence.

## Required regressions

Add deterministic tests which fail on the current candidate and prove at
least:

1. the persistent unit invokes the absolute interpreter with `-E -s` and a
   hostile Python environment cannot redirect any supervisor import;
2. the installed fragment is a system unit with the exact dedicated `User=` and
   `Group=`, and no persistent user-service fragment or enablement is installed;
3. a same-named malicious unit created in the account's user configuration
   after installation cannot change, replace or restart the system supervisor;
4. a different active/lingering user's manager never starts a supervisor and
   receives no supervisor state/runtime residue;
5. install and upgrade perform a checked system `daemon-reload`, and the new
   fragment is the configuration used after restart;
6. reload failure, stop failure, disable failure, unlink failure and
   post-unlink reload failure each fail closed with a recoverable fragment or
   persistent owner and no ownership gap;
7. removal racing stop admission preserves the existing drain guarantee under
   the system-service topology;
8. a detected old user-service installation cannot coexist with or race the
   new system service;
9. an oversized single directory causes `code-too-large` after bounded iterator
   consumption and bounded retained memory, both in the general walker and at
   the `site-packages` level;
10. a fully root-owned fixed tree, interpreter, dependencies and system
    fragment install, verify, become ready, survive supervisor restart and
    remove through the drain protocol;
11. the persistent system supervisor still creates each transient invocation
    only through the dedicated account's user manager with exactly
    `PATH=/usr/bin:/bin` and the unchanged fixed SA-2 vector; and
12. all preceding ownership, ambiguous-start, restart, cgroup-identity, drain,
    status-mapping, concurrency, OC-gate, journal-integrity, fixed-vector,
    one-shot, unrelated-unit and stable-diagnostic regressions remain unchanged.

Use barriers at the real admission/drain and manager-operation boundaries for
race tests. A mock that only records a command without modeling its result or
the relevant manager state does not establish upgrade/removal recovery.

## Disposable-host proof

Use synthetic data and the canonical secret-excluding synchronization. All
system-level work is limited to `oracle-test`. Record and restore the original
account, home, linger, system/user units, manager environments, sudoers,
runtime, state, filesystem ownership and host-cleanliness state.

On the final code, prove through real systemd managers:

- install creates and enables exactly one root-owned system service which runs
  as `freedom-executor`, while its lingering user manager owns only the
  transient invocation units;
- hostile Python manager/service variables do not alter the imported code or
  dependency paths;
- creating and enabling a malicious same-named user fragment after install has
  no effect on the persistent supervisor;
- an active second user manager never receives or starts the supervisor;
- an installed-fragment upgrade plus checked daemon reload and restart uses the
  new fragment, while injected reload failure never reports success;
- removal drains admission, refuses under a pending invocation, and succeeds
  only after affirmative emptiness without leaving system or global-user
  enablement;
- a request racing removal is either admitted under the persistent owner or
  refused before launch, never launched into an ownership gap;
- supervisor restart with a live contained member retains the durable record,
  block and eventual recovery;
- a real reboot starts the system supervisor and the lingering dedicated user
  manager without an interactive login, preserves fail-closed ordering while
  the bus becomes ready, and never starts another user's supervisor; and
- an oversized test tree refuses at the configured bound without unbounded
  enumeration or an OOM condition.

Do not install or enable anything in production or staging.

## Verification

On the final synchronized tree run:

- all executor ownership, user-manager, supervisor, interrupt and installer
  tests;
- all executor host modules plus the new system-service, hostile-environment,
  shadowing, reload/upgrade, multi-user and bounded-enumeration proofs;
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
for the privilege, hostile-environment, manager-reload, removal race, reboot
and cleanup proofs where invocation details affect the claim.

## Acceptance criteria

Recommend acceptance only if all are true:

1. the persistent supervisor ignores all account-controlled Python
   configuration and imports only validated root-owned code/dependencies;
2. its persistent fragment and lifecycle are controlled solely by the system
   manager while its process runs as the dedicated unprivileged account;
3. account-owned user configuration cannot replace or affect the persistent
   supervisor;
4. install, upgrade and removal reload the correct manager and cannot report
   success with stale or unrecoverable configuration;
5. every trust traversal is bounded during enumeration, not only after names
   have been collected;
6. enablement starts exactly one supervisor for the dedicated account and no
   supervisor for any other user;
7. the dedicated user manager still owns the separate transient invocation
   services, with the exact environment and fixed SA-2 vector;
8. every earlier persistent-ownership, drain and OC invariant remains proved;
9. current-state authority and the runbook accurately describe the corrected
   inactive topology while production/staging activation remains prohibited;
   and
10. the real-host proofs, full regressions and final cleanliness check pass.

If a criterion cannot be met without broadening privilege, changing the fixed
SA-2 vector, weakening ownership, moving transient invocations out of the
dedicated user manager, or touching production/staging, stop on that exact
authority decision. Do not substitute a periodic shadow check, `ConditionUser=`,
a best-effort reload, unbounded enumeration, manual cleanup instruction or risk
acceptance recommendation.

## Handback

For the implementation handback, update the existing
`docs/review/route-3-executor-oc-implementation-handback.md`; do not create a
second handback. Append one concise
**Fifth executor review remediation** section containing:

- behavior corrected and exact files changed;
- the final persistent-system-service/transient-user-service topology;
- Python isolation, unit ownership, reload/recovery, bounded-traversal and
  single-account activation invariants;
- material final-tree tests and real-host results, including every failure,
  error and skip;
- the observed persistent and transient service identities, managers,
  environments and enablement paths;
- reboot, hostile-environment, shadowing, upgrade/removal-race and final
  host-cleanliness results;
- remaining production risks and deployment decisions; and
- one recommendation: accept for continued non-production development only if
  every criterion above is proved, otherwise keep the slice blocked on the
  precise remaining issue.

Do not record Peter's acceptance, assign another implementation slice, or
authorize production/staging installation or activation.
