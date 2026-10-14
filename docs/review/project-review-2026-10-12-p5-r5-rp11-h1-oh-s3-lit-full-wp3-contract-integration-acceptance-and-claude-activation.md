# WP-3 contract-integration acceptance and Claude activation — 2026-10-12

Decision owner: Peter Duscha, Product Owner and Acceptance Authority

Executor: Claude

Independent reviewer after return: Codex

## Decision

Peter Duscha explicitly accepts and activates exactly:

- [WP-3 contract-integration Claude prompt](phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-contract-integration-claude-prompt.md);
- work ID `C-P5.0-R5-RP11-H1-OH-S3-RT3-WP3-CI1-20261012-26`;
- 358 lines and 18,188 bytes; and
- SHA-256
  `894470357ed0fa1ed6c0fba251c471a9e549b7412068b1c1009984580ea91fce`.

Peter adopts decisions D-1 through D-6, D-9 and D-10 exactly as fixed in that
prompt and appoints Claude to execute the exact prompt once. The accepted
[independent Gemini review](project-review-2026-10-12-p5-r5-rp11-h1-oh-s3-lit-full-wp3-contract-integration-assignment.md)
records zero Blocking, zero Important and zero Optional findings.

## Adopted decision package

- D-1: use the system message bus for DI-1 through DI-5 and DI-S.
- D-2: use the accepted PID/start-time/uid Polkit request shape.
- D-3: adopt the accepted pre-mutation refusal and error mapping, including
  `effect not confirmed` and no silent retry.
- D-4: use completion-observation design O-C.
- D-5: retain the PID/start-time/uid subject and its known race residual.
- D-6: adopt the complete DI-5 normal-reply and error mapping.
- D-9: distinguish loaded already-inactive from not-loaded units.
- D-10: omit `TimeoutStartUSec` from the DI-3 backstop service contract.

These decisions are adopted only with the exact scope, rationale, failure
semantics and retained risks in the accepted prompt. D-7, D-8 and D-11 through
D-14 remain undecided. No Q3 question is closed by this activation, and Q6-6
and Q6-7 remain unanswered.

## Bounded authority

Claude may execute the exact prompt once, producing only the cumulative WP-3
interface-contract correction, the named contract-integration handback, the
four exact return snapshots and archive rows, and the four bounded current-state
pointer updates required by the prompt.

Authority is repository-documentation integration only. No network, SSH,
`oracle-test`, production, staging, Foundry, database, retained-evidence,
secret, credential, host-installation or package access is authorized. No
application, configuration, infrastructure or launcher edit, source retrieval,
implementation, package installation, service/database operation, test, build,
formatter, hook, cleanup outside assignment-created files, runtime/service
activation, rollback, commit or push is authorized. Do not touch the R5 or H-0G retained
paths.

## Preserved boundary and terminal gate

Baseline v1.8, F-1 B2-F, both lifecycle acts in, B3-OUT, effective EX-1/EX-2
and no EX-3 remain unchanged. Concrete Route 3 remains unestablished, LIT-FULL
is not selected for implementation, BC-2 remains a later WP-9 question and
WP-4 through WP-7 remain separately gated and unauthorized. Residual `R-M.1`
retains its accepted limited provenance basis.

The accepted WP-3 HARD STOP remains in force outside this exact integration
authority. Authority ends at the prompt-defined `PASS`, `HARD STOP` or
`INVALID RUN`. The returned integration requires independent Codex review and
Peter's later gate decision before any WP-4 authority is considered.

## Invocation

```text
Execute the exact accepted assignment in docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-contract-integration-claude-prompt.md once. Proceed autonomously through every authorized repository-documentation step until the prompt-defined terminal state. Do not access any network, host, retained evidence or later work package. Write the complete contract-integration handback and reconcile the four current-state pointers before stopping.
```
