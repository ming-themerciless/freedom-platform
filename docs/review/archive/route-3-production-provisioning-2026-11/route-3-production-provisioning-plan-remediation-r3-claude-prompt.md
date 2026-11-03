# Claude prompt — Route 3 production provisioning-plan remediation R3

Date prepared: 2026-11-01  
Owner and acceptance authority: Peter Duscha  
Implementer: Claude  
Reviewer after return: Codex  
Target: the uncommitted Route 3 provisioning-plan candidate currently in the
workspace

## Assignment

Apply one narrow correction to the Route 3 production provisioning plan for
the two defects independently reproduced in Codex's review of the R2 return:

1. S1.1 can attribute another apt transaction's package to Route 3 during the
   interval between its idle check/snapshot and Route 3 apt acquiring the
   package-manager lock; R then removes that package and returns success.
2. `route3_unit` accepts recognized `systemctl is-active` text without checking
   the command's status; a failed query that prints `inactive` is therefore
   treated as a definite inactive manager state.

Do not redesign the provisioning plan. R2's closed apt set, origin binding,
staged S1.0 evidence, R0 recovery, stage separation and production NO-GO
boundary remain in force.

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
   part P blocks D, S1.1, R and R3;
7. `docs/review/route-3-production-readiness-handback.md`, especially the R2
   return;
8. `docs/review/route-3-production-provisioning-plan-remediation-r2-claude-prompt.md`;
   and
9. the two review findings above.

The selected deployment remains `/opt/freedom-route3/{code,venv}`. The live
`freedom-bot`, `freedom-web` and `freedom-worker` paths and services remain
untouched.

## Authority and hard boundary

Peter's act of giving this prompt to Claude authorizes:

- repository documentation and focused test changes required below; and
- full relevant testing on `oracle-test`, including root package simulation,
  failure injection, rollback and cleanup testing.

It authorizes **no production or staging access of any kind and no production
or staging mutation**. Do not inspect production again. Do not create, inspect,
edit or remove a production grant; install or remove a production package;
create a production account, deployment, artifact, policy or unit; reload,
enable, start, stop or restart a production service; reboot production; run
Route 3; or perform a migration, cutover or RB-1 outside `oracle-test`.

Do not read secrets, credentials, `.env`, process environments or arguments,
or player data. If a guard refuses a command, stop rather than routing around
it.

## Correction 1 — make apt ownership transaction-derived or refuse removal

The R2 time-of-check design is insufficient. `route3_apt_idle`,
`beforeC1.dpkg`, `apt.intent` and a later package delta do not prove which apt
transaction installed an intent member. A separate transaction can install an
intent member after the snapshot and before Route 3 apt takes its own lock; the
current delta then labels that package Route 3-owned.

Replace that inference with evidence generated **inside the specific Route 3
apt transaction after it owns apt/dpkg serialization**. The evidence must name
the exact packages that this invocation actually submits for installation and
must be durably associated with this attempt before those package effects can
be treated as automatically removable.

An apt/dpkg transaction hook or another apt-supported per-invocation mechanism
is acceptable if it is narrowly configured on the one S1.1 command, writes
only into the verified evidence directory, has a documented machine-readable
format, is made durable, and is validated against the reviewed closure. Do not
change global apt configuration. Do not infer ownership from elapsed time,
the shell PID alone, the package delta alone, or an idle check performed before
apt obtains its lock.

The required behavior is:

- a package installed by a separate transaction in the pre-acquisition race
  is never recorded as Route 3-owned and is never named to `apt-get remove`;
- a successful Route 3 apt transaction records exactly its own package effect;
- a non-zero or interrupted Route 3 apt transaction may automatically remove
  only packages supported by durable transaction-specific evidence;
- if an interruption occurs before trustworthy transaction-specific evidence
  exists, R removes **no package**, returns a named non-zero escalation status,
  and preserves the evidence for operator review;
- a malformed, missing, duplicated, out-of-closure or contradictory
  transaction record is an ambiguity, not permission to derive ownership from
  the before/after package delta;
- a later unrelated package and a later package depending on a Route 3-owned
  package remain protected by R2's refusal behavior;
- no pre-existing package is removed, downgraded or newly treated as owned;
- successful and refused rollback remain idempotent; and
- the runbook explicitly removes the R2 residual claiming that the
  pre-acquisition race is merely checked by the idle and delta checks.

Use the safest bounded fallback: ambiguity escalates without automatic package
removal. It is preferable to require attended recovery of an ambiguous package
state than to delete a package whose ownership is unproved.

Exercise the selected transaction-evidence mechanism against the real apt
version on `oracle-test` without installing or removing an unrelated host
package. A simulation, fixture-owned disposable package transaction, or an
apt-supported no-effect probe is acceptable only if it establishes the actual
hook/protocol shape and status propagation used by the runbook. Do not weaken
the production predicate to fit the fake solver.

## Correction 2 — make manager observations status-aware

Replace `route3_unit`'s output-only decision with a definite manager query that
checks both command status and a strictly allowlisted state.

Prefer a `systemctl show` property query whose successful observation has an
unambiguous success status. If `systemctl is-active` remains, encode and test
the exact status/output pairs produced by the target systemd version; never
accept recognized text paired with a status that means command/query failure.

Apply the helper consistently wherever R or R3 uses manager state to decide
whether destructive rollback may proceed or whether STOP-A has been restored.
Also inspect S2.1's direct manager checks and use the same fail-closed rule for
its STOP-A claim where applicable.

Required behavior:

- a failed manager command that prints `inactive`, `failed`, `active` or any
  other plausible state is **indeterminate**;
- empty output with a nominal success status is indeterminate;
- unknown or malformed output is indeterminate;
- only a command/status/state combination proved to mean a definite state may
  be used;
- R3 performs no installer removal, sudoers removal, SA-2 removal or linger
  change when the initial supervisor-state query is indeterminate;
- final manager verification failure keeps R/R3 non-zero and never prints
  `Pre-state restored`, `STOP-A re-established` or `STOP-A verified`; and
- legitimate inactive, failed, active and not-found states used by the plan
  continue to behave as documented.

Do not change the installer or supervisor to solve an operator-query defect.

## Regression coverage

Extend `tests/test_provisioning_plan.py` using the literal extracted blocks and
helpers. Preserve the 160 passing R2 cases and add at least:

1. the exact reproduced race: after Route 3 records its pre-transaction
   snapshot but before its apt command owns serialization, a separate apt
   transaction installs one or more reviewed intent members; S1.1/R must not
   record or remove those packages as Route 3-owned;
2. the same race followed by a successful Route 3 apt invocation;
3. an interrupted Route 3 apt invocation with a complete durable
   transaction-specific record removes only the recorded effect;
4. interruption before that record exists removes nothing and returns the
   explicit ambiguity/escalation status;
5. missing, malformed, duplicate, out-of-closure and contradictory transaction
   records each fail closed without package removal;
6. an unrelated package and a reverse-dependent package remain protected;
7. mutation back to R2's `intent ∩ package delta` ownership inference causes
   the race regression to fail;
8. manager output `inactive`, `failed` and `active`, each paired with a query
   failure status, is indeterminate and blocks R3 before its first mutation;
9. empty output/success and malformed output/success are indeterminate;
10. the real legitimate status/state pairs required by R3 and S2.1 pass;
11. final manager-query failure prevents every restored/verified success
    message; and
12. mutation that discards the manager command status causes the matching
    regression to fail.

String-presence assertions are not sufficient. Run the literal functions and
blocks. Keep deterministic fake-world cases for exhaustive failures and add a
narrow real-`systemctl` read-only check on `oracle-test` establishing the
status/state pairs the helper accepts. Do not create or start a real Route 3
unit for this correction.

## Scope discipline

Expected files are limited to:

- `docs/operations/executor-supervisor-provisioning-runbook.md`;
- `tests/test_provisioning_plan.py`;
- the existing production-readiness handback; and
- the live current-authority records needed to point to the R3 return while
  retaining the production NO-GO.

Only if the apt transaction-evidence mechanism cannot be expressed safely in
the literal runbook may Claude add one small, standard-library-only operator
helper under `tools/`, included in the controlled deployment manifest and
covered by focused trust/input/status tests. Do not add a helper merely for
convenience.

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
4. the real read-only apt transaction-protocol and systemctl status/state
   checks on `oracle-test`;
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
`/opt/freedom-route3` tree, `frt-plan-*` path, temporary apt-hook file or pytest
temporary residue remains. Confirm `dpkg --audit` is clean and no test hold or
package remains.

Report every failure, error and skip with reliable status. Do not call a result
pre-existing without a meaningful baseline comparison.

## Required return

Add one concise **Production provisioning-plan remediation R3 return —
2026-11-01** above the R2 return in
`docs/review/route-3-production-readiness-handback.md`. State:

- files and behavior changed;
- the exact transaction-specific apt ownership mechanism;
- the behavior when transaction ownership cannot be proved;
- direct proof that the reproduced pre-acquisition race preserves the other
  transaction's packages;
- the accepted manager command/status/state matrix;
- proof that status/output disagreement blocks R3 before mutation;
- focused and disposable-host results, including failures, errors and skips;
- `oracle-test` cleanup disposition;
- confirmation that no production or staging access occurred; and
- one recommendation: ready or not ready for independent Codex re-review.

Reconcile the active handover, status, active delivery plan, implementation
plan §20, decision/RAID registers, change log and review index to say that R3
has returned for independent review while provisioning, installation and
activation remain unauthorized. Preserve the R1/R2 history and Peter's
2026-10-31 decisions.

Do not accept the plan, authorize provisioning or activation, commit, push or
perform production work. Stop after the return.
