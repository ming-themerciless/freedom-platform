"""Executor OS-6 persistent ownership on the disposable host (third remediation).

The real ``ubuntu`` user manager, a repository-owned supervisor *system service* running as ``ubuntu`` (the production code path
with a stand-in member vector and compressed timings), a separate transient invocation service per
admitted stop, the real ``ubuntu -> sudo -n`` boundary and a **root** member held in genuine
uninterruptible sleep (``dd`` with ``O_DIRECT`` on a ``dm-delay`` device). The accepted SA-2 vector itself
is exercised in ``test_executor_interrupt_host.py`` against the production unit text. Synthetic data only.

    sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test \\
        /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs -s \\
        tests/systemd_integration/test_executor_supervisor_host.py

Lingering is enabled for the run if it was off (so the user manager survives session loss) and restored.
"""

from __future__ import annotations

import json
import os
import secrets
import shutil
import signal
import stat
import subprocess
import time
from datetime import datetime
from pathlib import Path

import pytest

import test_route3_hold_host as hold_host  # noqa: F401  (applies the same disposable-host guards)
from test_route3_hold_host import run, wait_until

from executor_host_support import (
    GID,
    PYTHON,
    REPO,
    UID,
    Linger,
    as_user,
    invocation_cgroups,
    invocation_units,
    read_log,
    standin_service,
    user_manager_state,
    sctl,
    usctl,
    ushow,
)

DEVICE = f"fbsup{secrets.token_hex(3)}"
LOG = Path(f"/var/tmp/{DEVICE}-observe.log")
PRE_EXISTING = sorted(str(p) for p in Path("/var/tmp").glob("p5-r5-rp11-h0*"))
MEMBER = ["sudo", "-n", "/usr/bin/dd", f"if=/dev/mapper/{DEVICE}", "of=/dev/null", "bs=4096", "count=1", "iflag=direct"]
TIMING = {"wait": 3.0, "term_grace": 1.0, "descendants": 1.0, "kill_reap": 2.0, "kill_rounds": 2, "bind": 10.0,
          "clear": 5.0, "start_resolve": 3.0, "poll": 0.1, "recovery_interval": 1.0}
CLIENT = (
    "import sys\n"
    "from adapters.executor.interrupt import SudoStopInvoker\n"
    "print(SudoStopInvoker(socket_path=sys.argv[1], deadline_seconds=float(sys.argv[2])).invoke_stop().name, flush=True)\n"
)


@pytest.fixture(scope="module", autouse=True)
def linger():
    before_tmp = os.lstat("/var/tmp")
    with Linger() as state:
        yield state
    after = os.lstat("/var/tmp")
    assert (after.st_uid, after.st_gid, stat.S_IMODE(after.st_mode)) == (0, 0, 0o1777) == (
        before_tmp.st_uid, before_tmp.st_gid, stat.S_IMODE(before_tmp.st_mode))
    assert sorted(str(p) for p in Path("/var/tmp").glob("p5-r5-rp11-h0*")) == PRE_EXISTING
    assert run("systemctl", "is-active", "polkit.service").stdout.strip() == "active"


def dd_pids() -> list[str]:
    found = []
    for entry in Path("/proc").iterdir():
        if entry.name.isdigit():
            try:
                if (entry / "comm").read_text().strip() == "dd" and f"/dev/mapper/{DEVICE}".encode() in (entry / "cmdline").read_bytes():
                    found.append(entry.name)
            except OSError:
                continue
    return found


def in_d_state() -> bool:
    pids = dd_pids()
    try:
        return bool(pids) and all("State:\tD" in Path(f"/proc/{pid}/status").read_text() for pid in pids)
    except OSError:
        return False


def launches(since: str) -> int:
    out = run("journalctl", "--no-pager", "-o", "cat", "--since", since, "_COMM=sudo").stdout
    return sum(1 for line in out.splitlines() if "COMMAND=" in line and f"if=/dev/mapper/{DEVICE}" in line)


def stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def client(service, deadline: float = 60.0) -> subprocess.Popen:
    """An executor: the production ``SudoStopInvoker`` as ``ubuntu`` with an emptied environment."""
    return subprocess.Popen(
        ["runuser", "-u", "ubuntu", "--", "env", "-i", "PATH=/usr/bin:/bin", f"PYTHONPATH={REPO}", PYTHON, "-B", "-c", CLIENT,
         service.socket, str(deadline)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd="/")


def outcome(proc: subprocess.Popen, timeout: float = 90.0) -> str:
    out, err = proc.communicate(timeout=timeout)
    assert proc.returncode == 0, err
    return out.strip()


def state_files(service) -> list[str]:
    try:
        return sorted(os.listdir(service.state / "invocations"))
    except OSError:
        return ["<unreadable>"]


def bystander(prefix: str) -> str:
    name = f"{prefix}-{secrets.token_hex(3)}.service"
    assert as_user("systemd-run", "--user", "--quiet", f"--unit={name}", "/usr/bin/sleep", "600").returncode == 0
    return name


@pytest.fixture
def stuck_device():
    image = Path(f"/var/tmp/{DEVICE}.img")
    run("modprobe", "dm_delay")
    run("truncate", "-s", "64M", str(image), check=True)
    loop = run("losetup", "-f", "--show", str(image), check=True).stdout.strip()
    sectors = run("blockdev", "--getsz", loop, check=True).stdout.strip()
    released = []

    def release():
        if released:
            return
        released.append(1)
        run("dmsetup", "suspend", "--noudevsync", "--noflush", DEVICE)
        run("dmsetup", "load", DEVICE, "--table", f"0 {sectors} linear {loop} 0")
        run("dmsetup", "resume", "--noudevsync", DEVICE)

    try:
        run("dmsetup", "create", "--noudevsync", "--noudevrules", DEVICE, "--table", f"0 {sectors} delay {loop} 0 600000", check=True)
        run("dmsetup", "mknodes")
        yield release
    finally:
        release()
        wait_until(lambda: dd_pids() == [], 30)
        assert wait_until(lambda: run("dmsetup", "remove", "--noudevsync", "-f", DEVICE).returncode == 0, 30)
        run("losetup", "-d", loop)
        image.unlink(missing_ok=True)


@pytest.fixture
def supervisor(stuck_device):
    LOG.unlink(missing_ok=True)
    LOG.write_text("")
    shutil.chown(LOG, UID, GID)
    service = standin_service(argv=MEMBER, timing=TIMING, log=LOG)
    service.install()
    try:
        service.start()
        yield service
    finally:
        stuck_device()  # a held member could never be removed otherwise
        wait_until(lambda: dd_pids() == [], 30)
        run("chattr", "-i", str(service.state / "invocations"))
        wait_until(lambda: invocation_units() == [] and invocation_cgroups() == [], 30)  # the owner finishes its own cleanup
        service.remove()
        LOG.unlink(missing_ok=True)
        for leftover in [*invocation_units(), *bystanders()]:  # hygiene after a failed test only
            usctl("stop", leftover)
            usctl("reset-failed", leftover)
        assert wait_until(lambda: invocation_units() == [] and invocation_cgroups() == [] and dd_pids() == [], 30), (
            invocation_units(), invocation_cgroups(), dd_pids())
        assert not service.file.exists() and not service.state.exists()


def bystanders() -> list[str]:
    out = usctl("list-units", "--all", "--plain", "--no-legend", "fbexec-unrelated-*", "fbexec-bystander-*").stdout
    return [line.split()[0] for line in out.splitlines() if line.strip()]


def test_the_owner_survives_executor_death_and_its_own_restart_and_cleans_up_after_the_io_is_released(supervisor, stuck_device):
    other = bystander("fbexec-unrelated")
    unrelated_before = ushow(other, "ActiveState", "InvocationID", "MainPID", "ControlGroup")
    evidence: dict[str, dict] = {}

    def boundary(label: str, unit: str | None = None) -> None:
        evidence[label] = {
            "user_manager": user_manager_state(),
            "supervisor": supervisor.info(),
            "invocation": ushow(unit, "ActiveState", "SubState", "MainPID", "InvocationID", "ControlGroup") if unit else None,
            "state_files": state_files(supervisor),
            "dd": dd_pids(),
        }

    since = stamp()
    boundary("ready")
    assert evidence["ready"]["user_manager"]["ActiveState"] == "active" and evidence["ready"]["state_files"] == []

    first = client(supervisor)
    assert wait_until(lambda: any(e["label"] == "put:bound" for e in read_log(LOG)) and in_d_state(), 60), read_log(LOG)
    entries = read_log(LOG)
    labels = [e["label"] for e in entries]
    # Durable ownership precedes the member: prepared < start-sent < start call < bound.
    assert labels.index("put:prepared") < labels.index("put:start-sent") < labels.index("start-call:before") < labels.index("start-call:after")
    by = {e["label"]: e for e in entries}
    assert by["put:prepared"]["unit"] is None and len(by["put:prepared"]["state_dir"]) == 1
    assert by["put:start-sent"]["unit"] is None  # the record is durable while no unit can exist yet
    assert by["start-call:before"]["unit"] is None and by["start-call:before"]["state_dir"]
    assert by["start-call:after"]["unit"] is not None
    assert by["put:bound"]["unit"]["invocation_id"] and by["put:bound"]["unit"]["control_group"]
    (unit,) = invocation_units()
    boundary("manager-bound", unit)
    assert evidence["manager-bound"]["invocation"]["ActiveState"] in ("active", "deactivating")
    assert launches(since) == 1 and len(dd_pids()) == 1

    first.send_signal(signal.SIGKILL)  # the executor dies while the member remains
    first.wait()
    assert in_d_state() and invocation_units() == [unit]
    assert wait_until(lambda: any(e["label"] == "put:cleanup" for e in read_log(LOG)), 30)
    boundary("executor-killed", unit)
    assert evidence["executor-killed"]["state_files"] and in_d_state()

    assert outcome(client(supervisor)) == "BLOCKED"  # a second executor is refused; nothing more is launched
    assert launches(since) == 1 and len(dd_pids()) == 1

    # The supervisor dies abruptly and systemd restarts it. The user manager keeps the populated invocation unit.
    old = supervisor.info()
    old_cgroup = ushow(unit, "ControlGroup")["ControlGroup"]
    assert old_cgroup and old_cgroup != old["ControlGroup"] and not old_cgroup.startswith(old["ControlGroup"] + "/")
    boundary("before-supervisor-death", unit)
    assert sctl("kill", "--kill-whom=all", "--signal=SIGKILL", supervisor.name).returncode == 0
    end = time.monotonic() + 40
    while True:
        assert invocation_units() == [unit] and in_d_state() and len(dd_pids()) == 1  # continuously retained, never relaunched
        assert state_files(supervisor)  # the block is never dropped
        info = supervisor.info()
        if info["MainPID"] not in ("0", old["MainPID"]) and supervisor.ready():
            break
        assert time.monotonic() < end, "the supervisor did not come back"
        time.sleep(0.1)
    new = supervisor.info()
    assert new["MainPID"] != old["MainPID"] and int(new["NRestarts"]) == int(old["NRestarts"]) + 1
    boundary("supervisor-restarted", unit)
    assert evidence["supervisor-restarted"]["invocation"]["ControlGroup"] == old_cgroup
    starts = [e for e in read_log(LOG) if e["label"] == "supervisor-start"]
    assert len(starts) == 2 and starts[0]["pid"] != starts[1]["pid"] and starts[1]["state_dir"]  # the replacement found the record
    assert outcome(client(supervisor)) == "BLOCKED"
    assert launches(since) == 1 and len(dd_pids()) == 1

    time.sleep(3)  # the restarted supervisor keeps recovering (cgroup.kill and observation only); the member stays
    assert in_d_state() and invocation_units() == [unit] and state_files(supervisor)

    stuck_device()  # the delayed I/O completes: the pending SIGKILL now takes effect
    assert wait_until(lambda: dd_pids() == [], 30)
    assert wait_until(lambda: state_files(supervisor) == [] and invocation_units() == [] and invocation_cgroups() == [], 60), (
        state_files(supervisor), invocation_units(), invocation_cgroups())  # no manual deletion of record, unit or cgroup
    boundary("terminal")
    assert evidence["terminal"]["state_files"] == [] and evidence["terminal"]["dd"] == []

    # Cleared only after the boundary was empty, so a stop is admitted again: a second launch. The released stand-in
    # exits 1 (direct I/O to the swapped table is invalid), an unexpected status, which keeps the typed mapping.
    assert outcome(client(supervisor)) == "NOT_CONFIRMED" and launches(since) == 2
    assert wait_until(lambda: state_files(supervisor) == [] and invocation_units() == [], 30)
    assert ushow(other, "ActiveState", "InvocationID", "MainPID", "ControlGroup") == unrelated_before
    usctl("stop", other)
    print("\nEVIDENCE " + json.dumps(evidence, sort_keys=True))
    print("OBSERVED " + json.dumps(
        [{"label": e["label"], "state_dir": e["state_dir"],
          "unit": f'{e["unit"]["active"]}/{e["unit"]["sub"]}' if isinstance(e.get("unit"), dict) else e.get("unit")}
         for e in read_log(LOG)], sort_keys=True))
