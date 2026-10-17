"""RT-1 ``consume`` through PID 1 on the disposable host.

The role runs as the real ``ExecStartPre=+`` of a disposable, fixed-name
``rp11-capture-pass-a.service`` (a test-only unit written under
``/run/systemd/system`` and removed at teardown; nothing is installed as a
production capture unit). The artifact is built fresh from the hash-pinned wheel;
the holder is created by SA-1 (or its DI-2 adapter) exactly as in the hold suite,
so the ACT journal, the ``act`` record and the live Polkit grant are the
holder's own output. The operator's ``start`` is authorized only by that grant
(``ubuntu`` without sudo). Synthetic data only.

    sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test \\
        FREEDOM_RP11_WHEEL=/path/to/jeepney-0.9.0-py3-none-any.whl \\
        /opt/freedom-blades/runtime/venv-web/bin/python -m pytest -q -rfEs \\
        tests/systemd_integration/test_route3_consume_host.py

Polkit is never restarted to make a removal observable: the series waits for the
daemon's own directory watch.
"""

from __future__ import annotations

import fcntl
import json
import os
import signal
import subprocess
import time
from pathlib import Path

import pytest

import test_route3_hold_host as hold_host  # noqa: F401  (applies the same disposable-host guards)
from test_route3_hold_host import (  # noqa: F401
    FOREIGN_RULE,
    activations,
    artifact,
    operator_start,
    polkit_pid,
    rp11_processes,
    run,
    show,
    wait_until,
)

from adapters.systemd.manager import ROLE_ARTIFACT, ROLE_INTERPRETER
from application.rp11.canonical import parse_canonical
from application.rp11.pk import PkMode, PkOutcome
from rp11_fixtures import RULE_BYTES

UNIT = "rp11-capture-pass-a.service"
VECTOR = [ROLE_INTERPRETER, "-I", "-S", ROLE_ARTIFACT, "consume"]
STOP_VECTOR = [ROLE_INTERPRETER, "-I", "-S", ROLE_ARTIFACT, "stop"]
PRE_EXISTING = sorted(str(p) for p in Path("/var/tmp").glob("p5-r5-rp11-h0*"))


@pytest.fixture(scope="module", autouse=True)
def _untouched_preexisting_directories():
    yield
    assert sorted(str(p) for p in Path("/var/tmp").glob("p5-r5-rp11-h0*")) == PRE_EXISTING


# --- the disposable capture unit ----------------------------------------------------------


def capture_service(act, *, timeout_start: int | None = None) -> str:
    """``[Service]`` body: RT-1 as ``ExecStartPre=+``; the main process creates the
    capture root, records the ``INVOCATION_ID`` it was started with and stays up."""
    root = act.capture_root
    main = (
        f"/usr/bin/sh -c 'mkdir -m 0700 {root} && echo $$INVOCATION_ID > {root}/main-invocation"
        " && exec /usr/bin/sleep 600'"
    )
    body = f"Type=exec\nExecStartPre=+{' '.join(VECTOR)}\n"
    if timeout_start is not None:
        body += f"TimeoutStartSec={timeout_start}\n"
    return body + f"ExecStart={main}\n"


def ready(activations, *, via_role: bool = False, **service):
    """A holder in HL: ``hold-start`` durable, the grant live, K released."""
    act = activations()
    act.since = int(time.time()) - 1
    act.prepare(service=capture_service(act, **service))
    if via_role:
        started = act.start_holder_via_role()
        assert started.returncode == 0, started.stderr
    else:
        act.start_holder()
    act.wait_op("hold-start")
    assert os.path.exists(act.paths.rule)
    return act


def unit_log(act) -> str:
    return run("journalctl", "--no-pager", "-o", "cat", "-u", UNIT, f"--since=@{act.since}").stdout


def consume_line(act) -> str:
    found = [line for line in unit_log(act).splitlines() if line.startswith("rp11-consume ")]
    assert len(found) == 1, (found, unit_log(act))
    return found[0]


def claim_dir(act) -> Path:
    return Path(act.paths.consume_dir)


def claim_lines(act) -> list[dict]:
    journal = claim_dir(act) / "journal"
    if not journal.exists():
        return []
    return [json.loads(line) for line in journal.read_bytes().splitlines() if line.endswith(b"}")]


def claim_ops(act) -> list[str]:
    return [doc["op"] for doc in claim_lines(act)]


def main_started(act) -> bool:
    return os.path.lexists(act.capture_root)


def assert_failed_start(act, *, status: int | None = None, result: str = "exit-code") -> None:
    """systemd reports a failed start and the main process was never executed (PO-21 (o))."""
    assert wait_until(lambda: show(UNIT, "ActiveState")["ActiveState"] == "failed", 30), show(UNIT, "ActiveState")
    state = show(UNIT, "Result", "ExecMainStartTimestampMonotonic", "ExecMainPID")
    assert state["Result"] == result, state
    assert state["ExecMainStartTimestampMonotonic"] == "0" and state["ExecMainPID"] == "0", state
    assert not main_started(act)
    if status is not None:
        assert f"status={status}/" in unit_log(act), unit_log(act)


def settle(act):
    """The holder ends and the existing stop-post cleanup runs; returns the two lines."""
    return act.wait_stopped(timeout=90)


# ---------------------------------------------------------------------------
# a complete lifecycle: SA-1, hold, RT-1 (PID 1), the main process, SA-2, cleanup
# ---------------------------------------------------------------------------


def test_a_complete_lifecycle_consumes_once_and_cleanup_reports_it(activations):
    """RT-1 end to end (inventory §5.1): CQ-0 … CQ-7 under PID 1 against the real manager,
    the real Polkit and the holder's own evidence; then SA-2 and the accepted cleanup."""
    act = ready(activations, via_role=True)
    polkit_before = polkit_pid()
    holder_invocation = show(act.unit, "InvocationID")["InvocationID"]
    tau0 = act.lines("hold-start")[0]["capture"]["inactive_enter_us"]
    assert act.lines("run-start")[0]["holder_invocation_id"] == holder_invocation
    rule_before = os.lstat(act.paths.rule)
    started = operator_start()  # authorized only by the live grant
    assert started.returncode == 0, (started.stderr, unit_log(act), claim_lines(act))
    assert wait_until(lambda: os.path.exists(f"{act.capture_root}/main-invocation"), 30), unit_log(act)
    # (1) consumed and run-end are durable, the grant is gone, the main process started
    ops = claim_ops(act)
    assert ops[:3] == ["run-start", "remove-intent", "removed"] and ops[-3:] == ["grant-check", "consumed", "run-end"]
    assert set(ops[3:-3]) <= {"child"}
    lines = claim_lines(act)
    assert lines[-1]["outcome"] == "consumed" and lines[-2]["pk_status"] == "not-authorized"
    assert not os.path.lexists(act.paths.rule)
    assert consume_line(act) == f"rp11-consume consumed {act.id} step=none class=none pk=not-authorized"
    assert show(UNIT, "ActiveState")["ActiveState"] == "active"
    # (4) the identities were checked against the real manager, inside RT-1's own start job
    main_invocation = Path(f"{act.capture_root}/main-invocation").read_text().strip()
    start = lines[0]
    assert start["invocation_id"] == main_invocation == show(UNIT, "InvocationID")["InvocationID"]
    assert lines[-2]["inactive_enter_us"] == tau0
    intent = lines[1]
    assert (intent["path"], intent["dev"], intent["ino"]) == (act.paths.rule, rule_before.st_dev, rule_before.st_ino)
    assert start["helper"]["role"] == "consume" and start["boot_id"] == act.fx.boot_id
    assert start["lock"]["object"]["path"] == act.paths.lock_dir
    # the claim: root 0755 directory, 0644 journal; K released
    info, jinfo = os.lstat(claim_dir(act)), os.lstat(claim_dir(act) / "journal")
    assert (info.st_uid, info.st_gid, info.st_mode & 0o7777) == (0, 0, 0o755)
    assert (jinfo.st_uid, jinfo.st_gid, jinfo.st_mode & 0o7777, jinfo.st_nlink) == (0, 0, 0o644, 1)
    fd = os.open(act.paths.lock_dir, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)  # RT-1 closed its descriptor (LD-4)
    finally:
        os.close(fd)
    # (5) the real PK/2 series is decisive only once Polkit has ceased authorizing ``start``
    assert operator_start().returncode != 0
    assert act.pk(PkMode.FIRST_DECISIVE).outcome is PkOutcome.NOT_AUTHORIZED
    assert polkit_pid() == polkit_before  # no restart to make the removal observable
    # a later same-boot attempt is refused without opening the existing claim
    before = (claim_dir(act) / "journal").read_bytes()
    again = run(*VECTOR)
    assert again.returncode == 23 and "consume-repeated" in again.stderr, again.stderr
    assert (claim_dir(act) / "journal").read_bytes() == before
    # SA-2 then the accepted cleanup
    stopped = run("runuser", "-u", "ubuntu", "--", "sudo", "-n", *STOP_VECTOR)
    assert stopped.returncode == 0, stopped.stderr
    hold, cl = settle(act)
    assert hold.startswith(f"rp11-hold hold-ended {act.id} step=HL detail=pass-ended"), act.log()
    assert cl.startswith(f"rp11-cl st1-verified {act.id} k=1"), cl
    deact = act.record("deact-1")
    assert deact["outcome"] == "st1-verified"
    assert deact["consume"] == {"class": "claimed", "outcome": "consumed"}
    assert claim_dir(act).exists()  # retained evidence: no procedure removes the claim
    assert not os.path.lexists(act.paths.rule) and not os.path.lexists(act.paths.tree_p)


# ---------------------------------------------------------------------------
# a failed RT-1 at each material phase: failed start, main process unexecuted
# ---------------------------------------------------------------------------


def _damage_pass_config(act):
    os.chmod(act.paths.pass_config, 0o600)


def _damage_k(act):
    os.chmod(act.paths.lock_dir, 0o750)


def _damage_rule(act):
    os.chmod(act.paths.rule, 0o664)  # the same inode, no longer A1-intact


def _plant_deact_evidence(act):
    """CQ-4 (RT1.CQ4.5) is false. Unlike a capture root or a claim this is not something HL
    watches, so the holder keeps holding and the grant stays live until RT-1 runs."""
    os.mkdir(f"/var/tmp/{act.id}-deact-1-evidence", 0o755)


PHASES = {
    # name: (arrange, exit status, line prefix, claim ops, rule survives, cleanup attempt)
    "cq0-unidentified": (_damage_pass_config, 21, "consume-unidentified unidentified step=CQ-0 class=pass-config", [], True, 1),
    "cq1-unusable-k": (_damage_k, 21, "consume-unidentified", [], True, 1),
    "cq3-damaged-rule": (_damage_rule, 27, "consume-failed", ["run-start", "consume-failed", "run-end"], True, 1),
    "cq4-deactivation-evidence": (
        _plant_deact_evidence, 26, "consume-precondition",
        ["run-start", "remove-intent", "removed", "consume-failed", "run-end"], False, 2,
    ),
}


@pytest.mark.parametrize("phase", sorted(PHASES))
def test_a_failed_consume_leaves_the_main_process_unexecuted(activations, phase):
    arrange, status, prefix, expected_ops, rule_survives, attempt = PHASES[phase]
    act = ready(activations)
    arrange(act)
    started = operator_start()  # the grant authorizes the job; RT-1 then refuses it
    assert started.returncode != 0
    assert_failed_start(act, status=status, result="exit-code")
    assert prefix in consume_line(act), unit_log(act)
    assert claim_ops(act) == expected_ops
    if not rule_survives:  # RT-1 removed it (journaled); a rule it never touched is IGR's to remove later
        assert not os.path.lexists(act.paths.rule)
    elif phase == "cq3-damaged-rule":  # kept by RT-1 and by IGR alike
        assert os.path.lexists(act.paths.rule)
    if phase == "cq1-unusable-k":
        os.chmod(act.paths.lock_dir, 0o700)
    # recoverable by the existing cleanup path
    hold, cl = settle(act)
    assert cl.startswith("rp11-cl "), cl
    assert act.has_record(f"deact-{attempt}")
    if phase == "cq3-damaged-rule":
        assert act.record("deact-1")["active_rule"]["class"] == "present-damaged-unremoved"
    else:
        assert not os.path.lexists(act.paths.rule)


def test_a_var_tmp_that_is_not_root_1777_makes_no_claim_but_the_grant_is_still_removed(activations):
    """RT1.CQ2.1 / grant priority: no claim could be made, yet the live attributable grant is
    removed and checked before the attempt fails with ``consume-claim-failed``."""
    act = ready(activations)
    os.chmod("/var/tmp", 0o755)
    try:
        assert operator_start().returncode != 0
        assert_failed_start(act, status=24)
    finally:
        os.chmod("/var/tmp", 0o1777)
    line = f"rp11-consume consume-claim-failed {act.id} step=CQ-2 class=claim-not-made pk=not-authorized"
    assert line in consume_line(act)
    assert not claim_dir(act).exists() and not os.path.lexists(act.paths.rule)
    settle(act)


def test_a_held_k_is_busy_at_once_and_fails_the_start(activations):
    act = ready(activations)
    fd = os.open(act.paths.lock_dir, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        began = time.monotonic()
        assert operator_start().returncode != 0
        assert time.monotonic() - began < 10  # never waited for K
        assert_failed_start(act, status=22)
        assert f"rp11-consume consume-busy {act.id} step=CQ-1 class=k-held" in consume_line(act)
        assert not claim_dir(act).exists() and os.path.lexists(act.paths.rule)
    finally:
        os.close(fd)
    settle(act)


def test_a_grant_that_is_still_authorizing_after_removal_fails_the_start(activations):
    """CQ-5: another rule keeps Polkit authorizing ``start``; the removed pathname proves nothing."""
    act = ready(activations)
    FOREIGN_RULE.write_bytes(RULE_BYTES % b"ubuntu")
    os.chmod(FOREIGN_RULE, 0o644)
    try:
        assert operator_start().returncode != 0
        assert_failed_start(act, status=27)
        assert f"rp11-consume consume-failed {act.id} step=CQ-5 class=removed-unconfirmed" in consume_line(act)
        ops = claim_ops(act)
        assert ops[:3] == ["run-start", "remove-intent", "removed"] and "consumed" not in ops
        check = [d for d in claim_lines(act) if d["op"] == "grant-check"][0]
        assert (check["outcome"], check["reason"]) == ("unconfirmed", "still-authorized")
        assert not os.path.lexists(act.paths.rule)
    finally:
        FOREIGN_RULE.unlink(missing_ok=True)
    settle(act)


# ---------------------------------------------------------------------------
# two concurrent consumes: one claim, one removal
# ---------------------------------------------------------------------------


def test_two_concurrent_roles_cannot_both_consume_and_the_real_manager_is_read(activations):
    """Two root consumes started together outside any start job. The capture unit is not
    ``activating`` so neither can pass CQ-4, but exactly one wins the barrier and removes the
    grant; the other is refused at K or at the barrier. Both ran with no INVOCATION_ID."""
    act = ready(activations)
    procs = [subprocess.Popen(VECTOR, stderr=subprocess.PIPE, text=True, env={}) for _ in range(2)]
    results = [(p.wait(), p.stderr.read()) for p in procs]
    codes = sorted(code for code, _ in results)
    assert codes[0] in (22, 23, 26) and codes[1] in (22, 23, 26) and codes.count(26) == 1, results
    assert claim_ops(act).count("run-start") == 1 and claim_ops(act).count("removed") == 1
    assert claim_lines(act)[0]["invocation_id"] == "absent"
    assert [d for d in claim_lines(act) if d["op"] == "consume-failed"][0]["class"] == "capture"  # DI-1 vs the manager
    assert not os.path.lexists(act.paths.rule)
    settle(act)


def test_parallel_start_requests_run_one_exec_start_pre(activations):
    act = ready(activations)
    jobs = [subprocess.Popen(["runuser", "-u", "ubuntu", "--", "systemctl", "--no-ask-password", "start", UNIT],
                             stderr=subprocess.PIPE, text=True) for _ in range(2)]
    codes = [job.wait() for job in jobs]
    assert 0 in codes
    assert wait_until(lambda: os.path.exists(f"{act.capture_root}/main-invocation"), 30), unit_log(act)
    assert claim_ops(act).count("run-start") == 1 and claim_ops(act).count("consumed") == 1
    run("systemctl", "stop", UNIT, check=True)
    settle(act)


# ---------------------------------------------------------------------------
# termination and start timeout: the accepted one-shot / residual behaviour
# ---------------------------------------------------------------------------


def _consume_pids() -> list[int]:
    found = []
    for entry in Path("/proc").iterdir():
        if entry.name.isdigit():
            try:
                argv = (entry / "cmdline").read_bytes().split(b"\0")
            except OSError:
                continue
            if b"rp11_h1.py" in b" ".join(argv) and argv[-2:-1] == [b"consume"]:
                found.append(int(entry.name))
    return found


def _slow_consume(act):
    """A foreign rule keeps CQ-5's series running (about 5 s) after the grant is removed."""
    FOREIGN_RULE.write_bytes(RULE_BYTES % b"ubuntu")
    os.chmod(FOREIGN_RULE, 0o644)
    return subprocess.Popen(["runuser", "-u", "ubuntu", "--", "systemctl", "--no-ask-password", "start", UNIT],
                            stderr=subprocess.PIPE, text=True)


def test_sigterm_during_the_authorization_series_fails_the_start_and_is_recoverable(activations):
    act = ready(activations)
    job = _slow_consume(act)
    try:
        assert wait_until(lambda: "removed" in claim_ops(act), 30), unit_log(act)
        pids = _consume_pids()
        assert len(pids) == 1, pids
        os.kill(pids[0], signal.SIGTERM)  # the default action: no handler, no exit status of its own
    finally:
        FOREIGN_RULE.unlink(missing_ok=True)
    assert job.wait() != 0
    assert_failed_start(act, result="signal")
    ops = claim_ops(act)
    assert ops[:3] == ["run-start", "remove-intent", "removed"] and "consumed" not in ops and "run-end" not in ops
    assert not [line for line in unit_log(act).splitlines() if line.startswith("rp11-consume ")]
    assert wait_until(lambda: _consume_pids() == [], 10)
    hold, cl = settle(act)
    assert cl.startswith("rp11-cl "), cl
    assert not os.path.lexists(act.paths.rule) and act.has_record("deact-1")
    assert act.record("deact-1")["consume"] == {"class": "claimed", "outcome": "incomplete"}
    # the claim is a one-shot barrier: another start in this boot is refused
    assert claim_dir(act).exists()


def test_a_start_timeout_terminates_consume_and_the_main_process_never_runs(activations):
    """N1 is a necessary condition only: here ``TimeoutStartSec`` (3 s) is shorter than the
    series (about 5 s), so PID 1, not RT-1, ends the attempt."""
    act = ready(activations, timeout_start=3)
    job = _slow_consume(act)
    try:
        assert job.wait() != 0
    finally:
        FOREIGN_RULE.unlink(missing_ok=True)
    assert_failed_start(act, result="timeout")
    assert "consumed" not in claim_ops(act) and "run-end" not in claim_ops(act)
    assert wait_until(lambda: _consume_pids() == [], 10)
    hold, cl = settle(act)
    assert cl.startswith("rp11-cl "), cl
    assert not os.path.lexists(act.paths.rule) and act.has_record("deact-1")


# ---------------------------------------------------------------------------
# the first image under PID 1
# ---------------------------------------------------------------------------


def test_an_operand_or_alias_is_refused_before_any_state_operation(activations):
    act = ready(activations)
    for tail in (["x"], [act.id], ["--now"], ["consume"], ["CONSUME"]):
        proc = run(*VECTOR, *tail)
        assert proc.returncode == 64 and "not an accepted role vector" in proc.stderr, (tail, proc.stderr)
    assert not claim_dir(act).exists() and os.path.lexists(act.paths.rule)
    assert run("systemctl", "is-active", UNIT).stdout.strip() != "active"
    run("systemctl", "stop", act.unit, check=True)
    settle(act)


def test_hostile_invocation_ids_are_refused_before_any_state_operation(activations):
    act = ready(activations)
    for value in ("not-hex", "A" * 32, "a" * 31, "", "a" * 100_000):
        proc = subprocess.run(VECTOR, capture_output=True, text=True, env={"INVOCATION_ID": value})
        assert proc.returncode == 64 and "malformed or duplicate INVOCATION_ID" in proc.stderr
    assert not claim_dir(act).exists() and os.path.lexists(act.paths.rule)
    run("systemctl", "stop", act.unit, check=True)
    settle(act)
