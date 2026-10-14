# Claude implementation prompt — Route 3 backstop role

Date: 2026-10-13
Authority: Peter Duscha's continuation of the accepted Route 3 sequence,
baseline v1.9 and the active delivery plan
Mode: implement, test comprehensively on `oracle-test`, remediate concrete
defects once, and hand back

## Assignment

Implement the exact controlled `backstop` vector over the delivered shared
cleanup engine:

```text
/usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py \
  backstop <activation_id> <a2_sha256>
```

Implement RT-4 BS-1 through BS-4 and its composition of shared CL. Leave
`hold` refusing with exit 69. Do not implement `attest`, `consume`, the static
`start`/`stop` roles, an installer, production activation or unrelated Phase 5
work. Preserve unrelated working-tree changes. Do not commit or push.

Work through implementation, focused tests, real root/systemd/Polkit tests and
one bounded remediation cycle. Do not return a plan or create another proof or
prompt-review chain.

## Read before editing

1. `.agents/AGENTS.md` in full.
2. `docs/implementation-plan.md`: reading map and §§0, 12 Phase 5.0, 13, 14,
   16 and 20.
3. `docs/review/Handover information`,
   `docs/project-management/active-delivery-plan.md` and
   `docs/operations/disposable-test-server.md`.
4. `docs/review/route-3-stop-post-role-implementation-handback.md` and the
   delivered `application/rp11`, `adapters/rp11`, artifact and tests end to end.
5. The operation inventory §§4 helpers genuinely used by RT-4, 5.4, 6 RT-4,
   7, 8.1, 9, 10.3, 11.1 and the applicable §12 gap rows.
6. The interface contract §§3.0–3.6 and the accepted manager-adapter handback.

The old research gates are historical, not active prerequisites. Explicit GAP
rows remain non-operative. For reversible details the accepted text leaves
open—such as the destination of the BS-4 terminal line—choose the smallest
root-controlled, bounded design, pin it in tests and record it briefly. Stop
only for a choice that changes product scope, authorization/privacy,
production data authority, destructive production behavior or irreversible
architecture.

## Delivered base to preserve

Build on these interfaces; do not fork replacements:

- `application.rp11.cleanup.CleanupProcedure`, `Invocation`, `Trigger` and the
  typed terminal outcomes;
- `application.rp11.authority.Params`, `A2Pins`, `H1Record` and `Authority`;
- `application.rp11.records.validate_record` and schema
  `rp11-activation-record/2`;
- `application.rp11.paths.Layout` and `ActivationPaths`;
- `adapters.rp11.fsops.LocalRecordStore`, `LocalAttemptStore`, `LocalLock`,
  `LocalActivationFs` and `LocalHostFacts`;
- `adapters.rp11.stop_post.StopPostServices` and its shared composition
  pattern; and
- `UnitControl.read_unit()` and `disarm_backstop()` through the accepted
  `SystemdManagerAdapter`.

Extend narrow interfaces where RT-4 genuinely needs more capability. Do not
make the filesystem or unit-control APIs generic, and do not put orchestration
into `rp11_roles.py`.

Before changing code, replace the three `SUITE_BOT`, `SUITE_WEB` and
`SUITE_FOUNDRY` placeholders in the completed stop-post handback with the exact
already-obtained results, or run the documented serial suites and record their
exact results. This is completion of the preceding handback, not a new review
gate; continue unless it reveals a new Route 3 regression.

## Required behavior

### Authority and first image

- Apply the same first-image, operand, descriptor, environment, signal, cwd,
  umask and installed-artifact integrity controls as `stop-post`.
- Add `backstop_max` to the H-1 `Params` authority with accepted range 1–99 and
  recommended/default value 20. Keep the document closed-key validation,
  canonical encoding and existing parameter bounds. Update fixtures and all
  record expectations coherently; do not accept a caller/environment override.
- Add `Trigger.BACKSTOP` and ensure CL records and diagnostics identify the
  trigger as `backstop` while retaining the same cleanup semantics.

### BS-1 — holder ownership

- Read only `ActiveState` of `holder_unit_name(activation_id)` through DI-1.
- For `activating`, `active`, `deactivating` or `reloading`, exit 0 with no
  mutation, attempt directory, journal or record.
- `inactive`, `failed` and a typed not-loaded result continue to BS-2. Any
  timeout, disconnect, malformed reply, unexpected refusal or other read error
  exits non-zero and performs no mutation. Never read an error as inactive.

### BS-2 and BS-3 — terminal record decisions

- Add a narrow, descriptor-relative, no-follow, bounded record enumeration
  operation. It may consider only exact
  `<activation_id>.deact-<k>.json` names with `1 <= k <= 99` in the fixed
  root-controlled record directory.
- Select the greatest present `k` as the latest attempt. Read it with the
  existing root-owned, one-link, mode-0444 and size-capped record path, parse
  canonical bytes, run `validate_record`, and require its `activation_id` and
  `attempt` to match the name and requested activation. A malformed, missing,
  replaced, symlinked, oversized or mismatched greatest record must not be
  skipped in favor of an older success; continue fail-closed to BS-4.
- BS-2: if that record is valid `deact` / `st1-verified`, call DI-4 exactly once
  for this activation's derived backstop timer, then exit 0 only on confirmed
  `ControlOk` or the narrow pre-mutation `NOT_LOADED` refusal.
- BS-3: if the valid latest record is `hard-stop`, disarm only when its recorded
  residual/identity evidence proves no A1-intact activation object remains and
  `active_rule.class` is neither `removed-unconfirmed` nor
  `grant-unremovable`. Pin the exact predicate in small pure tests. Otherwise
  continue to BS-4.
- At the BS-2 and BS-3 disarm sites, an error after dispatch has unknown effect:
  exit non-zero, do not retry, do not run CL, do not write a record and never
  claim the timer is stopped. Apply the same conservative rule to any other
  DI-4 error or unexpected refusal.

### BS-4 — cleanup and terminal bound

- Otherwise run the existing `CleanupProcedure` once with trigger `backstop`.
  CL-G remains the first cleanup act. Reuse every attribution, grant-priority,
  interruption, Polkit-subject, record and diagnostic rule from stop-post.
- Determine the prospective cleanup attempt from exact existing attempt names.
  At most `backstop_max` firings may enter CL and no attempt may exceed 99.
  At `B+1` or prospective `k > 99`, do not enter CL and do not fabricate a
  cleanup record.
- On that terminal path, make one DI-4 call, append one bounded canonical line
  to a root-controlled existing/new backstop-terminal journal chosen as the
  reversible implementation detail, durably flush it, and exit non-zero. The
  line must state only classes/tokens: activation, bound reason and typed
  disarm outcome—no environment, raw evidence or exception value.
- For the previously open Q6-7 detail, use the reversible fail-closed default:
  a terminal DI-4 timeout, disconnect, lost reply or other unconfirmed effect
  is recorded as unconfirmed, is never silently retried and never becomes a
  claim that the timer stopped. Journal failure also remains non-zero and must
  not trigger a record or CL run.
- Concurrent firings must not allow more than B CL attempts. Use the existing
  per-activation lock/attempt ownership or a narrower equivalent; after losing
  a publication/attempt race, re-observe and take only a valid current branch.
- Never start, stop, restart, signal or kill the holder or capture unit. The
  only BS mutation outside shared CL is DI-4 on the derived timer name.
- Keep output fixed, bounded and safe. Unexpected exceptions exit 70 without a
  traceback or success claim.

## Tests and disposable-host execution

Add regression-first application/adapter tests. At minimum cover:

- exact role vector acceptance; `hold` still exit 69; all other shapes refused;
- every holder state, not-loaded, malformed reply, timeout and disconnect;
- no evidence access or mutation on the BS-1 early-exit/error branches;
- no records; one valid latest `st1-verified`; one valid latest `hard-stop` for
  every residual/grant predicate; multiple attempt numbers and irrelevant
  names;
- malformed, non-canonical, torn, oversized, foreign, wrong-mode, symlinked,
  replaced and activation/attempt-mismatched latest records, proving no fallback
  to an older success;
- all three logical DI-4 sites with confirmed stop, not-loaded, timeout,
  disconnect, lost reply, late completion and no silent retry;
- B-1, B and B+1 plus prospective k=99 and k=100, including B < 99;
- terminal-line short write/fsync failure, fixed diagnostics and no record;
- shared CL success, hard-stop, GP-R3 and interruption/recovery with trigger
  `backstop`;
- simultaneous timer firings, attempt/publication collisions and proof that no
  execution exceeds B or targets another activation/unit; and
- artifact manifest/import behavior under exact Python 3.14 `-I -S`.

On `oracle-test`, build a fresh root-owned artifact and run the exact vector as
the backstop service through real PID 1. Exercise BS-1 ownership, BS-2 and BS-3
disarms, repeated firings through terminal bound, manager and Polkit restart,
an interrupted cleanup recovered by the next firing, concurrent firings and a
deliberately hung firing terminated by the real `RuntimeMaxSec` /
`TimeoutStopSec` properties. Verify every firing and disarm targets only its
own derived units.

Run focused suites locally where supported and on `oracle-test`, then root
integration twice on the final tree. Re-sync and run bot, web and Foundry
suites serially with the documented database settings; compare exact results
to the completed stop-post baseline and do not repair unrelated failures. Run
guard tests, `git diff --check`, `compileall` and configured static checks.

After every root run remove and verify absence of all RP-11 units, processes,
Polkit rules, artifacts, evidence and record state, and verify
`polkit.service` is active. Use no real secret or player data.

## Acceptance and handback

RT-4 is acceptable only when every RT-4 row has a named executable test or
real-host check, all three disarm sites fail closed, no malformed/older record
can authorize disarm, no foreign object is removed, retry bounds terminate,
real PID-1 containment works, `hold` remains unavailable and no new repository
suite regression appears.

Write one concise handback at
`docs/review/route-3-backstop-role-implementation-handback.md` containing:

- behavior delivered and principal files changed;
- RT-4 row-to-test/check coverage;
- exact commands and results, skips and unchanged baseline failures;
- exact-runtime, PID-1, Polkit, interruption, concurrency and recovery results;
- cleanup confirmation;
- remaining production risks; and
- one recommendation: proceed to hold, remediate one named blocker, or replace
  the approach.

Do not update status or handover. Do not create a review/remediation prompt,
proof chain, hash ledger or source-completion package.
