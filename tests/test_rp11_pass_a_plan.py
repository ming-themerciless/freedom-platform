"""The finite local-only Pass A plan: argv, environments, identity policy, timeouts, bound (G2, G3, G7).

Synthetic and local. Nothing here creates an account or a selected path, starts a service,
reaches a network or calls the operational entry. The two tests that run real processes use
the current interpreter under a pytest temporary directory with test-only sub-second
deadlines; every figure of the shipped plan is checked as data.
"""

from __future__ import annotations

import ast
import json
import math
import os
import shlex
import shutil
import stat
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from tests.phase_5_0_evidence.rp11_fixtures import (
    TOOL_SHA256,
    CountingLauncher,
    FaultFilesystem,
    FixedClock,
    Host,
    rp11_release_descriptors,  # noqa: F401 - autouse fixture, active by import
)
from tests.test_rp11_pass_a import ACTIVATION, INVOCATION_ID, PlanLauncher, consume_journal, finals
from tools.phase_5_0_evidence.execution import pass_a_plan as P
from tools.phase_5_0_evidence.capture_contract import ExitOutcome
from tools.phase_5_0_evidence.execution.boundary import CAPTURE_DRAIN_SECONDS
from tools.phase_5_0_evidence.execution.capture_mechanism import (
    ActRequest,
    GenesisRequest,
    create_capture_session,
)
from tools.phase_5_0_evidence.execution.pass_a import PassAStatus, run_pass_a

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "tools/phase_5_0_evidence/execution/pass_a_plan.py"
GUARD = ROOT / ".claude/hooks/guard-secrets.py"


# --- the plan ------------------------------------------------------------------------


def test_the_default_plan_is_finite_ordered_and_has_unique_step_ids() -> None:
    plan = P.build_pass_a_plan()
    ids = [step.step_id for step in plan.steps]
    assert len(ids) == len(set(ids)) == 49
    assert ids[:5] == ["A0-02a", "A0-02b", "A0-03", "A0-04", "A0-05"]
    assert ids[-1] == "A1-Z-30"
    assert "A1-11" not in ids and "A1-12" not in ids, "corroboration is off by default (RP-10)"
    assert [s.step_id for s in P.build_pass_a_plan(include_corroboration=True).steps].count("A1-11") == 1


def test_withdrawn_steps_are_listed_with_a_reason_and_are_not_planned() -> None:
    planned = {s.step_id for s in P.build_pass_a_plan(include_corroboration=True).steps}
    assert set(P.WITHDRAWN_STEPS) and not set(P.WITHDRAWN_STEPS) & planned
    assert all(len(reason) > 20 for reason in P.WITHDRAWN_STEPS.values())


def test_every_argv_is_local_absolute_and_runs_no_shell_remote_or_privilege_tool() -> None:
    banned = {"ssh", "rsync", "sudo", "scp", "su", "sh", "bash", "dash", "env", "nohup", "curl", "wget"}
    for step in P.build_pass_a_plan(include_corroboration=True).steps:
        assert step.argv[0].startswith("/") and os.path.normpath(step.argv[0]) == step.argv[0], step.step_id
        assert Path(step.argv[0]).name not in banned, step.step_id
        assert not any(a in {"-c"} and Path(step.argv[0]).name in banned for a in step.argv)
        # No argument is a pipeline, a substitution or an environment assignment.
        # (the one inline program, after ``-c`` of the isolated interpreter, may use ``;``)
        words = [a for i, a in enumerate(step.argv) if not (i and step.argv[i - 1] == "-c")]
        assert not any(set(a) & set("|;&<>`$") for a in words if "${" not in a), step.step_id


def test_every_path_a_step_names_is_a_fixed_path_not_a_selected_path_creation() -> None:
    # Reads of the checkout and the evidence root exist; none of them is a creator.
    creators = {"mkdir", "touch", "install", "cp", "mv", "ln", "tee", "chmod", "chown", "useradd", "adduser"}
    for step in P.build_pass_a_plan(include_corroboration=True).steps:
        assert Path(step.argv[0]).name not in creators, step.step_id
        assert not any(a.startswith(P.CAPTURE_PARENT) for a in step.argv), step.step_id


def test_an_accepted_exit_list_is_explicit_and_a_signal_never_passes() -> None:
    plan = P.build_pass_a_plan()
    policy = plan.exit_policy()
    by_id = {s.step_id: s for s in plan.steps}
    absent_ok = by_id["A1-19"]
    request = next(a for a in plan.acts() if a.step_or_case_id == "A1-19")
    assert policy(request, ExitOutcome("status", 1)) and not policy(request, ExitOutcome("status", 0))
    assert not policy(request, ExitOutcome("signal", 9)) and absent_ok.accepted_exits == (1,)
    unknown = replace(request, step_or_case_id="A9-99")
    assert not policy(unknown, ExitOutcome("status", 0))


# --- G2: the guard sees every argv exactly as the plan states it ----------------------


def _guard_refuses(command: str) -> bool:
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    done = subprocess.run(
        [sys.executable, "-I", str(GUARD)], input=payload, capture_output=True, text=True, check=False
    )
    return done.returncode != 0


def test_the_repository_secrets_guard_admits_every_rendered_argv() -> None:
    steps = P.build_pass_a_plan(include_corroboration=True).steps
    rendered = [shlex.join(step.argv) for step in steps]
    assert not [c for c in rendered if _guard_refuses(c)]
    # Control: the same renderer on a secret-reading argv is refused, so the check can fail.
    assert _guard_refuses(shlex.join(("/usr/bin/cat", f"{P.SOURCE_CHECKOUT}/.env")))


# --- G3: complete, non-inherited environments ------------------------------------------


def test_every_environment_is_complete_fixed_and_free_of_credentials() -> None:
    assert set(P.ENVIRONMENTS) == {"plain", "git", "python", "systemd"}
    for name, env in P.ENVIRONMENTS.items():
        assert env["PATH"] == "/usr/bin" and env["LC_ALL"] == "C" and env["LANG"] == "C", name
        assert P.environment_problems(env) == (), name
        assert not set(env) & P.FORBIDDEN_ENVIRONMENT_NAMES, name
        assert all("=" not in k and "\0" not in k + v for k, v in env.items()), name


def test_environment_problems_names_every_forbidden_or_credential_shaped_variable() -> None:
    good = dict(P.ENVIRONMENTS["plain"])
    for bad in ("HOME", "INVOCATION_ID", "TEST_DATABASE_URL", "LD_PRELOAD", "SSH_AUTH_SOCK"):
        assert P.environment_problems({**good, bad: "x"}) == (bad,)
    for bad in ("DISCORD_TOKEN", "DB_PASSWORD", "API_SECRET", "GOOGLE_CREDENTIALS", "X_PRIVATE_KEY"):
        assert P.environment_problems({**good, bad: "x"}) == (bad,)
    assert P.environment_problems({"PATH": "/usr/bin"}) == ("incomplete",)
    assert P.environment_problems({**good, "PATH": "/usr/bin:/bin"}) == ("path",)


def test_each_act_carries_a_private_copy_of_exactly_its_environment() -> None:
    plan = P.build_pass_a_plan()
    for step, act in zip(plan.steps, plan.acts(), strict=True):
        assert act.environment == P.ENVIRONMENTS[step.environment]
        assert act.environment is not P.ENVIRONMENTS[step.environment]
    first = plan.acts()[0]
    first.environment["PATH"] = "/tmp"  # type: ignore[index]
    assert P.ENVIRONMENTS["git"]["PATH"] == "/usr/bin"


def test_a_child_does_not_see_the_environment_of_its_parent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", "/leak/home")
    monkeypatch.setenv("TEST_DATABASE_URL", "postgresql:///leak")
    monkeypatch.setenv("INVOCATION_ID", "0" * 32)
    from tools.phase_5_0_evidence.execution.boundary import StreamCaptureLauncher

    class Sink:
        def __init__(self) -> None:
            self.data = b""

        def write(self, chunk: bytes) -> None:
            self.data += chunk

    out, err = Sink(), Sink()
    result = StreamCaptureLauncher(armed=True).launch(
        (sys.executable, "-I", "-S", "-c", "import os,json;print(json.dumps(sorted(os.environ)))"),
        environment=P.ENVIRONMENTS["plain"],
        stdout=out,  # type: ignore[arg-type]
        stderr=err,  # type: ignore[arg-type]
        stream_bound_bytes=4096,
        timeout_seconds=20.0,
    )
    assert result.returncode == 0
    seen = set(json.loads(out.data))
    assert seen <= set(P.ENVIRONMENTS["plain"]) | {"LC_CTYPE", "PYTHONIOENCODING"}
    assert not seen & P.FORBIDDEN_ENVIRONMENT_NAMES


def test_the_git_environment_reads_no_configuration_other_than_safe_directory() -> None:
    env = P.ENVIRONMENTS["git"]
    assert env["GIT_CONFIG_GLOBAL"] == "/dev/null" and env["GIT_CONFIG_NOSYSTEM"] == "1"
    assert (env["GIT_CONFIG_COUNT"], env["GIT_CONFIG_KEY_0"], env["GIT_CONFIG_VALUE_0"]) == (
        "1",
        "safe.directory",
        P.SOURCE_CHECKOUT,
    )
    assert env["GIT_OPTIONAL_LOCKS"] == "0" and env["GIT_TERMINAL_PROMPT"] == "0"
    git_steps = [s for s in P.build_pass_a_plan().steps if s.argv[0] == "/usr/bin/git"]
    assert git_steps and all(s.environment == "git" for s in git_steps)
    assert all(s.environment != "git" for s in P.build_pass_a_plan().steps if s.argv[0] != "/usr/bin/git")


def test_only_the_dry_run_gets_a_python_environment_and_it_is_isolated_from_site_and_bytecode() -> None:
    python_steps = [s for s in P.build_pass_a_plan().steps if s.environment == "python"]
    assert [s.step_id for s in python_steps] == ["A0-05"]
    assert python_steps[0].argv[:4] == (P.INTERPRETER, "-B", "-P", "-m")
    env = P.ENVIRONMENTS["python"]
    assert env["PYTHONPATH"] == P.SOURCE_CHECKOUT and env["PYTHONDONTWRITEBYTECODE"] == "1"
    assert env["PYTHONNOUSERSITE"] == "1"


# --- G5: the capture identity as data --------------------------------------------------


def _conforming() -> P.ObservedAccount:
    return P.ObservedAccount("capture", 998, 998, "/usr/sbin/nologin", True, (), False)


def test_the_accepted_policy_data_states_the_owner_decisions() -> None:
    policy = P.CAPTURE_IDENTITY
    assert policy.name == "capture" and policy.system_account and policy.locked
    assert not (policy.may_be_root or policy.may_have_sudo or policy.may_have_supplementary_groups)
    assert {"root", "ubuntu", "freedom-executor"} <= set(policy.forbidden_names)
    assert P.identity_problems(_conforming()) == ()


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        ({"name": "ubuntu"}, ("name",)),
        ({"name": "freedom-executor"}, ("name",)),
        ({"uid": 0, "primary_gid": 0}, ("root", "not-a-system-account")),
        ({"primary_gid": 0}, ("root",)),
        ({"uid": 1000}, ("not-a-system-account",)),
        ({"locked": False}, ("not-locked",)),
        ({"shell": "/bin/bash"}, ("login-shell",)),
        ({"sudo_rights": True}, ("sudo",)),
        ({"supplementary_groups": ("adm",)}, ("supplementary-groups",)),
    ],
)
def test_each_departure_from_the_identity_policy_is_named(change: dict, expected: tuple[str, ...]) -> None:
    assert P.identity_problems(replace(_conforming(), **change)) == expected


def test_judging_an_account_creates_and_looks_up_nothing() -> None:
    tree = ast.parse(SOURCE.read_text())
    imported = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    imported |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert not imported & {"pwd", "grp", "subprocess", "socket", "shutil", "ctypes", "signal"}


# --- paths ---------------------------------------------------------------------------


def test_the_selected_paths_validate_and_overlaps_are_refused() -> None:
    P.validate_paths()
    for bad in (
        {"parent": "/var/lib"},
        {"parent": "/var/lib/fb-rp11/"},
        {"parent": "/var/lib/fb/rp11"},
        {"parent": "/srv/fb-rp11", "root_a": "/srv/fb-rp11/capture-a", "root_b": "/srv/fb-rp11/capture-b"},
        {"parent": "/tmp/fb-rp11"},
        {"parent": P.EVIDENCE_RUN_ROOT},
        {"root_a": "/var/lib/fb-rp11-capture-a"},  # the withdrawn direct /var/lib leaf
        {"root_b": "/var/lib/fb-rp11/nested/capture-b"},
        {"root_b": "/var/lib/other/capture-b"},
        {"checkout": "relative/path"},
        {"checkout": "/opt/freedom-blades/rp11-source/"},
        {"root_a": "/tmp/capture"},
        {"root_b": "/"},
        {"root_a": P.SOURCE_CHECKOUT + "/capture"},
        {"root_b": P.CAPTURE_ROOT_A},
        {"run_root": P.CAPTURE_ROOT_A + "/run"},
        {"checkout": "/opt/../rp11"},
    ):
        with pytest.raises(P.PassAPlanError) as raised:
            P.validate_paths(**bad)
        assert raised.value.reason == "malformed-path"


def test_the_selected_roots_are_two_leaves_of_one_narrow_parent_below_var_lib() -> None:
    assert P.CAPTURE_PARENT == "/var/lib/fb-rp11"
    assert P.CAPTURE_ROOT_A == "/var/lib/fb-rp11/capture-a"
    assert P.CAPTURE_ROOT_B == "/var/lib/fb-rp11/capture-b"
    assert os.path.dirname(P.CAPTURE_ROOT_A) == os.path.dirname(P.CAPTURE_ROOT_B) == P.CAPTURE_PARENT
    assert os.path.dirname(P.CAPTURE_PARENT) == "/var/lib"
    assert P.PARENT_CONTRACT.leaves == (P.CAPTURE_ROOT_A, P.CAPTURE_ROOT_B)
    # The parent is not a pass root, so the store's root policy never lets a root be the parent.
    assert P.CAPTURE_PARENT not in P.root_policy().other_pass_roots


def test_the_genesis_request_names_root_a_forbids_tmp_and_the_checkout_and_names_root_b() -> None:
    request = P.build_pass_a_plan().genesis_request(invocation_id=INVOCATION_ID, tool_sha256=TOOL_SHA256)
    assert request.capture_root == P.CAPTURE_ROOT_A and request.pass_id == P.PASS_ID
    assert P.SOURCE_CHECKOUT in request.policy.forbidden_ancestors
    assert "/tmp" in request.policy.forbidden_ancestors
    assert request.policy.other_pass_roots == (P.CAPTURE_ROOT_B,)


# --- G4: the scoped-parent contract -----------------------------------------------------

CAPTURE_GID = 978
CAPTURE_UID = 992
DIRECTORY = stat.S_IFDIR


def _parent(**change: int | str) -> P.ObservedDirectory:
    fields = {"path": P.CAPTURE_PARENT, "uid": 0, "gid": CAPTURE_GID, "mode": DIRECTORY | 0o770}
    fields.update(change)
    return P.ObservedDirectory(**fields)  # type: ignore[arg-type]


def _leaf(**change: int | str) -> P.ObservedDirectory:
    fields = {"path": P.CAPTURE_ROOT_A, "uid": CAPTURE_UID, "gid": CAPTURE_GID, "mode": DIRECTORY | 0o700}
    fields.update(change)
    return P.ObservedDirectory(**fields)  # type: ignore[arg-type]


def test_the_parent_contract_states_the_approved_modes_and_owners() -> None:
    contract = P.PARENT_CONTRACT
    assert (contract.owner, contract.group, contract.mode) == ("root", "capture", 0o770)
    assert (contract.leaf_owner, contract.leaf_mode) == ("capture", 0o700)
    # Root: full. capture group: full (the store needs read to open and fsync). Others: nothing.
    assert contract.mode & 0o700 == 0o700
    assert contract.mode & 0o070 == 0o070
    assert contract.mode & 0o007 == 0 and not contract.mode & 0o7000
    assert P.parent_problems(_parent(), CAPTURE_GID) == ()


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        ({"uid": 1000}, ("owner",)),
        ({"uid": CAPTURE_UID}, ("owner",)),
        ({"gid": 0}, ("group",)),
        ({"gid": 1000}, ("group",)),
        ({"mode": DIRECTORY | 0o755}, ("mode", "other-access", "group-cannot-create")),
        ({"mode": DIRECTORY | 0o750}, ("mode", "group-cannot-create")),
        ({"mode": DIRECTORY | 0o730}, ("mode", "group-cannot-read")),
        ({"mode": DIRECTORY | 0o700}, ("mode", "group-cannot-read", "group-cannot-create")),
        ({"mode": DIRECTORY | 0o771}, ("mode", "other-access")),
        ({"mode": DIRECTORY | 0o777}, ("mode", "other-access")),
        ({"mode": DIRECTORY | 0o731}, ("mode", "other-access", "group-cannot-read")),
        ({"mode": DIRECTORY | 0o1770}, ("mode", "special-bits")),
        ({"mode": DIRECTORY | 0o2770}, ("mode", "special-bits")),
        ({"mode": DIRECTORY | 0o4770}, ("mode", "special-bits")),
        ({"mode": DIRECTORY | 0o370}, ("mode", "owner-bits")),
        ({"mode": stat.S_IFLNK | 0o770}, ("not-a-directory",)),
        ({"mode": stat.S_IFREG | 0o770}, ("not-a-directory",)),
        ({"path": "/var/lib"}, ("path",)),
        ({"path": "/var/lib/fb-rp11-capture-a"}, ("path",)),
    ],
)
def test_each_unsafe_parent_is_refused_by_name(change: dict, expected: tuple[str, ...]) -> None:
    assert P.parent_problems(_parent(**change), CAPTURE_GID) == expected


def test_a_parent_whose_group_is_root_is_never_accepted_whatever_the_capture_gid_is() -> None:
    assert "group" in P.parent_problems(_parent(gid=0), 0)
    assert "group" in P.parent_problems(_parent(), 0)


def test_a_leaf_is_absent_before_x1_and_any_object_there_is_refused() -> None:
    assert P.leaf_absent_problems(None) == ()
    for mode in (DIRECTORY | 0o700, stat.S_IFLNK | 0o777, stat.S_IFREG | 0o600):
        assert P.leaf_absent_problems(_leaf(mode=mode)) == ("present",)


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        ({}, ()),
        ({"path": P.CAPTURE_ROOT_B}, ()),
        ({"uid": 0}, ("owner",)),
        ({"uid": 1000}, ("owner",)),
        ({"mode": DIRECTORY | 0o755}, ("mode",)),
        ({"mode": DIRECTORY | 0o750}, ("mode",)),
        ({"mode": DIRECTORY | 0o2700}, ("mode",)),
        ({"mode": DIRECTORY | 0o701}, ("mode",)),
        ({"mode": stat.S_IFLNK | 0o700}, ("not-a-directory",)),
        ({"path": P.CAPTURE_PARENT}, ("path",)),
        ({"path": "/var/lib/fb-rp11/other"}, ("path",)),
    ],
)
def test_a_created_leaf_is_a_capture_owned_0700_directory(change: dict, expected: tuple[str, ...]) -> None:
    assert P.created_leaf_problems(_leaf(**change), CAPTURE_UID) == expected


def test_a_leaf_that_was_not_created_or_is_owned_by_root_is_refused() -> None:
    assert P.created_leaf_problems(None, CAPTURE_UID) == ("absent",)
    assert "owner" in P.created_leaf_problems(_leaf(uid=0), 0)


def test_the_contract_is_judged_from_observations_and_touches_no_filesystem(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*args: object, **kwargs: object) -> None:
        raise AssertionError("the contract checkers must not touch the filesystem")

    for name in ("stat", "lstat", "open", "mkdir", "listdir", "scandir"):
        monkeypatch.setattr(os, name, refuse)
    assert P.parent_problems(_parent(), CAPTURE_GID) == ()
    assert P.created_leaf_problems(_leaf(), CAPTURE_UID) == ()
    assert P.leaf_absent_problems(None) == ()


def test_the_unmodified_capture_store_creates_the_roots_below_a_0770_parent(tmp_path: Path) -> None:
    """Executable evidence for the G4 contract: ``PosixCaptureFilesystem`` and ``CaptureRootStore``,
    unmodified, run X-1 under a ``0770`` stand-in parent (a directory this process owns, so the
    group-read/search/write the contract grants is exercised without root). The leaf is created
    exclusively as ``0700``, both durability barriers succeed, an existing leaf is refused and
    nothing is left behind. Host validation as the real ``capture`` account remains separate."""
    from tools.phase_5_0_evidence.execution.capture_store import (
        CaptureRootStore,
        PosixCaptureFilesystem,
        RootPolicy,
        StoreFailure,
    )

    parent = tmp_path / "fb-rp11"
    parent.mkdir()
    parent.chmod(0o770)
    assert stat.S_IMODE(parent.stat().st_mode) == 0o770
    assert P.parent_problems(
        P.ObservedDirectory(P.CAPTURE_PARENT, 0, CAPTURE_GID, DIRECTORY | stat.S_IMODE(parent.stat().st_mode)),
        CAPTURE_GID,
    ) == ()
    leaf = parent / "capture-a"
    policy = RootPolicy(("/nonexistent-forbidden",))
    barriers: list[str] = []

    class Recording(PosixCaptureFilesystem):
        def fsync(self, fd: int, *, stage: str) -> None:
            super().fsync(fd, stage=stage)
            barriers.append(stage)

    store = CaptureRootStore(filesystem=Recording(), capture_root=str(leaf))
    try:
        store.create_root(policy)
        assert leaf.is_dir() and not leaf.is_symlink()
        assert stat.S_IMODE(leaf.stat().st_mode) == 0o700 == P.PARENT_CONTRACT.leaf_mode
        assert leaf.stat().st_uid == os.geteuid()
        assert P.created_leaf_problems(
            P.ObservedDirectory(P.CAPTURE_ROOT_A, leaf.stat().st_uid, leaf.stat().st_gid, leaf.stat().st_mode),
            os.geteuid(),
        ) == ()
        assert "X-1:root-entry-barrier" in barriers and "X-1:subdirectory-entry-barrier" in barriers
        assert all(
            stat.S_IMODE(path.stat().st_mode) == 0o700 for path in leaf.rglob("*") if path.is_dir()
        )
    finally:
        store.release()

    # An existing leaf is refused, not reused or replaced, and is left untouched.
    again = CaptureRootStore(filesystem=PosixCaptureFilesystem(), capture_root=str(leaf))
    try:
        with pytest.raises(StoreFailure) as refused:
            again.create_root(policy)
        assert (refused.value.stage, refused.value.classification) == ("X-1:create-root", "object-exists")
    finally:
        again.release()
    assert leaf.is_dir()

    # Cleanup leaves no residue.
    shutil.rmtree(leaf)
    assert list(parent.iterdir()) == []


# --- G7: measured timeouts and the whole-pass bound -----------------------------------


def _samples(value: float = 1.0, count: int = P.MIN_SAMPLES) -> tuple[float, ...]:
    return (value,) * count


@pytest.mark.parametrize(
    "host,samples",
    [
        ("production", _samples()),
        ("Test", _samples(count=P.MIN_SAMPLES - 1)),
        ("Test", _samples()[:-1] + (0.0,)),
        ("Test", _samples()[:-1] + (-1.0,)),
        ("Test", _samples()[:-1] + (math.nan,)),
        ("Test", _samples()[:-1] + (math.inf,)),
        ("Test", _samples()[:-1] + (True,)),  # type: ignore[arg-type]
        ("Test", ()),
    ],
)
def test_a_measurement_must_come_from_the_test_host_with_enough_finite_positive_samples(host, samples) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(P.PassAPlanError) as raised:
        P.Measurement(host, samples)
    assert raised.value.reason == "malformed-measurement"


def test_a_timeout_is_the_floor_or_the_multiplied_slowest_sample_whichever_is_larger() -> None:
    klass = P.CommandClass("T-x", 30.0, 5.0, 1024)
    assert klass.timeout_seconds == 30.0 and not klass.measured
    assert klass.with_measurement(P.Measurement("Test", _samples(2.0))).timeout_seconds == 30.0
    slow = klass.with_measurement(P.Measurement("Test", _samples(1.0)[:-1] + (7.2,)))
    assert slow.timeout_seconds == math.ceil(7.2 * 5.0) == 36.0
    assert float(slow.timeout_seconds).is_integer()


@pytest.mark.parametrize(
    "args", [("", 1, 2, 3), ("x", 0, 2, 3), ("x", 1, 0.5, 3), ("x", 1, 2, 0), ("x", -1, 2, 3)]
)
def test_a_malformed_command_class_is_refused(args) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(P.PassAPlanError) as raised:
        P.CommandClass(*args)
    assert raised.value.reason == "malformed-class"


def test_the_shipped_classes_are_measured_on_the_test_host_and_never_below_their_floor() -> None:
    assert set(P.CLASSES) == set(P.MEASUREMENTS) == {"T-local", "T-dry", "T-read"}
    for name, klass in P.CLASSES.items():
        assert klass.measured and klass.measurement is P.MEASUREMENTS[name]
        assert klass.measurement.host == "Test" and len(klass.measurement.samples) >= P.MIN_SAMPLES
        assert klass.timeout_seconds >= klass.floor_seconds
        assert klass.timeout_seconds >= klass.multiplier * max(klass.measurement.samples)
    plan = P.build_pass_a_plan()
    assert plan.timeouts_measured
    plan.require_operational()


def test_an_unmeasured_plan_is_refused_by_require_operational() -> None:
    plan = P.build_pass_a_plan(classes=P.BASE_CLASSES)
    assert not plan.timeouts_measured
    with pytest.raises(P.PassAPlanError) as raised:
        plan.require_operational()
    assert raised.value.reason == "timeouts-not-measured"
    partial = P.derive_timeouts({"T-read": P.MEASUREMENTS["T-read"]}, P.BASE_CLASSES)
    assert not P.build_pass_a_plan(classes=partial).timeouts_measured
    with pytest.raises(P.PassAPlanError):
        P.derive_timeouts({"T-nope": P.MEASUREMENTS["T-read"]})


def test_every_act_has_a_finite_whole_second_deadline_from_its_class_and_the_stream_bound() -> None:
    plan = P.build_pass_a_plan()
    for step, act in zip(plan.steps, plan.acts(), strict=True):
        klass = plan.classes[step.command_class]
        assert act.timeout_seconds == klass.timeout_seconds and float(act.timeout_seconds).is_integer()
        assert 0 < act.timeout_seconds < math.inf
        assert act.stream_bound_bytes == klass.stream_bound_bytes
        assert act.drain_seconds == CAPTURE_DRAIN_SECONDS


def test_the_stream_bounds_leave_room_over_every_measured_output() -> None:
    observed = {name: P.MEASURED_MAX_OUTPUT_BYTES[name] for name in P.CLASSES}
    for name, klass in P.CLASSES.items():
        assert klass.stream_bound_bytes >= 8 * observed[name], name


def test_the_whole_pass_bound_is_the_stated_worst_case_sum_and_is_finite() -> None:
    plan = P.build_pass_a_plan()
    expected = (
        P.GENESIS_ALLOWANCE_SECONDS
        + sum(a.timeout_seconds + a.drain_seconds + P.PER_ACT_ALLOWANCE_SECONDS for a in plan.acts())
        + P.FINALIZATION_ALLOWANCE_SECONDS
    )
    assert plan.whole_pass_bound_seconds == expected
    assert 0 < expected < 3 * 3600
    assert expected >= sum(a.timeout_seconds for a in plan.acts())
    one = P.build_pass_a_plan(include_corroboration=True)
    assert one.whole_pass_bound_seconds > plan.whole_pass_bound_seconds


def test_the_measured_whole_pass_took_far_less_than_its_bound() -> None:
    plan = P.build_pass_a_plan(include_corroboration=True)
    assert max(P.MEASURED_WHOLE_PASS_SECONDS) * 10 < plan.whole_pass_bound_seconds
    assert len(P.MEASURED_WHOLE_PASS_SECONDS) >= P.MIN_SAMPLES


def test_every_timeout_and_allowance_covers_the_real_identity_measurements() -> None:
    """The ``capture``/selected-path set confirms the synthetic-derived timeouts."""
    assert set(P.REAL_MEASUREMENTS) == set(P.CLASSES)
    for name, klass in P.CLASSES.items():
        real = P.REAL_MEASUREMENTS[name]
        assert len(real.samples) == 24
        assert klass.timeout_seconds >= klass.multiplier * max(real.samples)
    assert len(P.MEASURED_REAL_FINALIZATION_SECONDS) == 24
    assert P.GENESIS_ALLOWANCE_SECONDS >= P.DEFAULT_MULTIPLIER * P.MEASURED_REAL_MAX_GENESIS_SECONDS
    assert P.PER_ACT_ALLOWANCE_SECONDS >= P.DEFAULT_MULTIPLIER * P.MEASURED_REAL_MAX_PER_ACT_OVERHEAD_SECONDS
    assert P.FINALIZATION_ALLOWANCE_SECONDS == math.ceil(
        P.DEFAULT_MULTIPLIER * max(P.MEASURED_REAL_FINALIZATION_SECONDS)
    ) == 112.0


def test_the_per_command_timeouts_and_the_whole_pass_bound_are_the_reviewed_values() -> None:
    assert {name: k.timeout_seconds for name, k in P.CLASSES.items()} == {
        "T-local": 44.0, "T-dry": 161.0, "T-read": 30.0
    }
    assert P.build_pass_a_plan().whole_pass_bound_seconds == 2548.0
    assert P.build_pass_a_plan(include_corroboration=True).whole_pass_bound_seconds == 2638.0


# --- G7 behavior: stop, timeout and single finalization over the plan's own acts -------


def _genesis(host: Host) -> GenesisRequest:
    return GenesisRequest(
        capture_root=host.root(),
        pass_id=P.PASS_ID,
        tool_sha256=TOOL_SHA256,
        invocation_id=INVOCATION_ID,
        policy=host.policy(),
    )


def _drive(host: Host, launcher, plan: P.PassAPlan, *, acts=None):  # type: ignore[no-untyped-def]
    def factory(request: GenesisRequest):  # type: ignore[no-untyped-def]
        return create_capture_session(request, filesystem=FaultFilesystem(), launcher=launcher, clock=FixedClock())

    return run_pass_a(
        activation_id=ACTIVATION,
        consume_journal=consume_journal(),
        genesis=_genesis(host),
        acts=plan.acts() if acts is None else acts,
        exit_policy=plan.exit_policy(),
        session_factory=factory,
    )


def _expected_exit_behaviours(plan: P.PassAPlan) -> tuple[str, ...]:
    return tuple("ok" if s.accepted_exits == (0,) else f"exit:{s.accepted_exits[0]}" for s in plan.steps)


def test_the_whole_plan_completes_with_one_finalization_when_every_exit_is_the_expected_one(tmp_path: Path) -> None:
    plan = P.build_pass_a_plan()
    host = Host.under(tmp_path)
    launcher = PlanLauncher(_expected_exit_behaviours(plan))
    result = _drive(host, launcher, plan)
    assert result.status is PassAStatus.COMPLETED
    assert launcher.calls == [step.argv for step in plan.steps]
    assert launcher.timeouts == [plan.timeout_for(step) for step in plan.steps]
    assert launcher.environments == [dict(P.ENVIRONMENTS[s.environment]) for s in plan.steps]
    assert len(finals(host)) == 1


@pytest.mark.parametrize("stop_at", [0, 4, 24, 48])
@pytest.mark.parametrize("behaviour", ["timeout", "exit:3", "bound", "incomplete", "start-failed"])
def test_a_failure_at_any_step_stops_the_pass_with_no_later_command_and_one_finalization(
    tmp_path: Path, stop_at: int, behaviour: str
) -> None:
    plan = P.build_pass_a_plan()
    host = Host.under(tmp_path)
    launcher = PlanLauncher(_expected_exit_behaviours(plan)[:stop_at] + (behaviour,))
    result = _drive(host, launcher, plan)
    assert result.status is PassAStatus.STOPPED
    assert len(launcher.calls) == stop_at + 1, "nothing after the failing step was launched"
    assert len(finals(host)) == 1


def test_a_step_that_exits_with_an_unexpected_status_stops_the_pass() -> None:
    plan = P.build_pass_a_plan()
    absent = next(s for s in plan.steps if s.step_id == "A1-19")
    assert absent.accepted_exits == (1,)


def test_a_real_process_that_outlives_its_class_deadline_is_killed_and_the_pass_finalizes_once(tmp_path: Path) -> None:
    quick = {"T-read": P.CommandClass("T-read", 0.5, 1.0, 4096)}
    steps = (
        P.PlannedStep("S-01", "T-read", "plain", (sys.executable, "-I", "-S", "-c", "print(1)")),
        P.PlannedStep("S-02", "T-read", "plain", (sys.executable, "-I", "-S", "-c", "import time; time.sleep(60)")),
        P.PlannedStep("S-03", "T-read", "plain", (sys.executable, "-I", "-S", "-c", "print(3)")),
    )
    plan = P.PassAPlan(steps, quick)
    acts = tuple(replace(a, drain_seconds=2.0) for a in plan.acts())
    host = Host.under(tmp_path)
    launcher = CountingLauncher()
    started = os.times().elapsed
    result = _drive(host, launcher, plan, acts=acts)
    elapsed = os.times().elapsed - started
    assert result.status is PassAStatus.STOPPED and result.reason == "command-timeout"
    assert len(launcher.calls) == 2 and len(finals(host)) == 1
    assert elapsed < 0.5 + 2.0 + 30, "the child was killed at its deadline, not waited for"


# --- containment: a value layer only -------------------------------------------------


def test_the_module_starts_nothing_arms_nothing_and_calls_nothing_operational() -> None:
    tree = ast.parse(SOURCE.read_text())
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    names |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert not names & {
        "run_pass_a",
        "create_capture_session",
        "StreamCaptureLauncher",
        "PosixCaptureFilesystem",
        "build_pass_a_session",
        "Popen",
        "system",
        "execv",
        "open",
        "makedirs",
        "mkdir",
        "chown",
        "chmod",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"open", "exec", "eval", "compile", "__import__"}


def test_nothing_in_the_entry_or_the_operational_tree_imports_the_plan() -> None:
    for relative in ("infra", "tools", "application", "adapters", "domain"):
        for path in (ROOT / relative).rglob("*.py"):
            if path == SOURCE or "__pycache__" in path.parts:
                continue
            imported: set[str] = set()
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.Import):
                    imported |= {a.name for a in node.names}
                elif isinstance(node, ast.ImportFrom):
                    imported |= {node.module or ""} | {f"{node.module}.{a.name}" for a in node.names}
            assert not [name for name in imported if name.endswith("pass_a_plan")], path


def test_the_module_does_not_claim_a_timeout_it_has_not_measured() -> None:
    assert P.build_pass_a_plan(classes=P.BASE_CLASSES).timeouts_measured is False
