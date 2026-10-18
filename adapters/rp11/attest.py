"""Composition root of ``deact <id> <a2> attest`` (RT-5).

Builds the manager adapter and the shared cleanup for the fixed production ``Layout``
and runs ``application.rp11.attest.AttestProcedure`` once. The controlled first image has
already validated the two operands and emptied the environment; nothing from the
environment or the caller chooses a path, a unit or a parameter here, and no provenance
(parent PID, ``INVOCATION_ID``) exists to record. RT5.PRE uses the manager adapter with
the default H-1 deadlines, as ``backstop`` does for BS-1 (no authority is read before
it); the cleanup it then runs uses the A-2/H-1 chain exactly as ``stop-post`` does.

Output is one fixed line on standard error. An unexpected exception is one fixed line
naming only its class and exits 70: never a traceback, never success.
"""

from __future__ import annotations

import sys
from collections.abc import Callable

from adapters.systemd.bus import BusConnection
from application.rp11.attest import AttestProcedure
from application.rp11.authority import Params
from application.rp11.cleanup import Trigger
from application.rp11.paths import Layout
from application.unit_control import ControlSpecError, validate_activation_id

from .process import SystemClock
from .stop_post import StopPostServices, build_procedure

EX_INTERNAL = 70


def build_attest(
    activation_id: str,
    a2_sha256: str,
    *,
    layout: Layout,
    services: StopPostServices,
    clock,
) -> AttestProcedure:
    def cleanup(holder_state: str):
        return build_procedure(
            activation_id,
            a2_sha256,
            invocation_id=None,
            parent_pid=None,
            layout=layout,
            services=services,
            clock=clock,
            trigger=Trigger.ATTEST,
            holder_state=holder_state,
        ).run()

    return AttestProcedure(activation_id, services.units(Params()), cleanup)


def run_attest(
    activation_id: str,
    a2_sha256: str,
    *,
    layout: Layout | None = None,
    connector: Callable[[], BusConnection] | None = None,
) -> int:
    try:
        label = validate_activation_id(activation_id)
    except ControlSpecError:
        label = "invalid-activation"  # the entry validates first; never echo an unchecked value
    try:
        if connector is None:
            from adapters.systemd.jeepney_bus import connect_system_bus

            connector = connect_system_bus
        clock = SystemClock()
        outcome = build_attest(
            activation_id,
            a2_sha256,
            layout=layout or Layout(),
            services=StopPostServices(connector, clock),
            clock=clock,
        ).run()
    except Exception as exc:  # noqa: BLE001 - fail closed with a fixed, value-free line
        print(f"rp11-attest internal-error {label} {type(exc).__name__}", file=sys.stderr)
        return EX_INTERNAL
    print(outcome.line, file=sys.stderr)
    return outcome.exit_code
