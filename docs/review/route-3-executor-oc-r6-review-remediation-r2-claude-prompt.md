# Claude remediation prompt — executor OC R6 deterministic proof and current state

Status: **ACCEPTED AND AUTHORIZED REMEDIATION PROMPT**

Authority: Peter Duscha, Product Owner and Acceptance Authority

Implementer: Claude

Independent reviewer after return: Codex

Date: 2026-10-21

## Assignment

Correct the returned Route 3 executor OC R6 remediation candidate in place.
Independent Codex re-review found no remaining defect in the post-write
ownership implementation, but found one defect in its required real-socket
proof and one current-state documentation defect. Preserve the implementation
and every result not implicated by these findings.

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
   [`R6 review-remediation prompt`](route-3-executor-oc-r6-review-remediation-claude-prompt.md);
6. the final three sections of the cumulative executor handback; and
7. `adapters/executor/interrupt.py` and the relevant tests before editing them.

Preserve the shared dirty worktree. Do not discard or rewrite another agent's
changes. Use the canonical secret-excluding synchronization command for
`oracle-test`; use no real credential or player data.

## Finding 1 — Important: the real-socket proof is not deterministic

The returned ownership implementation is correct as reviewed: the phase flag
is set immediately before `sendall(PROTOCOL_REQUEST)`, and every
`BaseException` at or after that boundary becomes `HANDED_OFF`. Do not redesign
or reopen that code without a demonstrated regression.

The two new real Unix-socket tests do not yet provide the deterministic proof
claimed by the handback. Their peer threads call `recv(64)` once and then set
the `crossed` event. Unix stream sockets do not preserve message boundaries and
one `recv` may return only a prefix. The event can therefore release the local
`KeyboardInterrupt` before the peer has received the complete
`PROTOCOL_REQUEST`; a later assertion may fail, but the ordering proof itself
is not deterministic.

Correct the tests so that the peer reads exactly the complete fixed request
before publishing the event. Use a bounded explicit read loop or an equivalent
deterministic helper that:

- accumulates bytes until exactly `len(PROTOCOL_REQUEST)` bytes have arrived;
- fails on EOF, timeout, surplus or a value different from
  `PROTOCOL_REQUEST`;
- sets `crossed` only after that exact complete request is held by the peer;
- retains event/barrier ordering and uses no sleep as race evidence;
- proves the local `KeyboardInterrupt` is reported only after that event;
- closes and joins every socket/thread reliably even when an assertion fails;
  and
- still proves one connection, one request and no retry.

Apply this to both real-socket interruption cases: interruption reported from
the request write after the complete line crossed, and interruption while the
peer holds the complete request and the client waits for a reply. Keep the
scripted write/reply/close `BaseException` matrix and definite pre-write tests.

Demonstrate that the corrected real-socket tests fail against the reviewed
pre-remediation ownership code for the intended reason, or retain the already
reported mutation evidence where it directly applies. Do not introduce a
timing-only test or rely on a successful run as proof that a single `recv`
returned all bytes.

## Finding 2 — Important: reconcile the actual returned state

The cumulative handback contains the R6 review-remediation return, but current
authorities still describe that remediation as merely assigned. Reconcile:

- `docs/review/Handover information`;
- `docs/project-management/status.md`;
- `docs/project-management/active-delivery-plan.md`;
- implementation-plan §20;
- `docs/project-management/decision-register.md`;
- the append-only `docs/project-management/change-log.md`; and
- `docs/review/README.md`.

They must distinguish the events and say consistently:

- Claude returned the first R6 implementation candidate;
- independent Codex review found the post-write `BaseException` ownership gap;
- Peter assigned the first bounded R6 review remediation;
- Claude returned that remediation with the corrected ownership boundary;
- independent Codex re-review found no remaining implementation defect, but
  found the nondeterministic real-socket proof and stale current-state text;
- Peter accepted this second bounded remediation prompt and assigned Claude
  the correction;
- the candidate remains unaccepted pending this correction and independent
  re-review;
- no successor slice is assigned; and
- production/staging installation or activation remains prohibited.

Do not rewrite historical assignment or return text as though it never
existed. Add an append-only correction/assignment entry where the document is
append-only. Do not conflate prompt acceptance, implementation return,
independent review or eventual Peter acceptance.

## Preserved implementation boundary

Do not reopen or redesign:

- `SudoStopInvoker.invoke_stop()` or its write-started ownership boundary,
  absent a regression caused by the test repair;
- the root-controlled system-service supervisor topology;
- the dedicated account's systemd user-manager ownership of transient units;
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

1. the two corrected real Unix-socket interruption tests repeatedly enough to
   exercise their synchronization without converting repetition into the
   proof;
2. the complete executor ownership/usermanager/supervisor/interrupt/installer/
   system-service focused set;
3. the relevant documentation/current-state checks that can be identified;
4. `compileall`; and
5. `git diff --check`.

The independent re-review baseline is:

- focused executor set: **509 passed**;
- `tests/web/test_p3_4_static_assets.py`: **110 passed, 1 unrelated failure**
  naming five undeclared `tools/phase_5_0_evidence/` files;
- `compileall`: clean; and
- `git diff --check`: clean.

Do not rerun the SA-2/artifact set or root/systemd package module unless the
final diff or an observed failure touches their behavior. The reviewed repair
is client-test and documentation only. Run a broader suite only when a changed
dependency or observed failure makes it material.

Report every failure, error, skip, retry, altered command and infrastructure
incident. Use `-o tmp_path_retention_policy=none` where appropriate on the
small `/tmp` tmpfs. Before returning, verify that no test account/group/home,
linger entry, sudoers fixture, unit/drop-in, service, transient unit, process,
cgroup, mount, state/runtime directory or pytest residue remains.

## Handback

Append one concise **R6 review remediation R2 return** section to
`docs/review/route-3-executor-oc-implementation-handback.md` containing:

- the deterministic full-request socket synchronization correction;
- why the old single-`recv` tests did not establish the claimed order;
- current-state documents changed;
- exact material commands and reliable results;
- failures, skips, retries and cleanup;
- remaining production prerequisites and risks; and
- a statement that nothing was accepted, committed, pushed or activated.

Stop after the handback. Codex independently re-reviews the final tree; Peter
decides acceptance afterward.
