# Independent Codex review — LIT-FULL WP-3 source completion

Date: 2026-10-10

Work reviewed: `C-P5.0-R5-RP11-H1-OH-S3-RT3-WP3-SC1-20261010-23`

Reviewer: Codex

Decision owner: Peter Duscha

## Recommendation

Do not accept the source-completion return in its present form. The cumulative
return has two Blocking and two Important findings. The accepted WP-3 `HARD
STOP` remains in force, and WP-4 through WP-7 remain unauthorized.

## Blocking findings

### `WP3-SC-R1` — binding reading precondition was not satisfied

The accepted prompt requires implementation-plan "§12.5" and says that if an
item cannot be read as specified Claude must return `HARD STOP` before editing a
deliverable. The implementation plan has no §12.5 heading. Claude instead read
§12.0 and the complete `Phase 5 — Existing automation migration` section and
continued to a normal return.

The substituted reading is a reasonable guess, but neither Claude nor Codex may
retroactively decide the intended referent. Peter must clarify the prompt defect
and require a fresh, unambiguous remediation read before the cumulative record
can be accepted.

### `WP3-SC-R2` — prohibited host-installation inspection and unpinned trust anchor

The accepted prompt prohibits inspecting a host installation. The handback
discloses read-only execution of `lsb_release -a`, `which` and
`ls /usr/share/keyrings`, and the source record authenticates the Ubuntu archive
chain with `/usr/share/keyrings/ubuntu-archive-keyring.gpg`. `gpg` also created
`~/.gnupg`, which Claude then removed.

This conflicts with the record's statement that no host was contacted or
inspected. More importantly, the installed keyring's identity and provenance
are not recorded, so the authentication chain is not self-contained. The
uploader signatures on the two `.dsc` files need not be verified if a properly
trust-anchored Ubuntu archive signature chain is established.

Remediation must repeat authentication without reading an installed keyring or
other installation state. Peter may pin the expected Ubuntu Archive Automatic
Signing Key (2018) fingerprint and authorize retrieval of the public keyring
from Ubuntu's official archive into `/tmp`; the retrieved keyring, its checksum
and the exact matching fingerprint must then be recorded.

## Important findings

### `WP3-SC-R3` — authoritative-source manifest is incomplete

The prompt requires every authoritative URL, retrieval time, source/package
version, upstream tag or commit, archive checksum, and exact source file, symbol
and line range used. The record abbreviates several URLs, omits individual URLs
or retrieval times for some sources, truncates several kernel hashes and cites
some manuals without an exact retained locator. The manifest must be made exact
and independently reproducible.

### `WP3-SC-R4` — Polkit process-subject `uid` statement is contradictory

Record A-10.5 says the PID/start-time `unix-process` form carries `pid`, `uid`
and `start-time`; A-10.6 correctly says `uid` is optional in that general form.
The general Polkit contract must be separated from the proposed
`pkcheck`-equivalent request shape, which does supply `uid`.

## Checks and unaffected conclusions

Repository-only checks confirmed the record's stated line, byte and SHA-256
identity; the four source-completion-authorization snapshots and archive-index
hashes; clean tracked-file `git diff --check`; and no diff to the accepted
interface contract. A narrow primary-source spot check supported the pivotal
`StartTransientUnit` ordering and Polkit non-interactive decision-path claims.

The return otherwise preserves the fixed boundary, separates `ASF`, `MD`, `DR`,
`PSC` and residual `UF` material, leaves Q6-6 and Q6-7 unanswered, selects no
`UF-15` through `UF-18` mechanism, and authorizes no successor work.

No tests, builds, formatters, linters, host access or retained-evidence access
were used for this independent review.

## Required disposition

Peter should authorize one bounded cumulative remediation covering exactly
`WP3-SC-R1` through `WP3-SC-R4`, followed by independent Codex re-review. The
remediation must not integrate the record into the accepted interface contract,
close a Q3 question, answer Q6-6 or Q6-7, establish concrete Route 3, select
LIT-FULL, or prepare WP-4 through WP-7.
