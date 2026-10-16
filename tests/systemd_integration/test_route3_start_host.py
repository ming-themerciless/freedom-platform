"""SA-1 ``start`` through the controlled artifact on the disposable host.

The artifact is built fresh from the hash-pinned wheel and the role is launched
as the executor does: ``ubuntu`` through the ``sudo -n`` preamble (EX-1). Real
systemd and Polkit; synthetic activations only. The complete holder lifecycle
(ACT, HL, IGR, stop-post, backstop) through this role is
``test_route3_hold_host.py::test_hold_activates_the_operator_starts_the_pass_and_every_rung_cleans_up``.

    sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test \\
        FREEDOM_RP11_WHEEL=/path/to/jeepney-0.9.0-py3-none-any.whl \\
        /opt/freedom-blades/runtime/venv-web/bin/python -m pytest -q -rfEs \\
        tests/systemd_integration/test_route3_start_host.py
"""

from __future__ import annotations

import re
import secrets
from datetime import UTC, datetime

import test_route3_hold_host as hold_host  # noqa: F401  (applies the same disposable-host guards)
from test_route3_hold_host import activations, artifact, run, show, wait_until  # noqa: F401

from adapters.rp11.start import run_start
from adapters.systemd.bus import BusTimeout
from adapters.systemd.jeepney_bus import connect_system_bus
from adapters.systemd.manager import ROLE_ARTIFACT, ROLE_INTERPRETER

A2 = "5f" * 32


def stderr_tail(proc) -> str:
    return proc.stderr.rstrip().splitlines()[-1]


def exec_argv(unit: str, prop: str) -> list[str]:
    value = show(unit, prop)[prop]
    found = re.search(r"argv\[\]=(.*?) ;", value)
    assert found, value
    return found.group(1).split(" ")


def test_start_creates_exactly_the_accepted_holder_unit_under_sudo(activations):
    act = activations()
    act.prepare()
    proc = act.start_holder_via_role()
    assert proc.returncode == 0, proc.stderr
    assert "rp11_h1: role=start runtime=ok" in proc.stderr and stderr_tail(proc) == "rp11-start started"
    props = show(
        act.unit, "Type", "Restart", "OOMScoreAdjust", "RuntimeMaxUSec", "TimeoutStopUSec", "Environment", "User",
    )
    assert props["Type"] == "exec" and props["Restart"] == "no" and props["OOMScoreAdjust"] == "-1000"
    assert props["RuntimeMaxUSec"] == "15min" and props["TimeoutStopUSec"] == "1min"
    assert props["Environment"] == "" and props["User"] == ""
    assert exec_argv(act.unit, "ExecStart") == [
        ROLE_INTERPRETER, "-I", "-S", ROLE_ARTIFACT, "hold", act.id, act.fx.a2_sha256,
    ]
    assert exec_argv(act.unit, "ExecStopPost") == [
        ROLE_INTERPRETER, "-I", "-S", ROLE_ARTIFACT, "deact", act.id, act.fx.a2_sha256, "stop-post",
    ]
    units = run("systemctl", "list-units", f"{act.id}*", "--all", "--no-legend", "--plain").stdout.split()
    assert {u for u in units if u.startswith("rp11-act-")} <= {act.unit, act.timer, act.backstop_service}
    assert not any(u.endswith((".scope", ".slice")) for u in units)
    act.wait_op("hold-start")
    run("systemctl", "stop", act.unit, check=True)
    hold, cl = act.wait_stopped()
    assert hold.startswith(f"rp11-hold interrupted {act.id}") and cl.startswith(f"rp11-cl st1-verified {act.id}")


def test_a_loaded_name_is_refused_once_and_the_first_holder_is_untouched(activations):
    act = activations()
    act.prepare()
    assert act.start_holder_via_role().returncode == 0
    act.wait_op("hold-start")
    before = show(act.unit, "InvocationID", "MainPID", "ActiveState")
    again = act.start_holder_via_role()
    assert again.returncode == 20 and stderr_tail(again) == "rp11-start refused exists", again.stderr
    assert show(act.unit, "InvocationID", "MainPID", "ActiveState") == before
    run("systemctl", "stop", act.unit, check=True)
    act.wait_stopped()


def test_without_authorization_the_role_is_refused_and_creates_nothing():
    activation_id = f"rp11-act-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{secrets.token_hex(4)}"
    # ubuntu without sudo: the real manager's authorization (Polkit) refuses it.
    proc = run(
        "runuser", "-u", "ubuntu", "--", ROLE_INTERPRETER, "-I", "-S", ROLE_ARTIFACT,
        "start", activation_id, A2, "900", "60",
    )
    # Exact: a connector, manager or subscription failure is a different outcome
    # (21, effect-not-sent) and must fail this test, not satisfy it.
    assert proc.returncode == 20, (proc.returncode, proc.stderr)
    assert stderr_tail(proc) == "rp11-start refused not-authorized", proc.stderr
    assert show(f"{activation_id}.service", "LoadState")["LoadState"] == "not-found"
    assert run("systemctl", "list-units", f"{activation_id}*", "--all", "--no-legend").stdout.strip() == ""


class TimeoutAfterSend:
    """The real connection; the mutating call is sent for real, then its reply is
    withheld (a deadline). ``sent`` proves the role never sends a second time."""

    def __init__(self, sent: list[str]) -> None:
        self._real, self._sent = connect_system_bus(), sent

    def call(self, request, *, timeout):
        if request.member != "StartTransientUnit":
            return self._real.call(request, timeout=timeout)
        self._sent.append(request.member)
        self._real.call(request, timeout=timeout)  # the effect really happens
        raise BusTimeout("injected deadline after the call was sent")

    def watch_signals(self, **kwargs):
        return self._real.watch_signals(**kwargs)

    def close(self):
        self._real.close()


def test_an_unconfirmed_outcome_is_one_send_no_retry_and_never_success(activations, capsys):
    act = activations()
    act.prepare()
    sent: list[str] = []
    status = run_start(
        act.id, act.fx.a2_sha256, act.lease["lease_s"], act.lease["stop_timeout_s"],
        connector=lambda: TimeoutAfterSend(sent),
    )
    assert status == 22 and capsys.readouterr().err == "rp11-start error effect-not-confirmed\n"
    assert sent == ["StartTransientUnit"]
    assert wait_until(lambda: show(act.unit, "ActiveState")["ActiveState"] == "active", 10)
    again = act.start_holder_via_role()  # a blind retry by the executor cannot duplicate
    assert again.returncode == 20 and stderr_tail(again) == "rp11-start refused exists", again.stderr
    act.wait_op("hold-start")
    run("systemctl", "stop", act.unit, check=True)
    act.wait_stopped()
