# Handback — Route 3 `consume` role (RT-1)

Date: 2026-10-16 · Implemented by Claude · Status: **accepted by Peter
Duscha on 2026-10-17 for continued non-production development after independent
Codex re-review; uncommitted.** RT-5 `attest`, the non-root executor and
production/staging activation were not part of this slice.

## Delivered behavior

The controlled artifact accepts a sixth fixed vector, with no operand:

```text
/usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py consume
```

`rp11_h1.parse_role_argv` accepts only `["consume"]`; every operand, option,
alias, case/whitespace variant exits 64 before any state operation. The role
reads `INVOCATION_ID` (provenance only; absent ⇒ the literal `absent`, a
duplicate/malformed/oversized value ⇒ 64) and nothing else from the environment.
It installs no signal handler (SG-8); PID 1's `TimeoutStartUSec` is its terminator.

`application/rp11/consume.py::ConsumeProcedure` (ports in the same module,
adapters and composition root in `adapters/rp11/consume.py`) runs, in order:

| Step | Behavior |
|---|---|
| CQ-0 | fixed `pass-a.json` through no-follow descriptors: root `0644` regular one-link ≤ 65,536 B, strict canonical JSON; only `activation_id` is taken. Any failure ⇒ `consume-unidentified`, nothing created |
| CQ-1 | K derived from that id, root `0700` verified, **one** non-blocking `flock`; absent/damaged ⇒ unidentified, held ⇒ `consume-busy`; never waits, scans or signals |
| CQ-2 | `/var/tmp` verified root `1777`; `<id>-consume-evidence` created `0700`, no replace (the same-boot barrier). `EEXIST` ⇒ `consume-repeated`, nothing opened. Journal created `0600`→`0644`, directory `0755`, `run-start {invocation_id, boot_id, claim, act_journal{sha256,length}, lock, helper}`, flushed journal → claim directory → `/var/tmp` |
| CQ-3 | ACT journal + A-2 → H-1 chain (reused `parse_journal`, `act_evidence`, `load_authority`), same boot; the live rule is classified against the ACT identity **and A-2's staged-rule digest**, re-verified through a descriptor by the reused `fs.remove`, `remove-intent` durable → `unlinkat` → directory flush → `removed`. Absent/damaged/foreign/uninspected/unprovable/unremovable is never success |
| CQ-4 | pass-config re-read: same `(dev, ino)`, bytes equal A-2's pin, A1-intact against its ACT identity, names this activation; same boot; `activated` root `0444` `act` record; fresh ACT read with `hold-start` and no `hold-end` (τ₀ from it); no `<id>-deact-*` directory and no deact record; capture root absent; DI-1 holder `active` + journaled invocation id; DI-1 capture `activating` + RT-1's own id + τ₀ |
| CQ-5 | rule name absent; the existing PK/2 series, `seek-not-authorized`, verb `start`, once; `child` lines then `grant-check`; only `not-authorized` continues |
| CQ-6/7 | `consumed {pk_status, inactive_enter_us}` then `run-end {consumed}`, K closed, exit 0 |

**Grant priority.** If the claim could not be made, or any journal create/open/
write/flush fails once it exists (or an unexpected exception occurs), the same
removal runs from the ACT identity and the pinned digest alone, no unwritable
line is attempted, PK/2 runs with its result held in memory, CQ-4 is never
reached, and the attempt fails. K is closed on every return and exception path.

**Exit map** (0 only for complete CQ-7): 21 `consume-unidentified`, 22
`consume-busy`, 23 `consume-repeated`, 24 `consume-claim-failed`, 25
`consume-evidence-unwritable`, 26 `consume-precondition`, 27 `consume-failed
{step,class}`, 70 unexpected exception. Output is one line of closed tokens plus
the validated activation id: `rp11-consume <end> <id|unidentified> step=<CQ-n|none>
class=<token> pk=<outcome|absent>`; exception text, paths, D-Bus detail and file
content are never rendered (unexpected exception: the fixed line
`rp11-consume consume-internal-error`).

## Files

New: `application/rp11/consume.py`, `adapters/rp11/consume.py`,
`tests/test_rp11_consume.py`, `tests/systemd_integration/test_route3_consume_host.py`,
this handback. Changed: `application/rp11/journal.py` (the consume journal
grammar: `run-start` as above, `consumed {pk_status, inactive_enter_us}`,
`run-end` ∈ {`consumed`,`failed`}; the earlier shapes are invalid, no production
journal exists), `application/rp11/paths.py` (`Layout.tree_p`/`pass_config`: the
fixed CQ-0 path before any id is known), `infra/rp11-h1/{rp11_h1.py,rp11_roles.py,
build.py}` (vector, role dispatch, both modules in the exact source manifest and
imported up front), `tests/test_rp11_h1_artifact.py`, `tests/test_rp11_hold.py`
(`World(pass_extra=)`; the HL consume-journal fixture uses the new grammar),
`tests/systemd_integration/test_route3_hold_host.py` (`prepare(service=)` for a
test-only capture-unit body; `activation_id` in the synthetic pass document),
`tests/web/test_p3_4_static_assets.py` (two exact paths added to the enumerated
allowlist; nothing loosened) and the current-state docs (handover, status, active
delivery plan, review README). The manager/Polkit adapter, `unit_control.py` and
all accepted role code are untouched.

## Reversible choices where the old research left the mechanism open

1. **A-2 locator.** RT-1 has no operand, so A-2's digest is read from the ACT
   journal's `run-start` — but trusted only through the root-owned store: A-2 is
   selected by that digest (`0444`, digest-verified), must name this activation
   and pin the same pass-config, staged-rule and boot facts as the journal, H-1
   must chain from it, and the ACT directory must be owned by H-1's operator.
   Editing the journal can therefore only select another valid root-owned A-2 of
   the same activation. The staged-rule digest is A-2's pin, never a journal
   field alone (mutation-checked).
2. **`pass-a.json` carries `activation_id`** (CQ-0); the pinned document must
   name the same activation (CQ-4). A-2's `_pass_document` is unchanged.
3. The ACT journal is first read under 4 MiB (the largest H-1 `journal_max_bytes`,
   needed before H-1 is readable) and then held to H-1's own cap.
4. K is `LocalLock.acquire(0)`: any non-held, non-absent result is `consume-busy`.
5. The PK/2 result of a grant-priority end is shown only as `pk=` in the stderr
   line (it cannot be journaled).
6. `consume-failed` classes: `act-journal`, `invalid-journal`, `invalid-authority`,
   `boot`, `unprovable`, `absent`, `damaged`, `foreign`, `uninspected`,
   `unremovable`, `pass-config`, `act-record`, `hold`,
   `deactivation-evidence`, `capture-root`, `holder`, `capture`,
   `removed-unconfirmed`; claim classes `claim-exists`, `claim-not-made`,
   `claim-evidence`, `run-start`, `consumed`, `run-end`.

## Requirement → test

Local rows: `tests/test_rp11_consume.py` (the real holder runs; `consume` starts
from inside its HL loop, so the ACT journal, `act` record, authority and live rule
are genuine; real descriptor-relative adapters; DI-1 and PK/2 are fakes, plus the
real `PkSeries` over scripted DI-5 answers). Host rows: `test_route3_consume_host.py`.

- **RT1.FI.1/2, H-FI** — exact zero-operand parsing and 16 refused spellings,
  hostile/oversized/duplicate `INVOCATION_ID`, absent accepted, environment emptied,
  start/stop still read none: `tests/test_rp11_h1_artifact.py` (new cases) ;
  no handler/spawn/signal/environment: source test over both modules; host
  `test_an_operand_or_alias_…`, `test_hostile_invocation_ids_…`.
- **CQ-0** — 17 identity failures (missing, symlink, hard link, directory, parent
  symlink, modes, oversize, non-JSON/non-canonical/non-object, missing/bad/typed id,
  path-like id, trailing newline, empty), each creating nothing.
- **CQ-1** — absent/mode/file/symlink K ⇒ unidentified; held K ⇒ busy with a clock
  that fails the test if RT-1 sleeps; host busy test.
- **CQ-2** — barrier: `EEXIST` with an unopenable and a symlinked claim (never
  opened/followed), a later attempt, 8 concurrent full procedures (one consumes),
  8 concurrent claim creations (one wins), `/var/tmp` not `1777`, mkdir error,
  journal-create error, wrong-mode claim, unreadable ACT journal, ACT directory
  not `0700`; every journal **write** failure 1–7 and **flush** failure 1–9
  (the grant is gone and the attempt non-zero at each); flush order
  journal → claim → `/var/tmp`.
- **CQ-3** — torn tail tolerated; corrupt journal; five authority-chain breaks;
  journal forged to a different staged-rule digest; journal that attributes planted
  content to the grant (`unprovable`); other boot; foreign-owner ACT directory;
  absent, damaged, same-bytes-other-inode, symlinked, uninspectable (read fault),
  unremovable and swapped-after-classification rules (nothing unattributed is
  removed); write-ahead ordering spy.
- **Grant priority** — `test_grant_priority_removes_before_…`, the I/O matrix above,
  the claim-failed cases (`pk=not-authorized`, CQ-4 never read), unexpected
  exception before and after the claim.
- **CQ-4** — 16 independent false/unreadable conditions (pass config replaced,
  edited, chmod, removed; boot; `act` record missing/writable/not-activated;
  ACT without `hold-start`, with `hold-end`, unreadable; deact directory, deact
  record, unreadable listing; capture root, dangling symlink) and 13 DI-1 cases
  (both sites: states, other/stale/missing invocation id, τ, read error) plus the
  `absent` provenance; all fail closed after the removal.
- **CQ-5** — rule re-created; authorized / only-errors / interrupted / not-seen /
  still-authorized; the real series: denial, challenge, authorized-then-denied
  decide; persistent authorization, timeout, malformed reply, transport error,
  replaced subject and spawn failure do not; one series run, every subject reaped.
- **CQ-6/7, exit map** — `run-end` failing after `consumed`; `consumed` not written;
  stable exit map; diagnostics regex; no record written, nothing but the rule
  removed.
- **Interruption** — death (`BaseException`) before the claim, during `run-start`,
  between `remove-intent` and `unlinkat`, inside PK/2, after `consumed`: never
  returns, K closed, claim is the barrier, a second attempt is `consume-repeated`,
  the existing stop-post cleanup recovers.
- **Journal grammar, manifest, reuse** — closed field sets; manifest lists both
  modules once; reused primitives named; no second removal path.

Mutation checks (22 single-line mutations of the new modules; all but one caught):
no write-ahead, skip grant-priority removal, absent-is-success, non-decisive PK
passes, K never released, each CQ-4 check removed one at a time, `consumed` before
PK, run-end failure ⇒ success, K wait, `act` record unchecked, barrier replaces,
`/var/tmp` mode unchecked, pass mode unchecked. The one survivor removed a
redundant clause (`observe` identity vs. CQ-0), kept as race protection. A first
survivor — the staged-rule digest taken from the journal rather than A-2 — led to
`test_cq3_a_journal_that_attributes_foreign_content_…`.

Host (`oracle-test`, PID 1 as the real `ExecStartPre=+` of a disposable
fixed-name capture unit, fresh artifact from the pinned wheel):

1. complete lifecycle SA-1 → hold → RT-1 → SA-2 → cleanup: `consumed` + `run-end`
   durable, rule gone, K free, main started with the same `INVOCATION_ID` RT-1
   journaled, τ₀ equals the ACT `hold-start`, `deact-1` `st1-verified` with
   `consume {claimed, consumed}`, Polkit PID unchanged, a later attempt is exit 23
   without touching the claim;
2. failed starts leave `ExecStart=` unexecuted (`Result=exit-code`,
   `ExecMainPID=0`) at CQ-0, CQ-1 (unusable and held K), CQ-2 (`/var/tmp` not
   `1777`, grant still removed, `pk=not-authorized`), CQ-3 (damaged rule kept),
   CQ-4 (deact evidence present, rule removed), CQ-5 (foreign rule keeps
   authorizing ⇒ `removed-unconfirmed`);
3. two concurrent root consumes: one claim, one `removed`; two parallel `systemctl
   start`: one `ExecStartPre`;
4. holder/capture invocation ids and τ₀ compared with the real manager (success)
   and a mismatch (`capture`) when not inside the start job;
5. PK/2 decisive only after Polkit stopped authorizing (real `grant-check`, then
   `FIRST_DECISIVE` not-authorized and the operator's own `start` refused);
6. SIGTERM during CQ-5 (`Result=signal`) and `TimeoutStartSec=3` (`Result=timeout`):
   no `consumed`, no `run-end`, no main process, claim retained, cleanup recovers
   (`consume {claimed, incomplete}`);
7. the lifecycle above;
8. teardown (fixture assertions + separate check below).

## Commands and results (exit statuses, counts, every skip and failure)

Final tree synced with the documented secret-excluding rsync to
`/opt/freedom-blades/platform` on `oracle-test` (the only later change is this
handback's figures).

1. Focused unit/application/artifact/manager set, host:
   `cd /opt/freedom-blades/platform && /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/test_rp11_consume.py tests/test_rp11_h1_artifact.py tests/test_rp11_hold.py tests/test_rp11_cleanup.py tests/test_rp11_backstop.py tests/test_rp11_records.py tests/test_rp11_pk_sn.py tests/test_rp11_start.py tests/test_rp11_stop.py tests/test_systemd_unit_control.py`
   — exit 0, **2042 passed, 2 skipped** (`RLIMIT_NOFILE` above 1048583; hard limit
   524288). The same files plus the static-asset module locally (repo venv):
   2151 passed, 2 skipped, 2 failed (item 4).
2. Root RT-1 module, fresh artifact from the pinned wheel:
   `sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_RP11_WHEEL=/home/ubuntu/jeepney-0.9.0-py3-none-any.whl /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/systemd_integration/test_route3_consume_host.py`
   — exit 0, **14 passed** (140 s). The first real PID-1 run failed because the
   synthetic pass document lacked `activation_id` (fixture fixed); one later
   failure was my own race (IGR removes an untouched rule once the holder ends),
   replaced by assertions on RT-1's own journaled effects.
3. Same command over `tests/systemd_integration` — exit 0, **142 passed, 2
   skipped** (858 s); skips are the two fresh-reboot proofs
   (`FREEDOM_TMPFILES_BOOT_PROOF=1`). Previous 128 + 14 new.
4. `… -m pytest -q -rfEs tests/web/test_p3_4_static_assets.py` — **109 passed, 2
   failed**: `test_the_discovery_enumerates_untracked_files_rather_than_directories`
   and `test_every_evidence_harness_source_in_the_tree_is_declared` (undeclared
   `tools/phase_5_0_evidence/*`). **Freshly reproduced baseline:** a clean
   `git worktree` of `7bdc930` gives the same 2 failures, 109 passed.
5. Bot suite, `PATH='/usr/lib/postgresql/16/bin:/usr/bin:/bin'`
   `TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'`
   `… -m pytest -q -rfEs tests/test_*.py` — exit 1, **6 failed, 6430 passed, 20
   skipped, 39 errors** (1016 s). All 45 are in `tests/test_r5_runner.py` (5 F, 39
   E) and `tests/test_sheet_bootstrap_boundary.py` (1 F), files this work does not
   touch; identical to the baseline recorded in the SA-2 handback for a clean
   tree (not re-run on the baseline in this session). Skips: 2 backup-role, 2
   `RLIMIT_NOFILE`, 16 `RP11_LAUNCH_BUILD_ROOT` not provisioned.
6. Web suite, serially after the bot suite, same environment, `tests/web` — exit
   1, **2 failed, 2890 passed, 80 skipped** (655 s). The skip count is the
   documented 80 (54 + 26 matrix cells), not the database-skipped figure; the 2
   failures are item 4.
7. Foundry: `node --test foundry-module/tests/*.test.mjs` — **171 passed, 0 failed**.
8. `python3 -m py_compile` over every touched Python path — exit 0.
   `git diff --check` — exit 0.

Suites ran with `SigIgn 0x1001000` (default SIGINT/SIGQUIT), bot and web never in parallel.

## Host cleanup (verified separately after the root and full runs)

No `rp11*` unit or process; no `/usr/local/libexec/freedom-blades-rp11`,
`/var/lib/freedom-blades-rp11`, `/run/polkit-1`, `/var/tmp/rp11-*`, test unit
file, foreign rule or consume evidence/log; `polkit.service` active; `/var/tmp`
is `root:root 1777`; the six `/var/tmp/p5-r5-rp11-h0*` directories untouched.

## Effects and risks

No deployment, migration, schema or recovery change; inactive outside
`oracle-test`; the test capture unit is a fixture removed at teardown and no
production capture-unit installer exists. Remaining risks: the retained
PID/start-time/uid subject risk and the transient inspection-failure decision;
the final independent production security review; N1 (`TimeoutStartUSec` > the
PK/2 budget) is a property of the future production unit, which RT-1 does not
install or enforce; the A-2 locator trusts the operator-writable ACT journal only
to *select* a root-owned A-2 (choice 1); a poisoned root-owned `pass-a.json` could
burn another activation's barrier (needs root); RT-1 leaves a live grant in place
on `consume-repeated`/unprovable cases for the holder's IGR and CL, as accepted.

## Recommendation

**Accept for independent Codex review as submitted.** No blocker is known.

## Review remediation — 2026-10-17

At remediation return time this was **not accepted** and remained uncommitted.
The later independent re-review and Peter's acceptance are recorded below.

### Findings and dispositions

1. **Evidence failure bypassed grant priority.** `_failed()` ignored the results of
   its `consume-failed` and `run-end` appends. Now a failed or unflushed
   `consume-failed` returns through `_grant_priority(EVIDENCE_UNWRITABLE, <step>,
   "evidence")` and a failed `run-end` through the same with class `run-end`. The
   selected FAILED/PRECONDITION result stands only while both lines are written
   and flushed. Grant priority is otherwise unchanged: provable removal only,
   nothing written after the journal broke, CQ-4 never reached, always non-zero,
   claim retained, no `consumed`.
2. **Unexpected CQ-5 exception retried PK/2.** New `_State.pk_attempted`, set
   *before* the series is entered in `_run_pk`; grant priority runs the in-memory
   series only when `not pk_attempted` and the rule is absent (replacing the old
   `pk is None` test). An exception, typed error, `unconfirmed`, interruption or
   abandonment therefore never starts a second series, subject or schedule.
   A new `_State.step` records the running stage, so an unexpected exception now
   reports its real `step=` (`class=unexpected`) instead of always `CQ-3`; the
   diagnostic still carries no exception text, path or value.

### Failure-record write/flush matrix (observed; every row: exit 25, no `consumed`, K free, claim retained)

| Case (consume-failed = write *n*) | Fault | Journal after | Rule | PK/2 runs |
|---|---|---|---|---|
| CQ-3 foreign rule (*n*=2) | `consume-failed` write / flush | `run-start` / `+consume-failed` | kept | 0 (`pk=absent`) |
| CQ-3 rule absent (*n*=2) | same | same | gone | 1, in memory |
| CQ-4 capture-root (*n*=4) | same | `run-start remove-intent removed` (`+consume-failed` on flush) | gone | 1, in memory (`not-authorized`); CQ-4 not resumed |
| CQ-5 unconfirmed (*n*=6) | same | `… child grant-check` (`+consume-failed`) | gone | 1 total (already attempted; `pk=unconfirmed`) |
| all four | `run-end` write / flush (class `run-end`) | `+consume-failed` / `+consume-failed run-end` | as above | as above |
| CQ-5, `grant-check` unwritable, `interrupted` | write 5 | `… removed child` | gone | 1 (not retried) |

Also: an exception inside the first real PK/2 series ⇒ exit 70, `step=CQ-5
class=unexpected`, one series, one subject; an exception in CQ-4 before any series
⇒ exit 70, `step=CQ-4`, one in-memory series; `run_consume()` prints exactly
`rp11-consume consume-internal-error <id> step=CQ-5 class=unexpected pk=absent`.
All 19 new regressions failed on the pre-fix code and pass now.

### Principal files

`application/rp11/consume.py` (`_State.pk_attempted/step`, `_failed`, `_run_pk`,
`_grant_priority`, step tracking); `tests/test_rp11_consume.py` (new
"review remediation" section). No adapter, artifact or other role changed.

### Final-tree commands and results

Synced with the documented rsync; `oracle-test`, `cd /opt/freedom-blades/platform`,
interpreter `/opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs`.

1. Focused set (`tests/test_rp11_consume.py test_rp11_h1_artifact.py test_rp11_hold.py
   test_rp11_cleanup.py test_rp11_backstop.py test_rp11_records.py test_rp11_pk_sn.py
   test_rp11_start.py test_rp11_stop.py test_systemd_unit_control.py`) — exit 0,
   **2062 passed, 2 skipped** (`RLIMIT_NOFILE` above 1048583).
2. Root: `sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test
   FREEDOM_RP11_WHEEL=/home/ubuntu/jeepney-0.9.0-py3-none-any.whl … tests/systemd_integration/test_route3_consume_host.py`
   — **14 passed** (162 s), fresh artifact from the pinned wheel.
3. Same env over `tests/systemd_integration`: first run **141 passed, 1 failed, 2
   skipped** (893 s) — `test_route3_stop_host.py::test_a_loaded_failed_capture_unit_is_stopped`
   (`ActiveState` read `active` right after starting an `ExecStart=/usr/bin/false`
   unit: a timing race in a file this work does not touch). That file alone passed
   3/3 (9 tests each). Complete rerun: exit 0, **142 passed, 2 skipped** (806 s);
   skips are the two `FREEDOM_TMPFILES_BOOT_PROOF=1` fresh-reboot proofs.
4. `tests/web/test_p3_4_static_assets.py` — **109 passed, 2 failed**, the same two
   recorded baseline failures (`…untracked_files_rather_than_directories`,
   `…every_evidence_harness_source_in_the_tree_is_declared`), freshly reproduced
   against `7bdc930` in the previous cycle; not repaired.
5. Bot, serial, `PATH='/usr/lib/postgresql/16/bin:/usr/bin:/bin'
   TEST_DATABASE_URL='postgresql+psycopg:///freedom_test' … tests/test_*.py` —
   exit 1, **6 failed, 6450 passed, 20 skipped, 39 errors** (1014 s). The 45 are in
   `tests/test_r5_runner.py` (5 F, 39 E) and `tests/test_sheet_bootstrap_boundary.py`
   (1 F): the same IDs/counts as the recorded baseline, not re-run on the base.
   Skips: 2 backup-role (no non-owner role), 2 `RLIMIT_NOFILE`, 16
   `RP11_LAUNCH_BUILD_ROOT` not provisioned.
6. Web, serially after the bot suite, same env, `tests/web` — exit 1, **2 failed,
   2890 passed, 80 skipped** (693 s): the documented 80 (54 + 26 matrix cells); the
   2 failures are item 4.
7. `node --test foundry-module/tests/*.test.mjs` — **171 passed, 0 failed**.
8. `python3 -m py_compile` over every touched Python path — exit 0; `git diff
   --check` — exit 0.

Suites ran with default signal dispositions (`SigIgn 0x1001000`); bot and web were
never concurrent.

### Host cleanup (checked separately after the root and full runs)

No `rp11*` unit or process, no `/usr/local/libexec/freedom-blades-rp11`,
`/var/lib/freedom-blades-rp11`, `/run/polkit-1`, `/run/rp11-*`, `/var/tmp/rp11-*`
(incl. `rp11-act-*`), test unit file, Polkit rule or consume evidence; test logs
and `/tmp/pytest-of-ubuntu` removed; `polkit.service` active; `/var/tmp` is
`root:root 1777`; the six `/var/tmp/p5-r5-rp11-h0*` directories untouched.

### Remaining risks (unchanged)

Those listed above: the PID/start-time/uid subject and transient-inspection
decisions, the final independent production security review, N1, the A-2 locator
choice, the root-only poisoned `pass-a.json` case, and a live grant intentionally
left on `consume-repeated`/unprovable cases. The host-level lifecycle was not
extended for the two fixes; their evidence is the unit regressions plus the
unchanged root run.

### Recommendation

**Accept RT-1 for continued non-production development**, subject to Codex
re-review. No blocker is known.

## Independent Codex re-review and acceptance — 2026-10-17

Independent Codex re-review found no blocking issue. The failure-record paths
enter grant priority on every tested write/flush failure, and PK/2 is marked
attempted before construction/execution so an exception or non-decisive result
cannot start a second series. The final synchronized tree independently passed
the focused set (**2062 passed, 2 documented `RLIMIT_NOFILE` skips**) and the
fresh controlled-artifact root/systemd consume module (**14 passed**).
`py_compile` and `git diff --check` passed. Separate host inspection found no
new RP-11 unit, process, rule, artifact or consume path; `polkit.service` was
active, `/var/tmp` remained `root:root 1777`, and the six protected pre-existing
directories remained present.

Peter Duscha accepted RT-1 on 2026-10-17 for continued non-production
development. This acceptance itself did not authorize production or staging
activation, RT-5 implementation, the non-root executor, or waive the documented
production security review and remaining risks. Peter separately assigned RT-5
in the active handover after this acceptance.
