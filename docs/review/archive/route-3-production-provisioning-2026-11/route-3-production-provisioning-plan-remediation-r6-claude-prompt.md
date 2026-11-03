# Claude prompt — Route 3 production provisioning-plan remediation R6

Date prepared: 2026-11-02  
Owner and acceptance authority: Peter Duscha  
Implementer: Claude  
Reviewer after return: Codex  
Target: the uncommitted Route 3 production provisioning-plan R5 candidate currently in the workspace

## Assignment

Complete one narrow correction of the Route 3 production provisioning-plan R5
return. Do not redesign the provisioning plan and do not restore automatic
package or hold rollback.

Codex's independent review found that R5's central safety correction is
materially sound: R no longer removes, purges, autoremoves, downgrades or
unholds packages, and a package/hold difference is preserved for attended
recovery. The return is nevertheless not review-ready because:

1. the canonical handback still identifies R4 as latest and contains no R5
   return, while the live records claim R5 was returned;
2. the submitted provisioning-plan module is red because its new structural
   test mistakenly treats S1.1's authorized `apt-mark hold` as prohibited
   rollback;
3. R's final wrapper describes every non-zero result as status 28 package/hold
   recovery, including statuses 20–27; and
4. the available full-run result was contaminated by overlapping
   provisioning-plan and apt tests, so it is not acceptance evidence.

Correct those defects, produce one uncontaminated final verification, complete
cleanup and write the missing canonical return. The candidate remains
**NO-GO**. Provisioning, installation and activation remain unauthorized.
This prompt authorizes repository remediation and full relevant testing on
`oracle-test`; it authorizes no production or staging access or mutation.

## Governing material

Before acting, read completely:

1. `.agents/AGENTS.md`;
2. `docs/implementation-plan.md` using its reading map, especially §0, §13,
   §14, §16, §17 and §20;
3. `docs/review/Handover information`;
4. `docs/operations/disposable-test-server.md`;
5. `docs/project-management/active-delivery-plan.md`;
6. `docs/operations/executor-supervisor-provisioning-runbook.md`, especially
   part P block D, S1.1, R and the rollback matrix;
7. `docs/review/route-3-production-readiness-handback.md`, especially the R4
   return; and
8. `docs/review/route-3-production-provisioning-plan-remediation-r5-claude-prompt.md`.

The selected deployment remains `/opt/freedom-route3/{code,venv}`. The live
`freedom-bot`, `freedom-web` and `freedom-worker` paths and services remain
untouched.

## Authority and hard boundary

Peter's act of giving this prompt to Claude authorizes:

- the focused repository documentation and test changes required below; and
- full relevant testing on `oracle-test`, including root-owned fixture package
  transactions, interruption/failure injection and cleanup testing.

It authorizes **no production or staging access of any kind and no production
or staging mutation**. Do not inspect production again. Do not create, inspect,
edit or remove a production grant; install or remove a production package;
create a production account, deployment, artifact, policy or unit; reload,
enable, start, stop or restart a production service; reboot production; run
Route 3; or perform a migration, cutover or RB-1 outside `oracle-test`.

Do not read secrets, credentials, `.env`, process environments or arguments,
or player data. If a guard refuses a command, stop rather than routing around
it.

## Preserve the accepted R5 safety direction

These requirements are fixed:

- R must never remove, purge, autoremove, downgrade, hold or unhold a package.
- `apt.txn` and `apt.effects` are diagnostic observations only. They never
  establish package ownership.
- At C1, exact equality with the recorded package and hold pre-state permits
  status 0.
- Any package or hold difference is preserved and reported, all evidence is
  retained, and R returns status 28 for attended recovery.
- Later S1 objects are undone first where their existing controls permit.
- Peter decides whether and how any package may be removed.
- Production, staging, provisioning, installation and activation remain
  unauthorized.
- Every production release field remains `UNSET`; the plan remains NO-GO.

Do not weaken S1.1's reviewed closure, exact-version, origin, interpreter
digest, `dpkg --verify`, artifact or hold checks. Do not weaken R's object,
identity, manager, path, mount, reverse-order or evidence-integrity controls.

## Required correction 1 — repair the R5 structural test

Correct
`test_r5_no_s1_rollback_path_contains_a_package_removal_purge_autoremove_downgrade_or_unhold`
in `tests/test_provisioning_plan.py`.

Its final assertion currently scans every block, including S1.1, using
`PACKAGE_REMOVAL`. The pattern's `(un)?hold` alternative also recognizes
S1.1's authorized `apt-mark hold`. That contradicts the test's immediately
preceding explicit S1.1 exception.

The corrected coverage must prove all of the following:

- R0 and R contain no package removal, purge, autoremove, downgrade, hold or
  unhold operation;
- no recovery or rollback path contains any such operation;
- no block other than S1.1 performs `apt-mark hold`;
- S1.1 retains only its authorized install and hold mutations;
- block D contains no prohibited rollback mutation; and
- deliberately reintroducing removal, purge, autoremove, downgrade or unhold
  behavior is detected by executable or mutation coverage.

Do not delete the test, reduce it to string-presence evidence or broadly weaken
the prohibition.

## Required correction 2 — make R's final message status-accurate

The wrapper after block R currently labels every non-zero return as:

`status 28: packages or holds need ATTENDED recovery`

That statement is false for statuses 20–27. Change the wrapper so that:

- rc 0 reports that the pre-state was restored;
- rc 28 specifically reports that package or hold differences require attended
  recovery;
- every other non-zero rc reports its actual status and directs escalation
  without describing it as status 28; and
- the original return status is preserved exactly.

Add focused executable tests for rc 0, rc 28 and at least one representative
non-28 failure. Prove that a non-28 result does not print the status-28
explanation. Do not change the existing meanings of statuses 20–28.

## Required correction 3 — uncontaminated serial verification

Use only the disposable `oracle-test` server for privileged and package-manager
testing. Synchronize the exact workspace with the canonical secret-excluding
procedure.

Before starting:

- confirm that no other provisioning-plan pytest process is running;
- confirm that no apt or dpkg transaction is running;
- do not begin while another agent or verification script is using the shared
  fixture paths or package manager; and
- inspect stale fixtures and remove only artifacts certainly attributable to
  these tests and safe to remove under the disposable-server procedure.

Run package-manager and provisioning-plan tests serially. Do not overlap root,
real-apt or provisioning-plan runs. If another run appears, stop and wait or
return the conflict; do not produce knowingly contaminated evidence.

After the final executable or test change, run at minimum:

1. the complete `tests/test_provisioning_plan.py` as root;
2. the focused R5/R6 tests;
3. `tests/test_production_checklist_item_8.py` as root;
4. `tests/test_production_checklist_item_5b.py`,
   `tests/test_executor_supervisor_install.py` and
   `tests/test_executor_system_service.py`;
5. directly affected structural and deployment-artifact tests;
6. `bash -n` over block D and every executable runbook/checklist block added
   or changed;
7. `.claude/hooks/test_guards.py`; and
8. `git diff --check`.

Use the documented Python environment and required test-database
configuration. Record exact commands, counts, failures, errors, skips and
elapsed times. Report authoring or environmental failures honestly.

A failed complete run followed only by selected passing reruns is not final
evidence. After the last change, the complete provisioning-plan module must
pass from start to finish in one uncontaminated run.

## Required correction 4 — cleanup

After all tests finish, verify and report:

- `dpkg --audit` is clean;
- no fixture package or package hold remains;
- no test apt hook or apt configuration drop-in remains;
- no relevant apt, dpkg or pytest process remains;
- no attributable `frt-plan-*`, `frt-r5-*` or `frt-r6-*` path remains;
- no attributable `/opt/freedom-route3*` or `/root/route3-*` fixture remains;
- no attributable pytest temporary directory remains; and
- no fixture account, group, linger file, sudoers fragment, unit, tmpfiles
  fragment, state/runtime path, mount or artifact remains.

Do not remove unrelated or uncertain artifacts. Identify anything retained and
explain why.

## Required correction 5 — canonical return and live records

Add one concise **Production provisioning-plan remediation R6 return —
2026-11-02** above the R4 return in
`docs/review/route-3-production-readiness-handback.md`. Preserve the historical
R1–R4 returns. State:

- the assignment and implementer;
- the independent-review findings addressed;
- every file and behavior changed;
- that automatic S1.1 package removal and unholding remain absent;
- the exact status-28 attended boundary and what R can still undo safely;
- focused and complete disposable-host commands and results, including every
  failure, error and skip;
- the disposition of the earlier contaminated run;
- final `oracle-test` cleanup evidence;
- confirmation that no production or staging access occurred;
- that release fields remain `UNSET` and the plan remains NO-GO;
- that provisioning, installation and activation remain unauthorized; and
- one recommendation: ready or not ready for independent Codex re-review.

Do not claim a successful return before the final complete serial run and
cleanup finish.

After the canonical return is complete, reconcile:

- `docs/review/Handover information`;
- `docs/project-management/status.md`;
- `docs/project-management/change-log.md`;
- `docs/review/README.md`; and
- other live current-authority records already changed for the R5 return where
  needed to remove a direct contradiction.

The records must identify R6 as returned for independent review and preserve
the NO-GO and authorization boundary. Do not describe R5 as successfully
verified: its safety direction is retained, but its return package was
incomplete and its submitted suite was red.

## Scope discipline

Expected files are limited to:

- `docs/operations/executor-supervisor-provisioning-runbook.md`;
- `tests/test_provisioning_plan.py`;
- `docs/review/route-3-production-readiness-handback.md`;
- `docs/review/Handover information`;
- `docs/project-management/status.md`;
- `docs/project-management/change-log.md`;
- `docs/review/README.md`; and
- other already-modified live records only where required to reconcile a
  direct R5/R6 current-state contradiction.

Do not change application or bot code, the installer implementation, executor
supervisor implementation, service units, SA-2, Polkit or sudoers policy, the
account model, migrations or schemas, credentials or environment
configuration, release artifacts or release fields.

If any excluded file appears necessary, stop and return the conflict rather
than expanding scope. Do not provision, install, activate, commit or push
unless separately and explicitly authorized.

Return the completed R6 package for independent Codex re-review. Do not claim
acceptance, finding closure or provisioning authorization. Stop after the
return.
