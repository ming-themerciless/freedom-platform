# Gemini prompt — independent review of proposed WP-3 contract integration

Review work ID: `C-P5.0-R5-RP11-H1-OH-S3-RT3-WP3-CI1-REV1-20261012-27`

## Role and objective

Peter Duscha assigns Gemini to perform an independent, repository-only review
of the proposed Claude contract-integration assignment. Review the prompt; do
not execute it, edit the interface contract, adopt its proposed decisions,
accept it, appoint Claude or authorize WP-4.

Candidate:

`docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-contract-integration-claude-prompt.md`

Expected candidate identity:

- lines: `358`;
- bytes: `18,188`; and
- SHA-256: `894470357ed0fa1ed6c0fba251c471a9e549b7412068b1c1009984580ea91fce`.

This review assignment authorizes only repository reads/static checks, the
single durable review record, four pre-return snapshots, four archive-index
rows and bounded reconciliation of the four current-state pointers.

## Required reading

Before substantive review, read completely, first byte through EOF except
where a named portion is expressly sufficient:

1. `.agents/AGENTS.md`;
2. the reading map and §§0, 16, 17 and 20 of
   `docs/implementation-plan.md`;
3. `docs/review/Handover information`;
4. the active restriction banner in
   `docs/operations/disposable-test-server.md`;
5. the candidate prompt above;
6. `docs/review/project-review-2026-10-11-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-evidence-acceptance-and-contract-integration-direction.md`;
7. `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-interface-contract.md`;
8. `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-record.md`;
9. `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r2-remediation-handback.md`;
10. `docs/review/project-review-2026-10-11-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r2-remediation.md`; and
11. `docs/review/project-review-2026-10-11-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r2-remediation-acceptance.md`.

Independently run `wc -l -c` and `sha256sum` on the candidate before review.
If any expected value differs, do not review changed bytes; return the identity
hard stop defined below.

## Review standard

Determine whether Peter can safely accept the exact candidate, thereby adopting
its eight-decision package and authorizing one Claude execution. At minimum:

1. verify the activation condition prevents execution before a separate exact-
   identity acceptance and Claude appointment; the named future activation
   record is expected to be absent during this review and must not be created
   by Gemini;
2. verify the candidate decides exactly D-1 through D-6, D-9 and D-10, and
   neither decides nor indirectly answers D-7, D-8, D-11 through D-14, Q6-6 or
   Q6-7;
3. review each proposed choice against A-01 through A-14, P-01/P-04/P-05/P-09/
   P-10/P-11/P-13, the accepted contract and the governing boundary;
4. determine whether system bus for all manager calls is supported and whether
   R-01.1 remains disclosed;
5. verify the PID/start-time/uid Polkit shape matches H-PROC.5, keeps `uid`
   mandatory in this contract, and carries A-13.4's known-broken race warning
   without implying race freedom;
6. verify D-3 maps only justified pre-mutation refusal cases, maps every Polkit
   ERROR to `error`, preserves unknown/unconfirmed effects and grants no retry;
7. verify O-C installs observation before mutation, filters by returned job
   path, uses state reads only as observation, and defines missing-signal/
   disconnect/deadline behavior without deciding Q4-7, Q6-6 or Q6-7;
8. verify D-6 covers every boolean combination and every non-normal reply;
9. verify D-9's distinction between loaded already-inactive and not-loaded is
   consistent for DI-4 and DI-S and does not manufacture causal proof;
10. verify D-10 resolves the accepted-text discrepancy narrowly and preserves
    the remaining DI-3 properties;
11. verify contract integration removes contradictions rather than appending
    decisions, preserves evidence classifications/residuals, makes Q3-1
    through Q3-7 closure-ready without pre-accepting them, and keeps Q3-9 and
    Q3-11 open;
12. verify Q3-9, Q3-11, D-7/D-8/D-11…D-14, R-M.1 and all later gates remain
    explicit;
13. verify deliverables, identities, reading ledger, snapshots, archive rows,
    current-pointer reconciliation, checks and terminal states are exact and
    feasible; and
14. verify no host, network, retained evidence, implementation, test, build,
    formatter, commit, push or later-package authority is created.

Do not treat verbosity or stylistic preference as a finding unless it affects
correctness, safety, auditability or executability. Do not remediate the
candidate during review.

## Finding classes and required record

Use Blocking, Important and Optional. For each finding give a stable ID such as
`WP3-CI-AR1`, class, exact candidate location, governing evidence, impact and
smallest sufficient correction. State zero explicitly for empty classes.

Create exactly:

`docs/review/project-review-2026-10-12-p5-r5-rp11-h1-oh-s3-lit-full-wp3-contract-integration-assignment.md`

This is the durable handback for every terminal state. It must contain the
review identity, observed candidate identity, sources read, analysis against
all fourteen checks, ordered findings and counts, checks performed/not
performed, prohibited-action confirmation, and exactly one conclusion:

- `ACCEPTABLE FOR PETER'S EXPLICIT ACCEPTANCE — NO FINDINGS`;
- `ACCEPTABLE FOR PETER'S EXPLICIT ACCEPTANCE — OPTIONAL FINDINGS ONLY`;
- `REMEDIATION REQUIRED BEFORE ACCEPTANCE`; or
- `HARD STOP — CANDIDATE IDENTITY MISMATCH`.

State that the review neither adopts the proposed decisions nor accepts or
authorizes the candidate, and that Peter must accept its exact identity and
appoint Claude before execution.

## Current-state reconciliation

Before editing a pointer, preserve its exact pre-return bytes as:

1. `docs/review/Handover-information-through-2026-10-12-lit-full-wp3-contract-integration-assignment-preparation.md`;
2. `docs/project-management/status-through-2026-10-12-lit-full-wp3-contract-integration-assignment-preparation.md`;
3. `docs/implementation-plan-through-2026-10-12-lit-full-wp3-contract-integration-assignment-preparation.md`; and
4. `docs/operations/disposable-test-server-through-2026-10-12-lit-full-wp3-contract-integration-assignment-preparation.md`.

Add their SHA-256 values to the corresponding archive READMEs, without
overwriting or editing an existing snapshot. Reconcile only `docs/review/Handover
information`, `docs/project-management/status.md`, implementation-plan §20 and
the disposable-server restriction banner.

For no findings or optional-only findings, use:
`WP-3 CONTRACT-INTEGRATION ASSIGNMENT REVIEWED — PETER ACCEPTANCE AND CLAUDE APPOINTMENT PENDING`.

For a Blocking or Important finding, use:
`WP-3 CONTRACT-INTEGRATION ASSIGNMENT REVIEWED — REMEDIATION REQUIRED BEFORE ACCEPTANCE`.

For an identity mismatch, use:
`HARD STOP — WP-3 CONTRACT-INTEGRATION CANDIDATE IDENTITY MISMATCH`.

All pointers must link the durable review record and preserve the accepted WP-3
HARD STOP, open questions, operational restrictions and later gates.

## Operations and terminal states

Permitted: repository reads/searches; candidate identity and static Markdown/
link/table checks; read-only Git inspection; the one review record; four exact
snapshots; four archive-index rows; and four bounded pointer updates.

Prohibited: editing the candidate, interface contract, source-completion
record, accepted/historical evidence or existing snapshots; network, SSH,
hosts, retained evidence, secrets, `/etc`, `/proc`, `/sys`, packages, tests,
builds, formatters, hooks, implementation, application/configuration/
infrastructure edits, services, databases, cleanup, activation, rollback,
commit or push.

- `PASS`: identity matched and the complete review handback and reconciliation
  are written. This does not accept or authorize the candidate.
- `HARD STOP`: identity mismatch or an unreadable required source. Write the
  full handback and reconcile pointers before stopping.
- `INVALID RUN`: independence was compromised, a prohibited action occurred or
  the reviewed bytes cannot be established. Write the full handback, disclose
  the condition and reconcile pointers without a candidate verdict.

At the first terminal state, finish the durable handback and pointer
reconciliation, then stop. Do not remediate or execute the candidate.

## Exact invocation

Hand this assignment to Gemini exactly as:

`/goal Execute the active assignment in docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-contract-integration-gemini-review-prompt.md. Proceed autonomously through every authorized step in order until the defined terminal state (PASS, INVALID RUN, or HARD STOP). Do not post intermediate progress updates, do not yield turns for user confirmation on background tasks, and do not stop until the final handback and closing record are fully written.`
