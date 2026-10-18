"""RT-3 ``deact … stop-post``: the shared cleanup engine on temporary trees.

Every activation path lives under ``tmp_path`` (``Layout``) and the test user
stands in for root (``Owner``). Real descriptor-relative filesystem adapters are
used throughout; systemd, Polkit and the baseline are injected fakes here and
real on the disposable host (``tests/systemd_integration``).

Row coverage (inventory §4.16, §5.3) is named in each test's docstring.
"""

from __future__ import annotations

import fcntl
import grp
import hashlib
import json
import os
import pwd
import re
import stat
import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True  # repo umask 0002 would leave group-writable bytecode

from adapters.rp11.fsops import (  # noqa: E402
    FileIO,
    LocalActivationFs,
    LocalAttemptStore,
    LocalHostFacts,
    LocalLock,
    LocalRecordStore,
    UNREACHABLE,
    open_dir,
)
from adapters.rp11.stop_post import build_procedure, run_stop_post  # noqa: E402
from application.rp11.attribution import (  # noqa: E402
    Attribution,
    Identity,
    ObjectKind,
    Observed,
    Owner,
    classify,
    classify_file,
)
from application.rp11.authority import (  # noqa: E402
    A2Pins,
    AuthorityError,
    H1Record,
    Operator,
    Params,
)
from application.rp11.baseline import first_difference  # noqa: E402
from application.rp11.canonical import CanonicalError, canonical_bytes, parse_canonical  # noqa: E402
from application.rp11.cleanup import CleanupProcedure, GrrOutcome, Invocation, Terminal, Trigger, grr_outcome  # noqa: E402
from application.rp11.journal import (  # noqa: E402
    GENESIS,
    JournalKind,
    JournalSchemaError,
    parse_journal,
    serialize_line,
)
from application.rp11.paths import ActivationPaths, Layout  # noqa: E402
from application.rp11.pk import PkOutcome, PkResult  # noqa: E402
from application.rp11.sn import ChildHandle, HandleState  # noqa: E402
from application.rp11.ports import EvidenceWriteError, RemovalOutcome  # noqa: E402
from application.rp11.records import validate_record  # noqa: E402
from application.unit_control import ControlError, ControlOk, UnitProperty  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rp11_fixtures import ActivationFixture  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ACT_ID = "rp11-act-20261013T101500Z-0a1b2c3d"
BOOT = "11111111-2222-3333-4444-555555555555"
OTHER_BOOT = "99999999-2222-3333-4444-555555555555"

pytestmark = pytest.mark.skipif(os.geteuid() == 0, reason="the local tree tests run unprivileged")


# ---------------------------------------------------------------------------
# fixtures and fakes
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _umask():
    previous = os.umask(0o022)
    yield
    os.umask(previous)


@pytest.fixture
def layout(tmp_path: Path) -> Layout:
    for d in ("run", "var_tmp", "tool"):
        (tmp_path / d).mkdir(mode=0o755)
    (tmp_path / "boot_id").write_text(BOOT + "\n")
    (tmp_path / "mountinfo").write_text(
        f"25 1 0:23 / {tmp_path / 'run'} rw,nosuid shared:5 - tmpfs tmpfs rw\n"
    )
    tool = tmp_path / "tool/rp11_h1.py"
    tool.write_text("# entry\n")
    os.chmod(tool, 0o644)
    return Layout(
        run=str(tmp_path / "run"),
        var_tmp=str(tmp_path / "var_tmp"),
        store=str(tmp_path / "store"),
        owner=Owner(os.getuid(), os.getgid()),
        tool=str(tool),
        boot_id_file=str(tmp_path / "boot_id"),
        mountinfo=str(tmp_path / "mountinfo"),
    )


def _baseline() -> dict:
    me = pwd.getpwuid(os.getuid())
    return {
        "host": {"nodename": "test", "architecture": "x86_64"},
        "operator": {
            "user": me.pw_name,
            "uid": me.pw_uid,
            "gid": me.pw_gid,
            "groups": [[grp.getgrgid(me.pw_gid).gr_name, me.pw_gid]],
        },
        "packages": [["systemd", "260", "amd64"]],
    }


@pytest.fixture
def fx(layout: Layout) -> ActivationFixture:
    fixture = ActivationFixture(
        layout, ACT_ID, BOOT, _baseline(), operator_user=pwd.getpwuid(os.getuid()).pw_name
    )
    fixture.write_authority()
    return fixture


class Events(list):
    def mark(self, name: str) -> None:
        self.append(name)


class FakeUnits:
    def __init__(self, events: Events, states=("inactive", "inactive"), error: bool = False):
        self.events = events
        self.states = list(states)
        self.error = error

    def read_unit(self, unit, props):
        self.events.mark("di1")
        if self.error:
            return ControlError(getattr(self, "kind", "timeout"))
        state = self.states.pop(0) if len(self.states) > 1 else self.states[0]
        values = {
            UnitProperty.ACTIVE_STATE: state,
            UnitProperty.INACTIVE_ENTER_TIMESTAMP_MONOTONIC: 0,
        }
        return ControlOk({p: values[p] for p in props})


class FakePk:
    """A ``seek-not-authorized`` series as PkSeries returns it: a decided
    ``not-authorized`` after a settled subject, otherwise ``unconfirmed``. A series
    never reports ``authorized`` in this mode; a still-authorized grant (outcome
    ``AUTHORIZED`` here) is its ``unconfirmed``/``still-authorized`` result."""

    def __init__(self, events: Events, outcome=PkOutcome.NOT_AUTHORIZED, reason=None):
        self.events = events
        self.outcome = outcome
        self.reason = reason
        self.calls = 0

    def run(self, operator, verb, mode):
        self.events.mark("pk")
        self.calls += 1
        outcome, reason = self.outcome, self.reason
        if outcome is PkOutcome.AUTHORIZED:
            outcome, reason = PkOutcome.UNCONFIRMED, reason or "still-authorized"
        elif outcome is PkOutcome.NOT_AUTHORIZED:
            reason = reason or "decided"
        else:
            reason = reason or "only-errors"
        child = ChildHandle(
            pid=4242, pgid=4242, start_ticks=100, created_ms=0, deadline_ms=1_000, s0_ran=True,
            grace_deadline_ms=1, state=HandleState.REAPED,
            sends=[{"signal": "SIGKILL", "result": "sent", "offset_ms": 0, "late": False}],
        ).entry()
        return PkResult(mode, verb, outcome, reason, calls=1, children=[child])


class FakeBaseline:
    def __init__(self, events: Events, value):
        self.events = events
        self.value = value

    def recompute(self):
        self.events.mark("baseline")
        return self.value


class FakeServices:
    def __init__(self, events: Events, *, units=None, pk=None, baseline="same"):
        self.events = events
        self._units = units or FakeUnits(events)
        self._pk = pk or FakePk(events)
        self._baseline = FakeBaseline(events, _baseline() if baseline == "same" else baseline)

    def units(self, params):
        return self._units

    def pk(self, params):
        return self._pk

    def baseline(self, params):
        return self._baseline


class RecordingFs(LocalActivationFs):
    """The real adapter, recording each call and optionally crashing at one."""

    def __init__(self, owner, events: Events, crash: str | None = None):
        super().__init__(owner)
        self.events = events
        self.crash = crash

    def _hit(self, name: str) -> None:
        self.events.mark(name)
        if self.crash == name:
            raise Crash(name)

    def read_root_file(self, path, **kw):
        self._hit(f"read:{Path(path).name}")
        return super().read_root_file(path, **kw)

    def read_journal(self, directory, **kw):
        self._hit(f"read-journal:{Path(directory).name}")
        return super().read_journal(directory, **kw)

    def remove(self, path, identity, *, directory, before_unlink):
        name = Path(path).name

        def ahead(observed):
            before_unlink(observed)
            self._hit(f"unlink:{name}")

        result = super().remove(path, identity, directory=directory, before_unlink=ahead)
        if result.outcome is RemovalOutcome.REMOVED:
            self._hit(f"removed:{name}")
        return result


class Crash(BaseException):
    """A process death at an interruption point (BaseException: nothing catches it)."""


class RecordingLock(LocalLock):
    def __init__(self, *a, events: Events, **kw):
        super().__init__(*a, **kw)
        self.events = events

    def acquire(self, deadline_ms):
        self.events.mark("lock")
        return super().acquire(deadline_ms)


class RecordingAttempts(LocalAttemptStore):
    def __init__(self, *a, events: Events, crash: str | None = None, **kw):
        super().__init__(*a, **kw)
        self.events = events
        self.crash = crash

    def create(self, k):
        self.events.mark("attempt-dir")
        sink = super().create(k)
        if self.crash == "after-attempt-dir":
            raise Crash("after-attempt-dir")
        return sink


class FakeClock:
    def __init__(self):
        self.now = 1_000_000

    def monotonic_ms(self):
        return self.now

    def sleep_ms(self, ms):
        self.now += ms


class FailingIO(FileIO):
    """Fails the n-th write (short write) or fsync (error) on journals and records."""

    def __init__(self, *, fail_write_at: int | None = None, fail_fsync_at: int | None = None):
        self.writes = 0
        self.fsyncs = 0
        self.fail_write_at = fail_write_at
        self.fail_fsync_at = fail_fsync_at

    def write(self, fd, data):
        self.writes += 1
        if self.writes == self.fail_write_at:
            return os.write(fd, data[: len(data) // 2])  # short write: a torn line
        return super().write(fd, data)

    def fsync(self, fd):
        self.fsyncs += 1
        if self.fsyncs == self.fail_fsync_at:
            raise OSError(5, "EIO")
        super().fsync(fd)


class InspectionFault:
    """A deterministic failure of one inspection call on one target object, raised
    inside the real ``adapters.rp11.fsops`` (which calls ``os.<call>``).

    ``call``: ``fstat``, ``read`` (the bounded content read for the hash),
    ``listxattr``, ``listdir`` (a directory's emptiness), or ``fallback`` (the
    final ``open`` refused with ``EACCES`` and the no-follow ``lstat`` of the
    fallback observation then failing with ``EIO``). Every other descriptor and
    name is untouched. Only while ``active``; ``hits`` counts injected failures.
    """

    CALLS = ("fstat", "read", "listxattr", "listdir", "fallback")

    def __init__(self, monkeypatch, target: str, call: str, *, active: bool = True):
        assert call in self.CALLS
        self.target = os.path.realpath(target)
        self.parent, self.name = os.path.split(self.target)
        self.call = call
        self.active = active
        self.hits = 0
        real = {n: getattr(os, n) for n in ("fstat", "read", "listxattr", "listdir", "open", "stat")}

        def names(fd, path) -> bool:
            if not (self.active and type(fd) is int and fd >= 0):
                return False
            try:
                return os.readlink(f"/proc/self/fd/{fd}") == path
            except OSError:
                return False

        def fail(err=5):
            self.hits += 1
            raise OSError(err, os.strerror(err))

        def on_fd(name):
            def patched(fd, *a, **kw):
                if names(fd, self.target):
                    fail()
                return real[name](fd, *a, **kw)
            return patched

        if call in ("fstat", "read", "listxattr", "listdir"):
            monkeypatch.setattr(os, call, on_fd(call))
            return

        def open_(path, flags, mode=0o777, *, dir_fd=None):
            if path == self.name and dir_fd is not None and names(dir_fd, self.parent):
                fail(13)
            return real["open"](path, flags, mode, dir_fd=dir_fd)

        def stat_(path, *, dir_fd=None, follow_symlinks=True):
            if path == self.name and dir_fd is not None and names(dir_fd, self.parent):
                fail()
            return real["stat"](path, dir_fd=dir_fd, follow_symlinks=follow_symlinks)

        monkeypatch.setattr(os, "open", open_)
        monkeypatch.setattr(os, "stat", stat_)


class CloseFault:
    """A deterministic failure of ``os.close`` on the target's descriptor or on its
    parent directory's descriptor, raised inside the real ``adapters.rp11.fsops``.

    ``role``: ``target`` (a descriptor naming the object) or ``parent`` (one naming
    its directory). ``shape``: ``closed`` (the descriptor is really closed, then
    ``EIO`` is reported) or ``unknown`` (``EIO`` is reported and the descriptor is
    left open, its state unknown to the caller; the fixture closes it afterwards).
    ``attempts`` lists every descriptor number a close was attempted on while
    faulting: a retry would repeat a number. Only while ``active``.
    """

    ROLES = ("target", "parent")
    SHAPES = ("closed", "unknown")

    def __init__(self, monkeypatch, target: str, role: str, shape: str = "closed", *, active: bool = True):
        assert role in self.ROLES and shape in self.SHAPES
        real = os.path.realpath(target)
        self.path = real if role == "target" else os.path.dirname(real)
        self.shape = shape
        self.active = active
        self.attempts: list[int] = []
        self.leaked: list[int] = []
        real_close = os.close

        def close(fd):
            if self.active and type(fd) is int and fd >= 0:
                try:
                    hit = os.readlink(f"/proc/self/fd/{fd}") == self.path
                except OSError:
                    hit = False
                if hit:
                    self.attempts.append(fd)
                    if shape == "closed":
                        real_close(fd)
                    else:
                        self.leaked.append(fd)
                    raise OSError(5, "EIO")
            return real_close(fd)

        self._real_close = real_close
        monkeypatch.setattr(os, "close", close)

    @property
    def hits(self) -> int:
        return len(self.attempts)

    def never_retried(self) -> bool:
        return len(set(self.attempts)) == len(self.attempts)

    def release(self) -> None:
        for fd in self.leaked:
            try:
                self._real_close(fd)
            except OSError:
                pass
        self.leaked.clear()


@pytest.fixture
def close_fault(monkeypatch, request):
    made: list[CloseFault] = []

    def make(target: str, role: str, shape: str = "closed", **kw) -> CloseFault:
        fault = CloseFault(monkeypatch, target, role, shape, **kw)
        made.append(fault)
        return fault

    yield make
    for fault in made:
        fault.active = False
        fault.release()


def procedure(
    layout: Layout,
    fx: ActivationFixture,
    *,
    events: Events | None = None,
    services=None,
    crash: str | None = None,
    io: FileIO | None = None,
    record_io: FileIO | None = None,
    clock=None,
    a2: str | None = None,
    trigger: Trigger = Trigger.STOP_POST,
    holder_state: str = "deactivating",
) -> tuple[CleanupProcedure, Events]:
    events = events if events is not None else Events()
    paths = ActivationPaths(layout, ACT_ID)
    fs = RecordingFs(layout.owner, events, crash)
    clock = clock or FakeClock()
    proc = CleanupProcedure(
        Invocation(
            ACT_ID,
            a2 or fx.a2_sha256,
            trigger,
            *((None, None) if trigger is Trigger.ATTEST else (4242, "0123456789abcdef0123456789abcdef")),
            holder_state=holder_state,
        ),
        paths,
        fs=fs,
        journals=fs,
        attempts=RecordingAttempts(
            var_tmp=layout.var_tmp, activation_id=ACT_ID, owner=layout.owner, io=io, events=events, crash=crash
        ),
        records=LocalRecordStore(paths.record_dir, layout.owner, io=record_io),
        lock=RecordingLock(paths.lock_dir, layout.owner, clock, events=events),
        host=LocalHostFacts(boot_id_file=layout.boot_id_file, mountinfo=layout.mountinfo, run=layout.run),
        services=services or FakeServices(events),
        tool_sha256=hashlib.sha256(b"# entry\n").hexdigest(),
    )
    return proc, events


def run_cl(layout, fx, **kw):
    proc, events = procedure(layout, fx, **kw)
    return proc.run(), events


def attempt_journal(layout: Layout, k: int) -> list[dict]:
    data = Path(layout.var_tmp, f"{ACT_ID}-deact-{k}-evidence/journal").read_bytes()
    return [json.loads(line) for line in data.splitlines()]


def ops(layout, k) -> list[str]:
    return [line["op"] for line in attempt_journal(layout, k)]


def record(layout, k) -> dict:
    data = Path(layout.store, f"activation/{ACT_ID}.deact-{k}.json").read_bytes()
    doc = parse_canonical(data)
    validate_record(doc)
    return doc


def paths(layout) -> ActivationPaths:
    return ActivationPaths(layout, ACT_ID)


# ---------------------------------------------------------------------------
# canonical bytes and the journal format (H-JRN.4 … H-JRN.10)
# ---------------------------------------------------------------------------


def test_canonical_bytes_match_the_accepted_serialization():
    doc = {"b": [1, True, "x"], "a": {"z": "absent"}}
    assert canonical_bytes(doc) == b'{"a":{"z":"absent"},"b":[1,true,"x"]}\n'
    assert parse_canonical(canonical_bytes(doc)) == doc


@pytest.mark.parametrize(
    "data",
    [
        b'{"a":1.5}\n',
        b'{"a":null}\n',
        b'{"a": 1}\n',
        b'{"b":1,"a":2}\n',
        b'{"a":1,"a":1}\n',
        b'{"a":"\xc3\xa9"}\n',
        b'{"a":1}',
        b'{"a":NaN}\n',
        b"[1]\n[2]\n",
    ],
)
def test_non_canonical_bytes_are_refused(data):
    with pytest.raises(CanonicalError):
        parse_canonical(data)


def _act_lines(n_extra: int = 1) -> bytes:
    lines = []
    prev = GENESIS
    start = {
        "a2_sha256": "a" * 64,
        "h1_record_sha256": "b" * 64,
        "h2_record_sha256": "e" * 64,
        "boot_id": BOOT,
        "pass_config_sha256": "c" * 64,
        "staged_rule_sha256": "d" * 64,
        "lock": {"object": {"path": "/run/k", "dev": 1, "ino": 2}, "mode": "held", "wait_ms": 0},
        "capture": {
            "active_state": "inactive",
            "invocation_id": "absent",
            "inactive_enter_us": 0,
            "m_a_us": 1,
            "bsp_retries": 0,
        },
        "holder_invocation_id": "absent",
        "tool_sha256": "f" * 64,
        "helper": {"role": "hold", "image_sha256": ["9" * 64], "tool_sha256": "f" * 64},
        "lease": {"lease_s": 900},
        "params": {"pk_op_ms": 5000},
    }
    entries = [("run-start", start)] + [("hold-end", {"reason": "pass-ended", "observation": "absent"})] * n_extra
    for seq, (op, fields) in enumerate(entries, start=1):
        line = serialize_line(JournalKind.ACT, seq=seq, prev=prev, run=ACT_ID, op=op, fields=fields)
        lines.append(line)
        prev = hashlib.sha256(line).hexdigest()
    return b"".join(lines)


def test_a_valid_journal_parses_and_reports_its_digest():
    data = _act_lines(2)
    parsed = parse_journal(data, kind=JournalKind.ACT, run=ACT_ID)
    assert parsed.valid and len(parsed.lines) == 3 and not parsed.torn_tail
    assert parsed.sha256 == hashlib.sha256(data).hexdigest() and parsed.length == len(data)


def test_a_torn_tail_is_ignored_and_reported():
    data = _act_lines(1) + b'{"seq":3,"op":"hold-e'
    parsed = parse_journal(data, kind=JournalKind.ACT, run=ACT_ID)
    assert parsed.valid and parsed.torn_tail and len(parsed.lines) == 2


@pytest.mark.parametrize(
    "mutate,reason",
    [
        (lambda d: d.replace(b'"seq":2', b'"seq":3'), "seq"),
        (lambda d: d.replace(b'"prev":"' + b"0" * 64, b'"prev":"' + b"1" * 64), "prev"),
        (lambda d: d.replace(ACT_ID.encode(), b"rp11-act-20261013T101500Z-ffffffff"), "run"),
        (lambda d: d.replace(b'"op":"hold-end"', b'"op":"hold-xxx"'), "op"),
        (lambda d: d.replace(b'"reason":"pass-ended"', b'"reason":"pass-ended","x":1'), ""),
        (lambda d: d.replace(b'"reason":"pass-ended"', b'"reason": "pass-ended"'), "canonical"),
        (lambda d: d.replace(b'"reason":"pass-ended",', b""), ""),
        (lambda d: b"", "no complete line"),
    ],
)
def test_an_invalid_journal_is_invalid_as_a_whole(mutate, reason):
    parsed = parse_journal(mutate(_act_lines(1)), kind=JournalKind.ACT, run=ACT_ID)
    assert not parsed.valid and parsed.lines == ()


def test_a_line_outside_its_op_grammar_cannot_be_written():
    with pytest.raises(JournalSchemaError):
        serialize_line(JournalKind.ATTEMPT, seq=1, prev=GENESIS, run="r", op="removed", fields={"path": "rel"})
    with pytest.raises(JournalSchemaError):
        serialize_line(JournalKind.ATTEMPT, seq=1, prev=GENESIS, run="r", op="igr", fields={"outcome": "removed"})


# ---------------------------------------------------------------------------
# attribution (H-GR1.1)
# ---------------------------------------------------------------------------


def _obs(**kw) -> Observed:
    base = dict(kind=ObjectKind.FILE, dev=1, ino=2, uid=0, gid=0, mode=0o644, nlink=1, size=3, sha256="e" * 64)
    base.update(kw)
    return Observed(**base)


IDENT = Identity("/run/x", ObjectKind.FILE, 1, 2, 0o644, "e" * 64, 3)


@pytest.mark.parametrize(
    "observed,expected",
    [
        (_obs(), Attribution.A1_INTACT),
        (None, Attribution.ABSENT),
        (_obs(ino=3), Attribution.A0),
        (_obs(kind=ObjectKind.SYMLINK), Attribution.A0),
        (_obs(sha256="f" * 64), Attribution.A1_DAMAGED),
        (_obs(mode=0o666), Attribution.A1_DAMAGED),
        (_obs(uid=1000), Attribution.A1_DAMAGED),
        (_obs(nlink=2), Attribution.A1_DAMAGED),
        (_obs(size=4), Attribution.A1_DAMAGED),
        (_obs(sha256=None), Attribution.A1_DAMAGED),
        (_obs(xattr_names=("system.posix_acl_access",)), Attribution.A1_DAMAGED),
    ],
)
def test_attribution_classes(observed, expected):
    assert classify(IDENT, observed, Owner()) is expected


def test_no_identity_makes_any_present_object_a0():
    assert classify(None, _obs(), Owner()) is Attribution.A0


# ---------------------------------------------------------------------------
# authority chain (A-2 → H-1)
# ---------------------------------------------------------------------------


def test_authority_chains_from_the_operand(fx, layout):
    store = Path(layout.store)
    a2 = (store / "a2" / f"{fx.a2_sha256}.json").read_bytes()
    pins = A2Pins.parse(a2, operand_sha256=fx.a2_sha256, activation_id=ACT_ID)
    h1 = H1Record.parse((store / "h1" / f"{pins.h1_record_id}.json").read_bytes(), pins=pins)
    assert h1.params.pk_op_ms == 5_000 and h1.operator.uid == os.getuid()
    with pytest.raises(AuthorityError):
        A2Pins.parse(a2, operand_sha256="0" * 64, activation_id=ACT_ID)
    with pytest.raises(AuthorityError):
        A2Pins.parse(a2, operand_sha256=fx.a2_sha256, activation_id="rp11-act-20261013T101500Z-ffffffff")
    with pytest.raises(AuthorityError):
        H1Record.parse(b"{}\n", pins=pins)


@pytest.mark.parametrize(
    "field,value",
    [("pk_op_ms", 4_999), ("pk_call_ms", 10_001), ("reap_grace_ms", 499), ("lock_wait_ms", 999),
     ("slice_ms", 251), ("journal_max_bytes", 1), ("pk_op_ms", True)],
)
def test_parameters_outside_their_accepted_range_are_refused(field, value):
    doc = Params().to_doc()
    doc[field] = value
    with pytest.raises(AuthorityError):
        Params.from_doc(doc)


def test_an_operator_in_group_0_is_refused():
    with pytest.raises(AuthorityError):
        Operator.from_baseline({"operator": {"user": "u", "uid": 5, "gid": 5, "groups": [["root", 0], ["u", 5]]}})


def test_first_difference_names_a_key_path_not_a_value():
    a = {"host": {"kernel_release": "7.0.0"}, "files": [{"sha256": "a"}]}
    b = {"host": {"kernel_release": "7.0.1"}, "files": [{"sha256": "a"}]}
    assert first_difference(a, b) == "baseline.host.kernel_release"
    assert first_difference(a, {**a, "files": [{"sha256": "b"}]}) == "baseline.files[0].sha256"
    assert first_difference(a, {"host": a["host"]}) == "baseline.files"


# ---------------------------------------------------------------------------
# RT-3 end to end: valid cleanup to st1-verified
# ---------------------------------------------------------------------------


def test_valid_cleanup_reaches_st1_verified_and_removes_every_activation_object(fx, layout):
    """RT3.CLG … RT3.CL7, RT3.CLOUT: grant.id-driven CL-G, every object removed,
    both records published, the attempt journal complete and chained."""
    fx.activate()
    out, _ = run_cl(layout, fx)
    assert out.terminal is Terminal.ST1_VERIFIED and out.terminal.exit_code == 0
    p = paths(layout)
    for path in (p.rule, p.pass_config, p.tree_p, p.grant_id, p.lock_dir):
        assert not os.path.lexists(path), path
    assert os.path.isdir(p.rules_dir)  # pre-existing: never removed
    doc = record(layout, 1)
    assert doc["outcome"] == "st1-verified" and doc["failure"] == "absent"
    assert doc["active_rule"]["class"] == "removed-earlier"
    assert doc["grant_identity"]["cl_g"] == "removed" and doc["release"]["first_rung"] == "cl-g"
    assert doc["pass_config"]["class"] == "removed"
    assert [d["class"] for d in doc["directories"]] == ["removed", "pre-existing-kept", "removed"]
    assert doc["st1"]["verified"] and all(doc["st1"]["checks"].values())
    assert doc["lock"]["mode"] == "held"
    act = Path(layout.store, f"activation/{ACT_ID}.act.json")
    assert stat.S_IMODE(act.stat().st_mode) == 0o444 and json.loads(act.read_text())["outcome"] == "failed"
    assert ops(layout, 1)[:2] == ["run-start", "cl-g"] and ops(layout, 1)[-1] == "run-end"
    parsed = parse_journal(
        Path(layout.var_tmp, f"{ACT_ID}-deact-1-evidence/journal").read_bytes(),
        kind=JournalKind.ATTEMPT,
        run=f"{ACT_ID}-deact-1",
    )
    assert parsed.valid
    own = [j for j in doc["journals"] if j["path"].endswith("deact-1-evidence/journal")][0]
    lines = [line.raw for line in parsed.lines]
    intent_index = next(
        i for i, line in enumerate(parsed.lines)
        if line.op == "file-intent" and line.fields["name"].endswith("deact-1.json")
    )
    prefix = b"".join(lines[:intent_index])
    assert own == {"path": own["path"], "sha256": hashlib.sha256(prefix).hexdigest(), "length": len(prefix)}


def test_without_grant_id_the_journal_based_removal_is_write_ahead_and_verified(fx, layout):
    """H-CL.G.1 identity-unavailable ⇒ CL-3 G-R1 with write-ahead; INV-13 removed-verified."""
    fx.activate(grant_id=False)
    out, _ = run_cl(layout, fx)
    assert out.terminal is Terminal.ST1_VERIFIED
    journal = attempt_journal(layout, 1)
    rule = paths(layout).rule
    idx_intent = next(i for i, l in enumerate(journal) if l["op"] == "remove-intent" and l["path"] == rule)
    assert journal[idx_intent + 1] == {**journal[idx_intent + 1], "op": "removed", "path": rule}
    assert journal[1]["outcome"] == "identity-unavailable"
    assert record(layout, 1)["active_rule"]["class"] == "removed-verified"


def test_without_the_act_positive_control_removal_is_only_unconfirmed(fx, layout):
    fx.activate(grant_id=False, positive_control=False)
    out, _ = run_cl(layout, fx)
    assert out.rule_class == "removed-unconfirmed" and out.terminal is Terminal.HARD_STOP


def test_a_repeated_cleanup_after_st1_verified_removes_nothing_and_verifies_again(fx, layout):
    """AC-12: idempotence; the second attempt classes everything removed-earlier."""
    fx.activate(grant_id=False)
    assert run_cl(layout, fx)[0].terminal is Terminal.ST1_VERIFIED
    out, _ = run_cl(layout, fx)
    assert out.terminal is Terminal.ST1_VERIFIED and out.k == 2
    doc = record(layout, 2)
    assert doc["active_rule"]["class"] == "removed-earlier"
    assert doc["pass_config"]["class"] == "removed-earlier"
    assert len(doc["journals"]) == 3  # ACT, attempt 1, own prefix
    assert not Path(layout.store, f"activation/{ACT_ID}.deact-1.json").stat().st_mode & 0o222


# ---------------------------------------------------------------------------
# ordering: CL-G before every slower act (GR-2)
# ---------------------------------------------------------------------------


def test_the_grant_is_removed_before_any_ext4_read_lock_journal_or_polkit_call(fx, layout):
    fx.activate()
    out, events = run_cl(layout, fx)
    assert out.terminal is Terminal.ST1_VERIFIED
    removed = events.index("removed:50-freedom-blades-rp11.rules")
    assert events[:removed] == ["read:grant.id", "unlink:50-freedom-blades-rp11.rules"]
    for later in ("lock", "attempt-dir", "pk", "di1", "baseline", f"read:{fx.a2_sha256}.json"):
        assert events.index(later) > removed, later


def test_the_grant_is_still_removed_when_the_authority_is_invalid(fx, layout):
    fx.activate()
    out, _ = run_cl(layout, fx, a2="f" * 64)
    assert not os.path.lexists(paths(layout).rule)
    assert out.terminal is Terminal.HARD_STOP and out.failure == "invalid-authority"
    assert os.path.exists(paths(layout).pass_config)  # nothing else attributable
    doc = record(layout, 1)
    assert doc["h1_record"] == "absent" and doc["pk"]["outcome"] == "unconfirmed"


# ---------------------------------------------------------------------------
# journals: missing, torn, non-canonical, oversized, hash-chain, wrong run
# ---------------------------------------------------------------------------


def _rewrite_act(layout, transform):
    journal = Path(paths(layout).act_dir) / "journal"
    original = journal.read_bytes()
    data = transform(original)
    assert data != original, "the mutation must change the journal"
    os.chmod(journal, 0o644)
    journal.write_bytes(data)
    os.chmod(journal, 0o644)


@pytest.mark.parametrize(
    "transform",
    [
        lambda d: d.replace(b'"seq":2,', b'"seq":7,', 1),  # seq gap
        lambda d: d.replace(b'"seq":2,"tag"', b'"seq":2, "tag"', 1),  # non-canonical
        lambda d: d.replace(b'"op":"tree-sealed"', b'"op":"tree-sealer"'),  # unknown op
        lambda d: d.replace(b'"run":"' + ACT_ID.encode(), b'"run":"rp11-act-20261013T101500Z-ffffffff', 1),
        lambda d: d[:200] + (b"X" if d[200:201] != b"X" else b"Y") + d[201:],  # hash chain
    ],
    ids=["seq", "non-canonical", "op", "wrong-run", "chain"],
)
def test_an_invalid_act_journal_attributes_nothing(fx, layout, transform):
    """H-JRN.9 / H-CL.1.1: invalid ⇒ every object A0; only grant.id's CL-G still acts."""
    fx.activate()
    _rewrite_act(layout, transform)
    out, _ = run_cl(layout, fx)
    p = paths(layout)
    assert not os.path.lexists(p.rule)  # CL-G by grant.id, independent of the journal
    assert os.path.exists(p.pass_config) and os.path.isdir(p.tree_p)
    assert out.pass_class == "present-foreign-unremoved"
    assert out.terminal is Terminal.HARD_STOP
    doc = record(layout, 1)
    assert doc["failure"]["class"] in {"invalid-journal", "residual"}
    assert {r["path"] for r in doc["residual"]} >= {p.pass_config}
    assert "pass-a" not in json.dumps(doc["residual"]).replace(p.pass_config, "")  # no content


def test_a_missing_act_journal_and_no_grant_id_removes_nothing(fx, layout):
    fx.activate(grant_id=False)
    (Path(paths(layout).act_dir) / "journal").unlink()
    out, _ = run_cl(layout, fx)
    assert os.path.exists(paths(layout).rule) and out.rule_class == "present-foreign-unremoved"
    assert out.terminal is Terminal.HARD_STOP


def test_an_oversized_act_journal_is_invalid(fx, layout):
    fx.activate(grant_id=False)
    _rewrite_act(layout, lambda d: d + b"x" * (fx.params.journal_max_bytes + 1))
    out, _ = run_cl(layout, fx)
    assert os.path.exists(paths(layout).rule) and out.terminal is Terminal.HARD_STOP


def test_a_torn_act_tail_still_attributes_its_durable_prefix(fx, layout):
    fx.activate(grant_id=False)
    _rewrite_act(layout, lambda d: d + b'{"op":"hold-')
    out, _ = run_cl(layout, fx)
    assert out.terminal is Terminal.ST1_VERIFIED


def test_an_act_directory_with_the_wrong_mode_or_a_symlinked_journal_is_not_read(fx, layout):
    fx.activate(grant_id=False)
    os.chmod(paths(layout).act_dir, 0o755)
    out, _ = run_cl(layout, fx)
    assert os.path.exists(paths(layout).rule) and out.terminal is Terminal.HARD_STOP


def test_a_journal_naming_another_activation_authority_is_invalid(fx, layout):
    """CL-1: the ACT run-start must carry the operand's A-2 pins, else it attributes nothing."""
    fx.activate(grant_id=False)
    store = Path(layout.store)
    a2 = json.loads((store / "a2" / f"{fx.a2_sha256}.json").read_text())
    a2["pass_config_sha256"] = "0" * 64
    data = canonical_bytes(a2)
    sha = hashlib.sha256(data).hexdigest()
    other_a2 = store / "a2" / f"{sha}.json"
    other_a2.write_bytes(data)
    os.chmod(other_a2, 0o444)
    out, _ = run_cl(layout, fx, a2=sha)
    assert os.path.exists(paths(layout).rule) and out.terminal is Terminal.HARD_STOP


# ---------------------------------------------------------------------------
# objects: intact, absent, damaged, foreign, symlinked, replaced, unremovable
# ---------------------------------------------------------------------------


def _replace(path: str, data: bytes, mode: int = 0o644) -> None:
    """Same name and bytes, another inode (created first, so the number is not reused)."""
    fresh = Path(path + ".new")
    fresh.write_bytes(data)
    os.chmod(fresh, mode)
    os.rename(fresh, path)


def _damage(path: str) -> None:
    os.chmod(path, 0o644)
    with open(path, "r+b") as handle:
        handle.write(b"X")
    os.chmod(path, 0o644)


@pytest.mark.parametrize("grant_id", [True, False])
def test_a_damaged_rule_is_kept_and_escalated(fx, layout, grant_id):
    fx.activate(grant_id=grant_id)
    _damage(paths(layout).rule)
    out, _ = run_cl(layout, fx)
    assert os.path.exists(paths(layout).rule)
    assert out.rule_class == "present-damaged-unremoved" and out.terminal is Terminal.HARD_STOP
    residual = {r["path"]: r for r in record(layout, 1)["residual"]}
    assert residual[paths(layout).rule]["class"] == "present-damaged-unremoved"


@pytest.mark.parametrize("grant_id", [True, False])
def test_a_replaced_rule_is_foreign_and_kept(fx, layout, grant_id):
    fx.activate(grant_id=grant_id)
    _replace(paths(layout).rule, fx.rule_bytes)
    out, _ = run_cl(layout, fx)
    assert os.path.exists(paths(layout).rule) and out.rule_class == "present-foreign-unremoved"


@pytest.mark.parametrize("grant_id", [True, False])
def test_a_symlinked_rule_is_kept_and_its_target_untouched(fx, layout, grant_id, tmp_path):
    fx.activate(grant_id=grant_id)
    target = tmp_path / "target.rules"
    target.write_bytes(fx.rule_bytes)
    os.unlink(paths(layout).rule)
    os.symlink(target, paths(layout).rule)
    out, _ = run_cl(layout, fx)
    assert os.path.islink(paths(layout).rule) and target.read_bytes() == fx.rule_bytes
    assert out.rule_class == "present-foreign-unremoved"


def test_an_unremovable_rule_is_grant_unremovable(fx, layout):
    fx.activate()
    os.chmod(paths(layout).rules_dir, 0o555)
    try:
        out, _ = run_cl(layout, fx)
    finally:
        os.chmod(paths(layout).rules_dir, 0o755)
    assert out.rule_class == "grant-unremovable" and out.terminal is Terminal.HARD_STOP
    assert record(layout, 1)["grant_identity"]["cl_g"] == "unremovable"


def test_an_unremovable_journal_based_rule_is_journaled_as_remove_failed(fx, layout):
    fx.activate(grant_id=False)
    os.chmod(paths(layout).rules_dir, 0o555)
    try:
        out, _ = run_cl(layout, fx)
    finally:
        os.chmod(paths(layout).rules_dir, 0o755)
    assert out.rule_class == "grant-unremovable"
    assert "remove-failed" in ops(layout, 1)


@pytest.mark.parametrize("change", ["damage", "replace", "symlink"])
def test_pass_config_damaged_replaced_or_symlinked_is_kept(fx, layout, change, tmp_path):
    fx.activate()
    target = paths(layout).pass_config
    if change == "damage":
        _damage(target)
    elif change == "replace":
        _replace(target, fx.pass_bytes)
    else:
        os.unlink(target)
        os.symlink(tmp_path / "elsewhere", target)
    out, _ = run_cl(layout, fx)
    assert os.path.lexists(target)
    assert out.pass_class == ("present-damaged-unremoved" if change == "damage" else "present-foreign-unremoved")
    assert "present-nonempty-unremoved" in out.dir_classes  # tree P is not empty
    assert not os.path.lexists(paths(layout).rule)  # the grant still goes first


def test_a_tree_p_holding_a_foreign_file_is_not_removed(fx, layout):
    fx.activate()
    Path(paths(layout).tree_p, "planted").write_text("x")
    out, _ = run_cl(layout, fx)
    assert os.path.isdir(paths(layout).tree_p) and Path(paths(layout).tree_p, "planted").exists()
    assert out.dir_classes[0] == "present-nonempty-unremoved"


def test_a_replaced_tree_p_directory_is_foreign(fx, layout):
    fx.activate()
    tree = paths(layout).tree_p
    os.unlink(paths(layout).pass_config)
    os.mkdir(tree + ".new", 0o755)
    os.rename(tree + ".new", tree)  # another inode at the same name
    out, _ = run_cl(layout, fx)
    assert os.path.isdir(tree) and out.dir_classes[0] == "present-foreign-unremoved"


def test_a_grant_id_naming_another_object_removes_nothing(fx, layout):
    """NT-LD-10: a grant.id whose identity is not at the rule path removes nothing."""
    fx.activate()
    p = paths(layout)
    doc = parse_canonical(Path(p.grant_id).read_bytes())
    doc["ino"] += 1
    _replace(p.grant_id, canonical_bytes(doc), 0o600)
    out, _ = run_cl(layout, fx)
    assert os.path.exists(p.rule) and out.rule_class == "present-foreign-unremoved"
    assert record(layout, 1)["grant_identity"]["conflict"] is True


@pytest.mark.parametrize("mode", [0o644, 0o640])
def test_a_grant_id_with_the_wrong_mode_is_identity_unavailable(fx, layout, mode):
    fx.activate()
    os.chmod(paths(layout).grant_id, mode)
    out, _ = run_cl(layout, fx)
    journal = attempt_journal(layout, 1)
    assert journal[1]["outcome"] == "identity-unavailable"
    assert out.rule_class == "removed-verified"  # the journal-based path still removes it


def test_objects_never_given_an_identity_are_never_linked(fx, layout):
    """H-CL.3.1: absent with no identity line ⇒ never-linked (a file-intent alone is no identity)."""
    fx.activate(rule=False, pass_config=False, grant_id=False)
    out, _ = run_cl(layout, fx)
    assert out.rule_class == "never-linked" and out.pass_class == "never-linked"
    assert out.terminal is Terminal.ST1_VERIFIED


def test_identified_objects_found_absent_are_absent_before_removal(fx, layout):
    """H-CL.3.1 / IM-I I2: absent, identity durable, no removal line ⇒ absent-before-removal."""
    fx.activate()
    p = paths(layout)
    for path in (p.rule, p.pass_config, p.grant_id):
        os.unlink(path)
    out, _ = run_cl(layout, fx)
    assert out.rule_class == "absent-before-removal" and out.pass_class == "absent-before-removal"
    assert out.terminal is Terminal.ST1_VERIFIED  # still needs, and gets, PK not authorized


def test_other_boot_objects_are_a0_and_absent_ones_cleared_by_boot(fx, layout):
    """H-CL.1.3 boot scoping; H-CL.3.1 cleared-by-boot needs /run to be tmpfs."""
    fx.activate()
    p = paths(layout)
    os.unlink(p.rule)
    Path(layout.boot_id_file).write_text(OTHER_BOOT + "\n")
    out, _ = run_cl(layout, fx)
    assert out.rule_class == "cleared-by-boot"
    assert os.path.exists(p.pass_config) and out.pass_class == "present-foreign-unremoved"
    assert out.terminal is Terminal.HARD_STOP


def test_without_tmpfs_an_absent_other_boot_rule_is_not_cleared_by_boot(fx, layout):
    fx.activate()
    os.unlink(paths(layout).rule)
    Path(layout.boot_id_file).write_text(OTHER_BOOT + "\n")
    Path(layout.mountinfo).write_text(f"25 1 0:23 / {layout.run} rw - ext4 /dev/x rw\n")
    out, _ = run_cl(layout, fx)
    assert out.rule_class == "absent-before-removal"


def test_tree_r_created_by_act_is_removed_bottom_up(fx, layout):
    fx.rules_dir_preexists = False
    fx.activate()
    out, _ = run_cl(layout, fx)
    assert out.terminal is Terminal.ST1_VERIFIED
    assert not os.path.lexists(paths(layout).polkit_run_dir)
    assert out.dir_classes == ["removed", "removed", "removed", "removed"]


def test_an_s0_temporary_name_is_reported_and_kept(fx, layout):
    fx.activate()
    temp = Path(layout.run, f".rp11-{ACT_ID}-p.tmp")
    temp.mkdir(mode=0o700)
    out, _ = run_cl(layout, fx)
    assert temp.is_dir() and out.terminal is Terminal.ST1_VERIFIED
    assert [r["class"] for r in record(layout, 1)["residual"]] == ["s0"]


# ---------------------------------------------------------------------------
# lock (CL-0): acquired, degraded at λ, absent; concurrency; k exhaustion
# ---------------------------------------------------------------------------


def test_a_lock_held_elsewhere_degrades_after_lambda_and_cleanup_continues(fx, layout):
    fx.activate()
    holder = os.open(paths(layout).lock_dir, os.O_RDONLY | os.O_DIRECTORY)
    fcntl.flock(holder, fcntl.LOCK_EX)
    clock = FakeClock()
    try:
        out, _ = run_cl(layout, fx, clock=clock)
    finally:
        os.close(holder)
    doc = record(layout, 1)
    assert doc["lock"]["mode"] == "degraded" and doc["lock"]["wait_ms"] >= fx.params.lock_wait_ms
    assert out.terminal is Terminal.ST1_VERIFIED


def test_an_absent_lock_object_is_recorded_absent(fx, layout):
    fx.activate(grant_id=False)
    os.rmdir(paths(layout).lock_dir)
    out, _ = run_cl(layout, fx)
    assert record(layout, 1)["lock"]["mode"] == "absent"
    assert out.dir_classes[-1] == "absent-before-removal"


def test_a_lock_object_with_the_wrong_mode_is_not_used(fx, layout):
    fx.activate(grant_id=False)
    os.chmod(paths(layout).lock_dir, 0o755)
    out, _ = run_cl(layout, fx)
    assert record(layout, 1)["lock"]["mode"] == "absent"
    assert os.path.isdir(paths(layout).lock_dir)  # not A1-intact: kept
    assert out.terminal is Terminal.HARD_STOP


def test_a_concurrent_attempt_owning_k_acts_on_nothing_further(fx, layout, monkeypatch):
    fx.activate()
    original = LocalActivationFs.list_prefixed
    monkeypatch.setattr(LocalActivationFs, "list_prefixed", lambda self, d, p: ())
    Path(layout.var_tmp, f"{ACT_ID}-deact-1-evidence").mkdir()
    out, events = run_cl(layout, fx)
    monkeypatch.setattr(LocalActivationFs, "list_prefixed", original)
    assert out.terminal is Terminal.CONCURRENT_DEACT and out.terminal.exit_code == 5
    assert "pk" not in events and os.path.exists(paths(layout).pass_config)
    assert not os.path.lexists(paths(layout).rule)  # CL-G already ran
    assert not Path(layout.store, f"activation/{ACT_ID}.deact-1.json").exists()


def test_attempt_number_exhaustion_enters_grant_priority_mode(fx, layout):
    fx.activate()
    for k in range(1, 100):
        Path(layout.var_tmp, f"{ACT_ID}-deact-{k}-evidence").mkdir()
    out, _ = run_cl(layout, fx)
    assert out.terminal is Terminal.EVIDENCE_UNWRITABLE and out.k is None
    p = paths(layout)
    assert not os.path.lexists(p.rule) and not os.path.lexists(p.pass_config)
    assert not list(Path(layout.store, "activation").iterdir())


# ---------------------------------------------------------------------------
# DI results: unit state, Polkit series, baseline
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("state", ["active", "activating", "deactivating", "reloading"])
def test_an_active_capture_unit_is_unit_still_active_after_removing_the_grant(fx, layout, state):
    fx.activate()
    events = Events()
    out, _ = run_cl(layout, fx, events=events, services=FakeServices(events, units=FakeUnits(events, (state,))))
    assert out.terminal is Terminal.UNIT_STILL_ACTIVE and out.terminal.exit_code == 2
    assert not os.path.lexists(paths(layout).rule)
    assert record(layout, 1)["failure"]["class"] == "unit-still-active"


@pytest.mark.parametrize(
    "kind", ["timeout", "disconnected", "invalid-reply", "org.freedesktop.DBus.Error.UnknownObject"]
)
def test_a_failed_unit_read_is_observation_failed_never_inactive(fx, layout, kind):
    fx.activate()
    events = Events()
    units = FakeUnits(events, error=True)
    units.kind = kind
    out, _ = run_cl(layout, fx, events=events, services=FakeServices(events, units=units))
    assert out.terminal is Terminal.HARD_STOP and out.failure == "observation-failed"
    assert record(layout, 1)["st1"]["checks"]["capture-unit-not-active"] is False


@pytest.mark.parametrize(
    "outcome,reason", [(PkOutcome.UNCONFIRMED, "still-authorized"), (PkOutcome.UNCONFIRMED, "only-errors")]
)
def test_an_unconfirmed_series_is_never_st1(fx, layout, outcome, reason):
    fx.activate(grant_id=False)
    events = Events()
    pk = FakePk(events, outcome, reason)
    out, _ = run_cl(layout, fx, events=events, services=FakeServices(events, pk=pk))
    assert out.terminal is Terminal.HARD_STOP and out.rule_class == "removed-unconfirmed"
    doc = record(layout, 1)
    assert doc["pk"]["outcome"] == "unconfirmed" and doc["pk"]["reason"] == reason


def test_an_authorized_series_after_cleanup_is_hard_stop(fx, layout):
    fx.activate()
    events = Events()
    out, _ = run_cl(layout, fx, events=events, services=FakeServices(events, pk=FakePk(events, PkOutcome.AUTHORIZED)))
    assert out.terminal is Terminal.HARD_STOP and out.failure == "grant-unconfirmed"


def test_a_baseline_difference_is_reported_by_key_path_only(fx, layout):
    fx.activate()
    changed = _baseline()
    changed["packages"] = [["systemd", "261", "amd64"]]
    events = Events()
    out, _ = run_cl(layout, fx, events=events, services=FakeServices(events, baseline=changed))
    doc = record(layout, 1)
    assert out.terminal is Terminal.HARD_STOP
    assert doc["st1"]["first_difference"] == "baseline.packages[0][1]"
    assert "261" not in json.dumps(doc["st1"])


def test_an_unavailable_baseline_never_verifies(fx, layout):
    fx.activate()
    events = Events()
    out, _ = run_cl(layout, fx, events=events, services=FakeServices(events, baseline=None))
    assert out.terminal is Terminal.HARD_STOP
    assert record(layout, 1)["st1"]["checks"]["baseline-equal"] is False


# ---------------------------------------------------------------------------
# interruption and recovery at L0 … L9 (IM-L)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "crash,point",
    [
        ("unlink:50-freedom-blades-rp11.rules", "L0"),
        ("removed:50-freedom-blades-rp11.rules", "L1"),
        ("after-attempt-dir", "L2"),
        ("read-journal:" + f"{ACT_ID}-act-evidence", "L3"),
        ("unlink:pass-a.json", "L5"),
        ("removed:pass-a.json", "L5"),
        ("removed:freedom-blades-rp11", "L6"),
        ("removed:grant.id", "L6"),
    ],
)
def test_an_interrupted_attempt_is_recovered_by_the_next_one(fx, layout, crash, point):
    """IM-L: a death at each point leaves a state the next attempt classes and finishes."""
    fx.activate()
    proc, _ = procedure(layout, fx, crash=crash)
    with pytest.raises(Crash):
        proc.run()
    out, _ = run_cl(layout, fx)
    assert out.terminal is Terminal.ST1_VERIFIED, (point, out)
    p = paths(layout)
    for path in (p.rule, p.pass_config, p.tree_p, p.grant_id, p.lock_dir):
        assert not os.path.lexists(path), (point, path)


def test_an_interruption_in_the_polkit_series_l4_is_recovered(fx, layout):
    fx.activate()

    class DyingPk(FakePk):
        def run(self, *a):
            raise Crash("L4")

    events = Events()
    proc, _ = procedure(layout, fx, events=events, services=FakeServices(events, pk=DyingPk(events)))
    with pytest.raises(Crash):
        proc.run()
    assert run_cl(layout, fx)[0].terminal is Terminal.ST1_VERIFIED


def test_an_interruption_in_verification_l7_and_publication_l8_is_recovered(fx, layout):
    fx.activate()

    class DyingBaseline(FakeBaseline):
        def recompute(self):
            raise Crash("L7")

    events = Events()
    services = FakeServices(events)
    services._baseline = DyingBaseline(events, None)
    proc, _ = procedure(layout, fx, events=events, services=services)
    with pytest.raises(Crash):
        proc.run()
    out, _ = run_cl(layout, fx)
    assert out.terminal is Terminal.ST1_VERIFIED and out.k == 2
    assert "run-end" not in ops(layout, 1) and "run-end" in ops(layout, 2)


def test_after_l9_a_repeat_only_adds_a_record(fx, layout):
    fx.activate()
    assert run_cl(layout, fx)[0].terminal is Terminal.ST1_VERIFIED
    assert run_cl(layout, fx)[0].terminal is Terminal.ST1_VERIFIED
    names = sorted(os.listdir(Path(layout.store, "activation")))
    assert names == [f"{ACT_ID}.act.json", f"{ACT_ID}.deact-1.json", f"{ACT_ID}.deact-2.json"]


# ---------------------------------------------------------------------------
# evidence failures: GP-R3 (E-a, E-b, E-c) and record publication
# ---------------------------------------------------------------------------


def test_e_a_unwritable_evidence_parent_still_clears_attributable_objects(fx, layout):
    """GP-R3 E-a: no attempt directory; A1-intact objects removed, nothing claimed."""
    fx.activate(grant_id=False)
    os.chmod(layout.var_tmp, 0o555)
    try:
        out, _ = run_cl(layout, fx)
    finally:
        os.chmod(layout.var_tmp, 0o755)
    assert out.terminal is Terminal.EVIDENCE_UNWRITABLE and out.terminal.exit_code == 4
    assert out.diagnostic(ACT_ID).startswith(f"rp11-cl grant-priority {ACT_ID} rule=removed-unconfirmed pk=")
    p = paths(layout)
    assert not os.path.lexists(p.rule) and not os.path.lexists(p.pass_config)
    assert not list(Path(layout.store, "activation").iterdir())
    assert out.rule_class == "removed-unconfirmed"


@pytest.mark.parametrize(
    "io,entry",
    [
        (lambda: FailingIO(fail_write_at=1), "E-b run-start short write"),
        (lambda: FailingIO(fail_fsync_at=4), "E-b run-start flush"),
        (lambda: FailingIO(fail_write_at=4), "E-b remove-intent short write"),
        (lambda: FailingIO(fail_fsync_at=9), "E-c a later flush"),
    ],
)
def test_journal_short_write_or_failed_flush_enters_grant_priority_mode(fx, layout, io, entry):
    fx.activate(grant_id=False)
    failing = io()
    out, _ = run_cl(layout, fx, io=failing)
    assert out.terminal is Terminal.EVIDENCE_UNWRITABLE, entry
    p = paths(layout)
    assert not os.path.lexists(p.rule), entry
    assert not list(Path(layout.store, "activation").iterdir()), entry
    # the next attempt classes what GP removed and never claims "removed" for it
    out2, _ = run_cl(layout, fx)
    assert out2.terminal is Terminal.ST1_VERIFIED, entry
    assert record(layout, 2)["active_rule"]["class"] in {"absent-before-removal", "removed-earlier"}


def test_no_line_follows_a_failed_append(fx, layout):
    fx.activate(grant_id=False)
    failing = FailingIO(fail_write_at=3)
    run_cl(layout, fx, io=failing)
    data = Path(layout.var_tmp, f"{ACT_ID}-deact-1-evidence/journal").read_bytes()
    assert data.count(b"\n") == 2 and not data.endswith(b"\n")  # two lines, then the torn third


def test_a_record_collision_is_record_unpublished_and_the_next_attempt_records(fx, layout):
    fx.activate()
    Path(layout.store, "activation").mkdir(exist_ok=True)
    squat = Path(layout.store, f"activation/{ACT_ID}.deact-1.json")
    squat.write_text("{}\n")
    os.chmod(squat, 0o444)
    out, _ = run_cl(layout, fx)
    assert out.terminal is Terminal.RECORD_UNPUBLISHED and out.terminal.exit_code == 3
    assert squat.read_text() == "{}\n"  # never replaced
    assert not os.path.lexists(paths(layout).rule)  # removals stay durable
    out2, _ = run_cl(layout, fx)
    assert out2.terminal is Terminal.ST1_VERIFIED and record(layout, 2)["outcome"] == "st1-verified"


def test_a_failed_record_flush_is_record_unpublished(fx, layout):
    fx.activate()
    out, _ = run_cl(layout, fx, record_io=FailingIO(fail_fsync_at=1))
    assert out.terminal is Terminal.RECORD_UNPUBLISHED
    assert not Path(layout.store, f"activation/{ACT_ID}.deact-1.json").exists()


def _act_path(layout) -> Path:
    return Path(layout.store, f"activation/{ACT_ID}.act.json")


def test_an_existing_valid_act_record_is_preserved_and_its_digest_linked(fx, layout):
    """CL-7: the immutable ACT record this activation already has is linked as it is."""
    fx.activate()
    assert run_cl(layout, fx)[0].terminal is Terminal.ST1_VERIFIED  # publishes the one failed ACT record
    kept = _act_path(layout).read_bytes()
    out, _ = run_cl(layout, fx)
    assert out.terminal is Terminal.ST1_VERIFIED and out.k == 2
    assert _act_path(layout).read_bytes() == kept
    assert record(layout, 2)["act_record_sha256"] == hashlib.sha256(kept).hexdigest()
    assert record(layout, 1)["act_record_sha256"] == record(layout, 2)["act_record_sha256"]


def _other_activation(act: bytes, deact: bytes) -> bytes:
    return act.replace(ACT_ID.encode(), b"rp11-act-20261013T101500Z-ffffffff")


def _other_a2(act: bytes, deact: bytes) -> bytes:
    doc = parse_canonical(act)
    other = "f" * 64
    doc["authority"] = {"a2_path": doc["authority"]["a2_path"].replace(doc["authority"]["a2_sha256"], other),
                        "a2_sha256": other}
    return canonical_bytes(doc)


def _with(**changes):
    def build(act: bytes, deact: bytes) -> bytes:
        return canonical_bytes({**parse_canonical(act), **changes})

    return build


BAD_ACT_RECORDS = {
    "the-old-kept-fixture": lambda act, deact: b'{"kept":true}\n',
    "empty-object": lambda act, deact: b"{}\n",
    "non-canonical": lambda act, deact: json.dumps(parse_canonical(act), indent=1).encode() + b"\n",
    "truncated": lambda act, deact: act[: len(act) // 2],
    "no-final-lf": lambda act, deact: act[:-1],
    "not-json": lambda act, deact: b"rp11\n",
    "schema-invalid": _with(trigger="nowhere"),
    "missing-nested-field": lambda act, deact: canonical_bytes(
        {**parse_canonical(act), "pk": {k: v for k, v in parse_canonical(act)["pk"].items() if k != "calls"}}
    ),
    "wrong-kind-a-deactivation-record": lambda act, deact: deact,
    "wrong-activation": _other_activation,
    "other-a2": _other_a2,
    "nonzero-attempt": _with(attempt=1),
    "outcome-of-the-other-kind": _with(outcome="hard-stop"),
    "activated-without-its-facts": _with(outcome="activated", failure="absent", trigger="act"),
}


@pytest.mark.parametrize("case", sorted(BAD_ACT_RECORDS))
def test_an_invalid_existing_act_record_is_never_rewritten_and_never_chained(fx, layout, case):
    """CL-7 fails closed as ``record-unpublished``: the colliding object stays as it
    is and no deactivation record (least of all ``st1-verified``) names its digest."""
    fx.activate()
    assert run_cl(layout, fx)[0].terminal is Terminal.ST1_VERIFIED
    act_bytes, deact_bytes = _act_path(layout).read_bytes(), Path(layout.store, f"activation/{ACT_ID}.deact-1.json").read_bytes()
    bad = BAD_ACT_RECORDS[case](act_bytes, deact_bytes)
    assert bad != act_bytes
    _act_path(layout).unlink()
    _act_path(layout).write_bytes(bad)
    os.chmod(_act_path(layout), 0o444)
    names = sorted(os.listdir(Path(layout.store, "activation")))
    out, _ = run_cl(layout, fx)
    assert out.terminal is Terminal.RECORD_UNPUBLISHED and out.terminal.exit_code == 3 and out.failure == "record-unpublished"
    assert _act_path(layout).read_bytes() == bad
    assert sorted(os.listdir(Path(layout.store, "activation"))) == names  # no deact-2, no rewrite
    assert not Path(layout.store, f"activation/{ACT_ID}.deact-2.json").exists()
    assert ops(layout, 2)[-1] == "run-end"
    assert attempt_journal(layout, 2)[-1]["outcome"] == "record-unpublished"


@pytest.mark.parametrize("mode", [0o644, 0o666])
def test_an_act_record_the_store_will_not_read_back_is_never_rewritten(fx, layout, mode):
    fx.activate()
    assert run_cl(layout, fx)[0].terminal is Terminal.ST1_VERIFIED
    kept = _act_path(layout).read_bytes()
    os.chmod(_act_path(layout), mode)
    names = sorted(os.listdir(Path(layout.store, "activation")))
    out, _ = run_cl(layout, fx)
    assert out.terminal is Terminal.RECORD_UNPUBLISHED
    assert _act_path(layout).read_bytes() == kept and sorted(os.listdir(Path(layout.store, "activation"))) == names


def test_an_absent_act_record_is_published_once_as_a_valid_failed_record(fx, layout):
    fx.activate()
    assert not _act_path(layout).exists()
    out, _ = run_cl(layout, fx)
    assert out.terminal is Terminal.ST1_VERIFIED
    act = parse_canonical(_act_path(layout).read_bytes())
    validate_record(act)
    assert (act["kind"], act["attempt"], act["outcome"]) == ("act", 0, "failed")
    assert act["failure"] == {"step": "CL-7", "class": "act-unconfirmed"} and act["act_record_sha256"] == "absent"
    assert stat.S_IMODE(_act_path(layout).stat().st_mode) == 0o444
    assert record(layout, 1)["act_record_sha256"] == hashlib.sha256(_act_path(layout).read_bytes()).hexdigest()


def test_records_are_root_only_0444_and_validate(fx, layout):
    fx.activate()
    run_cl(layout, fx)
    for name in os.listdir(Path(layout.store, "activation")):
        info = os.lstat(Path(layout.store, "activation", name))
        assert stat.S_IMODE(info.st_mode) == 0o444 and info.st_nlink == 1
        validate_record(parse_canonical(Path(layout.store, "activation", name).read_bytes()))


# ---------------------------------------------------------------------------
# diagnostics and the composition root
# ---------------------------------------------------------------------------


def test_the_diagnostic_line_is_fixed_and_carries_no_values(fx, layout):
    fx.activate()
    out, _ = run_cl(layout, fx)
    line = out.diagnostic(ACT_ID)
    assert re.fullmatch(
        rf"rp11-cl st1-verified {ACT_ID} k=1 rule=[a-z-]+ pk=[a-z-]+ pass_config=[a-z-]+ "
        r"dirs=[a-z,-]+ failure=[a-z-]+",
        line,
    )
    assert layout.run not in line and len(line) < 400


def test_an_unexpected_exception_exits_70_with_a_fixed_line_and_no_traceback(monkeypatch, capsys, layout):
    def boom(*a, **k):
        raise ValueError("secret-content /etc/shadow")

    monkeypatch.setattr("adapters.rp11.stop_post.build_procedure", boom)
    assert run_stop_post(ACT_ID, "a" * 64, invocation_id="absent", parent_pid=1, layout=layout, connector=lambda: None) == 70
    err = capsys.readouterr().err
    assert err == f"rp11-cl internal-error {ACT_ID} ValueError\n"


def test_the_composition_root_runs_the_real_adapters(fx, layout, capsys):
    fx.activate()
    events = Events()
    proc = build_procedure(
        ACT_ID, fx.a2_sha256, invocation_id="absent", parent_pid=1, layout=layout,
        services=FakeServices(events), clock=FakeClock(),
    )
    out = proc.run()
    assert out.terminal is Terminal.ST1_VERIFIED


def test_the_attempt_directory_and_journal_modes(fx, layout):
    fx.activate()
    run_cl(layout, fx)
    d = Path(layout.var_tmp, f"{ACT_ID}-deact-1-evidence")
    assert stat.S_IMODE(d.stat().st_mode) == 0o755
    assert stat.S_IMODE((d / "journal").stat().st_mode) == 0o644


def test_nothing_in_a_runtime_path_imports_the_role_engine():
    pattern = re.compile(r"(application\.rp11|adapters\.rp11)")
    offenders = []
    for base in ("main.py", "config.py", "ext", "models", "helpers", "connectors", "adapters/web",
                 "adapters/http", "adapters/worker", "application/web", "application/worker", "tools"):
        target = ROOT / base
        files = [target] if target.is_file() else list(target.rglob("*.py"))
        offenders += [str(f.relative_to(ROOT)) for f in files if pattern.search(f.read_text())]
    assert offenders == []


# ---------------------------------------------------------------------------
# no dynamic subprocess, shell or distribution executable (BQ-4, H-FI.7)
# ---------------------------------------------------------------------------

_FORBIDDEN_CALLS = {
    "system", "popen", "execv", "execve", "execvp", "execvpe", "execl", "execle", "execlp",
    "execlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe", "spawnl", "spawnle", "posix_spawn",
    "posix_spawnp", "forkpty",
}
_FORBIDDEN_MODULES = {"subprocess", "pty", "multiprocessing", "concurrent", "asyncio", "shlex"}
_FORBIDDEN_TEXT = re.compile(r"/usr/bin/(systemctl|pkcheck|sleep|sh|bash|env)\b|systemd-run")


def _artifact_runtime_modules() -> list[Path]:
    sys.path.insert(0, str(ROOT / "infra/rp11-h1"))
    import importlib.util

    spec = importlib.util.spec_from_file_location("rp11_build_for_guard", ROOT / "infra/rp11-h1/build.py")
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    return [ROOT / s for s in build.SOURCES] + [ROOT / "infra/rp11-h1/rp11_h1.py", ROOT / "infra/rp11-h1/rp11_roles.py"]


def test_no_artifact_module_starts_a_dynamic_program_or_a_shell():
    import ast

    forks = []
    for path in _artifact_runtime_modules():
        source = path.read_text()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names] + ([node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
                assert not {n.split(".")[0] for n in names} & _FORBIDDEN_MODULES, (path, names)
            if isinstance(node, ast.Attribute) and node.attr in _FORBIDDEN_CALLS:
                pytest.fail(f"{path.relative_to(ROOT)} uses {node.attr}")
            if isinstance(node, ast.Attribute) and node.attr == "fork":
                forks.append(str(path.relative_to(ROOT)))
        assert not _FORBIDDEN_TEXT.search(source.replace("/usr/bin/python3.14", "")), path
    # the single process-creation function: the DI-6 subject (H-PROC.6)
    assert forks == ["adapters/rp11/process.py"]


# ---------------------------------------------------------------------------
# GRR remediation: a failed target inspection is a typed non-removal at the
# concrete adapter (H-GR1.2, H-GRR.4 … H-GRR.5, H-CL.G.1 … H-CL.G.2)
# ---------------------------------------------------------------------------

# fault → (Removal attribution, GRR class). A failed content read, attribute listing,
# ``fstat`` or fallback observation establishes neither damage nor another object:
# the grant may still be the intact, authorizing rule, so it is ``UNINSPECTED``
# (kept, never removed, and a recovery owner must remain).
GRR_FAULTS = [
    ("read", Attribution.UNINSPECTED, GrrOutcome.KEPT_UNINSPECTED),
    ("listxattr", Attribution.UNINSPECTED, GrrOutcome.KEPT_UNINSPECTED),
    ("fstat", Attribution.UNINSPECTED, GrrOutcome.KEPT_UNINSPECTED),
    ("fallback", Attribution.UNINSPECTED, GrrOutcome.KEPT_UNINSPECTED),
]
RULE_CLASS_FOR = {
    GrrOutcome.KEPT_DAMAGED: "present-damaged-unremoved",
    GrrOutcome.KEPT_FOREIGN: "present-foreign-unremoved",
    GrrOutcome.KEPT_UNINSPECTED: "present-uninspected-unremoved",
}


def _rule_target(tmp_path: Path) -> tuple[str, Identity]:
    rules = tmp_path / "rules.d"
    rules.mkdir(mode=0o755)
    path = rules / "50-x.rules"
    data = b"// synthetic rule\n"
    path.write_bytes(data)
    os.chmod(path, 0o644)
    info = os.stat(path)
    return str(path), Identity(
        str(path), ObjectKind.FILE, info.st_dev, info.st_ino, 0o644, hashlib.sha256(data).hexdigest(), len(data)
    )


def _dir_target(tmp_path: Path) -> tuple[str, Identity]:
    path = tmp_path / "tree"
    path.mkdir(mode=0o700)
    os.chmod(path, 0o700)
    info = os.stat(path)
    return str(path), Identity(str(path), ObjectKind.DIR, info.st_dev, info.st_ino, 0o700)


def _owner() -> Owner:
    return Owner(os.getuid(), os.getgid())


def _unchanged(path: str, identity: Identity) -> bool:
    info = os.lstat(path)
    return (info.st_dev, info.st_ino, stat.S_IMODE(info.st_mode)) == (identity.dev, identity.ino, identity.mode)


@pytest.mark.parametrize("call,attribution,grr", GRR_FAULTS)
def test_a_failed_target_inspection_is_a_typed_non_removal(tmp_path, monkeypatch, call, attribution, grr):
    path, identity = _rule_target(tmp_path)
    fault = InspectionFault(monkeypatch, path, call)
    seen: list = []
    removal = LocalActivationFs(_owner()).remove(path, identity, directory=False, before_unlink=seen.append)
    assert fault.hits >= 1
    assert (removal.outcome, removal.attribution) == (RemovalOutcome.MISMATCH, attribution)
    assert grr_outcome(removal) == (grr, 0)
    assert seen == [] and _unchanged(path, identity)
    if call in ("fstat", "fallback"):
        assert removal.observed == UNREACHABLE
    else:
        assert (removal.observed.dev, removal.observed.ino) == (identity.dev, identity.ino)
        assert removal.observed.sha256 is None if call == "read" else removal.observed.xattr_names == ("unlistable",)


@pytest.mark.parametrize("call,attribution", [("listdir", Attribution.A1_DAMAGED), ("fstat", Attribution.A0),
                                              ("listxattr", Attribution.A1_DAMAGED), ("fallback", Attribution.A0)])
def test_a_failed_directory_inspection_keeps_the_directory(tmp_path, monkeypatch, call, attribution):
    path, identity = _dir_target(tmp_path)
    fault = InspectionFault(monkeypatch, path, call)
    seen: list = []
    removal = LocalActivationFs(_owner()).remove(path, identity, directory=True, before_unlink=seen.append)
    assert fault.hits >= 1
    assert (removal.outcome, removal.attribution) == (RemovalOutcome.MISMATCH, attribution)
    assert seen == [] and os.path.isdir(path) and _unchanged(path, identity)
    if call == "listdir":
        assert removal.observed.empty is None


@pytest.mark.parametrize("call", ["read", "fstat", "listxattr", "fallback"])
def test_observe_never_raises_for_a_failed_inspection(tmp_path, monkeypatch, call):
    path, identity = _rule_target(tmp_path)
    fault = InspectionFault(monkeypatch, path, call)
    observed = LocalActivationFs(_owner()).observe(path)
    assert fault.hits >= 1 and observed is not None
    if call == "listxattr":
        assert observed.xattr_names == ("unlistable",)  # never A1-intact at removal (above)
    else:
        assert observed.sha256 is None and classify(identity, observed, _owner()) is not Attribution.A1_INTACT


@pytest.mark.parametrize("call", ["read", "fstat"])
def test_a_failed_grant_id_read_is_identity_unavailable(tmp_path, monkeypatch, call):
    path, _ = _rule_target(tmp_path)
    os.chmod(path, 0o600)
    fault = InspectionFault(monkeypatch, path, call)
    assert LocalActivationFs(_owner()).read_root_file(path, max_bytes=4_096, mode=0o600) is None
    assert fault.hits >= 1
    fault.active = False
    assert LocalActivationFs(_owner()).read_root_file(path, max_bytes=4_096, mode=0o600) is not None


def test_the_unfaulted_adapter_still_removes_both_kinds(tmp_path, monkeypatch):
    fs = LocalActivationFs(_owner())
    path, identity = _rule_target(tmp_path)
    fault = InspectionFault(monkeypatch, path, "read", active=False)
    seen: list = []
    removal = fs.remove(path, identity, directory=False, before_unlink=seen.append)
    assert (removal.outcome, removal.attribution) == (RemovalOutcome.REMOVED, Attribution.A1_INTACT)
    assert grr_outcome(removal) == (GrrOutcome.REMOVED, 0) and len(seen) == 1 and not os.path.lexists(path)
    assert fault.hits == 0
    d, d_identity = _dir_target(tmp_path)
    assert fs.remove(d, d_identity, directory=True, before_unlink=seen.append).outcome is RemovalOutcome.REMOVED


def _replace_same_bytes(path: str) -> None:
    fresh = path + ".new"
    Path(fresh).write_bytes(Path(path).read_bytes())
    os.chmod(fresh, 0o644)
    os.rename(fresh, path)


@pytest.mark.parametrize(
    "case,outcome,attribution,grr,present",
    [
        ("absent", RemovalOutcome.ABSENT, None, (GrrOutcome.ABSENT, 0), False),
        ("parent-absent", RemovalOutcome.ABSENT, None, (GrrOutcome.ABSENT, 0), False),
        ("damaged", RemovalOutcome.MISMATCH, Attribution.A1_DAMAGED, (GrrOutcome.KEPT_DAMAGED, 0), True),
        ("foreign", RemovalOutcome.MISMATCH, Attribution.A0, (GrrOutcome.KEPT_FOREIGN, 0), True),
        ("unremovable", RemovalOutcome.UNREMOVABLE, Attribution.A1_INTACT, (GrrOutcome.UNREMOVABLE, 13), True),
        ("parent-flush-fails", RemovalOutcome.REMOVED, Attribution.A1_INTACT, (GrrOutcome.REMOVED, 0), False),
    ],
)
def test_the_accepted_removal_outcomes_are_unchanged(tmp_path, monkeypatch, case, outcome, attribution, grr, present):
    path, identity = _rule_target(tmp_path)
    parent = os.path.dirname(path)
    if case == "absent":
        os.unlink(path)
    elif case == "parent-absent":
        os.unlink(path)
        os.rmdir(parent)
    elif case == "damaged":
        os.chmod(path, 0o664)
    elif case == "foreign":
        _replace_same_bytes(path)
    elif case == "unremovable":
        os.chmod(parent, 0o555)
    else:
        real_fsync = os.fsync

        def fsync(fd):
            if os.readlink(f"/proc/self/fd/{fd}") == os.path.realpath(parent):
                raise OSError(5, "EIO")
            return real_fsync(fd)

        monkeypatch.setattr(os, "fsync", fsync)
    try:
        removal = LocalActivationFs(_owner()).remove(path, identity, directory=False, before_unlink=lambda _o: None)
    finally:
        if os.path.isdir(parent):
            os.chmod(parent, 0o755)
    assert (removal.outcome, removal.attribution) == (outcome, attribution)
    assert grr_outcome(removal) == grr and os.path.lexists(path) == present


@pytest.mark.parametrize("call", ["read", "listxattr", "fstat", "fallback"])
def test_an_uninspected_grant_is_neither_damaged_nor_foreign_nor_removable(tmp_path, monkeypatch, call):
    path, identity = _rule_target(tmp_path)
    InspectionFault(monkeypatch, path, call)
    seen: list = []
    removal = LocalActivationFs(_owner()).remove(path, identity, directory=False, before_unlink=seen.append)
    assert removal.attribution is Attribution.UNINSPECTED
    assert removal.attribution not in (Attribution.A1_DAMAGED, Attribution.A0, Attribution.A1_INTACT)
    assert grr_outcome(removal) == (GrrOutcome.KEPT_UNINSPECTED, 0) and seen == [] and _unchanged(path, identity)


def test_a_symlinked_parent_leaves_the_grant_uninspected_not_foreign(tmp_path):
    """The no-follow resolution cannot reach the object: nothing is established."""
    path, identity = _rule_target(tmp_path)
    parent = os.path.dirname(path)
    os.rename(parent, parent + ".real")
    os.symlink(parent + ".real", parent)
    seen: list = []
    removal = LocalActivationFs(_owner()).remove(path, identity, directory=False, before_unlink=seen.append)
    assert (removal.outcome, removal.attribution) == (RemovalOutcome.MISMATCH, Attribution.UNINSPECTED)
    assert seen == [] and LocalActivationFs(_owner()).observe(path) == UNREACHABLE
    assert os.path.exists(parent + ".real/50-x.rules")


def _cf_observed(identity: Identity, **changes) -> Observed:
    base = dict(kind=ObjectKind.FILE, dev=identity.dev, ino=identity.ino, uid=os.getuid(), gid=os.getgid(),
                mode=identity.mode, nlink=1, size=identity.size, sha256=identity.sha256, xattr_names=())
    return Observed(**{**base, **changes})


CF_IDENT = Identity("/x", ObjectKind.FILE, 7, 9, 0o644, "a" * 64, 12)


@pytest.mark.parametrize(
    "changes,expected",
    [
        ({}, Attribution.A1_INTACT),
        ({"sha256": None}, Attribution.UNINSPECTED),
        ({"xattr_names": ("unlistable",)}, Attribution.UNINSPECTED),
        ({"sha256": None, "xattr_names": ("unlistable",)}, Attribution.UNINSPECTED),
        # a failed read does not hide a fact that was established
        ({"sha256": None, "mode": 0o664}, Attribution.A1_DAMAGED),
        ({"sha256": None, "size": 13}, Attribution.A1_DAMAGED),
        ({"sha256": None, "nlink": 2}, Attribution.A1_DAMAGED),
        ({"sha256": None, "uid": os.getuid() + 1}, Attribution.A1_DAMAGED),
        ({"sha256": None, "xattr_names": ("security.capability",)}, Attribution.A1_DAMAGED),
        ({"sha256": "b" * 64}, Attribution.A1_DAMAGED),
        ({"xattr_names": ("system.posix_acl_access",)}, Attribution.A1_DAMAGED),
        # another object is positively another object, readable or not
        ({"ino": 10}, Attribution.A0),
        ({"ino": 10, "sha256": None}, Attribution.A0),
        ({"kind": ObjectKind.DIR, "sha256": None}, Attribution.A0),
    ],
)
def test_classify_file_names_only_what_the_observation_establishes(changes, expected):
    assert classify_file(CF_IDENT, _cf_observed(CF_IDENT, **changes), Owner(os.getuid(), os.getgid())) is expected


def test_classify_file_never_attributes_without_an_identity_or_an_observation():
    assert classify_file(None, _cf_observed(CF_IDENT, sha256=None), Owner(os.getuid(), os.getgid())) is Attribution.A0
    assert classify_file(CF_IDENT, None, Owner(os.getuid(), os.getgid())) is Attribution.ABSENT
    assert classify_file(CF_IDENT, UNREACHABLE, Owner(os.getuid(), os.getgid())) is Attribution.UNINSPECTED


def test_without_grant_id_an_uninspected_rule_is_kept_and_recovered_later(fx, layout, monkeypatch):
    """CL-3 (G-R1): the journal identity is not enough to remove an object whose
    inspection failed; the class is the uninspected one and a later attempt removes it."""
    fx.activate(grant_id=False)
    p = paths(layout)
    info = os.stat(p.rule)
    fault = InspectionFault(monkeypatch, p.rule, "read")
    out, _ = run_cl(layout, fx)
    assert fault.hits >= 1 and out.terminal is Terminal.HARD_STOP
    assert out.rule_class == "present-uninspected-unremoved"
    fault.active = False
    assert os.lstat(p.rule).st_ino == info.st_ino
    assert not [line for line in attempt_journal(layout, 1) if line.get("path") == p.rule and line["op"].startswith("remove")]
    assert record(layout, 1)["grant_identity"]["cl_g"] == "identity-unavailable"
    again, _ = run_cl(layout, fx)
    assert again.terminal is Terminal.ST1_VERIFIED and not os.path.lexists(p.rule)


def test_a_failing_write_ahead_propagates_and_nothing_is_unlinked(tmp_path):
    """G-R1: ``before_unlink`` failures are not inspection failures; they reach
    the caller's GP-R3 handling untranslated and the object stays."""
    path, identity = _rule_target(tmp_path)

    def write_ahead(_observed):
        raise EvidenceWriteError("journal no longer accepts lines")

    with pytest.raises(EvidenceWriteError):
        LocalActivationFs(_owner()).remove(path, identity, directory=False, before_unlink=write_ahead)
    assert _unchanged(path, identity)


def test_a_failed_remove_intent_still_enters_grant_priority_not_a_kept_class(fx, layout):
    """The cleanup's write-ahead failure keeps its GP-R3 meaning (H-GR1.3)."""
    fx.activate(grant_id=False)
    out, _ = run_cl(layout, fx, io=FailingIO(fail_write_at=4))  # the rule's remove-intent
    assert out.terminal is Terminal.EVIDENCE_UNWRITABLE
    assert out.rule_class == "removed-unconfirmed" and not os.path.lexists(paths(layout).rule)


@pytest.mark.parametrize("call,_attribution,grr", GRR_FAULTS)
def test_stop_post_cl_g_survives_a_persistent_grant_inspection_failure(fx, layout, monkeypatch, call, _attribution, grr):
    """RT3.CLG: CL-G returns a closed outcome, CL-0 … CL-7 still run, the grant is
    kept, the record is a hard stop with the rule as a residual; once the
    failure clears, the next attempt removes the grant and verifies."""
    fx.activate()
    p = paths(layout)
    info = os.stat(p.rule)
    fault = InspectionFault(monkeypatch, p.rule, call)
    out, _ = run_cl(layout, fx)
    assert fault.hits >= 1
    rule_class = RULE_CLASS_FOR[grr]
    assert out.terminal is Terminal.HARD_STOP and out.rule_class == rule_class, out.diagnostic(ACT_ID)
    fault.active = False
    assert os.lstat(p.rule).st_ino == info.st_ino and Path(p.rule).read_bytes() == fx.rule_bytes
    doc = record(layout, 1)
    assert doc["outcome"] == "hard-stop" and not doc["st1"]["verified"]
    assert doc["grant_identity"]["cl_g"] == grr.value and doc["active_rule"]["class"] == rule_class
    assert doc["release"]["first_rung"] == "absent"
    assert any(r["path"] == p.rule and r["class"] == rule_class for r in doc["residual"])
    journal = attempt_journal(layout, 1)
    assert [line["op"] for line in journal[:2]] == ["run-start", "cl-g"] and journal[-1]["op"] == "run-end"
    assert journal[1]["outcome"] == grr.value
    assert not os.path.lexists(p.pass_config)  # CL-5 ran
    out2, _ = run_cl(layout, fx)
    assert out2.terminal is Terminal.ST1_VERIFIED, out2.diagnostic(ACT_ID)
    assert not os.path.lexists(p.rule)


# ---------------------------------------------------------------------------
# GRR remediation: descriptor cleanup never raises and never overrides the typed
# result (H-GRR.5, H-GRR.8, RT2.IGR.2); one close, never retried
# ---------------------------------------------------------------------------

CLOSE_CASES = [(role, shape) for role in CloseFault.ROLES for shape in CloseFault.SHAPES]


@pytest.mark.parametrize("role,shape", CLOSE_CASES)
def test_a_close_error_after_reverification_keeps_the_removal(tmp_path, close_fault, role, shape):
    path, identity = _rule_target(tmp_path)
    fault = close_fault(path, role, shape)
    seen: list = []
    removal = LocalActivationFs(_owner()).remove(path, identity, directory=False, before_unlink=seen.append)
    assert fault.hits >= 1 and fault.never_retried()
    assert (removal.outcome, removal.attribution) == (RemovalOutcome.REMOVED, Attribution.A1_INTACT)
    assert grr_outcome(removal) == (GrrOutcome.REMOVED, 0) and len(seen) == 1 and not os.path.lexists(path)


@pytest.mark.parametrize("role,shape", CLOSE_CASES)
def test_a_close_error_after_a_directory_reverification_keeps_the_removal(tmp_path, close_fault, role, shape):
    path, identity = _dir_target(tmp_path)
    fault = close_fault(path, role, shape)
    removal = LocalActivationFs(_owner()).remove(path, identity, directory=True, before_unlink=lambda _o: None)
    assert fault.hits >= 1 and fault.never_retried()
    assert removal.outcome is RemovalOutcome.REMOVED and not os.path.lexists(path)


@pytest.mark.parametrize("role,shape", CLOSE_CASES)
@pytest.mark.parametrize("case", ["damaged", "foreign"])
def test_a_close_error_after_a_mismatch_keeps_the_mismatch_and_the_object(tmp_path, close_fault, role, shape, case):
    path, identity = _rule_target(tmp_path)
    if case == "damaged":
        os.chmod(path, 0o664)
    else:
        _replace_same_bytes(path)
    ino = os.lstat(path).st_ino
    fault = close_fault(path, role, shape)
    seen: list = []
    removal = LocalActivationFs(_owner()).remove(path, identity, directory=False, before_unlink=seen.append)
    assert fault.hits >= 1 and fault.never_retried()
    attribution = Attribution.A1_DAMAGED if case == "damaged" else Attribution.A0
    assert (removal.outcome, removal.attribution) == (RemovalOutcome.MISMATCH, attribution)
    assert seen == [] and os.lstat(path).st_ino == ino


@pytest.mark.parametrize("shape", CloseFault.SHAPES)
@pytest.mark.parametrize(
    "case,outcome,grr,present",
    [
        ("absent", RemovalOutcome.ABSENT, (GrrOutcome.ABSENT, 0), False),
        ("mismatch", RemovalOutcome.MISMATCH, (GrrOutcome.KEPT_DAMAGED, 0), True),
        ("unremovable", RemovalOutcome.UNREMOVABLE, (GrrOutcome.UNREMOVABLE, 13), True),
        ("removed", RemovalOutcome.REMOVED, (GrrOutcome.REMOVED, 0), False),
    ],
)
def test_a_parent_close_error_preserves_each_terminal_result(tmp_path, close_fault, shape, case, outcome, grr, present):
    path, identity = _rule_target(tmp_path)
    parent = os.path.dirname(path)
    if case == "absent":
        os.unlink(path)
    elif case == "mismatch":
        os.chmod(path, 0o664)
    elif case == "unremovable":
        os.chmod(parent, 0o555)
    fault = close_fault(path, "parent", shape)
    try:
        removal = LocalActivationFs(_owner()).remove(path, identity, directory=False, before_unlink=lambda _o: None)
    finally:
        os.chmod(parent, 0o755)
    assert fault.hits >= 1 and fault.never_retried()
    assert removal.outcome is outcome and grr_outcome(removal) == grr and os.path.lexists(path) == present


def test_a_write_ahead_failure_still_propagates_through_a_close_error(tmp_path, close_fault):
    path, identity = _rule_target(tmp_path)
    fault = close_fault(path, "target")

    def write_ahead(_observed):
        raise EvidenceWriteError("journal no longer accepts lines")

    with pytest.raises(EvidenceWriteError):
        LocalActivationFs(_owner()).remove(path, identity, directory=False, before_unlink=write_ahead)
    assert fault.hits >= 1 and fault.never_retried() and _unchanged(path, identity)


@pytest.mark.parametrize("role,shape", CLOSE_CASES)
def test_observe_never_raises_for_a_close_error(tmp_path, close_fault, role, shape):
    path, identity = _rule_target(tmp_path)
    expected = LocalActivationFs(_owner()).observe(path)
    fault = close_fault(path, role, shape)
    assert LocalActivationFs(_owner()).observe(path) == expected
    assert fault.hits >= 1 and fault.never_retried() and classify(identity, expected, _owner()) is Attribution.A1_INTACT


@pytest.mark.parametrize("role,shape", CLOSE_CASES)
def test_a_close_error_keeps_a_valid_grant_id_and_an_inspection_failure_stays_unavailable(
    tmp_path, monkeypatch, close_fault, role, shape
):
    path, _ = _rule_target(tmp_path)
    os.chmod(path, 0o600)
    good = LocalActivationFs(_owner()).read_root_file(path, max_bytes=4_096, mode=0o600)
    assert good is not None
    fault = close_fault(path, role, shape)
    assert LocalActivationFs(_owner()).read_root_file(path, max_bytes=4_096, mode=0o600) == good
    assert fault.hits >= 1 and fault.never_retried()
    inspect = InspectionFault(monkeypatch, path, "read")
    assert LocalActivationFs(_owner()).read_root_file(path, max_bytes=4_096, mode=0o600) is None
    assert inspect.hits >= 1


@pytest.mark.parametrize("role,shape", CLOSE_CASES)
def test_stop_post_cl_g_survives_a_close_error_on_the_grant(fx, layout, close_fault, role, shape):
    """CL-G removes the grant, CL-0 … CL-7 all run and the attempt is recorded."""
    fx.activate()
    p = paths(layout)
    fault = close_fault(p.rule, role, shape)
    out, _ = run_cl(layout, fx)
    assert fault.hits >= 1  # descriptor numbers are reused across operations: no retry check here
    assert out.terminal is Terminal.ST1_VERIFIED, out.diagnostic(ACT_ID)
    assert not os.path.lexists(p.rule) and record(layout, 1)["grant_identity"]["cl_g"] == "removed"
    journal = attempt_journal(layout, 1)
    assert [line["op"] for line in journal[:2]] == ["run-start", "cl-g"] and journal[-1]["op"] == "run-end"


@pytest.mark.parametrize("shape", CloseFault.SHAPES)
def test_a_close_error_on_a_traversed_ancestor_does_not_change_the_result(tmp_path, close_fault, shape):
    path, identity = _rule_target(tmp_path)
    fault = close_fault(str(tmp_path), "target", shape)  # closed while open_dir walks past it
    removal = LocalActivationFs(_owner()).remove(path, identity, directory=False, before_unlink=lambda _o: None)
    assert fault.hits >= 1 and fault.never_retried() and removal.outcome is RemovalOutcome.REMOVED


@pytest.mark.parametrize("shape", CloseFault.SHAPES)
def test_a_close_error_while_open_dir_unwinds_keeps_the_original_failure(tmp_path, close_fault, shape):
    path, identity = _rule_target(tmp_path)
    missing = os.path.join(os.path.dirname(path), "gone", "x")
    fault = close_fault(os.path.dirname(path), "target", shape)  # the last good descriptor, closed on failure
    removal = LocalActivationFs(_owner()).remove(missing, identity, directory=False, before_unlink=lambda _o: None)
    assert fault.hits >= 1 and removal.outcome is RemovalOutcome.ABSENT
    with pytest.raises(FileNotFoundError):
        open_dir(missing.rsplit("/", 1)[0])


@pytest.mark.parametrize("shape", CloseFault.SHAPES)
def test_neighbouring_readers_are_not_overridden_by_a_close_error(tmp_path, close_fault, shape):
    path, _ = _rule_target(tmp_path)
    directory = os.path.dirname(path)
    fs = LocalActivationFs(_owner())
    fault = close_fault(directory, "target", shape)
    assert fs.list_prefixed(directory, "50-") == ("50-x.rules",)
    assert fault.hits >= 1 and fault.never_retried()
    journal_dir = tmp_path / "evidence"
    journal_dir.mkdir(mode=0o700)
    journal = journal_dir / "journal"
    journal.write_bytes(b"{}\n")
    os.chmod(journal, 0o644)
    for role, target in (("target", str(journal)), ("parent", str(journal))):
        fault = close_fault(target, role, shape)
        data = fs.read_journal(str(journal_dir), max_bytes=4_096, dir_uid=os.getuid(), dir_mode=0o700)
        assert data == b"{}\n" and fault.hits >= 1 and fault.never_retried()
