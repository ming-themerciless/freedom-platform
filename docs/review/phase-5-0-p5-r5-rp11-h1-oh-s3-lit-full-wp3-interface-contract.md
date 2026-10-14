# LIT-FULL WP-3 interface contract — cumulative integration of the source-completion evidence and decisions D-1 … D-6, D-9, D-10

Work IDs: original `C-P5.0-R5-RP11-H1-OH-S3-RT3-WP3-20261009-20` · R1 revision
`C-P5.0-R5-RP11-H1-OH-S3-RT3-WP3-R1-20261010-22` · this integration
`C-P5.0-R5-RP11-H1-OH-S3-RT3-WP3-CI1-20261012-26` · executor Claude · 2026-10-12 ·
repository documentation only: no host, no network, no research, no retained evidence.

**WP-3 CONTRACT INTEGRATION RETURNED — INDEPENDENT CODEX REVIEW PENDING**

**What this file is.** The accepted WP-3 interface contract, corrected cumulatively in
place. Its earlier text was a `HARD STOP`: eighteen facts `UF-01` … `UF-18` were
unsupported by the authorized repository sources, and no Q3 question could be closed.
The [accepted source-completion record](phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-record.md)
(1,758 lines, 240,533 bytes, SHA-256
`4c2a1b76a72002de77ca885ba248f086c302b5e9aebebd117cfa90b8989a1049`) now gives, for every
former `UF-01` … `UF-18`, the evidence result, the proposals and the residuals (§6.1).
That record's classifications are preserved here exactly: an `ASF` or `MD` row stays a
version-bound source fact or a derivation; a `PSC` row stays a proposal; an
unavailable mechanism stays unavailable; a residual stays a residual. **Nothing was
turned into a source fact by being integrated.**

**What is decided.** Only eight decisions are decided here, adopted by Peter Duscha as a
unit by accepting the exact integration prompt (§11): **D-1, D-2, D-3, D-4, D-5, D-6, D-9
and D-10**. They are recorded as `DEC` and only to the scope, rationale, failure semantics
and retained risks fixed in that prompt. **D-7, D-8 and D-11 … D-14 are not decided.**

**What this makes of the Q3 questions.** Q3-1 … Q3-7 are reconciled as **closure-ready** on
the accepted evidence and these eight decisions (§5). *Closure-ready is not closed*: the
closure is accepted only after independent Codex review and Peter's later gate decision.
Q3-9 stays open (blocked by R-03.1, D-7 and Q6-2). Q3-11 keeps its fail-closed record
`PO3-11.1` (blocked by D-11 … D-14 and Q6-3). Q6-6 and Q6-7 are **not answered**; Q4-1,
Q4-7, Q4-8 and Q4-11 are later-package inputs and are not decided (§7).

**What is not changed.** Baseline v1.8; LIT-FULL under R3-ROOT is a readiness investigation
only and is not selected for implementation; concrete Route 3 is unestablished; exactly
RT-1 … RT-5, SA-1 (`start`) and SA-2 (`stop`) are in scope; F-1 is B2-F, both lifecycle
acts are in, B3-OUT is effective; EX-1 and EX-2 are effective only for their accepted uses
and no EX-3 exists; no dynamic child or distribution executable is admitted beneath a first
design-controlled root image; DI-6 is the only retained replacement-child intent; H-1, RB-1,
RS-1 and H-1R are outside the set; BC-2 is a later WP-9 decision; WP-4 … WP-7 are separately
gated and **not** authorized by this file. This file selects nothing for implementation and
chooses no language, library, binding or syscall.

**The former `HARD STOP`.** The accepted WP-3 `HARD STOP` is recorded in §12 and **remains in
force** until independent Codex review and Peter's later gate decision replace it. This
file does not accept itself and does not authorize WP-4.

**Residual `R-M.1` (visible wherever its facts are integrated: §3.6, §3.9, §6.2).** The Ubuntu
kernel delta `linux_7.0.0-31.31.diff.gz` is **not** authenticated through the current signed
Ubuntu `Sources` indexes. Peter accepted it, for the limited facts A-12.3 and A-15.2 only,
because its exact byte count and SHA-256 equal the already accepted R2 Appendix D evidence.
That is a limited provenance basis; it is **not** archive-chain authentication.

**Revision history.** R1 (2026-10-10, finding `WP3-HS-R1`) added the cancellation and
abandonment treatment of §3.0 and expanded `UF-05`. CI1 (2026-10-12, this revision)
integrates the accepted evidence and the eight decisions. Every prior row or section that
changed is listed in §12.

## 1. Fixed scope, source hierarchy, fact classes and version boundary

**Scope.** LIT-FULL under the R3-ROOT readiness investigation: procedures RT-1 … RT-5, SA-1
(`start`) and SA-2 (`stop`); EX-1 (`sudo` launch preamble, LR-2 only) and EX-2 (installer
class, HB-1) stay outside the root-procedure set; BQ-4 means no dynamic child. Baseline
v1.8, F-1 B2-F, both lifecycle acts in, B3-OUT, EX-1, EX-2 and no EX-3 are unchanged.
Q6-6 and Q6-7 are **not answered** here (§3.0.5 and §3.4 state only that the
`effect: "unknown"` mapping and the BS-4 extension are theirs). BC-2 remains a later WP-9
question. D-7 remains with Q3-9/Q6-2; D-8 remains with Q6-6; D-11 … D-14 are undecided.
Q3-9 stays blocked by R-03.1, D-7 and Q6-2; Q3-11 keeps its fail-closed treatment and stays
blocked by D-11 … D-14 and Q6-3. A cancelled client wait is not proof that a queued job
stopped or that a mutating request had no effect.

**Source hierarchy** (highest first; a lower source never overrides a higher):

1. `.agents/AGENTS.md`, `docs/implementation-plan.md`, `docs/review/Handover information`.
2. Peter Duscha's decisions: the adoption of D-1 … D-6, D-9 and D-10 as fixed in the
   [accepted integration prompt](phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-contract-integration-claude-prompt.md)
   (358 lines, 18,188 bytes, SHA-256 `894470357ed0fa1ed6c0fba251c471a9e549b7412068b1c1009984580ea91fce`)
   by the [acceptance and activation record](project-review-2026-10-12-p5-r5-rp11-h1-oh-s3-lit-full-wp3-contract-integration-acceptance-and-claude-activation.md)
   (74 lines, 3,795 bytes, SHA-256 `19eff0574a49e5f7364b3f4e2c1268cb22dc10b317f327a4c94638d2c7ca91fa`);
   and the [evidence-acceptance decision](project-review-2026-10-11-p5-r5-rp11-h1-oh-s3-lit-full-wp3-source-completion-evidence-acceptance-and-contract-integration-direction.md)
   (57 lines, 3,093 bytes, SHA-256 `a7af48d1b6ee3a500d33d96e87944e26ac2a031d936bf930a7c149318778da0c`),
   including its limited `R-M.1` provenance basis.
3. The accepted WP-2 inventory
   (`phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp2-operation-inventory.md`, 318 rows, 77 steps,
   41 call sites), the accepted R8 proposal and its acceptance, the accepted one-host amendment
   proposal and its D3-R6 acceptance, the accepted WP-1 R6 proposal with its acceptance, BQ
   decisions and EX-1/EX-2 change control, and g1-decisions.
4. The accepted OH-S2 R2 citation record
   (`phase-5-0-p5-r5-rp11-h1-oh-s2-r2-citations.md`, cited as **R2**).
5. **The accepted WP-3 source-completion record** (cited as the *source record*, by its stable
   identifiers `A-nn.n`, `P-nn.n`, `R-nn.n`, `O-n`; identity above): the carrier of the
   version-bound primary-source evidence for the former `UF-01` … `UF-18`. It reproduces R2's
   Appendix A and B lists independently (A-03.1) and reports, rather than resolves, its
   disagreements with accepted texts (O-1 … O-6). Where it and a higher source differ, the
   higher source governs and the difference stays reported.

**Version boundary.** Every version-bound claim is bound to systemd `259.5-0ubuntu3.4` and
polkit `127-2ubuntu1.1` (R2; source record §2) and, for the source record's further facts, to
the versions that record's §2 names: D-Bus Specification 0.43, glibc `2.43-2ubuntu2.4`, dpkg
`1.23.7ubuntu1`, git `2.53.0`, man-pages `6.17`, Linux `v7.0`/`v7.0.14` and the Ubuntu kernel
delta `7.0.0-31.31` (residual `R-M.1`). No claim is made for any other version, and none is
extended by inference. No installed-host version, build option or policy is assumed (R-01.1,
R-10.1, R-15.1, R-16.1, R-17.1, R-18.1).

**Fact classes.** Each statement in this file carries exactly one class.

| Class | Meaning | Rule |
|---|---|---|
| `SF` | Accepted source fact (original contract) | Quoted or paraphrased from an authorized source with file and line. |
| `ASF` | Authoritative source fact of the source record | Stated by that record with a primary-source citation bound to its §2 versions; cited here by record identifier and tier (`S` server, `W` wire/API, `R` reference client — never a contract). |
| `MD` | Mechanical derivation | Follows by counting, matching or set operations over `SF`/`ASF`; the derivation is stated. |
| `DR` | Accepted design requirement | A requirement already accepted in WP-2/R8/D (intent, failure contract). Not a wire fact. |
| `DEC` | Adopted decision | One of D-1 … D-6, D-9, D-10, exactly as fixed by Peter's acceptance of the integration prompt (§11). |
| `PSC` | Proposed source-completion mechanism | A proposal of the source record. Never a fact. It binds only where a `DEC` adopts it, and then only to the extent the `DEC` states. |
| `PO3` | Proposed obligation | A WP-3 proposal for WP-4/maintainer decision from the original contract. Not accepted until reviewed. Where a `DEC` now decides the point, the row says so. |
| `UF` | Former unsupported-fact identifier | `UF-01` … `UF-18` are kept as identifiers; their evidence disposition is §6.1. A residual `R-nn.n` or a still-open `PSC` is never described as a supported fact. |
| `IO` | Integration observation | A point this integration run noticed while reconciling the evidence with the decisions (§6.3). It is neither a source fact nor a decision, and it decides nothing. |

A `PSC` that no `DEC` adopts is never used as a requirement. Where a `PO3` obligation
depended on a `UF`, its dependence is now stated against the evidence identifiers of §4.2.

## 2. Closed interface roster and call-site mapping

Closed roster (`SF`, R8 DI table lines 3791–3796; WP-2 §7.1 line 729): **DI-1**
unit-state read; **DI-2** create holder unit; **DI-3** create backstop timer and
service; **DI-4** disarm backstop timer; **DI-5** Polkit decision; **DI-6**
authorization subject; plus **DI-S**, the SA-2 stop-unit call. Seven interfaces,
no other. Mapping to all 41 WP-2 logical call sites (`MD`: parsed from WP-2
§7.1, inventory lines 743–783, by call-site identifier prefix):

| Call site | Interface | Procedure | Accepted act | Implementing row(s) | Governing closure | Note |
|---|---|---|---|---|---|---|
| `CALL-DI1-01` | DI-1 | RT-1 | CQ-4 OS-4: holder `ActiveState` and `InvocationID` | `RT1.CQ4.7` | Q3-1 |  |
| `CALL-DI1-02` | DI-1 | RT-1 | CQ-4 OS-1: capture unit `ActiveState`, `InvocationID`, `InactiveEnterTimestampMonotonic` | `RT1.CQ4.8` | Q3-1 | read during the unit's own start-pre (OS-1) |
| `CALL-DI1-03` | DI-1 | RT-2 | AM-0 (i): `LoadState` of three units (one stated act, three unit reads) | `RT2.AM0.5` | Q3-1 | unit that may be unloaded / not yet created (`LoadState`) |
| `CALL-DI1-04` | DI-1 | RT-2 | AM-0 (iii): capture-unit baseline under BSP (the BSP retries are this same site) | `RT2.AM0.12` | Q3-1 |  |
| `CALL-DI1-05` | DI-1 | RT-2 | AK-1: the backstop timer must be `active` | `RT2.AK1.3` | Q3-1 |  |
| `CALL-DI1-06` | DI-1 | RT-2 | AV-1 H-2b baseline recomputation: `unit` key | `RT2.AV1.2` composing `H-BSE.10` | Q3-1, Q3-9 |  |
| `CALL-DI1-07` | DI-1 | RT-2 | AV-1 H-2b baseline recomputation: `manager` key | `RT2.AV1.2` composing `H-BSE.11` | Q3-1, Q3-9 |  |
| `CALL-DI1-08` | DI-1 | RT-2 | `hold-start`: re-read while K is held | `RT2.HS.1` | Q3-1 |  |
| `CALL-DI1-09` | DI-1 | RT-2 | HL observation (the OS-5 decision's re-observation under the lock is this same site run again) | `RT2.HL.3`; re-run `RT2.HL.7` | Q3-1 |  |
| `CALL-DI1-10` | DI-1 | RT-3 | CL-2: capture-unit state | `RT3.CL2` composing `H-CL.2.1`, `H-DI1.1` | Q3-1 |  |
| `CALL-DI1-11` | DI-1 | RT-3 | CL-6: capture unit not active | `RT3.CL6` composing `H-CL.6.3` | Q3-1 |  |
| `CALL-DI1-12` | DI-1 | RT-3 | CL-6 baseline recomputation: `unit` key | `RT3.CL6` composing `H-BSE.10` | Q3-1, Q3-9 |  |
| `CALL-DI1-13` | DI-1 | RT-3 | CL-6 baseline recomputation: `manager` key | `RT3.CL6` composing `H-BSE.11` | Q3-1, Q3-9 |  |
| `CALL-DI1-14` | DI-1 | RT-4 | BS-1: holder `ActiveState` | `RT4.BS1.1` | Q3-1 |  |
| `CALL-DI1-15` | DI-1 | RT-4 | CL-2: capture-unit state | `RT4.CL2` composing `H-CL.2.1`, `H-DI1.1` | Q3-1 |  |
| `CALL-DI1-16` | DI-1 | RT-4 | CL-6: capture unit not active | `RT4.CL6` composing `H-CL.6.3` | Q3-1 |  |
| `CALL-DI1-17` | DI-1 | RT-4 | CL-6 baseline recomputation: `unit` key | `RT4.CL6` composing `H-BSE.10` | Q3-1, Q3-9 |  |
| `CALL-DI1-18` | DI-1 | RT-4 | CL-6 baseline recomputation: `manager` key | `RT4.CL6` composing `H-BSE.11` | Q3-1, Q3-9 |  |
| `CALL-DI1-19` | DI-1 | RT-5 | `attest` precondition: three unit-state reads (one stated act) | `RT5.PRE.1` | Q3-1 | units that may be `not-found` |
| `CALL-DI1-20` | DI-1 | RT-5 | CL-2: capture-unit state | `RT5.CL2` composing `H-CL.2.1`, `H-DI1.1` | Q3-1 |  |
| `CALL-DI1-21` | DI-1 | RT-5 | CL-6: capture unit not active | `RT5.CL6` composing `H-CL.6.3` | Q3-1 |  |
| `CALL-DI1-22` | DI-1 | RT-5 | CL-6 baseline recomputation: `unit` key | `RT5.CL6` composing `H-BSE.10` | Q3-1, Q3-9 |  |
| `CALL-DI1-23` | DI-1 | RT-5 | CL-6 baseline recomputation: `manager` key | `RT5.CL6` composing `H-BSE.11` | Q3-1, Q3-9 |  |
| `CALL-DI2-01` | DI-2 | SA-1 | AP-2: create the transient holder unit | `SA1.OP.2` | Q3-2 |  |
| `CALL-DI3-01` | DI-3 | RT-2 | AK-1: create the backstop timer and service | `RT2.AK1.2` | Q3-3 |  |
| `CALL-DI4-01` | DI-4 | RT-4 | BS-2: disarm after a `st1-verified` record | `RT4.BS2.2` | Q3-4 |  |
| `CALL-DI4-02` | DI-4 | RT-4 | BS-3: disarm after a `hard-stop` record with nothing further removable | `RT4.BS3.1` (decision and invocation), `RT4.BS2.2` (the disarm operation it invokes) | Q3-4 |  |
| `CALL-DI4-03` | DI-4 | RT-4 | BS-4 terminal disarm (`backstop_max` exceeded or `k` > 99) | `RT4.BS4.2` | Q3-4 |  |
| `CALL-DI5-01` | DI-5 | RT-1 | CQ-5: PK/2 seek-not-authorized for `start` — the decision | `RT1.CQ5.2` (PK/2 inside, `H-PK2.4`, `H-PK2.5`) | Q3-5, Q3-6 |  |
| `CALL-DI5-02` | DI-5 | RT-2 | AV-1 positive control: PK/2 seek-authorized for `start` — the decision | `RT2.AV1.3` (PK/2 inside, `H-PK2.4`, `H-PK2.5`) | Q3-5, Q3-6 |  |
| `CALL-DI5-03` | DI-5 | RT-2 | AV-1 negative control: PK/2 first-decisive for `stop` — the decision | `RT2.AV1.4` (PK/2 inside, `H-PK2.4`, `H-PK2.5`) | Q3-5, Q3-6 |  |
| `CALL-DI5-04` | DI-5 | RT-3 | CL-4: PK/2 seek-not-authorized for `start` — the decision | `RT3.CL4` composing `H-PK2.4`, `H-PK2.5` | Q3-5, Q3-6 |  |
| `CALL-DI5-05` | DI-5 | RT-4 | CL-4: PK/2 seek-not-authorized for `start` — the decision | `RT4.CL4` composing `H-PK2.4`, `H-PK2.5` | Q3-5, Q3-6 |  |
| `CALL-DI5-06` | DI-5 | RT-5 | CL-4: PK/2 seek-not-authorized for `start` — the decision | `RT5.CL4` composing `H-PK2.4`, `H-PK2.5` | Q3-5, Q3-6 |  |
| `CALL-DI6-01` | DI-6 | RT-1 | CQ-5: PK/2 seek-not-authorized for `start` — the subject created for it | `RT1.CQ5.2` (PK/2 inside, `H-PROC.1` … `H-PROC.5`) | Q3-6 |  |
| `CALL-DI6-02` | DI-6 | RT-2 | AV-1 positive control: PK/2 seek-authorized for `start` — the subject created for it | `RT2.AV1.3` (PK/2 inside, `H-PROC.1` … `H-PROC.5`) | Q3-6 |  |
| `CALL-DI6-03` | DI-6 | RT-2 | AV-1 negative control: PK/2 first-decisive for `stop` — the subject created for it | `RT2.AV1.4` (PK/2 inside, `H-PROC.1` … `H-PROC.5`) | Q3-6 |  |
| `CALL-DI6-04` | DI-6 | RT-3 | CL-4: PK/2 seek-not-authorized for `start` — the subject created for it | `RT3.CL4` composing `H-PROC.1`, `H-PROC.2`, `H-PROC.3`, `H-PROC.5` | Q3-6 |  |
| `CALL-DI6-05` | DI-6 | RT-4 | CL-4: PK/2 seek-not-authorized for `start` — the subject created for it | `RT4.CL4` composing `H-PROC.1`, `H-PROC.2`, `H-PROC.3`, `H-PROC.5` | Q3-6 |  |
| `CALL-DI6-06` | DI-6 | RT-5 | CL-4: PK/2 seek-not-authorized for `start` — the subject created for it | `RT5.CL4` composing `H-PROC.1`, `H-PROC.2`, `H-PROC.3`, `H-PROC.5` | Q3-6 |  |
| `CALL-DIS-01` | DI-S | SA-2 | OS-6 `stop`: stop-unit call for `rp11-capture-pass-a.service` | `SA2.OP.2` | Q3-7 |  |

Procedure-by-interface matrix (`MD`, same parse):

| Interface | RT-1 | RT-2 | RT-3 | RT-4 | RT-5 | SA-1 | SA-2 | Sites |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| DI-1 | 2 | 7 | 4 | 5 | 5 | — | — | 23 |
| DI-2 | — | — | — | — | — | 1 | — | 1 |
| DI-3 | — | 1 | — | — | — | — | — | 1 |
| DI-4 | — | — | — | 3 | — | — | — | 3 |
| DI-5 | 1 | 2 | 1 | 1 | 1 | — | — | 6 |
| DI-6 | 1 | 2 | 1 | 1 | 1 | — | — | 6 |
| DI-S | — | — | — | — | — | — | 1 | 1 |
| **All** | **4** | **12** | **6** | **10** | **7** | **1** | **1** | **41** |

## 3. Per-interface contract

Each interface section states, in order: the **adopted decisions** (`DEC`) that apply; the
**supported facts** (`SF`/`ASF`/`MD`/`DR`) with source-record identifiers; the **request,
response, value-encoding, completion, cancellation and failure** semantics those facts and
decisions fix; the **retained risks and residuals**; and the **later-package inputs** that
this file does not decide. No language, library, binding, parser, syscall sequence, buffer
size, retry algorithm or process-creation mechanism is chosen anywhere in this section.

### 3.0 Common contract

#### 3.0.1 Transport — `DEC` D-1

* `DEC` D-1: use the **system message bus** for DI-1, DI-2, DI-3, DI-4 and DI-S, and for DI-5
  as Polkit requires. Systemd's private manager socket is **not** selected. This keeps one
  authenticated transport locus, matches the accepted TR-4 (D line 940) and avoids a second
  transport contract. The source record's `PSC` P-01.1 candidate (T-A) is the one adopted;
  candidate (T-B) is not selected.
* `ASF` facts used (all tier as the record states): system-bus address and default socket
  A-01.1, A-01.2; the line-oriented authentication protocol, `EXTERNAL` identity as a numeric
  uid and the start of the message stream A-01.3; message framing, header fields, alignment
  and limits A-01.4; the mandatory first `Hello`, match rules through `AddMatch` and the fact
  that a client disconnects by closing the socket A-01.5; the shipped bus policy for the
  manager and for polkit A-01.6. A-01.7 … A-01.9 describe the private socket and why DI-5 needs
  the system bus in any case; they are retained as evidence and select nothing.
* Consequence of this decision, stated as fact: manager broadcast signals reach an API-bus
  client only if at least one client called `Manager.Subscribe()` (or the job is tracked) **and**
  the receiving client holds a match rule (A-05.10, A-01.5). `DEC` D-4 builds on this.
* **Retained risk.** The installed message-bus implementation, its version and its active
  policy are **not** assumed facts: they are recorded as residual **R-01.1** (the specification
  constrains protocol behaviour, not version-specific limits). R-01.2 (kernel credential
  passing with the initial NUL byte) and R-04.2 (the bus daemon's own error replies) stay open.
* **Not decided.** Connection lifetime and reuse, buffer sizes, read/write loop, timeout
  enforcement (Q4-7) and file-descriptor passing are WP-4's and are not designed here.

#### 3.0.2 Result discipline — `DEC` D-3

Every interface result is exactly one of `ok(value)`, `refused(reason)` or `error(kind)`;
DI-5 uses its own accepted three-way outcome (§3.5). There is no fourth state and no implicit
success (`PO3-C1`, retained; it is the vocabulary D-3, D-6 and D-9 are written in).

`DEC` D-3 adopts `PSC` P-04.1 **with only the already defined refusal cases**:

| Server or transport outcome | Contract result |
|---|---|
| DI-2 `org.freedesktop.systemd1.UnitExists` | `refused(exists)` |
| a method-specific `org.freedesktop.DBus.Error.InvalidArgs` raised **before mutation** | `refused(invalid-request)` |
| systemd `org.freedesktop.DBus.Error.AccessDenied` or `…InteractiveAuthorizationRequired`, where the manager refuses the requested operation | `refused(not-authorized)` |
| DI-4/DI-S `NoSuchUnit` | per D-9 (§3.4): `refused(not-loaded)` |
| a normal DI-5 challenge (not a D-Bus error) | per D-6 (§3.5): `not-authorized` |
| **every other** D-Bus ERROR; an unknown error name; a malformed, truncated or oversized reply; an authentication or service-availability error; a disconnect; `NoReply`; a transport timeout; a client deadline; an abandoned wait | `error(kind)` |

For a **mutating** interface (DI-2, DI-3, DI-4, DI-S) an `error` additionally carries the
accepted wording **`effect not confirmed`** and **never permits a silent retry**. The four
Polkit ERROR names (`Failed`, `Cancelled`, `NotSupported`, `NotAuthorized`; A-04.5) are **not**
mapped to `not-authorized`: D-6 maps only a well-formed normal reply.

* `ASF` facts used: ERROR message representation and the absence of any call-cancellation or
  reply-timeout rule on the wire A-04.1; the error names the pinned manager emits on these
  paths A-04.2; errno-style mapping is a client-library convention A-04.3; the sd-bus client's
  25 s default and `NoReply` are a reference-client default, not a wire property A-04.4;
  Polkit's errors A-04.5; a challenge is a normal reply A-04.6.
* The concrete `kind` vocabulary beyond the stable categories already named — `job-result`
  (D-4) and `invalid-reply` (D-6) — is a **WP-4** matter. **Q6-6 and Q6-7 are not decided by
  translating `effect not confirmed` to any new non-child `effect` field.**
* **Retained risks.** R-04.1 (error-name coverage is complete for the paths used, not for all
  D-Bus methods); R-04.2; R-13.3 (polkitd's error strings are not a stable contract: treat as
  an `error` kind only). **See also IO-3** (§6.3) for two points at which D-3's text and the
  evidence meet and which D-3 does not itself settle.

#### 3.0.3 Completion observation — `DEC` D-4

`DEC` D-4 selects `PSC` P-05.3 **O-C** for **DI-2, DI-3, DI-4 and DI-S**:

1. install the system-bus signal match and call `Manager.Subscribe()` **before** issuing the
   mutating method;
2. retain the returned job path and accept a `JobRemoved` completion only when that path and
   the expected unit match;
3. after completion, read the target unit state needed by the calling contract; and
4. treat the state read as an **observation**, not as a reconstruction of a lost
   `JobRemoved` result and not as proof that this request caused the state.

If the method reply is lost, the connection is lost, no matching signal is received before the
later WP-4 deadline, or the completion cannot be parsed, the result is `error` with
`effect not confirmed`, with no retry. A state read may be recorded as observed context but
**may not promote** that result to `ok` or `refused`. A `JobRemoved` result other than `done`
is `error(job-result)`. A `done` stop of a loaded already-inactive unit is D-9's benign no-op
(§3.4).

* `ASF` facts used: the reply to `StartUnit`/`StopUnit`/`StartTransientUnit` carries only the
  job path and **is not completion** A-05.5; `JobRemoved(u id, o job, s unit, s result)` on the
  Manager object, with the thirteen result values, and `JobNew` before it A-05.9; delivery
  conditions and the manual's recipe (subscribe/match first, call, filter by returned path)
  A-05.10; after removal the job no longer exists and only the unit's resulting state is
  readable A-05.11; `JobRemoved` is **not emitted while the manager reloads** A-05.8; a
  `canceled` result is not by itself proof that the requester cancelled it A-05.7.
* The expected unit is the unit named by the call's job: the holder `⟨id⟩.service` (DI-2);
  the backstop **timer** `⟨id⟩-backstop.timer` (DI-3 — the single start job is queued for the
  main unit only, A-08.1); the backstop timer (DI-4); `rp11-capture-pass-a.service` (DI-S).
* This decides the **observation design**, not the deadline mechanism (**Q4-7**), the meaning
  of `effect: "unknown"` for a non-child call (**D-8/Q6-6**) or its possible BS-4 extension
  (**Q6-7**). It also answers `PSC` P-05.4 (what a design relying on O-A does when no signal
  arrives): `error`, `effect not confirmed`, no retry.
* **Not covered by D-4.** What happens if the match installation or `Subscribe()` itself fails
  before the mutating method is issued: D-3's catch-all `error(kind)` applies and no further
  meaning is assigned (**IO-4**, §6.3). `Subscribe()` by an already-subscribed client yields
  `…AlreadySubscribed` (A-04.2); its handling is a WP-4 detail.

#### 3.0.4 Cancellation and abandonment (retained from R1, reconciled with `DEC` D-3/D-4)

Two different things are called cancellation and this file never merges them.
**Cancelling a client wait** is the client ceasing to wait for, or losing its connection to, a
call or a job result. **Cancelling a manager job** is a request that the manager stop a queued
or running job.

* `ASF` A-05.1 (`W`): the D-Bus specification defines **no message that cancels a method
  call**, no server-visible "client stopped waiting" notification, no per-call timeout and no
  rule for what a service does when the caller's connection closes.
* `ASF` A-05.2 (`R`): a reference client abandons a wait by letting its own timeout elapse,
  closing the connection or dropping its match; none of these is communicated to the manager as
  "cancel".
* `ASF` A-05.3 (`S`): the only ways to cancel a manager job are `Manager.CancelJob(u id)` and
  `Job.Cancel()`; each needs `manage-units` unless the caller owns the job, and the manual
  states that cancellation "will not have any effect on jobs whose execution has already
  begun". **No DI roster entry requests job cancellation; none is part of this contract.**
* `ASF` A-05.4 (`S`): a job is bound to the manager, not to a connection; a service or timer job
  is **not** collected because its requester disconnected or timed out. A-05.6 (`S`, an
  absence finding over the cited functions, stated as such): no source examined makes the
  server undo anything because a reply could not be delivered. A-05.12 (`S`, absence finding):
  a failure inside `StartTransientUnit` after the unit is made transient leaves a transient unit
  in memory without a job. A-05.13: `StartUnit`/`StopUnit` on a name that is not loaded first
  loads it, so even a refused `StopUnit` can load a stub.
* Consequently, and by `DEC` D-3/D-4: **a cancelled client wait, a client disconnection, a
  client deadline, an abandoned wait and an unconfirmed outcome are each `error` for the
  cancelled call; none is `ok` or `refused`.** For a mutating interface the `error` carries
  `effect not confirmed`; it is **never proof that the request had no effect and never proof
  that a queued job stopped**, and **no silent retry follows** (`PO3-X1`, `PO3-X2`: now decided
  by D-3 for the interface result; the child-form SN-10/A-I-16 `effect: "unknown"` rule is `DR`
  and its mapping to a non-child call stays **Q6-6**).
* `PO3-X3` (retained): a cancelled wait on a read (DI-1) yields `error` and never a value; a
  read starts, stops and changes nothing except possibly loading a stub (A-02.7), so no
  unknown-effect question arises for it.
* `ASF` R-05.1 / R-05.2: the installed bus's behaviour when a client disconnects with a service
  reply pending is not in any examined source; all behaviour is source-derived, none was
  executed. A WP-4 design must treat a lost reply as lost.

| Interface | Cancellation / abandonment treatment after integration | Class | Evidence | Still open |
|---|---|---|---|---|
| DI-1 | A cancelled or interrupted read is `error`, never a value. No job, no unknown-effect question | `DEC` D-3 (`PO3-1.4`, `PO3-X3` retained) | A-05.1, A-02.7, A-14.1 | Q4-7 (deadline) |
| DI-2 | Wait cancellation, deadline, disconnect, lost reply: `error`, `effect not confirmed`, no retry. The accepted job continues (A-05.4); a post-`unit_make_transient` failure leaves a jobless transient unit (A-05.12) | `DEC` D-3, D-4 | A-05.1 … A-05.6, A-05.12 | whether DI-2 is inside SN-10 and the `effect` wording for a non-child call: Q6-6; Q4-7 |
| DI-3 | As DI-2; the timer and/or its auxiliary service may exist without a queued job after a late failure; stopping the timer does not stop the service (A-09.6). Child-form `effect: "unknown"` is `DR` (SN-10/A-I-16) | `DEC` D-3, D-4 + `DR` | A-05.1 … A-05.6, A-05.12, A-09.6 | Q6-6; Q4-7; BS-RM citation (OH-S2b) |
| DI-4 | As DI-2 (three sites). The stop job runs to its result. SN-10 is `DR` at BS-2 and BS-3; **BS-4 is not extended** | `DEC` D-3, D-4 + `DR` | A-05.1 … A-05.6, A-09.4 | Q6-6 (BS-2, BS-3); **Q6-7 (BS-4)**; Q4-7; Q4-11 |
| DI-5 | A client that stops waiting changes no polkitd state; `CancelCheckAuthorization` is moot for a non-interactive check; the cancellation id is empty. An abandon is `error` | `DEC` D-2, D-6 + `DR` H-PK2.5 | A-10.7, A-10.8, A-10.9 | Q4-7 |
| DI-6 | No client wait of its own. Cancellation belongs to the enclosing DI-5 decision and to the later cleanup of the subject under the accepted SN contract (`DR` H-PROC.1, H-PK2.7: signalled once after the call; a failed, unmade or unreaped subject is abandoned or `reap-unknown`, recorded, living at most 60 s) | `DR` | A-10.8 (via DI-5) | Q4-1, Q4-8 (mechanics) |
| DI-S | As DI-2 (one site, SA-2). The accepted text states no failure contract for the stop call (SA2.OP.2); the interface-level result is D-3's | `DEC` D-3, D-4, D-9 | A-05.1 … A-05.6, A-09.4 | whether DI-S is inside SN-10: Q6-6; Q4-7; Q4-11 |

#### 3.0.5 The `effect not confirmed` wording and the Q6-6 / Q6-7 boundary

* `DEC` D-3's wording **`effect not confirmed`** is the accepted annotation of a mutating
  interface's `error`. It is **not** the answer to Q6-6 and it is **not** a new non-child
  `effect` field.
* `DR` SN-10 / A-I-16 (R8 lines 2521, 3212; W2 inventory §8.1): a mutating **child** whose
  result is `error`, interrupted or indeterminate has an *unknown* effect, no later step may
  read it as "not created" or "not stopped", and no retry, repetition or search is granted.
  W2 carries the obligation unmapped for non-child interactions (Q6-6, Q6-7). **That mapping is
  not decided here.** Q6-7 (the BS-4 extension) is not answered by the fact that D-3's
  annotation applies to every DI-4 site.
* `DR` WP-2 Q4-7: enforcing the class-E deadline `c`, including cancellation, the fail-closed
  `error` at expiry and behaviour after expiry, on an in-process interface call is a WP-4
  question. `PO3-C2` (retained): no interface call carries an elapsed-time bound claimed by
  WP-3.

### 3.1 DI-1 — unit-state read (23 call sites)

*Decisions applied.* `DEC` D-1 (system bus); `DEC` D-3 (every DI-1 ERROR, deadline or abandon is
`error(kind)`; D-3 defines no refusal case for a read); `DEC` D-4 step 3 (the post-completion
state read of DI-2/3/4/S is a DI-1 read, an observation only).

*Supported — design requirements.*

* `DR` H-DI1.1 (inventory line 252): obtain named properties of one named unit, read-only. The
  properties used are `ActiveState`, `InvocationID`, `InactiveEnterTimestampMonotonic`, `Job`,
  `LoadState`, `Result`, and for baselines `ExecMainStartTimestampMonotonic` and
  `TimeoutStartUSec`; these eight are `MD` all present in R2 Appendix A (rows #7, #169, #166,
  #170, #215, #343, #101, #436) and none carries `HIDDEN` or `EXPLICIT` (A-03.1, A-14.3).
* `DR` H-DI1.2 (line 253): value text is the exact bytes after the first `=` of the printed
  form, decoded as strict UTF-8; a failed decode is a stop; a property the manager does not
  report is a stop, enforced by the reader because the reference tool does not fail (`SF` R2
  line 481: a `-p` name the manager does not return is skipped, exit 0).
* `DR` H-DI1.3 (line 254): reads start, stop and change nothing; reading an unloaded unit may
  load it; a read made during the unit's own start-pre returns without waiting and reports
  `activating`, the attempt's `InvocationID` and the earlier τ. `DR` H-DI1.4 (line 255): a
  satisfied read is never evidence of absence; `InvocationID` of an `inactive` unit may be
  stale and `InactiveEnterTimestampMonotonic` may read `0`.

*Supported — source record.*

* **Name to object (A-02.1, A-02.2, `ASF/S`, `MD`).** The unit object path is
  `/org/freedesktop/systemd1/unit/` followed by `bus_label_escape(name)`: the empty string
  maps to `_`; ASCII letters, and digits except as first character, are copied; every other
  byte is `_` plus two **lowercase** hexadecimal digits. The path is **computed by the client**;
  no `GetUnit`/`LoadUnit` is issued for it. `rp11-capture-pass-a.service` →
  `/org/freedesktop/systemd1/unit/rp11_2dcapture_2dpass_2da_2eservice`.
* **Unloaded units (A-02.3, A-02.5, A-02.6, A-02.7, `ASF/S`).** A property access on a unit path
  loads the unit if it is not loaded, creating an in-memory stub even when no unit file exists;
  `GetUnit` is the loaded-only form and `LoadUnit` the loading form. A loaded unit without a
  unit file reports `LoadState` `not-found`. A read therefore *changes manager state* (a stub is
  loaded and later garbage-collected) but starts, stops and creates no job; a later read of an
  inactive unit may find it unloaded again. A path whose label unescapes to a 128-bit ID is
  looked up as an invocation ID (`NoUnitForInvocationID` if absent). A malformed path reaches
  the client as `…UnknownObject`, not `InvalidArgs` (A-02.4).
* **Methods (A-14.1, A-14.2, A-14.4, `ASF/S`, `W`).** `Properties.Get(interface, property)`
  answers by exact `(path, interface, member)`; `Properties.GetAll(interface)` omits `HIDDEN`
  and `EXPLICIT` properties; a wrong interface/name pair is `…UnknownProperty`. **A per-property
  `Get` can read a `HIDDEN` or `EXPLICIT` property that `GetAll` omits** (A-14.3, `MD`): the
  pinned tree has 28 hidden Unit/Service and 5 hidden Manager entries and no `EXPLICIT` one;
  all eight DI-1 properties and every property of R2 Appendices A and B are visible, so no
  DI-1 use depends on this. The contract does not select `Get` or `GetAll`.
* **Wire types and text rules for the eight DI-1 properties** (source record §3 `UF-03` table;
  rules A-03.3 … A-03.7). The wire signatures and server encodings are `ASF/S`/`W`; the
  printed-text column is the behaviour of the reference client `systemctl show -p` (`ASF/R`,
  never a contract):

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

* **Typed-to-text.** Reproducing the printed text H-DI1.2 expects from a **typed** value is a
  separate, fully determined computation per signature and per property name (A-03.3 …
  A-03.7); it is *determined* for the eight properties above. Whether the **baseline** is
  compared as reproduced printed text or as typed values is **D-7 / Q6-2 — undecided here**
  and belongs to Q3-9 (§3.8).

*Request, response, value encoding, completion, cancellation, failure.*
`PO3-1.1` Request = (unit name, ordered list of property names) on the system bus (`DEC` D-1);
response = for each name either `value(text)` per H-DI1.2 or `absent`, never both, order
preserved. `PO3-1.2` `absent` for a name in the baseline set is a stop (H-DI1.2). `PO3-1.3` A
read completes when all names are answered (one METHOD_RETURN, no job: A-14.1); no partial
result is returned. `PO3-1.4` A cancelled or interrupted read yields `error`, never a value —
now `DEC` D-3. Every DI-1 ERROR (`UnknownObject`, `UnknownProperty`, `InvalidArgs`,
`NoUnitForInvocationID`, `NoReply`, `Disconnected`, …) is `error(kind)`: D-3 defines no
`refused` case for a read, so a read can never be softened to a refusal.

*Retained risks and residuals.* R-01.1 (installed broker), R-01.2, R-02.1 (garbage-collection
timing of a loaded stub: no accepted DI-1 use needs it, because a satisfied read is never
evidence of absence), R-03.1 (the version-bound baseline property list is a repository artifact
outside the required reading: **Q3-9**), R-03.2 (locale/timestamp-style details not re-derived:
Q6-2), R-03.3 (the 11 + 21 `Timestamp` properties are excluded from the baseline's compared
set by accepted D 4.3.3 text), R-04.1, R-04.2, `O-2` (the manual lists fewer modes/results
than the source; the source governs).

*Later-package inputs (not decided).* Q4-7 (deadline); Q6-2/D-7 (typed versus printed baseline
text).

*State.* **Q3-1: closure-ready** on A-01.x, A-02.x, A-03.x, A-04.x, A-14.x, D-1, D-3 and D-4(3);
**not closed**. The DI-1 half of Q3-9 stays open (§3.8).

### 3.2 DI-2 — create holder unit (1 call site: SA-1)

*Decisions applied.* `DEC` D-1; `DEC` D-3 (`UnitExists` is `refused(exists)`); `DEC` D-4 (O-C
completion observation).

*Supported — design requirements.* `DR` SA1.OP.2 (inventory line 583): create the holder
`⟨id⟩.service` as one transient system service of type `exec` carrying the accepted AP-2
properties in one `StartTransientUnit`-equivalent call; its only effect is the transient
holder unit. `SF` D line 1989: the holder literal.

*Supported — source record.*

* **Method (A-06.1, `ASF/W`).** `org.freedesktop.systemd1.Manager.StartTransientUnit`, input
  signature `ssa(sv)a(sa(sv))` = `name`, `mode`, `properties`, `aux`; output `o` (the job
  object path). The method is `SD_BUS_VTABLE_UNPRIVILEGED` and "Managed via polkit".
* **Authorization first (A-06.4, A-09.5, `ASF/S`).** The Polkit check (action
  `org.freedesktop.systemd1.manage-units`, details `unit` = the new unit name, `verb` = `start`)
  runs **before** any unit is created; a caller treated as privileged (effective uid equal to
  the manager's) skips Polkit.
* **Mode (A-06.2, A-06.3).** `mode` must be accepted by `job_mode_from_string`; an unknown string
  is refused before any other effect with `InvalidArgs`. The ten valid strings and their
  constraints are in A-06.2; the job type is always start. **No accepted record and no adopted
  decision selects the string** (**IO-2**, §6.3).
* **Properties on the wire (A-07.1 … A-07.4, `ASF/S`, `MD`).** Server-side transient setters
  accept only the `…USec` spellings (`t`, microseconds); the `…Sec` spellings of the accepted
  command-line literals exist only in a client's parser (A-07.1). For the holder: `Type "exec"`
  (`s`), `Restart "no"` (`s`), `OOMScoreAdjust -1000` (`i`), `RuntimeMaxUSec ⟨L⟩·10⁶` (`t`),
  `TimeoutStopUSec ⟨S⟩·10⁶` (`t`), `ExecStopPost` and `ExecStart` each `a(sasb)` with one
  element `(path, complete argv including argv[0], ignore-failure=false)` (A-07.2: `argv[0]` is
  independent of `path`; a command with no argv is refused). The `Ex` form `a(sasas)` is used
  only if a modifier requires it. The setting is also written as text for the unit,
  specifier-escaped, and `$VAR` is environment-expanded at exec time unless the `Ex` form carries
  `no-env-expand`; the accepted literals contain neither `%` nor `$` (A-07.3, R2 §8 (b)).
  `aux` carries no auxiliary unit for the holder (`DR` SA1.OP.2: its only effect is the holder).
* **Refusal and partial effect (A-02.6, A-04.2, A-05.12, A-06.5).** A name that is loaded, has a
  fragment or source path, a job, or is merged is refused with `…UnitExists`; a "pristine"
  stub (`not-found`/`loaded`, no fragment, no job, not merged) does not block creation. The
  handler checks mode, runs the Polkit check, then loads the main unit and marks it transient,
  applies `properties` in a two-pass walk (validate all pairs, then apply), creates every `aux`
  unit and only then queues the start job. **Errors in the mode check and the Polkit check
  leave no state; the cited bodies contain no rollback of the transient unit if a later step
  fails** (absence finding): an error after the unit is made transient leaves a transient unit
  in memory without a job.

*Request, response, value encoding.* Request = the call above on the system bus (`DEC` D-1).
Response = the job path `o`. The reply **is not completion** (A-05.5).

*Completion.* `DEC` D-4 O-C (§3.0.3): match + `Subscribe()` first, accept `JobRemoved` for the
returned path and unit `⟨id⟩.service`, then read the holder's state (`ActiveState`, `Job`,
`Result`, `InvocationID`) as observation only.

*Failure mapping (`DEC` D-3; IO-3 states two boundary points).*

| Outcome | Result |
|---|---|
| `…UnitExists` | `refused(exists)` |
| `InvalidArgs` raised by the mode check or by the unit name/type check, before the unit is made transient (A-06.2, A-04.2, A-05.12(a)) | `refused(invalid-request)` |
| `AccessDenied` / `InteractiveAuthorizationRequired` from the authorization step (A-04.2) | `refused(not-authorized)` |
| `InvalidArgs` / `PropertyReadOnly` / a property-setter error raised after the unit is made transient (A-06.5, A-05.12) | `error(kind)`, `effect not confirmed` |
| `JobRemoved` result other than `done` | `error(job-result)` |
| reply lost, connection lost, no matching signal before the WP-4 deadline, unparsable completion, every other ERROR | `error(kind)`, `effect not confirmed`, no retry |

*Cancellation.* §3.0.4: abandonment never proves the holder was not created and never permits
a silent retry. Class: `DEC` D-3; DI-2 is not named by SN-10.

*Retained risks and residuals.* R-05.1, R-05.2, R-06.1 (per-type setter errors not
enumerated), R-06.2 (unused modes not analysed), R-07.1 … R-07.3; `O-2` (the manual calls `aux`
"unused" but this version processes it).

*Later-package inputs (not decided).* **Q6-6** (whether DI-2 is inside SN-10 and the meaning of
`effect: "unknown"` for a non-child call, with D-8); Q4-7.

*State.* **Q3-2: closure-ready** on A-05.x, A-06.x, A-07.x, A-02.6, D-1, D-3, D-4; **not closed**.

### 3.3 DI-3 — create backstop timer and service (1 call site: RT-2 AK-1)

*Decisions applied.* `DEC` D-1; `DEC` D-3; `DEC` D-4; `DEC` D-10.

*Supported — design requirements.* `DR` RT2.AK1.2 (line 457): create `⟨id⟩-backstop.timer`
firing at `--on-active=⟨R⟩` and `--on-unit-active=⟨R⟩` with `AccuracySec=1s`, and
`⟨id⟩-backstop.service` (type `exec`, `Restart=no`, `OOMScoreAdjust=-1000`,
`RuntimeMaxSec=⟨S_b⟩`, `TimeoutStopSec=⟨S⟩`, **no `TimeoutStartSec=`**, role `backstop`).
`SF` R2 §8 (d), (j); `SF` D line 2009: backstop literal. `DR` SN-10 / A-I-16: the
`effect: "unknown"` obligation applies to this call as a historical child; its mapping is
**Q6-6 and is not decided here**. Carried dependency, not owned by WP-3: the `RuntimeMaxSec`
on a timer-started `Type=exec` service (BS-RM) is adopted by DEC-2 but its citation obligation
(OH-S2b) is still proposed.

*Supported — source record.*

* **One call (A-08.1, `ASF/S`+`R`).** A timer and its service are created in **one**
  `StartTransientUnit` call: `name` is the timer, `properties` are the timer's properties, and
  `aux` carries one element `(service name, a(sv) service properties)`. The server creates the
  main unit, then every `aux` unit through the same path, then queues the start job for the
  **main (timer) unit only**. The manual calls `aux` "unused"; this version uses it (`O-2`).
* **Naming relation (A-08.3).** A timer without an explicit trigger triggers the same-prefix
  `.service` and gains `Before=` and `Triggers=` on it; the Timer interface's `Unit` property
  (`s`) reports the triggered unit. The reference client derives the other suffix from a
  `.timer`/`.service` name (A-08.2).
* **Write-side timer properties (A-08.4).** `AccuracyUSec t`, `RandomizedDelayUSec t`,
  `RandomizedOffsetUSec t`, `FixedRandomDelay b`, `WakeSystem b`, `Persistent b`,
  `RemainAfterElapse b`, `OnTimezoneChange b`, `OnClockChange b`, `DeferReactivation b`,
  **`TimersMonotonic a(st)`** (base name, µs) and `TimersCalendar a(ss)`. A `TimersMonotonic`
  base must be one of `OnActiveSec`, `OnBootSec`, `OnStartupSec`, `OnUnitActiveSec`,
  `OnUnitInactiveSec`; any other base (including `OnCalendar`) is `InvalidArgs`. The read-side
  Timer interface has 18 properties (A-08.5; `TimersMonotonic` is `a(stt)` there).
* **For the accepted backstop (A-08.7, A-07.4, `MD`):** `name` = `⟨activation_id⟩-backstop.timer`;
  `properties` = `TimersMonotonic [("OnActiveSec", R·10⁶)]`, `TimersMonotonic
  [("OnUnitActiveSec", R·10⁶)]`, `AccuracyUSec 1000000`; `aux` =
  `[(⟨activation_id⟩-backstop.service, service properties)]`. `RemainAfterElapse false` is a
  client convention, not required by the accepted rows (R-08.2).

*`DEC` D-10 — backstop service timeout property.* Follow accepted WP-2 row `RT2.AK1.2` and
BS-RM: **the DI-3 backstop service has no `TimeoutStartUSec` property.** Its relevant
properties remain `Type=exec`, `Restart=no`, `OOMScoreAdjust=-1000`,
`RuntimeMaxUSec=⟨S_b⟩·10⁶`, `TimeoutStopUSec=⟨S⟩·10⁶` and the accepted `ExecStart`
(wire spellings per A-07.1/A-07.4). This decision resolves **only** the conflicting
`TimeoutStartSec=⟨S⟩` literal in D R2 (f) for the LIT-FULL DI-3 contract (R-08.1, `O-3`); it
does not rewrite the historical source. *Clarification:* `TimeoutStartUSec` remains one of the
eight properties DI-1 *reads* (§3.1) — D-10 concerns what DI-3 *sets*.

*Completion.* `DEC` D-4 O-C: expected unit = the backstop **timer**; then read the timer's
`ActiveState`/`LoadState` and the `Triggers`/`Unit` link as observation only.

*Failure mapping (`DEC` D-3).* As §3.2 with these differences: D-3 names `UnitExists` for DI-2
only, so the same server error from this call is `error(kind)`, `effect not confirmed` — it is
not extended (**IO-3(a)**); a failure after step (c) of A-05.12 may leave the timer unit and/or
its auxiliary service in memory without a queued job; stopping the timer later does not stop
the service (A-09.6). Child-form `effect: "unknown"` (SN-10/A-I-16) is `DR`; its mapping to
this non-child call is **Q6-6**.

*Cancellation.* §3.0.4. Abandonment never proves the timer or service was not created and
never permits a silent retry.

*Retained risks and residuals.* R-05.1, R-05.2, R-06.x, R-07.x, R-08.1 (resolved for this
contract by D-10; the historical source is unchanged), R-08.2.

*State.* **Q3-3: closure-ready** on A-05.x, A-06.x, A-07.x, A-08.x, A-09.6, D-1, D-3, D-4, D-10;
**not closed**.

### 3.4 DI-4 — disarm backstop timer (3 call sites: BS-2, BS-3, BS-4)

*Decisions applied.* `DEC` D-1; `DEC` D-3; `DEC` D-4; `DEC` D-9.

*Supported — design requirements.* `DR` RT4.BS2.2 (line 531): stop `⟨id⟩-backstop.timer`, the
only unit verb the backstop issues; BS-3 (RT4.BS3.1, line 532) invokes the same operation;
BS-4 (RT4.BS4.2, line 534) is the terminal disarm (`CALL-DI4-03`). `SF` R2 §6.2 (lines
625–627): the stop verb is Polkit-checked for non-root callers. `DR` WP2-R2-2 (inventory line
27): SN-10 / A-I-16 applies to BS-2 and BS-3 only; whether it extends to BS-4 is **not decided**
and is carried as part of **Q6-7**.

*Supported — source record.*

* **Method (A-09.1, `ASF/W`).** `StopUnit(s name, s mode) → o job`. The valid mode strings are
  those of A-06.2 except that `isolate` and `restart-dependencies` are invalid for stop
  (`InvalidArgs`) and `triggering` is valid only for stop. The mode string is not selected
  (**IO-2**, §6.3).
* **Flow (A-09.2, A-05.13, `ASF/S`).** The unit is loaded by name (creating a stub when no unit
  file exists); the mode is parsed; the Polkit check with verb `stop` runs; then the job is
  queued. **Even a refused `StopUnit` can therefore load a stub**; `refused(not-loaded)` does
  not mean the manager's state was untouched.
* **Root caller (A-09.5, `ASF/S`).** The authorization helper returns "authorized" **without
  querying Polkit** when the sender is privileged (effective uid equal to the manager's), unless
  the action was registered `ALWAYS_QUERY` (the manage-units helper does not set it).
* **Results by state (A-09.3, A-09.4, A-09.7, `ASF/S`, `MD`)** for `StopUnit(timer, mode)` from
  a root caller: (i) loaded and active ⇒ reply `o`, later `JobRemoved … done`; (ii) loaded and
  inactive or failed ⇒ reply `o`, `JobRemoved … done` (no state change; `unit_stop` returns
  `-EALREADY`, which ends the job `done`); (iii) not loaded (`not-found`, `bad-setting` or
  `error` load state and inactive) ⇒ ERROR `…NoSuchUnit` "Unit %s not loaded.", **no job is
  queued**; (iv) invalid mode ⇒ `InvalidArgs`, no job. A frozen unit ends `frozen`
  (`-EDEADLK`); a unit with `RefuseManualStop` is refused before queueing with `…OnlyByDependency`.
* **Stopping a timer (A-09.6).** `timer_stop` moves the timer to its dead state; the triggered
  `.service` is a separate unit and is **not** stopped by this operation. Transient units are
  released as soon as they are not running or referenced anymore.

*`DEC` D-9 — stop of an inactive or not-loaded unit.* Distinguish the two facts rather than
merging them:

* loaded and already inactive/failed, followed by `JobRemoved … done`, is
  **`ok(already-stopped)`**; and
* `NoSuchUnit` before a job is queued is **`refused(not-loaded)`**.

Apply this to DI-4 and DI-S. **Do not infer from either result that a different earlier request
had no effect.** The special fact is preserved: a transient unit that has already been
collected after a prior stop is in the not-loaded case (iii). The `PSC` P-09.1 alternative
(merging the two) is not selected.

*Request, response, completion.* Request = the call above on the system bus (`DEC` D-1).
Response = the job path. Completion: `DEC` D-4 O-C with expected unit = the backstop timer; the
post-completion read of `ActiveState`/`LoadState` is an observation and cannot turn a lost
completion into `ok(already-stopped)` or any other success.

*Failure mapping (`DEC` D-3, D-9).*

| Outcome | Result |
|---|---|
| `JobRemoved … done` after a stop of a loaded unit | `ok` (D-9 `already-stopped` where the unit was loaded and already inactive/failed — see IO-1) |
| `NoSuchUnit`, no job queued | `refused(not-loaded)` |
| invalid-mode `InvalidArgs`, no job queued | `refused(invalid-request)` |
| `AccessDenied` / `InteractiveAuthorizationRequired` | `refused(not-authorized)` |
| `JobRemoved` result other than `done` (e.g. `frozen`, `skipped`, `canceled`) | `error(job-result)` |
| reply lost, connection lost, no matching signal before the WP-4 deadline, unparsable completion, every other ERROR (including `OnlyByDependency`) | `error(kind)`, `effect not confirmed`, no retry |

**IO-1** (§6.3): the evidence shows `JobRemoved … done` is the same signal for a stop that
stopped an active unit and for the `-EALREADY` no-op (A-05.9, A-09.4, A-09.7); D-4(4) forbids
reading the later state as proof of causation. The source of the fact "the unit was loaded and
already inactive/failed *when the stop ran*" is therefore not supplied by the evidence or by
D-9 and is left to WP-4 and to the independent review. It is not invented here.

*Cancellation.* §3.0.4. Abandonment never proves the timer was or was not stopped, nor that a
queued job stopped; no silent retry. At BS-2 and BS-3 the child-form unknown-effect rule is `DR`
(mapping **Q6-6**); at **BS-4 no SN-10 text exists and Q6-7 is not answered**: D-3's annotation
is the interface result, not an extension of SN-10.

*Retained risks and residuals.* R-05.1, R-05.2, R-09.1 (a stop arriving for a unit in start-pre:
accepted R2 PO-21 (u), carried), R-09.2.

*Later-package inputs (not decided).* Q6-6 (BS-2, BS-3), **Q6-7 (BS-4)**, Q4-7, Q4-11.

*State.* **Q3-4: closure-ready** on A-09.x, A-05.x, D-1, D-3, D-4, D-9; **not closed**.

### 3.5 DI-5 — Polkit decision (6 call sites)

*Decisions applied.* `DEC` D-1 (system bus, as Polkit requires); `DEC` D-2 (request);
`DEC` D-3 (errors); `DEC` D-6 (result mapping).

*Supported — design requirements.* `DR` H-PK2.4 (line 275): ask the authorization authority,
as root and without interaction, for action `org.freedesktop.systemd1.manage-units` with
details `unit` = `rp11-capture-pass-a.service` and `verb` = the series verb, for the subject of
H-PROC.5. `DR` H-PK2.5 (line 276): one outcome — `authorized`, `not-authorized` or `error`; any
unparsable result, deadline or abandon is `error`; volume cap 65,536 bytes. `DR` R8 §9.3 E-2
(line 3808): the `pkcheck` exit-status mapping is a command-line contract that **does not carry
over** to an interface.

*Supported — source record.*

* **Method (A-10.1, A-10.2, `ASF/W`).** Well-known name `org.freedesktop.PolicyKit1`, object
  `/org/freedesktop/PolicyKit1/Authority` (the interface XML's prose misspells it), interface
  `org.freedesktop.PolicyKit1.Authority`, on the **system** bus. `CheckAuthorization` input
  `(sa{sv}) s a{ss} u s` = `subject`, `action_id`, `details`, `flags`, `cancellation_id`;
  output `(bba{ss})` = `is_authorized`, `is_challenge`, `details`.
* **Flags and details (A-10.3, A-10.4).** Flags: `NONE` = 0, `ALLOW_USER_INTERACTION` = `1<<0`,
  `ALWAYS_CHECK` = `1<<1`. `details` is `a{ss}`; keys beginning `polkit.` are reserved. **Only
  uid 0 (or an action owner) may pass details** or ask about another identity's subject;
  otherwise `…Error.NotAuthorized`.
* **Subject kinds (A-10.5, A-10.6, A-10.10, A-10.12).** The decoder reads a `unix-process`
  subject in two forms. General PID/start-time form: `pid` (`u`) and `start-time` (`t`)
  required, `uid` (`i`) optional. Pidfd form (only with a file-descriptor list and a `pidfd`
  key of type `h`): `uid` required. `pkcheck --process pid,start,uid` puts on the wire subject
  `("unix-process", {pid u, start-time t, uid i})`, **no `pidfd`**, the action, `details
  {unit, verb}`, flags `0` and an empty cancellation id (A-10.10); the libpolkit encoder always
  writes `pid`, `start-time` and `uid` and adds `pidfd` only when its safety flag is set
  (A-10.12).
* **Cancellation (A-10.7, A-10.8, A-10.9).** `cancellation_id` is the empty string if
  cancellation is not needed; polkitd creates a cancellable only for a non-empty id, and the
  cancellable is consulted **only** for an interactive challenge. A non-interactive request
  (flags `NONE`) completes inside the call and is unaffected by `CancelCheckAuthorization`; a
  client that abandons it changes no polkitd state.
* **Results (A-10.11, A-04.6, A-11.1 … A-11.3).** polkitd never constructs a result with both
  booleans true: it returns `(true,false)` authorized, `(false,true)` challenge or
  `(false,false)` not authorized; an unregistered action is a `Failed` ERROR. A challenge is a
  normal METHOD_RETURN, not an error. `pkcheck`'s own mapping (call failure ⇒ 127, authorized
  ⇒ 0, challenge ⇒ 2, dismissed ⇒ 3, else 1) is a reference-client rule that does not carry
  over; `polkit.dismissed` arises only from an interactive challenge, which flags `0` cannot
  reach (A-11.2).

*`DEC` D-2 — the DI-5 request.* Select `PSC` P-10.1 shape **S-A**: `CheckAuthorization` with
subject **`("unix-process", {pid u, start-time t, uid i})`**, action
**`org.freedesktop.systemd1.manage-units`**, details containing **exactly `unit` and `verb`**,
flags **`0`**, and an **empty cancellation id**. The supplied `uid` is deliberate: the general
PID/start-time decoder permits it to be absent (A-10.6), but the accepted H-PROC.5 obtains it
and this contract requires it. Shape S-B (`pidfd` + `uid`) is not selected.

*`DEC` D-6 — result mapping (`PSC` P-11.1).* For a well-formed `(bba{ss})` reply:

| `is_authorized` | `is_challenge` | DI-5 outcome |
|---|---|---|
| true | false | `authorized` |
| false | false or true | `not-authorized` |
| true | true | `error(invalid-reply)` |

Every D-Bus ERROR (including the four Polkit names and the bus's own `ServiceUnknown` and
`NoReply`), a wrong signature, a malformed, truncated or oversized reply, a deadline and an
abandon is `error` under D-3. The returned details map is **not** used to alter these three
outcomes. A challenge is `not-authorized`, never `error` (`PO3-5.2`, matching the accepted
H-PK2.5 table).

*Failure and cancellation.* The call is non-interactive, so cancellation of the Polkit call is
moot (A-10.8); an abandon is `error` (`DR` H-PK2.5). A subject whose start time no longer
matches `/proc` produces an ERROR, not an authorization result (A-13.1; §3.6), hence `error`.

*Retained risks and residuals.* R-10.1 (whether the installed polkitd was built with
`HAVE_PIDFD_OPEN`; not inspected), R-10.2, R-11.1 (whether the accepted 65,536-byte volume cap
has a D-Bus counterpart is not decided by any source; D-6's "oversized" therefore has no
threshold here: WP-4, Q4-5/Q4-11), R-13.3, A-13.5 (**a root subject is authorized for any
action without consulting policy unless `ALWAYS_CHECK` is set** — with flags `0` this governs
what a uid-0 subject can show), `O-5` (the XML prose and the decoder differ; the decoder governs).

*Later-package inputs (not decided).* Q4-7 (deadline).

*State.* **Q3-5: closure-ready** on A-10.x, A-11.x, A-04.5, D-1, D-2, D-3, D-6; **not closed**.

### 3.6 DI-6 — authorization subject (6 call sites)

*Decisions applied.* `DEC` D-2 (the subject carries pid, start time **and** uid); `DEC` D-5.

*Supported — design requirements.* `DR` H-PROC.5 (inventory line 265): obtain the subject's
start time and UID for the authorization call by reading the child's start time from `/proc`
(field 22) and its UID; unreadable ⇒ the call is `error`. `DR` H-PROC.4 (line 264): the child
handle records PID, process-group and session ID, and `start_ticks` (`/proc/<pid>/stat` field
22), but `start_ticks` there is **optional (PO-SN (d), R8 line 2921), proposed and not
accepted**. `SF` R8 PK/2 (lines 2322–2354; Subject 2324).

*`DEC` D-5 — authorization subject form.* **Retain H-PROC.5 and select the
PID/start-time/uid subject of D-2, not the pidfd form.** Do not amend the accepted
process-creation contract or add file-descriptor passing in WP-3. **A-13.4 is preserved
prominently: upstream (polkit's own source) calls this PID/start-time fallback "known broken"
for race-free process identity** (a non-atomic `fork` lets an attacker obtain a process
indistinguishable by pid and start time; reliable tracking "requires support for PID File
Descriptors in the kernel, dbus-daemon/broker and systemd"). **The choice is compatibility with
the accepted boundary, not a claim of race freedom.** The residual **remains a Route 3
readiness risk and must be carried to any later WP-4 consideration.** The `PSC` P-13.1
pidfd-form option is not selected.

*Supported — source record.*

* **Encoding (A-12.1, A-12.2, A-12.4, `ASF/W`, `MD`).** On the wire the start time is the
  `start-time` key, a D-Bus `UINT64` (`t`), a decimal integer parsed from the `/proc/<pid>/stat`
  token that is 20th after the `") "` following the **last** `)` — stat field 22. It is
  "expressed in clock ticks", the boot-time clock (includes suspended time) adjusted by the
  reader's time-namespace offset. The value H-PROC.5 reads, the value polkitd reads and the
  `start_ticks` of the child handle are the same field read the same way: **unsigned 64-bit
  decimal clock ticks, no other transformation.** A fewer-than-20-token or non-numeric stat is a
  `Failed` error.
* **A supplied start time of `0` (A-12.5, `ASF/S`)** means "look it up now" — no verification
  against what the client saw. The evidence does not establish that a read field-22 value of
  `0` cannot occur; its handling is a WP-4 matter (Q4-1).
* **Verification by polkitd (A-13.1 … A-13.3, `ASF/S`).** When the subject's user is resolved,
  polkitd reads `/proc/<pid>/status` (`Uid:` — the **real** uid, first value), re-reads the
  start time and compares: a difference is a `Failed` ERROR "process with PID %d has been
  replaced"; a missing process is `Failed`. This is an ERROR reply, not an authorization result.
  The supplied `uid` is the identity policy is evaluated for ("supplied by the client, so we rely
  on the caller to validate its acceptability"); a root caller's mismatching uid is not an error
  and the decision is made for the supplied uid (A-13.2) — **this makes the DI-6 uid read
  security-relevant to the decision (`O-6`)**. When built with `HAVE_PIDFD_OPEN`, polkitd opens a
  pidfd itself for a pid it is given; that descriptor is marked not safe and is not sent on the
  wire; the start-time comparison is still made (A-13.3).
* **Reading `/proc/<pid>/stat` can wait or fail (A-12.3, `ASF/S`).** Ubuntu's kernel delta
  (`7.0.0-31.31`) takes `exec_update_lock` with `down_read_killable` before formatting: a read
  can wait while the target is in `execve` and can fail instead of returning a value. H-PROC.5's
  "unreadable ⇒ the call is `error`" already covers a failed read.
  **Residual `R-M.1` applies to this fact:** the Ubuntu kernel delta is not authenticated
  through the current signed `Sources` indexes; Peter accepted it for A-12.3 and A-15.2 only,
  on the equality of its byte count and SHA-256 with the already accepted R2 Appendix D evidence.
  This is a limited provenance basis, **not** archive-chain authentication.

*Cancellation.* DI-6 has no client-wait cancellation fact of its own (§3.0.4): an abandon is
`error` (`DR` H-PK2.5), and the later cleanup of the subject is the accepted SN contract's
(`DR` H-PROC.1, H-PK2.7). The mechanics are WP-4's (Q4-1, Q4-8) and are not designed here.

*Retained risks and residuals.* **A-13.4 (race-free identity is not claimed)**, R-10.1/R-13.1,
R-12.1 (`USER_HZ` not extracted; the encoding is unaffected), R-12.2, R-13.2, R-13.3, **R-M.1**.
H-PROC.5 says "its UID"; polkitd's own resolution reads the **real** uid (A-13.1): alignment of
the two is a WP-4 detail (Q4-1).

*Later-package inputs (not decided).* Q4-1, Q4-8 (creation and cleanup mechanics), Q6-4.

*State.* **Q3-6: closure-ready** on A-10.5, A-10.6, A-10.10, A-10.12, A-12.x, A-13.x, D-2, D-5;
**not closed**.

### 3.7 DI-S — SA-2 stop-unit call (1 call site)

*Decisions applied.* `DEC` D-1; `DEC` D-3; `DEC` D-4; `DEC` D-9 ("apply this to DI-4 and DI-S").

*Supported.* `DR` SA2.OP.2 (inventory line 595): request the stop of exactly one unit,
`rp11-capture-pass-a.service`, and no other; never to start, restart or reset it. The accepted
text states **no** failure contract for the stop call. `ASF` A-09.1 … A-09.5 and A-09.7 apply
as for DI-4 with the service as target: the same four observable results; a root caller is not
Polkit-checked (A-09.5); `NoSuchUnit` for a not-loaded name (A-09.3); `done` for a loaded
inactive/failed unit (A-09.4). `PSC` P-09.2: the accepted text excludes a stop during start-pre
from the route.

*Request, completion, failure.* Request: `StopUnit(rp11-capture-pass-a.service, mode)` on the
system bus; the mode string is not selected (**IO-2**). Completion: `DEC` D-4 O-C, expected
unit `rp11-capture-pass-a.service`, then read `ActiveState`/`Result`/`InvocationID` as
observation. Failure mapping: exactly the table of §3.4 (`ok(already-stopped)`,
`refused(not-loaded)`, `refused(invalid-request)`, `refused(not-authorized)`,
`error(job-result)`, `error(kind)` with `effect not confirmed` and no retry); **IO-1** applies.

*Cancellation.* §3.0.4: abandonment never proves the unit was or was not stopped, nor that a
queued job stopped; no silent retry. DI-S is not named by SN-10 (inventory line 859).

*Retained risks and residuals.* R-09.1 (stop during start-pre, accepted R2 PO-21 (u), carried),
R-09.2 (the run time of `unit_stop` for a running service is outside the evidence), R-05.1,
R-05.2.

*Later-package inputs (not decided).* Q6-6 (whether DI-S is inside SN-10), Q4-7, Q4-11.

*State.* **Q3-7: closure-ready** on A-09.x, A-05.x, D-1, D-3, D-4, D-9; **not closed**.

### 3.8 Baseline reads (Q3-9) — remain open

*Supported.* `MD` the baseline schema (D lines 4160–4186) and value encoding (D line 4286) name
the properties read by `H-BSE.10` and `H-BSE.11`; all eight DI-1 properties are visible to
`GetAll` (§3.1). The source record supplies the signatures and print rules of all 590 visible
properties (A-03.1 … A-03.7: 464 Unit+Service and 126 Manager names, equal to R2 Appendices A
and B) and shows that a per-property `Get` can reach `HIDDEN`/`EXPLICIT` properties (A-14.3).

*Not supported / not decided.* **R-03.1**: the version-bound baseline property list
(`infra/rp11-unit-properties.<systemd version>.txt`, "proposed" in D 4.3.3) is a repository
artifact outside the required reading, so the byte-exact text of its members was not
enumerated. **D-7 / Q6-2**: whether the baseline compares reproduced printed text or typed
values is undecided; the 29 `…USec`/`…Timespan` properties, sentinel values, `ay` hex, `as`
quoting and the `Exec*` struct form each need a separate computation if text is reproduced
(A-03.3 … A-03.7), and `Timestamp` text depends on timezone and `--timestamp` style (R-03.2).
**Q3-9 is not closure-ready and is not closed.**

### 3.9 Baseline acquisition (Q3-11) — fail-closed record retained

Rows `H-BSE.1`, `.2`, `.3`, `.4`, `.6` (inventory lines 305–310) acquire host identity
(nodename, machine-id hash, architecture, kernel release), operator identity (passwd/group/NSS),
repository state, package state and the launcher's file identity. Each row states that the
tool's mechanism is not stated. `SF` R2 line 620: group membership is evaluated through NSS at
each decision.

**`PO3-11.1` stays in force:** until a mechanism is supported *and decided*, each of these five
acquisitions is recorded as *unavailable* and the baseline that needs it fails closed; no value
is invented. The source record now supplies authoritative facts about direct sources and
**candidate** mechanisms for each, and **none is adopted**: P-15.1 … P-15.3 (UTS-derived keys
and `/etc/machine-id`), P-16.1 … P-16.3 (operator account/group data — `P-16.2` library NSS is
compatible with the loader-free boundary only if the configured sources are `files`),
P-17.1 … P-17.3 (commit identity; launcher attributes; the re-read/carried split of `H-BSE.6` is
left open because accepted text does not decide it), P-18.1 … P-18.3 (installed-package records).
These are blocked by **D-11, D-12, D-13 and D-14** (undecided) and by **Q6-3**. A-15.2 (the
kernel's `uname` result is the caller's UTS namespace plus two personality overrides, and
Ubuntu's `compat_uts_machine=` parameter) rests partly on the Ubuntu kernel delta: **residual
`R-M.1` applies** — limited provenance basis, not archive-chain authentication. Residuals
R-15.1 … R-18.2 are unchanged (§6.2). Installed versions of git, dpkg and the NSS configuration
are unknown and only a separately gated host observation could supply them.

## 4. Citation matrix

### 4.1 Original citations (retained)

Every `SF` used in §3, with its authorized location. Line numbers are lines of the cited file
in this working tree. `R2` = OH-S2 R2 citation record; `R8` = R8 remediation proposal; `D` =
one-host design amendment proposal; `W2` = WP-2 inventory. Version binding: systemd
`259.5-0ubuntu3.4`, polkit `127-2ubuntu1.1`. These rows are retained from the R1 contract; the
only change is to C-23, whose statement is true of the records it cites *as they stood* and is
superseded for WP-3 by §4.2 (see §12).

| Ref | Class | Statement | Source | Used in |
|---|---|---|---|---|
| C-01 | SF | `systemctl show` issues one `GetAll("")` on the unit object | R2 line 479 | §3.1 |
| C-02 | SF | `GetAll` omits `HIDDEN` and `PROPERTY_EXPLICIT` properties | R2 line 480 | §3.1, §3.8 |
| C-03 | SF | a `-p` name the manager does not return is skipped; exit 0 | R2 line 481 | §3.1 |
| C-04 | SF | `StartUnit` has signature `ss` (name, mode) for `systemctl start` | R2 line 585 (S-8) | §3 |
| C-05 | SF | `StartUnit`/`StopUnit` call `bus_verify_manage_units_async_full` with details `unit`, `verb`; job queued only after a positive decision | R2 lines 625–627 | §3.4, §3.5, §3.7 |
| C-06 | SF | shipped defaults of `manage-units`: `auth_admin` / `auth_admin` / `auth_admin_keep` | R2 lines 630–632 | §3.5 |
| C-07 | SF | only uid 0 or an action owner may pass details to `CheckAuthorization` | R2 line 646 | §3.5 |
| C-08 | SF | a root subject is always authorized unless `ALWAYS_CHECK` | R2 line 647 | §3.5 |
| C-09 | SF | group membership is evaluated through NSS at each decision | R2 line 620 | §3.9 |
| C-10 | SF | `pkcheck` exit statuses 0/1/2/3/126/127; unprivileged `--detail` ⇒ 127 | R2 line 656 | §3.5 |
| C-11 | SF | `systemd-run --system` makes a PID-1-supervised service via `StartTransientUnit` | R2 line 697 (a) | §3.2 |
| C-12 | SF | `RuntimeMaxSec=` deadline on `CLOCK_MONOTONIC`, suspended time not counted | R2 line 700 (d) | §3.3 |
| C-13 | SF | timers `--on-active=`/`--on-unit-active=` with `AccuracySec=1s` | R2 line 706 (j) | §3.3 |
| C-14 | SF | failed unit stays loaded with last `InvocationID`; inactive unit may be unloaded | R2 line 707 (k) | §3.1 |
| C-15 | SF | `systemctl show -p` changes nothing but may load an unloaded unit | R2 line 708 (l) | §3.1 |
| C-16 | SF | `StartTransientUnit` refuses a loaded/fragment/jobbed/merged unit: `Unit %s was already loaded or has a fragment file.` | R2 line 709 (m) | §3.2 |
| C-17 | SF | `ExecStart=` only after every `ExecStartPre=` exits 0 | R2 line 711 (o) | §3.1 |
| C-18 | SF | polkit authorizes `StartUnit` once before enqueueing | R2 line 712 (p) | §3.5 |
| C-19 | SF | `--wait` uses signal matches and `GetAll`; no polkit action after `StartUnit` | R2 line 713 (q) | §3.2 |
| C-20 | SF | `InactiveEnterTimestampMonotonic` set only on non-inactive → inactive/failed; `failed`→`inactive` does not set it | R2 line 715 (s) | §3.1 |
| C-21 | SF | read from an `ExecStartPre=+` process during its own start reports `activating` and the attempt's `InvocationID` | R2 line 718 (v) | §3.1 |
| C-22 | SF | the eight DI-1 properties are Appendix A rows #7, #169, #166, #170, #215, #343, #101, #436 | R2 lines 1182, 1344, 1341, 1345, 1390, 1518, 1276, 1611 | §3.1 |
| C-23 | SF | no accepted record cites a client-side contract: bus address and authentication, marshalling, `StartTransientUnit` argument structures, Polkit subject structure, error mapping — true of the records as cited by R8, **superseded for WP-3 by the source record (§4.2)** | R8 line 3808 (E-2) | §4.2, §6 |
| C-24 | SF | system-bus socket as transport locus (TR-4) | D line 940 | §3 |
| C-25 | SF | holder literal; backstop literal; BS-2 | D lines 1989, 2009, 2025 | §3.2, §3.3, §3.4 |
| C-26 | SF | baseline schema; value encoding; ExecStart normalization | D lines 4160–4186, 4286, 4264 | §3.8 |
| C-27 | SF | PK/2 call (2333), outcome (2337), subject (2324) | R8 lines 2322–2354 | §3.5, §3.6 |
| C-28 | SF | `/proc` field 22 start time for the authorization subject | W2 line 265 (H-PROC.5) | §3.6 |
| C-29 | DR | per-interface intents and failure contracts | W2 rows H-DI1.1–.4 (252–255), SA1.OP.2 (583), RT2.AK1.2 (457), RT4.BS2.2/BS3.1/BS4.2 (531, 532, 534), H-PK2.4/.5 (275, 276), H-PROC.4/.5 (264, 265), SA2.OP.2 (595) | §3 |
| C-30 | SF | SN-10 / A-I-16 for DI-4 at BS-2/BS-3 only; BS-4 extension undecided (Q6-7) | W2 line 27 | §3.3, §3.4 |
| C-31 | MD | Appendix A 464 rows, Appendix B 126 rows (58 `yes`); no `EXPLICIT` flag | counted over R2 lines 1165–1773 | §3.1 |
| C-32 | MD | 7 interfaces, 41 sites, procedure matrix, 34 distinct Q3-tagged rows | parse of W2 lines 146–598, 743–783 | §2, §8 |
| C-33 | DR | SN-10 / A-I-16 child-form unknown-effect rule: DI-3 yes, DI-4 yes at BS-2/BS-3, not stated at BS-4 (Q6-7), DI-2 and DI-S not named; carried unmapped (Q6-6); H-PROC.1, H-PK2.5, H-PK2.7 for the subject and the abandon; Q4-7 for deadline and cancellation enforcement | W2 lines 457, 531, 532, 534, 583, 595, 261, 276, 278, 851–861, 1348, 1364, 1365 | §3.0.5, §3.0.4, §3.2–§3.7 |
| C-34 | DR | SN-10 effect unknown for a mutating child; IS-8 no retry, no repetition, no search | R8 lines 2521, 3212 | §3.0.5, §3.0.4 |

### 4.2 Source-record identifiers relied on

The facts, proposals and residuals of the accepted source record are cited **by its stable
identifiers**, never restated from memory. Each row lists every identifier of the record's block
for that `UF`. `A-` = authoritative source fact or derivation (`ASF`/`MD`), `P-` = proposal
(`PSC`; **not** a fact; binding only where a `DEC` adopts it, as the third column says), `R-` =
residual gap. The record's own tier (`S`/`W`/`R`) travels with each `A-` row there.

| UF block | Facts and derivations (`A-`) | Proposals (`P-`) and their disposition | Residuals (`R-`) | Used in |
|---|---|---|---|---|
| UF-01 | A-01.1, A-01.2, A-01.3, A-01.4, A-01.5, A-01.6, A-01.7, A-01.8, A-01.9 | P-01.1 — candidate T-A **adopted by D-1**; T-B not selected | R-01.1, R-01.2 | §3.0.1 |
| UF-02 | A-02.1, A-02.2, A-02.3, A-02.4, A-02.5, A-02.6, A-02.7 | — | R-02.1 | §3.1 |
| UF-03 | A-03.1, A-03.2, A-03.3, A-03.4, A-03.5, A-03.6, A-03.7 | — | R-03.1, R-03.2, R-03.3 | §3.1, §3.8 |
| UF-04 | A-04.1, A-04.2, A-04.3, A-04.4, A-04.5, A-04.6 | P-04.1 — **adopted by D-3** (only the defined refusal cases); P-04.2 — resolved by D-9 | R-04.1, R-04.2 | §3.0.2, §3.4 |
| UF-05 | A-05.1, A-05.2, A-05.3, A-05.4, A-05.5, A-05.6, A-05.7, A-05.8, A-05.9, A-05.10, A-05.11, A-05.12, A-05.13 | P-05.1 — substance fixed by D-3; P-05.2 — **not adopted** beyond D-3's list; P-05.3 — O-C **adopted by D-4**; P-05.4 — answered by D-4 | R-05.1, R-05.2, R-05.3 | §3.0.3, §3.0.4, §3.2–§3.4, §3.7 |
| UF-06 | A-06.1, A-06.2, A-06.3, A-06.4, A-06.5 | — | R-06.1, R-06.2 | §3.2 |
| UF-07 | A-07.1, A-07.2, A-07.3, A-07.4 | — | R-07.1, R-07.2, R-07.3 | §3.2, §3.3 |
| UF-08 | A-08.1, A-08.2, A-08.3, A-08.4, A-08.5, A-08.6, A-08.7 | — | R-08.1, R-08.2 | §3.3 |
| UF-09 | A-09.1, A-09.2, A-09.3, A-09.4, A-09.5, A-09.6, A-09.7 | P-09.1 — resolved by D-9; P-09.2 — applied to DI-S | R-09.1, R-09.2 | §3.4, §3.7 |
| UF-10 | A-10.1, A-10.2, A-10.3, A-10.4, A-10.5, A-10.6, A-10.7, A-10.8, A-10.9, A-10.10, A-10.11, A-10.12 | P-10.1 — shape S-A **adopted by D-2**; S-B not selected | R-10.1, R-10.2 | §3.5 |
| UF-11 | A-11.1, A-11.2, A-11.3 | P-11.1 — **adopted by D-6** | R-11.1 | §3.5 |
| UF-12 | A-12.1, A-12.2, A-12.3, A-12.4, A-12.5 | — | R-12.1, R-12.2 | §3.6 |
| UF-13 | A-13.1, A-13.2, A-13.3, A-13.4, A-13.5 | P-13.1 — pidfd option **not selected** (D-5) | R-13.1, R-13.2, R-13.3 | §3.6 |
| UF-14 | A-14.1, A-14.2, A-14.3, A-14.4 | — | R-14.1 | §3.1, §3.8 |
| UF-15 | A-15.1, A-15.2, A-15.3, A-15.4 | P-15.1, P-15.2, P-15.3: none adopted (D-11 undecided) | R-15.1, R-15.2 | §3.9 |
| UF-16 | A-16.1, A-16.2, A-16.3, A-16.4, A-16.5 | P-16.1, P-16.2, P-16.3: none adopted (D-12 undecided) | R-16.1, R-16.2 | §3.9 |
| UF-17 | A-17.1, A-17.2, A-17.3, A-17.4, A-17.5 | P-17.1, P-17.2, P-17.3: none adopted (D-13 undecided) | R-17.1, R-17.2, R-17.3 | §3.9 |
| UF-18 | A-18.1, A-18.2, A-18.3, A-18.4, A-18.5, A-18.6 | P-18.1, P-18.2, P-18.3: none adopted (D-14 undecided) | R-18.1, R-18.2 | §3.9 |

Observations of the source record cited here: `O-1` … `O-6` (§6.2). Appendix E of the record
indexes every line-range citation behind these identifiers (220 citations, 68 files); this
contract does not duplicate it.

## 5. Q3 closure and readiness table

**Closure-ready** is used exactly as the source record's §6 defines "could close after
acceptance": every *fact* the question needs is now an `ASF`/`MD`/`DR` and only decisions
remain — here, only decisions already adopted (D-1 … D-6, D-9, D-10). **Closure-ready is not
closed.** Closure is accepted only after independent Codex review and Peter's later gate
decision; this file does not close any Q3 question. The source record's §6 parenthetical
dependencies on D-7 (Q3-1: typed versus printed *baseline* text) and D-8 (Q3-2: the `effect`
wording for a non-child call) are separate Q6-2 and Q6-6 matters: under the accepted direction
D-7 stays with Q3-9/Q6-2 and D-8 with Q6-6, and neither is a missing WP-3 interface fact.

| Q3 | Question (WP-2 §12, inventory lines 1325–1337) | Before (R1 contract) | **After integration** | Decisions applied | Outside WP-3 — visible, not decided | Carried residuals / observations | Section |
|---|---|---|---|---|---|---|---|
| Q3-1 | DI-1 interface, value forms, version-bound citation | Not closed (UF-01, 02, 03, 04) | **Closure-ready** | D-1, D-3; D-4(3) | D-7 (Q3-9/Q6-2); Q4-7 | R-01.1, R-01.2, R-02.1, R-03.1 (Q3-9), R-03.2, R-04.1, R-04.2 | §3.1 |
| Q3-2 | DI-2 holder creation | Not closed (UF-01, 04, 05, 06, 07) | **Closure-ready** | D-1, D-3, D-4 | D-8/Q6-6; Q4-7 | R-05.1, R-05.2, R-06.1, R-06.2, R-07.1 … R-07.3; IO-2, IO-3, IO-4 | §3.2 |
| Q3-3 | DI-3 timer and service creation | Not closed (UF-01, 04, 05, 06, 07, 08) | **Closure-ready** | D-1, D-3, D-4, D-10 | Q6-6; Q4-7; BS-RM citation (OH-S2b) | R-05.1, R-05.2, R-08.1 (resolved for DI-3 by D-10), R-08.2; IO-2, IO-3, IO-4 | §3.3 |
| Q3-4 | DI-4 disarm, three sites | Not closed (UF-01, 04, 05, 09) | **Closure-ready** | D-1, D-3, D-4, D-9 | Q6-6 (BS-2, BS-3); **Q6-7 (BS-4)**; Q4-7; Q4-11 | R-05.1, R-05.2, R-09.1, R-09.2; IO-1, IO-2, IO-4 | §3.4 |
| Q3-5 | DI-5 Polkit decision | Not closed (UF-01, 04, 10, 11) | **Closure-ready** | D-1, D-2, D-3, D-6 | Q4-7 | R-10.1, R-10.2, R-11.1, R-13.3; A-13.5 | §3.5 |
| Q3-6 | DI-6 subject to DI-5 | Not closed (UF-10, 12, 13) | **Closure-ready** | D-2, D-5 | Q4-1, Q4-8; Q6-4 | **A-13.4**, R-10.1/R-13.1, R-12.1, R-12.2, R-13.2, R-13.3, **R-M.1** | §3.6 |
| Q3-7 | SA-2 stop-unit call | Not closed (UF-01, 04, 05, 09) | **Closure-ready** | D-1, D-3, D-4, D-9 | Q6-6 (is DI-S inside SN-10?); Q4-7; Q4-11 | R-05.1, R-05.2, R-09.1, R-09.2; IO-1, IO-2, IO-4 | §3.7 |
| Q3-9 | explicit/hidden property reads and printed-form facts | Not closed (UF-03, UF-14) | **Open — not closure-ready** | — (facts A-03.x, A-14.x supplied) | D-7; Q6-2; R-03.1 | R-03.1, R-03.2, R-03.3 | §3.8 |
| Q3-11 | direct on-disk / kernel facts for the baseline | Closed as fail-closed record (`PO3-11.1`); UF-15 … UF-18 recorded | **Fail-closed record retained** (`PO3-11.1`); no mechanism adopted | — (P-15 … P-18 not selected) | D-11, D-12, D-13, D-14; Q6-3 | R-15.1 … R-18.2; **R-M.1** (A-15.2) | §3.9 |

Result: **0 of 8 interface questions closed; 7 of 8 (Q3-1 … Q3-7) closure-ready; Q3-9 open;
Q3-11 answered only as a fail-closed record.** Q6-6 and Q6-7 are unanswered.

## 6. Former unsupported-fact registry — evidence disposition, residuals and observations

### 6.1 Disposition of every former `UF-01` … `UF-18`

The R1 contract's `UF` registry (the exact missing-fact statements are kept verbatim in the
source record §3 and in the git history of this file) is replaced by this table. "Status" is the
source record's own word. A `PSC` that no decision adopted is listed as **not adopted**.

| UF | Subject | Source-record status | Evidence ids | Decisions applied | Still open (not a supported fact) | Contract section |
|---|---|---|---|---|---|---|
| UF-01 | client transport, authentication, framing | supported | A-01.1 … A-01.9 | D-1 (adopts P-01.1 T-A; T-B not selected) | R-01.1, R-01.2 | §3.0.1 |
| UF-02 | unit name to object | supported | A-02.1 … A-02.7 | — | R-02.1 | §3.1 |
| UF-03 | wire types and typed-to-text | **partially supported** | A-03.1 … A-03.7 | — (D-7 undecided) | R-03.1, R-03.2, R-03.3 | §3.1, §3.8 |
| UF-04 | bus error representation and mapping | supported as to representation; mapping is `PSC` | A-04.1 … A-04.6 | D-3 (adopts P-04.1, limited); D-9 (resolves P-04.2) | R-04.1, R-04.2 | §3.0.2, §3.4 |
| UF-05 | job completion, cancellation, abandonment, effect observation | **partially supported** | A-05.1 … A-05.13 | D-3 (P-05.1); D-4 (adopts P-05.3 O-C; answers P-05.4); P-05.2 **not adopted** beyond D-3's list | R-05.1, R-05.2, R-05.3 (Q6-6, Q6-7) | §3.0.3, §3.0.4 |
| UF-06 | `StartTransientUnit` signature and job mode | supported | A-06.1 … A-06.5 | — | R-06.1, R-06.2; IO-2 | §3.2 |
| UF-07 | write-side properties and exec structure | supported (properties the accepted literals use) | A-07.1 … A-07.4 | — | R-07.1 … R-07.3 | §3.2, §3.3 |
| UF-08 | timer and service created together | supported | A-08.1 … A-08.7 | D-10 (R-08.1) | R-08.2 | §3.3 |
| UF-09 | `StopUnit` semantics, not-loaded, root caller | supported | A-09.1 … A-09.7 | D-9 (resolves P-09.1; P-09.2 applied to DI-S); D-3 | R-09.1, R-09.2; IO-1 | §3.4, §3.7 |
| UF-10 | Polkit `CheckAuthorization` | supported | A-10.1 … A-10.12 | D-2 (adopts P-10.1 S-A; S-B not selected); D-1 | R-10.1, R-10.2 | §3.5 |
| UF-11 | authority result fields to outcomes | supported as a field-level description; mapping is `PSC` | A-11.1 … A-11.3 | D-6 (adopts P-11.1) | R-11.1 | §3.5 |
| UF-12 | process-subject start time unit and encoding | supported | A-12.1 … A-12.5 | D-5 | R-12.1, R-12.2; **R-M.1** (A-12.3) | §3.6 |
| UF-13 | polkitd treatment of start time and uid | supported | A-13.1 … A-13.5 | D-5 (P-13.1 pidfd option not selected) | **A-13.4**; R-13.1 … R-13.3 | §3.6 |
| UF-14 | per-property reads of hidden/explicit properties | supported | A-14.1 … A-14.4 | — | R-14.1 | §3.1, §3.8 |
| UF-15 | host nodename, machine-id hash, architecture, kernel release | supported as to facts; **mechanism is `PSC`, not closed** | A-15.1 … A-15.4 | — (D-11 undecided; P-15.1 … P-15.3 not adopted) | R-15.1, R-15.2; **R-M.1** (A-15.2) | §3.9 |
| UF-16 | operator account, group and supplementary-group data | supported as to facts; **mechanism is `PSC`, not closed** | A-16.1 … A-16.5 | — (D-12 undecided; P-16.1 … P-16.3 not adopted) | R-16.1, R-16.2 | §3.9 |
| UF-17 | repository commit identity, launcher attributes, re-read/carried split | **partially supported**; mechanism is `PSC` | A-17.1 … A-17.5 | — (D-13 undecided; P-17.1 … P-17.3 not adopted) | R-17.1 … R-17.3 | §3.9 |
| UF-18 | installed-package records | supported as to facts; **mechanism is `PSC`, not closed** | A-18.1 … A-18.6 | — (D-14 undecided; P-18.1 … P-18.3 not adopted) | R-18.1, R-18.2 | §3.9 |

No `UF` is described as closed. "Supported" means the record found the fact in exact primary
sources; it does not mean a design decision exists.

### 6.2 Residual register (R-01.1 … R-18.x, R-M.1) and source-record observations

Every residual of the source record's §7 is preserved with its exact statement and owner. The
last column states only what integration changed (nothing, unless a decision says so).

| Residual | Exact statement | Owner | Status after integration |
|---|---|---|---|
| R-01.1 | installed message-bus implementation, version and active policy (HF-07 `dbus`) not examined | a later, separately gated host-observation slice (not authorized here); WP-4 must not assume | carried; D-1 requires it to be recorded as a residual, not an assumed fact |
| R-01.2 | kernel credential-passing semantics for the initial NUL byte not researched | WP-3 follow-up (documentation) or WP-4 | carried |
| R-02.1 | garbage-collection timing of loaded stubs | not needed by any accepted use; no owner required | carried; needed by no accepted use |
| R-03.1 | the version-bound baseline property list (D 4.3.3) is a repository artifact outside the required reading | WP-6 (Q6-2) with Peter; WP-3 may cite it once supplied | carried; blocks Q3-9 together with D-7 and Q6-2 |
| R-03.2 | `FORMAT_TIMESTAMP_STYLE`/locale details not re-derived | WP-6 (Q6-2) | carried (Q6-2) |
| R-04.1, R-04.2 | error-name coverage limited to the paths used; bus-daemon errors not enumerated | WP-4 (Q4-11) | carried; IO-3 touches the same ground |
| R-05.1 | message-bus behavior on client disconnect with a pending service reply | later host-observation slice; WP-4 design must treat the reply as lost | carried |
| R-05.2 | all behavior is source-derived; no execution | WP-5 (proof/evidence method) | carried |
| R-05.3 | `effect: "unknown"` meaning for non-child calls | **Q6-6 (WP-6)** — not answered | carried; **Q6-6 not answered** (D-8), Q6-7 for BS-4 not answered |
| R-06.1, R-06.2, R-07.1 … R-07.3 | per-type setter errors; unused job modes; sandbox properties | WP-4 (Q4-11) as needed | carried |
| R-08.1 | D R2 (f) vs RT2.AK1.2 on `TimeoutStartSec` | maintainer decision D-10 | **resolved for the LIT-FULL DI-3 contract by D-10**; the historical sources and the source record are unchanged |
| R-09.1, R-09.2 | stop during start-pre; `unit_stop` run time | accepted PO-21 (u) (carried); WP-4 (Q4-7) | carried |
| R-10.1, R-13.1 | whether the installed polkitd was built with `HAVE_PIDFD_OPEN` | later host-observation slice or a package-file inspection step | carried; D-5 keeps the PID/start-time risk visible (A-13.4) |
| R-10.2, R-13.2 | GDBus disconnect behavior; `pidfd_open(2)` semantics beyond polkit's use | WP-3 follow-up (documentation) | carried |
| R-11.1 | a D-Bus counterpart for the 65,536-byte volume cap | WP-4 (Q4-5/Q4-11) | carried; D-6's "oversized" therefore has no threshold here |
| R-12.1, R-12.2 | `USER_HZ`/`_SC_CLK_TCK` value; polkit's "millisecond" comment | none needed (encoding is unaffected) | carried |
| R-13.3 | polkitd's error strings are not a stable contract | WP-4 (treat as `error` kind only) | carried |
| R-14.1 | R2 Appendix C.1 "27" vs 28 entries | editorial correction of an accepted record (maintainer) | carried; accepted-record editorial observation 2 of 2 (O-4) |
| R-15.1, R-15.2 | host personality/namespace; exact `UTS_MACHINE` | later host-observation slice | carried; Q3-11 stays fail-closed |
| R-16.1, R-16.2 | host `nsswitch.conf`/`libnss-systemd`; `userdb` mechanism | later host-observation slice; WP-6 (Q6-3) | carried; Q3-11 stays fail-closed |
| R-17.1 … R-17.3 | installed git version/ref storage; ref-file byte formats; `statx` details | later host-observation slice; WP-4 | carried; Q3-11 stays fail-closed |
| R-18.1, R-18.2 | installed dpkg version; `info/*.list`/`updates/` byte formats | later host-observation slice; WP-4 | carried; Q3-11 stays fail-closed |
| R-M.1 | the Ubuntu kernel delta `linux` `7.0.0-31.31` is not authenticated through the current signed `Sources` indexes (the version is superseded there); A-12.3 and A-15.2 rest on the diff's equality with R2 Appendix D (§2.4) | maintainer: accept the R2 cross-reference or direct another authentication source; no new fact depends on it | **carried unchanged**; accepted on the limited provenance basis recorded in the evidence-acceptance decision (A-12.3 and A-15.2 only); **not** archive-chain authentication |

**Observations of the source record (Appendix C), preserved unchanged:**

| Id | Observation | Status after integration |
|---|---|---|
| O-1 | WP-2 row `RT2.AM0.5` has the holder read its own `LoadState` as `not-found` at AM-0, although the holder is the running main process of `⟨activation_id⟩.service`; D R2 (d) places the three-unit condition in the executor's AP-0 | **Accepted-record editorial observation 1 of 2**, preserved; no erratum is written here |
| O-2 | the systemd manual disagrees with its source in three places (`aux` "unused"; five documented job modes versus ten; six documented `JobRemoved` results versus thirteen); the source governs | preserved |
| O-3 | D R2 (f) lists `--property=TimeoutStartSec=⟨S⟩` in the backstop literal; WP-2 row `RT2.AK1.2` (after BS-RM) says "no `TimeoutStartSec=`" | **resolved for the LIT-FULL DI-3 contract only, by D-10**; the historical sources are unchanged |
| O-4 | R2 Appendix C.1 labels the hidden Unit/Service group "(27)" but lists 28 entries | **Accepted-record editorial observation 2 of 2** (R-14.1), preserved; no erratum is written here |
| O-5 | the Polkit interface XML spells the path `PoliycKit1` in prose, types `pidfd` as `int32` and lists `uid` in both `unix-process` forms; the decoder and the introspection data differ | preserved; the decoder governs |
| O-6 | polkitd takes the supplied uid of a trusted caller as the identity for policy (A-13.2), so the DI-6 uid read is security-relevant | preserved; a fact for D-5, not a defect |

### 6.3 Integration observations (`IO`) — neither source facts nor decisions

These were noticed while reconciling the accepted evidence with the eight decisions. **Each is
disclosed and left for the independent review and for the successor package; none is filled by
this file, and none decides D-7, D-8, D-11 … D-14, Q6-6 or Q6-7.**

* **IO-1 — discriminating `already-stopped`.** D-9 maps "loaded and already inactive/failed,
  followed by `JobRemoved … done`" to `ok(already-stopped)`. The evidence shows `done` is the
  same signal for a stop that stopped an active unit and for the `-EALREADY` no-op (A-05.9,
  A-09.4, A-09.7), and D-4(4) forbids reading a later state as proof of what this request caused.
  Which observation establishes "inactive/failed *when the stop ran*" is not supplied. §3.4 and
  §3.7 reproduce D-9 exactly and flag the gap.
* **IO-2 — job-mode strings are unselected.** `StartTransientUnit` and `StopUnit` each take a
  mode string (A-06.1, A-09.1; valid sets A-06.2, A-09.1). No accepted record and none of the
  eight decisions selects one. A repository search of the WP-2 inventory and of the one-host
  design record finds no `--job-mode` (0 matches in each), so the historical command lines
  relied on their client's default; the evidence names that default only for `systemd-run`
  (`fail`, A-06.3, tier `R` — a reference client, not a contract) and records none for
  `systemctl stop`. The request parameter is therefore **unselected, not unsupported**: the
  valid set and semantics are supported facts. Selecting a string needs an authorized decision
  before an interface is built; WP-4 may not fill it from memory.
* **IO-3 — two boundary points of D-3.** (a) D-3 names `UnitExists` for **DI-2**. The same
  server error can come from DI-3's call (the same method); it is not listed, so under D-3's
  "every other D-Bus ERROR" clause it is `error(kind)` with `effect not confirmed` (this file
  does not extend the refusal). (b) D-3 says "`InvalidArgs` **before mutation**". The evidence
  places the mode check (A-05.12(a)) and the Polkit check before any state; it lists the unit
  name/type `InvalidArgs` (A-04.2, `dbus-manager.c:1040-1048`) with them only in the proposal
  P-05.2, and it shows property-walk errors arising *after* the unit is made transient (A-05.12,
  A-06.5). §3.2 maps to `refused(invalid-request)` the mode and name/type errors and to `error`
  the property-phase errors; whether the name/type check precedes `unit_make_transient` is for
  the reviewer to confirm against the cited source order. A stub loaded by a read or by a refused
  stop (A-02.7, A-05.13) is treated as not being "mutation" in the sense of a job or unit
  state change, consistently with `DR` H-DI1.3.
* **IO-4 — failure of the pre-call subscription.** D-4 requires the match and `Subscribe()`
  before the mutating call but does not say what a failure of either means. D-3's catch-all
  applies (`error(kind)`); the mutating method has not been issued, so this file assigns no
  effect annotation to it and no further meaning.

## 7. WP-4 input table

What WP-4 may take from this file, and what it may not. **This table does not authorize WP-4**:
WP-4 … WP-7 remain separately gated and unauthorized, and the integrated contract is not
accepted until independent Codex review and Peter's later gate decision.

| # | WP-4 input | Class | Status |
|---|---|---|---|
| 1 | The closed roster of seven interfaces and 41 sites (§2) | MD | usable |
| 2 | The adopted decisions D-1, D-2, D-3, D-4, D-5, D-6, D-9, D-10 with the scope, failure semantics and retained risks of §11 | DEC | decided by Peter; the integration text awaits Codex review |
| 3 | The intent, outcome set and failure contract per interface (§3, `DR`) and the cancellation treatment table (§3.0.4) | DR | usable |
| 4 | Source-record evidence by identifier (§4.2, `ASF`/`MD`) | ASF/MD | usable subject to review; version-bound to the versions of §1 |
| 5 | `PO3` obligations still proposed: `PO3-C2` (no elapsed bound claimed by WP-3), `PO3-1.1` … `PO3-1.3` (DI-1 request/response shape), `PO3-4.2`, `PO3-11.1` (Q3-11 fail-closed record) | PO3 | needs review |
| 6 | Unselected request parameters: the job-mode strings (IO-2) and the discrimination source for `already-stopped` (IO-1); the failure of the pre-call subscription (IO-4); the two D-3 boundary points (IO-3) | IO | **must be fixed by an authorized decision or review before any interface is built**; WP-4 may not fill them from memory |
| 7 | `PSC` not adopted and therefore not usable: P-01.1 (T-B), P-05.2 beyond D-3's list, P-10.1 (S-B), P-13.1 (pidfd option), P-15.1 … P-18.3 | PSC | not usable |
| 8 | Carried, not owned by WP-3: Q4-1 (subject creation), Q4-7 (deadline and cancellation enforcement), Q4-8 (subject cleanup), Q4-11 (error vocabulary and failure details), Q4-5 (parser bounds, the D-Bus counterpart of the 65,536-byte cap: R-11.1); Q6-6 and Q6-7 (not answered); Q6-2 / D-7; Q6-3; Q6-4; BS-RM citation (OH-S2b); the 109 unclassified run-time-varying names (C-4) | — | later packages; **not** missing WP-3 interface facts |
| 9 | Residual risks that must travel with any later consideration: A-13.4 (PID/start-time fallback "known broken" for race-free identity: a Route 3 readiness risk), R-01.1, R-10.1/R-13.1, R-05.1/R-05.2, R-M.1 | — | carried |
| 10 | Q3-9 and Q3-11 remain open: D-7, Q6-2, R-03.1; D-11 … D-14, Q6-3 | — | blocked |

## 8. Reconciliation

| Item | Expected | This file | Result |
|---|---|---|---|
| Interfaces in the roster | 7 (DI-1 … DI-6, DI-S) | 7 | match |
| Logical call sites | 41 | 41 (23 + 1 + 1 + 3 + 6 + 6 + 1) | match |
| Q3 identifiers closed, ready or recorded | 9, exactly those listed | 9 (Q3-1, 2, 3, 4, 5, 6, 7, 9, 11) | match; none invented or omitted |
| Q3 identifiers found in WP-2 operation-row tags outside the nine | 0 | 0 | match |
| Q3 tag instances / distinct rows | 38 / 34 | 38 / 34 | match |
| Per-Q3 row counts (§11.4) | 13, 1, 1, 3, 6, 6, 1, 2, 5 | 13, 1, 1, 3, 6, 6, 1, 2, 5 | match |
| Operation rows parsed (§4–§5 of WP-2) | 318 | 318 | match |
| Former unsupported facts dispositioned | 18 (`UF-01` … `UF-18`) | 18 (§6.1) | match |
| Citation-matrix entries retained | 34 (`C-01` … `C-34`) | 34 (§4.1) | match |
| Source-record identifiers (`A-`, `P-`, `R-`, `O-`) cited | all exist in the accepted record | all resolved (§4.2, §6.2) | match |
| Decisions in the register | 14 (D-1 … D-14): 8 adopted, 6 undecided | 14: 8 adopted, 6 undecided (§11) | match |
| Interfaces with a stated cancellation treatment (§3.0.4) | 7 | 7 | match |
| Q3 states | Q3-1 … Q3-7 closure-ready; Q3-9 open; Q3-11 fail-closed | as stated (§5) | match |

The 38 tag instances are 34 rows because `H-CL.4.2`, `RT1.CQ5.2`, `RT2.AV1.3` and
`RT2.AV1.4` each carry both Q3-5 and Q3-6.

### 8.1 Q3-tagged rows (every row carrying a Q3 identifier)

| Row | Inventory line | Class | Q3 identifier(s) carried (inventory tag) | Interface | Contract section | Closure state |
|---|---:|---|---|---|---|---|
| `H-DI1.1` | 252 | UA | Q3-1 (`A;Q3-1;Q4-7`) | DI-1 | §3.1 | covered; closure-ready (§5); not closed |
| `H-DI1.3` | 254 | CN | Q3-1 (`A;Q3-1`) | DI-1 | §3.1 | covered; closure-ready (§5); not closed |
| `H-PROC.4` | 264 | ID | Q3-6 (`A;Q3-6`) | DI-6 (subject identity) | §3.6 | covered; closure-ready (§5); not closed |
| `H-PROC.5` | 265 | FS | Q3-6 (`A;Q3-6`) | DI-6 (subject identity) | §3.6 | covered; closure-ready (§5); not closed |
| `H-PK2.4` | 275 | UA | Q3-5 (`A;Q3-5;Q4-7`) | DI-5 | §3.5 | covered; closure-ready (§5); not closed |
| `H-PK2.5` | 276 | PR | Q3-5 (`A;Q3-5;Q6-1`) | DI-5 | §3.5 | covered; closure-ready (§5); not closed |
| `H-BSE.1` | 305 | FS | Q3-11 (`A;Q3-11;Q6-3`) | none (baseline acquisition, Q3-11) | §3.9 | covered; answered as fail-closed record (§3.9) |
| `H-BSE.2` | 306 | FS | Q3-11 (`A;Q3-11;Q6-3`) | none (baseline acquisition, Q3-11) | §3.9 | covered; answered as fail-closed record (§3.9) |
| `H-BSE.3` | 307 | FS | Q3-11 (`A;Q3-11;Q6-3`) | none (baseline acquisition, Q3-11) | §3.9 | covered; answered as fail-closed record (§3.9) |
| `H-BSE.4` | 308 | FS | Q3-11 (`A;Q3-11;Q6-3`) | none (baseline acquisition, Q3-11) | §3.9 | covered; answered as fail-closed record (§3.9) |
| `H-BSE.6` | 310 | FS | Q3-11 (`A;Q3-11;Q6-2`) | none (baseline acquisition, Q3-11) | §3.9 | covered; answered as fail-closed record (§3.9) |
| `H-BSE.10` | 314 | UA | Q3-9 (`A;Q3-9;Q6-2`) | DI-1 (baseline `unit` / `manager` reads) | §3.1, §3.8 | covered; **open — not closure-ready** (§5) |
| `H-BSE.11` | 315 | UA | Q3-9 (`A;Q3-9`) | DI-1 (baseline `unit` / `manager` reads) | §3.1, §3.8 | covered; **open — not closure-ready** (§5) |
| `H-CL.2.1` | 351 | UA | Q3-1 (`A;Q3-1;Q4-7`) | DI-1 | §3.1 | covered; closure-ready (§5); not closed |
| `H-CL.4.2` | 356 | UA | Q3-5, Q3-6 (`A;Q3-5;Q3-6;Q4-1`) | DI-5 and DI-6 | §3.5, §3.6 | covered; closure-ready (§5); not closed |
| `H-CL.6.3` | 363 | UA | Q3-1 (`A;Q3-1;Q4-7`) | DI-1 | §3.1 | covered; closure-ready (§5); not closed |
| `RT1.CQ4.7` | 417 | UA | Q3-1 (`A;Q3-1;Q4-7`) | DI-1 | §3.1 | covered; closure-ready (§5); not closed |
| `RT1.CQ4.8` | 418 | UA | Q3-1 (`A;Q3-1;Q4-7`) | DI-1 | §3.1 | covered; closure-ready (§5); not closed |
| `RT1.CQ5.2` | 420 | UA | Q3-5, Q3-6 (`A;Q3-5;Q3-6;Q4-1`) | DI-5 and DI-6 | §3.5, §3.6 | covered; closure-ready (§5); not closed |
| `RT2.AM0.5` | 443 | UA | Q3-1 (`A;Q3-1`) | DI-1 | §3.1 | covered; closure-ready (§5); not closed |
| `RT2.AM0.12` | 450 | UA | Q3-1 (`A;Q3-1;Q4-7`) | DI-1 | §3.1 | covered; closure-ready (§5); not closed |
| `RT2.AK1.2` | 457 | UA | Q3-3 (`A;Q3-3;Q4-7;Q6-6`) | DI-3 | §3.3 | covered; closure-ready (§5); not closed |
| `RT2.AK1.3` | 458 | UA | Q3-1 (`A;Q3-1`) | DI-1 | §3.1 | covered; closure-ready (§5); not closed |
| `RT2.AV1.3` | 474 | UA | Q3-5, Q3-6 (`A;Q3-5;Q3-6;Q4-1`) | DI-5 and DI-6 | §3.5, §3.6 | covered; closure-ready (§5); not closed |
| `RT2.AV1.4` | 475 | UA | Q3-5, Q3-6 (`A;Q3-5;Q3-6;Q4-1`) | DI-5 and DI-6 | §3.5, §3.6 | covered; closure-ready (§5); not closed |
| `RT2.HS.1` | 478 | UA | Q3-1 (`A;Q3-1;Q4-7`) | DI-1 | §3.1 | covered; closure-ready (§5); not closed |
| `RT2.HL.3` | 483 | UA | Q3-1 (`A;Q3-1;Q4-7`) | DI-1 | §3.1 | covered; closure-ready (§5); not closed |
| `RT4.BS1.1` | 529 | UA | Q3-1 (`A;Q3-1;Q4-7`) | DI-1 | §3.1 | covered; closure-ready (§5); not closed |
| `RT4.BS2.2` | 531 | UA | Q3-4 (`A;Q3-4;Q4-7;Q6-6`) | DI-4 | §3.4 | covered; closure-ready (§5); not closed |
| `RT4.BS3.1` | 532 | PR | Q3-4 (`A;Q3-4;Q4-7;Q6-6`) | DI-4 | §3.4 | covered; closure-ready (§5); not closed |
| `RT4.BS4.2` | 534 | UA | Q3-4 (`A;Q3-4;Q4-7;Q4-11;Q6-7`) | DI-4 | §3.4 | covered; closure-ready (§5); not closed |
| `RT5.PRE.1` | 558 | UA | Q3-1 (`A;Q3-1;Q4-7`) | DI-1 | §3.1 | covered; closure-ready (§5); not closed |
| `SA1.OP.2` | 583 | UA | Q3-2 (`A;Q3-2;Q4-7`) | DI-2 | §3.2 | covered; closure-ready (§5); not closed |
| `SA2.OP.2` | 595 | UA | Q3-7 (`A;Q3-7;Q4-7;Q4-11`) | DI-S | §3.7 | covered; closure-ready (§5); not closed |

### 8.2 Rows per Q3 identifier

| Q3 | Rows carrying it | Count (this parse) | Count (inventory §11.4) |
|---|---|---:|---:|
| Q3-1 | `H-DI1.1` `H-DI1.3` `H-CL.2.1` `H-CL.6.3` `RT1.CQ4.7` `RT1.CQ4.8` `RT2.AM0.5` `RT2.AM0.12` `RT2.AK1.3` `RT2.HS.1` `RT2.HL.3` `RT4.BS1.1` `RT5.PRE.1` | 13 | 13 |
| Q3-2 | `SA1.OP.2` | 1 | 1 |
| Q3-3 | `RT2.AK1.2` | 1 | 1 |
| Q3-4 | `RT4.BS2.2` `RT4.BS3.1` `RT4.BS4.2` | 3 | 3 |
| Q3-5 | `H-PK2.4` `H-PK2.5` `H-CL.4.2` `RT1.CQ5.2` `RT2.AV1.3` `RT2.AV1.4` | 6 | 6 |
| Q3-6 | `H-PROC.4` `H-PROC.5` `H-CL.4.2` `RT1.CQ5.2` `RT2.AV1.3` `RT2.AV1.4` | 6 | 6 |
| Q3-7 | `SA2.OP.2` | 1 | 1 |
| Q3-9 | `H-BSE.10` `H-BSE.11` | 2 | 2 |
| Q3-11 | `H-BSE.1` `H-BSE.2` `H-BSE.3` `H-BSE.4` `H-BSE.6` | 5 | 5 |

## 9. Acceptance checklist

| # | Required content | Present | State |
|---|---|---|---|
| 1 | Fixed scope, source hierarchy, fact classes, version boundary | §1 | complete |
| 2 | Closed roster mapped to all 41 call sites | §2 | complete |
| 3 | Request, response, value encoding, completion, cancellation, failure per interface | §3, §3.0 | complete **on the accepted evidence and the eight decisions**; the unselected parameters and boundary points are disclosed as IO-1 … IO-4 (§6.3) |
| 4 | Citation matrix and source-record identifiers | §4 | complete |
| 5 | Exact Q3 closure/readiness table, nine ids | §5 | complete; **0 of 8 interface questions closed, Q3-1 … Q3-7 closure-ready** |
| 6 | Disposition of every former `UF`; residual and observation register | §6 | complete |
| 7 | WP-4 input table | §7 | complete |
| 8 | Reconciliation of Q3-tagged rows and call sites | §8 | complete |
| 9 | Acceptance checklist | §9 | this table |
| 10 | Integration result and return state | §10 | `WP-3 CONTRACT INTEGRATION RETURNED — INDEPENDENT CODEX REVIEW PENDING` |
| 11 | Decision register D-1 … D-14 | §11 | complete |
| 12 | Cumulative change register (including the former `HARD STOP` wording) | §12 | complete |
| – | No language, library, binding or syscall chosen | whole file | confirmed |
| – | D-7, D-8, D-11 … D-14 undecided; Q6-6, Q6-7 unanswered; BC-2 later; WP-4 … WP-7 not prepared or authorized | §1, §3.0.5, §3.8, §3.9, §11 | confirmed |
| – | R-M.1 visible and not described as archive-chain authentication | header, §3.6, §3.9, §6.2 | confirmed |

## 10. Integration result

**Result: `PASS` of the integration step; the contract is not accepted.** The accepted
source-completion evidence and the eight adopted decisions are integrated cumulatively. Q3-1 …
Q3-7 are closure-ready; Q3-9 is open; Q3-11 keeps its fail-closed record. Only D-1 … D-6, D-9
and D-10 are decided. No `PSC`, residual or unavailable mechanism was turned into a source fact;
no fact was taken from memory; no network, host, retained-evidence or secret access occurred.

The **accepted WP-3 `HARD STOP` remains in force** until independent Codex review and Peter's
later gate decision replace it. The next authority step is that review and gate decision. This
file does not make or prepare them, does not accept itself and does not authorize WP-4 … WP-7.
The former §10 text is preserved verbatim in §12.2.

## 11. Decision register D-1 … D-14

Eight decisions are adopted; six are undecided. "Adopted" means Peter Duscha accepted the exact
integration prompt (358 lines, 18,188 bytes, SHA-256
`894470357ed0fa1ed6c0fba251c471a9e549b7412068b1c1009984580ea91fce`) on 2026-10-12, which adopts
D-1 … D-6, D-9 and D-10 **as a unit** and appoints Claude to record them without substitution
or expansion. The adopting record is the acceptance-and-activation record (74 lines, 3,795 bytes,
SHA-256 `19eff0574a49e5f7364b3f4e2c1268cb22dc10b317f327a4c94638d2c7ca91fa`).

### 11.1 Summary

| Id | Subject | Status | Source proposal | Interfaces and Q3 | Section |
|---|---|---|---|---|---|
| D-1 | Transport for the manager interfaces | **Adopted** | P-01.1 (T-A) | DI-1 … DI-5, DI-S; Q3-1 … Q3-5, Q3-7 | §3.0.1 |
| D-2 | DI-5 request shape | **Adopted** | P-10.1 (S-A) | DI-5, DI-6; Q3-5, Q3-6 | §3.5 |
| D-3 | ERROR-name and transport-failure mapping | **Adopted** | P-04.1 (only the defined refusal cases) | DI-1 … DI-5, DI-S; Q3-1 … Q3-5, Q3-7 | §3.0.2 |
| D-4 | Completion-observation design | **Adopted** | P-05.3 (O-C), P-05.4 | DI-2, DI-3, DI-4, DI-S; Q3-2, Q3-3, Q3-4, Q3-7 | §3.0.3 |
| D-5 | Authorization subject form | **Adopted** | A-13.4; P-13.1 (pidfd not selected) | DI-6, DI-5; Q3-6 | §3.6 |
| D-6 | DI-5 result mapping | **Adopted** | P-11.1 | DI-5; Q3-5 | §3.5 |
| D-7 | Typed versus printed baseline text | **Undecided** (Q6-2) | — | DI-1 baseline reads; Q3-9 | §3.8 |
| D-8 | Meaning of `effect: "unknown"` for non-child calls | **Undecided** (Q6-6) | — | DI-2, DI-3, DI-4, DI-S; Q3-2 … Q3-4, Q3-7 | §3.0.5 |
| D-9 | `StopUnit` of an inactive or not-loaded unit | **Adopted** | P-09.1, P-04.2 | DI-4, DI-S; Q3-4, Q3-7 | §3.4, §3.7 |
| D-10 | Backstop service timeout property | **Adopted** | O-3, R-08.1 | DI-3; Q3-3 | §3.3 |
| D-11 | UTS-derived keys and malformed `/etc/machine-id` (UF-15) | **Undecided** | P-15.1 … P-15.3 | Q3-11 | §3.9 |
| D-12 | Files-only versus library NSS (UF-16; also Q6-3) | **Undecided** | P-16.1 … P-16.3 | Q3-11 | §3.9 |
| D-13 | Carry or re-read the commit identity; `H-BSE.6` key split (UF-17) | **Undecided** | P-17.1 … P-17.3 | Q3-11 | §3.9 |
| D-14 | Status-file parse versus carried record; pending `updates/` (UF-18) | **Undecided** | P-18.1 … P-18.3 | Q3-11 | §3.9 |

### 11.2 The eight adopted decisions

**D-1 — one transport.** *Decision:* use the system message bus for DI-1, DI-2, DI-3, DI-4 and
DI-S, and for DI-5 as required by Polkit; do not select systemd's private manager socket.
*Rationale:* one authenticated transport locus, matches accepted TR-4 (D line 940), no second
transport contract; A-01.9 shows DI-5 needs the system bus in any case. *Affected:* every
interface that reaches the manager or the authority; Q3-1 … Q3-5, Q3-7. *Retained risks:*
**R-01.1** — the installed broker, version and policy are recorded as a residual, **not** as an
assumed fact; R-01.2; R-04.2; the connection, buffer and deadline design is WP-4's (Q4-7).

**D-2 — DI-5 request.** *Decision:* P-10.1 shape S-A: `CheckAuthorization` with subject
`("unix-process", {pid u, start-time t, uid i})`, action `org.freedesktop.systemd1.manage-units`,
details exactly `unit` and `verb`, flags `0`, empty cancellation id; the supplied `uid` is
deliberate. *Rationale:* it is the shape `pkcheck` puts on the wire (A-10.10), and the accepted
H-PROC.5 already obtains the uid, although the general PID/start-time decoder allows it to be
absent (A-10.6). *Affected:* DI-5, DI-6; Q3-5, Q3-6. *Retained risks:* A-13.5 (a root subject is
authorized without policy at flags `0`); R-10.1; R-13.3; `O-5`, `O-6`.

**D-3 — errors and transport failures.** *Decision:* P-04.1 with only the already defined
refusal cases (§3.0.2); every other outcome is `error(kind)`, mutating interfaces carry
`effect not confirmed` and never permit a silent retry; the four Polkit ERROR names are not
`not-authorized`; the `kind` vocabulary beyond the named categories is WP-4's; Q6-6 and Q6-7 are
not decided by it. *Rationale:* refusal only where a cause is known to precede mutation, fail
closed everywhere else (consistent with `DR` SN-10/A-I-16 and IS-8). *Affected:* DI-1 … DI-5,
DI-S; Q3-1 … Q3-5, Q3-7. *Retained risks:* R-04.1, R-04.2, R-13.3; IO-3.

**D-4 — completion observation.** *Decision:* P-05.3 O-C for DI-2, DI-3, DI-4 and DI-S
(§3.0.3). *Rationale:* the manager's own `JobRemoved` for the returned job path is the only
completion signal (A-05.5, A-05.9, A-05.10); a state read is observation, so a lost completion
can never be promoted to a success. *Affected:* DI-2, DI-3, DI-4, DI-S; Q3-2, Q3-3, Q3-4,
Q3-7. *Retained risks:* A-05.8 (no `JobRemoved` during a reload), R-05.1, R-05.2; IO-4; the
deadline mechanism is Q4-7; `effect: "unknown"` is D-8/Q6-6; the BS-4 extension is Q6-7.

**D-5 — authorization subject form.** *Decision:* retain H-PROC.5 and the PID/start-time/uid
subject of D-2, not the pidfd form; amend no process-creation contract; add no
file-descriptor passing in WP-3. *Rationale:* compatibility with the accepted boundary, **not**
a claim of race freedom. *Affected:* DI-6 and DI-5; Q3-6. *Retained risks:* **A-13.4** — upstream
calls this fallback "known broken" for race-free process identity; it remains a Route 3 readiness
risk and **must be carried to any later WP-4 consideration**; R-10.1/R-13.1; A-12.5; **R-M.1**
(A-12.3).

**D-6 — DI-5 result mapping.** *Decision:* P-11.1 for a well-formed `(bba{ss})`: `(true,false)`
authorized; `(false, either)` not-authorized; `(true,true)` `error(invalid-reply)`; everything
else `error` under D-3; the details map does not alter the three outcomes. *Rationale:* polkitd
never constructs both-true (A-10.11), so it can only mean a defective reply; a challenge is a
normal reply and not an error (A-04.6). *Affected:* DI-5; Q3-5. *Retained risks:* R-11.1 (no
threshold for "oversized"); R-13.3.

**D-9 — stop of an inactive or not-loaded unit.** *Decision:* loaded and already
inactive/failed followed by `JobRemoved … done` is `ok(already-stopped)`; `NoSuchUnit` before a
job is queued is `refused(not-loaded)`; applies to DI-4 and DI-S; neither result implies a
different earlier request had no effect; a transient unit already collected after a prior stop
is in the not-loaded case. *Rationale:* the two facts are different (A-09.3 versus A-09.4) and
the contract must not merge them. *Affected:* DI-4, DI-S; Q3-4, Q3-7. *Retained risks:* **IO-1**;
A-05.13 (a refused stop can still load a stub); R-09.1, R-09.2.

**D-10 — backstop service timeout property.** *Decision:* the DI-3 backstop service has no
`TimeoutStartUSec`; its relevant properties are `Type=exec`, `Restart=no`,
`OOMScoreAdjust=-1000`, `RuntimeMaxUSec=⟨S_b⟩·10⁶`, `TimeoutStopUSec=⟨S⟩·10⁶` and the accepted
`ExecStart`; this resolves only the `TimeoutStartSec=⟨S⟩` literal of D R2 (f) for the LIT-FULL
DI-3 contract and rewrites no historical source. *Rationale:* follows accepted WP-2 row
`RT2.AK1.2` and BS-RM. *Affected:* DI-3; Q3-3. *Retained risks:* the BS-RM citation obligation
(OH-S2b) is still proposed and is not owned by WP-3; R-08.2.

### 11.3 The six undecided decisions

* **D-7** — whether the baseline compares reproduced printed text or typed values (Q6-2).
  Needed by Q3-9 together with R-03.1. The facts that bear on it are A-03.1 … A-03.7.
* **D-8** — the meaning of `effect: "unknown"` for a non-child call (Q6-6), and its possible
  BS-4 extension (Q6-7). D-3's `effect not confirmed` wording does not decide it.
* **D-11** — the source of the UTS-derived keys and the rule for a malformed `/etc/machine-id`
  (UF-15; P-15.1 … P-15.3).
* **D-12** — files-only parsing versus library NSS, and whether "NSS" in `H-BSE.2` is preserved
  literally; also the Q6-3 behaviour-preservation question (UF-16; P-16.1 … P-16.3). P-16.2 is
  compatible with the loader-free boundary only if the configured sources are `files`.
* **D-13** — carry or re-read the commit identity and the key-by-key re-read/carried split of
  `H-BSE.6` (UF-17; P-17.1 … P-17.3); accepted text does not decide it.
* **D-14** — status-file parse versus carried record and the rule for pending `updates/` entries
  (UF-18; P-18.1 … P-18.3).

None of these is decided, selected or implied by this file.

## 12. Cumulative change register

The pre-integration contract (the R1 revision) was **469 lines, 50,599 bytes, SHA-256
`b766c10f2c28ac2d32a7dc7ee4ab2c92a3cf80d67fd70f345a9f0dd7ba92c888`**; it is preserved
unchanged in Git history (`git show HEAD:docs/review/phase-5-0-p5-r5-rp11-h1-oh-s3-lit-full-wp3-interface-contract.md`
on the tree this integration started from). Every historical file other than this one remains
unchanged. "Old §n" means the section of the R1 revision.

### 12.1 Section and row ledger

| # | Old location (R1 revision) | Change | Replacement |
|---:|---|---|---|
| 1 | Title (line 1) `… interface contract — HARD STOP` | replaced | New title and the cumulative terminal summary (header block); former wording quoted in §12.2 |
| 2 | Work-ID line (lines 3–4) | extended | Work IDs: original, R1, CI1 |
| 3 | "**Terminal state: `HARD STOP`.** … eighteen facts …" (lines 6–14) | replaced | Header paragraphs "What this file is", "What is decided", "What this makes of the Q3 questions", "The former HARD STOP"; quoted in §12.2 |
| 4 | "R1 revision" paragraph (lines 16–29) | condensed | "Revision history" (header); the cancellation substance is retained in §3.0.4, the citation correction in §4.1 |
| 5 | §1 Scope | updated | §1 Scope: adds the unchanged-boundary list, D-7/D-8/D-11 … D-14 undecided, Q3-9/Q3-11 states |
| 6 | §1 Source hierarchy (3 levels) | replaced | §1 Source hierarchy (5 levels): adds Peter's decisions (level 2) and the accepted source-completion record with its fixed identity (level 5) |
| 7 | §1 Version boundary | extended | §1 Version boundary: adds the source record's versions and `R-M.1` |
| 8 | §1 Fact classes (`SF`, `MD`, `DR`, `PO3`, `UF`) | extended | §1 Fact classes: adds `ASF`, `DEC`, `PSC`, `IO`; `UF` becomes a former identifier |
| 9 | §2 roster, 41-row call-site mapping, procedure matrix | **unchanged** | §2 (copied without change) |
| 10 | §3 intro | rewritten | §3 intro |
| 11 | §3 common bullet: TR-4 "Nothing more … (`UF-01`)" | replaced | §3.0.1 (D-1; A-01.x) |
| 12 | §3 common bullets: `SF` R2 §6.2/§6.3 | retained | §3.4, §3.5 |
| 13 | §3 common bullet: WP-2 §7.1 counting only | retained | §2 |
| 14 | §3 common bullets: `DR` SN-10/IS-8; `DR` Q4-7 | retained and reconciled | §3.0.5 |
| 15 | §3 common `PO3-C1` (content conditional on `UF-04`) | replaced | §3.0.2 (D-3; the vocabulary is decided by the adopted decisions) |
| 16 | §3 common `PO3-C2` | retained | §3.0.5, §7 row 5 |
| 17 | §3.0 Cancellation and abandonment; `PO3-X1`, `PO3-X2` | now decided | §3.0.4 (D-3, D-4); the child-form `DR` rule and Q6-6/Q6-7 unchanged |
| 18 | §3.0 `PO3-X3` | retained | §3.0.4 |
| 19 | §3.0 `UF-05 (expanded)` | dispositioned | §3.0.3, §3.0.4, §6.1 (UF-05 **partially supported**; A-05.1 … A-05.13) |
| 20 | §3.0 seven-interface cancellation treatment table (classes `UF`+`PO3`, gaps UF-xx) | replaced | §3.0.4 table (classes `DEC`/`DR`, evidence ids, remaining Q-items) |
| 21 | §3.1 DI-1 (`PO3-1.1` … `PO3-1.4`; stop on UF-02, 03, 04, 14) | rewritten | §3.1 (D-1, D-3; A-02.x, A-03.x, A-14.x; Q3-1 closure-ready) |
| 22 | §3.2 DI-2 (stop on UF-05, 06, 07) | rewritten | §3.2 (D-1, D-3, D-4; A-05.x … A-07.x; `PO3-2.1` and `PO3-2.4` now D-3; Q3-2 closure-ready) |
| 23 | §3.3 DI-3 (stop on UF-08, 05, 06, 07; `RuntimeMaxSec`/`TimeoutStopSec` spellings) | rewritten | §3.3 (D-10; A-08.x, A-07.x; server spellings `…USec`; Q3-3 closure-ready) |
| 24 | §3.4 DI-4 (`PO3-4.1` conditional on UF-09) | rewritten | §3.4 (D-9 decides the conditional outcome; A-09.x; Q3-4 closure-ready) |
| 25 | §3.5 DI-5 (`PO3-5.1` … `PO3-5.3`; stop on UF-10, 11) | rewritten | §3.5 (D-2, D-6; A-10.x, A-11.x; Q3-5 closure-ready) |
| 26 | §3.6 DI-6 (`PO3-6.1`; stop on UF-12, 13) | rewritten | §3.6 (D-5; A-12.x, A-13.x incl. A-13.4, R-M.1; Q3-6 closure-ready) |
| 27 | §3.7 DI-S (`PO3-7.1`, `PO3-7.2`; stop on UF-09) | rewritten | §3.7 (D-9; Q3-7 closure-ready) |
| 28 | §3.8 Baseline reads (Q3-9 "cannot be closed") | updated | §3.8 (Q3-9 open: R-03.1, D-7, Q6-2) |
| 29 | §3.9 Baseline acquisition (Q3-11 fail-closed, `PO3-11.1`) | updated | §3.9 (fail-closed record retained; PSC not adopted; D-11 … D-14) |
| 30 | §4 matrix C-01 … C-34 | retained | §4.1 |
| 31 | §4 row C-23 ("no accepted record cites a client-side contract") | amended | §4.1 C-23: marked as true of the records as they stood and superseded for WP-3 by §4.2 |
| 32 | §4 "Not cited because absent …: see §6" | replaced | §4.2 source-record identifiers |
| 33 | §5 Q3 closure table (nine rows "Not closed" / Q3-11 fail-closed); "Result: 0 of 8 …" | replaced | §5 (before/after; Q3-1 … Q3-7 closure-ready; Q3-9 open; Q3-11 fail-closed) |
| 34 | §6 Unsupported-fact registry `UF-01` … `UF-18` and its search evidence | replaced | §6.1 evidence disposition, §6.2 residual register and observations, §6.3 integration observations |
| 35 | §7 WP-4 input table (row 5: "must be supplied by an authorized source") | replaced | §7 |
| 36 | §8 Reconciliation (UF count 18, citation entries 34, etc.) | updated | §8 |
| 37 | §8.1 Q3-tagged rows: closure column "covered; **not closed**" | updated | §8.1: "closure-ready" for Q3-1 … Q3-7 rows; "open" for the two Q3-9 rows; Q3-11 rows unchanged |
| 38 | §8.2 Rows per Q3 identifier | **unchanged** | §8.2 |
| 39 | §9 Acceptance checklist (row 9: stop-rule result `HARD STOP`) | updated | §9 |
| 40 | §10 Stop-rule result `HARD STOP` | replaced | §10 Integration result; former text quoted in §12.2 |
| 41 | — | new | §11 Decision register D-1 … D-14 |
| 42 | — | new | §12 Cumulative change register |
| 43 | — | new | §13 Return state |

Unchanged in substance across all of the above: the seven interfaces, the 41 call sites, the 34
Q3-tagged rows, every `DR` quotation, every residual of the source record, the non-answers to
Q6-6 and Q6-7, and the boundary list.

### 12.2 Former `HARD STOP` wording (verbatim from the R1 revision)

The title:

> # LIT-FULL WP-3 interface contract — HARD STOP

The terminal-state paragraphs (old lines 6–14):

> **Terminal state: `HARD STOP`.** The authorized repository sources do not support
> eighteen facts that the nine required Q3 closures need (registry in §6, `UF-01`
> … `UF-18`; `UF-05` expanded by R1 to cover cancellation and abandonment). Per the accepted prompt's stop rule, no citation was manufactured,
> nothing was silently deferred, no fact was introduced from memory, and nothing
> was researched. This file is therefore **not a complete interface contract**: it
> records everything the sources do support, separates it from what they do not,
> and names each missing fact exactly. Q3-1 … Q3-7 and Q3-9 are **not closed**.
> Q3-11 is closed as a fail-closed record (§5). WP-4 … WP-7 are neither prepared
> nor authorized.

Old §10 (old lines 458–469):

> ## 10. Stop-rule result
>
> **`HARD STOP`.** The authorized repository sources do not support the facts
> `UF-01` … `UF-14` that Q3-1 … Q3-7 and Q3-9 require (the exact statements are in
> §6; `UF-05` now includes the cancellation and abandonment semantics of DI-2, DI-3,
> DI-4 and DI-S). Cancelling a client wait is not proof that a queued job stopped or
> that a mutating request had no effect, and no silent retry follows. This R1
> revision preserves the `HARD STOP`. Q3-11's `UF-15` … `UF-18` are recorded in a fail-closed answer. No citation
> was manufactured, no gap was deferred silently, no fact was taken from memory and
> no research was done. The next authority step is for a maintainer to decide how
> the client-side facts are to be supplied by an authorized record; this file does
> not make or prepare that decision and does not authorize WP-4 … WP-7.

These passages describe the state of the R1 revision. They are quoted, not restated: the accepted
`HARD STOP` remains in force until independent Codex review and Peter's later gate decision
replace it, and this file does not itself replace it.

## 13. Return state

This state does not authorize WP-4 and does not itself accept the integrated contract. The
accepted WP-3 `HARD STOP` remains in force until independent Codex review and Peter's later gate
decision replace it.

WP-3 CONTRACT INTEGRATION RETURNED — INDEPENDENT CODEX REVIEW PENDING
