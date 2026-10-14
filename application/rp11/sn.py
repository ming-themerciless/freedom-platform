"""SN: the signal, validation, reap and wait contract for a child of a root helper.

The only child the Route 3 roles create is the DI-6 authorization subject
(inventory §8.1, PC-1), so this implements the PK-subject path of SN (SN-I-3):
after its Polkit call the subject is settled exactly once.

    S0  t_g = now + g, once, only for a handle still ``running``
    S1  validate (SN-4): running, pid > 1, pgid == pid, pgid is not ours,
        getpgid(pid) == getsid(pid) == pgid, start ticks unchanged
    S4  one SIGKILL to the group (no SIGTERM for a PK subject), result recorded
    S5  reap attempts, capped sleeps only while now < t_g; an attempt begun at
        or after t_g is the final one
    S6  still unreaped after the final attempt: abandoned, never signalled again
    S7  record once and return; nothing here decides the enclosing result
    S8  a reap attempt that raises: reap-unknown, every later send suppressed

A send is never proof of exit and ``ESRCH`` is never read as "gone". Process
access is the injected ``ProcessOps``, so every branch is testable without a
real child. Clock values in the record are observations, never claims.
"""

from __future__ import annotations

import errno
import signal
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from .canonical import ABSENT

MAX_CHILD_ENTRIES = 64


class HandleState(str, Enum):
    RUNNING = "running"
    REAPED = "reaped"
    ABANDONED = "abandoned"
    REAP_UNKNOWN = "reap-unknown"


class ReapError(Exception):
    """A reap attempt raised (RA-E)."""


class ProcessOps(Protocol):
    def monotonic_ms(self) -> int: ...

    def sleep_ms(self, ms: int) -> None: ...

    def own_pgrp(self) -> int: ...

    def getpgid(self, pid: int) -> int: ...

    def getsid(self, pid: int) -> int: ...

    def start_ticks(self, pid: int) -> int:
        """``/proc/<pid>/stat`` field 22, read capped at 4,096 bytes; raises if unreadable."""
        ...

    def killpg(self, pgid: int, sig: int) -> None: ...

    def reap(self, pid: int) -> bool:
        """One non-blocking reap attempt: True if reaped now; raises ``ReapError``."""
        ...


@dataclass
class ChildHandle:
    pid: int
    pgid: int
    start_ticks: int | None
    created_ms: int
    deadline_ms: int
    role: str = "pk-subject"
    argv0: str = "rp11-subject"
    state: HandleState = HandleState.RUNNING
    identity_verifiable: bool = True
    ready: bool = True  # credentials applied and the subject reported in
    s0_ran: bool = False
    grace_deadline_ms: int | None = None
    sends: list[dict] = field(default_factory=list)
    anomalies: list[str] = field(default_factory=list)
    waits_skipped: int = 0
    send_suppressed: bool = False

    def entry(self) -> dict:
        """The ``children[]`` entry (§8.5); ``"absent"`` stands for ``null``."""
        last = self.sends[-1]["signal"] if self.sends else ABSENT
        return {
            "role": self.role,
            "argv0": self.argv0,
            "pid": self.pid,
            "pgid": self.pgid,
            "start_ticks": self.start_ticks if self.start_ticks is not None else ABSENT,
            "deadline_ms": self.deadline_ms,
            "s0_ran": self.s0_ran,
            "grace_deadline_ms": self.grace_deadline_ms if self.s0_ran else ABSENT,
            "outcome": "reap-error"
            if self.state is HandleState.REAP_UNKNOWN and not self.s0_ran
            else "exited",
            "sends": list(self.sends),
            "waits_skipped": self.waits_skipped,
            "reaped": self.state is HandleState.REAPED,
            "abandoned": self.state is HandleState.ABANDONED,
            "reap_unknown": self.state is HandleState.REAP_UNKNOWN,
            "send_suppressed": self.send_suppressed,
            "last_signal": last,
            "effect": "none",
            "anomalies": list(self.anomalies),
        }


def _send_result(exc: BaseException | None) -> tuple[str, str | None]:
    if exc is None:
        return "sent", None
    if isinstance(exc, ProcessLookupError) or getattr(exc, "errno", None) == errno.ESRCH:
        return "esrch", "esrch-while-unreaped"
    if isinstance(exc, PermissionError) or getattr(exc, "errno", None) == errno.EPERM:
        return "eperm", "eperm-from-root"
    if isinstance(exc, OSError):
        return f"errno:{exc.errno if exc.errno is not None else 0}", "send-error"
    return f"exception:{type(exc).__name__}", "send-error"


class SignalContract:
    """Runs SN for one handle. Holds no state between handles."""

    def __init__(self, ops: ProcessOps, *, grace_ms: int, slice_ms: int) -> None:
        self._ops = ops
        self._grace = grace_ms
        self._slice = slice_ms

    def settle_pk_subject(self, handle: ChildHandle) -> ChildHandle:
        if handle.state is not HandleState.RUNNING:
            handle.sends.append(self._not_sent(f"not-sent({handle.state.value})"))
            return handle  # S1-a ⇒ S7: no call, no wait, no clock read
        # S0
        t_g = self._ops.monotonic_ms() + self._grace
        handle.s0_ran = True
        handle.grace_deadline_ms = t_g
        # S1 + S4: validate, then one SIGKILL
        verdict = self._validate(handle)
        if verdict is None:
            self._send(handle, signal.SIGKILL, t_g)
        else:
            handle.sends.append(self._not_sent(verdict))
        # S5 / S6 / S8
        self._reap_until(handle, t_g)
        return handle

    # --- S1 -------------------------------------------------------------

    def _validate(self, handle: ChildHandle) -> str | None:
        if not handle.identity_verifiable:
            return "not-sent(identity-unverifiable)"
        ops = self._ops
        try:
            if handle.pid <= 1 or handle.pgid != handle.pid or handle.pgid == ops.own_pgrp():
                return "not-sent(identity-mismatch)"
            if ops.getpgid(handle.pid) != handle.pgid or ops.getsid(handle.pid) != handle.pgid:
                return "not-sent(identity-mismatch)"
            if handle.start_ticks is not None and ops.start_ticks(handle.pid) != handle.start_ticks:
                return "not-sent(identity-mismatch)"
        except (OSError, ValueError):
            return "not-sent(identity-unverifiable)"
        return None

    # --- S4 -------------------------------------------------------------

    def _send(self, handle: ChildHandle, sig: int, t_g: int) -> None:
        start = self._ops.monotonic_ms()
        try:
            self._ops.killpg(handle.pgid, sig)
            exc: BaseException | None = None
        except Exception as caught:  # noqa: BLE001 - every result is recorded (SN-R 4-6)
            exc = caught
        returned = self._ops.monotonic_ms()
        result, anomaly = _send_result(exc)
        if anomaly:
            handle.anomalies.append(anomaly)
        handle.sends.append(
            {
                "signal": signal.Signals(sig).name,
                "result": result,
                "offset_ms": max(0, start - handle.created_ms),
                "late": returned >= t_g,
            }
        )

    @staticmethod
    def _not_sent(result: str) -> dict:
        return {"signal": "SIGKILL", "result": result, "offset_ms": 0, "late": False}

    # --- S5 / S6 / S8 -----------------------------------------------------

    def _reap_until(self, handle: ChildHandle, t_g: int) -> None:
        ops = self._ops
        while True:
            began = ops.monotonic_ms()
            try:
                reaped = ops.reap(handle.pid)
            except ReapError:
                # S8: reap-unknown; nothing more is sent, waited for or read.
                handle.state = HandleState.REAP_UNKNOWN
                handle.send_suppressed = True
                handle.anomalies.append("reap-error")
                return
            if reaped:
                handle.state = HandleState.REAPED
                return
            if began >= t_g:
                handle.state = HandleState.ABANDONED  # S6
                handle.anomalies.append("abandoned")
                return
            now = ops.monotonic_ms()
            if now >= t_g:
                handle.waits_skipped += 1
                continue  # the next attempt is the final one; no sleep at or after t_g
            ops.sleep_ms(min(self._slice, t_g - now))
