# Project governance

Status: controlled baseline v1.9, accepted 2026-10-12. Phase 3 and Phase 4
remain approved. Phase 5 development and all testing levels on the disposable
server are authorized.

- Current state: [status.md](status.md)
- Current work: [active-delivery-plan.md](active-delivery-plan.md)
- Current authority: [Handover information](../review/Handover%20information)

Historical status and handover states remain in their archive indexes. Dated
research, prompt, review and handback records are historical unless the current
handover links them as controlling material.

## Operating model

Peter Duscha is Product Sponsor, Acceptance Authority, Product Owner, Data
Owner, Operations Owner and Delivery Lead. Agents implement and review; Peter
retains product and production accountability.

Implementation is the default once a slice appears in the active delivery plan.
Reversible technical choices do not require a separate gate. Escalate before:

- changing product scope or production data authority;
- changing authorization or privacy policy;
- making an irreversible architecture or migration choice;
- performing a destructive production/staging operation; or
- activating a feature in production.

## Ready and done

A slice is ready when its intended behavior, safety boundary and executable
acceptance tests are clear enough to begin. Missing speculative detail is not a
blocker; implement it reversibly and test it.

A slice is done when:

- the intended behavior works;
- relevant narrow and full suites pass with skips explained;
- failure, authorization and recovery behavior is tested in proportion to risk;
- configuration, migration and operational notes are current; and
- the concise handback records results and remaining production risks.

## Testing authority

Every testing level is authorized on `oracle-test`: SSH/sync, packages, builds,
network, root/systemd, PostgreSQL, destructive database and migration drills,
failure injection, restart, rollback/recovery and end-to-end testing. The host
is disposable and may be reset.

This authority never includes production/staging mutation or copying real
secrets or player data to the test host.

## Reviews and gates

Review code and executable evidence at meaningful package boundaries. An
independent review is mandatory before production activation and for security,
authorization/privacy, migration/data-integrity, financial/rules,
Foundry-write and destructive cutover boundaries. It is not required for every
reversible implementation parameter or documentation update.

A production gate has four outcomes: approved, conditionally approved,
rejected, or deferred. Peter records the decision. Blocking security, data-loss,
authorization, privacy, financial-integrity or production-reliability findings
must be fixed or explicitly risk-accepted before production use.

## Documentation

Keep documentation proportional and current:

- one active delivery plan;
- code and tests as the primary technical record;
- short ADRs for durable architecture choices;
- one concise handback per meaningful implementation slice; and
- operations/migration/recovery instructions where behavior requires them.

Do not create byte-identity ledgers, exhaustive reading logs, prompt activation
records, per-question closure packages or recursive remediation chains unless
Peter explicitly requests them.
