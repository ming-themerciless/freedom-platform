# Claude remediation prompt — executor OC R6 socket-proof ordering assertion

Status: **ACCEPTED AND AUTHORIZED NON-BLOCKING REMEDIATION PROMPT**

Authority: Peter Duscha, Product Owner and Acceptance Authority

Implementer: Claude

Independent reviewer after return: Codex

Date: 2026-10-22

## Assignment

Correct one narrow defect in the returned Route 3 executor OC R6 socket-proof
hardening. Independent Codex review found no production-code or safety defect,
and the recommendation to accept the production candidate remains unchanged.
The defect is confined to one real-socket test's proof of event ordering.

This is test-only remediation. Update only the implicated test in
`tests/test_executor_supervisor.py` and append the return to the existing
[`executor handback`](route-3-executor-oc-implementation-handback.md). Do not
change production code, create another handback, or reopen the R6 design.

The production candidate remains unaccepted pending Peter's decision. No
successor slice, production or staging installation or activation, commit, or
push is authorized.

## Required context

Before changing anything, read:

1. `.agents/AGENTS.md` completely;
2. the reading map and §§0, 13, 16 and 20 of
   `docs/implementation-plan.md`;
3. `docs/review/Handover information`;
4. `docs/operations/disposable-test-server.md`;
5. the accepted
   [`socket-proof hardening prompt`](route-3-executor-oc-r6-nonblocking-test-hardening-claude-prompt.md);
6. the final three sections of the cumulative executor handback; and
7. the real-socket helper and tests in `tests/test_executor_supervisor.py`.

Preserve the shared dirty worktree. Do not discard or rewrite another agent's
changes. Use no real credential or player data.

## Finding — Important: the write-error test can pass without its write error

In
`test_a_request_write_after_the_complete_line_crossed_is_owned_never_retryable`,
the patched `sendall_then_fail()` currently does this:

```python
if not crossed.wait(5):
    return
raise BrokenPipeError
```

If the wait times out, the patched write returns normally. The invoker can then
reach its ordinary reply path and still return `HANDED_OFF`; meanwhile the peer
may set `crossed` before the final assertions run. The test can therefore pass
without establishing that `crossed.wait(5)` returned true and without injecting
the `BrokenPipeError` named by the test and handback.

Correct the test so that it records the result of the bounded wait, always
injects the intended `BrokenPipeError` after that wait, and asserts on the test
thread that the recorded wait result was exactly true. Follow the adjacent
real-socket `KeyboardInterrupt` test's `order == [True]` pattern or an equally
small deterministic equivalent.

The corrected test must prove all of the following:

- the real client sent exactly one `PROTOCOL_REQUEST` on one connection;
- the test-only half-close let the peer establish exact request plus EOF;
- the peer held that complete request before the injected write error;
- the injected `BrokenPipeError` occurred on the post-write boundary;
- the result was `PrivilegedStop.HANDED_OFF`; and
- no retry, second request, sleep-based ordering, thread leak, or socket leak
  was introduced.

Do not weaken the exact-request/surplus checks or replace the bounded event
ordering with eventual-state assertions. Retain the scripted
write/reply/close matrix and the other real-socket cases unchanged unless a
demonstrated regression requires a directly related adjustment.

## Preserved boundary

Do not change:

- `adapters/executor/interrupt.py` or any other production code;
- the ownership boundary, protocol, supervisor topology or transient units;
- readiness, installer, privilege-vector or environment decisions;
- OC-1/OC-2/OC-3, journal validation, cgroup identity, drain/removal or
  one-shot behavior;
- accepted Route 3 roles; or
- production/staging state.

If the narrow test correction cannot be made within this boundary, stop and
report the concrete blocker rather than expanding scope.

## Required verification

On the exact final tree, run at minimum:

1. the corrected write-error test and the exact-request reader plus all three
   real-socket cases repeatedly;
2. the complete focused executor set:
   `tests/test_executor_*.py` and
   `tests/systemd_integration/test_executor_*.py`;
3. `compileall` for the changed test; and
4. `git diff --check`.

The independently reproduced baseline is **511 passed, 5 documented host-only
skips** for the focused set. A test-only correction does not require the SA-2,
root/systemd package, bot, web or Foundry suites unless the final diff or an
observed failure reaches those behaviors.

Report reliable statuses and every failure, error, skip, retry, altered command
or infrastructure incident. If testing on `oracle-test`, use the canonical
secret-excluding synchronization procedure and leave no pytest or executor
residue.

## Handback

Append one concise **R6 socket-proof ordering remediation return** section to
`docs/review/route-3-executor-oc-implementation-handback.md` containing:

- the exact assertion correction;
- why the old timeout branch could pass without injecting the error;
- files changed;
- material commands and reliable results, including skips;
- cleanup and any incident; and
- confirmation that no production code, production/staging state, acceptance,
  commit or push was involved.

Stop after the handback for independent Codex re-review.
