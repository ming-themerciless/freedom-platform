"""A-2 pins, the H-1 record and the parameters cleanup runs with.

The role receives only the activation id and A-2's SHA-256. Everything else it
uses comes from root-owned files whose digests chain from that operand:

    operand a2_sha256 ─▶ A-2 file (digest equal) ─▶ h1_record_sha256 ─▶ H-1 record

Neither is taken from the environment, the caller or a browser. Formats are
this implementation's choice (the accepted text leaves the A-2 and H-1 locators
open, Q4-6), canonical JSON, pinned by tests:

* A-2: ``/var/lib/freedom-blades-rp11/a2/<a2_sha256>.json``, schema
  ``rp11-a2/3``. It quotes the complete ``pass-a.json`` document (``pass_config``,
  whose ``canonical_bytes`` hash to ``pass_config_sha256``), the staged rule's
  ``(dev, ino)`` (``staged_rule``; its path is ``ActivationPaths.staged_rule``),
  the lease, including ``bs_runtime_s`` (S_b, RT2.AK1.2), ``h2_record_sha256``
  and ``helper {image_sha256[], tool_sha256}`` — the tool and image digests
  RT2.AM0.1 lists among A-2's pins, recorded unchanged in ``run-start``
  (RT2.AM0.16). The holder additionally requires the installed tool to hash to
  ``helper.tool_sha256`` before it records it; ``image_sha256`` (1 … 16
  distinct digests) is taken from A-2 alone;
* H-1: ``/var/lib/freedom-blades-rp11/h1/<record_id>.json``, schema
  ``rp11-h1-record/1``, with ``baseline``, ``baseline_sha256`` and ``params``.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from .canonical import CanonicalError, canonical_bytes, parse_canonical

A2_SCHEMA = "rp11-a2/3"
MAX_IMAGES = 16
PASS_SCHEMA = "rp11-pass-a/1"
MAX_PASS_BYTES = 65_536  # the pass-a.json volume cap (inventory §11.1)
H1_SCHEMA = "rp11-h1-record/1"
MAX_A2_BYTES = 65_536
MAX_H1_BYTES = 1 << 20

AUTHORITY_LIMIT = (
    "Staging and activation separation on oracle-test is an authority boundary, "
    "not a privilege boundary: ubuntu has unrestricted sudo. ST-1 is not privilege-inert."
)

_HEX64 = re.compile(r"[0-9a-f]{64}")
_RECORD_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}")
_ACTIVATION = re.compile(r"rp11-act-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}")
_BOOT_ID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_USER = re.compile(r"[a-z_][a-z0-9_-]{0,31}")
_ABS_PATH = re.compile(r"(/[A-Za-z0-9_.][A-Za-z0-9_.-]{0,254}){1,32}")


class AuthorityError(ValueError):
    """A-2 or H-1 is missing, malformed or does not chain from the operand."""


def _int_in(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise AuthorityError(f"{name} outside {low}..{high}")
    return value


def _str_match(value: object, pattern: re.Pattern[str], name: str) -> str:
    if type(value) is not str or not pattern.fullmatch(value):
        raise AuthorityError(f"{name} malformed")
    return value


def _exact_keys(doc: object, keys: set[str], name: str) -> dict:
    if type(doc) is not dict or set(doc) != keys:
        raise AuthorityError(f"{name} does not have exactly its closed keys")
    return doc


@dataclass(frozen=True)
class Params:
    """R8 §7.6 values (inventory §11.1), each checked against its accepted range."""

    pk_op_ms: int = 30_000
    pk_call_ms: int = 5_000
    reap_grace_ms: int = 2_000
    lock_wait_ms: int = 5_000
    slice_ms: int = 100
    journal_max_bytes: int = 1_048_576
    backstop_max: int = 20  # B: most backstop firings that may enter CL (RT4.BS4.1)

    def __post_init__(self) -> None:
        _int_in(self.pk_op_ms, 5_000, 60_000, "pk_op_ms")
        _int_in(self.pk_call_ms, 1_000, 10_000, "pk_call_ms")
        if self.pk_call_ms > self.pk_op_ms:
            raise AuthorityError("pk_call_ms must not exceed pk_op_ms")
        _int_in(self.reap_grace_ms, 500, 5_000, "reap_grace_ms")
        _int_in(self.lock_wait_ms, 1_000, 10_000, "lock_wait_ms")
        _int_in(self.slice_ms, 50, 250, "slice_ms")
        _int_in(self.journal_max_bytes, 65_536, 4_194_304, "journal_max_bytes")
        _int_in(self.backstop_max, 1, 99, "backstop_max")

    @classmethod
    def from_doc(cls, doc: object) -> Params:
        fields = {f for f in cls.__dataclass_fields__}
        doc = _exact_keys(doc, fields, "params")
        return cls(**doc)

    def to_doc(self) -> dict[str, int]:
        return {name: getattr(self, name) for name in self.__dataclass_fields__}


@dataclass(frozen=True)
class Operator:
    """The account a Polkit subject runs as (H-1 ``baseline.operator``)."""

    user: str
    uid: int
    gid: int
    groups: tuple[int, ...]

    @classmethod
    def from_baseline(cls, baseline: dict) -> Operator:
        op = baseline.get("operator") if type(baseline) is dict else None
        op = _exact_keys(op, {"user", "uid", "gid", "groups"}, "operator")
        user = _str_match(op["user"], _USER, "operator.user")
        uid = _int_in(op["uid"], 1, 0x7FFFFFFF, "operator.uid")
        gid = _int_in(op["gid"], 1, 0x7FFFFFFF, "operator.gid")
        groups = op["groups"]
        if type(groups) is not list or len(groups) > 64:
            raise AuthorityError("operator.groups malformed")
        gids = []
        for entry in groups:
            if (
                type(entry) is not list
                or len(entry) != 2
                or type(entry[0]) is not str
                or not _USER.fullmatch(entry[0])
            ):
                raise AuthorityError("operator.groups entry malformed")
            gids.append(_int_in(entry[1], 0, 0x7FFFFFFF, "group gid"))
        if 0 in gids:
            raise AuthorityError("operator is in group 0")
        if gids != sorted(gids):
            raise AuthorityError("operator.groups not sorted by gid")
        return cls(user=user, uid=uid, gid=gid, groups=tuple(gids))


@dataclass(frozen=True)
class A2Pins:
    sha256: str
    activation_id: str
    h1_record_id: str
    h1_record_sha256: str
    boot_id: str
    pass_config_sha256: str
    staged_rule_sha256: str
    lease: dict[str, int]
    pass_config: dict
    staged_rule_dev: int
    staged_rule_ino: int
    h2_record_sha256: str
    image_sha256: tuple[str, ...]
    tool_sha256: str

    _KEYS = frozenset(
        {
            "schema",
            "activation_id",
            "h1_record_id",
            "h1_record_sha256",
            "h2_record_sha256",
            "helper",
            "boot_id",
            "pass_config",
            "pass_config_sha256",
            "staged_rule",
            "staged_rule_sha256",
            "lease",
            "authority_limit",
        }
    )
    _LEASE = {
        "start_window_s": (60, 3_600),  # W
        "lease_s": (61, 86_400),  # L
        "poll_ms": (250, 5_000),  # Δ
        "stop_timeout_s": (60, 600),  # S
        "backstop_period_s": (30, 600),  # R
        "bs_runtime_s": (60, 600),  # S_b
    }

    @property
    def capture_root(self) -> str:
        return self.pass_config["capture_root"]

    @property
    def pass_bytes(self) -> bytes:
        """The exact bytes AM-1 publishes: ``canonical_bytes`` of the quoted document."""
        return canonical_bytes(self.pass_config)

    @classmethod
    def parse(cls, data: bytes, *, operand_sha256: str, activation_id: str) -> A2Pins:
        if len(data) > MAX_A2_BYTES:
            raise AuthorityError("A-2 exceeds its volume cap")
        if hashlib.sha256(data).hexdigest() != operand_sha256:
            raise AuthorityError("A-2 digest differs from the operand")
        try:
            doc = parse_canonical(data)
        except CanonicalError as exc:
            raise AuthorityError(f"A-2 is not canonical: {exc}") from exc
        doc = _exact_keys(doc, set(cls._KEYS), "A-2")
        if doc["schema"] != A2_SCHEMA or doc["authority_limit"] != AUTHORITY_LIMIT:
            raise AuthorityError("A-2 schema or authority limit differs")
        if _str_match(doc["activation_id"], _ACTIVATION, "activation_id") != activation_id:
            raise AuthorityError("A-2 names another activation")
        lease = _exact_keys(doc["lease"], set(cls._LEASE), "lease")
        for name, (low, high) in cls._LEASE.items():
            _int_in(lease[name], low, high, name)
        if not lease["start_window_s"] < lease["lease_s"]:
            raise AuthorityError("lease_s must exceed start_window_s")
        pass_sha = _str_match(doc["pass_config_sha256"], _HEX64, "pass_config")
        pass_config = _pass_document(doc["pass_config"], pass_sha)
        staged = _exact_keys(doc["staged_rule"], {"dev", "ino"}, "staged_rule")
        helper = _exact_keys(doc["helper"], {"image_sha256", "tool_sha256"}, "helper")
        images = helper["image_sha256"]
        if (
            type(images) is not list
            or not 1 <= len(images) <= MAX_IMAGES
            or len(set(map(str, images))) != len(images)
        ):
            raise AuthorityError("helper.image_sha256 malformed")
        return cls(
            sha256=operand_sha256,
            activation_id=activation_id,
            h1_record_id=_str_match(doc["h1_record_id"], _RECORD_ID, "h1_record_id"),
            h1_record_sha256=_str_match(doc["h1_record_sha256"], _HEX64, "h1_record_sha256"),
            boot_id=_str_match(doc["boot_id"], _BOOT_ID, "boot_id"),
            pass_config_sha256=pass_sha,
            staged_rule_sha256=_str_match(doc["staged_rule_sha256"], _HEX64, "staged_rule"),
            lease=dict(lease),
            pass_config=pass_config,
            staged_rule_dev=_int_in(staged["dev"], 0, 0xFFFFFFFFFFFFFFFF, "staged_rule.dev"),
            staged_rule_ino=_int_in(staged["ino"], 1, 0xFFFFFFFFFFFFFFFF, "staged_rule.ino"),
            h2_record_sha256=_str_match(doc["h2_record_sha256"], _HEX64, "h2_record_sha256"),
            image_sha256=tuple(_str_match(i, _HEX64, "helper.image_sha256") for i in images),
            tool_sha256=_str_match(helper["tool_sha256"], _HEX64, "helper.tool_sha256"),
        )


def _pass_document(doc: object, pinned_sha256: str) -> dict:
    """The quoted ``pass-a.json`` document: an object within the volume cap whose
    ``canonical_bytes`` hash to the pin, of schema ``rp11-pass-a/1`` and naming an
    absolute ``capture_root``. Its other keys are opaque and published unchanged."""
    if type(doc) is not dict:
        raise AuthorityError("pass_config is not an object")
    try:
        data = canonical_bytes(doc)
    except CanonicalError as exc:
        raise AuthorityError(f"pass_config is not canonical: {exc}") from exc
    if len(data) > MAX_PASS_BYTES:
        raise AuthorityError("pass_config exceeds its volume cap")
    if hashlib.sha256(data).hexdigest() != pinned_sha256:
        raise AuthorityError("pass_config differs from its pinned digest")
    if doc.get("schema") != PASS_SCHEMA:
        raise AuthorityError("pass_config schema differs")
    root = doc.get("capture_root")
    if type(root) is not str or not _ABS_PATH.fullmatch(root) or "/../" in root + "/" or "/./" in root + "/":
        raise AuthorityError("pass_config capture_root malformed")
    return doc


@dataclass(frozen=True)
class H1Record:
    sha256: str
    record_id: str
    baseline: dict
    baseline_sha256: str
    params: Params
    operator: Operator

    @classmethod
    def parse(cls, data: bytes, *, pins: A2Pins) -> H1Record:
        if len(data) > MAX_H1_BYTES:
            raise AuthorityError("H-1 record exceeds its volume cap")
        digest = hashlib.sha256(data).hexdigest()
        if digest != pins.h1_record_sha256:
            raise AuthorityError("H-1 record digest differs from A-2's pin")
        try:
            doc = parse_canonical(data)
        except CanonicalError as exc:
            raise AuthorityError(f"H-1 record is not canonical: {exc}") from exc
        doc = _exact_keys(
            doc, {"schema", "record_id", "baseline", "baseline_sha256", "params"}, "H-1"
        )
        if doc["schema"] != H1_SCHEMA or doc["record_id"] != pins.h1_record_id:
            raise AuthorityError("H-1 schema or record id differs")
        baseline = doc["baseline"]
        if type(baseline) is not dict:
            raise AuthorityError("H-1 baseline malformed")
        baseline_sha256 = hashlib.sha256(canonical_bytes(baseline)).hexdigest()
        if doc["baseline_sha256"] != baseline_sha256:
            raise AuthorityError("H-1 baseline_sha256 does not match its baseline")
        return cls(
            sha256=digest,
            record_id=doc["record_id"],
            baseline=baseline,
            baseline_sha256=baseline_sha256,
            params=Params.from_doc(doc["params"]),
            operator=Operator.from_baseline(baseline),
        )


@dataclass(frozen=True)
class Authority:
    pins: A2Pins
    h1: H1Record


def load_authority(fs, paths, *, a2_sha256: str, activation_id: str) -> Authority:
    """Read A-2 by the operand, then the H-1 record it pins, from root-only ``0444``
    files (``fs.read_root_file``, ``paths.a2_file``/``h1_file``). Raises
    ``AuthorityError`` for anything missing or not chaining."""
    data = fs.read_root_file(paths.a2_file(a2_sha256), max_bytes=MAX_A2_BYTES, mode=0o444)
    if data is None:
        raise AuthorityError("A-2 file unavailable")
    pins = A2Pins.parse(data, operand_sha256=a2_sha256, activation_id=activation_id)
    h1_data = fs.read_root_file(paths.h1_file(pins.h1_record_id), max_bytes=MAX_H1_BYTES, mode=0o444)
    if h1_data is None:
        raise AuthorityError("H-1 record unavailable")
    return Authority(pins, H1Record.parse(h1_data, pins=pins))
