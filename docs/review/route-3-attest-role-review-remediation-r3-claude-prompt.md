# Claude remediation prompt — Route 3 `attest` third review finding

Date: 2026-10-17
Authority: Peter Duscha's explicit request, baseline v1.9, the active
implementation-first delivery plan, and the independent Codex review of the
twice-remediated uncommitted RT-5 candidate
Mode: one bounded remediation and verification cycle on `oracle-test`; no
production or staging activation

## Assignment

Remediate the one remaining blocking false-success path in RT-5 `attest`:
after a boot change, a canonically valid and correctly chained ACT journal can
omit tree P's `tree-intent` or `tree-linked` line and still let RT-5 publish
`st1-verified` with directory class `never-created`.

Add regressions that reproduce both cases before the correction, make the
smallest RT-5-scoped fail-closed change, rerun the required checks on the final
tree, and append one concise **Third review remediation** section to the
existing attest handback.

The maintainer's request for this prompt explicitly supersedes the second
remediation prompt's instruction not to create another remediation prompt.
Nothing else in the earlier scope changes.

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
6. `docs/review/route-3-attest-role-implementation-claude-prompt.md`, both
   earlier attest remediation prompts, and
   `docs/review/route-3-attest-role-implementation-handback.md`.
7. The operation inventory §§3 RT-5, 4, 5.5, 6 RT-5, 7, 8.1 and 10, plus the
   RT-5 rows and reconciliation tables in §§11–12, especially CL-1, CL-4,
   CL-5b, CL-6, CL-7 and `cleared-by-boot`.
8. The interface contract §§3.0, 3.1, 3.5 and 3.6.
9. `application/rp11/cleanup.py`, `application/rp11/evidence.py`,
   `application/rp11/journal.py`, `application/rp11/hold.py`, the current RT-5
   tests, the reboot host test, and the complete current diff from accepted
   commit `94fb3e7`.

Historical WP closure labels are not current development gates. Their accepted
RT-5, H-CL, H-GRR, H-PK2, H-SN and DI-1/DI-5/DI-6 requirements remain
implementation inputs.

## Blocking finding — missing mandatory tree evidence still becomes success

The second remediation made `TreeEvidence.unidentified()` reject a missing
`dir-identity` inside a tree that `ActEvidence` already reconstructed as
linked. It does not establish that the mandatory tree itself was recorded and
linked.

`ActEvidence.unidentified_directories()` iterates only existing linked trees.
If tree P's `tree-intent` is absent, no tree P exists in `ActEvidence`. If its
`tree-linked` line is absent, tree P is excluded as unlinked. In both cases the
set of unidentified linked-tree directories is empty. Cleanup then classifies
the absent fixed tree-P path as `never-created`; `_attest_eligible()` does not
reject that class, and all other positive checks can produce success.

Independent review reproduced both cases on the synchronized final tree. For
each case it:

1. created the normal valid synthetic activation;
2. cleared its `/run` objects and changed the boot ID;
3. removed either tree P's `tree-intent` line or its `tree-linked` line;
4. rebuilt the journal with production `serialize_line`, contiguous sequence
   numbers and the correct `prev` digest chain;
5. confirmed `parse_journal(...).valid` was true; and
6. ran RT-5 with positive PK/2 `not-authorized` and an equal baseline.

Both cases returned exit 0 and terminal `st1-verified`; the directory classes
were `never-created`, `pre-existing-kept`, `cleared-by-boot`, with failure
`none`.

This violates the first remediation's requirement that missing, incomplete or
otherwise invalid ACT evidence cannot contribute to `st1-verified`, and the
RT-5 rule that every activation-owned `/run` object needed for ST-1 must have a
complete `cleared-by-boot` proof or an exact durable prior removal.

Make RT-5 fail closed so that:

- tree P is mandatory activation evidence, not merely one member of whatever
  linked trees happened to parse;
- its `tree-intent` must identify the expected fixed parent and top path, carry
  the expected directory inventory, and be followed by the matching durable
  `tree-linked` fact before it can support success;
- after a boot change, the required tree-P top identity must establish the
  existing `cleared-by-boot` proof, or a durable prior `removed` fact must cover
  that exact expected path;
- omitting the tree intent, tree link or required identity cannot yield
  `never-created` success, even with positive PK/2 and an equal baseline;
- a malformed, duplicated, reordered, mismatched-tag, wrong-parent,
  wrong-top, wrong-member or hybrid tree-P history cannot substitute for the
  exact production tree shape;
- the accepted conditional tree-R behavior remains correct: a genuinely
  pre-existing rules directory stays permitted, while an activation-created
  tree R still requires the evidence and identity rules from the second
  remediation;
- a durable prior removal remains sufficient only for the exact expected path
  and only under the existing prior-removal contract;
- no A0, damaged, foreign, uninspected, unprovable or unremovable object is
  removed; and
- same-boot valid cleanup and accepted `stop-post` and `backstop` behavior are
  unchanged.

Prefer an explicit RT-5 success-eligibility check over the expected production
tree shape. Do not make every `never-created` directory globally fatal, loosen
the journal grammar, infer proof from pathname absence, rerun PK/2, or add a
second cleanup implementation.

If the current durable evidence cannot distinguish an activation-created tree
R from a genuinely pre-existing rules directory for any newly discovered
case, stop and report that precise evidence gap rather than inventing a fact.

## Required regressions

Use production parsing and serialization, not a mock that bypasses evidence
derivation. Add at least:

1. the exact changed-boot tree-P `tree-intent` omission, requiring exit 1,
   `hard-stop`, `st1.verified == false`, no `st1-verified` journal/record claim
   and a stable closed failure token;
2. the exact changed-boot tree-P `tree-linked` omission with the same result;
3. both cases with positive PK/2 and an equal baseline, proving those checks
   cannot repair incomplete tree evidence;
4. wrong parent, wrong top, wrong tag and wrong declared directory inventory;
5. duplicate or mismatched tree-P intent/link histories that must not be
   accepted by choosing a convenient entry;
6. a positive changed-boot activation with the exact tree-P evidence and every
   required identity, which still reaches `st1-verified`;
7. the existing activation-created tree-R, genuinely pre-existing rules
   directory and exact durable-prior-removal positive controls; and
8. unchanged same-boot, `stop-post` and `backstop` positive controls.

Demonstrate that the two primary regressions fail against the pre-fix candidate
before applying the correction. Keep that red-before evidence concise; do not
create another proof document.

## Disposable-host proof

Use synthetic data and the documented secret-excluding synchronization
command. On `oracle-test`, build a fresh root-owned controlled artifact from
the pinned Jeepney wheel.

Repeat the installed exact `sudo -n` proof after a real reboot. In addition to
the existing valid-evidence A, planted-path B and missing-evidence C cases, add
or adapt one case so that an ACT journal whose tree-P intent or link is missing
cannot reach `st1-verified` through the installed vector. The journal must be
rebuilt canonically with the production serializer and remain structurally
valid, so this proves the semantic fail-closed rule rather than only malformed
JSON rejection.

Teardown must leave no RP-11 unit, process, Polkit rule, artifact,
staging/store path, attempt evidence, proof-state file or test log;
`polkit.service` must be active, `/var/tmp` must be `root:root 1777`, and the
six protected pre-existing `/var/tmp/p5-r5-rp11-h0*` directories must remain
unchanged. Do not restart Polkit merely to make rule removal observable; reboot
only the disposable host.

## Required verification

Re-sync after the final code change and run on the final tree:

1. the new regressions and complete `tests/test_rp11_attest.py`;
2. the focused RT-5/cleanup/consume/artifact/hold/backstop/records/PK/start/
   stop/unit-control set named in the earlier remediation prompts;
3. `tests/systemd_integration/test_route3_attest_host.py` as root with a fresh
   controlled artifact;
4. the literal real-reboot prepare, reboot, readiness, verify and cleanup
   sequence, including the new semantic-incompleteness host case;
5. the complete `tests/systemd_integration` suite serially;
6. `tests/web/test_p3_4_static_assets.py`, with any claimed baseline failure
   freshly reproduced against accepted commit `94fb3e7`;
7. the documented bot and web suites serially with
   `TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'`, confirming the web
   skip count remains 80;
8. the Foundry Node suite without a pipeline that masks `node`'s exit status;
9. Python compilation over every touched Python path, repository guard tests,
   configured static checks and `git diff --check`, including every untracked
   file; and
10. separate post-root-test and post-reboot host-cleanliness inspection.

Record exact copy-pastable commands actually run, working directories, material
environment variables, exit statuses, pass/fail/error/skip counts and every
skip reason. Do not use placeholders or a pipeline whose final command masks
the tested process's status. Do not call a failure pre-existing without an
exact final-tree/baseline comparison. Never run bot and web suites in parallel.

Production, staging, real secrets and real player data remain outside the
authority.

## Acceptance criteria

- RT-5 cannot publish `st1-verified` or exit 0 after a boot change when the
  mandatory tree-P intent, matching link or required identity is absent or
  inconsistent.
- A syntactically valid, canonically serialized and correctly chained but
  semantically incomplete tree history fails closed.
- `never-created` cannot substitute for complete tree-P boot-clearance evidence
  or an exact durable prior removal.
- Complete changed-boot evidence still succeeds through real PK/2 and baseline
  checks; genuine pre-existing directory behavior remains intact.
- Same-boot RT-5 and accepted `stop-post`, `backstop`, `hold`, `consume`,
  `start` and `stop` behavior remain unchanged.
- The handback contains exact final-tree commands with reliable exit statuses.
- The disposable host is clean and production/staging remain untouched.

## Handback

Append one concise **Third review remediation** section to
`docs/review/route-3-attest-role-implementation-handback.md`; do not create a
new handback. Include:

- the finding and exact disposition;
- the mandatory tree-P evidence rule;
- red-before and fixed-after outcomes for missing `tree-intent` and
  `tree-linked`;
- the repeated real-reboot outcomes, including the semantic-incompleteness
  installed-vector case;
- principal files changed;
- exact final-tree commands and results, including failures and skips;
- separate host-cleanliness results;
- unchanged remaining production risks; and
- one recommendation: accept RT-5 for continued non-production development or
  remediate one specifically named remaining blocker.

Update concise current-state documents only enough to say that this third
remediation was returned for independent Codex re-review. Do not record Peter's
acceptance, assign the non-root executor or OC checks, or authorize production
or staging. Return the complete uncommitted candidate for independent Codex
re-review.
