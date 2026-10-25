# Executor supervisor — provisioning runbook (Route 3 executor OC)

**Status: accepted on 2026-10-22 for continued non-production development as
part of the cumulative executor OC R6 candidate. Nothing in this runbook has
been run on production or staging, and following it does not authorize
activation.** Activation is a separate, explicit operator action behind its own
review (see the final review and acceptance in
`docs/review/route-3-executor-oc-implementation-handback.md`).

The 2026-10-22
[`Route 3 production-readiness assignment`](../review/route-3-production-readiness-claude-prompt.md)
required this lifecycle to be rehearsed at the real fixed paths with a
root-owned deployment on `oracle-test`; it was, with no bind mount (see the
[readiness handback](../review/route-3-production-readiness-handback.md)). Peter
accepted the cumulative readiness candidate for continued non-production
development on 2026-10-24. That acceptance does not authorize use of this
runbook on production or staging. On 2026-10-25 Peter selected Route 3 only as
a bounded, attended migration/cutover evidence facility. Each activation and
any use of this runbook still require separate explicit authority; recurring,
unattended and general-maintenance use are outside the decision.

Peter separately authorized the §6 read-only production inspection on
2026-10-25. It returned **NO-GO** before this runbook: the production host does
not have the required Python 3.14, account, Route 3 artifacts/units/runtime
paths or tmpfiles prerequisite, and its live checkout/Python 3.12 venv are not
the required root-owned trust roots. Root-only sudoers and private Polkit
checks remain incomplete. That inspection authority does not authorize any
command in this runbook that changes state.

Scope: the administrator-provisioned prerequisites that `tools/executor_supervisor_install.py` *verifies and never
edits*, then the install, verification, upgrade, rollback and removal of the supervisor **system service**. The
persistent supervisor is a root-owned system unit that runs as the unprivileged `freedom-executor` account; the account's
lingering systemd *user* manager owns only the separate transient per-invocation services. Every step below was exercised
on the disposable `oracle-test` host against a root-owned test package (the fifth-remediation proof, repeated for the sixth correction, in
`tests/systemd_integration/test_executor_package_host.py` and the reboot proof in `test_executor_reboot_host.py`); the
production values called out as "production-specific" were not.

## 0. Fixed facts (nothing here is configurable)

| Item | Value |
|---|---|
| Account | `freedom-executor` (non-root, non-login shell, owned home, lingering, primary group `freedom-executor`) |
| Unit (installed by the tool) | `/etc/systemd/system/freedom-blades-executor-supervisor.service`, root-owned `0644`, `User=freedom-executor`, `Group=freedom-executor`, enabled in the **system** manager only (`multi-user.target.wants`), not started by install |
| Interpreter flags | `/opt/freedom-blades/runtime/venv-web/bin/python -E -s -m adapters.executor.supervisor`: `-E` ignores `PYTHONPATH`, `PYTHONHOME`, `PYTHONUSERBASE` and every other `PYTHON*` variable, and `-s` drops the account's user site; its configured environment is only `PATH=/usr/bin:/bin` (systemd may add service metadata) |
| Code root | `/opt/freedom-blades/platform` (`adapters/`, `application/` trees imported by the service) |
| Interpreter and dependencies | `/opt/freedom-blades/runtime/venv-web` (`bin/python`, `pyvenv.cfg`, `site-packages`, the pinned `jeepney` tree); trust rules in §4 |
| Only privileged vector | `sudo -n /usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py stop` |
| Socket | `/run/freedom-blades-executor/supervisor.sock` (`RuntimeDirectory=`, owned by the account, `0700`) |
| State | `/var/lib/freedom-blades-executor` (`StateDirectory=`, owned by the account, `0700`); one fixed record, `invocations/active.json` |
| Invocations | one transient `freedom-executor-stop-<nonce>.service` per admitted stop, created by the supervisor through the account's **user** manager (`/run/user/<uid>/bus`), never in the system manager |
| Member environment | minimized to `PATH=/usr/bin:/bin`: the supervisor snapshots manager variables and unsets them plus known systemd-generated names. This is defense in depth and an observed test condition, not an atomic authorization invariant |

The privileged invariant is independent of exact environment equality. The transient service can execute only the fixed
SA-2 argv above; sudoers permits only that argv; Python starts with `-I -S`; and the root-owned artifact selects `stop`
from argv before reading anything and clears the environment. A same-UID process could change the user manager's
environment between the supervisor's snapshot and `StartTransientUnit`, so deployment and review must never treat the
observed PATH-only environment as the control that makes the root transition safe.

**Trusted sudo-policy prerequisite (not mechanically verifiable by the installer).** The installer proves the command list
(`sudo -l -U`), not the rest of the host's sudo policy. The environment-independence claim holds only on a host whose
sudoers keeps sudo's default environment sanitizing for this account: no `!env_reset`, no `env_keep`/`env_check` entry that
passes `LD_*`, `PYTHON*` or `PATH`, no `SETENV` tag, no `Defaults:freedom-executor` override and no `secure_path` weakening. A
production review must confirm that by reading the effective sudoers files themselves (the `sudo-rs` on Ubuntu 26.04 does
not print a `Defaults` section in `sudo -l`); where it cannot be confirmed the vector must not be activated. The R6 handback
records a one-off disposable-host probe of the real `sudo` (hostile `PYTHON*`, `LD_*`, `BASH_ENV` and `PATH` values reach
nothing; only `HOME` and sudo's own `PATH` do); it is evidence about that host, not an installer check.

**Request-write ownership and readiness.** The executor client treats any error raised by the request write as
`HANDED_OFF` (the whole line may already be admitted, so a retry could launch SA-2 twice); only failures before the write
is attempted are `NOT_SENT`. The supervisor publishes `READY=1` only after readiness, the first recovery pass, the socket
bind/listen and the start of its serving worker; a client arriving at that instant queues in the listen backlog and is served.
If the serving worker ever stops, the service exits non-zero so systemd restarts a viable owner.

Installer exit codes: `0` ok, `2` usage, `10` prerequisite refused, `11` conflict/shadowed, `12` verify failed,
`13` I/O (a manager command that times out or cannot run is also `13` `io-error` once the earlier state is verified; `state-unavailable` and `enablement-unavailable` are `13` too: an upgrade is refused, before anything changes, when the unit's state or its `wants` link cannot be observed strictly, see below), `14` `remove` refused (`invocation-pending`, `drain-unconfirmed`, `drain-lost`), `15` `recovery-incomplete` (an
`install` upgrade or a `remove` failed **and** putting the earlier fragment/owner back could not be completed and verified: see §8b).
Diagnostics are fixed words.
Enablement is observed strictly wherever an upgrade could change anything: only a genuinely absent
`multi-user.target.wants/freedom-blades-executor-supervisor.service` means "disabled", only the expected symlink means "enabled", and an
I/O or permission error, a non-link object, a malformed link or an unexpected target is `enablement-unavailable` (13, nothing changed) before the
upgrade or `recovery-incomplete` (15) after it: inspect `ls -l` of that path as root, correct it, and rerun `install`.
The installer finds `systemctl`, `runuser` and `sudo` only in `/usr/sbin:/usr/bin:/sbin:/bin` and runs them with that
`PATH` (the caller's `PATH` is never consulted). It uses the system manager to enable, disable, reload, stop and inspect the
persistent supervisor; it talks to the account's user manager (through `runuser`) only to list transient invocation units.

## 1. Preconditions

1. Run as root on the target host. Have a second root session open before touching sudoers.
2. The SA-2 artifact (`/usr/local/libexec/freedom-blades-rp11/rp11_h1.py`) and `/usr/bin/python3.14` are installed
   through their own reviewed procedure. Without the artifact the client ends `NOT_CONFIRMED`; that is the safe outcome
   but means no stop is ever confirmed.
3. The repository revision to deploy has passed independent review and is checked out (or rsynced) at
   `/opt/freedom-blades/platform`. No `.env`, credential or key file is read or copied by any step here.

## 2. Account and lingering (administrator, once)

```
useradd --system --create-home --home-dir /home/freedom-executor \
        --shell /usr/sbin/nologin freedom-executor
loginctl enable-linger freedom-executor        # creates /var/lib/systemd/linger/freedom-executor
```

`--system` is acceptable if the host's UID policy allows a user manager for system UIDs; if `user@<uid>.service` will
not start for it, create the account as a regular non-login user instead (the tool only checks non-root, non-login
shell, owned home, and a primary group named `freedom-executor` whose gid is the account's own: the unit's `Group=`). The account must have no password and no SSH keys. Do not add it to any group that grants write
access to the code tree, `sudo`, `wheel` or `docker`.

Check: `getent passwd freedom-executor` (shell `nologin`/`false`), `getent group freedom-executor` (same gid),
`ls /var/lib/systemd/linger/freedom-executor`.

## 3. Sudoers (administrator, once, exactly one command)

Create `/etc/sudoers.d/freedom-executor-sa2` (mode `0440`, root:root) containing exactly:

```
freedom-executor ALL=(root) NOPASSWD: /usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py stop
```

Validate before relying on it: `visudo -cf /etc/sudoers.d/freedom-executor-sa2`. Then
`sudo -l -U freedom-executor` must list **one** command line, equal to the vector above, whose run-as is `root` (printed
`(root)`, or `(root : root)`) and whose only tag is `NOPASSWD`. Anything else makes the installer refuse
(`sudoers-not-exact`): extra commands, wildcards, `ALL`, a second drop-in granting more, a stale drop-in, **any wider
run-as** (`(ALL)`, `(ALL : ALL)`, `(root : ALL)`, another user or group, a list, `#uid`, `%group`), or an additional
tag (`SETENV`, `NOEXEC`, `LOG_OUTPUT`, `PASSWD` …). Do not widen this entry to make a test pass. The run-as and tag check
applies to the printed grant; the `Defaults` section, which `sudo -l` does not print under `sudo-rs`, is still the production
review's to read (§9 and the readiness checklist).

## 4. Root-owned runtime

The service imports code from a tree the account must not be able to modify. `install`, `verify` and `verify-ready`
**enforce** the following and refuse (exit `10`) at the first violation; nothing below is a reminder only.

Every directory and file traversed must be owned by root (never by the account), must not be writable by group or
others, and must be a directory or regular file (a symlink only where stated):

1. **Path chain.** `/` and every directory down to `/opt/freedom-blades/platform`, and down to
   `/opt/freedom-blades/runtime/venv-web`. A symlink in these chains is allowed only if it is root-owned and its
   complete target chain passes the same checks (absolute targets are read within the filesystem root; a target that
   escapes upward, a loop, or more than 16 links is refused).
2. **Imported code.** The whole `adapters/` and `application/` trees, walked by descriptor without following anything.
   **Any symlink anywhere in either tree is refused** (`code-symlink`); a socket, FIFO or device is refused
   (`code-untrusted`). Every enumeration is bounded **while it iterates**: one shared budget of 20,000 entries (and depth 32)
   covers the trees, the interpreter's `lib/python3*` siblings, the venv `lib` directory and `site-packages`; each directory
   iterator is drawn one entry at a time against that budget, so the entry that overflows it is the last one ever read and
   nothing is gathered, sorted or sampled beyond it. A tree beyond the bound is refused with `code-too-large`.
3. **Interpreter.** `venv-web/pyvenv.cfg` (regular file, no link, at most 8 KiB, with an absolute `home =`),
   `venv-web/bin/python` with its **complete link chain and every target**, the `home` directory and its sibling
   `lib/python3*` directories (the directories themselves, not their contents).
4. **Dependencies.** Exactly one `venv-web/lib/python3.*`; its `site-packages` directory and every top-level entry in
   it (these include the `.pth` files that run at interpreter start; links are refused); and the **whole `jeepney`
   tree** (required to exist; links refused). Other installed packages are not imported by the service and are not
   walked, but their top-level entries are still checked as above.
5. **The service fragment and its manager locations.** `infra/executor/freedom-blades-executor-supervisor.service` in the repository being
   installed: link-free path from `/`, regular file, link count 1, root-owned, not writable by group or others. It is
   read to its exact `fstat` size; a short read, early EOF or growth refuses (`source-invalid`). The installed copy is
   written with every short write completed; a write that makes no progress fails the install (`install-failed`)
   before the destination is linked, leaving nothing behind. No other system-manager location may hold or modify a unit of that
   name (`/usr/lib`, `/usr/local/lib`, `/run`, `*.control`, any `.d`/`.wants`/`.requires`): `shadowed`. A leftover
   user-service candidate (§9a) is refused as `legacy-user-service`.

Provisioning that satisfies this:

1. Create `/opt/freedom-blades/runtime` root-owned `0755`, and build the venv as root:
   `python3.14 -m venv /opt/freedom-blades/runtime/venv-web`, then install the **pinned** `jeepney` wheel (the version
   recorded in the controlled artifact set; `oracle-test` used `jeepney-0.9.0`) with `--no-index --no-deps`. No other
   package source.
2. Deploy the code with `rsync` as root *excluding* `.env*`, keys, credential JSON and `.git`, with no symlinks in
   `adapters/` or `application/` (replace any by the real file), then `chown -R root:root` and `chmod -R go-w` on the
   platform tree and the venv.
3. Production-specific: confirm the interpreter and every dependency are provisioned this way; the host proof used a
   root-owned python3.14 venv with `jeepney` bind-mounted over `/opt/freedom-blades` for the duration of the test. The
   production-readiness rehearsal instead parked the ordinary checkout and venv by rename, made `/opt/freedom-blades` and
   `/opt/freedom-blades/runtime` root-owned `0755`, and deployed a root-owned, `.git`-free copy and a root-owned
   `python3.14 -m venv` plus the pinned wheel (`pip install --no-index --no-deps`) at the real paths. A deployment copied
   from a setgid checkout keeps `2755` on its directories; the installer accepts that (no group write), but a cleaner
   deployment clears it (`chmod -R g-s`).

## 5. Install, verify, start

```
cd /opt/freedom-blades/platform
python3 -m tools.executor_supervisor_install verify          # expect: not-installed (12) before first install
python3 -m tools.executor_supervisor_install install         # expect: installed (0); does not start the service
systemctl start freedom-blades-executor-supervisor.service
python3 -m tools.executor_supervisor_install verify-ready    # expect: ready (0)
```

`install` writes the fragment root-owned `0644` in `/etc/systemd/system`, enables it in the **system** manager
(`systemctl enable`, never `--global`, never `--user`), runs `systemctl daemon-reload` and then asks the manager what it
loaded: the unit must be `LoadState=loaded` from exactly that fragment with `NeedDaemonReload=no`, or the install fails
and must have empty `DropInPaths`, `User=freedom-executor`, `Group=freedom-executor` and configured
`Environment=PATH=/usr/bin:/bin`, or the install fails (`reload-failed`; `verify` reports `manager-stale`). The filesystem
check independently refuses a same-named fragment or name-specific or dash-prefix (`freedom-blades-.service.d`) drop-in in every supported system-unit load path,
including `.control`, transient, attached and generator locations. A failed upgrade restores the previous fragment **and
verifies the restoration** (bytes on disk, loaded by the manager with no drop-in, **enablement in both directions** — a unit that was
disabled is disabled again, one that was enabled is enabled again, the link is checked — and unit state unchanged); this holds for every
failure after the fragment may have changed, including a manager command that times out, cannot run or raises an OS error, not only a
non-zero exit. If that cannot be
confirmed the result is `recovery-incomplete` (15), never a restored one (§8b). A
failed first install leaves a root-owned fragment that a rerun completes. After a reboot the system manager starts the enabled unit by itself, with no login; it retries every second
(`StartLimitIntervalSec=0`) and stays not-ready, refusing every stop, until the account's lingering user manager and its bus
answer, the first recovery pass completes, the socket is bound and the serving thread has started. Only then does the
supervisor publish `READY=1`. The manual `start` is needed only for the first activation without a reboot.

`verify` reports `not-installed` (12) whenever the installed fragment is not byte-identical to the repository fragment:
absent, an older recognized fragment awaiting `install`, or a modified one. It does not mean the file is missing.

Refusals map to fixed words: `account-missing|unsuitable|home`, `linger-off`, `sudoers-not-exact|unreadable`,
`code-writable|missing|symlink|untrusted|too-large`, `source-untrusted|invalid|missing`, `unit-dir`, `shadowed`,
`legacy-user-service`, `owner-without-fragment`, `destination-conflict`, `install-failed`, `enable-failed`, `reload-failed`, `state-unavailable`, `enablement-unavailable`, `recovery-incomplete`; `verify` adds
`not-installed`, `not-enabled`, `manager-stale`; `verify-ready` adds `manager-not-running`, `supervisor-not-ready` (not active, no
socket, or the supervisor's process is not the account's), `state-untrusted`. Fix the named prerequisite; never edit the
tool's checks.

Confirm after start: `systemctl show -p User,Group,Environment,MainPID,FragmentPath,DropInPaths,NeedDaemonReload freedom-blades-executor-supervisor.service`;
`journalctl -u freedom-blades-executor-supervisor.service` shows the supervisor ready; `ls -ld /var/lib/freedom-blades-executor
/run/freedom-blades-executor` show the account and `0700`; exactly one process runs `python -E -s -m adapters.executor.supervisor`,
as the account; `loginctl list-sessions` need not show any session for the account.

## 6. Acceptance probes (once, in a maintenance window, not during a live SA-2)

1. `sudo -u freedom-executor sudo -n /bin/true` must be refused.
2. The sudo log for the account shows only the fixed vector when the executor client exercises a stop.
3. Reboot test: leave the supervisor stopped with no records, reboot, confirm the unit is `active` without any login
   and `verify-ready` returns `ready`; `systemctl show -p ActiveEnterTimestampMonotonic` of the supervisor is later than that of
   `user@<uid>.service`.
4. No other user's manager has the unit: `systemctl --user -M <other>@ show freedom-blades-executor-supervisor.service -pLoadState`
   is `not-found`, and `find /etc/systemd/user /home -name 'freedom-blades-executor-supervisor*'` finds nothing.
5. A unit of the same name created under `~freedom-executor/.config/systemd/user` is a separate unit in the account's own
   manager; it cannot change the system supervisor's fragment, command, PID or restarts (the host proof does exactly this).
6. Exercise one stop while observing the transient member. A PATH-only `/proc/<pid>/environ` is the expected regression
   observation, but is not an authorization proof: repeat safety review against the fixed sudoers/SA-2 argv, Python
   `-I -S`, and the root-owned `stop` artifact's no-environment-read path.

## 7. Upgrade

1. Review and deploy the new revision as in §4.
2. `python3 -m tools.executor_supervisor_install verify` (still `installed`/trusted).
3. `python3 -m tools.executor_supervisor_install install`. If the unit in the repository changed, the installer
   replaces the installed fragment **atomically**, but only a root-owned `0644` regular file that carries the installer's
   `# Managed-By: tools.executor_supervisor_install` line (anything else is `destination-conflict` and is never touched), runs the
   checked `daemon-reload` and proves the manager loaded the new fragment; if it cannot, the previous fragment is put back
   and the install fails with `reload-failed`; if the previous fragment cannot be put back and confirmed, the install exits
   `recovery-incomplete` (15) and §8b applies. The running supervisor keeps its old configuration until restarted.
4. Restart: `systemctl restart freedom-blades-executor-supervisor.service`. Restart does not touch a populated invocation
   unit (it lives in the account's user manager); the recovery loop re-adopts the record. Re-run `verify-ready`.

## 8. Rollback and removal

* Rollback of code: redeploy the previous reviewed revision (§4), run `install` (which upgrades a recognized older
  fragment) and restart the supervisor.
* `python3 -m tools.executor_supervisor_install remove` does **not** infer safety from its own directory and
  `list-units` snapshots. It sends the running supervisor a root-only maintenance **drain** request over the
  supervisor socket (the socket must be owned by the account; the supervisor authenticates the maintenance peer as uid 0). The
  supervisor takes its own admission lock, closes admission **for the rest of its life**, and acknowledges only if it
  holds no ownership record, finds no damaged entry, has no adopter running and the user manager lists no
  `freedom-executor-stop-*` unit. The installer holds that connection open, re-checks the state directory and the unit
  list itself while admission is closed, confirms the connection is still alive, then stops the system service (judged by
  the manager's own `ActiveState`, not an exit code), re-checks that nothing appeared across the stop, disables the unit,
  unlinks only a fragment it recognizes, runs the checked `daemon-reload` and proves the manager no longer holds the unit
  (`LoadState=not-found`). A second `remove` after success is a no-op that succeeds. If no supervisor is listening, removal
  proceeds only when the unit is `inactive` and the state directory is empty (nothing can then be admitting); a unit that is
  starting, restarting or in an unknown state is refused (`drain-unconfirmed`; with the user manager down the unit keeps
  restarting by design: `systemctl stop` it yourself, then `remove`).
* **A running supervisor whose fragment is absent is refused (`11 owner-without-fragment`) before anything is drained, stopped
  or reloaded.** The manager can still hold and run a loaded copy after the fragment and enablement are gone; that copy would
  not survive a reboot, so removing it could lose the only owner. The same word covers a unit that is not `inactive`, or a
  supervisor that still answers on the socket while the manager says `inactive`. Operator response: run `install` (it writes the
  fragment, enables it and reloads, and leaves the running supervisor alone), then `remove` as usual. With the fragment and the
  loaded unit both genuinely absent, `remove` is still an idempotent no-op that succeeds. If an owner somehow appears after that
  check and removal then fails, the result is always `recovery-incomplete` (15): a drained or stopped supervisor with no
  fragment cannot be given a persistent owner by the tool.
* **Quiesce the executor before `remove`.** Every refusal restarts the supervisor, which drops the connection of any request
  in flight (the client then reports `HANDED_OFF`; the invocation is still owned and settled once). The production-readiness
  load rehearsal (three clients re-admitting back to back) was refused six times in a row (`invocation-pending`) with 35 SA-2
  launches for 35 admitted requests (30 answered, 5 `HANDED_OFF`); `remove` succeeded at once when the clients stopped.
* Fail-closed refusals and failures, each leaving a **persistent owner when the restoration can be completed and is
  verified**: the fragment present (restored from the identical bytes if it had already been unlinked), enabled, loaded by
  the manager, and the supervisor **restarted** and reported running (a drained supervisor refuses every stop until
  restarted). The installer checks each of those after the restoration; when any of them cannot be established the result is
  `15 recovery-incomplete` instead of the original word (also when the restoration itself raises or times out), and §8b is the operator's response: `14 invocation-pending` (a record, unit or in-flight invocation);
  `14 drain-unconfirmed` (no or malformed answer, wrong peer, lost reply, unreadable manager state, a starting
  supervisor); `14 drain-lost` (the connection dropped between acknowledgment and stop, i.e. the supervisor
  restarted); `13 stop-failed`, `disable-failed`, `remove-failed`, `reload-failed` (including the reload after the unlink). A
  restarted supervisor re-adopts any record, so retrying later is safe. Do not delete records by hand: an ambiguous
  same-boot `start-sent` record (the `StartTransientUnit` call may be queued) blocks until reboot by design, and removal
  stays refused while it exists.
* `remove` leaves the (empty) `/var/lib/freedom-blades-executor` and `/run/freedom-blades-executor` directories that systemd keeps; deleting state is a separate administrator decision.
* `remove` never touches the account, lingering or sudoers. Revoking those is a separate administrator action
  (delete the sudoers drop-in first, then `loginctl disable-linger`, then **wait until `systemctl is-active user@<uid>.service`
  reports `inactive`** — it stays `deactivating` for several seconds and `userdel` refuses while the manager's process
  runs — then `userdel -r`) and should follow a successful `remove`. A refused `remove` must be resolved first.

## 8b. `recovery-incomplete` (exit 15): operator response

`recovery-incomplete` means an `install` upgrade or a `remove` failed and the attempt to put the earlier fragment and owner
back **did not complete or could not be confirmed**. It replaces the original failure word; it never means "restored". It
does not mean an invocation was abandoned: the tool reaches the point of changing anything only after the drain and the
installer's own emptiness checks, never deletes state, and `remove` stays refused (`invocation-pending`) while a record exists.
The installer never overwrites a foreign object at the fragment path and never loosens a trust check to finish.

1. Do not repeat the command blindly and do not delete anything under `/var/lib/freedom-blades-executor`.
2. Establish the state as root, read-only first:
   `ls -l /etc/systemd/system/freedom-blades-executor-supervisor.service /etc/systemd/system/multi-user.target.wants/freedom-blades-executor-supervisor.service`;
   `systemctl show freedom-blades-executor-supervisor.service -pLoadState,FragmentPath,DropInPaths,NeedDaemonReload,ActiveState,MainPID,UnitFileState`;
   `ls -l /var/lib/freedom-blades-executor/invocations`; `journalctl -u freedom-blades-executor-supervisor.service -n 50`.
3. Resolve the named cause (full filesystem, a manager command that times out, a manager that does not reload, a foreign file or drop-in at the fragment path,
   or a higher-precedence unit of the same name such as one in `/etc/systemd/system.control`). A foreign object is the
   administrator's to inspect; the tool will not touch it. The unit may be left **stopped**: after a failed removal the
   installer restarts the supervisor only when it could verify what the manager loaded, and it does not start a unit whose
   loaded configuration it could not verify. If a failed attempt left the `multi-user.target.wants` link pointing at the
   foreign unit (rehearsed: `systemctl enable` links to the fragment the manager actually loaded), `install` reports
   `enable-failed` after the override is gone: run `systemctl disable freedom-blades-executor-supervisor.service` first to drop
   the dangling link, then `install`.
4. Then converge with the tool: after a failed **upgrade**, run `install` again (a fragment already new only needs enabling and
   the checked reload; an old one is upgraded again; if the unit had been disabled and the restoration could not disable it, `systemctl disable` it first if that is the intended state) and `systemctl restart` if the unit is not running; after a failed
   **removal**, run `install` to put the fragment back and enable it, `systemctl reset-failed` and `systemctl start` the unit, run
   `verify-ready`, and only then retry `remove` in a quiet window (§8). If the executor was idle and the fragment is simply gone,
   the supervisor may be running from the manager's loaded copy only: it will not survive a reboot until `install` has
   been run again (`remove` refuses that state with `owner-without-fragment` until then).
5. Do not activate or resume the executor until `verify-ready` says `ready`.

## 8a. Migrating from the preceding user-service candidate (`legacy-user-service`)

The earlier candidate installed the same unit name as a *user* unit in `/etc/systemd/user`, globally enabled. It was never
accepted or deployed, so the installer does not migrate it: it refuses (`legacy-user-service`, exit 11) while any of
`/etc/systemd/user/freedom-blades-executor-supervisor.service{,.d,.wants}` or
`/etc/systemd/user/default.target.wants/freedom-blades-executor-supervisor.service` exists, and the system unit itself
carries `ConditionPathExists=!/etc/systemd/user/freedom-blades-executor-supervisor.service` so it will not start beside one.
If a host ever had it, clean up as root, in this order, and only with no invocation pending:

```
systemctl --user -M freedom-executor@ stop freedom-blades-executor-supervisor.service     # for every user manager that ran it
systemctl --global disable freedom-blades-executor-supervisor.service
rm /etc/systemd/user/freedom-blades-executor-supervisor.service
systemctl daemon-reload
# then remove any ~/.local/state/freedom-blades-executor and /run/user/<uid>/freedom-blades-executor it left, after
# checking they hold no invocations/active.json record; only then run `install`.
```

Never run both supervisors: each has its own ownership store, so two would be two owners of one boundary.

## 9. Known limits (carry into the review)

* The account can create a unit of the same name under its own `~/.config/systemd/user`. That is a separate unit in its
  own user manager: it has no effect on the root-owned system supervisor (its fragment, command, PID or restarts), which no
  user manager can load, reload, enable or stop. There is no residual shadowing risk to accept, and the installer no
  longer performs or relies on any point-in-time shadow scan of the account's directories.
* The supervisor runs as the dedicated account, so the account can signal its own process (it is the
  same uid; as with the earlier user-service design): code integrity of the running supervisor rests on the root-owned code tree, `-E -s`, and `NoNewPrivileges`, not
  on process isolation from the account. The sudoers entry bounds the privileged impact to the single fixed vector.
* Member-environment minimization is deliberately not an atomic guarantee. The manager-environment read and
  `StartTransientUnit` are separate D-Bus operations, and systemd may add new generated variables. Security therefore
  rests on the exact sudo vector and the root-owned `stop` artifact's `-I -S`, no-environment-read behavior; a PATH-only
  `/proc/<pid>/environ` observation is regression evidence, not an authorization proof.
* An ambiguous same-boot `start-sent` record (the process crashed after committing it and before or during the
  `StartTransientUnit` call, with the unit still absent) is never cleared on elapsed time; it blocks admission and
  removal until reboot, or until the deterministic unit appears and is adopted. This availability loss is an accepted,
  fail-closed consequence for this slice. A `prepared` record clears on affirmative unit absence; a changed boot
  identity clears any record. The boot-id rule is proven by unit test, and the earlier host reboot proof cannot
  distinguish it from the absent-unit/cgroup rule.
* The drain acknowledgment is valid only while its connection is held; a supervisor that restarts between the
  acknowledgment and the stop is detected by the dropped connection (and, after the stop, by the re-check), not
  prevented. The re-check closes the remaining window by restarting the owner when anything appeared.
* Trust is verified by path at install/verify time; ownership and mode are not re-checked while the service runs, so
  the root-owned, non-writable property depends on the deployment keeping it.
* One unrelated attest-host test (`test_default_action_termination_leaves_no_false_record_and_is_recovered_explicitly`)
  is a timing flake with no baseline comparison yet.
* Production interpreter/dependency provisioning (§4), the SA-2 artifact installation and any polkit policy on the host are outside this tool (the account must hold none that lets it control system units; the host proof confirms a default Ubuntu host denies it).
