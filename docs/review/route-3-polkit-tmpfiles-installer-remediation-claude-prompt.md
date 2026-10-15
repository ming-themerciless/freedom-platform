# Claude remediation prompt — Route 3 Polkit tmpfiles installer cleanup

Date: 2026-10-15
Authority: baseline v1.9, the active handover and delivery plan, and the
independent Codex review of
`docs/review/route-3-polkit-tmpfiles-installer-handback.md`
Mode: one bounded remediation; implementation and full disposable-host testing;
no production or staging activation

## Assignment

Remediate the single installer failure-path finding below in the current working
tree. Add the regression first, implement the smallest safe fix, test it on
`oracle-test`, and update the existing tmpfiles handback in place. Do not return
a new plan or design package, and do not reopen the completed Route 3 role or
its earlier security remediation.

Preserve unrelated working-tree changes. Do not commit or push. Do not activate
Route 3, install anything in production or staging, or use real secrets or
player data.

## Read before editing

1. `.agents/AGENTS.md` in full.
2. `docs/implementation-plan.md`: its reading map and §§0, 9, 12 Phase 5.0,
   13, 14, 16 and 20.
3. `docs/review/Handover information` and
   `docs/project-management/active-delivery-plan.md`.
4. `docs/operations/disposable-test-server.md`.
5. `docs/review/route-3-polkit-tmpfiles-installer-claude-prompt.md` and
   `docs/review/route-3-polkit-tmpfiles-installer-handback.md`.
6. `tools/polkit_tmpfiles.py`, `tests/test_polkit_tmpfiles.py`, and
   `tests/systemd_integration/test_polkit_tmpfiles_host.py` end to end.

The prior reboot proof is valid evidence and does not need to be repeated for a
fix confined to publication cleanup and recognition. Repeat it only if the fix
changes the fragment, its destination, tmpfiles semantics, verification of boot
ordering, or the Route 3 boot-proof harness.

## Blocking finding

`install()` publishes the final name with `link(2)` and then attempts to unlink
the temporary name. The cleanup block at `tools/polkit_tmpfiles.py` currently
discards every `OSError` from that unlink and proceeds to return `installed`.

If the unlink fails after publication, both names remain as hard links to the
same inode. The command nevertheless exits 0. A later install recognizes the
public name and returns `already-installed` without noticing the alias; removal
deletes only the public name and can leave the hidden temporary file behind.
This contradicts the handback's claims that the temporary file is unlinked and
that failure/interruption removes it.

The independent reproduction used an injected `Fs.unlink_at` failure only for
the temporary name. `install()` returned `installed`, while the directory held:

```text
.freedom-blades-rp11-polkit-rules.conf.tmp-<pid>  nlink=2
freedom-blades-rp11-polkit-rules.conf             nlink=2
```

This is an operator-boundary correctness defect. Do not dismiss it because the
two names contain complete bytes or because the real package directory is
root-owned: an I/O/cleanup failure must not be promoted to success, and the
installer must not subsequently recognize a leaked alias as a clean state.

## Required remediation

- A temporary-name unlink failure after successful publication must produce a
  fixed safe diagnostic and non-zero result, never `installed`/exit 0.
- The public destination must remain either absent or a complete, fsynced,
  root-owned `0644` fragment. Do not introduce an overwrite window or permit a
  truncated accepted destination.
- Define and test a safely attributable recovery result for any complete
  same-inode temporary alias that can remain after an unlink or interruption
  failure. A later `install`, `verify`, or `remove` must not silently call that
  state clean and leave the alias invisible. It may recover it automatically
  only when attribution is exact; otherwise it must fail closed with a fixed
  diagnostic and retain the uncertain object.
- Recognition must account for link count or an equivalent exact alias check.
  A destination with an unexplained extra hard link must not be accepted as a
  normal `already-installed` fragment.
- Never scan broadly and delete by prefix alone. Never remove a different
  inode, foreign object, changed bytes, symlink, directory, FIFO, unrelated
  tmpfiles fragment, or anything under `/run` as part of this remediation.
- Preserve the existing source validation, root and directory-safety checks,
  no-overwrite `link(2)` publication property, file and directory fsyncs,
  fixed-path/no-environment interface, exit-code vocabulary, safe diagnostics,
  and absence of Polkit restart/reload/D-Bus mutations.
- Correct the existing handback's cleanup claims to match the implemented and
  tested behavior. Do not claim that cleanup is guaranteed after `SIGKILL` or
  an underlying unlink operation that cannot succeed.

Choose the smallest reversible implementation that meets these outcomes. Do
not introduce a packaging framework or a general filesystem transaction layer.

## Required regression tests

Add focused host-independent tests that, at minimum, prove:

1. temporary unlink fails after the final hard link is published: the operator
   returns the intended non-zero exit and fixed diagnostic, never success;
2. the public name, if present after that failure, has exact complete bytes,
   owner and mode and is never truncated;
3. retry, verify and removal each handle the leaked same-inode alias according
   to the selected recovery contract, with no false `already-installed` or
   `verify: ok` state;
4. an unexplained extra hard link or foreign lookalike is retained and refused,
   not removed as though it were the installer's temporary file;
5. interruption during the cleanup phase is non-success and does not broaden
   removal authority;
6. the normal first install still ends with exactly one public name and
   `st_nlink == 1`, idempotent reinstall remains unchanged, and recognized
   removal leaves no installer-owned name; and
7. all existing conflict, short-write, flush, publication-race, symlink,
   metadata, safe-output and structural no-Polkit-action tests remain green.

Extend the real-root host test only where it adds behavior that cannot be
proved through the filesystem seam. Do not plant a persistent synthetic file in
`/usr/lib/tmpfiles.d`; use its existing throwaway root-owned directory pattern.

## Disposable-host verification

Synchronize the final workspace with the exact secret-excluding command in
`docs/operations/disposable-test-server.md`. Run serially on `oracle-test`, at
minimum:

1. `tests/test_polkit_tmpfiles.py`;
2. `tests/systemd_integration/test_polkit_tmpfiles_host.py` as root with
   `FREEDOM_SYSTEMD_INTEGRATION=oracle-test`;
3. the focused `test_polkit_tmpfiles.py`, `test_rp11_*.py` and
   `test_systemd_unit_control.py` set;
4. the complete root `tests/systemd_integration` suite with the pinned Jeepney
   wheel and `/usr/sbin` in `PATH`;
5. the complete bot suite, followed serially by the complete web suite with
   PostgreSQL 16 `PATH` and exported
   `TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'`;
6. the complete Foundry Node suite and `.claude/hooks/test_guards.py`; and
7. `git diff --check`, `compileall`, and every configured formatter, linter or
   type checker, or an accurate statement that none is configured.

Report exact pass/fail/error/skip counts and compare any non-green result by
test identity with the established baseline. A targeted pass does not replace
the final-tree suite. Do not weaken or repair unrelated tests.

After root tests, confirm that the disposable host has no installer temporary
alias, fragment, RP-11 unit/process/rule/store/artifact/evidence or unexpected
`/run/polkit-1` object, and that `polkit.service` is active. Restore the host to
the clean pre-slice state without touching production or staging.

## Acceptance criteria

- No temporary cleanup failure or interruption is returned as success.
- Publication still cannot overwrite a name that appears concurrently, and an
  accepted destination can never be truncated.
- A leaked same-inode alias is either exactly recovered or visibly refused;
  retry, verify and removal never conceal it.
- Foreign and uncertain objects are retained, with removal authority no broader
  than before.
- Focused, real-root and regression suites establish no new failure relative to
  the documented baseline.
- The handback states the corrected cleanup and recovery semantics precisely.
- Production/staging remain untouched and Route 3 remains inactive there.

## Handback

Update
`docs/review/route-3-polkit-tmpfiles-installer-handback.md` in place with one
concise remediation section. Correct the superseded install/cleanup wording and
record:

- the finding and its disposition;
- the selected failure and recovery behavior;
- principal files changed;
- exact final-tree commands and results, including skips and baseline failures;
- disposable-host cleanup state;
- unchanged production gates and risks; and
- one recommendation: accept the prerequisite for continued development or
  remediate one specifically named remaining blocker.

Do not create another prompt, handback, review record, proof chain, decision
package or hash ledger.
