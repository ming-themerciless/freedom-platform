# Claude implementation prompt — Route 3 Polkit tmpfiles prerequisite

Date: 2026-10-14
Authority: baseline v1.9, the active handover and delivery plan, Peter
Duscha's instruction to proceed to the next small implementation slice
Mode: implementation and full disposable-host testing, including a real reboot;
no production or staging activation

## Assignment

Implement the repository-managed `tmpfiles.d` prerequisite that makes
`/run/polkit-1/rules.d` exist with its accepted ownership and mode before
Polkit starts. Install it on `oracle-test`, prove it across a real reboot under
PID 1, exercise the existing Route 3 behavior without a harness-created rules
directory or Polkit restart, then return the disposable host to its prior clean
state.

This is one small installer/operations slice. Deliver running code,
configuration and tests, not another design, proof or remediation chain. Do
not revisit the completed Route 3 security remediation or its two non-blocking
validator observations. Do not implement a Package 5.0 consumer, enable a
production caller, activate Route 3 in production or staging, commit, or push.

All required root, systemd, Polkit, package, network, failure-injection and
reboot testing is authorized on `oracle-test`. Production and staging mutation,
real credentials, real player data and weakening any authorization or cleanup
control remain prohibited.

## Read before editing

1. `.agents/AGENTS.md` in full.
2. `docs/implementation-plan.md`: its reading map and §§0, 9, 12 Phase 5.0,
   13, 14, 16 and 20.
3. `docs/review/Handover information` and
   `docs/project-management/active-delivery-plan.md`.
4. `docs/operations/disposable-test-server.md`.
5. The current sections of
   `docs/review/route-3-hold-role-implementation-handback.md`.
6. `application/rp11/paths.py`, `application/rp11/hold.py`,
   `adapters/rp11/{baseline,fsops}.py`, the existing Route 3 host tests and any
   existing repository installer/provisioner patterns that are directly useful.

Historical research gates, open Q labels and superseded host restrictions are
not current prerequisites. Do not revive them. Make reversible implementation
choices, pin them with tests and record them briefly in the handback.

## Required outcome

The installed fragment must ensure that a normal boot creates these directories
before `polkit.service` starts:

```text
/run/polkit-1          root:root 0755
/run/polkit-1/rules.d  root:root 0755
```

Use ordinary `tmpfiles.d` directory entries, not a boot-time shell/Python
helper and not a service that restarts or reloads Polkit. Place the source
fragment under `infra/` in the repository and give the installed fragment a
stable, Freedom-Blades-specific name in the normal system tmpfiles location.
The fragment owns only the two directories above. It must not create a rule,
grant, activation, authority record, evidence directory or service unit.

The implementation must also provide a narrow, non-interactive operator path
to install, verify and remove this fragment. Reuse a suitable existing
installer/provisioner pattern if one fits; do not introduce a framework. Its
observable behavior must be deterministic and safely bounded:

- installation validates the repository source before changing the host;
- an absent destination is installed with the intended root ownership and
  mode;
- a byte-identical correct destination is an idempotent success;
- a conflicting file, symlink, directory or unexpected ownership/mode fails
  closed and is not overwritten;
- verification checks the installed bytes and metadata, the runtime directory
  types/ownership/modes, the current boot, active Polkit state and the boot
  ordering relevant to this prerequisite;
- removal deletes only the exact installed fragment it recognizes; a changed
  or replaced destination is retained and reported;
- removal never recursively deletes `/run/polkit-1`, `rules.d`, a Polkit rule
  or another package's content; runtime cleanup is limited to empty objects
  created by this slice, or is deferred to the disposable reboot;
- failures use fixed safe diagnostics and non-zero exit codes without emitting
  secrets, arbitrary file content or tracebacks; and
- interrupted or failed installation cannot leave a truncated accepted
  fragment.

Use a package-owned location such as `/usr/lib/tmpfiles.d` unless inspection of
the supported Ubuntu/systemd packaging convention establishes a better
repository-consistent choice. Do not silently choose `/etc/tmpfiles.d` merely
because it is convenient for a test: `/etc` is the administrator override
layer. If a different location is selected, explain the concrete reason in the
handback.

Do not claim that creating the directory on an already running host changes
what the current polkitd watches. The required proof is boot ordering: install
the fragment, reboot, and demonstrate that Polkit started with the directory
already present. The Route 3 role must continue never to restart or reload
Polkit.

## Tests

Add focused tests for the fragment and operator boundary. At minimum cover:

1. exact tmpfiles entry paths, types, uid/gid and modes;
2. source absence, malformed source and unexpected extra entry refusal;
3. first install and byte-identical idempotent reinstall;
4. conflicting destination bytes, mode, owner, symlink and non-file refusal
   without replacement;
5. short write, failed flush/rename and interruption behavior at injectable
   filesystem seams where the selected installer has them;
6. verification of missing, malformed, wrongly owned or wrongly mode-set
   runtime directories and inactive/failed Polkit;
7. exact recognized removal, changed-destination retention and repeated
   removal;
8. proof that install/remove touches no Route 3 rule, activation record,
   evidence path, service unit or unrelated tmpfiles fragment; and
9. structural checks that production code does not invoke a Polkit restart,
   reload or equivalent D-Bus action.

Keep unit tests host-independent. Put real-root behavior in the existing
`tests/systemd_integration` lane, gated by
`FREEDOM_SYSTEMD_INTEGRATION=oracle-test`, hostname `Test` and root, consistent
with the current Route 3 host tests.

## Disposable-host reboot proof

Synchronize the final workspace with the exact secret-excluding command in
`docs/operations/disposable-test-server.md`. On `oracle-test`:

1. capture a safe pre-install inventory of the fragment target, both runtime
   directories, `polkit.service` and relevant boot-order facts;
2. prove conflict refusal before the success case, using only synthetic
   disposable objects created by this run;
3. install the fragment through the delivered operator path and verify its
   exact bytes and metadata;
4. run the fragment explicitly once to prove its immediate directory result,
   while making no claim about the already-running polkitd;
5. reboot the host and wait for SSH/systemd readiness without busy-looping;
6. after reboot, record the new boot ID and prove both directories have the
   required type, owner and mode, `polkit.service` is active, and systemd's boot
   timing/order shows the tmpfiles setup completed before Polkit started;
7. without creating either directory in the test harness and without restarting
   or reloading Polkit, run a genuine synthetic Route 3 hold/stop-post/backstop
   success and cleanup path; assert the Polkit MainPID is unchanged throughout;
8. exercise one fail-closed Route 3 path and confirm the recovery owner and
   cleanup behavior remain correct;
9. run the complete root `tests/systemd_integration` suite with the pinned
   Jeepney wheel and `/usr/sbin` in `PATH` while the fragment is installed;
10. remove the fragment through the delivered operator path, reboot again if
    needed to return `/run` to its pre-slice state, and confirm no RP-11 unit,
    process, rule, grant, runtime object, evidence, test artifact or modified
    unrelated configuration remains; leave `polkit.service` active.

The reboot proof must not depend only on timestamps from the test process.
Prefer systemd unit ordering and journal/monotonic boot evidence together with
the post-boot filesystem facts. A passing role flow without a Polkit restart is
the end-to-end behavioral proof.

If SSH does not return after a reboot, use the documented host address and safe
connectivity checks. Do not mutate production or staging as a fallback.

## Regression verification

After the final code change, re-sync and run serially on `oracle-test`:

- the new focused installer/tmpfiles tests;
- the focused Route 3 artifact, unit-control, hold, cleanup, backstop, records,
  PK/SN and launch suites;
- the complete root `tests/systemd_integration` suite;
- the complete bot suite;
- the complete web suite with PostgreSQL 16 `PATH` and
  `TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'`, confirming the
  database-enabled skip count;
- the complete Foundry Node suite;
- `python3 .claude/hooks/test_guards.py`;
- `git diff --check`, `compileall`, and every configured formatter, linter or
  type checker, or an accurate statement that none is configured.

Use `/opt/freedom-blades/runtime/venv-web/bin/python` for bot and web suites and
run them serially against the shared test database. Report exact commands,
passes, failures, errors and skips. Compare non-green results by test name with
the established baseline; do not weaken tests or fix unrelated failures.

## Acceptance criteria

This slice is acceptable only when:

- a repository-owned tmpfiles fragment and operator install/verify/remove path
  are implemented and tested;
- installation is idempotent but never overwrites an unrecognized target;
- a real reboot proves the required directories exist correctly before Polkit
  starts;
- a real Route 3 success path works after that boot without harness directory
  creation or any Polkit restart/reload;
- conflict, malformed state, interruption and rollback cases fail closed;
- the final disposable host is clean and Polkit is active;
- no regression is introduced against the bot, web, Foundry or existing Route
  3 baselines; and
- production/staging remain untouched and Route 3 remains inactive there.

## Handback

Create one concise
`docs/review/route-3-polkit-tmpfiles-installer-handback.md`. Include only:

- behavior and files delivered;
- the exact fragment destination and why it is the package-owned layer;
- install/verify/remove semantics and refusal cases;
- named automated tests and exact final-tree results;
- reboot IDs and the boot-order, directory, Polkit-MainPID and real-role proof;
- final disposable-host cleanup;
- remaining production gates and risks; and
- one recommendation: accept this prerequisite for continued development or
  remediate one specifically named blocker.

Update the active handover, delivery plan and project status in place only if
the executable result supports the update. Do not create another prompt,
review record, proof chain or decision package. Do not claim production
activation readiness: the transient inspection-risk decision and final
production security review remain separate gates.
