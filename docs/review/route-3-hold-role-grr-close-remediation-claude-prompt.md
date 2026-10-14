# Claude remediation prompt — Route 3 GRR descriptor-close exception safety

Date: 2026-10-14
Authority: baseline v1.9, active handover and delivery plan, and the independent
Codex review of the Route 3 GRR exception-safety remediation
Mode: one bounded implementation and verification cycle on the disposable host;
no production or staging activation

## Assignment

Remediate the one remaining blocking Route 3 finding: descriptor cleanup can
still raise out of the concrete filesystem adapter after an otherwise handled
GRR operation. The existing remediation converts open, lookup, `fstat`, bounded
read/hash, extended-attribute and directory-listing failures, but its unguarded
`os.close()` calls can override the typed result. This contradicts the accepted
rule that GRR never raises and the adapter's statement that only
`before_unlink` may propagate.

Add regression tests that fail for the defect, implement the smallest safe
adapter-boundary correction, run the required checks on `oracle-test`, and
update the existing hold handback in place. Do not create another handback,
prompt, proof chain or contract reinterpretation. Do not commit or push.

Do not add a production caller, installer, `consume`, `attest`, static
`start`/`stop`, or any production/staging activation. Preserve unrelated
working-tree changes and all earlier `run-start`, `igr`, `run-end`, descriptor-
isolation, pre-journal K/S0 and GRR inspection-failure behavior.

## Read before editing

1. `.agents/AGENTS.md` in full.
2. `docs/implementation-plan.md`: reading map, §§0, 12 Phase 5.0, 13, 14, 16
   and 20.
3. `docs/review/Handover information`.
4. `docs/project-management/active-delivery-plan.md`.
5. `docs/operations/disposable-test-server.md`.
6. `docs/review/route-3-hold-role-implementation-claude-prompt.md`,
   `docs/review/route-3-hold-role-review-remediation-claude-prompt.md`,
   `docs/review/route-3-hold-role-grr-remediation-claude-prompt.md`, and the
   current-result section of
   `docs/review/route-3-hold-role-implementation-handback.md`.
7. From the operation inventory, `H-GR1.1` through `H-GR1.7`, `H-GRR.1`
   through `H-GRR.8`, `H-CL.G.1` through `H-CL.G.2`, and `RT2.IGR.1`
   through `RT2.IGR.4`.

Historical closure labels are not development gates. The accepted non-GAP
operation rows remain the behavior contract for this slice.

## Blocking finding

`adapters/rp11/fsops.py` still has unguarded descriptor closes on GRR-reachable
paths:

- `observe_at()` closes its target descriptor in a `finally` block;
- `LocalActivationFs.remove()` closes both the re-verification descriptor and
  its parent descriptor in `finally` blocks; and
- `read_root_file()` closes `grant.id` and its parent descriptor in `finally`
  blocks.

A deterministic probe made the target-descriptor `close` close the descriptor
and then raise `OSError(EIO)`. `LocalActivationFs.remove()` propagated the
exception and left the rule present. The same failure from inline IGR occurs
after `igr_state` becomes `running` but before it becomes `done`, recreating
the original missing-`igr`, missing-`run-end` and missing-explicit-K-release
failure. A parent-close exception can instead override an already selected
`absent`, `mismatch`, `unremovable` or `removed` result.

This also makes the current claims that `observe_at()` never raises `OSError`
and that only `before_unlink` may escape from `remove()` false. It contradicts
`H-GRR.5`, `H-GRR.8` and `RT2.IGR.2`.

## Required fix

Make descriptor cleanup on the GRR filesystem boundary best effort and
non-throwing without weakening attribution or removal authority.

Use a narrow adapter-local helper if useful. Its semantics must be explicit:

- call `os.close(fd)` at most once;
- catch only the close failure that cannot affect the already established
  filesystem verdict;
- never retry a failed close, because after `EINTR` or another reported error
  the descriptor's state may be unknown and its number could be reused; and
- never let a cleanup error override the typed result already selected by the
  operation.

Apply that behavior to every target and parent descriptor close reachable from
GRR-1 through GRR-4, including `observe_at()`, `remove()` and
`read_root_file()`. Audit the narrow neighboring helper paths in the same
module so that their docstrings remain true, but do not turn this into a broad
filesystem rewrite.

Preserve these boundaries:

- A close failure after a complete re-verification does not erase those facts
  or broaden removal authority. The existing attribution and removal decision
  continues unchanged.
- A close failure after a mismatch preserves the mismatch and leaves the
  object untouched.
- A parent close after `absent`, `mismatch`, `unremovable` or `removed`
  preserves that exact result. Never report `removed` unless unlink/rmdir
  actually succeeded.
- Successful `grant.id` inspection remains available to GRR-1 even if its
  read-only descriptor cleanup reports an error. An earlier inspection/read
  failure still returns `None`.
- Do not catch or translate exceptions raised by `before_unlink`. Its
  `EvidenceWriteError` must still enter the existing G-R1/GP-R3 path, and no
  unlink may occur when write-ahead evidence fails.
- Preserve `ENOENT` as `absent`, unlink errors as `unremovable {errno}`, ignored
  parent-directory flush errors, and all existing damaged/foreign outcomes.
- Do not add broad handlers to `_igr()` or `_cl_g()`. All GRR callers must get
  the same behavior from the concrete adapter.
- Keep GRR free of locks, spawns, signals, authorization calls, network work
  and ext4 evidence writes.

## Required regression tests

Extend the concrete fault injector to target descriptor close and parent-
descriptor close deterministically. Cover both realistic close-error shapes:
the injected operation may close and then report an error, or may report an
error while leaving the descriptor state unknown. Do not retry the same
descriptor number in either case.

At minimum prove:

1. A target close error after successful file re-verification does not escape,
   `before_unlink` is called exactly once, and the normal typed removal outcome
   is preserved.
2. A target close error after a damaged or otherwise mismatching observation
   preserves the selected mismatch, does not call `before_unlink`, and leaves
   the same inode present.
3. A parent close error preserves each representative terminal result:
   `absent`, `mismatch`, `unremovable`, and `removed`. The path state must agree
   with the result.
4. `observe_at()` does not raise when its target close reports an error and
   returns the same conservative observation it established beforehand.
5. `read_root_file()` does not raise for target- or parent-close errors: valid
   `grant.id` bytes remain available, while a separate inspection/read failure
   remains `identity-unavailable`.
6. Inline IGR reaches `done`, writes the exact `igr {outcome, identity}` and
   `run-end` lines where writable, and releases K in the already-selected order
   when target or parent close reports an error.
7. Stop-post CL-G reaches CL-0 through CL-7 and records its attempt rather than
   escaping before cleanup.
8. Backstop CL-G records its firing outcome and retains the existing
   retry/disarm rules rather than crashing.
9. A `before_unlink` `EvidenceWriteError` still propagates into GP-R3 and is not
   swallowed by the close handling.
10. Existing open/stat/fstat/read/hash/xattr/listing, absent, damaged, foreign,
    unlink-unremovable and parent-flush cases retain their current outcomes.

Use synthetic deterministic injection; do not require a damaged filesystem.
Mutation-test the fix by restoring the unguarded close at each corrected site,
show that the corresponding new tests fail, then revert every mutation and
confirm the final file is restored.

## Required verification

All test levels remain authorized on `oracle-test`; use only synthetic data.
Synchronize with the documented secret-excluding command and run, in order:

1. focused filesystem, hold, cleanup and backstop suites, plus the related
   artifact/unit-control suites already used by this slice;
2. the complete Route 3 root systemd integration suite with the pinned Jeepney
   wheel;
3. the complete bot suite;
4. the complete web suite with exported
   `TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'`, confirming the
   database-enabled skip count;
5. the complete Foundry Node suite;
6. `.claude/hooks/test_guards.py`;
7. `git diff --check`, `compileall`, and every configured formatter, linter or
   type checker, or explicitly state that none is configured.

Run bot and web serially with the documented PostgreSQL 16 `PATH` and
`/opt/freedom-blades/runtime/venv-web` interpreter. Ensure `/usr/sbin` is
available to the root integration suite because its operator test invokes
`runuser`. A targeted rerun may diagnose a failure but is not final regression
evidence. Compare exact failures, errors and skips with the established
baseline; do not weaken tests or repair unrelated baseline failures.

After root tests, verify that no holder/backstop unit, process, Polkit rule,
capture unit, Route 3 `/run` object, temporary artifact or new evidence remains
and that `polkit.service` is active. Remove only disposable test artifacts
created by this work.

## Acceptance criteria

- No target- or parent-descriptor close failure reachable through GRR escapes
  the concrete adapter or overrides its typed result.
- No close operation is retried after an error.
- IGR, stop-post CL-G and backstop CL-G retain their ordering and complete their
  required recovery behavior.
- No unreadable, partially observed, damaged, foreign or replaced object is
  removed, and no failed unlink is reported as removed.
- `before_unlink` evidence failures retain the existing G-R1/GP-R3 semantics.
- The existing GRR inspection-failure regression matrix remains green.
- Focused and real-PID-1 tests pass, and final-tree bot, web and Foundry suites
  introduce no regression relative to the accepted baseline.
- No production/staging state, real secret or player data is touched.

## Handback update

Update `docs/review/route-3-hold-role-implementation-handback.md` in place with
one new concise current-result section that supersedes the present acceptance
claim. Include the finding and disposition, principal files changed, exact
close-failure semantics and typed outcomes, named regression and mutation
tests, exact final-tree commands/results, real-host cleanup confirmation,
remaining production risks, and one recommendation: accept the complete role
series or remediate one named blocker. Do not create another handback.
