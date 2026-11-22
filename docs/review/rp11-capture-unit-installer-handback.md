# RP-11 capture-unit installer mechanics — implementation handback

**Date:** 2026-11-21  
**Disposition:** reusable installer mechanics implemented and tested on `oracle-test`; production deployment remains out of scope.

## Delivered

Added `tools/rp11_capture_unit_install.py`, a root-owned system-unit installer, verifier and remover. It accepts a reviewed source fragment at the fixed default path, verifies the RP-11 artifact/interpreter trust chain and manager state, requires the fixed privileged consume command, checks a single finite start timeout, rejects enablement and drop-in/shadow paths, and performs checked daemon reload with rollback/read-back. It never starts, stops or enables the capture unit.

No production unit fragment is shipped. No `ExecStart`, sandbox profile, timeout budget or production capture policy was chosen. The default CLI therefore refuses installation while its source fragment is absent. This code is a mechanics slice, not a deployable production capture service.

The synthetic host integration test uses a random unit name and synthetic stand-in only. Identity-tracked cleanup removes only objects created by that test and fails while preserving unexpected or replaced state. The production unit name is explicitly kept absent; no activation, pass, evidence, grant or production mutation was performed.

## Verification

- Focused local suite: **165 passed** (`tests/test_rp11_capture_unit_install.py` and `tests/test_rp11_capture_unit_install_cleanup.py`).
- Disposable real-systemd suite: **9 passed** (`tests/systemd_integration/test_rp11_capture_unit_install_host.py`, root on `oracle-test`).
- `py_compile` passed for the installer and its tests/helpers; `git diff --check` passed.
- Post-run disposable-host checks found no synthetic scratch directory, unit fragment, synthetic unit, or stand-in artifact.
- No production command was run, no commit was created, and no production unit fragment or deployment policy was added.

## Remaining production work

The production `rp11-capture-pass-a.service` definition still needs an approved `ExecStart`, sandbox directives/properties, timeout budget, and a reviewed source/activation procedure. That work requires its own security review and explicit production authorization before deployment. S4 acceptance remains incomplete: probes 2 and 6 still need a genuine capture pass and valid consume evidence; probes 3 and 5 also remain incomplete. The supervisor’s last recorded production state remains active and ready; this implementation does not change or revalidate that state.

[Active handover](Handover%20information) · [Current status](../project-management/status.md) · [Implementation plan](../implementation-plan.md)
