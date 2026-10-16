# Claude implementation prompt — Route 3 static `stop` role

Date: 2026-10-15
Authority: Peter Duscha, baseline v1.9 and the active implementation-first
delivery plan
Reviewer after handback: Codex

## Assignment

Implement SA-2, the second real non-production Package 5.0 consumer of the
accepted Route 3 boundary, as this exact controlled-artifact vector:

```text
/usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py stop
```

The role accepts no operand, option or alternate spelling. It makes exactly one
call to the existing DI-S `stop_capture_unit()` boundary and returns that call's
typed result. Keep the implementation inactive outside `oracle-test`. Do not
implement a Package 5.0 coordinator, the executor's OC-1/OC-2/OC-3 checks,
`consume`, `attest`, migration work, production activation or unrelated cleanup.
Do not commit or push.

## Current working-tree boundary

The working tree contains the accepted but uncommitted SA-1 `start` slice and
the documentation recording Peter's 2026-10-15 acceptance. Those changes are
the base for this work. Preserve them exactly except for the smallest shared
artifact/parser edits required to add `stop`; do not reset, revert, overwrite or
recharacterize them. The last accepted Git commit remains `a447558`, but it
predates accepted SA-1 and therefore is not the complete implementation base.

Inspect `git status` and the complete diff before editing. Preserve all
unrelated maintainer changes. The prompt itself is reviewer-owned and must be
preserved.

## Required reading

Before planning or editing, read completely:

1. `.agents/AGENTS.md`;
2. the implementation-plan reading map, §§0, 12 Phase 5.0, 13, 14, 16 and 20;
3. `docs/review/Handover information`;
4. `docs/project-management/active-delivery-plan.md`;
5. `docs/operations/disposable-test-server.md`;
6. `docs/review/route-3-manager-polkit-implementation-handback.md`;
7. `docs/review/route-3-start-role-implementation-handback.md` and the current
   SA-1 code/tests;
8. the completed stop-post, backstop and hold handbacks;
9. operation inventory §§4.1, 5.7, 6 SA-2, 7, 8.1 and applicable §12 rows; and
10. interface contract §§3.0 and 3.7, including D-3, D-4, D-9, IO-1 and IO-2.

Historical WP closure labels are not current development gates under baseline
v1.9. Their accepted SA-2 and DI-S requirements remain implementation inputs.

## Boundary ownership

The executor calls SA-2 only after it has established all three preconditions:

- OC-1: `rp11-capture-pass-a.service` is active;
- OC-2: its `InvocationID` matches the consume journal's `run-start`; and
- OC-3: the journal contains `consumed`.

Those checks are outside this role. Do not read unit state, the consume journal,
the capture root, an activation record or any other state before calling DI-S.
Do not attempt to detect `start-pre`; a stop during `start-pre` is outside the
authorized route and the executor owns that exclusion. SA-2 neither finalizes
X-3 nor decides whether the larger pass should continue.

## Required behavior

- Add only the exact `stop` vector above. Reject every operand, option, alias,
  extra token and alternate spelling before opening the bus or performing any
  state operation.
- `stop` is a `sudo`-started first image under EX-1 and reads **no environment
  variable**. No inherited value, including malformed, duplicate, oversized or
  well-formed `INVOCATION_ID`, may select, reject or change a valid `stop`.
  Continue to empty the environment and retain all accepted first-image checks:
  descriptors 0–2 open, every descriptor at or above 3 closed and verified,
  resettable signal dispositions and signal mask reset, umask `022`, cwd `/`,
  and the existing artifact-integrity checks. Preserve provenance handling for
  the PID-1 roles that consume `INVOCATION_ID`.
- Invoke `UnitControl.stop_capture_unit()` exactly once. The caller supplies no
  unit name, job mode, bus, executable, property or arbitrary argument. Rely on
  the accepted manager adapter to issue only
  `StopUnit(rp11-capture-pass-a.service, "fail")` on the system bus.
- Never start, restart, reset, reload, kill or signal a unit. Create no child,
  send no signal, write no record and perform no additional read or wait beyond
  the completion observation already encapsulated by DI-S.
- Preserve the accepted three-way result. A completed `done` stop is
  `ok(stopped)` whether the loaded unit had been active, inactive or failed;
  never claim causation or introduce an `already-stopped` result.
  `NoSuchUnit` is `refused(not-loaded)`; pre-mutation `InvalidArgs` is
  `refused(invalid-request)`; manager authorization denial is
  `refused(not-authorized)`.
- Every other manager/transport failure, non-`done` job result, lost or malformed
  reply, disconnect, deadline or unconfirmed completion is an error. Any error
  after the one mutating call was sent is `effect-not-confirmed`, permits no
  silent retry and must never be promoted by a later state observation.
- Treat apparent success as untrusted boundary data. Accept `ControlOk` only
  when it carries a `StopCompletion` with outcome `STOPPED` and a structurally
  valid `JobCompletion` for exactly `rp11-capture-pass-a.service`, including the
  accepted ASCII systemd job-object-path shape. `ControlOk(None)`, a different
  value type, another outcome/unit, or an empty/arbitrary/malformed job path is
  an unconfirmed error after exactly one call—not success and not an internal
  pre-send failure.
- Use fixed, value-safe diagnostics and stable exit statuses. Align with the
  accepted SA-1 role: success 0; typed refusal 20; proven pre-send error 21;
  effect not confirmed 22; unexpected internal exception/result 70. Output must
  reveal no exception text, D-Bus detail, object path, environment value or
  other caller-controlled value. A completed stop must be rendered simply as
  stopped, consistent with `ok(stopped)`.
- Include every new production module in the controlled artifact's exact source
  manifest. Preserve root ownership, no-symlink/non-writable artifact checks,
  the four accepted existing role vectors, and every SA-1 remediation.
- Do not alter the accepted manager/Polkit adapter merely to make an SA-2 fake
  result pass. Keep role-level result validation at the SA-2 application
  boundary unless a smaller equally isolated value-object correction is
  demonstrably safer.
- Do not weaken the manager/Polkit boundary, scope guard, `tmpfiles.d`
  prerequisite, production gates or existing tests.

## Focused test requirements

Write regressions before the corresponding implementation where practical.
Cover at least:

1. the exact zero-operand vector and rejection of extra/alternate tokens before
   a bus is opened;
2. no environment read for `stop`, including genuine duplicate raw `envp`,
   malformed and oversized `INVOCATION_ID`, while provenance-consuming roles
   remain unchanged;
3. one DI-S call and no retry for success, every typed refusal/error, exception,
   timeout, disconnect, lost reply, non-`done` completion and unknown result;
4. fixed safe diagnostics and the exit-status mapping above;
5. `ControlOk(None)`, a non-`StopCompletion`, wrong outcome, wrong unit, missing
   completion, and empty, short, non-ASCII-digit or otherwise malformed job
   paths, each proving one call, exit 22 and no value leakage;
6. a valid completion for the fixed capture unit, proving one call, stopped and
   exit 0;
7. no role-level DI-1 read, journal/record access, child, signal, retry or
   caller-selectable target; and
8. preservation of all accepted `start`, `hold`, `stop-post` and `backstop`
   vectors, manifests and artifact-integrity behavior.

Do not loosen an existing assertion or allowlist simply because the new files
are untracked. Add only the exact production/test paths justified by SA-2.

## Disposable-host proof

Use synthetic data and the documented secret-excluding synchronization command.
On `oracle-test`, build a fresh root-owned controlled artifact from the pinned
Jeepney wheel and exercise the exact vector through the accepted `sudo -n`
launch preamble as `ubuntu`, not only as an already-root test process.

At minimum prove:

1. an active disposable capture service receives exactly one `StopUnit` and the
   role returns stopped;
2. a loaded inactive or failed capture service returns stopped without claiming
   whether this request caused the state;
3. a not-loaded capture unit returns `refused(not-loaded)` with no stop job
   queued; do not claim that the manager created no transient stub while
   resolving the fixed name;
4. an unauthorized invocation returns `refused(not-authorized)` with the unit
   left running and no other mutation;
5. one post-send unconfirmed outcome returns exit 22, sends exactly once and is
   never retried or promoted by observation;
6. extra operands and hostile environment entries are refused or ignored at the
   correct boundary before any manager call;
7. the accepted SA-1 lifecycle and the complete Route 3 systemd integration
   suite remain green; and
8. teardown leaves no RP-11 unit, process, Polkit rule, artifact, staging/store
   path, `/var/tmp/rp11-act-*` path or SA-2 evidence/log, with
   `polkit.service` active and the pre-existing
   `/var/tmp/p5-r5-rp11-h0*` directories untouched.

## Required verification

On the final tree, run and record exact copy-pastable commands, working
directories, exit statuses, pass/fail/error/skip counts and every skip reason:

1. the new SA-2 unit/application tests, `tests/test_rp11_h1_artifact.py` and
   `tests/test_systemd_unit_control.py`;
2. the new SA-2 root/systemd host module with a fresh controlled artifact;
3. the complete `tests/systemd_integration` suite serially;
4. `tests/web/test_p3_4_static_assets.py`, reporting established unrelated
   baseline failures rather than hiding or repairing them;
5. the documented bot suite and web suite serially with
   `TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'`, checking that the
   web skip count remains the documented 80 rather than the false-green
   database-skipped count;
6. the Foundry Node suite;
7. Python compilation over every touched Python path; and
8. `git diff --check`.

Compare known failures against an actual recorded or freshly reproduced
baseline. Do not call a failure pre-existing from memory. Do not run the bot and
web suites in parallel because they share the disposable database.

After root tests, verify cleanup separately. Production and staging, real
secrets and real player data remain outside the authority.

## Documentation and handback

Create one concise
`docs/review/route-3-stop-role-implementation-handback.md`. Update only the
current-state documents needed to say that Claude implemented the uncommitted
SA-2 candidate and independent Codex review is pending. Do not record Peter's
acceptance or any production authorization that has not happened, and do not
create a prompt/review/remediation chain.

The handback must include:

- delivered behavior and exact files;
- SA-2/H-FI/DI-S requirement-to-test coverage;
- exact focused, real-host and comparison-suite commands/results;
- every failure, error and skip, with verified baseline disposition;
- host cleanup state;
- deployment/migration/recovery effects and unchanged production risks; and
- one recommendation: accept, remediate one specifically named blocker, or
  replace the approach.

Return the uncommitted candidate for independent Codex review. Production and
staging activation remain unauthorized. The transient inspection-failure
decision and final independent production security review remain mandatory
before any activation.
