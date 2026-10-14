# Handback — Route 3 role slice 1: shared cleanup and `deact … stop-post`

Date: 2026-10-13 · Authority: baseline v1.9, active handover, [prompt](route-3-stop-post-role-implementation-claude-prompt.md) · Not committed or pushed.

## Behavior delivered

`/usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py deact <id> <a2> stop-post`
now runs the real cleanup (RT-3). `hold` and `backstop` still refuse with 69. No production
activation; only the controlled artifact imports the new code (asserted by a test).

* **First image (H-FI).** Before any state access the entry point checks fds 0–2 (else 71),
  closes every fd ≥ 3, resets every resettable signal disposition and clears the mask, sets
  `umask 022` and `cwd /`, takes only `INVOCATION_ID` from the initial environment
  (`/proc/self/environ`; duplicate or not 32 lowercase hex ⇒ 64) as diagnostic provenance, then
  empties the environment. Operands are validated by the existing grammar (64 otherwise).
* **CL-G first.** `grant.id` (root `0600`, ≤ 4,096 B, one canonical line, this boot) drives GRR
  on tmpfs before the A-2/H-1 read, the lock, any `ext4` access, any spawn or Polkit call.
* **CL-0 … CL-7, GP-R3, outcome rule** (`application/rp11/cleanup.py`): lock on K to λ
  (`held`/`degraded`/`absent`), `k` = 1 + existing attempt dirs, exclusive attempt dir `0755` and
  journal `0644`, `run-start` + held `cl-g`; ACT/earlier/consume journals parsed and boot-scoped;
  DI-1 capture-unit reads; rule, `pass-a.json`, tree P, tree R, `grant.id`, K removed only when
  A1-intact against a durable identity **and** again on a descriptor immediately before
  `unlinkat`, write-ahead (`remove-intent` → unlink → `removed`); A0/damaged/foreign/nonempty/
  other-boot objects kept and listed in `residual` (metadata and digest only); PK/2
  seek-not-authorized; ST-1 checks including the in-process baseline recomputation (first
  differing key path only); `act` record (if absent, `failed`) and `deact-<k>` record by PF
  (`O_TMPFILE`, durable identity, `linkat` no-replace, `0444`, re-read), `run-end`.
* **GP-R3.** Any journal create/append/flush failure (short write, failed `fsync`, unwritable
  parent, `k` > 99) stops all further evidence, still removes A1-intact objects after descriptor
  re-verification, runs the PK and CL-6 checks, writes no record and prints the GP-7 literal
  `rp11-cl grant-priority <id> rule=… pk=… pass_config=… dirs=…`.
* **DI boundaries.** DI-1 via `SystemdManagerAdapter.read_unit`, DI-5 via
  `PolkitAuthorityAdapter`, DI-6 via `ProcSubjectSource`; deadlines from the H-1 parameters. No
  `systemctl`, `pkcheck`, `sleep`, shell or other executable; a static AST test pins that and the
  single `fork` site.
* **Subject (PC-1, form (F)).** A fork continuing in the image: `setsid`, operator groups/GID/UID
  with real/effective/saved checked, `chdir /`, every fd ≥ 3 closed, `alarm(60)` with default
  `SIGALRM`, then `pause()`. Ready = byte **and** pipe EOF. Settled by SN: S0 grace deadline,
  SN-4 validation (pgid/sid/start ticks), one `SIGKILL` to the group, capped reap loop,
  abandon, `reap-unknown` suppression; never `SIGTERM`, never a retry.
* **Terminals and exits.** `st1-verified` 0, `hard-stop` (with residual) 1, `unit-still-active`
  2, `record-unpublished` 3, `evidence-unwritable` 4, `concurrent-deact` 5, internal error 70
  (fixed line, class name only, no traceback). One bounded diagnostic line, classes only.

**Reversible choices pinned by tests** (documented in the modules): A-2 at
`/var/lib/freedom-blades-rp11/a2/<a2>.json` (`rp11-a2/1`) chaining to the H-1 record
`…/h1/<id>.json` (`rp11-h1-record/1` with `baseline`, `baseline_sha256`, `params`); per-op journal
field lists, `run` names (`<id>`, `<id>-deact-<k>`, `<id>-consume`) and lowercase tree tags;
`"absent"` instead of `null` for `grace_deadline_ms`; a Route 3 baseline profile (`host`,
`operator` from `/etc/passwd`/`/etc/group`, `packages` from the dpkg status file, interpreter,
entry and artifact-tree digests, record-store/artifact directories, `absent`, `po18`, capture-unit
`LoadState`/`TimeoutStartUSec`); PK *not authorized* required for **every** rule class before
`st1-verified` (stricter than the outcome row); a `cl-g` removal classed `removed-earlier`
(H-CL.G.2); `removed-verified` additionally needs an ACT `grant-check` *authorized*.

## Principal files

New: `application/rp11/{__init__,attribution,authority,baseline,canonical,cleanup,evidence,journal,paths,pk,ports,records,sn}.py`,
`adapters/rp11/{__init__,baseline,fsops,process,stop_post}.py`, `tests/test_rp11_cleanup.py`,
`tests/test_rp11_pk_sn.py`, `tests/rp11_fixtures.py`,
`tests/systemd_integration/test_route3_stop_post_host.py`.
Changed: `infra/rp11-h1/rp11_h1.py` (first-image controls, provenance), `infra/rp11-h1/rp11_roles.py`
(stop-post dispatch), `infra/rp11-h1/build.py` (`SOURCES` += the 18 new runtime modules; exact
wheel verification unchanged), `tests/test_rp11_h1_artifact.py`,
`tests/systemd_integration/{test_route3_host.py,rp11_roles_double.py}` (stop-post is no longer
69; attempt evidence cleaned), `tests/web/test_p3_4_static_assets.py` (scope allowlist += the 18
modules). No dependency, migration, configuration or `.env.example` change.

## RT-3 row → evidence

Local tests are in `tests/test_rp11_cleanup.py` (C), `tests/test_rp11_pk_sn.py` (P) and
`tests/test_rp11_h1_artifact.py` (A); host checks in `test_route3_stop_post_host.py` (H).

| Row | Executable evidence |
|---|---|
| RT3.FI.1 | A `test_first_image_controls_run_before_the_role`, `…malformed_invocation_id…`, `…closed_standard_descriptor…`, `…role_vector_is_validated…`, `test_only_one_well_formed_invocation_id…`, `test_entry_rejects_every_other_vector`; H all tests run the exact vector under PID 1 |
| RT3.FI.2 | H `test_an_interrupted_stop_post_is_recovered_by_a_restarted_attempt` (PID 1 kill, no handler, next attempt recovers) |
| RT3.CLG | C `test_the_grant_is_removed_before_any_ext4_read_lock_journal_or_polkit_call`, `…still_removed_when_the_authority_is_invalid`, `…grant_id_naming_another_object…`, `…grant_id_with_the_wrong_mode…`, `test_an_unremovable_rule_is_grant_unremovable`; H `…reaches_st1_verified…` (`first_rung` `cl-g`) |
| RT3.CL0 | C lock held/degraded/absent/wrong-mode tests, `…concurrent_attempt_owning_k…`, `test_attempt_number_exhaustion…`, `test_the_attempt_directory_and_journal_modes`; H `test_concurrent_stop_posts_never_double_act`, `test_attempt_exhaustion_on_the_host…` |
| RT3.CL1 | C journal parse tests (torn, seq, prev, run, op, fields, non-canonical, empty), `test_an_invalid_act_journal_attributes_nothing[*]`, missing/oversized/wrong-mode ACT, `…naming_another_activation_authority…`, other-boot and tmpfs tests, authority chain tests |
| RT3.CL2 | C `test_an_active_capture_unit_is_unit_still_active…[4 states]`, `test_a_failed_unit_read_is_observation_failed…[4 kinds]` |
| RT3.CL3 | C intact/damaged/replaced/symlinked/unremovable rule tests (with and without `grant.id`), `…write_ahead_and_verified`, absent/never-linked tests; H damaged/foreign test |
| RT3.CL4 | P every DI-5 error kind, denial, challenge, persistent authorization, uid mismatch, replaced subject, spawn failure, not-ready subject, schedule; C unconfirmed/authorized series tests; H real series as root (positive control, then *not authorized*), `still-authorized` with a foreign rule |
| RT3.CL5 | C pass-config damaged/replaced/symlinked, absent, removed-earlier |
| RT3.CL5b | C nonempty and replaced tree P, tree R bottom-up, S0 temp name kept, K wrong mode / absent; H tree R (`/run/polkit-1`) removed |
| RT3.CL6 | C baseline difference (key path only), baseline unavailable, unit at end; H real baseline recomputes equal |
| RT3.CL7 | C record collision → `record-unpublished` then recovery, failed record flush, existing `act` record never rewritten, `0444`/schema checks, own-journal prefix digest |
| RT3.CLGP | C E-a (unwritable parent, k exhaustion), E-b/E-c short write and failed `fsync`, no line after a failed append, next attempt's classes |
| RT3.CLOUT | C `test_valid_cleanup_reaches_st1_verified…`, every hard-stop test; H st1-verified and hard-stop via PID 1 |
| RT3.SN.1 | P SN-R rows 1, 2, 4–10, 12 (sent, ESRCH, EPERM, errno, exception, identity mismatch/unverifiable, own group, reap-error, late send, abandon, no re-signal); real subject: own session, only fds 0–2, `cwd /`, `SIGALRM` default, reaped; H subject removed with the cgroup after a PID 1 kill |
| L0 … L9 | C `test_an_interrupted_attempt_is_recovered_by_the_next_one[L0,L1,L2,L3,L5×2,L6×2]`, `…polkit_series_l4…`, `…verification_l7…`, `…after_l9…`; H L4 under PID 1 |

## Commands and results

`oracle-test`, final synced tree, serial, `PATH=/usr/lib/postgresql/16/bin:/usr/bin:/bin`,
`TEST_DATABASE_URL=postgresql+psycopg:///freedom_test`:

* Focused (`…/venv-web/bin/python -m pytest -q -rfEs tests/test_rp11_cleanup.py tests/test_rp11_pk_sn.py tests/test_rp11_h1_artifact.py tests/test_systemd_unit_control.py`):
  **667 passed** (126 + 40 + 84 + 417), also locally. The real-subject test was run 25× on the host
  after the remediation below: 25/25.
* Root (`sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_RP11_WHEEL=/tmp/rp11-wheel/jeepney-0.9.0-py3-none-any.whl …/venv-web/bin/python -m pytest -q -rfEs tests/systemd_integration`):
  **73 passed** (66 existing + 7 new), twice on the final tree (~150 s each).
* Bot `tests/test_*.py` (`-rfEs`): **7 failed, 4846 passed, 18 skipped, 39 errors** (1 h 15 min,
  completed 2026-10-13). The 6 failures and 39 errors are the established baseline set by name
  (`test_r5_runner.py` ×5 F + 39 E, `test_sheet_bootstrap_boundary.py` ×1 F). The seventh,
  `test_snapshot_database.py::test_two_concurrent_applies_of_the_same_key_produce_one_effect`, ran
  while the 2-CPU host was at load ≈ 18; it passed 5/5 in isolation afterwards and touches no
  Route 3 code: a load-sensitive flake, not a regression. Skips are the 18 known toolchain/
  environment skips.
* Web `tests/web`: **1 failed, 2891 passed, 80 skipped** (the known 80; the one failure,
  `test_p3_4_static_assets.py::test_every_evidence_harness_source_in_the_tree_is_declared`, is the
  established baseline failure).
* Foundry `node --test foundry-module/tests/*.test.mjs`: **171 passed, 0 failed**.
* `python3 .claude/hooks/test_guards.py`: 26 refused, 14 allowed, all pass. `git diff --check`: clean;
  new files have no trailing whitespace. `compileall`: clean. **No formatter, linter or type
  checker is configured in the repository**; none was run.

## Exact runtime, real host, interruption, recovery

* Fresh root build from the pinned wheel; every artifact object `root:root`, not group/other
  writable. PID 1 runs the holder (`hold` exits 69) and then the exact `ExecStopPost` vector.
* Happy path through PID 1 with a **live** synthetic grant (positive control: the real fork
  subject with `ubuntu`'s credentials gets *authorized*): exit 0 `st1-verified`, rule, tree P,
  `/run/polkit-1` (tree R), `grant.id`, K gone; records `root:root 0444`; a later real PK check
  is *not authorized*. Also without `grant.id`: `removed-verified`.
* Damaged `pass-a.json`, a foreign-owned file planted in tree P and the rule replaced by another
  inode: all **retained**, exit 1, residual lists each with its class, PK `still-authorized`.
* Interruption: PID 1 kills the stop-post (cgroup `SIGKILL`) inside its Polkit series; attempt 1
  has no `run-end` and no record, the grant is already gone; a restarted holder runs attempt 2 to
  `st1-verified`, its record cites attempt 1's journal. Concurrent direct runs and `k` exhaustion
  also behave as specified.
* **Remediation (one cycle).** (1) Found on the host, intermittent: the subject could still hold
  its readiness-pipe descriptor when the parent read "ready". Ready now requires the byte and
  EOF; 25/25 afterwards. (2) Found in review: GP-R3's diagnostic did not use the accepted GP-7
  literal; fixed and pinned locally and on the host.

**Cleanup** (checked after every root run): no `rp11-*` unit, no `rp11_h1.py` process, nothing
under `/run` named `rp11`, no `/run/polkit-1`, no `/var/tmp/rp11-act-*`, no
`/var/lib/freedom-blades-rp11`, `/usr/local/libexec` empty and `root:root 0755`,
`/etc/polkit-1/rules.d` empty, `polkit.service` active.

## Remaining production risks

1. **polkitd 127 does not load a `/run/polkit-1/rules.d` created after it started** (observed:
   *unconfirmed* until `systemctl restart polkit`; removal in a watched directory is seen in
   ~0.2 s). The host tests restart polkit as harness setup. `hold`'s AV-1 positive control will
   fail on this host unless the directory exists at polkitd start or polkit is reloaded — a
   design decision for Peter before `hold`; cleanup does not depend on it.
2. PID/start-time subject identity is not race-free (A-13.4, retained).
3. No installer writes real A-2/H-1 records yet; their locators, schemas and the Route 3 baseline
   profile are this slice's choices and must be adopted by `hold`/the installer. `launcher`,
   `repository`, `citations`, `manager` and `po17` keys are not recomputed (Q3-9/Q3-11/Q6-2).
4. `/var/tmp` and the ACT directory are writable by `ubuntu`: it can squat attempt names
   (⇒ `concurrent-deact` or GP-R3, no record) or replace the ACT journal (⇒ nothing attributable).
   `grant.id` keeps the grant removal independent of both; the rest is the accepted OH-D-6 limit.
5. An unexpected exception exits 70 without a record; the backstop (next slice) is the rung that
   finishes it.
6. Carried from the adapter: trusted build input, no upgrade path, fixed paths, independent
   security review still required before activation.

## Recommendation

**Proceed to backstop.** RT-3 and every shared operation it uses run against real systemd and
Polkit, fail closed on every malformed, damaged, foreign, concurrent and interrupted case
exercised, and leave the host clean. Risk 1 must be decided before `hold`, not before `backstop`.
