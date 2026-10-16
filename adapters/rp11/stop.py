"""Composition root for the SA-2 ``stop`` role.

The caller supplies nothing: the systemd adapter owns the one fixed unit and the
job mode. Output is fixed and a DI-S error is never retried.
"""

from __future__ import annotations

import sys
from collections.abc import Callable

from adapters.systemd.bus import BusConnection
from adapters.systemd.manager import SystemdManagerAdapter
from application.rp11.stop import StopEnd, StopProcedure
from application.unit_control import UnitControl

EX_INTERNAL = 70


def run_stop(
    *,
    units: UnitControl | None = None,
    connector: Callable[[], BusConnection] | None = None,
) -> int:
    try:
        if units is None:
            if connector is None:
                from adapters.systemd.jeepney_bus import connect_system_bus

                connector = connect_system_bus
            units = SystemdManagerAdapter(connector)
        outcome = StopProcedure(units).run()
    except Exception:  # noqa: BLE001 - fixed, value-free failure at the outer boundary
        print("rp11-stop internal-error", file=sys.stderr)
        return EX_INTERNAL
    if outcome.end is StopEnd.STOPPED:
        print("rp11-stop stopped", file=sys.stderr)
    elif outcome.end is StopEnd.REFUSED:
        print(f"rp11-stop refused {outcome.detail}", file=sys.stderr)
    else:
        certainty = "effect-not-confirmed" if outcome.effect_not_confirmed else "effect-not-sent"
        print(f"rp11-stop error {certainty}", file=sys.stderr)
    return outcome.exit_code
