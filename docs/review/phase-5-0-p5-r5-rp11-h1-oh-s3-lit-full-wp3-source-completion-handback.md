# LIT-FULL WP-3 source-completion handback — 2026-10-10

Work ID `C-P5.0-R5-RP11-H1-OH-S3-RT3-WP3-SC1-20261010-23` · executor Claude ·
reviewer Codex (pending) · decision owner Peter Duscha

**WP-3 SOURCE COMPLETION RETURNED — INDEPENDENT CODEX REVIEW PENDING**

This is not a `HARD STOP`: the pinned Ubuntu sources were authenticated and all
eighteen facts `UF-01` … `UF-18` were researched. The return does **not** accept
the record, edit or integrate into the accepted interface contract, close any Q3
question, answer Q6-6 or Q6-7, authorize WP-4 … WP-7, establish concrete Route 3
or select LIT-FULL. The accepted WP-3 `HARD STOP` remains in force.

Deliverables: [source record](phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-record.md)
(this handback is the companion) and the four current-state pointers listed in §6.

## 1. Required reading — completed before the first edit

All eighteen items the prompt requires were read before the first deliverable
edit, and re-hashed after reading (identical). Identity ledger (path relative to
the repository root; lines; bytes; SHA-256):

| # | Path | Lines | Bytes | SHA-256 |
|---:|---|---:|---:|---|
| 1 | `.agents/AGENTS.md` | 700 | 36,014 | `87bab4ab8d67e308af0c59b99c8604235ee84d75cfa12448458b1a04cc88390a` |
| 2 | `docs/implementation-plan.md` | 2,602 | 127,966 | `40bc8df325f374b2d0374d3fd74dda1b6cf51db090482072db85abe1870ed201` |
| 3 | `docs/review/Handover information` | 32 | 2,021 | `b8e88605a1e97d9afe32664c6f11bae2951689c99a0e6a9b3cc597d74c473811` |
| 4 | `docs/operations/disposable-test-server.md` | 322 | 14,941 | `f459ef7f5ade14482174ae32ecdbcba8376192b9cba5c920ac0ff108cc23f4e7` |
| 5 | `docs/review/project-review-2026-10-10-p5-r5-rp11-h1-oh-s3-lit-full-wp3-r1-remediation-acceptance.md` | 49 | 2,945 | `576ef26b6ab56fdb5845491cd7222095fca86fe55c2397f3abf285acc5758362` |
| 6 | `docs/review/project-review-2026-10-10-p5-r5-rp11-h1-oh-s3-lit-full-wp3-r1-remediation.md` | 107 | 5,955 | `369c85c13cce02a67f1f90688e2081619ba13f4bc48c4b4fff853d7055be4514` |
| 7 | `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-interface-contract.md` | 469 | 50,599 | `b766c10f2c28ac2d32a7dc7ee4ab2c92a3cf80d67fd70f345a9f0dd7ba92c888` |
| 8 | `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-r1-remediation-handback.md` | 173 | 14,345 | `82d4502fbfa7c84421335be083e1bc58eb63a0cd2459c74fd29bd06d34662a03` |
| 9 | `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-r1-remediation-claude-prompt.md` | 242 | 12,684 | `0452dd4c77aa4f92196ffa24ca0292e810f1bf1765133161eab2f57b34f553d9` |
| 10 | `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s2-r2-citations.md` | 1,866 | 177,481 | `299f0598bb198572f2edb994234a63956ecafc9ab1873cb10879d0a238dea1a5` |
| 11 | `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp2-operation-inventory.md` | 1,450 | 230,574 | `da341efb8c29b862d63c1463e981ccfedbe1f6680de2d416ff285fdae06461fd` |
| 12 | `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-r8-remediation-proposal.md` | 4,816 | 551,246 | `ab5db5010d9d1b2738b04f1ffbd62ab4414d901e9f7f79323ac49f811f660e04` |
| 13 | `docs/review/phase-5-0-p5-r5-rp11-h1-oracle-test-one-host-design-amendment-proposal.md` | 7,307 | 525,019 | `a752a4b8fe7eb1edf3e3a25decd3a7517ecccc85fedbb0b0b7e003cb7e615d02` |
| 14 | `docs/review/project-review-2026-10-07-p5-r5-rp11-h1-oh-s3-r8-acceptance.md` | 46 | 2,653 | `594292d44d9ad5b161dc61a6f4cdc6457b56029d73cc1be60da84153c8c01e30` |
| 15 | `docs/review/project-review-2026-10-06-p5-r5-rp11-h1-oh-s2-r2-acceptance.md` | 43 | 2,186 | `af72d1e2017292b932148c467004bb096556553cdb6d5e9453846c12e20f258c` |
| 16 | `docs/review/project-review-2026-10-09-p5-r5-rp11-h1-oh-s3-lit-full-wp2-acceptance.md` | 27 | 1,626 | `b9a1691c6cbb9aca6c26e53ceaad08c7548d8e0aa4fb5392378701964b8be202` |
| 17 | `docs/review/project-review-2026-10-10-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-direction.md` | 34 | 1,652 | `25ea974e7d6c1d7822ac7e474d6ecb69787e6f1effbae5a7ca870e0f4a35025f` |
| 18 | `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-claude-prompt.md` | 298 | 14,613 | `2181446868adb30fd43fc0ec46224eee44ef93951c6ec617159026d263f1c9c2` |

Items 1 – 11 and 14 – 18 were read in full except as follows (stated plainly):

* **Items 12 and 13** (the 551 KB R8 proposal and the 525 KB one-host amendment
  proposal) were read at the passages the prompt and the contract cite — item 12:
  §§7.5, 7.5a, 8.1, 9.3 in full; item 13: lines 936–944, 1005–1016, 1980–2040,
  4133–4492 and 5064–5113 — not end to end.
* **Item 2, "§12.5".** The implementation plan has no heading numbered §12.5. I
  read §12.0 (lines 1178–1212) and the whole "Phase 5 — Existing automation
  migration" section (lines 1634–1925) as the only plausible referents, together
  with the reading map and §0 (1–184), §3, §5, §13, §16, §17 and §20. **Codex
  should confirm which section the prompt meant.**

Item 18's hash equals the value Peter accepted. The Claude-memory index was also
consulted; it contains no instruction that changes this scope.

## 2. Research performed

Everything is itemised in record §2 (URLs, retrieval times, byte sizes, SHA-256).
In short:

* **Authentication chain (Ubuntu).** Signed `InRelease` for `resolute`,
  `resolute-updates`, `resolute-security` (Ubuntu Archive Automatic Signing Key
  2018, fingerprint `F6ECB3762474EDA9D21B7022871920D1991BC93C`, verified with the
  host's `ubuntu-archive-keyring`) → `Sources.xz` hashes → the six files of
  `systemd 259.5-0ubuntu3.4` and `policykit-1 127-2ubuntu1.1`; all sizes and
  hashes equal the signed entries and equal R2 Appendix D. Both orig tarballs are
  byte-identical to the upstream GitHub tags `v259.5` and `127`. Retrieval:
  `InRelease` 21:52:28Z, pinned downloads 21:52:59Z–21:53:01Z, GitHub 22:12:26Z,
  Launchpad pages 22:15:33Z.
* **Not authenticated:** the uploader PGP signatures on the two `.dsc` files
  (key `50C4A0DDCF31E452CEB19B516569D855A744BE93` is not available). The record
  does not rely on them.
* **Distro patches:** systemd 40 and polkit 2 applied in full without failure
  and classified by touched files; none alters a function cited for a contract
  fact (record §2.4).
* **Other sources:** D-Bus Specification 0.43 (22:04:15Z); glibc `2.43-2ubuntu2.4`,
  dpkg `1.23.7ubuntu1`, git `1:2.53.0-1ubuntu1`, Linux man-pages `6.17-1`
  (22:07:54Z–22:07:58Z); Linux kernel `v7.0.14`/`v7.0` files and the Ubuntu
  `linux_7.0.0-31.31` diff (about 22:09Z; the Ubuntu diff hash equals R2).
* **Method limit.** Static reading only. No pinned binary was run; no bus
  message exchanged; every "server does X" means "the cited source does X in
  this version". Mechanical extraction of the systemd method/property/signal
  vtables reproduced R2 Appendix A (464) and Appendix B (126) exactly.

## 3. Disposition of every unsupported fact

| UF | Subject | Status in record | Principal residuals |
|---|---|---|---|
| UF-01 | transport, authentication, framing | supported | R-01.1 installed bus implementation/policy; R-01.2 |
| UF-02 | unit name → object | supported | R-02.1 (not needed) |
| UF-03 | wire types, typed-to-text rules | **partially supported** | R-03.1 version-bound property list (repository artifact outside reading) → WP-6/Q6-2; R-03.2 |
| UF-04 | bus error representation | supported | R-04.1, R-04.2 |
| UF-05 | job completion, cancel, abandon, disconnect, effect observation | **partially supported** | R-05.1 disconnect with pending reply; R-05.2 source-only; **R-05.3 = Q6-6, unanswered** |
| UF-06 | `StartTransientUnit` signature, mode | supported | R-06.1, R-06.2 |
| UF-07 | write-side properties, exec structure | supported | R-07.1 … R-07.3 |
| UF-08 | timer and service together | supported | R-08.1 (O-3) |
| UF-09 | `StopUnit` semantics | supported | R-09.1, R-09.2 |
| UF-10 | Polkit `CheckAuthorization` | supported | R-10.1 pidfd build option; R-10.2 |
| UF-11 | result fields → outcomes | supported | R-11.1 |
| UF-12 | process start time unit/encoding | supported | R-12.1, R-12.2 |
| UF-13 | polkitd treatment of start time, uid | supported | R-13.1 … R-13.3 |
| UF-14 | per-property reads of hidden/explicit properties | supported | R-14.1 |
| UF-15 | host nodename, machine-id hash, arch, kernel release | supported as to facts; mechanism `PSC` | R-15.1, R-15.2 |
| UF-16 | account, group, supplementary groups via NSS | supported as to facts; mechanism `PSC` | R-16.1, R-16.2 |
| UF-17 | commit identity, launcher attributes, re-read vs carried | **partially supported** (re-read/carried split not decided by accepted text) | R-17.1 … R-17.3 |
| UF-18 | installed-package records | supported as to facts; mechanism `PSC` | R-18.1, R-18.2 |

No `UF` is called closed. `UF-15` … `UF-18` carry `PSC` proposals only; their
acquisition mechanisms are **not** selected — decisions D-11 … D-14 (record
Appendix B) are Peter's. Notably `P-16.2` (library NSS) is flagged as
incompatible with the accepted boundary unless the configured NSS sources are
`files`. The full residual list with owners is record §7; the `PSC` register is
Appendix A; the Q3 readiness table (§6 of the record) closes none and states
Q3-9 and Q3-11 are not closable on the present evidence.

## 4. Principal findings for the reviewer

1. For DI-2/3/4/S a cancelled client wait, client timeout, lost connection or
   unreadable reply proves neither that a queued job stopped nor that the
   mutating request had no effect; a failure after a unit becomes transient can
   leave a jobless transient unit (A-05.4, A-05.6, A-05.12). Only an explicit
   `CancelJob` cancels, and not a job already executing. No silent retry.
2. Polkit's own source describes the PID/start-time subject form as "known
   broken" without pidfds (A-13.4), and a root caller's supplied uid is trusted
   (A-13.2). Both feed decision D-5.
3. Observations O-1 … O-6 (record Appendix C), reported and not decided: the
   `RT2.AM0.5` holder `LoadState` wording; manual-versus-source differences in
   three places; the `TimeoutStartSec` conflict between D R2 (f) and `RT2.AK1.2`;
   R2 Appendix C.1 "27" versus 28 entries; Polkit XML typos; supplied-uid trust.
4. Recommendation (record §9, separate from the evidence): review first; the
   contract could probably be completed for Q3-1 … Q3-7 after decisions D-1 …
   D-6, D-9, D-10 are recorded; Q6-6 and Q6-7 remain the real gate for
   DI-2/3/4/S behavior.

## 5. Record identity and checks

Record: `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-record.md`
— **1,085 lines; 135,576 bytes; SHA-256
`0a1b0173d6f82ef980228355e04abba0e6e40fd23bc4e2b636a825c0162a7b9a`.**
(This handback does not hash itself.)

Checks run:

* `wc -l -c` and `sha256sum` on all reading items before and after reading and on the record;
* mechanical citation check: 275 line-ranges in the record against the extracted
  sources, 0 out of bounds;
* mechanical Markdown-table parse: 36 tables, column counts consistent (one
  stray `|` escaped);
* trailing-whitespace/tab search on the record; `git diff --check` (clean for
  tracked files — it does not cover untracked files);
* `sha256sum -c` of the six pinned files against the signed index; `gpgv`
  verification of the three `InRelease` files; byte comparison of orig tarballs
  with upstream tags;
* the final link/path, whitespace and status checks listed in §6 were run after
  the pointers were replaced.

Checks **not run, by prohibition**: test suites, hook tests
(`python3 .claude/hooks/test_guards.py` was not changed and not run), builds,
formatters, linters, package installation, execution of downloaded code, any
service/database operation. No suite figure is claimed.

## 6. Files created and edited

Created: the record; this handback; four dated snapshots of the previous
(source-completion-authorization) current state —
`docs/review/Handover-information-through-2026-10-10-lit-full-wp3-source-completion-authorization.md`,
`docs/project-management/status-through-2026-10-10-lit-full-wp3-source-completion-authorization.md`,
`docs/implementation-plan-through-2026-10-10-lit-full-wp3-source-completion-authorization.md`,
`docs/operations/disposable-test-server-through-2026-10-10-lit-full-wp3-source-completion-authorization.md`;
each hash is in its archive index.

Edited (pointers and indexes only): `docs/review/Handover information`;
`docs/project-management/status.md`; `docs/implementation-plan.md` (§20 block
only); `docs/operations/disposable-test-server.md` (restriction banner, lines
1–34 only); the four archive `README.md` indexes.

Not edited: the accepted interface contract and every other prohibited file;
application code, tests, configuration, infrastructure, hooks.

## 7. Prohibited operations — confirmation and disclosures

No SSH or host access, no retained evidence, secret, credential, player data,
production, staging, `oracle-test`, Foundry or database access; no package
installation, build, test, formatter, service operation, cleanup of existing
paths, workspace recreation, OH-S4/OH-S4p or later slice, H-1/H-2, activation,
rollback, commit or push. R5 and H-0G retained paths untouched. WP-4 … WP-7 not
prepared. Downloads were confined to one fresh `0700` directory under `/tmp`
(inside the session scratchpad); nothing was vendored or executed.

Disclosures, for completeness:

* `gpg --verify` of a `.dsc` created `~/.gnupg` (a public-keyring file and a
  random-seed file only) in the executing user's home. I removed that directory,
  which I had created myself, and it had no pre-existing content.
* On the **executing workspace** (not `oracle-test`) I ran read-only
  `lsb_release -a`, `which` and `ls /usr/share/keyrings` to locate the Ubuntu
  archive keyring; `patch`, `tar` and three Python scripts ran on copies of
  downloaded source text; `git ls-remote` queried kernel.org and GitHub.
* The `.dsc` uploader signatures remain unverified (§2).

## 8. Focused questions for Codex

1. Which section did "§12.5" in the prompt mean (§1 above)?
2. Are the tier labels (`S` server source, `W` wire/spec, `R` reference client,
   `M` mapping proposal) applied honestly, and is each `ASF` supported by its
   cited lines?
3. Are the two absence-based findings (A-10.8 "decision completes inside the
   call" for flags 0; A-05.12 jobless transient unit) adequately labelled?
4. Is the uploader-signature gap acceptable given the archive signature chain?
5. Do O-1 … O-6 deserve erratum records, and are D-10 and the `UF-17` split
   correctly left undecided?
6. Does any `PSC` exceed "above WP-4 mechanics" or touch Q6-6/Q6-7?

## 9. Current state

**WP-3 SOURCE COMPLETION RETURNED — INDEPENDENT CODEX REVIEW PENDING.** Next:
Codex independent review of the cumulative return; then Peter decides whether
and how the record is integrated. No agent may treat this return as acceptance.
