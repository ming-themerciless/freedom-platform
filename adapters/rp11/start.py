"""Composition root for the SA-1 ``start`` role.

The caller supplies only the four validated fields of ``HolderSpec``. The
systemd adapter derives the unit name and both role command vectors. Output is
fixed and a DI-2 error is never retried.
"""

from __future__ import annotations

import sys
from collections.abc import Callable

from adapters.systemd.bus import BusConnection
from adapters.systemd.manager import SystemdManagerAdapter
from application.rp11.start import StartEnd, StartProcedure, validate_start_durations
from application.unit_control import HolderSpec, UnitControl

EX_INTERNAL = 70


def run_start(
    activation_id: str,
    artifact_sha256: str,
    runtime_max_seconds: int,
    timeout_stop_seconds: int,
    *,
    units: UnitControl | None = None,
    connector: Callable[[], BusConnection] | None = None,
) -> int:
    try:
        validate_start_durations(runtime_max_seconds, timeout_stop_seconds)
        if units is None:
            if connector is None:
                from adapters.systemd.jeepney_bus import connect_system_bus

                connector = connect_system_bus
            units = SystemdManagerAdapter(connector)
        outcome = StartProcedure(units).run(
            HolderSpec(
                activation_id=activation_id,
                artifact_sha256=artifact_sha256,
                runtime_max_seconds=runtime_max_seconds,
                timeout_stop_seconds=timeout_stop_seconds,
            )
        )
    except Exception:  # noqa: BLE001 - fixed, value-free failure at the outer boundary
        print("rp11-start internal-error", file=sys.stderr)
        return EX_INTERNAL
    if outcome.end is StartEnd.STARTED:
        print("rp11-start started", file=sys.stderr)
    elif outcome.end is StartEnd.REFUSED:
        print(f"rp11-start refused {outcome.detail}", file=sys.stderr)
    else:
        certainty = "effect-not-confirmed" if outcome.effect_not_confirmed else "effect-not-sent"
        print(f"rp11-start error {certainty}", file=sys.stderr)
    return outcome.exit_code
