# Project status

## Current status — production Ubuntu remediation and Lavalink residue removal complete; Route 3 NO-GO — 2026-11-11

The attended production continuation closed the privileged Ubuntu remediation:
logrotate, SSH hardening, bwrap profile replacement, obsolete virtualenv
removal, NodeSource/Caddy sources, Caddy 2.11.9, production Python environments,
eligible Ubuntu security updates, backup hashes/listings and privileged journal
evidence are complete. A 31-sample/30-minute observation was clean: worker,
bot, PostgreSQL and Caddy active with zero restarts or warning-priority lines;
`freedom-web` inactive; PostgreSQL reachable with zero `ERROR`/`FATAL`/`PANIC`.
Five phased Ubuntu updates remain deferred by apt policy. The temporary sudo
grant was removed and passwordless sudo again fails.

Apt's restart scan exposed an active, enabled production `lavalink.service`
running `/opt/lavalink/Lavalink.jar`. OD-40 removed music completely, so this
was prohibited residue, not a platform dependency. Peter authorized complete
live-host removal on 2026-11-11 and it was **completed that day** (about 01:07
UTC): the service was stopped, disabled and its unit and enablement link
deleted; `/opt/lavalink` (including logs, plugins and cache) and the service's
private temporary directories were removed; the `lavalink` account (UID 995)
and group (GID 996) were deleted after a check that no other path was owned by
them; and `openjdk-17-jre-headless` was purged together with its Java-only
dependency chain (`ca-certificates-java`, `java-common`, `libpcsclite1`) after a
simulation showed no unrelated removal. Verified absent: unit, process, port
2333, paths, account/group and any `lavalink` reference under `/etc`, `/usr/local`
and cron (except the system-maintained `passwd-`/`group-`/`shadow-`/`gshadow-`
rollback copies, which keep the former entry until shadow-utils next rewrites
them). Worker, bot, PostgreSQL and Caddy remained active with zero restarts and
zero warning-priority journal lines; `freedom-web` stayed inactive; the three
Foundry backends and HTTPS hosts answer 302. No music configuration or
credential was read. The maintainer removed the final stale Lavalink reference
from the protected repository-local `.env` on 2026-11-11 without exposing its
contents. No live music residue remains. Historical music references remain
evidence and are not rewritten. The temporary sudo grant was revoked as the
final privileged step.

## Historical entries, 2026-11-07 to 2026-11-09 — superseded where they conflict with the section above

Everything from here through the OpenSSH paragraph is a dated snapshot kept as
evidence. Where it describes production as unchanged, root-only work or
evidence as blocked, the upgrade as open, observation as partial, backup
hashes/sizes as missing, or sources as disabled, that was the state **on the
date given** and was resolved by the 2026-11-09–11 attended continuation
described in the current section above and in the production-upgrade
handback. Suite figures and the Route 3 position below remain accurate as
stated.

**Dependency currency (2026-11-08).** The direct dependency bounds were raised to
the current releases and `requirements-web.lock` regenerated (reproduced
byte-for-byte on a second clean install): FastAPI 0.162 with Starlette 1.10,
uvicorn 0.54, cryptography 50, SQLAlchemy 2.1, py_webauthn 3, pytest 9,
pytest-asyncio 1.x. No upstream incompatibility required a pin; deliberate
exclusions and the security invariants are unchanged. One SQLAlchemy 2.1
deprecation in production code was fixed and is now guarded (`pytest.ini` turns
`SADeprecationWarning` into an error), and uvicorn 0.54's access-line format was
re-verified against the OAuth-code redaction with a live process. `oracle-test`
runs Node 24.22.2 like production. Exact-tree suites on `oracle-test`, serial:
**bot 7,571 passed, 0 failed, 0 errors, 337 skipped; web 2,893 passed, 0 failed,
80 skipped; Foundry 171 passed**. On that date production `venv-web`/`venv-bot`
still held the older sets; they were rebuilt from this tested set in the
2026-11-09–11 attended continuation. Independent review accepted the
dependency changes and updated `.agents/AGENTS.md`. See the handback's
"Dependency currency return". The paragraphs below are the state as of the R2
and currency-continuation entries; where they quote suite figures, the figures
above are current.

Production was upgraded from Ubuntu 24.04 to 26.04.1 LTS (kernel 7.0.0-43,
systemd 259.9, OpenSSH 10.2p1, Python 3.14.4 from the Ubuntu archive, Caddy
2.10.2 and Node.js 24.22.2). The web and bot virtualenvs were rebuilt on Python
3.14. PostgreSQL was then migrated from 16 to Ubuntu PostgreSQL 18.6 on port
5432; PG 16 was removed after row counts matched. `freedom-bot`,
`freedom-worker` and Foundry are running again; `freedom-web` remains stopped
as before. The temporary passwordless-sudo grant was removed and its negative
check passed.

Peter has approved the policy that supported OS, database, runtimes,
dependencies and related infrastructure are upgraded before the platform begins
production use. That approval covers the completed PostgreSQL 16-to-18
migration and removal of the superseded cluster. It does not waive backup,
restore, compatibility, observation or review evidence.

Disposable PG16-to-PG18 and native PG18 restore drills passed with synthetic
data. After the R2 remediation the Python 3.14/PG18 exact-tree suites are
**green** at the default descriptor limit: bot 7,566 passed, 0 failed, 0 errors,
337 skipped (two complete runs, identical skip lines, each with a printed reason);
web 2,892 passed, 0 failed, 80 skipped; Foundry 171 passed. R2 fixed the R5
runner pin (a command line removed by an unrelated sweep), the undeclared
evidence sources, the Python 3.14 libffi descriptor reaching the H-1 role, the
descriptor leak (the `hold` and `cleanup` roles never closed their journal), a
legacy-connector test that needed a developer's real environment file, and a
snapshot-import idempotency gap that a loaded stress run exposed (a same-key
retry that overlapped its original could be refused instead of receiving the
original result). `requirements-web.lock` was refreshed on Python 3.14. The
H-1 change alters that Route 3 artifact's digest; block F stays `UNSET`.
Independent Codex re-review found no remaining repository or disposable-host
finding and independently passed a focused 940-test set with the two documented
hard-limit skips. The tested `soupsieve` 4.0.1 lock is accepted under Peter's
pre-production currency instruction. Details are in the handback's R2 section.

*Historical (2026-11-08); superseded.* At that date production evidence was only
partly complete. Read-only, without sudo: a fresh 30-minute state observation
found `freedom-bot`, `freedom-worker`, PostgreSQL 18 and Caddy active with
unchanged start times and zero restarts, and `freedom-web` inactive. Not
obtainable then without privilege: journal warning/error counts (the account is
outside `adm`/`systemd-journal`) and the final backup set's SHA-256 values,
sizes and `postgres` archive size (root-only directory); they were recorded as
missing and none was invented. **Both were later collected** under privilege
and are in the handback (checksums pass, `db-postgres.dump` is 2,042 bytes,
31-sample/30-minute clean observation). The first production write occurred at
15:27, before the authorized 16:00 window; Peter accepted it on 2026-11-09 as a
documented process deviation. At that date NodeSource and the empty Caddy source
were disabled (both were enabled in the later continuation), and the retained
conffile variants were classified in the handback (one, `sshd_config.ucf-old`,
newly found).

*Historical (2026-11-08, unprivileged, on the production host); superseded.*
Currency continuation: Ubuntu archive packages were current; Node 24.22.2 is the
newest 24.x and Foundry v14 needs Node 24, and the Foundry suite passed on it
(171). Caddy 2.10.2 then trailed upstream 2.11.9 and the NodeSource/Caddy
sources were disabled; the `bwrap-userns-restrict` AppArmor profile was a stale
local copy. New findings then: production `logrotate.service` was failed
(duplicate `cloud-init` logrotate files) and `venv-web` was still the pre-R2
lock. All of these were fixed in the 2026-11-09–11 attended continuation (see
the current section above). A scratch-cluster test run mistakenly reached
production's `freedom_test` (disposable test lane, no service uses it); it was
repaired to migration 0013 and `tests/conftest.py` now refuses such targets
(still in force). `oracle-test` became package-current on Node 24.22.2 and its
post-boot database-safety and Foundry checks passed. The root-only production
items and the journal/backup evidence were blocked by the sandbox at that time
and were completed later under privilege.

*Historical (2026-11-09 decision); production actions since completed.* Peter
selected `PermitRootLogin prohibit-password` and confirmed that obsolete
`/opt/discord-bots/venv*` paths may be removed after verifying they are unused.
On `oracle-test`, the SSH setting was made explicit and validated after reload,
and the legacy directory was already absent with no dependency found by bounded
process, open-file, `/proc`, unit or cron checks. At that point production had
not been changed; both production actions were then completed in the attended
continuation (SSH policy explicit and effective; unused `venv`/`venv-web`
removed after reference checks).

There is no production OpenSSH ownership defect. The `nobody:nogroup` owners
and `Bad owner or permissions` a sandboxed agent session saw are how every
root-owned path appears inside that session's user namespace (one mapped uid,
sudo refused by `NoNewPrivs`); unsandboxed (2026-11-07) the paths are `root:root`
and ordinary `ssh oracle-test` works, so no repair was needed or made. The R2
([prompt](../review/production-ubuntu-26-04-upgrade-review-remediation-r2-claude-prompt.md))
is closed for repository and disposable-host remediation. `.agents/AGENTS.md`'s suite section,
the `run-suites` skill and the runbook were all updated in R2 and agree with
these figures.
Route 3 remains NO-GO and block F `UNSET`; the old S0.0 no longer applies.

## Retained Route 3 position — provisioning plan accepted; release identities pending

Baseline v1.9 remains active. Phase 3 and Phase 4 gates are approved; Phase 5
implementation and unrestricted testing on the disposable `oracle-test` server
remain authorized.

Peter accepted the Route 3 production provisioning plan on 2026-11-03 after
Codex independently re-reviewed the R6 candidate and its R7 documentation
correction with no remaining finding. Final evidence on the exact candidate
included:

- `tests/test_provisioning_plan.py`: **309 passed**;
- production checklist item 8: **51 passed**;
- checklist 5b plus installer/system-service modules: **315 passed**;
- guard suite: **40 passed**;
- clean shell syntax, `git diff --check` and disposable-host cleanup; and
- no production or staging access during the provisioning-plan remediation.

The completed inspection and provisioning-remediation prompts are historical
in the [November 2026 archive](../review/archive/route-3-production-provisioning-2026-11/README.md).
The cumulative behavior and evidence record remains the
[production-readiness handback](../review/route-3-production-readiness-handback.md).

### Open gates

- The production release fields remain `UNSET`: reviewed revision, archive and
  manifest digests, exact Python 3.14 package closure and origins, interpreter
  digest, and SA-2 tree digest.
- The accepted candidate must be committed and published before a release
  revision or archive can be supplied.
- The release-record/package procedure was redesigned on 2026-11-11 for the
  Python 3.14 packages already installed as part of the host baseline
  (`tools/route3_release_record.py`, runbook part P, blocks S0.A/S0.3; the former
  S0.0 is withdrawn and refuses). It is an uncommitted implementation. Codex's
  review of it (blocking: installed payload not bound to the signed archive;
  mutating blocks relied on an operator having run S0.3) was remediated:
  `reference.record`/`ROUTE3_REFERENCE_SHA256`, one mechanical `route3_gate` at
  every mutating boundary, no install path, exact per-member origins. The
  remediated tree awaits its `oracle-test` run and re-review (see the handback's
  "Independent review remediation"). A second review (2026-11-11) found S4.1
  started the supervisor before any gate; S4.1 now runs the full gate first
  (handback §13). On `oracle-test` Codex recorded
  `tests/test_route3_release_record.py` 269 passed (400.13 s), the real
  reference-interpreter run passed (digest
  `be9a2a5eada8c89c1c399fdfb8397179e877c20d8db0739c802f726d4d0e69fd`), and
  `tests/test_provisioning_plan.py` 219 passed / 4 stale-expectation failures
  (3186.80 s) on the earlier run. *That pending state is superseded
  (2026-11-12, handback §13.1).* Codex's exact-tree results on `oracle-test`
  for the reviewed, still-uncommitted candidate: release-record module 269
  passed (400.13 s, unprivileged); focused provisioning rerun 24 passed, 210
  deselected (296.66 s); full `tests/test_provisioning_plan.py` as root **234
  passed** (3,381.14 s, 56 min 21 s); canonical bot suite with
  `TEST_DATABASE_URL` and default descriptor limits as `ubuntu` **7,853
  passed, 250 skipped** (1,194.78 s; printed skip reasons limited to the
  documented root/ownership/real-apt/systemd/RLIMIT/non-owner-role/RP-11
  toolchain conditions); database-enabled web suite **2,893 passed, 80
  skipped** (606.21 s); Foundry Node suite **171 passed, 0 skipped** (3.65 s).
  `git diff --check` is rerun by Codex after this edit. This validates the
  **uncommitted candidate on the disposable host, not production**. Route 3
  stays NO-GO, every block-F release value stays `UNSET`, and no
  production/staging mutation, provisioning, installation, activation, commit
  or push occurred. Next controlled step: publication/commit of the exact
  reviewed candidate, then a separately authorized production read-only S0.A
  attestation to populate the release identities. S1, S3 and S4 remain
  separate gates.
- Off-production reference generation is complete and independently exercised
  on `oracle-test` (2026-11-14; handback §14). Both reference commands accept a
  private `--apt-config`; insecure sources and an architecture-filtered source
  with a nonempty variant list are refused before apt runs. The reference binds
  `Architecture-Variant` and every installed file, so the wrong build is a
  fail-closed mismatch. The disposable host was brought from superseded libc
  `2.43-2ubuntu2.4` to offered `2.43-2ubuntu2.7`; the corrected isolated config
  fetched signed `binary-amd64v3` indexes. The interpreter reference matched
  the installed digest `be9a2a5e...`; the 32-member payload reference verified
  the host (`baseline` SHA-256 `497a3915...`, `reference` SHA-256 `5d6a3ee7...`).
  Final disposable evidence: release-record module **346 passed**; provisioning
  module as root **234 passed**; bot **7,928 passed, 252 skipped**; web **2,894
  passed, 80 skipped**; Foundry **171 passed**. Earlier failed attempts (blanket
  variant refusal, `[arch=amd64]`, missing `universe`, full `/tmp`) are retained
  in the handback and all are closed. This validates the uncommitted candidate,
  not production. Route 3 stays NO-GO and every block-F value remains `UNSET`.
- Production S1 inert provisioning requires a later explicit written
  authorization after all release fields are supplied and reviewed.
- S3 arming/install and S4 activation are separate later decisions. Activation
  also requires the named attending operator, escalation contact, bounded
  window, pre/post residual checks and verified cleanup/reboot response.
- Account-dependent sudo, Polkit, user-manager and process checks repeat after
  any separately authorized provisioning.

The Route 3 plan therefore remains **NO-GO**. Provisioning, installation,
activation, migration/cutover and RB-1 are unauthorized. The separately
assigned OS/runtime/database remediation does not alter those boundaries.

[Active handover](../review/Handover%20information) ·
[Active delivery plan](active-delivery-plan.md) ·
[Implementation plan](../implementation-plan.md) ·
[Provisioning runbook](../operations/executor-supervisor-provisioning-runbook.md)
