# Claude assignment — LIT-FULL WP-3 source-completion R2 remediation

Date: 2026-10-11

Work ID: `C-P5.0-R5-RP11-H1-OH-S3-RT3-WP3-SC1-R2-20261011-25`

Status: **accepted and authorized for one Claude execution by Peter Duscha**

Executor: Claude

Independent reviewer after return: Codex

Decision owner: Peter Duscha, Product Owner and Acceptance Authority

## Authorization and objective

Peter authorizes Claude to execute this exact prompt once. Remediate exactly the
two Important findings `WP3-SC-R1-RE1` and `WP3-SC-R1-RE2` in the independent
Codex re-review of the WP-3 source-completion R1 return:

1. replace the falsely duplicated `v7.0.14` retrieval identities in the `v7.0`
   kernel manifest rows with a fresh, exact and independently reproducible
   comparison of the two tags; and
2. remove the remaining contradiction that says `uid` is optional in every
   Polkit `unix-process` form while also saying it is required in the pidfd form.

Correct the cumulative source-completion record in place and create a new R2
remediation handback. Do not edit the accepted R1-corrected WP-3 interface
contract. This remediation does not accept or integrate the source record,
close or reopen a Q3 question, answer Q6-6 or Q6-7, resolve residual `R-M.1`,
authorize WP-4 through WP-7, establish concrete Route 3 or select LIT-FULL.

## Required reading — binding precondition

Before the first deliverable edit, read every item below exactly as stated.
Items marked “completely” mean first byte through EOF in this execution. Earlier
reading, a search, excerpt, synopsis or memory does not satisfy this execution's
read.

1. `.agents/AGENTS.md`, completely;
2. the reading map and §§0, 3, 5, 12.0, the complete section headed
   `Phase 5 — Existing automation migration`, 13, 16, 17 and 20 of
   `docs/implementation-plan.md`;
3. `docs/review/Handover information`, completely;
4. the active restriction banner in
   `docs/operations/disposable-test-server.md`;
5. `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-record.md`, completely;
6. `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r1-remediation-claude-prompt.md`, completely;
7. `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r1-remediation-handback.md`, completely;
8. `docs/review/project-review-2026-10-11-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r1-remediation.md`, completely;
9. this exact prompt, completely; and
10. `docs/review/project-review-2026-10-11-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r2-remediation-acceptance-and-claude-activation.md`, completely.

Before the first edit, record each item's path or precisely named portion, line
count, byte count and SHA-256 in working notes. The R2 handback must contain the
complete ledger and state unambiguously that every item was read as specified
before the first edit. If any item or named section cannot be read as specified,
return `HARD STOP` before editing a deliverable. Do not guess another referent.

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
- residual `R-M.1` remains disclosed and undecided; and
- WP-4 through WP-7 remain separately gated and unauthorized.

Do not weaken any accepted failure, interruption, residual, cancellation,
unknown-effect, no-retry or fail-closed rule. A cancelled client wait is not
proof that a queued job stopped or that a mutating request had no effect.

## Authorized network research and scratch boundary

After the reading precondition is complete, authoritative network retrieval is
authorized only for the exact kernel.org repair described below.

1. Create one fresh mode-`0700` directory under `/tmp`. Put every download,
   command output and helper-script output there. Set any tool-specific home
   explicitly inside that directory.
2. Retrieve from the official kernel.org stable-tree cgit service the following
   six paths at **both** exact refs `v7.0` and `v7.0.14`:
   - `kernel/sys.c`;
   - `include/uapi/linux/utsname.h`;
   - `kernel/utsname_sysctl.c`;
   - `fs/proc/array.c`;
   - `fs/stat.c`; and
   - `fs/xattr.c`.
3. Retrieve the official kernel.org tag and commit pages for **both** exact refs
   `v7.0` and `v7.0.14`.
4. Record the full requested URL, any effective URL after redirect, UTC
   completion timestamp, exact byte count and full SHA-256 for every retrieved
   object. The query parameter must match the row label: `h=v7.0` for a `v7.0`
   row and `h=v7.0.14` for a `v7.0.14` row.
5. Compare each of the six file pairs byte for byte. If any pair differs, or if
   either tag/commit identity cannot be established exactly, return `HARD STOP`;
   do not preserve the old equality claim, substitute another ref or infer a
   result from matching sizes.
6. Do not re-download the Ubuntu archive keyring, Ubuntu release/index/package
   chain, Ubuntu kernel delta, systemd, Polkit or any other source. R1's
   completed trust-anchor remediation is not reopened, and `R-M.1` is not owned
   by this assignment.

Authoritative sources are limited to the official kernel.org stable-tree cgit
service for this retrieval. Pre-existing utilities may be invoked by ordinary
command name solely to download, hash, compare or statically read these objects.
Do not resolve or record their installed paths or versions and do not inspect
the installation that supplies them. Ordinary incidental runtime use of the
dynamic loader, shared libraries, DNS resolver configuration and TLS CA store
is permitted; it is not host evidence and may not support a finding.

## Absolute prohibition on host-installation inspection

Do not deliberately read or query local installation identity or state. In
particular, do not run `lsb_release`, `uname`, `hostnamectl`, `which`, `whereis`,
package-query commands or service commands; do not read `/usr/share/keyrings`,
`/etc`, `/proc`, `/sys`, installed binaries, installed package databases,
default GnuPG state, shell profiles or user configuration; and do not create or
modify anything under `~` or the executing user's home.

Repository reads and the single fresh `/tmp` directory are the only local
filesystem authorities. Do not SSH or connect to `oracle-test`, production,
staging, Foundry, a database, retained evidence or any other host/service.

If a tool attempts a side effect outside the repository or fresh `/tmp`
directory, stop that tool if possible, disclose the exact side effect and
return `HARD STOP`; do not clean it up unless this prompt explicitly created the
path inside `/tmp`.

## Required remediation — `WP3-SC-R1-RE1`

1. In §2.4 of the cumulative record, replace every `v7.0` file row that points
   to `h=v7.0.14` with the independently retrieved `h=v7.0` object's actual
   URL, timestamp, byte count and full SHA-256.
2. Do the same for the `v7.0` tag-page and commit-page rows. They must not reuse
   the `v7.0.14` retrieval identity.
3. Refresh the `v7.0.14` rows from this execution as the other side of the
   comparison. Do not combine two retrievals into one timestamp or checksum.
4. State the result of a byte-for-byte comparison for each of the six file
   pairs. Equality may be claimed only if all six comparisons succeed.
5. Re-check the §1 `KN` convention, §2.4 prose, A-12.2, A-15.2, Appendix E
   kernel provenance rows, Appendix F, the R2 handback and every summary that
   says the files are identical. Correct only what this retrieval establishes.
6. Preserve residual `R-M.1` exactly as a separate Ubuntu-kernel-delta
   authentication gap. This upstream tag correction neither closes nor weakens
   it.

## Required remediation — `WP3-SC-R1-RE2`

1. Rewrite the opening of A-10.6 so it says exactly that `uid` is optional in
   the general PID/start-time form and required in the pidfd form. It must not
   say or imply that `uid` is optional in every form.
2. Correct Appendix F's A-10.6 summary in the same way.
3. Search the complete cumulative record for every equivalent “optional in
   every form” statement and correct it when it purports to summarize the
   decoder.
4. Re-check R1.4, A-10.5, A-10.10, A-10.12, P-10.1, A-13.2, the DI-6 row, the
   Q3-5/Q3-6 readiness rows, Appendix A and O-5 for consistency. Do not select
   either request shape, amend H-PROC.5 or decide D-2/D-5.

## Deliverables

1. Correct cumulatively in place:
   `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-record.md`.
2. Create:
   `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r2-remediation-handback.md`.
3. Preserve the original source-completion prompt and handback, both independent
   reviews, the R1 prompt and handback, both activation records, the accepted
   interface contract, WP-2 inventory, accepted proposals/acceptances and every
   historical snapshot unchanged.
4. At terminal return, preserve the then-current four R2-authorization pointers
   in dated, verbatim `lit-full-wp3-source-completion-r2-remediation-authorization`
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
- `R-M.1` remains a disclosed residual for Peter and is not decided here.

## Allowed checks

Allowed checks are repository-only reads/searches; the exact bounded kernel.org
retrieval above; checksum, byte-comparison and source-identity verification
inside the fresh `/tmp` directory; link/path checks; `wc -l -c`; `sha256sum`;
mechanical Markdown-table parsing; `git diff --check`; and read-only Git
status/diff.

Do not run application or hook suites, builds, formatters or linters. They do
not establish these two documentation/source-manifest corrections and remain
outside this assignment.

## Handback requirements

The R2 handback must report:

- both findings and exactly how each was remediated;
- the complete pre-edit reading ledger;
- every old defective `v7.0` row and its corrected retrieval identity;
- the exact sixteen kernel.org requested URLs, any effective URLs, timestamps,
  byte counts and full SHA-256 values;
- all six byte-comparison results and both tags' tag/commit identities;
- every changed Polkit statement;
- record and handback paths, line counts, byte counts and full SHA-256 where
  non-self-referential;
- every file created and edited;
- exact checks and results and checks not run with reasons;
- confirmation that the accepted interface contract is byte-identical;
- confirmation that no host-installation or prohibited path was inspected;
- any attempted side effect outside the allowed paths;
- all unresolved questions and decisions, including unchanged `R-M.1`; and
- focused questions for Codex's independent re-review.

## Prohibited operations

Do not access secrets, credentials, player data, retained evidence, production,
staging, `oracle-test`, Foundry or a database. Do not inspect a host
installation, install or update packages, execute downloaded project code, edit
application code, tests, hooks, configuration or infrastructure, implement a
client or launcher, build, test, format, operate a service/database, recreate
the workspace, perform OH-S4/OH-S4p or later work, H-1/H-2, activation,
rollback, commit or push.

Do not prepare or authorize WP-4 through WP-7. The R5 and H-0G retained paths
remain untouched pending separately gated LC-3 through LC-5 authority.

## Terminal state and current-state wording

On successful remediation, the handback and four current-state pointers must
say exactly:

`WP-3 SOURCE COMPLETION R2 REMEDIATION RETURNED — INDEPENDENT CODEX RE-REVIEW PENDING`

Return `HARD STOP` instead if any reading cannot be completed, a `v7.0` or
`v7.0.14` object cannot be retrieved and identified exactly, any of the six
file pairs differs, a manifest fact remains too ambiguous to classify, a source
conflict requires Peter's decision, or a tool touches a prohibited path. Record
the exact reason and make the current-state pointers consistent.

Either terminal state preserves the accepted WP-3 HARD STOP and all fixed
boundaries. Neither state accepts the evidence record, authorizes contract
integration or releases successor work. Codex must independently re-review the
cumulative return, after which Peter retains the acceptance decision.

## Exact invocation

Execute exactly:

```text
Execute the exact accepted assignment in docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r2-remediation-claude-prompt.md once. Proceed autonomously through every authorized repository-and-primary-source step until the prompt-defined terminal state. Use only the repository and one fresh /tmp research directory; do not inspect any host installation or prepare WP-4 through WP-7. Write the complete cumulative record, R2 handback and current-state return before stopping.
```
