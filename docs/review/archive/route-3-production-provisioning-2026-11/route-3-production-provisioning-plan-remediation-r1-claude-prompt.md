# Claude prompt — Route 3 production provisioning-plan remediation R1

Date prepared: 2026-10-31  
Owner and acceptance authority: Peter Duscha  
Reviewer after return: Codex  
Target: the uncommitted Route 3 candidate currently in the workspace

## Assignment

Remediate Codex's independent review findings in the Route 3 production
provisioning plan. Produce one exact, reproducible and rollback-complete plan
that Peter can review before deciding whether to authorize provisioning.

Peter made two controlling decisions on 2026-10-31:

1. he confirmed that `/etc/sudoers.d/zz-claude-window` is absent; and
2. he accepted the Phase A stop/order procedural deviation.

Record those decisions in the current authority documents and close the two
corresponding blockers. They do **not** authorize provisioning, installation or
activation. Peter explicitly withholds provisioning authorization until this
plan has passed review.

Correct these six review findings:

1. provisioning and activation are mixed: `install` enables the supervisor,
   an ordinary reboot can then start it, and the same runbook block explicitly
   starts it;
2. the production source, exact version and integrity identity of Python 3.14,
   the SA-2 artifact, the Jeepney wheel and the deployable code are not defined;
3. the deployment is described only as an `rsync` from an unspecified mutable
   checkout, with no immutable revision/artifact, exact exclusions, digest
   verification or staged publication;
4. rollback describes the installed service but not every partial first-time
   provisioning state, including account, linger, sudoers, deployment, venv,
   packages, SA-2 artifact and `tmpfiles.d` prerequisite;
5. privileged installer invocations use ambient `python3` rather than an exact
   interpreter under a sanitized environment; and
6. the runbook and current records still describe the temporary grant and Phase
   A deviation as open.

This is a bounded plan remediation. Do not create a new architecture, change
the accepted Route 3 risk boundary, or execute the plan on production.

## Governing material

Before acting, read completely:

1. `.agents/AGENTS.md`;
2. `docs/implementation-plan.md` using its reading map, especially §0, §14,
   §16, §17 and §20;
3. `docs/review/Handover information`;
4. `docs/operations/disposable-test-server.md`;
5. `docs/project-management/active-delivery-plan.md`;
6. `docs/operations/executor-supervisor-provisioning-runbook.md`;
7. `docs/review/route-3-production-readiness-handback.md`, especially §§5.1,
   6–7 and 9;
8. `docs/review/route-3-production-inspection-remediation-r4-claude-prompt.md`;
   and
9. the six review findings quoted above.

The selected deployment remains
`/opt/freedom-route3/{code,venv}`. The live `freedom-bot`, `freedom-web` and
`freedom-worker` paths and services remain untouched.

## Authority and hard boundary

Peter's act of giving this prompt to Claude authorizes:

- repository documentation and focused test changes required below; and
- full relevant testing on `oracle-test`, including root/systemd, package,
  reboot, failure-injection, rollback and cleanup testing.

It authorizes **no production or staging access of any kind and no production
or staging mutation**. Do not repeat the sudoers observation. Do not create,
inspect, edit or remove a production grant; install Python or a package; create
an account, group, home, linger entry, deployment tree, artifact, policy,
runtime/state path or unit; reload, enable, start, stop or restart a service;
reboot; run Route 3; or perform a migration, cutover or RB-1 outside
`oracle-test`.

Do not read secrets, credentials, `.env`, process environments or arguments, or
player data. If a guard refuses a command, stop rather than routing around it.

## Remediation 1 — define a non-activating provisioning boundary

Split the procedure into explicit authority stages. At minimum distinguish:

1. read-only production preflight;
2. inert prerequisite provisioning;
3. post-provision read-only verification and evidence capture;
4. installation/enablement, if it is not part of the inert stage; and
5. activation, attended acceptance probes and later removal.

The reviewed provisioning stage must have one unmistakable **STOP** point. At
that point:

- the supervisor is not running;
- no Route 3 transient invocation can run;
- an ordinary or maintenance reboot cannot start the supervisor;
- no smoke stop, capture pass, migration or cutover has occurred; and
- the exact state left on the host is listed and can be verified read-only.

The present installer always enables its unit. Therefore do not place
`tools.executor_supervisor_install install` inside the inert provisioning
stage unless the implementation is changed and proved to leave no enabled or
latent auto-start state. Prefer the smaller safe boundary: provision and verify
the prerequisites, stop before installer `install`, and reserve install,
enable, start/reboot and acceptance probes for a later explicit authorization.
If that cannot meet the accepted package contract, explain why and make the
smallest tested installer change necessary; do not silently redefine enabling
as non-activation.

Also avoid creating an effective privileged execution route earlier than
necessary. State exactly when the sudoers grant, the account's running user
manager and the SA-2 artifact become jointly usable. Order the stages so an
unattended interval has the least capability, and name any residual that must
remain for Peter's later decision.

Use headings and executable blocks that cannot reasonably be mistaken for one
continuous authorization. Every state-changing block begins with its required
authority and ends with a reliable status and a stop condition.

## Remediation 2 — define the controlled artifact set

Replace every phrase such as “installed through its own reviewed procedure,”
“the pinned wheel,” “the controlled artifact set,” “the reviewed revision” or
“deploy with rsync” with a reproducible input or an explicit blocking field.

The plan must identify, as applicable:

- the supported production OS/repository source for Python 3.14;
- exact Python packages, architecture and versions, plus the method for
  verifying repository origin and installed-file integrity;
- the exact `/usr/bin/python3.14` identity required by the accepted Route 3
  contract, including how version/digest drift is handled;
- the exact Jeepney wheel filename, version, SHA-256, acquisition/storage
  location and `--no-index --no-deps` installation command;
- the exact SA-2 artifact source, reviewed revision or generated artifact,
  destination, owner/mode and integrity identity;
- the `tmpfiles.d` prerequisite source, destination, owner/mode and integrity
  identity;
- the deployable application revision and a deterministic archive or manifest
  digest that represents the reviewed bytes; and
- the service fragment and every other repository file executed as root or by
  the executor.

Use existing accepted pins and evidence only where they actually govern this
deployment. Do not promote an `oracle-test` observation into a production
source decision without authority. Do not fetch an unpinned artifact during
production execution.

The workspace is uncommitted. Do not invent a commit ID or claim that mutable
bytes are an immutable release. If a final release revision, archive digest,
package source or artifact cannot yet be fixed, make it a named hard preflight
field whose absence returns **NO-GO**, identify who supplies it, and keep the
plan not ready rather than filling it with a placeholder that an operator could
miss. The returned review candidate must make every unresolved value obvious.

## Remediation 3 — make deployment exact and publication safe

Supply the literal deployment procedure rather than a prose `rsync` summary.
It must:

- consume only the controlled artifact set from Remediation 2;
- use a root-only staging area on the same filesystem as the final deployment;
- verify all expected digests before publication;
- reject unexpected files, symlinks in prohibited trees, special files,
  incorrect ownership/mode and secrets or credential-like files;
- state exact inclusion/exclusion behavior for `.env*`, keys, credential JSON,
  `.git`, caches and build/test residue;
- avoid reading or copying the ordinary checkout's secret files;
- prevent a mutable source from changing during copy;
- leave no partially trusted final tree after interruption;
- publish to `/opt/freedom-route3/{code,venv}` through a reviewed staged or
  otherwise transactionally bounded sequence compatible with venv paths; and
- run the existing trust verifier before any later root execution from the
  deployment.

Do not use recursive `chown` or `chmod` as a substitute for source integrity.
If they remain part of publication, bound them to the verified staging tree and
verify the resulting final tree before it becomes executable input.

All operator variables must be assigned from fixed reviewed values, validated
before use and quoted. Destructive cleanup must resolve and verify exact narrow
targets; never use a broad variable, glob, `/`, `~` or a workspace root.

## Remediation 4 — complete rollback for every checkpoint

Add a checkpoint/rollback matrix covering success and failure after every
state-changing step. Capture the pre-existing state first so cleanup removes
only objects created by this operation and never removes a package, account,
file or policy that existed beforehand.

Cover at least:

- Python packages and supporting packages;
- staging and final `/opt/freedom-route3` trees;
- the executor account, primary group, home and user-manager state;
- linger;
- the one-command sudoers drop-in;
- the SA-2 artifact and its parent directory where applicable;
- the `tmpfiles.d` prerequisite and any derived runtime effect;
- the supervisor fragment, wants link and manager reload state;
- runtime/state directories and invocation records;
- a partial first install, `recovery-incomplete` and an unexpected reboot; and
- evidence files created by the procedure.

For each checkpoint state the rollback trigger, exact action, expected status,
verification, escalation condition and whether a reboot is required or
forbidden. Preserve the existing fail-closed rule: never delete ownership
records by hand and never continue after an unknown or `recovery-incomplete`
state.

Distinguish rollback of inert provisioning from removal after activation.
`tools.executor_supervisor_install remove` is not a universal rollback for a
failure that happened before installation.

## Remediation 5 — use exact, sanitized privileged invocations

Replace every privileged `python3 -m tools.executor_supervisor_install ...`
with one reviewed literal invocation using an absolute interpreter, an empty or
explicitly sanitized environment, fixed `PATH`, the required isolation flags
and the trusted code root. The module and its imports must resolve only from
the trusted deployment.

Prove that hostile `PATH`, `PYTHONPATH`, `PYTHONHOME`, user site and working
directory cannot redirect the installer. Preserve the command's real exit
status; no pipeline, `echo` or trailing cleanup command may mask it.

Use the same literal consistently for `verify`, `install`, `verify-ready` and
`remove`, while placing each operation only in its authorized stage.

## Remediation 6 — record Peter's decisions and reconcile authority

Update the live records so they consistently state:

- Peter confirmed `/etc/sudoers.d/zz-claude-window` absent on 2026-10-31;
- Peter accepted the Phase A stop/order deviation on 2026-10-31;
- both blockers are closed;
- the provisioning plan is undergoing remediation/review;
- provisioning, installation and activation remain unauthorized; and
- activation remains a separate decision after any provisioning authorization
  and post-provision verification.

Reconcile at least:

- `docs/review/Handover information`;
- `docs/project-management/status.md`;
- `docs/project-management/active-delivery-plan.md`;
- `docs/implementation-plan.md` §20;
- the top/current decision and RAID entries;
- one new append-only change-log row;
- `docs/review/README.md`;
- the provisioning runbook; and
- the existing production-readiness handback.

Do not rewrite historical observations or claim a command transcript that was
not supplied. Record Peter's decisions as decisions, not as independently
reproduced evidence. Do not require another review merely for those two
documentation corrections; review is required for the materially changed
executable production plan.

## Regression coverage

Add focused tests that extract the literal current runbook blocks and establish
the material plan properties. String-presence assertions alone are
insufficient. Cover at least:

- the provisioning-only path reaches its explicit stop without calling
  installer `install`, enabling, starting, restarting, rebooting, invoking SA-2
  or running a smoke test;
- a reboot at the provisioning stop cannot auto-start the supervisor;
- missing or mismatched artifact identity fails before publication or
  privileged execution;
- the deployment block rejects a mutable/untrusted input, prohibited symlink,
  unexpected file and partial staging state;
- hostile shell/Python environment cannot redirect the installer invocation;
- every installer invocation preserves statuses 0, 10, 12, 13 and 15;
- each created prerequisite has a rollback checkpoint, and rollback refuses to
  remove a simulated pre-existing object;
- partial failure at representative checkpoints converges to the captured
  pre-state or produces one explicit escalation/no-go state; and
- the activation commands are absent from the provisioning block and present
  only behind their own later-authorization heading.

Use deterministic local seams for command extraction and failure injection,
then exercise the exact root/systemd lifecycle on `oracle-test` where it is
material. Do not weaken a production predicate to fit a user-owned test tree.

If no installer implementation changes are needed, do not rerun unrelated bot,
web or Node suites. If the installer or service fragment changes, run its full
focused unit, structural and root/systemd package coverage.

## Scope discipline

Expected files are limited to:

- `docs/operations/executor-supervisor-provisioning-runbook.md`;
- the existing production-readiness handback and the live current-authority
  records listed above;
- focused provisioning-plan/runbook tests; and
- only if the non-activating boundary cannot otherwise be met, the smallest
  installer/service-fragment change plus its direct tests.

Do not redesign the executor, supervisor ownership protocol, SA-2 behavior,
Polkit policy, sudo vector, account model, transient-risk decision, coordinator,
start orchestration, automatic attestation, migration/cutover or RB-1. Do not
create another prompt, handback, evidence dossier or recursive remediation
chain. Update the existing handback once.

## Verification

Synchronize the exact workspace to `oracle-test` using the canonical
secret-excluding command. Run serially with
`TEST_DATABASE_URL=postgresql+psycopg:///freedom_test`:

1. the new or changed provisioning-plan/runbook regression module;
2. `tests/test_production_checklist_item_8.py` and
   `tests/test_production_checklist_item_5b.py`;
3. `tests/test_executor_supervisor_install.py` and
   `tests/test_executor_system_service.py`;
4. if executable package behavior changed,
   `tests/systemd_integration/test_executor_package_host.py` as root with
   `FREEDOM_SYSTEMD_INTEGRATION=oracle-test` and root's normal executable path;
5. directly affected structural/deployment-artifact tests;
6. `bash -n` over every executable shell block added or changed;
7. `.claude/hooks/test_guards.py`; and
8. `git diff --check`.

For literal destructive-plan tests, substitute only an isolated temporary root
on `oracle-test`; never target the real `/opt/freedom-route3`, system sudoers,
accounts or units unless the established disposable-host fixture owns and
cleans those exact test objects. Establish after root testing that no test
account/group, linger file, sudoers fragment, unit, state/runtime path, mount,
artifact or `/opt/freedom-route3` tree remains.

Report every failure, error and skip with reliable status. A documentation-only
authority correction needs no behavioral rerun, but every changed executable
operator block and any implementation change does.

## Required return

Add one concise **Production provisioning-plan remediation R1 return —
2026-10-31** near the top of the existing production-readiness handback. State:

- files and behavior changed;
- the precise provisioning-only stop state;
- whether any effective privileged route exists at that stop;
- the complete controlled artifact identities, or each remaining named hard
  blocker and owner;
- deployment publication and integrity guarantees;
- rollback coverage for partial provisioning;
- how privileged invocations are isolated and status-preserving;
- focused and host-test results, including failures, errors and skips;
- `oracle-test` cleanup disposition;
- confirmation that no production or staging access occurred; and
- one recommendation: ready or not ready for independent Codex re-review.

Do not accept the plan, authorize provisioning or activation, commit, push or
perform production work. Stop after the return.
