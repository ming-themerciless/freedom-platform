# Active delivery plan — implementation-first baseline v1.9

Status: approved and active; Ubuntu 26.04/PostgreSQL 18 remediation assigned,
Route 3 release fields no-go 2026-11-07

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

The cumulative inactive Route 3 production-readiness candidate is accepted for
continued non-production development. Peter has selected production as the
direction and bounded Route 3 to explicitly authorized, attended
migration/cutover evidence activations. It is not a general maintenance
facility and is not approved for recurring or unattended use.

The transient inspection-failure residual is accepted only inside that bounded
use: every activation needs a named attending operator, pre/post residual-state
checks and verified root removal or reboot before the operating window closes
if cleanup is uncertain. Any recurring or unattended use requires a stronger
trusted-identity and automated-reconciliation design, tests and independent
security review.

The 2026-10-25 production-specific §6 inspection was a historical observation:
Python 3.14 and the Route 3 account, units, artifact, runtime paths and tmpfiles
prerequisite were absent then. Production has since been upgraded to Ubuntu
26.04.1, Ubuntu Python 3.14.4 and Ubuntu PostgreSQL 18.6. That maintenance did
not provision or activate Route 3, and the old S0.0 release-preparation
procedure no longer applies to the pre-installed Python baseline.

Peter then gave the follow-up assignment and named the window, himself as
rollback owner and retention until reviewed. Root-assisted sudoers and private
Polkit classification **completed** (nothing reaches the future account). Phase
B stopped on a live-path coexistence conflict; Phase C did not begin. Production
changes were Peter's temporary root grant(s), the approved `chmod 0440` of
`/etc/sudoers.d/foundry-bot`, and an `rm -f` of the grant file whose status was
never reported; nothing was provisioned or installed and no service restarted.

Peter then selected a distinct trusted deployment, `/opt/freedom-route3/{code,venv}`.
It is implemented and rehearsed only on `oracle-test`; the live services stay on
their paths and are not edited or restarted. The root does not exist on
production, and the selection authorizes no production change.

Peter confirmed on 2026-10-31 that `/etc/sudoers.d/zz-claude-window` is
**absent** and accepted the Phase A stop/order deviation. Peter accepted the
production provisioning plan on 2026-11-03 after Codex's independent R6/R7
re-review found no remaining issue. The completed prompt chain is archived;
runbook part P and the cumulative handback remain the forward contract and
evidence.

Peter's 2026-11-07 pre-production currency decision requires supported OS,
database, runtime, dependency and related infrastructure upgrades before the
platform enters production use. It approves the completed PostgreSQL 16-to-18
migration and retirement of the superseded cluster; it does not waive backup,
restore, compatibility, observation or independent-review evidence.

The Ubuntu 26.04/PostgreSQL 18 R2 remediation returned on 2026-11-07 and passed
independent Codex re-review on 2026-11-08 with no remaining repository or
disposable-host finding: the disposable exact-tree suites are green
at the default descriptor limit (2026-11-07: bot 7,566 passed, 337 skipped; web 2,892
passed, 80 skipped; Foundry 171; superseded by the 2026-11-08 dependency-currency
figures below), and the SSH route needed no repair, because the apparent
`nobody:nogroup` ownership was an agent-sandbox user-namespace artifact
(unsandboxed, the paths are `root:root` and `ssh oracle-test` works). Still open:
production journal warning/error counts and the final backup hashes and sizes,
which the remediation account cannot read, and Peter's decision on the 15:27
write. Production application or schema mutation, `freedom-web` activation and
Route 3 execution remain out of scope. See the handback's R2 section.

Dependency currency, 2026-11-08: the stale direct Python bounds were raised (FastAPI
0.162, uvicorn 0.54, cryptography 50, SQLAlchemy 2.1, py_webauthn 3, pytest 9,
pytest-asyncio 1.x) and the web lock regenerated; the exact-tree `oracle-test` suites are
green on it (bot 7,571 passed, 337 skipped; web 2,893 passed, 80 skipped; Foundry 171 on
Node 24.22.2). Production's virtualenvs still hold the older sets and need an attended,
privileged rebuild. See the handback's "Dependency currency return".

The Route 3 plan review gate remains closed, but every block-F release identity
is `UNSET`. Its release-record/package procedure must be redesigned for the
pre-installed Python 3.14 baseline and independently reviewed before release
preparation resumes. Only then may Peter separately decide whether to authorize
S1 inert provisioning; S3 arming/install and S4 activation remain later
independent decisions. Account-dependent inspection repeats after any
separately authorized provisioning. The coordinator, start orchestration,
automatic attestation, migration/cutover and RB-1 remain unassigned.

Currency continuation, 2026-11-08: the unprivileged items are closed or
classified in the production-upgrade handback; root-only production work and
the journal/backup evidence need a privileged production session. `oracle-test`
now runs Node 24.22.2 and current Ubuntu packages. Database suites run there, never on the
production host (a scratch-cluster run reached production's `freedom_test` and was
repaired; `tests/conftest.py` now requires the dedicated host identity as well as
the default socket).

## Evidence and boundaries

- Accepted provisioning-plan evidence: exact-tree **309 / 51 / 315 passed**,
  guard suite **40 passed**, clean shell syntax and `git diff --check`, clean
  disposable-host residue state, and a clean independent R6/R7 re-review.
- Final focused checklist review: exact-tree **53/53**, clean `bash -n` and
  `git diff --check`; the structural run retained one known baseline allowlist
  failure.
- Production facts are in handback §§6.1–6.2; §6.1's counts come from checklist
  v1 (old live paths) and the current checklist is v2 (trusted deployment paths).
  Post-provision account facts, F-1 through F-3 and the bounded
  activation/rollback procedure remain later gates; sudoers and Polkit policy
  are no longer open.
- Discord remains the community platform and identity/integration source. Only
  the legacy Freedom bot is eventually retired under implementation-plan
  §15.2 after the full completion criteria are met.

[Active handover](../review/Handover%20information) ·
[Current status](status.md) ·
[Implementation plan](../implementation-plan.md) ·
[Archived predecessor plan](active-delivery-plan-through-2026-10-24-route-3-production-readiness.md)
