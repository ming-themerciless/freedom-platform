# Implementation-first reset — handback

## Delivered

- Baseline v1.9 makes implementation and executable testing the default.
- Every testing level is authorized on the disposable `oracle-test` server.
- The WP-1 through WP-3 proof chain and its open labels are historical inputs,
  not development gates.
- The active Route 3 adapter slice now has a concise implementation/test plan
  and an explicit finish line based on running code.
- Current agent, project-management, handover, status, operations and Claude
  procedural instructions agree on the new authority.
- Displaced current-state documents were preserved in indexed snapshots. Older
  review files stay at their paths for link integrity and are classified as
  historical by `docs/review/README.md`.

## Verification

- `git diff --check`: clean.
- Local-link check across 17 changed canonical/index documents: 0 broken.
- Disposable-server document has one copy each of sections 1 through 4; a
  pre-existing duplicated copy was removed.
- No application tests were run because this slice changes documentation only.

## Safety boundary

Production and staging were not accessed or changed. No secrets or player data
were read. Existing unrelated working-tree changes were preserved.

## Next action

Run the existing suites on `oracle-test`, then implement and test the seven
Route 3 manager/Polkit interface intents under the active delivery plan.
