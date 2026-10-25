# Active handover — Route 3 production-readiness checklist completion independently re-reviewed — 2026-10-24

**IMPLEMENTATION AND FULL DISPOSABLE-SERVER TESTING AUTHORIZED**

Independent Codex re-review of the final portability follow-up found no
remaining implementation defect and recommends acceptance for continued
non-production development. The extracted checklist is byte-identical between
the workspace and `oracle-test`; the focused module passed **53/53** there;
`bash -n` and `git diff --check` passed. The directly affected structural run
reproduced **127 passed, 1 known baseline allowlist failure**. The fixed
isolated Python probe distinguishes existing paths, `ENOENT` and other
`OSError` outcomes without parsing diagnostic text; search and unit-query
failures remain `INCOMPLETE`. Peter's acceptance and transient-risk decision
remain separate. Production/staging access, inspection and activation remain
unauthorized.

Codex's focused re-review synchronized the exact direct-completion tree to
`oracle-test` and found a portability defect: the repository host's GNU
coreutils `stat` wording matched the checklist, while `oracle-test`'s uutils
wording did not, producing **6 failed, 45 passed**. Peter assigns Claude the
final portability follow-up under the same existing direct-completion section:
classify absence from `FileNotFoundError`/`ENOENT` through the fixed isolated
Python 3.14 interpreter, never from diagnostic text; preserve `INCOMPLETE` for
every other failure; add the focused three-outcome proof; synchronize first and
run only the focused checks on `oracle-test`. No new remediation or full-suite
run is authorized. The candidate remains unaccepted and all production/staging
prohibitions remain.

Peter accepts Codex's review disposition and assigns Claude one direct
completion correction under the existing
[`fifth remediation prompt`](route-3-production-readiness-review-remediation-r5-claude-prompt.md),
not a sixth remediation round. Item 5b currently reports `COMPLETE` after a
directory search or unit query returns non-zero. Claude must make those outcomes
`INCOMPLETE`, add the two focused regressions, run only the focused checklist,
shell-syntax, directly affected structural and diff checks, and update the
existing handback/current-state records in place. No full-suite rerun is
required. The candidate remains unaccepted; there is no transient-risk decision
and no production/staging access, inspection or activation.

Claude has completed that direct correction (handback "Direct completion correction after the fifth review", 2026-10-24): item 5b prints `COMPLETE` only when the path set was formed, every existing directory was searched with status 0 (absence is accepted only when `stat` reports it) and all three unit queries succeeded; otherwise `INCOMPLETE`. Two focused regressions added; checklist module now 53 passed on `oracle-test` after a portability follow-up (absence decided by `os.lstat` errno via the fixed `python3.14 -I -S`, not by `stat` diagnostic text), `bash -n` and `git diff --check` clean. Returned for independent Codex re-review; not accepted.

Claude has returned the **fifth** production-readiness review remediation for independent Codex re-review (handback "Fifth review remediation return", 2026-10-23): checklist item 5b (and the identical path-set/pid copies in items 5 and 11) now fails closed on every fact-gathering status (root and account NSS records validated without a masking pipeline, the account-context `unit-paths` result usable only at status 0, every append/sort/search reported, scratch removed by an `EXIT` trap), proved by 47 executable checks and a host decoy probe; `oracle-test` was already in the documented canonical state when inspected (the root-owned Python 3.14 state Codex saw was not reproducible and its cause is not established) and is unchanged apart from removed scratch; the fourth-return section Codex found absent is present in the tree, but its figures are replaced by fresh final-tree runs. No installer or product code changed. Not accepted; no transient-risk decision; no production/staging access, inspection or activation.

Superseded record (kept for history): Claude has returned the **fourth** production-readiness review remediation for independent Codex re-review (handback "Fourth review remediation return", 2026-10-23): enablement is observed strictly (only an absent wants link is "disabled"; an I/O or permission error, a foreign object or an unexpected target is `enablement-unavailable`, exit 13, before an upgrade changes anything and `recovery-incomplete`, exit 15, after it), checklist item 5b inspects only the fixed `freedom-executor` account and prints only allowlisted unit properties (never a description; an ambient `ACCOUNT` is ignored), and the current-state headings are reconciled. Not accepted; no transient-risk decision; no production/staging access, inspection or activation.

Assignment record (returned above; kept for history): Peter accepted Codex's re-review findings and assigned Claude one final bounded
**fourth** production-readiness remediation under the
[`fourth remediation prompt`](route-3-production-readiness-review-remediation-r4-claude-prompt.md): make wants-link observation
strict, make checklist item 5b fixed-account and allowlisted-output only, and
reconcile stale current-state headings. The candidate remains unaccepted; no
transient-risk decision and no production/staging access, inspection or
activation is authorized.

Peter accepts Codex's re-review findings and assigns Claude one bounded **third**
production-readiness remediation under the
[`third remediation prompt`](route-3-production-readiness-review-remediation-r3-claude-prompt.md): distinguish successful from
unknown unit-state observations across upgrade recovery, require both a successful manager operation and the expected link for
symmetric enablement restoration, and inspect the dedicated executor account's effective user-unit paths rather than the
operator's paths. The candidate remains unaccepted; no transient-risk decision and no production/staging access, inspection or
activation is authorized.

Claude has returned the **third** review remediation for independent Codex re-review (handback "Third review remediation return"); not accepted, no risk decision, no production/staging access, inspection or activation.

Claude has returned the **second** review remediation for independent Codex re-review
([`second remediation prompt`](route-3-production-readiness-review-remediation-r2-claude-prompt.md); handback "Second review
remediation return"): every manager exception or timeout during an upgrade now enters the verified restoration path, enablement
is restored in both directions (a disabled unit is disabled again), `remove` refuses a running supervisor whose fragment is
absent (`owner-without-fragment`, exit 11) and a drained owner that cannot be given a persistent fragment is
`recovery-incomplete`, and the production read-only checklist no longer prints process arguments and is shell-valid. Still
unaccepted; no risk decision; no production/staging access or activation.

Earlier return (first remediation, kept for history): the review remediation for independent Codex re-review: the installer now verifies upgrade/removal recovery and exits `recovery-incomplete` (15) when it cannot, the sudo verifier accepts only run-as `root` with `NOPASSWD`, the residual lifecycle and recommendation are corrected, the production read-only fact methods are complete, and the handback is finished on the final tree ([handback](route-3-production-readiness-handback.md), §0). The candidate is not accepted; Peter has made no transient-risk decision; production/staging access or activation remains prohibited.

Current assignment (2026-10-22, returned above): independent Codex review of the returned
production-readiness handback found blocking installer recovery and sudo-policy
verification defects, a materially incorrect residual-lifecycle statement,
incomplete production-policy inspection methods and unfinished final-tree
evidence. Peter assigns Claude one bounded correction under the
[`production-readiness review remediation prompt`](route-3-production-readiness-review-remediation-claude-prompt.md).
The candidate remains unaccepted; Peter has made no transient-risk decision,
and production/staging inspection or activation remains prohibited.

Preceding assignment (2026-10-22): Peter assigned Claude one bounded Route 3
production-readiness and security-gate preparation slice under the
[`production-readiness prompt`](route-3-production-readiness-claude-prompt.md).
Claude must review the complete accepted privileged chain, perform an exact-path
root-owned install/reboot/failure/rollback/removal rehearsal on `oracle-test`,
prepare the transient inspection-failure decision and the production-specific
read-only fact checklist, and return one concise handback for independent Codex
review.

Claude has returned it for independent Codex review (see the
[`production-readiness handback`](route-3-production-readiness-handback.md)): exact-path rehearsal complete and host restored,
inspection-failure analysis with a recommendation (not a decision), and the production read-only fact checklist.
Nothing here records acceptance, the risk decision or readiness.

This assignment authorizes no production or staging access, inspection,
installation or activation. It does not decide the transient inspection-failure
risk or authorize the full coordinator, start orchestration, automatic
attestation, migration/cutover or RB-1. Any production inspection and any
activation remain separate explicit decisions after independent review.

Current executor state (2026-10-22): Claude returned the bounded test-only
socket-proof ordering correction. Independent Codex re-review found no
remaining finding: the corrected real-socket test records and requires the
successful complete-request crossing, always injects its promised
`BrokenPipeError`, and retains the one-request `HANDED_OFF` proof. Codex
reproduced the five targeted cases in 12 consecutive `oracle-test` runs and the
focused **511 passed, 5 documented host-only skips** result; `compileall` and
`git diff --check` were clean. Peter accepts the cumulative executor OC R6
candidate for continued non-production development.

The accepted executor candidate supplies the implementation input for the
production-readiness assignment above. The full coordinator, start
orchestration, automatic attestation, production capture-unit/executor
installation, production or staging activation, migration/cutover and RB-1
remain outside current authority.

Earlier executor state (2026-10-21, retained as history): Claude returned the first R6
implementation candidate; independent Codex review found the post-write
`BaseException` ownership gap; Peter assigned the first bounded remediation;
Claude returned it with the corrected ownership boundary; independent Codex
re-review found no remaining implementation defect but found the two real-socket
proofs nondeterministic (a single `recv` may return a prefix) and current-state
text stale; Peter accepted the
[`second remediation prompt`](route-3-executor-oc-r6-review-remediation-r2-claude-prompt.md) and assigned Claude
the correction; Claude has returned it (exact full-request peer read before the
`crossed` event; documents reconciled). Independent Codex re-review found no
implementation or production-safety defect and recommends acceptance. One test-
helper overclaim remains: its bounded read proves that the complete fixed request
arrived before `crossed`, but does not reject every separately delivered surplus
byte. Peter records that observation as non-blocking and assigns the optional
[`socket-proof hardening prompt`](route-3-executor-oc-r6-nonblocking-test-hardening-claude-prompt.md).
At that point the candidate was not yet accepted; no successor slice was
assigned, and production/staging installation or activation remained prohibited.

Earlier state, retained as history: Claude returned the R6 candidate for independent Codex
review. The focused, SA-2/artifact, documentation and root/systemd package
suites reproduced, but review found one blocking ownership gap: a
`KeyboardInterrupt` or other `BaseException` at or after the request-write
boundary can escape instead of becoming `HANDED_OFF`. Several current-state
documents also still described the completed first R6 assignment as pending.
Peter accepts the recommendation and assigns Claude one bounded correction
under the
[`R6 review-remediation prompt`](route-3-executor-oc-r6-review-remediation-claude-prompt.md).
At that point the candidate was not accepted, no successor slice was assigned,
and production/staging installation or activation remained prohibited. The
environment decision, fixed sudoers/SA-2 argv, Python `-I -S` and root-owned
`stop` artifact boundary are unchanged.

Peter Duscha supersedes the WP-3 research-only hard stop and the associated
WP-4 through WP-7 documentation gates for development work. The WP-1 through
WP-3 records remain historical evidence; they are not current prerequisites and
need no further closure or reconciliation.

Peter Duscha accepted the complete inactive Route 3 role series on 2026-10-14
after independent review of the final GRR descriptor-close remediation. The
manager/Polkit adapter and all three dependency-ordered role slices are now
complete for continued development:

1. shared cleanup plus `deact … stop-post` — accepted;
2. `backstop`, reusing the accepted cleanup implementation — accepted; and
3. `hold`, including GRR inspection- and descriptor-close exception safety —
   accepted.

The subsequent security remediation and re-review remediation are also
complete. Independent re-review confirmed that BS-3 now requires positive
post-cleanup non-authorization for every rule class, the retry bound no longer
treats pathname absence as authorization proof, and contradictory cleanup
authorization evidence fails closed. The reviewer recommends acceptance for
continued development. Two additional validator observations are recorded in
the existing handback as non-blocking production-review hardening; they do not
justify another remediation or documentation chain.

Peter accepted the repository-managed Polkit `tmpfiles.d` prerequisite on
2026-10-15 after implementation, real-reboot proof, two security remediations
and the focused restore-path hardening. The package fragment and its bounded
install/verify/remove operator path are complete for continued development.
Production activation still requires an explicit decision on the transient
inspection-failure risk and the final production security review of the
completed series. This acceptance authorizes none of those activation steps.

[Accepted role-series handback](route-3-hold-role-implementation-handback.md) ·
[Latest remediation result](route-3-hold-role-implementation-handback.md#current-security-remediation-2--2026-10-14) ·
[Completed backstop handback](route-3-backstop-role-implementation-handback.md) ·
[Completed stop-post handback](route-3-stop-post-role-implementation-handback.md) ·
[Accepted adapter handback](route-3-manager-polkit-implementation-handback.md).

All levels of testing are authorized on `oracle-test`, including SSH and sync,
dependency installation, builds, network tests, root/systemd operations,
PostgreSQL work, destructive migration/recovery drills, failure injection,
restart/rollback exercises, and end-to-end tests. The disposable host may be
reset as needed.

Still prohibited without a separate explicit instruction: production or
staging mutation, use or disclosure of real secrets or player data, weakening
authorization, and destructive operations outside the disposable environment.

The role implementation sequence and repository-managed Polkit `tmpfiles.d`
prerequisite are closed. Peter accepted the first real, non-production Package
5.0 consumer, static SA-1 `start` through DI-2, on 2026-10-15 after independent
Codex re-review found no blocking issue in the second remediation. Malformed
`ControlOk` payloads now fail closed as `effect-not-confirmed` with exit 22;
the focused and complete Route 3 disposable-host suites passed. The accepted
implementation evidence remains in the
[`start` handback](route-3-start-role-implementation-handback.md).

Peter accepted static SA-2 `stop` through the existing narrow stop-unit boundary
for continued non-production development on 2026-10-16. Independent Codex
re-review found no blocking issue after the refusal-diagnostic, typed-result and
test-only host-job assertion remediations. The exact-unit unrelated-job proof,
the complete SA-2 host module and the focused application/artifact suites passed
on `oracle-test`; see the [`stop` handback`](route-3-stop-role-implementation-handback.md).
That acceptance did not itself assign another slice. Peter has now approved the
recommended sequence and assigned RT-1 `consume` as the next bounded Package
5.0 implementation slice under the
[`consume` implementation prompt](route-3-consume-role-implementation-claude-prompt.md).
Claude implemented the PID-1 `ExecStartPre=+` role as an **uncommitted
candidate** and exercised it fully on `oracle-test`
([handback](route-3-consume-role-implementation-handback.md)). Independent Codex
review found two blocking failure-path defects: an evidence failure while
recording an already-selected failure can bypass grant-priority processing, and
an unexpected CQ-5 exception can silently run PK/2 twice. Peter has assigned
one bounded remediation under the
[`consume` review-remediation prompt](route-3-consume-role-review-remediation-claude-prompt.md).
The remediation is complete. Independent Codex re-review found no blocking
issue: the focused set passed with 2062 tests and 2 documented resource-limit
skips, the fresh controlled-artifact root/systemd consume module passed all 14
tests, compilation and diff checks passed, and separate host cleanup inspection
was clean. Peter accepted RT-1 for continued non-production development on
2026-10-17.

Peter now assigns RT-5 `attest` as the next bounded Package 5.0 slice under the
[`attest` implementation prompt](route-3-attest-role-implementation-claude-prompt.md).
Implement the existing interactive root role through the controlled artifact,
reusing the accepted cleanup engine with trigger `attest` and enforcing its
unit-state precondition before cleanup. Exercise it fully on `oracle-test`,
including real `sudo -n`, refusal while the holder or either backstop unit is in
an active transitional state, same-boot cleanup, a real-reboot
`cleared-by-boot` proof, interruption, exact argument and environment refusal,
artifact integrity and clean teardown. Return one concise handback for
independent review. Do not reopen accepted RT-1 behavior except for a
demonstrated regression.

The controlled vector is:

```text
sudo -n /usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py deact <activation_id> <a2_sha256> attest
```

It accepts only the validated activation and A-2 operands, reads no environment
variable, runs no unit, and must refuse cleanup while the holder, backstop
service or backstop timer is `activating`, `active`, `deactivating` or
`reloading`. Otherwise it runs the accepted cleanup procedure with trigger
`attest`; it must never infer success from missing evidence or an unconfirmed
authorization result.

Claude implemented the role as an **uncommitted candidate** and exercised it fully on
`oracle-test`, including real `sudo -n`, a real kernel reboot and clean teardown
([handback](route-3-attest-role-implementation-handback.md)). Independent Codex
review found two blocking issues: RT-5 can publish `st1-verified` after required
old-boot identity or trusted `/run` evidence is missing, and the handback's
abbreviated commands are not independently reproducible. Peter assigns one
bounded correction under the
[`attest` review-remediation prompt](route-3-attest-role-review-remediation-claude-prompt.md).
Claude completed that remediation and returned the candidate for independent Codex
re-review (appended section of the handback). Two later reviews each found a further
false-success path; the latest, a missing mandatory tree-P `tree-intent`/`tree-linked`,
was remediated under the
[third review prompt](route-3-attest-role-review-remediation-r3-claude-prompt.md) and
returned for independent Codex re-review. Nothing here records acceptance.

That re-review found one further blocking false-success path: the exact tree-P
check discards file-member mode/digest/size, collapses duplicate directory
declarations and ignores undeclared directory identities, allowing canonical
changed-boot evidence with an inexact production-tree history to publish
`st1-verified`. Peter assigns one bounded correction under the
[`fifth attest review-remediation prompt`](route-3-attest-role-review-remediation-r5-claude-prompt.md).
Claude completed it and returned the candidate for independent Codex re-review
(**Fifth review remediation** in the handback). Nothing here records acceptance.

Independent Codex re-review found no remaining implementation-quality blocker.
The fifth correction preserves and compares the complete ordered tree-P member
and identity history, derives the expected file facts from validated A-2 data,
and remains scoped to changed-boot RT-5; the reviewer independently reproduced
the focused **2369 passed, 2 documented environment skips** result against
matching files on `oracle-test`.

Peter's 2026-10-18 evidence-policy clarification applies the canonical
`.agents/AGENTS.md` handoff standard: evidence must establish material
correctness, safety and regression claims, but a handback is not a terminal
transcript. The fifth section's summarized commands are therefore a
non-blocking documentation variance, not grounds for another remediation or
full-suite cycle. Reliable statuses and disclosed failures/skips remain
required, as do exact invocations where privilege, environment, ordering,
reboot phases or status propagation materially affect the claim.

Peter accepted RT-5 for continued non-production development on 2026-10-18.
Peter now assigns Claude the first bounded non-root executor slice under the
[`executor OC implementation prompt`](route-3-executor-oc-implementation-claude-prompt.md).
Implement the real OS-6 interruption path: as unprivileged `ubuntu`, read the
fixed capture unit and the activation-derived consume journal, make the route
available only when exact OC-1/OC-2/OC-3 evidence holds, and then invoke the
accepted static SA-2 `stop` role at most once through its fixed `sudo -n`
controlled-artifact vector. Every uncertain, malformed, stale-looking or
unavailable input fails closed without privilege or mutation; CX-3 leaves the
pass running without a grant.

Exercise the slice fully on `oracle-test`, including the real unprivileged to
`sudo -n` boundary, active success, activating/start-pre refusal, invocation
mismatch, missing/torn/consumed-less journals, SA-2 uncertainty, absence of
retry, unrelated-unit isolation and clean teardown. Return one concise handback
for independent Codex review.

The full coordinator, start orchestration, automatic attestation, production
capture-unit/executor installers, production or staging activation,
migration/cutover and RB-1 remain outside this assignment. Do not reopen the
accepted roles absent a demonstrated regression and do not replace executable
testing with another proof-document chain.

Claude's executor candidate established a real kernel limit: a member in
uninterruptible sleep can remain populated after bounded `cgroup.kill` rounds.
Peter therefore approves in principle a changed lifecycle contract under which
an unsettled but still-contained invocation may be transferred to a persistent
owner that blocks orchestration and continues recovery until the boundary is
empty.

The second-remediation candidate did not satisfy that contract and was not
accepted at that stage. Independent Codex review reproduced an exception path in which all
kill rounds completed, the hand-off marker write failed, the exception
propagated, the scope closed and the member remained alive. The normal
`UNSETTLED` result has the same defect when the marker cannot be written. The
candidate also has no already-running persistent supervised owner; its host
test calls one-shot recovery manually and does not prove owner restart or
continuous recovery.

Peter therefore kept that candidate blocked and assigned Claude one bounded correction under
the [third executor review-remediation prompt](route-3-executor-oc-review-remediation-r3-claude-prompt.md).
Within the approved ownership contract, establish durable recoverable ownership
before privileged launch, retain it on every return and exception path, and
prove on `oracle-test` a real persistent owner's restart, continued
orchestration block, no duplicate SA-2 invocation and eventual cleanup. Update
the existing executor handback in place; do not create another handback.
Peter had also directly assigned the inactive executor supervisor package (the
service fragment, `tools/executor_supervisor_install.py` and the provisioning
runbook); its ownership-race and code-trust defects are corrected under the
[fourth executor review-remediation prompt](route-3-executor-oc-review-remediation-r4-claude-prompt.md),
and its package-boundary defects under the
[fifth executor review-remediation prompt](route-3-executor-oc-review-remediation-r5-claude-prompt.md),
in which Peter selected a root-owned system-service wrapper for the persistent
supervisor (running as the unprivileged `freedom-executor` account; the
dedicated lingering user manager still owns the transient invocation services).
This records the assignment, not acceptance. Installing or activating that
package in production or staging, and any other production-installer work,
remain unauthorized.

On 2026-10-21 Peter approved the independent-review recommendation to preserve
that topology and correct four defects in place: a request write that fails is
an ambiguous handoff rather than proof of non-delivery; readiness follows the
serving-thread start; installer verification covers effective drop-ins and
execution identity; and the PATH-only transient environment is defense in depth,
not an atomic security premise. The privileged premise is the fixed sudoers/SA-2
argv, Python `-I -S`, and the root-owned `stop` artifact's environment-free path.
The bounded correction and full `oracle-test` testing are authorized and append
to the existing handback. This is not acceptance; independent review remains
required and production/staging activation remains prohibited.

Claude returned that implementation. Independent Codex review reproduced 484
focused executor passes, 325 SA-2/artifact passes with two documented RLIMIT
skips, 346 documentation checks and all 12 root/systemd package cases. It also
reproduced a blocking post-write interruption path: `KeyboardInterrupt` from
`sendall(PROTOCOL_REQUEST)` escapes rather than returning `HANDED_OFF`. Peter
therefore assigns one direct correction under the
[R6 review-remediation prompt](route-3-executor-oc-r6-review-remediation-claude-prompt.md),
including deterministic write/reply/close interruption regressions and current-
state documentation reconciliation. Nothing here accepts the candidate.

The selected architecture is a restartable supervisor (a root-controlled
system service running as the dedicated unprivileged account) plus one separate
transient service per admitted invocation, owned by that account's systemd user
manager. The supervisor durably commits exclusive prepared state before its
single `StartTransientUnit` call; that call launches the exact fixed `sudo -n`
vector directly inside the new unit's cgroup. The supervisor is not the
invocation's cgroup owner and can restart while the user manager retains a
stuck invocation. `oracle-test` has systemd 259, unified cgroup v2 and an active
`ubuntu` user manager; its current `Linger=no` may be changed only temporarily
for the proof and must be restored. Production linger or system-service
installation remains a later decision.

[Active delivery plan](../project-management/active-delivery-plan.md) ·
[Phase 5 packages](../implementation-plan.md#phase-5--existing-automation-migration) ·
[Disposable test server](../operations/disposable-test-server.md) ·
[Reset handback](implementation-first-reset-handback-2026-10-12.md) ·
[Archived predecessor handover](Handover-information-through-2026-10-13-route-3-hold-active.md) ·
[Historical review records](README.md) ·
[Handover archive index](handover-archive/README.md).
