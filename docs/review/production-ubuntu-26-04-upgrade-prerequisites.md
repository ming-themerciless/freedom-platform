# Production Ubuntu 26.04 upgrade — prerequisites and venv procedure (draft)

Status: draft for Peter and independent review. Uncommitted. It authorizes
nothing; the governing text remains
`production-ubuntu-26-04-upgrade-claude-prompt.md`. Production is NO-GO until
Part A is complete.

## Evidence this draft rests on

* Phase B rehearsal (synthetic Ubuntu 24.04.5 VM on `oracle-test`, 2026-11-05):
  `do-release-upgrade` rc=0; after reboot 26.04.1, kernel 7.0.0-42, systemd 259,
  cgroup v2, OpenSSH 10.2, `/tmp` tmpfs, PostgreSQL 16 online on 5432 with data
  intact, no PostgreSQL 18 cluster, `dpkg --audit` clean, `python3.14`,
  `-minimal` and `-venv` 3.14.4-1ubuntu0.2 installed by the upgrader itself
  from the Ubuntu archive.
* The upgrade removes `python3.12-minimal` and `python3.12-venv`. A virtualenv
  built on 3.12 then resolves to 3.14 and loses its installed packages.
* `postgresql-16` survives but has no archive source on 26.04 (no security
  updates). `autoremove` did not propose removing it.
* Application suites on Python 3.14.4 (`oracle-test`, this tree): web 2890
  passed / 80 skipped / 2 failed (same 2 on 3.12); bot differs from 3.12 only in
  Route 3 descriptor tests (extra fd after importing `ctypes`) and a missing
  `jeepney` in the test venv.

## Part A — what Peter must supply (provider side)

1. Maintenance window: start time and a six-hour end time.
2. Peter named as rollback and escalation owner for the whole window.
3. A completed boot-volume snapshot of the production VM, taken **after** the
   application writers and PostgreSQL are stopped (Phase C step 5). Record only
   the non-secret snapshot identifier and its "completed" status.
4. Tested access to the provider serial/recovery console, proved by logging in
   once before the window.
5. The exact provider steps Peter will follow to restore the boot volume from
   that snapshot.

Generic procedure (adapt to the provider's console; the provider is not recorded
in the repository, so these are not provider-specific commands):

* Snapshot: provider console → the production instance → its boot volume →
  create backup/snapshot; wait for status "available/completed"; note the ID.
  If the console offers "application-consistent" or "stop instance first",
  prefer a snapshot taken while the instance is stopped.
* Console: provider console → instance → serial/VNC console connection; log in
  as a local user once. If no local password exists, the provider's recovery
  mechanism must be verified instead, since SSH may be unavailable during the
  window.
* Restore: provider console → create a new boot volume from the snapshot →
  stop the instance → detach the current boot volume (keep it) → attach the
  restored volume as boot → start. Write down who does this and the
  expected duration.

Note: the host is a KVM guest (AMD EPYC-Milan); `sshd` currently allows root
login and password authentication. Leave those unchanged during the window.

## Part B — rebuilding the four Python 3.12 virtualenvs for 3.14

Affected: `/opt/freedom-blades/runtime/venv-web`, `.../venv-bot`,
`/opt/discord-bots/venv`, `/opt/discord-bots/venv-web`. Ownership today:
`foundry:nogroup 2775`, `foundry:nogroup 2775`, `foundry:discordbot 775`,
`foundry:foundry 775`.

Do this **after** the upgrade, before any service starts, while writers stay
stopped (Phase E, before Phase F):

1. For each venv, create a sibling directory (`<venv>.py314`) with
   `/usr/bin/python3.14 -m venv`, as the owning user, preserving the mode above.
2. Install from the repository lock/requirements file that matches the venv:
   web venvs from `requirements-web.lock`; bot venv from `requirements.txt`
   (the test venv also needs `requirements-dev.txt`, which includes
   `infra/rp11-h1/requirements.txt` for `jeepney`). The `/opt/discord-bots`
   venvs are legacy; confirm which requirements file they use before building,
   and do not guess.
3. `pip check` must report no broken requirements; import the application's
   top-level modules (`discord`, `sqlalchemy`, `psycopg`, `googleapiclient`,
   `fastapi`) with each new interpreter.
4. Only then change each service's interpreter path to the new directory, one
   unit at a time, and run `systemd-analyze verify` on it. Keep the old
   directories untouched until the 30-minute observation passes.
5. Nothing here needs network access beyond the Ubuntu archive and PyPI. Do not
   run it before the window: building venvs on production is a production write.

Open question for Peter: whether `/opt/discord-bots/*` is still used by any
running unit. The enumerated units use `freedom-bot`, `freedom-worker` and
`pm2-foundry`; their interpreter paths were not read in Phase A.

## Not covered here

Route 3 redesign for a pre-existing Python 3.14 (S0.0 no longer applies),
the 3.14 `ctypes` descriptor behavior in `rp11_h1`, and the pinned digest of
`tools/r5_runner/blocks/s04b-sync.argv`. Block F stays `UNSET`.
