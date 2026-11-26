"""RP-11 G6 preparation: capture-tool digest and SA-2 tree binding.

Every artifact here is **synthetic** (a stand-in wheel in a temporary directory).
It is not a gate-closing SA-2 build, installs nothing and runs no mechanism.

The public review requires root and a protected ancestor chain, which a
temporary directory does not have. Digest and tree-content tests therefore use
the internal reader; the protection tests call the public functions, simulating
root and ancestor metadata where the test is not run as root.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import tempfile
from pathlib import Path

import pytest

from tests.test_rp11_h1_artifact import GOOD_MEMBERS, ROOT, WHEEL_NAME, build, make_wheel, pin
from tools import route3_release_record as release
from tools.phase_5_0_evidence import capture_contract as contract

BOUNDARY = "lib/tools/phase_5_0_evidence/execution/boundary.py"


@pytest.fixture
def wheel(tmp_path, monkeypatch):
    source = tmp_path / "wheel"
    source.mkdir()
    path = make_wheel(source / WHEEL_NAME, GOOD_MEMBERS)
    pin(monkeypatch, path)
    return path


@pytest.fixture
def tree(wheel, tmp_path):
    return build.build(wheel, tmp_path / "artifact")


def _inputs(tree):
    """The internal, unprotected reading of a synthetic tree owned by this user."""
    return build._read_tree_inputs(tree, os.geteuid())


@pytest.fixture
def synthetic_review(monkeypatch):
    """Stand the internal reader in for the public one, to test what is built on it
    (the gate and the command line). A test seam only; nothing in build.py does this."""
    monkeypatch.setattr(build, "review_inputs", _inputs)


def _tool_digest_of(directory):
    return contract.capture_tool_sha256(
        {name: (directory / name).read_bytes() for name in contract.RP11_SOURCES}
    )


def _rewrite(path, data):
    path.write_bytes(data)
    path.chmod(0o644)


def test_the_restated_construction_equals_the_contract():
    assert build.RP11_SOURCES == contract.RP11_SOURCES
    assert build.TOOL_DIGEST_SCHEMA == contract.TOOL_DIGEST_SCHEMA
    assert set(build.RP11_SOURCES) <= set(build.ENTRY_SOURCES)


def test_review_inputs_bind_the_tool_digest_and_the_tree_digest_to_the_built_bytes(tree):
    inputs = _inputs(tree)
    assert inputs["capture_tool_sha256"] == _tool_digest_of(tree / "lib")
    assert inputs["tree_sha256"] == release.sa2_tree_digest(tree)
    assert [name for name, _ in inputs["files"]] == sorted(
        str(path.relative_to(tree)) for path in tree.rglob("*") if path.is_file()
    )
    assert _inputs(tree) == inputs


def test_two_builds_give_identical_review_inputs(wheel, tmp_path):
    first = build.build(wheel, tmp_path / "a")
    second = build.build(wheel, tmp_path / "b")
    assert _inputs(first) == _inputs(second)


def test_review_reads_the_built_tree_and_not_the_checkout(wheel, tmp_path, monkeypatch):
    checkout = tmp_path / "checkout"
    for name in (*build.SOURCES, *build.ENTRY_SOURCES):
        target = checkout / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    monkeypatch.setattr(build, "ROOT", checkout)
    built = build.build(wheel, tmp_path / "artifact")
    inputs = _inputs(built)

    for name in build.RP11_SOURCES:
        (checkout / name).write_bytes(b"# changed after copying\n")
    assert _inputs(built) == inputs
    shutil.rmtree(checkout)
    monkeypatch.setattr(build, "HERE", tmp_path / "absent")
    assert _inputs(built) == inputs


def test_the_digest_follows_the_bytes_placed_in_the_artifact(wheel, tmp_path, monkeypatch):
    checkout = tmp_path / "checkout"
    for name in (*build.SOURCES, *build.ENTRY_SOURCES):
        target = checkout / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    edited = checkout / build.RP11_SOURCES[0]
    edited.write_bytes(edited.read_bytes() + b"# synthetic edit\n")
    monkeypatch.setattr(build, "ROOT", checkout)
    inputs = _inputs(build.build(wheel, tmp_path / "artifact"))
    assert inputs["capture_tool_sha256"] == _tool_digest_of(checkout)
    assert inputs["capture_tool_sha256"] != _tool_digest_of(ROOT)


def test_a_build_whose_tree_is_not_what_it_placed_fails_and_leaves_nothing(wheel, tmp_path, monkeypatch):
    real = build._unsafe_tree

    def tamper_after_the_mode_check(top, owner):
        problem = real(top, owner)
        _rewrite(top / BOUNDARY, b"# swapped in staging\n")
        return problem

    monkeypatch.setattr(build, "_unsafe_tree", tamper_after_the_mode_check)
    with pytest.raises(build.BuildError, match="bytes the build placed"):
        build.build(wheel, tmp_path / "artifact")
    assert not (tmp_path / "artifact").exists()
    assert [p.name for p in tmp_path.iterdir() if p.name.startswith(".")] == []


def test_the_gate_accepts_only_both_matching_digests(tree, synthetic_review):
    inputs = _inputs(tree)
    good = (inputs["tree_sha256"], inputs["capture_tool_sha256"])
    assert build.verify_review(tree, *good) == inputs
    for bad in (("0" * 64, good[1]), (good[0], "0" * 64), (good[1], good[0])):
        with pytest.raises(build.BuildError, match="expected"):
            build.verify_review(tree, *bad)
    for bad in (None, "", "0" * 63, "A" * 64, "0" * 64 + "\n"):
        for pair in ((bad, good[1]), (good[0], bad)):
            with pytest.raises(build.BuildError, match="64 lowercase hex"):
                build.verify_review(tree, *pair)


@pytest.mark.parametrize(
    ("name", "moves_tool_digest"), [(BOUNDARY, True), ("rp11_entry.py", False)]
)
def test_any_changed_byte_fails_the_gate(tree, synthetic_review, name, moves_tool_digest):
    before = _inputs(tree)
    _rewrite(tree / name, (tree / name).read_bytes() + b"#")
    after = _inputs(tree)
    assert after["tree_sha256"] != before["tree_sha256"]
    assert (after["capture_tool_sha256"] != before["capture_tool_sha256"]) is moves_tool_digest
    with pytest.raises(build.BuildError, match="tree_sha256"):
        build.verify_review(tree, before["tree_sha256"], before["capture_tool_sha256"])


def _extra(tree, name):
    _rewrite(tree / "lib" / name, b"x")


def _directory(tree, name):
    path = tree / "lib" / name
    path.mkdir()
    path.chmod(0o755)
    return path


def _link(tree):
    (tree / "lib" / "link.py").symlink_to(tree / BOUNDARY)


def _link_directory(tree):
    (tree / "lib" / "linked").symlink_to(tree / "lib" / "tools")


def _bytecode(tree):
    _rewrite(_directory(tree, "__pycache__") / "x.cpython-314.pyc", b"x")


@pytest.mark.parametrize(
    "tamper",
    [
        lambda tree: (tree / BOUNDARY).unlink(),
        lambda tree: (tree / BOUNDARY).chmod(0o664),
        lambda tree: (tree / "lib").chmod(0o775),
        lambda tree: tree.chmod(0o700),
        _link,
        _link_directory,
        lambda tree: os.mkfifo(tree / "lib" / "pipe", 0o644),
        lambda tree: _directory(tree, "empty"),
        _bytecode,
        lambda tree: _extra(tree, "stale.pyc"),
        lambda tree: _extra(tree, "two words.py"),
    ],
    ids=[
        "missing-source",
        "writable-file",
        "writable-directory",
        "top-mode",
        "link",
        "linked-directory",
        "fifo",
        "empty-directory",
        "pycache",
        "pyc",
        "unplain-name",
    ],
)
def test_an_unsafe_or_incomplete_tree_yields_no_review_inputs(tree, tamper):
    tamper(tree)
    with pytest.raises(build.BuildError):
        _inputs(tree)


def test_an_absent_linked_or_foreign_owned_tree_is_refused(tree, tmp_path):
    link = tmp_path / "link"
    link.symlink_to(tree)
    for path in (tmp_path / "absent", link, tree / "rp11_entry.py"):
        with pytest.raises(build.BuildError):
            _inputs(path)
    with pytest.raises(build.BuildError, match="owner uid"):
        build._read_tree_inputs(tree, os.geteuid() + 1)


def test_the_command_line_prints_inputs_gates_and_refuses(
    tree, synthetic_review, wheel, tmp_path, capsys
):
    review = ["--review", str(tree)]
    assert build.main(review) == 0
    printed = capsys.readouterr().out
    inputs = json.loads(printed)
    gate = [
        "--expect-tree-sha256",
        inputs["tree_sha256"],
        "--expect-capture-tool-sha256",
        inputs["capture_tool_sha256"],
    ]
    assert build.main(review + gate) == 0
    assert capsys.readouterr().out == printed

    assert build.main(review + gate[:3] + ["0" * 64]) == 1
    refused = capsys.readouterr()
    assert refused.out == "" and "capture_tool_sha256" in refused.err

    for argv in (
        review + gate[:2],
        review + gate[2:],
        review + ["--dest", str(tmp_path / "x")],
        ["--wheel", str(wheel)],
        ["--wheel", str(wheel), "--dest", str(tmp_path / "x"), *gate],
    ):
        with pytest.raises(SystemExit) as stopped:
            build.main(argv)
        assert stopped.value.code == 2
    assert not (tmp_path / "x").exists()


# G6-R1: the public review fails closed without root and a protected chain.

ZEROS = "0" * 64
GATE_ARGS = ["--expect-tree-sha256", ZEROS, "--expect-capture-tool-sha256", ZEROS]


def _assert_public_review_refuses(tree, match, capsys):
    """Every public entry refuses: the two functions and both CLI forms."""
    with pytest.raises(build.BuildError, match=match):
        build.review_inputs(tree)
    with pytest.raises(build.BuildError, match=match):
        build.verify_review(tree, ZEROS, ZEROS)
    capsys.readouterr()
    for extra in ([], GATE_ARGS):
        assert build.main(["--review", str(tree), *extra]) == 1
        refused = capsys.readouterr()
        assert refused.out == "" and match in refused.err


def _as_root_with_protected_metadata(monkeypatch, changed=None):
    """Simulate root and a root-owned, non-writable filesystem.

    Every ``lstat`` reports uid 0 with group/other write removed, except the
    paths in ``changed`` (``{path: (uid, extra mode bits)}``). File types are real."""
    real = os.lstat
    changed = {os.fspath(path): value for path, value in (changed or {}).items()}

    def lstat(path, *args, **kwargs):
        info = list(real(path, *args, **kwargs))
        uid, bits = changed.get(os.fspath(path), (0, 0))
        info[stat.ST_MODE] = (info[stat.ST_MODE] & ~0o022) | bits
        info[stat.ST_UID] = uid
        return os.stat_result(info)

    monkeypatch.setattr(build.os, "geteuid", lambda: 0)
    monkeypatch.setattr(build.os, "lstat", lstat)


@pytest.fixture
def nested(wheel, tmp_path):
    return build.build(wheel, tmp_path / "outer" / "inner" / "artifact")


def test_the_public_review_refuses_a_non_root_caller(tree, monkeypatch, capsys):
    monkeypatch.setattr(build.os, "geteuid", lambda: 1000)
    _assert_public_review_refuses(tree, "must run as root", capsys)


def test_the_public_review_runs_the_protected_chain_check_before_reading(tree, monkeypatch, capsys):
    checked = []

    def problem(parent):
        checked.append(parent)
        return "synthetic chain problem"

    def never(*_args):
        raise AssertionError("the tree was read from an unsafe location")

    monkeypatch.setattr(build.os, "geteuid", lambda: 0)
    monkeypatch.setattr(build, "_install_parent_problem", problem)
    monkeypatch.setattr(build, "_read_tree_inputs", never)
    _assert_public_review_refuses(tree, "synthetic chain problem", capsys)
    assert checked == [tree.parent] * 4


def test_the_public_review_accepts_a_protected_chain(nested, monkeypatch):
    expected = _inputs(nested)
    _as_root_with_protected_metadata(monkeypatch)
    assert build.review_inputs(nested) == expected
    good = (expected["tree_sha256"], expected["capture_tool_sha256"])
    assert build.verify_review(nested, *good) == expected


@pytest.mark.parametrize("levels_up", [0, 1, 2], ids=["parent", "grandparent", "higher"])
@pytest.mark.parametrize(
    "state", [(0, 0o020), (0, 0o002), (1000, 0)], ids=["group-writable", "other-writable", "owner"]
)
def test_the_public_review_refuses_any_unprotected_ancestor(
    nested, monkeypatch, capsys, levels_up, state
):
    ancestor = nested.parents[levels_up]
    _as_root_with_protected_metadata(monkeypatch, {ancestor: state})
    _assert_public_review_refuses(nested, f"{ancestor} is not root-owned and protected", capsys)


def test_the_public_review_refuses_a_linked_ancestor_and_dotdot(nested, monkeypatch, capsys):
    link = nested.parents[2] / "link"
    link.symlink_to(nested.parents[1])
    _as_root_with_protected_metadata(monkeypatch)
    _assert_public_review_refuses(link / nested.name, f"{link} is not a real directory", capsys)
    _assert_public_review_refuses(link / ".." / "inner" / nested.name, "may not contain", capsys)


@pytest.mark.parametrize("name", [".", "lib", BOUNDARY], ids=["top", "directory", "file"])
def test_the_public_review_refuses_a_tree_object_not_owned_by_root(
    nested, monkeypatch, capsys, name
):
    _as_root_with_protected_metadata(monkeypatch, {nested / name: (1000, 0)})
    _assert_public_review_refuses(nested, "owner uid 1000", capsys)


def test_a_real_temporary_directory_is_not_a_protected_location(tree, monkeypatch, capsys):
    """No simulated metadata: ``tmp_path`` or an ancestor is unprotected unless
    pytest was given a protected basetemp."""
    if build._install_parent_problem(tree.parent) is None:
        pytest.skip("basetemp is itself protected")
    monkeypatch.setattr(build.os, "geteuid", lambda: 0)
    _assert_public_review_refuses(tree, "unsafe review location", capsys)


@pytest.mark.skipif(os.geteuid() != 0, reason="needs real root")
def test_as_real_root_the_review_follows_the_real_ancestor_chain(wheel, capsys):
    base = Path(tempfile.mkdtemp(prefix="rp11-g6-test.", dir="/root"))
    try:
        assert build._install_parent_problem(base) is None
        outer = base / "outer"
        built = build.build(wheel, outer / "artifact")
        assert build.review_inputs(built) == build._read_tree_inputs(built, 0)
        outer.chmod(0o775)
        _assert_public_review_refuses(built, f"{outer} is not root-owned and protected", capsys)
        outer.chmod(0o755)
        os.chown(outer, 65534, -1)
        _assert_public_review_refuses(built, f"{outer} is not root-owned and protected", capsys)
    finally:
        shutil.rmtree(base)
