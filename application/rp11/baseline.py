"""Baseline comparison (H-BSE.14, CL-6).

The recomputed baseline must serialize to the same ``canonical_bytes`` as the
H-1 record's ``baseline``; the digests are compared, never values a caller or
the environment supplied. On a difference the first differing key path is
reported, as a path of key names and list indexes only: no value is printed.

Keys (the Route 3 profile, this implementation's choice; the accepted text's
``launcher``, ``repository``, ``citations``, ``manager`` and ``po17`` keys
describe the withdrawn static-launcher route or remain open under Q3-9/Q3-11
and are not recomputed here):

``host``, ``operator``, ``packages``, ``files``, ``directories``, ``absent``,
``po18`` and ``unit`` (DI-1 ``LoadState`` and ``TimeoutStartUSec`` of the
capture unit).
"""

from __future__ import annotations

import hashlib

from .canonical import CanonicalError, canonical_bytes

BASELINE_KEYS = frozenset(
    {"host", "operator", "packages", "files", "directories", "absent", "po18", "unit"}
)


def baseline_sha256(baseline: dict) -> str:
    return hashlib.sha256(canonical_bytes(baseline)).hexdigest()


def first_difference(expected: object, observed: object, path: str = "baseline") -> str | None:
    """Key path of the first difference in canonical (sorted-key) order, or ``None``."""
    if type(expected) is not type(observed):
        return path
    if type(expected) is dict:
        for key in sorted(set(expected) | set(observed)):  # type: ignore[arg-type]
            if key not in expected or key not in observed:  # type: ignore[operator]
                return f"{path}.{key}"
            found = first_difference(expected[key], observed[key], f"{path}.{key}")  # type: ignore[index]
            if found:
                return found
        return None
    if type(expected) is list:
        for index, (a, b) in enumerate(zip(expected, observed)):  # type: ignore[arg-type]
            found = first_difference(a, b, f"{path}[{index}]")
            if found:
                return found
        if len(expected) != len(observed):  # type: ignore[arg-type]
            return f"{path}[{min(len(expected), len(observed))}]"  # type: ignore[arg-type]
        return None
    return None if expected == observed else path


def compare(expected_sha256: str, expected: dict, observed: dict | None) -> tuple[bool, str, str]:
    """``(equal, observed_sha256 or "absent", first differing key or "absent")``."""
    if observed is None:
        return False, "absent", "baseline"
    try:
        digest = baseline_sha256(observed)
    except CanonicalError:
        return False, "absent", "baseline"
    if digest == expected_sha256:
        return True, digest, "absent"
    return False, digest, first_difference(expected, observed) or "baseline"
