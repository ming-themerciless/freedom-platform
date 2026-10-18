# Claude remediation prompt — Route 3 `attest` review findings

Date: 2026-10-17
Authority: baseline v1.9, the active implementation-first delivery plan, and
the independent Codex review of the uncommitted RT-5 candidate
Mode: one bounded remediation and verification cycle on `oracle-test`; no
production or staging activation

## Assignment

Remediate the two blocking findings from the independent review of the
uncommitted RT-5 `attest` candidate:

1. a changed-boot attestation can publish `st1-verified` after required
   activation or `/run` evidence is missing or untrusted; and
2. the handback abbreviates required verification commands, so its evidence is
   not independently reproducible.

Add regressions that reproduce the false-success cases before fixing them,
make the smallest trigger-scoped fail-closed correction, rerun the required
checks on the final tree, and update the existing attest handback in place.

Do not return another plan or research package. Do not implement the non-root
executor, OC-1/OC-2/OC-3, a production capture-unit installer,
migration/cutover work, production or staging activation, or unrelated
cleanup. Preserve all unrelated working-tree changes. Do not commit or push.

The accepted manager/Polkit adapter, `consume`, `start`, `stop`, `hold`,
`stop-post` and `backstop` behavior is not reopened. In particular, do not
silently change accepted `stop-post` or `backstop` terminal semantics merely
because they use the shared cleanup engine. Keep the correction scoped to the
RT-5 contract while continuing to reuse `CleanupProcedure`; do not copy CL,
GRR, attribution, PK/2, publication or removal logic into the attest module.

## Read before editing

1. `.agents/AGENTS.md` in full.
2. `docs/implementation-plan.md`: reading map, §§0, 12 Phase 5.0, 13, 14, 16
   and 20.
3. `docs/review/Handover information`.
4. `docs/project-management/active-delivery-plan.md`.
5. `docs/operations/disposable-test-server.md`.
6. `docs/review/route-3-attest-role-implementation-claude-prompt.md` and
   `docs/review/route-3-attest-role-implementation-handback.md`.
7. The operation inventory §§3 RT-5, 4, 5.5, 6 RT-5, 7, 8.1 and 10, plus the
   RT-5 rows and reconciliation tables in §§11–12, especially CL-1, CL-4,
   CL-6, CL-7 and the `cleared-by-boot` conditions.
8. The interface contract §§3.0, 3.1, 3.5 and 3.6.
9. `application/rp11/cleanup.py`, `application/rp11/attest.py`,
   `adapters/rp11/attest.py`, the current RT-5 tests and the complete current
   diff from accepted commit `94fb3e7`.

Historical WP closure labels are not current development gates. Their accepted
RT-5, H-FI, H-CL, H-GRR, H-PK2, H-SN and DI-1/DI-5/DI-6 requirements remain
implementation inputs.

## Blocking finding 1 — missing boot evidence can become success

The candidate records `invalid-journal` when ACT evidence is absent or invalid,
but `CleanupProcedure._verified()` does not consider that failure. Its ordinary
allowed classes include `never-linked` and `absent-before-removal`. RT-5 can
therefore satisfy PK/2 and the baseline checks, publish `st1-verified`, and exit
0 even though it cannot prove the required old-boot identity or trusted tmpfs
clearance.

The submitted evidence confirms both defects:

- the real-reboot missing-identity case permits return code 0 and reports
  `never-linked`; and
- the injected non-tmpfs case reports `absent-before-removal` but does not
  require a hard stop.

This is not an ambiguity. The implementation assignment explicitly requires a
changed-boot case with missing identity, a wrong filesystem fact, or a failed
PK/2/ST-1 check to claim neither `cleared-by-boot` nor `st1-verified`.

Make RT-5 fail closed so that:

- missing, unreadable, malformed, incomplete, digest-mismatched or otherwise
  invalid ACT evidence cannot contribute to `st1-verified`;
- an `invalid-journal` failure cannot coexist with an RT-5
  `st1-verified` terminal, record or exit 0;
- after a boot change, absence of an activation-owned `/run` object contributes
  to RT-5 success only when the existing `cleared-by-boot` proof is complete:
  the boot IDs differ, `/run` is observed as `tmpfs`, the valid old identity is
  present and the current lookup is `ENOENT`;
- after a boot change, `never-linked` or `absent-before-removal` must not stand
  in for that proof for an activation-owned object whose safe disposition is
  needed for ST-1;
- a missing mount fact, a non-`tmpfs` fact, or a missing required identity
  produces a durable non-success result with a consistent closed failure token;
- positive PK/2 `not-authorized` and a matching baseline remain necessary but
  are not sufficient to repair missing attribution evidence; and
- no new path removes an A0, damaged, foreign, uninspected, unprovable or
  unremovable object.

Preserve legitimate evidence already accepted by the cleanup contract, such
as a durable prior removal, where it proves the object's disposition without
claiming boot clearance. Preserve the existing same-boot behavior when its
ACT evidence and attribution are valid. Do not turn pathname absence, authority
data alone, a newly manufactured record, or the current boot ID alone into
proof of earlier identity.

Prefer an explicit RT-5 success-eligibility rule inside the shared cleanup
engine or an equally small trigger-aware policy. Do not add a second cleanup
implementation, rerun PK/2, add another manager mutation, or weaken the closed
record/journal grammars. Existing `stop-post` and `backstop` behavior and tests
must remain unchanged unless a demonstrated regression requires a separate
maintainer decision.

Add regressions that require non-zero `hard-stop`, `st1.verified == false`, no
`st1-verified` journal/record claim and the expected durable failure for at
least:

1. the changed-boot activation with its ACT journal/evidence directory missing;
2. an invalid or incomplete old ACT journal that lacks the required identity;
3. a changed-boot absence with `/run` reported as a non-`tmpfs` filesystem;
4. a changed-boot absence with the `/run` mount fact unavailable;
5. the corresponding cases with otherwise positive PK/2 and baseline checks,
   proving those checks cannot override the evidence failure; and
6. the real-reboot C case through the installed exact `sudo -n` vector.

Retain positive controls for same-boot success with valid evidence and
changed-boot `cleared-by-boot` success with valid identities, observed tmpfs,
real PK/2 non-authorization and the pinned baseline. Retain the planted-path
hard-stop and all accepted cleanup regressions.

## Blocking finding 2 — verification commands are not reproducible

The handback replaces material parts of the focused, host, reboot, bot and web
commands with `…`, and describes other checks without the exact shell
invocation. Counts alone do not meet the assignment's evidence requirement.

Replace every abbreviated command in the existing handback with the exact
copy-pastable command actually run on the final tree. For every check record:

- the host and working directory;
- the complete executable and arguments;
- every material environment variable and wrapper, including the
  signal-resetting wrapper used for pytest;
- each reboot phase and the reboot command in execution order;
- the exit status and pass/fail/error/skip counts;
- every skip reason; and
- the exact baseline-comparison command where a failure is called pre-existing.

Do not reconstruct a plausible command after the fact and present it as one
that was run. If an original command is unavailable, rerun the check with an
exact recorded command on the final tree. Do not retain `…`, `<command>`, a
suite name standing in for a command, or another non-executable placeholder in
the final verification section. Long commands may use fenced shell blocks and
line continuations.

## Required verification

All test levels remain authorized on `oracle-test`. Use synthetic data and the
documented secret-excluding synchronization command. Do not touch production,
staging, real secrets or player data. Re-sync the final tree before the final
runs.

Run on the final tree, at minimum:

1. the new regressions plus `tests/test_rp11_attest.py`,
   `tests/test_rp11_consume.py`, `tests/test_rp11_h1_artifact.py`,
   `tests/test_rp11_hold.py`, `tests/test_rp11_cleanup.py`,
   `tests/test_rp11_backstop.py`, `tests/test_rp11_records.py`,
   `tests/test_rp11_pk_sn.py`, `tests/test_rp11_start.py`,
   `tests/test_rp11_stop.py` and `tests/test_systemd_unit_control.py`;
2. `tests/systemd_integration/test_route3_attest_host.py` as root with a fresh
   controlled artifact built from the pinned Jeepney wheel;
3. the explicit three-phase real-reboot attestation proof again, requiring the
   missing-evidence C case to hard-stop and the valid-evidence A case to reach
   `st1-verified`, followed by separate cleanup verification;
4. the complete `tests/systemd_integration` suite serially;
5. `tests/web/test_p3_4_static_assets.py`, reporting established unrelated
   baseline failures rather than hiding or repairing them;
6. the documented bot and web suites serially with
   `TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'`, confirming that the
   web skip count remains 80 rather than a false-green database-skipped count;
7. the Foundry Node suite;
8. Python compilation over every touched Python path, the repository guard
   tests and any configured static checks; and
9. `git diff --check`, together with direct coverage of the still-untracked new
   files rather than assuming the command inspected files absent from Git's
   diff.

Record exact copy-pastable commands, working directories, exit statuses and
all result counts and skip reasons. Do not cite pre-remediation figures as
final-tree evidence. Do not call a failure pre-existing unless it is freshly
reproduced against accepted commit `94fb3e7` or supported by an applicable
recorded baseline with the exact failing identifiers compared. Never run bot
and web suites in parallel because they share the disposable database.

After the root and reboot tests, verify cleanup in a separate command: no
RP-11 unit, process, Polkit rule, artifact, staging/store path, test unit,
proof-state file, new `/var/tmp/rp11-act-*` path, attempt evidence or test log
may remain; `polkit.service` must be active; `/var/tmp` must remain
`root:root 1777`; and the six pre-existing
`/var/tmp/p5-r5-rp11-h0*` directories must be unchanged.

## Acceptance criteria

- RT-5 cannot publish `st1-verified` or exit 0 with invalid/missing ACT
  evidence, a missing required old identity, a non-tmpfs `/run` fact or no
  mount fact.
- Changed-boot success still requires the complete existing
  `cleared-by-boot`, CL-4 and CL-6 proof; positive authorization/baseline checks
  cannot substitute for attribution evidence.
- The real-reboot valid-evidence case succeeds and the missing-evidence case
  hard-stops through the exact installed `sudo -n` vector.
- Same-boot valid-evidence cleanup, precondition refusal, grant priority,
  interruption, record publication and stable exit/diagnostic behavior remain
  intact.
- Accepted `stop-post`, `backstop`, `hold`, `consume`, `start` and `stop`
  behavior remains unchanged.
- The handback contains the exact commands actually run and no command
  placeholders.
- The disposable host is clean and production/staging remain unchanged.

## Handback and current-state update

Append one concise review-remediation section to
`docs/review/route-3-attest-role-implementation-handback.md`; do not create a
new handback. Correct or supersede the existing observations and
recommendation. Include:

- both review findings and their exact dispositions;
- the trigger-scoped success rule and why accepted role behavior is unchanged;
- the missing-identity, non-tmpfs and missing-mount regression outcomes;
- the repeated real-reboot A/B/C outcomes;
- principal files changed;
- exact final-tree commands and results, including failures and skips;
- host cleanup state;
- unchanged remaining production risks; and
- one recommendation: accept RT-5 for continued non-production development or
  remediate one specifically named remaining blocker.

Update the concise current-state documents only enough to say that this
remediation was returned for independent Codex re-review. Do not record
Peter's acceptance, assign the non-root executor or OC checks, or authorize
production/staging. Return the complete uncommitted candidate for independent
Codex re-review.
