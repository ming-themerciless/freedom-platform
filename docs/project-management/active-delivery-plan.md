# Active delivery plan — implementation-first baseline v1.9

Status: approved and active; provisioning plan accepted, release fields no-go 2026-11-03

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
2026-10-25. Its unprivileged part changed nothing and returned **NO-GO**: the
required Python 3.14, account, Route 3 units/artifact/runtime paths and tmpfiles
prerequisite are absent, and the live checkout plus Python 3.12 venv fail the
executor's root-owned trust boundary.

Peter then gave the follow-up assignment and named the window, himself as
rollback owner and retention until reviewed. Root-assisted sudoers and private
Polkit classification **completed** (nothing reaches the future account). Phase
B stopped on a live-path coexistence conflict; Phase C did not begin. Production
changes were Peter's temporary root grant(s), the approved `chmod 0440` of
`/etc/sudoers.d/foundry-bot`, and an `rm -f` of the grant file whose status was
never reported; nothing was provisioned or installed and no service restarted.

Peter then selected a distinct trusted deployment, `/opt/freedom-route3/{code,venv}`.
It is implemented and rehearsed only on `oracle-test`; the live services stay on
their paths and are not edited or restarted. The root does not exist on
production, and the selection authorizes no production change.

Peter confirmed on 2026-10-31 that `/etc/sudoers.d/zz-claude-window` is
**absent** and accepted the Phase A stop/order deviation. Peter accepted the
production provisioning plan on 2026-11-03 after Codex's independent R6/R7
re-review found no remaining issue. The completed prompt chain is archived;
runbook part P and the cumulative handback remain the forward contract and
evidence.

The plan review gate is closed, but every block-F release identity remains
`UNSET`. The next work is release preparation: commit/publish the exact accepted
candidate, produce the off-production archive/manifest/interpreter/SA-2
identities, separately authorize read-only production S0.0 to derive the exact
Python package closure and origins, and review the supplied release record.
Only then may Peter separately decide whether to authorize S1 inert
provisioning. S3 arming/install and S4 activation remain later independent
decisions. Account-dependent inspection repeats after any separately authorized
provisioning. The coordinator, start orchestration, automatic attestation,
migration/cutover and RB-1 remain unassigned.

## Evidence and boundaries

- Accepted provisioning-plan evidence: exact-tree **309 / 51 / 315 passed**,
  guard suite **40 passed**, clean shell syntax and `git diff --check`, clean
  disposable-host residue state, and a clean independent R6/R7 re-review.
- Final focused checklist review: exact-tree **53/53**, clean `bash -n` and
  `git diff --check`; the structural run retained one known baseline allowlist
  failure.
- Production facts are in handback §§6.1–6.2; §6.1's counts come from checklist
  v1 (old live paths) and the current checklist is v2 (trusted deployment paths).
  Post-provision account facts, F-1 through F-3 and the bounded
  activation/rollback procedure remain later gates; sudoers and Polkit policy
  are no longer open.
- Discord remains the community platform and identity/integration source. Only
  the legacy Freedom bot is eventually retired under implementation-plan
  §15.2 after the full completion criteria are met.

[Active handover](../review/Handover%20information) ·
[Current status](status.md) ·
[Implementation plan](../implementation-plan.md) ·
[Archived predecessor plan](active-delivery-plan-through-2026-10-24-route-3-production-readiness.md)
