"""RP-11 Pass A orchestration: bind, drive a finite plan, stop on first failure, finalize once.

Synthetic and local. Every command is an inert in-process fake or an inline program of
the current interpreter under a pytest temporary directory; every number below is a
test-only value, none is a Pass A value. Nothing here touches systemd, a network, a
database, a real capture root or any production or staging host.

The count that matters throughout is the number of ``*.final.json`` index files: X-3
publishes exactly one, so it is the externally visible measure of "one finalization
attempt".
"""

from __future__ import annotations

import ast
import importlib.util
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from application.rp11.journal import GENESIS, JournalKind, consume_run, serialize_line
from tests.phase_5_0_evidence.rp11_fixtures import (
    INERT_ENVIRONMENT,
    INVOCATION_ID,
    OTHER_INVOCATION_ID,
    PASS_A,
    TOOL_SHA256,
    CountingLauncher,
    FaultFilesystem,
    FixedClock,
    Host,
    act,
    python_argv,
    rp11_release_descriptors,  # noqa: F401 - autouse fixture, active by import
    writes,
)
from tools.phase_5_0_evidence.capture_contract import IndexState
from tools.phase_5_0_evidence.execution import pass_a
from tools.phase_5_0_evidence.execution.boundary import StreamCaptureResult
from tools.phase_5_0_evidence.execution.capture_mechanism import (
    ActRequest,
    CaptureSession,
    GenesisRequest,
    SessionState,
    create_capture_session,
)
from tools.phase_5_0_evidence.execution.capture_store import CaptureInterrupted
from tools.phase_5_0_evidence.execution.pass_a import (
    PassAPlanRefused,
    PassAStatus,
    run_pass_a,
)
from tools.phase_5_0_evidence.execution.start_binding import REFUSAL_REASONS

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path(pass_a.__file__)
ACTIVATION = "rp11-act-20261018T120000Z-0123abcd"
BOOT = "01234567-89ab-cdef-0123-456789abcdef"


# --- fixtures -----------------------------------------------------------------------


def consume_journal(invocation_id: str = INVOCATION_ID, activation: str = ACTIVATION) -> bytes:
    """A consume journal built by the production serializer (one ``run-start``)."""
    start = {
        "invocation_id": invocation_id,
        "boot_id": BOOT,
        "claim": {"dev": 1, "ino": 2},
        "act_journal": {"sha256": "a" * 64, "length": 10},
        "lock": {"object": {"path": "/run/k", "dev": 1, "ino": 3}, "mode": "held", "wait_ms": 0},
        "helper": {"role": "consume", "tool_sha256": "absent"},
    }
    return serialize_line(
        JournalKind.CONSUME, seq=1, prev=GENESIS, run=consume_run(activation), op="run-start", fields=start
    )


@dataclass
class PlanLauncher:
    """A fake launcher: call N behaves as ``behaviours[N]`` (``"ok"`` past the end).

    Behaviours: ``ok``, ``timeout``, ``start-failed``, ``bound``, ``incomplete``,
    ``crash`` (raises), ``exit:N`` (clean exit with code N)."""

    behaviours: tuple[str, ...] = ()
    calls: list[tuple[str, ...]] = field(default_factory=list)
    timeouts: list[float] = field(default_factory=list)
    environments: list[dict[str, str]] = field(default_factory=list)
    bounds: list[int] = field(default_factory=list)

    def launch(self, argv, *, environment, stdout, stderr, stream_bound_bytes, timeout_seconds, drain_seconds=5.0):  # type: ignore[no-untyped-def]
        index = len(self.calls)
        self.calls.append(tuple(argv))
        self.timeouts.append(timeout_seconds)
        self.environments.append(dict(environment))
        self.bounds.append(stream_bound_bytes)
        behaviour = self.behaviours[index] if index < len(self.behaviours) else "ok"
        if behaviour == "crash":
            raise RuntimeError("launcher bug")
        if behaviour == "start-failed":
            return StreamCaptureResult(False, "capture-start-failed", None, 0, 0, False, False, False)
        out, err = b"out-%d" % index, b"err-%d" % index
        stdout.write(out)
        stderr.write(err)
        code = int(behaviour.split(":")[1]) if behaviour.startswith("exit:") else 0
        return StreamCaptureResult(
            True,
            "",
            code,
            len(out),
            len(err),
            behaviour == "bound",
            behaviour != "incomplete",
            behaviour == "timeout",
        )


def accept_zero(request: ActRequest, outcome) -> bool:  # type: ignore[no-untyped-def]
    return outcome.kind == "status" and outcome.value == 0


def accept_anything(request: ActRequest, outcome) -> bool:  # type: ignore[no-untyped-def]
    return True


def genesis(host: Host, *, invocation_id: str = INVOCATION_ID, root: str | None = None) -> GenesisRequest:
    return GenesisRequest(
        capture_root=root or host.root(),
        pass_id=PASS_A,
        tool_sha256=TOOL_SHA256,
        invocation_id=invocation_id,
        policy=host.policy(),
    )


def plan(count: int, **keywords) -> tuple[ActRequest, ...]:  # type: ignore[no-untyped-def]
    return tuple(act(f"A1-{n:02d}", writes(b"", b""), **keywords) for n in range(1, count + 1))


class RecordingFactory:
    """The test's own session factory: the only place a session is built in this module.

    It records every genesis request it receives, so a test can prove it was not called
    (binding refusal, malformed plan) or was called exactly once with the pass's genesis."""

    def __init__(self, launcher, filesystem=None) -> None:  # type: ignore[no-untyped-def]
        self.launcher = launcher
        self.filesystem = filesystem if filesystem is not None else FaultFilesystem()
        self.requests: list[GenesisRequest] = []

    def __call__(self, request: GenesisRequest) -> CaptureSession:
        self.requests.append(request)
        return create_capture_session(
            request, filesystem=self.filesystem, launcher=self.launcher, clock=FixedClock()
        )


def run(host: Host, launcher, acts, *, policy=accept_zero, filesystem=None, journal=None, **overrides):  # type: ignore[no-untyped-def]
    arguments = dict(
        activation_id=ACTIVATION,
        consume_journal=consume_journal() if journal is None else journal,
        genesis=genesis(host),
        acts=acts,
        exit_policy=policy,
        session_factory=RecordingFactory(launcher, filesystem),
    )
    arguments.update(overrides)
    return run_pass_a(**arguments)


def finals(host: Host) -> list[str]:
    index = Path(host.root()) / "index"
    return sorted(p for p in os.listdir(index) if p.endswith(".final.json")) if index.is_dir() else []


def final_state(host: Host) -> IndexState:
    (name,) = finals(host)
    return IndexState.from_bytes((Path(host.root()) / "index" / name).read_bytes())


# --- a plan that runs to its end ------------------------------------------------------


def test_a_plan_that_runs_to_its_end_is_completed_with_one_x3_in_order(tmp_path: Path) -> None:
    host = Host.under(tmp_path)
    launcher = PlanLauncher()
    acts = (
        act("A1-01", writes(b"a", b""), bound=111, timeout=3.5),
        act("A1-02", writes(b"b", b""), bound=222, timeout=7.25),
        act("A1-03", writes(b"c", b""), bound=333, timeout=9.0),
    )
    result = run(host, launcher, acts)
    assert result.status is PassAStatus.COMPLETED and result.completed and result.reason is None
    assert launcher.calls == [a.argv for a in acts]
    assert [o.capture_seq for o in result.outcomes] == [1, 2, 3] and all(o.admitted for o in result.outcomes)
    assert result.failure is None
    assert (result.finalization.x3_outcome, result.finalization.x4_validity) == ("succeeded", "valid")
    assert result.finalization.admitted_records == 3
    assert result.binding.invocation_id == INVOCATION_ID and result.binding.x3_outcome == "succeeded"
    assert len(finals(host)) == 1
    state = final_state(host)
    assert state.terminal.status == "completed" and state.invocation_id == INVOCATION_ID


def test_every_value_of_every_act_reaches_the_launcher_exactly_as_injected(tmp_path: Path) -> None:
    host = Host.under(tmp_path)
    launcher = PlanLauncher()
    acts = (
        act("A1-01", writes(b"", b""), bound=111, timeout=3.5),
        act("A1-02", writes(b"", b""), bound=222, timeout=7.25),
    )
    run(host, launcher, acts)
    assert launcher.timeouts == [3.5, 7.25]
    assert launcher.bounds == [111, 222]
    assert launcher.environments == [INERT_ENVIRONMENT, INERT_ENVIRONMENT]


def test_the_plan_is_snapshotted_so_a_list_changed_mid_pass_adds_nothing(tmp_path: Path) -> None:
    host = Host.under(tmp_path)
    launcher = PlanLauncher()
    acts = list(plan(2))

    def policy(request, outcome):  # type: ignore[no-untyped-def]
        acts.append(act("A1-99", writes(b"", b"")))
        return True

    result = run(host, launcher, acts, policy=policy)
    assert result.completed and len(launcher.calls) == 2


# --- the first failure stops the pass and finalizes once ------------------------------


@pytest.mark.parametrize(
    ("behaviour", "classification", "may_have_run"),
    [
        ("timeout", "command-timeout", True),
        ("start-failed", "capture-start-failed", False),
        ("bound", "stream-bound-exceeded", True),
        ("incomplete", "stream-incomplete", True),
    ],
)
def test_the_first_failure_stops_the_pass_with_one_x3_and_no_later_command(
    tmp_path: Path, behaviour: str, classification: str, may_have_run: bool
) -> None:
    host = Host.under(tmp_path)
    launcher = PlanLauncher(("ok", behaviour))
    result = run(host, launcher, plan(4))
    assert result.status is PassAStatus.STOPPED and not result.completed
    assert result.reason == classification and result.failure.classification == classification
    assert result.failure.host_act_may_have_run is may_have_run
    assert len(launcher.calls) == 2, "no command after the failing one"
    assert [o.admitted for o in result.outcomes] == [True, False]
    assert result.finalization is result.outcomes[-1].stop
    assert result.finalization.x3_outcome == "succeeded"
    assert result.finalization.admitted_records == 1
    assert len(finals(host)) == 1
    terminal = final_state(host).terminal
    assert (terminal.status, terminal.capture_seq, terminal.reason) == ("stopped", 2, classification)


@pytest.mark.parametrize(
    ("request_act", "classification"),
    [
        (act("A1-02", ("relative",)), "request-malformed-argv"),
        (act("A1-02", writes(b"", b""), timeout=0.0), "request-malformed-timeout"),
        (act("A1-02", writes(b"", b""), timeout=float("inf")), "request-malformed-timeout"),
        (act("A1-02", writes(b"", b""), bound=0), "request-malformed-argv"),
    ],
)
def test_a_malformed_act_stops_the_pass_before_any_launch_and_finalizes_once(
    tmp_path: Path, request_act: ActRequest, classification: str
) -> None:
    host = Host.under(tmp_path)
    launcher = PlanLauncher()
    result = run(host, launcher, (plan(1)[0], request_act, plan(1)[0]))
    assert result.status is PassAStatus.STOPPED and result.reason == classification
    assert len(launcher.calls) == 1
    assert len(finals(host)) == 1 and final_state(host).terminal.reason == classification


def test_a_handled_command_timeout_of_a_real_process_takes_the_existing_finalization_path(tmp_path: Path) -> None:
    # A real, armed launcher and a real child that outlives a short test-only deadline.
    host = Host.under(tmp_path)
    launcher = CountingLauncher()
    hang = act("A1-02", python_argv("import time; time.sleep(60)"), timeout=0.5, drain=2.0)
    result = run_pass_a(
        activation_id=ACTIVATION,
        consume_journal=consume_journal(),
        genesis=genesis(host),
        acts=(
            act("A1-01", writes(b"a", b"")),
            hang,
            act("A1-03", writes(b"c", b"")),
        ),
        exit_policy=accept_zero,
        session_factory=RecordingFactory(launcher),
    )
    assert result.status is PassAStatus.STOPPED and result.reason == "command-timeout"
    assert result.failure.host_act_may_have_run and not result.outcomes[-1].admitted
    assert len(launcher.calls) == 2, "the third command was never issued"
    assert (result.finalization.x3_outcome, result.finalization.x4_validity) == ("succeeded", "valid")
    assert result.finalization.admitted_records == 1
    assert len(finals(host)) == 1
    terminal = final_state(host).terminal
    assert (terminal.status, terminal.capture_seq, terminal.reason) == ("stopped", 2, "command-timeout")


# --- exit policy: injected, never defaulted --------------------------------------------


def test_run_pass_a_has_no_default_exit_policy() -> None:
    import inspect

    parameter = inspect.signature(run_pass_a).parameters["exit_policy"]
    assert parameter.default is inspect.Parameter.empty and parameter.kind is parameter.KEYWORD_ONLY


def test_an_exit_the_policy_rejects_stops_the_pass_after_its_record_with_one_x3(tmp_path: Path) -> None:
    host = Host.under(tmp_path)
    launcher = PlanLauncher(("ok", "exit:3"))
    seen = []

    def policy(request, outcome):  # type: ignore[no-untyped-def]
        seen.append((request.step_or_case_id, outcome.kind, outcome.value))
        return accept_zero(request, outcome)

    result = run(host, launcher, plan(3), policy=policy)
    assert result.status is PassAStatus.STOPPED and result.reason == "unacceptable-exit"
    assert result.failure is None and all(o.admitted for o in result.outcomes)
    assert seen == [("A1-01", "status", 0), ("A1-02", "status", 3)]
    assert len(launcher.calls) == 2
    assert result.finalization.admitted_records == 2 and result.finalization.x3_outcome == "succeeded"
    assert len(finals(host)) == 1
    terminal = final_state(host).terminal
    assert (terminal.status, terminal.step_or_case_id, terminal.reason) == ("stopped", "A1-02", "unacceptable-exit")


def test_a_policy_that_accepts_a_nonzero_exit_lets_the_pass_complete(tmp_path: Path) -> None:
    host = Host.under(tmp_path)
    launcher = PlanLauncher(("exit:3", "exit:9"))
    result = run(host, launcher, plan(2), policy=accept_anything)
    assert result.completed and len(launcher.calls) == 2 and len(finals(host)) == 1


@pytest.mark.parametrize("verdict", [False, None, 1, "yes", 0])
def test_only_exactly_true_continues_the_pass(tmp_path: Path, verdict: object) -> None:
    host = Host.under(tmp_path)
    launcher = PlanLauncher()
    result = run(host, launcher, plan(2), policy=lambda request, outcome: verdict)
    assert result.status is PassAStatus.STOPPED and result.reason == "unacceptable-exit"
    assert len(launcher.calls) == 1 and len(finals(host)) == 1


# --- unexpected errors and interruption -------------------------------------------------


def test_a_policy_that_raises_finalizes_once_and_the_error_propagates(tmp_path: Path) -> None:
    host = Host.under(tmp_path)
    launcher = PlanLauncher()

    def policy(request, outcome):  # type: ignore[no-untyped-def]
        raise LookupError("policy bug")

    with pytest.raises(LookupError):
        run(host, launcher, plan(3), policy=policy)
    assert len(launcher.calls) == 1
    assert len(finals(host)) == 1
    assert final_state(host).terminal.reason == "orchestrator-error"


def test_a_launcher_that_raises_finalizes_once_and_the_error_propagates(tmp_path: Path) -> None:
    host = Host.under(tmp_path)
    launcher = PlanLauncher(("ok", "crash"))
    with pytest.raises(RuntimeError):
        run(host, launcher, plan(3))
    assert len(launcher.calls) == 2
    assert len(finals(host)) == 1
    state = final_state(host)
    assert state.terminal.reason == "orchestrator-error" and len(state.records) == 1


def test_an_interruption_propagates_and_no_x3_is_attempted(tmp_path: Path) -> None:
    host = Host.under(tmp_path)
    launcher = PlanLauncher()
    filesystem = FaultFilesystem(stage="P-1:create-stdout", mode="interrupt", occurrence=2)
    with pytest.raises(CaptureInterrupted):
        run(host, launcher, plan(3), filesystem=filesystem)
    assert len(launcher.calls) == 1
    assert finals(host) == []
    assert not any(stage.startswith("X-3") for _, stage in filesystem.after_interrupt)
    assert filesystem.after_interrupt == [], "no filesystem call at all after the interruption"


# --- no durable genesis -----------------------------------------------------------------


def test_a_root_without_durable_genesis_runs_nothing_and_writes_nothing(tmp_path: Path) -> None:
    host = Host.under(tmp_path)
    Path(host.root()).mkdir()
    (Path(host.root()) / "earlier").write_bytes(b"not ours")
    launcher = PlanLauncher()
    result = run(host, launcher, plan(2))
    assert result.status is PassAStatus.NO_GENESIS and result.reason == "no-durable-genesis"
    assert launcher.calls == [] and result.outcomes == ()
    assert (result.finalization.x3_outcome, result.finalization.x4_validity) == ("not-made", "inconclusive")
    assert result.binding.x3_outcome == "not-made"
    assert sorted(os.listdir(host.root())) == ["earlier"]


# --- finalization that does not come out clean -----------------------------------------


def test_a_failed_x3_at_the_end_of_a_clean_plan_is_not_reported_as_completed(tmp_path: Path) -> None:
    host = Host.under(tmp_path)
    launcher = PlanLauncher()
    result = run(host, launcher, plan(2), filesystem=FaultFilesystem(stage="X-3:create", mode="fail"))
    assert result.status is PassAStatus.FINALIZATION_INCOMPLETE and not result.completed
    assert result.finalization.x3_outcome == "failed"
    assert result.reason == result.finalization.x3_failure_classification
    assert all(o.admitted for o in result.outcomes) and len(launcher.calls) == 2
    assert result.binding.x3_outcome == "failed" and result.binding.final_state is None


def test_a_failed_x3_after_a_stop_is_one_attempt_and_stays_a_stop(tmp_path: Path) -> None:
    host = Host.under(tmp_path)
    launcher = PlanLauncher(("timeout",))
    filesystem = FaultFilesystem(stage="X-3:create", mode="fail")
    result = run(host, launcher, plan(2), filesystem=filesystem)
    assert result.status is PassAStatus.STOPPED and result.reason == "command-timeout"
    assert result.finalization.x3_outcome == "failed"
    create_calls = [call for call in filesystem.calls if call[0] == "create_exclusive" and call[1] == "X-3:create"]
    assert len(create_calls) == 1, "X-3 is attempted once and never retried"
    assert len(launcher.calls) == 1


# --- the start binding comes first -------------------------------------------------------


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"journal": consume_journal(OTHER_INVOCATION_ID)}, "invocation-mismatch"),
        ({"journal": b""}, "journal-invalid"),
        ({"journal": consume_journal(activation="rp11-act-20261018T120000Z-fedcba98")}, "journal-invalid"),
        ({"activation_id": "not-an-activation"}, "invalid-activation-id"),
        ({"journal": "text"}, "invalid-journal-input"),
    ],
)
def test_a_start_that_cannot_be_bound_creates_nothing_and_calls_nothing(
    tmp_path: Path, kwargs: dict, reason: str
) -> None:
    host = Host.under(tmp_path)
    launcher = PlanLauncher()
    filesystem = FaultFilesystem()
    factory = RecordingFactory(launcher, filesystem)
    result = run(host, launcher, plan(2), session_factory=factory, **kwargs)
    assert result.status is PassAStatus.BINDING_REFUSED and result.reason == reason
    assert reason in REFUSAL_REASONS
    assert (result.outcomes, result.failure, result.finalization, result.binding) == ((), None, None, None)
    assert factory.requests == [], "the factory is not called when the start cannot be bound"
    assert launcher.calls == [] and filesystem.calls == []
    assert not Path(host.root()).exists()


def test_the_invocation_id_bound_is_the_one_the_index_records(tmp_path: Path) -> None:
    host = Host.under(tmp_path)
    other = genesis(host, invocation_id=OTHER_INVOCATION_ID)
    # the journal names INVOCATION_ID; the genesis (and so the index) names the other
    result = run(host, PlanLauncher(), plan(1), genesis=other)
    assert result.status is PassAStatus.BINDING_REFUSED and result.reason == "invocation-mismatch"
    ok = run(host, PlanLauncher(), plan(1), genesis=other, journal=consume_journal(OTHER_INVOCATION_ID))
    assert ok.completed and final_state(host).invocation_id == OTHER_INVOCATION_ID


# --- the session factory is injected, never defaulted, and called once after the binding ---


def test_run_pass_a_has_no_default_session_factory() -> None:
    import inspect

    signature = inspect.signature(run_pass_a)
    assert set(signature.parameters) == {
        "activation_id", "consume_journal", "genesis", "acts", "exit_policy", "session_factory",
    }
    parameter = signature.parameters["session_factory"]
    assert parameter.default is inspect.Parameter.empty and parameter.kind is parameter.KEYWORD_ONLY


def test_the_factory_is_called_once_with_the_genesis_after_the_binding_succeeded(tmp_path: Path) -> None:
    host = Host.under(tmp_path)
    launcher = PlanLauncher()
    factory = RecordingFactory(launcher)
    request = genesis(host)
    result = run(host, launcher, plan(2), genesis=request, session_factory=factory)
    assert result.completed
    assert factory.requests == [request] and factory.requests[0] is request


def test_a_factory_that_returns_no_session_is_refused(tmp_path: Path) -> None:
    host = Host.under(tmp_path)
    with pytest.raises(PassAPlanRefused) as caught:
        run(host, PlanLauncher(), plan(1), session_factory=lambda request: None)
    assert caught.value.reason == "malformed-session"


class _ReturnsInState:
    """A factory that returns a real session already in a state the contract forbids.

    It counts the calls it receives and records every ``stop``/``complete``/``run_act``
    the orchestrator makes afterwards, so a test can prove the refusal is at the boundary."""

    def __init__(self, launcher, state) -> None:  # type: ignore[no-untyped-def]
        self._inner = RecordingFactory(launcher)
        self._state = state
        self.calls = 0
        self.session_calls: list[str] = []

    def __call__(self, request: GenesisRequest) -> CaptureSession:
        self.calls += 1
        session = self._inner(request)
        if self._state is SessionState.SEALED:
            session.stop(reason="orchestrator-error")  # the real X-3: seals the session
        else:
            session._state = self._state  # type: ignore[attr-defined]
        assert session.state is self._state
        for name in ("stop", "complete", "run_act"):
            def recorder(*args, _name=name, **kwargs):  # type: ignore[no-untyped-def]
                self.session_calls.append(_name)
                raise AssertionError(f"orchestrator called {_name} on a refused session")

            setattr(session, name, recorder)
        return session


@pytest.mark.parametrize("state", [SessionState.SEALED, SessionState.INTERRUPTED])
def test_a_factory_that_returns_a_disallowed_state_is_refused_at_the_boundary(
    tmp_path: Path, state: SessionState
) -> None:
    host = Host.under(tmp_path)
    factory = _ReturnsInState(PlanLauncher(), state)
    launcher = factory._inner.launcher
    with pytest.raises(PassAPlanRefused) as caught:
        run(host, launcher, plan(2), session_factory=factory)
    assert caught.value.reason == "malformed-session"
    assert factory.calls == 1 and len(factory._inner.requests) == 1
    assert factory.session_calls == [], "no finalization or act on the refused session"
    assert launcher.calls == []


def test_a_factory_that_raises_propagates_with_no_session_to_finalize(tmp_path: Path) -> None:
    host = Host.under(tmp_path)

    def factory(request: GenesisRequest) -> CaptureSession:
        raise RuntimeError("factory bug")

    with pytest.raises(RuntimeError, match="factory bug"):
        run(host, PlanLauncher(), plan(1), session_factory=factory)
    assert finals(host) == []


# --- a failing stop attempt never masks the original error -------------------------------


class _StopFails:
    """A factory whose session's one stop attempt raises ``error`` (the real X-3 never runs)."""

    def __init__(self, launcher, error: BaseException) -> None:  # type: ignore[no-untyped-def]
        self._inner = RecordingFactory(launcher)
        self._error = error
        self.stop_calls = 0

    def __call__(self, request: GenesisRequest) -> CaptureSession:
        session = self._inner(request)

        def stop(*, reason, step_or_case_id=None):  # type: ignore[no-untyped-def]
            self.stop_calls += 1
            raise self._error

        session.stop = stop  # type: ignore[method-assign]
        return session


def _policy_bug(request, outcome):  # type: ignore[no-untyped-def]
    raise LookupError("policy bug")


def test_a_stop_attempt_that_raises_does_not_replace_the_original_error(tmp_path: Path) -> None:
    host = Host.under(tmp_path)
    launcher = PlanLauncher()
    factory = _StopFails(launcher, OSError("stop bug"))
    with pytest.raises(LookupError, match="policy bug") as caught:
        run(host, launcher, plan(3), policy=_policy_bug, session_factory=factory)
    assert factory.stop_calls == 1, "one stop attempt, never retried"
    assert len(launcher.calls) == 1
    assert caught.value.__notes__ == [f"{pass_a.NOTE_STOP_ATTEMPT_FAILED} OSError"]
    assert "stop bug" not in "".join(caught.value.__notes__), "the note names the type only"


def test_an_error_whose_stop_attempt_succeeds_carries_no_note(tmp_path: Path) -> None:
    host = Host.under(tmp_path)
    launcher = PlanLauncher()
    with pytest.raises(LookupError) as caught:
        run(host, launcher, plan(3), policy=_policy_bug)
    assert getattr(caught.value, "__notes__", []) == []


def test_an_interruption_during_the_stop_attempt_propagates_over_the_original(tmp_path: Path) -> None:
    host = Host.under(tmp_path)
    launcher = PlanLauncher()
    factory = _StopFails(launcher, CaptureInterrupted("seam"))
    with pytest.raises(CaptureInterrupted) as caught:
        run(host, launcher, plan(3), policy=_policy_bug, session_factory=factory)
    assert factory.stop_calls == 1
    assert isinstance(caught.value.__context__, LookupError), "the original stays reachable"


# --- malformed plans are refused before any effect ---------------------------------------


def _generator():
    yield from plan(1)


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"acts": ()}, "empty-plan"),
        ({"acts": []}, "empty-plan"),
        ({"acts": _generator()}, "malformed-plan"),
        ({"acts": iter(plan(1))}, "malformed-plan"),
        ({"acts": {0}}, "malformed-plan"),
        ({"acts": "A1-01"}, "malformed-plan"),
        ({"acts": (plan(1)[0], {"argv": ()})}, "malformed-plan"),
        ({"acts": (None,)}, "malformed-plan"),
        ({"exit_policy": None}, "malformed-policy"),
        ({"exit_policy": "accept"}, "malformed-policy"),
        ({"genesis": {"capture_root": "x"}}, "malformed-request"),
        ({"session_factory": None}, "malformed-factory"),
        ({"session_factory": "create"}, "malformed-factory"),
    ],
)
def test_a_malformed_plan_or_policy_is_refused_before_any_effect(
    tmp_path: Path, overrides: dict, reason: str
) -> None:
    host = Host.under(tmp_path)
    launcher = PlanLauncher()
    filesystem = FaultFilesystem()
    acts = overrides.pop("acts", plan(1))
    policy = overrides.pop("exit_policy", accept_zero)
    with pytest.raises(PassAPlanRefused) as caught:
        run(host, launcher, acts, policy=policy, filesystem=filesystem, **overrides)
    assert caught.value.reason == reason and str(caught.value) == reason
    assert launcher.calls == [] and filesystem.calls == [] and not Path(host.root()).exists()


def test_an_unknown_plan_refusal_reason_cannot_be_raised() -> None:
    with pytest.raises(ValueError):
        PassAPlanRefused("because " + ACTIVATION)


# --- the module is policy-neutral, composes the existing parts and is imported, never called, by the entry --------------


def _tree() -> ast.Module:
    return ast.parse(SOURCE.read_text(encoding="utf-8"))


def test_the_module_contains_no_operational_value() -> None:
    tree = _tree()
    docstrings = {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef))
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
    }
    exported = {
        id(constant)
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(getattr(target, "id", None) == "__all__" for target in node.targets)
        for constant in ast.walk(node.value)
    }
    strings, numbers = [], []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and id(node) not in docstrings | exported:
            if isinstance(node.value, str):
                strings.append(node.value)
            elif isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
                numbers.append(node.value)
    # only fixed lower-case reason codes, enum values and one fixed message: no path,
    # argv, identifier or unit name
    assert all(all(c in "abcdefghijklmnopqrstuvwxyz- " for c in value) for value in strings), strings
    assert numbers == [], "no timeout, bound or other numeric value is chosen here"
    bare = ast.parse(SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(bare):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)) and ast.get_docstring(node):
            node.body = node.body[1:] or [ast.Pass()]
    code = ast.unparse(bare)
    for forbidden in ("/usr", "/run", "/var", "/etc", "systemctl", "rp11-act", "C-P5.0", "freedom-", "INVOCATION_ID"):
        assert forbidden not in code, forbidden


def test_the_module_reaches_nothing_outside_the_capture_mechanism_and_the_binding() -> None:
    tree = _tree()
    external = {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and not node.level
    } | {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert external <= {"__future__", "dataclasses", "enum", "typing"}
    names = {
        getattr(node, "id", None) or getattr(node, "attr", None)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Name, ast.Attribute))
    }
    assert not names & {
        "open", "os", "subprocess", "socket", "sys", "environ", "getenv", "Path", "StreamCaptureLauncher",
        "PosixCaptureFilesystem", "SystemUtcClock", "launch", "sleep", "time", "signal",
        "create_capture_session",
    }, "it must not start, time or touch anything itself except through the session"
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    assert not imported & {
        "create_capture_session", "StreamCaptureLauncher", "PosixCaptureFilesystem", "SystemUtcClock",
        "ProcessLauncher", "UtcClock", "CaptureFilesystem", "ReadOnlyFilesystem",
    }, "the session is built by the injected factory, never here (G8 composition lives in the entry)"


def test_the_one_stop_transition_is_the_only_finalization_it_uses() -> None:
    tree = _tree()
    called = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert {"stop", "complete", "binding"} <= called
    assert called.isdisjoint({"_stop_transition", "_finalize_once", "_external_end", "_x3_attempted", "_genesis"})


def _entry_sources() -> tuple[str, ...]:
    spec = importlib.util.spec_from_file_location("rp11_pass_a_build", ROOT / "infra/rp11-h1/build.py")
    module = importlib.util.module_from_spec(spec)
    previous, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module.ENTRY_SOURCES


def test_it_imports_only_modules_in_the_entry_closure_and_the_entry_never_calls_it() -> None:
    declared = set(_entry_sources())
    package = "tools/phase_5_0_evidence"
    needed = set()
    for node in ast.walk(_tree()):
        if isinstance(node, ast.ImportFrom) and node.level:
            base = Path(package) / "execution" if node.level == 1 else Path(package)
            module = (node.module or "").replace(".", "/")
            needed.add(str(base / f"{module}.py"))
    assert needed and needed <= declared, sorted(needed - declared)
    assert "tools/phase_5_0_evidence/execution/pass_a.py" in declared, "G8: the entry's closure carries it"
    entry_tree = ast.parse((ROOT / "infra/rp11-h1/rp11_entry.py").read_text(encoding="utf-8"))
    imports = [
        alias.name
        for node in ast.walk(entry_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    ]
    assert "tools.phase_5_0_evidence.execution.pass_a" in imports
    used = {getattr(n, "id", None) or getattr(n, "attr", None) for n in ast.walk(entry_tree)}
    assert not used & {"run_pass_a", "require_start_binding", "PassAResult", "PassAStatus"}, (
        "imported for the closure only: G2-G7 inputs are absent, so nothing calls it"
    )
