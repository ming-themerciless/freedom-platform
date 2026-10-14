---
name: handoff-checklist
description: Verify and report a change before handing it to a maintainer or reviewer. Use when finishing a milestone or scoped slice, writing a handback or submission, preparing a review gate, or about to claim work is complete. Covers the verification order, the required report contents, and the claims that may not be made.
---

# Handing off a change

**This skill is a procedural aid, not a source of rules.** The authority is
`.agents/AGENTS.md` "Contributor and agent workflow / Before handing off" and
`docs/implementation-plan.md` §16.3. If this file disagrees with
either, they win.

## Verify, in this order

1. Run narrow relevant tests, then the full available suite. Use the
   `run-suites` skill; it carries the skip-count trap and the serial rule.
2. Run the configured formatter, linter and type checker. Distinguish
   **unavailable or unconfigured tooling from a pass** and say which it was.
3. Review the diff for secrets, generated files, unrelated changes, unsafe logs
   and migration reversibility.
4. Check `git status` and confirm unrelated user changes are preserved.
5. Run `git diff --check`.

## Concise handback

From `.agents/AGENTS.md` and plan §16.3:

* behavior implemented and files changed;
* **exact commands run, the interpreter used, and the exact results**;
* **checks not run, and why**;
* configuration, migration, deployment and recovery effects;
* remaining production risks; and
* the next implementation action.

Do not add reading ledgers, file hashes, prompt histories or per-question proof
records unless Peter explicitly asks for them.

## Claims that may not be made

* **Never claim a check passed unless it was actually run.** A figure from a
  different tree or host is not evidence about this one.
* A passing test of an unfixed tree is a **defect reproduction**, not a passed
  safety invariant. Label it as such.
* Do not close a finding on the implementer's authority. Findings are closed by
  the reviewer or the Acceptance Authority, never by a passing suite.
* Do not treat a green suite as a gate approval, a risk acceptance, or an
  execution authorization.
* Separate **observations, assumptions, proof obligations, proposed decisions
  and unresolved dependencies**. Do not present one as another.

## Continue or stop

Continue through authorized non-production slices. Stop and ask a maintainer
when a decision changes product scope, production data authority,
authorization/privacy policy, destructive production behavior, irreversible
architecture or production activation. Blocking safety findings must be fixed
before the affected production boundary is crossed.
