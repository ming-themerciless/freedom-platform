"""Route 3 manager/Polkit adapter against the real system bus, systemd and Polkit.

These tests create real transient units, write a temporary Polkit rule, spawn
unprivileged processes and restart the manager. They are therefore opt-in and
refuse to run anywhere except the disposable host:

    sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test \\
        FREEDOM_RP11_WHEEL=/path/to/jeepney-0.9.0-py3-none-any.whl \\
        /opt/freedom-blades/runtime/venv-web/bin/python -m pytest -q -rs \\
        tests/systemd_integration

Every holder and backstop runs the exact role vector, so the controlled artifact
is built with ``infra/rp11-h1/build.py`` (from the hash-pinned wheel) into its
fixed path for the session and removed afterwards. Most tests install it with
``rp11_roles_double.py`` so a holder keeps running; the exact-runtime tests use
the production build, whose ``hold`` role finds no A-2 here and refuses, and whose
``stop-post`` and ``backstop`` are the real cleanup rungs
(``test_route3_stop_post_host.py``, ``test_route3_backstop_host.py``).

They live outside ``tests/test_*.py`` so the documented skip baseline of the
bot suite is unaffected. Everything created is unit-prefixed ``rp11-act-`` (or is
the one fixed ``rp11-capture-pass-a.service``), is tracked, and is removed by the
``host`` fixture teardown, which then asserts nothing was left behind.
"""

from __future__ import annotations

import importlib.util
import json
import os
import secrets
import shutil
import socket
import subprocess
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

if os.environ.get("FREEDOM_SYSTEMD_INTEGRATION") != "oracle-test":
    pytest.skip(
        "set FREEDOM_SYSTEMD_INTEGRATION=oracle-test (disposable host only)",
        allow_module_level=True,
    )
if socket.gethostname() != "Test":
    pytest.skip(
        "refusing to run: not the disposable host (hostname != Test)", allow_module_level=True
    )
if os.geteuid() != 0 or not Path("/run/systemd/system").is_dir():
    pytest.skip("needs root on a systemd host", allow_module_level=True)
pytest.importorskip("jeepney")

from adapters.systemd.bus import BusDisconnected, BusReply, BusRequest, BusTimeout, Variant  # noqa: E402
from adapters.systemd.jeepney_bus import _to_wire, connect_system_bus  # noqa: E402
from adapters.systemd import manager as manager_module  # noqa: E402
from adapters.systemd.manager import (  # noqa: E402
    ROLE_ARTIFACT,
    ROLE_INTERPRETER,
    Deadlines,
    SystemdManagerAdapter,
    unit_object_path,
)
from adapters.systemd.polkit import PolkitAuthorityAdapter  # noqa: E402
from adapters.systemd.subject import ProcSubjectSource  # noqa: E402
from application.unit_control import (  # noqa: E402
    CAPTURE_UNIT,
    BackstopCompletion,
    BackstopSpec,
    ControlError,
    ControlOk,
    ControlRefused,
    HolderSpec,
    PolkitAuthorized,
    PolkitNotAuthorized,
    ProcessSubject,
    RefusalReason,
    StopOutcome,
    TimerObservation,
    UnitProperty,
    UnitVerb,
)

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = Path(ROLE_ARTIFACT).parent
ARTIFACT_LIB = ARTIFACT_DIR / "lib"
ROLES_DOUBLE = Path(__file__).resolve().parent / "rp11_roles_double.py"
A2 = "5f" * 32  # synthetic A-2 identity
RULE_FILE = Path("/etc/polkit-1/rules.d/49-rp11-integration-test.rules")
NOBODY = 65534
SLEEP = "/usr/bin/sleep"


def _load_builder():
    spec = importlib.util.spec_from_file_location("rp11_h1_build", ROOT / "infra/rp11-h1/build.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_installed: list[str] = []


def remove_artifact() -> None:
    if ARTIFACT_DIR.is_symlink():
        ARTIFACT_DIR.unlink()
    shutil.rmtree(ARTIFACT_DIR, ignore_errors=True)
    _installed.clear()


def install_artifact(kind: str) -> None:
    """Build the artifact into its fixed path with the production or double roles."""
    if _installed == [kind]:
        return
    remove_artifact()
    wheel = os.environ.get("FREEDOM_RP11_WHEEL")
    assert wheel, "set FREEDOM_RP11_WHEEL to the jeepney wheel requirements.lock pins"
    roles = ROLES_DOUBLE if kind == "double" else None
    _load_builder().build(Path(wheel), ARTIFACT_DIR, roles)
    _installed[:] = [kind]


@pytest.fixture(scope="module", autouse=True)
def artifact():
    assert Path(ROLE_INTERPRETER).is_file(), f"{ROLE_INTERPRETER} is the role interpreter"
    install_artifact("double")
    yield
    remove_artifact()
    assert not os.path.lexists(ARTIFACT_DIR)
    assert not list(ARTIFACT_DIR.parent.glob(f".{ARTIFACT_DIR.name}.*"))  # no staging


@pytest.fixture
def double_roles():
    install_artifact("double")


def run(*argv: str, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True, check=check)


def show(unit: str, *props: str) -> dict[str, str]:
    out = run("systemctl", "show", unit, *(f"-p{p}" for p in props)).stdout
    values: dict[str, str] = {}
    for line in out.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            # Repeated properties (TimersMonotonic) are joined, not overwritten.
            values[key] = f"{values[key]}\n{value}" if key in values else value
    return values


def active_state(unit: str) -> str:
    return show(unit, "ActiveState").get("ActiveState", "?")


def wait_until(predicate, timeout=15.0, interval=0.1):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()


def loaded_units(prefix_glob: str) -> list[str]:
    out = run("systemctl", "list-units", prefix_glob, "--all", "--no-legend", "--plain").stdout
    return [line.split()[0] for line in out.splitlines() if line.strip()]


class Host:
    """Tracks every unit/process/rule this run creates and removes them."""

    def __init__(self) -> None:
        self.activation_ids: list[str] = []
        self.processes: list[subprocess.Popen] = []

    def activation_id(self) -> str:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        activation_id = f"rp11-act-{stamp}-{secrets.token_hex(4)}"
        self.activation_ids.append(activation_id)
        return activation_id

    def owned_units(self) -> list[str]:
        units = []
        for activation_id in self.activation_ids:
            units += loaded_units(f"{activation_id}*")
        return units + loaded_units(CAPTURE_UNIT)

    def clean(self) -> None:
        for proc in self.processes:
            if proc.poll() is None:
                proc.kill()
            proc.wait()
        self.processes.clear()
        names = [CAPTURE_UNIT]
        for activation_id in self.activation_ids:
            names += [
                f"{activation_id}.service",
                f"{activation_id}-backstop.timer",
                f"{activation_id}-backstop.service",
            ]
        run("systemctl", "stop", *names)
        run("systemctl", "reset-failed", *names)
        RULE_FILE.unlink(missing_ok=True)
        for activation_id in self.activation_ids:
            _remove_cleanup_evidence(activation_id)

    def start_capture(self, *extra: str, command=(SLEEP, "600"), block: bool = True) -> None:
        argv = [
            "systemd-run",
            "--quiet",
            f"--unit={CAPTURE_UNIT}",
            "-p",
            "Type=exec",
            *extra,
            *command,
        ]
        if not block:
            argv.insert(1, "--no-block")
        run(*argv, check=True)

    def unprivileged_process(self) -> subprocess.Popen:
        proc = subprocess.Popen(
            ["setpriv", f"--reuid={NOBODY}", f"--regid={NOBODY}", "--clear-groups", SLEEP, "300"]
        )
        self.processes.append(proc)
        assert wait_until(lambda: _real_uid(proc.pid) == NOBODY, timeout=5)
        return proc


def _remove_cleanup_evidence(activation_id: str) -> None:
    """The real stop-post leaves its attempt evidence under /var/tmp (retained by
    design); the disposable-host tests remove it afterwards."""
    for entry in Path("/var/tmp").glob(f"{activation_id}-*"):
        shutil.rmtree(entry, ignore_errors=True)


def _real_uid(pid: int) -> int | None:
    try:
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith("Uid:"):
                return int(line.split()[1])
    except OSError:
        return None
    return None


@pytest.fixture
def host(double_roles):
    h = Host()
    h.clean()
    assert loaded_units(CAPTURE_UNIT) == [], "capture unit already present before the test"
    yield h
    h.clean()
    assert h.owned_units() == [], "test left units behind"
    assert not RULE_FILE.exists()


def adapter(**deadlines) -> SystemdManagerAdapter:
    return SystemdManagerAdapter(
        connect_system_bus, deadlines=Deadlines(**deadlines) if deadlines else Deadlines()
    )


def holder(activation_id: str, **overrides) -> HolderSpec:
    base = dict(
        activation_id=activation_id,
        artifact_sha256=A2,
        runtime_max_seconds=900,
        timeout_stop_seconds=30,
    )
    base.update(overrides)
    return HolderSpec(**base)


def backstop(activation_id: str, **overrides) -> BackstopSpec:
    base = dict(
        activation_id=activation_id,
        artifact_sha256=A2,
        interval_seconds=3600,
        runtime_max_seconds=120,
        timeout_stop_seconds=20,
    )
    base.update(overrides)
    return BackstopSpec(**base)


# --- fault injection over the real connection ------------------------------


class NeverSignals:
    def next(self, *, timeout):
        time.sleep(min(timeout, 0.2))
        raise BusTimeout("signal suppressed")


class Faulty:
    """Real connection; one fault applied to the mutating call or its signals.

    ``performs`` records whether the real call was sent, so a test can show the
    effect happened even though the adapter reported an error.
    """

    MUTATING = {"StartTransientUnit", "StopUnit"}

    def __init__(self, real, mode: str, sent: list[str]) -> None:
        self._real = real
        self._mode = mode
        self._sent = sent

    def call(self, request, *, timeout):
        if request.member not in self.MUTATING:
            return self._real.call(request, timeout=timeout)
        self._sent.append(request.member)
        if self._mode == "lost-reply":
            from jeepney import DBusAddress, new_method_call

            address = DBusAddress(
                request.path, bus_name=request.destination, interface=request.interface
            )
            message = new_method_call(
                address, request.member, request.signature, _to_wire(request.body)
            )
            self._real._connection.send_message(message)
            self._real.close()
            raise BusDisconnected("reply lost")
        real_reply = self._real.call(request, timeout=timeout)  # the effect really happens
        if self._mode == "timeout":
            raise BusTimeout("injected deadline after the call was sent")
        if self._mode == "malformed":
            return BusReply("s", ("garbage",))
        return real_reply

    def watch_signals(self, **kwargs):
        if self._mode == "no-signal":
            return NeverSignals()
        return self._real.watch_signals(**kwargs)

    def close(self):
        self._real.close()


def faulty_adapter(mode: str, sent: list[str], **deadlines) -> SystemdManagerAdapter:
    return SystemdManagerAdapter(
        lambda: Faulty(connect_system_bus(), mode, sent),
        deadlines=Deadlines(**deadlines) if deadlines else Deadlines(),
    )


# =============================== DI-1 ======================================


def test_read_unit_not_loaded_capture_unit_reports_stub_state(host):
    result = adapter().read_unit(CAPTURE_UNIT, tuple(UnitProperty))
    assert isinstance(result, ControlOk)
    values = result.value
    assert values[UnitProperty.LOAD_STATE] == "not-found"
    assert values[UnitProperty.ACTIVE_STATE] == "inactive"
    assert values[UnitProperty.JOB] == 0
    assert values[UnitProperty.INVOCATION_ID] == ""
    assert isinstance(values[UnitProperty.TIMEOUT_START_USEC], int)
    assert set(values) == set(UnitProperty)


def test_read_unit_active_service_reports_invocation_and_timestamps(host):
    host.start_capture()
    result = adapter().read_unit(CAPTURE_UNIT, tuple(UnitProperty))
    values = result.value
    assert values[UnitProperty.ACTIVE_STATE] == "active"
    assert values[UnitProperty.LOAD_STATE] == "loaded"
    assert len(values[UnitProperty.INVOCATION_ID]) == 32
    assert values[UnitProperty.INVOCATION_ID] == show(CAPTURE_UNIT, "InvocationID")["InvocationID"]
    assert values[UnitProperty.EXEC_MAIN_START_TIMESTAMP_MONOTONIC] > 0
    assert values[UnitProperty.RESULT] == "success"


def test_read_unit_rejects_unlisted_unit_before_the_bus(host):
    result = adapter().read_unit("ssh.service", (UnitProperty.ACTIVE_STATE,))
    assert isinstance(result, ControlError) and result.kind == "invalid-request"


# =============================== DI-2 ======================================


def test_create_holder_creates_the_unit_with_the_requested_properties(host):
    activation_id = host.activation_id()
    result = adapter().create_holder(holder(activation_id))
    assert isinstance(result, ControlOk), result
    unit = f"{activation_id}.service"
    shown = show(
        unit,
        "Type",
        "Restart",
        "OOMScoreAdjust",
        "RuntimeMaxUSec",
        "TimeoutStopUSec",
        "ActiveState",
        "ExecStopPost",
        "ExecStart",
    )
    assert shown["Type"] == "exec" and shown["Restart"] == "no"
    assert shown["OOMScoreAdjust"] == "-1000"
    assert shown["RuntimeMaxUSec"] == "15min" and shown["TimeoutStopUSec"] == "30s"
    assert shown["ActiveState"] == "active"
    runtime = f"argv[]={ROLE_INTERPRETER} -I -S {ROLE_ARTIFACT}"
    assert f"path={ROLE_INTERPRETER} ; {runtime} hold {activation_id} {A2} ;" in shown["ExecStart"]
    assert (
        f"path={ROLE_INTERPRETER} ; {runtime} deact {activation_id} {A2} stop-post ;"
        in shown["ExecStopPost"]
    )
    assert result.value.observed[UnitProperty.ACTIVE_STATE] == "active"


def test_create_holder_twice_is_refused_exists_and_leaves_the_first_untouched(host):
    activation_id = host.activation_id()
    assert isinstance(adapter().create_holder(holder(activation_id)), ControlOk)
    unit = f"{activation_id}.service"
    before = show(unit, "InvocationID", "ExecMainPID")
    assert adapter().create_holder(holder(activation_id)) == ControlRefused(RefusalReason.EXISTS)
    assert show(unit, "InvocationID", "ExecMainPID") == before


def test_create_holder_whose_job_fails_is_job_result_error(host, monkeypatch):
    # The public API cannot name another executable; the internal constant is
    # redirected here only to make PID 1's exec fail and prove the mapping.
    monkeypatch.setattr(manager_module, "ROLE_INTERPRETER", "/nonexistent/python3.14")
    activation_id = host.activation_id()
    # The pre-execution check refuses such a runtime before the bus ...
    refused = adapter().create_holder(holder(activation_id))
    assert isinstance(refused, ControlError) and refused.kind == "unsafe-artifact"
    assert not refused.effect_not_confirmed and host.owned_units() == []
    # ... so it is bypassed here to reach PID 1's failing exec.
    monkeypatch.setattr(manager_module, "_role_runtime_problem", lambda: None)
    result = adapter().create_holder(holder(activation_id))
    assert isinstance(result, ControlError)
    assert result.kind == "job-result" and result.effect_not_confirmed
    assert "failed" in result.detail


def test_concurrent_duplicate_create_yields_one_success_and_one_refusal(host):
    activation_id = host.activation_id()
    results: list = []
    barrier = threading.Barrier(2)

    def go():
        barrier.wait()
        results.append(adapter().create_holder(holder(activation_id)))

    threads = [threading.Thread(target=go) for _ in range(2)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    oks = [r for r in results if isinstance(r, ControlOk)]
    others = [r for r in results if not isinstance(r, ControlOk)]
    assert len(oks) == 1, results
    assert len(others) == 1 and (
        others[0] == ControlRefused(RefusalReason.EXISTS) or isinstance(others[0], ControlError)
    ), others
    assert active_state(f"{activation_id}.service") == "active"


# =============================== DI-3 ======================================


def test_create_backstop_creates_timer_and_service_without_start_timeout(host):
    activation_id = host.activation_id()
    result = adapter().create_backstop(backstop(activation_id))
    assert isinstance(result, ControlOk), result
    timer = f"{activation_id}-backstop.timer"
    service = f"{activation_id}-backstop.service"
    # DI-3 O-C: the adapter's own returned observation names the aux service.
    assert isinstance(result.value, BackstopCompletion) and result.value.timer == timer
    assert result.value.observed == TimerObservation(
        active_state="active", load_state="loaded", triggers=(service,), unit=service
    )
    timer_props = show(timer, "ActiveState", "AccuracyUSec", "TimersMonotonic", "Triggers", "Unit")
    assert timer_props["ActiveState"] == "active"
    assert timer_props["AccuracyUSec"] == "1s"
    assert "OnActiveUSec=1h" in timer_props["TimersMonotonic"]
    assert "OnUnitActiveUSec=1h" in timer_props["TimersMonotonic"]
    assert timer_props["Unit"] == service
    svc = show(
        service,
        "Type",
        "Restart",
        "OOMScoreAdjust",
        "RuntimeMaxUSec",
        "TimeoutStopUSec",
        "TimeoutStartUSec",
        "ActiveState",
        "ExecStart",
    )
    assert (
        f"argv[]={ROLE_INTERPRETER} -I -S {ROLE_ARTIFACT} backstop {activation_id} {A2} ;"
        in svc["ExecStart"]
    )
    assert svc["Type"] == "exec" and svc["Restart"] == "no" and svc["OOMScoreAdjust"] == "-1000"
    assert svc["RuntimeMaxUSec"] == "2min" and svc["TimeoutStopUSec"] == "20s"
    # D-10: not set by DI-3, so it is the manager default rather than a value we chose.
    manager_default = run(
        "systemctl", "show", "-p", "DefaultTimeoutStartUSec", "--value"
    ).stdout.strip()
    assert manager_default and svc["TimeoutStartUSec"] == manager_default
    assert svc["ActiveState"] == "inactive"  # nothing has fired it


def test_create_backstop_duplicate_is_an_error_not_a_refusal(host):
    activation_id = host.activation_id()
    assert isinstance(adapter().create_backstop(backstop(activation_id)), ControlOk)
    again = adapter().create_backstop(backstop(activation_id))
    assert isinstance(again, ControlError) and again.effect_not_confirmed


# =============================== DI-4 ======================================


def test_disarm_backstop_stops_the_timer_and_a_second_disarm_is_not_loaded(host):
    activation_id = host.activation_id()
    assert isinstance(adapter().create_backstop(backstop(activation_id)), ControlOk)
    result = adapter().disarm_backstop(activation_id)
    assert isinstance(result, ControlOk) and result.value.outcome is StopOutcome.STOPPED
    assert active_state(f"{activation_id}-backstop.timer") == "inactive"
    # The transient timer is released once inactive, so a repeat is NoSuchUnit.
    assert wait_until(
        lambda: adapter().disarm_backstop(activation_id) == ControlRefused(RefusalReason.NOT_LOADED)
    )


def test_disarm_unknown_activation_is_not_loaded(host):
    activation_id = host.activation_id()
    assert adapter().disarm_backstop(activation_id) == ControlRefused(RefusalReason.NOT_LOADED)


# =============================== DI-S ======================================


def test_stop_capture_unit_active_inactive_and_not_loaded(host):
    host.start_capture()
    first = adapter().stop_capture_unit()
    assert isinstance(first, ControlOk) and first.value.outcome is StopOutcome.STOPPED
    assert active_state(CAPTURE_UNIT) == "inactive"
    # Transient unit collected after the stop: not-loaded, distinct from the no-op.
    assert wait_until(
        lambda: adapter().stop_capture_unit() == ControlRefused(RefusalReason.NOT_LOADED)
    )


def test_stop_capture_unit_loaded_but_failed_is_a_completed_stop(host):
    host.start_capture(command=("/usr/bin/false",))
    assert wait_until(lambda: active_state(CAPTURE_UNIT) == "failed")
    result = adapter().stop_capture_unit()
    assert isinstance(result, ControlOk) and result.value.outcome is StopOutcome.STOPPED


def test_stop_only_touches_the_capture_unit(host):
    activation_id = host.activation_id()
    assert isinstance(adapter().create_holder(holder(activation_id)), ControlOk)
    host.start_capture()
    assert isinstance(adapter().stop_capture_unit(), ControlOk)
    assert active_state(f"{activation_id}.service") == "active"


def test_stop_during_a_running_start_job_conflicts_under_mode_fail(host):
    # Pins why the job mode is "fail": "replace" would cancel somebody's start job.
    host.start_capture("-p", "ExecStartPre=/usr/bin/sleep 5", block=False)
    assert wait_until(lambda: active_state(CAPTURE_UNIT) == "activating", timeout=5)
    result = adapter().stop_capture_unit()
    assert isinstance(result, ControlError) and result.effect_not_confirmed
    assert result.kind == "org.freedesktop.systemd1.TransactionIsDestructive"
    assert wait_until(
        lambda: active_state(CAPTURE_UNIT) == "active", timeout=10
    )  # start job untouched


def test_concurrent_stops_of_an_active_unit_are_each_a_completed_stop_or_unconfirmed(host):
    host.start_capture("-p", "ExecStop=/usr/bin/sleep 2")
    results: list = []
    barrier = threading.Barrier(3)

    def go():
        barrier.wait()
        results.append(adapter().stop_capture_unit())

    threads = [threading.Thread(target=go) for _ in range(3)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    for r in results:
        assert isinstance(r, (ControlOk, ControlError, ControlRefused)), r
        if isinstance(r, ControlError):
            assert r.effect_not_confirmed
    assert any(isinstance(r, ControlOk) for r in results), results
    assert wait_until(lambda: active_state(CAPTURE_UNIT) == "inactive")


# ============== authorization (manager side) ================================

_UNPRIVILEGED_SCRIPT = r"""
import json, sys
sys.path[:0] = [{root!r}]
sys.path.append({lib!r})
from adapters.systemd.jeepney_bus import connect_system_bus
from adapters.systemd.manager import SystemdManagerAdapter
from application.unit_control import *
a = SystemdManagerAdapter(connect_system_bus)
aid = {aid!r}
out = {{}}
out["holder"] = repr(a.create_holder(HolderSpec(aid, {a2!r}, 60, 10)))
out["backstop"] = repr(a.create_backstop(BackstopSpec(aid, {a2!r}, 60, 60, 10)))
out["stop"] = repr(a.stop_capture_unit())
out["disarm"] = repr(a.disarm_backstop(aid))
out["read"] = repr(a.read_unit("rp11-capture-pass-a.service", (UnitProperty.ACTIVE_STATE,)))
print(json.dumps(out))
"""


def test_unprivileged_caller_is_refused_and_nothing_is_created(host):
    activation_id = host.activation_id()
    # The unprivileged caller uses the artifact's vendored client, not the venv.
    script = _UNPRIVILEGED_SCRIPT.format(
        root=str(ROOT), lib=str(ARTIFACT_LIB), aid=activation_id, a2=A2
    )
    proc = subprocess.run(
        [
            "setpriv",
            f"--reuid={NOBODY}",
            f"--regid={NOBODY}",
            "--clear-groups",
            "/usr/bin/python3",
            "-c",
            script,
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    refused = repr(ControlRefused(RefusalReason.NOT_AUTHORIZED))
    assert out["holder"] == out["backstop"] == out["stop"] == out["disarm"] == refused
    assert out["read"].startswith("ControlOk")  # reads are unprivileged
    assert host.owned_units() == [] or all(
        "backstop" not in u and not u.endswith(f"{activation_id}.service")
        for u in host.owned_units()
    )


# =============================== DI-6 / DI-5 ================================


def test_subject_for_a_live_process_matches_proc_and_polkit_accepts_it(host):
    proc = host.unprivileged_process()
    subject = ProcSubjectSource().subject_for_pid(proc.pid)
    assert isinstance(subject, ControlOk)
    assert subject.value.uid == NOBODY
    stat = Path(f"/proc/{proc.pid}/stat").read_text().rsplit(")", 1)[1].split()
    assert subject.value.start_time == int(stat[19])
    # polkitd accepts the subject (a replaced process would be an ERROR, not a decision).
    outcome = PolkitAuthorityAdapter(connect_system_bus).check(subject.value, UnitVerb.START)
    assert isinstance(outcome, (PolkitAuthorized, PolkitNotAuthorized))


def test_polkit_default_policy_is_a_challenge_for_an_unprivileged_subject(host):
    proc = host.unprivileged_process()
    subject = ProcSubjectSource().subject_for_pid(proc.pid).value
    polkit = PolkitAuthorityAdapter(connect_system_bus)
    assert polkit.check(subject, UnitVerb.START) == PolkitNotAuthorized(challenge=True)
    assert polkit.check(subject, UnitVerb.STOP) == PolkitNotAuthorized(challenge=True)


def test_polkit_rule_authorizes_start_only_and_denial_is_never_success(host):
    proc = host.unprivileged_process()
    subject = ProcSubjectSource().subject_for_pid(proc.pid).value
    RULE_FILE.write_text(
        "polkit.addRule(function(action, subject) {\n"
        '  if (action.id == "org.freedesktop.systemd1.manage-units" &&\n'
        '      action.lookup("unit") == "rp11-capture-pass-a.service" &&\n'
        '      action.lookup("verb") == "start" && subject.user == "nobody") {\n'
        "    return polkit.Result.YES;\n  }\n});\n"
    )
    polkit = PolkitAuthorityAdapter(connect_system_bus)
    assert wait_until(
        lambda: polkit.check(subject, UnitVerb.START) == PolkitAuthorized(), timeout=10
    )
    stop = polkit.check(subject, UnitVerb.STOP)
    assert isinstance(stop, PolkitNotAuthorized) and not isinstance(stop, PolkitAuthorized)
    RULE_FILE.unlink()
    assert wait_until(
        lambda: polkit.check(subject, UnitVerb.START) == PolkitNotAuthorized(challenge=True),
        timeout=10,
    )


def test_polkit_root_subject_is_authorized_for_everything(host):
    # A-13.5: with flags 0 a uid-0 subject bypasses policy, so a root subject is
    # not evidence that a rule works. Pinned so nobody reads it as such.
    root = ProcSubjectSource().subject_for_pid(os.getpid()).value
    assert root.uid == 0
    polkit = PolkitAuthorityAdapter(connect_system_bus)
    assert polkit.check(root, UnitVerb.START) == PolkitAuthorized()
    assert polkit.check(root, UnitVerb.STOP) == PolkitAuthorized()


@pytest.mark.parametrize("shift", [1, -1])
def test_polkit_replaced_subject_is_an_error_not_a_decision(host, shift):
    proc = host.unprivileged_process()
    real = ProcSubjectSource().subject_for_pid(proc.pid).value
    forged = ProcessSubject(real.pid, real.start_time + shift, real.uid)
    outcome = PolkitAuthorityAdapter(connect_system_bus).check(forged, UnitVerb.START)
    assert isinstance(outcome, ControlError)
    assert outcome.kind.startswith("org.freedesktop.PolicyKit1.Error")


def test_polkit_gone_process_is_an_error(host):
    proc = host.unprivileged_process()
    subject = ProcSubjectSource().subject_for_pid(proc.pid).value
    proc.kill()
    proc.wait()
    outcome = PolkitAuthorityAdapter(connect_system_bus).check(subject, UnitVerb.START)
    assert isinstance(outcome, ControlError)


def test_subject_for_a_vanished_pid_is_an_error(host):
    proc = host.unprivileged_process()
    pid = proc.pid
    proc.kill()
    proc.wait()
    assert isinstance(ProcSubjectSource().subject_for_pid(pid), ControlError)


def test_polkit_survives_a_service_restart(host):
    proc = host.unprivileged_process()
    subject = ProcSubjectSource().subject_for_pid(proc.pid).value
    polkit = PolkitAuthorityAdapter(connect_system_bus)
    assert polkit.check(subject, UnitVerb.START) == PolkitNotAuthorized(challenge=True)
    run("systemctl", "restart", "polkit.service", check=True)
    outcome = polkit.check(subject, UnitVerb.START)
    # Either bus activation brought it back in time, or the call is an error —
    # never a decision made up from a dead authority.
    assert outcome == PolkitNotAuthorized(challenge=True) or isinstance(outcome, ControlError)
    assert wait_until(
        lambda: polkit.check(subject, UnitVerb.START) == PolkitNotAuthorized(challenge=True),
        timeout=15,
    )


def test_polkit_stopped_authority_is_reactivated_or_an_error(host):
    proc = host.unprivileged_process()
    subject = ProcSubjectSource().subject_for_pid(proc.pid).value
    run("systemctl", "stop", "polkit.service", check=True)
    outcome = PolkitAuthorityAdapter(connect_system_bus).check(subject, UnitVerb.START)
    assert outcome == PolkitNotAuthorized(challenge=True) or isinstance(outcome, ControlError)


# ============== failure injection: lost / late / malformed ==================


@pytest.mark.parametrize("mode", ["lost-reply", "timeout", "malformed"])
def test_uncertain_create_is_unconfirmed_not_retried_and_recoverable(host, mode):
    activation_id = host.activation_id()
    sent: list[str] = []
    result = faulty_adapter(mode, sent).create_holder(holder(activation_id))
    assert isinstance(result, ControlError) and result.effect_not_confirmed, result
    assert sent == ["StartTransientUnit"]  # sent exactly once, never retried
    unit = f"{activation_id}.service"
    created = wait_until(lambda: active_state(unit) == "active", timeout=3)
    if mode != "lost-reply":
        # The call really reached systemd; only the answer was withheld or mangled.
        assert created
    # When the reply is lost the effect is genuinely indeterminate (observed both
    # ways), which is exactly why the error says "not confirmed". Recovery is the
    # caller's explicit decision after looking, and each branch is safe:
    again = adapter().create_holder(holder(activation_id))
    if created:
        assert again == ControlRefused(RefusalReason.EXISTS)  # a blind retry cannot duplicate
    else:
        assert isinstance(again, ControlOk)  # nothing happened, so a deliberate re-issue works
        assert active_state(unit) == "active"


def test_suppressed_completion_signal_is_unconfirmed_and_not_promoted_by_a_state_read(host):
    activation_id = host.activation_id()
    sent: list[str] = []
    result = faulty_adapter("no-signal", sent, completion_seconds=1).create_holder(
        holder(activation_id)
    )
    assert isinstance(result, ControlError) and result.kind == "completion-timeout"
    assert result.effect_not_confirmed
    assert sent == ["StartTransientUnit"]
    assert wait_until(
        lambda: active_state(f"{activation_id}.service") == "active"
    )  # it did succeed


def test_partial_backstop_failure_is_cleaned_up_by_an_explicit_disarm(host):
    activation_id = host.activation_id()
    sent: list[str] = []
    result = faulty_adapter("timeout", sent).create_backstop(backstop(activation_id))
    assert isinstance(result, ControlError) and result.effect_not_confirmed
    assert sent == ["StartTransientUnit"]
    timer = f"{activation_id}-backstop.timer"
    assert wait_until(lambda: active_state(timer) == "active", timeout=10)
    stopped = adapter().disarm_backstop(activation_id)
    assert isinstance(stopped, ControlOk)
    assert active_state(timer) == "inactive"
    assert wait_until(lambda: host.owned_units() == [], timeout=15)


def test_lost_backstop_reply_is_recovered_whichever_way_the_effect_went(host):
    activation_id = host.activation_id()
    sent: list[str] = []
    result = faulty_adapter("lost-reply", sent).create_backstop(backstop(activation_id))
    assert isinstance(result, ControlError) and result.effect_not_confirmed
    timer = f"{activation_id}-backstop.timer"
    created = wait_until(lambda: active_state(timer) == "active", timeout=3)
    stopped = adapter().disarm_backstop(activation_id)
    if created:
        assert isinstance(stopped, ControlOk)
    else:
        assert stopped == ControlRefused(RefusalReason.NOT_LOADED)
    assert wait_until(lambda: host.owned_units() == [], timeout=15)


def test_real_completion_deadline_then_late_completion(host):
    host.start_capture("-p", "ExecStop=/usr/bin/sleep 4")
    result = adapter(completion_seconds=1).stop_capture_unit()
    assert isinstance(result, ControlError) and result.kind == "completion-timeout"
    assert result.effect_not_confirmed
    # The late completion changes nothing about the answer already given.
    assert wait_until(lambda: active_state(CAPTURE_UNIT) in {"inactive", "?"}, timeout=20)
    assert isinstance(result, ControlError)


def test_manager_reexec_during_a_stop_is_a_confirmed_stop_or_unconfirmed(host):
    host.start_capture("-p", "ExecStop=/usr/bin/sleep 5")
    out: dict = {}
    thread = threading.Thread(
        target=lambda: out.update(r=adapter(completion_seconds=20).stop_capture_unit())
    )
    thread.start()
    time.sleep(2)
    run("systemctl", "daemon-reexec", check=True)
    thread.join(timeout=40)
    result = out["r"]
    if isinstance(result, ControlOk):
        assert result.value.outcome is StopOutcome.STOPPED
    else:
        assert isinstance(result, ControlError) and result.effect_not_confirmed, result
    assert wait_until(lambda: active_state(CAPTURE_UNIT) in {"inactive", "?"}, timeout=20)
    # The adapter works against the restarted manager.
    assert isinstance(adapter().read_unit(CAPTURE_UNIT, (UnitProperty.ACTIVE_STATE,)), ControlOk)


def test_connection_failure_to_a_missing_bus_is_an_error(host, monkeypatch):
    def refuse():
        raise BusDisconnected("no bus")

    result = SystemdManagerAdapter(refuse).stop_capture_unit()
    assert isinstance(result, ControlError) and result.kind == "connect-failed"
    assert not result.effect_not_confirmed  # nothing was sent


# ============== raw proofs for the refusal classifications ===================


def _raw(member, signature, body, interface="org.freedesktop.systemd1.Manager"):
    conn = connect_system_bus()
    try:
        return conn.call(
            BusRequest(
                "org.freedesktop.systemd1",
                "/org/freedesktop/systemd1",
                interface,
                member,
                signature,
                body,
            ),
            timeout=5,
        )
    finally:
        conn.close()


def test_stop_invalid_mode_and_bad_name_are_invalid_args_with_no_job(host):
    from adapters.systemd.bus import BusError

    for body in (("rp11-capture-pass-a.service", "bogus"), ("bad name!", "fail")):
        with pytest.raises(BusError) as info:
            _raw("StopUnit", "ss", body)
        assert info.value.name == "org.freedesktop.DBus.Error.InvalidArgs"
    assert loaded_units(CAPTURE_UNIT) == [] or active_state(CAPTURE_UNIT) == "inactive"


def test_create_with_bad_mode_or_property_creates_nothing(host):
    from adapters.systemd.bus import BusError

    activation_id = host.activation_id()
    unit = f"{activation_id}.service"
    with pytest.raises(BusError) as info:
        _raw(
            "StartTransientUnit",
            "ssa(sv)a(sa(sv))",
            (unit, "bogus", [("Type", Variant("s", "exec"))], []),
        )
    assert info.value.name == "org.freedesktop.DBus.Error.InvalidArgs"
    with pytest.raises(BusError) as info:
        _raw(
            "StartTransientUnit",
            "ssa(sv)a(sa(sv))",
            (unit, "fail", [("Type", Variant("s", "exec")), ("NoSuchProp", Variant("s", "x"))], []),
        )
    assert info.value.name == "org.freedesktop.DBus.Error.PropertyReadOnly"
    # Observed: nothing runs and no job exists. (A-05.12 says a jobless transient
    # stub is possible, which is why the adapter still reports these as errors.)
    assert active_state(unit) == "inactive"


def test_unit_object_path_matches_what_the_manager_serves(host):
    reply = _raw("GetUnit", "s", ("init.scope",))
    assert reply.body[0] == unit_object_path("init.scope")


# ============== the exact -I -S role runtime (remediation finding 2) ========


def _vector(role: str, activation_id: str) -> tuple[str, ...]:
    command = manager_module._role_command(manager_module._Role(role), activation_id, A2)
    manager_module._check_role_command(command, manager_module._Role(role))
    assert command.path == command.argv[0] == ROLE_INTERPRETER
    return command.argv


@pytest.fixture
def production_roles():
    install_artifact("production")
    yield
    install_artifact("double")


@pytest.mark.parametrize("role", ["hold", "stop-post", "backstop"])
def test_exact_role_vector_runs_isolated_and_imports_the_vendored_client(production_roles, role):
    """The adapter's own vector, executed as is: the interpreter starts with -I -S,
    the artifact finds its lib/ itself, the adapter and jeepney import, and each
    role fails closed without activation state. Nothing from the venv is reachable."""
    activation_id = f"rp11-act-20261012T101500Z-{secrets.token_hex(4)}"
    argv = _vector(role, activation_id)
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, env={}, cwd="/")
    finally:
        _remove_cleanup_evidence(activation_id)
    assert "runtime=ok python=3.14." in proc.stderr
    assert "isolated=1 no_site=1 jeepney=0.9.0" in proc.stderr
    assert "Traceback" not in proc.stderr
    if role == "stop-post":
        # The real cleanup runs (role slice 1). With no activation state and no
        # record store there is nothing to attribute and nowhere to record: it
        # fails closed (tests/systemd_integration/test_route3_stop_post_host.py).
        assert proc.returncode == 3, proc.stderr
        assert f"rp11-cl record-unpublished {activation_id} k=1" in proc.stderr
    elif role == "backstop":
        # The real backstop runs (role slice 2): the holder is not loaded, there is
        # no record and no store, so BS-4 runs CL unlocked, which fails closed
        # (tests/systemd_integration/test_route3_backstop_host.py).
        assert proc.returncode == 3, proc.stderr
        assert f"rp11-bs cleanup {activation_id} k=1 trigger=backstop lock=unavailable" in proc.stderr
        assert f"rp11-cl record-unpublished {activation_id} k=1" in proc.stderr
    else:
        # The real holder runs (role slice 3): there is no A-2 file, so AM-0
        # refuses before any state exists (tests/systemd_integration/test_route3_hold_host.py).
        assert proc.returncode == 20, proc.stderr
        assert f"rp11-hold invalid-authority {activation_id} step=AM-0" in proc.stderr


def test_exact_runtime_cannot_see_site_packages(production_roles):
    probe = (
        f"import sys; sys.path.append({str(ARTIFACT_LIB)!r});"
        "import jeepney, adapters.systemd.manager as m;"
        "print(jeepney.__file__); print(m.__file__);"
        "print(sys.flags.isolated, sys.flags.no_site);"
        "print(any('site-packages' in p or 'dist-packages' in p for p in sys.path))"
    )
    proc = subprocess.run(
        [ROLE_INTERPRETER, "-I", "-S", "-B", "-c", probe], capture_output=True, text=True, env={}
    )
    assert proc.returncode == 0, proc.stderr
    jeepney_file, adapter_file, flags, site = proc.stdout.split("\n")[:4]
    assert jeepney_file.startswith(str(ARTIFACT_LIB / "jeepney"))
    assert adapter_file == str(ARTIFACT_LIB / "adapters/systemd/manager.py")
    assert flags == "1 1" and site == "False"


def test_artifact_refuses_to_run_as_root_when_not_root_owned(production_roles):
    os.chown(ARTIFACT_LIB, NOBODY, NOBODY)
    try:
        argv = _vector("hold", f"rp11-act-20261012T101500Z-{secrets.token_hex(4)}")
        proc = subprocess.run(argv, capture_output=True, text=True, env={})
        assert proc.returncode == 77 and "not root-owned" in proc.stderr
    finally:
        os.chown(ARTIFACT_LIB, 0, 0)


# ======= unsafe artifact trees as root (security remediation finding 1) ======
#
# Each case plants a module whose top-level code writes MARKER, makes one object
# unsafe, and runs the adapter's exact vector as root. A refusal must be 77 with
# the marker absent: no unsafe module code ran.

UBUNTU = int(os.environ.get("SUDO_UID") or 1000)
MARKER = Path("/run/rp11-evil-marker")
ELSEWHERE = Path("/run/rp11-evil-elsewhere")
REAL_DIR = ARTIFACT_DIR.parent / "rp11-real-artifact"
EVIL_SOURCE = (
    f"open({str(MARKER)!r}, 'w').write('ran')\n"
    "def run(role, activation_id, artifact_sha256, **provenance):\n    return 69\n"
)


def _discard_mutations() -> None:
    MARKER.unlink(missing_ok=True)
    shutil.rmtree(ELSEWHERE, ignore_errors=True)
    if REAL_DIR.exists():
        shutil.rmtree(REAL_DIR)
    os.chmod(ARTIFACT_DIR.parent, 0o755)
    os.chown(ARTIFACT_DIR.parent, 0, 0)
    remove_artifact()  # the next fixture rebuilds whatever it needs


@pytest.fixture
def mutable_artifact():
    """A fresh production build that the test may damage; discarded afterwards."""
    _discard_mutations()
    install_artifact("production")
    ELSEWHERE.mkdir(mode=0o755)
    yield
    _discard_mutations()
    install_artifact("double")


def _plant(rel: str, *, uid: int = 0, mode: int = 0o644) -> Path:
    path = ARTIFACT_DIR / rel
    path.write_text(EVIL_SOURCE)
    os.chown(path, uid, uid)
    os.chmod(path, mode)
    return path


def _run_hold() -> subprocess.CompletedProcess:
    argv = _vector("hold", f"rp11-act-20261012T101500Z-{secrets.token_hex(4)}")
    return subprocess.run(argv, capture_output=True, text=True, env={}, cwd="/")


def _assert_refused_before_any_artifact_code(proc: subprocess.CompletedProcess) -> None:
    assert proc.returncode == 77, (proc.returncode, proc.stderr)
    assert "not root-owned and protected" in proc.stderr
    assert "Traceback" not in proc.stderr and "runtime=ok" not in proc.stderr
    assert not MARKER.exists(), "unsafe module top-level code executed"


def _symlink_roles():
    target = ELSEWHERE / "rp11_roles.py"
    target.write_text(EVIL_SOURCE)
    (ARTIFACT_LIB / "rp11_roles.py").unlink()
    (ARTIFACT_LIB / "rp11_roles.py").symlink_to(target)


def _symlink_adapters_dir():
    copy = ELSEWHERE / "adapters"
    shutil.copytree(ARTIFACT_LIB / "adapters", copy)
    (copy / "systemd/manager.py").write_text(EVIL_SOURCE)
    shutil.rmtree(ARTIFACT_LIB / "adapters")
    (ARTIFACT_LIB / "adapters").symlink_to(copy)


def _writable_nested_dir():
    _plant("lib/jeepney/io/blocking.py")
    os.chmod(ARTIFACT_LIB / "jeepney/io", 0o757)


def _group_writable_dir():
    _plant("lib/application/unit_control.py")
    os.chmod(ARTIFACT_LIB / "application", 0o775)


def _user_owned_dir():
    _plant("lib/jeepney/__init__.py")
    os.chown(ARTIFACT_LIB / "jeepney", UBUNTU, UBUNTU)


def _user_owned_metadata():
    _plant("lib/rp11_roles.py")
    os.chown(ARTIFACT_LIB / "jeepney-0.9.0.dist-info/METADATA", UBUNTU, UBUNTU)


@pytest.mark.parametrize(
    "damage",
    [
        # the reviewed reproduction: only the role module, user-owned, dirs intact
        pytest.param(lambda: _plant("lib/rp11_roles.py", uid=UBUNTU), id="roles-user-0644"),
        pytest.param(
            lambda: _plant("lib/rp11_roles.py", uid=UBUNTU, mode=0o444), id="roles-user-0444"
        ),
        pytest.param(
            lambda: _plant("lib/adapters/systemd/polkit.py", uid=UBUNTU), id="adapter-user"
        ),
        pytest.param(lambda: _plant("lib/jeepney/__init__.py", uid=UBUNTU), id="jeepney-user"),
        pytest.param(
            lambda: _plant("lib/application/unit_control.py", mode=0o664), id="boundary-g+w"
        ),
        pytest.param(lambda: _plant("lib/jeepney/io/blocking.py", mode=0o646), id="jeepney-o+w"),
        pytest.param(_writable_nested_dir, id="nested-dir-o+w"),
        pytest.param(_group_writable_dir, id="dir-g+w"),
        pytest.param(_user_owned_dir, id="dir-user"),
        pytest.param(_user_owned_metadata, id="dist-info-user"),
        pytest.param(_symlink_roles, id="symlinked-module"),
        pytest.param(_symlink_adapters_dir, id="symlinked-package"),
    ],
)
def test_an_unsafe_artifact_tree_is_refused_as_root_before_import(mutable_artifact, damage):
    damage()
    _assert_refused_before_any_artifact_code(_run_hold())


def test_the_marker_control_root_owned_protected_code_does_run(mutable_artifact):
    """Without this, an absent marker would prove nothing."""
    _plant("lib/rp11_roles.py")  # root:root 0644: a legitimate (if odd) build
    proc = _run_hold()
    assert proc.returncode == 69 and "runtime=ok" in proc.stderr, proc.stderr
    assert MARKER.read_text() == "ran"
    assert not list(ARTIFACT_DIR.rglob("__pycache__"))  # the entry writes no bytecode


def _writable_artifact_dir():
    _plant("lib/rp11_roles.py")
    os.chmod(ARTIFACT_DIR, 0o777)


def _writable_install_parent():
    _plant("lib/rp11_roles.py")
    os.chmod(ARTIFACT_DIR.parent, 0o777)


def _symlinked_artifact_dir():
    _plant("lib/rp11_roles.py")
    os.rename(ARTIFACT_DIR, REAL_DIR)
    ARTIFACT_DIR.symlink_to(REAL_DIR)


def _user_owned_entry_point():
    os.chown(ROLE_ARTIFACT, UBUNTU, UBUNTU)


@pytest.mark.parametrize(
    "damage",
    [
        pytest.param(_writable_artifact_dir, id="artifact-dir-o+w"),
        pytest.param(_writable_install_parent, id="libexec-o+w"),
        pytest.param(_symlinked_artifact_dir, id="artifact-dir-symlink"),
        pytest.param(_user_owned_entry_point, id="entry-point-user"),
    ],
)
def test_an_unsafe_entry_point_path_is_refused_by_the_adapter_before_the_bus(
    host, mutable_artifact, damage
):
    """The independent pre-execution invariant: the entry point cannot vouch for
    itself, so the adapter refuses to have PID 1 run it, and no unit exists."""
    damage()
    activation_id = host.activation_id()
    for result in (
        adapter().create_holder(holder(activation_id)),
        adapter().create_backstop(backstop(activation_id)),
    ):
        assert isinstance(result, ControlError) and result.kind == "unsafe-artifact", result
        assert not result.effect_not_confirmed
    assert host.owned_units() == []
    # The (unmodified) entry point's own check agrees; it is not what is relied on.
    _assert_refused_before_any_artifact_code(_run_hold())


def test_a_fresh_install_satisfies_both_checks(mutable_artifact):
    assert manager_module._role_runtime_problem() is None
    for path in [ARTIFACT_DIR, *ARTIFACT_DIR.rglob("*")]:
        info = path.lstat()
        assert info.st_uid == 0 and info.st_gid == 0, path
        assert (info.st_mode & 0o7777) == (0o755 if path.is_dir() else 0o644), path


def test_the_builder_refuses_an_install_parent_others_can_change(mutable_artifact):
    parent = ELSEWHERE / "open"
    parent.mkdir(mode=0o777)
    os.chmod(parent, 0o777)
    builder = _load_builder()
    with pytest.raises(builder.BuildError):
        builder.build(Path(os.environ["FREEDOM_RP11_WHEEL"]), parent / "artifact")
    assert list(parent.iterdir()) == []


def test_artifact_rejects_a_vector_the_adapter_would_never_build(production_roles):
    for tail in (["hold"], ["deact", "x", A2, "stop-post"], ["backstop", "a", A2, "extra"]):
        proc = subprocess.run(
            [ROLE_INTERPRETER, "-I", "-S", ROLE_ARTIFACT, *tail], capture_output=True, text=True
        )
        assert proc.returncode == 64, (tail, proc.stderr)


def test_pid1_executes_the_exact_holder_and_stop_post_vectors(host, production_roles):
    activation_id = host.activation_id()
    unit = f"{activation_id}.service"
    result = adapter().create_holder(holder(activation_id))
    assert isinstance(result, ControlOk), result  # exec of the interpreter succeeded
    # The production holder finds no A-2 here and ends 20 at AM-0; PID 1 then
    # runs ExecStopPost: the real cleanup, which finds no activation state and
    # no record store here and fails closed with record-unpublished (3).
    assert wait_until(lambda: active_state(unit) == "failed", timeout=20)
    shown = show(unit, "ExecMainStatus", "ExecStopPost", "InvocationID")
    assert shown["ExecMainStatus"] == "20"
    assert f"{ROLE_ARTIFACT} deact {activation_id} {A2} stop-post ;" in shown["ExecStopPost"]
    assert "code=exited ; status=3 }" in shown["ExecStopPost"]
    journal = run(
        "journalctl", "--no-pager", "-o", "cat", f"_SYSTEMD_INVOCATION_ID={shown['InvocationID']}"
    ).stdout
    assert "rp11_h1: role=hold runtime=ok python=3.14." in journal
    assert "rp11_h1: role=stop-post runtime=ok" in journal
    assert "isolated=1 no_site=1 jeepney=0.9.0" in journal


def test_pid1_executes_the_exact_backstop_vector(host, production_roles):
    activation_id = host.activation_id()
    result = adapter().create_backstop(backstop(activation_id))
    assert isinstance(result, ControlOk), result
    service = f"{activation_id}-backstop.service"
    run("systemctl", "start", service)  # fire it now rather than wait for R
    try:
        assert wait_until(lambda: active_state(service) == "failed", timeout=30)
        shown = show(service, "ExecMainStatus", "InvocationID")
        # The real backstop: no holder, record or store, so CL runs and fails closed.
        assert shown["ExecMainStatus"] == "3"
        journal = run(
            "journalctl", "--no-pager", "-o", "cat", f"_SYSTEMD_INVOCATION_ID={shown['InvocationID']}"
        ).stdout
        assert "rp11_h1: role=backstop runtime=ok python=3.14." in journal
        assert f"rp11-bs cleanup {activation_id} k=1 trigger=backstop" in journal
        assert isinstance(adapter().disarm_backstop(activation_id), ControlOk)
    finally:
        _remove_cleanup_evidence(activation_id)


# ===== first image: no inherited descriptor survives (H-FI.3 review finding) =====
#
# PID 1 itself passes no descriptor to a holder, so a transient root unit's main
# process opens 70,000 and 2**20+7 (above the former min(SC_OPEN_MAX, 2**20)
# bound), optionally lowers its soft limit below both, and then exec's the exact
# ``hold`` vector in place: the holder is the same PID and inherits both. The
# double role keeps it running so its descriptor table can be read live. The
# running holder legitimately holds descriptors it opened itself after the first
# image's controls (``ctypes`` keeps ``libffi`` open, ``O_CLOEXEC``), so its table
# is compared with a control holder that inherited nothing.

_FI_HIGH = (70_000, (1 << 20) + 7)
_FI_WRAPPER = """
import json, os, resource, sys
case, vector = sys.argv[1], sys.argv[2:]
numbers = (70_000, (1 << 20) + 7) if case != "none" else ()
if numbers:
    resource.setrlimit(resource.RLIMIT_NOFILE, (numbers[-1] + 1, numbers[-1] + 1))
for number in numbers:
    source = os.open("/dev/null", os.O_RDONLY)
    os.dup2(source, number, inheritable=True)
    os.close(source)
if case == "lowered-below":
    resource.setrlimit(resource.RLIMIT_NOFILE, (1_024, numbers[-1] + 1))
listed = [int(name) for name in os.listdir("/proc/self/fd")]
print(json.dumps({"before": [n for n in numbers if n in listed],
                  "limit": list(resource.getrlimit(resource.RLIMIT_NOFILE))}), file=sys.stderr, flush=True)
os.execv(vector[0], vector)
"""


def _running_holder_descriptors(case: str) -> tuple[dict, dict[int, tuple[str, int]]]:
    """``(wrapper facts, {fd >= 3: (target, flags)})`` of a live double holder."""
    activation_id = f"rp11-act-20261012T101500Z-{secrets.token_hex(4)}"
    unit = f"rp11-fi-probe-{secrets.token_hex(4)}"
    log = Path(f"/run/{unit}.log")
    started = run(
        "systemd-run", f"--unit={unit}", "--service-type=exec", "--collect", "--quiet",
        "-p", "User=root", "-p", f"StandardError=append:{log}",
        ROLE_INTERPRETER, "-I", "-S", "-B", "-c", _FI_WRAPPER, case, *_vector("hold", activation_id),
    )
    try:
        assert started.returncode == 0, started.stderr
        assert wait_until(lambda: log.exists() and "test double role=hold" in log.read_text(), timeout=30), (
            log.read_text() if log.exists() else "no log"
        )
        pid = show(f"{unit}.service", "MainPID")["MainPID"]
        assert b"rp11_h1.py" in Path(f"/proc/{pid}/cmdline").read_bytes()
        facts = json.loads(log.read_text().splitlines()[0])
        table = {}
        for name in os.listdir(f"/proc/{pid}/fd"):
            if int(name) >= 3:
                info = Path(f"/proc/{pid}/fdinfo/{name}").read_text()
                flags = int(next(l for l in info.splitlines() if l.startswith("flags:")).split()[1], 8)
                table[int(name)] = (os.readlink(f"/proc/{pid}/fd/{name}"), flags)
        return facts, table
    finally:
        run("systemctl", "stop", f"{unit}.service")
        log.unlink(missing_ok=True)
        assert run("systemctl", "is-active", f"{unit}.service").stdout.strip() != "active"


@pytest.mark.parametrize("case", ["raised", "lowered-below"])
def test_the_first_image_closes_inherited_descriptors_above_any_limit_under_pid1(case):
    assert int(Path("/proc/sys/fs/nr_open").read_text()) > _FI_HIGH[-1] + 1
    control_facts, control = _running_holder_descriptors("none")
    facts, table = _running_holder_descriptors(case)
    assert control_facts["before"] == [] and facts["before"] == list(_FI_HIGH), facts
    assert facts["limit"][0] == (1_024 if case == "lowered-below" else _FI_HIGH[-1] + 1), facts
    assert not set(_FI_HIGH) & set(table), table
    assert table == control, (table, control)  # only what the image opened itself
    assert all(flags & os.O_CLOEXEC and target != "/dev/null" for target, flags in table.values()), table
