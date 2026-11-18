# Review records

The active assignment and safety boundary are always in
[`Handover information`](Handover%20information). The current delivery state is
in the [active delivery plan](../project-management/active-delivery-plan.md).

## Current production-baseline remediation

- [Ubuntu 26.04 / PostgreSQL 18 handback](production-ubuntu-26-04-upgrade-handback.md)
- [Completed R2 remediation prompt](production-ubuntu-26-04-upgrade-review-remediation-r2-claude-prompt.md)
- [Disposable-server runbook](../operations/disposable-test-server.md)

Production and the disposable lane now use Ubuntu Python 3.14 and PostgreSQL
18. The disposable suites are green after R2 (2026-11-07) and again on the refreshed
dependency set (2026-11-08: bot 7,571 passed, web 2,893 passed, Foundry 171). The apparent
`nobody:nogroup` ownership of the production host's OpenSSH client
configuration was an agent-sandbox user-namespace artifact, not a production
defect: unsandboxed, the paths are `root:root` and ordinary `ssh oracle-test`
works. Peter assigned one bounded R2 remediation; independent Codex re-review
found no remaining repository or disposable-host finding. The active handover
contains the remaining authority and safety boundary.

## Retained Route 3 records

- [Accepted cumulative production-readiness and provisioning-plan handback](route-3-production-readiness-handback.md)
- [Accepted provisioning runbook](../operations/executor-supervisor-provisioning-runbook.md)
- [Production checklist v2 in handback §6](route-3-production-readiness-handback.md#6-production-specific-read-only-inspection-checklist)
- [Executor implementation handback](route-3-executor-oc-implementation-handback.md)

Peter accepted the Route 3 production provisioning plan on 2026-11-03 after
Codex's independent R6/R7 re-review found no remaining issue. The plan review
gate is closed, but every release field remains `UNSET`; production
provisioning, installation and activation remain unauthorized.

The former S0.0 release-preparation procedure assumed Python 3.14 was absent and
must not run. After the active production-baseline remediation closes, Route 3
needs a separately reviewed release-record/package redesign for pre-installed
Python 3.14 before release preparation or any S1 decision.

## Completed prompt archives

- [Production inspection and provisioning-plan remediation, November 2026](archive/route-3-production-provisioning-2026-11/README.md)
- [Production-readiness prompt package, October 2026](archive/route-3-production-readiness-2026-10/README.md)
- [Review archive index](archive/README.md)

All other dated prompts, reviews, handbacks, evidence records and snapshots in
this directory are historical evidence unless the active handover explicitly
links them as current. Historical material creates no authority and no new
development gate.

[Archived predecessor index](review-index-through-2026-10-24-route-3-production-readiness.md) ·
[Handover archive](handover-archive/README.md)
