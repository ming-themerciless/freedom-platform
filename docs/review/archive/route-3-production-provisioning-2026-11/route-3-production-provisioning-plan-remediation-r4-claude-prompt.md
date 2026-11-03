# Claude prompt — Route 3 production provisioning-plan remediation R4

Date prepared: 2026-11-01  
Owner and acceptance authority: Peter Duscha  
Implementer: Claude  
Reviewer after return: Codex  
Target: the uncommitted Route 3 provisioning-plan candidate currently in the
workspace

## Assignment

Apply one narrow correction to the Route 3 production provisioning plan for
the remaining package-ownership defect independently reproduced in Codex's
review of the R3 return.

R3's `DPkg::Pre-Install-Pkgs` hook durably proves which packages the Route 3
apt invocation submitted before unpacking. It does **not** prove which package
effects that invocation completed. If S1.1 is killed after the hook record is
written but before a recorded package is unpacked, and another transaction
later installs that exact package version before R runs, R currently treats
the package as Route 3-owned, removes it and returns success.

Codex reproduced that exact sequence against the literal runbook harness:

- S1.1 wrote a complete `apt.txn` and was killed before installing anything
  (`rc=137`);
- a separate transaction then installed recorded package
  `libfake-dep=1.0`; and
- R returned `0`, named `libfake-dep` to `apt-get remove`, removed it and
  reported the pre-state restored.

Close only this post-record/pre-effect attribution gap. Do not redesign the
provisioning plan. Preserve R3's status-aware manager queries and all R2/R3
controls that are not directly affected.

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
   part P block D, S1.1 and R;
7. `docs/review/route-3-production-readiness-handback.md`, especially the R3
   return and its stated post-hook residual; and
8. `docs/review/route-3-production-provisioning-plan-remediation-r3-claude-prompt.md`.

The selected deployment remains `/opt/freedom-route3/{code,venv}`. The live
`freedom-bot`, `freedom-web` and `freedom-worker` paths and services remain
untouched.

## Authority and hard boundary

Peter's act of giving this prompt to Claude authorizes:

- the focused repository documentation and test changes required below; and
- full relevant testing on `oracle-test`, including root-owned fixture package
  transactions, interruption/failure injection, rollback and cleanup testing.

It authorizes **no production or staging access of any kind and no production
or staging mutation**. Do not inspect production again. Do not create, inspect,
edit or remove a production grant; install or remove a production package;
create a production account, deployment, artifact, policy or unit; reload,
enable, start, stop or restart a production service; reboot production; run
Route 3; or perform a migration, cutover or RB-1 outside `oracle-test`.

Do not read secrets, credentials, `.env`, process environments or arguments,
or player data. If a guard refuses a command, stop rather than routing around
it.

## Required correction — prove completed effects or remove nothing

Keep the per-invocation pre-install transaction record if it remains useful,
but never promote a pre-install submission record by itself into proof that
Route 3 installed the package.

Automatic rollback may remove a package only when durable evidence proves
that the specific Route 3 apt invocation completed that exact package effect.
That evidence must be generated while the invocation still owns package-manager
serialization and after the relevant effect is observable. It must be written
only beneath the verified evidence directory, use a documented
machine-readable format, be made durable, and be validated against the
reviewed intent, the pre-install record and the pre-state.

An apt-supported per-invocation post-effect hook is acceptable if real-host
testing proves its ordering, lock/serialization context, protocol and status
behavior. Another mechanism is acceptable only if it establishes the same
transaction-specific completed-effect fact. Evidence inferred after apt has
released serialization from elapsed time, PID, package timestamps, the
pre-install record, or a before/after package delta is insufficient.

Required behavior:

- after a normal successful Route 3 apt invocation, completed-effect evidence
  names exactly the packages and versions that invocation installed;
- after a normal non-zero invocation, R may remove only the completed effects
  proved by that evidence;
- after a kill, signal or other interruption before completed-effect evidence
  is durably published, ownership is ambiguous even when `apt.txn` is complete;
  R removes **no package**, lifts **no hold**, preserves all evidence and exits
  the named ambiguity status (`28`, unless a narrowly justified existing
  status is more accurate);
- in the reproduced sequence above, the later transaction's package is never
  named to `apt-get remove`, remains installed, and R cannot report success or
  `Pre-state restored`;
- missing, truncated, malformed, duplicated, out-of-closure, contradictory,
  symlinked or wrongly owned/mode completed-effect evidence is ambiguity, not
  permission to fall back to `apt.txn` or a package delta;
- an effect record cannot claim a package absent from the validated
  pre-install transaction record or present in the pre-state;
- unrelated later packages and reverse dependants retain the existing R2/R3
  protections;
- no pre-existing or separately installed package is removed, downgraded or
  newly treated as Route 3-owned;
- successful and refused rollback remain idempotent; and
- the runbook and handback remove the R3 residual rather than merely
  reclassifying or accepting it.

Use the safest bounded fallback: when completed ownership cannot be proved,
escalate without automatic package removal. Attended recovery is preferable
to deleting a package whose installer is unknown.

## Regression coverage

Extend `tests/test_provisioning_plan.py` using the literal extracted helpers
and blocks. Preserve the existing R3 cases and add at least:

1. the exact Codex reproduction: complete `apt.txn`; kill before any unpack;
   another transaction installs one recorded exact version; R returns non-zero,
   removes nothing and preserves that package;
2. the same sequence with only some submitted packages installed by Route 3
   before the kill and the remaining recorded packages installed later by a
   separate transaction; without durable completed-effect evidence R treats
   the whole package effect as ambiguous and removes nothing;
3. a successful invocation publishes completed-effect evidence for exactly
   its installed set and R removes exactly that set;
4. a normal non-zero invocation with valid completed-effect evidence removes
   only the proved partial effect;
5. kill/failure at every material write, sync and publication boundary of the
   completed-effect record;
6. missing and each malformed/contradictory completed-effect record fails
   closed without unholding or removal;
7. a later unrelated package and a reverse dependant remain protected;
8. repeated refused rollback remains refused and non-mutating;
9. mutation that restores R3's `ROUTE3_OWN=$ROUTE3_TXN` fallback causes the
   exact reproduction to delete the other transaction's package and makes the
   regression fail; and
10. the existing manager status/output disagreement tests remain passing
    unchanged.

String-presence assertions are not sufficient. Execute the literal functions
and blocks. Exercise the chosen apt mechanism against the real apt version on
`oracle-test` with fixture-owned packages only. Prove the actual ordering,
serialization context, record contents and status propagation used by the
production plan; do not weaken the production predicate to fit the fake solver.

## Scope discipline

Expected files are limited to:

- `docs/operations/executor-supervisor-provisioning-runbook.md`;
- `tests/test_provisioning_plan.py`;
- `docs/review/route-3-production-readiness-handback.md`; and
- the live current-authority records needed to point to the R4 return while
  retaining the production NO-GO.

Only if safe completed-effect evidence cannot be expressed in the literal
runbook may Claude add one small standard-library-only operator helper under
`tools/`, included in the controlled deployment manifest and covered by
focused trust, input, interruption and status tests. Do not add a helper for
convenience.

Do not change the manager-query correction,
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
2. the exact post-hook/pre-effect Codex reproduction as a named committed
   regression test;
3. the real apt completed-effect protocol tests with fixture-owned packages;
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
`/opt/freedom-route3` tree, `frt-plan-*` path, temporary apt hook/effect file,
pytest temporary residue, package hold or fixture package remains. Confirm
`dpkg --audit` is clean.

Report every failure, error and skip with reliable status. Do not call a result
pre-existing without a meaningful baseline comparison.

## Required return

Add one concise **Production provisioning-plan remediation R4 return —
2026-11-01** above the R3 return in
`docs/review/route-3-production-readiness-handback.md`. State:

- files and behavior changed;
- the exact completed-effect evidence mechanism and why a pre-install record
  alone is no longer ownership;
- behavior after normal success, normal failure and interruption;
- direct proof that the reproduced later transaction's package is preserved;
- mutation proof that the former R3 fallback fails the new regression;
- real-apt protocol evidence;
- focused and disposable-host results, including failures, errors and skips;
- `oracle-test` cleanup disposition;
- confirmation that no production or staging access occurred; and
- one recommendation: ready or not ready for independent Codex re-review.

Reconcile the active handover, status, active delivery plan, implementation
plan §20, decision/RAID registers, change log and review index to say that R4
has returned for independent review while provisioning, installation and
activation remain unauthorized. Preserve the R1–R3 history, the accepted
manager-query correction and Peter's 2026-10-31 decisions.

Do not accept the plan, authorize provisioning or activation, commit, push or
perform production work. Stop after the return.
