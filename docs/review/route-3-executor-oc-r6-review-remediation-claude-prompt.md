# Claude remediation prompt — executor OC R6 interruption ownership

Status: **ACCEPTED AND AUTHORIZED REMEDIATION PROMPT**

Authority: Peter Duscha, Product Owner and Acceptance Authority

Implementer: Claude

Independent reviewer after return: Codex
Date: 2026-10-21

## Assignment

Correct the returned Route 3 executor OC R6 candidate in place. Independent
Codex review found one blocking implementation defect and one current-state
documentation defect. Preserve the selected architecture and every R6 result
that is not implicated by these findings.

This is one bounded correction, not a new design cycle. Update the existing
[`executor handback`](route-3-executor-oc-implementation-handback.md) in place
and return the corrected candidate for independent Codex re-review. Do not
create another handback or remediation chain.

The candidate is not accepted. Production or staging installation and
activation, a successor slice, commit and push remain unauthorized.

## Required context

Before changing anything, read:

1. `.agents/AGENTS.md` completely;
2. the reading map and §§0, 9, 13, 14, 16, 17 and 20 of
   `docs/implementation-plan.md`;
3. `docs/review/Handover information`;
4. `docs/operations/disposable-test-server.md`;
5. the accepted
   [`R6 implementation prompt`](route-3-executor-oc-r6-implementation-claude-prompt.md);
6. the final two sections of the cumulative executor handback; and
7. the relevant source and tests before editing them.

Preserve the shared dirty worktree. Do not discard or rewrite another agent's
changes. Use the canonical secret-excluding synchronization command for
`oracle-test`; use no real credential or player data.

## Finding 1 — Blocking: every post-write interruption must be owned

`SudoStopInvoker.invoke_stop()` currently catches only `OSError` around
`sendall(PROTOCOL_REQUEST)`, reply reads and the surrounding connection
boundary. A `KeyboardInterrupt` raised while `sendall` is executing escapes.
Codex reproduced this on the synchronized final tree with a fake connection:
the accepted request write raised `KeyboardInterrupt`, and `invoke_stop()`
propagated it rather than returning `PrivilegedStop.HANDED_OFF`.

This does not satisfy the accepted R6 contract. After the request write begins,
some or all bytes may have crossed; therefore every exceptional exit at or
after that boundary is owned/uncertain and must never grant retry permission.

Implement an explicit phase boundary:

- failures conclusively before `sendall(PROTOCOL_REQUEST)` begins may return
  `NOT_SENT`;
- set the post-write/owned state immediately before entering `sendall`;
- after that point, `OSError`, `KeyboardInterrupt`, `SystemExit`, another
  `BaseException`, reply failure, timeout, malformed reply and connection-close
  failure must produce `HANDED_OFF` rather than escape or return `NOT_SENT`;
- an exact result received without a later connection-boundary failure may keep
  its existing typed result;
- do not retry, reconnect or issue another request; and
- preserve the fixed protocol bytes, socket and peer-uid checks.

Use a narrow, readable state boundary. Do not broadly swallow a pre-write
interruption and misdescribe it as a delivered request. Trace the application
caller and retain exit 22/effect-not-confirmed behavior for an owned uncertain
outcome.

Add deterministic regressions that prove at least:

1. `KeyboardInterrupt` after the complete request line crosses returns
   `HANDED_OFF`;
2. interruption raised from `sendall` before its delivery extent is knowable is
   still `HANDED_OFF`;
3. interruption while waiting for the reply is `HANDED_OFF`;
4. a post-write connection-context/close exception is `HANDED_OFF`;
5. connect, peer and greeting failures before the write remain `NOT_SENT` and
   write no request; and
6. no case invokes or requests SA-2 twice.

Use events, barriers or controlled fakes where ordering matters. Do not use a
sleep as the proof of a race boundary. Include at least one real Unix-socket
case in which the peer receives the complete request before the local
interruption/failure is reported.

## Finding 2 — Important: reconcile current-state documentation

Claude's R6 return is present in the cumulative handback, but several current
authorities still say Claude must perform and return that implementation. Make
the current documents agree with the actual state and this assignment:

- `docs/review/Handover information`;
- `docs/project-management/status.md`;
- `docs/project-management/active-delivery-plan.md`;
- implementation-plan §20;
- `docs/project-management/decision-register.md`;
- the append-only `docs/project-management/change-log.md`; and
- `docs/review/README.md`.

They must say, consistently:

- Claude returned the first R6 implementation candidate;
- independent Codex review reproduced the main suites but found the blocking
  interruption-ownership defect above;
- Peter accepted this bounded remediation prompt and assigned Claude the
  correction;
- the candidate remains unaccepted pending remediation and re-review;
- no successor slice is assigned; and
- production/staging installation or activation remains prohibited.

Do not rewrite historical assignment text as though it never existed. Add an
append-only correction/assignment entry where the document is an append-only
record. Do not describe the implementation direction, candidate, independent
review or eventual Peter acceptance as the same event.

## Preserved implementation boundary

Do not reopen or redesign:

- the root-controlled system-service supervisor topology;
- the dedicated account's systemd user manager ownership of transient
  invocation units;
- durable `prepared`/`start-sent`/bound ownership and recovery;
- readiness ordering or serving-worker liveness handling;
- installer load-path, drop-in, effective identity and environment checks;
- the fixed sudo/SA-2 vector;
- Python `-I -S`, artifact trust and argv-only `stop` selection;
- environment minimization as defense in depth rather than an atomic premise;
- OC-1/OC-2/OC-3, journal validation, cgroup identity, drain/removal or
  one-shot launch behavior; or
- any accepted Route 3 role.

Change another area only if a regression demonstrates that the narrow repair
cannot otherwise be correct. Document that evidence before expanding scope.

## Required verification

Synchronize the exact final workspace to `oracle-test` and run, at minimum:

1. the complete executor ownership/usermanager/supervisor/interrupt/installer/
   system-service focused set;
2. the new interruption regressions, including the real-socket case;
3. documentation vocabulary checks;
4. `compileall`; and
5. `git diff --check`.

The independently reproduced pre-remediation baselines are:

- focused executor set: **484 passed**;
- SA-2/artifact set: **325 passed, 2 documented RLIMIT skips**;
- documentation vocabulary: **346 passed**; and
- root/systemd package module: **12 passed**.

Rerun the SA-2/artifact or root/systemd package module only if the final diff or
an observed failure touches their behavior; otherwise cite the independent
reproduction above and explain why the narrow repair cannot affect them. Run a
broader suite only when a changed dependency or observed failure makes it
material. Do not inflate evidence with unrelated test runs.

Report every failure, error, skip, retry, altered command and infrastructure
incident. Use `-o tmp_path_retention_policy=none` where appropriate on the
small `/tmp` tmpfs. Before returning, verify that no test account/group/home,
linger entry, sudoers fixture, unit/drop-in, service, transient unit, process,
cgroup, mount, state/runtime directory or pytest residue remains.

## Handback

Append one concise **R6 review remediation return** section to
`docs/review/route-3-executor-oc-implementation-handback.md` containing:

- the exact ownership-boundary correction;
- tests added and why they fail on the reviewed code;
- files changed;
- exact material commands and reliable results;
- failures, skips, retries and cleanup;
- confirmation that current documents are reconciled;
- remaining production prerequisites and risks; and
- a statement that nothing was accepted, committed, pushed or activated.

Stop after the handback. Codex independently re-reviews the final tree; Peter
decides acceptance afterward.
