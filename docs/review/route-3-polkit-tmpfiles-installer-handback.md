# Route 3 Polkit tmpfiles prerequisite — handback

Date: 2026-10-14 · Mode: implementation and full disposable-host testing ·
Production/staging untouched; Route 3 remains inactive there.

## Delivered

- `infra/tmpfiles.d/freedom-blades-rp11-polkit-rules.conf`: exactly
  `d /run/polkit-1 0755 root root -` and `d /run/polkit-1/rules.d 0755 root root -`.
  No rule, grant, record, evidence path or unit.
- `tools/polkit_tmpfiles.py` (`python -m tools.polkit_tmpfiles install|verify|remove`):
  non-interactive operator path; no path/env arguments; fixed diagnostics.
- Tests: `tests/test_polkit_tmpfiles.py` (74, host-independent),
  `tests/systemd_integration/test_polkit_tmpfiles_host.py` (4, real root), and two
  boot-proof tests in `test_route3_hold_host.py`
  (`FREEDOM_TMPFILES_BOOT_PROOF=1`, `FREEDOM_BOOT_POLKIT_PID`).
- Harness adaptation (no weakened assertion): the hold and stop-post fixtures now
  accept a pre-existing `/run/polkit-1` (created by the fragment) and the hold
  teardown re-creates exactly the two directories from the installed fragment.
  `tests/web/test_p3_4_static_assets.py` declares the two new production files.

## Destination choice

`/usr/lib/tmpfiles.d/freedom-blades-rp11-polkit-rules.conf` — the package-owned
layer (Ubuntu's own `polkit-tmpfiles.conf` lives there); `/etc/tmpfiles.d` is the
administrator override layer and was not used.

## Semantics

- **install**: validates the repository source first (exactly the two entries, ASCII,
  ≤4 KiB, regular non-symlink); requires root and a root-owned, non-group/other-writable
  destination directory; absent → temp file (`O_EXCL`, root 0644, written fully, fsynced)
  published with `link(2)` (fails if the name appeared), temp unlinked (a failure here is exit 13, see Remediation), directory fsynced;
  byte+owner+mode identical → `already-installed`; anything else (bytes, mode, owner,
  symlink, directory, FIFO, unexplained extra hard link) → exit 11, untouched. A failure or
  interrupt (incl. SIGTERM) before publication attempts to remove the temp (best effort; not guaranteed
  after SIGKILL or a failing unlink); a truncated accepted fragment cannot exist.
- **verify**: fragment bytes/metadata, both runtime directories (type, owner, mode), boot
  id, polkit active with a MainPID, `polkit.service` declared `After=systemd-tmpfiles-setup.service`,
  tmpfiles-setup succeeded and exited before polkit's start (monotonic), and the fragment's
  mtime precedes this boot. Only `systemctl show` is ever invoked.
- **remove**: unlinks only the recognized fragment; changed/replaced destination retained
  (exit 11); repeat is `already-absent`. Never touches `/run`; the empty directories
  disappear at the next boot.
- Exit codes: 0 ok, 2 usage, 10 refused source/host, 11 conflict/retained, 12 verify failed,
  13 I/O, 130 interrupted. No traceback or file content is printed.
- No Polkit restart/reload/D-Bus action exists in the code (AST structural test).

## Results (final tree, `oracle-test`, serial)

| Run | Result |
|---|---|
| `tests/test_polkit_tmpfiles.py` | 74 passed (superseded: 82 after remediation) |
| focused: polkit_tmpfiles + `test_rp11_*` + `test_systemd_unit_control` | 2421 passed, 18 skipped (no `RP11_LAUNCH_BUILD_ROOT`) |
| root `tests/systemd_integration`, fragment installed | 112 passed, 2 skipped (the boot-proof tests, run separately below) |
| boot-proof tests on fresh boot | 2 passed |
| bot `tests/test_*.py` (`TEST_DATABASE_URL` set) | 5911 passed, 6 failed, 39 errors, 20 skipped — the established baseline (6 F + 39 E, 20 skips, same ids: `test_r5_runner.py` ×44, `test_sheet_bootstrap_boundary.py`) |
| web `tests/web` (PG16 PATH, `TEST_DATABASE_URL`) | 2891 passed, 1 failed, 80 skipped (skip count correct). The failure, `test_every_evidence_harness_source_in_the_tree_is_declared`, names five committed `tools/phase_5_0_evidence` files from commit 4cbdf0b — not touched by this slice. An earlier run also failed `test_no_unrelated_production_files_modified` on my new files; fixed by declaring them |
| Foundry `node --test` | 171 pass, 0 fail |
| `python3 .claude/hooks/test_guards.py` | 40 cases, all passed |
| `git diff --check`, `compileall` | clean. No formatter/linter/type checker is configured |

Root suite was first 112 passed + 1 teardown error (stop-post fixture assumed the
directory absent); fixed and re-run green. I did not compare the one web failure against
a pre-slice run; it is unrelated to this slice's files by inspection only.

## Reboot proof (`oracle-test`)

- Pre-install: no fragment, no `/run/polkit-1`, polkit active (MainPID 3283080), boot
  `7f56a1be-…`; `/usr/lib/tmpfiles.d` and `/etc/tmpfiles.d` listing digests recorded.
- Conflict refusal with synthetic planted file, symlink and directory: exit 11, nothing replaced.
- Install (exit 0), second install `already-installed`, `cmp` identical to repo, `root:root 644`.
  Explicit `systemd-tmpfiles --create` made both directories `root:root 755` (no claim about
  the running polkitd). `verify` before reboot honestly failed only `fragment-predates-boot`.
- Boot `049ca408-…`: verify ok; journal: tmpfiles-setup finished at 26.56 s, polkit starting at
  33.17 s, polkitd started 37.68 s; directories present and `root:root 755`.
- Boot `ccdeec03-…` (the proof boot): tmpfiles-setup finished 26.44 s, polkit starting 31.65 s,
  polkitd started 35.75 s, MainPID 1198. With no harness directory creation and no restart,
  a real synthetic hold run: ACT activated, a real unprivileged operator `start` was authorized
  by the rule polkitd read from the boot-created `rules.d`, `hold-ended`/`st1-verified`, rule
  removed, a later start denied; a SIGKILL run recovered by CL-G (`st1-verified`, no grant
  left). MainPID stayed 1198 and both directories' inode/owner/mode were unchanged throughout.
- Fragment removed via the operator path (`removed`), host rebooted (`e2b90859-…`): no
  `/run/polkit-1`, no fragment, no RP-11 unit/process/rule/store/artifact/evidence; both tmpfiles
  listing digests equal the pre-slice values; `polkit.service` active.

## Remediation (2026-10-15): temp-unlink failure after publication

- **Finding:** `install()` ignored an unlink failure of the temporary name after `link(2)` and returned
  `installed`/0, leaving two names for one inode that later runs treated as clean. **Disposition: fixed.**
- **Behavior:** that failure (or an interrupt in cleanup) is now non-success: exit 13
  `refused: install-cleanup-failed` (130 on interrupt). The public name stays complete, 0644, root-owned.
  Recognition requires `st_nlink == 1`; if more, every extra link must be a regular file named
  `.freedom-blades-rp11-polkit-rules.conf.tmp-<digits>` in the same directory and the same inode, and
  their count must equal `nlink - 1` ("aliased"). Otherwise it is a conflict and everything is retained.
  Aliased: `install` unlinks exactly those names, fsyncs, re-inspects, reports `alias-recovered`
  (failure: exit 13 `alias-recovery-failed`); `remove` unlinks the aliases then the fragment; `verify`
  fails the new check `fragment-no-temporary-alias`. No prefix-only deletion; different-inode lookalikes,
  symlinks, FIFOs and foreign links are never touched. Temp left by a failure *before* publication
  (single link) is still only best-effort removed and is not attributed later.
- **Files:** `tools/polkit_tmpfiles.py`, `tests/test_polkit_tmpfiles.py` (+8 tests → 82). Fragment,
  destination, tmpfiles semantics and boot harness unchanged, so the reboot proof was not repeated.
  I added the tests together with the fix and did not run them against the old code.
- **Final-tree results (`oracle-test`, serial):** polkit_tmpfiles 82 passed; real-root host test 4 passed;
  focused polkit_tmpfiles + `test_rp11_*` + `test_systemd_unit_control` 2429 passed, 18 skipped
  (`RP11_LAUNCH_BUILD_ROOT`); root `tests/systemd_integration` 112 passed, 2 skipped (boot-proof);
  bot 5919 passed, 6 failed, 39 errors, 20 skipped (same baseline ids: `test_r5_runner.py` 5F+39E,
  `test_sheet_bootstrap_boundary.py` 1F); web 2891 passed, 1 failed, 80 skipped (same pre-existing
  `test_every_evidence_harness_source_in_the_tree_is_declared`); Foundry node 171 pass/0 fail;
  `.claude/hooks/test_guards.py` 40 cases passed; `git diff --check` and `compileall` clean; no formatter,
  linter or type checker configured. No OOM in dmesg.
- **Host state:** no fragment or temp alias in `/usr/lib/tmpfiles.d`, no `/run/polkit-1`, RP-11 unit,
  rule, store, artifact or evidence; `polkit.service` active. Production/staging untouched; Route 3 inactive there.
- **Recommendation:** accept the prerequisite for continued development.

## Second remediation (2026-10-15): effective-config overrides and removal races

- **Finding 1 — verify/install ignored higher-priority same-name overrides. Disposition: fixed.**
  Fixed locations, `lstat` only (never read, followed or printed): `/etc/tmpfiles.d`, `/run/tmpfiles.d`,
  `/usr/local/lib/tmpfiles.d` (the supported host's `tmpfiles.d(5)` lists all three above `/usr/lib`).
  Any object under the fragment's name — file, directory, FIFO, symlink, dangling symlink, `/dev/null`
  disabler — or a layer that cannot be shown free of one (symlinked or non-directory layer) counts. `install`
  fails closed (exit 11 `override-shadows-fragment`) before writing, before `already-installed`/`alias-recovered`,
  and again before reporting `installed`; `verify` fails the named check `no-higher-priority-override`;
  `remove` never touches an override, removes only the recognized fragment, and prints
  `note: … still shadows the fragment; left untouched` (also after `already-absent`). `/usr/lib/tmpfiles.d`
  stays the destination; nothing is copied into `/etc`.
- **Finding 2 — `remove`/alias cleanup unlinked by pathname after inspection. Disposition: fixed.**
  Every mutating action takes a bounded (5 s, polled `LOCK_NB`) `flock` on the validated root-owned destination
  directory — no lock file, released by the kernel on any exit; `verify` does not lock. Linux has no conditional
  unlink, so each deletion (fragment, attributed alias, installer temp name) is: `renameat2(RENAME_NOREPLACE)` to
  `.<fragment>.del-<pid>` → `lstat` must be the regular file with the recognized `(dev, ino)` → `unlink`. The recognized
  inode is held open from inspection, so its number cannot be reused (a first draft compared bare `(dev, ino)`;
  the replacement test caught tmpfs reusing the number). A different object is renamed back without overwriting
  and the action fails `destination-changed` (exit 11); an I/O failure or interrupt restores and re-raises;
  if it cannot be restored it stays under the quarantine name (`quarantine-retained`, exit 13) and later
  `install`/`remove` refuse (`quarantine-residue`) and `verify` fails `no-quarantine-residue` until an operator
  resolves it. Contention gives `lock-busy`/`lock-failed` (exit 13), so a stale remover cannot erase a later install.
- **Residual state, stated exactly:** a partial `remove` (aliases gone, then the fragment replaced) reports
  `destination-changed` with the replacement in place; a failed directory flush after removal reports
  `remove-failed` with the entry already gone (durability not claimed). Window not closed: a *privileged* actor
  that swaps the quarantine name itself between the `lstat` and the `unlink`. `RENAME_NOREPLACE` needs a filesystem
  that supports it (ext4, xfs, tmpfs do); otherwise the action fails closed with nothing changed.
- **Files:** `tools/polkit_tmpfiles.py`, `tests/test_polkit_tmpfiles.py` (82 → 191),
  `tests/systemd_integration/test_polkit_tmpfiles_host.py` (4 → 7; throwaway override layers and destination).
  Tests were added first and failed against the old code (102 failed, 82 old passed).
  Fragment, destination, directory semantics, boot-order checks and boot harness unchanged, so the earlier
  reboot proof was **reused**, not repeated.
- **Final-tree results (`oracle-test`, serial, after the documented rsync):** `tests/test_polkit_tmpfiles.py`
  191 passed; real-root `test_polkit_tmpfiles_host.py` 7 passed; focused polkit_tmpfiles + `test_rp11_*` +
  `test_systemd_unit_control` 2538 passed, 18 skipped (`RP11_LAUNCH_BUILD_ROOT`); root `tests/systemd_integration`
  (pinned Jeepney wheel, default root PATH) 115 passed, 2 skipped (boot-proof); bot 6028 passed, 6 failed, 39 errors,
  20 skipped (same ids as baseline: `test_r5_runner.py` 5F+39E, `test_sheet_bootstrap_boundary.py` 1F); web 2891 passed,
  1 failed, 80 skipped (same pre-existing `test_every_evidence_harness_source_in_the_tree_is_declared`); Foundry node
  171 pass/0 fail; `.claude/hooks/test_guards.py` 40 cases passed; `git diff --check` clean; files parse. No formatter,
  linter or type checker is configured. No OOM in dmesg. Local run of the 191 tests also passed.
- **Host state:** no package fragment, alias, quarantine or same-named override in any tmpfiles layer (only the
  unrelated pre-existing `freedom-blades-laboratory.conf` in `/etc/tmpfiles.d`), no `/run/polkit-1`, RP-11 unit,
  process, rule, store, artifact or evidence; `polkit.service` active; no orphan rotate-gate/caddy processes.
  Production/staging untouched; Route 3 inactive there.
- **Recommendation:** accept the prerequisite for continued development.

### Review hardening: restore interruption and durability

The follow-up review's two restore-path observations are remediated without changing the
fragment, destination, boot semantics or deletion authority. An interrupt while renaming a
quarantined replacement back now reports `quarantine-retained` with exit 130; an ordinary
restore failure reports the same residual state with exit 13. A successful restore is followed
by a directory `fsync`; failure or interruption there reports
`restore-durability-uncertain` (exit 13 or 130) with the replacement at its public name. Targeted
tests cover both failure classes and both interruption classes. The prior real-reboot proof
remains applicable. Final-tree verification on `oracle-test`: targeted installer tests 195
passed; real-root installer tests 7 passed; focused installer + `test_rp11_*` + systemd-unit
control tests 2542 passed, 18 skipped (two host `RLIMIT_NOFILE` limits and 16 tests requiring
`RP11_LAUNCH_BUILD_ROOT`); `py_compile` and `git diff --check` passed. The package fragment and
same-named override were absent from all four tmpfiles layers after testing, and
`polkit.service` was active. The unchanged bot, web, Foundry and guard suites were not rerun for
this narrow restore-only follow-up; their immediately preceding final-tree results remain above.


## Remaining production gates and risks

- Transient inspection-failure decision and final production security review (unchanged).
- Production would install via the same operator path; polkitd only sees the directory after a
  boot (or an operator-chosen restart outside Route 3). That is an activation-procedure item.
- Tests that restart Polkit as harness setup remain; they are not the role.

## Acceptance

Peter Duscha accepted this prerequisite for continued development on
2026-10-15. Production and staging activation remain unauthorized; the
transient inspection-failure decision and final production security review
remain mandatory before activation.
