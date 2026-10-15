# Claude remediation prompt — Route 3 security re-review findings

Date: 2026-10-14
Authority: baseline v1.9, the active handover and delivery plan, Peter Duscha's
request for remediation, and the independent Codex re-review of the uncommitted
Route 3 security remediation
Mode: one bounded implementation and verification cycle on the disposable host;
no production or staging activation

## Assignment

Remediate the three findings from the independent re-review of the Route 3
security-remediation tree. All three findings block acceptance because they can
allow the last automatic recovery owner to be disarmed without established
Polkit non-authorization, or allow contradictory durable evidence to authorize
that decision.

Add regression tests that fail on the current tree, implement the smallest
fail-closed corrections, run the required checks on `oracle-test`, and update
the existing Route 3 hold-role handback in place. Do not return a plan or a
paper-only proposal. Do not create another handback, review, proof chain,
contract package or remediation prompt. Do not commit or push.

This assignment authorizes implementation and every required test on the
disposable host, including root/systemd/Polkit operations and deterministic
failure injection. It does **not** authorize production or staging mutation,
production activation, installation of the future `tmpfiles.d` entry, use of
real secrets or player data, or weakening authorization or recovery controls.

Preserve unrelated working-tree changes and the correctly implemented portions
of the current remediation: the distinct `UNINSPECTED` attribution and record
classes, conservative no-unlink boundary, bounded attempt/evidence growth,
complete nested record-shape validation, guarded ACT-record collision handling,
GRR exception safety, write-ahead removal, and all previously accepted Route 3
behavior not contradicted below.

## Read before editing

1. `.agents/AGENTS.md` in full.
2. `docs/implementation-plan.md`: its reading map, §§0, 9, 12 Phase 5.0, 13,
   14, 16 and 20.
3. `docs/review/Handover information`.
4. `docs/project-management/active-delivery-plan.md`.
5. `docs/operations/disposable-test-server.md`.
6. This prompt and the **Current security remediation — 2026-10-14** section
   of `docs/review/route-3-hold-role-implementation-handback.md`.
7. The affected implementation and tests end to end:
   `application/rp11/{backstop,cleanup,records,pk,canonical}.py`,
   `adapters/rp11/fsops.py`, `tests/test_rp11_{backstop,records,cleanup,hold}.py`,
   and `tests/systemd_integration/test_route3_backstop_host.py`.
8. The operation-inventory rows governing `H-REC`, `H-CL.7`, `H-GRR`,
   `RT3.CL7`, `RT4.BS2`, `RT4.BS3` and `RT4.BS4`.

Historical research gates and open Q labels are not current development
blockers. Make reversible implementation choices and pin them with tests. Stop
and ask Peter only if a necessary choice changes production authorization
policy or requires an irreversible architecture decision.

## Governing safety property

The prior remediation prompt requires:

> A possibly live Route 3 grant must never cause BS-2, BS-3 or the retry-bound
> terminal path to disarm its last automatic recovery owner.

Rule absence or a successful unlink is not by itself proof that Polkit no
longer authorizes the operator. Disarm is permitted only after the accepted
checks establish both:

1. the grant rule is absent/removed and no other blocking activation object
   remains; and
2. Polkit positively reports `not-authorized` after cleanup.

`unconfirmed`, `authorized`, unavailable, malformed, contradictory or missing
authorization evidence is never equivalent to `not-authorized`.

## Finding 1 — blocking: BS-3 still disarms after an unconfirmed Polkit check

`application/rp11/backstop.py::hard_stop_permits_disarm()` applies the new
positive `not-authorized` requirement only when the active rule is a retained
damaged or foreign file. It still permits BS-3 for removed/absent rule classes
when `grant_check.after_cleanup` and `pk.outcome` are `unconfirmed`.

The current generated reproduction is not hypothetical:

- cleanup emits a valid `hard-stop` with failure
  `{step: CL-4, class: grant-unconfirmed}`;
- `active_rule.class` is `removed-earlier`;
- `grant_check.after_cleanup` and `pk.outcome` are both `unconfirmed`;
- `residual` is empty; and
- the next firing selects BS-3 and calls DI-4.

`tests/test_rp11_backstop.py::_hard_stop` and
`test_a_qualifying_hard_stop_disarms_at_bs3` explicitly encode that unsafe
transition. `tests/test_rp11_records.py::test_a_valid_eligible_hard_stop_record_still_selects_bs3`
uses the same generated record. The current handback acknowledges the exposure
as remaining risk 5 while nevertheless claiming all blockers fixed.

### Required correction

- Make positive post-cleanup non-authorization a necessary BS-3 condition for
  **every** active-rule class, not only kept damaged/foreign files.
- A `hard-stop` whose post-cleanup Polkit result is `authorized`, `unconfirmed`,
  absent, contradictory or otherwise not positively `not-authorized` must take
  BS-4 and retain the timer; it must not call DI-4 or report successful recovery.
- Preserve safe BS-3 for a genuine hard-stop whose record is valid, all
  blocking objects are gone/non-authorizing, and post-cleanup Polkit
  non-authorization is positively established.
- Do not obtain a green result by reclassifying an error as `not-authorized`,
  deleting an unattributed object, or weakening the record schema.

## Finding 2 — blocking: the retry-bound path uses pathname absence as authorization proof

`BackstopProcedure._terminal()` currently calls DI-4 whenever
`fs.observe(rule)` returns `None`. It does not run or consult an accepted
post-cleanup Polkit non-authorization check. The existing test
`test_the_terminal_disarm_is_one_call_one_line_and_never_success` explicitly
asserts that the capture/authorization unit is never read.

A rule file can be absent while Polkit still has its effect loaded or while the
reload/non-authorization observation is unconfirmed. Therefore pathname absence
alone cannot establish the governing safety property.

### Required correction

- At `backstop_max` and attempt 99/100, never disarm solely because the rule
  pathname is absent.
- Retain or transfer an effective automatic recovery owner until accepted
  evidence establishes positive `not-authorized` after the rule became absent.
- A small reversible implementation may perform a bounded Polkit
  `seek-not-authorized` check at the terminal firing, using the same fixed
  parameters, typed outcomes and process/reaping safety as cleanup. Another
  design is acceptable only if it establishes the same fact without unbounded
  filesystem growth or silently losing the owner.
- If the rule is present/uninspectable, or the Polkit check is anything other
  than positive `not-authorized`, write the bounded terminal diagnostic with
  `disarm=withheld`, leave the timer active, and exit non-zero.
- If both rule absence and positive non-authorization are established, retain
  the existing one-call DI-4 behavior and typed handling of confirmed,
  unconfirmed, refused and error outcomes.
- Preserve the bound: no new attempt directory after the limit, no unbounded
  record/evidence growth, and the terminal journal remains capped.

## Finding 3 — blocking: contradictory authorization evidence passes validation and selects BS-3

The new validator checks complete nested shapes, but
`application/rp11/records.py::_cross_cleanup()` does not require
`grant_check.after_cleanup` to agree with `pk.outcome` and its mode/evidence.

Starting from a valid generated hard-stop with a retained foreign rule and
positive `not-authorized`, changing only `pk.outcome` to `unconfirmed` while
leaving `grant_check.after_cleanup == not-authorized` is accepted by
`validate_record()` and still selects BS-3. The durable record therefore claims
two incompatible outcomes, and the branch predicate trusts the favorable one.

### Required correction

- Add cleanup-record cross-field validation that binds
  `grant_check.after_cleanup` to the actual `pk.outcome` represented by the same
  record. They must agree exactly whenever a post-cleanup check exists.
- Validate the associated `pk.mode`, calls, outcome, reason and child/process
  evidence sufficiently to prevent an impossible or hollow positive
  `not-authorized` claim from selecting BS-2 or BS-3.
- Preserve legitimate cleanup records in which no Polkit check ran, but ensure
  they cannot select BS-2 or BS-3.
- Keep `validate_record()` total: every malformed or contradictory input raises
  `RecordSchemaError` only. `branch_for_record()` must select BS-4 without an
  exception and must never fall back to an older record.
- Do not merely make `hard_stop_permits_disarm()` inspect both contradictory
  values. The durable record itself must be rejected because the schema claims
  to be a complete closed evidence boundary.

## Required regression tests

Add tests that fail on the current tree before applying the fixes. At minimum
prove all of the following.

### BS-3 authorization gate

1. The current generated `removed-earlier` + `pk=UNCONFIRMED` hard-stop selects
   BS-4, performs another bounded recovery attempt below the bound, and never
   calls DI-4.
2. The same case with `authorized`, absent or other non-positive authorization
   evidence also cannot select BS-3.
3. Once a later cleanup establishes `not-authorized` and produces accepted
   evidence, normal BS-2 or safe BS-3 disarm remains functional.
4. Kept uninspected, live foreign, `removed-unconfirmed`, `grant-unremovable`
   and A1-intact residual cases remain blocking.
5. A retained damaged/foreign inert rule with positive `not-authorized` retains
   the previously selected safe behavior and is never removed merely to stop
   the timer.

### Retry-bound authorization gate

6. At both `backstop_max` and attempt 99/100, rule absence plus
   `unconfirmed`, `authorized`, refused, malformed or unavailable Polkit
   evidence yields `disarm=withheld`, no DI-4 and an active timer.
7. Rule absence plus positive `not-authorized` permits exactly one DI-4 call;
   all DI-4 result classes keep their existing typed exit/report behavior.
8. Persistent withheld firings create no new attempt directory or activation
   record and remain bounded by the terminal-journal cap.
9. The behavior is exercised under real PID 1: the timer state, rule path,
   Polkit result and diagnostic must agree.

### Record consistency

10. Starting from each valid generated cleanup record, every unequal pair of
    `grant_check.after_cleanup` and `pk.outcome` raises only
    `RecordSchemaError` and selects BS-4.
11. Cover `pk.mode`, calls/outcome combinations and any other fields the
    positive non-authorization claim relies upon; impossible combinations are
    rejected.
12. A canonical contradictory greatest record never lets an older verified
    record decide.
13. Valid generated activated, failed-ACT, verified-deactivation, safe
    hard-stop and non-disarming hard-stop records still validate as intended.

Mutation-test each correction: temporarily restore the current BS-3 predicate,
restore the absence-only terminal decision, and remove the new cleanup-record
cross-field relation. Show the new tests fail for each mutation, then revert
every mutation and confirm the submitted tree is restored.

## Required verification

Use only synthetic data. Synchronize the final tree with the exact
secret-excluding command in `docs/operations/disposable-test-server.md`. Run
the following serially on `oracle-test`:

1. the focused artifact-store, unit-control, Route 3 hold, cleanup, backstop,
   records, PK/SN, H-1 artifact and launch gate/source suites;
2. the complete root `tests/systemd_integration` suite with
   `FREEDOM_SYSTEMD_INTEGRATION=oracle-test`, the pinned Jeepney wheel and
   `/usr/sbin` available in `PATH`;
3. the complete bot suite;
4. the complete web suite with exported
   `TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'`, verifying the
   database-enabled skip count rather than accepting the fast all-skipped run;
5. the complete Foundry Node suite;
6. `python3 .claude/hooks/test_guards.py`;
7. `git diff --check`, `compileall`, and every configured formatter, linter or
   type checker, or an accurate statement that none is configured.

Bot and web must use
`/opt/freedom-blades/runtime/venv-web/bin/python`, PostgreSQL 16's explicit
`PATH`, and run serially against the shared disposable database. Targeted
reruns may diagnose failures but are not final regression evidence. Compare
exact failure, error and skip names and counts with the established baseline;
do not weaken tests, structural guards or authorization to obtain green output.

After root tests, verify that no RP-11 unit, holder/backstop process, Polkit
rule, capture unit, Route 3 `/run` object, test artifact or new evidence remains
and that `polkit.service` is active. Remove only disposable artifacts created by
this work.

## Acceptance criteria

- BS-3 requires positive post-cleanup `not-authorized` for every otherwise
  eligible hard-stop.
- The retry-bound path never treats pathname absence as sufficient proof of
  non-authorization.
- A possibly live grant never causes BS-2, BS-3 or the terminal bound to disarm
  its last automatic recovery owner.
- Persistent uncertainty remains fail-closed without unbounded attempt,
  record or journal growth.
- Contradictory Polkit evidence is rejected by `validate_record()` with
  `RecordSchemaError` and can select only BS-4.
- No unreadable, partially observed, damaged, foreign or replaced object gains
  removal authority.
- Valid ACT, cleanup, BS-2 and genuinely safe BS-3 behavior remains functional.
- Focused and real-PID-1 tests pass, and final-tree bot, web and Foundry suites
  introduce no regression relative to the accepted baseline.
- The implementation remains inactive; no production/staging state, real
  secret or player data is touched.

## Handback update

Update `docs/review/route-3-hold-role-implementation-handback.md` in place with
one concise section that supersedes its current security-remediation
recommendation. Do not create another handback.

Include only:

- the three re-review findings and their dispositions;
- the exact universal BS-3 non-authorization predicate;
- the selected bounded-terminal authorization check and withheld behavior;
- the record cross-field relations added;
- principal files changed;
- named regression and mutation tests;
- exact final-tree commands and results, including skips and unchanged
  baseline failures/errors;
- real-host timer/rule/Polkit outcomes and cleanup confirmation;
- remaining production risks, including the uninstalled/unproved
  `tmpfiles.d` ordering and retained PID/start-time subject risk; and
- one unambiguous recommendation: accept the inactive role series for
  continued development or remediate one specifically named blocker.

Remove the current claim that an unconfirmed Polkit result after rule removal
is an accepted BS-3 risk. Do not claim production activation readiness: the
independent reviewer must re-review this remediation, and the separate
`tmpfiles.d` installation/reboot gate remains open.
