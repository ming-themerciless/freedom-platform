# WP-3 source-completion evidence acceptance and contract-integration direction — 2026-10-11

Decision owner: Peter Duscha, Product Owner and Acceptance Authority

## Decision

Peter Duscha accepts the cumulative, R1- and R2-corrected WP-3
source-completion record as the evidence basis for a later, separately reviewed
contract-integration step.

Peter also accepts the disclosed `R-M.1` provenance limitation for this Route 3
readiness investigation: the Ubuntu kernel delta `linux_7.0.0-31.31.diff.gz` is
not authenticated through the current signed Ubuntu `Sources` indexes, but its
exact byte count and SHA-256 equal the already accepted R2 Appendix D evidence.
That basis is accepted for the limited A-12.3 and A-15.2 facts. This decision
does not characterize the delta as archive-chain authenticated, and the
limitation must remain visible anywhere those facts are integrated.

The corrected record is accepted at 1,758 lines, 240,533 bytes and SHA-256
`4c2a1b76a72002de77ca885ba248f086c302b5e9aebebd117cfa90b8989a1049`.

## Contract-integration direction

Peter authorizes preparation of one bounded contract-integration assignment.
The proposed assignment must integrate only accepted WP-3 evidence, preserve
fact/proposal/residual classifications, and produce a decision-ready treatment
of D-1 through D-6, D-9 and D-10. Those choices remain Peter's; prompt
preparation does not decide them.

The exact assignment must be pinned by line count, byte count and SHA-256,
independently reviewed, and expressly accepted before any executor is
activated. Its return must receive independent review before any WP-4 authority
is considered.

## Preserved boundary

This decision does not itself edit or supersede the accepted interface
contract, close or reopen any Q3 question, answer Q6-6 or Q6-7, decide D-1
through D-14, establish concrete Route 3, select LIT-FULL, or authorize WP-4
through WP-7. D-7, D-8 and D-11 through D-14 remain outside the proposed
integration decision set unless Peter separately expands it through the
applicable gate.

The accepted WP-3 HARD STOP remains in force until a reviewed integration and
Peter's later gate decision replace it. No host-installation or retained-
evidence access, network research, implementation, interface-contract edit,
configuration/infrastructure edit, launcher work, build, test, formatter,
package installation, service/database operation, OH-S4/OH-S4p or later slice,
H-1/H-2, activation, rollback, commit or push is authorized. The R5 and H-0G
retained paths remain untouched.

## Accepted evidence

- [Corrected source-completion record](phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-record.md);
- [R2 remediation acceptance](project-review-2026-10-11-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r2-remediation-acceptance.md);
- [Independent Codex R2 re-review](project-review-2026-10-11-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r2-remediation.md); and
- [archived pre-decision handover](Handover-information-through-2026-10-11-lit-full-wp3-source-completion-r2-remediation-acceptance.md).
