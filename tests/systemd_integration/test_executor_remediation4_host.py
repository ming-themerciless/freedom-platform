"""Executor OS-6, fourth remediation, on the disposable host: ambiguous launch state, directory pressure, the exact member
environment and the maintenance drain, against the real ``ubuntu`` systemd 259 user manager.

The supervisor is the production code path (``adapters.executor.supervisor``) with a stand-in member vector and compressed
timings, run as a repository-owned system service running as ``ubuntu``; invocation units are real transient services created by the production
``StartTransientUnit`` adapter. Synthetic data only.

    sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test \\
        /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs -s \\
        tests/systemd_integration/test_executor_remediation4_host.py

Lingering is enabled for the run if it was off and restored.
"""

from __future__ import annotations

import os
import secrets
import stat
import subprocess
import time
from datetime import datetime
from pathlib import Path

import pytest

import test_route3_hold_host as hold_host  # noqa: F401  (applies the same disposable-host guards)
from test_route3_hold_host import run, wait_until

from adapters.executor.ownership import MAX_ENTRIES, START_SENT, Record
from executor_host_support import (
    GID,
    PYTHON,
    REPO,
    UID,
    Linger,
    boot_id,
    delayed_start,
    invocation_cgroups,
    invocation_units,
    plant_record,
    read_log,
    standin_service,
    sctl,
    usctl,
)
from tools.executor_supervisor_install import DrainSession, Failure

TOKEN = secrets.token_hex(3)
LOG = Path(f"/var/tmp/fbr4-{TOKEN}-observe.log")
ENV_FILE = Path(f"/var/tmp/fbr4-{TOKEN}-environ")
PROBE = Path(f"/var/tmp/fbr4-{TOKEN}-probe.py")
# `start_resolve` is the former elapsed-time clearance for an ambiguous start: every wait below is a multiple of it.
TIMING = {"wait": 30.0, "term_grace": 2.0, "descendants": 2.0, "kill_reap": 3.0, "kill_rounds": 2, "bind": 15.0,
          "clear": 8.0, "start_resolve": 2.0, "poll": 0.1, "recovery_interval": 1.0}
CLIENT = (
    "import sys\n"
    "from adapters.executor.interrupt import SudoStopInvoker\n"
    "print(SudoStopInvoker(socket_path=sys.argv[1], deadline_seconds=float(sys.argv[2])).invoke_stop().name, flush=True)\n"
)


@pytest.fixture(scope="module", autouse=True)
def linger():
    before = os.lstat("/var/tmp")
    with Linger() as state:
        yield state
    after = os.lstat("/var/tmp")
    assert (after.st_uid, after.st_gid, stat.S_IMODE(after.st_mode)) == (before.st_uid, before.st_gid, stat.S_IMODE(before.st_mode))
    assert run("systemctl", "is-active", "polkit.service").stdout.strip() == "active"


def stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def launches(since: str, marker: str) -> int:
    out = run("journalctl", "--no-pager", "-o", "cat", "--since", since, "_COMM=sudo").stdout
    return sum(1 for line in out.splitlines() if "COMMAND=" in line and marker in line)


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


def state_dir(service) -> Path:
    return service.state / "invocations"


def state_files(service) -> list[str]:
    try:
        return sorted(os.listdir(state_dir(service)))
    except OSError:
        return ["<unreadable>"]


def rss_kib(pid: str) -> int:
    for line in Path(f"/proc/{pid}/status").read_text().splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1])
    raise AssertionError("no VmRSS")


@pytest.fixture
def stand_in():
    """Build, start and always tear down a stand-in supervisor service."""
    made = []

    def make(argv, *, executable="/usr/bin/sudo", started=True):
        LOG.unlink(missing_ok=True)
        LOG.write_text("")
        os.chown(LOG, UID, GID)
        service = standin_service(argv=argv, timing=TIMING, log=LOG, executable=executable)
        service.install()
        made.append(service)
        if started:
            service.start()
        return service

    try:
        yield make
    finally:
        for service in made:
            service.remove()
        for leftover in invocation_units():
            usctl("stop", leftover)
            usctl("reset-failed", leftover)
        LOG.unlink(missing_ok=True)
        ENV_FILE.unlink(missing_ok=True)
        PROBE.unlink(missing_ok=True)
        assert wait_until(lambda: invocation_units() == [] and invocation_cgroups() == [], 30)


def stage_record(service, record) -> None:
    """With the supervisor stopped (so nothing races the plant), leave exactly ``record`` in its state directory."""
    sctl("stop", service.name)
    assert wait_until(lambda: service.info()["ActiveState"] == "inactive", 30)
    plant_record(service, record)


def test_an_ambiguous_same_boot_start_stays_blocking_beyond_the_former_deadline_and_a_delayed_unit_is_adopted_once(stand_in):
    marker = "2.111"
    service = stand_in(["sudo", "-n", "/usr/bin/sleep", marker], started=False)
    service.start()
    record = Record.fresh(boot_id()).to(START_SENT)  # the supervisor died after committing `start-sent`, before/while calling
    stage_record(service, record)
    since = stamp()
    service.start()
    began = time.monotonic()

    # Far beyond start_resolve (2 s) -- and several recovery passes -- with the deterministic unit absent on every read.
    while time.monotonic() - began < 3 * TIMING["start_resolve"] + 6:
        assert state_files(service) == ["active.json"], state_files(service)
        assert invocation_units() == []
        time.sleep(0.5)
    assert outcome(client(service)) == "BLOCKED"  # still owned: nothing is admitted
    assert [e["label"] for e in read_log(LOG) if e["label"].startswith(("start-call", "put:"))] == []  # no call, no rewrite

    # The queued request finally lands: the manager creates the deterministic unit. Nobody calls StartTransientUnit again.
    assert delayed_start(record.unit, "sudo", "-n", "/usr/bin/sleep", marker).returncode == 0
    assert wait_until(lambda: any(e["label"] == "put:bound" for e in read_log(LOG)), 30), read_log(LOG)
    assert wait_until(lambda: state_files(service) == [] and invocation_units() == [] and invocation_cgroups() == [], 60), (
        state_files(service), invocation_units(), invocation_cgroups())
    labels = [e["label"] for e in read_log(LOG)]
    assert "start-call:before" not in labels and labels.count("put:bound") == 1  # adopted and settled exactly once
    assert launches(since, f"/usr/bin/sleep {marker}") == 1  # one launch, by the delayed request alone


def test_directory_pressure_cannot_starve_the_real_record(stand_in):
    marker = "2.222"
    service = stand_in(["sudo", "-n", "/usr/bin/sleep", marker], started=False)
    service.start()
    sctl("stop", service.name)
    assert wait_until(lambda: service.info()["ActiveState"] == "inactive", 30)
    directory = state_dir(service)
    for index in range(3 * MAX_ENTRIES):  # created first, well past the entry limit
        fd = os.open(directory / f"a-junk-{index:05d}", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.fchown(fd, UID, GID)
        os.close(fd)
    record = Record.fresh(boot_id()).to(START_SENT)
    plant_record(service, record)
    since = stamp()
    service.start()
    pid = service.info()["MainPID"]
    assert outcome(client(service)) == "BLOCKED"  # the damage blocks admission
    assert delayed_start(record.unit, "sudo", "-n", "/usr/bin/sleep", marker).returncode == 0
    assert wait_until(lambda: not (directory / "active.json").exists() and invocation_units() == [], 60), (
        (directory / "active.json").exists(), invocation_units())  # the real record was found and driven to a clear boundary
    assert "put:bound" in [e["label"] for e in read_log(LOG)] and launches(since, f"/usr/bin/sleep {marker}") == 1
    assert len(os.listdir(directory)) == 3 * MAX_ENTRIES  # the junk is untouched, never opened, and still blocks
    assert outcome(client(service)) == "BLOCKED"
    assert service.info()["MainPID"] == pid and rss_kib(pid) < 150_000  # no restart, bounded memory (24 MiB junk names)


def test_the_transient_member_environment_is_observed_as_the_fixed_path(stand_in):
    PROBE.write_text(f"open({str(ENV_FILE)!r}, 'wb').write(open('/proc/self/environ', 'rb').read())\n")  # quotes stay out of the unit file
    PROBE.chmod(0o644)
    service = stand_in(["python3", "-I", "-S", str(PROBE)], executable="/usr/bin/python3")
    assert outcome(client(service)) == "STOPPED"
    raw = ENV_FILE.read_bytes()
    print(f"\nOBSERVED member environment: {raw!r}")
    # Observational regression, not an atomic guarantee across the separate manager query and creation calls.
    assert raw == b"PATH=/usr/bin:/bin\x00"
    names = [item.split(b"=", 1)[0] for item in raw.split(b"\x00") if item]
    assert names == [b"PATH"]
    for generated in (b"INVOCATION_ID", b"SYSTEMD_EXEC_PID", b"MANAGERPID", b"MEMORY_PRESSURE_WATCH", b"MEMORY_PRESSURE_WRITE", b"JOURNAL_STREAM"):
        assert generated not in raw
    assert wait_until(lambda: state_files(service) == [] and invocation_units() == [], 30)


def test_drain_closes_admission_refuses_under_a_pending_invocation_and_acknowledges_only_when_empty(stand_in):
    marker = "20.333"
    service = stand_in(["sudo", "-n", "/usr/bin/sleep", marker])
    since = stamp()
    pending = client(service)
    assert wait_until(lambda: state_files(service) == ["active.json"] and len(invocation_units()) == 1, 30)
    session = DrainSession(service.socket, UID, seconds=30)
    assert session.request() is False  # an invocation is admitted and owned: removal is refused
    assert session.alive()
    session.close()
    assert outcome(client(service)) == "NOT_SENT"  # drained for good: every later admission is refused before any record or launch
    assert launches(since, f"/usr/bin/sleep {marker}") == 1 and state_files(service) == ["active.json"]
    assert len(invocation_units()) == 1  # the owner and its invocation are untouched by the drain

    late = DrainSession(service.socket, UID, seconds=30)
    for _ in range(300):
        if late.request():
            break
        late.close()
        time.sleep(0.5)
        late = DrainSession(service.socket, UID, seconds=30)
    else:
        raise AssertionError("never drained")
    assert state_files(service) == [] and invocation_units() == [] and invocation_cgroups() == []  # affirmative emptiness
    assert outcome(pending, timeout=120) in ("NOT_CONFIRMED", "STOPPED")
    assert outcome(client(service)) == "NOT_SENT" and launches(since, f"/usr/bin/sleep {marker}") == 1
    late.close()


def test_a_supervisor_lost_during_drain_is_visible_to_the_maintainer_as_a_dropped_connection(stand_in):
    service = stand_in(["sudo", "-n", "/usr/bin/sleep", "2.444"])
    session = DrainSession(service.socket, UID, seconds=30)
    assert session.request() is True and session.alive()
    old = service.info()["MainPID"]
    assert sctl("kill", "--kill-whom=all", "--signal=SIGKILL", service.name).returncode == 0
    assert wait_until(lambda: not session.alive(), 20)  # EOF: the drain state died with the process
    assert wait_until(lambda: service.ready() and service.info()["MainPID"] not in ("0", old), 40)
    # The replacement is a different, undrained process: exactly why a drain acknowledgment is only valid while held.
    assert outcome(client(service)) in ("STOPPED", "NOT_CONFIRMED")
    session.close()


def test_a_drain_from_the_executor_uid_or_a_stop_from_a_stranger_is_not_served(stand_in):
    service = stand_in(["sudo", "-n", "/usr/bin/sleep", "2.555"])
    script = (
        "import socket, sys\n"
        "from adapters.executor.protocol import DRAIN_REQUEST, GREETING\n"
        "c = socket.socket(socket.AF_UNIX); c.settimeout(10); c.connect(sys.argv[1])\n"
        "assert c.recv(len(GREETING)) == GREETING\n"
        "c.sendall(DRAIN_REQUEST)\n"
        "print(repr(c.recv(64)), flush=True)\n"
    )
    out = subprocess.run(["runuser", "-u", "ubuntu", "--", "env", "-i", f"PYTHONPATH={REPO}", PYTHON, "-B", "-c", script, service.socket],
                         capture_output=True, text=True, cwd="/", check=False)
    assert out.returncode == 0 and out.stdout.strip() == "b''", (out.stdout, out.stderr)  # the executor itself cannot drain
    assert outcome(client(service)) in ("STOPPED", "NOT_CONFIRMED")  # and nothing was drained: it can still stop
    with pytest.raises(Failure):
        DrainSession(service.socket, UID + 1, seconds=5)  # an installer expecting another owner refuses the peer
