# Claude remediation R2 — close the Ubuntu 26.04 / PostgreSQL 18 upgrade findings

> **Correction, 2026-11-07.** Section 1 ("Repair and prove the canonical SSH
> route") rests on a false premise. The `nobody:nogroup` ownership is how every
> root-owned path appears inside the sandboxed agent session's user namespace;
> unsandboxed, the paths are `root:root` with the documented modes and ordinary
> `ssh oracle-test` exits 0. No production ownership repair is needed or
> authorized, and the production-repair authority in "Authority and safety
> boundary" item 1 was not used. The text below is kept unchanged as the
> assignment as written; the rest of the assignment continues unsandboxed over
> the ordinary route.

Peter requested this bounded remediation on 2026-11-07 after independent Codex
review of the production-upgrade handback. Production already runs Ubuntu
26.04.1, Ubuntu Python 3.14.4 and Ubuntu PostgreSQL 18.6. `oracle-test` matches
the Python/PostgreSQL baseline but its application suites are not green.

Peter's governing direction is explicit: before the platform begins production
use, bring its supported operating system, database, runtimes, dependencies and
related infrastructure up to date rather than activating on a superseded
baseline. That direction approves the completed PostgreSQL 16-to-18 migration
and retirement of the old cluster. It does not waive backup, restore,
compatibility, observation, safety or independent-review evidence.

## Authority and safety boundary

Peter's delivery of this prompt authorizes:

1. one bounded production repair of the system OpenSSH **client** configuration
   ownership described below, using an already supplied sudo capability;
2. secret-safe, read-only production checks needed to verify that repair,
   record the missing backup metadata, review package/conffile residuals and
   perform the final 30-minute service observation; and
3. unrestricted repository and disposable-host remediation/testing under the
   standing `oracle-test` authority.

It does **not** authorize creating or changing sudoers/Polkit/account policy;
reading secrets, player records, process environments or process arguments;
changing application data or schema; restoring a production dump; changing an
application connection; starting `freedom-web`; restarting an application or
database service; rebooting production; enabling or changing an APT source;
installing/removing/upgrading a production package; deleting the unused
`/opt/discord-bots` virtualenvs; executing any Route 3 stage; populating block F;
committing or pushing. If the already supplied sudo capability is absent, stop
before the production repair and report it; do not recreate one.

The first production write at 15:27 UTC remains for Peter alone to disposition.
Do not infer acceptance from this prompt. The production backup hashes and
`postgres` archive size may be observed but never invented. Do not inspect or
print backup contents.

Read completely before acting:

1. `.agents/AGENTS.md`;
2. the implementation-plan reading map and §§0, 13, 14, 16, 17 and 20;
3. `docs/review/Handover information`;
4. `docs/project-management/active-delivery-plan.md`;
5. `docs/operations/disposable-test-server.md`;
6. `docs/review/production-ubuntu-26-04-upgrade-handback.md`; and
7. the first remediation prompt only for its completed scope and evidence.

Preserve unrelated working-tree changes. Historical snapshots are evidence and
must not be rewritten as current state.

## 1. Repair and prove the canonical SSH route

Codex reproduced the current defect on production:

- `/etc/ssh/ssh_config.d` is owned by `nobody:nogroup`;
- its systemd-owned target directory and
  `/usr/lib/systemd/ssh_config.d/20-systemd-ssh-proxy.conf` are owned by
  `nobody:nogroup`; and
- ordinary `ssh oracle-test` fails with `Bad owner or permissions`.

Do not bypass the system configuration with `-F`, `-o UserKnownHostsFile`, a
different client, a direct-IP exception or a copied key. First use package
metadata and non-sensitive filesystem facts to identify the owning package,
packaged path/type/mode and expected root ownership. Determine whether a
tmpfiles rule, package script, mount/id-mapping issue or another repeatable
mechanism caused the ownership to change; do not assume a one-time `chown` is a
durable fix.

If and only if the expected packaged ownership is established, restore
`root:root` ownership on the affected directories, target and symlink as
applicable without changing their contents or modes. Verify:

- the exact owner/mode/type and symlink target;
- the relevant package verification result;
- `ssh -G oracle-test` exits zero without printing sensitive configuration;
- ordinary `ssh oracle-test true` exits zero; and
- the ownership remains correct after the investigation's safe triggering
  checks. A production reboot or package reinstall is not authorized.

If ownership changes again or the cause is indeterminate, stop production work,
record the evidence and do not route around the defect.

## 2. Re-observe the disposable baseline

Only after the ordinary SSH route works, inspect `oracle-test` and update the
runbook's provisional facts where observation differs. Record non-sensitive:

- OS and kernel;
- PostgreSQL package origin/version, cluster/unit/port and client path;
- Python interpreter and virtualenv version/origin;
- Node version;
- RAM, swap and filesystem capacity;
- the documented role/database names and restricted-role attributes; and
- the retained `/var/tmp/pg16-to-18`, `/var/tmp/suite18` and Python 3.12 venv
  sizes, without deleting them.

Synchronize the exact workspace with the canonical secret-excluding command.
Never copy production data or secrets.

## 3. Remediate the exact-tree failures

Make the smallest behavior-preserving repository corrections and add regression
tests where a defect is fixed. Resolve all of these rather than converting them
to accepted skips or raising a resource limit permanently:

1. **R5 runner pin/content mismatch.** Determine why commit `bc73738` changed
   `tools/r5_runner/blocks/s04b-sync.argv` from 313 to 288 bytes. Restore the
   accepted command content if the removal was accidental; change a pin only if
   the current content is independently established as the intended contract.
   Keep the runner resource and its tests consistent.
2. **Closed production-source inventory.** Reconcile the five present but
   undeclared `tools/phase_5_0_evidence` files with the exact per-file allowlist.
   Declare intended production sources explicitly; remove a file only when it
   is demonstrably dead and no accepted behavior or evidence depends on it.
   Preserve the guard's rejection of unknown siblings.
3. **Python 3.14/libffi descriptor behavior.** Fix the H-1 artifact/entry
   boundary so a descriptor opened by Python 3.14's `ctypes`/libffi behavior
   cannot reach a role, while retaining fail-closed handling for descriptors
   that cannot be enumerated or closed. Prove the actual production invocation
   shape (`/usr/bin/python3.14 -I -S`) on `oracle-test`; do not weaken the
   no-inherited-descriptor invariant or merely alter assertions.
4. **Test-suite descriptor leak.** Find and close the roughly 970 descriptors
   leaked by the `test_rp11_*` modules. The complete bot suite must run at the
   normal soft limit without `Too many open files`. `ulimit -n 4096` may be used
   diagnostically, but is not the fix.
5. **Result variation.** Explain and eliminate the 29-versus-27 H-1 failure
   variation and reconcile the 337-versus-341 bot skip counts. Every remaining
   skip must have a stable, printed reason. Do not choose a count by preference.
6. **Concurrency observation.** Stress
   `test_snapshot_database.py::test_two_concurrent_applies_of_the_same_input_produce_one_effect`
   enough to distinguish a load-sensitive product/test defect from an isolated
   environment event. Fix it if reproduced; otherwise record the bounded
   attempts and evidence without calling it proved absent.
7. **Dependency records.** Reconcile the committed bot/web development and
   runtime requirement files with the actual tested Python 3.14 resolution.
   `requirements-web.lock` is currently older than the disposable resolved set.
   Refresh locks reproducibly within the project's declared compatibility
   ranges, record deliberate version changes and run the complete suites on the
   result. A new framework major or a change outside declared ranges is a
   separately reported decision, not a drive-by upgrade. Do not install the
   refreshed set in production under this prompt.

Do not redesign Route 3 release preparation in this assignment. If the H-1 fix
changes a release artifact identity, report that consequence; block F stays
`UNSET` and the separate redesign remains required.

## 4. Exact-tree validation

Use PostgreSQL 18 and the Unix-socket
`TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'`. Run bot and web
serially. The 2 GiB swapfile and
`-o tmp_path_retention_policy=failed` may remain as small-host accommodations.

Run focused tests for every correction, then run the full suites at the normal
descriptor limit:

1. `tests/test_*.py` with `-q -rs`;
2. `tests/web` with `-q -rs`; and
3. the Foundry Node suite.

Require zero failures and zero errors. The web database-enabled skip count must
remain 80 unless a specific intentional test change explains it. Record the bot
skip count and every reason; it must be stable across two complete bot runs at
the normal limit. After that, one raised-limit diagnostic run may confirm that
the count and outcome do not change with 4096 descriptors.

Also run `pip check`, material isolated imports, configured static checks
affected by the edits, and `git diff --check`. Preserve every exit status. A
green focused run does not substitute for the complete runs.

## 5. Bounded production evidence completion

After repository/disposable results are green, use read-only production checks
only:

- record the existing final backup set's SHA-256 values and sizes, including
  the `postgres` archive, without printing paths that expose secrets or any
  content; verify the files still pass `pg_restore --list` but do not restore
  them;
- observe the services that are already active on PostgreSQL 18 for a fresh,
  uninterrupted 30 minutes, recording stable active state/restart counts and
  allowlisted warning/error totals without log contents, player data or
  secrets; do not start `freedom-web` or restart anything;
- classify the retained `.dpkg-dist`/`.dpkg-old` files and disabled NodeSource/
  Caddy source state using package names, paths, ownership/mode and package
  metadata only. Do not print sensitive configuration and do not change any
  conffile or source under this prompt; and
- confirm temporary sudo is still revoked after the authorized repair
  capability is withdrawn by Peter. Claude must not delete or edit a sudoers
  file under this assignment.

An unhealthy production observation is a stop and escalation, not authority to
repair or restart. Disposable restore evidence does not become production
restore evidence.

## 6. Documentation and return

Update only current-state documents whose observed facts or suite procedure
changed:

- `.agents/AGENTS.md`;
- `.claude/skills/run-suites/SKILL.md`;
- `docs/operations/disposable-test-server.md`;
- `docs/project-management/status.md`;
- `docs/project-management/active-delivery-plan.md`;
- `docs/review/Handover information`;
- implementation-plan §20 when the immediate action changes; and
- the existing production-upgrade handback.

Remove provisional non-green figures only after fresh green exact-tree runs.
Retain the pre-production currency policy, the still-open 15:27 disposition and
all truthful residuals. Do not edit archived status snapshots, invent a backup
field, claim a restore that did not run, or create another prompt/review chain.

Return one concise R2 section in the existing handback containing behavior and
files changed, exact test results and skips, production repair/evidence results,
remaining risks and the next action: independent Codex re-review. Do not commit
or push.
