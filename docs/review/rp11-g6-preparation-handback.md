# RP-11 G6 preparation handback (2026-11-26)

**Current status (2026-11-26): G6 is technically complete** at commit `2afca20`;
see [Follow-up: G6 technical completion](#follow-up-g6-technical-completion-2026-11-26).
The sections before that follow-up record the earlier preparation stage, when G6
was open, no digest was recorded and no reference build had run.

## Behavior (`infra/rp11-h1/build.py`)

* Every artifact file's digest is recorded from the bytes handed to the write.
  Before the final rename the staging tree is read back, and the build fails,
  leaving nothing, unless its files and digests are exactly that set.
* `review_inputs(tree)` reads only the built tree. From one read per file it
  derives `tree_sha256` (the `ROUTE3_SA2_TREE_SHA256` recipe),
  `capture_tool_sha256` (`rp11-capture-tool/1` over the seven sources under
  `lib/`) and the per-file list, as schema `rp11-sa2-review/1`.
* **Protected location (G6-R1).** The public `review_inputs`, `verify_review` and
  `build.py --review` fail closed unless run as root, with no `..` in the path,
  and `_install_parent_problem` (the build's install-parent contract) accepts
  every ancestor of the tree up to `/`: real directories, root-owned, not
  group/other-writable. The tree and all its objects must be root-owned. The
  ancestor check and the reading use one absolute spelling of the path. The
  content reader is the internal `_read_tree_inputs(tree, owner)`, used by
  `build` on its own staging tree and by synthetic tests; the CLI cannot reach
  it, and no option or environment variable relaxes the public check.
* It refuses an absent or linked top, links, special files, wrong owner or mode, unlistable or empty directories, bytecode, unplain names,
  files over 8 MiB, a file changing while read, and a missing capture-tool source.
* `build.py --review <dir>` prints the inputs and accepts nothing.
  Adding `--expect-tree-sha256` **and** `--expect-capture-tool-sha256` is the
  gate: exit 0 only if both match, 1 on refusal, 2 on bad usage. The expected
  values are supplied from outside; neither is stored in the repository.
* `build.py` still imports nothing from the repository, so the digest
  construction and source list are restated there; a test compares them with
  `capture_contract`.

The existing `--wheel`/`--dest` build invocation and the artifact tree layout
are unchanged; the review-only command-line form is new. No file
covered by the review manifest changed, so v38 and the capture-tool bytes are
unaffected. `build.py` itself is in the Route 3 archive pathspec: a future
release revision gets a new archive and manifest digest. Candidate digests in
older documents are historical and must not be used as expected values.

## Limits

* The gate trusts the `build.py` that runs it. A future build must run it from
  integrity-verified deployed code, not a mutable checkout.
* The review proves a protected location at the time it runs; the tree must stay
  in one between review and use. Mounts and filesystem-level changes are not
  inspected.
* Matching digests show identical bytes, not that the bytes are acceptable;
  that is the independent review. The expected values must not be copied from
  the same `--review` run they are meant to check.

## Tests

`tests/test_rp11_sa2_review.py` is new. Its artifacts are **synthetic** (stand-in
wheel, temporary directory) and close no gate. It covers: equality with the
contract's construction; tool-digest and tree-digest binding to the built bytes
(`capture_contract` and `sa2_tree_digest` as independent oracles); two identical
builds; inputs unchanged after the source copy is edited and removed; staging
tamper failing the build; the two-digest gate; unsafe trees; and the CLI.

### Results after the G6-R1 remediation

| Run | Result | Skips |
|---|---|---|
| Local, focused tests | 797 passed, 3 skipped in 16.52 s | the root-only G6 test and the two existing `RLIMIT` cases |
| `oracle-test`, unprivileged, focused tests | 797 passed, 3 skipped in 134.11 s | the same three |
| `oracle-test`, root, `tests/test_rp11_sa2_review.py` only, protected `/root` basetemp | 39 passed, 1 skipped in 5.60 s | the unsafe-temp test, because the basetemp was itself protected |

The real-root ancestor test, skipped off root, passed in the root run. The
unsafe-temp test skipped only in that run. `git diff --check` and `py_compile`
passed locally.

### Earlier results (before the remediation)

**Codex result:** the focused artifact/entry/consume/cleanup set finished **780
passed, 2 skipped** in 14.31 s. Both skips are the existing `RLIMIT_NOFILE`
cases: this environment cannot raise the soft limit above its hard limit.
`git diff --check` was clean. Nothing had run on `oracle-test` at that point.

Codex's first broader run, which also included `tests/test_route3_release_record.py`,
finished **1126 passed, 5 skipped, 1 failed** in 97.73 s. The one failure,
`test_the_read_only_verifications_also_run_the_whole_gate[S2.1]`, reproduced
alone on the unmodified Route 3 surface: its synthetic read-only verification
logged three `systemctl` read commands as mutations. The changed files neither
implement nor exercise that Route 3 path. It is disclosed, not counted as a
green broader run and not changed in this slice.

The focused command:

```text
venv-web/bin/python -m pytest -q -rs tests/test_rp11_sa2_review.py \
  tests/test_rp11_h1_artifact.py tests/test_rp11_entry_artifact.py \
  tests/test_rp11_entry.py tests/test_route3_release_record.py \
  tests/test_rp11_consume.py tests/test_rp11_cleanup.py
```

The only root run recorded against this change is
`tests/test_rp11_sa2_review.py`. No root run of the other artifact and systemd
paths that call `build.py` is recorded.

## Independent review (Codex, first cycle)

**Blocking finding G6-R1.** Public `review_inputs`, `verify_review` and
`build.py --review` verify the artifact root and descendants but do not verify
the artifact's ancestor chain. A root-owned `0755` tree reached through a
group/other-writable parent can be replaced as a whole between path-based
checks. The future integrity gate must require a root-run review of a
root-owned tree through a real, root-owned, non-group/other-writable ancestor
chain (the existing install-parent contract is suitable), while keeping any
non-root synthetic bypass internal to build/tests and unavailable from the
public CLI. Tests must prove non-root and unsafe-parent refusal.

**Status: remediated; Codex re-review clear.** Codex independently reviewed the
remediation below and found no remaining blocking source finding.

## G6-R1 remediation (Claude Code)

Changed `infra/rp11-h1/build.py` (above) and `tests/test_rp11_sa2_review.py`.
Existing digest construction, source lists, file modes and layout are unchanged.
Digest and content tests, the gate and CLI tests now use the internal reader
(the gate and CLI tests substitute it for the public function through a
fixture, a test seam only). New tests call the public functions and CLI forms:
non-root refusal; the ancestor check runs before any read (spy on
`_install_parent_problem`); a fully protected simulated chain accepted;
group-writable, other-writable and non-root-owned ancestors at three levels
refused; a symlinked ancestor and `..` refused; a non-root-owned top,
directory or file refused; a real unprotected temp directory refused; and a
root-only test over a real `/root` chain.

Verification results are under Tests.

## Next

On 2026-11-26 Peter authorized continuous completion of the following, including
publication and the `oracle-test` reference builds and their review, without
installation:

1. Publication: commit and publish the reviewed tree.
2. Then, on `oracle-test` only, acquire the published commit, and with the pinned
   jeepney wheel run two SA-2 reference builds into new scratch directories, run
   `build.py --review` on both, and record `tree_sha256` and
   `capture_tool_sha256` for independent review. No install.

That authorization does not cover installation, a production build, A-2/AUTH,
`run_pass_a`, any service or activation, or staging or production. G6 closes
only when the independent review of those inputs is accepted; G9 and G10 remain
separate.

## Follow-up: G6 technical completion (2026-11-26)

Supersedes the statements above that G6 is open or that no digest is recorded.
Results were supplied with the documentation instruction and not re-observed by
the recorder.

**Publication and acquisition.** Commit
`2afca2098625a3e09b05d3f51918c82ccebeb543` was published to canonical
`docs/platform-plan` (`ls-remote` matched). `oracle-test`
`/opt/freedom-blades/rp11-source` fetched it cleanly and detached at it from
`575218e`; `git fsck` clean.

**Reference builds.** Two root-owned, protected, non-installing builds under
`/root/rp11-g6-ref-2afca20/a` and `/b`, with pinned wheel `jeepney-0.9.0`, sha256
`97e5714520c16fc0a45695e5365a2e11b81ea79bba796e26f9f1d178cb182683`.
The trees were byte-identical, 97 files. Public review and cross-gate passed for
both. Each value below was independently derived and matched on both builds.

| Input | Value |
|---|---|
| `tree_sha256` (shell derivation) | `824c973907f9b954651973796bdc37633cb7fa931a1a56cd9aca1e66e62bdaca` |
| `capture_tool_sha256` (`capture_contract` derivation) | `f831d38c884822cd261b2da2c99da3d4958474d21eee2691b3e5e08028ea5134` |

**Review.** Codex review has no blocking finding; G6-R1 was remediated.

**Suites** (`oracle-test`; canonical suites at the exact commit, run serially):

| Run | Result |
|---|---|
| Canonical bot | 8487 passed, 281 skipped, 6 warnings, 2329.59 s |
| Canonical web, with `TEST_DATABASE_URL` | 2894 passed, 80 skipped, 1137 warnings, 1086.05 s |
| Foundry Node | 171 passed, 0 failed, 0 skipped, 7076.51276 ms |
| Root, G6 module | 39 passed, 1 skipped |
| Unprivileged, focused | 797 passed, 3 skipped |

Skip dispositions:

* **Canonical bot, 281:** the documented unprivileged root/ownership/provisioning
  and role-grant gates, the unprovisioned `RP11_LAUNCH_BUILD_ROOT`, two `RLIMIT`
  cases, two opt-in measurement cases, plus the new real-root G6 case.
* **Canonical web, 80:** permitted matrix cells, covered by the per-route success
  tests.
* **Root G6 module, 1:** the unsafe-temp case, skipped because the basetemp was
  protected.
* **Unprivileged focused, 3:** the real-root G6 case and two `RLIMIT` cases.

The earlier
broader local run that included `tests/test_route3_release_record.py`
(1126 passed, 5 skipped, **1 failed**; see Earlier results) stays disclosed as
recorded; this follow-up does not change its disposition.

**Binding.** The evidence is tied to implementation commit `2afca20`. The
documentation-only successor that records it changes no SA-2 input bytes. The
Limits section above still applies.

**Remaining gates:** G9 (A-6), G10 (A-2/AUTH) and the actual `run_pass_a`. G1 is
accepted for review only. No install, A-2/AUTH, `run_pass_a`, service action or
activation, staging or production action occurred or is authorized.
