# Claude prompt — Route 3 release-record preparation review remediation

Peter authorizes this bounded documentation correction after Codex's review of
`docs/review/route-3-release-record-preparation-claude-prompt.md` found one
blocking archive-proof gap. Correct that prompt and return the corrected
documentation for independent Codex re-review.

This assignment does **not** authorize execution of the release-preparation
prompt. Do not access production or staging, run S0.0 or any other runbook
block, contact package archives, create release artifacts, populate block F,
change tests or current-state records, commit, push, provision, install,
activate, migrate, cut over or run RB-1. The Route 3 plan remains **NO-GO**.

## Governing context

Before editing, read completely:

1. `.agents/AGENTS.md`;
2. the reading map and §§0, 13, 14, 16, 17 and 20 of
   `docs/implementation-plan.md`;
3. `docs/review/Handover information`;
4. `docs/operations/disposable-test-server.md`;
5. runbook part P, especially P.3, block D, block F, S0.2 and S1.2 in
   `docs/operations/executor-supervisor-provisioning-runbook.md`;
6. `docs/review/route-3-release-record-preparation-claude-prompt.md`; and
7. Codex's finding below.

Treat the governing documents as authority. Preserve every unrelated working-
tree change. Never read or inspect `.env`, credentials, tokens, cloud or agent
state, process environments, process argument lists, secrets or player data.

## Finding to remediate

The release-preparation prompt currently permits the generated archive to be
verified using either the runbook's staging-entry archive contract **or its
accepted focused tests**. The focused tests construct their own archive
fixtures and can pass without reading the retained `code.tar` and
`MANIFEST.sha256`. They therefore cannot prove that the retained artifacts
whose digests populate block F have the required member types, file set and
content.

This is blocking because S0.2 checks artifact type, custody and field digests
but does not execute the structural archive validator. If malformed retained
artifacts reached production, their first structural rejection would be S1.2,
after S1.1 had installed and held the Python package closure. Rollback could
then stop at the accepted status-28 attended package/hold recovery boundary.

## Required correction

Edit only
`docs/review/route-3-release-record-preparation-claude-prompt.md`, apart from
this supplied remediation prompt remaining in the working tree.

Replace the alternative proof at the archive-production step with an explicit,
mandatory validation of the **actual retained artifact pair**. The corrected
prompt must require all of the following:

1. Run the accepted `ROUTE3_STAGE_ENTRY` `archive` command from block D against
   the exact retained `code.tar` and `MANIFEST.sha256` whose SHA-256 values will
   populate block F. Do this on `oracle-test`, from the exact accepted release
   revision, using the documented isolated Python invocation. Do not merely
   reimplement or paraphrase the validator.
2. Require the validator to return status 0 and print its success result before
   either digest may be accepted. A non-zero, missing or ambiguous result is a
   NO-GO: leave block F unchanged and make no release-record commit.
3. Make clear that the validator proves the archive contains exactly the
   manifest's regular-file set and digests, with no links, special files,
   duplicate or prohibited members, or other contract violation enforced by
   the accepted staging entry.
4. Keep the provisioning-plan focused tests as additional regression evidence,
   never as a substitute for validating those retained files.
5. Add the same artifact-bound validator result to the final-tree validation
   checklist and to the required handback evidence, including the retained
   artifact paths, invocation, status and success result.
6. Preserve the original prompt's immutable release revision, archive pathspec,
   production authority boundary, secret exclusions, NO-GO behavior,
   independent-review requirement and all other instructions unchanged.

Do not broaden this correction into a new artifact design, test implementation,
runbook change, release-field change or production procedure. If the accepted
block-D validator cannot be invoked against the retained pair exactly as
required, stop and report that conflict rather than inventing a substitute.

## Validation and return

Perform documentation-only checks:

- inspect the resulting diff and confirm it changes only the original prompt
  plus this supplied remediation prompt;
- `git diff --check`, including an explicit whitespace check for untracked
  files;
- confirm the corrected text contains no remaining path that lets focused
  tests replace validation of the retained artifact pair; and
- confirm no authority text now permits production/staging access or execution
  during this remediation.

Do not run behavioral suites for this documentation-only correction. Do not
commit or push. Return the complete uncommitted two-prompt candidate for
independent Codex re-review, with a concise summary of the exact wording
changed and the documentation checks actually run and their statuses.
