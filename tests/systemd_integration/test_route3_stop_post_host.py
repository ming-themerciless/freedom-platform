"""RT-3 ``deact … stop-post`` through PID 1 on the disposable host.

Real systemd, real Polkit, real ``/run`` (tmpfs), ``/var/tmp`` and
``/var/lib/freedom-blades-rp11``, and the production artifact built fresh from
the hash-pinned wheel. Each test prepares a synthetic activation (no real
secret or player data), creates the holder through the accepted adapter (DI-2);
the production ``hold`` role finds the activation already built and stops at
AM-0 (precondition, 21, nothing touched), so PID 1 runs the exact
``ExecStopPost`` vector, which is the real cleanup.

    sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test \\
        FREEDOM_RP11_WHEEL=/path/to/jeepney-0.9.0-py3-none-any.whl \\
        /opt/freedom-blades/runtime/venv-web/bin/python -m pytest -q -rfEs \\
        tests/systemd_integration/test_route3_stop_post_host.py

Polkit is restarted after a test creates ``/run/polkit-1/rules.d``: polkitd 127
does not watch a rules directory that did not exist when it started (observed
here; a ``hold``-slice design input, not something cleanup relies on).
Everything is removed afterwards and the teardown asserts it.
"""

from __future__ import annotations

import importlib.util
import json
import os
import pwd
import shutil
import socket
import subprocess
import sys
import time
import secrets
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
from application.rp11.authority import Operator, Params  # noqa: E402
from application.rp11.canonical import parse_canonical  # noqa: E402
from application.rp11.paths import ActivationPaths, Layout  # noqa: E402
from application.rp11.pk import PkMode, PkOutcome  # noqa: E402
from application.rp11.records import validate_record  # noqa: E402
from application.unit_control import ControlOk, HolderSpec, UnitVerb  # noqa: E402
from rp11_fixtures import RULE_BYTES, ActivationFixture  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = Path(ROLE_ARTIFACT).parent
STORE = Path("/var/lib/freedom-blades-rp11")
FOREIGN_RULE = Path("/etc/polkit-1/rules.d/49-rp11-stop-post-test.rules")
LAYOUT = Layout()
PARAMS = Params(pk_op_ms=5_000, pk_call_ms=2_000, reap_grace_ms=2_000, lock_wait_ms=1_000)
OPERATOR = pwd.getpwnam("ubuntu")


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


def boot_id() -> str:
    return Path("/proc/sys/kernel/random/boot_id").read_text().strip()


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


# --- the production artifact, built fresh -----------------------------------------


def _builder():
    spec = importlib.util.spec_from_file_location("rp11_stop_post_build", ROOT / "infra/rp11-h1/build.py")
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
    assert not list(ARTIFACT_DIR.parent.glob(f".{ARTIFACT_DIR.name}.*"))


# --- one synthetic activation per test ----------------------------------------------


class Activation:
    def __init__(self) -> None:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        self.id = f"rp11-act-{stamp}-{secrets.token_hex(4)}"
        self.paths = ActivationPaths(LAYOUT, self.id)
        self.fx: ActivationFixture | None = None

    @property
    def unit(self) -> str:
        return f"{self.id}.service"

    def prepare(self, *, grant_id: bool = True) -> None:
        for sub in ("", "a2", "h1", "activation"):
            (STORE / sub).mkdir(mode=0o755, exist_ok=True)
            os.chmod(STORE / sub, 0o755)
        services = StopPostServices(connect_system_bus, SystemClock())
        baseline = HostBaseline(services.units(PARAMS)).recompute()
        assert baseline is not None, "baseline must be computable on the host"
        assert baseline["operator"]["uid"] == OPERATOR.pw_uid
        self.fx = ActivationFixture(LAYOUT, self.id, boot_id(), baseline, params=PARAMS)
        self.fx.rules_dir_preexists = os.path.isdir(self.paths.rules_dir)
        self.fx.write_authority()
        self.fx.activate(act_dir_uid=OPERATOR.pw_uid, grant_id=grant_id)
        restart_polkit()  # see the module docstring
        # Positive control with the real PK machinery: the synthetic grant is live.
        result = self.pk(PkMode.SEEK_AUTHORIZED)
        assert result.outcome is PkOutcome.AUTHORIZED, result.errors

    def pk(self, mode: PkMode):
        services = StopPostServices(connect_system_bus, SystemClock())
        operator = Operator.from_baseline(self.fx.baseline)
        return services.pk(PARAMS).run(operator, UnitVerb.START, mode)

    def start_holder(self) -> None:
        spec = HolderSpec(
            activation_id=self.id,
            artifact_sha256=self.fx.a2_sha256,
            runtime_max_seconds=900,
            timeout_stop_seconds=120,
        )
        result = SystemdManagerAdapter(connect_system_bus).create_holder(spec)
        assert isinstance(result, ControlOk), result

    def wait_stopped(self, timeout=60.0) -> dict[str, str]:
        assert wait_until(
            lambda: show(self.unit, "ActiveState")["ActiveState"] in {"failed", "inactive"}, timeout
        ), show(self.unit, "ActiveState", "SubState")
        return show(self.unit, "ExecMainStatus", "ExecStopPost", "InvocationID", "Result")

    def journal_text(self, invocation_id: str) -> str:
        return run("journalctl", "--no-pager", "-o", "cat", f"_SYSTEMD_INVOCATION_ID={invocation_id}").stdout

    def record(self, k: int) -> dict:
        path = STORE / "activation" / f"{self.id}.deact-{k}.json"
        info = path.lstat()
        assert (info.st_uid, info.st_gid, info.st_mode & 0o7777, info.st_nlink) == (0, 0, 0o444, 1)
        doc = parse_canonical(path.read_bytes())
        validate_record(doc)
        return doc

    def attempt_ops(self, k: int) -> list[str]:
        journal = Path(self.paths.attempt_dir(k)) / "journal"
        return [json.loads(line)["op"] for line in journal.read_bytes().splitlines() if line.endswith(b"}")]

    def clean(self) -> None:
        run("systemctl", "stop", self.unit)
        run("systemctl", "reset-failed", self.unit)
        for path in (self.paths.tree_p, self.paths.lock_dir):
            shutil.rmtree(path, ignore_errors=True)
        if self.fx is not None and not self.fx.rules_dir_preexists:
            shutil.rmtree(self.paths.polkit_run_dir, ignore_errors=True)
        else:
            Path(self.paths.rule).unlink(missing_ok=True)
        for entry in Path("/var/tmp").glob(f"{self.id}-*"):
            shutil.rmtree(entry, ignore_errors=True)


@pytest.fixture
def activation():
    assert not STORE.exists(), "record store left from an earlier run"
    polkit_preexisted = os.path.lexists("/run/polkit-1")  # e.g. from the boot-time tmpfiles.d fragment
    act = Activation()
    yield act
    act.clean()
    FOREIGN_RULE.unlink(missing_ok=True)
    shutil.rmtree(STORE, ignore_errors=True)
    for temp in Path("/run").glob(f".rp11-{act.id}-*"):
        shutil.rmtree(temp, ignore_errors=True)
    restart_polkit()
    assert wait_until(lambda: rp11_processes() == [], 10), rp11_processes()
    assert run("systemctl", "list-units", f"{act.id}*", "--all", "--no-legend").stdout.strip() == ""
    assert not os.path.lexists("/run/polkit-1") or polkit_preexisted or (
        act.fx is not None and act.fx.rules_dir_preexists
    )
    assert not list(Path("/var/tmp").glob(f"{act.id}-*"))
    assert not os.path.lexists(act.paths.tree_p) and not os.path.lexists(act.paths.lock_dir)
    assert run("systemctl", "is-active", "polkit.service").stdout.strip() == "active"


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------


def test_pid1_stop_post_reaches_st1_verified_and_removes_the_live_grant(activation):
    """RT-3 end to end: CL-G (grant.id) removes the live rule, CL-5/5b remove
    tree P, tree R, grant.id and K, PK/2 says not authorized for ubuntu through a
    real forked subject, the baseline recomputes equal, both records publish."""
    activation.prepare()
    activation.start_holder()
    shown = activation.wait_stopped()
    assert shown["ExecMainStatus"] == "21"  # hold: AM-0 finds the prepared objects present
    assert f"{ROLE_ARTIFACT} deact {activation.id} {activation.fx.a2_sha256} stop-post ;" in shown["ExecStopPost"]
    assert "code=exited ; status=0 }" in shown["ExecStopPost"], shown["ExecStopPost"]
    journal = activation.journal_text(shown["InvocationID"])
    assert f"rp11-cl st1-verified {activation.id} k=1" in journal
    assert "Traceback" not in journal
    p = activation.paths
    for path in (p.rule, p.pass_config, p.tree_p, p.grant_id, p.lock_dir):
        assert not os.path.lexists(path), path
    doc = activation.record(1)
    assert doc["outcome"] == "st1-verified" and doc["trigger"] == "stop-post"
    assert doc["release"]["first_rung"] == "cl-g" and doc["active_rule"]["class"] == "removed-earlier"
    assert doc["pk"]["outcome"] == "not-authorized" and doc["lock"]["mode"] == "held"
    assert doc["holder"]["invocation_id"] == shown["InvocationID"].replace("-", "")
    assert doc["st1"]["first_difference"] == "absent" and doc["st1"]["checks"]["baseline-equal"]
    assert all(c["reaped"] for c in doc["children"]["entries"]) and doc["children"]["entries"]
    assert doc["boot"]["run_fstype"] == "tmpfs"
    attempt = Path(p.attempt_dir(1))
    assert (attempt.stat().st_uid, attempt.stat().st_mode & 0o7777) == (0, 0o755)
    assert activation.attempt_ops(1)[:2] == ["run-start", "cl-g"] and activation.attempt_ops(1)[-1] == "run-end"
    assert activation.pk(PkMode.FIRST_DECISIVE).outcome is PkOutcome.NOT_AUTHORIZED


def test_without_grant_id_the_journal_based_removal_is_removed_verified(activation):
    activation.prepare(grant_id=False)
    activation.start_holder()
    shown = activation.wait_stopped()
    assert "status=0 }" in shown["ExecStopPost"]
    doc = activation.record(1)
    assert doc["active_rule"]["class"] == "removed-verified" and doc["release"]["first_rung"] == "stop-post"


def test_damaged_foreign_and_replaced_objects_are_retained_and_reported(activation):
    activation.prepare()
    p = activation.paths
    # replace the rule with another inode of the same bytes: still a live grant, not ours
    fresh = Path(p.rule + ".new")
    fresh.write_bytes(activation.fx.rule_bytes)
    os.chmod(fresh, 0o644)
    os.rename(fresh, p.rule)
    with open(p.pass_config, "r+b") as handle:  # damage pass-a.json in place
        handle.write(b"X")
    planted = Path(p.tree_p, "foreign-planted")
    planted.write_text("planted")
    os.chown(planted, OPERATOR.pw_uid, OPERATOR.pw_gid)
    activation.start_holder()
    shown = activation.wait_stopped()
    assert "status=1 }" in shown["ExecStopPost"], shown["ExecStopPost"]  # HARD STOP
    for path in (p.rule, p.pass_config, str(planted)):
        assert os.path.exists(path), path
    doc = activation.record(1)
    assert doc["outcome"] == "hard-stop"
    assert doc["grant_identity"]["cl_g"] == "kept-foreign"
    assert doc["active_rule"]["class"] == "present-foreign-unremoved"
    assert doc["pass_config"]["class"] == "present-damaged-unremoved"
    assert doc["pk"]["outcome"] == "unconfirmed" and doc["pk"]["reason"] == "still-authorized"
    residual = {r["path"]: r["class"] for r in doc["residual"]}
    assert residual[p.rule] == "present-foreign-unremoved"
    assert residual[p.pass_config] == "present-damaged-unremoved"
    assert residual[p.tree_p] == "present-nonempty-unremoved"
    assert "planted" not in json.dumps(doc).replace("foreign-planted", "")  # no content
    journal = activation.journal_text(shown["InvocationID"])
    assert f"rp11-cl hard-stop {activation.id}" in journal and "Traceback" not in journal


def test_an_interrupted_stop_post_is_recovered_by_a_restarted_attempt(activation):
    """IM-L L4: PID 1 kills the stop-post during its Polkit series (a foreign grant
    keeps the series running); the rule is already gone (CL-G). A second holder run
    of the same activation recovers to st1-verified."""
    activation.prepare()
    FOREIGN_RULE.write_bytes(RULE_BYTES % b"ubuntu")
    os.chmod(FOREIGN_RULE, 0o644)
    assert wait_until(lambda: activation.pk(PkMode.FIRST_DECISIVE).outcome is PkOutcome.AUTHORIZED, 10)
    activation.start_holder()
    journal = Path(activation.paths.attempt_dir(1)) / "journal"
    assert wait_until(lambda: journal.exists() and b'"op":"cl-g"' in journal.read_bytes(), 20)
    time.sleep(1.0)  # inside the 5 s series
    assert show(activation.unit, "ActiveState")["ActiveState"] == "deactivating"
    run("systemctl", "kill", "--kill-whom=all", "--signal=SIGKILL", activation.unit, check=True)
    activation.wait_stopped()
    assert "run-end" not in activation.attempt_ops(1)
    assert not os.path.lexists(activation.paths.rule)  # CL-G removed the grant before the kill
    assert not (STORE / "activation" / f"{activation.id}.deact-1.json").exists()
    assert wait_until(lambda: rp11_processes() == [], 10)  # the subject went with the cgroup
    FOREIGN_RULE.unlink()
    run("systemctl", "reset-failed", activation.unit, check=True)
    activation.start_holder()
    shown = activation.wait_stopped()
    assert "status=0 }" in shown["ExecStopPost"], shown["ExecStopPost"]
    doc = activation.record(2)
    assert doc["attempt"] == 2 and doc["outcome"] == "st1-verified"
    assert any(j["path"].endswith("deact-1-evidence/journal") for j in doc["journals"])


def test_concurrent_stop_posts_never_double_act(activation):
    activation.prepare()
    argv = [ROLE_INTERPRETER, "-I", "-S", ROLE_ARTIFACT, "deact", activation.id, activation.fx.a2_sha256, "stop-post"]
    procs = [subprocess.Popen(argv, stderr=subprocess.PIPE, env={}, cwd="/") for _ in range(2)]
    codes = sorted(proc.wait(timeout=60) for proc in procs)
    errs = [proc.stderr.read().decode() for proc in procs]
    assert 0 in codes and set(codes) <= {0, 1, 5}, (codes, errs)
    assert all("Traceback" not in e for e in errs)
    p = activation.paths
    for path in (p.rule, p.pass_config, p.tree_p, p.grant_id, p.lock_dir):
        assert not os.path.lexists(path), path
    modes = {activation.record(k)["lock"]["mode"] for k in (1, 2) if (STORE / "activation" / f"{activation.id}.deact-{k}.json").exists()}
    assert modes <= {"held", "degraded", "absent"}


def test_attempt_exhaustion_on_the_host_still_removes_the_grant(activation):
    activation.prepare()
    for k in range(1, 100):
        Path("/var/tmp", f"{activation.id}-deact-{k}-evidence").mkdir()
    argv = [ROLE_INTERPRETER, "-I", "-S", ROLE_ARTIFACT, "deact", activation.id, activation.fx.a2_sha256, "stop-post"]
    proc = subprocess.run(argv, capture_output=True, text=True, env={}, cwd="/")
    assert proc.returncode == 4, proc.stderr
    assert f"rp11-cl grant-priority {activation.id} rule=removed-earlier pk=not-authorized" in proc.stderr
    assert not os.path.lexists(activation.paths.rule)
    assert not list((STORE / "activation").iterdir())


def test_stop_post_without_any_activation_state_fails_closed(activation):
    """An activation id with no A-2, journal or objects: nothing to act on, never st1."""
    for sub in ("", "activation"):
        (STORE / sub).mkdir(mode=0o755, exist_ok=True)
    argv = [ROLE_INTERPRETER, "-I", "-S", ROLE_ARTIFACT, "deact", activation.id, "e" * 64, "stop-post"]
    proc = subprocess.run(argv, capture_output=True, text=True, env={}, cwd="/")
    assert proc.returncode == 1, proc.stderr
    assert f"rp11-cl hard-stop {activation.id} k=1" in proc.stderr and "failure=invalid-authority" in proc.stderr
    doc = activation.record(1)
    assert doc["h1_record"] == "absent" and doc["pk"]["outcome"] == "unconfirmed"
