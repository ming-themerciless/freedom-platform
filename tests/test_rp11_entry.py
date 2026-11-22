"""RP-11 Pass A capture entry (``rp11_entry.py``): bootstrap isolation and closure.

G12 (module loading under the isolated launcher). The entry is inert; these tests
prove the loading substrate only: the artifact closure is exactly what the entry
imports, the entry's shared first-image and tree checks equal ``rp11_h1.py``'s,
an unsafe artifact is refused with status 77 *before* any artifact module is
imported, and a good artifact is imported only from its own ``lib/``.

No test needs the real wheel, root, a host service or the network; the artifact is
built from the synthetic wheel of ``test_rp11_h1_artifact`` into ``tmp_path``.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.test_rp11_h1_artifact import GOOD_MEMBERS, WHEEL_NAME, make_wheel

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / "infra/rp11-h1"
ENTRY_PATH = HERE / "rp11_entry.py"
LOADED = "tools.phase_5_0_evidence.execution.capture_mechanism"
#: Not imported by the (inert) entry yet; a second closure root so the eventual entry
#: finds the G11 start-time binding, and the journal modules it uses, in ``lib/``.
START_BINDING = "tools.phase_5_0_evidence.execution.start_binding"
INVOCATION_ID = "0123456789abcdef0123456789abcdef"
RUN = ["run", "--pass", "A"]
#: Top-level packages of this repository the entry's closure may contain.
REPO_PACKAGES = ("tools", "application")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    previous, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


build = _load("rp11_entry_build", HERE / "build.py")
entry_source = _load("rp11_entry_source", ENTRY_PATH)


# --- the closure: ENTRY_SOURCES equals what the entry imports, by AST --------------


def _module_file(module: str) -> Path | None:
    """The repository file for a dotted module name, or ``None`` if not ours."""
    if module.split(".")[0] not in REPO_PACKAGES:
        return None
    base = ROOT.joinpath(*module.split("."))
    if base.is_dir():
        return base / "__init__.py"
    candidate = base.with_suffix(".py")
    return candidate if candidate.is_file() else None


def _imported_modules(path: Path, module: str) -> set[str]:
    """Every module a file imports, anywhere in it (TYPE_CHECKING and lazy included).

    Over-approximating is the safe direction: an import that never runs would only
    add a file, and a test that compared less would let a real one go missing."""
    package = module if path.name == "__init__.py" else module.rpartition(".")[0]
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                anchor = package.split(".")
                anchor = anchor[: len(anchor) - (node.level - 1)]
                base = ".".join(anchor + ([node.module] if node.module else []))
            else:
                base = node.module or ""
            names.add(base)
            names.update(f"{base}.{alias.name}" for alias in node.names)
    return names


def _closure(start: str) -> tuple[set[str], set[str]]:
    """``(repository files, third-party top-level names)`` reachable from ``start``.

    Importing ``a.b.c`` also imports the ``__init__.py`` of ``a`` and ``a.b``."""
    files: set[str] = set()
    outside: set[str] = set()
    pending = [start]
    seen: set[str] = set()
    stdlib = set(sys.stdlib_module_names)
    while pending:
        module = pending.pop()
        if module in seen:
            continue
        seen.add(module)
        path = _module_file(module)
        if path is None:
            top = module.split(".")[0]
            # ``from pkg.mod import name`` also yields ``pkg.mod.name``: an
            # attribute of a repository module, not a module and not third-party.
            if top and top not in stdlib and top not in REPO_PACKAGES and top != "__future__":
                outside.add(top)
            continue
        parts = module.split(".")
        for depth in range(1, len(parts)):
            pending.append(".".join(parts[:depth]))
        files.add(str(path.relative_to(ROOT)))
        pending.extend(_imported_modules(path, module))
    return files, outside


def test_the_entry_loads_exactly_the_one_declared_module():
    assert entry_source._LOADED == LOADED
    imports = _imported_modules(ENTRY_PATH, "rp11_entry")
    assert [name for name in imports if name.split(".")[0] in REPO_PACKAGES] == [LOADED]


def test_entry_sources_equal_the_ast_closure_of_the_loaded_module_in_both_directions():
    files, third_party = _closure(LOADED)
    binding_files, binding_third_party = _closure(START_BINDING)
    files |= binding_files
    third_party |= binding_third_party
    declared = set(build.ENTRY_SOURCES)
    assert files - set(build.SOURCES) == declared, (
        f"missing {sorted(files - set(build.SOURCES) - declared)}, "
        f"extra {sorted(declared - files)}"
    )
    assert third_party == set(), f"third-party imports in the entry closure: {third_party}"


def test_entry_sources_are_unique_real_files_and_do_not_overlap_the_role_sources():
    assert len(build.ENTRY_SOURCES) == len(set(build.ENTRY_SOURCES))
    assert not set(build.ENTRY_SOURCES) & set(build.SOURCES)
    for source in build.ENTRY_SOURCES:
        assert (ROOT / source).is_file() and not (ROOT / source).is_symlink(), source
        assert source.endswith(".py") and not source.startswith(("/", "."))


def test_the_closure_stays_independent_of_the_launcher_and_the_role_modules():
    # The capture mechanism must not pull the launcher module or consume roles in.
    assert "tools/phase_5_0_evidence/rp11_launch.py" not in build.ENTRY_SOURCES
    assert not any(source.startswith("application/rp11/") for source in build.ENTRY_SOURCES)


# --- the shared checks are the very ones rp11_h1.py runs --------------------------

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


def _functions(path: Path) -> dict[str, str]:
    tree = ast.parse(path.read_text())
    return {
        node.name: ast.dump(node)
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }


def test_the_shared_first_image_and_tree_checks_equal_rp11_h1s():
    entry, role = _functions(ENTRY_PATH), _functions(HERE / "rp11_h1.py")
    for name in SHARED:
        assert name in entry and name in role, name
        assert entry[name] == role[name], f"{name} differs between rp11_entry.py and rp11_h1.py"


def test_the_shared_constants_equal_rp11_h1s():
    role = _load("rp11_h1_for_constants", HERE / "rp11_h1.py")
    for name in ("_MAX_ENVIRON", "_OWN_FDS", "_HEX", "_WRITABLE_BY_OTHERS", "_MAX_TREE_ENTRIES"):
        assert getattr(entry_source, name) == getattr(role, name), name


def test_the_entry_never_wires_the_capture_session_or_the_launcher():
    """The safety sentinel stays authoritative; this is the entry-side restatement."""
    text = ENTRY_PATH.read_text()
    code = "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    )
    tree = ast.parse(text)
    docstring_free = [n for n in ast.walk(tree) if isinstance(n, (ast.Name, ast.Attribute))]
    used = {getattr(n, "id", None) or getattr(n, "attr", None) for n in docstring_free}
    assert not used & {"create_capture_session", "StreamCaptureLauncher", "ActRequest", "subprocess"}
    assert "subprocess" not in code.replace("starts no process", "")


def test_the_entry_requires_root_whoever_runs_it():
    assert entry_source._required_owner() == 0


# --- argument and INVOCATION_ID grammar, before anything is imported --------------


def test_the_entry_has_no_role_vectors_only_the_pass_a_vector():
    assert entry_source.ACCEPTED_ARGV == RUN


@pytest.fixture
def artifact(tmp_path, monkeypatch):
    source = tmp_path / "wheel"
    source.mkdir()
    wheel = make_wheel(source / WHEEL_NAME, GOOD_MEMBERS)
    digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    monkeypatch.setattr(build, "pinned_wheel", lambda: (WHEEL_NAME, digest))
    return build.build(source / WHEEL_NAME, tmp_path / "artifact")


def _driver(artifact: Path, *, patch_owner: bool) -> list[str]:
    """``python -I -S -c`` that runs the *built* entry, as the launcher would.

    With ``patch_owner`` the entry's two environment-dependent checks (it must be
    root-owned, and the tmp ancestors are not) are replaced so the good path can be
    exercised by an unprivileged test; every other check is the entry's own."""
    code = f"""
import importlib.util, sys
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("rp11_entry_built", {str(artifact / "rp11_entry.py")!r})
entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)
if {patch_owner!r}:
    entry._required_owner = lambda: {os.getuid()}
    entry._ancestors_problem = lambda directory, owner: None
status = entry.entry()
lib = {str(artifact / "lib")!r}
origins = sorted(
    getattr(m, "__file__", "") or ""
    for name, m in list(sys.modules.items())
    if name.split(".")[0] in ("tools", "application")
)
print("ORIGINS", *origins, sep="\\n", file=sys.stderr)
print("PATH", *sys.path, sep="\\n", file=sys.stderr)
sys.exit(status)
"""
    return [sys.executable, "-I", "-S", "-c", code, *RUN]


def _run(artifact, *, env, cwd="/", patch_owner=False, argv=None):
    command = _driver(artifact, patch_owner=patch_owner)
    if argv is not None:
        command = command[:-3] + list(argv)
    return subprocess.run(command, capture_output=True, text=True, env=env, cwd=cwd)


def _good_env(**extra):
    return {"INVOCATION_ID": INVOCATION_ID, **extra}


def test_the_build_installs_the_entry_and_the_closure_beside_the_role_entry(artifact):
    assert (artifact / "rp11_entry.py").read_bytes() == ENTRY_PATH.read_bytes()
    assert (artifact / "rp11_h1.py").is_file()
    for source in build.ENTRY_SOURCES:
        assert (artifact / "lib" / source).read_bytes() == (ROOT / source).read_bytes(), source
    assert (artifact / "rp11_entry.py").stat().st_mode & 0o777 == 0o644
    assert not list(artifact.rglob("__pycache__"))


@pytest.mark.parametrize(
    "argv",
    [
        ["run"],
        ["run", "--pass", "B"],
        ["run", "--pass", "a"],
        ["run", "--pass", "A", "extra"],
        ["hold", "x", "y"],
        ["consume"],
        [],
    ],
)
def test_any_other_vector_is_refused_with_64_before_any_import(artifact, argv):
    proc = _run(artifact, env=_good_env(), patch_owner=True, argv=argv)
    assert proc.returncode == 64, proc.stderr
    assert "not the accepted vector" in proc.stderr
    assert "ORIGINS" in proc.stderr and "tools" not in proc.stderr.split("PATH")[0]


@pytest.mark.parametrize(
    "env",
    [
        {},
        {"INVOCATION_ID": "not-hex"},
        {"INVOCATION_ID": "A" * 32},
        {"INVOCATION_ID": "a" * 31},
        {"INVOCATION_ID": "a" * 33},
        {"INVOCATION_ID": ""},
    ],
    ids=["absent", "not-hex", "upper", "short", "long", "empty"],
)
def test_a_missing_or_malformed_invocation_id_is_refused_with_64_before_any_import(artifact, env):
    proc = _run(artifact, env=env, patch_owner=True)
    assert proc.returncode == 64, proc.stderr
    assert "INVOCATION_ID must be present exactly once" in proc.stderr
    assert "capture_mechanism" not in proc.stderr


# --- unsafe or tampered artifact: refused before import ---------------------------

MARKER_NAME = "ENTRY-IMPORTED"


def _plant(artifact: Path, relative: str) -> Path:
    """Replace one closure module with code that proves it was imported."""
    marker = artifact.parent / MARKER_NAME
    target = artifact / "lib" / relative
    os.chmod(target, 0o644)
    target.write_bytes(f"open({str(marker)!r}, 'w').close()\n".encode())
    return marker


def _refused_before_import(proc, marker: Path, *, fragment: str) -> None:
    assert proc.returncode == 77, proc.stderr
    assert "artifact is not root-owned and protected" in proc.stderr
    assert fragment in proc.stderr, proc.stderr
    assert not marker.exists(), "artifact code ran before the tree was refused"


def test_a_tree_that_is_not_root_owned_is_refused_before_any_import(artifact):
    """No patching: the entry demands root ownership whoever runs it, and this
    artifact belongs to the test user (or lies under a world-writable ancestor)."""
    marker = _plant(artifact, "tools/phase_5_0_evidence/execution/capture_mechanism.py")
    if os.geteuid() == 0:
        # Run as root the whole synthetic tree is root-owned, which the entry
        # rightly accepts; make one closure file genuinely belong to an
        # unprivileged uid so the ownership refusal is what is exercised.
        os.chown(
            artifact / "lib/tools/phase_5_0_evidence/execution/capture_mechanism.py",
            65534,
            -1,
        )
    proc = _run(artifact, env=_good_env())
    assert proc.returncode == 77, proc.stderr
    assert not marker.exists()


@pytest.mark.parametrize(
    "target,mode",
    [
        ("lib/tools/phase_5_0_evidence/execution/capture_mechanism.py", 0o664),
        ("lib/tools/phase_5_0_evidence/capture_contract.py", 0o646),
        ("lib/application/idempotency.py", 0o666),
        ("lib/tools/phase_5_0_evidence/execution", 0o775),
        ("lib/tools", 0o777),
        ("lib", 0o777),
        ("rp11_entry.py", 0o664),
    ],
)
def test_a_group_or_other_writable_object_is_refused_before_any_import(artifact, target, mode):
    marker = _plant(artifact, "tools/phase_5_0_evidence/execution/capture_mechanism.py")
    os.chmod(artifact / target, mode)
    proc = _run(artifact, env=_good_env(), patch_owner=True)
    _refused_before_import(proc, marker, fragment="group or other writable")


@pytest.mark.parametrize(
    "target",
    [
        "lib/tools/phase_5_0_evidence/execution/capture_mechanism.py",
        "lib/tools/phase_5_0_evidence/execution",
        "lib/tools",
        "lib/application",
    ],
)
def test_a_symlinked_object_is_refused_before_any_import(artifact, tmp_path, target):
    marker = _plant(artifact, "tools/phase_5_0_evidence/execution/capture_mechanism.py")
    path = artifact / target
    elsewhere = tmp_path / "elsewhere"
    os.rename(path, elsewhere)
    path.symlink_to(elsewhere)
    proc = _run(artifact, env=_good_env(), patch_owner=True)
    _refused_before_import(proc, marker, fragment="symlink")


def test_a_non_regular_object_is_refused_before_any_import(artifact):
    marker = _plant(artifact, "tools/phase_5_0_evidence/execution/capture_mechanism.py")
    os.mkfifo(artifact / "lib/tools/fifo.py")
    proc = _run(artifact, env=_good_env(), patch_owner=True)
    _refused_before_import(proc, marker, fragment="not a regular file")


def test_an_object_owned_by_anyone_but_root_or_the_owner_is_refused(artifact):
    """The owner check proper: with the required owner set to a uid that is not the
    artifact's, every object fails. (``0`` stays accepted, as for rp11_h1.py.)"""
    marker = _plant(artifact, "tools/phase_5_0_evidence/execution/capture_mechanism.py")
    other = os.getuid() + 1 if os.getuid() else 1
    proc = subprocess.run(
        [
            sys.executable, "-I", "-S", "-c",
            "import importlib.util, sys\nsys.dont_write_bytecode = True\n"
            f"s = importlib.util.spec_from_file_location('e', {str(artifact / 'rp11_entry.py')!r})\n"
            "e = importlib.util.module_from_spec(s); s.loader.exec_module(e)\n"
            f"e._required_owner = lambda: {other}\n"
            "e._ancestors_problem = lambda d, o: None\n"
            "sys.exit(e.entry())\n",
            *RUN,
        ],
        capture_output=True, text=True, env=_good_env(), cwd="/",
    )
    if os.getuid() == 0:
        pytest.skip("root-owned objects are accepted for every required owner")
    _refused_before_import(proc, marker, fragment="owner uid")


def test_an_oversized_tree_is_refused_before_any_import(artifact):
    marker = _plant(artifact, "tools/phase_5_0_evidence/execution/capture_mechanism.py")
    for number in range(entry_source._MAX_TREE_ENTRIES):
        stray = artifact / "lib" / f"stray{number}.txt"
        stray.write_bytes(b"")
        os.chmod(stray, 0o644)  # only the entry count may refuse this tree
    proc = _run(artifact, env=_good_env(), patch_owner=True)
    _refused_before_import(proc, marker, fragment="entries")


def test_a_missing_lib_is_refused_before_any_import(artifact):
    import shutil

    shutil.rmtree(artifact / "lib")
    proc = _run(artifact, env=_good_env(), patch_owner=True)
    assert proc.returncode == 77, proc.stderr


# --- a good artifact: imports come from its own lib/ closure only -----------------


def test_a_good_artifact_imports_only_from_its_own_closure_and_stays_inert(artifact, tmp_path):
    hostile = tmp_path / "hostile"
    for relative in ("tools/phase_5_0_evidence/execution", "application"):
        (hostile / relative).mkdir(parents=True)
    marker = hostile / "PLANTED-IMPORTED"
    for relative in (
        "tools/__init__.py",
        "tools/phase_5_0_evidence/__init__.py",
        "tools/phase_5_0_evidence/execution/__init__.py",
        "tools/phase_5_0_evidence/execution/capture_mechanism.py",
        "application/__init__.py",
        "application/idempotency.py",
    ):
        (hostile / relative).write_text(f"open({str(marker)!r}, 'w').close()\n")
    # A stray module inside the artifact that the closure does not name.
    stray = artifact / "lib/tools/phase_5_0_evidence/stray.py"
    stray_marker = tmp_path / "STRAY-IMPORTED"
    stray.write_text(f"open({str(stray_marker)!r}, 'w').close()\n")
    os.chmod(stray, 0o644)

    proc = _run(
        artifact,
        env=_good_env(PYTHONPATH=str(hostile), PYTHONSTARTUP=str(hostile), PYTHONHOME="/nonexistent"),
        cwd=str(hostile),
        patch_owner=True,
    )
    assert proc.returncode == 69, proc.stderr
    assert "not implemented in this build" in proc.stderr
    assert not marker.exists() and not stray_marker.exists()

    origins, _, path_part = proc.stderr.partition("ORIGINS\n")[2].partition("PATH\n")
    loaded = [line for line in origins.splitlines() if line]
    lib = str(artifact / "lib")
    assert loaded and all(line.startswith(lib + os.sep) for line in loaded), loaded
    # The closure plus the role sources' ``application`` package marker it also needs.
    expected = {
        str(artifact / "lib" / source)
        for source in (*build.ENTRY_SOURCES, "application/__init__.py")
    }
    assert set(loaded) <= expected, sorted(set(loaded) - expected)
    assert str(artifact / "lib/tools/phase_5_0_evidence/execution/capture_mechanism.py") in loaded
    # lib is appended after the standard library, never ahead of it; the hostile
    # directory, the working directory and the artifact directory are not on it.
    paths = [line for line in path_part.splitlines() if line]
    assert paths[-1] == lib and paths.count(lib) == 1
    assert str(hostile) not in paths and str(artifact) not in paths and "" not in paths
    assert not list(artifact.rglob("__pycache__"))


def test_the_good_run_starts_no_process_and_creates_no_file(artifact, tmp_path):
    before = sorted(p for p in tmp_path.rglob("*"))
    proc = _run(artifact, env=_good_env(), patch_owner=True, cwd=str(tmp_path))
    assert proc.returncode == 69, proc.stderr
    assert sorted(p for p in tmp_path.rglob("*")) == before
    assert "rp11_entry:" in proc.stderr


# --- the raw initial environment is the only source of INVOCATION_ID ---------------

def _deny_proc_environ(monkeypatch):
    real_open = os.open

    def fake_open(path, *args, **kwargs):
        if path == "/proc/self/environ":
            raise PermissionError(13, "denied", path)
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(os, "open", fake_open)


@pytest.mark.parametrize("module_path", [ENTRY_PATH, HERE / "rp11_h1.py"], ids=["entry", "role"])
def test_an_unreadable_proc_self_environ_is_not_replaced_by_the_mapped_environment(
    module_path, monkeypatch, capsys
):
    """os.environ is normalised and cannot show a duplicate INVOCATION_ID, so a
    valid-looking mapped value must not be accepted when the raw block is unreadable."""
    module = _load("rp11_environ_fallback_probe", module_path)
    monkeypatch.setenv("INVOCATION_ID", INVOCATION_ID)
    _deny_proc_environ(monkeypatch)
    assert module._initial_environment() is None
    cleared = []
    monkeypatch.setattr(os.environ, "clear", lambda: cleared.append(True))
    assert module.first_image_controls() == module.EX_USAGE
    assert not cleared, "the environment must not be cleared after a refusal"
    assert "INVOCATION_ID" in capsys.readouterr().err


def test_a_failed_read_of_proc_self_environ_is_refused_not_truncated(monkeypatch):
    module = _load("rp11_environ_read_probe", ENTRY_PATH)

    def failing_read(fd, n):
        raise OSError(5, "I/O error")

    monkeypatch.setattr(os, "read", failing_read)
    assert module._initial_environment() is None


_ID_A = "a" * 32
_ID_B = "b" * 32


@pytest.mark.parametrize("module_path", [ENTRY_PATH, HERE / "rp11_h1.py"], ids=["entry", "role"])
@pytest.mark.parametrize(
    "block",
    [
        pytest.param(
            f"INVOCATION_ID={_ID_A}\0INVOCATION_ID={_ID_A}\0".encode(), id="identical-duplicate"
        ),
        pytest.param(
            f"INVOCATION_ID={_ID_A}\0INVOCATION_ID={_ID_B}\0".encode(), id="conflicting"
        ),
        pytest.param(
            f"PATH=/bin\0INVOCATION_ID={_ID_A}\0LANG=C\0INVOCATION_ID={_ID_A}".encode(),
            id="identical-duplicate-separated-no-trailing-nul",
        ),
    ],
)
def test_two_raw_invocation_id_entries_are_refused_even_when_identical(module_path, block):
    """The reason the raw /proc/self/environ block is parsed: os.environ collapses
    duplicates, so only the raw block can show two INVOCATION_ID entries."""
    module = _load("rp11_duplicate_invocation_probe", module_path)
    assert module.invocation_id_from(block) is None
    # the single well-formed value is still accepted (the refusal is the duplicate)
    assert module.invocation_id_from(f"INVOCATION_ID={_ID_A}\0".encode()) == _ID_A
