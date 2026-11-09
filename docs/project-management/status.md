# Project status

## Current status — Ubuntu 26.04 / PostgreSQL 18 R2 reviewed; dependencies current and green on `oracle-test`; production evidence partly open; Route 3 NO-GO — 2026-11-08

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
80 skipped; Foundry 171 passed**. Production `venv-web`/`venv-bot` still hold the
older sets (a privileged, attended step). Independent review accepted the
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

Production evidence is only partly complete. Read-only, without sudo: a fresh
30-minute state observation found `freedom-bot`, `freedom-worker`, PostgreSQL 18
and Caddy active with unchanged start times and zero restarts, and `freedom-web`
inactive. Not obtainable without privilege: journal warning/error counts (the
account is outside `adm`/`systemd-journal`) and the final backup set's SHA-256
values, sizes and `postgres` archive size (root-only directory); they remain
missing and none is invented. The first production write occurred at 15:27,
before the authorized 16:00 window, and still awaits Peter's disposition.
NodeSource and the empty Caddy source remain disabled, and the retained
conffile variants are now classified in the handback (one, `sshd_config.ucf-old`,
newly found).

Currency continuation (2026-11-08, unprivileged, on the production host):
Ubuntu archive packages are current; Node 24.22.2 is the newest 24.x and Foundry
v14 needs Node 24, and the Foundry suite passes on it (171). Caddy 2.10.2 trails
upstream 2.11.9 and the NodeSource/Caddy sources remain disabled; the
`bwrap-userns-restrict` AppArmor profile is a stale local copy. New: production
`logrotate.service` is failed (duplicate `cloud-init` logrotate files) and
`venv-web` is still the pre-R2 lock. A scratch-cluster test run mistakenly
reached production's `freedom_test` (disposable test lane, no service uses it);
it was repaired to migration 0013 and `tests/conftest.py` now refuses such
targets. `oracle-test` is now package-current on Node 24.22.2 and its post-boot
database-safety and Foundry checks pass. All root-only production items and the
journal/backup evidence remain blocked by the sandbox and are listed in the handback.

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
- The release-record/package procedure must be redesigned and independently
  reviewed for the Python 3.14 packages already installed as part of the host
  baseline; the former S0.0 must not be run.
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
