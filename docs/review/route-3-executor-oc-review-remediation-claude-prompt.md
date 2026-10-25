# Claude remediation prompt — Route 3 executor OC review findings

Date: 2026-10-19
Authority: Peter Duscha's remediation request, baseline v1.9, the active
implementation-first delivery plan, and the independent Codex review of the
uncommitted executor OC candidate
Mode: one bounded remediation and verification cycle on `oracle-test`; no
production or staging activation

## Assignment

Remediate the two blocking findings from independent review of the Route 3
non-root executor OC interruption candidate:

1. the supervisor can return `UNSETTLED` after a successful launch while a
   process belonging to the privileged invocation remains alive; and
2. the consume-journal reader can accept bytes from a replaced object, or from
   an object whose required file or directory metadata changed during the
   read.

Add regressions that reproduce both defects before correcting them. Make the
smallest fail-closed change that satisfies the original assignment, run the
required checks on the final tree, and append one concise review-remediation
section to the existing executor handback.

Do not return another implementation plan or proof-document chain. Do not
implement the full coordinator, scheduler, start orchestration, automatic
attestation, a production installer or sudoers rule, migration/cutover work,
or production/staging activation. Preserve unrelated working-tree changes.
Do not commit or push.

The accepted manager/Polkit adapter and the accepted `start`, `stop`,
`consume`, `attest`, `hold`, `stop-post` and `backstop` roles are not reopened.
Do not weaken their artifact, authorization, attribution, result, timeout or
test boundaries to make this remediation pass.

## Read before editing

1. `.agents/AGENTS.md` in full.
2. `docs/implementation-plan.md`: its reading map, §§0, 12 Phase 5.0, 13,
   14, 16 and 20.
3. `docs/review/Handover information`.
4. `docs/project-management/active-delivery-plan.md`.
5. `docs/operations/disposable-test-server.md`.
6. `docs/review/route-3-executor-oc-implementation-claude-prompt.md`,
   `docs/review/route-3-executor-oc-implementation-completion-claude-prompt.md`
   and the complete current
   `docs/review/route-3-executor-oc-implementation-handback.md`.
7. The one-host amendment §4.2.5-R6(b)–(d), especially OC-1–OC-3, durable by
   construction, Lemma R6 and the fixed A-2 interruption boundary.
8. The operation inventory's scope and roster, SA-2, §5.1 RT-1, §6
   SA-1/SA-2, §§7, 8.1, the OC reconciliation rows and CX-3.
9. The interface contract §§3.0, 3.1 and 3.7.
10. `application/executor/interrupt.py`, `adapters/executor/interrupt.py`,
    `adapters/executor/supervision.py`, all executor tests, the accepted SA-2
    implementation, and the complete current diff.

Historical WP closure labels are not current development gates. Their accepted
OC, DI-1, DI-S, SA-2 and A-2 requirements remain implementation inputs.

## Blocking finding 1 — `UNSETTLED` returns without settlement

The completion assignment requires affirmative evidence, on every return after
a successful launch, that the launched `sudo`, SA-2 and every process still
belonging to that invocation have exited. It also says explicitly that a typed
`UNSETTLED` result is honest uncertainty but is not process settlement.

The current `SudoStopInvoker` violates that invariant. `_settle()` can fail to
reach `ECHILD`; `_after_settling()` then returns `PrivilegedStop.UNSETTLED`;
`invoke_stop()` closes `KernelScope` and returns to the caller. The real-process
test for `orphan-forever` proves the behavior: the invoker returns while the
60-second descendant remains alive, and the test itself kills that descendant
afterward. The handback also records that a root process which ignores
`SIGTERM` after `sudo` is killed stays running.

The correction must satisfy the original lifecycle invariant rather than
rename the uncertainty:

- after a successful launch, every normal result or raised ordinary exception
  may leave the invoker only after a kernel-backed observation proves that no
  invocation member remains;
- timeout, `SIGTERM`, `SIGINT`, a direct-child exit, a descendant created
  during termination, reparenting, a lost launch handle and repeated signals
  must not abandon the invocation;
- no unrelated process may be targeted or accepted as part of the invocation
  from a numeric PID, name, command string or stale `/proc` observation;
- the ordinary successful SA-2 path must remain prompt and must not pay a
  termination grace period;
- resource use must remain bounded, SA-2 must never be retried, and no later
  unit observation may promote uncertainty to success; and
- the exact accepted privileged vector remains
  `sudo -n /usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py stop`.

Deleting `UNSETTLED`, waiting forever, suppressing termination indefinitely,
broad process killing, assuming SA-2 never hangs, or returning another error
while a member remains does not close the finding. A test that cleans up the
surviving process after the invoker returns proves the defect; it does not
prove production settlement.

### Authority stop if the fixed vector cannot satisfy the invariant

An unprivileged executor may be unable to guarantee bounded termination of an
arbitrary root descendant once `sudo` has exited or been killed. Investigate
kernel-backed solutions that preserve the fixed vector, but do not invent a
false guarantee or add a broader privileged capability.

If bounded affirmative settlement is technically impossible under the exact
accepted boundary, stop implementation of finding 1 and return a concise,
evidence-backed engineering decision instead. It must state:

1. the exact kernel/credential reason the fixed vector cannot meet the
   invariant;
2. the smallest supervision or privilege-boundary change that would meet it;
3. the security, authorization and performance consequences;
4. the focused tests and disposable-host proof that would establish it; and
5. the precise maintainer decision required before implementation.

Do not implement such a boundary change without Peter's explicit approval.
Finding 2 may still be corrected and tested independently, but the executor
slice must remain unaccepted and no successor slice may be assigned while the
lifecycle decision is open.

### Required lifecycle regressions

If finding 1 is implementable without a new authority decision, cover at least:

1. normal exit 0, 20, 21, 22, an unexpected status and signal death, each with
   the expected typed result and no invocation member left;
2. timeout, `SIGTERM` and `SIGINT`, including a direct child that initially
   ignores termination;
3. a descendant present before termination and one created during the
   termination race;
4. a direct child that exits before discovery while a descendant remains;
5. a privileged descendant that ignores `SIGTERM`, proving it is gone before
   return rather than deleted by test cleanup afterward;
6. repeated executor signals during settlement;
7. interruption or an ordinary exception inside the launch window after a
   child may have been created;
8. inconsistent identity evidence and PID-reuse pressure, proving no unrelated
   target is signalled or reaped;
9. process/resource-cap exhaustion without returning while a member survives;
   and
10. unchanged refusal before launch when the scope is unavailable or an
    unrelated child already exists.

Use deterministic synchronization for race tests. Do not rely on arbitrary
sleeps as the only reason a process is believed gone.

## Blocking finding 2 — journal name and metadata are not revalidated

`LocalConsumeJournalReader` currently checks the initial directory and file,
reads through the opened file descriptor, compares only the file's
`(size, ino, dev)` afterward, and reopens only the directory identity. It does
not establish that the directory entry named `journal` still identifies the
opened object. It also does not reject a concurrent change to required file or
directory ownership, mode or link count.

Independent review reproduced all of these on the current tree:

- replacing `journal` during `_read_capped()` caused the reader to return the
  old object's bytes while the name referred to a new object;
- changing the file mode from `0644` to `0600` during the read was accepted;
  and
- changing the evidence-directory mode from `0755` to `0700` during the read
  was accepted.

The correction must keep the fixed activation-derived path, descriptor-first
resolution, `O_NOFOLLOW`, byte cap and no caller-selected path. For one bounded
observation it must:

- retain the opened file's initial complete security-relevant identity and
  metadata;
- after the read, revalidate the opened object, including regular-file type,
  device, inode, owner, group, exact `0644` mode, link count one, size and
  metadata timestamps needed to detect in-place disagreement;
- perform a no-follow, descriptor-relative re-observation of the `journal`
  name and require it to identify that same acceptable opened object;
- re-resolve the fixed directory without following links and require the same
  directory identity plus root ownership and exact `0755` mode at the end;
- reject replacement, unlink/relink, hard-link creation, ownership/mode/type
  change, shrinkage, growth, short read, I/O failure or any metadata
  disagreement as unavailable; and
- close every descriptor exactly once on every success and failure path,
  preserving the accepted close-error discipline.

Do not compare pathnames alone, follow a symlink during revalidation, widen
permissions, make a second content read, or accept the original descriptor
merely because its bytes still parse. The application layer must continue to
parse only the returned immutable bytes and must never invoke SA-2 after a
reader rejection.

### Required journal regressions

Add deterministic fault-injection tests for at least:

1. atomic replacement of `journal` with another root-owned `0644`, one-link
   regular file of the same size;
2. unlinking or renaming the journal after it was opened;
3. file mode, owner/group and link-count changes during the read;
4. directory mode and owner/group changes during the read;
5. same-size in-place content/metadata change;
6. directory replacement while the opened file itself remains unchanged;
7. the existing short-read, growth, oversized, symlink and non-regular cases;
   and
8. a positive unchanged object whose exact bytes still pass OC-2/OC-3 and
   invoke SA-2 once.

For every damaged case assert the typed unavailable result, zero privileged
launches, one unit observation, one journal-reader attempt and no filesystem or
unit mutation by the executor. Use root-only ownership-change cases in the
disposable-host module where the local unit test cannot perform them.

## Required verification

All test levels remain authorized on `oracle-test`. Use synthetic data and the
documented secret-excluding synchronization command. Do not touch production,
staging, real secrets or player data.

If both findings are implemented, run on the final synchronized tree:

1. the complete executor application/adapter/supervision tests, including all
   new red-before/fixed-after regressions;
2. the complete executor host module as root, while its entry and privileged
   transition still exercise real `ubuntu -> sudo -n -> SA-2` behavior;
3. focused accepted `stop`, `consume`, `attest`, manager, artifact and
   unit-control regressions;
4. the complete `tests/systemd_integration` suite serially;
5. `tests/web/test_p3_4_static_assets.py`;
6. the documented bot and web suites serially with
   `TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'`, confirming the web
   skip count remains 80;
7. the Foundry Node suite;
8. Python compilation, repository guard tests, configured lint/type/static
   checks and `git diff --check`; and
9. a separate final host-cleanliness inspection.

Report reliable statuses and actual pass/fail/error/skip counts. Compare any
claimed pre-existing failure with the applicable accepted baseline; do not
repair unrelated evidence-harness files in this slice. Rerun the complete bot
and web suites after the final code change, serially, because they share the
disposable database. Give the exact invocation where root privilege,
environment, ordering, status propagation or a reboot affects what the result
proves; routine successful commands may cite the canonical repository
procedure.

The final cleanliness check must show no executor, `sudo`, SA-2 or invocation
member; no RP-11 test unit, artifact, Polkit rule, staging/store path, synthetic
activation evidence or test log; `polkit.service` active; `/var/tmp` still
`root:root 1777`; and the protected pre-existing
`/var/tmp/p5-r5-rp11-h0*` directories unchanged.

If finding 1 instead reaches the authority stop, run the complete focused
journal tests and proportionate regressions for finding 2. Run only the
experiments needed to establish the lifecycle impossibility and proposed
boundary; do not claim the executor suite accepted or rerun unrelated full
suites merely to produce a green count.

## Acceptance criteria

- No code path returns or propagates an ordinary exception after a successful
  privileged launch while any invocation member remains, or the handback
  clearly stops on the documented authority decision without claiming
  completion.
- Process identity and exit evidence remain kernel-backed and resistant to
  reparenting and PID reuse; no unrelated process is targeted.
- SA-2 is invoked at most once and uncertainty is never retried or promoted to
  success.
- Journal bytes are accepted only when the opened file, its fixed name binding
  and its directory retain the exact required identity and metadata throughout
  the bounded observation.
- Every replacement or metadata-disagreement regression is unavailable and
  launches no privileged process.
- Exact OC-1/OC-2/OC-3 success, CX-3, Lemma R6, stable diagnostics and the fixed
  unit/argv/environment boundary remain unchanged.
- Accepted Route 3 roles have no demonstrated regression, the disposable host
  is clean, and production/staging remain untouched.

## Handback and current-state discipline

Append one concise **Executor review remediation** section to
`docs/review/route-3-executor-oc-implementation-handback.md`; do not create a
new handback or rewrite its historical implementation sections. Include:

- both findings and their exact dispositions;
- the final process-lifecycle mechanism and why every post-launch return has
  affirmative kernel evidence, or the bounded engineering decision and exact
  maintainer question if that is impossible;
- the journal name-binding and metadata-revalidation rule;
- red-before and fixed-after outcomes for the reproduced races;
- principal files changed;
- material final-tree test and host results, including every failure/error/skip
  and its disposition;
- final host-cleanliness state;
- unchanged or newly identified production risks; and
- one recommendation: accept the executor OC slice for continued
  non-production development, or keep it blocked on one precisely named
  remediation/authority decision.

Do not record Peter's acceptance, assign the coordinator/start-orchestration
slice, authorize a production installer or activation, or create another
review/remediation document. Return the complete uncommitted candidate for
independent Codex re-review.
