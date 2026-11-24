"""Opt-in, synthetic timing measurement of the Pass A plan on ``oracle-test`` (G7).

Skipped unless **all** of: the host name is ``Test`` (the disposable host), and
``RP11_PASS_A_MEASURE_OUT`` and ``RP11_PASS_A_SYNTH_CHECKOUT`` are set. It runs the real
plan's argv and complete environments, through the real armed launcher and a real capture
session, against a *scratch* clone standing in for the selected checkout and a scratch
capture root. It never touches the selected paths, never creates the ``capture`` account
and is not an operational pass. The deadlines are generous test values, but the exit policy
is the plan's own (``plan.exit_policy()``): a status the plan does not list for a step, or
any signal, stops the pass, and every recorded outcome is asserted against that policy
again, so a round that "completed" with an unexpected exit is refused, never sampled.
The output is a JSON statement of timings, sizes and the exit of every step.

One *sample* of a class is the slowest step of that class in one whole run, so a sample is
already a worst case within its round.
"""

from __future__ import annotations

import json
import os
import socket
import time
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from tools.phase_5_0_evidence.capture_contract import ExitOutcome
from tests.phase_5_0_evidence.rp11_fixtures import (
    TOOL_SHA256,
    FaultFilesystem,
    FixedClock,
    Host,
    rp11_release_descriptors,  # noqa: F401 - autouse fixture, active by import
)
from tests.test_rp11_pass_a import ACTIVATION, INVOCATION_ID, consume_journal
from tools.phase_5_0_evidence.execution import pass_a_plan as plan_module
from tools.phase_5_0_evidence.execution.boundary import StreamCaptureLauncher
from tools.phase_5_0_evidence.execution.capture_mechanism import (
    ActRequest,
    GenesisRequest,
    create_capture_session,
)
from tools.phase_5_0_evidence.execution.pass_a import PassAStatus, run_pass_a

OUT = os.environ.get("RP11_PASS_A_MEASURE_OUT")
SYNTH = os.environ.get("RP11_PASS_A_SYNTH_CHECKOUT")
ROUNDS = int(os.environ.get("RP11_PASS_A_MEASURE_ROUNDS", "12"))
GENEROUS_SECONDS = 900.0

LABEL = os.environ.get("RP11_PASS_A_MEASURE_LABEL", "unlabelled")

needs_host = pytest.mark.skipif(
    not (OUT and SYNTH and socket.gethostname() == "Test"),
    reason="opt-in measurement: needs host 'Test', RP11_PASS_A_MEASURE_OUT and RP11_PASS_A_SYNTH_CHECKOUT",
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


def _rebased_acts(plan: plan_module.PassAPlan) -> tuple[ActRequest, ...]:
    return tuple(
        ActRequest(
            step_or_case_id=a.step_or_case_id,
            argv=tuple(_rebase(x) for x in a.argv),
            environment={k: _rebase(v) for k, v in a.environment.items()},
            stream_bound_bytes=a.stream_bound_bytes,
            timeout_seconds=GENEROUS_SECONDS,
            drain_seconds=a.drain_seconds,
        )
        for a in plan.acts()
    )


def _run_round(plan: plan_module.PassAPlan, acts: tuple[ActRequest, ...], round_dir: Path):  # type: ignore[no-untyped-def]
    round_dir.mkdir()
    host = Host.under(round_dir)
    launcher = TimingLauncher()

    def factory(request: GenesisRequest):  # type: ignore[no-untyped-def]
        return create_capture_session(request, filesystem=FaultFilesystem(), launcher=launcher, clock=FixedClock())

    started = time.monotonic()
    result = run_pass_a(
        activation_id=ACTIVATION,
        consume_journal=consume_journal(),
        genesis=GenesisRequest(
            capture_root=host.root(),
            pass_id=plan_module.PASS_ID,
            tool_sha256=TOOL_SHA256,
            invocation_id=INVOCATION_ID,
            policy=host.policy(),
        ),
        acts=acts,
        exit_policy=plan.exit_policy(),
        session_factory=factory,
    )
    return result, launcher, time.monotonic() - started


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


@needs_host
def test_control_a_real_unexpected_exit_stops_the_pass_and_is_refused(tmp_path: Path) -> None:
    """Regression control: ``uname -n`` exits 0; a plan that expects 3 must not complete."""
    plan = plan_module.build_pass_a_plan(include_corroboration=True)
    wrong = tuple(
        plan_module.PlannedStep(st.step_id, st.command_class, st.environment, st.argv, (3,), st.auth_row)
        if st.step_id == "A1-01"
        else st
        for st in plan.steps
    )
    wrong_plan = plan_module.PassAPlan(wrong, plan.classes)
    result, launcher, _ = _run_round(wrong_plan, _rebased_acts(wrong_plan), tmp_path / "control")
    assert result.status is not PassAStatus.COMPLETED
    assert len(launcher.rows) < len(wrong_plan.steps)  # it stopped at the first unexpected exit
    with pytest.raises(UnexpectedOutcome):
        verify_recorded_outcomes(wrong_plan, launcher.rows)


@needs_host
def test_measure_the_plan_on_the_disposable_host(tmp_path: Path) -> None:
    plan = plan_module.build_pass_a_plan(include_corroboration=True)
    acts = _rebased_acts(plan)
    rounds: list[dict] = []
    for round_number in range(ROUNDS):
        load_before = os.getloadavg()
        result, launcher, wall = _run_round(plan, acts, tmp_path / f"r{round_number}")
        load_after = os.getloadavg()
        assert result.status is PassAStatus.COMPLETED, result.reason
        verify_recorded_outcomes(plan, launcher.rows)
        children = sum(row["seconds"] for row in launcher.rows)
        rounds.append(
            {
                "wall_seconds": wall,
                "child_seconds": children,
                "mechanism_seconds": wall - children,
                "loadavg_before": load_before,
                "loadavg_after": load_after,
                "steps": [
                    {"step": step.step_id, "class": step.command_class, "accepted": step.accepted_exits, **row}
                    for step, row in zip(plan.steps, launcher.rows, strict=True)
                ],
            }
        )
    Path(OUT).write_text(
        json.dumps(
            {"host": socket.gethostname(), "label": LABEL, "user": os.environ.get("USER"), "acts": len(acts), "rounds": rounds},
            indent=1,
        )
    )
