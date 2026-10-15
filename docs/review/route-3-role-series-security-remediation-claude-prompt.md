# Claude remediation prompt — Route 3 independent security review

Date: 2026-10-14
Authority: baseline v1.9, the active handover and delivery plan, and the
independent Codex security review of the complete inactive Route 3 role series
Mode: one bounded implementation and verification cycle on the disposable host;
no production or staging activation

## Assignment

Remediate the three findings from the independent security review of the
complete inactive Route 3 role series. Two findings block production
activation; the third is an important durable-evidence defect.

Add regression tests that reproduce each defect, implement the smallest
fail-closed corrections, run the required checks on `oracle-test`, and update
the existing Route 3 hold-role handback in place. Do not return a plan or a
paper-only proposal. Do not create another handback, review, proof chain,
contract package or remediation prompt. Do not commit or push.

This assignment authorizes implementation and every required test on the
disposable host, including root/systemd/Polkit operations and deterministic
failure injection. It does **not** authorize production or staging mutation,
production activation, installation of the future `tmpfiles.d` entry, use of
real secrets or player data, or weakening authorization or recovery controls.

Preserve unrelated working-tree changes and all accepted Route 3 behavior not
named below, including artifact isolation, the fixed manager/Polkit boundary,
GRR inspection- and descriptor-close exception safety, write-ahead removal,
pre-journal K/S0 handling, and `run-start`/`igr`/`run-end` evidence.

## Read before editing

1. `.agents/AGENTS.md` in full.
2. `docs/implementation-plan.md`: its reading map, §§0, 9, 12 Phase 5.0, 13,
   14, 16 and 20.
3. `docs/review/Handover information`.
4. `docs/project-management/active-delivery-plan.md`.
5. `docs/operations/disposable-test-server.md`.
6. The **Current result — GRR exception safety — 2026-10-14** section of
   `docs/review/route-3-hold-role-implementation-handback.md`, then the rest of
   that handback only as needed for the affected behavior.
7. The affected implementation and tests end to end:
   `application/rp11/{backstop,cleanup,records,canonical}.py`,
   `adapters/rp11/fsops.py`, `tests/test_rp11_{backstop,cleanup,hold}.py`, and
   `tests/systemd_integration/test_route3_{backstop,stop_post,hold}_host.py`.
8. From the operation inventory, the record, cleanup, GRR and backstop rows
   that govern `H-REC`, `H-CL.7`, `H-GRR`, `RT3.CL7`, `RT4.BS2`, `RT4.BS3`
   and `RT4.BS4`.

Historical research gates and open Q labels are not current development
blockers. Make reversible implementation choices and pin them with tests. If a
choice would change production authorization policy or require an irreversible
architecture decision, stop and ask Peter; otherwise implement it.

## Finding 1 — blocking: inspection uncertainty can lose its recovery owner

GRR now correctly keeps an object when inspection is incomplete, but the
result is collapsed into `kept-damaged` or `kept-foreign`. CL-3 consequently
records `present-damaged-unremoved` or `present-foreign-unremoved` even when
the object is still the intact activation grant and only its inspection
failed. `hard_stop_permits_disarm()` permits both classes. The next backstop
firing therefore takes BS-3, disarms the timer and exits successfully while the
rule may remain loaded and authorize the operator.

The current tests encode the unsafe transition:

- `tests/test_rp11_backstop.py::test_backstop_cl_g_survives_a_persistent_grant_inspection_failure`
  keeps the same rule inode, then expects the next firing to disarm with no
  second cleanup attempt; and
- `tests/systemd_integration/test_route3_backstop_host.py::test_bs3_disarms_after_a_hard_stop_that_left_nothing_a1_intact`
  expects the timer to be disarmed while a retained rule file still exists.

This behavior is fail-closed for deletion but fail-open for privilege
exposure. The grant can remain usable until a later CP, boot or manual
attestation, with no automatic recovery owner.

### Required safety property

**A possibly live Route 3 grant must never cause BS-2, BS-3 or the retry-bound
terminal path to disarm its last automatic recovery owner.** A firing may
report a hard stop, but it must not report successful recovery or stop the only
automatic retry mechanism until rule absence/removal and non-authorization are
established by the accepted checks.

### Required correction

- Represent inspection uncertainty separately from positively established
  damage or foreign identity. Do not infer either from a failed read, `fstat`,
  xattr listing, directory listing or fallback observation when the facts do
  not establish it.
- Carry that distinction through `Removal`, GRR, CL-3, the deactivation-record
  schema, residual reporting and the BS-3 predicate. Use a concise closed class
  name and exact schema; do not encode it in free-form diagnostic text.
- A hard-stop record containing that class must not permit BS-3 disarm.
- Review the retry-bound path as well as BS-3. Exhausting
  `backstop_max` or attempt 99 must not strand a possibly live grant merely
  because the bounded counter was reached. Preserve bounded resource use, but
  retain or transfer an effective automatic recovery owner. A repeated,
  rate-limited firing that creates no unbounded attempt/evidence directories is
  an admissible reversible choice; silently disarming is not.
- Preserve the conservative removal boundary: an unreadable or incompletely
  observed object is never `A1_INTACT` and is never unlinked.
- Preserve the existing treatment of a *positively established* damaged or
  foreign replacement unless changing it is necessary to satisfy the safety
  property. Do not let a foreign root-created file manufacture authority over
  its removal.
- Do not solve this by treating an authorization error as
  `not-authorized`, by deleting an unattributed object, or by broad exception
  swallowing.

If the safest small implementation makes all present/unremoved active-rule
classes block disarm, that is acceptable. Prefer a distinct uncertainty class
when the adapter has enough facts to preserve the established
damaged/foreign distinction.

## Finding 2 — blocking: incomplete records can authorize BS-2 disarm

`application/rp11/records.py::validate_record()` promises a closed schema but
checks only the top-level key set and fragments of a few nested objects.
`application/rp11/backstop.py::branch_for_record()` trusts that validation and
selects BS-2 for an accepted `st1-verified` record.

The review constructed a canonical record with all required top-level names
but with `authority`, `pk` and `grant_identity` equal to `"absent"`, incomplete
`active_rule` and `pass_config` objects, and no supporting facts.
`validate_record()` accepted it and `branch_for_record()` returned `bs-2`.
Other malformed nested shapes can instead leak `KeyError`, `TypeError` or
`AttributeError`, bypassing the documented BS-4 fallback.

### Required correction

- Make `validate_record()` a total validator for the complete
  `rp11-activation-record/2` schema. Validate every nested object and list,
  exact nested key sets, exact scalar types, bounds, enumerations, digest/path
  forms, and the cross-field relationships on which ACT, ST1, BS-2 and BS-3
  rely.
- Reject subclasses and boolean-as-integer values wherever the existing
  boundary requires exact types.
- The function must either return normally for a fully valid record or raise
  `RecordSchemaError`. No malformed admitted value may leak `KeyError`,
  `TypeError`, `AttributeError`, `IndexError`, assertion failure or another
  shape exception.
- Keep `branch_for_record()` defensively fail-closed. Canonical but malformed,
  mismatched or unsupported records must select BS-4 and must never escape or
  fall back to an older successful record.
- Do not loosen the schema to make old malformed test fixtures valid. Update
  fixtures to emit the exact accepted record shape.
- Keep record size, ownership, no-follow, hard-link, mode and canonical-byte
  protections intact.

Prefer small schema helpers with one responsibility over one large sequence of
unchecked dictionary indexing. Do not introduce a general schema framework or
new dependency for this closed internal format.

## Finding 3 — important: an arbitrary existing ACT record is trusted

`application/rp11/cleanup.py::_ensure_act_record()` hashes any existing bytes
without parsing or validating them and without checking `kind`,
`activation_id` or `attempt`. The current
`test_an_existing_act_record_is_never_rewritten` deliberately places
`{"kept":true}\n`, links its digest from a new deactivation record and expects
`st1-verified`.

Immutability is correct; trusting arbitrary bytes is not. It creates a valid
deactivation record whose durable ACT evidence is malformed or belongs to a
different activation.

### Required correction

- Never replace, rewrite or delete an existing ACT record.
- Before using its digest, read it through the existing guarded record-store
  boundary, parse it canonically, apply the complete record validator, and
  require `kind == "act"`, this activation ID, and attempt `0`.
- Also require any ACT-specific cross-field invariants needed for a valid
  `activated` or `failed` record. Do not accept a deactivation record renamed
  as ACT evidence.
- If the existing object is unreadable, non-canonical, malformed, mismatched or
  otherwise invalid, CL-7 must fail closed as `record-unpublished`; it must not
  publish an `st1-verified` record chained to those bytes.
- Preserve the existing behavior when no ACT record exists: publish the one
  immutable `failed` ACT record through the accepted atomic path.

## Required regression tests

Add tests that fail on the current accepted commit before applying the fixes.
At minimum prove all of the following.

### Grant recovery and disarm

1. Each deterministic GRR inspection-failure family produces the new
   uncertainty class, keeps the same object/inode and never removes it.
2. Stop-post and backstop CL record that class as a hard stop and residual,
   without claiming ST1.
3. The next backstop firing does not select BS-3 and does not call DI-4 while
   the uncertainty remains.
4. When the injected failure clears, a later automatic firing re-inspects,
   removes the attributable grant, verifies non-authorization and eventually
   disarms through the normal verified path.
5. Persistent uncertainty through `backstop_max` and attempt 99 does not
   disarm or lose the automatic recovery owner, does not create unbounded
   attempt directories, and produces a bounded, useful diagnostic.
6. A positively established damaged or foreign replacement retains the chosen
   safe behavior and is never removed merely to make the timer stop.
7. Existing `removed-unconfirmed`, `grant-unremovable`, active-holder,
   confirmed-clean BS-2 and safe BS-3 cases retain their accepted behavior.

Exercise the final policy under real PID 1, including the fact that timer state
and the rule's actual path state agree with the reported result.

### Record validation

8. Retain the review's minimal canonical `st1-verified` reproduction and prove
   it now selects BS-4 rather than BS-2.
9. Starting from valid generated ACT, verified-deactivation and hard-stop
   records, systematically delete every nested required field, add an extra
   field, replace every object/list with each wrong scalar/container type, and
   exercise important boundary values. Every mutation must raise only
   `RecordSchemaError` when calling the validator directly and must select
   BS-4 without raising when read by the backstop.
10. Cover nested malformed shapes in `active_rule`, `pass_config`,
    `directories`, `grant_identity`, `pk`, `st1`, `children`, `journals`,
    `failure`, `residual`, `authority`, `capture`, `helper`, `params`, `lock`,
    `release`, `unit`, `lease`, `boot`, `time` and every other accepted nested
    field. Use table-driven helpers rather than hundreds of copied tests.
11. Prove a valid `st1-verified` record still selects BS-2 and a valid eligible
    hard-stop record still selects BS-3.
12. Prove the greatest malformed attempt never lets an older verified record
    decide.

### Existing ACT evidence

13. Existing canonical valid ACT records for this activation are preserved
    byte-for-byte and their digest is linked.
14. Non-canonical, truncated, schema-invalid, wrong-kind, wrong-activation and
    nonzero-attempt existing ACT records are never rewritten and cause
    `record-unpublished`, with no deactivation record falsely claiming ST1.
15. The current `{"kept":true}\n` case changes from `st1-verified` to the
    fail-closed result.
16. An absent ACT record still produces one valid immutable failed-ACT record
    and the cleanup result retains its existing semantics.

Mutation-test each correction: temporarily restore the unsafe BS-3/bound
decision, relax or bypass nested validation, and restore the unvalidated ACT
hash path. Show the new tests fail for each mutation, then revert every
mutation and confirm the submitted tree is restored.

## Required verification

Use only synthetic data. Synchronize the final tree with the exact
secret-excluding command in `docs/operations/disposable-test-server.md`. Run
the following serially on `oracle-test`:

1. the focused artifact-store, unit-control, Route 3 hold, cleanup, backstop,
   PK/SN, H-1 artifact and launch gate/source suites;
2. the complete root `tests/systemd_integration` suite with
   `FREEDOM_SYSTEMD_INTEGRATION=oracle-test`, the pinned Jeepney wheel and
   `/usr/sbin` available in `PATH`;
3. the complete bot suite;
4. the complete web suite with exported
   `TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'`, verifying the
   database-enabled skip count rather than accepting the fast all-skipped
   configuration;
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
and that `polkit.service` is active. Remove only disposable artifacts created
by this work.

## Acceptance criteria

- A possibly live activation grant never causes BS-2, BS-3 or the terminal
  bound to disarm its last automatic recovery owner.
- Transient inspection failure recovers automatically after the fault clears;
  persistent failure remains fail-closed without unbounded filesystem growth.
- No unreadable, partially observed, damaged, foreign or replaced object gains
  removal authority.
- Every activation record accepted by `validate_record()` satisfies the whole
  closed schema, and malformed input raises only `RecordSchemaError`.
- No malformed, incomplete or mismatched record can select BS-2 or BS-3, fall
  back to an older record, or escape from `branch_for_record()`.
- Cleanup never links an arbitrary existing ACT object into a new trusted
  deactivation record and never rewrites the collision.
- Valid ACT, cleanup, BS-2 and safe BS-3 behavior remains functional.
- Focused and real-PID-1 tests pass, and final-tree bot, web and Foundry suites
  introduce no regression relative to the accepted baseline.
- The implementation remains inactive; no production/staging state, real
  secret or player data is touched.

## Handback update

Update `docs/review/route-3-hold-role-implementation-handback.md` in place with
one concise **current security remediation** section that supersedes its
current acceptance recommendation. Do not create another handback.

Include only:

- the three findings and their dispositions;
- the selected uncertainty class and the exact retry/bound behavior;
- the complete record-validation boundary and existing-ACT collision behavior;
- principal files changed;
- named regression and mutation tests;
- exact final-tree commands and results, including skips and unchanged
  baseline failures/errors;
- real-host timer/rule outcomes and cleanup confirmation;
- remaining production risks, including the uninstalled/unproved `tmpfiles.d`
  ordering and retained PID/start-time subject risk; and
- one unambiguous recommendation: accept the inactive role series for
  continued development or remediate one specifically named blocker.

Do not update production or staging configuration. Do not claim production
activation readiness: the independent reviewer must re-review the remediation,
and the separate `tmpfiles.d` installation/reboot gate remains open.
