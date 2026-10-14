"""Activation records, schema ``rp11-activation-record/2`` (H-REC.1 … H-REC.4).

A record is ``canonical_bytes`` of exactly the closed keys below; no extra key,
no ``null``, no float, no environment content and no content of any object.
Records are published once (PF, ``0444``, no replace) and never rewritten or
deleted. ``validate_record`` is the schema check every published record passes.
"""

from __future__ import annotations

import re

from .canonical import ABSENT, CanonicalError, check_value

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

_HEX64 = re.compile(r"[0-9a-f]{64}")
_KEY_PATH = re.compile(r"[A-Za-z0-9_.\[\]-]{1,256}")


class RecordSchemaError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RecordSchemaError(message)


def _digest_or_absent(value: object) -> bool:
    return value == ABSENT or (type(value) is str and _HEX64.fullmatch(value) is not None)


def validate_record(doc: object) -> None:
    """Raise ``RecordSchemaError`` unless ``doc`` is a well-formed record."""
    _require(type(doc) is dict, "record is not an object")
    assert isinstance(doc, dict)
    _require(set(doc) == RECORD_KEYS, f"keys differ: {sorted(set(doc) ^ RECORD_KEYS)}")
    try:
        check_value(doc)
    except CanonicalError as exc:
        raise RecordSchemaError(str(exc)) from exc
    _require(doc["schema"] == SCHEMA, "schema")
    kind = doc["kind"]
    _require(kind in OUTCOMES, "kind")
    _require(doc["outcome"] in OUTCOMES[kind], "outcome")
    _require(doc["trigger"] in TRIGGERS, "trigger")
    attempt = doc["attempt"]
    _require(type(attempt) is int and (attempt == 0 if kind == "act" else 1 <= attempt <= 99), "attempt")
    _require(doc["active_rule"]["class"] in RULE_CLASSES | {ABSENT}, "rule class")
    _require(doc["pass_config"]["class"] in PASS_CLASSES | {ABSENT}, "pass class")
    for entry in doc["directories"]:
        _require(entry["class"] in DIR_CLASSES, "directory class")
    failure = doc["failure"]
    _require(
        failure == ABSENT
        or (type(failure) is dict and set(failure) == {"step", "class"} and failure["class"] in FAILURE_CLASSES),
        "failure",
    )
    _require((failure == ABSENT) == (doc["outcome"] in {"st1-verified", "activated"}), "failure/outcome")
    _require(doc["evidence_mode"] in {"journaled", "grant-priority"}, "evidence_mode")
    _require(_digest_or_absent(doc["act_record_sha256"]), "act_record_sha256")
    st1 = doc["st1"]
    _require(type(st1["verified"]) is bool, "st1.verified")
    _require(st1["verified"] == (doc["outcome"] == "st1-verified"), "st1/outcome")
    _require(
        st1["first_difference"] == ABSENT or _KEY_PATH.fullmatch(st1["first_difference"]) is not None,
        "st1.first_difference",
    )
    for journal in doc["journals"]:
        _require(set(journal) == {"path", "sha256", "length"}, "journal entry")
        _require(_digest_or_absent(journal["sha256"]), "journal sha256")
    children = doc["children"]
    _require(set(children) == {"entries", "overflow"} and len(children["entries"]) <= 64, "children")
    for child in children["entries"]:
        _require(
            child["s0_ran"] == (child["grace_deadline_ms"] != ABSENT), "children s0_ran/grace"
        )
        _require(child["outcome"] != "reap-error" or not child["s0_ran"], "children reap-error")
    for item in doc["residual"]:
        _require(
            set(item)
            == {"path", "class", "type", "uid", "gid", "mode", "size", "dev", "ino", "nlink", "xattr_names", "sha256"},
            "residual entry",
        )
