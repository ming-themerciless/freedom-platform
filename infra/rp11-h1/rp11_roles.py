"""Role behaviour of the RP-11 H-1 artifact: hold, stop-post, backstop, start, stop, consume and attest.

``hold`` runs the holder (``application.rp11.hold``) through its composition
root ``adapters.rp11.hold``; ``stop-post`` runs the shared cleanup engine
(``application.rp11.cleanup``) through ``adapters.rp11.stop_post``; ``backstop``
runs BS-1 … BS-4 over the same engine through ``adapters.rp11.backstop``. No
orchestration lives in this module. ``start`` and ``stop`` consume DI-2 and DI-S;
``consume`` (RT-1) takes no operand and runs ``adapters.rp11.consume``; ``attest`` (RT-5)
runs the cleanup behind its unit-state precondition through ``adapters.rp11.attest`` and
carries no provenance.
"""

import sys

EX_UNAVAILABLE = 69


def run(role: str, activation_id: str, artifact_sha256: str, *operands: int, **provenance) -> int:
    invocation_id = provenance.get("invocation_id", "absent")
    parent_pid = provenance.get("parent_pid", 0)
    if role == "hold":
        from adapters.rp11.hold import run_hold

        return run_hold(activation_id, artifact_sha256, invocation_id=invocation_id, parent_pid=parent_pid)
    if role == "stop-post":
        from adapters.rp11.stop_post import run_stop_post

        return run_stop_post(activation_id, artifact_sha256, invocation_id=invocation_id, parent_pid=parent_pid)
    if role == "backstop":
        from adapters.rp11.backstop import run_backstop

        return run_backstop(activation_id, artifact_sha256, invocation_id=invocation_id, parent_pid=parent_pid)
    if role == "start" and len(operands) == 2:
        from adapters.rp11.start import run_start

        return run_start(activation_id, artifact_sha256, operands[0], operands[1])
    if role == "stop" and not operands:
        from adapters.rp11.stop import run_stop

        return run_stop()
    if role == "consume" and not operands:
        from adapters.rp11.consume import run_consume

        return run_consume(invocation_id=invocation_id)
    if role == "attest" and not operands:
        from adapters.rp11.attest import run_attest

        return run_attest(activation_id, artifact_sha256)
    print(f"rp11_h1: role {role} is not implemented in this build", file=sys.stderr)
    return EX_UNAVAILABLE
