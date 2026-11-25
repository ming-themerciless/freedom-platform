"""Opt-in timing measurement of the Pass A plan on ``oracle-test`` (G7).

Skipped unless the host name is ``Test`` (the disposable host), ``RP11_PASS_A_MEASURE_OUT``
is set and exactly one mode is selected:

* **synthetic** (``RP11_PASS_A_SYNTH_CHECKOUT``): the plan's argv and environments rebased
  onto a *scratch* clone, with a scratch capture root per round;
* **real identity and paths** (``RP11_PASS_A_MEASURE_REAL=1``): the plan unchanged, run as
  the locked ``capture`` account against the acquired checkout, with the capture roots
  ``capture-a``/``capture-b`` used alternately. Before any round the account, the parent
  contract and the absence of both leaves are checked; each leaf a round creates is checked
  after X-1 and removed after that round, so both end absent. A leaf that already exists,
  including one created between the check and X-1, is refused by X-1 and left.

  Each real-path test takes a non-blocking exclusive ``flock`` on the capture parent
  directory itself (no lock file) before its first precondition or leaf check and holds it
  over every round and cleanup; a second real run fails before creating or removing
  anything. This closes the check-to-``rmtree`` window **between instances of this
  harness**. The lock is advisory: it does not restrain root, a manual command, another
  program or an older copy of this harness that does not take it. The device and inode
  comparison before removal is defense in depth only; it is not atomic with ``rmtree``, and
  a filesystem may reuse an inode number.

Neither mode is an operational pass: ``run_pass_a`` is **not** called, no consume journal or
activation is used or needed, and the captured evidence is discarded. The harness drives the
same ``CaptureSession`` (real armed launcher) act by act and judges every exit with the
plan's own ``plan.exit_policy()``: a status the plan does not list, or any signal, stops
the session, and every recorded outcome is asserted against that policy again, so a round
that "completed" with an unexpected exit is refused, never sampled. The deadlines are
generous test values unless ``RP11_PASS_A_MEASURE_PLAN_TIMEOUTS=1`` keeps the plan's own.
The output is a JSON statement of timings, sizes and the exit of every step. An existing
output file is refused before any round, so earlier evidence is never overwritten.

One *sample* of a class is the slowest step of that class in one whole run, so a sample is
already a worst case within its round.
"""

from __future__ import annotations

import contextlib
import fcntl
import json
import os
import pwd
import shutil
import socket
import stat
import subprocess
import sys
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from tools.phase_5_0_evidence.capture_contract import (
    RP11_SOURCES,
    X3_SUCCEEDED,
    X4_VALID,
    ExitOutcome,
    capture_tool_sha256,
)
from tests.phase_5_0_evidence.rp11_fixtures import (
    TOOL_SHA256,
    FaultFilesystem,
    FixedClock,
    INVOCATION_ID,
    Host,
    rp11_release_descriptors,  # noqa: F401 - autouse fixture, active by import
)
from tools.phase_5_0_evidence.execution import pass_a_plan as plan_module
from tools.phase_5_0_evidence.execution.boundary import StreamCaptureLauncher
from tools.phase_5_0_evidence.execution.capture_mechanism import (
    ActRequest,
    GenesisRequest,
    SessionState,
    SystemUtcClock,
    create_capture_session,
)
from tools.phase_5_0_evidence.execution.capture_store import PosixCaptureFilesystem, RootPolicy

OUT = os.environ.get("RP11_PASS_A_MEASURE_OUT")
SYNTH = os.environ.get("RP11_PASS_A_SYNTH_CHECKOUT")
REAL = os.environ.get("RP11_PASS_A_MEASURE_REAL") == "1"
PLAN_TIMEOUTS = os.environ.get("RP11_PASS_A_MEASURE_PLAN_TIMEOUTS") == "1"
ROUNDS = int(os.environ.get("RP11_PASS_A_MEASURE_ROUNDS", "12"))
GENEROUS_SECONDS = 900.0

LABEL = os.environ.get("RP11_PASS_A_MEASURE_LABEL", "unlabelled")

needs_host = pytest.mark.skipif(
    not (OUT and bool(SYNTH) != REAL and socket.gethostname() == "Test"),
    reason=(
        "opt-in measurement: needs host 'Test', RP11_PASS_A_MEASURE_OUT and exactly one of "
        "RP11_PASS_A_SYNTH_CHECKOUT or RP11_PASS_A_MEASURE_REAL=1"
    ),
)


class UnexpectedOutcome(AssertionError):
    """A recorded step outcome the plan's exit policy does not accept."""


def verify_recorded_outcomes(plan: plan_module.PassAPlan, rows: list[dict]) -> None:
    """Refuse unless every step ran, ended cleanly and exited as the plan expects.

    The outcome is judged by ``plan.exit_policy()``, the same callable the operational pass
    would use, so the measurement and the pass cannot disagree on what is expected."""
    if len(rows) != len(plan.steps):
        raise UnexpectedOutcome(f"{len(rows)} launches for {len(plan.steps)} steps")
    policy = plan.exit_policy()
    acts = {act.step_or_case_id: act for act in plan.acts()}
    for step, row in zip(plan.steps, rows, strict=True):
        if row["returncode"] is None or row["timed_out"] or row["bound_exceeded"] or not row["streams_complete"]:
            raise UnexpectedOutcome(f"{step.step_id}: not a clean exit: {row}")
        if not policy(acts[step.step_id], ExitOutcome.from_returncode(row["returncode"])):
            raise UnexpectedOutcome(f"{step.step_id}: exit {row['returncode']} not in {step.accepted_exits}")


@dataclass
class TimingLauncher:
    inner: StreamCaptureLauncher = field(default_factory=lambda: StreamCaptureLauncher(armed=True))
    rows: list[dict] = field(default_factory=list)
    pending: list[str] = field(default_factory=list)

    def launch(self, argv, **keywords):  # type: ignore[no-untyped-def]
        started = time.monotonic()
        result = self.inner.launch(argv, **keywords)
        self.rows.append(
            {
                "seconds": time.monotonic() - started,
                "returncode": result.returncode,
                "stdout_bytes": result.stdout_bytes,
                "stderr_bytes": result.stderr_bytes,
                "timed_out": result.timed_out,
                "bound_exceeded": result.bound_exceeded,
                "streams_complete": result.streams_complete,
            }
        )
        return result


def _rebase(text: str) -> str:
    return text.replace(plan_module.SOURCE_CHECKOUT, SYNTH)


def _measured_acts(plan: plan_module.PassAPlan) -> tuple[ActRequest, ...]:
    """The plan's acts: rebased onto the scratch clone in synthetic mode only; a generous
    deadline unless the plan's own timeouts are being confirmed."""
    rebase = (lambda text: text) if REAL else _rebase
    return tuple(
        ActRequest(
            step_or_case_id=a.step_or_case_id,
            argv=tuple(rebase(x) for x in a.argv),
            environment={k: rebase(v) for k, v in a.environment.items()},
            stream_bound_bytes=a.stream_bound_bytes,
            timeout_seconds=a.timeout_seconds if PLAN_TIMEOUTS else GENEROUS_SECONDS,
            drain_seconds=a.drain_seconds,
        )
        for a in plan.acts()
    )


# --- real identity and paths --------------------------------------------------------------


def _observe(path: str) -> plan_module.ObservedDirectory | None:
    try:
        facts = os.lstat(path)
    except FileNotFoundError:
        return None
    return plan_module.ObservedDirectory(path, facts.st_uid, facts.st_gid, facts.st_mode)


class RealPathsBusy(AssertionError):
    """Another holder has the capture parent's lock."""


@contextlib.contextmanager
def _exclusive_owner(directory: str) -> Iterator[None]:
    """Hold an exclusive advisory lock on ``directory`` itself, or refuse at once.

    The kernel drops it when the descriptor closes, including when the process dies. The
    descriptor is close-on-exec, so no captured command keeps the lock."""
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RealPathsBusy(f"{directory}: another real measurement owns it") from None
        yield
    finally:
        os.close(fd)


def _real_path_ownership() -> contextlib.AbstractContextManager[None]:
    """The lock every test that may touch the real leaves holds; nothing in synthetic mode."""
    return _exclusive_owner(plan_module.CAPTURE_PARENT) if REAL else contextlib.nullcontext()


def _require_real_preconditions() -> None:
    """Refuse before any capture unless this process is ``capture`` and the G4 state holds."""
    account = pwd.getpwnam(plan_module.CAPTURE_IDENTITY.name)
    assert account.pw_uid != 0 and os.getresuid() == (account.pw_uid,) * 3, "not the capture account"
    assert os.getresgid() == (account.pw_gid,) * 3, "not the capture group"
    assert set(os.getgroups()) <= {account.pw_gid}, "supplementary groups"
    assert account.pw_shell in plan_module.CAPTURE_IDENTITY.login_shells, "login shell"
    parent = _observe(plan_module.CAPTURE_PARENT)
    assert parent is not None
    assert plan_module.parent_problems(parent, account.pw_gid) == ()
    for leaf in plan_module.PARENT_CONTRACT.leaves:
        assert plan_module.leaf_absent_problems(_observe(leaf)) == (), f"{leaf} is present"


class CreationRecordingFilesystem(PosixCaptureFilesystem):
    """The real filesystem, remembering which capture-root leaf its own ``mkdir`` created."""

    created_root: tuple[int, int] | None = None

    def mkdir_exclusive(self, dir_fd: int, name: str, mode: int, *, stage: str) -> None:
        super().mkdir_exclusive(dir_fd, name, mode, stage=stage)  # raises if it exists
        if stage == "X-1:create-root":
            facts = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
            self.created_root = (facts.st_dev, facts.st_ino)


def _remove_created_leaf(
    path: str,
    created: tuple[int, int] | None,
    leaves: tuple[str, ...] = plan_module.PARENT_CONTRACT.leaves,
) -> bool:
    """Remove ``path`` if its device and inode match ``created``; ``None`` (this session
    created nothing) removes nothing, and a mismatch is refused.

    The comparison and ``rmtree`` are separate calls. On the real paths the caller must hold
    ``_real_path_ownership()``, which excludes other instances of this harness only."""
    assert path in leaves
    if created is None:
        return False
    try:
        facts = os.lstat(path)
    except FileNotFoundError:
        return False
    assert stat.S_ISDIR(facts.st_mode) and facts.st_uid == os.geteuid(), f"{path}: not ours"
    assert (facts.st_dev, facts.st_ino) == created, f"{path}: replaced since X-1"
    shutil.rmtree(path)
    assert _observe(path) is None
    return True


def _refuse_existing_output(path: str) -> None:
    assert not os.path.lexists(path), f"{path} exists; earlier evidence is never overwritten"


def _genesis(plan: plan_module.PassAPlan, round_dir: Path, leaf: str):  # type: ignore[no-untyped-def]
    if not REAL:
        host = Host.under(round_dir)
        return GenesisRequest(
            capture_root=host.root(),
            pass_id=plan_module.PASS_ID,
            tool_sha256=TOOL_SHA256,
            invocation_id=INVOCATION_ID,
            policy=host.policy(),
        )
    checkout = Path(plan_module.SOURCE_CHECKOUT)
    tool = capture_tool_sha256({name: (checkout / name).read_bytes() for name in RP11_SOURCES})
    request = plan.genesis_request(invocation_id=INVOCATION_ID, tool_sha256=tool)
    if leaf == plan_module.CAPTURE_ROOT_A:
        return request
    return GenesisRequest(
        capture_root=leaf,
        pass_id=request.pass_id,
        tool_sha256=tool,
        invocation_id=INVOCATION_ID,
        policy=plan_module.root_policy((plan_module.CAPTURE_ROOT_A,)),
    )


@dataclass
class Round:
    completed: bool
    reason: str | None
    launcher: TimingLauncher
    record: dict


def _run_round(
    plan: plan_module.PassAPlan,
    acts: tuple[ActRequest, ...],
    round_dir: Path,
    leaf: str = plan_module.CAPTURE_ROOT_A,
) -> Round:
    """Drive one capture session over ``acts`` without ``run_pass_a``; stop at the first
    unadmitted act or unaccepted exit, and finalize once."""
    round_dir.mkdir()
    if REAL:
        assert plan_module.leaf_absent_problems(_observe(leaf)) == (), f"{leaf} is present"
    request = _genesis(plan, round_dir, leaf)
    launcher = TimingLauncher()
    policy = plan.exit_policy()
    record: dict = {"capture_root": request.capture_root}
    run_act_seconds: list[float] = []
    reason: str | None = None
    filesystem = CreationRecordingFilesystem() if REAL else FaultFilesystem()
    started = time.monotonic()
    try:
        session = create_capture_session(
            request,
            filesystem=filesystem,
            launcher=launcher,
            clock=SystemUtcClock() if REAL else FixedClock(),
        )
        record["genesis_seconds"] = time.monotonic() - started
        assert session.state is SessionState.OPEN, session.state
        if REAL:
            created = _observe(leaf)
            account = pwd.getpwnam(plan_module.CAPTURE_IDENTITY.name)
            assert plan_module.created_leaf_problems(created, account.pw_uid) == ()
            record["leaf_after_x1"] = {"uid": created.uid, "gid": created.gid, "mode": oct(created.mode)}
        for act in acts:
            before = time.monotonic()
            outcome = session.run_act(act)
            run_act_seconds.append(time.monotonic() - before)
            if outcome.failure is not None or not outcome.admitted:
                reason = f"{act.step_or_case_id}: {outcome.failure.classification}"
                break
            if policy(act, outcome.exit) is not True:
                reason = f"{act.step_or_case_id}: unacceptable-exit"
                before = time.monotonic()
                final = session.stop(reason="unacceptable-exit", step_or_case_id=act.step_or_case_id)
                record["finalization_seconds"] = time.monotonic() - before
                break
        else:
            before = time.monotonic()
            final = session.complete()
            record["finalization_seconds"] = time.monotonic() - before
            if not (final.x3_outcome == X3_SUCCEEDED and final.x4_validity == X4_VALID):
                reason = f"finalization: {final.x3_outcome} {final.x4_validity}"
            record["x3"], record["x4"] = final.x3_outcome, final.x4_validity
            record["capture_index_sha256"] = session.binding().capture_index_sha256
        record["wall_seconds"] = time.monotonic() - started
        record["run_act_seconds"] = run_act_seconds
    finally:
        if REAL:
            _remove_created_leaf(leaf, filesystem.created_root)
    return Round(reason is None and len(run_act_seconds) == len(acts), reason, launcher, record)


# --- controls: the verifier and the policy refuse what they must --------------------------


def _clean_rows(plan: plan_module.PassAPlan) -> list[dict]:
    return [
        {"returncode": step.accepted_exits[0], "timed_out": False, "bound_exceeded": False, "streams_complete": True}
        for step in plan.steps
    ]


def test_control_the_verifier_accepts_the_expected_exits_and_refuses_every_departure() -> None:
    plan = plan_module.build_pass_a_plan(include_corroboration=True)
    verify_recorded_outcomes(plan, _clean_rows(plan))
    expecting_nonzero = next(i for i, st in enumerate(plan.steps) if 0 not in st.accepted_exits)
    expecting_zero = next(i for i, st in enumerate(plan.steps) if st.accepted_exits == (0,))
    for index, bad in (
        (expecting_nonzero, 0),  # the expected failure did not happen
        (expecting_zero, 1),  # an unexpected failure
        (expecting_zero, -9),  # killed by a signal
        (expecting_zero, -15),
    ):
        rows = _clean_rows(plan)
        rows[index]["returncode"] = bad
        with pytest.raises(UnexpectedOutcome):
            verify_recorded_outcomes(plan, rows)
    for key, value in (("timed_out", True), ("bound_exceeded", True), ("streams_complete", False), ("returncode", None)):
        rows = _clean_rows(plan)
        rows[0][key] = value
        with pytest.raises(UnexpectedOutcome):
            verify_recorded_outcomes(plan, rows)
    with pytest.raises(UnexpectedOutcome):
        verify_recorded_outcomes(plan, _clean_rows(plan)[:-1])


# --- controls: cleanup removes only what the session created, output is never overwritten ---


def _session_over(leaf: Path, filesystem: CreationRecordingFilesystem):  # type: ignore[no-untyped-def]
    request = GenesisRequest(
        capture_root=str(leaf),
        pass_id=plan_module.PASS_ID,
        tool_sha256=TOOL_SHA256,
        invocation_id=INVOCATION_ID,
        policy=RootPolicy(()),  # a temporary directory stands in for the capture parent
    )
    return create_capture_session(
        request, filesystem=filesystem, launcher=TimingLauncher(), clock=SystemUtcClock()
    )


def test_control_a_leaf_the_session_did_not_create_is_never_removed(tmp_path: Path) -> None:
    """The race the pre-round check cannot close: the leaf appears before X-1."""
    leaf = tmp_path / "capture-a"
    leaf.mkdir(mode=0o700)
    (leaf / "sentinel").write_text("someone else's")
    filesystem = CreationRecordingFilesystem()
    session = _session_over(leaf, filesystem)
    assert session.state is SessionState.NO_GENESIS and filesystem.created_root is None
    assert _remove_created_leaf(str(leaf), filesystem.created_root, (str(leaf),)) is False
    assert (leaf / "sentinel").read_text() == "someone else's"


def test_control_the_leaf_the_session_created_is_removed(tmp_path: Path) -> None:
    leaf = tmp_path / "capture-a"
    filesystem = CreationRecordingFilesystem()
    session = _session_over(leaf, filesystem)
    assert session.state is SessionState.OPEN and filesystem.created_root is not None
    session.complete()
    assert _remove_created_leaf(str(leaf), filesystem.created_root, (str(leaf),)) is True
    assert not os.path.lexists(leaf)


def test_control_a_replaced_leaf_and_an_unlisted_path_are_refused(tmp_path: Path) -> None:
    leaf = tmp_path / "capture-a"
    filesystem = CreationRecordingFilesystem()
    _session_over(leaf, filesystem).complete()
    leaf.rename(tmp_path / "original")  # still exists, so its inode cannot be reused
    leaf.mkdir(mode=0o700)
    with pytest.raises(AssertionError, match="replaced since X-1"):
        _remove_created_leaf(str(leaf), filesystem.created_root, (str(leaf),))
    with pytest.raises(AssertionError):
        _remove_created_leaf(str(tmp_path / "original"), filesystem.created_root, (str(leaf),))
    assert leaf.is_dir() and (tmp_path / "original").is_dir()


def test_control_an_existing_output_file_is_refused(tmp_path: Path) -> None:
    out = tmp_path / "quiet.json"
    _refuse_existing_output(str(out))
    out.write_text("evidence")
    with pytest.raises(AssertionError, match="never overwritten"):
        _refuse_existing_output(str(out))


# --- controls: real-path runs are serialized by the capture parent's lock ------------------


def test_control_the_parent_lock_refuses_a_second_owner_and_is_released(tmp_path: Path) -> None:
    parent = str(tmp_path)
    with _exclusive_owner(parent):
        with pytest.raises(RealPathsBusy), _exclusive_owner(parent):
            pass
        with pytest.raises(RealPathsBusy), _exclusive_owner(parent):  # the refusal released nothing
            pass
    with pytest.raises(KeyError), _exclusive_owner(parent):
        raise KeyError("a failing round")
    with _exclusive_owner(parent):
        pass
    assert os.listdir(parent) == []  # no lock file, no residue


def test_control_another_process_holds_the_parent_lock_until_it_dies(tmp_path: Path) -> None:
    holder = subprocess.Popen(
        [
            sys.executable,
            "-I",
            "-c",
            "import fcntl, os, sys\n"
            "fd = os.open(sys.argv[1], os.O_RDONLY | os.O_DIRECTORY)\n"
            "fcntl.flock(fd, fcntl.LOCK_EX)\n"
            "print('held', flush=True)\n"
            "sys.stdin.read()\n",
            str(tmp_path),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert holder.stdout.readline() == "held\n"
        with pytest.raises(RealPathsBusy), _exclusive_owner(str(tmp_path)):
            pass
    finally:
        holder.kill()  # no orderly unlock
        holder.communicate(timeout=30)
    with _exclusive_owner(str(tmp_path)):
        pass


def _stand_in_real_mode(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Real mode with a temporary directory as the capture parent."""
    parent = tmp_path / "parent"
    parent.mkdir()
    module = sys.modules[__name__]
    monkeypatch.setattr(module, "REAL", True)
    monkeypatch.setattr(module, "OUT", str(tmp_path / "out.json"))
    monkeypatch.setattr(plan_module, "CAPTURE_PARENT", str(parent))
    return parent


@pytest.mark.parametrize(
    "entry",
    ("test_control_a_real_unexpected_exit_stops_the_pass_and_is_refused", "test_measure_the_plan_on_the_disposable_host"),
)
def test_control_a_contended_real_test_checks_creates_and_removes_nothing(
    entry: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    parent = _stand_in_real_mode(monkeypatch, tmp_path)
    (parent / "capture-a").mkdir()  # the owner's leaf, mid-round
    (parent / "capture-a" / "sentinel").write_text("the owner's")
    reached: list[str] = []
    module = sys.modules[__name__]
    for name in ("_require_real_preconditions", "_run_round", "_remove_created_leaf"):
        monkeypatch.setattr(module, name, lambda *a, _name=name, **k: reached.append(_name))
    with _exclusive_owner(str(parent)), pytest.raises(RealPathsBusy):
        getattr(module, entry)(tmp_path)
    assert reached == []
    assert os.listdir(parent) == ["capture-a"]
    assert (parent / "capture-a" / "sentinel").read_text() == "the owner's"
    assert not os.path.lexists(tmp_path / "out.json")


def test_control_the_measurement_holds_the_lock_from_the_preconditions_over_every_round(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    parent = _stand_in_real_mode(monkeypatch, tmp_path)
    plan = plan_module.build_pass_a_plan(include_corroboration=True)
    held: list[str] = []

    def assert_held(stage: str) -> None:
        with pytest.raises(RealPathsBusy), _exclusive_owner(str(parent)):
            pass
        held.append(stage)

    def stub_round(plan_, acts, round_dir, leaf):  # type: ignore[no-untyped-def]
        assert_held("round")  # cleanup is inside the real ``_run_round``, so under the same hold
        return Round(True, None, TimingLauncher(rows=[{**row, "seconds": 0.0} for row in _clean_rows(plan)]), {"wall_seconds": 0.0})

    module = sys.modules[__name__]
    monkeypatch.setattr(module, "ROUNDS", 3)
    monkeypatch.setattr(module, "_require_real_preconditions", lambda: assert_held("preconditions"))
    monkeypatch.setattr(module, "_run_round", stub_round)
    test_measure_the_plan_on_the_disposable_host(tmp_path)
    assert held == ["preconditions", "round", "round", "round"]
    with _exclusive_owner(str(parent)):
        pass


@needs_host
def test_control_a_real_unexpected_exit_stops_the_pass_and_is_refused(tmp_path: Path) -> None:
    """Regression control: ``uname -n`` exits 0; a plan that expects 3 must not complete."""
    with _real_path_ownership():
        if REAL:
            _require_real_preconditions()
        plan = plan_module.build_pass_a_plan(include_corroboration=True)
        wrong = tuple(
            plan_module.PlannedStep(st.step_id, st.command_class, st.environment, st.argv, (3,), st.auth_row)
            if st.step_id == "A1-01"
            else st
            for st in plan.steps
        )
        wrong_plan = plan_module.PassAPlan(wrong, plan.classes)
        result = _run_round(wrong_plan, _measured_acts(wrong_plan), tmp_path / "control")
        assert not result.completed
        assert result.reason == "A1-01: unacceptable-exit"
        assert len(result.launcher.rows) < len(wrong_plan.steps)  # it stopped at the first unexpected exit
        with pytest.raises(UnexpectedOutcome):
            verify_recorded_outcomes(wrong_plan, result.launcher.rows)


@needs_host
def test_measure_the_plan_on_the_disposable_host(tmp_path: Path) -> None:
    with _real_path_ownership():
        _refuse_existing_output(OUT)
        if REAL:
            _require_real_preconditions()
        plan = plan_module.build_pass_a_plan(include_corroboration=True)
        acts = _measured_acts(plan)
        leaves = plan_module.PARENT_CONTRACT.leaves
        rounds: list[dict] = []
        for round_number in range(ROUNDS):
            load_before = os.getloadavg()
            result = _run_round(plan, acts, tmp_path / f"r{round_number}", leaves[round_number % len(leaves)])
            load_after = os.getloadavg()
            rows = result.launcher.rows
            assert result.completed, (result.reason, rows[-1:])
            verify_recorded_outcomes(plan, rows)
            children = sum(row["seconds"] for row in rows)
            rounds.append(
                {
                    **result.record,
                    "child_seconds": children,
                    "mechanism_seconds": result.record["wall_seconds"] - children,
                    "loadavg_before": load_before,
                    "loadavg_after": load_after,
                    "steps": [
                        {"step": step.step_id, "class": step.command_class, "accepted": step.accepted_exits, **row}
                        for step, row in zip(plan.steps, rows, strict=True)
                    ],
                }
            )
        with open(OUT, "x", encoding="utf-8") as handle:
            json.dump(
                {
                    "host": socket.gethostname(),
                    "label": LABEL,
                    "mode": "real" if REAL else "synthetic",
                    "plan_timeouts": PLAN_TIMEOUTS,
                    "uid": os.getuid(),
                    "gid": os.getgid(),
                    "groups": os.getgroups(),
                    "acts": len(acts),
                    "rounds": rounds,
                },
                handle,
                indent=1,
            )
