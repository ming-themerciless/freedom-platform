"""Production checklist item 8 (handback §6) runs ``tools.polkit_tmpfiles verify`` as root, so it must execute the reviewed copy inside the
trusted Route 3 deployment and nothing reachable from the ordinary checkout, its venv or the caller's Python environment. Before any deployment
Python is evaluated the entry itself must establish that every component from ``/`` through the tool and through the source fragment is a
symlink-free, root-owned, group/other-non-writable directory or regular file. The runbook carries the same entry and must return the verifier's
status. §6.1 must keep the historical v1 paths its recorded counts came from, labelled and non-executable.

Behavior tests that need real ownership run as root (``oracle-test``); they build their tree under ``/opt`` because ``/tmp`` is world-writable and
the production predicate rightly refuses it. The literal predicate is never weakened: a deployment is "trusted" only if root really owns it."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
HANDBACK = REPO / "docs/review/route-3-production-readiness-handback.md"
RUNBOOK = REPO / "docs/operations/executor-supervisor-provisioning-runbook.md"
TRUSTED_FILE = "/opt/freedom-route3/code/tools/polkit_tmpfiles.py"
ENTRY = re.compile(r"^ROUTE3_ENTRY='(?P<code>[^']+)'\n", re.M)
STEP = re.compile(r'^step "polkit_tmpfiles verify[^"]*" /usr/bin/env -i PATH=/usr/bin:/bin "\$ROUTE3_PY" -I -S -c "\$ROUTE3_ENTRY" "\$ROUTE3_TMPFILES" verify$', re.M)
FINDING = "[FINDING] trusted Route 3 tool or source fragment is missing, wrong-typed, symlinked, not root-owned or group/other-writable: verify not run"
ROOT = os.geteuid() == 0
needs_root = pytest.mark.skipif(not ROOT, reason="real root ownership is required: run on oracle-test as root (see the R4 return)")


def handback() -> str:
    return HANDBACK.read_text()


def section_6() -> str:
    text = handback()
    return text[text.index("\n## 6. Production-specific read-only fact checklist"): text.index("\n### 6.1 Production inspection result")]


def current_checklist() -> str:
    """The one executable v2 checklist: §6 holds exactly one bash block, and the historical record is never fenced as bash."""
    blocks = re.findall(r"```bash\n(.*?)\n```", section_6(), re.S)
    assert len(blocks) == 1, "§6 must hold exactly one executable checklist"
    return blocks[0]


def section_6_1() -> str:
    text = handback()
    return text[text.index("### 6.1 Production inspection result"): text.index("### 6.2 Production remediation return")]


def item_8_lines() -> str:
    body = current_checklist()
    return body[body.index("# 8  tmpfiles.d"): body.index("# 9  capacity")]


def prelude() -> str:
    body = current_checklist()
    return body[body.index("set -u"): body.index("# 1  OS, kernel")]


def entry_code(text: str) -> str:
    found = ENTRY.findall(text)
    assert len(found) == 1, "exactly one ROUTE3_ENTRY assignment"
    return found[0]


def runbook_blocks() -> list[str]:
    return re.findall(r"```bash\n(.*?)\n```", RUNBOOK.read_text(), re.S)


def runbook_definitions() -> str:
    """Block D of the runbook's part P: the one place the item-8 entry and the fixed seam literals live."""
    found = [b for b in runbook_blocks() if b.startswith("ROUTE3_PATH=")]
    assert len(found) == 1
    return found[0]


def runbook_block() -> str:
    """The standalone post-provision check (S2.2) with the definitions it needs, as one runnable script."""
    verify = [b for b in runbook_blocks() if b.startswith("# S2.2 ")]
    assert len(verify) == 1
    return runbook_definitions() + "\n" + verify[0]


def test_item_8_is_anchored_to_the_trusted_deployment_with_fixed_literals():
    block = item_8_lines()
    assert block.count("\nROUTE3_PY=/usr/bin/python3.14\n") == 1
    assert block.count(f"\nROUTE3_TMPFILES={TRUSTED_FILE}\n") == 1
    assert len(STEP.findall(block)) == 1
    entry_code(block)
    outside = ENTRY.sub("", block)
    commands = [line for line in outside.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    assert len(commands) == 3, commands  # the two seam literals and the one command: nothing else runs in item 8
    assert "-m tools" not in outside and "cd " not in outside and "bash -c" not in outside


def test_the_current_checklist_names_no_ordinary_checkout_or_live_venv_path():
    body = current_checklist()
    assert "/opt/freedom-blades" not in body
    assert "venv-web" not in body
    for root in ("code/tools", "code/infra/tmpfiles.d"):  # what item 8 executes as root is inside item 7's trust scope
        assert f"/opt/freedom-route3/{root} " in body or f"/opt/freedom-route3/{root};" in body or f"/opt/freedom-route3/{root}\\" in body, root


def test_the_entry_walks_both_paths_before_it_evaluates_anything_and_names_the_tools_own_fragment():
    code = entry_code(item_8_lines())
    assert code.index("chain(tool)") < code.index("runpy.run_path(") and code.rindex("chain(") < code.index("runpy.run_path(")
    assert "os.lstat" in code and "os.stat" not in code.replace("os.lstat", "") and "islink" not in code
    tools = (REPO / "tools/polkit_tmpfiles.py").read_text()
    name = re.search(r'^FRAGMENT_NAME = "([^"]+)"', tools, re.M)[1]
    assert re.search(r'^SOURCE_RELATIVE = Path\("infra"\) / "tmpfiles.d" / FRAGMENT_NAME$', tools, re.M)
    assert "Path(__file__).resolve().parent.parent / SOURCE_RELATIVE" in tools
    assert f'+"/infra/tmpfiles.d/{name}"' in code


def test_the_runbook_carries_the_same_entry_and_returns_the_verifiers_status():
    block = runbook_block()
    assert entry_code(runbook_definitions()) == entry_code(item_8_lines())
    assert block.count("ROUTE3_ENTRY='") == 1
    assert "ROUTE3_PY=/usr/bin/python3.14\n" in block and f"ROUTE3_TMPFILES={TRUSTED_FILE}\n" in block
    last = block.splitlines()[-1]
    assert last == '( /usr/bin/env -i PATH=/usr/bin:/bin "$ROUTE3_PY" -I -S -c "$ROUTE3_ENTRY" "$ROUTE3_TMPFILES" verify; rc=$?; echo "[rc=$rc]"; exit "$rc" )'
    assert "-m tools.polkit_tmpfiles" not in RUNBOOK.read_text()


def test_section_6_1_keeps_the_historical_v1_paths_and_is_not_executable():
    block = section_6_1()
    assert "HISTORICAL" in block and "v1" in block and "never to be run against production now" in block
    assert "```bash" not in block, "the historical record must not be fenced as an executable block"
    for literal in ("/opt/freedom-blades/platform/adapters", "/opt/freedom-blades/runtime/venv-web/bin/python",
                    "/opt/freedom-blades/platform/infra/executor/freedom-blades-executor-supervisor.service",
                    "cd /opt/freedom-blades/platform && exec python3 -m tools.polkit_tmpfiles verify",
                    "EXPECTED='/opt/freedom-blades/runtime/venv-web/bin/python -E -s -m adapters.executor.supervisor '"):
        assert literal in block, literal
    assert "no path under `/opt/freedom-route3` was inspected" in block
    assert "203" in block and "5,334" in block  # the recorded counts stay attached to the v1 paths


# ---- behavior: the literal checklist item and the literal runbook block, run against synthetic deployments --------------------------

FRAGMENT = "freedom-blades-rp11-polkit-rules.conf"


def stub(marker: Path, status: int = 0) -> str:
    # ``json`` is imported after start-up (``os``/``runpy``/``sys`` are already loaded, so shadowing them proves nothing)
    return f"import sys, json\nopen({str(marker)!r}, 'a').write('ran')\nprint('TRUSTED-MODULE', __name__, __file__, sys.argv[1:])\nsys.exit({status})\n"


def hostile_tree(root: Path) -> dict:
    """An ordinary checkout and Python environment that would hijack any ambient import, cwd or user-site lookup."""
    hostile, marker = root / "hostile", root / "HOSTILE-RAN"
    code = f"open({str(marker)!r}, 'a').write('ran')\n"
    (hostile / "tools").mkdir(parents=True)
    (hostile / "tools/__init__.py").write_text(code)
    (hostile / "tools/polkit_tmpfiles.py").write_text(code + "import sys; print('HOSTILE-TOOL'); sys.exit(0)\n")
    for name in ("json.py", "runpy.py", "sitecustomize.py", "usercustomize.py", "polkit_tmpfiles.py"):
        (hostile / name).write_text(code)
    user_site = root / "home/.local/lib/python3/site-packages"
    user_site.mkdir(parents=True)
    (user_site / "usercustomize.py").write_text(code)
    (user_site / "json.py").write_text(code)
    (root / "startup.py").write_text(code)
    return {"cwd": hostile, "marker": marker, "env": {
        "PYTHONPATH": str(hostile), "PYTHONHOME": str(hostile), "PYTHONUSERBASE": str(root / "home/.local"),
        "PYTHONSTARTUP": str(root / "startup.py"), "HOME": str(root / "home"), "PYTHONSAFEPATH": "", "BASH_ENV": ""}}


class Deployment:
    """A synthetic ``<base>/code/{tools,infra/tmpfiles.d}`` deployment. Under root it is built in a root-owned, non-writable tree outside ``/tmp``."""

    def __init__(self, base: Path, scratch: Path, *, tool_source: str | None = None, status: int = 0):
        self.base, self.scratch = base, scratch
        self.exec_marker = scratch / "TRUSTED-RAN"
        self.code, self.tools, self.infra, self.tmpfiles = base / "code", base / "code/tools", base / "code/infra", base / "code/infra/tmpfiles.d"
        self.tool, self.fragment = self.tools / "polkit_tmpfiles.py", self.tmpfiles / FRAGMENT
        self.tmpfiles.mkdir(parents=True)
        self.tools.mkdir(parents=True, exist_ok=True)
        self.tool.write_text(tool_source if tool_source is not None else stub(self.exec_marker, status))
        self.fragment.write_text((REPO / "infra/tmpfiles.d" / FRAGMENT).read_text())
        for directory in (base, self.code, self.tools, self.infra, self.tmpfiles):
            directory.chmod(0o755)
        self.tool.chmod(0o644)
        self.fragment.chmod(0o644)


@pytest.fixture
def deployment_factory(tmp_path):
    """Yield a builder; under root the tree is created in ``/opt`` (root-owned, 0755) and removed afterwards."""
    import shutil
    import tempfile
    roots: list[Path] = []

    def build(**kwargs) -> Deployment:
        base = Path(tempfile.mkdtemp(prefix="frt-test-", dir="/opt")) if ROOT else tmp_path / "deploy"
        roots.append(base)
        scratch = tmp_path / f"scratch{len(roots)}"
        scratch.mkdir()
        return Deployment(base, scratch, **kwargs)
    yield build
    for base in roots:
        real = base.with_name(base.name + "-real")
        if base.is_symlink():
            base.unlink()
        shutil.rmtree(base, ignore_errors=True)
        shutil.rmtree(real, ignore_errors=True)


def substitute(script: str, interpreter: str | None, tool: Path | str) -> str:
    out = script.replace("ROUTE3_PY=/usr/bin/python3.14", f"ROUTE3_PY={interpreter or sys.executable}").replace(f"ROUTE3_TMPFILES={TRUSTED_FILE}", f"ROUTE3_TMPFILES={tool}")
    assert out != script, "the seam lines must be the only substitution"
    return out


def run_bash(script: str, scratch: Path):
    hostile = hostile_tree(scratch)
    env = {"PATH": os.environ["PATH"], **hostile["env"]}
    result = subprocess.run(["/bin/bash", "-c", script], cwd=hostile["cwd"], env=env, capture_output=True, text=True, check=False, timeout=60)
    return result, hostile["marker"]


def run_item_8(dep: Deployment, tool: Path | str | None = None, *, interpreter: str | None = None, mutate=None):
    block = item_8_lines()
    if mutate:
        block = mutate(block)
    script = substitute(prelude() + block + '\nrm -rf "$OUT"\n', interpreter, tool or dep.tool)
    return run_bash(script, dep.scratch)


def run_runbook(dep: Deployment, tool: Path | str | None = None, *, interpreter: str | None = None):
    script = substitute(runbook_block(), interpreter, tool or dep.tool) + '\necho "after=$?"\n'
    return run_bash(script, dep.scratch)


def refused(result, dep: Deployment, marker: Path) -> None:
    assert "[rc=20]" in result.stdout and FINDING in result.stdout, result.stdout + result.stderr
    assert not dep.exec_marker.exists() and not marker.exists() and "TRUSTED-MODULE" not in result.stdout and "HOSTILE-TOOL" not in result.stdout


@needs_root
def test_a_root_owned_non_writable_symlink_free_deployment_executes_exactly_the_trusted_tool(deployment_factory):
    dep = deployment_factory()
    result, marker = run_item_8(dep)
    assert f"TRUSTED-MODULE __main__ {dep.tool} ['verify']" in result.stdout, result.stdout + result.stderr
    assert "[rc=0]" in result.stdout and FINDING not in result.stdout
    assert dep.exec_marker.read_text() == "ran" and not marker.exists(), "an ordinary-checkout or environment file was executed"


@needs_root
@pytest.mark.parametrize("status", [1, 7, 12])
def test_the_tools_nonzero_status_stays_visible_and_is_not_a_pass(deployment_factory, status):
    dep = deployment_factory(status=status)
    result, _ = run_item_8(dep)
    assert f"[rc={status}]" in result.stdout and "[rc=0]" not in result.stdout, result.stdout
    assert dep.exec_marker.exists()


def test_a_missing_deployment_fails_closed_with_no_checkout_fallback(tmp_path):
    scratch = tmp_path / "s"
    scratch.mkdir()
    dep = Deployment.__new__(Deployment)
    dep.scratch, dep.exec_marker = scratch, scratch / "TRUSTED-RAN"
    result, marker = run_item_8(dep, tmp_path / "nowhere/code/tools/polkit_tmpfiles.py")
    refused(result, dep, marker)


def test_a_missing_interpreter_is_a_visible_failure_and_runs_nothing(tmp_path):
    scratch = tmp_path / "s"
    scratch.mkdir()
    dep = Deployment.__new__(Deployment)
    dep.scratch, dep.exec_marker = scratch, scratch / "TRUSTED-RAN"
    result, marker = run_item_8(dep, tmp_path / "t.py", interpreter=str(tmp_path / "no-python3.14"))
    assert re.search(r"\[rc=(126|127)\]", result.stdout), result.stdout
    assert "TRUSTED-MODULE" not in result.stdout and not marker.exists()


def chown_nobody(path: Path) -> None:
    os.chown(path, 65534, 65534, follow_symlinks=False)


def replace_with_dir(path: Path) -> None:
    path.unlink()
    path.mkdir()
    path.chmod(0o755)


def replace_dir_with_file(path: Path) -> None:
    import shutil
    shutil.rmtree(path)
    path.write_text("x")
    path.chmod(0o644)


def make_missing(path: Path) -> None:
    path.unlink()


# (label, which path of the Deployment, mutation)
VIOLATIONS = [
    ("tool non-root-owned", "tool", lambda p, d: chown_nobody(p)),
    ("tool group-writable", "tool", lambda p, d: p.chmod(0o664)),
    ("tool other-writable", "tool", lambda p, d: p.chmod(0o646)),
    ("tool is a directory", "tool", lambda p, d: replace_with_dir(p)),
    ("tool missing", "tool", lambda p, d: make_missing(p)),
    ("tools dir non-root-owned", "tools", lambda p, d: chown_nobody(p)),
    ("code dir non-root-owned", "code", lambda p, d: chown_nobody(p)),
    ("deployment base non-root-owned", "base", lambda p, d: chown_nobody(p)),
    ("tools dir group-writable", "tools", lambda p, d: p.chmod(0o775)),
    ("code dir other-writable", "code", lambda p, d: p.chmod(0o757)),
    ("deployment base group-writable", "base", lambda p, d: p.chmod(0o775)),
    ("tools is a regular file", "tools", lambda p, d: replace_dir_with_file(p)),
    ("fragment non-root-owned", "fragment", lambda p, d: chown_nobody(p)),
    ("fragment group-writable", "fragment", lambda p, d: p.chmod(0o664)),
    ("fragment other-writable", "fragment", lambda p, d: p.chmod(0o646)),
    ("fragment is a directory", "fragment", lambda p, d: replace_with_dir(p)),
    ("fragment missing", "fragment", lambda p, d: make_missing(p)),
    ("infra dir non-root-owned", "infra", lambda p, d: chown_nobody(p)),
    ("tmpfiles.d non-root-owned", "tmpfiles", lambda p, d: chown_nobody(p)),
    ("infra dir writable", "infra", lambda p, d: p.chmod(0o775)),
    ("tmpfiles.d writable", "tmpfiles", lambda p, d: p.chmod(0o757)),
    ("tmpfiles.d is a regular file", "tmpfiles", lambda p, d: replace_dir_with_file(p)),
    ("infra missing", "infra", lambda p, d: __import__("shutil").rmtree(p)),
]
IDS = [v[0] for v in VIOLATIONS]


def violate(dep: Deployment, which: str, action) -> None:
    action(getattr(dep, which), dep)


def link_in_tree(dep: Deployment, which: str) -> None:
    """Replace a path by a symlink to a fully trusted copy beside it (same filesystem, root-owned, correctly moded): only the link is the defect."""
    path = dep.base if which == "base" else getattr(dep, which)
    real = path.with_name(path.name + "-real")
    path.rename(real)
    path.symlink_to(real)


@needs_root
@pytest.mark.parametrize("label,which,action", VIOLATIONS, ids=IDS)
def test_every_untrusted_component_is_refused_before_any_deployment_code_runs(deployment_factory, label, which, action):
    dep = deployment_factory()
    violate(dep, which, action)
    result, marker = run_item_8(dep)
    refused(result, dep, marker)


SYMLINKED = ["tool", "tools", "code", "base", "fragment", "infra", "tmpfiles"]


@needs_root
@pytest.mark.parametrize("which", SYMLINKED)
def test_a_symlinked_component_is_refused_on_its_own_account(deployment_factory, which):
    dep = deployment_factory()
    link_in_tree(dep, which)
    result, marker = run_item_8(dep)
    refused(result, dep, marker)


@needs_root
def test_the_runbook_block_returns_exactly_the_verifiers_status_and_refusal_status(deployment_factory):
    ok = deployment_factory()
    result, _ = run_runbook(ok)
    assert "[rc=0]" in result.stdout and result.stdout.rstrip().endswith("after=0"), result.stdout + result.stderr
    assert ok.exec_marker.exists()
    bad = deployment_factory(status=12)
    result, _ = run_runbook(bad)
    assert "[rc=12]" in result.stdout and result.stdout.rstrip().endswith("after=12"), result.stdout
    untrusted = deployment_factory()
    untrusted.tool.chmod(0o666)
    result, marker = run_runbook(untrusted)
    refused(result, untrusted, marker)
    assert result.stdout.rstrip().endswith("after=20")


def test_the_runbook_block_refuses_an_absent_deployment_with_the_same_non_zero_status(tmp_path):
    scratch = tmp_path / "s"
    scratch.mkdir()
    dep = Deployment.__new__(Deployment)
    dep.scratch, dep.exec_marker = scratch, scratch / "TRUSTED-RAN"
    result, marker = run_runbook(dep, tmp_path / "absent/code/tools/polkit_tmpfiles.py")
    refused(result, dep, marker)
    assert result.stdout.rstrip().endswith("after=20") and "STILL" not in result.stdout


def test_the_runbook_block_does_not_end_the_callers_shell(tmp_path):
    scratch = tmp_path / "s"
    scratch.mkdir()
    dep = Deployment.__new__(Deployment)
    dep.scratch, dep.exec_marker = scratch, scratch / "TRUSTED-RAN"
    script = substitute(runbook_block(), None, tmp_path / "absent/t.py") + '\nstatus=$?\necho "shell-alive status=$status"\n'
    result, _ = run_bash(script, scratch)
    assert "shell-alive status=20" in result.stdout, result.stdout


# ---- mutation: removing a refusal must make the matching regression fail ------------------------------------------------------------

MUTATIONS = [  # (name, entry mutation, a violation it must let through: a VIOLATIONS label, or ("link", which))
    ("ownership check removed", lambda c: c.replace("s.st_uid==0 and ", ""), "tool non-root-owned"),
    ("mode check removed", lambda c: c.replace(" and not s.st_mode&0o022", ""), "tool group-writable"),
    ("parent mode check removed", lambda c: c.replace(" and not s.st_mode&0o022", ""), "code dir other-writable"),
    ("lstat replaced by stat (parent symlinks followed)", lambda c: c.replace("os.lstat", "os.stat"), ("link", "tools")),
    ("fragment walk removed", lambda c: c.replace('chain(os.path.dirname(os.path.dirname(tool))+"/infra/tmpfiles.d/freedom-blades-rp11-polkit-rules.conf")', ""), ("link", "fragment")),
]


@needs_root
@pytest.mark.parametrize("name,mutator,case", MUTATIONS, ids=[m[0] for m in MUTATIONS])
def test_removing_a_refusal_makes_the_matching_regression_fail(deployment_factory, name, mutator, case):
    """The mutated entry must *execute* the violating deployment, which is exactly what the regression above asserts cannot happen."""
    dep = deployment_factory()
    if isinstance(case, tuple):
        link_in_tree(dep, case[1])
    else:
        which, action = next((v[1], v[2]) for v in VIOLATIONS if v[0] == case)
        violate(dep, which, action)
    original = entry_code(item_8_lines())
    mutated = mutator(original)
    assert mutated != original, "the mutation must change the entry"
    result, marker = run_item_8(dep, mutate=lambda block: block.replace(original, mutated))
    assert dep.exec_marker.exists() or "TRUSTED-MODULE" in result.stdout, f"the {name} mutation was not detected: {result.stdout}"


# ---- the real tool and the fixed production interpreter ----------------------------------------------------------------------------

@needs_root
def test_the_real_tool_runs_from_the_trusted_copy_and_reports_its_own_status(deployment_factory):
    """The reviewed tool, not a stub: its source fragment is resolved next to the trusted copy, and a failing ``verify`` stays a failure."""
    dep = deployment_factory(tool_source=(REPO / "tools/polkit_tmpfiles.py").read_text())
    result, marker = run_item_8(dep)
    assert "verify: FAILED" in result.stdout or "verify: ok" in result.stdout, result.stdout + result.stderr
    expected = "[rc=0]" if "verify: ok" in result.stdout else "[rc=12]"
    assert expected in result.stdout, result.stdout
    assert "ok   source" in result.stdout, "the fragment must be resolved beside the trusted copy"
    assert "HOSTILE-TOOL" not in result.stdout and not marker.exists()


@needs_root
@pytest.mark.skipif(not Path("/usr/bin/python3.14").exists(), reason="the fixed production interpreter /usr/bin/python3.14 is not installed on this host")
def test_the_fixed_production_interpreter_loads_the_trusted_tool_in_isolated_mode(deployment_factory):
    """Uses the literal production interpreter (present on ``oracle-test``): ``-I -S`` plus ``runpy.run_path`` on Python 3.14."""
    dep = deployment_factory()
    result, marker = run_item_8(dep, interpreter="/usr/bin/python3.14")
    assert f"TRUSTED-MODULE __main__ {dep.tool} ['verify']" in result.stdout, result.stdout + result.stderr
    assert "[rc=0]" in result.stdout and not marker.exists()
