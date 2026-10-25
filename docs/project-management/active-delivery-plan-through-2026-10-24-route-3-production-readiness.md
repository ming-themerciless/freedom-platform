# Active delivery plan — implementation-first reset

Status: approved and active; Route 3 production-readiness checklist completion independently re-reviewed 2026-10-24
Owner and acceptance authority: Peter Duscha
Baseline: v1.9

## Goal

Resume delivery of the Freedom Blades Platform through small implementation
increments and comprehensive testing. Research documents support the work but
are not prerequisites that must be made formally complete.

## Working rules

- Implement the smallest useful vertical slice, test it, review the result and
  continue.
- Reversible technical details may be chosen by the implementer and recorded in
  code, tests or a short ADR. They do not require a separate decision package.
- Ask Peter before changing product scope, production data authority,
  authorization/privacy policy, destructive production behavior or an
  irreversible architecture choice.
- A discovery gap blocks implementation only when proceeding could expose a
  secret, damage non-disposable data, bypass authorization, or make recovery
  impractical.
- Do not create proof chains, byte-identity ledgers, prompt-review cycles or
  per-question closure packages unless Peter explicitly asks for them.
- Judge implementation evidence by whether it establishes material correctness,
  safety and regression claims. Routine command transcription is not a gate;
  reliable statuses, disclosed failures/skips and exact invocations when their
  special environment or sequencing affects the claim remain required.

## Current implementation slice

The final portability follow-up has returned and independent Codex focused
re-review found no remaining implementation defect. The exact checklist matched
between the workspace and `oracle-test`; **53/53** focused tests, `bash -n` and
`git diff --check` passed there, while the structural run reproduced **127
passed, 1 known baseline allowlist failure**. Codex recommends acceptance for
continued non-production development. Peter's acceptance and transient-risk
decision remain separate; production/staging access, inspection and activation
remain prohibited.

Codex's review of the fifth return found one bounded defect: item 5b can print
`COMPLETE` after a directory search or unit query fails. Peter assigns Claude a
direct completion correction under the existing accepted fifth-remediation
scope: make either failure `INCOMPLETE`, add the two focused regressions, and
run only the focused checklist, shell-syntax, directly affected structural and
diff checks. This is not a sixth remediation round and no full-suite rerun is
required. The candidate and transient-risk decision remain unaccepted;
production/staging access, inspection and activation remain prohibited.

After Claude returned the third remediation, independent Codex re-review found
one remaining strict enablement-observation defect, two secret-safe/fixed-account
defects in checklist item 5b, and stale current-state headings. Peter assigned
the bounded [fourth remediation](../review/route-3-production-readiness-review-remediation-r4-claude-prompt.md).
Codex's review of that return then found a non-reproducible host-state discrepancy, residual status masking in checklist item 5b and a missing fourth-return section; Peter assigned the bounded [fifth remediation](../review/route-3-production-readiness-review-remediation-r5-claude-prompt.md), now returned. Claude has returned the **fifth** production-readiness review remediation for independent Codex re-review (handback "Fifth review remediation return", 2026-10-23): checklist item 5b (and the identical path-set/pid copies in items 5 and 11) now fails closed on every fact-gathering status (root and account NSS records validated without a masking pipeline, the account-context `unit-paths` result usable only at status 0, every append/sort/search reported, scratch removed by an `EXIT` trap), proved by 47 executable checks and a host decoy probe; `oracle-test` was already in the documented canonical state when inspected (the root-owned Python 3.14 state Codex saw was not reproducible and its cause is not established) and is unchanged apart from removed scratch; the fourth-return section Codex found absent is present in the tree, but its figures are replaced by fresh final-tree runs. No installer or product code changed. Not accepted; no transient-risk decision; no production/staging access, inspection or activation.

(History) Claude has returned it for independent Codex re-review (handback "Fourth review remediation return", 2026-10-23): enablement is observed strictly (only an absent wants link is "disabled"; an I/O or permission error, a foreign object or an unexpected target is `enablement-unavailable`, exit 13, before an upgrade changes anything and `recovery-incomplete`, exit 15, after it), checklist item 5b inspects only the fixed `freedom-executor` account and prints only allowlisted unit properties (never a description; an ambient `ACCOUNT` is ignored), and the current-state headings are reconciled. Not accepted; no transient-risk decision; no production/staging access, inspection or activation.
The candidate remains unaccepted; no risk decision or production/staging
access, inspection or activation is authorized.

Peter assigns Claude one bounded Route 3 production-readiness and security-gate
preparation under the
[accepted prompt](../review/route-3-production-readiness-claude-prompt.md).
It uses the accepted executor OC R6 candidate and complete inactive privileged
chain, performs an exact-path clean lifecycle rehearsal on `oracle-test`, and
prepares the transient inspection-failure decision plus the production-specific
read-only fact checklist for independent Codex review. It authorizes no
production/staging access or activation and makes no risk-acceptance decision.
Claude has returned it for independent Codex review
([handback](../review/route-3-production-readiness-handback.md)); it is not accepted. Codex found two blocking installer defects
(unverified restore failure; sudo run-as wider than documented), an inaccurate residual-lifecycle analysis, incomplete
production-inspection methods and unfinished evidence; Peter assigned the bounded
[review remediation](../review/route-3-production-readiness-review-remediation-claude-prompt.md), which Claude has returned
for independent Codex re-review (handback §0). A second independent review reproduced three installer recovery gaps
(manager exceptions bypassing upgrade recovery; a failed upgrade not restoring a disabled unit's enablement; removal losing a
loaded owner without status 15) and two defects in the proposed production inspection methods (a process listing that
could disclose secrets; non-executable command shapes). Peter assigned the bounded
[second remediation](../review/route-3-production-readiness-review-remediation-r2-claude-prompt.md), which Claude has returned
for independent Codex re-review (handback "Second review remediation return"). Still not accepted; no risk decision; no
production/staging access. Codex's re-review found two remaining recovery-verification defects (unknown `ActiveState` values
can compare equal; a non-zero enable/disable restoration command is discarded when its link effect matches) and one production
inspection gap (the operator's user-unit paths are enumerated instead of the dedicated account's). Peter assigns the bounded
[third remediation](../review/route-3-production-readiness-review-remediation-r3-claude-prompt.md). Claude has returned it for independent Codex re-review (handback "Third review remediation return"): strict unit-state observation, conjunctive enable/disable restoration check, and an executed account-context user-unit inspection (item 5b). Still not accepted; no risk decision; no production/staging access, inspection or activation.

The Route 3 manager/Polkit adapter represented by DI-1 through DI-6 and DI-S
was accepted on 2026-10-13. Peter Duscha accepted the complete inactive role
series on 2026-10-14 after independent review: shared cleanup and `stop-post`,
`backstop`, and `hold`, including the GRR inspection- and descriptor-close
exception-safety remediations. The historical WP-1 through WP-3 material
supplies the detailed operation contract but is not a documentation gate.

The later Route 3 security remediation is independently re-reviewed and has no
remaining blocker to continued development. Its BS-3, retry-bound and durable
cleanup-evidence corrections are complete. Two validator observations remain
non-blocking hardening for the production security review and must not become a
fourth prompt/review/remediation chain.

The Polkit `tmpfiles.d` prerequisite, its safe install/verify/remove boundary
and a real reboot proof on `oracle-test` are implemented (see
[handback](../review/route-3-polkit-tmpfiles-installer-handback.md)) and were
accepted by Peter Duscha on 2026-10-15 after the effective-configuration,
removal-race and restore-path remediations. This acceptance does not authorize
production or staging activation and does not reopen the completed role
implementation.

Claude implemented the first real Package 5.0 consumer, static SA-1 `start`,
through DI-2. After the environment-read, duration, denial-proof and malformed-
success remediations, independent Codex re-review found no blocking issue and
Peter accepted SA-1 for continued non-production development on 2026-10-15. See the
[`start` handback](../review/route-3-start-role-implementation-handback.md) and
its [assignment](../review/route-3-start-role-implementation-claude-prompt.md).
Static SA-2 `stop` through the existing narrow stop-unit boundary was then
implemented, remediated and independently re-reviewed. Peter accepted it for
continued non-production development on 2026-10-16; see the
[`stop` handback](../review/route-3-stop-role-implementation-handback.md). No
further Package 5.0 slice was assigned by that acceptance. Peter subsequently
approved the recommended continuation and assigned RT-1 `consume` as the next
bounded slice, with implementation and full `oracle-test` testing under its
[`Claude prompt`](../review/route-3-consume-role-implementation-claude-prompt.md).
Claude's uncommitted candidate and
[handback](../review/route-3-consume-role-implementation-handback.md) received
independent Codex review. Its two blocking failure-path defects were corrected
under one bounded
[remediation](../review/route-3-consume-role-review-remediation-claude-prompt.md).
Independent Codex re-review found no blocking issue, and Peter accepted RT-1
for continued non-production development on 2026-10-17. Peter then assigned
RT-5 `attest` as the next bounded slice. After implementation and five bounded
false-success corrections, independent Codex re-review found no remaining
implementation-quality blocker. Peter accepted RT-5 for continued
non-production development on 2026-10-18. Peter subsequently assigned the
non-root executor and its OC-1/OC-2/OC-3 checks; sequence item 10 records its
completed remediation chain and Peter's 2026-10-22 acceptance for continued
non-production development. The production-readiness preparation above is the
next assigned slice.

Implementation defaults may be refined by tests. Initially:

- use the system bus;
- preserve fail-closed errors and never silently retry an unconfirmed mutation;
- select explicit systemd job modes in code and cover them with integration
  tests instead of relying on command-line defaults;
- report a completed stop as `ok(stopped)` rather than claiming whether it was
  causally active or already stopped when the API cannot distinguish that;
- treat uncertain pre-mutation error classifications as errors until a test or
  supported API contract proves a narrower refusal safe; and
- keep the existing PID/start-time/uid Polkit subject for the prototype while
  retaining the documented race risk for the production decision.

## Implementation sequence

1. Implement the shared cleanup engine and `deact … stop-post`; exercise its
   attribution, removal, journal, record, authorization and interruption paths.
   **Complete 2026-10-13.**
2. Implement `backstop` over that cleanup engine, including BS-1 through BS-4,
   bounded retries and all three DI-4 disarm sites. **Complete 2026-10-13.**
3. Implement `hold` after both cleanup rungs exist, including activation,
   grant publication, verification, hold-loop observation and inline release.
   **Complete and accepted 2026-10-14.**
4. After each slice, run focused fake-boundary and real-host tests, clean the
   host, and compare the final tree against the established bot, web and Foundry
   baseline.
5. Review each security-sensitive slice before production activation. Ordinary
   non-production implementation may continue while non-blocking review
   comments are addressed.
6. Implement the first Package 5.0 consumer, static SA-1 `start`, through DI-2.
   **Implemented by Claude, independently re-reviewed and accepted by Peter
   2026-10-15.**
7. Implement static SA-2 `stop` through the existing narrow stop-unit boundary.
   **Implemented by Claude, independently re-reviewed and accepted by Peter
   2026-10-16.** See the [handback](../review/route-3-stop-role-implementation-handback.md).
8. Implement RT-1 `consume` as the capture unit's PID-1 `ExecStartPre=+` role,
   including the one-shot claim, grant-priority removal, CQ-4 preconditions,
   negative authorization proof and durable `consumed` commit. **Implemented,
   remediated, independently re-reviewed and accepted by Peter for continued
   non-production development on 2026-10-17**
   ([handback](../review/route-3-consume-role-implementation-handback.md)).
9. Implement RT-5 `attest` as the controlled interactive root role, reusing the
   accepted cleanup engine with trigger `attest` and enforcing its unit-state
   precondition before cleanup. **Assigned by Peter on 2026-10-17 under the
   [implementation prompt](../review/route-3-attest-role-implementation-claude-prompt.md).**
   Claude implemented it as an uncommitted candidate
   ([handback](../review/route-3-attest-role-implementation-handback.md));
   independent Codex review found a false `st1-verified` path when required
   boot evidence is missing and non-reproducible command evidence in the
   handback. One bounded
   [review remediation](../review/route-3-attest-role-review-remediation-claude-prompt.md)
   was completed and returned for independent Codex re-review; a third
   [remediation](../review/route-3-attest-role-review-remediation-r3-claude-prompt.md)
   (mandatory tree-P evidence) was likewise returned for re-review, as was a fifth
   (lossless exact tree-P member and identity history). Independent Codex
   re-review found no remaining implementation-quality blocker: the final code
   keeps and compares the complete ordered tree-P history, and the reviewer
   independently reproduced the focused **2369 passed, 2 documented environment
   skips** result. The fifth handback's
   summarized rather than literal routine commands are non-blocking under the
   governing evidence standard. Peter accepted RT-5 for continued
   non-production development on 2026-10-18. The non-root executor and
   OC-1/OC-2/OC-3 remain outside this accepted slice.
10. Implement the first real non-root executor slice: read the fixed capture
    unit and activation-derived consume journal as `ubuntu`, establish exact
    OC-1/OC-2/OC-3 fail-closed, and invoke the accepted SA-2 `stop` role at most
    once through its fixed `sudo -n` vector. **Assigned by Peter on 2026-10-18
    under the [executor OC implementation prompt](../review/route-3-executor-oc-implementation-claude-prompt.md).**
    The fail-closed OC gate was implemented, but lifecycle completion was
    **blocked after independent review on 2026-10-19**. Peter approved in
    principle transfer of a still-contained unsettled invocation to a
    persistent owner, but does not accept the current best-effort post-launch
    marker. The assigned correction had to establish durable recoverable ownership
    before privileged launch, retain it on every normal and exceptional path,
    and prove a real supervised owner's restart, continued blocking, no
    duplicate SA-2 invocation and eventual cleanup. Peter assigns this bounded
    correction under the [third executor review-remediation prompt](../review/route-3-executor-oc-review-remediation-r3-claude-prompt.md).
    The selected design uses a restartable supervisor and a separate transient
    service for each invocation, owned by the dedicated account's user manager;
    durable exclusive prepared state precedes the sole `StartTransientUnit`
    call, which launches the exact fixed sudo vector directly in its owned
    cgroup. For the inactive package Peter selected a root-owned system-service
    wrapper for the persistent supervisor (running as the unprivileged
    `freedom-executor` account). Production lingering/installation remains
    separately gated.
    The full coordinator, start orchestration, automatic attestation and
    production/staging installation or activation remain later work. The
    inactive supervisor package (unit fragment, installer tool and provisioning
    runbook) was directly assigned by Peter and is corrected under the
    [fourth](../review/route-3-executor-oc-review-remediation-r4-claude-prompt.md) and
    [fifth executor review-remediation prompt](../review/route-3-executor-oc-review-remediation-r5-claude-prompt.md);
    that is not acceptance and authorizes no installation or activation.
    Peter accepted and assigned one further bounded implementation correction on 2026-10-21: ambiguous
    request-write ownership, readiness ordering and effective loaded-unit checks
    are repaired, while PATH-only member environment becomes defense in depth
    rather than an atomic security premise. The fixed sudoers/SA-2 vector,
    Python `-I -S` and the root-owned `stop` artifact's environment-free path
    are the privileged invariant. Claude returned that candidate under the
    [accepted R6 implementation prompt](../review/route-3-executor-oc-r6-implementation-claude-prompt.md).
    Independent Codex review reproduced the principal suites but found that a
    `KeyboardInterrupt` or other `BaseException` at or after the request-write
    boundary can escape instead of becoming `HANDED_OFF`. Peter assigns the
    direct correction and current-document reconciliation under the
    [R6 review-remediation prompt](../review/route-3-executor-oc-r6-review-remediation-claude-prompt.md).
    Claude returned that remediation with the corrected ownership boundary.
    Independent Codex re-review found no remaining implementation defect but
    found the two real-socket proofs nondeterministic (one `recv` may return a
    prefix) and the current-state text stale. Peter accepted the
    [second remediation prompt](../review/route-3-executor-oc-r6-review-remediation-r2-claude-prompt.md)
    and assigned Claude the correction; Claude returned it for independent
    re-review. Codex found no implementation or production-safety defect. Peter
    classified the remaining test-helper surplus overclaim as non-blocking and
    assigned the optional
    [socket-proof hardening](../review/route-3-executor-oc-r6-nonblocking-test-hardening-claude-prompt.md),
    followed by one bounded ordering correction. Claude returned that final
    test-only correction; independent Codex re-review found no remaining
    finding and reproduced the focused **511 passed, 5 documented host-only
    skips** result on `oracle-test`. Peter accepted the cumulative executor OC
    R6 candidate for continued non-production development on 2026-10-22. Peter
    then assigned the production-readiness preparation described above;
    production/staging access or activation remains prohibited.

## Acceptance criteria

- every implemented operation row used by RT-1 through RT-4 is traced to an
  executable test or a named real-host check;
- cleanup never removes an unattributed, damaged or foreign object;
- mutation failures are fail-closed and unconfirmed manager effects are never
  silently retried or promoted to success;
- authorization failures do not become successes, and a live grant is removed
  before cleanup performs slower persistent work;
- disposable-host tests cover success, malformed evidence, interruption,
  timeout, duplicate/concurrent calls, service restart and cleanup/recovery;
- no new bot, web or Foundry failure/error is introduced relative to the
  established baseline, and skips are explained;
- no production/staging service or real player data is touched; and
- the handback contains only the implemented behavior, files changed, material
  test/check results and skips, remaining production risks and the next action,
  with exact commands only where invocation details affect what is proved.

## Finish line

The accepted inactive-role series ended with its three PID-1 vectors performing
their real behavior on `oracle-test`, no production activation, Peter's
2026-10-14 acceptance based on the running system, and completed independent
re-review of the subsequent security remediation. The selected `tmpfiles.d`
ordering is installed, proved across a real reboot and accepted for continued
development. RT-1 `consume`, RT-5 `attest` and the cumulative executor OC R6
candidate are accepted. The active production-readiness slice must now exercise
the exact production-path lifecycle on `oracle-test`, prepare Peter's transient
inspection-failure decision and return for independent production security and
operations review. Production-specific facts then require separately authorized
read-only inspection before any separately authorized activation.
Additional source-proof work is not an allowed substitute for implementation
and executable tests.
