# Project status

## Current status — Route 3 prerequisite accepted — 2026-10-15

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

The subsequent security remediation and its re-review corrections are
complete. Independent re-review confirmed the universal positive
non-authorization gate for BS-3, the bounded terminal Polkit check and the
cleanup-record consistency relations, and recommends acceptance for continued
development. Two additional validator observations are non-blocking hardening
for the production security review; they do not reopen the inactive series or
require another remediation cycle.

Peter Duscha accepted the Polkit `tmpfiles.d` prerequisite on 2026-10-15. The
accepted slice includes a
repository fragment, a safe install/verify/remove operator path and a real
reboot on `oracle-test` showing `/run/polkit-1/rules.d` exists before polkit
starts, with a real Route 3 hold success and recovery path run without any
Polkit restart. Effective-configuration overrides, pathname-replacement races,
restore interruption and restore durability are covered by the completed
remediations and executable tests
([handback](../review/route-3-polkit-tmpfiles-installer-handback.md)). The
disposable host is back to its prior state.

The next development increment is the first real Package 5.0 consumer on
`oracle-test`. Production and staging activation remain out of scope. Before
any production activation, the transient inspection-failure risk needs an
explicit decision and the completed series needs its final production security
review.

Production and staging remain unchanged. Real credentials and player data must
not be copied to the disposable environment.

[Active handover](../review/Handover%20information) ·
[Active delivery plan](active-delivery-plan.md) ·
[Accepted role-series handback](../review/route-3-hold-role-implementation-handback.md) ·
[Disposable-server procedure](../operations/disposable-test-server.md) ·
[Archived predecessor status](status-through-2026-10-13-route-3-hold-active.md) ·
[Status archive](status-archive/README.md).
