# Claude remediation prompt — Route 3 executor persistent ownership (review 3)

> **Historical assignment; superseded in part on 2026-10-21.** Preserve this
> prompt as the record of its original scope. Any statement that the transient
> service's fixed environment is an exact security invariant is superseded by
> the [sixth correction](route-3-executor-oc-implementation-handback.md#sixth-executor-review-correction-2026-10-21):
> minimization is defense in depth, while the fixed sudoers/SA-2 argv, Python
> `-I -S` and the root-owned `stop` artifact's no-environment-read path form the
> privileged invariant.

Date: 2026-10-19
Authority: Peter Duscha's direct assignment, baseline v1.9, the approved
persistent-ownership decision, and independent Codex review of the second
executor remediation
Reviewer after handback: Codex
Mode: one bounded implementation and disposable-host proof cycle; no production
or staging activation

## Assignment

Complete the Route 3 non-root executor OC slice under Peter's approved
lifecycle contract:

> After a successful privileged launch, the executor may finish only after the
> invocation is affirmatively settled or after the still-kernel-contained
> invocation is durably owned by an already-established persistent supervisor
> that blocks further orchestration and continues recovery until the boundary
> is empty.

The second-remediation candidate does not meet that contract. Its marker is a
best-effort write after launch. If the marker cannot be written,
`SudoStopInvoker` can still return `UNSETTLED` with a live member. On the two
`BaseException` paths, `_settled_or_handed_off()` discards the failed hand-off
result and propagates the original exception while the scope closes. The
candidate also provides a callable recovery loop, not a proved persistent
supervised owner: the host test starts one-shot recovery processes manually.

Correct those defects in the existing implementation and update the existing
handback in place. Do not create another prompt, handback or proof chain. Do
not commit or push.

## Governing context

Before editing, read and follow:

1. `.agents/AGENTS.md` completely;
2. the implementation-plan reading map and §§0, 12 Phase 5.0, 13, 14, 16 and
   20;
3. `docs/review/Handover information`;
4. `docs/project-management/active-delivery-plan.md`;
5. `docs/operations/disposable-test-server.md`;
6. the original executor prompt, completion prompt, first and second review
   prompts, and the complete current executor handback;
7. all files under `application/executor/` and `adapters/executor/`, all
   executor tests, the current diff and the production-file scope guards; and
8. the accepted SA-2 implementation and its exact privileged vector.

The working tree, not `HEAD`, is the implementation base. Preserve unrelated
maintainer changes and every accepted Route 3 role. Historical WP closure
labels are not development gates.

## Approved decision and fixed boundaries

Peter approves the ownership-contract change described above. This assignment
authorizes the smallest implementation needed to make that contract real,
including an inactive repository-owned persistent-supervisor entry point and a
disposable-host service used to prove it. It does not authorize a full Package
5.0 coordinator, scheduler, start orchestration, automatic attestation,
production installer, production/staging service installation or activation,
migration/cutover, RB-1, grants, rewards or game-data behavior.

The fixed privileged vector remains exactly:

```text
sudo -n /usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py stop
```

SA-2 remains one-shot. Recovery must never launch or retry SA-2 and must never
consult later **capture-unit** state to promote uncertainty to success. The
separate transient invocation unit is the kernel ownership and result boundary
and must be observed through exact typed manager properties. Preserve the fixed
capture unit, exact OC-1/OC-2/OC-3 gate, consume-journal validation, fixed
environment, stable diagnostics and CX-3/Lemma R6 behavior.

### Selected ownership architecture

Use the systemd user manager as the persistent kernel owner and a separate
restartable `ubuntu` supervisor service as the admission/recovery worker. Each
accepted stop invocation must run in its own uniquely named transient
**service** unit created through the user manager's `StartTransientUnit` D-Bus
API. Its `ExecStart` must be the exact fixed `sudo -n` vector above with the
fixed environment. Do not attach an already-created child to a scope: systemd
must create the process in the transient service's cgroup so there is no
creation-to-attachment race.

The invocation unit must be distinct from the supervisor service. A member in
uninterruptible sleep may keep the invocation unit populated and stopping, but
must not keep the supervisor's own service cgroup populated or prevent that
supervisor from restarting. PID 1 and the user manager retain the invocation
unit/cgroup while the restartable supervisor resolves durable state and
continues cleanup. The short-lived executor becomes a client of the supervisor;
it no longer owns the launched process through `Popen`.

Before `StartTransientUnit` is sent, the supervisor must hold exclusive
admission and durably commit a `prepared` record containing at least a fresh
nonce, the current boot identity and the deterministic transient-unit name.
After an acknowledged start, bind the record to the manager-issued unit
`InvocationID` and the exact cgroup identity. If the supervisor dies during the
D-Bus call, its replacement resolves that one deterministic unit name: it must
never issue the start again. A nonterminal or unreadable record blocks every
later admission.

`oracle-test` currently provides systemd 259, unified cgroup v2 and an active
`ubuntu` user manager. `ubuntu` has `Linger=no`; the host proof may enable
linger temporarily so the user manager survives login/session loss, but must
restore the original setting during teardown. Whether production uses user
lingering or an equivalent system-level installation remains a later deployment
decision. Do not install or enable either in production or staging here.

## Required lifecycle behavior

### Ownership before launch

Before the `StartTransientUnit` launch request can be sent, all of the following
must already be true:

1. the systemd user manager and restartable supervisor are ready;
2. exclusive admission is held and durable recovery state identifies a fresh,
   deterministic invocation-unit name without relying on a numeric PID,
   process name, command line or stale `/proc` observation;
3. no unit or nonterminal record already owns that name; and
4. failure, absence, unreadability, malformed state, unavailable supervision
   or failed durability refuses launch as `NOT_SENT` or `BLOCKED`.

`StartTransientUnit` must be the sole process-creation operation: systemd
creates the fresh containment boundary and creates `sudo` directly inside it.
There must be no interval in which the process exists outside its owned
invocation unit.

A directory that does not exist is not evidence that hand-off will later work.
Creating a marker only after settlement fails is not sufficient. The explicit
record states must distinguish at least pre-start preparation, an ambiguous
start call, a manager-bound live invocation, cleanup and terminal clearance.
The supervisor must not treat a `prepared` or ambiguous record as an empty
completed invocation.

### No unowned post-launch path

After launch, every normal return and every propagated ordinary exception must
leave one of exactly two proved states:

- systemd has reaped the invocation's main process, its typed terminal status
  has been captured, and the exact transient unit/cgroup is affirmatively
  empty; or
- a durable, recoverable record for a still-contained invocation owned by the
  user manager and persistent supervisor, with further orchestration blocked.

This applies to timeout, `SIGTERM`, `SIGINT`, repeated signals, direct-child
exit, reparenting, late descendants, lost launch handles, launch exceptions
after child creation, settlement observation errors, `cgroup.kill` errors,
marker/state I/O errors, resource pressure and failures raised while another
failure is already being handled.

Do not discard a failed transfer and re-raise. Do not return `UNSETTLED` merely
as an honest incident token while nobody owns the live member. If durable
ownership cannot be guaranteed before launch, refuse the launch.

### Persistent supervisor

The selected owner is the systemd-user-manager/transient-service arrangement
above, with a real long-running supervised worker rather than a function an
operator may run later. It must:

- start and establish readiness before an executor launch is admitted;
- retain or rediscover every admitted invocation after its own process restart;
- keep the orchestration block active while any invocation is unsettled or any
  ownership state is unreadable or malformed;
- retry only containment cleanup (`cgroup.kill` and empty-boundary
  observation), never SA-2;
- remove durable state only after affirmative empty-boundary evidence, with an
  explicitly proved reboot case if disappearance is accepted after reboot;
- survive malformed, duplicate, stale-looking and partially written state
  without targeting an unrelated cgroup or silently dropping the block;
- use bounded work and memory per pass without starving a valid invocation
  behind malformed records; and
- shut down and restart without creating an ownership gap.

Add the inactive repository-owned user service/socket definitions and narrow
supervisor entry point needed to define this owner. Installing them on
`oracle-test` for the test is authorized. A production installer, production
linger change or activation is not.

### Identity, durability and concurrency

- Bind recovery state to the exact containment identity. A writable pathname
  and matching basename alone must not let planted, replaced, renamed or reused
  state target an unrelated cgroup.
- Make file and directory durability explicit. Check all writes, including
  short writes, and synchronize the state transitions whose survival is part
  of the claim.
- Use descriptor-safe, no-follow operations and validate owner, mode, type,
  link count and identity at every trust boundary.
- Serialize admission so two concurrent executors cannot both pass an empty
  marker check and launch. One admitted invocation is the maximum until it is
  affirmatively settled and its ownership state is durably cleared.
- A supervisor restart, executor crash or executor `SIGKILL` after admission
  must not lose the containment or permit another SA-2 launch.
- A crash before, during or after `StartTransientUnit` must be resolved from
  the deterministic unit name and durable state without sending that call a
  second time.
- Cleanup may signal only the recorded invocation containment boundary. It
  must not identify or signal a process by numeric PID, name or command line.

The ordinary successful path must remain bounded and prompt. Do not solve the
problem by waiting forever, suppressing termination indefinitely, broadly
killing processes, widening sudoers, or adding another privileged command.

## Required regressions

Add deterministic tests that fail against the second-remediation candidate and
prove at least:

1. missing, unwritable, full, short-writing and fsync/rename-failing state
   storage refuses before launch;
2. an absent, stopped, starting, stale or malformed owner refuses before
   launch;
3. a durable pre-launch record cannot be cleared as an empty completed
   invocation during the launch race;
4. normal statuses 0, 20, 21, 22, unexpected status and signal death preserve
   the existing typed mapping and clear ownership only after settlement;
5. timeout, `SIGTERM`, `SIGINT`, repeated signals, late descendants and lost
   handles either settle or remain durably owned;
6. an ordinary exception plus an unkillable member plus every injected
   persistence failure never propagates or returns while leaving the member
   unowned;
7. every settlement observation and `cgroup.kill` failure retains ownership
   and the orchestration block;
8. executor `SIGKILL` after admission leaves the owner able to recover and
   blocks a second invocation without retrying SA-2;
9. supervisor termination and restart while a member is in uninterruptible sleep
   retain containment, state and the block, then eventually clean up after the
   I/O is released;
10. crashes before, during and after `StartTransientUnit`, including an
    acknowledged-but-not-recorded reply, resolve the deterministic unit and
    result in at most one fixed SA-2 launch;
11. two concurrent executor calls result in at most one fixed SA-2 launch;
12. malformed, planted, replaced, renamed and stale/reused records never clear
    a live block and never kill an unrelated cgroup;
13. record-count/resource pressure remains bounded and cannot starve the real
    invocation indefinitely;
14. clean settlement leaves no marker, transient invocation unit, cgroup,
    child or persistent block; and
15. all prior OC-1/OC-2/OC-3, journal-integrity, fixed-vector, one-shot,
    unrelated-unit and stable-diagnostic regressions remain unchanged.

Do not write a test that cleans up the surviving member after the invoker has
returned and call that settlement. For the hand-off case, the assertions must
show that the persistent owner already existed and owned the invocation at the
instant the invoker returned or the exception propagated.

## Disposable-host proof

Use synthetic data and the canonical secret-excluding synchronization. On
`oracle-test`, exercise the final code through the real `ubuntu` user manager,
the repository-owned supervisor service, separate transient invocation service
and the real `ubuntu -> sudo -n` boundary. Temporarily enable user lingering if
needed, record its initial state and restore it during teardown.

The host proof must include:

- ordinary active OC success through the exact accepted SA-2 vector;
- a root member held in genuine uninterruptible sleep;
- durable ownership established before that member is launched;
- executor termination, including `SIGKILL`, while the member remains;
- a refused concurrent/second executor with zero additional SA-2 launches;
- termination and automatic restart of the supervisor service while the member
  remains in its separate transient invocation unit, with the block and
  containment continuously retained;
- eventual cleanup after the delayed I/O is released, without manual deletion
  of the ownership record or cgroup;
- failure injection for unavailable/unwritable durable state before launch;
- unrelated-unit and unrelated-cgroup isolation; and
- clean teardown of services, processes, cgroups, devices, artifacts, state,
  evidence and logs.

The proof must distinguish the user manager's ownership of the still-populated
transient invocation service from the supervisor process that restarts. Report
the exact manager, supervisor and invocation-unit states at the prepared,
start-call, manager-bound, supervisor-death/restart, cleanup and terminal
boundaries. Keep `polkit.service` active, restore `ubuntu`'s original linger
setting, keep `/var/tmp` `root:root 1777`, and leave the protected
`p5-r5-rp11-h0*` directories unchanged.

## Verification

On the final synchronized tree run:

- all executor application, adapter, supervision and persistent-owner tests in
  the real user-manager service environment;
- the complete executor interruption, supervisor and hand-off host modules
  through real `sudo -n`;
- focused accepted `stop`, `consume`, `attest`, manager, artifact and
  unit-control regressions;
- the complete `tests/systemd_integration` suite serially;
- the canonical bot and web suites serially with the required PostgreSQL
  environment and web skip count, followed by Foundry;
- compilation, guard tests, configured static checks and `git diff --check`;
  and
- a separate final host-cleanliness inspection including persistent-owner
  services, processes, delegated cgroups, devices, marker state and the
  existing RP-11 artifact/unit/Polkit/evidence checks.

Report reliable pass/fail/error/skip counts. Do not classify a failure as
pre-existing without a meaningful accepted-baseline comparison. Exact commands
are required for the service lifecycle, privilege, failure-injection and
restart proof where ordering and status propagation affect the claim.

## Acceptance criteria

The remediation is reviewable only when all of these are true:

1. no privileged launch occurs unless durable ownership and a live persistent
   supervisor are already established;
2. no normal result or propagated ordinary exception after launch leaves a
   member without either affirmative settlement or proved persistent
   ownership;
3. supervisor and executor crashes/restarts cannot drop the orchestration block
   or cause a second SA-2 invocation;
4. the systemd user manager retains the separate transient invocation unit
   while the supervisor restarts, and the restarted supervisor continues
   recovery and eventually removes only an affirmatively empty boundary;
5. no unrelated process, unit or cgroup can be targeted by damaged, planted,
   stale or reused state;
6. the fixed SA-2 vector, OC gate, journal validation and accepted Route 3
   roles remain unchanged; and
7. the real-host restart/recovery proof and final cleanliness check pass.

If any condition cannot be achieved without broadening privilege, changing the
fixed vector, implementing the full coordinator or weakening the approved
contract, stop and identify the exact remaining authority decision. Do not
replace the blocker with another result token or an acceptance recommendation.

## Handback

Update only the existing
`docs/review/route-3-executor-oc-implementation-handback.md` with one concise
**Third executor review remediation** section containing:

- the ownership mechanism and why ownership exists before launch;
- exact production and test files changed;
- the state/identity/durability and restart invariants;
- material final-tree test and real-host results, failures and skips;
- final host-cleanliness state;
- deployment/recovery effects and remaining production risks; and
- exactly one recommendation: accept for continued non-production development
  only if every criterion above is proved, otherwise keep the slice blocked on
  one precisely named issue.

Do not record Peter's acceptance, assign a successor slice, or authorize a
production installer or activation.
