"""DI-5: the non-interactive Polkit decision, over the system bus.

Request shape is pinned by D-2: subject ``("unix-process", {pid u, start-time t,
uid i})``, action ``org.freedesktop.systemd1.manage-units``, details exactly
``unit`` and ``verb``, flags ``0`` (no interaction, no always-check), empty
cancellation id. Result mapping is D-6; every D-Bus ERROR, wrong signature,
inconsistent reply or malformed/oversized details map is an error, never a
decision. The subject is revalidated here, before the bus is opened.
"""

from __future__ import annotations

from application.unit_control import (
    CAPTURE_UNIT,
    ControlError,
    ControlSpecError,
    PolkitAuthorized,
    PolkitNotAuthorized,
    PolkitOutcome,
    ProcessSubject,
    UnitVerb,
)

from .bus import (
    BusConnector,
    BusDisconnected,
    BusError,
    BusProtocolError,
    BusRequest,
    BusTimeout,
    Variant,
)

POLKIT = "org.freedesktop.PolicyKit1"
AUTHORITY_PATH = "/org/freedesktop/PolicyKit1/Authority"
AUTHORITY_IFACE = "org.freedesktop.PolicyKit1.Authority"
ACTION_ID = "org.freedesktop.systemd1.manage-units"
CHECK_FLAGS_NONE = 0

# The reply's details map is bounded by entry count and by the UTF-8 bytes of all
# its keys and values together — the accepted 65,536-byte cap (R-11.1) — so one
# very large key or value cannot pass under the count.
_MAX_REPLY_DETAILS = 256
_MAX_REPLY_DETAIL_BYTES = 65_536


def _revalidated(subject: ProcessSubject) -> ProcessSubject:
    """A fresh subject built from ``subject``'s fields; raises on anything else.

    A frozen dataclass can still be forced or subclassed, so the exact type is
    required and construction-time validation is rerun on a new object.
    """
    if type(subject) is not ProcessSubject:
        raise ControlSpecError("subject must be a ProcessSubject")
    return ProcessSubject(pid=subject.pid, start_time=subject.start_time, uid=subject.uid)


class PolkitAuthorityAdapter:
    def __init__(self, connector: BusConnector, *, timeout_seconds: float = 10.0) -> None:
        if isinstance(timeout_seconds, bool) or not 0 < timeout_seconds <= 600:
            raise ValueError("timeout_seconds must be in (0, 600]")
        self._connector = connector
        self._timeout = timeout_seconds

    def check(self, subject: ProcessSubject, verb: UnitVerb) -> PolkitOutcome:
        try:
            subject = _revalidated(subject)
        except (ControlSpecError, AttributeError, TypeError) as exc:
            return ControlError("invalid-request", str(exc))
        try:
            verb = UnitVerb(verb)
        except (ValueError, TypeError):
            return ControlError("invalid-request", "verb is not start or stop")
        request = BusRequest(
            POLKIT,
            AUTHORITY_PATH,
            AUTHORITY_IFACE,
            "CheckAuthorization",
            "(sa{sv})sa{ss}us",
            (
                (
                    "unix-process",
                    {
                        "pid": Variant("u", subject.pid),
                        "start-time": Variant("t", subject.start_time),
                        "uid": Variant("i", subject.uid),
                    },
                ),
                ACTION_ID,
                {"unit": CAPTURE_UNIT, "verb": verb.value},
                CHECK_FLAGS_NONE,
                "",
            ),
        )
        try:
            connection = self._connector()
        except (BusDisconnected, BusProtocolError, BusTimeout, BusError, OSError) as exc:
            return ControlError("connect-failed", str(exc))
        try:
            reply = connection.call(request, timeout=self._timeout)
        except BusError as exc:
            # The four Polkit ERROR names are not mapped to not-authorized (D-3).
            return ControlError(exc.name, exc.message)
        except BusTimeout as exc:
            return ControlError("timeout", str(exc))
        except BusDisconnected as exc:
            return ControlError("disconnected", str(exc))
        except BusProtocolError as exc:
            return ControlError("invalid-reply", str(exc))
        finally:
            connection.close()
        return _map_reply(reply.signature, reply.body)


def _map_reply(signature: str, body: tuple) -> PolkitOutcome:
    if signature != "(bba{ss})" or len(body) != 1:
        return ControlError("invalid-reply", "unexpected CheckAuthorization signature")
    result = body[0]
    if not (isinstance(result, tuple) and len(result) == 3):
        return ControlError("invalid-reply", "malformed CheckAuthorization result")
    authorized, challenge, details = result
    if not isinstance(authorized, bool) or not isinstance(challenge, bool):
        return ControlError("invalid-reply", "non-boolean decision")
    if not _details_ok(details):
        return ControlError("invalid-reply", "malformed or oversized details")
    if authorized and challenge:
        return ControlError("invalid-reply", "authorized and challenge both set")
    if authorized:
        return PolkitAuthorized()
    return PolkitNotAuthorized(challenge=challenge)


def _details_ok(details: object) -> bool:
    """Exactly ``a{ss}``: a plain dict of plain, UTF-8-encodable strings, within bounds."""
    if type(details) is not dict or len(details) > _MAX_REPLY_DETAILS:
        return False
    total = 0
    for key, value in details.items():
        if type(key) is not str or type(value) is not str:
            return False
        # Characters never exceed bytes, so this pre-check avoids encoding a huge string.
        if total + len(key) + len(value) > _MAX_REPLY_DETAIL_BYTES:
            return False
        try:
            total += len(key.encode("utf-8")) + len(value.encode("utf-8"))
        except UnicodeEncodeError:
            return False
        if total > _MAX_REPLY_DETAIL_BYTES:
            return False
    return True
