# Claude implementation prompt — complete the Route 3 executor OC slice

Date: 2026-10-18
Authority: Peter Duscha, baseline v1.9, and the active implementation-first
delivery plan
Reviewer after handback: Codex
Mode: continuation of the original implementation; full disposable-server
testing; no production or staging activation

## Delivery intent

Continue and complete the implementation assigned by
`route-3-executor-oc-implementation-claude-prompt.md`.

This is **not a remediation assignment** and must not become another proof or
documentation cycle. The current uncommitted candidate is an implementation in
progress. Make the production code satisfy its original lifecycle invariant,
test the result at every appropriate level on `oracle-test`, and return one
concise updated implementation handback.

The long-term objective is a secure, performant, maintainable platform and an
inactive-by-default production installation package. Optimize this slice for
that objective: preserve fail-closed authorization, provide real process
containment, keep the ordinary success path small and bounded, and do not make
test-only claims that the production implementation cannot uphold.

Do not commit or push. Do not touch production or staging.

## Governing instructions and working tree

Before editing, read and follow the complete current authorities required by
the repository `AGENTS.md`, including `.agents/AGENTS.md`, the implementation
plan reading map and required sections, `docs/review/Handover information`, the
active delivery plan, and the disposable-server procedure.

Then inspect:

- the original executor implementation prompt;
- the current executor handback;
- the complete uncommitted diff and `git status`;
- `application/executor/interrupt.py`;
- `adapters/executor/interrupt.py`;
- both executor test modules; and
- the accepted SA-2 implementation and its process/timeout behavior.

Preserve all accepted Route 3 work and unrelated maintainer changes. The
working tree, not the last commit, is the implementation base.

## What is already acceptable

Retain the current fail-closed OC-1/OC-2/OC-3 decision, fixed unit and journal
selection, descriptor-safe bounded journal read, fixed `sudo -n` SA-2 vector,
one-attempt behavior, stable diagnostics, and typed result mapping unless a
demonstrated defect requires a change.

The successful-consume validator is adequate for the original OC-3 assignment.
Additional checks of non-authoritative journal detail fields may be sensible
hardening for the later production security review, but they are not blockers
for this completion and must not distract from the process-lifecycle defect.

## Required implementation completion

The original assignment requires:

> Bound the child wait and settle it safely on cancellation/interruption. Do
> not leave a `sudo`/SA-2 child running merely because the executor stopped
> waiting.

The current candidate does not yet establish that invariant. In particular:

- `_settle_bounded()` discovers descendants through current `PPid` links;
- it stops discovering them after the direct `sudo` child is reaped;
- a process created after the initial scan can be reparented and survive
  without any retained watch; and
- interruption during `Popen` is currently mapped to `UNSETTLED` without a
  child handle even though creation may have occurred.

A typed `UNSETTLED` result is honest about uncertainty, but it is not process
settlement and does not satisfy the quoted requirement. Do not relabel that
outcome as completion.

Implement a production-valid supervision design that satisfies all of these:

1. On every return after a successful launch, the executor has affirmative
   evidence that the launched `sudo`, the SA-2 process, and every process still
   belonging to that controlled invocation have exited.
2. Cancellation, `SIGTERM`, `SIGINT`, timeout, signal delivery races, direct
   child exit, late descendant creation, reparenting, and ordinary exceptions
   cannot abandon the invocation.
3. Identification is resistant to PID reuse. Do not kill or accept an unrelated
   process based only on a numeric PID, process name, command text, or an old
   `/proc` observation.
4. The design does not require polling an unbounded process tree, busy-waiting,
   or adding meaningful latency to the ordinary successful SA-2 path.
5. Resource use is capped and failures remain fail-closed. No retry of SA-2 and
   no later unit-state observation may turn uncertainty into success.
6. The behavior is based on a kernel-enforced or kernel-observed invocation
   boundary that remains usable after reparenting. The existing new session may
   be used if a complete, race-safe argument and implementation can be made;
   pidfds, process-session membership, a subreaper, or a scoped supervisor may
   be combined where appropriate. A one-time `PPid` tree snapshot alone is not
   sufficient.
7. Handle the `Popen` interruption window correctly. Do not claim that no
   process exists unless the launch API contract proves it. Prefer structuring
   signal handling so that asynchronous interruption cannot lose the only
   handle to a created child.

Do not solve this by weakening the invariant, suppressing interruption
indefinitely, waiting forever, broad process killing, adding an unrestricted
privileged command, or writing tests that omit the race.

If the exact accepted `sudo -n ... rp11_h1.py stop` boundary makes bounded,
affirmative settlement technically impossible for an unprivileged executor,
stop before inventing a false guarantee. In that case, return a short,
evidence-backed engineering decision identifying:

- the exact impossibility;
- the smallest privilege/supervision boundary change that resolves it;
- its security and performance consequences;
- the tests that would establish it; and
- whether it changes an accepted authorization or production-activation
  decision requiring Peter's approval.

Do not implement a materially broader privileged boundary without that
approval. Exhaust solutions that preserve the fixed vector first.

## Required tests

Add or correct tests that exercise the production adapter rather than only a
mock outcome. At minimum prove:

1. normal SA-2 success returns promptly and leaves no invocation process;
2. timeout and executor interruption settle and reap the direct child;
3. a descendant present before termination is observed through exit;
4. a descendant created during the termination race, after the first discovery
   pass, cannot escape through reparenting;
5. the direct child exiting before discovery does not make an extant invocation
   member invisible;
6. repeated signals during settlement do not abandon it;
7. PID reuse or inconsistent identity evidence is never treated as proof and
   never targets an unrelated process;
8. process-count/resource caps fail closed without broad killing;
9. the `Popen` interruption window cannot lose a launched child; and
10. all existing OC unavailability paths still launch no privileged process,
    while every SA-2 outcome still invokes it at most once.

Use deterministic synchronization for race tests; do not depend on arbitrary
sleeps. Include a focused real-host test on `oracle-test` using synthetic
artifacts and the real unprivileged `ubuntu` entry point. After every host test,
prove that no test executor, `sudo`, SA-2, capture unit, or invocation member
remains.

Add a small performance assertion or measurement appropriate to this code:
the normal already-completed child path must not incur a settlement grace
period or repeated `/proc` scans. Avoid brittle wall-clock microbenchmarks; use
observable call counts plus a generous end-to-end upper bound on the disposable
host if timing evidence is useful.

## Verification

After implementation, run on the final synchronized tree:

- the complete executor unit/adapter tests;
- the complete executor systemd-integration module;
- focused accepted `stop`, `consume`, `attest`, manager, artifact, and
  unit-control regressions;
- the complete `tests/systemd_integration` suite serially;
- the documented bot, web, and Foundry suites serially with their required
  environment and expected skips;
- configured compile, lint/type/static and guard checks; and
- `git diff --check` plus final disposable-host cleanliness checks.

Report actual pass/fail/error/skip results. Do not call a failure pre-existing
without comparison to the accepted baseline. Do not include a terminal
transcript when a concise evidence summary establishes the claim.

## Scope control

This assignment completes the existing executor OC slice. Do not implement the
full coordinator, scheduler, start orchestration, automatic attestation, or
production installer here. Those are the next production implementation
slices after this one is accepted; do not create new documentation gates for
them.

Do not change product behavior, production data authority, authorization or
privacy policy, destructive production behavior, or production activation.
Use no real secrets or player data.

## Handback

Update the existing executor implementation handback in place. Describe this
work as completion of the original implementation, not remediation. Include
only:

- the final supervision design and why its identity/lifecycle evidence is
  sufficient;
- production files changed;
- material deterministic and real-host tests;
- complete verification results and skips;
- remaining production risks, if any; and
- the next implementation slice: full coordinator/start orchestration, unless
  a genuine authority decision blocks it.

The handback is ready for review only when the code satisfies the original
lifecycle requirement or clearly demonstrates why the accepted privilege
boundary cannot satisfy it. Passing tests alone must not substitute for the
process-safety argument.
