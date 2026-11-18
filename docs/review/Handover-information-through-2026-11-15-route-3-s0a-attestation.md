# Active handover — production Ubuntu remediation and Lavalink residue removal complete; Route 3 remains NO-GO — 2026-11-11

**IMPLEMENTATION AND FULL DISPOSABLE-SERVER TESTING AUTHORIZED**

## Production continuation — current state

The attended privileged continuation completed the previously open Ubuntu
26.04 production work: logrotate is healthy; SSH explicitly uses
`PermitRootLogin prohibit-password`; the packaged `bwrap-userns-restrict`
profile replaced the stale local version; unused `/opt/discord-bots/venv*`
paths were removed; NodeSource and the official Caddy source are enabled; Caddy
2.11.9 and Node 24.22.2 are current; production `venv-web` and `venv-bot` were
rebuilt from the tested dependency set; eligible Ubuntu security updates were
installed; and the temporary sudo grant was removed. Five Ubuntu-phased updates
remain deferred by apt policy, not by an operator hold.

All final backup checksums pass; all four custom dumps pass `pg_restore --list`;
the missing `db-postgres.dump` size is 2,042 bytes. The clean final observation
ran for 31 samples over 30 minutes: worker, bot, PostgreSQL and Caddy remained
active with zero restarts and zero warning-priority journal lines,
`freedom-web` remained inactive, PostgreSQL stayed reachable and its log had no
`ERROR`, `FATAL` or `PANIC`. The single earlier PostgreSQL FATAL was the
operator's root-user `pg_isready` probe (`role "root" does not exist`), not an
application or data failure; later probes ran as `postgres`.

**Lavalink residue — removed and verified (2026-11-11).** Apt's restart scan
exposed an active, enabled `lavalink.service` running
`/opt/lavalink/Lavalink.jar`. Music is removed under OD-40, so it was prohibited
production residue with no platform consumer, and Peter explicitly authorized
complete removal on 2026-11-11. That removal is done: service stopped and
disabled; unit and enablement link, `/opt/lavalink` (logs, plugins, cache) and
the service's private temp directories deleted; `lavalink` account (UID 995) and
group (GID 996) deleted after confirming nothing else was owned by them;
`openjdk-17-jre-headless` plus `ca-certificates-java`, `java-common` and
`libpcsclite1` purged after a simulation showed no unrelated removal. No
process, port 2333, unit, path or account remains, and the worker, bot,
PostgreSQL and Caddy stayed active with zero restarts and zero warning-priority
journal lines (`freedom-web` inactive). No music configuration or credential was
read. The maintainer removed the final stale Lavalink reference from the
protected repository-local `.env` on 2026-11-11 without exposing its contents.
No live music residue remains. Historical records are preserved.

Production now runs Ubuntu 26.04.1, Ubuntu Python 3.14.4 and Ubuntu PostgreSQL
18.6. The existing web and bot virtualenvs were rebuilt on Python 3.14; the
PostgreSQL 16 cluster was migrated to 18 and removed. Peter has clarified and
approved the governing pre-production policy: while the platform has not begun
production use, bring its supported operating system, database, runtimes,
dependencies and related infrastructure up to date before activation. That
approval covers the completed PostgreSQL 16-to-18 migration and retirement of
the superseded cluster. It does not activate Route 3 or waive migration,
recovery, testing, observation or independent-review evidence.

## Earlier snapshots, 2026-11-07 to 2026-11-09 — historical; superseded where they conflict with the section above

The sections from here through "Currency continuation" are dated snapshots kept
as evidence. Statements in them that production was unchanged, that root-only
work or evidence was blocked, that the upgrade was open, that observation was
partial, that hashes or sizes were missing, or that sources were disabled
describe the state **on the date given**. The 2026-11-09–11 attended
continuation above resolved them. Disposable-host facts and suite figures
remain accurate as stated.

*Historical (2026-11-09 state), resolved.* The production upgrade was then not
closed. Peter accepted the first production write at 15:27 UTC, before the
authorized 16:00 window, as a documented process deviation on 2026-11-09. The
final PostgreSQL 18 service state had then received eight rather than 30
minutes of observation, and the final backup hashes and the `postgres` archive
size were not yet recorded in the handback. NodeSource and the empty Caddy
source were then disabled, and the retained `.dpkg-dist`/`.dpkg-old` files had
not yet been reviewed. Later: the 31-sample/30-minute observation was clean,
the backup hashes and sizes are recorded (see above and the handback), and
NodeSource and the Caddy source are enabled; the stale `bwrap-userns-restrict`
variant was replaced. This document does not assert a further review of any
other retained conffile variant.

There is **no production OpenSSH ownership defect**. The `nobody:nogroup`
owners and `Bad owner or permissions` seen earlier were an artifact of the
agent session's sandbox: its user namespace maps only uid 1000, so every
root-owned path (`/etc`, `/usr`, `/tmp`, `/usr/bin/ssh`, not only the SSH files)
showed as `nobody:nogroup`, and sudo was refused by `NoNewPrivs`. Unsandboxed
verification on 2026-11-07 (Peter's, repeated by the remediation agent) found
`/etc/ssh/ssh_config.d` and `/usr/lib/systemd/ssh_config.d` `root:root 755`, the
packaged target `root:root 644`, `ssh -G oracle-test` exiting 0 and ordinary
BatchMode `ssh oracle-test true` exiting 0. No ownership repair was needed,
authorized or made, and the system SSH configuration was never bypassed. The
sandbox diagnosis stays in the handback as evidence; the route is used from an
unsandboxed session.

## Disposable baseline and exact-tree suites

`oracle-test` runs Ubuntu 26.04.1, Ubuntu Python 3.14.4 and Ubuntu PostgreSQL
18.6 on port 5432. PostgreSQL 16 was removed after PG16-to-PG18 synthetic restore
comparison; a native PG18 dump/drop/restore drill also passed. The host has a
persistent 2 GiB swapfile. All data there is synthetic.

After the R2 remediation the exact-tree suites are **green** at the default
descriptor limit (2026-11-07): bot 7,566 passed, 0 failed, 0 errors, 337
skipped (two complete runs, identical skip lines, each with a printed reason);
web 2,892 passed, 0 failed, 80 skipped; Foundry 171 passed. R2 fixed the changed
`s04b-sync.argv`, the five undeclared evidence harness files, the Python
3.14/libffi descriptor reaching the H-1 role, the roughly 970 descriptors the RP-11
roles leaked (they never closed their journal), a test that needed a real
environment file, and a snapshot-import idempotency gap, and refreshed
`requirements-web.lock` on Python 3.14. `ulimit -n 4096` is not needed and
changes the skip count (it lowers the hard limit too, so four 70,001-descriptor
tests skip). The H-1 change alters that Route 3 artifact's digest; block F stays
`UNSET`.

## Assignment and boundaries (historical R2 assignment, 2026-11-07)

Peter assigned Claude the bounded
[Ubuntu 26.04 / PostgreSQL 18 remediation R2](production-ubuntu-26-04-upgrade-review-remediation-r2-claude-prompt.md).
Its work is returned in the production-upgrade handback and the independent
Codex re-review found no remaining repository or disposable-host finding. The
tested `soupsieve` 4.0.1 lock is accepted under Peter's pre-production currency
instruction. The prompt authorizes no production application/schema mutation,
player-data inspection, `freedom-web` activation or Route 3 stage. At that date
production evidence was still open: journal warning/error counts and the backup
hashes and sizes (both needed privilege the remediation account lacked). Both
were collected later in the attended privileged continuation (see above).

The old Route 3 S0.0 procedure assumed Python 3.14 was absent and no longer
applies (S0.0 is withdrawn in the runbook and only refuses). Every block-F
release identity remains `UNSET`; Route 3 stays NO-GO.

**Release-record redesign implemented 2026-11-11 (uncommitted; awaiting
independent review).** Runbook part P, "Release-record procedure", and the
stdlib-only, read-only tool `tools/route3_release_record.py` attest the
already-installed Python 3.14 closure (pinned set held, base set re-checked),
validate block F (no `UNSET`, bound to a committed baseline record), reproduce
the archive/manifest from a published revision and check the SA-2 tree digest.
New runbook blocks: S0.A (unprivileged attestation) and S0.3 (installed-baseline
gate). No release value has been supplied and no production or staging host was
inspected. Codex's independent review (same day) reached `oracle-test` and found
two blocking defects and one important one, remediated in the same uncommitted
tree: installed packages are now bound to the **signed-archive** packages through
a payload reference (`reference.record`, field `ROUTE3_REFERENCE_SHA256`) rather
than to the host's own dpkg metadata; the plan has **no install path** and every
mutating block reruns the whole trusted attestation (`route3_gate`) itself; and
per-member archive origins are compared exactly. The remediated tree still needs
its `oracle-test` run and a Codex re-review. See the
[handback](route-3-production-readiness-handback.md), "Release-record redesign
return" and "Independent review remediation". Route 3 stays NO-GO until that is
re-reviewed and Peter separately authorizes any production step.

**Final exact-tree evidence recorded 2026-11-12 (supersedes the "still needs its
`oracle-test` run and a Codex re-review" sentence above; the earlier paragraph is
kept as history).** After the second review round (S4.1 now runs the full gate
before starting the supervisor), Codex ran the exact reviewed, still-uncommitted
tree on `oracle-test`: `tests/test_route3_release_record.py` 269 passed (unprivileged);
focused provisioning rerun 24 passed, 210 deselected; full
`tests/test_provisioning_plan.py` as root 234 passed (56 min 21 s); canonical bot
suite 7,853 passed, 250 skipped (skip reasons limited to the documented
root/ownership/real-apt/systemd/RLIMIT/non-owner-role/RP-11 toolchain conditions);
web 2,893 passed, 80 skipped; Foundry 171 passed, 0 skipped. This validates the
uncommitted candidate, **not production**. Route 3 remains NO-GO, all block-F
release values remain `UNSET`, and no production/staging mutation, provisioning,
installation, activation, commit or push occurred. Next controlled step:
publication/commit of the exact reviewed candidate, then a separately authorized
production read-only S0.A attestation to populate the release identities; S1, S3
and S4 remain separate gates. See handback §13.1.

**Isolated apt reference generation complete (2026-11-14; uncommitted).**
After two independent corrections (variant builds must match the baseline, and
sources must not use `arch=amd64` while selecting `amd64v3`), the real
`oracle-test` proof is green. libc was brought current to `2.43-2ubuntu2.7`;
the isolated signed Ubuntu indexes selected `amd64v3`; the interpreter reference
matched `be9a2a5e...`; and `verify-host` accepted all 32 closure members
(`baseline` SHA-256 `497a3915...`, `reference` SHA-256 `5d6a3ee7...`). Exact
disposable results: release-record **346 passed**; provisioning as root **234
passed**; bot **7,928 passed, 252 skipped**; web **2,894 passed, 80 skipped**;
Foundry **171 passed**. Failed intermediate attempts and their disposition are
retained in handback §14. Route 3 remains NO-GO, every block-F value remains
`UNSET`, and production/staging were untouched.

**S0.A production attestation done (2026-11-15; record-only candidate committed and published). This supersedes the immediately preceding historical sentence that every block-F value remains `UNSET`, and every earlier `UNSET`/"S0.A next" statement.** The read-only S0.A returned rc 0 (32 members, plain `amd64`, interpreter `52e0a13e...`). Baseline record `cf9931cd...` and payload reference `31d744c7...` (generated on `oracle-test` with no architecture variant) are in `docs/operations/`. Block F is now **complete**: `ROUTE3_RELEASE_REV` is the already published deployable revision `26757f2ab67eb5be4f576dbc2166db5df8870857`, and the archive (`50f74b4f...`), manifest (`18e6794d...`) and SA-2 (`5e195c40...`) digests were reproduced on `oracle-test`; `check-fields` is `ok`. Codex reproduced the four identities and accepted them. Route 3 remains NO-GO (no artifact delivered; S0.1-S0.3, S1, S3 and S4 not run); no lasting operational production mutation occurred. **Next step:** The record-only candidate is committed and published on `origin/docs/platform-plan`; the next controlled step is separately authorized artifact delivery followed by read-only S0.2/S0.3. S1/S3/S4 stay separate and Route 3 remains NO-GO. See handback §15. Final exact-tree results on `oracle-test` (Codex): `tests/test_route3_release_record.py` 350 passed in 851.41 s; `tests/test_provisioning_plan.py` as root with the pinned wheel 235 passed in 4738.60 s; archive, manifest, SA-2 and `check-fields` values independently reproduced. No change requiring a rerun followed except this evidence-only documentation update.

## Currency continuation (2026-11-08) — historical snapshot

*Superseded by the current section above where it conflicts: the findings and
open items below were resolved on 2026-11-09–11.*

A sandboxed session on the production host (no sudo, no `oracle-test` route; the
sandbox was not bypassed) closed what was reachable without privilege. Production
Node 24.22.2 is the newest 24.x and Foundry v14 requires Node 24 (Node 26 is not
a Foundry runtime); the Foundry suite passed on it from the working tree (171).
Ubuntu archive packages were fully current. Caddy 2.10.2 then trailed upstream
2.11.9 (adapted configuration identical) and the NodeSource and Caddy update
paths were disabled. Conffile variants were compared by content. New findings
then: `logrotate` was failed on production (duplicate `cloud-init` logrotate
files), and the production `venv-web` was still the pre-R2 lock. A scratch-cluster web run
accidentally reached **production's `freedom_test`** through bare `psql`/`pg_dump`
children; it was disclosed and repaired (0013, schema owner/ACL/comment), and
`tests/conftest.py` now refuses every hostname except the disposable host
identity `Test` before resolving a database target. Database suites run on
`oracle-test` only (still in force). Details and the then-open privileged
to-do list (since completed): the handback's "Currency continuation".

## Dependency currency (2026-11-08, `oracle-test`)

Every stale direct Python bound was raised and the web lock regenerated: FastAPI
0.162 (Starlette 1.10 transitively), uvicorn 0.54, cryptography 50, SQLAlchemy 2.1,
py_webauthn 3, pytest 9, pytest-asyncio 1.x, python-multipart 0.0.33; no upstream
incompatibility required a pin, and the deliberate exclusions are unchanged. One
compatibility defect was fixed (a SQLAlchemy 2.1 `DISTINCT ON` deprecation, now an
error under `pytest.ini`), and uvicorn 0.54's access-line format was re-verified
against the N-7 OAuth-code redaction with a live process. `oracle-test` now runs
Node 24.22.2 like production. The exact-tree suites are green on that set: bot 7,571
passed, 337 skipped; web 2,893 passed, 80 skipped; Foundry 171 passed. Details: the
handback's "Dependency currency return". Independent review accepted the changes
and updated `.agents/AGENTS.md` with these figures and the dedicated-host guard.

*Historical (2026-11-09 decision and disposable-host check).* Peter selected
`PermitRootLogin prohibit-password` for production and confirmed that obsolete
`/opt/discord-bots/venv*` paths may be removed after verifying they are unused.
On `oracle-test`, the SSH policy was made explicit in a root-owned drop-in and
validated after reload; `/opt/discord-bots` was already absent, and bounded
process, open-file, `/proc`, unit and cron checks found no legacy-venv
dependency. Those disposable-host results claimed no production change at the
time; both production actions were then applied in the attended continuation
described in the current section above.

Every earlier snapshot in this document is superseded, where it conflicts, by
the completed continuation in "Production continuation — current state". No
host-remediation action remains open. Route 3 release preparation,
provisioning and activation remain separate and prohibited. Historical
snapshots are not rewritten.

[Current status](../project-management/status.md) ·
[Active delivery plan](../project-management/active-delivery-plan.md) ·
[Production-upgrade handback](production-ubuntu-26-04-upgrade-handback.md) ·
[Disposable test server](../operations/disposable-test-server.md)
