# Claude implementation prompt — Route 3 non-root executor OC interruption slice

Date: 2026-10-18
Authority: Peter Duscha, baseline v1.9, RT-5 acceptance, and the active
implementation-first delivery plan
Reviewer after handback: Codex
Mode: bounded implementation and full disposable-server testing; no production
or staging activation

## Assignment

Implement the first bounded non-root executor slice for Route 3: the OS-6
interruption path guarded by the fail-closed OC-1/OC-2/OC-3 condition.

The executor runs as the unprivileged `ubuntu` operator on `oracle-test`. Given
one validated activation ID, it must:

1. read `ActiveState` and `InvocationID` for the fixed
   `rp11-capture-pass-a.service` without privilege;
2. securely read and parse that activation's fixed consume journal;
3. make the route available only when all three accepted conditions hold; and
4. only then invoke the accepted static SA-2 `stop` role once through this exact
   privileged boundary:

```text
sudo -n /usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py stop
```

This is a real consumer of the evaluator, not a speculative interface. Keep the
implementation inactive outside tests on `oracle-test`. Do not commit or push.

## Current working-tree boundary

The working tree contains the accepted but uncommitted Route 3 series through
RT-5 `attest`, plus current-state documentation and the governing
implementation-evidence clarification. This complete working tree—not merely
the last Git commit—is the implementation base.

Inspect `git status` and the complete diff before editing. Preserve every
accepted role and unrelated maintainer change. Do not reset, revert, rewrite or
recharacterize the accepted `start`, `stop`, `consume`, `hold`, `stop-post`,
`backstop` or `attest` behavior. A shared-code change requires a demonstrated
need and regression coverage.

## Required reading

Before planning or editing, read completely:

1. `.agents/AGENTS.md`;
2. the implementation-plan reading map, §§0, 12 Phase 5.0, 13, 14, 16 and 20;
3. `docs/review/Handover information`;
4. `docs/project-management/active-delivery-plan.md`;
5. `docs/operations/disposable-test-server.md`;
6. the accepted `start`, `stop`, `consume` and `attest` implementation
   handbacks and their current code/tests;
7. the operation inventory's scope/roster, SA-2 row, §§5.1 RT-1, 6 SA-1/SA-2,
   7, 8.1, the OC reconciliation rows and CX-3;
8. the accepted one-host amendment §4.2.5-R6(b)–(d), especially OC-1–OC-3,
   durable-by-construction and Lemma R6; and
9. the interface contract §§3.0, 3.1 and 3.7.

Historical WP closure labels are not current development gates under baseline
v1.9. Their accepted OC, DI-1 and DI-S requirements remain implementation
inputs.

## Exact boundary and invariants

The route is available only while all of these hold for the same observation:

- **OC-1:** the capture unit's exact `ActiveState` is `active`;
- **OC-2:** its exact, non-empty `InvocationID` equals the consume journal's
  `run-start.invocation_id`; and
- **OC-3:** the valid consume journal contains a durable `consumed` line.

Every other state is unavailable. This includes `activating` and every
start-pre/start sub-state, `reloading`, `deactivating`, `inactive`, `failed`, an
unknown or malformed state, an empty or malformed invocation ID, an absent,
unreadable, oversized, replaced, non-regular, wrongly owned/mode, torn,
malformed, wrongly chained or wrong-run journal, a missing/duplicate/hybrid
`run-start`, no `consumed` line, or an invocation mismatch.

Unavailable means: do not call `sudo`, do not call SA-2 or DI-S, do not mutate a
unit or filesystem object, do not retry, and return a typed safe outcome. Under
CX-3 the pass continues without a grant. Do not turn unavailability into a
cleanup, finalization or attestation action.

The read and stop do not need to be atomic. Preserve Lemma R6: after OC-1–OC-3
were validly observed, a stale stop may land after the pass ended or on a later
attempt, but the durable one-shot claim has already crossed SB-1. Do not add a
second state read and do not reinterpret a later observation as permission to
retry.

## Required implementation behavior

### Application boundary

- Add one cohesive application service/value model for the interruption
  decision and result. It must depend on narrow injected ports for the unit
  observation, consume-journal read and accepted SA-2 invocation.
- Validate the activation ID with the existing accepted validator before any
  I/O. No caller supplies a unit name, path, executable, stop argument, job mode
  or environment-derived selector.
- Request exactly `ActiveState` and `InvocationID` for the fixed capture unit
  through the existing manager boundary. Treat only exact typed boundary data
  as evidence; subclasses, coercions, truthiness hooks and arbitrary objects
  must not manufacture availability.
- Parse journal bytes with the production `JournalKind.CONSUME` grammar and
  `consume_run(activation_id)`. A parser result that is invalid or has a torn
  tail is unavailable. Require exactly the accepted first `run-start`, its
  exact invocation identity, exactly one `consumed` line, no `consume-failed`,
  and exactly one terminal `run-end {outcome: consumed}` after `consumed`.
  Reject duplicated, reordered or hybrid histories that the production consume
  procedure cannot emit. Do not search raw bytes for tokens.
- Return a closed typed result that distinguishes at least `interrupted`,
  `unavailable` and `error/effect-not-confirmed`. Use stable safe reason tokens;
  never expose raw journal content, arbitrary exception text, paths supplied by
  a caller or untrusted boundary values.

### Non-root adapters

- Reuse `SystemdManagerAdapter.read_unit` over the system bus for the
  unprivileged fixed-unit read. Do not shell out to `systemctl` merely to parse
  presentation text, and do not call `stop_capture_unit()` directly from the
  non-root process.
- Add a narrow consume-journal reader for the fixed activation-derived path.
  It must be descriptor-safe and bounded: no symlink following, no path supplied
  by the caller, exact regular-file/ownership/mode checks for the accepted
  root-owned `0644` journal and its accepted directory, a size cap at least as
  strict as the existing maximum terminal-journal volume, and an `fstat`-based
  check on the opened object. Absence, replacement, short read, growth, I/O
  error or metadata disagreement is unavailable/error, never evidence.
- Invoke SA-2 without a shell, using a fixed argv containing the exact `sudo -n`
  vector above. The caller cannot add arguments or choose an executable. Invoke
  it at most once.
- Preserve SA-2's certainty. Exit 0 is `interrupted`; a typed refusal is not
  success; pre-send failure is an error; effect-not-confirmed, interruption,
  timeout, signal death, malformed output/status or an unexpected exit is
  fail-closed and never retried. Do not infer success from the unit later being
  inactive.
- Bound the child wait and settle it safely on cancellation/interruption. Do not
  leave a `sudo`/SA-2 child running merely because the executor stopped waiting.
  The chosen timeout and termination/reaping behavior are reversible
  implementation details and must be explicit in code and tests.

### Entry point and reporting

- Provide one narrow repository-owned non-root entry point for this slice. Its
  only caller-controlled operand is the activation ID. The exact module/CLI
  placement is a reversible implementation choice; pin the accepted argv and
  exit mapping in tests.
- Emit at most one bounded diagnostic line with stable tokens. No journal data,
  invocation ID, arbitrary exception, credential, environment value or internal
  path may be printed.
- Write no new operational record in this slice. Report the typed result to the
  caller; later executor orchestration/reporting remains separate.

## Required regressions

Add table-driven application tests using production journal serialization and
parsing. At minimum cover:

1. exact OC-1/OC-2/OC-3 success invokes SA-2 once and returns interrupted;
2. every admitted systemd state other than exact `active`, plus unknown,
   malformed, wrong-type and hostile equality/truthiness values;
3. empty, malformed and different unit invocation IDs;
4. absent, unreadable, oversized, symlinked, replaced, wrong-owner/mode and
   non-regular journal objects;
5. torn, malformed, wrongly chained, wrong-run, missing/duplicate/hybrid
   `run-start`, missing `consumed`, `consume-failed` and non-consumed terminal
   journals;
6. positive journal with a different invocation ID;
7. unit read refusal/error/malformed success and every journal-reader failure,
   each proving SA-2 was never invoked;
8. SA-2 success, typed refusal, pre-send error, effect-not-confirmed, timeout,
   interruption, signal death, malformed status/output and unexpected
   exception, each with exactly one or zero calls as appropriate and no retry;
9. a stale-read control consistent with Lemma R6, proving no second read or
   retry is introduced;
10. invalid activation IDs refused before unit, journal or subprocess I/O; and
11. unchanged focused tests for the accepted `stop`, `consume`, manager adapter
    and artifact boundaries.

Tests must assert absence of mutation/calls on every unavailable path, not only
the returned token.

## Disposable-host proof

Use synthetic data and the documented secret-excluding synchronization
procedure. On `oracle-test`, run the new entry as the real unprivileged
`ubuntu` user while the accepted controlled artifact is installed from the
pinned Jeepney wheel.

Prove at least:

- a real active capture unit whose invocation ID matches a canonical consumed
  journal is stopped through the exact `sudo -n` SA-2 vector;
- a real `activating`/start-pre unit is not stopped and no privileged child is
  launched;
- active with a mismatched invocation ID is not stopped;
- active with missing, torn and consumed-less journals is not stopped;
- an unavailable check leaves the unit and journal unchanged;
- an unrelated systemd job/unit is untouched; and
- a simulated unconfirmed SA-2 result is not retried or promoted to success.

The host test may create only transient test units and synthetic evidence under
the established Route 3 test paths. Teardown must leave no executor/SA-2
process, RP-11 unit, Polkit rule, artifact, staging/store path, attempt evidence,
test journal or test log; keep `polkit.service` active, `/var/tmp` `root:root
1777`, and the six protected `/var/tmp/p5-r5-rp11-h0*` directories unchanged.

## Verification and evidence

Follow the implementation-evidence standard in `.agents/AGENTS.md`. Evidence
must establish the material claims; do not produce a terminal transcript.

On the final synchronized tree run:

- the complete new executor unit/application tests;
- focused `stop`, `consume`, manager/unit-control, artifact and RT-5 regression
  tests affected by this slice;
- the new real-host executor module as `ubuntu` with the privileged boundary
  exercised through `sudo -n`;
- the complete `tests/systemd_integration` suite serially;
- the documented bot and web suites serially with the database environment and
  expected web skip count, followed by the Foundry suite;
- compilation/configured static checks, guard tests and `git diff --check`; and
- a final host-cleanliness inspection.

Report actual statuses, failures, errors and skips. A standard suite may cite
its canonical command. Record an exact invocation when privilege, environment,
ordering or status propagation materially affects the result. Do not call a
failure pre-existing without a meaningful accepted-baseline comparison.

## Explicit exclusions

Do not implement or activate:

- the full Package 5.0 coordinator or pass scheduler;
- start orchestration, AP-0/AP-1/AP-2 waiting, activation selection or candidate
  discovery;
- automatic attestation, reboot handling or deactivation-record reporting;
- X-3 finalization, capture-root mutation, grants or reward/data behavior;
- a production capture-unit, executor or artifact installer;
- production/staging services, configuration, sudoers, Polkit policy or data;
- migration/cutover work, RB-1 or any destructive action outside `oracle-test`;
  or
- changes to accepted roles absent a demonstrated regression.

Use no real secret or player data. Do not add another proof/remediation chain;
return one concise implementation handback.

## Acceptance criteria

- SA-2 is invoked once only after exact OC-1/OC-2/OC-3 evidence for the same
  activation; every uncertainty makes the route unavailable.
- No unavailable/error path invokes privilege or mutates the unit or evidence.
- Journal evidence is production-parsed, descriptor-safe, bounded and tied to
  the validated activation and observed invocation.
- The fixed capture unit and fixed SA-2 argv cannot be caller-controlled.
- A stale read cannot cause a retry or bypass the one-shot-claim reasoning of
  Lemma R6.
- SA-2 uncertainty remains uncertainty; later state never promotes it to
  success.
- Real unprivileged-to-`sudo -n` host behavior and clean teardown are proved on
  `oracle-test`.
- Accepted Route 3 roles and established repository baselines have no
  demonstrated regression.
- Production/staging remain untouched.

## Handback

Return one concise handback containing:

- behavior and invariants delivered;
- principal files changed;
- row/invariant-to-test coverage for OC-1–OC-3, CX-3 and Lemma R6;
- material final-tree test and host results, including failures and skips;
- host-cleanliness result;
- deployment/migration/recovery effects and remaining production risks; and
- one recommendation: accept this executor slice for continued non-production
  development, or remediate a named blocker.

Do not record Peter's acceptance, assign a successor slice or authorize a
production installer or activation. Stop after the handback for independent
Codex review.
