# Claude prompt — executor OC R6 non-blocking socket-proof hardening

Status: **ACCEPTED AND AUTHORIZED NON-BLOCKING FOLLOW-UP**

Authority: Peter Duscha, Product Owner and Acceptance Authority

Implementer: Claude

Independent reviewer after return: Codex

Date: 2026-10-21

## Assignment

Correct one narrow test-helper overclaim in the returned Route 3 executor OC R6
candidate. Independent Codex re-review found no implementation or production-
safety defect and recommends acceptance of the candidate. Peter classifies the
remaining observation as non-blocking: `read_exact_request()` proves that the
complete fixed request arrived before `crossed`, but does not deterministically
reject a surplus byte when a legal stream `recv()` returns exactly the requested
length and leaves the surplus queued.

This is test-proof hardening only. It is not a condition of candidate acceptance,
does not reopen the R6 implementation, and authorizes no production or staging
installation or activation and no successor slice.

## Required correction

Update only the relevant real-socket test helper and tests in
`tests/test_executor_supervisor.py`, plus the existing cumulative executor
handback. Do not change `adapters/executor/interrupt.py` or production code.

Use deterministic test-side stream framing. The recommended small correction is:

1. after the test client's real `sendall(PROTOCOL_REQUEST)` completes, half-close
   its write side with `shutdown(socket.SHUT_WR)` before releasing or reporting
   the injected interruption;
2. make the peer helper read, within its existing bound, until EOF while retaining
   no more than `len(PROTOCOL_REQUEST) + 1` bytes;
3. accept only exact `PROTOCOL_REQUEST` followed by EOF, and reject short input,
   wrong input, surplus and timeout;
4. retain the event ordering, one connection, one request, no retry, reliable
   close/join cleanup and absence of sleeps as race evidence; and
5. retain the scripted write/reply/close matrix and definite pre-write tests.

A different equally small deterministic framing is acceptable if it proves both
the complete request and absence of surplus without relying on one `recv`, timing,
or an unbounded wait. Explain any test-only half-close explicitly; it must not be
represented as production client behavior.

Add a regression in which the receiver obtains the exact request and a surplus in
separate reads. It must fail before the helper correction and pass afterward.

## Preserved boundary

Do not reopen the ownership boundary, supervisor topology, user-manager transient
units, readiness, installer verification, privilege vector, environment decision,
OC checks, accepted Route 3 roles, or any production/staging state. Preserve the
shared dirty worktree and use no real secret or player data.

## Verification and handback

On the exact final tree, run:

- the corrected reader and three real-socket cases repeatedly;
- the complete focused executor set (current baseline: **510 passed**);
- `compileall`; and
- `git diff --check`.

Use the canonical secret-excluding synchronization procedure if testing on
`oracle-test`. Report reliable statuses, failures, skips, retries and cleanup.
Append one concise **R6 non-blocking socket-proof hardening return** section to
`docs/review/route-3-executor-oc-implementation-handback.md`. Do not create
another handback. Stop after the return for independent review.
