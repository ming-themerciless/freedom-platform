# Claude remediation prompt — Route 3 production-readiness review findings, round 5

Date: 2026-10-23

Status: **ACCEPTED AND ASSIGNED by Peter Duscha, 2026-10-23; direct completion
returned and independently re-reviewed 2026-10-24 with acceptance recommended**

Implementer: Claude

Independent reviewer after return: Codex

Mode: one bounded in-place correction of the returned candidate and its
disposable-host evidence; no production or staging access, inspection or
activation

## Assignment

Correct the three findings from Codex's independent review of the fourth
production-readiness remediation:

1. `oracle-test` is not in the canonical restored state claimed by the
   handback and cannot currently run the documented suites;
2. production checklist item 5b still loses or masks command status at several
   fact-gathering boundaries; and
3. the handback says that a fourth-remediation return appears first, but no
   such section or fourth-round evidence exists.

This is a bounded correction of the disposable test environment, the item 5b
inspection method and its tests, and the existing production-readiness
handback. It is not a redesign of the accepted Route 3 topology, privileged
vector, role semantics, authorization policy or residual-risk options. Restore
the documented test lane, add the missing fail-closed regressions, rerun the
required evidence against the exact final tree, and update the existing
[`production-readiness handback`](route-3-production-readiness-handback.md) in
place. Do not create another handback or another remediation prompt.

The candidate remains unaccepted. This prompt makes no transient-risk decision
and authorizes no production or staging login, inspection, installation or
activation, successor slice, coordinator, start orchestration, automatic
attestation, migration/cutover, RB-1, commit or push.

## Direct completion correction after independent review

Codex's review of the fifth return found one remaining implementation defect:
item 5b can still print `[item 5b COMPLETE]` when a directory search or one of
the three unit queries failed. Peter assigns Claude this correction directly
under the existing round-five scope. This is completion of the accepted
fail-closed checklist requirement, not a sixth remediation round.

Make item 5b's closing result truthful:

- an expected absent directory may be reported as absent only when absence was
  established directly; a `find` failure must not be interpreted as absence;
- any I/O, permission or other search failure makes item 5b `INCOMPLETE`;
- any non-zero `list-unit-files` or allowlisted `show` query makes item 5b
  `INCOMPLETE`; and
- `COMPLETE` is printed only when the effective path set was formed, every
  existing directory was searched successfully, and all three unit queries
  succeeded.

Add two focused regressions: one injects a directory-search failure and one
injects a unit-query failure. Each must prove `INCOMPLETE`, absence of
`COMPLETE`, reliable status output and scratch cleanup. Preserve the fixed
account, allowlisted output and all production/staging prohibitions.

Run only the complete checklist test module, `bash -n` over the extracted
script, the directly affected tree-scanning/structural check, and
`git diff --check`. A full product, database, Node or root/systemd suite rerun
is not warranted because this correction changes only the read-only checklist
and its focused tests. Update the existing handback and current-state records
in place after the correction; do not create another prompt or handback.

### Final portability follow-up after Codex re-review — 2026-10-24

Codex synchronized the exact direct-completion tree to `oracle-test` and
reproduced **6 failed, 45 passed** in the focused checklist module. The
repository-host run passed because its GNU coreutils `stat` prints:

```text
stat: cannot statx '<path>': No such file or directory
```

The documented disposable host uses uutils coreutils and prints:

```text
stat: cannot stat '<path>': No such file or directory (os error 2)
```

The checklist currently compares the complete localized diagnostic string, so
ordinary absent user-unit directories are treated as unknown search failures.
This is the same direct-completion task, not another remediation round.

Replace diagnostic-text parsing with an errno/type result. Use the fixed
`/usr/bin/python3.14 -I -S` interpreter already required and inspected by this
checklist, with one path argument and no environment-derived program or module
path. The helper must use `os.lstat` (or an equivalently exact syscall result)
and return distinct fixed statuses for:

- the path exists;
- `FileNotFoundError`/`ENOENT`, which alone establishes absence; and
- every other `OSError`, which leaves the observation unavailable.

Do not print the exception or pathname through Python. The shell may print its
existing fixed `[absent]` or `[FINDING]` line after interpreting the fixed
status. A failed `find` followed by `ENOENT` is the only accepted absence; a
failed `find` followed by an existing path or any other error remains
`INCOMPLETE`. Preserve the rule that no unit query runs after a failed search
and that any failed unit query makes the final result `INCOMPLETE`.

Keep or strengthen the focused regressions so they prove all three outcomes:

1. failed `find` plus a genuinely missing path is accepted as absent and the
   otherwise successful item can finish `COMPLETE`;
2. failed `find` plus an existing path is a finding and finishes `INCOMPLETE`
   without unit queries; and
3. a non-ENOENT observation failure is a finding and finishes `INCOMPLETE`
   without unit queries.

Synchronize the exact final workspace with the canonical secret-excluding
`rsync` before testing. Evidence must come from `oracle-test`, not only the
repository host. Run exactly:

- the complete `tests/test_production_checklist_item_5b.py` module;
- `bash -n` over the extracted checklist;
- the directly affected structural/tree-scanning check; and
- `git diff --check`.

Report file hashes or another concise identity check only to establish that
the two focused files tested on `oracle-test` match the workspace. Report every
failure and retry. Do not run the full bot, web, Node or root/systemd suites.
Update the existing direct-completion section and current-state headings in
place, then stop for Codex's final focused review. Do not create a prompt,
handback or remediation number.

## Required context

Before changing anything, read completely and follow:

1. `.agents/AGENTS.md`;
2. the reading map and §§0, 9, 12 Phase 5.0, 13, 14, 16, 17 and 20 of
   `docs/implementation-plan.md`;
3. `docs/review/Handover information`;
4. `docs/project-management/active-delivery-plan.md`;
5. `docs/operations/disposable-test-server.md`;
6. `docs/operations/executor-supervisor-provisioning-runbook.md`;
7. the original production-readiness assignment and all four earlier
   remediation prompts;
8. the complete current production-readiness handback;
9. `tools/executor_supervisor_install.py`, its complete unit and real-host
   tests, the item 5b structural tests and the installed service fragment; and
10. the current diff, preserving the shared dirty worktree and every unrelated
    change.

Use only synthetic data and the canonical secret-excluding synchronization
procedure. Do not read a real secret or copy real player data.

## Finding 1 — Blocking: the disposable test lane was not restored

The handback claims that `/opt/freedom-blades/{,runtime}` were restored to
`ubuntu:ubuntu`, that `platform` was again the canonical setgid checkout, and
that `venv-web` was again the documented Python 3.12.14 test environment.
Codex instead observed on `oracle-test`:

- `/opt/freedom-blades/platform` as `root:root 0755`;
- `/opt/freedom-blades/runtime/venv-web` as `root:root 0755`;
- `venv-web/bin/python` resolving to `/usr/bin/python3.14`; and
- no importable pytest in that environment.

The canonical secret-excluding synchronization consequently exited 23 with
permission failures. This contradicts the machine profile in
`docs/operations/disposable-test-server.md` and prevents independent execution
of the required test commands.

Before changing the host, capture a concise, secret-safe comparison of its
current state and determine which rehearsal or teardown step left the checkout
and runtime behind. Then restore the disposable host to the documented
canonical test state using the authorized reset/recovery procedure. In
particular, prove all of the following before citing any rerun:

- the checkout is writable by `ubuntu`, has the documented ownership and
  setgid directory policy, and accepts the canonical rsync with exit 0;
- `/opt/freedom-blades/runtime/venv-web/bin/python` is the documented Python
  3.12.14 environment and can import pytest and the locked test dependencies;
- restoring the test lane did not leave an executor account, group, home,
  linger entry, sudoers rule, unit/drop-in, process, cgroup, mount, state/run
  directory, controlled artifact, deployment copy or decoy behind; and
- the exact workspace files under review match the files tested on
  `oracle-test`.

The host is disposable and full root/systemd testing there is authorized, but
do not erase the only available evidence of an unexplained state before
recording the facts needed to diagnose it. Do not describe a root-owned
production-shaped deployment tree as the restored canonical test checkout.

Add or correct teardown/restoration automation if the mismatch exposes an
executable cleanup defect. If the mismatch instead came from an interrupted or
out-of-order manual rehearsal, document that incident accurately and still
restore and verify the canonical state. Do not claim the earlier final-host
comparison passed.

## Finding 2 — Important: item 5b still masks or discards fact-gathering status

The item 5b shell method has several remaining unreliable boundaries:

- `root_home=$(getent passwd root | cut -d: -f6)` has no `pipefail` and records
  neither producer status nor record cardinality, so a failed or ambiguous NSS
  lookup can be hidden by `cut`;
- `chk asacct systemd-analyze --user unit-paths` deliberately returns zero
  after printing the wrapped status, and the following `cp` proceeds even when
  the account-context command failed; and
- the `cp`, `sort -u` and resulting dynamic-path preparation do not publish and
  enforce reliable success before the searches consume their output.

Make the method fail closed as an inspection procedure:

- obtain and validate exactly one root account record without a pipeline that
  can mask its status; an unavailable, duplicate or malformed root record is a
  fixed finding and item 5b runs no account-context command;
- retain the existing literal `ACCOUNT=freedom-executor` and validate exactly
  one dedicated-account record, its nonzero UID, dedicated absolute home,
  ownership, runtime directory and bus before use;
- make the account-context `systemd-analyze --user unit-paths` result available
  to later steps only when its actual status is zero;
- check and report every copy, append, normalization and search needed to form
  the effective path set; a failed producer must not be followed by a search
  that looks complete;
- preserve the secret-safe output boundary: identifiers, allowlisted state and
  safe path metadata only, never descriptions, contents, argv, environment or
  other free-form manager properties; and
- leave no scratch output behind on success or failure.

Add deterministic regressions that fail on the returned tree and cover at
least:

1. root NSS lookup failure, duplicate records and malformed records;
2. an account home equal to a nonstandard root home;
3. account-context `systemd-analyze` nonzero status with empty and partial
   output, proving no dynamic-path search follows it;
4. failure while saving or normalizing the unit-path result, proving subsequent
   searches and unit queries do not run as if the path set were complete;
5. a conflicting ambient `ACCOUNT`, invalid dedicated-account facts and an
   unavailable account bus;
6. a valid account and complete successful path search with every material
   command status represented; and
7. a transient implicated unit whose synthetic description contains a decoy,
   proving the unit identifier and allowlisted state are reported while the
   decoy appears zero times.

The test seam may substitute commands or a disposable account in a separate
test-only copy. It must not create a production account override or weaken the
literal fixed-account method.

## Finding 3 — Blocking evidence defect: the fourth return is absent

The handback introduction says the **Fourth review remediation return** is the
first section, but the document begins with `## Third review remediation
return`. The visible 233-installer, 3204-focused and 199-root results belong to
the third return and do not establish the later strict-enable-observation and
fixed-account/allowlisted-output changes.

Update the same handback in place with one concise **Fifth review remediation
return** section at the top. It must:

- state plainly that the promised fourth-return section was missing;
- describe the fourth-round implementation that is actually present in the
  tree, without inventing commands or results that were not retained;
- supersede the false earlier host-restoration claim and record the observed
  root-owned Python 3.14/no-pytest state as an incident;
- describe the round-5 host restoration and item 5b status correction;
- report exact final-tree verification performed after restoration, with
  reliable results, failures, errors, skips, retries and infrastructure
  incidents;
- identify every file changed in rounds 4 and 5;
- preserve the remaining production risks and gates; and
- confirm that nothing was accepted, committed, pushed or touched in
  production or staging.

Do not backfill unrecorded fourth-round evidence from memory. If an earlier
result cannot be established, label it unavailable and replace it with a new
run on the exact final tree. Correct the introduction, date, conclusion and any
earlier sentence that still asserts the missing section or the false restored
host state.

Reconcile the active handover, project status, active delivery plan,
implementation-plan §20, decision and RAID registers, change log and review
index only after the fifth remediation has actually returned. Preserve
historical entries; append superseding records where the document is
append-only.

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
- `owner-without-fragment`, removal recovery, strict `ActiveState`, strict
  enablement observation, BS-3 or the corrected transient inspection-failure
  analysis; or
- production topology, authorization policy or the transient-risk decision.

If a correct repair requires a different topology, authorization boundary or
accepted role behavior, stop and return the concrete decision instead of
implementing it.

## Required verification

First add focused regressions that demonstrably fail on the returned item 5b
method, then make them pass. Restore the documented test lane and synchronize
the exact final workspace to `oracle-test` with the canonical secret-excluding
command. Run shared-state suites serially.

At minimum, run and report:

1. the complete installer module, including all round-4 strict-enable cases;
2. the complete item 5b structural and executable-shell tests, including every
   new status-propagation case;
3. the exact production-shaped item 5b host probe with a conflicting ambient
   `ACCOUNT`, invalid NSS facts, failed unit-path discovery and the decoy
   description, with reliable status and zero decoy disclosure;
4. the complete focused manager/Polkit, cleanup, backstop, hold, consume,
   attest, start, stop, artifact, executor ownership/usermanager/supervisor/
   interrupt/installer/system-service and deployment-artifact set;
5. the complete root `tests/systemd_integration` suite with
   `FREEDOM_SYSTEMD_INTEGRATION=oracle-test`, the pinned wheel and root's own
   documented `PATH`;
6. the canonical bot suite, then the database-enabled web suite with
   `TEST_DATABASE_URL=postgresql+psycopg:///freedom_test` exported and the skip
   count checked, then the Foundry Node suite;
7. configured formatter, linter and type checker, or an accurate statement
   that each is not configured; `compileall` over changed Python; the shell
   syntax check over the extracted checklist; `.claude/hooks/test_guards.py`;
   and `git diff --check`; and
8. a final disposable-host comparison against a snapshot taken only after the
   canonical test lane is restored, covering checkout/runtime ownership and
   interpreter, accounts/groups/homes, linger, sudoers, Polkit/`tmpfiles.d`,
   units/drop-ins, processes, cgroups, mounts, state/run directories,
   artifacts, deployment copies, decoys, scratch files and pytest residue.

Run bot and web suites serially because they share the disposable database.
State that cited suites ran on `oracle-test`, not the repository host, and that
`TEST_DATABASE_URL` was exported for the web database tests. Report every
failure, error, skip, retry, altered command and infrastructure incident.

A full suite rerun is required after the last executable change. Documentation
edits made afterward require rerunning tree-scanning documentation and
structural checks, not unrelated behavioral suites, unless the edit changes an
executable instruction or the interpretation of earlier evidence.

## Documentation and handback

Update the existing production-readiness handback in place; do not create a
second handback. Include:

- the host-state discrepancy, its cause if established, and the verified
  canonical restoration;
- the item 5b status-propagation correction and its fail-first regressions;
- the fourth-round implementation summary and honest disposition of its
  previously missing evidence;
- files changed;
- material commands and reliable final-tree results, including failures and
  skips;
- exact-path host probes and the final restoration comparison;
- remaining production risks and gates; and
- confirmation that nothing was accepted, committed, pushed or touched in
  production or staging.

End with a concrete conclusion and recommendation for independent Codex
re-review. Stop after the handback. Codex re-reviews the exact final tree and
Peter decides the transient risk and acceptance afterward.
