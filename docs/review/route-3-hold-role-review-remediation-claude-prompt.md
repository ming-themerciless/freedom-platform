# Claude remediation prompt — Route 3 `hold` review findings

Date: 2026-10-13
Authority: baseline v1.9, active handover, active delivery plan and Codex review
of `docs/review/route-3-hold-role-implementation-handback.md`
Mode: one bounded remediation cycle; implementation and full disposable-host
testing; no production activation

## Assignment

Remediate the three findings below in the current working tree. Do not return a
new plan, research package or contract reinterpretation. Add regression tests
that fail for the contract defects, implement the smallest fixes, run the
required checks on `oracle-test`, and update the existing hold handback in
place.

Preserve unrelated working-tree changes. Do not commit or push. Do not add a
production caller, installer, `consume`, `attest`, static `start`/`stop`, or any
production/staging activation.

## Read before editing

1. `.agents/AGENTS.md` in full.
2. `docs/implementation-plan.md`: reading map, §§0, 12 Phase 5.0, 13, 14, 16
   and 20.
3. `docs/review/Handover information`.
4. `docs/project-management/active-delivery-plan.md`.
5. `docs/operations/disposable-test-server.md`.
6. `docs/review/route-3-hold-role-implementation-claude-prompt.md` and
   `docs/review/route-3-hold-role-implementation-handback.md`.
7. From the operation inventory, the shared journal/record helpers and RT-2
   rows `AM0.1`, `AM0.16`, `AM3.1`, `AM3.2`, and `IGR.1` through `IGR.4`.

Historical closure labels are not development gates, but the accepted
non-GAP operation rows named above remain the behavior contract for this
slice. Reversible placement and representation choices may be made and pinned
in tests; required evidence fields may not be silently deleted.

## Required fixes

### 1. Restore the complete ACT `run-start` contract

The implementation currently emits and validates a reduced `run-start`. It
omits fields required by `RT2.AM0.16` and changes the required lock envelope.

- Make the ACT journal's closed `run-start` schema and emitted line include:
  - `h2_record_sha256`;
  - `helper {role, image_sha256[], tool_sha256}`; and
  - `lock {object {path, dev, ino}, mode, wait_ms}`.
- Preserve all currently required capture, lease, parameter, authority and
  provenance fields.
- Source authority values from the validated A-2/H-1 chain or the verified
  artifact facts, as the accepted row requires. Do not take them from the
  environment or synthesize a digest from an unverified path.
- If the chosen A-2 schema must carry `h2_record_sha256` or pinned image/tool
  identities, evolve that schema narrowly, update every parser/fixture/cleanup
  consumer consistently, and retain strict closed-key and digest validation.
- Do not weaken journal parsing to accept both the reduced and complete schema
  indefinitely. This inactive slice has no production-format compatibility
  obligation; use one explicit schema version and test rejection of missing,
  malformed and extra fields.
- Add assertions against the exact complete first journal line, not merely the
  presence of `run-start` or a subset of its fields.

### 2. Restore the IGR identity evidence and resolve `run-end`

`RT2.IGR.3` requires the best-effort ACT line `igr {outcome, identity}`. The
current code and journal schema record only `outcome`.

- Add the identity field to the closed `igr` schema and emitted line.
- Record the in-memory grant identity used by GRR when one exists. Represent
  the pre-AM-2/no-grant case with the repository's existing explicit-absence
  convention and a closed typed grammar; do not infer identity by reopening a
  path after removal.
- Preserve the ordering: decide/remove the grant first, then append and flush
  the IGR line best effort. A failed or stalled evidence write must never keep
  a grant live or turn a removal into a false success.
- Test removed, absent, damaged/foreign, unremovable and broken-journal paths,
  including exact identity contents and the existing exactly-once latch.

`RT2.AM3.2` is `A;Q4-11`, not a GAP row: the ACT journal's closed operation set
includes `run-end`, although its placement was left for implementation.

- Select one safe placement and outcome vocabulary for `run-end`, document the
  reversible choice in the code/test, and emit it consistently without
  claiming success for an incomplete activation.
- Preserve `hold-end` as the holder's complete-end evidence and preserve the
  required K-close and IGR ordering. Pin the exact order of `hold-end`,
  `run-end`, K release and `igr` for normal, observation-failed,
  start-before-hold, interrupted and unexpected-exception paths where each
  line is applicable.
- If the accepted sources truly make a safe placement impossible rather than
  merely unspecified, stop this item and identify the precise conflicting
  rows for Peter. Do not solve the conflict by continuing to claim AM3.2 is
  covered while omitting the operation.

### 3. Produce valid final-tree regression evidence

The latest complete bot-suite run in the handback had five failures outside
the established baseline. The affected modules passed alone, but the complete
suite was not rerun, so the statement that the final tree introduced no new
failure is not established.

- Start from a clean disposable test state. Remove only test artifacts created
  by this work; preserve unrelated host files. Recreate the disposable
  `freedom_test` database if the interrupted backup/restore drill may have left
  it dirty.
- Synchronize the final workspace with the documented secret-excluding
  command.
- Run the bot and web suites serially, never concurrently, with the documented
  PostgreSQL 16 `PATH`, the `/opt/freedom-blades/runtime/venv-web` interpreter,
  and exported `TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'`.
- A targeted rerun may diagnose a failure but is not the final regression
  evidence. After any environment cleanup, test change or code change, rerun
  the complete affected suite against the exact final tree.
- Do not label an OOM-killed or otherwise incomplete run as evidence. Do not
  weaken tests or repair unrelated baseline failures.
- Compare exact failed/error/skipped test identities with the established
  baseline. If a new full-suite failure repeats and is demonstrably unrelated,
  report it as an unresolved blocker rather than asserting no regression.

## Required testing

All test levels are authorized on `oracle-test`; production and staging remain
out of scope. Use only synthetic fixtures.

Run, at minimum, in this order:

1. focused hold, cleanup, backstop, PK/SN, artifact and unit-control suites;
2. the complete root systemd integration suite with the pinned Jeepney wheel;
3. the complete bot suite;
4. the complete web suite, confirming the correct database-enabled skip count;
5. the complete Foundry Node suite;
6. `.claude/hooks/test_guards.py`;
7. `git diff --check`, `compileall`, and every configured formatter, linter or
   type checker (or state explicitly that none is configured).

Exercise at least these new regression cases directly:

- exact complete `run-start` keys and nested shapes;
- missing, malformed and extra new authority/journal fields fail closed;
- IGR records the exact in-memory identity for every removal outcome and an
  explicit absence before AM-2;
- IGR still removes first when its identity-bearing journal append fails;
- the selected `run-end` order on every applicable terminal class; and
- cleanup parses and attributes the revised journal without broadening any
  removal authority.

After root tests, verify that no holder/backstop unit, process, Polkit rule,
capture unit, Route 3 `/run` object, temporary artifact or new test evidence
remains, and that `polkit.service` is active.

## Acceptance criteria

- `run-start` exactly implements `RT2.AM0.16`, including the authority,
  helper and lock fields named above.
- IGR exactly implements `RT2.IGR.3`: removal decision first, then best-effort
  `{outcome, identity}` evidence, with no unsafe re-open.
- `RT2.AM3.2` has an implemented and tested `run-end` placement, or a precise
  maintainer-only conflict is reported without a false coverage claim.
- Revised parsing and cleanup remain fail closed and never remove an
  unattributed, damaged, foreign or replaced object.
- Focused and real-PID-1 tests pass.
- A completed final-tree bot suite has no failure or error outside the accepted
  baseline; the database-enabled web suite has the correct skip count; Foundry
  has no regression.
- No production/staging state, real secret or player data is touched.

## Handback

Update `docs/review/route-3-hold-role-implementation-handback.md` in place with
one concise final remediation section. Remove or correct superseded claims so
the document has one unambiguous current result. Include only:

- each of these three findings and its disposition;
- principal files changed;
- exact final-tree commands and results, including failures/errors/skips;
- the selected authority, identity and `run-end` representations;
- real-host cleanup confirmation;
- remaining production risks; and
- one recommendation: accept the complete role series, remediate one named
  blocker, or replace the approach.

Do not create another prompt, handback, proof chain, source-completion record,
hash ledger or recursive review package.
