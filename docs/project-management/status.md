# Project status

## Route 3 S1 inert provisioning complete at STOP-A; attended production reboot next — 2026-11-18

Baseline v1.9 remains active. Phase 3 and Phase 4 gates are approved; Phase 5
implementation and unrestricted testing on the disposable `oracle-test` server
remain authorized.

**Executed on production, 2026-11-18** (Peter's written S1 authorization,
attended root session): deployable revision
`26757f2ab67eb5be4f576dbc2166db5df8870857`; S1.0 through S1.4 each rc 0; S2.1 rc 0
with `STOP-A verified`; S2.2 rc 12, expected before the first post-S1 boot; all
32 signed-archive package payloads and metadata reverified at every trusted
gate. The five reviewed Python 3.14 packages are held, `/opt/freedom-route3` is
published and verified, the dormant `freedom-executor` account exists without
linger, and the `tmpfiles.d` fragment is installed. At STOP-A there is no
supervisor unit or enablement, no Route 3 process, no linger or user manager, no
sudoers grant, no SA-2 artifact, no state or runtime directory and no
activation or cutover. S3 and S4 were not run. Claude and Codex final review
found no defect and no rollback need. Run evidence is `/root/route3-s1-run.XqEtiYXR`;
the empty outer `/tmp/route3-s1-terminal.rc` is a mangled final `printf`, and
`/tmp/route3-s1-terminal.log` is complete. Evidence record:
[handback §16](../review/route-3-production-readiness-handback.md).

**Prepared, not executed:** an attended production reboot and the post-reboot
verification, written up in the
[reboot and continuation runbook](../operations/production-reboot-and-route-3-continuation-runbook.md).
Peter authorized the preparation and documentation only; the reboot has not been
authorized or run. Expected effect: the Freedom bot, worker, PostgreSQL, Caddy
and the Foundry backends restart; Route 3 cannot start, because at STOP-A
nothing exists for the boot to start.

**Gate sequence after the reboot:** new boot confirmed, service health, S2.1,
S2.2 must now return rc 0, the read-only S2.3 checklist and account-dependent
checks, independent review, then Peter's separate written decision on S3. S3
arming/install and S4 activation remain unauthorized, and a reboot between a
future S3.5 and S4 or R3 stays forbidden. Route 3 is bounded to explicitly
authorized, attended migration/cutover evidence activations.

**Production baseline (unchanged by S1):** Ubuntu 26.04.1, Python 3.14.4,
PostgreSQL 18.6, Caddy 2.11.9, Node 24.22.2; worker, bot, PostgreSQL and Caddy
active, `freedom-web` inactive. The Ubuntu remediation and Lavalink residue
removal closed on 2026-11-11 with no open item.

**Last disposable-host figures** (`oracle-test`, exact trees 2026-11-14/15):
release-record 350 passed; provisioning module as root 235 passed; bot 7,928
passed / 252 skipped; web 2,894 passed / 80 skipped; Foundry 171 passed. This
documentation consolidation ran no behavioral suite.

## History

Every earlier status entry (the 2026-11-15 S0.A record, the 2026-11-07 to
2026-11-11 production-baseline narrative, the accepted provisioning plan and the
review rounds) is preserved verbatim in
[`status-through-2026-11-15-route-3-s0a-attestation.md`](status-through-2026-11-15-route-3-s0a-attestation.md),
indexed in the [status archive](status-archive/README.md). It is evidence, not
current authority; its `UNSET`, "NO-GO" and "next step is artifact delivery"
statements describe the state on their dates.

[Active handover](../review/Handover%20information) ·
[Active delivery plan](active-delivery-plan.md) ·
[Implementation plan](../implementation-plan.md) ·
[Provisioning runbook](../operations/executor-supervisor-provisioning-runbook.md) ·
[Reboot and continuation runbook](../operations/production-reboot-and-route-3-continuation-runbook.md)
