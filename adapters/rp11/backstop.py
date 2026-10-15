"""Composition root of ``backstop <id> <a2>`` (RT-4).

Builds the adapters for the fixed production ``Layout`` and runs one firing of
``application.rp11.backstop.BackstopProcedure``. BS-1 … BS-3 and the terminal
disarm use the manager adapter with the default H-1 deadlines (they run before,
or without, a valid authority); the BS-4 bound and CL use the A-2/H-1 chain,
exactly as ``stop-post`` does (``adapters.rp11.stop_post``). Nothing from the
environment or the caller chooses a path, a parameter or a unit.

Output is fixed: one ``rp11-bs`` line per firing, plus CL's own line when BS-4
runs CL. An unexpected exception is one fixed line naming only its class and
exits 70: never a traceback, never success.
"""

from __future__ import annotations

import sys
from collections.abc import Callable

from adapters.systemd.bus import BusConnection
from application.rp11.authority import AuthorityError, Params, load_authority
from application.rp11.pk import PkMode, PkOutcome
from application.unit_control import UnitVerb
from application.rp11.backstop import BackstopOutcome, BackstopProcedure
from application.rp11.cleanup import Trigger
from application.rp11.paths import ActivationPaths, Layout

from .fsops import LocalActivationFs, LocalBackstopGuard, LocalRecordStore
from .process import SystemClock
from .stop_post import StopPostServices, build_procedure

EX_INTERNAL = 70


def build_backstop(
    activation_id: str,
    a2_sha256: str,
    *,
    invocation_id: str,
    parent_pid: int,
    layout: Layout,
    services: StopPostServices,
    clock,
) -> BackstopProcedure:
    paths = ActivationPaths(layout, activation_id)
    fs = LocalActivationFs(layout.owner)

    def limits() -> tuple[int, int]:
        try:
            params = load_authority(fs, paths, a2_sha256=a2_sha256, activation_id=activation_id).h1.params
        except AuthorityError:
            params = Params()
        return params.backstop_max, params.journal_max_bytes

    def grant_check() -> PkOutcome:
        """The bound's bounded ``seek-not-authorized`` series, as CL-4 runs it (same
        fixed parameters, subject and reaping). No valid authority, no operator or any
        failure is ``unconfirmed``: never a decision."""
        try:
            authority = load_authority(fs, paths, a2_sha256=a2_sha256, activation_id=activation_id)
            series = services.pk(authority.h1.params)
            return series.run(authority.h1.operator, UnitVerb.START, PkMode.SEEK_NOT_AUTHORIZED).outcome
        except Exception:  # noqa: BLE001 - fail closed: the owner is kept
            return PkOutcome.UNCONFIRMED

    def cleanup(k: int, holder_state: str):
        return build_procedure(
            activation_id,
            a2_sha256,
            invocation_id=invocation_id,
            parent_pid=parent_pid,
            layout=layout,
            services=services,
            clock=clock,
            trigger=Trigger.BACKSTOP,
            attempt=k,
            holder_state=holder_state,
        ).run()

    return BackstopProcedure(
        paths,
        units=services.units(Params()),
        records=LocalRecordStore(paths.record_dir, layout.owner),
        fs=fs,
        journals=fs,
        guard=LocalBackstopGuard(layout.store, activation_id, layout.owner),
        limits=limits,
        cleanup=cleanup,
        grant_check=grant_check,
    )


def run_backstop(
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
        procedure = build_backstop(
            activation_id,
            a2_sha256,
            invocation_id=invocation_id,
            parent_pid=parent_pid,
            layout=layout or Layout(),
            services=StopPostServices(connector, clock),
            clock=clock,
        )
        outcome: BackstopOutcome = procedure.run()
    except Exception as exc:  # noqa: BLE001 - fail closed with a fixed, value-free line
        print(f"rp11-bs internal-error {activation_id} {type(exc).__name__}", file=sys.stderr)
        return EX_INTERNAL
    for line in outcome.lines:
        print(line, file=sys.stderr)
    return outcome.exit_code
