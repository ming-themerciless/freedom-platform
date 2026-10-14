# Handback — Route 3 role slice 2: `backstop`

Date: 2026-10-13 · Authority: baseline v1.9, active handover, [prompt](route-3-backstop-role-implementation-claude-prompt.md) · Not committed or pushed.

## Behavior delivered

`/usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py backstop <id> <a2>`
now runs RT-4 over the delivered cleanup engine. `hold` still refuses with 69; `attest`,
`consume`, `start`/`stop`, an installer and production activation are not touched.

* **First image.** Unchanged entry point: the stop-post H-FI controls, operand grammar, artifact
  ownership check and `-I -S` imports apply to `backstop` as they did (the entry now imports
  `adapters.rp11.backstop` up front, so a missing module fails 70 before any role).
* **Authority.** `Params.backstop_max` (B), closed key of the H-1 `params`, range 1 … 99, default
  20. It comes only from the A-2 → H-1 chain (defaults when that chain is invalid, as CL does).
* **BS-1.** One DI-1 read of `<id>.service` `ActiveState`. `activating`/`active`/
  `deactivating`/`reloading` ⇒ exit 0 having touched no file or unit. `inactive`, `failed`, or a
  typed `refused(not-loaded)` continue (on the real manager a never-created holder reads as an
  `inactive` stub). Every error, refusal, unexpected or malformed state ⇒ exit 10, no access.
* **BS-2/BS-3.** New `RecordStore.deact_attempts`: descriptor-relative, no-follow listing of the
  record directory (root-only, ≤ 65,536 entries), exact `<id>.deact-<k>.json`, 1 ≤ k ≤ 99. Only
  the greatest k is read (existing root/`0444`/one-link/1 MiB read), parsed canonically,
  `validate_record`-ed and matched on kind, activation and attempt. `st1-verified` ⇒ BS-2;
  `hard-stop` that `hard_stop_permits_disarm` ⇒ BS-3; anything else (including any bad latest
  record) ⇒ BS-4, never an older record. BS-3 predicate (pure, table-tested): rule class known and
  not `removed-unconfirmed`/`grant-unremovable`; pass-config and `grant.id` classes known; no
  directory, pass-config, `grant.id` or residual class in {`unremovable`, `grant-unremovable`,
  `present-nonempty-unremoved`} (the A1-intact-but-kept classes). Damaged, foreign and S0
  leftovers do not block; an unstated class blocks.
* **DI-4.** At most one call per firing, always `disarm_backstop(<id>)` (the derived timer, mode
  `fail`). At BS-2/BS-3 only `ok` or `refused(not-loaded)` exit 0; any other result exits 11 with
  no retry, no CL and no record, and the line names `unconfirmed`/`error`/`refused`, never
  `stopped`.
* **BS-4.** Under a per-activation backstop lock, `k` = 1 + the `<id>-deact-` names (CL-0's own
  rule) and the backstop attempts are counted among the exact attempt names. `k` > 99 ⇒
  `attempt-limit`; ≥ B backstop attempts ⇒ `backstop-max`: one DI-4, one terminal line, exit 12
  (13 if the line is not durable). Otherwise the shared `CleanupProcedure` runs once with trigger
  `backstop` and `k` **pinned**: CL-0 owns exactly that `k` or none (`concurrent-deact`). After a
  lost attempt or publication race the firing re-observes BS-2/BS-3 once and takes only a branch
  that validation admits; otherwise CL's own exit (0 … 5).
* **Trigger.** `Trigger.BACKSTOP`; `run-start` and the records carry `trigger`/`helper.role`
  `backstop` and the BS-1 holder state; a firing's `INVOCATION_ID` is provenance only and is not
  recorded as the holder's (`holder.invocation_id` `absent`).
* **Output.** One `rp11-bs <class> <id> …` line per firing (tokens only), plus CL's own line
  when CL ran; an unexpected exception is `rp11-bs internal-error <id> <Class>`, exit 70.

**Reversible choices (pinned by tests, recorded in `application/rp11/backstop.py`):**
lock and terminal journal `/var/lib/freedom-blades-rp11/backstop/<id>.journal` (dir root `0755`,
file root `0644`, one link, `O_APPEND|O_NOFOLLOW`, `flock` non-blocking, ≤ 64 KiB); line
`{"activation_id","disarm","op":"backstop-terminal","reason","schema":"rp11-backstop-terminal/1"}`;
a held lock ⇒ 14 without CL; an unopenable lock ⇒ continue unlocked on the pinned `k`
(mirrors K's degraded mode), and the terminal path then exits 13; an attempt counts against B
unless its journal's first line is a well-formed `run-start` of that attempt with a non-backstop
trigger; unlistable attempts ⇒ 15, no CL and no disarm; Q6-7 default — a terminal DI-4 error is
recorded as `unconfirmed`/`error`, not retried, never a stopped claim. Exit codes 10–15 are new.

## Principal files

New: `application/rp11/backstop.py`, `adapters/rp11/backstop.py`, `tests/test_rp11_backstop.py`,
`tests/systemd_integration/test_route3_backstop_host.py`, this handback.
Changed: `application/rp11/{authority,cleanup,ports}.py` (`backstop_max`, `load_authority`,
`Trigger.BACKSTOP`, `Invocation.holder_state`, pinned `attempt`, `deact_attempts`/`BackstopGuard`
ports), `adapters/rp11/{fsops,stop_post}.py` (`deact_attempts`, `LocalBackstopGuard`;
`build_procedure` takes trigger/attempt/holder state), `infra/rp11-h1/{rp11_roles,rp11_h1,build}.py`,
`tests/test_rp11_h1_artifact.py`, `tests/systemd_integration/{test_route3_host,
test_route3_backstop_host,test_route3_stop_post_host}.py` (backstop is no longer 69; repeat-run
Polkit fixture setup resets only the disposable service's start-limit counter),
`tests/web/test_p3_4_static_assets.py` (scope allowlist += the two modules),
`docs/review/route-3-stop-post-role-implementation-handback.md` (suite placeholders completed).
No dependency, migration, configuration or `.env.example` change.

## RT-4 row → evidence

B = `tests/test_rp11_backstop.py`; A = `tests/test_rp11_h1_artifact.py`; C =
`tests/test_rp11_cleanup.py`; H = `tests/systemd_integration/test_route3_backstop_host.py`;
R = `tests/systemd_integration/test_route3_host.py`.

| Row | Executable evidence |
|---|---|
| RT4.FI.1 | A `test_entry_accepts_exactly_the_three_role_vectors`, `…rejects_every_other_vector`, first-image tests, `test_backstop_runs_its_composition_root_with_the_provenance`, `test_the_entry_imports_the_backstop_root_up_front`, `test_hold_still_refuses_rather_than_pretend`; R `test_exact_role_vector_runs_isolated…[backstop]`, `test_pid1_executes_the_exact_backstop_vector`; every H test runs the vector under PID 1 |
| RT4.FI.2 | H `test_a_hung_firing_is_ended_by_runtime_max_sec` (production firing, SIGTERM at S_b), `test_a_firing_that_ignores_sigterm_is_killed_after_timeout_stop_sec` (SIGKILL at S_b + S) |
| RT4.BS1.1 | B four owning states (no access: exploding ports), 14 error/refusal/state cases, inactive/failed/not-loaded continue, real adapter over a scripted bus (6 cases); H `test_bs1_an_active_holder_owns_the_activation`, `…never_existed_continues_to_cleanup` |
| RT4.BS2.1 | B no record, valid latest, 13 bad-latest cases with an older success present, greatest-attempt rule, 8 irrelevant names, bounded and unlistable/symlinked directory |
| RT4.BS2.2 | B 11 DI-4 results at BS-2 (one call, no CL/record), real adapter 9 bus outcomes; H `test_bs2_disarms_only_its_own_timer…` (another activation's timer stays active) |
| RT4.BS3.1 | B predicate tables (11 rule classes, 3 × 4 A1-intact placements, 5 non-blocking, 6 unstated/malformed), 11 DI-4 results at BS-3; H `test_bs3_disarms_after_a_hard_stop…` |
| RT4.BS4.1 | B `test_b_minus_1…_and_b_then_stops`, `test_successive_firings_terminate_at_b` (B = 4: exits 1,1,1,1,12,12,12), stop-post attempts not counted, 6 unknown-attempt cases, k = 99 enters, squatted names, unlistable attempts; H real timer to B = 2 |
| RT4.BS4.2 | B 11 terminal DI-4 results (one call, one line, exit 12, nothing entered CL), k = 100 `attempt-limit`, short write, failed `fsync`, size cap, 5 untrustworthy-journal cases, modes; H `test_the_real_timer_fires_until_backstop_max…`, `test_the_attempt_limit_is_terminal_on_the_host` |
| RT4.BS.1 | B `test_bs_never_names_the_holder_or_capture_unit_in_a_mutation`, unit-name sets in every concurrency case; H holder left active, other timer untouched |
| RT4.SN.1 | C/P stop-post SN evidence (shared); H subject gone after SIGTERM/SIGKILL and cgroup kill; C static AST test now covers the two new modules |
| RT4.CLG … CL7, CLOUT | B `test_backstop_cl_reaches_st1_verified_with_its_own_trigger`, hard-stop, record trigger/holder fields; C full stop-post engine suite (unchanged engine); H st1-verified via PID 1 |
| RT4.CLGP | B `test_backstop_cl_hard_stop_and_grant_priority` (GP-7 literal, exit 4, no record) |
| IM-B / recovery | B interruption at CL-G, CL-1, CL-5, CL-5b then next-firing recovery and BS-2; H `test_an_interrupted_firing_is_recovered_by_the_next`, manager re-exec/reload and polkit restart between and during firings |
| Concurrency | B lock held ⇒ 14, lost attempt race ⇒ re-observe (disarm / exit 5), publication collision, 6 simultaneous firings (exactly the B-th enters, other activation untouched), two-process `flock`; H three simultaneous exact vectors ⇒ one CL |

## Commands and results

`oracle-test`, final tree (code byte-identical to this workspace, checked by digest), serial,
`PATH=/usr/lib/postgresql/16/bin:/usr/bin:/bin`, `TEST_DATABASE_URL=postgresql+psycopg:///freedom_test`:

* Focused (`…/venv-web/bin/python -m pytest -q -rfEs tests/test_rp11_backstop.py tests/test_rp11_cleanup.py tests/test_rp11_pk_sn.py tests/test_rp11_h1_artifact.py tests/test_systemd_unit_control.py`):
  **868 passed** on the final reviewed tree (the two added cases prove unknown residual/directory
  classes cannot authorize BS-3); the pre-review implementation tree had 866 passed.
  The sandbox-local attempt was not a valid suite lane: its filesystem refuses the production
  `O_TMPFILE` publication link through `/proc/self/fd`, yielding 142 failed, 691 passed, 1 skipped
  and 32 dependent errors at record publication; the documented `oracle-test` lane above passes.
* Root (`sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_RP11_WHEEL=/tmp/rp11-wheel/jeepney-0.9.0-py3-none-any.whl …/venv-web/bin/python -m pytest -q -rfEs tests/systemd_integration`):
  **85 passed** on the final reviewed tree (2 min 50 s). An immediately preceding repeat run
  exposed only Polkit's fixture start-rate limit (83 passed, 2 failed, 2 teardown errors); the
  fixture now resets that disposable service's failed counter before its intentional restart.
* Bot `tests/test_*.py`: **6 failed, 5050 passed, 18 skipped, 39 errors** (15 min 50 s). Failures and
  errors are exactly the established set by name (`test_r5_runner.py` 5 F + 39 E,
  `test_sheet_bootstrap_boundary.py` 1 F). The two passes above Claude's 5048-pass backstop run are
  the added predicate regressions; no new failure. Skips: the 18 known.
* Web `tests/web`: **1 failed, 2891 passed, 80 skipped** — the same baseline failure
  (`test_every_evidence_harness_source_in_the_tree_is_declared`, the same five undeclared
  `tools/phase_5_0_evidence` files) and the known 80 skips. Unchanged from stop-post.
* Foundry `node --test foundry-module/tests/*.test.mjs`: **171 passed, 0 failed**.
* `python3 .claude/hooks/test_guards.py`: 26 refused, 14 allowed, all pass. `git diff --check`
  clean; new and changed files have no trailing whitespace; `compileall` clean. **No formatter,
  linter or type checker is configured**; none was run.
* The stop-post handback's three suite placeholders are completed with that run's exact results.

**Independent Codex review remediation.** Review found that `validate_record()` does not itself
constrain a residual entry's class, while `hard_stop_permits_disarm()` admitted an unknown string.
That contradicted the stated fail-closed predicate and could let BS-3 disarm without proof. The
predicate now admits only known rule/pass/directory/`s0` classes and regression tests cover unknown
residual and directory classes. The final focused, real BS-3, full system-integration, bot, web and
Foundry results above are from the remediated tree. The only other change was the disposable-host
fixture repeatability correction described above; no role restarts Polkit.

## Exact runtime, PID 1, Polkit, interruption, concurrency, recovery

* Fresh root build from the pinned wheel per module; every artifact object `root:root`, not
  group/other writable. Every firing is `<id>-backstop.service` created with its timer by DI-3 and
  run by PID 1 with the exact vector (interpreter `/usr/bin/python3.14 -I -S`, jeepney 0.9.0 from
  `lib/`); R also runs the vector directly with an empty environment.
* **BS-1:** a running `<id>.service` ⇒ exit 0, rule, store and timer untouched and the holder
  left running; a never-created holder (manager stub, `inactive`) ⇒ CL with `holder_state
  inactive`; a failed holder (production `hold` 69 → stop-post) ⇒ BS-2.
* **BS-2 / BS-3:** after a real stop-post `st1-verified` the firing disarms its own timer (another
  activation's timer stays `active`; no new attempt or record). After a real hard-stop that left
  only a foreign replacement of the rule in a pre-existing `rules.d`, BS-3 disarms and the
  foreign rule is kept.
* **Bound by the real timer:** `OnActiveSec`/`OnUnitActiveSec` = 3 s, B = 2, every CL hard-stops:
  two `cleanup` firings (records 1 and 2, trigger `backstop`), then one `bound-reached
  reason=backstop-max disarm=stopped`; the timer stops itself; exactly one terminal line. 99
  squatted attempt names ⇒ `attempt-limit`, no CL, the rule untouched.
* **Interruption:** PID 1 SIGKILLs a firing inside its Polkit series (a foreign grant in
  `/etc/polkit-1/rules.d` keeps it running): attempt 1 has no `run-end` and no record, the grant is
  already gone (CL-G); the subject went with the cgroup. The next firing reaches `st1-verified` as
  attempt 2 citing attempt 1's journal; the one after disarms at BS-2.
* **Hung firings (BS-RM):** the production firing stuck in the Polkit series ends `Result=timeout`
  at `RuntimeMaxSec=3` (PID 1's span < 8 s, no record, no process left). A role double that ignores
  SIGTERM is SIGKILLed at `RuntimeMaxSec + TimeoutStopSec` (status 9, span 13–16 s).
* **Restarts:** `daemon-reexec` keeps the transient timer armed; after it and a polkit restart the
  firing reaches `st1-verified`; after `daemon-reload` and another polkit restart the next firing
  disarms. A polkit restart *during* the series yields `st1-verified` only with a real *not
  authorized*, otherwise `hard-stop`; the timer is disarmed within two further firings.
* **Concurrency:** three simultaneous exact vectors as root ⇒ exactly one `rp11-bs cleanup … k=1`,
  one attempt directory, the others 14 (lock held) or 0 (record found, timer not loaded); every
  line names only this activation.
* **Remediation (one cycle).** Product: a lost-race firing resolved by re-observation did not
  print CL's line; fixed and pinned. Harness (host only): a firing that disarms its own timer is
  collected by PID 1 at once, so firings are read from the journal by unit and cursor; BS-3's host
  case needs a pre-existing `rules.d` (an ACT-created one holding a foreign rule is correctly
  A1-intact and non-empty, so BS-4 retries); RuntimeMaxSec checks use PID 1's own journal
  timestamps with headroom for a loaded 2-CPU host. No other defect was found.

## Cleanup

After each root run (two final runs, plus the earlier development runs): no `rp11-*` unit, no
`rp11_h1.py` process, nothing under `/run` named `rp11`, no `/run/polkit-1`, no
`/var/tmp/rp11-act-*`, no `/var/lib/freedom-blades-rp11` (so no backstop journal), `/usr/local/libexec`
empty and `root:root 0755`, `/etc/polkit-1/rules.d` empty, `polkit.service` active. The module
fixtures assert this and it was re-checked by hand. The separate development copy
`/opt/freedom-blades/platform-bs` on the disposable host (used so the stop-post baseline run was not
disturbed) is removed after the final run. No real secret or player data was used.

## Remaining production risks

1. **Retry semantics of BS-3 are literal.** A hard-stop whose only leftovers are an A1-intact but
   nonempty directory (e.g. ACT's `rules.d` holding a foreign rule) is retried by BS-4 until B,
   then terminal — bounded, but noisy. On this host `/run/polkit-1` does not pre-exist, so that is
   the normal shape of a foreign-rule hard stop.
2. **A firing that loses an attempt race has already run CL-G** (grant removal) before CL-0 says
   `concurrent-deact`; it creates no attempt and is not counted against B. That is the accepted
   CL-G-first order, not an extra attempt.
3. **The lock lives on ext4 under the record store.** If the store is unusable the firing runs
   unlocked on the pinned `k`; concurrent firings are then ordered only by CL-0's exclusive
   attempt directory, and an `ubuntu` name-squatter (OH-D-6) could in principle make one extra
   attempt. A missing store also means no record and no terminal line.
4. **Q6-7 accepted by Peter:** an unconfirmed terminal disarm is reported and left; the timer may
   fire again and each later firing is terminal again (one more DI-4, one more line, until the
   64 KiB cap, then exit 13 without a line).
5. Carried: polkitd 127 ignores a `rules.d` created after it started. A `tmpfiles.d` entry is the
   accepted preferred installer/activation design, but it is not yet installed or proved across a
   real reboot. PID/start-time subject identity is racy (A-13.4); no installer writes real A-2/H-1
   records; `/var/tmp` squatting (OH-D-6); independent security review before activation.

## Recommendation

**Proceed to hold.** Every RT-4 row has a named executable test or real-host check; all three
DI-4 sites fail closed and never retry or claim a stop; no malformed, replaced or older record
authorizes a disarm; no foreign object is removed and no other activation's unit is touched; the
bound terminates at B and at k = 100; PID 1's `RuntimeMaxSec`/`TimeoutStopSec` end hung firings;
`hold` still refuses 69; no suite regression. Baseline v1.9 makes the Q6-7 fail-closed default a
reversible tested detail, not a new decision gate. For the observed polkitd-127 behavior, successful
disposable-host hold flows must start Polkit with `/run/polkit-1/rules.d` already present; a directory
created after Polkit starts must be tested as a fail-closed AV-1 path. The role must never restart
Polkit. Production boot/install ordering remains a later activation review concern.

## Maintainer decisions (2026-10-13, Peter Duscha; clarified after review)

Both approved as recommended:

1. **polkitd rules.d at start (stop-post risk 1, carried risk 5):** a `tmpfiles.d` entry,
   `d /run/polkit-1/rules.d 0755 root root -`, is the preferred future installer/activation
   design. Installing it and proving it across a real reboot are deferred to that later slice and
   remain required before production activation. The current disposable-host `hold` harness
   creates the directory and restarts Polkit once as setup, and tests the late-directory case as a
   fail-closed path. `hold` itself never restarts or reloads Polkit; an AV-1 grant that is not
   confirmed fails closed and rolls back. With the directory pre-existing, ACT no longer creates
   it, so risk 1 above does not arise in that successful-flow shape.
2. **Q6-7:** the implemented default is accepted: an unconfirmed terminal DI-4 is reported and
   left, never retried within the firing and never claimed as stopped; later firings are terminal
   again until the 64 KiB cap.

## For Codex review

* **State.** Slice complete; no further Claude work is pending. Tree uncommitted and unpushed on
  `docs/platform-plan`, alongside the maintainer's unrelated working-tree changes.
* **Re-checked locally on the remediated tree (2026-10-13):** focused suites **868 passed**;
  `git diff --check` clean; guard tests 26 refused / 14 allowed, all pass.
* **Review scope:** the files under *Principal files*, the RT-4 evidence table, and the
  remediated `hard_stop_permits_disarm` (`application/rp11/backstop.py`) with its
  unknown-class regressions.
* **Review disposition:** Codex independently accepted the remediated slice. Peter accepted Q6-7
  and clarified the Polkit directory choice as a preferred future installer/activation design,
  not a current hold-slice reboot requirement. The decision register and active hold prompt now
  carry that boundary.
* **Host note.** `oracle-test` has no RP-11 residue and `polkit.service` is active. Eight orphaned
  `/bin/sh …/bin/caddy validate` stub processes left by the web suite's interruption tests (from
  both the stop-post baseline run and this slice's run; their temp files were already gone) were
  killed. That is a web-suite hygiene defect unrelated to Route 3, worth a separate fix.
