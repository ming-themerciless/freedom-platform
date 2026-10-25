"""Executor OS-6 interruption on the disposable host: ``ubuntu`` -> supervisor -> ``sudo -n`` -> SA-2 ``stop``.

The entry runs as the real unprivileged ``ubuntu`` operator from the repository
(``python -m adapters.executor.interrupt <id>``), observes the real capture unit over the
system bus, reads a synthetic canonical consume journal under ``/var/tmp`` and, only under
OC-1/OC-2/OC-3, asks the **repository-owned supervisor system service** (the unit text with only
the account substituted, installed for the run; lingering enabled and restored) to run the accepted artifact's ``stop`` role through the
exact ``sudo -n`` vector as a transient service of the account's user manager. The artifact is built fresh
from the hash-pinned wheel by the shared fixture. Synthetic data only; the capture unit is a
transient ``sleep``. Slow/stuck-member, restart and failure-injection proofs are in
``test_executor_supervisor_host.py``.

    sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test \\
        FREEDOM_RP11_WHEEL=/path/to/jeepney-0.9.0-py3-none-any.whl \\
        /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs \\
        tests/systemd_integration/test_executor_interrupt_host.py
"""

from __future__ import annotations

import hashlib
import os
import secrets
import shutil
import stat
import subprocess
import textwrap
from datetime import UTC, datetime
from pathlib import Path

import pytest

import test_route3_hold_host as hold_host  # noqa: F401  (applies the same disposable-host guards)
from test_route3_hold_host import (  # noqa: F401
    CAPTURE_UNIT_FILE,
    artifact,
    rp11_processes,
    run,
    show,
    wait_until,
)

from executor_host_support import Linger, invocation_cgroups, invocation_units, real_service, sctl, usctl  # noqa: E402

from application.rp11.journal import GENESIS, JournalKind, consume_run, serialize_line

UNIT = "rp11-capture-pass-a.service"
REPO = Path(__file__).resolve().parents[2]
PYTHON = "/opt/freedom-blades/runtime/venv-web/bin/python"
#: The executor as the unprivileged operator: a transient system service as ``ubuntu``. It holds no
#: privileged process; the supervisor (a separate system service) owns every invocation.
OPERATOR = ["systemd-run", "--quiet", "--pipe", "--wait", "--collect", "--uid=ubuntu", "--gid=ubuntu",
            f"--working-directory={REPO}"]
H64 = "c" * 64
PRE_EXISTING = sorted(str(p) for p in Path("/var/tmp").glob("p5-r5-rp11-h0*"))
ACTIVE_BODY = "Type=exec\nExecStart=/usr/bin/sleep 600\n"
START_PRE_BODY = "Type=exec\nExecStartPre=/usr/bin/sleep 600\nExecStart=/usr/bin/sleep 600\nTimeoutStartSec=900\n"


@pytest.fixture(scope="module", autouse=True)
def real_supervisor():
    """The production unit text (only the account substituted), installed for ``ubuntu`` on this disposable host for the run only."""
    with Linger():
        service = real_service()
        service.install()
        try:
            service.start()
            yield service
        finally:
            service.remove()
            assert wait_until(lambda: invocation_units() == [] and invocation_cgroups() == [], 30)


@pytest.fixture(scope="module", autouse=True)
def _host_state_unchanged():
    before_tmp = os.lstat("/var/tmp")
    yield
    after = os.lstat("/var/tmp")
    assert (after.st_uid, after.st_gid, stat.S_IMODE(after.st_mode)) == (0, 0, 0o1777) == (
        before_tmp.st_uid, before_tmp.st_gid, stat.S_IMODE(before_tmp.st_mode))
    assert sorted(str(p) for p in Path("/var/tmp").glob("p5-r5-rp11-h0*")) == PRE_EXISTING
    assert run("systemctl", "is-active", "polkit.service").stdout.strip() == "active"
    assert not CAPTURE_UNIT_FILE.exists() and not Path("/var/lib/freedom-blades-rp11").exists()


class Pass:
    """One synthetic activation id, the capture unit and the consume evidence for it."""

    def __init__(self) -> None:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        self.id = f"rp11-act-{stamp}-{secrets.token_hex(4)}"
        self.evidence = Path(f"/var/tmp/{self.id}-consume-evidence")
        self.journal = self.evidence / "journal"

    def unit(self, body: str) -> None:
        CAPTURE_UNIT_FILE.write_text(
            f"[Unit]\nDescription=RP-11 synthetic capture pass (executor host test)\n\n[Service]\n{body}"
        )
        run("systemctl", "daemon-reload", check=True)
        run("systemctl", "reset-failed", UNIT)

    def start_active(self) -> dict[str, str]:
        self.unit(ACTIVE_BODY)
        run("systemctl", "start", UNIT, check=True)
        state = show(UNIT, "ActiveState", "InvocationID", "MainPID", "Job")
        assert state["ActiveState"] == "active" and len(state["InvocationID"]) == 32
        return state

    def start_pre(self) -> dict[str, str]:
        self.unit(START_PRE_BODY)
        run("systemctl", "start", "--no-block", UNIT, check=True)
        assert wait_until(lambda: show(UNIT, "ActiveState")["ActiveState"] == "activating", 20)
        state = show(UNIT, "ActiveState", "SubState", "InvocationID", "MainPID", "Job")
        assert state["SubState"] == "start-pre" and len(state["InvocationID"]) == 32
        return state

    def write_journal(self, invocation: str, *, consumed: bool = True, run_end: bool = True,
                      torn: bool = False, late: bool = False) -> bytes:
        """The complete success trace ``ConsumeProcedure`` emits (CQ-2, CQ-3, CQ-5, CQ-6, CQ-7).

        ``late`` writes the canonical but production-impossible ``run-start, consumed, child, run-end``.
        """
        entries = [("run-start", {
            "invocation_id": invocation, "boot_id": "11111111-2222-3333-4444-555555555555",
            "claim": {"dev": 1, "ino": 2}, "act_journal": {"sha256": H64, "length": 10},
            "lock": {"object": {"path": "/run/k", "dev": 1, "ino": 3}, "mode": "held", "wait_ms": 0},
            "helper": {"role": "consume", "tool_sha256": H64}})]
        consumed_line = ("consumed", {"pk_status": "not-authorized", "inactive_enter_us": 5})
        if late:
            entries += [consumed_line, ("child", {"entry": {"a": 1}})]
        else:
            entries += [
                ("remove-intent", {"path": "/run/r", "dev": 1, "ino": 4, "sha256": H64}),
                ("removed", {"path": "/run/r"}),
                ("child", {"entry": {"n": 1}}),
                ("grant-check", {"verb": "start", "mode": "seek-not-authorized", "outcome": "not-authorized",
                                 "reason": "not-authorized", "calls": 1}),
            ]
            if consumed:
                entries.append(consumed_line)
        if run_end:
            entries.append(("run-end", {"outcome": "consumed"}))
        data, prev = b"", GENESIS
        for seq, (op, fields) in enumerate(entries, start=1):
            line = serialize_line(JournalKind.CONSUME, seq=seq, prev=prev, run=consume_run(self.id), op=op, fields=fields)
            data, prev = data + line, hashlib.sha256(line).hexdigest()
        if torn:
            data = data[:-7]
        self.evidence.mkdir(mode=0o700)
        self.journal.write_bytes(data)
        os.chmod(self.journal, 0o644)
        os.chmod(self.evidence, 0o755)
        return data

    def interrupt(self, *argv: str) -> subprocess.CompletedProcess:
        """The executor entry, as the unprivileged operator, with an emptied environment."""
        return subprocess.run(
            [*OPERATOR, "env", "-i", "PATH=/usr/bin:/bin", PYTHON, "-B", "-m",
             "adapters.executor.interrupt", *(argv or (self.id,))],
            capture_output=True, text=True, cwd=REPO,
        )


@pytest.fixture
def make_pass():
    assert not CAPTURE_UNIT_FILE.exists()
    made: list[Pass] = []
    extra_units: list[str] = []

    def make() -> Pass:
        made.append(Pass())
        return made[-1]

    make.extra_units = extra_units
    yield make
    for unit in extra_units:
        run("systemctl", "kill", "--signal=SIGKILL", unit)
        run("systemctl", "stop", unit)
        run("systemctl", "reset-failed", unit)
    run("systemctl", "kill", "--signal=SIGKILL", UNIT)
    run("systemctl", "stop", UNIT)
    CAPTURE_UNIT_FILE.unlink(missing_ok=True)
    run("systemctl", "daemon-reload", check=True)
    run("systemctl", "reset-failed", UNIT)
    for one in made:
        shutil.rmtree(one.evidence, ignore_errors=True)
        assert not list(Path("/var/tmp").glob(f"{one.id}-*"))
    assert wait_until(lambda: rp11_processes() == [], 10), rp11_processes()


def sudo_stop_lines(since: str) -> list[str]:
    """``sudo`` journal entries for the exact SA-2 vector since ``since``."""
    out = run("journalctl", "--no-pager", "-o", "cat", "--since", since, "_COMM=sudo").stdout
    return [line for line in out.splitlines() if "rp11_h1.py stop" in line and "COMMAND=" in line]


def stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def tail(proc) -> str:
    return proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else ""


def test_active_unit_with_a_matching_consumed_journal_is_stopped_through_the_exact_sudo_vector(make_pass):
    one = make_pass()
    state = one.start_active()
    one.write_journal(state["InvocationID"])
    since = stamp()
    proc = one.interrupt()
    assert proc.returncode == 0, proc.stderr  # the production-shaped history crosses ubuntu -> sudo -n
    assert proc.stderr == "rp11-interrupt interrupted\n"
    assert show(UNIT, "ActiveState")["ActiveState"] == "inactive"
    lines = sudo_stop_lines(since)
    assert len(lines) == 1 and "COMMAND=/usr/bin/python3.14 -I -S /usr/local/libexec/freedom-blades-rp11/rp11_h1.py stop" in lines[0]
    assert "USER=root" in lines[0]
    assert one.journal.read_bytes() and rp11_processes() == []


def test_a_real_start_pre_unit_is_not_stopped_and_no_privileged_child_is_launched(make_pass):
    one = make_pass()
    state = one.start_pre()
    one.write_journal(state["InvocationID"])  # even a perfect journal cannot override OC-1
    before_journal = one.journal.read_bytes()
    since = stamp()
    proc = one.interrupt()
    assert proc.returncode == 30 and proc.stderr == "rp11-interrupt unavailable not-active\n"
    assert show(UNIT, "ActiveState", "SubState", "InvocationID", "MainPID", "Job") == state
    assert sudo_stop_lines(since) == [] and run("journalctl", "--no-pager", "-o", "cat", "--since", since, "_COMM=sudo").stdout == ""
    assert one.journal.read_bytes() == before_journal


def test_active_with_a_mismatched_invocation_id_is_not_stopped(make_pass):
    one = make_pass()
    state = one.start_active()
    other = "0" * 32 if state["InvocationID"] != "0" * 32 else "1" * 32
    data = one.write_journal(other)
    since = stamp()
    proc = one.interrupt()
    assert proc.returncode == 30 and proc.stderr == "rp11-interrupt unavailable invocation-mismatch\n"
    assert show(UNIT, "ActiveState", "InvocationID", "MainPID") == {k: state[k] for k in ("ActiveState", "InvocationID", "MainPID")}
    assert sudo_stop_lines(since) == [] and one.journal.read_bytes() == data


@pytest.mark.parametrize(
    "variant,reason",
    [("missing", "journal-unavailable"), ("torn", "journal-torn"), ("no-consumed", "not-consumed"),
     ("no-run-end", "journal-incomplete"), ("late-operation", "journal-history")],
)
def test_active_with_a_missing_torn_or_incomplete_journal_is_not_stopped_and_evidence_is_unchanged(make_pass, variant, reason):
    one = make_pass()
    state = one.start_active()
    data = None
    if variant == "torn":
        data = one.write_journal(state["InvocationID"], torn=False)
        torn = data + b'{"seq":4,"op":"ch'
        one.journal.write_bytes(torn)
        data = torn
    elif variant == "no-consumed":
        data = one.write_journal(state["InvocationID"], consumed=False)
    elif variant == "no-run-end":
        data = one.write_journal(state["InvocationID"], run_end=False)
    elif variant == "late-operation":
        data = one.write_journal(state["InvocationID"], late=True)
    since = stamp()
    proc = one.interrupt()
    assert proc.returncode == 30 and tail(proc) == f"rp11-interrupt unavailable {reason}", proc.stderr
    assert show(UNIT, "ActiveState", "InvocationID", "MainPID") == {k: state[k] for k in ("ActiveState", "InvocationID", "MainPID")}
    assert sudo_stop_lines(since) == []
    if data is None:
        assert not one.evidence.exists()
    else:
        assert one.journal.read_bytes() == data


@pytest.mark.parametrize("damage", ["mode", "owner", "symlink"])
def test_unsafe_journal_objects_on_the_real_filesystem_are_unavailable(make_pass, damage):
    one = make_pass()
    state = one.start_active()
    data = one.write_journal(state["InvocationID"])
    if damage == "mode":
        os.chmod(one.journal, 0o666)
    elif damage == "owner":
        os.chown(one.journal, 1000, 1000)
    else:
        real = one.evidence / "real"
        one.journal.rename(real)
        one.journal.symlink_to(real)
    since = stamp()
    proc = one.interrupt()
    assert proc.returncode == 30 and tail(proc) == "rp11-interrupt unavailable journal-unavailable", proc.stderr
    assert show(UNIT, "ActiveState")["ActiveState"] == "active" and sudo_stop_lines(since) == []
    assert data


def test_an_unrelated_unit_and_pending_job_are_untouched_by_a_stop(make_pass):
    one = make_pass()
    token = secrets.token_hex(4)
    steady, pending = f"rp11-exec-unrelated-{token}.service", f"rp11-exec-pending-{token}.service"
    make_pass.extra_units.extend([steady, pending])
    assert run("systemd-run", "--quiet", f"--unit={steady}", "/usr/bin/sleep", "600").returncode == 0
    assert run("systemd-run", "--quiet", "--no-block", f"--unit={pending}", "--property=ExecStartPre=/usr/bin/sleep 600",
               "--property=TimeoutStartSec=900", "/usr/bin/sleep", "600").returncode == 0
    assert wait_until(lambda: show(pending, "ActiveState")["ActiveState"] == "activating", 20)
    keep = (show(steady, "ActiveState", "InvocationID", "MainPID"), show(pending, "ActiveState", "InvocationID", "Job"))
    state = one.start_active()
    one.write_journal(state["InvocationID"])
    proc = one.interrupt()
    assert proc.returncode == 0, proc.stderr
    assert show(UNIT, "ActiveState")["ActiveState"] == "inactive"
    assert (show(steady, "ActiveState", "InvocationID", "MainPID"), show(pending, "ActiveState", "InvocationID", "Job")) == keep
    jobs = run("systemctl", "list-jobs", "--no-legend", "--no-pager").stdout
    assert pending in jobs and UNIT not in jobs


@pytest.mark.parametrize("argv", [(), ("x",), ("rp11-capture-pass-a.service",)])
def test_invalid_operands_are_refused_before_any_bus_journal_or_sudo_activity(make_pass, argv):
    one = make_pass()
    state = one.start_active()
    since = stamp()
    proc = one.interrupt(*argv) if argv else subprocess.run(
        [*OPERATOR, "env", "-i", "PATH=/usr/bin:/bin", PYTHON, "-B", "-m", "adapters.executor.interrupt"],
        capture_output=True, text=True, cwd=REPO)
    assert proc.returncode == 64 and proc.stderr == "rp11-interrupt usage\n"
    assert show(UNIT, "ActiveState", "InvocationID")["InvocationID"] == state["InvocationID"] and sudo_stop_lines(since) == []


@pytest.mark.parametrize("target,change", [
    ("file", "uid"), ("file", "gid"), ("directory", "uid"), ("directory", "gid"),
    ("file", "mode"), ("directory", "mode"), ("file", "replace"), ("file", "unlink"),
])
def test_root_owned_journal_changes_during_the_read_are_unavailable(make_pass, monkeypatch, target, change):
    from adapters.executor import interrupt as module

    one = make_pass()
    state = one.start_active()
    one.write_journal(state["InvocationID"])
    reader = module.LocalConsumeJournalReader()
    assert reader.read_consume_journal(one.id) is not None  # the unchanged control object is accepted
    real = module._read_capped

    def read_then_change(fd, size):
        data = real(fd, size)
        path = one.journal if target == "file" else one.evidence
        if change == "uid":
            os.chown(path, 1001, -1)
        elif change == "gid":
            os.chown(path, -1, 1001)
        elif change == "mode":
            os.chmod(path, 0o600 if target == "file" else 0o700)
        elif change == "replace":
            other = one.evidence / "journal.new"
            other.write_bytes(data)
            os.chmod(other, 0o644)
            os.rename(other, one.journal)
        elif change == "unlink":
            os.unlink(one.journal)
        return data

    monkeypatch.setattr(module, "_read_capped", read_then_change)
    since = stamp()
    assert module.LocalConsumeJournalReader().read_consume_journal(one.id) is None
    assert sudo_stop_lines(since) == []


def test_an_absent_supervisor_refuses_before_any_sudo_and_the_capture_pass_continues(make_pass, real_supervisor):
    """CX-3 with an unavailable owner: nothing is launched, and the pass is neither stopped nor attested."""
    one = make_pass()
    state = one.start_active()
    one.write_journal(state["InvocationID"])
    sctl("stop", real_supervisor.name)
    try:
        since = stamp()
        proc = one.interrupt()
        assert proc.returncode == 21 and proc.stderr == "rp11-interrupt error stop-not-sent\n", proc.stderr
        assert show(UNIT, "ActiveState", "InvocationID")["InvocationID"] == state["InvocationID"]
        assert show(UNIT, "ActiveState")["ActiveState"] == "active" and sudo_stop_lines(since) == []
    finally:
        real_supervisor.start()
    proc = one.interrupt()  # the owner is back: the same pass is stopped, once
    assert proc.returncode == 0, proc.stderr
