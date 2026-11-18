# Active delivery plan — implementation-first baseline v1.9

Status: approved and active; Route 3 S1 inert provisioning complete on
production at STOP-A (2026-11-18); attended production reboot prepared, not
authorized or executed; S3 and S4 not authorized

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

**Production baseline.** Ubuntu 26.04.1, Ubuntu Python 3.14.4 and Ubuntu
PostgreSQL 18.6 are current; the attended Ubuntu continuation and the Lavalink
residue removal (music is removed under OD-40) closed on 2026-11-11 with no open
item. Peter's pre-production currency policy (implementation plan §14.1) stands:
supported OS, database, runtimes and dependencies are brought current before the
platform begins production use, without waiving backup, recovery, observation or
review evidence.

**Route 3, executed.** Peter bounded Route 3 to explicitly authorized, attended
migration/cutover evidence activations. It is not a general maintenance facility
and is not approved for recurring or unattended use; the transient
inspection-failure residual is accepted only inside that bounded use (named
attending operator, pre/post residual-state checks, verified root removal or
reboot if cleanup is uncertain). The provisioning plan (runbook part P) was
accepted on 2026-11-03; block F was completed on 2026-11-15; and on 2026-11-18,
under Peter's written S1 authorization, S1 inert provisioning ran on production
for deployable revision `26757f2ab67eb5be4f576dbc2166db5df8870857`: S1.0 through
S1.4 rc 0, S2.1 rc 0 with `STOP-A verified`, S2.2 rc 12 as expected before the
first post-S1 boot, all 32 package payloads reverified at every gate. Claude and
Codex final review found no defect or rollback need. STOP-A holds: no supervisor
unit, process, linger, sudoers grant, SA-2 artifact, state or runtime directory,
activation or cutover. Evidence: handback §16.

**Next action: an attended production reboot (prepared, not authorized).** Peter
authorized documenting it, not performing it. When Peter authorizes it, follow the
[reboot and continuation runbook](../operations/production-reboot-and-route-3-continuation-runbook.md):
new boot confirmed; service health; S2.1; S2.2 at rc 0; the read-only S2.3
checklist and account-dependent sudo, Polkit, user-manager and process checks;
independent review. The reboot interrupts the Freedom bot, worker, PostgreSQL,
Caddy and Foundry backends and cannot start Route 3, because nothing for the boot
to start exists at STOP-A.

**After that, separate decisions only.** S3 arming/install and S4 activation are
each a separate written decision of Peter's; S4 additionally needs the attending
operator, escalation contact and bounded window. A reboot between a future S3.5
and S4 or R3 is forbidden. The coordinator, start orchestration, automatic
attestation, migration/cutover and RB-1 remain unassigned.

## Evidence and boundaries

- Accepted provisioning-plan evidence: exact-tree 309 / 51 / 315 passed, guard
  suite 40 passed (2026-11-03), clean independent R6/R7 re-review.
- Release-record and reference tooling (2026-11-14/15, `oracle-test`):
  release-record module 350 passed; provisioning module as root 235 passed; bot
  7,928 passed / 252 skipped; web 2,894 passed / 80 skipped; Foundry 171 passed.
  Those validate the repository tree and the disposable host; the production
  result is the S1/S2 record above.
- Production facts and the v2 checklist are in the cumulative
  [handback](../review/route-3-production-readiness-handback.md) (§6 checklist,
  §15 S0.A, §16 S1 result).
- Discord remains the community platform and identity/integration source. Only
  the legacy Freedom bot is eventually retired under implementation-plan §15.2
  after the full completion criteria are met.

## History

The previous plan (S0.A attestation state; the 2026-11-07 to 2026-11-11
production-baseline paragraphs; the 2026-10-25 to 2026-11-03 Route 3
decisions) is preserved verbatim in
[`active-delivery-plan-through-2026-11-15-route-3-s0a-attestation.md`](active-delivery-plan-through-2026-11-15-route-3-s0a-attestation.md);
an earlier predecessor is
[`active-delivery-plan-through-2026-10-24-route-3-production-readiness.md`](active-delivery-plan-through-2026-10-24-route-3-production-readiness.md).
Both are indexed in the [plan archive](active-delivery-plan-archive/README.md)
and are evidence, not authority.

[Active handover](../review/Handover%20information) ·
[Current status](status.md) ·
[Implementation plan](../implementation-plan.md) ·
[Reboot and continuation runbook](../operations/production-reboot-and-route-3-continuation-runbook.md)
