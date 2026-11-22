"""The host test's teardown helpers and the timeout-bound validation, with no host access (temporary directories only).

``tests/systemd_integration/synthetic_cleanup.py`` must remove only the exact synthetic file or directory a fixture
created: never recursively, never a symlink, never a replaced file or unexpected residue.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent / "systemd_integration"))
from synthetic_cleanup import Ledger, identity, remove_dir_if_ours, remove_file_exact  # noqa: E402

from tools.rp11_capture_unit_install import UnitSpec  # noqa: E402


@pytest.mark.parametrize("bound", [float("nan"), float("inf"), float("-inf"), 0, -1, 0.0])
def test_a_non_finite_or_non_positive_timeout_bound_is_refused_at_construction(bound):
    with pytest.raises(ValueError):
        UnitSpec(max_start_timeout_seconds=bound)


def test_a_removed_tree_is_exactly_the_named_file_and_the_directories_rmdired(tmp_path):
    root = tmp_path / "scratch"
    leaf = root / "infra"
    leaf.mkdir(parents=True)
    (leaf / "unit.service").write_bytes(b"x")
    ids = {root: identity(root), leaf: identity(leaf)}
    remove_dir_if_ours(leaf, ids[leaf], files={"unit.service": (identity(leaf / "unit.service"), None)})
    remove_dir_if_ours(root, ids[root])
    assert not root.exists() and tmp_path.exists()


def test_unexpected_residue_is_refused_and_left_in_place(tmp_path):
    root = tmp_path / "scratch"
    root.mkdir()
    (root / "unit.service").write_bytes(b"x")
    (root / "someone-elses.txt").write_bytes(b"keep")
    with pytest.raises(AssertionError, match="unexpected residue"):
        remove_dir_if_ours(root, identity(root), files={"unit.service": (identity(root / "unit.service"), None)})
    assert (root / "someone-elses.txt").read_bytes() == b"keep" and not (root / "unit.service").exists()


def test_a_replaced_directory_is_refused_before_any_child_is_unlinked(tmp_path):
    root = tmp_path / "scratch"
    root.mkdir()
    (root / "override.conf").write_bytes(b"body")
    recorded_dir, recorded_file = identity(root), identity(root / "override.conf")
    (root / "override.conf").unlink()
    root.rmdir()
    root.mkdir()
    (root / "override.conf").write_bytes(b"body")  # same name and bytes, but a different directory and file
    # Make the recorded identity unmistakably different even if the filesystem reused the inode.
    other_dir = (recorded_dir[0], recorded_dir[1] + 1_000_003)
    with pytest.raises(AssertionError, match="not the directory this fixture created"):
        remove_dir_if_ours(root, other_dir, files={"override.conf": (recorded_file, b"body")})
    assert (root / "override.conf").read_bytes() == b"body"


def test_a_wrong_identity_or_changed_child_is_refused_and_the_directory_survives(tmp_path):
    root = tmp_path / "scratch"
    root.mkdir()
    child = root / "override.conf"
    child.write_bytes(b"body")
    recorded = identity(child)
    wrong = (recorded[0], recorded[1] + 1_000_003)
    with pytest.raises(AssertionError, match="not the file this fixture created"):
        remove_dir_if_ours(root, identity(root), files={"override.conf": (wrong, b"body")})
    child.write_bytes(b"edited by someone else")
    with pytest.raises(AssertionError, match="content is not the synthetic stand-in"):
        remove_dir_if_ours(root, identity(root), files={"override.conf": (recorded, b"body")})
    assert child.read_bytes() == b"edited by someone else" and root.is_dir()


def test_a_hard_linked_or_symlinked_child_is_refused(tmp_path):
    root = tmp_path / "scratch"
    root.mkdir()
    secret = tmp_path / "secret"
    secret.write_bytes(b"keep")
    (root / "a").symlink_to(secret)
    with pytest.raises(AssertionError, match="not a regular file"):
        remove_dir_if_ours(root, identity(root), files={"a": (identity(secret), None)})
    (root / "a").unlink()
    os.link(secret, root / "a")
    with pytest.raises(AssertionError, match="2 links"):
        remove_dir_if_ours(root, identity(root), files={"a": (identity(secret), None)})
    assert secret.read_bytes() == b"keep" and (root / "a").exists()


def test_the_ledger_records_at_creation_and_removes_only_what_it_created(tmp_path):
    ledger = Ledger()
    root = tmp_path / "scratch"
    ledger.mkdir(root)
    ledger.write(root / "override.conf", b"body")
    assert ledger.remove_all() == [] and not root.exists()
    ledger.mkdir(root)
    ledger.write(root / "override.conf", b"body")
    (root / "foreign.conf").write_bytes(b"keep")
    problems = ledger.remove_all()
    assert len(problems) == 1 and "unexpected residue" in problems[0]
    assert (root / "foreign.conf").read_bytes() == b"keep" and not (root / "override.conf").exists()


def test_the_ledger_refuses_a_replaced_directory_file_and_an_unrecorded_path(tmp_path):
    ledger = Ledger()
    root = tmp_path / "d"
    ledger.mkdir(root)
    ledger.write(root / "f", b"body")
    root.rename(tmp_path / "aside")  # kept alive, so the replacement cannot reuse its inode
    root.mkdir()
    (root / "f").write_bytes(b"body")  # same name and bytes, but not the recorded directory or file
    stranger = tmp_path / "stranger"
    stranger.write_bytes(b"keep")
    with pytest.raises(AssertionError, match="not created by this run"):
        ledger.remove_file(stranger)
    problems = ledger.remove_all()
    assert len(problems) == 1 and "not the directory this fixture created" in problems[0]
    assert (root / "f").read_bytes() == b"body" and stranger.read_bytes() == b"keep"
    assert (tmp_path / "aside" / "f").read_bytes() == b"body"


def test_a_ledger_write_never_overwrites_or_follows_a_symlink(tmp_path):
    ledger = Ledger()
    target = tmp_path / "target"
    target.write_bytes(b"keep")
    (tmp_path / "link").symlink_to(target)
    with pytest.raises(FileExistsError):
        ledger.write(tmp_path / "link", b"x")
    with pytest.raises(FileExistsError):
        ledger.write(target, b"x")
    assert target.read_bytes() == b"keep"


def test_a_nested_unexpected_directory_is_never_recursively_deleted(tmp_path):
    root = tmp_path / "parent"
    (root / "other" / "deep").mkdir(parents=True)
    (root / "other" / "deep" / "f").write_bytes(b"keep")
    with pytest.raises(AssertionError, match="unexpected residue"):
        remove_dir_if_ours(root, identity(root))
    assert (root / "other" / "deep" / "f").read_bytes() == b"keep"


def test_a_directory_replaced_since_creation_is_not_touched(tmp_path):
    root = tmp_path / "scratch"
    root.mkdir()
    recorded = identity(root)
    root.rmdir()
    root.mkdir()
    (root / "f").write_bytes(b"keep")
    # The inode may be reused by the filesystem; make the recorded identity unmistakably different.
    with pytest.raises(AssertionError, match="not the directory this fixture created"):
        remove_dir_if_ours(root, (recorded[0], recorded[1] + 1_000_003))
    assert (root / "f").exists()


def test_a_symlinked_directory_is_never_followed_or_removed(tmp_path):
    target = tmp_path / "real"
    target.mkdir()
    (target / "f").write_bytes(b"keep")
    link = tmp_path / "link"
    link.symlink_to(target)
    with pytest.raises(AssertionError):
        remove_dir_if_ours(link, identity(target))
    assert (target / "f").exists() and link.is_symlink()


def test_a_file_that_is_not_the_exact_stand_in_is_refused(tmp_path):
    stand_in = tmp_path / "rp11_h1.py"
    stand_in.write_bytes(b"real content")
    recorded = identity(stand_in)
    with pytest.raises(AssertionError, match="content is not the synthetic stand-in"):
        remove_file_exact(stand_in, content=b"synthetic", inode=recorded)
    assert stand_in.read_bytes() == b"real content"
    stand_in.unlink()
    stand_in.write_bytes(b"synthetic")  # same content, a different file than the one recorded
    other = (recorded[0], recorded[1] + 1_000_003)
    with pytest.raises(AssertionError, match="not the file this fixture created"):
        remove_file_exact(stand_in, content=b"synthetic", inode=other)
    remove_file_exact(stand_in, content=b"synthetic", inode=identity(stand_in))
    assert not stand_in.exists()


def test_a_symlink_or_directory_where_a_file_is_expected_is_refused(tmp_path):
    secret = tmp_path / "secret"
    secret.write_bytes(b"keep")
    link = tmp_path / "unit.service"
    link.symlink_to(secret)
    with pytest.raises(AssertionError, match="not a regular file"):
        remove_file_exact(link, inode=identity(secret))
    with pytest.raises(AssertionError, match="not a regular file"):
        remove_file_exact(link, prefix=b"keep")
    assert secret.read_bytes() == b"keep" and link.is_symlink()
    directory = tmp_path / "dir"
    directory.mkdir()
    with pytest.raises(AssertionError, match="not a regular file"):
        remove_file_exact(directory, inode=identity(directory))


def test_a_bare_path_or_foreign_prefix_never_authorizes_an_unlink(tmp_path):
    foreign = tmp_path / "unit.service"
    foreign.write_bytes(b"[Service]\nExecStart=/bin/false\n")
    with pytest.raises(ValueError):
        remove_file_exact(foreign)
    with pytest.raises(AssertionError, match="content is not the synthetic stand-in"):
        remove_file_exact(foreign, prefix=b"# marker\n")
    assert foreign.exists()


def test_an_absent_target_is_not_an_error(tmp_path):
    remove_file_exact(tmp_path / "missing", inode=(0, 0))
    remove_dir_if_ours(tmp_path / "missing", (0, 0))
    assert os.listdir(tmp_path) == []
