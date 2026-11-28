"""D1 continuation seam and D2 authority labels, on synthetic values only.

``run_pass_a`` is neither imported nor called. The seam is exercised through
``pass_a._drive`` and ``pass_a._validated_plan``, over capture sessions under a
pytest temporary directory with a scripted launcher that starts no process. Every
output is invented for the test; none is an observation of a host.
"""

from __future__ import annotations

import ast
import dataclasses
import os
import shutil
from pathlib import Path

import pytest

from tests.phase_5_0_evidence.rp11_fixtures import (
    INVOCATION_ID,
    OTHER_INVOCATION_ID,
    FaultFilesystem,
    Host,
    ScriptedLauncher,
    act,
    open_session,
    python_argv,
    rp11_release_descriptors,  # noqa: F401 - autouse fixture, active by import
)
from tests.test_rp11_pass_a_expectations import EXPECTED, PLAN, good_output
from tools import rp11_pass_a_expectations as V
from tools.phase_5_0_evidence.capture_contract import IndexState, sha256_hex
from tools.phase_5_0_evidence.execution import pass_a
from tools.phase_5_0_evidence.execution import pass_a_plan as P
from tools.phase_5_0_evidence.execution.capture_mechanism import (
    EVIDENCE_STAGES,
    JUDGED_STAGE,
    MAX_EVIDENCE_STREAM_BYTES,
    CaptureRefused,
    SessionState,
)
from tools.phase_5_0_evidence.execution.capture_store import CaptureInterrupted, StoreFailure

STDOUT_1 = "streams/stdout/000001"
STDERR_1 = "streams/stderr/000001"
RECORD_1 = "records/000001.json"
STATE_1 = "index/000001.open.json"
OUTPUT = (b"first-out", b"first-err", 0)


# --- D2: authority labels -------------------------------------------------------------


@pytest.mark.parametrize("corroboration", [False, True])
def test_every_planned_step_is_auth_read(corroboration: bool) -> None:
    steps = P.build_pass_a_plan(include_corroboration=corroboration).steps
    assert {s.auth_row for s in steps} == {"AUTH-READ"}


def test_the_default_plan_is_six_a0_and_forty_three_a1_acts_with_the_cluster_reads() -> None:
    steps = {s.step_id: s for s in P.build_pass_a_plan().steps}
    a0 = {"A0-02a", "A0-02b", "A0-03", "A0-04", "A0-05", "A1-S2"}
    assert a0 <= set(steps) and len(steps) - len(a0) == 43
    for step_id in ("A1-29", "A1-30", "A1-Z-29", "A1-Z-30"):
        assert steps[step_id].auth_row == "AUTH-READ", step_id


# --- trusted extraction ---------------------------------------------------------------


class NameRecordingFilesystem(FaultFilesystem):
    def __init__(self, **keywords) -> None:  # type: ignore[no-untyped-def]
        super().__init__(**keywords)
        self.read_opens: list[tuple[str, str]] = []
        self.directory_opens: list[str] = []

    def open_directory(self, dir_fd, name, *, stage):  # type: ignore[no-untyped-def]
        self.directory_opens.append(name)
        return super().open_directory(dir_fd, name, stage=stage)

    def open_read(self, dir_fd, name, *, stage):  # type: ignore[no-untyped-def]
        self.read_opens.append((stage, name))
        return super().open_read(dir_fd, name, stage=stage)


def one_act(host: Host, filesystem=None, outputs=(OUTPUT,)):  # type: ignore[no-untyped-def]
    session = open_session(host, filesystem=filesystem, launcher=ScriptedLauncher(list(outputs)))
    outcome = session.run_act(act("A1-01", python_argv("pass")))
    assert outcome.admitted
    return session, outcome


def test_the_evidence_is_the_latest_admitted_act_of_this_chain(tmp_path: Path) -> None:
    host = Host.under(tmp_path)
    session, first = one_act(host, outputs=(OUTPUT, (b"second-out", b"", 0)))
    evidence = session.admitted_evidence()
    assert (evidence.stdout, evidence.stderr) == (b"first-out", b"first-err")
    assert (evidence.pass_id, evidence.invocation_id, evidence.capture_seq) == (
        "C-P5.0-R5-OP1-A", INVOCATION_ID, 1,
    )
    assert evidence.record_sha256 == first.record_sha256 == sha256_hex(evidence.record.to_bytes())
    state = (Path(host.root()) / STATE_1).read_bytes()
    assert evidence.state_sha256 == sha256_hex(state)
    assert IndexState.from_bytes(state).records[-1].sha256 == evidence.record_sha256

    second = session.run_act(act("A1-02", python_argv("pass")))
    evidence = session.admitted_evidence()
    assert (evidence.capture_seq, evidence.record_sha256, evidence.stdout, evidence.stderr) == (
        2, second.record_sha256, b"second-out", b"",
    )


def test_only_admitted_names_are_opened_and_nothing_is_written(tmp_path: Path) -> None:
    host = Host.under(tmp_path)
    filesystem = NameRecordingFilesystem()
    session, _ = one_act(host, filesystem)
    for planted in ("streams/stdout/000002", "records/000002.json"):
        (Path(host.root()) / planted).write_bytes(b"planted")
    del filesystem.read_opens[:], filesystem.calls[:], filesystem.directory_opens[:]
    session.admitted_evidence()
    _, state, record, out, err, _ = EVIDENCE_STAGES
    assert filesystem.read_opens == [
        (state, "000001.open.json.staging"),
        (state, "000001.open.json"),
        (record, "000001.json.staging"),
        (record, "000001.json"),
        (out, "000001"),
        (err, "000001"),
    ]
    assert {method for method, _ in filesystem.calls} <= {
        "open_directory", "lstat_at", "open_read", "fstat", "digest", "read", "close",
    }
    ancestors = list(Path(host.root()).parts[:-1])
    assert filesystem.directory_opens == ancestors * 2, "never the root or a subdirectory"


def test_no_evidence_before_an_act_or_after_the_pass_ended(tmp_path: Path) -> None:
    session = open_session(Host.under(tmp_path))
    with pytest.raises(CaptureRefused):
        session.admitted_evidence()
    session.run_act(act("A1-01", python_argv("pass")))
    session.complete()
    with pytest.raises(CaptureRefused):
        session.admitted_evidence()


def _replace_with_equal_bytes(path: Path) -> None:
    data = path.read_bytes()
    other = path.with_name("other")
    other.write_bytes(data)
    other.chmod(0o600)
    os.replace(other, path)


def _symlink_to_equal_bytes(path: Path) -> None:
    elsewhere = path.parents[2] / f"elsewhere-{path.parent.name}"
    elsewhere.write_bytes(path.read_bytes())
    elsewhere.chmod(0o600)
    path.unlink()
    path.symlink_to(elsewhere)


def _rewrite_same_size(path: Path) -> None:
    path.write_bytes(b"X" * path.stat().st_size)


def _append(path: Path) -> None:
    with path.open("ab") as handle:
        handle.write(b"more")


TAMPERING = {
    "replaced": _replace_with_equal_bytes,
    "symlink": _symlink_to_equal_bytes,
    "same-size-rewrite": _rewrite_same_size,
    "appended": _append,
    "mode": lambda path: path.chmod(0o640),
    "extra-link": lambda path: os.link(path, path.with_name("extra")),
    "removed": lambda path: path.unlink(),
    "fifo": lambda path: (path.unlink(), os.mkfifo(path, 0o600)),
}


@pytest.mark.parametrize("target", [STDOUT_1, STDERR_1, RECORD_1, STATE_1])
@pytest.mark.parametrize("change", sorted(TAMPERING))
def test_a_changed_admitted_object_yields_no_evidence(tmp_path: Path, target: str, change: str) -> None:
    host = Host.under(tmp_path)
    session, _ = one_act(host)
    TAMPERING[change](Path(host.root()) / target)
    with pytest.raises(StoreFailure):
        session.admitted_evidence()
    assert session.state is SessionState.OPEN, "the caller owns the one stop transition"


def _swap_directory(directory: Path) -> None:
    """Move ``directory`` aside and put a byte-equal copy at its name."""
    moved = directory.with_name(directory.name + ".moved")
    directory.rename(moved)
    shutil.copytree(moved, directory, symlinks=True)


def _symlink_directory(directory: Path) -> None:
    """The name becomes a symbolic link to the very directory that is held."""
    moved = directory.with_name(directory.name + ".moved")
    directory.rename(moved)
    directory.symlink_to(moved)


def _remove_directory(directory: Path) -> None:
    directory.rename(directory.with_name(directory.name + ".moved"))


#: ``"."`` is the capture root itself, ``".."`` its parent (an ancestor).
BOUND_DIRECTORIES = ("..", ".", "index", "records", "streams", "streams/stdout", "streams/stderr")
SWAPS = {
    "replaced": _swap_directory,
    "symlink": _symlink_directory,
    "removed": _remove_directory,
    "mode": lambda directory: directory.chmod(0o750),
}


def bound_path(host: Host, relative: str) -> Path:
    root = Path(host.root())
    return root.parent if relative == ".." else root / relative


@pytest.mark.parametrize(
    ("relative", "change"),
    # An ancestor's mode is not part of its binding.
    [(r, c) for r in BOUND_DIRECTORIES for c in sorted(SWAPS) if (r, c) != ("..", "mode")],
)
def test_a_changed_directory_binding_is_refused_before_any_retained_open(
    tmp_path: Path, relative: str, change: str
) -> None:
    host = Host.under(tmp_path)
    filesystem = NameRecordingFilesystem()
    session, _ = one_act(host, filesystem)
    SWAPS[change](bound_path(host, relative))
    del filesystem.read_opens[:]
    with pytest.raises(StoreFailure) as failure:
        session.admitted_evidence()
    assert failure.value.stage == EVIDENCE_STAGES[0] and filesystem.read_opens == []
    assert session.state is SessionState.OPEN


class MutatingFilesystem(NameRecordingFilesystem):
    """Runs ``mutation`` once, right after the next ``read`` returned."""

    def __init__(self) -> None:
        super().__init__()
        self.mutation = None

    def read(self, fd, limit, *, stage):  # type: ignore[no-untyped-def]
        data = super().read(fd, limit, stage=stage)
        mutation, self.mutation = self.mutation, None
        if mutation is not None:
            mutation()
        return data


@pytest.mark.parametrize("change", sorted(TAMPERING))
def test_a_stream_changed_during_its_read_yields_no_evidence(tmp_path: Path, change: str) -> None:
    host = Host.under(tmp_path)
    filesystem = MutatingFilesystem()
    session, _ = one_act(host, filesystem)
    path = Path(host.root()) / STDOUT_1

    def mutate() -> None:
        TAMPERING[change](path)
        if change == "same-size-rewrite":
            # Do not depend on the filesystem's timestamp granularity.
            os.utime(path, ns=(0, 0))

    filesystem.mutation = mutate
    with pytest.raises(StoreFailure) as failure:
        session.admitted_evidence()
    assert failure.value.stage == "D1:read-stdout"


@pytest.mark.parametrize("relative", BOUND_DIRECTORIES)
def test_a_directory_replaced_during_a_read_yields_no_evidence(tmp_path: Path, relative: str) -> None:
    host = Host.under(tmp_path)
    filesystem = MutatingFilesystem()
    session, _ = one_act(host, filesystem)
    filesystem.mutation = lambda: _swap_directory(bound_path(host, relative))
    with pytest.raises(StoreFailure) as failure:
        session.admitted_evidence()
    # Renaming a directory leaves the stream inside it unchanged, so the closing
    # binding check is what refuses.
    assert failure.value.stage == EVIDENCE_STAGES[-1]


@pytest.mark.parametrize("stage", EVIDENCE_STAGES)
def test_a_storage_failure_while_reading_back_is_named_by_stage(tmp_path: Path, stage: str) -> None:
    session, _ = one_act(Host.under(tmp_path), FaultFilesystem(stage=stage))
    with pytest.raises(StoreFailure) as failure:
        session.admitted_evidence()
    assert failure.value.stage == stage and session.state is SessionState.OPEN


@pytest.mark.parametrize("stage", EVIDENCE_STAGES)
def test_an_interruption_while_reading_back_makes_no_further_call(tmp_path: Path, stage: str) -> None:
    filesystem = FaultFilesystem(stage=stage, mode="interrupt")
    session, _ = one_act(Host.under(tmp_path), filesystem)
    with pytest.raises(CaptureInterrupted):
        session.admitted_evidence()
    assert session.state is SessionState.INTERRUPTED and filesystem.after_interrupt == []
    for call in (session.admitted_evidence, session.complete):
        with pytest.raises(CaptureRefused):
            call()


# --- the seam -------------------------------------------------------------------------


class Judge:
    """A fake continuation: act N is answered with ``answers[N]``, ``True`` past the end."""

    def __init__(self, *answers: object, covers: object = True) -> None:
        self.answers = answers
        self.covered = covers
        self.seen: list[tuple[str, bytes]] = []

    def covers(self, plan):  # type: ignore[no-untyped-def]
        return self.covered

    def permits(self, request, evidence):  # type: ignore[no-untyped-def]
        index = len(self.seen)
        self.seen.append((request.step_or_case_id, evidence.stdout))
        return self.answers[index] if index < len(self.answers) else True


def accept_zero(request, outcome) -> bool:  # type: ignore[no-untyped-def]
    return outcome.kind == "status" and outcome.value == 0


def plan_of(count: int):  # type: ignore[no-untyped-def]
    return tuple(act(f"A1-{n:02d}", python_argv("pass")) for n in range(1, count + 1))


def drive(host: Host, plan, continuation, *, policy=accept_zero, filesystem=None, outputs=()):  # type: ignore[no-untyped-def]
    launcher = ScriptedLauncher(list(outputs))
    session = open_session(host, filesystem=filesystem, launcher=launcher)
    return pass_a._drive(session, plan, policy, continuation), launcher


def final_state(host: Host) -> IndexState:
    (path,) = (Path(host.root()) / "index").glob("*.final.json")
    return IndexState.from_bytes(path.read_bytes())


@pytest.mark.parametrize("answer", [False, None, 1, "yes"])
def test_anything_but_true_stops_before_the_next_act_with_one_x3(tmp_path: Path, answer: object) -> None:
    host = Host.under(tmp_path)
    judge = Judge(True, answer)
    result, launcher = drive(host, plan_of(4), judge)
    assert (result.status, result.reason) == (pass_a.PassAStatus.STOPPED, "continuation-refused")
    assert len(launcher.calls) == 2 and [s for s, _ in judge.seen] == ["A1-01", "A1-02"]
    assert result.finalization.x3_outcome == "succeeded" and result.finalization.admitted_records == 2
    terminal = final_state(host).terminal
    assert (terminal.status, terminal.reason, terminal.step_or_case_id) == (
        "stopped", "continuation-refused", "A1-02",
    )


def test_a_refusal_of_the_last_act_is_not_a_completed_pass(tmp_path: Path) -> None:
    result, _ = drive(Host.under(tmp_path), plan_of(2), Judge(True, False))
    assert result.status is pass_a.PassAStatus.STOPPED


def test_a_continuation_that_permits_every_act_completes(tmp_path: Path) -> None:
    judge = Judge()
    result, _ = drive(Host.under(tmp_path), plan_of(3), judge)
    assert result.completed and [out for _, out in judge.seen] == [b"out-0", b"out-1", b"out-2"]


def test_without_a_continuation_nothing_is_read_back(tmp_path: Path) -> None:
    filesystem = FaultFilesystem()
    result, _ = drive(Host.under(tmp_path), plan_of(2), None, filesystem=filesystem)
    assert result.completed
    assert not set(filesystem.stages()) & set(EVIDENCE_STAGES)
    assert "read" not in {method for method, _ in filesystem.calls}


def test_a_rejected_exit_is_decided_before_the_continuation(tmp_path: Path) -> None:
    judge = Judge()
    result, _ = drive(Host.under(tmp_path), plan_of(2), judge, outputs=((b"", b"", 3),))
    assert result.reason == "unacceptable-exit" and judge.seen == []


def test_evidence_changed_after_admission_stops_without_being_judged(tmp_path: Path) -> None:
    host = Host.under(tmp_path)
    judge = Judge()

    def tampering_policy(request, outcome) -> bool:  # type: ignore[no-untyped-def]
        # Runs between admission and the read-back.
        (Path(host.root()) / STDOUT_1).write_bytes(b"XXXXX")
        return True

    result, launcher = drive(host, plan_of(3), judge, policy=tampering_policy)
    assert (result.status, result.reason) == (pass_a.PassAStatus.STOPPED, "evidence-unverified")
    assert judge.seen == [] and len(launcher.calls) == 1
    assert result.finalization.x4_validity != "valid"


@pytest.mark.parametrize("stage", EVIDENCE_STAGES)
def test_a_failed_read_back_stops_before_the_next_act(tmp_path: Path, stage: str) -> None:
    judge = Judge()
    result, launcher = drive(
        Host.under(tmp_path), plan_of(3), judge, filesystem=FaultFilesystem(stage=stage)
    )
    assert result.reason == "evidence-unverified" and judge.seen == [] and len(launcher.calls) == 1


@pytest.mark.parametrize("relative", BOUND_DIRECTORIES)
def test_a_directory_replaced_while_judging_stops_before_the_next_act(
    tmp_path: Path, relative: str
) -> None:
    host = Host.under(tmp_path)

    class Swapping(Judge):
        def permits(self, request, evidence):  # type: ignore[no-untyped-def]
            _swap_directory(bound_path(host, relative))
            return super().permits(request, evidence)

    result, launcher = drive(host, plan_of(3), Swapping())
    assert (result.status, result.reason) == (pass_a.PassAStatus.STOPPED, "evidence-unverified")
    assert len(launcher.calls) == 1


@pytest.mark.parametrize(("mode", "raised"), [("fail", StoreFailure), ("interrupt", CaptureInterrupted)])
def test_the_after_judgement_check_fails_closed(tmp_path: Path, mode: str, raised: type) -> None:
    filesystem = FaultFilesystem(stage=JUDGED_STAGE, mode=mode)
    session, _ = one_act(Host.under(tmp_path), filesystem)
    session.admitted_evidence()
    with pytest.raises(raised):
        session.verify_evidence_bindings()
    expected = SessionState.OPEN if mode == "fail" else SessionState.INTERRUPTED
    assert session.state is expected and filesystem.after_interrupt == []


# --- the materialization bound --------------------------------------------------------


def test_the_evidence_bound_is_the_largest_planned_stream_bound() -> None:
    assert MAX_EVIDENCE_STREAM_BYTES == max(c.stream_bound_bytes for c in P.BASE_CLASSES.values())


def large_act(bound: int = 2 * MAX_EVIDENCE_STREAM_BYTES):  # type: ignore[no-untyped-def]
    return act("A1-01", python_argv("pass"), bound=bound)


def test_evidence_exactly_at_the_bound_is_materialized(tmp_path: Path) -> None:
    limit = MAX_EVIDENCE_STREAM_BYTES
    session = open_session(
        Host.under(tmp_path), launcher=ScriptedLauncher([(b"o" * limit, b"e" * limit, 0)])
    )
    assert session.run_act(large_act()).admitted
    evidence = session.admitted_evidence()
    assert (len(evidence.stdout), len(evidence.stderr)) == (limit, limit)


@pytest.mark.parametrize("over", ["stdout", "stderr"])
def test_oversized_evidence_is_refused_before_any_filesystem_call(tmp_path: Path, over: str) -> None:
    large = b"x" * (MAX_EVIDENCE_STREAM_BYTES + 1)
    output = (large, b"e", 0) if over == "stdout" else (b"o", large, 0)
    filesystem = FaultFilesystem()
    session = open_session(
        Host.under(tmp_path), filesystem=filesystem, launcher=ScriptedLauncher([output])
    )
    assert session.run_act(large_act()).admitted
    del filesystem.calls[:]
    with pytest.raises(StoreFailure) as failure:
        session.admitted_evidence()
    assert (failure.value.stage, failure.value.classification) == (
        f"D1:read-{over}", "evidence-oversized",
    )
    assert filesystem.calls == [] and session.state is SessionState.OPEN


@pytest.mark.parametrize("judged", [False, True])
def test_the_bound_applies_only_where_evidence_is_asked_for(tmp_path: Path, judged: bool) -> None:
    judge = Judge() if judged else None
    output = (b"o" * (MAX_EVIDENCE_STREAM_BYTES + 1), b"", 0)
    result, _ = drive(Host.under(tmp_path), (large_act(),), judge, outputs=(output,))
    if judge is None:
        assert result.completed
    else:
        assert result.reason == "evidence-unverified" and judge.seen == []


class _NoMethods:
    pass


@pytest.mark.parametrize("continuation", [Judge(covers=False), Judge(covers=1), _NoMethods(), "judge"])
def test_a_continuation_that_does_not_cover_the_plan_is_refused_before_any_effect(
    tmp_path: Path, continuation: object
) -> None:
    def factory(request):  # type: ignore[no-untyped-def]
        raise AssertionError("never called")

    host = Host.under(tmp_path)
    genesis = open_session(host)._request
    with pytest.raises(pass_a.PassAPlanRefused) as refused:
        pass_a._validated_plan(plan_of(2), accept_zero, genesis, factory, continuation)
    assert refused.value.reason == "malformed-continuation"


def test_the_public_entry_hands_the_continuation_to_both_steps() -> None:
    """By syntax only: ``run_pass_a`` is not called."""
    tree = ast.parse(Path(pass_a.__file__).read_text(encoding="utf-8"))
    (public,) = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run_pass_a"]
    forwarded = {
        node.func.id
        for node in ast.walk(public)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and any(isinstance(a, ast.Name) and a.id == "continuation" for a in node.args)
    }
    assert forwarded == {"_validated_plan", "_drive"}


# --- the D1 evaluator behind the seam -------------------------------------------------


def plan_acts():  # type: ignore[no-untyped-def]
    return P.build_pass_a_plan().acts()


def outputs(**changes: tuple[bytes, bytes, int]) -> list[tuple[bytes, bytes, int]]:
    listed = []
    for step in V.STEP_IDS:
        status, out, err = good_output(step)
        listed.append(changes.get(step.replace("-", "_"), (out, err, status)))
    return listed


def evaluated(
    host: Host, *, expected: V.Expectations = EXPECTED, invocation_id: str = INVOCATION_ID, **changes
):  # type: ignore[no-untyped-def]
    continuation = V.EvaluationContinuation(expected, PLAN, invocation_id=invocation_id)
    acts = plan_acts()
    assert continuation.covers(acts)
    result, launcher = drive(
        host, acts, continuation, policy=P.build_pass_a_plan().exit_policy(), outputs=outputs(**changes)
    )
    return result, launcher, continuation


def stopped_at(result, launcher, continuation, step: str, outcome: V.Outcome, reason: str) -> None:
    assert (result.status, result.reason) == (pass_a.PassAStatus.STOPPED, "continuation-refused")
    assert len(launcher.calls) == V.STEP_IDS.index(step) + 1, "no act after the refused one"
    failure = continuation.evaluation.first_failure
    assert (failure.step_id, failure.outcome, failure.reason) == (step, outcome, reason)
    assert not continuation.evaluation.established


def test_a_matching_synthetic_pass_is_established_from_read_back_bytes(tmp_path: Path) -> None:
    result, launcher, continuation = evaluated(Host.under(tmp_path))
    assert result.completed and len(launcher.calls) == 49 and continuation.evaluation.established
    cited = [v.record_sha256 for v in continuation.evaluation.verdicts]
    assert cited == [o.record_sha256 for o in result.outcomes]


@pytest.mark.parametrize(
    ("step", "output", "reason"),
    [
        ("A0-02a", (b"b" * 40 + b"\n", b"", 0), "value"),
        ("A1-01", (b"other-node\n", b"", 0), "value"),
        ("A1-19", (b"", b"stat: Permission denied\n", 1), "not-the-enoent-diagnostic"),
        ("A1-29", (b"inactive\n", b"", 0), "value"),
        ("A1-Z-30", (b"18 main 5432 online synthetic /moved /synthetic.log\n", b"", 0), "final-survey-differs"),
    ],
)
def test_a_material_mismatch_with_an_accepted_exit_stops_the_pass(
    tmp_path: Path, step: str, output: tuple[bytes, bytes, int], reason: str
) -> None:
    result, launcher, continuation = evaluated(
        Host.under(tmp_path), **{step.replace("-", "_"): output}
    )
    stopped_at(result, launcher, continuation, step, V.Outcome.MISMATCH, reason)


def test_without_a_reviewed_enoent_form_the_pass_stops_at_a1_19(tmp_path: Path) -> None:
    result, launcher, continuation = evaluated(
        Host.under(tmp_path), expected=dataclasses.replace(EXPECTED, run_root_enoent_stderr=None)
    )
    stopped_at(
        result, launcher, continuation, "A1-19", V.Outcome.UNESTABLISHED, "no-reviewed-enoent-form"
    )


def test_evidence_of_another_invocation_is_refused_at_the_first_act(tmp_path: Path) -> None:
    result, launcher, continuation = evaluated(Host.under(tmp_path), invocation_id=OTHER_INVOCATION_ID)
    stopped_at(result, launcher, continuation, "A0-02a", V.Outcome.MISMATCH, "not-the-current-act")


def test_only_the_exact_plan_is_covered_and_only_once() -> None:
    continuation = V.EvaluationContinuation(EXPECTED, PLAN, invocation_id=INVOCATION_ID)
    acts = plan_acts()
    other_argv = dataclasses.replace(acts[6], argv=("/usr/bin/uname", "-s"))
    for wrong in (acts[:-1], acts[:1], (), (*acts, acts[-1]), (acts[1], acts[0], *acts[2:]),
                  (*acts[:6], other_argv, *acts[7:])):
        assert continuation.covers(wrong) is False
    assert continuation.covers(acts) is True
    assert continuation.permits(acts[0], object()) is False
    assert continuation.covers(acts) is False, "one use"


def test_stale_evidence_and_any_call_after_a_refusal_are_refused(tmp_path: Path) -> None:
    acts = plan_acts()
    session = open_session(Host.under(tmp_path), launcher=ScriptedLauncher(outputs()))
    session.run_act(acts[0])
    first = session.admitted_evidence()
    continuation = V.EvaluationContinuation(EXPECTED, PLAN, invocation_id=INVOCATION_ID)
    assert continuation.permits(acts[0], first) is True
    assert continuation.permits(acts[1], first) is False, "the previous act's evidence"
    session.run_act(acts[1])
    assert continuation.permits(acts[1], session.admitted_evidence()) is False
    assert len(continuation.evaluation.verdicts) == 2
