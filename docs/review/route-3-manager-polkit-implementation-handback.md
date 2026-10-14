# Handback — Route 3 manager/Polkit adapter

Date: 2026-10-12 · Authority: baseline v1.9, active handover · Not committed or pushed.

## Security remediation — 2026-10-12 (current)

One cycle against the [security-remediation prompt](route-3-manager-polkit-security-remediation-claude-prompt.md)
(independent Codex review). Each finding was reproduced on the unremediated code first —
F1 as root with the exact vector on `oracle-test`, F2–F4 locally — and each reproduction is
kept as a regression test.

| # | Finding | Disposition |
|---|---|---|
| 1 | Entry point checked only the artifact root and `lib/`; a user-owned `lib/rp11_roles.py` was imported and run as root (reproduced: exit 69, `runtime=ok`, planted top-level code ran) | **Fixed.** Before `lib/` reaches `sys.path` or anything is imported, `rp11_h1.py` (as root) `lstat`s every directory from the artifact up to `/` and walks the whole tree without following links: every object must be a real directory or regular file, uid 0, not group/other-writable (≤ 1000 entries); otherwise 77. It sets `dont_write_bytecode`, so root runs no longer create `__pycache__`. **Bootstrap:** the entry point's self-check is not relied on. The adapter's new `adapters/systemd/artifact.py` independently requires `/usr/bin/python3.14` and `rp11_h1.py`, and every directory above them, to be root-owned, non-symlink and not group/other-writable before DI-2/DI-3 open the bus; otherwise `error(unsafe-artifact)`, no bus call, no unit. Once true, only root can break that invariant, so it also covers a backstop that fires later. `build.py` establishes it: as root it refuses an install parent chain that is not root-only, and it checks the staged tree (owner = builder, dirs 0755, files 0644, no links) before the atomic rename. Interpreter, `-I -S`, fixed path and the three vectors are unchanged. |
| 2 | `build.py` hashed one read of the wheel path, then reopened it for extraction, after the trusted sources; any member name was accepted (reproduced: a wheel swapped after hashing put its bytes into `lib/jeepney/` and over `lib/rp11_roles.py`) | **Fixed.** The wheel is opened once (`O_NOFOLLOW`, regular file, ≤ 1 MiB), read into memory, and `fstat` identity (dev, ino, size, mtime, ctime) must be unchanged after the read; that one buffer is hashed against the pin and is the only thing unzipped. Members must lie under exactly `jeepney/` or `jeepney-0.9.0.dist-info/` (derived from the pinned filename), with plain name components, regular-file type, ≤ 256 members and ≤ 8 MiB unpacked. Every artifact file, trusted or from the wheel, is created with exclusive create (`xb`), so a duplicate or colliding path fails the build. Traversal refusal, name/version/SHA-256 pin, atomic rename, modes and failed-build cleanup are retained. Deterministic test seams: a `hashlib` stand-in replaces the wheel right after hashing, and a `_read_fd` wrapper appends to or tears the bytes. |
| 3 | `_map_reply` accepted any `dict` ≤ 256 entries, e.g. `{"bad": 1}` → `PolkitAuthorized()` (reproduced; also a single 10 MB value) | **Fixed.** Details must be exactly `dict` with exactly-`str` keys and values (no subclasses, bytes, bools, ints, containers, `None`, lone surrogates), ≤ 256 entries **and** ≤ 65,536 UTF-8 bytes of keys plus values in total; otherwise `error(invalid-reply)` whatever the booleans say. D-2 request shape and D-6 boolean mapping unchanged. |
| 4 | DI-5 used `ProcessSubject` attributes unchecked; forced `pid=True` was encoded as `Variant("u", True)` and authorized; a lookalike was authorized; a deleted field raised `AttributeError` (all reproduced) | **Fixed.** Before the connector is called, `check` requires `type(subject) is ProcessSubject` and builds a fresh `ProcessSubject` from its fields (rerunning exact-`int` and `u`/`t`/`i` range validation), encoding only the fresh values; any failure, including `AttributeError`/`TypeError`, is `error(invalid-request)` with no connector or bus call. No pidfd; A-13.4 risk retained. |

Same defect class, found while fixing 4: `_checked_holder`/`_checked_backstop` called
`spec.validate()`, which an instance attribute can shadow on a frozen dataclass. They now call
`HolderSpec.validate(spec)` / `BackstopSpec.validate(spec)` (regression test added).

**Files.** New: `adapters/systemd/artifact.py`. Changed: `adapters/systemd/polkit.py`,
`adapters/systemd/manager.py`, `infra/rp11-h1/build.py` (`SOURCES` += `artifact.py`),
`infra/rp11-h1/rp11_h1.py`, `tests/test_systemd_unit_control.py`, `tests/test_rp11_h1_artifact.py`,
`tests/systemd_integration/test_route3_host.py`, `tests/web/test_p3_4_static_assets.py`
(allowlist += `adapters/systemd/artifact.py`). No dependency, migration, configuration or
`.env.example` change.

**Tests** (`oracle-test` unless stated; serial; `TEST_DATABASE_URL=postgresql+psycopg:///freedom_test`):

* Focused, local (`/opt/freedom-blades/runtime/venv-web/bin/python -m pytest -q -rfEs tests/test_systemd_unit_control.py tests/test_rp11_h1_artifact.py`): **488 passed** (was 277). Against the unremediated code, the new tests failed for each finding.
* Focused, same command on `oracle-test`: **488 passed**.
* Real host, as root (the prompt's command, `FREEDOM_RP11_WHEEL=/tmp/rp11-wheel/jeepney-0.9.0-py3-none-any.whl`): **66 passed**, three consecutive runs (was 47). Before the fix, the new F1 cases failed (exit 69/70 with the planted code imported). One existing test (`…job_fails_is_job_result_error`) redirects the interpreter to a missing path; it now first asserts `unsafe-artifact` with no unit, then bypasses only that check to keep proving the `job-result` mapping.
* Exact runtime: the adapter's three `/usr/bin/python3.14 -I -S …/rp11_h1.py` vectors exit 69 with `runtime=ok python=3.14.4 isolated=1 no_site=1 jeepney=0.9.0`. PID 1 runs the holder `ExecStart`/`ExecStopPost` and the fired backstop (`ExecMainStatus=69`). A fresh root build is root:root throughout, dirs 0755 and files 0644, and passes both checks.
* Artifact ownership/integrity, as root with the exact vector: each case plants a module whose top-level code writes `/run/rp11-evil-marker`. **Refused with 77 and no marker** for: user-owned `rp11_roles.py` (0644 — the reviewed reproduction — and 0444), user-owned adapter and `jeepney/__init__.py`, group-writable boundary module, other-writable jeepney module, other-writable nested `jeepney/io/`, group-writable `application/`, user-owned `jeepney/` directory, user-owned `dist-info/METADATA`, symlinked module, and symlinked `adapters/` package. **Control:** the same planted module, root-owned 0644, does run (marker written, exit 69), so the absence of the marker is meaningful. **Adapter refuses** (`unsafe-artifact`, no unit) and the entry also returns 77 for: other-writable artifact directory, other-writable `/usr/local/libexec`, symlinked artifact directory, and user-owned `rp11_h1.py`. The builder refuses an other-writable install parent and leaves it empty.
* Bot `tests/test_*.py` (`-rfEs -p no:cacheprovider`): **6 failed, 4650 passed, 18 skipped, 39 errors** (41 min). Failures and errors are the unchanged baseline, by name: five `tests/test_r5_runner.py` failures plus its 39 errors (pinned-hash mismatch), and `test_sheet_bootstrap_boundary::test_the_legacy_sheets_connector_still_exposes_read_and_write`. The 18 skips are the unchanged `RP11_LAUNCH_BUILD_ROOT` toolchain skips (16) and the backup/restore grant-role skip (2). Passes rose from 4438 with the new tests.
* Web `tests/web`: **1 failed, 2891 passed, 80 skipped** (33 min). The failure is the unchanged baseline `test_p3_4_static_assets::test_every_evidence_harness_source_in_the_tree_is_declared` (undeclared `tools/phase_5_0_evidence/*` files, not Route 3). Skips are the expected 54 + 26 matrix skips.
* Foundry `node --test foundry-module/tests/*.test.mjs`: **171 tests, 171 pass, 0 fail**.
* `python3 .claude/hooks/test_guards.py`: 26 refused, 14 allowed, all pass. `git diff --check` and the same check on the untracked Route 3 files: clean. `compileall`: clean. **No formatter, linter or type checker is configured in the repository.** Optional scratch-venv tools (not repository checks): ruff 0.17.0 (E,F,W,B,UP,SIM, line 100) over the Route 3 code and tests reports only the six pre-existing UP042/UP046 `str, Enum`/`Generic` findings, left unchanged; mypy over the five changed modules: no issues.

**Cleanup** (after every root run): no `rp11-*` unit, `/etc/polkit-1/rules.d/` empty, no test
process, no `/run/rp11-*` marker or scratch directory, nothing under `/usr/local/libexec` (no
artifact, no staging, no `rp11-real-artifact`), `/usr/local/libexec` back to `root:root 0755`,
`polkit.service` active.

**Remaining production risks.**
1. PID/start-time subject identity is not race-free (A-13.4).
2. Role behaviour (`hold`, `deact … stop-post`, `backstop`) is unimplemented; the artifact refuses with 69.
3. **Build input is trusted.** A root build copies the adapter sources from the checkout it runs from. On `oracle-test` that checkout is `ubuntu`-owned, so whoever can write it controls a root-owned artifact. A production install must build from a root-owned, reviewed checkout or release. This is not enforced in code yet.
4. No upgrade or rollback procedure: `build.py` refuses an existing destination, so replacing an installed artifact means removing it first. Production install and upgrade are unexercised outside `oracle-test`.
5. The checks protect against non-root modification only. Root, the distribution interpreter and its standard library are trusted. The adapter's check and PID 1's later exec are not atomic, so the closure rests on the root-only invariant.
6. Interpreter and artifact path are fixed constants; another OS needs a code change.
7. Unchanged from the original handback: `JobRemoved` is not emitted during a manager reload (surfaces as `completion-timeout`), and typed DI-1 values versus the printed baseline (D-7/Q6-2) are still undecided.

An independent security review is still required before activation. The adapter remains
inactive; no runtime path imports it (asserted by a test).

**Recommendation: accept Route 3 for role implementation.** All four blockers are closed with
regression tests and real-host evidence. Risk 3 (a root-owned build input) must be closed
before production install; it does not block implementing the roles on `oracle-test`.

---

## Prior remediation — 2026-10-12 (superseded)

Superseded by the section above for tests, cleanup, risks and recommendation; its
dispositions below still stand. One cycle against the
[remediation prompt](route-3-manager-polkit-remediation-claude-prompt.md).

| # | Finding | Disposition |
|---|---|---|
| 1 | `Command(path, argv)` let a caller run `/bin/sh -c …` as root | **Fixed.** `Command` removed. `HolderSpec`/`BackstopSpec` take only `activation_id`, `artifact_sha256` (lowercase SHA-256) and bounded durations. The adapter builds the three accepted vectors privately (`/usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py` + `hold ⟨id⟩ ⟨a2⟩` / `deact ⟨id⟩ ⟨a2⟩ stop-post` / `backstop ⟨id⟩ ⟨a2⟩`), revalidates the spec (exact type, forced fields) and checks each complete vector before opening the bus. |
| 2 | jeepney not importable under `-I -S`; `/usr/bin/python3.12` absent | **Fixed.** Interpreter is `/usr/bin/python3.14` (root-owned distribution interpreter on Ubuntu 26.04; accepted by Peter 2026-10-12). jeepney moved out of the web set into the artifact's own set `infra/rp11-h1/requirements.{txt,lock}` (wheel pinned by name and SHA-256). `infra/rp11-h1/build.py` refuses any other wheel, unpacks it (licence included) into the artifact's `lib/`, and renames the artifact into place. The entry `rp11_h1.py` appends its own `lib/` after the stdlib, refuses (77) to run as root from a non-root-owned or group/other-writable artifact, accepts only the three vectors (64 otherwise). **Role behaviour is not implemented**: `rp11_roles.py` exits 69. Tests need jeepney via `requirements-dev.txt`. |
| 3 | DI-3 returned no `Triggers`/`Unit` | **Fixed.** `create_backstop` returns `BackstopCompletion(job_path, timer, observed: TimerObservation \| None)`; `TimerObservation` = `Unit.ActiveState s`, `Unit.LoadState s`, `Unit.Triggers as`, `Timer.Unit s`. Any read failure gives `observed=None` and never changes a `done` result. DI-1's eight properties are unchanged. |
| 4 | `ProcessSubject` accepted `True`, `1.0`, `1.5` | **Fixed.** `pid`, `start_time`, `uid` must be exact `int` (bools, floats, strings, `None`, int subclasses rejected) and in the `u`/`t`/`i` ranges. pidfd not added; A-13.4 risk retained. |

**Files.** Changed: `application/unit_control.py`, `adapters/systemd/manager.py`,
`tests/test_systemd_unit_control.py`, `tests/systemd_integration/test_route3_host.py`,
`tests/web/test_p3_4_static_assets.py` (allowlist += the five `infra/rp11-h1/` files),
`requirements-dev.txt` (+`-r infra/rp11-h1/requirements.txt`); `requirements-web.{txt,lock}`
returned to their committed state (no jeepney). New: `infra/rp11-h1/{build.py,rp11_h1.py,rp11_roles.py,requirements.txt,requirements.lock}`,
`tests/test_rp11_h1_artifact.py`, `tests/systemd_integration/rp11_roles_double.py`.

Its test figures, cleanup, risks and recommendation are replaced by the current section above.

---

*Original implementation handback follows. Superseded where the remediation above differs (notably risk 2 and the jeepney dependency location).*

## Behavior delivered

A typed, inactive adapter for DI-1 … DI-6 and DI-S behind an application-owned
boundary. Nothing in a runtime path imports it (asserted by a test).

| Intent | Entry point | Notes |
|---|---|---|
| DI-1 | `read_unit` | the eight contract properties only; typed values; every failure is `error` |
| DI-2 | `create_holder` | `UnitExists` → `refused(exists)` |
| DI-3 | `create_backstop` | timer + aux service in one call; no `TimeoutStartUSec`; `UnitExists` stays `error` |
| DI-4 | `disarm_backstop` | `NoSuchUnit` → `refused(not-loaded)` |
| DI-5 | `PolkitAuthorityAdapter.check` | exact D-2 shape, flags 0; challenge → `PolkitNotAuthorized(challenge=True)` |
| DI-6 | `ProcSubjectSource.subject_for_pid` | pid + `/proc` field 22 + real uid; re-read to detect replacement; `0` rejected |
| DI-S | `stop_capture_unit` | exactly `rp11-capture-pass-a.service`; success is `stopped` |

Choices pinned by tests (all reversible):

* system bus only, via `jeepney` (pure Python, no deps); one fresh connection per
  operation, so closing it drops the `Subscribe()` and the match;
* `JobRemoved` match (narrowed by `arg2` = unit) and `Subscribe()` precede the
  mutating call; completion is matched on job path **and** unit;
* job mode `"fail"` everywhere. Observed: stopping a unit with a running start job
  gives `TransactionIsDestructive` (reported as `error`) instead of cancelling it;
* a mutating call is sent at most once; every post-send outcome that is not a proven
  `done` is `error` with `effect_not_confirmed`; the post-completion state read is
  attached as `observed` and never changes the result;
* refusals are only: `AccessDenied`/`InteractiveAuthorizationRequired` (all four
  mutations), `NoSuchUnit` (stops), `UnitExists` (DI-2), `InvalidArgs` (stops
  only). `InvalidArgs` on create stays `error` (it can follow mutation, A-05.12);
* activation ids must match `^rp11-act-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$`; DI-1 and
  the mutations accept no other unit name.

A defect the fake-transport tests could not see and the real bus found: jeepney's
local filter compares `sender` against the unique bus name, so a well-known
`sender` in the local rule never matched and every mutation ended in
`completion-timeout` despite succeeding. Fixed in `jeepney_bus.py`.

## Files

New: `application/unit_control.py`, `adapters/systemd/{__init__,bus,jeepney_bus,manager,polkit,subject}.py`,
`tests/test_systemd_unit_control.py`, `tests/systemd_integration/test_route3_host.py`.
Changed: `tests/web/test_p3_4_static_assets.py` (scope allowlist), `requirements-web.txt` (`jeepney>=0.9,<0.10`), `requirements-web.lock` (`jeepney==0.9.0`).

## Tests (`oracle-test`, serial, `TEST_DATABASE_URL` exported)

Pre-change baseline (before any of my files were synced):

* `tests/test_*.py`: 10 failed, 39 errors, 18 skipped, 4150 passed. Failures are
  unrelated and pre-existing: `tools/r5_runner` pinned-hash mismatch on
  `s04b-sync.argv` (41 lines of that error), `rotate-test-gate.sh` 30 s timeouts,
  and a test importing `config` without `DISCORD_TOKEN`.
* `tests/web`: 2 failed, 80 skipped (the documented 80), 2890 passed. The two
  failures depend on untracked files in a git tree and fail on the host's tree.
* `node --test foundry-module/tests/*.test.mjs`: 171 pass.

New tests:

* `tests/test_systemd_unit_control.py`: 172 passed locally and on the host.
  Five deliberate mutations (job mode, non-`done` accepted, a D-Bus type, Polkit
  flags, authorized+challenge) were each caught.
* `tests/systemd_integration` (real bus, systemd, Polkit; opt-in, hostname-guarded):
  39 passed, three consecutive runs plus the final run; no `rp11-*` unit or Polkit
  rule left behind. Command:
  `sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test /opt/freedom-blades/runtime/venv-web/bin/python -m pytest -q -rs tests/systemd_integration`.
  Covers success and denial (unprivileged caller refused on every mutation), invalid
  requests, active/failed/not-loaded stops, failed job, concurrent duplicates,
  timeout/lost reply/malformed reply/suppressed signal with no retry, late
  completion, `daemon-reexec` mid-stop, Polkit restart/stop, replaced and vanished
  subjects, and cleanup after a partial backstop.
* `python3 .claude/hooks/test_guards.py`: 26 refused, 14 allowed, all pass.

Final tree (re-synced, serial, `TEST_DATABASE_URL` exported):

* `tests/test_*.py`: 10 failed, 39 errors, 18 skipped, 4329 passed. Same failures
  and errors as the baseline; the +179 passes are the new contract tests and
  related collection.
* `tests/web`: **1 failed, 2891 passed, 80 skipped** (the documented 80).
  The remaining failure, `test_every_evidence_harness_source_in_the_tree_is_declared`,
  is a baseline failure. The other baseline failure
  (`test_the_discovery_enumerates_untracked_files_rather_than_directories`) now passes
  only because the new untracked directories satisfy its precondition; that is
  incidental, not a fix. The first final run also failed
  `test_no_unrelated_production_files_modified` (the repo's scope guard); I declared
  this slice with an exactly enumerated `PERMITTED_ROUTE_3_ADAPTER` allowlist in
  `tests/web/test_p3_4_static_assets.py` and reran the full web suite.
* `node --test foundry-module/tests/*.test.mjs`: 171 pass, 0 fail.
* The bot suite ran before the allowlist edit; that edit touches only a web test file.

No formatter, linter or type checker is configured in the repo. I ran ruff (E,F,W,B,UP,SIM)
and mypy (default strictness) over the new files from a scratch venv: clean after
fixes, apart from two long lines in the integration test's embedded script strings.

## Dependency, deployment, recovery effects

`jeepney==0.9.0` added to the web requirement set and installed in the host's
`venv-web`. No migration, configuration, `.env.example` or service change. The
integration tests restart `polkit.service` and run `systemctl daemon-reexec`;
disposable host only.

## Findings worth knowing

* After a lost reply the effect is genuinely indeterminate (observed both ways), so
  `effect not confirmed` is correct. The safe recovery is: look, then re-issue
  deliberately. A blind retry is refused with `exists` when the first took effect.
* A uid-0 Polkit subject is authorized for everything at flags 0 (A-13.5), so a root
  subject proves nothing about a rule; tests use an unprivileged subject.
* After `daemon-reexec` the stop still completed and `JobRemoved` still arrived in
  the one run observed; the test accepts either a confirmed stop or an unconfirmed
  error, never anything else.

## Remaining production risks

1. **PID/start-time subject identity is not race-free** (A-13.4; polkit calls it
   "known broken"). Not expanded to pidfd here.
2. **Interpreter fit.** The accepted holder design runs `python3.12 -I -S`, which
   cannot import a site-packages dependency such as jeepney. Whoever consumes this
   must either run outside `-S` or vendor the client. No consumer exists yet.
3. Adapter runs as root for DI-5 (details need uid 0); its blast radius is limited
   only by the narrow unit-name and verb validation, which is why no generic API exists.
4. `JobRemoved` is not emitted during a manager reload (A-05.8); such a case surfaces
   as `completion-timeout`, never as success. The signal buffer is bounded (1024), so
   a flood fails closed.
5. Read-only property values are typed, not the printed text of the historical baseline
   (D-7/Q6-2 still undecided).
6. No independent review has happened; this touches authorization, so one is required
   before any production activation.

## Recommendation

**Keep Route 3.** It is small, fails closed, and behaved as specified against real
systemd and Polkit. Resolve risk 2 (interpreter fit) with the first real consumer.
