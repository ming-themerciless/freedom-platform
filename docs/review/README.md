# Review records

The active assignment and safety boundary are always in
[`Handover information`](Handover%20information). The current delivery state is
in the [active delivery plan](../project-management/active-delivery-plan.md) and
[status](../project-management/status.md).

## Current Route 3 and production records

- [Reboot and continuation runbook](../operations/production-reboot-and-route-3-continuation-runbook.md):
  the prepared (not authorized, not executed) attended production reboot and the
  post-reboot gate sequence
- [Accepted provisioning runbook](../operations/executor-supervisor-provisioning-runbook.md):
  the sole executable authority for every Route 3 block (S1 executed to STOP-A on
  2026-11-18; S3 and S4 not run and not authorized)
- [Cumulative production-readiness handback](route-3-production-readiness-handback.md):
  evidence record; §6 holds the read-only v2 production checklist (S2.3), §15 the
  S0.A record and §16 the S1 result
- [Production checklist v2 in handback §6](route-3-production-readiness-handback.md#6-production-specific-read-only-fact-checklist)
- [Executor implementation handback](route-3-executor-oc-implementation-handback.md)
- [Ubuntu 26.04 / PostgreSQL 18 production-upgrade handback](production-ubuntu-26-04-upgrade-handback.md)
  and [prerequisites](production-ubuntu-26-04-upgrade-prerequisites.md)
- [Disposable-server runbook](../operations/disposable-test-server.md)

Production runs Ubuntu 26.04.1, Python 3.14.4 and PostgreSQL 18.6; the
Ubuntu/Lavalink continuation closed on 2026-11-11. Route 3 S1 inert provisioning
completed on production on 2026-11-18 and stopped at STOP-A. The next production
action is an explicitly attended reboot with read-only verification; S3 and S4
are separate and unauthorized.

## Completed prompt archives

- [Production-baseline and Route 3 release-record prompts, November 2026](archive/production-baseline-and-route-3-release-2026-11/README.md)
  (the former paths of the moved prompts hold short compatibility records)
- [Production inspection and provisioning-plan remediation, November 2026](archive/route-3-production-provisioning-2026-11/README.md)
- [Production-readiness prompt package, October 2026](archive/route-3-production-readiness-2026-10/README.md)
- [Review archive index](archive/README.md)

All other dated prompts, reviews, handbacks, evidence records and snapshots in
this directory are historical evidence unless the active handover explicitly
links them as current. Historical material creates no authority and no new
development gate.

[Archived predecessor index, 2026-11-15](review-index-through-2026-11-15-route-3-s0a-attestation.md) ·
[Archived predecessor index, 2026-10-24](review-index-through-2026-10-24-route-3-production-readiness.md) ·
[Handover archive](handover-archive/README.md)
