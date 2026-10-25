# Project status

## Current status — Route 3 production-readiness checklist completion independently re-reviewed — 2026-10-24

**Baseline v1.9 is active. Implementation and unrestricted testing on the
disposable `oracle-test` server are authorized.**

**Final focused re-review complete.** Codex found no remaining implementation
defect and recommends acceptance for continued non-production development.
The exact extracted checklist matched between the workspace and `oracle-test`;
the checklist module passed **53/53** there; `bash -n` and `git diff --check`
were clean; the structural run reproduced **127 passed, 1 known baseline
allowlist failure**. Peter's acceptance and transient-risk decision remain
separate. Production/staging access, inspection and activation remain
unauthorized.

**Direct completion assigned.** Codex's review of the fifth return found one
remaining bounded checklist defect: item 5b prints `COMPLETE` after a directory
search or unit query fails. Peter assigns Claude the direct correction under
the accepted fifth-remediation scope, with two focused regressions and only the
focused checklist, shell-syntax, directly affected structural and diff checks.
This is not a sixth remediation round and requires no full-suite rerun. The
candidate remains unaccepted; no transient-risk decision or production/staging
access, inspection or activation is authorized.

**Fifth review remediation returned.** Claude has returned the **fifth** production-readiness review remediation for independent Codex re-review (handback "Fifth review remediation return", 2026-10-23): checklist item 5b (and the identical path-set/pid copies in items 5 and 11) now fails closed on every fact-gathering status (root and account NSS records validated without a masking pipeline, the account-context `unit-paths` result usable only at status 0, every append/sort/search reported, scratch removed by an `EXIT` trap), proved by 47 executable checks and a host decoy probe; `oracle-test` was already in the documented canonical state when inspected (the root-owned Python 3.14 state Codex saw was not reproducible and its cause is not established) and is unchanged apart from removed scratch; the fourth-return section Codex found absent is present in the tree, but its figures are replaced by fresh final-tree runs. No installer or product code changed. Not accepted; no transient-risk decision; no production/staging access, inspection or activation.

**(History)** **Fourth review remediation returned.** Claude has returned the **fourth** production-readiness review remediation for independent Codex re-review (handback "Fourth review remediation return", 2026-10-23): enablement is observed strictly (only an absent wants link is "disabled"; an I/O or permission error, a foreign object or an unexpected target is `enablement-unavailable`, exit 13, before an upgrade changes anything and `recovery-incomplete`, exit 15, after it), checklist item 5b inspects only the fixed `freedom-executor` account and prints only allowlisted unit properties (never a description; an ambient `ACCOUNT` is ignored), and the current-state headings are reconciled. Not accepted; no transient-risk decision; no production/staging access, inspection or activation.

**Fourth review remediation assigned (history).** Independent Codex re-review found that
wants-link observation still conflates I/O failure with disabled state, item 5b
can print an untrusted unit description and accepts an ambient account override,
and current-state headings are stale. Peter assigns Claude the bounded
[fourth remediation](../review/route-3-production-readiness-review-remediation-r4-claude-prompt.md).
Nothing is accepted; the transient-risk decision and all production/staging
access, inspection and activation remain unauthorized.

**Active slice.** Peter assigns Claude the bounded
[Route 3 production-readiness and security-gate preparation](../review/route-3-production-readiness-claude-prompt.md).
The slice reviews the complete accepted privileged chain, performs an exact-path
root-owned deployment/reboot/failure/rollback/removal rehearsal on
`oracle-test`, prepares the transient inspection-failure decision and identifies
the minimal production-specific read-only facts for a later separately
authorized inspection. It returns for independent Codex review. Production and
staging access or activation, the risk decision, full coordinator, start
orchestration, automatic attestation, migration/cutover and RB-1 remain
unauthorized.

**Third review remediation assigned.** Independent Codex re-review found that unavailable pre/post `ActiveState`
observations can compare equal and falsely verify upgrade restoration, that restoration discards a non-zero `enable`/`disable`
status when the link happens to match, and that the production checklist enumerates the invoking operator's user-unit paths
rather than `freedom-executor`'s effective paths. Peter assigns Claude the bounded
[third remediation](../review/route-3-production-readiness-review-remediation-r3-claude-prompt.md). Nothing is accepted; Peter
has not decided the residual risk; production/staging access, inspection and activation remain unauthorized.

**Third review remediation returned.** Claude has returned the bounded third remediation for independent Codex re-review (handback "Third review remediation return"): unit-state observation is strict (`state-unavailable` before an upgrade, `recovery-incomplete` after), restoration checks the enable/disable status as well as the link, and the checklist inspects `freedom-executor`'s own user-unit paths (item 5b, executed on `oracle-test`). Not accepted; no risk decision; no production/staging access, inspection or activation.

**Second review remediation returned.** A second independent Codex review reproduced three installer recovery gaps and two
defects in the proposed production inspection methods. Claude returned the bounded
[second remediation](../review/route-3-production-readiness-review-remediation-r2-claude-prompt.md) for independent re-review
(handback "Second review remediation return"): manager exceptions enter the verified restoration path; enablement is restored
in both directions; `remove` refuses a running supervisor with an absent fragment (`owner-without-fragment`) and never discards
a failed restart; the production checklist prints no process arguments and its command shapes were executed on `oracle-test`.
Nothing is accepted; Peter has not decided the residual risk; production/staging access or activation is unauthorized.

**Review remediation returned (first).** Independent Codex review of the handback found blocking installer recovery and sudo-policy
defects, an inaccurate residual-lifecycle statement, incomplete production-inspection methods and unfinished evidence. Claude
returned the bounded [remediation](../review/route-3-production-readiness-review-remediation-claude-prompt.md) for independent
Codex re-review (see handback §0): verified recovery and `recovery-incomplete` (15) in the installer, exact run-as/tag sudo
verification, corrected residual lifecycle and recommendation, complete read-only fact methods, and final-tree suite figures.
Nothing is accepted; Peter has not decided the residual risk; production/staging access or activation is unauthorized.

**Returned.** Claude returned the slice for independent Codex review: [handback](../review/route-3-production-readiness-handback.md). It records no acceptance, risk decision, readiness or activation approval.

**Sequence.** The cumulative R6 candidate closed the post-write ownership,
readiness-order, effective-unit verification and socket-proof defects through
the recorded bounded remediations. Claude returned the final test-only ordering
correction. Independent Codex re-review found no remaining finding and
reproduced the five targeted cases in 12 consecutive `oracle-test` runs plus
the focused **511 passed, 5 documented host-only skips** result; `compileall`
and `git diff --check` were clean. Peter accepted the executor OC R6 candidate
for continued non-production development on 2026-10-22. No successor slice is
assigned, and production/staging installation or activation remains prohibited.
See the [cumulative executor handback](../review/route-3-executor-oc-implementation-handback.md#independent-codex-re-review-of-the-r6-socket-proof-ordering-remediation-and-acceptance-2026-10-22).

Earlier state, retained as history: Claude returned the R6 candidate in the existing
[executor handback](../review/route-3-executor-oc-implementation-handback.md).
Independent Codex review reproduced its principal suites but found one blocking
gap: `KeyboardInterrupt` or another `BaseException` at or after the request-write
boundary can escape instead of becoming `HANDED_OFF`. The active handover,
delivery plan and implementation-plan pointer also remained at the completed
assignment state.

Peter accepts the recommendation and assigns Claude the direct correction under
the [R6 review-remediation prompt](../review/route-3-executor-oc-r6-review-remediation-claude-prompt.md).
At that point the candidate remained unaccepted. No production/staging
installation or activation and no successor slice was authorized by that
historical assignment.

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
role. At that assignment point the full coordinator, start orchestration,
automatic attestation and production installer/activation work were out of
scope. The inactive executor supervisor package was subsequently assigned as
recorded below; actually installing or activating it in production/staging
remains out of scope.

Claude's executor candidate correctly implemented the fail-closed OC gate and
then established on `oracle-test` that bounded `cgroup.kill` cannot guarantee
disappearance of a task in uninterruptible sleep. Peter approved, in principle,
the resulting lifecycle change: an unsettled but kernel-contained invocation
may be transferred to a persistent owner which blocks further orchestration and
continues recovery until the boundary is empty.

The second-remediation implementation was **not accepted at that stage**. Independent Codex
review showed that hand-off remains best-effort after launch: marker failure can
still return `UNSETTLED`, and an ordinary exception can propagate after the
failed marker write while the member remains and the scope closes. It also
provides no already-running persistent supervised owner; its host test invokes
one-shot recovery manually and does not prove continuous ownership or restart
recovery. Peter kept the executor OC slice blocked until durable recoverable
ownership is established before privileged launch, retained on every exit
path, and proved through a real persistent-owner restart and eventual-cleanup
test, and assigned Claude that bounded correction under the
[third executor review-remediation prompt](../review/route-3-executor-oc-review-remediation-r3-claude-prompt.md);
no successor slice is assigned.
The selected design is a restartable supervisor plus a separate transient
service per invocation, owned by the dedicated account's systemd user manager.
Durable exclusive prepared state precedes the one `StartTransientUnit` call, and
systemd launches the exact fixed sudo vector directly inside the invocation
cgroup. This separation permits supervisor restart while the user manager
retains a stuck invocation. For the inactive package Peter selected a root-owned
system-service wrapper (`User=freedom-executor`) for the persistent supervisor,
corrected under the
[fifth executor review-remediation prompt](../review/route-3-executor-oc-review-remediation-r5-claude-prompt.md); production
installation, lingering and activation remain a later decision.
Peter approved a sixth bounded review correction on 2026-10-21 without changing
the topology. It closes the ambiguous request-write and readiness-order races,
extends installer verification to effective drop-ins and execution identity,
and replaces the impossible atomic exact-environment claim with the actual
privileged invariant: fixed sudoers/SA-2 argv, Python `-I -S`, and the root-owned
`stop` artifact's no-environment-read path. The completed remediation chain was
independently re-reviewed and accepted by Peter for continued non-production
development on 2026-10-22.
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
