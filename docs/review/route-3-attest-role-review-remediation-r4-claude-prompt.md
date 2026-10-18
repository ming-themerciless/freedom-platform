# Claude remediation prompt — Route 3 `attest` fourth review finding

Date: 2026-10-18
Authority: Peter Duscha's explicit request, baseline v1.9, the active
implementation-first delivery plan, and the independent Codex review of the
third-remediated uncommitted RT-5 candidate
Mode: one bounded verification-record remediation on `oracle-test`; no
production or staging activation

## Assignment

Correct the final-tree verification record in
`docs/review/route-3-attest-role-implementation-handback.md` so that the third
review remediation is independently reproducible and every reported exit
status is reliable.

This is a documentation/evidence correction, not an implementation assignment.
Do not change RT-5 or shared runtime code, tests, artifacts, unit behavior,
authorization behavior or cleanup semantics unless a newly executed check
demonstrates a real implementation defect. If that happens, stop and report the
defect rather than expanding this assignment.

Do not implement the non-root executor, OC-1/OC-2/OC-3, a production
capture-unit installer, migration/cutover work, or production/staging
activation. Preserve unrelated working-tree changes. Do not commit or push.

## Read before editing

1. `.agents/AGENTS.md` in full.
2. `docs/implementation-plan.md`: reading map, §§0, 12 Phase 5.0, 13, 14, 16
   and 20.
3. `docs/review/Handover information`.
4. `docs/project-management/active-delivery-plan.md`.
5. `docs/operations/disposable-test-server.md`.
6. `docs/review/route-3-attest-role-review-remediation-r3-claude-prompt.md`.
7. The complete third-remediation section of
   `docs/review/route-3-attest-role-implementation-handback.md`.
8. The independent Codex finding below.

Historical WP closure labels are not current development gates. The third
remediation's implementation result remains the candidate under review; this
assignment does not reopen accepted `consume`, `start`, `stop`, `hold`,
`stop-post`, `backstop`, manager/Polkit or tmpfiles behavior.

## Blocking finding — final-tree commands and Foundry status are not reliable evidence

The third-remediation handback does not satisfy its own assignment's explicit
acceptance criterion that it contain exact, copy-pastable final-tree commands
with reliable exit statuses.

In `docs/review/route-3-attest-role-implementation-handback.md`, the third
remediation currently uses abbreviated or indirect descriptions including:

- `the documented command of the second remediation`;
- `ssh oracle-test "... pytest ..."`;
- `FREEDOM_RP11_WHEEL=<wheel>`;
- `same command` and `same env`;
- `commands as in the second remediation`; and
- a compilation result without the literal command and complete path list.

Those are not copy-pastable commands for the final tree. Do not merely add a
cross-reference to an earlier section. Expand every item in the third
remediation into the exact literal command that was actually executed,
including working directory, material environment variables and the concrete
wheel path.

The Foundry command has an additional correctness problem:

```bash
ssh oracle-test "cd /opt/freedom-blades/platform && node --test \
  'foundry-module/tests/'*.test.mjs > /var/tmp/node.log 2>&1; echo NODE_EXIT=$?"
```

Because `$?` is inside a locally double-quoted SSH argument, the local shell
expands it before the command reaches `oracle-test`. The remote shell therefore
does not necessarily print the `node` result. Even if `$?` were only escaped,
the trailing `echo` would make SSH return the status of `echo`, masking a
failing Node process.

Re-run the Foundry suite on the synchronized final tree with a command that
both reports and propagates the remote Node exit status. For example, use a
single-quoted remote program or escape remote variables correctly, save the
status immediately after `node`, print the retained log summary, print the
status, and `exit` with that same status. Record the exact command and observed
test counts. Do not use a pipeline whose final command determines the tested
process's status.

## Evidence-recovery rule

Do not invent, normalize or reconstruct a command and describe it as one that
was run.

For each previously reported third-remediation result:

1. recover the exact command from trustworthy retained evidence such as shell
   history or an existing command/log record and copy it literally; or
2. if the exact command cannot be established, rerun that check on the current
   synchronized final tree with a fully recorded literal command.

The Foundry suite must be rerun regardless, because the recorded command did
not establish its exit status. A full real-reboot proof or other expensive
suite need not be repeated solely to change prose when its exact command and
result can be established honestly. If either cannot be established, rerun it;
do not preserve an unsupported claim.

Any rerun must use the documented secret-excluding synchronization command and
synthetic data only. Production, staging, real secrets and real player data
remain outside the authority. Bot and web suites must remain serial and the web
suite must export `TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'` and
report its skip count.

## Required correction

Append one concise `Fourth review remediation` section to the existing attest
handback. Do not create a new handback and do not rewrite the historical first,
second or third remediation sections. The new section must supersede only the
third section's verification-command presentation and recommendation.

Include:

1. the finding and its disposition;
2. the exact secret-excluding sync command;
3. exact, copy-pastable commands for every final-tree result retained from the
   third remediation: focused and attest-only tests, root host module, each
   reboot phase and readiness loop, whole systemd suite, static assets and its
   baseline comparison, serial bot and web suites and their baseline
   comparison, Foundry, compilation, guards, whitespace checks and host
   cleanliness;
4. the concrete working directory, interpreter, wheel path and all material
   environment variables;
5. each exit status, pass/fail/error/skip count and every skip reason;
6. a clear distinction between commands rerun in this correction and commands
   copied from trustworthy evidence of the third-remediation run;
7. the corrected Foundry command and fresh result, proving that Node's remote
   status was both reported and propagated;
8. any check whose prior result had to be withdrawn because its exact command
   or result could not be established;
9. final `git diff --check` coverage for tracked and untracked candidate files;
10. host-cleanliness state after any new root/systemd work; and
11. the unchanged production risks and one recommendation: accept RT-5 for
    continued non-production development, or remediate one specifically named
    blocker.

Do not use `<wheel>`, `...`, `same command`, `same env`, `as above`, `as in the
earlier remediation`, or similar substitutions inside the command record.
Commands may be placed in separate fenced blocks to keep them readable, but
each block must be directly executable after copying.

## Acceptance criteria

- Every retained final-tree verification claim is paired with the exact command
  actually run and its result.
- The Foundry suite is freshly run with the remote Node status preserved,
  printed and returned through SSH; a Node failure cannot be hidden by `echo`,
  redirection or a pipeline.
- No placeholder, ellipsis or backward reference is needed to execute any
  recorded command.
- Bot and web evidence remains serial, names the required PostgreSQL test URL,
  and reports the documented web skip count accurately.
- No implementation file changes unless verification reveals a real defect; if
  it does, the assignment stops with that defect reported.
- No production or staging system, real secret or real player data is touched.
- The handback still records no acceptance decision and assigns neither the
  non-root executor nor OC-1/OC-2/OC-3.

Return the complete uncommitted candidate for independent Codex re-review.
