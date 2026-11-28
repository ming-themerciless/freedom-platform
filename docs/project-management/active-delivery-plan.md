# Active delivery plan — implementation-first baseline v1.9

Status: approved and active; Route 3 S1, post-reboot G1-G6, S3 and S4.1 executed; S4 acceptance probes incomplete because production capture unit is absent; supervisor active and ready (2026-11-22)

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
- For the accepted RP-11 work, use the Claude implementation/remediation and
  Codex independent review loop in [implementation-plan §16.4](../implementation-plan.md#164-claude-implementation-and-codex-review-loop).
  Do not ask Peter to proceed between steps already within the authorized
  slice. Respect all separate operational and production gates.

## Current delivery position

**RP-11 single-host development, 2026-11-28.** D-1 through D-10 are approved
policy. The inert D-1 validator passed 979 focused checks after independent
review and remediation. The D-2 labels and opt-in D-1 continuation passed
independent review and 5,009 local checks. The v40 artifacts reproduced and
the dependent pins passed. Continue with the evaluator/config composition
and authority binding while the operational entry remains gated.
[Current handback](../review/rp11-d1-seam-d2-handback.md); earlier:
[precursor](../review/rp11-d1-expectations-precursor-handback.md).

**Production baseline.** Ubuntu 26.04.1, Ubuntu Python 3.14.4 and Ubuntu
PostgreSQL 18.6 are current; the attended Ubuntu continuation and the Lavalink
residue removal (music is removed under OD-40) closed on 2026-11-11 with no open
item. Peter's pre-production currency policy (implementation plan §14.1) stands:
supported OS, database, runtimes and dependencies are brought current before the
platform begins production use, without waiving backup, recovery, observation or
review evidence.

**Route 3, executed (S1 record, as at STOP-A before the reboot).** Peter bounded Route 3 to explicitly authorized, attended
migration/cutover evidence activations. It is not a general maintenance facility
and is not approved for recurring or unattended use; the transient
inspection-failure residual is accepted only inside that bounded use (named
attending operator, pre/post residual-state checks, verified root removal or
reboot if cleanup is uncertain). The provisioning plan (runbook part P) was
accepted on 2026-11-03; block F was completed on 2026-11-15; and on 2026-11-18,
under Peter's written S1 authorization, S1 inert provisioning ran on production
for deployable revision `26757f2ab67eb5be4f576dbc2166db5df8870857`: S1.0 through
S1.4 rc 0, S2.1 rc 0 with `STOP-A verified`, S2.2 rc 12 as expected before the
first post-S1 boot, all 32 package payloads reverified at every gate. Claude and
Codex final review found no defect or rollback need. STOP-A holds: no supervisor
unit, process, linger, sudoers grant, SA-2 artifact, state or runtime directory,
activation or cutover. Evidence: handback §16.

**After the reboot, 2026-11-18 (current).** The production reboot has happened
(new boot `7414d026-f72c-4461-ba00-0cee1c14f275`; it interrupted and restarted
the Freedom bot, worker, PostgreSQL, Caddy and Foundry backends, and could not
start Route 3 because nothing for the boot to start existed at STOP-A). **G1 to G6
passed** (G1 to G5 read-only in an attended root session; G6 Codex independent review): G2 (service health, the
31-sample observation, and the root evaluation of the warning-priority journal,
11 benign system entries and none from the four services or Route 3); G3 block D,
block F and S2.1 `[S2.1 rc=0]` with `STOP-A verified`; G4 S2.2 `[rc=0]`; G5 the §6
v2 checklist with the sudoers enumeration helper and the account-dependent checks,
every item matching STOP-A (S3-only objects absent; no sudoers grant reaches
`freedom-executor`; Polkit does not authorize it). Nothing was mutated and block R
was not needed. The temporary `/etc/sudoers.d/x` grant existed during the attended
verification and reached the attending account `foundry` only (not an executor
grant; it did not reach `freedom-executor`). It was removed after G6 and the final
diff review (`visudo -c` parsed OK, rc 0; `/etc/sudoers.d/x` confirmed absent;
unprivileged `sudo -n true` rc 1), so general passwordless sudo is no longer
available. **G6 passed:** Codex
independently reverified the extracted blocks, reran S2.1 and S2.2 (rc 0 each) and
reproduced the G2 journal result; no blocking operational finding, no rollback need.
Evidence: handback §16.1.

**S3 executed (2026-11-18, STOP-B).** After a first attempt stopped at S3.2 (missing `/usr/local/libexec`, host returned to STOP-A by R3 rc 0) and Codex's independent approval of the corrected S3.2/R3 C6p remediation, the maintainer explicitly authorized the rerun. Block D, block F, then S3.1 to S3.5 ran sequentially on production, each rc 0 (S3.4 installer verify 12 as expected, S3.5 install 0). The supervisor unit is enabled and inactive with no supervisor process. Evidence: handback §16.3.

**S4.1 executed (2026-11-20).** Peter authorized S4 with himself as attending operator and escalation contact for the current window. The full trusted attestation passed; `systemctl start` succeeded; `verify-ready` returned `ready` rc 0. Acceptance probes 1 and 4 passed. Probes 2 and 6 cannot run because production has no `rp11-capture-pass-a.service` and no valid consume-evidence activation. Probe 3 (reboot) was not run; probe 5 remains unrun. See handback §16.4. The supervisor is active and ready.

**RP-11 installer mechanics slice (2026-11-21).** A reusable installer/verifier/remover is implemented and passed 165 focused local tests and 9 real-systemd tests on `oracle-test`; its handback is [here](../review/rp11-capture-unit-installer-handback.md). No production fragment or policy is included, so it cannot install the production capture unit. The approved `ExecStart`, sandbox settings, timeout budget and production deployment/activation procedure remain undecided and unimplemented.

**RP-11 capture service: implementation direction accepted (2026-11-21).** Peter accepted the [design proposal](../review/rp11-capture-service-design-proposal.md)'s direction (static C launcher re-based to Python 3.14, entrypoint, SA-2 build inclusion, reviewed fragment); implementation starts, by Claude implementation with a Codex review/remediation loop on non-production hosts. Open and separately gated: production service identity, a proven timeout/finalization contract (no whole-service runtime bound is claimed), the production fragment, the SA-2 artifact rebuild, production install, activation and probes 2, 3, 5 and 6. No production or staging step is authorized.

**RP-11 launcher Python 3.14 rebase (2026-11-21).** The launcher rebase slice (proposal §4 step 1) and the regenerated review manifest (version 32) are complete and **passed Codex independent review with no blocking findings**; see the [handback](../review/rp11-launcher-py314-rebase-handback.md). The entrypoint contract source audit is done and the G11/G12 slice is implemented (see below); the full capture service is not complete. Codex's broad suite had 4 environment sentinel failures from the pre-existing `/run/freedom-blades/laboratory.lock` (not removed or changed). No SA-2 fragment or production step exists or is authorized; the only entry artifact is the inert bootstrap recorded below. Production is untouched and the S4 probe status is unchanged.

 **Entry-contract decisions accepted (2026-11-21).** Peter decided two points of the [Pass A entry contract](../review/rp11-pass-a-entry-contract-proposal.md) (G11, G12): (1) systemd `INVOCATION_ID` is **retained as capture provenance**, recorded once per pass in the capture index state chain and the handback binding, **not** in every `CaptureRecord` (schema consequence: `rp11-capture-index/3`, `rp11-capture-binding/2`; record schema unchanged; exact-schema readers, no migration because no real pass exists; tests listed in the contract §3 item 5); (2) the entrypoint **may load tested Python modules under the isolated Python 3.14 launcher**. After inspecting `infra/rp11-h1/build.py`, `infra/rp11-h1/rp11_h1.py` and `python3.14 -I -S` (stdlib-only `sys.path`, no script directory, `PYTHONPATH` ignored), the contract §3a selects the existing SA-2 mechanism: a fixed, root-owned, digest-bound dependency closure in `lib/` beside the entry, named by the entry itself after the root tree check, with no cwd, environment, site or repository lookup. **Scope:** these decisions authorize reversible implementation and testing on `oracle-test` only. They do **not** accept or authorize the DRAFT Pass A operational commands (G1), an operational run, any production or staging mutation, the production service identity, sandbox or timeout, the SA-2 rebuild or install, activation, or S4 probes 2, 3, 5 and 6. **Implemented (2026-11-22); independent Codex review passed (final review of the G11/G12 code and tests, no remaining blocking findings):** G11 `INVOCATION_ID` provenance is in the tree (`rp11-capture-index/3`, `rp11-capture-binding/2`, genesis/advance/final states, binding, X-4; `CaptureRecord` unchanged). G12 is an **inert** bootstrap `infra/rp11-h1/rp11_entry.py` plus a digest-bound `ENTRY_SOURCES` closure in `infra/rp11-h1/build.py` (root-owned tree check before any import, exit 77/64/69; `INVOCATION_ID` read only from the raw `/proc/self/environ`, failing closed when unreadable). See the [G11/G12 handback](../review/rp11-entry-bootstrap-g11-g12-handback.md). **Boundaries unchanged:** no operational Pass A, no safety-sentinel (G8) amendment, no SA-2 production rebuild or install, no production or staging access, no activation. **Final evidence (post-remediation; independent Codex review of the code and final tests passed, no blocking findings; focused runs, not the canonical full suites):** local Python 3.14.4 repository `venv-web`, unprivileged: entry/artifact/H1/install tests **520 passed, 2 skipped** (`RLIMIT_NOFILE` cannot be raised above the hard limit); capture/retention/cleanup **696 passed, 0 skipped**. `oracle-test`, root, Python 3.14.4 `venv-web`, pytest basetemp under protected `/root`: `tests/test_rp11_entry.py tests/test_rp11_entry_artifact.py tests/test_rp11_h1_artifact.py` **354 passed, 3 skipped** (each an expected identity-specific case: root-owned objects accepted, a tree-root-owned case, a non-root marker control). `oracle-test`, unprivileged `ubuntu`, grammar-compatible `/tmp` basetemp: capture/retention/cleanup **696 passed, 0 skipped**. Failed exploratory runs (wrong basetemp or identity) are disclosed and dispositioned in the handback. `rp11_h1.py` source changed, but the installed production SA-2 artifact was **not** changed or rebuilt; any future bundle use needs the separately authorized and reviewed artifact rebuild and digest update. Host activity was `oracle-test` testing only; no production or staging action. G1–G10 stay open.

**Remaining work:** complete the governed production capture-unit definition and deployment path before attempting probes 2 and 6. The accepted executor OC handback excluded a production-ready capture service; do not treat the synthetic host test or this mechanics slice as a production deployment artifact. Probe 3 needs a planned stop/reboot/readiness check; preserve the current active state until that test is prepared. Any status other than the
runbook's expected one is a stop and an escalation; R3 is the exit back to STOP-A and block R is run only on Peter's
instruction.

The executor coordinator, start orchestration, automatic attestation, production capture-unit policy/deployment, migration/cutover and RB-1 remain unassigned unless separately approved and staffed.

## G1 candidate-command review — 2026-11-22: NOT ACCEPTED

Codex reviewed the candidate commands in the
[operational evidence prompt](../review/phase-5-0-p5-r5-operational-evidence-authorization-prompt.md);
Claude corrected its documentation and Codex reviewed the remediation. G1 has
not passed. The draft's repository host is the production Ubuntu server, so its
local A0 tests, capture-root creation and `rsync`/`ssh` activity cannot run
under the current boundary. No commands were run or authorized by this review.
Before G1 can be reconsidered, document a maintainer-approved execution and
capture topology with approved source delivery; re-pin the harness and review
manifest to current Python 3.14, PostgreSQL 18 and kernel facts; and resolve
RP-11, C-11, the child environment, A-6, clean pinned-tree and owner inputs.
This review grants no AUTH-SYNC, AUTH-READ, AUTH-DBREAD or A-2 authority. Full
disposition: [entry-contract proposal §0a](../review/rp11-pass-a-entry-contract-proposal.md).

**Update 2026-11-22 (proposal only):** the recommended single-host `oracle-test` topology is now documented as an **unaccepted proposal** in [entry-contract proposal §0b](../review/rp11-pass-a-entry-contract-proposal.md#0b-g4-topology-proposal--single-host-oracle-test-2026-11-22); it was reviewed by Codex on 2026-11-22 with no blocking documentation finding, but it is not accepted by Peter and not authorized. Acceptance and re-derivation remain open: its acceptance, the checkout and capture-root path values, source-publication/acquisition authorization (exact-source acquisition from the canonical GitHub remote is **not** authorized by OP1 or A-2; it is a separately controlled pre-pass action), re-derivation of the sync row, C-11, the child environment and the AUTH rows, and G1 itself. G1 stays NOT ACCEPTED; no A-2; AUTH-SYNC, AUTH-READ and AUTH-DBREAD remain ungranted; nothing runs on production.

**Owner clarification 2026-11-22 (runtime host; scope only):** Peter clarified that production runtime must run on the production Ubuntu server; `oracle-test` is proof-of-concept, feasibility passes and testing only and has **no ongoing or production role**. The eventual production RP-11 capture runtime therefore belongs on production Ubuntu, but this clarifies scope only: production installation, access, activation and any real pass remain **unauthorized and separately gated** (identity, sandbox, timeout, SA-2 build, installation, activation and real-run gates all open). The §0b topology applies to the disposable feasibility exercise only and cannot decide or move a production runtime onto `oracle-test` ([entry-contract proposal §0b](../review/rp11-pass-a-entry-contract-proposal.md#0b-g4-topology-proposal--single-host-oracle-test-2026-11-22)). G1 stays NOT ACCEPTED; no A-2; AUTH-SYNC, AUTH-READ and AUTH-DBREAD remain ungranted; the source-acquisition authorization boundary is unchanged (exact-source acquisition is not authorized by OP1 or A-2).

**Implementation continuation update (2026-11-22).** The G11 start-binding helper has been implemented by Claude and source-reviewed by Codex after one remediation loop, with no remaining blocking finding. It validates the consume journal's `run-start.invocation_id` pairing but intentionally does not establish lifecycle completion; it is unwired and the entry remains inert. Its focused helper/entry/artifact tests passed on `oracle-test`: 421 passed, 3 identity-specific skips. The first run's `/tmp` basetemp caused 2 failures and 150 setup errors (272 passed); the rerun with a root-owned basetemp passed. The generated test directory was removed. The documented secret-excluding rsync synchronized the current workspace at Peter's explicit request; no canonical-remote source acquisition occurred. G1 source acquisition remains unauthorized; no production test or operation occurred. Continue with the next authorized implementation slice using the Claude/Codex loop. Preserve the dirty worktree. Current gate state and session-resume procedure: [active handover](../review/Handover%20information#current-implementation-resume-2026-11-22) and [status](status.md).

## Evidence and boundaries

- Accepted provisioning-plan evidence: exact-tree 309 / 51 / 315 passed, guard
  suite 40 passed (2026-11-03), clean independent R6/R7 re-review.
- Release-record and reference tooling (2026-11-14/15, `oracle-test`):
  release-record module 350 passed; provisioning module as root 235 passed; bot
  7,928 passed / 252 skipped; web 2,894 passed / 80 skipped; Foundry 171 passed.
  Those validate the repository tree and the disposable host; the production
  result is the S1/S2 record above.
- Production facts and the v2 checklist are in the cumulative
  [handback](../review/route-3-production-readiness-handback.md) (§6 checklist,
  §15 S0.A, §16 S1 result).
- Discord remains the community platform and identity/integration source. Only
  the legacy Freedom bot is eventually retired under implementation-plan §15.2
  after the full completion criteria are met.

## History

The previous plan (S0.A attestation state; the 2026-11-07 to 2026-11-11
production-baseline paragraphs; the 2026-10-25 to 2026-11-03 Route 3
decisions) is preserved verbatim in
[`active-delivery-plan-through-2026-11-15-route-3-s0a-attestation.md`](active-delivery-plan-through-2026-11-15-route-3-s0a-attestation.md);
an earlier predecessor is
[`active-delivery-plan-through-2026-10-24-route-3-production-readiness.md`](active-delivery-plan-through-2026-10-24-route-3-production-readiness.md).
Both are indexed in the [plan archive](active-delivery-plan-archive/README.md)
and are evidence, not authority.

[Active handover](../review/Handover%20information) ·
[Current status](status.md) ·
[Implementation plan](../implementation-plan.md) ·
[Reboot and continuation runbook](../operations/production-reboot-and-route-3-continuation-runbook.md)
