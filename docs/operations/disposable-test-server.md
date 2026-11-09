# Disposable Linux Test Server

**Active authority, 2026-10-12 — all levels of testing are authorized on this
disposable server.** This includes SSH and synchronization, dependency and
package installation, builds, network tests, root and systemd operations,
PostgreSQL changes, destructive database/migration drills, failure injection,
service restart, rollback/recovery and end-to-end tests. Reset the disposable
host when needed.

This authority does not extend to production or staging and does not permit
copying real secrets or player data to the test host. Continue to use synthetic
fixtures and the documented secret-excluding synchronization command.

[Active delivery plan](../project-management/active-delivery-plan.md) ·
[Active handover](../review/Handover%20information) ·
[Historical restriction archive](disposable-test-server-archive/README.md).
Agents that support skills should use the `run-suites` skill, which carries
this document's synchronization and execution procedure together with the
skip-count and serial-execution traps from `.agents/AGENTS.md`. The skill
checks the authority banner above first and cites both documents rather
than replacing either.

The server exists so that **Codex, Claude Code, Antigravity, and maintainers have full administrative (root) access** to execute end-to-end tests, destructive PostgreSQL migration drills, dependency builds, and system-level experiments in complete isolation from the production/staging host.

---

## 1. Machine Profile

| Property | Value |
|---|---|
| **Public IPv4** | `138.2.182.39` |
| **SSH Host Alias** | `oracle-test` (and direct IP `138.2.182.39`) |
| **Kernel Nodename** | `Test` (`uname -n`); distinct from the SSH alias |
| **User** | `ubuntu` |
| **Privilege Level** | Full passwordless `sudo` (`sudo ALL=(ALL) NOPASSWD:ALL`) |
| **SSH Authentication** | Key-based via `~/.ssh/id_ed25519` from this host |
| **Operating System** | Ubuntu 26.04.1 LTS (x86_64) |
| **Kernel** | `7.0.0-1015-oracle` (Ubuntu `linux-oracle`; observed 2026-11-07). Production runs `7.0.0-43-generic`, a different flavour of the same 7.0 series |
| **Node.js** | v24.22.2, npm 11.19.1 (`/usr/bin/node`, `nodejs` 24.22.2-1nodesource1 from the NodeSource `node_24.x` source). Production runs the same 24.22.2, which Foundry v14 requires. The Foundry suite passed on it here on 2026-11-08 |
| **Python Virtualenv** | `/opt/freedom-blades/runtime/venv-web`, built with `/usr/bin/python3.14 -m venv` (Ubuntu archive `python3.14` 3.14.4-1ubuntu0.2); `pip` 26.3 inside it; installed from the committed requirement files with `requirements-web.lock` as the constraint (section 3.5) |
| **Python Manager** | `uv` (`/usr/local/bin/uv`) |
| **Database Server** | Ubuntu archive PostgreSQL 18.6 (`18.6-0ubuntu0.26.04.1`): the only cluster is `18/main` on port 5432 (`start.conf` `auto`, unit `postgresql@18-main` enabled, Unix socket `/var/run/postgresql`). PostgreSQL 16 was removed after the synthetic migration and restore drills; `~/.postgresqlrc` and `/etc/postgresql-common/user_clusters` name `18 main`. **Cluster policy:** one Ubuntu-packaged cluster, archive packages only; no third-party PostgreSQL source (the former `apt.postgresql.org` source was removed). The apt sources are Ubuntu `resolute*` and NodeSource `node_24.x` |
| **PostgreSQL Roles** | `ubuntu` (superuser, local peer auth), `freedom_runtime_test` (restricted role: `NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS`, granted to `ubuntu`) |
| **Databases** | `freedom_test` (test lane), `freedom_dev` (development lane) |
| **Client Utilities** | `/usr/lib/postgresql/18/bin` explicitly prepended to `PATH` in test invocations (no global `/usr/local/bin` client symlinks) |
| **Memory accommodation** | 951 MiB RAM plus a persistent 2 GiB `/swapfile` (in `/etc/fstab`), added after pytest was OOM-killed; pytest retains only failed temporary paths. Two vCPUs; observed CPU steal of 12-31 percent and heavy swapping make a full bot run take 25 minutes when quiet and over two hours when not |
| **Repository Path** | `/opt/freedom-blades/platform` (owned by `ubuntu:ubuntu`) |

---

## 2. Access Configuration

The host configuration is established in `~/.ssh/config` on the primary development/staging server:

```ssh-config
Host oracle-test 138.2.182.39
    HostName 138.2.182.39
    User ubuntu
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking accept-new
```

The alias is the canonical route and works from an unsandboxed session
(`ssh -G oracle-test` and `ssh -o BatchMode=yes oracle-test true` both exit 0).
Inside a sandboxed agent session whose user namespace maps only uid 1000, OpenSSH
rejects the system client configuration with `Bad owner or permissions`, because
**every** root-owned path (`/etc`, `/usr`, `/tmp`, not only
`/etc/ssh/ssh_config.d` and its systemd target) then shows as `nobody:nogroup`
and sudo is refused by `NoNewPrivs`. That is an artifact of the sandbox, not an
on-disk or production defect: unsandboxed, the directories are `root:root 755`
and the target `root:root 644` (verified 2026-11-07). Do not bypass the system
configuration or "repair" ownership in response to that message; run the route
from an unsandboxed session instead. Only where the maintainer has explicitly
authorized it for a sandboxed session, `ssh -F ~/.ssh/config oracle-test`
(the same host, user and identity, ignoring only the misowned system file) may
carry already authorized disposable-host work; it is not canonical evidence that
the route works, and the secrets-guarded `rsync` shape has no such variant.

---

**Never run the database-marked suites anywhere but `oracle-test`.** The
repository checkout also exists on the production host, where role `foundry` owns
the production `freedom_*` databases. Several cases run bare `psql`, `pg_dump` and
`pg_restore` that cannot follow a custom socket, so even a scratch cluster there
leaves them on production's default server (2026-11-08: production's
`freedom_test` was reset and its migration downgraded; repaired and disclosed in
the handback). `tests/conftest.py` now refuses a `TEST_DATABASE_URL` that names a
non-default socket directory or port.

## 3. Agent Usage Instructions (Codex & Claude Code)

### 3.1 Running Administrative (Root) Commands

The `ubuntu` user has unrestricted, passwordless `sudo` rights. To run any administrative or system-level command:

```bash
ssh oracle-test "sudo <command>"
```

Examples:
- Restarting or inspecting PostgreSQL: `ssh oracle-test "sudo systemctl status postgresql"`
- Installing system packages: `ssh oracle-test "sudo apt-get install -y <package>"`
- Managing files or services: `ssh oracle-test "sudo systemctl restart <service>"`

### 3.2 Synchronizing Code to the Disposable Server

Before executing tests or scripts on the disposable server, sync the latest workspace state. Note that `--include='.env.example'` must precede `--exclude='.env*'` to ensure tracked example configuration is transferred while secrets remain excluded. Do not use broad `--delete-excluded`:

```bash
rsync -avz --delete \
  --include='.env.example' \
  --exclude='.env*' \
  --exclude='*.pem' \
  --exclude='*.key' \
  --exclude='*service_account*.json' \
  --exclude='*credentials*.json' \
  --exclude='__pycache__/' \
  --exclude='*.py[cod]' \
  --exclude='.pytest_cache/' \
  /opt/freedom-blades/platform/ oracle-test:/opt/freedom-blades/platform/
```

**Secrets guard (LAB-V6-P3 remediation r1, accepted 2026-09-19).** The repository secrets guard admits this command only in the documented shape: one plain `rsync` invocation whose exclusion values are **single-quoted**. It still refuses double-quoted or unquoted exclusion values, `--exclude-from`, a secret named as a source or destination, and any command that chains, substitutes, redirects or comments. Do not rewrite the command to get past a refusal; a refusal is a stop condition. [Independent review](../review/project-review-2026-09-19-lab-v6-p3-secrets-guard-remediation.md).

### 3.3 Running Test Suites Against PostgreSQL

The test database `freedom_test` is created on the authoritative PostgreSQL 18
cluster and owned by `ubuntu`. Run pytest directly using the remote Python 3.14
virtual environment with the PostgreSQL 18 client path, the database URL and
the current small-host accommodations:

```bash
ssh oracle-test "cd /opt/freedom-blades/platform && \
  PATH='/usr/lib/postgresql/18/bin:/usr/bin:/bin' \
  TEST_DATABASE_URL='postgresql+psycopg:///freedom_test' \
  /opt/freedom-blades/runtime/venv-web/bin/python -m pytest -q -rs -o tmp_path_retention_policy=failed tests/web"
```

To run a single test module:
```bash
ssh oracle-test "cd /opt/freedom-blades/platform && \
  PATH='/usr/lib/postgresql/18/bin:/usr/bin:/bin' \
  TEST_DATABASE_URL='postgresql+psycopg:///freedom_test' \
  /opt/freedom-blades/runtime/venv-web/bin/python -m pytest -q -o tmp_path_retention_policy=failed tests/web/test_structural_guards.py"
```

Run the three suites **serially**, at the **default descriptor limit**
(soft 1024, hard 524288): the bot suite `tests/test_*.py`, then `tests/web`, then
the Node suite. Do not raise the limit: `ulimit -n 4096` lowers the hard limit too
and changes the skip count. The `-o tmp_path_retention_policy=failed` option and
the swapfile are the only small-host accommodations.

Observed 2026-11-08 on the final tree (Python 3.14.4, PostgreSQL 18.6, Node 24.22.2,
the refreshed dependency set of section 3.5), all green:

| Suite | Result |
|---|---|
| `tests/test_*.py` | 7,571 passed, 0 failed, 0 errors, **337 skipped**; the skip reasons are identical to the 2026-11-07 run (the five extra passes are tests added since) |
| `tests/web` | 2,893 passed, 0 failed, **80 skipped** (the database-enabled count) |
| Foundry Node suite | 171 passed |

The 337 bot skips all print a reason: 267 need root, `/usr/bin/python3.14` and the
pinned jeepney wheel, 42 need real root ownership, 16 need the unprovisioned
`RP11_LAUNCH_BUILD_ROOT`, 7 need root and the real apt, 2 need a non-owner role
holding table grants, 2 need `RLIMIT_NOFILE` above the hard limit, 1 needs root
and a running systemd. The count belongs to user `ubuntu` at the default limit.
Timing is host-dependent: about 25 minutes for the bot suite and 16 for web when
the host is quiet, over an hour when it is CPU-starved (steal) and swapping.
Quote a figure only from a run of the tree being submitted.

### 3.4 Running Frontend / Node.js Tests

Node.js 24 (the version Foundry v14 and production use) is installed and supports the Node built-in test runner:

```bash
ssh oracle-test "cd /opt/freedom-blades/platform && node --test 'foundry-module/tests/'*.test.mjs"
```

### 3.5 Updating Python Dependencies

The virtualenv is rebuilt from the Ubuntu interpreter and the committed
requirement files. `requirements-web.lock` is the resolved web set (a clean
install of `requirements-web-dev.txt` plus `pip freeze`) and is used as a
**constraint**, so the web packages are exactly the locked ones while the bot
packages resolve within their declared ranges:

```bash
ssh oracle-test "cd /opt/freedom-blades/platform && \
  rm -rf /opt/freedom-blades/runtime/venv-web && \
  /usr/bin/python3.14 -m venv /opt/freedom-blades/runtime/venv-web && \
  /opt/freedom-blades/runtime/venv-web/bin/python -m pip install -q --upgrade pip && \
  /opt/freedom-blades/runtime/venv-web/bin/python -m pip install -c requirements-web.lock -r requirements-dev.txt -r requirements-web-dev.txt && \
  /opt/freedom-blades/runtime/venv-web/bin/python -m pip check"
```

To refresh the lock, install `requirements-web-dev.txt` alone into a scratch
venv, `pip freeze`, keep the file's header, and record every version change in
the handback. The tests forbid the Google libraries and jeepney in the web lock.

The direct requirements carry an upper bound on the next incompatible series (the
accepted dependency contract, section 1.5), and since the 2026-11-08 pre-production
currency refresh those bounds sit one series above the then-current releases rather
than at the Phase 3 snapshot. When a bound is raised, the sequence is: edit the
bound, regenerate the lock from a clean install on this host, confirm it reproduces
byte for byte on a second clean install, rebuild the runtime venv as above, then run
all three suites serially. `pytest.ini` turns a `SADeprecationWarning` into an
error, so a SQLAlchemy deprecation surfaces as a failure on the next bump. Also
re-run a live uvicorn with `tools.portal_server.install_access_log_redaction()`
installed and check that a request carrying `?code=` is logged as `?<redacted>`: the
N-7 redaction depends on uvicorn's access-line format, which the source-reading test
`tests/web/test_n7_access_log_redaction.py` pins.

---

## 4. Resetting the Disposable Environment

If a test corrupted the database or filesystem:

1. **Re-create the PostgreSQL 18 test database:**
   ```bash
   ssh oracle-test "PATH='/usr/lib/postgresql/18/bin:/usr/bin:/bin' dropdb -U ubuntu --if-exists freedom_test && PATH='/usr/lib/postgresql/18/bin:/usr/bin:/bin' createdb -U ubuntu freedom_test"
   A freshly created `freedom_test` reports a few extra bot-suite skips until a web run has granted the runtime role; restore a verified dump instead of recreating it if the skip count matters.
   ```
2. **Re-sync the repository tree safely:**
   ```bash
   rsync -avz --delete \
     --include='.env.example' \
     --exclude='.env*' \
     --exclude='*.pem' \
     --exclude='*.key' \
     --exclude='*service_account*.json' \
     --exclude='*credentials*.json' \
     --exclude='__pycache__/' \
     --exclude='*.py[cod]' \
     --exclude='.pytest_cache/' \
     /opt/freedom-blades/platform/ oracle-test:/opt/freedom-blades/platform/
   ```

For a recovery drill, stop all disposable writers, create a custom-format dump
and globals dump with PostgreSQL 18 tools, verify the dump checksum and
`pg_restore --list`, recreate only the named synthetic database, restore it,
and compare schema plus complete synthetic contents. Never use a production
dump or player data. The 2026-11-07 native PG18 dump/drop/restore drill passed
for all three databases included in that disposable drill; a later drill must
report its own reliable statuses rather than inheriting that result.
