"""SA-2 ``stop`` through the controlled artifact on the disposable host.

The artifact is built fresh from the hash-pinned wheel and the role is launched
as the executor does: ``ubuntu`` through the ``sudo -n`` preamble (EX-1). Real
systemd and Polkit against a disposable ``rp11-capture-pass-a.service``; synthetic
data only. Nothing here uses a record store beyond what the shared fixture
prepares and tears down.

    sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test \\
        FREEDOM_RP11_WHEEL=/path/to/jeepney-0.9.0-py3-none-any.whl \\
        /opt/freedom-blades/runtime/venv-web/bin/python -m pytest -q -rfEs \\
        tests/systemd_integration/test_route3_stop_host.py
"""

from __future__ import annotations

import test_route3_hold_host as hold_host  # noqa: F401  (applies the same disposable-host guards)
from test_route3_hold_host import (  # noqa: F401
    CAPTURE_UNIT_FILE,
    activations,
    artifact,
    run,
    show,
)

from adapters.rp11.stop import run_stop
from adapters.systemd.bus import BusTimeout
from adapters.systemd.jeepney_bus import connect_system_bus
from adapters.systemd.manager import ROLE_ARTIFACT, ROLE_INTERPRETER

UNIT = "rp11-capture-pass-a.service"
VECTOR = [ROLE_INTERPRETER, "-I", "-S", ROLE_ARTIFACT, "stop"]


def stderr_tail(proc) -> str:
    return proc.stderr.rstrip().splitlines()[-1]


def sudo_stop(*prefix: str, tail: tuple[str, ...] = ()):
    """SA-2 as the executor runs it: ``ubuntu`` through ``sudo -n`` (EX-1)."""
    return run("runuser", "-u", "ubuntu", "--", "sudo", "-n", *prefix, *VECTOR, *tail)


def unit_jobs(unit: str = UNIT) -> list[str]:
    """Queued jobs for exactly ``unit``; jobs of any other unit are not our concern."""
    rows = run("systemctl", "list-jobs", "--no-legend", "--no-pager").stdout.splitlines()
    return [row for row in rows if len(row.split()) > 1 and row.split()[1] == unit]


def prepared(activations, capture="long"):
    act = activations()
    act.prepare(capture=capture, restart=False)
    return act


def start_capture() -> dict[str, str]:
    run("systemctl", "start", UNIT, check=True)
    state = show(UNIT, "ActiveState", "InvocationID", "MainPID")
    assert state["ActiveState"] == "active"
    return state


def test_an_active_capture_unit_receives_one_stop_and_the_role_returns_stopped(activations):
    prepared(activations)
    start_capture()
    proc = sudo_stop()
    assert proc.returncode == 0, proc.stderr
    assert "rp11_h1: role=stop runtime=ok" in proc.stderr and stderr_tail(proc) == "rp11-stop stopped"
    assert show(UNIT, "ActiveState")["ActiveState"] == "inactive"
    assert unit_jobs() == []


def test_the_connector_sees_exactly_one_stop_unit_call_for_the_fixed_unit(activations):
    prepared(activations)
    start_capture()
    seen: list[tuple[str, tuple]] = []

    class Counting:
        def __init__(self):
            self._real = connect_system_bus()

        def call(self, request, *, timeout):
            if request.member == "StopUnit":
                seen.append((request.member, request.body))
            return self._real.call(request, timeout=timeout)

        def watch_signals(self, **kwargs):
            return self._real.watch_signals(**kwargs)

        def close(self):
            self._real.close()

    assert run_stop(connector=Counting) == 0
    assert seen == [("StopUnit", (UNIT, "fail"))]


def test_a_loaded_inactive_capture_unit_is_stopped_without_claiming_causation(activations):
    prepared(activations)
    start_capture()
    run("systemctl", "stop", UNIT, check=True)
    assert show(UNIT, "ActiveState", "LoadState") == {"ActiveState": "inactive", "LoadState": "loaded"}
    proc = sudo_stop()
    assert proc.returncode == 0, proc.stderr
    assert stderr_tail(proc) == "rp11-stop stopped"
    assert "already" not in proc.stderr


def test_a_loaded_failed_capture_unit_is_stopped(activations):
    prepared(activations)
    CAPTURE_UNIT_FILE.write_text(
        "[Unit]\nDescription=RP-11 synthetic failing capture (disposable host test)\n\n"
        "[Service]\nType=exec\nExecStart=/usr/bin/false\n"
    )
    run("systemctl", "daemon-reload", check=True)
    run("systemctl", "start", UNIT)
    assert show(UNIT, "ActiveState")["ActiveState"] == "failed"
    proc = sudo_stop()
    assert proc.returncode == 0, proc.stderr
    assert stderr_tail(proc) == "rp11-stop stopped"


def test_a_not_loaded_capture_unit_is_refused_and_no_stop_job_is_queued(activations):
    prepared(activations)
    CAPTURE_UNIT_FILE.unlink()
    run("systemctl", "daemon-reload", check=True)
    run("systemctl", "reset-failed", UNIT)
    assert show(UNIT, "LoadState")["LoadState"] == "not-found"
    proc = sudo_stop()
    assert proc.returncode == 20, (proc.returncode, proc.stderr)
    assert stderr_tail(proc) == "rp11-stop refused not-loaded"
    assert unit_jobs() == []


def test_without_authorization_the_role_is_refused_and_the_unit_keeps_running(activations):
    prepared(activations)
    before = start_capture()
    # ubuntu without sudo: the real manager's authorization (Polkit) refuses it.
    proc = run("runuser", "-u", "ubuntu", "--", *VECTOR)
    assert proc.returncode == 20, (proc.returncode, proc.stderr)  # not 21: a pre-send error is a different outcome
    assert stderr_tail(proc) == "rp11-stop refused not-authorized", proc.stderr
    assert show(UNIT, "ActiveState", "InvocationID", "MainPID") == before
    assert unit_jobs() == []


class TimeoutAfterSend:
    """The real connection; the mutating call is sent for real, then its reply is
    withheld (a deadline). ``sent`` proves the role never sends a second time."""

    def __init__(self, sent: list[str]) -> None:
        self._real, self._sent = connect_system_bus(), sent

    def call(self, request, *, timeout):
        if request.member != "StopUnit":
            return self._real.call(request, timeout=timeout)
        self._sent.append(request.member)
        self._real.call(request, timeout=timeout)  # the effect really happens
        raise BusTimeout("injected deadline after the call was sent")

    def watch_signals(self, **kwargs):
        return self._real.watch_signals(**kwargs)

    def close(self):
        self._real.close()


def test_an_unconfirmed_outcome_is_one_send_no_retry_and_never_promoted(activations, capsys):
    prepared(activations)
    start_capture()
    sent: list[str] = []
    status = run_stop(connector=lambda: TimeoutAfterSend(sent))
    assert status == 22 and capsys.readouterr().err == "rp11-stop error effect-not-confirmed\n"
    assert sent == ["StopUnit"]
    # The stop really happened, yet the observation does not turn 22 into success.
    assert show(UNIT, "ActiveState")["ActiveState"] == "inactive"
    assert status == 22


def test_an_extra_operand_is_refused_before_any_manager_call(activations):
    prepared(activations)
    before = start_capture()
    for tail in (("x",), (UNIT,), ("--force",), ("stop",)):
        proc = sudo_stop(tail=tail)
        assert proc.returncode == 64, (tail, proc.returncode, proc.stderr)
        assert "not an accepted role vector" in proc.stderr
    assert show(UNIT, "ActiveState", "InvocationID", "MainPID") == before
    assert unit_jobs() == []


def test_hostile_environment_entries_cannot_change_a_valid_stop(activations):
    prepared(activations)
    start_capture()
    proc = sudo_stop("/usr/bin/env", "INVOCATION_ID=not-hex", "PYTHONPATH=/evil", "LD_PRELOAD=/evil.so")
    assert proc.returncode == 0, proc.stderr
    assert stderr_tail(proc) == "rp11-stop stopped"
    assert "INVOCATION_ID" not in proc.stderr
    start_capture()
    big = "INVOCATION_ID=" + "a" * 100_000
    proc = sudo_stop("/usr/bin/env", big, *[f"PAD{i}={'x' * 100_000}" for i in range(11)])
    assert proc.returncode == 0, proc.stderr[-300:]
    assert stderr_tail(proc) == "rp11-stop stopped"
