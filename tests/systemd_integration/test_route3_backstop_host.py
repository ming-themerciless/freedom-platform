"""RT-4 ``backstop`` through PID 1 on the disposable host.

Real systemd, real Polkit, real ``/run``, ``/var/tmp`` and
``/var/lib/freedom-blades-rp11``, and the production artifact built fresh from
the hash-pinned wheel. Every firing is ``<id>-backstop.service``, created with
its timer by the accepted adapter (DI-3), running the exact
``backstop <id> <a2>`` vector; the holder, where one exists, is created by DI-2
(its real ``hold`` stops at AM-0 because the activation is already built, so
PID 1 then runs the real ``stop-post``).
Synthetic activations only.

    sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test \\
        FREEDOM_RP11_WHEEL=/path/to/jeepney-0.9.0-py3-none-any.whl \\
        /opt/freedom-blades/runtime/venv-web/bin/python -m pytest -q -rfEs \\
        tests/systemd_integration/test_route3_backstop_host.py
"""

from __future__ import annotations

import json
import os
import pwd
import shutil
import subprocess
import sys
import time
import secrets
from datetime import UTC, datetime
from pathlib import Path

import pytest

if os.environ.get("FREEDOM_SYSTEMD_INTEGRATION") != "oracle-test":
    pytest.skip("set FREEDOM_SYSTEMD_INTEGRATION=oracle-test (disposable host only)", allow_module_level=True)
import socket  # noqa: E402

if socket.gethostname() != "Test":
    pytest.skip("refusing to run: not the disposable host (hostname != Test)", allow_module_level=True)
if os.geteuid() != 0 or not Path("/run/systemd/system").is_dir():
    pytest.skip("needs root on a systemd host", allow_module_level=True)
pytest.importorskip("jeepney")

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import importlib.util  # noqa: E402

from adapters.rp11.baseline import HostBaseline  # noqa: E402
from adapters.rp11.process import SystemClock  # noqa: E402
from adapters.rp11.stop_post import StopPostServices  # noqa: E402
from adapters.systemd.jeepney_bus import connect_system_bus  # noqa: E402
from adapters.systemd.manager import ROLE_ARTIFACT, ROLE_INTERPRETER, SystemdManagerAdapter  # noqa: E402
from application.rp11.authority import Operator, Params  # noqa: E402
from application.rp11.canonical import parse_canonical  # noqa: E402
from application.rp11.paths import ActivationPaths, Layout  # noqa: E402
from application.rp11.pk import PkMode, PkOutcome  # noqa: E402
from application.rp11.records import validate_record  # noqa: E402
from application.unit_control import BackstopSpec, ControlOk, HolderSpec, UnitVerb  # noqa: E402
from rp11_fixtures import RULE_BYTES, ActivationFixture  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = Path(ROLE_ARTIFACT).parent
STORE = Path("/var/lib/freedom-blades-rp11")
FOREIGN_RULE = Path("/etc/polkit-1/rules.d/49-rp11-backstop-test.rules")
LAYOUT = Layout()
OPERATOR = pwd.getpwnam("ubuntu")
SLEEP = os.path.realpath("/usr/bin/sleep")


def params(backstop_max: int = 20) -> Params:
    return Params(pk_op_ms=5_000, pk_call_ms=2_000, reap_grace_ms=2_000, lock_wait_ms=1_000, backstop_max=backstop_max)


def run(*argv: str, check: bool = False, timeout: float = 120) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True, check=check, timeout=timeout)


def show(unit: str, *props: str) -> dict[str, str]:
    out = run("systemctl", "show", unit, *(f"-p{p}" for p in props)).stdout
    return dict(line.split("=", 1) for line in out.splitlines() if "=" in line)


def wait_until(predicate, timeout=30.0, interval=0.1) -> bool:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()


def restart_polkit() -> None:
    # The suite deliberately restarts Polkit often enough that repeated runs can
    # trip systemd's start-rate limiter. Reset only this disposable service's
    # counter so fixture setup remains repeatable.
    run("systemctl", "reset-failed", "polkit.service", check=True)
    run("systemctl", "restart", "polkit.service", check=True)
    assert wait_until(lambda: run("systemctl", "is-active", "polkit.service").stdout.strip() == "active")


def rp11_processes() -> list[str]:
    found = []
    for entry in Path("/proc").iterdir():
        if entry.name.isdigit() and int(entry.name) != os.getpid():
            try:
                cmdline = (entry / "cmdline").read_bytes()
            except OSError:
                continue
            if b"rp11_h1.py" in cmdline:
                found.append(entry.name)
    return found


def journal_cursor() -> str:
    out = run("journalctl", "--no-pager", "-n", "0", "--show-cursor").stdout
    return out.strip().rsplit("-- cursor: ", 1)[1]


def exit_status(journal: str) -> str | None:
    """The firing's exit status from PID 1's own messages; ``None`` until it ended."""
    for line in journal.splitlines():
        if "Main process exited, code=exited, status=" in line:
            return line.split("status=", 1)[1].split("/", 1)[0]
        if "Main process exited, code=killed, status=" in line:
            return "killed:" + line.split("status=", 1)[1].split("/", 1)[0]
    if "Deactivated successfully." in journal:
        return "0"
    if "Failed with result '" in journal:  # e.g. SIGTERM at RuntimeMaxSec, logged as a clean stop
        return "failed:" + journal.split("Failed with result '", 1)[1].split("'", 1)[0]
    return None


def unit_span_seconds(unit: str) -> float | None:
    """PID 1's own timing of the last firing: from its ``Started`` message to its
    ``Failed with result`` message, by the journal's monotonic timestamps."""
    out = run("journalctl", "--no-pager", "-o", "json", "-u", unit).stdout
    started = ended = None
    for line in out.splitlines():
        entry = json.loads(line)
        message = entry.get("MESSAGE")
        if not isinstance(message, str):
            continue
        stamp = int(entry["__MONOTONIC_TIMESTAMP"])
        if message.startswith("Started "):
            started, ended = stamp, None
        elif "Failed with result" in message and started is not None:
            ended = stamp
    if started is None or ended is None:
        return None
    return (ended - started) / 1e6


def adapter() -> SystemdManagerAdapter:
    return SystemdManagerAdapter(connect_system_bus)


# --- the production artifact, built fresh -----------------------------------------


def _builder():
    spec = importlib.util.spec_from_file_location("rp11_backstop_build", ROOT / "infra/rp11-h1/build.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module", autouse=True)
def artifact():
    wheel = os.environ.get("FREEDOM_RP11_WHEEL")
    assert wheel, "set FREEDOM_RP11_WHEEL"
    shutil.rmtree(ARTIFACT_DIR, ignore_errors=True)
    _builder().build(Path(wheel), ARTIFACT_DIR)
    for path in [ARTIFACT_DIR, *ARTIFACT_DIR.rglob("*")]:
        info = path.lstat()
        assert (info.st_uid, info.st_gid) == (0, 0) and not info.st_mode & 0o022, path
    yield
    shutil.rmtree(ARTIFACT_DIR, ignore_errors=True)
    assert not ARTIFACT_DIR.exists()


# --- one synthetic activation per test ----------------------------------------------


class Activation:
    def __init__(self) -> None:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        self.id = f"rp11-act-{stamp}-{secrets.token_hex(4)}"
        self.paths = ActivationPaths(LAYOUT, self.id)
        self.fx: ActivationFixture | None = None
        self.params = params()
        self.made_polkit_dir = False  # a test that pre-creates /run/polkit-1 removes it

    @property
    def holder(self) -> str:
        return f"{self.id}.service"

    @property
    def timer(self) -> str:
        return f"{self.id}-backstop.timer"

    @property
    def service(self) -> str:
        return f"{self.id}-backstop.service"

    def prepare(self, *, backstop_max: int = 20, pass_config: bool = True) -> None:
        self.params = params(backstop_max)
        for sub in ("", "a2", "h1", "activation"):
            (STORE / sub).mkdir(mode=0o755, exist_ok=True)
            os.chmod(STORE / sub, 0o755)
        services = StopPostServices(connect_system_bus, SystemClock())
        baseline = HostBaseline(services.units(self.params)).recompute()
        assert baseline is not None
        self.fx = ActivationFixture(LAYOUT, self.id, Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
                                    baseline, params=self.params)
        self.fx.rules_dir_preexists = os.path.isdir(self.paths.rules_dir)
        self.fx.write_authority()
        self.fx.activate(act_dir_uid=OPERATOR.pw_uid, pass_config=pass_config)
        restart_polkit()
        assert self.pk(PkMode.SEEK_AUTHORIZED).outcome is PkOutcome.AUTHORIZED  # the grant is live

    def pk(self, mode: PkMode):
        services = StopPostServices(connect_system_bus, SystemClock())
        return services.pk(self.params).run(Operator.from_baseline(self.fx.baseline), UnitVerb.START, mode)

    def arm(self, *, interval: int = 600, runtime_max: int = 120, timeout_stop: int = 20) -> None:
        spec = BackstopSpec(self.id, self.fx.a2_sha256, interval, runtime_max, timeout_stop)
        result = adapter().create_backstop(spec)
        assert isinstance(result, ControlOk), result

    def start_holder(self) -> dict[str, str]:
        spec = HolderSpec(activation_id=self.id, artifact_sha256=self.fx.a2_sha256,
                          runtime_max_seconds=900, timeout_stop_seconds=120)
        assert isinstance(adapter().create_holder(spec), ControlOk)
        assert wait_until(lambda: show(self.holder, "ActiveState")["ActiveState"] in {"failed", "inactive"}, 60)
        return show(self.holder, "ExecStopPost")

    def fire(self, timeout: float = 120) -> dict[str, str]:
        """One backstop firing through PID 1, waited for to its end.

        A firing that disarms its own timer leaves a transient service PID 1 may
        collect at once, so the firing is read from the journal by unit name after
        a cursor taken before the start, not from ``systemctl show``."""
        cursor = journal_cursor()
        run("systemctl", "start", "--wait", self.service, timeout=timeout)
        shown = show(self.service, "ExecMainStatus", "ExecMainCode", "InvocationID", "Result", "ActiveState")
        shown["journal"] = self.unit_journal(cursor)
        shown["status"] = exit_status(shown["journal"])
        assert "Traceback" not in shown["journal"], shown["journal"]
        return shown

    def unit_journal(self, cursor: str) -> str:
        assert wait_until(lambda: exit_status(self._journal_after(cursor)) is not None, 15)
        return self._journal_after(cursor)

    def _journal_after(self, cursor: str) -> str:
        return run("journalctl", "--no-pager", "-o", "cat", "-u", self.service, f"--after-cursor={cursor}").stdout

    def journal_text(self, invocation_id: str) -> str:
        return run("journalctl", "--no-pager", "-o", "cat", f"_SYSTEMD_INVOCATION_ID={invocation_id}").stdout

    def timer_state(self) -> str:
        return show(self.timer, "ActiveState").get("ActiveState", "")

    def record(self, k: int) -> dict:
        path = STORE / "activation" / f"{self.id}.deact-{k}.json"
        info = path.lstat()
        assert (info.st_uid, info.st_gid, info.st_mode & 0o7777, info.st_nlink) == (0, 0, 0o444, 1)
        doc = parse_canonical(path.read_bytes())
        validate_record(doc)
        return doc

    def attempts(self) -> list[str]:
        return sorted(p.name for p in Path("/var/tmp").glob(f"{self.id}-deact-*"))

    def attempt_ops(self, k: int) -> list[str]:
        journal = Path(self.paths.attempt_dir(k)) / "journal"
        return [json.loads(line)["op"] for line in journal.read_bytes().splitlines() if line.endswith(b"}")]

    def terminal_lines(self) -> list[dict]:
        path = STORE / "backstop" / f"{self.id}.journal"
        if not path.exists():
            return []
        info = path.lstat()
        assert (info.st_uid, info.st_mode & 0o7777, info.st_nlink) == (0, 0o644, 1)
        return [json.loads(line) for line in path.read_bytes().splitlines()]

    def clean(self) -> None:
        names = [self.holder, self.timer, self.service]
        run("systemctl", "stop", *names)
        run("systemctl", "reset-failed", *names)
        for path in (self.paths.tree_p, self.paths.lock_dir):
            shutil.rmtree(path, ignore_errors=True)
        if (self.fx is not None and not self.fx.rules_dir_preexists) or self.made_polkit_dir:
            shutil.rmtree(self.paths.polkit_run_dir, ignore_errors=True)
        else:
            Path(self.paths.rule).unlink(missing_ok=True)
        for entry in Path("/var/tmp").glob(f"{self.id}-*"):
            shutil.rmtree(entry, ignore_errors=True)
        for temp in Path("/run").glob(f".rp11-{self.id}-*"):
            shutil.rmtree(temp, ignore_errors=True)


@pytest.fixture
def activations():
    assert not STORE.exists(), "record store left from an earlier run"
    polkit_preexisted = os.path.lexists("/run/polkit-1")
    made: list[Activation] = []

    def new() -> Activation:
        act = Activation()
        made.append(act)
        return act

    yield new
    for act in made:
        act.clean()
    FOREIGN_RULE.unlink(missing_ok=True)
    shutil.rmtree(STORE, ignore_errors=True)
    restart_polkit()
    assert wait_until(lambda: rp11_processes() == [], 15), rp11_processes()
    for act in made:
        assert run("systemctl", "list-units", f"{act.id}*", "--all", "--no-legend").stdout.strip() == ""
        assert not list(Path("/var/tmp").glob(f"{act.id}-*"))
        assert not os.path.lexists(act.paths.tree_p) and not os.path.lexists(act.paths.lock_dir)
    assert not os.path.lexists("/run/polkit-1") or polkit_preexisted
    assert not STORE.exists() and not FOREIGN_RULE.exists()
    assert run("systemctl", "is-active", "polkit.service").stdout.strip() == "active"


@pytest.fixture
def activation(activations):
    return activations()


# ---------------------------------------------------------------------------
# BS-1
# ---------------------------------------------------------------------------


def test_bs1_an_active_holder_owns_the_activation(activation):
    activation.prepare()
    run("systemd-run", "--quiet", f"--unit={activation.holder}", "-p", "Type=exec", SLEEP, "600", check=True)
    activation.arm()
    shown = activation.fire()
    assert shown["status"] == "0", shown
    assert f"rp11-bs holder-active {activation.id} state=active" in shown["journal"]
    assert os.path.exists(activation.paths.rule) and activation.attempts() == []
    assert not (STORE / "backstop").exists() and activation.timer_state() == "active"
    assert show(activation.holder, "ActiveState")["ActiveState"] == "active"  # never stopped by BS


def test_bs1_a_holder_that_never_existed_continues_to_cleanup(activation):
    activation.prepare()
    activation.arm()
    shown = activation.fire()
    assert shown["status"] == "0", shown["journal"]
    assert f"rp11-bs cleanup {activation.id} k=1 trigger=backstop lock=held terminal=st1-verified" in shown["journal"]
    doc = activation.record(1)
    assert doc["trigger"] == "backstop" and doc["holder"]["active_state_at_start"] == "inactive"
    assert doc["release"]["first_rung"] == "cl-g" and doc["pk"]["outcome"] == "not-authorized"
    assert activation.attempt_ops(1)[:2] == ["run-start", "cl-g"]
    assert activation.pk(PkMode.FIRST_DECISIVE).outcome is PkOutcome.NOT_AUTHORIZED
    # BS-2 on the next firing
    shown = activation.fire()
    assert shown["status"] == "0" and f"rp11-bs disarmed {activation.id} branch=bs-2 k=1 disarm=stopped" in shown["journal"]
    assert wait_until(lambda: activation.timer_state() in {"inactive", ""}, 10)


# ---------------------------------------------------------------------------
# BS-2 / BS-3
# ---------------------------------------------------------------------------


def test_bs2_disarms_only_its_own_timer_after_a_verified_stop_post(activations):
    act, other = activations(), activations()
    act.prepare()
    shown = act.start_holder()
    assert "status=0 }" in shown["ExecStopPost"]  # RT-3 st1-verified, record 1
    act.arm()
    other.fx = act.fx  # the other activation only needs a timer of its own
    assert isinstance(adapter().create_backstop(BackstopSpec(other.id, act.fx.a2_sha256, 600, 120, 20)), ControlOk)
    before = act.attempts(), sorted(p.name for p in (STORE / "activation").iterdir())
    fired = act.fire()
    assert fired["status"] == "0"
    assert f"rp11-bs disarmed {act.id} branch=bs-2 k=1 disarm=stopped" in fired["journal"]
    assert wait_until(lambda: act.timer_state() in {"inactive", ""}, 10)
    assert other.timer_state() == "active"  # another activation's timer is untouched
    assert (act.attempts(), sorted(p.name for p in (STORE / "activation").iterdir())) == before
    other.fx = None


def test_bs3_disarms_after_a_hard_stop_that_left_nothing_a1_intact(activation):
    """A pre-existing rules directory (kept) holding a foreign replacement of the
    rule (A0, kept): nothing A1-intact remains, so BS-3 disarms. Had ACT created
    the rules directory it would be A1-intact and nonempty, and BS-4 would retry."""
    if not os.path.lexists("/run/polkit-1"):
        os.makedirs(ActivationPaths(LAYOUT, activation.id).rules_dir, mode=0o755)
        activation.made_polkit_dir = True
    activation.prepare(pass_config=False)
    p = activation.paths
    fresh = Path(p.rule + ".new")  # replace the rule by another inode: foreign (A0), not removable
    fresh.write_bytes(activation.fx.rule_bytes)
    os.chmod(fresh, 0o644)
    os.rename(fresh, p.rule)
    shown = activation.start_holder()
    assert "status=1 }" in shown["ExecStopPost"]
    doc = activation.record(1)
    assert doc["outcome"] == "hard-stop" and doc["active_rule"]["class"] == "present-foreign-unremoved"
    assert {d["role"]: d["class"] for d in doc["directories"]}["rules-dir"] == "pre-existing-kept"
    activation.arm()
    fired = activation.fire()
    assert fired["status"] == "0"
    assert f"rp11-bs disarmed {activation.id} branch=bs-3 k=1 disarm=stopped" in fired["journal"]
    assert os.path.exists(p.rule)  # BS never removes a foreign object
    assert activation.attempts() == [f"{activation.id}-deact-1-evidence"]


# ---------------------------------------------------------------------------
# BS-4: repeated firings by the real timer through the terminal bound
# ---------------------------------------------------------------------------


def test_the_real_timer_fires_until_backstop_max_then_disarms_itself(activation):
    activation.prepare(backstop_max=2)
    Path(activation.paths.tree_p, "planted").write_text("x")  # every CL hard-stops (tree P nonempty)
    activation.arm(interval=3, runtime_max=60, timeout_stop=10)
    assert wait_until(lambda: activation.timer_state() in {"inactive", ""}, 120), activation.timer_state()
    assert wait_until(lambda: show(activation.service, "ActiveState").get("ActiveState") != "active", 30)
    assert activation.attempts() == [f"{activation.id}-deact-{k}-evidence" for k in (1, 2)]
    for k in (1, 2):
        doc = activation.record(k)
        assert doc["trigger"] == "backstop" and doc["outcome"] == "hard-stop"
    (line,) = activation.terminal_lines()
    assert line == {"schema": "rp11-backstop-terminal/1", "op": "backstop-terminal", "activation_id": activation.id,
                    "reason": "backstop-max", "disarm": "stopped"}
    journal = run("journalctl", "--no-pager", "-o", "cat", "-u", activation.service).stdout
    assert journal.count(f"rp11-bs cleanup {activation.id}") == 2
    assert journal.count(f"rp11-bs bound-reached {activation.id} reason=backstop-max disarm=stopped") == 1
    assert not os.path.lexists(activation.paths.rule)  # the first firing's CL-G removed the grant


def test_the_attempt_limit_is_terminal_on_the_host(activation):
    activation.prepare()
    for k in range(1, 100):
        Path("/var/tmp", f"{activation.id}-deact-{k}-evidence").mkdir()
    activation.arm()
    fired = activation.fire()
    assert fired["status"] == "12"
    assert f"rp11-bs bound-reached {activation.id} reason=attempt-limit disarm=stopped" in fired["journal"]
    assert os.path.exists(activation.paths.rule)  # no CL, not even CL-G
    assert not list((STORE / "activation").iterdir())


# ---------------------------------------------------------------------------
# interruption, hung firings, restarts, concurrency
# ---------------------------------------------------------------------------


def _foreign_grant(activation) -> None:
    FOREIGN_RULE.write_bytes(RULE_BYTES % b"ubuntu")
    os.chmod(FOREIGN_RULE, 0o644)
    assert wait_until(lambda: activation.pk(PkMode.FIRST_DECISIVE).outcome is PkOutcome.AUTHORIZED, 10)


def test_an_interrupted_firing_is_recovered_by_the_next(activation):
    """IM-B: PID 1 kills a firing inside its Polkit series (a foreign grant keeps the
    series running); the next firing's CL reaches st1-verified, the one after disarms."""
    activation.prepare()
    _foreign_grant(activation)
    activation.arm()
    run("systemctl", "start", "--no-block", activation.service, check=True)
    journal = Path(activation.paths.attempt_dir(1)) / "journal"
    assert wait_until(lambda: journal.exists() and b'"op":"cl-g"' in journal.read_bytes(), 30)
    time.sleep(1.0)
    run("systemctl", "kill", "--kill-whom=all", "--signal=SIGKILL", activation.service, check=True)
    assert wait_until(lambda: show(activation.service, "ActiveState")["ActiveState"] in {"failed", "inactive"}, 30)
    assert "run-end" not in activation.attempt_ops(1)
    assert not os.path.lexists(activation.paths.rule)  # CL-G removed the grant before the kill
    assert not (STORE / "activation" / f"{activation.id}.deact-1.json").exists()
    assert wait_until(lambda: rp11_processes() == [], 10)
    FOREIGN_RULE.unlink()
    assert wait_until(lambda: activation.pk(PkMode.FIRST_DECISIVE).outcome is PkOutcome.NOT_AUTHORIZED, 10)
    fired = activation.fire()
    assert fired["status"] == "0", fired["journal"]
    doc = activation.record(2)
    assert doc["outcome"] == "st1-verified" and doc["trigger"] == "backstop"
    assert any(j["path"].endswith("deact-1-evidence/journal") for j in doc["journals"])
    fired = activation.fire()
    assert f"rp11-bs disarmed {activation.id} branch=bs-2 k=2 disarm=stopped" in fired["journal"]


def test_a_hung_firing_is_ended_by_runtime_max_sec(activation):
    """BS-RM: the production firing stuck in its Polkit series is SIGTERMed by PID 1
    at RuntimeMaxSec (default disposition: no handler); nothing it spawned survives."""
    activation.prepare()
    _foreign_grant(activation)
    activation.arm(runtime_max=3, timeout_stop=5)
    fired = activation.fire()
    assert fired["Result"] == "timeout" and fired["status"] == "failed:timeout", fired
    span = unit_span_seconds(activation.service)
    assert span is not None and 3 <= span < 3 + 5, span  # SIGTERM at S_b ends it before S
    if Path(activation.paths.attempt_dir(1), "journal").exists():
        assert "run-end" not in activation.attempt_ops(1)
    assert not (STORE / "activation" / f"{activation.id}.deact-1.json").exists()
    assert wait_until(lambda: rp11_processes() == [], 10), rp11_processes()


HANG_ROLE = b'''import signal, sys, time
def run(role, activation_id, artifact_sha256, **provenance):
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    print("hang-role ignoring SIGTERM", file=sys.stderr, flush=True)
    while True:
        time.sleep(60)
'''


def test_a_firing_that_ignores_sigterm_is_killed_after_timeout_stop_sec(activation):
    """The bound holds even against a role that ignored SIGTERM: PID 1 escalates to
    SIGKILL at TimeoutStopSec. A test double replaces only the role module."""
    activation.prepare()
    roles = ARTIFACT_DIR / "lib/rp11_roles.py"
    original = roles.read_bytes()
    roles.write_bytes(HANG_ROLE)
    try:
        activation.arm(runtime_max=10, timeout_stop=3)  # S_b leaves room to start on a loaded host
        fired = activation.fire()
    finally:
        roles.write_bytes(original)
    assert "hang-role ignoring SIGTERM" in fired["journal"], fired["journal"]
    assert fired["Result"] == "timeout" and fired["status"] == "killed:9", fired
    span = unit_span_seconds(activation.service)
    assert span is not None and 10 + 3 <= span < 10 + 3 + 3, span  # SIGTERM ignored at S_b, SIGKILL at S_b + S
    assert wait_until(lambda: rp11_processes() == [], 10)


def test_manager_reexec_and_polkit_restart_between_firings(activation):
    activation.prepare()
    activation.arm()
    run("systemctl", "daemon-reexec", check=True)
    assert wait_until(lambda: activation.timer_state() == "active", 30)
    restart_polkit()
    fired = activation.fire()
    assert fired["status"] == "0", fired["journal"]
    assert activation.record(1)["outcome"] == "st1-verified"
    run("systemctl", "daemon-reload", check=True)
    restart_polkit()
    fired = activation.fire()
    assert f"rp11-bs disarmed {activation.id} branch=bs-2 k=1 disarm=stopped" in fired["journal"]


def test_a_polkit_restart_during_a_firing_never_becomes_success(activation):
    activation.prepare()
    _foreign_grant(activation)  # keep the series running while polkitd restarts
    activation.arm()
    run("systemctl", "start", "--no-block", activation.service, check=True)
    journal = Path(activation.paths.attempt_dir(1)) / "journal"
    assert wait_until(lambda: journal.exists() and b'"op":"cl-g"' in journal.read_bytes(), 30)
    FOREIGN_RULE.unlink()
    restart_polkit()
    assert wait_until(lambda: show(activation.service, "ActiveState")["ActiveState"] in {"failed", "inactive"}, 60)
    status = show(activation.service, "ExecMainStatus")["ExecMainStatus"]
    doc = activation.record(1)
    assert (status, doc["outcome"]) in {("0", "st1-verified"), ("1", "hard-stop")}
    if doc["outcome"] == "st1-verified":
        assert doc["pk"]["outcome"] == "not-authorized"
    for _ in range(2):  # at most two more firings settle it
        fired = activation.fire()
        if "rp11-bs disarmed" in fired["journal"]:
            break
    assert wait_until(lambda: activation.timer_state() in {"inactive", ""}, 10)


def test_concurrent_firings_run_cl_once(activation):
    activation.prepare()
    argv = [ROLE_INTERPRETER, "-I", "-S", ROLE_ARTIFACT, "backstop", activation.id, activation.fx.a2_sha256]
    procs = [subprocess.Popen(argv, stderr=subprocess.PIPE, env={}, cwd="/") for _ in range(3)]
    codes = [proc.wait(timeout=90) for proc in procs]
    errs = [proc.stderr.read().decode() for proc in procs]
    assert all("Traceback" not in e for e in errs)
    # one firing runs CL; the others find the lock held (14) or, if later, the
    # record and an unarmed timer (BS-2 with disarm=not-loaded, 0)
    assert set(codes) <= {0, 14}, (codes, errs)
    assert activation.attempts() == [f"{activation.id}-deact-1-evidence"]
    assert sum(f"rp11-bs cleanup {activation.id} k=1" in e for e in errs) == 1
    for e in errs:
        for line in e.splitlines():
            if line.startswith(("rp11-bs", "rp11-cl")):
                assert activation.id in line
    assert activation.record(1)["outcome"] == "st1-verified"
