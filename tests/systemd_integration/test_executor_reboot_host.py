"""Executor OS-6 across a real kernel reboot: an ambiguous ``start-sent`` record clears on a *changed boot* and only then.

The record is left by a supervisor that died after committing ``start-sent`` (its deterministic unit absent). During the
same boot it must keep blocking (proved in ``test_executor_remediation4_host.py``); a reboot ends the old boot's queued
request and cgroup, so the next boot's supervisor, started by the *system* manager (enabled in ``multi-user.target``) with
no login, waits fail-closed for the lingering user manager's bus, clears the record and admits a new stop. A second lingering
user proves that no other user's manager ever starts or receives the supervisor. Three explicit phases, with the reboot
performed by the operator between them:

    export FREEDOM_SYSTEMD_INTEGRATION=oracle-test
    sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_EXECUTOR_REBOOT_PHASE=prepare \\
        /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs tests/systemd_integration/test_executor_reboot_host.py
    sudo systemctl reboot
    sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_EXECUTOR_REBOOT_PHASE=verify  ... (same module)
    sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_EXECUTOR_REBOOT_PHASE=cleanup ... (same module)

Without the variable every test here skips. ``cleanup`` restores lingering, removes the unit, state, second user and marker.
"""

from __future__ import annotations

import json
import os
import pwd
import subprocess
from pathlib import Path

import pytest

import test_route3_hold_host as hold_host  # noqa: F401  (applies the same disposable-host guards)
from test_route3_hold_host import run, wait_until

from adapters.executor.ownership import START_SENT, Record
from executor_host_support import (
    GID,
    PYTHON,
    REPO,
    UID,
    boot_id,
    invocation_cgroups,
    invocation_units,
    linger_state,
    plant_record,
    read_log,
    sctl,
    sshow,
    standin_service,
)

PHASE = os.environ.get("FREEDOM_EXECUTOR_REBOOT_PHASE", "")
OTHER = "fbexecother"  # a second lingering user: its manager must never start or receive the supervisor
MARKER = Path("/var/tmp/fbexec-reboot-marker.json")
LOG = Path("/var/tmp/fbexec-reboot-observe.log")
TIMING = {"wait": 10.0, "term_grace": 2.0, "descendants": 2.0, "kill_reap": 3.0, "kill_rounds": 2, "bind": 15.0,
          "clear": 8.0, "start_resolve": 2.0, "poll": 0.1, "recovery_interval": 1.0}
CLIENT = (
    "import sys\n"
    "from adapters.executor.interrupt import SudoStopInvoker\n"
    "print(SudoStopInvoker(socket_path=sys.argv[1], deadline_seconds=60).invoke_stop().name, flush=True)\n"
)

pytestmark = pytest.mark.skipif(not PHASE, reason="set FREEDOM_EXECUTOR_REBOOT_PHASE=prepare|verify|cleanup (the real-reboot proof is explicit)")


def service():
    """The same stand-in service object each phase (the unit name is fixed in the marker once prepared)."""
    name = json.loads(MARKER.read_text())["unit"] if MARKER.exists() else None
    made = standin_service(argv=["sudo", "-n", "/usr/bin/true"], timing=TIMING, log=LOG)
    if name:
        made.name, made.file = name, made.file.with_name(name)
        made.state_name = name.removesuffix(".service")
        made.state = made.state.with_name(made.state_name)
        made.runtime = made.runtime.with_name(made.state_name)
    return made


@pytest.mark.skipif(PHASE != "prepare", reason="phase")
def test_prepare_leaves_an_ambiguous_start_sent_record_with_an_enabled_supervisor():
    assert not MARKER.exists()
    initial = linger_state()
    if initial != "yes":
        run("loginctl", "enable-linger", "ubuntu", check=True)
    assert wait_until(lambda: Path(f"/run/user/{UID}/bus").exists(), 60)
    LOG.write_text("")
    os.chown(LOG, UID, GID)
    run("useradd", "-m", "-s", "/usr/sbin/nologin", OTHER, check=True)
    run("loginctl", "enable-linger", OTHER, check=True)
    assert wait_until(lambda: Path(f"/run/user/{pwd.getpwnam(OTHER).pw_uid}/bus").exists(), 60)
    svc = standin_service(argv=["sudo", "-n", "/usr/bin/true"], timing=TIMING, log=LOG)
    MARKER.write_text(json.dumps({"unit": svc.name, "initial_linger": initial, "boot": boot_id()}))
    svc.install()
    assert sctl("enable", svc.name).returncode == 0
    svc.start()
    sctl("stop", svc.name)
    assert wait_until(lambda: svc.info()["ActiveState"] == "inactive", 30)
    record = Record.fresh(boot_id()).to(START_SENT)  # committed, then the process died around the StartTransientUnit call
    plant_record(svc, record)
    assert sorted(os.listdir(svc.state / "invocations")) == ["active.json"] and invocation_units() == []
    print(f"\nPREPARED boot={boot_id()} unit={svc.name} nonce={record.nonce}")


@pytest.mark.skipif(PHASE != "verify", reason="phase")
def test_verify_after_the_reboot_the_old_boots_record_is_gone_and_a_stop_is_admitted():
    marker = json.loads(MARKER.read_text())
    assert boot_id() != marker["boot"], "no reboot happened between prepare and verify"
    svc = service()
    assert wait_until(svc.ready, 120), sctl("status", svc.name).stdout  # started by the system manager at boot, no login required
    other = pwd.getpwnam(OTHER)
    manager = sshow(f"user@{UID}.service", "ActiveState", "ActiveEnterTimestampMonotonic")
    started = sshow(svc.name, "ActiveEnterTimestampMonotonic", "NRestarts", "User")
    assert manager["ActiveState"] == "active"
    # Fail closed while the bus becomes ready: the unit can only have become active (READY=1 follows the manager check and the bind)
    # after the lingering user manager was up, and every earlier start attempt is on record as a refusal, not an admission.
    assert int(started["ActiveEnterTimestampMonotonic"]) > int(manager["ActiveEnterTimestampMonotonic"])
    journal = run("journalctl", "-b", "--no-pager", "-o", "cat", "-u", svc.name).stdout
    early = [line for line in journal.splitlines() if "not ready" in line]
    print(f"\nORDERING user_manager_active={manager['ActiveEnterTimestampMonotonic']} supervisor_active={started['ActiveEnterTimestampMonotonic']} "
          f"nrestarts={started['NRestarts']} not_ready_lines={len(early)}")
    # No other user's manager starts or receives the supervisor, and the one supervisor runs as the account.
    assert sshow(f"user@{other.pw_uid}.service", "ActiveState")["ActiveState"] == "active"
    other_runtime = f"/run/user/{other.pw_uid}"
    out = run("runuser", "-u", OTHER, "--", "env", f"XDG_RUNTIME_DIR={other_runtime}", f"DBUS_SESSION_BUS_ADDRESS=unix:path={other_runtime}/bus",
              "systemctl", "--user", "show", svc.name, "-pLoadState", "--value").stdout.strip()
    assert out == "not-found" and not Path(other_runtime, svc.state_name).exists() and not (Path(other.pw_dir) / ".local/state" / svc.state_name).exists()
    assert not list(Path("/etc/systemd/user").rglob(f"{svc.name}*")) and started["User"] == "ubuntu"
    assert [str(p) for p in Path("/home").iterdir() if (p / ".local/state" / svc.state_name).exists()] == []
    assert wait_until(lambda: not (svc.state / "invocations" / "active.json").exists(), 30)  # cleared by the changed boot id alone
    labels = [e["label"] for e in read_log(LOG)]
    assert "start-call:before" not in labels and "put:prepared" not in labels  # nothing was launched or rewritten to get there
    result = subprocess.run(
        ["runuser", "-u", "ubuntu", "--", "env", "-i", "PATH=/usr/bin:/bin", f"PYTHONPATH={REPO}", PYTHON, "-B", "-c", CLIENT, svc.socket],
        capture_output=True, text=True, cwd="/", check=False)
    print(f"\nCLIENT stdout={result.stdout!r} stderr={result.stderr!r} rc={result.returncode}")
    assert result.stdout.strip() in ("STOPPED", "NOT_CONFIRMED"), result  # admission is open again
    print(f"\nVERIFIED boot {marker['boot']} -> {boot_id()}; record cleared; stop admitted: {result.stdout.strip()}")


@pytest.mark.skipif(PHASE != "cleanup", reason="phase")
def test_cleanup_restores_the_host():
    marker = json.loads(MARKER.read_text())
    svc = service()
    sctl("disable", svc.name)
    svc.remove()
    run("loginctl", "disable-linger", OTHER)
    run("loginctl", "terminate-user", OTHER)
    run("userdel", "-r", OTHER)
    with pytest.raises(KeyError):
        pwd.getpwnam(OTHER)
    LOG.unlink(missing_ok=True)
    assert wait_until(lambda: invocation_units() == [] and invocation_cgroups() == [], 30)
    if marker["initial_linger"] != "yes":
        run("loginctl", "disable-linger", "ubuntu", check=True)
    assert linger_state() == marker["initial_linger"]
    MARKER.unlink()
    assert not svc.file.exists() and not svc.state.exists()
