# Active handover — Route 3 role implementation — 2026-10-13

**IMPLEMENTATION AND FULL DISPOSABLE-SERVER TESTING AUTHORIZED**

Peter Duscha supersedes the WP-3 research-only hard stop and the associated
WP-4 through WP-7 documentation gates for development work. The WP-1 through
WP-3 records remain historical evidence; they are not current prerequisites and
need no further closure or reconciliation.

Peter Duscha accepted the Route 3 manager/Polkit adapter on 2026-10-13 for the
next implementation stage. The four security findings are closed for continued
development, the final suite comparison introduced no Route 3 regression, and
the adapter remains inactive in production.

The active objective is to implement the three controlled role behaviors in
small dependency-ordered slices. The first two slices are complete and the
reviewed backstop handback recommends proceeding:

1. shared cleanup plus `deact … stop-post` — complete;
2. `backstop`, reusing the accepted cleanup implementation — complete; and
3. `hold`, now that both cleanup rungs exist — active.

Peter has accepted the backstop Q6-7 behavior. A `tmpfiles.d` entry is the
preferred future installer/activation design for the observed Polkit directory
ordering, but its installation and real-reboot proof remain outside the current
`hold` slice. The hold harness uses disposable pre-start setup and must prove
that late directory creation fails closed; the holder never restarts Polkit.

[Current Claude prompt](route-3-hold-role-implementation-claude-prompt.md) ·
[Completed backstop handback](route-3-backstop-role-implementation-handback.md) ·
[Completed stop-post handback](route-3-stop-post-role-implementation-handback.md) ·
[Accepted adapter handback](route-3-manager-polkit-implementation-handback.md).

All levels of testing are authorized on `oracle-test`, including SSH and sync,
dependency installation, builds, network tests, root/systemd operations,
PostgreSQL work, destructive migration/recovery drills, failure injection,
restart/rollback exercises, and end-to-end tests. The disposable host may be
reset as needed.

Still prohibited without a separate explicit instruction: production or
staging mutation, use or disclosure of real secrets or player data, weakening
authorization, and destructive operations outside the disposable environment.

Run these prompts sequentially, not concurrently. Keep each handback concise:
implemented behavior, files changed, exact test commands/results, remaining
production risks, and the next action. Do not create another evidence or
prompt-review chain.

[Active delivery plan](../project-management/active-delivery-plan.md) ·
[Disposable test server](../operations/disposable-test-server.md) ·
[Reset handback](implementation-first-reset-handback-2026-10-12.md) ·
[Archived WP-3 handover](Handover-information-through-2026-10-12-wp3-contract-review.md) ·
[Historical review records](README.md) ·
[Handover archive index](handover-archive/README.md).
