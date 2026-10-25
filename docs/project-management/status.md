# Project status

## Current status — Route 3 production inspection no-go — 2026-10-25

Baseline v1.9 remains active. Phase 3 and Phase 4 gates are approved; Phase 5
implementation and unrestricted testing on the disposable `oracle-test` server
remain authorized.

Peter accepted the cumulative Route 3 production-readiness candidate for
continued non-production development on 2026-10-24. The accepted chain now
includes the inactive manager/Polkit roles, static start/stop, consume, attest,
the non-root executor and persistent supervisor package, installer recovery,
strict sudo verification, and the fail-closed production fact checklist.
Independent final review reproduced **53/53** focused checklist tests on the
exact `oracle-test` tree, clean shell syntax and diff checks, and only the known
structural allowlist baseline failure.

Peter has now classified Route 3 as a bounded, attended migration/cutover
evidence facility and accepted the transient inspection-failure residual only
within that boundary. Route 3 is not approved for general maintenance,
recurring use or unattended operation. Every activation must be explicitly
authorized and attended, with pre/post residual checks and verified cleanup or
reboot before the operating window closes. Recurring use requires a stronger
trusted-identity and automated-reconciliation design.

### Open decisions and gates

- Peter authorized the §6 read-only production inspection on 2026-10-25. It
  made no production change and returned **NO-GO** for provisioning or
  activation: Python 3.14, the executor account, Route 3 units/artifact/runtime
  paths and the tmpfiles prerequisite are absent, while the live checkout and
  Python 3.12 venv fail the required root-owned, non-writable trust boundary.
- Sudoers and private Polkit policy could not be read without root and remain
  incomplete. They require a root-assisted, still read-only completion.
- A bounded Claude inspection/prerequisite-remediation prompt is prepared but
  is not active merely because it exists. It stops before supervisor install or
  activation and requires the named production prerequisites before writes.
- The account-dependent checks must be repeated after any later provisioning.
  The maintenance window, rollback owner and evidence retention are unnamed.
- Production installation and activation remain prohibited without their own
  explicit instructions. The inspection authority does not permit remediation.

[Active handover](../review/Handover%20information) ·
[Active delivery plan](active-delivery-plan.md) ·
[Accepted handback](../review/route-3-production-readiness-handback.md) ·
[Archived predecessor status](status-through-2026-10-24-route-3-production-readiness-acceptance.md)
