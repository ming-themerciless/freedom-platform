# Claude implementation prompt — Route 3 manager/Polkit adapter

Date: 2026-10-12
Authority: baseline v1.9 and the active handover
Mode: implement, test, remediate once, and hand back

## Assignment

Implement and validate the narrow Route 3 systemd-manager/Polkit adapter for
the seven interface intents DI-1 through DI-6 and DI-S. Work through the code,
tests and disposable-host integration runs; do not return only a plan, research
record or readiness assessment.

Continue autonomously through reversible implementation choices. Ask Peter
only if work would change product scope, production data authority,
authorization/privacy policy, destructive production behavior, irreversible
architecture or production activation.

## Read before editing

1. `.agents/AGENTS.md` in full.
2. `docs/implementation-plan.md`: reading map, §§0, 12 Phase 5.0, 13, 14, 16
   and 20.
3. `docs/review/Handover information`.
4. `docs/project-management/active-delivery-plan.md`.
5. `docs/operations/disposable-test-server.md`.
6. Sections 2 and 3.0–3.7 of
   `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-interface-contract.md`
   for the detailed request shapes and failure semantics.

The interface contract is technical background. Its former research gates,
Q3/Q6 closure labels and `HARD STOP` language are historical. Where it differs
from the active delivery plan, the active plan controls.

Inspect the relevant implementation and tests end to end before choosing
module locations. The working tree already contains documentation and WP3
changes: preserve them, avoid unrelated formatting or cleanup, and do not
discard or overwrite another contributor's work. Do not commit or push.

## Required behavior

Create a focused, typed adapter behind an application-owned boundary. It must
remain inactive in production configuration. Implement:

- **DI-1:** read the required properties of one named systemd unit.
- **DI-2:** create the transient holder service.
- **DI-3:** create the backstop timer and auxiliary service.
- **DI-4:** stop/disarm the backstop timer.
- **DI-5:** make the non-interactive Polkit authorization decision.
- **DI-6:** construct the `unix-process` subject from PID, `/proc` start ticks
  and real UID.
- **DI-S:** stop exactly `rp11-capture-pass-a.service`.

Apply these implementation rules:

- Use the system message bus. Do not use systemd's private manager socket.
- Use a maintained D-Bus client compatible with the deployed Python. Add and
  lock a dependency if necessary; do not implement the D-Bus wire protocol.
- Keep allowed unit names and verbs narrow. Validate activation-derived unit
  names and never expose an arbitrary unit-management API.
- Install the signal match and subscribe before a mutating manager call. Match
  `JobRemoved` by returned job path and expected unit.
- Select explicit systemd job modes in code. Choose reversible mode details
  from observed disposable-host behavior and pin them in tests.
- Use configurable, bounded deadlines. A timeout, disconnect, lost reply,
  malformed reply or uncertain completion is an error. For a mutating call it
  must report `effect not confirmed` and must never trigger a silent retry.
- Return typed `ok`, `refused` and `error` results. Preserve the narrow refusal
  mappings from the contract; unknown failures remain errors.
- Report a successfully completed stop as `ok(stopped)`. Do not claim
  `already-stopped`: the observed completion does not establish causation.
  `NoSuchUnit` remains `refused(not-loaded)`.
- For DI-5 send action `org.freedesktop.systemd1.manage-units`, details exactly
  `unit` and `verb`, flags `0`, and an empty cancellation ID. Map a challenge
  to `not-authorized`; malformed or error replies remain errors.
- For DI-6 use `("unix-process", {pid, start-time, uid})`, with the exact D-Bus
  integer types required by the contract. Treat unreadable, replaced or
  malformed `/proc` state as an error. Retain a clear production-risk note that
  PID/start-time identity is not race-free; do not expand this slice to pidfd.
- DI-3 must not set `TimeoutStartUSec` on the backstop service.
- A post-completion state read is diagnostic observation only. It must not turn
  a lost or uncertain completion into success.
- Keep transport details out of domain code and make the transport injectable
  so focused tests do not need a live bus.

Prefer the smallest coherent implementation. Do not implement the historical
41 call sites or activate the adapter in an existing production path unless a
real current consumer already provides the boundary. Do not build a generic
systemd control framework.

## Testing and remediation

All testing levels are authorized on `oracle-test`, including SSH, dependency
installation, root, systemd, Polkit, network, PostgreSQL, destructive recovery,
failure injection, restart and end-to-end tests. Use synthetic data only and
do not touch production or staging.

1. Record `git status`, then sync the current workspace with the exact
   secret-excluding `rsync` command in the disposable-server guide.
2. Establish the pre-change baseline on `oracle-test`, serially:

   ```bash
   cd /opt/freedom-blades/platform
   export PATH='/usr/lib/postgresql/16/bin:/usr/bin:/bin'
   export TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'
   /opt/freedom-blades/runtime/venv-web/bin/python -m pytest -q -rs tests/test_*.py
   /opt/freedom-blades/runtime/venv-web/bin/python -m pytest -q -rs tests/web
   node --test "foundry-module/tests/"*.test.mjs
   ```

   Record actual pass/fail/skip counts. Database-marked tests must not silently
   skip because `TEST_DATABASE_URL` was omitted; investigate any departure from
   the documented 80-skip baseline.
3. Add focused unit/contract tests using a fake transport for all seven intents,
   exact request shapes, type encodings, result mappings and deadline behavior.
4. Add disposable-host integration tests against the real system bus, systemd
   and Polkit. Use uniquely prefixed temporary units and temporary test-only
   policy/configuration. Exercise at least:

   - success and authorization denial;
   - invalid unit/request and malformed reply handling;
   - active, inactive and not-loaded stop behavior;
   - non-`done` job completion;
   - timeout, connection loss and lost/late completion;
   - duplicate calls and proof that uncertain mutations are not retried;
   - manager/service restart behavior; and
   - cleanup and recovery after partial failure.

5. Clean up every temporary unit, policy rule and test artifact on
   `oracle-test`. Add automated cleanup where practical and verify it.
6. Fix concrete blocking defects found by these tests in one remediation cycle.
7. Re-sync the final tree and rerun the focused tests plus all three baseline
   suites serially. Run the configured formatter, linter, type checker and
   `.claude/hooks/test_guards.py` where applicable.

If a host capability or dependency is missing, install or configure it on the
disposable server and continue. Stop only for a genuine safety boundary, an
external service unavailable after reasonable recovery attempts, or a material
decision reserved to Peter.

## Acceptance criteria

- Each of DI-1 through DI-6 and DI-S has executable success and failure tests.
- Requests and replies use the required D-Bus types and exact narrow targets.
- Authorization denial never becomes success.
- Uncertain mutations fail closed, say `effect not confirmed`, and are not
  silently retried.
- Timeout, disconnect, duplicate, restart and cleanup/recovery behavior is
  exercised on `oracle-test`.
- The adapter is not activated in production configuration.
- Bot, web and Foundry suites pass on the final tree, with exact skips stated.
- No production/staging system, secret or real player data is touched.

## Handback

Write one concise handback at
`docs/review/route-3-manager-polkit-implementation-handback.md` containing only:

- behavior delivered and the principal files changed;
- exact test commands and results, including skips;
- dependency, deployment, migration and recovery effects;
- remaining production risks, especially PID/start-time subject identity; and
- one recommendation: keep Route 3, remediate named defects, or replace it.

Update the current handover and status only if their current-state summary has
actually changed. Do not create hashes, reading ledgers, activation records,
review prompts, proof chains or another planning package.
