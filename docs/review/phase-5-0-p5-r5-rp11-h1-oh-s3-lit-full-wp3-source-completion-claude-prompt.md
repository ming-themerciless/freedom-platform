# Proposed Claude assignment — LIT-FULL WP-3 source completion

Date: 2026-10-10

Proposed work ID: `C-P5.0-R5-RP11-H1-OH-S3-RT3-WP3-SC1-20261010-23`

Status: **prepared under Peter's source-completion direction; exact prompt not
yet accepted, assigned or executable**

Proposed executor: Claude

Proposed independent reviewer: Codex

## Objective

Produce a version-bound, primary-source evidence record addressing the exact
unsupported facts `UF-01` through `UF-14` in the accepted WP-3 interface
contract, and a separately classified proposal for the direct acquisition
mechanisms represented by `UF-15` through `UF-18`.

This is a source-completion and proposal slice inside WP-3. It is not WP-4 and
does not implement, select or authorize the loader-free client, a static image,
a parser, a process-creation mechanism or a syscall sequence. It does not edit
the accepted R1-corrected interface contract. Its output becomes an authorized
source only after independent Codex review and Peter Duscha's later acceptance.

## Required reading — binding precondition

Before the first deliverable edit, read each item below as specified and record
its path, line count, byte count and SHA-256 in working notes. The handback must
contain the complete ledger and state unambiguously that the required reading
was completed before the first edit.

1. `.agents/AGENTS.md`, completely;
2. the reading map and §§0, 3, 5, 12.0, 12.5, 13, 16, 17 and 20 of
   `docs/implementation-plan.md`;
3. `docs/review/Handover information`, completely;
4. the active restriction banner in
   `docs/operations/disposable-test-server.md`;
5. `docs/review/project-review-2026-10-10-p5-r5-rp11-h1-oh-s3-lit-full-wp3-r1-remediation-acceptance.md`, completely;
6. `docs/review/project-review-2026-10-10-p5-r5-rp11-h1-oh-s3-lit-full-wp3-r1-remediation.md`, completely;
7. `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-interface-contract.md`, completely;
8. `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-r1-remediation-handback.md`, completely;
9. `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-r1-remediation-claude-prompt.md`, completely;
10. `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s2-r2-citations.md`, completely;
11. `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp2-operation-inventory.md`, completely;
12. §§7.5, 7.5a, 8.1 and 9.3 of
    `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-r8-remediation-proposal.md`;
13. the accepted baseline/property/acquisition passages cited by C-24 through
    C-26 and `UF-15` through `UF-18` in
    `docs/review/phase-5-0-p5-r5-rp11-h1-oracle-test-one-host-design-amendment-proposal.md`;
14. `docs/review/project-review-2026-10-07-p5-r5-rp11-h1-oh-s3-r8-acceptance.md`, completely;
15. `docs/review/project-review-2026-10-06-p5-r5-rp11-h1-oh-s2-r2-acceptance.md`, completely;
16. `docs/review/project-review-2026-10-09-p5-r5-rp11-h1-oh-s3-lit-full-wp2-acceptance.md`, completely;
17. `docs/review/project-review-2026-10-10-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-direction.md`, completely; and
18. this exact prompt, completely.

If an item cannot be read as specified, return `HARD STOP` before editing a
deliverable. Earlier reading or a generated synopsis does not replace this
execution's reading.

## Fixed accepted boundary

Preserve without reinterpretation:

- baseline v1.8;
- LIT-FULL under R3-ROOT remains a readiness investigation and is not selected
  for implementation;
- concrete Route 3 remains unestablished;
- in scope remain exactly RT-1 through RT-5, SA-1 (`start`) and SA-2 (`stop`);
- F-1 remains B2-F, both lifecycle acts remain in and B3-OUT remains effective;
- EX-1 and EX-2 remain effective only for their accepted uses; no EX-3 exists;
- no dynamic child or distribution executable is admitted beneath a first
  design-controlled root image;
- DI-6 remains the only retained replacement-child intent;
- H-1, RB-1, RS-1 and H-1R remain outside the set;
- Q6-6 and Q6-7 remain unanswered;
- BC-2 remains a later WP-9 decision; and
- WP-4 through WP-7 remain separately gated and unauthorized.

Do not weaken an accepted failure, interruption, residual, cancellation,
unknown-effect, no-retry or fail-closed rule. A cancelled client wait is not
proof that a queued job stopped or that a mutating request had no effect.

## Authorized external research

After the reading precondition is complete, authoritative network research is
authorized only for the objective above. Use primary sources:

1. the exact Ubuntu source packages corresponding to systemd
   `259.5-0ubuntu3.4` and polkit `127-2ubuntu1.1`, including Ubuntu/Launchpad
   package metadata and distro patches;
2. the matching upstream systemd and polkit repositories or release material,
   only to explain or cross-check the exact Ubuntu source and never to replace
   a distro-patched fact silently;
3. official D-Bus specifications and official project API documentation;
4. authoritative Linux kernel, libc/POSIX, NSS, Git-format and Ubuntu/dpkg
   specifications or source needed to assess `UF-15` through `UF-18`; and
5. official licensing and checksum metadata needed to identify those sources.

Do not rely on blogs, tutorials, Stack Overflow, forum posts, AI-generated
summaries, package-index aggregators or uncited memory. Secondary sources may be
used only to locate a primary source and may not support a result.

Downloads, if needed, must be confined to a fresh temporary directory under
`/tmp`. Record each authoritative URL, retrieval time, source/package version,
upstream tag or commit where applicable, archive checksum and the exact source
file, symbol and line range used. Do not vendor downloaded source into the
repository. Do not install packages, execute downloaded code, build source or
inspect a host installation.

If the exact Ubuntu source for either pinned package cannot be authenticated,
do not substitute a nearby version: record the precise gap and return
`HARD STOP`.

## Fact and proposal discipline

Keep these classes distinct:

- `ASF`: authoritative source fact, supported by an exact primary-source
  citation and bound to the applicable version;
- `MD`: mechanical derivation from cited `ASF` facts;
- `DR`: already accepted design requirement from the repository;
- `PSC`: proposed source-completion mechanism for Peter's later decision;
- `UF`: fact still unsupported after the authorized research.

A `PSC` is not an accepted fact and cannot close a question until independently
reviewed and accepted. Do not convert a candidate API, library facility, file
format or operating-system facility into a selected implementation mechanism.

## Required research coverage

### `UF-01` through `UF-14`

For every identifier, provide a row that:

1. quotes the exact accepted missing-fact statement without broadening it;
2. identifies every authoritative source examined;
3. states the supported fact with exact types, value forms and error or
   completion behavior where the source establishes them;
4. distinguishes manager/server behavior from the client contract;
5. records version applicability and distro-patch effects;
6. maps the result to the affected DI and Q3 identifiers;
7. states `supported`, `partially supported` or `unsupported`; and
8. names every residual gap exactly.

The record must specifically cover:

- system-bus addressing/authentication and D-Bus message framing;
- unit-name to object-path resolution, including unloaded units;
- property signatures and typed-to-text dependencies for DI-1/Q3-9;
- D-Bus error representation and proposed result mapping without turning that
  mapping into an accepted fact;
- job creation, observation, completion, cancellation, abandonment,
  disconnection and eventual-effect observation for DI-2, DI-3, DI-4 and DI-S;
- `StartTransientUnit` and `StopUnit` signatures, modes, property structures,
  timer/service relationships and already-inactive/not-loaded behavior;
- Polkit `CheckAuthorization`, process-subject, flags, details, cancellation and
  result-field contracts; and
- process-subject start-time units/encoding and validation behavior.

Do not answer Q6-6 or Q6-7 while researching cancellation or unknown effects.
The accepted `DR`/`PO3` split remains unchanged unless a later reviewed and
accepted record changes it.

### `UF-15` through `UF-18`

For each identifier, provide:

1. authoritative facts about available direct sources or stable formats;
2. one or more `PSC` mechanism candidates, with prerequisites and failure
   behavior stated abstractly;
3. whether each candidate is compatible in principle with the accepted
   loader-free/no-distribution-child boundary;
4. every version, portability, NSS, worktree, package-database, race or
   consistency limitation;
5. the exact later decision Peter would need to make; and
6. the WP-4 details deliberately left undesigned.

Do not choose a programming language, client library, parser implementation,
system-call sequence, static-image architecture, buffer size, retry algorithm
or process-creation mechanism. For `UF-17`, preserve the distinction between
facts that are re-read and facts carried from the accepted record; do not decide
that boundary unless existing accepted text already does.

## Deliverables

Create exactly:

1. `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-record.md`;
2. `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-handback.md`.

Do not edit the accepted R1-corrected interface contract, its handbacks,
reviews, acceptances, the WP-2 inventory, earlier prompts, historical snapshots,
application code, tests, configuration or infrastructure.

The source-completion record must include:

1. scope, boundary, source hierarchy and class definitions;
2. an authoritative-source manifest;
3. the complete `UF-01` through `UF-14` evidence matrix;
4. the complete `UF-15` through `UF-18` fact-and-proposal matrix;
5. a cancellation/completion reconciliation for all seven interfaces;
6. a Q3 readiness table that says what could close after acceptance and what
   remains blocked, without itself closing a Q3 question;
7. residual unsupported facts with exact owners;
8. explicit answers to the independent review questions listed below; and
9. a recommendation for Peter, clearly separated from evidence.

The handback must report:

- the required-reading ledger;
- research sources, URLs, retrieval times, versions and checksums;
- every `UF` disposition and residual gap;
- proposed mechanisms and decisions required for `UF-15` through `UF-18`;
- deliverable line, byte and SHA-256 identities where non-self-referential;
- files created and edited;
- exact checks and results, and checks not run with reasons;
- confirmation that no prohibited operation occurred; and
- focused questions for Codex's independent review.

## Independent review questions

The returned record must make it possible for Codex to answer:

1. Are the exact pinned Ubuntu sources authenticated and are distro patches
   accounted for?
2. Does every `ASF` state only what its cited primary source establishes?
3. Does the record distinguish server behavior, wire/API contract, proposed
   outcome mapping and implementation choice?
4. Are job completion and client-wait/job cancellation semantics complete for
   DI-2, DI-3, DI-4 and DI-S without deciding Q6-6 or Q6-7?
5. Are DI-5 and DI-6 subject/cancellation facts complete without conflation?
6. Are every `PSC` and every residual `UF` classified honestly?
7. Do the `UF-15` through `UF-18` proposals stay above WP-4 implementation
   mechanics and preserve the accepted boundary?
8. Is the Q3 readiness assessment complete, internally consistent and safe for
   a later contract-integration decision?

## Allowed checks

Allowed checks are repository-only reads and searches; authoritative web/source
retrieval within the scope above; checksum and source-identity verification;
link/path checks; `wc -l -c`; `sha256sum`; mechanical Markdown-table parsing;
`git diff --check`; and read-only Git status/diff.

Do not run application or hook suites, builds, formatters or linters. They do
not establish source facts and are outside this documentation/research slice.

## Prohibited operations

Do not use SSH or connect to any host. Do not access retained evidence, secrets,
credentials, player data, production, staging, `oracle-test`, Foundry or a
database. Do not install or update packages, execute downloaded code, edit
configuration or infrastructure, implement a client or launcher, build, test,
format, operate a service/database, clean up existing paths, recreate a
workspace, perform OH-S4/OH-S4p or later work, H-1/H-2, activation, rollback,
commit or push.

The R5 and H-0G retained paths remain untouched pending separately gated LC-3
through LC-5 authority. WP-4 through WP-7 must not be prepared or authorized.

## Return and current-state handling

Before replacing the four current-state pointers, preserve their exact
source-completion-authorization state in dated snapshots beside the canonical
files and add each SHA-256 to its archive index. Do not rewrite an earlier
snapshot.

Then update only:

1. `docs/review/Handover information`;
2. `docs/project-management/status.md`;
3. implementation-plan §20; and
4. the restriction banner in
   `docs/operations/disposable-test-server.md`.

On a complete return, the pointers and handback must say:

`WP-3 SOURCE COMPLETION RETURNED — INDEPENDENT CODEX REVIEW PENDING`

If an exact pinned source cannot be authenticated, a required fact remains too
ambiguous to classify, or a source conflict cannot be resolved without a
maintainer decision, return `HARD STOP` with the precise reason. In either case,
the accepted WP-3 HARD STOP remains in force.

This return does not accept the source record, modify the accepted interface
contract, authorize WP-4, establish concrete Route 3 or select LIT-FULL. Codex
must independently review the cumulative return, and Peter must later decide
acceptance before any contract integration or successor assignment.

## Invocation after exact acceptance

Execute exactly:

```text
Execute the exact accepted assignment in docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-claude-prompt.md. Proceed autonomously through every authorized repository-and-primary-source-research step until the prompt-defined terminal state. Do not access any host or retained evidence, do not edit the accepted interface contract, and do not prepare WP-4 through WP-7. Write the complete durable source record, handback and current-state return before stopping.
```
