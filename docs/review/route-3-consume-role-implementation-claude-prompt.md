# Claude implementation prompt — Route 3 `consume` role (RT-1)

Date: 2026-10-16
Authority: Peter Duscha, baseline v1.9 and the active implementation-first
delivery plan
Reviewer after handback: Codex

## Assignment

Implement RT-1 `consume`, the PID-1 `ExecStartPre=+` role that consumes one
accepted Route 3 activation grant before systemd may execute the fixed capture
unit's `ExecStart=`. Add exactly this controlled-artifact vector:

```text
/usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py consume
```

The role accepts no operand, option or alternate spelling. It identifies the
activation from the fixed `/run/freedom-blades-rp11/pass-a.json`, takes the
activation lock, creates the one-shot consume claim, removes the attributable
live Polkit rule, proves the grant is no longer authorizing `start`, and writes
durable `consumed` evidence before returning 0. Every other result is non-zero,
so PID 1 must not execute the capture service's main process.

Keep the implementation inactive outside `oracle-test`. Do not implement RT-5
`attest`, the non-root executor or its OC-1/OC-2/OC-3 checks, a production
capture-unit installer, migration/cutover work, production activation or
unrelated cleanup. Do not commit or push.

## Current working-tree boundary

The accepted implementation base is commit `7bdc930` (`Add and accept Route 3
start and stop roles`). The working tree also contains this reviewer-authored
prompt and current-state assignment edits. Preserve those files and all
unrelated maintainer changes. Inspect `git status` and the complete diff before
editing; do not reset, revert or overwrite accepted work.

## Required reading

Before planning or editing, read completely:

1. `.agents/AGENTS.md`;
2. the implementation-plan reading map, §§0, 12 Phase 5.0, 13, 14, 16 and 20;
3. `docs/review/Handover information`;
4. `docs/project-management/active-delivery-plan.md`;
5. `docs/operations/disposable-test-server.md`;
6. the accepted manager/Polkit, stop-post, backstop, hold, `start` and `stop`
   handbacks and the current implementations they name;
7. the operation inventory §§3 RT-1, 4, 5.1, 6 RT-1, 7, 8.1, 10 and the RT-1
   rows of §§11–12;
8. the interface contract §§3.0, 3.1, 3.5 and 3.6, including D-1 through D-6
   and the retained PID/start-time/uid risk; and
9. the current controlled-artifact entry point, manifest, application ports,
   authority/journal/evidence models, cleanup attribution and real-host tests.

Historical WP closure labels are not current development gates under baseline
v1.9. Their accepted RT-1, DI-1, DI-5, DI-6, H-FI, H-PK2 and H-SN requirements
remain implementation inputs. Where a reversible mechanism was formerly left
to a later package, choose the smallest implementation consistent with the
accepted contracts, record it briefly in code/tests or the handback, and prove
it. Stop and ask Peter only if the choice would change a safety boundary,
authorization policy, product scope or irreversible architecture.

## Boundary ownership

RT-1 begins at the first design-controlled image PID 1 executes as
`ExecStartPre=+` inside the fixed capture unit's start job. It receives nothing
from the requester. Its only environment input is its own systemd
`INVOCATION_ID`, used as provenance. If present it must occur exactly once and
be 32 lowercase hexadecimal characters; absence remains the literal accepted
`absent` provenance and cannot satisfy a real CQ-4 manager-ID comparison.

The future executor owns initiation of the larger pass and the later
OC-1/OC-2/OC-3 checks before SA-2. RT-1 does not implement that executor, choose
an activation, choose a capture root or finalize a pass. The disposable host
test may create a bounded test-only unit fixture to exercise the real
`ExecStartPre` relationship; do not add or install a production capture unit.

## Required behavior

Implement the accepted CQ-0 through CQ-7 sequence and preserve its ordering.
In particular:

- **First image.** Accept only `consume` with no operand. Run all accepted H-FI
  controls before role work: descriptors 0–2 open; every descriptor at or above
  3 closed and verified; resettable dispositions and the signal mask reset;
  umask `022`; cwd `/`; environment emptied. Unlike SA-1/SA-2, RT-1 processes
  `INVOCATION_ID` under the provenance rule above. It installs no signal
  handler; PID 1's finite `TimeoutStartUSec` remains the class-M terminator.
- **CQ-0 identify.** Open the fixed pass-config parent and `pass-a.json` through
  no-follow descriptors. Require a root-owned regular `0644`, one-link file no
  larger than 65,536 bytes. At this stage parse only a valid `activation_id`;
  malformed, missing, oversized, replaced or unsafe input is
  `consume-unidentified`, and creates nothing.
- **CQ-1 lock.** Derive K only from that validated activation ID, verify the
  accepted root-owned `0700` directory identity and try one non-blocking
  exclusive lock. Absence/invalidity is `consume-unidentified`; contention is
  `consume-busy`. Never wait for K and never scan, signal or kill its holder.
- **CQ-2 one-shot claim.** Under a verified root-owned `1777` `/var/tmp`, create
  `<activation_id>-consume-evidence` as root-owned `0700`, no replace. That
  creation is the permanent same-boot barrier. `EEXIST` is
  `consume-repeated`: do not open or trust the existing directory or journal.
  Create the claim journal exclusively, make it `0644`, then make the directory
  `0755`. Its canonical `run-start` must carry RT-1's invocation ID and boot ID,
  the claim identity, the exact ACT-journal digest/length and the accepted
  `lock`/`helper` fields. Flush the journal, claim directory and `/var/tmp` in
  the accepted order before continuing.
- **CQ-3 grant first.** Parse the bounded ACT journal and accepted authority
  chain; require the same boot. Take the staged-rule digest from that pinned
  authority chain, never from caller input or an untrusted journal field.
  Classify and re-verify the live rule through descriptors. Only an A1-intact
  rule may be removed. Durably append `remove-intent`, unlink exactly the fixed rule, flush
  its directory, then append `removed`. An absent, damaged, foreign or
  unprovable rule never becomes success.
- **Grant-priority failures.** Once a claim exists, any journal/open/write/flush
  failure must reduce the evidence RT-1 can claim, never preserve a safely
  removable live grant merely to report the failure. Use the accepted
  grant-priority form: classify and remove only from ACT identity plus the
  pinned authority digest, write no line that cannot be made durable, run
  CQ-5's negative authorization check in memory, never proceed to CQ-4, and
  always fail. If the claim could not be made, perform the same safe
  grant-priority removal/check
  where its prerequisites are available, then return `consume-claim-failed`.
- **CQ-4 preconditions.** Only after durable claim and grant removal, re-prove
  the unchanged pass-config identity and digest, same boot, activated root-owned
  activation record, valid ACT journal with `hold-start` and no `hold-end`, no
  deactivation evidence or record, and absence of the capture root named by the
  pinned pass config. Through DI-1 require the holder active with the journaled
  invocation ID and the capture unit activating with RT-1's invocation ID and
  the journaled inactive-enter timestamp. Every read error or mismatch fails
  closed as `consume-precondition`/`consume-failed`; a satisfied read is never
  treated as evidence of absence.
- **CQ-5 negative authorization.** Re-prove the fixed rule pathname absent,
  then run the existing PK/2 series in `SEEK_NOT_AUTHORIZED` mode for verb
  `start`, using the pinned operator, parameters, DI-5 and DI-6. Append the
  closed `grant-check` result. Only a positive `not-authorized` decision may
  continue. `authorized`, `unconfirmed`, timeout, malformed reply, transport
  error, subject error or abandonment is failure and can never be converted to
  success by pathname absence.
- **CQ-6/CQ-7 commit.** Append and flush `consumed {pk_status,
  inactive_enter_us}`. Then append and flush `run-end`, release K and return 0.
  A missing durable `consumed` line is never a pass. If `consumed` is durable
  but `run-end` fails, return non-zero and leave PID 1 unable to run
  `ExecStart=`. RT-1 writes no record file and removes no pass config, claim,
  directory or activation/deactivation record.

Use closed, bounded diagnostic tokens only. Preserve the accepted stable names
`consume-unidentified`, `consume-busy`, `consume-repeated`,
`consume-claim-failed`, `consume-evidence-unwritable`, `consume-precondition`
and `consume-failed {step, class}` without rendering exception text, arbitrary
paths, D-Bus detail, file content or environment values. Choose and document a
stable explicit non-zero exit map for failures; exit 0 belongs only to complete
CQ-7 success. Unexpected exceptions fail closed with a fixed value-safe line.

Reuse the accepted authority, journal, attribution, GRR, PK/2, signal-contract,
manager and filesystem primitives where their contracts match. Do not copy a
second weaker parser or removal path merely to isolate RT-1. Add narrowly scoped
ports/adapters where RT-1 needs behavior the current boundaries do not expose.
No dynamic distribution executable may appear below the controlled first
image; the only retained child intent is the existing DI-6 authorization
subject, governed by H-SN. Include every production module in the artifact's
exact source manifest, preserve the five accepted vectors while adding the
sixth exact vector, and preserve the artifact-integrity rules.

## Focused test requirements

Write regressions before the corresponding implementation where practical.
Map every RT-1 inventory row to an executable test or named host check. Cover at
least:

1. exact zero-operand parsing and rejection of every operand, option, alias,
   spelling/case variant before any state operation;
2. the specified absent provenance and refusal of duplicate, malformed and
   oversized `INVOCATION_ID`, plus preservation of the no-environment-read rule
   for SA-1/SA-2;
3. every CQ-0 identity/type/owner/mode/link/size/read/parse failure with no
   claim or mutation;
4. K absent/damaged/foreign and one-shot lock contention;
5. claim creation as the same-boot barrier, including concurrent calls,
   `EEXIST`, partial creation, every write/flush failure and refusal to open an
   existing claim;
6. ACT/H-1 parsing and authority-chain failures; absent, damaged, foreign,
   replaced and unremovable rules; descriptor/path replacement races; and proof
   that no unattributed object is removed;
7. grant-priority behavior at every evidence failure point, showing the live
   attributable grant is removed before slower persistent work and the attempt
   still cannot succeed;
8. every CQ-4 precondition independently false or unreadable, including both
   DI-1 sites and relevant replacement/race cases;
9. CQ-5 authorized, not-authorized, challenge, only-errors, still-authorized,
   subject replacement, interruption and timeout outcomes, with exact
   no-retry/settlement behavior and no success from pathname absence;
10. failure before and after `consumed`, proving only a durable `run-end` yields
    0 and proving K closes on every return/exception path;
11. default-signal interruption across representative points before claim,
    after claim, during removal, during PK/2 and after `consumed`, with the
    accepted residuals and no `ExecStart=` execution; and
12. preservation of accepted hold, stop-post, backstop, start and stop behavior,
    manifests, source allowlists and controlled-artifact checks.

Use mutation or fault-injection tests for the security-critical orderings; do
not weaken an assertion or widen an allowlist beyond the exact new files.

## Disposable-host proof

Use synthetic data and the documented secret-excluding synchronization command.
On `oracle-test`, build a fresh root-owned controlled artifact from the pinned
Jeepney wheel. Exercise RT-1 as the real PID-1 `ExecStartPre=+` of a disposable
fixed-name capture unit, not merely as a root subprocess.

At minimum prove:

1. a complete accepted activation reaches durable `consumed` and `run-end`,
   removes the live grant, releases K and permits the main process to start;
2. a failed RT-1 at each material phase leaves the main process unexecuted and
   systemd reports a failed start;
3. two concurrent starts cannot both consume, and a later same-boot attempt is
   refused without opening the existing claim;
4. the holder/capture invocation IDs and inactive-enter timestamp are checked
   against the real manager while RT-1 runs inside its own start job;
5. the real PK/2 negative-control series is decisive only after Polkit has
   ceased authorizing `start`;
6. termination and start-timeout cases preserve the accepted one-shot/residual
   behavior and are recoverable by the existing cleanup path;
7. a real complete lifecycle through accepted SA-1, hold, RT-1, SA-2 and cleanup
   introduces no regression; and
8. teardown leaves no RP-11 unit, process, Polkit rule, artifact, staging/store
   path or new `/var/tmp/rp11-act-*`/consume evidence/log, with
   `polkit.service` active and the six pre-existing
   `/var/tmp/p5-r5-rp11-h0*` directories untouched.

Do not restart Polkit merely to make rule removal observable; use its normal
directory watch. A test-only unit or fault injector must be removed during
teardown and must not become a production artifact.

## Required verification

On the final tree, run and record exact copy-pastable commands, working
directories, exit statuses, pass/fail/error/skip counts and every skip reason:

1. the new RT-1 unit/application tests plus the affected authority, journal,
   cleanup, PK/2, controlled-artifact and manager tests;
2. the new root/systemd RT-1 host module with a fresh controlled artifact;
3. the complete `tests/systemd_integration` suite serially;
4. `tests/web/test_p3_4_static_assets.py`, reporting any established unrelated
   baseline failures rather than hiding or repairing them;
5. the documented bot and web suites serially with
   `TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'`, checking that the
   web skip count remains the documented 80 rather than a false-green
   database-skipped count;
6. the Foundry Node suite;
7. Python compilation over every touched Python path; and
8. `git diff --check`.

Compare any failure with an actual recorded or freshly reproduced baseline; do
not call it pre-existing from memory. Do not run bot and web suites in parallel
because they share the disposable database. After root tests, verify cleanup
separately. Production and staging, real secrets and real player data remain
outside the authority.

## Documentation and handback

Create one concise
`docs/review/route-3-consume-role-implementation-handback.md`. Update only the
current-state documents needed to say that Claude implemented the uncommitted
RT-1 candidate and independent Codex review is pending. Do not record Peter's
acceptance or authorize RT-5, the executor, production or staging. Do not create
a prompt/review/remediation chain.

The handback must include:

- delivered behavior and exact files;
- RT-1/CQ-0…CQ-7/H-FI/DI-1/DI-5/DI-6/H-PK2/H-SN requirement-to-test coverage;
- exact focused, real-host and comparison-suite commands/results;
- every failure, error and skip with verified baseline disposition;
- host cleanup state;
- deployment, migration and recovery effects plus remaining production risks;
- any reversible implementation choice made where the old research left the
  mechanism open; and
- one recommendation: accept, remediate one specifically named blocker, or
  replace the approach.

Return the uncommitted candidate for independent Codex review. Production and
staging activation remain unauthorized. The transient inspection-failure
decision, retained PID/start-time/uid subject risk and final independent
production security review remain mandatory before any activation.
