# Claude remediation prompt — Route 3 production-readiness review findings, round 2

Date: 2026-10-22

Status: **ACCEPTED AND AUTHORIZED REMEDIATION PROMPT**

Authority: Peter Duscha, Product Owner and Acceptance Authority

Implementer: Claude

Independent reviewer after return: Codex

Mode: one bounded correction of the returned production-readiness candidate;
no production or staging access or activation

## Assignment

Correct the remaining Route 3 production-readiness findings in place. The
second independent Codex review reproduced three installer recovery gaps and
found two defects in the proposed production read-only inspection methods.

This is one bounded remediation, not a redesign of the accepted Route 3
topology, privileged vector, role semantics or authorization policy. Fix the
installer and its tests, correct the production checklist and runbook where
their claims are affected, verify the exact final tree on `oracle-test`, and
update the existing
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
7. the accepted original production-readiness assignment and first remediation
   prompt;
8. the complete current production-readiness handback;
9. `tools/executor_supervisor_install.py`, its complete unit and real-host
   tests, and the installed service fragment; and
10. the current diff, preserving the shared dirty worktree and all unrelated
    changes.

Use only synthetic data and the canonical secret-excluding synchronization
procedure. Do not read a real secret or copy real player data.

## Finding 1 — Blocking: manager exceptions bypass upgrade recovery

`Installer.install()` recovers only from the installer's typed `Failure`.
The real runner uses `subprocess.run(..., timeout=60)` and can instead raise
`TimeoutExpired`, another `SubprocessError`, or an `OSError`. If that occurs
after a recognized old fragment has been replaced, the exception bypasses
`_restore_upgrade()`: the new bytes can remain on disk while the manager still
holds the old fragment, and the CLI reports generic `io-error` (13) rather than
the required `recovery-incomplete` (15) when restoration cannot be completed
and verified.

Correct this within the existing installer design:

- once an upgrade may have changed the fragment, every ordinary manager/runner
  failure must enter the same restoration-and-verification path as a non-zero
  manager result;
- a successfully verified restoration may still report the original fixed
  operation failure;
- a restoration that fails or cannot be verified must report only the fixed
  `recovery-incomplete` word and exit 15;
- preserve deliberate process interruption semantics only if they cannot leave
  changed on-disk or manager state without an attempted recovery; and
- do not turn arbitrary programmer errors into false claims of a safe
  restoration.

Add deterministic regressions that fail on the reviewed code, including a
runner `TimeoutExpired` and an `OSError` at material enable/reload/show points.
Cover both successful restoration and incomplete restoration. Assert the
on-disk bytes, manager-loaded fragment, enablement and unit state, not only the
returned word.

## Finding 2 — Blocking: failed upgrade does not restore disabled enablement

The existing recovery records whether the recognized earlier unit was enabled,
but `_restore_upgrade()` only ensures that an originally enabled unit is
enabled. It does not undo enablement introduced by the failed upgrade when the
unit was originally disabled.

The reproduced case is:

1. an older recognized fragment is loaded and running but disabled;
2. `install` enables it;
3. the forward `daemon-reload` fails; and
4. the old bytes and manager configuration are restored, but the wants link is
   left behind while the command reports ordinary `reload-failed`.

Make enablement restoration symmetric. A successfully recovered upgrade must
leave the unit enabled if and only if it was enabled before the attempt. Check
the manager operation and the resulting link/state. If the original disabled
state cannot be restored and confirmed, return `recovery-incomplete` (15).

Add regressions for:

- disabled before the upgrade, temporarily enabled, then forward reload
  failure and successful restoration to disabled;
- failure to disable during restoration, producing `recovery-incomplete`;
- the already-covered originally enabled restoration; and
- a later safe retry from each recoverable result.

Update the runbook and handback so “enablement restored” means both directions,
not merely re-enabling an originally enabled unit.

## Finding 3 — Blocking: removal can lose a loaded owner without status 15

The runbook explicitly recognizes that the fragment may be absent while the
system manager still has a running loaded copy. `remove()` accepts that state,
drains and stops the owner, disables the unit and attempts its checked reload.
On failure, `_recover(None)` calls `_restart()` but discards whether the owner
was actually restarted. A reproduced failed restart returned `reload-failed`
(13) while leaving no fragment, no enablement and a failed supervisor.

Choose the smallest fail-closed correction consistent with the current design:

- either refuse an active/listening supervisor whose recognized fragment is
  absent before changing it, with an accurate fixed diagnostic and operator
  response; or
- define and implement a recovery path that can re-establish and verify the
  prior persistent owner from that state.

Do not claim persistence from a manager's in-memory loaded copy alone when no
fragment or enablement will survive reboot. Any removal failure after a running
owner was drained or stopped must either leave a verified persistent owner or
return `recovery-incomplete` (15). Never discard a failed restart.

Add deterministic regressions for an absent on-disk fragment with a loaded,
running supervisor, including reload failure followed by successful and failed
restart/recovery, the chosen refusal behavior if applicable, and safe operator
convergence. Preserve idempotent removal when the fragment and loaded unit are
both genuinely absent.

## Finding 4 — Important: the production process check can disclose secrets

Handback §6 item 11 uses `chk ps -eo user,args`. Because `chk` prints the
captured output, this can expose command-line credentials, tokens, database
URLs or unrelated production process data. It contradicts the checklist's
claim that no step prints a secret value and the assignment's instruction to
record conclusions rather than unrelated policy or secret values.

Replace it with a minimal, scoped method that establishes who runs as
`freedom-executor` and the required topology facts without printing all process
arguments on the host. If an exact command line for the dedicated account must
be verified, scope the inspection to the expected PID/account and record only a
redacted conclusion or an allowlisted executable/argv comparison. Do not dump
environment blocks or unrelated process arguments.

Review the rest of §6 for the same output-safety property. Keep the inspection
read-only and do not access production or staging while making this correction.

## Finding 5 — Important: inspection command shapes are not executable

Correct the following methods in handback §6:

- the login-defs expression currently escapes `|` inside an ERE, so it does
  not match normal `UID_MIN`, `UID_MAX`, `GID_MIN`, `GID_MAX`,
  `SYS_UID_*` or `SYS_GID_*` entries; and
- the two `find` examples use unescaped shell parentheses, causing a Bash
  syntax error before `chk` can record a reliable status.

Provide shell-valid command shapes, with `\(` and `\)` or an equivalent safe
form, and a correct ERE. Check every command or short script in §6 with
`bash -n` where applicable and exercise its parsing/status behavior on
`oracle-test` using synthetic or disposable-host facts. Placeholders such as
`<dir>` may remain only where the text clearly tells the operator to substitute
an enumerated path; the resulting command must be unambiguous and executable.

The status rule remains: every checked command reports its own status, and a
non-zero status is resolved or explained rather than hidden by a trailing
pipeline command.

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
- BS-3 or the corrected transient inspection-failure analysis; or
- production topology, authorization policy or the transient-risk decision.

If a correct installer repair would require a different topology,
authorization boundary or accepted role behavior, stop and return the concrete
decision instead of implementing it.

## Required verification

First add focused regressions that demonstrably fail on the reviewed installer,
then make them pass. Synchronize the exact final workspace to `oracle-test`
with the canonical secret-excluding command and run shared-state suites
serially.

At minimum, run and report:

1. the complete installer module, including the new exception, symmetric
   enablement and absent-fragment removal cases;
2. focused CLI fixed-word/exit-status checks proving incomplete recovery maps
   to exactly `recovery-incomplete` and 15;
3. relevant real-path `oracle-test` recovery probes where they can be injected
   deterministically and safely; do not claim host evidence for a failure that
   exists only in the deterministic harness;
4. the complete focused manager/Polkit, cleanup, backstop, hold, consume,
   attest, start, stop, artifact, executor ownership/usermanager/supervisor/
   interrupt/installer/system-service and deployment-artifact set;
5. the complete root `tests/systemd_integration` suite with
   `FREEDOM_SYSTEMD_INTEGRATION=oracle-test`, the pinned wheel and root's own
   documented `PATH`;
6. the canonical bot suite, then the database-enabled web suite with
   `TEST_DATABASE_URL=postgresql+psycopg:///freedom_test` and the expected skip
   count checked, then the Foundry Node suite;
7. executable checks for every corrected §6 command shape, including the
   login-defs match, both `find` forms, reliable non-zero status reporting and
   the secret-safe scoped process inspection;
8. configured formatter, linter and type checker, or an accurate statement
   that each is not configured; `compileall` over changed Python;
   `git diff --check`; and
9. a final disposable-host comparison covering accounts/groups/homes, linger,
   sudoers, Polkit/`tmpfiles.d`, units/drop-ins, processes, cgroups, mounts,
   state/run directories, artifacts, deployment copies, decoys and pytest
   residue.

Run the bot and web suites serially because they share the disposable database.
State that the cited suites ran on `oracle-test`, not the repository host, and
that `TEST_DATABASE_URL` was exported for the web database tests. Report every
failure, error, skip, retry, altered command and infrastructure incident.

A full suite rerun is required after the last executable change. Documentation
edits made afterward require rerunning the tree-scanning documentation/structural
checks, not unrelated behavioral suites, unless the edit changes an executable
instruction or interpretation of earlier evidence.

## Documentation and handback

Update the existing production-readiness handback in place with one concise
**second review remediation return** section and correct affected earlier text
so the document contains no contradictory recovery or inspection claims.
Include:

- the three installer corrections and tests that fail on the reviewed code and
  pass afterward;
- the safe, executable production inspection corrections;
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
