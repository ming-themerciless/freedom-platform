# Claude assignment — LIT-FULL WP-3 source-completion R1 remediation

Date: 2026-10-10

Work ID: `C-P5.0-R5-RP11-H1-OH-S3-RT3-WP3-SC1-R1-20261010-24`

Status: **accepted and authorized for one Claude execution by Peter Duscha**

Executor: Claude

Independent reviewer after return: Codex

Decision owner: Peter Duscha, Product Owner and Acceptance Authority

## Authorization and objective

Peter authorizes Claude to execute this exact prompt once. Remediate exactly the
four findings `WP3-SC-R1` through `WP3-SC-R4` in the independent Codex review of
the WP-3 source-completion return:

1. replace the impossible original "§12.5" reading precondition with a fresh,
   unambiguous cumulative reading basis;
2. repeat the Ubuntu source authentication without inspecting or relying on an
   installed host keyring or any other host-installation state;
3. make the authoritative-source manifest exact and independently reproducible;
   and
4. correct the contradictory Polkit `unix-process` `uid` statement.

Correct the cumulative source-completion record in place and create a new R1
remediation handback. Do not edit the accepted R1-corrected WP-3 interface
contract. This remediation does not accept or integrate the source record,
close a Q3 question, answer Q6-6 or Q6-7, authorize WP-4 through WP-7,
establish concrete Route 3 or select LIT-FULL.

## Peter's clarifications and trust-anchor decision

These decisions are part of this accepted remediation authority:

1. The original prompt's nonexistent "§12.5" meant the complete section headed
   `Phase 5 — Existing automation migration` under implementation-plan §12,
   currently beginning at line 1634 and ending immediately before §13. The
   heading, not the present line numbers, controls.
2. For this remediation, Peter pins the expected Ubuntu Archive Automatic
   Signing Key (2018) fingerprint exactly as
   `F6ECB3762474EDA9D21B7022871920D1991BC93C`.
3. Peter authorizes retrieval of
   `https://archive.ubuntu.com/ubuntu/project/ubuntu-archive-keyring.gpg` into
   the fresh `/tmp` research directory. That downloaded object may be used as
   the trust-anchor container only if an offline fingerprint listing made from
   that exact downloaded file contains the pinned fingerprint above and the
   signature verification reports that exact fingerprint. Record its complete
   URL, retrieval time, byte size and full SHA-256.
4. The `.dsc` uploader signatures are not required for this assignment. Do not
   fetch an uploader key merely to verify them. Authentication succeeds only
   through the pinned Ubuntu archive-key fingerprint, signed `InRelease`,
   authenticated `Sources.xz` hashes and exact source-file hashes.

These decisions repair the prompt defect and define the trust anchor; they do
not accept any source fact or implementation mechanism.

## Required reading — binding precondition

Before the first deliverable edit, read every item below exactly as stated.
Items marked "completely" mean first byte through EOF. Earlier reading, a
search, excerpt, synopsis or memory does not satisfy this execution's read.

1. `.agents/AGENTS.md`, completely;
2. the reading map and §§0, 3, 5, 12.0, the complete section headed
   `Phase 5 — Existing automation migration`, 13, 16, 17 and 20 of
   `docs/implementation-plan.md`;
3. `docs/review/Handover information`, completely;
4. the active restriction banner in
   `docs/operations/disposable-test-server.md`;
5. `docs/review/project-review-2026-10-10-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-acceptance-and-claude-activation.md`, completely;
6. `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-claude-prompt.md`, completely;
7. `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-record.md`, completely;
8. `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-handback.md`, completely;
9. `docs/review/project-review-2026-10-10-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion.md`, completely;
10. `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-interface-contract.md`, completely;
11. `docs/review/project-review-2026-10-10-p5-r5-rp11-h1-oh-s3-lit-full-wp3-r1-remediation-acceptance.md`, completely;
12. `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s2-r2-citations.md`, Appendix D completely and only other passages directly cited by the source-completion record;
13. `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp2-operation-inventory.md`, the `UF-01` through `UF-18`, Q3 and baseline-acquisition passages cited by the source-completion record;
14. this exact prompt, completely; and
15. `docs/review/project-review-2026-10-10-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r1-remediation-acceptance-and-claude-activation.md`, completely.

Before the first edit, record each item's path or precisely named portion, line
count, byte count and SHA-256 in working notes. The R1 handback must contain the
complete ledger and state unambiguously that every item was read as specified
before the first edit.

If any item or named section cannot be read as specified, return `HARD STOP`
before editing a deliverable. Do not guess another referent.

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
- BC-2 remains a later WP-9 decision; and
- WP-4 through WP-7 remain separately gated and unauthorized.

Do not weaken any accepted failure, interruption, residual, cancellation,
unknown-effect, no-retry or fail-closed rule. A cancelled client wait is not
proof that a queued job stopped or that a mutating request had no effect.

## Authorized network research and scratch boundary

After the reading precondition is complete, authoritative network retrieval is
authorized only to repeat and repair the source authentication and manifest
work described here.

1. Create one fresh mode-`0700` directory under `/tmp`. Put every download,
   extracted source, keyring, GnuPG home/keybox, command output and helper-script
   output there. Set any tool-specific home explicitly inside that directory.
2. Retrieve the official Ubuntu archive keyring URL and verify the pinned
   fingerprint exactly as Peter decided above. Do not use a keyserver, Web of
   Trust, installed keyring, default GnuPG home or uploader key.
3. Re-retrieve the exact `resolute`, `resolute-updates` and
   `resolute-security` `InRelease` and `Sources.xz` objects required for the
   chain. Verify each signature against the downloaded keyring and require the
   exact pinned signing fingerprint.
4. Re-retrieve the exact six systemd `259.5-0ubuntu3.4` and policykit-1
   `127-2ubuntu1.1` source-package files. Verify their sizes and full SHA-256
   values against the authenticated source indexes.
5. Re-retrieve only the other authoritative objects needed to replace a missing
   exact URL, retrieval time, full checksum or locator in the manifest. Do not
   broaden the research or add new substantive facts.
6. Authoritative sources remain limited to official Ubuntu/Launchpad archives,
   the official upstream project repositories, official D-Bus material and the
   authoritative kernel/libc/POSIX/NSS/Git/dpkg sources already within the
   original assignment. Secondary sources may locate but may not support a
   result.

Pre-existing utilities may be invoked by their ordinary command names solely
to download, hash, unpack, patch or statically read the authorized objects. Do
not resolve or record their installed paths or versions and do not inspect the
installation that supplies them. Ordinary incidental runtime use of the
system's dynamic loader, shared libraries, DNS resolver configuration and TLS
CA store is permitted; it is not host evidence and may not support a finding.

## Absolute prohibition on host-installation inspection

Do not deliberately read or query local installation identity or state. In particular, do
not run `lsb_release`, `uname`, `hostnamectl`, `which`, `whereis`, package-query
commands or service commands; do not read `/usr/share/keyrings`, `/etc`, `/proc`,
`/sys`, installed binaries, installed package databases, default GnuPG state,
shell profiles or user configuration; and do not create or modify anything
under `~` or the executing user's home.

Repository reads and the single fresh `/tmp` directory are the only local
filesystem authorities. Do not SSH or connect to `oracle-test`, production,
staging, Foundry, a database, retained evidence or any other host/service.

If a tool attempts a side effect outside the repository or fresh `/tmp`
directory, stop that tool if possible, disclose the exact side effect and
return `HARD STOP`; do not clean it up unless this prompt explicitly created the
path inside `/tmp`.

## Required remediation — `WP3-SC-R1`

1. Preserve the original accepted prompt and original handback unchanged as
   historical evidence.
2. State in the cumulative record and new handback that the original prompt's
   §12.5 reference was defective and that the original normal return did not
   satisfy its literal stop rule.
3. State Peter's clarification that the intended section was the complete
   `Phase 5 — Existing automation migration` section.
4. Use the fresh reading ledger from this execution as the cumulative record's
   valid pre-edit reading basis. Do not claim retroactive compliance by the
   original execution.

## Required remediation — `WP3-SC-R2`

1. Replace reliance on `/usr/share/keyrings/ubuntu-archive-keyring.gpg` with the
   downloaded `/tmp` keyring and Peter-pinned fingerprint route above.
2. Record the exact keyring URL, retrieval timestamp, byte count, full SHA-256,
   all fingerprints present or an exact bounded fingerprint listing, and the
   exact fingerprint that verified each `InRelease` signature.
3. Record the exact full URLs, timestamps, byte counts and full SHA-256 values
   for each `InRelease`, `Sources.xz` and source-package file.
4. State precisely what the chain proves and does not prove. The unavailable
   uploader keys remain a disclosed non-dependency, not a substitute stop.
5. Remove or correct every statement that says no host was inspected without
   acknowledging the original execution's disclosed prohibited inspection.
   Distinguish that historical fact from this remediation, which must perform
   none.
6. If the downloaded keyring lacks the pinned fingerprint, a signature reports
   another fingerprint, or any size/hash differs from the authenticated index,
   return `HARD STOP`; do not substitute another key, mirror, package version or
   nearby source version.

## Required remediation — `WP3-SC-R3`

Audit the complete manifest and every source citation. For every authoritative
object actually relied on, record:

- the full, non-abbreviated URL;
- UTC retrieval timestamp;
- exact version, tag and commit where applicable;
- byte count and full SHA-256 without ellipses;
- archive member or extracted relative path;
- exact symbol/section and line range used; and
- whether the cited lines are upstream, Ubuntu-patched or unchanged by the
  Ubuntu patch series.

Where a stable specification is HTML or a manual without useful source line
numbers, record its exact named section and a content anchor sufficient to find
the cited passage; do not invent line precision. Preserve the existing source
hierarchy and static-reading limitation.

Re-check every abbreviated URL and truncated checksum in §2. Ensure the new R1
handback itself contains or links unambiguously to the complete manifest and
does not claim that missing data is present.

## Required remediation — `WP3-SC-R4`

Correct A-10.5 and all dependent summaries so that they distinguish:

- the general polkit 127 `unix-process` PID/start-time form, where `pid` and
  `start-time` are required and `uid` is optional;
- the pidfd form, where this version requires `pidfd` and `uid`; and
- the `pkcheck`-equivalent `PSC` candidate, which deliberately supplies `pid`,
  `start-time` and `uid`.

Re-check A-10.6, A-10.10, P-10.1, A-12.x, A-13.x, DI-5/DI-6 reconciliation and
the Q3-5/Q3-6 readiness rows for consistency. Do not select either request
shape, amend H-PROC.5, or decide D-2/D-5.

## Deliverables

1. Correct cumulatively in place:
   `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-record.md`.
2. Create:
   `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r1-remediation-handback.md`.
3. Preserve the original prompt, original handback, independent review,
   activation record, accepted interface contract, WP-2 inventory, accepted
   proposals/acceptances and every historical snapshot unchanged.
4. At terminal return, preserve the then-current four R1-authorization pointers
   in dated, verbatim `lit-full-wp3-source-completion-r1-remediation-authorization`
   snapshots beside the canonical files, add each full SHA-256 to its archive
   index, then update only:
   - `docs/review/Handover information`;
   - `docs/project-management/status.md`;
   - implementation-plan §20; and
   - the restriction banner in
     `docs/operations/disposable-test-server.md`.

Do not integrate the evidence into the accepted interface contract.

## Fact, proposal and closure discipline

- Preserve `ASF`, `MD`, `DR`, `PSC` and residual `UF` as distinct classes.
- An `ASF` must say only what its exact primary source establishes.
- An absence finding remains expressly labelled as such.
- A reference-client behavior is not a wire or server contract.
- A `PSC` remains a proposal and selects no API, parser, library, language,
  syscall sequence, process-creation mechanism, retry algorithm, static-image
  architecture or buffer size.
- No Q3 question is closed or reopened by this remediation. Preserve Q3-11's
  existing fail-closed record while stating that no acquisition mechanism is
  selected.
- Q6-6 and Q6-7 remain unanswered.
- D-1 through D-14 remain proposals for Peter's later decision unless already
  accepted by a separate record; this assignment accepts none.

## Allowed checks

Allowed checks are repository-only reads/searches; the bounded network
retrieval above; checksum, signature and source-identity verification inside
the fresh `/tmp` directory; archive unpacking and distro-patch application
inside that directory; link/path checks; `wc -l -c`; `sha256sum`; mechanical
Markdown-table and citation-range parsing; `git diff --check`; and read-only Git
status/diff.

Do not run application or hook suites, builds, formatters or linters. They do
not establish source facts and remain outside this documentation/research
remediation.

## Handback requirements

The R1 handback must report:

- all four findings and exactly how each was remediated;
- the complete pre-edit reading ledger;
- Peter's §12.5 clarification and pinned trust-anchor decision;
- the complete authentication chain and manifest corrections;
- every changed `ASF`, `MD`, `PSC`, residual and Q3-readiness statement;
- record and handback paths, line counts, byte counts and full SHA-256 where
  non-self-referential;
- every file created and edited;
- exact checks and results and checks not run with reasons;
- confirmation that the accepted interface contract is byte-identical;
- confirmation that no host-installation or prohibited path was inspected;
- any attempted side effect outside the allowed paths;
- all unresolved questions and decisions; and
- focused questions for Codex's independent re-review.

## Prohibited operations

Do not access secrets, credentials, player data, retained evidence, production,
staging, `oracle-test`, Foundry or a database. Do not inspect a host
installation, install or update packages, execute downloaded project code,
edit application code, tests, hooks, configuration or infrastructure, implement
a client or launcher, build, test, format, operate a service/database, recreate
the workspace, perform OH-S4/OH-S4p or later work, H-1/H-2, activation,
rollback, commit or push.

Do not prepare or authorize WP-4 through WP-7. The R5 and H-0G retained paths
remain untouched pending separately gated LC-3 through LC-5 authority.

## Terminal state and current-state wording

On successful remediation, the handback and four current-state pointers must
say exactly:

`WP-3 SOURCE COMPLETION R1 REMEDIATION RETURNED — INDEPENDENT CODEX RE-REVIEW PENDING`

Return `HARD STOP` instead if any reading cannot be completed, the trust anchor
or exact source chain cannot be authenticated, a manifest fact remains too
ambiguous to classify, a source conflict requires Peter's decision, or a tool
touches a prohibited path. Record the exact reason and make the current-state
pointers consistent.

Either terminal state preserves the accepted WP-3 HARD STOP and all fixed
boundaries. Neither state accepts the evidence record, authorizes contract
integration or releases successor work. Codex must independently re-review the
cumulative return, after which Peter retains the acceptance decision.

## Exact invocation

Execute exactly:

```text
Execute the exact accepted assignment in docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r1-remediation-claude-prompt.md once. Proceed autonomously through every authorized repository-and-primary-source step until the prompt-defined terminal state. Use only the repository and one fresh /tmp research directory; do not inspect any host installation or prepare WP-4 through WP-7. Write the complete cumulative record, R1 handback and current-state return before stopping.
```
