"""Disposable-host support for the executor proofs: the ``ubuntu`` user manager and the supervisor *system* services.

The persistent supervisor is a root-controlled system service running as the account (``User=ubuntu`` here, the
dedicated ``freedom-executor`` in production); the account's lingering user manager owns only the transient invocation
units. Everything is reversible and torn down by the fixtures: lingering is enabled only if it was off and is
restored; unit files and state directories are created only if absent and removed afterwards.
"""

from __future__ import annotations

import json
import os
import pwd
import re
import secrets
import shutil
import stat
import subprocess
import time
from pathlib import Path

from test_route3_hold_host import run, wait_until

REPO = Path(__file__).resolve().parents[2]
PYTHON = "/opt/freedom-blades/runtime/venv-web/bin/python"
ACCOUNT = pwd.getpwnam("ubuntu")
UID, GID = ACCOUNT.pw_uid, ACCOUNT.pw_gid
RUNTIME = Path(f"/run/user/{UID}")
UNIT_DIR = Path("/etc/systemd/system")
STATE_ROOT = Path("/var/lib")
RUNTIME_ROOT = Path("/run")
REAL_UNIT = "freedom-blades-executor-supervisor.service"
REAL_FILE = REPO / "infra/executor" / REAL_UNIT


def as_user(*argv: str, check: bool = False) -> subprocess.CompletedProcess:
    env = [f"XDG_RUNTIME_DIR={RUNTIME}", f"DBUS_SESSION_BUS_ADDRESS=unix:path={RUNTIME}/bus"]
    return run("runuser", "-u", "ubuntu", "--", "env", *env, *argv, check=check)


def usctl(*args: str, check: bool = False) -> subprocess.CompletedProcess:
    return as_user("systemctl", "--user", "--no-pager", *args, check=check)


def ushow(unit: str, *props: str) -> dict[str, str]:
    out = usctl("show", unit, *(f"-p{p}" for p in props)).stdout
    return dict(line.split("=", 1) for line in out.splitlines() if "=" in line)


def user_manager_state() -> dict[str, str]:
    """PID 1's view of the user manager unit, plus the manager's own view of itself."""
    own = usctl("show", "--property=SystemState").stdout.strip()
    return {**show_system(f"user@{UID}.service", "ActiveState", "MainPID"), "SystemState": own.split("=", 1)[-1]}


def sctl(*args: str, check: bool = False) -> subprocess.CompletedProcess:
    """The system manager: the only thing that controls the persistent supervisor."""
    return run("systemctl", "--no-pager", *args, check=check)


def sshow(unit: str, *props: str) -> dict[str, str]:
    out = sctl("show", unit, *(f"-p{p}" for p in props)).stdout
    return dict(line.split("=", 1) for line in out.splitlines() if "=" in line)


def show_system(unit: str, *props: str) -> dict[str, str]:
    out = run("systemctl", "show", unit, *(f"-p{p}" for p in props)).stdout
    return dict(line.split("=", 1) for line in out.splitlines() if "=" in line)


def linger_state() -> str:
    out = run("loginctl", "show-user", "ubuntu", "-p", "Linger").stdout
    return out.strip().split("=", 1)[1] if "=" in out else "unknown"


class Linger:
    """Enable lingering for the proof (so the user manager survives login/session loss); restore on exit."""

    def __init__(self) -> None:
        self.initial = linger_state()

    def __enter__(self) -> Linger:
        if self.initial != "yes":
            run("loginctl", "enable-linger", "ubuntu", check=True)
        assert wait_until(lambda: (RUNTIME / "bus").exists(), 30), "the user manager did not start"
        assert wait_until(lambda: usctl("is-system-running").stdout.strip() in ("running", "degraded"), 30)
        return self

    def __exit__(self, *exc) -> None:
        if self.initial != "yes":
            run("loginctl", "disable-linger", "ubuntu")
        assert linger_state() == self.initial


class Service:
    """A system service (running as ``ubuntu``) installed for the test, started, observed and removed again."""

    def __init__(self, name: str, text: str, state_name: str) -> None:
        self.name, self.text, self.state_name = name, text, state_name
        self.file = UNIT_DIR / name
        self.state = STATE_ROOT / state_name
        self.runtime = RUNTIME_ROOT / state_name

    @property
    def socket(self) -> str:
        return str(self.runtime / "supervisor.sock")

    def install(self) -> None:
        assert not self.file.exists() and not self.state.exists() and not self.runtime.exists()
        self.file.write_text(self.text)
        os.chmod(self.file, 0o644)
        sctl("daemon-reload", check=True)

    def start(self) -> None:
        sctl("reset-failed", self.name)
        assert sctl("start", self.name).returncode == 0, sctl("status", self.name).stdout
        assert wait_until(self.ready, 30), sctl("status", self.name).stdout
        assert self.ready()

    def ready(self) -> bool:
        """``Type=notify``: the unit is ``active`` only after the supervisor sent READY=1, which follows the bind."""
        if sshow(self.name, "ActiveState")["ActiveState"] != "active":
            return False
        try:
            return stat.S_ISSOCK(os.lstat(self.socket).st_mode)
        except OSError:
            return False

    def info(self) -> dict[str, str]:
        return sshow(self.name, "ActiveState", "SubState", "MainPID", "NRestarts", "ControlGroup", "Result")

    def remove(self) -> None:
        sctl("stop", self.name)
        sctl("reset-failed", self.name)
        self.file.unlink(missing_ok=True)
        sctl("daemon-reload")
        shutil.rmtree(self.state, ignore_errors=True)
        shutil.rmtree(self.runtime, ignore_errors=True)
        assert not self.file.exists()


def _system_unit_text(state_name: str) -> str:
    """The production fragment with only the account substituted (``ubuntu`` for the dedicated account) on the disposable host."""
    text = REAL_FILE.read_text()
    assert "User=freedom-executor" in text and "Group=freedom-executor" in text
    return text.replace("User=freedom-executor", "User=ubuntu").replace("Group=freedom-executor", "Group=ubuntu")


def real_service() -> Service:
    return Service(REAL_UNIT, _system_unit_text("freedom-blades-executor"), "freedom-blades-executor")


def standin_service(*, argv: list[str], timing: dict, log: Path, executable: str = "/usr/bin/sudo") -> Service:
    token = secrets.token_hex(3)
    name = f"fbexec-standin-{token}.service"
    state_name = f"fbexec-standin-{token}"
    text = _system_unit_text(state_name)
    text = re.sub(r"^ExecStart=.*$", f"ExecStart={PYTHON} -E -s {REPO}/tests/systemd_integration/executor_standin_supervisor.py", text, flags=re.M)
    text = text.replace("StateDirectory=freedom-blades-executor", f"StateDirectory={state_name}")
    text = text.replace("RuntimeDirectory=freedom-blades-executor", f"RuntimeDirectory={state_name}")
    spec = json.dumps({"argv": argv, "executable": executable, "timing": timing})
    text = text.replace("[Service]\n", f"[Service]\nEnvironment=FB_STANDIN_REPO={REPO}\nEnvironment=FB_STANDIN_LOG={log}\n"
                        f"Environment='FB_STANDIN_SPEC={spec}'\n", 1)
    return Service(name, text, state_name)


def invocation_units() -> list[str]:
    out = usctl("list-units", "--all", "--plain", "--no-legend", "freedom-executor-stop-*").stdout
    return [line.split()[0] for line in out.splitlines() if line.strip()]


def invocation_cgroups() -> list[Path]:
    return [p for p in Path("/sys/fs/cgroup").rglob("freedom-executor-stop-*") if p.is_dir()]


def read_log(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


DELAYED_START = (
    "import os, sys\n"
    "from adapters.executor.usermanager import BusUserManager\n"
    "from adapters.executor.userbus import connect_user_bus\n"
    "BusUserManager(lambda: connect_user_bus(os.getuid())).start_transient(\n"
    "    sys.argv[1], tuple(sys.argv[2:]), executable='/usr/bin/sudo', environment=('PATH=/usr/bin:/bin',))\n"
)


def delayed_start(unit: str, *argv: str) -> subprocess.CompletedProcess:
    """A queued ``StartTransientUnit`` finally landing: the production adapter creates the deterministic unit, as ``ubuntu``."""
    return as_user(f"PYTHONPATH={REPO}", PYTHON, "-B", "-c", DELAYED_START, unit, *argv)


def boot_id() -> str:
    return Path("/proc/sys/kernel/random/boot_id").read_text().strip()


def plant_record(service: Service, record) -> None:
    """Write an ownership record into a *stopped* supervisor's state directory, as the service account would have left it."""
    path = service.state / "invocations" / "active.json"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(fd, record.encode())
        os.fchown(fd, UID, GID)
    finally:
        os.close(fd)
