# Claude prompt — Route 3 production inspection completion and prerequisite remediation

Date prepared: 2026-10-25  
Owner and acceptance authority: Peter Duscha  
Target: the production host whose active `freedom-bot.service` has
`WorkingDirectory=/opt/freedom-blades/platform`

## Assignment

Act as the implementing production operator for one bounded Route 3 follow-up.
Complete the root-only parts of the already-authorized production inspection,
then—only if every pre-mutation gate below is satisfied—remediate the known
production prerequisites to a **provisioned but uninstalled and inactive**
state. Return one concise handback for independent Codex review.

This is not another design or remediation loop. Use the accepted implementation
and runbook. Correct a newly demonstrated defect only if it is necessary for
this assignment and can be proved on `oracle-test`; otherwise stop once with a
precise blocker and recommended disposition.

Peter's act of giving you this prompt authorizes the root-assisted read-only
inspection. It authorizes production writes described below only after Peter
has supplied, in this same assignment, the maintenance window, rollback owner,
evidence-retention period and an approved Python 3.14/artifact source. If any of
those four facts is absent, finish the read-only work and ask once for the
missing facts before making a production change. Never request or accept a
password, token, `.env` content or other secret in chat.

## Governing material

Before acting, read completely:

1. `.agents/AGENTS.md`;
2. `docs/implementation-plan.md` using its reading map, especially §0, §16 and
   §20 plus the Route 3 material;
3. `docs/review/Handover information`;
4. `docs/operations/disposable-test-server.md`;
5. `docs/review/route-3-production-readiness-handback.md`, especially §§5.2,
   6, 6.1 and 7–10; and
6. `docs/operations/executor-supervisor-provisioning-runbook.md`.

Treat the current documents as authority and the archived remediation chain as
history. Preserve unrelated workspace changes. Do not commit, push, rewrite
Git history or create another prompt.

## Hard boundary

- Do not read, print, copy or modify `.env`, service-account JSON, credentials,
  tokens, database URLs, process environments, process argument strings or real
  player data.
- Do not run production application tests, migrations, database writes,
  Discord/Sheets/Foundry calls or capture-pass work.
- Do not start or install
  `freedom-blades-executor-supervisor.service`; the accepted installer enables
  the unit, so even an apparently inactive install would arm it for the next
  boot. Leave `tools.executor_supervisor_install verify` at the expected
  `not-installed` result.
- Do not start any `rp11-*` or `freedom-executor-stop-*` unit, invoke the SA-2
  vector, activate a Polkit grant, run a migration/cutover, or execute RB-1.
- Do not restart, reload, stop, replace or reconfigure `freedom-bot`,
  `freedom-web`, `freedom-worker`, Caddy, Foundry or PostgreSQL.
- Do not chown or chmod the live working checkout in place. The existing
  checkout is not a safe executor trust root and is also the live bot's working
  directory. Any exact-path deployment must use the reviewed staged-swap and
  rollback procedure below, inside the named window.
- Do not add an apt repository, PPA, package signing key, unpinned network
  dependency or locally compiled interpreter. Use only the Python 3.14 and SA-2
  artifact sources Peter explicitly approves. If no approved source is named,
  that is a stop, not permission to improvise.
- A failed or incomplete fact is a finding, never a pass. Do not weaken an
  installer/verifier check or widen sudo/Polkit policy to make production pass.
- Activation remains a separate maintainer decision after independent review.

## Phase A — finish the root-only inspection before any write

Run handback §6 items 4 and 6 from a root-capable session, using its exact
secret-safe output discipline.

1. Validate sudo syntax with `visudo -c`.
2. Recursively enumerate every effective sudoers include and includedir,
   including custom transitive paths. Record path, owner, mode and hash only.
3. Read the files privately and record conclusions, not contents:
   `env_reset` remains effective; no dangerous `env_keep`, `env_check` or
   `env_delete`; no `SETENV`, `!env_reset`, weakened `secure_path`, scoped
   executor default, alias expansion or grant that would reach
   `freedom-executor`. Since the account is initially absent, explicitly
   distinguish universal/alias grants from group membership that does not yet
   exist.
4. Enumerate every Polkit rules directory reported by the installed package.
   Privately classify every `*.rules` file for systemd actions, broad
   `YES`/`AUTH_*`, subject/unit tests and identities that could cover the future
   account. Record metadata, hashes and conclusions only; never dump rules.
5. Reconcile these conclusions with F-1 through F-3 and handback §6.1.

Stop without mutation if syntax fails, a policy cannot be enumerated, a broad
or ambiguous grant reaches the future account, a relevant systemd Polkit rule
already exists, or any result cannot be classified confidently. Return that
single blocker with the exact non-secret fact and recommended correction.

## Phase B — pre-mutation checkpoint

Before the first production write, record all of the following in the working
handback:

- Peter's named maintenance window, rollback owner and evidence-retention
  period;
- the approved, pinned provenance for `/usr/bin/python3.14`, the Python 3.14
  venv tooling and the reviewed SA-2 artifact;
- current boot id, mounts, capacity, active state and start timestamps of the
  existing Freedom services, and metadata/hashes—not content—of every file that
  this assignment may replace;
- the exact reviewed source-tree identity to deploy and a secret-excluding
  manifest;
- a rollback location on the same filesystem with sufficient capacity; and
- an explicit confirmation that no Route 3 unit/account/process/runtime state
  already exists beyond the known absent state.

The rollback owner must be able to restore the prior exact-path deployment and
verify the existing services. Do not call a Git checkout or the dirty working
tree a rollback. Do not move, overwrite or change ownership of the only copy.

If the live bot cannot tolerate an atomic exact-path swap without a restart,
or if the canonical repository must remain writable at that exact path, stop
and report the path-coexistence conflict. Do not silently convert the working
repository into a root-owned deployment.

## Phase C — bounded prerequisite remediation

Proceed only after Phases A and B are complete and clean. Follow the accepted
runbook rather than inventing equivalent commands.

1. Stage a secret-free, `.git`-free copy of the exact reviewed source and the
   pinned Python 3.14 venv on the same filesystem. Validate the complete trust
   scope before it can replace anything: root ownership, no group/other write,
   permitted object types and links, bounded trees, correct interpreter/link
   chain, one Python 3.14 site-packages directory and the pinned `jeepney` tree.
2. Preserve the current exact-path deployment as the rollback copy, then use
   the pre-agreed atomic swap. Do not restart an existing service. Immediately
   verify its active state and start timestamp are unchanged and the new path
   contains the intended bytes. On any discrepancy, invoke the agreed rollback
   and stop.
3. Install and verify the accepted `tmpfiles.d` prerequisite. If its
   boot-order proof requires reboot, use only the named window and rollback
   owner; verify all pre-existing services after boot before continuing.
4. Create only the fixed `freedom-executor` account/group/home and linger state
   from runbook §2. It must have a locked password, no SSH keys, a non-login
   shell and no supplementary privileged or code-writing group.
5. Install only the reviewed fixed SA-2 artifact and exact one-command sudoers
   entry from runbook §3. Validate the drop-in with `visudo` before relying on
   it. Do not invoke the command.
6. Provision the required fixed state/runtime parents exactly as documented,
   but do not create or activate a capture-pass rule and do not install or
   enable the supervisor service.

If any forward step fails, follow the runbook's recovery/rollback semantics.
Never continue from an unverified partial state. Record the actual recovery
status without claiming exact restoration unless it was verified.

## Phase D — verification and stopping point

Repeat the complete handback §6 checklist from the final production state,
including item 5b in the dedicated account's own manager context, the effective
sudo classification, Polkit classification/effect, complete trust scope,
tmpfiles ordering, capacity, logging and process exclusivity.

Additionally verify:

- all pre-existing production services retain their pre-window active state and
  start timestamps unless the approved reboot necessarily changed timestamps;
  after a reboot, verify they are healthy without exposing configuration;
- no Route 3 capture, stop or supervisor process/unit is active;
- no transient Polkit rule or activation record exists;
- `python3 -m tools.executor_supervisor_install verify` returns the expected
  `not-installed` status, proving the supervisor has not been armed;
- the executor account cannot run `/bin/true` through sudo; and
- its effective sudo listing contains exactly the fixed root/NOPASSWD SA-2
  vector, while the privately inspected Defaults remain safe.

Do not run `install`, `verify-ready`, a synthetic stop or any capture pass.
Stop with the production host provisioned, verified and inactive.

## Testing and evidence

Production inspection establishes host facts; it is not a place to exercise
failure injection. If repository code or executable instructions must change,
first reproduce the defect, implement the smallest correction, and run all
relevant focused and full suites serially on `oracle-test` using the canonical
environment and exported `TEST_DATABASE_URL`. Repeat only the affected
secret-safe production verification after independent review of that code
change. If no executable repository content changes, do not rerun behavioral
suites merely to decorate the handback.

Maintain reliable exit-status propagation. Keep terminal transcripts and
scratch outside the repository, remove bounded scratch at the end, and report
conclusions rather than bulk output. Never report a skipped, unreadable or
permission-denied check as passed.

## Required handback

Update the existing
`docs/review/route-3-production-readiness-handback.md` with one dated production
remediation return and reconcile only the live handover/status/delivery-plan
and concise decision/change/RAID records. Do not create another remediation
prompt, review chain or evidence dossier.

The handback must state:

1. authorization actually received, operator, window, rollback owner and
   evidence-retention period;
2. root-only sudo/Polkit conclusions and hashes/metadata without policy text;
3. exact production changes and exact sources/provenance;
4. pre/post existing-service health and whether a reboot occurred;
5. complete final §6 disposition, including every non-zero status;
6. rollback/recovery actions and what was independently verified;
7. repository files changed, tests actually run with pass/fail/skip counts, or
   why no behavioral suite was required;
8. confirmation that the supervisor and capture path remain uninstalled or
   inactive as required, and that no migration/cutover ran; and
9. a single recommendation: ready or not ready for independent Codex review of
   a later activation plan.

Do not claim production readiness merely because provisioning completed.
Independent Codex review and a separate Peter activation instruction remain
mandatory.
