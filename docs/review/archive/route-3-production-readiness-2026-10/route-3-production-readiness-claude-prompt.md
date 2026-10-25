# Claude prompt — Route 3 production-readiness and security-gate preparation

Date: 2026-10-22

Status: **ACCEPTED AND AUTHORIZED ASSIGNMENT**

Authority: Peter Duscha, Product Owner and Acceptance Authority

Implementer: Claude

Independent reviewer after handback: Codex

Mode: one bounded production-readiness review, disposable-host rehearsal and
proportionate correction cycle; no production or staging access or activation

## Assignment

Peter accepted the cumulative executor OC R6 candidate for continued
non-production development and now assigns the next step toward production:
prepare the complete inactive Route 3 privileged chain for its final independent
production security and operations review.

Inspect the accepted implementation end to end, exercise its real deployment
lifecycle from a clean state on `oracle-test`, correct reversible repository or
test defects found within the accepted design, and return one concise readiness
handback. The work must establish what is ready, what remains production-specific,
and the exact decision Peter must make about the transient inspection-failure
risk. It must not install, inspect or activate anything in production or staging.

This assignment prepares a later go/no-go decision. It is not that decision and
does not authorize production activation, a staging deployment, the full
coordinator, start orchestration, automatic attestation, migration/cutover,
RB-1, commit or push.

## Governing material

Before acting, read completely and follow:

1. `.agents/AGENTS.md`;
2. the reading map and §§0, 9, 12 Phase 5.0, 13, 14, 16, 17 and 20 of
   `docs/implementation-plan.md`;
3. `docs/review/Handover information`;
4. `docs/project-management/active-delivery-plan.md`;
5. `docs/operations/disposable-test-server.md`;
6. `docs/operations/executor-supervisor-provisioning-runbook.md`;
7. the accepted implementation handbacks for the manager/Polkit adapter,
   `tmpfiles.d`, `stop-post`, `backstop`, `hold`, SA-1 `start`, SA-2 `stop`,
   RT-1 `consume`, RT-5 `attest` and executor OC;
8. all current production code, installers, service fragments and focused tests
   belonging to that chain; and
9. the exact current diff and production-source scope guards.

Current-state authority overrides dated prompts. Historical records remain
evidence and must not be rewritten. Preserve every unrelated shared-tree change.

## Authority and safety boundary

All levels of testing are authorized on the disposable `oracle-test` host,
including root/systemd work, temporary accounts/groups, exact-path installation,
linger, synthetic sudoers policy, Polkit, reboot, failure injection, service
restart, rollback/removal, destructive cleanup and host reset.

Use only synthetic data and the canonical secret-excluding synchronization.
The disposable host may be rearranged as necessary, but establish a reversible
choreography before replacing its ordinary `/opt/freedom-blades/platform`
test checkout and restore the documented test environment afterwards.

This assignment does **not** authorize:

- any production or staging login, inspection, file read, mutation,
  installation or activation;
- real credentials, secrets or player data;
- widening sudoers, Polkit or any accepted authorization boundary;
- changing the fixed privileged vector, selected supervisor topology,
  OC-1/OC-2/OC-3, ownership state machine or accepted role semantics;
- deciding to accept the transient inspection-failure exposure on Peter's
  behalf;
- full coordinator, scheduler, start orchestration, automatic attestation,
  migration/cutover, RB-1, game-data behavior, commit or push.

If a production-specific fact is required, record the minimal read-only check
for a later separately authorized inspection. Do not perform it now.

## Accepted boundary to preserve

Preserve the accepted chain and, in particular:

- the root-controlled system supervisor running as `freedom-executor`;
- the dedicated account's lingering user manager owning one transient unit per
  admitted invocation;
- durable exclusive ownership before the sole `StartTransientUnit` call;
- recovery that adopts and settles but never launches or retries SA-2;
- the exact privileged vector:

  ```text
  sudo -n /usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py stop
  ```

- environment minimization as defense in depth, with privilege instead resting
  on exact sudo policy, Python `-I -S`, trusted root-owned paths and the
  environment-free `stop` artifact;
- append-only/fail-closed evidence, typed uncertainty, no false success and no
  retry after ambiguous handoff; and
- the accepted manager/Polkit, cleanup, backstop, hold, consume and attest
  invariants.

Do not reopen an accepted behavior merely because another design is possible.
A demonstrated security or lifecycle defect may be corrected within this
boundary. A correction that changes authorization, residual-risk ownership,
production topology or role semantics is a stop and decision item.

## Required work

### 1. Review the complete privileged chain

Trace the deployable path from the unprivileged executor through the supervisor,
the dedicated user manager, exact sudo transition, root-owned SA-2 artifact,
manager/Polkit adapter and cleanup/recovery roles. Confirm at least:

- every executable, argv, identity, filesystem owner/mode and manager boundary;
- absence of caller-controlled paths, operands, environment authority or shell
  interpretation at the root transition;
- one-shot and ambiguous-handoff behavior;
- durable owner survival across client/supervisor interruption and reboot;
- effective system-unit/drop-in and root-owned code/dependency verification;
- fail-closed behavior for unavailable, malformed, stale or contradictory
  evidence; and
- safe diagnostics, journals and logs without secrets or unrelated data.

Correct focused implementation, test or runbook defects if the accepted design
already determines the answer. Do not create a new proof-document chain.

### 2. Perform an exact-path production-like rehearsal on `oracle-test`

Exercise the accepted operator procedures against the real fixed paths and
service identities, not merely mocks or a bind-mounted substitute. The
rehearsal must use:

- a root-owned, non-writable deployment at `/opt/freedom-blades/platform`
  containing no `.git`, `.env`, key or credential file;
- a root-owned `/opt/freedom-blades/runtime/venv-web` with the supported
  interpreter and pinned offline dependencies;
- the real `freedom-executor` account/group, non-login shell, owned home and
  linger state;
- the exact one-command sudoers drop-in and effective sudo defaults required by
  the runbook;
- the accepted root-owned RP11 artifact, Polkit/`tmpfiles.d` prerequisite,
  system-service fragment, installer and dedicated user manager; and
- the real systemd 259/cgroup-v2 behavior on the disposable host.

If the exact fixed-path rehearsal cannot safely coexist with the normal test
checkout, stage a secret-free source copy elsewhere, record and verify the
starting state, perform a bounded move/reprovision/reboot/restore sequence, and
restore the canonical checkout and runtime afterwards. Do not claim an
exact-path rehearsal if a bind mount or substituted path still carries a
material production premise.

Exercise, with reliable status propagation:

1. prerequisite refusal before provisioning;
2. account, linger, exact sudoers and root-owned runtime provisioning;
3. install without implicit start, explicit first start and `verify-ready`;
4. boot without login and readiness only after the user manager and recovery;
5. one authorized end-to-end synthetic OC interruption and proof of exactly one
   SA-2 launch;
6. client interruption, supervisor restart with retained ownership, an
   ambiguous same-boot record, continued admission block and changed-boot
   recovery;
7. hostile environment, alternate argv, extra sudo grant, effective drop-in,
   writable code/dependency and wrong-service-identity refusals;
8. upgrade success and injected reload/restore failure;
9. drain under load, removal refusal while owned, eventual settlement, clean
   remove and rollback/reinstall; and
10. complete teardown and restoration of the documented disposable host.

Use accepted installers and procedures. Never weaken a prerequisite or broaden
sudo/Polkit policy to make the rehearsal pass.

### 3. Prepare the transient inspection-failure decision

The open risk is precise: a transient GRR inspection failure is typed as damaged
or foreign; cleanup retains the grant and records `present-*-unremoved`, while
the accepted BS-3 rule may disarm the backstop. The grant can therefore remain
live until CP, boot or `attest`. This is fail-closed for deletion but leaves a
bounded authorization-exposure residual.

Reproduce the relevant deterministic and real-host behavior and return a short
decision analysis containing:

- the exact trigger, observable record and maximum lifecycle of the live grant;
- what CP, reboot and `attest` each guarantee, and what happens if one is
  unavailable;
- whether monitoring/operator response can reliably detect and bound exposure;
- the security and availability consequences of at least: accepting the
  residual, keeping the backstop armed on this outcome, or adding a bounded
  retry/new typed state; and
- one evidence-backed recommendation to Peter.

Do not implement a changed BS-3 rule, retry class or authorization policy in
this slice. Peter decides after independent review.

### 4. Produce the production-specific fact checklist

List only facts that cannot be established on `oracle-test`, with one minimal
read-only command or inspection method for each. At minimum consider:

- OS, kernel, systemd/cgroup and Python versions;
- UID/GID and user-manager/linger policy;
- effective sudoers defaults and every grant reaching `freedom-executor`;
- existing system/user unit fragments, drop-ins, generator output and Polkit
  policy that could affect the service;
- ownership/mode/link state of deployment, interpreter, dependencies and
  artifact paths;
- capacity, logging/monitoring, maintenance window and rollback ownership; and
- whether any production topology fact conflicts with the accepted runbook.

This checklist is preparation for a later explicitly authorized **read-only**
production inspection. Do not include secret values and do not access the host.

### 5. Return a deploy/rollback recommendation

Provide an ordered, reversible activation outline tied to the accepted runbook:
preflight, backup/state capture, install, start or reboot, health/ownership
checks, one bounded smoke test, monitoring, rollback triggers, remove/revoke
order and evidence retention. Clearly separate:

- proved on `oracle-test`;
- requires later read-only production confirmation;
- requires Peter's risk decision;
- requires independent security/operations acceptance; and
- requires a separate production activation instruction.

Do not turn the outline into an executable production command until the
production facts and risk decision are accepted.

## Required verification

On the exact final tree and serially where shared state exists:

1. run the focused manager/Polkit, cleanup, role, artifact, consume, attest,
   executor ownership/usermanager/supervisor/interrupt/installer/system-service
   suites;
2. run the complete root `tests/systemd_integration` suite with the documented
   marker and pinned wheel;
3. perform the exact-path clean install/reboot/failure/rollback/removal rehearsal
   above;
4. after any executable change, run the canonical bot and database-enabled web
   suites serially and the Foundry Node suite; if no executable or executable
   instruction changes, explain why the accepted final-tree figures remain
   applicable;
5. run configured compilation/format/lint/type checks or state accurately what
   is not configured; run `git diff --check`; and
6. inspect the final host for accounts, groups, homes, linger files, sudoers,
   Polkit/tmpfiles fragments, units, processes, cgroups, mounts, runtime/state,
   root artifacts, decoys, deployment copies and pytest residue created by the
   assignment.

Report every failure, error, skip, retry, reboot phase, altered command and
infrastructure incident. A rerun does not erase an earlier failure. Do not call
a failure pre-existing without a meaningful baseline comparison.

## Stop conditions

Stop and return the concrete blocker if:

- exact-path rehearsal would require risking non-disposable or unresolved data;
- the fixed sudo vector cannot be isolated under the effective sudo policy;
- root-owned source/interpreter/dependency trust cannot be established;
- a live invocation can lose its owner, be launched twice or be reported as a
  confirmed success after uncertainty;
- closing a finding requires changing authorization, the BS-3 disposition,
  production topology or another material accepted boundary;
- production/staging access, a real secret or player data would be required; or
- the disposable host cannot be restored safely.

Ordinary defects and test failures within the accepted design are not stop
conditions; correct them and rerun proportionate evidence.

## Handback

Create one concise handback:

`docs/review/route-3-production-readiness-handback.md`

It must contain:

1. scope and exact files changed;
2. security-review findings and dispositions;
3. exact-path rehearsal topology, phases and reliable results;
4. focused/root/full-suite results with all failures and skips;
5. transient inspection-failure decision analysis and one recommendation;
6. production-specific read-only fact checklist;
7. deploy/rollback outline and explicit rollback triggers;
8. final disposable-host restoration evidence;
9. remaining risks and gates; and
10. exactly one conclusion: `Ready for independent production-readiness review`
    or `Changes required before production-readiness review`.

Update current-state documentation only as needed to record the return. Do not
record Peter's risk decision, production readiness, activation approval or
acceptance unless Peter has explicitly issued it. Stop after the handback for
independent Codex review.
