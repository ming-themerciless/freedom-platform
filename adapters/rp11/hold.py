"""Composition root of ``hold <id> <a2>`` (RT-2), with SG-1.

``run_hold`` first installs the flag-only handlers (SG-1) — before the A-2
read, before any state operation — then builds the adapters for the fixed
production ``Layout`` and runs ``application.rp11.hold.HoldProcedure`` once.

SG-1 … SG-9 as implemented here:

* the set H = ``SIGTERM``, ``SIGINT``, ``SIGHUP``, ``SIGQUIT``, ``SIGUSR1``,
  ``SIGUSR2``, ``SIGALRM`` gets one handler that only sets ``stop_requested``:
  it raises, calls, writes, locks and sends nothing and never calls IGR. A
  second signal sets the same flag. The handler runs on the main thread between
  steps (CPython), and system calls interrupted by it are resumed (PEP 475);
* ``SIGPIPE`` stays ignored; ``SIGCHLD`` is left at its default (never ignore or
  no-wait, so the sole reaper keeps working); the mask is never set;
* a signal before SG-1 takes its default action and ends the process before
  any object exists.

Output is one bounded ``rp11-hold …`` line; an unexpected exception is one fixed
line naming only its class, after IGR has run, and exits 70.
"""

from __future__ import annotations

import signal
import sys
from collections.abc import Callable

from adapters.systemd.bus import BusConnection
from application.rp11.hold import HoldInvocation, HoldProcedure, StopFlag
from application.rp11.paths import ActivationPaths, Layout

from .fsops import LocalActivationFs, LocalHostFacts, LocalRecordStore
from .holdfs import LocalActivationLock, LocalHoldHost, LocalPublisher
from .process import SystemClock
from .stop_post import StopPostServices

EX_INTERNAL = 70
STOP_SIGNALS = (
    signal.SIGTERM,
    signal.SIGINT,
    signal.SIGHUP,
    signal.SIGQUIT,
    signal.SIGUSR1,
    signal.SIGUSR2,
    signal.SIGALRM,
)


def install_stop_handlers(flag: StopFlag) -> None:
    """SG-1: flag-only handlers for H; ``SIGPIPE`` ignored."""

    def handler(_signum, _frame) -> None:
        flag.requested = True

    for signum in STOP_SIGNALS:
        signal.signal(signum, handler)
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)


def build_hold(
    activation_id: str,
    a2_sha256: str,
    *,
    invocation_id: str,
    parent_pid: int,
    layout: Layout,
    services,
    clock,
    flag: Callable[[], bool],
) -> HoldProcedure:
    paths = ActivationPaths(layout, activation_id)
    fs = LocalActivationFs(layout.owner)
    return HoldProcedure(
        HoldInvocation(activation_id, a2_sha256, invocation_id, parent_pid),
        paths,
        fs=fs,
        journals=fs,
        host_fs=LocalHoldHost(layout.owner),
        publisher=LocalPublisher(layout.owner),
        records=LocalRecordStore(paths.record_dir, layout.owner),
        lock=LocalActivationLock(paths.lock_dir, layout.owner),
        host=LocalHostFacts(boot_id_file=layout.boot_id_file, mountinfo=layout.mountinfo, run=layout.run),
        services=services,
        clock=clock,
        flag=flag,
    )


def run_hold(
    activation_id: str,
    a2_sha256: str,
    *,
    invocation_id: str,
    parent_pid: int,
    layout: Layout | None = None,
    connector: Callable[[], BusConnection] | None = None,
) -> int:
    flag = StopFlag()
    install_stop_handlers(flag)  # SG-1: the first act of the role
    try:
        if connector is None:
            from adapters.systemd.jeepney_bus import connect_system_bus

            connector = connect_system_bus
        clock = SystemClock()
        procedure = build_hold(
            activation_id,
            a2_sha256,
            invocation_id=invocation_id,
            parent_pid=parent_pid,
            layout=layout or Layout(),
            services=StopPostServices(connector, clock),
            clock=clock,
            flag=flag,
        )
        outcome = procedure.run()
    except Exception as exc:  # noqa: BLE001 - fail closed with a fixed, value-free line
        print(f"rp11-hold internal-error {activation_id} {type(exc).__name__}", file=sys.stderr)
        return EX_INTERNAL
    print(outcome.line(activation_id), file=sys.stderr)
    return outcome.exit_code
