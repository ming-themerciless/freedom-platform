"""Composition root of ``deact <id> <a2> stop-post`` (RT-3).

Builds the adapters for the fixed production ``Layout`` and runs the shared
cleanup once. Writes exactly one bounded diagnostic line to standard error
(the system journal) and returns the terminal class's exit status. Nothing from
the environment, the caller or the network chooses a path or a parameter here:
they come from ``Layout`` constants and the A-2/H-1 chain.

An unexpected exception is reported as one fixed line naming only the
exception class, with no traceback, and exits 70: it never becomes success.
"""

from __future__ import annotations

import hashlib
import sys
from collections.abc import Callable

from adapters.systemd.bus import BusConnection
from adapters.systemd.manager import Deadlines, SystemdManagerAdapter
from adapters.systemd.polkit import PolkitAuthorityAdapter
from adapters.systemd.subject import ProcSubjectSource
from application.rp11.authority import Params
from application.rp11.canonical import ABSENT
from application.rp11.cleanup import CleanupProcedure, Invocation, Trigger
from application.rp11.paths import ActivationPaths, Layout
from application.rp11.pk import PkSeries
from application.rp11.sn import SignalContract

from .baseline import HostBaseline
from .fsops import (
    LocalActivationFs,
    LocalAttemptStore,
    LocalHostFacts,
    LocalLock,
    LocalRecordStore,
)
from .process import ForkSubjectLauncher, LinuxProcessOps, SystemClock

EX_INTERNAL = 70
_COMPLETION_SECONDS = 30.0


class StopPostServices:
    """``Services`` for the real host: deadlines from the H-1 parameters."""

    def __init__(self, connector: Callable[[], BusConnection], clock: SystemClock) -> None:
        self._connector = connector
        self._clock = clock

    def units(self, params: Params) -> SystemdManagerAdapter:
        return SystemdManagerAdapter(
            self._connector,
            deadlines=Deadlines(
                call_seconds=params.pk_call_ms / 1000, completion_seconds=_COMPLETION_SECONDS
            ),
            clock=lambda: self._clock.monotonic_ms() / 1000,
        )

    def pk(self, params: Params) -> PkSeries:
        ops = LinuxProcessOps(self._clock)
        return PkSeries(
            launcher=ForkSubjectLauncher(ops, ready_ms=params.pk_call_ms),
            subjects=ProcSubjectSource(),
            authority=PolkitAuthorityAdapter(
                self._connector, timeout_seconds=params.pk_call_ms / 1000
            ),
            contract=SignalContract(ops, grace_ms=params.reap_grace_ms, slice_ms=params.slice_ms),
            clock=self._clock,
            params=params,
        )

    def baseline(self, params: Params) -> HostBaseline:
        return HostBaseline(self.units(params))


def build_procedure(
    activation_id: str,
    a2_sha256: str,
    *,
    invocation_id: str,
    parent_pid: int,
    layout: Layout,
    services,
    clock,
    trigger: Trigger = Trigger.STOP_POST,
    attempt: int | None = None,
    holder_state: str = "deactivating",
) -> CleanupProcedure:
    paths = ActivationPaths(layout, activation_id)
    fs = LocalActivationFs(layout.owner)
    tool = fs.read_root_file(layout.tool, max_bytes=1 << 20, mode=0o644)
    return CleanupProcedure(
        Invocation(
            activation_id=activation_id,
            a2_sha256=a2_sha256,
            trigger=trigger,
            parent_pid=parent_pid,
            invocation_id=invocation_id,
            holder_state=holder_state,
        ),
        paths,
        fs=fs,
        journals=fs,
        attempts=LocalAttemptStore(
            var_tmp=layout.var_tmp, activation_id=activation_id, owner=layout.owner
        ),
        records=LocalRecordStore(paths.record_dir, layout.owner),
        lock=LocalLock(paths.lock_dir, layout.owner, clock),
        host=LocalHostFacts(
            boot_id_file=layout.boot_id_file, mountinfo=layout.mountinfo, run=layout.run
        ),
        services=services,
        tool_sha256=hashlib.sha256(tool).hexdigest() if tool is not None else ABSENT,
        attempt=attempt,
    )


def run_stop_post(
    activation_id: str,
    a2_sha256: str,
    *,
    invocation_id: str,
    parent_pid: int,
    layout: Layout | None = None,
    connector: Callable[[], BusConnection] | None = None,
) -> int:
    try:
        if connector is None:
            from adapters.systemd.jeepney_bus import connect_system_bus

            connector = connect_system_bus
        clock = SystemClock()
        procedure = build_procedure(
            activation_id,
            a2_sha256,
            invocation_id=invocation_id,
            parent_pid=parent_pid,
            layout=layout or Layout(),
            services=StopPostServices(connector, clock),
            clock=clock,
        )
        outcome = procedure.run()
    except Exception as exc:  # noqa: BLE001 - fail closed with a fixed, value-free line
        print(f"rp11-cl internal-error {activation_id} {type(exc).__name__}", file=sys.stderr)
        return EX_INTERNAL
    print(outcome.diagnostic(activation_id), file=sys.stderr)
    return outcome.terminal.exit_code
