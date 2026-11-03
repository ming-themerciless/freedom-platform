# Claude prompt — Route 3 production provisioning-plan remediation R7

Date prepared: 2026-11-02  
Owner and acceptance authority: Peter Duscha  
Implementer: Claude  
Reviewer after return: Codex  
Target: the uncommitted Route 3 production provisioning-plan R6 candidate currently in the workspace

## Assignment

Complete one narrow documentation correction of the R6 return. Do not redesign
the provisioning plan, change block R, change tests, or repeat the completed
package-manager test campaign.

Codex's independent review initially observed the workspace before Claude's
late R6 return and cleanup updates had landed. Those two reported conditions
are now resolved in the shared workspace:

- the canonical R6 return and R6 live-current pointers are present; and
- a subsequent read-only check of `oracle-test` found no attributable
  `frt-plan-*`, `frt-r5-*`, `frt-r6-*`, `/opt/freedom-route3*` or
  `/root/route3-*` path, no package hold, a clean `dpkg --audit`, and no
  relevant pytest/apt/dpkg process.

The late update nevertheless left two direct documentation inconsistencies:

1. runbook Part P is still headed **"R4 remediation, 2026-11-01"**, although
   the current candidate and records correctly identify the R6 return; and
2. the R6 handback says every non-28 wrapper message "never mentions status
   28", while the unchanged literal message accurately says the result is
   **"not a status-28 package/hold result"**. The material claim is that a
   non-28 result does not print or receive the status-28 attended-recovery
   explanation, not that the characters `status-28` are absent.

Correct those statements, verify the current pointers and cleanup facts, and
return the same R6 candidate for independent Codex re-review. The candidate
remains **NO-GO**. Provisioning, installation and activation remain
unauthorized.

## Governing material

Before acting, read completely:

1. `.agents/AGENTS.md`;
2. `docs/implementation-plan.md` using its reading map, especially §0, §13,
   §14, §16, §17 and §20;
3. `docs/review/Handover information`;
4. `docs/operations/disposable-test-server.md`;
5. `docs/project-management/active-delivery-plan.md`;
6. `docs/operations/executor-supervisor-provisioning-runbook.md`, especially
   the Part P heading and block R's final wrapper;
7. `docs/review/route-3-production-readiness-handback.md`, especially the R6
   return; and
8. `docs/review/route-3-production-provisioning-plan-remediation-r6-claude-prompt.md`.

The selected deployment remains `/opt/freedom-route3/{code,venv}`. The live
`freedom-bot`, `freedom-web` and `freedom-worker` paths and services remain
untouched.

## Authority and hard boundary

Peter's act of giving this prompt to Claude authorizes:

- the two focused repository documentation corrections below; and
- read-only confirmation of the already-clean `oracle-test` state if needed.

It authorizes **no production or staging access or mutation** and no new
package transaction on any host. Do not provision, install, remove, purge,
hold, unhold, activate, restart or reboot anything. Do not create or remove an
account, grant, unit, policy, deployment, artifact or runtime path. Do not run
Route 3, a migration, a cutover or RB-1. Do not read secrets, credentials,
`.env`, process environments or arguments, or player data.

## Preserve the accepted R5/R6 safety direction

Do not change any executable block or test. In particular:

- R never removes, purges, autoremoves, downgrades, holds or unholds a package;
- package and hold differences remain the attended status-28 boundary;
- `apt.txn` and `apt.effects` remain diagnostic observations only;
- status 0 means the pre-state was restored;
- status 28 alone carries the package/hold attended-recovery explanation;
- every other non-zero status is preserved and reported as itself;
- release fields remain `UNSET`; and
- provisioning, installation and activation remain unauthorized.

## Required correction 1 — current runbook heading

Change the Part P heading in
`docs/operations/executor-supervisor-provisioning-runbook.md` so that it
identifies the current cumulative R6 remediation candidate and date rather
than R4. Preserve the existing NO-GO wording and every executable byte below
the heading.

Do not broadly replace historical R4 references. Historical R1–R5 returns and
their descriptions remain evidence.

## Required correction 2 — exact wrapper description

In the R6 return in
`docs/review/route-3-production-readiness-handback.md`, correct the description
of the non-28 wrapper output to match the literal text:

- it reports the actual status;
- it explicitly distinguishes that result from the status-28 package/hold
  result;
- it does **not** print the status-28 attended-recovery explanation; and
- it preserves the original status.

Remove or replace the inaccurate claim that it "never mentions status 28".
Do not change the wrapper merely to make the prose true. Do not alter the
reported 309 / 51 / 315 results or claim another test run.

## Required verification

After the documentation edits:

1. search the live current-authority records and confirm they identify R6 as
   returned for independent review, while historical R1–R5 text remains
   historical;
2. confirm the Part P heading identifies R6 and retains NO-GO;
3. compare the R6 handback's wrapper description with the literal wrapper;
4. run `git diff --check`;
5. inspect the focused diff for accidental executable, test, authority or
   historical-evidence changes; and
6. if you repeat the disposable-host cleanup check, keep it read-only and
   report the result accurately. Do not remove uncertain artifacts.

No behavioral suite rerun is required or useful for these documentation-only
corrections. The completed uncontaminated R6 results remain the evidence for
the unchanged executable tree. If any executable or test file changes, stop
and return the conflict instead of expanding this assignment.

## Return

Do not add another recursive handback section or claim a new behavioral test
campaign. Correct the existing R6 return in place and give one concise return
stating:

- the two documentation corrections made;
- the files changed;
- the pointer/search and `git diff --check` results;
- whether a read-only `oracle-test` cleanup confirmation was repeated;
- that no executable or test file changed;
- that no production or staging access occurred;
- that release fields remain `UNSET` and the plan remains NO-GO; and
- that provisioning, installation and activation remain unauthorized.

Return the corrected R6 candidate for independent Codex re-review. Do not
claim acceptance, finding closure or provisioning authorization. Do not
commit or push.

