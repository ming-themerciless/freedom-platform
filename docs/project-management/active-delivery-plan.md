# Active delivery plan — implementation-first reset

Status: approved and active; static SA-2 `stop` accepted 2026-10-16
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

## Current implementation slice

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
further Package 5.0 slice is assigned by that acceptance.

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

## Acceptance criteria

- every implemented operation row used by RT-2, RT-3 and RT-4 is traced to an
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
- the handback contains only the implemented behavior, files changed, exact
  test commands/results, remaining production risks and the next action.

## Finish line

The series ended with all three PID-1 role vectors performing their real behavior on
`oracle-test`, no production activation, Peter's 2026-10-14 acceptance based on
the running system, and completed independent re-review of the subsequent
security remediation. The selected `tmpfiles.d` ordering is installed, proved
across a real reboot and accepted for continued development. Before production
activation, decide the transient inspection-failure risk and complete the final
production security review.
Additional source-proof work is not an allowed substitute for implementation
and executable tests.
