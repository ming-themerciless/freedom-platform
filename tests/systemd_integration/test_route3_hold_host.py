"""RT-2 ``hold`` through PID 1 on the disposable host, with stop-post and backstop.

Real systemd, real Polkit, real ``/run`` (tmpfs), ``/var/tmp`` and
``/var/lib/freedom-blades-rp11``, and the production artifact built fresh from
the hash-pinned wheel. Each test prepares a synthetic activation (no real secret
or player data): A-2 and H-1 records, the staged rule, the operator-owned ACT
directory (AP-1) and a disposable ``rp11-capture-pass-a.service`` in
``/run/systemd/system`` whose start creates the capture root. The holder unit
is created by the accepted adapter (DI-2) exactly as SA-1 would, so PID 1 runs
the exact ``hold`` vector and then the exact ``ExecStopPost`` vector; the
holder's own DI-3 creates the backstop timer and service.

    sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test \\
        FREEDOM_RP11_WHEEL=/path/to/jeepney-0.9.0-py3-none-any.whl \\
        /opt/freedom-blades/runtime/venv-web/bin/python -m pytest -q -rfEs \\
        tests/systemd_integration/test_route3_hold_host.py

Polkit (harness setup only, never the role): polkitd 127 watches
``/run/polkit-1/rules.d`` only if it existed when polkitd started. For the
successful flows the harness creates it and restarts Polkit once; the
late-directory test removes it and restarts Polkit so the holder's own tree R
is created after polkitd started, which must fail closed at AV-1. The holder
never restarts or reloads Polkit (its ``MainPID`` is compared).

Everything is removed afterwards and the teardown asserts it.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import pwd
import secrets
import shutil
import socket
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

if os.environ.get("FREEDOM_SYSTEMD_INTEGRATION") != "oracle-test":
    pytest.skip("set FREEDOM_SYSTEMD_INTEGRATION=oracle-test (disposable host only)", allow_module_level=True)
if socket.gethostname() != "Test":
    pytest.skip("refusing to run: not the disposable host (hostname != Test)", allow_module_level=True)
if os.geteuid() != 0 or not Path("/run/systemd/system").is_dir():
    pytest.skip("needs root on a systemd host", allow_module_level=True)
pytest.importorskip("jeepney")

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from adapters.rp11.baseline import HostBaseline  # noqa: E402
from adapters.rp11.process import SystemClock  # noqa: E402
from adapters.rp11.stop_post import StopPostServices  # noqa: E402
from adapters.systemd.jeepney_bus import connect_system_bus  # noqa: E402
from adapters.systemd.manager import ROLE_ARTIFACT, ROLE_INTERPRETER, SystemdManagerAdapter  # noqa: E402
from application.rp11.authority import PASS_SCHEMA, Operator, Params  # noqa: E402
from application.rp11.canonical import parse_canonical  # noqa: E402
from application.rp11.paths import ActivationPaths, Layout  # noqa: E402
from application.rp11.pk import PkMode, PkOutcome  # noqa: E402
from application.rp11.records import validate_record  # noqa: E402
from application.unit_control import ControlOk, ControlRefused, HolderSpec, RefusalReason, UnitVerb  # noqa: E402
from rp11_fixtures import H2_RECORD_SHA256, RULE_BYTES, ActivationFixture  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = Path(ROLE_ARTIFACT).parent
STORE = Path("/var/lib/freedom-blades-rp11")
CAPTURE_UNIT_FILE = Path("/run/systemd/system/rp11-capture-pass-a.service")
FOREIGN_RULE = Path("/etc/polkit-1/rules.d/49-rp11-hold-test.rules")
LAYOUT = Layout()
PARAMS = Params(pk_op_ms=5_000, pk_call_ms=2_000, reap_grace_ms=2_000, lock_wait_ms=1_000)
OPERATOR = pwd.getpwnam("ubuntu")
LEASE = {
    "start_window_s": 60,
    "lease_s": 900,
    "poll_ms": 250,
    "stop_timeout_s": 60,
    "backstop_period_s": 30,
    "bs_runtime_s": 60,
}


def run(*argv: str, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True, check=check)


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


def polkit_pid() -> str:
    return show("polkit.service", "MainPID")["MainPID"]


def restart_polkit() -> None:
    # Harness setup only. Reset the disposable service's start-rate counter so
    # repeated runs stay repeatable (as in the stop-post and backstop suites).
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


def operator_start() -> subprocess.CompletedProcess:
    """The operator's own ``start``: ``ubuntu`` without sudo, no agent, so only a
    Polkit rule can authorize it."""
    return run("runuser", "-u", "ubuntu", "--", "systemctl", "--no-ask-password", "start",
               "rp11-capture-pass-a.service")


# --- the production artifact, built fresh -----------------------------------------


def _builder():
    spec = importlib.util.spec_from_file_location("rp11_hold_build", ROOT / "infra/rp11-h1/build.py")
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
        self.capture_root = f"/var/tmp/rp11-capture-{self.id}"
        self.fx: ActivationFixture | None = None
        self.lease = dict(LEASE)

    @property
    def unit(self) -> str:
        return f"{self.id}.service"

    @property
    def timer(self) -> str:
        return f"{self.id}-backstop.timer"

    @property
    def backstop_service(self) -> str:
        return f"{self.id}-backstop.service"

    def prepare(self, *, rules_dir: bool = True, capture: str = "mkdir", lease: dict | None = None,
                restart: bool = True) -> None:
        self.lease.update(lease or {})
        for sub in ("", "a2", "h1", "activation"):
            (STORE / sub).mkdir(mode=0o755, exist_ok=True)
            os.chmod(STORE / sub, 0o755)
        command = {"mkdir": f"/usr/bin/mkdir -m 0700 {self.capture_root}", "long": "/usr/bin/sleep 600"}[capture]
        CAPTURE_UNIT_FILE.write_text(
            "[Unit]\nDescription=RP-11 synthetic capture pass (disposable host test)\n\n"
            f"[Service]\nType=exec\nExecStart={command}\n"
        )
        run("systemctl", "daemon-reload", check=True)
        run("systemctl", "reset-failed", "rp11-capture-pass-a.service")
        services = StopPostServices(connect_system_bus, SystemClock())
        baseline = HostBaseline(services.units(PARAMS)).recompute()
        assert baseline is not None and baseline["unit"]["load_state"] == "loaded"
        self.fx = ActivationFixture(
            LAYOUT, self.id, Path("/proc/sys/kernel/random/boot_id").read_text().strip(), baseline,
            params=PARAMS, pass_doc={"schema": PASS_SCHEMA, "capture_root": self.capture_root},
        )
        self.fx.rules_dir_preexists = rules_dir
        self.fx.write_authority(lease=self.lease)
        act = Path(self.paths.act_dir)  # AP-1: the operator's ACT directory
        act.mkdir(mode=0o700)
        os.chown(act, OPERATOR.pw_uid, OPERATOR.pw_gid)
        os.chmod(act, 0o700)
        if not restart:  # share the running polkitd and its rules directory as they are
            return
        shutil.rmtree("/run/polkit-1", ignore_errors=True)
        if rules_dir:
            Path(self.paths.rules_dir).mkdir(mode=0o755, parents=True)
            os.chmod(self.paths.polkit_run_dir, 0o755)
        restart_polkit()  # polkitd watches only the rules directories present at its start

    def start_holder(self) -> None:
        spec = HolderSpec(
            activation_id=self.id,
            artifact_sha256=self.fx.a2_sha256,
            runtime_max_seconds=self.lease["lease_s"],
            timeout_stop_seconds=self.lease["stop_timeout_s"],
        )
        result = SystemdManagerAdapter(connect_system_bus).create_holder(spec)
        assert isinstance(result, ControlOk), result

    def pk(self, mode: PkMode, verb: UnitVerb = UnitVerb.START):
        services = StopPostServices(connect_system_bus, SystemClock())
        return services.pk(PARAMS).run(Operator.from_baseline(self.fx.baseline), verb, mode)

    def ops(self) -> list[str]:
        path = Path(self.paths.act_dir) / "journal"
        if not path.exists():
            return []
        return [json.loads(line)["op"] for line in path.read_bytes().splitlines() if line.endswith(b"}")]

    def lines(self, op: str) -> list[dict]:
        path = Path(self.paths.act_dir) / "journal"
        if not path.exists():
            return []
        return [doc for doc in (json.loads(line) for line in path.read_bytes().splitlines() if line.endswith(b"}")) if doc["op"] == op]

    def wait_op(self, op: str, timeout: float = 30.0) -> None:
        assert wait_until(lambda: op in self.ops(), timeout), self.ops()

    def wait_stopped(self, timeout=60.0, *, stop_post: bool = True) -> tuple[str, str]:
        """``(hold line, stop-post line)`` from the unit's own journal.

        A holder that ends cleanly is garbage-collected by PID 1 at once, so the
        unit's properties are gone; its journal (main process and ExecStopPost
        under the same unit name) is the evidence. ``""`` for a missing line."""
        assert wait_until(
            lambda: show(self.unit, "ActiveState")["ActiveState"] in {"failed", "inactive"}, timeout
        ), show(self.unit, "ActiveState", "SubState")
        if stop_post:
            assert wait_until(lambda: self.line("rp11-cl ") != "", 10), self.log()
        return self.line("rp11-hold "), self.line("rp11-cl ")

    def log(self) -> str:
        return run("journalctl", "--no-pager", "-o", "cat", "-u", self.unit).stdout

    def line(self, prefix: str) -> str:
        found = [line for line in self.log().splitlines() if line.startswith(prefix)]
        assert len(found) <= 1, found
        return found[0] if found else ""

    def record(self, name: str) -> dict:
        path = STORE / "activation" / f"{self.id}.{name}.json"
        info = path.lstat()
        assert (info.st_uid, info.st_gid, info.st_mode & 0o7777, info.st_nlink) == (0, 0, 0o444, 1)
        doc = parse_canonical(path.read_bytes())
        validate_record(doc)
        return doc

    def has_record(self, name: str) -> bool:
        return (STORE / "activation" / f"{self.id}.{name}.json").exists()

    def clean(self) -> None:
        for unit in (self.unit, self.timer, self.backstop_service):
            run("systemctl", "stop", unit)
            run("systemctl", "reset-failed", unit)
        for path in (self.paths.tree_p, self.paths.lock_dir, self.capture_root, "/run/polkit-1"):
            shutil.rmtree(path, ignore_errors=True)
        for entry in Path("/var/tmp").glob(f"{self.id}-*"):
            shutil.rmtree(entry, ignore_errors=True)
        for temp in Path("/run").glob(f".rp11-{self.id}-*"):
            shutil.rmtree(temp, ignore_errors=True)


@pytest.fixture
def activations():
    assert not STORE.exists(), "record store left from an earlier run"
    made: list[Activation] = []

    def make() -> Activation:
        made.append(Activation())
        return made[-1]

    yield make
    run("systemctl", "stop", "rp11-capture-pass-a.service")
    for act in made:
        act.clean()
    FOREIGN_RULE.unlink(missing_ok=True)
    CAPTURE_UNIT_FILE.unlink(missing_ok=True)
    run("systemctl", "daemon-reload", check=True)
    run("systemctl", "reset-failed", "rp11-capture-pass-a.service")
    shutil.rmtree(STORE, ignore_errors=True)
    restart_polkit()
    assert wait_until(lambda: rp11_processes() == [], 10), rp11_processes()
    for act in made:
        assert run("systemctl", "list-units", f"{act.id}*", "--all", "--no-legend").stdout.strip() == ""
        assert not list(Path("/var/tmp").glob(f"{act.id}-*")) and not os.path.lexists(act.capture_root)
        assert not os.path.lexists(act.paths.tree_p) and not os.path.lexists(act.paths.lock_dir)
    assert not os.path.lexists("/run/polkit-1")
    assert show("rp11-capture-pass-a.service", "LoadState")["LoadState"] == "not-found"
    assert run("systemctl", "is-active", "polkit.service").stdout.strip() == "active"


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------


def test_hold_activates_the_operator_starts_the_pass_and_every_rung_cleans_up(activations):
    """RT-2 end to end: ACT PASS, a real operator ``start`` under the grant, HL
    ``pass-ended``, IGR, stop-post ``st1-verified``, then the backstop's BS-2 disarm."""
    act = activations()
    act.prepare()
    polkit_before = polkit_pid()
    act.start_holder()
    act.wait_op("hold-start")
    doc = act.record("act")
    assert doc["outcome"] == "activated" and doc["trigger"] == "act" and doc["holder"]["invocation_id"] != "absent"
    assert doc["pk"]["outcome"] == "authorized" and doc["grant_check"]["stop_control"] == "not-authorized"
    assert all(c["reaped"] for c in doc["children"]["entries"]) and doc["children"]["entries"]
    assert show(act.timer, "ActiveState")["ActiveState"] == "active"
    assert show(act.unit, "ActiveState")["ActiveState"] == "active"
    assert all(os.path.exists(p) for p in (act.paths.rule, act.paths.pass_config, act.paths.grant_id))
    grant = parse_canonical(Path(act.paths.grant_id).read_bytes())  # the holder's in-memory identity
    k = os.lstat(act.paths.lock_dir)
    started = operator_start()
    assert started.returncode == 0, started.stderr  # the grant is real
    hold, cl = act.wait_stopped()
    assert hold == f"rp11-hold hold-ended {act.id} step=HL detail=pass-ended act_pass=yes igr=removed", act.log()
    assert cl.startswith(f"rp11-cl st1-verified {act.id} k=1 rule=removed-earlier pk=not-authorized"), cl
    assert "Traceback" not in act.log()
    ops = act.ops()
    assert act.lines("hold-end")[0]["reason"] == "pass-ended"
    assert act.lines("igr")[0]["outcome"] == "removed" and ops.index("hold-end") < ops.index("igr")
    # RT2.AM0.16: the complete run-start, its authority from A-2 and the verified tool
    start = act.lines("run-start")[0]
    assert set(start) == {
        "seq", "prev", "run", "op", "a2_sha256", "h1_record_sha256", "h2_record_sha256", "boot_id",
        "pass_config_sha256", "staged_rule_sha256", "tool_sha256", "holder_invocation_id", "lease", "lock",
        "capture", "helper", "params",
    }
    tool_sha256 = hashlib.sha256(Path(LAYOUT.tool).read_bytes()).hexdigest()
    assert start["tool_sha256"] == tool_sha256 == act.fx.tool_sha256
    assert start["helper"] == {**act.fx.helper("hold")} and start["h2_record_sha256"] == H2_RECORD_SHA256
    assert start["lock"] == {
        "object": {"path": act.paths.lock_dir, "dev": k.st_dev, "ino": k.st_ino}, "mode": "held", "wait_ms": 0,
    }
    # RT2.IGR.3: the identity GRR used; RT2.AM3.2: run-end last, after igr
    assert act.lines("igr")[0]["identity"] == {key: grant[key] for key in ("path", "dev", "ino", "sha256", "size", "mode")}
    assert ops[-2:] == ["igr", "run-end"] and act.lines("run-end")[0]["outcome"] == "hold-ended"
    deact = act.record("deact-1")
    assert deact["outcome"] == "st1-verified" and deact["release"]["first_rung"] == "igr"
    assert deact["active_rule"]["class"] == "removed-earlier"
    # Diagnostic only: PID 1 unloads the inactive capture unit, so τ may read 0
    # again (PO-21 (k)/(s)) and an unclaimed pass can be labelled ``none``.
    assert deact["consume"]["class"] in {"none", "unidentified"}
    for path in (act.paths.rule, act.paths.pass_config, act.paths.tree_p, act.paths.grant_id, act.paths.lock_dir):
        assert not os.path.lexists(path), path
    denied = operator_start()  # no grant survives
    assert denied.returncode != 0
    assert act.pk(PkMode.FIRST_DECISIVE).outcome is PkOutcome.NOT_AUTHORIZED
    # the holder's own DI-3: the backstop fires within R and disarms its timer (BS-2)
    assert wait_until(lambda: show(act.timer, "ActiveState")["ActiveState"] != "active", 50), show(act.timer, "ActiveState")
    assert not act.has_record("deact-2")
    assert polkit_pid() == polkit_before  # no role restarted Polkit


def test_a_rules_directory_created_after_polkit_started_fails_closed_at_av1(activations):
    act = activations()
    act.prepare(rules_dir=False)  # /run/polkit-1 absent when polkitd starts
    polkit_before = polkit_pid()
    act.start_holder()
    hold, cl = act.wait_stopped(timeout=60)
    assert hold == f"rp11-hold grant-not-seen {act.id} step=AV-1 detail=not-seen act_pass=no igr=removed" or hold.startswith(
        f"rp11-hold grant-not-seen {act.id} step=AV-1"), act.log()
    assert cl.startswith(f"rp11-cl st1-verified {act.id} k=1"), cl
    trees = [line["tag"] for line in act.lines("tree-intent")]
    assert trees == ["p", "r"]
    check = act.lines("grant-check")[0]
    assert (check["verb"], check["outcome"]) == ("start", "unconfirmed")
    assert act.lines("igr")[0]["outcome"] == "removed"
    assert act.ops()[-2:] == ["igr", "run-end"] and act.lines("run-end")[0]["outcome"] == "grant-not-seen"
    assert act.record("act")["outcome"] == "failed"
    deact = act.record("deact-1")
    assert deact["outcome"] == "st1-verified"
    assert {d["role"]: d["class"] for d in deact["directories"]}.get("tree-r") == "removed"
    assert not os.path.lexists("/run/polkit-1")
    assert polkit_pid() == polkit_before


@pytest.mark.parametrize("signals", [1, 2])
def test_sigterm_during_av1_runs_igr_once_and_stop_post_recovers(activations, signals):
    act = activations()
    act.prepare(rules_dir=False)  # a 5 s AV-1 series to interrupt
    act.start_holder()
    assert wait_until(
        lambda: any(l["name"] == "50-freedom-blades-rp11.rules" for l in act.lines("file-linked")), 30
    ), act.ops()
    main_pid = int(show(act.unit, "MainPID")["MainPID"])
    assert main_pid > 1
    for _ in range(signals):  # back to back: the second arrives while the first is handled
        os.kill(main_pid, 15)
    hold, cl = act.wait_stopped()
    assert hold == f"rp11-hold interrupted {act.id} step=AV-1 detail=none act_pass=no igr=removed", act.log()
    assert act.ops().count("igr") == 1 and "hold-start" not in act.ops()
    assert act.ops()[-2:] == ["igr", "run-end"] and act.lines("run-end")[0]["outcome"] == "interrupted"
    assert cl.startswith(f"rp11-cl st1-verified {act.id} k=1"), cl
    assert act.record("deact-1")["outcome"] == "st1-verified"
    assert "Traceback" not in act.log()
    assert wait_until(lambda: rp11_processes() == [], 10)  # the subject was settled


def test_stop_job_during_hl_ends_with_igr_then_stop_post(activations):
    act = activations()
    act.prepare()
    act.start_holder()
    act.wait_op("hold-start")
    run("systemctl", "stop", act.unit, check=True)  # SIGTERM through a stop job
    hold, cl = act.wait_stopped()
    assert hold == f"rp11-hold interrupted {act.id} step=HL detail=none act_pass=yes igr=removed", act.log()
    assert "hold-end" not in act.ops()
    assert act.ops()[-2:] == ["igr", "run-end"] and act.lines("run-end")[0]["outcome"] == "interrupted"
    assert cl.startswith(f"rp11-cl st1-verified {act.id} k=1"), cl


def test_sigkill_after_hold_start_is_recovered_by_cl_g(activations):
    act = activations()
    act.prepare()
    act.start_holder()
    act.wait_op("hold-start")
    run("systemctl", "kill", "--kill-whom=main", "--signal=SIGKILL", act.unit, check=True)
    hold, cl = act.wait_stopped()
    assert hold == "" and "igr" not in act.ops() and "run-end" not in act.ops()  # uncatchable: no IGR, no line
    assert cl.startswith(f"rp11-cl st1-verified {act.id} k=1 rule=removed-earlier"), cl
    deact = act.record("deact-1")
    assert deact["outcome"] == "st1-verified" and deact["release"]["first_rung"] == "cl-g"
    assert not os.path.lexists(act.paths.rule)


def test_holder_and_stop_post_killed_then_the_backstop_recovers(activations):
    """IM-A/IM-B: the holder is SIGKILLed after hold-start and its stop-post is
    SIGKILLed in its Polkit series (a foreign grant keeps the series running);
    the backstop the holder armed runs CL attempt 2 to st1-verified and then
    disarms its timer."""
    act = activations()
    act.prepare()
    act.start_holder()
    act.wait_op("hold-start")
    FOREIGN_RULE.write_bytes(RULE_BYTES % b"ubuntu")
    os.chmod(FOREIGN_RULE, 0o644)
    run("systemctl", "kill", "--kill-whom=main", "--signal=SIGKILL", act.unit, check=True)
    attempt = Path(act.paths.attempt_dir(1)) / "journal"
    assert wait_until(lambda: attempt.exists() and b'"op":"cl-g"' in attempt.read_bytes(), 30)
    time.sleep(1.0)  # inside CL-4's 5 s series
    run("systemctl", "kill", "--kill-whom=all", "--signal=SIGKILL", act.unit, check=True)
    act.wait_stopped(stop_post=False)
    assert not act.has_record("deact-1") and not os.path.lexists(act.paths.rule)
    FOREIGN_RULE.unlink()
    assert wait_until(lambda: act.has_record("deact-2"), 70)
    deact = act.record("deact-2")
    assert (deact["trigger"], deact["outcome"]) == ("backstop", "st1-verified")
    assert wait_until(lambda: show(act.timer, "ActiveState")["ActiveState"] != "active", 50)
    assert not act.has_record("deact-3")


def test_lease_expiry_with_a_running_pass_then_backstop_disarm(activations):
    act = activations()
    act.prepare(capture="long", lease={"lease_s": 61})
    act.start_holder()
    act.wait_op("hold-start")
    started = operator_start()
    assert started.returncode == 0, started.stderr
    assert wait_until(lambda: "pass-observed" in act.ops(), 10)
    hold, cl = act.wait_stopped(timeout=90)  # RuntimeMaxSec = L sends SIGTERM
    assert hold == f"rp11-hold interrupted {act.id} step=HL detail=none act_pass=yes igr=removed", act.log()
    assert cl.startswith(f"rp11-cl unit-still-active {act.id} k=1"), cl
    assert act.record("deact-1")["outcome"] == "hard-stop"
    assert not os.path.lexists(act.paths.rule)
    run("systemctl", "stop", "rp11-capture-pass-a.service", check=True)
    assert wait_until(lambda: show(act.timer, "ActiveState")["ActiveState"] != "active", 70)


def test_a_second_activation_is_refused_and_leaves_the_first_intact(activations):
    first = activations()
    first.prepare()
    first.start_holder()
    first.wait_op("hold-start")
    second = activations()
    second.prepare(restart=False)  # same /run/polkit-1/rules.d, polkit untouched
    second.start_holder()
    hold, cl = second.wait_stopped()
    assert hold == f"rp11-hold precondition {second.id} step=AM-0 detail=present act_pass=no igr=absent", second.log()
    assert second.ops() == []
    assert cl.startswith(f"rp11-cl hard-stop {second.id} k=1"), cl  # nothing attributable
    assert os.path.exists(first.paths.rule) and show(first.unit, "ActiveState")["ActiveState"] == "active"
    # the same activation id cannot be created twice (PO-21 (m))
    duplicate = SystemdManagerAdapter(connect_system_bus).create_holder(
        HolderSpec(first.id, first.fx.a2_sha256, 900, 60)
    )
    assert duplicate == ControlRefused(RefusalReason.EXISTS)
    run("systemctl", "stop", first.unit, check=True)
    hold, cl = first.wait_stopped()
    assert hold.startswith(f"rp11-hold interrupted {first.id} step=HL") and cl.startswith(f"rp11-cl st1-verified {first.id}")


def test_manager_reexec_and_polkit_restart_during_hl(activations):
    """Either outcome is correct and both are checked: the holder rides through
    the re-exec and Polkit restart and the pass ends normally, or an HL DI-1 read
    meets the re-executing manager and the activation ends ``observation-failed``
    (fail closed, never a guess) with its grant removed by IGR."""
    act = activations()
    act.prepare()
    act.start_holder()
    act.wait_op("hold-start")
    run("systemctl", "daemon-reexec", check=True)
    restart_polkit()  # harness: the pre-existing rules directory is read at start
    time.sleep(1.0)
    if show(act.unit, "ActiveState")["ActiveState"] == "active":
        started = operator_start()
        assert started.returncode == 0, started.stderr
        hold, cl = act.wait_stopped()
        assert hold.startswith(f"rp11-hold hold-ended {act.id} step=HL detail=pass-ended"), act.log()
    else:
        hold, cl = act.wait_stopped()
        assert hold == (
            f"rp11-hold observation-failed {act.id} step=HL detail=observation-failed act_pass=yes igr=removed"
        ), act.log()
        assert act.lines("hold-end")[0]["reason"] == "observation-failed"
        assert operator_start().returncode != 0
    assert cl.startswith(f"rp11-cl st1-verified {act.id}"), cl


def test_a_damaged_grant_is_never_removed(activations):
    act = activations()
    act.prepare()
    act.start_holder()
    act.wait_op("hold-start")
    os.chmod(act.paths.rule, 0o664)  # still the same inode, no longer A1-intact
    run("systemctl", "stop", act.unit, check=True)
    hold, cl = act.wait_stopped()
    assert hold.endswith("igr=kept-damaged"), hold
    assert cl.startswith(f"rp11-cl hard-stop {act.id}") and "rule=present-damaged-unremoved" in cl, cl
    assert act.record("deact-1")["active_rule"]["class"] == "present-damaged-unremoved"
    assert os.path.exists(act.paths.rule)


def test_a_start_before_hold_start_ends_the_activation(activations):
    act = activations()
    act.prepare(capture="long")
    act.start_holder()
    act.wait_op("backstop-armed", timeout=20)
    run("systemctl", "start", "rp11-capture-pass-a.service", check=True)  # a start before hold-start
    hold, cl = act.wait_stopped()
    assert hold.startswith(f"rp11-hold start-before-hold {act.id} step=hold-start"), act.log()
    assert act.lines("hold-end")[0]["reason"] == "start-before-hold" and "hold-start" not in act.ops()
    assert act.lines("igr")[0]["outcome"] == "removed"
    assert cl.startswith(f"rp11-cl unit-still-active {act.id}"), cl  # the capture unit is active


def test_a_preloaded_backstop_name_stops_at_am0(activations):
    act = activations()
    act.prepare()
    blocker = run("systemd-run", f"--unit={act.id}-backstop", "--service-type=exec", "/usr/bin/sleep", "600")
    assert blocker.returncode == 0, blocker.stderr
    try:
        act.start_holder()
        hold, _cl = act.wait_stopped()
        assert hold == f"rp11-hold precondition {act.id} step=AM-0 detail=unit-state act_pass=no igr=absent", act.log()
        assert act.ops() == [] and not os.path.lexists(act.paths.lock_dir)
    finally:
        run("systemctl", "stop", f"{act.id}-backstop.service")


# --- H-PROC.3 under PID 1: the DI-6 subject inherits no high descriptor -----------

_SUBJECT_FD_PROBE = """
import json, os, resource, sys
sys.path.insert(0, sys.argv[1])
from adapters.rp11.process import ForkSubjectLauncher, LinuxProcessOps, SystemClock
from application.rp11.authority import Operator
from application.rp11.sn import SignalContract

uid, gid, high = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
operator = Operator(user="ubuntu", uid=uid, gid=gid, groups=tuple(sorted(set(os.getgrouplist("ubuntu", gid)))))
ops = LinuxProcessOps(SystemClock())
unit_limits = resource.getrlimit(resource.RLIMIT_NOFILE)
resource.setrlimit(resource.RLIMIT_NOFILE, (high + 1, unit_limits[1]))  # the reviewer's reproduction
source = os.open("/dev/null", os.O_RDONLY)
os.dup2(source, high, inheritable=True)
os.close(source)
facts = {"unit_limits": list(unit_limits), "parent_has_high": str(high) in os.listdir("/proc/self/fd")}
for case, soft in (("raised", high + 1), ("lowered-below", unit_limits[0])):
    resource.setrlimit(resource.RLIMIT_NOFILE, (soft, unit_limits[1]))
    h = ForkSubjectLauncher(ops, ready_ms=2000).spawn(operator)
    status = dict(l.split(":\\t", 1) for l in open(f"/proc/{h.pid}/status").read().splitlines() if ":\\t" in l)
    facts[case] = {
        "ready": h.ready,
        "fds": sorted(os.listdir(f"/proc/{h.pid}/fd"), key=int),
        "uid": status["Uid"].split(),
        "cwd": os.readlink(f"/proc/{h.pid}/cwd"),
        "sid_is_pid": os.getsid(h.pid) == h.pid,
    }
    SignalContract(ops, grace_ms=2000, slice_ms=50).settle_pk_subject(h)
    facts[case]["state"] = h.state.value
print(json.dumps(facts))
"""


def test_the_di6_subject_inherits_no_descriptor_above_65535_under_pid1():
    """A transient root service with the holder's default ``LimitNOFILE`` (soft 1,024,
    hard 524,288 here): with an inheritable descriptor at 70,000, under a raised and
    a lowered-below soft limit, the real subject (credentials changed to the
    operator) is ready with exactly 0, 1 and 2, its own session, cwd ``/``."""
    unit = f"rp11-fd-probe-{secrets.token_hex(4)}"
    result = run(
        "systemd-run", f"--unit={unit}", "--wait", "--pipe", "--collect", "--quiet",
        "-p", "User=root", sys.executable, "-I", "-B", "-c", _SUBJECT_FD_PROBE,
        str(ROOT), str(OPERATOR.pw_uid), str(OPERATOR.pw_gid), "70000",
    )
    assert result.returncode == 0, result.stderr
    facts = json.loads(result.stdout.strip().splitlines()[-1])
    assert facts["parent_has_high"] and facts["unit_limits"][1] >= 70_001
    for case in ("raised", "lowered-below"):
        got = facts[case]
        assert got["ready"] and got["fds"] == ["0", "1", "2"], (case, got)
        assert got["uid"] == [str(OPERATOR.pw_uid)] * 4 and got["cwd"] == "/" and got["sid_is_pid"]
        assert got["state"] == "reaped", (case, got)
    assert run("systemctl", "is-active", unit).stdout.strip() != "active"
