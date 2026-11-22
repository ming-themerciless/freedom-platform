# RP-11 entry bootstrap and InvocationID chain — G11/G12 implementation handback

**Date:** 2026-11-22 (completion and independent review; Peter's G11/G12 decisions remain dated 2026-11-21) · **Scope:** the accepted G11/G12 slice of the
[entry contract](rp11-pass-a-entry-contract-proposal.md) §0, §3 item 5, §3a. Local tests and `oracle-test` test runs only; **no SA-2 rebuild or install, no production or staging access.** **Independent Codex review of the
G11/G12 code and tests passed with no remaining blocking findings** (source review, then the fail-closed remediation and
the duplicate raw-ID test below). Independent review remains required before any SA-2 rebuild; that rebuild is not authorized.

## Delivered

**G11 — `INVOCATION_ID` as pass-level provenance (implemented in this slice by Claude: schema changes,
provenance propagation and verifier checks; tests reviewed and remediated by Codex, 2026-11-22).** `invocation_id` is validated in `GenesisRequest`, then carried in genesis, every advance state and
the stop/final state (`capture_mechanism.py`), in `HandbackBinding`, and in X-4 (`retention_check.py` compares it
against the binding and across the whole chain). `INDEX_SCHEMA` is `rp11-capture-index/3` and `BINDING_FORMAT`
`rp11-capture-binding/2`; `CaptureRecord` and `RECORD_SCHEMA` are unchanged. Tests in
`test_rp11_capture.py` and `test_rp11_retention.py` cover contract §3 item 5 (a)–(e), (h): round-trip, every
state carries the value, malformed/missing refused before any root exists, old/new schema refusal both ways,
chain-digest binding, binding/final-state mismatch stops, rechained-state inconsistency, record bytes free of the field.
Every state, binding and verifier path carries and checks the field.

**G12 — isolated bootstrap and closure (implemented in this slice by Claude: the entry bootstrap, the
build closure and the tests; Codex reviewed and remediated the tests, 2026-11-22).** New
`tests/test_rp11_entry.py` (50 tests in the final suite, after the remediation and the duplicate raw-ID regression below):

- *Closure:* `build.ENTRY_SOURCES` equals the AST import closure of
  `tools.phase_5_0_evidence.execution.capture_mechanism` in both directions (relative imports, package `__init__`
  files, `TYPE_CHECKING` and lazy imports included), disjoint from `SOURCES`, no third-party import, no launcher or
  consume-role module; the entry loads exactly that one module.
- *Shared checks:* the nine first-image/tree functions and five constants are AST-equal to `rp11_h1.py`'s; the entry
  requires uid 0 whoever runs it; it names neither `create_capture_session` nor `StreamCaptureLauncher` nor `subprocess`.
- *Refused before import (exit 77):* not root-owned (unpatched), group/other-writable file or directory, symlinked
  file or directory, FIFO, wrong owner, oversized tree, missing `lib/`. Each case plants a module that writes a
  marker and asserts the marker was never created.
- *Refused before import (exit 64):* every vector but `run --pass A`; absent, malformed, short, long, upper-case or
  empty `INVOCATION_ID`.
- *Good artifact:* run as `python -I -S` with hostile `PYTHONPATH`, `PYTHONHOME`, cwd and a planted `tools/`/`application/`
  tree: exit 69 (inert), every `tools.*`/`application.*` module loaded from the artifact's own `lib/` and a subset of
  `ENTRY_SOURCES`, `lib` appended last and once after the stdlib, no hostile or script directory on `sys.path`, an
  unnamed stray module in `lib/` never imported, no bytecode written, no file created.
- *Build:* the built artifact carries `rp11_entry.py` and every closure file byte-equal to the repository, mode 0644.

Unprivileged tests patch only the entry's required-owner and ancestor checks (to run as the test user under `/tmp`);
the owner-based refusal itself is exercised unpatched in one test.

**Raw-environment fail-closed remediation (Codex review finding).** `INVOCATION_ID` is taken only from the raw
`/proc/self/environ` block, because the normalized `os.environ` cannot show a duplicate. `_initial_environment()` returns
`None` when that file cannot be opened or read completely (no truncation, no fallback to `os.environ`), and
`first_image_controls()` then refuses with exit 64 **before** clearing the environment. The same behavior applies to the
shared role in `rp11_h1.py`. Covered by two tests in `tests/test_rp11_entry.py` (unreadable block, failed read).

**Codex second review outcome (test coverage gap, closed).** Codex found that no direct regression test passed
`invocation_id_from` a raw block with two `INVOCATION_ID` entries. Added
`test_two_raw_invocation_id_entries_are_refused_even_when_identical` to `tests/test_rp11_entry.py`, parameterized over
`rp11_entry.py` and `rp11_h1.py` and over three raw NUL-separated blocks (identical duplicate, conflicting values,
identical duplicate separated by other variables with no trailing NUL); each must return `None`, and a single well-formed
entry is still accepted. The test revealed no defect and no implementation changed.
Focused run after the addition (Python 3.14.4, repository `venv-web`, repository host, non-root): `tests/test_rp11_entry.py`
50 passed; `tests/test_rp11_entry_artifact.py` 38 passed; together 88 passed, 0 skipped. This is not a canonical-suite figure.

## Final results (post-remediation, accepted)

Python 3.14.4 repository `venv-web` throughout. Focused runs, **not** the canonical full suites. Independent Codex review of
the code and these final tests passed with no blocking findings.

| Host / identity | Run | Result |
|---|---|---|
| Local, unprivileged | `tests/test_rp11_entry.py tests/test_rp11_entry_artifact.py tests/test_rp11_h1_artifact.py tests/test_rp11_capture_unit_install.py tests/test_rp11_capture_unit_install_cleanup.py` | **520 passed, 2 skipped** (`RLIMIT_NOFILE` cannot be raised above the hard limit 524288) |
| Local, unprivileged | `tests/phase_5_0_evidence/test_rp11_capture.py tests/phase_5_0_evidence/test_rp11_retention.py tests/test_rp11_cleanup.py` | **696 passed, 0 skipped** |
| `oracle-test`, root, pytest basetemp under protected `/root` | `tests/test_rp11_entry.py tests/test_rp11_entry_artifact.py tests/test_rp11_h1_artifact.py` | **354 passed, 3 skipped** |
| `oracle-test`, unprivileged `ubuntu`, grammar-compatible `/tmp` basetemp | capture/retention/cleanup (same three files as the second row) | **696 passed, 0 skipped** |

The 3 root skips are each expected and identity-specific: the case that accepts root-owned objects, a case whose tree root
is root-owned, and the non-root marker control. They cannot run under the identity they test.

### Failed exploratory runs (disclosed, dispositioned)

- **Root pytest under the default `/tmp` basetemp:** refused by the builder's ownership protections: 2 failed, 150 errors,
  205 passed. Environmental, not a code defect; rerun with the basetemp under protected `/root` (354 passed, 3 skipped above).
- **Root capture/retention/cleanup suites under a hidden `/root/.pytest-*` basetemp:** 343 failed / 119 passed / 234
  skipped. The dot-prefixed test root violates the capture-root grammar, and root is the wrong modeled identity for those
  suites. Rerun as `ubuntu` under `/tmp`: 696 passed, 0 skipped.
- **Intermediate `oracle-test` root H1 run, exited 1 with no pytest summary:** the process exited 1 after 51 progress dots
  and printed no pytest summary, so **no failure count exists for it and none is claimed**. It was exercising the in-process
  unsafe-tree test. The synthetic tree was root-owned under `/root`, so `entry.main` went past the expected ownership
  refusal and could close pytest's own file descriptors. Disposition: the fixture now assigns the planted module uid 65534,
  so the refusal fires as intended. The final combined root run passed (354 passed, 3 skipped, table above).
- **Root fixture assumptions** found in the tests were corrected using synthetic foreign-owned files; the final root suites pass.

These supersede the earlier author-run figures below, which predate the remediation.

## Checks (author-run, before the remediation; superseded by the table above)

Python 3.14.4, repository `venv-web`, repository host, non-root, no `TEST_DATABASE_URL`:

| Run | Result |
|---|---|
| `tests/test_rp11_entry.py` | 41 passed (count at that time; the final suite has 50) |
| `tests/test_rp11_entry.py tests/test_rp11_h1_artifact.py` | 308 passed, 2 skipped (`RLIMIT_NOFILE` cannot be raised) |
| `tests/phase_5_0_evidence tests/test_rp11_*.py tests/test_provisioning_plan.py` | 6,427 passed, 234 skipped (all root/systemd/real-wheel cases, printed as "needs root … (oracle-test)") |

Two deliberate mutations were each caught and then reverted: dropping one `ENTRY_SOURCES` entry (3 failures) and
importing the closure before the tree check (16 failures). The figures in this section were taken before the raw-environment remediation; the Codex-run results above are the
post-remediation evidence. This is not the full canonical suite and is not a
figure for the submitted tree; the root-only provisioning cases and the real-wheel build were not run.

## Not done, by scope

Boundaries: the bootstrap is **inert** (a good artifact exits 69 and does nothing). No operational Pass A, no safety
sentinel (G8) amendment, no SA-2 production rebuild or install, no production or staging access, no activation; tests ran locally and on the disposable `oracle-test` host only. G1–G10 remain open. Also not done: Pass A actions; `create_capture_session` wiring and the G8 sentinel (untouched); pairing `INVOCATION_ID` with the
consume `run-start` and the real-systemd InvocationID agreement test (contract §3 item 5 (f), (g)); the non-root
service-identity branch with the real identity (G5 open); SA-2 rebuild, tree-digest change, install, activation,
probes 2/3/5/6. No production or staging state was touched.

## Risks and next action

- The entry checks the tree's modes, types and owner but not content: content integrity rests on the SA-2 tree digest,
  which the unauthorized rebuild would change.
- `tools/_codex-work/` (Codex build output, untracked) and the Codex-reported `/run/freedom-blades/laboratory.lock`
  sentinel failures were left as they are.
- `rp11_h1.py` source changed in this slice, but the installed production SA-2 artifact was **not** changed or rebuilt. Any
  future bundle use requires the separately authorized and reviewed artifact rebuild and tree-digest update.
- Next: review is done and the focused `oracle-test` runs are recorded above. Run the canonical full suites on the tree being
  submitted before quoting canonical figures; the SA-2 rebuild and all operational steps stay separately gated.
