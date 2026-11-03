# Claude prompt — Route 3 production-inspection record remediation

Date prepared: 2026-10-25  
Owner and acceptance authority: Peter Duscha  
Reviewer after return: Codex  
Target record: [`route-3-production-readiness-handback.md`](route-3-production-readiness-handback.md), especially §6.2

## Assignment

Remediate the three blocking findings from Codex's independent review of the
2026-10-25 production-remediation return. This is a bounded evidence and
current-state reconciliation task. Preserve the production no-go and do not
resume provisioning, install or activate Route 3.

The findings to close are:

1. the canonical handover, status, delivery plan, implementation-plan §20 and
   concise decision/change/RAID/review-index records still describe the earlier
   unprivileged inspection and contradict §6.2;
2. the temporary production root grant has no auditable final disposition; and
3. the return does not reconcile the mandatory Phase A stop after the initial
   non-zero `visudo -c` with the later approved `chmod 0440`, which was a
   production mutation before the recorded Phase B checkpoint.

Return the corrected existing handback for one independent Codex re-review. Do
not create another prompt, handback, evidence dossier or recursive review
chain.

## Governing material

Before acting, read completely:

1. `.agents/AGENTS.md`;
2. `docs/implementation-plan.md` using its reading map, especially §0, §14,
   §16, §17 and §20;
3. `docs/review/Handover information`;
4. `docs/operations/disposable-test-server.md`;
5. `docs/review/route-3-production-readiness-handback.md`, especially its
   prelude and §§5.2, 6.1, 6.2, 7 and 9;
6. `docs/review/route-3-production-inspection-remediation-claude-prompt.md`;
   and
7. Codex's three findings quoted in this assignment.

Current-state documents outrank historical summaries, but do not silently
rewrite the historical §6.1 observation. Add a superseding current statement
where needed.

## Authority and hard boundary

Peter's act of giving this prompt to Claude authorizes:

- repository documentation changes required by this prompt; and
- secret-safe, read-only production checks narrowly necessary to establish
  whether the temporary root grant still exists and to record its metadata and
  effective disposition.

It does **not** authorize any production write. In particular:

- do not create, edit, chmod, chown, move or remove a sudoers file;
- do not extend, renew or replace the temporary root grant;
- do not install Python, packages, artifacts, accounts, linger state,
  `tmpfiles.d` fragments, units or policy;
- do not start, stop, restart, reload, enable or disable any service or unit;
- do not touch the live checkout, either venv, application configuration,
  database, Discord, Sheets, Foundry or player data;
- do not run Route 3, the supervisor installer, a capture pass, migration,
  cutover or RB-1; and
- never read or print `.env`, credentials, tokens, process environments,
  process argument strings, policy contents or real player data.

If the temporary grant still exists or its disposition cannot be proved
read-only, stop production work. Record the exact non-secret blocker and ask
Peter for a separate, narrowly scoped removal instruction. Do not remove it
under this prompt. If a guard refuses a command, stop rather than routing
around it.

## Remediation 1 — establish the temporary-grant disposition

Use contemporaneous operator evidence first. If a production check is needed,
inspect only the specifically identified temporary sudoers drop-in and the
mechanism that was intended to expire it. Do not enumerate or print unrelated
policy again.

Record in §6.2, without policy content or a reusable privilege recipe:

- the drop-in's exact path or, if revealing the path would itself be unsafe, a
  stable non-secret identifier sufficient for an operator to locate it;
- owner, group, mode and a shortened SHA256 metadata fingerprint;
- the grant's narrowly summarized subject and command scope;
- the expiry/removal mechanism and its intended deadline in UTC;
- the read-only command statuses used to determine final state;
- whether the file is absent, still present, or unobservable;
- whether the effective grant is absent, still effective, or unobservable;
  and
- the observation time in UTC and the operator who made it.

Do not call a timer or intended expiry proof of removal. Closure requires a
read-only observation that the file and effective grant are absent. If either
is present or cannot be established, the disposition remains open and the
overall recommendation remains no-go.

Also state whether the temporary grant was created by Peter outside Claude's
operation or by Claude under instruction, and distinguish that creation from
the later `foundry-bot` mode correction.

## Remediation 2 — reconcile the Phase A stop and production mutation

Do not manufacture retrospective authority. Inspect the contemporaneous
assignment record and operator evidence and write one precise account:

- `visudo -c` initially returned non-zero because
  `/etc/sudoers.d/foundry-bot` was mode `0644`;
- the original prompt required stopping without mutation on syntax failure and
  required the Phase B checkpoint before the first production write;
- Peter later approved the specific `chmod 0440` correction; and
- whether Peter's later message explicitly superseded both the Phase A stop
  and the Phase B ordering requirement.

If the evidence contains an explicit superseding instruction, cite its date,
scope and non-secret wording concisely. Then record the pre-change metadata,
post-change metadata, unchanged content hash, command status, existing-service
health and absence of reboot/restart.

If the evidence proves only approval of the chmod but does **not** explicitly
supersede the mandatory stop/order, say so. Classify it as a procedural
deviation that remains open for Peter's acceptance or rejection; do not call
Phase A fully compliant and do not claim the finding closed merely because the
resulting mode is correct.

Correct the §6.2 heading and prose so that a production mutation is never
described as part of a wholly read-only phase. Preserve §6.1 as the earlier
unprivileged observation.

## Remediation 3 — reconcile every current-state authority

Update only the existing concise current-state records required by the first
assignment:

- `docs/review/Handover information`;
- `docs/project-management/status.md`;
- `docs/project-management/active-delivery-plan.md`;
- `docs/implementation-plan.md` §20;
- the top/current entries of
  `docs/project-management/decision-register.md` and
  `docs/project-management/raid-register.md`;
- one new append-only superseding row in
  `docs/project-management/change-log.md` (do not alter the older row); and
- `docs/review/README.md`.

They must agree on these facts:

- Peter gave the follow-up assignment and supplied the named operational
  prerequisites;
- root-assisted sudoers and private-Polkit classification completed;
- the approved `foundry-bot` mode change was the only operator production
  mutation beyond Peter's temporary-grant mechanism;
- Phase B found the live-path coexistence conflict and Phase C did not begin;
- no Python, executor account, Route 3 artifact, policy, runtime/state path,
  unit or supervisor was provisioned or installed; no service was restarted;
  no migration/cutover ran;
- provisioning and activation remain no-go;
- the temporary grant's verified final disposition, or the fact that it
  remains an open blocker;
- the Phase A stop/order disposition, including any still-open procedural
  deviation; and
- the next gate is a maintainer architecture decision about a distinct trusted
  deployment root/venv or not deploying Route 3 on this host, plus closure of
  any grant or procedural finding. It is **not** another root-assisted reading
  of sudoers/Polkit, because that work has completed.

Do not imply that the follow-up prompt is still merely proposed. Do not say no
production state changed. Do not broaden the authorization for provisioning
or activation.

## Verification

This task changes documentation only. Do not rerun product, database, Node or
root/systemd suites. Run focused, non-mutating checks sufficient to establish:

1. `git diff --check` is clean;
2. every changed Markdown link resolves locally;
3. searches of the live current-state records find no surviving assertion that
   root sudoers/private-Polkit inspection is incomplete, the follow-up prompt
   is merely proposed, the operational names are still missing, or no
   production state changed;
4. searches find no assertion that provisioning or activation is authorized;
5. the earlier §6.1 historical observation remains clearly dated and is not
   silently rewritten; and
6. repository status and the exact files changed are reported.

If a read-only production check is performed, report every command's reliable
status and the non-secret conclusion. Do not paste terminal transcripts or
policy contents.

## Required return

Update the existing handback with one concise dated remediation return at the
top of the current production material, then reconcile the listed current-state
records. The return must state:

- files changed;
- the temporary grant's verified disposition and observation time, or the
  unresolved blocker;
- the Phase A stop/order disposition and whether Peter must still accept a
  procedural deviation;
- exact production checks performed and their statuses, with confirmation that
  no production write occurred during this remediation;
- documentation checks and actual results;
- remaining risks and gates; and
- one recommendation: ready or not ready for independent Codex re-review.

Do not accept the work, approve production, commit, push, or activate anything.
Stop after the return.
