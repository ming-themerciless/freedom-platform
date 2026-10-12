# Independent Codex re-review — LIT-FULL WP-3 source-completion R1 remediation

Date: 2026-10-11

Work reviewed: `C-P5.0-R5-RP11-H1-OH-S3-RT3-WP3-SC1-R1-20261010-24`

Reviewer: Codex

Decision owner: Peter Duscha

## Recommendation

Do not accept the R1 remediation in its present form. Two Important findings
remain. No Blocking or Optional finding was identified. The accepted WP-3
`HARD STOP` remains in force, and WP-4 through WP-7 remain unauthorized.

## Important findings

### `WP3-SC-R1-RE1` — the kernel manifest does not evidence the claimed `v7.0` retrieval

The six manifest rows labelled `v7.0` use the corresponding `v7.0.14` requested
URL, timestamp, byte count and SHA-256. The `v7.0` tag-page and commit-page rows
likewise use the `v7.0.14` URLs and retrieval identities while asserting the
different `v7.0` tag and commit identities. The record therefore does not
evidence a separate `v7.0` retrieval or the claimed byte comparison between the
two tags.

Remediation must retrieve both sides of the comparison from their exact
kernel.org URLs into one fresh `/tmp` research directory, record each object's
own URL, timestamp, size and full SHA-256, and either prove the six pairs are
byte-identical or return `HARD STOP`. The tag and commit metadata rows must
likewise carry the actual `v7.0` and `v7.0.14` retrieval identities.

### `WP3-SC-R1-RE2` — A-10.6 still contradicts itself about `uid`

A-10.6 says that `uid` is “optional in every form” and then correctly says that
the pidfd form requires `uid`. Appendix F repeats the same contradiction. The
surrounding R1 summary, A-10.5, A-10.10, A-10.12, P-10.1, A-13.2 and the Q3-6
row otherwise state the intended distinction consistently.

Remediation must say unambiguously that `uid` is optional in the general
PID/start-time form and required in the pidfd form, and must remove the phrase
“optional in every form” everywhere it purports to summarize the decoder.

## Checks and unaffected conclusions

Repository-only checks confirmed the record and accepted interface-contract
line, byte and SHA-256 identities reported by the handback; the four archived
R1-authorization snapshot hashes and index entries; synchronized current-state
pointers; and clean tracked-file `git diff --check`.

`WP3-SC-R1` and `WP3-SC-R2` from the first review appear remediated: the fresh
reading ledger and clarification are explicit, and the Ubuntu chain is recorded
from the downloaded keyring and Peter-pinned fingerprint rather than an installed
keyring. Residual `R-M.1` is disclosed honestly and remains for Peter; this review
does not accept it, reject it or authorize a different source.

No tests, builds, formatters, linters, network research, host inspection,
retained-evidence access or repository edits were used for this independent
re-review.

## Required disposition

Peter should authorize one bounded R2 documentation/source-manifest remediation
covering exactly `WP3-SC-R1-RE1` and `WP3-SC-R1-RE2`, followed by independent
Codex re-review. It must not integrate the source record into the accepted
interface contract, close or reopen a Q3 question, answer Q6-6 or Q6-7, resolve
`R-M.1`, establish concrete Route 3, select LIT-FULL or prepare WP-4 through
WP-7.
