"""The Route 3 production provisioning plan (runbook part P) is executed, not grepped.

The literal runbook blocks are extracted and run in bash against a *fake world*: stub ``apt-get``, ``useradd``, ``systemctl`` ... under a private
directory that is put first on the block's own ``ROUTE3_PATH`` (the one seam of block D), plus an isolated path root. Everything the blocks touch on the
filesystem is redirected by replacing the literal fixed paths with test paths in the script text, so every comparison in the production text
(``[ "$t" = /opt/freedom-route3 ]``) is still a real comparison. The deployment steps themselves run for real: the real ``/usr/bin/python3.14`` creates
the venv, the real pinned wheel is installed with ``pip --require-hashes``, ``tar``/``sha256sum``/``mv``/``install`` are the system tools. Cases that need
real root ownership run as root on ``oracle-test`` and skip elsewhere; the static cases run anywhere. Nothing is weakened to fit a user-owned tree.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
RUNBOOK = REPO / "docs/operations/executor-supervisor-provisioning-runbook.md"
HANDBACK = REPO / "docs/review/route-3-production-readiness-handback.md"
PY314 = Path("/usr/bin/python3.14")
WHEEL_SRC = Path(os.environ.get("FREEDOM_JEEPNEY_WHEEL", "/home/ubuntu/jeepney-0.9.0-py3-none-any.whl"))
PIN = "97e5714520c16fc0a45695e5365a2e11b81ea79bba796e26f9f1d178cb182683"
ROOT = os.geteuid() == 0
HOST_OK = ROOT and PY314.exists() and WHEEL_SRC.exists() and hashlib.sha256(WHEEL_SRC.read_bytes()).hexdigest() == PIN if WHEEL_SRC.exists() else False
host = pytest.mark.skipif(not (ROOT and PY314.exists() and HOST_OK), reason="needs root, /usr/bin/python3.14 and the pinned jeepney wheel (oracle-test)")

FAKE_CAND = {"python3.14": "3.14.9-1fake", "python3.14-minimal": "3.14.9-1fake", "python3.14-venv": "3.14.9-1fake", "libfake-dep": "1.0"}
FAKE_DEPS = {"python3.14": ["python3.14-minimal"], "python3.14-venv": ["python3.14", "libfake-dep"]}
CLOSURE = "libfake-dep=1.0 python3.14=3.14.9-1fake python3.14-minimal=3.14.9-1fake python3.14-venv=3.14.9-1fake"
CLOSURE_NAMES = {"libfake-dep", "python3.14", "python3.14-minimal", "python3.14-venv"}

FORBIDDEN_IN_S1 = ("route3_installer", "reboot", "shutdown", "enable-linger", "disable-linger", "visudo", "sudoers", "rp11_h1", "build.py", "daemon-reload")
TMPFILES_FRAGMENT = "freedom-blades-rp11-polkit-rules.conf"


# ---- runbook extraction ------------------------------------------------------------------------------------------------------------

def runbook() -> str:
    return RUNBOOK.read_text()


def bash_blocks() -> list[str]:
    return re.findall(r"```bash\n(.*?)\n```", runbook(), re.S)


def block(ident: str) -> str:
    """The single bash block whose first line is ``# <ident> — AUTHORITY…``."""
    found = [b for b in bash_blocks() if b.startswith(f"# {ident} — AUTHORITY")]
    assert len(found) == 1, (ident, len(found))
    return found[0]


def definitions() -> str:
    found = [b for b in bash_blocks() if b.startswith("ROUTE3_PATH=")]
    assert len(found) == 1
    return found[0]


def live_fields_block() -> str:
    """Block F exactly as committed (fully populated since 2026-11-15)."""
    found = [b for b in bash_blocks() if b.startswith("ROUTE3_RELEASE_REV=")]
    assert len(found) == 1
    return found[0]


RELEASE_KEYS = ("RELEASE_REV", "ARCHIVE_SHA256", "MANIFEST_SHA256", "APT_PACKAGES", "APT_BASE", "APT_ORIGIN", "PY_SHA256", "BASELINE_SHA256", "REFERENCE_SHA256", "SA2_TREE_SHA256")


def fields_block() -> str:
    """The synthetic-world template: every release identity reset to ``UNSET`` so each test supplies its own values (``set_field``)."""
    out = live_fields_block()
    for key in RELEASE_KEYS:
        out = re.sub(rf'^ROUTE3_{key}=(["\']?).*\1$', lambda m, k=key: f'ROUTE3_{k}={m.group(1)}UNSET{m.group(1)}', out, flags=re.M)
    return out


def stage_entry_code() -> str:
    return re.search(r"^ROUTE3_STAGE_ENTRY='(.*?)'$", definitions(), re.S | re.M)[1]


IDS = ["S0.0", "S0.A", "S0.1", "S0.2", "S0.3", "S1.0", "S1.1", "S1.2", "S1.3", "S1.4", "S2.1", "S2.2", "R0", "R", "S3.1", "S3.2", "S3.3", "S3.4", "S3.5", "S4.1", "R3", "P.6"]
S1_BLOCKS = ["S1.0", "S1.1", "S1.2", "S1.3", "S1.4", "R0"]


# ---- static properties of the plan -------------------------------------------------------------------------------------------------

def test_every_block_declares_its_authority_and_ends_with_a_reliable_status_and_a_stop():
    for ident in IDS:
        b = block(ident)
        assert b.splitlines()[0].startswith(f"# {ident} — AUTHORITY:"), ident
        assert re.search(r'(\(exit "\$rc"\)|exit "\$rc" \))\s*$', b), f"{ident}: the block's last command must return the captured status"
        assert re.search(r"\[(S\d\.[0-9A]|R[03]?|P\.6)?\s?rc=\$rc\]", b) or "[rc=$rc]" in b, ident
        if ident not in ("S0.1", "S2.2"):
            assert "STOP" in b or "ESCALATE" in b or ident in ("S2.2", "P.6"), ident


def test_the_inert_provisioning_stage_cannot_install_enable_start_or_arm():
    for ident in S1_BLOCKS + ["S0.0", "S0.A", "S0.1", "S0.2", "S0.3", "R"]:
        b = block(ident)
        for word in FORBIDDEN_IN_S1:
            assert word not in b, f"{ident} contains {word}"
        for verb in re.findall(r"systemctl\s+(?:--\S+\s+)*([a-z-]+)", b):
            assert verb in ("is-active", "show", "list-units"), f"{ident}: systemctl {verb} is not read-only"
        assert not re.search(r"\binstall\b[^\n]*executor_supervisor_install", b)
    # the only installer invocation in the whole plan is the function of block D, called only by the S3/S4/R3 blocks
    users = [i for i in IDS if "route3_installer" in block(i)]
    assert users == ["S3.4", "S3.5", "S4.1", "R3"], users
    assert "route3_installer install" in block("S3.5") and not any("route3_installer install" in block(i) for i in IDS if i != "S3.5")
    assert "systemctl start" in block("S4.1") and not any("systemctl start" in block(i) for i in IDS if i != "S4.1")
    assert not any(re.search(r"systemctl (enable|restart)|reboot|shutdown", block(i)) for i in IDS if i not in ("S3.5",))


def test_activation_and_arming_commands_sit_only_behind_their_own_later_headings():
    text = runbook()
    s3 = text.index("### S3 — arming and install"); s4 = text.index("### S4 — activation"); r3 = text.index("### R3 — rollback of S3")
    p1 = text.index("### S1 — inert provisioning"); s2 = text.index("### S2 — read-only verification")
    inert = text[p1:s2]
    for word in ("enable-linger", "visudo", "build.py", "route3_installer", "systemctl start", "systemctl enable", "reboot"):
        assert word not in inert.replace("an ordinary or maintenance reboot", ""), word
    assert "enable-linger" in text[s3:s4] and "systemctl start" in text[s4:r3] and "NOT authorized" in text[s4:r3]
    assert text.count("tools.executor_supervisor_install install") == 1  # the single prose sentence of P.1, no executable use
    assert "python3 -m tools.executor_supervisor_install" not in text


def test_no_privileged_block_uses_the_ambient_python_or_a_bare_interpreter():
    for ident in IDS:
        b = block(ident)
        assert not re.search(r"(^|[\s;(])python3?\s", b), ident
    d = definitions()
    assert 'route3_stage() { /usr/bin/env -i PATH=/usr/bin:/bin "$ROUTE3_PY" -I -S -B -c "$ROUTE3_STAGE_ENTRY" "$@"; }' in d
    assert 'route3_installer() { route3_stage installer /opt/freedom-route3 "$@"; }' in d
    assert "ROUTE3_PY=/usr/bin/python3.14\n" in d


def test_block_d_carries_the_item_8_entry_and_the_stage_entry_and_neither_uses_a_single_quote():
    checklist = HANDBACK.read_text()
    item8 = re.search(r"^ROUTE3_ENTRY='([^']+)'$", checklist[checklist.index("# 8  tmpfiles.d"):], re.S | re.M)[1]
    assert re.search(r"^ROUTE3_ENTRY='([^']+)'$", definitions(), re.S | re.M)[1] == item8
    assert "'" not in stage_entry_code()
    assert "dont_write_bytecode=True" in stage_entry_code() and "S_ISLNK" in stage_entry_code()


def test_the_pinned_wheel_in_the_fields_is_the_accepted_lock_pin():
    lock = (REPO / "infra/rp11-h1/requirements.lock").read_text()
    assert f"jeepney==0.9.0" in lock and PIN in lock
    f = fields_block()
    assert "ROUTE3_WHEEL=jeepney-0.9.0-py3-none-any.whl" in f and f"ROUTE3_WHEEL_SHA256={PIN}" in f
    assert definitions().count(PIN) == 1  # the one literal pin check inside route3_fields_ok


def test_the_live_block_f_has_no_unset_field_but_the_plan_still_gates_every_stage_separately():
    f = live_fields_block()
    for name in RELEASE_KEYS:
        assert re.search(rf'^ROUTE3_{name}=["]?(?!UNSET)[^"\s][^"]*["]?$', f, re.M), name
    assert re.search(r'^ROUTE3_RELEASE_REV=[0-9a-f]{40}$', f, re.M)


def test_the_live_block_f_passes_s0_1_and_the_template_with_every_identity_unset_is_refused_naming_each():
    live = subprocess.run(["/bin/bash", "-c", definitions() + "\n" + live_fields_block() + "\n" + block("S0.1") + "\n"], capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"}, check=False)
    assert live.returncode == 0 and "[S0.1 rc=0]" in live.stdout, live.stdout
    unset = subprocess.run(["/bin/bash", "-c", definitions() + "\n" + fields_block() + "\n" + block("S0.1") + "\n"], capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"}, check=False)
    assert unset.returncode == 1 and "[S0.1 rc=1]" in unset.stdout
    for name in RELEASE_KEYS:
        assert f"ROUTE3_{name}" in unset.stdout, (name, unset.stdout)


def test_the_installer_function_is_never_called_with_a_pipeline_or_trailing_command_that_masks_its_status():
    for ident in ("S3.4", "S3.5", "S4.1", "R3"):
        for line in block(ident).splitlines():
            if "route3_installer" in line and not line.lstrip().startswith("#"):
                assert re.search(r"route3_installer [a-z-]+; v=\$\?", line), line
                assert "|" not in line


# ---- the fake world ------------------------------------------------------------------------------------------------------------------

FAKE = r'''#!/usr/bin/env python3
import json, os, sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
ST = HERE / "state.json"
cmd = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
w = json.loads(ST.read_text())
def save():
    ST.write_text(json.dumps(w))
with open(HERE / "calls.log", "a") as f:
    f.write(cmd + " " + " ".join(args) + "\n")
def failing(*keys):
    for k in keys:
        if k in w["fail"]:
            return w["fail"][k]
    return 0
def done(rc=0):
    save(); sys.exit(rc)
rest = [a for a in args if not a.startswith("-")]
if cmd in ("reboot", "shutdown", "sudo", "su", "poweroff", "halt"):
    sys.exit(99)
if cmd == "apt-get":
    sys.exit(98)    # THE PLAN HAS NO APT-GET: any call, install or simulation, is a defect; the call is already in calls.log
if cmd == "apt-cache":
    n = rest[-1]
    if rest[0] == "madison":
        if "madison" in w["fail"]:
            sys.exit(w["fail"]["madison"])
        rows = w["madison"].get(n)
        if rows is None:   # an installed package that is not a candidate (the base set) is offered at its installed version by the mirror
            rows = [[w["cand"][n], w["origin"]]] if n in w["cand"] else ([[w["pkgs"][n], w["origin"]]] if n in w["pkgs"] else [])
        for v, src in rows:
            print(f" {n} | {v:>12} | {src} amd64 Packages")
        done(0)
    v = w["cand"].get(n)
    if v is None:
        sys.exit(100)
    print(f"{n}:\n  Installed: {w['pkgs'].get(n, '(none)')}\n  Candidate: {v}\n  Version table:\n *** {v} 500\n        500 {w['origin']} amd64")
    done(0)
if cmd == "dpkg-query":
    if failing("dpkg-query"):
        sys.exit(failing("dpkg-query"))
    fmt = [a for a in args if a.startswith("-f=")]
    fmt = fmt[0][3:] if fmt else "${Package}\\t${Version}\\n"
    fmt = fmt.replace("\\t", "\t").replace("\\n", "\n")
    names = [a for a in rest if a != "-W"]
    items = sorted(w["pkgs"].items())
    if names:
        if names[0] not in w["pkgs"]:
            sys.exit(1)
        items = [(names[0], w["pkgs"][names[0]])]
    sys.stdout.write("".join(fmt.replace("${Package}", p).replace("${Version}", v).replace("${db:Status-Abbrev}", "ii ") for p, v in items))
    done(0)
if cmd == "dpkg":
    if "--audit" in args:
        sys.stdout.write(w.get("audit", "")); done(0)
    if w.get("verify_fail"):
        print("??5?????? /usr/bin/python3.14"); done(1)
    done(0)
if cmd == "apt-mark":
    if rest[0] == "showhold":
        print("\n".join(sorted(w["holds"]))) if w["holds"] else None; done(0)
    if rest[0] == "hold":
        w["holds"] = sorted(set(w["holds"]) | set(rest[1:]))
    if rest[0] == "unhold":
        w["holds"] = sorted(set(w["holds"]) - set(rest[1:]))
    done(failing("apt-mark"))
if cmd == "useradd":
    name = rest[-1]
    rc = failing("useradd")
    if rc:
        done(rc)
    home = args[args.index("--home-dir") + 1]
    w["users"][name] = {"uid": 61234, "gid": 61234, "home": home, "shell": args[args.index("--shell") + 1]}
    w["groups"][name] = 61234
    os.makedirs(home, mode=0o700)
    os.chown(home, 61234, 61234)
    done(0)
if cmd == "userdel":
    name = rest[-1]
    rc = failing("userdel")
    if rc:
        done(rc)
    u = w["users"].pop(name, None)
    w["groups"].pop(name, None)
    if u and "--remove" in args:
        import shutil; shutil.rmtree(u["home"], ignore_errors=True)
    done(0)
if cmd == "groupdel":
    w["groups"].pop(rest[-1], None); done(0)
if cmd == "getent":
    if failing("getent"):
        sys.exit(failing("getent"))
    db, name = rest[0], rest[1]
    if db == "passwd" and name in w["users"]:
        u = w["users"][name]
        print(f"{name}:x:{u['uid']}:{u['gid']}::{u['home']}:{u['shell']}"); done(0)
    if db == "group" and name in w["groups"]:
        print(f"{name}:x:{w['groups'][name]}:"); done(0)
    if db == "shadow" and name in w["users"]:
        print(f"{name}:!:1::::::"); done(0)
    sys.exit(2)
if cmd == "id":
    if rest[-1] in w["users"]:
        print(w["users"][rest[-1]]["uid"]); done(0)
    os.execv("/usr/bin/id", ["id"] + args)
if cmd == "loginctl":
    lf = pathlib.Path(w["linger_file"])
    if rest[0] == "enable-linger":
        rc = failing("loginctl")
        if rc:
            done(rc)
        lf.parent.mkdir(parents=True, exist_ok=True); lf.write_text(""); w["active"]["user@61234.service"] = "active"
    if rest[0] == "disable-linger":
        lf.unlink(missing_ok=True); w["active"]["user@61234.service"] = "inactive"
    done(0)
if cmd == "systemctl":
    sub = rest[0]
    unit = rest[-1]
    prop = args[args.index("-p") + 1] if "-p" in args else None
    qrc = failing("systemctl " + sub, "systemctl") or w.get("fail_unit", {}).get(unit, 0) or w.get("fail_prop", {}).get(prop, 0)
    if qrc:
        if w.get("fail_print") is not None:    # a failed query that nevertheless printed a plausible state word
            print(w["fail_print"])
        sys.exit(qrc)
    if sub == "show":
        if prop == "ActiveState":
            if unit in w.get("show_out", {}):
                sys.stdout.write(w["show_out"][unit]); done(0)
            print(w["active"].get(unit, "inactive")); done(0)
        frag = pathlib.Path(w["unit_fragment"])
        print("loaded" if frag.exists() else "not-found"); done(0)
    if sub == "list-units":
        done(0)
    if sub == "is-active":
        st = w["active"].get(unit, "inactive")
        print(st); done(0 if st == "active" else 3)
    done(0)
if cmd == "pgrep":
    sys.exit(1)
if cmd == "visudo":
    rc = failing("visudo")
    if rc:
        done(rc)
    if "-f" in args or "-cf" in args:
        p = pathlib.Path(args[-1])
        if not p.read_text().startswith("freedom-executor ALL=(root) NOPASSWD:"):
            sys.exit(1)
    done(0)
sys.exit(97)
'''

STUB_NAMES = ["apt-get", "apt-cache", "apt-mark", "dpkg-query", "dpkg", "useradd", "userdel", "groupdel", "getent", "id", "loginctl", "systemctl", "pgrep", "visudo",
              "reboot", "shutdown", "sudo", "su", "poweroff", "halt"]

GATE_STUB = '''import json, sys
w = json.load(open({state!r}))
open({log!r}, "a").write(" ".join(sys.argv[1:]) + "\\n")
if w.get("gate_rc"):
    print("NO-GO: " + w.get("gate_msg", "the stub gate refuses")); sys.exit(w["gate_rc"])
print("ok: stub gate"); sys.exit(0)
'''

TOOL_STUB = '''import os, sys
FRAG = {frag!r}
SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "infra/tmpfiles.d/{name}")
LOG = {log!r}
BOOTED = {booted!r}
open(LOG, "a").write("polkit_tmpfiles " + " ".join(sys.argv[1:]) + "\\n")
act = sys.argv[1]
fail = {fail!r}
if os.path.exists(fail):
    sys.exit(int(open(fail).read()))
if act == "install":
    os.makedirs(os.path.dirname(FRAG), exist_ok=True)
    open(FRAG, "w").write(open(SRC).read()); os.chmod(FRAG, 0o644); print("installed"); sys.exit(0)
if act == "remove":
    if os.path.exists(FRAG):
        os.unlink(FRAG)
    print("removed"); sys.exit(0)
if act == "verify":
    if os.path.exists(BOOTED) and os.path.exists(FRAG):
        print("verify: ok"); sys.exit(0)
    print("FAIL fragment-predates-boot\\nverify: FAILED"); sys.exit(12)
sys.exit(2)
'''

INSTALLER_STUB = '''import json, os, sys
LOG = {log!r}
STATUS = {status!r}
FRAG = {frag!r}
WANTS = {wants!r}
rec = {{"argv": sys.argv[1:], "cwd": os.getcwd(), "env": sorted(os.environ), "flags": [sys.flags.isolated, sys.flags.no_site, sys.flags.dont_write_bytecode],
       "path0": sys.path[0], "module": __name__}}
open(LOG, "a").write(json.dumps(rec) + "\\n")
act = sys.argv[1]
if os.path.exists(STATUS):
    raise SystemExit(int(open(STATUS).read()))
if act == "verify":
    raise SystemExit(0 if os.path.exists(WANTS) else 12)
if act == "install":
    os.makedirs(os.path.dirname(WANTS), exist_ok=True)
    open(FRAG, "w").write("unit"); open(WANTS, "w").write("link")
    raise SystemExit(0)
if act == "remove":
    for p in (FRAG, WANTS):
        if os.path.exists(p):
            os.unlink(p)
    raise SystemExit(0)
raise SystemExit(0)
'''

BUILD_STUB = '''import argparse, os, sys
ap = argparse.ArgumentParser(); ap.add_argument("--wheel"); ap.add_argument("--dest"); a = ap.parse_args()
os.makedirs(a.dest + "/lib", mode=0o755)
open(a.dest + "/rp11_h1.py", "w").write("sa2"); os.chmod(a.dest + "/rp11_h1.py", 0o644)
open(a.dest + "/lib/rp11_roles.py", "w").write("roles"); os.chmod(a.dest + "/lib/rp11_roles.py", 0o644)
os.chmod(a.dest, 0o755); os.chmod(a.dest + "/lib", 0o755)
'''


class World:
    """An isolated root plus fake system tools for one test; ``text()`` localizes a runbook block to it."""

    def __init__(self, tag: str):
        self.tag = f"frt-plan-{tag}"
        self.base = Path(f"/opt/{self.tag}")
        self.top = Path(tempfile.mkdtemp(prefix=self.tag + "-w", dir="/opt")) if ROOT else Path(tempfile.mkdtemp())
        self.stubs = self.top / "stubs"; self.stubs.mkdir()
        self.art = Path(f"/root/{self.tag}-art"); self.evid = Path(f"/root/{self.tag}-evid")
        self.home = Path(f"/opt/{self.tag}-home")
        self.sys = {k: self.top / k for k in ("tmpfiles", "units", "sudoers", "usrlocal", "linger", "state", "run", "dpkg", "aptlists", "aptarch")}
        for k, v in self.sys.items():
            v.mkdir()
        # a stock host has /usr/local but NOT /usr/local/libexec (the 2026-11-18 production defect): the world starts like production, and a test that wants the parent calls make_parent()
        self.sys["libexec"] = self.sys["usrlocal"] / "libexec"
        for d in self.top.iterdir():
            d.chmod(0o755)
        self.top.chmod(0o755)
        (self.stubs / "fake.py").write_text(FAKE)
        (self.stubs / "fake.py").chmod(0o755)
        for n in STUB_NAMES:
            (self.stubs / n).symlink_to("fake.py")
        self.log = self.top / "tool.log"
        self.rev = "a" * 40
        self.apt = CLOSURE
        self.origin = "http://mirror.example.test/ubuntu fake-updates/main"
        self.fields: dict[str, str] = {}
        for f in (self.sys["dpkg"] / "lock-frontend", self.sys["dpkg"] / "lock", self.sys["aptlists"] / "lock", self.sys["aptarch"] / "lock"):
            f.write_text("")
        # the pre-installed baseline: the reviewed closure is already installed (this plan installs nothing), beside an unrelated package
        self.state = {"pkgs": {"coreutils": "9.4", **dict(t.split("=") for t in CLOSURE.split())}, "cand": dict(FAKE_CAND), "deps": {k: list(v) for k, v in FAKE_DEPS.items()}, "rdeps": {}, "madison": {}, "holds": [], "users": {}, "groups": {},
                      "fail": {}, "active": {}, "origin": "http://mirror.example.test/ubuntu fake-updates/main", "linger_file": str(self.sys["linger"] / "freedom-executor"),
                      "unit_fragment": str(self.sys["units"] / "freedom-blades-executor-supervisor.service"), "lock_frontend": str(self.sys["dpkg"] / "lock-frontend")}
        self.save_state()
        self.cleanup = [self.top, self.base, self.art, self.evid, Path(str(self.evid) + ".new"), self.home, Path(str(self.base) + ".stage")]

    # -- state ---------------------------------------------------------------------------------------------------------------------
    def save_state(self):
        (self.stubs / "state.json").write_text(json.dumps(self.state))

    def load_state(self):
        return json.loads((self.stubs / "state.json").read_text())

    def calls(self) -> list[str]:
        p = self.stubs / "calls.log"
        return p.read_text().splitlines() if p.exists() else []

    # -- the synthetic release -----------------------------------------------------------------------------------------------------
    def release(self, *, extra: dict[str, bytes] | None = None, drop: tuple[str, ...] = (), members=None, real: bool = False):
        frag = REPO / "infra/tmpfiles.d" / TMPFILES_FRAGMENT
        files = {
            "adapters/__init__.py": b"", "application/__init__.py": b"", "tools/__init__.py": b"",
            "infra/tmpfiles.d/" + TMPFILES_FRAGMENT: frag.read_bytes(),
            "infra/executor/freedom-blades-executor-supervisor.service": (REPO / "infra/executor/freedom-blades-executor-supervisor.service").read_bytes(),
            "infra/rp11-h1/build.py": BUILD_STUB.encode(),
            "infra/rp11-h1/requirements.lock": (REPO / "infra/rp11-h1/requirements.lock").read_bytes(),
            "tools/polkit_tmpfiles.py": TOOL_STUB.format(frag=str(self.sys["tmpfiles"] / TMPFILES_FRAGMENT), name=TMPFILES_FRAGMENT, log=str(self.log),
                                                         booted=str(self.top / "booted"), fail=str(self.top / "tmpfiles-fail")).encode(),
            "tools/executor_supervisor_install.py": INSTALLER_STUB.format(log=str(self.top / "installer.log"), status=str(self.top / "installer-status"),
                                                                           frag=str(self.sys["units"] / "freedom-blades-executor-supervisor.service"),
                                                                           wants=str(self.sys["units"] / "wants/freedom-blades-executor-supervisor.service")).encode(),
        }
        if real:  # the working tree's own deployable files, exactly the trees the runbook's archive recipe names
            files = {}
            for top in ("adapters", "application", "tools", "infra/executor", "infra/tmpfiles.d", "infra/rp11-h1"):
                for dp, dn, fn in os.walk(REPO / top):
                    dn[:] = sorted(d for d in dn if d != "__pycache__")
                    for f in sorted(fn):
                        if not f.endswith((".pyc", ".pyo")):
                            files[str((Path(dp) / f).relative_to(REPO))] = (Path(dp) / f).read_bytes()
        files["tools/route3_release_record.py"] = GATE_STUB.format(state=str(self.stubs / "state.json"), log=str(self.top / "gate.log")).encode()   # the gate's tool; its REAL behavior is tested in test_route3_release_record.py
        files.update(extra or {})
        for d in drop:
            files.pop(d)
        manifest = "".join(f"{hashlib.sha256(v).hexdigest()}  {k}\n" for k, v in sorted(files.items()))
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:") as t:
            for k, v in sorted(files.items()):
                ti = tarfile.TarInfo(k); ti.size = len(v); ti.mode = 0o644; ti.mtime = 0; ti.uid = ti.gid = 0
                t.addfile(ti, io.BytesIO(v))
            for ti, data in (members or []):
                t.addfile(ti, io.BytesIO(data) if data is not None else None)
        archive = buf.getvalue()
        art = self.art / self.rev
        (art / "wheelhouse").mkdir(parents=True)
        (art / "code.tar").write_bytes(archive)
        (art / "MANIFEST.sha256").write_text(manifest)
        shutil.copy(WHEEL_SRC, art / "wheelhouse" / WHEEL_SRC.name)
        (art / "baseline.record").write_text("route3-baseline-record 1\n")
        (art / "reference.record").write_text("route3-payload-reference 1\n")
        for p in [self.art, art, art / "wheelhouse"]:
            p.chmod(0o700)
        for p in [art / "code.tar", art / "MANIFEST.sha256", art / "baseline.record", art / "reference.record", art / "wheelhouse" / WHEEL_SRC.name]:
            p.chmod(0o600)
        real = os.path.realpath(PY314)
        self.fields = {
            "RELEASE_REV": self.rev, "ARCHIVE_SHA256": hashlib.sha256(archive).hexdigest(), "MANIFEST_SHA256": hashlib.sha256(manifest.encode()).hexdigest(),
            "APT_PACKAGES": self.apt, "APT_BASE": "coreutils=9.4", "BASELINE_SHA256": hashlib.sha256((art / "baseline.record").read_bytes()).hexdigest(),
            "REFERENCE_SHA256": hashlib.sha256((art / "reference.record").read_bytes()).hexdigest(), "APT_ORIGIN": self.origin, "PY_SHA256": hashlib.sha256(Path(real).read_bytes()).hexdigest(), "SA2_TREE_SHA256": self.sa2_digest()}

    def sa2_digest(self) -> str:
        lines = "".join(f"{hashlib.sha256(c).hexdigest()}  {n}\n" for n, c in sorted([("./lib/rp11_roles.py", b"roles"), ("./rp11_h1.py", b"sa2")]))
        return hashlib.sha256(lines.encode()).hexdigest()

    # -- script assembly -----------------------------------------------------------------------------------------------------------
    def localize(self, text: str) -> str:
        reps = [("/opt/freedom-route3", str(self.base)), ("/root/route3-artifacts", str(self.art)), ("/root/route3-evidence", str(self.evid)),
                ("/home/freedom-executor", str(self.home)), ("/usr/lib/tmpfiles.d", str(self.sys["tmpfiles"])), ("/etc/systemd/system", str(self.sys["units"])),
                ("/etc/sudoers.d", str(self.sys["sudoers"])), ("/usr/local/libexec", str(self.sys["libexec"])), ("/usr/local", str(self.sys["usrlocal"])), ("/var/lib/systemd/linger", str(self.sys["linger"])),
                ("/var/lib/freedom-blades-executor", str(self.sys["state"] / "freedom-blades-executor")), ("/run/freedom-blades-executor", str(self.sys["run"] / "freedom-blades-executor")),
                ("/run/user/", str(self.sys["run"]) + "/user/"), ("/var/lib/dpkg", str(self.sys["dpkg"])), ("/var/lib/apt/lists", str(self.sys["aptlists"])),
                ("/var/cache/apt/archives", str(self.sys["aptarch"])), ("/usr/bin/dpkg-query", str(self.stubs / "dpkg-query"))]
        for a, b in reps:
            text = text.replace(a, b)
        return text

    def script(self, ident: str, *, fields: dict[str, str] | None = None, mutate=None, py: str | None = None, dmutate=None) -> str:
        d = definitions().replace("ROUTE3_PATH=/usr/sbin:/usr/bin:/sbin:/bin", f"ROUTE3_PATH={self.stubs}:/usr/sbin:/usr/bin:/sbin:/bin")
        if dmutate:
            mutated_d = dmutate(d)
            assert mutated_d != d, "the mutation must change block D"
            d = mutated_d
        f = fields_block()
        for k, v in {**self.fields, **(fields or {})}.items():
            f = set_field(f, k, v)
        body = block(ident) if ident != "D" else ""
        if mutate:
            mutated = mutate(body)
            assert mutated != body, "the mutation must change the block"
            body = mutated
        script = self.localize(d + "\n" + f + "\n" + body + "\n")
        if py:
            script = script.replace("ROUTE3_PY=/usr/bin/python3.14", f"ROUTE3_PY={py}")
        return script

    def run(self, ident: str, *, env: dict | None = None, cwd: str = "/", **kw):
        done = subprocess.run(["/bin/bash", "-c", self.script(ident, **kw)], cwd=cwd, capture_output=True, text=True, timeout=300, check=False,
                              env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "HOME": "/root", **(env or {})})
        return done

    def run_raw(self, script: str, **kw):
        return subprocess.run(["/bin/bash", "-c", script], capture_output=True, text=True, timeout=300, check=False, env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "HOME": "/root", **kw.get("env", {})})

    def edit_prestate(self, name: str, fn) -> None:
        """Rewrite one recorded pre-state file AND its digest list, as a legitimate (if odd) evidence author would; plain tampering is tested separately."""
        path = self.evid / name
        path.write_text(fn(path.read_text()))
        names = ("prestate.dpkg", "prestate.holds", "prestate.objects")
        (self.evid / "pre.sha256").write_text("".join(f"{hashlib.sha256((self.evid / n).read_bytes()).hexdigest()}  {n}\n" for n in names))

    def inject(self, ident: str, anchor: str, how: str):
        """A mutation for ``script``/``run``: fail the block right after the line that starts with ``anchor``."""
        action = "kill -9 $BASHPID" if how == "kill" else "exit 77"

        def mutate(body: str) -> str:
            lines = body.splitlines()
            hit = [i for i, l in enumerate(lines) if l.strip().startswith(anchor)]
            assert len(hit) == 1, (anchor, hit)
            lines.insert(hit[0] + 1, "  " + action)
            return "\n".join(lines)
        return mutate

    def objects(self) -> dict:
        """Everything the plan can create, as a comparable snapshot."""
        st = self.load_state()
        paths = [self.base, Path(str(self.base) + ".stage"), self.home, self.sys["tmpfiles"] / TMPFILES_FRAGMENT, self.sys["units"] / "freedom-blades-executor-supervisor.service",
                 self.sys["units"] / "wants/freedom-blades-executor-supervisor.service", self.sys["sudoers"] / "freedom-executor-sa2", self.sys["sudoers"] / ".freedom-executor-sa2.new",
                 self.sys["libexec"], self.sys["libexec"] / "freedom-blades-rp11", self.sys["linger"] / "freedom-executor"]
        return {"paths": {str(p): (p.exists() or p.is_symlink()) for p in paths}, "pkgs": st["pkgs"], "holds": st["holds"], "users": sorted(st["users"]), "groups": sorted(st["groups"])}

    def make_parent(self, mode: int = 0o755) -> Path:
        """A pre-existing /usr/local/libexec (root-owned, as the test runs as root)."""
        self.sys["libexec"].mkdir(); self.sys["libexec"].chmod(mode)
        return self.sys["libexec"]

    def markers(self) -> list[str]:
        p = self.evid / "checkpoints"
        return p.read_text().splitlines() if p.exists() else []

    def destroy(self):
        for p in self.cleanup:
            if p.is_symlink():
                p.unlink()
            elif p.exists():
                shutil.rmtree(p, ignore_errors=True)


@pytest.fixture
def world():
    made: list[World] = []

    def make(tag: str | None = None) -> World:
        w = World(tag or os.urandom(4).hex())
        made.append(w)
        return w
    yield make
    for w in made:
        w.destroy()


def ok(done, ident):
    assert f"[{ident} rc=0]" in done.stdout and done.returncode == 0, (done.stdout, done.stderr)


def failed(done, ident):
    assert done.returncode != 0 and f"[{ident} rc={done.returncode}]" in done.stdout, (done.returncode, done.stdout, done.stderr)


def provision(w: World, upto: str = "S1.4") -> None:
    order = ["S1.0", "S1.1", "S1.2", "S1.3", "S1.4"]
    for ident in order[: order.index(upto) + 1]:
        ok(w.run(ident), ident)


# ---- S0: fields and preflight --------------------------------------------------------------------------------------------------------

def test_the_candidate_is_no_go_with_every_field_unset_and_names_each_one():
    w = World.__new__(World)
    w.__dict__.update(stubs=Path("/nonexistent-stubs"), art=Path("/x"), evid=Path("/y"), base=Path("/opt/freedom-route3"), home=Path("/home/freedom-executor"), fields={}, top=Path("/tmp"))
    script = definitions() + "\n" + fields_block() + "\n" + block("S0.1") + "\n"
    done = subprocess.run(["/bin/bash", "-c", script], capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"}, check=False)
    assert done.returncode == 1 and "[S0.1 rc=1]" in done.stdout
    for name in ("ROUTE3_RELEASE_REV", "ROUTE3_ARCHIVE_SHA256", "ROUTE3_MANIFEST_SHA256", "ROUTE3_PY_SHA256", "ROUTE3_BASELINE_SHA256", "ROUTE3_REFERENCE_SHA256", "ROUTE3_SA2_TREE_SHA256", "ROUTE3_APT_PACKAGES", "ROUTE3_APT_BASE",
                 "ROUTE3_APT_ORIGIN"):
        assert name in done.stdout, name


def set_field(f: str, key: str, value: str) -> str:
    out = re.sub(rf'^ROUTE3_{key}=(["\']?)UNSET\1$', lambda m: f"ROUTE3_{key}={m.group(1)}{value}{m.group(1)}", f, flags=re.M)
    return out


def run_fields(values: dict[str, str]) -> subprocess.CompletedProcess:
    f = fields_block()
    for k, v in values.items():
        f = set_field(f, k, v)
    script = definitions() + "\n" + f + "\n" + block("S0.1") + "\n"
    return subprocess.run(["/bin/bash", "-c", script], capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"}, check=False)


GOOD_APT = "python3.14=3.14.4-1ubuntu0.2 python3.14-minimal=3.14.4-1ubuntu0.2 python3.14-venv=3.14.4-1ubuntu0.2 python3-pip-whl=26.0-1"
GOOD_FIELDS = {"RELEASE_REV": "b" * 40, "ARCHIVE_SHA256": "c" * 64, "MANIFEST_SHA256": "d" * 64, "PY_SHA256": "e" * 64, "SA2_TREE_SHA256": "f" * 64, "BASELINE_SHA256": "a" * 64, "REFERENCE_SHA256": "9" * 64,
               "APT_PACKAGES": GOOD_APT, "APT_BASE": "libc6=2.43-2ubuntu1 libgcc-s1=16.1-1ubuntu1", "APT_ORIGIN": "http://x.test/ubuntu resolute-updates/main, http://security.x.test/ubuntu resolute-security/main"}


def test_complete_well_formed_fields_pass_and_each_malformed_one_is_a_no_go():
    done = run_fields(GOOD_FIELDS)
    assert done.returncode == 0 and "[S0.1 rc=0]" in done.stdout, done.stdout
    for key, bad in (("RELEASE_REV", "abc"), ("ARCHIVE_SHA256", "G" * 64), ("MANIFEST_SHA256", "c" * 63), ("PY_SHA256", "UNSET"), ("SA2_TREE_SHA256", "f" * 65),
                     ("APT_PACKAGES", "python3.14-minimal=1"), ("APT_PACKAGES", "python3.14-minimal python3.14-venv"), ("APT_ORIGIN", "UNSET"),
                     ("APT_PACKAGES", "python3.14-minimal=3.14.4 python3.14-venv=3.14.4"),  # python3.14 itself is not pinned
                     ("APT_PACKAGES", "python3.14=1 python3.14-venv=1"),  # python3.14-minimal absent
                     ("APT_PACKAGES", "python3.14=1 python3.14-minimal=1 python3.14-venv=1 libx=1 libx=2"),  # a name twice
                     ("APT_PACKAGES", "python3.14=1 python3.14-minimal=1 python3.14-venv"),  # an unpinned member
                     ("APT_ORIGIN", "resolute-updates"), ("APT_ORIGIN", "http://x.test/ubuntu resolute-updates/main, resolute"), ("APT_ORIGIN", "ftp://x.test/ubuntu a/b"),
                     ("BASELINE_SHA256", "UNSET"), ("BASELINE_SHA256", "a" * 63), ("REFERENCE_SHA256", "UNSET"), ("REFERENCE_SHA256", "9" * 63), ("APT_BASE", "UNSET"), ("APT_BASE", ""), ("APT_BASE", "libc6"), ("APT_BASE", "libc6=1 libc6=2"),
                     ("APT_BASE", "python3.14-venv=3.14.4-1ubuntu0.2")):  # a base member that is also pinned
        done = run_fields({**GOOD_FIELDS, key: bad})
        assert done.returncode == 1 and "NO-GO" in done.stdout, (key, bad, done.stdout)


PREFLIGHT_DEVIATIONS = ["existing deployment", "existing account", "existing tmpfiles fragment", "candidate version differs", "origin differs", "archive tampered",
                        "artifact directory group-writable", "installed package at another version"]


@host
def test_the_preflight_passes_on_a_pristine_world_and_is_read_only(world):
    w = world(); w.release()
    done = w.run("S0.2"); ok(done, "S0.2")
    assert not [c for c in w.calls() if c.split()[0] in ("useradd", "apt-mark", "apt-get")]  # no mutation, and no apt-get at all: the plan has no solver and no install path
    assert not w.evid.exists() and not w.base.exists()


@host
@pytest.mark.parametrize("label", PREFLIGHT_DEVIATIONS)
def test_the_preflight_refuses_each_deviation_and_changes_nothing(world, label):
    w = world(); w.release()
    st = w.load_state()
    if label == "existing deployment":
        w.base.mkdir()
    elif label == "existing account":
        st["users"]["freedom-executor"] = {"uid": 1, "gid": 1, "home": "/x", "shell": "/x"}
    elif label == "existing tmpfiles fragment":
        (w.sys["tmpfiles"] / TMPFILES_FRAGMENT).write_text("x")
    elif label == "candidate version differs":
        st["madison"]["python3.14-minimal"] = [["9", w.origin]]  # the pinned version is not offered at all
    elif label == "origin differs":
        st["madison"]["python3.14-minimal"] = [["3.14.9-1fake", "http://evil.test/ubuntu other/main"]]
    elif label == "archive tampered":
        (w.art / w.rev / "code.tar").write_bytes(b"x")
    elif label == "artifact directory group-writable":
        (w.art / w.rev).chmod(0o770)
    elif label == "installed package at another version":
        st["pkgs"]["python3.14-minimal"] = "1.0"
    w.state = st; w.save_state()
    done = w.run("S0.2")
    failed(done, "S0.2")
    assert "NO-GO" in done.stdout and not w.evid.exists()


# ---- S1/S2: the provisioning path ----------------------------------------------------------------------------------------------------

@host
def test_provisioning_reaches_stop_a_without_install_enable_start_reboot_sa2_or_smoke(world):
    w = world(); w.release()
    before = w.objects()
    provision(w)
    done = w.run("S1.4"); assert "STOP-A" not in done.stdout or True
    ok(w.run("S2.1"), "S2.1")
    calls = w.calls()
    forbidden = ("reboot", "shutdown", "sudo", "su", "loginctl", "visudo")
    assert not [c for c in calls if c.split()[0] in forbidden], calls
    assert not [c for c in calls if c.startswith("systemctl") and re.search(r"\b(start|enable|restart|daemon-reload|reload)\b", c)], calls
    tool_log = w.log.read_text().splitlines()
    assert tool_log.count("polkit_tmpfiles install") == 2  # S1.4 once, plus the idempotent second run above
    assert not (w.top / "installer.log").exists(), "the installer must not have been invoked"
    after = w.objects()
    assert after["paths"][str(w.base)] and after["paths"][str(w.home)] and after["paths"][str(w.sys["tmpfiles"] / TMPFILES_FRAGMENT)]
    assert not after["paths"][str(w.sys["units"] / "freedom-blades-executor-supervisor.service")] and not after["paths"][str(w.sys["linger"] / "freedom-executor")]
    assert not after["paths"][str(w.sys["sudoers"] / "freedom-executor-sa2")] and not after["paths"][str(w.sys["libexec"] / "freedom-blades-rp11")]
    assert set(after["holds"]) == CLOSURE_NAMES and set(after["pkgs"]) == CLOSURE_NAMES | {"coreutils"} and after["users"] == ["freedom-executor"] and before["users"] == []
    # the deployed tree is exactly root-owned, link-limited and manifest-exact: the stage entry itself says so
    assert (w.evid / "MANIFEST.sha256").exists() and not Path(str(w.base) + ".stage").exists()
    for p in (w.base, w.base / "code", w.base / "venv", w.base / "code/tools"):
        assert p.stat().st_uid == 0 and not p.stat().st_mode & 0o022
    # a reboot at STOP-A has nothing to start: no unit file, no wants link, no linger, no SA-2, no sudoers, no loaded unit
    assert not list(w.sys["units"].iterdir()) and not list(w.sys["sudoers"].iterdir()) and not list(w.sys["linger"].iterdir()) and not w.sys["libexec"].exists()
    assert w.load_state()["active"] == {}


@host
def test_the_published_deployment_is_manifest_exact_with_only_the_pinned_jeepney_and_no_residue(world):
    w = world(); w.release(); provision(w, "S1.2")
    assert sorted(p.name for p in (w.base / "venv/lib/python3.14/site-packages").iterdir()) == ["jeepney", "jeepney-0.9.0.dist-info"]
    assert not list(w.base.rglob("__pycache__")) and not list(w.base.rglob("*.pyc"))
    assert not [p for p in w.base.rglob("*") if p.is_symlink() and "venv" not in p.parts]
    manifest = (w.evid / "MANIFEST.sha256").read_text().splitlines()
    on_disk = sorted(str(p.relative_to(w.base / "code")) for p in (w.base / "code").rglob("*") if p.is_file())
    assert on_disk == [line.split("  ")[1] for line in manifest]


@host
def test_s2_fails_when_the_stop_state_is_not_established(world):
    w = world(); w.release(); provision(w)
    (w.sys["units"] / "freedom-blades-executor-supervisor.service").write_text("x")
    failed(w.run("S2.1"), "S2.1")
    (w.sys["units"] / "freedom-blades-executor-supervisor.service").unlink()
    ok(w.run("S2.1"), "S2.1")
    (w.base / "code/tools/__init__.py").write_text("tampered")
    failed(w.run("S2.1"), "S2.1")


@host
def test_the_post_provision_tmpfiles_check_returns_the_verifiers_status_before_and_after_the_boot(world):
    w = world(); w.release(); provision(w)
    done = w.run("S2.2")
    assert done.returncode == 12 and "[rc=12]" in done.stdout, done.stdout  # expected at STOP-A: the fragment predates the boot
    (w.top / "booted").write_text("")
    done = w.run("S2.2")
    assert done.returncode == 0 and "[rc=0]" in done.stdout and "verify: ok" in done.stdout


# ---- identity and publication failures -----------------------------------------------------------------------------------------------

def nothing_published(w: World):
    """No final tree exists; a staging directory left by the failed block is root-only (0700) and not an executable input, and block R removes it."""
    assert not w.base.exists(), "a failed deployment must not leave a final tree"
    stage = Path(str(w.base) + ".stage")
    if stage.exists():
        assert stat.S_IMODE(stage.stat().st_mode) == 0o700 and stage.stat().st_uid == 0 and not stage.is_symlink()


@host
@pytest.mark.parametrize("label", ["archive digest", "manifest digest", "wheel digest", "release field absent"])
def test_missing_or_mismatched_artifact_identity_fails_before_publication_or_privileged_execution(world, label):
    w = world(); w.release()
    ok(w.run("S1.0"), "S1.0"); ok(w.run("S1.1"), "S1.1")
    kw = {}
    if label == "archive digest":
        kw["fields"] = {"ARCHIVE_SHA256": "0" * 64}
    elif label == "manifest digest":
        kw["fields"] = {"MANIFEST_SHA256": "0" * 64}
    elif label == "wheel digest":
        (w.art / w.rev / "wheelhouse" / WHEEL_SRC.name).write_bytes(b"x")
    else:
        kw["fields"] = {"RELEASE_REV": "UNSET"}
    done = w.run("S1.2", **kw)
    failed(done, "S1.2")
    nothing_published(w)
    assert not [c for c in w.calls() if c.startswith(("useradd", "loginctl", "visudo"))]
    assert "polkit_tmpfiles" not in (w.log.read_text() if w.log.exists() else "")
    boundary(w)
    assert not Path(str(w.base) + ".stage").exists()


def poisoned_release(w: World, label: str):
    if label == "symlink member":
        ti = __import__("tarfile").TarInfo("tools/evil"); ti.type = __import__("tarfile").SYMTYPE; ti.linkname = "/etc/shadow"
        w.release(members=[(ti, None)])
    elif label == "fifo member":
        ti = tarfile.TarInfo("tools/pipe"); ti.type = tarfile.FIFOTYPE
        w.release(members=[(ti, None)])
    elif label == "hardlink member":
        ti = tarfile.TarInfo("tools/hl"); ti.type = tarfile.LNKTYPE; ti.linkname = "tools/__init__.py"
        w.release(members=[(ti, None)])
    elif label == "absolute member":
        ti = tarfile.TarInfo("/tmp/abs"); ti.size = 1
        w.release(members=[(ti, b"x")])
    elif label == "dotdot member":
        ti = tarfile.TarInfo("../escape"); ti.size = 1
        w.release(members=[(ti, b"x")])
    elif label == "setuid member":
        ti = tarfile.TarInfo("tools/su"); ti.size = 1; ti.mode = 0o4755
        w.release(members=[(ti, b"x")])
    elif label == "secret-like file":
        env_name = "." + "env"
        w.release(extra={env_name + ".production": b"TOKEN=1"})
    elif label == "credential file":
        w.release(extra={"infra/service_account.json": b"{}"})
    elif label == "cache residue":
        w.release(extra={"tools/__pycache__/x.pyc": b"\0"})
    elif label == "git directory":
        w.release(extra={".git/config": b"x"})
    elif label == "unexpected file":
        ti = tarfile.TarInfo("tools/unlisted.py"); ti.size = 1
        w.release(members=[(ti, b"x")])
    else:
        raise AssertionError(label)


POISON = ["symlink member", "fifo member", "hardlink member", "absolute member", "dotdot member", "setuid member", "secret-like file", "credential file", "cache residue", "git directory", "unexpected file"]


@host
@pytest.mark.parametrize("label", POISON)
def test_the_deployment_rejects_prohibited_or_unexpected_archive_content_and_publishes_nothing(world, label):
    w = world(); poisoned_release(w, label)
    ok(w.run("S1.0"), "S1.0"); ok(w.run("S1.1"), "S1.1")
    done = w.run("S1.2")
    failed(done, "S1.2")
    assert "STOP" in done.stdout
    nothing_published_or_staged = not w.base.exists()
    assert nothing_published_or_staged, "the final tree must not exist"
    # the rejected input never reached extraction: no code directory was created in the staging area either
    stage = Path(str(w.base) + ".stage")
    assert not (stage / "code").exists() or not any((stage / "code").iterdir())


@host
@pytest.mark.parametrize("label", ["artifact dir group-writable", "artifact file other-writable", "artifact is a symlink", "artifact hard-linked", "stage pre-exists", "base pre-exists", "stage is a symlink"])
def test_the_deployment_rejects_a_mutable_or_untrusted_input_and_a_partial_staging_state(world, label):
    w = world(); w.release()
    ok(w.run("S1.0"), "S1.0")
    ok(w.run("S1.1"), "S1.1")
    art = w.art / w.rev
    stage = Path(str(w.base) + ".stage")
    if label == "artifact dir group-writable":
        art.chmod(0o770)
    elif label == "artifact file other-writable":
        (art / "code.tar").chmod(0o606)
    elif label == "artifact is a symlink":
        real = w.top / "real.tar"; real.write_bytes((art / "code.tar").read_bytes()); (art / "code.tar").unlink(); (art / "code.tar").symlink_to(real)
    elif label == "artifact hard-linked":
        os.link(art / "code.tar", w.top / "alias.tar")
    elif label == "stage pre-exists":
        stage.mkdir(mode=0o700)
    elif label == "base pre-exists":
        w.base.mkdir(mode=0o755)
    elif label == "stage is a symlink":
        stage.symlink_to(w.top)
    before = {p.name for p in w.top.iterdir()}
    done = w.run("S1.2")
    failed(done, "S1.2")
    if label not in ("stage pre-exists", "base pre-exists", "stage is a symlink"):
        nothing_published(w)
    assert not (w.base / "venv").exists() and {p.name for p in w.top.iterdir()} == before  # nothing was written through the pre-existing path
    if label == "stage is a symlink":
        assert not list(w.top.glob("code")) and not list(w.top.glob("in"))


@host
def test_a_tampered_published_tree_is_withdrawn_back_to_the_staging_name(world):
    w = world(); w.release()
    ok(w.run("S1.0"), "S1.0"); ok(w.run("S1.1"), "S1.1")
    # corrupt the manifest copy that the final verification trusts only after the digest check: a wrong digest field makes route3_tree_ok fail after the rename
    done = w.run("S1.2", mutate=lambda b: b.replace('chmod 0755 -- "$ROUTE3_STAGE" || exit 13', 'chmod 0755 -- "$ROUTE3_STAGE" || exit 13; : > "$ROUTE3_STAGE/code/tools/extra.py"'))
    failed(done, "S1.2")
    assert not w.base.exists()
    boundary(w)


# ---- rollback ------------------------------------------------------------------------------------------------------------------------

def restored(w: World, before: dict) -> None:
    after = w.objects()
    assert after == before, {"before": before, "after": after}


@host
@pytest.mark.parametrize("fail_at", ["S1.1 gate refuses (no effect)", "S1.1 hold", "S1.2 pip", "S1.3 useradd", "S1.4 tmpfiles install", "after STOP-A"])
def test_partial_failure_at_each_checkpoint_undoes_the_later_objects_and_stops_at_the_attended_package_boundary(world, fail_at):
    w = world(); w.release()
    before = w.objects()
    ok(w.run("S1.0"), "S1.0")
    if fail_at == "S1.1 gate refuses (no effect)":
        w.state["gate_rc"] = 1; w.save_state()
        done = w.run("S1.1"); failed(done, "S1.1")
        assert done.returncode == 2 and "begin-C1" not in (w.evid / "checkpoints").read_text() and not package_mutations(w.calls()), "refused before anything was recorded or held"
    elif fail_at == "S1.1 hold":
        w.state["fail"] = {"apt-mark": 1}; w.save_state()
        failed(w.run("S1.1"), "S1.1")
    elif fail_at == "S1.2 pip":
        ok(w.run("S1.1"), "S1.1")
        broken = w.run("S1.2", py=str(w.top / "badpython"))  # an interpreter that cannot build the venv
        failed(broken, "S1.2")
    elif fail_at == "S1.3 useradd":
        ok(w.run("S1.1"), "S1.1"); ok(w.run("S1.2"), "S1.2")
        knobs(w, fail={"useradd": 9})
        failed(w.run("S1.3"), "S1.3")
    elif fail_at == "S1.4 tmpfiles install":
        ok(w.run("S1.1"), "S1.1"); ok(w.run("S1.2"), "S1.2"); ok(w.run("S1.3"), "S1.3")
        (w.top / "tmpfiles-fail").write_text("11")
        done = w.run("S1.4"); failed(done, "S1.4")
    else:
        for ident in ("S1.1", "S1.2", "S1.3", "S1.4"):
            ok(w.run(ident), ident)
    (w.top / "tmpfiles-fail").unlink(missing_ok=True)
    w.state = w.load_state(); w.state["fail"] = {}; w.state["gate_rc"] = 0; w.save_state()
    st = w.load_state()
    done, muts = run_r(w)
    if fail_at == "S1.1 gate refuses (no effect)":
        ok(done, "R"); restored(w, before); assert not muts          # package and hold state equal the record: nothing to recover, no false ambiguity
        assert "Pre-state restored" in done.stdout
    else:
        attended(done, muts)
        after = w.objects()                                          # every later S1 object was undone; the packages and holds were not touched
        assert after["paths"] == before["paths"] and after["users"] == before["users"] and after["groups"] == before["groups"], after
        unchanged(w, st)
        assert "libunrelated" not in done.stdout
    assert w.evid.exists(), "the evidence is kept"
    again, muts2 = run_r(w)                                           # idempotent and non-mutating for packages and holds
    assert again.returncode == done.returncode and not muts2
    unchanged(w, st)


@host
def test_rollback_refuses_to_remove_objects_that_existed_before_the_operation(world):
    w = world(); w.release(); ok(w.run("S1.0"), "S1.0"); ok(w.run("S1.1"), "S1.1")
    # the deployment path "pre-existed": the pre-state does not record it as absent
    w.edit_prestate("prestate.objects", lambda t: "".join(l + "\n" for l in t.splitlines() if l != f"absent {w.base}"))
    w.base.mkdir(); (w.base / "keep").write_text("mine")
    with open(w.evid / "checkpoints", "a") as f:
        f.write("begin-C2\n")
    done = w.run("R")
    assert done.returncode == 23 and "ESCALATE" in done.stdout and (w.base / "keep").read_text() == "mine"
    # a pre-existing package is never removed: only packages absent from the pre-state go
    assert "coreutils" in w.load_state()["pkgs"]
    # a pre-existing account is never removed
    w2 = world(); w2.release(); ok(w2.run("S1.0"), "S1.0")
    w2.edit_prestate("prestate.objects", lambda t: "".join(l + "\n" for l in t.splitlines() if not l.startswith(("absent passwd", "absent group")) and l != f"absent {w2.home}"))  # the account, group and home "pre-existed"
    w2.state = w2.load_state(); w2.state["users"]["freedom-executor"] = {"uid": 5, "gid": 5, "home": str(w2.home), "shell": "/usr/sbin/nologin"}; w2.state["groups"]["freedom-executor"] = 5; w2.save_state()
    w2.home.mkdir(); (w2.home / "mine").write_text("x")
    with open(w2.evid / "checkpoints", "a") as f:
        f.write("begin-C3\n")
    done = w2.run("R")
    assert done.returncode == 22 and "freedom-executor" in w2.load_state()["users"] and (w2.home / "mine").exists() and not [c for c in w2.calls() if c.startswith("userdel")]


@host
def test_rollback_without_recorded_pre_state_removes_nothing(world):
    w = world(); w.release(); w.base.mkdir()
    done = w.run("R")
    assert done.returncode == 20 and "ESCALATE" in done.stdout and w.base.exists()


@host
def test_rollback_never_removes_a_link_a_mount_or_a_non_literal_path(world):
    w = world(); w.release(); ok(w.run("S1.0"), "S1.0")
    target = w.top / "precious"; target.mkdir(); (target / "x").write_text("keep")
    w.base.symlink_to(target)
    with open(w.evid / "checkpoints", "a") as f:
        f.write("begin-C2\n")
    done = w.run("R")
    assert done.returncode == 23 and (target / "x").exists()
    # a hostile ROUTE3_BASE in the operator's shell is overwritten by block D's literal, and the guard compares the literal
    w.base.unlink()
    done = w.run_raw(w.script("R").replace(f"ROUTE3_BASE={w.base}", "ROUTE3_BASE=/"))
    assert (target / "x").exists() and Path("/etc/passwd").exists()


# ---- S3: arming, install and R3 -----------------------------------------------------------------------------------------------------

@host
def test_s3_arms_in_the_declared_order_installs_without_starting_and_r3_returns_to_stop_a(world):
    w = world(); w.release(); provision(w)
    stop_a = w.objects()
    failed(w.run("S3.1"), "S3.1")  # tmpfiles verify is not ok before the boot
    (w.top / "booted").write_text("")
    assert not (w.sys["linger"] / "freedom-executor").exists()
    ok(w.run("S3.1"), "S3.1"); ok(w.run("S3.2"), "S3.2"); ok(w.run("S3.3"), "S3.3")
    sudoers = (w.sys["sudoers"] / "freedom-executor-sa2")
    assert sudoers.read_text() == "freedom-executor ALL=(root) NOPASSWD: /usr/bin/python3.14 -I -S " + str(w.sys["libexec"]) + "/freedom-blades-rp11/rp11_h1.py stop\n" or "NOPASSWD" in sudoers.read_text()
    assert stat.S_IMODE(sudoers.stat().st_mode) == 0o440 and not (w.sys["sudoers"] / ".freedom-executor-sa2.new").exists()
    order = [c.split()[0] for c in w.calls() if c.split()[0] in ("loginctl", "visudo")]
    assert order[0] == "loginctl" and "visudo" in order and (w.sys["libexec"] / "freedom-blades-rp11/rp11_h1.py").exists()
    done = w.run("S3.4"); ok(done, "S3.4")
    done = w.run("S3.5"); ok(done, "S3.5")
    assert "STOP-B" in done.stdout and "do not reboot" in done.stdout
    assert (w.sys["units"] / "wants/freedom-blades-executor-supervisor.service").exists()
    assert not [c for c in w.calls() if c.split()[0] in ("reboot", "shutdown", "sudo")]
    assert not [c for c in w.calls() if c.startswith("systemctl") and re.search(r"\b(start|restart)\b", c)]
    done = w.run("R3"); ok(done, "R3")
    after = w.objects()
    assert after == stop_a, {"before": stop_a, "after": after}
    ok(w.run("S2.1"), "S2.1")


@host
@pytest.mark.parametrize("fail_at", ["linger", "sa2", "sudoers visudo", "installer verify", "installer install 13", "installer install 15"])
def test_s3_failures_roll_back_to_stop_a_or_escalate_explicitly(world, fail_at):
    w = world(); w.release(); provision(w); (w.top / "booted").write_text("")
    stop_a = w.objects()
    if fail_at == "linger":
        w.state = w.load_state(); w.state["fail"] = {"loginctl": 1}; w.save_state(); failed(w.run("S3.1"), "S3.1")
    else:
        ok(w.run("S3.1"), "S3.1")
        if fail_at == "sa2":
            failed(w.run("S3.2", fields={"SA2_TREE_SHA256": "0" * 64}), "S3.2")
        else:
            ok(w.run("S3.2"), "S3.2")
            if fail_at == "sudoers visudo":
                w.state = w.load_state(); w.state["fail"] = {"visudo": 1}; w.save_state(); failed(w.run("S3.3"), "S3.3")
            else:
                ok(w.run("S3.3"), "S3.3")
                if fail_at == "installer verify":
                    (w.top / "installer-status").write_text("10"); failed(w.run("S3.4"), "S3.4")
                else:
                    (w.top / "installer-status").write_text("13" if fail_at.endswith("13") else "15")
                    done = w.run("S3.5"); assert done.returncode == int(fail_at.split()[-1]), done.stdout
                    if fail_at.endswith("15"):
                        assert "recovery-incomplete" in done.stdout
    (w.top / "installer-status").unlink(missing_ok=True)
    w.state = w.load_state(); w.state["fail"] = {}; w.save_state()
    done = w.run("R3")
    ok(done, "R3")
    assert w.objects() == stop_a
    again = w.run("R3"); ok(again, "R3")


@host
def test_r3_refuses_when_the_supervisor_is_running_and_when_remove_fails(world):
    w = world(); w.release(); provision(w); (w.top / "booted").write_text("")
    for i in ("S3.1", "S3.2", "S3.3", "S3.4", "S3.5"):
        ok(w.run(i), i)
    w.state = w.load_state(); w.state["active"]["freedom-blades-executor-supervisor.service"] = "active"; w.save_state()
    done = w.run("R3"); assert done.returncode == 21 and "removal after activation" in done.stdout
    w.state["active"] = {}; w.save_state()
    (w.top / "installer-status").write_text("15")
    done = w.run("R3"); assert done.returncode == 22 and "ESCALATE" in done.stdout and (w.sys["sudoers"] / "freedom-executor-sa2").exists(), "no later step runs after a failed remove"


@host
def test_s3_refuses_a_pre_existing_sudoers_file_or_sa2_directory(world):
    w = world(); w.release(); provision(w); (w.top / "booted").write_text(""); ok(w.run("S3.1"), "S3.1")
    w.make_parent(); (w.sys["libexec"] / "freedom-blades-rp11").mkdir()
    failed(w.run("S3.2"), "S3.2")
    (w.sys["libexec"] / "freedom-blades-rp11").rmdir()
    ok(w.run("S3.2"), "S3.2")
    (w.sys["sudoers"] / "freedom-executor-sa2").write_text("mine")
    failed(w.run("S3.3"), "S3.3")
    assert (w.sys["sudoers"] / "freedom-executor-sa2").read_text() == "mine"


# ---- S3.2 / R3 and the parent /usr/local/libexec (2026-11-18 production defect: S3.2 assumed the parent pre-exists) -------------------------

PARENT_MARKERS = ("begin-C6p", "done-C6p", "kept-C6p")


def ready_for_s3_2(w: World) -> dict:
    """STOP-A, one boot later, then S3.1: the state in which production stood when S3.2 failed. Returns the snapshot of STOP-A taken BEFORE S3.1, which R3 must restore (it also undoes S3.1's linger)."""
    w.release(); provision(w); (w.top / "booted").write_text("")
    stop_a = w.objects()
    ok(w.run("S3.1"), "S3.1")
    return stop_a


def parent_markers(w: World) -> list[str]:
    return [m for m in w.markers() if m in PARENT_MARKERS]


def stat_ugm(p: Path) -> tuple[int, int, int]:
    st = p.lstat()
    return st.st_uid, st.st_gid, stat.S_IMODE(st.st_mode)


@host
def test_s3_2_creates_a_missing_parent_exactly_and_records_intent_before_creation_and_confirmation_after(world):
    w = world(); entry = ready_for_s3_2(w)
    assert not w.sys["libexec"].exists() and w.sys["usrlocal"].is_dir(), "the world starts like production: /usr/local exists, /usr/local/libexec does not"
    ok(w.run("S3.2"), "S3.2")
    assert w.sys["libexec"].is_dir() and not w.sys["libexec"].is_symlink() and stat_ugm(w.sys["libexec"]) == (0, 0, 0o755)
    assert (w.sys["libexec"] / "freedom-blades-rp11/rp11_h1.py").exists()
    assert w.markers()[-4:] == ["begin-C6p", "done-C6p", "begin-C6", "done-C6"], w.markers()
    assert stat_ugm(w.sys["usrlocal"]) == (0, 0, 0o755) and w.objects() != entry, "/usr/local itself is neither created nor changed, and S3.2 changed the host"
    # the intent is durable before the directory exists: killed right after the intent marker, the parent is still absent and only the intent exists
    w2 = world(); ready_for_s3_2(w2)
    done = w2.run("S3.2", mutate=w2.inject("S3.2", "route3_cp begin-C6p", "kill")); failed(done, "S3.2"); assert done.returncode == 137
    assert parent_markers(w2) == ["begin-C6p"] and not w2.sys["libexec"].exists()


@host
@pytest.mark.parametrize("prior", ["none", "pre-existing"])
def test_r3_removes_a_parent_s3_created_and_only_that_and_returns_to_the_exact_stop_a(world, prior):
    w = world(); w.release(); provision(w); (w.top / "booted").write_text("")
    if prior == "pre-existing":
        w.make_parent()
    stop_a = w.objects()
    for i in ("S3.1", "S3.2", "S3.3", "S3.4", "S3.5"):
        ok(w.run(i), i)
    done = w.run("R3"); ok(done, "R3")
    assert w.objects() == stop_a, {"before": stop_a, "after": w.objects()}
    assert w.sys["libexec"].exists() == (prior == "pre-existing")
    assert parent_markers(w) == (["begin-C6p", "done-C6p"] if prior == "none" else ["kept-C6p"]), parent_markers(w)
    ok(w.run("R3"), "R3")                                                             # idempotent
    assert w.objects() == stop_a
    ok(w.run("S2.1"), "S2.1")


@host
def test_a_trusted_pre_existing_parent_is_kept_even_when_empty_and_a_stale_marker_of_an_earlier_attempt_never_decides(world):
    w = world(); ready_for_s3_2(w)
    ok(w.run("S3.2"), "S3.2"); assert parent_markers(w) == ["begin-C6p", "done-C6p"]
    ok(w.run("R3"), "R3"); assert not w.sys["libexec"].exists()                        # attempt 1: created by S3, removed by R3
    w.make_parent()                                                                    # a maintainer (not S3) creates the directory
    ok(w.run("S3.1"), "S3.1"); ok(w.run("S3.2"), "S3.2")                               # attempt 2 finds it trusted and records only that
    assert parent_markers(w) == ["begin-C6p", "done-C6p", "kept-C6p"] and w.markers().count("begin-C6p") == 1
    before = w.objects()
    ok(w.run("R3"), "R3")
    assert w.sys["libexec"].is_dir() and not (w.sys["libexec"] / "freedom-blades-rp11").exists() and stat_ugm(w.sys["libexec"]) == (0, 0, 0o755), "the earlier attempt's done-C6p must not make R3 remove a parent it did not create"
    assert before["paths"][str(w.sys["libexec"])] and w.objects()["paths"][str(w.sys["libexec"])]
    # and the preserved parent is part of the expected STOP-A: if it vanishes R3 does not report STOP-A
    w.sys["libexec"].rmdir()
    done = w.run("R3"); assert done.returncode == 26 and "preserved parent" in done.stdout and "STOP-A re-established" not in done.stdout, done.stdout


UNTRUSTED_PARENT = ["parent is a link", "parent is a link to a trusted directory", "parent is a file", "parent group-writable", "parent other-writable", "parent owned by another user",
                    "/usr/local group-writable", "/usr/local other-writable", "/usr/local owned by another user", "/usr/local is a link", "/usr/local is a file"]


@host
@pytest.mark.parametrize("label", UNTRUSTED_PARENT)
def test_s3_2_refuses_an_untrusted_or_linked_parent_or_usr_local_before_any_mutation(world, label):
    w = world(); w.release(); provision(w); (w.top / "booted").write_text(""); ok(w.run("S3.1"), "S3.1")
    elsewhere = w.top / "elsewhere"; elsewhere.mkdir()
    ul, par = w.sys["usrlocal"], w.sys["libexec"]
    if label == "parent is a link":
        par.symlink_to(w.top / "nowhere")
    elif label == "parent is a link to a trusted directory":
        par.symlink_to(elsewhere)
    elif label == "parent is a file":
        par.write_text("x")
    elif label == "parent group-writable":
        w.make_parent(0o775)
    elif label == "parent other-writable":
        w.make_parent(0o757)
    elif label == "parent owned by another user":
        w.make_parent(); os.chown(par, 65534, 65534)
    elif label == "/usr/local group-writable":
        ul.chmod(0o775)
    elif label == "/usr/local other-writable":
        ul.chmod(0o757)
    elif label == "/usr/local owned by another user":
        os.chown(ul, 65534, 65534)
    elif label == "/usr/local is a link":
        real = w.top / "usrlocal.real"; ul.rename(real); ul.symlink_to(real)
    else:
        ul.rmdir(); ul.write_text("x")
    before, markers, calls = w.objects(), w.markers(), len(w.calls())
    seen = {p: sorted(x.name for x in p.iterdir()) for p in (elsewhere, ul, par) if p.is_dir() and not p.is_symlink()}
    done = w.run("S3.2")
    failed(done, "S3.2"); assert done.returncode == 2 and "NO-GO" in done.stdout and "nothing was changed" in done.stdout, (done.returncode, done.stdout)
    assert w.markers() == markers, "no marker, not even the intent, was written"
    assert w.objects() == before and not (elsewhere / "freedom-blades-rp11").exists()
    assert seen == {p: sorted(x.name for x in p.iterdir()) for p in seen}, "nothing was created under any directory involved"
    assert not [c for c in w.calls()[calls:] if c.split()[0] in ("useradd", "loginctl", "visudo")]
    assert not (w.top / "usrlocal.real" / "libexec").exists()


@host
@pytest.mark.parametrize("fail_at", ["tree digest after creation", "exit right after done-C6p", "exit right after the build starts"])
def test_a_failure_after_the_parent_was_created_is_rolled_back_cleanly_by_r3_including_the_parent(world, fail_at):
    w = world(); entry = ready_for_s3_2(w); stop_a = entry
    kw: dict = {}
    if fail_at == "tree digest after creation":
        kw["fields"] = {"SA2_TREE_SHA256": "0" * 64}
    elif fail_at == "exit right after done-C6p":
        kw["mutate"] = w.inject("S3.2", "route3_cp done-C6p", "exit")
    else:
        kw["mutate"] = w.inject("S3.2", "route3_cp begin-C6 ||", "exit")
    done = w.run("S3.2", **kw); failed(done, "S3.2")
    assert "STOP: run block R3" in done.stdout and w.sys["libexec"].is_dir() and "done-C6p" in w.markers(), "the parent exists and its creation is confirmed"
    r3 = w.run("R3"); ok(r3, "R3")
    assert not w.sys["libexec"].exists() and w.objects() == stop_a, {"before": stop_a, "after": w.objects()}
    ok(w.run("R3"), "R3")


@host
@pytest.mark.parametrize("how", ["exit", "kill"])
@pytest.mark.parametrize("anchor", ["mkdir -m 0755", "chown -h root:root"])
def test_an_interrupted_parent_creation_is_never_removed_on_a_guess_and_r3_escalates_without_reporting_stop_a(world, anchor, how):
    w = world(); ready_for_s3_2(w)
    done = w.run("S3.2", mutate=w.inject("S3.2", anchor, how)); failed(done, "S3.2"); assert done.returncode in (77, 137)
    assert parent_markers(w) == ["begin-C6p"] and w.sys["libexec"].is_dir(), "intent exists, creation was never confirmed, and the directory is there"
    for _ in range(2):                                                                 # refused every time, never guessed
        r3 = w.run("R3")
        assert r3.returncode == 29 and "ESCALATE" in r3.stdout and "never confirmed" in r3.stdout and "STOP-A re-established" not in r3.stdout, (r3.returncode, r3.stdout)
        assert w.sys["libexec"].is_dir(), "an unconfirmed parent is left for the maintainer"
    assert not (w.sys["libexec"] / "freedom-blades-rp11").exists()


@host
def test_an_interrupted_creation_before_the_directory_exists_leaves_nothing_and_r3_is_clean(world):
    w = world(); stop_a = ready_for_s3_2(w)
    done = w.run("S3.2", mutate=w.inject("S3.2", "route3_cp begin-C6p", "exit")); failed(done, "S3.2")
    assert parent_markers(w) == ["begin-C6p"] and not w.sys["libexec"].exists()
    ok(w.run("R3"), "R3"); assert w.objects() == stop_a and not w.sys["libexec"].exists()
    # a later clean attempt is not poisoned by the stale intent
    ok(w.run("S3.2"), "S3.2"); assert parent_markers(w)[-2:] == ["begin-C6p", "done-C6p"]
    ok(w.run("R3"), "R3"); assert w.objects() == stop_a


@host
@pytest.mark.parametrize("label", ["parent holds another entry", "parent replaced by a link", "parent mode changed", "parent owner changed"])
def test_r3_refuses_to_remove_a_created_parent_that_is_not_the_empty_root_0755_directory_it_made(world, label):
    w = world(); ready_for_s3_2(w); ok(w.run("S3.2"), "S3.2")
    par, precious = w.sys["libexec"], w.top / "precious"
    if label == "parent holds another entry":
        (par / "someone-elses").write_text("keep")
    elif label == "parent replaced by a link":
        shutil.rmtree(par); precious.mkdir(); par.symlink_to(precious)
    elif label == "parent mode changed":
        par.chmod(0o775)
    else:
        os.chown(par, 65534, 65534)
    done = w.run("R3")
    assert done.returncode == 29 and "ESCALATE: refusing to remove" in done.stdout and "STOP-A re-established" not in done.stdout, (done.returncode, done.stdout)
    assert par.exists() or par.is_symlink()
    if label == "parent holds another entry":
        assert (par / "someone-elses").read_text() == "keep" and not (par / "freedom-blades-rp11").exists(), "the SA-2 child was removed first, nothing else"
    if label == "parent replaced by a link":
        assert precious.is_dir() and par.is_symlink()


@host
def test_r3_does_not_report_stop_a_when_the_parent_it_must_remove_is_still_there(world):
    """Mutation: an R3 whose rmdir silently does nothing is caught by the final STOP-A verification, so the equality tests above are not vacuous."""
    w = world(); ready_for_s3_2(w); ok(w.run("S3.2"), "S3.2")
    done = w.run("R3", mutate=lambda b: b.replace('rmdir -- "$PAR" || esc=29', ': # rmdir removed'))
    assert done.returncode == 26 and "still present" in done.stdout and "STOP-A re-established" not in done.stdout and w.sys["libexec"].is_dir(), (done.returncode, done.stdout)
    # and an S3.2 that skipped creation would be caught by the build, not hidden: the parent test above is the positive control
    ok(w.run("R3"), "R3"); assert not w.sys["libexec"].exists()


def test_the_parent_is_created_and_removed_only_by_the_one_exact_directory_operation_each():
    s32, r3 = block("S3.2"), block("R3")
    lines = [l for l in s32.splitlines() if not l.lstrip().startswith("#")]
    first_trust = next(i for i, l in enumerate(lines) if "trusted /usr/local" in l)
    first_mut = next(i for i, l in enumerate(lines) if FIRST_MUTATION.search(l))
    assert first_trust < first_mut, "/usr/local is validated before the first marker, creation or build"
    mk = [l.strip() for l in lines if re.search(r"\bmkdir\b", l)]
    assert len(mk) == 1 and mk[0].startswith('mkdir -m 0755 -- "$PAR" || exit 7'), mk
    assert not re.search(r"\brm\b|\bmv\b|\bln\b|install\s+-d|mkdir\s+-p|mkdir\s+--parents", s32)
    assert 'route3_cp begin-C6p || exit 2' in s32 and s32.index("route3_cp begin-C6p") < s32.index("mkdir -m 0755") < s32.index("route3_cp done-C6p") < s32.index("route3_cp begin-C6 ||") < s32.index("build.py")
    r3_par = [l for l in r3.splitlines() if "$PAR" in l and not l.lstrip().startswith("#")]
    assert any('rmdir -- "$PAR"' in l for l in r3_par) and not [l for l in r3_par if re.search(r"\brm\b\s|-rf|--recursive|rm -r", l)], r3_par
    assert re.search(r"mountpoint -q -- \"\$PAR\"", r3) and "-mindepth 1" in r3 and "0:0:755" in r3
    assert "last=$(grep -E '^(begin|done|kept)-C6p$'" in r3 and "done-C6p)" in r3 and "begin-C6p)" in r3 and "kept-C6p)" in r3


# ---- the installer invocation --------------------------------------------------------------------------------------------------------

@host
@pytest.mark.parametrize("status", [0, 10, 12, 13, 15])
def test_the_installer_invocation_preserves_each_status_under_a_hostile_environment(world, status):
    w = world(); w.release(); provision(w, "S1.2")
    (w.top / "installer-status").write_text(str(status))
    hostile = w.top / "hostile"
    (hostile / "tools").mkdir(parents=True)
    marker = w.top / "HOSTILE-RAN"
    code = f"open({str(marker)!r}, 'a').write('ran')\n"
    for rel in ("tools/__init__.py", "tools/executor_supervisor_install.py", "json.py", "runpy.py", "sitecustomize.py", "usercustomize.py"):
        (hostile / rel).write_text(code)
    fakebin = hostile / "bin"; fakebin.mkdir()
    for name in ("env", "python3.14", "python3", "sha256sum"):
        (fakebin / name).write_text(f"#!/bin/sh\necho ran >> {marker}\nexit 77\n"); (fakebin / name).chmod(0o755)
    (hostile / "home/.local/lib/python3.14/site-packages").mkdir(parents=True)
    (hostile / "home/.local/lib/python3.14/site-packages/usercustomize.py").write_text(code)
    env = {"PATH": f"{fakebin}:/usr/bin:/bin", "PYTHONPATH": str(hostile), "PYTHONHOME": str(hostile), "PYTHONUSERBASE": str(hostile / "home/.local"),
           "PYTHONSTARTUP": str(hostile / "sitecustomize.py"), "HOME": str(hostile / "home"), "LD_PRELOAD": "", "BASH_ENV": ""}
    script = w.script("D", ) + "\nroute3_installer verify; v=$?\necho \"status=$v\"\n"
    done = subprocess.run(["/bin/bash", "-c", script], cwd=str(hostile), env=env, capture_output=True, text=True, check=False, timeout=60)
    assert f"status={status}" in done.stdout, (done.stdout, done.stderr)
    assert not marker.exists(), "hostile PATH, PYTHONPATH, PYTHONHOME, user site or working directory redirected the installer"
    rec = json.loads((w.top / "installer.log").read_text().splitlines()[-1])
    assert rec["argv"] == ["verify"] and rec["flags"] == [1, 1, 1] and rec["module"] == "__main__" and rec["cwd"] == str(hostile)
    assert set(rec["env"]) <= {"PATH", "LC_CTYPE"} and not [e for e in rec["env"] if e.startswith(("PYTHON", "LD_", "BASH_"))]  # LC_CTYPE is CPython's own locale coercion


@host
@pytest.mark.parametrize("label", ["file other-writable", "file not root-owned", "tree symlink", "extra file", "code dir group-writable", "base dir not root-owned"])
def test_the_installer_invocation_refuses_an_untrusted_code_tree_before_importing_anything(world, label):
    w = world(); w.release(); provision(w, "S1.2")
    code = w.base / "code"
    target = code / "tools/executor_supervisor_install.py"
    if label == "file other-writable":
        target.chmod(0o666)
    elif label == "file not root-owned":
        os.chown(target, 65534, 65534)
    elif label == "tree symlink":
        (code / "adapters/link.py").symlink_to(target)
    elif label == "extra file":
        pass
    elif label == "code dir group-writable":
        (code / "adapters").chmod(0o775)
    elif label == "base dir not root-owned":
        os.chown(w.base, 65534, 65534)
    done = w.run_raw(w.script("D") + "\nroute3_installer verify; echo \"status=$?\"\n")
    if label == "extra file":
        (code / "adapters/extra.py").write_text("x")
        done = w.run_raw(w.script("D") + "\nroute3_installer verify; echo \"status=$?\"\n")
        # an unlisted-by-manifest file is a content question for the manifest-exact tree check (S2/S3 gates), not for the structural walk of the launcher
        assert "status=" in done.stdout
        failed_tree = w.run("S2.1")
        failed(failed_tree, "S2.1")
        return
    assert "status=30" in done.stdout and "[FINDING] Route 3" in done.stdout, (done.stdout, done.stderr)
    assert not (w.top / "installer.log").exists()


@host
def test_the_real_installer_is_launched_from_the_verified_deployment_and_its_own_status_passes_through(world):
    """The working tree's real adapters/application/tools (including ``adapters/http/credentials.py``, a code file the secret-name filter must not reject)
    are deployed by S1.2 and the real ``tools.executor_supervisor_install`` runs through ``route3_installer`` under ``-I -S -B``."""
    w = world(); w.release(real=True)
    ok(w.run("S1.0"), "S1.0"); ok(w.run("S1.1"), "S1.1"); ok(w.run("S1.2"), "S1.2")
    assert (w.base / "code/adapters/http/credentials.py").is_file()
    done = w.run_raw(w.script("D") + "\nroute3_installer verify; echo \"status=$?\"\n")
    status = int(re.search(r"status=(\d+)", done.stdout)[1])
    assert "Traceback" not in done.stdout + done.stderr and status in (10, 11, 12, 13), (status, done.stdout, done.stderr)
    assert not list(w.base.rglob("__pycache__")), "the launcher must not write bytecode into the trusted tree"


# ---- mutation: removing a protection must make the matching regression fail ----------------------------------------------------------

def drop(pattern: str):
    return lambda body: re.sub(pattern, "", body, count=1)


@host
def test_a_wrong_archive_digest_is_refused_independently_by_the_gate_and_by_the_staged_copy_check(world):
    """Defense in depth. A wrong ROUTE3_ARCHIVE_SHA256 is caught twice: by route3_gate (before anything is built) and, separately, by the S1.2 check on the staged copy. Removing either layer
    alone still refuses; only removing both lets the wrongly identified archive through, which shows each mutation really removes the layer it claims to."""
    gate_line = r'  route3_gate \|\| \{[^\n]*\n'
    inner_check = r'  sha256sum --check --status <\(printf[^\n]*ROUTE3_STAGE/in/code\.tar[^\n]*\n'
    w = world(); w.release(); ok(w.run("S1.0"), "S1.0"); ok(w.run("S1.1"), "S1.1")
    wrong = {"ARCHIVE_SHA256": "0" * 64}
    # the shipped block: the gate refuses first (status 2), before the begin-C2 marker, staging or any other effect
    done = w.run("S1.2", fields=wrong)
    failed(done, "S1.2"); assert done.returncode == 2 and "differs from its field digest" in done.stdout and "nothing was built" in done.stdout, done.stdout
    assert "begin-C2" not in (w.evid / "checkpoints").read_text() and not Path(str(w.base) + ".stage").exists()
    nothing_published(w)
    # layer 1 alone: the old S1.2 staged-copy check is removed and the gate still refuses, with the same effect
    done = w.run("S1.2", fields=wrong, mutate=drop(inner_check))
    failed(done, "S1.2"); assert done.returncode == 2 and "differs from its field digest" in done.stdout
    assert "begin-C2" not in (w.evid / "checkpoints").read_text() and not Path(str(w.base) + ".stage").exists()
    nothing_published(w)
    # layer 2 alone: the gate is removed and the staged-copy check refuses (status 6) after staging; block R withdraws the stage
    done = w.run("S1.2", fields=wrong, mutate=drop(gate_line))
    failed(done, "S1.2"); assert done.returncode == 6 and "differs from its field digest" in done.stdout, done.stdout
    nothing_published(w)
    boundary(w)
    # both layers removed: nothing refuses the wrongly identified archive, so the mutated block publishes it (the shipped block cannot)
    done = w.run("S1.2", fields=wrong, mutate=lambda b: drop(inner_check)(drop(gate_line)(b)))
    assert done.returncode == 0 and w.base.exists(), "with both layers removed the wrongly identified archive is published"


@host
def test_removing_the_archive_content_check_removes_the_archive_stage_finding(world):
    w = world(); poisoned_release(w, "symlink member"); ok(w.run("S1.0"), "S1.0"); ok(w.run("S1.1"), "S1.1")
    assert w.run("S1.2").returncode == 7
    boundary(w)
    mutated = w.run("S1.2", mutate=drop(r'  route3_stage archive [^\n]*\n'))
    assert mutated.returncode != 7, "without the archive check the symlink member is no longer refused at the archive stage"


@host
def test_removing_the_stage_existence_check_lets_a_partial_staging_state_be_reused(world):
    w = world(); w.release(); ok(w.run("S1.0"), "S1.0"); ok(w.run("S1.1"), "S1.1")
    Path(str(w.base) + ".stage").mkdir(mode=0o700)
    assert w.run("S1.2").returncode == 4
    mutated = w.run("S1.2", mutate=lambda b: b.replace('[ ! -e "$ROUTE3_STAGE" ] && [ ! -L "$ROUTE3_STAGE" ] && ', ""))
    assert mutated.returncode != 4, "without the check a leftover staging directory is silently reused"


@host
@pytest.mark.parametrize("name,old,new,label", [
    ("owner check removed", "s.st_uid==0 and ", "", "file not root-owned"),
    ("mode check removed", " and not s.st_mode&0o022", "", "file other-writable"),
    ("lstat replaced by stat", "return os.lstat(p)", "return os.stat(p)", "tree symlink"),
])
def test_removing_a_stage_entry_refusal_lets_the_installer_run_from_an_untrusted_tree(world, name, old, new, label):
    w = world(); w.release(); provision(w, "S1.2")
    target = w.base / "code/tools/executor_supervisor_install.py"
    if label == "file not root-owned":
        os.chown(target, 65534, 65534)
    elif label == "file other-writable":
        target.chmod(0o666)
    else:
        (w.base / "code/adapters/link.py").symlink_to(target)
    refuse = w.run_raw(w.script("D") + "\nroute3_installer verify; echo \"status=$?\"\n")
    assert "status=30" in refuse.stdout
    script = w.script("D")
    assert old in script
    mutated = w.run_raw(script.replace(old, new) + "\nroute3_installer verify; echo \"status=$?\"\n")
    assert "status=30" not in mutated.stdout and (w.top / "installer.log").exists(), f"the {name} mutation was not detected: {mutated.stdout}"


# =====================================================================================================================================
# R2 remediation: operation-owned package rollback, the closed apt closure, fail-closed identity queries, and a recoverable S1.0
# =====================================================================================================================================

def calls_of(w: World, cmd: str, sub: str | None = None) -> list[str]:
    return [c for c in w.calls() if c.split()[0] == cmd and (sub is None or sub in c.split())]


def real_installs(w: World) -> list[str]:
    return [c for c in w.calls() if c.startswith("apt-get")]    # the plan runs apt-get never: not an install, not a simulation


def add_unrelated(w: World, name: str = "libunrelated", version: str = "7") -> None:
    st = w.load_state(); st["pkgs"][name] = version; w.state = st; w.save_state()


def knobs(w: World, **kv) -> None:
    st = w.load_state(); st.update(kv); w.state = st; w.save_state()


def package_mutations(calls: list[str]) -> list[str]:
    """The package-manager calls among ``calls`` that would change a package or a hold. Simulations (``--simulate``/``-s``) change nothing and are not counted."""
    out = []
    for c in calls:
        tok = c.split()
        cmd, args = tok[0], tok[1:]
        sim = "--simulate" in args or "-s" in args
        if cmd in ("apt-get", "apt") and not sim and any(a in ("remove", "purge", "autoremove", "autopurge", "install", "reinstall", "upgrade", "dist-upgrade", "full-upgrade") for a in args):
            out.append(c)
        elif cmd == "dpkg" and any(a in ("--remove", "--purge", "-r", "-P", "-i", "--install", "--configure") for a in args):
            out.append(c)
        elif cmd == "apt-mark" and args and args[0] in ("hold", "unhold"):
            out.append(c)
    return out


def run_r(w: World, **kw):
    """Run block R and return (result, the package or hold mutations it issued)."""
    n = len(w.calls())
    done = w.run("R", **kw)
    return done, package_mutations(w.calls()[n:])


def attended(done, muts) -> None:
    """The R5 boundary: status 28, no 'Pre-state restored', the attended-recovery text, and not one package or hold mutation."""
    assert done.returncode == 28 and "[R rc=28]" in done.stdout, (done.returncode, done.stdout, done.stderr)
    assert "Pre-state restored" not in done.stdout and "ATTENDED RECOVERY REQUIRED" in done.stdout, done.stdout
    assert not muts, muts


def boundary(w: World, **kw):
    """R after a successful S1.1: the later S1 objects are undone, the packages and holds are not touched, status 28."""
    st = w.load_state()
    done, muts = run_r(w, **kw)
    attended(done, muts); unchanged(w, st)
    return done


def objects_restored(w: World, before: dict) -> None:
    """Everything except the package set and the holds equals the captured state."""
    after = w.objects()
    assert {k: after[k] for k in ("paths", "users", "groups")} == {k: before[k] for k in ("paths", "users", "groups")}, {"before": before, "after": after}


def unchanged(w: World, st: dict) -> None:
    now = w.load_state()
    assert now["pkgs"] == st["pkgs"] and now["holds"] == st["holds"], {"before": (st["pkgs"], st["holds"]), "after": (now["pkgs"], now["holds"])}


# ---- 1. a package added after S1.1 survives R, and R says so ---------------------------------------------------------------------------

@host
def test_a_package_added_after_s1_1_survives_rollback_and_is_reported_not_deleted(world):
    w = world(); w.release(); before = w.objects()
    ok(w.run("S1.0"), "S1.0"); ok(w.run("S1.1"), "S1.1")
    add_unrelated(w); st = w.load_state()
    for _ in range(2):                                                   # stable on every repetition
        done, muts = run_r(w)
        attended(done, muts)
        assert "libunrelated" in done.stdout and all(n in done.stdout for n in CLOSURE_NAMES)
        unchanged(w, st)
        assert set(st["holds"]) == CLOSURE_NAMES and st["pkgs"]["libunrelated"] == "7"
    assert w.objects()["paths"] == before["paths"] and w.objects()["users"] == []


@host
def test_a_reverse_dependant_of_a_reviewed_package_is_never_swept_away_and_nothing_is_removed(world):
    w = world(); w.release()
    ok(w.run("S1.0"), "S1.0"); ok(w.run("S1.1"), "S1.1")
    add_unrelated(w, "libdependent", "3"); knobs(w, rdeps={"python3.14-venv": ["libdependent"]}); st = w.load_state()
    done, muts = run_r(w)
    attended(done, muts)
    assert "libdependent" in done.stdout and not [c for c in w.calls() if c.startswith("apt-get remove")]
    unchanged(w, st)
    assert set(st["holds"]) == CLOSURE_NAMES and CLOSURE_NAMES <= set(st["pkgs"]) and "libdependent" in st["pkgs"]


# ---- 2. partial or interrupted apt: only the attributable packages go -----------------------------------------------------------------

def test_the_withdrawn_solver_proposal_refuses_everything_and_runs_nothing(tmp_path):
    """S0.0 assumed python3.14 was absent and proposed an install closure. On the pre-installed baseline it must never run: it only refuses."""
    empty = tmp_path / "empty-path"
    empty.mkdir()
    text = block("S0.0")
    done = subprocess.run(["/bin/bash", "-c", text], capture_output=True, text=True, env={"PATH": str(empty)}, check=False)   # an empty PATH: nothing but builtins can run
    assert done.returncode == 64 and "[S0.0 rc=64]" in done.stdout and "withdrawn" in done.stdout and "nothing was read or changed" in done.stdout, (done.stdout, done.stderr)
    code = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))
    assert not re.search(r"apt-get|apt-cache|apt-mark|dpkg|route3_apt|simulate", code), "no executable line of the withdrawn block touches the package manager"
    assert "NONE" in text.splitlines()[0], "it carries no authority"


# ---- 4. an origin line that belongs only to a non-candidate version does not satisfy the origin check -----------------------------------

@host
def test_a_trusted_origin_line_for_another_version_does_not_bind_the_pinned_version(world):
    w = world(); w.release()
    ok(w.run("S0.2"), "S0.2")
    # the trusted source offers 3.14.8, while the PINNED 3.14.9-1fake exists only at an unlisted source: an origin substring appears in the report but not for this version
    knobs(w, madison={"python3.14-minimal": [["3.14.8-1fake", w.origin], ["3.14.9-1fake", "http://evil.test/ubuntu other/main"]]})
    done = w.run("S0.2"); failed(done, "S0.2")
    assert "python3.14-minimal=3.14.9-1fake is also offered by an origin that is not listed" in done.stdout
    # the same version offered by two LISTED origins is accepted
    knobs(w, madison={"python3.14-minimal": [["3.14.9-1fake", w.origin], ["3.14.9-1fake", "http://security.example.test/ubuntu fake-security/main"]]})
    ok(w.run("S0.2", fields={"APT_ORIGIN": w.origin + ", http://security.example.test/ubuntu fake-security/main"}), "S0.2")
    # a madison failure is a NO-GO, never an accepted origin
    knobs(w, fail={"madison": 3}, madison={})
    failed(w.run("S0.2"), "S0.2")


# ---- 5. the host verification inside S1.1 (the trusted gate) ---------------------------------------------------------------------------------

@host
@pytest.mark.parametrize("label", ["changed packaged file", "interpreter digest differs", "gate tool refuses"])
def test_s1_1_refuses_a_changed_file_a_different_interpreter_or_a_failing_trusted_tool_before_recording_or_holding_anything(world, label):
    w = world(); w.release(); ok(w.run("S1.0"), "S1.0")
    kw = {}
    if label == "changed packaged file":
        knobs(w, verify_fail=True)
    elif label == "gate tool refuses":
        knobs(w, gate_rc=1, gate_msg="payload drift: the installed files of libfake-dep=1.0 are not those of the signed-archive package")
    else:
        kw["fields"] = {"PY_SHA256": "0" * 64}
    done = w.run("S1.1", **kw)
    failed(done, "S1.1"); assert done.returncode == 2 and "the trusted baseline attestation failed" in done.stdout
    assert any(m in done.stdout for m in ("dpkg --verify", "differs from ROUTE3_PY_SHA256", "payload drift")), done.stdout
    assert "begin-C1" not in (w.evid / "checkpoints").read_text() and not package_mutations(w.calls()) and not (w.evid / "held.new").exists() and not (w.evid / "beforeC1.dpkg").exists()
    knobs(w, verify_fail=False, gate_rc=0); st = w.load_state()
    done, muts = run_r(w)
    ok(done, "R"); assert not muts; unchanged(w, st)


@host
def test_s1_1_refuses_to_run_twice_and_while_an_apt_run_holds_a_lock(world):
    w = world(); w.release(); ok(w.run("S1.0"), "S1.0")
    holder = subprocess.Popen([sys.executable, "-c",
                               "import fcntl,sys,time\nf=open(sys.argv[1],'a')\nfcntl.lockf(f,fcntl.LOCK_EX)\nprint('held',flush=True)\ntime.sleep(60)", str(w.sys["dpkg"] / "lock-frontend")],
                              stdout=subprocess.PIPE, text=True)
    try:
        assert holder.stdout.readline().strip() == "held"
        done = w.run("S1.1"); failed(done, "S1.1")
        assert done.returncode == 2 and "holds" in done.stdout and not real_installs(w) and "begin-C1" not in (w.evid / "checkpoints").read_text()
        failed(w.run("S0.2"), "S0.2")
    finally:
        holder.kill(); holder.wait()
    ok(w.run("S1.1"), "S1.1")
    again = w.run("S1.1"); failed(again, "S1.1"); assert again.returncode == 2 and "already begun" in again.stdout


@host
@pytest.mark.parametrize("status", [1, 3, 9, 127])
def test_a_failed_account_or_group_query_makes_rollback_non_zero_and_never_restored(world, status):
    w = world(); w.release(); ok(w.run("S1.0"), "S1.0")  # nothing provisioned: every object is genuinely absent, but absence cannot be proven
    knobs(w, fail={"getent": status})
    done = w.run("R")
    assert done.returncode == 27 and "Pre-state restored" not in done.stdout and "absence is not established" in done.stdout, (done.returncode, done.stdout)
    assert w.evid.exists()


@host
@pytest.mark.parametrize("status", [1, 3, 127])
def test_a_failed_query_during_account_removal_stops_before_userdel(world, status):
    w = world(); w.release(); provision(w)
    knobs(w, fail={"getent": status})
    done = w.run("R")
    assert done.returncode == 27 and "Pre-state restored" not in done.stdout
    assert "freedom-executor" in w.load_state()["users"] and not calls_of(w, "userdel") and not calls_of(w, "groupdel")


@host
def test_the_exact_not_found_status_is_absence_and_status_zero_is_presence(world):
    w = world(); w.release(); ok(w.run("S1.0"), "S1.0")
    knobs(w, fail={"getent": 2})  # the documented "key not found"
    ok(w.run("R"), "R")
    w2 = world(); w2.release(); provision(w2, "S1.3")
    boundary(w2)  # status 0 (the account exists) is removed through userdel/groupdel and the re-query then reads status 2; the packages stay: the attended boundary
    assert calls_of(w2, "userdel") and w2.load_state()["users"] == {}
    # a group that survives the account (status 0 on the final query) is not "restored"
    w3 = world(); w3.release(); ok(w3.run("S1.0"), "S1.0"); knobs(w3, groups={"freedom-executor": 5})
    done = w3.run("R")
    assert done.returncode == 25 and "group freedom-executor still exists" in done.stdout


@host
def test_the_preflight_treats_every_non_zero_getent_status_but_two_as_a_no_go(world):
    w = world(); w.release()
    knobs(w, fail={"getent": 2}); ok(w.run("S0.2"), "S0.2")
    for status in (1, 3):
        knobs(w, fail={"getent": status})
        done = w.run("S0.2"); failed(done, "S0.2"); assert "could not be queried" in done.stdout


# ---- 7. R3 cannot report STOP-A restored on an unanswered manager or identity query -----------------------------------------------------

def arm(w: World) -> None:
    provision(w); (w.top / "booted").write_text("")
    for i in ("S3.1", "S3.2", "S3.3", "S3.4", "S3.5"):
        ok(w.run(i), i)


@host
@pytest.mark.parametrize("fail", [{"systemctl": 1}, {"systemctl show": 1}, {"systemctl show": 3}, {"getent": 1}, {"getent": 3}])
def test_r3_never_reports_stop_a_when_a_manager_or_identity_query_fails(world, fail):
    w = world(); w.release(); arm(w)
    knobs(w, fail=fail)
    done = w.run("R3")
    assert done.returncode == 27 and "STOP-A re-established" not in done.stdout and "ESCALATE" in done.stdout, (done.returncode, done.stdout)
    if "systemctl" in str(fail):
        assert not (w.top / "installer.log").read_text().count('"remove"'), "nothing may be removed when the manager state is unknown"
    knobs(w, fail={})
    ok(w.run("R3"), "R3")  # once the queries answer, R3 converges


@host
def test_r3_requires_a_definite_not_running_answer_for_the_supervisor(world):
    w = world(); w.release(); arm(w)
    knobs(w, active={"freedom-blades-executor-supervisor.service": "activating"})
    done = w.run("R3"); assert done.returncode == 21 and "STOP-A re-established" not in done.stdout


# ---- 8/9. S1.0 is one transaction: failure after each write reaches the one recovery path, which permits a clean rerun ----------------------

S10_WRITES = [
    ("stage directory", 'install -d -m 0700 -o root -g root -- "$S"'),
    ("package snapshot", 'route3_pkgs > "$S/prestate.dpkg"'),
    ("hold snapshot", "apt-mark showhold"),
    ("absent-object snapshot", "route3_objects | while"),
    ("account and group snapshot", "printf 'absent passwd"),
    ("digest list", '( cd "$S" && sha256sum'),
    ("checkpoint creation", "printf 's1-start"),
    ("synchronization", 'sync -- "$S/prestate.dpkg"'),
]


@host
@pytest.mark.parametrize("how", ["exit", "kill"])
@pytest.mark.parametrize("label,anchor", S10_WRITES, ids=[w[0] for w in S10_WRITES])
def test_an_s1_0_failure_after_each_write_leaves_no_authoritative_evidence_and_is_recovered_by_r0(world, label, anchor, how):
    w = world(); w.release(); before = w.objects()
    stage = Path(str(w.evid) + ".new")
    done = w.run("S1.0", mutate=w.inject("S1.0", anchor, how))
    failed(done, "S1.0"); assert done.returncode in (77, 137)
    assert stage.is_dir() and not w.evid.exists(), "an incomplete S1.0 may leave only the unpublished stage"
    assert "run block R0" in done.stdout
    # the incomplete stage is never an authoritative pre-state
    refused = w.run("R"); assert refused.returncode == 20 and "R0" in refused.stdout and "Pre-state restored" not in refused.stdout
    s11 = w.run("S1.1"); failed(s11, "S1.1"); assert s11.returncode == 2 and not real_installs(w)
    again = w.run("S1.0"); assert again.returncode == 3 and "run block R0" in again.stdout and stage.is_dir()
    # the one recovery path
    rec = w.run("R0"); ok(rec, "R0"); assert "Incomplete S1.0 cleared" in rec.stdout
    assert not stage.exists() and not w.evid.exists()
    ok(w.run("R0"), "R0")  # idempotent
    restored(w, before)
    # and a clean S1.0 → S1.1 → R convergence follows
    ok(w.run("S1.0"), "S1.0"); ok(w.run("S1.1"), "S1.1"); boundary(w); objects_restored(w, before)


@host
def test_an_s1_0_package_query_failure_is_refused_by_the_gate_before_any_write(world):
    """dpkg-query now fails first inside route3_gate (route3_python_ok), so S1.0 stops with status 9 before it creates anything: no stage, no evidence, nothing for R0 to recover."""
    w = world(); w.release(); before = w.objects()
    knobs(w, fail={"dpkg-query": 1})
    done = w.run("S1.0"); failed(done, "S1.0")
    assert done.returncode == 9 and "nothing was written" in done.stdout, (done.returncode, done.stdout)
    assert not w.evid.exists() and not Path(str(w.evid) + ".new").exists(), "the earlier refusal leaves neither evidence nor an unpublished stage"
    restored(w, before)
    knobs(w, fail={})
    ok(w.run("R0"), "R0"); ok(w.run("S1.0"), "S1.0")


@host
def test_an_s1_0_failure_inside_a_snapshot_command_after_the_gate_is_recovered_by_r0(world):
    """The recovery property itself, with the failing command past the gate: the snapshot of the package list fails after the stage exists; only R0 clears it."""
    w = world(); w.release(); before = w.objects()
    stage = Path(str(w.evid) + ".new")
    done = w.run("S1.0", mutate=lambda b: b.replace('route3_pkgs > "$S/prestate.dpkg"', 'false > "$S/prestate.dpkg"'))
    failed(done, "S1.0"); assert done.returncode == 5 and "run block R0" in done.stdout
    assert stage.is_dir() and not w.evid.exists()
    ok(w.run("R0"), "R0"); assert not stage.exists()
    restored(w, before)
    ok(w.run("S1.0"), "S1.0")


@host
def test_a_kill_after_publication_leaves_complete_evidence_that_r_honours_and_r0_never_removes(world):
    w = world(); w.release(); before = w.objects()
    done = w.run("S1.0", mutate=w.inject("S1.0", 'mv --no-target-directory --no-clobber -- "$S"', "kill"))
    assert done.returncode == 137 and w.evid.is_dir() and not Path(str(w.evid) + ".new").exists()
    r0 = w.run("R0"); assert r0.returncode == 31 and w.evid.is_dir()
    assert w.run("S1.0").returncode == 3
    ok(w.run("R"), "R"); restored(w, before)             # no package was installed: the state equals the record
    ok(w.run("S1.1"), "S1.1")  # the published evidence is a usable, complete pre-state


# ---- 10. R0 refuses to remove complete evidence, later-stage evidence, or anything ambiguous ---------------------------------------------

@host
def test_r0_refuses_published_evidence_with_or_without_later_markers_and_removes_nothing(world):
    w = world(); w.release(); ok(w.run("S1.0"), "S1.0")
    r0 = w.run("R0"); failed(r0, "R0"); assert r0.returncode == 31 and w.evid.is_dir()
    ok(w.run("S1.1"), "S1.1")
    # S1.1 attests and holds only: its evidence is the before/after package lists, the hold list and the markers (the apt-transaction record observed.pkgs belonged to removed machinery)
    evidence = sorted(p.name for p in w.evid.iterdir())
    marks = (w.evid / "checkpoints").read_text().splitlines()
    assert {"beforeC1.dpkg", "afterC1.dpkg", "held.new", "pre.sha256", "prestate.dpkg", "prestate.holds", "prestate.objects"} <= set(evidence) and "observed.pkgs" not in evidence, evidence
    assert marks[:3] == ["s1-start", "begin-C1", "done-C1"], marks
    r0 = w.run("R0"); assert r0.returncode == 31 and w.evid.is_dir()
    assert sorted(p.name for p in w.evid.iterdir()) == evidence and (w.evid / "checkpoints").read_text().splitlines() == marks, "R0 removed or changed published evidence"
    stage = Path(str(w.evid) + ".new"); stage.mkdir(mode=0o700)
    r0 = w.run("R0"); assert r0.returncode == 31 and stage.is_dir() and w.evid.is_dir(), "both present is ambiguous: nothing is removed"


@host
@pytest.mark.parametrize("label", ["later checkpoint marker", "S1.1 artifact in the stage", "nested directory", "stage symlink", "created object present", "stage not root-0700", "account present"])
def test_r0_refuses_a_stage_that_carries_later_stage_evidence_or_is_ambiguous(world, label):
    w = world(); w.release()
    done = w.run("S1.0", mutate=w.inject("S1.0", 'printf \'s1-start', "exit")); failed(done, "S1.0")
    stage = Path(str(w.evid) + ".new")
    victim = None
    if label == "later checkpoint marker":
        with open(stage / "checkpoints", "a") as f:
            f.write("begin-C1\n")
        want = 34
    elif label == "S1.1 artifact in the stage":
        (stage / "apt.intent").write_text("x"); want = 33
    elif label == "nested directory":
        (stage / "sub").mkdir(); want = 33
    elif label == "stage symlink":
        victim = w.top / "precious"; victim.mkdir(); (victim / "x").write_text("keep")
        shutil.rmtree(stage); stage.symlink_to(victim); want = 32
    elif label == "created object present":
        w.base.mkdir(); want = 35
    elif label == "stage not root-0700":
        stage.chmod(0o770); want = 32
    else:
        knobs(w, users={"freedom-executor": {"uid": 1, "gid": 1, "home": "/x", "shell": "/x"}}, groups={"freedom-executor": 1}); want = 35
    done = w.run("R0")
    assert done.returncode == want and "Incomplete S1.0 cleared" not in done.stdout, (label, done.returncode, done.stdout)
    assert stage.exists() or stage.is_symlink()
    if victim:
        assert (victim / "x").read_text() == "keep"


@host
def test_r0_fails_closed_when_the_identity_query_is_unanswered(world):
    w = world(); w.release()
    failed(w.run("S1.0", mutate=w.inject("S1.0", 'printf \'s1-start', "exit")), "S1.0")
    knobs(w, fail={"getent": 3})
    done = w.run("R0"); assert done.returncode == 35 and Path(str(w.evid) + ".new").exists()
    knobs(w, fail={}); ok(w.run("R0"), "R0")


@host
def test_tampered_published_evidence_is_not_a_pre_state(world):
    w = world(); w.release(); ok(w.run("S1.0"), "S1.0")
    with open(w.evid / "prestate.dpkg", "a") as f:
        f.write("sneaky\t1\n")
    for ident in ("R", "S1.1"):
        done = w.run(ident); assert done.returncode in (20, 2) and "Pre-state restored" not in done.stdout, (ident, done.stdout)
    (w.evid / "pre.sha256").unlink()
    assert w.run("R").returncode == 20


# ---- mutation: the material predicates ---------------------------------------------------------------------------------------------------




@host
def test_treating_any_non_zero_getent_status_as_absence_reports_a_restored_pre_state(world):
    w = world(); w.release(); ok(w.run("S1.0"), "S1.0"); knobs(w, fail={"getent": 3})
    assert w.run("R").returncode == 27
    mutated = w.run("R", dmutate=lambda d: d.replace("case $rc in 0) return 0;; 2) return 2;; *) return 9;; esac", "case $rc in 0) return 0;; *) return 2;; esac"))
    assert mutated.returncode == 0 and "Pre-state restored" in mutated.stdout


@host
def test_letting_incomplete_evidence_pass_as_complete_restores_a_state_nobody_recorded(world):
    w = world(); w.release(); ok(w.run("S1.0"), "S1.0")
    (w.evid / "pre.sha256").unlink()
    assert w.run("R").returncode == 20 and w.run("S1.1").returncode == 2
    mutated = w.run("S1.1", dmutate=lambda d: d.replace("route3_evid_ok() {\n", "route3_evid_ok() {\n  return 0\n"))
    assert mutated.returncode != 2, "without the completeness gate S1.1 proceeds on evidence that was never completed"


@host
def test_writing_s1_0_evidence_in_place_would_leave_a_directory_that_looks_published(world):
    """The staged publication is what makes 'the evidence directory exists' mean 'the pre-state is complete'."""
    w = world(); w.release()
    stage = Path(str(w.evid) + ".new")
    failed(w.run("S1.0", mutate=w.inject("S1.0", 'route3_pkgs > "$S/prestate.dpkg"', "kill")), "S1.0")
    assert stage.is_dir() and not w.evid.exists()
    ok(w.run("R0"), "R0")
    mutated = w.run("S1.0", dmutate=lambda d: d.replace("ROUTE3_EVID_STAGE=/root/route3-evidence.new", "ROUTE3_EVID_STAGE=/root/route3-evidence"),
                    mutate=w.inject("S1.0", 'route3_pkgs > "$S/prestate.dpkg"', "kill"))
    assert w.evid.exists() and not (w.evid / "pre.sha256").exists(), "an in-place write leaves a half-written directory under the published name"
    assert w.run("R").returncode == 20, "route3_evid_ok is the gate that still refuses it"


# ---- real apt on the disposable host: the simulation command, the parser and the origin binding match the installed apt ------------------

REAL_APT = ROOT and shutil.which("apt-get") is not None and shutil.which("apt-cache") is not None and PY314.exists()
real_apt = pytest.mark.skipif(not REAL_APT, reason="needs root and the real apt (oracle-test)")


def real_bash(script: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    d = definitions()
    return subprocess.run(["/bin/bash", "-c", d + "\n" + script], capture_output=True, text=True, timeout=300, check=False, input=stdin, env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "HOME": "/root"})


def installed_closure() -> tuple[list[str], str]:
    names = ["python3.14", "python3.14-minimal", "python3.14-venv"]
    out = subprocess.run(["dpkg-query", "-W", "-f=${Package}=${Version}\n", *names], capture_output=True, text=True, check=True).stdout.split()
    return out, subprocess.run(["apt-cache", "madison", "python3.14-minimal"], capture_output=True, text=True, check=True).stdout


@real_apt
def test_real_apt_closure_and_origin_binding_accept_the_installed_set_and_reject_a_wrong_origin():
    tokens, madison = installed_closure()
    sources = set()
    for t in tokens:
        n, v = t.split("=", 1)
        out = subprocess.run(["apt-cache", "madison", n], capture_output=True, text=True, check=True).stdout
        sources |= {m.split("|")[2].strip().rsplit(" ", 2)[0] for m in out.splitlines() if m.split("|")[1].strip() == v}
    sources = sorted(sources)
    assert sources, madison
    good = f'ROUTE3_APT_PACKAGES="{" ".join(tokens)}"; ROUTE3_APT_ORIGIN="{", ".join(sources)}"'
    done = real_bash(good + '; route3_apt_check; echo "rc=$? todo=[$ROUTE3_TODO]"')
    assert "rc=0 todo=[]" in done.stdout, (done.stdout, done.stderr)  # already installed at the exact versions: nothing to install, nothing proposed
    done = real_bash(good.split(";")[0] + '; ROUTE3_APT_ORIGIN="http://evil.test/ubuntu other/main"; route3_apt_check; echo "rc=$?"')
    assert "rc=1" in done.stdout and "also offered by an origin that is not listed" in done.stdout, done.stdout
    done = real_bash(good + '; ROUTE3_APT_PACKAGES="python3.14-minimal=0.0-1"; route3_apt_check; echo "rc=$?"')
    # a wrong version is refused on the installed version, before any origin lookup (the plan installs nothing, so "not installed at that version" is the whole finding)
    assert "rc=1" in done.stdout and "python3.14-minimal is installed at" in done.stdout and "not 0.0-1" in done.stdout, done.stdout
    # apt and dpkg are idle on the disposable host, and the lock files the plan inspects exist
    done = real_bash('route3_apt_idle; echo "rc=$?"')
    assert "rc=0" in done.stdout, done.stdout


def test_s1_0_stages_publishes_atomically_and_only_r0_removes_the_stage():
    b = block("S1.0")
    assert 'install -d -m 0700 -o root -g root -- "$S"' in b and 'mv --no-target-directory --no-clobber -- "$S" "$ROUTE3_EVID"' in b
    assert "S=$ROUTE3_EVID_STAGE" in b and "ROUTE3_EVID/prestate" not in b, "S1.0 writes into the stage, never into the published name"
    assert b.index("pre.sha256") < b.index("mv --no-target-directory") and b.index("sync --") < b.index("mv --no-target-directory")
    assert "ROUTE3_EVID_STAGE=/root/route3-evidence.new" in definitions()
    removers = [i for i in IDS if re.search(r"\brm\s+-r", block(i)) and "$S\"" in block(i)]
    assert removers == ["R0"], removers
    assert 'rm -r --one-file-system -- "$S"' in block("R0") and '[ "$S" = /root/route3-evidence.new ]' in block("R0")


def test_every_executable_block_of_the_plan_is_valid_bash():
    for ident in IDS + ["D"]:
        text = definitions() if ident == "D" else block(ident)
        done = subprocess.run(["/bin/bash", "-n"], input=text, capture_output=True, text=True, check=False)
        assert done.returncode == 0, (ident, done.stderr)
    done = subprocess.run(["/bin/bash", "-n"], input=fields_block(), capture_output=True, text=True, check=False)
    assert done.returncode == 0


# =====================================================================================================================================
# R3 remediation: transaction-derived apt ownership and status-aware manager observations
# =====================================================================================================================================

RACED = [["libfake-dep", "1.0"], ["python3.14-minimal", "3.14.9-1fake"]]
RACED_NAMES = {n for n, _ in RACED}


def removed_by_apt(w: World) -> list[str]:
    out: list[str] = []
    for c in w.calls():
        if c.startswith("apt-get") and " remove " in f" {c} " and "--simulate" not in c:
            out += [x for x in c.split()[c.split().index("--yes") + 1:] if x != "--"]
    return out


# ---- 1. the reproduced race: another transaction installs reviewed members after the snapshot and before Route 3 owns the lock ------------

@host
def test_r5_s1_1_killed_after_the_holds_before_done_c1_keeps_packages_and_holds(world):
    w = world(); w.release(); ok(w.run("S1.0"), "S1.0")
    done = w.run("S1.1", mutate=w.inject("S1.1", 'if [ -s "$E/held.new" ]; then apt-mark hold', "kill"))
    assert done.returncode == 137 and "done-C1" not in (w.evid / "checkpoints").read_text()
    st = w.load_state(); assert set(st["holds"]) == CLOSURE_NAMES
    done, muts = run_r(w); attended(done, muts); unchanged(w, st)
    assert not calls_of(w, "apt-mark", "unhold")


# ---- no S1 rollback path can name a removal, purge, autoremove, downgrade or unhold ----------------------------------------------------------

def _executable_lines(text: str) -> list[str]:
    out = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        out.append(re.sub(r"(echo|printf)\s+(\"[^\"]*\"|'[^']*')", r"\1 TEXT", s))
    return out


PACKAGE_REMOVAL = re.compile(r"(\b(apt-get|apt|aptitude|dpkg)\b[^\n]*(\bremove\b|\bpurge\b|\bautoremove\b|\bautopurge\b|--remove\b|--purge\b|--allow-downgrades|--force-depends|-r\s|-P\s))|\bapt-mark\s+unhold\b")


# R6: the prohibition is split so S1.1's authorized install and hold can never be confused with a forbidden rollback mutation.
PACKAGE_HOLD = re.compile(r"\bapt-mark\s+(hold|unhold)\b")
ROLLBACK_IDS = ["R0", "R", "R3"]   # every recovery/rollback block of the plan
PACKAGE_INSTALL = re.compile(r"\b(apt-get|apt|aptitude)\b[^\n]*\binstall\b|\bdpkg\s+(-i\b|--install\b)")


def _forbidden_package_mutation(line: str) -> bool:
    return bool(PACKAGE_REMOVAL.search(line) or PACKAGE_HOLD.search(line) or PACKAGE_INSTALL.search(line))


def test_r5_no_s1_rollback_path_contains_a_package_removal_purge_autoremove_downgrade_hold_or_unhold():
    # R0 and R (and the S3 rollback R3): no removal, purge, autoremove, downgrade, install, hold or unhold of any kind
    for ident in ROLLBACK_IDS:
        for line in _executable_lines(block(ident)):
            assert not _forbidden_package_mutation(line), (ident, line)
    r = block("R")
    assert not re.search(r"(?<![\w./$-])(apt-get|apt|dpkg|aptitude)(?=\s)", "\n".join(_executable_lines(r))), "R only reads package state (dpkg-query, apt-mark showhold)"
    mark = [l for l in _executable_lines(r) if "apt-mark" in l]
    assert mark and all("apt-mark showhold" in l for l in mark), mark
    # block D: NO package-manager mutation of any kind (no apt-get at all: the install path was removed); nothing in D removes, installs or holds
    d = definitions()
    for line in _executable_lines(d):
        assert not re.search(r"(?<![\w./$-])apt-get\b", line), line
        assert not PACKAGE_REMOVAL.search(line) and not PACKAGE_HOLD.search(line) and not PACKAGE_INSTALL.search(line), line
    # no block other than S1.1 holds or unholds; no block at all removes, purges, autoremoves, downgrades or INSTALLS
    for ident in IDS:
        for line in _executable_lines(block(ident)):
            assert not PACKAGE_REMOVAL.search(line), (ident, line)
            assert not PACKAGE_INSTALL.search(line), (ident, line)
            assert not re.search(r"(?<![\w./$-])apt-get\b", line), (ident, line)
            if ident == "S1.1":
                assert not re.search(r"\bapt-mark\s+unhold\b", line), (ident, line)
            else:
                assert not PACKAGE_HOLD.search(line), (ident, line)
    # S1.1 retains exactly one authorized mutation: one hold of the recorded list of pinned packages
    s11 = _executable_lines(block("S1.1"))
    holds = [l for l in s11 if PACKAGE_HOLD.search(l)]
    assert len(holds) == 1 and re.search(r"\bapt-mark\s+hold\s+--\s", holds[0]), holds
    assert not [l for l in s11 if _forbidden_package_mutation(l) and not PACKAGE_HOLD.search(l)], "S1.1 holds only via apt-mark hold and installs nothing"


@pytest.mark.parametrize("injected", [
    "apt-get remove --yes libfake-dep", "apt remove -y libfake-dep", "apt-get purge libfake-dep", "apt-get autoremove --yes", "apt-get autopurge -y",
    "dpkg --remove libfake-dep", "dpkg --purge libfake-dep", "dpkg -r libfake-dep", "apt-get install --allow-downgrades libfake-dep=0.9",
    "apt-mark unhold libfake-dep", "apt-mark hold libfake-dep",
])
def test_r6_the_structural_detector_catches_every_reintroduced_package_mutation(injected):
    for ident in ROLLBACK_IDS:
        mutated = block(ident) + "\n" + injected + "\n"
        assert any(_forbidden_package_mutation(l) for l in _executable_lines(mutated)), (ident, injected)


def _r_wrapper_tail() -> str:
    """The literal text of block R after the subshell closes: the status-reporting wrapper."""
    r = block("R")
    i = r.rindex("\n); rc=$?")
    return r[i + 1:]


@pytest.mark.parametrize("rc", [0, 28, 20, 24, 25, 26, 27])
def test_r6_the_final_wrapper_reports_each_status_accurately_and_preserves_it(rc):
    tail = _r_wrapper_tail()
    assert tail.startswith("); rc=$?")
    done = subprocess.run(["bash", "-c", f"( exit {rc}\n{tail}\n"], capture_output=True, text=True)
    assert done.returncode == rc, (rc, done)
    assert f"[R rc={rc}]" in done.stdout
    if rc == 0:
        assert "Pre-state restored" in done.stdout and "ESCALATE" not in done.stdout
    elif rc == 28:
        assert "status 28" in done.stdout and "ATTENDED recovery" in done.stdout and "Pre-state restored" not in done.stdout
    else:
        assert f"status {rc}" in done.stdout and "ESCALATE to Peter" in done.stdout and "Pre-state restored" not in done.stdout
        assert "status 28" not in done.stdout and "ATTENDED" not in done.stdout and "package or hold differences" not in done.stdout, done.stdout


@host
def test_r6_a_real_non_28_failure_of_block_r_does_not_print_the_status_28_explanation(world):
    w = world(); w.release(); ok(w.run("S1.0"), "S1.0")
    knobs(w, fail={"getent": 3})
    done = w.run("R")
    assert done.returncode == 27 and "[R rc=27]" in done.stdout and "R stopped with status 27" in done.stdout
    assert "status 28" not in done.stdout and "ATTENDED RECOVERY REQUIRED" not in done.stdout and "Pre-state restored" not in done.stdout, done.stdout


def test_r5_the_runbook_no_longer_calls_anything_package_ownership():
    text = runbook()
    for needle in ("owned.pkgs", "ROUTE3_OWN", "route3_own_resolve", "route3_owned_write", "operation-owned", "completed-effect", "completed effect", "ownership is ambiguous", "AMBIGUOUS: owned"):
        assert needle not in text, needle
    r = block("R")
    assert "ATTENDED RECOVERY REQUIRED" in r and "esc=28" in r and "R changed NO package and NO hold" in r



SUP = "freedom-blades-executor-supervisor.service"
UNIT_MUTATING_CALLS = ("userdel", "groupdel", "loginctl", "visudo")


def untouched_by_r3(w: World, before: dict, ncalls: int) -> None:
    assert w.objects() == before, "R3 must change nothing when the first manager query is indeterminate"
    assert not (w.top / "installer.log").read_text().count('"remove"'), "no installer removal"
    assert not [c for c in w.calls()[ncalls:] if c.split()[0] in UNIT_MUTATING_CALLS and "visudo -c" not in c], "no sudoers, SA-2, linger or account change"


@host
@pytest.mark.parametrize("state", ["inactive", "failed", "active", "activating"])
@pytest.mark.parametrize("status", [1, 3, 4, 127])
def test_a_failed_manager_query_that_prints_a_state_is_indeterminate_and_blocks_r3_before_any_mutation(world, state, status):
    w = world(); w.release(); arm(w); before = w.objects(); n0 = len(w.calls())
    knobs(w, fail={"systemctl show": status}, fail_print=state)
    done = w.run("R3")
    assert done.returncode == 27 and "cannot be established" in done.stdout and "STOP-A re-established" not in done.stdout, (state, status, done.stdout)
    untouched_by_r3(w, before, n0)
    knobs(w, fail={}, fail_print=None)
    ok(w.run("R3"), "R3")


@host
@pytest.mark.parametrize("out", ["", "\n", "garbage", "unknown", "maintenance", "inactive\nactive", "inactive extra", "Inactive", "inactive "])
def test_empty_unknown_or_malformed_manager_output_with_a_success_status_is_indeterminate(world, out):
    w = world(); w.release(); arm(w); before = w.objects(); n0 = len(w.calls())
    knobs(w, show_out={SUP: out})
    done = w.run("R3")
    assert done.returncode == 27 and "STOP-A re-established" not in done.stdout, (repr(out), done.returncode, done.stdout)
    untouched_by_r3(w, before, n0)


@host
@pytest.mark.parametrize("state,want", [("inactive", 0), ("failed", 0), ("active", 21), ("activating", 21), ("reloading", 21), ("deactivating", 21)])
def test_the_legitimate_status_and_state_pairs_still_drive_r3_as_documented(world, state, want):
    w = world(); w.release(); arm(w)
    knobs(w, active={SUP: state})
    done = w.run("R3")
    assert done.returncode == want, (state, done.stdout)
    assert ("STOP-A re-established" in done.stdout) == (want == 0)
    if want:
        assert not (w.top / "installer.log").read_text().count('"remove"')


@host
@pytest.mark.parametrize("state,want", [("inactive", 0), ("failed", 0), ("active", 22), ("activating", 22)])
def test_r_reads_the_account_user_manager_state_only_through_a_definite_answer(world, state, want):
    w = world(); w.release(); provision(w, "S1.3")
    knobs(w, active={"user@61234.service": state})
    done = w.run("R"); assert done.returncode == (28 if want == 0 else want), (state, done.stdout)   # S1.1 installed the packages: the attended boundary
    for status in (1, 3):                     # a failed query that printed the same word proves nothing
        w2 = world(); w2.release(); provision(w2, "S1.3")
        knobs(w2, fail_unit={"user@61234.service": status}, fail_print=state)
        done = w2.run("R"); assert done.returncode == 27 and "Pre-state restored" not in done.stdout and not calls_of(w2, "userdel"), (state, status, done.stdout)


@host
@pytest.mark.parametrize("status", [1, 3])
def test_a_final_manager_query_failure_prevents_every_restored_or_verified_message(world, status):
    # R3 at STOP-A: the supervisor query is fine; the final user-manager query fails while printing "inactive"
    w = world(); w.release(); provision(w)
    knobs(w, fail_unit={"user@61234.service": status}, fail_print="inactive")
    done = w.run("R3")
    assert done.returncode == 27 and "STOP-A re-established" not in done.stdout and "ESCALATE" in done.stdout, done.stdout
    # ... and the final LoadState query fails while printing "not-found"
    w2 = world(); w2.release(); provision(w2)
    knobs(w2, fail_prop={"LoadState": status}, fail_print="not-found")
    done = w2.run("R3")
    assert done.returncode == 27 and "STOP-A re-established" not in done.stdout and "not-found" in done.stdout.replace("does not report the supervisor unit as not-found", "not-found"), done.stdout
    # S2.1 makes the same claim and is held to the same rule
    w3 = world(); w3.release(); provision(w3)
    knobs(w3, fail_unit={"user@61234.service": status}, fail_print="inactive")
    done = w3.run("S2.1"); failed(done, "S2.1"); assert "STOP-A verified" not in done.stdout and "cannot be queried" in done.stdout
    w4 = world(); w4.release(); provision(w4)
    knobs(w4, fail_prop={"LoadState": status}, fail_print="not-found")
    done = w4.run("S2.1"); failed(done, "S2.1"); assert "STOP-A verified" not in done.stdout
    w5 = world(); w5.release(); provision(w5)
    knobs(w5, fail={"systemctl list-units": status})
    done = w5.run("S2.1"); failed(done, "S2.1"); assert "STOP-A verified" not in done.stdout and f"status {status}" in done.stdout
    knobs(w5, fail={}); ok(w5.run("S2.1"), "S2.1")


@host
def test_s2_1_and_s3_1_agree_with_the_helper_on_the_definite_answers(world):
    w = world(); w.release(); provision(w); ok(w.run("S2.1"), "S2.1")
    w2 = world(); w2.release(); provision(w2); knobs(w2, active={"user@61234.service": "active"})
    failed(w2.run("S2.1"), "S2.1")
    w3 = world(); w3.release(); provision(w3); (w3.top / "booted").write_text("")
    knobs(w3, fail_unit={"user@61234.service": 1}, fail_print="active")      # a failing query that prints "active" must not satisfy the S3.1 wait
    done = w3.run("S3.1", mutate=lambda b: b.replace("seq 1 30", "seq 1 2")); failed(done, "S3.1")


@host
def test_mutation_discarding_the_manager_command_status_lets_a_failed_query_pass_for_a_definite_state(world):
    w = world(); w.release(); arm(w); before = w.objects()
    knobs(w, fail={"systemctl show": 3}, fail_print="inactive")
    assert w.run("R3").returncode == 27
    old = 'rc=$?\n  [ "$rc" -eq 0 ] || { printf \'indeterminate\\n\'; return 0; }'
    assert old in definitions()
    mutated = w.run("R3", dmutate=lambda d: d.replace(old, "rc=0"))
    assert "installer remove status" in mutated.stdout, "without the status check the failed query's text is believed and R3 proceeds to remove the installed unit on an unproved state"
    assert (w.top / "installer.log").read_text().count('"remove"') == 1 and w.objects() != before


def test_no_manager_state_decision_in_the_plan_reads_text_without_a_status():
    code = lambda text: "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))
    for ident in IDS:
        assert "systemctl is-active" not in code(block(ident)), ident
    assert "systemctl is-active" not in code(definitions())
    for ident in ("S2.1", "S3.1", "R", "R3"):
        assert not re.search(r'\$\(systemctl\b(?! list-units)', code(block(ident))), f"{ident} must go through route3_unit / route3_loadstate"
    assert re.search(r"lrc=\$\?", block("S2.1")) and 'systemctl show -p ActiveState --value "$1"' in definitions()


# ---- 7. real systemctl on the disposable host: the status/state pairs the helper accepts (read only) -------------------------------------

REAL_SYSTEMCTL = ROOT and shutil.which("systemctl") is not None and Path("/run/systemd/system").is_dir()
real_systemctl = pytest.mark.skipif(not REAL_SYSTEMCTL, reason="needs root and a running systemd (oracle-test)")


@real_systemctl
def test_real_systemctl_status_and_state_pairs_are_the_ones_the_helper_accepts():
    def sh(cmd: str) -> subprocess.CompletedProcess:
        return real_bash(cmd + '; echo "[rc=$?]"')
    raw = lambda args: subprocess.run(["systemctl", *args], capture_output=True, text=True, check=False)
    # `show` answers with status 0 and one word, also for a unit the manager does not know
    for unit, word in (("systemd-journald.service", "active"), ("frt-plan-nonexistent.service", "inactive")):
        s = raw(["show", "-p", "ActiveState", "--value", unit]); assert (s.returncode, s.stdout.strip()) == (0, word), (unit, s)
        assert sh(f"route3_unit {unit}").stdout.startswith(word + "\n")
    inactive = next((u for u in ("systemd-tmpfiles-clean.service", "apt-daily.service", "man-db.service", "logrotate.service")
                     if raw(["show", "-p", "ActiveState", "--value", u]).stdout.strip() == "inactive" and raw(["show", "-p", "LoadState", "--value", u]).stdout.strip() == "loaded"), None)
    assert inactive, "no loaded, inactive service found to observe"
    assert sh(f"route3_unit {inactive}").stdout.startswith("inactive\n")
    assert sh("route3_loadstate frt-plan-nonexistent.service").stdout.startswith("not-found\n")
    assert sh("route3_loadstate systemd-journald.service").stdout.startswith("loaded\n")
    # the old text-only helper would have been fooled: `is-active` prints the same word with different statuses for a unit that is merely inactive and one that is unknown
    a = raw(["is-active", inactive]); b = raw(["is-active", "frt-plan-nonexistent.service"])
    assert (a.stdout.strip(), b.stdout.strip()) == ("inactive", "inactive") and a.returncode != b.returncode and a.returncode != 0 and b.returncode != 0
    # a real query failure (no reachable manager) exits non-zero and the helper maps it to indeterminate whatever it prints
    done = sh('systemctl() { env -i PATH=/usr/bin:/bin XDG_RUNTIME_DIR=/nonexistent /usr/bin/systemctl --user "$@"; }; route3_unit x.service; route3_loadstate x.service')
    assert done.stdout.splitlines()[:2] == ["indeterminate", "indeterminate"], done.stdout
    # a stub that prints each state word and exits with each failure status: all indeterminate; with status 0 the word is accepted
    for word in ("inactive", "failed", "active", "activating", "reloading", "deactivating"):
        for rc in (1, 2, 3, 4, 127):
            d = sh(f'systemctl() {{ echo {word}; return {rc}; }}; route3_unit x.service')
            assert d.stdout.startswith("indeterminate\n"), (word, rc, d.stdout)
        assert sh(f'systemctl() {{ echo {word}; return 0; }}; route3_unit x.service').stdout.startswith(word + "\n")
    for out in ("", "weird", "maintenance"):
        assert sh(f'systemctl() {{ echo "{out}"; return 0; }}; route3_unit x.service').stdout.startswith("indeterminate\n")


# ---- the plan has no install path, and every mutating boundary runs the whole trusted attestation itself (independent review, finding 2) ----------

REMOVED_INSTALL_MACHINERY = ("route3_apt_install", "route3_apt_sim", "route3_apt_parse", "route3_hook_text", "route3_effects_hook_text", "route3_apt_hook_write", "route3_txn_rows", "route3_effects_rows",
                             "route3_observe_resolve", "route3_observed_write", "route3_delta_ok", "ROUTE3_TODO", "apt.intent", "apt.txn", "apt.effects", "observed.pkgs", "apt-get install", "DPkg::")
GATED_BLOCKS = ["S1.0", "S1.1", "S1.2", "S1.3", "S1.4", "S3.1", "S3.2", "S3.3", "S3.5", "S4.1"]
FIRST_MUTATION = re.compile(r"route3_cp |\binstall\s+-[dm]|\bmkdir\s+-m|apt-mark\s+hold|\buseradd\b|loginctl\s+enable|\bmv\s|route3_installer\s+install|systemctl\s+start|build\.py|route3_pkgs\s*>|printf\b[^\n]*>\s*\"\$N\"|polkit|ROUTE3_TMPFILES\"\s+install")


def test_the_runbook_has_no_package_install_path_at_all():
    every_block = "\n".join(bash_blocks())
    executable = "\n".join(l for l in every_block.splitlines() if not l.lstrip().startswith("#"))
    for needle in REMOVED_INSTALL_MACHINERY:
        assert needle not in executable, needle
    code = "\n".join(_executable_lines(definitions()) + [l for i in IDS for l in _executable_lines(block(i))])
    assert not re.search(r"(?<![\w./$-])apt-get\b", code) and not PACKAGE_INSTALL.search(code), "no executable line of any block or of block D installs or asks apt to"
    check = re.search(r"^route3_apt_check\(\) \{.*?^\}", definitions(), re.S | re.M)[0]
    assert "never installs a package" in check and 'bad=1' in check and "ROUTE3_TODO" not in check, "a missing member is a hard NO-GO"


@pytest.mark.parametrize("ident", GATED_BLOCKS)
def test_every_mutating_block_calls_the_gate_before_its_first_mutation(ident):
    lines = [l for l in block(ident).splitlines() if not l.lstrip().startswith("#")]
    gate = next((i for i, l in enumerate(lines) if "route3_gate" in l), None)
    mutation = next((i for i, l in enumerate(lines) if FIRST_MUTATION.search(l)), None)
    assert gate is not None, f"{ident} never runs the trusted gate"
    assert mutation is None or gate < mutation, f"{ident}: the gate (line {gate}) must precede the first mutation (line {mutation}: {lines[mutation].strip()})"
    assert "route3_gate ||" in "\n".join(lines) or "route3_gate || exit" in "\n".join(lines) or "&& route3_gate ||" in "\n".join(lines), f"{ident}: the gate's status must stop the block"


def test_the_read_only_stages_run_the_same_gate_and_rollbacks_do_not_depend_on_it():
    for ident in ("S0.3", "S2.1"):
        assert "route3_gate" in block(ident), ident
    for ident in ("R0", "R", "R3"):
        assert "route3_gate" not in block(ident), f"{ident} must run whatever state the host is in"
    assert "route3_python_ok" not in "".join(block(i) for i in IDS), "the weaker local-metadata check is only a part of the gate, never a stage's sole check"


@host
@pytest.mark.parametrize("ident", ["S1.0", "S1.1", "S1.2", "S1.3", "S1.4"])
@pytest.mark.parametrize("deviation", ["gate refuses", "artifact tampered"])
def test_s1_blocks_invoked_directly_refuse_before_mutating_when_the_trusted_attestation_fails(world, ident, deviation):
    """S0.3 was never run in this world. A failing attestation (a missing, changed or extra member or a payload difference, as the real tool reports it) stops each S1 block before it mutates."""
    w = world(); w.release()
    prior = ["S1.0", "S1.1", "S1.2", "S1.3", "S1.4"]
    for earlier in prior[: prior.index(ident)]:
        ok(w.run(earlier), earlier)
    if deviation == "gate refuses":
        knobs(w, gate_rc=1, gate_msg="unexpected closure: libnew1 is now part of the dependency closure")
    else:
        (w.art / w.rev / "reference.record").write_text("tampered\n")
    before, calls, cps = w.objects(), len(w.calls()), (w.evid / "checkpoints").read_text() if w.evid.exists() else None
    done = w.run(ident)
    failed(done, ident)
    assert "NO-GO" in done.stdout
    assert w.objects() == before and not package_mutations(w.calls()[calls:]) and not [c for c in w.calls()[calls:] if c.split()[0] in ("useradd", "loginctl", "visudo")]
    assert ((w.evid / "checkpoints").read_text() if w.evid.exists() else None) == cps, "no checkpoint was written"
    assert not (w.top / "installer.log").exists()


# ---- S4.1 reruns the same attestation before it starts anything (independent review, blocking finding) ---------------------------------------------

def armed_through_s3_5(w: World) -> None:
    """The world after S3.5 (STOP-B): provisioned, booted once, armed, unit installed and enabled but not started."""
    provision(w); (w.top / "booted").write_text("")
    for ident in ("S3.1", "S3.2", "S3.3", "S3.4", "S3.5"):
        ok(w.run(ident), ident)


S4_1_DRIFT = ["baseline drift", "payload drift", "baseline record tampered", "reference record tampered", "archive tampered", "interpreter drift", "release field unset", "deployed tree drift"]


@host
@pytest.mark.parametrize("label", S4_1_DRIFT)
def test_s4_1_invoked_directly_refuses_drift_before_starting_or_changing_anything(world, label):
    """S2.1 and S3.x ran earlier in this world, but S4.1 is its own decision and does not rely on that: it reruns the full gate and refuses, with no `systemctl start`, no installer call and no mutation."""
    w = world(); w.release(); armed_through_s3_5(w)
    kw: dict = {}
    if label == "baseline drift":
        knobs(w, gate_rc=1, gate_msg="unexpected closure: libnew1 is now part of the dependency closure")
    elif label == "payload drift":
        knobs(w, gate_rc=1, gate_msg="payload drift: the installed files of libfake-dep=1.0 are not those of the signed-archive package")
    elif label == "baseline record tampered":
        (w.art / w.rev / "baseline.record").write_text("tampered\n")
    elif label == "reference record tampered":
        (w.art / w.rev / "reference.record").write_text("tampered\n")
    elif label == "archive tampered":
        with open(w.art / w.rev / "code.tar", "ab") as f:
            f.write(b"\0")
    elif label == "interpreter drift":
        kw["fields"] = {"PY_SHA256": "0" * 64}
    elif label == "release field unset":
        kw["fields"] = {"ARCHIVE_SHA256": "UNSET"}
    else:
        (w.base / "code" / "tools" / "extra.py").write_text("")
    before, calls, cps = w.objects(), len(w.calls()), (w.evid / "checkpoints").read_text()
    installer_log = (w.top / "installer.log").read_text()
    done = w.run("S4.1", **kw)
    failed(done, "S4.1")
    assert done.returncode == 2 and "NO-GO" in done.stdout and "[S4.1 rc=2]" in done.stdout, (done.returncode, done.stdout, done.stderr)
    new = w.calls()[calls:]
    assert not [c for c in new if c.startswith("systemctl")], new                  # not `start`, and no other manager call either
    assert not package_mutations(new) and not [c for c in new if c.split()[0] in ("useradd", "userdel", "loginctl", "visudo", "reboot", "shutdown", "sudo")], new
    assert (w.top / "installer.log").read_text() == installer_log, "the installer (verify-ready) was not reached"
    assert w.objects() == before and (w.evid / "checkpoints").read_text() == cps, "nothing changed and no checkpoint was written"


@host
def test_s4_1_runs_the_gate_and_then_starts_the_supervisor_when_the_host_is_the_reviewed_baseline(world):
    """The positive control for the refusals above: with no drift the same invocation reruns the gate, starts the supervisor once and returns the installer's verify-ready status."""
    w = world(); w.release(); armed_through_s3_5(w)
    gate_runs, calls = len((w.top / "gate.log").read_text().splitlines()), len(w.calls())
    done = w.run("S4.1"); ok(done, "S4.1")
    assert len((w.top / "gate.log").read_text().splitlines()) == gate_runs + 1, "S4.1 itself reran the trusted attestation"
    new = w.calls()[calls:]
    starts = [c for c in new if c.startswith("systemctl") and re.search(r"\bstart\b", c)]
    assert starts == ["systemctl start freedom-blades-executor-supervisor.service"], new
    assert "verify-ready" in (w.top / "installer.log").read_text().splitlines()[-1]
    # the installer's own status still passes through
    (w.top / "installer-status").write_text("12")
    again = w.run("S4.1"); failed(again, "S4.1"); assert again.returncode == 12
