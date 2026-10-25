"""The executor supervisor *package* on the disposable host: ``install`` / ``verify`` / ``verify-ready`` / ``remove`` of the
production unit as a root-owned **system service** running as the dedicated account, against a root-owned test package, a
dedicated lingering account, a second lingering user and the exact SA-2 sudoers vector.

Nothing of the real tree is chowned. A root-owned copy of the repository and a root-owned Python 3.14 venv (with the
repository's pinned ``jeepney``) are bind-mounted over ``/opt/freedom-blades`` for the module and unmounted afterwards; the
accounts, their linger, the sudoers drop-in, the shadow tree, the decoys, the SA-2 stand-in artifact and every mount are created
here and removed (and asserted removed).

    sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test \\
        /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs -s \\
        tests/systemd_integration/test_executor_package_host.py

Production and staging are never touched; nothing here is a production installation.
"""

from __future__ import annotations

import os
import pwd
import secrets
import shutil
import stat
import subprocess
import threading
import time
import tracemalloc
from pathlib import Path

import pytest

import test_route3_hold_host as hold_host  # noqa: F401  (applies the same disposable-host guards)
from test_route3_hold_host import run, wait_until

from adapters.executor.ownership import START_SENT, Record
from executor_host_support import boot_id, linger_state, sctl, sshow
from tools import executor_supervisor_install as tool_module
from tools.executor_supervisor_install import ACCOUNT, SA2, UNIT, DrainSession, Installer

REPO = Path(__file__).resolve().parents[2]
REAL_ROOT = Path("/opt/freedom-blades")
TOKEN = secrets.token_hex(3)
SHADOW = Path(f"/var/tmp/fbpkg-{TOKEN}")
SUDOERS = Path(f"/etc/sudoers.d/zz-fbpkg-{TOKEN}")
DECOY = Path(f"/srv/fbpkg-{TOKEN}-decoy")
OTHER = f"fbpkgother{TOKEN}"
PY314 = "/usr/bin/python3.14"
SITE = REAL_ROOT / "runtime/venv-web/lib/python3.12/site-packages"
LIBEXEC = Path("/usr/local/libexec/freedom-blades-rp11")
ARTIFACT = LIBEXEC / "rp11_h1.py"
SYSTEM_DIR = Path("/etc/systemd/system")
USER_UNIT_DIR = Path("/etc/systemd/user")
STATE = Path("/var/lib/freedom-blades-executor")
RUNTIME = Path("/run/freedom-blades-executor")
SPAM = (
    "import random, sys, time\n"
    "from adapters.executor.interrupt import SudoStopInvoker\n"
    "end = time.time() + float(sys.argv[1]); invoker = SudoStopInvoker(deadline_seconds=60)\n"
    "while time.time() < end:\n"
    "    t0 = time.time(); name = invoker.invoke_stop().name\n"
    "    print(f'{t0:.6f} {time.time():.6f} {name}', flush=True)\n"
    "    time.sleep(random.random() * float(sys.argv[2]))\n"
)
ONE_STOP = "from adapters.executor.interrupt import SudoStopInvoker\nprint(SudoStopInvoker(deadline_seconds=60).invoke_stop().name)\n"
#: The SA-2 artifact stand-in: ``stop`` lasts a few seconds and then succeeds, so an in-flight invocation can be inspected.
STAND_IN_ARTIFACT = "import sys, time\ntime.sleep(float(open('/usr/local/libexec/freedom-blades-rp11/hold').read()))\nsys.exit(0)\n"


def listing(path: Path) -> list[str]:
    return sorted(p.name for p in path.iterdir()) if path.exists() else []


def mounted(path: Path) -> bool:
    return any(line.split()[4] == str(path) for line in Path("/proc/self/mountinfo").read_text().splitlines())


def residue() -> dict:
    """Everything the proof could leave behind that the final cleanliness check compares with the start."""
    return {
        "etc_user": listing(USER_UNIT_DIR), "user_wants": listing(USER_UNIT_DIR / "default.target.wants"),
        "etc_system": [n for n in listing(SYSTEM_DIR) if "freedom" in n or "fbexec" in n or "fbpkg" in n],
        "multi_user_wants": listing(SYSTEM_DIR / "multi-user.target.wants"),
        "linger_dir": listing(Path("/var/lib/systemd/linger")), "home": listing(Path("/home")), "sudoers": listing(Path("/etc/sudoers.d")),
        "state": [n for n in listing(Path("/var/lib")) if n.startswith(("freedom-blades-executor", "fbexec"))],
        "runtime": [n for n in listing(Path("/run")) if n.startswith(("freedom-blades-executor", "fbexec"))],
        "libexec": listing(LIBEXEC), "srv": [n for n in listing(Path("/srv")) if n.startswith("fbpkg")],
        "manager_env": run("systemctl", "show-environment").stdout, "ubuntu_linger": linger_state(),
        "ubuntu_state": listing(Path(pwd.getpwnam("ubuntu").pw_dir) / ".local/state"),
        "polkit": run("systemctl", "is-active", "polkit.service").stdout.strip(),
    }


@pytest.fixture(scope="module")
def package():
    """A root-owned package, its account, a second lingering user and the sudoers entry; all undone (and checked) on exit."""
    assert not mounted(REAL_ROOT), "a previous run left /opt/freedom-blades mounted"
    for name in (ACCOUNT, OTHER):
        with pytest.raises(KeyError):
            pwd.getpwnam(name)
    assert not SUDOERS.exists() and not (USER_UNIT_DIR / UNIT).exists() and not (SYSTEM_DIR / UNIT).exists()
    before = residue()
    assert before["state"] == [] and before["runtime"] == [], "an earlier run left supervisor state or runtime"
    before_root, before_tmp = os.lstat(REAL_ROOT), os.lstat("/var/tmp")
    mounts, account, other = [], None, None
    original_cwd = os.getcwd()
    os.chdir("/")  # nothing of this process may be inside the shadow mount, or it could never be unmounted
    try:
        tree = SHADOW / "freedom-blades"
        (tree / "runtime").mkdir(parents=True)
        run("rsync", "-a", "--chown=root:root", "--chmod=D755,F644", "--exclude=.git", "--exclude=venv-web", "--exclude=venv",
            "--exclude=__pycache__", "--exclude=*.pyc", "--exclude=.pytest_cache", "--exclude=node_modules",
            f"{REPO}/", f"{tree}/platform/", check=True)
        run("env", f"UV_CACHE_DIR={SHADOW}/uv-cache", "/usr/local/bin/uv", "venv", "--python", PY314, f"{tree}/runtime/venv-web", check=True)
        (site,) = (tree / "runtime/venv-web/lib").glob("python3.*/site-packages")
        for item in SITE.glob("jeepney*"):  # the pinned pure-Python dependency, copied from the repository's own venv
            run("cp", "-a", str(item), str(site), check=True)
        run("chown", "-R", "root:root", str(SHADOW))
        run("chmod", "-R", "go-w", str(SHADOW))
        for directory in (SHADOW, tree, tree / "runtime"):
            directory.chmod(0o755)
        SUDOERS.write_text(f"{ACCOUNT} ALL=(root) NOPASSWD: {SA2}\n")
        SUDOERS.chmod(0o440)
        assert run("visudo", "-cf", str(SUDOERS)).returncode == 0
        run("useradd", "-m", "-s", "/usr/sbin/nologin", ACCOUNT, check=True)
        run("useradd", "-m", "-s", "/usr/sbin/nologin", OTHER, check=True)
        account, other = pwd.getpwnam(ACCOUNT), pwd.getpwnam(OTHER)
        for name, entry in ((ACCOUNT, account), (OTHER, other)):
            run("loginctl", "enable-linger", name, check=True)
            assert wait_until(lambda entry=entry: Path(f"/run/user/{entry.pw_uid}/bus").exists(), 60), f"{name}'s user manager did not start"
        assert run("mount", "--bind", str(tree), str(REAL_ROOT)).returncode == 0
        mounts.append(REAL_ROOT)
        assert os.lstat(REAL_ROOT).st_uid == 0
        yield account
    finally:
        if account is not None:
            tool("remove")  # best effort: a clean state removes the unit; otherwise the explicit cleanup below does
            sctl("stop", UNIT)
            sctl("reset-failed", UNIT)
            for leftover in invocation_units(account):
                acct(account, "systemctl", "--user", "stop", leftover)
                acct(account, "systemctl", "--user", "reset-failed", leftover)
            if (SYSTEM_DIR / UNIT).exists() or (SYSTEM_DIR / "multi-user.target.wants" / UNIT).is_symlink():
                sctl("disable", UNIT)
                (SYSTEM_DIR / UNIT).unlink(missing_ok=True)
                sctl("daemon-reload")
        for name, entry in ((ACCOUNT, account), (OTHER, other)):
            if entry is not None:
                run("loginctl", "disable-linger", name)
                run("loginctl", "terminate-user", name)
                wait_until(lambda entry=entry: not Path(f"/run/user/{entry.pw_uid}").exists(), 60)
        os.chdir("/")
        stuck = []
        for target in reversed(mounts):
            gone = wait_until(lambda target=target: run("umount", str(target)).returncode == 0, 30)
            if not gone:
                print("\nBUSY", run("lsof", "-w", "+D", str(target)).stdout[:3000], run("umount", str(target)).stderr)
                stuck.append(target)
        for name, entry in ((ACCOUNT, account), (OTHER, other)):
            if entry is not None:
                run("userdel", "-r", name)
        SUDOERS.unlink(missing_ok=True)
        shutil.rmtree(DECOY, ignore_errors=True)
        if ARTIFACT.exists() and ARTIFACT.read_text() == STAND_IN_ARTIFACT:
            shutil.rmtree(LIBEXEC, ignore_errors=True)
        if not stuck:  # never delete a tree that is still mounted
            run("rm", "-rf", str(SHADOW))
        os.chdir(original_cwd)
        assert not stuck, f"could not unmount {stuck}"
        after = os.lstat(REAL_ROOT)
        assert not mounted(REAL_ROOT) and (after.st_uid, after.st_gid, after.st_mode) == (
            before_root.st_uid, before_root.st_gid, before_root.st_mode)
        for name in (ACCOUNT, OTHER):
            with pytest.raises(KeyError):
                pwd.getpwnam(name)
        assert not SUDOERS.exists() and not SHADOW.exists() and not DECOY.exists()
        assert residue() == before, {k: (before[k], v) for k, v in residue().items() if before[k] != v}
        tmp = os.lstat("/var/tmp")
        assert (tmp.st_uid, tmp.st_gid, stat.S_IMODE(tmp.st_mode)) == (before_tmp.st_uid, before_tmp.st_gid, stat.S_IMODE(before_tmp.st_mode))


def tool(action: str) -> subprocess.CompletedProcess:
    """The real installer, exactly as an operator runs it: root, an emptied environment, the repository as the working directory."""
    return subprocess.run(
        ["env", "-i", "PATH=/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE=1", PY314, "-m", "tools.executor_supervisor_install", action],
        capture_output=True, text=True, cwd=str(REAL_ROOT / "platform"), check=False)


def acct(account, *argv: str, user: str = ACCOUNT) -> subprocess.CompletedProcess:
    runtime = f"/run/user/{account.pw_uid}"
    return run("runuser", "-u", user, "--", "env", f"XDG_RUNTIME_DIR={runtime}", f"DBUS_SESSION_BUS_ADDRESS=unix:path={runtime}/bus", *argv)


def invocation_units(account) -> list[str]:
    out = acct(account, "systemctl", "--user", "--no-pager", "list-units", "--all", "--plain", "--no-legend", "freedom-executor-stop-*").stdout
    return [line.split()[0] for line in out.splitlines() if line.strip()]


def state_dir() -> Path:
    return STATE / "invocations"


def socket_path() -> str:
    return str(RUNTIME / "supervisor.sock")


def active() -> str:
    return sshow(UNIT, "ActiveState")["ActiveState"]


def start_service() -> None:
    sctl("reset-failed", UNIT)
    assert sctl("start", UNIT).returncode == 0, sctl("status", UNIT).stdout
    assert wait_until(lambda: tool("verify-ready").returncode == 0, 60), tool("verify-ready").stderr


def one_stop(account, **env) -> str:
    result = acct(account, "env", "-i", "PATH=/usr/bin:/bin", f"PYTHONPATH={REAL_ROOT}/platform", f"{REAL_ROOT}/runtime/venv-web/bin/python", "-B",
                  "-c", ONE_STOP, user=ACCOUNT)
    return result.stdout.strip() or result.stderr.strip()


def supervisors() -> list[tuple[int, int, list[str]]]:
    """Every persistent supervisor process on the host: (pid, real uid, argv)."""
    rows = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            argv = [part.decode() for part in (entry / "cmdline").read_bytes().split(b"\0") if part]
            uid = int(next(line for line in (entry / "status").read_text().splitlines() if line.startswith("Uid:")).split()[1])
        except (OSError, StopIteration, ValueError):
            continue
        if len(argv) == 5 and argv[1:] == ["-E", "-s", "-m", "adapters.executor.supervisor"]:
            rows.append((int(entry.name), uid, argv))
    return rows


def environ_of(pid: int) -> dict[str, str]:
    return dict(item.split("=", 1) for item in Path(f"/proc/{pid}/environ").read_bytes().decode().split("\0") if "=" in item)


@pytest.fixture
def installed(package):
    """The package installed (inactive) for one test; `remove` always leaves nothing behind."""
    assert tool("install").returncode == 0
    try:
        yield package
    finally:
        removed = tool("remove")
        if removed.returncode != 0:
            sctl("stop", UNIT)
            (state_dir() / "active.json").unlink(missing_ok=True)
            assert wait_until(lambda: tool("remove").returncode == 0, 60), tool("remove").stderr
        assert not (SYSTEM_DIR / UNIT).exists() and not (SYSTEM_DIR / "multi-user.target.wants" / UNIT).is_symlink()
        assert not (USER_UNIT_DIR / UNIT).exists() and not (USER_UNIT_DIR / "default.target.wants" / UNIT).is_symlink()
        assert wait_until(lambda: supervisors() == [], 30)
        # `remove` never deletes state; the (empty) directories systemd keeps are removed here so the disposable host is restored.
        assert listing(state_dir()) == []
        shutil.rmtree(STATE, ignore_errors=True)
        shutil.rmtree(RUNTIME, ignore_errors=True)


@pytest.fixture
def sa2_stand_in():
    """The SA-2 artifact path holds a stub whose ``stop`` takes ``hold`` seconds then succeeds (the vector itself is unchanged)."""
    assert not LIBEXEC.exists(), "an SA-2 artifact is already installed on this host"
    LIBEXEC.mkdir(mode=0o755)
    ARTIFACT.write_text(STAND_IN_ARTIFACT)
    (LIBEXEC / "hold").write_text("4")
    for path in (ARTIFACT, LIBEXEC / "hold"):
        os.chmod(path, 0o644)
    try:
        yield LIBEXEC / "hold"
    finally:
        shutil.rmtree(LIBEXEC, ignore_errors=True)


def journal_launches(since: float) -> list[float]:
    """Epoch times of the account's privileged launches, exactly the SA-2 vector, from the system journal."""
    out = run("journalctl", "--no-pager", "-o", "short-unix", f"--since=@{since - 1:.0f}", "_COMM=sudo").stdout
    return [float(line.split()[0]) for line in out.splitlines() if f"{ACCOUNT} :" in line and "COMMAND=" in line and SA2 in line]


def launches_for(rows, began: float) -> list[float]:
    """The journal's launches once it has caught up with the settled requests (journald lags), re-read after a pause for extras."""
    settled = len([row for row in rows if row[2] == "NOT_CONFIRMED"])
    wait_until(lambda: len(journal_launches(began)) >= settled, 20)
    time.sleep(1.5)
    return journal_launches(began)


# --- installation: exactly one root-owned system service, as the dedicated uid ---------------------------


def test_install_is_inactive_and_creates_exactly_one_root_owned_system_service_that_runs_as_the_dedicated_uid(installed):
    account = installed
    unit = SYSTEM_DIR / UNIT
    assert (unit.stat().st_uid, unit.stat().st_gid, stat.S_IMODE(unit.stat().st_mode)) == (0, 0, 0o644)
    assert unit.read_bytes() == (REPO / "infra/executor" / UNIT).read_bytes()
    assert os.readlink(SYSTEM_DIR / "multi-user.target.wants" / UNIT) == str(unit)
    assert run("systemctl", "is-enabled", UNIT).stdout.strip() == "enabled"
    found = run("find", "/etc/systemd", "/home", "/root", "/run/systemd", "/var/lib/systemd", "-name", f"{UNIT}*").stdout.split()
    assert sorted(found) == sorted([str(unit), str(SYSTEM_DIR / "multi-user.target.wants" / UNIT)])  # no global, per-user or user-manager link
    shown = sshow(UNIT, "User", "Group", "FragmentPath", "NeedDaemonReload", "LoadState", "ExecStart")
    assert (shown["User"], shown["Group"], shown["FragmentPath"], shown["NeedDaemonReload"], shown["LoadState"]) == (
        ACCOUNT, ACCOUNT, str(unit), "no", "loaded")
    assert " -E -s -m adapters.executor.supervisor" in shown["ExecStart"] and "path=/opt/freedom-blades/runtime/venv-web/bin/python" in shown["ExecStart"]
    assert active() == "inactive"  # install enables and never starts
    assert tool("verify").stdout.strip() == "executor-supervisor installed"
    not_ready = tool("verify-ready")
    assert not_ready.returncode == 12 and not_ready.stderr.strip() == "executor-supervisor supervisor-not-ready"

    start_service()
    assert tool("verify-ready").stdout.strip() == "executor-supervisor ready"
    assert active() == "active" and listing(state_dir()) == []
    (pid, uid, argv), = supervisors()  # exactly one persistent supervisor on the host
    assert uid == account.pw_uid and int(sshow(UNIT, "MainPID")["MainPID"]) == pid and argv[0] == f"{REAL_ROOT}/runtime/venv-web/bin/python"
    assert (STATE.stat().st_uid, stat.S_IMODE(STATE.stat().st_mode)) == (account.pw_uid, 0o700)
    assert (RUNTIME.stat().st_uid, stat.S_IMODE(RUNTIME.stat().st_mode)) == (account.pw_uid, 0o700)
    env = environ_of(pid)
    assert env["PATH"] == "/usr/bin:/bin" and not [k for k in env if k.startswith("PYTHON")]
    assert Path(f"/proc/{pid}/cgroup").read_text().strip().endswith(f"/system.slice/{UNIT}")  # the system manager's, not a user manager's
    assert acct(account, "systemctl", "--user", "show", UNIT, "-pLoadState", "--value").stdout.strip() == "not-found"  # the user manager has none

    # Exactly one privileged command, exactly the SA-2 vector, and nothing broader.
    listed = run("sudo", "-n", "-l", "-U", ACCOUNT).stdout
    commands = [line.strip() for line in listed.split("may run the following commands", 1)[1].splitlines()[1:] if line.strip()]
    assert commands == [f"(root) NOPASSWD: {SA2}"]
    assert acct(account, "sudo", "-n", "/bin/true").returncode != 0
    assert acct(account, "sudo", "-n", "/usr/bin/id").returncode != 0
    since = time.time()
    assert one_stop(account) == "NOT_CONFIRMED"  # the SA-2 artifact is not installed here: sudo ran the vector, python refused the file
    assert wait_until(lambda: len(journal_launches(since)) == 1, 15), journal_launches(since)  # journald lags the launch
    assert wait_until(lambda: listing(state_dir()) == [] and invocation_units(account) == [], 30)

    removed = tool("remove")
    assert removed.returncode == 0 and removed.stdout.strip() == "executor-supervisor removed", removed
    assert active() == "inactive" and not unit.exists() and not (SYSTEM_DIR / "multi-user.target.wants" / UNIT).is_symlink()
    assert sshow(UNIT, "LoadState", "NeedDaemonReload") == {"LoadState": "not-found", "NeedDaemonReload": "no"}  # the manager holds no stale unit
    assert tool("verify").returncode == 12  # not-installed
    assert Path(f"/var/lib/systemd/linger/{ACCOUNT}").exists()  # the account's linger, sudoers and the account itself are left alone
    assert SUDOERS.exists() and invocation_units(account) == [] and supervisors() == []


def test_the_transient_invocation_is_created_in_the_dedicated_user_manager_with_the_minimized_environment_and_fixed_vector(installed, sa2_stand_in):
    account = installed
    start_service()
    (supervisor,) = supervisors()
    client = subprocess.Popen(
        ["runuser", "-u", ACCOUNT, "--", "env", "-i", "PATH=/usr/bin:/bin", f"PYTHONPATH={REAL_ROOT}/platform",
         f"{REAL_ROOT}/runtime/venv-web/bin/python", "-B", "-c", ONE_STOP], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd="/")
    try:
        assert wait_until(lambda: len(invocation_units(account)) == 1, 20), invocation_units(account)
        (name,) = invocation_units(account)
        assert wait_until(lambda: any(a[:2] == ["sudo", "-n"] and a[-1] == "stop" for _, _, a in _sudo_processes(account)), 10)
        member = [row for row in _sudo_processes(account) if row[2][:2] == ["sudo", "-n"]][0]
        pid, argv = member[0], member[2]
        assert argv == ["sudo", "-n", PY314, "-I", "-S", str(ARTIFACT), "stop"]  # the unchanged fixed vector
        # This is the expected snapshot, and a useful regression check.  It is not the authorization boundary:
        # manager-environment enumeration and StartTransientUnit cannot be one atomic operation.
        assert environ_of(pid) == {"PATH": "/usr/bin:/bin"}
        cgroup = Path(f"/proc/{pid}/cgroup").read_text().strip()
        assert f"/user@{account.pw_uid}.service/" in cgroup and cgroup.endswith(f"/{name}")  # the dedicated uid's user manager owns it
        assert sshow(name, "LoadState")["LoadState"] == "not-found"  # and the system manager knows nothing of it
        assert supervisors() == [supervisor] and f"/{UNIT}" in Path(f"/proc/{supervisor[0]}/cgroup").read_text()  # the persistent owner is elsewhere
        assert (state_dir() / "active.json").exists()  # durable ownership before and during the launch
        out, err = client.communicate(timeout=60)
    finally:
        if client.poll() is None:
            client.kill()
    assert out.strip() == "STOPPED", (out, err)
    assert wait_until(lambda: listing(state_dir()) == [] and invocation_units(account) == [], 30)


def _sudo_processes(account) -> list[tuple[int, int, list[str]]]:
    rows = []
    for entry in Path("/proc").iterdir():
        if entry.name.isdigit():
            try:
                argv = [part.decode() for part in (entry / "cmdline").read_bytes().split(b"\0") if part]
                if argv[:1] == ["sudo"] and os.stat(entry).st_uid in (0, account.pw_uid):
                    rows.append((int(entry.name), account.pw_uid, argv))
            except (OSError, IndexError):
                pass
    return rows


# --- Python isolation, shadowing, other users -----------------------------------------------------------


def hostile_decoys(account) -> tuple[Path, dict[str, str]]:
    """Decoys on every channel an account or a manager environment could use; each records that it ran in a world-writable marker."""
    mark = DECOY / "ran"
    path, base = DECOY / "pythonpath", DECOY / "userbase"
    code = f"open({str(mark)!r}, 'a').write(__name__ + chr(10))\n"
    (path / "jeepney").mkdir(parents=True)
    for target in (path / "jeepney" / "__init__.py", path / "sitecustomize.py"):
        target.write_text(code)
    version = run(PY314, "-c", "import sys; print('%d.%d' % sys.version_info[:2])").stdout.strip()
    for site_dir in (base / f"lib/python{version}/site-packages", Path(account.pw_dir) / f".local/lib/python{version}/site-packages"):
        site_dir.mkdir(parents=True, exist_ok=True)
        (site_dir / "usercustomize.py").write_text(code)
    mark.write_text("")
    for item in [DECOY, *DECOY.rglob("*")]:
        os.chmod(item, 0o755 if item.is_dir() else 0o644)
    os.chmod(mark, 0o666)
    run("chown", "-R", f"{account.pw_uid}:{account.pw_gid}", str(Path(account.pw_dir) / ".local"))
    return mark, {"PYTHONPATH": str(path), "PYTHONUSERBASE": str(base), "PYTHONHOME": "/nonexistent-python-home",
                  "PYTHONSTARTUP": str(path / "sitecustomize.py"), "PYTHONINSPECT": "1", "PYTHONWARNINGS": "error", "PYTHONOPTIMIZE": "2"}


def test_hostile_python_manager_and_account_settings_cannot_redirect_the_real_service_imports(installed):
    account = installed
    mark, hostile = hostile_decoys(account)
    try:
        # Controls: without the unit's flags, the very same decoys really do take over an account-run interpreter.
        env = [f"{key}={value}" for key, value in hostile.items() if key not in ("PYTHONHOME", "PYTHONINSPECT")]
        interpreter = f"{REAL_ROOT}/runtime/venv-web/bin/python"
        for flags, expect in (([], True), (["-s"], True), (["-E"], False), (["-E", "-s"], False)):  # a venv has no user site of its own
            mark.write_text("")
            done = acct(account, "env", *env, interpreter, "-B", *flags, "-c", "import sys; sys.exit(0)", user=ACCOUNT)
            assert done.returncode == 0, done
            assert bool(mark.read_text()) is expect, (flags, mark.read_text())  # PYTHONPATH wins unless `-E`
        for flags, expect in (([], True), (["-E"], True), (["-E", "-s"], False)):  # the system interpreter does load the account's user site
            mark.write_text("")
            assert acct(account, PY314, "-B", *flags, "-c", "pass", user=ACCOUNT).returncode == 0
            assert bool(mark.read_text()) is expect, ("user site", flags)
        assert acct(account, "env", f"PYTHONHOME={hostile['PYTHONHOME']}", interpreter, "-c", "pass", user=ACCOUNT).returncode != 0
        assert acct(account, "env", f"PYTHONHOME={hostile['PYTHONHOME']}", interpreter, "-E", "-s", "-c", "pass", user=ACCOUNT).returncode == 0
        mark.write_text("")

        # The system manager itself carries the hostile variables, so every service it starts inherits them.
        assert sctl("set-environment", *(f"{key}={value}" for key, value in hostile.items())).returncode == 0
        try:
            start_service()
            (pid, uid, argv), = supervisors()
            assert uid == account.pw_uid and environ_of(pid)["PYTHONPATH"] == hostile["PYTHONPATH"]  # the hostile settings reached the process...
            assert mark.read_text() == ""  # ...and no decoy ran: sitecustomize, usercustomize and the planted jeepney stayed unimported
            assert sctl("restart", UNIT).returncode == 0
            assert wait_until(lambda: tool("verify-ready").returncode == 0, 60)
            assert one_stop(account) in ("NOT_CONFIRMED", "STOPPED") and mark.read_text() == ""  # the service really imported jeepney and ran
        finally:
            sctl("unset-environment", *hostile)
        assert not [line for line in run("systemctl", "show-environment").stdout.splitlines() if line.startswith("PYTHON")]
    finally:
        shutil.rmtree(Path(account.pw_dir) / ".local", ignore_errors=True)
        shutil.rmtree(DECOY, ignore_errors=True)


def test_a_malicious_same_named_unit_in_the_accounts_own_configuration_cannot_affect_the_persistent_supervisor(installed):
    account = installed
    start_service()
    flag = Path(account.pw_dir) / "attacker-ran"
    keys = ("MainPID", "NRestarts", "FragmentPath", "ExecStart", "ActiveEnterTimestampMonotonic", "DropInPaths", "InvocationID")
    before = sshow(UNIT, *keys)
    bytes_before = (SYSTEM_DIR / UNIT).read_bytes()
    (supervisor,) = supervisors()
    mine = Path(account.pw_dir) / ".config/systemd/user"
    (mine / "default.target.wants").mkdir(parents=True)
    (mine / UNIT).write_text(f"[Service]\nExecStart=/bin/sh -c 'touch {flag}; exec /bin/sleep 3600'\nRestart=always\n[Install]\nWantedBy=default.target\n")
    (mine / f"{UNIT}.d").mkdir()
    (mine / f"{UNIT}.d/override.conf").write_text(f"[Service]\nExecStart=\nExecStart=/bin/sh -c 'touch {flag}; exec /bin/sleep 3601'\n")
    run("chown", "-R", f"{account.pw_uid}:{account.pw_gid}", str(Path(account.pw_dir) / ".config"))
    try:
        outputs = []
        for command in (("daemon-reload",), ("enable", "--now", UNIT)):
            done = acct(account, "systemctl", "--user", *command)
            outputs.append((command, done.returncode, done.stdout, done.stderr))
        assert wait_until(flag.exists, 20), outputs
        for command in (("restart", UNIT), ("kill", UNIT), ("start", UNIT)):
            acct(account, "systemctl", "--user", *command)  # the account really does run its own unit of that name in its own manager...
        own = acct(account, "systemctl", "--user", "show", UNIT, "-pMainPID", "-pFragmentPath").stdout
        assert str(mine / UNIT) in own
        # ...and it changes nothing about the persistent system supervisor: fragment, command, PID, restarts, readiness.
        assert sshow(UNIT, *keys) == before and (SYSTEM_DIR / UNIT).read_bytes() == bytes_before and supervisors() == [supervisor]
        # The account cannot control the system unit through the system manager either (no polkit rule grants it).
        for command in (("stop",), ("restart",), ("disable",), ("kill",), ("mask",), ("daemon-reload",)):
            args = (UNIT,) if command != ("daemon-reload",) else ()
            denied = run("runuser", "-u", ACCOUNT, "--", "systemctl", "--no-ask-password", *command, *args)
            assert denied.returncode != 0, command
        assert sshow(UNIT, *keys) == before and supervisors() == [supervisor] and tool("verify-ready").returncode == 0
        # A restart of the account's whole user manager restarts its own unit again and still leaves the system one alone.
        assert sctl("restart", f"user@{account.pw_uid}.service").returncode == 0
        assert wait_until(lambda: Path(f"/run/user/{account.pw_uid}/bus").exists(), 60)
        assert wait_until(lambda: tool("verify-ready").returncode == 0, 60)
        after = sshow(UNIT, "MainPID", "FragmentPath", "ExecStart")
        assert (after["MainPID"], after["FragmentPath"], after["ExecStart"]) == (before["MainPID"], before["FragmentPath"], before["ExecStart"])
        # The supervisor's bus connection died with the old user manager: a request is refused (NOT_SENT, fail closed) until it
        # reconnects, then admitted through the same single owner.
        results = []
        assert wait_until(lambda: results.append(one_stop(account)) or results[-1] != "NOT_SENT", 30), results
        assert results[-1] in ("NOT_CONFIRMED", "STOPPED") and set(results[:-1]) <= {"NOT_SENT"} and supervisors() == [supervisor]
    finally:
        acct(account, "systemctl", "--user", "disable", "--now", UNIT)
        acct(account, "systemctl", "--user", "reset-failed")
        shutil.rmtree(Path(account.pw_dir) / ".config", ignore_errors=True)
        flag.unlink(missing_ok=True)


def test_another_active_lingering_users_manager_never_starts_or_receives_the_supervisor(installed, package):
    other = pwd.getpwnam(OTHER)
    start_service()
    for phase in ("after-start", "after-manager-restart"):
        if phase == "after-manager-restart":
            assert sctl("restart", f"user@{other.pw_uid}.service").returncode == 0
            assert wait_until(lambda: Path(f"/run/user/{other.pw_uid}/bus").exists(), 60)
            time.sleep(2)  # a global default.target.wants link would have started it by now
        assert acct(other, "systemctl", "--user", "show", UNIT, "-pLoadState", "--value", user=OTHER).stdout.strip() == "not-found", phase
        assert acct(other, "systemctl", "--user", "list-units", "--all", "--plain", "--no-legend", "freedom-blades-executor*", user=OTHER).stdout.strip() == ""
        assert not (Path(f"/run/user/{other.pw_uid}") / "freedom-blades-executor").exists(), phase
        assert not (Path(other.pw_dir) / ".local/state/freedom-blades-executor").exists(), phase
        assert [row for row in supervisors() if row[1] == other.pw_uid] == [] and len(supervisors()) == 1
    ubuntu = pwd.getpwnam("ubuntu")
    assert not (Path(ubuntu.pw_dir) / ".local/state/freedom-blades-executor").exists()  # the earlier global enablement's residue
    assert not any(p.is_symlink() for p in Path("/etc/systemd/user").rglob(UNIT))


# --- upgrade, reload and its injected failures ----------------------------------------------------------


class FailNthReload:
    """The real installer driving the real system manager, except that chosen ``daemon-reload`` calls report failure."""

    def __init__(self, failing: set[int]) -> None:
        self.failing, self.count, self.log = failing, 0, []

    def __call__(self, argv):
        if list(argv) == ["systemctl", "daemon-reload"]:
            self.count += 1
            self.log.append(("reload", self.count))
            if self.count in self.failing:
                return 1, ""  # the manager is never asked: the call "failed"
        else:
            self.log.append(tuple(argv))
        return tool_module._run(argv)


def real_installer(run_hook) -> Installer:
    return Installer(REAL_ROOT / "platform", run=run_hook)


def test_an_upgrade_loads_the_new_fragment_after_a_checked_reload_a_failed_reload_never_reports_success_and_the_restart_uses_it(installed):
    account = installed
    new = (SYSTEM_DIR / UNIT).read_bytes()
    old = new.replace(b"Environment=PATH=/usr/bin:/bin\n", b"Environment=PATH=/usr/bin:/bin\nEnvironment=FB_FRAGMENT=old\n")
    assert old != new and tool_module.MARKER in old.splitlines(keepends=True)
    (SYSTEM_DIR / UNIT).write_bytes(old)
    assert sctl("daemon-reload").returncode == 0
    start_service_old = sctl("start", UNIT)
    assert start_service_old.returncode == 0 and wait_until(lambda: active() == "active", 30)
    (pid, _, _), = supervisors()
    assert environ_of(pid).get("FB_FRAGMENT") == "old" and "FB_FRAGMENT=old" in sshow(UNIT, "Environment")["Environment"]

    # An injected reload failure: the installer fails, reports a stable word, restores the working fragment, and the manager stays coherent.
    hook = FailNthReload({1})
    with pytest.raises(tool_module.Failure) as caught:
        real_installer(hook).install()
    assert caught.value.word == "reload-failed" and caught.value.code == 13
    assert (SYSTEM_DIR / UNIT).read_bytes() == old and (SYSTEM_DIR / UNIT).stat().st_uid == 0
    assert sshow(UNIT, "NeedDaemonReload")["NeedDaemonReload"] == "no" and "FB_FRAGMENT=old" in sshow(UNIT, "Environment")["Environment"]
    assert supervisors()[0][0] == pid and active() == "active"  # the running owner was never disturbed

    # The real upgrade: checked reload, the new fragment is the loaded configuration, the running process is untouched until restarted.
    done = tool("install")
    assert done.returncode == 0 and done.stdout.strip() == "executor-supervisor installed", done
    assert (SYSTEM_DIR / UNIT).read_bytes() == new
    shown = sshow(UNIT, "NeedDaemonReload", "Environment")
    assert shown["NeedDaemonReload"] == "no" and "FB_FRAGMENT" not in shown["Environment"]
    assert supervisors()[0][0] == pid and environ_of(pid).get("FB_FRAGMENT") == "old"
    assert sctl("restart", UNIT).returncode == 0
    assert wait_until(lambda: tool("verify-ready").returncode == 0, 60)
    (new_pid, _, _), = supervisors()
    assert new_pid != pid and "FB_FRAGMENT" not in environ_of(new_pid)  # the restarted supervisor runs from the new fragment


class RaiseOnFirstReload(FailNthReload):
    """The real installer driving the real system manager, except that the first ``daemon-reload`` times out instead of returning."""

    def __call__(self, argv):
        if list(argv) == ["systemctl", "daemon-reload"] and not self.count:
            self.count += 1
            self.log.append(("reload", "timeout"))
            raise subprocess.TimeoutExpired(argv, 60)
        return super().__call__(argv)


@pytest.mark.parametrize("hook", [lambda: FailNthReload({1}), lambda: RaiseOnFirstReload(set())], ids=["exit-code", "timeout"])
def test_a_failed_upgrade_of_a_disabled_running_unit_leaves_it_disabled_and_loaded_as_before(installed, hook):
    account = installed
    new = (SYSTEM_DIR / UNIT).read_bytes()
    old = new.replace(b"Environment=PATH=/usr/bin:/bin\n", b"Environment=PATH=/usr/bin:/bin\nEnvironment=FB_FRAGMENT=old\n")
    assert old != new and tool_module.MARKER in old.splitlines(keepends=True)
    (SYSTEM_DIR / UNIT).write_bytes(old)
    assert sctl("daemon-reload").returncode == 0 and sctl("disable", UNIT).returncode == 0
    assert sctl("start", UNIT).returncode == 0 and wait_until(lambda: active() == "active", 30)
    (pid, _, _), = supervisors()
    assert sshow(UNIT, "UnitFileState")["UnitFileState"] == "disabled"

    with pytest.raises((tool_module.Failure, subprocess.TimeoutExpired)) as caught:
        real_installer(hook()).install()
    assert isinstance(caught.value, subprocess.TimeoutExpired) or (caught.value.word, caught.value.code) == ("reload-failed", 13)
    assert (SYSTEM_DIR / UNIT).read_bytes() == old and (SYSTEM_DIR / UNIT).stat().st_uid == 0
    assert not (SYSTEM_DIR / "multi-user.target.wants" / UNIT).exists() and sshow(UNIT, "UnitFileState")["UnitFileState"] == "disabled"
    shown = sshow(UNIT, "NeedDaemonReload", "Environment", "DropInPaths")
    assert shown["NeedDaemonReload"] == "no" and "FB_FRAGMENT=old" in shown["Environment"] and shown["DropInPaths"] == ""
    assert supervisors()[0][0] == pid and active() == "active"  # the running owner was never disturbed
    done = tool("install")  # a later safe retry
    assert done.returncode == 0 and (SYSTEM_DIR / UNIT).read_bytes() == new
    assert (SYSTEM_DIR / "multi-user.target.wants" / UNIT).is_symlink()


def test_removal_refuses_a_running_supervisor_whose_fragment_is_gone_and_install_then_remove_converges(installed):
    account = installed
    start_service()
    original = (SYSTEM_DIR / UNIT).read_bytes()
    (pid, _, _), = supervisors()
    (SYSTEM_DIR / "multi-user.target.wants" / UNIT).unlink()
    (SYSTEM_DIR / UNIT).unlink()  # the manager still holds and runs its loaded copy: it would not survive a reboot
    assert active() == "active"
    refused = tool("remove")
    assert refused.returncode == 11 and refused.stderr.strip() == "executor-supervisor owner-without-fragment", refused
    assert active() == "active" and supervisors()[0][0] == pid  # not drained, stopped or restarted
    converged = tool("install")  # writes the fragment, enables it, reloads; the running supervisor is left alone
    assert converged.returncode == 0 and (SYSTEM_DIR / UNIT).read_bytes() == original
    assert (SYSTEM_DIR / "multi-user.target.wants" / UNIT).is_symlink() and supervisors()[0][0] == pid
    assert tool("remove").returncode == 0 and sshow(UNIT, "LoadState")["LoadState"] == "not-found"


def test_a_failed_reload_during_removal_restores_the_fragment_and_a_running_owner_and_a_second_removal_completes(installed):
    account = installed
    start_service()
    original = (SYSTEM_DIR / UNIT).read_bytes()
    (old_pid, _, _), = supervisors()
    hook = FailNthReload({1})  # the reload that should drop the unit after the unlink
    with pytest.raises(tool_module.Failure) as caught:
        real_installer(hook).remove()
    assert caught.value.word == "reload-failed" and caught.value.code == 13
    assert (SYSTEM_DIR / UNIT).read_bytes() == original and (SYSTEM_DIR / "multi-user.target.wants" / UNIT).is_symlink()
    assert wait_until(lambda: tool("verify-ready").returncode == 0, 60)  # a persistent owner is running again: no ownership gap
    (new_pid, uid, _), = supervisors()
    assert uid == account.pw_uid and sshow(UNIT, "NeedDaemonReload", "LoadState") == {"NeedDaemonReload": "no", "LoadState": "loaded"}
    assert tool("remove").returncode == 0 and sshow(UNIT, "LoadState")["LoadState"] == "not-found"


# --- removal under the drain, and its races ---------------------------------------------------------------


def test_removal_is_refused_under_a_pending_record_keeps_the_service_running_and_succeeds_once_it_is_gone(installed):
    account = installed
    start_service()
    record = Record.fresh(boot_id()).to(START_SENT)  # an ambiguous same-boot launch: the call may be queued, so it blocks until reboot
    path = state_dir() / "active.json"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.write(fd, record.encode())
    os.fchown(fd, account.pw_uid, account.pw_gid)
    os.close(fd)
    refused = tool("remove")
    assert refused.returncode == 14 and refused.stderr.strip() == "executor-supervisor invocation-pending", refused
    assert (SYSTEM_DIR / UNIT).exists() and (SYSTEM_DIR / "multi-user.target.wants" / UNIT).is_symlink()
    assert wait_until(lambda: active() == "active" and tool("verify-ready").returncode == 0, 60)  # a drained owner was restarted
    assert path.exists()  # the record is untouched
    assert one_stop(account) == "BLOCKED"  # the restarted owner still blocks on the record (and admits nothing)
    path.unlink()  # test hygiene: the operator's ambiguous state ends only by reboot in production
    assert wait_until(lambda: tool("remove").returncode == 0, 60)


def test_a_supervisor_restart_with_a_live_contained_member_keeps_the_record_the_block_and_recovers(installed, sa2_stand_in):
    account = installed
    sa2_stand_in.write_text("12")
    start_service()
    client = subprocess.Popen(
        ["runuser", "-u", ACCOUNT, "--", "env", "-i", "PATH=/usr/bin:/bin", f"PYTHONPATH={REAL_ROOT}/platform",
         f"{REAL_ROOT}/runtime/venv-web/bin/python", "-B", "-c", ONE_STOP], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd="/")
    try:
        assert wait_until(lambda: len(invocation_units(account)) == 1 and (state_dir() / "active.json").exists(), 20)
        (name,) = invocation_units(account)
        (old_pid, _, _), = supervisors()
        assert sctl("kill", "--kill-whom=all", "--signal=SIGKILL", UNIT).returncode == 0  # the owner dies with the member still running
        client.communicate(timeout=60)
        assert invocation_units(account) == [name]  # the user manager kept the populated unit
        assert (state_dir() / "active.json").exists()  # and the durable record
        assert wait_until(lambda: active() == "active" and supervisors() and supervisors()[0][0] != old_pid, 30)
        assert one_stop(account) == "BLOCKED"  # the new owner blocks while the member lives
        assert wait_until(lambda: listing(state_dir()) == [] and invocation_units(account) == [], 60)  # and finally settles and clears it
        sa2_stand_in.write_text("1")
        assert one_stop(account) == "STOPPED"  # admission is open again
    finally:
        if client.poll() is None:
            client.kill()
    assert wait_until(lambda: listing(state_dir()) == [] and invocation_units(account) == [], 30)


def spam(account, seconds: float, workers: int = 4, pause: float = 0.3) -> list[subprocess.Popen]:
    return [
        subprocess.Popen(["runuser", "-u", ACCOUNT, "--", "env", "-i", "PATH=/usr/bin:/bin", f"PYTHONPATH={REAL_ROOT}/platform",
                          f"{REAL_ROOT}/runtime/venv-web/bin/python", "-B", "-c", SPAM, str(seconds), str(pause)],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd="/")
        for _ in range(workers)
    ]


def collect(procs) -> list[tuple[float, float, str]]:
    rows = []
    for proc in procs:
        out, err = proc.communicate(timeout=120)
        assert proc.returncode == 0, err
        rows += [(float(a), float(b), c) for a, b, c in (line.split() for line in out.splitlines())]
    return sorted(rows)


def test_a_request_racing_the_drain_is_admitted_under_the_owner_or_refused_before_launch_never_after_the_acknowledgment(installed):
    account = installed
    start_service()
    began = time.time()
    procs = spam(account, 16.0)
    time.sleep(5.0)
    acknowledged = None
    attempts = 0
    assert wait_until(lambda: (state_dir() / "active.json").exists(), 10)  # an invocation is in flight as the drain arrives
    while acknowledged is None and time.time() - began < 14:
        attempts += 1
        session = DrainSession(socket_path(), account.pw_uid, seconds=30)
        if session.request():
            acknowledged = time.time()
            held = session
            break
        session.close()  # pending: an invocation was admitted when the drain arrived
        time.sleep(0.05)
    assert acknowledged is not None, "the supervisor never reported empty"
    rows = collect(procs)
    held.close()
    launches = launches_for(rows, began)
    before = [row for row in rows if row[0] < acknowledged]
    after = [row for row in rows if row[0] > acknowledged]
    admitted = [row for row in rows if row[2] not in ("NOT_SENT", "BLOCKED")]
    print(f"\nRACE attempts={attempts} requests={len(rows)} admitted={len(admitted)} launches={len(launches)} "
          f"before_ack={len(before)} after_ack={len(after)} results={sorted({r[2] for r in rows})}")
    assert len(launches) >= 1 and len(after) >= 5  # the drain landed amid real traffic, on both sides
    assert not [moment for moment in launches if moment > acknowledged]  # nothing was launched after the acknowledgment
    assert all(row[2] == "NOT_SENT" for row in after)  # every later request was refused before any record or launch
    assert {row[2] for row in rows} <= {"NOT_SENT", "BLOCKED", "NOT_CONFIRMED"}  # a settled result or a pre-launch refusal; never an unowned one
    assert len(launches) == len([row for row in rows if row[2] == "NOT_CONFIRMED"])  # every launch belongs to a settled, owned request
    assert wait_until(lambda: listing(state_dir()) == [] and invocation_units(account) == [], 30)
    assert tool("remove").returncode == 0  # a drained, empty owner is removable


def test_removal_under_load_is_refused_while_an_invocation_is_admitted_and_completes_only_after_emptiness(installed):
    account = installed
    start_service()
    began = time.time()
    procs = spam(account, 40.0, workers=3, pause=3.0)  # real idle gaps between requests, so an empty moment exists
    time.sleep(1.5)
    refusals = 0
    finished = None
    while time.time() - began < 36:
        result = tool("remove")
        if result.returncode == 0:
            finished = time.time()
            break
        assert result.returncode == 14 and result.stderr.strip() in (
            "executor-supervisor invocation-pending", "executor-supervisor drain-unconfirmed"), result  # refused, not claimed
        refusals += 1
        assert (SYSTEM_DIR / UNIT).exists() and (SYSTEM_DIR / "multi-user.target.wants" / UNIT).is_symlink()  # still configured
        time.sleep(0.3)
    assert finished is not None, f"never removed after {refusals} refusals"
    rows = collect(procs)
    launches = launches_for(rows, began)
    print(f"\nREMOVAL refusals={refusals} requests={len(rows)} launches={len(launches)} results={sorted({r[2] for r in rows})}")
    assert listing(state_dir()) == [] and invocation_units(account) == []
    assert not [moment for moment in launches if moment > finished]  # nothing launched once the owner was gone
    # HANDED_OFF: a refusal restarted the owner under a client mid-request; the record persisted and the new owner settled it.
    assert {row[2] for row in rows} <= {"NOT_SENT", "BLOCKED", "NOT_CONFIRMED", "HANDED_OFF"}
    settled = len([row for row in rows if row[2] == "NOT_CONFIRMED"])
    assert settled <= len(launches) <= settled + len([row for row in rows if row[2] == "HANDED_OFF"])  # no launch without an owned request
    assert not (SYSTEM_DIR / UNIT).exists() and active() == "inactive"
    assert not (SYSTEM_DIR / "multi-user.target.wants" / UNIT).is_symlink() and not (USER_UNIT_DIR / "default.target.wants" / UNIT).is_symlink()


# --- bounded trust enumeration ----------------------------------------------------------------------------


def test_an_oversized_directory_in_the_trusted_tree_refuses_at_the_bound_without_unbounded_enumeration_or_memory(package):
    big = REAL_ROOT / "platform/adapters/zz_oversize"
    big.mkdir(mode=0o755)
    try:
        for index in range(250_000):
            os.close(os.open(big / f"entry-{index:06d}", os.O_WRONLY | os.O_CREAT, 0o644))
        draws = {"count": 0}
        real_scandir = os.scandir

        class Counting:
            def __init__(self, inner):
                self.inner = inner

            def __enter__(self):
                self.inner.__enter__()
                return self

            def __exit__(self, *exc):
                return self.inner.__exit__(*exc)

            def __iter__(self):
                return self

            def __next__(self):
                entry = next(self.inner)
                draws["count"] += 1
                return entry

        def scandir(source=".", *a, **k):
            inner = real_scandir(source, *a, **k)
            try:
                target = os.readlink(f"/proc/self/fd/{source}") if isinstance(source, int) else str(source)
            except OSError:
                target = ""
            return Counting(inner) if target.endswith("zz_oversize") else inner

        os.scandir = scandir
        tracemalloc.start()
        try:
            with pytest.raises(tool_module.Failure) as caught:
                Installer(REAL_ROOT / "platform").install()
        finally:
            os.scandir = real_scandir
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
        assert caught.value.word == "code-too-large" and caught.value.code == 10
        assert draws["count"] <= tool_module.MAX_WALK + 1, draws  # the iterator was never drawn past the budget (and one overflow entry)
        assert peak < 8 * 1024 * 1024, peak  # 250,000 names retained would be several times this
        refused = tool("install")  # and the real command line refuses with its stable word, writing nothing
        assert refused.returncode == 10 and refused.stderr.strip() == "executor-supervisor code-too-large", refused
        assert not (SYSTEM_DIR / UNIT).exists() and not (SYSTEM_DIR / "multi-user.target.wants" / UNIT).exists()
        print(f"\nOVERSIZE draws={draws['count']} (bound {tool_module.MAX_WALK}) tracemalloc_peak={peak}")
    finally:
        shutil.rmtree(big, ignore_errors=True)
    assert not big.exists()
