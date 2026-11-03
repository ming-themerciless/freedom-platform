# Claude prompt — Route 3 production provisioning-plan remediation R5

Date prepared: 2026-11-01  
Owner and acceptance authority: Peter Duscha  
Implementer: Claude  
Reviewer after return: Codex  
Target: the uncommitted Route 3 production provisioning-plan candidate currently in the workspace

## Assignment

Apply one narrow correction to the Route 3 production provisioning plan for
the remaining package-ownership defect independently reproduced in Codex's
review of the R4 return.

R4 changed ownership from the pre-install submission record to a durable
`DPkg::Post-Invoke` package-state observation. That observation is still not
exclusive proof that Route 3's submitted dpkg action created the effect. Apt
runs the configured `DPkg::Post-Invoke` list in order with
`DPKG_FRONTEND_LOCKED=true`; an earlier supported hook can invoke a separate
`dpkg` operation before the Route 3 hook queries package state. The Route 3
hook then records that separately installed package as its completed effect.

Codex reproduced that sequence on `oracle-test` with fixture-only packages:

- apt's submitted fixture package failed (`apt-get` status 100);
- an earlier per-invocation `DPkg::Post-Invoke` hook installed the same package
  name and version from a different fixture `.deb` using `dpkg`;
- the installed payload proved that it came from the earlier hook, not apt's
  submitted package;
- R4 nevertheless wrote the row to `apt.effects`; and
- `route3_own_resolve` returned the row as Route 3-owned, permitting R to name
  the separately installed package to `apt-get remove`.

Close this attribution problem by removing automatic package and hold rollback
from R. Do not attempt another post-state ownership inference and do not expand
the plan into an apt-hook isolation framework. Preserve the useful diagnostic
records if appropriate, but no pre-install record, post-invoke observation,
package delta, PID, timestamp, lock observation or combination of them is
authorization to remove or unhold a package automatically.

The candidate remains **NO-GO**. Provisioning, installation and activation are
unauthorized. This prompt authorizes repository remediation and full relevant
testing on `oracle-test`; it authorizes no production or staging access or
mutation.

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
8. `docs/review/route-3-production-provisioning-plan-remediation-r4-claude-prompt.md`.

The selected deployment remains `/opt/freedom-route3/{code,venv}`. The live
`freedom-bot`, `freedom-web` and `freedom-worker` paths and services remain
untouched.

## Authority and hard boundary

Peter's act of giving this prompt to Claude authorizes:

- the focused repository documentation and test changes required below; and
- full relevant testing on `oracle-test`, including root-owned fixture package
  transactions, apt-hook ordering, interruption/failure injection and cleanup
  testing.

It authorizes **no production or staging access of any kind and no production
or staging mutation**. Do not inspect production again. Do not create, inspect,
edit or remove a production grant; install or remove a production package;
create a production account, deployment, artifact, policy or unit; reload,
enable, start, stop or restart a production service; reboot production; run
Route 3; or perform a migration, cutover or RB-1 outside `oracle-test`.

Do not read secrets, credentials, `.env`, process environments or arguments,
or player data. If a guard refuses a command, stop rather than routing around
it.

## Required correction — package rollback is an attended boundary

R must never run `apt-get remove`, `apt remove`, `dpkg --remove`, `dpkg --purge`,
`apt-mark unhold` or an equivalent package/hold mutation for S1.1. This applies
after success, ordinary failure, signal, kill, hook failure, malformed or
missing evidence, a later transaction, or a decision to withdraw a completed
STOP-A state.

Required behavior:

- S1.1 may still install and hold the reviewed pinned closure under a future
  provisioning authorization. Its success checks remain fail-closed.
- S1.1 must retain enough root-only durable evidence for an attending operator
  to understand the reviewed intent, pre-state, apt status and observed
  package/hold state. Diagnostic evidence must not be described or consumed as
  automatic-removal ownership.
- If R reaches C1 and the current package and hold state exactly equals the
  recorded pre-C1/pre-operation state, R may report that no package or hold
  recovery is required and continue its final verification.
- If any package or hold difference remains at C1, R changes no package and no
  hold, preserves all evidence, prints the exact differences, exits **28** and
  requires attended recovery. It must not print `Pre-state restored`.
- R may continue to undo later S1 objects (tmpfiles fragment, dormant account,
  deployment tree) in reverse order under their existing controls before it
  reaches the package boundary. The return must describe this partial rollback
  accurately. It must never conceal or discard the package evidence.
- A second or later R invocation is stable and non-mutating for packages and
  holds. It may idempotently verify or finish the independently safe later-S1
  cleanup.
- A completed STOP-A withdrawal therefore reaches automatic status 0 only when
  packages and holds already equal the captured state. Otherwise it stops at
  attended recovery status 28. Do not retain the former claim that R
  automatically restores a successfully installed package closure.
- R0 remains limited to incomplete S1.0 evidence. R3 remains the rollback from
  S3 to STOP-A. Neither becomes a route to mutate the S1.1 package set.
- The plan must give the attending operator facts and escalation direction,
  not an unreviewed manual removal recipe. A later package-removal decision is
  outside this plan and requires Peter's explicit direction based on the kept
  evidence.
- Remove or correct every statement that calls `apt.effects`, `owned.pkgs`, a
  lock-held post-state query, or any package delta completed-effect ownership.
  If the R4 post hook remains for diagnostics, name it only as an observation
  that can include effects produced by another configured hook.

Do not weaken S1.1's reviewed closure, exact-version, origin, interpreter
digest, `dpkg --verify`, artifact or hold checks. Do not weaken R's object,
identity, manager, path, mount, reverse-order or evidence-integrity controls.

## Regression coverage

Extend `tests/test_provisioning_plan.py` using the literal extracted helpers
and blocks. Preserve the R2–R4 safety cases where their expected behavior is
still valid; explicitly rewrite only cases that asserted automatic package
removal or unholding, because that behavior is now removed. Add at least:

1. the exact Codex R4 reproduction with real fixture `.deb` files: apt's
   submitted package fails, an earlier `DPkg::Post-Invoke` hook separately
   installs the same name/version from a distinguishable payload, the Route 3
   observation sees it, and R exits 28 without removing or unholding it;
2. a successful S1.1 followed by R: packages and Route 3-added holds remain,
   no package-manager mutation command is issued, evidence remains and R exits
   28;
3. a normal non-zero partial installation followed by R with the same
   non-mutating status-28 behavior;
4. interruption before and after every former submission/effect publication
   boundary, all preserving packages and holds;
5. missing, malformed, contradictory, symlinked and wrongly owned/mode
   diagnostic records cannot enable a package or hold mutation;
6. a failure before any package or hold effect, with current package and hold
   state exactly matching the recorded state, permits R to finish without a
   false ambiguity;
7. unrelated later packages, same-name/version packages installed by another
   action and reverse dependants all remain untouched;
8. later S1 objects are safely undone before the attended C1 boundary, and a
   repeated R is idempotent without package/hold mutation;
9. a structural assertion that no S1 rollback path contains package removal,
   purge, autoremove, downgrade or unhold commands; and
10. a mutation that reintroduces the R4 automatic removal/unhold path makes a
    named regression delete or unhold the separately installed fixture and
    therefore fails.

String-presence assertions alone are not sufficient. Execute the literal
functions and blocks. Exercise the earlier-hook ordering against the real apt
version on `oracle-test` with fixture-owned packages only. Assert a
distinguishable payload so equal name/version cannot hide which `.deb` produced
the installed state.

The existing manager status/output disagreement tests must remain passing
unchanged. Preserve the exact exit status of every block.

## Scope discipline

Expected files are limited to:

- `docs/operations/executor-supervisor-provisioning-runbook.md`;
- `tests/test_provisioning_plan.py`;
- `docs/review/route-3-production-readiness-handback.md`; and
- the live current-authority records needed to point to the R5 return while
  retaining the production NO-GO.

Do not add another operator helper. Do not change the manager-query correction,
`tools/executor_supervisor_install.py`, the service fragment, supervisor, SA-2
roles, Polkit behavior, sudoers vector, account topology or application
behavior. If one of those changes appears necessary, stop and return the
conflict rather than expanding scope.

Do not create another prompt, another handback, an evidence dossier or another
remediation chain. Update the existing handback once.

## Verification

Synchronize the exact workspace to `oracle-test` using the canonical
secret-excluding command. Run serially with
`TEST_DATABASE_URL=postgresql+psycopg:///freedom_test`:

1. `tests/test_provisioning_plan.py` as root;
2. the committed real-apt earlier-`Post-Invoke` reproduction;
3. the existing real-apt submission/effect/interruption cases, revised only as
   needed to remove ownership claims;
4. `tests/test_production_checklist_item_8.py` as root;
5. `tests/test_production_checklist_item_5b.py`,
   `tests/test_executor_supervisor_install.py` and
   `tests/test_executor_system_service.py`;
6. directly affected structural and deployment-artifact tests;
7. `bash -n` over every executable runbook/checklist block added or changed;
8. `.claude/hooks/test_guards.py`; and
9. `git diff --check`.

The installer, service fragment, supervisor and manager-query correction are
out of scope and should not change. The root/systemd package-host module need
not be rerun unless Claude finds and reports an unexpected scope conflict
before editing.

For destructive-plan tests, substitute only fixture-owned exact paths and
packages on `oracle-test`. After testing, prove that no fixture account/group,
linger file, sudoers fragment, unit, state/runtime path, mount, artifact,
`/opt/freedom-route3` tree, `frt-plan-*` or `frt-r5-*` path, temporary apt hook,
pytest temporary residue, package hold or fixture package remains. Confirm
`dpkg --audit` is clean.

Report every failure, error and skip with reliable status. Do not call a result
pre-existing without a meaningful baseline comparison. Re-run the complete
focused module after the final executable or test change; a failing full run
followed only by selected reruns is not final evidence.

## Required return

Add one concise **Production provisioning-plan remediation R5 return —
2026-11-01** above the R4 return in
`docs/review/route-3-production-readiness-handback.md`. State:

- files and behavior changed;
- that automatic S1.1 package removal and unholding are gone;
- the exact status-28 attended boundary and what R can still undo safely;
- direct proof that the earlier-hook fixture remains installed and held state
  is not mutated by R;
- mutation proof that restoring R4 removal/unhold behavior fails;
- focused and disposable-host results, including failures, errors and skips;
- `oracle-test` cleanup disposition;
- confirmation that no production or staging access occurred; and
- one recommendation: ready or not ready for independent Codex re-review.

Reconcile the active handover, status, active delivery plan, implementation
plan §20, decision/RAID registers, change log and review index to say that R5
has returned for independent review while provisioning, installation and
activation remain unauthorized. Preserve the R1–R4 history, the accepted
manager-query correction and Peter's 2026-10-31 decisions.

Do not accept the plan, authorize provisioning or activation, commit, push or
perform production work. Stop after the return.
