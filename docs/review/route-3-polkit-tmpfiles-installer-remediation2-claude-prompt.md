# Claude remediation prompt — Route 3 Polkit tmpfiles effective-config and removal races

Date: 2026-10-15
Authority: baseline v1.9, the active handover and delivery plan, and the
independent Codex review of the first installer remediation
Mode: one bounded remediation; implementation and full disposable-host testing;
no production or staging activation

## Assignment

Remediate the two findings below in the current working tree. Add failing
regressions first, implement the smallest safe fixes, run the relevant final-tree
tests on `oracle-test`, and update the existing installer handback in place.

Do not reopen the completed Route 3 role series or its earlier security
remediation. Do not create another design or review chain, implement a Package
5.0 consumer, activate Route 3, commit, push, or mutate production or staging.
Preserve unrelated working-tree changes and use no real secrets or player data.

## Read before editing

1. `.agents/AGENTS.md` in full.
2. `docs/implementation-plan.md`: the reading map and §§0, 9, 12 Phase 5.0,
   13, 14, 16 and 20.
3. `docs/review/Handover information`,
   `docs/project-management/active-delivery-plan.md`, and
   `docs/operations/disposable-test-server.md`.
4. `docs/review/route-3-polkit-tmpfiles-installer-claude-prompt.md`, the existing
   remediation prompt, and
   `docs/review/route-3-polkit-tmpfiles-installer-handback.md`.
5. `tools/polkit_tmpfiles.py`, `tests/test_polkit_tmpfiles.py`,
   `tests/systemd_integration/test_polkit_tmpfiles_host.py`, and the tmpfiles
   fragment end to end.
6. The installed host's `tmpfiles.d(5)` precedence rules. On the supported host,
   `/etc/tmpfiles.d` overrides same-named files in `/run/tmpfiles.d` and
   `/usr/lib/tmpfiles.d`, and `/run/tmpfiles.d` overrides `/usr/lib/tmpfiles.d`.

The previous real-reboot proof remains evidence for the unchanged fragment and
boot ordering. Repeat it only if this remediation changes the fragment, its
destination, its directory semantics, the boot-order checks, or the Route 3
boot-proof harness.

## Finding 1 — verification ignores higher-priority tmpfiles overrides

The repository fragment is installed in the correct package-owned location:

```text
/usr/lib/tmpfiles.d/freedom-blades-rp11-polkit-rules.conf
```

However, `install()` and `verify()` inspect only that pathname. Systemd ignores
it when `/etc/tmpfiles.d` or `/run/tmpfiles.d` contains the same filename; the
standard administrator-disable mechanism is a same-named symlink to `/dev/null`.
The current verifier can therefore report `verify: ok` while the package fragment
will not be applied on the next boot, provided the runtime directories happen to
exist from the current boot or another creator.

This is a false readiness result. The choice of `/usr/lib/tmpfiles.d` remains
correct and must not be changed merely to bypass the override model.

### Required behavior

- Inspect every supported higher-priority same-name location using fixed paths,
  without following a symlink or accepting a path/environment argument.
- `install` must not report `installed`, `already-installed`, or
  `alias-recovered` while a higher-priority same-name object shadows the package
  fragment. Fail closed with a fixed safe diagnostic and non-zero exit.
- `verify` must expose a named failed check for any higher-priority same-name
  object, including a regular file, directory, FIFO, symlink, dangling symlink,
  and `/dev/null` disabling symlink. It must never report `verify: ok` in that
  state even if the current runtime directories and systemd timing look correct.
- `remove` must never delete, rewrite, chmod, chown, follow, or otherwise mutate
  an administrator/runtime override. It may remove only the recognized
  package-owned fragment and its exactly attributable installer alias. Report
  the override deterministically so the operator is not told that the effective
  configuration is clean or absent when it is still shadowed.
- Preserve `/etc/tmpfiles.d` as the administrator layer. Do not copy the package
  fragment there and do not silently treat byte identity as permission to remove
  an override.
- Do not solve this by parsing unrestricted host content or printing it. Fixed
  diagnostics must not expose arbitrary paths or file contents.
- Account for the supported host's effective same-name precedence rather than
  merely checking whether the package-layer file itself is correct.

## Finding 2 — recognized removal is vulnerable to pathname replacement

`remove()` calls `_inspect()`, closes the inspected descriptor, and later calls
`unlink_at()` on the public pathname. The pathname can be replaced between those
steps. A concurrent operator invocation or privileged replacement can therefore
make `remove()` unlink an object it never recognized and still return `removed`.
Exactly attributed temporary-alias deletion has the analogous check/use gap.

The independent reproduction injected a filesystem-seam replacement immediately
before the public unlink. The hook removed the recognized name, created a foreign
file at the same name, and then allowed the original unlink to proceed. Current
`remove()` returned `removed` and the foreign replacement was gone.

### Required behavior

- A destination or alias replaced after inspection must never be deleted as the
  recognized object.
- Concurrent invocations of this operator must not allow an older `remove` to
  erase a fragment installed by a later invocation or to promote an uncertain
  result to success.
- Preserve no-overwrite publication, exact byte/owner/mode recognition,
  `st_nlink` accounting, exact alias attribution, file and directory fsyncs,
  and fixed diagnostics.
- Do not broaden deletion authority, delete by prefix, recursively remove
  anything, or touch `/run`.
- Use a bounded mechanism appropriate for the fixed root-owned package directory.
  If cooperative serialization is used, it must cover every mutating action that
  participates in the race, have safe ownership/type/mode validation, avoid an
  unbounded wait, and have deterministic recovery/removal semantics. Do not
  introduce a general installer or filesystem-transaction framework.
- Revalidate identity at the destructive boundary. Serialization among this
  tool's invocations does not by itself justify deleting a pathname that no
  longer names the inspected inode.
- If Linux does not provide a single conditional-unlink primitive for the chosen
  approach, use a safely bounded quarantine/identity-check or equivalent design
  that retains or restores an uncertain replacement and reports non-success.
  Document the selected reversible behavior briefly in code/tests and the
  existing handback.
- Interruptions and injected I/O failures at every new mutation step must remain
  fail-closed. Never claim full rollback when an underlying operation can fail;
  report the exact safe residual state instead.

## Required regression tests

Keep ordinary tests host-independent and extend the real-root lane only for
behavior that cannot be established through the filesystem seam. At minimum,
prove all of the following:

1. Same-named regular files, directories, FIFOs, symlinks, dangling symlinks and
   `/dev/null` disabling symlinks in each supported higher-priority layer prevent
   a successful install/verification result.
2. Runtime directories and otherwise passing mocked systemd facts cannot hide a
   higher-priority override from `verify`.
3. Install, verify and remove never read through, replace or delete an override;
   byte-identical overrides remain administrator-owned objects.
4. With no override, first install, idempotent reinstall, alias recovery,
   verification, exact removal and repeated removal retain their documented
   behavior.
5. Replace the public pathname immediately before its destructive step with a
   foreign regular file, symlink, directory and FIFO. Each replacement is
   retained, the action is non-success, and no arbitrary content appears in
   diagnostics.
6. Replace an attributed alias immediately before alias cleanup. The replacement
   is retained and neither install nor remove reports success for an uncertain
   partial cleanup.
7. Exercise two coordinated mutating invocations so a stale remover cannot erase
   a newly installed fragment and both results describe the actual final state.
8. Inject failures and interruption into every new lock, quarantine, rename,
   restore, unlink and directory-fsync seam that the chosen implementation adds;
   assert no foreign object is lost and no uncertain outcome returns success.
9. Existing unexplained-hard-link, foreign-lookalike, cleanup-failure,
   publication-race, short-write, source-validation, metadata, safe-output and
   no-Polkit-action tests remain green.
10. Real-root tests confirm exact ownership/modes and bounded concurrency on a
    throwaway root-owned directory. Do not plant a persistent synthetic object
    in a real tmpfiles directory.

Do not weaken a test or make it assert only a mocked method call when the
filesystem outcome can be asserted directly.

## Disposable-host verification

Synchronize the final workspace with the exact secret-excluding `rsync` command
in `docs/operations/disposable-test-server.md`. Run serially on `oracle-test`:

1. `tests/test_polkit_tmpfiles.py`;
2. `tests/systemd_integration/test_polkit_tmpfiles_host.py` as root with
   `FREEDOM_SYSTEMD_INTEGRATION=oracle-test`;
3. focused `test_polkit_tmpfiles.py`, `test_rp11_*.py`, and
   `test_systemd_unit_control.py` tests;
4. the complete root `tests/systemd_integration` suite with the pinned Jeepney
   wheel and `/usr/sbin` in `PATH`;
5. the complete bot suite, then the complete web suite, serially, using
   `/opt/freedom-blades/runtime/venv-web/bin/python`, PostgreSQL 16 `PATH`, and
   exported `TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'`;
6. the complete Foundry Node suite and `.claude/hooks/test_guards.py`; and
7. `git diff --check`, `compileall`, and each configured formatter, linter or
   type checker, or an accurate statement that none is configured.

Report exact pass/fail/error/skip counts and compare non-green results by test
identity with the established baseline. The correct database-enabled web skip
count remains 80 unless a separately explained tree change changes it. Do not
repair unrelated failures.

After root tests, confirm the disposable host contains no package fragment,
installer alias, same-named synthetic override, RP-11 unit/process/rule/store/
artifact/evidence, or unexpected `/run/polkit-1` object, and that
`polkit.service` is active. Production and staging must remain untouched.

## Acceptance criteria

- No higher-priority same-name object can be hidden behind an install or verify
  success, and no such object is mutated by this operator.
- Removal and alias recovery delete only the inode actually recognized; a
  replacement or uncertain race is retained and reported as non-success.
- Concurrent mutating invocations cannot erase a later successful installation
  or produce a false clean result.
- Existing publication, alias-attribution, fixed-diagnostic, root/directory
  safety and no-Polkit-mutation properties remain intact.
- Focused, real-root and regression suites introduce no new failure relative to
  the documented baseline.
- The existing handback accurately states effective-config, concurrency,
  interruption and residual-state semantics.
- Production/staging remain untouched and Route 3 remains inactive there.

## Handback

Update
`docs/review/route-3-polkit-tmpfiles-installer-handback.md` in place with one
concise second-remediation section. Record:

- both findings and their dispositions;
- effective-config override behavior and the selected race-safe deletion model;
- principal files changed;
- exact final-tree commands and results, including skips and baseline failures;
- whether the prior reboot proof was reused and why;
- final disposable-host cleanup state; and
- remaining production gates and risks.

Return one recommendation: accept the prerequisite for continued development,
or remediate one specifically named remaining blocker. Do not add another prompt,
review record, decision package or documentation-only proof chain.
