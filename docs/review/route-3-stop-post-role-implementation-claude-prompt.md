# Claude implementation prompt — Route 3 shared cleanup and stop-post

Date: 2026-10-13
Authority: Peter Duscha's acceptance of the Route 3 adapter, baseline v1.9 and
the active handover
Mode: implement, test comprehensively on `oracle-test`, remediate concrete
defects once, and hand back

## Assignment

Implement the shared Route 3 cleanup engine and the exact controlled role
vector:

```text
/usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py \
  deact <activation_id> <a2_sha256> stop-post
```

This is the first of three sequential role slices. Implement RT-3 (`stop-post`)
and only the shared primitives it genuinely consumes. Leave `hold` and
`backstop` refusing with exit 69. Do not implement `attest`, `consume`, the
static `start`/`stop` roles, production activation, or unrelated Phase 5 work.

Work through implementation, focused tests, real root/systemd/Polkit tests and
one bounded remediation cycle. Do not return a plan or create another proof or
prompt-review chain. Preserve unrelated working-tree changes. Do not commit or
push.

## Read before editing

1. `.agents/AGENTS.md` in full.
2. `docs/implementation-plan.md`: reading map and §§0, 12 Phase 5.0, 13, 14,
   16 and 20.
3. `docs/review/Handover information` and
   `docs/project-management/active-delivery-plan.md`.
4. `docs/operations/disposable-test-server.md`.
5. `docs/review/route-3-manager-polkit-implementation-handback.md` and the
   current Route 3 implementation/tests end to end.
6. The operation inventory, limited to the parts this slice consumes:
   `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp2-operation-inventory.md`
   §§2.3–2.4, 3, 4.1–4.16, 5.3, 6 RT-3, 7, 8.1, 9, 10.1, 11.1 and
   the applicable deferred-question rows in §12.
7. The interface contract §§3.0–3.6 for the already implemented DI boundary.

The inventory is an implementation contract, not a reason to restart its old
research gates. Where it explicitly marks an operation as a non-operative GAP,
do not invent it. For an unspecified reversible representation or path, choose
the smallest root-controlled design, pin it in tests and document it briefly.
Stop only for a choice that would change product scope, authorization/privacy,
production data authority, destructive production behavior or irreversible
architecture.

## Required behavior

Implement RT-3 and its shared cleanup composition exactly enough that each
applicable row has executable evidence:

- Run the first-image controls before state access: validate the exact role
  operands, treat the environment as untrusted except the exact systemd
  invocation-id selection allowed by H-FI, verify descriptors 0–2, close higher
  descriptors, reset signal state/mask, fix umask and working directory, and do
  not add dynamic subprocesses.
- Implement CL-G as the first cleanup act: use `grant.id` when valid, apply GRR,
  and remove an attributable intact grant before any persistent evidence write,
  lock wait, authorization subject or other slower work.
- Implement CL-0 through CL-7 and GP-R3 with descriptor-relative, no-follow,
  bounded operations. Preserve the operation inventory's attribution classes:
  never remove A0, damaged, foreign, invalidly evidenced or unverified objects.
- Implement the accepted canonical journal and activation-record formats,
  volume caps, hash chains, write-ahead ordering, `fsync` points, attempt count
  and no-replace publication. Existing records are append-only in normal
  operation and are never rewritten or deleted.
- Use the accepted `SystemdManagerAdapter`, `PolkitAuthorityAdapter` and
  `ProcSubjectSource` boundaries for DI-1, DI-5 and DI-6. Do not call
  `systemctl`, `pkcheck`, `sleep`, a shell or another distribution executable.
- Create each Polkit subject through a narrow controlled static/image path with
  the accepted uid/gid/groups, separate session/process group and maximum
  60-second self-lifetime. Implement the H-SN validation, signal and reap
  contract; never treat a successful send or `ESRCH` as proof of exit.
- Implement baseline and evidence verification without trusting browser,
  environment or caller-supplied calculated values. Report the first differing
  baseline key safely when applicable.
- Produce only the accepted terminal classes: `st1-verified`, hard stop with a
  residual list, `record-unpublished`, `evidence-unwritable`,
  `unit-still-active`, or a narrower fail-closed error. A missing or malformed
  fact must never become successful cleanup.
- Keep output bounded and safe: no raw evidence contents, secrets, environment,
  internal exception traceback or unrelated player data.
- Keep the installed artifact root-owned/non-writable invariant from the
  accepted adapter slice. Add every new runtime module to the explicit artifact
  manifest and retain exact-wheel verification.

Choose a small typed object model for journals, records, attribution and cleanup
outcomes. Keep filesystem, systemd/Polkit transport and orchestration concerns
separate. Do not put the whole cleanup procedure into `rp11_roles.py`.

## Tests

Add regression-first unit/application tests using temporary trees and injected
adapters. At minimum cover:

- exact vector acceptance and refusal of every other role/argument shape;
- first-image descriptor, environment, signal and working-directory controls;
- valid cleanup to `st1-verified`;
- missing, torn, non-canonical, oversized, hash-chain-invalid and wrong-run
  journals;
- intact, absent, damaged, foreign, symlinked, replaced and unremovable rule,
  pass file and directory objects;
- grant removal ordering before persistent writes, locks and Polkit calls;
- lock acquired, degraded after deadline, concurrent cleanup and attempt `k`
  exhaustion;
- every DI-1/DI-5/DI-6 success, denial, malformed, timeout, disconnect and
  subject-replacement path used by RT-3;
- interruption/failure injection at L0–L9 and the H-SN reap-error,
  identity-mismatch, abandoned and late-send paths;
- journal/record short write, failed flush, publication collision and recovery;
- safe bounded diagnostics and absence of dynamic subprocess/shell use; and
- artifact build/import under the exact `/usr/bin/python3.14 -I -S` runtime.

On `oracle-test`, build a fresh root-owned artifact from synthetic inputs and
exercise stop-post through PID 1 against real systemd and Polkit. Use deliberately
damaged, foreign-owned and replaced fixtures and prove they are retained and
reported. Exercise interruption/restart recovery and cleanup after every run.
Do not use real secrets or player data.

Run the focused suites locally where supported, then on `oracle-test`. Re-sync
the final tree and run the bot, web and Foundry suites serially with the
documented `TEST_DATABASE_URL`, comparing exact names/counts with the current
baseline in the accepted adapter handback. Do not repair unrelated baseline
failures or weaken a structural guard to obtain green output. Run guard tests,
`git diff --check`, `compileall` and configured static checks.

After every root run verify no RP-11 unit, subject process, Polkit rule,
artifact/staging directory, marker or test evidence remains and that
`polkit.service` is active.

## Acceptance criteria

- RT-3 and every shared operation it consumes map to named executable tests or
  a named real-host check.
- Cleanup removes only an immediately reverified A1-intact object and removes a
  live attributable grant before slower cleanup work.
- Malformed, missing, damaged, foreign, concurrent and interrupted states fail
  closed without false `st1-verified`.
- DI and subject failures never become authorization or cleanup success.
- Journals and records are bounded, canonical, ordered, durable and
  append-only/no-replace as specified.
- Exact isolated-runtime and PID-1 execution work on `oracle-test`; cleanup is
  complete afterward.
- No new bot, web or Foundry regression is introduced.
- `hold` and `backstop` still refuse with exit 69 and production remains
  inactive.

## Handback

Write one concise handback at
`docs/review/route-3-stop-post-role-implementation-handback.md` containing:

- behavior delivered and principal files changed;
- operation-row-to-test/check coverage for RT-3;
- exact commands and results, including skips and unchanged baseline failures;
- exact-runtime, real-host, interruption and recovery outcomes;
- cleanup confirmation;
- remaining production risks; and
- one recommendation: proceed to backstop, remediate one named blocker, or
  replace the approach.

Do not update status or handover unless the active assignment actually changes.
Do not create another review prompt, remediation prompt, proof chain, hash
ledger or source-completion package.
