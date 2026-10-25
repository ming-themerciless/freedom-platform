"""The one privileged vector the executor may run, and the fixed environment it gets (SA-2 ``stop``)."""

from __future__ import annotations

from adapters.systemd.manager import ROLE_ARTIFACT, ROLE_INTERPRETER

SUDO = "/usr/bin/sudo"
#: The exact privileged boundary; no operand, no environment-derived part.
STOP_ARGV = ("sudo", "-n", ROLE_INTERPRETER, "-I", "-S", ROLE_ARTIFACT, "stop")
CHILD_ENV = {"PATH": "/usr/bin:/bin"}
