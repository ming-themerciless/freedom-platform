"""PK/2 (DI-5 + DI-6) and the SN contract for the authorization subject.

Fakes cover every DI-5 / DI-6 outcome and every SN-R branch the PK subject can
reach; the real fork subject is also run unprivileged here (same credentials,
so no change is needed) and as root against real Polkit on the disposable host.
"""

from __future__ import annotations

import contextlib
import errno
import os
import resource
import signal
import sys
import time

import pytest

sys.dont_write_bytecode = True

import adapters.rp11.process as process_module  # noqa: E402
from adapters.rp11.process import ForkSubjectLauncher, LinuxProcessOps, SystemClock  # noqa: E402
from application.rp11.authority import Operator, Params  # noqa: E402
from application.rp11.pk import PkMode, PkOutcome, PkSeries, schedule  # noqa: E402
from application.rp11.sn import ChildHandle, HandleState, ReapError, SignalContract  # noqa: E402
from application.unit_control import (  # noqa: E402
    ControlError,
    ControlOk,
    PolkitAuthorized,
    PolkitNotAuthorized,
    ProcessSubject,
    UnitVerb,
)

OPERATOR = Operator(user="ubuntu", uid=1000, gid=1000, groups=(1000,))


class Clock:
    def __init__(self) -> None:
        self.now = 10_000
        self.sleeps: list[int] = []

    def monotonic_ms(self) -> int:
        return self.now

    def sleep_ms(self, ms: int) -> None:
        assert ms > 0
        self.sleeps.append(ms)
        self.now += ms


class Ops(Clock):
    """Fake ``ProcessOps``: scripted identity, send and reap behaviour."""

    def __init__(self, *, reap_after: int | None = 0, reap_raises_at: int | None = None,
                 kill_exc: BaseException | None = None, pgid: int | None = None,
                 sid: int | None = None, ticks: int = 77, kill_takes: int = 0) -> None:
        super().__init__()
        self.reap_after = reap_after
        self.reap_raises_at = reap_raises_at
        self.kill_exc = kill_exc
        self.pgid = pgid
        self.sid = sid
        self.ticks = ticks
        self.kill_takes = kill_takes
        self.kills: list[tuple[int, int]] = []
        self.reaps = 0

    def own_pgrp(self) -> int:
        return 1

    def getpgid(self, pid):
        return self.pgid if self.pgid is not None else pid

    def getsid(self, pid):
        return self.sid if self.sid is not None else pid

    def start_ticks(self, pid):
        if self.ticks < 0:
            raise OSError(errno.ESRCH, "gone")
        return self.ticks

    def killpg(self, pgid, sig):
        self.kills.append((pgid, sig))
        self.now += self.kill_takes
        if self.kill_exc is not None:
            raise self.kill_exc

    def reap(self, pid):
        self.reaps += 1
        if self.reap_raises_at is not None and self.reaps >= self.reap_raises_at:
            raise ReapError("ECHILD")
        return self.reap_after is not None and self.reaps > self.reap_after


def handle(**kw) -> ChildHandle:
    base = dict(pid=500, pgid=500, start_ticks=77, created_ms=10_000, deadline_ms=70_000)
    base.update(kw)
    return ChildHandle(**base)


def settle(ops: Ops, h: ChildHandle | None = None) -> ChildHandle:
    return SignalContract(ops, grace_ms=2_000, slice_ms=100).settle_pk_subject(h or handle())


# ---------------------------------------------------------------------------
# SN (H-SN.2 … H-SN.16, table SN-R)
# ---------------------------------------------------------------------------


def test_a_subject_is_killed_once_and_reaped():
    ops = Ops(reap_after=0)
    h = settle(ops)
    assert ops.kills == [(500, signal.SIGKILL)]
    assert h.state is HandleState.REAPED
    entry = h.entry()
    assert entry["sends"] == [{"signal": "SIGKILL", "result": "sent", "offset_ms": 0, "late": False}]
    assert entry["s0_ran"] and entry["grace_deadline_ms"] == 12_000 and entry["reaped"]


def test_no_sigterm_is_ever_sent_to_a_pk_subject():
    ops = Ops(reap_after=5)
    settle(ops)
    assert [sig for _pg, sig in ops.kills] == [signal.SIGKILL]


def test_esrch_is_recorded_and_never_read_as_gone():
    ops = Ops(reap_after=3, kill_exc=ProcessLookupError(errno.ESRCH, "x"))
    h = settle(ops)
    assert h.sends[0]["result"] == "esrch" and "esrch-while-unreaped" in h.anomalies
    assert h.state is HandleState.REAPED and ops.reaps == 4  # it still had to be reaped


@pytest.mark.parametrize(
    "exc,result",
    [(PermissionError(errno.EPERM, "x"), "eperm"), (OSError(errno.EINVAL, "x"), "errno:22"),
     (RuntimeError("x"), "exception:RuntimeError")],
)
def test_failed_sends_are_recorded_never_retried(exc, result):
    ops = Ops(reap_after=None, kill_exc=exc)
    h = settle(ops)
    assert len(ops.kills) == 1 and h.sends[0]["result"] == result
    assert h.state is HandleState.ABANDONED


@pytest.mark.parametrize("field", ["pgid", "sid"])
def test_an_identity_mismatch_sends_nothing_and_abandons(field):
    ops = Ops(reap_after=None, **{field: 999})
    h = settle(ops)
    assert ops.kills == [] and h.sends[0]["result"] == "not-sent(identity-mismatch)"
    assert h.state is HandleState.ABANDONED and h.entry()["abandoned"]
    assert sum(ops.sleeps) <= 2_000 and all(s <= 100 for s in ops.sleeps)


def test_a_replaced_start_time_is_an_identity_mismatch():
    ops = Ops(reap_after=None, ticks=78)
    assert settle(ops).sends[0]["result"] == "not-sent(identity-mismatch)" and ops.kills == []


def test_an_unreadable_proc_entry_is_identity_unverifiable():
    ops = Ops(reap_after=0, ticks=-1)
    h = settle(ops)
    assert h.sends[0]["result"] == "not-sent(identity-unverifiable)" and ops.kills == []
    assert h.state is HandleState.REAPED


def test_a_handle_unverifiable_from_creation_is_never_signalled():
    ops = Ops(reap_after=None)
    h = settle(ops, handle(identity_verifiable=False))
    assert ops.kills == [] and h.state is HandleState.ABANDONED


def test_the_own_process_group_is_never_signalled():
    ops = Ops(reap_after=None)
    h = settle(ops, handle(pid=1, pgid=1))
    assert ops.kills == [] and h.sends[0]["result"] == "not-sent(identity-mismatch)"


def test_a_reap_error_suppresses_everything_after_it():
    ops = Ops(reap_after=None, reap_raises_at=1)
    h = settle(ops)
    assert h.state is HandleState.REAP_UNKNOWN and h.send_suppressed and "reap-error" in h.anomalies
    assert ops.sleeps == [] and len(ops.kills) == 1
    entry = h.entry()
    assert entry["reap_unknown"] and not entry["reaped"] and not entry["abandoned"]


def test_a_late_send_skips_every_timed_wait():
    ops = Ops(reap_after=None, kill_takes=2_500)
    h = settle(ops)
    assert h.sends[0]["late"] is True
    assert ops.sleeps == [] and ops.reaps == 1 and h.state is HandleState.ABANDONED


def test_an_abandoned_subject_is_never_signalled_again():
    ops = Ops(reap_after=None)
    h = settle(ops)
    assert h.state is HandleState.ABANDONED
    settle(ops, h)
    assert len(ops.kills) == 1 and h.sends[-1]["result"] == "not-sent(abandoned)"


def test_the_grace_budget_is_one_deadline_never_extended():
    ops = Ops(reap_after=None)
    h = settle(ops)
    assert h.grace_deadline_ms == 12_000 and ops.now <= 12_100


# ---------------------------------------------------------------------------
# PK/2 (H-PK2.1 … H-PK2.7) over DI-5 / DI-6
# ---------------------------------------------------------------------------


def test_the_schedule_is_the_accepted_offsets_within_p():
    assert schedule(5_000) == (0, 250, 500, 1_000, 2_000, 3_000, 4_000)
    assert schedule(30_000)[-3:] == (24_000, 26_000, 28_000) and len(schedule(30_000)) == 19


class Launcher:
    def __init__(self, clock: Clock, *, fail: bool = False, ready: bool = True):
        self.clock = clock
        self.fail = fail
        self.ready = ready
        self.spawned: list[ChildHandle] = []

    def spawn(self, operator):
        if self.fail:
            return ControlError("spawn-failed")
        h = handle(pid=600 + len(self.spawned), pgid=600 + len(self.spawned), ready=self.ready,
                   created_ms=self.clock.now)
        self.spawned.append(h)
        return h


class Subjects:
    def __init__(self, results):
        self.results = results

    def subject_for_pid(self, pid):
        result = self.results(pid)
        return result


class Authority:
    def __init__(self, answers):
        self.answers = list(answers)
        self.calls: list[tuple[ProcessSubject, UnitVerb]] = []

    def check(self, subject, verb):
        self.calls.append((subject, verb))
        return self.answers.pop(0) if len(self.answers) > 1 else self.answers[0]


def series(answers, *, subjects=None, launcher_kw=None, op_ms=5_000):
    clock = Ops(reap_after=0)
    launcher = Launcher(clock, **(launcher_kw or {}))
    authority = Authority(answers)
    subjects = subjects or Subjects(lambda pid: ControlOk(ProcessSubject(pid, 77, OPERATOR.uid)))
    pk = PkSeries(
        launcher=launcher,
        subjects=subjects,
        authority=authority,
        contract=SignalContract(clock, grace_ms=2_000, slice_ms=100),
        clock=clock,
        params=Params(pk_op_ms=op_ms, pk_call_ms=1_000),
    )
    return pk.run(OPERATOR, UnitVerb.START, PkMode.SEEK_NOT_AUTHORIZED), launcher, authority, clock


def test_a_denial_ends_the_series_not_authorized():
    result, launcher, authority, _ = series([PolkitNotAuthorized()])
    assert result.outcome is PkOutcome.NOT_AUTHORIZED and result.calls == 1
    assert authority.calls[0][1] is UnitVerb.START
    assert all(h.state is HandleState.REAPED for h in launcher.spawned)


def test_a_challenge_is_not_authorized_never_error():
    result, *_ = series([PolkitNotAuthorized(challenge=True)])
    assert result.outcome is PkOutcome.NOT_AUTHORIZED


def test_a_persistent_authorization_is_unconfirmed_still_authorized():
    result, launcher, _a, clock = series([PolkitAuthorized()])
    assert result.outcome is PkOutcome.UNCONFIRMED and result.reason == "still-authorized"
    assert result.calls == len(schedule(5_000)) == len(launcher.spawned)
    assert all(h.state is HandleState.REAPED for h in launcher.spawned)


def test_authorized_then_denied_ends_at_the_denial():
    result, *_ = series([PolkitAuthorized(), PolkitAuthorized(), PolkitNotAuthorized()])
    assert result.outcome is PkOutcome.NOT_AUTHORIZED and result.calls == 3


@pytest.mark.parametrize(
    "error",
    ["invalid-reply", "timeout", "disconnected", "connect-failed",
     "org.freedesktop.PolicyKit1.Error.Failed", "org.freedesktop.DBus.Error.NoReply"],
)
def test_every_di5_error_retries_and_never_decides(error):
    result, *_ = series([ControlError(error)])
    assert result.outcome is PkOutcome.UNCONFIRMED and result.reason == "only-errors"
    assert result.errors and all(e == f"polkit:{error}" for e in result.errors)


def test_an_error_then_a_denial_decides_on_the_denial():
    result, *_ = series([ControlError("timeout"), PolkitNotAuthorized()])
    assert result.outcome is PkOutcome.NOT_AUTHORIZED and result.calls == 2


@pytest.mark.parametrize("kind", ["proc-replaced", "proc-unreadable", "proc-malformed"])
def test_a_subject_that_cannot_be_identified_is_an_error(kind):
    result, _l, authority, _c = series(
        [PolkitNotAuthorized()], subjects=Subjects(lambda pid: ControlError(kind))
    )
    assert result.outcome is PkOutcome.UNCONFIRMED and authority.calls == []


def test_a_subject_with_another_uid_never_reaches_polkit():
    result, _l, authority, _c = series(
        [PolkitNotAuthorized()],
        subjects=Subjects(lambda pid: ControlOk(ProcessSubject(pid, 77, 0))),
    )
    assert result.outcome is PkOutcome.UNCONFIRMED and authority.calls == []
    assert "subject:uid-mismatch" in result.errors


def test_a_subject_replaced_between_creation_and_the_call_is_an_error():
    result, _l, authority, _c = series(
        [PolkitNotAuthorized()],
        subjects=Subjects(lambda pid: ControlOk(ProcessSubject(pid, 78, OPERATOR.uid))),
    )
    assert authority.calls == [] and "subject:replaced" in result.errors


def test_a_spawn_failure_or_an_unready_subject_is_an_error():
    result, *_ = series([PolkitNotAuthorized()], launcher_kw={"fail": True})
    assert result.outcome is PkOutcome.UNCONFIRMED and result.children == []
    result, launcher, authority, _ = series([PolkitNotAuthorized()], launcher_kw={"ready": False})
    assert result.outcome is PkOutcome.UNCONFIRMED and authority.calls == []
    assert all(h.state is HandleState.REAPED for h in launcher.spawned)  # still settled


def test_no_call_starts_after_p_and_children_are_bounded():
    result, launcher, _a, clock = series([ControlError("timeout")], op_ms=5_000)
    assert result.calls == 7 and len(result.children) == 7
    assert result.signal_counts() == {"sent": 7, "esrch": 0, "failed": 0, "not_sent": 0}


# ---------------------------------------------------------------------------
# the real fork subject (unprivileged: same credentials)
# ---------------------------------------------------------------------------


def _me() -> Operator:
    return Operator(user="me", uid=os.getuid(), gid=os.getgid(), groups=tuple(sorted(set(os.getgroups()))))


@pytest.mark.skipif(os.geteuid() == 0, reason="as root the credential change is exercised on the host")
def test_the_real_subject_has_its_own_session_no_descriptors_and_is_settled():
    ops = LinuxProcessOps(SystemClock())
    extra = os.open("/dev/null", os.O_RDONLY)  # a descriptor the subject must not inherit
    os.set_inheritable(extra, True)
    try:
        h = ForkSubjectLauncher(ops, ready_ms=2_000).spawn(_me())
    finally:
        os.close(extra)
    assert isinstance(h, ChildHandle) and h.ready and h.identity_verifiable
    assert os.getpgid(h.pid) == h.pid and os.getsid(h.pid) == h.pid
    assert sorted(os.listdir(f"/proc/{h.pid}/fd")) == ["0", "1", "2"]
    assert os.readlink(f"/proc/{h.pid}/cwd") == "/"
    status = dict(line.split(":\t", 1) for line in open(f"/proc/{h.pid}/status").read().splitlines() if ":\t" in line)
    assert status["Uid"].split()[0] == str(os.getuid())
    SignalContract(ops, grace_ms=2_000, slice_ms=50).settle_pk_subject(h)
    assert h.state is HandleState.REAPED and h.sends[0]["result"] == "sent"
    assert not os.path.exists(f"/proc/{h.pid}")


HIGH_FD = 70_000  # above the former fixed bound of 65,536


@contextlib.contextmanager
def nofile_soft_limit(at_least: int):
    """Raise the soft ``RLIMIT_NOFILE`` to ``at_least`` (within the hard limit) and
    restore the original pair on every exit, a skip or a failure included."""
    original = resource.getrlimit(resource.RLIMIT_NOFILE)
    soft, hard = original
    try:
        if hard != resource.RLIM_INFINITY and hard < at_least:
            pytest.skip(f"hard RLIMIT_NOFILE {hard} < {at_least}")
        if soft == resource.RLIM_INFINITY or soft < at_least:
            resource.setrlimit(resource.RLIMIT_NOFILE, (at_least, hard))
        yield
    finally:
        resource.setrlimit(resource.RLIMIT_NOFILE, original)
        assert resource.getrlimit(resource.RLIMIT_NOFILE) == original


@contextlib.contextmanager
def inheritable_descriptor(number: int):
    """An inheritable descriptor at exactly ``number``, closed on every exit."""
    source = os.open("/dev/null", os.O_RDONLY)
    try:
        assert os.dup2(source, number, inheritable=True) == number
    finally:
        os.close(source)
    try:
        assert os.get_inheritable(number)
        yield number
    finally:
        os.close(number)


def _ready_subject_fds(h: ChildHandle) -> list[str]:
    try:
        assert isinstance(h, ChildHandle) and h.ready and h.identity_verifiable
        return sorted(os.listdir(f"/proc/{h.pid}/fd"), key=int)
    finally:
        SignalContract(LinuxProcessOps(SystemClock()), grace_ms=2_000, slice_ms=50).settle_pk_subject(h)
        assert h.state is HandleState.REAPED


def test_a_descriptor_above_65535_is_not_inherited_by_the_ready_subject():
    """H-PROC.3 regression: the real fork subject, with an inheritable descriptor
    at 70,000, holds exactly 0, 1 and 2 once ready (the fixed 65,536 bound leaked it)."""
    with nofile_soft_limit(HIGH_FD + 1), inheritable_descriptor(HIGH_FD):
        assert str(HIGH_FD) in os.listdir("/proc/self/fd")
        h = ForkSubjectLauncher(LinuxProcessOps(SystemClock()), ready_ms=2_000).spawn(_me())
        assert _ready_subject_fds(h) == ["0", "1", "2"]


def test_a_descriptor_above_the_current_soft_limit_is_not_inherited():
    """The bound is not ``RLIMIT_NOFILE`` either: a descriptor opened under a high
    limit stays open after the limit is lowered below it, and must still be closed."""
    with nofile_soft_limit(HIGH_FD + 1), inheritable_descriptor(HIGH_FD):
        _soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        resource.setrlimit(resource.RLIMIT_NOFILE, (1_024, hard))  # restored by nofile_soft_limit
        h = ForkSubjectLauncher(LinuxProcessOps(SystemClock()), ready_ms=2_000).spawn(_me())
        assert _ready_subject_fds(h) == ["0", "1", "2"]


def test_a_subject_that_cannot_list_its_descriptors_never_reports_ready(monkeypatch):
    """Fail closed: without the descriptor listing the subject closes nothing it
    cannot prove and never sends the readiness byte."""
    monkeypatch.setattr(process_module, "_OWN_FDS", "/proc/self/no-such-directory")
    ops = LinuxProcessOps(SystemClock())
    h = ForkSubjectLauncher(ops, ready_ms=2_000).spawn(_me())
    assert isinstance(h, ChildHandle) and not h.ready
    SignalContract(ops, grace_ms=2_000, slice_ms=50).settle_pk_subject(h)
    assert h.state is HandleState.REAPED


def test_a_descriptor_that_survives_closing_is_an_error():
    """The verifying second listing: if a close did not take effect, raise."""
    pid = os.fork()
    if pid == 0:  # pragma: no cover - a throwaway child
        code = 1
        try:
            keep = os.open("/dev/null", os.O_RDONLY)
            extra = os.open("/dev/null", os.O_RDONLY)
            process_module.os.close = lambda fd: None  # a close that does nothing
            try:
                process_module.close_inherited_descriptors(keep=keep)
            except OSError:
                code = 0 if os.get_inheritable(extra) is False else 2
        finally:
            os._exit(code)
    _, status = os.waitpid(pid, 0)
    assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


@pytest.mark.skipif(os.geteuid() == 0, reason="unprivileged only")
def test_a_subject_that_cannot_take_the_credentials_never_reports_ready():
    ops = LinuxProcessOps(SystemClock())
    other = Operator(user="x", uid=os.getuid() + 1, gid=os.getgid(), groups=(os.getgid(),))
    h = ForkSubjectLauncher(ops, ready_ms=2_000).spawn(other)
    assert isinstance(h, ChildHandle) and not h.ready
    SignalContract(ops, grace_ms=2_000, slice_ms=50).settle_pk_subject(h)
    assert h.state is HandleState.REAPED


def test_linux_ops_refuse_any_other_signal_and_group_one():
    ops = LinuxProcessOps(SystemClock())
    with pytest.raises(ValueError):
        ops.killpg(12345, signal.SIGHUP)
    with pytest.raises(ValueError):
        ops.killpg(1, signal.SIGKILL)


def test_a_reap_of_a_foreign_pid_is_a_reap_error():
    with pytest.raises(ReapError):
        LinuxProcessOps(SystemClock()).reap(1)


def test_the_subject_lifetime_is_self_limited():
    """The child arms alarm(60) with SIGALRM at its default action (checked in
    /proc: SIGALRM neither caught nor ignored, no pending timer cancelled)."""
    if os.geteuid() == 0:
        pytest.skip("host test covers root")
    ops = LinuxProcessOps(SystemClock())
    h = ForkSubjectLauncher(ops, ready_ms=2_000).spawn(_me())
    try:
        status = open(f"/proc/{h.pid}/status").read()
        caught = int(next(l for l in status.splitlines() if l.startswith("SigCgt:")).split()[1], 16)
        ignored = int(next(l for l in status.splitlines() if l.startswith("SigIgn:")).split()[1], 16)
        alrm = 1 << (signal.SIGALRM - 1)
        assert not caught & alrm and not ignored & alrm
    finally:
        SignalContract(ops, grace_ms=2_000, slice_ms=50).settle_pk_subject(h)
    time.sleep(0)
