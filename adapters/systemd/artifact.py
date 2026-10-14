"""Pre-execution invariant for the controlled role runtime.

PID 1 runs ``ROLE_INTERPRETER -I -S ROLE_ARTIFACT …`` as root. The entry point
checks the rest of the artifact before importing anything from it, but it cannot
vouch for itself: if it had been modified, its check would be the attacker's.
So before asking PID 1 to run it, the adapter checks — in its own process — that
the interpreter and the entry point could have been changed only by root:

* every component from ``/`` down is reached without a symlink;
* every directory and the final regular file is owned by uid 0; and
* none of them is writable by group or others.

Once that holds, only root can break it, so a check when a unit is created also
covers a backstop that fires later. The artifact install contract
(``infra/rp11-h1/build.py``, run as root) is what establishes it.
"""

from __future__ import annotations

import os
import stat
from collections.abc import Callable

_WRITABLE_BY_OTHERS = stat.S_IWGRP | stat.S_IWOTH


def unsafe_root_path(
    path: str, *, lstat: Callable[[str], os.stat_result] = os.lstat
) -> str | None:
    """Why ``path`` is not a root-only regular file, or ``None`` if it is."""
    if (
        not isinstance(path, str)
        or not path.startswith("/")
        or "//" in path
        or os.path.normpath(path) != path
        or path == "/"
    ):
        return f"{path!r} is not a canonical absolute file path"
    parts = path.split("/")[1:]
    directories = ["/"] + ["/" + "/".join(parts[:i]) for i in range(1, len(parts))]
    for directory in directories:
        problem = _unsafe_object(directory, lstat, directory=True)
        if problem:
            return problem
    return _unsafe_object(path, lstat, directory=False)


def _unsafe_object(
    path: str, lstat: Callable[[str], os.stat_result], *, directory: bool
) -> str | None:
    try:
        info = lstat(path)
    except OSError as exc:
        return f"{path}: {exc.strerror or exc}"
    if stat.S_ISLNK(info.st_mode):
        return f"{path} is a symlink"
    if directory and not stat.S_ISDIR(info.st_mode):
        return f"{path} is not a directory"
    if not directory and not stat.S_ISREG(info.st_mode):
        return f"{path} is not a regular file"
    if info.st_uid != 0:
        return f"{path}: owner uid {info.st_uid}, not root"
    if info.st_mode & _WRITABLE_BY_OTHERS:
        return f"{path} is group or other writable"
    return None
