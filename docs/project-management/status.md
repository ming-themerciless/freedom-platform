# Project status

## Current status — Route 3 role series accepted — 2026-10-14

**Baseline v1.9 is active. Implementation and unrestricted testing on the
disposable `oracle-test` server are authorized.**

The former WP-3 research and contract-closure sequence is complete as historical
background and no longer blocks development. Its unresolved Q3/Q6 labels and
integration observations are implementation inputs, not gates.

Peter Duscha accepted the complete inactive Route 3 role series on 2026-10-14:
shared cleanup/`stop-post`, `backstop`, and `hold`, including the GRR
inspection- and descriptor-close exception-safety remediations. Independent
review found no remaining finding, and the final focused, root/systemd, bot,
web and Foundry comparisons introduced no Route 3 regression against the
established repository baseline.

Peter accepted the backstop Q6-7 behavior. The preferred future Polkit
installer mechanism is a `tmpfiles.d` entry, with installation and real-reboot
proof deferred until an installer/activation slice. Before any production
activation, the transient inspection-failure risk also needs an explicit
decision and the completed series needs an independent security review.

Production and staging remain unchanged. Real credentials and player data must
not be copied to the disposable environment.

[Active handover](../review/Handover%20information) ·
[Active delivery plan](active-delivery-plan.md) ·
[Accepted role-series handback](../review/route-3-hold-role-implementation-handback.md) ·
[Disposable-server procedure](../operations/disposable-test-server.md) ·
[Archived predecessor status](status-through-2026-10-13-route-3-hold-active.md) ·
[Status archive](status-archive/README.md).
