# Claude remediation prompt — Route 3 artifact and Polkit security

Date: 2026-10-12
Authority: Peter Duscha's direct instruction, baseline v1.9, active handover and
the independent Codex review
Mode: one bounded remediation cycle, full disposable-host testing, concise
in-place handback

## Assignment

Remediate the four blocking findings from the independent review of the Route 3
manager/Polkit adapter in the current working tree. Do not return another plan
or research package. Reproduce each finding with a regression test, implement
the fixes, exercise them on `oracle-test`, and update the existing handback in
place.

This prompt authorizes implementation and every required test on the disposable
host, including root/systemd/Polkit operations, deliberately unsafe synthetic
artifact ownership and mode fixtures, wheel-replacement race injection, service
restart, and cleanup. It does **not** authorize production or staging mutation,
production activation, real secrets or player data, weakening authorization,
or implementation of the `hold`, `stop-post` and `backstop` role behavior.

Preserve unrelated working-tree changes. Do not commit or push. Keep the adapter
inactive in production configuration.

## Read before editing

1. `.agents/AGENTS.md` in full.
2. `docs/implementation-plan.md`: reading map, §§0, 12 Phase 5.0, 13, 14, 16
   and 20.
3. `docs/review/Handover information`.
4. `docs/project-management/active-delivery-plan.md`.
5. `docs/operations/disposable-test-server.md`.
6. `docs/review/route-3-manager-polkit-implementation-handback.md`.
7. The relevant implementation and tests end to end:
   `application/unit_control.py`, `adapters/systemd/`, `infra/rp11-h1/`,
   `tests/test_systemd_unit_control.py`, `tests/test_rp11_h1_artifact.py` and
   `tests/systemd_integration/test_route3_host.py`.

Historical proof/closure labels are not active gates. Make the smallest
reversible implementation choices that close the executable findings below.

## Required fixes

### 1. Reject an unsafe controlled-artifact tree before importing from it

The current entry point checks only the artifact root and `lib/` directories.
On `oracle-test`, with those directories still `root:root 0755`, changing only
`lib/rp11_roles.py` to `ubuntu:ubuntu 0644` allowed the exact root role vector
to import and run it, exiting 69 instead of refusing with 77. A user-owned file
is writable by that user even when its parent directory is not.

- Before adding `lib/` to `sys.path` or importing any artifact module, validate
  every directory and regular file that can supply executable Python code to
  this artifact, including the entry point, application boundary, adapter,
  role module, Jeepney package and relevant import metadata.
- For a root execution, require root ownership; reject group/other-writable
  objects; reject symlinks and non-regular files where a regular file is
  expected. Validate ancestors needed to prevent path replacement.
- Do not describe a check performed by Python code as protection against that
  same entry-point file having already been modified. Close that bootstrap
  condition through the build/install contract and an independently checked
  pre-execution invariant, or state and test an equally strong small design.
- Keep the accepted fixed interpreter, `-I -S`, fixed artifact path and three
  exact role vectors. Do not add a shell or a caller-selectable executable.
- Add negative tests for at least: a non-root-owned imported `.py` file; an
  owner-writable imported file owned by a non-root user; group/other-writable
  files and nested directories; symlink substitution; and an unsafe entry
  point/install result. Prove no unsafe module top-level code executes.

### 2. Make wheel verification and extraction one race-safe operation

`build.py` currently hashes `wheel.read_bytes()`, closes it, and later reopens
the path with `ZipFile`. A writable wheel path can be replaced between those
operations. Extraction also occurs after trusted sources are copied and accepts
members outside the expected Jeepney namespaces, so a replacement wheel could
overwrite trusted artifact modules.

- Open the wheel once and bind verification and extraction to the same opened
  object/file identity. Do not verify one pathname snapshot and extract a later
  one.
- Fail closed if the source changes or cannot be safely held through the
  operation. Do not copy an installed package opportunistically.
- Allow only the files/namespaces expected from the pinned Jeepney wheel,
  including its required distribution metadata and licence. A wheel member
  must never overwrite `application/`, `adapters/`, `rp11_roles.py`, the entry
  point or another trusted artifact source.
- Preserve path-traversal protection, the exact filename/version/SHA-256 pin,
  atomic destination rename, safe modes and failed-build cleanup.
- Add deterministic tests that replace or mutate the source between the hash
  and extraction stages and prove that unverified bytes cannot enter the
  artifact. Add collision tests for trusted paths and unexpected top-level
  members.

Do not rely on timing-only tests. Introduce a controlled test seam if needed so
the replacement race is deterministic.

### 3. Fail closed on malformed or oversized Polkit detail maps

`_map_reply()` currently accepts any dictionary with at most 256 entries. The
review reproduced
`_map_reply("(bba{ss})", ((True, False, {"bad": 1}),))` returning
`PolkitAuthorized()` even though the declared result is `a{ss}`.

- Require the returned details value to be an exact supported mapping shape
  whose keys and values are strings; reject booleans, bytes, integers,
  containers, subclasses or other malformed values as appropriate for the
  transport contract.
- Apply a deterministic total-volume bound, not only an entry-count bound, so
  one very large key or value cannot bypass the oversized-reply control.
- A malformed or oversized details map must return
  `ControlError("invalid-reply", ...)` even when the two booleans otherwise say
  authorized. It must never become an authorization decision.
- Add boundary tests immediately below, at, and above the selected limits and
  tests for malformed keys and values in both authorized and denied replies.

Keep the existing D-2 request shape and D-6 boolean mapping unchanged.

### 4. Revalidate `ProcessSubject` at the DI-5 boundary

The value object validates normal construction, but `PolkitAuthorityAdapter`
uses its attributes without checking its exact type or rerunning validation.
The review forced a frozen subject's `pid` to `True`; DI-5 encoded
`Variant("u", True)` and accepted an authorized reply.

- Before opening the bus, require exactly `ProcessSubject`, revalidate exact
  integer types and the D-Bus `u`/`t`/`i` ranges, and return a typed
  `ControlError("invalid-request", ...)` for invalid, subclassed, lookalike or
  forced subjects.
- Invalid subjects must make no connector or bus call and must not raise an
  uncaught `AttributeError`, `TypeError` or marshalling exception.
- Add regression cases for forced booleans, floats, strings, `None`, out-of-range
  integers, subclasses and lookalike objects for all three fields.

Do not expand this slice to pidfd. Retain the A-13.4 production-risk statement.

## Testing

Use the documented secret-excluding synchronization command. Use synthetic
fixtures only. At minimum:

1. Reproduce all four findings before the corresponding fix, then retain each
   reproduction as a regression test.
2. Run locally where dependencies permit:

   ```bash
   /opt/freedom-blades/runtime/venv-web/bin/python -m pytest -q -rfEs \
     tests/test_systemd_unit_control.py tests/test_rp11_h1_artifact.py
   ```

3. Run the same focused suite on `oracle-test`.
4. Run the opt-in real-host suite as root with the pinned wheel:

   ```bash
   sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test \
     FREEDOM_RP11_WHEEL=/tmp/rp11-wheel/jeepney-0.9.0-py3-none-any.whl \
     PATH='/usr/lib/postgresql/16/bin:/usr/bin:/bin' \
     TEST_DATABASE_URL='postgresql+psycopg:///freedom_test' \
     /opt/freedom-blades/runtime/venv-web/bin/python -m pytest -q -rfEs \
     tests/systemd_integration
   ```

5. Exercise the exact `/usr/bin/python3.14 -I -S` vectors and verify unsafe
   artifact trees refuse before any unsafe module code executes.
6. Run `.claude/hooks/test_guards.py`, `git diff --check`, `compileall`, and the
   configured static checks. If none are configured, state that accurately;
   optional scratch-tool results must be identified as such.
7. Re-sync the final tree and run the bot, web and Foundry suites serially with
   `TEST_DATABASE_URL=postgresql+psycopg:///freedom_test`. Compare exact
   failure/error/skip names and counts with the existing red baseline; do not
   repair unrelated failures or weaken structural guards to obtain green output.
8. After every root/integration run, verify there is no `rp11-*` unit, test
   process, Polkit rule, artifact or staging directory left behind and that
   `polkit.service` is active.

## Acceptance criteria

- No user-owned, group/other-writable, symlinked or otherwise unsafe executable
  artifact object is imported or executed as root.
- Artifact build/install establishes a pre-execution invariant for the entry
  point rather than relying on self-verification after unsafe code could run.
- The bytes extracted are exactly the bytes hash-verified from the pinned
  Jeepney wheel; deterministic replacement and namespace-collision tests fail
  closed.
- Malformed or oversized Polkit details never yield an authorization decision.
- DI-5 accepts only a freshly revalidated exact `ProcessSubject` and invalid
  subjects cause no bus activity.
- Focused and real-host integration tests pass with no new repository-suite
  failure and with skips reported accurately.
- The adapter remains inactive and all disposable-host state is cleaned up.

## Handback

Update `docs/review/route-3-manager-polkit-implementation-handback.md` in place.
Replace or clearly supersede its current remediation section; do not append
another long historical narrative. Include only:

- the four findings and their disposition;
- principal files changed;
- exact commands and results, including unchanged baseline failures/skips;
- artifact ownership/integrity and exact-runtime outcomes;
- cleanup confirmation;
- remaining production risks; and
- one recommendation: accept Route 3 for role implementation, remediate one
  specifically named blocker, or replace Route 3.

Do not create another review prompt, proof chain, hash ledger, activation
record, source-completion document or recursive remediation package. Do not
update current status or handover unless the active assignment actually
changes.
