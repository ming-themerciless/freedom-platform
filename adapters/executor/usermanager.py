"""The systemd user manager as the executor's kernel-ownership boundary (OS-6, third remediation).

Each admitted SA-2 invocation is its own transient **service** created with the user manager's
``StartTransientUnit``: systemd forks ``sudo`` straight into the new unit's cgroup, so there is
no interval in which the process exists outside its owned boundary. The unit is not the
supervisor's own unit: PID 1 and the user manager keep a populated invocation unit while the
supervisor restarts.

``RemainAfterExit=yes`` keeps the unit (and its typed ``ExecMain*`` status) readable after
``sudo`` exits; a failed unit is kept by the default ``CollectMode``. The manager is only ever
read through exact typed properties, never through a process list.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from adapters.executor.ownership import UNIT_PREFIX
from adapters.systemd.bus import (
    BusConnection,
    BusDisconnected,
    BusError,
    BusProtocolError,
    BusReply,
    BusRequest,
    BusTimeout,
    Variant,
)

SYSTEMD = "org.freedesktop.systemd1"
MANAGER_PATH = "/org/freedesktop/systemd1"
MANAGER_IFACE = "org.freedesktop.systemd1.Manager"
UNIT_IFACE = "org.freedesktop.systemd1.Unit"
SERVICE_IFACE = "org.freedesktop.systemd1.Service"
PROPERTIES_IFACE = "org.freedesktop.DBus.Properties"
CALL_SECONDS = 10.0
#: Variables systemd is known to inject into a service itself (not through the manager's ``Environment``).
#: Unsetting these and the manager snapshot is defense in depth: the snapshot and ``StartTransientUnit`` are
#: separate calls, so exact pre-sudo environment equality is deliberately not a security premise.  The fixed
#: privileged vector uses Python ``-I -S`` and its ``stop`` entry reads no environment variable.
GENERATED_ENVIRONMENT = frozenset({
    "INVOCATION_ID", "SYSTEMD_EXEC_PID", "MANAGERPID", "MANAGERPIDFDID", "MEMORY_PRESSURE_WATCH", "MEMORY_PRESSURE_WRITE",
    "JOURNAL_STREAM", "NOTIFY_SOCKET", "WATCHDOG_PID", "WATCHDOG_USEC", "LISTEN_PID", "LISTEN_FDS", "LISTEN_FDNAMES",
    "CREDENTIALS_DIRECTORY", "RUNTIME_DIRECTORY", "STATE_DIRECTORY", "CACHE_DIRECTORY", "LOGS_DIRECTORY",
    "CONFIGURATION_DIRECTORY", "TERM", "EXIT_CODE", "EXIT_STATUS", "SERVICE_RESULT", "MAINPID", "REMOTE_ADDR", "REMOTE_PORT",
})
_NO_SUCH_UNIT = "org.freedesktop.systemd1.NoSuchUnit"


class ManagerUnavailable(Exception):
    """The manager did not answer a read, or answered something that is not the typed value asked for."""


class StartRefused(Exception):
    """The manager answered ``StartTransientUnit`` with an ERROR: no unit was created (definite)."""


class AmbiguousStart(Exception):
    """``StartTransientUnit`` got no reply (timeout, disconnect, protocol): the unit may exist."""


@dataclass(frozen=True)
class UnitView:
    load_state: str
    active_state: str
    sub_state: str
    invocation_id: str  # 32 hex
    control_group: str  # relative to the cgroup root; "" when the unit has no cgroup
    main_pid: int
    exec_main_code: int  # CLD_EXITED=1, CLD_KILLED=2, CLD_DUMPED=3; 0 = the main process never exited
    exec_main_status: int
    result: str

    @property
    def main_exited(self) -> bool:
        return self.exec_main_code != 0 and self.main_pid == 0


class UserManager(Protocol):
    def ready(self) -> None:
        """Raise ``ManagerUnavailable`` unless the manager answers and is running."""

    def unit(self, name: str) -> UnitView | None:
        """The unit's typed state; ``None`` only when the manager affirmatively has no such unit."""

    def invocation_units(self) -> tuple[str, ...]:
        """Every unit the manager has loaded under the invocation name pattern; ``ManagerUnavailable`` unless it can tell."""

    def start_transient(self, name: str, argv: tuple[str, ...], *, executable: str, environment: tuple[str, ...]) -> None: ...

    def stop(self, name: str) -> None: ...

    def reset_failed(self, name: str) -> None: ...


def _path(name: str) -> str:
    """The manager's object path for a unit name (bus path escaping of the characters it allows)."""
    out = []
    for char in name:
        if char.isascii() and (char.isalnum()):
            out.append(char)
        else:
            out.append(f"_{ord(char):02x}")
    return "/org/freedesktop/systemd1/unit/" + "".join(out)


def _variant(signature: str, value) -> Variant:
    return Variant(signature, value)


class BusUserManager:
    def __init__(self, connector: Callable[[], BusConnection], *, call_seconds: float = CALL_SECONDS) -> None:
        self._connector = connector
        self._call = call_seconds
        self._connection: BusConnection | None = None

    def _bus(self) -> BusConnection:
        if self._connection is None:
            try:
                self._connection = self._connector()
            except (BusDisconnected, BusProtocolError, OSError) as error:
                raise ManagerUnavailable("connect") from error
        return self._connection

    def _drop(self) -> None:
        connection, self._connection = self._connection, None
        close = getattr(connection, "close", None)
        if close is not None:
            try:
                close()
            except Exception:  # noqa: BLE001 - a dead connection is simply replaced
                pass

    def _send(self, path: str, interface: str, member: str, signature: str = "", body: tuple = ()) -> BusReply:
        try:
            return self._bus().call(BusRequest(SYSTEMD, path, interface, member, signature, body), timeout=self._call)
        except (BusTimeout, BusDisconnected, BusProtocolError):
            self._drop()
            raise

    # --- reads ---------------------------------------------------------------

    def ready(self) -> None:
        try:
            reply = self._send(MANAGER_PATH, PROPERTIES_IFACE, "Get", "ss", (MANAGER_IFACE, "SystemState"))
        except (BusError, BusTimeout, BusDisconnected, BusProtocolError) as error:
            raise ManagerUnavailable("ping") from error
        state = _decode(reply, "s")
        if state not in ("running", "degraded"):
            raise ManagerUnavailable("not-running")

    def invocation_units(self) -> tuple[str, ...]:
        pattern = f"{UNIT_PREFIX}*.service"
        try:
            reply = self._send(MANAGER_PATH, MANAGER_IFACE, "ListUnitsByPatterns", "asas", ([], [pattern]))
        except (BusError, BusTimeout, BusDisconnected, BusProtocolError) as error:
            raise ManagerUnavailable("list-units") from error
        if reply.signature != "a(ssssssouso)" or len(reply.body) != 1 or not isinstance(reply.body[0], (list, tuple)):
            raise ManagerUnavailable("list-units-malformed")
        names = []
        for item in reply.body[0]:
            if not isinstance(item, (list, tuple)) or len(item) != 10 or not isinstance(item[0], str):
                raise ManagerUnavailable("list-units-malformed")
            names.append(item[0])
        return tuple(sorted(names))

    def manager_environment(self) -> tuple[str, ...]:
        """Snapshot names the manager would hand a new unit, for best-effort minimization at creation."""
        try:
            reply = self._send(MANAGER_PATH, PROPERTIES_IFACE, "Get", "ss", (MANAGER_IFACE, "Environment"))
        except (BusError, BusTimeout, BusDisconnected, BusProtocolError) as error:
            raise ManagerUnavailable("environment") from error
        value = _decode(reply, "as")
        if not isinstance(value, (list, tuple)) or not all(isinstance(item, str) for item in value):
            raise ManagerUnavailable("environment-malformed")
        return tuple(item.split("=", 1)[0] for item in value if "=" in item)

    def unit(self, name: str) -> UnitView | None:
        try:
            reply = self._send(MANAGER_PATH, MANAGER_IFACE, "GetUnit", "s", (name,))
        except BusError as error:
            if error.name == _NO_SUCH_UNIT:
                return None
            raise ManagerUnavailable("get-unit") from error
        except (BusTimeout, BusDisconnected, BusProtocolError) as error:
            raise ManagerUnavailable("get-unit") from error
        if reply.signature != "o" or len(reply.body) != 1 or reply.body[0] != _path(name):
            raise ManagerUnavailable("get-unit-malformed")
        unit_props = self._all(reply.body[0], UNIT_IFACE)
        service_props = self._all(reply.body[0], SERVICE_IFACE)
        try:
            return UnitView(
                load_state=_typed(unit_props, "LoadState", "s", str),
                active_state=_typed(unit_props, "ActiveState", "s", str),
                sub_state=_typed(unit_props, "SubState", "s", str),
                invocation_id=_invocation(unit_props),
                control_group=_typed(service_props, "ControlGroup", "s", str),
                main_pid=_typed(service_props, "MainPID", "u", int),
                exec_main_code=_typed(service_props, "ExecMainCode", "i", int),
                exec_main_status=_typed(service_props, "ExecMainStatus", "i", int),
                result=_typed(service_props, "Result", "s", str),
            )
        except KeyError as error:
            raise ManagerUnavailable("property-malformed") from error

    def _all(self, path: str, interface: str) -> dict:
        try:
            reply = self._send(path, PROPERTIES_IFACE, "GetAll", "s", (interface,))
        except BusError as error:
            raise ManagerUnavailable("get-all") from error
        except (BusTimeout, BusDisconnected, BusProtocolError) as error:
            raise ManagerUnavailable("get-all") from error
        if reply.signature != "a{sv}" or len(reply.body) != 1 or not isinstance(reply.body[0], dict):
            raise ManagerUnavailable("get-all-malformed")
        return reply.body[0]

    # --- the one creation, and the cleanup that may be repeated ---------------

    def start_transient(self, name: str, argv: tuple[str, ...], *, executable: str, environment: tuple[str, ...]) -> None:
        # This snapshot cannot be atomic with StartTransientUnit.  It minimizes ambient input but does not authorize
        # the root transition; that boundary is the fixed sudo argv and the isolated, environment-free stop helper.
        unset = sorted((set(self.manager_environment()) | GENERATED_ENVIRONMENT) - {"PATH"})
        properties = [
            ("Description", _variant("s", "Freedom Blades executor SA-2 stop")),
            ("Type", _variant("s", "exec")),
            ("RemainAfterExit", _variant("b", True)),
            ("WorkingDirectory", _variant("s", "/")),
            ("Environment", _variant("as", list(environment))),
            ("UnsetEnvironment", _variant("as", unset)),
            ("ExecStart", _variant("a(sasb)", [(executable, list(argv), False)])),
        ]
        try:
            reply = self._send(MANAGER_PATH, MANAGER_IFACE, "StartTransientUnit", "ssa(sv)a(sa(sv))", (name, "fail", properties, []))
        except BusError as error:
            raise StartRefused(error.name) from error
        except (BusTimeout, BusDisconnected, BusProtocolError) as error:
            raise AmbiguousStart(type(error).__name__) from error
        if reply.signature != "o" or len(reply.body) != 1 or not str(reply.body[0]).startswith("/org/freedesktop/systemd1/job/"):
            raise AmbiguousStart("malformed-reply")

    def stop(self, name: str) -> None:
        self._best_effort("StopUnit", name, "replace")

    def reset_failed(self, name: str) -> None:
        self._best_effort("ResetFailedUnit", name)

    def _best_effort(self, member: str, name: str, mode: str | None = None) -> None:
        signature, body = ("ss", (name, mode)) if mode is not None else ("s", (name,))
        try:
            self._send(MANAGER_PATH, MANAGER_IFACE, member, signature, body)
        except BusError as error:
            if error.name != _NO_SUCH_UNIT and not error.name.endswith("NoSuchUnit"):
                raise ManagerUnavailable(member) from error
        except (BusTimeout, BusDisconnected, BusProtocolError) as error:
            raise ManagerUnavailable(member) from error


def _decode(reply: BusReply, signature: str):
    if reply.signature != "v" or len(reply.body) != 1:
        raise ManagerUnavailable("malformed")
    variant = reply.body[0]
    if not (isinstance(variant, tuple) and len(variant) == 2) or variant[0] != signature:
        raise ManagerUnavailable("malformed")
    return variant[1]


def _typed(props: dict, name: str, signature: str, kind: type):
    item = props[name]
    if not (isinstance(item, tuple) and len(item) == 2) or item[0] != signature:
        raise KeyError(name)
    value = item[1]
    if type(value) is not kind:
        raise KeyError(name)
    return value


def _invocation(props: dict) -> str:
    item = props["InvocationID"]
    if not (isinstance(item, tuple) and len(item) == 2) or item[0] != "ay":
        raise KeyError("InvocationID")
    value = item[1]
    if not isinstance(value, (bytes, bytearray)) or len(value) not in (0, 16):
        raise KeyError("InvocationID")
    return bytes(value).hex()
