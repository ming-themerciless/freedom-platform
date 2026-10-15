"""Activation records, schema ``rp11-activation-record/2`` (H-REC.1 … H-REC.4).

A record is ``canonical_bytes`` of exactly the closed keys below; no extra key,
no ``null``, no float, no environment content and no content of any object.
Records are published once (PF, ``0444``, no replace) and never rewritten or
deleted.

``validate_record`` is the total schema check every published and every read
record passes. It returns normally for a record that satisfies the whole closed
schema (every nested object and list with its exact keys, exact scalar types,
bounds, enumerations, digest and path forms) and the cross-field relations that
ACT, ST-1, BS-2 and BS-3 rely on, and otherwise raises ``RecordSchemaError`` and
nothing else. The nested grammar is a table of small checkers (``_obj``,
``_list``, ``_one_of`` …); the relations are ``_cross_*`` functions that only run
on a structurally valid record.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping

from .attribution import ObjectKind
from .authority import AUTHORITY_LIMIT, A2Pins, AuthorityError, Params
from .canonical import ABSENT, CanonicalError, check_value
from .pk import PROCEDURE, PkMode, PkOutcome
from .ports import LockMode

SCHEMA = "rp11-activation-record/2"

RECORD_KEYS = frozenset(
    {
        "schema",
        "kind",
        "activation_id",
        "attempt",
        "trigger",
        "authority",
        "authority_limit",
        "h1_record",
        "h2_record_sha256",
        "boot",
        "pass_config",
        "staged_rule",
        "active_rule",
        "grant_check",
        "unit",
        "lease",
        "holder",
        "consume",
        "directories",
        "lock",
        "grant_identity",
        "pk",
        "children",
        "release",
        "capture",
        "helper",
        "params",
        "st1",
        "journals",
        "act_record_sha256",
        "outcome",
        "failure",
        "residual",
        "evidence_mode",
        "time",
    }
)

RULE_CLASSES = frozenset(
    {
        "removed-verified",
        "removed-unconfirmed",
        "never-linked",
        "removed-earlier",
        "absent-before-removal",
        "present-damaged-unremoved",
        "present-foreign-unremoved",
        "present-uninspected-unremoved",
        "cleared-by-boot",
        "grant-unremovable",
    }
)
PASS_CLASSES = frozenset(
    {
        "removed",
        "never-linked",
        "removed-earlier",
        "absent-before-removal",
        "cleared-by-boot",
        "present-damaged-unremoved",
        "present-foreign-unremoved",
        "unremovable",
    }
)
DIR_CLASSES = frozenset(
    {
        "removed",
        "never-created",
        "removed-earlier",
        "absent-before-removal",
        "cleared-by-boot",
        "pre-existing-kept",
        "s0-kept",
        "present-nonempty-unremoved",
        "present-damaged-unremoved",
        "present-foreign-unremoved",
        "unremovable",
    }
)
RESIDUAL_CLASSES = RULE_CLASSES | PASS_CLASSES | DIR_CLASSES | {"s0"}
FAILURE_CLASSES = frozenset(
    {
        "lock-object",
        "capture-baseline-unstable",
        "grant-not-seen",
        "stop-control-unconfirmed",
        "act-unconfirmed",
        "invalid-journal",
        "invalid-authority",
        "record-unpublished",
        "evidence-unwritable",
        "observation-failed",
        "unit-still-active",
        "st1-not-verified",
        "grant-unconfirmed",
        "residual",
    }
)
OUTCOMES = {"act": frozenset({"activated", "failed"}), "deact": frozenset({"st1-verified", "hard-stop"})}
TRIGGERS = frozenset({"act", "stop-post", "backstop", "attest"})

# What CL-3 … CL-6 call clean: the classes under which ``st1-verified`` may be stated.
RULE_VERIFIED = frozenset(
    {"removed-verified", "never-linked", "removed-earlier", "absent-before-removal", "cleared-by-boot"}
)
PASS_VERIFIED = frozenset({"removed", "never-linked", "removed-earlier", "absent-before-removal", "cleared-by-boot"})
DIR_VERIFIED = frozenset(
    {
        "removed",
        "never-created",
        "removed-earlier",
        "absent-before-removal",
        "cleared-by-boot",
        "pre-existing-kept",
        "s0-kept",
    }
)
GRR_OUTCOMES = frozenset(
    {"removed", "absent", "kept-damaged", "kept-foreign", "kept-uninspected", "unremovable", "identity-unavailable"}
)
ST1_CHECKS = frozenset(
    {
        "rule-absent",
        "pass-config-absent",
        "tree-p-absent",
        "rules-dir-as-at-ap0",
        "lock-dir-absent-or-s0",
        "pk-not-authorized",
        "baseline-equal",
        "capture-unit-not-active",
    }
)
DIRECTORY_ROLES = frozenset({"tree-p", "tree-r", "rules-dir", "lock-dir"})
CONSUME_CLASSES = frozenset({"claimed", "indeterminate", "none", "unidentified"})
CONSUME_OUTCOMES = frozenset({"consumed", "failed", "incomplete", "unjournaled"})
HELPER_ROLES = frozenset({"hold", "stop-post", "backstop", "attest"})

PK_UNCONFIRMED_REASONS = frozenset({"only-errors", "still-authorized", "interrupted"})

MAX_DIRECTORIES = 64
MAX_CHILDREN = 64
MAX_JOURNALS = 128
MAX_RESIDUAL = 64
MAX_IMAGES = 16
_MAX_PATH = 4096

_HEX64 = re.compile(r"[0-9a-f]{64}")
_HEX32 = re.compile(r"[0-9a-f]{32}")
_TOKEN = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
_STEP = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,15}")
_ACTIVATION = re.compile(r"rp11-act-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}")
_BOOT_ID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_RECORD_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}")
_UTC = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
_KEY_PATH = re.compile(r"[A-Za-z0-9_.\[\]-]{1,256}")
_FSTYPE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,31}")
_SEND_RESULT = re.compile(r"[A-Za-z0-9:()_.-]{1,96}")
_SIGNAL = re.compile(r"SIG[A-Z0-9]{1,12}")
_ANOMALY = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
_ROLE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}")

_UINT_MAX = 0xFFFFFFFFFFFFFFFF


class RecordSchemaError(ValueError):
    pass


class _Bad(Exception):
    """Internal: one checker's rejection, carrying the field path built on the way out."""


Check = Callable[[object], None]


def _expect(condition: bool, why: str) -> None:
    if not condition:
        raise _Bad(why)


# --- checkers ---------------------------------------------------------------------


def _pattern(pattern: re.Pattern[str]) -> Check:
    def check(value: object) -> None:
        _expect(type(value) is str and pattern.fullmatch(value) is not None, "malformed text")

    return check


def _uint(value: object) -> None:
    _expect(type(value) is int and 0 <= value <= _UINT_MAX, "not an unsigned integer")


def _int_between(low: int, high: int) -> Check:
    def check(value: object) -> None:
        _expect(type(value) is int and low <= value <= high, f"outside {low}..{high}")

    return check


def _xattr_name(value: object) -> None:
    """Any non-empty name a filesystem can report (``os.listxattr``: no NUL, at most 255
    bytes). Canonical serialization escapes it, so a hostile name never blocks a record."""
    _expect(type(value) is str and 1 <= len(value) <= 255 and "\x00" not in value, "not an attribute name")


def _bool(value: object) -> None:
    _expect(type(value) is bool, "not a boolean")


def _path(value: object) -> None:
    _expect(
        type(value) is str
        and value.startswith("/")
        and len(value) <= _MAX_PATH
        and value.isascii()
        and "//" not in value
        and "\x00" not in value
        and all(part not in (".", "..") for part in value.split("/")[1:]),
        "not an absolute path",
    )


def _equals(expected: object) -> Check:
    def check(value: object) -> None:
        _expect(type(value) is type(expected) and value == expected, f"is not {expected!r}")

    return check


def _one_of(values: frozenset[str]) -> Check:
    def check(value: object) -> None:
        _expect(type(value) is str and value in values, "not an admitted value")

    return check


def _or_absent(inner: Check) -> Check:
    def check(value: object) -> None:
        if not (type(value) is str and value == ABSENT):
            inner(value)

    return check


def _obj(fields: Mapping[str, Check]) -> Check:
    def check(value: object) -> None:
        _expect(type(value) is dict, "not an object")
        assert isinstance(value, dict)
        _expect(set(value) == set(fields), f"keys differ: {sorted(set(value) ^ set(fields))}")
        for name, inner in fields.items():
            try:
                inner(value[name])
            except _Bad as exc:
                raise _Bad(f"{name}: {exc}") from None

    return check


def _list(inner: Check, limit: int, *, minimum: int = 0) -> Check:
    def check(value: object) -> None:
        _expect(type(value) is list and minimum <= len(value) <= limit, f"not a list of {minimum}..{limit}")
        assert isinstance(value, list)
        for index, item in enumerate(value):
            try:
                inner(item)
            except _Bad as exc:
                raise _Bad(f"[{index}]: {exc}") from None

    return check


HEX64 = _pattern(_HEX64)
DIGEST_OR_ABSENT = _or_absent(HEX64)
TOKEN = _pattern(_TOKEN)
TOKEN_OR_ABSENT = _or_absent(TOKEN)
BOOT_OR_ABSENT = _or_absent(_pattern(_BOOT_ID))
UTC_OR_ABSENT = _or_absent(_pattern(_UTC))

_IDENTITY = _obj({"path": _path, "dev": _uint, "ino": _uint})
IDENTITY_OR_ABSENT = _or_absent(_IDENTITY)


def _distinct_images(value: object) -> None:
    _list(HEX64, MAX_IMAGES)(value)
    assert isinstance(value, list)
    _expect(len(set(value)) == len(value), "duplicate digest")


def _signals(value: object) -> None:
    _obj({"sent": _uint, "esrch": _uint, "failed": _uint, "not_sent": _uint})(value)


_SEND = _obj(
    {
        "signal": _pattern(_SIGNAL),
        "result": _pattern(_SEND_RESULT),
        "offset_ms": _uint,
        "late": _bool,
    }
)
_CHILD = _obj(
    {
        "role": _pattern(_ROLE_NAME),
        "argv0": _pattern(_ROLE_NAME),
        "pid": _uint,
        "pgid": _uint,
        "start_ticks": _or_absent(_uint),
        "deadline_ms": _uint,
        "s0_ran": _bool,
        "grace_deadline_ms": _or_absent(_uint),
        "outcome": _one_of(frozenset({"exited", "reap-error"})),
        "sends": _list(_SEND, 8),
        "waits_skipped": _uint,
        "reaped": _bool,
        "abandoned": _bool,
        "reap_unknown": _bool,
        "send_suppressed": _bool,
        "last_signal": _or_absent(_pattern(_SIGNAL)),
        "effect": _equals("none"),
        "anomalies": _list(_pattern(_ANOMALY), 16),
    }
)
_RESIDUAL = _obj(
    {
        "path": _path,
        "class": _one_of(RESIDUAL_CLASSES),
        "type": _one_of(frozenset(kind.value for kind in ObjectKind)),
        "uid": _uint,
        "gid": _uint,
        "mode": _int_between(0, 0o7777),
        "size": _uint,
        "dev": _uint,
        "ino": _uint,
        "nlink": _uint,
        "xattr_names": _list(_xattr_name, 64),
        "sha256": lambda v: HEX64(v) if v != "unreadable" else None,
    }
)


def _lease(value: object) -> None:
    _obj({name: _int_between(*bounds) for name, bounds in A2Pins._LEASE.items()})(value)
    assert isinstance(value, dict)
    _expect(value["start_window_s"] < value["lease_s"], "lease_s must exceed start_window_s")


def _params(value: object) -> None:
    fields = set(Params.__dataclass_fields__) | {"sizing"}
    _obj({name: (_equals("necessary-conditions-met") if name == "sizing" else _uint) for name in fields})(value)
    assert isinstance(value, dict)
    try:
        Params(**{name: item for name, item in value.items() if name != "sizing"})
    except AuthorityError as exc:
        raise _Bad(str(exc)) from None


def _checks(value: object) -> None:
    _expect(type(value) is dict and set(value) <= ST1_CHECKS, "unknown ST-1 check")
    assert isinstance(value, dict)
    _expect(all(type(item) is bool for item in value.values()), "check is not a boolean")


def _children_entries(value: object) -> None:
    _list(_CHILD, MAX_CHILDREN)(value)
    assert isinstance(value, list)
    for child in value:
        _expect(child["s0_ran"] == (child["grace_deadline_ms"] != ABSENT), "s0_ran/grace_deadline_ms")
        _expect(child["outcome"] != "reap-error" or not child["s0_ran"], "reap-error after S0")


def _directory(value: object) -> None:
    _obj({"role": _one_of(DIRECTORY_ROLES), "path": _path, "class": _one_of(DIR_CLASSES)})(value)


def _capture(value: object) -> None:
    base = {"active_state": TOKEN, "inactive_enter_us": _uint}
    if type(value) is dict and "invocation_id" in value:
        _obj({**base, "invocation_id": _or_absent(_pattern(_HEX32))})(value)
    else:
        _obj(base)(value)


def _grant_check(value: object) -> None:
    base = {
        "procedure": _equals(PROCEDURE),
        "authorized_at_act": _one_of(frozenset({"authorized"}) | {ABSENT}),
        "after_cleanup": _or_absent(_one_of(frozenset(o.value for o in PkOutcome))),
    }
    if type(value) is dict and "stop_control" in value:
        _obj({**base, "stop_control": _one_of(frozenset(o.value for o in PkOutcome))})(value)
    else:
        _obj(base)(value)


_FAILURE = _obj({"step": _pattern(_STEP), "class": _one_of(FAILURE_CLASSES)})

_FIELDS: dict[str, Check] = {
    "schema": _equals(SCHEMA),
    "kind": _one_of(frozenset(OUTCOMES)),
    "activation_id": _pattern(_ACTIVATION),
    "attempt": _int_between(0, 99),
    "trigger": _one_of(TRIGGERS),
    "authority": _obj({"a2_path": _path, "a2_sha256": HEX64}),
    "authority_limit": _equals(AUTHORITY_LIMIT),
    "h1_record": _or_absent(_obj({"record_id": _pattern(_RECORD_ID), "sha256": HEX64})),
    "h2_record_sha256": DIGEST_OR_ABSENT,
    "boot": _obj(
        {
            "pinned": BOOT_OR_ABSENT,
            "act_boot": BOOT_OR_ABSENT,
            "observed_at_start": BOOT_OR_ABSENT,
            "observed_at_end": BOOT_OR_ABSENT,
            "run_fstype": _or_absent(_pattern(_FSTYPE)),
        }
    ),
    "pass_config": _obj(
        {
            "path": _path,
            "sha256_pinned": DIGEST_OR_ABSENT,
            "identity": IDENTITY_OR_ABSENT,
            "class": _or_absent(_one_of(PASS_CLASSES)),
        }
    ),
    "staged_rule": _obj({"sha256": DIGEST_OR_ABSENT}),
    "active_rule": _obj(
        {
            "path": _path,
            "sha256_expected": DIGEST_OR_ABSENT,
            "identity": IDENTITY_OR_ABSENT,
            "class": _or_absent(_one_of(RULE_CLASSES)),
        }
    ),
    "grant_check": _grant_check,
    "unit": _obj({"active_state_at_start": TOKEN_OR_ABSENT, "active_state_at_end": TOKEN_OR_ABSENT}),
    "lease": _or_absent(_lease),
    "holder": _obj(
        {
            "unit": _pattern(re.compile(r"rp11-act-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}\.service")),
            "invocation_id": _or_absent(_pattern(_HEX32)),
            "active_state_at_start": TOKEN,
            "result": TOKEN_OR_ABSENT,
            "hold_end_reason": TOKEN_OR_ABSENT,
        }
    ),
    "consume": _obj(
        {
            "class": _or_absent(_one_of(CONSUME_CLASSES)),
            "outcome": _or_absent(_one_of(CONSUME_OUTCOMES)),
        }
    ),
    "directories": _list(_directory, MAX_DIRECTORIES),
    "lock": _obj(
        {
            "object": IDENTITY_OR_ABSENT,
            "mode": _one_of(frozenset(mode.value for mode in LockMode)),
            "wait_ms": _uint,
        }
    ),
    "grant_identity": _obj(
        {
            "source": _one_of(frozenset({"grant.id", "journal", ABSENT})),
            "conflict": _bool,
            "cl_g": _or_absent(_one_of(GRR_OUTCOMES)),
            "grant_id_class": _or_absent(_one_of(PASS_CLASSES)),
        }
    ),
    "pk": _obj(
        {
            "procedure": _equals(PROCEDURE),
            "mode": _or_absent(_one_of(frozenset(mode.value for mode in PkMode))),
            "op_ms": _uint,
            "call_ms": _uint,
            "reap_grace_ms": _uint,
            "calls": _uint,
            "abandoned": _uint,
            "signals": _signals,
            "elapsed_ms": _uint,
            "outcome": _or_absent(_one_of(frozenset(o.value for o in PkOutcome))),
            "reason": TOKEN_OR_ABSENT,
        }
    ),
    "children": _obj({"entries": _children_entries, "overflow": _uint}),
    "release": _obj(
        {
            "first_rung": _one_of(frozenset({"igr", "cl-g", "stop-post", ABSENT})),
            "igr": _one_of(frozenset({"removed", ABSENT})),
        }
    ),
    "capture": _or_absent(_capture),
    "helper": _obj(
        {
            "role": _one_of(HELPER_ROLES),
            "image_sha256": _distinct_images,
            "tool_sha256": DIGEST_OR_ABSENT,
        }
    ),
    "params": _params,
    "st1": _obj(
        {
            "verified": _bool,
            "baseline_sha256_observed": DIGEST_OR_ABSENT,
            "first_difference": _or_absent(_pattern(_KEY_PATH)),
            "checks": _checks,
        }
    ),
    "journals": _list(_obj({"path": _path, "sha256": DIGEST_OR_ABSENT, "length": _uint}), MAX_JOURNALS),
    "act_record_sha256": DIGEST_OR_ABSENT,
    "outcome": _one_of(frozenset().union(*OUTCOMES.values())),
    "failure": _or_absent(_FAILURE),
    "residual": _list(_RESIDUAL, MAX_RESIDUAL),
    "evidence_mode": _one_of(frozenset({"journaled", "grant-priority"})),
    "time": _obj(
        {
            "start_utc": UTC_OR_ABSENT,
            "end_utc": UTC_OR_ABSENT,
            "grant_linked_utc": UTC_OR_ABSENT,
            "grant_removed_utc": UTC_OR_ABSENT,
        }
    ),
}

assert set(_FIELDS) == RECORD_KEYS


# --- cross-field relations ---------------------------------------------------------


def _cross_identity(doc: dict) -> None:
    kind, outcome, attempt = doc["kind"], doc["outcome"], doc["attempt"]
    _expect(outcome in OUTCOMES[kind], "outcome does not belong to the kind")
    _expect(attempt == 0 if kind == "act" else 1 <= attempt <= 99, "attempt")
    activated = kind == "act" and outcome == "activated"
    _expect((doc["trigger"] == "act") == activated, "trigger/outcome")
    _expect(doc["holder"]["unit"] == f"{doc['activation_id']}.service", "holder.unit")
    _expect(doc["authority"]["a2_path"].endswith(f"/a2/{doc['authority']['a2_sha256']}.json"), "authority.a2_path")
    failure = doc["failure"]
    _expect((failure == ABSENT) == (outcome in {"st1-verified", "activated"}), "failure/outcome")
    st1 = doc["st1"]
    _expect(st1["verified"] == (outcome == "st1-verified"), "st1/outcome")
    _expect(st1["verified"] is False or all(st1["checks"].values()), "st1.checks")
    if kind == "act":
        _expect(doc["act_record_sha256"] == ABSENT, "an act record names no act record")
    else:
        _expect(doc["act_record_sha256"] != ABSENT, "a deactivation record chains the act record")
    journals = doc["journals"]
    own = "-act-evidence/journal" if kind == "act" else f"-deact-{attempt}-evidence/journal"
    if activated:
        _expect(len(journals) == 1 and journals[0]["path"].endswith(f"{doc['activation_id']}{own}"), "journals")
    elif kind == "deact":
        _expect(bool(journals) and journals[-1]["path"].endswith(f"{doc['activation_id']}{own}"), "journals")


def _cross_activated(doc: dict) -> None:
    """ACT: the activated record states the grant seen and nothing about cleanup."""
    check = doc["grant_check"]
    _expect(check.get("stop_control") == "not-authorized", "grant_check.stop_control")
    _expect(check["authorized_at_act"] == "authorized" and check["after_cleanup"] == ABSENT, "grant_check")
    pk = doc["pk"]
    _expect(pk["outcome"] == "authorized" and pk["mode"] == "seek-authorized", "pk")
    _expect(doc["lock"]["mode"] == "held" and doc["lock"]["object"] != ABSENT, "lock")
    _expect(doc["helper"]["role"] == "hold" and bool(doc["helper"]["image_sha256"]), "helper")
    _expect(doc["helper"]["tool_sha256"] != ABSENT and doc["h1_record"] != ABSENT, "authority pins")
    _expect(doc["h2_record_sha256"] != ABSENT and doc["lease"] != ABSENT, "authority pins")
    _expect(doc["capture"] != ABSENT and "invocation_id" in doc["capture"], "capture")
    _expect(doc["directories"] == [] and doc["residual"] == [], "an activated record holds no cleanup facts")
    _expect(doc["st1"]["checks"] == {}, "st1.checks")
    _expect(doc["evidence_mode"] == "journaled", "evidence_mode")
    classes = (
        doc["active_rule"]["class"],
        doc["pass_config"]["class"],
        doc["grant_identity"]["cl_g"],
        doc["grant_identity"]["grant_id_class"],
    )
    _expect(all(c == ABSENT for c in classes), "an activated record states no cleanup class")
    _expect(doc["active_rule"]["identity"] != ABSENT and doc["pass_config"]["identity"] != ABSENT, "identities")


def _cross_cleanup(doc: dict) -> None:
    """A record written by CL-7 (a failed ACT record or a deactivation record)."""
    _expect(doc["active_rule"]["class"] != ABSENT, "active_rule.class is stated")
    _expect(doc["pass_config"]["class"] != ABSENT, "pass_config.class is stated")
    _expect(doc["grant_identity"]["grant_id_class"] != ABSENT, "grant_id_class is stated")
    _expect(doc["evidence_mode"] == "journaled", "a published cleanup record is journaled")
    _expect(set(doc["st1"]["checks"]) == ST1_CHECKS, "CL-6 states every ST-1 check")
    _expect(doc["helper"]["role"] in {"stop-post", "backstop", "attest"}, "helper.role")
    _expect(doc["helper"]["role"] == doc["trigger"], "helper.role/trigger")
    _expect("stop_control" not in doc["grant_check"], "grant_check")
    _cross_pk(doc)
    if doc["kind"] == "act":
        _expect(doc["failure"] == {"step": "CL-7", "class": "act-unconfirmed"}, "failed act failure")


def _cross_pk(doc: dict) -> None:
    """CL-4's post-cleanup Polkit check, stated once in ``pk`` and once in ``grant_check``
    and ``st1.checks``: the three must agree, and a positive ``not-authorized`` must be
    one a ``seek-not-authorized`` series could have reached (a decided call, a settled
    subject), so that no hollow or contradictory claim can select BS-2 or BS-3."""
    pk, check = doc["pk"], doc["grant_check"]
    outcome = pk["outcome"]
    _expect(check["after_cleanup"] == outcome, "grant_check.after_cleanup/pk.outcome")
    _expect(
        doc["st1"]["checks"]["pk-not-authorized"] == (outcome == PkOutcome.NOT_AUTHORIZED.value),
        "st1.checks.pk-not-authorized/pk.outcome",
    )
    children = doc["children"]
    seen = len(children["entries"]) + children["overflow"]
    if outcome == ABSENT:  # CL-4 did not run: nothing is claimed
        _expect(pk["mode"] == ABSENT and pk["reason"] == ABSENT, "pk without outcome")
        _expect(pk["calls"] == 0 and pk["abandoned"] == 0 and pk["elapsed_ms"] == 0, "pk without outcome")
        _expect(seen == 0 and all(n == 0 for n in pk["signals"].values()), "pk without outcome")
        return
    # cleanup only ever seeks non-authorization: ``authorized`` cannot be its result
    _expect(outcome in {PkOutcome.NOT_AUTHORIZED.value, PkOutcome.UNCONFIRMED.value}, "pk.outcome")
    _expect(pk["mode"] == PkMode.SEEK_NOT_AUTHORIZED.value, "pk.mode")
    _expect(seen <= pk["calls"], "pk.calls/children")
    _expect(pk["abandoned"] <= seen, "pk.abandoned")
    if children["overflow"] == 0:
        _expect(pk["abandoned"] == sum(1 for e in children["entries"] if e["abandoned"]), "pk.abandoned")
    if outcome == PkOutcome.NOT_AUTHORIZED.value:
        _expect(pk["reason"] == "decided" and pk["calls"] >= 1 and seen >= 1, "pk: not-authorized undecided")
    else:
        _expect(pk["reason"] in PK_UNCONFIRMED_REASONS, "pk.reason")
        _expect(pk["reason"] != "still-authorized" or (pk["calls"] >= 1 and seen >= 1), "pk.reason")


def _cross_verified(doc: dict) -> None:
    """ST-1 as BS-2 relies on it: every class clean, Polkit *not authorized*, baseline and
    capture unit checked, nothing but S0 left, and every authority fact present."""
    _expect(doc["active_rule"]["class"] in RULE_VERIFIED, "active_rule.class")
    _expect(doc["pass_config"]["class"] in PASS_VERIFIED, "pass_config.class")
    _expect(doc["grant_identity"]["grant_id_class"] in PASS_VERIFIED, "grant_id_class")
    _expect(all(d["class"] in DIR_VERIFIED for d in doc["directories"]), "directories")
    _expect(all(r["class"] == "s0" for r in doc["residual"]), "residual")
    _expect(doc["grant_check"]["after_cleanup"] == "not-authorized", "grant_check.after_cleanup")
    _expect(doc["pk"]["outcome"] == "not-authorized", "pk.outcome")
    _expect(doc["st1"]["baseline_sha256_observed"] != ABSENT, "st1.baseline_sha256_observed")
    _expect(doc["h1_record"] != ABSENT and doc["lease"] != ABSENT, "authority pins")
    _expect(doc["boot"]["pinned"] != ABSENT and doc["boot"]["observed_at_start"] != ABSENT, "boot")
    _expect(doc["unit"]["active_state_at_end"] in {"inactive", "failed"}, "unit.active_state_at_end")


# --- the entry point -----------------------------------------------------------------


def validate_record(doc: object) -> None:
    """Raise ``RecordSchemaError`` (only) unless ``doc`` is a well-formed record."""
    try:
        _validate(doc)
    except _Bad as exc:
        raise RecordSchemaError(str(exc)) from None


def _validate(doc: object) -> None:
    _expect(type(doc) is dict, "record is not an object")
    assert isinstance(doc, dict)
    _expect(set(doc) == RECORD_KEYS, f"keys differ: {sorted(set(doc) ^ RECORD_KEYS)}")
    try:
        check_value(doc)
    except CanonicalError as exc:
        raise _Bad(str(exc)) from None
    for name, check in _FIELDS.items():
        try:
            check(doc[name])
        except _Bad as exc:
            raise _Bad(f"{name}: {exc}") from None
    _cross_identity(doc)
    if doc["kind"] == "act" and doc["outcome"] == "activated":
        _cross_activated(doc)
    else:
        _cross_cleanup(doc)
    if doc["outcome"] == "st1-verified":
        _cross_verified(doc)
