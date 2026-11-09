# Claude prompt — attended production upgrade to Ubuntu 26.04.1 LTS

Peter authorizes one bounded, attended production operating-system upgrade from
Ubuntu 24.04 LTS to Ubuntu 26.04.1 LTS, followed by installation or verification
of the official Ubuntu Python 3.14 packages and restoration of the existing
production services. Production may be unavailable for up to six hours.

This is an operating-system maintenance assignment, not Route 3 provisioning or
activation. It does **not** authorize S0.2, S1, S2, S3, S4, any Route 3 rollback
block, creation of the `freedom-executor` account, installation of Route 3
artifacts or units, sudoers or Polkit changes, a PostgreSQL major-version
migration, an application/database schema migration, Foundry mutation,
migration/cutover evidence execution or RB-1. Block F remains `UNSET`.

The production host holds real services and player data. Safety takes priority
over completing the upgrade. Any failed prerequisite, ambiguous observation,
unexpected package removal, lost recovery route or uncertain database state is
a stop. Never convert a failed check into permission to continue.

## Authority and required human inputs

Peter's delivery of this prompt authorizes the production reads and writes
explicitly described below, including `sudo`, ordinary Ubuntu package updates,
`do-release-upgrade`, the required reboot(s), official Ubuntu Python 3.14
package installation if needed, and stopping/restarting the existing services.
It authorizes no other production change.

Use only an already-supplied sudo capability. Do not create, edit or remove a
sudoers file, Polkit rule, account, role, token or cloud credential. Confirm
`sudo -n true` works before the window and never print `sudo -l`, environment
variables, process arguments or credential-bearing configuration.

Before the **first production write**, Peter must supply or confirm in writing:

1. the maintenance-window start and a six-hour end time;
2. Peter as the reachable rollback/escalation owner for the whole window;
3. a completed provider boot-volume snapshot, identified by a non-secret
   snapshot/backup identifier and completion status;
4. tested access to the provider recovery/serial console after SSH loss; and
5. the exact provider procedure Peter will use to restore the pre-upgrade boot
   volume if Claude requests rollback.

Do not infer these from an old snapshot, a configured CLI, a dashboard that was
not checked, or the ability to use SSH. Do not open cloud credential files or
attempt to create a provider snapshot unless Peter separately supplies a
reviewed provider-side procedure and authority. If any input is absent, perform
only the read-only preflight and return NO-GO.

## Amendments by Peter, 2026-11-06 (supersede the five inputs above)

* Window: 2026-11-06 16:00 to 22:00 UTC. Peter is rollback and escalation owner.
* No provider boot-volume snapshot. Peter accepts this risk. Rollback is a
  restore from Peter's own Mac backup (taken about 13:20 UTC; Peter states it
  holds the system and the PostgreSQL data). Claude could not inspect it. Peter
  was asked to copy the Phase C logical dumps to the Mac himself.
* Provider recovery console exists (IONOS); Peter did not test it for this
  window. Claude never uses it or any provider credential.
* Temporary sudo: Peter created `/etc/sudoers.d/zz-claude-temp`
  (`NOPASSWD:ALL` for `foundry`). The automatic revoke timer was stopped on
  purpose because it would have fired mid-window and would not survive reboots.
  **The file must be revoked manually when the window ends** (or earlier on
  stop/rollback), by Peter or by Claude on request:
  `sudo rm -f /etc/sudoers.d/zz-claude-temp`, then confirm that
  `sudo -n true` fails. Claude must not forget this: it is the last step of
  the window, a line in the handback, and a reminder to Peter at every stop.
* Virtualenvs: rebuild only `/opt/freedom-blades/runtime/venv-web` and
  `.../venv-bot` on Python 3.14 (the only ones referenced by units). The two
  `/opt/discord-bots/*` venvs are unused and are left alone.
* PHP: no PHP exists on this host; out of scope.

## Governing context

Before acting, read completely:

1. `.agents/AGENTS.md`;
2. the reading map and §§0, 9, 13, 14, 16, 17 and 20 of
   `docs/implementation-plan.md`;
3. `docs/review/Handover information`;
4. `docs/project-management/active-delivery-plan.md`;
5. `docs/operations/disposable-test-server.md`;
6. runbook part P in
   `docs/operations/executor-supervisor-provisioning-runbook.md`, for its
   current NO-GO and authority boundaries only—do not execute its blocks;
7. the failed release-preparation return supplied by Peter and the retained
   off-production evidence for revision
   `dc1167aac1c132c6f9e855717c0947a0c1ceb606`; and
8. Canonical's current Ubuntu Server release-upgrade guide and Ubuntu 26.04.1
   release notes, including the 24.04→26.04 changes and known issues.

Use only official Canonical/Ubuntu documentation for upgrade behavior. The
supported command is ordinary `do-release-upgrade`; never use a development-
release flag. Ubuntu 26.04 removes cgroup-v1 support, moves systemd 255→259,
OpenSSH 9.6→10.2 and the archive's default PostgreSQL major to 18. It also uses
`tmpfs` for `/tmp` by default. Treat those as explicit pre/post checks, not
incidental package churn.

Never read, print, copy or modify `.env`, tokens, passwords, private keys,
service-account files, database URLs, OAuth secrets, player records, process
environments or process argument lists. Backups may contain real data only on
production or in the provider's approved encrypted backup facility; never copy
them to `oracle-test` or the repository.

## Phase A — read-only production preflight

Run Phase A before the maintenance window and change nothing. Create no file or
directory on production. Capture only non-sensitive facts and reliable statuses
in the tool result and summarize them in the return; do not persist raw output
on the host. The result must not contain configuration contents, environment
values, command lines, secrets or player data.

Establish all of the following:

- the host is the intended production host and runs supported Ubuntu 24.04 LTS
  on the expected architecture;
- the CPU satisfies Ubuntu 26.04's architecture baseline and the host uses
  unified cgroup v2; cgroup v1/hybrid is a hard stop;
- the current kernel, boot mode, root/boot filesystems and cloud guest agent
  have no reported failure;
- root has at least 15 GiB free and `/boot` has at least 1 GiB free after old,
  safely removable package caches are accounted for; do not remove anything in
  Phase A;
- `dpkg --audit` is empty, APT/dpkg locks are idle, no reboot is pending and no
  package operation is running;
- the configured release-upgrade policy offers the next LTS without `-d`;
- every enabled APT source is classified by URL/suite/component without reading
  authentication material; third-party repositories and foreign packages are
  listed by package/source name only;
- held packages, locally modified packaged files and conffile prompts likely to
  affect SSH, networking, firewall, sudo, systemd, PostgreSQL or the application
  are identified without printing file contents;
- `sshd -t` succeeds, the current SSH connection method is compatible with the
  OpenSSH 10.2 changes, and provider recovery-console access has been confirmed;
- firewall/network policy will not block the release upgrader's documented
  fallback SSH path if it is offered;
- `pg_lsclusters`, package metadata and systemd status establish every
  PostgreSQL cluster, version, port and active unit; PostgreSQL 16 remains the
  required application cluster and no major-version migration is authorized;
- the exact application/service units that can write data are enumerated from
  the known Freedom Blades unit names and current system-manager facts, without
  printing their environment or command lines;
- all existing application virtualenv interpreter paths resolve, and their
  versions and ownership/mode are recorded without reading environment files;
- production Git/worktree state is recorded without inspecting ignored secret
  files; and
- the provider snapshot, console and rollback inputs above are current for this
  exact pre-upgrade state.

Read the upgrader's proposed package summary before allowing it to commit.
Removal of `openssh-server`, `sudo`, the active cloud guest agent, the active
PostgreSQL 16 packages/cluster tooling, the kernel/boot tooling needed by this
host, or a required Freedom Blades runtime dependency is a hard stop. A foreign-
package prompt that cannot be reviewed completely is a hard stop. Do not purge
foreign packages merely to make the prompt shorter; return the list to Peter.

## Phase B — disposable rehearsal

Before the first production write, perform a synthetic rehearsal on
`oracle-test`. Do not copy production configuration, secrets or data.

Prefer a nested Ubuntu 24.04 VM if hardware virtualization is available. If it
is not, use a disposable Ubuntu 24.04 VM through a supported software-emulated
path. Do not reset or erase the existing `oracle-test` host or its retained
Route 3 evidence. Reproduce only the material topology: SSH, unified cgroup v2,
PostgreSQL 16 with synthetic data, representative Freedom Blades systemd units,
the current virtualenv interpreter shape, official Ubuntu sources and the
expected boot/reboot path.

Exercise the complete attended 24.04→26.04.1 upgrade and reboot. Prove:

- reconnection after reboot;
- Ubuntu 26.04.1, systemd 259 and unified cgroup v2;
- SSH remains usable;
- the PostgreSQL 16 cluster and synthetic data remain intact and no PostgreSQL
  18 cluster replaces or takes the production port;
- `/tmp` becoming tmpfs does not break the representative services;
- the existing virtualenv shape remains executable;
- official Ubuntu sources offer `python3.14`, `python3.14-minimal` and
  `python3.14-venv` for the upgraded host;
- installing those packages, if absent, proposes no removal, downgrade or
  third-party source and leaves package state clean; and
- a simulated application stop/start and health check succeeds.

Record the exact rehearsal results, failures and cleanup. A failed or materially
different rehearsal blocks production. Do not waive it because the target
`oracle-test` host already runs 26.04; the upgrade path itself is the subject.

## Phase C — maintenance entry and recoverable backup

Enter Phase C only after Phases A and B pass and Peter supplies the five human
inputs. Announce the start of the six-hour window. As the first authorized
production write, create a private root-owned evidence directory with mode
`0700` and files mode `0600`; it must contain only fixed checkpoint names,
timestamps, non-sensitive facts and command statuses—never raw configuration,
environment values, command lines, secrets or player data. Write and sync a
checkpoint before each state transition.

1. Stop and verify stopped every Freedom Blades application writer, including
   the live bot, web and worker units and any discovered scheduler/timer. Do not
   disable Discord as a platform or touch Discord configuration.
2. Confirm no application process remains that can write PostgreSQL or Sheet
   state. Do not inspect its arguments or environment.
3. Take fresh logical PostgreSQL backups under a root-owned production-only
   `0700` directory using peer/local administrative access. Use one custom-
   format backup per non-template application database plus a globals/roles
   backup. Do not print data or credentials.
4. Require every backup command to return zero, record SHA-256 and size, and
   validate custom archives with `pg_restore --list`. Keep the files on
   production and inside the provider snapshot boundary; never commit or copy
   them to `oracle-test`.
5. Stop PostgreSQL cleanly, verify it is stopped, and ask Peter to confirm that
   the named provider snapshot represents this quiescent state. If the supplied
   snapshot predates quiescence, require a new completed snapshot or stop.
6. Restart PostgreSQL only if needed for the release upgrader, while keeping all
   application writers stopped. Record the exact decision.

No upgrade command may run until the logical backups and quiescent provider
snapshot are both confirmed.

## Phase D — attended Ubuntu upgrade

Keep the application services stopped throughout.

1. Refresh official 24.04 package lists and fully update the current release
   using Canonical's documented phased-update procedure. Review the transaction
   before accepting it. Do not re-enable or add a repository.
2. If the current-release update requires a reboot, verify checkpoints and
   backups, reboot, reconnect through the normal or recovery console path, and
   repeat the Phase-A health essentials before continuing.
3. Start ordinary `do-release-upgrade` inside a persistent attended terminal.
   Do not use `--devel-release`, unattended answer files or blanket automatic
   conffile replacement.
4. Review the complete package installation/removal summary. Apply the Phase-A
   hard stops. Third-party repositories may be disabled by the upgrader and
   must remain disabled afterward unless separately reviewed.
5. Preserve locally modified SSH, network, firewall, sudo, PostgreSQL, systemd
   and application configuration by default. Record `.dpkg-dist`/`.dpkg-old`
   conflicts for later review without printing contents. Never guess through an
   ambiguous boot-, network- or access-critical prompt.
6. Keep an independent SSH session or confirmed provider console available.
   Preserve every command's status. If the upgrader fails, do not repeatedly
   rerun it; assess the documented recovery state once and escalate to Peter.
7. Reboot only after the upgrader reports successful completion and package
   state is not partial. Record the reboot checkpoint first.

If SSH does not return within the agreed bound, use the confirmed provider
console. Do not make speculative bootloader, network or filesystem changes.
Request snapshot restoration when the cause or recovery is uncertain.

## Phase E — post-upgrade validation and Python 3.14 baseline

After reboot, keep application writers stopped until every required check is
green.

Require and record:

- Ubuntu 26.04.1 LTS, a supported kernel, systemd 259, unified cgroup v2 and no
  failed boot-critical unit;
- working SSH plus provider-console fallback;
- correct mounts, capacity, time synchronization, DNS and outbound access;
- `dpkg --audit` empty, no interrupted package state and only reviewed official
  Ubuntu 26.04 sources enabled;
- no unexpected sudoers, Polkit, account, unit or timer change;
- PostgreSQL 16 still owns the application port and its original data directory,
  starts cleanly and exposes the expected database/schema inventories without
  printing player data;
- any automatically created PostgreSQL 18 cluster is not on the application
  port and remains stopped/disabled; do not drop it, run `pg_upgrade`, change
  the application connection or migrate a cluster;
- logical backup files and their hashes still exist;
- every pre-upgrade virtualenv interpreter still resolves and imports its
  locked runtime dependencies; and
- the known application service definitions remain valid under systemd 259 and
  their write paths do not depend on persistent `/tmp` content.

Then establish Python 3.14 as a host baseline:

1. Query official Ubuntu package metadata for `python3.14`,
   `python3.14-minimal` and `python3.14-venv`.
2. If all are already installed, record exact versions, origins,
   `dpkg --verify` results and the resolved interpreter SHA-256.
3. If any is absent, simulate installation of the exact official-archive
   closure first. Require only new packages—no removal, downgrade, third-party
   origin or unrelated upgrade. Review every exact `name=version` and origin,
   then install once and verify versions, `dpkg --verify`, interpreter path and
   SHA-256.
4. Do not add a PPA, `deadsnakes`, source build, `uv` interpreter, snap,
   alternative repository or manually downloaded binary. Do not place a hold;
   Route 3 package policy will be redesigned separately for a pre-existing host
   interpreter.

Do **not** run the old release-preparation S0.0 after installing or observing
the packages. It assumes all top-level Python packages are new and is no longer
the correct procedure once Python 3.14 is part of the upgraded host baseline.
Block F remains `UNSET` pending a revised, independently reviewed Route 3
release-record procedure.

## Phase F — service restoration and observation

Run focused smoke checks before enabling writes. Start services in dependency
order, PostgreSQL first, then the web/worker/bot units that were running before
the window. Do not start a service that was previously stopped or disabled.

For each service require active state, stable restart count, its existing
non-mutating health check and clean high-priority logs without printing secrets
or player data. Confirm Discord connectivity only through the application's
safe health/status surface; do not send test messages to real channels. Confirm
the website through its local health endpoint and a synthetic/non-mutating
request. Confirm workers have not applied queued mutations twice.

Observe for at least 30 minutes. Any database identity mismatch, repeated
service crash, authorization failure, missing runtime, network instability or
unexplained state is a rollback/escalation condition. Stop application writers
again before rollback.

## Rollback and hard stops

There is no supported downgrade from Ubuntu 26.04 to 24.04. Rollback means
Peter restores the named pre-upgrade provider boot-volume snapshot while all
application writers are stopped. The logical database backups are a second
recovery source, not permission to improvise an in-place downgrade.

Request rollback immediately when:

- recovery console or sudo access is lost or uncertain;
- boot, root filesystem, networking, SSH or PostgreSQL cannot be made healthy
  within the attended window using documented non-destructive recovery;
- the active PostgreSQL 16 cluster/data directory or application database
  identity differs;
- the upgrade needs removal of a hard-stop package or an unreviewed third-party
  repository;
- package state remains partial or `dpkg --audit` is non-empty;
- application writers cannot be restored safely; or
- fewer than 90 minutes remain before the window closes without a stable,
  observed service state.

Do not erase failed-upgrade evidence, purge packages, drop a PostgreSQL cluster,
delete a data directory, rewrite Git history, disable security controls or
extend the window silently.

## Documentation, validation and return

If the upgrade succeeds, update only the concise current-state records needed
to state the new production OS/kernel/systemd/Python baseline, the exact
maintenance result, PostgreSQL disposition, service status, remaining Route 3
NO-GO and next action. Add one concise handback at
`docs/review/production-ubuntu-26-04-upgrade-handback.md`.

The handback must include:

- the maintenance window, named rollback owner and non-secret provider snapshot
  identifier/status;
- preflight and rehearsal results;
- backup types, statuses, sizes and hashes without paths or contents that expose
  secrets;
- the release upgrader's result, reboots and reliable statuses;
- final OS/kernel/systemd/OpenSSH/PostgreSQL/Python versions and origins;
- every package removal, disabled third-party source, conffile conflict,
  failure, warning and disposition;
- exact service stop/start/health results and the 30-minute observation;
- whether rollback was requested or performed;
- confirmation that no secret/player data left production, no Route 3 stage ran
  and block F remains `UNSET`; and
- the next action: independent review followed by a separate redesign of the
  Route 3 release-record/package procedure for pre-existing Python 3.14.

Run relevant repository tests on `oracle-test`, not production, against the
unchanged application tree. Production validation is limited to package,
service and non-mutating health checks. Do not run destructive tests or the full
pytest suites on production.

Do not commit or push. Preserve the two existing untracked Route 3 prompt files
and every unrelated change. Return the complete uncommitted documentation
candidate and operational handback for independent Codex review. Production
activation beyond restoring the pre-existing services remains unauthorized.
