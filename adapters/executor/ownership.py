"""Durable ownership record of the executor's privileged invocation (OS-6, fourth remediation).

Admission permits one invocation at a time, so its record lives in one fixed, directly addressable
slot, ``active.json``, in a private state directory. The nonce, boot identity, deterministic unit
name and bound containment identity are inside the record. The record exists *before* anything is
launched and is removed only when the invocation is affirmatively settled, so "no record" is the one
state in which nothing can be running. Because the slot is opened by name, no amount of other
directory content can hide or delay it:

``prepared``   the unit name is reserved; nothing has been sent to the manager;
``start-sent`` written durably *before* ``StartTransientUnit`` is sent; the call may or may not
               have reached the manager, so the deterministic unit name must be resolved, never
               the call repeated;
``bound``      the manager acknowledged the unit; its ``InvocationID`` and cgroup identity are
               recorded, so cleanup can only ever name that cgroup;
``cleanup``    the supervisor has begun ending the boundary (stop / ``cgroup.kill``).

Any record, any other entry (it is named, never read) and any inability to read the directory
means *blocked*; the active slot is still read and driven on every pass. Every trust boundary is descriptor-based and no-follow, and checks owner, mode,
type, link count and size. Writes are checked (a short write is retried, a zero-byte write is an
error) and each transition is synchronized: file ``fsync``, ``rename``, directory ``fsync``.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import stat
from dataclasses import dataclass, replace

from adapters.rp11.fsops import close_quietly

PREPARED, START_SENT, BOUND, CLEANUP = "prepared", "start-sent", "bound", "cleanup"
STATES = (PREPARED, START_SENT, BOUND, CLEANUP)
UNIT_PREFIX = "freedom-executor-stop-"
MAX_RECORD_BYTES = 4096
MAX_ENTRIES = 4096  # a directory with more entries is damaged: it blocks, and a pass stays bounded (names only)
ACTIVE_NAME = "active.json"
STALE_TEMP_SECONDS = 60.0  # a temporary older than this is a crash leftover, not a write in progress


_TEMP_NAME = re.compile(r"\.tmp-[0-9a-f]{16}")
_NONCE = re.compile(r"[0-9a-f]{32}")
_INVOCATION = re.compile(r"[0-9a-f]{32}")
_BOOT = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_CGROUP_PART = re.compile(r"[A-Za-z0-9_.@:-]{1,255}")
_KEYS = {"v", "nonce", "boot", "unit", "state", "invocation_id", "cgroup", "cgroup_id"}


class StoreError(Exception):
    """The state directory or a record cannot be trusted or written. Always read as *blocked*."""


def unit_name(nonce: str) -> str:
    return f"{UNIT_PREFIX}{nonce[:16]}.service"


@dataclass(frozen=True)
class Record:
    nonce: str
    boot: str
    state: str = PREPARED
    invocation_id: str = ""
    cgroup: str = ""  # the manager's ``ControlGroup`` (relative to the cgroup root); "" = no cgroup existed
    cgroup_id: int = 0  # the cgroup directory's inode (the kernel's cgroup id) when ``cgroup`` is set

    @property
    def unit(self) -> str:
        return unit_name(self.nonce)

    @property
    def filename(self) -> str:
        return ACTIVE_NAME

    @staticmethod
    def fresh(boot: str) -> Record:
        return Record(secrets.token_hex(16), boot)

    def to(self, state: str, **changes) -> Record:
        return replace(self, state=state, **changes)

    def encode(self) -> bytes:
        return json.dumps(
            {"v": 1, "nonce": self.nonce, "boot": self.boot, "unit": self.unit, "state": self.state,
             "invocation_id": self.invocation_id, "cgroup": self.cgroup, "cgroup_id": self.cgroup_id},
            sort_keys=True,
        ).encode("ascii")


def _valid_cgroup(path: str, unit: str) -> bool:
    if path == "":
        return True
    parts = path.split("/")
    return (
        path.startswith("/user.slice/")
        and parts[0] == ""
        and len(parts) <= 12
        and parts[-1] == unit
        and all(_CGROUP_PART.fullmatch(part) and part not in (".", "..") for part in parts[1:])
    )


def decode(name: str, data: bytes) -> Record | None:
    """The record, or ``None`` when anything about it is not exactly the format written by ``encode``."""
    if name != ACTIVE_NAME or len(data) > MAX_RECORD_BYTES:
        return None
    try:
        value = json.loads(data.decode("ascii"))
    except (UnicodeDecodeError, ValueError):
        return None
    if type(value) is not dict or set(value) != _KEYS or type(value["v"]) is not int or value["v"] != 1:
        return None
    nonce, boot, state = value["nonce"], value["boot"], value["state"]
    invocation, cgroup, cgroup_id = value["invocation_id"], value["cgroup"], value["cgroup_id"]
    if any(type(item) is not str for item in (nonce, boot, state, invocation, cgroup, value["unit"])):
        return None
    if type(cgroup_id) is not int or cgroup_id < 0:
        return None
    if _NONCE.fullmatch(nonce) is None or _BOOT.fullmatch(boot) is None:
        return None
    if value["unit"] != unit_name(nonce) or state not in STATES:
        return None
    if not _valid_cgroup(cgroup, value["unit"]) or (cgroup == "") != (cgroup_id == 0):
        return None
    if state in (PREPARED, START_SENT):
        if invocation or cgroup or cgroup_id:
            return None
    elif _INVOCATION.fullmatch(invocation) is None:
        return None
    return Record(nonce, boot, state, invocation, cgroup, cgroup_id)


class FileOps:
    """The writes whose failure must be survivable; a seam for failure injection."""

    def create(self, name: str, dir_fd: int) -> int:
        return os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600, dir_fd=dir_fd)

    def write(self, fd: int, data: bytes) -> int:
        return os.write(fd, data)

    def fsync(self, fd: int) -> None:
        os.fsync(fd)

    def rename(self, source: str, target: str, dir_fd: int) -> None:
        os.rename(source, target, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)

    def unlink(self, name: str, dir_fd: int) -> None:
        os.unlink(name, dir_fd=dir_fd)


@dataclass(frozen=True)
class Listing:
    records: tuple[Record, ...]  # the active slot: at most one
    damaged: tuple[str, ...]  # an unreadable slot and every other entry (they block, they are never cleared)
    stray_temporaries: tuple[str, ...]

    @property
    def blocking(self) -> bool:
        return bool(self.records or self.damaged)


_DAMAGED = object()


class OwnershipStore:
    def __init__(self, directory: str, *, uid: int | None = None, ops: FileOps | None = None) -> None:
        self._dir = directory
        self._uid = os.getuid() if uid is None else uid
        self._ops = ops or FileOps()

    @property
    def directory(self) -> str:
        return self._dir

    def _open_dir(self) -> int:
        try:
            fd = os.open(self._dir, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        except OSError as error:
            raise StoreError("state-directory") from error
        try:
            info = os.fstat(fd)
            if not stat.S_ISDIR(info.st_mode) or info.st_uid != self._uid or stat.S_IMODE(info.st_mode) != 0o700:
                raise StoreError("state-directory-untrusted")
        except BaseException:
            close_quietly(fd)
            raise
        return fd

    def create_directory(self) -> None:
        """Create the leaf (mode 0700) if absent; the parent must exist. Idempotent."""
        try:
            os.mkdir(self._dir, 0o700)
        except FileExistsError:
            pass
        except OSError as error:
            raise StoreError("state-directory") from error

    def check_writable(self) -> None:
        """A real write, sync and removal: proves the directory takes a record before a launch needs one."""
        dfd = self._open_dir()
        name = f".tmp-{secrets.token_hex(8)}"
        try:
            try:
                self._write_file(dfd, name, b"probe")
            finally:
                self._unlink_quietly(dfd, name)
            self._ops.fsync(dfd)
        except OSError as error:
            raise StoreError("state-write") from error
        finally:
            close_quietly(dfd)

    def listing(self) -> Listing:
        """The active slot, read directly by name, plus a bounded scan that only *names* everything else."""
        dfd = self._open_dir()
        try:
            record, damaged, temporaries = self._read_active(dfd), [], []
            if record is _DAMAGED:
                damaged.append(ACTIVE_NAME)
            try:
                with os.scandir(dfd) as entries:
                    names = [entry.name for _, entry in zip(range(MAX_ENTRIES + 1), entries)]
            except OSError as error:
                raise StoreError("state-listing") from error
            for name in names[:MAX_ENTRIES]:
                if name == ACTIVE_NAME:
                    continue  # the slot was read by name above and is never judged by its position in a scan
                if _TEMP_NAME.fullmatch(name):
                    temporaries.append(name)
                else:
                    damaged.append(name)  # named, never opened: junk costs a name, not a read
            if len(names) > MAX_ENTRIES:
                damaged.append("<overflow>")
            found = () if record is None or record is _DAMAGED else (record,)
            return Listing(found, tuple(damaged), tuple(temporaries))
        finally:
            close_quietly(dfd)

    def _read_active(self, dfd: int):
        """The record; ``None`` when the slot does not exist; ``_DAMAGED`` for anything else that is there."""
        try:
            fd = os.open(ACTIVE_NAME, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=dfd)
        except FileNotFoundError:
            return None
        except OSError:
            return _DAMAGED
        try:
            info = os.fstat(fd)
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_uid != self._uid
                or stat.S_IMODE(info.st_mode) != 0o600
                or info.st_nlink != 1
                or info.st_size > MAX_RECORD_BYTES
            ):
                return _DAMAGED
            data = os.read(fd, MAX_RECORD_BYTES + 1)
            if len(data) != info.st_size:
                return _DAMAGED
        except OSError:
            return _DAMAGED
        finally:
            close_quietly(fd)
        return decode(ACTIVE_NAME, data) or _DAMAGED

    def put(self, record: Record) -> None:
        """Durably create or replace the record. ``StoreError`` means the transition is not guaranteed."""
        dfd = self._open_dir()
        temporary = f".tmp-{secrets.token_hex(8)}"
        try:
            try:
                self._write_file(dfd, temporary, record.encode())
                self._ops.rename(temporary, record.filename, dfd)
            except OSError as error:
                self._unlink_quietly(dfd, temporary)
                raise StoreError("state-write") from error
            try:
                self._ops.fsync(dfd)
            except OSError as error:
                raise StoreError("state-sync") from error
        finally:
            close_quietly(dfd)

    def remove(self, record: Record) -> None:
        """Durably remove the record (the invocation's terminal clearance)."""
        dfd = self._open_dir()
        try:
            try:
                self._ops.unlink(record.filename, dfd)
            except FileNotFoundError:
                pass
            except OSError as error:
                raise StoreError("state-remove") from error
            try:
                self._ops.fsync(dfd)
            except OSError as error:
                raise StoreError("state-sync") from error
        finally:
            close_quietly(dfd)

    def remove_stale_temporary(self, name: str, now: float) -> bool:
        """Remove a leftover ``.tmp-*`` of a crashed write, never a live one.

        A ``put`` holds its temporary only between creating it and renaming it onto the slot (a few milliseconds plus an
        ``fsync``), so a file younger than ``STALE_TEMP_SECONDS`` may be a write in progress and is left alone: deleting it
        would fail that admission before any record exists. Only our own regular files are ever removed.
        """
        if _TEMP_NAME.fullmatch(name) is None:
            return False
        dfd = self._open_dir()
        try:
            try:
                info = os.stat(name, dir_fd=dfd, follow_symlinks=False)
            except OSError:
                return False
            if not stat.S_ISREG(info.st_mode) or info.st_uid != self._uid or now - info.st_mtime < STALE_TEMP_SECONDS:
                return False
            self._unlink_quietly(dfd, name)
            return True
        finally:
            close_quietly(dfd)

    def _write_file(self, dfd: int, name: str, data: bytes) -> None:
        fd = self._ops.create(name, dfd)
        try:
            view = memoryview(data)
            while view:
                written = self._ops.write(fd, bytes(view))
                if written <= 0:
                    raise OSError(5, "short write made no progress")
                view = view[written:]
            self._ops.fsync(fd)
        finally:
            close_quietly(fd)

    def _unlink_quietly(self, dfd: int, name: str) -> None:
        try:
            os.unlink(name, dir_fd=dfd)
        except OSError:
            pass
