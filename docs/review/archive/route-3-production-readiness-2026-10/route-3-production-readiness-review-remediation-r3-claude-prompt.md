# Claude remediation prompt — Route 3 production-readiness review findings, round 3

Date: 2026-10-22

Status: **ACCEPTED AND AUTHORIZED REMEDIATION PROMPT**

Authority: Peter Duscha, Product Owner and Acceptance Authority

Implementer: Claude

Independent reviewer after return: Codex

Mode: one bounded correction of the returned production-readiness candidate;
no production or staging access, inspection or activation

## Assignment

Correct the three remaining findings from Codex's independent re-review of the
second production-readiness remediation. Two defects still let an upgrade
report the original failure even though restoration was not fully verified;
the production checklist also enumerates the invoking operator's user-unit
paths instead of the dedicated executor account's paths.

This is one bounded correction in the existing installer and checklist, not a
redesign of the accepted Route 3 topology, privileged vector, role semantics,
authorization policy or residual-risk options. Add the missing regressions,
correct the implementation and production inspection method, verify the exact
final tree on `oracle-test`, and update the existing
[`production-readiness handback`](route-3-production-readiness-handback.md) in
place. Do not create another handback or another remediation chain.

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
7. the original production-readiness assignment and the first and second
   remediation prompts;
8. the complete current production-readiness handback;
9. `tools/executor_supervisor_install.py`, its complete unit and real-host
   tests, and the installed service fragment; and
10. the current diff, preserving the shared dirty worktree and every unrelated
    change.

Use only synthetic data and the canonical secret-excluding synchronization
procedure. Do not read a real secret or copy real player data.

## Finding 1 — Blocking: an unavailable unit-state query can verify itself

`Installer._show()` maps a non-zero `systemctl show` result to `{}`, and
`_state()` maps that to the empty string. `install()` records that empty string
as the pre-upgrade state. During restoration, another failed `ActiveState`
query produces the same empty string, so `_restore_upgrade()` treats
"unknown before" and "unknown after" as equal and re-raises the original
`reload-failed` (13) instead of `recovery-incomplete` (15).

Codex reproduced this deterministically: an older recognized fragment was
loaded and running, every dedicated `ActiveState` query returned non-zero, the
forward reload failed and the earlier bytes were restored; the installer
reported `reload-failed` even though it had never established either the
original or restored unit state.

Correct the observation boundary without broadly changing accepted manager
semantics:

- before an upgrade can change the fragment, obtain a successful, recognized
  unit-state observation; if it is unavailable or malformed, fail with a fixed
  diagnostic and make no fragment, enablement or manager mutation;
- after an upgrade may have changed the fragment, restoration succeeds only
  when a fresh successful query establishes the exact recorded state;
- never represent an unavailable observation with a value that can compare
  equal to another unavailable observation;
- a non-zero result, timeout, OS error or malformed payload during final state
  verification makes the result exactly `recovery-incomplete` (15); and
- retain the existing rule that a successfully verified restoration reports
  the original operation failure.

Add deterministic regressions that fail on the reviewed code and cover at
least:

1. a non-zero initial `ActiveState` query: fixed failure, no write, enable,
   disable or reload;
2. a non-zero final restoration-state query after the fragment changed:
   `recovery-incomplete`/15;
3. a malformed or missing `ActiveState` value at each boundary;
4. a final query failure while the real modeled state also changed, proving
   that equality of sentinel values cannot hide the change; and
5. a later safe retry from every recoverable result.

Assert bytes on disk, manager-loaded bytes, enablement, running configuration
and actual modeled unit state, not only the returned word.

## Finding 2 — Blocking: enable/disable restoration discards manager status

`_restore_upgrade()` invokes `systemctl enable` or `disable` but discards the
returned status and accepts restoration when the final link happens to match.
Codex reproduced a `disable` that returned non-zero after removing the wants
link: the installer reported the original `reload-failed` (13), contrary to the
second-remediation requirement to check both the manager operation and the
resulting link/state.

Make the restoration check conjunctive:

- the required `enable` or `disable` command must return zero;
- the wants-link observation must independently match the recorded original
  enablement;
- a non-zero manager result is `recovery-incomplete` (15), even if the command
  partially changed the link into the desired state;
- a zero result with the wrong link remains `recovery-incomplete`; and
- successful restoration in both directions still re-raises the original
  operation failure and permits a later safe retry.

Add separate regressions for `enable` and `disable` returning non-zero after
producing the desired link state, plus the existing non-zero/no-effect and
zero/wrong-effect cases. Exercise the fixed word and exit 15 through `main()`.

## Finding 3 — Important: the checklist scans the wrong user-unit paths

Handback §6 item 5 runs `systemd-analyze --user unit-paths` in the production
operator's context. A root operator therefore receives root's paths, not the
dedicated `freedom-executor` account's paths. Codex confirmed this on
`oracle-test`: the root invocation omitted the ordinary user's home,
`/run/user/<uid>/systemd/transient`, generator and other runtime user-manager
paths. The later prose about repeating `systemctl --user -M
freedom-executor@ show` neither enumerates nor searches those paths.

Correct the checklist so that, after the account exists, it safely obtains and
searches the dedicated account's effective user-unit paths, including its home
and runtime/transient/generator paths. The method must:

- run in the account's correct user-manager context with an explicit trusted
  `HOME`, `XDG_RUNTIME_DIR` and bus address where required;
- preserve a reliable status for path enumeration and for every searched
  directory;
- inspect the implicated persistent and transient unit names and relevant
  drop-ins without printing unit contents, process arguments or environment
  blocks;
- state clearly what is deferred when the account does not yet exist and what
  must be repeated after provisioning; and
- remain a production read-only inspection method. If scratch output is
  unavoidable, keep it bounded, non-secret and remove it explicitly; do not
  require an unexplained pre-existing helper file.

Exercise the corrected command shape on `oracle-test` with a disposable
account or the existing test account setup. Prove that the account-context
result contains the account's home and `/run/user/<uid>` paths while the root
invocation does not, and that a planted implicated unit/drop-in in an
account-specific path is reported without its contents being printed.

Review the remainder of §6 for the same account-context assumption and correct
only affected statements or commands.

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
- `owner-without-fragment`, the removal recovery selected in round 2, BS-3 or
  the corrected transient inspection-failure analysis; or
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

1. the complete installer module, including every new observation-status and
   enable/disable partial-effect case;
2. focused CLI checks proving incomplete recovery prints exactly
   `recovery-incomplete` and exits 15;
3. a relevant real-manager `oracle-test` probe if the state-query or
   partial-effect failure can be injected deterministically without weakening
   the manager; otherwise state accurately that those failures are proved only
   in the deterministic harness;
4. the complete focused manager/Polkit, cleanup, backstop, hold, consume,
   attest, start, stop, artifact, executor ownership/usermanager/supervisor/
   interrupt/installer/system-service and deployment-artifact set;
5. the complete root `tests/systemd_integration` suite with
   `FREEDOM_SYSTEMD_INTEGRATION=oracle-test`, the pinned wheel and root's own
   documented `PATH`;
6. the canonical bot suite, then the database-enabled web suite with
   `TEST_DATABASE_URL=postgresql+psycopg:///freedom_test` and the expected skip
   count checked, then the Foundry Node suite;
7. executable checks for the corrected dedicated-account unit-path inspection,
   reliable non-zero status reporting and secret-safe output;
8. configured formatter, linter and type checker, or an accurate statement
   that each is not configured; `compileall` over changed Python;
   `git diff --check`; and
9. a final disposable-host comparison covering accounts/groups/homes, linger,
   sudoers, Polkit/`tmpfiles.d`, units/drop-ins, processes, cgroups, mounts,
   state/run directories, artifacts, deployment copies, decoys and pytest
   residue.

Run the bot and web suites serially because they share the disposable database.
State that cited suites ran on `oracle-test`, not the repository host, and that
`TEST_DATABASE_URL` was exported for the web database tests. Report every
failure, error, skip, retry, altered command and infrastructure incident.

A full suite rerun is required after the last executable change. Documentation
edits made afterward require rerunning the tree-scanning documentation and
structural checks, not unrelated behavioral suites, unless the edit changes an
executable instruction or interpretation of earlier evidence.

## Documentation and handback

Update the existing production-readiness handback in place with one concise
**third review remediation return** section and correct affected earlier text
so the document contains no contradictory recovery or inspection claims.
Include:

- the two installer corrections and the regressions that fail on the reviewed
  code and pass afterward;
- the corrected dedicated-account user-manager inspection method and its
  executable disposable-host proof;
- files changed;
- material commands and reliable results, including failures and skips;
- any exact-path host probes and the final restoration result;
- remaining production risks and gates; and
- confirmation that nothing was accepted, committed, pushed or touched in
  production or staging.

Reconcile the current-state pointers in `docs/review/Handover information`,
`docs/project-management/active-delivery-plan.md`,
`docs/project-management/status.md`, implementation-plan §20, the decision and
RAID registers, change log and review index. Preserve historical text and
append where a record is append-only.

End with a concrete conclusion and recommendation for independent Codex
re-review. Stop after the handback. Codex re-reviews the exact final tree and
Peter decides the transient risk and acceptance afterward.
