# Production reboot and Route 3 post-S1 continuation

**Status: PREPARED, NOT EXECUTED, NOT AUTHORIZED TO RUN BY THIS DOCUMENT.**
Peter authorized the preparation and documentation of this procedure on
2026-11-18. The documentation task that wrote it did not reboot the host, ran
no privileged command and touched no production state. The reboot itself is
Peter's separate, explicitly attended decision (named operator, window,
escalation contact). **S3 and S4 are not authorized by this document or by the
reboot.**

This is a procedure for reconnecting and verifying, not an implementation. It
defines **no new executable block**. Every Route 3 command is a block of the
accepted
[provisioning runbook](executor-supervisor-provisioning-runbook.md) (blocks D
and F, S2.1, S2.2, the S2.3 checklist, and R only on Peter's instruction), which
remains the sole executable authority. Where this page and that runbook differ,
the runbook wins and the difference is a defect to report.

## 1. State: EXECUTED versus PREPARED

| Item | State |
|---|---|
| Route 3 S0.A attestation, block F complete (deployable revision `26757f2ab67eb5be4f576dbc2166db5df8870857`) | EXECUTED 2026-11-15 |
| Route 3 S1 inert provisioning (S1.0 through S1.4, each rc 0), attended, root, 2026-11-18 | **EXECUTED** |
| S2.1 on production: rc 0, `STOP-A verified` | **EXECUTED** |
| S2.2 on production: rc 12 (`fragment-predates-boot`), the status P.2 expects before the first post-S1 boot | **EXECUTED, as expected** |
| Production reboot | **PREPARED only. Not authorized, not executed.** |
| Post-reboot verification (section 5) | PREPARED only |
| S2.3 account-dependent checks after the boot | PREPARED only |
| Independent review of the post-reboot evidence | PREPARED only |
| S3 arming and install; S4 activation | **NOT authorized, NOT run**, each a separate later written decision |

Run evidence of S1: `/root/route3-s1-run.XqEtiYXR` (root-only, persists across
a reboot). The outer `/tmp/route3-s1-terminal.rc` is empty only because the
caller's final `printf` was mangled after the wrapper had printed its complete
success result; `/tmp/route3-s1-terminal.log` is the complete record. `/tmp`
may not survive a boot, so the attending operator decides before the reboot
whether to keep a root-only copy of that log (a root action outside this
document). The `/root` evidence is authoritative either way.

## 2. Reconnect checklist (for an agent that has lost context)

1. Read `.agents/AGENTS.md`, then the active
   [handover](../review/Handover%20information) and
   [status](../project-management/status.md). Do not treat anything under an
   `-through-` snapshot or an archive directory as current.
2. Determine which row of section 1 is true **now**. Ask the maintainer, or read
   the newest dated record in the
   [handback §16](../review/route-3-production-readiness-handback.md), rather
   than assuming the reboot has or has not happened.
3. You may do read-only inspection of production only inside an authorized,
   attended session. An agent session has no sudo; root blocks are pasted by the
   attending operator.
4. You may **not**: reboot, run S3.x, S4.x, the installer, R, R3 or R0 on your
   own initiative, enable linger, create a sudoers or SA-2 object, delete
   `/root/route3-evidence`, or touch `.env`, credentials or player data.
5. Find your position in section 5 and continue from the first gate whose
   result is not recorded. Record each result in the handback, not in a new
   plan.

## 3. What a reboot interrupts, and why Route 3 cannot start from it

Expected, ordinary interruption (all of it restarts or is restarted by the
host's normal means): the Freedom bot (Discord commands unavailable), the
worker, PostgreSQL (clean shutdown and recovery), Caddy and every HTTPS host it
serves, and the Foundry backends reached through it. `freedom-web` is inactive
before and must remain inactive after. The outage length is unknown until
measured; the attending operator records start and end times.

Route 3 cannot start on this reboot because, at STOP-A (runbook P.2), nothing
exists for the boot to start: there is no supervisor unit fragment and no
`multi-user.target.wants` link, no lingering user manager and no
`user@<uid>.service`, no process of `freedom-executor`, no sudoers drop-in, no
SA-2 artifact, no state or runtime directory, and no activation or cutover. The
five Python 3.14 packages are held, `/opt/freedom-route3/{code,venv}` is
published and verified, the dormant account exists without linger, and one
`tmpfiles.d` fragment is installed. The only boot-time effect is the fragment:
systemd creates the empty `/run/polkit-1/rules.d`, which `polkitd` then watches.
No rules file is placed there by this plan; an unexpected file there is a
finding.

This is the "separate maintenance action (safe: nothing auto-starts)" that P.2
and S3.1 require: S3 needs one boot after S1.4 with S2.2 at rc 0.

## 4. Before the reboot (read-only; nothing here changes the host)

- Peter's explicit go for the reboot, with named operator, window and
  escalation contact, and notice to the community of the Discord-bot and Foundry
  outage. Without that go, stop here.
- The host is at STOP-A **now**: block D and block F pasted in one root shell,
  then S2.1 returns rc 0 and prints `STOP-A verified`. Any other result is a
  stop; do not reboot.
- Nothing is mid-operation: no apt or dpkg process, no migration, import,
  backup or restore running, and no Route 3 process.
- A current backup set exists and its checksums pass (the
  [production-upgrade handback](../review/production-ubuntu-26-04-upgrade-handback.md)
  records the 2026-11-11 verification method). No new backup procedure is
  defined here.
- Boot-time expectations are known: record which services are active now and
  confirm which are enabled to start at boot. Any service that is active but
  not enabled, or that needs a manual start (for example a Foundry backend),
  needs its restart procedure written down before the window. Confirm that
  `freedom-web` is not enabled.
- Out-of-band access to the host (provider console) is available for a boot
  that does not return.
- Do not combine the reboot with any other change. The five phased Ubuntu
  updates remain deferred by apt policy and are not applied in this window.
- **No reboot may be planned between a future S3.5 and S4 or R3.** This one is
  before S3, which is the permitted interval.

### 4.1 Pre-reboot baseline observed read-only (preparation evidence only)

Observed read-only on production before any reboot, recorded so G1 and G2 have
something to compare against:

- boot id `09238f67-3a8c-418b-91af-9b9ac4ffc2a4` (the boot G1 must show has
  ended);
- bot, worker, PostgreSQL and Caddy: enabled and active;
- `freedom-web`: disabled and inactive;
- Route 3 supervisor unit: `LoadState=not-found`, `ActiveState=inactive`;
- no failed units listed;
- exactly these package holds: `libpython3.14-minimal`, `libpython3.14-stdlib`,
  `python3.14`, `python3.14-minimal`, `python3.14-venv`.

This observation is not execution authority. It does **not** replace the
accepted root S2.1 check immediately before the reboot, nor the attending
operator's backup, out-of-band and window checks above.

## 5. Gate sequence after the reboot (strict order; each gate must pass before the next)

| Gate | Check | Pass means | If it fails |
|---|---|---|---|
| G1 | Reconnect; confirm the boot is new (boot identity and uptime) and the host is the production host | a boot that started after the attended reboot | stop; see section 6 |
| G2 | Service health: bot, worker, PostgreSQL, Caddy active; `freedom-web` inactive; PostgreSQL reachable; Foundry HTTPS hosts answer as before the reboot; no warning-priority journal lines for this boot beyond known benign ones; no failed units | the 2026-11-11 baseline shape (31 samples over 30 minutes, zero restarts) or the bounded observation Peter sets | ordinary service recovery (section 6); Route 3 is not involved |
| G3 | Block D and block F in one root shell, then S2.1 | rc 0, `STOP-A verified`: the boot started nothing of Route 3 | stop and escalate; do not run R |
| G4 | S2.2 (`polkit_tmpfiles verify`) | **rc 0**. rc 12 is no longer acceptable after a boot | stop and escalate; rc 20 or any other status is a failed prerequisite |
| G5 | S2.3: the read-only v2 production checklist of [handback §6](../review/route-3-production-readiness-handback.md#6-production-specific-read-only-fact-checklist), plus the account-dependent sudo, Polkit, user-manager and process checks the runbook defers until after provisioning. Items about S3-only objects must report them **absent** | every item matches STOP-A | stop and escalate |
| G6 | Independent review (Codex or another reviewer named by Peter) of the G1 to G5 evidence | no finding | findings go to Peter; no S3 decision until closed |
| G7 | Peter records, in writing, whether to authorize S3 | S3 is a **separate, later decision** by Peter. G1 to G6 passing is a precondition, never the authorization | none |

Notes:

- G3 and G4 are the same two accepted blocks that were run before the boot;
  this document only fixes when to run them again. S2.2 requires block D.
- A `[rc=N]` line is the status; read the status, not the surrounding text.
- Record the results (times, boot identity, statuses, any deviation) in the
  [handback](../review/route-3-production-readiness-handback.md) as a new
  dated subsection, and update the status and handover in the same step.

## 6. Rollback and escalation boundaries

- A reboot is not rolled back. If the host does not return, or returns
  degraded: out-of-band console access and Peter. Do not "fix" the host with
  Route 3 blocks.
- A service that does not return is recovered by the normal, pre-existing
  procedures for that service. Route 3 is dormant and is not part of that
  recovery.
- **Do not run block R (rollback of S1) reflexively.** A reboot does not
  invalidate S1. R's package-set handling is an attended boundary (status 28)
  decided only by Peter from the evidence. Run R only on Peter's explicit
  instruction.
- **Never delete `/root/route3-evidence`** or the run evidence. Disposal is
  Peter's separate decision (runbook P.6).
- Escalate to Peter immediately for: S2.1 not rc 0; S2.2 not rc 0 after the
  boot; any Route 3 process, unit, linger file, sudoers entry, SA-2 artifact or
  state directory present; any file in `/run/polkit-1/rules.d`; any drift in the
  held packages; or anything that suggests the reboot started something.
- Out of scope and unauthorized here: S3.1 through S3.5, S4.1, the installer
  `install`, enabling linger, creating the sudoers drop-in, activation,
  migration or cutover, RB-1, and a reboot at any point between a future S3.5
  and S4 or R3 (the unit would be enabled and a boot would start it; runbook
  P.2 and P.6).

## 7. Related records

- [Provisioning runbook](executor-supervisor-provisioning-runbook.md): P.1
  stages, P.2 STOP-A, blocks D, F, S2 and R; S3 onward is a later, separate
  decision.
- [Cumulative handback](../review/route-3-production-readiness-handback.md):
  §6 checklist and §16 for the S1 result and post-reboot results.
- [Active handover](../review/Handover%20information),
  [status](../project-management/status.md),
  [active delivery plan](../project-management/active-delivery-plan.md).
