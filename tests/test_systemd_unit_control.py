"""Route 3 manager/Polkit adapter — contract tests over a fake bus transport.

Covers DI-1 … DI-6 and DI-S: exact request shapes and D-Bus type encodings,
result mappings, deadline behaviour, and the fail-closed rules (a mutating call
is sent at most once; an unconfirmed outcome is never promoted to success).
No live bus is needed; the real-bus runs live in ``test_systemd_integration.py``.
"""

from __future__ import annotations

import ast
import dataclasses
import os
import re
import stat
from collections import deque
from pathlib import Path

import pytest

from adapters.systemd.bus import (
    BusDisconnected,
    BusError,
    BusProtocolError,
    BusReply,
    BusRequest,
    BusSignal,
    BusTimeout,
    Variant,
)
from adapters.systemd import manager as manager_module
from adapters.systemd.manager import (
    JOB_MODE,
    ROLE_ARTIFACT,
    ROLE_INTERPRETER,
    Deadlines,
    SystemdManagerAdapter,
    unit_object_path,
)
from adapters.systemd.polkit import ACTION_ID, PolkitAuthorityAdapter
from adapters.systemd.subject import ProcSubjectSource
from application.unit_control import (
    CAPTURE_UNIT,
    BackstopCompletion,
    BackstopSpec,
    ControlError,
    ControlOk,
    ControlRefused,
    ControlSpecError,
    HolderSpec,
    PolkitAuthorized,
    PolkitNotAuthorized,
    ProcessSubject,
    RefusalReason,
    StopOutcome,
    TimerObservation,
    UnitProperty,
    UnitVerb,
)

ACT = "rp11-act-20261012T101500Z-0a1b2c3d"
A2 = "0123456789abcdef" * 4
JOB = "/org/freedesktop/systemd1/job/4242"
ROOT = Path(__file__).resolve().parent.parent


# --- fakes -----------------------------------------------------------------


class FakeWatch:
    def __init__(self, signals):
        self._signals = deque(signals)

    def next(self, *, timeout):
        if not self._signals:
            raise BusTimeout("no signal")
        item = self._signals.popleft()
        if isinstance(item, Exception):
            raise item
        return item


class FakeConnection:
    """Scripted bus. ``handlers`` maps ``member`` to a reply, an exception or a
    callable(request) returning one of those."""

    def __init__(self, handlers=None, signals=(), watch_error=None):
        self.handlers = handlers or {}
        self.signals = list(signals)
        self.watch_error = watch_error
        self.calls: list[BusRequest] = []
        self.events: list[str] = []
        self.watch_args: dict | None = None
        self.closed = False

    def call(self, request, *, timeout):
        self.calls.append(request)
        self.events.append(request.member)
        handler = self.handlers.get(request.member)
        if callable(handler):
            handler = handler(request)
        if handler is None:
            handler = BusReply("", ())
        if isinstance(handler, Exception):
            raise handler
        return handler

    def watch_signals(self, **kwargs):
        self.events.append("watch")
        self.watch_args = kwargs
        if self.watch_error:
            raise self.watch_error
        return FakeWatch(self.signals)

    def close(self):
        self.closed = True


def removed(job=JOB, unit=f"{ACT}.service", result="done"):
    return BusSignal(
        "/org/freedesktop/systemd1",
        "org.freedesktop.systemd1.Manager",
        "JobRemoved",
        "uoss",
        (7, job, unit, result),
    )


def job_reply(path=JOB):
    return BusReply("o", (path,))


def props_handler(values):
    """Properties.Get handler keyed by property name -> (signature, value)."""

    def handle(request):
        name = request.body[1]
        if name not in values:
            return BusError("org.freedesktop.DBus.Error.UnknownProperty", name)
        signature, value = values[name]
        return BusReply("v", ((signature, value),))

    return handle


@pytest.fixture(autouse=True)
def safe_role_runtime(monkeypatch):
    """The fake bus has no installed artifact; the pre-execution check is tested below."""
    monkeypatch.setattr(manager_module, "_role_runtime_problem", lambda: None)


def adapter_for(conn, **kw):
    return SystemdManagerAdapter(lambda: conn, **kw)


def holder_spec():
    return HolderSpec(
        activation_id=ACT,
        artifact_sha256=A2,
        runtime_max_seconds=900,
        timeout_stop_seconds=30,
    )


def backstop_spec():
    return BackstopSpec(
        activation_id=ACT,
        artifact_sha256=A2,
        interval_seconds=60,
        runtime_max_seconds=120,
        timeout_stop_seconds=20,
    )


RUNTIME = (ROLE_INTERPRETER, "-I", "-S", ROLE_ARTIFACT)
HOLD_VECTOR = (ROLE_INTERPRETER, [*RUNTIME, "hold", ACT, A2], False)
STOP_POST_VECTOR = (ROLE_INTERPRETER, [*RUNTIME, "deact", ACT, A2, "stop-post"], False)
BACKSTOP_VECTOR = (ROLE_INTERPRETER, [*RUNTIME, "backstop", ACT, A2], False)


MUTATING = {
    "StartTransientUnit": ("create_holder", holder_spec),
    "StopUnit": ("stop_capture_unit", None),
}


def mutating_calls(conn):
    return [c for c in conn.calls if c.member in {"StartTransientUnit", "StopUnit"}]


# --- DI-1 ------------------------------------------------------------------


def test_unit_object_path_escaping():
    assert (
        unit_object_path(CAPTURE_UNIT)
        == "/org/freedesktop/systemd1/unit/rp11_2dcapture_2dpass_2da_2eservice"
    )
    assert unit_object_path("a1.service").endswith("/a1_2eservice")
    assert unit_object_path("1a").endswith("/_31a")  # leading digit is escaped


def test_read_unit_request_shape_and_decoding():
    conn = FakeConnection(
        {
            "Get": props_handler(
                {
                    "ActiveState": ("s", "active"),
                    "InvocationID": ("ay", bytes(range(16))),
                    "Job": ("(uo)", (0, "/")),
                    "InactiveEnterTimestampMonotonic": ("t", 0),
                    "Result": ("s", "success"),
                }
            )
        }
    )
    wanted = (
        UnitProperty.ACTIVE_STATE,
        UnitProperty.INVOCATION_ID,
        UnitProperty.JOB,
        UnitProperty.INACTIVE_ENTER_TIMESTAMP_MONOTONIC,
        UnitProperty.RESULT,
    )
    result = adapter_for(conn).read_unit(CAPTURE_UNIT, wanted)
    assert isinstance(result, ControlOk)
    assert result.value == {
        UnitProperty.ACTIVE_STATE: "active",
        UnitProperty.INVOCATION_ID: bytes(range(16)).hex(),
        UnitProperty.JOB: 0,
        UnitProperty.INACTIVE_ENTER_TIMESTAMP_MONOTONIC: 0,
        UnitProperty.RESULT: "success",
    }
    assert [(c.interface, c.member, c.signature) for c in conn.calls] == [
        ("org.freedesktop.DBus.Properties", "Get", "ss")
    ] * 5
    assert [c.body for c in conn.calls] == [
        ("org.freedesktop.systemd1.Unit", "ActiveState"),
        ("org.freedesktop.systemd1.Unit", "InvocationID"),
        ("org.freedesktop.systemd1.Unit", "Job"),
        ("org.freedesktop.systemd1.Unit", "InactiveEnterTimestampMonotonic"),
        ("org.freedesktop.systemd1.Service", "Result"),
    ]
    assert {c.path for c in conn.calls} == {unit_object_path(CAPTURE_UNIT)}
    assert {c.destination for c in conn.calls} == {"org.freedesktop.systemd1"}
    assert conn.closed


def test_read_unit_empty_invocation_id_is_empty_hex():
    conn = FakeConnection({"Get": props_handler({"InvocationID": ("ay", b"")})})
    result = adapter_for(conn).read_unit(CAPTURE_UNIT, (UnitProperty.INVOCATION_ID,))
    assert result.value == {UnitProperty.INVOCATION_ID: ""}


@pytest.mark.parametrize(
    "bad_unit",
    ["sshd.service", "", "../x", CAPTURE_UNIT + "x", "rp11-act-1.service", ACT + "-backstop.path"],
)
def test_read_unit_refuses_unlisted_units_without_touching_the_bus(bad_unit):
    conn = FakeConnection()
    result = adapter_for(conn).read_unit(bad_unit, (UnitProperty.ACTIVE_STATE,))
    assert isinstance(result, ControlError) and result.kind == "invalid-request"
    assert not result.effect_not_confirmed
    assert conn.calls == []


def test_read_unit_rejects_unknown_or_duplicate_property_names():
    conn = FakeConnection()
    a = adapter_for(conn)
    assert a.read_unit(CAPTURE_UNIT, ("MainPID",)).kind == "invalid-request"  # type: ignore[arg-type]
    assert a.read_unit(CAPTURE_UNIT, ()).kind == "invalid-request"
    two = (UnitProperty.ACTIVE_STATE, UnitProperty.ACTIVE_STATE)
    assert a.read_unit(CAPTURE_UNIT, two).kind == "invalid-request"
    assert conn.calls == []


@pytest.mark.parametrize(
    "reply",
    [
        BusReply("v", (("u", 3),)),  # wrong inner signature
        BusReply("s", ("active",)),  # not a variant
        BusReply("v", ()),
        BusReply("v", (("s", 5),)),  # type disagrees with signature
        BusReply("v", ("s",)),
    ],
)
def test_read_unit_malformed_reply_is_error(reply):
    conn = FakeConnection({"Get": reply})
    result = adapter_for(conn).read_unit(CAPTURE_UNIT, (UnitProperty.ACTIVE_STATE,))
    assert isinstance(result, ControlError) and result.kind == "invalid-reply"


def test_read_unit_bad_invocation_id_length_is_error():
    conn = FakeConnection({"Get": props_handler({"InvocationID": ("ay", b"abc")})})
    result = adapter_for(conn).read_unit(CAPTURE_UNIT, (UnitProperty.INVOCATION_ID,))
    assert result.kind == "invalid-reply"


@pytest.mark.parametrize(
    "exc,kind",
    [
        (
            BusError("org.freedesktop.DBus.Error.UnknownProperty", "x"),
            "org.freedesktop.DBus.Error.UnknownProperty",
        ),
        (
            BusError("org.freedesktop.DBus.Error.AccessDenied", "x"),
            "org.freedesktop.DBus.Error.AccessDenied",
        ),
        (BusTimeout("slow"), "timeout"),
        (BusDisconnected("gone"), "disconnected"),
        (BusProtocolError("junk"), "invalid-reply"),
    ],
)
def test_read_unit_failures_are_errors_never_refusals(exc, kind):
    conn = FakeConnection({"Get": exc})
    result = adapter_for(conn).read_unit(CAPTURE_UNIT, (UnitProperty.ACTIVE_STATE,))
    assert isinstance(result, ControlError)
    assert result.kind == kind
    assert not result.effect_not_confirmed  # a read has no unknown-effect question


def test_connect_failure_is_error():
    def boom():
        raise BusDisconnected("no bus")

    result = SystemdManagerAdapter(boom).read_unit(CAPTURE_UNIT, (UnitProperty.ACTIVE_STATE,))
    assert isinstance(result, ControlError) and result.kind == "connect-failed"


# --- DI-2 ------------------------------------------------------------------


def test_create_holder_request_shape_and_type_encoding():
    conn = FakeConnection(
        {"StartTransientUnit": job_reply(), "Get": props_handler({"ActiveState": ("s", "active")})},
        signals=[removed()],
    )
    result = adapter_for(conn).create_holder(holder_spec())
    assert isinstance(result, ControlOk)

    (call,) = mutating_calls(conn)
    assert (call.destination, call.path, call.interface, call.member) == (
        "org.freedesktop.systemd1",
        "/org/freedesktop/systemd1",
        "org.freedesktop.systemd1.Manager",
        "StartTransientUnit",
    )
    assert call.signature == "ssa(sv)a(sa(sv))"
    name, mode, properties, aux = call.body
    assert name == f"{ACT}.service"
    assert mode == JOB_MODE == "fail"
    assert aux == []
    assert properties == [
        ("Type", Variant("s", "exec")),
        ("Restart", Variant("s", "no")),
        ("OOMScoreAdjust", Variant("i", -1000)),
        ("RuntimeMaxUSec", Variant("t", 900_000_000)),
        ("TimeoutStopUSec", Variant("t", 30_000_000)),
        ("ExecStopPost", Variant("a(sasb)", [STOP_POST_VECTOR])),
        ("ExecStart", Variant("a(sasb)", [HOLD_VECTOR])),
    ]


def test_role_runtime_is_the_isolated_system_interpreter_and_controlled_artifact():
    assert ROLE_INTERPRETER == "/usr/bin/python3.14"
    assert ROLE_ARTIFACT == "/usr/local/libexec/freedom-blades-rp11/rp11_h1.py"
    for vector in (HOLD_VECTOR, STOP_POST_VECTOR, BACKSTOP_VECTOR):
        path, argv, ignore_failure = vector
        assert path == argv[0] == ROLE_INTERPRETER and argv[1:3] == ["-I", "-S"]
        assert ignore_failure is False
        assert not any(c in "".join(argv) for c in "%$\\\"' ;|&`\n")


def test_signal_match_and_subscribe_precede_the_mutating_call():
    conn = FakeConnection({"StartTransientUnit": job_reply()}, signals=[removed()])
    adapter_for(conn).create_holder(holder_spec())
    assert conn.events[:3] == ["watch", "Subscribe", "StartTransientUnit"]
    assert conn.watch_args == {
        "sender": "org.freedesktop.systemd1",
        "path": "/org/freedesktop/systemd1",
        "interface": "org.freedesktop.systemd1.Manager",
        "member": "JobRemoved",
        "arg2": f"{ACT}.service",
    }


def test_completion_is_matched_by_job_path_and_unit():
    other_job = removed(job="/org/freedesktop/systemd1/job/1")
    other_unit = removed(unit="someone-else.service")
    conn = FakeConnection(
        {"StartTransientUnit": job_reply(), "Get": props_handler({"ActiveState": ("s", "active")})},
        signals=[other_job, other_unit, removed()],
    )
    result = adapter_for(conn).create_holder(holder_spec())
    assert isinstance(result, ControlOk)
    assert result.value.job_path == JOB
    assert result.value.unit == f"{ACT}.service"


def test_observation_is_attached_but_never_decides_the_result():
    conn = FakeConnection(
        {"StartTransientUnit": job_reply(), "Get": BusError("x.Failure", "no")}, signals=[removed()]
    )
    result = adapter_for(conn).create_holder(holder_spec())
    assert isinstance(result, ControlOk)
    assert result.value.observed is None

    conn = FakeConnection(
        {
            "StartTransientUnit": job_reply(),
            "Get": props_handler(
                {
                    "ActiveState": ("s", "active"),
                    "LoadState": ("s", "loaded"),
                    "Job": ("(uo)", (0, "/")),
                    "Result": ("s", "success"),
                    "InvocationID": ("ay", b""),
                }
            ),
        },
        signals=[removed()],
    )
    result = adapter_for(conn).create_holder(holder_spec())
    assert result.value.observed[UnitProperty.ACTIVE_STATE] == "active"


def test_create_holder_unit_exists_is_refused_exists():
    conn = FakeConnection(
        {"StartTransientUnit": BusError("org.freedesktop.systemd1.UnitExists", "dup")}
    )
    result = adapter_for(conn).create_holder(holder_spec())
    assert result == ControlRefused(RefusalReason.EXISTS)


@pytest.mark.parametrize(
    "name",
    [
        "org.freedesktop.DBus.Error.AccessDenied",
        "org.freedesktop.DBus.Error.InteractiveAuthorizationRequired",
    ],
)
@pytest.mark.parametrize("operation", ["holder", "backstop", "disarm", "stop"])
def test_authorization_failures_are_refusals_never_success(name, operation):
    conn = FakeConnection(
        {"StartTransientUnit": BusError(name, "denied"), "StopUnit": BusError(name, "denied")}
    )
    a = adapter_for(conn)
    result = {
        "holder": lambda: a.create_holder(holder_spec()),
        "backstop": lambda: a.create_backstop(backstop_spec()),
        "disarm": lambda: a.disarm_backstop(ACT),
        "stop": lambda: a.stop_capture_unit(),
    }[operation]()
    assert result == ControlRefused(RefusalReason.NOT_AUTHORIZED)
    assert len(mutating_calls(conn)) == 1


def test_create_invalid_args_stays_an_error_because_it_may_follow_mutation():
    conn = FakeConnection(
        {"StartTransientUnit": BusError("org.freedesktop.DBus.Error.InvalidArgs", "bad")}
    )
    for result in (
        adapter_for(conn).create_holder(holder_spec()),
        adapter_for(conn).create_backstop(backstop_spec()),
    ):
        assert isinstance(result, ControlError)
        assert result.effect_not_confirmed
    assert len(mutating_calls(conn)) == 2  # one per operation, never retried within one


@pytest.mark.parametrize(
    "result_text",
    [
        "failed",
        "canceled",
        "timeout",
        "dependency",
        "skipped",
        "invalid",
        "assert",
        "unsupported",
        "collected",
        "once",
        "frozen",
        "concurrency",
        "",
    ],
)
def test_job_removed_other_than_done_is_job_result_error(result_text):
    conn = FakeConnection(
        {"StartTransientUnit": job_reply()}, signals=[removed(result=result_text)]
    )
    result = adapter_for(conn).create_holder(holder_spec())
    assert isinstance(result, ControlError)
    assert result.kind == "job-result"
    assert result.effect_not_confirmed
    assert "Get" not in conn.events  # no state read masks a failed job


@pytest.mark.parametrize(
    "signals",
    [[], [removed(job="/org/freedesktop/systemd1/job/1")], [BusTimeout("deadline")]],
)
def test_no_matching_completion_is_unconfirmed_and_not_promoted_by_a_state_read(signals):
    conn = FakeConnection(
        {"StartTransientUnit": job_reply(), "Get": props_handler({"ActiveState": ("s", "active")})},
        signals=signals,
    )
    result = adapter_for(conn).create_holder(holder_spec())
    assert isinstance(result, ControlError)
    assert result.kind == "completion-timeout"
    assert result.effect_not_confirmed
    assert "Get" not in conn.events  # the unit may well be active: still an error
    assert len(mutating_calls(conn)) == 1


def test_connection_lost_while_waiting_is_unconfirmed():
    conn = FakeConnection({"StartTransientUnit": job_reply()}, signals=[BusDisconnected("eof")])
    result = adapter_for(conn).create_holder(holder_spec())
    assert result == ControlError("disconnected", "eof", effect_not_confirmed=True)


def test_unparsable_matching_completion_is_unconfirmed():
    bad = BusSignal(
        "/org/freedesktop/systemd1",
        "org.freedesktop.systemd1.Manager",
        "JobRemoved",
        "s",
        ("junk",),
    )
    conn = FakeConnection({"StartTransientUnit": job_reply()}, signals=[bad])
    result = adapter_for(conn).create_holder(holder_spec())
    assert result.kind == "invalid-reply" and result.effect_not_confirmed


@pytest.mark.parametrize(
    "exc,kind",
    [
        (BusTimeout("slow"), "timeout"),
        (BusDisconnected("gone"), "disconnected"),
        (BusProtocolError("junk"), "invalid-reply"),
        (
            BusError("org.freedesktop.systemd1.JobTypeNotApplicable", "x"),
            "org.freedesktop.systemd1.JobTypeNotApplicable",
        ),
        (BusError("org.freedesktop.DBus.Error.NoReply", "x"), "org.freedesktop.DBus.Error.NoReply"),
    ],
)
def test_lost_or_failed_mutating_call_is_one_unconfirmed_error_with_no_retry(exc, kind):
    conn = FakeConnection({"StartTransientUnit": exc})
    result = adapter_for(conn).create_holder(holder_spec())
    assert result == ControlError(
        kind, str(exc.message if isinstance(exc, BusError) else exc), effect_not_confirmed=True
    )
    assert len(mutating_calls(conn)) == 1


@pytest.mark.parametrize(
    "reply",
    [
        BusReply("s", (JOB,)),
        BusReply("o", ("/org/freedesktop/systemd1/unit/x",)),
        BusReply("o", ("/org/freedesktop/systemd1/job/",)),
        BusReply("o", ("/org/freedesktop/systemd1/job/12x",)),
        BusReply("o", ()),
        BusReply("oo", (JOB, JOB)),
        BusReply("o", (5,)),
    ],
)
def test_malformed_mutating_reply_is_unconfirmed_error(reply):
    conn = FakeConnection({"StartTransientUnit": reply})
    result = adapter_for(conn).create_holder(holder_spec())
    assert result.kind == "invalid-reply" and result.effect_not_confirmed


def test_duplicate_calls_are_independent_and_each_sent_once():
    conn = FakeConnection({"StartTransientUnit": job_reply()}, signals=[])
    a = adapter_for(conn)
    first = a.create_holder(holder_spec())
    second = a.create_holder(holder_spec())
    assert first.kind == second.kind == "completion-timeout"
    assert len(mutating_calls(conn)) == 2  # the caller's two calls, nothing extra


def test_subscribe_failure_is_reported_before_any_mutating_call():
    conn = FakeConnection({"Subscribe": BusError("org.freedesktop.DBus.Error.AccessDenied", "no")})
    result = adapter_for(conn).create_holder(holder_spec())
    assert isinstance(result, ControlError) and result.kind == "subscribe-failed"
    assert not result.effect_not_confirmed
    assert mutating_calls(conn) == []


def test_match_failure_is_reported_before_any_mutating_call():
    conn = FakeConnection(watch_error=BusTimeout("AddMatch"))
    result = adapter_for(conn).stop_capture_unit()
    assert result.kind == "subscribe-failed" and not result.effect_not_confirmed
    assert mutating_calls(conn) == []


def test_already_subscribed_is_tolerated():
    conn = FakeConnection(
        {
            "Subscribe": BusError("org.freedesktop.systemd1.AlreadySubscribed", ""),
            "StartTransientUnit": job_reply(),
        },
        signals=[removed()],
    )
    assert isinstance(adapter_for(conn).create_holder(holder_spec()), ControlOk)


# --- DI-3 ------------------------------------------------------------------


def test_create_backstop_request_shape():
    conn = FakeConnection(
        {"StartTransientUnit": job_reply()}, signals=[removed(unit=f"{ACT}-backstop.timer")]
    )
    result = adapter_for(conn).create_backstop(backstop_spec())
    assert isinstance(result, ControlOk)
    assert isinstance(result.value, BackstopCompletion)
    assert result.value.timer == f"{ACT}-backstop.timer" and result.value.job_path == JOB
    assert conn.watch_args["arg2"] == f"{ACT}-backstop.timer"

    (call,) = mutating_calls(conn)
    name, mode, timer_props, aux = call.body
    assert call.signature == "ssa(sv)a(sa(sv))"
    assert name == f"{ACT}-backstop.timer" and mode == "fail"
    assert timer_props == [
        ("TimersMonotonic", Variant("a(st)", [("OnActiveSec", 60_000_000)])),
        ("TimersMonotonic", Variant("a(st)", [("OnUnitActiveSec", 60_000_000)])),
        ("AccuracyUSec", Variant("t", 1_000_000)),
    ]
    ((service_name, service_props),) = aux
    assert service_name == f"{ACT}-backstop.service"
    assert service_props == [
        ("Type", Variant("s", "exec")),
        ("Restart", Variant("s", "no")),
        ("OOMScoreAdjust", Variant("i", -1000)),
        ("RuntimeMaxUSec", Variant("t", 120_000_000)),
        ("TimeoutStopUSec", Variant("t", 20_000_000)),
        ("ExecStart", Variant("a(sasb)", [BACKSTOP_VECTOR])),
    ]
    # D-10: the backstop service never sets TimeoutStartUSec (or its Sec spelling).
    names = {n for n, _ in timer_props} | {n for n, _ in service_props}
    assert not {n for n in names if n.startswith("TimeoutStart")}


TIMER_LINK = {
    "ActiveState": ("s", "active"),
    "LoadState": ("s", "loaded"),
    "Triggers": ("as", [f"{ACT}-backstop.service"]),
    "Unit": ("s", f"{ACT}-backstop.service"),
}


def test_create_backstop_observes_the_timer_and_its_trigger_link():
    conn = FakeConnection(
        {"StartTransientUnit": job_reply(), "Get": props_handler(TIMER_LINK)},
        signals=[removed(unit=f"{ACT}-backstop.timer")],
    )
    result = adapter_for(conn).create_backstop(backstop_spec())
    assert result.value.observed == TimerObservation(
        active_state="active",
        load_state="loaded",
        triggers=(f"{ACT}-backstop.service",),
        unit=f"{ACT}-backstop.service",
    )
    gets = [c for c in conn.calls if c.member == "Get"]
    assert [(c.interface, c.signature, c.body) for c in gets] == [
        ("org.freedesktop.DBus.Properties", "ss", ("org.freedesktop.systemd1.Unit", "ActiveState")),
        ("org.freedesktop.DBus.Properties", "ss", ("org.freedesktop.systemd1.Unit", "LoadState")),
        ("org.freedesktop.DBus.Properties", "ss", ("org.freedesktop.systemd1.Unit", "Triggers")),
        ("org.freedesktop.DBus.Properties", "ss", ("org.freedesktop.systemd1.Timer", "Unit")),
    ]
    assert {c.path for c in gets} == {unit_object_path(f"{ACT}-backstop.timer")}
    assert conn.events.index("StartTransientUnit") < conn.events.index("Get")


@pytest.mark.parametrize(
    "override",
    [
        {"Triggers": ("s", "x.service")},  # wrong signature
        {"Triggers": ("as", [1])},  # wrong element type
        {"Unit": ("as", ["x"])},
        {"LoadState": ("u", 1)},
        BusError("org.freedesktop.DBus.Error.UnknownProperty", "Unit"),
        BusTimeout("slow"),
    ],
)
def test_timer_observation_failure_never_rewrites_a_done_completion(override):
    if isinstance(override, Exception):
        values = {k: v for k, v in TIMER_LINK.items() if k != "Unit"}
        handler = props_handler(values) if isinstance(override, BusError) else override
    else:
        handler = props_handler({**TIMER_LINK, **override})
    conn = FakeConnection(
        {"StartTransientUnit": job_reply(), "Get": handler},
        signals=[removed(unit=f"{ACT}-backstop.timer")],
    )
    result = adapter_for(conn).create_backstop(backstop_spec())
    assert isinstance(result, ControlOk)
    assert result.value == BackstopCompletion(JOB, f"{ACT}-backstop.timer")
    assert result.value.observed is None


def test_failed_backstop_job_reads_no_observation():
    conn = FakeConnection(
        {"StartTransientUnit": job_reply(), "Get": props_handler(TIMER_LINK)},
        signals=[removed(unit=f"{ACT}-backstop.timer", result="failed")],
    )
    result = adapter_for(conn).create_backstop(backstop_spec())
    assert isinstance(result, ControlError) and result.kind == "job-result"
    assert "Get" not in conn.events


def test_backstop_unit_exists_is_not_a_refusal():
    conn = FakeConnection(
        {"StartTransientUnit": BusError("org.freedesktop.systemd1.UnitExists", "dup")}
    )
    result = adapter_for(conn).create_backstop(backstop_spec())
    assert isinstance(result, ControlError) and result.effect_not_confirmed


def test_backstop_no_such_unit_is_not_a_refusal():
    conn = FakeConnection(
        {"StartTransientUnit": BusError("org.freedesktop.systemd1.NoSuchUnit", "x")}
    )
    assert isinstance(adapter_for(conn).create_backstop(backstop_spec()), ControlError)


# --- DI-4 and DI-S ---------------------------------------------------------


def test_disarm_backstop_request_shape_and_stopped_outcome():
    conn = FakeConnection(
        {"StopUnit": job_reply()}, signals=[removed(unit=f"{ACT}-backstop.timer")]
    )
    result = adapter_for(conn).disarm_backstop(ACT)
    assert isinstance(result, ControlOk)
    assert result.value.outcome is StopOutcome.STOPPED
    (call,) = mutating_calls(conn)
    assert (call.interface, call.member, call.signature, call.body) == (
        "org.freedesktop.systemd1.Manager",
        "StopUnit",
        "ss",
        (f"{ACT}-backstop.timer", "fail"),
    )


def test_stop_capture_unit_targets_exactly_the_capture_unit():
    conn = FakeConnection({"StopUnit": job_reply()}, signals=[removed(unit=CAPTURE_UNIT)])
    result = adapter_for(conn).stop_capture_unit()
    assert isinstance(result, ControlOk) and result.value.outcome is StopOutcome.STOPPED
    (call,) = mutating_calls(conn)
    assert call.body == (CAPTURE_UNIT, "fail")
    assert not hasattr(StopOutcome, "ALREADY_STOPPED")


@pytest.mark.parametrize("op", ["disarm", "stop"])
def test_stop_not_loaded_is_refused(op):
    conn = FakeConnection(
        {"StopUnit": BusError("org.freedesktop.systemd1.NoSuchUnit", "Unit not loaded.")}
    )
    a = adapter_for(conn)
    result = a.disarm_backstop(ACT) if op == "disarm" else a.stop_capture_unit()
    assert result == ControlRefused(RefusalReason.NOT_LOADED)


@pytest.mark.parametrize("op", ["disarm", "stop"])
def test_stop_invalid_args_is_a_pre_mutation_refusal(op):
    conn = FakeConnection({"StopUnit": BusError("org.freedesktop.DBus.Error.InvalidArgs", "mode")})
    a = adapter_for(conn)
    result = a.disarm_backstop(ACT) if op == "disarm" else a.stop_capture_unit()
    assert result == ControlRefused(RefusalReason.INVALID_REQUEST)


@pytest.mark.parametrize("result_text", ["canceled", "frozen", "skipped", "failed"])
def test_stop_job_result_other_than_done_is_error(result_text):
    conn = FakeConnection(
        {"StopUnit": job_reply()}, signals=[removed(unit=CAPTURE_UNIT, result=result_text)]
    )
    result = adapter_for(conn).stop_capture_unit()
    assert result.kind == "job-result" and result.effect_not_confirmed


def test_stop_only_by_dependency_and_other_errors_are_unconfirmed():
    conn = FakeConnection({"StopUnit": BusError("org.freedesktop.systemd1.OnlyByDependency", "x")})
    result = adapter_for(conn).stop_capture_unit()
    assert isinstance(result, ControlError) and result.effect_not_confirmed


def test_stop_without_completion_is_unconfirmed_and_not_promoted():
    conn = FakeConnection(
        {"StopUnit": job_reply(), "Get": props_handler({"ActiveState": ("s", "inactive")})},
        signals=[],
    )
    result = adapter_for(conn).stop_capture_unit()
    assert result.kind == "completion-timeout" and result.effect_not_confirmed
    assert "Get" not in conn.events


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "rp11-capture-pass-a.service",
        ACT + ".service",
        ACT + "-backstop.timer",
        ACT.upper(),
        "rp11-act-1-2",
        ACT + "\n",
    ],
)
def test_disarm_rejects_a_non_activation_id_without_touching_the_bus(bad):
    conn = FakeConnection()
    result = adapter_for(conn).disarm_backstop(bad)
    assert isinstance(result, ControlError) and result.kind == "invalid-request"
    assert conn.calls == [] and conn.events == []


def test_no_arbitrary_unit_management_surface():
    public = {n for n in dir(SystemdManagerAdapter) if not n.startswith("_")}
    assert public == {
        "read_unit",
        "create_holder",
        "create_backstop",
        "disarm_backstop",
        "stop_capture_unit",
    }


# --- deadlines -------------------------------------------------------------


@pytest.mark.parametrize("value", [0, -1, 601, True, "5", None, float("nan")])
def test_deadlines_must_be_bounded(value):
    with pytest.raises(ValueError):
        Deadlines(call_seconds=value)
    with pytest.raises(ValueError):
        Deadlines(completion_seconds=value)


def test_completion_deadline_is_enforced_even_if_signals_keep_arriving():
    now = [0.0]

    class Chatty:
        def next(self, *, timeout):
            now[0] += 10.0
            return removed(job="/org/freedesktop/systemd1/job/9")

    class Conn(FakeConnection):
        def watch_signals(self, **kwargs):
            self.events.append("watch")
            return Chatty()

    conn = Conn({"StartTransientUnit": job_reply()})
    a = SystemdManagerAdapter(
        lambda: conn, deadlines=Deadlines(completion_seconds=25), clock=lambda: now[0]
    )
    result = a.create_holder(holder_spec())
    assert result.kind == "completion-timeout" and result.effect_not_confirmed


# --- request value objects -------------------------------------------------


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "rp11-act-20261012T101500Z-0A1B2C3D",
        "rp11-act-2026-1012",
        ACT + ".service",
        "x" + ACT,
        ACT + "\n",
    ],
)
def test_activation_id_grammar_is_enforced(bad):
    with pytest.raises(ControlSpecError):
        HolderSpec(bad, A2, 1, 1)
    with pytest.raises(ControlSpecError):
        BackstopSpec(bad, A2, 1, 1, 1)


@pytest.mark.parametrize("seconds", [0, -5, True, 1.5, 7 * 24 * 3600 + 1])
def test_durations_must_be_bounded_integers(seconds):
    with pytest.raises(ControlSpecError):
        BackstopSpec(ACT, A2, seconds, 10, 10)


# --- no arbitrary command can be expressed (remediation finding 1) ----------

BAD_SHA256 = [
    A2.upper(),
    A2[:-1],
    A2 + "0",
    "g" * 64,
    A2[:-1] + "\n",
    " " + A2[1:],
    A2[:32] + " " + A2[33:],
    "",
    None,
    A2.encode(),
    int(A2, 16),
]


@pytest.mark.parametrize("bad", BAD_SHA256)
def test_artifact_identity_must_be_a_lowercase_sha256(bad):
    with pytest.raises(ControlSpecError):
        HolderSpec(ACT, bad, 10, 10)
    with pytest.raises(ControlSpecError):
        BackstopSpec(ACT, bad, 10, 10, 10)


def test_requests_carry_no_executable_role_or_argument_field():
    assert [f.name for f in dataclasses.fields(HolderSpec)] == [
        "activation_id",
        "artifact_sha256",
        "runtime_max_seconds",
        "timeout_stop_seconds",
    ]
    assert [f.name for f in dataclasses.fields(BackstopSpec)] == [
        "activation_id",
        "artifact_sha256",
        "interval_seconds",
        "runtime_max_seconds",
        "timeout_stop_seconds",
    ]
    import application.unit_control as boundary

    assert not hasattr(boundary, "Command")
    for forbidden in ("exec_start", "exec_stop_post", "argv", "path", "role", "command"):
        with pytest.raises(TypeError):
            HolderSpec(ACT, A2, 10, 10, **{forbidden: ("/bin/sh", "-c", "id")})
        with pytest.raises(TypeError):
            BackstopSpec(ACT, A2, 10, 10, 10, **{forbidden: ("/bin/sh", "-c", "id")})


@pytest.mark.parametrize(
    "field,value",
    [
        ("activation_id", f"{ACT} ; /bin/sh -c id"),
        ("activation_id", "/bin/sh"),
        ("activation_id", f"{ACT}\x00"),
        ("artifact_sha256", f"{A2} stop-post"),  # an extra argument
        ("artifact_sha256", f"{A2} --role backstop"),
        ("artifact_sha256", "-c"),
        ("runtime_max_seconds", 0),
    ],
)
@pytest.mark.parametrize("operation", ["holder", "backstop"])
def test_a_forced_spec_is_refused_before_the_bus(operation, field, value):
    spec = holder_spec() if operation == "holder" else backstop_spec()
    object.__setattr__(spec, field, value)  # bypasses __post_init__
    conn = FakeConnection()
    a = adapter_for(conn)
    result = a.create_holder(spec) if operation == "holder" else a.create_backstop(spec)
    assert isinstance(result, ControlError) and result.kind == "invalid-request"
    assert not result.effect_not_confirmed
    assert conn.calls == [] and conn.events == []


def test_lookalike_and_subclassed_specs_are_refused_before_the_bus():
    class Sneaky(HolderSpec):
        @property
        def unit_name(self):
            return "ssh.service"

    @dataclasses.dataclass(frozen=True)
    class Lookalike:
        activation_id: str = ACT
        artifact_sha256: str = A2
        runtime_max_seconds: int = 10
        timeout_stop_seconds: int = 10
        exec_start: tuple = ("/bin/sh", ("sh", "-c", "id"))

        def validate(self):
            return self

    conn = FakeConnection()
    a = adapter_for(conn)
    for spec in (Sneaky(ACT, A2, 10, 10), Lookalike()):
        result = a.create_holder(spec)  # type: ignore[arg-type]
        assert isinstance(result, ControlError) and result.kind == "invalid-request"
    result = a.create_backstop(holder_spec())  # type: ignore[arg-type]
    assert isinstance(result, ControlError) and result.kind == "invalid-request"
    assert conn.calls == []


@pytest.mark.parametrize("value", [0, -5, True, 1.5, 7 * 24 * 3600 + 1])
@pytest.mark.parametrize("operation", ["holder", "backstop"])
def test_a_forced_spec_with_a_shadowed_validate_is_still_refused(operation, value):
    # An instance attribute shadows the class method on a frozen dataclass, so
    # revalidation must not call ``spec.validate`` through the instance.
    spec = holder_spec() if operation == "holder" else backstop_spec()
    object.__setattr__(spec, "runtime_max_seconds", value)
    object.__setattr__(spec, "validate", lambda: spec)
    conn = FakeConnection()
    a = adapter_for(conn)
    result = a.create_holder(spec) if operation == "holder" else a.create_backstop(spec)
    assert isinstance(result, ControlError) and result.kind == "invalid-request"
    assert conn.calls == [] and conn.events == []


# Security remediation finding 1: before PID 1 is asked to run the entry point as
# root, the adapter checks that only root can have changed it. The entry point's
# own check cannot vouch for a modified entry point.


@pytest.mark.parametrize("operation", ["holder", "backstop"])
def test_an_unsafe_role_runtime_is_refused_before_the_bus(monkeypatch, operation):
    monkeypatch.setattr(
        manager_module, "_role_runtime_problem", lambda: f"{ROLE_ARTIFACT}: owner uid 1000"
    )
    conn = FakeConnection()
    a = adapter_for(conn)
    result = a.create_holder(holder_spec()) if operation == "holder" else (
        a.create_backstop(backstop_spec())
    )
    assert isinstance(result, ControlError) and result.kind == "unsafe-artifact"
    assert "owner uid 1000" in result.detail
    assert not result.effect_not_confirmed
    assert conn.calls == [] and conn.events == []


def test_stops_do_not_depend_on_the_role_runtime(monkeypatch):
    monkeypatch.setattr(manager_module, "_role_runtime_problem", lambda: "unsafe")
    conn = FakeConnection({"StopUnit": BusError("org.freedesktop.systemd1.NoSuchUnit")})
    assert adapter_for(conn).disarm_backstop(ACT) == ControlRefused(RefusalReason.NOT_LOADED)


def test_role_runtime_check_covers_the_interpreter_and_the_entry_point(monkeypatch):
    import adapters.systemd.artifact as artifact

    monkeypatch.undo()  # the real _role_runtime_problem
    seen = []
    monkeypatch.setattr(artifact, "unsafe_root_path", lambda p: seen.append(p))
    assert manager_module._role_runtime_problem() is None
    assert seen == [ROLE_INTERPRETER, ROLE_ARTIFACT]
    monkeypatch.setattr(
        artifact, "unsafe_root_path", lambda p: "bad" if p == ROLE_ARTIFACT else None
    )
    assert manager_module._role_runtime_problem() == "bad"


def _st(mode: int, uid: int = 0) -> os.stat_result:
    return os.stat_result((mode, 1, 1, 1, uid, 0, 0, 0, 0, 0))


_DIR = stat.S_IFDIR | 0o755
_FILE = stat.S_IFREG | 0o644


def _fake_fs(**overrides):
    tree = {
        "/": _st(_DIR),
        "/usr": _st(_DIR),
        "/usr/local": _st(_DIR),
        "/usr/local/libexec": _st(_DIR),
        "/usr/local/libexec/freedom-blades-rp11": _st(_DIR),
        "/usr/local/libexec/freedom-blades-rp11/rp11_h1.py": _st(_FILE),
    }
    for path, info in overrides.items():
        tree[path] = info

    def lstat(path):
        if path not in tree or tree[path] is None:
            raise FileNotFoundError(2, "No such file or directory", path)
        return tree[path]

    return lstat


ENTRY = "/usr/local/libexec/freedom-blades-rp11/rp11_h1.py"
ARTIFACT_PARENT = "/usr/local/libexec/freedom-blades-rp11"


def test_root_path_rule_accepts_a_root_owned_protected_chain():
    from adapters.systemd.artifact import unsafe_root_path

    assert unsafe_root_path(ENTRY, lstat=_fake_fs()) is None
    # read/execute bits and a sticky or setgid directory bit do not matter
    lstat = _fake_fs(**{ARTIFACT_PARENT: _st(stat.S_IFDIR | stat.S_ISGID | 0o555)})
    assert unsafe_root_path(ENTRY, lstat=lstat) is None


@pytest.mark.parametrize(
    "path,info,reason",
    [
        (ENTRY, _st(_FILE, uid=1000), "owner uid 1000"),
        (ENTRY, _st(stat.S_IFREG | 0o444, uid=1000), "owner uid 1000"),
        (ENTRY, _st(stat.S_IFREG | 0o664), "group or other writable"),
        (ENTRY, _st(stat.S_IFREG | 0o646), "group or other writable"),
        (ENTRY, _st(stat.S_IFLNK | 0o777), "symlink"),
        (ENTRY, _st(_DIR), "not a regular file"),
        (ENTRY, _st(stat.S_IFIFO | 0o644), "not a regular file"),
        (ENTRY, None, "No such file"),
        (ARTIFACT_PARENT, _st(_DIR, uid=1000), "owner uid 1000"),
        (ARTIFACT_PARENT, _st(stat.S_IFDIR | 0o775), "group or other writable"),
        (ARTIFACT_PARENT, _st(stat.S_IFDIR | 0o1777), "group or other writable"),
        (ARTIFACT_PARENT, _st(stat.S_IFLNK | 0o777), "symlink"),
        (ARTIFACT_PARENT, _st(_FILE), "not a directory"),
        ("/usr/local", _st(stat.S_IFDIR | 0o757), "group or other writable"),
        ("/", _st(_DIR, uid=1000), "owner uid 1000"),
    ],
)
def test_root_path_rule_refuses_any_unsafe_component(path, info, reason):
    from adapters.systemd.artifact import unsafe_root_path

    problem = unsafe_root_path(ENTRY, lstat=_fake_fs(**{path: info}))
    assert problem is not None and reason in problem and path in problem


@pytest.mark.parametrize(
    "path",
    [
        "rp11_h1.py",
        "/usr/local/libexec/../libexec/freedom-blades-rp11/rp11_h1.py",
        "/usr/local/libexec/./freedom-blades-rp11/rp11_h1.py",
        "/usr/local/libexec//freedom-blades-rp11/rp11_h1.py",
        "/",
        "",
    ],
)
def test_root_path_rule_refuses_a_non_canonical_path(path):
    from adapters.systemd.artifact import unsafe_root_path

    assert unsafe_root_path(path, lstat=_fake_fs()) is not None


def test_root_path_rule_against_the_real_filesystem(tmp_path):
    from adapters.systemd.artifact import unsafe_root_path

    real = Path(os.path.realpath("/usr/bin/env"))  # a symlink on some distributions
    if any(p.stat().st_uid != 0 for p in (real, *real.parents)):
        pytest.skip("host has no root-owned env executable")
    assert unsafe_root_path(str(real)) is None
    mine = tmp_path / "rp11_h1.py"
    mine.write_text("")
    assert unsafe_root_path(str(mine)) is not None  # /tmp is world-writable; file is not root's
    link = tmp_path / "link.py"
    link.symlink_to(real)
    assert unsafe_root_path(str(link)) is not None


_Role = manager_module._Role
_RoleCommand = manager_module._RoleCommand
_check = manager_module._check_role_command
HOLD = ("hold", ACT, A2)


@pytest.mark.parametrize(
    "role,path,argv",
    [
        # shell commands
        (_Role.HOLD, "/bin/sh", ("/bin/sh", "-c", "id")),
        (_Role.HOLD, ROLE_INTERPRETER, (ROLE_INTERPRETER, "-c", "import os")),
        # alternate executables and interpreters
        (_Role.HOLD, "/usr/bin/python3", ("/usr/bin/python3", "-I", "-S", ROLE_ARTIFACT, *HOLD)),
        (_Role.HOLD, ROLE_INTERPRETER, ("python3", "-I", "-S", ROLE_ARTIFACT, *HOLD)),
        (_Role.HOLD, ROLE_INTERPRETER, (ROLE_INTERPRETER, "-I", "-S", "/tmp/rp11_h1.py", *HOLD)),
        # isolation flags removed or reordered
        (_Role.HOLD, ROLE_INTERPRETER, (ROLE_INTERPRETER, "-I", ROLE_ARTIFACT, *HOLD)),
        (_Role.HOLD, ROLE_INTERPRETER, (ROLE_INTERPRETER, "-S", "-I", ROLE_ARTIFACT, *HOLD)),
        # role substitution
        (_Role.HOLD, ROLE_INTERPRETER, (*RUNTIME, "backstop", ACT, A2)),
        (_Role.BACKSTOP, ROLE_INTERPRETER, (*RUNTIME, "hold", ACT, A2)),
        (_Role.STOP_POST, ROLE_INTERPRETER, (*RUNTIME, "deact", ACT, A2, "attest")),
        (_Role.STOP_POST, ROLE_INTERPRETER, (*RUNTIME, "hold", ACT, A2)),
        (_Role.HOLD, ROLE_INTERPRETER, (*RUNTIME, "consume", ACT, A2)),
        # malformed operands
        (_Role.HOLD, ROLE_INTERPRETER, (*RUNTIME, "hold", ACT, A2.upper())),
        (_Role.HOLD, ROLE_INTERPRETER, (*RUNTIME, "hold", "rp11-act-x", A2)),
        (_Role.HOLD, ROLE_INTERPRETER, (*RUNTIME, "hold", A2, ACT)),
        # extra or missing arguments
        (_Role.HOLD, ROLE_INTERPRETER, (*RUNTIME, "hold", ACT, A2, "stop-post")),
        (_Role.BACKSTOP, ROLE_INTERPRETER, (*RUNTIME, "backstop", ACT, A2, "--now")),
        (_Role.STOP_POST, ROLE_INTERPRETER, (*RUNTIME, "deact", ACT, A2)),
        (_Role.HOLD, ROLE_INTERPRETER, (*RUNTIME, "hold", ACT)),
        (_Role.HOLD, ROLE_INTERPRETER, [*RUNTIME, "hold", ACT, A2]),  # not a tuple
    ],
)
def test_role_vector_check_refuses_everything_but_the_exact_role(role, path, argv):
    with pytest.raises(ControlSpecError):
        _check(_RoleCommand(path, argv), role)


@pytest.mark.parametrize("role", list(_Role))
def test_role_vector_check_accepts_the_built_vector(role):
    command = manager_module._role_command(role, ACT, A2)
    _check(command, role)
    expected = {
        _Role.HOLD: HOLD_VECTOR,
        _Role.STOP_POST: STOP_POST_VECTOR,
        _Role.BACKSTOP: BACKSTOP_VECTOR,
    }[role]
    assert (command.path, list(command.argv), False) == expected


# --- DI-5 ------------------------------------------------------------------

SUBJECT = ProcessSubject(pid=1234, start_time=987654321, uid=1000)


def polkit_for(conn, **kw):
    return PolkitAuthorityAdapter(lambda: conn, **kw)


def decision(authorized, challenge, details=None):
    return BusReply("(bba{ss})", ((authorized, challenge, details or {}),))


def test_polkit_request_shape_is_exact():
    conn = FakeConnection({"CheckAuthorization": decision(True, False)})
    outcome = polkit_for(conn).check(SUBJECT, UnitVerb.START)
    assert outcome == PolkitAuthorized()
    (call,) = conn.calls
    assert (call.destination, call.path, call.interface, call.member) == (
        "org.freedesktop.PolicyKit1",
        "/org/freedesktop/PolicyKit1/Authority",
        "org.freedesktop.PolicyKit1.Authority",
        "CheckAuthorization",
    )
    assert call.signature == "(sa{sv})sa{ss}us"
    subject, action, details, flags, cancellation = call.body
    assert subject == (
        "unix-process",
        {
            "pid": Variant("u", 1234),
            "start-time": Variant("t", 987654321),
            "uid": Variant("i", 1000),
        },
    )
    assert action == ACTION_ID == "org.freedesktop.systemd1.manage-units"
    assert details == {"unit": CAPTURE_UNIT, "verb": "start"}
    assert flags == 0 and cancellation == ""
    assert conn.closed


def test_polkit_stop_verb_and_details_are_exactly_unit_and_verb():
    conn = FakeConnection({"CheckAuthorization": decision(False, False)})
    polkit_for(conn).check(SUBJECT, UnitVerb.STOP)
    assert conn.calls[0].body[2] == {"unit": CAPTURE_UNIT, "verb": "stop"}


@pytest.mark.parametrize(
    "reply,expected",
    [
        (decision(True, False), PolkitAuthorized()),
        (decision(False, False), PolkitNotAuthorized(challenge=False)),
        (decision(False, True), PolkitNotAuthorized(challenge=True)),
        (decision(False, True, {"polkit.dismissed": "true"}), PolkitNotAuthorized(challenge=True)),
    ],
)
def test_polkit_result_mapping(reply, expected):
    conn = FakeConnection({"CheckAuthorization": reply})
    assert polkit_for(conn).check(SUBJECT, UnitVerb.START) == expected


@pytest.mark.parametrize(
    "reply",
    [
        decision(True, True),
        BusReply("(bba{ss})", ((1, 0, {}),)),
        BusReply("(bba{ss})", ((True, False),)),
        BusReply(
            "(bba{ss})",
            ((True, False, [])),
        ),
        BusReply("(bba{ss})", ((True, False, {str(i): "x" for i in range(300)}),)),
        BusReply("b", (True,)),
        BusReply("(bba{ss})", ()),
        BusReply("(bba{ss})", (True,)),
    ],
)
def test_polkit_malformed_or_inconsistent_reply_is_error_not_a_decision(reply):
    conn = FakeConnection({"CheckAuthorization": reply})
    outcome = polkit_for(conn).check(SUBJECT, UnitVerb.START)
    assert isinstance(outcome, ControlError) and outcome.kind == "invalid-reply"


@pytest.mark.parametrize(
    "exc,kind",
    [
        (
            BusError("org.freedesktop.PolicyKit1.Error.NotAuthorized", "x"),
            "org.freedesktop.PolicyKit1.Error.NotAuthorized",
        ),
        (
            BusError("org.freedesktop.PolicyKit1.Error.Failed", "replaced"),
            "org.freedesktop.PolicyKit1.Error.Failed",
        ),
        (
            BusError("org.freedesktop.PolicyKit1.Error.Cancelled", "x"),
            "org.freedesktop.PolicyKit1.Error.Cancelled",
        ),
        (
            BusError("org.freedesktop.PolicyKit1.Error.NotSupported", "x"),
            "org.freedesktop.PolicyKit1.Error.NotSupported",
        ),
        (
            BusError("org.freedesktop.DBus.Error.ServiceUnknown", "x"),
            "org.freedesktop.DBus.Error.ServiceUnknown",
        ),
        (BusTimeout("slow"), "timeout"),
        (BusDisconnected("gone"), "disconnected"),
        (BusProtocolError("junk"), "invalid-reply"),
    ],
)
def test_polkit_errors_never_become_a_decision(exc, kind):
    conn = FakeConnection({"CheckAuthorization": exc})
    outcome = polkit_for(conn).check(SUBJECT, UnitVerb.START)
    assert isinstance(outcome, ControlError) and outcome.kind == kind
    assert len(conn.calls) == 1  # not retried


def test_polkit_rejects_an_unknown_verb_without_calling():
    conn = FakeConnection()
    outcome = polkit_for(conn).check(SUBJECT, "restart")  # type: ignore[arg-type]
    assert isinstance(outcome, ControlError) and outcome.kind == "invalid-request"
    assert conn.calls == []


def test_polkit_connect_failure_is_error():
    def boom():
        raise BusDisconnected("none")

    assert PolkitAuthorityAdapter(boom).check(SUBJECT, UnitVerb.START).kind == "connect-failed"


# Security remediation finding 3: the details map is part of the decision reply.
# It must be exactly a{ss} within the entry and byte bounds, whatever the booleans say.

MAX_DETAILS = 256
MAX_DETAIL_BYTES = 65_536


def _detail_bytes(entries: int, total: int) -> dict:
    """``entries`` distinct entries whose keys and values total exactly ``total`` UTF-8 bytes."""
    details = {f"k{i:03d}": "" for i in range(entries)}
    used = sum(len(k) for k in details)
    details["k000"] = "x" * (total - used)
    return details


@pytest.mark.parametrize("authorized,challenge", [(True, False), (False, False), (False, True)])
@pytest.mark.parametrize(
    "details",
    [
        {"bad": 1},
        {"bad": True},
        {"bad": b"bytes"},
        {"bad": None},
        {"bad": ["x"]},
        {"bad": {"x": "y"}},
        {"bad": ("x",)},
        {1: "x"},
        {True: "x"},
        {b"bad": "x"},
        {("t",): "x"},
        {None: "x"},
    ],
)
def test_polkit_malformed_detail_keys_or_values_are_invalid_reply(authorized, challenge, details):
    reply = BusReply("(bba{ss})", ((authorized, challenge, details),))
    outcome = polkit_for(FakeConnection({"CheckAuthorization": reply})).check(
        SUBJECT, UnitVerb.START
    )
    assert isinstance(outcome, ControlError) and outcome.kind == "invalid-reply"


class _Str(str):
    pass


class _Dict(dict):
    pass


@pytest.mark.parametrize("authorized", [True, False])
@pytest.mark.parametrize(
    "details",
    [
        {_Str("k"): "v"},
        {"k": _Str("v")},
        _Dict({"k": "v"}),
        __import__("collections").OrderedDict({"k": "v"}),
        __import__("types").MappingProxyType({"k": "v"}),
        [("k", "v")],
        {"k": "\ud800"},  # a lone surrogate is not a D-Bus string
    ],
)
def test_polkit_details_must_be_an_exact_dict_of_exact_strings(authorized, details):
    reply = BusReply("(bba{ss})", ((authorized, False, details),))
    outcome = polkit_for(FakeConnection({"CheckAuthorization": reply})).check(
        SUBJECT, UnitVerb.START
    )
    assert isinstance(outcome, ControlError) and outcome.kind == "invalid-reply"


@pytest.mark.parametrize("authorized", [True, False])
@pytest.mark.parametrize(
    "details,accepted",
    [
        (_detail_bytes(MAX_DETAILS - 1, 4096), True),
        (_detail_bytes(MAX_DETAILS, 4096), True),
        (_detail_bytes(MAX_DETAILS + 1, 4096), False),
        (_detail_bytes(1, MAX_DETAIL_BYTES - 1), True),
        (_detail_bytes(1, MAX_DETAIL_BYTES), True),
        (_detail_bytes(1, MAX_DETAIL_BYTES + 1), False),
        (_detail_bytes(MAX_DETAILS, MAX_DETAIL_BYTES), True),
        (_detail_bytes(MAX_DETAILS, MAX_DETAIL_BYTES + 1), False),
        ({"k": "é" * ((MAX_DETAIL_BYTES - 1) // 2)}, True),  # 65,535 bytes, 32,767 chars
        ({"k": "é" * (MAX_DETAIL_BYTES // 2)}, False),  # bytes are counted, not characters
        ({"x" * (MAX_DETAIL_BYTES + 1): ""}, False),  # one large key
        ({"k": "x" * 10_000_000}, False),  # one very large value
    ],
)
def test_polkit_details_are_bounded_by_entries_and_total_bytes(authorized, details, accepted):
    reply = BusReply("(bba{ss})", ((authorized, False, details),))
    outcome = polkit_for(FakeConnection({"CheckAuthorization": reply})).check(
        SUBJECT, UnitVerb.START
    )
    if accepted:
        assert outcome == (PolkitAuthorized() if authorized else PolkitNotAuthorized())
    else:
        assert isinstance(outcome, ControlError) and outcome.kind == "invalid-reply"


def test_polkit_detail_limits_are_the_documented_values():
    import adapters.systemd.polkit as polkit_module

    assert polkit_module._MAX_REPLY_DETAILS == MAX_DETAILS
    assert polkit_module._MAX_REPLY_DETAIL_BYTES == MAX_DETAIL_BYTES


# Security remediation finding 4: DI-5 revalidates the subject itself; a forced,
# subclassed or lookalike subject never reaches the bus.


class _CountingConnector:
    def __init__(self):
        self.connects = 0
        self.conn = FakeConnection({"CheckAuthorization": decision(True, False)})

    def __call__(self):
        self.connects += 1
        return self.conn


def _assert_invalid_without_bus(subject):
    connector = _CountingConnector()
    outcome = PolkitAuthorityAdapter(connector).check(subject, UnitVerb.START)
    assert isinstance(outcome, ControlError) and outcome.kind == "invalid-request", outcome
    assert connector.connects == 0 and connector.conn.calls == []


@pytest.mark.parametrize("field", ["pid", "start_time", "uid"])
@pytest.mark.parametrize(
    "value",
    [True, False, 1.0, 1.5, "1", "", None, b"1", 1 + 0j, [1], (1,), 2**64, -1, 2**200],
)
def test_polkit_refuses_a_forced_subject_field_before_the_bus(field, value):
    subject = ProcessSubject(pid=1234, start_time=987654321, uid=1000)
    object.__setattr__(subject, field, value)  # bypasses __post_init__
    _assert_invalid_without_bus(subject)


@pytest.mark.parametrize(
    "field,value",
    [
        ("pid", 0),
        ("pid", 2**32),
        ("start_time", 0),
        ("start_time", 2**64),
        ("uid", -1),
        ("uid", 2**31),
    ],
)
def test_polkit_refuses_a_forced_out_of_range_subject_before_the_bus(field, value):
    subject = ProcessSubject(pid=1234, start_time=987654321, uid=1000)
    object.__setattr__(subject, field, value)
    _assert_invalid_without_bus(subject)


@pytest.mark.parametrize("field", ["pid", "start_time", "uid"])
def test_polkit_refuses_a_forced_int_subclass_or_missing_field_before_the_bus(field):
    import enum

    class Big(enum.IntEnum):
        ONE = 1

    subject = ProcessSubject(pid=1234, start_time=987654321, uid=1000)
    object.__setattr__(subject, field, Big.ONE)
    _assert_invalid_without_bus(subject)
    subject = ProcessSubject(pid=1234, start_time=987654321, uid=1000)
    object.__delattr__(subject, field)
    _assert_invalid_without_bus(subject)


def test_polkit_refuses_subclassed_and_lookalike_subjects_before_the_bus():
    class Sub(ProcessSubject):
        pass

    @dataclasses.dataclass(frozen=True)
    class Lookalike:
        pid: int = 1234
        start_time: int = 987654321
        uid: int = 1000

    class Shape:
        pid = 1234
        start_time = 987654321
        uid = 1000

    for subject in (Sub(1234, 987654321, 1000), Lookalike(), Shape(), None, (1234, 1, 1000)):
        _assert_invalid_without_bus(subject)
    swapped = ProcessSubject(pid=1234, start_time=987654321, uid=1000)
    object.__setattr__(swapped, "__class__", Lookalike)
    _assert_invalid_without_bus(swapped)


def test_polkit_encodes_the_revalidated_subject_values():
    connector = _CountingConnector()
    PolkitAuthorityAdapter(connector).check(
        ProcessSubject(pid=0xFFFFFFFF, start_time=0xFFFFFFFFFFFFFFFF, uid=0), UnitVerb.STOP
    )
    (call,) = connector.conn.calls
    fields = call.body[0][1]
    assert fields == {
        "pid": Variant("u", 0xFFFFFFFF),
        "start-time": Variant("t", 0xFFFFFFFFFFFFFFFF),
        "uid": Variant("i", 0),
    }
    assert all(type(v.value) is int for v in fields.values())


# --- DI-6 ------------------------------------------------------------------


def write_proc(root: Path, pid: int, stat: str, uid_line: str = "Uid:\t1000\t1000\t1000\t1000"):
    d = root / str(pid)
    d.mkdir(parents=True, exist_ok=True)
    (d / "stat").write_text(stat)
    (d / "status").write_text(f"Name:\tx\n{uid_line}\nGid:\t1\t1\t1\t1\n")


def stat_line(start="123456", comm="(bash)"):
    # fields 3.. : state, then 18 more up to field 21, then starttime (22)
    middle = " ".join(["S"] + ["0"] * 18)
    return f"77 {comm} {middle} {start} 1 2 3\n"


def test_subject_from_proc(tmp_path):
    write_proc(tmp_path, 77, stat_line("555"))
    result = ProcSubjectSource(tmp_path).subject_for_pid(77)
    assert result == ControlOk(ProcessSubject(pid=77, start_time=555, uid=1000))


def test_subject_handles_comm_with_spaces_and_parentheses(tmp_path):
    write_proc(tmp_path, 77, stat_line("999", comm="(a) b (c d)"))
    assert ProcSubjectSource(tmp_path).subject_for_pid(77).value.start_time == 999


def test_subject_uses_the_real_uid_not_the_effective_one(tmp_path):
    write_proc(tmp_path, 77, stat_line(), uid_line="Uid:\t1001\t0\t0\t0")
    assert ProcSubjectSource(tmp_path).subject_for_pid(77).value.uid == 1001


def test_subject_matches_the_running_process():
    import os

    result = ProcSubjectSource().subject_for_pid(os.getpid())
    assert isinstance(result, ControlOk)
    assert result.value.uid == os.getuid()
    fields = Path("/proc/self/stat").read_text().rsplit(")", 1)[1].split()
    assert result.value.start_time == int(fields[19])


@pytest.mark.parametrize(
    "stat",
    [
        "",
        "no-paren",
        "77 (x)",
        "77 (x) S 1 2",
        stat_line("abc"),
        stat_line("-5"),
        stat_line("0"),
        stat_line("1.5"),
        stat_line("١٢٣"),
        "77 (x)S " + " ".join(["0"] * 30),
    ],
)
def test_subject_malformed_stat_is_error(tmp_path, stat):
    write_proc(tmp_path, 77, stat)
    result = ProcSubjectSource(tmp_path).subject_for_pid(77)
    assert isinstance(result, ControlError)
    assert result.kind in {"proc-unreadable", "proc-malformed"}


@pytest.mark.parametrize(
    "uid_line",
    ["Gid:\t1", "Uid:", "Uid:\tx\t1\t1\t1", "Uid:\t-1\t1\t1\t1", f"Uid:\t{2**31}\t0\t0\t0"],
)
def test_subject_malformed_uid_is_error(tmp_path, uid_line):
    write_proc(tmp_path, 77, stat_line(), uid_line=uid_line)
    assert isinstance(ProcSubjectSource(tmp_path).subject_for_pid(77), ControlError)


def test_subject_missing_process_is_error(tmp_path):
    result = ProcSubjectSource(tmp_path).subject_for_pid(4321)
    assert isinstance(result, ControlError) and result.kind == "proc-unreadable"


def test_subject_replaced_between_reads_is_error(tmp_path):
    write_proc(tmp_path, 77, stat_line("100"))

    class Racy(ProcSubjectSource):
        def _real_uid(self, pid):
            uid = super()._real_uid(pid)
            write_proc(tmp_path, 77, stat_line("101"))
            return uid

    result = Racy(tmp_path).subject_for_pid(77)
    assert isinstance(result, ControlError) and result.kind == "proc-replaced"


@pytest.mark.parametrize("pid", [0, -1, 2**32, True, "7", None])
def test_subject_rejects_bad_pids(tmp_path, pid):
    assert ProcSubjectSource(tmp_path).subject_for_pid(pid).kind == "invalid-request"  # type: ignore[arg-type]


@pytest.mark.parametrize("field", ["pid", "start_time", "uid"])
@pytest.mark.parametrize("value", [True, False, 1.0, 1.5, "1", None, b"1", 1 + 0j])
def test_subject_value_object_accepts_only_exact_ints(field, value):
    base = {"pid": 1, "start_time": 1, "uid": 0}
    with pytest.raises(ControlSpecError):
        ProcessSubject(**{**base, field: value})


def test_subject_value_object_rejects_int_subclasses():
    import enum

    class Pid(enum.IntEnum):
        ONE = 1

    with pytest.raises(ControlSpecError):
        ProcessSubject(pid=Pid.ONE, start_time=1, uid=0)


def test_subject_value_object_accepts_the_range_limits():
    ProcessSubject(pid=0xFFFFFFFF, start_time=0xFFFFFFFFFFFFFFFF, uid=0x7FFFFFFF)
    ProcessSubject(pid=1, start_time=1, uid=0)


def test_subject_value_object_enforces_dbus_ranges():
    for kwargs in (
        {"pid": 0},
        {"pid": 2**32},
        {"start_time": 0},
        {"start_time": 2**64},
        {"uid": -1},
        {"uid": 2**31},
    ):
        base = {"pid": 1, "start_time": 1, "uid": 0, **kwargs}
        with pytest.raises(ControlSpecError):
            ProcessSubject(**base)


# --- structure -------------------------------------------------------------


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module.split(".")[0])
    return found


def test_application_boundary_knows_no_transport():
    assert _imports(ROOT / "application/unit_control.py") <= {
        "__future__",
        "collections",
        "re",
        "dataclasses",
        "enum",
        "typing",
    }


def test_only_the_jeepney_module_imports_the_client_library():
    for path in (ROOT / "adapters/systemd").glob("*.py"):
        uses = "jeepney" in _imports(path)
        assert uses == (path.name == "jeepney_bus.py"), path.name


def test_adapter_is_inactive_nothing_in_a_runtime_path_imports_it():
    pattern = re.compile(r"(adapters\.systemd|application\.unit_control)")
    offenders = []
    for base in (
        "main.py",
        "config.py",
        "ext",
        "models",
        "helpers",
        "connectors",
        "adapters/web",
        "adapters/http",
        "adapters/worker",
        "application/web",
        "application/worker",
        "tools",
    ):
        target = ROOT / base
        files = [target] if target.is_file() else list(target.rglob("*.py"))
        for f in files:
            if pattern.search(f.read_text()):
                offenders.append(str(f.relative_to(ROOT)))
    assert offenders == []
