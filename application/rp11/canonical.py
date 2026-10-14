"""``canonical_bytes``: the one serialization of every RP-11 journal line and record.

Design §4.3.1: ``json.dumps(doc, sort_keys=True, separators=(",", ":"),
ensure_ascii=True, allow_nan=False) + "\\n"`` encoded as ASCII. Values are
strings, integers, booleans, lists and objects only: no floats and no ``null``;
an absent fact is the string ``"absent"``.

``parse_canonical`` is the strict inverse: it accepts bytes only if they are
exactly the canonical serialization of the value they decode to.
"""

from __future__ import annotations

import json

ABSENT = "absent"

# Nesting is shallow in every accepted format; the bound keeps a hostile line
# from exhausting the stack of a recursive check.
_MAX_DEPTH = 16


class CanonicalError(ValueError):
    """A value or byte string is not canonical."""


def check_value(value: object, depth: int = 0) -> None:
    """Raise ``CanonicalError`` unless ``value`` uses only the admitted types."""
    if depth > _MAX_DEPTH:
        raise CanonicalError("nesting too deep")
    kind = type(value)
    if kind is str or kind is bool:
        return
    if kind is int:
        return
    if kind is list:
        for item in value:  # type: ignore[attr-defined]
            check_value(item, depth + 1)
        return
    if kind is dict:
        for key, item in value.items():  # type: ignore[attr-defined]
            if type(key) is not str:
                raise CanonicalError("object key is not a string")
            check_value(item, depth + 1)
        return
    raise CanonicalError(f"{kind.__name__} is not an admitted value type")


def canonical_bytes(doc: object) -> bytes:
    check_value(doc)
    text = json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return (text + "\n").encode("ascii")


def _reject_constant(name: str) -> object:
    raise CanonicalError(f"{name} is not admitted")


def _reject_float(text: str) -> object:
    raise CanonicalError("floats are not admitted")


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise CanonicalError("duplicate object key")
        result[key] = value
    return result


def parse_canonical(data: bytes) -> object:
    """Decode one canonical document (including its final LF) or raise."""
    if type(data) is not bytes or not data.endswith(b"\n"):
        raise CanonicalError("missing final LF")
    try:
        text = data[:-1].decode("ascii")
        value = json.loads(
            text,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
            object_pairs_hook=_unique_object,
        )
    except CanonicalError:
        raise
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise CanonicalError(f"not JSON: {type(exc).__name__}") from exc
    if value is None:
        raise CanonicalError("null is not admitted")
    check_value(value)
    if canonical_bytes(value) != data:
        raise CanonicalError("not in canonical form")
    return value
