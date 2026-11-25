"""RP-11 Pass A policy data: the finite local-only plan, its environments, timeouts and identity.

``pass_a`` is policy-neutral on purpose. This module is the policy it is handed:

* **One host.** Every command runs locally on ``oracle-test`` as a child of the capture
  mechanism, with a fixed absolute ``argv[0]``, no shell, no ``ssh``, no ``rsync``, no
  ``sudo`` (the accepted single-host topology, entry-contract proposal §0b). The
  withdrawn two-host commands are not carried over: each is either re-derived below or
  listed in ``WITHDRAWN_STEPS`` with its reason, so none disappears silently.
* **A complete, non-inherited child environment (G3).** ``ENVIRONMENTS`` names every
  variable a child receives; nothing comes from the launcher, the unit or the operator.
  ``HOME``, ``INVOCATION_ID``, ``TEST_DATABASE_URL`` and every credential-shaped name are
  absent by construction, not by filtering.
* **Guard-visible argv (G2).** Source acquisition is a separate, maintainer-controlled
  pre-pass action and is not in this plan. Every argv here is an ordinary command line
  that the repository secrets guard admits unchanged, so launching it through the
  mechanism is not a way around that guard (a test renders each one and asks the guard).
* **Fixed per-command timeouts and a derived whole-pass bound (G7).** Three command
  classes, each with a floor and a multiplier. A class's timeout is ``max(floor,
  ceil(multiplier x slowest of >= 10 samples taken on oracle-test))``. The samples in
  ``MEASUREMENTS`` were taken on ``oracle-test`` (host name ``Test``), idle and under
  CPU saturation, by running this plan's own argv, environments and exit policy through
  the real mechanism against a *scratch* clone and a *scratch* capture root (synthetic:
  neither selected path exists there, and the commands ran as ``ubuntu``). T-read lands on
  its floor; T-local (8.70 s loaded worst case) and T-dry (32.08 s) are above
  theirs, so the multiplier decides for those two classes. ``whole_pass_bound_seconds`` is the finite worst case: every act runs to
  its deadline, drains fully and pays its allowance. ``require_operational`` still
  refuses a plan whose used classes are unmeasured.
* **A scoped parent for the capture roots (G4).** The roots are ``/var/lib/fb-rp11/capture-a``
  and ``-b``. ``PARENT_CONTRACT`` states the pre-provisioned parent (``root:capture``, ``0770``:
  root and the ``capture`` group have full access; others nothing)
  and the leaf rule (absent before X-1, then created ``0700`` by the non-root ``capture``).
  ``parent_problems`` / ``leaf_absent_problems`` / ``created_leaf_problems`` judge *observed*
  directories against it and touch no filesystem. ``/var/lib`` is never widened. ``0770`` replaces
  the earlier ``0730`` because the unmodified ``CaptureRootStore`` opens every ancestor
  ``O_RDONLY`` and fsyncs the parent entry, which needs group read; the directory is purpose-built
  and ``capture`` is its only group member. Host validation remains outstanding.
* **The capture identity as data.** ``CAPTURE_IDENTITY`` states the accepted ``capture``
  account policy and ``identity_problems`` judges an *observed* account against it. Nothing
  here creates, modifies or looks up an account.

Nothing in this module starts a process, opens a file, arms a launcher, builds a session
or calls ``run_pass_a``. The entry does not import it: it is a value layer that a later,
separately authorized wiring step consumes. It lives beside ``pass_a`` in the execution
tier and its bytes are covered by the review manifest (version 37), so changing a command, an environment or a measurement moves the
reviewed digest and every pin derived from it.
"""

from __future__ import annotations

import math
import os
import re
import stat
from dataclasses import dataclass, field
from typing import Callable, Mapping

from ..capture_contract import IDENTIFIER, ExitOutcome
from ..errors import HarnessError
from .boundary import CAPTURE_DRAIN_SECONDS
from .capture_mechanism import ActRequest, GenesisRequest
from .capture_store import RootPolicy

# --- identity of the pass, the paths and the accepted account -------------------------

PASS_ID = "C-P5.0-R5-OP1-A"

#: Accepted 2026-11-24 for the disposable feasibility exercise only. Nothing creates them.
#: The capture roots are scoped under one narrow, pre-provisioned parent (G4 redesign,
#: maintainer-approved 2026-11-24 after direct ``/var/lib`` leaves failed exclusive creation
#: by the non-root ``capture`` account). The parent is ``PARENT_CONTRACT``; the leaves are
#: created by ``capture`` itself at X-1 and are absent before it.
SOURCE_CHECKOUT = "/opt/freedom-blades/rp11-source"
CAPTURE_PARENT = "/var/lib/fb-rp11"
CAPTURE_ROOT_A = f"{CAPTURE_PARENT}/capture-a"
CAPTURE_ROOT_B = f"{CAPTURE_PARENT}/capture-b"
EVIDENCE_RUN_ROOT = "/var/lib/fb-evidence-p5-0"

INTERPRETER = "/opt/freedom-blades/runtime/venv-web/bin/python"
DRY_RUN_MODULE = "tools.phase_5_0_evidence.execution.cli"


class PassAPlanError(HarnessError):
    """The plan data is inconsistent or not yet fit to run. ``reason`` is a fixed code."""

    REASONS = frozenset(
        {
            "malformed-path",
            "malformed-class",
            "malformed-step",
            "malformed-measurement",
            "timeouts-not-measured",
        }
    )

    def __init__(self, reason: str) -> None:
        if reason not in self.REASONS:
            raise ValueError("unknown plan error")
        self.reason = reason
        super().__init__(reason)


@dataclass(frozen=True, slots=True)
class ServiceIdentity:
    """The accepted policy for the capture service account (G5). Data, not an action."""

    name: str
    system_account: bool
    locked: bool
    login_shells: tuple[str, ...]
    may_be_root: bool
    may_have_sudo: bool
    may_have_supplementary_groups: bool
    forbidden_names: tuple[str, ...]


CAPTURE_IDENTITY = ServiceIdentity(
    name="capture",
    system_account=True,
    locked=True,
    login_shells=("/usr/sbin/nologin", "/bin/false", "/usr/bin/false"),
    may_be_root=False,
    may_have_sudo=False,
    may_have_supplementary_groups=False,
    forbidden_names=("root", "ubuntu", "freedom-executor"),
)


@dataclass(frozen=True, slots=True)
class ObservedAccount:
    """What a later, authorized step observed about an account; this module observes nothing."""

    name: str
    uid: int
    primary_gid: int
    shell: str
    locked: bool
    supplementary_groups: tuple[str, ...]
    sudo_rights: bool
    system_uid_max: int = 999


def identity_problems(
    observed: ObservedAccount, policy: ServiceIdentity = CAPTURE_IDENTITY
) -> tuple[str, ...]:
    """Every way ``observed`` departs from ``policy``; empty means it conforms."""
    problems: list[str] = []
    if observed.name != policy.name or observed.name in policy.forbidden_names:
        problems.append("name")
    if observed.uid == 0 or observed.primary_gid == 0:
        problems.append("root")
    if policy.system_account and not 0 < observed.uid <= observed.system_uid_max:
        problems.append("not-a-system-account")
    if policy.locked and not observed.locked:
        problems.append("not-locked")
    if observed.shell not in policy.login_shells:
        problems.append("login-shell")
    if observed.sudo_rights and not policy.may_have_sudo:
        problems.append("sudo")
    if observed.supplementary_groups and not policy.may_have_supplementary_groups:
        problems.append("supplementary-groups")
    return tuple(problems)


# --- paths ----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ParentContract:
    """The G4 parent/leaf filesystem contract, as data (nothing here touches a filesystem).

    The parent is provisioned *before* the pass by the host owner, as ``root:capture`` mode
    ``0770``: root and the ``capture`` group have full access (read, write, search), which the
    capture store needs to open and fsync the parent; others have nothing. Each
    leaf is absent until X-1, where the non-root ``capture`` account creates it exclusively
    with mode ``0700``, so a leaf is owned by ``capture`` and no one else can open it.
    ``/var/lib`` itself is never widened.
    """

    path: str
    owner: str
    group: str
    mode: int
    leaf_owner: str
    leaf_mode: int
    leaves: tuple[str, ...]


PARENT_CONTRACT = ParentContract(
    path=CAPTURE_PARENT,
    owner="root",
    group="capture",
    mode=0o770,
    leaf_owner="capture",
    leaf_mode=0o700,
    leaves=(CAPTURE_ROOT_A, CAPTURE_ROOT_B),
)


@dataclass(frozen=True, slots=True)
class ObservedDirectory:
    """What a later, authorized step observed with ``lstat`` about one path.

    ``mode`` is the complete ``st_mode`` so that a symbolic link, a file or a setgid bit is
    seen, not masked away. This module observes nothing."""

    path: str
    uid: int
    gid: int
    mode: int


def parent_problems(
    observed: ObservedDirectory, capture_gid: int, policy: ParentContract = PARENT_CONTRACT
) -> tuple[str, ...]:
    """Every way the parent departs from the contract; empty means it conforms.

    ``capture_gid`` is the observed primary group id of the ``capture`` account (never 0)."""
    problems: list[str] = []
    if observed.path != policy.path:
        problems.append("path")
    if not stat.S_ISDIR(observed.mode):
        problems.append("not-a-directory")  # includes a symbolic link, seen by lstat
    if observed.uid != 0:
        problems.append("owner")
    if capture_gid == 0 or observed.gid != capture_gid:
        problems.append("group")
    permission = stat.S_IMODE(observed.mode)
    if permission != policy.mode:
        problems.append("mode")
        if permission & 0o007:
            problems.append("other-access")
        if not permission & 0o040:
            problems.append("group-cannot-read")
        if permission & 0o030 != 0o030:
            problems.append("group-cannot-create")
        if permission & 0o7000:
            problems.append("special-bits")
        if permission & 0o700 != 0o700:
            problems.append("owner-bits")
    return tuple(problems)


def leaf_absent_problems(observed: ObservedDirectory | None) -> tuple[str, ...]:
    """Before X-1 a leaf must not exist at all (not even as a link): ``None`` conforms."""
    return () if observed is None else ("present",)


def created_leaf_problems(
    observed: ObservedDirectory | None, capture_uid: int, policy: ParentContract = PARENT_CONTRACT
) -> tuple[str, ...]:
    """After X-1 a leaf is a real directory owned by ``capture`` with exactly ``0700``."""
    if observed is None:
        return ("absent",)
    problems: list[str] = []
    if observed.path not in policy.leaves:
        problems.append("path")
    if not stat.S_ISDIR(observed.mode):
        problems.append("not-a-directory")
    if capture_uid == 0 or observed.uid != capture_uid:
        problems.append("owner")
    if stat.S_IMODE(observed.mode) != policy.leaf_mode:
        problems.append("mode")
    return tuple(problems)


def _is_under(path: str, ancestor: str) -> bool:
    return path == ancestor or path.startswith(ancestor.rstrip("/") + "/")


def validate_paths(
    checkout: str = SOURCE_CHECKOUT,
    root_a: str = CAPTURE_ROOT_A,
    root_b: str = CAPTURE_ROOT_B,
    run_root: str = EVIDENCE_RUN_ROOT,
    parent: str = CAPTURE_PARENT,
) -> None:
    """Absolute, normalized, outside ``/tmp``; no path inside or equal to another, except that
    each capture root is a direct child of the one capture ``parent``, which is itself a single
    component directly below ``/var/lib`` and overlaps neither the checkout nor the run root."""
    paths = (checkout, root_a, root_b, run_root)
    for path in (parent, *paths):
        if (
            not isinstance(path, str)
            or not path.startswith("/")
            or os.path.normpath(path) != path
            or path == "/"
            or _is_under(path, "/tmp")
        ):
            raise PassAPlanError("malformed-path")
    if os.path.dirname(parent) != "/var/lib":
        raise PassAPlanError("malformed-path")
    for root in (root_a, root_b):
        if os.path.dirname(root) != parent:
            raise PassAPlanError("malformed-path")
    for other in (checkout, run_root):
        if _is_under(parent, other) or _is_under(other, parent):
            raise PassAPlanError("malformed-path")
    for path in paths:
        if (
            not isinstance(path, str)
            or not path.startswith("/")
            or os.path.normpath(path) != path
            or path == "/"
            or _is_under(path, "/tmp")
        ):
            raise PassAPlanError("malformed-path")
    for i, left in enumerate(paths):
        for j, right in enumerate(paths):
            # By position, not identity: two equal strings are one path named twice.
            if i != j and _is_under(left, right):
                raise PassAPlanError("malformed-path")


def root_policy(other_pass_roots: tuple[str, ...] = (CAPTURE_ROOT_B,)) -> RootPolicy:
    """The root policy of Pass A: ``/tmp`` and the source checkout are forbidden ancestors."""
    return RootPolicy.for_repository(SOURCE_CHECKOUT, other_pass_roots)


# --- child environments (G3) ----------------------------------------------------------

_BASE_ENVIRONMENT = {"PATH": "/usr/bin", "LC_ALL": "C", "LANG": "C"}

#: The complete environment of each kind of child. A child gets exactly one mapping.
ENVIRONMENTS: Mapping[str, Mapping[str, str]] = {
    "plain": dict(_BASE_ENVIRONMENT),
    # The checkout is owned by someone other than ``capture``, so git's ownership check
    # needs ``safe.directory``; it is supplied through the command-scope configuration
    # block and every other configuration source is switched off. No repository lock is
    # taken (the checkout is read-only to ``capture``).
    "git": {
        **_BASE_ENVIRONMENT,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "safe.directory",
        "GIT_CONFIG_VALUE_0": SOURCE_CHECKOUT,
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
    },
    "python": {
        **_BASE_ENVIRONMENT,
        "PYTHONPATH": SOURCE_CHECKOUT,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
    },
    "systemd": {**_BASE_ENVIRONMENT, "SYSTEMD_COLORS": "0"},
}

#: Names that must never reach a child, whatever else changes.
FORBIDDEN_ENVIRONMENT_NAMES = frozenset(
    {"HOME", "INVOCATION_ID", "TEST_DATABASE_URL", "SSH_AUTH_SOCK", "LD_PRELOAD", "LD_LIBRARY_PATH"}
)
_CREDENTIAL_SHAPE = re.compile(r"(TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL|DATABASE_URL|PRIVATE_KEY)", re.IGNORECASE)
REQUIRED_ENVIRONMENT_NAMES = frozenset({"PATH", "LC_ALL", "LANG"})


def environment_problems(environment: Mapping[str, str]) -> tuple[str, ...]:
    """Every forbidden or credential-shaped name in ``environment``, then ``path`` if the
    search path is not the single fixed directory; ``("incomplete",)`` if a base name is missing."""
    if not REQUIRED_ENVIRONMENT_NAMES <= set(environment):
        return ("incomplete",)
    problems = [
        name
        for name in sorted(environment)
        if name in FORBIDDEN_ENVIRONMENT_NAMES or _CREDENTIAL_SHAPE.search(name)
    ]
    if environment["PATH"] != "/usr/bin":
        problems.append("path")
    return tuple(problems)


# --- command classes, measured timeouts, whole-pass bound (G7) -------------------------

MIN_SAMPLES = 10
DEFAULT_MULTIPLIER = 5.0
#: Mechanism work around each act, not part of any child's deadline: stream and record
#: publication with their barriers (per act), and the genesis and finalization sequences.
#: Conservative allowances, not measurements of this host.
GENESIS_ALLOWANCE_SECONDS = 30.0
PER_ACT_ALLOWANCE_SECONDS = 10.0
FINALIZATION_ALLOWANCE_SECONDS = 30.0


@dataclass(frozen=True, slots=True)
class Measurement:
    """Wall-clock samples of one class's real commands, taken on ``oracle-test``."""

    host: str
    samples: tuple[float, ...]

    def __post_init__(self) -> None:
        if (
            self.host != "Test"
            or len(self.samples) < MIN_SAMPLES
            or not all(
                isinstance(s, (int, float)) and not isinstance(s, bool) and math.isfinite(s) and s > 0
                for s in self.samples
            )
        ):
            raise PassAPlanError("malformed-measurement")


@dataclass(frozen=True, slots=True)
class CommandClass:
    name: str
    floor_seconds: float
    multiplier: float
    stream_bound_bytes: int
    measurement: Measurement | None = None

    def __post_init__(self) -> None:
        if not (
            self.name
            and self.floor_seconds > 0
            and self.multiplier >= 1
            and 0 < self.stream_bound_bytes
        ):
            raise PassAPlanError("malformed-class")

    @property
    def measured(self) -> bool:
        return self.measurement is not None

    @property
    def timeout_seconds(self) -> float:
        """Fixed per-command deadline: never below the floor, never below
        ``multiplier`` times the slowest sample. Whole seconds."""
        if self.measurement is None:
            return float(self.floor_seconds)
        return float(max(self.floor_seconds, math.ceil(max(self.measurement.samples) * self.multiplier)))

    def with_measurement(self, measurement: Measurement) -> "CommandClass":
        return CommandClass(
            self.name, self.floor_seconds, self.multiplier, self.stream_bound_bytes, measurement
        )


#: Floors are the candidate numbers of the entry-contract proposal §4 for the classes that
#: survive the single-host redesign (T-test and T-sync are gone with their commands).
BASE_CLASSES: Mapping[str, CommandClass] = {
    "T-local": CommandClass("T-local", 30.0, DEFAULT_MULTIPLIER, 64 * 1024),
    "T-dry": CommandClass("T-dry", 120.0, DEFAULT_MULTIPLIER, 512 * 1024),
    "T-read": CommandClass("T-read", 30.0, DEFAULT_MULTIPLIER, 256 * 1024),
}

#: Measured 2026-11-24 on ``oracle-test`` (host name ``Test``, 2 CPUs) by
#: ``tests/test_rp11_pass_a_measure.py``, on this plan as pinned (final bytes of every step):
#: 12 whole runs "idle" (1-minute load average 1.2-3.8 around the runs; the host is shared and
#: another session was working on it, so this is *not* a quiet host), then 12 whole runs under
#: deliberate CPU saturation (three busy loops on two CPUs; load average 6.8-9.6). One sample is
#: the slowest step of the class in one run, rounded up to 0.1 ms. Every run used the plan's
#: own exit policy (``plan.exit_policy()``), so a status the plan does not list, or a signal,
#: would have stopped the pass; each recorded outcome was then asserted against that policy
#: again. Synthetic: a scratch clone and a scratch capture root stood in for the two selected
#: paths, and the commands ran as ``ubuntu``, not ``capture`` (the account was not created),
#: so permission-dependent timing is unmeasured. All 51 steps of all 24 runs ended with the
#: exit status the plan expects; none timed out, exceeded its bound or left a stream
#: incomplete. Slowest sample per class: T-local 8.6966 s, T-dry 32.0789 s, T-read
#: 2.7107 s; slowest whole run 64.7008 s. An earlier 24-run set (slowest 7.1261 / 18.7189 /
#: 4.5872 s) was taken before one stat operand of A1-16 was removed and on a less contended
#: host; it is superseded, not merged. The timeouts are therefore T-local 44 s and T-dry
#: 161 s (both above their floors) and T-read 30 s (its floor).
MEASUREMENTS: Mapping[str, Measurement] = {
    "T-local": Measurement(
        "Test",
        (
        0.5712, 1.4123, 1.3908, 0.5763, 1.203, 0.4774, 0.7731, 0.5906,
        0.4141, 0.5933, 0.6007, 0.5996, 2.6197, 8.6966, 3.8956, 1.2006,
        4.0851, 4.6193, 2.2243, 3.2997, 3.7165, 3.698, 0.6928, 0.4828,
        ),
    ),
    "T-dry": Measurement(
        "Test",
        (
        4.3975, 4.5048, 6.5988, 3.1928, 6.3869, 7.1101, 4.9825, 4.8949,
        4.2072, 4.5817, 4.5069, 4.2008, 16.1927, 14.9018, 12.8011, 14.5772,
        16.1938, 14.9788, 32.0789, 15.1791, 15.2854, 14.2079, 4.5987, 4.9019,
        ),
    ),
    "T-read": Measurement(
        "Test",
        (
        1.1873, 0.3324, 0.3042, 0.5923, 0.4835, 0.4964, 0.4861, 0.4642,
        0.4123, 0.4988, 0.4063, 0.4758, 2.02, 1.9266, 1.6148, 1.7808,
        1.9103, 1.6985, 2.7107, 1.5821, 1.2982, 0.887, 0.5203, 0.4109,
        ),
    ),
}
#: Largest single-channel output of any measured step, per class (bytes).
MEASURED_MAX_OUTPUT_BYTES: Mapping[str, int] = {'T-local': 645, 'T-dry': 1456, 'T-read': 5026}
#: Wall-clock seconds of each of the 24 whole runs, mechanism included (51 steps).
MEASURED_WHOLE_PASS_SECONDS: tuple[float, ...] = (
        15.3766, 13.112, 15.3307, 12.8934, 15.9907, 14.684, 13.1153, 12.8016,
        12.0882, 13.2004, 12.6062, 12.3818, 51.5991, 54.1967, 44.2012, 49.501,
        48.6019, 49.6969, 64.7008, 50.4007, 48.6058, 28.8878, 12.9261, 12.9147,
)

# --- the finite plan ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PlannedStep:
    step_id: str
    command_class: str
    environment: str
    argv: tuple[str, ...]
    #: Exit statuses that let the pass continue. Everything else, including a signal,
    #: stops it.
    accepted_exits: tuple[int, ...] = (0,)
    #: Which authorization row of the old draft covers the step (a label, not a grant).
    auth_row: str = "AUTH-READ"

    def __post_init__(self) -> None:
        if not (
            IDENTIFIER.match(self.step_id)
            and self.command_class in BASE_CLASSES
            and self.environment in ENVIRONMENTS
            and self.argv
            and all(isinstance(a, str) and "\0" not in a for a in self.argv)
            and self.argv[0].startswith("/")
            and self.accepted_exits
            and all(isinstance(c, int) and 0 <= c <= 255 for c in self.accepted_exits)
        ):
            raise PassAPlanError("malformed-step")


def _s(step_id: str, klass: str, env: str, *argv: str, exits: tuple[int, ...] = (0,), auth: str = "AUTH-READ") -> PlannedStep:
    return PlannedStep(step_id, klass, env, tuple(argv), exits, auth)


def _git(*args: str) -> tuple[str, ...]:
    return ("/usr/bin/git", "-C", SOURCE_CHECKOUT, *args)


_PROMPT = f"{SOURCE_CHECKOUT}/docs/review/phase-5-0-p5-r5-operational-evidence-authorization-prompt.md"
_MANIFEST = f"{SOURCE_CHECKOUT}/docs/review/phase-5-0-evidence-harness-review-manifest.json"
_CONCRETE_PLAN = f"{SOURCE_CHECKOUT}/docs/review/phase-5-0-evidence-harness-concrete-plan.md"
_PINNED_SOURCES = tuple(
    f"{SOURCE_CHECKOUT}/tools/phase_5_0_evidence/{name}"
    for name in (
        "journal.py",
        "unit_sandbox.py",
        "execution/case_program.py",
        "execution/cli.py",
        "reservation.py",
    )
)
_ABSENT_GROUPS_AND_USERS = (
    ("group", "freedomjournal"),
    ("group", "freedomcoord"),
    ("group", "freedomsheet"),
    ("group", "fbprobe"),
    ("passwd", "freedomcoord"),
    ("passwd", "freedomsheet"),
    ("passwd", "fbprobe"),
)
_SURVEYED_PATHS = (
    "/etc/tmpfiles.d/freedom-blades-laboratory.conf",
    "/var/lib/freedom-blades",
    "/var/lib/freedom-blades/laboratory",
    "/var/lib/freedom-blades/recovery",
)


def _lab_survey(prefix: str, *, group_check: bool) -> list[PlannedStep]:
    """A1-19, (A1-20,) A1-21, A1-23, A1-24: the laboratory reads that A1-Z repeats."""
    steps = [_s(f"{prefix}19", "T-read", "plain", "/usr/bin/stat", "--format=%F", EVIDENCE_RUN_ROOT, exits=(1,))]
    if group_check:
        steps.append(_s(f"{prefix}20", "T-read", "plain", "/usr/bin/getent", "group", "freedomlab"))
    steps.append(_s(f"{prefix}21", "T-read", "plain", "/usr/bin/stat", "--format=%n %U:%G %a %F", *_SURVEYED_PATHS))
    for number, (database, name) in enumerate(_ABSENT_GROUPS_AND_USERS):
        steps.append(
            _s(f"{prefix}23{'abcdefg'[number]}", "T-read", "plain", "/usr/bin/getent", database, name, exits=(2,))
        )
    steps.append(
        _s(f"{prefix}24", "T-read", "systemd", "/usr/bin/systemctl", "--no-pager", "show",
           "--property=LoadState", "fb-evidence-s4.service")
    )
    return steps


def _db_survey(prefix: str) -> list[PlannedStep]:
    """A1-29 and A1-30: host-level cluster status only (the psql reads are withdrawn)."""
    return [
        _s(f"{prefix}29", "T-read", "systemd", "/usr/bin/systemctl", "is-active", "postgresql@18-main", auth="AUTH-DBREAD"),
        _s(f"{prefix}30", "T-read", "plain", "/usr/bin/pg_lsclusters", "--no-header", auth="AUTH-DBREAD"),
    ]


def _a0_and_identity_steps() -> list[PlannedStep]:
    steps = [
        _s("A0-02a", "T-local", "git", *_git("rev-parse", "HEAD")),
        _s("A0-02b", "T-local", "git", *_git("status", "--porcelain=v1")),
        _s("A0-03", "T-local", "plain", "/usr/bin/sha256sum", _PROMPT),
        _s("A0-04", "T-local", "plain", "/usr/bin/sha256sum", _MANIFEST, _CONCRETE_PLAN),
        _s("A0-05", "T-dry", "python", INTERPRETER, "-B", "-P", "-m", DRY_RUN_MODULE),
        _s("A1-S2", "T-local", "plain", "/usr/bin/sha256sum", *_PINNED_SOURCES),
        _s("A1-01", "T-read", "plain", "/usr/bin/uname", "-n"),
        _s("A1-02", "T-read", "plain", "/usr/bin/uname", "-r"),
        _s("A1-03", "T-read", "plain", "/usr/bin/uname", "-m"),
        _s("A1-04", "T-read", "plain", "/usr/bin/grep", "-E", "^PRETTY_NAME=", "/etc/os-release"),
        _s("A1-05", "T-read", "plain", "/usr/bin/cat", "/proc/sys/kernel/random/boot_id"),
        _s("A1-06", "T-read", "plain", "/usr/bin/sha256sum", "/etc/machine-id"),
        _s("A1-07", "T-read", "plain", "/usr/bin/findmnt", "--target", "/var/lib", "--noheadings", "--output", "SOURCE,FSTYPE,OPTIONS"),
        _s("A1-08", "T-read", "plain", "/usr/sbin/sysctl", "fs.protected_hardlinks"),
        _s("A1-09", "T-read", "plain", "/usr/bin/df", "--output=avail", "-B1", "/var/lib"),
        _s("A1-10", "T-read", "systemd", "/usr/bin/timedatectl", "--no-pager", "show",
           "--property=NTPSynchronized", "--property=Timezone"),
        _s("A1-13", "T-read", "plain", INTERPRETER, "-I", "-S", "-c",
           "import sys; print(sys.version_info[:3], sys.flags.isolated, sys.flags.no_site)"),
        _s("A1-16", "T-read", "plain", "/usr/bin/stat", "--format=%n %U:%G %a",
           "/usr/sbin/capsh", "/usr/bin/lsattr", "/usr/bin/systemd-run", "/usr/bin/setpriv"),
        _s("A1-17", "T-read", "plain", "/usr/bin/dpkg-query", "--show", "--showformat=${Package} ${Version}\\n",
           "libcap2-bin", "e2fsprogs", "systemd", "util-linux"),
        _s("A1-18", "T-read", "systemd", "/usr/bin/systemctl", "--version"),
    ]
    steps.extend(_lab_survey("A1-", group_check=True))
    return steps


def _a1_tail_steps() -> list[PlannedStep]:
    return [
        _s("A1-25", "T-read", "plain", "/usr/bin/ps", "-eo", "uid=,user=,comm=", "--sort=uid"),
        _s("A1-26", "T-read", "systemd", "/usr/bin/systemctl", "--no-pager", "list-units", "--type=service",
           "--state=running", "--no-legend", "--plain"),
        _s("A1-27", "T-read", "systemd", "/usr/bin/systemctl", "--no-pager", "list-timers", "--all", "--no-legend"),
        _s("A1-28", "T-read", "systemd", "/usr/bin/loginctl", "--no-pager", "list-sessions", "--no-legend"),
    ]


#: Run only with the digest-pinned, independently verified target-fact statement (RP-10),
#: which does not exist; excluded from the default plan.
CORROBORATIVE_STEPS: tuple[PlannedStep, ...] = (
    _s("A1-11", "T-read", "plain", "/usr/bin/readlink", "-f", INTERPRETER),
    # ``sha256sum`` follows the symlink, so this is the digest of the file A1-11 names;
    # no operator substitution of A1-11's output into a later argv exists.
    _s("A1-12", "T-read", "plain", "/usr/bin/sha256sum", INTERPRETER),
)

#: Steps of the old draft with no local, unprivileged analogue under the accepted
#: ``capture`` identity (non-root, no sudo, no supplementary groups). Withdrawn, not
#: dropped: each needs its own owner decision before it can return in any form.
WITHDRAWN_STEPS: Mapping[str, str] = {
    "A1-00": "the production-origin rsync; source acquisition is a separate pre-pass action",
    "A1-S1": "identical to A0-05 now that the checkout is the only tree",
    "A0-06": "pytest needs a writable temporary path the capture identity does not have; the classifier tests belong to the pinned tree's own suites",
    "A1-14": "reads a sudo-launched process; the capture identity has no sudo",
    "A1-15": "runs capsh under sudo; the capture identity has no sudo",
    "A1-22": "lifecycle.json sits under a 0750 root:freedomlab directory; absence cannot be told from denial",
    "A1-31": "psql as postgres needs sudo",
    "A1-32": "psql as postgres needs sudo",
    "A1-33": "pg_hba/pg_ident are root-only and need sudo",
}


@dataclass(frozen=True)
class PassAPlan:
    steps: tuple[PlannedStep, ...]
    classes: Mapping[str, CommandClass] = field(default_factory=lambda: dict(CLASSES))

    def __post_init__(self) -> None:
        ids = [step.step_id for step in self.steps]
        if not self.steps or len(set(ids)) != len(ids):
            raise PassAPlanError("malformed-step")
        if not {s.command_class for s in self.steps} <= set(self.classes):
            raise PassAPlanError("malformed-class")

    @property
    def timeouts_measured(self) -> bool:
        used = {step.command_class for step in self.steps}
        return all(self.classes[name].measured for name in used)

    def require_operational(self) -> None:
        """Refuse until every used class has a measurement taken on ``oracle-test``."""
        if not self.timeouts_measured:
            raise PassAPlanError("timeouts-not-measured")

    def timeout_for(self, step: PlannedStep) -> float:
        return self.classes[step.command_class].timeout_seconds

    def acts(self) -> tuple[ActRequest, ...]:
        return tuple(
            ActRequest(
                step_or_case_id=step.step_id,
                argv=step.argv,
                environment=dict(ENVIRONMENTS[step.environment]),
                stream_bound_bytes=self.classes[step.command_class].stream_bound_bytes,
                timeout_seconds=self.timeout_for(step),
                drain_seconds=CAPTURE_DRAIN_SECONDS,
            )
            for step in self.steps
        )

    @property
    def whole_pass_bound_seconds(self) -> float:
        """Worst case: every act runs to its deadline, drains fully and pays its allowance."""
        per_act = sum(
            self.timeout_for(step) + CAPTURE_DRAIN_SECONDS + PER_ACT_ALLOWANCE_SECONDS for step in self.steps
        )
        return GENESIS_ALLOWANCE_SECONDS + per_act + FINALIZATION_ALLOWANCE_SECONDS

    def exit_policy(self) -> Callable[[ActRequest, ExitOutcome], bool]:
        """Accept exactly the statuses the plan lists for the act; a signal never passes."""
        accepted = {step.step_id: frozenset(step.accepted_exits) for step in self.steps}

        def policy(request: ActRequest, outcome: ExitOutcome) -> bool:
            allowed = accepted.get(request.step_or_case_id)
            return allowed is not None and outcome.kind == "status" and outcome.value in allowed

        return policy

    def genesis_request(self, *, invocation_id: str, tool_sha256: str) -> GenesisRequest:
        validate_paths()
        return GenesisRequest(
            capture_root=CAPTURE_ROOT_A,
            pass_id=PASS_ID,
            tool_sha256=tool_sha256,
            invocation_id=invocation_id,
            policy=root_policy(),
        )


def build_pass_a_plan(
    *,
    include_corroboration: bool = False,
    classes: Mapping[str, CommandClass] | None = None,
) -> PassAPlan:
    """The finite plan, in the order of the old draft: admission, identity, survey, final survey.

    ``include_corroboration`` adds the A1-C readlink/sha256sum steps; it stays off while
    the target-fact statement (RP-10) does not exist."""
    validate_paths()
    steps = _a0_and_identity_steps()
    if include_corroboration:
        at = next(i for i, step in enumerate(steps) if step.step_id == "A1-13")
        steps[at:at] = list(CORROBORATIVE_STEPS)
    steps.extend(_a1_tail_steps())
    steps.extend(_db_survey("A1-"))
    steps.extend(_lab_survey("A1-Z-", group_check=False))
    steps.extend(_db_survey("A1-Z-"))
    return PassAPlan(tuple(steps), dict(classes) if classes is not None else dict(CLASSES))


def derive_timeouts(
    measurements: Mapping[str, Measurement], base: Mapping[str, CommandClass] = BASE_CLASSES
) -> dict[str, CommandClass]:
    """``base`` with each named class's measurement attached (an unknown name is refused)."""
    if not set(measurements) <= set(base):
        raise PassAPlanError("malformed-class")
    return {
        name: (klass.with_measurement(measurements[name]) if name in measurements else klass)
        for name, klass in base.items()
    }


CLASSES: Mapping[str, CommandClass] = derive_timeouts(MEASUREMENTS, BASE_CLASSES)


__all__ = [
    "BASE_CLASSES",
    "CAPTURE_IDENTITY",
    "CAPTURE_PARENT",
    "CAPTURE_ROOT_A",
    "CAPTURE_ROOT_B",
    "CLASSES",
    "CORROBORATIVE_STEPS",
    "ENVIRONMENTS",
    "EVIDENCE_RUN_ROOT",
    "FORBIDDEN_ENVIRONMENT_NAMES",
    "MEASUREMENTS",
    "MEASURED_MAX_OUTPUT_BYTES",
    "MEASURED_WHOLE_PASS_SECONDS",
    "Measurement",
    "ObservedAccount",
    "ObservedDirectory",
    "PARENT_CONTRACT",
    "PASS_ID",
    "ParentContract",
    "PassAPlan",
    "PassAPlanError",
    "PlannedStep",
    "SOURCE_CHECKOUT",
    "ServiceIdentity",
    "WITHDRAWN_STEPS",
    "build_pass_a_plan",
    "created_leaf_problems",
    "derive_timeouts",
    "environment_problems",
    "identity_problems",
    "leaf_absent_problems",
    "parent_problems",
    "root_policy",
    "validate_paths",
]
