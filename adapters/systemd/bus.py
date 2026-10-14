"""Injectable system-bus transport for the Route 3 adapter.

The adapter speaks to this small protocol; the D-Bus wire protocol is left to a
maintained client (``jeepney_bus``). Tests substitute a fake. Nothing here knows
about systemd or Polkit.

Values are plain Python (``int``, ``str``, ``bool``, ``bytes``, ``tuple`` for a
STRUCT, ``list`` for an ARRAY, ``dict`` for a DICT) except a VARIANT, which is
``Variant(signature, value)`` so that integer widths stay explicit.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Variant:
    signature: str
    value: object


@dataclass(frozen=True)
class BusRequest:
    destination: str
    path: str
    interface: str
    member: str
    signature: str = ""
    body: tuple = ()


@dataclass(frozen=True)
class BusReply:
    signature: str
    body: tuple


@dataclass(frozen=True)
class BusSignal:
    path: str
    interface: str
    member: str
    signature: str
    body: tuple


class BusError(Exception):
    """The peer answered with a D-Bus ERROR message."""

    def __init__(self, name: str, message: str = "") -> None:
        super().__init__(f"{name}: {message}" if message else name)
        self.name = name
        self.message = message


class BusTimeout(Exception):
    """The client deadline elapsed. Says nothing about what the peer did."""


class BusDisconnected(Exception):
    """The connection was lost, or could not be made."""


class BusProtocolError(Exception):
    """A message could not be decoded or violated the protocol."""


class SignalWatch(Protocol):
    def next(self, *, timeout: float) -> BusSignal:
        """Return the next matching signal; raise ``BusTimeout`` / ``BusDisconnected``."""
        ...


class BusConnection(Protocol):
    def call(self, request: BusRequest, *, timeout: float) -> BusReply: ...

    def watch_signals(
        self, *, sender: str, path: str, interface: str, member: str, arg2: str | None = None
    ) -> SignalWatch:
        """Install the match rule on the bus before returning."""
        ...

    def close(self) -> None: ...


BusConnector = Callable[[], BusConnection]
