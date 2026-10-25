"""Host-proof entry: the production supervisor with a stand-in member vector and short timings.

Installed by ``executor_host_support`` as a system service (Restart=always, ``User=ubuntu``) for the disposable-host
proofs only. Everything is the production ``adapters.executor.supervisor`` code path; the only
differences are the privileged argv (a root member held in uninterruptible sleep instead of SA-2,
which is never stuck), compressed timings, and an append-only observation log written at the
ownership boundaries (prepared, start-sent, the start call, bound, cleanup, supervisor start).
"""

from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.environ["FB_STANDIN_REPO"])
sys.dont_write_bytecode = True

from adapters.executor import ownership, supervisor, usermanager  # noqa: E402
from adapters.executor.userbus import connect_user_bus  # noqa: E402

LOG = os.environ["FB_STANDIN_LOG"]
SPEC = json.loads(os.environ["FB_STANDIN_SPEC"])
UID = os.getuid()
_observer = usermanager.BusUserManager(lambda: connect_user_bus(UID))


def observe(label: str, unit: str | None = None) -> None:
    entry = {"label": label, "t": time.time(), "pid": os.getpid()}
    try:
        names = [name for name in os.listdir(os.path.join(os.environ["STATE_DIRECTORY"], "invocations"))]
        entry["state_dir"] = sorted(names)
    except OSError as error:
        entry["state_dir"] = f"unreadable:{error.errno}"
    if unit:
        try:
            view = _observer.unit(unit)
            entry["unit"] = None if view is None else {
                "active": view.active_state, "sub": view.sub_state, "invocation_id": view.invocation_id,
                "control_group": view.control_group, "main_pid": view.main_pid}
            if view is not None and view.control_group:
                with open(f"/sys/fs/cgroup{view.control_group}/cgroup.events", encoding="ascii") as handle:
                    entry["cgroup_events"] = handle.read().split()
        except Exception as error:  # noqa: BLE001 - observation must never change behavior
            entry["unit"] = f"error:{type(error).__name__}"
    with open(LOG, "a", encoding="ascii") as handle:
        handle.write(json.dumps(entry) + "\n")


_put = ownership.OwnershipStore.put
_start = usermanager.BusUserManager.start_transient


def put(self, record):
    _put(self, record)
    observe(f"put:{record.state}", record.unit)


def start_transient(self, name, argv, **kwargs):
    observe("start-call:before", name)
    try:
        return _start(self, name, argv, **kwargs)
    finally:
        observe("start-call:after", name)


ownership.OwnershipStore.put = put
usermanager.BusUserManager.start_transient = start_transient
observe("supervisor-start")
raise SystemExit(supervisor.main(
    argv=tuple(SPEC["argv"]), executable=SPEC["executable"], timing=supervisor.Timing(**SPEC["timing"])))
