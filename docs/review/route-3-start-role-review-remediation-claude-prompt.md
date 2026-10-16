# Claude remediation prompt — Route 3 static `start` role review findings

Date: 2026-10-15
Authority: baseline v1.9, the active handover and delivery plan, and the
independent Codex review of the SA-1 candidate
Mode: one bounded remediation and verification cycle on `oracle-test`; no
production or staging activation

## Assignment

Remediate the three findings from the independent review of the uncommitted
SA-1 static `start` candidate. Add regression tests that fail for the findings,
make the smallest corrections, rerun the required checks on `oracle-test`, and
update the existing SA-1 handback in place.

Do not return another plan or research package. Do not implement SA-2 `stop`, a
Package 5.0 coordinator, `consume`, `attest`, migration work, production
activation or unrelated cleanup. Preserve unrelated working-tree changes. Do
not commit or push.

The accepted Route 3 manager/Polkit adapter and the `hold`, `stop-post` and
`backstop` roles are not reopened by this remediation. Do not weaken their
validation, artifact checks, authorization boundary, result discipline or
tests to make SA-1 pass.

## Read before editing

1. `.agents/AGENTS.md` in full.
2. `docs/implementation-plan.md`: reading map, §§0, 12 Phase 5.0, 13, 14, 16
   and 20.
3. `docs/review/Handover information`.
4. `docs/project-management/active-delivery-plan.md`.
5. `docs/operations/disposable-test-server.md`.
6. `docs/review/route-3-start-role-implementation-claude-prompt.md` and
   `docs/review/route-3-start-role-implementation-handback.md`.
7. Operation inventory §§4.1, 5.6, 6 SA-1, 7, 8.1 and 11.1, especially
   `H-FI.1`, `SA1.FI.1`, `SA1.OP.1` through `SA1.OP.3`, `lease_s` and
   `stop_timeout_s`.
8. Interface contract §§3.0 and 3.2.
9. The current SA-1 implementation and its diff from accepted commit
   `a447558`.

Historical WP closure labels are not active development gates. Their accepted
SA-1, H-FI and DI-2 requirements remain implementation inputs.

## Review findings and required fixes

### 1. Enforce the holder-duration contract at the privileged role boundary

The current `start` parser delegates both duration fields to the shared
`HolderSpec` validator, which admits any integer from 1 through 604800. The
static role therefore accepts values outside the controlled holder contract,
including a one-second stop timeout, a seven-day stop timeout and a seven-day
holder lease, and can pass them to DI-2.

The role must enforce the bounds that are knowable from its fixed operands:

- `lease_seconds`: `61..86400`; and
- `stop_timeout_seconds`: `60..600`.

The accepted relationship `start_window_s < lease_s` is established by the
authority/coordinator that owns both values and cannot be re-derived from this
four-operand role. Do not add an A-2 read, another operand or another state
operation to SA-1 to manufacture that comparison. The role still independently
rejects every lease that cannot possibly satisfy the accepted relationship and
every duration outside the absolute accepted ranges.

Keep decimal spelling canonical: ASCII digits only, no sign, whitespace,
leading zero, alternate base or extra operand. Reject malformed or out-of-range
durations before opening the bus or performing any DI-2 operation.

Prefer a holder-specific validator or value-object rule. Do not narrow the
accepted backstop interval/runtime fields accidentally by changing one shared
helper without separating their different contracts.

Add boundary tests for at least:

- accepted leases `61` and `86400`;
- refused leases `0`, `1`, `60`, `86401` and `604800`;
- accepted stop timeouts `60` and `600`;
- refused stop timeouts `0`, `1`, `59`, `601` and `604800`;
- leading-zero and non-ASCII-digit aliases; and
- proof that every refused vector opens no bus and creates no unit.

Reproduce at least one currently accepted out-of-contract value before fixing
it, then retain that case as a regression.

### 2. Make the real-host authorization proof exact

`test_without_authorization_the_role_is_refused_and_creates_nothing` currently
allows either the required `refused not-authorized` result or a generic
pre-send error. A broken connector, unavailable manager, failed subscription or
other setup defect can therefore pass a test described as proof of Polkit
authorization refusal.

On `oracle-test`, require the unprivileged exact artifact invocation to return:

```text
exit 20
rp11-start refused not-authorized
```

and prove that no unit or job was created. A pre-send error is a test failure,
not an alternate authorization result. If the disposable-host fixture does not
reliably establish the intended Polkit/systemd state, correct the fixture
without weakening the production boundary or accepting a broader result.

Retain separate fake-boundary coverage for pre-send connector and subscription
errors; those remain valid `effect-not-sent` application outcomes, but they are
not authorization-refusal evidence.

### 3. Exercise a genuinely duplicate raw `INVOCATION_ID`

The handback claims duplicate-environment coverage, but assigning the same key
through `os.environ` and `os.environb` replaces one mapping entry. It does not
construct the duplicate entries that `/proc/self/environ` can represent.

Add a deterministic subprocess/`execve` regression whose raw `envp` contains
two `INVOCATION_ID=` entries. A small test-only harness may call `execve`
directly with an explicit environment vector; do not add a compiler or runtime
dependency to the production artifact.

Prove with that same raw duplicate environment that:

1. a valid exact `start` invocation has the same result as the empty-environment
   control, reaches the role with `invocation_id=absent`, and has an empty
   environment after first-image controls; and
2. each implemented unit-started role that consumes provenance (`hold`,
   `deact ... stop-post`, and `backstop`) refuses before its composition root
   runs, with exit 64 and the fixed malformed/duplicate diagnostic.

Keep the existing direct regression that makes `_initial_environment()` fail
if the valid `start` path calls it. Do not replace end-to-end raw-environment
proof with another mapping assignment or only a unit test of
`invocation_id_from()`.

## Required verification

All test levels remain authorized on `oracle-test`. Use synthetic data and the
documented secret-excluding synchronization command. Do not touch production,
staging, real secrets or player data.

Run, at minimum, on the final tree:

1. `tests/test_rp11_start.py`, `tests/test_rp11_h1_artifact.py` and
   `tests/test_systemd_unit_control.py`;
2. `tests/systemd_integration/test_route3_start_host.py` as root with a fresh
   controlled artifact built from the pinned Jeepney wheel;
3. the complete existing Route 3 manager/artifact and role host suites needed
   to prove the duration change did not regress `hold`, `stop-post` or
   `backstop`;
4. the production-file scope guard;
5. Python compilation and `git diff --check`; and
6. broader bot, web and Foundry comparisons in proportion to the final shared
   surface. If shared production validation changes, run the documented full
   suites serially with `TEST_DATABASE_URL` exported and report the correct
   skip counts.

For every result, record the exact copy-pastable command, exit status, pass,
fail, error and skip counts, and every skip reason. Do not substitute a prose
suite description for the command. Do not label an unrelated failure
pre-existing unless it was actually compared with the relevant baseline or
clearly identify the statement as an inference.

After root tests, verify separately that no RP-11 unit, process, Polkit rule,
artifact, staging directory, store or test evidence from this work remains and
that `polkit.service` is active.

## Acceptance criteria

- The static `start` boundary rejects holder durations outside the accepted
  absolute ranges before DI-2 and accepts both range endpoints.
- No duration validation change broadens or accidentally narrows the accepted
  backstop contract.
- The real-host denial test proves the exact `not-authorized` result and cannot
  pass on a transport, manager, subscription or fixture failure.
- A real duplicate raw `INVOCATION_ID` cannot affect a valid `start`, while all
  three provenance-consuming roles still refuse it.
- `start` still reads no environment variable, makes exactly one DI-2 call,
  never retries an unconfirmed mutation and preserves the accepted three-way
  result.
- Existing PID-1 role vectors, artifact integrity checks and Route 3 lifecycle
  tests remain green.
- The disposable host is clean and production/staging remain unchanged.

## Handback update

Update `docs/review/route-3-start-role-implementation-handback.md` in place with
one concise remediation section. Do not create another handback. Include:

- each review finding and its disposition;
- principal files changed;
- the exact duration rules and boundary-test coverage;
- the exact raw duplicate-environment method and outcomes;
- the exact authorization-refusal outcome;
- exact copy-pastable final-tree commands and results, including failures and
  skips;
- host cleanup state;
- remaining production risks; and
- one recommendation: accept SA-1 for continued non-production development or
  remediate one specifically named remaining blocker.

Correct the current recommendation while remediation is in progress and do not
record maintainer acceptance. Return the uncommitted candidate for independent
Codex re-review. SA-2 remains deferred until that review and Peter's acceptance.
