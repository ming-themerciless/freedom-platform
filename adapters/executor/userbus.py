"""The executor's connection to its own systemd user manager (the user session bus).

Kept out of ``adapters.systemd.jeepney_bus``, which is part of the controlled RP-11 artifact: the
executor's transport must not change the artifact. It reuses that module's connection class.
"""

from __future__ import annotations

from jeepney.io.blocking import open_dbus_connection

from adapters.systemd.bus import BusConnection, BusDisconnected
from adapters.systemd.jeepney_bus import JeepneyConnection


def connect_user_bus(uid: int) -> BusConnection:
    """Open a fresh connection to ``/run/user/<uid>/bus``; no environment is read."""
    try:
        return JeepneyConnection(open_dbus_connection(bus=f"unix:path=/run/user/{uid}/bus"))
    except Exception as exc:  # noqa: BLE001
        raise BusDisconnected(f"{type(exc).__name__}: {exc}") from exc
