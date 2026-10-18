# Claude remediation prompt — Route 3 `attest` second review findings

Date: 2026-10-17
Authority: baseline v1.9, the active implementation-first delivery plan, and
the independent Codex re-review of the remediated uncommitted RT-5 candidate
Mode: one bounded remediation and verification cycle on `oracle-test`; no
production or staging activation

## Assignment

Remediate the two blockers found by independent re-review of the RT-5
`attest` candidate:

1. changed-boot attestation can still publish `st1-verified` when an
   activation-owned directory lacks its required old identity; and
2. the handback's final verification section still contains command
   placeholders and prose summaries instead of every exact command actually
   run.

Add a regression that is red before the code correction, make the smallest
RT-5-scoped fail-closed change, rerun the required checks on the final tree,
and update the existing attest handback in place. Do not create another
handback, review document, research package or remediation prompt.

Do not implement the non-root executor, OC-1/OC-2/OC-3, a production
capture-unit installer, migration/cutover work, or production/staging
activation. Preserve unrelated working-tree changes. Do not commit or push.

The accepted manager/Polkit adapter, `consume`, `start`, `stop`, `hold`,
`stop-post` and `backstop` behavior is not reopened. Continue to reuse
`CleanupProcedure`; do not copy cleanup, attribution, PK/2, publication or
removal logic into the attest module. A correction in shared code must be
trigger-scoped so accepted role semantics remain unchanged.

## Read before editing

1. `.agents/AGENTS.md` in full.
2. `docs/implementation-plan.md`: reading map, §§0, 12 Phase 5.0, 13, 14, 16
   and 20.
3. `docs/review/Handover information`.
4. `docs/project-management/active-delivery-plan.md`.
5. `docs/operations/disposable-test-server.md`.
6. `docs/review/route-3-attest-role-implementation-claude-prompt.md`,
   `docs/review/route-3-attest-role-review-remediation-claude-prompt.md` and
   `docs/review/route-3-attest-role-implementation-handback.md`.
7. The operation inventory §§3 RT-5, 4, 5.5, 6 RT-5, 7, 8.1 and 10, plus
   the RT-5 rows and reconciliation tables in §§11–12, especially CL-1,
   CL-4, CL-6, CL-7 and `cleared-by-boot`.
8. The interface contract §§3.0, 3.1, 3.5 and 3.6.
9. `application/rp11/cleanup.py`, `application/rp11/evidence.py`, the current
   RT-5 tests, the reboot host test, and the complete current diff from
   accepted commit `94fb3e7`.

Historical WP closure labels are not current development gates. Their
accepted RT-5, H-CL, H-GRR, H-PK2, H-SN and DI-1/DI-5/DI-6 requirements remain
implementation inputs.

## Blocking finding 1 — missing directory identity still becomes success

The first remediation rejects `never-linked` and `absent-before-removal` in
`CleanupProcedure._attest_eligible()`. Directory cleanup, however, rewrites
`never-linked` to `never-created`:

```python
klass = self._absent_class(path, identity)
klass = "never-created" if klass == "never-linked" else klass
```

`never-created` is in `DIR_OK` and is not in the new weak-class set. A linked
activation-owned tree can therefore lack its old directory identity after a
boot change while RT-5 still exits 0.

Independent re-review reproduced this on the synchronized final tree:

1. create the normal valid synthetic activation;
2. remove the `tree-p` top-directory `dir-identity` line while retaining the
   later pass configuration, rule and `grant.id` identities;
3. rebuild the journal with `serialize_line`, contiguous sequence numbers and
   the correct `prev` digest chain, so it remains canonically and structurally
   valid;
4. clear the activation's `/run` objects and change the boot ID; and
5. run RT-5 with positive PK/2 and matching baseline results.

The observed result was exit 0, terminal `st1-verified`,
`st1.verified == true`, and directory class `tree-p=never-created`; the rule,
pass configuration, `grant.id` and lock directory were `cleared-by-boot`.

This violates the required rule: after a boot change, every final
activation-owned `/run` object needed for ST-1 must have either the complete
existing `cleared-by-boot` proof (different boot IDs, observed `tmpfs`, valid
old identity and current `ENOENT`) or a durable prior removal. A linked tree's
missing member identity is not proof that the member was never created.

Make RT-5 fail closed so that:

- a linked activation-owned tree cannot contribute to changed-boot success
  when any required directory identity from its declared member inventory is
  missing;
- `never-created` does not stand in for old identity and boot clearance for a
  linked activation-owned final directory;
- the rule applies to `tree-p`, an activation-created `tree-r` and the lock
  directory wherever the ACT evidence says those objects belonged to the
  activation;
- a genuinely pre-existing rules directory may remain `pre-existing-kept`
  under the accepted cleanup contract;
- a durable prior `removed` fact may remain sufficient for that exact path;
- missing identity, positive PK/2 and an equal baseline cannot combine into
  success;
- no A0, damaged, foreign, uninspected, unprovable or unremovable object is
  removed; and
- same-boot valid cleanup and the accepted `stop-post` and `backstop`
  semantics remain unchanged.

Do not fix this by merely adding every `never-created` directory to a global
failure set. The decision must distinguish an activation-owned linked final
directory from a genuinely absent or pre-existing path using the ACT tree
intent/link evidence and prior durable removals. Keep the policy explicit and
testable.

Add regressions for at least:

1. the exact changed-boot `tree-p` case above, requiring exit 1,
   `hard-stop`, `st1.verified == false`, no `st1-verified` journal/record
   claim, and a consistent closed failure token;
2. a linked activation-created `tree-r` with a required directory identity
   omitted, including its nested `rules.d` member when declared;
3. the same cases with otherwise positive PK/2 and equal baseline checks;
4. a positive changed-boot activation in which every required identity is
   present and each disappeared object is `cleared-by-boot`;
5. a genuine pre-existing rules directory that remains permitted; and
6. unchanged same-boot, `stop-post` and `backstop` positive controls.

Use production journal parsing/serialization in the regression rather than a
mock that bypasses the relevant evidence derivation. Demonstrate that the new
regression fails against the pre-fix candidate before applying the correction.

## Blocking finding 2 — final commands remain non-reproducible

The first remediation required exact copy-pastable commands and prohibited
`...`, `…`, `<phase>`, `<command>`, `<file>` and suite names standing in for a
command. The handback still contains:

- `FREEDOM_ATTEST_REBOOT_PHASE=<phase>` instead of three literal phase
  commands;
- `<other phase>` in the reported skip reason;
- a prose description rather than the exact command that created and invoked
  the signal-resetting wrapper;
- a prose compilation claim without its exact command and explicit file list;
- `git diff --check --no-index /dev/null <file>` instead of the actual commands
  or an exact reproducible loop/list; and
- a cleanup-state claim without the separate exact inspection command.

Replace the final verification section with commands actually rerun on the
final tree. Record, literally and separately:

1. the synchronization command;
2. the focused pytest command;
3. the root host-module command;
4. the `prepare` reboot-phase command with
   `FREEDOM_ATTEST_REBOOT_PHASE=prepare`;
5. the exact `ssh oracle-test` reboot command and the exact readiness/wait
   command used afterward;
6. the `verify` command with the literal value `verify`;
7. the `cleanup` command with the literal value `cleanup`;
8. the complete systemd-integration command;
9. the static-assets command and exact accepted-baseline comparison command;
10. the exact wrapper creation/content command, bot command and web command,
    run serially with the documented database environment;
11. the Foundry command;
12. the exact compilation command with every path it checks;
13. the guard command and any configured static-check commands;
14. `git diff --check` plus exact coverage of every untracked file; and
15. the separate exact host-cleanliness inspection command.

For every check give its host, working directory, exit status, pass/fail/error/
skip counts and every skip reason. If an earlier exact command was not
retained, rerun the check and record the command used; do not reconstruct one
and call it historical evidence. Shell variables are acceptable only when the
same fenced block defines them to literal values and performs every invocation
copy-pastably. No placeholder may remain in the final verification section.

## Required verification

All test levels remain authorized on `oracle-test`. Use synthetic data and the
documented secret-excluding synchronization command. Re-sync after the last
change and run, on that final tree:

1. the new directory-identity regressions and the complete
   `tests/test_rp11_attest.py` module;
2. the focused RT-5/cleanup/consume/artifact/hold/backstop/records/PK/start/
   stop/unit-control set named in the first remediation prompt;
3. `tests/systemd_integration/test_route3_attest_host.py` as root with a fresh
   controlled artifact;
4. the literal three-phase real-reboot proof, retaining valid-evidence A,
   planted-path B and missing-evidence C;
5. the complete `tests/systemd_integration` suite serially;
6. `tests/web/test_p3_4_static_assets.py`, with any claimed baseline failure
   freshly reproduced against accepted commit `94fb3e7`;
7. the documented bot and web suites serially with
   `TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'`, confirming the web
   skip count is 80;
8. the Foundry Node suite;
9. Python compilation over every touched Python path, repository guard tests,
   configured static checks and `git diff --check`, including untracked files;
   and
10. separate post-root-test and post-reboot host-cleanliness inspection.

Do not call a failure pre-existing without an exact final-tree/baseline
comparison. Do not run the bot and web suites in parallel. Do not touch
production, staging, real secrets or player data.

## Acceptance criteria

- RT-5 cannot publish `st1-verified` or exit 0 after a boot change when a
  linked activation-owned final directory lacks its required old identity.
- `never-created` cannot substitute for `cleared-by-boot` or a durable prior
  removal for such a directory.
- Complete changed-boot evidence still succeeds through real PK/2 and baseline
  checks; genuine pre-existing directory handling remains intact.
- Same-boot RT-5 behavior and accepted `stop-post`, `backstop`, `hold`,
  `consume`, `start` and `stop` behavior are unchanged.
- The handback's final verification section contains only exact commands
  actually run, with no executable placeholder or prose substitute.
- The disposable host is clean and production/staging remain untouched.

## Handback

Append one concise **Second review remediation** section to
`docs/review/route-3-attest-role-implementation-handback.md`. It must include:

- both findings and their dispositions;
- the trigger-scoped directory-evidence rule;
- the red-before/fixed-after regression outcome;
- the repeated real-reboot A/B/C outcomes;
- principal files changed;
- the exact final-tree commands and results required above;
- the separate host-cleanliness result;
- unchanged remaining production risks; and
- one recommendation: accept RT-5 for continued non-production development,
  or remediate one specifically named remaining blocker.

Do not record Peter's acceptance, assign the non-root executor or OC checks, or
authorize production/staging. Return the complete uncommitted candidate for
independent Codex re-review.
