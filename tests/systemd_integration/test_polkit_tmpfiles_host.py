"""The Polkit ``tmpfiles.d`` installer against a real root-owned tree and real systemd.

Real root behaviour only: ownership, ``link(2)`` semantics and ``systemd-tmpfiles``
parsing of the repository fragment. Conflict and removal cases use synthetic
objects in a throwaway root-owned directory; the installed system fragment is
never modified by this module.

    sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test \\
        /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs \\
        tests/systemd_integration/test_polkit_tmpfiles_host.py
"""

from __future__ import annotations

import os
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

if os.environ.get("FREEDOM_SYSTEMD_INTEGRATION") != "oracle-test":
    pytest.skip("set FREEDOM_SYSTEMD_INTEGRATION=oracle-test (disposable host only)", allow_module_level=True)
if socket.gethostname() != "Test":
    pytest.skip("refusing to run: not the disposable host (hostname != Test)", allow_module_level=True)
if os.geteuid() != 0 or not Path("/run/systemd/system").is_dir():
    pytest.skip("needs root on a systemd host", allow_module_level=True)

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools import polkit_tmpfiles as pt  # noqa: E402

GOOD = (Path(__file__).resolve().parents[2] / pt.SOURCE_RELATIVE).read_bytes()
INSTALLED = Path("/usr/lib/tmpfiles.d") / pt.FRAGMENT_NAME


@pytest.fixture
def root_dir():
    path = Path(tempfile.mkdtemp(prefix="rp11-tmpfiles-", dir="/var/tmp"))
    os.chown(path, 0, 0)
    os.chmod(path, 0o755)
    yield path
    shutil.rmtree(path, ignore_errors=True)


def config(root_dir: Path, **extra) -> pt.Config:
    # throwaway override layers: the real /etc, /run and /usr/local tmpfiles.d are never written
    layers = tuple(str(root_dir / "layer" / n) for n in ("etc", "run", "local"))
    for layer in layers:
        os.makedirs(layer, mode=0o755, exist_ok=True)
    return pt.Config(dest_dir=str(root_dir / "dest"), override_dirs=layers, **extra)


@pytest.fixture(autouse=True)
def _dest(root_dir):
    (root_dir / "dest").mkdir(mode=0o755)
    os.chown(root_dir / "dest", 0, 0)


def test_real_root_install_idempotence_conflict_and_removal(root_dir):
    cfg = config(root_dir)
    dest = root_dir / "dest" / pt.FRAGMENT_NAME
    dest.write_bytes(b"synthetic conflicting file\n")
    os.chmod(dest, 0o644)
    with pytest.raises(pt.Refused) as err:
        pt.install(cfg)
    assert err.value.exit_code == pt.EXIT_CONFLICT and dest.read_bytes() == b"synthetic conflicting file\n"
    with pytest.raises(pt.Refused):
        pt.remove(cfg)
    dest.unlink()
    assert pt.install(cfg) == "installed"
    info = dest.lstat()
    assert (info.st_uid, info.st_gid, stat.S_IMODE(info.st_mode), info.st_nlink) == (0, 0, 0o644, 1)
    assert dest.read_bytes() == GOOD
    assert pt.install(cfg) == "already-installed"
    assert pt.remove(cfg) == "removed" and pt.remove(cfg) == "already-absent"
    assert list((root_dir / "dest").iterdir()) == []


def test_non_root_owned_destination_directory_is_refused(root_dir):
    os.chown(root_dir / "dest", 65534, 65534)
    with pytest.raises(pt.Refused) as err:
        pt.install(config(root_dir))
    assert err.value.code == "destination-directory-unsafe"


def test_systemd_tmpfiles_parses_the_fragment_and_makes_exactly_the_two_directories(root_dir):
    """Run the repository fragment against a throwaway root, never ``/run``."""
    fragment = root_dir / "fragment.conf"
    fragment.write_bytes(GOOD)
    sandbox = root_dir / "root"
    sandbox.mkdir()
    done = subprocess.run(["systemd-tmpfiles", "--create", f"--root={sandbox}", str(fragment)],
                          capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    made = sorted(str(p.relative_to(sandbox)) for p in sandbox.rglob("*"))
    assert made == ["run", "run/polkit-1", "run/polkit-1/rules.d"]
    for rel in ("run/polkit-1", "run/polkit-1/rules.d"):
        info = (sandbox / rel).lstat()
        assert (info.st_uid, info.st_gid, stat.S_IMODE(info.st_mode)) == (0, 0, 0o755)


def test_live_verify_agrees_with_whether_the_fragment_is_installed():
    checks = dict(pt.verify(pt.Config()))
    assert checks["source"] and checks["boot-id"]
    assert checks["fragment"] == INSTALLED.is_file()
    assert checks["polkit-active"] and checks["polkit-ordered-after-tmpfiles-setup"]
    if not INSTALLED.is_file():
        assert not checks["fragment-predates-boot"]


def test_real_root_override_in_each_layer_blocks_install_and_verify_and_survives_remove(root_dir):
    for index, kind in enumerate(("devnull", "regular", "dangling")):
        cfg = config(root_dir)
        victim = Path(cfg.override_dirs[index]) / pt.FRAGMENT_NAME
        {"devnull": lambda: victim.symlink_to("/dev/null"),
         "regular": lambda: victim.write_bytes(GOOD),
         "dangling": lambda: victim.symlink_to("nowhere")}[kind]()
        with pytest.raises(pt.Refused) as err:
            pt.install(cfg)
        assert err.value.code == "override-shadows-fragment"
        assert list((root_dir / "dest").iterdir()) == []
        victim.unlink()
        assert pt.install(cfg) == "installed"
        victim_again = {"devnull": lambda: victim.symlink_to("/dev/null"),
                        "regular": lambda: victim.write_bytes(GOOD),
                        "dangling": lambda: victim.symlink_to("nowhere")}[kind]
        victim_again()
        checks = dict(pt.verify(cfg))
        assert checks["no-higher-priority-override"] is False
        before = victim.lstat()
        assert pt.remove(cfg) == "removed"
        assert victim.lstat().st_ino == before.st_ino  # untouched
        victim.unlink()


def test_real_root_lock_is_exclusive_between_processes_and_bounded(root_dir):
    cfg = config(root_dir, lock_timeout_s=0.5)
    holder = subprocess.Popen(
        [sys.executable, "-c",
         "import fcntl,os,sys;fd=os.open(sys.argv[1],os.O_RDONLY|os.O_DIRECTORY);"
         "fcntl.flock(fd,fcntl.LOCK_EX);print('held',flush=True);sys.stdin.read()", cfg.dest_dir],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    try:
        assert holder.stdout.readline().strip() == "held"
        for action in (pt.install, pt.remove):
            with pytest.raises(pt.Refused) as err:
                action(cfg)
            assert err.value.code == "lock-busy"
        assert list((root_dir / "dest").iterdir()) == []
    finally:
        holder.communicate("")  # closing stdin ends the holder and releases the lock
    assert pt.install(cfg) == "installed"
    assert pt.remove(cfg) == "removed"


def test_real_root_quarantine_rename_never_overwrites_and_restores_a_foreign_replacement(root_dir):
    cfg = config(root_dir)
    dest = root_dir / "dest" / pt.FRAGMENT_NAME
    assert pt.install(cfg) == "installed"

    class Swap(pt.Fs):
        def rename_noreplace(self, dir_fd, source, target):
            if source == pt.FRAGMENT_NAME:
                dest.unlink()
                os.mkfifo(dest, 0o644)
            super().rename_noreplace(dir_fd, source, target)

    with pytest.raises(pt.Refused) as err:
        pt.remove(cfg, Swap())
    assert err.value.code == "destination-changed"
    assert stat.S_ISFIFO(dest.lstat().st_mode) and [p.name for p in dest.parent.iterdir()] == [pt.FRAGMENT_NAME]
