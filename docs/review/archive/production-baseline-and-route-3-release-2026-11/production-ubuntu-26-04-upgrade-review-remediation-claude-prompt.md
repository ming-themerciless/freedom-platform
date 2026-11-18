# Claude remediation — production Ubuntu 26.04 / PostgreSQL 18 review

> **Correction, 2026-11-07.** The OpenSSH client "ownership defect" described
> below was not a production defect. The `nobody:nogroup` owners and `Bad owner
> or permissions` came from the sandboxed agent session's user namespace (one
> mapped uid), where every root-owned path appears that way. Unsandboxed, the
> directories and target are `root:root` with the documented modes and ordinary
> `ssh oracle-test` works; no repair was needed or authorized. The text below is
> kept unchanged as the assignment as written. See the production-upgrade
> handback, "SSH route: sandbox artifact, not a production defect".

Peter requested this remediation on 2026-11-06 after independent Codex
re-review. The production Ubuntu/Python/PostgreSQL work has already occurred.
This assignment validates and documents that result; it does not authorize any
new production write.

## Authority and safety boundary

Read the required repository entry documents before acting. Full administrative
and destructive testing is authorized on the disposable `oracle-test` host by
the active handover and `docs/operations/disposable-test-server.md`. You may
upgrade its synthetic test software and databases, reboot it, rebuild its test
virtualenv, and run every repository suite there.

Do not access or mutate production or staging. Do not recreate temporary sudo,
read secrets, copy production dumps or player data, start `freedom-web`, change
production services or package sources, or execute any Route 3 stage. Block F
remains `UNSET`. Preserve all unrelated working-tree changes.

The following facts are accepted inputs and must not be re-probed on
production:

- Peter confirms `/etc/sudoers.d/zz-claude-temp` was removed and `sudo -n true`
  fails with interactive authentication required.
- Production now runs Ubuntu 26.04.1, Python 3.14.4 and PostgreSQL 18.6.
- The first production write occurred at 15:27, before the authorized 16:00
  start. Only Peter can disposition that deviation.
- Production dumps were copied by Peter to his Mac. Do not claim that no player
  data left the production host; state the approved destination accurately.
- The current host's OpenSSH client refuses
  `/etc/ssh/ssh_config.d/20-systemd-ssh-proxy.conf` with `Bad owner or
  permissions`. Read-only inspection found `/etc/ssh/ssh_config.d`,
  `/usr/lib/systemd/ssh_config.d`, and the packaged target owned by
  `nobody:nogroup`. This blocks canonical access to `oracle-test`; do not bypass
  the system configuration or change production ownership under this
  assignment.

## Required remediation

### 1. Establish the PostgreSQL 18 disposable test baseline

Inspect `oracle-test` first and record non-sensitive package, cluster and Python
facts. Then make PostgreSQL 18 the authoritative disposable test lane on port
5432 using Ubuntu-supported cluster tooling. Preserve or recreate only the
synthetic `freedom_test` and `freedom_dev` databases and the documented
restricted test-role shape. PostgreSQL 16 need not remain installed after all
recovery evidence below succeeds.

Before removing the PG 16 lane, create a synthetic PG 16 custom-format dump and
globals dump, verify their checksums and archive listings, restore them into PG
18, and compare schema objects, constraints, sequences and complete synthetic
table contents—not merely row counts. Also exercise a native PG 18 dump/drop/
restore cycle. Report reliable statuses and clean up only disposable artifacts.

Use the Ubuntu 26.04 archive packages unless the existing documented host facts
show an already accepted source. Do not add an unreviewed third-party package
source merely to obtain a version.

This work cannot start until Peter separately authorizes and completes the
production-host OpenSSH client ownership repair, or supplies another explicitly
approved administrative path to the disposable host. Treat the current SSH
failure as a stop, not permission to bypass system configuration.

### 2. Align the Python test runtime

Rebuild `/opt/freedom-blades/runtime/venv-web` on the installed Ubuntu
`/usr/bin/python3.14` and install the committed bot and web development
requirements reproducibly. Verify interpreter origin/version, `pip check`, and
the material application imports. Do not use or modify the unused production
paths under `/opt/discord-bots`.

### 3. Run the exact-tree suites serially

Synchronize the current workspace with the canonical secret-excluding command.
Against PostgreSQL 18, export the Unix-socket
`TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'`, use the PostgreSQL 18
client path, and run serially:

1. `tests/test_*.py`;
2. `tests/web`;
3. the Foundry Node test suite.

Use `-rs`, preserve each exit status, and report passes, failures, errors and
skips. The expected database-enabled skip count is 80; investigate any change.
Do not relabel a failure as pre-existing without an exact-tree comparison that
supports that statement. Run relevant migration/restore checks and
`git diff --check` after documentation changes.

### 4. Update canonical documentation from observed facts

Only after the disposable upgrade and tests succeed, update:

- `.agents/AGENTS.md` canonical suite commands;
- `docs/operations/disposable-test-server.md` machine profile, PostgreSQL and
  Python versions, cluster policy, client path, reset/recovery commands and
  suite examples;
- `docs/project-management/status.md`; and
- `docs/review/production-ubuntu-26-04-upgrade-handback.md`.

Do not edit historical snapshots to make them current. Do not state that a
production 30-minute PostgreSQL 18 observation occurred: only eight minutes are
currently evidenced. Keep that as a residual unless Peter separately supplies
new, bounded production observation evidence. Do not invent missing backup
hashes, the `postgres` dump size, or Peter's disposition of the early write;
name each missing input plainly.

Correct the handback so it distinguishes:

- the completed OS/Python service observation on PostgreSQL 16;
- the subsequent PostgreSQL 18 migration and its eight-minute observation;
- disposable PG18 compatibility/recovery evidence from production evidence;
- approved off-host backup handling from a false claim that no player data
  left the host; and
- completed temporary-sudo revocation from the still-open validation gaps.

The production package-source residual also remains explicit: NodeSource and
the empty Caddy source list are disabled, and restoring an update path is a
separate production decision.

## Return

Return one concise handback section in the existing production-upgrade handback
or a direct update to it; do not create another prompt/review chain. Include:

- actual disposable software versions and source/origin;
- PG 16-to-18 synthetic restore and native PG18 restore results;
- exact serial suite results and skips;
- canonical documents changed;
- unresolved production-only evidence or decisions; and
- confirmation that production, staging, secrets, player data, Route 3 and
  block F were untouched.

Do not commit or push. Stop and report if the PG18 restore, application suites,
database-enabled skip count, Python 3.14 runtime, or canonical documentation
cannot be made consistent on `oracle-test`.
