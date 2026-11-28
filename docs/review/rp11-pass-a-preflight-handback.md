# RP-11 Pass A config/authority binding precursor — handback for Codex review

**Date:** 2026-11-28 · **Implementer:** Claude · **State:** implemented, **not
run**, awaiting Codex tests and review. Inert and unwired. Nothing here is an
approval, a grant or a start authorization.

## Not run

**Claude executed no Python.** The session's permission mode refused the pytest
run (no approval surface), and it was not retried another way. Everything below
was checked by reading. No pass figure is claimed.

## Codex R1 — fixed, fix **not run**

Codex ran an initial four-module set: **612 passed**, before this fix. That figure
does not cover the changed bytes.

**Defect (reproduced by Codex):** a `PassAPlan` subclass with identical steps and
acts but a `whole_pass_bound_seconds` returning 0 had the same plan identity and
bound at the last admissible instant plus one second. The duration was not in the
identity, and the window check looked it up on the mutable plan separately.

**Fix:**

* `snapshot_plan` replaces `plan_identity`. It reads the plan once into immutable
  values; the identity (now `rp11-plan-identity/2`) includes
  `whole_pass_bound_ms`, and the window check uses that same integer.
* A duration must be a positive, finite, whole number of milliseconds and at
  least the sum of every act's timeout and drain.
* `BoundRecords.acts` returns the full act policy (argv, environment, class, AUTH
  row, stream bound, timeout, drain, accepted exits), with
  `whole_pass_bound_ms`. **Later wiring must use these and must not reuse the
  caller's plan object or its `acts`, `exit_policy` or duration.** Nothing
  enforces that yet.
* The module does not import the plan, so it does not require the exact
  `PassAPlan` type; it relies on the single snapshot and the pinned identity.
* New controls: invalid durations, changed duration, late acceptance, single
  read, and the returned policy.

**A-6:** the substring check is consistency only. The record's subject and
accepting disposition are authenticated by external review metadata that the
trust-root builder vouches for.

**Machine helper digest:** `helper.tool_sha256` is the machine A-2's existing,
distinct artifact field. It is not `capture_tool_sha256` (the capture-tool source
digest), and the two are not compared.

The A-3 (revocation and supersession) and consume-role limitations below are
unchanged.

## Delivered

* `tools/rp11_pass_a_preflight.py` (new): `bind_records(records, trust, plan,
  now=…)`, pure over supplied bytes. It returns evaluator `Expectations`, the
  judged plan and the binding digests, or raises `PreflightRefused(reason, record)`.
* `tests/test_rp11_pass_a_preflight.py` (new): synthetic records only. Parser
  bounds, duplicates and non-canonical bytes; closed keys and blocks; wrong
  values with every later digest and pin recomputed; missing records; stage order
  and window edges; truncated and altered plans; mixed activations; containment.

No covered source, manifest, concrete plan, SA-2 input or pin changed (`git
status` shows only the two new files and three test files). `rp11-a2/3` and the
consume role are unchanged. `run_pass_a` is neither imported nor called.

## Guard changes — please review these specifically

| File | Change |
|---|---|
| `tests/web/test_p3_4_static_assets.py` | new one-path list `PERMITTED_RP11_PREFLIGHT_PRECURSOR` and its narrowness test |
| `tests/test_rp11_cleanup.py` | `_ROLE_REFERENCE_EXCEPTIONS` gains the new file with exactly two import statements (`A2Pins`, `AuthorityError`; the canonical functions) |
| `tests/test_rp11_pass_a_expectations.py` | the "nothing imports the evaluator" scan now also skips this one precursor, which has its own nothing-imports-it test |

The last two **widen existing guards**. They follow the `start_binding` precedent
and are needed to reuse the one authority parser and the one evaluator instead of
copying them. If Codex rejects either, the module needs another home. The guard
that nothing imports `pass_a_plan` is unchanged: the plan is an argument, and
three plan constants are held equal by a test.

## Design (reversible choices)

* **Trust root.** `TrustRoot` has no defaults: the two names, the operator who
  will start, activation, commit, capture-tool and tree digests, the A-6
  classifier digest and one digest per input. Digests show identical bytes, not
  authorship. Whoever builds the trust root vouches for authorship through an
  independent channel. **Nothing in the repository builds one.**
* **No digest cycle.** `pass-a.json` embeds no record digest. Order:
  config → machine A-2 (quotes it) and A-1 → acquisition authorization → result →
  written A-2 → A-5 → execution authorization.
* **Written records** are UTF-8 documents with exactly one canonical-JSON fenced
  block (`rp11-…`). The pin covers the whole document, so the structured fields
  are the signed text. Prose is not interpreted.
* **Machine A-2 binding (D-5).** The **execution authorization** names both the
  written A-2 and machine A-2 digests. The written A-2 does not name the machine
  file, so it can precede staging (`boot_id`, staged-rule inode). **Please
  confirm this reading of D-5.** If the written grant itself must name the
  machine file, add that field; it still creates no cycle.
* **Plan identity** is a digest of every act's step id, argv, environment, class,
  bound, timeout, drain, accepted exits and AUTH row, plus the whole-pass
  duration, pass id, root and checkout. Only the exact 49-act default sequence is accepted.
* **Expectations digest** covers every value the evaluator compares and is
  independent of activation, operator and window, so A-1 can accept it first.
* **AUTH-READ** must be granted for exactly A0 and A1. AUTH-SYNC and AUTH-DBREAD
  have no field (D-2). Acquisition has its own grant and result and grants no
  execution.
* **Stricter than the draft:** the window must contain `now` **and** `now` plus
  the whole-pass bound (2548 s). The reviewer may be neither owner nor operator;
  the operator may not be `capture`. A config without an `ENOENT` form, or with
  one naming another path, is refused, because the pass would stop at A1-19 and
  use up `capture-a`.
* **Differs from the entry-contract proposal §2:** no authorization flags or
  record digests in the config (circular, and D-2 retired two rows), and no
  per-command timeouts there (bound by plan identity).

## Review of A-1 / A-5 / execution prerequisites (code reading only)

A successful bind does **not** satisfy these:

1. **Authenticity.** No trust-root source, signature or protected store exists
   for the written records.
2. **A-3, revocation and supersession.** Not checked.
3. **A-4** is the evaluator's in-pass job; the continuation is still unwired.
4. **A-5** is checked as a pinned statement by the named owner. Its truth, and
   quietness of the host, are not checked.
5. **A-6** is checked only as: pinned record bytes contain the classifier digest,
   and the config pins the same digest. The record's subject and disposition are
   not read from it (see R1).
6. **Artifact measurement (B-5).** Tool and tree digests are compared between
   records and the trust root, never with installed bytes. Manifest, plan,
   contract and reviewed digests are not recomputed from a tree. D-6 "record-only
   successor" is not verified.
7. **Consume prerequisites** (ACT journal, activated record, H-1, H-2, hold,
   lease, one-shot claim) remain the consume role's. The window is not compared
   with the lease. This check is repeatable: it is no replay protection.
8. **Pre-start host state** (§4.3: identity, parent, absent root) is not checked.
9. **Wiring.** The binding covers plan data, not the callables. A later entry
   must take acts, exit policy, duration, expectations, genesis tool digest and
   evaluator plan from this one result (never the caller's plan), supply a trusted clock, and decide what
   happens if the window closes mid-pass. B-3 and B-4 stay open: this fixes a
   candidate config format and the grant coverage, with no loader or per-act
   enforcement.
10. **Existing blockers** stay: M-1 (`prompt_sha256` is whatever A0-03 hashes,
    still the old draft), no evidenced `ENOENT` form (the grammar is synthetic),
    B-1, B-2, B-6, B-8 … B-12, and D-3, D-9, D-10 record formats.

## Commands for Codex

No host or database; none calls `run_pass_a`:

```text
cd /opt/freedom-blades/platform && env -u TEST_DATABASE_URL PYTHONDONTWRITEBYTECODE=1 \
  /opt/freedom-blades/platform/venv-web/bin/python -m pytest -q -rs -p no:cacheprovider \
  tests/test_rp11_pass_a_preflight.py tests/test_rp11_pass_a_expectations.py \
  tests/test_rp11_pass_a_continuation.py tests/test_rp11_cleanup.py \
  tests/test_rejected_scope_absent.py tests/web/test_p3_4_static_assets.py \
  tests/test_systemd_unit_control.py tests/test_rp11_entry.py tests/test_rp11_h1_artifact.py \
  tests/phase_5_0_evidence/test_no_execution.py tests/phase_5_0_evidence/test_rp11_capture.py
env -u TEST_DATABASE_URL PYTHONDONTWRITEBYTECODE=1 \
  /opt/freedom-blades/platform/venv-web/bin/python -m pytest -q -rs -p no:cacheprovider \
  tests/test_rp11_pass_a_plan.py -k "not (completes_with_one_finalization or failure_at_any_step or unexpected_status or outlives_its_class)"
```

Some selected modules start local child processes in pytest temporary
directories (for example `git`). The `-k` filter is the one used in the D-1 seam
handback to leave out the tests that call `run_pass_a`.

## Effects and next action

No deployment, migration or recovery effect. No build, install, host or network
access, acquisition, activation, service, staging, production, secret, commit or
push. `status.md` and the change log were not updated.

## Independent Codex disposition — 2026-11-28

Reviewed against the clean v40 baseline `bf3875d55a29185fd5812fc88a4e12162657ccaa`.
The initial test selection passed 612 checks but independent review reproduced
a late-window acceptance with a restated duration. Claude made the duration
part of plan identity v2 and used the same immutable snapshot for the
fingerprint, window check and returned act policy. Regression tests cover
changed and invalid durations, the exact time edge and a second-read trap.

The final local, database-free selection passed **1,710 tests** with zero
failures or skips. It covered preflight, evaluator, continuation, cleanup,
static scope, no-execution, capture, retention and R5 pins. The three scope
guard adjustments name exact modules or imports. Nothing operational
imports the companion. Manifest v40 and its covered sources remain unchanged.

The companion can verify agreement among test records. A future integration
must authenticate the external trust root, enforce A-3 and existing consume
checks, read the protected configuration, and use only the bound plan
snapshot. The target diagnostic and artifact pins still need their own
reviewed evidence. No operational caller, grant or start was created.
