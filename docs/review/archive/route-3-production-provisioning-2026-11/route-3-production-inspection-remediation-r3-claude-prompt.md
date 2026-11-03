# Claude prompt — Route 3 current-authority and trusted-checklist remediation

Date prepared: 2026-10-29  
Owner and acceptance authority: Peter Duscha  
Reviewer after return: Codex  
Target: the uncommitted Route 3 production-readiness candidate currently in the workspace

## Assignment

Remediate the three findings from Codex's independent review of the current
tree:

1. the active handover and other current-state authorities disagree about the
   third temporary root grant and the already-selected separate Route 3
   deployment root;
2. production checklist item 8 still executes `tools.polkit_tmpfiles` from the
   mutable live checkout rather than the trusted Route 3 deployment; and
3. changing §6's checklist paths in place made the historical §6.1 production
   result appear to have come from checks that did not exist when it ran.

This is one bounded remediation of the existing return. Preserve the production
no-go. Return the same handback for independent Codex re-review. Do not create
another prompt, handback, evidence dossier or recursive review chain.

## Governing material

Before acting, read completely:

1. `.agents/AGENTS.md`;
2. `docs/implementation-plan.md` using its reading map, especially §0, §14,
   §16, §17 and §20;
3. `docs/review/Handover information`;
4. `docs/operations/disposable-test-server.md`;
5. `docs/review/route-3-production-readiness-handback.md`, especially §§5.2,
   6, 6.1 and 6.2;
6. `docs/operations/executor-supervisor-provisioning-runbook.md`;
7. `docs/review/route-3-production-inspection-remediation-r2-claude-prompt.md`;
   and
8. Codex's three findings quoted by this assignment.

The latest explicit Peter decision in the current tree controls: the Route 3
direction is a distinct trusted deployment at
`/opt/freedom-route3/{code,venv}`. That decision authorizes reversible
implementation and full `oracle-test` testing, not production provisioning,
installation or activation.

## Authority and hard boundary

Peter's act of giving this prompt to Claude authorizes:

- the repository changes required below;
- full relevant testing on `oracle-test`, including root/systemd and cleanup;
  and
- secret-safe, narrowly scoped **read-only** production checks needed to
  establish the third temporary grant's final disposition.

It does **not** authorize any production write. In particular:

- do not create, renew, edit, chmod, chown, move or remove a sudoers file;
- do not create or extend a temporary grant or timer;
- do not provision `/opt/freedom-route3`, Python, a venv, an account, linger,
  an artifact, `tmpfiles.d`, Polkit, state/runtime paths or a unit;
- do not install, start, stop, restart, reload, enable or disable a service;
- do not run a capture pass, supervisor install/remove, migration, cutover or
  RB-1;
- do not touch the live application checkout, venvs, configuration, database,
  Discord, Sheets, Foundry or player data; and
- never read or print `.env`, credentials, tokens, policy contents, process
  environments, process arguments or real player data.

If the grant file or an effective broad grant is still present, or its state
cannot be proved read-only, record the blocker and stop production inspection.
Do not remove it under this prompt. A guard refusal is a stop condition.

## Remediation 1 — close or accurately carry the third-grant state

The handback records that Peter created a third grant at approximately 18:18
UTC on 2026-10-25, using `/etc/sudoers.d/zz-claude-window`, with a timer deadline
of 21:18:45 UTC. A deadline or vanished timer is not proof that the file was
removed.

Use contemporaneous evidence first. If needed, perform only the narrow
read-only checks authorized above. Record:

- observation time and operator;
- reliable status for each command;
- whether the named file is absent, present or unobservable;
- whether `foundry` has any effective broad passwordless grant, absent,
  present or unobservable;
- timer/service final state, clearly labelled supporting evidence rather than
  proof of file removal; and
- whether the item is closed or remains an explicit blocker.

Do not publish policy contents or a reusable privilege recipe. A concise
subject/scope classification and metadata are sufficient.

Reconcile every live authority to the same state:

- `docs/review/Handover information`;
- `docs/project-management/status.md`;
- `docs/project-management/active-delivery-plan.md`;
- `docs/implementation-plan.md` §20;
- the top/current entries in the decision and RAID registers;
- a new append-only superseding change-log row; and
- `docs/review/README.md`.

All must also say that Peter selected the distinct
`/opt/freedom-route3/{code,venv}` direction and that it has been implemented and
rehearsed only on `oracle-test`. Remove stale statements that the architecture
decision is still pending, that the third grant is currently known absent, or
that the next action is to move the live services off the old paths. The new
design deliberately leaves those services untouched.

Do not close or erase the separately open Phase A stop/order deviation unless
Peter explicitly accepts or rejects it. Do not infer acceptance from this
assignment.

## Remediation 2 — make checklist item 8 use trusted code

After provisioning, every root-executed Route 3 tool must come from the
root-owned deployment, never the mutable live checkout. Correct production
checklist item 8 and the provisioning runbook so the post-provision verification
executes the reviewed `tools.polkit_tmpfiles` implementation from
`/opt/freedom-route3/code` with a fixed interpreter and sanitized environment.

Requirements:

- no import or executable-code path may resolve through
  `/opt/freedom-blades/platform`, its venv, user site-packages, `PYTHONPATH`,
  `PYTHONHOME` or an ambient working directory;
- use the fixed Python 3.14 interpreter approved by the Route 3 package and
  isolation flags appropriate to loading the trusted local package;
- preserve `polkit_tmpfiles verify` behavior and reliable exit status;
- before provisioning, the checklist must report the trusted deployment as
  absent/incomplete rather than falling back to the mutable checkout;
- do not weaken source-fragment, ownership, mode, override, boot-order or
  runtime-directory verification; and
- do not make the production checklist itself an installation instruction.

Add focused regression coverage that extracts the actual checklist/runbook
command and proves it cannot import from a hostile old checkout or hostile
Python environment. Include at least:

- trusted deployment present: the expected trusted module is executed;
- trusted deployment absent: fail closed with no old-checkout fallback;
- hostile ambient `PYTHONPATH`, `PYTHONHOME`, user site and working directory:
  none redirects execution; and
- the invoked verification command's non-zero status remains visible and is
  not converted into a pass.

Choose the smallest implementation that meets those requirements. If Python's
normal `-I` module-search behavior prevents loading the trusted package, use an
explicit, reviewed entry-point shape that names the trusted file/package
without reopening ambient path injection. Prove the exact chosen shape in the
tests.

## Remediation 3 — restore historical §6.1 reproducibility

Do not leave §6.1 saying that the modified checklist “above” produced the old
inspection result.

Preserve both truths explicitly:

1. the 2026-10-25 §6.1 inspection used the old
   `/opt/freedom-blades/platform` and
   `/opt/freedom-blades/runtime/venv-web` trust-scope checks and produced the
   recorded counts; and
2. the prospective/post-provision checklist now targets
   `/opt/freedom-route3/{code,venv}`.

Use the smallest non-duplicative structure that remains executable and
auditable. Acceptable approaches include a clearly labelled historical path
block adjacent to §6.1 plus a separately labelled current checklist, or a
versioned path-parameter record whose exact historical and current literal
values are both shown. Do not rewrite the old result as if the new paths were
inspected. Do not revive obsolete authority.

Update checklist extraction tests so they select the current executable block
unambiguously and also assert that §6.1 retains the old literal paths and is
labelled historical. The historical block must never become an instruction to
run against production now.

## Scope discipline

Keep the existing separate-root implementation unless a focused test exposes a
real defect. Do not redesign the supervisor, installer recovery, sudo vector,
Polkit policy, account model, transient-risk decision or bounded-use policy.

Expected implementation files are limited to:

- the handback and listed current-state records;
- `docs/operations/executor-supervisor-provisioning-runbook.md`;
- checklist-focused tests, preferably
  `tests/test_production_checklist_item_5b.py` or one narrowly named companion;
  and
- only if required for a safe trusted entry point, one small dedicated
  operator wrapper plus its focused test.

Changes to the supervisor, installer lifecycle, unit hardening, SA-2 artifact,
application behavior or production services are outside this remediation.

## Verification

Synchronize the exact workspace to `oracle-test` using the canonical
secret-excluding command. Run serially:

1. the new/changed checklist regression module;
2. `tests/test_executor_supervisor_install.py` and
   `tests/test_executor_system_service.py`;
3. `tests/systemd_integration/test_executor_package_host.py` as root with
   `FREEDOM_SYSTEMD_INTEGRATION=oracle-test` and root's normal executable path;
4. the directly affected structural/deployment-artifact tests;
5. `bash -n` over the extracted current checklist;
6. `.claude/hooks/test_guards.py`; and
7. `git diff --check`.

Use `TEST_DATABASE_URL=postgresql+psycopg:///freedom_test` for pytest even when
the focused modules do not currently need the database. Do not run bot, web or
Node full suites merely to decorate this bounded correction unless executable
product code outside the checklist entry point changes. If a standard suite is
run, report every failure, error and skip honestly.

Codex's 2026-10-29 review of the exact pre-remediation tree reproduced **126
passed, 2 failed** in `tests/web/test_p3_4_static_assets.py` plus
`tests/test_deployment_artifacts.py`: the previously disclosed evidence-harness
allowlist failure and the tree-dependent test that requires an untracked
directory. Do not repeat the older **127 passed, 1 failed** figure as evidence
for the remediated tree. Report the new result and either establish a meaningful
accepted/pristine-baseline comparison for every failure or classify it as an
unresolved failure; do not call a failure pre-existing merely because an older
handback did.

After the root host module, establish that `oracle-test` has no
`/opt/freedom-route3`, mount, account, sudoers fragment, unit, state/runtime
directory or test artifact left by the run.

## Required return

Update the existing production-readiness handback with one concise dated
remediation return and reconcile the live records listed above. State:

- behavior and files changed;
- the third grant's verified final disposition or exact unresolved blocker;
- that the Phase A deviation remains open unless Peter separately decided it;
- the selected separate-root decision and the actual next gate;
- how current checklist item 8 is anchored to trusted code and fails closed;
- how §6.1's historical path/result relationship is preserved;
- production checks actually performed, reliable statuses, and confirmation
  that this remediation made no production write;
- every test/check result, including failures, errors and skips;
- `oracle-test` cleanup disposition; and
- one recommendation: ready or not ready for independent Codex re-review.

Do not accept the work, approve production provisioning or activation, commit,
push or perform a production mutation. Stop after the return.
