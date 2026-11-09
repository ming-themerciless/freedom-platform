---
name: run-suites
description: Run the Freedom Blades test suites correctly and report the result honestly. Use whenever asked to run tests, verify a change, confirm something works, or cite suite figures. Carries the two facts that otherwise produce a green run proving nothing - the TEST_DATABASE_URL export and the skip-count check - plus the serial-execution rule and the canonical interpreter path.
---

# Running the suites

**This skill is a procedural aid, not a source of rules.** The authority is
`.agents/AGENTS.md` "Testing / Running the suites" and
`docs/operations/disposable-test-server.md`. If this file and either of those
disagree, they win and the disagreement is a defect to report, not a choice to
make.

## Authority

Baseline v1.9 authorizes every testing level on `oracle-test`, including SSH,
packages, network, root/systemd, PostgreSQL, destructive migration/recovery
drills and end-to-end tests. Read the active handover for the current slice,
but do not revive restrictions from archived Package 5.0 evidence work.
Production/staging and real secrets/player data remain excluded.

## The two facts that make a false green possible

Both are load-bearing. State them in any evidence that cites a figure.

* **The repository and the test environment are different hosts.** Work in
  `/opt/freedom-blades/platform`. The documented interpreter is
  `/opt/freedom-blades/runtime/venv-web/bin/python` **on `oracle-test`**. The
  historical `/opt/discord-bots/` environments are not the default. An
  interpreter path existing on one host says nothing about another.
* **`TEST_DATABASE_URL` must be exported.** Without it every database-marked
  test skips, the web suite finishes in about twelve seconds reporting roughly
  **1362 skipped**, and **it still exits 0**. With it, the correct web skip count
  is **80**. Check the skip count before believing a pass, and use `-rs` so each
  reason prints. The bot suite skips 337 as user `ubuntu` at the default descriptor
  limit (reasons printed; identical in two complete runs). `ulimit -n 4096` also
  lowers the hard limit, so four tests that need 70,001 descriptors skip as well
  (341), and some tests skip unless root. Report the count with its limit and user.

## Order of execution

Narrow first, then broad. Run the bot and web suites **serially**: they share one
disposable database (finding F-6), so a parallel run is a different verification,
not a faster one.

1. Structural or focused tests for what changed.
2. The changed area's full module.
3. The complete available suites.

## The canonical run, on `oracle-test`

Synchronize first with the secret-excluding procedure in
`docs/operations/disposable-test-server.md` §3.2. Do not use
`--delete-excluded`, and keep `--include='.env.example'` before `--exclude='.env*'`.

```bash
cd /opt/freedom-blades/platform
export PATH='/usr/lib/postgresql/18/bin:/usr/bin:/bin'
export TEST_DATABASE_URL='postgresql+psycopg:///freedom_test'
/opt/freedom-blades/runtime/venv-web/bin/python -m pytest -q -rs -o tmp_path_retention_policy=failed tests/test_*.py
/opt/freedom-blades/runtime/venv-web/bin/python -m pytest -q -rs -o tmp_path_retention_policy=failed tests/web
node --test "foundry-module/tests/"*.test.mjs
```

The disposable lane is Ubuntu Python 3.14/PostgreSQL 18 with a 2 GiB swapfile.
Failed-only temporary-path retention and the swapfile accommodate the 951 MiB
host. **Do not raise the descriptor limit**: `ulimit -n 4096` lowers the hard
limit too, which changes the skip count (337 becomes 341), and the descriptor
leak it used to hide is fixed. The 2026-11-08 exact-tree result, on the
refreshed dependency set (FastAPI 0.162, SQLAlchemy 2.1, pytest 9, pytest-asyncio
1.x), is green (bot: 7,571 passed, 0 failed, 0 errors, 337 skipped, the same skip
reasons as 2026-11-07; web: 2,893 passed, 80 skipped; Foundry: 171 passed). Skip counts: web 80, bot 337
as user `ubuntu`; each prints a reason, so compare the reasons if a count moves.
Always report a fresh result rather than citing those figures for a later tree.

## Reporting

* Re-run the full set against the tree you are actually submitting. A figure
  carried from an earlier tree describes a state that no longer exists.
* Report the exact command, the interpreter, the counts, and the skip reasons.
* Report every check that could not be run, and why.
* **Do not claim a check passed unless it was actually run.** A passing defect
  reproduction is evidence the defect is open, not a passed invariant.
