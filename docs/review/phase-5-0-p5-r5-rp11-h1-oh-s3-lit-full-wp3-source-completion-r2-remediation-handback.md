# LIT-FULL WP-3 source-completion R2 remediation — handback

Work ID `C-P5.0-R5-RP11-H1-OH-S3-RT3-WP3-SC1-R2-20261011-25` · executor Claude ·
reviewer Codex (re-review pending) · decision owner Peter Duscha · 2026-10-11

**WP-3 SOURCE COMPLETION R2 REMEDIATION RETURNED — INDEPENDENT CODEX RE-REVIEW PENDING**

This is not a `HARD STOP`: every required reading item was read before the first
deliverable edit, all sixteen kernel.org objects were retrieved and identified
exactly, and all six file pairs are byte-identical. The return does **not** accept
the record, integrate it into the accepted interface contract, close or reopen any
Q3 question, answer Q6-6 or Q6-7, decide D-1 … D-14, resolve residual `R-M.1`,
authorize WP-4 … WP-7, establish concrete Route 3 or select LIT-FULL. The accepted
WP-3 `HARD STOP` stays in force.

Deliverables: the cumulatively corrected
[source-completion record](phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-record.md)
(§R2, §2.4, A-10.6, Appendix F and F.2) and this handback.

## 1. Findings and exact remediation

| Finding | Remediation (record location) |
|---|---|
| `WP3-SC-R1-RE1` — the six `v7.0` kernel-file rows and the `v7.0` tag-page and commit-page rows reused the `v7.0.14` retrieval identities | All sixteen objects (6 paths × 2 refs, plus tag page and commit page per ref) were retrieved afresh in this execution, each with its own `h=` value. §2.4 now lists each with full requested URL (equal to the effective URL; no redirect), UTC completion time, exact bytes and full SHA-256; the `v7.0.14` rows are refreshed as the other side of the comparison and no two rows share a retrieval. A separate table gives the six `cmp` results (all IDENTICAL) and the tag/commit identities of both refs are tied to the pages that print them. Wording that said the files are identical was rechecked: the §1 `KN` convention row, UF-12 sources line and A-15.2 now cite the R2 comparison. A-12.2, Appendix E.1 and Appendix E kernel provenance rows state no equality beyond what the comparison now supports and needed no change. `R-M.1` and the Ubuntu-delta text are unchanged. |
| `WP3-SC-R1-RE2` — A-10.6 and Appendix F said `uid` is optional in every Polkit process-subject form | A-10.6 now opens: `uid` is optional in the general PID/start-time form and required in the pidfd form (the "absent ⇒ −1" clause moved into the general-form sentence). The Appendix F A-10.6 summary is corrected the same way. A whole-record search for equivalent statements found none further; R1.4, A-10.5, A-10.10, A-10.12, P-10.1, A-13.2, the DI-6 row, the Q3-5/Q3-6 rows, Appendix A and O-5 were rechecked and are consistent. No request shape is selected; H-PROC.5 and D-2/D-5 are untouched. |

## 2. Required-reading ledger — completed before the first deliverable edit

Every item was read as specified before any deliverable was edited; "completely" means
first byte to end of file in this execution. Identities below were taken from the
working tree before the first edit (line/byte/SHA-256 are of the whole file even where
only named portions were required). Paths are repository-relative.

| # | Item | Lines | Bytes | SHA-256 | Portion read |
|---:|---|---:|---:|---|---|
| 1 | `.agents/AGENTS.md` | 700 | 36,014 | `87bab4ab8d67e308af0c59b99c8604235ee84d75cfa12448458b1a04cc88390a` | completely (lines 1–700) |
| 2 | `docs/implementation-plan.md` | 2,609 | 128,492 | `4ca8b3512eae1a82f3edf68f1ebf4dc7e4a8244202cc26b1b326e39c7fd14a22` | reading map and §0 (lines 1–184); §3 (267–288); §5 (353–408); §12.0 (1190–1212); the complete section headed `Phase 5 — Existing automation migration` (1634–1926, from its heading to the line before `### Phase 6`); §13 (2112–2216); §16 (2395–2492); §17 (2493–2513); §20 (2559–2609, to end of file) |
| 3 | `docs/review/Handover information` | 39 | 2,556 | `85971f4f50d155fb448818d6f968ddb09c0840c17959ca41d8c340a09725d09e` | completely |
| 4 | `docs/operations/disposable-test-server.md` | 329 | 15,583 | `c8286c9789affa34a340ba6b7a087b25addbd1af9119cafbd4ac04522bce1c37` | active restriction banner (lines 1–41) and the lines that follow it through line 80 |
| 5 | `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-record.md` (pre-edit state) | 1,660 | 231,256 | `2f1bf54f1620ae4a6b541a0271da6ad5f61abde6eae6d3d894a4a4b39a8eccff` | completely (lines 1–1660) |
| 6 | `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r1-remediation-claude-prompt.md` | 345 | 18,090 | `134e4acbf22c88aded8819e439cff1c8b3bf18556b8cf3091c2c975f8569a602` | completely |
| 7 | `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r1-remediation-handback.md` | 192 | 16,269 | `384df2c3499fc5ab5d1feb7af3b8d6bf1cda953380bd69bc362e6bee7cdb3033` | completely |
| 8 | `docs/review/project-review-2026-10-11-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r1-remediation.md` | 69 | 3,249 | `4b8dd7b4583080e5f9783d9fa51a834ef828a573fdc26b35437c19daf8e44a21` | completely |
| 9 | `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r2-remediation-claude-prompt.md` | 280 | 14,534 | `21a94f29e2860f22c4fdcccfeef3e584f2c723899377fbc11c0a3adc3900aa33` | completely |
| 10 | `docs/review/project-review-2026-10-11-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r2-remediation-acceptance-and-claude-activation.md` | 73 | 3,749 | `b0aa58bb47e5b9a725b7a76ca9e9266dc08ea990a46aa3a2379644709d834bc1` | completely |

Statement: **each item was read as specified before the first deliverable edit.** Item 9's
hash equals the value Peter recorded in item 10. The first deliverable edit followed the
kernel.org retrieval, which followed this reading. Observation (unchanged from R1):
`docs/operations/disposable-test-server.md` repeats its sections 1–4 further down; this is
pre-existing, outside the banner and was not touched.

## 3. Old defective `v7.0` rows and their corrected retrieval identities

The eight rows of the R1 record's §2.4 whose label said `v7.0` but whose URL, time, size and
hash were those of the `v7.0.14` row, with the replacement. (Corrected-identity references are
rows of the §4 table below.)

| # | Old defective R1 row (object) | Old requested URL (wrong ref) | Old time | Old bytes | Old SHA-256 (copied from the `v7.0.14` row) | Corrected identity |
|---:|---|---|---|---:|---|---|
| 1 | `kernel/sys.c` at `v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/kernel/sys.c?h=v7.0.14` | 2026-10-10T23:09:52Z | 74,515 | `418d0bd8929cb41497a73a23e6700412224b062ec6904145c0628d5225abcd5e` | §4 table row 1: `h=v7.0`, 2026-10-11T11:27:48Z, 74,515 bytes, `418d0bd8929cb41497a73a23e6700412224b062ec6904145c0628d5225abcd5e` |
| 2 | `include/uapi/linux/utsname.h` at `v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/include/uapi/linux/utsname.h?h=v7.0.14` | 2026-10-10T23:09:53Z | 684 | `e6a7aeffebf22a2d74b5e671ab5ff8bb99b0655cefb544bfca0acc22aa396c2a` | §4 table row 2: `h=v7.0`, 2026-10-11T11:27:48Z, 684 bytes, `e6a7aeffebf22a2d74b5e671ab5ff8bb99b0655cefb544bfca0acc22aa396c2a` |
| 3 | `kernel/utsname_sysctl.c` at `v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/kernel/utsname_sysctl.c?h=v7.0.14` | 2026-10-10T23:09:53Z | 3,526 | `0670f6501ebd63123e7d76d92f64ab9f450e828412bc431f5c4d63673a7fdc01` | §4 table row 3: `h=v7.0`, 2026-10-11T11:27:49Z, 3,526 bytes, `0670f6501ebd63123e7d76d92f64ab9f450e828412bc431f5c4d63673a7fdc01` |
| 4 | `fs/proc/array.c` at `v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/fs/proc/array.c?h=v7.0.14` | 2026-10-10T23:09:53Z | 23,003 | `b33ac7b8c8aa20c85d61c2eb77eec60716bbba7075870a9c358cb533c89ba85a` | §4 table row 4: `h=v7.0`, 2026-10-11T11:27:49Z, 23,003 bytes, `b33ac7b8c8aa20c85d61c2eb77eec60716bbba7075870a9c358cb533c89ba85a` |
| 5 | `fs/stat.c` at `v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/fs/stat.c?h=v7.0.14` | 2026-10-10T23:09:54Z | 27,228 | `47d331643ef846d014684819266beb580fd6da3e9430b0cdedebed53e99d9078` | §4 table row 5: `h=v7.0`, 2026-10-11T11:27:49Z, 27,228 bytes, `47d331643ef846d014684819266beb580fd6da3e9430b0cdedebed53e99d9078` |
| 6 | `fs/xattr.c` at `v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/fs/xattr.c?h=v7.0.14` | 2026-10-10T23:09:54Z | 41,353 | `2f3737b36b44f4773c872d89bbb03cfc47906beebc2b0ab21635e6b65fe71228` | §4 table row 6: `h=v7.0`, 2026-10-11T11:27:49Z, 41,353 bytes, `2f3737b36b44f4773c872d89bbb03cfc47906beebc2b0ab21635e6b65fe71228` |
| 7 | tag page `v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/tag/?h=v7.0.14` | 2026-10-10T23:10:00Z | 10,443 | `9c33ae19821d74355abf762f6bb6368a291f904a6aa12eed39abf0babc627afd` | §4 table row 7: `h=v7.0`, 2026-10-11T11:27:49Z, 10,075 bytes, `5aab24ec4c02e12d873ef2f17dd96c83a684931e35fe35421a1a9684f04b732c` |
| 8 | commit page `v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/commit/?h=v7.0.14` | 2026-10-10T23:10:01Z | 14,039 | `1a4c12737f5a3657911c78e33701ca089fcd1b8a43d6297445fa5138c4def641` | §4 table row 8: `h=v7.0`, 2026-10-11T11:27:50Z, 13,118 bytes, `b2f408fa1bc03f2af723950dec3ce7796d4a67691553cafd65061860d4906e40` |

## 4. The sixteen kernel.org retrievals (this execution)

One fresh mode-`0700` directory `/tmp/p5r2.wgEhC5` (`mktemp -d /tmp/p5r2.XXXXXX`); `env -i` with
`PATH` retained and `HOME`, `TMPDIR` and the XDG variables pointed into that directory;
`curl -q --proto '=https' --proto-redir '=https' --tlsv1.2 -fsSL`; each object fetched once;
the time is `date -u` at completion of the transfer. Base URL
`https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git`; the query parameter equals the
row label in every row; the effective URL equals the requested URL in all sixteen (no redirect).

| # | Object | Full URL requested | Effective URL | Completed (UTC) | Bytes | SHA-256 |
|---:|---|---|---|---|---:|---|
| 1 | `kernel/sys.c` at `v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/kernel/sys.c?h=v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/kernel/sys.c?h=v7.0` (same) | 2026-10-11T11:27:48Z | 74,515 | `418d0bd8929cb41497a73a23e6700412224b062ec6904145c0628d5225abcd5e` |
| 2 | `include/uapi/linux/utsname.h` at `v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/include/uapi/linux/utsname.h?h=v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/include/uapi/linux/utsname.h?h=v7.0` (same) | 2026-10-11T11:27:48Z | 684 | `e6a7aeffebf22a2d74b5e671ab5ff8bb99b0655cefb544bfca0acc22aa396c2a` |
| 3 | `kernel/utsname_sysctl.c` at `v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/kernel/utsname_sysctl.c?h=v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/kernel/utsname_sysctl.c?h=v7.0` (same) | 2026-10-11T11:27:49Z | 3,526 | `0670f6501ebd63123e7d76d92f64ab9f450e828412bc431f5c4d63673a7fdc01` |
| 4 | `fs/proc/array.c` at `v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/fs/proc/array.c?h=v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/fs/proc/array.c?h=v7.0` (same) | 2026-10-11T11:27:49Z | 23,003 | `b33ac7b8c8aa20c85d61c2eb77eec60716bbba7075870a9c358cb533c89ba85a` |
| 5 | `fs/stat.c` at `v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/fs/stat.c?h=v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/fs/stat.c?h=v7.0` (same) | 2026-10-11T11:27:49Z | 27,228 | `47d331643ef846d014684819266beb580fd6da3e9430b0cdedebed53e99d9078` |
| 6 | `fs/xattr.c` at `v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/fs/xattr.c?h=v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/fs/xattr.c?h=v7.0` (same) | 2026-10-11T11:27:49Z | 41,353 | `2f3737b36b44f4773c872d89bbb03cfc47906beebc2b0ab21635e6b65fe71228` |
| 7 | tag page `v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/tag/?h=v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/tag/?h=v7.0` (same) | 2026-10-11T11:27:49Z | 10,075 | `5aab24ec4c02e12d873ef2f17dd96c83a684931e35fe35421a1a9684f04b732c` |
| 8 | commit page `v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/commit/?h=v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/commit/?h=v7.0` (same) | 2026-10-11T11:27:50Z | 13,118 | `b2f408fa1bc03f2af723950dec3ce7796d4a67691553cafd65061860d4906e40` |
| 9 | `kernel/sys.c` at `v7.0.14` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/kernel/sys.c?h=v7.0.14` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/kernel/sys.c?h=v7.0.14` (same) | 2026-10-11T11:27:50Z | 74,515 | `418d0bd8929cb41497a73a23e6700412224b062ec6904145c0628d5225abcd5e` |
| 10 | `include/uapi/linux/utsname.h` at `v7.0.14` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/include/uapi/linux/utsname.h?h=v7.0.14` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/include/uapi/linux/utsname.h?h=v7.0.14` (same) | 2026-10-11T11:27:50Z | 684 | `e6a7aeffebf22a2d74b5e671ab5ff8bb99b0655cefb544bfca0acc22aa396c2a` |
| 11 | `kernel/utsname_sysctl.c` at `v7.0.14` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/kernel/utsname_sysctl.c?h=v7.0.14` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/kernel/utsname_sysctl.c?h=v7.0.14` (same) | 2026-10-11T11:27:50Z | 3,526 | `0670f6501ebd63123e7d76d92f64ab9f450e828412bc431f5c4d63673a7fdc01` |
| 12 | `fs/proc/array.c` at `v7.0.14` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/fs/proc/array.c?h=v7.0.14` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/fs/proc/array.c?h=v7.0.14` (same) | 2026-10-11T11:27:50Z | 23,003 | `b33ac7b8c8aa20c85d61c2eb77eec60716bbba7075870a9c358cb533c89ba85a` |
| 13 | `fs/stat.c` at `v7.0.14` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/fs/stat.c?h=v7.0.14` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/fs/stat.c?h=v7.0.14` (same) | 2026-10-11T11:27:50Z | 27,228 | `47d331643ef846d014684819266beb580fd6da3e9430b0cdedebed53e99d9078` |
| 14 | `fs/xattr.c` at `v7.0.14` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/fs/xattr.c?h=v7.0.14` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/fs/xattr.c?h=v7.0.14` (same) | 2026-10-11T11:27:51Z | 41,353 | `2f3737b36b44f4773c872d89bbb03cfc47906beebc2b0ab21635e6b65fe71228` |
| 15 | tag page `v7.0.14` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/tag/?h=v7.0.14` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/tag/?h=v7.0.14` (same) | 2026-10-11T11:27:51Z | 10,443 | `a6c6997a08392c66234e2edc12c0a78f15e9fbe79191e647bfb694475effadce` |
| 16 | commit page `v7.0.14` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/commit/?h=v7.0.14` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/commit/?h=v7.0.14` (same) | 2026-10-11T11:27:51Z | 14,039 | `8b0f599f3a89b48d5e4085c37a091b620185737816b8454db4e2ac81b1a6a04b` |

The tag and commit pages end with a `generated by cgit … at <time>` line, so their hashes
identify this retrieval only.

## 5. Byte-for-byte comparison and tag/commit identities

`cmp -s` on the two retrieved copies of each pair:

| File | `v7.0` bytes | `v7.0.14` bytes | SHA-256 equal | `cmp -s` result |
|---|---:|---:|---|---|
| `kernel/sys.c` | 74,515 | 74,515 | yes | IDENTICAL |
| `include/uapi/linux/utsname.h` | 684 | 684 | yes | IDENTICAL |
| `kernel/utsname_sysctl.c` | 3,526 | 3,526 | yes | IDENTICAL |
| `fs/proc/array.c` | 23,003 | 23,003 | yes | IDENTICAL |
| `fs/stat.c` | 27,228 | 27,228 | yes | IDENTICAL |
| `fs/xattr.c` | 41,353 | 41,353 | yes | IDENTICAL |

**All six pairs are byte-identical**, so equality is claimed (not inferred from sizes). Tag and
commit identities, each read from the page retrieved with its own `h=` value:

| Ref | Tag object | Tagged commit | Tree | Tag date, tagger |
|---|---|---|---|---|
| `v7.0` | `3131ff5a117498bb4b9db3a238bb311cbf8383ce` | `028ef9c96e96197026887c0f092424679298aae8` (commit page) | `6e2e13adb3ebf0a7a19583d58009f8372b592387` | 2026-04-12 13:48:06 -0700, Linus Torvalds |
| `v7.0.14` | `b38d6c0b6e7f406a7feb7d46f184ec3edaac8c3b` | `458c6079fc1d41d564c37679c8ace02cd83ee817` (commit page) | `8436e2406cd520564dfafab6112b18ca59a6f331` | 2026-06-27 11:07:46 +0100, Greg Kroah-Hartman |

The tag pages print the tagged commit abbreviated (`028ef9c96e…`, `458c6079fc…`); the full commit
identifier is that of the same ref's commit page. These identities equal those R1 asserted, which
the R1 retrieval had not evidenced for `v7.0`. The six SHA-256 values also equal those R1 gave for
its `v7.0.14` rows.

## 6. Changed Polkit statements

| Where | Before (R1) | After (R2) |
|---|---|---|
| A-10.6, opening | "`uid` (`i`) is **optional in every form**: absent ⇒ −1." followed by the general-form and pidfd-form clauses | "`uid` (`i`) is **optional in the general PID/start-time form and required in the pidfd form**." The general-form clause now ends "`uid` is optional (absent ⇒ −1)"; the pidfd-form clause is unchanged ("`uid` is **required** …") |
| Appendix F (R1 register), A-10.6 row | "rewritten: `uid` optional in every form; PID/start-time form requires `pid` and `start-time`; …" | rewritten to say the R1 wording "optional in every form" was self-contradictory and is superseded by R2 (F.2); PID/start-time form requires `pid` and `start-time` (`uid` optional); pidfd form requires `pidfd` and `uid` |
| Appendix F.2 | — | new R2 register rows for A-10.6 and the Appendix F correction |

No other Polkit statement was changed. Rechecked and unchanged: R1.4, A-10.5, A-10.10, A-10.12, P-10.1,
A-13.2, the DI-6 row, the Q3-5/Q3-6 readiness rows, Appendix A and O-5. The only remaining occurrences of
the phrase "optional in every" are quotations of the defect in §R2.2 and Appendix F/F.2.

## 7. Record and handback identity

`docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-record.md` —
**1,758 lines; 240,533 bytes; SHA-256 `4c2a1b76a72002de77ca885ba248f086c302b5e9aebebd117cfa90b8989a1049`**
(pre-edit: 1,660 lines; 231,256 bytes; `2f1bf54f1620ae4a6b541a0271da6ad5f61abde6eae6d3d894a4a4b39a8eccff`).
This handback does not hash itself; its line count, byte count and SHA-256 are in the chat return.

## 8. Files created and edited

Created:

| File | Lines | Bytes | SHA-256 (also in its archive index) |
|---|---:|---:|---|
| `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r2-remediation-handback.md` | this file | | not self-referential |
| `docs/review/Handover-information-through-2026-10-11-lit-full-wp3-source-completion-r2-remediation-authorization.md` | 39 | 2,556 | `85971f4f50d155fb448818d6f968ddb09c0840c17959ca41d8c340a09725d09e` |
| `docs/project-management/status-through-2026-10-11-lit-full-wp3-source-completion-r2-remediation-authorization.md` | 48 | 2,936 | `a10e18d8218eb954eead5b9ab4aaca91a38a743c723b024a0b71917b2b7185e7` |
| `docs/implementation-plan-through-2026-10-11-lit-full-wp3-source-completion-r2-remediation-authorization.md` (§20, heading to end of file) | 51 | 3,268 | `6e6192b42e2da785d4739225cd29f8f5a5d46f945dda8bafadce93a6439affe7` |
| `docs/operations/disposable-test-server-through-2026-10-11-lit-full-wp3-source-completion-r2-remediation-authorization.md` (banner lines 1–41) | 41 | 2,819 | `f7eb07aa26576e415bdd174abdbe31f95e66aa177d144d24571abccb3af7b589` |

Each snapshot was confirmed byte-identical to the canonical content it preserves (`cmp` for the
two whole-file snapshots; `sed` line ranges for the other two).

Edited: the source-completion record (in place); `docs/review/Handover information`;
`docs/project-management/status.md`; `docs/implementation-plan.md` (§20 `Current state` block
and links only); `docs/operations/disposable-test-server.md` (banner lines 1–41 only); one row
each in the four archive `README.md` indexes (`handover-archive`, `status-archive`,
`implementation-plan-archive`, `disposable-test-server-archive`).

Not edited: the accepted interface contract (byte-identical, below), the original prompt and
handback, both independent reviews, the R1 prompt and handback, all activation records, the WP-2
inventory, accepted proposals and acceptances, earlier snapshots, application code, tests, hooks,
configuration, infrastructure.

## 9. Checks

Run, all inside the repository or the fresh `/tmp` directory: `wc -l -c` and `sha256sum` of the
reading items (before the first edit) and of the record, contract and snapshots (after); the
sixteen retrievals with `curl` and `sha256sum`; `cmp -s` on the six pairs; extraction of the tag
and commit identities from the retrieved pages; a mechanical script confirming that the set of
`` `path:lines` `` citation tokens outside Appendix E.1 is identical before and after the edits (221
= 221), that no `v7.0` row cites `h=v7.0.14`, that every Markdown table of the record has regular
column counts (0 irregular rows), and that the record has no trailing whitespace or tabs; searches
of the whole record for "optional in every", "every form", "all forms", "either form", "both forms"
and `uid … optional` statements; a link/path check of the edited documents (all links resolve once
this handback exists); `git diff --check` (clean for tracked files) and read-only `git status`.

Not run, by prohibition: application and hook suites, builds, formatters, linters, package
installation, execution of downloaded code, any service or database operation. **No suite figure is
claimed.** Not re-checked, by prohibition: the Ubuntu keyring/release/index/package chain, the
Ubuntu kernel delta, systemd, Polkit and every other R1 source — R1's completed trust-anchor
remediation is not reopened, and the Polkit source text was not re-read (the `uid` correction is a
wording repair of A-10.6 against the finding and the record's own other rows, which Codex confirmed
state the pidfd requirement).

## 10. Confirmations

* **Accepted interface contract byte-identical:** `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-interface-contract.md`
  — 469 lines, 50,599 bytes, SHA-256 `b766c10f2c28ac2d32a7dc7ee4ab2c92a3cf80d67fd70f345a9f0dd7ba92c888`, before and after.
* **No host-installation or prohibited path was inspected.** No `lsb_release`, `uname`, `hostnamectl`,
  `which`, `whereis`, package-query or service command was run; no installed keyring, default GnuPG
  state, `/usr/share/keyrings`, `/etc`, `/proc`, `/sys`, installed binary, package database, shell
  profile or user configuration was read; nothing was created or modified under `~`; no SSH,
  `oracle-test`, production, staging, Foundry, database, secret, retained-evidence, R5 or H-0G path
  was touched. The shell tool's own start-up and the ordinary incidental dynamic-loader, DNS and
  TLS-CA-store use of `curl` are outside this attestation, as the prompt provides. Pre-existing
  utilities were invoked by ordinary command name; their paths and versions were not resolved or
  recorded.
* **Attempted side effects outside the allowed paths:** none. The research directory
  `/tmp/p5r2.wgEhC5` (mode 0700, containing the downloads, the manifest, a copy of the pre-edit
  record and helper scripts) was not deleted.
* No commit, push, build, test, formatter, package installation or service/database operation.
  WP-4 … WP-7 were not prepared.

## 11. Unresolved questions and decisions

Unchanged from the record: D-1 … D-14 (proposals for Peter; none accepted here); Q6-6 and Q6-7
(unanswered); R-03.1 and Q6-2; D-10 (`TimeoutStartSec` discrepancy); the `.dsc` uploader-key
non-dependency; and **residual `R-M.1`** — the Ubuntu kernel delta `7.0.0-31.31` is still not
authenticated through the current signed indexes, A-12.3 and A-15.2 still rest on the diff's equality
with R2 Appendix D, and this upstream-tag correction neither closes nor weakens that gap; it remains
disclosed and undecided for Peter. Whether the record becomes the evidence basis for contract
integration is Peter's decision after Codex's re-review.

## 12. Focused questions for Codex's independent re-review

1. Does §2.4 now evidence two independent retrievals — each row with its own `h=` value, requested = effective URL, time, bytes and full SHA-256 — and does the `cmp` table support the byte-identical claim for all six pairs?
2. Are the tag and commit identities of both refs adequately tied to the pages that print them, given that the tag pages show the tagged commit only in abbreviated form and the full commit id comes from the commit page?
3. Is the treatment of the `generated by cgit` line (hashes identifying only this retrieval) acceptable for the four HTML rows?
4. Does A-10.6 now state unambiguously that `uid` is optional in the general PID/start-time form and required in the pidfd form, and is Appendix F's A-10.6 summary consistent with it?
5. Does Appendix F.2 account for every changed statement, and is "no statement elsewhere purports to summarize the decoder as optional in every form" borne out?
6. Is `R-M.1` preserved exactly, with no wording that could be read as closed or weakened by the upstream-tag correction?

## 13. Current state

**WP-3 SOURCE COMPLETION R2 REMEDIATION RETURNED — INDEPENDENT CODEX RE-REVIEW PENDING.**
No agent may treat this return as acceptance.
