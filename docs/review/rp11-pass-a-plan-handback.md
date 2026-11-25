# Handback — single-host Pass A plan, child environments, identity and timeout policy (G2/G3/G7) — 2026-11-24

Slice: the finite local-only Pass A plan for the accepted single-host `oracle-test` topology —
fixed argv, complete non-inherited child environments, the `capture` identity as policy data,
measured per-class timeouts and the derived whole-pass bound.

**Status: implemented, tested and measured with synthetic stand-ins; accepted for review only.**
The entry still exits 69 and `run_pass_a` has no caller. No operational Pass A, source
acquisition, selected-path or `capture` account creation, A-2/AUTH grant, SA-2 build/install,
service install/activation, acceptance probe or production/staging access took place. The only
execution was the disposable-host measurement and tests described below.

## Delivered

* `tools/phase_5_0_evidence/execution/pass_a_plan.py` — data only (no process, file, account
  lookup, launcher or session; the entry and build closure do not import it). It is a **covered
  source of manifest v35** (65 → 66 sources).
  * **Plan (G2):** 49 fixed steps (51 with the RP-10-gated A1-11/A1-12); each argv has an absolute
    `argv[0]`, no shell, no `ssh`/`rsync`/`sudo`; expected non-zero exits are listed per step.
    Nine withdrawn-draft steps are kept in `WITHDRAWN_STEPS` with reasons. A test renders every
    argv through `guard-secrets.py`; all are admitted unchanged.
  * **Environments (G3):** `plain`, `git`, `python`, `systemd` — complete mappings, no inherited
    variables, no `HOME`, `INVOCATION_ID`, database URL or credential-shaped name.
  * **Identity (G5):** `CAPTURE_IDENTITY` and a pure `identity_problems(observed)`.
  * **Timeouts and bound (G7):** fixed class timeouts and the whole-pass bound are derived from
    the measured samples embedded in the module (24: 12 idle-ish + 12 loaded) by
    `timeout = max(floor, ceil(5 × slowest sample))`. Result: **T-local 44 s, T-dry 161 s,
    T-read 30 s (its floor); whole-pass bound 2466 s (49 steps), 2556 s with corroboration.**
    `require_operational()` refuses a plan whose used classes are unmeasured.
  * `validate_paths` now compares by position, not identity.
* `tests/test_rp11_pass_a_plan.py`, `tests/test_rp11_pass_a_measure.py` (opt-in host measurement).
* Manifest v35 and every pin derived from it.

## Measurement harness and its limits

The measurement pass runs under `plan.exit_policy()` — the policy an operational pass would use —
so any status the plan does not list for a step, and any signal, stops it. `verify_recorded_outcomes`
re-judges every recorded outcome and refuses a missing return code, a timeout, an exceeded bound,
an incomplete stream or a short launch count. Controls: a pure test requires the verifier to refuse
an expected failure that did not happen, an unexpected exit 1, SIGKILL, SIGTERM, each unclean flag
and a short run; a host test plans `uname -n` as expecting exit 3 and requires the pass to stop at
that step and the verifier to refuse the rows.

Samples: 24 whole runs × 51 steps on `oracle-test` (host `Test`, 2 CPUs), one sample being the
slowest step of a class in one run. Every step exited as planned; none timed out, exceeded its
bound or left a stream incomplete. Slowest samples: T-local 8.70 s, T-dry 32.08 s, T-read 2.71 s;
slowest whole run 64.70 s.

**Limitations (the timeouts are a statement about this shared host under the loads sampled, not a
proof for production):**

* **Synthetic stand-ins:** a scratch `git clone` replaced the selected checkout (plan paths rebased
  onto it) and a scratch capture root was used per round. The selected paths were untouched and
  do not exist.
* **Wrong identity:** every command ran as `ubuntu`, not `capture`; the account was not created, so
  permission-dependent behaviour is unmeasured.
* **The "idle" set was not quiet** (another session active, load average 1.2–3.8; 6.8–9.6 in the
  loaded set, which used three busy loops on two CPUs). The sets were taken in that order, not
  interleaved. An earlier, less contended set peaked at 7.1 / 18.7 / 4.6 s; it was discarded and is
  not merged. Figures move about twofold with contention.
* Deadlines during sampling were a generous test value, so a sample is a duration, not a pass
  against the final timeout.

## Test results (final tree)

| Where | Result |
|---|---|
| Codex, local focused | **978 passed, 4 skipped** (2 opt-in measurement, 2 `RLIMIT`) |
| Codex, `oracle-test` focused, with one strict synthetic measurement round | **980 passed, 2 `RLIMIT` skipped**, 176.46 s |
| `oracle-test` canonical bot `tests/test_*.py` (serial, default descriptor limit) | **8400 passed, 280 skipped, 6 warnings, 0 failures**, 2397.65 s |
| `oracle-test` canonical web, `TEST_DATABASE_URL` set | **2894 passed, 80 skipped, 1137 warnings, 0 failures**, 1157.90 s |
| `oracle-test` Foundry Node | **171 passed, 0 failed, 0 skipped**, 6.79 s |

The +2 bot skips versus v34 are the new opt-in measurement tests; the remaining skips keep their
documented root/ownership/toolchain/role/`RLIMIT` reasons. Codex's independent review found no
remaining blocking implementation or safety finding after the exit-policy remediation. This is
validation only and authorizes no operational action.

## Manifest and pins

Manifest v35 (66 covered sources; only `pass_a_plan.py` added): aggregate `79ca24be…77f6`, JSON
`a6d98d04…78bc` (377,690 bytes), concrete plan `0548e277…67e4` (178,764 bytes), regenerated from
the final source bytes. Pins re-derived in the operational prompt §4.3, the R5 assignment, the
runner `PINS` and digest, the four runner blocks and `tests/test_r5_runner.py`.

## Remaining boundary

1. Not authorized, not done: source acquisition, creating the selected paths or the `capture`
   account (G4 filesystem acceptance and the account's real properties are unobserved), A-2/AUTH,
   SA-2 build/install, service install/activation, probes, operational Pass A, production/staging.
   G6 final digest and SA-2 review, G9 and G10 remain open. All operational and production
   boundaries are unchanged.
2. Measurement under the real `capture` identity and paths has not happened; the checkout must be
   readable by `capture` (including `.git`) and published by the maintainer first.

**Next action:** the separately gated steps in item 1, in the maintainer's order. The plan module,
its tests and the v35 pins have been independently reviewed.

## Follow-up 2026-11-24 — G4 disposable-host result (filesystem acceptance FAILED)

With Peter's explicit disposable-host authorization, `oracle-test` was checked. The slice is
committed locally as `592678b` but not pushed, so exact-source acquisition remains blocked on
maintainer publication. Preflight: checkout and roots absent; `/opt/freedom-blades`
`ubuntu:ubuntu` 755; `/var/lib` `root:root` 755. `capture` was created by system `useradd` (uid
992, gid 978, locked, home `/nonexistent`, shell `/usr/sbin/nologin`, primary group only, no
sudo). Exclusive `mkdir --mode=700` as `capture` for `/var/lib/fb-rp11-capture-a` and `-b` each
returned rc 1 *Permission denied*; the roots remain absent.

**G4 filesystem acceptance failed:** the direct `/var/lib` leaves conflict with exclusive
creation by non-root `capture`. This also means the "wrong identity" and "paths untouched"
limitations above still stand: nothing was measured under `capture` or at the selected paths.
**Decision needed, none selected:** change the path/parent design, a narrowly provisioned parent,
or a revised exclusive-create lifecycle/security. Do not weaken `/var/lib` or silently precreate
the roots. Production untouched; no source acquired, `run_pass_a`, A-2/AUTH, SA-2, service,
activation or probe. No code or pin changed, so the results and manifest v35 above are unaffected.

## Follow-up 2 2026-11-24 — G4 scoped-parent redesign (Claude; for Codex review)

**Historical, superseded:** the 0730 mode, its open finding and the "Not done" host note below
are replaced by follow-ups 3 and 4.

Peter approved a narrowly provisioned parent. **Roots are now `/var/lib/fb-rp11/capture-a` and
`/var/lib/fb-rp11/capture-b`.** Parent contract: `/var/lib/fb-rp11` is pre-provisioned by root as
`root:capture` mode **0730** (root full; `capture` group write + search, no read or listing;
others nothing; no setuid/setgid/sticky); the leaves are absent before X-1 and created exclusively
mode 0700 by non-root `capture`; `/var/lib` stays `root:root` 755.

**Changed**
* `pass_a_plan.py`: `CAPTURE_PARENT`, roots derived from it; `ParentContract`/`PARENT_CONTRACT`;
  `ObservedDirectory` (an `lstat` observation with the full `st_mode`); pure `parent_problems`,
  `leaf_absent_problems`, `created_leaf_problems`; `validate_paths(..., parent=)` now requires the
  parent to be one component below `/var/lib`, each root a direct child of it, and no overlap with the
  checkout or `R`. No filesystem access, no step/argv/environment/measurement change.
* `tests/test_rp11_pass_a_plan.py` (+16 tests/cases): the contract's modes and owners; 19 unsafe
  parents each refused by name (wrong owner/group, 0755/0750/0770/0700/0731/0737/0777, setuid/setgid/
  sticky, 0330, symlink, file, wrong path); absent-before-X-1; created-leaf owner/mode/type; path
  refusals incl. the withdrawn direct leaf; checkers touch no filesystem; the open finding below.
* Manifest **v36** (covered bytes of `pass_a_plan.py` only; 66 sources): aggregate `0499adfb…0bfcd7`,
  JSON `59c5ab87…4e6c56` (377,690 bytes), concrete plan `171cfa12…7753` (178,764 bytes). The
  generator ran twice to scratch with byte-identical manifest, plan and output. Re-derived: the operational
  prompt, R5 assignment, runner `PINS`, blocks s01/s04c/s04d/s11 (incl. `review_manifest.py`
  `41bc4dff…3c80`, 80,219 bytes), `tests/test_r5_runner.py`, `test_r16_remediation`.
* Proposal §0b/§4/G4 row, implementation plan §16, handover, status, change-log.

**Superseded by follow-up 3 (mode 0770; no open finding).** *Original finding:* `CaptureRootStore.create_root` opens every ancestor `O_RDONLY` and
fsyncs the parent's directory entry. The group has no read on 0730, so the store cannot create a root
below the approved parent. Reproduced with an owner-`0330` stand-in (same rule, no root needed): `O_RDONLY`
EACCES; `O_PATH` open and `mkdirat`/`rmdir` succeed; `fsync` on `O_PATH` EBADF; `create_root` fails closed at
`X-1:open-ancestor` / `open-refused` and leaves nothing (pinned by a test that must be replaced when the store
changes). Options: change the store to traverse by `O_PATH` and settle a different durability barrier for the
root entry (a durability design choice, so not made here), or a parent mode that grants group read (e.g. 0770).
The store and `capture_mechanism` are unmodified.

**Not done.** `ssh oracle-test` from this sandboxed session fails with the documented
`Bad owner or permissions on /etc/ssh/ssh_config.d/…` artifact; the runbook forbids the `-F` workaround without
explicit authorization, so the parent was not provisioned and no leaf was created or removed as `capture`
(both leaves remain absent as last recorded). The measurement under `capture` and at the real paths is still
outstanding. Planned survey steps do not observe the parent (no step changed).

## Follow-up 3 2026-11-24 — parent mode 0770 (Claude; for Codex review)

Peter resolved the 0730-versus-store finding by changing the dedicated parent contract to
`/var/lib/fb-rp11` = `root:capture` mode **0770** (the directory is purpose-built and `capture` is its
only group member). `/var/lib` stays `root:root` 755; leaves stay absent before X-1 and are created
exclusively 0700 by non-root `capture`. **No open durability finding.**

**Changed**
* `pass_a_plan.py`: `PARENT_CONTRACT.mode = 0o770`; `parent_problems` reasons are now `group-cannot-read`,
  `group-cannot-create`, `other-access`, `special-bits`, `owner-bits`, `mode` (plus `path`, `not-a-directory`,
  `owner`, `group`). Docstrings no longer state an open finding. No step, argv, environment or measurement change.
* `tests/test_rp11_pass_a_plan.py`: 0770 accepted; 0730 (`group-cannot-read`), 0750, 0755, 0700, 0771, 0777, 0731,
  setuid/setgid/sticky 0770, 0370, wrong owner/group, link, file and wrong path refused with accurate reasons.
  The test pinning the store failure under 0330 is **removed** and replaced by an integration test using the
  unmodified `PosixCaptureFilesystem` and `CaptureRootStore` under a 0770 stand-in parent: X-1 creates the leaf
  exclusively as 0700 (and its subdirectories 0700), the root-entry and subdirectory-entry fsync barriers run and
  succeed, a second `create_root` on the existing leaf is refused (`X-1:create-root` / `object-exists`) and
  leaves it intact, and cleanup leaves the parent empty.
* Manifest **v37** (covered bytes of `pass_a_plan.py` and the version comment in `review_manifest.py`; 66 sources):
  aggregate `36ad663b…bbe41d5`, JSON `9b6fe73c…14ac87` (377,690 bytes), concrete plan `6e502219…87a5e5`
  (178,764 bytes), `review_manifest.py` `6c498490…591b7c` (80,791 bytes). Generator run twice to scratch with
  byte-identical manifest, plan and output. Re-derived: operational prompt, R5 assignment, runner `PINS`, blocks
  s01/s04c/s04d/s11, `tests/test_r5_runner.py`, `test_r16_remediation`.
* Proposal §0b/§4/G4 row, implementation plan §16, handover, status, change-log.

**Not done (remains for Codex).** Host validation: provisioning `/var/lib/fb-rp11` as `root:capture` 0770 and creating and
removing the leaves as the real `capture` account on `oracle-test`. No SSH, push, source acquisition or `run_pass_a`;
no A-2/AUTH, SA-2, service, probe or production/staging action. The stand-in test shows the unmodified store works
under 0770 permissions as the owning user; it does not prove behaviour as `capture` on the host.

## Follow-up 4 2026-11-25 — G4 host filesystem acceptance (Codex validation, recorded by Claude)

Documentation-only record of Codex's host validation; Claude did not run or re-observe it.

On `oracle-test`, under the `root:capture` mode 0770 parent `/var/lib/fb-rp11`, the
unmodified `CaptureRootStore` / `PosixCaptureFilesystem` ran as the capture account
(UID 992, GID 978) for both `/var/lib/fb-rp11/capture-a` and
`/var/lib/fb-rp11/capture-b`. Each leaf started absent; X-1 created it mode 0700, owned
992:978, with the durability path; a duplicate create was refused
(`X-1:create-root` / `object-exists`); cleanup restored it to absent. The parent ended
empty. Exact outputs:

```text
ok root=/var/lib/fb-rp11/capture-a uid=992 gid=978 mode=0700 duplicate=refused cleanup=absent
ok root=/var/lib/fb-rp11/capture-b uid=992 gid=978 mode=0700 duplicate=refused cleanup=absent
```

**G4 disposable filesystem acceptance is technically complete, pending final suite
evidence only.** It grants no operational authorization. Production and operational gates are unchanged. Exact-source
acquisition stays blocked until the maintainer publishes the final successor commit.
No push, source acquisition, `run_pass_a`, A-2/AUTH, SA-2, service, activation or probe.

**Limits.** No source was acquired, so this is not evidence from an acquired published
checkout. It is not a timing measurement: G7 figures remain unmeasured under `capture`
and at the selected paths. No push, source acquisition, `run_pass_a`, A-2/AUTH, SA-2,
service or production action. The 0730 mode and its open finding (follow-up 2) are
historical and superseded. No covered source, test, manifest or pin changed in this
follow-up.

**Next action:** final suite evidence, then maintainer publication of the final successor
commit. Source acquisition still needs its own authorization.

## Follow-up 5 2026-11-25 — final suite evidence (recorded by Claude; results supplied, not re-observed)

Documentation-only. On `oracle-test`, for the current tree (manifest v37; no source, test, manifest, plan or pin
changed by this record):

| Suite | Result |
|---|---|
| Focused reviewer suite | **780 passed in 68.20 s**, no skips or failures |
| Canonical bot suite (`tests/test_*.py`) | **8437 passed, 280 skipped, 6 warnings in 2494.81 s (0:41:34)**, exit 0 |
| Canonical web suite (`tests/web`) | **2894 passed, 80 skipped, 1137 warnings in 1212.82 s (0:20:12)**, exit 0 |
| Foundry Node suite | **171 passed, 0 failed, 0 skipped in 7689.042305 ms**, exit 0 |

The bot skips are the documented root/toolchain/opt-in environment gates; the web skips are permitted matrix cells
asserted by per-route success cases. These supersede the v35 figures above as the current-tree result.

**G4 disposable filesystem acceptance is complete** (follow-up 4 host result plus this evidence). It grants no
operational authorization: no push, source acquisition, `run_pass_a`, A-2/AUTH, SA-2, service or production action.
G7 timings remain unmeasured under `capture` and at the selected paths.

**Next action:** maintainer publication of the final successor commit; source acquisition still needs its own
authorization.

## Follow-up 6 2026-11-25 — publication record (observed by Codex, recorded by Claude; not re-observed)

Documentation-only. Supersedes every publication-pending statement above, including the "Next action" of follow-up 5.
Commit `b279de11978308b60ee9d491b43952cf9f113871` is published: `refs/heads/docs/platform-plan` on the canonical origin
`git@github.com:ming-themerciless/freedom-platform.git` pointed to it.

Publication does not authorize source acquisition, `run_pass_a`, A-2/AUTH, SA-2, services, staging or production.

**Next action:** none for publication; source acquisition still needs its own authorization.
