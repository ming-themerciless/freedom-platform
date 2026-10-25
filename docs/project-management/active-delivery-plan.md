# Active delivery plan — implementation-first baseline v1.9

Status: approved and active; production inspection returned no-go 2026-10-25

Owner and acceptance authority: Peter Duscha

## Working rules

- Deliver small implementation slices and prove them with executable tests.
- Use `oracle-test` for every required test level, including root/systemd,
  PostgreSQL, failure injection, reboot and recovery work.
- Production and staging access or mutation require separate explicit
  authority. Never use real secrets or player data on the disposable host.
- Reversible technical details may be selected and tested by the implementer.
  Ask Peter before changing product scope, data authority,
  authorization/privacy policy, destructive production behavior, irreversible
  architecture or production activation.
- Use one concise handback per slice. Historical prompts and remediation
  records are evidence, not current authority.

## Current delivery position

The cumulative inactive Route 3 production-readiness candidate is accepted for
continued non-production development. Peter has selected production as the
direction and bounded Route 3 to explicitly authorized, attended
migration/cutover evidence activations. It is not a general maintenance
facility and is not approved for recurring or unattended use.

The transient inspection-failure residual is accepted only inside that bounded
use: every activation needs a named attending operator, pre/post residual-state
checks and verified root removal or reboot before the operating window closes
if cleanup is uncertain. Any recurring or unattended use requires a stronger
trusted-identity and automated-reconciliation design, tests and independent
security review.

Peter authorized the production-specific §6 read-only inspection on
2026-10-25. The unprivileged portion is complete and made no change. It returned
**NO-GO**: the required Python 3.14, account, Route 3 units/artifact/runtime
paths and tmpfiles prerequisite are absent, and the live checkout plus Python
3.12 venv fail the executor's root-owned trust boundary. Sudoers and private
Polkit policy require root and remain incomplete.

The next gate is root-assisted completion of those two read-only policy checks,
then a reviewed provisioning plan. Installation, remediation and activation
are not authorized. Account-dependent inspection repeats after any separately
authorized provisioning. The coordinator, start orchestration, automatic
attestation, migration/cutover and RB-1 remain unassigned.

A bounded Claude follow-up prompt is prepared for that gate. Its existence is
not authority to mutate production: the prompt requires Peter's named window,
rollback owner, retention period and approved Python/artifact sources before
writes, and it stops before supervisor installation or activation.

## Evidence and boundaries

- Final focused checklist review: exact-tree **53/53**, clean `bash -n` and
  `git diff --check`; the structural run retained one known baseline allowlist
  failure.
- The accessible production facts are recorded in handback §6.1. Sudo
  `Defaults`, private Polkit policy, post-provision account facts, F-1 through
  F-3, named operational ownership and the bounded activation/rollback
  procedure remain open gates.
- Discord remains the community platform and identity/integration source. Only
  the legacy Freedom bot is eventually retired under implementation-plan
  §15.2 after the full completion criteria are met.

[Active handover](../review/Handover%20information) ·
[Current status](status.md) ·
[Implementation plan](../implementation-plan.md) ·
[Archived predecessor plan](active-delivery-plan-through-2026-10-24-route-3-production-readiness.md)
