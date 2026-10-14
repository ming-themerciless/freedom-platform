# Claude remediation prompt — Route 3 manager/Polkit adapter

Date: 2026-10-12
Authority: baseline v1.9, active handover and Codex implementation review
Mode: one bounded remediation cycle, full disposable-host testing, concise handback

## Assignment

Remediate the Route 3 manager/Polkit adapter in the current working tree. Do
not return another plan or research package. Inspect the implementation, add
regression tests that fail for each finding, implement the fixes, run them on
`oracle-test`, and hand back the result.

Preserve unrelated working-tree changes. Do not commit or push. Do not activate
the adapter in production or connect it to a runtime consumer in this slice.

## Read before editing

1. `.agents/AGENTS.md` in full.
2. `docs/implementation-plan.md`: reading map, §§0, 12 Phase 5.0, 13, 14, 16
   and 20.
3. `docs/review/Handover information`.
4. `docs/project-management/active-delivery-plan.md`.
5. `docs/operations/disposable-test-server.md`.
6. `docs/review/route-3-manager-polkit-implementation-handback.md`.
7. Only the technical sections needed from the historical records:
   interface-contract §§3.2–3.6 and operation-inventory rows `RT-2`, `RT-3`,
   `RT-4`, `SA1.OP.1` and `SA1.OP.2`.

Historical closure labels and documentation gates are not active. Make
reversible implementation choices and prove them with tests.

## Required fixes

### 1. Close the arbitrary root-command surface

The public `Command(path, argv)` accepted by `HolderSpec` and `BackstopSpec`
currently permits inputs such as `/bin/sh -c ...`, which systemd would execute
as root. Unit-name validation does not contain that authority.

- Remove caller-controlled executable paths and free-form argv from the public
  holder/backstop request boundary.
- Replace them with narrow typed inputs and role-specific construction for the
  accepted commands only:
  - holder `ExecStart`: `hold`;
  - holder `ExecStopPost`: `deact ... stop-post`; and
  - backstop service `ExecStart`: `backstop`.
- Derive the interpreter, controlled script/artifact path, fixed flags, role
  names and argument order internally. A caller may supply only validated
  values genuinely variable in the contract, such as activation ID, the
  required lowercase SHA-256 identity and bounded durations.
- Preserve `-I -S`. Do not introduce a shell, environment expansion, systemd
  specifier expansion, caller-selected role, arbitrary unit, arbitrary verb,
  arbitrary executable or arbitrary argument tail.
- Validate the exact resulting vectors before opening the bus. Add negative
  tests proving shell commands, alternate executables, role substitution,
  malformed hashes and extra arguments cannot be expressed through the public
  API.

If a small internal command value is useful for marshalling, keep it private to
the adapter and construct it only from the validated role-specific objects.

### 2. Make the intended `-I -S` runtime executable

The adapter currently depends on site-installed Jeepney, while the accepted
roles run with isolated Python and disabled site initialization. On
`oracle-test`, `/usr/bin/python3.12` is absent and the documented virtualenv
interpreter cannot import Jeepney under `-I -S`.

- Preserve `-I -S`; do not solve this by enabling site initialization.
- Keep using a maintained D-Bus implementation; do not write a new D-Bus wire
  protocol.
- Choose the smallest reproducible packaging arrangement that makes the D-Bus
  client importable by the exact isolated interpreter and controlled artifact
  used by the role vectors. If vendoring is selected, include the dependency's
  required files, version and licence, keep it inside the controlled artifact,
  and verify its integrity through the repository's normal dependency/artifact
  mechanism. Do not copy an installed package opportunistically from the host.
- Put the dependency in the requirement/deployment set owned by the actual
  consumer. Do not leave it classified solely as a web dependency unless the
  web runtime is genuinely the consumer.
- Add a subprocess test that invokes the exact interpreter, `-I -S`, controlled
  import path and adapter import. Run that exact test on `oracle-test`.
- Do not claim end-to-end viability unless the exact command vector executes
  successfully on the disposable host.

If preserving `-I -S` with a maintained client would require an irreversible
architecture or licensing decision, stop only that part and report the precise
choice Peter must make. Continue and complete the other fixes.

### 3. Complete the DI-3 post-completion observation

After a successful backstop creation, return diagnostic observation of:

- timer `ActiveState`;
- timer `LoadState`;
- unit `Triggers`; and
- timer `Unit`.

Use their exact D-Bus interfaces and signatures. Keep this observation
diagnostic: failure to read it must not rewrite a proven `JobRemoved ... done`
completion. Prefer a typed timer-observation value rather than widening DI-1's
eight-property public contract indiscriminately.

Add fake-transport request/decoding tests and a real-host assertion that the
returned `Triggers` and `Unit` identify the auxiliary backstop service. A
separate `systemctl show` assertion is not a substitute for checking the
adapter's returned observation.

### 4. Enforce exact DI-6 value types

`ProcessSubject` must reject booleans, floats and non-integers for `pid`,
`start_time` and `uid`, in addition to enforcing the D-Bus `u`, `t` and `i`
ranges. Add regression cases including `True`, `False`, `1.0`, `1.5`, strings
and `None` for every field.

Do not expand this remediation to pidfd. Retain the existing production-risk
statement about PID/start-time identity.

## Testing

All test levels are authorized on `oracle-test`. Use synthetic data and the
documented secret-excluding synchronization command. Do not touch production,
staging, real secrets or player data.

Run, at minimum:

1. the new regression tests locally where dependencies permit;
2. `tests/test_systemd_unit_control.py` on `oracle-test`;
3. the opt-in real systemd/Polkit integration suite as root;
4. the exact `-I -S` subprocess/import and role-vector test;
5. `.claude/hooks/test_guards.py`;
6. bot, web and Foundry suites serially with
   `TEST_DATABASE_URL=postgresql+psycopg:///freedom_test`; and
7. `git diff --check` plus the configured static checks.

Verify after integration testing that no `rp11-*` temporary unit, Polkit rule,
test process or test artifact remains.

The repository-wide bot/web baseline was already red before this adapter.
Compare exact before/after failures and do not broaden this remediation into
unrelated evidence-harness repair. Do not weaken or edit a structural guard
merely to obtain green output. A pre-existing unchanged failure may be reported
as such; every new or changed failure caused by this remediation must be fixed.

## Acceptance criteria

- The public application boundary cannot represent an arbitrary executable,
  shell command, role or argument tail.
- Exact accepted role vectors are derived from validated typed inputs.
- The adapter and maintained D-Bus client load and execute under the exact
  `-I -S` runtime tested on `oracle-test`, or a precise maintainer-only decision
  is returned for this item without blocking completion of the others.
- DI-3 returns `ActiveState`, `LoadState`, `Triggers` and `Unit` observation.
- `ProcessSubject` accepts only exact integers in the required ranges.
- All focused unit and real-host integration tests pass.
- No new repository-suite failure is introduced and existing skip counts are
  stated accurately.
- The adapter remains inactive in production configuration.

## Handback

Update `docs/review/route-3-manager-polkit-implementation-handback.md` in place
with a short remediation section, or replace it with an equally concise current
handback. Include only:

- the four findings and their disposition;
- principal files changed;
- exact commands and results, including unchanged baseline failures/skips;
- exact-runtime/import outcome;
- cleanup confirmation;
- remaining production risks; and
- one recommendation: accept Route 3, remediate a specifically named remaining
  defect, or replace it.

Do not create another proof chain, hash ledger, activation record, review
prompt, source-completion document or recursive remediation package.
