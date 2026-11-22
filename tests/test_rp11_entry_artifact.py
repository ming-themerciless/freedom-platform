"""G12: the inert Pass A entry and its fixed module-loading substrate (SA-2 artifact).

Synthetic artifacts only. Nothing here runs the capture mechanism, a host act, SSH,
rsync or a systemd unit, and nothing rebuilds or installs the production artifact.
"""

from __future__ import annotations

import ast
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from tests.test_rp11_h1_artifact import GOOD_MEMBERS, WHEEL_NAME, _load, build, make_wheel, pin

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / "infra/rp11-h1"
INVOCATION_ID = "0123456789abcdef0123456789abcdef"
ARGV = ["run", "--pass", "A"]
LOADED = "tools.phase_5_0_evidence.execution.capture_mechanism"
#: Not imported by the (inert) entry yet; a second closure root so the eventual entry
#: finds the G11 start-time binding, and the journal modules it uses, in ``lib/``.
START_BINDING = "tools.phase_5_0_evidence.execution.start_binding"
SHARED = (
    "invocation_id_from",
    "_initial_environment",
    "_listed_descriptors",
    "_is_open",
    "close_descriptors_from_3",
    "_object_problem",
    "_lstat_problem",
    "_ancestors_problem",
    "_tree_problem",
)

entry_source = HERE / "rp11_entry.py"


# -- the dependency closure --------------------------------------------------


def _module_file(name: str) -> Path | None:
    base = ROOT.joinpath(*name.split("."))
    if (base / "__init__.py").is_file():
        return base / "__init__.py"
    return base.with_suffix(".py") if base.with_suffix(".py").is_file() else None


def _closure(start: str) -> tuple[set[str], set[str]]:
    """Repository files `start` imports, with package `__init__`s, and third-party names."""
    files: set[str] = set()
    third_party: set[str] = set()
    pending = [start]
    seen: set[str] = set()
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        path = _module_file(name)
        assert path is not None, name
        files.add(str(path.relative_to(ROOT)))
        parts = name.split(".")
        pending += [".".join(parts[:i]) for i in range(1, len(parts))]
        package = name if path.name == "__init__.py" else ".".join(parts[:-1])
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                candidates = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    base = package.split(".")
                    base = base[: len(base) - (node.level - 1)]
                    module = ".".join([*base, *([node.module] if node.module else [])])
                else:
                    module = node.module or ""
                candidates = [module, *(f"{module}.{alias.name}" for alias in node.names)]
            else:
                continue
            for candidate in candidates:
                if candidate.split(".")[0] in ("tools", "application", "adapters"):
                    if _module_file(candidate):
                        pending.append(candidate)
                elif candidate.split(".")[0] not in sys.stdlib_module_names:
                    third_party.add(candidate.split(".")[0])
    return files, third_party


def test_the_entry_loads_exactly_one_module_and_nothing_third_party():
    tree = ast.parse(entry_source.read_text(encoding="utf-8"))
    imported = [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
        if alias.name.split(".")[0] in ("tools", "application", "adapters")
    ]
    assert imported == [LOADED]
    assert f'_LOADED = "{LOADED}"' in entry_source.read_text(encoding="utf-8")


def test_entry_sources_are_exactly_the_entrys_dependency_closure():
    files, third_party = _closure(LOADED)
    binding_files, binding_third_party = _closure(START_BINDING)
    files |= binding_files
    third_party |= binding_third_party
    assert third_party == set()
    assert len(build.ENTRY_SOURCES) == len(set(build.ENTRY_SOURCES))
    # both directions: nothing missing, nothing extra
    assert files - set(build.SOURCES) == set(build.ENTRY_SOURCES)
    assert set(build.ENTRY_SOURCES) <= files


@pytest.fixture
def artifact(tmp_path, monkeypatch):
    source = tmp_path / "wheel"
    source.mkdir()
    pin(monkeypatch, make_wheel(source / WHEEL_NAME, GOOD_MEMBERS))
    return build.build(source / WHEEL_NAME, tmp_path / "artifact")


def test_the_built_tree_carries_the_entry_and_its_closure_beside_the_role_entry(artifact):
    assert (artifact / "rp11_entry.py").read_bytes() == entry_source.read_bytes()
    assert (artifact / "rp11_h1.py").is_file()
    for name in build.ENTRY_SOURCES:
        assert (artifact / "lib" / name).read_bytes() == (ROOT / name).read_bytes(), name
    assert build._unsafe_tree(artifact, os.getuid()) is None
    assert stat.S_IMODE((artifact / "rp11_entry.py").stat().st_mode) == 0o644
    assert not list(artifact.rglob("__pycache__"))


# -- the shared first-image and tree checks ------------------------------------


def _function(path: Path, name: str) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    (node,) = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
    return ast.dump(node)


@pytest.mark.parametrize("name", SHARED)
def test_the_shared_checks_equal_the_role_entrys_checks(name):
    assert _function(entry_source, name) == _function(HERE / "rp11_h1.py", name)


def test_the_shared_constants_equal_the_role_entrys():
    def constants(path):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        return {
            t.id: ast.dump(n.value)
            for n in tree.body
            if isinstance(n, ast.Assign)
            for t in n.targets
            if isinstance(t, ast.Name)
            and t.id in ("_MAX_ENVIRON", "_OWN_FDS", "_HEX", "_WRITABLE_BY_OTHERS")
        }

    assert constants(entry_source) == constants(HERE / "rp11_h1.py")
    assert len(constants(entry_source)) == 4


def test_the_entry_requires_root_ownership_whoever_runs_it():
    module = _load("rp11_entry_owner", entry_source)
    assert module._required_owner() == 0


# -- inertness -----------------------------------------------------------------

_FORBIDDEN_NAMES = {
    "create_capture_session",
    "StreamCaptureLauncher",
    "subprocess",
    "socket",
    "ctypes",
    "system",
    "fork",
    "forkpty",
    "posix_spawn",
    "popen",
    "execv",
    "execve",
    "execl",
    "execvp",
    "spawnv",
    "run_act",
}


def test_the_entry_cannot_reach_the_mechanism_a_host_act_or_a_connection():
    tree = ast.parse(entry_source.read_text(encoding="utf-8"))
    used = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used.add(node.id)
        elif isinstance(node, ast.Attribute):
            used.add(node.attr)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            used |= {a.name.split(".")[0] for a in node.names}
            used |= {a.name for a in node.names}
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            lowered = node.value.lower()
            assert "rsync" not in lowered and "ssh" not in lowered.split(), node.value
    assert used & _FORBIDDEN_NAMES == set()
    # the only module it loads, it loads by import and never calls into
    calls = {
        n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
    }
    assert not any("mechanism" in str(c) for c in calls)


DRIVER = """
import importlib.util, json, os, sys
entry_path, out, trust_ancestors = sys.argv[1:4]
sys.dont_write_bytecode = True
base_path = list(sys.path)
events = []
WATCH = {"subprocess.Popen", "os.system", "os.exec", "os.fork", "os.forkpty",
         "os.posix_spawn", "os.spawn", "socket.connect", "socket.bind", "ctypes.dlopen"}
def hook(event, args):
    if event in WATCH:
        events.append(event)
sys.addaudithook(hook)
spec = importlib.util.spec_from_file_location("rp11_entry_under_test", entry_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module._required_owner = lambda: os.getuid()   # the test tree is ours, not root's
if trust_ancestors == "yes":
    module._ancestors_problem = lambda d, o: None  # /tmp is not root-protected
sys.argv = [entry_path, *sys.argv[4:]]
rc = module.entry()
modules = {n: getattr(m, "__file__", None) for n, m in sys.modules.items()
           if n not in ("rp11_entry_under_test", "__main__") and getattr(m, "__file__", None)}
with open(out, "w") as handle:
    json.dump({"rc": rc, "base_path": base_path, "path": sys.path, "events": events,
               "modules": modules, "flags": [sys.flags.isolated, sys.flags.no_site,
               sys.dont_write_bytecode]}, handle)
sys.exit(rc)
"""


def _plant(directory: Path, marker: Path) -> Path:
    for package in ("tools", "application", "adapters"):
        (directory / package).mkdir(parents=True)
        (directory / package / "__init__.py").write_text(f"open({str(marker)!r}, 'w')\n")
    return directory


def _run(artifact: Path, tmp_path: Path, *, argv=ARGV, env=None, cwd=None, trust="yes"):
    driver = tmp_path / "driver" / "driver.py"
    driver.parent.mkdir(exist_ok=True)
    driver.write_text(DRIVER)
    out = tmp_path / "result.json"
    proc = subprocess.run(
        [sys.executable, "-I", "-S", str(driver), str(artifact / "rp11_entry.py"), str(out), trust, *argv],
        capture_output=True,
        text=True,
        env={"INVOCATION_ID": INVOCATION_ID} if env is None else env,
        cwd=str(cwd or tmp_path),
    )
    return proc, (json.loads(out.read_text()) if out.exists() else None)


def test_the_entry_is_inert_and_loads_only_from_the_fixed_directory(artifact, tmp_path):
    marker = tmp_path / "PLANTED-CODE-RAN"
    hostile_path = _plant(tmp_path / "hostile-path", marker)
    hostile_cwd = _plant(tmp_path / "hostile-cwd", marker)
    # a stray sibling of lib/ in the artifact directory is not on sys.path either
    (artifact / "tools").mkdir()
    (artifact / "tools/__init__.py").write_text(f"open({str(marker)!r}, 'w')\n")
    os.chmod(artifact / "tools", 0o755)
    os.chmod(artifact / "tools/__init__.py", 0o644)  # trusted, but not on sys.path
    before = sorted(p.name for p in tmp_path.iterdir())
    proc, result = _run(
        artifact,
        tmp_path,
        env={
            "INVOCATION_ID": INVOCATION_ID,
            "PYTHONPATH": str(hostile_path),
            "PYTHONSTARTUP": str(hostile_path / "tools/__init__.py"),
            "PYTHONUSERBASE": str(hostile_path),
            "PYTHONDONTWRITEBYTECODE": "",
        },
        cwd=hostile_cwd,
    )
    assert proc.returncode == 69, proc.stderr
    assert "not implemented" in proc.stderr
    assert not marker.exists()
    lib = str(artifact / "lib")
    assert result["path"] == [*result["base_path"], lib]  # appended last, nothing else
    assert result["flags"] == [1, 1, True]
    assert result["events"] == []  # no process, connection or exec
    stdlib = tuple(result["base_path"])
    for name, file in result["modules"].items():
        assert file.startswith(stdlib) or file.startswith(lib + "/"), (name, file)
    assert result["modules"][LOADED].startswith(lib + "/")
    assert result["modules"]["tools"] == f"{lib}/tools/__init__.py"
    assert not list(artifact.rglob("__pycache__"))
    after = sorted(p.name for p in tmp_path.iterdir() if p.name not in ("result.json", "driver"))
    assert after == before  # no capture root or other file appeared


def _assert_nothing_loaded(result, artifact):
    assert result["rc"] == 64
    assert result["path"] == result["base_path"]  # lib/ never reached sys.path
    assert not [f for f in result["modules"].values() if f.startswith(str(artifact / "lib"))]
    assert LOADED not in result["modules"]


@pytest.mark.parametrize(
    "env",
    [
        {},
        {"INVOCATION_ID": ""},
        {"INVOCATION_ID": INVOCATION_ID.upper()},
        {"INVOCATION_ID": INVOCATION_ID[:-1]},
        {"INVOCATION_ID": INVOCATION_ID + "0"},
        {"INVOCATION_ID": INVOCATION_ID[:8] + "-" + INVOCATION_ID[9:]},
    ],
    ids=["absent", "empty", "uppercase", "short", "long", "dashed"],
)
def test_a_missing_or_malformed_invocation_id_is_refused_before_any_import(artifact, tmp_path, env):
    proc, result = _run(artifact, tmp_path, env=env)
    assert proc.returncode == 64, proc.stderr
    _assert_nothing_loaded(result, artifact)


@pytest.mark.parametrize(
    "argv", [[], ["run"], ["run", "--pass", "B"], ["run", "--pass", "A", "x"], ["hold", "--pass", "A"]]
)
def test_only_the_one_argument_vector_is_accepted(artifact, tmp_path, argv):
    proc, result = _run(artifact, tmp_path, argv=argv)
    assert proc.returncode == 64, proc.stderr
    _assert_nothing_loaded(result, artifact)


# -- an untrusted or tampered bundle is rejected before anything is imported -----


def test_a_bundle_not_owned_by_root_is_refused_for_a_non_root_caller_too(artifact, tmp_path):
    if os.geteuid() == 0:
        pytest.skip("as root the test tree is root-owned")
    marker = artifact.parent / "EVIL-RAN"
    (artifact / "lib/tools/phase_5_0_evidence/errors.py").write_text(f"open({str(marker)!r}, 'w')\n")
    proc = subprocess.run(
        [sys.executable, "-I", "-S", str(artifact / "rp11_entry.py"), *ARGV],
        capture_output=True,
        text=True,
        env={"INVOCATION_ID": INVOCATION_ID},
        cwd="/",
    )
    assert proc.returncode == 77, proc.stderr
    assert "owner uid" in proc.stderr or "writable" in proc.stderr
    assert not marker.exists()


def _entry_for(artifact: Path, monkeypatch):
    module = _load(f"rp11_entry_{abs(hash(artifact))}", artifact / "rp11_entry.py")
    monkeypatch.setattr(module, "_required_owner", lambda: os.getuid())
    monkeypatch.setattr(module, "_ancestors_problem", lambda d, o: None)
    return module


def _tamper_mode(path, mode):
    def apply(artifact):
        os.chmod(artifact / path, mode)

    return apply


def _tamper_symlink(artifact):
    target = artifact / "lib/tools/phase_5_0_evidence/errors.py"
    elsewhere = artifact.parent / "elsewhere.py"
    os.rename(target, elsewhere)
    target.symlink_to(elsewhere)


def _tamper_fifo(artifact):
    os.mkfifo(artifact / "lib/tools/fifo.py")


def _tamper_extra_writable(artifact):
    stray = artifact / "lib/tools/stray.py"
    stray.write_text("")
    os.chmod(stray, 0o666)


@pytest.mark.parametrize(
    "tamper",
    [
        _tamper_mode("lib/tools/phase_5_0_evidence/capture_contract.py", 0o664),
        _tamper_mode("lib/tools/phase_5_0_evidence/execution", 0o775),
        _tamper_mode("lib/tools", 0o777),
        _tamper_mode("lib", 0o777),
        _tamper_mode("rp11_entry.py", 0o666),
        _tamper_symlink,
        _tamper_fifo,
        _tamper_extra_writable,
    ],
    ids=["file", "subdir", "tools", "lib", "entry", "symlink", "fifo", "stray"],
)
def test_a_tampered_bundle_is_refused_before_lib_reaches_sys_path_or_anything_is_imported(
    artifact, monkeypatch, tamper
):
    marker = artifact.parent / "EVIL-RAN"
    module = _entry_for(artifact, monkeypatch)
    tamper(artifact)
    sentinel = artifact / "lib/tools/phase_5_0_evidence/errors.py"
    if sentinel.is_file() and not sentinel.is_symlink():
        os.chmod(sentinel, 0o644)
        sentinel.write_text(f"open({str(marker)!r}, 'w')\n")
        os.chmod(sentinel, 0o644)
    before = list(sys.path)
    modules = set(sys.modules)
    assert module.main(ARGV) == 77
    assert not marker.exists()
    assert sys.path == before
    assert set(sys.modules) == modules


def test_the_owner_branch_refuses_an_object_of_another_uid(artifact, monkeypatch):
    module = _entry_for(artifact, monkeypatch)
    if os.geteuid() == 0:
        # Root-owned objects are always accepted, so give one object a foreign owner.
        os.chown(artifact / "lib/tools/phase_5_0_evidence/errors.py", 65534, -1)
    monkeypatch.setattr(module, "_required_owner", lambda: os.getuid() + 1)
    before = list(sys.path)
    assert module.main(ARGV) == 77
    assert sys.path == before


def test_a_clean_tree_is_accepted_for_its_owner_and_refused_for_root(artifact):
    module = _load("rp11_entry_clean", artifact / "rp11_entry.py")
    assert module._tree_problem(str(artifact), os.getuid()) is None
    if os.geteuid() != 0:
        assert f"owner uid {os.getuid()}" in module._tree_problem(str(artifact), 0)
