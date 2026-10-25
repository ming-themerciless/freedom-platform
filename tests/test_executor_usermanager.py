"""The user-manager adapter: one StartTransientUnit with the fixed vector, strictly typed reads."""

from __future__ import annotations

import pytest

from adapters.executor.usermanager import (
    AmbiguousStart,
    GENERATED_ENVIRONMENT,
    BusUserManager,
    ManagerUnavailable,
    StartRefused,
)
from adapters.systemd.bus import BusDisconnected, BusError, BusProtocolError, BusReply, BusTimeout, Variant

NAME = "freedom-executor-stop-0123456789abcdef.service"
PATH = "/org/freedesktop/systemd1/unit/freedom_2dexecutor_2dstop_2d0123456789abcdef_2eservice"


class Bus:
    def __init__(self, handler):
        self.handler, self.requests, self.closed = handler, [], False

    def call(self, request, *, timeout):
        self.requests.append(request)
        result = self.handler(request)
        if isinstance(result, Exception):
            raise result
        return result

    def close(self):
        self.closed = True


def good_unit(**changes):
    unit = {
        "LoadState": ("s", "loaded"), "ActiveState": ("s", "active"), "SubState": ("s", "exited"),
        "InvocationID": ("ay", bytes.fromhex("ab" * 16)),
    }
    service = {
        "ControlGroup": ("s", ""), "MainPID": ("u", 0), "ExecMainCode": ("i", 1), "ExecMainStatus": ("i", 0), "Result": ("s", "success"),
    }
    unit.update({k: v for k, v in changes.items() if k in unit})
    service.update({k: v for k, v in changes.items() if k in service})
    return unit, service


def unit_handler(unit, service):
    def handle(request):
        if request.member == "GetUnit":
            return BusReply("o", (PATH,))
        if request.member == "GetAll":
            return BusReply("a{sv}", ({"org.freedesktop.systemd1.Unit": unit}.get(request.body[0]) or service,))
        raise AssertionError(request.member)

    return handle


def manager(handler) -> tuple[BusUserManager, Bus]:
    bus = Bus(handler)
    return BusUserManager(lambda: bus), bus


def test_a_unit_is_read_as_exact_typed_values():
    mgr, _ = manager(unit_handler(*good_unit()))
    view = mgr.unit(NAME)
    assert (view.active_state, view.sub_state, view.invocation_id, view.control_group, view.main_pid) == (
        "active", "exited", "ab" * 16, "", 0)
    assert view.main_exited and (view.exec_main_code, view.exec_main_status, view.result) == (1, 0, "success")


def test_a_running_unit_has_not_exited():
    mgr, _ = manager(unit_handler(*good_unit(MainPID=("u", 77), ExecMainCode=("i", 0), ControlGroup=("s", "/user.slice/x"))))
    assert not mgr.unit(NAME).main_exited


def test_no_such_unit_is_the_only_affirmative_absence():
    mgr, _ = manager(lambda r: BusError("org.freedesktop.systemd1.NoSuchUnit", "x"))
    assert mgr.unit(NAME) is None
    for failure in (BusError("org.freedesktop.DBus.Error.AccessDenied"), BusTimeout("t"), BusDisconnected("d"), BusProtocolError("p")):
        other, _ = manager(lambda r, f=failure: f)
        with pytest.raises(ManagerUnavailable):
            other.unit(NAME)


@pytest.mark.parametrize(
    "changes",
    [
        {"ActiveState": ("u", 1)},
        {"InvocationID": ("ay", b"short")},
        {"MainPID": ("i", 0)},
        {"ExecMainCode": ("u", 1)},
        {"Result": ("s", b"bytes")},
        {"ExecMainStatus": ("i", True)},
    ],
)
def test_wrongly_typed_properties_are_unavailable_never_a_guess(changes):
    mgr, _ = manager(unit_handler(*good_unit(**changes)))
    with pytest.raises(ManagerUnavailable):
        mgr.unit(NAME)


def test_a_missing_property_or_wrong_object_path_is_unavailable():
    unit, service = good_unit()
    del service["Result"]
    mgr, _ = manager(unit_handler(unit, service))
    with pytest.raises(ManagerUnavailable):
        mgr.unit(NAME)
    other, _ = manager(lambda r: BusReply("o", ("/org/freedesktop/systemd1/unit/other",)))
    with pytest.raises(ManagerUnavailable):
        other.unit(NAME)


def start_handler(reply=None, environment=("HOME=/home/x", "PATH=/bin", "LANG=C")):
    def handle(request):
        if request.member == "Get":
            return BusReply("v", (("as", list(environment)),))
        assert request.member == "StartTransientUnit"
        return reply or BusReply("o", ("/org/freedesktop/systemd1/job/9",))

    return handle


def test_start_transient_sends_the_fixed_vector_and_environment_once():
    mgr, bus = manager(start_handler())
    argv = ("sudo", "-n", "/usr/bin/python3.14", "-I", "-S", "/x/rp11_h1.py", "stop")
    mgr.start_transient(NAME, argv, executable="/usr/bin/sudo", environment=("PATH=/usr/bin:/bin",))
    (start,) = [r for r in bus.requests if r.member == "StartTransientUnit"]
    name, mode, properties, aux = start.body
    assert (name, mode, aux, start.signature) == (NAME, "fail", [], "ssa(sv)a(sa(sv))")
    props = dict(properties)
    assert props["ExecStart"] == Variant("a(sasb)", [("/usr/bin/sudo", list(argv), False)])
    assert props["Environment"] == Variant("as", ["PATH=/usr/bin:/bin"])
    unset = props["UnsetEnvironment"]
    assert unset.signature == "as" and unset.value == sorted({"HOME", "LANG"} | GENERATED_ENVIRONMENT)
    # Manager-inherited AND systemd-generated names are all unset; the one fixed PATH is never unset.
    assert {"HOME", "LANG", "INVOCATION_ID", "SYSTEMD_EXEC_PID", "MANAGERPID", "MANAGERPIDFDID",
            "MEMORY_PRESSURE_WATCH", "MEMORY_PRESSURE_WRITE", "JOURNAL_STREAM"} <= set(unset.value) and "PATH" not in unset.value
    assert props["Type"] == Variant("s", "exec") and props["RemainAfterExit"] == Variant("b", True)


@pytest.mark.parametrize(
    "failure,expected",
    [
        (BusError("org.freedesktop.systemd1.UnitExists"), StartRefused),
        (BusTimeout("t"), AmbiguousStart),
        (BusDisconnected("d"), AmbiguousStart),
        (BusProtocolError("p"), AmbiguousStart),
    ],
)
def test_start_failures_are_classified_definite_or_ambiguous(failure, expected):
    def handle(request):
        return BusReply("v", (("as", ["PATH=/bin"]),)) if request.member == "Get" else failure

    mgr, _ = manager(handle)
    with pytest.raises(expected):
        mgr.start_transient(NAME, ("sudo",), executable="/usr/bin/sudo", environment=())


def test_a_malformed_start_reply_is_ambiguous_not_success():
    mgr, _ = manager(start_handler(BusReply("s", ("hello",))))
    with pytest.raises(AmbiguousStart):
        mgr.start_transient(NAME, ("sudo",), executable="/usr/bin/sudo", environment=())


def test_stop_and_reset_tolerate_an_absent_unit_but_not_a_dead_manager():
    mgr, _ = manager(lambda r: BusError("org.freedesktop.systemd1.NoSuchUnit"))
    mgr.stop(NAME)
    mgr.reset_failed(NAME)
    down, _ = manager(lambda r: BusTimeout("t"))
    with pytest.raises(ManagerUnavailable):
        down.stop(NAME)


def test_ready_requires_a_running_manager_and_a_failed_connection_is_replaced():
    mgr, _ = manager(lambda r: BusReply("v", (("s", "running"),)))
    mgr.ready()
    starting, _ = manager(lambda r: BusReply("v", (("s", "starting"),)))
    with pytest.raises(ManagerUnavailable):
        starting.ready()
    bus = Bus(lambda r: BusTimeout("t"))
    made = []
    flaky = BusUserManager(lambda: made.append(1) or bus)
    for _ in range(2):
        with pytest.raises(ManagerUnavailable):
            flaky.ready()
    assert len(made) == 2 and bus.closed  # a timed-out connection is dropped and re-made
    broken = BusUserManager(lambda: (_ for _ in ()).throw(BusDisconnected("no bus")))
    with pytest.raises(ManagerUnavailable):
        broken.ready()


def test_the_vector_is_never_wrapped_to_clean_the_environment():
    mgr, bus = manager(start_handler())
    argv = ("sudo", "-n", "/usr/bin/python3.14", "-I", "-S", "/x/rp11_h1.py", "stop")
    mgr.start_transient(NAME, argv, executable="/usr/bin/sudo", environment=("PATH=/usr/bin:/bin",))
    (start,) = [r for r in bus.requests if r.member == "StartTransientUnit"]
    (execstart,) = [value for key, value in start.body[2] if key == "ExecStart"]
    assert execstart.value == [("/usr/bin/sudo", list(argv), False)]  # no env, no shell: the executable and argv are the vector


def test_invocation_units_lists_every_loaded_matching_unit_and_nothing_unless_the_manager_says_so():
    seen = []

    def handle(request):
        seen.append(request)
        row = lambda name: (name, "d", "loaded", "failed", "failed", "", "/o", 0, "", "/")  # noqa: E731
        return BusReply("a(ssssssouso)", ([row("freedom-executor-stop-b.service"), row("freedom-executor-stop-a.service")],))

    mgr, _ = manager(handle)
    assert mgr.invocation_units() == ("freedom-executor-stop-a.service", "freedom-executor-stop-b.service")
    (request,) = seen
    assert (request.member, request.signature, request.body) == ("ListUnitsByPatterns", "asas", ([], ["freedom-executor-stop-*.service"]))
    empty, _ = manager(lambda r: BusReply("a(ssssssouso)", ([],)))
    assert empty.invocation_units() == ()


@pytest.mark.parametrize(
    "answer",
    [BusTimeout("t"), BusDisconnected("d"), BusProtocolError("p"), BusError("org.x.Failed"),
     BusReply("s", ("x",)), BusReply("a(ssssssouso)", ()), BusReply("a(ssssssouso)", ([("short",)],)),
     BusReply("a(ssssssouso)", ([(1,) * 10],))],
)
def test_an_unreadable_or_malformed_unit_listing_is_never_read_as_empty(answer):
    mgr, _ = manager(lambda r: answer)
    with pytest.raises(ManagerUnavailable):
        mgr.invocation_units()
