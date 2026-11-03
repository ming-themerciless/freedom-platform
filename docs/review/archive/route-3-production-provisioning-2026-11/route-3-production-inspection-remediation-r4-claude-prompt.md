# Claude prompt — Route 3 trusted item-8 and exit-status remediation

Date prepared: 2026-10-30  
Owner and acceptance authority: Peter Duscha  
Reviewer after return: Codex  
Target: the uncommitted Route 3 production-readiness candidate currently in the workspace

## Assignment

Remediate the two blocking findings from Codex's independent review of the R3
return:

1. checklist item 8 can still execute an untrusted regular file as root because
   it does not enforce ownership, mode or symlink-free parent components before
   `runpy.run_path()`; and
2. the provisioning runbook appends `echo "[rc=$?]"`, so verifier failure is
   printed but the runbook block itself exits 0.

This is one bounded correction of the existing R3 return. Preserve the
production no-go and the existing current-authority reconciliation. Update the
same production-readiness handback; do not create another handback, evidence
dossier or recursive review chain.

## Governing material

Before acting, read completely:

1. `.agents/AGENTS.md`;
2. `docs/implementation-plan.md` using its reading map, especially §0, §14,
   §16, §17 and §20;
3. `docs/review/Handover information`;
4. `docs/operations/disposable-test-server.md`;
5. `docs/review/route-3-production-readiness-handback.md`, especially its R3
   return and §§6–6.2;
6. `docs/operations/executor-supervisor-provisioning-runbook.md`;
7. `docs/review/route-3-production-inspection-remediation-r3-claude-prompt.md`;
   and
8. Codex's two findings quoted by this assignment.

The selected direction remains the separate trusted deployment at
`/opt/freedom-route3/{code,venv}`. This prompt changes no topology, production
authority, bounded-use policy, transient-risk decision or open production
disposition.

## Authority and hard boundary

Peter's act of giving this prompt to Claude authorizes:

- the repository changes required below; and
- full relevant testing on `oracle-test`, including root/systemd rehearsal and
  cleanup.

It authorizes **no production or staging access, inspection or write**. Do not
run another production check. Do not create, inspect, edit or remove a sudoers
file or grant; provision `/opt/freedom-route3`; install Python, an account,
artifact, policy or unit; change a service; run Route 3, migration, cutover or
RB-1; or read secrets, policy contents, process environments/arguments or player
data. The temporary-grant file disposition and Phase A deviation remain open
for Peter exactly as the current handover states.

If a guard refuses a command, stop rather than routing around it.

## Remediation 1 — enforce trust before item 8 executes code

The current entry point rejects only a missing or final-component symlink. It
then executes any regular file, including one that is non-root-owned or writable
and one reached through a symlinked parent. Item 7's diagnostic output is not a
gate: the checklist continues into item 8 after printing violations. Item 8
must therefore establish its own executable trust precondition before any
deployment Python source is evaluated.

Correct the executable v2 checklist and the runbook's matching post-provision
check so that:

- every path component from `/` through the deployed tool is checked without
  following symlinks;
- the deployment directories are real directories, owned by uid 0 and not
  writable by group or others;
- `tools/polkit_tmpfiles.py` is a real regular file, owned by uid 0 and not
  writable by group or others;
- the source fragment that the tool resolves beside itself, including its
  parent components, is subject to the same applicable directory/file trust
  rules before the tool can load it;
- any missing, wrong-type, symlinked, non-root-owned or writable component
  produces one fixed, non-secret finding, exits non-zero and evaluates no
  deployment Python source;
- a hostile ordinary checkout, ambient working directory, Python environment
  or user site remains unable to redirect code or imports;
- the fixed interpreter and isolation properties from R3 remain in force; and
- after the checks succeed, an unprivileged actor cannot swap the validated
  tool or fragment before it is opened. It is sufficient to make every parent
  directory root-owned and non-writable to non-root before execution; do not
  claim protection against a concurrent root attacker.

Do not treat a preceding `find`, `namei` or printed checklist finding as the
execution gate. The command that is about to evaluate Python must itself refuse
unless the complete required trust state has been established.

Choose the smallest auditable implementation. A narrowly scoped checked-in
launcher is allowed only if its own installation and trust source are already
inside the verified boundary and the change remains within this assignment; do
not broaden this into a new provisioning framework.

## Remediation 2 — preserve the runbook command's exit status

The runbook may print `[rc=N]`, but its executable block must also return `N`.
Do not leave a trailing `echo`, pipeline or other command that converts verifier
failure into shell success.

The block must be safe to paste into an operator's interactive shell without
terminating that outer shell merely to preserve status. A subshell or equivalent
bounded shape may capture the verifier status, print it, and return the same
status to the caller. Required outcomes include:

- trusted verifier success: printed `rc=0`, block status 0;
- absent or untrusted deployment: printed refusal status, the same non-zero
  block status, no deployment code executed; and
- `polkit_tmpfiles verify` failure such as 12: printed `rc=12`, block status 12.

The checklist may retain its established collect-all `chk` reporting model,
provided the tested command's real status is printed accurately and never
described as a pass. The standalone runbook block must propagate status because
it is a provisioning prerequisite.

## Regression coverage

Extend the focused checklist tests to extract and execute the literal current
checklist and runbook commands. Do not merely assert that expected strings are
present. Cover at least:

- a root-owned, non-writable, symlink-free synthetic deployment succeeds and
  executes exactly the expected tool;
- tool file non-root-owned;
- tool file group- or other-writable;
- final tool symlink;
- symlinked `tools`, `code` or another material parent component;
- non-root-owned or writable material parent directory;
- wrong-type or missing component;
- source fragment non-root-owned, writable, symlinked, wrong-type or missing;
- hostile `PYTHONPATH`, `PYTHONHOME`, user site, working directory and ordinary
  checkout cannot redirect execution;
- every refusal leaves an execution marker absent;
- the real trusted tool still resolves its source fragment from the trusted
  deployment and preserves its own 0/12 behavior; and
- the extracted runbook block returns exactly 0, the trust-refusal status and
  verifier status 12 in the corresponding cases.

Tests that substitute a user-owned `tmp_path` tree must deliberately construct
the ownership/mode conditions the production trust check expects. Do not call a
default user-owned writable fixture "trusted" and weaken production validation
to make it pass. Root-required ownership cases belong on `oracle-test` under the
authorized root test lane or in a deterministic seam that proves the exact
production predicate without bypassing it.

Include a mutation check showing that removal of an ownership/mode or parent-
symlink refusal makes a corresponding regression fail. Do not add a framework
or generalized security DSL.

## Scope discipline

Expected implementation files are limited to:

- `docs/review/route-3-production-readiness-handback.md`;
- `docs/operations/executor-supervisor-provisioning-runbook.md`;
- `tests/test_production_checklist_item_8.py` and, only if extraction sharing
  requires it, the existing checklist 5b test; and
- at most one small dedicated trusted-launcher module plus its focused test if
  the inline entry point cannot be made auditable.

Do not redesign or edit the supervisor, installer lifecycle, unit hardening,
SA-2 artifact, sudo vector, Polkit policy, account model, application behavior
or production services. Do not rewrite current-state records merely to repeat
the same no-go and open blockers. Update one existing current record only if a
material implementation statement would otherwise become false.

## Verification

Synchronize the exact workspace to `oracle-test` using the canonical
secret-excluding command. Run serially:

1. the changed checklist regression module, including the literal runbook
   status cases;
2. `tests/test_production_checklist_item_5b.py`;
3. `tests/test_executor_supervisor_install.py` and
   `tests/test_executor_system_service.py`;
4. `tests/systemd_integration/test_executor_package_host.py` as root with
   `FREEDOM_SYSTEMD_INTEGRATION=oracle-test` and root's normal executable path;
5. the directly affected structural/deployment-artifact tests;
6. `bash -n` over every changed executable shell block;
7. `.claude/hooks/test_guards.py`; and
8. `git diff --check`.

Use `TEST_DATABASE_URL=postgresql+psycopg:///freedom_test` for pytest. Do not run
bot, web or Node full suites unless executable product code outside this bounded
entry point changes. Report failures, errors and skips honestly. The accepted
pre-remediation structural comparison is **126 passed, 2 failed** on both the
workspace and pristine `HEAD`; do not replace it with an older figure or call a
new failure pre-existing without a meaningful comparison.

After the root host module, establish that `oracle-test` has no
`/opt/freedom-route3`, related mount, executor account/group, test sudoers
fragment, unit, state/runtime directory or test artifact left by the run.

## Required return

Add one concise **R4 direct-completion return** at the top of the existing
production-readiness handback. State:

- behavior and files changed;
- the exact trust properties item 8 now enforces before evaluating code;
- how an unprivileged swap is prevented after validation;
- how the standalone runbook block preserves both printed and process status;
- regression and mutation coverage;
- every test/check result, including failures, errors and skips;
- `oracle-test` cleanup disposition;
- confirmation that no production or staging access occurred; and
- one recommendation: ready or not ready for independent Codex re-review.

Keep the third-grant file and Phase A deviation blockers open. Do not accept the
work, approve production provisioning or activation, commit, push or create
another remediation prompt. Stop after the return.
