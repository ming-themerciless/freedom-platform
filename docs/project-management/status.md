# Project status

## Current status — non-root executor OC interruption slice assigned — 2026-10-18

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

Claude implemented the first real Package 5.0 consumer, static SA-1 `start`,
through DI-2. Its environment-read, duration, denial-proof and malformed-success
findings are remediated. Independent Codex re-review found no blocking issue;
Peter accepted SA-1 for continued non-production development on 2026-10-15
([handback](../review/route-3-start-role-implementation-handback.md)).

Static SA-2 `stop` through the existing narrow stop-unit boundary was implemented
and tested on `oracle-test`. Its refusal-diagnostic and typed-result findings
were remediated, and its unit-scoped host-job assertions were proved while an
unrelated systemd job remained queued. Independent Codex re-review found no
blocking issue; Peter accepted SA-2 for continued non-production development on
2026-10-16
([handback](../review/route-3-stop-role-implementation-handback.md)). No further
Package 5.0 slice was assigned by this acceptance. Peter subsequently approved
the recommended implementation sequence and assigned RT-1 `consume` to Claude
as the next bounded slice
([assignment](../review/route-3-consume-role-implementation-claude-prompt.md)).
Claude implemented it as an uncommitted candidate that runs as the capture
unit's PID-1 `ExecStartPre=+` and exercised it fully on `oracle-test`
([handback](../review/route-3-consume-role-implementation-handback.md)).
Independent Codex review found two blocking failure-path defects: failure
evidence can become unwritable without entering grant priority, and an
unexpected CQ-5 exception can retry PK/2. One bounded
[remediation](../review/route-3-consume-role-review-remediation-claude-prompt.md)
was implemented and verified on `oracle-test`. Independent Codex re-review found
no blocking issue, independently reproduced the focused **2062 passed, 2
skipped** result and the fresh root/systemd **14 passed** result, and verified
clean teardown. Peter accepted RT-1 for continued non-production development on
2026-10-17. Peter then assigned RT-5 `attest` as the next bounded slice. The
assignment is defined by the
[`attest` implementation prompt](../review/route-3-attest-role-implementation-claude-prompt.md).
Claude implemented it as an **uncommitted candidate** and exercised it on
`oracle-test`, including a real reboot
([handback](../review/route-3-attest-role-implementation-handback.md)). Independent
Codex review found a blocking false-success path when old-boot identity or
trusted `/run` evidence is missing, plus non-reproducible abbreviated commands
in the handback. Peter assigned one bounded
[review remediation](../review/route-3-attest-role-review-remediation-claude-prompt.md),
which Claude completed and returned for independent Codex re-review. Two further
reviews found and Claude remediated, in turn, a missing directory identity and a missing
mandatory tree-P `tree-intent`/`tree-linked`; the third remediation was returned for
independent Codex re-review ([third review prompt](../review/route-3-attest-role-review-remediation-r3-claude-prompt.md)).
A fifth bounded correction then made the changed-boot tree-P comparison lossless
for member fields, declaration cardinality and identity history. Independent
Codex re-review found no remaining implementation-quality blocker and
independently reproduced the focused **2369 passed, 2 documented environment
skips** result against matching files on `oracle-test`. Under Peter's 2026-10-18 evidence-policy clarification,
the fifth handback's summarized routine commands are a non-blocking
documentation variance rather than another remediation trigger. Peter accepted
RT-5 for continued non-production development on 2026-10-18. The non-root
executor and its fail-closed OC-1/OC-2/OC-3 checks were outside that accepted
slice. Peter subsequently assigned Claude the first real executor interruption
path under the
[`executor OC implementation prompt`](../review/route-3-executor-oc-implementation-claude-prompt.md):
unprivileged fixed-unit and consume-journal reads, exact OC-1/OC-2/OC-3
evaluation, and at most one fixed `sudo -n` call to the accepted SA-2 `stop`
role. The full coordinator, start orchestration, automatic attestation and
production installers/activation remain out of scope.
Production and staging activation remain out of scope. Before any production
activation, the transient inspection-failure risk needs an explicit decision
and the completed series needs its final production security review.

Production and staging remain unchanged. Real credentials and player data must
not be copied to the disposable environment.

[Active handover](../review/Handover%20information) ·
[Active delivery plan](active-delivery-plan.md) ·
[Accepted role-series handback](../review/route-3-hold-role-implementation-handback.md) ·
[Disposable-server procedure](../operations/disposable-test-server.md) ·
[Archived predecessor status](status-through-2026-10-13-route-3-hold-active.md) ·
[Status archive](status-archive/README.md).
