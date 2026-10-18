"""RT-5 ``deact … attest`` through the real ``sudo -n`` launch preamble on the disposable host.

Real systemd, real Polkit, real ``/run`` (tmpfs), ``/var/tmp`` and
``/var/lib/freedom-blades-rp11``, and the production artifact built fresh from the
hash-pinned wheel. Every attest invocation is the exact operator vector,

    runuser -u ubuntu -- sudo -n /usr/bin/python3.14 -I -S \\
        /usr/local/libexec/freedom-blades-rp11/rp11_h1.py deact <id> <a2> attest

(``ubuntu`` is the disposable host's operator; ``sudo`` is the one launch preamble
outside the controlled tree). Activations are synthetic (the fixtures of
``test_route3_stop_post_host``): a live grant, tree P/R, ``grant.id`` and K are created
under the real runtime paths with no holder, so ``attest`` is the explicit recovery.
Live owners are test-only transient units named after the activation and removed at
teardown; nothing is installed as a production unit.

    sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test \\
        FREEDOM_RP11_WHEEL=/path/to/jeepney-0.9.0-py3-none-any.whl \\
        /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs \\
        tests/systemd_integration/test_route3_attest_host.py

The real-reboot proof is ``test_route3_attest_reboot_host.py``.

Polkit is restarted only by the harness when it creates ``/run/polkit-1/rules.d`` (a
directory that does not exist at boot on this host unless the ``tmpfiles.d`` fragment is
installed); ``attest`` itself never restarts or reloads it, and rule removal is observed
through polkitd's own directory watch (its ``MainPID`` is compared).
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from pathlib import Path

import pytest

import test_route3_stop_post_host as host  # noqa: F401  (applies the same disposable-host guards)
from test_route3_stop_post_host import (  # noqa: F401
    FOREIGN_RULE,
    OPERATOR,
    STORE,
    activation,
    artifact,
    run,
    show,
    wait_until,
)

from adapters.systemd.manager import ROLE_ARTIFACT, ROLE_INTERPRETER
from application.rp11.pk import PkMode, PkOutcome
from rp11_fixtures import RULE_BYTES

PRE_EXISTING = sorted(str(p) for p in Path("/var/tmp").glob("p5-r5-rp11-h0*"))


@pytest.fixture(scope="module", autouse=True)
def _untouched_preexisting_directories():
    yield
    assert sorted(str(p) for p in Path("/var/tmp").glob("p5-r5-rp11-h0*")) == PRE_EXISTING


def vector(act, a2: str | None = None) -> list[str]:
    return [ROLE_INTERPRETER, "-I", "-S", ROLE_ARTIFACT, "deact", act.id, a2 or act.fx.a2_sha256, "attest"]


def attest(act, a2: str | None = None) -> subprocess.CompletedProcess:
    """The operator's own attest: ``ubuntu`` through ``sudo -n`` (EX-1), empty environment."""
    return subprocess.run(
        ["runuser", "-u", "ubuntu", "--", "sudo", "-n", *vector(act, a2)],
        capture_output=True, text=True, cwd="/", env={"PATH": os.environ.get("PATH", "/usr/sbin:/usr/bin")},
    )


def deact_names(act) -> list[str]:
    return sorted(p.name for p in (STORE / "activation").glob(f"{act.id}.deact-*.json"))


def attempt_dirs(act) -> list[str]:
    return sorted(p.name for p in Path("/var/tmp").glob(f"{act.id}-deact-*"))


def snapshot(act) -> dict[str, tuple]:
    """Every object RT-5 could create, read-modify or remove for this activation."""
    found = {}
    for root in ("/run/polkit-1", act.paths.tree_p, act.paths.lock_dir, str(STORE), "/var/tmp"):
        base = Path(root)
        if not base.exists():
            continue
        for path in [base, *base.rglob("*")] if root != "/var/tmp" else [p for p in base.glob(f"{act.id}-*")]:
            try:
                info = path.lstat()
            except OSError:
                continue
            found[str(path)] = (info.st_mode, info.st_ino, info.st_size, info.st_mtime_ns)
    return found


# --- test-only owner units -------------------------------------------------------------


class Owners:
    """Transient units named like the activation's three owners (removed at teardown)."""

    def __init__(self, act) -> None:
        self.act = act
        self.names: set[str] = set()

    def service(self, name: str, state: str) -> None:
        props = {
            "active": [],
            "activating": ["--property=ExecStartPre=/usr/bin/sleep 600", "--property=TimeoutStartSec=900"],
            "deactivating": ["--property=ExecStop=/usr/bin/sleep 600", "--property=TimeoutStopSec=900"],
            "reloading": ["--property=ExecReload=/usr/bin/sleep 600"],
        }[state]
        done = run("systemd-run", "--quiet", "--no-block", f"--unit={name}", *props, "/usr/bin/sleep", "600")
        assert done.returncode == 0, done.stderr
        self.names.add(name)
        if state == "deactivating":
            assert wait_until(lambda: show(name, "ActiveState")["ActiveState"] == "active", 20)
            run("systemctl", "stop", "--no-block", name, check=True)
        elif state == "reloading":
            assert wait_until(lambda: show(name, "ActiveState")["ActiveState"] == "active", 20)
            run("systemctl", "reload", "--no-block", name, check=True)
        assert wait_until(lambda: show(name, "ActiveState")["ActiveState"] == state, 20), show(name, "ActiveState")

    def timer(self) -> None:
        stem = f"{self.act.id}-backstop"
        done = run("systemd-run", "--quiet", f"--unit={stem}", "--on-active=3600", "/usr/bin/true")
        assert done.returncode == 0, done.stderr
        self.names.update({f"{stem}.timer", f"{stem}.service"})
        assert show(f"{stem}.timer", "ActiveState")["ActiveState"] == "active"

    def release(self) -> None:
        for name in sorted(self.names):
            run("systemctl", "kill", "--signal=SIGKILL", name)
            run("systemctl", "stop", name)
            run("systemctl", "reset-failed", name)
        for name in sorted(self.names):
            assert wait_until(
                lambda n=name: show(n, "ActiveState")["ActiveState"] in {"inactive", "failed"}, 30
            ), (name, show(name, "ActiveState"))
        self.names.clear()


@pytest.fixture
def owners(activation):
    made = Owners(activation)
    yield made
    made.release()
    assert run("systemctl", "list-units", f"{activation.id}*", "--all", "--no-legend").stdout.strip() == ""


# ---------------------------------------------------------------------------
# RT5.PRE — a live owner refuses before any cleanup effect
# ---------------------------------------------------------------------------


def test_every_live_or_transitional_owner_refuses_before_any_cleanup_effect(activation, owners):
    """RT5.PRE.1: holder, backstop service and timer in each blocking state, through the real
    manager. The refusal exits 30, names the unit and the state, and changes nothing: the live
    grant, tree P/R, ``grant.id``, K, the store and ``/var/tmp`` are byte-for-byte as they were,
    Polkit is untouched and the owner keeps running."""
    activation.prepare()
    polkit_before = show("polkit.service", "MainPID")["MainPID"]
    before = snapshot(activation)
    cases = [
        ("holder", activation.unit, "active"),
        ("holder", activation.unit, "activating"),
        ("holder", activation.unit, "deactivating"),
        ("holder", activation.unit, "reloading"),
        ("service", f"{activation.id}-backstop.service", "active"),
        ("service", f"{activation.id}-backstop.service", "activating"),
        ("service", f"{activation.id}-backstop.service", "deactivating"),
        ("service", f"{activation.id}-backstop.service", "reloading"),
        ("timer", f"{activation.id}-backstop.timer", "active"),
    ]
    for role, unit, state in cases:
        if role == "timer":
            owners.timer()
        else:
            owners.service(unit, state)
        done = attest(activation)
        assert done.returncode == 30, (role, state, done.stderr)
        assert done.stderr.strip().splitlines()[-1] == (
            f"rp11-attest owner-active {activation.id} unit={role} state={state}"
        ), done.stderr
        assert "Traceback" not in done.stderr
        assert os.path.lexists(activation.paths.rule), (role, state)  # CL-G never ran
        assert show(unit, "ActiveState")["ActiveState"] == state  # nothing started, stopped or reset
        assert snapshot(activation) == before, (role, state)
        assert deact_names(activation) == [] and attempt_dirs(activation) == []
        owners.release()
    assert show("polkit.service", "MainPID")["MainPID"] == polkit_before
    assert activation.pk(PkMode.FIRST_DECISIVE).outcome is PkOutcome.AUTHORIZED  # the grant is still live


def test_unrelated_active_units_do_not_affect_the_decision(activation, owners):
    """A satisfied or blocking read is about one unit only: another activation's live units and
    a similarly named unit of this one are not owners."""
    activation.prepare()
    other = "rp11-act-20200101T000000Z-deadbeef"
    owners.service(f"{other}.service", "active")
    owners.service(f"{other}-backstop.service", "active")
    owners.service(f"{activation.id}-backstop-extra.service", "active")
    done = attest(activation)
    assert done.returncode == 0, done.stderr
    assert f"rp11-cl st1-verified {activation.id} k=1" in done.stderr
    assert show(f"{other}.service", "ActiveState")["ActiveState"] == "active"
    assert show(f"{activation.id}-backstop-extra.service", "ActiveState")["ActiveState"] == "active"


def test_an_unestablished_precondition_refuses_before_any_cleanup_effect(activation):
    """RT5.PRE.4: with the system bus unreachable (a private mount namespace hides its socket;
    nothing on the host is changed) no state is established: exit 31, nothing created or removed."""
    activation.prepare()
    before = snapshot(activation)
    inner = " ".join(["exec", *vector(activation)])
    done = subprocess.run(
        ["unshare", "--mount", "sh", "-c", f"mount --bind /dev/null /run/dbus/system_bus_socket && {inner}"],
        capture_output=True, text=True, cwd="/", env={"PATH": os.environ.get("PATH", "/usr/sbin:/usr/bin")},
    )
    assert done.returncode == 31, done.stderr
    assert done.stderr.strip().splitlines()[-1] == (
        f"rp11-attest precondition-unestablished {activation.id} unit=holder read=error"
    ), done.stderr
    assert snapshot(activation) == before and os.path.lexists(activation.paths.rule)
    assert deact_names(activation) == [] and attempt_dirs(activation) == []


# ---------------------------------------------------------------------------
# RT5.CL — same-boot cleanup through sudo
# ---------------------------------------------------------------------------


def test_same_boot_attest_runs_the_accepted_cleanup_to_st1_verified(activation):
    """RT5.CL.1/.2: no live owner; CL-G removes the live rule by ``grant.id``, CL-5/5b remove tree
    P/R, ``grant.id`` and K, real Polkit says not authorized, the baseline recomputes equal, both
    records publish; the evidence names ``attest`` and carries no provenance."""
    activation.prepare()
    polkit_before = show("polkit.service", "MainPID")["MainPID"]
    done = attest(activation)
    assert done.returncode == 0, done.stderr
    lines = done.stderr.strip().splitlines()
    assert lines[-1].startswith(f"rp11-cl st1-verified {activation.id} k=1 rule=removed-earlier pk=not-authorized"), lines
    assert any(line.startswith("rp11_h1: role=attest ") for line in lines) and "Traceback" not in done.stderr
    p = activation.paths
    for path in (p.rule, p.pass_config, p.tree_p, p.grant_id, p.lock_dir):
        assert not os.path.lexists(path), path
    doc = activation.record(1)
    assert doc["outcome"] == "st1-verified" and doc["trigger"] == "attest" and doc["helper"]["role"] == "attest"
    assert doc["release"]["first_rung"] == "cl-g" and doc["holder"]["invocation_id"] == "absent"
    assert doc["holder"]["active_state_at_start"] in {"inactive", "failed"}
    assert doc["pk"]["mode"] == "seek-not-authorized" and doc["pk"]["outcome"] == "not-authorized"
    assert doc["st1"]["checks"]["baseline-equal"] and doc["st1"]["checks"]["pk-not-authorized"]
    assert doc["children"]["entries"] and all(c["reaped"] for c in doc["children"]["entries"])
    assert doc["boot"]["pinned"] == doc["boot"]["act_boot"] == doc["boot"]["observed_at_start"]
    journal = Path(p.attempt_dir(1), "journal").read_bytes()
    first = json.loads(journal.splitlines()[0])
    assert first["op"] == "run-start" and first["trigger"] == "attest" and "provenance" not in first
    assert b"parent_pid" not in journal and activation.attempt_ops(1)[:2] == ["run-start", "cl-g"]
    assert activation.attempt_ops(1)[-1] == "run-end"
    assert activation.pk(PkMode.FIRST_DECISIVE).outcome is PkOutcome.NOT_AUTHORIZED
    assert show("polkit.service", "MainPID")["MainPID"] == polkit_before  # no restart for the removal
    # a repeat is a new attempt that finds everything removed earlier and verifies again
    again = attest(activation)
    assert again.returncode == 0 and f"rp11-cl st1-verified {activation.id} k=2 " in again.stderr, again.stderr
    second = activation.record(2)
    assert second["trigger"] == "attest" and second["active_rule"]["class"] in {"removed-earlier", "absent-before-removal"}
    assert deact_names(activation)[-1].endswith("deact-2.json")


def test_a_wrong_a2_operand_never_reaches_success(activation):
    activation.prepare()
    done = attest(activation, a2="e" * 64)
    assert done.returncode == 1 and "failure=invalid-authority" in done.stderr, done.stderr
    assert activation.record(1)["h1_record"] == "absent" and activation.record(1)["trigger"] == "attest"
    assert not os.path.lexists(activation.paths.rule)  # the attributable grant is removed by CL-G first


def test_damaged_foreign_and_replaced_objects_are_retained_and_reported(activation):
    """RT5.CL.3: nothing but an A1-intact object is removed; every other class is kept."""
    activation.prepare()
    p = activation.paths
    fresh = Path(p.rule + ".new")
    fresh.write_bytes(activation.fx.rule_bytes)
    os.chmod(fresh, 0o644)
    os.rename(fresh, p.rule)  # same bytes, another inode: a live grant that is not ours
    with open(p.pass_config, "r+b") as handle:
        handle.write(b"X")
    planted = Path(p.tree_p, "foreign-planted")
    planted.write_text("planted")
    os.chown(planted, OPERATOR.pw_uid, OPERATOR.pw_gid)
    done = attest(activation)
    assert done.returncode == 1, done.stderr
    for path in (p.rule, p.pass_config, str(planted)):
        assert os.path.exists(path), path
    doc = activation.record(1)
    assert doc["trigger"] == "attest" and doc["outcome"] == "hard-stop" and doc["st1"]["verified"] is False
    assert doc["active_rule"]["class"] == "present-foreign-unremoved"
    assert doc["pass_config"]["class"] == "present-damaged-unremoved"
    assert doc["pk"]["outcome"] == "unconfirmed" and doc["pk"]["reason"] == "still-authorized"
    residual = {r["path"]: r["class"] for r in doc["residual"]}
    assert residual[p.rule] == "present-foreign-unremoved" and residual[p.tree_p] == "present-nonempty-unremoved"
    assert f"rp11-cl hard-stop {activation.id}" in done.stderr


def test_an_unremovable_grant_is_kept_reported_and_never_success(activation):
    """RT5.CL.3: an A1-intact rule that cannot be unlinked (immutable) is ``grant-unremovable``."""
    activation.prepare()
    p = activation.paths
    flagged = run("chattr", "+i", p.rule)
    if flagged.returncode != 0:
        pytest.skip(f"this filesystem has no immutable attribute: {flagged.stderr.strip()}")
    try:
        done = attest(activation)
        assert done.returncode == 1, done.stderr
        assert os.path.exists(p.rule)
        doc = activation.record(1)
        assert doc["active_rule"]["class"] in {"grant-unremovable", "present-uninspected-unremoved"}
        assert doc["outcome"] == "hard-stop" and doc["pk"]["outcome"] == "unconfirmed"
    finally:
        run("chattr", "-i", p.rule)


def test_a_non_regular_object_in_place_of_the_pass_config_is_kept(activation):
    activation.prepare()
    p = activation.paths
    os.unlink(p.pass_config)
    os.mkfifo(p.pass_config, 0o644)
    done = attest(activation)
    assert done.returncode == 1, done.stderr
    assert os.path.exists(p.pass_config)
    assert activation.record(1)["pass_config"]["class"].startswith("present-")


def test_concurrent_attests_never_double_act_or_remove_a_foreign_object(activation):
    """RT5.CL.6: two simultaneous attests: one attempt number each, no record overwritten, a
    foreign file planted in tree P survives both."""
    activation.prepare()
    p = activation.paths
    planted = Path(p.tree_p, "foreign-planted")
    planted.write_text("planted")
    os.chown(planted, OPERATOR.pw_uid, OPERATOR.pw_gid)
    argv = ["runuser", "-u", "ubuntu", "--", "sudo", "-n", *vector(activation)]
    env = {"PATH": os.environ.get("PATH", "/usr/sbin:/usr/bin")}
    procs = [subprocess.Popen(argv, stderr=subprocess.PIPE, env=env, cwd="/") for _ in range(2)]
    codes = sorted(proc.wait(timeout=120) for proc in procs)
    errs = [proc.stderr.read().decode() for proc in procs]
    assert set(codes) <= {1, 5}, (codes, errs)  # the foreign file makes every complete pass a hard stop
    assert all("Traceback" not in e for e in errs)
    assert planted.read_text() == "planted"
    assert not os.path.lexists(p.rule) and not os.path.lexists(p.pass_config)
    names = deact_names(activation)
    assert names and len(set(names)) == len(names)
    assert {activation.record(int(n.split("deact-")[1].split(".")[0]))["trigger"] for n in names} == {"attest"}
    assert len(attempt_dirs(activation)) >= len(names)


def test_two_concurrent_clean_attests_publish_one_verified_record_each_never_the_same(activation):
    activation.prepare()
    argv = ["runuser", "-u", "ubuntu", "--", "sudo", "-n", *vector(activation)]
    env = {"PATH": os.environ.get("PATH", "/usr/sbin:/usr/bin")}
    procs = [subprocess.Popen(argv, stderr=subprocess.PIPE, env=env, cwd="/") for _ in range(2)]
    codes = sorted(proc.wait(timeout=120) for proc in procs)
    errs = [proc.stderr.read().decode() for proc in procs]
    assert 0 in codes and set(codes) <= {0, 1, 5}, (codes, errs)
    assert all("Traceback" not in e for e in errs)
    p = activation.paths
    for path in (p.rule, p.pass_config, p.tree_p, p.grant_id, p.lock_dir):
        assert not os.path.lexists(path), path
    names = deact_names(activation)
    assert len(names) == len(set(names)) == codes.count(0) + codes.count(1)


# ---------------------------------------------------------------------------
# interruption — default action, no handler, explicit later recovery
# ---------------------------------------------------------------------------


def _attest_python_pids(act) -> list[int]:
    found = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            argv = (entry / "cmdline").read_bytes().split(b"\0")
        except OSError:
            continue
        if argv and argv[0].endswith(b"python3.14") and act.id.encode() in argv and b"attest" in argv:
            found.append(int(entry.name))
    return found


def test_default_action_termination_leaves_no_false_record_and_is_recovered_explicitly(activation):
    """RT5.OUT.4: a foreign grant keeps the Polkit series running; the role is terminated by
    SIGTERM (its default action: no handler is installed) after CL-G. No terminal record or
    ``run-end`` exists; the attributable rule is already gone; no automatic action is taken; a
    later explicit attest reconciles from the earlier attempt's evidence and verifies."""
    activation.prepare()
    FOREIGN_RULE.write_bytes(RULE_BYTES % b"ubuntu")
    os.chmod(FOREIGN_RULE, 0o644)
    assert wait_until(lambda: activation.pk(PkMode.FIRST_DECISIVE).outcome is PkOutcome.AUTHORIZED, 10)
    argv = ["runuser", "-u", "ubuntu", "--", "sudo", "-n", *vector(activation)]
    proc = subprocess.Popen(argv, stderr=subprocess.PIPE, text=True, cwd="/",
                            env={"PATH": os.environ.get("PATH", "/usr/sbin:/usr/bin")})
    journal = Path(activation.paths.attempt_dir(1)) / "journal"
    assert wait_until(lambda: journal.exists() and b'"op":"cl-g"' in journal.read_bytes(), 20)
    time.sleep(1.0)  # inside the bounded Polkit series
    pids = _attest_python_pids(activation)
    assert len(pids) == 1, pids
    os.kill(pids[0], signal.SIGTERM)
    proc.wait(timeout=30)
    assert proc.returncode != 0
    assert "run-end" not in activation.attempt_ops(1)
    assert deact_names(activation) == []  # no false terminal record
    assert not os.path.lexists(activation.paths.rule)  # CL-G removed the attributable grant first
    # no automatic owner acts on a left-behind subject: it ends by its own bounded lifetime
    assert wait_until(lambda: host.rp11_processes() == [], 90), host.rp11_processes()
    FOREIGN_RULE.unlink()
    assert wait_until(lambda: activation.pk(PkMode.FIRST_DECISIVE).outcome is PkOutcome.NOT_AUTHORIZED, 15)
    done = attest(activation)
    assert done.returncode == 0, done.stderr
    doc = activation.record(2)
    assert doc["attempt"] == 2 and doc["outcome"] == "st1-verified" and doc["trigger"] == "attest"
    assert any(j["path"].endswith("deact-1-evidence/journal") for j in doc["journals"])
    assert doc["active_rule"]["class"] in {"absent-before-removal", "removed-earlier"}
