"""The executor <-> supervisor wire contract: one request line, one result line.

``stop 1`` is accepted only from the supervisor's own (dedicated executor) uid; ``drain 1`` only from the
maintenance peer, root. A drain connection is held open after its answer so that the maintainer can tell
a lost supervisor (EOF) from a drained one.
"""

from __future__ import annotations

import socket
import struct

#: Sent by the supervisor on accept, only when it is ready. A client sends nothing until it has read exactly this.
GREETING = b"freedom-executor-supervisor 1\n"
PROTOCOL_REQUEST = b"stop 1\n"
DRAIN_REQUEST = b"drain 1\n"
DRAIN_EMPTY = b"drain empty\n"  # admission is closed for good and nothing is owned, recorded or running
DRAIN_PENDING = b"drain pending\n"  # admission is closed, but an invocation, record or unit exists (or cannot be excluded)
MAX_REQUEST_BYTES = 16
SOCKET_NAME = "supervisor.sock"
#: The persistent supervisor is a root-controlled *system* service running as the dedicated account; its runtime and
#: state directories are the system manager's ``RuntimeDirectory=`` / ``StateDirectory=`` of that one unit.
DIRECTORY_NAME = "freedom-blades-executor"
RUNTIME_ROOT = f"/run/{DIRECTORY_NAME}"
STATE_ROOT = f"/var/lib/{DIRECTORY_NAME}"
SOCKET_PATH = f"{RUNTIME_ROOT}/{SOCKET_NAME}"


def peer_uid(conn: socket.socket) -> int:
    creds = conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
    return struct.unpack("3i", creds)[1]
