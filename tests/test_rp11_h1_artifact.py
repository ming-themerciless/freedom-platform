"""RP-11 H-1 controlled artifact: builder integrity checks and entry-point grammar.

The real build, the exact ``/usr/bin/python3.14 -I -S`` runtime and PID 1
execution are exercised as root on the disposable host by
``tests/systemd_integration``; these tests need neither the wheel nor root.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import json
import os
import resource
import signal
import shutil
import stat
import subprocess
import sys
import warnings
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / "infra/rp11-h1"
ACT = "rp11-act-20261012T101500Z-0a1b2c3d"
A2 = "0123456789abcdef" * 4


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    previous, sys.dont_write_bytecode = sys.dont_write_bytecode, True  # keep trees clean
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


build = _load("rp11_h1_build", HERE / "build.py")
entry = _load("rp11_h1_entry", HERE / "rp11_h1.py")


def test_artifact_carries_exactly_the_adapter_the_roles_and_their_boundary():
    expected = {"application/__init__.py", "application/unit_control.py", "adapters/__init__.py"}
    for package in ("adapters/systemd", "adapters/rp11", "application/rp11"):
        expected |= {str(p.relative_to(ROOT)) for p in (ROOT / package).glob("*.py")}
    assert set(build.SOURCES) == expected
    assert len(build.SOURCES) == len(set(build.SOURCES))


def test_lock_pins_one_hashed_wheel_inside_the_declared_range():
    filename, digest = build.pinned_wheel()
    assert filename == "jeepney-0.9.0-py3-none-any.whl"
    assert digest == "97e5714520c16fc0a45695e5365a2e11b81ea79bba796e26f9f1d178cb182683"
    assert "jeepney>=0.9,<0.10" in (HERE / "requirements.txt").read_text()


def test_web_runtime_set_no_longer_carries_the_client():
    for name in ("requirements-web.txt", "requirements-web.lock"):
        assert "jeepney" not in (ROOT / name).read_text().lower(), name


def test_a_wheel_with_the_wrong_name_or_hash_is_refused_and_nothing_is_built(tmp_path):
    impostor = tmp_path / "jeepney-0.9.0-py3-none-any.whl"
    impostor.write_bytes(b"not the pinned wheel")
    renamed = tmp_path / "jeepney-0.9.1-py3-none-any.whl"
    renamed.write_bytes(b"x")
    dest = tmp_path / "artifact"
    for wheel in (impostor, renamed):
        with pytest.raises(build.BuildError):
            build.build(wheel, dest)
    assert not dest.exists()
    assert set(tmp_path.iterdir()) == {impostor, renamed}  # no staging left behind


def test_an_existing_destination_is_refused(tmp_path, monkeypatch):
    wheel = tmp_path / "jeepney-0.9.0-py3-none-any.whl"
    wheel.write_bytes(b"w")
    monkeypatch.setattr(
        build, "pinned_wheel", lambda: (wheel.name, hashlib.sha256(b"w").hexdigest())
    )
    dest = tmp_path / "artifact"
    dest.mkdir()
    with pytest.raises(build.BuildError):
        build.build(wheel, dest)


# --- synthetic pinned wheel --------------------------------------------------

WHEEL_NAME = "jeepney-0.9.0-py3-none-any.whl"
# Just enough of jeepney for the adapter modules to import under -I -S.
GOOD_MEMBERS = {
    "jeepney/__init__.py": (
        b"__version__ = '0.9.0'\n"
        b"DBusAddress = HeaderFields = MatchRule = MessageType = None\n"
        b"message_bus = new_method_call = None\n"
    ),
    "jeepney/io/__init__.py": b"",
    "jeepney/io/blocking.py": b"DBusConnection = open_dbus_connection = None\n",
    "jeepney-0.9.0.dist-info/METADATA": b"Name: jeepney\nVersion: 0.9.0\n",
    "jeepney-0.9.0.dist-info/WHEEL": b"Wheel-Version: 1.0\n",
    "jeepney-0.9.0.dist-info/RECORD": b"",
    "jeepney-0.9.0.dist-info/licenses/LICENSE": b"MIT\n",
}
EVIL = b"open('/proc/self/cwd/EVIL-RAN', 'w')\n"


def make_wheel(path: Path, members: dict[str, bytes], infos=()) -> Path:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # duplicate names are a deliberate fixture
        with zipfile.ZipFile(path, "w") as archive:
            for name, data in members.items():
                archive.writestr(name, data)
            for info, data in infos:
                archive.writestr(info, data)
    return path


def pin(monkeypatch, wheel: Path) -> None:
    digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    monkeypatch.setattr(build, "pinned_wheel", lambda: (WHEEL_NAME, digest))


@pytest.fixture
def wheels(tmp_path, monkeypatch):
    """``(good wheel pinned, workdir)``; the wheel lives in its own directory."""
    source = tmp_path / "wheel"
    source.mkdir()
    good = make_wheel(source / WHEEL_NAME, GOOD_MEMBERS)
    pin(monkeypatch, good)
    return good, tmp_path


def lib_bytes(dest: Path, name: str) -> bytes:
    return (dest / "lib" / name).read_bytes()


def assert_nothing_built(workdir: Path, dest: Path) -> None:
    assert not dest.exists()
    assert [p.name for p in workdir.iterdir() if p.name.startswith(".")] == []  # no staging


def test_build_unpacks_exactly_the_pinned_bytes_with_safe_modes(wheels):
    good, workdir = wheels
    dest = build.build(good, workdir / "artifact")
    for name, data in GOOD_MEMBERS.items():
        assert lib_bytes(dest, name) == data
    assert lib_bytes(dest, "rp11_roles.py") == (HERE / "rp11_roles.py").read_bytes()
    assert (dest / "rp11_h1.py").read_bytes() == (HERE / "rp11_h1.py").read_bytes()
    for path in [dest, *dest.rglob("*")]:
        mode = stat.S_IMODE(path.lstat().st_mode)
        assert not path.is_symlink()
        assert mode == (0o755 if path.is_dir() else 0o644), path
    assert entry_for(dest)._tree_problem(str(dest), os.getuid()) is None


# Security remediation finding 2: the bytes extracted must be the bytes hashed.


class _SwappingHashlib:
    """``hashlib`` whose ``sha256`` replaces the wheel on disk once it has hashed."""

    def __init__(self, wheel: Path, replacement: Path) -> None:
        self.wheel, self.replacement, self.swapped = wheel, replacement, False

    def sha256(self, data=b""):
        digest = hashlib.sha256(data)
        if not self.swapped:
            os.replace(self.replacement, self.wheel)
            self.swapped = True
        return digest


def test_a_wheel_replaced_after_hashing_cannot_enter_the_artifact(wheels, monkeypatch):
    good, workdir = wheels
    evil_members = {**GOOD_MEMBERS, "jeepney/__init__.py": EVIL, "rp11_roles.py": EVIL}
    evil = make_wheel(workdir / "evil.whl", evil_members)
    swapper = _SwappingHashlib(good, evil)
    monkeypatch.setattr(build, "hashlib", swapper)
    try:
        dest = build.build(good, workdir / "artifact")
    except build.BuildError:
        assert_nothing_built(workdir, workdir / "artifact")
        return
    assert swapper.swapped  # the wheel path now holds the evil wheel
    assert lib_bytes(dest, "jeepney/__init__.py") == GOOD_MEMBERS["jeepney/__init__.py"]
    assert lib_bytes(dest, "rp11_roles.py") == (HERE / "rp11_roles.py").read_bytes()
    assert EVIL not in b"".join(p.read_bytes() for p in dest.rglob("*") if p.is_file())


def test_a_wheel_modified_in_place_while_held_fails_closed(wheels, monkeypatch):
    good, workdir = wheels
    real_read = build._read_fd

    def read_then_mutate(fd):
        data = real_read(fd)
        with open(good, "ab") as handle:
            handle.write(b"appended after the read")
        return data

    monkeypatch.setattr(build, "_read_fd", read_then_mutate)
    with pytest.raises(build.BuildError, match="changed"):
        build.build(good, workdir / "artifact")
    assert_nothing_built(workdir, workdir / "artifact")


def test_bytes_read_during_an_in_place_rewrite_fail_the_hash(wheels, monkeypatch):
    good, workdir = wheels
    real_read = build._read_fd
    def torn(fd):
        data = real_read(fd)
        return data[:-1] + bytes([data[-1] ^ 0xFF])  # same length, different bytes

    monkeypatch.setattr(build, "_read_fd", torn)
    with pytest.raises(build.BuildError, match="SHA-256"):
        build.build(good, workdir / "artifact")
    assert_nothing_built(workdir, workdir / "artifact")


def test_a_symlinked_or_non_regular_wheel_is_refused(wheels):
    good, workdir = wheels
    links = workdir / "links"
    links.mkdir()
    (links / WHEEL_NAME).symlink_to(good)
    folder = workdir / "folder" / WHEEL_NAME
    folder.mkdir(parents=True)
    fifo_dir = workdir / "fifo"
    fifo_dir.mkdir()
    os.mkfifo(fifo_dir / WHEEL_NAME)
    for wheel in (links / WHEEL_NAME, folder, fifo_dir / WHEEL_NAME):
        with pytest.raises(build.BuildError):
            build.build(wheel, workdir / "artifact")
        assert not (workdir / "artifact").exists()


def test_an_oversized_wheel_is_refused_before_it_is_read(wheels, monkeypatch):
    good, workdir = wheels
    monkeypatch.setattr(build, "_MAX_WHEEL_BYTES", good.stat().st_size - 1)
    with pytest.raises(build.BuildError, match="large"):
        build.build(good, workdir / "artifact")
    assert_nothing_built(workdir, workdir / "artifact")


@pytest.mark.parametrize(
    "member",
    [
        # trusted artifact paths
        "application/unit_control.py",
        "application/__init__.py",
        "adapters/systemd/manager.py",
        "rp11_roles.py",
        "rp11_h1.py",
        # unexpected top-level members and look-alike namespaces
        "evil/__init__.py",
        "sitecustomize.py",
        "jeepney.py",
        "jeepney_extra/__init__.py",
        "Jeepney/__init__.py",
        "jeepney-0.9.1.dist-info/METADATA",
        "jeepney-0.9.0.data/scripts/x",
        # traversal and non-canonical names
        "../escape.py",
        "/etc/escape.py",
        "a/../../escape.py",
        "jeepney/../rp11_roles.py",
        "jeepney/./x.py",
        "jeepney//x.py",
        "jeepney/sub\\x.py",
    ],
)
def test_a_member_outside_the_jeepney_namespaces_is_refused(wheels, monkeypatch, member):
    _good, workdir = wheels
    bad = make_wheel(workdir / "wheel" / WHEEL_NAME, {**GOOD_MEMBERS, member: EVIL})
    pin(monkeypatch, bad)
    with pytest.raises(build.BuildError):
        build.build(bad, workdir / "artifact")
    assert_nothing_built(workdir, workdir / "artifact")
    assert not (workdir / "escape.py").exists() and not Path("/etc/escape.py").exists()


def test_a_duplicate_or_non_regular_member_is_refused(wheels, monkeypatch):
    _good, workdir = wheels
    link = zipfile.ZipInfo("jeepney/link.py")
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    fifo = zipfile.ZipInfo("jeepney/fifo")
    fifo.external_attr = (stat.S_IFIFO | 0o644) << 16
    cases = [
        (zipfile.ZipInfo("jeepney/__init__.py"), EVIL),  # a second copy of a name
        (link, b"../../rp11_roles.py"),
        (fifo, b""),
    ]
    for info in cases:
        bad = make_wheel(workdir / "wheel" / WHEEL_NAME, GOOD_MEMBERS, [info])
        pin(monkeypatch, bad)
        with pytest.raises(build.BuildError):
            build.build(bad, workdir / "artifact")
        assert_nothing_built(workdir, workdir / "artifact")


def test_member_count_and_total_size_are_bounded(wheels, monkeypatch):
    good, workdir = wheels
    monkeypatch.setattr(build, "_MAX_MEMBERS", len(GOOD_MEMBERS) - 1)
    with pytest.raises(build.BuildError):
        build.build(good, workdir / "artifact")
    monkeypatch.setattr(build, "_MAX_MEMBERS", len(GOOD_MEMBERS))
    monkeypatch.setattr(build, "_MAX_UNPACKED_BYTES", sum(map(len, GOOD_MEMBERS.values())) - 1)
    with pytest.raises(build.BuildError):
        build.build(good, workdir / "artifact")
    assert_nothing_built(workdir, workdir / "artifact")
    monkeypatch.setattr(build, "_MAX_UNPACKED_BYTES", sum(map(len, GOOD_MEMBERS.values())))
    assert build.build(good, workdir / "artifact").is_dir()


def test_the_namespaces_follow_the_pin():
    assert build._wheel_namespaces("jeepney-0.9.0-py3-none-any.whl") == (
        "jeepney",
        "jeepney-0.9.0.dist-info",
    )


def test_an_install_parent_that_others_can_change_is_reported(tmp_path):
    assert build._install_parent_problem(tmp_path) is not None  # /tmp is world-writable
    if all(p.stat().st_uid == 0 for p in (Path("/usr"), Path("/"))):
        assert build._install_parent_problem(Path("/usr")) is None


# Security remediation finding 1: the entry point refuses an unsafe tree before
# it puts lib/ on sys.path or imports anything from it.


def entry_for(dest: Path):
    return _load(f"rp11_h1_entry_{abs(hash(dest))}", dest / "rp11_h1.py")


@pytest.fixture
def artifact(wheels):
    good, workdir = wheels
    return build.build(good, workdir / "artifact")


def test_a_clean_tree_passes_for_its_owner_and_fails_for_root(artifact):
    entry = entry_for(artifact)
    assert entry._tree_problem(str(artifact), os.getuid()) is None
    problem = entry._tree_problem(str(artifact), 0)
    assert problem is not None and f"owner uid {os.getuid()}" in problem


@pytest.mark.parametrize(
    "target,change,reason",
    [
        ("lib/rp11_roles.py", 0o664, "group or other writable"),
        ("lib/rp11_roles.py", 0o646, "group or other writable"),
        ("lib/adapters/systemd/polkit.py", 0o666, "group or other writable"),
        ("lib/jeepney-0.9.0.dist-info/METADATA", 0o664, "group or other writable"),
        ("rp11_h1.py", 0o664, "group or other writable"),
        ("lib/jeepney/io", 0o757, "group or other writable"),
        ("lib/application", 0o775, "group or other writable"),
        ("lib", 0o777, "group or other writable"),
        ("lib/adapters/systemd", 0o1777, "group or other writable"),
    ],
)
def test_a_group_or_other_writable_object_anywhere_is_refused(artifact, target, change, reason):
    path = artifact / target
    os.chmod(path, change)
    problem = entry_for(artifact)._tree_problem(str(artifact), os.getuid())
    assert problem is not None and reason in problem and str(path) in problem


@pytest.mark.parametrize(
    "target",
    ["lib/rp11_roles.py", "lib/jeepney", "lib/adapters/systemd/manager.py", "lib/application"],
)
def test_a_symlink_substitution_is_refused(artifact, tmp_path, target):
    path = artifact / target
    elsewhere = tmp_path / "elsewhere"
    os.rename(path, elsewhere)
    path.symlink_to(elsewhere)
    problem = entry_for(artifact)._tree_problem(str(artifact), os.getuid())
    assert problem is not None and "symlink" in problem and str(path) in problem


def test_a_non_regular_file_is_refused(artifact):
    os.mkfifo(artifact / "lib/jeepney/io/fifo.py")
    problem = entry_for(artifact)._tree_problem(str(artifact), os.getuid())
    assert problem is not None and "not a regular file" in problem


def test_a_missing_lib_or_an_oversized_tree_is_refused(artifact, monkeypatch):
    entry = entry_for(artifact)
    monkeypatch.setattr(entry, "_MAX_TREE_ENTRIES", 5)
    assert "entries" in entry._tree_problem(str(artifact), os.getuid())
    monkeypatch.undo()
    shutil.rmtree(artifact / "lib")
    assert "lib" in entry._tree_problem(str(artifact), os.getuid())


def test_ancestors_are_checked_up_to_the_root(artifact):
    entry = entry_for(artifact)
    problem = entry._ancestors_problem(str(artifact), os.getuid())
    assert problem is not None  # /tmp, an ancestor of tmp_path, is world-writable
    if Path("/usr/bin").stat().st_uid == 0:
        assert entry._ancestors_problem("/usr/bin", 0) is None
    assert "symlink" in entry._ancestors_problem(str(_symlinked_dir(artifact)), os.getuid())


def _symlinked_dir(artifact: Path) -> Path:
    link = artifact.parent / "artifact-link"
    link.symlink_to(artifact)
    return link / "lib"


def test_an_unsafe_tree_refuses_as_root_before_any_artifact_code_runs(artifact, monkeypatch):
    """The original finding, in-process: as root, a module the root cannot vouch for
    must not run. The marker proves its top-level code did not execute."""
    marker = artifact.parent / "EVIL-RAN"
    roles = artifact / "lib/rp11_roles.py"
    os.chmod(roles, 0o644)
    roles.write_bytes(f"open({str(marker)!r}, 'w')\ndef run(*a, **k):\n    return 69\n".encode())
    entry = entry_for(artifact)
    monkeypatch.setattr(entry, "_required_owner", lambda: 0)
    before = list(sys.path)
    assert entry.main(["hold", ACT, A2]) == 77
    assert not marker.exists()
    assert sys.path == before and "rp11_roles" not in sys.modules


def test_the_marker_module_does_run_when_not_refused(artifact):
    """Control for the test above: unrefused, the same module's top-level code runs."""
    if os.geteuid() == 0:
        pytest.skip("as root this tree (not root-owned) is refused; see the test above")
    marker = artifact.parent / "EVIL-RAN"
    roles = artifact / "lib/rp11_roles.py"
    roles.write_bytes(f"open({str(marker)!r}, 'w')\ndef run(*a, **k):\n    return 69\n".encode())
    proc = subprocess.run(
        [sys.executable, "-I", "-S", str(artifact / "rp11_h1.py"), "hold", ACT, A2],
        capture_output=True,
        text=True,
        env={},
        cwd="/",
    )
    assert proc.returncode == 69, proc.stderr
    assert marker.exists()
    assert not list(artifact.rglob("__pycache__"))  # the entry writes no bytecode


def test_a_tree_problem_is_reported_by_main_as_77(artifact, monkeypatch):
    entry = entry_for(artifact)
    monkeypatch.setattr(entry, "_required_owner", lambda: os.getuid())
    monkeypatch.setattr(entry, "_ancestors_problem", lambda d, o: None)
    os.chmod(artifact / "lib/jeepney/io/blocking.py", 0o666)
    assert entry.main(["hold", ACT, A2]) == 77
    assert str(artifact / "lib") not in sys.path


@pytest.mark.parametrize(
    "argv,expected",
    [
        (["hold", ACT, A2], ("hold", ACT, A2, ())),
        (["deact", ACT, A2, "stop-post"], ("stop-post", ACT, A2, ())),
        (["backstop", ACT, A2], ("backstop", ACT, A2, ())),
        (["start", ACT, A2, "900", "60"], ("start", ACT, A2, (900, 60))),
        (["stop"], ("stop", "", "", ())),
    ],
)
def test_entry_accepts_exactly_the_five_role_vectors(argv, expected):
    assert entry.parse_role_argv(argv) == expected


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["hold"],
        ["hold", ACT],
        ["hold", ACT, A2, "extra"],
        ["deact", ACT, A2],
        ["deact", ACT, A2, "attest"],
        ["backstop", ACT, A2, "stop-post"],
        ["consume", ACT, A2],
        ["start", ACT, A2, "0", "60"],
        ["start", ACT, A2, "0900", "60"],
        ["start", ACT, A2, "900", "604801"],
        ["start", ACT, A2, "900", "60", "extra"],
        ["stop-post", ACT, A2],
        ["stop", ""],
        ["stop", "stop"],
        ["stop", ACT],
        ["stop", ACT, A2],
        ["stop", "--force"],
        ["stop", "rp11-capture-pass-a.service"],
        ["STOP"],
        ["Stop"],
        ["stop "],
        [" stop"],
        ["stop\n"],
        ["stop\x00"],
        ["--stop"],
        ["stop-capture"],
        ["hold", ACT, A2.upper()],
        ["hold", "rp11-act-x", A2],
        ["hold", A2, ACT],
        ["-c", "import os", A2],
    ],
)
def test_entry_rejects_every_other_vector(argv):
    assert entry.parse_role_argv(argv) is None


@pytest.mark.parametrize("lease", ["61", "900", "86400"])
@pytest.mark.parametrize("stop", ["60", "120", "600"])
def test_entry_accepts_both_ends_of_each_holder_duration_range(lease, stop):
    assert entry.parse_role_argv(["start", ACT, A2, lease, stop]) == ("start", ACT, A2, (int(lease), int(stop)))


@pytest.mark.parametrize(
    "lease,stop",
    [(v, "60") for v in ("0", "1", "60", "86401", "604800", "999999")]
    + [("900", v) for v in ("0", "1", "59", "601", "604800", "999999")]
    + [("604800", "1"), ("1", "604800"), ("0061", "60"), ("900", "060"), ("\u0669\u0660\u0660", "60"),
       ("900", "\u0666\u0660"), ("+900", "60"), ("900", "-60"), (" 900", "60"), ("900", "60\n"),
       ("0x384", "60"), ("9e2", "60"), ("", "60")],
)
def test_entry_refuses_a_holder_duration_outside_the_contract(lease, stop):
    assert entry.parse_role_argv(["start", ACT, A2, lease, stop]) is None


def test_hold_runs_its_composition_root_with_the_provenance(monkeypatch):
    """Role slice 3: ``hold`` is real and reaches only the holder's composition root."""
    import adapters.rp11.backstop as backstop
    import adapters.rp11.hold as hold
    import adapters.rp11.stop_post as stop_post

    def never(*a, **k):
        raise AssertionError("hold must not reach a cleanup rung itself")

    seen = {}

    def fake(activation_id, a2, **kw):
        seen.update(kw, activation_id=activation_id, a2=a2)
        return 33

    monkeypatch.setattr(stop_post, "run_stop_post", never)
    monkeypatch.setattr(backstop, "run_backstop", never)
    monkeypatch.setattr(hold, "run_hold", fake)
    roles = _load("rp11_roles_prod", HERE / "rp11_roles.py")
    assert roles.run("hold", ACT, A2, invocation_id="a" * 32, parent_pid=1) == 33
    assert seen == {"activation_id": ACT, "a2": A2, "invocation_id": "a" * 32, "parent_pid": 1}


def test_an_unknown_role_still_refuses():
    roles = _load("rp11_roles_prod4", HERE / "rp11_roles.py")
    assert roles.run("consume", ACT, A2) == 69


def test_start_runs_its_composition_root_with_only_validated_operands(monkeypatch):
    import adapters.rp11.start as start

    seen = {}

    def fake(activation_id, a2, runtime, timeout):
        seen.update(activation_id=activation_id, a2=a2, runtime=runtime, timeout=timeout)
        return 22

    monkeypatch.setattr(start, "run_start", fake)
    roles = _load("rp11_roles_start", HERE / "rp11_roles.py")
    assert roles.run("start", ACT, A2, 900, 60, invocation_id="ignored") == 22
    assert seen == {"activation_id": ACT, "a2": A2, "runtime": 900, "timeout": 60}


def test_the_entry_imports_the_start_root_up_front():
    source = (HERE / "rp11_h1.py").read_text()
    assert "import adapters.rp11.start  # noqa: F401" in source
    assert {"application/rp11/start.py", "adapters/rp11/start.py"} <= set(build.SOURCES)


def test_stop_runs_its_composition_root_with_no_operand(monkeypatch):
    import adapters.rp11.stop as stop

    calls = []

    def fake(*args, **kwargs):
        calls.append((args, kwargs))
        return 22

    monkeypatch.setattr(stop, "run_stop", fake)
    roles = _load("rp11_roles_stop", HERE / "rp11_roles.py")
    assert roles.run("stop", "", "", invocation_id="ignored", parent_pid=1) == 22
    assert calls == [((), {})]
    assert roles.run("stop", "", "", 5) == 69  # an operand is never forwarded
    assert len(calls) == 1


def test_the_entry_imports_the_stop_root_up_front():
    source = (HERE / "rp11_h1.py").read_text()
    assert "import adapters.rp11.stop  # noqa: F401" in source
    assert {"application/rp11/stop.py", "adapters/rp11/stop.py"} <= set(build.SOURCES)


def test_backstop_runs_its_composition_root_with_the_provenance(monkeypatch):
    import adapters.rp11.backstop as backstop

    seen = {}

    def fake(activation_id, a2, **kw):
        seen.update(kw, activation_id=activation_id, a2=a2)
        return 12

    monkeypatch.setattr(backstop, "run_backstop", fake)
    roles = _load("rp11_roles_prod3", HERE / "rp11_roles.py")
    assert roles.run("backstop", ACT, A2, invocation_id="c" * 32, parent_pid=9) == 12
    assert seen == {"activation_id": ACT, "a2": A2, "invocation_id": "c" * 32, "parent_pid": 9}


def test_the_entry_imports_the_backstop_root_up_front():
    """A missing backstop module must fail at import (70), before any role runs."""
    source = (HERE / "rp11_h1.py").read_text()
    assert "import adapters.rp11.backstop  # noqa: F401" in source
    assert {"application/rp11/backstop.py", "adapters/rp11/backstop.py"} <= set(build.SOURCES)


def test_the_entry_imports_the_hold_root_up_front():
    """Likewise for the holder: every hold module is in the artifact manifest."""
    source = (HERE / "rp11_h1.py").read_text()
    assert "import adapters.rp11.hold  # noqa: F401" in source
    assert {
        "application/rp11/hl.py",
        "application/rp11/hold.py",
        "adapters/rp11/hold.py",
        "adapters/rp11/holdfs.py",
    } <= set(build.SOURCES)


def test_stop_post_runs_the_cleanup_composition_root_with_the_provenance(monkeypatch):
    import adapters.rp11.stop_post as stop_post

    seen = {}

    def fake(activation_id, a2, **kw):
        seen.update(kw, activation_id=activation_id, a2=a2)
        return 0

    monkeypatch.setattr(stop_post, "run_stop_post", fake)
    roles = _load("rp11_roles_prod2", HERE / "rp11_roles.py")
    assert roles.run("stop-post", ACT, A2, invocation_id="b" * 32, parent_pid=7) == 0
    assert seen == {"activation_id": ACT, "a2": A2, "invocation_id": "b" * 32, "parent_pid": 7}


# --- first-image controls (H-FI, RT3.FI.1) ---------------------------------------


@pytest.mark.parametrize(
    "block,expected",
    [
        (b"PATH=/bin\0INVOCATION_ID=" + b"a" * 32 + b"\0", "a" * 32),
        (b"PATH=/bin\0", "absent"),
        (b"", "absent"),
        (b"INVOCATION_ID=" + b"a" * 32 + b"\0INVOCATION_ID=" + b"b" * 32, None),
        (b"INVOCATION_ID=" + b"A" * 32, None),
        (b"INVOCATION_ID=" + b"a" * 31, None),
        (b"INVOCATION_ID=", None),
        (b"INVOCATION_ID=" + b"\xff" * 32, None),
    ],
)
def test_only_one_well_formed_invocation_id_is_taken_from_the_environment(block, expected):
    assert entry.invocation_id_from(block) == expected


PROBE = """
import json, os, signal
def run(role, activation_id, artifact_sha256, **provenance):
    open_fds = []
    for fd in sorted(int(name) for name in os.listdir("/proc/self/fd")):
        try:
            os.fstat(fd)  # the listing's own descriptor is closed again by now
            if fd >= 3:
                open_fds.append(fd)
        except OSError:
            pass
    umask = os.umask(0o022)
    state = {
        "role": role, "provenance": provenance, "fds": open_fds, "umask": umask,
        "cwd": os.getcwd(), "environ": sorted(os.environ),
        "mask": sorted(int(s) for s in signal.pthread_sigmask(signal.SIG_BLOCK, [])),
        "default": [s.name for s in (signal.SIGTERM, signal.SIGINT, signal.SIGPIPE, signal.SIGCHLD)
                    if signal.getsignal(s) == signal.SIG_DFL],
    }
    with open(%r, "w") as handle:
        json.dump(state, handle)
    return 0
"""


def _probe(artifact: Path, tmp_path: Path, *, env, preexec=None, pass_fds=()):
    out = tmp_path / "probe.json"
    (artifact / "lib/rp11_roles.py").write_text(PROBE % str(out))
    proc = subprocess.run(
        [sys.executable, "-I", "-S", str(artifact / "rp11_h1.py"), "deact", ACT, A2, "stop-post"],
        capture_output=True, text=True, env=env, cwd=str(tmp_path), preexec_fn=preexec,
        pass_fds=pass_fds,
    )
    return proc, (json.loads(out.read_text()) if out.exists() else None)


def test_first_image_controls_run_before_the_role(artifact, tmp_path):
    def hostile():
        os.umask(0o000)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGUSR1, signal.SIGTERM})

    extra = os.open("/dev/null", os.O_RDONLY)
    try:
        proc, state = _probe(
            artifact, tmp_path,
            env={"INVOCATION_ID": "c" * 32, "PYTHONPATH": "/evil", "LD_PRELOAD": "/evil.so"},
            preexec=hostile, pass_fds=(extra,),
        )
    finally:
        os.close(extra)
    assert proc.returncode == 0, proc.stderr
    assert state["provenance"] == {"invocation_id": "c" * 32, "parent_pid": os.getpid()}
    assert state["fds"] == [] and state["umask"] == 0o022 and state["cwd"] == "/"
    assert state["environ"] == [] and state["mask"] == []
    assert state["default"] == ["SIGTERM", "SIGINT", "SIGPIPE", "SIGCHLD"]


def test_a_malformed_invocation_id_is_refused_before_any_role_runs(artifact, tmp_path):
    proc, state = _probe(artifact, tmp_path, env={"INVOCATION_ID": "not-hex"})
    assert proc.returncode == 64 and state is None
    assert "malformed or duplicate INVOCATION_ID" in proc.stderr


START_PROBE = PROBE.replace("def run(role, activation_id, artifact_sha256, **provenance):",
                            "def run(role, activation_id, artifact_sha256, *operands, **provenance):").replace(
    '"role": role,', '"role": role, "operands": list(operands),')


def _start_probe(artifact, tmp_path, env, role_argv):
    out = tmp_path / "probe.json"
    (artifact / "lib/rp11_roles.py").write_text(START_PROBE % str(out))
    proc = subprocess.run(
        [sys.executable, "-I", "-S", str(artifact / "rp11_h1.py"), *role_argv],
        capture_output=True, text=True, env=env, cwd=str(tmp_path),
    )
    return proc, (json.loads(out.read_text()) if out.exists() else None)


START_ARGV = ["start", ACT, A2, "900", "60"]
HOSTILE_INVOCATION_IDS = {
    "malformed": {"INVOCATION_ID": "not-hex"},
    "uppercase": {"INVOCATION_ID": "A" * 32},
    "short": {"INVOCATION_ID": "a" * 31},
    "empty": {"INVOCATION_ID": ""},
    "oversized": {"INVOCATION_ID": "a" * 100_000, **{f"PAD{i}": "x" * 100_000 for i in range(11)}},
    "well-formed": {"INVOCATION_ID": "c" * 32},
    "none": {},
}


@pytest.mark.parametrize("name", sorted(HOSTILE_INVOCATION_IDS))
def test_no_environment_value_can_change_a_valid_start(artifact, tmp_path, name):
    """H-FI.1 / SA1.FI.1: ``start`` reads no environment variable."""
    proc, state = _start_probe(artifact, tmp_path, HOSTILE_INVOCATION_IDS[name], START_ARGV)
    assert proc.returncode == 0, proc.stderr
    assert state["role"] == "start" and state["operands"] == [900, 60]
    assert state["provenance"] == {"invocation_id": "absent", "parent_pid": os.getpid()}
    assert state["environ"] == [] and state["fds"] == [] and state["umask"] == 0o022
    assert state["cwd"] == "/" and state["mask"] == []
    assert "INVOCATION_ID" not in proc.stderr


@pytest.mark.parametrize("name", ["malformed", "uppercase", "short", "empty", "oversized"])
@pytest.mark.parametrize("role_argv", [["deact", ACT, A2, "stop-post"], ["hold", ACT, A2], ["backstop", ACT, A2]])
def test_the_same_values_still_refuse_every_role_that_consumes_the_provenance(
    artifact, tmp_path, name, role_argv
):
    proc, state = _start_probe(artifact, tmp_path, HOSTILE_INVOCATION_IDS[name], role_argv)
    assert proc.returncode == 64 and state is None
    assert "malformed or duplicate INVOCATION_ID" in proc.stderr


# Review finding 3: ``os.environ``/``os.environb`` cannot hold two entries for one key,
# so a genuine duplicate needs a raw ``envp`` handed to ``execve(2)`` itself.
RAW_EXEC = """
import ctypes, sys
libc = ctypes.CDLL(None, use_errno=True)
path, *rest = [a.encode() for a in sys.argv[1:]]
split = rest.index(b"--")
argv, envp = rest[:split], rest[split + 1:]
c_argv = (ctypes.c_char_p * (len(argv) + 1))(*argv, None)
c_envp = (ctypes.c_char_p * (len(envp) + 1))(*envp, None)
libc.execve(path, c_argv, c_envp)
sys.exit(127)
"""
DUPLICATE_ENVP = ["INVOCATION_ID=" + "a" * 32, "PATH=/usr/bin", "INVOCATION_ID=" + "b" * 32]


def _raw_exec(argv, envp, *, cwd):
    return subprocess.run(
        [sys.executable, "-I", "-c", RAW_EXEC, argv[0], *argv, "--", *envp],
        capture_output=True, cwd=str(cwd),
    )


def test_the_raw_harness_really_delivers_two_invocation_id_entries(tmp_path):
    proc = _raw_exec(["/bin/cat", "/proc/self/environ"], DUPLICATE_ENVP, cwd=tmp_path)
    entries = proc.stdout.split(b"\0")
    assert [e for e in entries if e.startswith(b"INVOCATION_ID=")] == [
        b"INVOCATION_ID=" + b"a" * 32, b"INVOCATION_ID=" + b"b" * 32,
    ]


def _raw_start_probe(artifact, tmp_path, envp, role_argv):
    out = tmp_path / "probe.json"
    (artifact / "lib/rp11_roles.py").write_text(START_PROBE % str(out))
    argv = [sys.executable, "-I", "-S", str(artifact / "rp11_h1.py"), *role_argv]
    proc = _raw_exec(argv, envp, cwd=tmp_path)
    return proc, (json.loads(out.read_text()) if out.exists() else None)


def test_a_genuinely_duplicated_invocation_id_cannot_affect_a_valid_start(artifact, tmp_path):
    control, control_state = _raw_start_probe(artifact, tmp_path, [], START_ARGV)
    (tmp_path / "probe.json").unlink()
    proc, state = _raw_start_probe(artifact, tmp_path, DUPLICATE_ENVP, START_ARGV)
    assert control.returncode == 0 and proc.returncode == 0, proc.stderr
    assert proc.returncode == control.returncode and state == control_state
    assert proc.stderr.decode().replace(str(tmp_path), "") == control.stderr.decode().replace(str(tmp_path), "")
    assert state["role"] == "start" and state["operands"] == [900, 60]
    assert state["provenance"]["invocation_id"] == "absent"
    assert state["environ"] == [] and state["fds"] == []
    assert "INVOCATION_ID" not in proc.stderr.decode()


@pytest.mark.parametrize("role_argv", [["deact", ACT, A2, "stop-post"], ["hold", ACT, A2], ["backstop", ACT, A2]])
def test_a_genuinely_duplicated_invocation_id_refuses_every_provenance_role(artifact, tmp_path, role_argv):
    proc, state = _raw_start_probe(artifact, tmp_path, DUPLICATE_ENVP, role_argv)
    assert proc.returncode == 64 and state is None
    assert b"malformed or duplicate INVOCATION_ID" in proc.stderr


STOP_ARGV = ["stop"]


@pytest.mark.parametrize("name", sorted(HOSTILE_INVOCATION_IDS))
def test_no_environment_value_can_change_a_valid_stop(artifact, tmp_path, name):
    """H-FI.1 / SA2.FI.1: ``stop`` reads no environment variable."""
    proc, state = _start_probe(artifact, tmp_path, HOSTILE_INVOCATION_IDS[name], STOP_ARGV)
    assert proc.returncode == 0, proc.stderr
    assert state["role"] == "stop" and state["operands"] == []
    assert state["provenance"] == {"invocation_id": "absent", "parent_pid": os.getpid()}
    assert state["environ"] == [] and state["fds"] == [] and state["umask"] == 0o022
    assert state["cwd"] == "/" and state["mask"] == []
    assert "INVOCATION_ID" not in proc.stderr


def test_a_genuinely_duplicated_invocation_id_cannot_affect_a_valid_stop(artifact, tmp_path):
    control, control_state = _raw_start_probe(artifact, tmp_path, [], STOP_ARGV)
    (tmp_path / "probe.json").unlink()
    proc, state = _raw_start_probe(artifact, tmp_path, DUPLICATE_ENVP, STOP_ARGV)
    assert control.returncode == 0 and proc.returncode == 0, proc.stderr
    assert state == control_state
    assert proc.stderr.decode().replace(str(tmp_path), "") == control.stderr.decode().replace(str(tmp_path), "")
    assert state["role"] == "stop" and state["provenance"]["invocation_id"] == "absent"
    assert state["environ"] == [] and state["fds"] == []
    assert "INVOCATION_ID" not in proc.stderr.decode()


@pytest.mark.parametrize("role_argv", [["stop", "x"], ["stop", ACT, A2], ["stop", "--now"], ["STOP"]])
def test_an_extra_or_alternate_stop_token_is_refused_before_any_role_runs(artifact, tmp_path, role_argv):
    for env in ({}, {"INVOCATION_ID": "not-hex"}):
        proc, state = _start_probe(artifact, tmp_path, env, role_argv)
        assert proc.returncode == 64 and state is None
        assert "not an accepted role vector" in proc.stderr or "INVOCATION_ID" in proc.stderr


def test_a_valid_stop_never_calls_the_environment_reading_helper():
    def forbidden(*_):
        raise AssertionError("stop must not read the environment")

    pid = os.fork()
    if pid == 0:  # pragma: no cover - a throwaway child
        code = 99
        try:
            entry._initial_environment = forbidden
            entry.invocation_id_from = forbidden
            os.environ["INVOCATION_ID"] = "x" * 5
            result = entry.first_image_controls(reads_environment=False)
            code = 0 if result == {"invocation_id": "absent", "parent_pid": os.getppid()} else 1
        except BaseException:
            code = 2
        finally:
            os._exit(code)
    _, status = os.waitpid(pid, 0)
    assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_a_valid_start_never_calls_the_environment_reading_helper(monkeypatch):
    def forbidden():
        raise AssertionError("start must not read the environment")

    def child():
        entry._initial_environment = forbidden
        entry.invocation_id_from = lambda block: forbidden()
        os.environ["INVOCATION_ID"] = "x" * 5
        os.environb[b"INVOCATION_ID"] = b"dup"

    pid = os.fork()
    if pid == 0:  # pragma: no cover - a throwaway child
        code = 99
        try:
            child()
            result = entry.first_image_controls(reads_environment=False)
            code = 0 if result == {"invocation_id": "absent", "parent_pid": os.getppid()} else 1
        except BaseException:
            code = 2
        finally:
            os._exit(code)
    _, status = os.waitpid(pid, 0)
    assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_only_the_start_and_stop_vectors_select_the_environment_free_path():
    source = (HERE / "rp11_h1.py").read_text()
    assert 'first_image_controls(reads_environment=sys.argv[1:2] not in (["start"], ["stop"]))' in source
    assert entry.first_image_controls.__defaults__ == (True,)


def test_a_closed_standard_descriptor_is_refused(artifact, tmp_path):
    proc, state = _probe(artifact, tmp_path, env={}, preexec=lambda: os.close(0))
    assert proc.returncode == 71 and state is None


# H-FI.3 review finding: the close was bounded by min(SC_OPEN_MAX, 2**20) at
# start, so a descriptor above a lowered soft limit, or above 2**20, reached the
# role. It is now found by listing /proc/self/fd and verified by a second listing.

HIGH_FD = 70_000  # above a 1,024 soft limit, below the usual hard limits
HUGE_FD = (1 << 20) + 7  # above the former 2**20 cap; needs root to raise the hard limit


@contextlib.contextmanager
def inherited_descriptor(number: int):
    """An inheritable descriptor at exactly ``number`` (limits raised as needed),
    with the original ``RLIMIT_NOFILE`` restored and asserted on every exit."""
    original = resource.getrlimit(resource.RLIMIT_NOFILE)
    soft, hard = original
    try:
        if hard != resource.RLIM_INFINITY and hard <= number:
            with open("/proc/sys/fs/nr_open") as handle:
                nr_open = int(handle.read())
            if os.geteuid() != 0 or nr_open <= number:
                pytest.skip(f"cannot raise RLIMIT_NOFILE above {number} (hard {hard}, nr_open {nr_open})")
            hard = number + 1
        if soft == resource.RLIM_INFINITY or soft <= number:
            resource.setrlimit(resource.RLIMIT_NOFILE, (number + 1, hard))
        source = os.open("/dev/null", os.O_RDONLY)
        try:
            assert os.dup2(source, number, inheritable=True) == number
        finally:
            os.close(source)
        try:
            yield number
        finally:
            os.close(number)
    finally:
        resource.setrlimit(resource.RLIMIT_NOFILE, original)
        assert resource.getrlimit(resource.RLIMIT_NOFILE) == original


@pytest.mark.parametrize("number", [HIGH_FD, HUGE_FD], ids=["70000", "2**20+7"])
@pytest.mark.parametrize("soft", ["raised", "lowered-below"])
def test_a_high_inherited_descriptor_never_reaches_the_role(artifact, tmp_path, number, soft):
    """Raised: the soft limit is above the descriptor (2**20+7 escaped the old cap).
    Lowered-below: the image starts with a soft limit of 1,024 while the descriptor
    is still open (escaped the old SC_OPEN_MAX bound)."""
    def lower():
        if soft == "lowered-below":
            resource.setrlimit(resource.RLIMIT_NOFILE, (1_024, resource.getrlimit(resource.RLIMIT_NOFILE)[1]))

    with inherited_descriptor(number):
        assert str(number) in os.listdir("/proc/self/fd")
        proc, state = _probe(artifact, tmp_path, env={}, preexec=lower, pass_fds=(number,))
    assert proc.returncode == 0, proc.stderr
    assert state["fds"] == []


def _first_image_in_a_child(break_it) -> tuple[int, int]:
    """Run ``first_image_controls`` in a throwaway child holding descriptor 3 or
    higher; ``(status, extra-descriptor-still-open)``."""
    pid = os.fork()
    if pid == 0:  # pragma: no cover - a throwaway child
        code = 99
        try:
            extra = os.open("/dev/null", os.O_RDONLY)
            break_it()
            result = entry.first_image_controls()
            code = (result if isinstance(result, int) else 0) * 2 + (1 if entry._is_open(extra) else 0)
        finally:
            os._exit(code)
    _, status = os.waitpid(pid, 0)
    assert os.WIFEXITED(status)
    code = os.WEXITSTATUS(status)
    return code // 2, code % 2


def test_an_image_that_cannot_list_its_descriptors_is_refused(monkeypatch):
    """Fail closed: without the listing nothing is proved closed, so 71."""
    monkeypatch.setattr(entry, "_OWN_FDS", "/proc/self/no-such-directory")
    assert _first_image_in_a_child(lambda: None) == (71, 1)


def test_a_descriptor_that_survives_closing_is_refused():
    """The verifying second listing: a close that did not take effect is 71."""
    def no_op_close():
        entry.os.close = lambda fd: None

    assert _first_image_in_a_child(no_op_close) == (71, 1)


def test_the_close_leaves_only_the_standard_descriptors():
    status, extra_open = _first_image_in_a_child(lambda: None)
    assert (status, extra_open) == (0, 0)


def test_a_refused_close_runs_no_role(artifact, tmp_path):
    """End to end through the built image: with the listing unavailable (its path
    replaced in this disposable build) the image exits 71 and no role runs."""
    script = artifact / "rp11_h1.py"
    script.write_text(script.read_text().replace('"/proc/self/fd"', '"/proc/self/no-such-directory"', 1))
    proc, state = _probe(artifact, tmp_path, env={})
    assert proc.returncode == 71 and state is None
    assert "inherited descriptors could not be closed" in proc.stderr


def test_the_role_vector_is_validated_before_the_role(artifact, tmp_path):
    out = tmp_path / "probe.json"
    (artifact / "lib/rp11_roles.py").write_text(PROBE % str(out))
    for tail in (["deact", ACT, A2, "attest"], ["deact", ACT, A2], ["deact", ACT, A2.upper(), "stop-post"]):
        proc = subprocess.run(
            [sys.executable, "-I", "-S", str(artifact / "rp11_h1.py"), *tail],
            capture_output=True, text=True, env={}, cwd="/",
        )
        assert proc.returncode == 64 and not out.exists(), tail
