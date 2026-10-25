# Claude remediation prompt — Route 3 production-readiness review findings, round 4

Date: 2026-10-23

Status: **ACCEPTED AND AUTHORIZED REMEDIATION PROMPT**

Authority: Peter Duscha, Product Owner and Acceptance Authority

Implementer: Claude

Independent reviewer after return: Codex

Mode: one final bounded in-place correction of the returned candidate; no
production or staging access, inspection or activation

## Assignment

Correct the four remaining findings from Codex's independent re-review of the
third production-readiness remediation:

1. enablement observation still treats every `OSError` as "disabled";
2. checklist item 5b can print a unit's untrusted `Description`;
3. item 5b permits an ambient `ACCOUNT` value to redirect inspection; and
4. current-state headings still describe the third remediation as assigned
   after Claude returned it.

This is a bounded correction in the existing installer, focused tests,
production read-only checklist and current-state documents. It is not a
redesign of the accepted Route 3 topology, privileged vector, role semantics,
authorization policy or residual-risk options. Add the missing regressions,
correct the implementation and inspection method, verify the exact final tree
on `oracle-test`, and update the existing
[`production-readiness handback`](route-3-production-readiness-handback.md) in
place. Do not create another handback or widen the remediation chain.

The candidate remains unaccepted. This prompt makes no transient-risk decision
and authorizes no production or staging login, inspection, installation or
activation, successor slice, coordinator, start orchestration, automatic
attestation, migration/cutover, RB-1, commit or push.

## Required context

Before changing anything, read completely and follow:

1. `.agents/AGENTS.md`;
2. the reading map and §§0, 9, 12 Phase 5.0, 13, 14, 16, 17 and 20 of
   `docs/implementation-plan.md`;
3. `docs/review/Handover information`;
4. `docs/project-management/active-delivery-plan.md`;
5. `docs/operations/disposable-test-server.md`;
6. `docs/operations/executor-supervisor-provisioning-runbook.md`;
7. the original production-readiness assignment and all three earlier
   remediation prompts;
8. the complete current production-readiness handback;
9. `tools/executor_supervisor_install.py`, its complete unit and real-host
   tests, and the installed service fragment; and
10. the current diff, preserving the shared dirty worktree and every unrelated
    change.

Use only synthetic data and the canonical secret-excluding synchronization
procedure. Do not read a real secret or copy real player data.

## Finding 1 — Blocking: an unobservable wants link is treated as disabled

`Installer._enabled()` catches every `OSError` from the wants-link observation
and returns `False`. That conflates a genuinely absent pathname with an I/O or
permission failure and can therefore record, compare or restore an unknown
enablement state as though it were disabled.

Codex reproduced the consequential post-mutation case on `oracle-test`: an
initially disabled recognized old fragment was upgraded, the forward `enable`
created the wants link, every later `readlink` failed with injected `EIO`, and
recovery returned the original `enable-failed`/13 even though the wants link
remained. Earlier bytes, loaded bytes and unit state were restored, but
enablement was neither observed nor restored. An initially enabled case also
returned an ordinary I/O failure even though its original link had never been
successfully observed.

Make enablement observation strict at every upgrade boundary:

- only a genuine `FileNotFoundError` for the exact wants-link pathname means
  disabled;
- only the exact expected symlink target means enabled;
- an I/O or permission error, a non-symlink object, malformed link, or an
  unexpected target is an unavailable/invalid observation, never `False`;
- before any upgrade mutation, an unavailable/invalid observation must produce
  one fixed diagnostic and no fragment, link or manager mutation;
- after an upgrade may have mutated anything, inability to establish or restore
  the exact original enablement is `recovery-incomplete` and exit 15; and
- a verified full restoration still reports the original operation failure and
  permits a later safe retry.

Do not weaken the round-3 strict `ActiveState` boundary. If older call sites
intentionally use a lenient existence check and changing them globally would
alter accepted behavior, introduce a narrowly named strict observation helper
for upgrade capture and verification instead of silently changing unrelated
semantics.

Add deterministic regressions that fail on the reviewed tree and cover at
least:

1. `EIO` or permission failure before mutation: fixed failure and no mutation;
2. initially disabled, forward enable creates the link, later observations
   fail: `recovery-incomplete`/15 and no false restoration claim;
3. initially enabled, restoration-time observation fails:
   `recovery-incomplete`/15;
4. a non-symlink object and an unexpected symlink target at each relevant
   boundary;
5. genuine link absence as the valid disabled state; and
6. a later safe retry from every recoverable result.

Assert disk bytes, manager-loaded bytes, actual link/object state, running
configuration and unit state, not only the returned word. Exercise exit 15
through `main()`.

## Finding 2 — Important: item 5b can print an untrusted unit description

Handback §6 item 5b uses `systemctl --user list-units`. That output includes the
unit `Description`. Codex proved the leak on `oracle-test` by starting a
transient implicated unit whose synthetic description contained
`DECOY_TOKEN_SHOULD_NOT_PRINT`; the token appeared in the checklist output.

Replace this with a secret-safe, explicit allowlist of facts. The corrected
method may emit only the implicated unit identifier and the minimum required
load/active/sub state and safe path metadata. It must not print descriptions,
unit contents, command arguments, environment values or other free-form
manager properties. Preserve reliable status for every query and search; do
not allow a pipeline to hide a failed producer.

Exercise the exact command shape on `oracle-test` with a disposable transient
unit whose description contains the decoy. Prove that the implicated unit and
allowlisted state are reported, every command status is reliable, and the decoy
appears zero times in captured output.

## Finding 3 — Important: ambient `ACCOUNT` can redirect item 5b

Item 5b currently begins `ACCOUNT=${ACCOUNT:-freedom-executor}`. A caller's
ambient `ACCOUNT` can therefore redirect a supposedly dedicated-account
inspection to root or another account.

Hard-code `ACCOUNT=freedom-executor` in the production checklist. If automated
proof needs a disposable account, use a clearly separate test-only copy or
harness substitution; do not expose a production override. Validate the
NSS-derived UID, home, runtime directory and bus address before use, preserve
reliable failure statuses, and ensure a missing or malformed dedicated account
cannot accidentally select `/`, root's home/runtime, or another account.

On `oracle-test`, run the production-shaped method with a conflicting ambient
`ACCOUNT` and prove it still selects `freedom-executor`. Also prove the explicit
test seam against the disposable account without changing the production
command.

## Finding 4 — Important: current-state headings are stale

The active handover, project status and active delivery plan still headline the
third remediation as assigned even though their bodies record its return.
Reconcile all current-state pointers so that, on return, they say the fourth
remediation has returned for independent Codex re-review with the correct date.

Also reconcile implementation-plan §20, the decision and RAID registers,
change log and review index. Preserve historical entries; append superseding
records where the document is append-only. Do not rewrite history as though an
earlier finding or return never occurred.

## Preserved boundary

Do not reopen or redesign:

- the root-controlled system supervisor and dedicated account;
- the account's lingering user manager and one transient unit per invocation;
- durable exclusive ownership before the sole `StartTransientUnit` call;
- recovery that adopts and settles but never launches or retries SA-2;
- the exact privileged SA-2 argv and strict root-only `NOPASSWD` verification;
- OC-1/OC-2/OC-3, one-shot and ambiguous-handoff behavior;
- accepted manager/Polkit, cleanup, backstop, hold, start, stop, consume or
  attest semantics;
- `owner-without-fragment`, removal recovery, strict `ActiveState`, BS-3 or the
  corrected transient inspection-failure analysis; or
- production topology, authorization policy or the transient-risk decision.

If a correct repair requires a different topology, authorization boundary or
accepted role behavior, stop and return the concrete decision instead of
implementing it.

## Required verification

First add focused regressions that demonstrably fail on the reviewed installer,
then make them pass. Synchronize the exact final workspace to `oracle-test`
with the canonical secret-excluding command and run shared-state suites
serially.

At minimum, run and report:

1. the complete installer module, including every new strict-enable-observation
   case;
2. focused CLI checks proving incomplete recovery prints exactly
   `recovery-incomplete` and exits 15;
3. executable shell and host probes for item 5b, including a conflicting
   ambient `ACCOUNT`, invalid NSS results, reliable non-zero statuses and a
   decoy description that appears zero times in output;
4. the complete focused manager/Polkit, cleanup, backstop, hold, consume,
   attest, start, stop, artifact, executor ownership/usermanager/supervisor/
   interrupt/installer/system-service and deployment-artifact set;
5. the complete root `tests/systemd_integration` suite with
   `FREEDOM_SYSTEMD_INTEGRATION=oracle-test`, the pinned wheel and root's own
   documented `PATH`;
6. the canonical bot suite, then the database-enabled web suite with
   `TEST_DATABASE_URL=postgresql+psycopg:///freedom_test` exported and the
   expected skip count checked, then the Foundry Node suite;
7. configured formatter, linter and type checker, or an accurate statement
   that each is not configured; `compileall` over changed Python; and
   `git diff --check`; and
8. a final disposable-host comparison covering accounts/groups/homes, linger,
   sudoers, Polkit/`tmpfiles.d`, units/drop-ins, processes, cgroups, mounts,
   state/run directories, artifacts, deployment copies, decoys and pytest
   residue.

Run bot and web suites serially because they share the disposable database.
State that cited suites ran on `oracle-test`, not the repository host, and that
`TEST_DATABASE_URL` was exported for the web database tests. Report every
failure, error, skip, retry, altered command and infrastructure incident.

A full suite rerun is required after the last executable change. Documentation
edits made afterward require rerunning tree-scanning documentation and
structural checks, not unrelated behavioral suites, unless the edit changes an
executable instruction or interpretation of earlier evidence.

## Documentation and handback

Update the existing production-readiness handback in place with one concise
**fourth review remediation return** section and correct affected earlier text
so the document contains no contradictory recovery or inspection claims.
Include:

- the strict enablement-observation correction and its before-/after-mutation
  regressions;
- the fixed-account, allowlisted-output item 5b method and disposable-host
  proofs;
- files changed;
- material commands and reliable results, including failures and skips;
- any exact-path host probes and the final restoration result;
- remaining production risks and gates; and
- confirmation that nothing was accepted, committed, pushed or touched in
  production or staging.

Reconcile the current-state pointers named in Finding 4. End with a concrete
conclusion and recommendation for independent Codex re-review. Stop after the
handback. Codex re-reviews the exact final tree and Peter decides the transient
risk and acceptance afterward.
