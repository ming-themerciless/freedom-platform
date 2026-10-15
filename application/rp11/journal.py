"""Journal format ``rp11-journal/1``: closed ``op`` sets, line serialization and parsing.

Every line is ``canonical_bytes(entry)`` with ``seq`` (1, 2, … without a gap),
``prev`` (SHA-256 of the previous line's exact bytes; 64 ``0`` for ``seq`` 1),
``run``, ``op`` and exactly the closed fields of that ``op`` (H-JRN.4, H-JRN.5).

Parsing (H-JRN.9) splits at LF; a final segment without LF is a torn tail,
ignored and reported. Every complete line must be canonical, contiguous,
chained, of the expected ``run``, of a known ``op`` and carry exactly its
fields. Any violation makes the whole journal invalid, and an invalid journal
attributes nothing (every object is A0).

The accepted text names the ``op`` sets and some field lists; the remaining
field lists below are this implementation's choice, pinned by tests:

* the ``run`` of the ``ACT`` journal is the activation id, of a CL attempt
  journal ``<activation_id>-deact-<k>`` and of the consume journal
  ``<activation_id>-consume``;
* ``dir`` in ``file-*`` lines is the object's final absolute directory, also for
  a tree member published while the tree still had its temporary name;
* ``dir-identity`` belongs to the most recent ``tree-intent``;
* ``ACT`` ``run-start`` carries exactly RT2.AM0.16's fields, with ``lock``
  ``{object, mode "held", wait_ms}`` (the holder writes it only after K is
  created and locked by its one attempt), ``helper.role`` ``hold`` and
  ``helper.tool_sha256`` equal to ``tool_sha256``;
* ``ACT`` ``igr`` is ``{outcome, identity}`` (RT2.IGR.3): the GRR outcome and
  the in-memory grant identity it used, or ``"absent"`` when AM-1G never
  produced one (then the outcome can only be ``absent``);
* ``ACT`` ``run-end`` (RT2.AM3.2) is the holder's last line, written best effort
  after IGR from the same ``finally``; ``outcome`` is the holder's end class
  (``ACT_RUN_END_OUTCOMES``), so it never states success for an incomplete
  activation. ``hold-end`` stays the complete-end line of HL.

There is one grammar per ``op``; a journal written to an earlier field list is
invalid, not accepted alongside (this inactive slice has no production journals
to stay compatible with).
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum

from .canonical import ABSENT, CanonicalError, canonical_bytes, parse_canonical

GENESIS = "0" * 64
_HEX64 = re.compile(r"[0-9a-f]{64}")
_HEX32 = re.compile(r"[0-9a-f]{32}")
_TOKEN = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
_NAME = re.compile(r"[A-Za-z0-9_.][A-Za-z0-9_.-]{0,254}")
_BOOT_ID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_MAX_PATH = 4096

Validator = Callable[[object], bool]


# --- field grammars ---------------------------------------------------------


def _str(pattern: re.Pattern[str]) -> Validator:
    return lambda v: type(v) is str and pattern.fullmatch(v) is not None


def _uint(v: object) -> bool:
    return type(v) is int and 0 <= v <= 0xFFFFFFFFFFFFFFFF


def _bool(v: object) -> bool:
    return type(v) is bool


def _path(v: object) -> bool:
    return (
        type(v) is str
        and v.startswith("/")
        and len(v) <= _MAX_PATH
        and "//" not in v
        and "\x00" not in v
        and all(part not in (".", "..") for part in v.split("/")[1:])
        and v.isascii()
    )


def _mode(v: object) -> bool:
    return type(v) is int and 0 <= v <= 0o7777


def _or_absent(inner: Validator) -> Validator:
    return lambda v: v == ABSENT or inner(v)


def _object(fields: Mapping[str, Validator]) -> Validator:
    def check(v: object) -> bool:
        return (
            type(v) is dict
            and set(v) == set(fields)
            and all(fields[k](v[k]) for k in fields)
        )

    return check


def _list(inner: Validator, limit: int) -> Validator:
    return lambda v: type(v) is list and len(v) <= limit and all(inner(i) for i in v)


def _any_of(*options: Validator) -> Validator:
    return lambda v: any(option(v) for option in options)


def _one_of(values: frozenset[str]) -> Validator:
    return lambda v: type(v) is str and v in values


def _distinct_digests(limit: int) -> Validator:
    """A non-empty list of at most ``limit`` distinct SHA-256 digests."""
    return lambda v: (
        type(v) is list
        and 0 < len(v) <= limit
        and all(HEX64(i) for i in v)
        and len(set(v)) == len(v)
    )


HEX64 = _str(_HEX64)
TOKEN = _str(_TOKEN)
NAME = _str(_NAME)
BOOT_ID = _str(_BOOT_ID)
INVOCATION = _or_absent(_str(_HEX32))
UINT = _uint
PATH = _path

_IDENTITY = _object({"path": PATH, "dev": UINT, "ino": UINT})
_DIR_MEMBER = _object({"rel": _str(re.compile(r"\.|[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)*")), "kind": lambda v: v == "dir", "mode": _mode})
_FILE_MEMBER = _object(
    {
        "rel": _str(re.compile(r"[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)*")),
        "kind": lambda v: v == "file",
        "mode": _mode,
        "sha256": HEX64,
        "size": UINT,
    }
)
_CHILD = lambda v: type(v) is dict and len(v) <= 32  # noqa: E731 - schema in records


def _uint_map(limit: int) -> Validator:
    """An object of at most ``limit`` token-named unsigned integers (``lease``, ``params``)."""
    return lambda v: (
        type(v) is dict
        and 0 < len(v) <= limit
        and all(_TOKEN.fullmatch(k.replace("_", "-")) and _uint(i) for k, i in v.items())
    )


# HL's observation as ``hold-end`` records it (``"absent"`` when it failed).
_HL_OBSERVATION = _or_absent(
    _object(
        {
            "active_state": TOKEN,
            "invocation_id": INVOCATION,
            "inactive_enter_us": UINT,
            "job": UINT,
            "exec_main_start_us": UINT,
            "capture_root": _bool,
            "claim": _bool,
            "consumed": _bool,
        }
    )
)


# --- closed op sets ----------------------------------------------------------


class JournalKind(str, Enum):
    ACT = "act"
    ATTEMPT = "attempt"
    CONSUME = "consume"


_FILE_INTENT = {
    "dir": PATH,
    "name": NAME,
    "sha256": HEX64,
    "size": UINT,
    "uid": UINT,
    "gid": UINT,
    "mode": _mode,
    "grant": _bool,
}
_FILE_IDENTITY = {"dir": PATH, "name": NAME, "dev": UINT, "ino": UINT}
_FILE_LINKED = {"dir": PATH, "name": NAME}
_REMOVE_INTENT = {"path": PATH, "dev": UINT, "ino": UINT, "sha256": _or_absent(HEX64)}
_REMOVED = {"path": PATH}
_REMOVE_FAILED = {"path": PATH, "errno": UINT}
_GRANT_CHECK = {"verb": TOKEN, "mode": TOKEN, "outcome": TOKEN, "reason": TOKEN, "calls": UINT}
_RUN_END = {"outcome": TOKEN}
_CHILD_LINE = {"entry": _CHILD}

# The holder's end classes (``application.rp11.hold.HoldEnd``) plus the end of an
# unexpected exception; a test keeps this equal to ``HoldEnd``.
ACT_RUN_END_OUTCOMES = frozenset(
    {
        "hold-ended",
        "invalid-authority",
        "precondition",
        "lock-object",
        "capture-baseline-unstable",
        "capture-busy-at-act",
        "evidence-unwritable",
        "backstop-unconfirmed",
        "publication-failed",
        "grant-not-seen",
        "stop-control-unconfirmed",
        "stop-control-authorized",
        "verification-failed",
        "act-record-unpublished",
        "start-before-hold",
        "observation-failed",
        "interrupted",
        "internal-error",
    }
)
# GRR outcomes the holder's IGR can reach (it never lacks the in-memory identity
# it would need for ``identity-unavailable``).
IGR_OUTCOMES = frozenset(
    {"removed", "absent", "kept-damaged", "kept-foreign", "kept-uninspected", "unremovable"}
)
MAX_IMAGES = 16

# The in-memory grant identity GRR re-verifies against (RT2.IGR.2 … .3).
_GRANT_IDENTITY = _object(
    {"path": PATH, "dev": UINT, "ino": UINT, "sha256": HEX64, "size": UINT, "mode": _mode}
)


def _act_run_start_consistent(fields: Mapping[str, object]) -> bool:
    return fields["helper"]["tool_sha256"] == fields["tool_sha256"]


def _igr_consistent(fields: Mapping[str, object]) -> bool:
    return fields["identity"] != ABSENT or fields["outcome"] == "absent"


# Relations between the fields of one line, checked after each field's grammar.
_CROSS: dict[tuple[JournalKind, str], Callable[[Mapping[str, object]], bool]] = {
    (JournalKind.ACT, "run-start"): _act_run_start_consistent,
    (JournalKind.ACT, "igr"): _igr_consistent,
}

OPS: dict[JournalKind, dict[str, dict[str, Validator]]] = {
    JournalKind.ACT: {
        "run-start": {
            "a2_sha256": HEX64,
            "h1_record_sha256": HEX64,
            "h2_record_sha256": HEX64,
            "boot_id": BOOT_ID,
            "pass_config_sha256": HEX64,
            "staged_rule_sha256": HEX64,
            "lock": _object(
                {
                    "object": _IDENTITY,
                    "mode": lambda v: v == "held",
                    "wait_ms": UINT,
                }
            ),
            "capture": _object(
                {
                    "active_state": TOKEN,
                    "invocation_id": INVOCATION,
                    "inactive_enter_us": UINT,
                    "m_a_us": UINT,
                    "bsp_retries": UINT,
                }
            ),
            "holder_invocation_id": INVOCATION,
            "tool_sha256": HEX64,
            "helper": _object(
                {
                    "role": lambda v: v == "hold",
                    "image_sha256": _distinct_digests(MAX_IMAGES),
                    "tool_sha256": HEX64,
                }
            ),
            "lease": _uint_map(8),
            "params": _uint_map(16),
        },
        "backstop-intent": {"timer": NAME},
        "backstop-armed": {"timer": NAME, "period_s": UINT, "max": UINT, "runtime_s": UINT},
        "tree-intent": {
            "parent": PATH,
            "top": NAME,
            "temp": NAME,
            "tag": TOKEN,
            "members": _list(_any_of(_DIR_MEMBER, _FILE_MEMBER), 64),
        },
        "dir-identity": {"rel": _str(re.compile(r"\.|[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)*")), "dev": UINT, "ino": UINT},
        "file-intent": _FILE_INTENT,
        "file-identity": _FILE_IDENTITY,
        "file-linked": _FILE_LINKED,
        "tree-sealed": {"temp": NAME, "inventory_sha256": HEX64},
        "tree-linked": {"parent": PATH, "top": NAME},
        "grant-check": _GRANT_CHECK,
        "hold-start": {
            "capture": _object({"active_state": TOKEN, "inactive_enter_us": UINT}),
        },
        "pass-observed": {"active_state": TOKEN, "invocation_id": INVOCATION},
        "hold-end": {"reason": TOKEN, "observation": _HL_OBSERVATION},
        "run-end": {"outcome": _one_of(ACT_RUN_END_OUTCOMES)},
        "igr": {"outcome": _one_of(IGR_OUTCOMES), "identity": _or_absent(_GRANT_IDENTITY)},
        "child": _CHILD_LINE,
    },
    JournalKind.ATTEMPT: {
        "run-start": {
            "trigger": TOKEN,
            "boot_id": BOOT_ID,
            "holder_state": TOKEN,
            "lock": _object(
                {
                    "object": _or_absent(_IDENTITY),
                    "mode": TOKEN,
                    "wait_ms": UINT,
                }
            ),
            "helper": _object({"role": TOKEN, "tool_sha256": _or_absent(HEX64)}),
            "provenance": _object({"parent_pid": UINT, "invocation_id": INVOCATION}),
        },
        "remove-intent": _REMOVE_INTENT,
        "removed": _REMOVED,
        "remove-failed": _REMOVE_FAILED,
        "grant-check": _GRANT_CHECK,
        "classified": {"object": TOKEN, "path": PATH, "class": TOKEN},
        "file-intent": _FILE_INTENT,
        "file-identity": _FILE_IDENTITY,
        "file-linked": _FILE_LINKED,
        "run-end": _RUN_END,
        "cl-g": {"outcome": TOKEN, "errno": UINT},
        "child": _CHILD_LINE,
    },
    JournalKind.CONSUME: {
        "run-start": {"boot_id": BOOT_ID, "invocation_id": INVOCATION},
        "remove-intent": _REMOVE_INTENT,
        "removed": _REMOVED,
        "remove-failed": _REMOVE_FAILED,
        "grant-check": _GRANT_CHECK,
        "consumed": {},
        "consume-failed": {"step": TOKEN, "class": TOKEN},
        "run-end": _RUN_END,
        "child": _CHILD_LINE,
    },
}


def attempt_run(activation_id: str, k: int) -> str:
    return f"{activation_id}-deact-{k}"


def consume_run(activation_id: str) -> str:
    return f"{activation_id}-consume"


# --- lines ------------------------------------------------------------------


@dataclass(frozen=True)
class JournalLine:
    seq: int
    op: str
    fields: Mapping[str, object]
    raw: bytes

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.raw).hexdigest()


class JournalSchemaError(ValueError):
    pass


def check_fields(kind: JournalKind, op: str, fields: Mapping[str, object]) -> None:
    schema = OPS[kind].get(op)
    if schema is None:
        raise JournalSchemaError(f"unknown op {op!r} for a {kind.value} journal")
    if set(fields) != set(schema):
        raise JournalSchemaError(f"{op}: fields are not exactly the closed set")
    for name, valid in schema.items():
        if not valid(fields[name]):
            raise JournalSchemaError(f"{op}: field {name} outside its grammar")
    cross = _CROSS.get((kind, op))
    if cross is not None and not cross(fields):
        raise JournalSchemaError(f"{op}: fields are inconsistent")


def serialize_line(
    kind: JournalKind, *, seq: int, prev: str, run: str, op: str, fields: Mapping[str, object]
) -> bytes:
    """The exact bytes of one line; raises on any schema violation."""
    check_fields(kind, op, fields)
    reserved = {"seq", "prev", "run", "op"} & set(fields)
    if reserved:
        raise JournalSchemaError("a field shadows a line header")
    if type(seq) is not int or seq < 1 or not HEX64(prev):
        raise JournalSchemaError("bad line header")
    return canonical_bytes({**fields, "seq": seq, "prev": prev, "run": run, "op": op})


# --- parsing ----------------------------------------------------------------


@dataclass(frozen=True)
class ParsedJournal:
    """A parse result. ``valid`` is false for any violation; ``lines`` is then empty."""

    valid: bool
    lines: tuple[JournalLine, ...] = ()
    torn_tail: bool = False
    reason: str = ""
    length: int = 0
    sha256: str = ""

    def ops(self, op: str) -> tuple[JournalLine, ...]:
        return tuple(line for line in self.lines if line.op == op)


def invalid(reason: str, data: bytes = b"") -> ParsedJournal:
    return ParsedJournal(
        valid=False, reason=reason, length=len(data), sha256=hashlib.sha256(data).hexdigest()
    )


def parse_journal(data: bytes, *, kind: JournalKind, run: str) -> ParsedJournal:
    digest = hashlib.sha256(data).hexdigest()
    segments = data.split(b"\n")
    torn = segments[-1] != b""
    complete = segments[:-1]
    lines: list[JournalLine] = []
    prev = GENESIS
    for index, segment in enumerate(complete, start=1):
        raw = segment + b"\n"
        try:
            entry = parse_canonical(raw)
        except CanonicalError as exc:
            return invalid(f"line {index}: {exc}", data)
        if type(entry) is not dict:
            return invalid(f"line {index}: not an object", data)
        header = {k: entry.get(k) for k in ("seq", "prev", "run", "op")}
        if header["seq"] != index or type(header["seq"]) is not int:
            return invalid(f"line {index}: seq is not contiguous", data)
        if header["prev"] != prev:
            return invalid(f"line {index}: prev does not chain", data)
        if header["run"] != run:
            return invalid(f"line {index}: unexpected run", data)
        op = header["op"]
        fields = {k: v for k, v in entry.items() if k not in header}
        try:
            check_fields(kind, op if type(op) is str else "", fields)
        except JournalSchemaError as exc:
            return invalid(f"line {index}: {exc}", data)
        lines.append(JournalLine(seq=index, op=op, fields=fields, raw=raw))
        prev = hashlib.sha256(raw).hexdigest()
    if not lines:
        return invalid("no complete line", data)
    if [line.seq for line in lines if line.op == "run-start"] != [1]:
        return invalid("run-start is not exactly the first line", data)
    return ParsedJournal(
        valid=True, lines=tuple(lines), torn_tail=torn, length=len(data), sha256=digest
    )


def last_digest(parsed: ParsedJournal) -> str:
    return parsed.lines[-1].digest if parsed.lines else GENESIS
