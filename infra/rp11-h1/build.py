"""Assemble the RP-11 H-1 controlled artifact.

    python3 infra/rp11-h1/build.py --wheel <jeepney wheel> --dest <dir>

Layout of ``<dir>`` (installed as ``/usr/local/libexec/freedom-blades-rp11``):

    rp11_h1.py                     the role entry point
    rp11_entry.py                  the Pass A capture entry (G8 composition staged; same lib/)
    lib/application/...            the application boundary (unit_control only)
    lib/adapters/systemd/...       the Route 3 adapter
    lib/tools/phase_5_0_evidence/...   the capture entry's fixed dependency closure
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

Integrity review (RP-11 G6). The capture-tool digest and the SA-2 tree digest
are both derived from one read of the **built tree**, never from the checkout:

    python3 build.py --review <dir>
    python3 build.py --review <dir> --expect-tree-sha256 <hex> \\
                                    --expect-capture-tool-sha256 <hex>

The first form prints the review inputs (one canonical JSON line) and accepts
nothing. The second is the gate: it exits 0 only if both digests equal the
reviewer's values, which come from outside; none is recorded here. Either form
must run as root, on a root-owned tree whose every ancestor up to ``/`` is a
real root-owned directory not writable by group or others (the install-parent
contract), so nobody else can swap the tree or a directory above it; the path
may not contain ``..``. It refuses a tree without the modes above, or holding a
link, special file, bytecode, empty directory or lacking a capture-tool source.
The build runs the same reading, without the root and ancestor requirement, on
its own staging tree and fails unless that tree is exactly the files and bytes
it wrote.

Standard library only, and it imports nothing from the repository.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
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
    "application/rp11/attest.py",
    "application/rp11/attribution.py",
    "application/rp11/authority.py",
    "application/rp11/backstop.py",
    "application/rp11/baseline.py",
    "application/rp11/canonical.py",
    "application/rp11/cleanup.py",
    "application/rp11/consume.py",
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
    "adapters/rp11/attest.py",
    "adapters/rp11/backstop.py",
    "adapters/rp11/baseline.py",
    "adapters/rp11/consume.py",
    "adapters/rp11/fsops.py",
    "adapters/rp11/hold.py",
    "adapters/rp11/holdfs.py",
    "adapters/rp11/process.py",
    "adapters/rp11/stop_post.py",
    "adapters/rp11/start.py",
    "adapters/rp11/stop.py",
)

# The capture entry (``rp11_entry.py``) loads the RP-11 capture mechanism. These are
# its complete, mechanically computed dependency closure outside ``SOURCES``: every
# repository module ``tools.phase_5_0_evidence.execution.capture_mechanism``
# imports, with its package ``__init__`` files, and nothing third-party. A test
# computes the closure from the entry's imports by AST and keeps this equal to it.
# The roots are ``capture_mechanism`` and ``execution/pass_a.py`` (the policy-neutral
# Pass A orchestrator, which brings in ``start_binding.py``, the G11 InvocationID/consume
# ``run-start`` pairing, and the journal modules it uses). The entry imports ``pass_a``
# but calls nothing in it: the run path stays unavailable (exit 69) until G2-G7 land.
ENTRY_SOURCES = (
    "application/idempotency.py",
    "tools/__init__.py",
    "tools/phase_5_0_evidence/__init__.py",
    "tools/phase_5_0_evidence/capability.py",
    "tools/phase_5_0_evidence/capture.py",
    "tools/phase_5_0_evidence/capture_contract.py",
    "tools/phase_5_0_evidence/durability_model.py",
    "tools/phase_5_0_evidence/errors.py",
    "tools/phase_5_0_evidence/execution/__init__.py",
    "tools/phase_5_0_evidence/execution/boundary.py",
    "tools/phase_5_0_evidence/execution/capture_mechanism.py",
    "tools/phase_5_0_evidence/execution/capture_store.py",
    "tools/phase_5_0_evidence/execution/descriptors.py",
    "tools/phase_5_0_evidence/execution/pass_a.py",
    "tools/phase_5_0_evidence/execution/retention_check.py",
    "tools/phase_5_0_evidence/execution/start_binding.py",
    "tools/phase_5_0_evidence/identity.py",
    "tools/phase_5_0_evidence/records.py",
)

# The ``rp11-capture-tool/1`` construction of ``capture_contract``, restated here
# because this file imports nothing from the repository; a test keeps the schema,
# the source list and the digest equal to ``capture_contract``'s. The paths are
# relative to ``lib/`` in the built tree.
TOOL_DIGEST_SCHEMA = "rp11-capture-tool/1"
RP11_SOURCES = (
    "tools/phase_5_0_evidence/capture_contract.py",
    "tools/phase_5_0_evidence/errors.py",
    "tools/phase_5_0_evidence/execution/boundary.py",
    "tools/phase_5_0_evidence/execution/capture_mechanism.py",
    "tools/phase_5_0_evidence/execution/capture_store.py",
    "tools/phase_5_0_evidence/execution/descriptors.py",
    "tools/phase_5_0_evidence/execution/retention_check.py",
)
REVIEW_SCHEMA = "rp11-sa2-review/1"

_SHA256 = re.compile(r"[0-9a-f]{64}")
_PLAIN_NAME = re.compile(r"[A-Za-z0-9._+@/-]+")
_MAX_TREE_FILE_BYTES = 8 << 20

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


def _write_new(root: Path, name: str, data: bytes, placed: dict[str, str]) -> None:
    """Create ``root/name``; an existing path, including a symlink, is a build error.

    ``placed`` records the digest of the bytes handed to the write."""
    target = root / name
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(target, "xb") as handle:
            handle.write(data)
    except FileExistsError as exc:
        raise BuildError(f"{target} would be written twice") from exc
    placed[name] = hashlib.sha256(data).hexdigest()


def _unpack(data: bytes, root: Path, namespaces: tuple[str, str], placed: dict[str, str]) -> None:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        members = [m for m in archive.infolist() if not m.is_dir()]
        if len(members) > _MAX_MEMBERS:
            raise BuildError("wheel has too many members")
        if sum(m.file_size for m in members) > _MAX_UNPACKED_BYTES:
            raise BuildError("wheel unpacks too large")
        for member in members:
            parts = _member_parts(member, namespaces)
            _write_new(root, "/".join(["lib", *parts]), archive.read(member), placed)


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


def _tree_file_sha256(path: str) -> str:
    """SHA-256 of one artifact file, read once from one open, unchanged file."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_size > _MAX_TREE_FILE_BYTES:
            raise BuildError(f"{path} is not a bounded regular file")
        digest, size = hashlib.sha256(), 0
        while size <= _MAX_TREE_FILE_BYTES:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
        after = os.fstat(fd)
    finally:
        os.close(fd)
    if _identity(before) != _identity(after) or size != after.st_size:
        raise BuildError(f"{path} changed while it was read")
    return digest.hexdigest()


def _tree_digests(tree: Path, owner: int) -> dict[str, str]:
    """``{relative name: sha256}`` of every file in a safe artifact tree."""

    def unreadable(exc: OSError) -> None:
        raise BuildError(f"cannot list {exc.filename}: {exc.strerror}")

    def check(path: str, mode: int, is_kind) -> None:
        info = os.lstat(path)
        if not is_kind(info.st_mode):
            raise BuildError(f"{path} is a link, special file or wrong type")
        if info.st_uid != owner:
            raise BuildError(f"{path}: owner uid {info.st_uid}")
        if stat.S_IMODE(info.st_mode) != mode:
            raise BuildError(f"{path}: mode {stat.S_IMODE(info.st_mode):o}")

    top = os.path.abspath(tree)
    check(top, 0o755, stat.S_ISDIR)
    files: dict[str, str] = {}
    for directory, dirnames, filenames in os.walk(top, onerror=unreadable):
        if not (dirnames or filenames):
            raise BuildError(f"{directory} is an empty directory")
        for name in dirnames:
            if name == "__pycache__":
                raise BuildError(f"{directory} holds bytecode")
            check(os.path.join(directory, name), 0o755, stat.S_ISDIR)
        for name in filenames:
            path = os.path.join(directory, name)
            relative = os.path.relpath(path, top)
            if not _PLAIN_NAME.fullmatch(relative) or name.endswith(".pyc"):
                raise BuildError(f"unexpected file name {relative!r}")
            check(path, 0o644, stat.S_ISREG)
            files[relative] = _tree_file_sha256(path)
    return files


def _read_tree_inputs(tree: Path, owner: int) -> dict:
    """The digests of ``tree``, whose objects must belong to ``owner``.

    Internal: for ``build`` on its own staging tree and for synthetic tests. It
    checks nothing above ``tree``, so it is not a review; use ``review_inputs``.

    Both digests come from the same per-file digests. ``tree_sha256`` is the
    ``ROUTE3_SA2_TREE_SHA256`` recipe (``sha256sum`` listing, bytewise sorted)."""
    try:
        files = _tree_digests(Path(tree), owner)
    except OSError as exc:
        raise BuildError(f"cannot review the tree: {exc}") from exc
    missing = [name for name in RP11_SOURCES if f"lib/{name}" not in files]
    if missing:
        raise BuildError(f"capture-tool sources absent from the tree: {', '.join(missing)}")
    ordered = sorted(files, key=str.encode)
    listing = "".join(f"{files[name]}  ./{name}\n" for name in ordered)
    # capture_contract.canonical_bytes
    document = {
        "schema": TOOL_DIGEST_SCHEMA,
        "sources": [[name, files[f"lib/{name}"]] for name in RP11_SOURCES],
    }
    canonical = json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )
    return {
        "schema": REVIEW_SCHEMA,
        "tree_sha256": hashlib.sha256(listing.encode()).hexdigest(),
        "capture_tool_schema": TOOL_DIGEST_SCHEMA,
        "capture_tool_sha256": hashlib.sha256((canonical + "\n").encode("ascii")).hexdigest(),
        "files": [[name, files[name]] for name in ordered],
    }


def review_inputs(tree: Path) -> dict:
    """The integrity review inputs of a built tree, from that tree's bytes only.

    Fails closed unless the caller is root, the tree is root-owned and every
    directory above it satisfies the install-parent contract."""
    if os.geteuid() != 0:
        raise BuildError("integrity review must run as root")
    if ".." in Path(tree).parts:
        raise BuildError("the reviewed path may not contain '..'")
    # One absolute spelling for both the ancestor check and the reading.
    top = Path(os.path.abspath(tree))
    problem = _install_parent_problem(top.parent)
    if problem:
        raise BuildError(f"unsafe review location: {problem}")
    return _read_tree_inputs(top, 0)


def verify_review(tree: Path, tree_sha256: str, capture_tool_sha256: str) -> dict:
    """The gate: the tree's review inputs, only if both externally supplied digests match."""
    expected = {"tree_sha256": tree_sha256, "capture_tool_sha256": capture_tool_sha256}
    for key, value in expected.items():
        if not isinstance(value, str) or not _SHA256.fullmatch(value):
            raise BuildError(f"expected {key} must be 64 lowercase hex digits")
    inputs = review_inputs(tree)
    for key, value in expected.items():
        if inputs[key] != value:
            raise BuildError(f"{key} is {inputs[key]}, expected {value}")
    return inputs


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
        (staging / "lib").mkdir()
        placed: dict[str, str] = {}
        _unpack(data, staging, _wheel_namespaces(wheel.name), placed)
        for source in (*SOURCES, *ENTRY_SOURCES):
            _write_new(staging, f"lib/{source}", (ROOT / source).read_bytes(), placed)
        _write_new(staging, "lib/rp11_roles.py", (roles or HERE / "rp11_roles.py").read_bytes(), placed)
        _write_new(staging, "rp11_h1.py", (HERE / "rp11_h1.py").read_bytes(), placed)
        _write_new(staging, "rp11_entry.py", (HERE / "rp11_entry.py").read_bytes(), placed)
        for directory, _dirnames, filenames in os.walk(staging):
            os.chmod(directory, 0o755)
            for name in filenames:
                os.chmod(os.path.join(directory, name), 0o644)
        problem = _unsafe_tree(staging, os.geteuid())
        if problem:
            raise BuildError(f"built tree is unsafe: {problem}")
        if dict(_read_tree_inputs(staging, os.geteuid())["files"]) != placed:
            raise BuildError("built tree is not the bytes the build placed")
        os.rename(staging, dest)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--wheel", type=Path)
    parser.add_argument("--dest", type=Path)
    parser.add_argument("--roles", type=Path, help="replace lib/rp11_roles.py (tests only)")
    parser.add_argument("--review", type=Path, help="review a built tree; builds nothing")
    parser.add_argument("--expect-tree-sha256")
    parser.add_argument("--expect-capture-tool-sha256")
    args = parser.parse_args(argv)
    expected = (args.expect_tree_sha256, args.expect_capture_tool_sha256)
    if args.review is not None:
        if any(value is not None for value in (args.wheel, args.dest, args.roles)):
            parser.error("--review takes no build option")
        if (expected[0] is None) != (expected[1] is None):
            parser.error("give both expected digests or neither")
    elif args.wheel is None or args.dest is None:
        parser.error("--wheel and --dest are required to build")
    elif expected != (None, None):
        parser.error("expected digests apply only to --review")
    try:
        if args.review is None:
            print(build(args.wheel, args.dest, args.roles))
        else:
            if expected[0] is None:
                inputs = review_inputs(args.review)
            else:
                inputs = verify_review(args.review, *expected)
            print(json.dumps(inputs, sort_keys=True, separators=(",", ":")))
    except (BuildError, OSError) as exc:
        print(f"build.py: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
