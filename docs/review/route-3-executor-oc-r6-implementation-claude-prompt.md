# Claude implementation prompt — accepted Route 3 executor OC correction R6

Date: 2026-10-21
Status: **ACCEPTED AND AUTHORIZED IMPLEMENTATION PROMPT**
Authority: Peter Duscha, Product Owner and Acceptance Authority
Implementer: Claude
Reviewer after handback: Codex
Mode: one bounded implementation, documentation and full disposable-host test
cycle; no production/staging installation or activation

## Accepted decision and assignment

Peter accepts the recommended R6 implementation direction and authorizes Claude
to implement it. Preserve the selected Route 3 topology and correct the inactive
executor supervisor candidate in place.

The shared working tree already contains an R6 candidate produced during Codex's
review. Treat it as implementation input, not as accepted code and not as proof
that this assignment is complete. Inspect every changed path, retain correct
work, repair or complete anything that does not satisfy this prompt, add any
missing regression, run the required evidence on `oracle-test`, and update the
existing executor handback in place.

Acceptance of this prompt accepts the architecture and security contract below.
It does **not** accept the resulting implementation, close the executor OC gate,
authorize production/staging installation or activation, or assign a successor
slice. The completed candidate returns to Codex for independent review and then
to Peter for an acceptance decision.

Do not create another implementation handback. Do not commit or push.

## Governing material

Before changing or testing anything, read completely and follow:

1. `.agents/AGENTS.md`;
2. the reading map in `docs/implementation-plan.md`, then §§0, 12 Phase 5.0,
   13, 14, 16 and 20, plus any directly implicated section;
3. `docs/review/Handover information`;
4. `docs/project-management/active-delivery-plan.md`;
5. `docs/operations/disposable-test-server.md`;
6. `docs/operations/executor-supervisor-provisioning-runbook.md`;
7. `docs/review/route-3-executor-oc-implementation-handback.md`, including its
   authoritative sixth-correction section and all earlier historical sections;
8. the original executor implementation/completion prompts and R1 through R5
   remediation prompts, applying the supersession notices on R3 through R5;
9. every current file under `application/executor/`, `adapters/executor/` and
   `infra/executor/`, `tools/executor_supervisor_install.py`, all executor unit
   and systemd-integration tests, the current diff and production scope guards;
   and
10. the accepted SA-2 `stop` implementation and controlled root artifact.

Current-state authority overrides dated historical assignments. Historical
records remain evidence and must not be rewritten. Preserve unrelated
maintainer changes and work safely in the existing dirty tree.

## Authority and safety boundary

This prompt authorizes all implementation, test and documentation changes
strictly required for R6, plus all levels of isolated testing on `oracle-test`:
root, systemd, temporary accounts and groups, linger, synthetic sudoers fixtures,
failure injection, restart/recovery, reboot if materially required, bounded
stress tests and cleanup.

Use only synthetic data and the canonical secret-excluding synchronization.
Restore the disposable host to its starting state and report cleanliness.

This prompt does not authorize:

- production or staging mutation;
- real secrets or player data;
- a broader sudo command or weaker authorization;
- the full coordinator, scheduler, start orchestration, automatic attestation,
  migration/cutover, RB-1, grants, rewards or game-data changes;
- reopening accepted Route 3 roles absent a demonstrated regression;
- acceptance of R6, production activation, successor work, commit or push.

If completing R6 would require an irreversible architecture, product-scope,
privacy, data-authority or production-safety decision outside the accepted
contract, stop and name the exact decision instead of guessing.

## Fixed architecture and privileged boundary

Preserve:

- one root-controlled system service for the persistent supervisor, running as
  `User=freedom-executor` and `Group=freedom-executor`;
- one separate transient service per admitted invocation in that account's
  lingering systemd user manager;
- durable exclusive ownership before the sole `StartTransientUnit` request;
- recovery that adopts and settles but never launches or retries SA-2;
- the fixed OC-1/OC-2/OC-3 gate, consume-journal validation, CX-3, Lemma R6,
  stable diagnostics and unrelated-unit isolation; and
- the exact privileged vector:

```text
sudo -n /usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py stop
```

### Accepted R6 environment decision

Do not claim that the transient process has an atomically guaranteed exact
environment. `manager_environment()` and `StartTransientUnit` are separate
D-Bus calls, a same-uid actor can mutate the user-manager environment between
them, and systemd's generated variable set is not a closed future-proof list.

Retain environment minimization as defense in depth:

- configure `PATH=/usr/bin:/bin`;
- snapshot and unset manager variables;
- unset known systemd-generated variables; and
- keep the executable and argv fixed, with no shell, `env` wrapper or
  caller-controlled operand.

The accepted privileged security property is instead that account- or
manager-controlled environment cannot redirect or change the root SA-2 `stop`
operation. Enforce and prove that through the exact sudoers command, trusted
sudo policy behavior, Python `-I -S`, root-owned/non-writable interpreter and
artifact paths, argv-only role selection, no environment read by valid `stop`
before the environment is cleared, and rejection of every alternate vector.

If installed sudo behavior or configuration does not support that property,
stop with the concrete gap. Do not silently reinstate exact PATH-only equality
as the security argument and do not widen the accepted vector without a new
decision.

## Required implementation

### 1. Own every ambiguous request write

In `SudoStopInvoker.invoke_stop()`, distinguish failures before the request
write is attempted from failures once `sendall(PROTOCOL_REQUEST)` begins.

- A definite pre-write failure may return `NOT_SENT`.
- Any exception from the request write must return `HANDED_OFF`, because some
  or all bytes may have crossed and the complete line may already be admitted.
- Every later timeout, disconnect, malformed response, close failure or
  interruption remains owned/uncertain, never retry permission or success.

Trace the application caller and preserve the one-shot guarantee: no returned
state may permit a second SA-2 launch after the first request may have crossed.

### 2. Publish readiness after serving starts

The persistent supervisor must complete manager readiness and the first
recovery pass, bind/listen on its socket, create and start the serving worker,
and only then publish `READY=1`.

Confirm that a client arriving immediately at readiness is safely queued or
served, and that no startup failure can leave systemd believing a viable owner
exists when it does not. Preserve fail-closed restart behavior while the user
manager or bus is unavailable.

### 3. Verify the effective system unit, not only its fragment

The installer must refuse any same-named fragment or name-specific drop-in in
every supported system-manager load location on the target systemd 259 host,
including `.control`, transient, attached, generator, `/etc`, `/run`,
`/usr/local` and `/usr` locations.

After every install, upgrade, restore or unlink, use the owning system manager's
reported effective state. A present reviewed unit requires at least:

- `LoadState=loaded`;
- `FragmentPath=/etc/systemd/system/freedom-blades-executor-supervisor.service`;
- empty `DropInPaths`;
- `NeedDaemonReload=no`;
- `User=freedom-executor`;
- `Group=freedom-executor`; and
- configured `Environment=PATH=/usr/bin:/bin`.

Absence after removal must be affirmatively reported by the manager. Preserve
recoverable upgrade/removal behavior and stable `reload-failed`/
`manager-stale` diagnostics. A changed effective identity, configured
environment or loaded drop-in must never pass merely because the fragment path
matches.

### 4. Reconcile all current documentation

Keep current documentation aligned with the accepted decision and implemented
behavior:

- active handover, project status and active-delivery state;
- implementation plan §20;
- decision register and append-only change log;
- provisioning runbook and review index;
- cumulative executor handback; and
- explicit supersession notices on historical R3/R4/R5 prompts.

Preserve the distinction between accepted implementation direction, completed
candidate, independent review and Peter's later acceptance. Do not rewrite
historical requirements as though they were never issued. Do not claim
production/staging installation authority.

The runbook must state the effective-unit checks, readiness order, environment
minimization, actual privileged invariant and any trusted production sudo-policy
prerequisite the implementation cannot mechanically verify.

## Required deterministic regressions

Add or retain regressions that fail on the pre-R6 candidate and prove:

1. an error raised by `sendall(PROTOCOL_REQUEST)` is `HANDED_OFF`, including a
   fake connection representing a complete line followed by `BrokenPipeError`;
2. failures before the write is attempted remain `NOT_SENT`;
3. the serving thread is started before `READY=1` and an immediate client is
   not lost;
4. a drop-in under `.control` or another supported system-unit path is refused;
5. non-empty effective `DropInPaths`, wrong effective `User`, wrong `Group` and
   changed configured environment each produce `manager-stale` or make reload
   fail as appropriate;
6. the drain/admission race is synchronized at the durable-record and actual
   launch boundary and proves that no launch follows an empty acknowledgment;
7. hostile manager/account environment still cannot redirect the supervisor or
   privileged `stop` operation;
8. valid `stop` reads no environment variable, alternate argv is refused and
   the environment is cleared; and
9. all preceding ownership, restart, recovery, cgroup identity, drain/removal,
   code-trust, bounded-enumeration, OC gate and stable-result regressions remain
   unchanged.

Tests must prove event ordering with deterministic barriers. Do not replace a
race with sleeps or weaken an assertion to obtain a pass.

## Required disposable-host evidence

Synchronize the exact final workspace using the canonical secret exclusions.
On `oracle-test`, at minimum run:

1. the complete executor ownership/usermanager/supervisor/interrupt/installer/
   system-service focused set;
2. SA-2 `stop` plus artifact regressions proving hostile-environment invariance
   and that valid `stop` never calls the environment reader;
3. the root/systemd executor package module using the documented wheel and
   integration marker;
4. the documentation vocabulary test;
5. compilation and whitespace checks; and
6. any targeted adversarial probe needed to establish sudo/environment or
   systemd load-path behavior not already covered.

Run broader bot, web, Foundry or complete systemd-integration suites when a
changed dependency or observed failure makes them material. Do not rerun large
unrelated suites merely to inflate a count; compare any claimed regression to
the applicable accepted baseline.

The existing R6 candidate reports 476 focused executor passes, 73 SA-2 boundary
passes, 12 root/systemd package passes and 346 documentation checks. Those are
claims to reproduce or correct, not authority to skip testing.

The package module creates a 250,000-entry stress tree. Inspect the small `/tmp`
tmpfs before testing. `-o tmp_path_retention_policy=none` is permitted for the
focused suite. Remove only positively identified disposable pytest directories,
report that cleanup, and never delete a broad or unresolved path.

For every privilege-, environment-, ordering-, reboot- or status-sensitive
claim, record the exact invocation and reliable exit status. Report every
failure, skip, warning, retry, altered command and infrastructure incident. A
successful rerun does not erase a failed first run.

Before handback, independently confirm there is no test account/group/home,
linger file, sudoers fixture, unit fragment/link/drop-in, service, transient
unit, process, cgroup, mount, state/runtime directory, decoy or pytest residue
left by this assignment.

## Stop conditions

Stop and return a precise blocker rather than improvising if:

- preserving the fixed vector cannot establish environment-independent root
  execution on the supported sudo implementation;
- the manager cannot prove the complete effective-unit property under systemd
  259;
- a request-write or readiness outcome cannot be classified without permitting
  duplicate privilege or loss of the persistent owner;
- a required fix broadens product scope, authorization or production authority;
- real credentials/player data would be required; or
- disposable-host cleanup cannot be completed safely.

Ordinary test failures, implementation defects and difficult debugging are not
stop conditions; repair them within this accepted scope and rerun proportionate
evidence.

## Required handback

Update only the existing
`docs/review/route-3-executor-oc-implementation-handback.md`. Append one concise
Claude implementation section after the current R6 material; do not create a
new handback or review chain.

The handback must state:

1. the accepted R6 contract and exact files changed;
2. whether the existing candidate was retained, corrected or completed, with
   material differences called out;
3. the source-level reasoning for request-write ownership, readiness,
   effective-unit verification and environment-independent privilege;
4. deterministic regressions added or retained;
5. exact material host invocations and reliable results, including every
   failure/skip/deviation and any baseline comparison;
6. final host-cleanliness evidence;
7. remaining production prerequisites and residual risks, especially trusted
   sudo policy/configuration;
8. an explicit statement that production/staging were untouched, nothing was
   committed or pushed, and no acceptance or successor authority is claimed;
   and
9. exactly one recommendation: `Accept for continued non-production
   development` or `Changes required before acceptance`.

Stop after the handback. The implementation then awaits independent Codex
review and Peter's acceptance decision.
