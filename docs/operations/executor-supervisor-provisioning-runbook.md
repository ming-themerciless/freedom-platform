# Executor supervisor — provisioning runbook (Route 3 executor OC)

**Status: accepted on 2026-10-22 for continued non-production development as
part of the cumulative executor OC R6 candidate. Nothing in this runbook has
been run on production or staging, and following it does not authorize
activation.** Activation is a separate, explicit operator action behind its own
review (see the final review and acceptance in
`docs/review/route-3-executor-oc-implementation-handback.md`).

The 2026-10-22
[`Route 3 production-readiness assignment`](../review/route-3-production-readiness-claude-prompt.md)
required this lifecycle to be rehearsed at the real fixed paths with a
root-owned deployment on `oracle-test`; it was, with no bind mount (see the
[readiness handback](../review/route-3-production-readiness-handback.md)). Peter
accepted the cumulative readiness candidate for continued non-production
development on 2026-10-24. That acceptance does not authorize use of this
runbook on production or staging. On 2026-10-25 Peter selected Route 3 only as
a bounded, attended migration/cutover evidence facility. Each activation and
any use of this runbook still require separate explicit authority; recurring,
unattended and general-maintenance use are outside the decision.

Peter separately authorized the §6 read-only production inspection on
2026-10-25. It returned **NO-GO** before this runbook: the production host does
not have the required Python 3.14, account, Route 3 artifacts/units/runtime
paths or tmpfiles prerequisite, and its live checkout/Python 3.12 venv are not
the required root-owned trust roots. The later root-assisted classification of
sudoers and private Polkit completed (nothing reaches the future account), and
Peter selected the distinct `/opt/freedom-route3/{code,venv}` deployment used
throughout this runbook; it is implemented and rehearsed only on `oracle-test`.
On 2026-10-31 Peter confirmed that the temporary grant file `/etc/sudoers.d/zz-claude-window` is absent and accepted the Phase A stop/order
deviation (both blockers closed; his decisions). Peter accepted the independently reviewed provisioning plan on 2026-11-03. None of that authorizes any command in this runbook that changes state:
release identities remain `UNSET`, and provisioning, installation and activation are unauthorized.

Scope: the administrator-provisioned prerequisites that `tools/executor_supervisor_install.py` *verifies and never
edits*, then the install, verification, upgrade, rollback and removal of the supervisor **system service**. The
persistent supervisor is a root-owned system unit that runs as the unprivileged `freedom-executor` account; the account's
lingering systemd *user* manager owns only the separate transient per-invocation services. Every step below was exercised
on the disposable `oracle-test` host against a root-owned test package (the fifth-remediation proof, repeated for the sixth correction, in
`tests/systemd_integration/test_executor_package_host.py` and the reboot proof in `test_executor_reboot_host.py`); the
production values called out as "production-specific" were not.

## P. Production provisioning plan (R6 remediation, 2026-11-02) — NO-GO until every field in block F is supplied

**Status of this plan: accepted 2026-11-03; it authorizes nothing.** Peter decided on 2026-10-31 that `/etc/sudoers.d/zz-claude-window` is absent
and accepted the Phase A stop/order deviation; both blockers are closed. Codex's independent R6/R7 re-review found no remaining issue, and Peter accepted part P. Provisioning, installation and activation remain **unauthorized**:
every release field is still `UNSET`, S1 requires a later written decision after the exact release record is supplied and reviewed, and activation is a separate later decision. Every block
below is for a **future** operator under that future written authority; none has been run on production or staging. Rehearsed only on `oracle-test`.

### P.1 Stages and authority — one stage is never authority for the next

| Stage | What it does | Changes the host? | Authority needed | Ends at |
|---|---|---|---|---|
| **S0** | S0.0 is **withdrawn** and refuses to run (it assumed Python 3.14 absent); S0.A attests the already-installed Python 3.14 closure; S0.1 fields are all set; S0.2 read-only host preflight; S0.3 runs the trusted gate (`route3_gate`): the installed baseline against the reviewed record **and** every member's installed payload and metadata against the signed-archive reference | S0.A, S0.2 and S0.3 read only; S0.0 and S0.1 do nothing | Peter's authorization of a read-only production preflight | `[S0.* rc=0]` or **NO-GO** |
| **S1** | **Inert** prerequisites: evidence/pre-state (staged, then published by one rename), a **hold** on the attested pinned Python packages (nothing is installed), the verified deployment `/opt/freedom-route3/{code,venv}`, the dormant `freedom-executor` account (no linger), the `tmpfiles.d` fragment | yes | Peter's written **provisioning** authorization | **STOP-A** (below) |
| **S2** | Read-only verification of the STOP-A state, and the v2 checklist | no | same authorization as S1 | `[S2.* rc=0]` |
| **S3** | **Arming + install**: lingering user manager, SA-2 artifact, the one-command sudoers drop-in, installer `verify` and `install` (which **enables** the unit) | yes | a **separate** written authorization, after S2 and one post-S1 boot | **STOP-B** |
| **S4** | **Activation**: start, `verify-ready`, acceptance probes, later removal | yes | a third, separate decision, with the attending operator and window of the handover | outside this plan |

Rules for every block: it begins with `# AUTHORITY:`; it runs in a subshell, so pasting it never ends your shell; it prints `[<id> rc=N]` and **returns the same N**
(its last command is `(exit "$rc")`); a non-zero status is a **STOP** — run the rollback block (R, or R3 for S3), never retry in place. Paste block D and block F
first, in the same root shell. Never paste a later stage's block under an earlier stage's authority. `tools.executor_supervisor_install install` appears only in S3.

### P.2 STOP-A: the exact state the provisioning stage leaves

After S1 and a passing S2.1 the host holds exactly these new objects, and nothing else: the reviewed `python3.14` package closure (held with `apt-mark hold`); `/opt/freedom-route3/{code,venv}`
(root-owned, no group/other write, exactly the release manifest and the pinned `jeepney`); the `freedom-executor` account, its same-named primary group and its home (no
password, `nologin`, **no linger**); `/usr/lib/tmpfiles.d/freedom-blades-rp11-polkit-rules.conf`; and the root-only evidence directory `/root/route3-evidence` (pre-state, checkpoints,
manifest copy). At STOP-A:

* the supervisor is **not installed**: no unit fragment, no `multi-user.target.wants` link, `LoadState=not-found`; **an ordinary or maintenance reboot cannot start it**, because nothing for the
  boot to start exists (S2.1 proves each of those absences);
* no Route 3 transient invocation can run: there is no supervisor, no lingering user manager (`user@<uid>.service` inactive, no `/run/user/<uid>`), no process of the account, no SA-2
  artifact and no sudoers drop-in;
* no smoke stop, capture pass, migration or cutover has occurred or can occur; the installer was not invoked and `install` is absent from S1;
* **no effective privileged execution route exists.** The route needs a process of the account to reach `sudo` and the root-owned SA-2 artifact; at STOP-A the account is dormant and the
  sudoers drop-in and SA-2 artifact do not exist. They are created in S3 in the order *linger → SA-2 artifact → sudoers* (sudoers last), and the three are jointly usable only once
  the supervisor runs, i.e. in S4. Even after S3 the unit is enabled but not started; a reboot between S3 and S4 would start it, so a boot is forbidden in that interval (P.6);
* `polkit_tmpfiles verify` is **expected to exit 12 (`fragment-predates-boot`) until the next boot**, because the fragment is newer than the running boot; the first boot after S1 is a separate maintenance
  action (safe: nothing auto-starts) and S3 requires `verify` to exit 0 after it. Residual that remains for Peter's later decision: from that boot on, systemd creates the empty
  `/run/polkit-1/rules.d`, which `polkitd` will watch; no rules file is placed there by this plan.

### P.3 Controlled artifact set — every identity is a field or a named blocker

Nothing is fetched during production execution. The operator receives the artifacts below in a root-only directory `/root/route3-artifacts/<ROUTE3_RELEASE_REV>/` (root-owned `0700`, files root-owned, not
group/other-writable) and S0.2/S0.3/S1.2 refuse anything whose SHA-256 differs from the field. Until the supplier enters a reviewed, published revision and the attested baseline, every field below is
**`UNSET`**, a hard blocker that returns NO-GO. Nothing here is promoted from an `oracle-test` observation into a production decision.

| Artifact | Identity | State |
|---|---|---|
| Reviewed release | `ROUTE3_RELEASE_REV` (40-hex commit id of the independently reviewed, committed candidate) | **BLOCKER — supplier: Peter** (commit and publication are his) |
| Deployable code | `code.tar` = `git archive --format=tar <REV> -- adapters application tools infra/executor infra/tmpfiles.d infra/rp11-h1` built on the maintainer workstation (never on production), plus `MANIFEST.sha256` (`<sha256>␣␣<path>` per file, sorted, LF). `ROUTE3_ARCHIVE_SHA256`, `ROUTE3_MANIFEST_SHA256` | **BLOCKER — supplier: Peter / maintainer workstation**, after the commit. The manifest, not the tar, is the content identity: the tree must equal it exactly (set and digests). Includes the service fragment and every repository file executed as root or by the executor |
| Python 3.14 (installed host baseline) | **The attested dependency closure of the three installed roots** `python3.14`, `python3.14-minimal` (owns `/usr/bin/python3.14`) and `python3.14-venv`, split in two: the **pinned set** `ROUTE3_APT_PACKAGES` (members built from source package `python3.14`; exact `name=version`; later held) and the **base set** `ROUTE3_APT_BASE` (every other closure member; exact `name=version`; re-checked, never held). Accepted archive sources: `ROUTE3_APT_ORIGIN`, a sorted, comma-separated list of `<url> <suite>/<component>` entries. Interpreter identity: `ROUTE3_PY_SHA256` (independent reference, below). Binding: `ROUTE3_BASELINE_SHA256`, the SHA-256 of the reviewed baseline record file | **BLOCKER — supplier: Peter**, from the S0.A attestation of the production host's own installed packages (no install, no simulation; no third-party repository, no `deadsnakes`, no build from source). `oracle-test` has the same Ubuntu 26.04.1 baseline but is **not** a production value |
| Signed-archive payload reference | `reference.record`: for every closure member the SHA-256 the archive's **signed index** states for exactly that package file, a digest of the package's own metadata (control fields, conffile list with packaged md5s, maintainer scripts, `md5sums`) and a digest of its non-conffile payload (content, mode and owner of every file, every symlink target). Identity: `ROUTE3_REFERENCE_SHA256`. Delivered as `<ART>/<REV>/reference.record`; committed as `docs/operations/route3-payload-reference.txt` | **BLOCKER — supplier: Peter**, derived by `reference-payload` on a non-production host from the committed baseline record (no production download, no production mutation). This is the only thing that binds the installed bytes to the archive: `dpkg --verify` and `apt-cache madison` compare the host with itself and with what an archive *offers* |
| Jeepney wheel | `jeepney-0.9.0-py3-none-any.whl`, SHA-256 `97e5714520c16fc0a45695e5365a2e11b81ea79bba796e26f9f1d178cb182683` (the accepted pin, `infra/rp11-h1/requirements.lock`; the same wheel builds SA-2 and the venv) | **fixed**. Custody: obtained once, off production, by `pip download --no-deps --only-binary=:all: --require-hashes -r infra/rp11-h1/requirements.lock` and delivered to `<ART>/<REV>/wheelhouse/`. Installed only with `--no-index --no-deps --require-hashes` (S1.2) |
| SA-2 artifact | built **from the deployed, verified code and the same wheel** by `infra/rp11-h1/build.py` into `/usr/local/libexec/freedom-blades-rp11` (root-owned, directories `0755`, files `0644`); identity `ROUTE3_SA2_TREE_SHA256` = SHA-256 of the sorted `sha256␣␣path` listing of that tree (S3.2 computes it) | **BLOCKER — supplier: Peter**, from a reference build of the release revision on a non-production host; built only in S3 |
| `tmpfiles.d` prerequisite | `infra/tmpfiles.d/freedom-blades-rp11-polkit-rules.conf` from the manifest, installed by the reviewed tool to `/usr/lib/tmpfiles.d/` root-owned `0644`; S2.1 compares it byte-for-byte with the manifest copy | covered by the manifest |
| Service fragment | `infra/executor/freedom-blades-executor-supervisor.service`, from the manifest; placed only by installer `install` in S3 | covered by the manifest |

**Release-record procedure (2026-11-11 redesign; replaces the former S0.0 closure proposal).** Production already runs Ubuntu 26.04.1 with Ubuntu Python 3.14.4 as part of its host baseline, so there is
nothing to simulate and nothing to install: the closure is **attested from what is installed**. The old S0.0 assumed the interpreter was absent, would have proposed an install set from a solver run and
**must never run** (it now refuses). Every step below is read-only on the host it inspects; the tool is [`tools/route3_release_record.py`](../../tools/route3_release_record.py), standard library only, run as
`/usr/bin/python3.14 -I -S -B <tool> <command>` so no ambient module, environment or bytecode takes part. Status 0 = ok, 1 = `NO-GO:` findings (each printed), 2 = usage, 3 = the environment could not be read.

1. **Reviewed revision (Peter, workstation).** Commit and publish the candidate. `ROUTE3_RELEASE_REV` is that full 40-hex commit. A later release-record commit that changes only block F, the baseline record and documents is
   not a new deployable revision; `verify-release` proves no path of the archive pathspec changed.
2. **Archive and manifest (non-production host).** `build-archive --repo <checkout> --rev <REV> --out <new directory>` runs P.3's literal `git archive` (user and system git configuration neutralised, tar umask pinned),
   validates every member exactly as block D's `archive` check does (regular files and directories only, no link, device, special mode bit, secret-named, cache or non-plain name), writes `code.tar` and a
   `MANIFEST.sha256` byte-identical to P.3's recipe, and prints the two digests. It refuses an existing directory.
3. **Production attestation (S0.A, read-only, unprivileged).** Run `attest-host` and keep its output as the **baseline record**. The record is canonical text — operating system, interpreter path/real file/SHA-256, the three
   roots and, per member, class (`pin`/`base`), name, version, architecture, source package and every archive source that offers exactly that version — so an unchanged host always renders the same bytes.
   *Closure:* the transitive `Depends`/`Pre-Depends` closure of the three roots over the **installed** packages (first installed alternative, then `Provides`; `Recommends`/`Suggests` are not followed). *Pinned set:* members whose
   source package is `python3.14` — the interpreter family — exact, held at S1.1, `dpkg --verify` clean. *Base set:* every other member (libc6, OpenSSL, …) — attested exactly and re-checked at every stage, but **not held**, because
   holding shared libraries would stop their security updates; a change to any of them is NO-GO until the record is re-attested and re-reviewed, never an in-place upgrade. The attestation refuses (status 1): a package that is not cleanly installed,
   a dependency nothing installed satisfies, a package installed for more than one architecture, a member that no configured **archive** source offers at exactly its installed version (a locally built or orphaned package; dpkg's own
   status file listed by `apt-cache madison` is only the installed-state marker, never an origin), an origin shape it does not understand, and an interpreter that is not a file of `python3.14-minimal`.
   Archive origins are compared at every later stage as **exact per-member sets** (a member offered by one source more, or one less, than reviewed is drift; a member with no reviewed or live origin is refused, never accepted). But an archive *offering* a name and version
   says nothing about the bytes installed on the host: that is what the payload reference of step 4 binds.
4. **Independent references (non-production host).**
   *Interpreter:* `reference-interpreter --version <python3.14-minimal version of the record> --workdir <empty directory>` downloads that exact `python3.14-minimal`, requires its SHA-256 to equal the one the archive's **signed index**
   states, and prints the digest of `./usr/bin/python3.14` inside the package. That digest is `ROUTE3_PY_SHA256`; it must equal the **installed** file's digest in the baseline record.
   *Payload reference:* `reference-payload --record <baseline record> --workdir <empty directory>` does the same for **every** closure member: the index SHA-256 of exactly `name=version` is read first, the package is downloaded, its SHA-256 must
   equal it before it is opened, the archive source must be one the record reviewed, and the tool then reads the `.deb` in memory (never extracting it) and prints the **payload reference**: per member the index SHA-256, a metadata digest
   and a payload digest as defined in P.3. `ROUTE3_REFERENCE_SHA256` is its SHA-256. The trust anchor is the archive's signed index as verified by `apt` on that host; the reference contains nothing taken from any installed system.
   *Isolated apt configuration (optional, both commands: `--apt-config <absolute file>`).* Use it when the generating host does not offer exactly the reviewed archive build: a **regional mirror** (refused as "none of which the baseline record
   reviewed"), **no suitable source** ("the archive index shows nothing for ..."), or the **wrong architecture variant**. With `APT::Architecture-Variants "amd64v3"` apt selects, for the same name and version, a build that dpkg still records as
   `Architecture: amd64` but whose index stanza says `Architecture-Variant: amd64v3` and whose file is `..._amd64v3.deb`: other bytes, other SHA-256. Production and `oracle-test` may run such builds (observed on `oracle-test`, reported 2026-11-14: `libc6` and
   `python3.14-minimal` installed as `amd64v3`), so **plain `amd64` is never assumed**: the configuration must name the variant the baseline host runs, or none if it runs the plain build. Read it from that host read-only, either
   `dpkg-query -W -f='${Package} ${Architecture} ${Architecture-Variant}\n' <closure packages>` or the `Architecture-Variant` row that `payload-rows --package <name>` prints; the baseline record needs no variant column because the reference binds the
   build itself: the package's own control fields **including `Architecture-Variant`** (present only on a variant build, so a plain package's digests are unchanged) and every file. A reference generated for the other build, or for a mirror's
   different bytes, is therefore not accepted by luck of a version string: `verify-host` reports `payload drift` for it, and the tools do not guess or refuse variants on the generating host. (Real apt prints one stanza per version, the one
   `APT::Architecture-Variants` selects; two different SHA-256 values for one version are refused as "does not state exactly one SHA-256".) The tools run apt with an empty environment, so `APT_CONFIG` cannot reach them; the file is passed as `-c`, which
   layers it over the system's configuration without editing `/etc/apt`. It must be an absolute regular file owned by the caller, not writable by group or others, in a directory nobody else can replace entries in (create the scratch directory
   `0700`); and it must keep apt's signature verification: the tools refuse (before any apt call) a configuration, or sources it names, that enable `Acquire::AllowInsecureRepositories`, `APT::Get::AllowUnauthenticated`, `trusted=yes` or
   `allow-insecure=yes`. Build it once per generating host, naming the reviewed `ROUTE3_APT_ORIGIN` URL, suite and component (the sources and keyring below are an example for the Ubuntu archive; use the record's origin):

   ```text
   S=<new 0700 scratch directory>   # sources.list:  deb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] <reviewed URL> <suite> <component>      (NO arch= option, see below)
   apt.conf:  Dir::Etc::sourcelist "$S/sources.list";   Dir::Etc::sourceparts "$S/sources.list.d";   Dir::State "$S/state";   Dir::State::status "$S/status";   Dir::Cache "$S/cache";
              APT::Architecture "amd64";   APT::Architectures "amd64";   APT::Architecture-Variants "<the baseline host's variant, e.g. amd64v3; empty only if it runs the plain build>";      (substitute the absolute path for $S: apt does not expand it)
   create:    $S/sources.list.d  $S/state/lists/partial  $S/cache/archives/partial  (directories), $S/status (empty file)
   refresh:   TMPDIR=<scratch> apt-get update -c $S/apt.conf        # the one network step; downloads and verifies the signed index, writing only under $S
   ```

   **Never put an architecture filter on the source (`[arch=amd64 ...]`, `arch+=`, `arch-=`, deb822 `Architectures:`) while `APT::Architecture-Variants` is nonempty.** The plain and the variant build of one version live in different indexes (`main/binary-amd64/Packages` and
   `main/binary-amd64v3/Packages`, each with its own signed `Release` entry). A source filtered to `arch=amd64` makes `apt-get update` fetch only the first, so `apt-cache show` and `apt-get download` select the **plain** build even though the variant is configured: observed on
   `oracle-test` (2026-11-14, first real-archive attempt): with `APT::Architecture-Variants "amd64v3"` and `[arch=amd64 ...]` sources apt fetched `binary-amd64` and downloaded `python3.14-minimal_3.14.4-1ubuntu0.2_amd64.deb`, giving interpreter digest `52e0a13e...` instead of the installed
   `be9a2a5e...`, and `reference-payload` then failed on `python3-pip-whl` because the plain archive lacked the installed version. Removing only `arch=amd64` made `apt-get update` fetch `binary-amd64v3/Packages`, `apt-cache` showed `Filename ..._amd64v3.deb`, SHA-256 `049113...` and
   `Architecture-Variant: amd64v3`. The tools therefore **refuse such a configuration before any apt call** ("cannot select the architecture variant it names"), by reading the sources the effective configuration (`apt-config dump -c`) names; the filter is harmless, and not refused, when the variant list is empty. That check is
   an early diagnosis, not the safeguard: the origin comparison, the signed-index digest check and the payload/interpreter equality at `verify-host` still fail closed for a wrong build whatever the cause.
   The tools then read `apt-cache show`/`madison` and `apt-get download` against that state alone; the origin comparison and the signed-index digest check apply unchanged, so a configuration that selects the wrong archive or the wrong build fails closed.
   **A version the archive no longer offers cannot be referenced:** the signed index lists only current versions, so a baseline host whose installed package has since been superseded (observed on `oracle-test`: installed `libc6 2.43-2ubuntu2.4`,
   archives now offer `2.43-2ubuntu2.7`) fails attestation ("offered by no configured archive source") and `reference-payload` has nothing to read. Bring that host current (or re-attest the baseline after its authorized update) rather than relaxing the check.
   `payload-rows --package <name>` and `payload-rows --deb <file>` print the canonical rows on each side for diagnosis (a read-only command; production is not asked for them).
5. **SA-2 tree (non-production host).** `sa2-reference --archive <code.tar> --wheel <pinned wheel>` extracts the validated archive, builds the SA-2 artifact twice into fresh destinations exactly as S3.2 does and prints the
   digest only if both agree. `sa2-digest <tree>` computes S3.2's identity for any tree and refuses links, special files, group/other-writable entries, plain-name violations and an empty tree.
6. **Fill the record.** `propose --record <baseline record> --reference <payload reference>` prints the package values for review. Peter enters block F **in the reviewed repository** and commits the baseline record as
   `docs/operations/route3-baseline-record.txt` and the payload reference as `docs/operations/route3-payload-reference.txt` (package names, versions and digests only; no secret). `check-fields --runbook <this file> --record <record> --reference <reference>`
   must print `ok`: it refuses any `UNSET`, any malformed value, a baseline or reference digest that is not the file's SHA-256, a reference derived for another record or whose members differ from the record's, and tokens/origins/interpreter digest
   that differ from the record.
7. **Prove the artifacts.** `verify-release --repo <checkout> --runbook <this file> --artifacts <directory> --published-ref <ref> [--sa2-dir <tree>]` reproduces the archive from `ROUTE3_RELEASE_REV` and requires: the commit is an ancestor of
   the published reference; the working tree equals the revision and has no uncommitted or untracked file inside the archive pathspec (**no mutable or unreviewed tree**); `ROUTE3_ARCHIVE_SHA256`/`ROUTE3_MANIFEST_SHA256` equal the
   reproduced artifacts; `code.tar`, `MANIFEST.sha256` and the pinned wheel in the directory are byte-identical to them; and the SA-2 tree, when given, has the field digest.
8. **Deliver, then S0.1–S0.3 on production.** The root-only directory `/root/route3-artifacts/<REV>/` holds `code.tar`, `MANIFEST.sha256`, `baseline.record` and `reference.record` (the committed files, byte for byte) and `wheelhouse/<wheel>`.
   S0.2 verifies the first, second and fourth against their fields; S0.3 runs `route3_gate`. Independent review of the completed record precedes any S1 decision.

**What each stage re-checks, mechanically.** `route3_gate` (block D) is the single attestation: it verifies the three reviewed artifacts against block F, refuses an interpreter that is not the signed-archive package's file *before running it*, runs the tool **from the
digest-verified `code.tar`**, and requires the host to equal the baseline record **and** every member's installed package metadata and non-conffile payload to equal the signed-archive reference, then repeats the `dpkg --verify` and base-set checks
(`route3_python_ok`). It runs in S0.3, S2.1 and **at every mutating boundary: S1.0, S1.1 (before and after the hold), S1.2, S1.3, S1.4, S3.1, S3.2, S3.3, S3.5 and the activation S4.1 (before `systemctl start`)** — so invoking any of those blocks directly, without S0.3, a missing, changed or extra closure member or payload fails
**before the block mutates anything**. **Any difference is NO-GO**: stop, do not upgrade or install anything, return to Peter for a re-attested and re-reviewed record. `apt-mark hold` (S1.1) freezes only the pinned set. The
`/usr/bin/python3.14` path is the one the accepted contract names (sudoers vector, `-I -S` entries); no other interpreter is substituted. *No install path exists:* the apt-transaction machinery of the earlier plan (solver preflight, in-transaction hooks,
`apt-get install`) was removed; a missing member is a hard NO-GO, never an installation.

*What the payload comparison does and does not establish.* Compared exactly: the control fields the closure is computed from, the conffile list with the packaged md5s, every maintainer script and `md5sums` dpkg keeps, and for every file of the package's own
file list that is not a conffile its type, mode, owner and content (symlinks: target); merged-`/usr` aliases are resolved on both sides. A local edit of a **conffile** is host policy and is not compared (its list and packaged md5 are). Refused outright: a dpkg
`path-exclude`/`path-include` configuration (it changes what is legitimately unpacked). A diversion or statoverride needs no rule of its own: the file at a diverted or re-owned path is compared as installed, so the other package's file (or a changed mode or owner) is a payload difference. **Not covered:** files that no package owns (for example Python bytecode caches under a package directory), and
the circularity that the host's own interpreter and libraries run the check (mitigated by refusing a non-reference interpreter before it runs and by the independent `sha256sum`; an adversary who already controls root on the host can defeat any self-attestation).

### D. Definitions — no effect on the host; paste first

The two Python programs are the only code the operator's root shell evaluates before a deployment is verified. They are standard-library only, contain no single quote, and are run as
`/usr/bin/env -i PATH=/usr/bin:/bin /usr/bin/python3.14 -I -S -B -c …` (empty environment, isolated mode: no `PYTHONPATH`, `PYTHONHOME`, user site, working directory or `site`; no bytecode written into the trusted tree).
`ROUTE3_ENTRY` is the item-8 entry of the handback checklist, identical to it. `ROUTE3_STAGE_ENTRY` checks an archive (`archive`: only regular files and directories, no link, device or special mode bit, and no name that is an environment file, `.git*`, `.pgpass`, a private key or certificate (`*.pem`, `*.key`, `*.p12`, `*.pfx`), a cache (`__pycache__`, `*.pyc`), `id_*`, or a credential/service-account/secret *data* file (those words in a name that is extensionless or ends `.json`, `.yaml`, `.yml`, `.toml`, `.ini`, `.cfg`, `.conf`, `.txt`, `.b64`, `.asc`, `.gpg`; a `.py` source such as `adapters/http/credentials.py` is code, covered by the manifest digest), exactly the manifest's file set and digests), checks a deployment (`tree`: real root-owned directories and files without group/other write, no link except the five fixed venv links, no hard-linked file, the code
tree exactly the manifest, `site-packages` exactly the pinned `jeepney`), and starts the installer (`installer`: the same tree walk first, then `tools.executor_supervisor_install` from the trusted code root only).

```bash
ROUTE3_PATH=/usr/sbin:/usr/bin:/sbin:/bin
ROUTE3_PY=/usr/bin/python3.14
ROUTE3_BASE=/opt/freedom-route3
ROUTE3_STAGE=/opt/freedom-route3.stage
ROUTE3_ART=/root/route3-artifacts
ROUTE3_EVID=/root/route3-evidence
ROUTE3_EVID_STAGE=/root/route3-evidence.new
ROUTE3_ACCOUNT=freedom-executor
ROUTE3_HOME=/home/freedom-executor
ROUTE3_TMPFILES=/opt/freedom-route3/code/tools/polkit_tmpfiles.py
ROUTE3_ENTRY='import os,runpy,stat,sys
def refuse():
    print("[FINDING] trusted Route 3 tool or source fragment is missing, wrong-typed, symlinked, not root-owned or group/other-writable: verify not run")
    sys.exit(20)
def trusted(p,kind):
    try:
        s=os.lstat(p)
    except OSError:
        refuse()
    (stat.S_IFMT(s.st_mode)==kind and s.st_uid==0 and not s.st_mode&0o022) or refuse()
def chain(path):
    parts=path.split("/")
    (parts[0]=="" and len(parts)>2 and all(c not in ("","..",".") for c in parts[1:])) or refuse()
    cur="/"
    trusted(cur,stat.S_IFDIR)
    for c in parts[1:-1]:
        cur=os.path.join(cur,c)
        trusted(cur,stat.S_IFDIR)
    trusted(path,stat.S_IFREG)
tool=sys.argv[1]
chain(tool)
chain(os.path.dirname(os.path.dirname(tool))+"/infra/tmpfiles.d/freedom-blades-rp11-polkit-rules.conf")
sys.argv[1:]=sys.argv[2:]
runpy.run_path(tool,run_name="__main__")'
ROUTE3_STAGE_ENTRY='import hashlib,os,re,runpy,stat,sys,tarfile
def refuse(why):
    print("[FINDING] Route 3 "+why+": nothing was changed or executed")
    sys.exit(30)
BAD=re.compile(r"[.]env.*|[.]git.*|[.]pgpass|__pycache__|id_[a-z0-9]+|.*[.](pem|key|pyc|pyo|p12|pfx)|.*(credential|service_account|secret).*[.](json|ya?ml|toml|ini|cfg|conf|txt|b64|asc|gpg)|.*(credential|service_account|secret)[^.]*",re.I)
def rel_ok(r):
    return r!="" and not r.startswith("/") and all(c not in ("","..",".") and not BAD.fullmatch(c) for c in r.split("/"))
def manifest(path):
    out={}
    for line in open(path,encoding="ascii").read().splitlines():
        m=re.fullmatch(r"([0-9a-f]{64})  (\S+)",line)
        (m and rel_ok(m[2]) and m[2] not in out) or refuse("manifest is malformed")
        out[m[2]]=m[1]
    return out
def lst(p):
    try:
        return os.lstat(p)
    except OSError:
        refuse("path is missing: "+p)
def sound(p,kind):
    s=lst(p)
    (stat.S_IFMT(s.st_mode)==kind and s.st_uid==0 and not s.st_mode&0o022) or refuse("path is wrong-typed, symlinked, not root-owned or group/other-writable: "+p)
    return s
def chain(path):
    cur="/"
    sound(cur,stat.S_IFDIR)
    for c in path.strip("/").split("/"):
        cur=os.path.join(cur,c)
        sound(cur,stat.S_IFDIR)
def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()
def walk(top,allow):
    files,n=set(),0
    stack=[top]
    while stack:
        d=stack.pop()
        with os.scandir(d) as it:
            for e in it:
                n+=1
                n<=50000 or refuse("tree is too large")
                p=e.path
                r=os.path.relpath(p,top)
                s=lst(p)
                if stat.S_ISLNK(s.st_mode):
                    (allow.get(r)==os.readlink(p) and s.st_uid==0) or refuse("tree holds an unexpected symlink: "+r)
                elif stat.S_ISDIR(s.st_mode):
                    sound(p,stat.S_IFDIR)
                    stack.append(p)
                else:
                    sound(p,stat.S_IFREG)
                    s.st_nlink==1 or refuse("tree holds a multiply linked file: "+r)
                    files.add(r)
    return files
VENV_LINKS={"bin/python":"python3.14","bin/python3":"python3.14","bin/python3.14":"/usr/bin/python3.14","bin/\U0001d70bthon":"python3.14","lib64":"lib"}
def tree(root,mf):
    chain(root)
    sound(root+"/code",stat.S_IFDIR)
    code=walk(root+"/code",{})
    exp=manifest(mf)
    code==set(exp) or refuse("code tree is not exactly the manifest file set")
    for r,d in exp.items():
        sha(root+"/code/"+r)==d or refuse("code file differs from the manifest: "+r)
    sound(root+"/venv",stat.S_IFDIR)
    walk(root+"/venv",VENV_LINKS)
    sound(root+"/venv/pyvenv.cfg",stat.S_IFREG)
    sp=root+"/venv/lib/python3.14/site-packages"
    sorted(os.listdir(sp))==["jeepney","jeepney-0.9.0.dist-info"] or refuse("site-packages is not exactly the pinned jeepney")
    print("tree: ok "+root)
def archive(ar,mf):
    exp=manifest(mf)
    seen={}
    total=0
    with tarfile.open(ar,"r:") as t:
        for m in t:
            n=m.name.rstrip("/")
            rel_ok(n) or refuse("archive member name is not allowed")
            m.mode&0o7000==0 or refuse("archive member has a special mode bit")
            if m.isdir():
                continue
            m.isreg() or refuse("archive member is not a regular file or directory")
            n not in seen or refuse("archive member is duplicated")
            total+=m.size
            (m.size<=8<<20 and total<=128<<20) or refuse("archive is too large")
            seen[n]=hashlib.sha256(t.extractfile(m).read()).hexdigest()
    seen==exp or refuse("archive is not exactly the manifest (file set or digest)")
    print("archive: ok")
cmd,args=sys.argv[1],sys.argv[2:]
if cmd=="archive":
    archive(*args)
elif cmd=="tree":
    tree(*args)
elif cmd=="installer":
    root=args[0]
    chain(root)
    sound(root+"/code",stat.S_IFDIR)
    walk(root+"/code",{})
    sys.dont_write_bytecode=True
    sys.path.insert(0,root+"/code")
    sys.argv=["executor_supervisor_install"]+args[1:]
    runpy.run_module("tools.executor_supervisor_install",run_name="__main__",alter_sys=True)
else:
    refuse("entry command is unknown")'
# every Python evaluation as root: absolute interpreter, empty environment, isolated mode, no bytecode; the status is the program's own
route3_stage() { /usr/bin/env -i PATH=/usr/bin:/bin "$ROUTE3_PY" -I -S -B -c "$ROUTE3_STAGE_ENTRY" "$@"; }
# the one installer invocation (verify | install | verify-ready | remove): module and imports resolve only from the verified /opt/freedom-route3/code
route3_installer() { route3_stage installer /opt/freedom-route3 "$@"; }
route3_cp() { printf '%s\n' "$1" >> "$ROUTE3_EVID/checkpoints" && sync -- "$ROUTE3_EVID/checkpoints"; }
route3_fields_ok() {
  local bad=0 v re='^[0-9a-f]{64}$' pk o ol
  [[ $ROUTE3_RELEASE_REV =~ ^[0-9a-f]{40}$ ]] || { echo "NO-GO: ROUTE3_RELEASE_REV is unset or not a 40-hex commit id (supplier: Peter)"; bad=1; }
  for v in ROUTE3_ARCHIVE_SHA256 ROUTE3_MANIFEST_SHA256 ROUTE3_PY_SHA256 ROUTE3_BASELINE_SHA256 ROUTE3_REFERENCE_SHA256 ROUTE3_SA2_TREE_SHA256 ROUTE3_WHEEL_SHA256; do
    [[ ${!v} =~ $re ]] || { echo "NO-GO: $v is unset or not a SHA-256 (supplier: Peter)"; bad=1; }
  done
  # ROUTE3_APT_PACKAGES is the PINNED set of the attested closure (the members built from source package python3.14, held at S1.1): exact name=version for python3.14, python3.14-minimal and python3.14-venv, no name twice
  re='^[a-z0-9][a-z0-9.+-]*=[A-Za-z0-9.+~:-]+( [a-z0-9][a-z0-9.+-]*=[A-Za-z0-9.+~:-]+)*$'
  pk=" $ROUTE3_APT_PACKAGES "
  if [[ $ROUTE3_APT_PACKAGES =~ $re && $pk == *" python3.14="* && $pk == *" python3.14-minimal="* && $pk == *" python3.14-venv="* ]] && [ -z "$(route3_tokens | cut -d= -f1 | LC_ALL=C sort | uniq -d)" ]; then :; else
    echo "NO-GO: ROUTE3_APT_PACKAGES must be the attested pinned set: exact name=version for python3.14, python3.14-minimal, python3.14-venv and every other member built from source package python3.14, no name twice (supplier: Peter)"; bad=1; fi
  # ROUTE3_APT_BASE is the rest of the attested closure (re-checked, never held): exact name=version, no name twice, and no name that is also pinned
  if [[ $ROUTE3_APT_BASE =~ $re ]] && [ -z "$(for t in $ROUTE3_APT_BASE $ROUTE3_APT_PACKAGES; do printf '%s\n' "${t%%=*}"; done | LC_ALL=C sort | uniq -d)" ]; then :; else
    echo "NO-GO: ROUTE3_APT_BASE must be the attested base set: exact name=version, no name twice and none that is also in ROUTE3_APT_PACKAGES (supplier: Peter)"; bad=1; fi
  # the origin field is a comma-separated list of "<archive url> <suite>/<component>" entries, each the exact source text of apt-cache madison
  if [[ $ROUTE3_APT_ORIGIN =~ ^[A-Za-z0-9\ ,=./:_-]+$ ]]; then
    IFS=, read -ra ol <<< "$ROUTE3_APT_ORIGIN"
    for o in "${ol[@]}"; do o=${o# }; o=${o% }; [[ $o =~ ^https?://[^\ ]+\ [A-Za-z0-9._-]+/[A-Za-z0-9._-]+$ ]] || { echo "NO-GO: ROUTE3_APT_ORIGIN entry is not '<url> <suite>/<component>': $o"; bad=1; }; done
  else echo "NO-GO: ROUTE3_APT_ORIGIN is unset or malformed (supplier: Peter)"; bad=1; fi
  [ "$ROUTE3_WHEEL" = jeepney-0.9.0-py3-none-any.whl ] && [ "$ROUTE3_WHEEL_SHA256" = 97e5714520c16fc0a45695e5365a2e11b81ea79bba796e26f9f1d178cb182683 ] || { echo "NO-GO: the wheel is not the accepted pin"; bad=1; }
  return "$bad"
}
route3_tokens() { local t; for t in $ROUTE3_APT_PACKAGES; do printf '%s\n' "$t"; done | LC_ALL=C sort; }
# the objects a first-time provisioning creates; all must be absent before S1 and are absent again after a complete rollback
route3_objects() {
  printf '%s\n' "$ROUTE3_BASE" "$ROUTE3_STAGE" "$ROUTE3_HOME" /usr/local/libexec/freedom-blades-rp11 /etc/sudoers.d/freedom-executor-sa2 /etc/sudoers.d/.freedom-executor-sa2.new \
    /usr/lib/tmpfiles.d/freedom-blades-rp11-polkit-rules.conf /etc/systemd/system/freedom-blades-executor-supervisor.service \
    /etc/systemd/system/multi-user.target.wants/freedom-blades-executor-supervisor.service /var/lib/systemd/linger/freedom-executor \
    /var/lib/freedom-blades-executor /run/freedom-blades-executor
}
# Identity and manager queries are three-valued; only a DEFINITE answer may be read as absence or as "stopped".
# getent(1) documents status 0 = found and 2 = key not found. Every other status (1, 3, 127, a signal ...) is a failed or indeterminate query.
route3_id() { local rc; getent "$1" "$2" >/dev/null 2>&1; rc=$?; case $rc in 0) return 0;; 2) return 2;; *) return 9;; esac; }   # 0 present, 2 absent, 9 indeterminate
# A manager state is read from `systemctl show -p ActiveState --value`, whose successful observation is status 0 plus exactly one state word (also for a unit the manager does not know: inactive). Any other status
# (the manager or the bus does not answer: 1; a usage error: 2 ...) is a failed query EVEN IF it printed a plausible word, and so is empty, unknown or multi-word output: both are "indeterminate", never "stopped".
# (`systemctl is-active` is deliberately not used: it prints the same words with status 3 for inactive, failed and activating alike, so text without a status proves nothing.)
route3_unit() {
  local s rc
  s=$(LC_ALL=C systemctl show -p ActiveState --value "$1" 2>/dev/null); rc=$?
  [ "$rc" -eq 0 ] || { printf 'indeterminate\n'; return 0; }
  case $s in active|activating|reloading|deactivating|inactive|failed) printf '%s\n' "$s";; *) printf 'indeterminate\n';; esac
}
route3_loadstate() {
  local s rc
  s=$(LC_ALL=C systemctl show -p LoadState --value "$1" 2>/dev/null); rc=$?
  if [ "$rc" -eq 0 ] && [[ $s =~ ^[a-z-]+$ ]]; then printf '%s\n' "$s"; else printf 'indeterminate\n'; fi
}
route3_absent_ok() {
  local p k rc bad=0
  while IFS= read -r p; do
    if [ -e "$p" ] || [ -L "$p" ]; then echo "NO-GO: already exists: $p"; bad=1; fi
  done < <(route3_objects)
  for k in passwd group; do
    route3_id "$k" "$ROUTE3_ACCOUNT"; rc=$?
    [ "$rc" -eq 2 ] || { echo "NO-GO: $k $ROUTE3_ACCOUNT exists or could not be queried (status $rc: 0 exists, 9 query failed)"; bad=1; }
  done
  return "$bad"
}
# the deployment is exactly the manifest recorded in the evidence directory, whose own digest is the field
route3_tree_ok() {
  sha256sum --check --status <(printf '%s  %s\n' "$ROUTE3_MANIFEST_SHA256" "$ROUTE3_EVID/MANIFEST.sha256") && route3_stage tree /opt/freedom-route3 "$ROUTE3_EVID/MANIFEST.sha256"
}
# Published evidence is authoritative only if it is a real root-0700 directory, its recorded pre-state still matches the digest list written with it, and its checkpoints start at s1-start.
# S1.0 builds the evidence in ROUTE3_EVID_STAGE and publishes it with one rename(2), so an incomplete S1.0 never leaves anything under this name.
route3_evid_ok() {
  [ -d "$ROUTE3_EVID" ] && [ ! -L "$ROUTE3_EVID" ] && [ "$(stat -c %u:%a "$ROUTE3_EVID")" = 0:700 ] || return 1
  [ -f "$ROUTE3_EVID/pre.sha256" ] && [ -f "$ROUTE3_EVID/checkpoints" ] && [ "$(head -n 1 "$ROUTE3_EVID/checkpoints")" = s1-start ] || return 1
  [ "$(awk '{print $2}' "$ROUTE3_EVID/pre.sha256" | tr '\n' ' ')" = "prestate.dpkg prestate.holds prestate.objects " ] || return 1
  ( cd "$ROUTE3_EVID" && sha256sum --check --status pre.sha256 )
}
route3_pkgs() { dpkg-query -W -f='${Package}\t${Version}\n' | LC_ALL=C sort; }
route3_has_name() { awk -F'\t' -v n="$2" '$1 == n { f = 1 } END { exit f ? 0 : 1 }' "$1"; }
# ---- the apt closure -------------------------------------------------------------------------------------------------------------
# The package-manager serialization assumption, checked mechanically: no process holds an apt or dpkg lock (fcntl or flock; /proc/locks lists both).
route3_apt_idle() {
  local f ino bad=0
  [ -r /proc/locks ] || { echo "NO-GO: /proc/locks is unreadable: an active apt or dpkg run cannot be excluded"; return 1; }
  for f in /var/lib/dpkg/lock-frontend /var/lib/dpkg/lock /var/lib/apt/lists/lock /var/cache/apt/archives/lock; do
    if [ ! -f "$f" ]; then echo "NO-GO: $f is missing: an active apt or dpkg run cannot be excluded"; bad=1; continue; fi
    ino=$(stat -c %i -- "$f") || { bad=1; continue; }
    if awk -v i="$ino" '{ n = split($6, a, ":"); if (a[n] == i) h = 1 } END { exit h ? 0 : 1 }' /proc/locks; then echo "NO-GO: an apt or dpkg run holds $f"; bad=1; fi
  done
  return "$bad"
}
# EVERY archive source that offers exactly name=version must be a listed origin, and at least one must offer it. apt-cache madison prints "name | version | url suite/component arch Packages".
route3_apt_origin_ok() {
  local n=$1 v=$2 out a b c src seen=0 bad=0 o hit allowed
  out=$(LC_ALL=C apt-cache madison "$n") || { echo "NO-GO: apt-cache madison $n failed"; return 1; }
  IFS=, read -ra allowed <<< "$ROUTE3_APT_ORIGIN"
  while IFS='|' read -r a b c; do
    a=${a//[[:space:]]/}; b=${b//[[:space:]]/}
    [ "$a" = "$n" ] && [ "$b" = "$v" ] || continue
    c=${c#"${c%%[![:space:]]*}"}; c=${c%"${c##*[![:space:]]}"}
    # dpkg's own status file is listed for an INSTALLED version as the installed-state marker; it is not an archive source and never an origin
    case $c in /var/lib/dpkg/status|"/var/lib/dpkg/status "*) continue;; esac
    src=${c% Packages}; src=${src% *}; seen=1; hit=0
    for o in "${allowed[@]}"; do o=${o#"${o%%[![:space:]]*}"}; o=${o%"${o##*[![:space:]]}"}; [ "$src" = "$o" ] && hit=1; done
    [ "$hit" -eq 1 ] || { echo "NO-GO: $n=$v is also offered by an origin that is not listed: $src"; bad=1; }
  done <<< "$out"
  [ "$seen" -eq 1 ] || { echo "NO-GO: $n=$v is offered by no configured archive source"; bad=1; }
  return "$bad"
}
# The reviewed PINNED closure against the host, read-only. This plan has NO install path: a member that is absent, installed at another version or offered by an unlisted origin is a hard NO-GO before any mutation.
route3_apt_check() {
  local t n v inst bad=0
  for t in $ROUTE3_APT_PACKAGES; do
    n=${t%%=*}; v=${t#*=}
    inst=$(dpkg-query -W -f='${Version}' "$n" 2>/dev/null)
    if [ -z "$inst" ]; then echo "NO-GO: $n is not installed; this plan never installs a package, so the host is not the reviewed baseline"; bad=1
    elif [ "$inst" != "$v" ]; then echo "NO-GO: $n is installed at $inst, not $v"; bad=1
    else route3_apt_origin_ok "$n" "$v" || bad=1; fi
  done
  return "$bad"
}
# the pinned interpreter packages: every pinned member at its exact version, no changed packaged file (dpkg --verify: LOCAL metadata only), the real interpreter is the reviewed file (sha256sum, independent of Python), and the base set unchanged.
# This is a supplement. The independent proof against the signed archive is route3_gate below.
route3_python_ok() {
  local t n real h bad=0 out
  for t in $ROUTE3_APT_PACKAGES; do
    n=${t%%=*}
    [ "$(dpkg-query -W -f='${Version}' "$n" 2>/dev/null)" = "${t#*=}" ] || { echo "NO-GO: package $n is not at the pinned version"; bad=1; }
  done
  out=$(dpkg --verify $(for t in $ROUTE3_APT_PACKAGES; do printf '%s ' "${t%%=*}"; done)); [ $? -eq 0 ] && [ -z "$out" ] || { echo "NO-GO: dpkg --verify reports a changed packaged file"; bad=1; }
  real=$(readlink -f -- "$ROUTE3_PY"); read -r h _ < <(sha256sum -- "$real") ; [ "$h" = "$ROUTE3_PY_SHA256" ] || { echo "NO-GO: the real interpreter differs from ROUTE3_PY_SHA256"; bad=1; }
  route3_base_ok || bad=1
  return "$bad"
}
# the BASE set of the attested closure: every member installed at exactly its reviewed version and offered only by listed archive origins. Read-only: base packages are never installed, held or changed by this plan,
# so a difference means the host moved since the baseline record was reviewed: re-attest and re-review, never upgrade in place
route3_base_ok() {
  local t n v inst bad=0
  for t in $ROUTE3_APT_BASE; do
    n=${t%%=*}; v=${t#*=}
    inst=$(dpkg-query -W -f='${Version}' "$n" 2>/dev/null)
    [ "$inst" = "$v" ] || { echo "NO-GO: base package $n is at ${inst:-<absent>}, not the attested $v (re-attest and re-review; never upgrade in place)"; bad=1; continue; }
    route3_apt_origin_ok "$n" "$v" || bad=1
  done
  return "$bad"
}
# THE TRUSTED ATTESTATION, run mechanically at EVERY mutating boundary (S1.0, S1.1, S1.2, S1.3, S1.4, S3.1, S3.2, S3.3, S3.5, and S4.1 before it starts anything) and by S0.3 and S2.1: nothing relies on an operator having run S0.3 earlier, and nothing runs from a checkout.
# It (1) requires fields, the three reviewed artifacts (code.tar, baseline.record, reference.record) to be root-owned, non-writable and equal to their field digests; (2) refuses the interpreter unless its SHA-256 (sha256sum, not Python)
# equals ROUTE3_PY_SHA256, the digest taken from the signed-archive package, BEFORE that interpreter runs anything; (3) runs the tool FROM the digest-verified code.tar, which re-attests the whole closure against the baseline record
# (members, versions, architectures, source packages, exact per-member archive origins, interpreter) AND recomputes every member's package metadata and non-conffile payload from the installed files and compares them with the
# signed-archive reference (a same-name, same-version package from a removed or untrusted repository, or crafted locally with matching metadata, fails here); and (4) repeats the dpkg and base-set checks. Any member missing,
# changed or extra is NO-GO. It installs, upgrades, holds and writes nothing. Status 0 ok, 1 NO-GO, 2 untrusted or mismatching artifact.
route3_gate() (
  set -o pipefail; export PATH="$ROUTE3_PATH"
  local d f real h A="$ROUTE3_ART/$ROUTE3_RELEASE_REV" bad=0
  route3_fields_ok || return 1
  for d in "$ROUTE3_ART" "$A"; do
    [ -d "$d" ] && [ ! -L "$d" ] && [ "$(stat -c %u "$d")" = 0 ] && [ $(( 0$(stat -c %a "$d") & 022 )) -eq 0 ] || { echo "NO-GO: artifact directory is not a real root-owned non-writable directory: $d"; return 2; }
  done
  for f in "$A/code.tar" "$A/baseline.record" "$A/reference.record"; do
    [ -f "$f" ] && [ ! -L "$f" ] && [ "$(stat -c %u:%h "$f")" = 0:1 ] && [ $(( 0$(stat -c %a "$f") & 022 )) -eq 0 ] || { echo "NO-GO: artifact is not a real root-owned non-writable file: $f"; return 2; }
  done
  sha256sum --check --status <(printf '%s  %s\n' "$ROUTE3_ARCHIVE_SHA256" "$A/code.tar" "$ROUTE3_BASELINE_SHA256" "$A/baseline.record" "$ROUTE3_REFERENCE_SHA256" "$A/reference.record") \
    || { echo "NO-GO: code.tar, baseline.record or reference.record differs from its field digest"; return 2; }
  real=$(readlink -f -- "$ROUTE3_PY") && [ -n "$real" ] && read -r h _ < <(sha256sum -- "$real") && [ "$h" = "$ROUTE3_PY_SHA256" ] \
    || { echo "NO-GO: the interpreter differs from ROUTE3_PY_SHA256 (the signed-archive package's file); it is not run"; return 1; }
  tar --extract --to-stdout --file "$A/code.tar" tools/route3_release_record.py \
    | /usr/bin/env -i PATH=/usr/bin:/bin "$ROUTE3_PY" -I -S -B - verify-host --record "$A/baseline.record" --reference "$A/reference.record" \
        --field "APT_PACKAGES=$ROUTE3_APT_PACKAGES" --field "APT_BASE=$ROUTE3_APT_BASE" --field "APT_ORIGIN=$ROUTE3_APT_ORIGIN" --field "PY_SHA256=$ROUTE3_PY_SHA256" \
        --field "BASELINE_SHA256=$ROUTE3_BASELINE_SHA256" --field "REFERENCE_SHA256=$ROUTE3_REFERENCE_SHA256" || bad=1
  route3_python_ok || bad=1
  return "$bad"
)
```

### F. Release fields — every `UNSET` is a hard NO-GO (the supplier edits this block in the reviewed release record, never on the host ad hoc)

```bash
ROUTE3_RELEASE_REV=UNSET
ROUTE3_ARCHIVE_SHA256=UNSET
ROUTE3_MANIFEST_SHA256=UNSET
ROUTE3_APT_PACKAGES="UNSET"
ROUTE3_APT_BASE="UNSET"
ROUTE3_APT_ORIGIN="UNSET"
ROUTE3_PY_SHA256=UNSET
ROUTE3_BASELINE_SHA256=UNSET
ROUTE3_REFERENCE_SHA256=UNSET
ROUTE3_SA2_TREE_SHA256=UNSET
ROUTE3_WHEEL=jeepney-0.9.0-py3-none-any.whl
ROUTE3_WHEEL_SHA256=97e5714520c16fc0a45695e5365a2e11b81ea79bba796e26f9f1d178cb182683
```

### S0 — read-only production preflight

```bash
# S0.0 — AUTHORITY: NONE. WITHDRAWN on 2026-11-11 and never to be run. It assumed python3.14 was absent and proposed an apt INSTALL closure from a solver simulation; production already has Ubuntu Python 3.14 installed.
# The block only refuses: it reads nothing, writes nothing and proposes nothing. It is superseded by S0.A (read-only attestation of the installed closure).
( echo "NO-GO: S0.0 is withdrawn (it assumed Python 3.14 absent); use S0.A, the read-only attestation of the installed baseline"; exit 64 ); rc=$?; echo "[S0.0 rc=$rc]"; echo "STOP: nothing was read or changed"; (exit "$rc")
```

```bash
# S0.A — AUTHORITY: Peter's authorization of a read-only production preflight. Reads only and writes nothing; UNPRIVILEGED (refuses to run as root). Needs block D only (no field).
# Prints the baseline record of the INSTALLED Python 3.14 closure (release-record procedure, step 3). ROUTE3_TOOL names a regular copy of tools/route3_release_record.py from ROUTE3_RELEASE_REV; its digest is printed
# on the error stream first and must equal `git show <REV>:tools/route3_release_record.py | sha256sum` computed on the workstation. Copy the printed record off the host; the block creates no file there.
( export PATH="$ROUTE3_PATH"
  [ "$(id -u)" -ne 0 ] || { echo "NO-GO: S0.A is unprivileged; do not run it as root"; exit 2; }
  [ -f "${ROUTE3_TOOL:-}" ] && [ ! -L "$ROUTE3_TOOL" ] || { echo "NO-GO: set ROUTE3_TOOL to a regular copy of tools/route3_release_record.py"; exit 2; }
  sha256sum -- "$ROUTE3_TOOL" >&2 || exit 2
  /usr/bin/env -i PATH=/usr/bin:/bin "$ROUTE3_PY" -I -S -B "$ROUTE3_TOOL" attest-host
); rc=$?; echo "[S0.A rc=$rc]"; [ "$rc" -eq 0 ] || echo "STOP: nothing was changed; return the findings to Peter"; (exit "$rc")
```

```bash
# S0.1 — AUTHORITY: none needed (reads shell variables only). No effect on the host.
route3_fields_ok; rc=$?; echo "[S0.1 rc=$rc]"; [ "$rc" -eq 0 ] || echo "STOP: NO-GO — the plan is not ready; supply every field"; (exit "$rc")
```

```bash
# S0.2 — AUTHORITY: Peter's authorization of a read-only production preflight. Reads only; writes nothing.
( export PATH="$ROUTE3_PATH"; bad=0; A="$ROUTE3_ART/$ROUTE3_RELEASE_REV"
  route3_fields_ok || exit 1
  route3_absent_ok || bad=1
  route3_apt_idle || bad=1
  route3_apt_check || bad=1
  for d in "$ROUTE3_ART" "$A" "$A/wheelhouse"; do
    [ -d "$d" ] && [ ! -L "$d" ] && [ "$(stat -c %u "$d")" = 0 ] && [ $(( 0$(stat -c %a "$d") & 022 )) -eq 0 ] || { echo "NO-GO: artifact directory is not a real root-owned non-writable directory: $d"; bad=1; }
  done
  for f in "$A/code.tar" "$A/MANIFEST.sha256" "$A/wheelhouse/$ROUTE3_WHEEL"; do
    [ -f "$f" ] && [ ! -L "$f" ] && [ "$(stat -c %u:%h "$f")" = 0:1 ] && [ $(( 0$(stat -c %a "$f") & 022 )) -eq 0 ] || { echo "NO-GO: artifact is not a real root-owned non-writable file: $f"; bad=1; }
  done
  sha256sum --check --status <(printf '%s  %s\n' "$ROUTE3_ARCHIVE_SHA256" "$A/code.tar" "$ROUTE3_MANIFEST_SHA256" "$A/MANIFEST.sha256" "$ROUTE3_WHEEL_SHA256" "$A/wheelhouse/$ROUTE3_WHEEL") || { echo "NO-GO: an artifact differs from its field digest"; bad=1; }
  avail=$(df --output=avail -B1 /opt | tail -n 1); [ "${avail:-0}" -ge 536870912 ] || { echo "NO-GO: less than 512 MiB free under /opt"; bad=1; }
  exit "$bad"
); rc=$?; echo "[S0.2 rc=$rc]"; [ "$rc" -eq 0 ] || echo "STOP: NO-GO — nothing was changed"; (exit "$rc")
```

```bash
# S0.3 — AUTHORITY: Peter's authorization of a read-only production preflight. Reads only; writes nothing. Run as root after S0.1 and S0.2.
# The installed-baseline gate (block D, route3_gate). It requires the reviewed baseline record (<ART>/<REV>/baseline.record) and the signed-archive payload reference (<ART>/<REV>/reference.record) to be the ones block F names, runs the
# tool FROM THE DIGEST-VERIFIED code.tar (never from a checkout) and requires the host to still be exactly that baseline: same closure, versions, architectures, source packages, exact per-member archive origins and interpreter, no
# changed packaged file, AND every member's installed package metadata and non-conffile payload equal to the signed-archive package. A missing, changed or additional member, an unreviewed origin, a payload or metadata difference or any drift is
# NO-GO: nothing here installs, upgrades or holds anything. S0.3 is NOT the control that protects S1 or S3: those blocks run the same gate themselves, so skipping S0.3 skips nothing.
( export PATH="$ROUTE3_PATH"
  route3_gate || exit "$?"
); rc=$?; echo "[S0.3 rc=$rc]"; if [ "$rc" -eq 0 ]; then echo "ok: the host still is the reviewed baseline"; else echo "STOP: NO-GO — the host is not the reviewed baseline; nothing was changed"; fi; (exit "$rc")
```

### S1 — inert provisioning (ends at STOP-A)

```bash
# S1.0 — AUTHORITY: Peter's written provisioning authorization (stage S1). Records the pre-state every rollback relies on, as ONE transaction: it builds /root/route3-evidence.new (root 0700) and publishes it as
# /root/route3-evidence by a single rename(2) only after every file is written and synced. Nothing but evidence is created. A status other than 0 leaves either nothing published (run block R0) or a complete published pre-state (run block R).
( set -o pipefail; umask 077; export PATH="$ROUTE3_PATH"; cd / || exit 1; S=$ROUTE3_EVID_STAGE
  route3_fields_ok || exit 1
  route3_gate || { echo "NO-GO: the trusted baseline attestation failed; nothing was written"; exit 9; }
  route3_absent_ok || exit 2
  { [ ! -e "$ROUTE3_EVID" ] && [ ! -L "$ROUTE3_EVID" ]; } || { echo "NO-GO: an evidence directory already exists; a previous attempt needs rollback R first"; exit 3; }
  { [ ! -e "$S" ] && [ ! -L "$S" ]; } || { echo "NO-GO: an unpublished S1.0 stage exists; run block R0 first"; exit 3; }
  install -d -m 0700 -o root -g root -- "$S" || exit 4
  route3_pkgs > "$S/prestate.dpkg" || exit 5
  apt-mark showhold | LC_ALL=C sort > "$S/prestate.holds" || exit 5
  route3_objects | while IFS= read -r p; do printf 'absent %s\n' "$p"; done > "$S/prestate.objects" || exit 5
  printf 'absent passwd %s\nabsent group %s\n' "$ROUTE3_ACCOUNT" "$ROUTE3_ACCOUNT" >> "$S/prestate.objects" || exit 5
  ( cd "$S" && sha256sum -- prestate.dpkg prestate.holds prestate.objects > pre.sha256 ) || exit 5
  printf 's1-start\n' > "$S/checkpoints" || exit 5
  sync -- "$S/prestate.dpkg" "$S/prestate.holds" "$S/prestate.objects" "$S/pre.sha256" "$S/checkpoints" "$S" || exit 6
  mv --no-target-directory --no-clobber -- "$S" "$ROUTE3_EVID" || exit 7
  { [ ! -e "$S" ] && route3_evid_ok; } || { echo "NO-GO: the evidence was not published"; exit 7; }
  sync -- "${ROUTE3_EVID%/*}" || exit 8
); rc=$?; echo "[S1.0 rc=$rc]"; [ "$rc" -eq 0 ] || echo "STOP: run block R0 if /root/route3-evidence.new exists, or block R if /root/route3-evidence exists; nothing else was changed"; (exit "$rc")
```

```bash
# S1.1 — AUTHORITY: Peter's written provisioning authorization (stage S1). Holds the reviewed PINNED Python packages (ROUTE3_APT_PACKAGES; the base set is never held). THIS PLAN INSTALLS NO PACKAGE: there is no install path, no solver run
# and no apt transaction. Before anything is recorded or held it reruns the full trusted attestation (route3_gate: baseline record, signed-archive payload reference, installed payload and metadata, from the digest-verified artifacts);
# a missing, changed or extra closure member or payload is NO-GO with nothing mutated, whether or not S0.3 was ever run. Network: none is needed.
# NOTHING S1.1 holds is ever unheld by this plan: rollback of the package set is an ATTENDED boundary (block R, status 28), decided only by Peter from the evidence kept here.
# A pre-snapshot (beforeC1.dpkg) and the Route 3 hold list (held.new) are recorded first; afterC1.dpkg records the package set afterwards. If the block dies, the evidence on disk is what the attending operator has.
( set -o pipefail; umask 022; export PATH="$ROUTE3_PATH"; cd / || exit 1; E=$ROUTE3_EVID
  route3_fields_ok || exit 1
  route3_evid_ok || { echo "NO-GO: S1.0 has not completed (no published, verified evidence)"; exit 2; }
  ! grep -qx begin-C1 "$E/checkpoints" || { echo "NO-GO: S1.1 was already begun; run block R, never retry in place"; exit 2; }
  route3_apt_idle || exit 2
  a=$(dpkg --audit 2>&1); [ $? -eq 0 ] && [ -z "$a" ] || { echo "NO-GO: dpkg --audit reports a package in a partial state"; exit 2; }
  route3_gate || { echo "NO-GO: the trusted baseline attestation failed; no package was held and nothing was recorded"; exit 2; }
  route3_apt_check || exit 2
  route3_pkgs > "$E/beforeC1.dpkg" || exit 3
  sync -- "$E/beforeC1.dpkg" && sync -- "$E" || exit 3
  route3_cp begin-C1 || exit 3
  : > "$E/held.new"
  for t in $ROUTE3_APT_PACKAGES; do
    n=${t%%=*}
    grep -qxF -- "$n" "$E/prestate.holds" || printf '%s\n' "$n" >> "$E/held.new"
  done
  sync -- "$E/held.new" || exit 6
  if [ -s "$E/held.new" ]; then apt-mark hold -- $(cat "$E/held.new") || exit 6; fi
  route3_pkgs > "$E/afterC1.dpkg" || exit 5
  route3_gate || { echo "NO-GO: the trusted baseline attestation failed after the hold"; exit 4; }
  route3_cp done-C1 || exit 7
); rc=$?; echo "[S1.1 rc=$rc]"; [ "$rc" -eq 0 ] || echo "STOP: run block R; do not retry in place"; (exit "$rc")
```

```bash
# S1.2 — AUTHORITY: Peter's written provisioning authorization (stage S1). Builds and publishes /opt/freedom-route3/{code,venv} from the controlled artifact set only.
# Source custody: the artifacts are root-only; they are copied into a root-0700 staging directory on the same filesystem and every digest is verified ON THE COPIES that are then used.
# Publication: one rename(2) of the verified staging directory; the final tree is verified again and moved back if it fails. No recursive chown/chmod is used.
( umask 022; export PATH="$ROUTE3_PATH"; cd / || exit 1; A="$ROUTE3_ART/$ROUTE3_RELEASE_REV"
  route3_fields_ok || exit 1
  route3_evid_ok && grep -qx done-C1 "$ROUTE3_EVID/checkpoints" || { echo "NO-GO: S1.0/S1.1 have not completed"; exit 2; }
  route3_gate || { echo "NO-GO: the trusted baseline attestation failed; nothing was built"; exit 2; }
  route3_cp begin-C2 || exit 2
  for d in "$ROUTE3_ART" "$A" "$A/wheelhouse"; do
    [ -d "$d" ] && [ ! -L "$d" ] && [ "$(stat -c %u "$d")" = 0 ] && [ $(( 0$(stat -c %a "$d") & 022 )) -eq 0 ] || { echo "NO-GO: untrusted artifact directory: $d"; exit 3; }
  done
  for f in "$A/code.tar" "$A/MANIFEST.sha256" "$A/wheelhouse/$ROUTE3_WHEEL"; do
    [ -f "$f" ] && [ ! -L "$f" ] && [ "$(stat -c %u:%h "$f")" = 0:1 ] && [ $(( 0$(stat -c %a "$f") & 022 )) -eq 0 ] || { echo "NO-GO: untrusted artifact file: $f"; exit 3; }
  done
  [ ! -e "$ROUTE3_STAGE" ] && [ ! -L "$ROUTE3_STAGE" ] && [ ! -e "$ROUTE3_BASE" ] && [ ! -L "$ROUTE3_BASE" ] || { echo "NO-GO: a staging or deployment path already exists (partial state): run block R"; exit 4; }
  install -d -m 0700 -o root -g root -- "$ROUTE3_STAGE" "$ROUTE3_STAGE/in" "$ROUTE3_STAGE/in/wheelhouse" || exit 5
  install -m 0600 -o root -g root -- "$A/code.tar" "$A/MANIFEST.sha256" "$ROUTE3_STAGE/in/" || exit 5
  install -m 0600 -o root -g root -- "$A/wheelhouse/$ROUTE3_WHEEL" "$ROUTE3_STAGE/in/wheelhouse/" || exit 5
  sha256sum --check --status <(printf '%s  %s\n' "$ROUTE3_ARCHIVE_SHA256" "$ROUTE3_STAGE/in/code.tar" "$ROUTE3_MANIFEST_SHA256" "$ROUTE3_STAGE/in/MANIFEST.sha256" "$ROUTE3_WHEEL_SHA256" "$ROUTE3_STAGE/in/wheelhouse/$ROUTE3_WHEEL") || { echo "NO-GO: an artifact differs from its field digest"; exit 6; }
  route3_stage archive "$ROUTE3_STAGE/in/code.tar" "$ROUTE3_STAGE/in/MANIFEST.sha256" || exit 7
  install -d -m 0755 -o root -g root -- "$ROUTE3_STAGE/code" || exit 8
  tar --extract --file "$ROUTE3_STAGE/in/code.tar" --directory "$ROUTE3_STAGE/code" --no-same-owner --no-same-permissions --numeric-owner || exit 8
  /usr/bin/env -i PATH=/usr/bin:/bin "$ROUTE3_PY" -I -m venv "$ROUTE3_STAGE/venv" || exit 9
  printf 'jeepney==0.9.0 --hash=sha256:%s\n' "$ROUTE3_WHEEL_SHA256" > "$ROUTE3_STAGE/in/requirements.txt" || exit 9
  /usr/bin/env -i PATH=/usr/bin:/bin "$ROUTE3_STAGE/venv/bin/python" -I -m pip install --no-index --no-deps --no-compile --no-cache-dir --disable-pip-version-check --require-hashes \
      --find-links "$ROUTE3_STAGE/in/wheelhouse" --requirement "$ROUTE3_STAGE/in/requirements.txt" || exit 10
  /usr/bin/env -i PATH=/usr/bin:/bin "$ROUTE3_STAGE/venv/bin/python" -I -m pip uninstall --yes --disable-pip-version-check pip || exit 11
  route3_stage tree "$ROUTE3_STAGE" "$ROUTE3_STAGE/in/MANIFEST.sha256" || exit 12
  install -m 0600 -o root -g root -- "$ROUTE3_STAGE/in/MANIFEST.sha256" "$ROUTE3_EVID/MANIFEST.sha256" || exit 12
  rm -r --one-file-system -- "$ROUTE3_STAGE/in" || exit 13
  [ "$(ls -A "$ROUTE3_STAGE" | LC_ALL=C sort | tr '\n' ' ')" = "code venv " ] || { echo "NO-GO: unexpected entry in the staged deployment"; exit 13; }
  chmod 0755 -- "$ROUTE3_STAGE" || exit 13
  mv --no-target-directory --no-clobber -- "$ROUTE3_STAGE" "$ROUTE3_BASE" || exit 14
  if [ -e "$ROUTE3_STAGE" ] || ! route3_tree_ok; then
    echo "NO-GO: the published tree failed verification; withdrawing it"
    mv --no-target-directory --no-clobber -- "$ROUTE3_BASE" "$ROUTE3_STAGE"; chmod 0700 -- "$ROUTE3_STAGE" 2>/dev/null
    exit 15
  fi
  route3_cp done-C2 || exit 16
); rc=$?; echo "[S1.2 rc=$rc]"; [ "$rc" -eq 0 ] || echo "STOP: run block R; do not retry in place"; (exit "$rc")
```

```bash
# S1.3 — AUTHORITY: Peter's written provisioning authorization (stage S1). Creates the dormant account, its same-named group and its home. It does NOT enable linger.
( umask 022; export PATH="$ROUTE3_PATH"; cd / || exit 1
  grep -qx done-C2 "$ROUTE3_EVID/checkpoints" || { echo "NO-GO: S1.2 has not completed"; exit 2; }
  route3_gate || { echo "NO-GO: the trusted baseline attestation failed; no account was created"; exit 2; }
  route3_cp begin-C3 || exit 2
  useradd --system --create-home --home-dir "$ROUTE3_HOME" --shell /usr/sbin/nologin "$ROUTE3_ACCOUNT" || exit 3
  ent=$(getent passwd "$ROUTE3_ACCOUNT") || exit 4
  IFS=: read -r _ _ uid gid _ home shell <<< "$ent"
  [ "$uid" -gt 0 ] && [ "$home" = "$ROUTE3_HOME" ] && [ "$shell" = /usr/sbin/nologin ] || { echo "NO-GO: account facts differ"; exit 4; }
  [ "$(getent group "$ROUTE3_ACCOUNT" | cut -d: -f3)" = "$gid" ] || { echo "NO-GO: primary group differs"; exit 4; }
  [ "$(stat -c %u "$ROUTE3_HOME")" = "$uid" ] || { echo "NO-GO: home is not owned by the account"; exit 4; }
  [ ! -e /var/lib/systemd/linger/freedom-executor ] || { echo "NO-GO: linger exists"; exit 4; }
  route3_cp done-C3 || exit 5
); rc=$?; echo "[S1.3 rc=$rc]"; [ "$rc" -eq 0 ] || echo "STOP: run block R; do not retry in place"; (exit "$rc")
```

```bash
# S1.4 — AUTHORITY: Peter's written provisioning authorization (stage S1). Installs the Polkit tmpfiles.d fragment with the reviewed copy inside the verified deployment (never the ordinary checkout).
# Effect: one root-owned 0644 file under /usr/lib/tmpfiles.d; nothing runs systemd-tmpfiles, restarts or reloads Polkit now.
( umask 022; export PATH="$ROUTE3_PATH"; cd / || exit 1
  grep -qx done-C3 "$ROUTE3_EVID/checkpoints" || { echo "NO-GO: S1.3 has not completed"; exit 2; }
  route3_tree_ok || exit 3
  route3_gate || { echo "NO-GO: the trusted baseline attestation failed; the tmpfiles fragment was not installed"; exit 2; }
  route3_cp begin-C4 || exit 2
  /usr/bin/env -i PATH=/usr/bin:/bin "$ROUTE3_PY" -I -S -c "$ROUTE3_ENTRY" "$ROUTE3_TMPFILES" install; r=$?
  [ "$r" -eq 0 ] || { echo "tmpfiles install status $r"; exit 4; }
  route3_cp done-C4 || exit 5
); rc=$?; echo "[S1.4 rc=$rc]"
if [ "$rc" -eq 0 ]; then echo "STOP-A: provisioning is complete. Run S2 (read-only). Do NOT arm, install or start under this authority: stage S3 is a separate authorization."
else echo "STOP: run block R; do not retry in place"; fi; (exit "$rc")
```

### S2 — read-only verification of STOP-A

```bash
# S2.1 — AUTHORITY: same as S1 (read-only). Proves the STOP-A state: the deployment equals the manifest, the Python identity is unchanged, and nothing can start the supervisor.
( export PATH="$ROUTE3_PATH"; bad=0; cd / || exit 1
  route3_fields_ok || exit 1
  route3_tree_ok || bad=1
  route3_gate || bad=1
  ent=$(getent passwd "$ROUTE3_ACCOUNT") || { echo "FAIL: account is absent or the query failed"; exit 1; }
  IFS=: read -r _ _ uid _ _ home shell <<< "$ent"
  [ "$home" = "$ROUTE3_HOME" ] && [ "$shell" = /usr/sbin/nologin ] || { echo "FAIL: account facts"; bad=1; }
  for p in /var/lib/systemd/linger/freedom-executor /run/user/"$uid" /etc/systemd/system/freedom-blades-executor-supervisor.service \
           /etc/systemd/system/multi-user.target.wants/freedom-blades-executor-supervisor.service /etc/sudoers.d/freedom-executor-sa2 /usr/local/libexec/freedom-blades-rp11 \
           /var/lib/freedom-blades-executor /run/freedom-blades-executor "$ROUTE3_STAGE"; do
    if [ -e "$p" ] || [ -L "$p" ]; then echo "FAIL: exists at STOP-A: $p"; bad=1; fi
  done
  # every manager answer is status-aware (route3_loadstate, route3_unit): a failed or unanswered query is a FAIL, never "absent" or "stopped"
  [ "$(route3_loadstate freedom-blades-executor-supervisor.service)" = not-found ] || { echo "FAIL: the manager does not report the supervisor unit as not-found (or cannot be queried)"; bad=1; }
  lu=$(systemctl list-units --all --no-legend 'freedom-blades-executor*' 'freedom-executor-stop-*'); lrc=$?
  { [ "$lrc" -eq 0 ] && [ -z "$lu" ]; } || { echo "FAIL: a Route 3 unit is loaded (or the manager cannot be queried; status $lrc)"; bad=1; }
  [ "$(route3_unit "user@$uid.service")" = inactive ] || { echo "FAIL: the account's user manager is not inactive (or cannot be queried)"; bad=1; }
  pgrep -u "$uid" >/dev/null; [ $? -eq 1 ] || { echo "FAIL: a process runs as the account"; bad=1; }
  F=freedom-blades-rp11-polkit-rules.conf
  cmp -s "/usr/lib/tmpfiles.d/$F" "$ROUTE3_BASE/code/infra/tmpfiles.d/$F" && [ "$(stat -c %u:%a "/usr/lib/tmpfiles.d/$F")" = 0:644 ] || { echo "FAIL: tmpfiles fragment differs from the manifest copy"; bad=1; }
  exit "$bad"
); rc=$?; echo "[S2.1 rc=$rc]"; [ "$rc" -eq 0 ] && echo "STOP-A verified." || echo "STOP: STOP-A is not established; run block R"; (exit "$rc")
```

S2.2 is the **post-provision tmpfiles check** below (exit 12 is the expected status at STOP-A until the next boot; it must be 0 after that boot, before S3). S2.3: the read-only v2 production checklist of
[handback §6](../review/route-3-production-readiness-handback.md) may be run; items for S3-only objects report them absent.

### R0 — recovery of an incomplete S1.0 (nothing but evidence was ever written)

S1.0 builds its evidence in `/root/route3-evidence.new` and publishes it by one rename. A failure or kill at any instruction before that rename leaves **no** `/root/route3-evidence`, so no rollback input exists and R refuses (status 20); the
unpublished stage is not a pre-state — only publication makes one. R0 removes that one literal directory, and only when it can prove the host holds nothing of any later stage; otherwise it changes nothing and escalates. After status 0,
S1.0 may be run again. R0 never touches `/root/route3-evidence`: a published pre-state, with or without later markers, is real evidence and belongs to block R.

```bash
# R0 — AUTHORITY: Peter's written provisioning authorization (stage S1) or the operator's duty to clear a failed S1.0. Idempotent. Removes only the literal directory /root/route3-evidence.new.
( set -o pipefail; umask 022; export PATH="$ROUTE3_PATH"; cd / || exit 1; S=$ROUTE3_EVID_STAGE; bad=0
  [ "$S" = /root/route3-evidence.new ] || { echo "REFUSE: the stage path is not the fixed literal"; exit 30; }
  if [ -e "$ROUTE3_EVID" ] || [ -L "$ROUTE3_EVID" ]; then echo "REFUSE: published evidence exists; R0 never removes it (use block R)"; exit 31; fi
  if [ ! -e "$S" ] && [ ! -L "$S" ]; then echo "nothing to recover: no unpublished S1.0 stage"; exit 0; fi
  { [ -d "$S" ] && [ ! -L "$S" ] && [ "$(stat -c %u:%a "$S")" = 0:700 ] && ! mountpoint -q -- "$S"; } || { echo "ESCALATE: the stage is not a real root-0700 directory"; exit 32; }
  while IFS= read -r -d '' e; do
    case ${e##*/} in prestate.dpkg|prestate.holds|prestate.objects|pre.sha256|checkpoints) ;; *) echo "ESCALATE: unexpected entry in the stage: $e"; bad=1; continue;; esac
    { [ "${e%/*}" = "$S" ] && [ -f "$e" ] && [ ! -L "$e" ]; } || { echo "ESCALATE: the stage entry is not a plain file: $e"; bad=1; }
  done < <(find "$S" -mindepth 1 -print0)
  [ "$bad" -eq 0 ] || exit 33
  if [ -e "$S/checkpoints" ] && [ -n "$(grep -vx s1-start "$S/checkpoints")" ]; then echo "ESCALATE: the stage carries a later-stage marker"; exit 34; fi
  route3_absent_ok || { echo "ESCALATE: an object of a later stage exists, or the account/group cannot be queried: use block R"; exit 35; }
  rm -r --one-file-system -- "$S" || exit 36
  [ ! -e "$S" ] && [ ! -L "$S" ] || exit 36
); rc=$?; echo "[R0 rc=$rc]"; [ "$rc" -eq 0 ] && echo "Incomplete S1.0 cleared. S1.0 may be run again." || echo "ESCALATE to Peter: make no further change"; (exit "$rc")
```

### R — rollback of inert provisioning (S1) — run after any non-zero S1 status, or to undo STOP-A

Rolls back **only objects this operation created**, using the pre-state recorded by S1.0: an object that existed before is never touched, and a checkpoint is undone only if its `begin-` marker exists (a step that failed halfway is
therefore undone too). Every action is idempotent, targets one exact path, uses no glob, never `rm -rf` a variable that is not first compared with its fixed literal, and never removes, purges, downgrades, autoremoves, holds or unholds **any** package (see below). It is
**not** a rollback of S3 (use R3) and `installer remove` is not used here: nothing was installed. No reboot is required or wanted; a reboot after S1.4 only creates the empty `/run/polkit-1/rules.d`, which is harmless
and removed at the next boot after the fragment is gone. The evidence directory is kept.

Packages and holds — **an attended boundary; R never mutates them.** R runs no `apt-get remove`, `apt remove`, `dpkg --remove`, `dpkg --purge`, `apt-get autoremove`, downgrade, `apt-mark hold` or `apt-mark unhold`, after success, after an ordinary or partial failure, after a signal or kill,
with malformed or missing evidence, and for a completed STOP-A withdrawal. No package delta, PID, timestamp, lock observation or combination of them is authorization to do so, and attribution of a package effect to this plan is not decidable by it. **This plan installs no package at all** (the former S1.1 apt transaction, its
in-transaction hooks and the solver preflight were removed on 2026-11-11 after independent review: an `apt-get install` path in a plan that only attests an installed baseline could have installed a missing member if the operator skipped the attestation).

S1.1 keeps root-only durable evidence in `/root/route3-evidence` for the attending operator: the pre-state (`prestate.dpkg`, `prestate.holds`, `beforeC1.dpkg`), the Route 3 hold list (`held.new`) and the later package and hold state (`afterC1.dpkg`, `now.dpkg`, `now.holds`).

When R reaches C1 it compares the current package set and hold list with the recorded pre-state:

* **exactly equal** (for example S1.1 failed before any effect): R reports that no package or hold recovery is required and continues with its final verification;
* **any difference**: R changes no package and no hold, preserves all evidence, prints the exact differences, does **not** print `Pre-state restored`, and exits **28**. Attended recovery is required. The plan gives the operator these facts and the direction to escalate to Peter; it contains no manual removal recipe.
  A later package-removal decision is outside this plan and needs Peter's explicit direction based on the kept evidence.

R still undoes the later S1 objects — the tmpfiles fragment (C4), the dormant account (C3) and the deployment tree (C2) — in reverse order under their own controls **before** it reaches this boundary, so a status-28 R is a *partial* rollback: those objects are gone, the packages and holds are not. A second or later R is
stable and non-mutating for packages and holds; it only re-verifies and finishes the independently safe later-S1 cleanup. A completed STOP-A withdrawal therefore reaches status 0 only when the packages and holds already equal the captured state; after a successful S1.1 it ends at status 28.
R0 remains limited to incomplete S1.0 evidence and R3 to the rollback from S3 to STOP-A; neither mutates the S1.1 package set.
Identity and manager queries are three-valued (`route3_id`, `route3_unit`): only status 2 from `getent` is absence, and a manager state counts only when `systemctl show -p ActiveState --value` exits **0** and prints one of `active`, `activating`, `reloading`, `deactivating`,
`inactive`, `failed`; any other status — even one that printed `inactive`, `failed` or `active` — or empty/unknown output is *indeterminate*. An unanswerable query is status 27 (25 inside the linger step), never "restored".

```bash
# R — AUTHORITY: Peter's written provisioning authorization (stage S1) or the operator's duty to restore the captured pre-state. Idempotent. Status 0 only when the pre-state is restored.
( set -o pipefail; umask 022; export PATH="$ROUTE3_PATH"; cd / || exit 1; esc=0; E=$ROUTE3_EVID
  route3_evid_ok || { echo "ESCALATE: no verified recorded pre-state; nothing was removed (if /root/route3-evidence.new exists, run block R0)"; exit 20; }
  has() { grep -qx -- "$1" "$E/checkpoints"; }
  pre() { grep -qxF -- "absent $1" "$E/prestate.objects"; }
  if has begin-C4; then
    if [ -f "$ROUTE3_TMPFILES" ]; then
      /usr/bin/env -i PATH=/usr/bin:/bin "$ROUTE3_PY" -I -S -c "$ROUTE3_ENTRY" "$ROUTE3_TMPFILES" remove; r=$?
      [ "$r" -eq 0 ] || { echo "ESCALATE: tmpfiles remove status $r"; esc=21; }
    elif [ -e /usr/lib/tmpfiles.d/freedom-blades-rp11-polkit-rules.conf ]; then echo "ESCALATE: tmpfiles fragment present but the tool is not"; esc=21; fi
  fi
  if has begin-C3 && [ "$esc" -eq 0 ]; then
    if pre "passwd $ROUTE3_ACCOUNT" && pre "group $ROUTE3_ACCOUNT" && pre "$ROUTE3_HOME"; then
      route3_id passwd "$ROUTE3_ACCOUNT"; ps=$?
      if [ "$ps" -eq 0 ]; then
        ent=$(getent passwd "$ROUTE3_ACCOUNT") && uid=$(printf '%s\n' "$ent" | cut -d: -f3) && [ -n "$uid" ] || { echo "ESCALATE: the account cannot be read"; esc=27; }
        if [ "$esc" -eq 0 ]; then
          us=$(route3_unit "user@$uid.service")
          if [ -e /var/lib/systemd/linger/freedom-executor ] || [ "$us" = active ] || [ "$us" = activating ]; then echo "ESCALATE: linger or a user manager exists (S3 was begun: use R3 first)"; esc=22
          elif [ "$us" != inactive ] && [ "$us" != failed ]; then echo "ESCALATE: the user manager state cannot be established ($us)"; esc=27
          else userdel --remove "$ROUTE3_ACCOUNT" || { echo "ESCALATE: userdel failed"; esc=22; }; fi
        fi
      elif [ "$ps" -ne 2 ]; then echo "ESCALATE: the account query failed (status $ps): absence is not established"; esc=27; fi
      if [ "$esc" -eq 0 ]; then
        route3_id group "$ROUTE3_ACCOUNT"; gs=$?
        if [ "$gs" -eq 0 ]; then groupdel "$ROUTE3_ACCOUNT" || esc=22
        elif [ "$gs" -ne 2 ]; then echo "ESCALATE: the group query failed (status $gs): absence is not established"; esc=27; fi
      fi
      if [ "$esc" -eq 0 ] && [ -d "$ROUTE3_HOME" ] && [ ! -L "$ROUTE3_HOME" ] && [ "$ROUTE3_HOME" = /home/freedom-executor ]; then rm -r --one-file-system -- "$ROUTE3_HOME" || esc=22; fi
    else echo "ESCALATE: the account, group or home existed before this operation; it is not ours to remove"; esc=22; fi
  fi
  if has begin-C2 && [ "$esc" -eq 0 ]; then
    if [ -e /etc/systemd/system/freedom-blades-executor-supervisor.service ]; then echo "ESCALATE: the supervisor fragment exists (S3 was begun: use R3 first)"; esc=23; fi
    for t in "$ROUTE3_STAGE" "$ROUTE3_BASE"; do
      [ "$esc" -eq 0 ] || break
      if [ -e "$t" ] || [ -L "$t" ]; then
        if { [ "$t" = /opt/freedom-route3.stage ] || [ "$t" = /opt/freedom-route3 ]; } && pre "$t" && [ -d "$t" ] && [ ! -L "$t" ] && ! mountpoint -q -- "$t"; then
          rm -r --one-file-system -- "$t" || esc=23
        else echo "ESCALATE: refusing to remove $t (pre-existing, a link, a mount or not the fixed path)"; esc=23; fi
      fi
    done
  fi
  if has begin-C1 && [ "$esc" -eq 0 ]; then
    # The package set and the holds are an ATTENDED boundary: R compares and reports, it never removes, purges, downgrades, autoremoves, holds or unholds anything.
    route3_apt_idle || { echo "ESCALATE: an apt or dpkg run may be active; the package state cannot be compared now"; esc=24; }
    if [ "$esc" -eq 0 ]; then
      route3_pkgs > "$E/now.dpkg" && apt-mark showhold | LC_ALL=C sort > "$E/now.holds" || { echo "ESCALATE: the package or hold set cannot be read"; esc=24; }
    fi
    if [ "$esc" -eq 0 ]; then
      pkg_lost=$(LC_ALL=C comm -23 "$E/prestate.dpkg" "$E/now.dpkg"); pkg_added=$(LC_ALL=C comm -13 "$E/prestate.dpkg" "$E/now.dpkg")
      hold_lost=$(LC_ALL=C comm -23 "$E/prestate.holds" "$E/now.holds"); hold_added=$(LC_ALL=C comm -13 "$E/prestate.holds" "$E/now.holds")
      if [ -n "$pkg_lost$pkg_added$hold_lost$hold_added" ]; then
        echo "ESCALATE: ATTENDED RECOVERY REQUIRED. The package or hold state differs from the state recorded before this operation. R changed NO package and NO hold and keeps all evidence"
        echo "(held.new beforeC1.dpkg afterC1.dpkg now.dpkg now.holds prestate.dpkg prestate.holds in $E)."
        [ -z "$pkg_added" ] || { echo "installed since the recorded state (name<TAB>version):"; printf '%s\n' "$pkg_added"; }
        [ -z "$pkg_lost" ] || { echo "missing or changed since the recorded state (name<TAB>version):"; printf '%s\n' "$pkg_lost"; }
        [ -z "$hold_added" ] || { echo "held since the recorded state:"; printf '%s\n' "$hold_added"; }
        [ -z "$hold_lost" ] || { echo "no longer held since the recorded state:"; printf '%s\n' "$hold_lost"; }
        echo "Later objects of S1 (tmpfiles fragment, account, deployment tree) were undone above where their own controls allowed. Whether and how to remove any package is Peter's decision from this evidence."
        esc=28
      else echo "No package or hold recovery is required: the package set and the holds equal the recorded state."; fi
    fi
  fi
  if [ "$esc" -eq 0 ]; then
    while IFS= read -r line; do
      case $line in "absent "*) p=${line#absent }; case $p in "passwd "*|"group "*) continue;; esac
        if [ -e "$p" ] || [ -L "$p" ]; then echo "ESCALATE: still present: $p"; esc=25; fi;; esac
    done < "$E/prestate.objects"
    for k in passwd group; do
      route3_id "$k" "$ROUTE3_ACCOUNT"; ks=$?
      case $ks in 2) ;; 0) echo "ESCALATE: $k $ROUTE3_ACCOUNT still exists"; esc=25;; *) echo "ESCALATE: the $k query failed (status $ks): absence is not established"; esc=27;; esac
    done
    apt-mark showhold | LC_ALL=C sort > "$E/now.holds" || { echo "ESCALATE: the hold list cannot be read"; esc=24; }
    cmp -s "$E/prestate.holds" "$E/now.holds" || { echo "ESCALATE: the hold list differs from the pre-state (see now.holds)"; esc=25; }
    route3_pkgs > "$E/now.dpkg" || { echo "ESCALATE: the package set cannot be read"; esc=24; }
    lost=$(LC_ALL=C comm -23 "$E/prestate.dpkg" "$E/now.dpkg"); added=$(LC_ALL=C comm -13 "$E/prestate.dpkg" "$E/now.dpkg")
    [ -z "$lost" ] || { echo "ESCALATE: a package of the pre-state is removed or changed:"; printf '%s\n' "$lost"; esc=25; }
    if [ -n "$added" ]; then
      echo "ESCALATE: the package set differs from the pre-state; these additions are PRESERVED (R never removes a package):"; printf '%s\n' "$added"
      [ "$esc" -ne 0 ] || esc=26
    fi
  fi
  exit "$esc"
); rc=$?; echo "[R rc=$rc]"; if [ "$rc" -eq 0 ]; then echo "Pre-state restored. Evidence kept in /root/route3-evidence."; elif [ "$rc" -eq 28 ]; then echo "ESCALATE to Peter: the pre-state is not restored (status 28: package or hold differences need ATTENDED recovery); make no further change"; else echo "ESCALATE to Peter: R stopped with status $rc (not a status-28 package/hold result); the pre-state is not confirmed restored; see the printed ESCALATE lines and the status table; make no further change"; fi; (exit "$rc")
```

### Checkpoint and rollback matrix (S1; S3 rows follow in P.6)

Failure of a step, or success followed by a decision to withdraw, takes the same route: run **R**. `begin-Cn` is written before a step and `done-Cn` after it.

| Checkpoint | Created by | Rollback action (in R, reverse order) | Expected status | Verification | Escalate when | Reboot |
|---|---|---|---|---|---|---|
| C0 evidence | S1.0 (staged in `route3-evidence.new`, published by one rename) | published: **kept** (disposal is Peter's separate decision, P.6). Unpublished (S1.0 failed or was killed at any point before the rename): **R0** removes only the literal stage, after proving it holds no later marker and no later-stage object | R0: 0 | R refuses without a verified published pre-state (status 20); R0 refuses when `/root/route3-evidence` exists (31) | R0: stage not a real root-0700 directory (32), unexpected entry (33), later marker (34), later-stage object or unanswerable identity query (35) | none |
| C1 packages | S1.1 (`apt-mark hold` of the pinned set after the trusted gate; **no install**) | **none: packages and holds are an attended boundary.** R compares the current set with `prestate.dpkg` / `prestate.holds`: equal = no recovery needed; any difference = no package or hold is changed, the differences are printed, all evidence is kept (no remove, purge, autoremove, downgrade, hold or unhold) | 0 only when equal; **28** when any package or hold difference remains (attended recovery, Peter decides) | `now.dpkg` equals `prestate.dpkg` and `now.holds` equals `prestate.holds` | an apt/dpkg run is active (24), the package or hold set cannot be read (24), a pre-state package is gone or changed (25), a non-recorded addition remains after an equal C1 comparison (26), the manager or identity cannot be queried (27), **any package or hold difference at C1 (28)** | none |
| C2 deployment | S1.2 (staging dir, then `/opt/freedom-route3`) | remove the fixed stage path and the fixed base path only if both were absent in the pre-state, are real directories, not links and not mounts | 0 | both paths absent | a path pre-existed, is a link or a mount, or the supervisor fragment exists | none |
| C3 account | S1.3 (`useradd --create-home`) | `userdel --remove`, `groupdel`, remove the fixed home — only if account, group and home were all absent before and no linger / user manager exists | 0 | `getent` status **2** for passwd and group (status 0 = exists; any other status = query failed) ; home absent | any of them pre-existed; linger or `user@<uid>` present (S3 begun: R3 first); **a failed identity/manager query (27)** — never read as absence | none |
| C4 tmpfiles | S1.4 | reviewed tool `remove` (removes only a byte- and metadata-identical fragment) | 0 | fragment absent | tool absent while the fragment exists, or a shadowing file (the tool reports it) | none; an empty `/run/polkit-1/rules.d` created by a boot in between is harmless and gone at the next boot |
| unexpected reboot after S1.4 | operator | none needed: no unit exists; the boot creates only the empty runtime directories | n/a | S2.1 still `rc=0`; `polkit_tmpfiles verify` may now return 0 | S2.1 fails | the event itself |
| interrupted block | any | the `begin-` marker already written selects the undo; the stage path left behind is removed by C2; an interrupted S1.1 changes no package or hold in R: any package or hold difference is status 28 with all evidence kept, an equal state continues | 0 | as above | as above | none |

### S3 — arming and install (a SEPARATE authorization; nothing in S0–S2 authorizes it)

S3 creates the privileged route's parts in the order *linger → SA-2 artifact → sudoers (last)* and installs the unit. **`install` enables the unit**: after S3.5 the supervisor is enabled but not
started, and a boot would start it. The interval from S3.5 to S4 (or to R3) therefore forbids a reboot. If S3 is authorized, S4 should follow in the same window; otherwise run R3.

```bash
# S3.1 — AUTHORITY: Peter's separate written S3 authorization (arming + install). Creates the account's lingering user manager. Needs S2 passed and one boot after S1.4 (tmpfiles verify must be ok).
( umask 022; export PATH="$ROUTE3_PATH"; cd / || exit 1
  route3_fields_ok && route3_tree_ok && route3_gate || exit 1
  grep -qx done-C4 "$ROUTE3_EVID/checkpoints" || { echo "NO-GO: S1 has not completed"; exit 2; }
  /usr/bin/env -i PATH=/usr/bin:/bin "$ROUTE3_PY" -I -S -c "$ROUTE3_ENTRY" "$ROUTE3_TMPFILES" verify || { echo "NO-GO: tmpfiles verify is not ok (the first boot after S1.4 has not happened?)"; exit 2; }
  uid=$(id -u "$ROUTE3_ACCOUNT") || exit 2
  route3_cp begin-C5 || exit 2
  loginctl enable-linger "$ROUTE3_ACCOUNT" || exit 3
  for i in $(seq 1 30); do [ "$(route3_unit "user@$uid.service")" = active ] && break; sleep 1; done
  [ "$(route3_unit "user@$uid.service")" = active ] && [ -e /var/lib/systemd/linger/freedom-executor ] || { echo "NO-GO: the user manager did not start"; exit 4; }
  route3_cp done-C5 || exit 5
); rc=$?; echo "[S3.1 rc=$rc]"; [ "$rc" -eq 0 ] || echo "STOP: run block R3; do not retry in place"; (exit "$rc")
```

```bash
# S3.2 — AUTHORITY: Peter's separate written S3 authorization. Builds the SA-2 artifact from the verified deployed code and the pinned wheel into /usr/local/libexec/freedom-blades-rp11 (new, root-owned).
# Identity: SHA-256 of `find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum` run inside the artifact directory must equal ROUTE3_SA2_TREE_SHA256.
( umask 022; set -o pipefail; export PATH="$ROUTE3_PATH"; cd / || exit 1; DEST=/usr/local/libexec/freedom-blades-rp11; W="$ROUTE3_ART/$ROUTE3_RELEASE_REV/wheelhouse/$ROUTE3_WHEEL"
  route3_fields_ok && route3_tree_ok && route3_gate || exit 1
  grep -qx done-C5 "$ROUTE3_EVID/checkpoints" || { echo "NO-GO: S3.1 has not completed"; exit 2; }
  sha256sum --check --status <(printf '%s  %s\n' "$ROUTE3_WHEEL_SHA256" "$W") || { echo "NO-GO: the wheel differs from the pin"; exit 2; }
  [ "$(stat -c %u "/usr/local/libexec")" = 0 ] && [ $(( 0$(stat -c %a /usr/local/libexec) & 022 )) -eq 0 ] && [ ! -e "$DEST" ] && [ ! -L "$DEST" ] || { echo "NO-GO: parent untrusted or destination exists"; exit 2; }
  route3_cp begin-C6 || exit 2
  /usr/bin/env -i PATH=/usr/bin:/bin "$ROUTE3_PY" -I -S -B "$ROUTE3_BASE/code/infra/rp11-h1/build.py" --wheel "$W" --dest "$DEST" || exit 3
  [ -z "$(find "$DEST" \( ! -user root -o -perm /022 -o -type l \) -print)" ] || { echo "NO-GO: artifact ownership, mode or link"; exit 4; }
  d=$(cd "$DEST" && find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum | sha256sum | cut -d' ' -f1)
  [ "$d" = "$ROUTE3_SA2_TREE_SHA256" ] || { echo "NO-GO: the SA-2 tree differs from ROUTE3_SA2_TREE_SHA256"; exit 5; }
  route3_cp done-C6 || exit 6
); rc=$?; echo "[S3.2 rc=$rc]"; [ "$rc" -eq 0 ] || echo "STOP: run block R3; do not retry in place"; (exit "$rc")
```

```bash
# S3.3 — AUTHORITY: Peter's separate written S3 authorization. Creates the one-command sudoers drop-in LAST, under a dot-name sudo ignores until it is validated and renamed. Have a second root session open.
( umask 077; export PATH="$ROUTE3_PATH"; cd / || exit 1; F=/etc/sudoers.d/freedom-executor-sa2; N=/etc/sudoers.d/.freedom-executor-sa2.new
  grep -qx done-C6 "$ROUTE3_EVID/checkpoints" || { echo "NO-GO: S3.2 has not completed"; exit 2; }
  route3_gate || { echo "NO-GO: the trusted baseline attestation failed; no sudoers file was written"; exit 2; }
  [ ! -e "$F" ] && [ ! -L "$F" ] && [ ! -e "$N" ] && [ ! -L "$N" ] || { echo "NO-GO: a sudoers file already exists"; exit 2; }
  route3_cp begin-C7 || exit 2
  printf '%s\n' 'freedom-executor ALL=(root) NOPASSWD: /usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py stop' > "$N" || exit 3
  chmod 0440 -- "$N" && visudo -cf "$N" || exit 4
  mv --no-target-directory --no-clobber -- "$N" "$F" || exit 5
  visudo -c || exit 6
  route3_cp done-C7 || exit 7
); rc=$?; echo "[S3.3 rc=$rc]"; [ "$rc" -eq 0 ] || echo "STOP: run block R3; do not retry in place"; (exit "$rc")
```

```bash
# S3.4 — AUTHORITY: Peter's separate written S3 authorization (read-only). Installer verify before the first install: expect 12 (not-installed). Any other status is a STOP.
( export PATH="$ROUTE3_PATH"; cd / || exit 1
  grep -qx done-C7 "$ROUTE3_EVID/checkpoints" || { echo "NO-GO: S3.3 has not completed"; exit 2; }
  route3_installer verify; v=$?; echo "installer verify status $v"
  [ "$v" -eq 12 ] || exit 3
); rc=$?; echo "[S3.4 rc=$rc]"; [ "$rc" -eq 0 ] || echo "STOP: a status other than 12 (see the refusal word above and the status table in §5); run block R3"; (exit "$rc")
```

```bash
# S3.5 — AUTHORITY: Peter's separate written S3 authorization. Runs installer INSTALL, which writes the fragment and ENABLES the unit in the system manager. It does not start it.
( export PATH="$ROUTE3_PATH"; cd / || exit 1
  grep -qx done-C7 "$ROUTE3_EVID/checkpoints" || { echo "NO-GO: S3.3 has not completed"; exit 2; }
  route3_gate || { echo "NO-GO: the trusted baseline attestation failed; the unit was not installed"; exit 2; }
  route3_cp begin-C8 || exit 2
  route3_installer install; v=$?; echo "installer install status $v"
  [ "$v" -eq 0 ] || exit "$v"
  route3_cp done-C8 || exit 5
); rc=$?; echo "[S3.5 rc=$rc]"
if [ "$rc" -eq 0 ]; then echo "STOP-B: the unit is ENABLED and NOT started. A reboot would start it: do not reboot. Go to S4 under its own authority, or run R3 now."
elif [ "$rc" -eq 15 ]; then echo "STOP: recovery-incomplete (15): do not repeat; follow section 8b and escalate to Peter"
else echo "STOP: run block R3; do not retry in place"; fi; (exit "$rc")
```

Installer status table (preserved exactly by `route3_installer`): `0` ok · `2` usage · `10` prerequisite refused · `11` conflict/shadowed · `12` verify failed (`not-installed`, `not-enabled`,
`manager-stale`) · `13` I/O · `14` `remove` refused · `15` `recovery-incomplete` · `20`/`30` the trust walk before any installer code ran (`20`: tmpfiles entry; `30`: stage entry). The entry
adds no statuses of its own to the installer's, passes `sys.exit` through unchanged, and nothing follows it in a pipeline.

### S4 — activation (NOT authorized by this plan; its own decision, attending operator and window)

```bash
# S4.1 — AUTHORITY: Peter's separate written ACTIVATION decision (attending operator, window, escalation contact). NOT authorized by anything in this plan.
# Activation is the most consequential mutation of the plan, so it reruns the full trusted attestation itself (fields, deployed tree, route3_gate: artifacts, interpreter, baseline record, signed-archive payload reference) BEFORE
# `systemctl start`: any drift is NO-GO with nothing started, whether or not S2.1 or S3.x ran earlier or recently.
( export PATH="$ROUTE3_PATH"; cd / || exit 1
  grep -qx done-C8 "$ROUTE3_EVID/checkpoints" || { echo "NO-GO: S3.5 has not completed"; exit 2; }
  route3_fields_ok && route3_tree_ok && route3_gate || { echo "NO-GO: the trusted baseline attestation failed; the supervisor was not started"; exit 2; }
  systemctl start freedom-blades-executor-supervisor.service || exit 3
  route3_installer verify-ready; v=$?; echo "installer verify-ready status $v"
  exit "$v"
); rc=$?; echo "[S4.1 rc=$rc]"; [ "$rc" -eq 0 ] || echo "STOP: do not run any probe; follow section 8b or section 8 removal"; (exit "$rc")
```

Acceptance probes are §6; removal after activation is §8, with `route3_installer remove` as the only installer invocation.

### R3 — rollback of S3, and the difference from removal after activation

R3 undoes S3 in reverse order and returns the host to STOP-A; run **R** afterwards to go further back. It is **not** `installer remove` alone: `remove` undoes only the installed unit, so it is a rollback only for a failure that happened
after S3.5 began; a failure before it (linger, SA-2, sudoers) has no installed unit to remove. Removal after *activation* (S4) is §8 and needs the drain protocol; R3 is only for an unstarted supervisor and
refuses when the unit is running. Never delete ownership records by hand and never continue after an unknown or `recovery-incomplete` state.

```bash
# R3 — AUTHORITY: Peter's separate S3 authorization, or the operator's duty to restore STOP-A. Idempotent. Status 0 only when the S3 objects are gone and STOP-A is re-established.
( umask 022; export PATH="$ROUTE3_PATH"; cd / || exit 1; esc=0; DEST=/usr/local/libexec/freedom-blades-rp11; F=/etc/sudoers.d/freedom-executor-sa2; N=/etc/sudoers.d/.freedom-executor-sa2.new
  route3_evid_ok || { echo "ESCALATE: no verified recorded pre-state"; exit 20; }
  has() { grep -qx -- "$1" "$ROUTE3_EVID/checkpoints"; }
  pre() { grep -qxF -- "absent $1" "$ROUTE3_EVID/prestate.objects"; }
  sv=$(route3_unit freedom-blades-executor-supervisor.service)
  case $sv in
    active|activating|reloading|deactivating) echo "ESCALATE: the supervisor is running; this is a removal after activation (section 8)"; exit 21;;
    inactive|failed) ;;
    *) echo "ESCALATE: the supervisor state cannot be established (the manager does not answer): nothing was changed"; exit 27;;
  esac
  if has begin-C8; then
    route3_installer remove; v=$?; echo "installer remove status $v"
    [ "$v" -eq 0 ] || { echo "ESCALATE: installer remove status $v (section 8b for 15)"; esc=22; }
  fi
  if has begin-C7 && [ "$esc" -eq 0 ]; then
    for t in "$F" "$N"; do
      if [ -e "$t" ] || [ -L "$t" ]; then
        if pre "$t" && [ -f "$t" ] && [ ! -L "$t" ]; then rm -- "$t" || esc=23; else echo "ESCALATE: refusing to remove $t"; esc=23; fi
      fi
    done
    [ "$esc" -ne 0 ] || visudo -c >/dev/null || { echo "ESCALATE: visudo -c fails after removal"; esc=23; }
  fi
  if has begin-C6 && [ "$esc" -eq 0 ] && { [ -e "$DEST" ] || [ -L "$DEST" ]; }; then
    if pre "$DEST" && [ "$DEST" = /usr/local/libexec/freedom-blades-rp11 ] && [ -d "$DEST" ] && [ ! -L "$DEST" ] && ! mountpoint -q -- "$DEST"; then rm -r --one-file-system -- "$DEST" || esc=24
    else echo "ESCALATE: refusing to remove $DEST"; esc=24; fi
  fi
  uid=
  if [ "$esc" -eq 0 ]; then
    route3_id passwd "$ROUTE3_ACCOUNT"; ps=$?
    case $ps in
      0) uid=$(getent passwd "$ROUTE3_ACCOUNT" | cut -d: -f3); [ -n "$uid" ] || { echo "ESCALATE: the account cannot be read"; esc=27; };;
      2) ;;
      *) echo "ESCALATE: the account query failed (status $ps): the user manager cannot be assessed"; esc=27;;
    esac
  fi
  if has begin-C5 && [ "$esc" -eq 0 ]; then
    if [ -n "$uid" ] && [ -e /var/lib/systemd/linger/freedom-executor ]; then
      pre /var/lib/systemd/linger/freedom-executor || { echo "ESCALATE: linger pre-existed"; esc=25; }
      [ "$esc" -ne 0 ] || loginctl disable-linger "$ROUTE3_ACCOUNT" || esc=25
      for i in $(seq 1 60); do [ "$(route3_unit "user@$uid.service")" = inactive ] && break; sleep 1; done
      [ "$(route3_unit "user@$uid.service")" = inactive ] || { echo "ESCALATE: the user manager is still running or cannot be queried"; esc=25; }
    fi
  fi
  if [ "$esc" -eq 0 ]; then
    for p in "$F" "$N" "$DEST" /var/lib/systemd/linger/freedom-executor /etc/systemd/system/freedom-blades-executor-supervisor.service /etc/systemd/system/multi-user.target.wants/freedom-blades-executor-supervisor.service; do
      if [ -e "$p" ] || [ -L "$p" ]; then echo "ESCALATE: still present: $p"; esc=26; fi
    done
    [ "$(route3_loadstate freedom-blades-executor-supervisor.service)" = not-found ] || { echo "ESCALATE: the manager does not report the supervisor unit as not-found"; esc=27; }
    [ -z "$uid" ] || [ "$(route3_unit "user@$uid.service")" = inactive ] || { echo "ESCALATE: the account's user manager is not inactive"; esc=27; }
  fi
  exit "$esc"
); rc=$?; echo "[R3 rc=$rc]"; [ "$rc" -eq 0 ] && echo "STOP-A re-established. Run S2.1, or block R to remove S1." || echo "ESCALATE to Peter: make no further change"; (exit "$rc")
```

### P.6 S3 rows of the rollback matrix, the boot rule, and evidence disposal

| Checkpoint | Created by | Rollback action | Expected status | Verification | Escalate when | Reboot |
|---|---|---|---|---|---|---|
| C5 linger | S3.1 | `loginctl disable-linger`; wait until `user@<uid>.service` is `inactive` | 0 | linger file absent, manager inactive, supervisor `LoadState=not-found` | linger pre-existed; manager still running after 60 s; **the manager or the account cannot be queried (27)** — R3 never reports STOP-A on an unanswered query | none |
| C6 SA-2 artifact | S3.2 | remove the fixed destination only if absent in the pre-state, a real directory, not a link or mount | 0 | destination absent | pre-existed, link or mount | none |
| C7 sudoers | S3.3 | remove the drop-in and its dot-named temporary only if absent in the pre-state; `visudo -c` afterwards | 0 | both absent, `visudo -c` ok | pre-existed; `visudo -c` fails (keep the second root session) | none |
| C8 install | S3.5 | `installer remove` (supervisor never started: no drain needed) | 0 | fragment, wants link absent; manager `LoadState=not-found` | status 14 or 15 (section 8b); never edit records by hand | **forbidden** between S3.5 and R3/S4 while the unit is enabled |
| partial first `install` | S3.5 | R3 starts with `remove`; a root-owned fragment left by a failed first install is removed by it or completed by a rerun only under the section 8b procedure | 0 | as C8 | `recovery-incomplete` (15) | forbidden until resolved |
| `recovery-incomplete` | S3.5 / R3 | none by this plan: section 8b | 15 | n/a | always: stop and escalate | forbidden |
| unexpected reboot while enabled | operator | the unit starts and fails closed (not ready until the user manager answers); run section 8 removal, not R3 | n/a | `verify-ready` / unit state | any invocation record exists | the event itself |
| runtime/state dirs, invocation records | the running supervisor (S4) | **never** deleted by this plan; `remove` leaves the empty directories (section 8) | n/a | n/a | any record | n/a |
| evidence | S1.0, S1.2 | published evidence is kept until Peter accepts the rollback result; then disposal below (never the routine recovery of an incomplete S1.0 — that is R0) | 0 | directory absent | n/a | none |

Evidence disposal (a separate decision of Peter's, after reading the evidence; not part of R or R3):

```bash
# P.6 — AUTHORITY: Peter's explicit disposal decision. Removes only the fixed evidence directory.
( [ "$ROUTE3_EVID" = /root/route3-evidence ] && [ -d "$ROUTE3_EVID" ] && [ ! -L "$ROUTE3_EVID" ] && [ "$(stat -c %u "$ROUTE3_EVID")" = 0 ] && rm -r --one-file-system -- "$ROUTE3_EVID" ); rc=$?; echo "[P.6 rc=$rc]"; (exit "$rc")
```

The unresolved fields in block F are the only reason this plan is not executable today. **The returned candidate is NO-GO by construction** until Peter (or the supplier named per field) fills them from a committed,
independently reviewed release.

## 0. Fixed facts (nothing here is configurable)

| Item | Value |
|---|---|
| Account | `freedom-executor` (non-root, non-login shell, owned home, lingering, primary group `freedom-executor`) |
| Unit (installed by the tool) | `/etc/systemd/system/freedom-blades-executor-supervisor.service`, root-owned `0644`, `User=freedom-executor`, `Group=freedom-executor`, enabled in the **system** manager only (`multi-user.target.wants`), not started by install |
| Interpreter flags | `/opt/freedom-route3/venv/bin/python -E -s -m adapters.executor.supervisor`: `-E` ignores `PYTHONPATH`, `PYTHONHOME`, `PYTHONUSERBASE` and every other `PYTHON*` variable, and `-s` drops the account's user site; its configured environment is only `PATH=/usr/bin:/bin` (systemd may add service metadata) |
| Code root | `/opt/freedom-route3/code` (`adapters/`, `application/` trees imported by the service) |
| Interpreter and dependencies | `/opt/freedom-route3/venv` (`bin/python`, `pyvenv.cfg`, `site-packages`, the pinned `jeepney` tree); trust rules in §4 |
| Only privileged vector | `sudo -n /usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py stop` |
| Socket | `/run/freedom-blades-executor/supervisor.sock` (`RuntimeDirectory=`, owned by the account, `0700`) |
| State | `/var/lib/freedom-blades-executor` (`StateDirectory=`, owned by the account, `0700`); one fixed record, `invocations/active.json` |
| Invocations | one transient `freedom-executor-stop-<nonce>.service` per admitted stop, created by the supervisor through the account's **user** manager (`/run/user/<uid>/bus`), never in the system manager |
| Member environment | minimized to `PATH=/usr/bin:/bin`: the supervisor snapshots manager variables and unsets them plus known systemd-generated names. This is defense in depth and an observed test condition, not an atomic authorization invariant |

The privileged invariant is independent of exact environment equality. The transient service can execute only the fixed
SA-2 argv above; sudoers permits only that argv; Python starts with `-I -S`; and the root-owned artifact selects `stop`
from argv before reading anything and clears the environment. A same-UID process could change the user manager's
environment between the supervisor's snapshot and `StartTransientUnit`, so deployment and review must never treat the
observed PATH-only environment as the control that makes the root transition safe.

**Trusted sudo-policy prerequisite (not mechanically verifiable by the installer).** The installer proves the command list
(`sudo -l -U`), not the rest of the host's sudo policy. The environment-independence claim holds only on a host whose
sudoers keeps sudo's default environment sanitizing for this account: no `!env_reset`, no `env_keep`/`env_check` entry that
passes `LD_*`, `PYTHON*` or `PATH`, no `SETENV` tag, no `Defaults:freedom-executor` override and no `secure_path` weakening. A
production review must confirm that by reading the effective sudoers files themselves (the `sudo-rs` on Ubuntu 26.04 does
not print a `Defaults` section in `sudo -l`); where it cannot be confirmed the vector must not be activated. The R6 handback
records a one-off disposable-host probe of the real `sudo` (hostile `PYTHON*`, `LD_*`, `BASH_ENV` and `PATH` values reach
nothing; only `HOME` and sudo's own `PATH` do); it is evidence about that host, not an installer check.

**Request-write ownership and readiness.** The executor client treats any error raised by the request write as
`HANDED_OFF` (the whole line may already be admitted, so a retry could launch SA-2 twice); only failures before the write
is attempted are `NOT_SENT`. The supervisor publishes `READY=1` only after readiness, the first recovery pass, the socket
bind/listen and the start of its serving worker; a client arriving at that instant queues in the listen backlog and is served.
If the serving worker ever stops, the service exits non-zero so systemd restarts a viable owner.

Installer exit codes: `0` ok, `2` usage, `10` prerequisite refused, `11` conflict/shadowed, `12` verify failed,
`13` I/O (a manager command that times out or cannot run is also `13` `io-error` once the earlier state is verified; `state-unavailable` and `enablement-unavailable` are `13` too: an upgrade is refused, before anything changes, when the unit's state or its `wants` link cannot be observed strictly, see below), `14` `remove` refused (`invocation-pending`, `drain-unconfirmed`, `drain-lost`), `15` `recovery-incomplete` (an
`install` upgrade or a `remove` failed **and** putting the earlier fragment/owner back could not be completed and verified: see §8b).
Diagnostics are fixed words.
Enablement is observed strictly wherever an upgrade could change anything: only a genuinely absent
`multi-user.target.wants/freedom-blades-executor-supervisor.service` means "disabled", only the expected symlink means "enabled", and an
I/O or permission error, a non-link object, a malformed link or an unexpected target is `enablement-unavailable` (13, nothing changed) before the
upgrade or `recovery-incomplete` (15) after it: inspect `ls -l` of that path as root, correct it, and rerun `install`.
The installer finds `systemctl`, `runuser` and `sudo` only in `/usr/sbin:/usr/bin:/sbin:/bin` and runs them with that
`PATH` (the caller's `PATH` is never consulted). It uses the system manager to enable, disable, reload, stop and inspect the
persistent supervisor; it talks to the account's user manager (through `runuser`) only to list transient invocation units.

## 1. Preconditions

1. Run as root on the target host, under the written authority of the stage being run (P.1). Have a second root session open before touching sudoers (S3.3).
2. Every identity in block F is set (S0.1 returns 0). The SA-2 artifact is built by S3.2 from the verified deployment and the pinned wheel; `/usr/bin/python3.14` comes from the pinned Ubuntu packages of S1.1. There is
   no other procedure. Without the artifact the client ends `NOT_CONFIRMED`; that is the safe outcome but means no stop is ever confirmed.
3. The release revision to deploy has passed independent review and is committed; the deployment is the manifest-exact tree of S1.2, never a copy of a mutable checkout. No secret or credential file is read or copied by any step here.

## 2. Account and lingering (S1.3 creates the account; S3.1 enables linger)

The account is created by block **S1.3** (`useradd --system --create-home --home-dir /home/freedom-executor --shell /usr/sbin/nologin freedom-executor`, no linger) and lingering by block **S3.1**
(`loginctl enable-linger freedom-executor`, creating `/var/lib/systemd/linger/freedom-executor`); neither is run by hand.

`--system` is acceptable if the host's UID policy allows a user manager for system UIDs; if `user@<uid>.service` will
not start for it, create the account as a regular non-login user instead (the tool only checks non-root, non-login
shell, owned home, and a primary group named `freedom-executor` whose gid is the account's own: the unit's `Group=`). The account must have no password and no SSH keys. Do not add it to any group that grants write
access to the code tree, `sudo`, `wheel` or `docker`.

Check: `getent passwd freedom-executor` (shell `nologin`/`false`), `getent group freedom-executor` (same gid),
`ls /var/lib/systemd/linger/freedom-executor`.

## 3. Sudoers (S3.3, once, exactly one command, created last)

Block **S3.3** creates `/etc/sudoers.d/freedom-executor-sa2` (mode `0440`, root:root) containing exactly:

```
freedom-executor ALL=(root) NOPASSWD: /usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py stop
```

Validate before relying on it: `visudo -cf /etc/sudoers.d/freedom-executor-sa2`. Then
`sudo -l -U freedom-executor` must list **one** command line, equal to the vector above, whose run-as is `root` (printed
`(root)`, or `(root : root)`) and whose only tag is `NOPASSWD`. Anything else makes the installer refuse
(`sudoers-not-exact`): extra commands, wildcards, `ALL`, a second drop-in granting more, a stale drop-in, **any wider
run-as** (`(ALL)`, `(ALL : ALL)`, `(root : ALL)`, another user or group, a list, `#uid`, `%group`), or an additional
tag (`SETENV`, `NOEXEC`, `LOG_OUTPUT`, `PASSWD` …). Do not widen this entry to make a test pass. The run-as and tag check
applies to the printed grant; the `Defaults` section, which `sudo -l` does not print under `sudo-rs`, is still the production
review's to read (§9 and the readiness checklist).

## 4. Root-owned runtime

The service imports code from a tree the account must not be able to modify. `install`, `verify` and `verify-ready`
**enforce** the following and refuse (exit `10`) at the first violation; nothing below is a reminder only.

Every directory and file traversed must be owned by root (never by the account), must not be writable by group or
others, and must be a directory or regular file (a symlink only where stated):

1. **Path chain.** `/` and every directory down to `/opt/freedom-route3/code`, and down to
   `/opt/freedom-route3/venv`. A symlink in these chains is allowed only if it is root-owned and its
   complete target chain passes the same checks (absolute targets are read within the filesystem root; a target that
   escapes upward, a loop, or more than 16 links is refused).
2. **Imported code.** The whole `adapters/` and `application/` trees, walked by descriptor without following anything.
   **Any symlink anywhere in either tree is refused** (`code-symlink`); a socket, FIFO or device is refused
   (`code-untrusted`). Every enumeration is bounded **while it iterates**: one shared budget of 20,000 entries (and depth 32)
   covers the trees, the interpreter's `lib/python3*` siblings, the venv `lib` directory and `site-packages`; each directory
   iterator is drawn one entry at a time against that budget, so the entry that overflows it is the last one ever read and
   nothing is gathered, sorted or sampled beyond it. A tree beyond the bound is refused with `code-too-large`.
3. **Interpreter.** `venv/pyvenv.cfg` (regular file, no link, at most 8 KiB, with an absolute `home =`),
   `venv/bin/python` with its **complete link chain and every target**, the `home` directory and its sibling
   `lib/python3*` directories (the directories themselves, not their contents).
4. **Dependencies.** Exactly one `venv/lib/python3.*`; its `site-packages` directory and every top-level entry in
   it (these include the `.pth` files that run at interpreter start; links are refused); and the **whole `jeepney`
   tree** (required to exist; links refused). Other installed packages are not imported by the service and are not
   walked, but their top-level entries are still checked as above.
5. **The service fragment and its manager locations.** `infra/executor/freedom-blades-executor-supervisor.service` in the repository being
   installed: link-free path from `/`, regular file, link count 1, root-owned, not writable by group or others. It is
   read to its exact `fstat` size; a short read, early EOF or growth refuses (`source-invalid`). The installed copy is
   written with every short write completed; a write that makes no progress fails the install (`install-failed`)
   before the destination is linked, leaving nothing behind. No other system-manager location may hold or modify a unit of that
   name (`/usr/lib`, `/usr/local/lib`, `/run`, `*.control`, any `.d`/`.wants`/`.requires`): `shadowed`. A leftover
   user-service candidate (§9a) is refused as `legacy-user-service`.

Provisioning that satisfies this is block **S1.2** (and S1.1 for the interpreter packages), which consumes only the controlled artifact set of P.3: a digest-verified archive and wheel
copied into a root-only staging directory on the same filesystem, a manifest-exact code tree, a venv holding only the pinned `jeepney` installed with `--no-index --no-deps --require-hashes`,
one verified `rename(2)` publication, and a final verification (`route3_stage tree`) that checks exactly the properties above plus the manifest. No recursive `chown`/`chmod` is used. The package host proof
(`tests/systemd_integration/test_executor_package_host.py`) bind-mounts a root-owned copy of the repository (`code`) and a root-owned python3.14 venv with `jeepney` (`venv`) over `/opt/freedom-route3` for the
module and unmounts them afterwards. Because `/opt/freedom-route3` is separate from the ordinary checkout and venv, no live path is renamed, re-owned or replaced, and `freedom-bot`
and `freedom-worker` are neither edited nor restarted. S1.2 extracts with `umask 022` and `--no-same-permissions`, so the deployment never carries a setgid bit (the installer would accept one, since it has no group write).

### S2.2 Post-provision tmpfiles check (read-only; not an installation step)

After S1.4, the Polkit `tmpfiles.d` prerequisite is verified with the **reviewed copy inside the deployment**, never the ordinary checkout; it is the same entry (`ROUTE3_ENTRY`, block D) as production
checklist item 8 (handback §6). It is a fixed interpreter, an empty environment and isolated mode (`-I -S`: no `PYTHONPATH`, `PYTHONHOME`, user site or working directory), loading the tool by its absolute path.
**Before any deployment Python is evaluated**, the entry itself walks `/` through the tool, and `infra/tmpfiles.d/` through the source fragment the tool reads
beside itself, with `lstat` (no symlink followed): every directory must be a real directory and the tool and fragment real regular files, all owned by
uid 0 and not writable by group or others. Any missing, wrong-type, symlinked, non-root-owned or writable component prints one fixed finding and exits
20 with nothing evaluated; there is no fallback to `/opt/freedom-blades/platform`. Because every parent is root-owned and not writable by non-root, an
unprivileged actor cannot swap the validated files before they are opened (a concurrent root attacker is out of scope). `polkit_tmpfiles` exits 0 only
when `verify: ok`; any other status is a failed prerequisite, except that **12 is the expected status at STOP-A until the next boot** (P.2). The block prints `[rc=N]` and **returns the same `N`**
(a subshell, so pasting it does not end your shell).

```bash
# S2.2 — AUTHORITY: same as S1 (read-only). Needs block D.
( /usr/bin/env -i PATH=/usr/bin:/bin "$ROUTE3_PY" -I -S -c "$ROUTE3_ENTRY" "$ROUTE3_TMPFILES" verify; rc=$?; echo "[rc=$rc]"; exit "$rc" )
```

## 5. Install, verify, start

Installation is stage **S3** and activation is stage **S4** (P.1); the sequence is S3.4 (`route3_installer verify`, expect `not-installed` 12), S3.5 (`route3_installer install`, expect `installed` 0; enables, does not start) and
S4.1 (`systemctl start`, then `route3_installer verify-ready`, expect `ready` 0). `route3_installer` (block D) is the **only** way the installer is invoked: absolute `/usr/bin/python3.14`, empty environment, `-I -S -B`,
the verified code root only; hostile `PATH`, `PYTHONPATH`, `PYTHONHOME`, user site and working directory cannot redirect it, and its exit status is the installer's own.

`install` writes the fragment root-owned `0644` in `/etc/systemd/system`, enables it in the **system** manager
(`systemctl enable`, never `--global`, never `--user`), runs `systemctl daemon-reload` and then asks the manager what it
loaded: the unit must be `LoadState=loaded` from exactly that fragment with `NeedDaemonReload=no`, or the install fails
and must have empty `DropInPaths`, `User=freedom-executor`, `Group=freedom-executor` and configured
`Environment=PATH=/usr/bin:/bin`, or the install fails (`reload-failed`; `verify` reports `manager-stale`). The filesystem
check independently refuses a same-named fragment or name-specific or dash-prefix (`freedom-blades-.service.d`) drop-in in every supported system-unit load path,
including `.control`, transient, attached and generator locations. A failed upgrade restores the previous fragment **and
verifies the restoration** (bytes on disk, loaded by the manager with no drop-in, **enablement in both directions** — a unit that was
disabled is disabled again, one that was enabled is enabled again, the link is checked — and unit state unchanged); this holds for every
failure after the fragment may have changed, including a manager command that times out, cannot run or raises an OS error, not only a
non-zero exit. If that cannot be
confirmed the result is `recovery-incomplete` (15), never a restored one (§8b). A
failed first install leaves a root-owned fragment that a rerun completes. After a reboot the system manager starts the enabled unit by itself, with no login; it retries every second
(`StartLimitIntervalSec=0`) and stays not-ready, refusing every stop, until the account's lingering user manager and its bus
answer, the first recovery pass completes, the socket is bound and the serving thread has started. Only then does the
supervisor publish `READY=1`. The manual `start` is needed only for the first activation without a reboot.

`verify` reports `not-installed` (12) whenever the installed fragment is not byte-identical to the repository fragment:
absent, an older recognized fragment awaiting `install`, or a modified one. It does not mean the file is missing.

Refusals map to fixed words: `account-missing|unsuitable|home`, `linger-off`, `sudoers-not-exact|unreadable`,
`code-writable|missing|symlink|untrusted|too-large`, `source-untrusted|invalid|missing`, `unit-dir`, `shadowed`,
`legacy-user-service`, `owner-without-fragment`, `destination-conflict`, `install-failed`, `enable-failed`, `reload-failed`, `state-unavailable`, `enablement-unavailable`, `recovery-incomplete`; `verify` adds
`not-installed`, `not-enabled`, `manager-stale`; `verify-ready` adds `manager-not-running`, `supervisor-not-ready` (not active, no
socket, or the supervisor's process is not the account's), `state-untrusted`. Fix the named prerequisite; never edit the
tool's checks.

Confirm after start: `systemctl show -p User,Group,Environment,MainPID,FragmentPath,DropInPaths,NeedDaemonReload freedom-blades-executor-supervisor.service`;
`journalctl -u freedom-blades-executor-supervisor.service` shows the supervisor ready; `ls -ld /var/lib/freedom-blades-executor
/run/freedom-blades-executor` show the account and `0700`; exactly one process runs `python -E -s -m adapters.executor.supervisor`,
as the account; `loginctl list-sessions` need not show any session for the account.

## 6. Acceptance probes (stage S4 only: once, in a maintenance window, not during a live SA-2)

1. `sudo -u freedom-executor sudo -n /bin/true` must be refused.
2. The sudo log for the account shows only the fixed vector when the executor client exercises a stop.
3. Reboot test: leave the supervisor stopped with no records, reboot, confirm the unit is `active` without any login
   and `verify-ready` returns `ready`; `systemctl show -p ActiveEnterTimestampMonotonic` of the supervisor is later than that of
   `user@<uid>.service`.
4. No other user's manager has the unit: `systemctl --user -M <other>@ show freedom-blades-executor-supervisor.service -pLoadState`
   is `not-found`, and `find /etc/systemd/user /home -name 'freedom-blades-executor-supervisor*'` finds nothing.
5. A unit of the same name created under `~freedom-executor/.config/systemd/user` is a separate unit in the account's own
   manager; it cannot change the system supervisor's fragment, command, PID or restarts (the host proof does exactly this).
6. Exercise one stop while observing the transient member. A PATH-only `/proc/<pid>/environ` is the expected regression
   observation, but is not an authorization proof: repeat safety review against the fixed sudoers/SA-2 argv, Python
   `-I -S`, and the root-owned `stop` artifact's no-environment-read path.

## 7. Upgrade

1. Review and deploy the new revision as in §4.
2. `route3_installer verify` (still `installed`/trusted).
3. `route3_installer install`. If the unit in the repository changed, the installer
   replaces the installed fragment **atomically**, but only a root-owned `0644` regular file that carries the installer's
   `# Managed-By: tools.executor_supervisor_install` line (anything else is `destination-conflict` and is never touched), runs the
   checked `daemon-reload` and proves the manager loaded the new fragment; if it cannot, the previous fragment is put back
   and the install fails with `reload-failed`; if the previous fragment cannot be put back and confirmed, the install exits
   `recovery-incomplete` (15) and §8b applies. The running supervisor keeps its old configuration until restarted.
4. Restart: `systemctl restart freedom-blades-executor-supervisor.service`. Restart does not touch a populated invocation
   unit (it lives in the account's user manager); the recovery loop re-adopts the record. Re-run `verify-ready`.

## 8. Rollback and removal

* Rollback of code: redeploy the previous reviewed revision (§4), run `install` (which upgrades a recognized older
  fragment) and restart the supervisor.
* `route3_installer remove` does **not** infer safety from its own directory and
  `list-units` snapshots. It sends the running supervisor a root-only maintenance **drain** request over the
  supervisor socket (the socket must be owned by the account; the supervisor authenticates the maintenance peer as uid 0). The
  supervisor takes its own admission lock, closes admission **for the rest of its life**, and acknowledges only if it
  holds no ownership record, finds no damaged entry, has no adopter running and the user manager lists no
  `freedom-executor-stop-*` unit. The installer holds that connection open, re-checks the state directory and the unit
  list itself while admission is closed, confirms the connection is still alive, then stops the system service (judged by
  the manager's own `ActiveState`, not an exit code), re-checks that nothing appeared across the stop, disables the unit,
  unlinks only a fragment it recognizes, runs the checked `daemon-reload` and proves the manager no longer holds the unit
  (`LoadState=not-found`). A second `remove` after success is a no-op that succeeds. If no supervisor is listening, removal
  proceeds only when the unit is `inactive` and the state directory is empty (nothing can then be admitting); a unit that is
  starting, restarting or in an unknown state is refused (`drain-unconfirmed`; with the user manager down the unit keeps
  restarting by design: `systemctl stop` it yourself, then `remove`).
* **A running supervisor whose fragment is absent is refused (`11 owner-without-fragment`) before anything is drained, stopped
  or reloaded.** The manager can still hold and run a loaded copy after the fragment and enablement are gone; that copy would
  not survive a reboot, so removing it could lose the only owner. The same word covers a unit that is not `inactive`, or a
  supervisor that still answers on the socket while the manager says `inactive`. Operator response: run `install` (it writes the
  fragment, enables it and reloads, and leaves the running supervisor alone), then `remove` as usual. With the fragment and the
  loaded unit both genuinely absent, `remove` is still an idempotent no-op that succeeds. If an owner somehow appears after that
  check and removal then fails, the result is always `recovery-incomplete` (15): a drained or stopped supervisor with no
  fragment cannot be given a persistent owner by the tool.
* **Quiesce the executor before `remove`.** Every refusal restarts the supervisor, which drops the connection of any request
  in flight (the client then reports `HANDED_OFF`; the invocation is still owned and settled once). The production-readiness
  load rehearsal (three clients re-admitting back to back) was refused six times in a row (`invocation-pending`) with 35 SA-2
  launches for 35 admitted requests (30 answered, 5 `HANDED_OFF`); `remove` succeeded at once when the clients stopped.
* Fail-closed refusals and failures, each leaving a **persistent owner when the restoration can be completed and is
  verified**: the fragment present (restored from the identical bytes if it had already been unlinked), enabled, loaded by
  the manager, and the supervisor **restarted** and reported running (a drained supervisor refuses every stop until
  restarted). The installer checks each of those after the restoration; when any of them cannot be established the result is
  `15 recovery-incomplete` instead of the original word (also when the restoration itself raises or times out), and §8b is the operator's response: `14 invocation-pending` (a record, unit or in-flight invocation);
  `14 drain-unconfirmed` (no or malformed answer, wrong peer, lost reply, unreadable manager state, a starting
  supervisor); `14 drain-lost` (the connection dropped between acknowledgment and stop, i.e. the supervisor
  restarted); `13 stop-failed`, `disable-failed`, `remove-failed`, `reload-failed` (including the reload after the unlink). A
  restarted supervisor re-adopts any record, so retrying later is safe. Do not delete records by hand: an ambiguous
  same-boot `start-sent` record (the `StartTransientUnit` call may be queued) blocks until reboot by design, and removal
  stays refused while it exists.
* `remove` leaves the (empty) `/var/lib/freedom-blades-executor` and `/run/freedom-blades-executor` directories that systemd keeps; deleting state is a separate administrator decision.
* `remove` never touches the account, lingering or sudoers. Revoking those is a separate administrator action
  (delete the sudoers drop-in first, then `loginctl disable-linger`, then **wait until `systemctl is-active user@<uid>.service`
  reports `inactive`** — it stays `deactivating` for several seconds and `userdel` refuses while the manager's process
  runs — then `userdel -r`) and should follow a successful `remove`. A refused `remove` must be resolved first.

## 8b. `recovery-incomplete` (exit 15): operator response

`recovery-incomplete` means an `install` upgrade or a `remove` failed and the attempt to put the earlier fragment and owner
back **did not complete or could not be confirmed**. It replaces the original failure word; it never means "restored". It
does not mean an invocation was abandoned: the tool reaches the point of changing anything only after the drain and the
installer's own emptiness checks, never deletes state, and `remove` stays refused (`invocation-pending`) while a record exists.
The installer never overwrites a foreign object at the fragment path and never loosens a trust check to finish.

1. Do not repeat the command blindly and do not delete anything under `/var/lib/freedom-blades-executor`.
2. Establish the state as root, read-only first:
   `ls -l /etc/systemd/system/freedom-blades-executor-supervisor.service /etc/systemd/system/multi-user.target.wants/freedom-blades-executor-supervisor.service`;
   `systemctl show freedom-blades-executor-supervisor.service -pLoadState,FragmentPath,DropInPaths,NeedDaemonReload,ActiveState,MainPID,UnitFileState`;
   `ls -l /var/lib/freedom-blades-executor/invocations`; `journalctl -u freedom-blades-executor-supervisor.service -n 50`.
3. Resolve the named cause (full filesystem, a manager command that times out, a manager that does not reload, a foreign file or drop-in at the fragment path,
   or a higher-precedence unit of the same name such as one in `/etc/systemd/system.control`). A foreign object is the
   administrator's to inspect; the tool will not touch it. The unit may be left **stopped**: after a failed removal the
   installer restarts the supervisor only when it could verify what the manager loaded, and it does not start a unit whose
   loaded configuration it could not verify. If a failed attempt left the `multi-user.target.wants` link pointing at the
   foreign unit (rehearsed: `systemctl enable` links to the fragment the manager actually loaded), `install` reports
   `enable-failed` after the override is gone: run `systemctl disable freedom-blades-executor-supervisor.service` first to drop
   the dangling link, then `install`.
4. Then converge with the tool: after a failed **upgrade**, run `install` again (a fragment already new only needs enabling and
   the checked reload; an old one is upgraded again; if the unit had been disabled and the restoration could not disable it, `systemctl disable` it first if that is the intended state) and `systemctl restart` if the unit is not running; after a failed
   **removal**, run `install` to put the fragment back and enable it, `systemctl reset-failed` and `systemctl start` the unit, run
   `verify-ready`, and only then retry `remove` in a quiet window (§8). If the executor was idle and the fragment is simply gone,
   the supervisor may be running from the manager's loaded copy only: it will not survive a reboot until `install` has
   been run again (`remove` refuses that state with `owner-without-fragment` until then).
5. Do not activate or resume the executor until `verify-ready` says `ready`.

## 8a. Migrating from the preceding user-service candidate (`legacy-user-service`)

The earlier candidate installed the same unit name as a *user* unit in `/etc/systemd/user`, globally enabled. It was never
accepted or deployed, so the installer does not migrate it: it refuses (`legacy-user-service`, exit 11) while any of
`/etc/systemd/user/freedom-blades-executor-supervisor.service{,.d,.wants}` or
`/etc/systemd/user/default.target.wants/freedom-blades-executor-supervisor.service` exists, and the system unit itself
carries `ConditionPathExists=!/etc/systemd/user/freedom-blades-executor-supervisor.service` so it will not start beside one.
If a host ever had it, clean up as root, in this order, and only with no invocation pending:

```
systemctl --user -M freedom-executor@ stop freedom-blades-executor-supervisor.service     # for every user manager that ran it
systemctl --global disable freedom-blades-executor-supervisor.service
rm /etc/systemd/user/freedom-blades-executor-supervisor.service
systemctl daemon-reload
# then remove any ~/.local/state/freedom-blades-executor and /run/user/<uid>/freedom-blades-executor it left, after
# checking they hold no invocations/active.json record; only then run `install`.
```

Never run both supervisors: each has its own ownership store, so two would be two owners of one boundary.

## 9. Known limits (carry into the review)

* The account can create a unit of the same name under its own `~/.config/systemd/user`. That is a separate unit in its
  own user manager: it has no effect on the root-owned system supervisor (its fragment, command, PID or restarts), which no
  user manager can load, reload, enable or stop. There is no residual shadowing risk to accept, and the installer no
  longer performs or relies on any point-in-time shadow scan of the account's directories.
* The supervisor runs as the dedicated account, so the account can signal its own process (it is the
  same uid; as with the earlier user-service design): code integrity of the running supervisor rests on the root-owned code tree, `-E -s`, and `NoNewPrivileges`, not
  on process isolation from the account. The sudoers entry bounds the privileged impact to the single fixed vector.
* Member-environment minimization is deliberately not an atomic guarantee. The manager-environment read and
  `StartTransientUnit` are separate D-Bus operations, and systemd may add new generated variables. Security therefore
  rests on the exact sudo vector and the root-owned `stop` artifact's `-I -S`, no-environment-read behavior; a PATH-only
  `/proc/<pid>/environ` observation is regression evidence, not an authorization proof.
* An ambiguous same-boot `start-sent` record (the process crashed after committing it and before or during the
  `StartTransientUnit` call, with the unit still absent) is never cleared on elapsed time; it blocks admission and
  removal until reboot, or until the deterministic unit appears and is adopted. This availability loss is an accepted,
  fail-closed consequence for this slice. A `prepared` record clears on affirmative unit absence; a changed boot
  identity clears any record. The boot-id rule is proven by unit test, and the earlier host reboot proof cannot
  distinguish it from the absent-unit/cgroup rule.
* The drain acknowledgment is valid only while its connection is held; a supervisor that restarts between the
  acknowledgment and the stop is detected by the dropped connection (and, after the stop, by the re-check), not
  prevented. The re-check closes the remaining window by restarting the owner when anything appeared.
* Trust is verified by path at install/verify time; ownership and mode are not re-checked while the service runs, so
  the root-owned, non-writable property depends on the deployment keeping it.
* One unrelated attest-host test (`test_default_action_termination_leaves_no_false_record_and_is_recovered_explicitly`)
  is a timing flake with no baseline comparison yet.
* Production interpreter/dependency provisioning (§4), the SA-2 artifact installation and any polkit policy on the host are outside this tool (the account must hold none that lets it control system units; the host proof confirms a default Ubuntu host denies it).
