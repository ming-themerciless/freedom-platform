"""In-process baseline recomputation (H-BSE, CL-6), with no child process.

Each key is read directly: ``uname(2)``, ``/etc/machine-id``, ``/etc/passwd``
and ``/etc/group`` (not NSS, which may load modules or talk to services), the
dpkg status database, ``lstat``/descriptor reads of the installed artifact and
interpreter, and DI-1 for the capture unit. The key set is the Route 3 profile
of ``application.rp11.baseline``. Any unreadable fact makes ``recompute``
return ``None``, which can never compare equal.

The same function produces the H-1 record's baseline (the installer class is
outside this slice; the disposable-host tests use it to write synthetic H-1
records), so recording and recomputation cannot drift apart.
"""

from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass

from application.unit_control import (
    CAPTURE_UNIT,
    ControlOk,
    UnitControl,
    UnitProperty,
)

PACKAGES = (
    "dbus",
    "libc6",
    "libpolkit-gobject-1-0",
    "libsystemd0",
    "polkitd",
    "python3.14",
    "python3.14-minimal",
    "systemd",
    "systemd-sysv",
)
_MAX_SMALL = 1 << 20
_MAX_DPKG_STATUS = 32 << 20
_MAX_HASHED = 64 << 20
_FORBIDDEN = ("security.capability", "system.posix_acl_access", "system.posix_acl_default")


class BaselineUnavailable(Exception):
    pass


@dataclass(frozen=True)
class BaselinePaths:
    machine_id: str = "/etc/machine-id"
    passwd: str = "/etc/passwd"
    group: str = "/etc/group"
    dpkg_status: str = "/var/lib/dpkg/status"
    interpreter: str = "/usr/bin/python3.14"
    artifact: str = "/usr/local/libexec/freedom-blades-rp11"
    store: str = "/var/lib/freedom-blades-rp11"
    absent: tuple[str, ...] = (
        "/etc/freedom-blades-rp11",
        "/etc/polkit-1/rules.d/50-freedom-blades-rp11.rules",
        "/usr/local/share/polkit-1/rules.d/50-freedom-blades-rp11.rules",
        "/usr/share/polkit-1/rules.d/50-freedom-blades-rp11.rules",
    )


def _read(path: str, cap: int) -> bytes:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > cap:
            raise BaselineUnavailable(f"{path} is not a bounded regular file")
        data = b""
        while len(data) <= info.st_size:
            chunk = os.read(fd, min(1 << 20, info.st_size + 1 - len(data)))
            if not chunk:
                break
            data += chunk
        if len(data) != info.st_size:
            raise BaselineUnavailable(f"{path} changed while read")
        return data
    finally:
        os.close(fd)


def _lines(path: str) -> list[list[str]]:
    text = _read(path, _MAX_SMALL).decode("utf-8")
    return [line.split(":") for line in text.splitlines() if line and not line.startswith("#")]


def operator_facts(user: str, passwd: str, group: str) -> dict:
    entries = [e for e in _lines(passwd) if len(e) >= 7 and e[0] == user]
    if len(entries) != 1:
        raise BaselineUnavailable("operator account not exactly once in passwd")
    uid, gid = int(entries[0][2]), int(entries[0][3])
    groups: dict[int, str] = {}
    for entry in _lines(group):
        if len(entry) < 4 or not entry[2].isdigit():
            continue
        members = [m for m in entry[3].split(",") if m]
        number = int(entry[2])
        if number == gid or user in members:
            if number in groups and groups[number] != entry[0]:
                raise BaselineUnavailable("duplicate group id")
            groups[number] = entry[0]
    if gid not in groups:
        raise BaselineUnavailable("primary group missing")
    return {
        "user": user,
        "uid": uid,
        "gid": gid,
        "groups": [[name, number] for number, name in sorted(groups.items())],
    }


def package_facts(status_path: str, names: tuple[str, ...] = PACKAGES) -> list[list[str]]:
    """``[package, version, architecture]`` for each fixed name; ``absent`` if not installed."""
    found: dict[str, list[str]] = {}
    text = _read(status_path, _MAX_DPKG_STATUS).decode("utf-8", "strict")
    for stanza in text.split("\n\n"):
        fields: dict[str, str] = {}
        for line in stanza.splitlines():
            if line[:1] in (" ", "\t") or ":" not in line:
                continue
            key, _, value = line.partition(":")
            fields[key] = value.strip()
        name = fields.get("Package")
        if name in names and fields.get("Status", "").endswith(" installed"):
            if name in found:
                raise BaselineUnavailable(f"{name} installed more than once")
            found[name] = [name, fields.get("Version", "absent"), fields.get("Architecture", "absent")]
    return [found.get(name, [name, "absent", "absent"]) for name in sorted(names)]


def _xattr_flags(path: str) -> tuple[bool, bool]:
    try:
        names = os.listxattr(path, follow_symlinks=False)
    except OSError:
        names = list(_FORBIDDEN)  # unknowable: never compares equal to a clean record
    return ("security.capability" in names, any(n.startswith("system.posix_acl") for n in names))


def file_facts(role: str, path: str) -> dict:
    info = os.lstat(path)
    if not stat.S_ISREG(info.st_mode):
        raise BaselineUnavailable(f"{path} is not a regular file")
    capability, acl = _xattr_flags(path)
    return {
        "role": role,
        "path": path,
        "sha256": hashlib.sha256(_read(path, _MAX_HASHED)).hexdigest(),
        "size": info.st_size,
        "owner": info.st_uid,
        "group": info.st_gid,
        "mode": stat.S_IMODE(info.st_mode),
        "dev": info.st_dev,
        "ino": info.st_ino,
        "setid": bool(info.st_mode & (stat.S_ISUID | stat.S_ISGID)),
        "file_capability": capability,
        "posix_acl": acl,
    }


def directory_facts(path: str) -> dict:
    info = os.lstat(path)
    if not stat.S_ISDIR(info.st_mode):
        raise BaselineUnavailable(f"{path} is not a directory")
    _capability, acl = _xattr_flags(path)
    return {
        "path": path,
        "owner": info.st_uid,
        "group": info.st_gid,
        "mode": stat.S_IMODE(info.st_mode),
        "posix_acl": acl,
        "dev": info.st_dev,
        "ino": info.st_ino,
    }


def tree_digest(top: str, limit: int = 1_000) -> str:
    """SHA-256 over the sorted inventory ``rel kind uid gid mode size sha256`` of a tree,
    walked without following any link."""
    rows = []
    for directory, dirnames, filenames in os.walk(top, followlinks=False):
        dirnames.sort()
        for name in sorted(dirnames + filenames):
            path = os.path.join(directory, name)
            info = os.lstat(path)
            rel = os.path.relpath(path, top)
            if stat.S_ISREG(info.st_mode):
                digest = hashlib.sha256(_read(path, _MAX_HASHED)).hexdigest()
                kind = "file"
            elif stat.S_ISDIR(info.st_mode):
                digest, kind = "absent", "dir"
            else:
                digest, kind = "absent", "other"
            rows.append(
                f"{rel}\0{kind}\0{info.st_uid}\0{info.st_gid}\0"
                f"{stat.S_IMODE(info.st_mode):o}\0{info.st_size}\0{digest}\n"
            )
            if len(rows) > limit:
                raise BaselineUnavailable("tree too large")
    return hashlib.sha256("".join(sorted(rows)).encode()).hexdigest()


def _parents(path: str) -> list[str]:
    parts = path.rstrip("/").split("/")[1:]
    return ["/"] + ["/" + "/".join(parts[: i + 1]) for i in range(len(parts))]


def _release_at_least(release: str, minimum: tuple[int, int]) -> bool:
    numbers = []
    for part in release.split("-")[0].split(".")[:2]:
        if not part.isdigit():
            return False
        numbers.append(int(part))
    return tuple(numbers) >= minimum


class HostBaseline:
    """``BaselineSource`` over the local host."""

    def __init__(
        self,
        units: UnitControl,
        *,
        operator_user: str = "ubuntu",
        paths: BaselinePaths | None = None,
    ) -> None:
        self._units = units
        self._user = operator_user
        self._paths = paths or BaselinePaths()

    def recompute(self) -> dict | None:
        try:
            return self._compute()
        except (BaselineUnavailable, OSError, ValueError, UnicodeDecodeError):
            return None

    def _compute(self) -> dict:
        p = self._paths
        uname = os.uname()
        entry = f"{p.artifact}/rp11_h1.py"
        directories = sorted(
            set(_parents(p.artifact))
            | {p.store, f"{p.store}/a2", f"{p.store}/h1", f"{p.store}/activation"}
        )
        return {
            "host": {
                "nodename": uname.nodename,
                "machine_id_sha256": hashlib.sha256(_read(p.machine_id, 4_096)).hexdigest(),
                "architecture": uname.machine,
                "kernel_release": uname.release,
            },
            "operator": operator_facts(self._user, p.passwd, p.group),
            "packages": package_facts(p.dpkg_status),
            "files": [
                file_facts("interpreter", p.interpreter),
                file_facts("entry", entry),
                {"role": "artifact-tree", "path": p.artifact, "sha256": tree_digest(p.artifact)},
            ],
            "directories": [directory_facts(d) for d in directories],
            "absent": [[path, "present" if os.path.lexists(path) else "absent"] for path in p.absent],
            "po18": {
                "machine": uname.machine,
                "release": uname.release,
                "release_at_least_5_9": _release_at_least(uname.release, (5, 9)),
            },
            "unit": self._unit(),
        }

    def _unit(self) -> dict:
        read = self._units.read_unit(
            CAPTURE_UNIT, (UnitProperty.LOAD_STATE, UnitProperty.TIMEOUT_START_USEC)
        )
        if not isinstance(read, ControlOk):
            raise BaselineUnavailable("capture unit unreadable")
        return {
            "load_state": read.value[UnitProperty.LOAD_STATE],
            "timeout_start_usec": read.value[UnitProperty.TIMEOUT_START_USEC],
        }
