"""DI-6: build the Polkit ``unix-process`` subject from ``/proc``.

PID, ``/proc/<pid>/stat`` field 22 (start ticks) and the real uid from
``/proc/<pid>/status``. Anything unreadable, replaced between reads, zero or
malformed is an error: a start time of ``0`` would make polkitd skip
verification (A-12.5), so it is never passed through.

PRODUCTION RISK (A-13.4, retained): PID/start-time identity is not race-free;
polkit's own source calls it "known broken". This slice does not use pidfd.
"""

from __future__ import annotations

from pathlib import Path

from application.unit_control import (
    ControlError,
    ControlOk,
    ControlResult,
    ControlSpecError,
    ProcessSubject,
)

_STAT_START_INDEX = 19  # field 22, counted from the token after ") " (field 3)


class ProcSubjectSource:
    def __init__(self, proc_root: Path = Path("/proc")) -> None:
        self._proc = proc_root

    def subject_for_pid(self, pid: int) -> ControlResult[ProcessSubject]:
        if isinstance(pid, bool) or not isinstance(pid, int) or not 1 <= pid <= 0xFFFFFFFF:
            return ControlError("invalid-request", "pid out of range")
        try:
            first = self._start_ticks(pid)
            uid = self._real_uid(pid)
            second = self._start_ticks(pid)
        except (OSError, ValueError) as exc:
            return ControlError("proc-unreadable", f"{type(exc).__name__}: {exc}")
        if first != second:
            return ControlError("proc-replaced", "start time changed while reading")
        try:
            return ControlOk(ProcessSubject(pid=pid, start_time=first, uid=uid))
        except ControlSpecError as exc:
            return ControlError("proc-malformed", str(exc))

    def _start_ticks(self, pid: int) -> int:
        raw = (self._proc / str(pid) / "stat").read_bytes().decode("utf-8")
        close = raw.rfind(")")
        if close < 0 or raw[close + 1 : close + 2] != " ":
            raise ValueError("stat has no comm terminator")
        tokens = raw[close + 2 :].split()
        if len(tokens) <= _STAT_START_INDEX:
            raise ValueError("stat has fewer than 22 fields")
        token = tokens[_STAT_START_INDEX]
        if not token.isascii() or not token.isdigit():
            raise ValueError("start time is not a decimal integer")
        return int(token)

    def _real_uid(self, pid: int) -> int:
        text = (self._proc / str(pid) / "status").read_bytes().decode("utf-8")
        for line in text.splitlines():
            if line.startswith("Uid:"):
                fields = line.split()[1:]
                if not fields or not fields[0].isascii() or not fields[0].isdigit():
                    raise ValueError("Uid line malformed")
                return int(fields[0])
        raise ValueError("no Uid line")
