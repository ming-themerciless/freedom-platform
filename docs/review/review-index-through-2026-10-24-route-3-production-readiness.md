# Review records

The active assignment is always [`Handover information`](Handover%20information).
Only records linked from that file or from the
[active delivery plan](../project-management/active-delivery-plan.md) control
current work.

All other dated prompts, reviews, handbacks, evidence records, snapshots and
WP-1/WP-2/WP-3 research artifacts in this directory are **historical archive
material**. They remain at their original paths so existing evidence links do
not break. They may inform implementation but do not create current authority,
block testing, or require further reconciliation unless the active handover
explicitly revives one.

Going forward, use one concise handback per implementation slice. Do not create
prompt-review-remediation chains, identity ledgers or closure records unless
Peter Duscha explicitly requests them.

The complete inactive Route 3 role series was accepted on 2026-10-14. Its
current implementation record is the
[`hold` handback](route-3-hold-role-implementation-handback.md). The Polkit
`tmpfiles.d` prerequisite was accepted on 2026-10-15; its current implementation
record is the
[`tmpfiles` handback](route-3-polkit-tmpfiles-installer-handback.md). The first
Package 5.0 consumer is assigned by the
[`start` implementation prompt](route-3-start-role-implementation-claude-prompt.md);
Claude's `start` implementation and its
[handback](route-3-start-role-implementation-handback.md) were independently
re-reviewed and accepted by Peter on 2026-10-15. Static SA-2 `stop`, assigned to Claude by the
[`stop` implementation prompt](route-3-stop-role-implementation-claude-prompt.md),
is implemented and accepted for continued non-production development
([handback](route-3-stop-role-implementation-handback.md)). Its refusal-diagnostic,
typed-result and test-only host-job assertion remediations are complete;
independent Codex re-review found no blocking issue, and Peter accepted SA-2 for
continued non-production development on 2026-10-16.
Peter then assigned RT-1 `consume` to Claude under the
[`consume` implementation prompt](route-3-consume-role-implementation-claude-prompt.md).
Claude implemented it as an uncommitted candidate
([handback](route-3-consume-role-implementation-handback.md)); independent Codex
review found two blocking failure-path defects. One bounded
[review remediation](route-3-consume-role-review-remediation-claude-prompt.md)
was completed. Independent Codex re-review found no blocking issue, and Peter
accepted RT-1 for continued non-production development on 2026-10-17. Peter
then assigned RT-5 `attest` as the next bounded slice under the
[`attest` implementation prompt](route-3-attest-role-implementation-claude-prompt.md).
Claude implemented it as an uncommitted candidate
([handback](route-3-attest-role-implementation-handback.md)). Independent Codex
review found a blocking false-success path with missing boot evidence and
non-reproducible abbreviated commands. One bounded
[review remediation](route-3-attest-role-review-remediation-claude-prompt.md) was
completed and returned for independent Codex re-review; the second and third
remediations (missing directory identity; missing mandatory tree-P evidence, see
[third review prompt](route-3-attest-role-review-remediation-r3-claude-prompt.md)) were
likewise returned for re-review. A fifth correction made the exact tree-P
comparison lossless; independent Codex re-review found no remaining
implementation-quality blocker and independently reproduced the focused 271-test
pass, then the complete focused role set at **2369 passed, 2 documented
environment skips**. The 2026-10-18 governing evidence clarification treats summarized routine
commands as non-blocking when material claims remain assessable. Peter accepted
RT-5 for continued non-production development on 2026-10-18. The non-root
executor and its OC-1/OC-2/OC-3 checks were outside that accepted slice. Peter
then assigned Claude the first real executor interruption path under the
[`executor OC implementation prompt`](route-3-executor-oc-implementation-claude-prompt.md).
The cumulative implementation and remediation record is the
[`executor handback`](route-3-executor-oc-implementation-handback.md). Peter
selected the root-controlled system-service wrapper for the inactive supervisor
package on 2026-10-20 and approved the sixth bounded review correction on
2026-10-21. The current correction treats request-write failure as an ambiguous
handoff, starts the serving thread before `READY=1`, verifies effective loaded
drop-ins and execution properties, and treats the observed PATH-only transient
environment as defense in depth rather than an atomic authorization invariant.
The privileged invariant is the fixed sudoers/SA-2 argv, Python `-I -S`, and the
root-owned `stop` artifact's no-environment-read path. Claude returned the R6
candidate; independent Codex review reproduced its principal suites but found
that `KeyboardInterrupt` or another `BaseException` at or after the request-
write boundary can escape instead of becoming `HANDED_OFF`. Peter assigns the
direct correction and current-state documentation reconciliation under the
[`R6 review-remediation prompt`](route-3-executor-oc-r6-review-remediation-claude-prompt.md).
Claude returned that remediation; independent Codex re-review found no remaining
implementation defect but found the real-socket proofs nondeterministic (one
`recv` may return a prefix) and current-state text stale. Peter accepted the
[`second remediation prompt`](route-3-executor-oc-r6-review-remediation-r2-claude-prompt.md) and assigned
Claude the correction, which has returned for independent re-review.
Codex found no implementation or production-safety defect. Peter recorded the
remaining separately-delivered-surplus helper overclaim as non-blocking and
authorized optional test-only hardening under the
[`Claude prompt`](route-3-executor-oc-r6-nonblocking-test-hardening-claude-prompt.md),
followed by one bounded ordering correction. Claude returned that correction;
independent Codex re-review found no remaining finding and reproduced the
focused **511 passed, 5 documented host-only skips** result on `oracle-test`.
Peter accepted the cumulative executor OC R6 candidate for continued
non-production development on 2026-10-22. The full coordinator and production
or staging installation/activation remain later work.
The accepted and authorized Claude implementation briefing is
[`route-3-executor-oc-r6-implementation-claude-prompt.md`](route-3-executor-oc-r6-implementation-claude-prompt.md).
It accepted the R6 implementation direction rather than the candidate; the
completed implementation has now passed independent review and received the
separate acceptance recorded above.
The remaining production-activation gates are summarized in the active handover.

After accepting the cumulative executor OC R6 candidate on 2026-10-22, Peter
assigned Claude the next bounded step under the
[`Route 3 production-readiness prompt`](route-3-production-readiness-claude-prompt.md).
The assignment covers complete-chain security review preparation and an
exact-path clean lifecycle rehearsal on `oracle-test`; it authorizes no
production/staging access or activation and leaves the transient
inspection-failure disposition to Peter after independent Codex review.
Claude has returned it: [handback](route-3-production-readiness-handback.md). Codex found blocking installer
recovery/sudo defects and an inaccurate residual analysis; Peter assigned the
[review remediation prompt](route-3-production-readiness-review-remediation-claude-prompt.md); Claude has returned the
remediation in the same handback (§0), awaiting independent Codex re-review. Not accepted.
A second independent review reproduced three installer recovery gaps and two inspection-method defects; Peter assigned the
[second review remediation prompt](route-3-production-readiness-review-remediation-r2-claude-prompt.md) and Claude has
returned it in the same handback ("Second review remediation return"), awaiting independent Codex re-review. Not accepted.
That re-review found two remaining upgrade-restoration verification defects and one dedicated-account user-unit-path inspection
gap. Peter assigns Claude the bounded
[third review remediation prompt](route-3-production-readiness-review-remediation-r3-claude-prompt.md). The candidate remains
unaccepted; Claude has returned it in the same handback ("Third review remediation return"), awaiting independent Codex re-review; production/staging access, inspection and activation remain unauthorized.
That re-review found a remaining strict wants-link observation defect, unit-description disclosure and ambient-account redirection in checklist item 5b, and stale current-state headings. Peter assigns Claude the bounded
[fourth review remediation prompt](route-3-production-readiness-review-remediation-r4-claude-prompt.md). Claude has returned it in the
same handback ("Fourth review remediation return", 2026-10-23), awaiting independent Codex re-review. The candidate remains
unaccepted; production/staging access, inspection and activation remain unauthorized.
Codex's review of that return reported a host-state discrepancy, residual status masking in checklist item 5b and a missing fourth-return section; Peter assigned the bounded
[fifth review remediation prompt](route-3-production-readiness-review-remediation-r5-claude-prompt.md). Claude has returned it in the same handback ("Fifth review remediation return", 2026-10-23), awaiting independent Codex re-review; the candidate remains unaccepted and production/staging access, inspection and activation remain unauthorized.
Codex's review of the fifth return found one bounded false-completion path:
item 5b still prints `COMPLETE` after a directory search or unit query fails.
Peter assigns Claude the direct completion correction under the existing
round-five prompt; this is not a sixth remediation round and requires only the
focused checks named there. The candidate remains unaccepted.
Claude returned the final portability follow-up after replacing diagnostic-text
parsing with the fixed isolated Python errno/type probe. Independent Codex
focused re-review found no remaining implementation defect: exact extracted
checklist identity, **53/53** focused tests, clean `bash -n` and
`git diff --check`, and **127 passed, 1 known baseline structural failure**.
Codex recommends acceptance for continued non-production development; Peter's
acceptance and transient-risk decision remain separate, with no production or
staging activity authorized.
