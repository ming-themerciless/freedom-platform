# LIT-FULL WP-3 source-completion record — version-bound primary-source evidence (R1- and R2-corrected)

Work ID `C-P5.0-R5-RP11-H1-OH-S3-RT3-WP3-SC1-20261010-23`, cumulatively corrected
in place by R1 remediation work ID `C-P5.0-R5-RP11-H1-OH-S3-RT3-WP3-SC1-R1-20261010-24` ·
executor Claude · 2026-10-10 · repository reads plus bounded primary-source
retrieval into one fresh `/tmp` directory; no installed keyring or other
host-installation state read by the R1 remediation; no retained evidence.
(The *original* execution's disclosed host-installation inspection is a
historical fact, stated in §R1.2; it is not erased by this correction.) Corrected
again in place by R2 remediation work ID `C-P5.0-R5-RP11-H1-OH-S3-RT3-WP3-SC1-R2-20261011-25`
(executor Claude, 2026-10-11; repository reads plus the bounded kernel.org retrieval of
§2.4 into a second fresh `/tmp` directory; no host-installation state read; no retained evidence).

**WP-3 SOURCE COMPLETION R2 REMEDIATION RETURNED — INDEPENDENT CODEX RE-REVIEW PENDING**

This record supplies evidence for the eighteen unsupported facts `UF-01` …
`UF-18` of the accepted, R1-corrected [WP-3 interface contract](phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-interface-contract.md).
It does **not** edit that contract, close any Q3 question, accept itself, answer
Q6-6 or Q6-7, authorize WP-4 … WP-7, establish concrete Route 3 or select
LIT-FULL. The accepted WP-3 `HARD STOP` remains in force until Peter Duscha
decides, after independent Codex re-review, whether and how this record is
integrated. Companions: [original handback](phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-handback.md)
(unchanged historical evidence), the [R1 remediation handback](phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r1-remediation-handback.md)
and the [R2 remediation handback](phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r2-remediation-handback.md).

## R1. R1 remediation record (findings `WP3-SC-R1` … `WP3-SC-R4`)

Authority: [accepted R1 remediation prompt](phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r1-remediation-claude-prompt.md)
(345 lines, 18,090 bytes, SHA-256 `134e4acbf22c88aded8819e439cff1c8b3bf18556b8cf3091c2c975f8569a602`)
and its [acceptance and activation](project-review-2026-10-10-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r1-remediation-acceptance-and-claude-activation.md);
findings from the [independent Codex review](project-review-2026-10-10-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion.md).
Nothing below accepts a source fact, selects an implementation mechanism, closes
a Q3 question or answers Q6-6 or Q6-7. Appendix F lists every statement this
correction changed.

### R1.1 `WP3-SC-R1` — the reading precondition

* The original accepted prompt required reading implementation-plan "§12.5".
  **That reference was defective:** the plan has no heading numbered §12.5. The
  original execution read §12.0 and the section headed `Phase 5 — Existing
  automation migration` as the "only plausible referents" and then continued to a
  normal return. **The original normal return did not satisfy the prompt's literal
  stop rule** (an item that cannot be read as specified ⇒ `HARD STOP` before editing
  a deliverable). The original prompt and original handback are preserved unchanged
  as historical evidence.
* Peter's clarification (R1 prompt, "Peter's clarifications", item 1): the intended
  section was the complete section headed `Phase 5 — Existing automation migration`
  under implementation-plan §12; the heading, not the line numbers, controls.
* **Reading basis of this corrected record.** The R1 execution read all fifteen
  items of the R1 prompt's reading list, including that complete Phase 5 section
  (read from its heading through the line before §13 so that either end of the
  section is covered), before its first deliverable edit. Their path, line, byte and
  SHA-256 ledger is in §1 of the R1 remediation handback. The original execution is
  **not** credited with retroactive compliance; this ledger is the valid pre-edit
  reading basis of the corrected record.

### R1.2 `WP3-SC-R2` — trust anchor and host-installation inspection

* The original execution authenticated the Ubuntu archive chain with an installed
  keyring (`/usr/share/keyrings/ubuntu-archive-keyring.gpg`) and, as its own handback
  disclosed, ran `lsb_release -a`, `which` and `ls /usr/share/keyrings` on the
  executing workspace; `gpg` also created, and the executor removed, `~/.gnupg`. The
  original record's statements that "no host was contacted" and that nothing was
  inspected were therefore incomplete, and the installed keyring's provenance was
  not recorded. Those are historical facts and are acknowledged here, not erased.
* **The R1 remediation performed none of these.** It downloaded the keyring from
  the official URL Peter authorized into the fresh research directory, listed its
  fingerprints offline, required the pinned fingerprint
  `F6ECB3762474EDA9D21B7022871920D1991BC93C` both in the listing and as the signing
  fingerprint of every `InRelease`, and then repeated the whole chain (§2.1). It read
  no installed keyring, default GnuPG state, `/usr/share/keyrings`, `/etc`, `/proc`,
  `/sys`, package database, service or shell profile, and wrote nothing under `~`
  (`HOME`, `GNUPGHOME`, `TMPDIR` and the XDG variables pointed into the research
  directory; `curl` ran with `-q`). Ordinary incidental runtime use of the dynamic
  loader, shared libraries, DNS configuration and the TLS CA store is not host
  evidence and supports no finding.
* The `.dsc` uploader signatures are **not** required by this assignment and were not
  checked; the uploader key was not fetched. This is a disclosed non-dependency.

### R1.3 `WP3-SC-R3` — manifest

§2 is rewritten: every authoritative object has its full URL, UTC retrieval time,
byte count and full SHA-256 (no ellipsis anywhere); versions, tags and commits are
given where they apply; Appendix E lists **every** line-range citation of this
record with its archive-relative path, enclosing symbol or element, a content
anchor, and whether the cited lines are upstream text, Ubuntu-patched or untouched
by the Ubuntu patch series; named-section citations (specification, manual and
man-page passages without usable line numbers) carry a section name and a content
anchor (Appendix E.2). All abbreviated paths and URLs of the original §2 and §§3–4
were expanded. Where an object cannot be authenticated through the archive chain
(the Ubuntu kernel delta) that is stated in §2.4, not hidden.

### R1.4 `WP3-SC-R4` — Polkit `unix-process` `uid`

A-10.5, A-10.6, A-10.10, a new A-10.12, P-10.1, A-13.2, the DI-6 row of §5, the
Q3-5/Q3-6 rows of §6, Appendix A and O-5 now distinguish three things that the
original text had merged: (1) the **general polkit 127 PID/start-time form** — `pid`
and `start-time` required, `uid` optional; (2) the **pidfd form** — this version
requires `pidfd` **and** `uid`; (3) the **`pkcheck`-equivalent `PSC` candidate**,
which deliberately supplies `pid`, `start-time` and `uid`. Neither request shape is
selected, H-PROC.5 is not amended, and D-2/D-5 are not decided.

## R2. R2 remediation record (findings `WP3-SC-R1-RE1` and `WP3-SC-R1-RE2`)

Authority: [accepted R2 remediation prompt](phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r2-remediation-claude-prompt.md)
(280 lines, 14,534 bytes, SHA-256 `21a94f29e2860f22c4fdcccfeef3e584f2c723899377fbc11c0a3adc3900aa33`)
and its [acceptance and activation](project-review-2026-10-11-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r2-remediation-acceptance-and-claude-activation.md);
findings from the [independent Codex R1 re-review](project-review-2026-10-11-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r1-remediation.md).
The reading ledger of this execution is in §2 of the [R2 remediation handback](phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-r2-remediation-handback.md).
Nothing below accepts a source fact, selects an implementation mechanism, closes or reopens a
Q3 question, answers Q6-6 or Q6-7, decides D-1 … D-14, or touches residual `R-M.1`.
Appendix F.2 lists every statement this correction changed.

### R2.1 `WP3-SC-R1-RE1` — the kernel manifest

* **Defect.** In R1, the six `v7.0` file rows and the `v7.0` tag-page and commit-page rows of
  §2.4 carried the `h=v7.0.14` URL, timestamp, byte count and SHA-256 of the corresponding
  `v7.0.14` rows. The R1 claim that the files are identical in the two tags was therefore not
  evidenced by two independent retrievals.
* **Remediation.** All sixteen objects (six paths × two refs, plus the tag page and commit page of
  each ref) were retrieved afresh from the official kernel.org stable-tree cgit service, each with
  its own `h=` value, and recorded one by one in §2.4 with full requested URL (equal to the effective
  URL; no redirect), UTC completion time, exact byte count and full SHA-256.
* **Result.** All six pairs are byte-identical by `cmp`; the tag and commit identities of both refs
  are those §2.4 states. The former equality claim is thus now evidenced; it was correct, but R1 had
  not shown it. A-12.2 and A-15.2 were rechecked: their kernel content is unchanged; the
  statements that the two tags are identical now point to the R2 comparison. Appendix E.1's `KN`
  citations (CI-188, CI-207 … CI-209) are unchanged: they cite the `v7.0.14` files and every cited
  line still resolves.
* **Unchanged.** The Ubuntu kernel delta `7.0.0-31.31` and residual `R-M.1` are exactly as in R1:
  the upstream-tag comparison neither closes nor weakens the separate Ubuntu-delta authentication
  gap (§2.4, §7). The delta was not re-downloaded.

### R2.2 `WP3-SC-R1-RE2` — Polkit `unix-process` `uid`

* **Defect.** The opening of A-10.6 and the A-10.6 row of Appendix F said `uid` is "optional in every
  form" while the same rows correctly said the pidfd form requires it.
* **Remediation.** A-10.6 now opens: `uid` is optional in the general PID/start-time form and required
  in the pidfd form; the Appendix F row is corrected the same way and cross-refers to F.2. A search of the whole
  record for equivalent statements ("every form", "all forms", "either form", "both forms",
  "optional in …", "… optional") found no further statement that purports to summarize the decoder
  as optional in every form; R1.4, A-10.5, A-10.10, A-10.12, P-10.1, A-13.2, the DI-6 row, the Q3-5 and
  Q3-6 rows, Appendix A and O-5 were rechecked and are consistent with the three shapes
  (general form: `uid` optional; pidfd form: `pidfd` and `uid` required; `pkcheck`-equivalent
  `PSC` candidate: `pid`, `start-time` and `uid` supplied deliberately). Neither request shape is
  selected, H-PROC.5 is not amended and D-2/D-5 are not decided.

## 1. Scope, boundary, source hierarchy and class definitions

**Scope.** Exactly the objective of the accepted prompt: a version-bound
evidence record for `UF-01` … `UF-14`, and a separately classified fact-and-
proposal record for the acquisition mechanisms of `UF-15` … `UF-18`. The seven
interfaces (DI-1 … DI-6, DI-S) and 41 call sites are those of the accepted
contract (§2 there) and are not re-derived.

**Preserved accepted boundary** (unchanged by this record): baseline v1.8;
LIT-FULL under R3-ROOT is a readiness investigation only; concrete Route 3 is
unestablished; in scope are exactly RT-1 … RT-5, SA-1 (`start`) and SA-2
(`stop`); F-1 is B2-F, both lifecycle acts are in, B3-OUT is effective; EX-1 and
EX-2 are effective only for their accepted uses and no EX-3 exists; no dynamic
child or distribution executable beneath a first design-controlled root image;
DI-6 is the only retained replacement-child intent; H-1, RB-1, RS-1 and H-1R are
outside the set; Q6-6 and Q6-7 are unanswered; BC-2 is a later WP-9 decision;
WP-4 … WP-7 are separately gated. A cancelled client wait is not proof that a
queued job stopped or that a mutating request had no effect, and no silent retry
follows from it.

**Source hierarchy** (highest first; a lower source never overrides a higher):
(1) `.agents/AGENTS.md`, `docs/implementation-plan.md`, `docs/review/Handover
information`; (2) the accepted WP-2 inventory, R8 proposal, one-host design
amendment, the accepted contract and the R2 citation record; (3) the primary
sources of §2, each bound to the version stated there. A distro-patched fact is
never replaced silently by an upstream fact (§2.7).

**Fact classes** (the prompt's five, each statement carries exactly one):

| Class | Meaning in this record |
|---|---|
| `ASF` | Authoritative source fact: stated by an exact primary-source citation, bound to the version in §2. |
| `MD` | Mechanical derivation from cited `ASF` facts; the derivation is stated. |
| `DR` | Already accepted design requirement from the repository (WP-2, R8, the contract); quoted, not extended. |
| `PSC` | Proposed source-completion mechanism for Peter's later decision. Never an accepted fact; closes nothing. |
| `UF` | Fact still unsupported after the authorized research; the exact residual is named. |

Every `ASF`/`MD` row additionally carries a **tier** so that server behavior,
wire contract, proposed mapping and implementation choice are never merged
(review question 3): `S` = behavior of the pinned manager or authority
implementation; `W` = published wire/API contract (D-Bus specification, interface
XML, manual); `R` = behavior of a *reference client* shipped in a pinned source
(`systemctl`, `systemd-run`, `pkcheck`, systemd's own Polkit client); an `R` row
shows how a client does something and is never a contract. `PSC` rows are tier
`M` (proposed outcome mapping) and no row is tier `I` (implementation choice):
**no language, library, binding, parser, syscall sequence, static-image
architecture, buffer size, retry algorithm or process-creation mechanism is
chosen anywhere in this record.**

**Citation conventions (R1, exact).** A citation is written `` `path:lines` ``, where
`path` is the path **inside the unpacked source archive named in §2** with the
archive's single top-level directory removed, and `lines` are 1-based line numbers
of that file:

| Prefix | Archive and tree the path is relative to | Numbering |
|---|---|---|
| `SD` | `systemd-259.5/` of `systemd_259.5.orig.tar.gz` **after the 40 Ubuntu patches** of §2.7; paths beginning `debian/` are in `systemd_259.5-0ubuntu3.4.debian.tar.xz` | post-patch |
| `PK` | `polkit-127/` of `policykit-1_127.orig.tar.gz` after the 2 Ubuntu patches (none touches a cited file) | post-patch (= upstream) |
| `GL` | `glibc-2.43/` of `glibc_2.43.orig.tar.xz`; paths beginning `debian/` are in the `debian.tar.xz` | **unpatched upstream** (the 103 Ubuntu patches shift some later lines; Appendix E says where a cited file is patched) |
| `DP` | `dpkg-1.23.7ubuntu1/` of `dpkg_1.23.7ubuntu1.tar.xz` (native format) | as shipped |
| `GT` | `git-2.53.0/` of `git_2.53.0.orig.tar.xz` | upstream (no Ubuntu patch series) |
| `MP` | `manpages-6.17/` of `manpages_6.17.orig.tar.xz` (page files are `man/man<N>/<name>.<N>`) | named section + content anchor, no line numbers |
| `KN` | Linux `v7.0.14` file fetched from `git.kernel.org` (byte-identical to the `v7.0` file for each of the six files in §2.4, established by the R2 comparison) | upstream; Ubuntu delta recorded separately |
| `DB §name` | D-Bus Specification 0.43, section heading `name` | section + content anchor (Appendix E.2) |

A systemd manual line range is written as a file path, e.g.
`man/org.freedesktop.systemd1.xml:1275-1276`. Repository records (`R2`, `W2`, `D`,
`R8`, the contract) are cited by their own line numbers in this working tree; their
identities are in Appendix E.3. **Appendix E.1 lists every line-range citation of
this record**, mechanically extracted from the final text, with the resolved file,
enclosing symbol or XML element, a content anchor (the first cited line, quoted) and
its provenance class; the enclosing symbol is the nearest preceding definition at
the first cited line and can name a neighbouring definition when a range begins in
file-scope declarations. Statements of what a source "does" are static-reading
statements (§2.8).

## 2. Authoritative-source manifest (R1: exact and reproducible)

**Retrieval environment.** Everything below **except the sixteen kernel.org upstream rows of
§2.4** (files, tag pages and commit pages, which the R2 remediation re-retrieved on 2026-10-11
into its own fresh directory, as §2.4 states) was retrieved on 2026-10-10 between
23:08:13Z and 23:10:58Z by the R1 remediation into **one fresh mode-`0700` directory**
created with `mktemp -d /tmp/p5r1.XXXXXX` (this execution: `/tmp/p5r1.Hy69ok`), with
sub-directories for downloads, extracted sources, command output, the GnuPG home and
helper scripts. `HOME`, `TMPDIR`, `GNUPGHOME` and the XDG variables were set into that
directory; `curl -q --proto '=https' --proto-redir '=https' --tlsv1.2 -fsSL` fetched
each object once; times are the system clock in UTC (`date -u`) at completion of the
transfer. Nothing was installed, built, vendored or executed; archives were unpacked
with `tar --no-same-owner --no-same-permissions`, Ubuntu patches were applied with GNU
`patch -p1` to copies, and small read-only Python scripts parsed text. The directory
is not part of the repository; this section and Appendix E are what makes its content
reproducible.

### 2.1 Trust anchor and authentication chain for the Ubuntu archive sources

**Trust anchor (Peter's R1 decision).** The expected key is the Ubuntu Archive
Automatic Signing Key (2018), fingerprint `F6ECB3762474EDA9D21B7022871920D1991BC93C`.
The keyring container was retrieved from the official URL and used only after the
checks below.

| Object | Full URL requested | Retrieved (UTC, completion) | Bytes | SHA-256 | Verification / note |
|---|---|---|---:|---|---|
| Ubuntu archive keyring (trust-anchor container) | `https://archive.ubuntu.com/ubuntu/project/ubuntu-archive-keyring.gpg` | 2026-10-10T23:08:13Z | 3,607 | `80a36b0a6de2f69f49d2df75ef473ccde121e9e190b9ea01d20a4f63778d5c31` | offline listing contains the pinned fingerprint; see §2.1 |

**Offline fingerprint listing of that exact file** (`gpg --homedir <research
dir>/g --no-autostart --no-auto-key-retrieve --show-keys --with-colons --fingerprint
--with-subkey-fingerprint <keyring>`; no keyserver, no Web of Trust, no default home).
The listing contains three primary keys and no subkeys:

| Primary-key fingerprint | User ID |
|---|---|
| `790BC7277767219C42C86F933B4FE6ACC0B21F32` | Ubuntu Archive Automatic Signing Key (2012) |
| `843938DF228D22F7B3742BC0D94AA3F0EFE21092` | Ubuntu CD Image Automatic Signing Key (2012) |
| `F6ECB3762474EDA9D21B7022871920D1991BC93C` | Ubuntu Archive Automatic Signing Key (2018) — **the pinned fingerprint is present** |

**Signed release files.** Each was verified with `gpgv --homedir <research dir>/g
--keyring <downloaded keyring> --status-fd 1 --output <verified text> InRelease`. All three
reported `GOODSIG 871920D1991BC93C` and a `VALIDSIG` whose signing-key and
primary-key fields are **both** exactly `F6ECB3762474EDA9D21B7022871920D1991BC93C`
(`[GNUPG:] VALIDSIG F6ECB3762474EDA9D21B7022871920D1991BC93C <date> <epoch> 0 4 0 1 10 01 F6ECB3762474EDA9D21B7022871920D1991BC93C`):

| Object | Full URL requested | Retrieved (UTC, completion) | Bytes | SHA-256 | Verification / note |
|---|---|---|---:|---|---|
| `resolute` `InRelease` | `https://archive.ubuntu.com/ubuntu/dists/resolute/InRelease` | 2026-10-10T23:08:18Z | 135,549 | `45f95ce276cdba3e41870516a130e03c58b8b7a79e9546b0efe9e526d255740c` | signed 2026-04-23 17:07:30Z (`Date:` 2026-04-23 17:07:15 UTC); `VALIDSIG` primary fingerprint `F6ECB3762474EDA9D21B7022871920D1991BC93C` |
| `resolute-updates` `InRelease` | `https://archive.ubuntu.com/ubuntu/dists/resolute-updates/InRelease` | 2026-10-10T23:08:19Z | 137,401 | `6d5bc27919996fe671a69a36372f25ffc59a3ea6f3bb6eef2609db23f585802e` | signed 2026-10-10 13:15:19Z (`Date:` 2026-10-10 13:15:02 UTC); same `VALIDSIG` fingerprint |
| `resolute-security` `InRelease` | `https://archive.ubuntu.com/ubuntu/dists/resolute-security/InRelease` | 2026-10-10T23:08:19Z | 137,403 | `a26a066f41f5252fab95a265d88d3ee2147beac79849b452377136364b85039f` | signed 2026-10-10 03:48:31Z (`Date:` 2026-10-10 3:48:18 UTC); same `VALIDSIG` fingerprint |

**Source indexes**, verified against the signed `SHA256:` section of the matching
`InRelease`:

| Object | Full URL requested | Retrieved (UTC, completion) | Bytes | SHA-256 | Verification / note |
|---|---|---|---:|---|---|
| `resolute` `Sources.xz` | `https://archive.ubuntu.com/ubuntu/dists/resolute/main/source/Sources.xz` | 2026-10-10T23:08:19Z | 1,001,572 | `dce0fc8e2a473b26f729b1204fd4c12ae068428f743f96761392a059ab7bbfcd` | equals the SHA-256 and size listed in the verified `resolute` `InRelease` |
| `resolute-updates` `Sources.xz` | `https://archive.ubuntu.com/ubuntu/dists/resolute-updates/main/source/Sources.xz` | 2026-10-10T23:08:19Z | 342,076 | `5b27c98885f1e9e8d72f66c890e4524fcffe70709cb7548528fceecaa153f4ae` | equals the entry in the verified `resolute-updates` `InRelease` |
| `resolute-security` `Sources.xz` | `https://archive.ubuntu.com/ubuntu/dists/resolute-security/main/source/Sources.xz` | 2026-10-10T23:08:20Z | 190,652 | `383ad7201f153fa6376f059234c691211651fe65e2539fe169d1e544fb272165` | equals the entry in the verified `resolute-security` `InRelease` |

**Stanzas.** `systemd 259.5-0ubuntu3.4` and `policykit-1 127-2ubuntu1.1` appear in
the `Sources` of both `resolute-updates` and `resolute-security`, with identical file
lists; the `Checksums-Sha256` lines of the stanza are the expected values of the next
table. Likewise `glibc 2.43-2ubuntu2.4` (`resolute-security` and `resolute-updates`,
identical), `dpkg 1.23.7ubuntu1`, `git 1:2.53.0-1ubuntu1` and `manpages 6.17-1`
(`resolute`).

**The six pinned source files** (all from `https://archive.ubuntu.com/ubuntu/pool/main/`):

| Object | Full URL requested | Retrieved (UTC, completion) | Bytes | SHA-256 | Verification / note |
|---|---|---|---:|---|---|
| systemd `orig` tarball | `https://archive.ubuntu.com/ubuntu/pool/main/s/systemd/systemd_259.5.orig.tar.gz` | 2026-10-10T23:08:47Z | 17,336,729 | `80ed55a8a69c4bd1fb12a36659303372b37baf9ee224ef4f032db4b748be0f76` | size and SHA-256 equal the `Checksums-Sha256` entry of the authenticated `Sources` stanza (`sha256sum -c`: OK) |
| systemd Ubuntu `debian` tarball | `https://archive.ubuntu.com/ubuntu/pool/main/s/systemd/systemd_259.5-0ubuntu3.4.debian.tar.xz` | 2026-10-10T23:08:47Z | 267,032 | `34048bc4b67dce61835a5a959d903f912d68bb09a93ba654e6ae33410c74aaa9` | size and SHA-256 equal the `Checksums-Sha256` entry of the authenticated `Sources` stanza (`sha256sum -c`: OK) |
| systemd `.dsc` | `https://archive.ubuntu.com/ubuntu/pool/main/s/systemd/systemd_259.5-0ubuntu3.4.dsc` | 2026-10-10T23:08:47Z | 8,779 | `c4c764e0b98b7840619f16f42fb8229a344bc2946bd1a74612280d5e218f8177` | size and SHA-256 equal the `Checksums-Sha256` entry of the authenticated `Sources` stanza (`sha256sum -c`: OK) |
| polkit `orig` tarball | `https://archive.ubuntu.com/ubuntu/pool/main/p/policykit-1/policykit-1_127.orig.tar.gz` | 2026-10-10T23:08:48Z | 472,872 | `9b7bc16f086479dcc626c575976568ba4a85d34297a750d8ab3d2e57f6d8b988` | size and SHA-256 equal the `Checksums-Sha256` entry of the authenticated `Sources` stanza (`sha256sum -c`: OK) |
| polkit Ubuntu `debian` tarball | `https://archive.ubuntu.com/ubuntu/pool/main/p/policykit-1/policykit-1_127-2ubuntu1.1.debian.tar.xz` | 2026-10-10T23:08:48Z | 31,456 | `2f8f11ca818b9726dd8ed9f8979e0a0211edb7b9ee1949b6fb5df697333da73d` | size and SHA-256 equal the `Checksums-Sha256` entry of the authenticated `Sources` stanza (`sha256sum -c`: OK) |
| polkit `.dsc` | `https://archive.ubuntu.com/ubuntu/pool/main/p/policykit-1/policykit-1_127-2ubuntu1.1.dsc` | 2026-10-10T23:08:49Z | 3,201 | `838df29d92dd84c99173e5610cadcec33c66965760bdc8023573045c488c00f6` | size and SHA-256 equal the `Checksums-Sha256` entry of the authenticated `Sources` stanza (`sha256sum -c`: OK) |

**What the chain proves.** A key whose fingerprint Peter pinned, obtained inside a
container whose listing contains that fingerprint, signed the three release files;
the signed files list the hash of each `Sources.xz`; the unmodified `Sources.xz`
files list the size and SHA-256 of each source file; and each downloaded file has
exactly that size and hash. Hence the six files are the Ubuntu archive's files for
the two exact package versions. **What it does not prove:** that the container
itself is genuine beyond the pinned fingerprint (the trust anchor is Peter's
decision, not an independent proof); that the upstream project is free of defects;
that any installed binary equals this source; or who uploaded the package. The
uploader PGP signatures on the `.dsc` files (systemd: key
`50C4A0DDCF31E452CEB19B516569D855A744BE93`) are **not required** by the R1
assignment, were not checked in R1 and no uploader key was fetched: a disclosed
non-dependency, not a substitute stop.

### 2.2 Upstream cross-check (explains the Ubuntu source; never replaces it)

| Object | Full URL requested | Retrieved (UTC, completion) | Bytes | SHA-256 | Verification / note |
|---|---|---|---:|---|---|
| systemd upstream tag `v259.5` archive | `https://github.com/systemd/systemd/archive/refs/tags/v259.5.tar.gz` (redirected to `https://codeload.github.com/systemd/systemd/tar.gz/refs/tags/v259.5`) | 2026-10-10T23:09:37Z | 17,336,729 | `80ed55a8a69c4bd1fb12a36659303372b37baf9ee224ef4f032db4b748be0f76` | byte-identical to the systemd `orig` tarball; `git archive` header comment = commit `b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a` |
| polkit upstream tag `127` archive | `https://github.com/polkit-org/polkit/archive/refs/tags/127.tar.gz` (redirected to `https://codeload.github.com/polkit-org/polkit/tar.gz/refs/tags/127`) | 2026-10-10T23:09:37Z | 472,872 | `9b7bc16f086479dcc626c575976568ba4a85d34297a750d8ab3d2e57f6d8b988` | byte-identical to the polkit `orig` tarball; header comment = commit `9e4894c969eecf26a3ba762f4f7a268aa0fb3e51` |
| systemd ref advertisement | `https://github.com/systemd/systemd.git/info/refs?service=git-upload-pack` | 2026-10-10T23:09:43Z | 7,842,454 | `fb16e4cb3a277ebf204a97e65af0c2f671ebb03b77663ae74140c22abd431ec1` | `refs/tags/v259.5` = tag object `4f8299955d8edfa6dab6879cbd7f199274b121fc`; `refs/tags/v259.5^{}` = commit `b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a` (advertisement is dynamic; its hash identifies this retrieval only) |
| polkit ref advertisement | `https://github.com/polkit-org/polkit.git/info/refs?service=git-upload-pack` | 2026-10-10T23:09:43Z | 22,323 | `cdb677658afabf3f47b9156bdee74a8a071878dda07229fe209d301028a6e7dc` | `refs/tags/127` = commit `9e4894c969eecf26a3ba762f4f7a268aa0fb3e51` (lightweight tag; dynamic) |

systemd tag `v259.5`: tag object `4f8299955d8edfa6dab6879cbd7f199274b121fc` → commit
`b3d8fc43e9cb531d958c17ef2cd93b374bc14e8a`. polkit tag `127` (lightweight): commit
`9e4894c969eecf26a3ba762f4f7a268aa0fb3e51`. Both Ubuntu `orig` tarballs are
byte-identical to the upstream tag archives, so upstream and Ubuntu `orig` text are
the same bytes; Ubuntu differences are only the patch series (§2.7).

### 2.3 Other Ubuntu source packages

All from `https://archive.ubuntu.com/ubuntu/pool/main/`, each verified against the
authenticated `Sources` stanza of §2.1 (`sha256sum -c`). The installed versions of
dpkg and git are not recorded in any required reading; these are the archive's
current releases, not host bindings. The `glibc_2.43.orig.tar.xz.asc` file was not
fetched or used.

| Object | Full URL requested | Retrieved (UTC, completion) | Bytes | SHA-256 | Verification / note |
|---|---|---|---:|---|---|
| glibc `2.43-2ubuntu2.4` `orig` | `https://archive.ubuntu.com/ubuntu/pool/main/g/glibc/glibc_2.43.orig.tar.xz` | 2026-10-10T23:09:26Z | 20,297,012 | `d9c86c6b5dbddb43a3e08270c5844fc5177d19442cf5b8df4be7c07cd5fa3831` | size and SHA-256 equal the entry of the authenticated `Sources` stanza of the named pocket (`sha256sum -c`: OK) (`resolute-security`; identical stanza in `resolute-updates`) |
| glibc `debian` tarball | `https://archive.ubuntu.com/ubuntu/pool/main/g/glibc/glibc_2.43-2ubuntu2.4.debian.tar.xz` | 2026-10-10T23:09:26Z | 530,764 | `28103a7cf808c29901c6053d89a4e8299880abfbb850c0d97a09c8df8533e306` | size and SHA-256 equal the entry of the authenticated `Sources` stanza of the named pocket (`sha256sum -c`: OK) |
| glibc `.dsc` | `https://archive.ubuntu.com/ubuntu/pool/main/g/glibc/glibc_2.43-2ubuntu2.4.dsc` | 2026-10-10T23:09:27Z | 9,078 | `da10d551ca51076bf7bf663de38369d04e267386b8211c283c2814e68e482ed3` | size and SHA-256 equal the entry of the authenticated `Sources` stanza of the named pocket (`sha256sum -c`: OK) |
| dpkg `1.23.7ubuntu1` source (native format) | `https://archive.ubuntu.com/ubuntu/pool/main/d/dpkg/dpkg_1.23.7ubuntu1.tar.xz` | 2026-10-10T23:09:27Z | 5,773,036 | `fa67fcf0f5de3d31f32ff28f9480dbe59cc2a6fe6313d695c5081e44c44b5c4a` | size and SHA-256 equal the entry of the authenticated `Sources` stanza of `resolute` (`sha256sum -c`: OK) |
| dpkg `.dsc` | `https://archive.ubuntu.com/ubuntu/pool/main/d/dpkg/dpkg_1.23.7ubuntu1.dsc` | 2026-10-10T23:09:27Z | 3,482 | `fef83ee2495cf1021b253590db06086fcf60db6df7d72ba6f80b8a3bd1766da9` | size and SHA-256 equal the entry of the authenticated `Sources` stanza of `resolute` (`sha256sum -c`: OK) |
| git `1:2.53.0-1ubuntu1` `orig` | `https://archive.ubuntu.com/ubuntu/pool/main/g/git/git_2.53.0.orig.tar.xz` | 2026-10-10T23:09:27Z | 7,993,096 | `5818bd7d80b061bbbdfec8a433d609dc8818a05991f731ffc4a561e2ca18c653` | size and SHA-256 equal the entry of the authenticated `Sources` stanza of `resolute` (`sha256sum -c`: OK) |
| git `debian` tarball | `https://archive.ubuntu.com/ubuntu/pool/main/g/git/git_2.53.0-1ubuntu1.debian.tar.xz` | 2026-10-10T23:09:28Z | 835,760 | `de1843ed2a314adce0111d5d7053270932c709e8a3e98752f07ec38f359ba3a3` | size and SHA-256 equal the entry of the authenticated `Sources` stanza of `resolute` (`sha256sum -c`: OK) |
| git `.dsc` | `https://archive.ubuntu.com/ubuntu/pool/main/g/git/git_2.53.0-1ubuntu1.dsc` | 2026-10-10T23:09:28Z | 2,656 | `5725094be101993b4c03ebb8a77c0808870d639b2a7039f20063af27d7a8ebf4` | size and SHA-256 equal the entry of the authenticated `Sources` stanza of `resolute` (`sha256sum -c`: OK) |
| Linux man-pages `6.17-1` `orig` | `https://archive.ubuntu.com/ubuntu/pool/main/m/manpages/manpages_6.17.orig.tar.xz` | 2026-10-10T23:09:29Z | 1,915,956 | `78a60c882cbdb843fbf84915754277e4e7fda987f2078e851e32480be7ec5461` | size and SHA-256 equal the entry of the authenticated `Sources` stanza of `resolute` (`sha256sum -c`: OK) |
| man-pages `debian` tarball | `https://archive.ubuntu.com/ubuntu/pool/main/m/manpages/manpages_6.17-1.debian.tar.xz` | 2026-10-10T23:10:58Z | 56,704 | `6d27527cca64c6e03429ed1beb364ddbbd3ad9a9b62c649679c59d54342b363d` | size and SHA-256 equal the entry of the authenticated `Sources` stanza of `resolute` (`sha256sum -c`: OK) |
| man-pages `.dsc` | `https://archive.ubuntu.com/ubuntu/pool/main/m/manpages/manpages_6.17-1.dsc` | 2026-10-10T23:09:29Z | 2,252 | `50e897ba2bb661cbc289857d56349ce35d11ee53f34131865815f537ee43ec0f` | size and SHA-256 equal the entry of the authenticated `Sources` stanza of `resolute` (`sha256sum -c`: OK) |

### 2.4 Linux kernel sources

**R2 re-retrieval (finding `WP3-SC-R1-RE1`).** Every row of the tables below was
retrieved by the R2 remediation (work ID `C-P5.0-R5-RP11-H1-OH-S3-RT3-WP3-SC1-R2-20261011-25`)
on 2026-10-11 between 11:27:48Z and 11:27:51Z into **one fresh mode-`0700` directory**
created with `mktemp -d /tmp/p5r2.XXXXXX` (this execution: `/tmp/p5r2.wgEhC5`). `HOME`,
`TMPDIR` and the XDG variables were set into that directory; `curl -q --proto '=https'
--proto-redir '=https' --tlsv1.2 -fsSL` fetched each of the sixteen objects once from the
official kernel.org stable-tree cgit service; times are the system clock in UTC at
completion of each transfer. In every row the full requested URL equals the effective URL
(no redirect occurred), and the query parameter equals the row label (`h=v7.0` for a `v7.0`
row, `h=v7.0.14` for a `v7.0.14` row). The R1 rows, in which the six `v7.0` file rows and
the `v7.0` tag-page and commit-page rows reused the `v7.0.14` URL, timestamp, size and
SHA-256, are **replaced**; the `v7.0.14` rows are refreshed from this execution as the other
side of the comparison, and no two rows share a retrieval.

Upstream files from the stable tree at tags `v7.0.14` (tag object
`b38d6c0b6e7f406a7feb7d46f184ec3edaac8c3b`, commit `458c6079fc1d41d564c37679c8ace02cd83ee817`,
tag date 2026-06-27 11:07:46 +0100, tagged by Greg Kroah-Hartman) and `v7.0` (tag object
`3131ff5a117498bb4b9db3a238bb311cbf8383ce`, commit `028ef9c96e96197026887c0f092424679298aae8`,
tag date 2026-04-12 13:48:06 -0700, tagged by Linus Torvalds). These identities are those
printed by the two tag pages and two commit pages of the second table, each retrieved with its
own `h=` value. Each of the six files is **byte-identical** in the two tags: `cmp` of the two
retrieved copies succeeded for all six pairs (table below). Equality is claimed only because all
six comparisons succeeded; it is not inferred from equal sizes, and no other ref was substituted.

| Object | Full URL requested (= effective URL) | Retrieved (UTC, completion) | Bytes | SHA-256 | Verification / note |
|---|---|---|---:|---|---|
| `kernel/sys.c` at `v7.0.14` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/kernel/sys.c?h=v7.0.14` | 2026-10-11T11:27:50Z | 74,515 | `418d0bd8929cb41497a73a23e6700412224b062ec6904145c0628d5225abcd5e` | cited line numbers refer to this file |
| `include/uapi/linux/utsname.h` at `v7.0.14` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/include/uapi/linux/utsname.h?h=v7.0.14` | 2026-10-11T11:27:50Z | 684 | `e6a7aeffebf22a2d74b5e671ab5ff8bb99b0655cefb544bfca0acc22aa396c2a` | cited line numbers refer to this file |
| `kernel/utsname_sysctl.c` at `v7.0.14` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/kernel/utsname_sysctl.c?h=v7.0.14` | 2026-10-11T11:27:50Z | 3,526 | `0670f6501ebd63123e7d76d92f64ab9f450e828412bc431f5c4d63673a7fdc01` | cited line numbers refer to this file |
| `fs/proc/array.c` at `v7.0.14` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/fs/proc/array.c?h=v7.0.14` | 2026-10-11T11:27:50Z | 23,003 | `b33ac7b8c8aa20c85d61c2eb77eec60716bbba7075870a9c358cb533c89ba85a` | cited line numbers refer to this file |
| `fs/stat.c` at `v7.0.14` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/fs/stat.c?h=v7.0.14` | 2026-10-11T11:27:50Z | 27,228 | `47d331643ef846d014684819266beb580fd6da3e9430b0cdedebed53e99d9078` | cited line numbers refer to this file |
| `fs/xattr.c` at `v7.0.14` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/fs/xattr.c?h=v7.0.14` | 2026-10-11T11:27:51Z | 41,353 | `2f3737b36b44f4773c872d89bbb03cfc47906beebc2b0ab21635e6b65fe71228` | cited line numbers refer to this file |
| `kernel/sys.c` at `v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/kernel/sys.c?h=v7.0` | 2026-10-11T11:27:48Z | 74,515 | `418d0bd8929cb41497a73a23e6700412224b062ec6904145c0628d5225abcd5e` | compared with the `v7.0.14` file of this table: `cmp` IDENTICAL |
| `include/uapi/linux/utsname.h` at `v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/include/uapi/linux/utsname.h?h=v7.0` | 2026-10-11T11:27:48Z | 684 | `e6a7aeffebf22a2d74b5e671ab5ff8bb99b0655cefb544bfca0acc22aa396c2a` | compared with the `v7.0.14` file of this table: `cmp` IDENTICAL |
| `kernel/utsname_sysctl.c` at `v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/kernel/utsname_sysctl.c?h=v7.0` | 2026-10-11T11:27:49Z | 3,526 | `0670f6501ebd63123e7d76d92f64ab9f450e828412bc431f5c4d63673a7fdc01` | compared with the `v7.0.14` file of this table: `cmp` IDENTICAL |
| `fs/proc/array.c` at `v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/fs/proc/array.c?h=v7.0` | 2026-10-11T11:27:49Z | 23,003 | `b33ac7b8c8aa20c85d61c2eb77eec60716bbba7075870a9c358cb533c89ba85a` | compared with the `v7.0.14` file of this table: `cmp` IDENTICAL |
| `fs/stat.c` at `v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/fs/stat.c?h=v7.0` | 2026-10-11T11:27:49Z | 27,228 | `47d331643ef846d014684819266beb580fd6da3e9430b0cdedebed53e99d9078` | compared with the `v7.0.14` file of this table: `cmp` IDENTICAL |
| `fs/xattr.c` at `v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/fs/xattr.c?h=v7.0` | 2026-10-11T11:27:49Z | 41,353 | `2f3737b36b44f4773c872d89bbb03cfc47906beebc2b0ab21635e6b65fe71228` | compared with the `v7.0.14` file of this table: `cmp` IDENTICAL |

**Byte-for-byte comparison of the six pairs** (`cmp -s` on the two retrieved copies in the fresh directory):

| File | `v7.0` bytes | `v7.0.14` bytes | `v7.0` SHA-256 = `v7.0.14` SHA-256 | `cmp` result |
|---|---:|---:|---|---|
| `kernel/sys.c` | 74,515 | 74,515 | yes | IDENTICAL |
| `include/uapi/linux/utsname.h` | 684 | 684 | yes | IDENTICAL |
| `kernel/utsname_sysctl.c` | 3,526 | 3,526 | yes | IDENTICAL |
| `fs/proc/array.c` | 23,003 | 23,003 | yes | IDENTICAL |
| `fs/stat.c` | 27,228 | 27,228 | yes | IDENTICAL |
| `fs/xattr.c` | 41,353 | 41,353 | yes | IDENTICAL |

Result: **all six pairs byte-identical**. (For information: the six SHA-256 values equal those that the R1
record gave for its `v7.0.14` rows; R1's `v7.0` rows were not independent retrievals and supported nothing.)

Tag and commit identities (HTML pages of the kernel.org cgit instance; each page ends with a
`generated by cgit … at <time>` line, so the hashes identify this retrieval only and differ from R1's):

| Object | Full URL requested (= effective URL) | Retrieved (UTC, completion) | Bytes | SHA-256 | Verification / note |
|---|---|---|---:|---|---|
| tag page `v7.0.14` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/tag/?h=v7.0.14` | 2026-10-11T11:27:51Z | 10,443 | `a6c6997a08392c66234e2edc12c0a78f15e9fbe79191e647bfb694475effadce` | tag name `v7.0.14` (`b38d6c0b6e7f406a7feb7d46f184ec3edaac8c3b`); tagged object commit `458c6079fc…` (abbreviated by the page; full identifier from the commit page) |
| commit page `v7.0.14` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/commit/?h=v7.0.14` | 2026-10-11T11:27:51Z | 14,039 | `8b0f599f3a89b48d5e4085c37a091b620185737816b8454db4e2ac81b1a6a04b` | commit `458c6079fc1d41d564c37679c8ace02cd83ee817`, tree `8436e2406cd520564dfafab6112b18ca59a6f331`, parent `39a2b95e008665c14f84e50ed411d898df7cd11b` |
| tag page `v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/tag/?h=v7.0` | 2026-10-11T11:27:49Z | 10,075 | `5aab24ec4c02e12d873ef2f17dd96c83a684931e35fe35421a1a9684f04b732c` | tag name `v7.0` (`3131ff5a117498bb4b9db3a238bb311cbf8383ce`); tagged object commit `028ef9c96e…` (abbreviated by the page; full identifier from the commit page) |
| commit page `v7.0` | `https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/commit/?h=v7.0` | 2026-10-11T11:27:50Z | 13,118 | `b2f408fa1bc03f2af723950dec3ce7796d4a67691553cafd65061860d4906e40` | commit `028ef9c96e96197026887c0f092424679298aae8`, tree `6e2e13adb3ebf0a7a19583d58009f8372b592387`, parent `10d97b74e2eef787d823f9bc05cb044b47d25c41` |

The Ubuntu delta for the host kernel `7.0.0-31-generic` (R2 §1.1 A-3). It is the
diff of Ubuntu's `linux-7.0.0` tree against the `linux-7.0.0.orig` tarball, unpacked
with `gzip -dc` (10,621,358 bytes of text). Among the files cited in this record it
touches only `kernel/sys.c` (hunk old-side lines 1308-1313) and `fs/proc/array.c`
(old-side 482-487 and 657-662); it does not touch `include/uapi/linux/utsname.h`,
`kernel/utsname_sysctl.c`, `fs/stat.c` or `fs/xattr.c`.

| Object | Full URL requested | Retrieved (UTC, completion) | Bytes | SHA-256 | Verification / note |
|---|---|---|---:|---|---|
| Ubuntu kernel delta `linux_7.0.0-31.31.diff.gz` | `https://launchpad.net/ubuntu/+archive/primary/+sourcefiles/linux/7.0.0-31.31/linux_7.0.0-31.31.diff.gz` (redirected to `https://launchpadlibrarian.net/871769417/linux_7.0.0-31.31.diff.gz`) | 2026-10-10T23:09:19Z | 2,399,688 | `7d1ee5c5a554dc037f9d1ce643b644edff63c01718a4fa1d5c735e064b33cd6a` | NOT chain-authenticated (the current archive indexes list `linux` `7.0.0-38.38`/`7.0.0-14.14` only; `archive.ubuntu.com` pool returned 404); SHA-256 and size equal R2 Appendix D |

**Authentication gap (R1 disclosure).** The kernel source package `linux`
`7.0.0-31.31` is no longer listed in the current signed `Sources` indexes (they list
`7.0.0-38.38` in `resolute-updates`/`resolute-security` and `7.0.0-14.14` in
`resolute`), and `https://archive.ubuntu.com/ubuntu/pool/main/l/linux/linux_7.0.0-31.31.diff.gz` returned HTTP 404. The diff was therefore retrieved from Launchpad and its identity rests on its
**equality with R2 Appendix D** (an accepted repository record), not on the signed
archive chain. Only A-12.3 and A-15.2 use it, as statements about Ubuntu's delta;
both are labelled accordingly in Appendix F and carry no other evidence. No nearby
kernel version was substituted.

### 2.5 D-Bus specification and the project manuals

| Object | Full URL requested | Retrieved (UTC, completion) | Bytes | SHA-256 | Verification / note |
|---|---|---|---:|---|---|
| D-Bus Specification 0.43 (HTML) | `https://dbus.freedesktop.org/doc/dbus-specification.html` | 2026-10-10T23:09:52Z | 339,535 | `623a8a947f820a521d12b5706ef603f5bf443cf312695bb756c4e4efd258e75a` | `Last-Modified: Thu, 27 Feb 2025 17:37:12 GMT`, `ETag "52e4f-62f2323e624a5"`, `Content-Length: 339535` (response headers, 2026-10-10 23:09:51Z); hash equals the original record's |

HTML is cited by section heading plus a content anchor (Appendix E.2); the page
carries no stable line numbers. The systemd D-Bus API manual
(`man/org.freedesktop.systemd1.xml`) and the polkit interface description
(`data/org.freedesktop.PolicyKit1.Authority.xml`) are inside the `orig` tarballs of
§2.1 and are cited by line range in the same way as source files.

### 2.6 Launchpad package pages (metadata only)

| Object | Full URL requested | Retrieved (UTC, completion) | Bytes | SHA-256 | Verification / note |
|---|---|---|---:|---|---|
| Launchpad page, systemd `259.5-0ubuntu3.4` | `https://launchpad.net/ubuntu/+source/systemd/259.5-0ubuntu3.4` | 2026-10-10T23:10:01Z | 42,240 | `19dc693de2cc67fca19d2d72ba188b3831522fe7907fd39161bef0c1882ea901` | metadata only (uploaded by Nick Rosbrook on 2026-07-28, Resolute, published `updates`); dynamic page: hash differs from the original record's (`dcbca5399fd4197a0e5c149903b887289895dd5f60a8fc55059485259fdf6c62`), identifies this retrieval only |
| Launchpad page, polkit `127-2ubuntu1.1` | `https://launchpad.net/ubuntu/+source/policykit-1/127-2ubuntu1.1` | 2026-10-10T23:10:03Z | 24,441 | `83e3eacc72ee3a86c7d4541f6f2e23a7ccae3f7fa2b984217e4d12141fe27418` | metadata only (uploaded by Marc Deslauriers on 2026-09-11, Resolute, published `updates`); dynamic page (the original record's hash was `651e4bd8d4137ac6757fafe8d4aee7262e3df48dc7fe602ffd70b23fed5a65fc`) |

### 2.7 Distro patches accounted for

`debian/patches/series` of each package was applied in full with `patch -p1` to a
copy of the `orig` tree: **systemd 40 of 40, polkit 2 of 2, glibc 103 of 103,
man-pages 13 of 13; no failure.** The cited line numbers of `SD` and `PK` are those of
the patched tree (§1 table). The table lists every patch that touches a file cited in
Appendix E (line-range citations only; named-section citations are in Appendix E.2).

| Source | Cited files | Patches that touch a cited file (series order : patch name : cited file) |
|---|---:|---|
| systemd `259.5-0ubuntu3.4` (40 patches, all applied) | 43 | 04: `lp2077538/login-Add-XDG_SESSION_EXTRA_DEVICE_ACCESS-variable-for-ad.patch` : `src/core/manager.c`; 20: `lp2150773-core-Open-netfilter-socket-only-when-needed.patch` : `src/core/unit.c`; 33: `GHSA-3jgj-3phh-hx5j/core-limit-the-number-of-units-that-can-be-requested-over.patch` : `src/core/dbus-manager.c`; 37: `GHSA-3jgj-3phh-hx5j/dbus-manager-limit-the-number-of-states-patterns-per-quer.patch` : `src/core/dbus-manager.c`; 38: `GHSA-3jgj-3phh-hx5j/dbus-limit-the-number-of-env-variables-to-something-reaso.patch` : `src/core/dbus-manager.c` |
| polkit `127-2ubuntu1.1` (2 patches, all applied) | 13 | none |
| glibc `2.43-2ubuntu2.4` (103 patches, all applied) | 5 | 01: `git-updates.diff` : `nss/nss_database.c` |
| man-pages `6.17-1` (13 patches, all applied) | 0 | none |
| git `1:2.53.0-1ubuntu1` | — | Ubuntu `debian.tar.xz` contains no `debian/patches` directory: the `orig` tree is used unpatched |
| dpkg `1.23.7ubuntu1` | — | native-format source (single tarball): no separate upstream tarball and no patch series; the Ubuntu tree itself is cited |

* **polkit** — both patches (`CVE-2026-4897.patch`, `CVE-2026-85498.patch`) change
  only `src/polkitagent/polkitagenthelperprivate.c`. No file cited in this record is
  modified.
* **systemd** — the full list of patches with the files each touches was produced
  by the apply run and is summarised by the table; the patches touching a cited file
  add `LimitsExceeded` guards to unrelated methods of `dbus-manager.c`
  (`ListUnitsByNames`, `list_units_filtered`, `dump_impl`, `list_unit_files_by_patterns`,
  `SetEnvironment`, `UnsetEnvironment`, `UnsetAndSetEnvironment`), defer the netfilter
  socket in `unit.c` and `cgroup.c`, and add a user-manager-only option to `manager.c`.
  Every `dbus-manager.c` citation of this record is checked against the post-patch
  numbering and lies outside the patched hunks (Appendix E.1). No patch touches
  `dbus-unit.c`, `dbus-job.c`, `job.c`, `transaction.c`, `bus-polkit.c`,
  `dbus-util.c`, `bus-print-properties.c`, `systemctl-show.c`, `run.c`,
  `bus-unit-util.c`, `dbus-execute.c`, `dbus-service.c`, `dbus-timer.c`, `sd-bus.c`,
  `bus-objects.c`, `bus-convenience.c` or the vtable files.
* **glibc** (R1 addition — the original record did not apply this series) — the only
  patch touching a cited file is `git-updates.diff`, which patches
  `nss/nss_database.c` at old-side lines 59, 245, 247, 442-443, 468, 494, 506-507, 512
  and 519; the cited lines 297-402 contain none of them but are numbered **in the
  unpatched file** (the series shifts them by +2: `nss_database_reload` starts at 294
  unpatched and 296 patched).
* **man-pages** — `0008-nsswitch.conf.5.patch` adds five lines to
  `man/man5/nsswitch.conf.5` at line 274; the cited sentence ("the sources from which
  to obtain name-service information") is at line 13, untouched. No other cited page is
  patched.
* **git** and **dpkg** — see the table.

### 2.8 Method limits

This is static reading of exact sources. No pinned binary was run or inspected; no
D-Bus message was exchanged; no host or retained evidence was read. A statement of the
form "the server does X" means "the cited source code does X in this version", not
"the installed daemon was observed to do X". A reference-client statement (tier `R`)
describes a client, never a contract. Statements resting on an absence in the cited
function bodies (A-05.6, A-05.12, A-10.8) are labelled as absence findings.

## 3. Evidence matrix `UF-01` … `UF-14`

Each block states, in the order of the prompt: the accepted missing-fact
statement **quoted verbatim** from contract §6; the sources examined; the
supported facts; the manager/server-versus-client split (tier); version and
distro-patch effects; the DI/Q3 mapping; the status; and every residual gap.
Fact identifiers are `A-<uf>.<n>` (`ASF`/`MD`), `P-<uf>.<n>` (`PSC`) and `R-<uf>.<n>`
(residual gap).

### UF-01 — client transport, authentication and message framing

> Accepted statement (contract §6): "Client transport, authentication and message framing used to reach the manager and the authority (only the system-bus socket locus, D line 940, is stated)"

* **Sources examined.** DB §System message bus, §Authentication Protocol,
  §Message Format, §Marshaling, §Header Fields, §Hello, §Message Bus Names,
  §AddMatch; `SD` `src/libsystemd/sd-bus/{bus-internal.h,sd-bus.c}`,
  `src/shared/bus-util.c`, `src/core/{dbus.c,org.freedesktop.systemd1.conf}`;
  `PK` `data/org.freedesktop.PolicyKit1.conf.in`.
* **Affects.** DI-1 … DI-5, DI-S (every interface that reaches the manager or
  the authority); Q3-1 … Q3-5, Q3-7.
* **Version/distro.** The wire facts are bound to D-Bus Specification 0.43; the
  server-side facts to the pinned `SD`/`PK` trees (no patch touches a cited file).

| Id | Class/tier | Fact | Source |
|---|---|---|---|
| A-01.1 | ASF/W | The system bus address is the value of `DBUS_SYSTEM_BUS_ADDRESS` if set, else the well-known `unix:path=/var/run/dbus/system_bus_socket`; where `/var/run` is synonymous with `/run`, implementations "might prefer" `unix:path=/run/dbus/system_bus_socket`. | DB §System message bus |
| A-01.2 | ASF/R | systemd's own client uses `secure_getenv("DBUS_SYSTEM_BUS_ADDRESS")` and otherwise `DEFAULT_SYSTEM_BUS_ADDRESS` = `"unix:path=/run/dbus/system_bus_socket"`. | `SD` `src/libsystemd/sd-bus/bus-internal.h:16`; `src/libsystemd/sd-bus/sd-bus.c:1311-1325`; `src/shared/bus-util.c:758-760` |
| A-01.3 | ASF/W | Authentication is a line protocol (each line ends `\r\n`, command names `[A-Z_]`). The client's first transmitted byte is a single NUL (it may carry socket credentials usable with SASL `EXTERNAL`). Client commands: `AUTH [mechanism] [initial-response]`, `CANCEL`, `BEGIN`, `DATA <hex>`, `ERROR`, `NEGOTIATE_UNIX_FD`; server replies: `REJECTED <mechanisms>`, `OK <server GUID in hex>`, `DATA`, `ERROR`, `AGREE_UNIX_FD`. On Unix a non-empty SASL authorization identity is a numeric user ID written in ASCII decimal digits; `AUTH EXTERNAL` carries that string hex-encoded (example: `AUTH EXTERNAL 31303030` = uid 1000, answered `OK 1234deadbeef`). `BEGIN` is not answered; the byte after its `\r\n` is the first byte of the message stream. | DB §Authentication Protocol (Protocol Overview, nul byte, AUTH, OK, BEGIN, NEGOTIATE_UNIX_FD, examples) |
| A-01.4 | ASF/W | Message framing: header signature `yyyyuua(yv)` (endianness byte `l`/`B`, message type, flags, major protocol version `1`, body length `u32`, serial `u32` non-zero, array of header fields), padded to an 8-byte boundary; types METHOD_CALL=1, METHOD_RETURN=2, ERROR=3, SIGNAL=4; flags NO_REPLY_EXPECTED=0x1, NO_AUTO_START=0x2, ALLOW_INTERACTIVE_AUTHORIZATION=0x4; header field codes PATH=1, INTERFACE=2, MEMBER=3, ERROR_NAME=4, REPLY_SERIAL=5, DESTINATION=6, SENDER=7, SIGNATURE=8, UNIX_FDS=9; natural alignment, STRUCT/DICT_ENTRY 8-aligned, strings `u32` length + UTF-8 + NUL, signatures 1-byte length, arrays `u32` byte length (max 64 MiB), variants signature + value, depth ≤ 64, message ≤ 128 MiB. | DB §Message Format, §Marshaling (Wire Format), §Header Fields, §Valid Signatures |
| A-01.5 | ASF/W | On a message bus the first message must be `org.freedesktop.DBus.Hello` (reply: the connection's unique name, which begins with `:`); any other message first leads to disconnection; "There is no corresponding \"disconnect\" request; if a client wishes to disconnect from the bus, it simply closes the socket (or other communication channel)"; signals reach a client only through match rules added with `org.freedesktop.DBus.AddMatch(s)`. | DB §Hello, §Message Bus Names, §AddMatch |
| A-01.6 | ASF/S | Bus policy shipped by the pinned packages: systemd `org.freedesktop.systemd1.conf` lets user `root` own the name and send to / receive from `org.freedesktop.systemd1` without restriction (lines 18-28) and denies the default context except an enumerated allow-list that includes `Get`/`GetAll`, `GetUnit`, `LoadUnit`, `GetJob`, `Subscribe` and, under "Managed via polkit", `StartUnit` (207), `StopUnit` (215), `StartTransientUnit` (275), `CancelJob` (287); polkit `org.freedesktop.PolicyKit1.conf.in` lets only the polkitd user own `org.freedesktop.PolicyKit1` and lets the default context send to it (lines 7-13). | `SD` `src/core/org.freedesktop.systemd1.conf:16-31,49,113,203-287`; `PK` `data/org.freedesktop.PolicyKit1.conf.in:7-13` |
| A-01.7 | ASF/S | The manager additionally listens, as PID 1, on a private socket `/run/systemd/private` bound under `umask 0077`; an accepted connection is refused unless the peer uid is `0` or the manager's own euid (`bus_check_peercred`: `ucred.uid != 0 && ucred.uid != geteuid()` ⇒ `-EPERM`); it is a direct (peer-to-peer) D-Bus connection with sender name `org.freedesktop.systemd1`, negotiated credentials and `CONNECTIONS_MAX` bound. | `SD` `src/core/dbus.c:895-957` (`bus_init_private`), `619-692` (`bus_on_connection`), `src/shared/bus-util.c:225-240` |
| A-01.8 | ASF/R | systemd's root-run tools connect to that private socket instead of the system bus when `geteuid() == 0` and the transport is local; the private-socket client does not call `sd_bus_set_bus_client`, the system-bus client does (`src/shared/bus-util.c:766`), so only the latter performs `Hello`. | `SD` `src/shared/bus-util.c:242-266,510-552,758-775` |
| A-01.9 | MD | Direct delivery of `JobNew`/`JobRemoved`-class signals: connections on the private socket receive manager signals unconditionally, API-bus clients only when subscribed or tracked (A-05.4). The private socket does **not** reach `org.freedesktop.PolicyKit1`, which is a name on the system bus (A-10.1); DI-5 therefore needs the system bus even if DI-1 … DI-4 and DI-S were to use the private socket. | derived from A-01.7, `SD` `src/core/dbus.c:1092-1121`, `src/shared/bus-polkit.c:82-88` |

* **`PSC` (tier M, not a selection).** P-01.1 candidate transports: (T-A) the
  system bus socket for all seven interfaces; (T-B) the system bus for DI-5 and
  the private socket for the manager interfaces when the caller is root. Both are
  stream sockets to a local path and are compatible in principle with the
  loader-free/no-distribution-child boundary; neither requires a child process.
  *The decision (which, and whether the accepted TR-4 "system-bus socket" locus
  is to be extended to the private socket) is Peter's, informed by WP-4; this
  record does not make it.* Left undesigned: connection lifetime and reuse,
  buffer sizes, read/write loop, timeout enforcement (Q4-7), file-descriptor
  passing.
* **Status: supported** for transport, authentication and framing (wire facts
  A-01.1 … A-01.5; pinned-server facts A-01.6 … A-01.9).
* **Residuals.** R-01.1: the installed message-bus implementation (HF-07 lists the
  `dbus` package; its version, whether it is `dbus-daemon` or `dbus-broker`, and
  its active policy files were not in any source examined) is not bound; the
  specification constrains its protocol behavior but not its version-specific
  limits. R-01.2: credential passing on the Unix socket (what the kernel
  delivers with the NUL byte and how a server checks it) was not researched.

### UF-02 — unit name to object

> Accepted statement: "How a unit name resolves to the object that holds its properties, including a unit that is not loaded"

* **Sources.** `SD` `src/basic/{unit-def.c,bus-label.c,hexdecoct.c}`,
  `src/core/{dbus-manager.c,dbus.c,manager.c,unit.c}`, `src/systemctl/systemctl-show.c`.
* **Affects.** DI-1 (23 call sites); Q3-1. **Version/distro.** `SD`; `manager.c`
  and `unit.c` are touched by unrelated patches (§2.7).

| Id | Class/tier | Fact | Source |
|---|---|---|---|
| A-02.1 | ASF/S | The unit object path is `/org/freedesktop/systemd1/unit/` followed by `bus_label_escape(name)`. That escape maps the empty string to `_`; copies every ASCII letter, and every ASCII digit except as the first character; and writes every other byte as `_` plus two **lowercase** hexadecimal digits of the byte value (`"0123456789abcdef"`). | `SD` `src/basic/unit-def.c:11-21`; `src/basic/bus-label.c:10-43`; `src/basic/hexdecoct.c:35-38` |
| A-02.2 | MD | Applying A-02.1: `rp11-capture-pass-a.service` → `/org/freedesktop/systemd1/unit/rp11_2dcapture_2dpass_2da_2eservice`; `rp11-act-20261010T000000Z-0123abcd.service` → `/org/freedesktop/systemd1/unit/rp11_2dact_2d20261010T000000Z_2d0123abcd_2eservice`; the `-backstop.timer` and `-backstop.service` names escape the same way (`…_2dbackstop_2etimer`, `…_2dbackstop_2eservice`). The path is computed by the client; `systemctl show` does exactly this (`unit_dbus_path_from_name`) and issues no `GetUnit`/`LoadUnit` for it. The example identifier matches the accepted `activation_id` grammar of RT1.CQ0.5. | derived from A-02.1; `SD` `src/systemctl/systemctl-show.c:2582-2589` |
| A-02.3 | ASF/S | A property access or `GetAll` on a unit path reaches `bus_unit_find` → `find_unit` → `manager_load_unit_from_dbus_path`. That function unescapes the label; if the result parses as a 128-bit ID it looks the unit up by invocation ID (not found ⇒ `org.freedesktop.systemd1.NoUnitForInvocationID`); otherwise a name that is neither a valid plain/instance unit name nor an ID ⇒ `org.freedesktop.DBus.Error.InvalidArgs` "Unit name %s is neither a valid invocation ID nor unit name."; otherwise **`manager_load_unit` loads the unit**, creating an in-memory unit even when no unit file exists. | `SD` `src/core/dbus.c:225-257,259-268`; `src/core/manager.c:3335-3375` |
| A-02.4 | ASF/S | `find_unit` returns `0` (not found) when `manager_load_unit_from_dbus_path` fails; the caller then continues and the connection finally answers `org.freedesktop.DBus.Error.UnknownObject` "Unknown object '<path>'." — i.e. the specific `InvalidArgs` text of A-02.3 is not what a property client sees for a malformed path. | `SD` `src/core/dbus.c:248-253`; `src/libsystemd/sd-bus/bus-objects.c:593-601`; `src/libsystemd/sd-bus/sd-bus.c:3071-3085` |
| A-02.5 | ASF/S | Method forms: `GetUnit(s name) → o` returns the path only for a **loaded** unit, else `org.freedesktop.systemd1.NoSuchUnit` "Unit %s not loaded."; an empty name means the caller's own unit (`"Client not member of any unit."` if none). `LoadUnit(s name) → o` is "similar … but will load the unit from disk if possible". Both are flagged `SD_BUS_VTABLE_UNPRIVILEGED` and are in the default bus-policy allow-list. | `SD` `src/core/dbus-manager.c:487-529,549-568,726-745,3018-3047`; `man/org.freedesktop.systemd1.xml:1275-1276`; A-01.6 |
| A-02.6 | ASF/S | A unit that is loaded but has no unit file reports `LoadState` `not-found` (the load-state strings are `stub`, `loaded`, `not-found`, `bad-setting`, `error`, `merged`, `masked`). A unit in `NOT_FOUND` or `LOADED` state with no fragment, no source path, no job and not merged is "pristine" and does not prevent `StartTransientUnit` from creating that name. | `SD` `src/basic/unit-def.c:89-97`; `src/core/unit.c:5248-5265`; `src/core/dbus-manager.c:1054-1056` |
| A-02.7 | ASF/S | Reading a property of a not-yet-loaded unit therefore *changes manager state* (a stub is loaded and later garbage-collected) but starts, stops and creates no job; for an inactive unit that is not loaded a later read may find it unloaded again (`LoadState` `not-found`, `InvocationID` possibly empty, `InactiveEnterTimestampMonotonic` possibly `0`). | A-02.3 with accepted R2 §8 (k), (l), (s) (carried) |

* **Status: supported.** Residual R-02.1: the *timing* of garbage collection of a
  loaded stub (when `unit_gc` unloads it) was not analysed; no DI-1 closure
  needs it, because every accepted DI-1 use treats a satisfied read as "never
  evidence of absence" (H-DI1.4).

### UF-03 — wire types and typed-to-text rules

> Accepted statement: "The wire type of each of the eight DI-1 properties (and of Appendix A/B baseline properties) and the rule from typed value to the printed text H-DI1.2 expects; R2 Appendix A/B carry names, interfaces, flags and source lines but no type signatures"

* **Sources.** `SD` vtables in `src/core/{dbus-unit.c,dbus-service.c,dbus-cgroup.c,dbus-execute.c,dbus-kill.c,dbus-timer.c,dbus-manager.c}`,
  `src/shared/{bus-get-properties.c,bus-print-properties.c}`, `src/systemctl/systemctl-show.c`,
  `src/basic/time-util.c`, `src/basic/escape.c`; R2 Appendices A and B for the name lists.
* **Affects.** DI-1; Q3-1, Q3-9 (and Q6-2, which is not decided here).

**The eight DI-1 properties (all visible to `GetAll`, none `HIDDEN`/`EXPLICIT`):**

| Property | Interface | Signature | Encoding/semantics (server) | Printed text by `systemctl show -p` (reference client) |
|---|---|---|---|---|
| `ActiveState` | `org.freedesktop.systemd1.Unit` | `s` | one of `active`, `reloading`, `inactive`, `failed`, `activating`, `deactivating`, `maintenance`, `refreshing` (`src/basic/unit-def.c:102-111`) | the string as is (a string with `\n` prints `[unprintable]`) — `src/shared/bus-print-properties.c:75-92` |
| `InvocationID` | `…Unit` | `ay` | an empty array when the ID is null, else exactly 16 bytes (`src/shared/bus-get-properties.c:64-79`; `src/core/dbus-unit.c:992`) | lowercase hex, two digits per byte, no separator (`src/shared/bus-print-properties.c:292-312`); empty ⇒ `InvocationID=` only when empty values are shown (`-p` shows them) |
| `InactiveEnterTimestampMonotonic` | `…Unit` | `t` | µs on `CLOCK_MONOTONIC`, `0` when never set (R2 §8 (s)) | decimal (`%"PRIu64`): the name neither ends in `Timestamp` nor contains `USec` (`src/shared/bus-print-properties.c:115-125,189`) |
| `Job` | `…Unit` | `(uo)` | `(id, job path)`; `(0, "/")` when there is no job (`src/core/dbus-unit.c:254-277,958`) | the numeric id if > 0, else an empty value (`src/systemctl/systemctl-show.c:1232-1244`) |
| `LoadState` | `…Unit` | `s` | strings of A-02.6 | as is |
| `Result` | `org.freedesktop.systemd1.Service` | `s` | `success`, `resources`, `protocol`, `timeout`, `exit-code`, `signal`, `core-dump`, `watchdog`, `start-limit-hit`, `oom-kill`, `exec-condition` (`src/core/service.c:5875-5887`) | as is |
| `ExecMainStartTimestampMonotonic` | `…Service` | `t` | µs `CLOCK_MONOTONIC`, `0` before the main process is spawned (R2 §8 (v)) | decimal |
| `TimeoutStartUSec` | `…Service` | `t` | µs; `UINT64_MAX` = infinity | `FORMAT_TIMESPAN(u, 0)` — a **human-readable, lossy-looking** text such as `1min 30s`; `infinity` for `UINT64_MAX`; `0` for `0` (`src/shared/bus-print-properties.c:124-125`; `src/basic/time-util.c:520-624`) |

| Id | Class/tier | Fact | Source |
|---|---|---|---|
| A-03.1 | MD | A mechanical extraction of every `SD_BUS_PROPERTY`/`SD_BUS_WRITABLE_PROPERTY` entry (including the `BUS_PROPERTY_DUAL_TIMESTAMP`, `BUS_EXEC_STATUS_VTABLE` and `BUS_EXEC_*COMMAND*_VTABLE` macro expansions) of the nine vtables yields 641 rows. Removing `HIDDEN`/`EXPLICIT` rows leaves **464 visible Unit+Service names and 126 visible Manager names, equal — as sets of names and as interface assignments — to R2 Appendices A and B**. This reproduces R2's accepted lists independently and attaches the missing signatures. | extraction script over `SD` vtables; R2 Appendices A, B |
| A-03.2 | MD | Signature census, visible Unit+Service (464): `t` 120, `s` 92, `b` 67, `as` 59, `i` 23, `u` 18, `ay` 12, `a(ss)` 8, `a(sasbttttuii)` 8, `a(sasasttttuii)` 8, `a(st)` 6, `a(sst)` 5, `(bas)` 5, `(aiai)` 3, `(bs)` 3, `(tus)` 3, `(tt)` 3, `a(sbbsi)` 2, `(ss)` 2, `a(iayu)` 2, `a(iiqq)` 2, `q` 2, `a(say)` 2, `a(ssbt)` 2, and one each of `(uo)`, `a(iiss)`, `a(sb)`, `a(sba(ss))`, `a(ssba(ss))`, `aay`, `a(bs)` (31 signatures). Manager (126): `t` 88, `s` 17, `b` 8, `u` 7, `as` 2, `at` 1, `d` 1, `y` 1, `i` 1. | same |
| A-03.3 | ASF/R | `bus_print_property` prints, by wire type: `s` as is; `b` `yes`/`no`; `x` `%"PRIi64`; `i` `%"PRIi32`; `d` `%g`; `u` as `%04o` when the name contains `UMask` or `Mode`, `[not set]` for invalid `UID`/`GID`, else `%"PRIu32`; `as` as space-joined `shell_maybe_quote` items; `ay` as hex; `au` as `%08x`; **any other type returns "unprintable"** and is skipped (or printed `[unprintable]` when empty values are shown). `t` is name-dependent: names ending `Timestamp` or equal to `NextElapseUSecRealtime`, `LastTriggerUSec`, `TimeUSec`, `RTCTimeUSec` go through `FORMAT_TIMESTAMP`; `ManagedOOMMemoryPressureDurationUSec` = `UINT64_MAX` ⇒ `[not set]`; any other name containing `USec` ⇒ `FORMAT_TIMESPAN(u, 0)`; `CoredumpFilter` hex; `RestrictNamespaces`, `MountFlags`, `CapabilityBoundingSet`/`AmbientCapabilities` symbolic; `CPUWeight`/`StartupCPUWeight` `idle`; sentinel values ⇒ `[not set]`, `infinity` or `[no data]`; else decimal. | `SD` `src/shared/bus-print-properties.c:61-341` |
| A-03.4 | ASF/R | `systemctl show` overrides the generic printer: `t` timestamps use `FORMAT_TIMESTAMP_STYLE(…, arg_timestamp_style)`; `(uo)` `Job` prints the id only; `(so)` `Unit`, `(ss)` `LoadError`, `(bas)`-family lists and the `a(sasbttttuii)`/`a(sasasttttuii)` arrays are printed in special forms. For the `Exec*` arrays each element is one line `{ path=… ; argv[]=… ; ignore_errors=… ; start_time=[…] ; stop_time=[…] ; pid=… ; code=… ; status=… }` (the `…Ex` form replaces `ignore_errors` by `flags=<space-separated flags>`). | `SD` `src/systemctl/systemctl-show.c:1173-1300,1515-1571` |
| A-03.5 | MD | Census by print rule for the 120+88 `t` properties: Unit+Service — 11 `Timestamp` (`ActiveEnterTimestamp`, `ActiveExitTimestamp`, `AssertTimestamp`, `ConditionTimestamp`, `ExecMainExitTimestamp`, `ExecMainHandoffTimestamp`, `ExecMainStartTimestamp`, `InactiveEnterTimestamp`, `InactiveExitTimestamp`, `StateChangeTimestamp`, `WatchdogTimestamp`), 17 `…USec` timespans (`CPUQuotaPerSecUSec`, `CPUQuotaPeriodUSec`, `JobRunningTimeoutUSec`, `JobTimeoutUSec`, `LogRateLimitIntervalUSec`, `MemoryPressureThresholdUSec`, `RestartMaxDelayUSec`, `RestartUSec`, `RestartUSecNext`, `RuntimeMaxUSec`, `RuntimeRandomizedExtraUSec`, `StartLimitIntervalUSec`, `TimeoutAbortUSec`, `TimeoutCleanUSec`, `TimeoutStartUSec`, `TimeoutStopUSec`, `WatchdogUSec`), 1 `ManagedOOMMemoryPressureDurationUSec`, 1 `CoredumpFilter`, 1 `RestrictNamespaces`, 1 `MountFlags`, 2 capability sets, 2 `CPUWeight` and 84 decimal-or-sentinel; Manager — 21 `Timestamp`, 12 `…USec` (`DefaultDeviceTimeoutUSec`, `DefaultMemoryPressureThresholdUSec`, `DefaultRestartUSec`, `DefaultStartLimitIntervalUSec`, `DefaultTimeoutAbortUSec`, `DefaultTimeoutStartUSec`, `DefaultTimeoutStopUSec`, `DefaultTimerAccuracyUSec`, `KExecWatchdogUSec`, `RebootWatchdogUSec`, `RuntimeWatchdogPreUSec`, `RuntimeWatchdogUSec`) and 55 decimal-or-sentinel. | script over A-03.1 applying A-03.3 |
| A-03.6 | ASF/S | `format_timespan(buf, 64, t, accuracy)`: `USEC_INFINITY` ⇒ `infinity`; `t <= 0` ⇒ `0`; otherwise the units `y` (31,557,600 s), `month` (2,629,800 s), `w`, `d`, `h`, `min`, `s`, `ms`, `us` are emitted largest-first, space-separated, each with `t / unit` and the remainder carried; for `t` < 1 min with a non-zero remainder the last unit is written in dot notation to the number of digits `accuracy` allows (accuracy `0` ⇒ full microsecond precision). The result "can be parsed with `parse_sec`". | `SD` `src/basic/time-util.c:520-624`; `src/basic/time-util.h:53,55,62,148` |
| A-03.7 | ASF/S | `shell_maybe_quote(s, 0)` returns `s` unchanged unless it contains a control character, invalid UTF-8, whitespace or a character of `SHELL_NEED_QUOTES`, in which case it returns a `"`-quoted, backslash-escaped form. | `SD` `src/basic/escape.c:552-592` |

* **Typed-to-text dependency statement (review question 3).** H-DI1.2 /
  D 4.3.3 define each baseline value as "the exact bytes after the first `=` of the
  printed form". Facts A-03.3 … A-03.7 show that, for a loader-free reader of the
  **typed** value, reproducing that text is a *separate, fully determined
  computation per signature and per property name* — in particular for the 29
  `…USec`/`…Timespan` properties (`format_timespan`), sentinel values, `ay`
  hex, `as` quoting and the `Exec*` struct form — and that the text of a
  `Timestamp` property depends on timezone and `--timestamp` style. Whether that
  computation is performed, or the typed values are compared instead, is Q6-2's
  (undecided here); no choice is made.
* **Status: partially supported.** Supported: the wire signature and interface of
  all 590 visible properties; the governing print function and its source for each
  signature; exact rules for the eight DI-1 properties. Residuals: R-03.1 the
  version-bound baseline property list (`infra/rp11-unit-properties.<systemd
  version>.txt`, "proposed" in D 4.3.3) is a repository artifact that is not in
  any required reading, so the byte-exact text of its *members* was not
  enumerated property by property; R-03.2 the Unicode/locale-sensitive parts of
  `FORMAT_TIMESTAMP_STYLE` and of `shell_maybe_quote` were identified, not
  re-derived; R-03.3 the 11 + 21 `Timestamp` properties are excluded from the
  baseline's compared set by D 4.3.3 (V set), so their text needs no
  reproduction — that exclusion is accepted text, not a finding here.

### UF-04 — bus error representation and proposed mapping

> Accepted statement: "How a bus error is represented and mapped to `refused`/`error` kinds"

* **Sources.** DB §Message Types (Method Calls, Errors), §Error names;
  `SD` `src/libsystemd/sd-bus/{bus-error.c,bus-common-errors.h,sd-bus.c}`,
  `src/systemd/sd-bus-protocol.h`, `src/core/{dbus-manager.c,dbus-unit.c,dbus-job.c}`,
  `src/shared/bus-polkit.c`; `PK` `data/org.freedesktop.PolicyKit1.Authority.xml`,
  `src/polkit/polkiterror.c`, `src/polkitbackend/polkitbackendauthority.c`.
* **Affects.** DI-1 … DI-5, DI-S; Q3-1 … Q3-5, Q3-7. **Tier split.** The wire
  representation is `W`; which names a pinned server emits is `S`; the mapping
  to `ok`/`refused`/`error` is `PSC` (tier M) and is **not** a fact.

| Id | Class/tier | Fact | Source |
|---|---|---|---|
| A-04.1 | ASF/W | A failed method call is answered by a message of type ERROR (3) carrying the header fields `ERROR_NAME` (string, same syntax as an interface name) and `REPLY_SERIAL`; "if the first argument exists and is a string, it is an error message". The reply is exactly one of METHOD_RETURN or ERROR; with `NO_REPLY_EXPECTED` neither is sent. The specification defines no per-call timeout and no cancellation message; a client that stops waiting simply stops reading, and "a client … simply closes the socket" to disconnect. | DB §Header Fields, §Error names, §Method Calls, §Errors, §Hello |
| A-04.2 | ASF/S | Names emitted by the pinned manager code on the paths used here: `org.freedesktop.DBus.Error.InvalidArgs` (invalid job mode: `src/core/dbus-manager.c:1144`, `src/core/dbus-unit.c:408`; invalid unit name/type: `src/core/dbus-manager.c:1040-1048`; non-zero `StartUnitWithFlags` flags: `src/core/dbus-unit.c:415-426`); `org.freedesktop.systemd1.NoSuchUnit` (`src/core/dbus-manager.c:511`; stop of an unloaded/inactive load-error unit `src/core/dbus-unit.c:1976-1977`; start of a not-found unit `src/core/dbus-unit.c:2730-2731`); `…UnitExists` (`src/core/dbus-manager.c:1055`); `…NoSuchJob` (`src/core/dbus-manager.c:1187,1214`); `…OnlyByDependency` (`src/core/dbus-unit.c:1983-1986`); `…UnitMasked`, `…BadUnitSetting` and an errno-derived error for a unit in load state `error` (`src/core/dbus-unit.c:2733-2741`); `…JobTypeNotApplicable`, `…ConcurrencyLimitReached` (`src/core/transaction.c:999-1010`); transaction conflicts `…TransactionJobsConflicting`, `…TransactionIsDestructive`, `…TransactionOrderIsCyclic`; `…NoIsolation`, `…ShuttingDown`; `…AlreadySubscribed` (`src/core/dbus-manager.c:1421`); `org.freedesktop.DBus.Error.AccessDenied` / `…InteractiveAuthorizationRequired` from the authorization path (`src/shared/bus-polkit.c:326-330`, `-EACCES`). The names are defined in `src/libsystemd/sd-bus/bus-common-errors.h:6-38` and `src/systemd/sd-bus-protocol.h:65-98`. | as cited |
| A-04.3 | ASF/R | A generic errno-derived error is carried as `System.Error.<ERRNONAME>`; `sd-bus` maps standard names to errnos (`ENOMEM`, `EHOSTUNREACH` for `ServiceUnknown`, `ETIMEDOUT` for `NoReply`/`Timeout`, `EACCES` for `AccessDenied`/`AuthFailed`/`InteractiveAuthorizationRequired`, `EINVAL` for `InvalidArgs`, `ENOENT`, `EEXIST`, `EBADR` for the `Unknown*` names, `ECONNRESET` for `Disconnected`, …). This is a client-library convention, not wire contract. | `SD` `src/libsystemd/sd-bus/bus-error.c:14-47,64-71,176` |
| A-04.4 | ASF/R | The sd-bus client reports an elapsed method call as `org.freedesktop.DBus.Error.NoReply` "Method call timed out"; its default method-call timeout is 25 s (`BUS_DEFAULT_TIMEOUT`), overridable by the environment variable `SYSTEMD_BUS_TIMEOUT` or `sd_bus_set_method_call_timeout`. This is a *reference-client* default, not a server or wire property. | `SD` `src/libsystemd/sd-bus/sd-bus.c:2684,4382-4413`; `src/libsystemd/sd-bus/bus-internal.h:311` |
| A-04.5 | ASF/S | Polkit errors on the wire: `org.freedesktop.PolicyKit1.Error.{Failed,Cancelled,NotSupported,NotAuthorized}` (codes 0-3) and `org.freedesktop.PolicyKit1.Error.CancellationIdNotUnique` (code 1000, not exposed in the GObject enum). systemd's own Polkit client treats `Failed`, `Cancelled` and `NotAuthorized` as denial, an unknown service as "polkit absent", and any other error as an error passed through. | `PK` `src/polkit/polkiterror.c:33-39`; `data/org.freedesktop.PolicyKit1.Authority.xml:207-225`; `src/polkitbackend/polkitbackendauthority.c:830-843`; `SD` `src/shared/bus-polkit.c:288-312` |
| A-04.6 | MD | An authorization *challenge* (`is_challenge` true, not authorized) is distinct from an error: it arrives as a normal METHOD_RETURN (A-10.2). | derived from A-10.2 |

* **`PSC` (tier M — proposed outcome mapping, not an accepted fact).**
  P-04.1: a server ERROR whose name is in the set of A-04.2/A-04.5 is mapped to
  `refused(<name>)` **only** where the contract already defines a refusal
  (`PO3-2.1`: `UnitExists` ⇒ `refused(exists)`; `PO3-5.2`: challenge ⇒
  `not-authorized`); every other ERROR, every malformed or oversized reply, every
  transport failure (`Disconnected`/`NoReply`/`Timeout`/`AuthFailed`,
  `ServiceUnknown`) and every client-side timeout is mapped to `error(<name or
  kind>)`; and for a mutating interface an `error` is annotated "effect not
  confirmed" per `PO3-X2`. P-04.2: for `StopUnit`, `NoSuchUnit` is *either*
  `refused(not-loaded)` or a benign "already stopped" outcome — see UF-09; this
  is the conditional `PO3-4.1`. These proposals decide nothing about Q6-6/Q6-7.
* **Status: supported** as to representation and emitted names; the mapping is
  `PSC` only. **Residuals.** R-04.1 error-name coverage is complete for the
  methods and paths used here, not for all D-Bus methods; R-04.2 the
  message-bus daemon's own error replies (`org.freedesktop.DBus.Error.*` from the
  bus, e.g. `AccessDenied` from policy, `OOM` from `AddMatch`) are specified in
  the D-Bus specification but not exhaustively enumerated here.

### UF-05 — job completion, cancellation, abandonment, disconnection, effect observation

> Accepted statement (expanded in R1, quoted in full): "**Expanded in R1 (same identifier, no renumbering).** For DI-2, DI-3, DI-4 and DI-S: the job-completion mechanism (R2 (q) says only that `--wait` uses signal matches and `GetAll`) **and** the cancellation and abandonment facts: how a client cancels or abandons its wait; whether an already accepted or queued job continues; how the eventual job result and the mutation's effect are observed; how cancellation, client disconnection and an unconfirmed outcome map to the accepted `refused`/`error` outcomes and unknown-effect boundaries. A cancelled client wait is not proof that a queued job stopped or that a mutating request had no effect"

The four sub-facts are answered separately. **Cancelling a client wait** and
**cancelling a manager job** are kept apart as in contract §3.0.

* **Sources.** `SD` `src/core/{dbus-manager.c,dbus-unit.c,dbus-job.c,job.c,transaction.c,unit.c,dbus.c}`,
  `src/shared/{bus-wait-for-jobs.c,bus-polkit.c}`, `src/libsystemd/sd-bus/sd-bus.c`; `man/org.freedesktop.systemd1.xml`; DB.
* **Version/distro.** `SD` with the three `dbus-manager.c` patches of §2.7 (they
  add argument-count limits to unrelated methods).

**(i) How a client cancels or abandons its wait — `W`/`R`.**

| Id | Class/tier | Fact | Source |
|---|---|---|---|
| A-05.1 | ASF/W | The D-Bus specification defines **no message that cancels a method call** and no server-visible "client stopped waiting" notification; it defines neither a per-call timeout nor what a service does when the caller's connection closes. | DB §Method Calls; §Hello (disconnect = close the socket); a search of the specification text for "cancel"/"timeout" finds only the SASL `CANCEL` command, SASL cookie-authentication timeouts, the interactive-authorization hint that a caller "should also set a suitably long timeout" and an activation-timeout FIXME — none is a call-cancellation or reply-timeout rule |
| A-05.2 | ASF/R | A reference client abandons a wait by (a) letting its own method-call timeout elapse (A-04.4: `NoReply`), (b) closing the connection, or (c) dropping its signal match slot; `bus_wait_for_jobs` ends a wait on the local pseudo-signal `org.freedesktop.DBus.Local.Disconnected`. None of these is communicated to the manager as "cancel". | `SD` `src/shared/bus-wait-for-jobs.c:81-123`; `src/libsystemd/sd-bus/sd-bus.c:2684` |
| A-05.3 | ASF/S | The *only* ways to cancel a manager job are `Manager.CancelJob(u id)` and `Job.Cancel()`. Each requires `org.freedesktop.systemd1.manage-units` unless the caller is **the job's owner** (a sender tracked in `j->bus_track`, i.e. a sender that queued it), and ends in `job_finish_and_invalidate(j, JOB_CANCELED, …)`. `ClearJobs()` flushes queued jobs (manage-units). The manual states that cancellation "will not have any effect on jobs whose execution has already begun" and that `canceled` "does not necessarily mean … that the job operation is actually cancelled". | `SD` `src/core/dbus-job.c:45-69`; `src/core/dbus-manager.c:1200-1238`; `man/org.freedesktop.systemd1.xml:1364-1371,1644-1646` |

**(ii) Whether an accepted/queued job continues after the client leaves — `S`.**

| Id | Class/tier | Fact | Source |
|---|---|---|---|
| A-05.4 | ASF/S | A job is bound to the *manager*, not to a connection: when the last tracked requester drops off the bus the handler only runs `job_add_to_gc_queue(j)`, and `job_may_gc` returns false for every unit type except those whose vtable sets `gc_jobs` (device units); a service or timer job is therefore not collected because its requester disconnected or timed out. The same holds for jobs referenced by private-bus clients (`ref_by_private_bus`). | `SD` `src/core/dbus-job.c:318-328,361-377`; `src/core/job.c:1465-1523` |
| A-05.5 | ASF/S | `JobNew` is sent before the reply (`bus_job_send_pending_change_signal(j, true)`, `src/core/dbus-unit.c:2022-2023`) and the METHOD_RETURN to `StartUnit`/`StopUnit`/`StartTransientUnit` carries only the job object path `o`; the manual: the job "has been enqueued for asynchronous activation", callers that want the outcome "need to monitor the result of this job". **The reply is not completion.** | `SD` `src/core/dbus-unit.c:2077-2109,2014-2031`; `man/org.freedesktop.systemd1.xml:1288-1294` |
| A-05.6 | ASF/S | With a bus time-out on the client or a lost reply, the call may have reached the manager and queued a job; no source examined makes the server undo anything because the reply could not be delivered. (This is an *absence* finding over the cited functions, stated as such.) | absence over `SD` `src/core/dbus-manager.c:1125-1168`, `src/core/dbus-unit.c:379-440,1955-2109` |
| A-05.7 | ASF/S | `JOB_CANCELED` is also produced without any `CancelJob` call: installing a new job that conflicts with the unit's existing installed job cancels the existing one (`job_install`), an `isolate` transaction cancels the jobs of units outside it, and `ClearJobs` cancels every job. A `JobRemoved` result `canceled` is therefore not by itself proof that the job was cancelled by its own requester. | `SD` `src/core/job.c:241-246`; `src/core/transaction.c:650-660`; `src/core/manager.c:2516-2524` |
| A-05.8 | ASF/S | `JobRemoved` is **not emitted while the manager reloads** ("daemon-reload should be transparent to job observers"); a client that waits across a reload receives the signal only when the job is later removed, and the `Reloading` signal exists (`src/core/dbus-manager.c:3495`). | `SD` `src/core/job.c:172-174` |

**(iii) Completion and effect observation — `S`/`R`.**

| Id | Class/tier | Fact | Source |
|---|---|---|---|
| A-05.9 | ASF/S | Completion is reported by the manager signal `JobRemoved(u id, o job, s unit, s result)` on object `/org/freedesktop/systemd1`, interface `org.freedesktop.systemd1.Manager`, with `result` one of `done`, `canceled`, `timeout`, `failed`, `dependency`, `skipped`, `invalid`, `assert`, `unsupported`, `collected`, `once`, `frozen`, `concurrency` (13 values in the source; the manual lists six). `JobNew(u,o,s)` precedes it. A job finishing with `-EALREADY` (for example `unit_stop` on an inactive unit) ends `done`; `-EBADR` ends `skipped`. | `SD` `src/core/dbus-manager.c:3485-3490`; `src/core/dbus-job.c:195-221,274-300`; `src/core/job.c:957-985,1660-1674`; `src/core/unit.c:2062-2070`; `man/org.freedesktop.systemd1.xml:1638-1650` |
| A-05.10 | ASF/S | Delivery: the signal is a broadcast sent to every *private-socket* connection unconditionally and to the API-bus connection only if at least one client called `Manager.Subscribe()` or the job's own `bus_track` is non-empty (the sender that queued it is added by `bus_job_track_sender`). On the system bus a receiving client must additionally hold a match rule (A-01.5). The manual's recipe: subscribe/match first, call, filter by the returned job path. | `SD` `src/core/dbus.c:1092-1121`; `src/core/dbus-job.c:361-377`; `src/core/dbus-manager.c:1394-1425,3243-3252`; `src/shared/bus-wait-for-jobs.c:96-105`; `man/org.freedesktop.systemd1.xml:1289-1294,1441-1452` |
| A-05.11 | ASF/S | After removal the job no longer exists (`GetJob` ⇒ `NoSuchJob` "Job %u does not exist."), so a client that did not receive `JobRemoved` cannot recover the *result string*; it can still read the resulting *state* (`ActiveState`, `Job`, `Result`, `InvocationID`; UF-03) of the unit. `Job` objects expose `Id u`, `Unit (so)`, `JobType s`, `State s` (`waiting`/`running`), `ActivationDetails a(ss)`. | `SD` `src/core/dbus-manager.c:1170-1198`; `src/core/dbus-job.c:122-143`; `src/core/job.c:1640-1658` |
| A-05.12 | ASF/S | **Partial effect inside `StartTransientUnit`.** The handler (a) checks the mode, (b) runs the Polkit check, (c) loads the main unit and marks it transient (`manager_load_unit`, `unit_make_transient`), applies the properties in the two-pass walk of A-06.5 and dispatches the load queue, (d) creates every auxiliary unit the same way, (e) only then queues the start job. The cited bodies contain no rollback of (c) when a property is rejected, (d) fails or (e) fails; an error after `unit_make_transient` therefore leaves a transient unit in memory without a job. Errors in (a) and (b) leave no state. | `SD` `src/core/dbus-manager.c:1125-1168,1025-1123` (absence finding) |
| A-05.13 | ASF/S | `StopUnit`/`StartUnit` on a name that is not loaded first *load* it (`manager_load_unit`), so even a refused `StopUnit` can load a stub (A-02.3, A-02.7). | `SD` `src/core/dbus-manager.c:747-772` |

**(iv) Mapping — `PSC` only.** The accepted outcome vocabulary (`ok`, `refused`,
`error`, `effect: unknown`) is used; **Q6-6 and Q6-7 are not answered.**

| Id | Class/tier | Proposal | Basis |
|---|---|---|---|
| P-05.1 | PSC/M | Cancelling a client wait, a client-side timeout (`NoReply`), a lost connection and any reply the client could not read are **never evidence that the request had no effect** and never evidence that a queued job stopped; for DI-2, DI-3, DI-4 and DI-S each is recorded as `error` with the contract's "effect not confirmed" annotation, with no silent retry. | A-05.1 … A-05.6; `PO3-X1`, `PO3-X2` (unchanged) |
| P-05.2 | PSC/M | An ERROR reply whose name is in the "no state touched" set — `InvalidArgs` for mode/name/type, `NoSuchUnit` from `StopUnit`/`GetUnit`, `UnitExists`, Polkit denial (`AccessDenied`) — may be recorded as a refusal that is, per the cited code, issued *before* any job is queued; every other ERROR after the call reached `StartTransientUnit` step (c) is `error`/"effect not confirmed" because of A-05.12. | A-04.2, A-05.12 |
| P-05.3 | PSC/M | Completion observation candidates: (O-A) a `JobRemoved` match plus the returned job path (needs subscription/tracking and, on the system bus, a match rule); (O-B) state reads of the target unit after the reply (A-05.11); (O-C) both. A `done` result for a stop of an inactive unit is a *no-op completion*, not evidence that this request changed anything (A-05.9, `-EALREADY`). | A-05.9 … A-05.11 |
| P-05.4 | PSC/M | Because `JobRemoved` is not sent during a reload (A-05.8) and may be lost with a connection, a design that relies on O-A must define what it does when no signal arrives; this record does not define it. | A-05.8 |

* **Status: partially supported.** The cancellation/abandonment facts (A-05.1 …
  A-05.8), the completion/observation facts (A-05.9 … A-05.13) and the absence of
  any server-side undo are supported by exact source. **Residuals.** R-05.1 the
  behavior of the *installed message bus* when a client disconnects while a
  service reply is pending (whether the bus informs the service, drops the reply
  or errors) is bus-implementation behavior outside the pinned sources and the
  D-Bus specification text examined; R-05.2 no execution was performed, so the
  claims in A-05.6 and A-05.12 are absence-of-code findings, not observed
  behavior; R-05.3 the mapping of these facts to `effect: "unknown"` is Q6-6 (and,
  for DI-4 at BS-4, Q6-7) and stays undecided.

### UF-06 — `StartTransientUnit` signature and job mode

> Accepted statement: "The `StartTransientUnit` signature and job mode (R2 gives only the refusal text)"

* **Sources.** `SD` `src/core/{dbus-manager.c,dbus-unit.c,manager.c}`, `src/basic/unit-def.c`,
  `src/run/run.c`, `src/shared/bus-unit-util.c`, `man/org.freedesktop.systemd1.xml`. **Affects.** DI-2, DI-3; Q3-2, Q3-3.

| Id | Class/tier | Fact | Source |
|---|---|---|---|
| A-06.1 | ASF/W | `org.freedesktop.systemd1.Manager.StartTransientUnit` has input signature `ssa(sv)a(sa(sv))` — `name`, `mode`, `properties`, `aux` — and output `o` (the job object path). The method is `SD_BUS_VTABLE_UNPRIVILEGED` and sits under "Managed via polkit" in the bus policy (A-01.6). | `SD` `src/core/dbus-manager.c:3158-3162`; `src/core/org.freedesktop.systemd1.conf:203,275` |
| A-06.2 | ASF/S | `mode` is a string accepted by `job_mode_from_string`; an unknown string is refused before any other effect with `org.freedesktop.DBus.Error.InvalidArgs` "Job mode %s is invalid." The ten modes are `fail`, `lenient`, `replace`, `replace-irreversibly`, `isolate`, `flush`, `ignore-dependencies`, `ignore-requirements`, `triggering`, `restart-dependencies`. The handler's job type is always start; `isolate` additionally requires the unit to allow isolation (`NoIsolation` otherwise), `triggering` is valid only for stop jobs and `restart-dependencies` only for start jobs (`InvalidArgs`). | `SD` `src/core/dbus-manager.c:1138-1144`; `src/basic/unit-def.c:358-371`; `src/core/manager.c:2145-2155` |
| A-06.3 | ASF/R | `systemd-run` sends mode `fail` (its `arg_job_mode` default `JOB_FAIL`) for service, scope and trigger units, and sends an empty or populated `aux` array as in A-08.1. The manual describes `fail` as "will fail if this would change an already queued job". | `SD` `src/run/run.c:113,2145,2895`; `man/org.freedesktop.systemd1.xml:1281-1284` |
| A-06.4 | ASF/S | Authorization is checked *before* any unit is created: `bus_verify_manage_units_async_impl(manager, name, "start", …)` — action `org.freedesktop.systemd1.manage-units`, details `unit` = the new unit name and `verb` = `start` (plus `polkit.message`, `polkit.gettext_domain`). A caller treated as privileged skips Polkit (A-09.5). | `SD` `src/core/dbus-manager.c:1146-1156`; `src/core/dbus-util.c:161-201` |
| A-06.5 | ASF/S | `properties` (`a(sv)`) is applied by `bus_unit_set_properties(u, message, UNIT_RUNTIME, false, …)` to the freshly created unit (the same machinery as `SetUnitProperties`). The array is walked **twice**: a first pass validates every pair without applying it, a second applies them ("transaction-like behaviour without actually providing full transactions"). A pair the unit type does not accept ends the call with `org.freedesktop.DBus.Error.PropertyReadOnly` "Cannot set property %s, or unknown property."; a malformed message ends with the errno-derived "Failed to set unit properties: …". These errors are raised while the (transient, still unloaded) unit already exists in memory (A-05.12). | `SD` `src/core/dbus-manager.c:1025-1084`; `src/core/dbus-unit.c:2622-2718` |

* **Status: supported.** Residuals: R-06.1 the exact error produced by each
  per-type setter for a badly valued property was not enumerated (A-06.5 gives
  the framework behavior only); R-06.2 the semantics of `ignore-dependencies` /
  `ignore-requirements` / `lenient` / `flush` were not analysed (no accepted use
  requires them); the unit manual lists five modes (Appendix C).

### UF-07 — write-side property names, types, units and exec-command structure

> Accepted statement: "Write-side property names, types and units and the exec-command structure for the holder and backstop service (including `ExecStopPost=`)"

* **Sources.** `SD` `src/core/{dbus-service.c,dbus-execute.c,dbus-timer.c}`,
  `src/shared/bus-unit-util.c`, `src/run/run.c`, `src/basic/{process-util.c,unit-def.c}`,
  `src/core/service.c`. **Affects.** DI-2, DI-3; Q3-2, Q3-3.

The write side is the set of `(name, variant)` pairs that `bus_service_set_transient_property`
and the execution-context setter accept. `systemd-run` shows which pairs a
reference client sends (tier `R`); the server column is tier `S`.

| Property sent | Variant | Server acceptance | Client conversion (reference) | Source |
|---|---|---|---|---|
| `Type` | `s` | `service_type_from_string`; `exec` is a member of the table | `--service-type=exec` ⇒ `("Type", "s", "exec")` | `src/core/dbus-service.c:568-569`; `src/core/service.c:5828`; `src/run/run.c:1449-1453` |
| `Restart` | `s` | `service_restart_from_string`; `no` is a member | `Restart=no` ⇒ `("Restart", "s", "no")` | `src/core/dbus-service.c:679-680`; `src/core/service.c:5801`; `src/shared/bus-unit-util.c:2622` |
| `OOMScoreAdjust` | `i` (int32) | must satisfy `oom_score_adjust_is_valid` (`OOM_SCORE_ADJ_MIN`…`OOM_SCORE_ADJ_MAX`), else `InvalidArgs` "OOM score adjust value out of range" | `OOMScoreAdjust=-1000` ⇒ `("OOMScoreAdjust", "i", -1000)` | `src/core/dbus-execute.c:3511-3519`; `src/basic/process-util.c:1249-1251`; `src/shared/bus-unit-util.c:2485` |
| `RuntimeMaxUSec` | `t` (µs) | `bus_set_transient_usec` | `RuntimeMaxSec=<s>` is parsed with `parse_sec` and sent as **`RuntimeMaxUSec`** in µs (suffix `Sec` → `USec`) | `src/core/dbus-service.c:610-611`; `src/shared/bus-unit-util.c:257-277,2606,2641` |
| `TimeoutStopUSec` | `t` (µs) | `bus_set_transient_usec` | `TimeoutStopSec=<s>` ⇒ **`TimeoutStopUSec`** | `src/core/dbus-service.c:594-595`; `src/shared/bus-unit-util.c:2608,2639` |
| `ExecStart`, `ExecStopPost` | `a(sasb)` | one array element per command: `s` path (a valid file name or absolute path, else `InvalidArgs`), `as` **complete argv including `argv[0]`** (must be non-empty), `b` ignore-failure | `ExecStart=`/`ExecStopPost=` via `bus_append_exec_command`; the plain form is used unless a modifier requires the `Ex` form | `src/core/dbus-execute.c:1651-1727`; `src/core/dbus-service.c:694-698`; `src/shared/bus-unit-util.c:566-735,2661` |
| `ExecStartEx`, `ExecStopPostEx` | `a(sasas)` | same, with `as` = flag names (`ignore-failure`, `privileged`, `no-setuid`, `no-env-expand`, `via-shell`) instead of `b` | chosen when a `:`, `+`, `!` or `\|` modifier is present (`-` alone stays in the plain form via the `b`) | `src/core/dbus-execute.c:1688-1706`; `src/shared/bus-unit-util.c:572-657`; `src/shared/exec-util.c:482-488` |
| `Environment` and others | `as` … | not used by the accepted literals | — | — |

| Id | Class/tier | Fact | Source |
|---|---|---|---|
| A-07.1 | ASF/S | The server-side transient setters accept only the `…USec` spellings for time values (microseconds, `t`); the `…Sec` spellings in the accepted command-line literals (`RuntimeMaxSec=`, `TimeoutStopSec=`, `AccuracySec=`) exist only in the *client's* parser. (One exception: the timer setter also tolerates the obsolete name `AccuracySec` with a `t` value and logs a notice.) | `SD` `src/core/dbus-service.c:577-611`; `src/core/dbus-timer.c:211-217` |
| A-07.2 | ASF/S | `argv[0]` is part of the `as` array and is independent of the `path` string; for `via-shell` commands both are normalised to `sh`/`-sh`. A command line with no argv is refused. | `SD` `src/core/dbus-execute.c:1708-1727` |
| A-07.3 | ASF/S | The transient setting is also written as text for the unit (specifier-escaped; environment-expansion-escaped unless `no-env-expand`), so `%` in an argument is escaped and `$VAR` is subject to environment expansion at exec time unless the Ex form carries `no-env-expand` (accepted text R2 §8 (b) already records that the literals contain neither). | `SD` `src/core/dbus-execute.c:1775-1790` |
| A-07.4 | MD | For the accepted holder (RT-1/SA1.OP.2): the wire properties are `Restart "no"`, `OOMScoreAdjust -1000`, `RuntimeMaxUSec ⟨L⟩·10⁶`, `TimeoutStopUSec ⟨S⟩·10⁶`, `ExecStopPost [(path, argv, false)]`, `ExecStart [(path, argv, false)]`, `Type "exec"` — each value form fixed by the table above. For the backstop service (RT2.AK1.2): `Type "exec"`, `Restart "no"`, `OOMScoreAdjust -1000`, `RuntimeMaxUSec ⟨S_b⟩·10⁶`, `TimeoutStopUSec ⟨S⟩·10⁶`, `ExecStart …`, and **no `TimeoutStartUSec`** (BS-RM). | derived from the table and WP-2 rows `SA1.OP.2`, `RT2.AK1.2` |

* **Status: supported** for the properties the accepted literals use.
  Residuals: R-07.1 acceptance of the *unit type* of a property that the
  setter does not know is an error whose exact text depends on
  `bus_unit_set_properties`; R-07.2 the two-pass walk of A-06.5 validates all pairs before
  applying any, so a call with one unacceptable pair is not partially applied to
  the unit's properties; errors that appear only in the apply pass, and the
  state left by `unit_make_transient` before validation (A-05.12), were not
  tested; R-07.3 the sandboxing/credential properties the unit
  could carry were out of scope.

### UF-08 — timer and service created together

> Accepted statement: "How a timer and its service are created together, their naming relation, and the timer property names and types (the Timer interface is not in Appendix A)"

* **Sources.** `SD` `src/run/run.c`, `src/shared/bus-unit-util.c`, `src/core/{dbus-manager.c,dbus-timer.c,timer.c}`.
  **Affects.** DI-3; Q3-3.

| Id | Class/tier | Fact | Source |
|---|---|---|---|
| A-08.1 | ASF/S+R | A timer and its service are created in **one** `StartTransientUnit` call: `name` is the timer (`<x>.timer`), `properties` are the timer's properties, and `aux` carries one element `(service name, a(sv) service properties)` for `<x>.service`. The server creates the main unit, then every `aux` unit through the same `transient_unit_from_message`, then queues the start job for the main (timer) unit only. The manual says `aux` "is currently unused and should be passed as an empty array"; the source of this version uses it (Appendix C). | `SD` `src/core/dbus-manager.c:1086-1123,1158-1167`; `src/run/run.c:2874-2955`; `man/org.freedesktop.systemd1.xml:1602-1603` |
| A-08.2 | ASF/R | `systemd-run --unit=<id>-backstop` (a name without a recognised unit suffix) is mangled to `<id>-backstop.service` and `<id>-backstop.timer`; given a `.service` or `.timer` name the other suffix is derived by `unit_name_change_suffix`. | `SD` `src/run/run.c:2971-3017` |
| A-08.3 | ASF/S | Naming relation: a timer unit without an explicit trigger triggers the same-prefix `.service` (`unit_load_related_unit(…, ".service")`) and gains `Before=` + `Triggers=` on it. The `Unit` property of the Timer interface (`s`) reports the triggered unit. | `SD` `src/core/timer.c:115-129`; `src/core/dbus-timer.c:108` |
| A-08.4 | ASF/S | **Write-side timer properties** accepted by `bus_timer_set_transient_property`: `AccuracyUSec t`, `RandomizedDelayUSec t`, `RandomizedOffsetUSec t`, `FixedRandomDelay b`, `WakeSystem b`, `Persistent b`, `RemainAfterElapse b`, `OnTimezoneChange b`, `OnClockChange b`, `DeferReactivation b`, **`TimersMonotonic a(st)`** (element = base name, µs) and `TimersCalendar a(ss)` (base `OnCalendar`, expression). A `TimersMonotonic` base must be one of `OnActiveSec`, `OnBootSec`, `OnStartupSec`, `OnUnitActiveSec`, `OnUnitInactiveSec`; any other base (including `OnCalendar`) ⇒ `InvalidArgs` "Invalid timer base: %s". An empty `TimersMonotonic` array clears the monotonic specs. | `SD` `src/core/dbus-timer.c:195-300`; `src/core/timer.c:1018-1025` |
| A-08.5 | ASF/S | **Read-side Timer interface** (`org.freedesktop.systemd1.Timer`, 18 properties): `Unit s`, `TimersMonotonic a(stt)` (base, offset, next-elapse µs — three fields, not the two of the write side), `TimersCalendar a(sst)`, `OnClockChange b`, `OnTimezoneChange b`, `NextElapseUSecRealtime t`, `NextElapseUSecMonotonic t`, `LastTriggerUSec t`, `LastTriggerUSecMonotonic t`, `Result s`, `AccuracyUSec t`, `RandomizedDelayUSec t`, `RandomizedOffsetUSec t`, `FixedRandomDelay b`, `Persistent b`, `WakeSystem b`, `RemainAfterElapse b`, `DeferReactivation b`. | `SD` `src/core/dbus-timer.c:106-124` (extraction) |
| A-08.6 | ASF/R | The reference client sends one `TimersMonotonic` property per option (`--on-active=` ⇒ `("TimersMonotonic","a(st)",1,"OnActiveSec",µs)`, `--on-unit-active=` ⇒ `…"OnUnitActiveSec"…`), `--timer-property=AccuracySec=1s` ⇒ `("AccuracyUSec","t",1000000)`, and always adds `RemainAfterElapse=false` for its transient timers. | `SD` `src/shared/bus-unit-util.c:2252-2269,2747-2753`; `src/run/run.c:1701-1716` |
| A-08.7 | MD | For the accepted backstop (RT2.AK1.2): one call, `name` = `⟨activation_id⟩-backstop.timer`, `properties` = `TimersMonotonic [("OnActiveSec", R·10⁶)]`, `TimersMonotonic [("OnUnitActiveSec", R·10⁶)]`, `AccuracyUSec 1000000` (and, if the executor copies the reference client, `RemainAfterElapse false`), `aux` = `[(⟨activation_id⟩-backstop.service, service properties of A-07.4)]`. | derived from A-08.1 … A-08.6, A-07.4, WP-2 `RT2.AK1.2` |

* **Status: supported.** Residuals: R-08.1 the accepted D R2 (f) literal passes
  `--property=TimeoutStartSec=⟨S⟩` while the WP-2 row `RT2.AK1.2` says "no
  `TimeoutStartSec=`" (BS-RM); the two accepted texts differ and this record
  follows neither (Appendix C, O-3). R-08.2 `RemainAfterElapse` is a client
  convention, not required by the accepted rows.

### UF-09 — `StopUnit`: signature, modes, already-inactive and not-loaded, root caller

> Accepted statement: "The `StopUnit` signature, mode and semantics; the result for an already-inactive or not-loaded unit; whether systemd Polkit-checks a root caller"

* **Sources.** `SD` `src/core/{dbus-manager.c,dbus-unit.c,job.c,transaction.c,unit.c,timer.c}`,
  `src/libsystemd/sd-bus/bus-convenience.c`, `src/shared/bus-polkit.c`; R2 §6.2, §8 (j). **Affects.**
  DI-4 (3 sites), DI-S; Q3-4, Q3-7.

| Id | Class/tier | Fact | Source |
|---|---|---|---|
| A-09.1 | ASF/W | `StopUnit(s name, s mode) → o job`. Mode strings are those of A-06.2 except that `isolate` is invalid for stop (`InvalidArgs` "Isolate is only valid for start.") and `restart-dependencies` is invalid for stop; `triggering` is valid only for stop. | `SD` `src/core/dbus-manager.c:3063-3067,770-772`; `src/core/manager.c:2145-2155`; `man/org.freedesktop.systemd1.xml:1303-1305` |
| A-09.2 | ASF/S | Flow: the unit is loaded by name (`manager_load_unit`, creating a stub when no unit file exists); the mode is parsed (invalid ⇒ `InvalidArgs` "Job mode %s invalid"); a Polkit check with verb `stop` (A-09.5); then `bus_unit_queue_job_one`. | `SD` `src/core/dbus-manager.c:747-772`; `src/core/dbus-unit.c:379-440` |
| A-09.3 | ASF/S | **Not loaded / load error and inactive** (including the stub just created by A-09.2 for a name with no unit): `bus_unit_queue_job_one` refuses a stop job with `org.freedesktop.systemd1.NoSuchUnit` "Unit %s not loaded." (`UNIT_IS_LOAD_ERROR` = `not-found`, `bad-setting` or `error`, and active state inactive). No job is queued; the load-state validation of the transaction is skipped for stop jobs. | `SD` `src/core/dbus-unit.c:1976-1977`; `src/core/unit.h:84-86`; `src/core/transaction.c:975-997` |
| A-09.4 | ASF/S | **Loaded and already inactive or failed**: the anchor job of a transaction is never dropped as "redundant" (`tr->anchor_job == k` ⇒ keep); a job is queued and the reply is the job path. When it runs, `unit_stop` returns `-EALREADY` for an inactive or failed unit, and `-EALREADY` finishes the job with result **`done`**. A frozen unit yields `-EDEADLK` ⇒ result `frozen`. A unit with `RefuseManualStop` is refused before queueing with `org.freedesktop.systemd1.OnlyByDependency`. | `SD` `src/core/transaction.c:305-314`; `src/core/unit.c:2062-2088`; `src/core/job.c:906-985`; `src/core/dbus-unit.c:1979-1986` |
| A-09.5 | ASF/S | **Root caller.** `bus_verify_polkit_async_full` returns "authorized" **without querying Polkit** when `sd_bus_query_sender_privilege(call, -1)` is positive, unless the action was registered with `POLKIT_ALWAYS_QUERY` (the manage-units helper does not set it). That function returns positive when the sender's effective uid equals the manager's uid (0 for PID 1) and, when the manager is not root, for a root sender. The sender credentials are those the bus (or, on the private socket, the peer) provides; augmented credentials are refused for authorization. | `SD` `src/shared/bus-polkit.c:540-583`; `src/core/dbus-util.c:161-210`; `src/libsystemd/sd-bus/bus-convenience.c:675-743` |
| A-09.6 | ASF/S | Stopping a `.timer` unit moves it to its dead state (`timer_stop` → `timer_enter_dead`) and returns `1`; the triggered `.service` is a separate unit and is not stopped by this operation (the only job-mode that also stops triggering units is `triggering`, which acts on units that *trigger* the target). Accepted R2 §8 (j) carries the corresponding "stop on the timer enters dead and disables the event sources". Transient units are "released as soon as [they are] not running or referenced anymore". | `SD` `src/core/timer.c:710-717`; `man/org.freedesktop.systemd1.xml:1597-1599`; R2 §8 (j) |
| A-09.7 | MD | Observable results of a `StopUnit(timer, mode)` from a root caller, by state: (i) loaded and active ⇒ reply `o`, later `JobRemoved … done`; (ii) loaded and inactive/failed ⇒ reply `o`, `JobRemoved … done` (no state change); (iii) not loaded ⇒ ERROR `NoSuchUnit`, no job; (iv) invalid mode ⇒ `InvalidArgs`, no job. | A-09.2 … A-09.5 |

* **`PSC`.** P-09.1 (resolves the conditional `PO3-4.1`/`PO3-7.1` text, but
  decides nothing): the three observable results above are *facts*; whether (ii)
  and (iii) are recorded as `ok(already-stopped)` or `refused(not-loaded)` is an
  outcome-vocabulary decision for the contract-integration step, because the
  accepted contract made it "conditional on `UF-09`" and no accepted text assigns
  it. A transient timer that has already been collected after a stop is case (iii).
  P-09.2: DI-S (SA-2) obtains the same four results for `rp11-capture-pass-a.service`;
  the accepted text excludes a stop during start-pre from the route.
* **Status: supported.** Residuals: R-09.1 job behavior when a stop arrives for a
  unit that is `activating`/in start-pre is the accepted R2 PO-21 (u) matter,
  carried, not re-derived; R-09.2 the exact run-time of `unit_stop` for a running
  service (signals, timeouts) is outside UF-09.

### UF-10 — Polkit `CheckAuthorization`: method, signature, subject, flags, details, cancellation

> Accepted statement: "The Polkit check method, its signature, the process-subject encoding, flags, details encoding and cancellation of the Polkit call (DI-6 cancellation belongs to the enclosing DI-5 decision, §3.0)"

* **Sources.** `PK` `data/org.freedesktop.PolicyKit1.Authority.xml`,
  `src/polkit/{polkitauthority.c,polkitsubject.c,polkitunixprocess.c,polkitcheckauthorizationflags.h}`,
  `src/polkitbackend/{polkitbackendauthority.c,polkitbackendinteractiveauthority.c,polkitbackendsessionmonitor-systemd.c}`,
  `src/programs/pkcheck.c`; `SD` `src/shared/bus-polkit.c`. **Affects.** DI-5; Q3-5, Q3-6.
  **Version/distro.** `PK` 127; no Ubuntu patch touches a cited file (§2.7).

| Id | Class/tier | Fact | Source |
|---|---|---|---|
| A-10.1 | ASF/W | Well-known name `org.freedesktop.PolicyKit1`, object `/org/freedesktop/PolicyKit1/Authority`, interface `org.freedesktop.PolicyKit1.Authority` on the **system** message bus. (The interface XML's prose misspells the path as `PoliycKit1`; both polkitd and systemd's client use the correct path.) | `PK` `data/org.freedesktop.PolicyKit1.Authority.xml:33-35`; `SD` `src/shared/bus-polkit.c:82-88` |
| A-10.2 | ASF/W | `CheckAuthorization` input `(sa{sv}) s a{ss} u s` — `subject`, `action_id`, `details`, `flags`, `cancellation_id` — output `(bba{ss})` = `is_authorized`, `is_challenge`, `details`. | `PK` `data/org.freedesktop.PolicyKit1.Authority.xml:275-304`; `src/polkitbackend/polkitbackendauthority.c:607-613` |
| A-10.3 | ASF/W | `flags` (`u`) bits: `NONE` = 0, `ALLOW_USER_INTERACTION` = `1<<0`, `ALWAYS_CHECK` = `1<<1` ("check access against policy even if the subject is the root user"). `ALLOW_USER_INTERACTION` is documented to block while the user authenticates. | `PK` `src/polkit/polkitcheckauthorizationflags.h:35-47`; `data/org.freedesktop.PolicyKit1.Authority.xml:135-145` |
| A-10.4 | ASF/W | `details` is `a{ss}`; the interface text reserves keys starting `polkit.` ("cannot be used"). Only uid 0 (or an identity named by the action's `org.freedesktop.policykit.owner` annotation) may pass details, or ask about a subject that belongs to another identity; otherwise `org.freedesktop.PolicyKit1.Error.NotAuthorized` "Only trusted callers (e.g. uid 0 or an action owner) can use CheckAuthorization() and pass details". (No code enforcing the `polkit.` reservation was located in the files searched.) | `PK` `data/org.freedesktop.PolicyKit1.Authority.xml:288`; `src/polkitbackend/polkitbackendinteractiveauthority.c:885-935,1044-1085` |
| A-10.5 | ASF/W | `subject` is `(sa{sv})`: a kind string plus a dictionary; the kinds are `unix-process`, `unix-session` (`session-id s`) and `system-bus-name` (`name s`, which must be a valid unique name). For `unix-process` the **interface documentation** says the dictionary carries `pidfd` and `uid`, "or alternatively" `pid`, `uid` and `start-time`, and types `pidfd` as `int32`; the **decoder** (A-10.6) and the **libpolkit encoder** (A-10.12) behave differently from that prose, and the three are deliberately kept apart: general PID/start-time form (A-10.6: `pid` and `start-time` required, `uid` optional), pidfd form (A-10.6: `pidfd` and `uid` required) and the `pkcheck`-equivalent shape (A-10.10, A-10.12: `pid`, `start-time` and `uid`). | `PK` `data/org.freedesktop.PolicyKit1.Authority.xml:43-45`; `src/polkit/polkitsubject.c:299-341,399-534` |
| A-10.6 | ASF/S | polkitd's decoder (`polkit_subject_new_for_gvariant_invocation`) reads a `unix-process` subject as follows. `uid` (`i`) is **optional in the general PID/start-time form and required in the pidfd form**. **General PID/start-time form** (used whenever the message carries no file-descriptor list or the dictionary has no `pidfd` key): `pid` (`u`) and `start-time` (`t`) are **both required** (missing or ill-typed ⇒ `Failed`, text prefixed "Error parsing unix-process subject: "); `uid` is optional (absent ⇒ −1). **pidfd form** (used only when the message carries a file-descriptor list **and** a `pidfd` key of type `h`): `uid` is **required** (absent ⇒ `Failed` "Error parsing unix-process subject: 'pidfd' specified withtout 'uid'", sic), `pid` and `start-time` are not read, and the process is created from the descriptor. A `pidfd` key with no descriptor list is ignored and the PID/start-time form applies. | `PK` `src/polkit/polkitsubject.c:415-482` |
| A-10.7 | ASF/W | **Cancellation.** `cancellation_id` (`s`) is "a unique id used to cancel the authentication check via `CancelCheckAuthorization()` or the empty string if cancellation is not needed"; polkitd scopes it per calling connection (`"<sender unique name>-<id>"`); reusing a non-empty id already in use by that caller ⇒ `org.freedesktop.PolicyKit1.Error.CancellationIdNotUnique`; `CancelCheckAuthorization(s)` for an unknown id ⇒ `Failed` with text "No such cancellation_id '<id>' for name <name>", for a known id it cancels the request's `GCancellable` and replies `()`. polkitd creates a cancellable only for a non-empty id and removes the registration when the request completes. | `PK` `src/polkitbackend/polkitbackendauthority.c:779-870,874-908,746-777`; `data/org.freedesktop.PolicyKit1.Authority.xml:221-224,296-312` |
| A-10.8 | MD | That `cancellable` is consulted **only** for an interactive challenge (`ALLOW_USER_INTERACTION` set, `is_challenge` true, an authentication agent registered): `check_authorization` passes it solely to `authentication_agent_initiate_challenge`, and otherwise completes the request synchronously inside the same call. A non-interactive request (flags `NONE`) therefore cannot be affected by `CancelCheckAuthorization`, and a client that abandons it changes no polkitd state (the decision path only reads rules and the in-memory temporary-authorization store). | derived from `PK` `src/polkitbackend/polkitbackendinteractiveauthority.c:941-1160` (esp. 1106-1146) |
| A-10.9 | ASF/R | The reference client `libpolkit` sends the empty `cancellation_id` unless the caller supplied a `GCancellable`, in which case it generates `cancellation-id-<n>` and, when the cancellable fires, sends `CancelCheckAuthorization`; its D-Bus call uses `G_DBUS_CALL_FLAGS_NONE` and timeout `G_MAXINT` ("no timeout"). `pkcheck` supplies no cancellable. | `PK` `src/polkit/polkitauthority.c:820-868,905-947` |
| A-10.10 | ASF/R | `pkcheck --process pid,start,uid --detail unit … --detail verb …` (without `--allow-user-interaction`) builds its subject with `polkit_unix_process_new_for_owner(pid, start, uid)` (the three-value form; the two-value form `pid,start` omits `uid`), and with the encoder of A-10.12 puts on the wire: subject `("unix-process", {pid u, start-time t, uid i})` **and no `pidfd`**, the action, `details {unit, verb}`, flags `0`, cancellation `""`. This `pkcheck`-equivalent shape therefore *deliberately supplies* `uid`, which the general PID/start-time form of A-10.6 does not itself require. systemd's own client sends subject `("system-bus-name", {name s})`, `us` = flags and `NULL` (= empty) cancellation id. | `PK` `src/programs/pkcheck.c:387-419,541-550`; `src/polkit/polkitsubject.c:299-341`; `SD` `src/shared/bus-polkit.c:63-106` |
| A-10.11 | ASF/S | Authorization of an *unregistered* action ⇒ `Failed` "Action %s is not registered". polkitd never constructs a result with both booleans true: it returns `(true,false)` (authorized), `(false,true)` (challenge), `(false,false)` (not authorized). | `PK` `src/polkitbackend/polkitbackendinteractiveauthority.c:1216-1224,1237,1286,1299,1370,1381` |
| A-10.12 | ASF/R | libpolkit's encoder (`polkit_subject_to_gvariant`) always writes `pid` (`u`), `start-time` (`t`) and `uid` (`i`) for a `PolkitUnixProcess`, and adds `pidfd` (`h`) **only** when the object's `pidfd_is_safe` flag is set. That flag is set in the constructor only when a descriptor was supplied by the caller ("We didn't open it ourselves here, so we must have got it from D-Bus"); a descriptor the constructor opens itself (when built with `HAVE_PIDFD_OPEN`) leaves it unset, so a client that constructs a process subject from a pid never puts `pidfd` on the wire. | `PK` `src/polkit/polkitsubject.c:299-341`; `src/polkit/polkitunixprocess.c:376-424` |

* **`PSC`.** P-10.1 candidate request shapes for DI-5 (all tier M, none selected):
  (S-A) the `pkcheck`-equivalent shape of A-10.10 (`unix-process` with `pid`,
  `start-time` **and** `uid`; flags 0; empty cancellation id; details exactly
  `unit`, `verb`) — `uid` is supplied deliberately, because H-PROC.5 reads it,
  although the general PID/start-time form requires only `pid` and `start-time`
  (A-10.6); (S-B) a `pidfd` + `uid` subject (both required in the pidfd form,
  A-10.6), which needs file-descriptor passing (UNIX_FDS negotiation, A-01.3)
  and is **not** the shape the accepted H-PROC.5 describes — adopting it would
  be an amendment, so it is listed only as an option. The decoder would also
  accept a PID/start-time subject without `uid` (A-10.6); that is a fact about
  the decoder, not a candidate of this record, and neither shape is selected. DI-5 as accepted is non-interactive, so the
  cancellation id is `""` and cancellation of the Polkit call is moot (A-10.8).
* **Status: supported.** Residuals: R-10.1 whether the installed polkitd was
  built with `HAVE_PIDFD_OPEN` (derived true from `meson.build:215` when
  `SYS_pidfd_open` is defined; the built binary was not inspected); R-10.2 polkitd's
  behavior when a *non-interactive* client disconnects mid-call is moot by A-10.8 but
  was not separately traced in `GDBus`.

### UF-11 — mapping the authority's result fields to the three accepted outcomes

> Accepted statement: "The mapping from the authority's result fields to `authorized`/`not-authorized`/`error`, replacing `pkcheck`'s exit statuses (R8 E-2)"

* **Sources.** `PK` `src/programs/pkcheck.c`, `src/polkit/polkitauthorizationresult.c`,
  `polkitbackendinteractiveauthority.c`; `SD` `src/shared/bus-polkit.c`. **Affects.**
  DI-5; Q3-5.

| Id | Class/tier | Fact | Source |
|---|---|---|---|
| A-11.1 | ASF/R | `pkcheck`'s own mapping from the *result fields* is: call failed ⇒ 127; `is_authorized` ⇒ 0; else `is_challenge` ⇒ 2 (whether or not interaction was requested); else the detail `polkit.dismissed` present ⇒ 3; else 1. This is a reference-client rule that the accepted R8 E-2 says "does not carry over". | `PK` `src/programs/pkcheck.c:551-557,588-645`; `src/polkit/polkitauthorizationresult.c:238-262` |
| A-11.2 | ASF/S | `polkit.dismissed` is inserted only when an authentication-agent challenge is dismissed (`dismissed` ⇒ `(false,false)` with that key); a request made without `ALLOW_USER_INTERACTION` cannot take that path. | `PK` `src/polkitbackend/polkitbackendinteractiveauthority.c:719-800,1106-1135` |
| A-11.3 | ASF/R | systemd's own client reads `(bba{ss})` and treats `is_authorized` as grant, a `false`+`is_challenge` as `InteractiveAuthorizationRequired`, `false`+`false` as denial; it maps the errors `Failed`, `Cancelled`, `NotAuthorized` to denial and a missing service to "polkit absent". | `SD` `src/shared/bus-polkit.c:273-337` |

* **`PSC` (tier M).** P-11.1: map the reply fields to the accepted outcomes of
  H-PK2.5 / `PO3-5.1` as: `(true, ·, ·)` ⇒ `authorized`; `(false, true, ·)` ⇒
  `not-authorized` (`PO3-5.2`: a challenge is not an error); `(false, false, ·)` ⇒
  `not-authorized`; **every** D-Bus ERROR reply (including the four Polkit error
  names and the bus's own `ServiceUnknown`/`NoReply`), a reply whose signature is
  not `(bba{ss})`, a reply with both booleans true (never produced by polkitd,
  A-10.11), a truncated or oversize reply and a client-side deadline or abandon ⇒
  `error` (consistent with H-PK2.5 "any unparsable result, deadline or abandon is
  `error`"). The `details` map is not needed for the three outcomes.
* **Status: supported** as a field-level description; the mapping is `PSC`.
  Residual: R-11.1 whether the accepted `volume cap 65,536 bytes` of H-PK2.5
  has a D-Bus counterpart (a received message size) is not decided by any source
  here (the specification caps messages at 128 MiB, A-01.4).

### UF-12 — process-subject start time: unit and encoding

> Accepted statement: "The unit and encoding of a process subject's start time, and that `/proc` field 22 is that value (H-PROC.5 names the field; PO-SN (d) is proposed only)"

* **Sources.** `PK` `src/polkit/{polkitunixprocess.c,polkitsubject.c}`; `MP` `proc_pid_stat(5)`;
  `KN` `fs/proc/array.c` (upstream `v7.0`/`v7.0.14`, byte-identical per the R2 comparison in §2.4; Ubuntu delta §2.4).
  **Affects.** DI-6; Q3-6.

| Id | Class/tier | Fact | Source |
|---|---|---|---|
| A-12.1 | ASF/W | On the wire the start time is the `start-time` key of the subject dictionary, a D-Bus `UINT64` (`t`); its value is a decimal integer parsed with `strtoull(…, 10)` from the `/proc/<pid>/stat` token that is 20th after the `") "` that follows the **last** `)` (the command name may contain `)`), i.e. stat field 22; fewer than 20 tokens or a non-numeric token ⇒ `POLKIT_ERROR_FAILED` "Error parsing file /proc/<pid>/stat". | `PK` `src/polkit/polkitsubject.c:299-341,471-478`; `src/polkit/polkitunixprocess.c:1261-1330` |
| A-12.2 | ASF/W | stat field 22 `starttime` is "the time the process started after system boot", "expressed in clock ticks (divide by `sysconf(_SC_CLK_TCK)`)" since Linux 2.6. The kernel prints it as `nsec_to_clock_t(timens_add_boottime_ns(task->start_boottime))` — the boot-time clock (it includes suspended time) adjusted by the reader's time-namespace boot-time offset. | `MP` `man/man5/proc_pid_stat.5` field (22); `KN` `fs/proc/array.c:580-581,606` |
| A-12.3 | ASF/S | Ubuntu's kernel delta (`7.0.0-31.31`) changes `do_task_stat` to take `task->signal->exec_update_lock` with `down_read_killable` before formatting and to return the error if a fatal signal arrives: a read of `/proc/<pid>/stat` can therefore wait while the target is in `execve` and fail instead of returning a value. The H-PROC.5 rule "unreadable ⇒ the call is `error`" already covers a failed read. | Ubuntu diff `linux_7.0.0-31.31.diff.gz` hunk `fs/proc/array.c @@ -482,6 +482,11`, `@@ -657,6 +662,7`; accepted `H-PROC.5` |
| A-12.4 | MD | The value H-PROC.5 reads ("`/proc` field 22") and the value polkitd/libpolkit read and compare are the **same field read the same way**; `start_ticks` of the child handle (H-PROC.4, optional PO-SN (d)) is also that field. The encoding for DI-5 is therefore: unsigned 64-bit decimal clock ticks, no other transformation. | A-12.1, A-12.2 |
| A-12.5 | ASF/S | A supplied `start-time` of `0` means "look it up now" (`start_time == 0` ⇒ `get_start_time_for_pid`), i.e. no verification against what the client saw. | `PK` `src/polkit/polkitunixprocess.c:426-427,1015-1019` |

* **Status: supported.** Residuals: R-12.1 the numeric value of `sysconf(_SC_CLK_TCK)`
  / `USER_HZ` for this kernel/architecture was not extracted (it does not affect
  the encoding); R-12.2 the polkit source comment calls the granularity "in the
  millisecond range", the field is in clock ticks — the comment is not relied on.

### UF-13 — how polkitd treats the subject's start time and uid

> Accepted statement: "How polkitd treats a process subject's start time and uid (verification, mismatch result)"

* **Sources.** `PK` `src/polkit/polkitunixprocess.c`, `src/polkit/polkitsubject.c`,
  `src/polkitbackend/polkitbackendsessionmonitor-systemd.c`,
  `src/polkitbackend/polkitbackendinteractiveauthority.c`, `meson.build`.
  **Affects.** DI-6 → DI-5; Q3-6.

| Id | Class/tier | Fact | Source |
|---|---|---|---|
| A-13.1 | ASF/S | **Start-time verification.** When the user of a `unix-process` subject is resolved, polkitd calls `polkit_unix_process_get_racy_uid__`, which reads `/proc/<pid>/status` (`Uid:` — the **real** uid, first value), then re-reads the start time and compares it with the subject's `start_time`; a difference ⇒ `POLKIT_ERROR_FAILED` "process with PID %d has been replaced"; a missing process or `pid <= 0` ⇒ `Failed` "Process not found" or the GIO read error. This is an ERROR reply, not an authorization result. | `PK` `src/polkit/polkitunixprocess.c:1806-1927`; `src/polkitbackend/polkitbackendsessionmonitor-systemd.c:268-302` |
| A-13.2 | ASF/S | **uid.** The supplied `uid` (optional in the PID/start-time form, required in the pidfd form; A-10.6) is, when present, the identity policy is evaluated for ("every subject has a user; this is supplied by the client, so we rely on the caller to validate its acceptability"). If it differs from the current real uid, the request is accepted only from a trusted caller (uid 0 or action owner); a root caller's mismatching uid is not an error and the decision is made for the supplied uid. An absent `uid` is filled from `/proc` at construction; if that fails, `Failed` "Unix process subject does not have uid set". The NSS-dependent group tests of rules are evaluated for that uid at each decision (R2 §6.1). | `PK` `src/polkitbackend/polkitbackendinteractiveauthority.c:1002-1086,1226-1232`; `src/polkit/polkitunixprocess.c:429-439`; `src/polkitbackend/polkitbackendsessionmonitor-systemd.c:284-301` |
| A-13.3 | ASF/S | **pidfd behavior of polkitd 127.** When built with `HAVE_PIDFD_OPEN`, constructing a `unix-process` from a `pid` opens a pidfd for that pid, stores it, and sets the stored pid to 0; the pid is thereafter recovered from `/proc/self/fdinfo/<pidfd>` (`Pid:`). `polkit_unix_process_exists_sync` returns `TRUE` without comparing start times when a pidfd is held. A pidfd that polkitd opened itself is marked *not safe* (it is sent on the wire only when `pidfd_is_safe`). The start-time comparison of A-13.1 is still made against the supplied value. | `PK` `src/polkit/polkitunixprocess.c:320-368,375-427,730-748,1105-1143`; `meson.build:215` |
| A-13.4 | ASF/S | polkit's own source states that reliable, race-free tracking "requires support for PID File Descriptors in the kernel, dbus-daemon/broker and systemd", that the PID/start-time fallback "is now known broken" (a non-atomic `fork` lets an attacker obtain a process indistinguishable by pid and start time), and that `polkit_subject_equal` on two processes should be avoided without pidfds. | `PK` `src/polkit/polkitunixprocess.c:55-147` |
| A-13.5 | ASF/S | **Root subject.** A subject whose resolved user is uid 0 is authorized for any action without consulting policy, unless `ALWAYS_CHECK` is set. | `PK` `src/polkitbackend/polkitbackendinteractiveauthority.c:1234-1239`; R2 §6.3 |

* **`PSC`.** P-13.1: an executor that follows the accepted DI-6 intent can
  expect, for a live unreaped child it created, a decision for the supplied uid;
  a start-time that no longer matches is an ERROR (mapped to `error`, P-11.1). The
  residual weakness named by polkit's own comments (A-13.4) is an upstream
  property of the PID/start-time form and is **not** closed by this record; whether
  the pidfd form (P-10.1 S-B) is preferable is a decision for Peter.
* **Status: supported.** Residuals: R-13.1 derived `HAVE_PIDFD_OPEN` (see R-10.1);
  R-13.2 the kernel's own `pidfd_open(2)` and `/proc/self/fdinfo` semantics were not
  researched beyond polkit's use; R-13.3 polkitd's `Failed` error text for a
  timing mismatch is a string in this version, not a stable contract.

### UF-14 — per-property reads of `HIDDEN`/`EXPLICIT` properties

> Accepted statement: "Whether a per-property read can reach `HIDDEN`/`EXPLICIT` properties that `GetAll` omits"

* **Sources.** `SD` `src/libsystemd/sd-bus/bus-objects.c`, vtable files, `src/systemd/sd-bus-vtable.h`;
  DB §`org.freedesktop.DBus.Properties`. **Affects.** DI-1; Q3-9.

| Id | Class/tier | Fact | Source |
|---|---|---|---|
| A-14.1 | ASF/S | `Properties.Get(interface, property)` looks the property up by exact `(path, interface, member)` in the object's property table and answers it. The lookup and `property_get_set_callbacks_run` contain **no test of `SD_BUS_VTABLE_HIDDEN` or `SD_BUS_VTABLE_PROPERTY_EXPLICIT`**; the code comment states "Read access to properties is always unrestricted". | `SD` `src/libsystemd/sd-bus/bus-objects.c:1331-1353,565-630` |
| A-14.2 | ASF/S | `Properties.GetAll(interface)` omits `HIDDEN` properties and `EXPLICIT` properties (the latter "only in those generated as a response to an explicit request"); an empty interface string means all interfaces. | `SD` `src/libsystemd/sd-bus/bus-objects.c:751-798,1355-1372` |
| A-14.3 | MD | Therefore a per-property `Get` **can** read a `HIDDEN` or `EXPLICIT` property that `GetAll` omits, provided the exact interface name and property name are given. The hidden set in the pinned tree is 28 Unit/Service entries and 5 Manager entries; **no** `EXPLICIT` property exists in any of the nine vtables. All eight DI-1 properties, and every property of R2 Appendices A and B, are visible, so no DI-1 use depends on this. | extraction (A-03.1); `SD` `src/core/dbus-cgroup.c:438-448`, `src/core/dbus-service.c:345,413-417`, `src/core/dbus-execute.c:1418-1422`, `src/core/dbus-unit.c:965,1090-1096`, `src/core/dbus-manager.c:2950,2964-2965,3014-3016` |
| A-14.4 | ASF/W | The D-Bus specification says that for `GetAll` "properties not accessible to the caller … should be silently omitted" and `Get` of such properties "an appropriate access control error should be returned"; and that an empty interface name with duplicate property names has undefined results. The systemd implementation returns `UnknownProperty` "Unknown interface %s or property %s." for a wrong interface/name pair (`Get` has no empty-interface form). | DB §`org.freedesktop.DBus.Properties`; `SD` `src/libsystemd/sd-bus/bus-objects.c:1463-1474` |

* **Status: supported.** Residual: R-14.1 R2 Appendix C.1 labels the hidden
  Unit/Service group "(27)" but lists 28 entries (Appendix C, O-4); the extraction
  gives 28.


## 4. Fact-and-proposal matrix `UF-15` … `UF-18` (baseline acquisition, Q3-11)

These four items concern *how a static image would obtain* the baseline facts of
`H-BSE.1`, `.2`, `.3`, `.4` and `.6`. The accepted answer today is the
fail-closed record `PO3-11.1` (each acquisition `unavailable`, the baseline fails
closed). This section adds authoritative facts and **candidate** mechanisms
(`PSC`, tier M); it chooses none and designs no WP-4 mechanics. For every item the
six prompt headings are answered in order.

### UF-15 — host nodename, machine-id hash, architecture, kernel release (H-BSE.1)

> Accepted statement: "Direct acquisition of host nodename, machine-id hash, architecture, kernel release (H-BSE.1)"

**1. Authoritative facts about direct sources.**

| Id | Class/tier | Fact | Source |
|---|---|---|---|
| A-15.1 | ASF/W | `uname(2)` fills `sysname`, `nodename`, `release`, `version`, `machine` (and the GNU `domainname`); the library prototype leaves field lengths unspecified ("use `sizeof`"); the kernel has name/release/version/machine built in, while `nodename` is the administrator-configured name (set with `sethostname(2)`); standard POSIX.1-2024. | `MP` `man/man2/uname.2` (NOTES, VERSIONS, STANDARDS) |
| A-15.2 | ASF/S | The kernel's `newuname` copies the *caller's UTS namespace* `struct new_utsname` under `uts_sem` (six fields of `__NEW_UTS_LEN + 1` = 65 bytes each, 390 bytes) and then applies two personality-dependent overrides: with the `UNAME26` personality the release string is rewritten, and with `PER_LINUX32` the `machine` string is replaced by `COMPAT_UTS_MACHINE`. Ubuntu `7.0.0-31.31` adds a `compat_uts_machine=` early parameter that changes that replacement string. Upstream `v7.0` and `v7.0.14` are byte-identical for `kernel/sys.c`, `include/uapi/linux/utsname.h` and `kernel/utsname_sysctl.c` (R2 comparison, §2.4). | `KN` `kernel/sys.c:1308-1366`; `include/uapi/linux/utsname.h:1-28`; Ubuntu diff hunk `kernel/sys.c @@ -1308,6 +1308,21` |
| A-15.3 | ASF/S | The same data is exposed as `/proc/sys/kernel/{arch,ostype,osrelease,version,hostname,domainname}`; the first four are mode `0444`, `hostname` and `domainname` `0644`. | `KN` `kernel/utsname_sysctl.c:74-123` |
| A-15.4 | ASF/W | `/etc/machine-id` is "a single newline-terminated, hexadecimal, 32-character, lowercase ID" that "may not be all zeros"; it may be empty or missing on a first boot (systemd then writes the literal `uninitialized\n` and overmounts a temporary file carrying the real ID), may be bind-mounted over, and is overridden by `systemd.machine_id=` / `--machine-id=` for the running manager. It "should be considered confidential" and not exposed — hence the baseline stores only its SHA-256 (H-BSE.1). | `SD` `man/machine-id.xml` (Description, Initialization, First Boot Semantics) |

**2. `PSC` candidates (tier M).**

| Id | Candidate | Prerequisites | Failure behavior (abstract) |
|---|---|---|---|
| P-15.1 | Obtain `nodename`, `release`, `machine` (and `version` if ever needed) with the `uname` system call. | a process that can issue the call; no files | call failure ⇒ that baseline key `unavailable` (`PO3-11.1`) |
| P-15.2 | Obtain the same four from `/proc/sys/kernel/{hostname,osrelease,arch,version}`. | `/proc` mounted and readable | open/read failure or an empty/over-long value ⇒ `unavailable` |
| P-15.3 | Obtain the machine-id digest by reading `/etc/machine-id` once and hashing its bytes (SHA-256, as H-JRN.4 already uses). | file readable; a hash facility (an accepted need regardless) | absent, unreadable, wrong length, not 32 lowercase hex plus LF, the `uninitialized` marker, or all zeros ⇒ one of: `unavailable`, or "recorded as the literal bytes' digest" — **a decision (D-11)** |

**3. Compatibility with the accepted boundary.** P-15.1 … P-15.3 use a system call
or file reads only; none requires an `execve`, a child process or a distribution
program. They are compatible in principle with the loader-free/no-distribution-
child boundary and with BQ-4. (They do not fix how the call or read is realized.)

**4. Limitations.** (a) Personality: the `uname` call, unlike the `/proc` files
(which are read-only views of the namespace data), can return an altered `release`
or `machine` for a process with `UNAME26` or `PER_LINUX32`; the baseline's
`architecture` is `x86_64` and `kernel_release` is compared numerically on the
dotted prefix (D 4.3.2 `po18`). (b) Namespace: both views are those of the
*calling* process's UTS namespace. (c) `nodename` is mutable at run time by root.
(d) `/etc/machine-id` can be overmounted or transient (A-15.4): the file bytes need
not equal the running manager's ID. (e) The H-BSE.1 hash is of the file, not of the
manager's ID. (f) Distro delta on the kernel: only A-15.2's `compat_uts_machine`.

**5. Decision Peter would need to make (later).** D-11: which source (P-15.1 or
P-15.2) the acquisition uses for the three UTS-derived keys, and what the
acquisition records when `/etc/machine-id` is not a well-formed 33-byte value.

**6. WP-4 details left undesigned.** the call wrapper and error mapping, buffer
handling for 65-byte fields, how `/proc` text is trimmed, the hash implementation,
and whether the value is cached between H-2 and AP-0.

**Status: supported as to facts; mechanism is `PSC` (not closed).** Residuals:
R-15.1 the installed host's personality/namespace situation was not observed (no
host observation was authorized); R-15.2 exact `UTS_MACHINE` string for this build was not extracted.

### UF-16 — operator account, group and supplementary-group data through NSS (H-BSE.2)

> Accepted statement: "Direct acquisition of operator account, group and supplementary-group data through NSS (H-BSE.2)"

**1. Authoritative facts.**

| Id | Class/tier | Fact | Source |
|---|---|---|---|
| A-16.1 | ASF/W | `/etc/passwd` has seven colon-separated fields `name:password:UID:GID:GECOS:directory:shell`; `/etc/group` has four `group_name:password:GID:user_list` with `user_list` the comma-separated member names. The group file lists *supplementary* membership; the primary GID is in the passwd record. | `MP` `man/man5/passwd.5`, `man/man5/group.5` |
| A-16.2 | ASF/W | `/etc/nsswitch.conf` determines, per database (`passwd`, `group`, `initgroups`, …), "the sources from which to obtain name-service information … and in what order". `getgrouplist(user, group, groups, &ngroups)` "scans the group database" and returns the user's groups, **adding `group` (normally the passwd GID) if it is not among them**; `*ngroups` is value-result and may exceed the capacity. | `MP` `man/man5/nsswitch.conf.5`, `man/man3/getgrouplist.3` |
| A-16.3 | ASF/S | glibc `2.43-2ubuntu2.4` implements the lookup in the C library: `internal_getgrouplist` consults the `initgroups` database if configured, else the `group` database, else `files`; it removes duplicates and honors per-source actions; `nsswitch.conf` is re-read with file-change detection. The modules `files` and `dns` are built in; **any other service is loaded with `__libc_dlopen("libnss_<name>.so<revision>")`**, i.e. requires the dynamic loader. The manual notes that in statically linked programs "the main application and NSS modules do not share the same thread-local variable `errno`". | `GL` `nss/initgroups.c:46-137`; `nss/nss_module.c:170-189`; `nss/nss_database.c:297-402`; `manual/nss.texi:521-530` |
| A-16.4 | ASF/S | The packaged default `/etc/nsswitch.conf` lists only `files` for `passwd`, `group`, `shadow`, `gshadow`; the pinned systemd's `libnss-systemd` post-install script adds `systemd` to those databases when that package is installed, and `nss-systemd` answers `getpwnam`/`getgrnam` through `userdb_*` calls (a different mechanism from files). | `GL` `debian/local/etc/nsswitch.conf:7-10`; `SD` `debian/libnss-systemd.postinst:14-28`; `src/nss-systemd/nss-systemd.c:337,477` |
| A-16.5 | DR | R2 §6.1 (accepted): group membership used by Polkit rules "is evaluated through NSS at each decision"; HF-03 records `ubuntu` with groups `ubuntu adm cdrom sudo dip lxd freedomlab`. | R2 line 620 |

**2. `PSC` candidates.**

| Id | Candidate | Prerequisites | Failure behavior (abstract) |
|---|---|---|---|
| P-16.1 | Parse `/etc/passwd` and `/etc/group` directly per A-16.1 (name, uid, gid, primary group, supplementary list sorted by gid). | both files readable; a bounded line parser (an accepted Q4-5 need anyway) | missing/oversize/unparsable ⇒ `unavailable` |
| P-16.2 | Resolve through the C library's NSS entry points (`getpwnam_r`, `getgrouplist`, `getgrgid_r`) as the baseline text says "through NSS". | an NSS-capable C library at run time; if `nsswitch.conf` names a service other than `files`/`dns`, the dynamic loader and the service module | any non-`files` source ⇒ requires `dlopen` of a distribution library; failure ⇒ `unavailable` |
| P-16.3 | Declare the operator keys of the baseline a **file-database** fact (equal to NSS only while `passwd`/`group` are `files`) and make "the configured `nsswitch.conf` lists exactly `files` for `passwd`, `group` and `initgroups`" a further baseline fact. | `/etc/nsswitch.conf` readable and parsable | a different configuration ⇒ `unavailable` (fail closed) |

**3. Compatibility with the boundary.** P-16.1 and P-16.3 are compatible in
principle (file reads only). **P-16.2 is compatible only if the configured sources
are `files`** (built into the C library): any other source loads a
`libnss_<name>.so.2` object (A-16.3), which is a dynamically loaded distribution
library under a static root image — the situation the loader-free boundary
(LR-2/BQ-4) exists to exclude. A statically linked C library does not remove that
requirement (A-16.3, manual). Whether `getgrouplist` through `files` alone is
"loader-free" is a boundary interpretation left to Peter.

**4. Limitations.** (a) NSS equivalence: files-only parsing equals NSS only when
`nsswitch.conf` is files-only for the three databases; the host configuration and
whether `libnss-systemd` is installed were **not** established by any accepted
record (HF-07's package list does not include it). (b) `initgroups` versus `group`:
`getgrouplist` uses the `initgroups` database when configured (A-16.3). (c)
`passwd`/`group` are mutable at run time and are not read atomically; `files`
databases can change between H-2 and the pass (the baseline's drift rule already
stops on a changed uid/gid/groups, D 4.6.3). (d) The primary group is added by
`getgrouplist` (A-16.2) and is in `passwd`, not necessarily in the `group`
`user_list`. (e) Portability across versions: man-pages 6.17 and glibc 2.43 are the
versions read.

**5. Decision.** D-12: choose P-16.1/P-16.3 (files-only, fail closed otherwise)
versus P-16.2 (library NSS), and decide whether "NSS" in `H-BSE.2` must be
preserved literally; this is also the Q6-3 behavior-preservation question.

**6. WP-4 left undesigned.** the parser, line/size bounds, sorting, the
supplementary-group derivation, and error mapping.

**Status: supported as to facts; mechanism is `PSC` (not closed).** Residuals:
R-16.1 host `nsswitch.conf` and `libnss-systemd` presence unknown; R-16.2 the
`userdb` varlink mechanism behind `nss-systemd` was identified, not analysed.

### UF-17 — repository commit identity, launcher file attributes, re-read-versus-carried keys (H-BSE.3, H-BSE.6)

> Accepted statement: "Direct acquisition of repository commit identity and of the launcher file attributes, and which `H-BSE.6` keys are re-read vs carried (H-BSE.3, H-BSE.6)"

**1. Authoritative facts.**

| Id | Class/tier | Fact | Source |
|---|---|---|---|
| A-17.1 | ASF/W | Git on-disk layout (git `2.53.0` documentation): a repository directory contains `HEAD` (a symref such as `ref: refs/heads/<name>` or, when detached, a commit id), `refs/heads/<name>` files, an optional `packed-refs` file recording the same refs "in a more efficient way", the object store (`objects/…` loose objects and `objects/pack/`), `commondir` and `worktrees/` for linked worktrees; a working tree's `.git` may be a *gitfile* — a text file `gitdir: <path>`; with `$GIT_COMMON_DIR` set, `refs`, `packed-refs`, `config`, `worktrees` come from the common directory. An alternative reference storage (`reftable`) exists in this version. | `GT` `Documentation/gitrepository-layout.adoc:19-33,96-143,262-283`; `Documentation/technical/reftable.adoc` (existence) |
| A-17.2 | ASF/W | The loose-object, pack and hash-function formats are specified (`gitformat-loose`, `gitformat-pack`, `Documentation/technical/hash-function-transition`); `git rev-parse HEAD` is defined by `gitrevisions`/`git-rev-parse`. The names of the documents were located; their detailed rules were **not** transcribed here. | `GT` `Documentation/{gitformat-loose,gitformat-pack,git-rev-parse,gitrevisions}.adoc`, `Documentation/technical/hash-function-transition.adoc` |
| A-17.3 | ASF/W | File attributes of the launcher are obtained with `stat`/`fstat`/`statx(2)` (mode and type, uid, gid, size, device and inode numbers, link count; `statx` adds mount id and attribute flags), the extended-attribute calls `getxattr`/`fgetxattr`/`listxattr`/`flistxattr` (`ERANGE` size protocol), and, for path-walk without symlink following, `openat2(2)` with `RESOLVE_NO_SYMLINKS`. File capabilities are stored in the extended attribute `security.capability`; POSIX ACLs in `system.posix_acl_access` (the accepted H-GRR.4/PF.9 already "list extended-attribute names"). | `MP` `man/man2/{stat,statx,getxattr,fgetxattr,listxattr,flistxattr,openat2}.2`, `man/man7/{capabilities,xattr}.7` |
| A-17.4 | DR | H-BSE.6 lists the keys path, sha256, size, owner, group, mode, `setid`, file capability, ACL, `(dev, ino)`, parents **plus carried record facts** (toolchain lock digest, build-root manifest digest, `builds`, `ha_variation`, `ic1_record_sha256`, `t_l10/11/12`, `xd_*`, agreed stream, `interpreter_version`, `d9_2`, `installation_source_record_sha256`); "which sub-keys are re-read and which are carried is not stated". H-BSE.3 lists `commit`, `manifest_version`, `reviewed_digest`, `expected_sha256_file_sha256`, `manifest_json_sha256`; "acquisition of the commit identity inside the tool not stated". | WP-2 inventory lines 307, 310 |
| A-17.5 | MD | Partition of the H-BSE.6 keys by the *kind* of fact, mechanically, from A-17.3/A-17.4 and D 4.3.2: **observable on the host file** — `path`, `sha256` (re-hash), `size`, `owner`, `group`, `mode`, `setid`, `file_capability`, `posix_acl`, `dev`, `ino`, `parents`; **facts about earlier builds and reviews** (digests of records, build outputs, verdicts, an agreed stream, `interpreter_version`) — not derivable from the installed file; they can only be *carried* from the accepted record or *re-read from the record files* named by the digests. This is a classification of the keys, **not** a decision of which are re-read (accepted text defers that, as the prompt requires). | D 4.3.2 `launcher`; A-17.3 |

**2. `PSC` candidates.**

| Id | Candidate | Prerequisites | Failure behavior (abstract) |
|---|---|---|---|
| P-17.1 | Resolve the repository commit by reading `HEAD`, following a symref to its loose ref file or to `packed-refs`, in the git directory (following a gitfile / `commondir` first). | repository directory readable; layout is files-ref-storage with the expected hash function | any other layout (`reftable`, unexpected hash length, unreadable ref), a detached/unborn HEAD that does not name a commit, or a mismatch with the pinned commit ⇒ `unavailable`/baseline mismatch |
| P-17.2 | Take the commit identity as a **carried** fact (the pinned commit in the accepted authority/A-2 record) and re-verify only the controlled-path digests (D 4.3.2 `repository`/H-BSE.7), never reading Git metadata. | the accepted record carries it | none beyond digest mismatch |
| P-17.3 | Re-read the launcher's observable attributes (A-17.5 first group) with the calls of A-17.3 on an open descriptor, and carry the second group from the accepted records. | file openable; xattr support on the filesystem | any call failure ⇒ `unavailable`; `ERANGE` handling per the calls' protocol |

**3. Compatibility with the boundary.** All three use file reads, system calls and
hashing in-process; none requires a child, a distribution program (`git`) or the
dynamic loader. P-17.1 re-implements a small part of Git's reference lookup and is
the candidate that most depends on Git-format stability (below).

**4. Limitations.** (a) Version/portability: the documents read are git `2.53.0`;
the installed git version is **not** recorded in any source examined, and the
reference backend is selectable (`files` or `reftable`), so a layout other than the
documented files backend must fail closed. (b) Worktree: a linked worktree's
`.git` is a gitfile and refs live in the common directory (A-17.1). (c) Packed
versus loose refs: a ref can be in either place; `packed-refs` can be rewritten
concurrently (racy read). (d) Replacement refs (`refs/replace/…`), shallow files
and alternates change object resolution and are outside a ref lookup. (e) The
accepted A0-02 check runs `git rev-parse HEAD` and an empty `git status
--porcelain=v1` locally in the *pass* path (D line 1012), a use of the `git` program
that the accepted text places outside the root-procedure set. (f) ACL and
capability reads depend on filesystem xattr support; D 4.3.2 requires `posix_acl` and
`file_capability` false. (g) TOCTOU: name-based path walks race with root; the accepted
text already limits claims to root-trusted state (R-10).

**5. Decision.** D-13: carry or re-read the commit identity (P-17.1 vs P-17.2), and
state, key by key, which H-BSE.6 keys are re-read (A-17.5 first group) and which
are carried (second group) — the prompt asks that this boundary not be decided
unless accepted text already does; **accepted text does not**, so it is left open.

**6. WP-4 left undesigned.** the ref/pack parser (if any), hash-function handling,
descriptor lifetimes, path-walk strategy, and how a carried fact is bound to the
accepted record.

**Status: partially supported** (facts located for Git format and file attributes;
the re-read/carried boundary is undecided by accepted text). Residuals: R-17.1
installed git version/ref storage unknown; R-17.2 the exact byte formats of
`packed-refs`, `HEAD` symrefs and loose refs were identified in the layout
document but not transcribed; R-17.3 `statx` mount-id and `STATX_ATTR_*` details not
needed for the accepted keys were not read.

### UF-18 — installed-package name/version/architecture records (H-BSE.4)

> Accepted statement: "Direct acquisition of installed-package name/version/architecture records (H-BSE.4)"

**1. Authoritative facts** (dpkg `1.23.7ubuntu1`; the installed dpkg version is not recorded).

| Id | Class/tier | Fact | Source |
|---|---|---|---|
| A-18.1 | ASF/W | `dpkg-query` is "a tool to show information about packages listed in the dpkg database"; `-l` without a pattern lists the packages in `%ADMINDIR%/status`; `-S` searches the packages' file lists, prints diversions with localized strings and "will not list extra files created by maintainer scripts, nor … alternatives"; machine parsing is "customary to set the locale to `C.UTF-8`". | `DP` `man/dpkg-query.pod` (Description, `-l`, `-S`) |
| A-18.2 | ASF/S | The status database is written whole and atomically: `writedb` creates an `atomic_file` with the `ATOMIC_FILE_BACKUP` flag (the previous file is kept as a backup), optionally syncs it and its directory, then commits (renames) it. | `DP` `lib/dpkg/dump.c:557-580` |
| A-18.3 | ASF/S | The *effective* database is the `status` file **plus** any pending journal files in the `updates/` directory: `modstatdb_open` → `cleanupdates()` parses `status`, then parses each file in `updates/` as an update and, when it holds write access, rewrites `status` and unlinks them; a reader that parses only `status` can miss an interrupted run's pending updates. `modstatdb_checkpoint` rewrites `status` and removes the process's own update files. | `DP` `lib/dpkg/dbmodify.c:88-140,361-395,403-431` |
| A-18.4 | ASF/S | dpkg serialises writers with a lock file and a front-end lock (`LOCKFILE`, `FRONTENDLOCKFILE`); read-only access takes none of them. | `DP` `lib/dpkg/dbmodify.c:165-186,360-370` |
| A-18.5 | ASF/W | Stanzas of `status` use the control-file syntax (`Package`, `Version`, `Architecture`, `Status`, `Multi-Arch`, … one field per line, stanzas separated by blank lines); the version string has its own ordering/format rules. | `DP` `man/deb-control.pod`, `man/deb822.pod`, `man/deb-version.pod` |
| A-18.6 | DR | H-BSE.4 lists the sorted `[package, version, architecture]` of the fixed HF-07 set (systemd, systemd-sysv, libsystemd0, libsystemd-shared, polkitd, libpolkit-gobject-1-0, libc6, libc-bin, the python3.12 family, coreutils, util-linux, sudo, dbus) **plus the package that owns `/usr/bin/pkcheck`** (HF-07 amendment, found with `dpkg -S`). | WP-2 inventory line 308; D lines 4437, 4453 |

**2. `PSC` candidates.**

| Id | Candidate | Prerequisites | Failure behavior (abstract) |
|---|---|---|---|
| P-18.1 | Parse `/var/lib/dpkg/status` for the fixed set (installed-state stanzas only) and report `[package, version, architecture]`. | readable file; a bounded stanza parser; a decision on pending `updates/` | unparsable/oversize ⇒ `unavailable`; presence of any file in `updates/` ⇒ `unavailable` (candidate rule) |
| P-18.2 | Resolve the package owning `/usr/bin/pkcheck` by scanning `/var/lib/dpkg/info/*.list` (path-to-package), applying diversions. | `info/` readable; a decision on merged-`/usr` aliases | ambiguous/zero owners ⇒ `unavailable` |
| P-18.3 | Carry the package set from the accepted H-1 record and compare only for equality with a cheap re-read of the version fields. | accepted record | mismatch ⇒ baseline mismatch (as accepted) |

**3. Compatibility with the boundary.** All are in-process file reads; none needs a
child or `dpkg-query`. Compatible in principle.

**4. Limitations.** (a) Consistency: `status` is replaced atomically (A-18.2) so a
single read is a consistent snapshot, but the effective state also includes
`updates/` (A-18.3); reading without that rule can be stale after an interrupted
operation, and a concurrent `apt`/`dpkg` run (writers hold locks the reader does
not take) can change the file between H-2 and the pass (the accepted drift rule,
D 4.6.3, already stops on a package-version change; `unattended-upgrades` is
active on the host, R2 HF-17). (b) `dpkg -S` equivalence: the `.list` files list
only package-shipped paths, not maintainer-script files or alternatives (A-18.1);
diversions and the merged-`/usr` layout (`/bin` → `/usr/bin`) must be handled to
reproduce the same owner. (c) Output locale: `dpkg-query` text is localized unless
`C.UTF-8`; the baseline stores the *package* record, not the text. (d) Version
binding: dpkg `1.23.7ubuntu1` is the archive release read; the installed version
and the on-disk database format version for it are unrecorded. (e) Multi-arch:
`Architecture` can be `all`, `amd64` or a foreign architecture and a package name
can occur more than once.

**5. Decision.** D-14: file parse (P-18.1/P-18.2) versus carried record (P-18.3),
and the rule for pending `updates/` entries.

**6. WP-4 left undesigned.** the stanza parser and its bounds, the sort, handling
of `Multi-Arch`, diversions and alias paths, and the size limits.

**Status: supported as to facts; mechanism is `PSC` (not closed).** Residuals:
R-18.1 installed dpkg version unknown; R-18.2 the on-disk format of
`/var/lib/dpkg/info/*.list` and of `updates/` entries was identified from code,
not transcribed.

## 5. Cancellation and completion reconciliation — all seven interfaces

The table states, per interface, only what §3 established and keeps the three
layers apart: **S/W** facts, the **proposed mapping** (`PSC`, tier M) and what is
left to later packages. It decides neither Q6-6 nor Q6-7 and does not extend
SN-10/A-I-16 to any non-child interaction (`DR` rows are quoted from WP-2 §8.1).

| Interface (sites) | Wire call and completion | Cancelling/abandoning the client wait | What the server keeps doing | How the effect is observed | Proposed mapping (PSC) | Not decided here |
|---|---|---|---|---|---|---|
| **DI-1** read (23) | `Properties.Get`/`GetAll` → one METHOD_RETURN (A-14.1); no job | the spec has no cancel (A-05.1); a timeout/close is just a dropped reply | nothing is started or stopped; a read of an unloaded name **loads a stub** (A-02.3, A-02.7) | the reply itself | cancelled/interrupted read ⇒ `error`, never a value (`PO3-1.4`/`PO3-X3`, unchanged); no unknown-effect question (no mutation except the in-memory stub) | transport (P-01.1); mapping of ERROR names (P-04.1) |
| **DI-2** create holder (1: SA-1) | `StartTransientUnit` → job path `o` (A-06.1); completion later by `JobRemoved` or state reads (A-05.9 … A-05.11) | the same; **the reply is not completion** (A-05.5) | the job and the transient unit persist (A-05.4); a failure after the unit is made transient leaves a jobless transient unit (A-05.12); a name that is already loaded ⇒ `UnitExists`, nothing created (A-02.6, A-04.2) | `ActiveState`/`Job`/`Result`/`InvocationID` of the holder (UF-03); `JobRemoved` if subscribed (A-05.10) | `UnitExists` ⇒ `refused(exists)` (`PO3-2.1`); timeout, close, unreadable reply, other ERROR ⇒ `error`, **effect not confirmed, never "not created", no silent retry** (`PO3-2.4`, `PO3-X2`; class `PO3`, DI-2 is not named by SN-10) | meaning of `effect: "unknown"` for a non-child call (Q6-6 incl. whether DI-2 is inside it); the completion-observation design (P-05.3); deadline enforcement (Q4-7) |
| **DI-3** create backstop timer+service (1: RT-2 AK-1) | one `StartTransientUnit` carrying the timer and the aux service (A-08.1) → job path of the timer | same | as DI-2, plus: the timer unit and/or its auxiliary service may exist in memory without a queued job if the call fails after step (c) of A-05.12; stopping the timer later does not stop the service (A-09.6) | `ActiveState` of `<id>-backstop.timer`, `Triggers`/`Unit` link (A-08.3), unit existence by `LoadState` | as DI-2; additionally, per `DR` SN-10/A-I-16 (child form) `effect: "unknown"` after `error`, interruption or indeterminate completion, and CL's by-name disarm keyed to `backstop-intent` — **mapping to this non-child call is Q6-6** | Q6-6; BS-RM citation obligation (OH-S2b, carried, not owned here) |
| **DI-4** disarm (3: BS-2, BS-3, BS-4) | `StopUnit(timer, mode)` → job path; `done` also for an already-inactive loaded timer (A-09.4); `NoSuchUnit` for a not-loaded one (A-09.3) | same | the stop job runs to its result; stopping the timer leaves the service alone | `ActiveState`/`LoadState` of the timer; `JobRemoved` | `NoSuchUnit` ⇒ a refusal-or-benign outcome per **D-9** (not an accepted fact); timeout/close/unreadable ⇒ `error`, never "stopped"/"not stopped" (`PO3-4.3`, `PO3-X2`); BS-2/BS-3 `DR` SN-10 (child form) → mapping Q6-6; **BS-4: no SN-10 text exists; Q6-7 is untouched** | Q6-6 (BS-2, BS-3); Q6-7 (BS-4) |
| **DI-5** Polkit decision (6) | `CheckAuthorization` → `(bba{ss})` (A-10.2); with flags `0` the whole decision completes inside the call (A-10.8) | a client that stops waiting changes no polkitd state; `CancelCheckAuthorization` is moot for a non-interactive check (A-10.7, A-10.8); libpolkit adds a cancellation id only when given a cancellable (A-10.9) | nothing outlives the call | the reply fields only | fields ⇒ `authorized`/`not-authorized`/`error` per P-11.1; any deadline, abandon or unparsable reply ⇒ `error` (H-PK2.5, `DR`) | deadline enforcement (Q4-7); the choice of request shape (P-10.1) |
| **DI-6** subject (6) | not a bus call: a local process whose pid, start time and uid are read from `/proc` (H-PROC.5) and put in DI-5's `subject` (A-10.5, A-10.6, A-10.10, A-10.12, A-12.1); the accepted H-PROC.5 reads all three, so the proposed `pkcheck`-equivalent shape supplies `uid` although the general PID/start-time form does not require it (A-10.6) | no client wait of its own (contract §3.0 stands); cancellation belongs to the enclosing DI-5 decision and the later cleanup under SN (`DR` H-PROC.1, H-PK2.7) | polkitd verifies the supplied start time against `/proc` at decision time and answers a mismatch with an ERROR (A-13.1); a root caller's supplied uid is trusted (A-13.2); polkit's own text calls the PID/start-time form "known broken" without pidfds (A-13.4) | the DI-5 result | an unreadable `/proc` field, a mismatch ERROR or a vanished process ⇒ `error` (H-PROC.5, H-PK2.5) | Q4-1/Q4-8 (creation, cleanup mechanics); Q6-4; whether to adopt the pidfd form (D-5) |
| **DI-S** stop capture unit (1: SA-2) | `StopUnit(rp11-capture-pass-a.service, mode)`; root caller ⇒ no Polkit (A-09.5) | same | the stop job runs to its result | `ActiveState`/`Result`/`InvocationID` of the capture unit; `JobRemoved` | as DI-4 (`PO3-7.1`, `PO3-7.2`): `error`, never proof the unit was or was not stopped; class `PO3` (DI-S is not named by SN-10) | Q6-6 (whether DI-S is inside SN-10); Q4-7, Q4-11 |

**Common statement (unchanged and reinforced).** For DI-2, DI-3, DI-4 and DI-S a
cancelled client wait, a client-side timeout, a lost connection or an unreadable
reply is **not proof that a queued job stopped and not proof that the mutating
request had no effect** (A-05.4, A-05.6, A-05.12); nothing in the pinned sources
undoes a request because its reply could not be delivered; no silent retry follows.
The only server-side cancellation is an explicit `CancelJob`/`Job.Cancel`, which by
the manual "will not have any effect on jobs whose execution has already begun".

## 6. Q3 readiness table (does not close any Q3 question)

"Could close after acceptance" means: every *fact* the question needs is now an
`ASF`/`MD`/`DR` in this record **and** only the listed *decisions* (Appendix B)
would remain for the contract-integration step. Nothing here closes a question.

| Q3 | Facts now supported (record ids) | Could close after acceptance, subject to decisions | Remains blocked / not inferable |
|---|---|---|---|
| Q3-1 DI-1 | name→object A-02.1-7; types and print text A-03.1-7; unloaded and own-start-pre reads A-02.6/7 (R2 carried); transport A-01.x; errors A-04.x; no job A-05 | yes, after **D-1** (transport), **D-3** (error mapping), **D-7** (typed vs printed baseline text is Q6-2, separate) | property list file R-03.1; installed broker R-01.1 |
| Q3-2 DI-2 | signature/mode A-06.x; properties and exec structure A-07.x; completion/cancel/abandon A-05.x; refusal `UnitExists` A-04.2 | yes, after **D-1**, **D-3**, **D-4** (completion-observation design), **D-8** (`effect` wording for a non-child call is Q6-6) | Q6-6; Q4-7 enforcement |
| Q3-3 DI-3 | as Q3-2 plus timer/aux A-08.x; stop-leaves-service A-09.6 | yes, after the same decisions and **D-10** (resolve RT2.AK1.2 vs D R2 (f) on `TimeoutStartSec`, O-3) | Q6-6; BS-RM citation (OH-S2b) |
| Q3-4 DI-4 | `StopUnit` A-09.x; timer behavior A-09.6 | yes, after **D-1**, **D-3**, **D-9** (not-loaded/already-inactive outcome) | Q6-6 (BS-2, BS-3); **Q6-7 (BS-4) stays open** |
| Q3-5 DI-5 | method, signature, flags, details, cancellation, errors A-10.1-A-10.12; mapping facts A-11.x | yes, after **D-2** (request shape), **D-3**, **D-6** (field→outcome mapping) | Q4-7 (deadline); R-10.1 built-in pidfd |
| Q3-6 DI-6→DI-5 | encoding A-10.5, A-10.6, A-10.10, A-10.12, A-12.x (three shapes kept apart: PID/start-time with optional `uid`; pidfd with required `uid`; `pkcheck`-equivalent with all three); polkitd treatment A-13.x | yes, after **D-5** (start-time form vs pidfd form) | Q4-1/Q4-8 mechanics; Q6-4; R-13.x |
| Q3-7 DI-S | `StopUnit` + root no-Polkit A-09.5, A-09.7 | yes, after **D-1**, **D-3**, **D-9** | Q6-6 (is DI-S inside SN-10?); Q4-7/Q4-11 |
| Q3-9 baseline reads | `Get` reaches hidden/explicit A-14.x; types/print rules A-03.x | **partially**: facts for the read path closed; **blocked on R-03.1** (the version-bound property list is not in evidence) and **D-7** | Q6-2 (byte equivalence of the baseline) |
| Q3-11 baseline acquisition | direct sources and formats A-15 … A-18 | **no**: needs decisions **D-11 … D-14** (per-UF mechanism and boundary) before any acquisition is more than `unavailable`; the contract's fail-closed record `PO3-11.1` stays in force and no acquisition mechanism is selected | Q6-3; installed versions of git/dpkg/NSS config unknown |

## 7. Residual unsupported facts and their owners

| Residual | Exact statement | Owner |
|---|---|---|
| R-01.1 | installed message-bus implementation, version and active policy (HF-07 `dbus`) not examined | a later, separately gated host-observation slice (not authorized here); WP-4 must not assume |
| R-01.2 | kernel credential-passing semantics for the initial NUL byte not researched | WP-3 follow-up (documentation) or WP-4 |
| R-02.1 | garbage-collection timing of loaded stubs | not needed by any accepted use; no owner required |
| R-03.1 | the version-bound baseline property list (D 4.3.3) is a repository artifact outside the required reading | WP-6 (Q6-2) with Peter; WP-3 may cite it once supplied |
| R-03.2 | `FORMAT_TIMESTAMP_STYLE`/locale details not re-derived | WP-6 (Q6-2) |
| R-04.1, R-04.2 | error-name coverage limited to the paths used; bus-daemon errors not enumerated | WP-4 (Q4-11) |
| R-05.1 | message-bus behavior on client disconnect with a pending service reply | later host-observation slice; WP-4 design must treat the reply as lost |
| R-05.2 | all behavior is source-derived; no execution | WP-5 (proof/evidence method) |
| R-05.3 | `effect: "unknown"` meaning for non-child calls | **Q6-6 (WP-6)** — not answered |
| R-06.1, R-06.2, R-07.1 … R-07.3 | per-type setter errors; unused job modes; sandbox properties | WP-4 (Q4-11) as needed |
| R-08.1 | D R2 (f) vs RT2.AK1.2 on `TimeoutStartSec` | maintainer decision D-10 |
| R-09.1, R-09.2 | stop during start-pre; `unit_stop` run time | accepted PO-21 (u) (carried); WP-4 (Q4-7) |
| R-10.1, R-13.1 | whether the installed polkitd was built with `HAVE_PIDFD_OPEN` | later host-observation slice or a package-file inspection step |
| R-10.2, R-13.2 | GDBus disconnect behavior; `pidfd_open(2)` semantics beyond polkit's use | WP-3 follow-up (documentation) |
| R-11.1 | a D-Bus counterpart for the 65,536-byte volume cap | WP-4 (Q4-5/Q4-11) |
| R-12.1, R-12.2 | `USER_HZ`/`_SC_CLK_TCK` value; polkit's "millisecond" comment | none needed (encoding is unaffected) |
| R-13.3 | polkitd's error strings are not a stable contract | WP-4 (treat as `error` kind only) |
| R-14.1 | R2 Appendix C.1 "27" vs 28 entries | editorial correction of an accepted record (maintainer) |
| R-15.1, R-15.2 | host personality/namespace; exact `UTS_MACHINE` | later host-observation slice |
| R-16.1, R-16.2 | host `nsswitch.conf`/`libnss-systemd`; `userdb` mechanism | later host-observation slice; WP-6 (Q6-3) |
| R-17.1 … R-17.3 | installed git version/ref storage; ref-file byte formats; `statx` details | later host-observation slice; WP-4 |
| R-18.1, R-18.2 | installed dpkg version; `info/*.list`/`updates/` byte formats | later host-observation slice; WP-4 |
| R-M.1 | the Ubuntu kernel delta `linux` `7.0.0-31.31` is not authenticated through the current signed `Sources` indexes (the version is superseded there); A-12.3 and A-15.2 rest on the diff's equality with R2 Appendix D (§2.4) | maintainer: accept the R2 cross-reference or direct another authentication source; no new fact depends on it |

## 8. Answers to the independent review questions

1. **Are the exact pinned Ubuntu sources authenticated and are distro patches
   accounted for?** Yes for authenticity of the *archive* sources (R1: repeated
   without any installed keyring): the signed `InRelease` (Ubuntu Archive Automatic
   Signing Key 2018, fingerprint `F6ECB3762474EDA9D21B7022871920D1991BC93C` pinned by
   Peter and verified against the keyring downloaded into the research directory,
   §2.1) vouches for `Sources`, which list exactly the six
   files; all six sizes and SHA-256 values match (§2.1); both orig tarballs are
   byte-identical to the upstream tags. The uploader signatures on the `.dsc` files
   were not verified (key unavailable) and are not relied on. Patches: the full
   series was applied (systemd 40, polkit 2; also glibc 103 and man-pages 13, R1) and each patch was classified by the
   files it touches (§2.7, Appendix E); none changes a function cited for a contract fact.
2. **Does every `ASF` state only what its cited primary source establishes?**
   Each `ASF` row cites a file and line range (or a specification section/manual
   page) of a source bound in §2; statements that rest on an *absence* in the cited
   bodies are labelled as such (A-05.6, A-05.12), derived statements are `MD` with
   the derivation, and reference-client behavior is tier `R`. Two places where the
   manual and the source disagree are reported, not blended (Appendix C).
3. **Does the record distinguish server behavior, wire/API contract, proposed
   outcome mapping and implementation choice?** Yes: every row carries tier
   `S`/`W`/`R`; proposed mappings are `PSC` tier `M` and appear only under
   "`PSC`" headings and in §5 column 6; no tier `I` row exists.
4. **Are job completion and client-wait/job cancellation semantics complete for
   DI-2, DI-3, DI-4 and DI-S without deciding Q6-6 or Q6-7?** The four sub-facts
   of the expanded `UF-05` are each answered with exact source (A-05.1 … A-05.13),
   the mapping is `PSC` only, §5 states per interface what stays undecided, and
   Q6-6/Q6-7 are named as not answered. The residuals R-05.1 … R-05.3 are listed.
5. **Are DI-5 and DI-6 subject/cancellation facts complete without conflation?**
   DI-5 (the bus call: A-10.x, A-11.x) and DI-6 (the local subject and what polkitd
   does with it: A-12.x, A-13.x) are separate blocks; §5 keeps DI-6's "no client
   wait of its own" statement and routes cancellation to the enclosing DI-5
   decision and the later cleanup, as contract §3.0 requires. The pidfd/start-time
   choice and the process-creation mechanics are left to decisions D-5 and
   Q4-1/Q4-8.
6. **Are every `PSC` and every residual `UF` classified honestly?** Appendix A
   lists every `PSC` with its decision; §7 lists every residual with an owner; the
   statuses (`supported`, `partially supported`) are stated per item: `UF-03`,
   `UF-05` and `UF-17` are *partially supported*; `UF-15` … `UF-18` are supported as
   to facts with the mechanism left as `PSC`; no `UF` is called closed.
7. **Do the `UF-15` … `UF-18` proposals stay above WP-4 mechanics and preserve the
   accepted boundary?** Each proposal states prerequisites and failure behavior
   abstractly, names the later decision and lists the undesigned WP-4 details; none
   chooses a language, library, parser, syscall sequence or buffer size; `P-16.2`
   is explicitly flagged as incompatible with the boundary unless the configured
   NSS sources are `files`. `UF-17`'s re-read/carried split is left undecided
   because accepted text does not decide it.
8. **Is the Q3 readiness assessment complete, internally consistent and safe for a
   later contract-integration decision?** §6 covers exactly the nine Q3
   identifiers, names the decisions each depends on (Appendix B), closes none,
   and keeps Q3-9 and Q3-11 not closable on the present evidence.

## 9. Recommendation for Peter (separate from the evidence above)

1. **Do not integrate yet; obtain Codex's independent review of this record
   first.** Then decide acceptance of the record as the evidence basis for a
   *contract-integration* step. Acceptance would not by itself close any Q3 item.
2. **The interface contract can probably be completed for Q3-1 … Q3-7 once the
   eight decisions D-1 … D-6, D-9 and D-10 are recorded** (Appendix B: transport,
   request shape for Polkit, error mapping, completion-observation design, subject
   form, field→outcome mapping, `StopUnit` outcome for not-loaded/already-inactive,
   the `TimeoutStartSec` discrepancy); D-7 and D-8 belong to Q6-2 and Q6-6 and are
   not made here. None of the eight needs host access. They are better made in one
   reviewed integration record than inside WP-4.
3. **Treat the polkit upstream statement about PID/start-time subjects as a design
   risk to be decided, not an implementation detail** (A-13.4, D-5). If the
   pidfd form is preferred, accepted text H-PROC.5/PO-SN (d) must be amended
   before WP-4 uses it.
4. **Q3-9 and Q3-11 need your decisions on scope before more research is useful.**
   Q3-9 is blocked by the version-bound property list (R-03.1) and by Q6-2; Q3-11
   by per-item mechanism decisions (D-11 … D-14) and by installed-version facts
   that only a separately gated host observation can supply. It would be
   reasonable to keep Q3-11's fail-closed record in force and decide whether
   LIT-FULL remains attractive given Q3-11 and Q6-3 before spending more on it.
5. **Correct the two small accepted-record inconsistencies** (R2 Appendix C.1
   count label; the holder `LoadState` row, Appendix C O-1) by dated erratum when
   convenient; neither blocks WP-3.
6. **Q6-6 and Q6-7 remain the real gate for DI-2/3/4/S behavior.** Every
   mapping above is conditional on them. This record gives the facts they need
   (A-05.x) but cannot answer them.

## Appendix A — `PSC` register (none accepted, none selected)

| Id | UF | Proposal (summary) | Decision it requires |
|---|---|---|---|
| P-01.1 | 01 | transports: system bus for all, or system bus for DI-5 + private socket for manager calls when root | D-1 |
| P-04.1, P-04.2 | 04 | ERROR/transport/timeout ⇒ `refused`/`error` mapping; `NoSuchUnit` on stop | D-3, D-9 |
| P-05.1 … P-05.4 | 05 | abandon/timeout/disconnect are `error` + effect not confirmed; refusal set; completion observation O-A/O-B/O-C; behavior when no signal arrives | D-4, D-8 (Q6-6) |
| P-09.1, P-09.2 | 09 | outcome vocabulary for `StopUnit` on not-loaded and already-inactive units | D-9 |
| P-10.1 | 10 | DI-5 request shape: `pkcheck`-equivalent (`pid`, `start-time`, `uid`) vs pidfd (`pidfd`, `uid`); the decoder's PID/start-time-without-`uid` acceptance is a fact (A-10.6), not a candidate | D-2, D-5 |
| P-11.1 | 11 | result fields ⇒ `authorized`/`not-authorized`/`error` | D-6 |
| P-13.1 | 13 | expected polkitd behavior for a live unreaped child; pidfd form as option | D-5 |
| P-15.1 … P-15.3 | 15 | `uname` vs `/proc/sys/kernel`, machine-id read | D-11 |
| P-16.1 … P-16.3 | 16 | files parse, library NSS, files-only declared fact | D-12 |
| P-17.1 … P-17.3 | 17 | ref lookup, carried commit, attribute reads | D-13 |
| P-18.1 … P-18.3 | 18 | status parse, `.list` owner lookup, carried record | D-14 |

## Appendix B — decisions that would remain (Peter)

| Id | Decision |
|---|---|
| D-1 | Transport(s) for the manager interfaces (P-01.1). |
| D-2 | DI-5 request shape (P-10.1). |
| D-3 | ERROR-name and transport-failure mapping (P-04.1). |
| D-4 | Completion-observation design for DI-2/3/4/S (P-05.3, P-05.4). |
| D-5 | Subject form: PID + start time (as H-PROC.5) or pidfd (amendment) (A-13.4). |
| D-6 | Result-field mapping (P-11.1). |
| D-7 | Typed-versus-printed baseline text (Q6-2; not decided here). |
| D-8 | Meaning of `effect: "unknown"` for non-child calls (Q6-6; **not decided here**). |
| D-9 | Outcome for `StopUnit` on a not-loaded/already-inactive unit (P-09.1). |
| D-10 | Resolve the `TimeoutStartSec` discrepancy between D R2 (f) and `RT2.AK1.2` (O-3). |
| D-11 | UF-15: source for the UTS-derived keys and the rule for a malformed `/etc/machine-id`. |
| D-12 | UF-16: files-only versus library NSS, and whether "NSS" in `H-BSE.2` is preserved literally (also Q6-3). |
| D-13 | UF-17: carry or re-read the commit identity, and the key-by-key re-read/carried split of `H-BSE.6`. |
| D-14 | UF-18: status-file parse versus carried record, and the rule for pending `updates/` entries. |

## Appendix C — observations about accepted texts and sources (reported, not decided)

* **O-1.** WP-2 row `RT2.AM0.5` has the holder, at AM-0, read `LoadState` of
  `⟨activation_id⟩.service`, the backstop timer and the backstop service and
  requires each to be `not-found`. The holder is the running main process of
  `⟨activation_id⟩.service` (created by SA-1), so its own `LoadState` cannot be
  `not-found` at AM-0; D R2 (d) places the three-unit `LoadState` condition in
  the executor's AP-0 (before AP-2). The accepted AM-0 text is ambiguous here
  (compare Q6-7, which is not answered). The record reports it for the reviewer.
* **O-2.** The systemd manual of this version disagrees with its source in three
  places: `aux` of `StartTransientUnit` ("unused", but processed: A-08.1); the mode
  list for `StartUnit` (five documented, ten in the table: A-06.2); the
  `JobRemoved` result list (six documented, thirteen in the table: A-05.9).
  The source governs this record.
* **O-3.** D R2 (f) lists `--property=TimeoutStartSec=⟨S⟩` in the backstop literal;
  WP-2 row `RT2.AK1.2` (after BS-RM) says "no `TimeoutStartSec=`". Both are
  "accepted text"; the record follows neither and flags D-10.
* **O-4.** R2 Appendix C.1 labels the hidden Unit/Service group "(27)" but lists 28
  entries; the independent extraction gives 28 (A-14.3).
* **O-5.** The Polkit interface XML spells its object path `PoliycKit1` in prose,
  says the `pidfd` key has type `int32`, and lists `uid` in **both** `unix-process`
  forms; the code and the introspection data use `/org/freedesktop/PolicyKit1/Authority`,
  the D-Bus handle type `h`, and make `uid` optional in the PID/start-time form
  (A-10.1, A-10.5, A-10.6). The decoder governs this record.
* **O-6.** The accepted contract says polkitd's treatment of start time and uid
  is unsupported (UF-13); the source shows the supplied uid of a trusted caller is
  taken as the identity for policy (A-13.2). This makes the DI-6 uid read of
  H-PROC.5 security-relevant to the decision, which is a fact for D-5, not a defect.

## Appendix E — citation index and locators (R1)

### E.1 Every line-range citation

Method: the table is generated mechanically from the final text of this record. For
each `` `path:lines` `` token the script resolves `path` in the extracted and patched
trees of §2, checks that the lines exist, finds the enclosing C definition (or XML
element) at the first cited line, quotes the first cited line as a content anchor
(truncated to 60 characters; “”-quoted) and classifies the lines by comparing the
unpatched and patched file (for `GL`, in unpatched numbering) or the Ubuntu kernel
diff. "Record id" is the fact row or heading in which the citation stands. No
citation is out of bounds and none is unresolved.

Generated mechanically from this record's 220 line-range citations over 68 distinct files (see Appendix E method).

| # | Record id | Src | Archive-relative file | Lines | Enclosing symbol / element | Content anchor (first cited line) | Provenance of the cited lines |
|---:|---|---|---|---|---|---|---|
| CI-001 | 1. Scope, | SD | `systemd-259.5/man/org.freedesktop.systemd1.xml` | 1275-1276 | n/a (non-C text) | “<para><function>LoadUnit()</function> is similar to <functio” | upstream text; file not touched by the Ubuntu patch series |
| CI-002 | A-01.2 | SD | `systemd-259.5/src/libsystemd/sd-bus/bus-internal.h` | 16 | file scope | “#define DEFAULT_SYSTEM_BUS_ADDRESS "unix:path=/run/dbus/syst” | upstream text; file not touched by the Ubuntu patch series |
| CI-003 | A-01.2 | SD | `systemd-259.5/src/libsystemd/sd-bus/sd-bus.c` | 1311-1325 | bus_set_address_system | “int bus_set_address_system(sd_bus *b) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-004 | A-01.2 | SD | `systemd-259.5/src/shared/bus-util.c` | 758-760 | bus_open_system_watch_bind_with_description | “e = secure_getenv("DBUS_SYSTEM_BUS_ADDRESS");” | upstream text; file not touched by the Ubuntu patch series |
| CI-005 | A-01.6 | SD | `systemd-259.5/src/core/org.freedesktop.systemd1.conf` | 16-31, 49, 113, 203-287 | n/a (non-C text) | “<policy user="root">”; “<!-- Completely open to anyone: org.freedesktop.systemd1.Man”; “send_member="Subscribe"/>”; “<!-- Managed via polkit or other criteria: org.freedesktop.s” | upstream text; file not touched by the Ubuntu patch series |
| CI-006 | A-01.6 | PK | `polkit-127/data/org.freedesktop.PolicyKit1.conf.in` | 7-13 | n/a (non-C text) | “<policy user="@polkitd_user@">” | upstream text; file not touched by the Ubuntu patch series |
| CI-007 | A-01.7 | SD | `systemd-259.5/src/core/dbus.c` | 895-957 | bus_init_private | “int bus_init_private(Manager *m) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-008 | A-01.7 | SD | `systemd-259.5/src/shared/bus-util.c` | 225-240 | bus_check_peercred | “fd = sd_bus_get_fd(bus);” | upstream text; file not touched by the Ubuntu patch series |
| CI-009 | A-01.8 | SD | `systemd-259.5/src/shared/bus-util.c` | 766 | bus_open_system_watch_bind_with_description | “r = sd_bus_set_bus_client(bus, true);” | upstream text; file not touched by the Ubuntu patch series |
| CI-010 | A-01.8 | SD | `systemd-259.5/src/shared/bus-util.c` | 242-266, 510-552, 758-775 | bus_connect_system_systemd; bus_connect_transport_systemd; bus_open_system_watch_bind_with_description | “int bus_connect_system_systemd(sd_bus **ret) {”; “int bus_connect_transport_systemd(”; “e = secure_getenv("DBUS_SYSTEM_BUS_ADDRESS");” | upstream text; file not touched by the Ubuntu patch series |
| CI-011 | A-01.9 | SD | `systemd-259.5/src/core/dbus.c` | 1092-1121 | bus_foreach_bus | “int bus_foreach_bus(” | upstream text; file not touched by the Ubuntu patch series |
| CI-012 | A-01.9 | SD | `systemd-259.5/src/shared/bus-polkit.c` | 82-88 | bus_message_new_polkit_auth_call_for_bus | “r = sd_bus_message_new_method_call(” | upstream text; file not touched by the Ubuntu patch series |
| CI-013 | A-02.1 | SD | `systemd-259.5/src/basic/unit-def.c` | 11-21 | unit_dbus_path_from_name | “char* unit_dbus_path_from_name(const char *name) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-014 | A-02.1 | SD | `systemd-259.5/src/basic/bus-label.c` | 10-43 | bus_label_escape | “char* bus_label_escape(const char *s) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-015 | A-02.1 | SD | `systemd-259.5/src/basic/hexdecoct.c` | 35-38 | hexchar | “char hexchar(int x) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-016 | A-02.2 | SD | `systemd-259.5/src/systemctl/systemctl-show.c` | 2582-2589 | verb_show | “STRV_FOREACH(name, names) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-017 | A-02.3 | SD | `systemd-259.5/src/core/dbus.c` | 225-257, 259-268 | find_unit; bus_unit_find | “static int find_unit(Manager *m, sd_bus *bus, const char *pa”; “static int bus_unit_find(sd_bus *bus, const char *path, cons” | upstream text; file not touched by the Ubuntu patch series |
| CI-018 | A-02.3 | SD | `systemd-259.5/src/core/manager.c` | 3335-3375 | manager_load_unit_from_dbus_path | “int manager_load_unit_from_dbus_path(Manager *m, const char ” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-019 | A-02.4 | SD | `systemd-259.5/src/core/dbus.c` | 248-253 | find_unit | “r = manager_load_unit_from_dbus_path(m, path, reterr_error, ” | upstream text; file not touched by the Ubuntu patch series |
| CI-020 | A-02.4 | SD | `systemd-259.5/src/libsystemd/sd-bus/bus-objects.c` | 593-601 | property_get_set_callbacks_run | “r = vtable_property_get_userdata(bus, m->path, c, &u, &error” | upstream text; file not touched by the Ubuntu patch series |
| CI-021 | A-02.4 | SD | `systemd-259.5/src/libsystemd/sd-bus/sd-bus.c` | 3071-3085 | process_running | “if (m->header->type == SD_BUS_MESSAGE_METHOD_CALL) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-022 | A-02.5 | SD | `systemd-259.5/src/core/dbus-manager.c` | 487-529, 549-568, 726-745, 3018-3047 | bus_get_unit_by_name; method_get_unit; method_load_unit; bus_manager_vtable | “static int bus_get_unit_by_name(Manager *m, sd_bus_message *”; “static int method_get_unit(sd_bus_message *message, void *us”; “static int method_load_unit(sd_bus_message *message, void *u”; “SD_BUS_METHOD_WITH_ARGS("GetUnit",” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-023 | A-02.5 | SD | `systemd-259.5/man/org.freedesktop.systemd1.xml` | 1275-1276 | n/a (non-C text) | “<para><function>LoadUnit()</function> is similar to <functio” | upstream text; file not touched by the Ubuntu patch series |
| CI-024 | A-02.6 | SD | `systemd-259.5/src/basic/unit-def.c` | 89-97 | unit_dbus_interface_from_name | “static const char* const unit_load_state_table[_UNIT_LOAD_ST” | upstream text; file not touched by the Ubuntu patch series |
| CI-025 | A-02.6 | SD | `systemd-259.5/src/core/unit.c` | 5248-5265 | unit_is_pristine | “bool unit_is_pristine(Unit *u) {” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-026 | A-02.6 | SD | `systemd-259.5/src/core/dbus-manager.c` | 1054-1056 | transient_unit_from_message | “if (!unit_is_pristine(u))” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-027 | table:ActiveState | SD | `systemd-259.5/src/basic/unit-def.c` | 102-111 | unit_dbus_interface_from_name | “static const char* const unit_active_state_table[_UNIT_ACTIV” | upstream text; file not touched by the Ubuntu patch series |
| CI-028 | table:ActiveState | SD | `systemd-259.5/src/shared/bus-print-properties.c` | 75-92 | bus_print_property | “case SD_BUS_TYPE_STRING: {” | upstream text; file not touched by the Ubuntu patch series |
| CI-029 | table:InvocationID | SD | `systemd-259.5/src/shared/bus-get-properties.c` | 64-79 | bus_property_get_id128 | “int bus_property_get_id128(” | upstream text; file not touched by the Ubuntu patch series |
| CI-030 | table:InvocationID | SD | `systemd-259.5/src/core/dbus-unit.c` | 992 | bus_unit_vtable | “SD_BUS_PROPERTY("InvocationID", "ay", bus_property_get_id128” | upstream text; file not touched by the Ubuntu patch series |
| CI-031 | table:InvocationID | SD | `systemd-259.5/src/shared/bus-print-properties.c` | 292-312 | bus_print_property | “} else if (streq(contents, "y")) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-032 | table:InactiveEnterTimestampMonotonic | SD | `systemd-259.5/src/shared/bus-print-properties.c` | 115-125, 189 | bus_print_property | “if (bus_property_is_timestamp(name))”; “bus_print_property_valuef(name, expected_value, flags, "%"PR” | upstream text; file not touched by the Ubuntu patch series |
| CI-033 | table:Job | SD | `systemd-259.5/src/core/dbus-unit.c` | 254-277, 958 | property_get_job; bus_unit_vtable | “static int property_get_job(”; “SD_BUS_PROPERTY("Job", "(uo)", property_get_job, offsetof(Un” | upstream text; file not touched by the Ubuntu patch series |
| CI-034 | table:Job | SD | `systemd-259.5/src/systemctl/systemctl-show.c` | 1232-1244 | print_property | “if (contents[0] == SD_BUS_TYPE_UINT32 && streq(name, "Job"))” | upstream text; file not touched by the Ubuntu patch series |
| CI-035 | table:Result | SD | `systemd-259.5/src/core/service.c` | 5875-5887 | service_freezer_action | “static const char* const service_result_table[_SERVICE_RESUL” | upstream text; file not touched by the Ubuntu patch series |
| CI-036 | table:TimeoutStartUSec | SD | `systemd-259.5/src/shared/bus-print-properties.c` | 124-125 | bus_print_property | “else if (strstr(name, "USec"))” | upstream text; file not touched by the Ubuntu patch series |
| CI-037 | table:TimeoutStartUSec | SD | `systemd-259.5/src/basic/time-util.c` | 520-624 | format_timespan | “char* format_timespan(char *buf, size_t l, usec_t t, usec_t ” | upstream text; file not touched by the Ubuntu patch series |
| CI-038 | A-03.3 | SD | `systemd-259.5/src/shared/bus-print-properties.c` | 61-341 | bus_print_property | “static int bus_print_property(const char *name, const char *” | upstream text; file not touched by the Ubuntu patch series |
| CI-039 | A-03.4 | SD | `systemd-259.5/src/systemctl/systemctl-show.c` | 1173-1300, 1515-1571 | print_property | “static int print_property(const char *name, const char *expe”; “} else if (contents[0] == SD_BUS_TYPE_STRUCT_BEGIN && starts” | upstream text; file not touched by the Ubuntu patch series |
| CI-040 | A-03.6 | SD | `systemd-259.5/src/basic/time-util.c` | 520-624 | format_timespan | “char* format_timespan(char *buf, size_t l, usec_t t, usec_t ” | upstream text; file not touched by the Ubuntu patch series |
| CI-041 | A-03.6 | SD | `systemd-259.5/src/basic/time-util.h` | 53, 55, 62, 148 | file scope; format_timestamp | “#define USEC_PER_MONTH ((usec_t) (2629800ULL*USEC_PER_SEC))”; “#define USEC_PER_YEAR ((usec_t) (31557600ULL*USEC_PER_SEC))”; “#define FORMAT_TIMESPAN_MAX 64U”; “#define FORMAT_TIMESPAN(t, accuracy) format_timespan((char[F” | upstream text; file not touched by the Ubuntu patch series |
| CI-042 | A-03.7 | SD | `systemd-259.5/src/basic/escape.c` | 552-592 | shell_maybe_quote | “char* shell_maybe_quote(const char *s, ShellEscapeFlags flag” | upstream text; file not touched by the Ubuntu patch series |
| CI-043 | A-04.2 | SD | `systemd-259.5/src/core/dbus-manager.c` | 1144 | method_start_transient_unit | “return sd_bus_error_setf(reterr_error, SD_BUS_ERROR_INVALID_” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-044 | A-04.2 | SD | `systemd-259.5/src/core/dbus-unit.c` | 408 | bus_unit_method_start_generic | “return sd_bus_error_setf(reterr_error, SD_BUS_ERROR_INVALID_” | upstream text; file not touched by the Ubuntu patch series |
| CI-045 | A-04.2 | SD | `systemd-259.5/src/core/dbus-manager.c` | 1040-1048 | transient_unit_from_message | “t = unit_name_to_type(name);” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-046 | A-04.2 | SD | `systemd-259.5/src/core/dbus-unit.c` | 415-426 | bus_unit_method_start_generic | “if (sd_bus_message_is_method_call(message, NULL, "StartUnitW” | upstream text; file not touched by the Ubuntu patch series |
| CI-047 | A-04.2 | SD | `systemd-259.5/src/core/dbus-manager.c` | 511 | bus_get_unit_by_name | “return sd_bus_error_setf(reterr_error, BUS_ERROR_NO_SUCH_UNI” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-048 | A-04.2 | SD | `systemd-259.5/src/core/dbus-unit.c` | 1976-1977 | bus_unit_queue_job_one | “if (type == JOB_STOP && UNIT_IS_LOAD_ERROR(u->load_state) &&” | upstream text; file not touched by the Ubuntu patch series |
| CI-049 | A-04.2 | SD | `systemd-259.5/src/core/dbus-unit.c` | 2730-2731 | bus_unit_validate_load_state | “case UNIT_NOT_FOUND:” | upstream text; file not touched by the Ubuntu patch series |
| CI-050 | A-04.2 | SD | `systemd-259.5/src/core/dbus-manager.c` | 1055 | transient_unit_from_message | “return sd_bus_error_setf(reterr_error, BUS_ERROR_UNIT_EXISTS” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-051 | A-04.2 | SD | `systemd-259.5/src/core/dbus-manager.c` | 1187, 1214 | method_get_job; method_cancel_job | “return sd_bus_error_setf(reterr_error, BUS_ERROR_NO_SUCH_JOB”; “return sd_bus_error_setf(reterr_error, BUS_ERROR_NO_SUCH_JOB” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-052 | A-04.2 | SD | `systemd-259.5/src/core/dbus-unit.c` | 1983-1986 | bus_unit_queue_job_one | “return sd_bus_error_setf(reterr_error,” | upstream text; file not touched by the Ubuntu patch series |
| CI-053 | A-04.2 | SD | `systemd-259.5/src/core/dbus-unit.c` | 2733-2741 | bus_unit_validate_load_state | “case UNIT_BAD_SETTING:” | upstream text; file not touched by the Ubuntu patch series |
| CI-054 | A-04.2 | SD | `systemd-259.5/src/core/transaction.c` | 999-1010 | transaction_add_job_and_dependencies | “if (!unit_job_is_applicable(unit, type))” | upstream text; file not touched by the Ubuntu patch series |
| CI-055 | A-04.2 | SD | `systemd-259.5/src/core/dbus-manager.c` | 1421 | method_subscribe | “return sd_bus_error_set(reterr_error, BUS_ERROR_ALREADY_SUBS” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-056 | A-04.2 | SD | `systemd-259.5/src/shared/bus-polkit.c` | 326-330 | async_polkit_read_reply | “} else if (challenge) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-057 | A-04.2 | SD | `systemd-259.5/src/libsystemd/sd-bus/bus-common-errors.h` | 6-38 | file scope | “#define BUS_ERROR_NO_SUCH_UNIT                 "org.freedesk” | upstream text; file not touched by the Ubuntu patch series |
| CI-058 | A-04.2 | SD | `systemd-259.5/src/systemd/sd-bus-protocol.h` | 65-98 | file scope | “#define SD_BUS_ERROR_FAILED                             "org” | upstream text; file not touched by the Ubuntu patch series |
| CI-059 | A-04.3 | SD | `systemd-259.5/src/libsystemd/sd-bus/bus-error.c` | 14-47, 64-71, 176 | bus_standard_errors; bus_error_name_to_errno; errno_to_bus_error_name_new | “SD_BUS_ERROR_MAP(SD_BUS_ERROR_NO_MEMORY,                    ”; “p = startswith(name, "System.Error.");”; “n = strjoin("System.Error.", name);” | upstream text; file not touched by the Ubuntu patch series |
| CI-060 | A-04.4 | SD | `systemd-259.5/src/libsystemd/sd-bus/sd-bus.c` | 2684, 4382-4413 | process_timeout; sd_bus_set_method_call_timeout | “&SD_BUS_ERROR_MAKE_CONST(SD_BUS_ERROR_NO_REPLY, "Method call”; “_public_ int sd_bus_set_method_call_timeout(sd_bus *bus, uin” | upstream text; file not touched by the Ubuntu patch series |
| CI-061 | A-04.4 | SD | `systemd-259.5/src/libsystemd/sd-bus/bus-internal.h` | 311 | BUS_IS_OPEN | “#define BUS_DEFAULT_TIMEOUT ((usec_t) (25 * USEC_PER_SEC))” | upstream text; file not touched by the Ubuntu patch series |
| CI-062 | A-04.5 | PK | `polkit-127/src/polkit/polkiterror.c` | 33-39 | file scope | “static const GDBusErrorEntry polkit_error_entries[] =” | upstream text; file not touched by the Ubuntu patch series |
| CI-063 | A-04.5 | PK | `polkit-127/data/org.freedesktop.PolicyKit1.Authority.xml` | 207-225 | <org.freedesktop.PolicyKit1.Authority> | “<annotation name="org.gtk.EggDBus.ErrorDomain.Member" value=” | upstream text; file not touched by the Ubuntu patch series |
| CI-064 | A-04.5 | PK | `polkit-127/src/polkitbackend/polkitbackendauthority.c` | 830-843 | server_handle_check_authorization | “if (g_hash_table_lookup (server->cancellation_id_to_check_au” | upstream text; file not touched by the Ubuntu patch series |
| CI-065 | A-04.5 | SD | `systemd-259.5/src/shared/bus-polkit.c` | 288-312 | async_polkit_read_reply | “if (sd_bus_message_is_method_error(reply, NULL)) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-066 | A-05.2 | SD | `systemd-259.5/src/shared/bus-wait-for-jobs.c` | 81-123 | bus_wait_for_jobs_new | “int bus_wait_for_jobs_new(sd_bus *bus, BusWaitForJobs **ret)” | upstream text; file not touched by the Ubuntu patch series |
| CI-067 | A-05.2 | SD | `systemd-259.5/src/libsystemd/sd-bus/sd-bus.c` | 2684 | process_timeout | “&SD_BUS_ERROR_MAKE_CONST(SD_BUS_ERROR_NO_REPLY, "Method call” | upstream text; file not touched by the Ubuntu patch series |
| CI-068 | A-05.3 | SD | `systemd-259.5/src/core/dbus-job.c` | 45-69 | bus_job_method_cancel | “int bus_job_method_cancel(sd_bus_message *message, void *use” | upstream text; file not touched by the Ubuntu patch series |
| CI-069 | A-05.3 | SD | `systemd-259.5/src/core/dbus-manager.c` | 1200-1238 | method_cancel_job | “static int method_cancel_job(sd_bus_message *message, void *” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-070 | A-05.3 | SD | `systemd-259.5/man/org.freedesktop.systemd1.xml` | 1364-1371, 1644-1646 | n/a (non-C text) | “<para><function>CancelJob()</function> cancels a specific jo”; “job. <literal>canceled</literal> indicates that a job has be” | upstream text; file not touched by the Ubuntu patch series |
| CI-071 | A-05.4 | SD | `systemd-259.5/src/core/dbus-job.c` | 318-328, 361-377 | bus_job_track_handler; bus_job_track_sender | “static int bus_job_track_handler(sd_bus_track *t, void *user”; “int bus_job_track_sender(Job *j, sd_bus_message *m) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-072 | A-05.4 | SD | `systemd-259.5/src/core/job.c` | 1465-1523 | job_may_gc | “bool job_may_gc(Job *j) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-073 | A-05.5 | SD | `systemd-259.5/src/core/dbus-unit.c` | 2022-2023 | bus_unit_queue_job_one | “/* Before we send the method reply, force out the announceme” | upstream text; file not touched by the Ubuntu patch series |
| CI-074 | A-05.5 | SD | `systemd-259.5/src/core/dbus-unit.c` | 2077-2109, 2014-2031 | bus_unit_queue_job; bus_unit_queue_job_one | “int bus_unit_queue_job(”; “r = manager_add_job_full(u->manager, type, u, mode, /* extra” | upstream text; file not touched by the Ubuntu patch series |
| CI-075 | A-05.5 | SD | `systemd-259.5/man/org.freedesktop.systemd1.xml` | 1288-1294 | n/a (non-C text) | “latter two options. On reply, if successful, this method ret” | upstream text; file not touched by the Ubuntu patch series |
| CI-076 | A-05.6 | SD | `systemd-259.5/src/core/dbus-manager.c` | 1125-1168 | method_start_transient_unit | “static int method_start_transient_unit(sd_bus_message *messa” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-077 | A-05.6 | SD | `systemd-259.5/src/core/dbus-unit.c` | 379-440, 1955-2109 | bus_unit_method_start_generic; bus_unit_queue_job_one | “int bus_unit_method_start_generic(”; “int bus_unit_queue_job_one(” | upstream text; file not touched by the Ubuntu patch series |
| CI-078 | A-05.7 | SD | `systemd-259.5/src/core/job.c` | 241-246 | job_install | “pj = j->type == JOB_NOP ? &j->unit->nop_job : &j->unit->job;” | upstream text; file not touched by the Ubuntu patch series |
| CI-079 | A-05.7 | SD | `systemd-259.5/src/core/transaction.c` | 650-660 | transaction_apply | “assert(j->installed);” | upstream text; file not touched by the Ubuntu patch series |
| CI-080 | A-05.7 | SD | `systemd-259.5/src/core/manager.c` | 2516-2524 | manager_clear_jobs | “void manager_clear_jobs(Manager *m) {” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-081 | A-05.8 | SD | `systemd-259.5/src/core/dbus-manager.c` | 3495 | bus_manager_vtable | “SD_BUS_SIGNAL_WITH_ARGS("Reloading",” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-082 | A-05.8 | SD | `systemd-259.5/src/core/job.c` | 172-174 | job_uninstall | “/* daemon-reload should be transparent to job observers */” | upstream text; file not touched by the Ubuntu patch series |
| CI-083 | A-05.9 | SD | `systemd-259.5/src/core/dbus-manager.c` | 3485-3490 | bus_manager_vtable | “SD_BUS_SIGNAL_WITH_ARGS("JobNew",” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-084 | A-05.9 | SD | `systemd-259.5/src/core/dbus-job.c` | 195-221, 274-300 | send_new_signal; send_removed_signal | “static int send_new_signal(sd_bus *bus, void *userdata) {”; “static int send_removed_signal(sd_bus *bus, void *userdata) ” | upstream text; file not touched by the Ubuntu patch series |
| CI-085 | A-05.9 | SD | `systemd-259.5/src/core/job.c` | 957-985, 1660-1674 | job_run_and_invalidate; job_get_after | “if (r == -EAGAIN)”; “static const char* const job_result_table[_JOB_RESULT_MAX] =” | upstream text; file not touched by the Ubuntu patch series |
| CI-086 | A-05.9 | SD | `systemd-259.5/src/core/unit.c` | 2062-2070 | unit_stop | “int unit_stop(Unit *u) {” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-087 | A-05.9 | SD | `systemd-259.5/man/org.freedesktop.systemd1.xml` | 1638-1650 | n/a (non-C text) | “<para><function>JobNew()</function> and <function>JobRemoved” | upstream text; file not touched by the Ubuntu patch series |
| CI-088 | A-05.10 | SD | `systemd-259.5/src/core/dbus.c` | 1092-1121 | bus_foreach_bus | “int bus_foreach_bus(” | upstream text; file not touched by the Ubuntu patch series |
| CI-089 | A-05.10 | SD | `systemd-259.5/src/core/dbus-job.c` | 361-377 | bus_job_track_sender | “int bus_job_track_sender(Job *j, sd_bus_message *m) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-090 | A-05.10 | SD | `systemd-259.5/src/core/dbus-manager.c` | 1394-1425, 3243-3252 | method_subscribe; bus_manager_vtable | “static int method_subscribe(sd_bus_message *message, void *u”; “SD_BUS_METHOD("Subscribe",” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-091 | A-05.10 | SD | `systemd-259.5/src/shared/bus-wait-for-jobs.c` | 96-105 | bus_wait_for_jobs_new | “/* When we are a bus client we match by sender. Direct conne” | upstream text; file not touched by the Ubuntu patch series |
| CI-092 | A-05.10 | SD | `systemd-259.5/man/org.freedesktop.systemd1.xml` | 1289-1294, 1441-1452 | n/a (non-C text) | “which has been enqueued for asynchronous activation. Callers”; “<para><function>Subscribe()</function> enables most bus sign” | upstream text; file not touched by the Ubuntu patch series |
| CI-093 | A-05.11 | SD | `systemd-259.5/src/core/dbus-manager.c` | 1170-1198 | method_get_job | “static int method_get_job(sd_bus_message *message, void *use” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-094 | A-05.11 | SD | `systemd-259.5/src/core/dbus-job.c` | 122-143 | bus_job_vtable | “const sd_bus_vtable bus_job_vtable[] = {” | upstream text; file not touched by the Ubuntu patch series |
| CI-095 | A-05.11 | SD | `systemd-259.5/src/core/job.c` | 1640-1658 | job_get_after | “[JOB_WAITING] = "waiting",” | upstream text; file not touched by the Ubuntu patch series |
| CI-096 | A-05.12 | SD | `systemd-259.5/src/core/dbus-manager.c` | 1125-1168, 1025-1123 | method_start_transient_unit; transient_unit_from_message | “static int method_start_transient_unit(sd_bus_message *messa”; “static int transient_unit_from_message(” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-097 | A-05.13 | SD | `systemd-259.5/src/core/dbus-manager.c` | 747-772 | method_start_unit_generic | “static int method_start_unit_generic(sd_bus_message *message” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-098 | A-06.1 | SD | `systemd-259.5/src/core/dbus-manager.c` | 3158-3162 | bus_manager_vtable | “SD_BUS_METHOD_WITH_ARGS("StartTransientUnit",” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-099 | A-06.1 | SD | `systemd-259.5/src/core/org.freedesktop.systemd1.conf` | 203, 275 | n/a (non-C text) | “<!-- Managed via polkit or other criteria: org.freedesktop.s”; “send_member="StartTransientUnit"/>” | upstream text; file not touched by the Ubuntu patch series |
| CI-100 | A-06.2 | SD | `systemd-259.5/src/core/dbus-manager.c` | 1138-1144 | method_start_transient_unit | “r = sd_bus_message_read(message, "ss", &name, &smode);” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-101 | A-06.2 | SD | `systemd-259.5/src/basic/unit-def.c` | 358-371 | unit_types_list | “static const char* const job_mode_table[_JOB_MODE_MAX] = {” | upstream text; file not touched by the Ubuntu patch series |
| CI-102 | A-06.2 | SD | `systemd-259.5/src/core/manager.c` | 2145-2155 | manager_add_job_full | “if (mode == JOB_ISOLATE && type != JOB_START)” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-103 | A-06.3 | SD | `systemd-259.5/src/run/run.c` | 113, 2145, 2895 | file scope; make_transient_service_unit; make_transient_trigger_unit | “static JobMode arg_job_mode = JOB_FAIL;”; “r = sd_bus_message_append(m, "ss", service, job_mode_to_stri”; “r = sd_bus_message_append(m, "ss", trigger, job_mode_to_stri” | upstream text; file not touched by the Ubuntu patch series |
| CI-104 | A-06.3 | SD | `systemd-259.5/man/org.freedesktop.systemd1.xml` | 1281-1284 | n/a (non-C text) | “<literal>ignore-requirements</literal>. If <literal>replace<” | upstream text; file not touched by the Ubuntu patch series |
| CI-105 | A-06.4 | SD | `systemd-259.5/src/core/dbus-manager.c` | 1146-1156 | method_start_transient_unit | “r = bus_verify_manage_units_async_impl(” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-106 | A-06.4 | SD | `systemd-259.5/src/core/dbus-util.c` | 161-201 | bus_verify_manage_units_async_impl | “int bus_verify_manage_units_async_impl(” | upstream text; file not touched by the Ubuntu patch series |
| CI-107 | A-06.5 | SD | `systemd-259.5/src/core/dbus-manager.c` | 1025-1084 | transient_unit_from_message | “static int transient_unit_from_message(” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-108 | A-06.5 | SD | `systemd-259.5/src/core/dbus-unit.c` | 2622-2718 | bus_unit_set_properties | “int bus_unit_set_properties(” | upstream text; file not touched by the Ubuntu patch series |
| CI-109 | table:Type | SD | `systemd-259.5/src/core/dbus-service.c` | 568-569 | bus_service_set_transient_property | “if (streq(name, "Type"))” | upstream text; file not touched by the Ubuntu patch series |
| CI-110 | table:Type | SD | `systemd-259.5/src/core/service.c` | 5828 | service_freezer_action | “[SERVICE_EXEC]          = "exec",” | upstream text; file not touched by the Ubuntu patch series |
| CI-111 | table:Type | SD | `systemd-259.5/src/run/run.c` | 1449-1453 | transient_service_set_properties | “if (arg_service_type) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-112 | table:Restart | SD | `systemd-259.5/src/core/dbus-service.c` | 679-680 | bus_service_set_transient_property | “if (streq(name, "Restart"))” | upstream text; file not touched by the Ubuntu patch series |
| CI-113 | table:Restart | SD | `systemd-259.5/src/core/service.c` | 5801 | service_freezer_action | “[SERVICE_RESTART_NO]          = "no",” | upstream text; file not touched by the Ubuntu patch series |
| CI-114 | table:Restart | SD | `systemd-259.5/src/shared/bus-unit-util.c` | 2622 | service_properties | “{ "Restart",                               bus_append_string” | upstream text; file not touched by the Ubuntu patch series |
| CI-115 | table:OOMScoreAdjust | SD | `systemd-259.5/src/core/dbus-execute.c` | 3511-3519 | bus_exec_context_set_transient_property | “} else if (streq(name, "OOMScoreAdjust")) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-116 | table:OOMScoreAdjust | SD | `systemd-259.5/src/basic/process-util.c` | 1249-1251 | oom_score_adjust_is_valid | “bool oom_score_adjust_is_valid(int oa) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-117 | table:OOMScoreAdjust | SD | `systemd-259.5/src/shared/bus-unit-util.c` | 2485 | execute_properties | “{ "OOMScoreAdjust",                        bus_append_safe_a” | upstream text; file not touched by the Ubuntu patch series |
| CI-118 | table:RuntimeMaxUSec | SD | `systemd-259.5/src/core/dbus-service.c` | 610-611 | bus_service_set_transient_property | “if (streq(name, "RuntimeMaxUSec"))” | upstream text; file not touched by the Ubuntu patch series |
| CI-119 | table:RuntimeMaxUSec | SD | `systemd-259.5/src/shared/bus-unit-util.c` | 257-277, 2606, 2641 | bus_append_parse_sec_rename; scope_properties; service_properties | “static int bus_append_parse_sec_rename(sd_bus_message *m, co”; “{ "RuntimeMaxSec",                         bus_append_parse_”; “{ "RuntimeMaxSec",                         bus_append_parse_” | upstream text; file not touched by the Ubuntu patch series |
| CI-120 | table:TimeoutStopUSec | SD | `systemd-259.5/src/core/dbus-service.c` | 594-595 | bus_service_set_transient_property | “if (streq(name, "TimeoutStopUSec"))” | upstream text; file not touched by the Ubuntu patch series |
| CI-121 | table:TimeoutStopUSec | SD | `systemd-259.5/src/shared/bus-unit-util.c` | 2608, 2639 | scope_properties; service_properties | “{ "TimeoutStopSec",                        bus_append_parse_”; “{ "TimeoutStopSec",                        bus_append_parse_” | upstream text; file not touched by the Ubuntu patch series |
| CI-122 | table:ExecStart | SD | `systemd-259.5/src/core/dbus-execute.c` | 1651-1727 | bus_set_transient_exec_command | “int bus_set_transient_exec_command(” | upstream text; file not touched by the Ubuntu patch series |
| CI-123 | table:ExecStart | SD | `systemd-259.5/src/core/dbus-service.c` | 694-698 | bus_service_set_transient_property | “ci = service_exec_command_from_string(name);” | upstream text; file not touched by the Ubuntu patch series |
| CI-124 | table:ExecStart | SD | `systemd-259.5/src/shared/bus-unit-util.c` | 566-735, 2661 | bus_append_exec_command; service_properties | “static int bus_append_exec_command(sd_bus_message *m, const ”; “{ "ExecStopPost",                          bus_append_exec_c” | upstream text; file not touched by the Ubuntu patch series |
| CI-125 | table:ExecStartEx | SD | `systemd-259.5/src/core/dbus-execute.c` | 1688-1706 | bus_set_transient_exec_command | “if (ex_prop) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-126 | table:ExecStartEx | SD | `systemd-259.5/src/shared/bus-unit-util.c` | 572-657 | bus_append_exec_command | “switch (*eq) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-127 | table:ExecStartEx | SD | `systemd-259.5/src/shared/exec-util.c` | 482-488 | exec_command_strings | “static const char* const exec_command_strings[] = {” | upstream text; file not touched by the Ubuntu patch series |
| CI-128 | A-07.1 | SD | `systemd-259.5/src/core/dbus-service.c` | 577-611 | bus_service_set_transient_property | “if (streq(name, "RestartUSec"))” | upstream text; file not touched by the Ubuntu patch series |
| CI-129 | A-07.1 | SD | `systemd-259.5/src/core/dbus-timer.c` | 211-217 | bus_timer_set_transient_property | “if (streq(name, "AccuracyUSec"))” | upstream text; file not touched by the Ubuntu patch series |
| CI-130 | A-07.2 | SD | `systemd-259.5/src/core/dbus-execute.c` | 1708-1727 | bus_set_transient_exec_command | “if (!FLAGS_SET(command_flags, EXEC_COMMAND_VIA_SHELL)) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-131 | A-07.3 | SD | `systemd-259.5/src/core/dbus-execute.c` | 1775-1790 | bus_set_transient_exec_command | “LIST_FOREACH(command, c, *exec_command) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-132 | A-08.1 | SD | `systemd-259.5/src/core/dbus-manager.c` | 1086-1123, 1158-1167 | transient_aux_units_from_message; method_start_transient_unit | “static int transient_aux_units_from_message(”; “r = transient_unit_from_message(m, message, name, &u, reterr” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-133 | A-08.1 | SD | `systemd-259.5/src/run/run.c` | 2874-2955 | make_transient_trigger_unit | “static int make_transient_trigger_unit(” | upstream text; file not touched by the Ubuntu patch series |
| CI-134 | A-08.1 | SD | `systemd-259.5/man/org.freedesktop.systemd1.xml` | 1602-1603 | n/a (non-C text) | “<function>SetUnitProperties()</function>. <varname>aux</varn” | upstream text; file not touched by the Ubuntu patch series |
| CI-135 | A-08.2 | SD | `systemd-259.5/src/run/run.c` | 2971-3017 | start_transient_trigger | “if (arg_unit) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-136 | A-08.3 | SD | `systemd-259.5/src/core/timer.c` | 115-129 | timer_add_trigger_dependencies | “static int timer_add_trigger_dependencies(Timer *t) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-137 | A-08.3 | SD | `systemd-259.5/src/core/dbus-timer.c` | 108 | bus_timer_vtable | “SD_BUS_PROPERTY("Unit", "s", bus_property_get_triggered_unit” | upstream text; file not touched by the Ubuntu patch series |
| CI-138 | A-08.4 | SD | `systemd-259.5/src/core/dbus-timer.c` | 195-300 | bus_timer_set_transient_property | “static int bus_timer_set_transient_property(” | upstream text; file not touched by the Ubuntu patch series |
| CI-139 | A-08.4 | SD | `systemd-259.5/src/core/timer.c` | 1018-1025 | timer_next_elapse_monotonic | “static const char* const timer_base_table[_TIMER_BASE_MAX] =” | upstream text; file not touched by the Ubuntu patch series |
| CI-140 | A-08.5 | SD | `systemd-259.5/src/core/dbus-timer.c` | 106-124 | bus_timer_vtable | “const sd_bus_vtable bus_timer_vtable[] = {” | upstream text; file not touched by the Ubuntu patch series |
| CI-141 | A-08.6 | SD | `systemd-259.5/src/shared/bus-unit-util.c` | 2252-2269, 2747-2753 | bus_append_timers_monotonic; timer_properties | “static int bus_append_timers_monotonic(sd_bus_message *m, co”; “{ "AccuracySec",                           bus_append_parse_” | upstream text; file not touched by the Ubuntu patch series |
| CI-142 | A-08.6 | SD | `systemd-259.5/src/run/run.c` | 1701-1716 | transient_timer_set_properties | “static int transient_timer_set_properties(sd_bus_message *m)” | upstream text; file not touched by the Ubuntu patch series |
| CI-143 | A-09.1 | SD | `systemd-259.5/src/core/dbus-manager.c` | 3063-3067, 770-772 | bus_manager_vtable; method_stop_unit | “SD_BUS_METHOD_WITH_ARGS("StopUnit",”; “static int method_stop_unit(sd_bus_message *message, void *u” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-144 | A-09.1 | SD | `systemd-259.5/src/core/manager.c` | 2145-2155 | manager_add_job_full | “if (mode == JOB_ISOLATE && type != JOB_START)” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-145 | A-09.1 | SD | `systemd-259.5/man/org.freedesktop.systemd1.xml` | 1303-1305 | n/a (non-C text) | “<para><function>StopUnit()</function> is similar to <functio” | upstream text; file not touched by the Ubuntu patch series |
| CI-146 | A-09.2 | SD | `systemd-259.5/src/core/dbus-manager.c` | 747-772 | method_start_unit_generic | “static int method_start_unit_generic(sd_bus_message *message” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-147 | A-09.2 | SD | `systemd-259.5/src/core/dbus-unit.c` | 379-440 | bus_unit_method_start_generic | “int bus_unit_method_start_generic(” | upstream text; file not touched by the Ubuntu patch series |
| CI-148 | A-09.3 | SD | `systemd-259.5/src/core/dbus-unit.c` | 1976-1977 | bus_unit_queue_job_one | “if (type == JOB_STOP && UNIT_IS_LOAD_ERROR(u->load_state) &&” | upstream text; file not touched by the Ubuntu patch series |
| CI-149 | A-09.3 | SD | `systemd-259.5/src/core/unit.h` | 84-86 | UNIT_IS_LOAD_ERROR | “static inline bool UNIT_IS_LOAD_ERROR(UnitLoadState t) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-150 | A-09.3 | SD | `systemd-259.5/src/core/transaction.c` | 975-997 | transaction_add_job_and_dependencies | “if (type != JOB_STOP) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-151 | A-09.4 | SD | `systemd-259.5/src/core/transaction.c` | 305-314 | transaction_drop_redundant | “HASHMAP_FOREACH(j, tr->jobs) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-152 | A-09.4 | SD | `systemd-259.5/src/core/unit.c` | 2062-2088 | unit_stop | “int unit_stop(Unit *u) {” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-153 | A-09.4 | SD | `systemd-259.5/src/core/job.c` | 906-985 | job_run_and_invalidate | “int job_run_and_invalidate(Job *j) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-154 | A-09.4 | SD | `systemd-259.5/src/core/dbus-unit.c` | 1979-1986 | bus_unit_queue_job_one | “if ((type == JOB_START && u->refuse_manual_start) \|\|” | upstream text; file not touched by the Ubuntu patch series |
| CI-155 | A-09.5 | SD | `systemd-259.5/src/shared/bus-polkit.c` | 540-583 | bus_verify_polkit_async_full | “int bus_verify_polkit_async_full(” | upstream text; file not touched by the Ubuntu patch series |
| CI-156 | A-09.5 | SD | `systemd-259.5/src/core/dbus-util.c` | 161-210 | bus_verify_manage_units_async_impl | “int bus_verify_manage_units_async_impl(” | upstream text; file not touched by the Ubuntu patch series |
| CI-157 | A-09.5 | SD | `systemd-259.5/src/libsystemd/sd-bus/bus-convenience.c` | 675-743 | sd_bus_query_sender_privilege | “_public_ int sd_bus_query_sender_privilege(sd_bus_message *m” | upstream text; file not touched by the Ubuntu patch series |
| CI-158 | A-09.6 | SD | `systemd-259.5/src/core/timer.c` | 710-717 | timer_stop | “static int timer_stop(Unit *u) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-159 | A-09.6 | SD | `systemd-259.5/man/org.freedesktop.systemd1.xml` | 1597-1599 | n/a (non-C text) | “<para><function>StartTransientUnit()</function> may be used ” | upstream text; file not touched by the Ubuntu patch series |
| CI-160 | A-10.1 | PK | `polkit-127/data/org.freedesktop.PolicyKit1.Authority.xml` | 33-35 | <org.freedesktop.PolicyKit1.Authority> | “<interface name="org.freedesktop.PolicyKit1.Authority">” | upstream text; file not touched by the Ubuntu patch series |
| CI-161 | A-10.1 | SD | `systemd-259.5/src/shared/bus-polkit.c` | 82-88 | bus_message_new_polkit_auth_call_for_bus | “r = sd_bus_message_new_method_call(” | upstream text; file not touched by the Ubuntu patch series |
| CI-162 | A-10.2 | PK | `polkit-127/data/org.freedesktop.PolicyKit1.Authority.xml` | 275-304 | <CheckAuthorization> | “<method name="CheckAuthorization">” | upstream text; file not touched by the Ubuntu patch series |
| CI-163 | A-10.2 | PK | `polkit-127/src/polkitbackend/polkitbackendauthority.c` | 607-613 | on_sessions_changed | “"    <method name='CheckAuthorization'>"” | upstream text; file not touched by the Ubuntu patch series |
| CI-164 | A-10.3 | PK | `polkit-127/src/polkit/polkitcheckauthorizationflags.h` | 35-47 | file scope | “* @POLKIT_CHECK_AUTHORIZATION_FLAGS_NONE: No flags set.” | upstream text; file not touched by the Ubuntu patch series |
| CI-165 | A-10.3 | PK | `polkit-127/data/org.freedesktop.PolicyKit1.Authority.xml` | 135-145 | <org.freedesktop.PolicyKit1.Authority> | “<annotation name="org.gtk.EggDBus.DeclareFlags" value="Check” | upstream text; file not touched by the Ubuntu patch series |
| CI-166 | A-10.4 | PK | `polkit-127/data/org.freedesktop.PolicyKit1.Authority.xml` | 288 | <CheckAuthorization> | “<annotation name="org.gtk.EggDBus.DocString" value="Details ” | upstream text; file not touched by the Ubuntu patch series |
| CI-167 | A-10.4 | PK | `polkit-127/src/polkitbackend/polkitbackendinteractiveauthority.c` | 885-935, 1044-1085 | may_identity_check_authorization; polkit_backend_interactive_authority_check_authorization | “may_identity_check_authorization (PolkitBackendInteractiveAu”; “/* Not anyone is allowed to check that process XYZ is allowe” | upstream text; file not touched by the Ubuntu patch series |
| CI-168 | A-10.5 | PK | `polkit-127/data/org.freedesktop.PolicyKit1.Authority.xml` | 43-45 | <org.freedesktop.PolicyKit1.Authority> | “<formalpara><title>Unix Process</title><para><literal>subjec” | upstream text; file not touched by the Ubuntu patch series |
| CI-169 | A-10.5 | PK | `polkit-127/src/polkit/polkitsubject.c` | 299-341, 399-534 | polkit_subject_from_string; lookup_asv | “polkit_subject_to_gvariant (PolkitSubject *subject)”; “PolkitSubject *” | upstream text; file not touched by the Ubuntu patch series |
| CI-170 | A-10.6 | PK | `polkit-127/src/polkit/polkitsubject.c` | 415-482 | polkit_subject_new_for_gvariant_invocation | “if (g_strcmp0 (kind, "unix-process") == 0)” | upstream text; file not touched by the Ubuntu patch series |
| CI-171 | A-10.7 | PK | `polkit-127/src/polkitbackend/polkitbackendauthority.c` | 779-870, 874-908, 746-777 | check_auth_cb; server_handle_check_authorization; check_auth_data_free | “server_handle_check_authorization (Server                 *s”; “server_handle_cancel_check_authorization (Server            ”; “check_auth_cb (GObject      *source_object,” | upstream text; file not touched by the Ubuntu patch series |
| CI-172 | A-10.7 | PK | `polkit-127/data/org.freedesktop.PolicyKit1.Authority.xml` | 221-224, 296-312 | <org.freedesktop.PolicyKit1.Authority>; <CheckAuthorization> | “<annotation name="org.gtk.EggDBus.ErrorDomain.Member" value=”; “<arg name="cancellation_id" direction="in" type="s">” | upstream text; file not touched by the Ubuntu patch series |
| CI-173 | A-10.8 | PK | `polkit-127/src/polkitbackend/polkitbackendinteractiveauthority.c` | 941-1160 | polkit_backend_interactive_authority_check_authorization | “polkit_backend_interactive_authority_check_authorization (Po” | upstream text; file not touched by the Ubuntu patch series |
| CI-174 | A-10.9 | PK | `polkit-127/src/polkit/polkitauthority.c` | 820-868, 905-947 | cancel_check_authorization_cb; check_authorization_cb | “check_authorization_cb (GDBusProxy    *proxy,”; “polkit_authority_check_authorization (PolkitAuthority       ” | upstream text; file not touched by the Ubuntu patch series |
| CI-175 | A-10.10 | PK | `polkit-127/src/programs/pkcheck.c` | 387-419, 541-550 | main | “else if (g_strcmp0 (argv[n], "--process") == 0 \|\| g_strcmp0 ”; “flags = POLKIT_CHECK_AUTHORIZATION_FLAGS_NONE;” | upstream text; file not touched by the Ubuntu patch series |
| CI-176 | A-10.10 | PK | `polkit-127/src/polkit/polkitsubject.c` | 299-341 | polkit_subject_from_string | “polkit_subject_to_gvariant (PolkitSubject *subject)” | upstream text; file not touched by the Ubuntu patch series |
| CI-177 | A-10.10 | SD | `systemd-259.5/src/shared/bus-polkit.c` | 63-106 | bus_message_new_polkit_auth_call_for_bus | “static int bus_message_new_polkit_auth_call_for_bus(” | upstream text; file not touched by the Ubuntu patch series |
| CI-178 | A-10.11 | PK | `polkit-127/src/polkitbackend/polkitbackendinteractiveauthority.c` | 1216-1224, 1237, 1286, 1299, 1370, 1381 | check_authorization_sync | “if (action_desc == NULL)”; “result = polkit_authorization_result_new (TRUE, FALSE, NULL)”; “result = polkit_authorization_result_new (TRUE, FALSE, detai”; “result = polkit_authorization_result_new (TRUE, FALSE, detai”; “result = polkit_authorization_result_new (FALSE, TRUE, detai”; “result = polkit_authorization_result_new (FALSE, FALSE, deta” | upstream text; file not touched by the Ubuntu patch series |
| CI-179 | A-10.12 | PK | `polkit-127/src/polkit/polkitsubject.c` | 299-341 | polkit_subject_from_string | “polkit_subject_to_gvariant (PolkitSubject *subject)” | upstream text; file not touched by the Ubuntu patch series |
| CI-180 | A-10.12 | PK | `polkit-127/src/polkit/polkitunixprocess.c` | 376-424 | polkit_unix_process_constructed | “PolkitUnixProcess *process = POLKIT_UNIX_PROCESS (object);” | upstream text; file not touched by the Ubuntu patch series |
| CI-181 | UF-10 text | PK | `polkit-127/meson.build` | 215 | n/a (non-C text) | “config_data.set('HAVE_PIDFD_OPEN', cc.get_define('SYS_pidfd_” | upstream text; file not touched by the Ubuntu patch series |
| CI-182 | A-11.1 | PK | `polkit-127/src/programs/pkcheck.c` | 551-557, 588-645 | main | “if (result == NULL)”; “if (polkit_authorization_result_get_is_authorized (result))” | upstream text; file not touched by the Ubuntu patch series |
| CI-183 | A-11.1 | PK | `polkit-127/src/polkit/polkitauthorizationresult.c` | 238-262 | polkit_authorization_result_get_temporary_authorization_id | “* polkit_authorization_result_get_dismissed:” | upstream text; file not touched by the Ubuntu patch series |
| CI-184 | A-11.2 | PK | `polkit-127/src/polkitbackend/polkitbackendinteractiveauthority.c` | 719-800, 1106-1135 | check_authorization_challenge_cb; polkit_backend_interactive_authority_check_authorization | “check_authorization_challenge_cb (AuthenticationAgent       ”; “/* Caller is up for a challenge! With light sabers! Use an a” | upstream text; file not touched by the Ubuntu patch series |
| CI-185 | A-11.3 | SD | `systemd-259.5/src/shared/bus-polkit.c` | 273-337 | async_polkit_read_reply | “static int async_polkit_read_reply(sd_bus_message *reply, As” | upstream text; file not touched by the Ubuntu patch series |
| CI-186 | A-12.1 | PK | `polkit-127/src/polkit/polkitsubject.c` | 299-341, 471-478 | polkit_subject_from_string; polkit_subject_new_for_gvariant_invocation | “polkit_subject_to_gvariant (PolkitSubject *subject)”; “v = lookup_asv (details_gvariant, "start-time", G_VARIANT_TY” | upstream text; file not touched by the Ubuntu patch series |
| CI-187 | A-12.1 | PK | `polkit-127/src/polkit/polkitunixprocess.c` | 1261-1330 | get_kinfo_proc | “static guint64” | upstream text; file not touched by the Ubuntu patch series |
| CI-188 | A-12.2 | KN | `linux v7.0.14 fs/proc/array.c` | 580-581, 606 | do_task_stat | “nsec_to_clock_t(timens_add_boottime_ns(task->start_boottime)”; “seq_put_decimal_ull(m, " ", start_time);” | upstream v7.0.14; Ubuntu delta touches this file at 482-487,657-662 (old-side), outside the cited lines |
| CI-189 | A-12.5 | PK | `polkit-127/src/polkit/polkitunixprocess.c` | 426-427, 1015-1019 | polkit_unix_process_constructed; polkit_unix_process_new_full | “if (process->start_time == 0)”; “* polkit_unix_process_new_for_owner:” | upstream text; file not touched by the Ubuntu patch series |
| CI-190 | A-13.1 | PK | `polkit-127/src/polkit/polkitunixprocess.c` | 1806-1927 | polkit_unix_process_get_racy_uid__ | “polkit_unix_process_get_racy_uid__ (PolkitUnixProcess  *proc” | upstream text; file not touched by the Ubuntu patch series |
| CI-191 | A-13.1 | PK | `polkit-127/src/polkitbackend/polkitbackendsessionmonitor-systemd.c` | 268-302 | polkit_backend_session_monitor_get_user_for_subject | “polkit_backend_session_monitor_get_user_for_subject (PolkitB” | upstream text; file not touched by the Ubuntu patch series |
| CI-192 | A-13.2 | PK | `polkit-127/src/polkitbackend/polkitbackendinteractiveauthority.c` | 1002-1086, 1226-1232 | polkit_backend_interactive_authority_check_authorization; check_authorization_sync | “user_of_caller = polkit_backend_session_monitor_get_user_for”; “/* every subject has a user; this is supplied by the client,” | upstream text; file not touched by the Ubuntu patch series |
| CI-193 | A-13.2 | PK | `polkit-127/src/polkit/polkitunixprocess.c` | 429-439 | polkit_unix_process_constructed | “if (process->uid == -1)” | upstream text; file not touched by the Ubuntu patch series |
| CI-194 | A-13.2 | PK | `polkit-127/src/polkitbackend/polkitbackendsessionmonitor-systemd.c` | 284-301 | polkit_backend_session_monitor_get_user_for_subject | “subject_uid = polkit_unix_process_get_uid (POLKIT_UNIX_PROCE” | upstream text; file not touched by the Ubuntu patch series |
| CI-195 | A-13.3 | PK | `polkit-127/src/polkit/polkitunixprocess.c` | 320-368, 375-427, 730-748, 1105-1143 | polkit_unix_process_set_property; polkit_unix_process_constructed; polkit_unix_process_get_pid; polkit_unix_process_exists_sync | “polkit_unix_process_get_pid_from_pidfd (gint   pidfd,”; “polkit_unix_process_constructed (GObject *object)”; “polkit_unix_process_get_pid (PolkitUnixProcess *process)”; “polkit_unix_process_exists_sync (PolkitSubject   *subject,” | upstream text; file not touched by the Ubuntu patch series |
| CI-196 | A-13.3 | PK | `polkit-127/meson.build` | 215 | n/a (non-C text) | “config_data.set('HAVE_PIDFD_OPEN', cc.get_define('SYS_pidfd_” | upstream text; file not touched by the Ubuntu patch series |
| CI-197 | A-13.4 | PK | `polkit-127/src/polkit/polkitunixprocess.c` | 55-147 | file scope | “* SECTION:polkitunixprocess” | upstream text; file not touched by the Ubuntu patch series |
| CI-198 | A-13.5 | PK | `polkit-127/src/polkitbackend/polkitbackendinteractiveauthority.c` | 1234-1239 | check_authorization_sync | “/* special case: uid 0, root, is _always_ authorized for any” | upstream text; file not touched by the Ubuntu patch series |
| CI-199 | A-14.1 | SD | `systemd-259.5/src/libsystemd/sd-bus/bus-objects.c` | 1331-1353, 565-630 | object_find_and_run; property_get_set_callbacks_run | “if (streq(m->interface, "org.freedesktop.DBus.Properties")) ”; “static int property_get_set_callbacks_run(” | upstream text; file not touched by the Ubuntu patch series |
| CI-200 | A-14.2 | SD | `systemd-259.5/src/libsystemd/sd-bus/bus-objects.c` | 751-798, 1355-1372 | vtable_append_all_properties; object_find_and_run | “static int vtable_append_all_properties(”; “} else if (streq(m->member, "GetAll")) {” | upstream text; file not touched by the Ubuntu patch series |
| CI-201 | A-14.3 | SD | `systemd-259.5/src/core/dbus-cgroup.c` | 438-448 | bus_cgroup_vtable | “SD_BUS_PROPERTY("MemoryLimit", "t", bus_property_get_uint64_” | upstream text; file not touched by the Ubuntu patch series |
| CI-202 | A-14.3 | SD | `systemd-259.5/src/core/dbus-service.c` | 345, 413-417 | bus_service_vtable | “SD_BUS_PROPERTY("PermissionsStartOnly", "b", bus_property_ge”; “SD_BUS_PROPERTY("StartLimitInterval", "t", bus_property_get_” | upstream text; file not touched by the Ubuntu patch series |
| CI-203 | A-14.3 | SD | `systemd-259.5/src/core/dbus-execute.c` | 1418-1422 | bus_exec_vtable | “SD_BUS_PROPERTY("Capabilities", "s", property_get_empty_stri” | upstream text; file not touched by the Ubuntu patch series |
| CI-204 | A-14.3 | SD | `systemd-259.5/src/core/dbus-unit.c` | 965, 1090-1096 | bus_unit_vtable | “SD_BUS_PROPERTY("OnSuccesJobMode", "s", property_get_job_mod”; “SD_BUS_PROPERTY("RequiresOverridable", "as", property_get_em” | upstream text; file not touched by the Ubuntu patch series |
| CI-205 | A-14.3 | SD | `systemd-259.5/src/core/dbus-manager.c` | 2950, 2964-2965, 3014-3016 | bus_manager_vtable | “SD_BUS_WRITABLE_PROPERTY("ShutdownWatchdogUSec", "t", proper”; “SD_BUS_PROPERTY("DefaultStartLimitIntervalSec", "t", bus_pro”; “SD_BUS_PROPERTY("DefaultBlockIOAccounting", "b", bus_propert” | Ubuntu-patched file; cited lines lie outside every patched hunk (numbers are post-patch) |
| CI-206 | A-14.4 | SD | `systemd-259.5/src/libsystemd/sd-bus/bus-objects.c` | 1463-1474 | bus_process_object | “if (sd_bus_message_is_method_call(m, "org.freedesktop.DBus.P” | upstream text; file not touched by the Ubuntu patch series |
| CI-207 | A-15.2 | KN | `linux v7.0.14 kernel/sys.c` | 1308-1366 | setsid | “DECLARE_RWSEM(uts_sem);” | upstream v7.0.14; Ubuntu delta 7.0.0-31.31 hunk(s) OVERLAP the cited lines: 1308-1313 |
| CI-208 | A-15.2 | KN | `linux v7.0.14 include/uapi/linux/utsname.h` | 1-28 | file scope | “/* SPDX-License-Identifier: GPL-2.0 WITH Linux-syscall-note ” | upstream v7.0.14 (identical to v7.0); Ubuntu delta 7.0.0-31.31 does not touch this file |
| CI-209 | A-15.3 | KN | `linux v7.0.14 kernel/utsname_sysctl.c` | 74-123 | proc_do_uts_string | “static DEFINE_CTL_TABLE_POLL(hostname_poll);” | upstream v7.0.14 (identical to v7.0); Ubuntu delta 7.0.0-31.31 does not touch this file |
| CI-210 | A-16.3 | GL | `glibc-2.43/nss/initgroups.c` | 46-137 | internal_getgrouplist | “internal_getgrouplist (const char *user, gid_t group, long i” | upstream text; file not touched by the Ubuntu patch series |
| CI-211 | A-16.3 | GL | `glibc-2.43/nss/nss_module.c` | 170-189 | module_load | “module_load (struct nss_module *module)” | upstream text; file not touched by the Ubuntu patch series |
| CI-212 | A-16.3 | GL | `glibc-2.43/nss/nss_database.c` | 297-402 | nss_database_reload | “FILE *fp = fopen (_PATH_NSSWITCH_CONF, "rce");” | Ubuntu-patched file; cited lines lie outside every patched hunk; numbers are those of the unpatched upstream file (the Ubuntu series shifts later lines) |
| CI-213 | A-16.3 | GL | `glibc-2.43/manual/nss.texi` | 521-530 | n/a (non-C text) | “In statically linked programs, the main application and NSS ” | upstream text; file not touched by the Ubuntu patch series |
| CI-214 | A-16.4 | GL | `glibc debian.tar.xz debian/local/etc/nsswitch.conf` | 7-10 | n/a (non-C text) | “passwd:         files” | Ubuntu packaging file (debian tarball), not upstream |
| CI-215 | A-16.4 | SD | `systemd debian.tar.xz debian/libnss-systemd.postinst` | 14-28 | n/a (non-C text) | “local nsswitch="${DPKG_ROOT}/etc/nsswitch.conf"” | Ubuntu packaging file (debian tarball), not upstream |
| CI-216 | A-16.4 | SD | `systemd-259.5/src/nss-systemd/nss-systemd.c` | 337, 477 | _nss_systemd_getpwnam_r; _nss_systemd_getgrnam_r | “status = userdb_getpwnam(name, pwd, buffer, buflen, &e);”; “status = userdb_getgrnam(name, gr, buffer, buflen, &e);” | upstream text; file not touched by the Ubuntu patch series |
| CI-217 | A-17.1 | GT | `git-2.53.0/Documentation/gitrepository-layout.adoc` | 19-33, 96-143, 262-283 | n/a (non-C text) | “* a '<project>.git' directory that is a 'bare' repository”; “References are stored in subdirectories of this”; “This is similar to 'info/grafts' but is internally used” | upstream; no Ubuntu patch series exists for this source |
| CI-218 | A-18.2 | DP | `dpkg-1.23.7ubuntu1/lib/dpkg/dump.c` | 557-580 | writedb_stanzas | “writedb(const char *filename, enum writedb_flags flags)” | Ubuntu native-format source tree; no separate upstream tarball or patch series |
| CI-219 | A-18.3 | DP | `dpkg-1.23.7ubuntu1/lib/dpkg/dbmodify.c` | 88-140, 361-395, 403-431 | ulist_select; modstatdb_open; modstatdb_get_status | “cleanupdates(void)”; “ohshit(_("required read/write access to the dpkg database di”; “modstatdb_checkpoint(void)” | Ubuntu native-format source tree; no separate upstream tarball or patch series |
| CI-220 | A-18.4 | DP | `dpkg-1.23.7ubuntu1/lib/dpkg/dbmodify.c` | 165-186, 360-370 | createimptmp; modstatdb_open | “onerr_abort--;”; “else if (readwritereq >= msdbrw_write)” | Ubuntu native-format source tree; no separate upstream tarball or patch series |

### E.2 Named-section citations (no usable line numbers)

Each anchor was confirmed by a text search in the retrieved file (the specification
HTML after tag removal). `P` = provenance: **U** upstream text, untouched by any Ubuntu
patch series; **A** Ubuntu-patched file, cited text outside the patched hunks.

| Source | File (archive-relative) | Section / element | Content anchor | P |
|---|---|---|---|---|
| `DB` | `dbus-specification.html` | System message bus | `unix:path=/var/run/dbus/system_bus_socket`; “might prefer” | U |
| `DB` | same | Authentication Protocol (Protocol Overview, AUTH, BEGIN, NEGOTIATE_UNIX_FD) | `AUTH EXTERNAL 31303030`; “nul byte” | U |
| `DB` | same | Message Format; Valid Signatures | `yyyyuua(yv)`; “134217728 (128 MiB)” | U |
| `DB` | same | Marshaling; Header Fields | “Arrays have a maximum length … 67108864 (64 MiB)”; `ALLOW_INTERACTIVE_AUTHORIZATION`; `NO_REPLY_EXPECTED` | U |
| `DB` | same | Hello; Message Bus Names | “There is no corresponding \"disconnect\" request; if a client wishes to disconnect from the bus, it simply closes the socket” | U |
| `DB` | same | AddMatch | `org.freedesktop.DBus.AddMatch` | U |
| `DB` | same | Method Calls; Errors; Error names | “it is an error message” | U |
| `DB` | same | `org.freedesktop.DBus.Properties` | “an appropriate access control error” | U |
| `DB` | same | interactive authorization hint (flag `ALLOW_INTERACTIVE_AUTHORIZATION`) | “suitably long timeout” | U |
| `MP` | `man/man2/uname.2` | NOTES, VERSIONS, STANDARDS | “sizeof”; “sethostname”; “POSIX.1” | U |
| `MP` | `man/man5/proc_pid_stat.5` | field (22) `starttime` | “after system boot”; `sysconf(_SC_CLK_TCK)` | U |
| `MP` | `man/man5/passwd.5`, `man/man5/group.5` | field lists | “GECOS”; `user_list` | U |
| `MP` | `man/man5/nsswitch.conf.5` | DESCRIPTION (line 13) | “name-service information” | A (patch 0008 touches line 274 only) |
| `MP` | `man/man3/getgrouplist.3` | DESCRIPTION | “scans the group database”; `ngroups` | U |
| `MP` | `man/man2/{stat,statx,getxattr,fgetxattr,listxattr,flistxattr,openat2}.2`, `man/man7/{capabilities,xattr}.7` | per page | `stx_mnt_id` (statx); `ERANGE` (getxattr); `RESOLVE_NO_SYMLINKS` (openat2); `security.capability` (capabilities); `system.posix_acl` (xattr) | U |
| `SD` | `man/machine-id.xml` | Description; Initialization; First Boot Semantics | “lowercase ID”; “uninitialized”; “confidential” | U |
| `SD` | `man/org.freedesktop.systemd1.xml` | `StartTransientUnit`, `CancelJob`, `JobRemoved` text | “enqueued for asynchronous activation”; “whose execution has already begun” | U (line ranges in E.1) |
| `DP` | `man/dpkg-query.pod` | DESCRIPTION; `-l`; `-S` | “dpkg database”; `C.UTF-8` | Ubuntu native tree |
| `DP` | `man/deb-control.pod`, `man/deb822.pod`, `man/deb-version.pod` | field syntax | `Multi-Arch` | Ubuntu native tree |
| `GT` | `Documentation/gitrepository-layout.adoc` | `HEAD`, `refs`, `packed-refs`, `commondir`, gitfile | `packed-refs`; `gitdir`; `commondir` | U |
| `GT` | `Documentation/{gitformat-loose,gitformat-pack,git-rev-parse,gitrevisions}.adoc`, `Documentation/technical/{reftable,hash-function-transition}.adoc` | existence of the format documents only (A-17.2); their rules are not transcribed | file names | U |
| `GL` | `manual/nss.texi` | NSS static-linking note | `errno` (lines 521-530 in E.1) | U |

### E.3 Repository records cited

Identities of the accepted repository records whose own line numbers or rows are
cited (this working tree, 2026-10-10):

| Short name | Repository path | Lines | Bytes | SHA-256 (this tree) | Cited as |
|---|---|---:|---:|---|---|
| R2 | `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s2-r2-citations.md` | 1866 | 177481 | `299f0598bb198572f2edb994234a63956ecafc9ab1873cb10879d0a238dea1a5` | R2 §n and R2 line n (e.g. line 620) |
| W2 / WP-2 inventory | `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp2-operation-inventory.md` | 1450 | 230574 | `da341efb8c29b862d63c1463e981ccfedbe1f6680de2d416ff285fdae06461fd` | WP-2 inventory line n, row ids H-…, RT…, SA… |
| D | `docs/review/phase-5-0-p5-r5-rp11-h1-oracle-test-one-host-design-amendment-proposal.md` | 7307 | 525019 | `a752a4b8fe7eb1edf3e3a25decd3a7517ecccc85fedbb0b0b7e003cb7e615d02` | D line n (940, 1012, 4437, 4453), D 4.x.y |
| R8 | `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-r8-remediation-proposal.md` | 4816 | 551246 | `ab5db5010d9d1b2738b04f1ffbd62ab4414d901e9f7f79323ac49f811f660e04` | R8 §n (E-2, SN-10) |
| Contract | `docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-interface-contract.md` | 469 | 50599 | `b766c10f2c28ac2d32a7dc7ee4ab2c92a3cf80d67fd70f345a9f0dd7ba92c888` | contract §n, UF-nn statements quoted verbatim |

## Appendix F — R1 change register (every changed statement)

| Where | Class | Change | Finding |
|---|---|---|---|
| Header, status line, new §R1, §1 "Citation conventions" | — | R1 status; reading-basis statement; conventions made exact; "line-printing helper" sentence removed | R1, R3 |
| §2 (all subsections) | — | rewritten: downloaded trust anchor, fingerprints, signature results, full URLs/times/sizes/hashes, upstream tags and commits, kernel hashes complete (no ellipsis), glibc/man-pages patch series applied, kernel-delta authentication gap, Launchpad pages | R2, R3 |
| Every citation token in §§3–4 | — | paths expanded to archive-relative form (e.g. `core/dbus-manager.c` ⇒ `src/core/dbus-manager.c`, `sd-bus/sd-bus.c` ⇒ `src/libsystemd/sd-bus/sd-bus.c`, `data/…Authority.xml` ⇒ the full file name, `man2/uname.2` ⇒ `man/man2/uname.2`, `SDM n` ⇒ `man/org.freedesktop.systemd1.xml:n`); `meson.build:215` is the polkit root file; A-10.6 and A-10.7 citations repaired (they had been mis-parsed because of stray backtick quoting) | R3 |
| A-01.5 | ASF/W | quotation corrected to the specification's exact wording; meaning unchanged | R3 |
| A-01 … A-09, A-14 (other than A-01.5) | ASF/MD | text unchanged; only citations expanded; Appendix E.1 states patched/unpatched provenance for each | R3 |
| A-10.5 | ASF/W | rewritten to separate documentation prose, decoder and encoder and to name the three shapes | R4 |
| A-10.6 | ASF/S | rewritten (R1 wording "`uid` optional in every form" was self-contradictory and is **superseded by R2**, see F.2): PID/start-time form requires `pid` and `start-time` (`uid` optional); pidfd form requires `pidfd` and `uid`; citation range corrected to `415-482` | R4; R2 corrects |
| A-10.7 | ASF/W | error-text quotation de-marked; citations expanded; substance unchanged | R3 |
| A-10.10 | ASF/R | adds that `pkcheck` uses `polkit_unix_process_new_for_owner`, that the `pkcheck`-equivalent shape *deliberately supplies* `uid`, and that no `pidfd` is sent | R4 |
| A-10.12 | ASF/R | **new**: libpolkit encoder always writes `pid`, `start-time`, `uid`; `pidfd` only if `pidfd_is_safe` | R4 |
| P-10.1 | PSC/M | wording: `uid` is supplied deliberately in S-A; S-B requires `pidfd`+`uid`; decoder's acceptance of PID/start-time without `uid` is a fact, not a candidate; no shape selected | R4 |
| A-13.2 | ASF/S | `uid` qualifier added (optional in PID/start-time form, required in pidfd form) | R4 |
| §5 DI-6 row; §6 Q3-5, Q3-6 rows; Appendix A P-10.1 row; O-5 | MD/PSC/obs. | consistency edits for R4; O-5 now also records that the XML prose lists `uid` in both forms while the decoder does not require it | R4 |
| §6 Q3-11 row | readiness | sentence added: `PO3-11.1` fail-closed record stays in force and no acquisition mechanism is selected; closure state unchanged | boundary |
| §7 residuals | residual | **new R-M.1**: the Ubuntu kernel delta `7.0.0-31.31` is not authenticated through the current signed indexes; A-12.3 and A-15.2 rest on equality with R2 Appendix D | R2, R3 |
| A-12.3, A-15.2 | ASF/S | text unchanged; the delta's provenance is now stated in §2.4 | R3 |
| §8 answers 1, 2 | — | updated for the downloaded trust anchor and the additional patch series | R2 |

Re-checked and **unchanged**: A-10.1 … A-10.4, A-10.8, A-10.9, A-10.11, A-11.1 … A-11.3,
P-11.1, A-12.1 … A-12.5, A-13.1, A-13.3 … A-13.5, P-13.1, D-1 … D-14, every other
residual, every other readiness row, and the answers to Q6-6 and Q6-7 (still none).

### F.2 R2 change register (findings `WP3-SC-R1-RE1`, `WP3-SC-R1-RE2`)

| Where | Class | Change | Finding |
|---|---|---|---|
| Title, header, status line, companions | — | R1/R2 title; R2 work ID; status line is now `WP-3 SOURCE COMPLETION R2 REMEDIATION RETURNED — INDEPENDENT CODEX RE-REVIEW PENDING`; R2 handback linked | R2 |
| New §R2 (R2.1, R2.2) | — | R2 authority, defects, remediation, results | RE1, RE2 |
| §2 "Retrieval environment" | — | states that the sixteen kernel.org rows of §2.4 were retrieved by R2 on 2026-10-11, all other rows by R1 | RE1 |
| §2.4 (all sixteen kernel.org rows; prose) | — | all rows replaced by independent retrievals (own `h=` value, requested = effective URL, UTC time, bytes, full SHA-256); six `cmp` results tabulated; tag and commit identities of both refs tied to the pages that print them; the R1 shared-identity rows are gone; the Ubuntu-delta paragraph, its row and the "Authentication gap" paragraph are unchanged | RE1 |
| §1 "Citation conventions" `KN` row; UF-12 sources line; A-15.2 | ASF/S | wording: "byte-identical (R2 comparison, §2.4)" instead of the unevidenced "identical"; no kernel fact changed | RE1 |
| A-10.6 | ASF/S | opening rewritten: `uid` optional in the general PID/start-time form and required in the pidfd form; "absent ⇒ −1" moved to the general-form clause; remainder unchanged | RE2 |
| Appendix F (R1 register), A-10.6 row | — | the R1 summary "optional in every form" corrected and cross-referred to F.2 | RE2 |

Rechecked and **unchanged**: A-12.2 (kernel content), Appendix E.1 (`KN` rows CI-188, CI-207 … CI-209 and
all 220 citations), R1.4, A-10.5, A-10.10, A-10.12, P-10.1, A-13.2, the §5 DI-6 row, the §6 Q3-5/Q3-6 rows,
Appendix A, O-5, A-12.3 and A-15.2 as to the Ubuntu delta, residual `R-M.1` (§7), every Q3 readiness state,
D-1 … D-14 (still proposals), and the non-answers to Q6-6 and Q6-7.
