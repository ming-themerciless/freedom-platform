# RP-11 capture service (`rp11-capture-pass-a.service`) — design proposal

**Date:** 2026-11-21 · **Status (updated 2026-11-21): IMPLEMENTATION DIRECTION ACCEPTED by Peter Duscha; implementation starts.** Accepted: the §4 direction (retain the static C launcher re-based to Python 3.14, implement the entrypoint, fold both into the SA-2 build, add a reviewed fragment), delivered by Claude implementation with a Codex review/remediation loop. **Still open and separately gated, not decided by this acceptance:** the production service identity; a proven timeout/finalization contract (§4, §5; no whole-service runtime bound is claimed); the production unit fragment (`infra/rp11/rp11-capture-pass-a.service` does not exist); the SA-2 artifact rebuild and its authorization (changes `ROUTE3_SA2_TREE_SHA256`); production installation; activation; and acceptance probes 2, 3, 5 and 6. This is still not a unit fragment and not installable, changes no RP-11 or S4 acceptance, and **no production or staging step is authorized.** The §3 candidate values other than the accepted launcher `ExecStart` direction, the §6 sandbox and §8 decisions 2 to 4 remain open for Peter's later decision; §8 decision 5 (production installation and activation) stays separate and unauthorized. **Progress (2026-11-21):** §4 step 1 (launcher re-base on Python 3.14) and the regenerated review manifest are done and passed Codex independent review with no blocking findings ([handback](rp11-launcher-py314-rebase-handback.md)); source audit complete; decision proposal prepared ([entry contract proposal](rp11-pass-a-entry-contract-proposal.md)), unaccepted; the G11/G12 slice (inert `rp11_entry.py` bootstrap, digest-bound closure, `INVOCATION_ID` index/binding schemas) is implemented, [handback](rp11-entry-bootstrap-g11-g12-handback.md), and **independent Codex review of the code and final tests passed with no remaining blocking findings**. Final evidence (focused runs, not canonical suites; Python 3.14.4 `venv-web`): local unprivileged 520 passed, 2 skipped and 696 passed, 0 skipped; `oracle-test` root `test_rp11_entry.py`/`test_rp11_entry_artifact.py`/`test_rp11_h1_artifact.py` 354 passed, 3 skipped (expected identity-specific); `oracle-test` `ubuntu` capture/retention/cleanup 696 passed, 0 skipped. `rp11_h1.py` source changed but the installed production SA-2 artifact was not changed or rebuilt; any future bundle use needs the separately authorized, reviewed rebuild and digest update. No operational Pass A, no safety-sentinel (G8) amendment, no SA-2 production rebuild or install, no production or staging access, no activation; the Pass A logic and the unit fragment are not implemented; steps 2 to 4 are pending. **Entry-contract decisions accepted (2026-11-21):** Peter decided (1) that systemd `INVOCATION_ID` is retained as capture provenance, recorded once per pass in the index state chain and handback binding (not per `CaptureRecord`), and (2) that the entrypoint may load tested Python modules under the isolated Python 3.14 launcher via a fixed, root-owned, digest-bound dependency closure beside `rp11_h1.py` with no cwd/environment/site lookup (selected in the [entry contract](rp11-pass-a-entry-contract-proposal.md) §0, §3a, G11, G12). These authorize reversible implementation and `oracle-test` testing only; they do **not** accept the DRAFT Pass A operational commands, an operational run, production/staging mutation, the production identity, sandbox or timeout, the SA-2 rebuild or install, activation or S4 probes, and they do not change the §3 candidates or §8 decisions 2 to 4. The candidate requirements in the body below are the original proposal text and are unchanged; later edits add only progress and evidence updates (status wording, a mechanism status note and a same-InvocationID evidence section), which record what was done or observed and do not change or accept any technical requirement.

**Current-state note (2026-11-22, owner clarification; historical text below unchanged):** Peter's direction is that the production host for the RP-11 capture runtime is the production **Ubuntu** server, and `oracle-test` is proof-of-concept/testing only with no ongoing or production role (see [entry-contract proposal §0b](rp11-pass-a-entry-contract-proposal.md#0b-g4-topology-proposal--single-host-oracle-test-2026-11-22)). This is a host-direction clarification only: all production service policy, identity, sandbox, timeout, SA-2 artifact rebuild, installation and activation remain **undecided and unauthorized**.

Read for this proposal: `.agents/AGENTS.md`; implementation-plan reading map, §§0, 12, 14, 16, 20; [Handover information](Handover%20information); [active delivery plan](../project-management/active-delivery-plan.md); [status](../project-management/status.md); [installer handback](rp11-capture-unit-installer-handback.md); the disposable-host runbook; the D3-R4 one-host amendment and the R1/R2 remediation proposals named in §5.

## 1. Current accepted facts, kept apart from everything else

**Accepted/current (handover, status, plan §20):**
- Production is Ubuntu 26.04.1 with Ubuntu Python **3.14.4**. The supervisor is active and ready (S4.1, 2026-11-20). Probes 1 and 4 passed. Probes 2 and 6 are blocked because `rp11-capture-pass-a.service` does not exist; probes 3 and 5 are unrun.
- **Current boundary: no production install, activation, start or probe is authorized.** Production and staging mutation, real secrets and player data stay outside every disposable-host authority.
- Installer *mechanics* exist: `tools/rp11_capture_unit_install.py` (installer/verifier/remover). Its 165 focused tests and 9 real-systemd tests on `oracle-test` are **prior mechanics evidence about the installer. They are not tests of this proposal, of any unit shape below, or of any entrypoint.** The installer ships no fragment and refuses with `source-missing` because `infra/rp11/rp11-capture-pass-a.service` is absent.
- The installer mechanics fix: exactly one `ExecStartPre=+/usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py consume`, exactly one `ExecStart=` (content not judged), one finite `TimeoutStartSec=`, no `TimeoutSec=`, no `[Install]`, no enablement, no drop-ins (`tools/rp11_capture_unit_install.py:17-25`). The finite `TimeoutStartSec=` is a requirement of these installer mechanics, not an already accepted production design. `required_directives` and `required_properties` are empty until a reviewed fragment supplies them.
- Disposable-host boundary: every test level is authorized on `oracle-test` (hostname `Test`); a matching database name is not safety evidence.

**Historical design (evidence, not authority):** the D3-R4/R6 one-host amendment and the static-launcher work describe a unit with `User=ubuntu`, `NoNewPrivileges=yes` and no environment or PAM directives. That was an `oracle-test` design under Python 3.12 and has not been re-accepted for production.

## 2. Evidence that there is no runnable capture `ExecStart` today

*Items 1, 2 and 4 are the source audit as it stood at audit time (before the inert entry bootstrap was added). Current state, 2026-11-22: an **inert** entry bootstrap `infra/rp11-h1/rp11_entry.py` now exists and `infra/rp11-h1/build.py` packages it in the source build definition ([G11/G12 handback](rp11-entry-bootstrap-g11-g12-handback.md)). It carries no operational Pass A logic. Still absent: the operational Pass A entry logic, a built or installed SA-2 artifact containing the bootstrap (no SA-2 rebuild has been run or authorized), and the production fragment `infra/rp11/rp11-capture-pass-a.service`. The conclusion below, that no runnable `ExecStart` exists, therefore still holds.*

1. **The launcher contract targeted a then-missing file and was wired to nothing (audit-time heading).** (Updated 2026-11-21: this originally recorded a Python 3.12 contract; both `tools/phase_5_0_evidence/rp11_launch.py` and `infra/rp11-launch/launch.c` are now at Python 3.14, see the [launcher rebase handback](rp11-launcher-py314-rebase-handback.md).) `tools/phase_5_0_evidence/rp11_launch.py:44-56` fixes `/usr/bin/python3.14` and an argv ending in `/usr/local/libexec/freedom-blades-rp11/rp11_entry.py run --pass A`. *At audit time* that entrypoint did not exist (now only the inert bootstrap exists, with no Pass A logic and no built SA-2 artifact), so the contract was "data … wired to nothing" and `plan.is_executable` is `False`.
2. **At audit time no `rp11_entry.py` existed** in the repository (only doc and test references); the inert bootstrap was added afterwards (see the note above). `infra/rp11-launch/` holds the C launcher source.
3. **Production Python is 3.14** (`ROLE_INTERPRETER = "/usr/bin/python3.14"`, `adapters/systemd/manager.py:90`).
4. **SA-2 roles do not run a pass.** `infra/rp11-h1/rp11_h1.py` lists seven vectors (`hold`, `deact … stop-post`, `backstop`, `start`, `stop`, `consume`, `deact … attest`). `consume` is the pre-start step only, and, at audit time, `infra/rp11-h1/build.py` had no entry module (it now packages the inert `rp11_entry.py`).

A runnable Pass A `ExecStart` cannot be derived or used yet, because the launcher argv's entry target `rp11_entry.py` exists only as an inert bootstrap with no operational Pass A logic, is not in any built or installed SA-2 artifact, and the command is therefore not runnable. Nor may the `rp11_h1.py` roles stand in for one.

## 3. Recommended candidate unit shape (non-installable)

This is a proposal. Peter accepted the launcher `ExecStart` direction (§8 decision 1); the other values remain candidates (§8 decisions 2 to 4). It is not a fragment and nothing below is applied anywhere.

| Property | Candidate |
|---|---|
| Type | `Type=exec` |
| Pre-step | exactly one privileged pre-step, the fixed consume vector `ExecStartPre=+/usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py consume`, unchanged |
| Main command | exactly one `ExecStart=/usr/local/libexec/freedom-blades-rp11/rp11-launch --pass A` (the retained static C launcher, re-based to Python 3.14, §4; re-base done and passed Codex independent review). **This path is not runnable today**: it becomes runnable only when the re-based launcher and the operational Pass A entrypoint (only an inert bootstrap exists) are included in a reviewed, built, digest-bound artifact |
| Account | a non-root operator account. **Identity unresolved**: do not assume `ubuntu`: the historical D3-R4 proposal used `User=ubuntu` on `oracle-test`, and the production service identity is not established by current authoritative records. Confirm it is not `freedom-executor` |
| Working directory | `WorkingDirectory=/` |
| Umask | `UMask=0077` |
| Stdio | `StandardInput=null`; `StandardOutput=journal`; `StandardError=journal` |
| Privilege | `NoNewPrivileges=yes` |
| Install | no `[Install]` section |
| Restart | `Restart=no` |
| Start timeout | one finite `TimeoutStartSec=` (required by the installer mechanics; 90 s is a candidate only), see §5 |
| Run-time cap | no `RuntimeMaxSec=` (§5) |

**Explicitly non-installable until all of these hold:** the static launcher re-based for Python 3.14 (done in source; passed Codex independent review) is included in the digest-bound artifact; the operational Pass A entrypoint (beyond the inert bootstrap) is implemented, independently reviewed and packaged in a built artifact; both are included in a reviewed, digest-bound artifact (the SA-2 tree); the entrypoint satisfies the bounded-execution requirement in §4; and the production identity is chosen. Until then the installer correctly refuses.

## 4. `ExecStart` target — recommendation: retain the static C launcher

**Recommendation (direction accepted by Peter, §8 decision 1; the candidate `ExecStart` below remains a proposal):** retain the existing accepted static C launcher design (`rp11-launch/1`, source in `infra/rp11-launch/`), re-based to Python 3.14. The candidate unit `ExecStart` is exactly `/usr/local/libexec/freedom-blades-rp11/rp11-launch --pass A`. The launcher execs the reviewed entrypoint under the fixed contract (interpreter `/usr/bin/python3.14`, `LC_ALL=C`, `PATH=/usr/bin`, `INVOCATION_ID`), so the `rp11_launch.py` contract is re-issued for 3.14 (done 2026-11-21; originally written against 3.12). Direct-Python `ExecStart` is not recommended and is not the §3 candidate. This path is **not runnable** until the re-based launcher and the operational Pass A entrypoint (only an inert bootstrap exists) are included in a reviewed, built, digest-bound artifact.

Dependency work, in order:
1. **Done (2026-11-21); Codex independent review passed, no blocking findings:** re-base the static C launcher and its contract on 3.14 ([handback](rp11-launcher-py314-rebase-handback.md)).
2. **Partly implemented (2026-11-22; inert bootstrap and `INVOCATION_ID` schemas only, independent Codex review passed; see the [G11/G12 handback](rp11-entry-bootstrap-g11-g12-handback.md)). Pass A logic and evidence output remain pending; the `run-start` pairing check is implemented as an inert, unwired helper (`execution/start_binding.py`, 2026-11-22; source-reviewed by Codex with no remaining blocking findings; focused helper/entry/artifact tests passed on `oracle-test`—421 passed, 3 identity-specific skips; the entry does not call it):** implement the entry (Pass A logic, evidence output, the `INVOCATION_ID`/`run-start` pairing the consume role expects) with 3.14-compatible code and tests. Accepted for this step: `INVOCATION_ID` is recorded once per pass in the index state chain and handback binding (schemas `rp11-capture-index/3`, `rp11-capture-binding/2`; `CaptureRecord` unchanged), and the entry loads its tested modules from a fixed root-owned digest-bound `lib/` closure beside `rp11_h1.py` (entry contract §0, §3 item 5, §3a). The old C-11 loader and `sys.path` insertion stay rejected.
3. **Pending:** add launcher and entry, with the entry's computed dependency closure (entry contract §3a), to `infra/rp11-h1/build.py`. That changes `ROUTE3_SA2_TREE_SHA256`, the archive, its manifest and runbook references, so S3.2 needs a separate authorized rebuild.
4. **Pending:** add the reviewed fragment at `infra/rp11/rp11-capture-pass-a.service`.

**Bounded-execution requirement.** Because no manager-side runtime cap is recommended (§5), the eventual entrypoint must bound every child command it runs (an explicit timeout on each) and, on a handled timeout, attempt the prescribed evidence finalization before exiting. If that cannot be guaranteed, the service design remains **not ready**.

**Mechanism status (2026-11-21).** The capture mechanism now enforces the first half: `ActRequest.timeout_seconds` and `ProcessLauncher.launch(timeout_seconds=...)` are required (no default; positive and finite, else refused). `StreamCaptureLauncher` runs each child in its own process group, and at the monotonic deadline kills the group, drains both channels for at most the existing `drain_seconds`, reaps the child and returns `timed_out`. `CaptureSession` treats that as a started host act (`command-timeout`, `host_act_may_have_run`), admits no record, leaves both stream files unadmitted and takes the one stop transition (exactly one X-3 attempt, no retry). **No timeout value is chosen here or in the mechanism:** the Pass A plan must supply one per command. Tests use a test-only constant that is not a Pass A value. What remains open: an entrypoint that actually uses this, and the values.

**Same `InvocationID` across `ExecStartPre=` and `ExecStart=` (checked 2026-11-21; distinguish the grades).**
- *Test assertion in the repository (host suite, not run in this check):* `tests/systemd_integration/test_route3_consume_host.py` (`test_a_complete_lifecycle_consumes_once_and_cleanup_reports_it`) runs the consume role as a real `ExecStartPre=+` of a disposable `rp11-capture-pass-a.service`, has the `ExecStart=` process write its own `$INVOCATION_ID`, and asserts `run-start.invocation_id == main-invocation == systemctl show InvocationID`. That is executable evidence for the pairing on `oracle-test`'s systemd, and only for that disposable unit and systemd version; it needs root and the oracle-test host.
- *Source-reading, not a test result:* the R2 citations record (`phase-5-0-p5-r5-rp11-h1-oh-s2-r1-citations.md`, row (n)) states from systemd source (`service.c:3026`) that one `InvocationID` per start is used for all commands of that start.
- *Not established:* that this pairing was accepted as a contract for **production** (Ubuntu 26.04.1 systemd) or for the Pass A launcher/entry; only the inert bootstrap exists, and the Pass A entry logic does not. The entry must still read `INVOCATION_ID` and pair it with the consume `run-start` itself; any production claim needs a run on the production-equivalent systemd, not this inference.


## 5. Start timeout and run-time policy

**What `TimeoutStartSec=` does.** Per the [systemd.service documentation](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html), for `Type=exec` the start job completes once the main binary has been successfully executed, and `TimeoutStartSec=` bounds `ExecStartPre=` plus startup up to that point. **It does not cap the full Pass A runtime.** The R2 and R1 remediation proposals ([`phase-5-0-p5-r5-rp11-h1-oh-s3-r2-remediation-proposal.md`](phase-5-0-p5-r5-rp11-h1-oh-s3-r2-remediation-proposal.md) line 98 and §8, [`phase-5-0-p5-r5-rp11-h1-oh-s3-r1-design-remediation-proposal.md`](phase-5-0-p5-r5-rp11-h1-oh-s3-r1-design-remediation-proposal.md) §7.3) record the same `Type=exec` handoff. Any text that treats this timeout as the pass budget is wrong.

**`RuntimeMaxSec=`.** It is a separate policy: it terminates a running service. Applied here it would kill a pass mid-run and could leave evidence inconclusive. **Recommendation: `RuntimeMaxSec=` stays absent** unless a separate design explicitly accepts forced mid-pass termination and its residue behavior. Each child command must have a deadline and a handled timeout must attempt one prescribed finalization (§4), but **no whole-service runtime bound is claimed** until the finite pass plan and the finalization bound are specified and tested. The entry contract is therefore **not ready** until its timeout/finalization behavior is proven. (The backstop unit's `RuntimeMaxSec=` in the R3 proposals concerns that unit, not this one.)

**D3-R4 AP-0 condition — historical, not current.** The D3-R4 one-host proposal (§4.2.5-R4 (g), A-2) required a finite recorded `TimeoutStartSec` of at least `⌈PO-11(d) bound/1,000⌉ + 30` seconds. This is a **historical accepted design condition for that one-host proposal. It is not a current production acceptance.** PO-11(d) bounds the **Polkit re-check**, not Pass A runtime. The earlier formula in this document, `max(P,B)+30`, is withdrawn: it treated the start timeout as if it covered a pass bound `B`, which it does not.

**Requirement and candidate.** One finite `TimeoutStartSec=` is a requirement of the new installer mechanics (§1), not an already accepted production design. **`TimeoutStartSec=90` is a candidate only.** Basis, in source: the R1 proposal (§7.3) records that HF-16 observed `DefaultTimeoutStartUSec=1min 30s` and that with P + c = 35,000 ms the D3 floor is 65 s, leaving 25 s under the default; the one-host amendment (item (r), "R2 §8 (r)", line ~2595) records the applicable start timeout in the H-1 baseline; and the installer tests and `test_rp11_capture_unit_install_host.py` use synthetic `TimeoutStartSec=90` fragments. Those are mechanics and design observations, not an acceptance of 90 for production. This is a concrete candidate, not an approval, and it caps only consume plus exec handoff.

Required before acceptance, on `oracle-test` with a synthetic unit name only:
1. Read back `TimeoutStartUSec` from the manager and confirm it is 90 s and finite.
2. Prove that consume plus exec handoff completes well inside 90 s under the real entry and the chosen identity.
3. If it does not fit, revise the value and re-read it. Do not stretch it to cover runtime.

## 6. Candidate sandbox (none accepted)

Candidates, in order of confidence:
- `ProtectSystem=strict`.
- `ProtectHome=read-only` (candidate, replacing `yes`). Caveats: home directories stay readable, so it does not hide them; any home write fails; and it must be tested against the chosen identity's home, the entry's reads and the evidence paths. Drop or narrow it if any of these conflict.
- `PrivateTmp=yes` and `PrivateDevices=yes`.
- An empty `CapabilityBoundingSet=` (no capabilities for the non-root main process).
- `ProtectKernelTunables=yes`, `ProtectKernelModules=yes`, `ProtectControlGroups=yes`, `LockPersonality=yes`.

Add `ReadWritePaths=` for the fixed capture root **only if** the reviewed runner writes there. Do not add a path until the runner is known.

**Needing compatibility tests** (real systemd on `oracle-test`, the real entry, one failing case per restriction): `ProtectSystem=strict` against the evidence write path; `ProtectHome` against any home access; `PrivateTmp`/`PrivateDevices` against temporary files, `/dev/null` and randomness; the empty capability set against every operation the entry performs; the kernel and cgroup protections; and an interaction check that the `+` pre-step still runs unrestricted while `ExecStart` is sandboxed. Also record the `systemd-analyze security` result per directive.

**No network or address-family restrictions are recommended** (`RestrictAddressFamilies`, `IPAddressDeny`, `PrivateNetwork`) until the commands and networks the entry needs are known. A syscall filter is likewise deferred until the entry exists and can be traced.

Other candidates from the earlier matrix keep their tests: stdio produces no secret or evidence-path echo and passes a journal retention check; `UMask=0077` gives intended evidence file modes; `Restart=no` leaves a failed pass `failed`, not retried; no `Environment=` or PAM directives, verified by manager read-back.

## 7. Gates (deployment kept separate)

1. **Design acceptance** (Peter): **direction accepted 2026-11-21** (§8 decision 1, launcher `ExecStart` direction). Decisions 2 to 4 (identity, sandbox, start timeout/bounded execution) remain open.
2. **Launcher rebuild and entry implementation, with independent review** (security-sensitive; required before production activation), including the §4 bounded-execution requirement. **Launcher Python 3.14 re-base: done; Codex independent review passed with no blocking findings. Inert G11/G12 bootstrap and its independent Codex review: done and passed (no remaining blocking findings); operational Pass A logic, evidence output and the `run-start` pairing: pending.**
3. **Fragment and SA-2 build change** in the repository, then focused tests and the installer suites against the real fragment. **Pending.**
4. **`oracle-test` rehearsal** (**pending**): install, verify and remove the real fragment under a synthetic name, then a genuine pass with consume evidence, running the canonical suites and quoting actual skips. This satisfies no production gate.
5. **Production installation**: a separate attended authorization (plan §14.2, handover), covering the changed SA-2 artifact and the unit install. Install is distinct from activation.
6. **Production activation and probes 2/6** (then 3 and 5): a further separate authorization with Peter attending.

Also open independently: confirm and remove the temporary broad sudo grant noted in the handover.

## 8. Product Owner decisions

1. **Decided: direction accepted by Peter Duscha (2026-11-21).** Retain the **static C launcher** re-based on 3.14. The candidate `ExecStart=/usr/local/libexec/freedom-blades-rp11/rp11-launch --pass A` is preserved as the proposal and is not runnable until a reviewed, digest-bound artifact contains the launcher and the entrypoint.

Still open (decisions 2 to 4):
2. Accept or revise the **service identity** (non-root; production account to be named).
3. Accept or revise the **sandbox** candidate in §6 (including `ProtectHome=read-only`).
4. Accept or revise the **start timeout** candidate (`TimeoutStartSec=90` as a candidate only; no `RuntimeMaxSec=` absent a separate accepted forced-termination design) and the **entrypoint bounded-execution requirement** (§4; if not guaranteed, the design is not ready).
5. **Production installation** and **production activation** remain two separate steps. Each requires separate, explicit authorization from Peter Duscha (Acceptance Authority) and Peter's attendance. This proposal grants neither. SA-2 rebuild authority belongs to the installation decision.

## 9. Conflicts with existing contracts

- Originally recorded: the `rp11_launch.py` contract (3.12, target `rp11_entry.py` then absent) conflicted with the 3.14 production baseline and §4 re-based it. **Updated 2026-11-21:** the 3.14 re-base is done in the launcher source and contract; outstanding are the operational Pass A logic in `rp11_entry.py` (only the inert bootstrap exists and is packaged by the source build definition), the unbuilt/uninstalled SA-2 artifact, and the absent production fragment.
- The D3-R4 text's `User=ubuntu` conflicts with the open production identity; and its `⌈PO-11(d)/1,000⌉+30` condition is a Polkit-window rule that is easily misread as a runtime rule.
- The previous revision of this proposal conflicted with systemd's documented `Type=exec` behavior; §5 corrects it.
- No conflict found with the installer: it judges only the consume vector, a single finite `TimeoutStartSec=`, no `[Install]` and the spec's required directives. Any `RuntimeMaxSec=` or sandbox line passes through unjudged, so the installer will not catch a wrong one.
