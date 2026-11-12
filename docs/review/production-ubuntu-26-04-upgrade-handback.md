# Production Ubuntu 26.04.1 upgrade — handback

Status: upgrade completed; R2 remediation independently re-reviewed with no
remaining repository or disposable-host finding. Peter has confirmed that bringing the supported OS, database,
runtimes, dependencies and related infrastructure up to date before production
use is the intended policy. That confirmation approves the completed PG16-to-
PG18 migration and retirement of the superseded cluster; it does not waive the
remaining recovery, compatibility, observation or review evidence.

The first disposable-host remediation below established the PG18 and Python 3.14
environment and restore evidence but was not green; the **R2 return at the end of
this record supersedes its suite results: the exact-tree suites are green** at the
default descriptor limit, and the SSH "defect" was a sandbox artifact. Production
evidence is partly open (journal counts and backup hashes need privilege the
remediation account lacks). Authority:
`production-ubuntu-26-04-upgrade-claude-prompt.md` with Peter's 2026-11-06
amendments and his later in-window instruction to migrate PostgreSQL 16 to 18
(the prompt excluded that migration). No Route 3 stage ran; block F remains
`UNSET`.

## Window and recovery

* Authorized window: 2026-11-06 16:00 to 22:00 UTC; Peter was
  rollback/escalation owner. The first production write and checkpoint occurred
  at 15:27, 33 minutes before the authorized start. This is an authority
  deviation pending Peter's explicit disposition; it is not treated as an
  amended window.
* No provider snapshot (risk accepted by Peter). Rollback source: Peter's Mac
  backup (~13:20 UTC) plus the logical dumps Peter copied to the Mac. Those
  production-data backups left the host under Peter's direct handling; they
  were not copied to the repository or `oracle-test`.
* Provider recovery console was not tested for this window and was never used.
* Rollback was neither requested nor performed.

## Preflight and rehearsal

* Phase B rehearsal (synthetic 24.04.5 VM on `oracle-test`, 2026-11-05) passed:
  `do-release-upgrade` rc=0, 26.04.1, systemd 259, cgroup v2, PostgreSQL 16
  intact on 5432 with no PG 18 cluster, `/tmp` tmpfs, Python 3.14 packages
  installed by the upgrader itself. Details in
  `production-ubuntu-26-04-upgrade-prerequisites.md`.

## Backups (on production only)

Custom-format dumps of `freedom_dev`, `freedom_staging`, `freedom_test` plus a
globals dump, taken twice with writers stopped (15:27 and 16:00). Every
checksum verifies and every custom archive passes `pg_restore --list` (checked
again after the upgrade). Sizes: 247,462 / 297,737 / 261,400 bytes; globals
1,032 bytes. The 16:00 set was confirmed by Peter as copied to the Mac. A third
set taken immediately before the PG 16 to 18 migration is in
`pg16-final/` beside them; these dumps are the recovery source now that the PG 16
cluster is gone, and remain until Peter says they can be deleted. The handback
does not yet contain the recorded SHA-256 values or the `postgres` archive's
size; those evidence fields remain to be supplied. Archive listing is not a
restore test, and no restore of this final set has been reported.

## Upgrade

* 24.04 `dist-upgrade` rc=0, reboot 1 (15:44), then ordinary
  `do-release-upgrade` in a tmux session, started 16:04:55, complete 16:22:55,
  reboot 2 into kernel 7.0.0-43.
* Proposed removals reviewed and accepted: keyboxd, libimobiledevice6,
  libxmlsec1t64, libxmlsec1t64-openssl, mesa-va-drivers, mesa-vdpau-drivers,
  packagekit-tools, python3-lib2to3. 128 new, 883 upgraded. No hard-stop
  package affected.
* The upgrader's second prompt (119 obsolete packages, including
  `postgresql-16`, `postgresql-client-16`, `libicu74`, old 6.8 kernels,
  `python3.12*`) was answered **No** during the upgrade. After service
  restoration, at Peter's request, the reviewed simulation (no PostgreSQL
  dependency in it) was applied: `autoremove --purge` (95 packages: Python 3.12,
  g++-13, multimedia/mesa libraries, 6.8 kernel images/headers/tools), explicit
  purge of the 6.8.0-147/-149 kernel sets, `dpkg --purge` of 76 config-only
  entries, removal of orphaned `/lib/modules` directories, `apt-get clean` and
  the two dead `venv-*.py312-old` directories. `postgresql-16` was kept at
  this point and removed later (see PostgreSQL 16 to 18). Only kernel 7.0.0-43 remains; `dpkg --audit` empty;
  services unaffected.
* Conffiles: `bwrap-userns-restrict` and `fuse.conf` kept local (`.dpkg-dist`
  present); `ca-certificates.conf.dpkg-old` present, not reviewed.
* Third-party sources: NodeSource disabled by the upgrader (`nodejs`
  24.22.2 from NodeSource remains installed and working); the Caddy source list
  is empty. Both stay disabled pending a separate review.
* No upgrader failure; `dpkg --audit` empty.

## Final state

| Item | Value |
|---|---|
| OS | Ubuntu 26.04.1 LTS |
| Kernel | 7.0.0-43-generic |
| systemd | 259.9-0ubuntu0.1, unified cgroup v2, no failed unit |
| OpenSSH | 10.2p1-2ubuntu3.8, `sshd -t` ok |
| `/tmp` | tmpfs |
| PostgreSQL | 18.6-0ubuntu0.26.04.1 (Ubuntu 26.04 archive), cluster 18/main online on 5432; PostgreSQL 16 removed |
| Python | 3.14.4-1ubuntu0.2 for `python3.14`, `-minimal`, `-venv` (Ubuntu archive); `dpkg --verify` clean; interpreter SHA-256 `52e0a13e…cb41` |
| Caddy / Node | 2.10.2 / 24.22.2 |

**Correction (2026-11-07): there is no SSH client defect on the production
host.** Post-review verification had reported `/etc/ssh/ssh_config.d` and the
systemd-owned target of `20-systemd-ssh-proxy.conf` as owned by `nobody:nogroup`,
with OpenSSH refusing the configuration (`Bad owner or permissions`). That was
how the sandboxed agent session saw every root-owned path (see "SSH route:
sandbox artifact, not a production defect" below). Unsandboxed, the directories
are `root:root 755`, the packaged target `root:root 644`, and ordinary
`ssh oracle-test` works. No ownership was changed at any point.

## Virtualenvs

`venv-web` and `venv-bot` were rebuilt on `/usr/bin/python3.14`. Deviation
from the prerequisites draft: the old directory was moved aside to
`*.py312-old` and the new venv built at the original path, so no unit file
changed. The old directories were deleted after cleanup (see Upgrade).

* web: `requirements-web.lock`; bot: `requirements.txt` constrained to the exact
  versions the previous venv held. `pip check` clean for both; top-level imports
  succeed with `-I`; the web app modules import. Mode restored to `2775`
  `foundry:nogroup`.
* `systemd-analyze verify` is clean for all four units. The one warning
  concerns the system `xfs_scrub` slice, not an application unit.
* The two `/opt/discord-bots/*` venvs are unused and were left alone.

## Services

* `pm2-foundry` was stopped for the window and came back at boot; Foundry
  instances respond (HTTP 302 on 30001–30003), Caddy active.
* `freedom-bot` and `freedom-worker` were active before the window and had been
  disabled by the operator in step C7. They were re-enabled and started in the
  order worker, bot at 18:32; both active, 0 restarts, no warning-level log
  lines, Discord gateway connected and the bot logged in. `freedom-web` was
  disabled before the window and was left stopped.
* 30-minute observation (18:33–19:03) passed: 0 restarts and 0 warning-level
  log lines for bot and worker. The services were then stopped for the
  PostgreSQL migration and restarted on PG 18 (below). This observation proves
  the post-OS-upgrade PostgreSQL 16 state only; it does not satisfy the final
  PostgreSQL 18 observation requirement.

## PostgreSQL 16 to 18 (Peter's instruction, 19:37 UTC)

Peter authorised the migration because no production use of the databases had
started. Method: Debian `pg_upgradecluster -v 18 16 main` (dump/restore; PG 16
had data checksums off, so `pg_upgrade` in place was not used).

1. Observation closed, then `freedom-bot` and `freedom-worker` stopped
   (`freedom-web` was already stopped); no application session remained.
2. Final dumps (`freedom_dev`, `freedom_staging`, `freedom_test`, `postgres`,
   globals) written to a root-only `0700` directory on production, checksums
   verified, every archive passes `pg_restore --list`. Contents identical in size
   to the 15:27/16:00 sets.
3. Simulated `apt-get install postgresql-18`: 4 new packages, no removal. Installed
   18.6; no cluster was auto-created.
4. `pg_upgradecluster` rc=0. 18/main took port 5432; 16/main stayed on 5433,
   stopped, data directory untouched.
5. Verification before any writer started: exact row count of every base table in
   each database compared between the old and new cluster, identical (31 tables
   each; 5, 423 and 1 rows). Alembic version `0013` in all three. Roles are the
   same four; none stores a password, as in PG 16. `pg_hba.conf`, port, SSL and
   `max_connections` carried over; the new cluster has data checksums on.
6. Worker then bot restarted 19:38; Discord gateway connected; an application
   session was visible on `freedom_staging`. 8 minutes of observation: 0
   restarts, 0 warnings, 0 PostgreSQL `ERROR`/`FATAL`.
7. Then `pg_dropcluster 16 main`, purge of `postgresql-16` and
   `postgresql-client-16`, `autoremove --purge` (nothing further) and purge of
   config-only entries. `dpkg --audit` empty; only `/var/lib/postgresql/18`
   remains.

**Validation gap (as first written; partly superseded below):** the repository
suites were not run against PostgreSQL 18 and `oracle-test` still ran PG 16, so
the test environment did not match production. No application connection
setting was changed. The final PG 18 production service state received eight
minutes, not 30; **that observation gap is unchanged and is a production-only
residual**. The original production PG 16 cluster was removed before
independent review or a restore drill. The disposable-host work below supplies
PG 18 compatibility and restore evidence from synthetic data; it is not
production evidence and does not substitute for a production restore test.

## Open items

1. **Closed — temporary sudo revoked.** Done at Peter's request:
   `/etc/sudoers.d/zz-claude-temp`
   removed and `sudo -n true` now fails ("interactive authentication is
   required"). It was the last privileged action; the revocation checkpoint was
   written first.
2. Decide whether `freedom-web` should be started; it was off before the window.
3. Review the `.dpkg-dist`/`.dpkg-old` files. Classified by content on
   2026-11-08 (see "Currency continuation"): three are benign; the stale
   `bwrap-userns-restrict` AppArmor profile and `PermitRootLogin yes` need a
   privileged or Peter decision.
4. `/opt/discord-bots/venv*` are unused and now point at the removed Python
   3.12; delete on Peter's decision. Journal uses 2.1 GB.
5. Sudoers/Polkit/account comparison against a pre-window baseline was not
   possible (no baseline captured); no change was made by this work.
6. Obtain Peter's disposition of the 15:27 pre-window production write and the
   missing backup evidence fields. Do not reconstruct or invent either.
7. **Closed — no SSH defect; sandbox artifact.** The `nobody:nogroup` ownership
   was how every root-owned path looks inside the sandboxed agent session.
   Unsandboxed verification (Peter's, repeated in the R2 continuation) found the
   paths `root:root` and ordinary `ssh oracle-test` working. No repair was needed,
   authorized or made; see "SSH route: sandbox artifact, not a production
   defect".
8. Open decisions from the disposable remediation: see the list at the end of
   that section.

## Disposable PostgreSQL 18 / Python 3.14 remediation (2026-11-06/07)

Everything here ran on `oracle-test` with synthetic data. None of it is
production evidence. Production, staging, secrets, player data, Route 3 and
block F were not touched.

**Software and origin (observed).** Ubuntu 26.04.1; PostgreSQL 18.6
(`18.6-0ubuntu0.26.04.1`, Ubuntu archive); cluster `18/main` on 5432, enabled
and online after a reboot; Python 3.14.4 (`3.14.4-1ubuntu0.2`, Ubuntu archive),
`venv-web` rebuilt on `/usr/bin/python3.14`; `pip` upgraded to 26.3 inside it.
PG 16 had come from the third-party `apt.postgresql.org` (pgdg) source; the
cluster was dropped, `postgresql-16`/`postgresql-client-16` purged, and
`pgdg.list` moved aside (kept in `/var/tmp/pg16-to-18/`). No new source was
added. Stale PG 16 pointers in `~/.postgresqlrc` and
`/etc/postgresql-common/user_clusters` were repointed to 18. The restricted role
`freedom_runtime_test` (NOLOGIN, no superuser/createdb/createrole/replication/
bypassrls, granted to `ubuntu`) survived; `freedom_test` and `freedom_dev` exist.
A 2 GiB `/swapfile` (in `/etc/fstab`) was added because the first pytest run was
OOM-killed on the 951 MiB host.

**PG 16 to 18 synthetic restore.** Custom-format dumps of `freedom_test` and
`freedom_dev` plus a globals dump were taken from PG 16, checksum-verified and
listed with `pg_restore -l`, then restored into PG 18 (all exit 0; the globals
file reported only the expected "role already exists" for `postgres` and
`ubuntu`). A catalog and complete-content fingerprint (relations, columns,
constraints, indexes, triggers, functions, views, enums, sequences, and an
`md5` over every row of every table) matched between clusters except for three
PG 18 representation differences: NOT NULL now listed in `pg_constraint`, the
new `MAINTAIN` privilege bit, and CHECK/partial-index expressions deparsed with
casts on array elements (equal after cast normalisation). **Limit of this
evidence:** `freedom_test` holds 31 tables but one row (`alembic_version`), so
a synthetic probe database (two tables, 1,750 rows, jsonb/array/bytea/unicode,
bigserial, identity, standalone sequence, FK, CHECK, view) was added: rows and
sequence state were identical and sequences continued correctly. The probe
database has been dropped.

**Native PG 18 restore.** `pg_dumpall --globals-only` plus `pg_dump -Fc` of the
three databases, checksum and listing verified, each database dropped and
restored: the post-restore fingerprint was byte-identical to the pre-drop one
for all three.

**Suites, exact tree, serial, PG 18, `TEST_DATABASE_URL` exported.** Run with
`-rfEs -o tmp_path_retention_policy=failed` (a deviation from the canonical
`-rs`, needed for memory).

| Suite | Result |
|---|---|
| `tests/test_*.py`, Python 3.14 | 56 failed, 39 errors, 7,461 passed, 337 skipped (reproduced identically in a second full run) |
| `tests/web`, Python 3.14 | 2 failed, 2,890 passed, **80 skipped** (expected count met) |
| Foundry Node suite | 171 passed, 0 failed |

The first attempt of both pytest suites was killed by the kernel OOM killer
(exit 137) and produced no result; it is not counted.

**Classification of the failures, each against the same tree.**

* `test_r5_runner.py` (5 failed, 39 errors), `test_sheet_bootstrap_boundary.py`
  (1) and the two `test_p3_4_static_assets.py` web failures fail identically
  under Python 3.12 on PG 18. They are tree states, not the upgrade:
  commit `bc73738` removed a line from `tools/r5_runner/blocks/s04b-sync.argv`
  (313 to 288 bytes), so it no longer matches the pin its test asserts (it
  matched at `d216cb1`); the static-asset tests find five undeclared files under
  `tools/phase_5_0_evidence` and no untracked directory. None was changed here.
* `test_rp11_h1_artifact.py` (29 failed) pass on 3.12 and fail on 3.14.
  Cause: on Python 3.14 with libffi 8.2.0, `import ctypes` leaves a descriptor
  open on `libffi.so`; the tests assert no descriptor at or above 3 at role
  entry. This is a real 3.14 difference in the artifact Route 3 will run on
  production's 3.14. A later run with the descriptor limit raised showed 27, not
  29, failures; the 2-test variation is not explained.
* `test_worker_env_file.py` (21 failed, `Too many open files`) appears only in
  the full run. The `test_rp11_*` modules leak about 970 descriptors under both
  3.12 and 3.14, leaving the process just under the default 1024 limit; 3.14
  reaches 1,021. With `ulimit -n 4096` the full 3.14 run has no
  `test_worker_env_file` failures (33 failed, 39 errors, 341 skipped).
* The 3.12 full run (7 failed, 39 errors, 337 skipped) additionally failed
  `test_snapshot_database.py::test_two_concurrent_applies_of_the_same_input_produce_one_effect`
  once; it passed in the 3.14 runs and standalone under both. Treated as the
  known load-sensitive flake, not as an upgrade effect.
* The 337 bot-suite skips are the same in both interpreters (mostly root-only
  and unprovisioned-toolchain tests); they are not the 80 figure, which applies
  to the web suite.

**Python runtime checks.** Interpreter `/usr/bin/python3.14` 3.14.4; `pip check`
clean; 20 of 20 material application imports succeed with `-I`. The committed
dev requirements are version ranges, so the resolved set was recorded with
`pip freeze`, not pinned; `requirements-web.lock` is older than that set
(for example alembic 1.19.1 against 1.20.1) and was not touched.

**Canonical documents reconciled by Codex, 2026-11-07.** `.agents/AGENTS.md`,
the `run-suites` skill, the disposable-server runbook, current status, active
handover, active delivery plan, implementation-plan §§14 and 20, and the change
log now describe PG18/Python 3.14 and the observed non-green state. They retain
both bot skip counts rather than selecting one, use the descriptor limit and
failed-only temporary-path retention as provisional small-host accommodations,
and do not present a passing baseline. Historical snapshots were not rewritten.

Peter assigned one bounded R2 remediation to restore the canonical SSH route,
fix the classified suite failures and descriptor leaks, reconcile the 337/341
skip and H-1 variations, complete the bounded outstanding upgrade evidence and
update these current documents with fresh results. The production 30-minute
PG18 observation, backup evidence fields and 15:27 disposition have not been
invented.

**Decisions and evidence still needed (not resolvable from the disposable host).**

1. Peter's disposition of the 15:27 production write before the 16:00 start.
2. Backup SHA-256 values and the `postgres` dump size, not supplied; none
   invented here.
3. Production PG 18: only eight minutes are evidenced; a 30-minute observation
   would need new bounded production evidence.
4. NodeSource and the empty Caddy source stay disabled; restoring an update path
   is a separate production decision.
5. The `s04b-sync.argv` pin versus content, and the undeclared
   `tools/phase_5_0_evidence` files: a maintainer fix of the file, the pin or
   the declarations.
6. The libffi descriptor under Python 3.14 against the H-1 artifact's
   no-inherited-descriptor invariant and its tests; this affects the Route 3
   release procedure on production's 3.14 and was not touched.
7. The test-suite descriptor leak (about 970 in `test_rp11_*`) and whether the
   canonical procedure should raise the limit or the tests should be fixed.
8. The documents then described the non-green baseline; R2 has since made the
   suites green and updated them (items 5 to 7 are closed by the R2 return).

*Superseded by R2:* the scratch directory `/var/tmp/suite18/` and the old 3.12 venv
named here were removed after the R2 comparisons. Retained on `oracle-test`:
`/var/tmp/pg16-to-18/` (dumps, fingerprints and logs, 860 KB: the migration
evidence) and `/var/tmp/r2-evidence/` (final result logs, the skip list and the
tested package freeze, 200 KB).

## Confirmations

No secret or player data was copied to the repository, `oracle-test`, or an
unapproved third party. Production database dumps, which may contain player
data, were copied off-host only to Peter's Mac by Peter as the accepted recovery
source. No Route 3 stage, account, artifact, unit, persistent sudoers/Polkit
change or application schema migration ran. The temporary sudo grant was
removed after the window. The only database change is the PostgreSQL 16 to 18
cluster migration above, with no application schema change. Block F remains
`UNSET`.

Peter's 2026-11-07 pre-production currency decision approves that completed
major-version migration and removal of the superseded PG16 cluster because the
platform had not begun production database use. The first-write timing
deviation and the evidence gaps above remain separate and open.

The R2 return below is complete and has passed independent Codex re-review.
The production-only evidence and authority items remain open independently.

## R2 remediation return (2026-11-07)

**Outcome: complete for the repository and the disposable host; production
evidence partly complete, with the remainder blocked on privilege the remediation
account does not have.** The Python 3.14 / PostgreSQL 18 exact-tree suites are
green at the default descriptor limit. Nothing was committed or pushed. No
production state was changed, and no secret, player record, staging system,
Route 3 stage or block F was touched.

**Transport.** The first R2 session and the later sessions ran in a sandbox whose
user namespace maps one uid, so the canonical `ssh oracle-test` was refused there
(see the SSH section). The `oracle-test` work in the sandboxed later sessions used
an explicit `ssh -F ~/.ssh/config oracle-test` (same host, user and identity;
only the misowned system file ignored), as the maintainer authorized for that
sandbox. **One continuation session ran unsandboxed** (identity uid map,
`NoNewPrivs: 0`) and used the canonical route unchanged: plain `ssh oracle-test`
and the documented secret-excluding `rsync`. It produced the descriptor-leak and
snapshot-idempotency fixes, the lock refresh and the final serial suite runs below.
The explicit-`-F` transport is **not** evidence that the canonical route works; the
unsandboxed checks in the SSH section are. The secrets-guarded `rsync` shape was
used unchanged while a session could run it, and single files were otherwise copied
over the same explicit ssh and verified by SHA-256 (final proof below).

### SSH route: sandbox artifact, not a production defect

**Conclusion (confirmed 2026-11-07): there was never a production ownership
defect, so no repair was needed, authorized or made.** The first R2 session's
sandbox diagnosis is preserved below as evidence; the unsandboxed confirmation
follows it.

*Evidence from the first (sandboxed) R2 session, as recorded then:*

* The supplied sudo capability was unusable: `sudo -n true` was refused with "the
  no new privileges flag is set" (`NoNewPrivs: 1`, seccomp filter active). Per the
  prompt I stopped before the repair and did not recreate a capability.
* Cause of the observed `nobody:nogroup`: the session ran in a user namespace with
  a single mapped id (`/proc/self/uid_map` was `1000 0 1`, PID 1 of the session
  uid 1000). Every path owned by an unmapped id is shown as 65534, and that was
  **all** of the system: `/etc`, `/etc/passwd`, `/etc/shadow`, `/usr`,
  `/usr/bin/ssh`, `/etc/ssh/ssh_config`, `/tmp`, `/run/systemd` and
  `/etc/sudoers.d`, not only the three SSH paths. OpenSSH stats in that namespace
  and rejects the first system file it checks. Paths owned by uid 1000 (`~`,
  `~/.ssh`, the repository) showed correctly. That matched the earlier report
  that the route worked during the window (not sandboxed) and the later Codex
  reproduction (made from a sandboxed session).
* Limit at the time: strongly indicated, not confirmed from outside the
  namespace. `dpkg -V openssh-client` printed nothing and did not discriminate.
  The agent did not override the sandbox on its own authority, did not use `-F`,
  another client or a direct-IP route, and changed nothing.

*Unsandboxed confirmation (Peter's verification; repeated independently by the R2
continuation session, which ran with an identity uid map, `NoNewPrivs: 0`, no
seccomp filter):*

* `/etc/ssh/ssh_config.d` and `/usr/lib/systemd/ssh_config.d` are `root:root 755`;
  `/usr/lib/systemd/ssh_config.d/20-systemd-ssh-proxy.conf` is `root:root 644`;
  `/etc/ssh/ssh_config.d/20-systemd-ssh-proxy.conf` is a root-owned symlink to it.
* `ssh -G oracle-test` exits 0 and `ssh -o BatchMode=yes oracle-test true` exits 0,
  with the system configuration in force (no `-F` or other override).
* `sudo -n true` from that session is refused with "interactive authentication is
  required", so the temporary grant remains revoked and none was needed.
* The lesson for the runbook: `Bad owner or permissions` together with
  `nobody:nogroup` on **every** system path means "run from an unsandboxed
  session", not "repair ownership".

### Repository changes (all verified on `oracle-test`, Python 3.14.4, PostgreSQL 18.6)

| Group | Finding and change | Result |
|---|---|---|
| R5 runner pin | Commit `bc73738` removed `--exclude=yt-cookies.txt` from `tools/r5_runner/blocks/s04b-sync.argv` (313 to 288 bytes) in a repository-wide sweep of that name, without amending the hash-pinned R3 contract. Restored byte for byte from `bc73738^` (it can only exclude more), declared as one file in a scope allowlist. | `test_r5_runner.py` passes (was 5 failed, 39 errors) |
| Evidence inventory | Five undeclared files are live (imported by `review_manifest.py`, each other and the RP-11 suites) and are now declared by exact name; unknown siblings are still refused. The discovery test no longer needs this checkout to contain an untracked directory. | `test_p3_4_static_assets.py` passes |
| H-1 on Python 3.14 | `import ctypes` (via `adapters.rp11.holdfs`) makes libffi open and keep `libffi.so`, after the entry's start-up close pass. `infra/rp11-h1/rp11_h1.py` repeats the listing-based close and verify after the up-front imports and before any role; failure to list or close is exit 71. Five new tests fail on the old entry. | `test_rp11_h1_artifact.py` passes, 2 root-only skips with reason |
| Descriptor leak (~970) | The `hold` role (ACT journal) and the `cleanup` role (attempt journal) opened an evidence journal and never closed it; a real process exits right after, which hid it. Both now close it after their last line; `EvidenceSink` gained `close()` and `JournalAppender.close` is idempotent (a double close could hit a reused descriptor number). A crash-simulating fixture that never handed its journal to the role now closes it itself. Two regression tests fail on the original code and pass now. The leak across the four modules fell from about 970 to baseline. | Bot suite runs at the default 1024 limit |
| Test needing a real env file | `test_the_legacy_sheets_connector_still_exposes_read_and_write` passed only where a developer's dotenv file sat beside `config.py` and failed on the disposable host, which never receives one. It now sets inert placeholders, imports fresh and restores `sys.modules`. | passes |
| Snapshot-import idempotency | `apply` looks the request key up and only then reconciles. A same-key retry that overlapped its original could find the key absent, then a changed database, and be refused as stale/blocked where idempotency owes it the original result. Under CPU load 24 of 120 repetitions of the two concurrent-apply tests failed; none failed idle. `apply` now looks the key up once more before refusing (`_committed_retry`). A deterministic test that hides the committed row from the first lookup fails on the original code. A stale preview under a *new* key is still refused (tested). The same-input race test now accepts a typed stale/blocked refusal, which serial execution legitimately produces; the same-key race stays strict. | 120 of 120 pass idle and under load after the fix |
| Scope guard | `application/foundry/import_service.py` declared as one exact file. | passes |
| Lock | `requirements-web.lock` refreshed on Python 3.14 (below). | all entries equal the tested set |

**Release-identity consequence.** `infra/rp11-h1/rp11_h1.py` is part of the Route 3
artifact, so its digest changed (`6e535749…` to a new one); no document or test
pins the old digest. The `hold`/`cleanup` role change is in the same security-
sensitive family and needs the independent review Route 3 already requires. Block
F stays `UNSET`; the separate release-preparation redesign is still required.

### Dependency records

The web dev set was installed alone into a scratch Python 3.14 venv and frozen:
the same 46 packages, every change inside the declared ranges, no Google or
jeepney entry (tests forbid both). The refreshed file keeps its header plus a note.
Changes include alembic 1.19.1 to 1.20.1, SQLAlchemy 2.0.52 to 2.0.57, psycopg
3.3.4 to 3.3.8, pydantic 2.13.4 to 2.14.3 (core 2.46.4 to 2.50.4), anyio 4.14.2 to
4.16.0, click 8.4.2 to 8.5.1, cbor2 6.1.4 to 6.2.1, uvloop 0.22.1 to 0.23.0,
watchfiles 1.2.0 to 1.3.0, websockets 17.0.1 to 17.4 and the rest patch-level.
The transitive `soupsieve` moved from
2.9.2 to **4.0.1**, a major version of a library the project does not constrain
(`beautifulsoup4` 4.15.0 is unchanged and accepts it); the suites are green on it.
Peter's explicit pre-production currency instruction resolves this reversible
dependency choice in favour of the tested current lock; no separate exception or
downgrade is required.
`venv-web` was rebuilt from `/usr/bin/python3.14` with that lock as a pip
constraint plus `requirements-dev.txt` and `requirements-web-dev.txt`: `pip check`
clean, 20 of 20 material imports succeed with `-I`, and every lock entry equals the
installed version. The bot packages have no lock; the resolved set is 71 packages
(for example py-cord 2.8.1, google-api-python-client 2.201.0, google-auth 2.62.1,
cryptography 44.0.3, jeepney 0.9.0, pytest 8.4.2, pytest-asyncio 0.24.0). Nothing
was installed in production.

### Final exact-tree results (PostgreSQL 18, Unix-socket `TEST_DATABASE_URL`, serial)

Run with `-q -rfEs -o tmp_path_retention_policy=failed` (a superset of `-rs`; the
option and the swapfile are the small-host accommodations) at the **default**
limit (soft 1024, hard 524288), as user `ubuntu`, after every code change:

| Run | Result | Exit |
|---|---|---|
| Bot `tests/test_*.py`, run 1 | 7,566 passed, 0 failed, 0 errors, 337 skipped, 1 h 01 m (CPU-starved host) | 0 |
| Web `tests/web` | 2,892 passed, 0 failed, **80 skipped**, 17 m | 0 |
| Foundry `node --test` | 171 passed, 0 failed | 0 |
| Bot, run 2 | 7,566 passed, 0 failed, 0 errors, 337 skipped, 24 m | 0 |

The 337 bot skips are stable: the two runs' `SKIPPED` lines are identical (reasons
and locations), and each prints a reason: 267 need root, `/usr/bin/python3.14` and
the pinned jeepney wheel; 42 need real root ownership; 12 plus 4 need the
unprovisioned `RP11_LAUNCH_BUILD_ROOT`; 7 need root and the real apt; 2 need a
non-owner role holding table grants; 2 need `RLIMIT_NOFILE` above the hard limit;
1 needs root and a running systemd. The two `RLIMIT` skips are what is left of the
earlier 29-versus-27 H-1 and 337-versus-341 variation: `ulimit -n 4096` lowers the
**hard** limit too, so four 70,001-descriptor tests skip at 4096 and run at the
default limit. The one raised-limit diagnostic run (`ulimit -n 4096`, so soft and hard
4096; run last, as the prompt allows) exited 0 with 7,562 passed, 0 failed, 0 errors
and 341 skipped: the same 337 plus exactly the four tests that need 70,001
descriptors (two in `test_rp11_h1_artifact.py` and two in `test_rp11_pk_sn.py`),
whose skip lines name the 4096 hard limit. The outcome does not otherwise change.
A second diagnostic raised **only the soft** limit (`ulimit -Sn 4096`, hard left at
524288): 7,566 passed, 0 failed, 0 errors, **337 skipped**, exit 0, 24 minutes, the
same result as at the default limit. So the count does not depend on the number of
descriptors available, only on the hard limit (the 337 versus 341 difference).
(The first attempt at this run was lost when scratch files on the host were removed
while it ran; this is the rerun.)
No OOM kill occurred in these runs (the kernel's count stayed at the two kills of
the first, pre-swap attempt). Exact-tree proof: a SHA-256 manifest of every
non-ignored file (1,936) matched between the working tree and `oracle-test` except
seven documentation and skill-text files edited after the runs; no code, test, lock
or script differs.

**An interruption to disclose.** A first final sequence was stopped at 15:17 by a
stop script on the host that the session recording this did not start, and the
sequence was restarted at 15:22 on the corrected tree; the results above are the
restart's. The first sequence had found two defects of mine, both fixed before the
restart: my new descriptor regression test asserted an absolute zero that another
test's fixture could break (it now compares before and after), and the scope guard
rightly flagged the undeclared `import_service.py`. Its result is not counted.

Also run: `pip check` (clean); material imports with `-I`; the focused tests for
every change; `git diff --check` (clean); `python3 -B .claude/hooks/test_guards.py`
(40 cases, all passed: 26 refused and 14 allowed, exit 0).

### Production evidence (read-only, no sudo)

* **Service observation.** A fresh 30-minute poll (31 samples, one per minute,
  14:39 to about 15:09 UTC on 2026-11-07, `systemctl show` only) found
  `freedom-bot`, `freedom-worker`, `postgresql@18-main` and `caddy` active with
  unchanged monotonic start stamps and `NRestarts=0` in every sample, and
  `freedom-web` inactive. Their start times (bot 19:38:56, worker 19:38:41,
  PostgreSQL 19:38:10 on 2026-11-06) show no restart in the roughly 19 hours since
  the migration. **This is a state observation, not the requested log-level
  one:** the account is outside the `adm` and `systemd-journal` groups and has no
  sudo, so warning and error totals could not be counted. They remain a gap.
  `postgresql@18-main` reports `enabled-runtime`, which is how the Debian cluster
  generator presents an `auto` cluster; not a defect.
* **Backup evidence: not obtainable.** The final backup set is in a root-only
  `0700` directory. The SHA-256 values, sizes (including the `postgres` archive) and
  a `pg_restore --list` re-check need root; none was invented, and no backup was
  restored or read. The values still have to be supplied or collected by someone
  with the privilege.
* **Conffile variants and sources** (names, owner, mode and package metadata only,
  contents not read): `/etc/apparmor.d/bwrap-userns-restrict.dpkg-dist` (`root:root
  644`, package apparmor, local conffile kept), `/etc/fuse.conf.dpkg-dist` (`root:root
  644`, fuse3, local conffile kept), `/etc/ca-certificates.conf.dpkg-old`
  (`root:root 644`, no dpkg owner: generated by a maintainer script), and
  **newly found** `/etc/ssh/sshd_config.ucf-old` (`root:root 644`, no dpkg owner:
  ucf-managed). No file was changed. `nodesource.sources` is `Enabled: no` (URI
  `node_24.x`), `caddy-stable.list` is empty (0 bytes), `ubuntu.sources` lists only
  `resolute`, `-updates`, `-backports` and `-security`. `nodejs` 24.22.2-1nodesource1
  and `caddy` 2.10.2 stay installed with no update path; restoring one is a
  separate production decision.
* **Temporary sudo** remains revoked: `sudo -n true` from the remediation session
  fails with "interactive authentication is required", and no sudoers file was
  edited.

### Remaining risks and decisions

1. Peter's decision on the 15:27 early write (still undispositioned).
2. Missing production evidence needing privilege: journal warning/error counts for
   the observation, and the final backup SHA-256 values, sizes and listing.
3. NodeSource and Caddy update paths remain disabled; the four conffile variants
   are classified but unreviewed by a human.
4. The suites are green on this host; they remain slow on 951 MiB and a CPU-starved
   VM (an hour or more). A larger test host would be a cheap fix and is Peter's call.
5. Production's Node is 24, `oracle-test`'s is 22; the Foundry suite is green on 22
   there and, as of 2026-11-08, also on 24.22.2 from this working tree (171 passed).
   Installing 24 on `oracle-test` still needs an unsandboxed session.
6. `.agents/AGENTS.md` is a read-only mount in the sandbox that ran R2
   (`/proc/self/mountinfo`), a protection that was not bypassed, so R2 did not edit
   it. An agent with write access has since applied the suite-section update; its
   current text (bot 337 skips at the default limit with printed reasons, no
   raised limit, results 7,566 / 2,892 / 171, `ulimit -n 4096` adding four skips)
   was re-read after the runs and agrees with every figure in this return.

### Independent Codex re-review disposition (2026-11-08)

The R2 code, tests, lock refresh, safety boundary and evidence were reviewed with
no remaining Blocking or Important finding. An independent focused run on the
documented Python 3.14/PostgreSQL 18 disposable lane passed **940 tests**, with
the two expected hard-`RLIMIT_NOFILE` skips. A preceding invocation mistyped the
database name; the database safety guard refused it before any database test ran,
and the corrected canonical Unix-socket invocation is the result counted here.
`git diff --check` is clean. The `soupsieve` 4.0.1 lock choice is accepted under
Peter's explicit pre-production currency policy. R2 is closed for repository and
disposable-host remediation; it does not close the production-only items above or
authorize Route 3.

Next action: obtain the privileged production evidence and Peter's 15:27
disposition. Confirmation of untouched systems: production services, packages,
sources, conffiles, application data and schema, staging, secrets, player data,
Route 3 and block F were not changed or read by R2 or this re-review.

## Currency continuation (2026-11-08, sandboxed session on the production host)

Scope: close every item reachable without privilege. Peter's pre-production
currency policy was in force; production writes were authorized only as bounded
currency actions. The session ran **on the production host as `foundry`**, inside
the sandbox that maps one uid (`/proc/self/uid_map` `1000 0 1`, `NoNewPrivs: 1`,
seccomp active, groups `foundry,nogroup`). Observed proof of the blocker:
`stat /etc /etc/ssh` shows `nobody:nogroup`; `ssh -G oracle-test` exits 255 with
`Bad owner or permissions on /etc/ssh/ssh_config.d/20-systemd-ssh-proxy.conf`;
`sudo -n true` exits 1 ("no new privileges" flag); `journalctl` prints the
"not seeing messages from other users" hint; `/root` and the backup directory are
unreadable. Following the runbook, **`-F` and the sandbox were not bypassed**, so
nothing was done on `oracle-test` and no privileged production write was possible.

### Done

* **Node 24 and the Foundry suite.** Production's Node 24.22.2 is the newest 24.x
  (nodejs.org index, 2026-10-27). Foundry's requirements page says v14 needs Node
  24; Node 26 "Lithium" (26.13.0) is the current LTS but is **not** a Foundry v14
  runtime, so 24 is the correct pin, not a lag. The suite (pure, no network, no
  writes) ran from this working tree on Node 24.22.2: **171 passed, 0 failed,
  exit 0**. That is the Node 24 evidence for the repository; it is not the
  canonical `oracle-test` lane.
* **OS currency.** `apt-get -s dist-upgrade` against lists refreshed 2026-11-08
  (InRelease 00:30, timer 07:22): 0 upgradable, nothing new, `dpkg --audit` clean,
  only kernel 7.0.0-43 installed, no `reboot-required`. PostgreSQL 18.6 and
  Python 3.14.4 are the newest Ubuntu archive builds.
* **Third-party sources.** `nodejs` 24.22.2 is current but its source is
  `Enabled: no`, so no future 24.x security update will arrive. `caddy` 2.10.2 is
  behind upstream 2.11.9 (2026-11-05) and the archive only has 2.6.2: no path
  exists. A stock 2.11.9 binary (checksum verified, scratch directory, since
  removed) adapted a copy of the live Caddyfile to JSON **identical** to 2.10.2's
  (the unreadable gate import stubbed empty); a full `validate` was impossible
  because the TLS key is unreadable (correct). Both upgrades need root:
  re-enable `node_24.x`, add the Caddy stable repository, `apt-get install
  caddy`, `systemctl restart caddy`, then confirm services. Not done.
* **Conffile variants** (contents compared, nothing changed):
  `ca-certificates.conf.dpkg-old` is the previous generated list: five roots now
  `!`-disabled, four newer roots added, i.e. `update-ca-certificates` output, benign.
  `fuse.conf.dpkg-dist` is packaged comment text; the local file enables
  `user_allow_other`, kept deliberately. `sshd_config.ucf-old` equals the live file
  except the live one adds the newer comment block and `AcceptEnv ... COLORTERM
  NO_COLOR`; local `PermitRootLogin yes` was already in the old file. With
  `PasswordAuthentication no` (cloudimg drop-in) this is key-only root login:
  a hardening choice for Peter, not changed. `bwrap-userns-restrict` is the one
  with a substantive gap: the local profile is the 24.04 `abi 4.0` text with
  `px /**`; the 26.04 packaged one is `abi 5.0` with `pix` and `mediate_deleted`.
  Replacing it needs root and a bwrap check, so it stays an open privileged item.
* **Python currency.** The production `venv-web` is still the **pre-R2 lock**: 27
  packages differ from `requirements-web.lock` (alembic 1.19.1 vs 1.20.1,
  SQLAlchemy 2.0.52 vs 2.0.57, psycopg 3.3.4 vs 3.3.8, pydantic 2.13.4 vs 2.14.3,
  soupsieve 2.9.2 vs 4.0.1 and others); it also carries pytest. `freedom-worker`
  runs from it, so rebuilding it needs a service restart and was not attempted.
  `venv-bot` (live bot) is behind the newest in-range releases (for example
  aiohttp 3.14.3 vs 3.14.5, google-api-python-client 2.199.0 vs 2.201.0,
  SQLAlchemy 2.0.52); `pip` is 25.1.1 in both.
* **Newer-than-declared candidate set.** The declared ranges cap FastAPI
  (<0.116), Starlette (0.46.2 locked), uvicorn (<0.33), cryptography (<45),
  SQLAlchemy (<2.1), pytest (<9), pytest-asyncio (<0.25) and py_webauthn (<3).
  Installed uncapped in a scratch Python 3.14 venv: fastapi 0.162.2, starlette
  1.10.0, uvicorn 0.54.0, cryptography 50.0.2, SQLAlchemy 2.1.8, webauthn 3.0.1,
  pytest 9.2.0, pytest-asyncio 1.4.1; `pip check` clean. `tests/web` against it:
  **2,890 passed, 80 skipped, 2 failed**. The two failures are the incident below,
  not evidence about the set (they acted on the wrong server). This is **not a
  canonical run** and the ranges and lock were not changed: raising security-
  sensitive framework majors belongs on `oracle-test` with the bot suite and
  independent review. It shows the web suite is not blocked by them.
* **New production finding: `logrotate.service` is failed** (since 2026-11-08
  00:28:57 UTC; the earlier "no failed unit" no longer holds). A dry run
  (`logrotate -d` on a scratch state file) reports the deterministic error
  `cloud-init-base:1 duplicate log entry for /var/log/cloud-init-output.log`:
  `/etc/logrotate.d/cloud-init` (the orphan from the 24.04 package) and
  `/etc/logrotate.d/cloud-init-base` (26.04) are byte-identical and both match
  `/var/log/cloud-init*.log`. The same shape appears in public Ubuntu bug
  reports (not confirmed for 26.04). Fix, as root: remove `/etc/logrotate.d/cloud-init`
  (keeping `-base`), then `systemctl reset-failed logrotate; systemctl start
  logrotate`. Other logs are still rotated; the failing exit is the only symptom.
  `oracle-test` may have the same duplicate; it was not inspected.

### Incident disclosed: scratch test run reached production `freedom_test`

To obtain the web-suite evidence above I ran `tests/web` on this host against a
throwaway PostgreSQL 18 cluster (own socket directory and port), believing it
isolated. It was not: `test_identity_migration_backup_restore.py` and
`test_migration_0013_rollback_boundary.py` run bare `pg_dump`/`psql`/`pg_restore`
with only `--dbname=freedom_test` and deliberately strip every `PG*` variable, so
they connect to the host's **default** socket, i.e. production's cluster, where
role `foundry` owns `freedom_test`. Effects, found afterwards by read-only
comparison: that database's `public` schema was dropped and restored from a dump
taken a moment earlier (data identical; owner, ACL and comment reset) and migration
0013 was downgraded to 0012. `freedom_dev` and `freedom_staging` are not named by
those tests and were not addressed. `freedom_test` holds no application data and
no service uses it (staging is the one with a live session).

Repair (bounded to that database, recorded here as the only production write):
`alembic upgrade head` (0012 to 0013) through the repository, then `ALTER SCHEMA
public OWNER TO pg_database_owner`, `GRANT USAGE ... TO PUBLIC` and the default
comment. A `pg_dump -s` comparison against the scratch cluster at head differed
only in how PostgreSQL 18 deparses array casts inside CHECK constraints and one
partial index (semantically equal), as the earlier restore comparisons found.
Version is 0013, 31 tables, one `alembic_version` row. Unknowable: any table
privileges the database held before; the PostgreSQL log needed to prove none was
unreadable. The scratch cluster and files were removed. No other suite was run
here.

Repository defect fixed: `tests/conftest.py` now refuses (a failing, not skipping,
check) a `TEST_DATABASE_URL` whose socket directory or port is not the libpq
default, because the bare children cannot follow it. Regression tests in
`tests/test_database_safety.py` fail on the old conftest and pass now; the file
passes in full (129). The lesson also belongs in the runbook: **database-marked
suites run on `oracle-test`, never on the production host.**

### Still open (genuinely blocked by privilege or by decision)

1. Journal warning/error counts and the final backup SHA-256 values, sizes,
   `postgres` archive size and `pg_restore --list` re-check: need `adm`/root. Not
   invented.
2. Peter's disposition of the 15:27 write.
3. On production, as root and attended: remove the duplicate logrotate file;
   enable NodeSource 24 and add the Caddy repository, then upgrade Caddy; review
   and replace `bwrap-userns-restrict`; rebuild `venv-web` and `venv-bot` from the
   tested sets and restart `freedom-worker`/`freedom-bot` (a service-impacting
   step, not taken unattended); decide `PermitRootLogin yes`.
4. The 30-minute PostgreSQL 18 log-level observation.

Cleanup: scratch cluster, venv, downloaded Caddy, configuration copies and logs
were deleted; the working tree changed only in `tests/conftest.py`,
`tests/test_database_safety.py` and the documents. Memory notes could not be saved
(the memory directory is a read-only mount in this sandbox).

## Dependency currency return (2026-11-08, `oracle-test` via the authorized `ssh -F`)

Scope: Peter's instruction that supported dependencies be current before
production. Every direct Python bound in `requirements.txt`, `requirements-dev.txt`,
`requirements-web.txt` and `requirements-web-dev.txt` was checked against PyPI and
the accepted dependency contract (`phase-3-configuration-and-dependency-contract.md`
§1.2/§1.3/§1.5). No pin was found to be required by an upstream incompatibility;
the full tree is green on the newest releases. Nothing was committed or pushed and
no production state was touched. The database suites ran on `oracle-test` only
(hostname `Test`); the production host ran no database-marked test.

**Transport.** The session ran in the one-uid sandbox, so plain `ssh`/`rsync`
failed with the known `Bad owner or permissions` message. As authorized for this
session, `ssh -F /home/foundry/.ssh/config oracle-test` and the documented
secret-excluding `rsync` with `-e 'ssh -F …'` carried the work. That is not
evidence that the canonical route works (it does, unsandboxed).

### Bounds changed

| Package | Was | Now | Note |
|---|---|---|---|
| `fastapi` | `>=0.115,<0.116` | `>=0.162,<0.163` | pulls Starlette 1.10 |
| `uvicorn[standard]` | `>=0.32,<0.33` | `>=0.54,<0.55` | N-7 redaction re-verified live (below) |
| `webauthn` | `>=2.2,<3` | `>=3.0.1,<4` | py_webauthn 3 |
| `cryptography` | `>=43,<45` | `>=50,<51` | AES-256-GCM paths pass |
| `SQLAlchemy` (bot and web) | `>=2.0.36,<2.1` | `>=2.1.8,<2.2` | one deprecation fixed (below) |
| `pytest` | `>=8.2,<9` | `>=9.2,<10` | both dev files |
| `pytest-asyncio` | `>=0.24,<0.25` | `>=1.4,<2` | both dev files |
| `python-multipart` | `>=0.0.9,<0.1` | `>=0.0.33,<0.1` | floor only |

Unchanged because the bound is already at or above the newest release: `jinja2`
(3.1.6, `<3.2`), `itsdangerous` (2.2.0), `httpx` (0.28.1, `<0.29`),
`beautifulsoup4` (4.15.0), `alembic` (1.20.1, `<2`), `psycopg` (3.3.8, `<4`),
`python-dotenv` (1.2.4) and the RP-11 H-1 `jeepney` (0.9.0, `<0.10`, hash-pinned in
its own artifact lock, deliberately outside this refresh). `py-cord`,
`google-api-python-client` and `google-auth` carry no upper bound by design and
resolved to their newest (2.8.1, 2.201.0, 2.62.1). Deliberate exclusions (contract
§1.4: Redis, task queues, session/CSRF/JWT libraries, `pydantic-settings`, any
Google or jeepney package in the web lock) are unchanged; the web lock contains
none of them. SQLAlchemy 2.1 no longer pulls `greenlet`, which nothing uses (no
async engine anywhere in the repository), so it left the lock.

### Lock (`requirements-web.lock`, 48 entries)

Generated by installing `requirements-web-dev.txt` alone into an empty Python 3.14.4
venv and freezing, once on the repository host and once on `oracle-test`; the two
freezes are identical to each other and to the committed file. Changes against the
2026-11-07 lock: fastapi 0.115.14 to 0.162.2, starlette 0.46.2 to 1.10.0,
uvicorn 0.32.1 to 0.54.0, cryptography 44.0.3 to 50.0.2, pyOpenSSL 25.1.0 to
26.4.0, SQLAlchemy 2.0.57 to 2.1.8, webauthn 2.7.1 to 3.0.1, pytest 8.4.2 to 9.2.0,
pytest-asyncio 0.24.0 to 1.4.1.post1; greenlet removed; annotated-doc 0.0.5,
opentelemetry-api 1.45.2 and pyasn1_modules 0.4.2 added; the remaining 36 entries
unchanged. No Google or jeepney entry. `venv-web` on `oracle-test` was rebuilt with
the documented recipe (lock as constraint, plus both dev files): 71 packages,
`pip check` clean, every lock entry equal to the installed version, and the
top-level packages and the web application modules import with `-I`.

### Compatibility defects found and fixed

1. **SQLAlchemy 2.1 deprecation (production code).** `ReconciliationJobRepository.
   latest_stamps` used `select().distinct(expr)` for `DISTINCT ON`, which 2.1
   deprecates and a later 2.x removes. It now uses the PostgreSQL
   `distinct_on` extension (`adapters/web/repositories.py`); the compiled SQL is the
   same `DISTINCT ON (reconciliation_jobs.snapshot_id)`. Regression:
   `tests/web/test_sqlalchemy_current_series.py` (no database) fails on the old
   spelling with the `SADeprecationWarning` and passes on the fix, and `pytest.ini`
   now turns `SADeprecationWarning` into an error so the next bump fails loudly
   instead of scrolling past in the warnings summary.
2. **No other defect.** The first web run on the new set was green (2,892 passed,
   80 skipped) before that fix; nothing else needed changing. The two remaining
   warnings are third-party: httpx's per-request `cookies=` deprecation (httpx 0.28.1
   is the newest; raised by how the tests pass cookies, about 1,150 occurrences) and
   py-cord 2.8.1's use of `asyncio.iscoroutinefunction` (removal in Python 3.16). Both
   are upstream or test-side and are left, not suppressed.

### Security invariant check: uvicorn and the N-7 access-log redaction

`tools/portal_server.py` redacts the OAuth `code`/`state` query string and
pseudonymises the client address, and is pinned to uvicorn's exact access-line
format. Passing unit tests do not show that a newer uvicorn emits the same record,
so it was checked directly. The installed 0.54.0 source logs the identical format
and five arguments in `httptools_impl` and `h11_impl` and builds the client field
with the same `"%s:%d" % client`; `tests/web/test_n7_access_log_redaction.py`, which
reads that source, passes. A live uvicorn 0.54.0 process started with the unit's
`--factory --proxy-headers` shape and the real `install_access_log_redaction()`
logged `client-xxxxxxxx - "GET /auth/discord/callback?<redacted> HTTP/1.1"` on both
the httptools and h11 implementations with no code, state or address in the log.
Disclosure of an error in my own first probe: it did not call the installer (the
filter is installed by `application()`, not at import), logged the code in clear
text, and was discarded; the second probe above is the valid one. The comment at
`ACCESS_LOG_FORMAT` records the re-verification.

### Final exact-tree results (PostgreSQL 18, Unix-socket `TEST_DATABASE_URL`, serial)

Run with `-q -rfEs -o tmp_path_retention_policy=failed` at the default descriptor
limit as user `ubuntu`, bot then web then Foundry, on the tree after the last code
change (a SHA-256 manifest comparison follows the table):

| Run | Result | Exit |
|---|---|---|
| Bot `tests/test_*.py` (also run once earlier in the session on the same code) | 7,571 passed, 0 failed, 0 errors, **337 skipped**, 13 min | 0 |
| Web `tests/web` | 2,893 passed, 0 failed, **80 skipped**, 10 min | 0 |
| Foundry `node --test` (Node 24.22.2) | 171 passed, 0 failed, 0 skipped | 0 |

Both complete bot runs (the earlier 7,571 / 337 in 14 min 50 s and this one) have
byte-identical `SKIPPED` lines; the earlier first web run (before the `distinct_on`
fix and the new test) was 2,892 passed / 80 skipped. No `SADeprecationWarning`
remains in either suite; the only web warnings are the two httpx cookie lines. No
OOM kill (`dmesg` count 0) and no orphaned `rotate-test-gate`/`caddy validate`
process afterwards. `git diff --check` clean; `python3 -B .claude/hooks/test_guards.py`
passed all 40 cases (26 refused, 14 allowed).

The bot count is 5 above R2's 7,566 because the production-host session added
`test_database_safety.py` cases after that figure (three tests, two of them
parametrized to five items); the web count is one above 2,892 because of the new
regression test. The 337 bot skips carry the same printed reasons as before (267 /
42 / 16 / 7 / 2 / 2 / 1). Node was 24.22.2 on `oracle-test`, matching production.

### Not done, and why

* `.agents/AGENTS.md` was read-only to the implementing sandbox; the independent
  reviewer updated its suite figures and database-host rule after the return.
* Production's `venv-web` and `venv-bot` still hold the previous sets. Rebuilding
  them from the tested lock and requirements, with an attended restart of
  `freedom-worker` and `freedom-bot`, is a service-impacting production step that
  needs privilege and attendance and was not taken. The tested installs are on
  `oracle-test`.
* No other production item changed: logrotate, Caddy/NodeSource, `bwrap` profile,
  journal and backup evidence and the 15:27 disposition remain as listed earlier.

Cleanup: the scratch venvs and logs on both hosts and the staged scripts were
removed; the working tree changed only in the files listed in the status entry.

### Independent continuation review and disposable-host currency (2026-11-08)

Independent review found no remaining dependency-compatibility defect. The
SQLAlchemy `distinct_on` change preserves the compiled PostgreSQL query and the
clean lock is reproducible. `oracle-test` was brought fully current: Node/npm
24.22.2/11.19.1, 47 Ubuntu updates, stale generic kernels removed while
7.0.0-1015-oracle was retained, followed by a clean reboot. PostgreSQL 18 and
SSH are active; no package is upgradable; `dpkg --audit` and failed-unit checks
are clean. Post-boot database-safety passed 130 tests and Foundry passed 171.
The database guard was strengthened to require the dedicated hostname `Test`,
so production hostname `ubuntu` refuses before connecting; local refusal
coverage passed. The production incident's present state was checked read-only:
31 tables owned by `foundry`, migration 0013, and no non-owner table grants;
this cannot reconstruct unknown pre-incident ACL history.

A final continuation rechecked the two new safety areas after the disposable
host reboot: `tests/test_database_safety.py` plus
`tests/web/test_sqlalchemy_current_series.py` passed **131 tests**. Production's
five relevant services are active; `logrotate.service` remains failed; apt has
no archive upgrade to offer; Node is 24.22.2; both Python 3.14.4 virtualenvs pass
`pip check`, but still contain the older dependency sets; and Caddy remains
2.10.2. The PostgreSQL journal is not visible to this account, so an empty
unprivileged query is not treated as log evidence.

No unattended privilege path remains available in this session. `sudo -n` is
suppressed by the process `NoNewPrivileges` boundary; the forwarded SSH-agent
socket named by `SSH_AUTH_SOCK` is absent; clean-config, batch-mode localhost
root SSH is denied; and a system-manager transient unit is denied because it
requires interactive authentication. Consequently the root-only list above
cannot be completed or evidenced from this session. The final focused run's
remote caches were removed. One local `connectors/__pycache__` owned by the
sandbox-mapped `nobody:nogroup` remains because the same boundary denies its
removal; it contains only generated bytecode and is not a tracked change.

## Maintainer dispositions and disposable-host verification (2026-11-09)

Peter accepted the 15:27 pre-window production write as a documented process
deviation. He selected `PermitRootLogin prohibit-password` and confirmed that
obsolete `/opt/discord-bots/venv*` paths may be removed after verifying they are
unused. These decisions close the three maintainer-decision items; they do not
claim that the two production filesystem/configuration actions have run.

The selected SSH policy was applied on `oracle-test` as
`/etc/ssh/sshd_config.d/00-freedom-root-login.conf`, owned `root:root` with mode
0644. `sshd -t` passed, the effective policy is `permitrootlogin
prohibit-password` with `passwordauthentication no`, `ssh.service` reloaded and
remained active, and a fresh SSH connection succeeded. `/opt/discord-bots` was
already absent. Bounded checks found no `/opt/discord-bots/venv*` reference in
process command lines, open files, process executable/current/root paths,
systemd units or cron configuration. There was therefore nothing to delete on
the disposable host. It had no failed units, `logrotate.service` was not failed,
and `logrotate --debug /etc/logrotate.conf` completed successfully. `dpkg
--audit` and the upgradable-package list were empty, no reboot was required,
PostgreSQL 18 remained online, the Python 3.14.4 runtime environment passed
`pip check`, and no stale `bwrap-userns-restrict` conffile variant was present.

Remaining production work is unchanged except for those resolved decisions: an
attended privileged session must apply and verify the selected SSH policy and
legacy-venv removal, complete the other root-only remediation, and collect the
missing journal and backup evidence. Production and staging were not accessed
or changed by this continuation.

## Privileged production continuation and music-residue finding (2026-11-09–11)

Peter authorized the attended root-only continuation. It completed the open
Ubuntu remediation: the duplicate orphan `/etc/logrotate.d/cloud-init` was
removed (the retained `cloud-init-base` configuration validates and
`logrotate.service` succeeds); `PermitRootLogin prohibit-password` is explicit
and effective after `sshd -t` and reload; the Ubuntu 26.04
`bwrap-userns-restrict` profile replaced the stale version and loaded; and the
unused `/opt/discord-bots/venv` and `venv-web` trees were deleted only after
process, open-file, `/proc`, systemd, cron and Caddy reference checks were empty.

NodeSource 24 and the official Caddy stable source are enabled. Node remains
24.22.2; Caddy upgraded from 2.10.2 to 2.11.9, validated, restarted and returned
HTTP 302 through each Foundry backend and the HTTPS proxy. Production
`venv-web` was rebuilt exactly from `requirements-web.lock`; `venv-bot` was
built from `requirements.txt` constrained by that lock. Both Python 3.14.4
environments pass `pip check` and required imports. Worker then bot restarted
successfully; their pre-cutover environments were retained until the final
observation passed, then removed. Ten newly eligible Ubuntu archive/security
updates were installed; five phased updates remain deferred by apt policy. Apt
restarted `lavalink.service`, which exposed the separate residue finding below.

The final `pg16-final` backup evidence is now complete. All recorded checksums
pass and the four custom dumps pass `pg_restore --list`:

| File | Bytes | SHA-256 |
|---|---:|---|
| `db-freedom_dev.dump` | 247,462 | `27b87d5223c62bc2eb3635c49dc3355297039ea1c750ccdc6df667157321580a` |
| `db-freedom_staging.dump` | 297,737 | `531960eb25925675918b07b53b37136c48672e319e2da716e75ab99bae8eb7d8` |
| `db-freedom_test.dump` | 261,400 | `9219eb7ccc0453c4c73aaf8fc7b45026da1c3052dad6b360a67b0a139a0d5b6b` |
| `db-postgres.dump` | 2,042 | `26ed8b558e3e036a41dd75d41f7e6d2d4cd8a3c9bd68065f982eb2f648d9b24f` |
| `globals.sql` | 1,032 | `af65c4624d2d638886531ecfdc6dd7c820e3b9a27dec9ef61f435d8cc4bedec5` |

The final observation ran from 2026-11-10 00:26:30 through 00:56:32 UTC: 31
samples, worker/bot/PostgreSQL/Caddy active throughout with zero restarts,
`freedom-web` inactive, PostgreSQL reachable as `postgres`, zero
warning-priority lines for all four services and zero PostgreSQL
`ERROR`/`FATAL`/`PANIC`. One FATAL immediately after cutover was caused by an
operator `pg_isready` probe run as root (`role "root" does not exist`); it
preceded this observation and was not an application or data failure. The
temporary `/etc/sudoers.d/zz-codex-window` grant was removed and `sudo -n`
again fails.

**New finding and authority.** The apt restart scan exposed an active, enabled
`lavalink.service` executing `/opt/lavalink/Lavalink.jar` as the dedicated
`lavalink` account. OD-40 removed music completely; this live service is
prohibited residue, not a platform dependency. Peter explicitly directed its
complete removal on 2026-11-11: service/unit/enablement, runtime/config/log
paths and account/group, without reading music configuration or credentials.
Removal was then executed and verified; see the section below. Route 3 remains NO-GO.

## Lavalink residue removal — executed and verified (2026-11-11)

Executed by the authorized operator session under temporary sudo, about 01:06–01:08
UTC. Music configuration and credentials were not read: `/opt/lavalink/application.yml`
was only listed by name and size.

**Preflight.** `lavalink.service` (`/etc/systemd/system/lavalink.service`, enabled via
`multi-user.target.wants`, no drop-ins, no reverse dependents) ran `/usr/bin/java -jar
/opt/lavalink/Lavalink.jar` as `lavalink` (UID 995/GID 996, home `/opt/lavalink`,
`nologin`), listening only on `127.0.0.1:2333`. UID/GID 995/996 owned only paths under
`/opt/lavalink`; the only configuration references were the unit and its wants link; the
only Java process was Lavalink; `openjdk-17-jre-headless` was manually installed with
`ca-certificates-java` as its only installed reverse dependency.

**Removed.** Stopped and disabled the service (rc 0); deleted the unit and enablement
link and reloaded systemd (`LoadState=not-found`); deleted `/opt/lavalink` (87 MB: jar,
`application.yml`, YouTube plugin, `logs/`, `.cache/`) and the service's two
`systemd-private-*-lavalink.service-*` temporary directories; confirmed no remaining
file by owner UID 995/GID 996; `userdel lavalink` (rc 0, which removed the matching
group). `apt-get -s purge --auto-remove openjdk-17-jre-headless` proposed exactly four
removals — `openjdk-17-jre-headless`, `ca-certificates-java`, `java-common`,
`libpcsclite1` — all in the Java-only chain, with a plain `autoremove --purge`
simulation proposing none; the real purge ran (rc 0, 194 MB freed, `dpkg --audit` clean).
Platform packages and the CA bundle (`ca-certificates`, mtime unchanged) were not touched.

**Absence verified.** No `lavalink` unit file or loaded unit (`is-enabled`: not-found,
`is-active`: inactive); no `lavalink` or Java process; no listener on 2333; `/opt/lavalink`,
`/usr/lib/jvm`, `/etc/java*`, `/etc/ssl/certs/java` and private temp dirs absent; no
`lavalink` entry in `passwd`/`group`/`shadow`/`gshadow`, and no UID 995/GID 996; no
`*lavalink*`-named or unowned file outside the preserved evidence below; no reference
under `/etc`, `/usr/local` or cron, and no music timer. The only residues are
intentionally preserved: the 2026-11-09 pre-removal inventories under
`/var/backups/freedom-remediation-20261109T1724Z/lavalink-*.txt`, the systemd journal
history, repository documentation, and the system-maintained `/etc/passwd-`, `group-`,
`shadow-` and `gshadow-` rollback copies, which keep the former entry until shadow-utils
next rewrites them (they hold no credential for this service).

**Final protected-file closure.** A search for repository executable/configuration
residue outside `docs/` initially matched only the untracked repository-local `.env`
(by file name; its content was not displayed). The maintainer confirmed removal of the
stale Lavalink reference on 2026-11-11 without exposing the file's contents.
`.env.example`, code and `infra/` are clean; no live music residue remains.

**Platform health after removal.** `freedom-bot`, `freedom-worker`, `postgresql` and
`caddy` active and enabled with `NRestarts=0`; `freedom-web` inactive and disabled; no
failed units; zero warning-priority journal lines for bot, worker and Caddy since 00:50
UTC; PostgreSQL accepting connections. The PostgreSQL log shows `role "root" does not
exist` at 01:08:02 UTC — this operator's own root-run `pg_isready` health probe, the same
artifact described above, not an application error. Foundry backends 30001–30003 return
302 directly and through Caddy HTTPS (`-k`; the Cloudflare Origin certificate is not
publicly trusted, as before). Disk 41 % used, `dpkg --audit` clean. Observation, unrelated
to this removal: `freedom-blades.rpgworld.org` serves a static root
(`/opt/discord-bots/freedom-bot/design-prototype`) that does not exist, so it returns 404;
nothing under `/opt/discord-bots` was touched here. No commit, Route 3 action,
`freedom-web` activation, application/schema change, secret or player-data access occurred.

The temporary `/etc/sudoers.d/zz-codex-window` grant was revoked as the final privileged
step; the result is recorded in the operator's return.
