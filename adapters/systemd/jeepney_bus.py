"""``jeepney`` implementation of the bus transport (system bus only).

jeepney is a maintained, pure-Python D-Bus client; the wire protocol is not
reimplemented here. The systemd private manager socket is never used (D-1).
This is the only module that imports jeepney.
"""

from __future__ import annotations

import contextlib
from collections import deque

from jeepney import DBusAddress, HeaderFields, MatchRule, MessageType, message_bus, new_method_call
from jeepney.io.blocking import DBusConnection, open_dbus_connection

from .bus import (
    BusConnection,
    BusDisconnected,
    BusError,
    BusProtocolError,
    BusReply,
    BusRequest,
    BusSignal,
    BusTimeout,
    Variant,
)

# Bounded buffer for matched signals. An overflow evicts the oldest signal, which
# can only turn a completion into a timeout — an error, never a false success.
_SIGNAL_BUFFER = 1024
_MATCH_TIMEOUT_S = 5.0


def _to_wire(value):
    if isinstance(value, Variant):
        return (value.signature, _to_wire(value.value))
    if isinstance(value, tuple):
        return tuple(_to_wire(item) for item in value)
    if isinstance(value, list):
        return [_to_wire(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_wire(item) for key, item in value.items()}
    return value


def _from_wire(value):
    # A VARIANT arrives as ``(signature, value)``; callers that expect one
    # unwrap it themselves, because a bare tuple is also a STRUCT.
    return value


def _translate(exc: BaseException) -> Exception:
    if isinstance(exc, TimeoutError):
        return BusTimeout(str(exc))
    if isinstance(exc, (ConnectionError, EOFError, BrokenPipeError, OSError)):
        return BusDisconnected(f"{type(exc).__name__}: {exc}")
    return BusProtocolError(f"{type(exc).__name__}: {exc}")


class _Watch:
    def __init__(self, connection: DBusConnection, queue: deque, handle) -> None:
        self._connection = connection
        self._queue = queue
        self._handle = handle

    def next(self, *, timeout: float) -> BusSignal:
        try:
            message = self._connection.recv_until_filtered(self._queue, timeout=timeout)
        except Exception as exc:  # noqa: BLE001 - classified by _translate
            raise _translate(exc) from exc
        header = message.header
        fields = header.fields
        try:
            return BusSignal(
                path=str(fields.get(HeaderFields.path, "")),
                interface=str(fields.get(HeaderFields.interface, "")),
                member=str(fields.get(HeaderFields.member, "")),
                signature=str(fields.get(HeaderFields.signature, "")),
                body=tuple(_from_wire(item) for item in message.body),
            )
        except Exception as exc:  # noqa: BLE001
            raise BusProtocolError(str(exc)) from exc


class JeepneyConnection:
    def __init__(self, connection: DBusConnection) -> None:
        self._connection = connection
        self._handles: list = []

    def call(self, request: BusRequest, *, timeout: float) -> BusReply:
        address = DBusAddress(
            request.path, bus_name=request.destination, interface=request.interface
        )
        message = new_method_call(
            address, request.member, request.signature, _to_wire(request.body)
        )
        try:
            reply = self._connection.send_and_get_reply(message, timeout=timeout)
        except Exception as exc:  # noqa: BLE001
            raise _translate(exc) from exc
        if reply.header.message_type is MessageType.error:
            name = reply.header.fields.get(HeaderFields.error_name, "")
            text = reply.body[0] if reply.body and isinstance(reply.body[0], str) else ""
            raise BusError(str(name), text)
        if reply.header.message_type is not MessageType.method_return:
            raise BusProtocolError("unexpected reply message type")
        return BusReply(
            signature=str(reply.header.fields.get(HeaderFields.signature, "")),
            body=tuple(_from_wire(item) for item in reply.body),
        )

    def watch_signals(self, *, sender, path, interface, member, arg2=None) -> _Watch:
        # The bus daemon resolves the well-known ``sender`` to its owner, so only
        # that peer's signals are delivered. jeepney's local filter compares
        # ``sender`` literally against the *unique* name in the header, so the
        # local rule must not carry it or nothing would ever match.
        bus_rule = MatchRule(
            type="signal", sender=sender, path=path, interface=interface, member=member
        )
        local_rule = MatchRule(type="signal", path=path, interface=interface, member=member)
        if arg2 is not None:
            bus_rule.add_arg_condition(2, arg2)
            local_rule.add_arg_condition(2, arg2)
        queue: deque = deque(maxlen=_SIGNAL_BUFFER)
        # Filter first so nothing delivered after AddMatch can be missed.
        handle = self._connection.filter(local_rule, queue=queue)
        self._handles.append(handle)
        try:
            self._connection.send_and_get_reply(
                message_bus.AddMatch(bus_rule), timeout=_MATCH_TIMEOUT_S
            )
        except Exception as exc:  # noqa: BLE001
            raise _translate(exc) from exc
        return _Watch(self._connection, queue, handle)

    def close(self) -> None:
        for handle in self._handles:
            with contextlib.suppress(Exception):  # best-effort cleanup
                handle.close()
        with contextlib.suppress(Exception):
            self._connection.close()


def connect_system_bus() -> BusConnection:
    """Open a fresh connection to the system message bus."""
    try:
        return JeepneyConnection(open_dbus_connection(bus="SYSTEM"))
    except Exception as exc:  # noqa: BLE001
        raise BusDisconnected(f"{type(exc).__name__}: {exc}") from exc
