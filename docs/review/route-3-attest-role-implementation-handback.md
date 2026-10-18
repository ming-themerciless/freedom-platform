# Route 3 `attest` role (RT-5) — implementation handback

Date: 2026-10-17 · Executor: Claude · Reviewer after handback: Codex
Status: **accepted by Peter Duscha on 2026-10-18 for continued non-production
development**, built on accepted commit `94fb3e7`; the
review-remediation section at the end supersedes the verification and recommendation
sections. Independent Codex re-review found no implementation-quality blocker.
This acceptance does not authorize the non-root executor, OC-1/OC-2/OC-3, a production capture-unit
installer, or production/staging activation.

Current-state note: the dated remediation sections below correctly record that
acceptance and the executor assignment had not happened when each section was
returned. They are superseded by Peter's later RT-5 acceptance and the separate
2026-10-18 assignment of the non-root executor OC interruption slice in the
active handover; they are not current assignment statements.

## Delivered behavior

The interactive root recovery role

```text
sudo -n /usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py deact <activation_id> <a2_sha256> attest
```

* **First image.** Accepts only that vector, through the existing strict
  activation-id and lowercase-SHA-256 validators; every alias, option, extra or
  missing operand and case/whitespace variant is refused (exit 64) before any
  state operation. The environment-free decision is made from `argv` alone
  (`reads_environment_for`): `attest` joins `start` and `stop`, reads **no**
  environment variable (not `INVOCATION_ID`) and records no caller PID. H-FI
  controls are unchanged (fds 0–2 open, ≥3 closed and verified, signals/mask
  reset, umask `022`, cwd `/`, environment emptied). `stop-post`, `hold`,
  `backstop`, `consume` still read and validate `INVOCATION_ID`.
* **RT5.PRE** (`application/rp11/attest.py`). Before CL-G, three DI-1
  `ActiveState` reads — holder `<id>.service`, `<id>-backstop.timer`,
  `<id>-backstop.service`, all derived from the validated id — in that order,
  stopping at the first that decides. `activating`/`active`/`deactivating`/
  `reloading` ⇒ **`owner-active`, exit 30**. `inactive`, `failed` and a typed
  not-loaded refusal do not block. Anything else — timeout, disconnect, malformed
  or partial reply, unknown error, unexpected refusal, a non-`str` or any other
  state (`maintenance`, `refreshing`, case/whitespace variants) — is
  **`precondition-unestablished`, exit 31**. Either refusal creates no attempt
  directory, journal or record, removes nothing, makes no Polkit call, reads no
  authority or evidence file, takes no lock and starts/stops/resets nothing.
* **Cleanup.** Otherwise the existing `CleanupProcedure` runs once with the new
  closed trigger `attest` (`Trigger.ATTEST`); no CL/GRR/attribution/PK/2/record
  logic was copied. The holder's own PRE answer (`inactive`/`failed`/`not-found`)
  is the only observed fact passed into `holder_state`. Attempt numbering shares
  the existing sequence; `attest` was already a non-backstop trigger for the
  backstop firing bound.
* **Journal/record grammar.** `Invocation` carries `parent_pid`/`invocation_id`
  only for the two unit-started triggers and refuses them for `attest`. The
  attempt `run-start` grammar is refined, not padded: an `attest` line has **no
  `provenance` key at all**; `stop-post`/`backstop` keep their exact shape; an
  `attest` line with provenance, a unit-started line without it, and any
  trigger/`helper.role` hybrid involving `attest` are invalid. The deactivation
  record already admitted `attest` and carries no provenance.
* **Same boot** = ordinary CL. **Later boot** = CL-1 boot scoping unchanged:
  anything found under `/run` is A0 and kept; an absent object is
  `cleared-by-boot` only when boot ids differ, `/run` is observed tmpfs, a valid
  old identity line exists and the lookup is `ENOENT`. `st1-verified` still needs
  the existing CL-4 (`SEEK_NOT_AUTHORIZED` for `start`, one series, no retry) and
  CL-6 (baseline, capture unit) checks.
* **Result.** Exit 0 only for `st1-verified`; `1` hard-stop, `2` unit-still-active,
  `3` record-unpublished, `4` evidence-unwritable (GP-R3), `5` concurrent-deact
  (the cleanup's own map); **30** owner-active, **31** precondition-unestablished,
  **70** unexpected exception (one fixed line naming only the class; an unchecked
  activation id is never echoed). One bounded diagnostic line on stderr; no handler
  is installed, so default-action termination can leave a missing terminal record
  (every later gate stays fail-closed until a later attest succeeds).
* Inactive outside `oracle-test`: nothing creates units or installs the artifact.

## Files

New: `application/rp11/attest.py` (RT5.PRE + orchestration),
`adapters/rp11/attest.py` (composition root; reuses `StopPostServices` and
`build_procedure`), `tests/test_rp11_attest.py` (218),
`tests/systemd_integration/test_route3_attest_host.py` (11),
`tests/systemd_integration/test_route3_attest_reboot_host.py` (explicit phased
real-reboot proof).

Changed: `application/rp11/cleanup.py` (`Trigger.ATTEST`, optional provenance,
`run-start` without `provenance` for `attest`), `application/rp11/journal.py`
(per-trigger `run-start` schema + trigger/role cross-check), `adapters/rp11/
stop_post.py` (`build_procedure` accepts optional provenance),
`infra/rp11-h1/{rp11_h1.py,rp11_roles.py,build.py}` (vector, env-free selection,
up-front import, manifest: exactly the two new production modules, once each),
`tests/test_rp11_h1_artifact.py` (seven-vector pin, attest refusal/env cases),
`tests/test_rp11_cleanup.py` (`procedure()` takes `trigger`/`holder_state`),
`tests/web/test_p3_4_static_assets.py` (allowlist widened by exactly
`application/rp11/attest.py` and `adapters/rp11/attest.py`), and the five
current-state documents (implementation-plan, active-delivery-plan, status,
Handover information, review README).

## Row → test coverage

| Row | Executable proof |
|---|---|
| RT5.FI.1 vector, env-free, H-FI | `test_rp11_h1_artifact.py`: seven-vector acceptance, 25 added refused vectors, `test_no_environment_value_can_change_a_valid_attest` (7 hostile/oversized environments), genuine duplicate `INVOCATION_ID` via raw `execve`, `reads_environment_for`, unchanged provenance roles; imports/manifest tests |
| RT5.FI.2 / PRE.3 no handler, interruption | `test_default_signal_interruption_…` (9 points), Polkit-series and publication interruption, `test_no_signal_handler_…`; host: SIGTERM mid-series |
| RT5.PRE.1 three reads, blocking states | `test_a_live_owner_in_any_unit_refuses_before_cleanup` (3×4), permitted 27-combination matrix, 24 unestablished cases × 3 units, read-prefix order, no mutating call; host: every unit × state through the real manager |
| RT5.PRE.1 refusal changes nothing | `test_a_refusal_creates_reads_removes_and_asks_nothing` (tree snapshot, no authority read, no lock/Polkit/capture read); host snapshot equality and unchanged `ActiveState` |
| names derived from the validated id | `test_no_unit_name_comes_from_the_caller` (14 hostile ids), `test_another_activations_units_are_never_read`; host unrelated-unit test |
| RT5.PRE.2 same boot / later boot | `test_same_boot_…`, `test_a_later_boot_records_cleared_by_boot_…`, non-tmpfs, no mount fact, missing identity, unreadable boot id, planted pathname/rule, baseline mismatch; **host: real reboot** |
| RT5.CLG / CL0–CL7 / CLOUT / CLGP | same-boot success, damaged, foreign, unremovable (immutable on host), unit-still-active, capture read error, attempt exhaustion (exit 4), journal write/flush failures, record collision/flush (exit 3), concurrent attempt (exit 5) |
| RT5.CL4 / H-PK2 / H-SN | the **real PK/2 series** over scripted DI-5/DI-6: authorized, timeout, malformed reply, transport error, Polkit error, subject error, replaced subject, no subject, unready subject — each exactly one series, every child settled; denial and challenge are the positive result |
| attempt numbering | `test_attempt_numbers_share_one_sequence_…` (stop-post, attest, backstop, attest = 1…4; `is_backstop_attempt` false/false/true/false; no record overwritten) |
| journal/record grammar | `test_the_attempt_run_start_grammar_is_closed_per_trigger` (13 shapes), `Invocation` provenance guard, accepted `stop-post` shape test |
| RT5.OUT exits, diagnostic, no leak | exit-map tests, one-line composition-root tests, `internal-error` with no value, invalid id never echoed, module has no `os.environ`/process/signal use |
| DI-1 / DI-5 / DI-6 / H-SN on the host | host: real manager reads, real Polkit non-authorization through a real forked subject, children reaped |

Mutation checks (each fails a named test, then reverted): PRE ignores owners; PRE
coerces an unlisted state; `cleared-by-boot` without tmpfs; old boot treated as
same boot; `st1-verified` without the PK check (both the outcome rule and the ST-1
check removed); `attest` emitting provenance; record-schema errors swallowed at
publication.

## Commands and results

Superseded: the first submission's abbreviated commands were not reproducible. The exact
commands, working directories, exit statuses and counts run on the final tree are in
**Review remediation** below.

## Host cleanup

* After `prepare` (before the reboot): artifact built, tmpfiles fragment installed,
  three ACT evidence directories, store, A's rule/pass config live.
* After the reboot, before `verify`: `/run/freedom-blades-rp11` and the rule gone
  (tmpfs), `/run/polkit-1/rules.d` recreated empty by the fragment, evidence,
  artifact and the six protected directories present, `polkit.service` active.
* After `cleanup` and again after the whole systemd suite and the web/bot runs
  (checked in separate calls): no `rp11*` unit or process, no
  `/usr/local/libexec/freedom-blades-rp11`, `/var/lib/freedom-blades-rp11`,
  `/run/polkit-1`, `/var/tmp/rp11-*`, fragment, test unit file, foreign rule or
  proof state file; `polkit.service` active; `/var/tmp` is `root:root 1777`; the
  six protected directories untouched. The tmpfiles fragment was installed only for
  the proof and removed by `cleanup`.

## Effects and risks

No deployment, migration, schema or recovery change; nothing is active outside
`oracle-test`. The reboot proof installs and removes the repository's own
`tmpfiles.d` fragment through its accepted tool; test units are transient and
removed.

Remaining production risks: the retained PID/start-time/uid subject risk; the
transient inspection-failure decision; the final independent production security
review; `sudo` as the one launch preamble outside the controlled tree (EX-1);
the sequential, non-atomic PRE reads (a unit can start between the reads and CL —
DI-1 cannot offer a snapshot, and CL-G/CL-0's lock are what then serialize);
no executor yet decides when to attest or reports its record.

## Reversible choices

* **States outside the admitted set fail closed.** The explicitly admitted set is
  `inactive`, `failed` and typed not-loaded; the blocking set is the four
  transitional/active states. Everything else (`maintenance`, `refreshing`, a
  future state, wrong type/case/whitespace) is `precondition-unestablished`
  (exit 31) and is not coerced either way. Pinned in
  `test_the_admitted_state_sets_are_closed_and_disjoint` and the unestablished
  matrix; a newer systemd state refuses attestation until deliberately added.
* PRE stops at the first deciding read (a blocked holder does not read the other
  two); the diagnostic names that unit only.
* Exit map 30/31 (disjoint from the cleanup's 0–5, backstop 10–15, start/stop
  20–22, entry 64–77).
* `holder_state` records the holder's PRE answer; the record's `holder.invocation_id`
  is `absent` (no unit owns the run).
* On a real host an unloaded unit's `ActiveState` read returns `inactive` (systemd
  loads a stub), so the typed `NOT_LOADED` branch is exercised in unit tests only.

## Observations and recommendation

Superseded by **Review remediation** below (Observations 1 and 2 were the blocking
finding and are fixed; the recommendation is restated there).

## Review remediation (2026-10-17)

### Findings and dispositions

1. **Missing boot evidence became success — fixed.** `CleanupProcedure._verified()` ignored
   the recorded `invalid-journal` failure and accepted `never-linked` /
   `absent-before-removal`, so a changed-boot attest with missing ACT evidence, a
   non-`tmpfs` `/run` or no mount fact could publish `st1-verified` and exit 0.
2. **Abbreviated commands — fixed.** The old verification section is replaced; the exact
   commands run on the final tree are below, with no placeholder.

### Trigger-scoped success rule

`application/rp11/cleanup.py`: `_verified()` additionally requires `_attest_eligible()`.
It returns `True` for `stop-post` and `backstop`, so their behavior, tests and terminal
semantics are untouched. For `attest` it requires a valid ACT journal and no recorded
`invalid-journal` failure; and, after a boot change, none of the rule, pass-config,
`grant.id` or directory classes may be `never-linked` / `absent-before-removal`. Each
`/run` object must carry the full `cleared-by-boot` proof (boot ids differ, `/run`
observed `tmpfs`, valid old identity, ENOENT) or a durable earlier removal. Same-boot
with valid evidence is unchanged. Nothing new removes an object, reruns PK/2 or touches
the journal and record grammars. Failure token: `invalid-journal` for missing or invalid
ACT evidence; the existing `st1-not-verified` for a missing identity, non-tmpfs or
missing mount fact. Positive PK/2 `not-authorized` and a matching baseline remain
necessary and are not sufficient.

### Regression outcomes (`tests/test_rp11_attest.py`, 225 tests; red before the fix)

With the rule disabled, 9 tests failed (three existing weak-class tests, now also
requiring exit 1 / `hard-stop` / no `st1-verified`, and six new ones); with it, all pass.
Each of these gives exit 1, a durable `hard-stop` record and `st1.verified == false`:
ACT evidence directory missing (changed boot and same boot); ACT journal truncated before
the grant identity; ACT journal with a flipped byte (digest mismatch); non-`tmpfs`
`/run`; unavailable `/run` mount fact; and each of missing / non-tmpfs / no-mount-fact
with a real positive PK/2 `not-authorized` and equal baseline. Positive controls retained
and passing: same-boot success, changed-boot `cleared-by-boot` success, planted-path
hard-stop.

### Real-reboot A/B/C (boot id changed across the reboot)

* A (valid evidence): `st1-verified`, exit 0, rule and pass-config `cleared-by-boot`,
  `pk=not-authorized`.
* B (authorizing rule planted in the new boot): exit 1, kept `present-foreign-unremoved`.
* C (ACT evidence removed): through the installed `sudo -n` vector exit **1**,
  `rp11-cl hard-stop … failure=invalid-journal`, no `cleared-by-boot`, no `st1-verified`.

### Principal files changed

`application/rp11/cleanup.py`, `tests/test_rp11_attest.py`,
`tests/systemd_integration/test_route3_attest_reboot_host.py` (C now requires the
hard-stop), this handback and the five current-state documents (one sentence each: the
remediation was returned for independent Codex re-review).


The first remediation's verification list is superseded by the **Second review
remediation** below: it contained placeholders and prose substitutes, and every check was
rerun on the final tree with the literal commands recorded there.

## Second review remediation (2026-10-17)

### Findings and dispositions

1. **Missing directory identity still became success — fixed.** Directory cleanup rewrites
   `never-linked` to `never-created`, which is in `DIR_OK` and was not in the weak-class set.
   A linked activation-owned directory without its `dir-identity` line therefore reached
   `st1-verified` after a boot change.
2. **Non-reproducible final commands — fixed.** The old verification section is replaced;
   the section below holds only commands rerun on the final tree, with no placeholder.

### Trigger-scoped directory-evidence rule

`application/rp11/evidence.py`: `TreeEvidence` records every directory its `tree-intent`
member inventory declares (`declared`) and reports those with no `dir-identity` line
(`unidentified()`); `ActEvidence.unidentified_directories()` returns them for **linked**
trees only (tree P, an activation-created tree R and its nested `rules.d`). An unlinked
tree was never an activation object and contributes nothing; the lock directory's identity
is part of `run-start` and cannot be missing in a valid journal.

`application/rp11/cleanup.py`, `_attest_eligible()` (already `attest`-only; after a boot
change): any such path not covered by a durable prior `removed` fact for that exact path
makes the run ineligible, so `_verified()` is false. The result is exit 1, `hard-stop`,
`st1.verified == false` and the existing closed token `st1-not-verified`. A genuinely
pre-existing rules directory has no tree R in the journal and stays `pre-existing-kept`.
`never-created` is not added to a global failure set, nothing new is removed, and
same-boot cleanup, `stop-post`, `backstop`, `hold`, `consume`, `start` and `stop` are
untouched.

### Regression outcome (`tests/test_rp11_attest.py`, 234 tests)

Nine new tests rebuild the ACT journal through the production `serialize_line` and
`parse_journal` (contiguous `seq`, correct `prev` chain, only the named `dir-identity`
line removed) and run the real cleanup with real PK/2 `not-authorized` and an equal
baseline. With the `_attest_eligible` addition disabled, 4 failed: `tree-p-top`, `tree-r-top`
and `tree-r-rules.d` of the hard-stop test, and the exact-case test (tree P, other objects
`cleared-by-boot`). With it, all 9 pass. Retained positive controls, passing: changed boot
with every identity present and tree R (all recorded directories `cleared-by-boot`); a
pre-existing rules directory (`pre-existing-kept`); a durable prior removal of tree P
covering a missing identity (`removed-earlier`, exit 0, k=2); `stop-post` and `backstop`
still `st1-verified` for the same damaged journal; plus the earlier same-boot and
`cleared-by-boot` tests.

Observation, unchanged by this fix: after a boot change the cleanup does not record a
`cleared-by-boot` directory class for an activation-created tree R (it only classifies a
still-present rules directory). The new rule guards tree R through its identities; a
recorded per-directory class would be a separate, optional improvement.

### Real-reboot A/B/C, repeated (new boot id `988c7fd3-a332-4830-bc7f-25537329c7f9`)

`verify` passed 4 tests: A (valid evidence) `st1-verified`, exit 0, `cleared-by-boot`;
B (authorizing rule planted in the new boot) exit 1, kept `present-foreign-unremoved`;
C (ACT evidence removed) exit 1, `hard-stop`, `failure=invalid-journal`, no
`st1-verified`; plus the module's fourth `verify` test.

### Principal files changed

`application/rp11/evidence.py`, `application/rp11/cleanup.py`, `tests/test_rp11_attest.py`
(the other uncommitted files are the earlier RT-5 candidate, unchanged here), and this
handback.

### Final-tree commands and results

All on `oracle-test` over ssh from the repository host unless stated; working directory
`/opt/freedom-blades/platform`; interpreter `/opt/freedom-blades/runtime/venv-web/bin/python`.
The tree was synchronized once after the last code change; only this handback changed
afterwards.

1. Synchronization (repository host, `/opt/freedom-blades/platform`), exit 0:
   ```bash
   rsync -avz --delete --include='.env.example' --exclude='.env*' --exclude='*.pem' --exclude='*.key' --exclude='*service_account*.json' --exclude='*credentials*.json' --exclude='__pycache__/' --exclude='*.py[cod]' --exclude='.pytest_cache/' /opt/freedom-blades/platform/ oracle-test:/opt/freedom-blades/platform/
   ```
2. Focused set, exit 0, **2332 passed, 2 skipped** (97 s; skips: `RLIMIT_NOFILE` above
   1048583, hard 524288, ×2) — includes the complete `tests/test_rp11_attest.py`:
   ```bash
   ssh oracle-test "cd /opt/freedom-blades/platform && /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/test_rp11_attest.py tests/test_rp11_consume.py tests/test_rp11_h1_artifact.py tests/test_rp11_hold.py tests/test_rp11_cleanup.py tests/test_rp11_backstop.py tests/test_rp11_records.py tests/test_rp11_pk_sn.py tests/test_rp11_start.py tests/test_rp11_stop.py tests/test_systemd_unit_control.py"
   ```
   The attest module alone, exit 0, **234 passed**, 0 skipped:
   ```bash
   ssh oracle-test "cd /opt/freedom-blades/platform && /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/test_rp11_attest.py"
   ```
3. Root host module (fresh artifact from the pinned wheel), exit 0, **11 passed**, 0 skipped (50 s):
   ```bash
   ssh oracle-test "cd /opt/freedom-blades/platform && sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_RP11_WHEEL=/home/ubuntu/jeepney-0.9.0-py3-none-any.whl /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/systemd_integration/test_route3_attest_host.py"
   ```
4. Real reboot, in this order:
   * `prepare`, exit 0, **1 passed, 5 skipped** (skips: `phase is not 'verify'` ×4,
     `phase is not 'cleanup'` ×1):
     ```bash
     ssh oracle-test "cd /opt/freedom-blades/platform && sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_RP11_WHEEL=/home/ubuntu/jeepney-0.9.0-py3-none-any.whl FREEDOM_ATTEST_REBOOT_PHASE=prepare /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/systemd_integration/test_route3_attest_reboot_host.py"
     ```
   * reboot (exit 0) and the readiness wait (loops until ssh answers; printed boot time
     2026-10-17 22:15:46 and the new boot id):
     ```bash
     ssh oracle-test "sudo systemctl reboot"
     until ssh -o ConnectTimeout=5 -o BatchMode=yes oracle-test "uptime -s; cat /proc/sys/kernel/random/boot_id"; do sleep 5; done
     ```
   * `verify`, exit 0, **4 passed, 2 skipped** (skips: `phase is not 'prepare'`,
     `phase is not 'cleanup'`):
     ```bash
     ssh oracle-test "cd /opt/freedom-blades/platform && sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_RP11_WHEEL=/home/ubuntu/jeepney-0.9.0-py3-none-any.whl FREEDOM_ATTEST_REBOOT_PHASE=verify /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/systemd_integration/test_route3_attest_reboot_host.py"
     ```
   * `cleanup`, exit 0, **1 passed, 5 skipped** (skips: `phase is not 'prepare'` ×1,
     `phase is not 'verify'` ×4):
     ```bash
     ssh oracle-test "cd /opt/freedom-blades/platform && sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_RP11_WHEEL=/home/ubuntu/jeepney-0.9.0-py3-none-any.whl FREEDOM_ATTEST_REBOOT_PHASE=cleanup /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/systemd_integration/test_route3_attest_reboot_host.py"
     ```
5. Whole systemd suite, serially, exit 0, **153 passed, 3 skipped** (796 s). Skips: the
   reboot module without a phase (`set FREEDOM_ATTEST_REBOOT_PHASE=prepare|verify|cleanup`)
   and two hold tests needing `FREEDOM_TMPFILES_BOOT_PROOF=1`:
   ```bash
   ssh oracle-test "cd /opt/freedom-blades/platform && sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_RP11_WHEEL=/home/ubuntu/jeepney-0.9.0-py3-none-any.whl /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/systemd_integration"
   ```
6. Static assets, exit 1, **2 failed, 109 passed**, 0 skipped:
   ```bash
   ssh oracle-test "cd /opt/freedom-blades/platform && /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/web/test_p3_4_static_assets.py"
   ```
   Failures: `test_the_discovery_enumerates_untracked_files_rather_than_directories` and
   `test_every_evidence_harness_source_in_the_tree_is_declared`. Baseline comparison, freshly
   run against accepted commit `94fb3e7` (exit 1, the same two failures, 109 passed):
   ```bash
   ssh oracle-test "git -C /opt/freedom-blades/platform worktree add --detach /var/tmp/base-94fb3e7 94fb3e7 && cd /var/tmp/base-94fb3e7 && /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/web/test_p3_4_static_assets.py"
   ```
7. Bot then web, serially. Wrapper creation (resets SIGHUP/SIGINT/SIGQUIT to `SIG_DFL`),
   runner creation, and invocation, in this order:
   ```bash
   ssh oracle-test "printf '%s\n' 'import os, signal, sys' 'for s in (signal.SIGHUP, signal.SIGINT, signal.SIGQUIT):' '    signal.signal(s, signal.SIG_DFL)' 'os.execv(\"/bin/bash\", [\"bash\", \"-c\", sys.argv[1]])' > /tmp/run-reset.py && cat /tmp/run-reset.py && rm -rf /tmp/pytest-of-ubuntu && pgrep -af 'rotate-test-gate|caddy validate' | grep -v pgrep; echo ok"
   ssh oracle-test "rm -f /var/tmp/bot.log /var/tmp/web.log; rm -rf /tmp/pytest-of-ubuntu; printf '%s\n' 'cd /opt/freedom-blades/platform' \"export PATH='/usr/lib/postgresql/16/bin:/usr/bin:/bin'\" \"export TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'\" '/opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/test_*.py > /var/tmp/bot.log 2>&1; echo BOT_EXIT=\$? >> /var/tmp/bot.log' '/opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/web > /var/tmp/web.log 2>&1; echo WEB_EXIT=\$? >> /var/tmp/web.log' > /tmp/run-suites.sh; cat /tmp/run-suites.sh"
   ssh oracle-test "python3 /tmp/run-reset.py 'bash /tmp/run-suites.sh'"
   ```
   (An earlier attempt with a single nested-quoted invocation was stopped within seconds,
   before any result, and replaced by the above; no output of it is used.)
   * bot: `BOT_EXIT=1`, **6 failed, 6722 passed, 20 skipped, 39 errors** (959 s). All 45 are in
     `tests/test_r5_runner.py` (5 F, 39 E) and `tests/test_sheet_bootstrap_boundary.py` (1 F).
     Exact baseline comparison against the `94fb3e7` worktree from item 6, run as:
     ```bash
     ssh oracle-test "grep -E '^(FAILED|ERROR)' /var/tmp/bot.log | sed 's/ - .*//' | sort > /var/tmp/final-ids.txt; cd /var/tmp/base-94fb3e7 && PATH='/usr/lib/postgresql/16/bin:/usr/bin:/bin' TEST_DATABASE_URL='postgresql+psycopg:///freedom_test' /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfE tests/test_r5_runner.py tests/test_sheet_bootstrap_boundary.py > /var/tmp/base.log 2>&1; tail -1 /var/tmp/base.log; grep -E '^(FAILED|ERROR)' /var/tmp/base.log | sed 's/ - .*//' | sort > /var/tmp/base-ids.txt; wc -l /var/tmp/final-ids.txt /var/tmp/base-ids.txt; diff /var/tmp/final-ids.txt /var/tmp/base-ids.txt && echo IDS_IDENTICAL"
     ```
     The baseline run gave 6 failed, 39 passed, 39 errors; both ID lists have 45 lines and
     `diff` printed `IDS_IDENTICAL`. Skips (20): 16 `RP11_LAUNCH_BUILD_ROOT is not set`, 2
     `RLIMIT_NOFILE`, 2 backup-role ("needs exactly one non-owner role holding table grants;
     found none").
   * web: `WEB_EXIT=1`, **2 failed, 2890 passed, 80 skipped** (578 s). The skip count is the
     documented 80 (54 in `tests/web/test_p3_2_matrix.py`, 26 in `tests/web/test_p3_3_matrix.py`:
     "permitted cells are asserted by the per-route success cases"). The two failures are item 6's baseline pair.
8. Foundry, exit 0, 171 tests, **171 pass**, 0 fail, 0 skipped:
   ```bash
   ssh oracle-test "cd /opt/freedom-blades/platform && node --test 'foundry-module/tests/'*.test.mjs 2>&1 | tail -9"
   ```
9. Compilation, repository host, `/opt/freedom-blades/platform`, exit 0, all 15 printed `ok`:
   ```bash
   python3 -B -c "
   files='''adapters/rp11/stop_post.py application/rp11/cleanup.py application/rp11/journal.py application/rp11/evidence.py infra/rp11-h1/build.py infra/rp11-h1/rp11_h1.py infra/rp11-h1/rp11_roles.py tests/test_rp11_cleanup.py tests/test_rp11_h1_artifact.py tests/web/test_p3_4_static_assets.py adapters/rp11/attest.py application/rp11/attest.py tests/systemd_integration/test_route3_attest_host.py tests/systemd_integration/test_route3_attest_reboot_host.py tests/test_rp11_attest.py'''.split()
   for f in files:
       compile(open(f).read(), f, 'exec'); print('ok', f)
   "
   ```
10. Guards, repository host, exit 0, "40 cases: 26 must be refused, 14 must be allowed; all
    guard cases passed": `python3 .claude/hooks/test_guards.py`. No mypy, ruff or other
    static checker is installed or configured.
11. Whitespace, repository host, `/opt/freedom-blades/platform`: `git diff --check` exit 0, no
    output. Untracked files, each checked (exit 1 with no output means a difference and no
    whitespace finding; a file with trailing whitespace exits 3 and prints it, verified with a control):
    ```bash
    for f in $(git ls-files --others --exclude-standard); do git diff --check --no-index /dev/null "$f"; echo "exit=$? $f"; done
    ```
    All nine untracked files gave `exit=1` and no output; the command was re-run after this
    handback was written, with the same result.
12. Host cleanliness, inspected in separate calls after the root test (3), after the reboot
    proof (4), and after all suites and the removal of the baseline worktree and scratch files.
    The final command:
    ```bash
    ssh oracle-test "ls -d /usr/local/libexec/freedom-blades-rp11 /var/lib/freedom-blades-rp11 /run/polkit-1 /var/tmp/rp11-* /run/rp11-* /var/tmp/base-94fb3e7 /tmp/run-reset.py /tmp/run-suites.sh 2>&1; systemctl list-units --all 'rp11*' --no-legend; pgrep -af 'rp11|rotate-test-gate|caddy validate' | grep -v pgrep; systemctl is-active polkit; stat -c '%U:%G %a %n' /var/tmp /usr/local/libexec; ls -d /var/tmp/p5-r5-rp11-h0* | wc -l; git -C /opt/freedom-blades/platform worktree list"
    ```
    Result (the first two calls used the same command without the temp-path and worktree entries): every listed path absent, no `rp11*` unit or process, no orphaned
    gate or `caddy` process, `polkit` active, `/var/tmp` `root:root 1777`, `/usr/local/libexec`
    `root:root 755`, six `/var/tmp/p5-r5-rp11-h0*` directories, and one worktree
    (`/opt/freedom-blades/platform`). Production and staging were not touched; only synthetic data.

### Unchanged remaining production risks

Retained PID/start-time/uid subject risk; the transient inspection-failure decision; the
final independent production security review; `sudo` as the launch preamble outside the
controlled tree; non-atomic sequential PRE reads; no executor yet decides when to attest;
and no per-directory `cleared-by-boot` record for an activation-created tree R (see the
observation above).

### Recommendation

Accept RT-5 for continued non-production development; no remaining blocker is known.
Peter's acceptance is not recorded here, and the non-root executor and OC checks are not assigned.

## Third review remediation (2026-10-18)

### Finding and disposition

**Missing mandatory tree-P evidence still became success — fixed.** After a boot change a
canonically valid, correctly chained ACT journal could omit tree P's `tree-intent` or its
`tree-linked` line. No tree P then existed in `ActEvidence` (or it was unlinked), so the set
of unidentified linked directories was empty, cleanup classed the fixed path `never-created`
and RT-5 published `st1-verified`.

### Mandatory tree-P evidence rule

`application/rp11/evidence.py`: `TreeEvidence` now also records the declared file members,
declared directory modes, the number of `tree-linked` lines that followed the intent
(`links`) and whether the history was ordered (`ordered`: no `dir-identity` after a link, no
link naming another path). `TreeEvidence.is_exactly(...)` and `ActEvidence.trees_at(...)`
test the shape. `application/rp11/cleanup.py`: `_tree_p_recorded()`, called first in the
`attest`-only, changed-boot part of `_attest_eligible()`, requires exactly one tree-P-tagged
intent in the journal and exactly one tree at the fixed parent/top, with parent `/run`, the
fixed top, temp `.rp11-<id>-p.tmp`, tag `p`, directory inventory `[top 0755]`, file inventory
`[pass-a.json]`, exactly one matching link, and in order. Any other history (missing,
duplicated, reordered, mismatched, wrong parent/top/tag/temp/mode/member, hybrid) makes the
run ineligible: exit 1, `hard-stop`, `st1.verified == false`, token `st1-not-verified`. The
existing identity rule follows: a missing top identity still needs a durable prior `removed`
fact for that exact path; a prior removal does not stand in for a missing intent or link.
Tree R is unchanged (conditional; a genuinely pre-existing rules directory stays permitted).
Same-boot cleanup, `stop-post`, `backstop` and the other roles are untouched. Nothing new
is removed and no pathname absence is treated as proof.

### Red-before / fixed-after (`tests/test_rp11_attest.py`)

Twenty new tests rebuild the ACT journal through the production `serialize_line` (contiguous
`seq`, correct `prev`; `parse_journal(...).valid` asserted) and run the real cleanup with
real PK/2 `not-authorized` and an equal baseline. Against the pre-fix candidate (the
`_tree_p_recorded` check absent) 16 of the 20 failed, including both primary cases:
missing `tree-intent` and missing `tree-linked` each returned exit 0 / `st1-verified` with
classes `never-created`. Fixed: all pass. Variants covered: wrong parent, top, tag, temp,
mode, file member, extra directory; link with wrong top or parent; duplicate intent, link
and identity; a twin intent; link before identity; prior removal with a missing intent. The
other 4 of the 20 passed before the fix (they include the `stop-post`/`backstop` unchanged controls). Retained
positive controls (full changed-boot evidence, tree R, pre-existing rules directory, durable
prior removal, same-boot) all still pass.

### Real reboot (new boot id `ee223a51-1224-41c9-b1f3-17b755018688`)

`verify` passed 6, skipped 2: boot cleared objects and kept evidence; C (no journal) exit 1
`invalid-journal`; **D** (valid chain, tree-P `tree-intent` removed) and **E** (valid chain,
`tree-linked` removed) each exit 1, `hard-stop`, PK `not-authorized`, baseline equal, tree P
`never-created`, failure `st1-not-verified`, no `st1-verified`; B (planted rule) exit 1,
kept; A (valid evidence) exit 0, `st1-verified`, `cleared-by-boot`.

### Principal files changed

`application/rp11/evidence.py`, `application/rp11/cleanup.py`, `tests/test_rp11_attest.py`,
`tests/systemd_integration/test_route3_attest_reboot_host.py` (cases D, E), this handback,
and one-sentence status lines in the four current-state documents.

### Final-tree commands and results

Working directory `/opt/freedom-blades/platform`; interpreter
`/opt/freedom-blades/runtime/venv-web/bin/python`; the tree was synchronized after the last
code change (only docs changed afterwards). Wheel `/home/ubuntu/jeepney-0.9.0-py3-none-any.whl`.

1. Sync (repository host), exit 0: the documented command of the second remediation.
2. Focused set, exit 0, **2351 passed, 2 skipped** (`RLIMIT_NOFILE` above 1048583, hard
   524288, x2): the same `ssh oracle-test "... pytest -q -rfEs tests/test_rp11_attest.py
   tests/test_rp11_consume.py tests/test_rp11_h1_artifact.py tests/test_rp11_hold.py
   tests/test_rp11_cleanup.py tests/test_rp11_backstop.py tests/test_rp11_records.py
   tests/test_rp11_pk_sn.py tests/test_rp11_start.py tests/test_rp11_stop.py
   tests/test_systemd_unit_control.py"` as in the second remediation. Attest module alone:
   exit 0, **253 passed**.
3. Root host module, exit 0, **11 passed**: `ssh oracle-test "cd /opt/freedom-blades/platform &&
   sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_RP11_WHEEL=<wheel>
   /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs
   tests/systemd_integration/test_route3_attest_host.py"`.
4. Reboot, same command with `FREEDOM_ATTEST_REBOOT_PHASE=` `prepare` (exit 0, 1 passed, 7
   skipped: other phases), `ssh oracle-test "sudo systemctl reboot"` plus the
   `until ssh ... uptime -s; cat boot_id` wait loop, `verify` (exit 0, 6 passed, 2 skipped:
   `prepare`, `cleanup`), `cleanup` (exit 0, 1 passed, 7 skipped).
5. Whole systemd suite, serial, same env without the phase, exit 0, **153 passed, 3 skipped**
   (826 s): the reboot module without a phase and two hold tests needing
   `FREEDOM_TMPFILES_BOOT_PROOF=1`.
6. Static assets, exit 1, **2 failed, 109 passed**; the same two tests
   (`test_the_discovery_enumerates_untracked_files_rather_than_directories`,
   `test_every_evidence_harness_source_in_the_tree_is_declared`) fail identically, 2 failed /
   109 passed, in a fresh detached worktree of `94fb3e7`.
7. Bot then web, serially, via the SIGHUP/SIGINT/SIGQUIT-reset wrapper and
   `TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'`, `PATH='/usr/lib/postgresql/16/bin:/usr/bin:/bin'`
   (commands as in the second remediation):
   * bot `BOT_EXIT=1`: **6 failed, 6741 passed, 20 skipped, 39 errors** (1049 s). The 45
     failing/erroring IDs (`tests/test_r5_runner.py`, `tests/test_sheet_bootstrap_boundary.py`)
     are identical to the `94fb3e7` worktree's (6 failed, 39 passed, 39 errors; `diff` printed
     `IDS_IDENTICAL`). Skips: 16 `RP11_LAUNCH_BUILD_ROOT is not set`, 2 `RLIMIT_NOFILE`, 2
     backup-role ("needs exactly one non-owner role holding table grants").
   * web `WEB_EXIT=1`: **2 failed, 2890 passed, 80 skipped** (726 s); skip count 80 (54
     `test_p3_2_matrix.py`, 26 `test_p3_3_matrix.py`); the two failures are item 6's pair.
8. Foundry: `ssh oracle-test "cd /opt/freedom-blades/platform && node --test
   'foundry-module/tests/'*.test.mjs > /var/tmp/node.log 2>&1; echo NODE_EXIT=$?"` printed
   `NODE_EXIT=0`; 171 tests, 171 pass, 0 fail, 0 skipped.
9. Compilation over the 15 touched Python paths of the second remediation, repository host:
   all `ok`. Guards: `python3 .claude/hooks/test_guards.py`, exit 0 (26 refused / 14 allowed).
   `git diff --check` exit 0; each of the untracked files checked with
   `git diff --check --no-index /dev/null <file>`: no whitespace finding. No mypy, ruff or
   other static checker is configured.
10. Host cleanliness, separate calls after the root test, after the reboot `cleanup`, and
    after all suites and removal of the baseline worktree and scratch files: no
    `/usr/local/libexec/freedom-blades-rp11`, `/var/lib/freedom-blades-rp11`, `/run/polkit-1`,
    `/var/tmp/rp11-*`, `/run/rp11-*`, proof-state file, tmpfiles fragment, `rp11*` unit,
    process, orphaned gate/`caddy` process or extra worktree; `polkit` active; `/var/tmp`
    `root:root 1777`; `/usr/local/libexec` `root:root 755`; six `/var/tmp/p5-r5-rp11-h0*`
    directories (and, in the proof, their facts unchanged). Production and staging untouched;
    only synthetic data.

### Unchanged remaining production risks

As before: retained PID/start-time/uid subject risk; the transient inspection-failure
decision; the final independent production security review; `sudo` as the launch preamble
outside the controlled tree; non-atomic sequential PRE reads; no executor yet decides when
to attest; no per-directory `cleared-by-boot` record for an activation-created tree R.

### Recommendation

Accept RT-5 for continued non-production development; no remaining blocker is known. Peter's
acceptance is not recorded here, and the non-root executor and OC checks are not assigned.

## Fourth review remediation (2026-10-18)

This section supersedes only the third section's "Final-tree commands and results" presentation
and its recommendation. No implementation, test, artifact or unit file changed; the third
section's implementation result is the unchanged candidate under review.

### Finding and disposition

**The third remediation's final-tree record was not reproducible and two exit statuses were
unreliable — corrected (documentation only).** The third section used backward references and
placeholders (`<wheel>`, "same command", "as in the second remediation") and recorded the
Foundry run as `ssh oracle-test "... node --test ... > /var/tmp/node.log 2>&1; echo NODE_EXIT=$?"`.
There `$?` sits inside a locally double-quoted argument, so the local shell expands it, and the
trailing `echo` would in any case make SSH return the status of `echo`, not of `node`.

Evidence recovery. The exact commands and outputs of the third-remediation run were recovered
from the retained Claude Code session transcript of that run
(`~/.claude/projects/-opt-freedom-blades-platform/730e3055-3c29-426f-af9f-f98d73ee5821.jsonl`,
tool calls and results at 2026-10-18T00:05Z–00:56Z) and are copied literally below, marked
**[third-run transcript]**. Checks marked **[rerun in this correction]** were executed again
today on the synchronized tree. Nothing is reconstructed or normalized.

* Withdrawn and replaced by fresh reruns: (a) the Foundry command and its status (above);
  (b) the static-assets result's "exit 1", because the third-run command was piped to `tail -6`,
  so the recorded status was `tail`'s, not pytest's; (c) the guards status, piped to `tail -2`
  for the same reason. The third-run test counts for (b) and (c) were genuine and are
  corroborated by the reruns.
* The third section's "Compilation over the 15 touched paths of the second remediation" is now
  spelled out with the complete path list (item 9).
* All third-run results other than (a)–(c) are retained: each has a literal command and a
  status that is the status of the tested process (`echo exit=$?` directly after the `ssh`, or
  `…_EXIT=$?` written inside the remote script immediately after pytest).

### Common facts

Repository host working directory `/opt/freedom-blades/platform`. On `oracle-test`: working
directory `/opt/freedom-blades/platform`; interpreter `/opt/freedom-blades/runtime/venv-web/bin/python`;
wheel `/home/ubuntu/jeepney-0.9.0-py3-none-any.whl` (pinned `jeepney 0.9.0`); material
environment: `FREEDOM_SYSTEMD_INTEGRATION=oracle-test`, `FREEDOM_RP11_WHEEL`,
`FREEDOM_ATTEST_REBOOT_PHASE` (reboot module only), and, for the bot and web suites,
`PATH='/usr/lib/postgresql/16/bin:/usr/bin:/bin'` and
`TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'` (the root suites deliberately do not
override `PATH`). Production and staging were not touched; synthetic data only.

### Code unchanged since the third-run sync

The third run synchronized once after its last code change (00:05:51Z). Today's sync below
transferred only `docs/review/route-3-attest-role-review-remediation-r4-claude-prompt.md` (and
`.git` bookkeeping), and deleted two remote-only directories `.codex/` and `.aws/` that are not
part of the tree. No code, test or artifact file was re-sent, which corroborates that the
third-run results below describe the current code.

### Commands, statuses and results

**1. Secret-excluding synchronization** — [rerun in this correction], repository host, exit 0
(the secrets guard admits only this bare form):

```bash
rsync -avz --delete --include='.env.example' --exclude='.env*' --exclude='*.pem' --exclude='*.key' --exclude='*service_account*.json' --exclude='*credentials*.json' --exclude='__pycache__/' --exclude='*.py[cod]' --exclude='.pytest_cache/' /opt/freedom-blades/platform/ oracle-test:/opt/freedom-blades/platform/
```

**2. Focused set** — [third-run transcript], `exit=0`, **2351 passed, 2 skipped** in 97.69 s;
skips (2): `tests/test_rp11_h1_artifact.py:1107` "cannot raise RLIMIT_NOFILE above 1048583 (hard
524288, nr_open 2147483584)" ×2:

```bash
ssh oracle-test "cd /opt/freedom-blades/platform && /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/test_rp11_attest.py tests/test_rp11_consume.py tests/test_rp11_h1_artifact.py tests/test_rp11_hold.py tests/test_rp11_cleanup.py tests/test_rp11_backstop.py tests/test_rp11_records.py tests/test_rp11_pk_sn.py tests/test_rp11_start.py tests/test_rp11_stop.py tests/test_systemd_unit_control.py"; echo exit=$?
```

Attest module alone — [third-run transcript], `exit=0`, **253 passed**, 0 skipped, 6.06 s:

```bash
ssh oracle-test "cd /opt/freedom-blades/platform && /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/test_rp11_attest.py"; echo exit=$?
```

**3. Root host module** — [third-run transcript], `exit=0`, **11 passed**, 0 skipped, 46.80 s:

```bash
ssh oracle-test "cd /opt/freedom-blades/platform && sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_RP11_WHEEL=/home/ubuntu/jeepney-0.9.0-py3-none-any.whl /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/systemd_integration/test_route3_attest_host.py"; echo exit=$?
```

**4. Real reboot, in this order** — [third-run transcript]. Boot id before: not recorded;
after: `ee223a51-1224-41c9-b1f3-17b755018688` (boot time 2026-10-18 00:09:47). Today's host still
reports that boot id; no reboot was done in this correction.

`prepare`, `exit=0`, **1 passed, 7 skipped** (`phase is not 'verify'` ×6 across five lines
(1+1+2+1+1) and `phase is not 'cleanup'` ×1):

```bash
ssh oracle-test "cd /opt/freedom-blades/platform && sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_RP11_WHEEL=/home/ubuntu/jeepney-0.9.0-py3-none-any.whl FREEDOM_ATTEST_REBOOT_PHASE=prepare /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/systemd_integration/test_route3_attest_reboot_host.py"; echo exit=$?
```

Reboot and readiness loop (`exit=0` printed for the reboot request; the loop printed eight
`ssh: connect … Connection timed out/refused` lines, then `2026-10-18 00:09:47` and the boot id):

```bash
ssh oracle-test "sudo systemctl reboot"; echo exit=$?; sleep 20; until ssh -o ConnectTimeout=5 -o BatchMode=yes oracle-test "uptime -s; cat /proc/sys/kernel/random/boot_id"; do sleep 5; done
```

`verify`, `exit=0`, **6 passed, 2 skipped** (`phase is not 'prepare'`, `phase is not 'cleanup'`):

```bash
ssh oracle-test "cd /opt/freedom-blades/platform && sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_RP11_WHEEL=/home/ubuntu/jeepney-0.9.0-py3-none-any.whl FREEDOM_ATTEST_REBOOT_PHASE=verify /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/systemd_integration/test_route3_attest_reboot_host.py"; echo exit=$?
```

`cleanup`, `exit=0`, **1 passed, 7 skipped** (`prepare` ×1, `verify` ×6):

```bash
ssh oracle-test "cd /opt/freedom-blades/platform && sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_RP11_WHEEL=/home/ubuntu/jeepney-0.9.0-py3-none-any.whl FREEDOM_ATTEST_REBOOT_PHASE=cleanup /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/systemd_integration/test_route3_attest_reboot_host.py"; echo exit=$?
```

**5. Whole systemd suite, serially** — [third-run transcript], `SYSD_EXIT=0` (written to the log
inside the remote script directly after pytest), **153 passed, 3 skipped** in 826.60 s. Skips:
`test_route3_attest_reboot_host.py:56` "set FREEDOM_ATTEST_REBOOT_PHASE=prepare|verify|cleanup
(the real-reboot proof is explicit)"; `test_route3_hold_host.py:709` and `:733` "run once on a
freshly rebooted host with the fragment installed (FREEDOM_TMPFILES_BOOT_PROOF=1)". The `tail`
after the `;` only displayed the retained log; it does not carry the status.

```bash
ssh oracle-test "cd /opt/freedom-blades/platform && sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_RP11_WHEEL=/home/ubuntu/jeepney-0.9.0-py3-none-any.whl /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/systemd_integration > /var/tmp/sysd.log 2>&1; echo SYSD_EXIT=\$? >> /var/tmp/sysd.log"; tail -8 <(ssh oracle-test "tail -8 /var/tmp/sysd.log")
```

**6. Static assets and baseline** — [rerun in this correction], status taken from pytest itself
and returned through SSH. Tree under test: **`STATIC_EXIT=1`, SSH exit 1, 2 failed, 109 passed**,
0 skipped, 3.40 s:

```bash
ssh oracle-test 'cd /opt/freedom-blades/platform && /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/web/test_p3_4_static_assets.py > /var/tmp/static.log 2>&1; rc=$?; tail -4 /var/tmp/static.log; echo STATIC_EXIT=$rc; exit $rc'; echo SSH_EXIT=$?
```

Accepted commit `94fb3e7` in a detached worktree: `WORKTREE_EXIT=0`, **`BASE_STATIC_EXIT=1`,
SSH exit 1, the same 2 failed, 109 passed**, 1.64 s. The two failures in both trees are
`test_the_discovery_enumerates_untracked_files_rather_than_directories` and
`test_every_evidence_harness_source_in_the_tree_is_declared`:

```bash
ssh oracle-test 'git -C /opt/freedom-blades/platform worktree add --detach /var/tmp/base-94fb3e7 94fb3e7 > /var/tmp/wt.log 2>&1; rc=$?; echo WORKTREE_EXIT=$rc; test $rc -eq 0 || exit $rc; cd /var/tmp/base-94fb3e7 && /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/web/test_p3_4_static_assets.py > /var/tmp/static-base.log 2>&1; rc=$?; tail -4 /var/tmp/static-base.log; echo BASE_STATIC_EXIT=$rc; exit $rc'; echo SSH_EXIT=$?
```

(The third-run baseline used the worktree created in that run by
`git -C /opt/freedom-blades/platform worktree add --detach /var/tmp/base-94fb3e7 94fb3e7`; the
same two failures, 109 passed, were observed. The fresh pair above replaces it as the
status-reliable record.)

**7. Bot then web, serially** — [third-run transcript]. Step 1: the SIGHUP/SIGINT/SIGQUIT-reset
wrapper (needed because a backgrounded job inherits ignored SIGINT and breaks the rotate-gate
tests) and cleanup; printed `ok`:

```bash
ssh oracle-test "printf '%s\n' 'import os, signal, sys' 'for s in (signal.SIGHUP, signal.SIGINT, signal.SIGQUIT):' '    signal.signal(s, signal.SIG_DFL)' 'os.execv(\"/bin/bash\", [\"bash\", \"-c\", sys.argv[1]])' > /tmp/run-reset.py && rm -rf /tmp/pytest-of-ubuntu && pgrep -af 'rotate-test-gate|caddy validate' | grep -v pgrep; echo ok"
```

Step 2: the runner script (statuses are written inside it directly after each pytest):

```bash
ssh oracle-test "rm -f /var/tmp/bot.log /var/tmp/web.log; printf '%s\n' 'cd /opt/freedom-blades/platform' \"export PATH='/usr/lib/postgresql/16/bin:/usr/bin:/bin'\" \"export TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'\" '/opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/test_*.py > /var/tmp/bot.log 2>&1; echo BOT_EXIT=\$? >> /var/tmp/bot.log' '/opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/web > /var/tmp/web.log 2>&1; echo WEB_EXIT=\$? >> /var/tmp/web.log' > /tmp/run-suites.sh; cat /tmp/run-suites.sh"
```

Step 3: invocation (bot first, then web, in one process sequence; `ssh_exit=0`):

```bash
ssh oracle-test "python3 /tmp/run-reset.py 'bash /tmp/run-suites.sh'"; echo ssh_exit=$?
```

* Bot: `BOT_EXIT=1`, **6 failed, 6741 passed, 20 skipped, 39 errors** in 1048.67 s. Skips (20):
  16 `RP11_LAUNCH_BUILD_ROOT is not set: no pinned rp11-launch build root is provisioned here`,
  2 `cannot raise RLIMIT_NOFILE above 1048583 (hard 524288 …)`, 2 `This check needs exactly one
  non-owner role holding table grants`. The 45 failing/erroring IDs are in
  `tests/test_r5_runner.py` and `tests/test_sheet_bootstrap_boundary.py`.
* Web: `WEB_EXIT=1`, **2 failed, 2890 passed, 80 skipped**, 1137 warnings, 725.78 s. The skip
  count is the documented 80: 54 `tests/web/test_p3_2_matrix.py:155` and 26
  `tests/web/test_p3_3_matrix.py:198`, both "permitted cells are asserted by the per-route
  success cases". The two failures are item 6's pair. The run was serial and with
  `TEST_DATABASE_URL` exported; no `Out of memory` entry in `dmesg` (count 0).
* Baseline comparison against the `94fb3e7` worktree (`BOT_EXIT` ids vs baseline ids):
  [third-run transcript], printed `6 failed, 39 passed, 39 errors in 9.92s`, 45 lines in each
  ID file, `IDS_IDENTICAL`:

```bash
ssh oracle-test "grep -E '^(FAILED|ERROR)' /var/tmp/bot.log | sed 's/ - .*//' | sort > /var/tmp/final-ids.txt; cd /var/tmp/base-94fb3e7 && PATH='/usr/lib/postgresql/16/bin:/usr/bin:/bin' TEST_DATABASE_URL='postgresql+psycopg:///freedom_test' /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfE tests/test_r5_runner.py tests/test_sheet_bootstrap_boundary.py > /var/tmp/base.log 2>&1; tail -1 /var/tmp/base.log; grep -E '^(FAILED|ERROR)' /var/tmp/base.log | sed 's/ - .*//' | sort > /var/tmp/base-ids.txt; wc -l /var/tmp/final-ids.txt /var/tmp/base-ids.txt; diff /var/tmp/final-ids.txt /var/tmp/base-ids.txt && echo IDS_IDENTICAL; grep '^SKIPPED' /var/tmp/bot.log | sed -E 's/^SKIPPED \[([0-9]+)\] [^:]+:[0-9]+: (.{0,50}).*/\1 \2/'"
```

The tail of that comparison is a `diff … && echo` whose printed `IDS_IDENTICAL` is the result;
the remote shell's final status is that of the skip-summary `sed`, so only the printed lines,
not the SSH status, are cited.

**8. Foundry** — [rerun in this correction], tree synchronized by item 1. The remote program is
single-quoted, so `$?` is expanded by the remote shell; the status is saved in `rc` directly
after `node` (no pipeline), the retained log's summary is printed, the status is printed and
`exit $rc` returns it through SSH. Result: **`NODE_EXIT=0`, SSH exit 0; 171 tests, 171 pass, 0
fail, 0 skipped**:

```bash
ssh oracle-test 'cd /opt/freedom-blades/platform && node --test "foundry-module/tests/"*.test.mjs > /var/tmp/node.log 2>&1; rc=$?; grep -E "^# (tests|pass|fail|skipped)" /var/tmp/node.log; echo NODE_EXIT=$rc; exit $rc'; echo SSH_EXIT=$?
```

Propagation control — [rerun in this correction], the identical wrapper around a Node process
that fails on purpose printed `NODE_EXIT=3` and returned SSH exit 3, so a Node failure cannot be
hidden by the redirection or the `echo`:

```bash
ssh oracle-test 'cd /opt/freedom-blades/platform && node -e "process.exit(3)" > /var/tmp/node-control.log 2>&1; rc=$?; echo NODE_EXIT=$rc; exit $rc'; echo SSH_EXIT=$?
```

**9. Compilation, guards, whitespace** — [rerun in this correction], repository host,
`/opt/freedom-blades/platform`. Compilation, all 15 paths printed `ok`, `COMPILE_EXIT=0`:

```bash
python3 -B -c "
files='''adapters/rp11/stop_post.py application/rp11/cleanup.py application/rp11/journal.py application/rp11/evidence.py infra/rp11-h1/build.py infra/rp11-h1/rp11_h1.py infra/rp11-h1/rp11_roles.py tests/test_rp11_cleanup.py tests/test_rp11_h1_artifact.py tests/web/test_p3_4_static_assets.py adapters/rp11/attest.py application/rp11/attest.py tests/systemd_integration/test_route3_attest_host.py tests/systemd_integration/test_route3_attest_reboot_host.py tests/test_rp11_attest.py'''.split()
for f in files:
    compile(open(f).read(), f, 'exec'); print('ok', f)
"; echo COMPILE_EXIT=$?
```

Guards, `GUARDS_EXIT=0` taken from the script (no pipeline), "40 cases: 26 must be refused, 14
must be allowed; all guard cases passed":

```bash
python3 .claude/hooks/test_guards.py > /tmp/claude-1000/guards.out 2>&1; rc=$?; tail -2 /tmp/claude-1000/guards.out; echo GUARDS_EXIT=$rc
```

No mypy, ruff or other static checker is installed or configured. Whitespace coverage of the
final candidate (tracked changes, and every untracked file including the r4 prompt and this
handback) is recorded in item 11 below.

**10. Host cleanliness** — [rerun in this correction] after the new `oracle-test` work (Foundry,
static assets, baseline worktree). First the scratch removal (`CLEAN_EXIT=0`), then the check:

```bash
ssh oracle-test 'git -C /opt/freedom-blades/platform worktree remove --force /var/tmp/base-94fb3e7; git -C /opt/freedom-blades/platform worktree prune; rm -f /var/tmp/node.log /var/tmp/node-control.log /var/tmp/static.log /var/tmp/static-base.log /var/tmp/wt.log; rm -rf /tmp/pytest-of-ubuntu'; echo CLEAN_EXIT=$?
```

```bash
ssh oracle-test "ls -d /usr/local/libexec/freedom-blades-rp11 /var/lib/freedom-blades-rp11 /run/polkit-1 /var/tmp/rp11-* /run/rp11-* /var/tmp/base-94fb3e7 /tmp/run-reset.py /tmp/run-suites.sh 2>&1; systemctl list-units --all 'rp11*' --no-legend; pgrep -af 'rp11|rotate-test-gate|caddy validate' | grep -v pgrep; systemctl is-active polkit; stat -c '%U:%G %a %n' /var/tmp /usr/local/libexec; ls -d /var/tmp/p5-r5-rp11-h0* | wc -l; git -C /opt/freedom-blades/platform worktree list"
```

Result: every listed path absent, no `rp11*` unit or process, no gate or `caddy` process,
`polkit` active, `/var/tmp` `root:root 1777`, `/usr/local/libexec` `root:root 755`, six
`/var/tmp/p5-r5-rp11-h0*` directories, one worktree (`/opt/freedom-blades/platform`). No new
root or systemd work was done in this correction; the third run's own after-root, after-reboot
and after-suites cleanliness checks (command shapes identical to the one above) reported the
same state.

**11. Whitespace** — [rerun in this correction] after this section was written, repository host,
`/opt/freedom-blades/platform`. Tracked changes: `DIFFCHECK_EXIT=0`, no output. Untracked
files: all eleven (including the r4 prompt and this handback) gave `exit=1` and no output
(`git diff --check --no-index` exits 1 for "files differ" and 3 with printed findings when
trailing whitespace exists, as verified with a control in the first remediation):

```bash
git diff --check; echo DIFFCHECK_EXIT=$?; for f in $(git ls-files --others --exclude-standard); do git diff --check --no-index /dev/null "$f"; echo "exit=$? $f"; done
```

### Unchanged remaining production risks

As before: retained PID/start-time/uid subject risk; the transient inspection-failure
decision; the final independent production security review; `sudo` as the launch preamble
outside the controlled tree; non-atomic sequential PRE reads; no executor yet decides when to
attest; no per-directory `cleared-by-boot` record for an activation-created tree R.

### Recommendation

Accept RT-5 for continued non-production development; no remaining blocker is known. Peter's
acceptance is not recorded here, and the non-root executor and OC-1/OC-2/OC-3 checks are not
assigned.

## Fifth review remediation (2026-10-18)

### Finding and disposition

Finding: `TreeEvidence.is_exactly` compared a lossy projection of tree P — file paths only
(no mode/SHA-256/size), directories through a `rel`-keyed dict (duplicates collapsed) and
undeclared `dir-identity` lines ignored — so five canonical, correctly chained ACT journals
reached `st1-verified` after a boot change. Disposition: fixed; RT-5 changed-boot success now
requires the exact production tree-P history.

### Lossless exact-tree evidence rule

* `TreeEvidence` now keeps the complete ordered `tree-intent.members` (`(rel, kind, mode)`,
  plus `sha256`, `size` for a file) and every `dir-identity` `rel` in journal order
  (`application/rp11/evidence.py`). `declared`/`declared_modes` are unchanged for the other
  triggers.
* `CleanupProcedure._tree_p_recorded` (RT-5 changed-boot only) compares `members` to exactly
  `(".", dir, 0755)` then `("pass-a.json", file, 0644, <A-2 pass_config_sha256>,
  len(pins.pass_bytes))`. Digest and size come from the validated A-2 pins (`pass_bytes`
  hashes to the pin), not from the ACT journal; no pins means not exact. Any duplicate, extra,
  missing, reordered or differing member fails.
* Identity lines must be an in-order subsequence of the declared directories: a missing one is
  still covered only by the accepted durable-prior-removal rule; duplicated, undeclared or
  out-of-order ones fail. Parent/top/temp/tag, one matching `tree-linked`, and ordering rules
  are unchanged. Same-boot RT-5, `stop-post` and `backstop` are untouched.

### Red-before / fixed-after (`tests/test_rp11_attest.py`, 271 tests)

New canonical-journal cases in `test_a_changed_boot_with_an_inexact_tree_p_history_is_a_hard_stop`:
`file-wrong-mode`, `file-wrong-sha256`, `file-wrong-size`, `duplicate-top-member`,
`duplicate-file-member`, `conflicting-duplicate-directory`, `undeclared-identity-before`,
`undeclared-identity-after`, `missing-identity-with-extra`, `reordered-identities`, plus a
parametrized unit test of identity cardinality/order. Each asserts positive PK/2
`not-authorized`, equal baseline, exit 1, `hard-stop`, `st1.verified == false`, no
`st1-verified` claim, failure `st1-not-verified`. Existing controls (omitted intent/link,
wrong parent/top/tag/temp, tree-R, pre-existing rules directory, prior removal, same-boot,
`stop-post`, `backstop`, positive changed-boot success) pass unchanged.

Red-before: the pre-fix candidate source was not retained, so the old comparison was
re-created as a pytest plugin (`is_exactly` over directory dict, file paths and an
identity count, as in the finding) and run against the new tests: **6 failed, 18 passed** —
`file-wrong-mode`, `file-wrong-sha256`, `file-wrong-size`, `undeclared-identity-before`,
`undeclared-identity-after` (the five reproduced cases) and `duplicate-top-member`. Fixed
tree: all pass. The other new cases pass under the old simulation because other checks already
caught them; this is a re-creation, not the original binary.

### Real reboot (new boot id `3000549b-3db0-4d33-87c3-a9e524895fbe`)

Prepare, `sudo systemctl reboot`, readiness, verify, cleanup, exactly as the earlier sections.
Verify: **9 passed, 2 skipped** (other phases). A (valid evidence) `st1-verified` through the
installed `sudo -n` vector; B, C, D, E hard-stop as before; new **F** (pass-a.json digest
changed), **G** (undeclared `dir-identity`) and **H** (duplicate top member) are canonical and
chained yet exit 1, `hard-stop`, `st1-not-verified`, positive PK/2 and equal baseline asserted,
no `st1-verified`. Protected `/var/tmp/p5-r5-rp11-h0*` unchanged (asserted by the fixtures).

### Principal files changed

`application/rp11/evidence.py`, `application/rp11/cleanup.py`, `tests/test_rp11_attest.py`,
`tests/systemd_integration/test_route3_attest_reboot_host.py` (F, G, H; generalized journal
rewriter), this handback, the handover and the active delivery plan (status line only).

### Final-tree commands and results

`oracle-test`, `/opt/freedom-blades/platform`, interpreter
`/opt/freedom-blades/runtime/venv-web/bin/python`; synchronized once after the last code change
(the documented rsync command in the earlier sections, exit 0). Handover/plan one-line edits
and this section came after.

1. Attest module: `... -B -m pytest -q -rfEs tests/test_rp11_attest.py` — exit 0, **271 passed**.
2. Focused set (attest, consume, h1_artifact, hold, cleanup, backstop, records, pk_sn, start,
   stop, systemd_unit_control) — exit 0, **2369 passed, 2 skipped** (`RLIMIT_NOFILE` ×2).
3. Root host module with `sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test
   FREEDOM_RP11_WHEEL=/home/ubuntu/jeepney-0.9.0-py3-none-any.whl` on
   `tests/systemd_integration/test_route3_attest_host.py` — exit 0, **11 passed**.
4. Real reboot phases (`FREEDOM_ATTEST_REBOOT_PHASE=prepare|verify|cleanup`, same env on
   `test_route3_attest_reboot_host.py`): prepare exit 0 (1 passed, 10 skipped), verify exit 0
   (9 passed, 2 skipped), cleanup exit 0 (1 passed, 10 skipped).
5. Complete `tests/systemd_integration` serially, same env, output to a log with the status
   saved: **exit 1, 1 failed, 152 passed, 3 skipped** (842.93 s). Failure:
   `test_route3_consume_host.py::test_sigterm_during_the_authorization_series_fails_the_start_and_is_recoverable`
   (`len(pids) == 1` saw two consume PIDs). Re-run alone: **passed**; the whole consume host
   module re-run: **14 passed**. I treat it as a timing flake in untouched consume code; I did
   not reproduce it on `94fb3e7`, so it is not claimed pre-existing. Skips: the reboot module
   without a phase, and two hold tests needing `FREEDOM_TMPFILES_BOOT_PROOF=1`.
6. `tests/web/test_p3_4_static_assets.py` with `TEST_DATABASE_URL`: **2 failed, 109 passed**
   (`test_the_discovery_enumerates_untracked_files_rather_than_directories`,
   `test_every_evidence_harness_source_in_the_tree_is_declared`); the same file in a fresh
   `94fb3e7` worktree: **the same 2 failed, 109 passed** — baseline.
7. Bot (`tests/test_*.py`) then web (`tests/web`), serial, `PATH` and `TEST_DATABASE_URL`
   exported, statuses written inside the runner: bot `BOT_EXIT=1`, **6 failed, 6759 passed, 20
   skipped, 39 errors** (960 s); the 45 failing/erroring IDs (`tests/test_r5_runner.py`,
   `tests/test_sheet_bootstrap_boundary.py`) are identical to the `94fb3e7` worktree's (45 each,
   `IDS_IDENTICAL`). Skips: 16 `RP11_LAUNCH_BUILD_ROOT is not set`, 2 `RLIMIT_NOFILE`, 2 no
   non-owner role. Web `WEB_EXIT=1`, **2 failed, 2890 passed, 80 skipped** (608 s): the two
   item-6 failures; skip count 80 (54 `test_p3_2_matrix.py:155`, 26 `test_p3_3_matrix.py:198`,
   "permitted cells are asserted by the per-route success cases").
8. Foundry: `node --test "foundry-module/tests/"*.test.mjs` with `rc=$?` saved, printed and
   `exit $rc`: `NODE_EXIT=0`, SSH 0; 171 tests, 171 pass, 0 fail, 0 skipped.
9. Repository host: compile of the 15 touched paths `COMPILE_EXIT=0`; `python3
   .claude/hooks/test_guards.py` `GUARDS_EXIT=0` (26 refused / 14 allowed); `git diff --check`
   exit 0; `git diff --check --no-index /dev/null <file>` for all untracked files gave no
   findings. No mypy/ruff is configured.
10. Host cleanliness, inspected after the root test, after the reboot `cleanup` and after the
    suites and scratch removal: no RP-11 unit, process, Polkit rules directory, artifact,
    store/staging path, attempt evidence, proof-state file or test log; `polkit` active;
    `/var/tmp` `root:root 1777`; six `p5-r5-rp11-h0*` directories; one worktree.

### Unchanged remaining production risks

As before: retained PID/start-time/uid subject risk; the transient inspection-failure
decision; the final independent production security review; `sudo` as the launch preamble
outside the controlled tree; non-atomic sequential PRE reads; no executor yet decides when to
attest; no per-directory `cleared-by-boot` record for an activation-created tree R. One
observed flake (item 5) in the consume SIGTERM host test is outside this change.

### Recommendation

Accept RT-5 for continued non-production development; no remaining blocker is known. Peter's
acceptance is not recorded here, and the non-root executor and OC-1/OC-2/OC-3 checks are not
assigned.
