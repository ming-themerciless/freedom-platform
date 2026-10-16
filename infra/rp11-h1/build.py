"""Assemble the RP-11 H-1 controlled artifact.

    python3 infra/rp11-h1/build.py --wheel <jeepney wheel> --dest <dir>

Layout of ``<dir>`` (installed as ``/usr/local/libexec/freedom-blades-rp11``):

    rp11_h1.py                     the role entry point
    lib/application/...            the application boundary (unit_control only)
    lib/adapters/systemd/...       the Route 3 adapter
    lib/rp11_roles.py              role behaviour (``--roles`` replaces it)
    lib/jeepney/, lib/jeepney-<v>.dist-info/   the D-Bus client, licence included

The wheel must be exactly the one ``requirements.lock`` pins, by name and
SHA-256; anything else is refused before ``<dir>`` exists. It is opened once,
without following a symlink, and read into memory; that one copy is hashed and
is the only thing unpacked, so a wheel path replaced or rewritten during the
build cannot supply unverified bytes, and a change seen while it is held fails
the build. The wheel is pure Python (``py3-none-any``), so installing it is
unpacking it, and only its two namespaces — the ``jeepney`` package and its
``.dist-info`` — are accepted; every file is created exclusively, so nothing in
the wheel can replace a trusted artifact source.

Install contract: run as root. The directories above ``<dir>`` must already be
root-owned and not writable by group or others, and ``<dir>`` must not exist.
The artifact is built beside it, checked (every object owned by the builder, no
symlinks, directories 0755, files 0644) and renamed into place, so a failed
build leaves nothing at ``<dir>``. The adapter and the entry point check this
state again before the entry point runs as root.

Standard library only, and it imports nothing from the repository.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import os
import re
import shutil
import stat
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LOCK = HERE / "requirements.lock"

# Exactly what the adapter and the roles need at runtime; a test keeps this equal
# to the adapter and role packages so a new module cannot be left out silently.
SOURCES = (
    "application/__init__.py",
    "application/unit_control.py",
    "adapters/__init__.py",
    "adapters/systemd/__init__.py",
    "adapters/systemd/artifact.py",
    "adapters/systemd/bus.py",
    "adapters/systemd/jeepney_bus.py",
    "adapters/systemd/manager.py",
    "adapters/systemd/polkit.py",
    "adapters/systemd/subject.py",
    "application/rp11/__init__.py",
    "application/rp11/attribution.py",
    "application/rp11/authority.py",
    "application/rp11/backstop.py",
    "application/rp11/baseline.py",
    "application/rp11/canonical.py",
    "application/rp11/cleanup.py",
    "application/rp11/evidence.py",
    "application/rp11/hl.py",
    "application/rp11/hold.py",
    "application/rp11/journal.py",
    "application/rp11/paths.py",
    "application/rp11/pk.py",
    "application/rp11/ports.py",
    "application/rp11/records.py",
    "application/rp11/sn.py",
    "application/rp11/start.py",
    "application/rp11/stop.py",
    "adapters/rp11/__init__.py",
    "adapters/rp11/backstop.py",
    "adapters/rp11/baseline.py",
    "adapters/rp11/fsops.py",
    "adapters/rp11/hold.py",
    "adapters/rp11/holdfs.py",
    "adapters/rp11/process.py",
    "adapters/rp11/stop_post.py",
    "adapters/rp11/start.py",
    "adapters/rp11/stop.py",
)

_PIN = re.compile(r"([A-Za-z0-9_.-]+)==([A-Za-z0-9_.]+) \\ --hash=sha256:([0-9a-f]{64})")
_MEMBER_PART = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*")

# Bounds well above the pinned wheel (49 KB, 34 members, ~200 KB unpacked).
_MAX_WHEEL_BYTES = 1 << 20
_MAX_MEMBERS = 256
_MAX_UNPACKED_BYTES = 8 << 20


class BuildError(Exception):
    pass


def pinned_wheel() -> tuple[str, str]:
    """``(wheel filename, sha256)`` from the lock; exactly one pin is expected."""
    text = "\n".join(
        line for line in LOCK.read_text().splitlines() if not line.lstrip().startswith("#")
    )
    pin = _PIN.fullmatch(" ".join(text.split()))
    if pin is None:
        raise BuildError("requirements.lock must pin exactly one hashed wheel")
    name, version, digest = pin.groups()
    return f"{name}-{version}-py3-none-any.whl", digest


def _wheel_namespaces(filename: str) -> tuple[str, str]:
    """The package and ``.dist-info`` directory a pinned ``name-version-…`` wheel may hold."""
    name, version = filename.split("-")[:2]
    return name, f"{name}-{version}.dist-info"


def _read_fd(fd: int) -> bytes:
    """Read ``fd`` to EOF, never more than ``_MAX_WHEEL_BYTES`` + 1 bytes."""
    chunks = []
    remaining = _MAX_WHEEL_BYTES + 1
    while remaining > 0:
        chunk = os.read(fd, min(remaining, 65536))
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _identity(info: os.stat_result) -> tuple[int, ...]:
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def read_verified_wheel(wheel: Path) -> bytes:
    """The pinned wheel's bytes, read once from one open file and hash-checked."""
    filename, digest = pinned_wheel()
    if wheel.name != filename:
        raise BuildError(f"wheel must be {filename}, got {wheel.name}")
    try:
        fd = os.open(wheel, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    except OSError as exc:
        raise BuildError(f"cannot open the wheel without following a link: {exc}") from exc
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise BuildError("wheel is not a regular file")
        if before.st_size > _MAX_WHEEL_BYTES:
            raise BuildError("wheel is too large")
        data = _read_fd(fd)
        after = os.fstat(fd)
    finally:
        os.close(fd)
    if _identity(before) != _identity(after) or len(data) != after.st_size:
        raise BuildError("wheel changed while it was read")
    actual = hashlib.sha256(data).hexdigest()
    if actual != digest:
        raise BuildError(f"wheel SHA-256 {actual} does not match the lock")
    return data


def _member_parts(member: zipfile.ZipInfo, namespaces: tuple[str, str]) -> list[str]:
    name = member.filename
    parts = name.split("/")
    if (
        len(parts) < 2
        or parts[0] not in namespaces
        or not all(_MEMBER_PART.fullmatch(part) for part in parts)
    ):
        raise BuildError(f"unexpected wheel member {name!r}")
    kind = stat.S_IFMT(member.external_attr >> 16)
    if kind not in (0, stat.S_IFREG):
        raise BuildError(f"wheel member {name!r} is not a regular file")
    return parts


def _write_new(target: Path, data: bytes) -> None:
    """Create ``target``; an existing path, including a symlink, is a build error."""
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(target, "xb") as handle:
            handle.write(data)
    except FileExistsError as exc:
        raise BuildError(f"{target} would be written twice") from exc


def _unpack(data: bytes, lib: Path, namespaces: tuple[str, str]) -> None:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        members = [m for m in archive.infolist() if not m.is_dir()]
        if len(members) > _MAX_MEMBERS:
            raise BuildError("wheel has too many members")
        if sum(m.file_size for m in members) > _MAX_UNPACKED_BYTES:
            raise BuildError("wheel unpacks too large")
        for member in members:
            parts = _member_parts(member, namespaces)
            _write_new(lib.joinpath(*parts), archive.read(member))


def _unsafe_tree(top: Path, owner: int) -> str | None:
    for directory, dirnames, filenames in os.walk(top):
        for name in [".", *dirnames, *filenames]:
            path = os.path.join(directory, name) if name != "." else directory
            info = os.lstat(path)
            is_dir = stat.S_ISDIR(info.st_mode)
            if not (is_dir or stat.S_ISREG(info.st_mode)):
                return f"{path} is not a regular file or directory"
            if info.st_uid != owner:
                return f"{path}: owner uid {info.st_uid}"
            if stat.S_IMODE(info.st_mode) != (0o755 if is_dir else 0o644):
                return f"{path}: mode {stat.S_IMODE(info.st_mode):o}"
    return None


def _install_parent_problem(parent: Path) -> str | None:
    """Why a root install under ``parent`` could be replaced by someone else."""
    current = parent
    while True:
        try:
            info = os.lstat(current)
        except OSError as exc:
            return f"{current}: {exc.strerror}"
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            return f"{current} is not a real directory"
        if info.st_uid != 0 or info.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            return f"{current} is not root-owned and protected"
        if current.parent == current:
            return None
        current = current.parent


def build(wheel: Path, dest: Path, roles: Path | None = None) -> Path:
    data = read_verified_wheel(wheel)
    dest = Path(os.path.abspath(dest))
    if os.path.lexists(dest):
        raise BuildError(f"{dest} already exists")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if os.geteuid() == 0:
        problem = _install_parent_problem(dest.parent)
        if problem:
            raise BuildError(f"unsafe install location: {problem}")
    staging = Path(tempfile.mkdtemp(prefix=f".{dest.name}.", dir=dest.parent))
    try:
        lib = staging / "lib"
        lib.mkdir()
        _unpack(data, lib, _wheel_namespaces(wheel.name))
        for source in SOURCES:
            _write_new(lib / source, (ROOT / source).read_bytes())
        _write_new(lib / "rp11_roles.py", (roles or HERE / "rp11_roles.py").read_bytes())
        _write_new(staging / "rp11_h1.py", (HERE / "rp11_h1.py").read_bytes())
        for directory, _dirnames, filenames in os.walk(staging):
            os.chmod(directory, 0o755)
            for name in filenames:
                os.chmod(os.path.join(directory, name), 0o644)
        problem = _unsafe_tree(staging, os.geteuid())
        if problem:
            raise BuildError(f"built tree is unsafe: {problem}")
        os.rename(staging, dest)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--dest", type=Path, required=True)
    parser.add_argument("--roles", type=Path, help="replace lib/rp11_roles.py (tests only)")
    args = parser.parse_args(argv)
    try:
        print(build(args.wheel, args.dest, args.roles))
    except (BuildError, OSError) as exc:
        print(f"build.py: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
