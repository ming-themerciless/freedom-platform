# RP-11 D1 expected-results precursor — handback for Codex re-review

**Date:** 2026-11-28 · **Implementer:** Claude · **State:** Codex findings
remediated; **remediation not run**; awaiting Codex re-run and re-review; not
wired.

## Delivered

* `tools/rp11_pass_a_expectations.py` (new): pure, fail-closed evaluation of the
  49-act default plan. Only `MATCH` and `RECORDED` permit continuation. It binds
  admitted record digest, stream digests, pass id, step, sequence and argv before
  judging; gates pins, identity facts, exit, absence and A1-Z equality.
* `tests/test_rp11_pass_a_expectations.py` (new): synthetic tests, including
  agreement of step order, accepted exits and final-survey pairs with
  `pass_a_plan`, and that nothing operational imports the module.
* `tests/web/test_p3_4_static_assets.py` (existing, changed in remediation): the
  scope-guard declaration below.
* Policy D1–D10 recorded in the
  [candidate §14](rp11-single-host-pass-a-amendment-candidate.md#14-owner-policy-decisions--2026-11-28)
  and the handover.

No existing production source, manifest, plan or pin changed.

## Initial run and remediation

**The first submission failed a guard.** It was handed over without any test
run. Codex's targeted run then reported **294 passed, 1 failed**:
`test_no_unrelated_production_files_modified` rejected
`tools/rp11_pass_a_expectations.py` as an undeclared change. The earlier handback
named only the `test_rp11_capture.py` sentinels as likely to see the new file and
missed this guard. These figures are Codex's report; Claude did not observe the
run.

| # | Finding | Remediation |
|---|---|---|
| 1 | Scope guard rejects the new module | New list `PERMITTED_RP11_REVIEW_PRECURSOR` holding that one path, following the existing one-list-per-authorization pattern. Added to `scope_violation` and `PRODUCTION_ALLOWLISTS`, with a narrowness test. No prefix and no general exemption |
| 2 | Frozen `Expectations` kept caller-owned mappings | `source_sha256` and `dry_run` are copied, then validated, and held as read-only `MappingProxyType`. A non-mapping is refused. Test mutates the originals |
| 3 | `ENOENT` form accepted any line containing the phrase, and any later pathname | The form must fully match `stat` or `/usr/bin/stat`, `: cannot stat` or `statx`, one quoted path, `: No such file or directory`, one newline. The quoted path must equal the planned operand. Negative controls cover suffix, permission, compound and neighbouring-path cases |
| 4 | Blank output counted as a recorded observation | The six non-empty observations stop with `blank-output` when every line is blank. A1-27 and A1-28 are unchanged |
| 5 | Admission and plan provenance unclear | Documented in the module: the admitted digest must come from a trusted admission by the current invocation, and the planned argv from the reviewed, pinned plan |

The grammar in finding 3 is **synthetic**. It is not an observation of the
target's `stat`. If the reviewed real shape differs, the grammar needs a reviewed
change; until a form is supplied, `None` still refuses.

## Checks

**Claude executed no test, before or after remediation.** Each pytest invocation
was refused by the session's permission mode (no approval surface). The
remediation was checked only by reading it. **The re-run is Codex's to observe**;
no pass figure is claimed.

Suggested targeted run (no host, no database):

```text
env -u TEST_DATABASE_URL PYTHONDONTWRITEBYTECODE=1 \
  /opt/freedom-blades/platform/venv-web/bin/python -m pytest -q -rs -p no:cacheprovider \
  tests/test_rp11_pass_a_expectations.py tests/web/test_p3_4_static_assets.py \
  tests/test_rp11_pass_a_plan.py tests/test_rp11_pass_a.py
```

This may not be the selection behind the 294 + 1 figure. The last two modules
start local child processes in some tests, and so do some static-asset tests
(`git`).

## Limitations

See [candidate §14.1](rp11-single-host-pass-a-amendment-candidate.md#141-d-1-precursor-review-only-not-wired).
In short: no reviewed `ENOENT` form (A1-19 stops without one); gate formats are
unconfirmed against target records; eight observations are recorded without a
value gate; no streams reach the orchestrator yet; B-7 and M-2 stay open.

* `CaptureRecord` carries no per-record `InvocationID`. The evaluator cannot tell
  records of two invocations apart; integration must bind the current chain.
* The evaluator checks planned step ids and order, not that the argv are the
  reviewed plan's.

Points for review: A1-20 requires `ubuntu` among the members but allows others;
A1-30 compares only the first four columns on first reading (the final reading
must equal it byte for byte); stderr must be empty on every act except the two
run-root readings; A0-05 pins the seven named dry-run fields, not the whole
output.

## Effects and next action

No deployment, migration or recovery effect. Nothing contacted a host, staging or
production; no `run_pass_a`, SA-2 build or grant; nothing was committed or
pushed. `docs/project-management/status.md` and the change log were not updated.
## Codex independent re-review — 2026-11-28

The D-1 precursor passed review after Claude fixed the undeclared source
path, snapshotted the expectation maps, tightened the synthetic absence
grammar to an exact diagnostic for the planned path, and rejected blank
output for observations that must produce text. The scope declaration admits
one exact review module. The initial failure remains recorded above.

Codex ran the evaluator, static asset and scope, no-execution, and RP-11
capture modules with the documented interpreter and `TEST_DATABASE_URL`
unset. **979 passed, 0 skipped, 0 failed in 10.12 s**. No operational act
was exercised. The current-invocation admission, real diagnostic pin,
in-pass wiring, D-2 authority labels and regenerated review pins remain
integration work.
