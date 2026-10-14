# Project status

## Current status — Route 3 `hold` implementation active — 2026-10-13

**Baseline v1.9 is active. Implementation and unrestricted testing on the
disposable `oracle-test` server are authorized.**

The former WP-3 research and contract-closure sequence is complete as historical
background and no longer blocks development. Its unresolved Q3/Q6 labels and
integration observations are implementation inputs, not gates.

Peter Duscha accepted the Route 3 manager/Polkit adapter on 2026-10-13. Its four
security-remediation findings are closed for continued development, and its
final comparison introduced no Route 3 regression against the existing red
repository baseline.

Current slice: implement the role behaviors in dependency order under the
[active delivery plan](active-delivery-plan.md). Shared cleanup/`stop-post` is
complete; `backstop` is complete; `hold` is the active assignment. The adapter
and roles remain inactive in production.

Peter accepted the backstop Q6-7 behavior. The preferred future Polkit
installer mechanism is a `tmpfiles.d` entry, with installation and real-reboot
proof deferred until the installer/activation slice; the current hold harness
must cover pre-start setup and late-directory fail-closed behavior.

Production and staging remain unchanged. Real credentials and player data must
not be copied to the disposable environment.

[Active handover](../review/Handover%20information) ·
[Active delivery plan](active-delivery-plan.md) ·
[Disposable-server procedure](../operations/disposable-test-server.md) ·
[Archived pre-reset status](status-through-2026-10-12-wp3-contract-review.md) ·
[Status archive](status-archive/README.md).
