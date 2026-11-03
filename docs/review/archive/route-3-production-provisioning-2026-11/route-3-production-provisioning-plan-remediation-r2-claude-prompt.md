# Claude prompt — Route 3 production provisioning-plan remediation R2

Date prepared: 2026-11-01  
Owner and acceptance authority: Peter Duscha  
Implementer: Claude  
Reviewer after return: Codex  
Target: the uncommitted Route 3 provisioning-plan candidate currently in the
workspace

## Assignment

Remediate the four findings from Codex's independent review of the Route 3
production provisioning-plan R1 return. Produce one rollback-complete,
fail-closed plan that can be independently re-reviewed before Peter decides
whether to authorize provisioning.

The R1 focused suite passed **133/133** on the exact synchronized
`oracle-test` tree, but that result does not close the findings below. Codex
directly reproduced two omitted failure paths:

1. after S1.1, adding an unrelated package and then running R caused R to
   remove that package together with the Route 3 packages and return 0; and
2. failure during S1.0 after creating the evidence directory left R returning
   20 and left S1.0 unable to be rerun.

The candidate remains **NO-GO**. Provisioning, installation and activation are
unauthorized. This prompt authorizes repository remediation and full relevant
testing on `oracle-test`; it authorizes no production or staging access or
mutation.

Correct exactly these findings:

1. **Rollback removes packages that the Route 3 operation did not install.**
   R currently diffs the package set at rollback time against the S1.0
   pre-state and removes every intervening addition. A package installed by
   another attended action after S1.0 is therefore deleted even though it is
   not owned by this operation.
2. **The controlled Python package set is not closed.**
   `route3_fields_ok` requires only `python3.14-minimal` and
   `python3.14-venv`; `apt-get` may resolve additional dependencies that are
   neither pinned nor origin-checked, and `route3_python_ok` verifies only the
   names listed in `ROUTE3_APT_PACKAGES`. The existing fake-world happy path
   demonstrates the gap by adding an unpinned `libfake-dep` while the plan
   passes.
3. **Rollback account verification fails open on identity-query errors.**
   R treats every non-zero `getent` result as absence, although the preflight
   correctly distinguishes the absent status from a failed query. R can
   therefore report that the pre-state is restored without proving the
   account and group are absent.
4. **S1.0 has no rollback-complete partial-failure path.**
   A failure after the evidence directory is created but before its pre-state
   is complete leaves an evidence directory that prevents another S1.0, while
   R refuses because it has no complete pre-state. The plan's “rollback for
   every checkpoint” claim is therefore false.

This is a bounded plan remediation. Do not redesign the executor, supervisor,
installer, service unit, SA-2 behavior, Polkit policy, sudo vector, account
model, transient-risk decision, activation procedure, coordinator,
start orchestration, migration/cutover or RB-1.

## Governing material

Before acting, read completely:

1. `.agents/AGENTS.md`;
2. `docs/implementation-plan.md` using its reading map, especially §0, §13,
   §14, §16, §17 and §20;
3. `docs/review/Handover information`;
4. `docs/operations/disposable-test-server.md`;
5. `docs/project-management/active-delivery-plan.md`;
6. `docs/operations/executor-supervisor-provisioning-runbook.md`, especially
   part P;
7. `docs/review/route-3-production-readiness-handback.md`, especially the
   Production provisioning-plan remediation R1 return;
8. `docs/review/route-3-production-provisioning-plan-remediation-r1-claude-prompt.md`;
   and
9. the four review findings above.

The selected deployment remains `/opt/freedom-route3/{code,venv}`. The live
`freedom-bot`, `freedom-web` and `freedom-worker` paths and services remain
untouched.

## Authority and hard boundary

Peter's act of giving this prompt to Claude authorizes:

- repository documentation and focused test changes required below; and
- full relevant testing on `oracle-test`, including root/systemd, package,
  failure-injection, rollback and cleanup testing.

It authorizes **no production or staging access of any kind and no production
or staging mutation**. Do not inspect production again. Do not create, inspect,
edit or remove a production grant; install a production package; create a
production account, group, home, linger entry, deployment tree, artifact,
policy, runtime/state path or unit; reload, enable, start, stop or restart a
production service; reboot production; run Route 3; or perform a migration,
cutover or RB-1 outside `oracle-test`.

Do not read secrets, credentials, `.env`, process environments or arguments,
or player data. If a guard refuses a command, stop rather than routing around
it.

## Remediation 1 — make package rollback operation-owned

Record the exact package effect attributable to S1.1 and use that record for
rollback. R must never derive its removal set from all differences between the
current host and the old S1.0 snapshot.

At minimum:

- capture the pre-state before `apt-get`;
- after a successful `apt-get`, capture the exact package/version result and
  derive the packages newly installed by that command;
- make the operation-owned removal list durable before S1.1 can report
  success;
- for an interrupted or non-zero `apt-get` that may have partially installed
  packages, establish the attributable package set without sweeping in a
  later unrelated change;
- remove only operation-owned packages, with no `purge` or `autoremove`;
- never downgrade, remove or unhold a package that pre-existed the operation;
- preserve a package added after S1.1, return an explicit escalation if that
  means the complete package snapshot cannot equal the old pre-state, and do
  not delete the unrelated package merely to make the snapshot compare equal;
- make any concurrency/serialization assumption explicit and mechanically
  checked. An operator instruction such as “do not run apt concurrently” is
  not by itself ownership evidence after an interrupted command; and
- keep rollback idempotent.

If the only safe design is to hold the package-manager lock across a bounded
critical section or to use an apt simulation/transaction record, implement the
smallest auditable version and test its interruption behavior. Do not solve the
finding by deleting every later package addition.

## Remediation 2 — close and verify the apt artifact set

The production package transaction must consume an exact reviewed closure, not
just two top-level names followed by ambient dependency resolution.

The release record and executable blocks must:

- require `python3.14`, `python3.14-minimal`, `python3.14-venv` and every
  package the production solver will install or change, each as exact
  `name=version`;
- establish the complete solver result during the read-only production
  preflight without installing anything;
- fail if the solver proposes any install, upgrade, downgrade, removal or
  version not represented exactly in the reviewed field;
- bind every selected candidate version to the intended Ubuntu archive origin;
  do not accept an origin substring merely because it appears somewhere in an
  `apt-cache policy` report for a different version or source;
- install only after the simulated transaction exactly matches the reviewed
  package closure;
- after installation, verify every package/version in that closure and the
  packaged-file integrity checks, plus the existing interpreter digest;
- fail if any additional dependency appears; and
- document a reproducible source for `ROUTE3_PY_SHA256` while Python 3.14 is
  still absent on production. Do not claim that S0.2 hashes a production file
  that does not yet exist. Use an independently obtained, package-bound
  reference identity or leave a named blocker with an exact acquisition
  procedure.

Do not promote the current `oracle-test` versions or repository observations
to production values. The fields remain `UNSET` unless Peter supplies the
reviewed production values.

## Remediation 3 — fail closed on account and group queries

Every rollback decision and final verification must distinguish:

- the exact, documented `getent` result meaning “not found”;
- status 0 meaning the identity exists; and
- every other status meaning the query failed or is indeterminate.

R may report success only after it has affirmatively established that both the
account and group are absent. A query error is an explicit escalation status,
not absence. Apply the same rule anywhere R or R3 relies on `getent`, `id`,
`systemctl is-active` or equivalent identity/manager observations to decide
that cleanup is complete. Do not weaken the already fail-closed preflight.

The rollback result must remain non-zero when an identity or manager query is
unavailable, even if every filesystem object appears absent.

## Remediation 4 — make S1.0 recoverable at every instruction boundary

Treat evidence/pre-state creation as its own transaction with an explicit
incomplete state.

The plan must safely handle failure after each S1.0 state-changing or writing
operation, including:

- evidence-directory creation;
- package snapshot capture;
- hold snapshot capture;
- absent-object/account/group snapshot capture; and
- checkpoint creation or synchronization.

A partial S1.0 must have one exact recovery path that:

- never treats incomplete evidence as an authoritative pre-state;
- removes or quarantines only the literal evidence directory created by that
  failed S1.0 attempt, after proving it contains no completed pre-state and no
  later checkpoint;
- refuses if any S1.1-or-later marker or created object is present;
- preserves complete evidence from a real provisioning attempt;
- returns a reliable non-zero escalation rather than guessing when the state
  is ambiguous; and
- permits a clean S1.0 retry after successful recovery.

Prefer staged evidence creation followed by one atomic publication of a
complete pre-state, with a narrowly verified cleanup path for the unpublished
stage. Do not make Peter's post-review evidence-disposal block the routine
recovery for an incomplete S1.0.

Update the checkpoint/rollback matrix and handback claims so they describe the
actual behavior rather than retaining the R1 overclaim.

## Regression coverage

Extend `tests/test_provisioning_plan.py` using the literal extracted runbook
blocks. String-presence assertions are not sufficient. Preserve the existing
coverage and add at least:

1. a package added after S1.1 survives R; R does not name it in `apt-get
   remove`, and the result explicitly reports any remaining pre-state
   difference without deleting it;
2. a partial/non-zero apt install removes only packages attributable to that
   attempted transaction;
3. an exact reviewed apt closure passes, while an omitted dependency,
   additional solver dependency, version change, removal, downgrade and
   candidate-origin mismatch each fail before installation;
4. a trusted-origin line belonging only to a non-candidate version does not
   satisfy the candidate-origin check;
5. post-install verification fails on an unlisted package effect or a listed
   package/version mismatch;
6. account and group lookup status 0, the exact absent status and at least two
   other non-zero statuses are distinguished; query errors make R non-zero and
   never print `Pre-state restored`;
7. manager/identity-query failure in R3 cannot report STOP-A restored;
8. deterministic failure after each S1.0 write listed above reaches the exact
   incomplete-evidence recovery path;
9. successful incomplete-S1.0 recovery permits a clean S1.0 rerun;
10. recovery refuses to remove complete evidence or evidence carrying any
    later-stage marker; and
11. the full S1→S2 STOP-A path, R convergence, S3→R3 path, sanitized installer
    statuses, archive/deployment trust and checklist item 8 continue to pass.

Mutation-test the material predicates: removing operation ownership from the
package removal list, accepting an extra solver package, treating arbitrary
non-zero `getent` as absence, or allowing incomplete evidence to masquerade as
complete must each cause a regression to fail.

Use real apt only on `oracle-test`, never production. A deterministic fake
solver is appropriate for exhaustive transaction shapes, but at least one
disposable-host check must confirm that the chosen simulation command and
machine-readable parsing match the actual Ubuntu apt version. Do not install or
remove unrelated disposable-host packages merely to create a test case.

## Scope discipline

Expected files are limited to:

- `docs/operations/executor-supervisor-provisioning-runbook.md`;
- `tests/test_provisioning_plan.py`;
- the existing production-readiness handback;
- the live current-authority records needed to point to this R2 remediation
  and retain the production NO-GO; and
- only if an executable helper is strictly necessary for safe apt-plan parsing,
  one small repository-owned helper plus focused tests. Prefer keeping the
  executable plan self-contained.

Do not change `tools/executor_supervisor_install.py`, the service fragment,
supervisor, SA-2 roles, Polkit behavior, sudoers vector, account topology or
application behavior. If one of those appears necessary, stop and return the
conflict rather than expanding scope.

Do not create another prompt, another handback, an evidence dossier or a
recursive remediation chain. Update the existing handback once.

## Verification

Synchronize the exact workspace to `oracle-test` using the canonical
secret-excluding command. Run serially with
`TEST_DATABASE_URL=postgresql+psycopg:///freedom_test`:

1. `tests/test_provisioning_plan.py` as root;
2. `tests/test_production_checklist_item_8.py` as root;
3. `tests/test_production_checklist_item_5b.py`,
   `tests/test_executor_supervisor_install.py` and
   `tests/test_executor_system_service.py`;
4. the real read-only apt simulation/parser check on `oracle-test`;
5. directly affected structural and deployment-artifact tests;
6. `bash -n` over every executable runbook/checklist block added or changed;
7. `.claude/hooks/test_guards.py`; and
8. `git diff --check`.

The installer, service fragment and supervisor are out of scope and should not
change, so the root/systemd package-host module need not be rerun unless Claude
finds and reports an unexpected scope conflict before editing those files.

For destructive-plan tests, substitute only fixture-owned exact paths on
`oracle-test`. After root testing, prove that no test account/group, linger
file, sudoers fragment, unit, state/runtime path, mount, artifact,
`/opt/freedom-route3` tree, `frt-plan-*` path or pytest temporary residue
remains.

Report every failure, error and skip with reliable status. Do not call a result
pre-existing without a meaningful baseline comparison.

## Required return

Add one concise **Production provisioning-plan remediation R2 return —
2026-11-01** above the R1 return in
`docs/review/route-3-production-readiness-handback.md`. State:

- files and behavior changed;
- how the apt closure is obtained, origin-bound, reviewed and verified;
- how package ownership is recorded for both successful and interrupted apt
  operations;
- proof that an unrelated later package survives rollback;
- the exact fail-closed identity-query behavior;
- the incomplete-S1.0 evidence transaction and recovery path;
- focused and disposable-host test results, including failures, errors and
  skips;
- `oracle-test` cleanup disposition;
- confirmation that no production or staging access occurred; and
- one recommendation: ready or not ready for independent Codex re-review.

Reconcile the active handover, status, active delivery plan, implementation
plan §20, decision/RAID registers, change log and review index to say that R2
has returned for independent review while provisioning, installation and
activation remain unauthorized. Preserve historical observations and Peter's
2026-10-31 decisions.

Do not accept the plan, authorize provisioning or activation, commit, push or
perform production work. Stop after the return.
