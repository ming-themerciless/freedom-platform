# Handback — Route 3 production-readiness and security-gate preparation

Date: 2026-10-22 · Implementer: Claude · Reviewer after handback: Codex · Authority: Peter Duscha

Assignment: [`route-3-production-readiness-claude-prompt.md`](route-3-production-readiness-claude-prompt.md).
Review remediation: [`route-3-production-readiness-review-remediation-claude-prompt.md`](route-3-production-readiness-review-remediation-claude-prompt.md).
Second review remediation: [`route-3-production-readiness-review-remediation-r2-claude-prompt.md`](route-3-production-readiness-review-remediation-r2-claude-prompt.md).
Third review remediation: [`route-3-production-readiness-review-remediation-r3-claude-prompt.md`](route-3-production-readiness-review-remediation-r3-claude-prompt.md).
Fourth review remediation: [`route-3-production-readiness-review-remediation-r4-claude-prompt.md`](route-3-production-readiness-review-remediation-r4-claude-prompt.md).
Fifth review remediation: [`route-3-production-readiness-review-remediation-r5-claude-prompt.md`](route-3-production-readiness-review-remediation-r5-claude-prompt.md)
(this document was updated in place; the **Fifth review remediation return** below is the latest, then the Fourth, the Third and the Second, §0 is the
first remediation return, and §§1–10 were corrected so they do not contradict any; where §8 or §10 or an earlier return states a host or test result, the Fifth return supersedes it).

The implementation and review work recorded before §6.1 did not touch
production or staging, use a real secret or player data, commit or push.
**Peter accepted the cumulative candidate on 2026-10-24
for continued non-production development after the clean final focused
review.** That acceptance is not a transient inspection-failure decision and
does not authorize production/staging access, inspection, installation or
activation. **Subsequent decision, 2026-10-25:** Peter selected the bounded
production direction and accepted the residual only for explicitly authorized,
attended migration/cutover evidence activations under §5.2. That decision still
does not authorize production/staging access, inspection, installation or
activation.

**Later authorization and result, 2026-10-25:** Peter explicitly authorized
the read-only production inspection in §6. Its secret-safe, unprivileged
portion was executed without changing state and returned the no-go recorded in
§6.1. Root-only sudoers/private-Polkit checks remain incomplete; remediation,
installation and activation are not authorized.

## Direct completion correction after the fifth review (2026-10-24)

**Independent Codex final focused re-review and disposition.** No remaining
implementation defect was found, and Peter accepted the cumulative candidate
for continued non-production development on 2026-10-24. Codex independently
confirmed that the extracted checklist hash
matches between the workspace and `oracle-test`, then reproduced **53 passed**
for the complete checklist module, a clean `bash -n`, and clean
`git diff --check`. The directly affected structural run reproduced **127
passed, 1 failed**, the same disclosed baseline evidence-harness allowlist
failure. The acceptance makes no transient-risk decision and authorizes no
production/staging activity.

Codex found that item 5b could print `[item 5b COMPLETE]` after a directory search or a unit query failed. Corrected under the round-five direct-completion
prompt section; product and installer code are unchanged. Item 5b's `search_user_dirs` no longer counts every non-zero `find` as an absent path: after a
failed `find` it runs `LC_ALL=C stat` on the directory, and only a stat "No such file or directory" is reported `[absent]`; any other failure (I/O,
permission) is a `[FINDING]`, counted in `SEARCH_FAILED`, and makes the search return failure so the closing line is `[item 5b INCOMPLETE]` and no unit query
runs. A non-zero `list-unit-files` or either allowlisted `show` now also yields `[item 5b INCOMPLETE]`; `COMPLETE` prints only when the path set was formed,
every existing directory was searched with status 0, and all three queries succeeded. Account, allowlist and prohibitions are untouched.

**Portability follow-up (2026-10-24, same task).** Codex reproduced 6 failed / 45 passed on `oracle-test`: the first correction compared the complete `stat`
diagnostic, which differs between GNU coreutils (`cannot statx '<path>'`) and the host's uutils (`cannot stat '<path>': ... (os error 2)`). Absence is now decided
by errno: after a failed `find`, `"$PROBE_PY" -I -S -c` (`PROBE_PY=/usr/bin/python3.14`, a literal line like `RUN_USER_DIR`, substituted only in a test copy) runs
`os.lstat` on one path argument and exits 10 for `FileNotFoundError` (the only accepted absence), 11 for any other `OSError`, 0 if the path exists; the shell prints
only its fixed `[absent]` / `[FINDING] ... (probe status N)` line, never the exception or pathname from Python. Regressions now prove all three outcomes (missing
path accepted and `COMPLETE`; existing path after failed `find`: finding, `INCOMPLETE`, no unit query; ENOTDIR observation failure, status 11: finding, `INCOMPLETE`,
no unit query) plus a uutils-style `stat` diagnostic that must not matter. Module now 53 cases.
Verification on `oracle-test` after the canonical secret-excluding `rsync` (exit 0; one earlier piped rsync was refused by the secrets guard and rerun bare): the two
focused files match the workspace by sha256 (`tests/test_production_checklist_item_5b.py` 03d350d1…07333, this handback 6cef35aa…3df2694, taken before this note was added; only prose was edited afterward); checklist module
**53 passed**, rc 0; `bash -n` over the extracted checklist rc 0; `test_p3_4_static_assets.py` + `test_deployment_artifacts.py` **127 passed, 1 failed** (the same accepted
baseline allowlist failure `test_every_evidence_harness_source_in_the_tree_is_declared`); `git diff --check` clean. No retries; no full suites run. Nothing accepted, committed or pushed.

Regressions added to `tests/test_production_checklist_item_5b.py` (53 cases after the portability follow-up; 47 before this correction): an injected directory-search failure
on an existing directory, and a unit-query failure (parametrized over `list-unit-files` and `show`); each asserts `INCOMPLETE`, no `COMPLETE`, printed
statuses, and the existing harness asserts empty scratch. With the two new conditions removed, those three cases fail; with the correction all pass.

Run (repository host, `venv-web`, checklist module only, as the prompt limits): checklist module **51 passed** (superseded by the portability follow-up above); `bash -n` over the extracted script ok;
`git diff --check` clean; tree-scanning structural run (`test_p3_4_static_assets.py`, `test_deployment_artifacts.py`) **127 passed, 1 failed**, the same
accepted baseline allowlist failure (`test_every_evidence_harness_source_in_the_tree_is_declared`). No full product, database, Node or root/systemd rerun
(not warranted by this read-only checklist change); earlier figures in this document are unchanged by it. Nothing is accepted, committed or pushed; no
production or staging access. Recommendation: Codex re-review of the §6 item 5b text and its test.

## Fifth review remediation return

Date: 2026-10-23. Codex's review of the fourth remediation reported three findings. All are addressed in place; the accepted topology, SA-2 vector, role
semantics, BS-3, strict `ActiveState`, strict enablement observation, authorization policy and residual-risk options are unchanged, and **no installer or
product code changed in this round** (only checklist item 5b/5/11 text and its test). Nothing is accepted, committed or pushed; no production or staging access occurred.

**Finding 3 — the fourth-return section (stated first because it limits what can be cited).** Codex reported that this document began with the Third return and
that no fourth-round evidence existed. The tree I received at the start of round 5 **does** contain a `## Fourth review remediation return` section at the top
(with its table, the 254-case installer figure, 3243 focused, 199/6 root, 6F/7433/20s/39E bot, 1F/2891/80s web, 171 Node). I cannot establish whether it was
added after Codex's snapshot or was missed; I did not retain the fourth-round command output, so **I do not rely on any fourth-round suite figure**. The
implementation it describes is present in the tree and unchanged by me (`Installer._observed_enabled()` and `_observed_state()` in
`tools/executor_supervisor_install.py`, the 21 added installer cases, runbook §8b step 2, `tests/test_production_checklist_item_5b.py`). Every result cited below
is a new run on the final tree. (The new totals exceed the fourth section's by exactly the 29 cases added this round, which is consistent with, but does not
prove, those earlier runs.)

**Finding 1 — the host state.** Codex observed `/opt/freedom-blades/platform` and `runtime/venv-web` as `root:root 0755`, `venv-web/bin/python` resolving to
`/usr/bin/python3.14`, and no pytest. **I could not reproduce it.** When I first looked (2026-10-23 ~13:03 UTC, before changing anything) `oracle-test` was already
in the documented state: `/opt/freedom-blades` `ubuntu:ubuntu 0755`, `platform` `ubuntu:ubuntu 2775` (setgid), `runtime` and `venv-web` `ubuntu:ubuntu 0775`,
`venv-web/bin/python` → uv CPython 3.12.14, pytest 8.4.2 importable, no entry under `platform` or `runtime` owned by anyone but `ubuntu`, and no executor
account, group, home, linger entry, unit, state/run directory, artifact or decoy. The sudo journal of this boot (since 2026-10-22 00:49) contains no `chown`,
`chmod`, `venv` or move of `platform`/`runtime` except the round-2 rehearsal's `chmod`/`chown` of one file under `venv-web/lib/python3.14/site-packages/jeepney`
at 2026-10-22 00:52 (so `venv-web` was then a production-shaped Python 3.14 tree; `runtime` was last modified 2026-10-22 02:33, when it was restored), no
privileged command at all between 12:12 and 13:03 on 2026-10-23, and every one of the boot's 1744 SSH logins came from a single address. **The cause is not
established.** My earlier §8 claim ("back to `ubuntu:ubuntu`…") was true of the state I last saw but was not backed by a comparison Codex could repeat; treat it
and the "final host comparison" lines of the earlier returns as superseded. Because the state was already canonical I made **no ownership or interpreter change**;
I restored nothing, I verified: the canonical secret-excluding `rsync` ran with no error and the checkout accepted it; the host-side `venv-web` ran the installer
module and the suites below. I did remove scratch the earlier rounds left behind, after recording it: three root-owned `/tmp/tmp.*` directories from earlier item 5b/checklist
probes (20:05–22:15 on 2026-10-22: `last.out`/`last.err`, path lists, `block2`, `login.defs`, `pids`, `proc*.out`), five ubuntu-owned `/tmp/tmp.*` directories each holding one
`freedom_test` dump with grants/inventory files (left by the database backup/restore tests — one more appears after every web-suite run; not changed here) and
`/var/tmp/r3.wheel`. The baseline snapshot was taken after that removal.

**Finding 2 — item 5b status propagation.** Corrected in the §6 script (new helpers `req`, `save`, `step`, `append_lines`, an `EXIT` trap, `root_facts`,
`prep_user_paths`, `search_user_dirs`):

* `getent passwd root` is run without a pipeline (`root_home=$(… | cut)` is gone); its status is printed, a failure, a duplicate or a malformed record (wrong name,
  uid ≠ 0, relative or empty home, not exactly seven fields) is a fixed finding and no account-context command runs. The root home is compared with and without a trailing slash.
* The dedicated-account record also needs exactly seven fields. `ACCOUNT=freedom-executor` is still a literal; a second literal line `RUN_USER_DIR=/run/user` is
  the only other test seam (a test copy points it at a disposable runtime directory); production text keeps both literal.
* `systemd-analyze --user unit-paths` as the account is run through `save`: its stdout is kept only when the actual status was 0; a failure deletes the partial
  file, prints the status and stderr, and nothing is searched or queried.
* The appends, the two counts (grep rc 1 = none, rc 2 = failure), `sort -u -o` and the line count each report their status and abort the procedure on failure; the
  searches report how many directories were searched and how many returned non-zero (rc 1 = absent path), and the closing line is
  `[item 5b COMPLETE]` or `[item 5b INCOMPLETE]`. The scratch directory is removed by an `EXIT` trap, so it does not survive a failure or an interrupt, and a failed
  `mktemp` stops the script before anything is written.
* The same defect existed in two other `cp "$OUT/last.out" …` copies: item 5's system path set (now `save` + checked append; no directory is searched if the set
  was not formed) and item 11's `pgrep` pid list (status printed; rc 1 = none; other statuses a finding). Output remains identifiers, allowlisted state and path metadata only.

**Fail-first regressions** (`tests/test_production_checklist_item_5b.py`, 47 cases, was 18; root/account NSS stubs, a Python `runuser` stand-in that honors `-p` and
knows a decoy Description/Environment/ExecStart, a disposable account home and a socket-bearing runtime directory, `TMPDIR` pinned and checked empty after every run):
root lookup failure/enumeration failure/failure that still printed a record/empty/duplicate/malformed (11); home equal to a nonstandard root home, with and without a
trailing slash; unavailable bus and missing runtime directory; conflicting ambient `ACCOUNT`; 13 invalid dedicated-account records; account-context
`unit-paths` failing with empty and partial output (rc 1 and 127); failure creating the saved result, failing `sort`, failing append (read-only result): in each, no `find`, no
`list-unit-files`, no `show`; a valid account with every material status represented; the decoy transient unit (identifier and allowlisted state reported, decoy
text, environment name/value and argument 0 times); item 5's system path set formed/not formed. Run against the checklist as returned (copy of the fourth-return
text): **45 of 47 fail**; with only the scratch-directory and seam assertions relaxed, so that the failure is behavioral, **29 of 47 fail** (the pipeline hiding the root lookup, the
unchecked `cp`, the missing summary, scratch left behind). With the correction all **47 pass**.

**Executed proof on `oracle-test`** (synthetic `fbprobe` accounts only, linger on, a transient `freedom-executor-stop-decoy.service` in its user manager with
`--description=DECOY_TOKEN_SHOULD_NOT_PRINT`, environment `DECOY_ENV_SHOULD_NOT_PRINT=secretvalue`, argument `DECOY_ARG_SHOULD_NOT_PRINT`; the test copy differs from the
production text by exactly the `ACCOUNT=` line, shown with `diff`; all accounts, the unit, the linger entry and the scratch were removed afterwards):
(A) the unmodified production text with ambient `ACCOUNT=fbprobe` looked up only `freedom-executor` (`[rc=2]`, deferral line; `fbprobe` appeared once, in item 3's linger listing);
(B) the complete checklist with ambient `ACCOUNT=root`: rc 0, 102 statuses printed (36 non-zero, absent paths and expected pre-provisioning rc), `getent` root and account `[rc=0]`,
`unit-paths` `[rc=0]` (4 paths under the home, 11 under `/run/user/<uid>`), `sort` `[rc=0]`, 15 directories searched (11 non-zero = absent), both unit queries `[rc=0]`,
`[item 5b COMPLETE]`, `Id=freedom-executor-stop-decoy.service`, `LoadState=loaded`, `ActiveState=active`, `SubState=running` and its transient `FragmentPath`, root's home
paths 0, **decoy hits 0**, scratch entries left 0; (C) real accounts with home `/`, `/root` and a nonexistent home: fixed findings, 0 account-context lines;
(D) a `getent` wrapper making the root lookup fail, return two records, and return an empty record with status 0: three fixed findings, 0 account-context lines;
(E) a `runuser` wrapper failing only the `unit-paths` call with partial output: `[rc=1]`, the "discovery failed" finding, `[item 5b INCOMPLETE]`, 0 searches, 0 unit queries, partial text printed 0 times.
Scratch entries left after every case: 0.

**Verification (on `oracle-test`, not the repository host; the exact final executable tree synchronized with the canonical secret-excluding `rsync`, no error; bot, web and root suites run serially; `TEST_DATABASE_URL=postgresql+psycopg:///freedom_test` exported for the web run; skip count checked; no altered command, no retry).**

| Check | Result |
|---|---|
| Complete installer module (incl. every strict-enablement case) | **254 passed**, rc 0. |
| Checklist item 5b/5/11 structural and executable-shell tests | **47 passed**, rc 0. |
| Focused set (executor interrupt/ownership/supervisor/installer/system-service/usermanager, `polkit_tmpfiles`, checklist 5b, rp11 attest/backstop/cleanup/consume/h1_artifact/hold/inspection-failure/pk_sn/records/start/stop, `systemd_unit_control`, `deployment_artifacts`) | **3272 passed, 2 skipped** (documented `RLIMIT_NOFILE`), rc 0, 236 s. |
| Complete root `tests/systemd_integration` (`FREEDOM_SYSTEMD_INTEGRATION=oracle-test`, pinned wheel, root's own `PATH`) | **199 passed, 6 skipped**, rc 0, 24 m 51 s (6 documented reboot-phase skips). |
| Bot suite, serial, `-o tmp_path_retention_policy=failed -rfEs` | **6 failed, 7462 passed, 20 skipped, 39 errors**, rc 1 (16 m 00 s): exactly the accepted baseline (`test_r5_runner.py` 5 F + 39 E; `test_sheet_bootstrap_boundary.py` 1 F). |
| Web suite, serial, `TEST_DATABASE_URL` exported | **1 failed, 2891 passed, 80 skipped**, rc 1 (10 m 07 s); skips exactly 80; the failure is the accepted baseline `test_p3_4_static_assets.py::test_every_evidence_harness_source_in_the_tree_is_declared`. |
| Foundry Node suite | **171 passed, 0 failed**, rc 0. |
| Tree-scanning checks after the last documentation edit (structural guards, `test_p3_4_static_assets.py`, `test_deployment_artifacts.py`, installer module, checklist 5b test, system-service test; re-synchronized; on `oracle-test`) | **506 passed, 1 failed**: the same accepted baseline allowlist failure. No executable instruction changed after the full runs. |
| `compileall` (installer, its tests, the 5b test, `adapters/executor`, `application/executor`, `tests/systemd_integration`), `bash -n` over the extracted checklist, `.claude/hooks/test_guards.py`, `git diff --check` | rc 0 / rc 0 / 40 cases passed / clean. No formatter, linter or type checker is configured (no configuration file) or installed. |

**Incidents.** (a) The secrets guard refused my first two `rsync` attempts (a redirect, then a pipe); the documented bare command succeeded. (b) `rsync --delete` again removes host-only
directories from the disposable checkout. (c) The 29 behavioral failures against the returned text were counted with a throwaway copy of the tests in my scratchpad; that copy is not part of the tree. No other failure,
error, retry or infrastructure incident occurred.

**Final host comparison** (snapshot taken after the scratch removal above, compared with a second one after the last suite run and my own cleanup of `/tmp/pytest-of-ubuntu`, the
web run's dump directory and my `/var/tmp` logs): checkout/runtime ownership and interpreter, accounts/groups/homes, linger, sudoers (the five file hashes), Polkit and `tmpfiles.d`,
units and drop-ins, processes, cgroups, mounts, state/run directories, `/usr/local/libexec`, artifacts, deployment copies, decoys, scratch and pytest residue, OOM counter and failed units are
**identical** except the modification time of `/etc/sudoers.d` and its parent (the root suite installs and removes a rule). The one residue the suites create by design — one `tmp.*`
dump directory per web run — was removed by me, not by the suite.

**Files changed.** Round 4: `tools/executor_supervisor_install.py`, `tests/test_executor_supervisor_install.py`, `tests/test_production_checklist_item_5b.py` (new), `docs/operations/executor-supervisor-provisioning-runbook.md`, this handback, and the current-state records (handover, status, active delivery plan, §20, decision and RAID registers, change log, review index).
Round 5: `docs/review/route-3-production-readiness-handback.md` (§6 prelude and items 5, 5b and 11, §8/§10 notes, this section), `tests/test_production_checklist_item_5b.py` (rewritten, 47 cases), and the same current-state records (superseding entries appended; history kept). No other file changed.

**Remaining production risks and gates.** Unchanged: restoration is operator-recoverable, not automatic; the restoration-write failure, the unverifiable restoring reload, the late-appearing owner, the state-query and enable/disable partial effects and the wants-link observation failures are proved only in the deterministic harness; the §5 transient-risk residual, F-1 to F-3, the sudo `Defaults` premise and the §6 production inspection (including item 5b after provisioning, which must be repeated then) remain open; a separate activation instruction is required. The unexplained host-state discrepancy of Finding 1 is open as an observation: I could not reproduce it, so I cannot say what produced it or exclude a recurrence.

**Conclusion and recommendation.** Item 5b (and the two identical copies in items 5 and 11) now fails closed: every fact-gathering status is printed, a failed producer stops the dependent search, and the scratch cannot outlive the script; 47 executable checks and a decoy probe on the host support this. The host was in the documented state when I looked and is unchanged apart from removed scratch; the cause of Codex's different observation is not established, and the fourth-return section Codex found absent is present in the tree but its own figures are replaced by the new runs above. Nothing was accepted, committed or pushed; production and staging were not touched; no transient-risk decision is made. I recommend independent Codex re-review of this exact tree (checklist §6 and its test), then Peter's decision on the residual risk. I stop after this handback.

## Fourth review remediation return

Codex's re-review of the third remediation left four findings. All are corrected in place; the accepted topology, SA-2 vector,
role semantics, BS-3, strict `ActiveState`, authorization policy and residual-risk options are unchanged. Nothing is accepted,
committed or pushed; no production or staging access occurred.

| # | Finding | Correction |
|---|---|---|
| 1 | `Installer._enabled()` mapped every `OSError` to "disabled", so an unobservable wants link could be recorded, compared or "restored" as disabled | New narrowly named `Installer._observed_enabled()`: only `FileNotFoundError` for the exact wants-link path is disabled, only the expected target (`/etc/systemd/system/<unit>` or `../<unit>`) is enabled; an I/O or permission error, non-symlink object, malformed link or unexpected target raises `enablement-unavailable` (13). `install()` captures it **before** any mutation (a refusal with no write, link or manager command) and uses it for the forward enable check, `_upgrade_intact()` and `_restore_upgrade()`, so after a mutation an enablement that cannot be established or restored is exactly `recovery-incomplete` (15). A verified restoration still re-raises the original failure and allows a safe retry. The lenient `_enabled()` stays only in `verify`, `remove` and `_recover`, whose semantics are unchanged. |
| 2 | Item 5b used `list-units`, which prints each unit's `Description` | Replaced by an explicit allowlist: `systemctl --user list-unit-files` (names and states) and `systemctl --user show <pattern> -pId -pLoadState -pActiveState -pSubState -pFragmentPath -pDropInPaths`. No description, `cat`, `status` or unlisted property. Item 5's system-manager `list-units` had the same disclosure and was changed the same way. The `grep -c … \| sed` pipelines in 5b became command substitutions whose status is printed. |
| 3 | `ACCOUNT=${ACCOUNT:-freedom-executor}` let an ambient value redirect item 5b | `ACCOUNT=freedom-executor` is a literal. `acct_facts` validates one account-database entry (name, uid positive and never 0, home absolute, never `/`, root's home or containing `..`, owned by the uid), then `/run/user/<uid>` ownership and the bus socket, before any `runuser`; every other outcome is a fixed finding (`getent` rc 2 is the deferral line). A test harness substitutes that single line in a separate copy; there is no production override. |
| 4 | Current-state headings said the third remediation was assigned after it returned | Handover, status, active delivery plan, §20, decision and RAID registers, change log (new superseding row) and review index now say the fourth remediation has returned for independent Codex re-review on 2026-10-23. Earlier entries are kept as history. The runbook documents `enablement-unavailable`/`state-unavailable` and the wants-link check in §8b step 2. |

**Regressions.** `tests/test_executor_supervisor_install.py` +21 cases (module 254, was 233): `EIO`, permission and not-a-directory errors on the wants link before an upgrade, initially enabled and disabled (6: `enablement-unavailable`, 13, through `main()`, disk bytes, manager-loaded bytes, running configuration, link state and zero `enable`/`disable`/`daemon-reload` calls asserted, then a safe retry); a non-symlink, a wrong-target link and a malformed link before an upgrade (6, object left untouched, safe retry); the valid disabled state by genuine absence (also with no wants directory) and both accepted link forms; initially disabled, forward `enable` creates the link and every later observation fails (`recovery-incomplete`, 15, through `main()`, link still present, old bytes on disk and loaded, safe retry); initially enabled with the restoration-time observation failing (15); a foreign object or wrong-target link appearing across the restoring reload (3) or left by the forward `enable` (2); and a failure after a failed reload. With `_observed_enabled()` made lenient again (the reviewed behavior), **15 of the new cases fail**; with the correction all **254 pass**. `tests/test_production_checklist_item_5b.py` (new, 18 cases) extracts the real §6 script and runs item 5b under stubs: the literal account and the absence of any `${ACCOUNT…}` default; no `list-units`/`cat`/`status` and only named `show` properties anywhere in the script; a conflicting ambient `ACCOUNT=root` ignored (only `freedom-executor` is looked up and nothing runs in an account context); 11 malformed-NSS cases plus a `getent` failure and root's-home collision refused before any account-context command; and the valid branch passing exactly the validated home, runtime directory and bus to `runuser`. Against a reconstruction of the reviewed 5b, **17 of 18 fail**.

**Executed proof on `oracle-test`** (disposable `fbprobe` account with linger, a transient `freedom-executor-stop-decoy.service` in its user manager with `--description=DECOY_TOKEN_SHOULD_NOT_PRINT`, environment `DECOY_ENV_SHOULD_NOT_PRINT=secretvalue` and argument `DECOY_ARG_SHOULD_NOT_PRINT`). The reviewed `list-units` printed the description decoy 1 time. The corrected block (test-only copy differing from the production text by exactly the `ACCOUNT=` line, checked with `diff`) run with a **conflicting ambient `ACCOUNT=root`** reported `Id=freedom-executor-stop-decoy.service`, `LoadState=loaded`, `ActiveState=active`, `SubState=running` and its transient `FragmentPath`, selected `fbprobe` (home paths under `/home/fbprobe`, runtime paths under `/run/user/<uid>`), printed a status for all 20 commands (11 non-zero were absent paths, rc 1) and printed **every decoy 0 times** (description, environment name and value, argument). The unmodified production text with ambient `ACCOUNT=fbprobe` or `root` looked up only `freedom-executor` (absent: `[rc=2]` and the deferral line, `fbprobe` mentioned 0 times). Real accounts with home `/`, `/root` and a nonexistent home were refused with fixed findings and no `runuser`/`systemctl`; with the user manager stopped the result was the "no runtime directory or bus" finding. The complete checklist ran to its end (`rc 0`, 77 statuses) with a decoy on the system manager printed 0 times. All probe accounts, the transient units and the scratch directory were removed.

**Files changed.** `tools/executor_supervisor_install.py`, `tests/test_executor_supervisor_install.py`, `tests/test_production_checklist_item_5b.py` (new), `docs/operations/executor-supervisor-provisioning-runbook.md`, this handback (§6 item 5/5b, row 5, third-return note, this section) and the current-state records named in finding 4.

**Verification (on `oracle-test`, not the repository host; exact final tree synchronized with the canonical secret-excluding command; shared-state suites serial; `TEST_DATABASE_URL=postgresql+psycopg:///freedom_test` exported for the web run; skip count checked).**

| Check | Result |
|---|---|
| Installer module (incl. every strict-enablement case; exit 15 through `main()`) | **254 passed** on `oracle-test` (also on the repository host). |
| Focused set (executor interrupt/ownership/supervisor/installer/system-service/usermanager, `polkit_tmpfiles`, checklist 5b, rp11 attest/backstop/cleanup/consume/h1_artifact/hold/inspection-failure/pk_sn/records/start/stop, `systemd_unit_control`, `deployment_artifacts`) | **3243 passed, 2 skipped** (documented `RLIMIT_NOFILE`), rc 0, 299 s. |
| Complete root `tests/systemd_integration` (`FREEDOM_SYSTEMD_INTEGRATION=oracle-test`, pinned wheel, root's own `PATH`) | **199 passed, 6 skipped**, rc 0, 25 m 03 s (6 documented host-only reboot-phase skips). This is the rerun after the last executable change; see incident (a) for the discarded earlier run. |
| Bot suite, serial, `-o tmp_path_retention_policy=failed -rfEs` | **6 failed, 7433 passed, 20 skipped, 39 errors**, rc 1 (19 m 28 s): exactly the accepted baseline (`test_r5_runner.py` 5 F + 39 E; `test_sheet_bootstrap_boundary.py` 1 F); no OOM. |
| Web suite, serial, `TEST_DATABASE_URL` exported | **1 failed, 2891 passed, 80 skipped**, rc 1 (10 m 25 s); skips exactly 80; the failure is the accepted baseline `test_p3_4_static_assets.py::test_every_evidence_harness_source_in_the_tree_is_declared`. |
| Foundry Node suite | **171 passed, 0 failed**, rc 0. |
| `compileall` (installer, its tests, the new test, `adapters/executor`, `application/executor`), `git diff --check`, whitespace check of the untracked files, `.claude/hooks/test_guards.py` | rc 0 / clean / no complaints / 40 cases passed. No formatter, linter or type checker is configured or installed (no configuration file; no `ruff`/`mypy`). |
| Tree-scanning checks after the last documentation edit (structural guards, `test_p3_4_static_assets.py`, `test_deployment_artifacts.py`, installer module, checklist 5b test; on `oracle-test`) | **469 passed, 1 failed**: the same accepted baseline allowlist failure (`test_every_evidence_harness_source_in_the_tree_is_declared`). No executable instruction changed after the full runs. |
| Real-manager injection of an `EIO` on the wants link | **Not performed**: it cannot be injected race-free into the real manager without weakening it; the enablement failure paths are proved **only in the deterministic harness**. Item 5b's method is proved on the host (above). |

**Incidents.** (a) My first complete root run was interrupted by me (SIGINT, after a few seconds) to fix a skip in my new test; it left `/var/lib/freedom-blades-executor` and `/run/freedom-blades-executor` behind, so the next complete root run had 39 setup errors (`executor_host_support.Service.install` precondition) plus the three timing-sensitive host failures already reported as intermittent in the earlier returns (`test_route3_attest_host…default_action_termination…`, `test_route3_hold_host…second_activation…`, `test_route3_stop_host…loaded_failed_capture_unit…`). That run (3 failed, 157 passed, 6 skipped, 39 errors) is **not cited**; I removed the residue and reran the whole root suite after the bot/web/Node runs. (b) The secrets guard refused a piped `rsync` once; rerun bare. (c) The documented `rsync --delete` removes host-only directories from the disposable checkout. (d) My first versions of two new tests had harness mistakes (`monkeypatch.undo()` also undoing the `os.lstat` fixture; a `repr` newline in a stub) and were fixed before any cited run; one 5b test skipped on `oracle-test` (the uid had a session bus) and was rewritten to assert both branches, after which the focused set was rerun.

**Final host comparison.** Snapshot before the first sync and after the last run, covering accounts/groups/homes, linger, sudoers and hashes, Polkit/`tmpfiles.d`, units/drop-ins, processes, cgroups, mounts, state/run directories, artifacts, deployment copies, decoys and pytest residue: identical apart from directory mtimes, one `dbus-daemon` of my ssh session and the removal of a stale `/tmp/pytest-of-ubuntu`; `/usr/local/libexec` is `root:root 0755`; no `/run/rp11-*`, `/run/polkit-1`, `freedom-executor` account, executor state/run directory or probe account; no OOM kill (`dmesg` 0); no `rotate-test-gate`/`caddy` orphan; my `/var/tmp` and `/tmp` scratch removed.

**Remaining production risks and gates.** Unchanged from the third return: restoration is operator-recoverable, not automatic; the restoration-write failure, the unverifiable restoring reload, the late-appearing owner, the state-query and enable/disable partial effects and now the wants-link observation failures are proved only in the deterministic harness. The §5 transient-risk residual, F-1 to F-3, the sudo `Defaults` premise and the §6 production inspection (including item 5b after provisioning) remain open; a separate activation instruction is required.

**Conclusion and recommendation.** All four findings are corrected: enablement is observed strictly at every upgrade boundary (`enablement-unavailable` before, `recovery-incomplete` after), item 5b inspects only the fixed account and emits only allowlisted facts (proved by 18 executable checks and a decoy probe on the host), and the current-state headings are reconciled. Nothing was accepted, committed or pushed; production and staging were not touched; no transient-risk decision is made. I recommend independent Codex re-review of this exact tree (installer, its tests, checklist item 5b and its test, runbook diagnostics), then Peter's decision on the residual risk. I stop after this handback.

## Third review remediation return

Codex's re-review of the second remediation left three findings. All are corrected in place; the accepted topology, SA-2 vector,
role semantics, BS-3, authorization policy and residual-risk options are unchanged.

| # | Finding | Correction |
|---|---|---|
| 1 | An unavailable `ActiveState` query became `""`; recorded before an upgrade and seen again during restoration, it compared equal and a `reload-failed` (13) was reported although neither state was ever established | New `Installer._observed_state()` returns only a state the manager actually reported (non-zero result, missing or empty property, or a word outside the systemd state set raises `state-unavailable`, exit 13). `install()` takes it **before** an upgrade can change anything (a recognized fragment): unavailable means a fixed failure with no write, enable, disable or reload. `_upgrade_intact()` and the final restoration check use the same strict query, so a timeout, OS error, non-zero or malformed answer there is exactly `recovery-incomplete` (15). A verified restoration still re-raises the original failure. `_state()` (lenient, `""` when unknown) remains only where unknown already means "may be running" (`remove`, `_drained`). |
| 2 | `_restore_upgrade()` discarded the `systemctl enable`/`disable` status and accepted a matching link | The check is conjunctive: the command must return zero **and** the wants link must independently match the recorded enablement. Non-zero is `recovery-incomplete` even when the command produced the desired link; zero with the wrong link remains `recovery-incomplete`. |
| 3 | §6 item 5 ran `systemd-analyze --user unit-paths` as the operator (root's paths) | New item 5b runs in the account's context (`runuser -u freedom-executor -- env -i HOME= XDG_RUNTIME_DIR=/run/user/<uid> DBUS_SESSION_BUS_ADDRESS=… systemd-analyze --user`, values from the account database), then searches names only in every effective user path plus `$HOME/.config/systemd/user`, `/run/user/<uid>/systemd/{transient,generator*,user.control}`, with a status per directory, lists the account manager's unit files/units and shows the supervisor unit's fragment/drop-in paths (never `cat`). Before the account exists it prints a deferral line; it **must be repeated after provisioning**. *(The fixed-account validation and the `list-units` replacement below are superseded by the fourth return: the third-return method read `ACCOUNT` from the environment and listed units with `list-units`, which printed unit descriptions.)* Scratch output is bounded path lists in `$OUT`, removed explicitly at the end; the sudoers helper is now written to `$OUT` instead of an assumed `/var/tmp` file. The rest of §6 was reviewed: the other account-dependent steps (items 4(d)/4(e), 6 `pkcheck`, 11) already run only after the account exists and use its uid. |

**Regressions (11 new; 10 fail on the reviewed installer, the 11th pins the already-correct verified restoration and retry).** The
reviewed installer was reconstructed by reversing the edits: **10 failed, 223 passed**; corrected installer **233 passed**. Cases: the
initial `ActiveState` query failing, empty, garbage or missing (×4: `state-unavailable`, bytes/loaded/enablement/running/state unchanged, no `enable`/`disable`/`daemon-reload` call, safe retry);
the same while the unit really is stopped (×4); a failed/malformed query after the fragment changed (×4, through `main()`: exactly
`recovery-incomplete`, exit 15, earlier bytes on disk and loaded); a failed final query while the modeled state really changed;
a restoring `enable`/`disable` returning non-zero after producing the link (×2, through `main()`, 15, then a later safe retry);
and a restoring `enable` returning zero without the link. Assertions cover bytes on disk, manager-loaded bytes, enablement, running
configuration and modeled unit state.
(The parametrized "state unavailable after the change" cases pass on the reviewed code too, because the pre-upgrade value there was a real state; the sentinel-equality defect is reproduced by the initial-query cases.)

**Executed proof of the corrected inspection (`oracle-test`, disposable `fbprobe` account with linger, a planted persistent unit with
a drop-in carrying a decoy credential, and a planted transient `freedom-executor-stop-x.service` under `/run/user/<uid>/systemd/transient`).**
The account-context run returned rc 0 with 4 paths under its home and 11 under `/run/user/1002`; root's own `systemd-analyze --user
unit-paths` matched none of them. The planted unit, drop-in directory and transient unit were reported by name; the manager showed
`FragmentPath` and `DropInPaths`; the decoy credential appeared nowhere in the output; non-zero statuses were printed for absent paths (rc 1) and
the scratch directory was removed ("scratch removed"). With a non-existent account the deferral line was printed. The account, linger, user manager and helper files were removed. The whole checklist extracted from this document passes `bash -n`.

**Files changed.** `tools/executor_supervisor_install.py`, `tests/test_executor_supervisor_install.py`, this handback (§6 item 5/5b, row 5,
sudoers helper, scratch cleanup, this section), and the current-state pointers in `docs/review/Handover information`,
`active-delivery-plan.md`, `status.md`, `implementation-plan.md` §20, `decision-register.md`, `raid-register.md`, `change-log.md`, `docs/review/README.md`.

**Verification (on `oracle-test`, not the repository host; exact final tree synchronized with the canonical secret-excluding command; shared-state suites serial; `TEST_DATABASE_URL=postgresql+psycopg:///freedom_test` exported for the web run; skip count checked).**

| Check | Result |
|---|---|
| Installer module | **233 passed** (also on the repository host, `venv-web`). |
| Focused set (executor interrupt/ownership/supervisor/installer/system-service/usermanager, `polkit_tmpfiles`, rp11 attest/backstop/cleanup/consume/h1_artifact/hold/inspection-failure/pk_sn/records/start/stop, `systemd_unit_control`, `deployment_artifacts`) | **3204 passed, 2 skipped** (documented `RLIMIT_NOFILE`), rc 0, 212 s. |
| Complete root `tests/systemd_integration` (`FREEDOM_SYSTEMD_INTEGRATION=oracle-test`, pinned wheel, root's own `PATH`), final tree | **199 passed, 6 skipped**, rc 0, 24 m 17 s (6 documented reboot-phase skips). See incident (a). |
| Bot suite, serial, `-o tmp_path_retention_policy=failed -rfEs` | **6 failed, 7394 passed, 20 skipped, 39 errors**, rc 1 (17 m 09 s): exactly the accepted baseline (`test_r5_runner.py` 5 F + 39 E; `test_sheet_bootstrap_boundary.py` 1 F); no OOM. |
| Web suite, serial, `TEST_DATABASE_URL` exported | **1 failed, 2891 passed, 80 skipped**, rc 1 (10 m 24 s); skips exactly the documented 80; the failure is the accepted baseline `test_p3_4_static_assets.py::test_every_evidence_harness_source_in_the_tree_is_declared`. |
| Foundry Node suite | **171 passed, 0 failed**, rc 0. |
| `compileall` (installer and its tests), `git diff --check`, `.claude/hooks/test_guards.py` | rc 0 / clean / 40 cases passed. No formatter, linter or type checker is configured or installed. |
| Real-manager probe of the state-query / partial-effect failures | **Not performed**: those failures cannot be injected into the real manager deterministically without weakening it; they are proved **only in the deterministic harness**. The earlier real-manager host probes (second return) are unchanged. |

**Incidents.** (a) The first complete root run on this tree ran for 1 h 30 (host heavily loaded; the earlier comparable run took 25 min) and
failed two timing-sensitive host tests, `test_route3_hold_host.py::test_a_second_activation_is_refused_and_leaves_the_first_intact` and
`test_route3_stop_host.py::test_a_loaded_failed_capture_unit_is_stopped` (the latter already reported intermittent in the second return). Both passed standalone (2 passed), and a full
rerun after the last executable change passed 199/6. I did not establish the cause of the failed run; it is reported, not cited as passing evidence. (b) The documented `rsync --delete` again removed host-only `.codex/` and `.aws/`; the
guard refused one piped rsync and I reran it bare. (c) A first `pgrep` cleanliness probe matched its own ssh shell.

**Final host comparison.** Compared with a snapshot taken after my probe account was already removed: accounts/groups/homes, linger, sudoers and hashes, Polkit/`tmpfiles.d`, units/drop-ins, processes, cgroups, mounts, state/run directories, artifacts, deployment copies and decoys are identical apart from directory mtimes, one ssh session scope and polkit's private tmp name; `/usr/local/libexec` is `root:root 0755`; no `/run/rp11-*` or `/run/polkit-1`; no OOM kill; pytest residue and my `/var/tmp` helper files removed.

**Remaining production risks and gates.** Unchanged from the second return: restoration is operator-recoverable, not automatic; the restoration-write failure, the unverifiable restoring reload and the late-appearing owner are not host-proven, nor now the state-query and enable/disable partial-effect failures. The §5 transient-risk residual, F-1 to F-3, the sudo `Defaults` premise and the §6 production inspection (including item 5b after provisioning) remain open; a separate activation instruction is required.

**Conclusion and recommendation.** Both installer verification gaps and the user-unit-path inspection error are corrected, with regressions that fail on the reviewed code and an executed, secret-safe account-context method. Nothing was accepted, committed or pushed; production and staging were not touched; no transient-risk decision is made. I recommend independent Codex re-review of this exact tree (installer, its tests, handback §6 item 5b), then Peter's decision on the residual risk. I stop after this handback.

## Second review remediation return

The second independent Codex review reproduced three installer recovery gaps and two defects in the proposed production
inspection methods. All five are corrected in place. The accepted topology, SA-2 vector, role semantics, BS-3 and authorization
policy are unchanged. Nothing is accepted, committed or pushed; no production or staging access occurred.

| # | Finding | Correction |
|---|---|---|
| 1 | A manager `TimeoutExpired`, `SubprocessError` or `OSError` after an upgrade replaced the fragment bypassed `_restore_upgrade()` (new bytes left on disk, manager holding the old fragment, generic `io-error` 13) | `Installer.install()` now handles **any** exception raised once the fragment may have changed (typed `Failure`, runner timeout/`SubprocessError`/`OSError`, and interruptions). Unless the earlier fragment is already provably in place, loaded, enabled and running as before (`_upgrade_intact`), it runs the verified restoration. If that is verified, the **original exception** is re-raised (a typed failure keeps its fixed word; a timeout still maps to `io-error` 13; a programmer error is not turned into a fixed word or a "restored" claim). If it fails, raises, or cannot be verified, the result is only `recovery-incomplete` (15). `_restore_upgrade()`, `_recover()` and `_restart()` themselves treat a manager that times out or cannot run as a failed step, never as an escaping exception. |
| 2 | A failed upgrade re-enabled an originally enabled unit but left enablement introduced by the attempt on an originally disabled one | Enablement restoration is symmetric: after the checked restoring reload the installer enables **or disables** the unit to match the recorded original, then checks the resulting link, the unit state and the loaded fragment. A disable that fails or exits 0 but leaves the link is `recovery-incomplete`. |
| 3 | `remove()` accepted a running supervisor whose fragment was absent, drained and stopped it, and on reload failure `_recover(None)` discarded the failed restart (reproduced: `reload-failed` 13 with no fragment, no enablement and a failed supervisor) | Smallest fail-closed choice, the first option of the prompt: `remove()` now **refuses before anything changes** when no fragment is installed but the manager reports the unit not `inactive`, or a supervisor still answers on the socket (`11 owner-without-fragment`; an unobservable unit state is `14 drain-unconfirmed`). Nothing is drained, stopped or reloaded. Operator response: `install` (it writes the fragment, enables and reloads and leaves the running supervisor alone) and then `remove`. If an owner nevertheless appears after that check and removal fails, `_recover(None)` restarts what it can but always reports `recovery-incomplete` (15): a manager's in-memory copy is not a persistent owner. A failed restart is never discarded, and removal with the fragment and loaded unit both genuinely absent stays an idempotent no-op. |
| 4 | §6 item 11 used `ps -eo user,args`, which prints every process's arguments (credentials, URLs, tokens) | Replaced: `ps -u freedom-executor -o pid=,user:32=,comm=` (command **name** only, only the account's processes), and a per-pid fixed word saying whether the account's argv equals the expected supervisor argv (compared, never printed). Reviewed the rest of §6: `cat` of logind/journald configuration became a match of the specific keys; `systemctl cat` of production units became `systemctl show` of non-secret properties plus a credential-directive *count*; nothing prints an environment block or process arguments. |
| 5 | The `login.defs` ERE escaped `\|`, and two `find` examples used unescaped shell parentheses | The `login.defs` match uses two plain `-e` patterns (no alternation to escape in a table); every `find` uses `\(`/`\)`; every command lives in one script, no longer inside table cells. The script passes `bash -n` and was executed on `oracle-test` (below). |

**Tests that fail on the reviewed code and pass now.** The reviewed installer was reconstructed by reversing my edits to it; the
module run against it: **23 failed, 193 passed** (all 23 new cases fail), and with the corrected installer **216 passed**.
New (25 cases; 23 fail on the reviewed installer, the other two — the originally enabled restoration and idempotent removal with fragment and loaded unit both absent — pin behavior that was already correct): runner `TimeoutExpired`/`OSError`/`FileNotFoundError` at material
`daemon-reload`, `show` (the loaded-fragment check) and `enable` points with successful restoration, asserting on-disk bytes
(root-owned `0644`), the manager-loaded fragment, the running configuration, enablement and unit state, then a later safe
retry; the same exceptions with an unverifiable restoration (second timeout, second `OSError`, unexpected loaded drop-in, failing
restoration write) giving `recovery-incomplete` through `main()` with exactly the fixed line and exit 15; an interruption and a
programmer error (`KeyboardInterrupt`, `ValueError`) still attempting recovery and never being reported as a restoration; a
disabled unit staying disabled after the forward reload fails, through `main()` (`reload-failed` 13); failure to disable and a
disable that leaves the link (`recovery-incomplete`) with a later safe retry; the originally enabled case; and, for removal, the
refusal for an active/activating/failed/deactivating unit and for a listening supervisor with an `inactive` unit (nothing drained,
stopped or reloaded), an unobservable state, safe operator convergence (`install`, then `remove`), a supervisor that appears
after the refusal check and cannot be recovered (`recovery-incomplete`, never a plain `reload-failed`, with `install` then
`remove` converging), idempotent removal when fragment and loaded unit are both absent, and a manager timeout during removal
(recovered with a verified owner, or `recovery-incomplete` when the restoration also fails). The earlier 191 cases are unchanged.

**Real-path (`oracle-test`) probes added.** `tests/systemd_integration/test_executor_package_host.py` gained two host tests
against the real system manager and the bind-mounted root-owned package: a failed upgrade of a *disabled, running* unit
(first with a failing `daemon-reload`, then with a runner `TimeoutExpired`) leaves the earlier bytes loaded, the unit still
`disabled` with no `wants` link, the running supervisor undisturbed, and a later `install` completes; and a running supervisor
whose fragment and link were deleted (the manager still holding its loaded copy) is refused by `remove` with exit 11 and the
fixed `owner-without-fragment` line, untouched, after which `install` then `remove` converge. No host evidence is claimed for the
restoration-write failure, for an unverifiable restoring reload after a timeout, or for the late-appearing-owner path: those exist
only in the deterministic harness.

**Production inspection (§6).** The script was extracted from this document, passed `bash -n`, and ran to its end on
`oracle-test` with every status printed (76 statuses; non-zero statuses were the expected absent paths). Executed probes with
synthetic facts: the `login.defs` match returned all eight `UID/GID` `MIN/MAX`/`SYS_*` lines from a synthetic file and four lines from
the real one; the reviewed `find` form fails at parse time (`syntax error near unexpected token '('`) while the corrected form
runs, reports rc 0 with **no output for a clean tree** and prints exactly the four violations (account-not-root file, world-
writable file, symlink, FIFO) of a planted tree, `-links +1` finds the hard-linked file, and a nonexistent root reports its own
`rc=1` rather than a clean result. The secret-safe process check was run against a temporary `freedom-executor` account whose
process carried a decoy credential in its argument vector: the reviewed `ps -eo user,args` would have printed it (3 matching
lines), the corrected output contained it **0** times, listed the account's processes by name and flagged the non-supervisor
argv by fixed word; with `EXPECTED` pointed at the other process's argv it reported "the supervisor (expected argv)". The
temporary account and tree were removed.

**Files changed (this return).** `tools/executor_supervisor_install.py`, `tests/test_executor_supervisor_install.py`,
`tests/systemd_integration/test_executor_package_host.py`, `docs/operations/executor-supervisor-provisioning-runbook.md`
(exit codes, symmetric enablement, `owner-without-fragment`, §8b), this handback (§6 rewritten, this section, corrected claims
elsewhere), and the current-state pointers: `docs/review/Handover information`, `active-delivery-plan.md`, `status.md`,
`implementation-plan.md` §20, `decision-register.md`, `raid-register.md`, `change-log.md`, `docs/review/README.md`.

**Verification (all on `oracle-test`, not the repository host; the exact final tree synchronized with the canonical
secret-excluding command; shared-state suites serial; `TEST_DATABASE_URL=postgresql+psycopg:///freedom_test` exported for the web
run and its skip count checked).**

| Check | Result |
|---|---|
| Installer module | **216 passed** on `oracle-test` (and on the repository host, `venv-web`); 23 of the 25 new cases fail on the reviewed installer (above). |
| Focused set (executor interrupt/ownership/supervisor/installer/system-service/usermanager, `polkit_tmpfiles`, rp11 attest/backstop/cleanup/consume/h1_artifact/hold/inspection-failure residual/pk_sn/records/start/stop, `systemd_unit_control`, `deployment_artifacts`) | **3187 passed, 2 skipped**, rc 0, 125 s (the 2 skips are the documented `RLIMIT_NOFILE` cases). |
| Complete root `tests/systemd_integration` (`FREEDOM_SYSTEMD_INTEGRATION=oracle-test`, pinned wheel `FREEDOM_RP11_WHEEL`, root's own `PATH`) on the final tree, including the three new host cases | **199 passed, 6 skipped**, rc 0, 25 m 02 s (6 documented host-only reboot-phase skips). |
| Bot suite `tests/test_*.py`, serial, `-o tmp_path_retention_policy=failed -rfEs` | **6 failed, 7377 passed, 20 skipped, 39 errors** (18 m 16 s), rc 1: exactly the accepted baseline (`test_r5_runner.py` 5 F + 39 E, `test_sheet_bootstrap_boundary.py::test_the_legacy_sheets_connector_still_exposes_read_and_write`); no OOM kill. |
| Web suite `tests/web`, serial, `TEST_DATABASE_URL` exported | **1 failed, 2891 passed, 80 skipped** (10 m 54 s), rc 1; the skip count is exactly the documented 80. The one failure, `test_p3_4_static_assets.py::test_every_evidence_harness_source_in_the_tree_is_declared`, is the accepted baseline allowlist failure (reproduced on pristine `HEAD` in the first return). |
| Foundry Node suite | **171 passed, 0 failed**, rc 0. |
| §6 checklist | `bash -n` ok; run to the end on `oracle-test` (86 statuses printed in the final run, script rc 0); executable probes above. |
| `compileall` (installer, its tests, `adapters/executor`, `application/executor`, the new host tests), `git diff --check`, `.claude/hooks/test_guards.py` | rc 0 / no whitespace error (also `--no-index --check` of the untracked files) / 40 cases passed. No formatter, linter or type checker is configured or installed. |
| Tree-scanning checks after the last documentation edit | structural guards, `test_p3_4_static_assets.py`, `test_deployment_artifacts.py` and the installer module: 413 passed, 1 failed (the same baseline allowlist failure). |

**Failures, skips, retries, incidents.** (a) The first complete root run (before the three host cases existed) failed two
timing-sensitive host tests unrelated to the installer, `test_route3_consume_host.py::test_sigterm_during_the_authorization_series…`
(two `consume` pids visible instead of one) and `test_route3_stop_host.py::test_a_loaded_failed_capture_unit_is_stopped` (`active`
read where `failed` was expected). Both passed 3/3 standalone. A second complete run failed only the consume test again, while the
whole consume module (14), the executor and `polkit_tmpfiles` host modules plus that test (51 passed, 3 skipped) and the attest and
backstop modules plus that test (31 passed, 1 skipped) all passed. I found no interaction and neither module imports the
installer; the third complete run, on the final tree, passed everything (199 passed, 6 skipped). I did not establish the cause of
the two failed runs; that intermittent race is reported, not explained, and runs 1 and 2 are not cited as passing evidence.
(b) My first version of the timeout host test never raised (it tested the wrong counter) and failed once; fixed and rerun.
(c) The documented `rsync --delete` again removed the host-only `.codex/` and `.aws/` directories from the disposable checkout.
(d) The guard refused an `rsync` I piped or chained twice; rerun bare. (e) The bot/web/Node run preceded the three host tests and
the handback/records edits; those touched only `tests/systemd_integration` (not collected by those suites) and documentation, and
the tree-scanning modules were rerun afterwards (table).

**Final host comparison.** Before (captured before the first sync) and after the last run, covering accounts/groups/homes, linger,
sudoers and hashes, Polkit/`tmpfiles.d`, units and drop-ins, processes, cgroups, mounts, state/run directories, artifacts,
deployment copies, decoys and pytest residue: identical except kernel-worker names, one sshd session, the `/usr/local/libexec`
timestamp (`root:root 0755` unchanged) and the removal of a stale `/tmp/pytest-of-ubuntu`. The temporary `freedom-executor`
account and planted tree of the §6 probes were removed; no OOM kill (`dmesg` 0); no pytest, `rotate-test-gate` or `caddy` process.


**Remaining production risks and gates.** The installer's recovery is an operator-recoverable state, not an automatic repair;
failure to write restored bytes, an unverifiable restoring reload after a timeout and the late-appearing owner are not host-
proven. The §5 transient-risk residual, F-1 to F-3, the sudo `Defaults` premise and the §6 read-only production inspection
remain open, and a separate activation instruction is still required.

**Conclusion and recommendation.** The three installer gaps and the two inspection defects are corrected in place, with 23
regression cases that fail on the reviewed installer, two real-manager host probes, and an executed, secret-safe production
checklist. Nothing was accepted, committed or pushed, and production and staging were not touched. I recommend independent Codex
re-review of this exact tree (installer, its tests, runbook §§7–8b, handback §6), then Peter's decision on the residual risk
and monitoring condition. I stop after this handback.

## 0. Review remediation return

Codex found two blocking installer/security defects, an inaccurate residual-risk analysis, incomplete production-inspection
methods and an unfinished handback. All five are corrected in place. The accepted Route 3 topology, SA-2 vector, role
semantics, BS-3 and authorization policy are unchanged.

| # | Finding | Correction |
|---|---|---|
| 1 | Restore failure untested and discarded | `tools/executor_supervisor_install.py`: a failed upgrade or removal now **restores and then verifies** (bytes on disk, manager-loaded fragment with empty `DropInPaths` and the expected effective properties, enablement, unit state; for removal also a running owner with a main PID). Any step that fails or cannot be confirmed exits the new distinct status **15 `recovery-incomplete`**, never the original word and never a "restored" claim. A foreign object at the fragment path is never replaced. §0.1. |
| 2 | Sudo verification accepted a wider run-as | `_sudoers` parses run-as and tags and accepts only run-as `root` (printed `(root)` or `(root : root)`) with the single tag `NOPASSWD` and the exact SA-2 argv. `(ALL)`, `(ALL : ALL)`, other users/groups, lists, extra tags and alternate argv are refused. §0.2. |
| 3 | Residual lifecycle and recommendation | §5 rewritten from the running behavior; the recommendation is restated with a fully specified, **proposed** monitoring condition. |
| 4 | Production fact checks incomplete and unsafe | §6 rewritten: transitive sudo include enumeration, effective Defaults and grants, all Polkit rules, all unit fragments/drop-ins/generators, full ownership scope, reliable status propagation. |
| 5 | Unfinished verification | §3 reports every suite on the exact final tree; §4 lists incidents including the unusable earlier background run. |

### 0.1 Recovery

Before, a failed upgrade discarded the failure of `_place(previous, replace=True)` and ran an unchecked restoring
`daemon-reload`; `_recover()` discarded failure to put the fragment back and never established a persistent owner; and
`_drained()` restarted a drained supervisor without checking it. Now:

* **Upgrade** (`_restore_upgrade`): the earlier bytes go back only over this installer's own marked fragment (anything else is
  left alone); then a checked reload (`LoadState=loaded`, `FragmentPath`, empty `DropInPaths`, `User`/`Group` = the dedicated account,
  `NeedDaemonReload=no`), enablement **restored in both directions** (a unit that was disabled is disabled again; see the second
  return), and the unit state unchanged. This applies to every failure after the fragment may have changed, including a manager
  timeout or OS error (second return), not only a non-zero exit. A restored *earlier* revision may legitimately carry a different
  `Environment=` (the accepted host test `test_an_upgrade_loads_the_new_fragment…` restores one), so for a restoration the
  environment is not compared; a forward install still compares everything. An upgrade that failed before changing
  anything is not reloaded and is not reported as restored. A first-install failure behaves as before.
* **Removal** (`_recover`): the fragment goes back by an exclusive link (never over a foreign object), then enabled, a
  checked reload, a restart, and the manager must report the unit `active` with a main PID. A running supervisor whose fragment
  is absent is refused before anything changes (`owner-without-fragment`, second return). A drain refusal's restart is
  checked the same way. When the loaded configuration cannot be verified the unit is deliberately **not** restarted.
* The result is `recovery-incomplete` (15, fixed line `executor-supervisor recovery-incomplete`). It is raised only after the
  drain and the installer's own emptiness checks; the tool never deletes state, and `remove` stays refused
  (`invocation-pending`) while a record exists (tested). Operator response: runbook §8b (new).

**Tests that fail on the reviewed code and pass now** (the reviewed installer was reconstructed by reversing my edits to it; run against it the module gave 21 failed and 168 passed, and with the corrected installer all 191 pass). New: 11 upgrade and 10 removal
restore-failure cases covering (1) replacement/reload failure then failure to restore the
bytes, (2) bytes restored but the restoring reload failing or loading an unexpected drop-in, (3) removal reload failure then
failure to put the fragment back, (4) restoration then enable or restart failure, a failed stop plus failed restart, and a drain
refusal whose restart fails, (5) the restored-earlier-revision rules (own `Environment=` accepted; another `User=` is `recovery-incomplete`; the forward install still exact) and the successful recoveries still reporting their original word with a verified owner, and
(6) a later safe retry (`install`/`remove`) from every recoverable state; plus a foreign object that takes the fragment's
place (never replaced), unchanged unit state, "nothing changed ⇒ not reloaded", the owned-invocation case, and the
exit-status/fixed-line mapping. Injection is by a failing `_place`, scripted manager reload results, a hook that changes the
manager after a reload, a failing restart and a failing enable.

### 0.2 Sudo verification

`_SUDO_RULE` previously accepted `(ALL)` and `(ALL : ALL)`. The verifier now separates run-as, tags and command:
exactly one listed command; run-as normalised and required to be `root` or `root : root`; tags exactly `NOPASSWD`; command
byte-equal to the SA-2 argv. Table-driven tests: 4 accepted forms, 27 refusals (`(ALL)`, `(ALL : ALL)`, `(root : ALL)`,
`(ALL : root)`, `(ubuntu)`, lists, `#0`, `%wheel`, empty/missing run-as, no/other tag, `SETENV`/`NOEXEC`/`LOG_OUTPUT` in either order,
wildcard, alternate argv, comma list, `ALL`, extra lines, empty), each checked through both `verify` and `install`, and that a wider
run-as writes nothing. **Real host** (`sudo-rs 0.2.13`, exact fixed paths, real `verify`/`install`): the exact rule gave
`not-installed` (12) before and `installed`/`installed` after `install`; each temporary replacement of the drop-in
(`(ALL)`, `(ALL : ALL)`, `(root : ALL)`, `(ubuntu)`, `SETENV`, `NOEXEC`; each passed `visudo -cf` and printed as the real
`sudo -l` form) was refused by both `verify` and `install` with `sudoers-not-exact` (10); the drop-in was restored byte-
identical (`cmp`) and `verify` returned `installed`.

## 1. Scope and files changed

| File | Change |
|---|---|
| `tools/executor_supervisor_install.py` | Verified recovery for upgrade and removal, `recovery-incomplete` (15), strict sudo run-as/tag verification. Nothing else: no path, vector, trust check or topology changed. |
| `tests/test_executor_supervisor_install.py` | +54 cases (§0), then +25 (second return; module total 216). World hooks for restart failure, post-reload faults, the effective user/environment and scripted runner exceptions. |
| `tests/systemd_integration/test_executor_package_host.py` | +3 real-manager host cases (second return): disabled-unit upgrade failure by exit code and by timeout; refusal of a running supervisor with an absent fragment. |
| `tests/test_rp11_inspection_failure_residual.py` (new, 16 cases) | Characterizes the transient inspection-failure behavior (§5). Pins current behavior only. |
| `docs/operations/executor-supervisor-provisioning-runbook.md` | The first return's five operator-text corrections (§2.3), plus exit 15, the exact sudo rule, §8b. |
| This file and the current-state records | The return. |

## 2. Security review and exact-path rehearsal

### 2.1 Chain review — findings and dispositions

I read the executor client, supervisor, ownership store, user-manager adapter, installer, service fragment, and the
cleanup/backstop/attribution core. Every point of the required trace held: fixed executable, argv and sudoers line; no
caller-controlled path, operand, environment or shell at the root transition; one `StartTransientUnit` after a durable
`start-sent` record; recovery adopts and settles, never launches; typed uncertainty everywhere (`HANDED_OFF`, `BLOCKED`,
`NOT_CONFIRMED`).

| # | Finding | Severity | Disposition |
|---|---|---|---|
| F-1 | The supervisor is an **ownership** gate, not a privilege gate. The account is the same uid as its clients and sudoers grants it the fixed vector, so any `freedom-executor` process can run `sudo -n … stop` directly and skip OC-1/2/3 (done in §2.2 step 7, rc 20 "refused: not loaded"). Impact is bounded to the SA-2 `stop` of the capture unit. | Accepted design | Already stated in the runbook §9; the security review must acknowledge it explicitly. The executor must be the only code running as the account. |
| F-2 | Installer cannot see sudoers `Defaults` (documented). A `Defaults:freedom-executor env_keep += "PYTHONPATH LD_PRELOAD PATH"` drop-in left `verify` at `installed`. With it, hostile `PYTHONPATH`/`LD_PRELOAD`/`BASH_ENV`/`PATH` reached nothing (no marker created), but that outcome does not distinguish sudo-rs refusing the variables from `-I -S` ignoring them. | Medium for production | Production fact checklist §6 item 4 makes reading the effective `Defaults` mandatory. No code change: the runbook already says the vector must not be activated if it cannot be confirmed. |
| F-3 | The supervisor unit has no sandbox directives: `systemd-analyze security` exposure 9.0 UNSAFE. It runs as the unprivileged account with `NoNewPrivileges=yes` and `CapEff=0`, no sessions, locked password. | Low (hardening) | Not applied: adding `ProtectSystem=`, `RestrictAddressFamilies=` etc. changes the accepted boundary and needs its own proof (bus, cgroup delegation). Offered for the security review. |
| F-4 | `verify` says `not-installed` for an installed fragment that is stale or modified. | Low (diagnostic) | Runbook now says so. Wording kept: the fixed words are an interface. |
| F-5 | Revoke order in the runbook fails: after `loginctl disable-linger` the user manager stays `deactivating` for several seconds and `userdel` refuses ("currently used by process"). | Low (runbook) | Fixed in the runbook (wait for `inactive`). Hit for real in my teardown. |
| F-6 | `remove` under continuous admission was refused 6 of 6 times; each refusal restarts the supervisor and turns in-flight requests into `HANDED_OFF`. | Low (operational) | By design and fail-closed; runbook now says to quiesce the executor first. |
| F-7 | A deployment copied from a setgid checkout keeps `2755` directories. The installer accepts it (no group write). | Info | Runbook notes `chmod -R g-s`. |
| F-8 | `disposable-test-server.md` still lists kernel `7.0.0-31-generic`; the host runs `7.0.0-1013-oracle`, systemd 259.5, sudo-rs 0.2.13, Python 3.12.14 (venv) / 3.14.4 (system). | Info | Not changed (outside the slice). |
| F-9 | (remediation) A failed upgrade/removal could report a restoration that was never established; sudo run-as was wider than documented. | Blocking | Corrected (§0). |
| F-10 | (remediation, found in the rehearsal) After a `recovery-incomplete` removal caused by a higher-precedence unit, `systemctl enable` links `multi-user.target.wants` to the overriding fragment; once the override is removed `install` reports `enable-failed` until `systemctl disable` drops the dangling link. | Low (runbook) | Documented in runbook §8b step 3. |

No finding required changing the accepted design, and none meets a stop condition.

### 2.2 Exact-path rehearsal — topology and results

**Topology.** `oracle-test` (Ubuntu 26.04, kernel 7.0.0-1013-oracle, systemd 259.5, cgroup2, sudo-rs 0.2.13, 2 CPUs,
951 MiB). The ordinary checkout and venv were **parked by rename** (`platform.canon`, `venv-web.canon`);
`/opt/freedom-blades` and `/opt/freedom-blades/runtime` were made root-owned; a secret-free, `.git`-free, root-owned copy
(no `.e*` file; no key or credential file) was placed at `/opt/freedom-blades/platform` and a root-owned `python3.14 -m venv`
with the hash-pinned `jeepney-0.9.0` wheel (`--no-index --no-deps`) at `/opt/freedom-blades/runtime/venv-web`. The real
`freedom-executor` account (system uid 997, `nologin`, owned home, linger), the exact one-command sudoers drop-in, the
artifact built at `/usr/local/libexec/freedom-blades-rp11` and the Polkit `tmpfiles.d` fragment were provisioned with the
accepted installers. **No bind mount or substituted path was used.** Host starting state was captured and re-compared at the
end (§8). Two real reboots in the original rehearsal; the remediation rehearsal (rows 8a–8c) was a second, shorter provisioning
at the same paths without a reboot.

| # | Phase | Result |
|---|---|---|
| 1 | Prerequisite refusal before provisioning | `verify`/`install`/`verify-ready` → `account-missing`, rc 10; nothing installed. |
| 2 | Provisioning | Account, linger, sudoers (`visudo -cf` ok; `sudo -l -U` lists exactly one command), artifact (root:root 0755/0644), `tmpfiles.d` install ok. `polkit_tmpfiles verify` failed three checks before reboot, as designed (runtime dirs absent, fragment postdates boot). |
| 3 | Install without implicit start, explicit first start | `install` → `installed`, unit `inactive`/`enabled`, no state or run directory; `verify-ready` → `supervisor-not-ready`. After `systemctl start`: `ready`; `User/Group=freedom-executor`, `Environment=PATH=/usr/bin:/bin`, `DropInPaths=` empty, `NeedDaemonReload=no`, state/run `0700` owned by the account, one process `python -E -s -m adapters.executor.supervisor`; `sudo -n /bin/true` as the account refused. |
| 4 | Boot without login (reboot 1) | Supervisor `active` unprivileged by itself, `ActiveEnter` 43.41 s after the user manager's 42.80 s, `NRestarts=0`, no "not ready" lines, no login session; `verify-ready` `ready`; `polkit_tmpfiles verify` fully `ok`. |
| 5 | One authorized end-to-end OC interruption | As `freedom-executor`: active capture unit + canonical consume journal → exit 0; capture unit `inactive`; **exactly one** `sudo` journal line for the fixed vector; no record, no invocation unit left. |
| 6a | Client interruption / supervisor restart / admission | Slow-stopping capture unit. Client `kill -9` mid-stop: record kept. Supervisor restart (MainPID 1196→2482) while the invocation unit stayed alive: record re-adopted. Second admission → `BLOCKED`. `remove` → `invocation-pending` (14), unit still enabled/loaded/active. Settled: record gone, **exactly one** vector launch. |
| 6b | Ambiguous same-boot `start-sent` record | Planted into the stopped supervisor's state: `verify-ready` ready, admission `BLOCKED`, **still blocked and present after 75 s**, `remove` refused (14). **Reboot 2**: record gone (changed boot id), supervisor up by itself, admission open (`REFUSED` = the artifact declining a missing capture unit). |
| 7 | Refusals | Hostile env (`PYTHONPATH/HOME/STARTUP/USERBASE/INSPECT`, `BASH_ENV`, `ENV`, `LD_PRELOAD` from a compiled .so, `LD_LIBRARY_PATH`, `PATH` shadow) — **no marker**; `--preserve-env` refused by sudo-rs; `-E` ignored with a warning. 12 alternate argvs and `-u ubuntu` all refused (rc 1). Extra grant / `ALL` / second `SETENV` drop-in → `sudoers-not-exact` (10). Effective drop-in, dash-prefix drop-in, `/run` shadow → `shadowed` (11). Group/world-writable or account-owned code, dependency (`jeepney/low_level.py`, `site-packages` entry), platform dir, runtime dir, `pyvenv.cfg`; symlink in code; FIFO → `code-writable/-symlink/-untrusted` (10). Login shell → `account-unsuitable`; linger off → `linger-off`; altered fragment (`User=ubuntu`) → `not-installed` then restored by `install`; a root-owned listener on the socket path → client `NOT_SENT`, listener received 0 bytes. After every probe `verify-ready` returned `ready`. (My first dependency probe named a nonexistent file; it was redone on `low_level.py`.) |
| 8 | Upgrade (first rehearsal) | Success: new fragment installed atomically (`RestartSec` 1→2), running supervisor untouched until restart. Injected reload failure (fragment with a bad section header, which the real manager rejects) → `reload-failed` (13), previous fragment restored byte-for-byte, supervisor never interrupted. Injected install failure (`chattr +i` on the installed fragment) → `install-failed` (13), nothing changed. This row tested **successful** restoration only; the restore-failure claim made here originally was wrong (see 8b/8c). Rollback to the original fragment → `installed`. |
| 8a | Sudo exact vs wider run-as (remediation) | §0.2, real `verify`/`install`. |
| 8b | **Upgrade, restoration failure at the exact paths** (remediation) | Old recognized fragment installed and loaded, repository fragment given a bad section header (`install` → `reload-failed` 13, old bytes restored, loaded, `active`: the successful path again). Then an old recognized fragment with an extra `Environment=FB_FRAGMENT=old`: the same failure → `reload-failed` (13), restored byte-for-byte and accepted (8b′). Then an old recognized fragment with `User=nobody`, same failing new fragment: `install` → **`recovery-incomplete` (15)**; the old bytes were restored byte-for-byte (`cmp`), the real manager loaded them with `User=nobody`, and the checked reload refused to call a non-dedicated account a restoration; the supervisor stayed `active`. Safe retry: repaired repository fragment → `install` → `installed`, fragment == repository, `verify` `installed`. |
| 8b′ | Restored earlier revision with its own `Environment=` | Accepted by design (`reload-failed`, bytes restored, effective `Environment=PATH=/usr/bin:/bin FB_FRAGMENT=old`). Found by the existing host test `test_an_upgrade_loads_the_new_fragment_after_a_checked_reload_…` failing on my first version of the check (incident 10). |
| 8c | **Removal, restoration failure at the exact paths** (remediation) | With a same-named copy in `/usr/local/lib/systemd/system` (lower precedence): `remove` → reload still shows the unit loaded → `reload-failed` (13); fragment restored, enabled, loaded from `/etc`, supervisor restarted and `active` (successful recovery, real manager). With the copy in `/etc/systemd/system.control` (higher precedence): the same removal → **`recovery-incomplete` (15)**; the fragment was restored byte-for-byte but the manager loaded the override (`FragmentPath` under `system.control`), so the tool did not claim an owner and did not restart the unit (`ActiveState=inactive`); state directory empty and untouched. Operator response rehearsed: remove the override; `install` reported `enable-failed` (a dangling `wants` link to the override, finding F-10); `systemctl disable`, `install`, `start`, `verify-ready` → `ready`. Safe retry of `remove` → `removed`; `install` → `installed`, `ready`. With a state entry planted while stopped, `remove` → `invocation-pending` (14) and the entry survived. |
| 8d | Not injectable on the host | **Failure to write the restored bytes** (the second `_place` failing after the first succeeded) has no race-free host injection (an immutable bit or full filesystem would equally fail the first write). It is covered only by the deterministic unit tests that make the second `_place` fail; no host result is claimed for it. |
| 9 | Drain, removal, reinstall | Removal refused while owned. Under load (3 clients re-admitting back to back, 45 s): `remove` refused 6/6 (`invocation-pending`); **35 vector launches = 30 answered + 5 `HANDED_OFF`** (one per admitted request); 821 `BLOCKED`, 235 `NOT_SENT`. Quiescent: `remove` → `removed`, second `remove` no-op, fragment gone, `LoadState=not-found`, empty state/run dirs left by design, account/linger/sudoers untouched, client `NOT_SENT`. Reinstall + OC interruption pass. |
| 10 | Teardown and restore | §8. |

Not exercised (not possible or out of scope): a *bound* record across a reboot on the host (covered by unit test; the earlier
reboot proof used `start-sent`), a stuck uninterruptible member (kernel-level, covered in the accepted executor handback),
row 8d.

### 2.3 Documentation corrected

Runbook: rehearsal done without bind mount and the deployment recipe; meaning of `not-installed`; wait for `user@<uid>`
`inactive` before `userdel`; quiesce before `remove`; setgid note; (remediation) exit 15, the exact sudo run-as/tag rule, and
§8b "recovery-incomplete: operator response".

## 3. Verification

**The figures in this section are from the first remediation tree and are superseded by the "Second review remediation return" table.** All runs on `oracle-test` (not the repository host), on the final tree synchronized with the canonical secret-excluding
command; shared-state suites serially; web database tests with `TEST_DATABASE_URL=postgresql+psycopg:///freedom_test`
exported and the skip count checked against the documented 80.

| Check | Result |
|---|---|
| (first return; superseded by the second-return table above) Installer module on the repository host and on `oracle-test` | **191 passed** (repository host, `venv-web`, 3.6 s; also inside the focused set below on `oracle-test`). 21 of the new cases fail on the reviewed installer (§0.1). |
| Focused set (executor ownership/usermanager/supervisor/interrupt/installer/system-service; manager/Polkit `systemd_unit_control`; cleanup; backstop; hold; consume; attest; start; stop; artifact; `polkit_tmpfiles`; inspection-failure residual; deployment artifacts) | **3162 passed, 2 skipped**, rc 0, 131 s, on `oracle-test` (20 modules: executor interrupt/ownership/supervisor/installer/system-service/usermanager, `polkit_tmpfiles`, rp11 attest/backstop/cleanup/consume/h1_artifact/hold/inspection-failure residual/records/pk_sn/start/stop, `systemd_unit_control`, `deployment_artifacts`). The 2 skips are the documented `RLIMIT_NOFILE` cases (`test_rp11_h1_artifact.py:1107`). |
| Complete root `tests/systemd_integration` (`FREEDOM_SYSTEMD_INTEGRATION=oracle-test`, pinned wheel, root's own PATH) | **196 passed, 6 skipped**, rc 0, 23 m 34 s (`sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_RP11_WHEEL=/home/ubuntu/jeepney-0.9.0-py3-none-any.whl …/venv-web/bin/python -B -m pytest -q -rfEs tests/systemd_integration`, root's own `PATH`; the 6 skips are the documented host-only reboot-phase cases, e.g. `FREEDOM_TMPFILES_BOOT_PROOF=1`). Afterwards: no `/run/rp11-*`, no `/run/polkit-1`, no `/var/tmp/rp11-act-*`, `/usr/local/libexec` `root:root 0755`. A first run on the tree before the restoration-check correction gave 1 failed (incident 10) and is not cited. |
| Bot suite `tests/test_*.py`, serial, `-o tmp_path_retention_policy=failed` | **6 failed, 7352 passed, 20 skipped, 39 errors** (17 m 21 s), rc 1: exactly the accepted baseline ids (`test_r5_runner.py` 5 F + 39 E, `test_sheet_bootstrap_boundary.py::test_the_legacy_sheets_connector_still_exposes_read_and_write`), as recorded in the executor handback; no OOM kill. Run with `-o tmp_path_retention_policy=failed` and `-rfEs` (the documented host-memory deviation from the bare `-rs` command). |
| Web suite `tests/web`, serial, `TEST_DATABASE_URL` exported (skip count checked) | **1 failed, 2891 passed, 80 skipped** (10 m 33 s), rc 1, with `TEST_DATABASE_URL=postgresql+psycopg:///freedom_test` exported and the skip count **exactly the documented 80**. The one failure, `tests/web/test_p3_4_static_assets.py::test_every_evidence_harness_source_in_the_tree_is_declared`, names five tracked `tools/phase_5_0_evidence/` files that its allowlist does not declare. It is the accepted baseline failure recorded in the manager/Polkit and executor handbacks, and I reproduced it on a pristine `git archive HEAD` extraction on `oracle-test` (same assertion), so it is independent of this change; I did not fix it (outside this slice). |
| Foundry Node suite | **171 passed, 0 failed**, rc 0 (`node --test foundry-module/tests/*.test.mjs`). |
| `git diff --check`, `compileall`, formatter/linter/type checker | No formatter, linter or type checker is configured (no `pyproject.toml`/`setup.cfg`/`ruff`/`mypy` configuration; none installed). `compileall` over the changed Python and `adapters/executor`, `application/executor`, `tools`, `tests/test_executor_*.py`: rc 0. `git diff --check`: rc 0 (tracked files); the new untracked files were checked with `git diff --no-index --check` and report no whitespace error. `python3 .claude/hooks/test_guards.py`: 40 cases passed. |

After the last documentation edits, the tree-scanning modules (`tests/web/test_structural_guards.py`, `tests/web/test_p3_4_static_assets.py`, `tests/test_deployment_artifacts.py`) and the installer module were rerun on `oracle-test`: 388 passed, 1 failed (the same baseline allowlist failure).

Why the full bot/web/Node suites were run although the production change is confined to the installer: structural guards
scan the tree, and the earlier figures would otherwise describe a different tree.

## 4. Incidents and reruns (nothing hidden)

1. The secrets guard refused my first `rsync` because I piped its output; I reran the documented command bare.
2. The documented `--delete` sync removed the host-only `.codex/` and `.aws/` directories from the disposable checkout.
3. My teardown script's wait loop treated `deactivating` as finished, so `userdel` failed once; I waited and finished by hand
   (this is finding F-5).
4. My first dependency-writable probe named a file that does not exist (redone).
5. The first run of the new test module had 14 failures from my own wrong assumptions about the record vocabulary
   (`authorized` is recorded as `unconfirmed`/`still-authorized`; an unreadable `grant.id` leaves a residual); I corrected the
   test to the observed behavior and reran (16 passed). No implementation was changed to make it pass.
6. Two host reboots were deliberate parts of the rehearsal; the root suite and the OOM counter (`dmesg`) restart with a boot.
7. **Earlier background run (superseded, unusable as evidence).** A previous session's background web/Node run reported
   `1 failed, 2891 passed, 80 skipped` (`tests/web/test_p3_4_static_assets.py::test_every_evidence_harness_source_in_the_tree_is_declared`),
   Node 171 pass, and a separate 196-passed/6-skipped systemd run; its task finished with exit 1 and its output was not retained
   in the handback, so it is not cited for any result. The runs in §3 are fresh; the web outcome is reported there with its
   disposition.
8. (Remediation) The first remediation rehearsal's script assumed `install` would succeed after the override was removed; it
   reported `enable-failed` (F-10). I repaired the host by hand with `systemctl disable` and reran those steps; the sequence
   is in row 8c and the runbook. My teardown and the final comparison followed.
9. (Remediation) My first guard test for a foreign object swapped `Installer._place` by assignment; I replaced it with
   `monkeypatch`. One test used `monkeypatch.undo()`, which also undid the suite's `os.lstat` fixture; replaced with a targeted
   undo. Neither touched production code.
10. (Remediation) **My first corrected installer failed one existing root-suite test** (`test_executor_package_host.py::test_an_upgrade_loads_the_new_fragment_after_a_checked_reload_a_failed_reload_never_reports_success_and_the_restart_uses_it`: expected `reload-failed`, got `recovery-incomplete`) because the restoration check demanded the *current* revision's exact `Environment=` of an older recognized fragment that legitimately has an extra variable. That was my over-strict check, not an old defect: the restoration check now judges source and account only (§0.1), the case is pinned in unit tests, and every host rehearsal and suite was **rerun on the corrected tree**; the first root run (1 failed, 195 passed, 6 skipped) and a bot run I interrupted with SIGINT after the fix (no OOM, no orphan) are discarded and not cited.

## 5. Transient inspection-failure decision analysis

**What changed in this analysis.** The first return said the unattributable rule "lasts until CP, `attest` or reboot" and
that the conditions were "independent". Both were wrong. Corrected below from the running behavior.

**The risk as it stands today is narrower than its historical wording.** The hold-era description ("a transient inspection
failure reads as damaged or foreign … BS-3 may disarm") was true then. The accepted remediation since changed it, and I
reproduced the current behavior (`tests/test_rp11_inspection_failure_residual.py`, 16 cases, passing):

* **Failed inspection of the rule** (lookup, `fstat`, content read, attribute listing; 4 injected failures × 3 Polkit
  answers = 12 cases): class `present-uninspected-unremoved`; `hard_stop_permits_disarm` is **false for every Polkit answer**;
  the timer stays the owner; once the failure clears, the **next firing's cleanup removes the grant** and verifies. This
  is already the "bounded retry" and it is covered by the existing host suite as well.
* **Transient failure of `grant.id` alone**: the journal-based removal still removes the grant; the unreadable `grant.id`
  remains a residual that blocks the disarm until a later firing clears it.
* **The remaining path**: the genuine rule with **both** identity sources lost (`grant.id` and a usable ACT journal; both live
  under operator-writable `/var/tmp`, a known accepted property). By the accepted rule "no identity ⇒ A0" it is
  `present-foreign-unremoved` and is never removed. BS-3 then disarms **only if Polkit positively reported
  `not-authorized` after cleanup**. If the rule still authorizes, the series records `unconfirmed` (`still-authorized`) and
  the owner is kept (pinned for all three answers). A firing's own cleanup never disarms while the rule path exists.

**Trigger and record.** Trigger = identity loss **and** a false `not-authorized` for a present rule. These are **coincident
conditions**: nothing in the repository or the tests establishes that they are independent, and a common cause (an operator
or boot event that clears `/var/tmp` and also leaves polkitd without the rules directory) could produce both. The
repository `tmpfiles.d` prerequisite closes the **known boot-order cause** of the false `not-authorized` (polkitd not watching
`/run/polkit-1/rules.d`; `polkit_tmpfiles verify` was `ok` after reboot); it does not prove that every possible false
`not-authorized` observation is closed (a polkitd restart, a reload failure or a rules-directory race are not excluded).
Observable: cleanup exit 1, `rp11-cl hard-stop … rule=present-foreign-unremoved …`, the record
`/var/lib/freedom-blades-rp11/activation/<id>.deact-<k>.json` with a `residual` entry for the rule, then
`rp11-bs disarmed <id> branch=bs-3 …`, and the rule file still present under `/run/polkit-1/rules.d/`.

**Lifecycle after BS-3 disarms (corrected).** For this specific residual:

* **CP** (the RT-1 `consume` role, `ExecStartPre=+` of the next capture-pass start) **detects** the foreign rule and **fails
  the start closed**; it does **not** clear it (`tests/test_rp11_consume.py` CQ-3 foreign/symlink/uninspected,
  `rule_gone=False`; host `test_a_grant_that_is_still_authorizing_after_removal_fails_the_start`).
* **`attest`** (root, interactive) runs the same cleanup core with a unit-state precondition; with no identity it also
  **detects and reports** and does **not** clear the object.
* **Reboot** clears the `/run` object (record `cleared-by-boot`; proven by the accepted RT-5 real-reboot proof, not re-run here).
* Before a reboot a **root operator may remove it** only after separately verifying that it is the foreign residual named by
  the alert/procedure (§5.1), because no automatic path will.
* **Absent a reboot or that verified manual response, the file's lifetime has no automatic bound** once BS-3 has disarmed
  the timer. While it exists, every start of the capture pass fails closed at CP, so the practical effect is
  a standing Polkit authorization that cannot produce a running pass but that nothing removes.

**Detection.** The signals exist (exit status, journal lines, record, rule path). **Nothing in the repository alerts on
them today.**

### 5.1 Options and recommendation

| Option | Effect on the residual | Cost |
|---|---|---|
| A. Accept the residual with **no** added monitoring | The file may persist without bound and unnoticed | None. **Not recommended**: with the corrected lifecycle, nothing bounds or reveals it. |
| A′. Accept **conditionally**, with the monitoring condition below made a precondition of activation | Detected within the maximum interval; removed or cleared by reboot within the response deadline; activation halts meanwhile | An external alert and a named responder (not provided by the repository) |
| B. Never disarm while the rule path exists (make BS-3 match BS-4) | Closes it: the timer keeps the owner until the rule is gone | A genuinely foreign inert file (accepted test `…keeps_the_accepted_bs3`) would leave a timer that fires forever and fails once the 64 KiB terminal journal is full (exit 13): permanent noise needing manual cleanup. Changes an accepted rule. |
| C. New typed state "identity unavailable" retried within the existing bound before a foreign verdict | Targets exactly the residual (identity loss is *unknown*, not *foreign*) | New record class, validator and backstop change plus tests; independent review; delays every real foreign case by up to B firings. Does not help if both identity sources stay lost. |

**Recommendation to Peter (not a decision): A′ for the first bounded activation; revisit B or C only if the monitoring ever
fires.** A is withdrawn: it rested on a lifecycle statement that was wrong. B and C change accepted behavior and are
decision items, not part of this correction.

**Proposed monitoring condition — none of this exists today; Peter must accept it, name the responder, and it must be built
and tested before activation:**

| Element | Proposal |
|---|---|
| Signal | Either (a) the rule path `/run/polkit-1/rules.d/50-freedom-blades-rp11.rules` present while no activation is running (no `rp11-capture-pass-a.service` activity and no unexpired activation record), or (b) a journal line `rp11-bs disarmed <id> branch=bs-3` / `rp11-cl hard-stop … rule=present-foreign-unremoved`. Either is an alert. |
| Maximum detection interval | 5 minutes (a periodic check of (a) at 1-minute cadence, journal match for (b) continuous). The residual's exposure is therefore ≤ 5 minutes before a human is told. |
| Accountable responder | The on-duty activation operator named by Peter (not Claude); a second named person for escalation. |
| Response deadline | Acknowledge within 15 minutes; verified removal or reboot within 60 minutes. |
| Manual verification before removal | As root, confirm: no activation is running; the alert's activation id and its `deact-*.json` record carry a `residual` entry for exactly this path; the file's content equals the reviewed fixed rule text and its owner/mode/type are the reviewed ones. If every check holds, `rm` that one file (then confirm Polkit reports `not-authorized`); if any check fails, do not remove it, treat it as an unexplained foreign rule and escalate. A reboot is the alternative that needs no verification. |
| Escalation | Not verified within the deadline; any mismatch in the verification; a second alert within the activation window; or removal that does not make Polkit answer `not-authorized`. Escalate to Peter. |
| Activation / rollback consequence | No activation without the monitor deployed and a named responder. While an alert is open: no further capture-pass start and no new activation. A `branch=bs-3` disarm with the rule present is a rollback trigger (§7 item 9). Closing the alert needs the rule gone and `polkit_tmpfiles verify` `ok`. |

Evidence for the recommendation: the transient-inspection case the finding was written for is closed and retried; the
leftover path needs two coincident faults, one of whose known causes is closed by the verified `tmpfiles.d` prerequisite; a
live rule is recorded `still-authorized` and keeps its owner; even a retained unattributable grant cannot yield a running
pass because CP fails the start closed. What it does not have: independence of the faults, an automatic bound, or any
current alert. This is a recommendation, not a decision.

### 5.2 Peter's bounded-use decision — 2026-10-25

Peter selects production as the direction and classifies Route 3 as a bounded,
attended migration/cutover evidence facility, not a general maintenance
facility. The residual is accepted only for explicitly authorized attended
activations. Each activation must begin with proof that no residual rule or
activation state exists and end with proof that both are absent; uncertain
cleanup requires verified root removal or reboot before the operating window
closes. Route 3 is disabled or removed after the evidence window.

This bounded decision replaces the need for a permanent monitor for this use
case; the attending operator performs the checks and owns the response. It does
not approve recurring or unattended use. Such use requires a stronger
trusted-identity and automated-reconciliation design, failure-injection tests,
disposable-host rehearsal and independent security review. It also does not
authorize production/staging access, inspection, installation or activation;
those remain separate gates.

## 6. Production-specific read-only fact checklist

Facts `oracle-test` cannot establish. Each step is read-only. **No step prints a secret value:** no command prints process
arguments, environment blocks, whole configuration files that could carry credentials, or unit files; where a file's content
might matter, only a count or the specific non-secret keys are printed. Record **conclusions**, not copies of unrelated
policy. Run only after a separate instruction; this document authorizes no production access.

**Status propagation (applies to every step).** Every checked command is run through `chk`, which prints its own status
immediately and never ends in a pipeline. A line with `rc≠0` is a finding to resolve or explain (for example `getent` rc 2 =
no such account before provisioning, `find` rc 1 on a directory that does not exist, `pgrep` rc 1 = no process), never a
pass. The checklist below is one script: it was checked with `bash -n` and executed on `oracle-test`, where it ran to the
end with every status printed (§3).

| # | Fact | Method (all command shapes are in the script below) |
|---|---|---|
| 1 | OS, kernel, systemd, cgroup, Python | Script item 1. |
| 2 | UID/GID policy, name collision | Script item 2: `getent` for the account and group (rc 2 expected before provisioning) and the `login.defs` match, which uses two plain `-e` patterns so there is no alternation to escape. |
| 3 | User-manager and linger policy | Script item 3 prints only `UserTasksMax`, `KillUserProcesses` and `RemoveIPC` lines, never the files. |
| 4 | **Effective sudo policy**, complete | (a) `visudo -c`, rc must be 0. (b) Enumerate **every file reached through `@include`, `#include`, `@includedir`, `#includedir`, following custom paths transitively** with the enumeration script after the table (it prints path, owner, mode and a hash, never contents). (c) In every file listed, read **all** `Defaults` forms (`Defaults`, `Defaults:user`, `Defaults>runas`, `Defaults!cmnd`, `Defaults@host`) and every alias, and record conclusions: `env_reset` on; `env_keep`/`env_check`/`env_delete` do not pass `LD_*`, `PYTHON*`, `PATH`, `BASH_ENV`, `ENV`; no `setenv`, no `!env_reset`, no `secure_path` weakening, no `Defaults` scoped to `freedom-executor`, its group or a matching alias. (d) Enumerate **every grant reaching `freedom-executor`**: lines naming the user, its group(s) (script item 4 `id`, else `getent group`), `%group`, `#uid`, `ALL` user specs, and user/runas/command aliases, in every enumerated file. (e) After provisioning only: `sudo -n -l -U freedom-executor` must show exactly the one rule (run-as `root`, `NOPASSWD` only), and the installer's own `verify`. Anything that cannot be read or classified means the vector must not be activated. |
| 5 | Existing fragments, drop-ins, generators for **every implicated service name** (`freedom-blades-executor-supervisor.service`, `freedom-executor-stop-*.service`, `rp11-capture-pass-a.service`, the `rp11-*` units, `user@<uid>.service`) | Script item 5: both managers' `unit-paths` are read from a saved copy and each directory, plus the fixed override and generator directories, is searched with the escaped-parenthesis `find`; the dash-truncated drop-in directories (`freedom-.service.d`, `freedom-blades-.service.d`, `freedom-blades-executor-.service.d`) match `freedom*`. Unit properties are shown with `systemctl show`, never `systemctl cat`; a fragment or drop-in is opened only after `secret_directives` reports a count of 0 (a non-zero count is recorded, the file is not printed). **The dedicated account's user manager is inspected by item 5b, in the account's own context.** The account is the literal `ACCOUNT=freedom-executor` (never read from the environment: an ambient `ACCOUNT` is ignored); its uid, home, runtime directory and bus are validated from one account-database entry before any account-context command (never uid 0, `/`, root's home or a `..` path; the home and `/run/user/<uid>` must be directories owned by that uid and the bus a socket), and a missing, malformed or ambiguous account prints a fixed finding and runs nothing. It then runs `systemd-analyze --user unit-paths` as the account (`runuser -u freedom-executor -- env -i HOME=… XDG_RUNTIME_DIR=/run/user/<uid> DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/<uid>/bus …`), searches names only in every effective user path plus the account's home and `/run/user/<uid>/systemd/{transient,generator*,user.control}`, and reports unit state **only through an explicit allowlist**: `systemctl --user list-unit-files` (names and enablement states) and `systemctl --user show <pattern> -pId -pLoadState -pActiveState -pSubState -pFragmentPath -pDropInPaths` (plus `-pSourcePath -pUnitFileState` for the supervisor unit). It never uses `list-units` (its output carries each unit's free-form `Description`), `cat`, `status` or an unlisted property. The system-manager lookup in item 5 uses the same allowlisted `show`. **It needs the account: before provisioning it prints a deferral line, and it must be repeated after provisioning (and after any later change to the account's manager).** |
| 6 | **Polkit**, contents and effect | Script item 6 lists every rules directory polkitd reads (add any directory `dpkg -L polkitd` shows). **Read every `*.rules` file in all of them** (not only names mentioning systemd) for `org.freedesktop.systemd1.*`, a broad `return polkit.Result.YES/AUTH_*`, group or user matches covering `freedom-executor` or `unix-user:`/`unix-group:`, and any `subject` or `unit` test; record each file's owner/mode/hash and your conclusion. Effect after provisioning: the `pkcheck` line in script item 6 must not report authorized. |
| 7 | Ownership, type, links and write mode for the **complete trusted scope**: `/` and each directory in the chain to the code root and to the venv; `/opt/freedom-blades/platform` (whole `adapters/` and `application/` trees); the venv (`pyvenv.cfg`, `bin/python` and its link chain, its `home` and sibling `lib/python3*`, `site-packages` top-level entries, the whole `jeepney` tree); the root interpreter `/usr/bin/python3.14` (its link chain, standard library and `lib-dynload`, which the SA-2 `-I -S` interpreter imports as root); `/usr/local/libexec/freedom-blades-rp11` (whole tree); the repository service fragment | Script item 7: `namei -mo` and `readlink -f` per object (add the directories of the chain to the venv and the artifact); per tree the escaped-parenthesis `find` (it includes files that are not writable but not root-owned, which the installer also refuses): **every printed line is a violation to explain; no output with rc 0 means clean**; `findmnt -T` per root catches a mount inside the scope; `-links +1` on the fragment; the interpreter's `sys.prefix` is read first and its library directory is searched. |
| 8 | `tmpfiles.d` state and Polkit ordering | Script item 8 (run from the repository directory, read-only). |
| 9 | Capacity | Script item 9. |
| 10 | Logging and monitoring | Script item 10 prints only the retention keys, never the journald files; whether the §5.1 monitor can be built and who owns it. |
| 11 | Topology conflicts: who else runs as the account or reaches the capture unit | Script item 11. It never prints `ps` arguments or an environment: it shows the capture unit's non-secret properties and its credential-directive count, the two directories' ownership, and, once the account exists, only `pid`, `user` and the command *name* of processes of that account (`ps -u`), and for each such pid a fixed word saying whether its argv equals the expected supervisor argv (the argv itself is compared, never printed). Confirm the executor will be the only code running as the account (finding F-1); any "NOT the supervisor argv" line is a finding. Before provisioning the answer is "account absent". |
| 12 | Maintenance window, rollback owner, evidence retention | Not a command: Peter names them. |

The script (checked with `bash -n`; `<…>` placeholders appear only inside comments):

```bash
set -u -o pipefail
OUT=$(mktemp -d) && [ -d "$OUT" ] && [ -w "$OUT" ] || { echo "[FINDING] no scratch directory: nothing was run"; exit 1; }
trap 'rm -rf "$OUT"' EXIT   # the scratch never outlives the script, whichever way it ends
chk() { "$@" >"$OUT/last.out" 2>"$OUT/last.err"; local rc=$?; echo "[rc=$rc] $*"; cat "$OUT/last.out" "$OUT/last.err"; return 0; }
# like chk, but returns the command's own status so a caller can stop when a fact that later steps depend on was not established
req() { "$@" >"$OUT/last.out" 2>"$OUT/last.err"; local rc=$?; echo "[rc=$rc] $*"; cat "$OUT/last.out" "$OUT/last.err"; return $rc; }
# save FILE cmd...: FILE holds the command's stdout only when its actual status was 0 (a failed or partial answer is deleted, never reused)
save() { local file=$1 rc; shift; "$@" >"$file" 2>"$OUT/last.err"; rc=$?; echo "[rc=$rc] $*"
         if [ "$rc" = 0 ]; then cat "$file" "$OUT/last.err"; else rm -f "$file"; cat "$OUT/last.err"; fi; return $rc; }
# step LABEL cmd...: runs a bookkeeping step (append, sort, count) and reports its actual status
step() { local label=$1 rc; shift; "$@"; rc=$?; echo "[rc=$rc] $label"; return $rc; }
# append_lines FILE line...: one write whose status is the status of the append
append_lines() { local file=$1; shift; printf '%s\n' "$@" >> "$file"; }
# a command whose output must never be shown (a count, a match): only its status and a fixed word are printed
quiet() { local label=$1; shift; "$@" >/dev/null 2>&1; local rc=$?; echo "[rc=$rc] $label"; return 0; }

# 1  OS, kernel, systemd, cgroup, Python
chk cat /etc/os-release; chk uname -r; chk systemctl --version; chk stat -fc %T /sys/fs/cgroup; chk /usr/bin/python3.14 -V

# 2  UID/GID policy and name collision (getent rc 2 = no such entry = the expected "absent")
chk getent passwd freedom-executor; chk getent group freedom-executor
chk grep -E -e '^(SYS_)?UID_(MIN|MAX)[[:space:]]' -e '^(SYS_)?GID_(MIN|MAX)[[:space:]]' /etc/login.defs

# 3  user-manager and linger policy: only the three keys that matter are printed, never whole files
chk grep -rhE '^(UserTasksMax|KillUserProcesses|RemoveIPC)=' /etc/systemd/logind.conf /etc/systemd/logind.conf.d
chk ls /var/lib/systemd/linger; chk systemctl show -p DefaultTasksMax

# 4  effective sudo policy (a: syntax; b: every reached file, via the enumeration script in this section; e: after provisioning only)
chk visudo -c
chk python3 -I "$OUT/enumerate_sudoers.py"              # item 4(b): save the Python listing printed below this script as that file first; paths, owner, mode, hash, never contents
chk id freedom-executor                                   # rc 1 before provisioning; the group list drives 4(d)
#   chk sudo -n -l -U freedom-executor                    # 4(e), after provisioning: exactly the one rule

# 5  fragments, drop-ins and generators for every implicated name
# the SYSTEM manager's paths (user paths are item 5b) plus the fixed override and generator directories; no directory is searched
# unless the path set was actually formed (a failed producer is reported, never followed by a search that looks complete)
if save "$OUT/paths" systemd-analyze unit-paths && step 'append the fixed override and generator directories' append_lines "$OUT/paths" \
     /etc/systemd/system.control /run/systemd/system.control /run/systemd/transient /run/systemd/generator \
     /run/systemd/generator.early /run/systemd/generator.late /etc/systemd/user /usr/lib/systemd/user /etc/systemd/system.attached; then
  while read -r dir; do
    chk find "$dir" -maxdepth 2 \( -name 'freedom*' -o -name 'rp11*' \)   # rc 1 for a path that does not exist: say so, do not hide it
  done < "$OUT/paths"
else
  echo "[FINDING] the system manager's path set could not be formed: no system-path search was run; item 5 is incomplete"
fi
chk systemctl list-unit-files 'freedom*' 'rp11*'
# list-units would print each unit's free-form Description: ask for an explicit allowlist of properties instead
chk systemctl show 'freedom-executor-stop-*' 'rp11-*' -pId -pLoadState -pActiveState -pSubState -pFragmentPath -pDropInPaths
for unit in freedom-blades-executor-supervisor.service rp11-capture-pass-a.service; do
  chk systemctl show "$unit" -pFragmentPath -pDropInPaths -pSourcePath -pLoadState -pUnitFileState
done
chk systemd-delta --type=extended,overridden,masked
chk ls /etc/systemd/system-generators /run/systemd/system-generators /usr/local/lib/systemd/system-generators /usr/lib/systemd/system-generators /etc/systemd/user-generators /usr/lib/systemd/user-generators
# A fragment is read only after counting its credential-bearing directives; a non-zero count is recorded, the file is not printed.
secret_directives() { grep -c -E '^[[:space:]]*(Environment|EnvironmentFile|LoadCredential|SetCredential|ImportCredential)=' "$1"; }
#   chk secret_directives <fragment-or-drop-in path from the show output above>    (rc 1 with output 0 = none present)

# 5b the dedicated account's own user manager (needs the account; before provisioning only the deferral line is printed)
#    The root invocation of `systemd-analyze --user` describes root's paths, never the account's, so the paths are asked for in the
#    account's context with an explicit trusted HOME, XDG_RUNTIME_DIR and bus address derived from ONE account-database entry.
#    The account is fixed and is never read from the environment: a caller's ambient ACCOUNT cannot redirect this inspection.
#    (A test harness substitutes this single line in a separate test-only copy; there is no production override.)
ACCOUNT=freedom-executor
PROBE_PY=/usr/bin/python3.14   # fixed interpreter (items 1 and 7); a test copy substitutes this literal line
RUN_USER_DIR=/run/user   # the second and last test seam line (a test copy points it at a disposable runtime directory); production text keeps it literal
root_facts() {   # sets ROOT_HOME from exactly one well-formed root record, without a pipeline that could hide the lookup's status
  local entry rc name pw uid gid gecos home shell extra colons
  entry=$(getent passwd root); rc=$?
  echo "[rc=$rc] getent passwd root"
  if [ "$rc" != 0 ]; then echo "[FINDING] root's account record could not be read: item 5b not run"; return 1; fi
  case $entry in *$'\n'*) echo "[FINDING] more than one root account record: item 5b not run"; return 1;; esac
  colons=${entry//[^:]/}
  IFS=: read -r name pw uid gid gecos home shell extra <<<"$entry"
  if [ "${#colons}" != 6 ] || [ "$name" != root ] || [ "$uid" != 0 ] || [[ ! $home =~ ^/[^[:space:]:]*$ ]]; then
    echo "[FINDING] root's account record is malformed: item 5b not run"; return 1; fi
  ROOT_HOME=$home
  return 0
}
acct_facts() {   # sets ACCT_UID ACCT_HOME ACCT_RT; prints why and returns 1 unless every fact is exactly as expected
  local entry rc name pw uid gid gecos home shell extra colons owner
  entry=$(getent passwd "$ACCOUNT"); rc=$?
  echo "[rc=$rc] getent passwd $ACCOUNT"
  if [ "$rc" = 2 ]; then echo "[account absent] DEFERRED: the account's user-unit paths cannot be enumerated yet; repeat item 5b after provisioning"; return 1; fi
  if [ "$rc" != 0 ]; then echo "[FINDING] the account database could not be queried: item 5b not run"; return 1; fi
  case $entry in *$'\n'*) echo "[FINDING] more than one account database entry: item 5b not run"; return 1;; esac
  colons=${entry//[^:]/}
  IFS=: read -r name pw uid gid gecos home shell extra <<<"$entry"
  if [ "${#colons}" != 6 ]; then echo "[FINDING] the account database entry is malformed: item 5b not run"; return 1; fi
  if [ "$name" != "$ACCOUNT" ]; then echo "[FINDING] the entry is not for $ACCOUNT: item 5b not run"; return 1; fi
  if [[ ! $uid =~ ^[1-9][0-9]{0,9}$ ]]; then echo "[FINDING] uid is not a positive number (never 0, never empty): item 5b not run"; return 1; fi
  root_facts || return 1
  if [[ ! $home =~ ^/[A-Za-z0-9._-]+(/[A-Za-z0-9._-]+)*$ || $home == *..* || $home == /root || $home == "$ROOT_HOME" || $home == "${ROOT_HOME%/}" ]]; then
    echo "[FINDING] home is not a dedicated absolute directory (never /, root's home or a path with ..): item 5b not run"; return 1; fi
  owner=$(stat -c %u -- "$home"); rc=$?
  if [ "$rc" != 0 ] || [ "$owner" != "$uid" ] || [ ! -d "$home" ]; then echo "[FINDING] home is not a directory owned by uid $uid: item 5b not run"; return 1; fi
  ACCT_UID=$uid; ACCT_HOME=$home; ACCT_RT=$RUN_USER_DIR/$uid
  owner=$(stat -c %u -- "$ACCT_RT"); rc=$?
  if [ "$rc" != 0 ] || [ "$owner" != "$uid" ] || [ ! -d "$ACCT_RT" ] || [ ! -S "$ACCT_RT/bus" ]; then
    echo "[FINDING] no runtime directory or bus for uid $uid (its user manager is not running; is linger on?): item 5b not run"; return 1; fi
  return 0
}
prep_user_paths() {   # forms $OUT/user-dirs from the account manager's own answer; returns 1 on the first step whose status is not as required
  local n rc dir want
  save "$OUT/user-paths" asacct systemd-analyze --user unit-paths || { echo "[FINDING] the account's unit-path discovery failed: no user-path search or unit query was run"; return 1; }
  step 'append the account home and runtime directory paths' append_lines "$OUT/user-paths" "$ACCT_HOME/.config/systemd/user" "$ACCT_RT/systemd/transient" \
    "$ACCT_RT/systemd/generator" "$ACCT_RT/systemd/generator.early" "$ACCT_RT/systemd/generator.late" "$ACCT_RT/systemd/user.control" \
    || { echo "[FINDING] the effective path set could not be completed: no user-path search or unit query was run"; return 1; }
  n=$(grep -c "^$ACCT_HOME/" "$OUT/user-paths"); rc=$?; echo "[rc=$rc] user-paths under the account home: $n"          # rc 1 = none, rc 2 = the count failed
  [ "$rc" -le 1 ] || { echo "[FINDING] the home-path count failed: no user-path search or unit query was run"; return 1; }
  n=$(grep -c "^$ACCT_RT/" "$OUT/user-paths"); rc=$?; echo "[rc=$rc] user-paths under the account runtime dir: $n"
  [ "$rc" -le 1 ] || { echo "[FINDING] the runtime-path count failed: no user-path search or unit query was run"; return 1; }
  step 'sort -u the effective path set' sort -u -o "$OUT/user-dirs" "$OUT/user-paths" \
    || { echo "[FINDING] the effective path set could not be normalized: no user-path search or unit query was run"; return 1; }
  want=$(wc -l < "$OUT/user-dirs") || { echo "[FINDING] the normalized path set could not be counted: no search or unit query was run"; return 1; }
  [ "$want" -gt 0 ] || { echo "[FINDING] the normalized path set is empty: no user-path search or unit query was run"; return 1; }
  return 0
}
search_user_dirs() {   # names only (never contents); a path is "absent" only when os.lstat raises ENOENT, any other failed search is a failure
  local dir rc
  SEARCHED=0; ABSENT=0; SEARCH_FAILED=0
  while read -r dir; do
    SEARCHED=$((SEARCHED + 1))
    req find "$dir" -maxdepth 2 \( -name 'freedom*' -o -name 'rp11*' \) && continue
    "$PROBE_PY" -I -S -c 'import os,sys
try: os.lstat(sys.argv[1])
except FileNotFoundError: sys.exit(10)
except OSError: sys.exit(11)' "$dir" 2>/dev/null; rc=$?   # fixed statuses from the errno, never from diagnostic text: 0 exists, 10 ENOENT, anything else unavailable
    if [ "$rc" = 10 ]; then
      ABSENT=$((ABSENT + 1)); echo "[absent] a searched user-path directory does not exist (ENOENT)"
    else
      SEARCH_FAILED=$((SEARCH_FAILED + 1)); echo "[FINDING] a user-path search failed and its absence was not established (probe status $rc)"
    fi
  done < "$OUT/user-dirs"
  echo "[searched $SEARCHED user-path directories; $ABSENT established absent; $SEARCH_FAILED failed]"
  [ "$SEARCH_FAILED" = 0 ] && [ "$SEARCHED" = "$(wc -l < "$OUT/user-dirs")" ]
}
if acct_facts; then
  asacct() { runuser -u "$ACCOUNT" -- env -i PATH=/usr/bin:/bin HOME="$ACCT_HOME" XDG_RUNTIME_DIR="$ACCT_RT" \
               DBUS_SESSION_BUS_ADDRESS="unix:path=$ACCT_RT/bus" "$@"; }
  if prep_user_paths && search_user_dirs; then
    # Unit state as the account's manager reports it, as an explicit allowlist: the implicated unit identifier, its load/active/sub state
    # and its fragment and drop-in PATHS. Never `list-units` (it prints each unit's free-form Description), never `cat`, never an
    # unlisted property (command arguments, environment values). rc != 0 = the manager is not reachable.
    QUERY_FAILED=0
    req asacct systemctl --user list-unit-files 'freedom*' 'rp11*' || QUERY_FAILED=$((QUERY_FAILED + 1))   # unit file names and enablement states only
    req asacct systemctl --user show 'freedom-executor-stop-*' 'freedom-blades-*' 'rp11-*' -pId -pLoadState -pActiveState -pSubState -pFragmentPath -pDropInPaths \
      || QUERY_FAILED=$((QUERY_FAILED + 1))
    req asacct systemctl --user show freedom-blades-executor-supervisor.service -pId -pLoadState -pActiveState -pSubState -pFragmentPath -pDropInPaths -pSourcePath -pUnitFileState \
      || QUERY_FAILED=$((QUERY_FAILED + 1))
    if [ "$QUERY_FAILED" = 0 ]; then
      echo "[item 5b COMPLETE] the path set was formed, every existing directory was searched, and all 3 unit queries succeeded"
    else
      echo "[item 5b INCOMPLETE] $QUERY_FAILED of 3 unit queries reported a non-zero status; the unit state above is not a complete answer"
    fi
  else
    echo "[item 5b INCOMPLETE] the effective user-path set was not established and searched; nothing above is a complete answer"
  fi
fi

# 6  Polkit: every rules directory polkitd reads (add any directory `chk dpkg -L polkitd` shows), then read every *.rules file
for dir in /etc/polkit-1/rules.d /usr/share/polkit-1/rules.d /usr/local/share/polkit-1/rules.d /run/polkit-1/rules.d; do
  chk ls -la "$dir"
done
chk ls -la /etc/polkit-1/localauthority /etc/polkit-1/localauthority.conf.d
chk systemctl is-active polkit.service; chk ls -ld /run/polkit-1/rules.d
#   after provisioning, with PID = a short-lived process run as freedom-executor (must not report authorized):
#   chk pkcheck --action-id org.freedesktop.systemd1.manage-units --process "$PID" --details unit freedom-blades-executor-supervisor.service

# 7  ownership, type, links and write mode of the complete trusted scope
chk namei -mo /opt/freedom-blades/platform/adapters
chk namei -mo /opt/freedom-blades/runtime/venv-web/bin/python
chk readlink -f /opt/freedom-blades/runtime/venv-web/bin/python
chk readlink -f /usr/bin/python3.14
for root in /opt/freedom-blades/platform/adapters /opt/freedom-blades/platform/application /opt/freedom-blades/platform/infra/executor \
            /opt/freedom-blades/runtime/venv-web /usr/local/libexec/freedom-blades-rp11; do
  chk find "$root" \( ! -user root -o -perm /022 -o -type l -o \( ! -type f ! -type d \) \) -printf '%u %g %m %y %p -> %l\n'
  chk findmnt -T "$root"
done
chk find /opt/freedom-blades/platform/infra/executor/freedom-blades-executor-supervisor.service -links +1
chk /usr/bin/python3.14 -c 'import sys;print(sys.prefix)'; PREFIX=$(sed -n 1p "$OUT/last.out")
chk find "$PREFIX/lib/python3.14" \( ! -user root -o -perm /022 \) -printf '%u %g %m %y %p\n'

# 8  tmpfiles.d state and Polkit ordering (read-only)
chk bash -c 'cd /opt/freedom-blades/platform && exec python3 -m tools.polkit_tmpfiles verify'

# 9  capacity
chk nproc; chk free -m; chk df -h /var /run /opt; chk cat /proc/sys/kernel/pid_max

# 10 logging: only the retention keys are printed
chk journalctl --disk-usage
chk grep -rhE '^(Storage|SystemMaxUse|RuntimeMaxUse|MaxRetentionSec|ForwardTo[A-Za-z]*)=' /etc/systemd/journald.conf /etc/systemd/journald.conf.d

# 11 topology: who runs as the account, and who else reaches the capture unit. No process arguments, no environment, no
#    unrelated process is printed. Before provisioning the account is absent and the answer is "none".
chk systemctl show rp11-capture-pass-a.service -pFragmentPath -pDropInPaths -pActiveState -pUser -pGroup
quiet 'credential directives in the capture unit fragment (count only)' secret_directives /etc/systemd/system/rp11-capture-pass-a.service
chk ls -ld /var/lib/freedom-blades-rp11 /run/freedom-blades-executor
if getent passwd freedom-executor >/dev/null; then
  chk ps -u freedom-executor -o pid=,user:32=,comm=          # name only: never args
  EXPECTED='/opt/freedom-blades/runtime/venv-web/bin/python -E -s -m adapters.executor.supervisor '
  pgrep -u freedom-executor >"$OUT/pids" 2>"$OUT/last.err"; rc=$?; echo "[rc=$rc] pgrep -u freedom-executor"; cat "$OUT/last.err"   # rc 1 = no process runs as the account
  if [ "$rc" = 0 ]; then
    while read -r pid; do                                   # scoped to the account's own pids; argv compared, never printed
      if [ "$(tr '\0' ' ' < "/proc/$pid/cmdline")" = "$EXPECTED" ]; then echo "pid $pid: the supervisor (expected argv)"
      else echo "pid $pid: NOT the supervisor argv (argv not printed): investigate"; fi
    done < "$OUT/pids"
  elif [ "$rc" != 1 ]; then echo "[FINDING] the process lookup failed: the account's processes are unknown"; fi
else
  echo "[account absent] no process can run as freedom-executor"
fi

rm -rf "$OUT"; [ ! -e "$OUT" ] && echo "scratch removed"   # the only scratch directory: bounded, non-secret path lists, removed explicitly
```

Item 4(b), `python3 -I "$OUT/enumerate_sudoers.py"` (prints `FILE <path> uid= gid= mode= sha256=`; tested on `oracle-test` with a custom
chain, an `@includedir` and a skipped dotted name):

```python
import hashlib, os, re, socket
seen, todo = set(), ["/etc/sudoers"]
host = socket.gethostname().split(".")[0]
while todo:
    f = todo.pop()
    if f in seen:
        continue
    seen.add(f)
    st, data = os.stat(f), open(f, "rb").read()
    print(f"FILE {f} uid={st.st_uid} gid={st.st_gid} mode={st.st_mode & 0o7777:o} sha256={hashlib.sha256(data).hexdigest()}")
    for line in data.decode("utf-8", "replace").splitlines():
        m = re.match(r"\s*[@#](include|includedir)\s+(\S.*?)\s*$", line)
        if not m:
            continue
        target = m[2].strip('"').replace("%h", host).replace("%%", "%")
        if not target.startswith("/"):
            target = os.path.join(os.path.dirname(f), target)
        if m[1] == "include":
            todo.append(target)
        else:
            todo.extend(os.path.join(target, n) for n in sorted(os.listdir(target)) if "." not in n and not n.endswith("~"))
```

An unreadable or missing included file raises, so the script exits non-zero instead of listing a partial set.

### 6.1 Production inspection result — 2026-10-25

Peter explicitly authorized this section's read-only production inspection.
Codex established the target from the current checkout and active
`freedom-bot.service`: its `WorkingDirectory` is
`/opt/freedom-blades/platform`. Only the secret-safe checks above were run. No
account, package, policy, file ownership, service or runtime state changed.

**Disposition: NO-GO for provisioning or activation.** This is a fact record,
not remediation authority.

| Checklist area | Production conclusion |
|---|---|
| 1–3 host/account policy | Ubuntu 24.04.4, kernel 6.8.0-139, systemd 255 and unified cgroup v2. `/usr/bin/python3.14` is absent. `freedom-executor` user/group are absent. UID/GID normal ranges are 1000–60000. No explicit relevant logind setting was found; its drop-in directory is absent. No linger entry exists. |
| 4 sudo | `visudo -c`, recursive include enumeration and semantic classification could not read `/etc/sudoers`; non-interactive sudo requires a password. The effective `Defaults` and grants are therefore **incomplete**, never passed. No credential was requested or printed. |
| 5 units/topology | The Route 3 supervisor, capture-pass and stop units are not installed. The existing `freedom-bot`, `freedom-web` and `freedom-worker` names do not collide. The dedicated account is absent, so item 5b is correctly deferred and must be repeated after provisioning. |
| 6 Polkit | Polkit is active. `/run/polkit-1/rules.d` and the local/share directory are absent. Five public rules were classified; none referenced a `systemd1` action or `freedom-executor`. `/etc/polkit-1/rules.d` is root/polkitd-only and could not be read, so the complete policy conclusion and post-provision `pkcheck` remain open. |
| 7 trusted scope | The current live tree is not an executor deployment. Violation counts are 203 under `adapters/`, 185 under `application/`, two under `infra/executor` and 5,334 under the venv. The tree/venv are non-root-owned and group-writable; the venv contains links and resolves to `/usr/bin/python3.12`. `/usr/local/libexec/freedom-blades-rp11` is absent. The repository service-fragment link-count check found no extra hard link. |
| 8 tmpfiles/ordering | `python3 -m tools.polkit_tmpfiles verify` returned 12: source is present, but the installed fragment, both runtime directories and fragment-before-boot condition fail. Polkit ordering checks themselves pass. |
| 9 capacity | 6 CPUs; 7.7 GiB RAM with about 2.9 GiB available at inspection; 4 GiB swap; root volume 233 GiB with 134 GiB available; `/run` 788 MiB with 786 MiB available. No capacity blocker observed. |
| 10 logging | Journals use 183.1 MiB. No explicit relevant journald retention key was found and its drop-in directory is absent. The bounded attended-use decision does not require the unbuilt recurring monitor, but item 12 still must name evidence retention. |
| 11 process exclusivity | The Route 3 capture unit and runtime/state paths are absent. With no `freedom-executor` account, no process can run as it. Repeat after provisioning to establish F-1's exclusivity premise. |
| 12 operations | Open: maintenance window, rollback owner, attending operator/escalation contact for the eventual activation, and evidence-retention period are not named. |

**Next gate.** Complete items 4 and 6 from a root session, still read-only.
Then prepare a reviewed provisioning plan that creates a separate trusted,
root-owned deployment and resolves every prerequisite without treating the
current live working checkout as trusted executor code. Installation,
ownership changes, account creation, policy edits, service changes and
activation each remain outside this inspection authority. All account- and
effect-dependent checks repeat after any separately authorized provisioning.

### 6.2 Production remediation return — 2026-10-25 (stopped at Phase B)

**Authorization received.** Peter gave the follow-up prompt, supplied a
time-boxed root grant (temporary sudoers drop-in, auto-expiring after 3 h),
named himself rollback owner, set evidence retention to "until reviewed", and
approved a SHA256-pinned standalone Python 3.14 tarball and `rp11_h1.py` from
the reviewed tree. Operator: Claude. Window: opened 2026-10-25 ~14:00 UTC.

**Phase A (root-only, read-only) — complete, no blocker in the policy.**
`visudo -c` initially returned 1 only because `/etc/sudoers.d/foundry-bot` was
mode 0644. Peter approved `chmod 0440` on that one file; `visudo -c` now returns
0 and the file hash (`b635341c389b`) is unchanged. Sudoers: the only include is
`@includedir /etc/sudoers.d`; `env_reset` set; no `env_keep`/`env_check`/
`env_delete`/`SETENV`/`!env_reset`; `secure_path` is the Ubuntu default; no
aliases; grantees are `root`, `foundry`, `%sudo` (member: `foundry`) and
`%admin` (empty). Nothing can reach the not-yet-existing `freedom-executor`.
Polkit: `/etc/polkit-1/rules.d` is empty; five packaged rules (hashes
`543995005caa`, `29f073ed9a8a`, `16da883b6ec3`, `06c328a41876`, `f199e386a929`)
contain no `systemd1` action or `freedom` identity; identity tests are the
`sudo`/`admin` groups only. All Route 3 state remains absent. This closes the
open items in §6.1 rows 4 and 6; it does not close the post-provision checks.

**Phase B — blocker: path-coexistence conflict. No Phase C step was taken.**
The runbook's fixed code root and venv are the live paths, and they are in use:
- `freedom-bot` (since 2026-10-23 06:42:16) runs `venv-bot` and
  `freedom-worker` (06:42:17) runs `venv-web`, both with `WorkingDirectory`
  `/opt/freedom-blades/platform`. Replacing `venv-web` with a Python 3.14 venv
  holding only `jeepney` would break the worker at its next restart.
- `/opt/freedom-blades`, `platform`, `runtime` and both venvs are
  `foundry`-owned `2775`. The checkout is the maintainer's canonical working
  repository: 57 uncommitted entries (many untracked, existing nowhere else)
  and 92 commits ahead of `origin/main`. Making it root-owned and `.git`-free
  at that path is the case the prompt tells the operator to stop on.
- Moving the live services to another path requires editing and restarting
  them, which the assignment forbids.

Existing services were not touched: boot id `01a8708d-…`, uptime since
2026-09-10, no reboot, no restart. Production changes made in total: the
temporary grant (Peter) and the `foundry-bot` mode fix (approved). No Python
install, account, sudoers entry for the executor, tmpfiles fragment, artifact or
state directory was created. The supervisor is not installed, no capture path
exists and no migration or cutover ran. No repository code changed; no
behavioral suite was required.

**Recommendation: not ready.** Provisioning on this host needs a maintainer
architecture decision first (a separate root-owned deployment root and venv with
the services moved onto non-conflicting paths, or no Route 3 on this host).

## 7. Deploy and rollback outline (not an executable instruction)

1. **Preflight** (read-only): §6 complete and compared with this handback; stop if sudo `Defaults` cannot be read or any
   topology conflict exists.
2. **State capture**: record accounts, linger, sudoers hashes, units, `/run/polkit-1`, `/opt/freedom-blades` owners; take the
   rollback copy of the current deployment.
3. **Provision** (runbook §2–§4): `tmpfiles.d` prerequisite and reboot window; account and linger; one-command sudoers;
   root-owned deployment and venv; SA-2 artifact. `verify` must say `not-installed`, then refusals must be absent.
4. **Install**: `install` (no start); `verify`. Exit 15 (`recovery-incomplete`) at any step is a stop: runbook §8b.
5. **Start or reboot**: `systemctl start` or the maintenance reboot; `verify-ready` = `ready`; unit `active`, no restarts.
6. **Health/ownership checks**: `User/Group`, `DropInPaths` empty, `PATH`-only environment, state/run `0700`, one process,
   `sudo -n /bin/true` refused for the account.
7. **One bounded smoke test**: one synthetic interruption in the window; expect exactly one vector `sudo` line, capture unit
   stopped, no residual record or invocation unit.
8. **Monitoring** (the §5.1 proposed condition) on from this point, and not before it is built and tested.
9. **Rollback triggers**: any refusal word from `verify`/`verify-ready`; exit 15; more than one vector line for one request; a
   record that does not settle; `NOT_CONFIRMED`/`HANDED_OFF` that persists beyond the settlement bound; a rule file present
   with no activation; a `branch=bs-3` disarm with the rule present; a boot where the supervisor is not ready within the
   window.
10. **Rollback / remove order**: quiesce the executor; `remove` (refused ⇒ resolve, do not delete records); delete the
    sudoers drop-in; `disable-linger`; wait for `user@<uid>` `inactive`; `userdel -r`; remove the artifact and, last, the
    `tmpfiles.d` fragment.
11. **Evidence retention**: this handback, the `verify` outputs, the journal excerpts of the smoke test, the sudoers hashes.

| Category | Items |
|---|---|
| Proved on `oracle-test` | steps 3–7 and 10 of the outline at the real paths, including both reboots, failure injection (reload failure, upgrade and removal `recovery-incomplete`) and removal; the exact-versus-wider sudo rule through the real installer |
| Needs later read-only production confirmation | §6 in full |
| Needs Peter's risk decision | the §5 residual (A′/B/C) and the §5.1 monitoring condition |
| Needs independent security/operations acceptance | F-1 to F-3, the sudo `Defaults` premise, the topology |
| Needs a separate production activation instruction | every step above on production |

## 8. Final host restoration

*(Superseded by the Fifth review remediation return: the restoration statements below were not backed by a comparison Codex could repeat; the Fifth return records the host state actually observed and a fresh comparison.)*

The host was compared before and after (accounts, groups, homes, linger, sudoers and hashes, Polkit/tmpfiles, units,
user managers, processes, cgroups, mounts, state/run directories, libexec, `/var/tmp`, pytest residue, OOM counter).
After the original rehearsal: differences were only directory timestamps, `systemd-private-*` directories renewed by the two
reboots, and the per-boot OOM counter (6 → 0). After the remediation rehearsal's teardown the same comparison differed only in
directory timestamps and my own scratch script. **No** account, group, home, linger file, sudoers file, unit (including the
`/usr/local/lib/systemd/system` and `system.control` overrides), process, cgroup, mount, Polkit/tmpfiles fragment, state/run
directory, libexec artifact or deployment copy remains. `/opt/freedom-blades/{,runtime}` are back to
`ubuntu:ubuntu` `0755`/`0775`, `platform` is the canonical setgid checkout, `venv-web` is the Python 3.12.14 venv, and my
scratch files in `/var/tmp` and `/srv/fb-stage` are removed. Final check after the last suite run (`snap-after` against the pre-rehearsal capture): only directory timestamps, the polkit `systemd-private-*` directory renewed by the root suite's polkit restarts, and the removal of a stale `/tmp/pytest-of-ubuntu` differ; no OOM kill (`dmesg` 0), no pytest/`rotate-test-gate`/`caddy` process, no `freedom-executor` account, no unit or file of this slice. `systemctl is-system-running` reports `degraded` solely because `ModemManager.service` is failed, which is unrelated and predates this work (host up since 00:49). My scratch under `/var/tmp` was removed.

## 9. Remaining risks and gates

* The §5 residual awaits Peter's decision; no monitoring exists in the repository yet, and the corrected lifecycle has no
  automatic bound.
* F-1 (same-uid clients can run the fixed vector) and F-2 (sudo `Defaults` invisible to the installer) rest on
  production facts and on the security review.
* Unit hardening (F-3) is open for the review.
* Trust is verified at install/verify time; ownership and mode are not re-checked while the service runs.
* `recovery-incomplete` is an explicit, operator-recoverable state, not an automatic repair: a failure to write the restored
  bytes was exercised only by deterministic tests, not on the host (row 8d). After a failed removal the unit may be left
  stopped by design until the operator acts.
* A bound record across a reboot and a stuck uninterruptible member were not reproduced on the host.
* Production/staging inspection, activation, the coordinator, start orchestration, automatic attestation, migration/cutover
  and RB-1 remain outside current authority.

## 10. Conclusion

*(Written for the first remediation; the Fifth review remediation return supersedes its suite figures and host statements.)*

All five findings are corrected, and the accepted topology, SA-2 vector, role semantics, BS-3 and authorization policy are unchanged.

* **Installer.** Upgrade and removal now restore and then verify; whatever cannot be restored or confirmed is the distinct `recovery-incomplete` (15), proven by 21 tests that fail on the reviewed code, by the existing successful-recovery paths and by the exact-path host rehearsal (rows 8b/8c). The one restore failure that cannot be injected race-free on the host, failure to write the restored bytes, is covered only by deterministic tests (row 8d).
* **Sudo.** The verifier accepts exactly run-as `root`, tag `NOPASSWD` and the fixed argv; real `verify`/`install` accepted the exact rule and refused six wider variants on `sudo-rs`.
* **Evidence.** All suites ran on the final tree on `oracle-test`: focused 3162 passed/2 skipped; root 196 passed/6 skipped; bot at its accepted baseline; web 1 baseline failure (reproduced on pristine `HEAD`) with the 80 expected skips; Node 171 passed.
* **Decision input.** §5 now states the corrected lifecycle. My recommendation is A′ (accept the residual only with the §5.1 monitoring condition, which does not exist today and must be built, owned and tested before activation); Peter decides, and B or C remain available if monitoring ever fires.
* **Not done and not claimed:** no production or staging access, no commit or push, no acceptance, no risk decision, no activation.

**Recommendation:** independent Codex re-review of this exact tree (installer, its tests, runbook §8b, handback §§0, 5, 6), then Peter's decision on the residual risk and monitoring condition. Open gates: the §6 read-only production inspection, F-1 to F-3, the sudo `Defaults` premise and a separate activation instruction. After the suites finished I edited only this handback (figures and conclusion) and the current-state records; no executable instruction or code changed.
