# Claude implementation prompt — Route 3 hold role

Date: 2026-10-13
Authority: Peter Duscha's Route 3 acceptance, baseline v1.9 and the active
delivery plan
Sequence: run only after stop-post and backstop are implemented and their
blocking defects are closed

## Assignment

Implement the exact controlled holder vector:

```text
/usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py \
  hold <activation_id> <a2_sha256>
```

Implement RT-2 ACT, AK-1, AM-0 through AM-3, AV-1, hold-start, HL, IGR and GRR
over the accepted manager/Polkit adapter and the already implemented cleanup
rungs. This is still an inactive disposable-host implementation. Do not add a
production caller, implement consume/attest/static start/stop, repair unrelated
baseline failures, commit or push.

## Required context

Read the canonical agent agreement; implementation plan reading map and
§§0/12 Phase 5.0/13/14/16/20; active handover/plan; disposable-server guide;
accepted adapter handback; and completed stop-post/backstop handbacks and code.
From the operation inventory read §§2.3–2.4, 3, all §4 helpers used by RT-2,
5.2, 6 RT-2, 7, 8.1, 9, 10.2–10.5, 11.1 and applicable §12 gaps. Read the
interface contract §§3.0–3.6.

Treat explicit GAP rows as non-operative. In particular, do not invent the
AM-0 unterminated-activation check. Select reversible missing paths and typed
representations narrowly, root-control them, and pin them in tests.

The observed polkitd-127 behavior is an implementation input, not a new gate:
for successful disposable-host flows, create `/run/polkit-1/rules.d` before
Polkit starts and restart Polkit only as harness setup. Also prove that a
directory first created after Polkit starts makes AV-1 fail closed. The holder
must never restart or reload Polkit. Peter has selected a `tmpfiles.d` entry as
the preferred future installer/activation design, but installing it and proving
it across a real reboot remain outside this slice and are required before
production activation. Do not install or reboot-test that production mechanism
here. The backstop slice's Q6-7 fail-closed behavior is accepted.

## Required behavior

- Apply H-FI and install the exact flag-only SG-1 handlers before state work.
  Handlers only set `stop_requested`; all I/O, cleanup and exit decisions remain
  in the main thread. Check the flag at every required boundary and sliced wait.
- Validate the A-2 digest and bounded typed content, boot id, `/run` tmpfs and
  parent safety, required absence conditions and exact allowed unit states.
- Create and exclusively lock K using descriptor-relative no-follow operations.
  Establish the capture baseline with the accepted monotonic ordering and at
  most five 2-ms retries; a read error never becomes an inactive baseline.
- Create the ACT journal and preserve its canonical hash chain, write-ahead
  ordering, volume bounds and durability contract.
- AK-1: write `backstop-intent` before DI-3, create the exact accepted timer and
  service through `SystemdManagerAdapter`, treat unconfirmed effect as unknown
  and never retry silently, verify the timer through DI-1, then durably record
  `backstop-armed`.
- Build and publish tree P, any admissible tree R, `grant.id` and the Polkit rule
  through the accepted PF/PT protocols. Never replace an existing name. Link
  the grant only after its identity is durable and check the stop flag
  immediately before and after the link.
- AV-1: reload/verify the rule and recompute the complete baseline; perform the
  positive `start` and negative `stop` Polkit controls through DI-5/DI-6. Any
  malformed, denied-positive, authorized-negative or unconfirmed result fails
  closed and invokes IGR/cleanup.
- AM-3 publishes the no-replace activation record; only its durable commit is
  ACT PASS. `hold-start` must be durable before K is closed.
- HL polls at the accepted bounded interval, uses DI-1 under the lock for each
  decision, implements the accepted OS-1/OS-5/OS-7 outcomes and never guesses
  from a failed observation.
- On every catchable end, run IGR exactly once. GRR removes only the immediately
  reverified attributable intact grant, before slower work. Then return so
  PID 1 runs the already implemented stop-post cleanup.
- Reuse the shared journal, record, attribution, subject and cleanup modules;
  do not duplicate them. Keep all output bounded and safe and every new module
  in the exact artifact manifest.

## Tests and host execution

Trace every RT-2 row to a named test or host check. At minimum cover:

- all first-image and signal-delivery boundaries, including a second signal and
  each catchable/uncatchable termination class that can be exercised safely;
- A-2, H-1, pass configuration, staged-rule and baseline corruption/size cases;
- boot, tmpfs, parent mode/owner/ACL, path type/symlink and absence failures;
- K collision, lock failure, BSP retry boundaries and capture busy states;
- every journal/PF/PT short-write, flush, collision, replacement and recovery
  point;
- DI-3 success, exists, authorization refusal, timeout, disconnect, lost reply,
  late completion and proof of one send/no retry;
- exact timer/service properties and active-state verification;
- stop flags immediately before/after rule link and during every bounded wait;
- AV-1 positive/negative Polkit controls, malformed subjects/replies and subject
  cleanup;
- AM-3 publication collision and failed-act recovery by stop-post/backstop;
- HL normal completion, observation failure, start-before-hold and concurrent
  stop/expiry; and
- IGR idempotency, damaged/foreign grant retention, unremovable grant and
  handoff through real `ExecStopPost` and backstop recovery.

On `oracle-test`, build the final root-owned artifact and run genuine PID-1
holder, stop-post and backstop flows with synthetic A-2/H-1/pass/rule inputs.
Exercise success, failure injection, signals, lease expiry, manager/polkit
restart, duplicate activation, lost replies, hard cleanup and recovery. Prove
no grant survives a completed safe path and no foreign/damaged object is
removed. Clean every unit, rule, subject, artifact, staging directory and test
evidence after each run; leave `polkit.service` active.

Run focused suites locally and remotely, then re-sync and run bot, web and
Foundry serially with the documented database setting. Compare exact failures,
errors and skips to the accepted baseline; do not fix unrelated failures or
weaken guards. Run guard tests, `git diff --check`, `compileall` and configured
static checks.

## Acceptance and handback

The slice is acceptable only if all RT-2 rows have evidence, ACT PASS cannot
precede durable verification, every catchable end attempts IGR exactly once,
manager/authorization uncertainty never becomes success, real PID-1 flows
recover through stop-post/backstop, cleanup is complete, and no new repository
regression appears.

Write `docs/review/route-3-hold-role-implementation-handback.md` with delivered
behavior/files, row-to-test coverage, exact results and unchanged baseline
failures, real-host interruption/recovery outcomes, cleanup, remaining
production risks and one recommendation: accept the complete role series,
remediate one blocker, or replace the approach. Do not create another prompt,
proof chain or activation record.
