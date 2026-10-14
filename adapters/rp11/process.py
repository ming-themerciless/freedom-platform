"""The DI-6 authorization subject and the process calls of the SN contract.

The subject is a **fork that continues in this static image** (inventory PC-1,
form (F)): no ``execve`` at all, so no distribution program (``sleep``) and no
shell. In the child, before anything else:

0. every disposition the parent may have set (the holder's flag-only SG-1
   handlers and its ignored ``SIGPIPE``) back to the default, so ``SIGALRM``
   and every other signal end the subject;
1. ``setsid()`` — its own session and process group (pgid == sid == pid);
2. the supplementary groups, GID and UID of the H-1 operator, then a check that
   real, effective and saved IDs all equal them;
3. ``chdir("/")`` and every descriptor ≥ 3 closed except the readiness pipe
   (H-PROC.3), found by listing ``/proc/self/fd`` — never by a numeric bound, so
   a descriptor above any constant or above the current ``RLIMIT_NOFILE`` is
   closed too — and a second listing proving nothing else is open, else the
   subject never reports ready;
4. ``alarm(60)`` with ``SIGALRM`` at its default action: the kernel ends the
   subject after at most 60 s on its own, whatever the parent does;
5. one byte on the readiness pipe, the pipe closed, then ``pause()``.

The parent waits for that byte and the pipe's end-of-file for at most
``pk_call_ms``; a subject that never reports is still handed to SN so it is
signalled and reaped (or abandoned).
Only ``reap`` (``waitpid(WNOHANG)``) ever reaps (the sole-reaper invariant).
"""

from __future__ import annotations

import errno
import os
import select
import signal
import time

from application.rp11.authority import Operator
from application.rp11.sn import ChildHandle, ReapError
from application.unit_control import ControlError

SUBJECT_LIFETIME_S = 60
# The holder's SG-1 set plus SIGPIPE: a fork inherits the parent's handlers.
_DEFAULT_IN_SUBJECT = (
    signal.SIGALRM,
    signal.SIGTERM,
    signal.SIGINT,
    signal.SIGHUP,
    signal.SIGQUIT,
    signal.SIGUSR1,
    signal.SIGUSR2,
    signal.SIGPIPE,
)
_STAT_START_INDEX = 19  # field 22, counted from the token after ") "
_OWN_FDS = "/proc/self/fd"


class SystemClock:
    def monotonic_ms(self) -> int:
        return time.monotonic_ns() // 1_000_000

    def monotonic_us(self) -> int:
        """CLOCK_MONOTONIC floored to µs: the clock of systemd's ``*TimestampMonotonic``."""
        return time.clock_gettime_ns(time.CLOCK_MONOTONIC) // 1_000

    def sleep_ms(self, ms: int) -> None:
        if ms > 0:
            time.sleep(ms / 1000)


def read_start_ticks(pid: int, proc_root: str = "/proc") -> int:
    with open(f"{proc_root}/{pid}/stat", "rb") as handle:
        raw = handle.read(4_096).decode("ascii", "strict")
    close = raw.rfind(")")
    if close < 0 or raw[close + 1 : close + 2] != " ":
        raise ValueError("stat has no comm terminator")
    tokens = raw[close + 2 :].split()
    if len(tokens) <= _STAT_START_INDEX or not tokens[_STAT_START_INDEX].isdigit():
        raise ValueError("stat has no start time")
    return int(tokens[_STAT_START_INDEX])


class LinuxProcessOps:
    """``application.rp11.sn.ProcessOps`` on Linux."""

    def __init__(self, clock: SystemClock | None = None) -> None:
        self._clock = clock or SystemClock()

    def monotonic_ms(self) -> int:
        return self._clock.monotonic_ms()

    def sleep_ms(self, ms: int) -> None:
        self._clock.sleep_ms(ms)

    def own_pgrp(self) -> int:
        return os.getpgrp()

    def getpgid(self, pid: int) -> int:
        return os.getpgid(pid)

    def getsid(self, pid: int) -> int:
        return os.getsid(pid)

    def start_ticks(self, pid: int) -> int:
        return read_start_ticks(pid)

    def killpg(self, pgid: int, sig: int) -> None:
        if sig not in (signal.SIGTERM, signal.SIGKILL) or pgid <= 1:
            raise ValueError("SN sends only SIGTERM or SIGKILL to a child group")
        os.killpg(pgid, sig)

    def reap(self, pid: int) -> bool:
        try:
            got, _status = os.waitpid(pid, os.WNOHANG)
        except OSError as exc:
            raise ReapError(type(exc).__name__) from exc
        return got == pid


def _listed_descriptors() -> list[int]:
    # The listing opens one descriptor of its own; it is closed again on return.
    return [int(name) for name in os.listdir(_OWN_FDS)]


def _is_open(fd: int) -> bool:
    try:
        os.get_inheritable(fd)  # fcntl(F_GETFD): EBADF once closed
    except OSError:
        return False
    return True


def close_inherited_descriptors(*, keep: int) -> None:
    """H-PROC.3: close every descriptor ≥ 3 except ``keep``, whatever its number.

    The kernel's list of this process's open descriptors is enumerated, so no
    upper bound is assumed: not a constant, not ``RLIMIT_NOFILE`` (which may have
    been raised up to ``fs.nr_open`` or lowered below a descriptor that is already
    open) and no ``RLIM_INFINITY`` case to interpret. A second listing must show
    nothing else open; otherwise ``OSError`` — in the subject that means it never
    reports ready. Without ``/proc`` the listing fails the same way (fail closed).
    """
    for fd in _listed_descriptors():
        if fd >= 3 and fd != keep:
            try:
                os.close(fd)
            except OSError:
                pass  # the listing's own descriptor, already closed
    survivors = [fd for fd in _listed_descriptors() if fd >= 3 and fd != keep and _is_open(fd)]
    if survivors:
        raise OSError(errno.EBADF, "an inherited descriptor survived")


def _child(write_fd: int, operator: Operator) -> None:
    """Runs in the forked child only; never returns."""
    code = 127
    try:
        for signum in _DEFAULT_IN_SUBJECT:
            signal.signal(signum, signal.SIG_DFL)
        os.setsid()
        wanted = (operator.uid, operator.gid, sorted(set(operator.groups)))
        current = (os.getuid(), os.getgid(), sorted(set(os.getgroups())))
        if os.geteuid() == 0 or current != wanted:
            os.setgroups(list(operator.groups))
            os.setgid(operator.gid)
            os.setuid(operator.uid)
        if (
            os.getresuid() != (operator.uid,) * 3
            or os.getresgid() != (operator.gid,) * 3
            or sorted(set(os.getgroups())) != sorted(set(operator.groups))
        ):
            code = 126
            raise PermissionError("credentials not applied")
        os.chdir("/")
        close_inherited_descriptors(keep=write_fd)
        signal.alarm(SUBJECT_LIFETIME_S)
        os.write(write_fd, b"1")
        os.close(write_fd)
        while True:
            signal.pause()
    except BaseException:  # noqa: BLE001 - the child must never return into the parent's code
        pass
    os._exit(code)


class ForkSubjectLauncher:
    """``SubjectLauncher``: one subject per PK call."""

    def __init__(self, ops: LinuxProcessOps, *, ready_ms: int) -> None:
        self._ops = ops
        self._ready_ms = ready_ms

    def spawn(self, operator: Operator) -> ChildHandle | ControlError:
        try:
            read_fd, write_fd = os.pipe2(os.O_CLOEXEC)
        except OSError as exc:
            return ControlError("spawn-failed", type(exc).__name__)
        try:
            pid = os.fork()
        except OSError as exc:
            os.close(read_fd)
            os.close(write_fd)
            return ControlError("spawn-failed", type(exc).__name__)
        if pid == 0:  # pragma: no cover - exercised as a real child
            os.close(read_fd)
            _child(write_fd, operator)
        os.close(write_fd)
        created = self._ops.monotonic_ms()
        try:
            ready = self._await_ready(read_fd)
        finally:
            os.close(read_fd)
        handle = ChildHandle(
            pid=pid,
            pgid=pid,
            start_ticks=None,
            created_ms=created,
            deadline_ms=created + SUBJECT_LIFETIME_S * 1000,
            ready=ready,
        )
        try:
            handle.start_ticks = self._ops.start_ticks(pid)
            if (
                self._ops.getpgid(pid) != pid
                or self._ops.getsid(pid) != pid
                or pid == self._ops.own_pgrp()
            ):
                handle.identity_verifiable = False
        except (OSError, ValueError):
            handle.identity_verifiable = False
        return handle

    def _await_ready(self, read_fd: int) -> bool:
        """Ready means the byte ``1`` **and** end-of-file: the subject has closed its
        last descriptor ≥ 3 (the pipe) before it is used as a Polkit subject."""
        poller = select.poll()
        poller.register(read_fd, select.POLLIN | select.POLLHUP)
        deadline = self._ops.monotonic_ms() + self._ready_ms
        received = b""
        while True:
            remaining = deadline - self._ops.monotonic_ms()
            if remaining <= 0 or not poller.poll(remaining):
                return False
            try:
                chunk = os.read(read_fd, 2)
            except OSError:
                return False
            if not chunk:
                return received == b"1"
            received += chunk
            if len(received) > 1:
                return False
