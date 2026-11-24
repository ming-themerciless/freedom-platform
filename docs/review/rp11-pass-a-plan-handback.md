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
