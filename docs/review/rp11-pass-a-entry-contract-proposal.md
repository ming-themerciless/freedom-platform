# RP-11 Pass A entry contract — topology and service-policy decisions accepted; execution remains gated

**G9 update (2026-11-27).** A-6 is met for the digest named in the
[independent MD-5 acceptance](rp11-g9-md5-independent-acceptance.md),
at implementation commit `7373fd405c719f63927eac7c2fc9b87a82d6dbb4`
and manifest v39. This supersedes earlier statements that A-6 is absent.
RP-10 remains open and A1-C is `not_run (RP-10 unmet)`. G10 and execution
retain their separate gates.

**Date:** 2026-11-21 (updated 2026-11-26) · **Current status (2026-11-26):** G1's command/value layer is **accepted for review, NOT authorized to run**. **G8 staged composition is implemented and independently reviewed**; nothing calls its factory and the run path still ends at exit 69. Peter has accepted the single-host `oracle-test` feasibility topology and fixed paths in §0b, selected the service account name `capture`, accepted the measured-conservative timeout policy, and provisionally accepted the reviewed capture mechanism. These decisions settle the corresponding policy choices; they do **not** complete the remaining implementation and evidence. G2/G3/G7 are implemented and reviewed in `pass_a_plan.py` (manifest v35 at review, v37 for the G4 parent contract, now v38 after the G7 real-identity measurement; 24 samples measured with synthetic stand-ins, fixed timeouts and whole-pass bound derived; Codex found no remaining blocking finding) but carry no operational authorization; G4 disposable filesystem acceptance is complete (both roots, 2026-11-25; final suite evidence recorded in plan-handback follow-up 5) (§0b; the 2026-11-24 direct-leaf failure is historical and superseded), and **G6 is technically complete** (final capture-tool digest and non-installing SA-2 reference builds reviewed at `2afca20`; see the G6 note below). G9/G10 and A-2 stay open. The completed canonical source acquisition and non-installing `oracle-test` reference builds are the only source-acquisition and SA-2 build actions; there is still no A-2, AUTH-SYNC, AUTH-READ or AUTH-DBREAD grant, operational Pass A, production/staging access, SA-2 production build or install, activation or probe. The canonical validation of the then-current v37 tree on `oracle-test` was green (2026-11-25: bot 8437 passed, 280 skipped, 0 failures; web 2894 passed, 80 skipped; Foundry Node 171 passed; focused reviewer suite 780 passed; see plan-handback follow-up 5). The earlier v35 (8400/280) and v34 (8327/278) figures were earlier trees. This validation authorizes no `run_pass_a` call or operational pass.

**G6 technical completion (2026-11-26; supersedes every statement below that G6, the final capture-tool digest or the integrity-pinned SA-2 build review is open or incomplete; facts supplied, not re-observed by the recorder):** at commit `2afca2098625a3e09b05d3f51918c82ccebeb543`, two non-installing `oracle-test` reference builds were byte-identical and passed review; Codex review has no blocking finding. Digests and suite figures: [G6 handback follow-up](rp11-g6-preparation-handback.md). **Remaining:** G9/A-6, G10/A-2/AUTH and the actual `run_pass_a`; G1 is accepted for review only. No install, A-2/AUTH, `run_pass_a`, service/activation, staging or production action occurred or is authorized.

**G7 v38 validation and publication (2026-11-25; supersedes every statement below that v38 publication, re-acquisition or remote lock validation is pending; observed by Codex, not re-observed by the recorder):** commit `575218e0410a5c97200fb11c94c8111f5b86e0ce` is published on `docs/platform-plan` and re-acquired clean and detached on `oracle-test`; the v38 hashes matched; the real capture advisory-lock/measurement module passed as uid 992 / gid 978 (12 passed). Canonical bot, final web and Node suites passed; the initial web run had one failure, dispositioned in [plan handback](rp11-pass-a-plan-handback.md) follow-up 10. **Remaining:** G6 final capture-tool digest and integrity-pinned SA-2 build review, G9/A-6, G10/A-2/AUTH and the actual `run_pass_a`. Services, staging and production remain unauthorized.

**G7 v38 review note (2026-11-25; supersedes every G7 review-pending or not-yet-measured statement below, including in §4, and the no-source-acquisition wording above only as to the completed `b279` acquisition):** the authorized acquisition of `b279de11978308b60ee9d491b43952cf9f113871` and the real measurement as `capture` at the selected paths are complete. Per-command timeouts are unchanged at 44 s / 161 s / 30 s, the finalization allowance is 112 s, the whole-pass bound is 2548 s (2638 s with corroboration), and the manifest is v38. Independent Codex review passed after the advisory-lock remediation, with no blocking source finding ([plan handback](rp11-pass-a-plan-handback.md) follow-up 9). The v38 successor steps that remained at review time are complete (note above). This review grants no A-2/AUTH, `run_pass_a`, SA-2, service, staging or production authority.

**Publication note (2026-11-25; supersedes every publication-pending statement below, including in §0b and the G4 row; observed by Codex, not re-observed by the recorder):** commit `b279de11978308b60ee9d491b43952cf9f113871` is published; `refs/heads/docs/platform-plan` on the canonical origin `git@github.com:ming-themerciless/freedom-platform.git` pointed to it. Publication does not authorize source acquisition, `run_pass_a`, A-2/AUTH, SA-2, services, staging or production.

**Historical status block (2026-11-22; superseded for G1 and G8 by the paragraph above; kept as history):** *the single-host `oracle-test` topology of §0b is PROPOSED only — Codex reviewed 2026-11-22 with no blocking documentation finding; still not accepted by Peter and not authorized; G1 stayed NOT ACCEPTED on 2026-11-22. Not implementation of the operational Pass A: G11 and the G12 bootstrap were implemented locally (inert; see the [G11/G12 handback](rp11-entry-bootstrap-g11-g12-handback.md)), and independent Codex review of the code and tests passed with no remaining blocking findings (final focused runs, not canonical suites, Python 3.14.4 `venv-web`: local 520 passed, 2 skipped and 696 passed, 0 skipped; `oracle-test` root 354 passed, 3 skipped; `oracle-test` `ubuntu` 696 passed, 0 skipped). The installed production SA-2 artifact was not changed or rebuilt although `rp11_h1.py` source changed.*

## 0a. Codex review disposition of G1 and Claude remediation note — 2026-11-22

**Disposition (2026-11-22, historical; superseded 2026-11-23 — G1 command/value layer is now accepted for review, not authorized to run): the G1 candidate command set was NOT ACCEPTED.** It remained DRAFT / NOT ACCEPTED / NOT AUTHORIZED at that date, and
**G1 had not passed then.** This section is a short record of one review and one documentation-only remediation. No code,
test, operational or mutating production action occurred. One disclosure corrects an earlier version of this sentence,
which said that no host action was taken: during the remediation Claude ran a single local, read-only `hostname`
command. It contacted no other host, accessed no production data or credentials, changed no state, and its output was
not used as admissible operational evidence. This section is not a further review round and opens none.

**Material findings of the independent Codex review, and what was done**

| # | Finding | Remediation (documentation only) | Status |
|---|---|---|---|
| 1 | **Topology conflicts with the production boundary.** The maintainer-established fact is that the repository host is the production Ubuntu server. The draft runs local project tests (A0-05/A0-06) and creates the capture root there and issues the `rsync` and every `ssh` from there. Baseline v1.9 excludes production access and mutation and confines full testing to `oracle-test`. | The prompt now carries a G1 status block saying the topology is unresolved and the set unreviewable as an operational set; no A0 test, capture-root creation, sync, SSH, database or other operational command may run on production. A candidate safe path (execution/capture workspace on `oracle-test`, with a maintainer-approved source delivery) is **named only as a path needing a documented decision**; no command was rewritten for it. Follow-up 2026-11-22: that path is now written up as a concrete **proposal** in §0b (still no command rewritten, nothing accepted). | **Open blocker** (needs a maintainer decision; G4; proposal in §0b) |
| 2 | **Stale handback format.** The prompt's fixed block used `rp11-capture-binding/1` and no `invocation_id`. | Aligned to the accepted G11: `rp11-capture-binding/2`, eight-line body with `invocation_id` (`[0-9a-f]{32}`, between `pass_id` and `capture_root`), B0-RA and C-12 updated, and an explicit exact-schema rule (a `/1` block, a missing `invocation_id`, or an index of another schema is refused; index schema is `rp11-capture-index/3`; no dual reader). No stale `rp11-capture-index/2` reference remains outside this document's historical description of the G11 change. | Editorial/schema correction done; matches the implemented code (`capture_contract.py`) |
| 3 | **Stale inventory.** Kernel `7.0.0-31-generic`, PostgreSQL `16/main`, Python 3.12. | Stated values now follow the disposable-server document: kernel `7.0.0-1015-oracle` (observed 2026-11-07), PostgreSQL 18.6 cluster `18/main` as the only cluster (A1-29/30/33, B6.8, B7-07 and AUTH-DB adjusted), Python 3.14.4. They are marked observational and subject to revalidation. No unrelated pin was changed; no digest or `PIN.dry_run` figure was touched. | Prompt text corrected; **harness source constants were still stale at that date** (`approved_target.py`, `plan.py`, `case_runtime.INTERPRETER_PYTHON_VERSION`); re-pinned 2026-11-23 (manifest v33, then v34) |
| 4 | **Standing blockers must not be lost.** | Preserved and restated: RP-11 unmet; C-11 and the pinned child environment unresolved (G2, G3); A-6 independent MD-5 acceptance absent (stops at A0-09); an exact clean pinned tree and the owner's A-1, A-2 and A-5 inputs still required. Command review grants none of AUTH-SYNC, AUTH-READ, AUTH-DBREAD or A-2 and authorizes no execution. | Open |

**Editorial and schema corrections are not acceptance.** The `/2` and `invocation_id` alignment and the factual
re-statements make the draft *consistent* with accepted G11 and the current disposable-server record. They do not
review, accept or authorize any command, do not satisfy any RP prerequisite, and do not change G1-G10 (G1 stayed open on 2026-11-22; see the current status above;
the G11 and G12 rows are unchanged).

**Remaining blockers before G1 can be reconsidered:** (1) a documented maintainer decision on the execution and capture
topology (G4) — **a concrete single-host proposal now exists in §0b and is Codex-reviewed 2026-11-22 (no blocking documentation finding) and awaiting
Peter's acceptance; it is not accepted** — with the host roles, source delivery, capture root, the §5 synchronization
row, C-11, the child environment, A0 host locality, evidence semantics and B0-RA re-derived for it (the old
`ssh oracle-test` and production-origin `rsync` command set is withdrawn, not carried over) and then re-reviewed;
(2) harness source constants and the review manifest re-pinned for Python 3.14, `18/main` and the current kernel,
with a new reviewed digest; (3) RP-11 accepted and its tool digest pinned (G6); (4) C-11 and the child environment
(G2, G3); (5) A-6, `MI.pinned_commit` on a clean tree, and the owner's A-1, A-2 and A-5 inputs. Only after those can
Codex re-review an amended draft; acceptance of commands would still not be authorization to run them.

## 0b. G4 topology proposal — single-host `oracle-test` (2026-11-22)

**Decision accepted by Peter Duscha on 2026-11-24, for the disposable feasibility exercise only.** The topology and fixed paths below are accepted. This documentation decision does not run any host, network, database or test action. It does not accept OP1, authorize exact-source acquisition, accept G1 for execution, or start anything. Exact-source acquisition from the canonical public remote remains a separately authorized pre-pass action. There is no A-2; AUTH-SYNC, AUTH-READ and AUTH-DBREAD are not granted.

**Scope of this topology (owner clarification, 2026-11-22).** The single-host `oracle-test` topology below applies **only** to the OP1 harness-facsimile Pass A/B feasibility exercise and proof-of-concept on the disposable host. Peter Duscha clarified on 2026-11-22 that the **eventual production RP-11 capture service/runtime is to run on the production Ubuntu server**, and that **`oracle-test` is only for proof-of-concept, feasibility passes and tests and has no ongoing or production runtime role.** Three things stay distinct:

* **Accepted direction (runtime host):** the production runtime belongs on production Ubuntu. This clarifies scope only.
* **Accepted (G4 test-topology choice):** the feasibility work uses the single-host `oracle-test` topology below. This decides the disposable topology only; it cannot decide, imply or move a production runtime onto `oracle-test`.
* **Not authorized:** installation on, access to, or activation on production,
  and any real pass. The `capture` identity is selected but its creation and use
  are not authorized; the sandbox, timeout measurements and bound (G7), SA-2
  build/rebuild, installation, activation and real-run gates stay separately
  gated. This grants no A-2, AUTH-SYNC, AUTH-READ or AUTH-DBREAD and does not
  accept G1 for execution.

**Accepted topology (feasibility exercise only).**

1. **Production is never in Pass A/B.** The production Ubuntu server is not the source workspace, the capture host or
   the command-execution host. No A0 test, capture-root creation, sync, SSH, database access or other operational
   command runs there, and no file is created there.
2. **`oracle-test` is the only host**: repository workspace, RP-11 capture host and target/command-execution host. The
   capture mechanism launches the target commands **locally** with reviewed fixed argv and a pinned environment. No
   SSH hop, tunnel or bypass.
3. **Source** is a **dedicated clean checkout on `oracle-test` at `/opt/freedom-blades/rp11-source`**, distinct from the
   capture roots, `/tmp`, run root `R` and the existing rsync-synced `/opt/freedom-blades/platform` test tree, at an
   exact owner-published commit of `https://github.com/ming-themerciless/freedom-platform.git`. Nothing is sourced,
   `rsync`ed or `scp`ed from production, and nothing depends on uncommitted or unpublished local changes. If the exact
   reviewed source is not published, **stop pending maintainer-controlled publication**. No Git credentials or
   secrets are added. Clone/fetch is a **pre-pass source-acquisition action** on the disposable host, not an OP1
   command; before any pass its exact commit, clean status and manifest/source digests are recorded and reviewed
   (feeding `MI.pinned_commit`).
4. **Capture roots A and B** are `/var/lib/fb-rp11/capture-a` and
   `/var/lib/fb-rp11/capture-b` (scoped-parent redesign, maintainer-approved
   2026-11-24; the earlier direct `/var/lib/fb-rp11-capture-a`/`-b` leaves are
   withdrawn, see the G4 result below). They live on `oracle-test`, separate from
   each other, the checkout, `/tmp` and `R` (`/var/lib/fb-evidence-p5-0`).
   **Parent contract.** `/var/lib/fb-rp11` is a pre-provisioned narrow
   `root:capture` directory, mode **0770** (root and the `capture` group full:
   read, write, search; others nothing; no setuid/setgid/sticky bits; `capture`
   is the only group member and the directory is purpose-built), directly below the unmodified
   `root:root` 755 `/var/lib`. The two leaves stay **absent** until X-1, where the
   non-root `capture` account creates each exclusively with mode **0700**. The
   parent is provisioned by the host owner as root, never by the pass. The leaves
   still require the §9.5.1 filesystem-acceptance test; this decision creates
   nothing. **Mode history (historical, superseded):** 0730 was first approved but withholds the read the
   unmodified `CaptureRootStore` needs (it opens every ancestor `O_RDONLY` and fsyncs
   the parent entry), so Peter changed it to **0770** on 2026-11-24. No durability
   finding is open: executable evidence runs the unmodified store under a 0770
   stand-in parent (plan handback, follow-up 3). Host validation as `capture`
   passed for both roots on 2026-11-25 (below; follow-up 4); final suite evidence is recorded (follow-up 5).

**Implications (each is an open re-derivation, not a decision).**

* **The old command list is withdrawn.** The draft's `ssh oracle-test ...` commands and production-origin `rsync` are
  not carried over. The §5 sync row, AUTH-SYNC/AUTH-READ meaning, C-11 (guard analysis of whatever replaces the
  `rsync`), the child process environment (G3), A0 host locality, per-act evidence semantics (a local launch has no
  ssh transcript; stdout/stderr/exit are of the local child) and the B0-RA retention check must be redesigned for one
  host and reviewed. Do not silently keep any old command.
* **RP-11 requirements text conflicts.** The prompt's RP-11 row requires the capture root on the repository host
  "with no file created on `oracle-test`", and A1-19/A1-Z survey `oracle-test` as the unmodified target. Both must be
  amended so that capture files, the checkout and the capture unit's own identity and unit are expressly excluded
  from, or accounted for in, the target-state surveys, and `R` provably stays absent. Without that amendment the
  topology is self-contradictory.
* **Observer effect.** The capture host and target are one, so the capture tool's identity, unit, checkout and root
  can perturb the facts being surveyed; the draft's identity, process and service checks must name what is expected
  to exist.
* **Isolation.** `oracle-test` runs DB suites and prior rehearsals; the capture roots, checkout and any run window must
  not share files or run concurrently with them (the DB suites share one disposable database, finding F-6, and a
  concurrent run can break or wipe a rehearsal).
* **Evidence is disposable-host evidence** and its feasibility conclusions say nothing about production; production
  S4 probes and capture-unit deployment are unchanged and separately gated.

**Still-open blockers, all preserved (updated 2026-11-26):** G1 is accepted for review only and not authorized to run; its command set must now be re-derived for the accepted single-host topology. No A-2 or AUTH-SYNC/READ/DBREAD grant exists. C-11 and the child environment are implemented for review but not accepted (G2, G3); G4 disposable filesystem acceptance is complete (both roots, 2026-11-25; final suite evidence recorded); A-6 is absent (G9). G8 staged composition is complete but provides no run path. The `capture` identity is selected and mirrored only on disposable `oracle-test`; it is not installed or authorized on production. G6 is technically complete (2026-11-26, note above; design acceptance remains subject to revision before production); G7 has an accepted policy and derived values (44 s / 161 s / 30 s unchanged; finalization allowance 112 s; bound 2548 s, 2638 s with corroboration; manifest v38), measured as `capture` at the selected paths; Codex review passed (superseding note of 2026-11-25 above), with v38 successor publication, re-acquisition and remote lock validation complete (2026-11-25, note above). Harness constants and the review manifest were re-pinned on 2026-11-23
(Python 3.14, `18/main`, kernel `7.0.0-1015-oracle`; manifest v34), superseding the earlier `3.12`/`16/main`/`7.0.0-31-generic`
pins; an exact clean pinned tree and the owner's A-1, A-2 and A-5 inputs are still required.

**Recorded choices.** The checkout is `/opt/freedom-blades/rp11-source`; capture
roots are `/var/lib/fb-rp11/capture-a` and `/var/lib/fb-rp11/capture-b` under the
scoped parent below (originally direct `/var/lib` leaves, withdrawn); the
maintainer publishes the exact commit to the canonical public remote before a
separately authorized acquisition; and the dedicated account is `capture` for
disposable fidelity testing and the intended production service identity. It
must be a locked, non-login system account, non-root, with no sudo or
supplementary groups, and must not be `ubuntu` or `freedom-executor`. No account
is created by this decision, and production installation remains separately
gated. G4 disposable filesystem acceptance is complete (both roots, 2026-11-25; final suite evidence recorded, below).

**G4 scoped-parent redesign (2026-11-24, maintainer-approved; implemented in
data and tests; host filesystem acceptance 2026-11-25, below).** Roots become
`/var/lib/fb-rp11/capture-a` and `/var/lib/fb-rp11/capture-b`. The parent
`/var/lib/fb-rp11` is pre-provisioned `root:capture` 0770; the leaves are absent
before X-1 and created 0700 by non-root `capture`. `/var/lib` is not widened.
`pass_a_plan.PARENT_CONTRACT` states this and `parent_problems`,
`leaf_absent_problems` and `created_leaf_problems` refuse every unsafe owner,
group, mode, special bit, link or file. No durability finding is open (§0b item 4).

**G4 host filesystem-acceptance result of the scoped-parent design (2026-11-25).**
On `oracle-test`, under the `root:capture` mode 0770 parent `/var/lib/fb-rp11`, the
unmodified `CaptureRootStore` / `PosixCaptureFilesystem` ran as the capture account
(UID 992, GID 978) for both `/var/lib/fb-rp11/capture-a` and
`/var/lib/fb-rp11/capture-b`. Each leaf started absent; X-1 created it mode 0700, owned
992:978, with the durability path; a duplicate create was refused
(`X-1:create-root` / `object-exists`); cleanup restored it to absent. The parent ended
empty. Exact outputs:

```text
ok root=/var/lib/fb-rp11/capture-a uid=992 gid=978 mode=0700 duplicate=refused cleanup=absent
ok root=/var/lib/fb-rp11/capture-b uid=992 gid=978 mode=0700 duplicate=refused cleanup=absent
```

**Final suite evidence (2026-11-25; recorded, not re-observed):** focused reviewer suite 780 passed (no skips or failures); bot 8437 passed, 280 skipped, 6 warnings, exit 0; web 2894 passed, 80 skipped, 1137 warnings, exit 0; Foundry Node 171 passed, 0 failed, 0 skipped, exit 0 (details: plan-handback follow-up 5).

**G4 disposable filesystem acceptance is complete.** It grants no operational authorization. Production and operational gates are unchanged. Exact-source
acquisition stays blocked until the maintainer publishes the final successor commit.
No push, source acquisition, `run_pass_a`, A-2/AUTH, SA-2, service, activation or probe.
No source acquisition or `run_pass_a` call is part of this result.

**Historical, superseded: G4 filesystem-acceptance result of the direct-leaf design (2026-11-24): FAILED.** Under Peter's explicit
disposable-host authorization, on `oracle-test` the checkout and both roots were
absent, `/opt/freedom-blades` is `ubuntu:ubuntu` 755 and `/var/lib` is `root:root`
755. The `capture` account (system `useradd`; uid 992, gid 978; locked; home
`/nonexistent`; shell `/usr/sbin/nologin`; only its primary group; no sudo) ran
exclusive `mkdir --mode=700` for `/var/lib/fb-rp11-capture-a` and `-b`; each
returned rc 1 *Permission denied* and both remain absent. The selected direct
`/var/lib` leaves therefore conflict with exclusive creation by non-root
`capture`. **Decision needed, none selected:** change the path/parent design, a
narrowly provisioned parent, or a revised exclusive-create lifecycle/security.
`/var/lib` must not be weakened and the roots must not be silently precreated. The
reviewed slice (`592678b`) is committed locally but unpublished, so exact-source
acquisition remains blocked on maintainer publication. Production untouched; no
source acquired, `run_pass_a`, A-2/AUTH, SA-2, service, activation or probe.

**Remaining G4 verification criterion for technical closure.** G4 constrains the choice of the **feasibility test topology only**; accepting it cannot decide, imply or move the production runtime onto `oracle-test` (the production runtime host is Ubuntu per the 2026-11-22 clarification above, with installation and activation separately gated and unauthorized). The recorded decision supplies the feasibility topology, paths, publication method and production boundary. As of 2026-11-25 the filesystem result above covers both selected roots: G4 disposable filesystem acceptance is complete (both roots, 2026-11-25; final suite evidence recorded). The criterion as first written required the filesystem acceptance result for both selected roots and confirmation that nothing is created or run on production. The original acceptance checklist required Peter to record in writing: the feasibility topology above or a
stated amendment, stated as applying to the disposable feasibility passes only; the checkout path, capture-root A and B paths and the filesystem acceptance result; the publication
method for the exact commit; confirmation that nothing is created or run on production; and the explicit statement
that this does not itself accept G1, authorize AUTH-SYNC/READ/DBREAD or A-2, give `oracle-test` any production runtime role, or authorize production installation or activation.

**Acceptance criteria for a G1 draft re-review (Codex).** The amended prompt must show: (1) no production host role
and no `ssh`/production `rsync` command; every command local to `oracle-test` with fixed argv, pinned environment and
per-command timeout; (2) a source-acquisition record (commit, clean status, manifest/source digests) preceding A0, and
A0 that verifies it; (3) the RP-11 "no file on `oracle-test`" text and the A1 surveys amended per the implications
above; (4) a replacement for the §5 sync row with its guard analysis (C-11) and child environment (G3), or its
removal with the row, authorization flags and stale AUTH-SYNC wording withdrawn; (5) B0-RA re-derived for local
roots; (6) harness constants and review manifest re-pinned (Python 3.14, `18/main`, current kernel); (7) all blockers
above still listed. Acceptance of commands would still not authorize running them (A-2).

## 0. Decisions accepted by Peter Duscha (2026-11-21)

*(Scope list as of 2026-11-21; G1 and G8 have since moved — see the current status at the top.)* These are decisions, not proposals. They authorize **reversible implementation and testing on `oracle-test`
only** (baseline v1.9; synthetic names, no real secrets or player data). They do **not** accept or authorize
anything else in this document, in particular:

- the **DRAFT Pass A operational commands** (G1) — still not accepted, not authorized, not to be executed;
- **an operational run** of Pass A on any host (G10/A-2 is the only thing that starts a pass);
- any **production or staging** mutation or access;
- the **production service identity, sandbox and timeout** (G5, G7, design proposal §8 decisions 2 to 4);
- the **SA-2 artifact rebuild or install** (changes `ROUTE3_SA2_TREE_SHA256`; separately authorized), activation,
  or **S4 probes 2, 3, 5, 6**; and
- G2–G4, G6–G10 and the safety-sentinel amendment (G8), which were open exactly as in §6 on 2026-11-21 (for the later dispositions, including the 2026-11-24 owner decisions, see the current status and table above).

**D-G11 — systemd `INVOCATION_ID` is retained as capture provenance.** It is recorded **once per pass**, at
pass level: in the capture index state chain and in the handback binding. It is **not** duplicated into every
`CaptureRecord`. Consequences, all to be implemented and proven on `oracle-test` (§3 item 5):

1. *Index.* `IndexState` gains one `invocation_id` field (the lowercase 32-hex grammar of
   `rp11_launch.INVOCATION_ID_GRAMMAR`). Genesis fixes it; every later state must carry the same value, and the
   existing `previous` chain digest then binds it for the whole pass, so no per-record copy is needed.
   `INDEX_SCHEMA` moves `rp11-capture-index/2` → `/3`.
2. *Binding.* `HandbackBinding` gains `invocation_id`; `BINDING_FORMAT` moves `rp11-capture-binding/1` → `/2`.
3. *Record.* `CaptureRecord` and `RECORD_SCHEMA` (`rp11-capture-record/1`) are **unchanged**.
4. *Compatibility.* Parsers are exact-schema (`schema-mismatch` otherwise, as today): `/3` and `/2` artifacts
   are refused by `/2` and `/1` readers and the reverse. No dual-version reader is added. No retained `/2` index
   or `/1` binding exists for a real pass (no pass has run), so no migration is needed; existing test fixtures are
   regenerated. The capture-tool digest (`rp11-capture-tool/1`) and the review manifest change with the source
   and must be regenerated; no digest is pinned in production yet.
5. *Pairing is still the entry's job.* Recording does not replace the start-time check that
   `INVOCATION_ID` equals the consume `run-start.invocation_id` (§3 item 3).

**D-G12 — the entry may load tested Python modules under the isolated Python 3.14 launcher**, through a
reviewed, fixed packaging and import strategy (§3a). Peter accepted the principle; the concrete strategy selected
in §3a is a reversible implementation choice for `oracle-test` work and still needs the independent review that
security-sensitive production boundaries require (plan §16.3) before any SA-2 rebuild or activation.

*Original proposal text below is preserved; where it says G11 or G12 is open, §0 and the updated §3 item 4/§3a
and §6 rows supersede it.*

> ## DRAFT / NOT ACCEPTED / NOT AUTHORIZED — historical text (2026-11-22), superseded for G1's command/value layer on 2026-11-23 (accepted for review only; not authorized to run; the prompt carries its own current status block)
> The operational authorization prompt this proposal draws on,
> [`phase-5-0-p5-r5-operational-evidence-authorization-prompt.md`](phase-5-0-p5-r5-operational-evidence-authorization-prompt.md)
> (C-P5.0-R5-OP1), is itself **DRAFT ONLY. NOT ACCEPTED. NOT AUTHORIZED. DO NOT EXECUTE.** It is used here
> **only as a source of candidate commands**. No command named or cited below is approved, and none has
> been or may be executed on the strength of this document. Some of its figures predate the Python 3.14 / PostgreSQL 18
> baseline: the prompt's stated facts were corrected editorially on 2026-11-22 (see the disposition section below), but
> the harness source constants it derives from (`3.12`, cluster `16/main`, kernel `7.0.0-31-generic`) were not re-pinned
> at that date (re-pinned 2026-11-23 to Python 3.14, `18/main` and kernel `7.0.0-1015-oracle`, manifest v34). Its host topology is unresolved and
> conflicts with the production boundary (disposition finding 1).

**What this is.** The contract for the operational logic of `/usr/local/libexec/freedom-blades-rp11/rp11_entry.py run --pass A` (at proposal time absent; today only the bootstrap and the unreachable G8 session factory exist, and the run path ends at exit 69)
(`tools/phase_5_0_evidence/rp11_launch.py:51-56`; [design proposal](rp11-capture-service-design-proposal.md) §4
step 2). **What it is not:** code, an executable entrypoint, a unit fragment, or an authorization.

**Safety sentinel.** `test_nothing_outside_tests_arms_the_launcher_or_creates_a_session`
(`tests/phase_5_0_evidence/test_rp11_capture.py:1460`) fails if any module under `tools/` other than
`capture_mechanism.py` calls `create_capture_session` or `StreamCaptureLauncher`; the module docstring
(§"Not wired") says the same. **This document does not wire either.** *Historical (2026-11-21) text: writing the entry's `create_capture_session` call site needed the owner's G8 decision and G1–G3.* **Current (2026-11-25):** G8 staged composition is implemented and independently reviewed — the sentinel was amended for exactly one factory, `build_pass_a_session`, in the entry, which nothing calls. No run path exists (exit 69). The G2/G3/G7 plan, environments and measured timeouts are implemented for review in `pass_a_plan.py` (manifest now v37) but not operationally authorized; G4 filesystem acceptance passed for disposable feasibility on 2026-11-25, final suite validation recorded in plan-handback follow-up 5; G6 final digest/SA-2 review remains incomplete, and A-2 is absent.

## 1. Recommended logical order

Cites the draft's own sections; no shell is copied. Every host act goes through the RP-11 mechanism, one exact
argv, no shell, one act at a time, no retry (draft §6.2, §11.3).

| # | Phase | Source in draft | Selected options | Notes |
|---|---|---|---|---|
| 1 | Stated-state check: A-1…A-6 preconditions and the four current-state records | §4.1, A0-01, A0-09 | none (reads records) | Any miss stops before the mechanism exists. A-6 (MD-5 acceptance record) missing stops the pass (A0-09) |
| 2 | **Local admission**, no host contact | §6.1 A0-02 … A0-07 | none | `git rev-parse`/`status`, `sha256sum` pins, harness dry run, classifier tests. A0-02 clean status requires the capture root to lie outside the worktree |
| 3 | **Capture admission and genesis (X-1)**: tool-digest check, exclusive root creation, genesis publication | §6.1 A0-08, §9.5.2, §9.5.4 | none | `create_capture_session` is called here, and only here. Failure ⇒ `NO_GENESIS`, no host command, no X-3 |
| 4 | **One rsync sync** | §5, A1-00 | **AUTH-SYNC** | Exactly once; argv byte-for-byte from §5 (§5 "Do not alter…"). `--delete` is a listed target mutation (§13.1) |
| 5 | **Read-only SSH preflight**, in written order | §6.2: A1-S, A1-T, A1-I, A1-L, A1-Q | **AUTH-READ** | A1-C steps (A1-11, 12, 14, 15) run only if A0-09 referenced a pinned `MI.target_fact_statement`; else recorded `not_run (RP-10 unmet)` |
| 6 | PostgreSQL baseline | §6.2 A1-D | **AUTH-DBREAD** (optional) | If not granted, recorded "not run" (§4.2). Pass B cannot start without it |
| 7 | Final-state survey | §6.2 A1-Z | AUTH-READ (+AUTH-DBREAD for A1-29…33) | Every value must equal its earlier value |
| 8 | **Finalize** (X-3 once, then X-4) and emit the `rp11-capture-binding/2` handback block | §9.5.3 steps 2–5, §14 | none | Handback prose is not written by the entry |

Order rationale: admission precedes any contact; X-1 (the capability test) precedes the first host
command (A0-08); sync precedes the identity checks because A1-S verifies the synchronized tree. AUTH-V7,
-HARNESS, -DB, -PRODUCERS, -RR and -REBOOT are Pass B rows and are **out of scope** here (§4.2).

## 2. Candidate input/config schema

The entry takes **no operator-typed values at run time** beyond `--pass A` (launcher contract: argc 3,
`--pass A`, fixed environment `LC_ALL=C`, `PATH=/usr/bin`, `INVOCATION_ID`; `rp11_launch.py:30-56`).
Everything else comes from one reviewed, digest-pinned, root-owned config file read by the entry.

| Value | Candidate source | Validation | Status |
|---|---|---|---|
| activation id | the `activation_id` field of the canonical, root-owned `pass-a.json` pass config. The consume role reads this exact field first (`application/rp11/consume.py`, `_identify`, CQ-0: `validate_activation_id(doc.get("activation_id"))`; module docstring: "`pass-a.json` must carry `activation_id` (CQ-0)"). The pass-config contract is in `application/rp11/authority.py` (`_pass_document`: canonical bytes within `MAX_PASS_BYTES`, SHA-256 equal to the pinned digest, schema `rp11-pass-a/1`; `A2Pins.parse` requires the pinned `activation_id` to equal the identified one). The entry reads the same field from the same config, then locates the consume journal for that activation and compares `run-start.invocation_id` with `INVOCATION_ID` (§3) | `validate_activation_id` grammar (as consume applies it); must equal the A-2 pin; the journal's `run-start.invocation_id` must equal `INVOCATION_ID` | field name and source established; the entry must reuse the consume validation, not a looser re-implementation |
| `INVOCATION_ID` | process environment, from the launcher | `[0-9a-f]{32}` (`rp11_launch.py:INVOCATION_ID_GRAMMAR`) | fixed by launcher contract |
| `pass_id` | constant `C-P5.0-R5-OP1-A` (draft §14) | `require_identifier` | fixed by draft |
| capture root (`MI.capture_root_A`) | the config file; owner-supplied in the A-2 authorization (draft §4.5) | exactly `/var/lib/fb-rp11/capture-a` for Pass A; absolute, outside worktree and `/tmp`, a direct child of the `root:capture` 0770 parent `/var/lib/fb-rp11`, absent before X-1, component grammar of `parse_capture_root`; `/var/lib/fb-rp11/capture-b` is reserved for Pass B | paths redesigned 2026-11-24 (scoped parent); G4 filesystem acceptance passed for disposable feasibility on 2026-11-25, final suite validation recorded in plan-handback follow-up 5 |
| capture tool digest (`PIN.capture_tool_sha256`) | the config file; **computed by the SA-2 build, never by the entry from itself** | `require_sha256`; compared by the A0-08 admission check | not pinned today (draft §6.1 A0-08) |
| pinned commit (`MI.pinned_commit`), prompt/manifest/plan digests | the config file, from A-1/A-2 records | 40 / 64 lowercase hex | owner-supplied |
| authorization flags | the config file: `auth_sync`, `auth_read`, `auth_dbread` booleans, each carrying the dated A-2 record path + SHA-256 | a missing flag is **false**; the entry refuses a phase whose row is false | owner-supplied; never inferred |
| operator / identity | `MI.operator` from A-2 (named person or agent); service Unix identity from the unit (`User=capture`) | recorded in the handback; `capture` is a dedicated locked, non-login system account, non-root, without sudo or supplementary groups, and is not `ubuntu` or `freedom-executor` | identity policy decided 2026-11-24; account creation/install not authorized |
| window | `MI.pass_a_window_utc` | entry refuses to start outside it | owner-supplied |
| per-command timeouts | the config file, one value per command class (§4) | `valid_timeout_seconds`: positive, finite | candidate numbers only |

Config rules (candidate): the entry opens the fixed configured path without following symlinks, verifies the
opened file's attributes, parses the content as canonical JSON bytes (per `application/rp11/canonical.py`), and
matches its SHA-256 against the digest pinned in the A-2 record. **The entry refuses to run** if the file is
absent, not root-owned, group- or other-writable, **not readable by the eventual selected non-root service
identity**, not canonical JSON bytes, unparseable, has an unknown key, or its SHA-256 differs from the digest
pinned in the A-2 record. No default is substituted for any missing value. No numeric mode is fixed here: the service
identity is non-root, so a root-owned `0600` file is unreadable to it and must not be assumed usable. A concrete
mode or group is chosen only after G5 resolves the identity, and is validated by a test that checks the actual
permissions as that identity (the read must succeed and a write attempt must fail).

## 3. Consume-journal binding contract

1. The unit runs exactly one `ExecStartPre=+/usr/bin/python3.14 -I -S …/rp11_h1.py consume`; the consume role
   records `INVOCATION_ID` as `run-start.invocation_id` and consumes the grant.
2. The launcher passes `INVOCATION_ID` through to the entry (fixed environment, 32 lowercase hex).
3. **The entry reads `INVOCATION_ID` and must itself pair it with the consume `run-start`** (design proposal
   §4, "Same InvocationID"). Mismatch, absence, or a malformed value ⇒ no mechanism call, no host contact,
   non-zero exit.
4. **(Decision accepted, §0 D-G11; implemented 2026-11-22; independent Codex review passed.) Recording `INVOCATION_ID` was not supported by the
   schemas as originally written (the field list below describes the code before the implementation).** The current
   `capture_contract.IndexState` (`pass_id`, `capture_root`, `tool_sha256`, `owner_uid`, `state_number`,
   `previous`, `status`, `records`, …), `CaptureRecord` and `HandbackBinding` (`pass_id`, `capture_root`,
   `x3_outcome`, `x4_validity`, `final_state`, `capture_index_sha256`) contain no `INVOCATION_ID` field
   (`tools/phase_5_0_evidence/capture_contract.py`), so neither genesis nor the binding records it today.
   Attributing a retained capture root to one start therefore required a schema change; Peter accepted
   pass-level recording (index state chain and handback binding, not per record) as **G11**. This pass changes
   no schema and no code.
5. **Tests required for G11 (all on `oracle-test`, synthetic data):** (a) genesis stores `invocation_id` and the
   serialized state round-trips; (b) a later state with a different, missing or malformed value is refused, and a
   state-chain tamper of the field breaks `previous`; (c) `/2` index and `/1` binding are refused by the new
   readers and vice versa (`schema-mismatch`); (d) `CaptureRecord` bytes are unchanged (golden); (e) the binding
   carries the value and `verify` rejects a binding whose value differs from the final state's; (f) the entry
   refuses to create genesis if `INVOCATION_ID` is absent, malformed or unequal to the consume `run-start`;
   (g) the real-systemd capture-unit test (below) asserts index, binding, `run-start` and
   `systemctl show InvocationID` all agree; (h) the tool-digest and review-manifest tests are regenerated and pass.

**Evidence grade, kept separate.**
- *Test evidence (disposable unit, real systemd on `oracle-test`):*
  `tests/systemd_integration/test_route3_consume_host.py::test_a_complete_lifecycle_consumes_once_and_cleanup_reports_it`
  (line 145; the assertion is line 169) runs the consume role as a real `ExecStartPre=+` of a disposable
  capture unit, has the `ExecStart=` process write its own `$INVOCATION_ID`, and asserts
  `start["invocation_id"] == main_invocation == show(UNIT, "InvocationID")["InvocationID"]`.
  It was **not run for this proposal**.
- *Supported inference, not yet established for the capture unit:* that the same equality holds for the
  real `rp11-capture-pass-a.service` through the **static launcher → Python entry** chain on production-
  equivalent systemd. The test's `ExecStart` is `sh -c … exec sleep`, not the launcher. **This stays an
  inference until the capture unit has its own integration test** with the real launcher and entry, on
  `oracle-test`, and a production-equivalent systemd check for production.

## 3a. Bootstrap and import strategy (G12: loading accepted; strategy implemented as an inert bootstrap, independent Codex review passed)

The launcher execs `/usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_entry.py run --pass A`
(`rp11_launch.py:44-56`). Inspected for this section: `infra/rp11-h1/build.py`, `infra/rp11-h1/rp11_h1.py`
and the behavior of `python3.14 -I -S` (read-only local check; `PYTHONPATH=/nonexistent` set).

**Observed `-I -S` facts.** `sys.path` is exactly `python314.zip`, `/usr/lib/python3.14`, `lib-dynload`; the
script's directory is **not** on it; `PYTHONPATH` is ignored; `sys.flags.isolated=1`, `no_site=1`,
`safe_path=True`. So the entry cannot import `application.*` or `tools.*` merely by being installed, and nothing
is found by cwd, environment or site. The artifact must name its own import directory.

**Existing mechanism (already reviewed and in production use for the SA-2 roles).** `build.py` assembles a
root-owned tree (`rp11_h1.py` plus `lib/`) from a fixed `SOURCES` list and one hash-pinned wheel; it stamps
directories 0755 and files 0644, refuses symlinks and other types, and renames it into place. `rp11_h1.py`
runs a first-image control pass (descriptors, signals, umask, cwd, environment emptied), then, **as root**,
checks every ancestor and every object in the tree before `lib/` reaches `sys.path`; sets
`sys.dont_write_bytecode`; **appends** `lib` after the standard library so it cannot shadow a stdlib module;
imports the full set up front and fails with 70 on any `ImportError`. A test keeps `SOURCES` equal to the real
package contents.

**Selected strategy (reversible implementation choice; `oracle-test` only).** Reuse that mechanism; do not
invent a second one:
1. `rp11_entry.py` is a **second script in the same artifact directory** as `rp11_h1.py`, importing from the
   same `lib/`. The launcher's argv is unchanged.
2. `build.py` `SOURCES` gains **the entry's complete, mechanically computed dependency closure**: the
   `tools/__init__.py`, `tools/phase_5_0_evidence/…` and `…/execution/…` modules the capture mechanism imports,
   plus `application.idempotency` and the `application.rp11` consume validation the entry reuses (§2). A first
   static estimate from `capture_mechanism.py` and `capture_contract.py` finds 15 `tools` modules and one extra
   `application` module; this is indicative only (it includes imports under `TYPE_CHECKING` and lazy imports and
   was not run) and the real list is fixed by the test below, not by this document.
3. A new test computes the closure of the entry by AST and asserts it equals the `SOURCES` additions in both
   directions (no module missing, none extra), so a new import cannot be left out silently, and that no
   dependency is third-party beyond the one pinned wheel.
4. At run time the entry performs the **same checks before any artifact import**: first-image controls, then
   root-owned-tree verification of the artifact directory and every ancestor, then append `lib` after the stdlib.
   No `sys.path` insertion of the repository, cwd, environment value, `.pth`, `site` or user directory; no
   `PYTHONPATH`; no bytecode written; no in-memory loader. The shared checks are factored into one reviewed
   module rather than copied, or copied with an equality test (implementer's choice).
5. **Digest binding.** The whole tree, including the entry and its closure, is covered by the SA-2 tree digest
   (`ROUTE3_SA2_TREE_SHA256`), and `PIN.capture_tool_sha256` is computed by the build, never by the entry from
   itself (§2). Adding the entry and closure therefore changes the digest, the archive, its manifest and runbook
   references; **that rebuild is not authorized here.**
6. The entry runs as the selected non-root service identity `capture` (G5), so the root-ownership branch of the check
   is exercised through the unit; the test must also exercise the non-root branch with the entry's actual
   identity, and prove that a tampered or group-writable file, a symlink, a stray extra file and a planted
   `tools`/`application` module in cwd, script directory or `PYTHONPATH` are not imported.

**Rejected alternatives (recorded so they are not revived):** the historical C-11 in-memory loader
(unaccepted, remains so); inserting a repository checkout on `sys.path`; relying on the script directory
(`-I` removes it); `site-packages`, `.pth` or `PYTHONPATH`; a zipapp (adds a second loader and verification
surface for no benefit over the existing tree check).

**Status.** The decision to load tested modules is accepted. The strategy above is the selected design basis
for implementation on `oracle-test`; it is implementable, not yet implemented. Independent review of the
entry, its closure and the tree checks (security-sensitive) is required before any SA-2 rebuild, install or
activation; none is authorized by this document.

## 4. Per-command timeout candidate policy

**Policy accepted by Peter Duscha on 2026-11-24.** Every redesigned local
command has a fixed, conservative timeout derived from measurements on
`oracle-test`. A timeout stops the pass through the reviewed single finalization
path; there is no retry, resume or continuation after the timed-out act. The
candidate numbers below are not accepted values: G7 remains technically
incomplete until the local commands have been measured, the fixed class values
and derived whole-pass bound are recorded, and the failure behavior is tested.

The primitive now exists: `ActRequest.timeout_seconds` is required with no default
(`capture_mechanism.py:240`); `StreamCaptureLauncher` runs each child in its own process group, kills the
group at the monotonic deadline, drains for at most `drain_seconds` (default 5 s,
`boundary.py:CAPTURE_DRAIN_SECONDS`), reaps, and reports `timed_out` (`boundary.py:1161-1210`;
`test_rp11_capture.py:582-853`). The deadline is applied by the mechanism **around** the argv; it does not
alter the argv, so the draft's "no added option" rule (§5) is unaffected.

**Candidate numbers only — none accepted, none measured:**

| Class | Commands (draft) | Candidate timeout |
|---|---|---|
| T-local | A0-02 … A0-04 | 30 s |
| T-dry | A0-05 and A1-S1 (harness dry run) | 120 s |
| T-test | A0-06 (two classifier test files) | 300 s |
| T-sync | A1-00 rsync | 600 s |
| T-read | every other `ssh oracle-test "…"` read, incl. `sudo` reads and `psql` | 30 s |

Plus the existing 5 s drain per act. **Arithmetic bound (candidate):** ≈ 58 acts with AUTH-DBREAD
(≈ 48 without) ⇒ worst case ≈ 54 minutes, typical expected far less. Because the unit carries no
`RuntimeMaxSec=` and `TimeoutStartSec=` bounds only consume + exec handoff (design proposal §5), **this sum
is the only whole-pass bound**; it is a derived number, not a manager-enforced one.

**Validation method (on `oracle-test`, synthetic data only; satisfies no gate):**
1. Time each class's real command ten times on `oracle-test`; set the candidate to a documented multiple of
   the observed maximum (suggest ≥ 5×, floor per class above). Rsync measured from both a no-change and a
   full-tree state.
2. For each class, run the mechanism against a deliberately slow synthetic stand-in (a sleeping argv) with
   the candidate value divided down to a few seconds, and confirm `command-timeout`, group kill, reap, one X-3
   and unadmitted residue (§5).
3. Run the real entry inside the disposable capture unit and confirm the whole pass finishes inside the
   derived bound and consume + exec handoff fits `TimeoutStartSec`.
4. A value that fails is revised and re-measured; it is not stretched to hide slowness.

## 5. Exact timeout and stop behavior

Taken from `capture_mechanism.py` ("The one stop transition") and draft §9.5.3, §11:

1. **Timeout.** The deadline passes ⇒ the mechanism kills the child's process group, drains both streams for
   at most the drain limit, reaps the child, classifies `command-timeout` with `host_act_may_have_run`.
   The act is **not admitted** (no per-act record, no X-2 state); its stream files and any staging names are
   **unadmitted residue**.
2. **One stop transition**, same path for timeout, any capture failure (C-10), any §11.1 refusal and any
   §11.2 band stop: leave `OPEN`; refuse every later act without touching the filesystem or launcher; make
   **exactly one** X-3 attempt, only if genesis is durable and the session was not interrupted
   (`_x3_attempted` set before the first call); seal the session read-only behaviorally (no `chmod`); apply
   X-4 to the bytes on disk, or `inconclusive` if X-3 failed or was not made.
3. **Residue is preserved.** Unadmitted objects are retained unmodified, recorded in *F* by exact relative
   name and type, and reported in the handback. **Nothing is completed, renamed, deleted, adopted, digested
   into evidence, repaired or re-run**; the entry has no cleanup path for the capture root.
4. **No retry, no resume, no further host command**, not even read-only (§11.1, §11.3). Interruption of the
   entry process (kill, host restart) ⇒ no X-3, even after recovery; a new process cannot open the root
   (`create_capture_session` is exclusive-create only).
5. **Entry exit status.** Zero only after X-3 succeeded and X-4 is `valid` with every phase 1–8 done; any
   other path exits non-zero. A `stop` (SIGTERM, `systemctl stop`) is treated as an interruption signal
   handled by step 2 if the session is still `OPEN` and not inside a mechanism call; the entry must not
   install handlers that run mechanism calls from signal context (candidate rule; to be proven by test).
6. **No `RuntimeMaxSec=`** (design proposal §5); forced manager termination would be treated as an
   interruption (step 4).

## 6. Decisions and gates — each separate

*Update 2026-11-24 (implemented, tested, measured with synthetic stand-ins; accepted for review only):* `tools/phase_5_0_evidence/execution/pass_a_plan.py` (covered by manifest v35) holds the single-host plan, the four child environments (G3), the `capture` identity as data and the measured timeout/bound policy (G7), with `tests/test_rp11_pass_a_plan.py` and the opt-in `tests/test_rp11_pass_a_measure.py`; see the [handback](rp11-pass-a-plan-handback.md). The embedded 24 samples (12 idle-ish + 12 loaded) were measured on `oracle-test` as `ubuntu` against a synthetic scratch clone and capture root, under the plan's own exit policy, which the harness now enforces with unexpected-exit controls (every step exited as planned); the selected paths and `capture` account were untouched. Fixed class timeouts 44 s / 161 s / 30 s and whole-pass bound 2466 s are derived from them. Focused tests: local 978 passed, 4 skipped; `oracle-test` 980 passed, 2 `RLIMIT` skipped. Canonical v35: bot 8400 passed, 280 skipped, 0 failures (2397.65 s); web 2894 passed, 80 skipped, 0 failures (1157.90 s); Node 171 passed (6.79 s). Codex's independent review found no remaining blocking implementation or safety finding after the exit-policy remediation. The G2/G3/G7 rows below are **implemented and reviewed** but not operationally authorized: the entry still exits 69, `run_pass_a` has no caller, and real `capture` identity/path evidence remains gated.

| ID | Owner decision | Recommendation | Gate / what it does not authorize |
|---|---|---|---|
| G1 | **Operational command set.** | The 2026-11-23 command/value layer and manifest v34 passed review, but its two-host command list is now withdrawn and superseded for topology. Re-derive every command as a fixed local `oracle-test` argv with the accepted paths, pinned environment and measured timeout after G2/G3; then review the amended set. | Command acceptance is not A-2 run authority. No AUTH grant, source acquisition, operational pass, production/staging access, SA-2 build/install, activation or probe is authorized. |
| G2 | **C-11 guards — requirement under redesign.** The old definition covered the withdrawn production-origin `rsync`. Under the accepted single-host `oracle-test` topology, C-11 must cover the guard-conformant exact-source acquisition and every locally launched fixed argv, with no guard bypass, and determine whether a separate source-acquisition authorization replaces AUTH-SYNC. | Review the exact acquisition method and prove argv equality with guarded interactive invocations. | **Plan implemented for review (2026-11-24):** every local argv is fixed in `pass_a_plan.py` and admitted unchanged by `guard-secrets.py`; exact-source acquisition and its authorization remain undecided and unperformed. Not accepted, not authorized to run. |
| G3 | **Pinned process environment — requirement under redesign.** Under the accepted single-host topology the old SSH/rsync children are withdrawn. Pin every variable for the actual local child commands; inherit nothing from the launcher, and derive any `HOME` or credential need per command. | Define the child mapping and test it against the chosen sandbox (`ProtectHome`). | **Implemented for review (2026-11-24):** four complete non-inherited environments in `pass_a_plan.py`, exercised on `oracle-test` as `ubuntu`; behaviour under the real `capture` account and `ProtectHome` sandbox is not yet observed. Not accepted, not authorized to run. |
| G4 | **Capture topology and paths.** | **Direction accepted 2026-11-24 for disposable feasibility only:** single-host `oracle-test`; checkout `/opt/freedom-blades/rp11-source`; roots `/var/lib/fb-rp11/capture-a` and `/var/lib/fb-rp11/capture-b` under the pre-provisioned `root:capture` 0770 parent `/var/lib/fb-rp11` (scoped-parent redesign, approved 2026-11-24, mode corrected from 0730 to 0770 the same day, replacing the failed direct `/var/lib` leaves); maintainer-published exact commit from the canonical public remote. Production has no role. | Policy choice closed. The direct-leaf design **failed filesystem acceptance 2026-11-24** (rc 1); the maintainer approved the scoped-parent remedy, implemented as data and tests. No durability finding is open (0770; the unmodified store is exercised under a 0770 stand-in, plan handback follow-up 3). **2026-11-25:** the host test as `capture` passed for both roots (follow-up 4); disposable filesystem acceptance is complete (final suite evidence recorded in follow-up 5). The v38 successor `575218e` is published and re-acquired (2026-11-25, note above). No A-2/AUTH/run authority. |
| G5 | **Resolve service identity.** | **Decided 2026-11-24:** `capture`, a dedicated locked non-login system account, non-root, no sudo or supplementary groups, not `ubuntu` or `freedom-executor`; mirror it on `oracle-test` for fidelity. | Identity policy closed. No account creation, production install or activation is authorized. |
| G6 | **Accept capture-mechanism findings and pin the tool.** | **Provisionally accepted 2026-11-24, subject to revision before production.** | Design choice settled for continued non-production work; **Technically complete 2026-11-26** at `2afca20` (final tool digest and non-installing SA-2 reference builds reviewed; [G6 handback](rp11-g6-preparation-handback.md)). RP-11 is not production-ready; no install or run authority. |
| G7 | **Timeout values** (§4) and the derived whole-pass bound. | **Policy accepted 2026-11-24:** measured conservative fixed per-command values; timeout stops safely through the single finalization path. | **Values derived for review (2026-11-24):** timeouts 44 s / 161 s / 30 s and whole-pass bound 2466 s, from 24 embedded samples measured with synthetic stand-ins as `ubuntu` on a shared host; not measured under `capture` or the selected paths. **2026-11-25:** measured as `capture` at the selected paths; timeouts unchanged, finalization allowance 30 s → 112 s, bound 2548 s (manifest v38, [plan handback](rp11-pass-a-plan-handback.md) follow-up 7). **Review (2026-11-25; supersedes pending review):** authorized `b279` acquisition and real measurement complete; timeouts 44 s / 161 s / 30 s, allowance 112 s, bound 2548 s (2638 s with corroboration), manifest v38; Codex review passed after advisory-lock remediation, no blocking source finding (follow-up 9). **Update 2026-11-25:** v38 successor publication, re-acquisition and remote lock validation are complete. Not authority to run. |
| G8 | **Amend the safety sentinel** to permit the one reviewed `create_capture_session` call site in the entry | Only after G1–G6 and the entry's review; separate change | **Update 2026-11-23/24: staged composition implemented and independently reviewed** (one factory, `build_pass_a_session`; sentinel amended for exactly that site; nothing calls it; run path unavailable, exit 69). Original condition (historical): without the amendment, nothing could be wired. G2/G3/G7 are implemented for review but not accepted, G4 filesystem acceptance passed for disposable feasibility on 2026-11-25, final suite validation recorded in plan-handback follow-up 5, G6 is technically complete (2026-11-26), and A-2 is absent; the amendment is not authority to run. |
| G9 | **A-6 / MD-5 independent acceptance record**, and RP-10 statement for A1-C | **A-6 met for manifest v39** (2026-11-27). [Independent acceptance](rp11-g9-md5-independent-acceptance.md) names the classifier digest and candidate `MI.md5_disposition` reference. | RP-10 remains open. A1-C is `not_run (RP-10 unmet)`. |
| G10 | **AUTH-SYNC / AUTH-READ / AUTH-DBREAD**: Peter's written A-2 grant naming the operator, with A-5 data attestation. **Current state: all three grants remain absent.** AUTH-SYNC meant the old production-origin synchronization, withdrawn by §0b; the meanings and bands of AUTH-SYNC, AUTH-READ and AUTH-DBREAD must be **redefined in the amended prompt** for the single-host topology (proposal requirement, not decided; AUTH-SYNC may be replaced by a separate source-acquisition authorization or removed, see G2). G1 command acceptance stays distinct from, and does not imply, any of these or A-2 | Grant per row, per pass, only after all other design and contract decisions G1–G9 are decided and G11 (provenance) and G12 (import/bootstrap) are implemented and reviewed; production authorization stays separate and unchanged | A-2 is the only thing that starts a pass |
| G11 | **DECIDED (Peter, 2026-11-21): retain `INVOCATION_ID` as capture provenance**, recorded once per pass in `IndexState` (chain-bound) and `HandbackBinding`, not per `CaptureRecord`; schemas `rp11-capture-index/3`, `rp11-capture-binding/2` (§0, §3 items 4–5) | Implement and test on `oracle-test` | Implemented locally 2026-11-21 (`rp11-capture-index/3`, `rp11-capture-binding/2`); independent Codex review passed. Does not accept G1–G10 or authorize any run or production step; must still be in place before the G10 grant |
| G12 | **DECIDED in principle (Peter, 2026-11-21): the entry may load tested modules under the isolated 3.14 launcher.** Concrete strategy selected in §3a (fixed root-owned digest-bound closure beside `rp11_h1.py`, no cwd/env/site lookup) | Implement and test on `oracle-test`; independent review before any SA-2 rebuild/activation | Inert bootstrap and closure implemented locally 2026-11-22, tests local; independent Codex review passed; SA-2 rebuild unauthorized; the old C-11 loader and `sys.path` insertion stay rejected |

**No production authority.** Nothing here authorizes production or staging access, installation of the
capture unit, activation, any consume of a real grant, S4 probes 2/3/5/6, or an SA-2 rebuild; each stays
separately gated and attended (Handover; plan §14.2; design proposal §7–8). All rehearsals above are
`oracle-test`-only with synthetic names and no real secrets or player data.
