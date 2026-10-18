# Claude remediation prompt — Route 3 `attest` fifth review finding

Date: 2026-10-18
Authority: Peter Duscha's explicit request, baseline v1.9, the active
implementation-first delivery plan, and the independent Codex review of the
fourth-remediated uncommitted RT-5 candidate
Mode: one bounded implementation and verification remediation on `oracle-test`;
no production or staging activation

> **Current-state evidence clarification, 2026-10-18.** Peter Duscha superseded
> this completed prompt's command-transcription requirements with the
> implementation-evidence standard in `.agents/AGENTS.md`. The behavioral,
> security, reliable-status, failure-disclosure and baseline-comparison
> requirements below remain in force. Routine command transcription and its
> formatting are not acceptance gates when the material implementation claims
> and results can otherwise be independently assessed. An exact invocation is
> still required when privilege, environment, ordering, reboot phases or status
> propagation materially affects what it proves. This clarification does not
> weaken the later production security review or authorize production/staging
> activation.

## Assignment

Close the remaining RT-5 changed-boot false-success path in the exact tree-P
evidence check. A canonically serialized, correctly chained ACT journal whose
tree-P history is not the exact production history can still contribute to
`st1-verified` and exit 0.

Add regressions that reproduce every case below before the correction, make the
smallest RT-5-scoped fail-closed change, rerun the required checks on the final
tree, and append one concise **Fifth review remediation** section to the existing
attest handback.

Do not implement the non-root executor, OC-1/OC-2/OC-3, a production
capture-unit installer, migration/cutover work, production or staging
activation, or unrelated cleanup. Preserve unrelated working-tree changes. Do
not commit or push.

The accepted manager/Polkit adapter, `consume`, `start`, `stop`, `hold`,
`stop-post` and `backstop` behavior is not reopened. Continue to reuse
`CleanupProcedure`; do not copy cleanup, attribution, PK/2, publication or
removal logic into the attest module. Any shared-code correction must remain
trigger-scoped so accepted role semantics do not change.

## Read before editing

1. `.agents/AGENTS.md` in full.
2. `docs/implementation-plan.md`: reading map, §§0, 12 Phase 5.0, 13, 14, 16
   and 20.
3. `docs/review/Handover information`.
4. `docs/project-management/active-delivery-plan.md`.
5. `docs/operations/disposable-test-server.md`.
6. `docs/review/route-3-attest-role-implementation-claude-prompt.md`, all four
   earlier attest remediation prompts, and the complete
   `docs/review/route-3-attest-role-implementation-handback.md`.
7. The operation inventory §§3 RT-5, 4.5, 4.6, 4.16, 5.5, 6 RT-5, 7, 8.1 and
   10, plus the RT-5 rows and reconciliation tables in §§11–12, especially
   H-JRN.9, H-PT, CL-1, CL-5b, CL-6, CL-7 and `cleared-by-boot`.
8. The interface contract §§3.0, 3.1, 3.5 and 3.6.
9. `application/rp11/evidence.py`, `application/rp11/cleanup.py`,
   `application/rp11/journal.py`, `application/rp11/hold.py`,
   `application/rp11/publish.py`, the current RT-5 tests, the reboot host test,
   and the complete current diff from accepted commit `94fb3e7`.

Historical WP closure labels are not current development gates. Their accepted
RT-5, H-CL, H-JRN, H-PT, H-GRR, H-PK2, H-SN and DI-1/DI-5/DI-6 requirements
remain implementation inputs.

## Blocking finding — the exact tree-P check discards evidence fields

The third remediation added `TreeEvidence.is_exactly(...)` and
`CleanupProcedure._tree_p_recorded()`, but the evidence projection is lossy:

- `TreeEvidence.declared_files` retains only each file path, discarding the
  tree-intent member's mode, SHA-256 and size;
- `act_evidence()` builds directory declarations through a dictionary keyed by
  `rel`, so an exact duplicate declaration is silently collapsed; and
- a `dir-identity` whose `rel` is not declared by the current tree intent is
  silently ignored rather than making that tree history inexact.

`is_exactly()` therefore proves only a subset of the production tree-P shape.
It does not establish that the original ordered member inventory and identity
history are exact.

Independent review reproduced five cases on the synchronized final tree. Each
case:

1. created the normal valid synthetic activation;
2. cleared its `/run` objects and changed the boot ID;
3. changed only the tree-P history;
4. rebuilt the ACT journal with production `serialize_line`, contiguous
   sequence numbers and the correct `prev` digest chain;
5. confirmed `parse_journal(...).valid` was true; and
6. ran RT-5 with positive PK/2 `not-authorized` and an equal baseline.

The five changes were:

1. tree-P's `pass-a.json` member mode changed from `0644` to `0600`;
2. its member SHA-256 changed to another valid lowercase digest;
3. its member size changed by one;
4. a duplicate copy of the top-directory member declaration was inserted; and
5. an extra `dir-identity` for undeclared relative path `not-declared` was
   inserted while the required identity remained present.

All five returned exit 0 and terminal `st1-verified`. This violates the third
remediation's requirement that a malformed, duplicated, wrong-member or hybrid
tree-P history cannot substitute for the exact production tree shape, and its
acceptance criterion that a syntactically valid but semantically incomplete or
inconsistent tree history fails closed.

## Required correction

Make RT-5 fail closed after a boot change unless tree P has exactly the history
the production publisher emits:

- preserve and compare the complete ordered `tree-intent.members` sequence;
- require exactly one top-directory declaration `.` with mode `0755`;
- require exactly one `pass-a.json` file declaration with mode `0644`, the
  A-2-pinned pass-config SHA-256, and the exact pinned pass-config byte length;
- reject duplicate directory or file member declarations, including exact
  duplicates that a dictionary would otherwise collapse;
- reject every `dir-identity` not naming one declared directory member;
- require exactly one identity for each required directory, in production
  order and before the matching link, subject only to the already accepted
  exact durable-prior-removal rule for a missing old identity;
- retain the existing exact parent, top, temporary name, tag, one matching
  `tree-linked` line and ordering requirements; and
- reject extra, missing, reordered, mismatched or hybrid tree-P evidence rather
  than choosing or projecting a convenient subset.

Derive variable expected facts from the already validated A-2/H-1 authority
chain; do not introduce a second source of truth. A file member's expected
digest and size must agree with the pinned canonical `pass-a.json` bytes, not
merely with another untrusted ACT-journal field.

Keep this an RT-5 changed-boot success-eligibility rule. Do not make historical
ACT journals globally unparsable, make every cleanup trigger reject these
histories, loosen the journal grammar, infer proof from pathname absence,
rerun PK/2, or add another cleanup implementation. Same-boot RT-5 and accepted
`stop-post` and `backstop` semantics must remain unchanged.

Do not remove any A0, damaged, foreign, uninspected, unprovable or unremovable
object. If the existing trusted authority data cannot establish one of the
expected production member facts, stop and report that precise evidence gap
rather than inventing a value.

## Required regressions

Use production parsing and serialization, not a mock that bypasses evidence
derivation. Add at least:

1. the three exact changed-boot file-member cases above: wrong mode, wrong
   SHA-256 and wrong size;
2. an exact duplicate top-directory member declaration;
3. an exact duplicate file-member declaration;
4. an undeclared `dir-identity` both before and after the required identity;
5. duplicated, missing and reordered required directory identities;
6. a directory declaration duplicated with a conflicting mode;
7. a positive changed-boot activation with the exact production member fields,
   every required identity, matching link, real positive PK/2 and equal
   baseline, which still reaches `st1-verified`;
8. the existing tree-P intent/link omission, wrong parent/top/tag/temp/member,
   activation-created tree-R, genuinely pre-existing rules directory and exact
   durable-prior-removal controls; and
9. unchanged same-boot RT-5, `stop-post` and `backstop` positive controls.

Every damaged changed-boot case must require exit 1, `hard-stop`,
`st1.verified == false`, no `st1-verified` journal or record claim and the
stable closed failure token `st1-not-verified`. Positive PK/2 and equal baseline
must be asserted so they cannot mask incomplete evidence.

Demonstrate that the five independently reproduced cases fail their hard-stop
assertions against the pre-fix candidate, then pass after the correction. Keep
the red-before evidence concise and in the existing handback; do not create a
separate proof document.

## Disposable-host proof

Use synthetic data and the documented secret-excluding synchronization
command. On `oracle-test`, build a fresh root-owned controlled artifact from
the pinned Jeepney wheel.

Repeat the installed exact `sudo -n` proof after a real reboot. In addition to
the valid-evidence A, planted-path B, missing-evidence C and missing-intent/link
D/E cases, add or adapt at least one case whose ACT journal remains canonical
and correctly chained but contains one of the newly covered lossy-projection
histories. It must hard-stop through the installed vector and must not publish
`st1-verified`.

Teardown must leave no RP-11 unit, process, Polkit rule, artifact,
staging/store path, attempt evidence, proof-state file or test log;
`polkit.service` must be active, `/var/tmp` must be `root:root 1777`, and the
six protected pre-existing `/var/tmp/p5-r5-rp11-h0*` directories must remain
unchanged. Do not restart Polkit merely to make rule removal observable; reboot
only the disposable host.

## Required verification

Re-sync after the final code change and run on the final tree:

1. the new red-before/fixed-after regressions and complete
   `tests/test_rp11_attest.py`;
2. the focused RT-5/cleanup/consume/artifact/hold/backstop/records/PK/start/
   stop/unit-control set used by the prior remediation;
3. `tests/systemd_integration/test_route3_attest_host.py` as root with a fresh
   controlled artifact;
4. the literal real-reboot prepare, reboot, readiness, verify and cleanup
   sequence, including the new semantically inconsistent installed-vector case;
5. the complete `tests/systemd_integration` suite serially;
6. `tests/web/test_p3_4_static_assets.py`, with any claimed baseline failure
   freshly reproduced against accepted commit `94fb3e7`;
7. the documented bot and web suites serially with
   `TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'`, confirming the web
   skip count remains 80;
8. the Foundry Node suite with the remote Node status saved, printed and
   propagated through SSH;
9. Python compilation over every touched Python path, repository guard tests,
   configured static checks and `git diff --check`, including every untracked
   file; and
10. separate post-root-test, post-reboot and final host-cleanliness inspection.

Record exact copy-pastable commands actually run, working directories, material
environment variables, reliable exit statuses, pass/fail/error/skip counts and
every skip reason. Do not use placeholders, ellipses, backward references or a
pipeline/trailing command that masks the tested process's status. Do not call a
failure pre-existing without an exact final-tree/baseline comparison. Never run
bot and web suites in parallel.

Production, staging, real secrets and real player data remain outside the
authority.

## Acceptance criteria

- RT-5 cannot publish `st1-verified` or exit 0 after a boot change when any
  tree-P member field, declaration cardinality or directory identity history
  differs from the production shape.
- The five independently reproduced canonical-journal cases hard-stop with
  `st1-not-verified` even when PK/2 is positively not-authorized and the
  baseline is equal.
- Duplicate declarations cannot disappear through dictionary projection, and
  undeclared identities cannot be silently ignored.
- The expected pass-config mode, digest and size come from the trusted
  authority chain and match the production publisher's member declaration.
- Complete changed-boot evidence still succeeds through real PK/2 and baseline
  checks; genuine pre-existing directory and exact prior-removal behavior stay
  intact.
- Same-boot RT-5 and accepted `stop-post`, `backstop`, `hold`, `consume`,
  `start` and `stop` behavior remain unchanged.
- The handback contains exact final-tree commands with reliable exit statuses.
- The disposable host is clean and production/staging remain untouched.

## Handback

Append one concise **Fifth review remediation** section to
`docs/review/route-3-attest-role-implementation-handback.md`; do not create a
new handback or rewrite the historical remediation sections. Include:

- the finding and exact disposition;
- the lossless exact-tree evidence rule;
- red-before and fixed-after outcomes for all five reproduced cases;
- the repeated real-reboot outcome including the new inconsistent-history
  installed-vector case;
- principal files changed;
- exact final-tree commands and results, including failures and skips;
- separate host-cleanliness results;
- unchanged remaining production risks; and
- one recommendation: accept RT-5 for continued non-production development or
  remediate one specifically named remaining blocker.

Update concise current-state documents only enough to say that this fifth
remediation was returned for independent Codex re-review. Do not record Peter's
acceptance, assign the non-root executor or OC checks, or authorize production
or staging. Return the complete uncommitted candidate for independent Codex
re-review.
