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
The full coordinator and production installers/activation remain later work.
The remaining production-activation gates are summarized in the active handover.
