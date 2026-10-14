# Claude assignment — LIT-FULL WP-3 contract integration

Date: 2026-10-12

Work ID: `C-P5.0-R5-RP11-H1-OH-S3-RT3-WP3-CI1-20261012-26`

Status: **proposed; independent Gemini review and Peter Duscha's explicit
acceptance of these exact bytes are required before one Claude execution**

Proposed executor after acceptance: Claude

Independent reviewer after return: Codex

Decision owner: Peter Duscha, Product Owner and Acceptance Authority

## Authorization condition and objective

This file is not presently executable. Claude may execute it exactly once only
after a separate acceptance-and-activation record states that Peter accepts
this file's exact line count, byte count and SHA-256, adopts the eight proposed
decisions below, and appoints Claude.

Once that condition is met, integrate the accepted WP-3 source-completion
evidence into the cumulative WP-3 interface contract, record decisions D-1
through D-6, D-9 and D-10 exactly as fixed below, and create the named
contract-integration handback. Preserve every remaining residual and gate.

This is repository-documentation integration only. It is not implementation,
WP-4 preparation, a Route 3 selection, a LIT-FULL implementation selection, or
authority to close Q6-6 or Q6-7.

## Required reading — binding precondition

Before the first deliverable edit, read every item below exactly as stated.
"Completely" means first byte through EOF during this execution; a prior read,
search result, excerpt, synopsis or memory does not satisfy it.

1. `.agents/AGENTS.md`, completely;
2. the reading map and §§0, 3, 5, 12.0, the complete section headed
   `Phase 5 — Existing automation migration`, 13, 16, 17 and 20 of
   `docs/implementation-plan.md`;
3. `docs/review/Handover information`, completely;
4. the active restriction banner in
   `docs/operations/disposable-test-server.md`;
5. `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-interface-contract.md`, completely;
6. `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-record.md`, completely;
7. `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r2-remediation-handback.md`, completely;
8. `docs/review/project-review-2026-10-11-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r2-remediation.md`, completely;
9. `docs/review/project-review-2026-10-11-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r2-remediation-acceptance.md`, completely;
10. `docs/review/project-review-2026-10-11-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-evidence-acceptance-and-contract-integration-direction.md`, completely;
11. this exact prompt, completely; and
12. `docs/review/project-review-2026-10-12-p5-r5-rp11-h1-oh-s3-lit-full-wp3-contract-integration-acceptance-and-claude-activation.md`, completely.

Before the first edit, record each item's path or precisely named portion, line
count, byte count and SHA-256 in working notes. The handback must reproduce the
complete ledger and state that all required reading was completed before the
first edit. If an item cannot be read as specified, the activation record is
absent, or that record does not identify this prompt's exact bytes and appoint
Claude, return `HARD STOP` without editing a deliverable.

The accepted source-completion record's fixed identity is 1,758 lines, 240,533
bytes and SHA-256
`4c2a1b76a72002de77ca885ba248f086c302b5e9aebebd117cfa90b8989a1049`.
The pre-integration interface contract's fixed identity is 469 lines, 50,599
bytes and SHA-256
`b766c10f2c28ac2d32a7dc7ee4ab2c92a3cf80d67fd70f345a9f0dd7ba92c888`.
Verify both before substantive integration. An identity mismatch is `HARD
STOP`; do not reinterpret changed bytes.

## Fixed accepted boundary

Preserve without reinterpretation:

- baseline v1.8;
- LIT-FULL under R3-ROOT remains a readiness investigation only;
- concrete Route 3 remains unestablished;
- in scope remain exactly RT-1 through RT-5, SA-1 (`start`) and SA-2 (`stop`);
- F-1 remains B2-F, both lifecycle acts remain in and B3-OUT remains effective;
- EX-1 and EX-2 remain effective only for their accepted uses; no EX-3 exists;
- no dynamic child or distribution executable is admitted beneath a first
  design-controlled root image;
- DI-6 remains the only retained replacement-child intent;
- H-1, RB-1, RS-1 and H-1R remain outside the set;
- Q6-6 and Q6-7 remain unanswered;
- BC-2 remains a later WP-9 decision;
- D-7, D-8 and D-11 through D-14 remain undecided and outside this assignment;
- Q3-9 remains blocked by R-03.1/D-7/Q6-2;
- Q3-11 retains `PO3-11.1` fail-closed treatment and remains blocked by D-11
  through D-14 and Q6-3;
- residual `R-M.1` remains visible and accepted only on the limited provenance
  basis recorded in the evidence-acceptance decision; it is not
  archive-chain authentication;
- no accepted evidence, historical prompt, handback, review, acceptance or
  snapshot is rewritten; and
- WP-4 through WP-7 remain separately gated and unauthorized.

Do not weaken any accepted failure, interruption, residual, cancellation,
unknown-effect, no-retry or fail-closed rule. A cancelled client wait is not
proof that a queued job stopped or that a mutating request had no effect.

## Decisions fixed by Peter's later acceptance of this prompt

The following text is a proposed decision package until Peter accepts this
prompt. Acceptance of these exact bytes adopts all eight choices as a unit.
Claude must record them without substitution or expansion.

### D-1 — one transport

Use the system message bus for DI-1, DI-2, DI-3, DI-4 and DI-S, and for DI-5 as
required by Polkit. Do not select systemd's private manager socket. This keeps
one authenticated transport locus, matches accepted TR-4 and avoids a second
transport contract. Record installed broker/version/policy as residual R-01.1,
not as an assumed fact.

### D-2 — DI-5 request

Select P-10.1 shape S-A: `CheckAuthorization` with subject
`("unix-process", {pid u, start-time t, uid i})`, action
`org.freedesktop.systemd1.manage-units`, details containing exactly `unit` and
`verb`, flags `0`, and empty cancellation id. The supplied `uid` is deliberate;
the general PID/start-time decoder permits it to be absent, but the accepted
H-PROC.5 obtains it and this contract requires it.

### D-3 — errors and transport failures

Adopt P-04.1 with only the already defined refusal cases:

- DI-2 `UnitExists` is `refused(exists)`;
- method-specific `InvalidArgs` before mutation is `refused(invalid-request)`;
- systemd `AccessDenied` or `InteractiveAuthorizationRequired` is
  `refused(not-authorized)` where the manager refuses the requested operation;
- DI-4/DI-S `NoSuchUnit` uses D-9 below; and
- a normal DI-5 challenge is not a D-Bus error and uses D-6 below.

Every other D-Bus ERROR, unknown error name, malformed/truncated/oversized
reply, authentication or service-availability error, disconnect, `NoReply`,
transport timeout, client deadline or abandoned wait is `error(kind)`. For a
mutating interface it also carries the accepted wording `effect not confirmed`
and never permits a silent retry. Do not map the four Polkit ERROR names to
`not-authorized`; D-6 maps only a well-formed normal reply.

The concrete `kind` vocabulary beyond the stable categories already named is
a WP-4 matter. Do not decide Q6-6 or Q6-7 by translating `effect not confirmed`
to any new non-child `effect` field.

### D-4 — completion observation

Select P-05.3 O-C for DI-2, DI-3, DI-4 and DI-S:

1. install the system-bus signal match and call `Manager.Subscribe()` before
   issuing the mutating method;
2. retain the returned job path and accept a `JobRemoved` completion only when
   that path and the expected unit match;
3. after completion, read the target unit state needed by the calling contract;
   and
4. treat the state read as an observation, not as a reconstruction of a lost
   `JobRemoved` result or proof that this request caused the state.

If the method reply is lost, the connection is lost, no matching signal is
received before the later WP-4 deadline, or the completion cannot be parsed,
return `error` with `effect not confirmed`; do not retry. A state read may be
recorded as observed context but may not promote that result to `ok` or
`refused`. A `JobRemoved` result other than `done` is `error(job-result)`.
A `done` stop of a loaded already-inactive unit is D-9's benign no-op.

This decides the observation design, not the deadline mechanism (Q4-7), the
meaning of `effect: "unknown"` for a non-child call (D-8/Q6-6), or its possible
BS-4 extension (Q6-7).

### D-5 — authorization subject form

Retain H-PROC.5 and select the PID/start-time/uid subject of D-2, not the pidfd
form. Do not amend the accepted process-creation contract or add file-descriptor
passing in WP-3. Preserve A-13.4 prominently: upstream calls this fallback
known broken for race-free process identity. The choice is compatibility with
the accepted boundary, not a claim of race freedom. The residual must remain a
Route 3 readiness risk and must be carried to any later WP-4 consideration.

### D-6 — DI-5 result mapping

Adopt P-11.1. For a well-formed `(bba{ss})` reply:

- `is_authorized=true` and `is_challenge=false` is `authorized`;
- `is_authorized=false` and either value of `is_challenge` is
  `not-authorized`; and
- both booleans true is `error(invalid-reply)`.

Every D-Bus ERROR, wrong signature, malformed/truncated/oversized reply,
deadline or abandon is `error` under D-3. The returned details map is not used
to alter these three outcomes.

### D-9 — stop of inactive or not-loaded unit

Distinguish the two facts rather than merging them:

- loaded and already inactive/failed, followed by `JobRemoved … done`, is
  `ok(already-stopped)`; and
- `NoSuchUnit` before a job is queued is `refused(not-loaded)`.

Apply this to DI-4 and DI-S. Do not infer from either result that a different
earlier request had no effect. Preserve the special fact that a transient unit
already collected after a prior stop is in the not-loaded case.

### D-10 — backstop service timeout property

Follow accepted WP-2 row `RT2.AK1.2` and BS-RM: the DI-3 backstop service has
no `TimeoutStartUSec` property. Its relevant properties remain `Type=exec`,
`Restart=no`, `OOMScoreAdjust=-1000`, `RuntimeMaxUSec=⟨S_b⟩·10⁶`,
`TimeoutStopUSec=⟨S⟩·10⁶` and the accepted `ExecStart`. Record that this
decision resolves only the conflicting `TimeoutStartSec=⟨S⟩` literal in D R2
(f) for the LIT-FULL DI-3 contract; it does not rewrite the historical source.

## Required contract integration

Correct the interface contract cumulatively in place. Do not merely append a
decision list while leaving its earlier `UF`, `PSC`, stop and readiness text in
contradiction. At minimum:

1. Replace the title/terminal summary with an accurate cumulative state. State
   that the accepted source-completion record now gives the evidence result,
   proposals and residuals for every former `UF-01` through `UF-18`; do not
   turn a `PSC`, residual or unavailable mechanism into a source fact. Only
   D-1 through D-6, D-9 and D-10 are decided.
2. Add the accepted source-completion record to the source hierarchy with its
   fixed identity. Preserve its `ASF`, `MD`, `PSC`, residual and observation
   classifications; only the eight adopted proposals become accepted contract
   decisions.
3. Reconcile every DI-1 through DI-6 and DI-S section with A-01 through A-14,
   the selected decisions, and the exact request/response, encoding,
   completion, cancellation and failure semantics. Retain citations by stable
   source-record identifier rather than copying unsupported facts from memory.
4. Reconcile Q3-1 through Q3-7 as **closure-ready** on the accepted evidence
   and these eight decisions, consistently with source-record §9 recommendation
   2. Do not call that closure accepted before independent review and Peter's
   later gate decision. Keep Q4-1/Q4-7/Q4-8/Q4-11 and Q6-6/Q6-7 visible as
   later-package inputs without treating them as missing WP-3 interface facts;
   do not decide them. D-7 remains with Q3-9/Q6-2 and D-8 with Q6-6.
5. Keep Q3-9 and Q3-11 open exactly as fixed above. Do not select P-15 through
   P-18 or decide D-11 through D-14.
6. Update the citation matrix, WP-4 input table, Q3-tagged-row reconciliation,
   acceptance checklist, stop result and all cross-references so they agree.
7. Add a durable decision register for D-1 through D-14 showing the eight
   decisions adopted here and the six still undecided. Include rationale,
   affected interfaces and retained risks for every adopted decision.
8. Preserve R-01.1 through R-18.x, `R-M.1`, O-1 through O-5 and the two
   accepted-record editorial observations unless the accepted evidence or an
   adopted decision expressly changes their status. Do not silently erase a
   residual because its preferred option was not selected.
9. Add a cumulative change register that identifies every prior contract row
   or section changed and its replacement, including the former `HARD STOP`
   wording. Historical files remain unchanged.
10. End with the exact normal return state:
   `WP-3 CONTRACT INTEGRATION RETURNED — INDEPENDENT CODEX REVIEW PENDING`.
   This state does not authorize WP-4 and does not itself accept the integrated
   contract.

If the accepted evidence plus the fixed decisions cannot support a required
replacement without deciding D-7, D-8 or D-11 through D-14, answering Q6-6 or
Q6-7, inventing a fact, or weakening a boundary, preserve the conflict and
return `HARD STOP` instead of filling it.

## Deliverables

1. Correct cumulatively in place:
   `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-interface-contract.md`.
2. Create:
   `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-contract-integration-handback.md`.

The handback is mandatory for every terminal state and must contain:

- work ID, executor, UTC date and terminal state;
- complete pre-edit reading ledger;
- pre- and post-edit line count, byte count and SHA-256 for the contract;
- line count, byte count and SHA-256 for the handback, using the established
  self-identity convention if necessary;
- a D-1 through D-14 disposition table;
- exact section-level change ledger;
- Q3 closure/readiness table before and after integration;
- retained residual and open-question register;
- files created, files changed and confirmation that all other paths stayed
  unchanged;
- checks performed and their exact results;
- checks deliberately not performed; and
- confirmation that no prohibited operation occurred.

## Current-state reconciliation on return

Before changing a current-state pointer, preserve its exact pre-return bytes in
these new snapshots beside the canonical files:

1. `docs/review/Handover-information-through-2026-10-12-lit-full-wp3-contract-integration-authorization.md`;
2. `docs/project-management/status-through-2026-10-12-lit-full-wp3-contract-integration-authorization.md`;
3. `docs/implementation-plan-through-2026-10-12-lit-full-wp3-contract-integration-authorization.md`; and
4. `docs/operations/disposable-test-server-through-2026-10-12-lit-full-wp3-contract-integration-authorization.md`.

Add each snapshot's SHA-256 to its corresponding archive README. Never
overwrite a snapshot. Then reconcile only:

1. `docs/review/Handover information`;
2. `docs/project-management/status.md`;
3. implementation-plan §20; and
4. the active restriction banner in
   `docs/operations/disposable-test-server.md`.

All four pointers must link the handback and agree on the exact normal return
state above, or on `HARD STOP — WP-3 CONTRACT INTEGRATION` with the precise
reason. Preserve all restrictions and later gates.

## Checks

Run only repository-static checks:

- `wc -l -c` and `sha256sum` for every required identity and deliverable;
- exact searches for D-1 through D-14, Q3-1 through Q3-11 as applicable,
  Q6-6, Q6-7, `UF-`, `PSC`, `HARD STOP`, `TimeoutStart`, `pidfd`,
  `effect not confirmed` and `R-M.1`;
- Markdown table-shape and repository-relative link-target checks;
- a citation-identifier comparison against the accepted source-completion
  record;
- `git diff --check`; and
- read-only `git status --short` and `git diff --stat`.

Do not run tests, builds, formatters, hooks or application code. This assignment
changes documentation and performs no executable implementation.

## Permitted and prohibited operations

Permitted: repository reads/searches; editing the two deliverables; creating
the four exact return snapshots; adding four archive-index rows; and reconciling
the four exact current-state pointers. Ordinary read-only Git inspection and
the static checks above are permitted.

Prohibited: network access; SSH; `oracle-test`; production, staging, Foundry,
databases or retained evidence; secrets or credentials; host-installation,
package, `/etc`, `/proc` or `/sys` inspection; application, configuration,
infrastructure or launcher edits; source retrieval; implementation; package
installation; service/database operations; tests, builds, formatters or hooks;
cleanup outside files created by this assignment; activation; rollback; commit;
and push. Do not touch R5 or H-0G retained paths.

## Terminal states

- `PASS`: the two deliverables, return snapshots, archive rows and four pointer
  updates are complete and consistent. The pointer state is the exact normal
  return phrase. `PASS` does not accept the integrated contract or authorize
  WP-4.
- `HARD STOP`: an identity/reading precondition fails, evidence is insufficient
  under the fixed decisions, a conflict requires an excluded decision, or an
  authorized deliverable cannot be completed. Write the complete handback and
  reconcile the pointers to the exact hard-stop state before stopping.
- `INVALID RUN`: a prohibited action occurred, the accepted boundary was
  crossed, or the run cannot establish what bytes it read or changed. Write
  the complete handback, disclose the condition, reconcile the pointers and
  stop.

At the first terminal state, finish the handback and bounded pointer
reconciliation, then stop. Do not begin remediation, WP-4 preparation or any
later work.
