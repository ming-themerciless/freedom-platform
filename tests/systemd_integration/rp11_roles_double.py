"""Test double for ``infra/rp11-h1/rp11_roles.py`` on the disposable host only.

The real hold role is not implemented, so a holder built from the production
artifact exits at once. Tests that need a running holder install the artifact
with this module instead: ``hold`` waits until PID 1 stops it, ``deact`` and
``backstop`` succeed. The entry point, isolation and imports are unchanged.
"""

import sys
import time


def run(role: str, activation_id: str, artifact_sha256: str, **_provenance) -> int:
    print(f"rp11_h1: test double role={role}", file=sys.stderr)
    if role == "hold":
        while True:
            time.sleep(3600)
    return 0
