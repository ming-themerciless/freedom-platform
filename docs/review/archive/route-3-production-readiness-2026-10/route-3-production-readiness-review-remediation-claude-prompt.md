# Claude remediation prompt — Route 3 production-readiness review findings

Date: 2026-10-22

Status: **ACCEPTED AND AUTHORIZED REMEDIATION PROMPT**

Authority: Peter Duscha, Product Owner and Acceptance Authority

Implementer: Claude

Independent reviewer after return: Codex

Mode: one bounded correction of the returned production-readiness candidate;
no production or staging access or activation

## Assignment

Correct the Route 3 production-readiness candidate in place. Independent Codex
review found two blocking installer/security defects, a materially inaccurate
residual-risk analysis, incomplete production-inspection methods and an
unfinished verification handback.

This is one bounded remediation, not a redesign of the accepted Route 3
topology or role semantics. Fix the implicated installer and tests, correct the
runbook and decision material, complete the required final-tree verification,
and update the existing
[`production-readiness handback`](route-3-production-readiness-handback.md) in
place. Do not create another handback or another remediation chain.

The candidate is not accepted. This prompt makes no transient-risk decision
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
7. the accepted
   [`production-readiness assignment`](route-3-production-readiness-claude-prompt.md);
8. the complete returned production-readiness handback;
9. `tools/executor_supervisor_install.py`, its complete unit and real-host
   tests, and the installed service fragment; and
10. the cleanup, backstop, consume, attest and Polkit/`tmpfiles.d` code and
    tests needed to verify the corrected residual analysis.

Inspect the exact current diff before editing. Preserve the shared dirty
worktree and every unrelated change. Use only synthetic data and the canonical
secret-excluding synchronization procedure. Do not read a real secret or copy
real player data.

## Finding 1 — Blocking: restore failure is untested and silently discarded

The handback says that an injected restore failure is covered by
`test_executor_supervisor_install.py` at the tests beginning near lines 670 and
1059. It is not. Those tests inject the failure that *causes* recovery and then
allow restoration to succeed. They do not fail restoration itself.

The implementation also suppresses the material recovery failure:

- during a failed upgrade, failure of `_place(previous, replace=True)` is
  discarded before an unchecked restoring `daemon-reload`; and
- during failed removal recovery, `_recover()` discards failure to put the
  fragment back and does not establish that enable, reload and restart left a
  persistent owner.

That behavior cannot support the runbook's unconditional statements that a
failed upgrade restores the prior fragment and a failed removal leaves the
persistent owner behind.

Correct this within the existing installer design. At minimum:

- never suppress or mislabel a failed restoration;
- return a distinct, fixed diagnostic and non-zero status for incomplete
  recovery, without reporting the original operation as safely restored;
- after a recovery attempt, verify the actual on-disk fragment, enablement,
  manager-loaded fragment/effective properties and running-owner state that
  the result claims;
- preserve the previous byte-for-byte fragment and owner when restoration is
  possible;
- do not overwrite a foreign object or weaken any trust check;
- do not claim that a persistent owner exists when it cannot be established;
- keep removal unavailable while an invocation is owned; and
- document the exact operator response when recovery is incomplete.

Add deterministic regressions for both upgrade and removal that fail on the
reviewed code. Cover at least:

1. replacement/reload failure followed by failure to restore the old bytes;
2. old bytes restored but the restoring reload failing or loading an
   unexpected effective fragment;
3. removal reload failure followed by failure to replace the unlinked
   fragment;
4. restoration followed by enable or restart failure;
5. the existing successful-recovery paths; and
6. a later safe retry from every recoverable state.

Use the smallest explicit recovery result consistent with the existing fixed-
word CLI. Do not invent a claim that arbitrary filesystem or manager failure
can always be repaired automatically. If a state can only be made explicit and
operator-recoverable, fail closed, describe it truthfully, and prove that no
owned invocation was abandoned.

Exercise the material failure path on `oracle-test` at the real fixed paths if
it can be injected deterministically and restored safely. If a particular
restore failure cannot be injected there without a nondeterministic race or
damage outside the disposable boundary, say exactly so and rely only on a
deterministic test that actually fails restoration; do not cite a successful-
restore test as restore-failure evidence.

## Finding 2 — Blocking: sudo verification accepts a wider run-as policy

The runbook requires exactly:

```text
freedom-executor ALL=(root) NOPASSWD: /usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py stop
```

However, `_SUDO_RULE` currently accepts output whose run-as field is `(ALL)` or
`(ALL : ALL)` (and other forms wider than the documented root-only rule). The
rehearsal's `-u ubuntu` refusal proves the particular drop-in that was installed;
it does not prove that the installer rejects those wider policies.

Make the verifier enforce the documented invariant:

- exactly one effective command grant reaches `freedom-executor`;
- it is `NOPASSWD` for the fixed SA-2 argv;
- its run-as user is root only, with no arbitrary-user or arbitrary-group
  selection; and
- tags or output forms that add `SETENV`, wildcards, aliases or another
  capability are refused.

Add table-driven parser tests for the accepted output produced by the supported
sudo implementation and refusals for `(ALL)`, `(ALL : ALL)`, alternate users or
groups, extra tags, extra commands and alternate argv. Add a real-host probe on
`oracle-test` showing that the exact rule is accepted and a temporary wider
run-as rule is refused by installer `verify`; restore the host afterward.

Do not widen sudoers or change the privileged vector, Python `-I -S`, artifact
role selection or the dedicated-account topology.

## Finding 3 — Blocking decision input: correct the residual lifecycle and recommendation

The handback first says that the unattributable foreign rule lasts until CP,
`attest` or reboot, then correctly explains that CP and `attest` retain that
same foreign rule because neither has an identity permitting removal. Reconcile
the analysis with the running behavior:

- for the specific residual where both identity sources are lost, CP and
  `attest` detect the object and fail closed but do **not** clear it;
- reboot clears the `/run` object;
- before reboot, a root operator may remove it only after separately verifying
  that it is the foreign residual identified by the alert/procedure; and
- absent reboot or verified manual response, its file lifetime has no automatic
  bound after BS-3 disarms the timer.

Remove the unsupported claim that the required conditions are independent.
Describe them as coincident conditions unless executable evidence establishes
independence. Likewise, `tmpfiles.d` mitigates the known boot-order cause; it
does not prove that every possible false `not-authorized` observation is
closed.

Re-evaluate options A/B/C and the recommendation using those corrected facts.
If recommending conditional acceptance with monitoring, specify the proposed
maximum detection interval, exact signal, accountable responder, response
deadline, manual verification/removal or reboot action, escalation condition,
and activation/rollback consequence. Clearly distinguish a proposed condition
from monitoring that already exists: the repository currently supplies no such
alert. Peter, not Claude, makes the risk decision.

Do not change BS-3, add a retry state or alter authorization policy in this
remediation. A desired behavior change is a decision item, not permission to
expand this correction.

## Finding 4 — Important: make the production fact checks complete and safe

The checklist must establish the effective policy, not infer it from likely
filenames.

Correct it so that a later separately authorized read-only production
inspection will:

- validate sudo syntax and enumerate every file reached through `@include`,
  `#include`, `@includedir` or `#includedir`, following custom paths
  transitively;
- inspect all effective user-specific and global Defaults and every grant
  reaching `freedom-executor`, while recording conclusions rather than copying
  unrelated policy or secret values into the handback;
- inspect the contents/effect of every relevant Polkit rule in all configured
  rule directories, not only filenames containing `systemd`;
- inspect effective system and user unit fragments, drop-ins and generator
  output for every implicated service name;
- establish ownership, type, link and write-mode facts for the complete trusted
  deployment/interpreter/dependency/artifact scope, including non-root-owned
  but non-writable files; and
- use reliable status propagation so `grep`, `head` or another trailing command
  cannot turn an inspection error into apparent success.

Keep the checklist minimal and read-only. It is preparation only: do not access
production or staging, and do not print secret values.

## Finding 5 — Blocking evidence: finish the handback on the exact final tree

The returned handback still contains `ROOT_RESULT`, `BOT_RESULT`, `WEB_RESULT`,
`NODE_RESULT`, `CHECKS_RESULT`, `FINAL_HOST` and `CONCLUSION`. Replace every
placeholder with an actual, reliably obtained result or a precise disclosed
failure. Do not describe a running or interrupted command as passed.

The earlier incomplete background run is not evidence unless its final exit
status and output were retained reliably. Report it as an incident if it was
interrupted, superseded or otherwise unusable. A rerun does not erase that
fact.

## Preserved boundary

Do not reopen or redesign:

- the root-controlled system supervisor and dedicated account;
- the account's lingering user manager and one transient unit per invocation;
- durable exclusive ownership before the sole `StartTransientUnit` call;
- recovery that adopts and settles but never launches or retries SA-2;
- the exact privileged SA-2 argv;
- OC-1/OC-2/OC-3, one-shot and ambiguous-handoff behavior;
- accepted manager/Polkit, cleanup, backstop, hold, start, stop, consume or
  attest semantics; or
- production topology, authorization policy or the transient-risk decision.

The installer may be changed only as necessary to enforce its already
documented sudo and recovery contracts. If a correct repair would require a
different topology, authorization boundary or accepted role behavior, stop and
return the concrete decision instead of implementing it.

## Required verification

Synchronize the exact final workspace to `oracle-test` with the canonical
secret-excluding command. Run shared-state suites serially.

At minimum, run and report:

1. focused installer tests, including every new restore and sudo-policy
   regression;
2. the complete focused manager/Polkit, cleanup, backstop, hold, consume,
   attest, start, stop, artifact, executor ownership/usermanager/supervisor/
   interrupt/installer/system-service and deployment-artifact set;
3. the complete root `tests/systemd_integration` suite with
   `FREEDOM_SYSTEMD_INTEGRATION=oracle-test`, the pinned wheel and root's own
   documented `PATH`;
4. the real-host exact sudo-policy acceptance/refusal probe and the material
   recovery rehearsal described above;
5. the canonical bot suite, then the database-enabled web suite with
   `TEST_DATABASE_URL=postgresql+psycopg:///freedom_test`, checking that the web
   skip count is exactly the documented 80, then the Foundry Node suite;
6. configured formatter, linter and type checker, or an accurate statement for
   each check that is not configured;
7. `compileall` over changed Python and `git diff --check`; and
8. a final host comparison covering accounts/groups/homes, linger, sudoers,
   Polkit/`tmpfiles.d`, units/drop-ins, processes, cgroups, mounts, state/run
   directories, artifacts, deployment copies, decoys and pytest residue.

Run the canonical bot and web suites serially because they share the disposable
database. Use the documented `/opt/freedom-blades/runtime/venv-web` interpreter
and PostgreSQL 16 `PATH`. State both load-bearing facts with the reported suite
figures: the suite ran on `oracle-test`, not the repository host, and the web
database tests ran with `TEST_DATABASE_URL` exported and 80 expected skips.

Report every failure, error, skip, retry, reboot phase, altered command and
infrastructure incident. Do not call a failure pre-existing without a
meaningful accepted-baseline comparison. Do not leave a background suite
running after the handback is marked complete.

## Documentation and handback

Update the existing production-readiness handback in place with one concise
**review remediation return** section and correct the affected earlier text so
the document does not retain contradictory claims. Include:

- the installer recovery and sudo-verification corrections;
- tests that failed on the reviewed code and now pass;
- the corrected residual lifecycle, options and recommendation;
- the complete production read-only fact methods;
- files changed;
- material commands and reliable results, including failures and skips;
- the exact-path host probes and final restoration result;
- remaining production risks and gates; and
- confirmation that nothing was accepted, committed, pushed or touched in
  production or staging.

Reconcile current-state pointers in `docs/review/Handover information`,
`docs/project-management/active-delivery-plan.md`, `docs/project-management/status.md`,
implementation-plan §20, the decision/RAID registers, change log and review
index. Preserve historical text and append where a record is append-only.

End with a concrete conclusion and recommendation for independent Codex
re-review. Stop after the handback. Codex re-reviews the exact final tree and
Peter decides the risk and acceptance afterward.
