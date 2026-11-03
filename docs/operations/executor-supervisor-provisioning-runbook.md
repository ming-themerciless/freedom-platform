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
| **S0** | S0.0 proposes the apt closure (solver simulation); S0.1 fields are all set; S0.2 read-only host preflight | S0.0 and S0.2 read only; S0.1 no | Peter's authorization of a read-only production preflight | `[S0.* rc=0]` or **NO-GO** |
| **S1** | **Inert** prerequisites: evidence/pre-state (staged, then published by one rename), the reviewed Python package closure, the verified deployment `/opt/freedom-route3/{code,venv}`, the dormant `freedom-executor` account (no linger), the `tmpfiles.d` fragment | yes | Peter's written **provisioning** authorization | **STOP-A** (below) |
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
group/other-writable) and S0.2/S1.2 refuse anything whose SHA-256 differs from the field. The workspace is **uncommitted**, so no release revision exists yet: the first four fields below
are **hard blockers** that return NO-GO until the supplier fills them. Nothing here is promoted from an `oracle-test` observation into a production decision.

| Artifact | Identity | State |
|---|---|---|
| Reviewed release | `ROUTE3_RELEASE_REV` (40-hex commit id of the independently reviewed, committed candidate) | **BLOCKER — supplier: Peter** (commit and publication are his) |
| Deployable code | `code.tar` = `git archive --format=tar <REV> -- adapters application tools infra/executor infra/tmpfiles.d infra/rp11-h1` built on the maintainer workstation (never on production), plus `MANIFEST.sha256` (`<sha256>␣␣<path>` per file, sorted, LF). `ROUTE3_ARCHIVE_SHA256`, `ROUTE3_MANIFEST_SHA256` | **BLOCKER — supplier: Peter / maintainer workstation**, after the commit. The manifest, not the tar, is the content identity: the tree must equal it exactly (set and digests). Includes the service fragment and every repository file executed as root or by the executor |
| Python 3.14 | **The complete closure** of Ubuntu archive packages the solver installs for `python3.14`, `python3.14-minimal` (owns `/usr/bin/python3.14`) and `python3.14-venv`, each **exact `name=version`**: `ROUTE3_APT_PACKAGES`. Accepted archive sources: `ROUTE3_APT_ORIGIN`, a comma-separated list of `<url> <suite>/<component>` entries, exactly as `apt-cache madison` prints them. Interpreter identity: `ROUTE3_PY_SHA256` (see "Reference identity" below) | **BLOCKER — supplier: Peter**, from S0.0 (read-only solver simulation on the production host's own configured source; no third-party repository, no `deadsnakes`, no build from source). `oracle-test` observation only, not a production value: Ubuntu 26.04.1 `resolute`, `python3.14-minimal 3.14.4-1ubuntu0.2` (`amd64v3`), offered by `resolute-updates` and `resolute-security` |
| Jeepney wheel | `jeepney-0.9.0-py3-none-any.whl`, SHA-256 `97e5714520c16fc0a45695e5365a2e11b81ea79bba796e26f9f1d178cb182683` (the accepted pin, `infra/rp11-h1/requirements.lock`; the same wheel builds SA-2 and the venv) | **fixed**. Custody: obtained once, off production, by `pip download --no-deps --only-binary=:all: --require-hashes -r infra/rp11-h1/requirements.lock` and delivered to `<ART>/<REV>/wheelhouse/`. Installed only with `--no-index --no-deps --require-hashes` (S1.2) |
| SA-2 artifact | built **from the deployed, verified code and the same wheel** by `infra/rp11-h1/build.py` into `/usr/local/libexec/freedom-blades-rp11` (root-owned, directories `0755`, files `0644`); identity `ROUTE3_SA2_TREE_SHA256` = SHA-256 of the sorted `sha256␣␣path` listing of that tree (S3.2 computes it) | **BLOCKER — supplier: Peter**, from a reference build of the release revision on a non-production host; built only in S3 |
| `tmpfiles.d` prerequisite | `infra/tmpfiles.d/freedom-blades-rp11-polkit-rules.conf` from the manifest, installed by the reviewed tool to `/usr/lib/tmpfiles.d/` root-owned `0644`; S2.1 compares it byte-for-byte with the manifest copy | covered by the manifest |
| Service fragment | `infra/executor/freedom-blades-executor-supervisor.service`, from the manifest; placed only by installer `install` in S3 | covered by the manifest |

Release-record recipe (maintainer workstation, after the commit; **not** a production step and not part of any block here): `git archive --format=tar --output=code.tar <REV> -- adapters application tools infra/executor infra/tmpfiles.d infra/rp11-h1`;
extract it into an empty directory and run `find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum | sed 's#  ./#  #' > MANIFEST.sha256` inside it; `sha256sum code.tar MANIFEST.sha256` are the two fields. S1.2 refuses an archive that is not exactly that
manifest (no other file, no link, no directory-only surprise), so a mutable checkout, a stray cache or an extra file cannot ride along. The SA-2 identity is computed on a non-production host by building the release as S3.2 does and hashing the listing defined there.

**Apt closure — how it is obtained, bound and checked.** (1) *Obtain:* S0.0 runs `apt-get --simulate --no-install-recommends install python3.14 python3.14-minimal python3.14-venv` on the production host against its own already-downloaded
package lists and prints every `Inst` result as `name=version`, plus each version's archive sources from `apt-cache madison`. Nothing is installed and no list is refreshed. Any proposed upgrade, downgrade or removal is "NOT ACCEPTABLE" (S0.0 fails): the plan installs
only packages that are new to the host, so a rollback never has to undo a change to an existing one. (2) *Review:* Peter reviews the printed set and sources and enters it as `ROUTE3_APT_PACKAGES` and `ROUTE3_APT_ORIGIN`. (3) *Bind:* `route3_apt_origin_ok` accepts a member
only if every configured source that offers exactly that `name=version` is a listed origin, and at least one does; a listed origin line for a different version, or an unlisted source for the same version, fails. (4) *Check before installing (S0.2 and again S1.1):* the solver,
asked to install exactly the members not yet installed (pinned `=version`), must propose exactly those members at exactly those versions — a missing dependency, an additional one, another version, an upgrade, a downgrade or a removal each fail before anything is installed. A member
installed at another version fails. (5) *Verify after (S1.1, S2.1, S3):* every member at its exact version, `dpkg --verify` over every member, the real interpreter's SHA-256, and — S1.1 only — nothing was removed or changed and nothing outside the recorded intent was added (exit 4).

**Reference identity for `ROUTE3_PY_SHA256`** (the file does not exist on production before S1.1, so S0.2 cannot hash it). The reference is the `/usr/bin/python3.14` member of the **`python3.14-minimal` package file itself**, obtained off production: on a non-production host with the same
Ubuntu archive configuration, in an empty directory as an unprivileged user, `apt-get download python3.14-minimal=<ROUTE3 version>`; confirm the downloaded `.deb`'s SHA-256 equals the `SHA256:` that `apt-cache show python3.14-minimal=<version>` prints for that exact version (the archive's signed
index); then `dpkg-deb --fsys-tarfile python3.14-minimal_*.deb | tar -xO ./usr/bin/python3.14 | sha256sum`. That digest is the field. S1.1 proves the installed file equals it (exit 4 → rollback otherwise); nothing in S0 claims to hash a production file. On `oracle-test` this
procedure was run and its digest equals the digest of the installed `/usr/bin/python3.14` (R2 return); the value is an observation of that host and is not promoted to a production field.

Drift: `apt-mark hold` freezes the pinned packages from S1.1 on. At every later stage S2.1/S3.x re-check version, `dpkg --verify` and the SHA-256 of the real interpreter; **any difference is NO-GO**: stop,
do not upgrade in place, return to Peter for a re-reviewed set of fields. The `/usr/bin/python3.14` path is the one the accepted contract names (sudoers vector, `-I -S` entries); no other interpreter is substituted.

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
  for v in ROUTE3_ARCHIVE_SHA256 ROUTE3_MANIFEST_SHA256 ROUTE3_PY_SHA256 ROUTE3_SA2_TREE_SHA256 ROUTE3_WHEEL_SHA256; do
    [[ ${!v} =~ $re ]] || { echo "NO-GO: $v is unset or not a SHA-256 (supplier: Peter)"; bad=1; }
  done
  # the apt field is the COMPLETE reviewed closure: every package the solver will install, each exact name=version, no name twice
  re='^[a-z0-9][a-z0-9.+-]*=[A-Za-z0-9.+~:-]+( [a-z0-9][a-z0-9.+-]*=[A-Za-z0-9.+~:-]+)*$'
  pk=" $ROUTE3_APT_PACKAGES "
  if [[ $ROUTE3_APT_PACKAGES =~ $re && $pk == *" python3.14="* && $pk == *" python3.14-minimal="* && $pk == *" python3.14-venv="* ]] && [ -z "$(route3_tokens | cut -d= -f1 | LC_ALL=C sort | uniq -d)" ]; then :; else
    echo "NO-GO: ROUTE3_APT_PACKAGES must be the complete closure: exact name=version for python3.14, python3.14-minimal, python3.14-venv and every other package the solver installs, no name twice (supplier: Peter)"; bad=1; fi
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
# stdin: apt-get --simulate output. stdout: "new name=version" | "change name old>new" | "remove name" | "malformed ..." (Conf, headings and the rest are ignored)
route3_apt_parse() {
  awk '
    $1 == "Inst" { name = $2; old = ""
      if ($3 ~ /^\[/) { old = $3; sub(/^\[/, "", old); sub(/\]$/, "", old) }
      i = index($0, "("); if (i == 0) { print "malformed " $0; next }
      split(substr($0, i + 1), a, " ")
      if (old != "") print "change " name " " old ">" a[1]; else print "new " name "=" a[1]
      next }
    $1 == "Remv" || $1 == "Purg" { print "remove " $2 }'
}
# read-only solver result for the given arguments; sets ROUTE3_SIM
route3_apt_sim() {
  local out rc
  out=$(/usr/bin/env -i PATH="$ROUTE3_PATH" LC_ALL=C apt-get --simulate --no-install-recommends install -- "$@" 2>&1); rc=$?
  [ "$rc" -eq 0 ] || { echo "NO-GO: the apt-get simulation failed (status $rc)"; return 1; }
  ROUTE3_SIM=$(printf '%s\n' "$out" | route3_apt_parse)
}
# EVERY archive source that offers exactly name=version must be a listed origin, and at least one must offer it. apt-cache madison prints "name | version | url suite/component arch Packages".
route3_apt_origin_ok() {
  local n=$1 v=$2 out a b c src seen=0 bad=0 o hit allowed
  out=$(LC_ALL=C apt-cache madison "$n") || { echo "NO-GO: apt-cache madison $n failed"; return 1; }
  IFS=, read -ra allowed <<< "$ROUTE3_APT_ORIGIN"
  while IFS='|' read -r a b c; do
    a=${a//[[:space:]]/}; b=${b//[[:space:]]/}
    [ "$a" = "$n" ] && [ "$b" = "$v" ] || continue
    c=${c#"${c%%[![:space:]]*}"}; c=${c%"${c##*[![:space:]]}"}; src=${c% Packages}; src=${src% *}; seen=1; hit=0
    for o in "${allowed[@]}"; do o=${o#"${o%%[![:space:]]*}"}; o=${o%"${o##*[![:space:]]}"}; [ "$src" = "$o" ] && hit=1; done
    [ "$hit" -eq 1 ] || { echo "NO-GO: $n=$v is also offered by an origin that is not listed: $src"; bad=1; }
  done <<< "$out"
  [ "$seen" -eq 1 ] || { echo "NO-GO: $n=$v is offered by no configured archive source"; bad=1; }
  return "$bad"
}
# The reviewed closure against the host, read-only. Sets ROUTE3_TODO (the members not yet installed, one name=version per line, sorted) only when ALL of these hold:
# every member is offered by a listed origin only; no member is installed at another version; the solver, asked to install exactly the missing members, proposes exactly those
# members at exactly those versions and nothing else (no extra package, no upgrade, no downgrade, no removal).
route3_apt_check() {
  local t n v inst bad=0 got other
  ROUTE3_TODO=
  for t in $ROUTE3_APT_PACKAGES; do
    n=${t%%=*}; v=${t#*=}
    route3_apt_origin_ok "$n" "$v" || bad=1
    inst=$(dpkg-query -W -f='${Version}' "$n" 2>/dev/null)
    if [ -z "$inst" ]; then ROUTE3_TODO+="$t"$'\n'
    elif [ "$inst" != "$v" ]; then echo "NO-GO: $n is installed at $inst, not $v"; bad=1; fi
  done
  [ "$bad" -eq 0 ] || return 1
  ROUTE3_TODO=$(printf '%s' "$ROUTE3_TODO" | LC_ALL=C sort)
  [ -n "$ROUTE3_TODO" ] || return 0
  route3_apt_sim $ROUTE3_TODO || return 1
  other=$(printf '%s\n' "$ROUTE3_SIM" | awk '$1 != "new" && NF')
  [ -z "$other" ] || { echo "NO-GO: the solver proposes a change, removal or something unparsed:"; printf '%s\n' "$other"; return 1; }
  got=$(printf '%s\n' "$ROUTE3_SIM" | awk '$1 == "new" { print $2 }' | LC_ALL=C sort)
  [ "$got" = "$ROUTE3_TODO" ] || { echo "NO-GO: the solver result is not exactly the reviewed closure"; echo "solver would install:"; printf '%s\n' "$got"; echo "reviewed, not yet installed:"; printf '%s\n' "$ROUTE3_TODO"; return 1; }
}
# ---- apt DIAGNOSTIC evidence recorded INSIDE the Route 3 apt transaction (never ownership, never authority to remove or unhold) -------
# NO package or hold is ever removed, purged, downgraded or unheld by this plan after S1.1 has installed it. An idle check, a snapshot, a package delta, a PID, a timestamp, a lock observation or the records below cannot say
# WHICH action created a package effect: apt runs the configured DPkg::Post-Invoke list in order under the same frontend lock, so an EARLIER configured hook can run a separate dpkg operation before the Route 3 hook queries package state
# and the Route 3 hook would then observe that effect as if it were its own. The records are kept ONLY so that an attending operator can see the reviewed intent, what the invocation submitted and what dpkg reported afterwards.
# The one S1.1 apt-get carries TWO per-invocation hooks (-o on that command only; no global apt configuration is read or changed):
#  1. DPkg::Pre-Install-Pkgs runs after apt holds the dpkg frontend lock and BEFORE dpkg unpacks anything (protocol Version 3 on the descriptor named by InfoFD). It proves the lock is held by one of its own
#     ancestors, refuses anything but a plain new installation and durably writes /root/route3-evidence/apt.txn (write, fsync, rename, fsync): what this invocation SUBMITTED. That is a record of intent to
#     install. It is NOT proof that anything was installed.
#  2. DPkg::Post-Invoke runs after dpkg finished (also after a failed dpkg run, verified on the real apt) and BEFORE apt releases the frontend lock, in the same process tree. It proves that lock is held by one of its
#     own ancestors, reads apt.txn, asks dpkg for the state of exactly those packages and durably writes /root/route3-evidence/apt.effects (write, fsync, rename, fsync): the packages of apt.txn that dpkg reported as
#     installed at exactly the recorded version. This is an OBSERVATION of package state. It can include an effect produced by ANOTHER configured hook that ran earlier in the same list (a separate dpkg
#     operation of the same name and version), so it is NOT proof that this invocation's submitted action created the effect and it is NOT ownership.
# S1.1 uses the records only as FAIL-CLOSED success checks (a missing, malformed or contradictory record fails S1.1). R never reads them to decide a package or hold mutation: R mutates no package and no hold at all.
# apt.txn format (tab separated): line 1 "route3-apt-txn 1"; then one "pkg<TAB>name<TAB>version" line per package this invocation submits; last line "end<TAB>N" with N equal to the number of pkg lines.
# apt.effects format (tab separated, a diagnostic observation): line 1 "route3-apt-effects 1"; line 2 "txn<TAB>SHA-256 of apt.txn"; then one "eff<TAB>name<TAB>version" line per observed package; last line "end<TAB>N" with N equal to the number of eff lines.
route3_hook_text() {
  cat <<'HOOK'
#!/bin/sh
# Route 3 apt transaction record: DPkg::Pre-Install-Pkgs, protocol Version 3. Writes only below the evidence directory.
E=/root/route3-evidence
umask 077
set -C
PATH=/usr/bin:/bin; export PATH
fail() { echo "route3 apt hook: $1" >&2; exit "$2"; }
case ${APT_HOOK_INFO_FD:-} in ''|*[!0-9]*) fail "no protocol descriptor" 70;; esac
[ "$APT_HOOK_INFO_FD" -ge 3 ] || fail "unusable protocol descriptor" 70
[ -d "$E" ] && [ ! -L "$E" ] && [ "$(stat -c %u:%a -- "$E")" = 0:700 ] || fail "the evidence directory is not a root-0700 directory" 70
ino=$(stat -c %i -- /var/lib/dpkg/lock-frontend) || fail "no dpkg frontend lock file" 74
p=$$; held=
while [ "$p" -gt 1 ]; do
  if awk -v p="$p" -v i="$ino" '$4 == "WRITE" && $5 == p { n = split($6, a, ":"); if (a[n] == i) f = 1 } END { exit f ? 0 : 1 }' /proc/locks; then held=1; break; fi
  p=$(awk '{ sub(/^.*\) /, ""); print $2 }' /proc/"$p"/stat) || break
  case $p in ''|*[!0-9]*) break;; esac
done
[ -n "$held" ] || fail "no ancestor holds the dpkg frontend lock: this is not inside an apt transaction" 74
{ [ ! -e "$E/apt.txn" ] && [ ! -L "$E/apt.txn" ] && [ ! -e "$E/apt.txn.tmp" ] && [ ! -L "$E/apt.txn.tmp" ]; } || fail "a transaction record already exists" 71
eval "exec 9<&$APT_HOOK_INFO_FD" || fail "cannot read the protocol descriptor" 70
awk '
  BEGIN { print "route3-apt-txn 1" }
  NR == 1 { if ($0 != "VERSION 3") bad = "header"; next }
  st == 0 { if ($0 == "") st = 1; next }
  { if (NF != 9) { bad = "row"; next }
    if ($9 == "**CONFIGURE**") next
    if ($9 == "**REMOVE**" || $2 != "-" || $5 != "<" || $9 !~ /^\//) { bad = "effect"; next }
    if ($1 !~ /^[a-z0-9][a-z0-9.+-]*$/ || $6 !~ /^[A-Za-z0-9.+~:-]+$/) { bad = "name"; next }
    print "pkg\t" $1 "\t" $6; n++ }
  END { if (bad != "" || st != 1) { print "route3 apt hook: unsupported protocol (" bad ")" > "/dev/stderr"; exit 1 }; print "end\t" n + 0 }' <&9 > "$E/apt.txn.tmp" || { rm -f -- "$E/apt.txn.tmp"; fail "unsupported or malformed protocol: nothing recorded" 72; }
sync -- "$E/apt.txn.tmp" && mv --no-target-directory --no-clobber -- "$E/apt.txn.tmp" "$E/apt.txn" && sync -- "$E" || fail "the record could not be made durable" 73
HOOK
}
route3_effects_hook_text() {
  cat <<'HOOK'
#!/bin/sh
# Route 3 apt package-state observation (diagnostic only, not ownership): DPkg::Post-Invoke, inside the apt process tree that still holds the dpkg frontend lock. Writes only below the evidence directory.
E=/root/route3-evidence
DQ=/usr/bin/dpkg-query
umask 077
set -C
PATH=/usr/bin:/bin; export PATH
fail() { echo "route3 apt effects hook: $1" >&2; exit "$2"; }
[ -d "$E" ] && [ ! -L "$E" ] && [ "$(stat -c %u:%a -- "$E")" = 0:700 ] || fail "the evidence directory is not a root-0700 directory" 80
[ ! -e "$E/apt.txn" ] && [ ! -L "$E/apt.txn" ] && exit 0
{ [ -f "$E/apt.txn" ] && [ ! -L "$E/apt.txn" ] && [ "$(stat -c %u:%a -- "$E/apt.txn")" = 0:600 ]; } || fail "the transaction record is not a plain root-0600 file" 81
ino=$(stat -c %i -- /var/lib/dpkg/lock-frontend) || fail "no dpkg frontend lock file" 84
p=$$; held=
while [ "$p" -gt 1 ]; do
  if awk -v p="$p" -v i="$ino" '$4 == "WRITE" && $5 == p { n = split($6, a, ":"); if (a[n] == i) f = 1 } END { exit f ? 0 : 1 }' /proc/locks; then held=1; break; fi
  p=$(awk '{ sub(/^.*\) /, ""); print $2 }' /proc/"$p"/stat) || break
  case $p in ''|*[!0-9]*) break;; esac
done
[ -n "$held" ] || fail "no ancestor holds the dpkg frontend lock: this is not inside an apt transaction" 84
{ [ ! -e "$E/apt.effects" ] && [ ! -L "$E/apt.effects" ] && [ ! -e "$E/apt.effects.tmp" ] && [ ! -L "$E/apt.effects.tmp" ]; } || fail "an effect record already exists" 85
sum=$(sha256sum -- "$E/apt.txn" | cut -d' ' -f1); [ "${#sum}" -eq 64 ] || fail "the transaction record cannot be digested" 81
rows=$(awk -F'\t' '
  NR == 1 { if ($0 != "route3-apt-txn 1") bad = 1; next }
  $1 == "pkg" && NF == 3 && !seen && $2 ~ /^[a-z0-9][a-z0-9.+-]*$/ && $3 ~ /^[A-Za-z0-9.+~:-]+$/ { n++; print $2 "\t" $3; next }
  $1 == "end" && NF == 2 && !seen && $2 ~ /^[0-9]+$/ { seen = 1; want = $2; next }
  { bad = 1 }
  END { if (NR < 2 || bad || !seen || want + 0 != n + 0) exit 1 }' "$E/apt.txn") || fail "the transaction record is malformed" 81
T=$(printf '\t'); NL='
'
out=; n=0; IFS=$NL
for r in $rows; do
  name=${r%%"$T"*}; ver=${r#*"$T"}
  st=$("$DQ" -W -f='${db:Status-Abbrev}\t${Version}\n' -- "$name" 2>/dev/null); rc=$?
  [ "$rc" -ne 1 ] || continue
  [ "$rc" -eq 0 ] || fail "dpkg cannot be queried for $name" 86
  abbrev=${st%%"$T"*}; have=${st#*"$T"}
  case $abbrev in ?[HUFWti]*) [ "$have" = "$ver" ] || continue;; *) continue;; esac
  out="$out$name$T$ver$NL"; n=$((n + 1))
done
{ printf 'route3-apt-effects 1\ntxn\t%s\n' "$sum"; printf '%s' "$out" | awk -F'\t' 'NF == 2 { print "eff\t" $1 "\t" $2 }'; printf 'end\t%s\n' "$n"; } > "$E/apt.effects.tmp" || { rm -f -- "$E/apt.effects.tmp"; fail "the effect record could not be written" 87; }
sync -- "$E/apt.effects.tmp" || fail "the effect record could not be made durable" 88
mv --no-target-directory --no-clobber -- "$E/apt.effects.tmp" "$E/apt.effects" || fail "the effect record could not be published" 89
sync -- "$E" || fail "the effect record directory could not be made durable" 89
HOOK
}
# writes both hooks into the verified evidence directory (root 0700) before apt runs
route3_apt_hook_write() {
  route3_hook_text > "$ROUTE3_EVID/apt-hook.sh.tmp" && chmod 0700 -- "$ROUTE3_EVID/apt-hook.sh.tmp" && sync -- "$ROUTE3_EVID/apt-hook.sh.tmp" \
    && mv -- "$ROUTE3_EVID/apt-hook.sh.tmp" "$ROUTE3_EVID/apt-hook.sh" \
    && route3_effects_hook_text > "$ROUTE3_EVID/apt-effects-hook.sh.tmp" && chmod 0700 -- "$ROUTE3_EVID/apt-effects-hook.sh.tmp" && sync -- "$ROUTE3_EVID/apt-effects-hook.sh.tmp" \
    && mv -- "$ROUTE3_EVID/apt-effects-hook.sh.tmp" "$ROUTE3_EVID/apt-effects-hook.sh" && sync -- "$ROUTE3_EVID"
}
# the ONE S1.1 apt-get: $@ = the exact name=version members to install. Both hooks are configured with -o on this command only.
route3_apt_install() {
  local h="$ROUTE3_EVID/apt-hook.sh" e="$ROUTE3_EVID/apt-effects-hook.sh"
  /usr/bin/env -i PATH="$ROUTE3_PATH" DEBIAN_FRONTEND=noninteractive LC_ALL=C apt-get install --yes --no-install-recommends \
    -o "DPkg::Pre-Install-Pkgs::=$h" -o "DPkg::Tools::Options::$h::Version=3" -o "DPkg::Tools::Options::$h::InfoFD=3" -o "DPkg::Post-Invoke::=$e" -- "$@"
}
# $1 = the record. Sets ROUTE3_TXN (sorted "name<TAB>version" rows, one per line) and returns 0 ONLY for a complete, well-formed record that is consistent with the reviewed intent and the pre-install snapshot.
# A missing, truncated, malformed, duplicated, out-of-closure or contradictory record is an AMBIGUITY (status 1): ownership is never derived from the package delta instead.
route3_txn_rows() {
  local f=$1 r
  ROUTE3_TXN=
  { [ -f "$f" ] && [ ! -L "$f" ] && [ "$(stat -c %u:%a -- "$f")" = 0:600 ]; } || { echo "AMBIGUOUS: the transaction record is not a plain root-0600 file"; return 1; }
  r=$(awk -F'\t' '
    NR == 1 { if ($0 != "route3-apt-txn 1") bad = 1; next }
    $1 == "pkg" && NF == 3 && !seen && $2 ~ /^[a-z0-9][a-z0-9.+-]*$/ && $3 ~ /^[A-Za-z0-9.+~:-]+$/ { rows++; print $2 "\t" $3; next }
    $1 == "end" && NF == 2 && !seen && $2 ~ /^[0-9]+$/ { seen = 1; want = $2; next }
    { bad = 1 }
    END { if (NR < 2 || bad || !seen || want + 0 != rows + 0) exit 1 }' "$f") || { echo "AMBIGUOUS: the transaction record is malformed, truncated or inconsistent"; return 1; }
  r=$(printf '%s\n' "$r" | awk NF | LC_ALL=C sort)
  printf '%s\n' "$r" | awk -F'\t' 'NF && seen[$1]++ { d = 1 } END { exit d ? 1 : 0 }' || { echo "AMBIGUOUS: the transaction record names a package twice"; return 1; }
  [ -z "$(LC_ALL=C comm -13 "$ROUTE3_EVID/apt.intent" <(printf '%s\n' "$r" | awk NF))" ] || { echo "AMBIGUOUS: the transaction record names a package outside the reviewed intent"; return 1; }
  awk -F'\t' 'NR == FNR { b[$1]; next } ($1 in b) { bad = 1 } END { exit bad ? 1 : 0 }' "$ROUTE3_EVID/beforeC1.dpkg" <(printf '%s\n' "$r" | awk NF) \
    || { echo "AMBIGUOUS: the transaction record names a package that was already installed before the transaction"; return 1; }
  ROUTE3_TXN=$r
}
# $1 = the observation record. Needs ROUTE3_TXN (route3_txn_rows). Sets ROUTE3_EFF (sorted "name<TAB>version" rows) and returns 0 ONLY for a complete, well-formed record bound to THIS apt.txn (its SHA-256), whose every row is a
# row of the validated transaction record, is in the reviewed intent and was neither installed in the pre-install snapshot nor in the recorded pre-state. Anything else is an AMBIGUITY (status 1).
# A fail-closed S1.1 success check and a diagnostic: the rows are an OBSERVATION that may include an effect produced by another configured hook, never ownership.
route3_effects_rows() {
  local f=$1 r want
  ROUTE3_EFF=
  { [ -f "$f" ] && [ ! -L "$f" ] && [ "$(stat -c %u:%a -- "$f")" = 0:600 ]; } || { echo "AMBIGUOUS: the observation record is missing or not a plain root-0600 file"; return 1; }
  want=$(sha256sum -- "$ROUTE3_EVID/apt.txn" | cut -d' ' -f1)
  [ "${#want}" -eq 64 ] || { echo "AMBIGUOUS: the transaction record cannot be digested"; return 1; }
  r=$(awk -F'\t' -v want="$want" '
    NR == 1 { if ($0 != "route3-apt-effects 1") bad = 1; next }
    NR == 2 { if ($1 != "txn" || NF != 2 || $2 != want) bad = 1; next }
    $1 == "eff" && NF == 3 && !seen && $2 ~ /^[a-z0-9][a-z0-9.+-]*$/ && $3 ~ /^[A-Za-z0-9.+~:-]+$/ { rows++; print $2 "\t" $3; next }
    $1 == "end" && NF == 2 && !seen && $2 ~ /^[0-9]+$/ { seen = 1; n = $2; next }
    { bad = 1 }
    END { if (NR < 3 || bad || !seen || n + 0 != rows + 0) exit 1 }' "$f") || { echo "AMBIGUOUS: the observation record is malformed, truncated, inconsistent or bound to another transaction record"; return 1; }
  r=$(printf '%s\n' "$r" | awk NF | LC_ALL=C sort)
  printf '%s\n' "$r" | awk -F'\t' 'NF && seen[$1]++ { d = 1 } END { exit d ? 1 : 0 }' || { echo "AMBIGUOUS: the observation record names a package twice"; return 1; }
  [ -z "$(LC_ALL=C comm -13 <(printf '%s\n' "$ROUTE3_TXN" | awk NF) <(printf '%s\n' "$r" | awk NF))" ] || { echo "AMBIGUOUS: the observation record names a package the transaction record does not"; return 1; }
  [ -z "$(LC_ALL=C comm -13 "$ROUTE3_EVID/apt.intent" <(printf '%s\n' "$r" | awk NF))" ] || { echo "AMBIGUOUS: the observation record names a package outside the reviewed intent"; return 1; }
  awk -F'\t' 'NR == FNR { b[$1]; next } ($1 in b) { bad = 1 } END { exit bad ? 1 : 0 }' "$ROUTE3_EVID/beforeC1.dpkg" <(printf '%s\n' "$r" | awk NF) \
    && awk -F'\t' 'NR == FNR { b[$1]; next } ($1 in b) { bad = 1 } END { exit bad ? 1 : 0 }' "$ROUTE3_EVID/prestate.dpkg" <(printf '%s\n' "$r" | awk NF) \
    || { echo "AMBIGUOUS: the observation record names a package that was already installed before the transaction"; return 1; }
  ROUTE3_EFF=$r
}
# Sets ROUTE3_TXN (what this apt transaction SUBMITTED) and ROUTE3_EFF (what dpkg was OBSERVED to report afterwards). Used by S1.1 ONLY, as a fail-closed success check and to write the diagnostic observed.pkgs. R never calls it.
# Returns 0, or 1 = AMBIGUITY (S1.1 then fails):
#  * the reviewed intent is empty: no apt run happened, nothing was observed;
#  * a transaction record exists: it must be valid AND a valid observation record bound to it must exist;
#  * no transaction record: an observation record is a contradiction; and if an intent member appeared since the snapshot some action installed it and this one proved nothing: AMBIGUITY.
route3_observe_resolve() {
  local appeared
  ROUTE3_TXN=; ROUTE3_EFF=
  if [ ! -s "$ROUTE3_EVID/apt.intent" ]; then :
  elif [ -e "$ROUTE3_EVID/apt.txn" ] || [ -L "$ROUTE3_EVID/apt.txn" ]; then
    route3_txn_rows "$ROUTE3_EVID/apt.txn" || return 1
    route3_effects_rows "$ROUTE3_EVID/apt.effects" || return 1
  else
    { [ ! -e "$ROUTE3_EVID/apt.effects" ] && [ ! -L "$ROUTE3_EVID/apt.effects" ]; } || { echo "AMBIGUOUS: an observation record exists without a transaction record"; return 1; }
    appeared=$(LC_ALL=C comm -12 "$ROUTE3_EVID/apt.intent" <(LC_ALL=C comm -13 "$ROUTE3_EVID/beforeC1.dpkg" "$1"))
    [ -z "$appeared" ] || { echo "AMBIGUOUS: reviewed packages appeared but no transaction record exists:"; printf '%s\n' "$appeared"; return 1; }
  fi
  return 0
}
# $1 = snapshot before apt-get, $2 = snapshot after (apt returned 0). Nothing was removed or changed, nothing outside the recorded intent was added, and every package the record says this transaction installed is installed.
# A reviewed member that is installed but NOT in the record was installed by another action: it is reported only.
route3_delta_ok() {
  local gone extra lost other short
  gone=$(LC_ALL=C comm -23 "$1" "$2")
  short=$(LC_ALL=C comm -23 <(printf '%s\n' "$ROUTE3_TXN" | awk NF) <(printf '%s\n' "$ROUTE3_EFF" | awk NF))
  extra=$(LC_ALL=C comm -13 "$ROUTE3_EVID/apt.intent" <(LC_ALL=C comm -13 "$1" "$2"))
  lost=$(LC_ALL=C comm -23 <(printf '%s\n' "$ROUTE3_TXN" | awk NF) "$2")
  other=$(LC_ALL=C comm -23 <(LC_ALL=C comm -12 "$ROUTE3_EVID/apt.intent" <(LC_ALL=C comm -13 "$1" "$2")) <(printf '%s\n' "$ROUTE3_TXN" | awk NF))
  [ -z "$gone" ] || { echo "NO-GO: the install removed or changed an existing package:"; printf '%s\n' "$gone"; }
  [ -z "$extra" ] || { echo "NO-GO: the install added a package outside the reviewed closure:"; printf '%s\n' "$extra"; }
  [ -z "$lost" ] || { echo "NO-GO: a package the transaction record says was installed is not installed:"; printf '%s\n' "$lost"; }
  [ -z "$short" ] || { echo "NO-GO: apt returned 0 but the observation record does not cover a package the transaction submitted:"; printf '%s\n' "$short"; }
  [ -z "$other" ] || { echo "NOTE: installed by ANOTHER transaction before this one took its lock; reported only, and no rollback ever removes a package:"; printf '%s\n' "$other"; }
  [ -z "$gone" ] && [ -z "$extra" ] && [ -z "$lost" ] && [ -z "$short" ]
}
# $1 = snapshot after apt-get (any status): writes the DIAGNOSTIC observed.pkgs (the observed rows of apt.effects that dpkg reports at exactly the recorded version). Durable (write, fsync, rename, fsync) before S1.1 may succeed. NOT ownership; R never reads it.
route3_observed_write() {
  route3_observe_resolve "$1" || return 1
  LC_ALL=C comm -12 <(printf '%s\n' "$ROUTE3_EFF" | awk NF) "$1" > "$ROUTE3_EVID/observed.tmp" \
    && sync -- "$ROUTE3_EVID/observed.tmp" && mv -- "$ROUTE3_EVID/observed.tmp" "$ROUTE3_EVID/observed.pkgs" && sync -- "$ROUTE3_EVID"
}
# the pinned interpreter packages, unchanged since S1.1: every closure member at its exact version, no changed packaged file, and the real interpreter is the reviewed file
route3_python_ok() {
  local t n real h bad=0 out
  for t in $ROUTE3_APT_PACKAGES; do
    n=${t%%=*}
    [ "$(dpkg-query -W -f='${Version}' "$n" 2>/dev/null)" = "${t#*=}" ] || { echo "NO-GO: package $n is not at the pinned version"; bad=1; }
  done
  out=$(dpkg --verify $(for t in $ROUTE3_APT_PACKAGES; do printf '%s ' "${t%%=*}"; done)); [ $? -eq 0 ] && [ -z "$out" ] || { echo "NO-GO: dpkg --verify reports a changed packaged file"; bad=1; }
  real=$(readlink -f -- "$ROUTE3_PY"); read -r h _ < <(sha256sum -- "$real") ; [ "$h" = "$ROUTE3_PY_SHA256" ] || { echo "NO-GO: the real interpreter differs from ROUTE3_PY_SHA256"; bad=1; }
  return "$bad"
}
```

### F. Release fields — every `UNSET` is a hard NO-GO (the supplier edits this block in the reviewed release record, never on the host ad hoc)

```bash
ROUTE3_RELEASE_REV=UNSET
ROUTE3_ARCHIVE_SHA256=UNSET
ROUTE3_MANIFEST_SHA256=UNSET
ROUTE3_APT_PACKAGES="UNSET"
ROUTE3_APT_ORIGIN="UNSET"
ROUTE3_PY_SHA256=UNSET
ROUTE3_SA2_TREE_SHA256=UNSET
ROUTE3_WHEEL=jeepney-0.9.0-py3-none-any.whl
ROUTE3_WHEEL_SHA256=97e5714520c16fc0a45695e5365a2e11b81ea79bba796e26f9f1d178cb182683
```

### S0 — read-only production preflight

```bash
# S0.0 — AUTHORITY: Peter's authorization of a read-only production preflight. Reads only; writes nothing. Needs block D only (no field): it PROPOSES the closure and its sources so the supplier can review them.
# It is how the closure for ROUTE3_APT_PACKAGES is established without installing anything: the solver is run with --simulate against the host's own configured, already-downloaded package lists.
( export PATH="$ROUTE3_PATH"; bad=0
  route3_apt_sim python3.14 python3.14-minimal python3.14-venv || exit 1
  printf '%s\n' "$ROUTE3_SIM" | awk '$1 != "new" && NF { print "NOT ACCEPTABLE: " $0 }'
  echo "proposed ROUTE3_APT_PACKAGES (review every entry; add the top-level three if they are already installed):"
  printf '%s\n' "$ROUTE3_SIM" | awk '$1 == "new" { print "  " $2 }' | LC_ALL=C sort
  echo "archive sources offering each proposed version (apt-cache madison; ROUTE3_APT_ORIGIN lists the accepted <url> <suite>/<component> entries):"
  for t in $(printf '%s\n' "$ROUTE3_SIM" | awk '$1 == "new" { print $2 }'); do LC_ALL=C apt-cache madison "${t%%=*}" | awk -F'|' -v v="${t#*=}" '{ x = $2; gsub(/ /, "", x); if (x == v) print "  " $0 }'; done
  printf '%s\n' "$ROUTE3_SIM" | awk '$1 != "new" && NF { f = 1 } END { exit f ? 1 : 0 }' || bad=1
  exit "$bad"
); rc=$?; echo "[S0.0 rc=$rc]"; [ "$rc" -eq 0 ] || echo "STOP: the solver proposes a change or removal, or failed — nothing was changed; return to Peter"; (exit "$rc")
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

### S1 — inert provisioning (ends at STOP-A)

```bash
# S1.0 — AUTHORITY: Peter's written provisioning authorization (stage S1). Records the pre-state every rollback relies on, as ONE transaction: it builds /root/route3-evidence.new (root 0700) and publishes it as
# /root/route3-evidence by a single rename(2) only after every file is written and synced. Nothing but evidence is created. A status other than 0 leaves either nothing published (run block R0) or a complete published pre-state (run block R).
( set -o pipefail; umask 077; export PATH="$ROUTE3_PATH"; cd / || exit 1; S=$ROUTE3_EVID_STAGE
  route3_fields_ok || exit 1
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
# S1.1 — AUTHORITY: Peter's written provisioning authorization (stage S1). Installs and holds the reviewed Python package closure from the host's own Ubuntu archive. Network: the host's configured mirror only.
# NOTHING S1.1 installs or holds is ever removed or unheld by this plan: rollback of the package set is an ATTENDED boundary (block R, status 28), decided only by Peter from the evidence kept here.
# The reviewed intent (apt.intent), a pre-snapshot (beforeC1.dpkg) and the Route 3 hold list (held.new) are recorded first. The one apt-get then carries two diagnostic in-transaction hooks (block D): apt.txn is what the
# invocation SUBMITTED, apt.effects is what dpkg was OBSERVED to report afterwards (it can include an effect another configured hook produced; it is not ownership). Success stays fail-closed on them.
# Right after apt-get returns (any status) the validated observation is copied durably to observed.pkgs and afterC1.dpkg records the package set. If the block, or apt, dies, the evidence on disk is what the attending operator has.
( set -o pipefail; umask 022; export PATH="$ROUTE3_PATH"; cd / || exit 1; E=$ROUTE3_EVID
  route3_fields_ok || exit 1
  route3_evid_ok || { echo "NO-GO: S1.0 has not completed (no published, verified evidence)"; exit 2; }
  ! grep -qx begin-C1 "$E/checkpoints" || { echo "NO-GO: S1.1 was already begun; run block R, never retry in place"; exit 2; }
  route3_apt_idle || exit 2
  a=$(dpkg --audit 2>&1); [ $? -eq 0 ] && [ -z "$a" ] || { echo "NO-GO: dpkg --audit reports a package in a partial state"; exit 2; }
  route3_apt_check || exit 2
  { [ -z "$ROUTE3_TODO" ] || printf '%s\n' "$ROUTE3_TODO" | tr = '\t'; } | LC_ALL=C sort > "$E/apt.intent.tmp" || exit 3
  route3_pkgs > "$E/beforeC1.dpkg" || exit 3
  sync -- "$E/apt.intent.tmp" "$E/beforeC1.dpkg" && mv -- "$E/apt.intent.tmp" "$E/apt.intent" && sync -- "$E" || exit 3
  route3_apt_hook_write || exit 3
  route3_cp begin-C1 || exit 3
  [ -z "$ROUTE3_TODO" ] || route3_apt_install $ROUTE3_TODO
  arc=$?
  route3_pkgs > "$E/afterC1.dpkg" || exit 5
  route3_observed_write "$E/afterC1.dpkg" || { echo "ESCALATE: the package observation of this attempt is missing or contradictory; run block R, which changes no package and no hold"; exit 5; }
  [ "$arc" -eq 0 ] || { echo "apt-get install status $arc"; exit 3; }
  route3_delta_ok "$E/beforeC1.dpkg" "$E/afterC1.dpkg" || exit 4
  route3_python_ok || exit 4
  : > "$E/held.new"
  for t in $ROUTE3_APT_PACKAGES; do
    n=${t%%=*}
    grep -qxF -- "$n" "$E/prestate.holds" || printf '%s\n' "$n" >> "$E/held.new"
  done
  sync -- "$E/held.new" || exit 6
  if [ -s "$E/held.new" ]; then apt-mark hold -- $(cat "$E/held.new") || exit 6; fi
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
  route3_python_ok || bad=1
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
after a hook failure, with malformed or missing evidence, and for a completed STOP-A withdrawal. No pre-install record, post-invoke observation, package delta, PID, timestamp, lock observation or combination of them is authorization to do so: apt runs the configured `DPkg::Post-Invoke` list in order
under the same frontend lock, so an earlier configured hook can run a separate `dpkg` operation of the same name and version before the Route 3 hook queries package state, and the Route 3 observation then looks exactly like an effect of the submitted action. Attribution is therefore not decidable by the plan.

S1.1 keeps root-only durable evidence in `/root/route3-evidence` for the attending operator: the reviewed intent (`apt.intent`), the pre-state (`prestate.dpkg`, `prestate.holds`, `beforeC1.dpkg`), what the invocation submitted (`apt.txn`), what dpkg was observed to report afterwards
(`apt.effects`, `observed.pkgs`: a diagnostic observation that can include effects produced by another configured hook, never ownership), the Route 3 hold list (`held.new`) and the later package and hold state (`afterC1.dpkg`, `now.dpkg`, `now.holds`).

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
        echo "(apt.intent apt.txn apt.effects observed.pkgs held.new beforeC1.dpkg afterC1.dpkg now.dpkg now.holds prestate.dpkg prestate.holds in $E). apt.effects is a diagnostic observation, not proof of who installed a package."
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
| C1 packages | S1.1 (`apt-get install` with the two diagnostic in-transaction hooks, `apt-mark hold`) | **none: packages and holds are an attended boundary.** R compares the current set with `prestate.dpkg` / `prestate.holds`: equal = no recovery needed; any difference = no package or hold is changed, the differences are printed, all evidence is kept (no remove, purge, autoremove, downgrade, hold or unhold) | 0 only when equal; **28** when any package or hold difference remains (attended recovery, Peter decides) | `now.dpkg` equals `prestate.dpkg` and `now.holds` equals `prestate.holds` | an apt/dpkg run is active (24), the package or hold set cannot be read (24), a pre-state package is gone or changed (25), a non-recorded addition remains after an equal C1 comparison (26), the manager or identity cannot be queried (27), **any package or hold difference at C1 (28)** | none |
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
  route3_fields_ok && route3_tree_ok && route3_python_ok || exit 1
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
  route3_fields_ok && route3_tree_ok && route3_python_ok || exit 1
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
( export PATH="$ROUTE3_PATH"; cd / || exit 1
  grep -qx done-C8 "$ROUTE3_EVID/checkpoints" || { echo "NO-GO: S3.5 has not completed"; exit 2; }
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
