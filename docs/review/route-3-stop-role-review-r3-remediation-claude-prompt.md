# Claude remediation prompt — Route 3 static `stop` host-job assertion scope

Date: 2026-10-16
Authority: baseline v1.9, the active implementation-first delivery plan, and
the independent Codex re-review of the twice-remediated uncommitted SA-2
candidate
Mode: one bounded test-only remediation and verification cycle on
`oracle-test`; no production or staging activation

## Assignment

Remediate the one remaining verification blocker in the SA-2 static `stop`
candidate: two real-host assertions incorrectly require the disposable host's
entire systemd job queue to be empty, although the behavior under test requires
only that no job for `rp11-capture-pass-a.service` remains or was queued.

Make the smallest test-only correction, prove it while an unrelated systemd
job is deliberately present, rerun the required final-tree checks, and append
the result to the existing SA-2 handback.

Do not change `application/rp11/stop.py`, `adapters/rp11/stop.py`, the accepted
manager/Polkit adapter, the controlled-artifact runtime, SA-1 `start`, or the
accepted `hold`, `stop-post` and `backstop` roles. The two typed-result fixes
have independently reproduced their required fail-closed outcomes and are not
reopened by this test correction.

Do not create another plan, review record or handback. Do not implement a
Package 5.0 coordinator, executor OC-1/OC-2/OC-3 checks, `consume`, `attest`,
migration work, production activation or unrelated cleanup. Preserve unrelated
working-tree changes. Do not commit or push.

## Read before editing

1. `.agents/AGENTS.md` in full.
2. `docs/implementation-plan.md`: reading map, §§0, 12 Phase 5.0, 13, 14, 16
   and 20.
3. `docs/review/Handover information`.
4. `docs/project-management/active-delivery-plan.md`.
5. `docs/operations/disposable-test-server.md`.
6. `docs/review/route-3-stop-role-implementation-claude-prompt.md`, both prior
   stop remediation prompts, and
   `docs/review/route-3-stop-role-implementation-handback.md`.
7. `tests/systemd_integration/test_route3_stop_host.py`, its imported host
   fixtures, and the complete current diff from accepted commit `a447558`.

Historical WP closure labels are not current development gates. Their accepted
SA-2 and DI-S requirements remain implementation inputs.

## Blocking finding — assertions inspect unrelated host jobs

The active-success and authorization-denial tests currently end with:

```python
assert run("systemctl", "list-jobs", "--no-legend").stdout.strip() == ""
```

at `tests/systemd_integration/test_route3_stop_host.py:64` and `:136` in the
reviewed tree. This asks whether *any* systemd job exists on `oracle-test`, not
whether SA-2 left or queued a job for the fixed capture unit.

The implementation handback already disclosed a first-run failure of the line
64 assertion followed by a passing rerun. Independent Codex re-review then
reproduced the same defect at line 136:

```text
445262 apt-daily.service start running
```

The SA-2 result and all capture-unit state assertions passed; only the
host-global empty-queue assertion failed. The isolated test passed after the
unrelated job completed. This establishes a test-scope defect, not an SA-2
runtime failure.

Replace both host-global assertions with an exact capture-unit-specific check.
Prefer asking `systemctl list-jobs` for the literal fixed unit or parsing the
unit column exactly. A broad substring assertion is acceptable only if it
cannot confuse another unit name with the fixed capture unit. Match the
already-correct intent of the not-loaded test: prove that no stop job for
`rp11-capture-pass-a.service` is queued without making any claim about jobs
owned by apt, timers, package maintenance or another service.

Do not weaken the surrounding behavior checks:

- active stop must still return exit 0, render exactly `rp11-stop stopped`, and
  leave the fixed unit inactive;
- authorization denial must still return exit 20, render exactly
  `rp11-stop refused not-authorized`, preserve the same capture-unit
  `ActiveState`, `InvocationID` and `MainPID`, and queue no job for that unit;
- the connector proof must still observe exactly one
  `StopUnit(rp11-capture-pass-a.service, "fail")`;
- the not-loaded, post-send uncertainty, exact-vector and hostile-environment
  cases remain unchanged; and
- no assertion may hide a job for the fixed capture unit merely because an
  unrelated job also exists.

Keep the correction focused in
`tests/systemd_integration/test_route3_stop_host.py`. A small local helper is
permitted if it makes exact unit scoping clearer and is used by every
applicable assertion. Do not add sleeps, retries, polling for a globally empty
queue, disable timers, stop apt services or otherwise alter the host to make
the old assertion pass.

## Required unrelated-job proof

On `oracle-test`, deliberately keep one synthetic, unrelated, bounded oneshot
job in the systemd queue while running the two corrected tests. Use a unique
test-only unit name that cannot match `rp11-capture-pass-a.service`, synthetic
arguments only, and a finite duration long enough for both tests. Establish
before the test invocation that `systemctl list-jobs --no-legend` shows that
unrelated unit.

The proof must show simultaneously:

1. the unrelated job is present;
2. both corrected SA-2 tests pass;
3. neither test mistakes the unrelated job for a capture-unit job; and
4. teardown stops/resets/removes the synthetic unit even if the test command
   fails.

Use an explicit shell cleanup trap or an equivalently reliable bounded cleanup
procedure. Do not reuse or disturb `apt-daily.service`, another system service,
or any pre-existing `/var/tmp/p5-r5-rp11-h0*` path. Record the exact commands
and output needed to establish presence and cleanup; do not merely infer that a
background job overlapped the tests.

## Required verification

All test levels remain authorized on `oracle-test`. Use synthetic data and the
documented secret-excluding synchronization command. Do not touch production,
staging, real secrets or player data.

Run on the final tree, at minimum:

1. the deliberate unrelated-job proof above over
   `test_an_active_capture_unit_receives_one_stop_and_the_role_returns_stopped`
   and
   `test_without_authorization_the_role_is_refused_and_the_unit_keeps_running`;
2. the complete `tests/systemd_integration/test_route3_stop_host.py` module as
   root with a fresh controlled artifact from the pinned Jeepney wheel;
3. `tests/test_rp11_stop.py`, `tests/test_rp11_start.py`,
   `tests/test_rp11_h1_artifact.py` and `tests/test_systemd_unit_control.py`;
4. Python compilation over the touched Python test path; and
5. `git diff --check`.

The complete `tests/systemd_integration` suite, bot suite, web suite and Foundry
suite need not be repeated solely for this assertion-scope correction: the
twice-remediated code under test is unchanged and the complete systemd suite
already passed on that exact code. Run broader suites if production code,
shared fixtures or another surface changes despite this boundary.

For every check, record the exact copy-pastable command, working directory,
exit status, pass/fail/error/skip counts and every skip reason. Do not cite a
pre-fix or intermediate count as final-tree evidence. Clearly distinguish the
new deterministic unrelated-job proof from the earlier incidental
`apt-daily.service` observation.

After root tests, verify separately that:

- the synthetic unrelated proof unit is absent and has no queued job;
- no RP-11 unit or process remains;
- no RP-11 Polkit rule, artifact, staging directory or store remains;
- no `/var/tmp/rp11-act-*` path or SA-2 evidence/log remains;
- the unrelated `/var/tmp/p5-r5-rp11-h0*` paths were not removed; and
- `polkit.service` is active.

## Acceptance criteria

- Neither corrected test requires the host-global systemd job queue to be
  empty.
- Both tests prove exactly that no job for
  `rp11-capture-pass-a.service` remains or was queued at the asserted point.
- Both corrected tests pass while a separately established unrelated systemd
  job is present.
- The existing result, state-preservation, fixed-target and one-call assertions
  remain intact.
- No production module, shared result object, manager adapter or controlled
  artifact source changes.
- The complete SA-2 host module and focused application/artifact suites pass on
  the final tree with every skip reported.
- Current-state documents describe the host-verification correction as
  complete and independent Codex re-review pending without claiming
  acceptance.
- The disposable host is clean and production/staging remain unchanged.

## Handback update

Append one concise host-verification remediation section to
`docs/review/route-3-stop-role-implementation-handback.md`; do not create a new
handback. Include:

- the host-global assertion defect and the independent `apt-daily.service`
  reproduction;
- the exact unit-scoped correction;
- the deliberate unrelated-job proof, including establishment and cleanup;
- principal file changed;
- exact final-tree commands and results, including failures and skips;
- final host cleanup state;
- unchanged remaining production risks; and
- one recommendation: accept SA-2 for continued non-production development or
  remediate one specifically named remaining blocker.

Update only the current-state documents needed to say that this bounded
test-only remediation is complete and independent Codex re-review is pending.
Do not record Peter's acceptance or any production/staging authorization that
has not happened.

Return the uncommitted candidate for independent Codex re-review. Production
and staging activation remain unauthorized; the transient inspection-failure
decision and final independent production security review remain mandatory
before any activation.
