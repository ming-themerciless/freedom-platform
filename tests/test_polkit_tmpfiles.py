"""Host-independent tests for the Route 3 Polkit ``tmpfiles.d`` installer.

The destination, ``/run`` and the "root" owner are a temporary directory and the
test user; real-root behaviour is in ``tests/systemd_integration``.
"""

from __future__ import annotations

import ast
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True

from tools import polkit_tmpfiles as pt  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
SOURCE = REPO / pt.SOURCE_RELATIVE
GOOD = SOURCE.read_bytes()
UID, GID = os.getuid(), os.getgid()


def make_config(tmp_path: Path, *, source: bytes | None = GOOD, populate_run: bool = True) -> pt.Config:
    dest = tmp_path / "tmpfiles.d"
    dest.mkdir(mode=0o755)
    run = tmp_path / "run"
    run.mkdir()
    if populate_run:
        for rel in pt.RUNTIME_DIRS:
            (run / rel).mkdir(mode=0o755)
            os.chmod(run / rel, 0o755)
    src = tmp_path / "source.conf"
    if source is not None:
        src.write_bytes(source)
    boot = tmp_path / "boot_id"
    boot.write_text("7f56a1be-bf42-4a23-83bd-0b9b9087d664\n")
    layers = []
    for layer in ("etc", "run", "local"):
        (tmp_path / "override" / layer).mkdir(parents=True, mode=0o755)
        layers.append(str(tmp_path / "override" / layer))
    return pt.Config(source=src, dest_dir=str(dest), run=str(run), boot_id_file=str(boot),
                     uid=UID, gid=GID, require_root=False,
                     override_dirs=tuple(layers), lock_timeout_s=0.3)


def dest_of(config: pt.Config) -> Path:
    return Path(config.dest_dir) / pt.FRAGMENT_NAME


class FakeSystemd(pt.SystemdFacts):
    def __init__(self, polkit=None, setup=None, fail=False):
        self.polkit = {"ActiveState": "active", "MainPID": "42", "ExecMainStartTimestampMonotonic": "900",
                       "After": "basic.target systemd-tmpfiles-setup.service sysinit.target"} | (polkit or {})
        self.setup = {"Result": "success", "ExecMainExitTimestampMonotonic": "500"} | (setup or {})
        self.fail = fail
        self.calls: list[tuple[str, tuple[str, ...]]] = []

    def show(self, unit, props):
        self.calls.append((unit, tuple(props)))
        if self.fail:
            raise OSError("down")
        return dict(self.polkit if unit == "polkit.service" else self.setup)


# ---- 1. the repository fragment ------------------------------------------------


def test_fragment_is_exactly_the_two_directory_entries():
    entries = pt.parse_fragment(GOOD)
    assert entries == (
        ("d", "/run/polkit-1", "0755", "root", "root", "-"),
        ("d", "/run/polkit-1/rules.d", "0755", "root", "root", "-"),
    )
    # nothing but comments, blanks and those two lines
    body = [ln for ln in GOOD.decode().splitlines() if ln.strip() and not ln.startswith("#")]
    assert len(body) == 2 and all(ln.startswith("d ") for ln in body)


def test_installed_name_is_freedom_blades_specific_and_in_the_package_layer():
    assert pt.FRAGMENT_NAME == "freedom-blades-rp11-polkit-rules.conf"
    assert pt.Config().dest_dir == "/usr/lib/tmpfiles.d"
    assert SOURCE.parent == REPO / "infra" / "tmpfiles.d"


# ---- 2. source refusal ---------------------------------------------------------

BAD_SOURCES = {
    "empty": b"",
    "no-final-newline": GOOD.rstrip(b"\n"),
    "extra-entry": GOOD + b"f /run/polkit-1/rules.d/50-x.rules 0644 root root -\n",
    "extra-dir": GOOD + b"d /run/polkit-1/evidence 0755 root root -\n",
    "wrong-mode": GOOD.replace(b"0755", b"0777", 1),
    "wrong-owner": GOOD.replace(b"root root", b"polkitd root", 1),
    "wrong-path": GOOD.replace(b"/run/polkit-1/rules.d", b"/etc/polkit-1/rules.d"),
    "reordered": b"d /run/polkit-1/rules.d 0755 root root -\nd /run/polkit-1 0755 root root -\n",
    "missing-entry": b"d /run/polkit-1 0755 root root -\n",
    "tab-separated": GOOD.replace(b" 0755 root root -", b"\t0755\troot\troot\t-"),
    "crlf": GOOD.replace(b"\n", b"\r\n"),
    "nul": GOOD + b"\0",
    "non-ascii": GOOD + "# ä\n".encode(),
    "oversize": GOOD + b"#" * pt.MAX_FRAGMENT_BYTES + b"\n",
}


@pytest.mark.parametrize("name", sorted(BAD_SOURCES))
def test_malformed_or_extended_source_is_refused_before_the_host_changes(tmp_path, name):
    config = make_config(tmp_path, source=BAD_SOURCES[name])
    with pytest.raises(pt.Refused) as err:
        pt.install(config)
    assert err.value.exit_code == pt.EXIT_REFUSED
    assert os.listdir(config.dest_dir) == []


def test_absent_and_symlinked_source_is_refused(tmp_path):
    config = make_config(tmp_path, source=None)
    with pytest.raises(pt.Refused) as err:
        pt.install(config)
    assert err.value.code == "source-unreadable"
    real = tmp_path / "real.conf"
    real.write_bytes(GOOD)
    link = Path(config.source)
    link.symlink_to(real)
    with pytest.raises(pt.Refused):
        pt.install(config)
    assert os.listdir(config.dest_dir) == []


def test_non_root_install_is_refused_without_touching_anything(tmp_path):
    if os.geteuid() == 0:
        pytest.skip("runs as root")
    config = make_config(tmp_path)
    config = pt.Config(**{**config.__dict__, "require_root": True})
    with pytest.raises(pt.Refused) as err:
        pt.install(config)
    assert err.value.code == "not-root"
    assert os.listdir(config.dest_dir) == []


# ---- 3. install and idempotency ------------------------------------------------


def test_first_install_writes_exact_bytes_owner_and_mode_and_leaves_no_temp(tmp_path):
    config = make_config(tmp_path)
    assert pt.install(config) == "installed"
    info = os.lstat(dest_of(config))
    assert stat.S_ISREG(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o644
    assert (info.st_uid, info.st_gid) == (UID, GID) and info.st_nlink == 1
    assert dest_of(config).read_bytes() == GOOD
    assert os.listdir(config.dest_dir) == [pt.FRAGMENT_NAME]


def test_byte_identical_reinstall_is_an_idempotent_success_that_does_not_rewrite(tmp_path):
    config = make_config(tmp_path)
    pt.install(config)
    before = os.lstat(dest_of(config))
    assert pt.install(config) == "already-installed"
    after = os.lstat(dest_of(config))
    assert (before.st_ino, before.st_mtime_ns) == (after.st_ino, after.st_mtime_ns)


# ---- 4. conflicts are never replaced -------------------------------------------


def _plant(config, kind):
    dest = dest_of(config)
    if kind == "bytes":
        dest.write_bytes(GOOD + b"# edited\n")
        os.chmod(dest, 0o644)
    elif kind == "mode":
        dest.write_bytes(GOOD)
        os.chmod(dest, 0o664)
    elif kind == "symlink":
        (Path(config.dest_dir) / "elsewhere").write_bytes(GOOD)
        dest.symlink_to("elsewhere")
    elif kind == "dangling-symlink":
        dest.symlink_to("nowhere")
    elif kind == "directory":
        dest.mkdir()
    elif kind == "fifo":
        os.mkfifo(dest, 0o644)
    elif kind == "empty":
        dest.write_bytes(b"")
        os.chmod(dest, 0o644)


def _snapshot(config):
    out = {}
    for entry in sorted(os.listdir(config.dest_dir)):
        info = os.lstat(Path(config.dest_dir) / entry)
        out[entry] = (info.st_mode, info.st_ino, info.st_size, info.st_mtime_ns)
    return out


@pytest.mark.parametrize("kind", ["bytes", "mode", "symlink", "dangling-symlink", "directory", "fifo", "empty"])
def test_conflicting_destination_fails_closed_and_is_not_replaced(tmp_path, kind):
    config = make_config(tmp_path)
    _plant(config, kind)
    before = _snapshot(config)
    with pytest.raises(pt.Refused) as err:
        pt.install(config)
    assert err.value.exit_code == pt.EXIT_CONFLICT
    assert _snapshot(config) == before


def test_wrong_owner_is_a_conflict(tmp_path):
    config = make_config(tmp_path)
    pt.install(config)
    other = pt.Config(**{**config.__dict__, "uid": UID + 1})
    with pytest.raises(pt.Refused):  # the directory owner no longer matches either
        pt.install(other)
    with pytest.raises(pt.Refused):
        pt.remove(other)
    assert dest_of(config).read_bytes() == GOOD


def test_group_writable_destination_directory_is_refused(tmp_path):
    config = make_config(tmp_path)
    os.chmod(config.dest_dir, 0o775)
    with pytest.raises(pt.Refused) as err:
        pt.install(config)
    assert err.value.code == "destination-directory-unsafe"
    assert os.listdir(config.dest_dir) == []


def test_missing_or_symlinked_destination_directory_is_refused(tmp_path):
    config = make_config(tmp_path)
    moved = tmp_path / "real-dir"
    Path(config.dest_dir).rename(moved)
    with pytest.raises(pt.Refused):
        pt.install(config)
    Path(config.dest_dir).symlink_to(moved)
    with pytest.raises(pt.Refused):
        pt.install(config)
    assert os.listdir(moved) == []


def test_a_name_that_appears_during_install_is_not_overwritten(tmp_path):
    config = make_config(tmp_path)

    class Racing(pt.Fs):
        def link_at(self, dir_fd, source, dest):
            (Path(config.dest_dir) / dest).write_bytes(b"someone else\n")
            super().link_at(dir_fd, source, dest)

    with pytest.raises(pt.Refused) as err:
        pt.install(config, Racing())
    assert err.value.exit_code == pt.EXIT_CONFLICT
    assert dest_of(config).read_bytes() == b"someone else\n"
    assert os.listdir(config.dest_dir) == [pt.FRAGMENT_NAME]


# ---- 5. interruption, short writes, failed flush/rename ------------------------


def test_short_writes_are_completed(tmp_path):
    config = make_config(tmp_path)

    class Short(pt.Fs):
        def write(self, fd, data):
            return super().write(fd, data[:7])

    assert pt.install(config, Short()) == "installed"
    assert dest_of(config).read_bytes() == GOOD


@pytest.mark.parametrize("seam", ["write-zero", "write-error", "fsync", "fchmod", "fchown", "link", "create", "dir-fsync"])
def test_failed_step_leaves_no_accepted_or_temporary_file(tmp_path, seam):
    config = make_config(tmp_path)
    boom = OSError(5, "injected")
    calls = {"fsync": 0}

    class Failing(pt.Fs):
        def write(self, fd, data):
            if seam == "write-zero":
                return 0
            if seam == "write-error":
                raise boom
            return super().write(fd, data)

        def fsync(self, fd):
            calls["fsync"] += 1
            if seam == "fsync" and calls["fsync"] == 1 or seam == "dir-fsync" and calls["fsync"] == 2:
                raise boom
            super().fsync(fd)

        def fchmod(self, fd, mode):
            if seam == "fchmod":
                raise boom
            super().fchmod(fd, mode)

        def fchown(self, fd, uid, gid):
            if seam == "fchown":
                raise boom
            super().fchown(fd, uid, gid)

        def link_at(self, dir_fd, source, dest):
            if seam == "link":
                raise boom
            super().link_at(dir_fd, source, dest)

        def create_at(self, dir_fd, name):
            if seam == "create":
                raise boom
            return super().create_at(dir_fd, name)

    with pytest.raises(pt.Refused) as err:
        pt.install(config, Failing())
    assert err.value.exit_code == pt.EXIT_IO
    leftovers = os.listdir(config.dest_dir)
    # only the final directory flush can fail after the complete file is in place
    assert leftovers == ([pt.FRAGMENT_NAME] if seam == "dir-fsync" else [])
    if leftovers:
        assert dest_of(config).read_bytes() == GOOD


def test_interruption_removes_the_temporary_file_and_never_publishes_a_partial(tmp_path):
    config = make_config(tmp_path)

    class Interrupted(pt.Fs):
        def fsync(self, fd):
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        pt.install(config, Interrupted())
    assert os.listdir(config.dest_dir) == []
    assert pt.main(["install"], config, Interrupted()) == pt.EXIT_INTERRUPTED


# ---- 5b. temporary-name cleanup after publication --------------------------------


class StuckTemp(pt.Fs):
    """``unlink_at`` of the installer's temporary name fails (or is interrupted)."""

    def __init__(self, error=None):
        self.error = error or PermissionError(1, "injected")

    def unlink_at(self, dir_fd, name):
        if name.startswith("."):
            raise self.error
        super().unlink_at(dir_fd, name)


def _leak_alias(config, error=None):
    """Install with a temp unlink that fails; returns the leaked alias name."""
    try:
        pt.install(config, StuckTemp(error))
    except BaseException:  # noqa: BLE001 - the caller asserts the outcome separately
        pass
    names = [n for n in os.listdir(config.dest_dir) if n != pt.FRAGMENT_NAME]
    assert len(names) == 1
    return names[0]


def test_temp_unlink_failure_after_publication_is_not_success(tmp_path, capsys):
    config = make_config(tmp_path)
    assert pt.main(["install"], config, StuckTemp()) == pt.EXIT_IO
    captured = capsys.readouterr()
    assert captured.err == "refused: install-cleanup-failed\n" and "installed" not in captured.out
    info = os.lstat(dest_of(config))  # the public name is complete, never truncated
    assert dest_of(config).read_bytes() == GOOD
    assert stat.S_IMODE(info.st_mode) == 0o644 and (info.st_uid, info.st_gid) == (UID, GID)
    assert info.st_nlink == 2


def test_leaked_alias_is_never_called_clean_by_install_verify_or_remove_until_recovered(tmp_path, capsys):
    config = make_config(tmp_path)
    alias = _leak_alias(config)
    os.utime(dest_of(config), (1, 1))
    results = passing(config)
    assert failed(results) == {"fragment", "fragment-predates-boot", "fragment-no-temporary-alias"}
    assert pt.main(["verify"], config, None, FakeSystemd()) == pt.EXIT_VERIFY_FAILED
    assert "verify: ok" not in capsys.readouterr().out
    # install recovers exactly the attributed alias and reports it, not "already-installed"
    assert pt.install(config) == "alias-recovered"
    assert os.listdir(config.dest_dir) == [pt.FRAGMENT_NAME] and os.lstat(dest_of(config)).st_nlink == 1
    assert pt.install(config) == "already-installed"
    assert alias not in os.listdir(config.dest_dir)


def test_remove_deletes_the_leaked_alias_and_the_fragment_and_nothing_else(tmp_path):
    config = make_config(tmp_path)
    _leak_alias(config)
    other = Path(config.dest_dir) / "unrelated.conf"
    other.write_text("keep\n")
    assert pt.remove(config) == "removed"
    assert os.listdir(config.dest_dir) == ["unrelated.conf"]


def test_alias_recovery_failure_is_non_success_and_retains_everything(tmp_path):
    config = make_config(tmp_path)
    _leak_alias(config)
    before = _snapshot(config)
    with pytest.raises(pt.Refused) as err:
        pt.install(config, StuckTemp())
    assert (err.value.code, err.value.exit_code) == ("alias-recovery-failed", pt.EXIT_IO)
    assert _snapshot(config) == before
    with pytest.raises(pt.Refused) as err:
        pt.remove(config, StuckTemp())
    assert err.value.code == "remove-failed" and dest_of(config).read_bytes() == GOOD


def test_unexplained_extra_hard_link_is_a_conflict_everywhere_and_retained(tmp_path):
    config = make_config(tmp_path)
    pt.install(config)
    stray = Path(config.dest_dir) / "stray-name"
    os.link(dest_of(config), stray)
    before = _snapshot(config)
    with pytest.raises(pt.Refused) as err:
        pt.install(config)
    assert err.value.exit_code == pt.EXIT_CONFLICT
    with pytest.raises(pt.Refused) as err:
        pt.remove(config)
    assert err.value.code == "destination-retained"
    assert "fragment" in failed(passing(config))
    assert _snapshot(config) == before


def test_alias_plus_an_unexplained_link_is_retained_not_partially_recovered(tmp_path):
    config = make_config(tmp_path)
    alias = _leak_alias(config)
    os.link(dest_of(config), Path(config.dest_dir) / "stray-name")
    before = _snapshot(config)
    for action in (pt.install, pt.remove):
        with pytest.raises(pt.Refused) as err:
            action(config)
        assert err.value.exit_code == pt.EXIT_CONFLICT
    assert _snapshot(config) == before and alias in os.listdir(config.dest_dir)


def test_foreign_temp_lookalikes_are_never_removed(tmp_path):
    config = make_config(tmp_path)
    pt.install(config)
    d = Path(config.dest_dir)
    lookalike = d / f".{pt.FRAGMENT_NAME}.tmp-1"
    lookalike.write_bytes(GOOD)  # same bytes, different inode
    symlink = d / f".{pt.FRAGMENT_NAME}.tmp-2"
    symlink.symlink_to(pt.FRAGMENT_NAME)
    fifo = d / f".{pt.FRAGMENT_NAME}.tmp-3"
    os.mkfifo(fifo)
    before = _snapshot(config)
    assert pt.install(config) == "already-installed"
    assert pt.remove(config) == "removed"
    after = _snapshot(config)
    assert set(after) == set(before) - {pt.FRAGMENT_NAME}
    # an aliased fragment whose second name is a lookalike of a different file stays a conflict
    (tmp_path / "second").mkdir()
    config2 = make_config(tmp_path / "second")
    pt.install(config2)
    foreign = Path(config2.dest_dir) / ".other.tmp-9"
    os.link(dest_of(config2), foreign)
    with pytest.raises(pt.Refused):
        pt.install(config2)
    assert foreign.exists() and dest_of(config2).exists()


def test_interruption_during_cleanup_is_non_success_and_a_later_install_recovers(tmp_path):
    config = make_config(tmp_path)
    assert pt.main(["install"], config, StuckTemp(KeyboardInterrupt())) == pt.EXIT_INTERRUPTED
    assert dest_of(config).read_bytes() == GOOD and os.lstat(dest_of(config)).st_nlink == 2
    with pytest.raises(KeyboardInterrupt):
        pt.remove(config, StuckTemp(KeyboardInterrupt()))
    assert dest_of(config).exists()  # nothing beyond the attributed names was ever touched
    assert pt.install(config) == "alias-recovered"


# ---- 6. verification ------------------------------------------------------------


def passing(config, systemd=None):
    return pt.verify(config, None, systemd or FakeSystemd(), uptime=lambda: 10_000.0)


def failed(results):
    return {name for name, ok in results if not ok}


def test_verify_passes_for_installed_fragment_correct_directories_and_ordered_polkit(tmp_path):
    config = make_config(tmp_path)
    pt.install(config)
    os.utime(dest_of(config), (1, 1))
    assert failed(passing(config)) == set()


def test_verify_reports_a_fragment_installed_after_this_boot(tmp_path):
    config = make_config(tmp_path)
    pt.install(config)
    assert failed(pt.verify(config, None, FakeSystemd(), uptime=lambda: 1_000.0)) == {"fragment-predates-boot"}


@pytest.mark.parametrize("damage,expected", [
    ("missing-fragment", {"fragment", "fragment-predates-boot"}),
    ("edited-fragment", {"fragment", "fragment-predates-boot"}),
    ("no-run-dir", {"runtime-dir {run}/polkit-1", "runtime-dir {run}/polkit-1/rules.d"}),
    ("no-rules-dir", {"runtime-dir {run}/polkit-1/rules.d"}),
    ("mode", {"runtime-dir {run}/polkit-1/rules.d"}),
    ("mode-parent", {"runtime-dir {run}/polkit-1"}),
    ("owner", {"runtime-dir {run}/polkit-1", "runtime-dir {run}/polkit-1/rules.d"}),
    ("rules-is-file", {"runtime-dir {run}/polkit-1/rules.d"}),
    ("rules-is-symlink", {"runtime-dir {run}/polkit-1/rules.d"}),
])
def test_verify_detects_each_damaged_or_missing_object(tmp_path, damage, expected):
    config = make_config(tmp_path)
    pt.install(config)
    os.utime(dest_of(config), (1, 1))
    run = Path(config.run)
    if damage == "missing-fragment":
        dest_of(config).unlink()
    elif damage == "edited-fragment":
        dest_of(config).write_bytes(GOOD + b"# x\n")
    elif damage == "no-run-dir":
        (run / "polkit-1/rules.d").rmdir()
        (run / "polkit-1").rmdir()
    elif damage == "no-rules-dir":
        (run / "polkit-1/rules.d").rmdir()
    elif damage == "mode":
        os.chmod(run / "polkit-1/rules.d", 0o775)
    elif damage == "mode-parent":
        os.chmod(run / "polkit-1", 0o700)
    elif damage == "owner":
        config = pt.Config(**{**config.__dict__, "gid": GID + 1})
        expected = expected | {"fragment", "fragment-predates-boot"}
    elif damage == "rules-is-file":
        (run / "polkit-1/rules.d").rmdir()
        (run / "polkit-1/rules.d").write_text("")
    elif damage == "rules-is-symlink":
        (run / "polkit-1/rules.d").rmdir()
        (run / "polkit-1/rules.d").symlink_to(run)
    assert failed(passing(config)) == {e.format(run=config.run) for e in expected}


@pytest.mark.parametrize("systemd,expected", [
    (FakeSystemd(polkit={"ActiveState": "failed", "MainPID": "0"}), {"polkit-active"}),
    (FakeSystemd(polkit={"ActiveState": "inactive", "MainPID": "0"}), {"polkit-active"}),
    (FakeSystemd(polkit={"After": "basic.target"}), {"polkit-ordered-after-tmpfiles-setup"}),
    (FakeSystemd(polkit={"ExecMainStartTimestampMonotonic": "400"}), {"tmpfiles-setup-finished-before-polkit-start"}),
    (FakeSystemd(setup={"Result": "exit-code"}), {"tmpfiles-setup-finished-before-polkit-start"}),
    (FakeSystemd(setup={"ExecMainExitTimestampMonotonic": "0"}), {"tmpfiles-setup-finished-before-polkit-start"}),
    (FakeSystemd(fail=True), {"polkit-active", "polkit-ordered-after-tmpfiles-setup",
                              "tmpfiles-setup-finished-before-polkit-start"}),
])
def test_verify_detects_inactive_failed_or_misordered_polkit(tmp_path, systemd, expected):
    config = make_config(tmp_path)
    pt.install(config)
    os.utime(dest_of(config), (1, 1))
    assert failed(passing(config, systemd)) == expected


def test_verify_reports_a_malformed_boot_id_and_a_bad_source(tmp_path):
    config = make_config(tmp_path, source=BAD_SOURCES["extra-entry"])
    Path(config.boot_id_file).write_text("nope")
    assert {"source", "fragment", "boot-id"} <= failed(passing(config))


def test_verify_only_asks_systemd_to_show_the_two_units(tmp_path):
    config = make_config(tmp_path)
    systemd = FakeSystemd()
    passing(config, systemd)
    assert [unit for unit, _ in systemd.calls] == ["polkit.service", "systemd-tmpfiles-setup.service"]


# ---- 7. removal -----------------------------------------------------------------


def test_exact_recognized_removal_then_repeated_removal(tmp_path):
    config = make_config(tmp_path)
    pt.install(config)
    assert pt.remove(config) == "removed"
    assert os.listdir(config.dest_dir) == []
    assert pt.remove(config) == "already-absent"


@pytest.mark.parametrize("kind", ["bytes", "mode", "symlink", "directory"])
def test_changed_or_replaced_destination_is_retained_and_reported(tmp_path, kind):
    config = make_config(tmp_path)
    _plant(config, kind)
    before = _snapshot(config)
    with pytest.raises(pt.Refused) as err:
        pt.remove(config)
    assert (err.value.code, err.value.exit_code) == ("destination-retained", pt.EXIT_CONFLICT)
    assert _snapshot(config) == before


def test_failed_unlink_is_reported_without_a_traceback(tmp_path, capsys):
    config = make_config(tmp_path)
    pt.install(config)

    class Stuck(pt.Fs):
        def unlink_at(self, dir_fd, name):
            raise PermissionError(1, "injected")

    assert pt.main(["remove"], config, Stuck()) == pt.EXIT_IO
    err = capsys.readouterr().err
    assert err == "refused: remove-failed\n" and "Traceback" not in err
    assert dest_of(config).read_bytes() == GOOD


# ---- 8. nothing else is touched -------------------------------------------------


def test_install_and_remove_touch_no_runtime_rule_record_evidence_or_other_fragment(tmp_path):
    config = make_config(tmp_path)
    other = Path(config.dest_dir) / "unrelated.conf"
    other.write_text("d /run/other 0755 root root -\n")
    rule = Path(config.run) / "polkit-1/rules.d/50-freedom-blades-rp11.rules"
    rule.write_text("// not ours to touch\n")
    store = tmp_path / "var-lib-freedom-blades-rp11"
    store.mkdir()
    (store / "record").write_text("x")

    def tree():
        return sorted((str(p), p.lstat().st_mode, p.lstat().st_mtime_ns, p.lstat().st_ino)
                      for root in (tmp_path / "run", store) for p in [root, *root.rglob("*")])

    runtime_before, other_before = tree(), other.stat().st_mtime_ns
    pt.install(config)
    pt.remove(config)
    assert tree() == runtime_before and other.read_text() == "d /run/other 0755 root root -\n"
    assert other.stat().st_mtime_ns == other_before and os.listdir(config.dest_dir) == ["unrelated.conf"]


def test_remove_note_says_run_is_left_until_next_boot(tmp_path, capsys):
    config = make_config(tmp_path)
    pt.main(["install"], config)
    assert pt.main(["remove"], config) == pt.EXIT_OK
    assert "/run/polkit-1 is left in place until the next boot" in capsys.readouterr().out


# ---- command line ---------------------------------------------------------------


def test_cli_exit_codes_and_fixed_diagnostics(tmp_path, capsys):
    config = make_config(tmp_path)
    assert pt.main(["install"], config) == pt.EXIT_OK
    assert pt.main(["install"], config) == pt.EXIT_OK
    assert "install: already-installed" in capsys.readouterr().out
    dest_of(config).write_bytes(b"secret-looking content\n")
    os.chmod(dest_of(config), 0o644)
    assert pt.main(["install"], config) == pt.EXIT_CONFLICT
    captured = capsys.readouterr()
    assert captured.err == "refused: destination-conflict\n" and "secret" not in captured.out + captured.err
    assert pt.main(["verify"], config, None, FakeSystemd()) == pt.EXIT_VERIFY_FAILED
    with pytest.raises(SystemExit) as usage:
        pt.main(["restart"], config)
    assert usage.value.code == pt.EXIT_USAGE


def test_unexpected_exception_prints_no_traceback(tmp_path, capsys):
    config = make_config(tmp_path)

    class Broken(pt.Fs):
        def open_dir(self, path):
            raise RuntimeError("secret detail")

    assert pt.main(["install"], config, Broken()) == pt.EXIT_IO
    err = capsys.readouterr().err
    assert err == "error: unexpected-failure\n"


def test_module_exposes_no_path_argument_or_environment_override():
    source = (REPO / "tools/polkit_tmpfiles.py").read_text()
    assert "os.environ" not in source and "getenv" not in source
    help_text = subprocess.run([sys.executable, "-B", "-m", "tools.polkit_tmpfiles", "-h"], cwd=REPO,
                               capture_output=True, text=True).stdout
    assert "--" not in help_text.replace("--help", "").replace("-h, ", "")


# ---- 9. structural: no Polkit restart, reload or bus action ----------------------

FORBIDDEN = re.compile(
    r"restart|reload|try-|kill|stop|start-unit|StartUnit|StopUnit|ReloadUnit|RestartUnit|"
    r"reexec|dbus|jeepney|busctl|Manager|enable|disable|mask|daemon", re.IGNORECASE)


def _code_tokens(path: Path):
    tree = ast.parse(path.read_text())
    docstrings = {id(node.body[0].value) for node in ast.walk(tree)
                  if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)) and node.body
                  and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant)}
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            yield node.value
        elif isinstance(node, ast.Name):
            yield node.id
        elif isinstance(node, ast.Attribute):
            yield node.attr
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            yield from (a.name for a in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                yield node.module


def test_production_code_cannot_restart_reload_or_signal_polkit():
    offenders = [t for t in _code_tokens(REPO / "tools/polkit_tmpfiles.py")
                 if FORBIDDEN.search(t) and t not in {"EXIT_INTERRUPTED"}]
    assert offenders == []


def test_systemctl_is_only_ever_invoked_with_show():
    seen = []

    def fake_run(argv, **kwargs):
        seen.append(argv)
        return subprocess.CompletedProcess(argv, 0, stdout="ActiveState=active\n", stderr="")

    original = subprocess.run
    subprocess.run = fake_run
    try:
        pt.SystemdFacts().show("polkit.service", ("ActiveState",))
    finally:
        subprocess.run = original
    assert seen == [[pt.SYSTEMCTL, "show", "polkit.service", "--property=ActiveState"]]
    assert sum(1 for node in ast.walk(ast.parse((REPO / "tools/polkit_tmpfiles.py").read_text()))
               if isinstance(node, ast.Call) and getattr(node.func, "attr", "") in {"run", "Popen", "call", "check_call", "check_output", "system"}) == 1


# ---- 10. effective configuration: higher-priority same-name overrides --------------

LAYERS = (0, 1, 2)  # /etc/tmpfiles.d, /run/tmpfiles.d, /usr/local/lib/tmpfiles.d (fixed order in production)


def override_path(config, layer):
    return Path(config.override_dirs[layer]) / pt.FRAGMENT_NAME


def plant_override(config, layer, kind):
    path = override_path(config, layer)
    if kind == "regular":
        path.write_bytes(b"d /run/other 0755 root root -\n")
    elif kind == "identical":
        path.write_bytes(GOOD)
        os.chmod(path, 0o644)
    elif kind == "directory":
        path.mkdir()
    elif kind == "fifo":
        os.mkfifo(path, 0o644)
    elif kind == "symlink":
        (path.parent / "real.conf").write_bytes(GOOD)
        path.symlink_to("real.conf")
    elif kind == "dangling":
        path.symlink_to("nowhere")
    elif kind == "devnull":
        path.symlink_to("/dev/null")
    return path


OVERRIDE_KINDS = ["regular", "identical", "directory", "fifo", "symlink", "dangling", "devnull"]


def tree_snapshot(root):
    out = {}
    for p in sorted([root, *root.rglob("*")]):
        info = p.lstat()
        out[str(p)] = (info.st_mode, info.st_ino, info.st_size, info.st_mtime_ns,
                       os.readlink(p) if stat.S_ISLNK(info.st_mode) else None)
    return out


@pytest.mark.parametrize("kind", OVERRIDE_KINDS)
@pytest.mark.parametrize("layer", LAYERS)
def test_install_refuses_while_an_override_shadows_the_fragment_and_writes_nothing(tmp_path, layer, kind):
    config = make_config(tmp_path)
    plant_override(config, layer, kind)
    before_override, before_dest = tree_snapshot(tmp_path / "override"), tree_snapshot(Path(config.dest_dir))
    with pytest.raises(pt.Refused) as err:
        pt.install(config)
    assert (err.value.code, err.value.exit_code) == ("override-shadows-fragment", pt.EXIT_CONFLICT)
    assert tree_snapshot(tmp_path / "override") == before_override
    assert tree_snapshot(Path(config.dest_dir)) == before_dest  # nothing published, no temp left


@pytest.mark.parametrize("kind", OVERRIDE_KINDS)
@pytest.mark.parametrize("layer", LAYERS)
def test_an_override_planted_after_install_is_never_reported_as_verified_or_reinstalled(tmp_path, layer, kind):
    config = make_config(tmp_path)
    assert pt.install(config) == "installed"
    os.utime(dest_of(config), (1, 1))
    assert failed(passing(config)) == set()
    plant_override(config, layer, kind)
    # runtime directories exist and every mocked systemd fact passes; only the override fails
    assert failed(passing(config)) == {"no-higher-priority-override"}
    with pytest.raises(pt.Refused) as err:
        pt.install(config)  # not "already-installed"
    assert err.value.code == "override-shadows-fragment"


def test_verify_cli_never_prints_ok_while_shadowed_and_prints_no_host_content(tmp_path, capsys):
    config = make_config(tmp_path)
    pt.install(config)
    os.utime(dest_of(config), (1, 1))
    plant_override(config, 0, "regular")
    code = pt.main(["verify"], config, None, FakeSystemd())
    out = capsys.readouterr().out
    assert code == pt.EXIT_VERIFY_FAILED and "verify: ok" not in out
    assert "FAIL no-higher-priority-override" in out and str(tmp_path / "override") not in out and "d /run/other" not in out


@pytest.mark.parametrize("how", ["symlinked-directory", "not-a-directory"])
def test_an_override_layer_that_cannot_be_shown_empty_fails_closed(tmp_path, how):
    config = make_config(tmp_path)
    layer = Path(config.override_dirs[1])
    layer.rmdir()
    if how == "symlinked-directory":
        layer.symlink_to(tmp_path)
    else:
        layer.write_text("")
    with pytest.raises(pt.Refused) as err:
        pt.install(config)
    assert err.value.code == "override-shadows-fragment"
    assert "no-higher-priority-override" in failed(passing(config))


def test_absent_override_layers_are_clean(tmp_path):
    config = make_config(tmp_path)
    for d in config.override_dirs:
        Path(d).rmdir()
    assert pt.install(config) == "installed"
    os.utime(dest_of(config), (1, 1))
    assert failed(passing(config)) == set()


@pytest.mark.parametrize("kind", OVERRIDE_KINDS)
@pytest.mark.parametrize("layer", LAYERS)
def test_remove_never_touches_an_override_and_says_it_still_shadows(tmp_path, capsys, layer, kind):
    config = make_config(tmp_path)
    pt.install(config)
    plant_override(config, layer, kind)
    before = tree_snapshot(tmp_path / "override")
    assert pt.main(["remove"], config) == pt.EXIT_OK
    out = capsys.readouterr().out
    assert "remove: removed" in out and "still shadows" in out
    assert tree_snapshot(tmp_path / "override") == before
    assert os.listdir(config.dest_dir) == []
    assert pt.main(["remove"], config) == pt.EXIT_OK  # repeated: absent, still reported as shadowed
    out = capsys.readouterr().out
    assert "remove: already-absent" in out and "still shadows" in out
    assert tree_snapshot(tmp_path / "override") == before


def test_without_an_override_remove_makes_no_shadow_statement(tmp_path, capsys):
    config = make_config(tmp_path)
    pt.main(["install"], config)
    pt.main(["remove"], config)
    assert "shadows" not in capsys.readouterr().out


def test_an_override_appearing_during_install_is_not_reported_as_success(tmp_path):
    config = make_config(tmp_path)

    class Late(pt.Fs):
        def link_at(self, dir_fd, source, dest):
            super().link_at(dir_fd, source, dest)
            plant_override(config, 0, "devnull")

    with pytest.raises(pt.Refused) as err:
        pt.install(config, Late())
    assert err.value.code == "override-shadows-fragment"
    assert dest_of(config).read_bytes() == GOOD and os.lstat(dest_of(config)).st_nlink == 1


# ---- 11. removal and alias cleanup are bound to the inspected inode ----------------

FOREIGN = b"foreign content that must never be printed\n"
REPLACEMENTS = ["regular", "symlink", "directory", "fifo"]


def put_foreign(path: Path, kind: str):
    if os.path.lexists(path):
        if path.is_dir() and not path.is_symlink():
            path.rmdir()
        else:
            path.unlink()
    if kind == "regular":
        path.write_bytes(FOREIGN)
        os.chmod(path, 0o644)
    elif kind == "symlink":
        path.symlink_to("elsewhere")
    elif kind == "directory":
        path.mkdir()
    elif kind == "fifo":
        os.mkfifo(path, 0o644)


class Replacing(pt.Fs):
    """Swaps ``target`` for a foreign object immediately before its destructive step."""

    def __init__(self, directory, target, kind):
        self.path, self.target, self.kind, self.done = Path(directory) / target, target, kind, False

    def rename_noreplace(self, dir_fd, src, dst):
        if src == self.target and not self.done:
            self.done = True
            put_foreign(self.path, self.kind)
        super().rename_noreplace(dir_fd, src, dst)

    def unlink_at(self, dir_fd, name):  # a design that unlinks by public name would be caught here
        if name == self.target and not self.done:
            self.done = True
            put_foreign(self.path, self.kind)
        super().unlink_at(dir_fd, name)


def assert_foreign_retained(config, name, kind, before_ino):
    path = Path(config.dest_dir) / name
    info = os.lstat(path)
    assert info.st_ino == before_ino
    assert {"regular": stat.S_ISREG, "symlink": stat.S_ISLNK, "directory": stat.S_ISDIR,
            "fifo": stat.S_ISFIFO}[kind](info.st_mode)
    assert not [n for n in os.listdir(config.dest_dir) if ".del-" in n]


@pytest.mark.parametrize("kind", REPLACEMENTS)
def test_remove_retains_a_replacement_of_the_public_name_and_is_non_success(tmp_path, capsys, kind):
    config = make_config(tmp_path)
    pt.install(config)
    fs = Replacing(config.dest_dir, pt.FRAGMENT_NAME, kind)
    assert pt.main(["remove"], config, fs) == pt.EXIT_CONFLICT
    captured = capsys.readouterr()
    assert captured.err == "refused: destination-changed\n" and "removed" not in captured.out
    assert "foreign" not in captured.out + captured.err
    assert_foreign_retained(config, pt.FRAGMENT_NAME, kind, os.lstat(dest_of(config)).st_ino)
    assert os.listdir(config.dest_dir) == [pt.FRAGMENT_NAME]


@pytest.mark.parametrize("kind", REPLACEMENTS)
def test_remove_retains_a_replaced_attributed_alias_and_leaves_the_fragment(tmp_path, capsys, kind):
    config = make_config(tmp_path)
    alias = _leak_alias(config)
    fs = Replacing(config.dest_dir, alias, kind)
    assert pt.main(["remove"], config, fs) == pt.EXIT_CONFLICT
    captured = capsys.readouterr()
    assert "removed" not in captured.out and "foreign" not in captured.out + captured.err
    assert_foreign_retained(config, alias, kind, os.lstat(Path(config.dest_dir) / alias).st_ino)
    assert dest_of(config).read_bytes() == GOOD


@pytest.mark.parametrize("kind", REPLACEMENTS)
def test_install_alias_recovery_retains_a_replaced_alias_and_is_non_success(tmp_path, capsys, kind):
    config = make_config(tmp_path)
    alias = _leak_alias(config)
    fs = Replacing(config.dest_dir, alias, kind)
    assert pt.main(["install"], config, fs) == pt.EXIT_CONFLICT
    captured = capsys.readouterr()
    assert "alias-recovered" not in captured.out and "foreign" not in captured.out + captured.err
    assert_foreign_retained(config, alias, kind, os.lstat(Path(config.dest_dir) / alias).st_ino)


@pytest.mark.parametrize("kind", REPLACEMENTS)
def test_install_temp_cleanup_never_deletes_a_replaced_temporary_name(tmp_path, kind):
    config = make_config(tmp_path)
    temp = f".{pt.FRAGMENT_NAME}.tmp-{os.getpid()}"
    fs = Replacing(config.dest_dir, temp, kind)
    with pytest.raises(pt.Refused) as err:
        pt.install(config, fs)
    assert err.value.exit_code in (pt.EXIT_IO, pt.EXIT_CONFLICT)
    assert (Path(config.dest_dir) / temp).exists() or (Path(config.dest_dir) / temp).is_symlink()
    assert dest_of(config).read_bytes() == GOOD


def test_a_replacement_that_cannot_be_restored_is_retained_in_quarantine_and_blocks_later_runs(tmp_path, capsys):
    config = make_config(tmp_path)
    pt.install(config)

    class Reclaimed(Replacing):
        def rename_noreplace(self, dir_fd, src, dst):
            if dst == pt.FRAGMENT_NAME and src != self.target:  # the restore step
                put_foreign(self.path, "regular")  # a third party re-created the public name
            super().rename_noreplace(dir_fd, src, dst)

    fs = Reclaimed(config.dest_dir, pt.FRAGMENT_NAME, "symlink")
    assert pt.main(["remove"], config, fs) == pt.EXIT_IO
    assert capsys.readouterr().err == "refused: quarantine-retained\n"
    names = sorted(os.listdir(config.dest_dir))
    assert len(names) == 2 and pt.FRAGMENT_NAME in names  # the replacement is still on disk
    assert dest_of(config).read_bytes() == FOREIGN
    quarantine = [n for n in names if n != pt.FRAGMENT_NAME][0]
    assert os.path.islink(Path(config.dest_dir) / quarantine)
    for action in (pt.install, pt.remove):
        with pytest.raises(pt.Refused) as err:
            action(config)
        assert err.value.code == "quarantine-residue"
    assert "no-quarantine-residue" in failed(passing(config))


# ---- 12. serialization of the mutating actions -----------------------------------------


def hold_lock(config):
    fd = os.open(config.dest_dir, os.O_RDONLY | os.O_DIRECTORY)
    import fcntl

    fcntl.flock(fd, fcntl.LOCK_EX)
    return fd


@pytest.mark.parametrize("action", ["install", "remove"])
def test_a_busy_lock_is_a_bounded_non_success_and_changes_nothing(tmp_path, capsys, action):
    config = make_config(tmp_path)
    if action == "remove":
        pt.install(config)
    before = _snapshot(config)
    fd = hold_lock(config)
    try:
        started = pt.time.monotonic()
        assert pt.main([action], config) == pt.EXIT_IO
        assert pt.time.monotonic() - started < 5
    finally:
        os.close(fd)
    assert capsys.readouterr().err == "refused: lock-busy\n"
    assert _snapshot(config) == before
    assert pt.main([action], config) == pt.EXIT_OK  # released: works again


def test_verify_does_not_take_the_lock(tmp_path):
    config = make_config(tmp_path)
    pt.install(config)
    fd = hold_lock(config)
    try:
        assert "fragment" not in failed(passing(config))
    finally:
        os.close(fd)


def test_install_during_a_remove_cannot_be_erased_by_the_stale_remover(tmp_path):
    config = make_config(tmp_path)
    pt.install(config)
    seen = {}

    class Remover(pt.Fs):
        def rename_noreplace(self, dir_fd, src, dst):
            # the remover has inspected and holds the lock; a second operator tries to install
            try:
                pt.install(config)
            except pt.Refused as refusal:
                seen["install"] = refusal.code
            super().rename_noreplace(dir_fd, src, dst)

    assert pt.remove(config, Remover()) == "removed"
    assert seen == {"install": "lock-busy"}
    assert os.listdir(config.dest_dir) == []  # the final state is what both results say
    assert pt.install(config) == "installed"


def test_remove_during_an_install_cannot_remove_the_new_fragment(tmp_path):
    config = make_config(tmp_path)
    seen = {}

    class Installer(pt.Fs):
        def link_at(self, dir_fd, source, dest):
            try:
                pt.remove(config)
            except pt.Refused as refusal:
                seen["remove"] = refusal.code
            super().link_at(dir_fd, source, dest)

    assert pt.install(config, Installer()) == "installed"
    assert seen == {"remove": "lock-busy"}
    assert dest_of(config).read_bytes() == GOOD


def test_a_waiting_install_proceeds_after_the_remover_finishes(tmp_path):
    import threading

    base = make_config(tmp_path)
    config = pt.Config(**{**base.__dict__, "lock_timeout_s": 10.0})
    pt.install(config)
    results = {}

    def late_install():
        results["install"] = pt.install(config)

    thread = threading.Thread(target=late_install)

    class Remover(pt.Fs):
        def rename_noreplace(self, dir_fd, src, dst):
            if not thread.is_alive():
                thread.start()
                pt.time.sleep(0.3)  # the installer is now waiting on the lock
            super().rename_noreplace(dir_fd, src, dst)

    assert pt.remove(config, Remover()) == "removed"
    thread.join(10)
    assert results == {"install": "installed"}
    assert dest_of(config).read_bytes() == GOOD


# ---- 13. injected failure and interruption at every new mutation step -------------------


class Boom(pt.Fs):
    """Fails (or is interrupted at) the Nth call of one seam."""

    def __init__(self, seam, error, nth=1):
        self.seam, self.error, self.nth, self.count = seam, error, nth, 0

    def _hit(self, seam):
        if seam == self.seam:
            self.count += 1
            if self.count == self.nth:
                raise self.error

    def flock_nb(self, fd):
        self._hit("lock")
        super().flock_nb(fd)

    def rename_noreplace(self, dir_fd, src, dst):
        self._hit("rename" if dst.startswith(".") else "restore")
        super().rename_noreplace(dir_fd, src, dst)

    def lstat_at(self, dir_fd, name):
        if ".del-" in name:
            self._hit("lstat-quarantine")
        return super().lstat_at(dir_fd, name)

    def unlink_at(self, dir_fd, name):
        self._hit("unlink")
        super().unlink_at(dir_fd, name)

    def fsync(self, fd):
        self._hit("fsync")
        super().fsync(fd)


IO = OSError(5, "injected")


@pytest.mark.parametrize("seam", ["rename", "lstat-quarantine", "unlink"])
@pytest.mark.parametrize("action", ["remove", "alias-install"])
def test_failure_in_a_retirement_step_restores_the_object_and_is_non_success(tmp_path, seam, action):
    config = make_config(tmp_path)
    if action == "remove":
        pt.install(config)
    else:
        _leak_alias(config)
    before = _snapshot(config)
    run = pt.remove if action == "remove" else pt.install
    with pytest.raises(pt.Refused) as err:
        run(config, Boom(seam, IO))
    assert err.value.exit_code == pt.EXIT_IO
    assert _snapshot(config) == before  # nothing lost, nothing renamed away, no quarantine left


@pytest.mark.parametrize("seam", ["rename", "lstat-quarantine", "unlink"])
def test_interruption_in_a_retirement_step_restores_the_object(tmp_path, seam):
    config = make_config(tmp_path)
    pt.install(config)
    before = _snapshot(config)
    with pytest.raises(KeyboardInterrupt):
        pt.remove(config, Boom(seam, KeyboardInterrupt()))
    assert _snapshot(config) == before


@pytest.mark.parametrize("seam", ["lstat-quarantine", "unlink"])
def test_failure_followed_by_a_failed_restore_reports_the_exact_residue(tmp_path, capsys, seam):
    config = make_config(tmp_path)
    pt.install(config)

    class Both(Boom):
        def rename_noreplace(self, dir_fd, src, dst):
            if dst == pt.FRAGMENT_NAME:
                raise IO
            super().rename_noreplace(dir_fd, src, dst)

    assert pt.main(["remove"], config, Both(seam, IO)) == pt.EXIT_IO
    assert capsys.readouterr().err == "refused: quarantine-retained\n"
    names = os.listdir(config.dest_dir)
    assert len(names) == 1 and ".del-" in names[0]  # the recognized object survives, named
    assert (Path(config.dest_dir) / names[0]).read_bytes() == GOOD


@pytest.mark.parametrize(
    ("error", "exit_code"),
    [(IO, pt.EXIT_IO), (KeyboardInterrupt(), pt.EXIT_INTERRUPTED)],
)
def test_replacement_restore_failure_reports_quarantine_residue(tmp_path, capsys, error, exit_code):
    config = make_config(tmp_path)
    pt.install(config)

    class RestoreFails(Replacing):
        def rename_noreplace(self, dir_fd, src, dst):
            if dst == pt.FRAGMENT_NAME and src != self.target:
                raise error
            super().rename_noreplace(dir_fd, src, dst)

    assert pt.main(["remove"], config, RestoreFails(config.dest_dir, pt.FRAGMENT_NAME, "symlink")) == exit_code
    assert capsys.readouterr().err == "refused: quarantine-retained\n"
    names = os.listdir(config.dest_dir)
    assert len(names) == 1 and ".del-" in names[0]
    assert os.path.islink(Path(config.dest_dir) / names[0])


@pytest.mark.parametrize(
    ("error", "exit_code"),
    [(IO, pt.EXIT_IO), (KeyboardInterrupt(), pt.EXIT_INTERRUPTED)],
)
def test_replacement_restore_flush_failure_reports_uncertain_durability(tmp_path, capsys, error, exit_code):
    config = make_config(tmp_path)
    pt.install(config)

    class RestoreFlushFails(Replacing):
        def fsync(self, fd):
            raise error

    fs = RestoreFlushFails(config.dest_dir, pt.FRAGMENT_NAME, "symlink")
    assert pt.main(["remove"], config, fs) == exit_code
    assert capsys.readouterr().err == "refused: restore-durability-uncertain\n"
    assert os.path.islink(dest_of(config))
    assert not [name for name in os.listdir(config.dest_dir) if ".del-" in name]


def test_failed_directory_flush_after_removal_is_non_success(tmp_path, capsys):
    config = make_config(tmp_path)
    pt.install(config)
    assert pt.main(["remove"], config, Boom("fsync", IO)) == pt.EXIT_IO
    assert capsys.readouterr().err == "refused: remove-failed\n"
    assert os.listdir(config.dest_dir) == []  # the entry is gone; durability is not claimed


@pytest.mark.parametrize("action", ["install", "remove"])
@pytest.mark.parametrize("error", [IO, KeyboardInterrupt()])
def test_lock_failure_or_interruption_changes_nothing(tmp_path, action, error):
    config = make_config(tmp_path)
    if action == "remove":
        pt.install(config)
    before = _snapshot(config)
    run = pt.install if action == "install" else pt.remove
    if isinstance(error, KeyboardInterrupt):
        with pytest.raises(KeyboardInterrupt):
            run(config, Boom("lock", error))
    else:
        with pytest.raises(pt.Refused) as err:
            run(config, Boom("lock", error))
        assert (err.value.code, err.value.exit_code) == ("lock-failed", pt.EXIT_IO)
    assert _snapshot(config) == before


def test_quarantine_residue_is_refused_not_adopted_or_deleted(tmp_path):
    config = make_config(tmp_path)
    pt.install(config)
    residue = Path(config.dest_dir) / f".{pt.FRAGMENT_NAME}.del-77"
    residue.write_bytes(b"leftover\n")
    before = _snapshot(config)
    for action in (pt.install, pt.remove):
        with pytest.raises(pt.Refused) as err:
            action(config)
        assert (err.value.code, err.value.exit_code) == ("quarantine-residue", pt.EXIT_CONFLICT)
    assert _snapshot(config) == before
