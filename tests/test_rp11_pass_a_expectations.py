"""D1 evaluation of RP-11 Pass A expected results, on synthetic values only.

Pure: no process, no host, no capture session, no ``run_pass_a``. Every output
below is invented for the test. None is an observation of a host, and the
``ENOENT`` line in particular is **not** a reviewed or pinned form.
"""

from __future__ import annotations

import ast
import dataclasses
from pathlib import Path

import pytest

from tools import rp11_pass_a_expectations as V
from tools.phase_5_0_evidence.capture_contract import (
    CaptureRecord,
    ExitOutcome,
    StreamBinding,
    sha256_hex,
    stream_name,
)
from tools.phase_5_0_evidence.execution import pass_a_plan as P

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "tools/rp11_pass_a_expectations.py"

PLAN = tuple(V.PlannedAct(s.step_id, s.argv) for s in P.build_pass_a_plan().steps)
ARGV = {act.step_id: act.argv for act in PLAN}
ENOENT = f"stat: cannot statx '{P.EVIDENCE_RUN_ROOT}': No such file or directory\n".encode()

DRY_RUN = {
    "steps planned": "7",
    "mutations declared": "3",
    "cleanup steps derived": "4",
    "unresolved conflicts": "1 (X-1)",
    "unconfirmed facts": "synthetic_fact (each one refuses)",
    "review manifest digest": "d" * 64,
    "executable": "False",
}
EXPECTED = V.Expectations(
    pass_id=P.PASS_ID,
    pinned_commit="a" * 40,
    prompt_sha256="1" * 64,
    manifest_json_sha256="2" * 64,
    concrete_plan_sha256="3" * 64,
    source_sha256={name: str(4 + i) * 64 for i, name in enumerate(V.SOURCE_PIN_NAMES)},
    dry_run=DRY_RUN,
    nodename="synthetic-node",
    kernel_release="0.0.0-synthetic",
    machine="synthetic64",
    os_pretty_name="Synthetic OS 1",
    var_lib_source="/dev/synthetic1",
    var_lib_fstype="synthfs",
    run_root_enoent_stderr=ENOENT,
)


def listing(step: str, digests) -> str:
    return "".join(f"{d}  {path}\n" for d, path in zip(digests, ARGV[step][1:]))


def dry_run_text(**changes: str) -> str:
    values = {**DRY_RUN, **changes}
    return V.DRY_RUN_HEADER + "\n  target : synthetic\n" + "".join(
        f"  {name:<22}: {value}\n" for name, value in values.items()
    )


def good_output(step: str) -> tuple[int, bytes, bytes]:
    base = step.replace("A1-Z-", "A1-")
    if base == "A1-19":
        return 1, b"", ENOENT
    if base.startswith("A1-23"):
        return 2, b"", b""
    text = {
        "A0-02a": "a" * 40 + "\n",
        "A0-02b": "",
        "A0-05": dry_run_text(),
        "A1-01": "synthetic-node\n",
        "A1-02": "0.0.0-synthetic\n",
        "A1-03": "synthetic64\n",
        "A1-04": 'PRETTY_NAME="Synthetic OS 1"\n',
        "A1-05": "00000000-1111-2222-3333-444444444444\n",
        "A1-06": "e" * 64 + "  /etc/machine-id\n",
        "A1-07": "/dev/synthetic1 synthfs rw,relatime\n",
        "A1-08": "fs.protected_hardlinks = 1\n",
        "A1-13": "(3, 14, 0) 1 1\n",
        "A1-20": "freedomlab:x:900:ubuntu\n",
        "A1-24": "LoadState=not-found\n",
        "A1-27": "",
        "A1-28": "",
        "A1-29": "active\n",
        "A1-30": "18 main 5432 online synthetic /synthetic /synthetic.log\n",
    }.get(base)
    if base == "A0-03":
        text = listing(base, ["1" * 64])
    elif base == "A0-04":
        text = listing(base, ["2" * 64, "3" * 64])
    elif base == "A1-S2":
        text = listing(base, EXPECTED.source_sha256.values())
    elif base == "A1-16":
        text = "".join(f"{path} root:root 755\n" for path in ARGV[base][2:])
    elif base == "A1-21":
        states = (
            "root:root 644 regular file",
            "root:root 755 directory",
            "root:freedomlab 750 directory",
            "root:root 700 directory",
        )
        text = "".join(f"{p} {s}\n" for p, s in zip(ARGV[step][2:], states))
    elif text is None:
        text = "synthetic observation\n"
    return 0, text.encode(), b""


def evidence(
    step: str,
    *,
    status: int | None = None,
    kind: str = "status",
    stdout: bytes | None = None,
    stderr: bytes | None = None,
    argv: tuple[str, ...] | None = None,
) -> V.ActEvidence:
    default_status, default_out, default_err = good_output(step)
    out = default_out if stdout is None else stdout
    err = default_err if stderr is None else stderr
    seq = V.STEP_IDS.index(step) + 1
    record = CaptureRecord(
        pass_id=P.PASS_ID,
        capture_seq=seq,
        step_or_case_id=step,
        argv=ARGV[step] if argv is None else argv,
        clock_source="synthetic",
        started_utc="2026-01-01T00:00:00.000000Z",
        ended_utc="2026-01-01T00:00:01.000000Z",
        exit=ExitOutcome(kind, default_status if status is None else status),
        stream_bound_bytes=1 << 20,
        stdout=StreamBinding(stream_name(seq, "stdout"), sha256_hex(out), len(out)),
        stderr=StreamBinding(stream_name(seq, "stderr"), sha256_hex(err), len(err)),
    )
    return V.ActEvidence(True, sha256_hex(record.to_bytes()), record, out, err)


def run(overrides=None, expected: V.Expectations = EXPECTED) -> V.Evaluation:
    overrides = overrides or {}
    return V.evaluate_pass(expected, PLAN, [overrides.get(s) or evidence(s) for s in V.STEP_IDS])


def failed_at(result: V.Evaluation, step: str, outcome: V.Outcome, reason: str) -> None:
    failure = result.first_failure
    assert not result.established
    assert failure is not None
    assert (failure.step_id, failure.outcome, failure.reason) == (step, outcome, reason)
    assert result.verdicts[-1] is failure, "nothing after the first failure is judged"


# --- agreement with the plan ----------------------------------------------------------


def test_the_step_list_exits_and_final_pairs_agree_with_the_plan() -> None:
    steps = P.build_pass_a_plan().steps
    assert V.STEP_IDS == tuple(s.step_id for s in steps) and len(steps) == 49
    for step in steps:
        assert step.accepted_exits == (V._accepted_status(step.step_id),), step.step_id
    by_id = {s.step_id: s for s in steps}
    assert set(V.FINAL_SURVEY_PAIRS) == {s for s in by_id if s.startswith("A1-Z-")}
    for last, first in V.FINAL_SURVEY_PAIRS.items():
        assert (by_id[last].argv, by_id[last].environment) == (by_id[first].argv, by_id[first].environment)


def test_a_complete_matching_synthetic_pass_is_established_and_cited() -> None:
    result = run()
    assert result.established and result.first_failure is None
    assert [v.capture_seq for v in result.verdicts] == list(range(1, 50))
    assert all(v.record_sha256 and v.stdout_sha256 and v.stderr_sha256 for v in result.verdicts)
    recorded = {v.step_id for v in result.verdicts if v.outcome is V.Outcome.RECORDED}
    assert recorded == {"A1-09", "A1-10", "A1-17", "A1-18", "A1-25", "A1-26", "A1-27", "A1-28"}


# --- material gates -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("step", "stdout", "reason"),
    [
        ("A0-02a", b"b" * 40 + b"\n", "value"),
        ("A0-02a", b"a" * 40, "value"),
        ("A0-02b", b" M file\n", "dirty-checkout"),
        ("A0-03", listing("A0-03", ["9" * 64]).encode(), "digest"),
        ("A0-04", listing("A0-04", ["2" * 64]).encode(), "digest"),
        ("A0-04", listing("A0-04", ["3" * 64, "2" * 64]).encode(), "digest"),
        ("A0-05", dry_run_text(executable="True").encode(), "dry-run-value"),
        ("A0-05", dry_run_text(**{"review manifest digest": "c" * 64}).encode(), "dry-run-value"),
        ("A0-05", dry_run_text().replace("  executable", "  other").encode(), "dry-run-field-count"),
        ("A0-05", (dry_run_text() + "  executable : False\n").encode(), "dry-run-field-count"),
        ("A0-05", dry_run_text()[:-1].encode(), "unreadable-output"),
        ("A0-05", b"synthetic\n" + dry_run_text().encode(), "dry-run-header"),
        ("A1-S2", listing("A1-S2", ["4" * 64] * 5).encode(), "digest"),
        ("A1-01", b"other\n", "value"),
        ("A1-02", b"0.0.1\n", "value"),
        ("A1-03", b"aarch64\n", "value"),
        ("A1-04", b'PRETTY_NAME="Other"\n', "value"),
        ("A1-05", b"unreadable\n", "form"),
        ("A1-06", b"e" * 64 + b"  /etc/other\n", "form"),
        ("A1-07", b"/dev/synthetic1 synthfs ro\n", "mount-not-rw"),
        ("A1-07", b"/dev/other synthfs rw\n", "mount"),
        ("A1-08", b"fs.protected_hardlinks = 0\n", "value"),
        ("A1-09", b"", "unreadable-output"),
        ("A1-13", b"(3, 12, 3) 1 1\n", "form"),
        ("A1-13", b"(3, 14, 0) 0 1\n", "form"),
        ("A1-16", "".join(f"{p} root:root 775\n" for p in ARGV["A1-16"][2:]).encode(), "writable"),
        ("A1-16", f"{ARGV['A1-16'][2]} root:root 755\n".encode(), "line-count"),
        ("A1-20", b"freedomlab:x:900:other\n", "member"),
        ("A1-21", good_output("A1-21")[1].replace(b" 700 ", b" 755 "), "value"),
        ("A1-23d", b"fbprobe:x:1:\n", "unexpected-stdout"),
        ("A1-24", b"LoadState=loaded\n", "value"),
        ("A1-29", b"inactive\n", "value"),
        ("A1-30", good_output("A1-30")[1] + b"16 main 5433 online x y z\n", "line-count"),
        ("A1-30", b"18 main 5432 down x y z\n", "cluster"),
    ],
)
def test_a_wrong_value_with_the_accepted_exit_stops(step: str, stdout: bytes, reason: str) -> None:
    failed_at(run({step: evidence(step, stdout=stdout)}), step, V.Outcome.MISMATCH, reason)


@pytest.mark.parametrize("step", V.STEP_IDS)
def test_every_step_stops_on_another_status_and_on_a_signal(step: str) -> None:
    status = good_output(step)[0]
    failed_at(run({step: evidence(step, status=status + 3)}), step, V.Outcome.MISMATCH, "exit")
    failed_at(run({step: evidence(step, kind="signal", status=status)}), step, V.Outcome.MISMATCH, "exit")


@pytest.mark.parametrize("step", [s for s in V.STEP_IDS if not s.endswith("-19")])
def test_unexpected_stderr_stops_every_step(step: str) -> None:
    failed_at(run({step: evidence(step, stderr=b"warning\n")}), step, V.Outcome.MISMATCH, "unexpected-stderr")


# --- absence --------------------------------------------------------------------------


@pytest.mark.parametrize("step", ["A1-19", "A1-Z-19"])
@pytest.mark.parametrize(
    "stderr",
    [
        f"stat: cannot statx '{P.EVIDENCE_RUN_ROOT}': Permission denied\n".encode(),
        ENOENT[:-1] + b": Permission denied\n",
        ENOENT + ENOENT,
        ENOENT + b"extra\n",
        ENOENT[:-1],
        b"",
    ],
)
def test_exit_one_without_the_exact_diagnostic_is_not_absence(step: str, stderr: bytes) -> None:
    failed_at(run({step: evidence(step, stderr=stderr)}), step, V.Outcome.MISMATCH, "not-the-enoent-diagnostic")


def test_exit_one_with_stdout_is_not_absence() -> None:
    result = run({"A1-19": evidence("A1-19", stdout=b"directory\n")})
    failed_at(result, "A1-19", V.Outcome.MISMATCH, "unexpected-stdout")


def test_without_a_reviewed_enoent_form_absence_is_unestablished() -> None:
    result = run(expected=dataclasses.replace(EXPECTED, run_root_enoent_stderr=None))
    failed_at(result, "A1-19", V.Outcome.UNESTABLISHED, "no-reviewed-enoent-form")


def test_a_form_naming_another_path_does_not_establish_absence() -> None:
    other = b"stat: cannot statx '/other': No such file or directory\n"
    result = run(
        {"A1-19": evidence("A1-19", stderr=other)},
        expected=dataclasses.replace(EXPECTED, run_root_enoent_stderr=other),
    )
    failed_at(result, "A1-19", V.Outcome.MISMATCH, "enoent-form-names-another-path")


_ROOT_QUOTED = f"'{P.EVIDENCE_RUN_ROOT}'"
_REASON = "No such file or directory"


@pytest.mark.parametrize(
    "form",
    [
        # The phrase and the path, in the wrong places or with company.
        f"{_REASON} {P.EVIDENCE_RUN_ROOT}\n",
        f"stat: {_REASON}: {_ROOT_QUOTED}\n",
        f"stat: cannot statx '/other': {_REASON} {P.EVIDENCE_RUN_ROOT}\n",
        f"stat: cannot statx {_ROOT_QUOTED}: Permission denied ({_REASON})\n",
        f"stat: cannot statx {_ROOT_QUOTED}: Permission denied: {_REASON}\n",
        f"stat: cannot statx {_ROOT_QUOTED}: {_REASON}: Permission denied\n",
        f"stat: cannot statx {_ROOT_QUOTED}: {_REASON} (cached)\n",
        f"stat: cannot statx '/other': Permission denied; stat: cannot statx {_ROOT_QUOTED}: {_REASON}\n",
        f"warning stat: cannot statx {_ROOT_QUOTED}: {_REASON}\n",
        f"ls: cannot access {_ROOT_QUOTED}: {_REASON}\n",
        f"stat: cannot statx {P.EVIDENCE_RUN_ROOT}: {_REASON}\n",
        f"stat: cannot statx {_ROOT_QUOTED}: {_REASON}\r\n",
        f"stat: cannot statx {_ROOT_QUOTED}: {_REASON}",
    ],
)
def test_a_form_that_is_not_one_anchored_enoent_diagnostic_is_refused(form: str) -> None:
    with pytest.raises(V.ExpectationRefused):
        dataclasses.replace(EXPECTED, run_root_enoent_stderr=form.encode())


@pytest.mark.parametrize("path", [P.EVIDENCE_RUN_ROOT + "-old", P.EVIDENCE_RUN_ROOT + "/child", "/var/lib"])
def test_a_form_for_a_neighbouring_path_does_not_establish_absence(path: str) -> None:
    other = f"stat: cannot statx '{path}': {_REASON}\n".encode()
    result = run(
        {"A1-19": evidence("A1-19", stderr=other)},
        expected=dataclasses.replace(EXPECTED, run_root_enoent_stderr=other),
    )
    failed_at(result, "A1-19", V.Outcome.MISMATCH, "enoent-form-names-another-path")


# --- recorded observations ------------------------------------------------------------


@pytest.mark.parametrize("step", ["A1-09", "A1-10", "A1-17", "A1-18", "A1-25", "A1-26"])
@pytest.mark.parametrize("stdout", [b"\n", b"   \n", b"\t\n \n\n"])
def test_blank_output_is_not_an_observation(step: str, stdout: bytes) -> None:
    failed_at(run({step: evidence(step, stdout=stdout)}), step, V.Outcome.MISMATCH, "blank-output")


# --- final survey ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("step", "stdout"),
    [
        ("A1-Z-30", b"18 main 5432 online synthetic /moved /synthetic.log\n"),
    ],
)
def test_a_final_reading_that_passes_alone_but_differs_stops(step: str, stdout: bytes) -> None:
    failed_at(run({step: evidence(step, stdout=stdout)}), step, V.Outcome.MISMATCH, "final-survey-differs")


@pytest.mark.parametrize("step", sorted(V.FINAL_SURVEY_PAIRS))
def test_a_final_reading_without_its_first_reading_is_unestablished(step: str) -> None:
    result = V.evaluate_act(EXPECTED, PLAN, V.STEP_IDS.index(step), evidence(step), {})
    assert (result.outcome, result.reason) == (V.Outcome.UNESTABLISHED, "first-reading-not-established")


def test_two_equal_but_wrong_readings_do_not_count() -> None:
    wrong = b"inactive\n"
    earlier = {"A1-29": evidence("A1-29", stdout=wrong)}
    result = V.evaluate_act(
        EXPECTED, PLAN, V.STEP_IDS.index("A1-Z-29"), evidence("A1-Z-29", stdout=wrong), earlier
    )
    assert not result.permits_continuation


# --- partial and ambiguous evidence ---------------------------------------------------


@pytest.mark.parametrize(
    ("changes", "outcome", "reason"),
    [
        ({"admitted": False}, V.Outcome.UNESTABLISHED, "not-admitted"),
        ({"admitted": 1}, V.Outcome.UNESTABLISHED, "not-admitted"),
        ({"admitted_record_sha256": None}, V.Outcome.UNESTABLISHED, "not-admitted"),
        ({"record": None}, V.Outcome.UNESTABLISHED, "not-admitted"),
        ({"stdout": None}, V.Outcome.UNESTABLISHED, "stream-missing"),
        ({"stderr": None}, V.Outcome.UNESTABLISHED, "stream-missing"),
        ({"admitted_record_sha256": "0" * 64}, V.Outcome.MISMATCH, "record-digest"),
        ({"stdout": b"synthetic-no"}, V.Outcome.MISMATCH, "stream-digest"),
        ({"stderr": b"x"}, V.Outcome.MISMATCH, "stream-digest"),
    ],
)
def test_unbound_evidence_never_counts(changes, outcome, reason) -> None:
    broken = dataclasses.replace(evidence("A1-01"), **changes)
    failed_at(run({"A1-01": broken}), "A1-01", outcome, reason)


def test_a_record_of_another_act_argv_or_pass_never_counts() -> None:
    other_argv = evidence("A1-01", argv=("/usr/bin/uname", "-r"))
    for wrong in (other_argv, evidence("A1-02")):
        failed_at(run({"A1-01": wrong}), "A1-01", V.Outcome.MISMATCH, "record-not-the-planned-act")
    result = run(expected=dataclasses.replace(EXPECTED, pass_id="other-pass"))
    failed_at(result, "A0-02a", V.Outcome.MISMATCH, "record-not-the-planned-act")


@pytest.mark.parametrize("count", [0, 1, 36, 48])
def test_a_short_pass_is_never_established(count: int) -> None:
    result = V.evaluate_pass(EXPECTED, PLAN, [evidence(s) for s in V.STEP_IDS[:count]])
    failed_at(result, V.STEP_IDS[count], V.Outcome.UNESTABLISHED, "no-evidence")


def test_a_hand_built_partial_evaluation_is_not_established() -> None:
    assert not V.Evaluation(()).established
    assert not V.Evaluation(run().verdicts[:-1]).established


def test_surplus_evidence_and_altered_plans_are_refused() -> None:
    everything = [evidence(s) for s in V.STEP_IDS]
    with pytest.raises(V.ExpectationRefused):
        V.evaluate_pass(EXPECTED, PLAN, [*everything, everything[-1]])
    for plan in (PLAN[:-1], PLAN[:37], (PLAN[1], PLAN[0], *PLAN[2:]), ()):
        with pytest.raises(V.ExpectationRefused):
            V.evaluate_pass(EXPECTED, plan, [])
    for index in (-1, 49, True):
        with pytest.raises(V.ExpectationRefused):
            V.evaluate_act(EXPECTED, PLAN, index, None, {})


# --- required inputs ------------------------------------------------------------------


def test_every_expected_value_is_required_and_has_no_default() -> None:
    for field in dataclasses.fields(V.Expectations):
        assert field.default is dataclasses.MISSING and field.default_factory is dataclasses.MISSING


@pytest.mark.parametrize(
    "changes",
    [
        {"pinned_commit": "HEAD"},
        {"prompt_sha256": ""},
        {"source_sha256": {"journal.py": "4" * 64}},
        {"dry_run": {k: v for k, v in DRY_RUN.items() if k != "executable"}},
        {"dry_run": {**DRY_RUN, "executable": "True"}},
        {"nodename": ""},
        {"run_root_enoent_stderr": b""},
        {"run_root_enoent_stderr": b"stat: Permission denied\n"},
    ],
)
def test_malformed_expectations_are_refused(changes) -> None:
    with pytest.raises(V.ExpectationRefused):
        dataclasses.replace(EXPECTED, **changes)


def test_changing_the_callers_mappings_cannot_change_what_is_expected() -> None:
    sources = dict(EXPECTED.source_sha256)
    dry_run = dict(DRY_RUN)
    expected = dataclasses.replace(EXPECTED, source_sha256=sources, dry_run=dry_run)
    sources["journal.py"] = "9" * 64
    dry_run["executable"] = "True"

    assert run(expected=expected).established
    changed_sources = listing("A1-S2", sources.values()).encode()
    result = run({"A1-S2": evidence("A1-S2", stdout=changed_sources)}, expected)
    failed_at(result, "A1-S2", V.Outcome.MISMATCH, "digest")
    changed_dry_run = dry_run_text(executable="True").encode()
    result = run({"A0-05": evidence("A0-05", stdout=changed_dry_run)}, expected)
    failed_at(result, "A0-05", V.Outcome.MISMATCH, "dry-run-value")
    for mapping in (expected.source_sha256, expected.dry_run):
        with pytest.raises(TypeError):
            mapping["journal.py"] = "9" * 64  # type: ignore[index]


# --- containment ----------------------------------------------------------------------


def test_the_module_is_pure_and_nothing_operational_imports_it() -> None:
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    imported = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    imported |= {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    assert imported == {
        "__future__", "re", "dataclasses", "enum", "types", "typing", "phase_5_0_evidence.capture_contract",
    }
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    assert not names & {"open", "exec", "eval", "__import__", "run_pass_a"}
    for relative in ("infra", "tools", "application", "adapters", "domain"):
        for path in (ROOT / relative).rglob("*.py"):
            if path != MODULE and "__pycache__" not in path.parts:
                assert "rp11_pass_a_expectations" not in path.read_text(encoding="utf-8"), path
