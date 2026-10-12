# LIT-FULL WP-3 source-completion R1 remediation — handback

Work ID `C-P5.0-R5-RP11-H1-OH-S3-RT3-WP3-SC1-R1-20261010-24` · executor Claude ·
reviewer Codex (re-review pending) · decision owner Peter Duscha

**WP-3 SOURCE COMPLETION R1 REMEDIATION RETURNED — INDEPENDENT CODEX RE-REVIEW PENDING**

This is not a `HARD STOP`: every required reading item was read before the first
deliverable edit, the pinned trust anchor and the whole Ubuntu chain authenticated,
and all six pinned source files matched the signed index. The return does **not**
accept the record, integrate it into the accepted interface contract, close or
reopen any Q3 question, answer Q6-6 or Q6-7, authorize WP-4 … WP-7, establish
concrete Route 3 or select LIT-FULL. The accepted WP-3 `HARD STOP` stays in force.

Deliverables: the cumulatively corrected
[source-completion record](phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-record.md)
(**the complete manifest is its §2 and Appendix E; nothing is withheld from it**) and this handback.

## 1. Findings and exact remediation

| Finding | Remediation (record location) |
|---|---|
| `WP3-SC-R1` impossible "§12.5" precondition | Record §R1.1 states that the original reference was defective and that the original normal return did not satisfy its literal stop rule; records Peter's clarification (complete `Phase 5 — Existing automation migration` section); uses this execution's fresh ledger (§2 below) as the valid pre-edit reading basis and claims no retroactive compliance. Original prompt and original handback are byte-unchanged. |
| `WP3-SC-R2` host-installation inspection / unpinned trust anchor | Whole chain repeated from the downloaded keyring and Peter's pinned fingerprint (record §2.1); all three `InRelease` signatures report exactly `F6ECB3762474EDA9D21B7022871920D1991BC93C`; every size/hash equals the authenticated index. Record §R1.2 acknowledges the original execution's disclosed `lsb_release -a`, `which`, `ls /usr/share/keyrings` and `~/.gnupg` creation and states that this remediation did none. `.dsc` uploader signatures: not required, not checked. |
| `WP3-SC-R3` incomplete manifest | Record §2 rewritten (full URLs, UTC times, bytes, full SHA-256 everywhere; tags and commits; archive-relative paths); Appendix E.1 lists all 220 line-range citations with file, enclosing symbol/element, content anchor and upstream/patched/unchanged class; E.2 gives section + anchor for named-section citations; E.3 identifies the cited repository records. Abbreviated URLs and truncated kernel hashes are gone; the 6 kernel files are now known byte-identical in `v7.0` and `v7.0.14`. |
| `WP3-SC-R4` Polkit `uid` contradiction | A-10.5/A-10.6/A-10.10 rewritten, A-10.12 added, P-10.1, A-13.2, the DI-6 row, Q3-5/Q3-6 readiness rows, Appendix A and O-5 aligned: general PID/start-time form needs `pid` + `start-time` (`uid` optional); pidfd form needs `pidfd` + `uid`; the `pkcheck`-equivalent candidate deliberately supplies `pid`, `start-time`, `uid`. No shape selected; H-PROC.5 and D-2/D-5 untouched. |

## 2. Required-reading ledger — completed before the first deliverable edit

Every item below was read as specified before any deliverable was edited ("completely"
= first byte to EOF in this execution). Identities were taken before reading and
re-checked after for the files that matter; none changed. Paths are repository-relative.

| # | Item | Lines | Bytes | SHA-256 | Portion read |
|---:|---|---:|---:|---|---|
| 1 | `.agents/AGENTS.md` | 700 | 36,014 | `87bab4ab8d67e308af0c59b99c8604235ee84d75cfa12448458b1a04cc88390a` | completely |
| 2 | `docs/implementation-plan.md` | 2,607 | 128,380 | `645a2eff6db567bd386b887854e79aa45a20bd8a51f542c1e9857e524adf13b3` | lines 1–411 (reading map, §0, §3, §5), 1178–1217 (§12.0), 1630–2217 (the complete `Phase 5 — Existing automation migration` section from its heading, continued through every following phase to §13 so that both ends of the section are covered, and all of §13), 2390–2607 (§16, §17, §18–§19, §20) |
| 3 | `docs/review/Handover information` | 37 | 2,444 | `5b5b55297c204f2c2513353ea7ceb869ebf74fecc32b96d4d2efe90f6cb5fa3f` | completely |
| 4 | `docs/operations/disposable-test-server.md` | 327 | 15,407 | `c726ed1b300878f3445170da1085754da31115d98ac68ae72d31cfbac2f711fe` | completely (active restriction banner lines 1–39) |
| 5 | `project-review-2026-10-10-…-wp3-source-completion-acceptance-and-claude-activation.md` | 58 | 2,906 | `5353cb24c820d106cc02f4ffda5b4c76dc17f275cf7678aa8633710fc7e9baca` | completely |
| 6 | `phase-5-0-…-wp3-source-completion-claude-prompt.md` | 298 | 14,613 | `2181446868adb30fd43fc0ec46224eee44ef93951c6ec617159026d263f1c9c2` | completely |
| 7 | `phase-5-0-…-wp3-source-completion-record.md` (pre-edit state) | 1,085 | 135,576 | `0a1b0173d6f82ef980228355e04abba0e6e40fd23bc4e2b636a825c0162a7b9a` | completely |
| 8 | `phase-5-0-…-wp3-source-completion-handback.md` | 221 | 14,907 | `94d6668717b1d0850d933e40a3bf3f3d353891ecfdb0680b09b153e6ac883fe7` | completely |
| 9 | `project-review-2026-10-10-…-wp3-source-completion.md` | 91 | 4,325 | `a62cc3331fb4ea2b58185a370fb0d95383ad4f5e7218dce1f6a0e9bd3b8b17ac` | completely |
| 10 | `phase-5-0-…-wp3-interface-contract.md` | 469 | 50,599 | `b766c10f2c28ac2d32a7dc7ee4ab2c92a3cf80d67fd70f345a9f0dd7ba92c888` | completely |
| 11 | `project-review-2026-10-10-…-wp3-r1-remediation-acceptance.md` | 49 | 2,945 | `576ef26b6ab56fdb5845491cd7222095fca86fe55c2397f3abf285acc5758362` | completely |
| 12 | `phase-5-0-…-oh-s2-r2-citations.md` | 1,866 | 177,481 | `299f0598bb198572f2edb994234a63956ecafc9ab1873cb10879d0a238dea1a5` | Appendix D completely (lines 1790–1825) with Appendix E (1826–1866); and the passages the record cites: §1.1 (298–326), §6 (594–667), §8 (688–723), Appendix C (1774–1789) |
| 13 | `phase-5-0-…-wp2-operation-inventory.md` | 1,450 | 230,574 | `da341efb8c29b862d63c1463e981ccfedbe1f6680de2d416ff285fdae06461fd` | the passages the record cites: lines 248–327 (H-DI1, H-PROC, H-PK2, H-SN, H-BSE), 715–745 (§7), 826–862 (§8/§8.1), 1321–1450 (§12 Q3/Q4/Q6 questions, §13, §14, §15); the `UF-01` … `UF-18` statements themselves are in item 10 §6 |
| 14 | `phase-5-0-…-wp3-source-completion-r1-remediation-claude-prompt.md` | 345 | 18,090 | `134e4acbf22c88aded8819e439cff1c8b3bf18556b8cf3091c2c975f8569a602` | completely |
| 15 | `project-review-2026-10-10-…-r1-remediation-acceptance-and-claude-activation.md` | 75 | 4,002 | `1f7d57e461676695ed539af0f90b0c223cf586821dcca54791cb084c193ef743` | completely |

Statement: **each item was read as specified before the first deliverable edit.**
Item 6's hash equals the prompt Peter accepted for the original run; item 14's
equals the value in item 15. Observation: `docs/operations/disposable-test-server.md`
contains a second copy of its sections 1–4 (roughly lines 188–327 repeat 40–186);
this is pre-existing, outside the banner and was not touched.

## 3. Peter's clarification and trust-anchor decision as applied

* "§12.5" meant the complete section headed `Phase 5 — Existing automation
  migration`; recorded in record §R1.1.
* Pinned fingerprint `F6ECB3762474EDA9D21B7022871920D1991BC93C`. Keyring URL
  `https://archive.ubuntu.com/ubuntu/project/ubuntu-archive-keyring.gpg`, retrieved
  2026-10-10T23:08:13Z, **3,607 bytes**, SHA-256
  `80a36b0a6de2f69f49d2df75ef473ccde121e9e190b9ea01d20a4f63778d5c31`. Offline
  listing of that file: three primary keys, no subkeys — `790BC7277767219C42C86F933B4FE6ACC0B21F32`
  (Archive 2012), `843938DF228D22F7B3742BC0D94AA3F0EFE21092` (CD Image 2012) and
  `F6ECB3762474EDA9D21B7022871920D1991BC93C` (Archive 2018, **present**). Each
  `InRelease` verified with `GOODSIG 871920D1991BC93C` and `VALIDSIG` signing and
  primary fingerprints both `F6ECB3762474EDA9D21B7022871920D1991BC93C`.
* No size or hash differed from the authenticated index, no other key, mirror, package
  version or nearby source version was used: **no `HARD STOP` condition arose.**

## 4. Authentication chain and manifest corrections

The complete chain (keyring → three `InRelease` → three `Sources.xz` → stanzas →
six files) and every other object are tabulated with full URL, time, bytes and
SHA-256 in record §2.1–§2.6 and, per citation, in Appendix E. Summary of corrections
relative to the original return:

* the installed keyring is replaced by the downloaded, pinned one;
* every URL in full; every retrieval time per object; kernel hashes complete;
* the six kernel files are byte-identical in `v7.0` and `v7.0.14` (original said four);
  tag objects and commits for both tags are recorded (`v7.0.14`: tag
  `b38d6c0b6e7f406a7feb7d46f184ec3edaac8c3b`, commit `458c6079fc1d41d564c37679c8ace02cd83ee817`;
  `v7.0`: tag `3131ff5a117498bb4b9db3a238bb311cbf8383ce`, commit
  `028ef9c96e96197026887c0f092424679298aae8`); systemd `v259.5` tag object
  `4f8299955d8edfa6dab6879cbd7f199274b121fc` → commit `b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a`; polkit `127` commit
  `9e4894c969eecf26a3ba762f4f7a268aa0fb3e51`;
* the glibc (103) and man-pages (13) distro series, not applied originally, were applied
  without failure; glibc citations are stated in unpatched numbering and the one
  patched cited file (`nss/nss_database.c`, +2 shift) and the one patched man page
  (`nsswitch.conf.5`, outside the cited text) are identified;
* **new disclosed gap:** the Ubuntu kernel delta `7.0.0-31.31` is no longer in the signed
  indexes (current: `7.0.0-38.38`; pool path 404); the diff was retrieved from
  Launchpad and equals R2 Appendix D, but is **not** chain-authenticated — recorded as
  §2.4 and residual `R-M.1`; only A-12.3 and A-15.2 use it;
* Launchpad HTML pages and ref advertisements are dynamic; their hashes (which differ from
  the original record's for the Launchpad pages) identify this retrieval only.

What the chain proves and does not prove, and the uploader-key non-dependency, are in record §2.1.

## 5. Changed `ASF`, `MD`, `PSC`, residual and Q3-readiness statements

Complete register: record **Appendix F**. In short — changed: A-01.5 (quotation made
exact), A-10.5, A-10.6, A-10.7 (citations), A-10.10, new A-10.12, P-10.1, A-13.2,
the DI-6 row of §5, Q3-5 and Q3-6 readiness fact lists, Q3-11 row (sentence that
`PO3-11.1` stays in force and no mechanism is selected; state unchanged), new residual
`R-M.1`, Appendix A P-10.1 row, O-5, answers 1–2 of §8, and every citation path.
**No** Q3 question is closed or reopened; Q3-9 and Q3-11 remain not closable; Q6-6
and Q6-7 remain unanswered; D-1 … D-14 remain proposals; no `PSC` selects an API,
parser, library, language, syscall sequence, process-creation mechanism, retry
algorithm, static-image architecture or buffer size.

## 6. Files created and edited

Created: this handback; four dated, verbatim snapshots of the R1-authorization pointers,
named `…-through-2026-10-10-lit-full-wp3-source-completion-r1-remediation-authorization.md`:

| Snapshot | Lines | Bytes | SHA-256 (also in its archive index) |
|---|---:|---:|---|
| `docs/review/Handover-information-through-2026-10-10-lit-full-wp3-source-completion-r1-remediation-authorization.md` | 37 | 2,444 | `5b5b55297c204f2c2513353ea7ceb869ebf74fecc32b96d4d2efe90f6cb5fa3f` |
| `docs/project-management/status-through-2026-10-10-lit-full-wp3-source-completion-r1-remediation-authorization.md` | 46 | 2,824 | `6cdbebbcd6f371cac10d8fa24c2b23229978ef9694e7a490ccf2bb2d963854da` |
| `docs/implementation-plan-through-2026-10-10-lit-full-wp3-source-completion-r1-remediation-authorization.md` (§20 block) | 49 | 3,156 | `4832c8f2a86f8550bcc29ddb96c40053b080dba420b9b550d750b2ec5c115a15` |
| `docs/operations/disposable-test-server-through-2026-10-10-lit-full-wp3-source-completion-r1-remediation-authorization.md` (banner lines 1–39) | 39 | 2,643 | `17e47cb22dd19646e656d7c467b7c3e524aebe413781ffc3752036a76846709c` |

Edited: the source-completion record (in place); `docs/review/Handover information`;
`docs/project-management/status.md`; `docs/implementation-plan.md` (§20 block only);
`docs/operations/disposable-test-server.md` (banner lines 1–39 only); the four archive
`README.md` indexes (one row each). Not edited: the accepted interface contract
(byte-identical, SHA-256 `b766c10f…c888`, 469 lines, 50,599 bytes), the original prompt, the
original handback, the independent review, the activation records, the WP-2 inventory,
earlier snapshots, application code, tests, hooks, configuration, infrastructure.

## 7. Record identity

`docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-record.md` —
**1,660 lines; 231,256 bytes; SHA-256 `2f1bf54f1620ae4a6b541a0271da6ad5f61abde6eae6d3d894a4a4b39a8eccff`**
(pre-edit: 1,085 lines; 135,576 bytes; `0a1b0173…a7b9a` as in the ledger). This handback does
not hash itself.

## 8. Checks

Run (all inside the repository or the fresh `/tmp` directory): `wc -l -c` and `sha256sum`
of all reading items before and after reading, of the record, and of the preserved files;
`sha256sum -c` of the six pinned files and of the glibc, dpkg, git and man-pages files
against the authenticated `Sources` entries (all OK); `gpg --show-keys` offline listing;
`gpgv` of three `InRelease`; byte comparison of the `orig` tarballs with the upstream
tag archives (identical); byte comparison of the six kernel files across tags
(identical); `patch -p1` of four patch series (all applied); mechanical extraction and
resolution of all line-range citations against the extracted trees with a bounds check
(220 citations, 0 unresolved, 0 out of bounds); mechanical Markdown-table column check
of the record (0 irregular rows); trailing-whitespace/tab search of the record; link/path
check and `git diff --check` and read-only `git status`/`git diff` (final results in §9).

Not run, by prohibition: test suites, hook tests, builds, formatters, linters, package
installation, execution of downloaded code, any service/database operation. No suite
figure is claimed. Not checked: `.dsc` uploader signatures (not required).

## 9. Prohibited operations and final verification

No installed keyring, default GnuPG home, `/usr/share/keyrings`, `/etc`, `/proc`, `/sys`,
package database, service, shell profile or user configuration was read or written; nothing
was created under `~`; no `lsb_release`, `uname`, `hostnamectl`, `which`, `whereis`,
package-query or service command was run; no SSH, `oracle-test`, production, staging,
Foundry, database, secret, retained evidence, R5 or H-0G path was touched; nothing was
installed, built, formatted, committed or pushed; WP-4 … WP-7 were not prepared. The shell
tool's own start-up and ordinary incidental dynamic-loader/DNS/TLS-store use are outside
this attestation, as the prompt provides. No tool attempted a side effect outside the
repository or the fresh directory. The research directory `/tmp/p5r1.Hy69ok` (mode 0700)
was not deleted.

## 10. Unresolved questions and decisions

Unchanged from the record: D-1 … D-14 (Peter); Q6-6, Q6-7 (WP-6); R-03.1 and Q6-2; D-10
(`TimeoutStartSec` discrepancy); the uploader-key non-dependency; and the new `R-M.1`
(kernel-delta authentication). Whether the record becomes the evidence basis for contract
integration is Peter's decision after Codex's re-review.

## 11. Focused questions for Codex

1. Are the 15 reading items and the §2 "read from the heading through every phase to §13" treatment of the Phase 5 section acceptable for `WP3-SC-R1`?
2. Is the downloaded-keyring chain (§2.1) self-contained, and is the stated limit of what it proves honest?
3. Is Appendix E (220 citations, symbols, anchors, provenance) sufficient for `WP3-SC-R3`, and is the `GL` unpatched-numbering convention acceptable?
4. Is the kernel-delta authentication gap (`R-M.1`) adequately disclosed, or should a different authentication source be requested?
5. Do A-10.5/A-10.6/A-10.10/A-10.12/P-10.1 now state the three shapes without selecting one?
6. Does Appendix F account for every changed statement?

## 12. Current state

**WP-3 SOURCE COMPLETION R1 REMEDIATION RETURNED — INDEPENDENT CODEX RE-REVIEW PENDING.**
No agent may treat this return as acceptance.
