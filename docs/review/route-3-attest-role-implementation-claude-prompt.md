# Claude implementation prompt — Route 3 `attest` role (RT-5)

Date: 2026-10-17
Authority: Peter Duscha, baseline v1.9 and the active implementation-first
delivery plan
Reviewer after handback: Codex

## Assignment

Implement RT-5 `attest`, the interactive root recovery role that runs the
accepted shared cleanup procedure only after proving that no holder or backstop
unit still owns the activation. Add exactly this controlled-artifact vector:

```text
/usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py deact <activation_id> <a2_sha256> attest
```

The operator invokes that installed vector through `sudo -n`; `sudo` is the
sole launch preamble outside the controlled first image. The role validates the
activation and A-2 operands, reads no environment variable, performs the three
RT5.PRE unit-state reads, and refuses without entering cleanup when any owner is
active or the precondition cannot be established. Otherwise it runs the
existing cleanup engine with trigger `attest`. In the same boot this is ordinary
CL; after a kernel boot it may record `cleared-by-boot` and `st1-verified` only
when the existing CL-4 negative-authorization and CL-6 ST-1 checks both hold.

Keep the implementation inactive outside `oracle-test`. Do not implement the
non-root executor, OC-1/OC-2/OC-3, a production capture-unit installer,
migration/cutover work, production or staging activation, or unrelated cleanup.
Do not commit or push.

## Current working-tree boundary

The accepted implementation base is commit `94fb3e7` (`feat: implement Route 3
consume role for rp11-h1 artifact and tests`). The working tree was clean when
this assignment was written except for this prompt and its current-state links.
Preserve all maintainer changes. Inspect `git status` and the complete diff
before editing; do not reset, revert or overwrite accepted work.

RT-1 `consume`, SA-1 `start`, SA-2 `stop`, the manager/Polkit adapter, the
repository-managed `tmpfiles.d` prerequisite and the RT-2/RT-3/RT-4 role series
are accepted. Do not reopen or weaken them to make RT-5 pass.

## Required reading

Before planning or editing, read completely:

1. `.agents/AGENTS.md`;
2. the implementation-plan reading map, §§0, 12 Phase 5.0, 13, 14, 16 and 20;
3. `docs/review/Handover information`;
4. `docs/project-management/active-delivery-plan.md`;
5. `docs/operations/disposable-test-server.md`;
6. the accepted manager/Polkit, stop-post, backstop, hold, `start`, `stop` and
   `consume` handbacks and the current implementations they name;
7. the operation inventory §§3 RT-5, 4, 5.5, 6 RT-5, 7, 8.1 and 10, plus the
   RT-5 rows and reconciliation tables in §§11–12;
8. the interface contract §§3.0, 3.1, 3.5 and 3.6, including D-1 through D-6
   and the retained PID/start-time/uid subject risk; and
9. the controlled-artifact entry point and manifest, shared cleanup engine,
   stop-post composition root, manager ports, authority/journal/evidence models,
   record grammar, filesystem adapters and real-host Route 3 tests.

Historical WP closure labels are not current development gates under baseline
v1.9. Their accepted RT-5, H-FI, H-CL, H-GRR, H-PK2, H-SN and DI-1/DI-5/DI-6
requirements remain implementation inputs. Choose the smallest reversible
mechanism consistent with those contracts, record it briefly in code/tests or
the handback, and prove it. Stop and ask Peter only if a choice changes a safety
boundary, authorization policy, product scope or irreversible architecture.

## Boundary ownership

RT-5 begins at the first design-controlled static image executed by `sudo -n`.
It is not a systemd unit and has no PID-1 timeout or automatic recovery owner.
It receives exactly the validated activation identifier, A-2 SHA-256 and fixed
`attest` trigger. It reads no environment variable, including
`INVOCATION_ID`, and records no caller PID or invocation provenance.

The future non-root executor decides when to request attestation and reports its
record. RT-5 does not implement that executor, initiate or stop a pass, evaluate
OC-1/OC-2/OC-3, choose an activation, search for candidates, or act on a
left-behind child. It starts, stops, restarts, signals and kills no unit or
process. A boot is a separate recovery event, not an action taken by RT-5.

## Required behavior

### Controlled first image and exact vector

- Accept only `deact <activation_id> <a2_sha256> attest`, with the existing
  strict activation-ID and lowercase SHA-256 validators. Refuse aliases,
  omitted/extra operands, options and case/whitespace variants before any state
  operation. The installed and tested runtime remains the exact Python 3.14
  vector above.
- Run the accepted H-FI controls: descriptors 0–2 open; every descriptor at or
  above 3 closed and verified; resettable signal dispositions and the signal
  mask reset; umask `022`; cwd `/`; environment emptied. The role must not read
  `INVOCATION_ID` or any other environment value before clearing it.
- Preserve every accepted role vector and its environment rule. In particular,
  `stop-post`, `hold`, `backstop` and `consume` still process their permitted
  provenance; `start`, `stop` and `attest` read none.
- Import every production dependency up front and include every new production
  module exactly once in the controlled artifact's source manifest. Preserve
  the root-owned tree and exact-runtime integrity checks.

### RT5.PRE — no live owner

- Before CL-G, use the accepted DI-1 adapter to read `ActiveState` for exactly:
  the holder `<activation_id>.service`, the backstop timer
  `<activation_id>-backstop.timer`, and the backstop service
  `<activation_id>-backstop.service`. Derive all names from the validated ID;
  accept no unit name from the caller.
- If any read reports `activating`, `active`, `deactivating` or `reloading`,
  refuse attestation with a stable non-zero result. Create no attempt directory,
  journal or record; remove nothing; make no Polkit call; do not read cleanup
  evidence or authority files.
- Typed `not-found`, `inactive` and `failed` do not block. A timeout,
  disconnect, malformed/partial reply, unknown error, unexpected refusal or any
  other inability to establish a permitted result fails closed before CL. A
  satisfied read is never evidence about another unit. Do not silently coerce
  any other supported `ActiveState`; pin its fail-closed treatment in tests and
  document the reversible choice.
- Complete the precondition without a start/stop/restart/reset request. Do not
  treat sequential reads as an atomic manager snapshot or claim a race-free
  observation that DI-1 cannot provide.

### Shared cleanup with trigger `attest`

- Extend the closed trigger grammar with `attest` and reuse
  `CleanupProcedure`; do not copy CL, GRR, attribution, PK/2, record publication
  or filesystem removal logic into an RT-5-specific implementation.
- Once RT5.PRE passes, CL-G is the first cleanup act. Then preserve the accepted
  CL-0 through CL-7, GP-R3 and outcome ordering. The attempt number shares the
  existing deactivation-attempt sequence; `attest` remains a non-backstop
  trigger for the backstop firing bound.
- `attest` attempt journals and deactivation records use the closed trigger
  value `attest`. They carry no parent PID or `INVOCATION_ID` provenance. Pass
  only manager-observed state into fields already owned by the cleanup contract.
  The current attempt-journal grammar requires a provenance object for the two
  implemented triggers; refine that closed grammar for `attest` rather than
  writing dummy `0`/`absent` provenance. Preserve the exact existing
  `stop-post` and `backstop` shapes and make old or hybrid attest shapes invalid.
- In the same boot, use the ordinary CL attribution classes and remove only an
  A1-intact object after descriptor re-verification and the accepted write-ahead
  evidence. Damaged, foreign, uninspected, unprovable and unremovable objects
  are kept and cannot become success.
- In a later boot, retain CL-1 boot scoping: every object found under `/run`
  from the old activation is A0. Classify an absent old-boot object as
  `cleared-by-boot` only when all existing requirements hold: different boot
  IDs, `/run` observed as tmpfs, a valid old identity line and `ENOENT`. RT-5
  removes nothing merely because the boot changed.
- CL-4 must run the existing PK/2 `SEEK_NOT_AUTHORIZED` series for verb `start`.
  Only a positive `not-authorized` result permits `removed-verified` or
  `cleared-by-boot` to contribute to `st1-verified`. `authorized`,
  `unconfirmed`, timeout, malformed reply, transport error, subject error or
  abandonment is never success and is never silently retried.
- CL-6 must independently prove ST-1 and the pinned baseline. Publish
  `st1-verified` only when the complete existing outcome rule holds. Otherwise
  publish the existing hard-stop/residual result or the narrower existing
  terminal failure. Never infer success from pathname absence, a missing
  record, a reboot or an interrupted earlier attempt.
- Preserve grant-priority behavior for evidence creation/write/flush failures:
  remove only a safely attributable live grant, hold unverifiable results in
  memory, claim no durable evidence that was not flushed, and always return
  non-zero.

### Interruption, result and diagnostics

- Install no signal handler. There is no whole-life timeout enforcer for this
  interactive role. Default-action interruption may leave a missing terminal
  record/line; every later RP-11 gate remains fail closed until a later explicit
  recovery succeeds.
- RT-5 has no automatic owner for a left-behind authorization subject. Record
  the accepted child terminal information when available; otherwise expose the
  existing `children-unknown`/missing-terminal evidence and do nothing to the
  child.
- Choose and test a stable explicit exit map. Exit 0 belongs only to a complete
  `st1-verified` cleanup. A blocked/unestablished precondition, hard stop,
  concurrent attempt, unwritable evidence, unpublished record and unexpected
  exception are all non-zero and distinguishable by closed tokens.
- Emit one bounded, value-safe diagnostic line. Never render exception text,
  arbitrary paths, D-Bus detail, environment content, file content or a
  traceback. Unexpected exceptions fail closed with a fixed internal result.

Use a small application procedure for RT5.PRE and orchestration if needed, with
ports owned by that procedure and the production composition root in
`adapters/rp11/`. Reuse `StopPostServices`, the manager adapter and
`build_procedure` where their contracts match. Do not make the shared cleanup
engine aware of CLI parsing or `sudo`.

## Focused test requirements

Write regressions before implementation where practical. Map every RT-5 row to
an executable test or named host check. Cover at least:

1. exact vector parsing and refusal of every missing/extra operand, option,
   alias, spelling/case/whitespace variant before state access;
2. hostile, duplicated, malformed and oversized environment values proving
   `attest` reads none and clears all environment, while every accepted role's
   prior environment behavior remains unchanged;
3. the full three-unit precondition matrix: each unit independently in every
   blocking state, typed `not-found`/`inactive`/`failed`, other supported states,
   malformed values, timeout, disconnect and read error;
4. proof that a blocked or unestablished precondition performs exactly the
   bounded precondition reads needed to decide (and no unrelated read), enters
   no CL step, creates nothing, reads no evidence/authority, calls no Polkit
   operation and mutates nothing;
5. all three names derived from the validated activation and no caller-selected
   path/unit, including metacharacter and cross-activation attempts;
6. same-boot cleanup success, hard stop, concurrent attempt, damaged/foreign/
   uninspected objects, unremovable grant, manager error and GP-R3 evidence
   failures through the reused engine with trigger `attest`;
7. later-boot `cleared-by-boot` for the rule, pass config and eligible
   directories, plus wrong/same boot, non-tmpfs, missing identity, present old
   pathname and baseline mismatch cases that must not become success;
8. CL-4 authorized, not-authorized, challenge, only-errors, still-authorized,
   timeout, malformed reply, transport error, replaced subject and interruption,
   with at most one PK/2 series and every subject settled or explicitly unknown;
9. exact attempt numbering across mixed `stop-post`, `backstop` and `attest`
   attempts, with `attest` excluded from the backstop firing count and no record
   overwrite;
10. default-signal interruption at representative PRE/CL/journal/removal/PK/
    publication points, proving no false terminal record and explicit later
    recovery where safe;
11. stable exits and bounded diagnostics, including unexpected exceptions and
    absence of exception/path/environment leakage; and
12. preservation of accepted cleanup, backstop, hold, start, stop and consume
    behavior, journal/record grammars, manifest, source allowlists and artifact
    integrity.

Use fault injection and mutation checks for precondition-before-mutation,
old-boot attribution, negative authorization and terminal publication. Do not
weaken an assertion or widen an allowlist beyond the exact new files.

## Disposable-host proof

Use synthetic data and the documented secret-excluding synchronization command.
On `oracle-test`, build a fresh root-owned controlled artifact from the pinned
Jeepney wheel and invoke RT-5 as the real operator with the exact `sudo -n`
vector, not merely as an already-root Python subprocess.

At minimum prove:

1. each live/transitional holder, timer and service state refuses before any
   cleanup effect, while unrelated active units do not affect the decision;
2. a same-boot activation with no live owner runs the accepted cleanup engine,
   removes only attributable objects, obtains real Polkit non-authorization and
   publishes the correct terminal evidence;
3. a same-boot damaged/foreign/uninspectable/unremovable object is retained and
   reported without false success;
4. a real kernel reboot clears the disposable activation's `/run` objects;
   afterward the exact `sudo -n` attest vector records `cleared-by-boot` and
   reaches `st1-verified` only after real CL-4 and CL-6 checks. Preserve the six
   pre-existing `/var/tmp/p5-r5-rp11-h0*` directories across the reboot;
5. a changed-boot case with a planted pathname, missing identity, wrong
   filesystem fact or failed PK/2/ST-1 check cannot claim `cleared-by-boot` or
   `st1-verified`;
6. concurrent attest invocations cannot publish the same attempt or record and
   cannot remove a foreign object;
7. default-action termination during cleanup leaves no false terminal record;
   a later explicit attest reports/reconciles only what the accepted evidence
   proves, with no automatic child action; and
8. teardown leaves no RP-11 unit, process, Polkit rule, artifact, staging/store
   test state, attempt evidence or logs; `polkit.service` is active,
   `/var/tmp` is `root:root 1777`, and the six protected pre-existing
   directories are untouched.

Do not restart Polkit merely to make rule removal observable; use its normal
directory watch. Reboot only the disposable host. Any test-only unit, fixture,
fault injector or installed artifact must be removed during teardown and must
not become a production installer.

## Required verification

On the final tree, run and record exact copy-pastable commands, working
directories, exit statuses, pass/fail/error/skip counts and every skip reason:

1. the new RT-5 unit/application tests plus affected cleanup, backstop,
   authority, journal, record, PK/2, artifact and manager tests;
2. the new root/systemd/sudo RT-5 host module with a fresh controlled artifact;
3. the explicit real-reboot attestation proof and separate post-reboot cleanup
   verification;
4. the complete `tests/systemd_integration` suite serially;
5. `tests/web/test_p3_4_static_assets.py`, reporting established unrelated
   baseline failures rather than hiding or repairing them;
6. the documented bot and web suites serially with
   `TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'`, confirming that the
   web skip count remains 80 rather than a false-green database-skipped count;
7. the Foundry Node suite;
8. Python compilation over every touched Python path, configured static checks,
   the repository guard tests and `git diff --check`.

Compare every failure with an applicable recorded baseline or freshly reproduce
it against accepted commit `94fb3e7`; do not call a failure pre-existing from
memory. Never run bot and web suites in parallel because they share the
disposable database. Re-sync the final tree before the final runs and verify
host cleanup separately after root tests and after the reboot proof.

Production and staging, real secrets and real player data remain outside the
authority.

## Documentation and handback

Create one concise
`docs/review/route-3-attest-role-implementation-handback.md`. Update only the
current-state documents needed to say that Claude implemented the uncommitted
RT-5 candidate and independent Codex review is pending. Do not record Peter's
acceptance, authorize the non-root executor or OC checks, or authorize
production/staging. Do not create a review/remediation prompt or proof chain.

The handback must include:

- delivered behavior and exact files;
- RT-5/PRE/CL/H-FI/DI-1/DI-5/DI-6/H-PK2/H-SN row-to-test coverage;
- exact focused, same-boot, real-reboot, host and comparison-suite commands and
  results;
- every failure, error and skip with verified baseline disposition;
- host cleanup state before and after reboot;
- deployment, migration and recovery effects plus remaining production risks;
- reversible implementation choices, especially treatment of manager states
  outside the explicitly admitted precondition set; and
- one recommendation: accept, remediate one specifically named blocker, or
  replace the approach.

Return the uncommitted candidate for independent Codex review. Production and
staging activation remain unauthorized. The transient inspection-failure
decision, retained PID/start-time/uid subject risk and final independent
production security review remain mandatory before any activation.
