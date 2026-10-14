"""Descriptor-relative filesystem operations for the cleanup procedure.

Every path is resolved from ``/`` one component at a time with
``O_DIRECTORY|O_NOFOLLOW``; every final object is looked up and opened with
``O_NOFOLLOW`` relative to its parent's descriptor. No symbolic link is ever
followed and no path is re-resolved between a re-verification and its
``unlinkat`` except through the same parent descriptor (H-GR1.7: only root can
swap a name in that window).

Bounded reads: a file is read at most ``size + 1`` bytes and only within its
volume cap. Writes to journals and records go through ``FileIO`` so tests can
inject short writes and failed flushes.
"""

from __future__ import annotations

import errno
import fcntl
import hashlib
import os
import re
import stat
from collections.abc import Callable
from datetime import UTC, datetime

from application.rp11.attribution import (
    MAX_VERIFIED_FILE_BYTES,
    Attribution,
    Identity,
    ObjectKind,
    Observed,
    Owner,
    classify,
)
from application.rp11.canonical import canonical_bytes
from application.rp11.journal import GENESIS, JournalKind, serialize_line
from application.rp11.ports import (
    EvidenceSink,
    EvidenceWriteError,
    GuardMode,
    LockMode,
    LockState,
    Published,
    Removal,
    RemovalOutcome,
)

_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
_FILE_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
_MAX_LISTING = 4_096
_MAX_RECORD_BYTES = 1 << 20
_MAX_RECORD_ENTRIES = 65_536  # the record directory holds every activation's records
_MAX_TERMINAL_BYTES = 65_536


class FileIO:
    """The two calls whose failure the evidence contract is about."""

    def write(self, fd: int, data: bytes) -> int:
        return os.write(fd, data)

    def fsync(self, fd: int) -> None:
        os.fsync(fd)


def close_quietly(fd: int) -> None:
    """Release a descriptor on the inspection/removal boundary: one ``os.close``,
    never retried, and a reported failure never escapes. After ``EINTR``, ``EIO``
    or any other error the descriptor's state is unknown and its number may be
    reused, so a retry could close a stranger's descriptor; the filesystem verdict
    already selected by the caller is not affected by the cleanup."""
    try:
        os.close(fd)
    except OSError:
        pass


def split(path: str) -> tuple[str, str]:
    if not path.startswith("/") or path == "/" or path.endswith("/"):
        raise ValueError("not an absolute object path")
    parent, _, name = path.rpartition("/")
    return parent or "/", name


def open_dir(path: str) -> int:
    """Open ``path`` as a directory, component by component, never following a link."""
    fd = os.open("/", _DIR_FLAGS)
    try:
        for part in path.split("/")[1:]:
            if not part:
                continue
            nxt = os.open(part, _DIR_FLAGS, dir_fd=fd)
            close_quietly(fd)
            fd = nxt
    except BaseException:
        close_quietly(fd)
        raise
    return fd


def _kind(mode: int) -> ObjectKind:
    if stat.S_ISREG(mode):
        return ObjectKind.FILE
    if stat.S_ISDIR(mode):
        return ObjectKind.DIR
    if stat.S_ISLNK(mode):
        return ObjectKind.SYMLINK
    return ObjectKind.OTHER


def _observed(info: os.stat_result, **extra) -> Observed:
    return Observed(
        kind=_kind(info.st_mode),
        dev=info.st_dev,
        ino=info.st_ino,
        uid=info.st_uid,
        gid=info.st_gid,
        mode=stat.S_IMODE(info.st_mode),
        nlink=info.st_nlink,
        size=info.st_size,
        **extra,
    )


# An object whose parent cannot be resolved without following a link (or is
# otherwise unreachable) is never attributable and is reported, not ignored.
UNREACHABLE = Observed(
    kind=ObjectKind.OTHER, dev=0, ino=0, uid=0xFFFFFFFF, gid=0xFFFFFFFF, mode=0, nlink=0, size=0
)


def _read_capped(fd: int, size: int) -> bytes:
    chunks = []
    remaining = size + 1
    while remaining > 0:
        chunk = os.read(fd, min(remaining, 65_536))
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


UNLISTABLE = "unlistable"  # the extended-attribute names could not be listed


def _xattrs(fd: int) -> tuple[str, ...]:
    try:
        return tuple(os.listxattr(fd))
    except OSError:
        return (UNLISTABLE,)


def describe_fd(fd: int, *, list_dir: bool) -> Observed:
    """``fstat``, extended-attribute names, the SHA-256 of a small regular file
    (at most ``size + 1`` bytes read) or, for a directory, whether it is empty.

    Only ``fstat`` may raise. A content read or directory listing that fails
    leaves ``sha256`` or ``empty`` as ``None`` (not established), and unlistable
    attribute names are ``UNLISTABLE``; none of these can classify A1-intact."""
    info = os.fstat(fd)
    kind = _kind(info.st_mode)
    sha = None
    empty = None
    if kind is ObjectKind.FILE and info.st_size <= MAX_VERIFIED_FILE_BYTES:
        try:
            data = _read_capped(fd, info.st_size)
        except OSError:
            data = None
        if data is not None and len(data) == info.st_size:
            sha = hashlib.sha256(data).hexdigest()
    elif kind is ObjectKind.DIR and list_dir:
        try:
            empty = len(os.listdir(fd)) == 0
        except OSError:
            empty = None
    return _observed(info, sha256=sha, xattr_names=_xattrs(fd), empty=empty)


def observe_at(parent_fd: int, name: str, *, list_dir: bool) -> Observed | None:
    """No-follow lookup; ``None`` only for ``ENOENT``. Never raises ``OSError``: a
    lookup that fails otherwise is ``UNREACHABLE`` (present, never attributable),
    and a failed descriptor close does not change the observation."""
    try:
        info = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None
    except OSError:
        return UNREACHABLE
    kind = _kind(info.st_mode)
    if kind not in (ObjectKind.FILE, ObjectKind.DIR):
        return _observed(info)
    flags = _DIR_FLAGS if kind is ObjectKind.DIR else _FILE_FLAGS
    try:
        fd = os.open(name, flags, dir_fd=parent_fd)
    except FileNotFoundError:
        return None
    except OSError:
        return _observed(info)  # present but not openable: never A1-intact
    try:
        return describe_fd(fd, list_dir=list_dir)
    except OSError:
        return _observed(info)  # descriptor not inspectable: never A1-intact
    finally:
        close_quietly(fd)


def _reverified(identity: Identity, observed: Observed, owner: Owner, *, directory: bool) -> Attribution:
    """G-R1 / GRR-3 on a descriptor's observation. An object whose attribute
    names could not be listed was not completely observed: never A1-intact."""
    attribution = classify(identity, observed, owner, require_empty=directory)
    if attribution is Attribution.A1_INTACT and UNLISTABLE in observed.xattr_names:
        return Attribution.A1_DAMAGED
    return attribution


class LocalActivationFs:
    """``ActivationFs`` and ``JournalSource`` on the local filesystem."""

    def __init__(self, owner: Owner) -> None:
        self._owner = owner

    # --- ActivationFs -------------------------------------------------------

    def observe(self, path: str, *, list_dir: bool = False) -> Observed | None:
        parent, name = split(path)
        try:
            pfd = open_dir(parent)
        except FileNotFoundError:
            return None
        except OSError:
            return UNREACHABLE
        try:
            return observe_at(pfd, name, list_dir=list_dir)
        finally:
            close_quietly(pfd)

    def remove(
        self,
        path: str,
        identity: Identity,
        *,
        directory: bool,
        before_unlink: Callable[[Observed], None],
    ) -> Removal:
        """G-R1 / GRR-2 … GRR-4. Never raises for the target's inspection: a failed
        ``fstat`` is ``MISMATCH`` A0; a failed content read, attribute listing or
        directory listing leaves the fact unestablished, so the object is kept
        (A1-damaged when type and ``(dev, ino)`` still match, else A0). A failed
        descriptor close never overrides the selected result. Only
        ``before_unlink`` may raise, and then nothing is unlinked."""
        parent, name = split(path)
        try:
            pfd = open_dir(parent)
        except FileNotFoundError:
            return Removal(RemovalOutcome.ABSENT)
        except OSError:
            return Removal(RemovalOutcome.MISMATCH, Attribution.A0, UNREACHABLE)
        try:
            # G-R1: re-verify through a descriptor immediately before removal.
            flags = _DIR_FLAGS if directory else _FILE_FLAGS
            try:
                fd = os.open(name, flags, dir_fd=pfd)
            except FileNotFoundError:
                return Removal(RemovalOutcome.ABSENT)
            except OSError:
                observed = observe_at(pfd, name, list_dir=directory)
                if observed is None:
                    return Removal(RemovalOutcome.ABSENT)
                return Removal(RemovalOutcome.MISMATCH, Attribution.A0, observed)
            try:
                observed = describe_fd(fd, list_dir=directory)
            except OSError:
                return Removal(RemovalOutcome.MISMATCH, Attribution.A0, UNREACHABLE)
            finally:
                close_quietly(fd)
            attribution = _reverified(identity, observed, self._owner, directory=directory)
            if attribution is not Attribution.A1_INTACT:
                return Removal(RemovalOutcome.MISMATCH, attribution, observed)
            before_unlink(observed)
            try:
                if directory:
                    os.rmdir(name, dir_fd=pfd)
                else:
                    os.unlink(name, dir_fd=pfd)
            except FileNotFoundError:
                return Removal(RemovalOutcome.ABSENT, attribution, observed)
            except OSError as exc:
                return Removal(RemovalOutcome.UNREMOVABLE, attribution, observed, exc.errno or errno.EIO)
            try:
                os.fsync(pfd)  # on tmpfs possibly a no-op; the result is not relied on
            except OSError:
                pass
            return Removal(RemovalOutcome.REMOVED, attribution, observed)
        finally:
            close_quietly(pfd)

    def read_root_file(self, path: str, *, max_bytes: int, mode: int) -> bytes | None:
        """Any failed lookup, ``fstat`` or read is ``None`` (GRR-1: ``identity-unavailable``)."""
        parent, name = split(path)
        try:
            pfd = open_dir(parent)
        except OSError:
            return None
        try:
            pinfo = os.fstat(pfd)
            if pinfo.st_uid != self._owner.uid or pinfo.st_mode & 0o022:
                return None
            try:
                fd = os.open(name, _FILE_FLAGS, dir_fd=pfd)
            except OSError:
                return None
            try:
                info = os.fstat(fd)
                if (
                    not stat.S_ISREG(info.st_mode)
                    or (info.st_uid, info.st_gid) != (self._owner.uid, self._owner.gid)
                    or stat.S_IMODE(info.st_mode) != mode
                    or info.st_nlink != 1
                    or info.st_size > max_bytes
                ):
                    return None
                data = _read_capped(fd, info.st_size)
                return data if len(data) == info.st_size else None
            finally:
                close_quietly(fd)
        except OSError:
            return None
        finally:
            close_quietly(pfd)

    def list_prefixed(self, directory: str, prefix: str) -> tuple[str, ...] | None:
        try:
            fd = open_dir(directory)
        except OSError:
            return None
        try:
            names = os.listdir(fd)
        except OSError:
            return None
        finally:
            close_quietly(fd)
        found = tuple(sorted(n for n in names if n.startswith(prefix)))
        return found if len(found) <= _MAX_LISTING else None

    # --- JournalSource ----------------------------------------------------------

    def read_journal(
        self, directory: str, *, max_bytes: int, dir_uid: int, dir_mode: int
    ) -> bytes | None:
        try:
            dfd = open_dir(directory)
        except OSError:
            return None
        try:
            dinfo = os.fstat(dfd)
            if dinfo.st_uid != dir_uid or stat.S_IMODE(dinfo.st_mode) != dir_mode:
                return None
            try:
                fd = os.open("journal", _FILE_FLAGS, dir_fd=dfd)
            except OSError:
                return None
            try:
                info = os.fstat(fd)
                if (
                    not stat.S_ISREG(info.st_mode)
                    or (info.st_uid, info.st_gid) != (self._owner.uid, self._owner.gid)
                    or stat.S_IMODE(info.st_mode) != 0o644
                    or info.st_nlink != 1
                    or info.st_size > max_bytes
                ):
                    return None
                data = _read_capped(fd, info.st_size)
                return data if len(data) == info.st_size else None
            finally:
                close_quietly(fd)
        finally:
            close_quietly(dfd)


# --- journals -------------------------------------------------------------------


class JournalAppender:
    """An ``EvidenceSink`` over one exclusively created journal descriptor.

    Each line is one ``write`` of the whole line followed by ``fsync`` (H-JRN.6,
    H-JRN.7). A short write or any error breaks the sink: nothing is ever retried
    and no later line is written, so a torn line can only be the last one.
    """

    def __init__(self, fd: int, *, kind: JournalKind, run: str, io: FileIO) -> None:
        self._fd = fd
        self._kind = kind
        self._run = run
        self._io = io
        self._seq = 0
        self._prev = GENESIS
        self._hash = hashlib.sha256()
        self._length = 0
        self._broken = False

    def append(self, op: str, fields: dict) -> None:
        if self._broken:
            raise EvidenceWriteError("journal no longer accepts lines")
        line = serialize_line(
            self._kind, seq=self._seq + 1, prev=self._prev, run=self._run, op=op, fields=fields
        )
        try:
            written = self._io.write(self._fd, line)
            if written != len(line):
                raise EvidenceWriteError("short write")
            self._io.fsync(self._fd)
        except (OSError, EvidenceWriteError) as exc:
            self._broken = True
            raise EvidenceWriteError(str(exc)) from exc
        self._seq += 1
        self._prev = hashlib.sha256(line).hexdigest()
        self._hash.update(line)
        self._length += len(line)

    def prefix(self) -> tuple[str, int]:
        return self._hash.hexdigest(), self._length

    def close(self) -> None:
        try:
            os.close(self._fd)
        except OSError:
            pass


class LocalAttemptStore:
    """CL-0: ``<var_tmp>/<id>-deact-<k>-evidence/`` (``0755``) and its journal (``0644``)."""

    def __init__(self, *, var_tmp: str, activation_id: str, owner: Owner, io: FileIO | None = None) -> None:
        self._var_tmp = var_tmp
        self._activation_id = activation_id
        self._owner = owner
        self._io = io or FileIO()
        self.sink: JournalAppender | None = None

    def create(self, k: int) -> EvidenceSink:
        name = f"{self._activation_id}-deact-{k}-evidence"
        try:
            vfd = open_dir(self._var_tmp)
        except OSError as exc:
            raise EvidenceWriteError(f"cannot open the evidence parent: {exc.strerror}") from exc
        try:
            try:
                os.mkdir(name, 0o755, dir_fd=vfd)
            except FileExistsError:
                raise
            except OSError as exc:
                raise EvidenceWriteError(f"cannot create the attempt directory: {exc.strerror}") from exc
            try:
                dfd = os.open(name, _DIR_FLAGS, dir_fd=vfd)
            except OSError as exc:
                raise EvidenceWriteError(f"attempt directory: {exc.strerror}") from exc
            try:
                os.fchmod(dfd, 0o755)
                if os.fstat(dfd).st_uid != self._owner.uid:
                    raise EvidenceWriteError("attempt directory has an unexpected owner")
                self._io.fsync(vfd)
                jfd = os.open(
                    "journal",
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_APPEND | os.O_NOFOLLOW | os.O_CLOEXEC,
                    0o644,
                    dir_fd=dfd,
                )
                os.fchmod(jfd, 0o644)
                self._io.fsync(jfd)
                self._io.fsync(dfd)
            except OSError as exc:
                raise EvidenceWriteError(f"journal: {exc.strerror}") from exc
            finally:
                os.close(dfd)
        finally:
            os.close(vfd)
        self.sink = JournalAppender(
            jfd, kind=JournalKind.ATTEMPT, run=f"{self._activation_id}-deact-{k}", io=self._io
        )
        return self.sink


# --- records (protocol PF) -------------------------------------------------------


class LocalRecordStore:
    """``RecordStore``: PF into the record directory, ``0444``, never replacing."""

    def __init__(self, directory: str, owner: Owner, io: FileIO | None = None) -> None:
        self._dir = directory
        self._owner = owner
        self._io = io or FileIO()
        self._fs = LocalActivationFs(owner)

    def read(self, name: str) -> bytes | None:
        return self._fs.read_root_file(f"{self._dir}/{name}", max_bytes=_MAX_RECORD_BYTES, mode=0o444)

    def deact_attempts(self, activation_id: str) -> tuple[int, ...] | None:
        """Exact ``<id>.deact-<k>.json`` names (``1 <= k <= 99``) by descriptor, no-follow
        resolution of the directory, at most ``_MAX_RECORD_ENTRIES`` entries examined."""
        pattern = re.compile(re.escape(activation_id) + r"\.deact-([1-9][0-9]?)\.json")
        try:
            fd = open_dir(self._dir)
        except OSError:
            return None
        found = []
        try:
            info = os.fstat(fd)
            if info.st_uid != self._owner.uid or info.st_mode & 0o022:
                return None
            with os.scandir(fd) as entries:
                for seen, entry in enumerate(entries, start=1):
                    if seen > _MAX_RECORD_ENTRIES:
                        return None
                    match = pattern.fullmatch(entry.name)
                    if match:
                        found.append(int(match.group(1)))
        except OSError:
            return None
        finally:
            os.close(fd)
        return tuple(sorted(found))

    def publish(self, name: str, data: bytes, sink: EvidenceSink) -> Published:
        digest = hashlib.sha256(data).hexdigest()
        rfd = open_dir(self._dir)
        try:
            dinfo = os.fstat(rfd)
            if dinfo.st_uid != self._owner.uid or dinfo.st_mode & 0o022:
                raise PermissionError(errno.EPERM, "record directory is not root-only")
            # PF-1: nothing at the name.
            try:
                os.stat(name, dir_fd=rfd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise FileExistsError(errno.EEXIST, "preexisting-path")
            # PF-2
            sink.append(
                "file-intent",
                {
                    "dir": self._dir,
                    "name": name,
                    "sha256": digest,
                    "size": len(data),
                    "uid": self._owner.uid,
                    "gid": self._owner.gid,
                    "mode": 0o444,
                    "grant": False,
                },
            )
            # PF-3, PF-4: an unnamed inode whose identity is durable before any name.
            fd = os.open(".", os.O_TMPFILE | os.O_WRONLY | os.O_CLOEXEC, 0o600, dir_fd=rfd)
            try:
                info = os.fstat(fd)
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 0 or info.st_size != 0:
                    raise OSError(errno.EIO, "unnamed inode is not fresh")
                sink.append(
                    "file-identity",
                    {"dir": self._dir, "name": name, "dev": info.st_dev, "ino": info.st_ino},
                )
                # PF-5
                view = memoryview(data)
                while view:
                    written = self._io.write(fd, bytes(view))
                    if written <= 0:
                        raise OSError(errno.EIO, "short write")
                    view = view[written:]
                self._io.fsync(fd)
                os.fchown(fd, self._owner.uid, self._owner.gid)
                os.fchmod(fd, 0o444)
                self._io.fsync(fd)
                after = os.fstat(fd)
                if (after.st_dev, after.st_ino, after.st_size, stat.S_IMODE(after.st_mode)) != (
                    info.st_dev,
                    info.st_ino,
                    len(data),
                    0o444,
                ):
                    raise OSError(errno.EIO, "record changed before linking")
                # PF-6: link, never replacing (EEXIST is a hard stop: the object is A0).
                os.link(f"/proc/self/fd/{fd}", name, dst_dir_fd=rfd, follow_symlinks=True)
            finally:
                os.close(fd)
            self._io.fsync(rfd)  # PF-7
            sink.append("file-linked", {"dir": self._dir, "name": name})  # PF-8
            # PF-9
            observed = observe_at(rfd, name, list_dir=False)
            expected = Identity(
                path=f"{self._dir}/{name}",
                kind=ObjectKind.FILE,
                dev=info.st_dev,
                ino=info.st_ino,
                mode=0o444,
                sha256=digest,
                size=len(data),
            )
            if len(data) > MAX_VERIFIED_FILE_BYTES:
                ok = observed is not None and (observed.dev, observed.ino) == (info.st_dev, info.st_ino)
            else:
                ok = classify(expected, observed, self._owner) is Attribution.A1_INTACT
            if not ok:
                raise OSError(errno.EIO, "record re-read differs")
            return Published(digest, len(data))
        finally:
            os.close(rfd)


# --- the lock on K -----------------------------------------------------------------


class LocalLock:
    """CL-0 / H-LK: ``flock(LOCK_EX|LOCK_NB)`` on K, repeated until λ.

    K absent, not a root ``0700`` directory or unopenable: ``absent``. Still held
    by another process at the deadline, or any other error: ``degraded``. In
    both cases cleanup continues without ordering against CP.
    """

    def __init__(self, path: str, owner: Owner, clock, *, slice_ms: int = 100) -> None:
        self._path = path
        self._owner = owner
        self._clock = clock
        self._slice = slice_ms
        self._fd: int | None = None

    def acquire(self, deadline_ms: int) -> LockState:
        start = self._clock.monotonic_ms()
        parent, name = split(self._path)
        try:
            pfd = open_dir(parent)
        except OSError:
            return LockState(LockMode.ABSENT, None, 0)
        try:
            fd = os.open(name, _DIR_FLAGS, dir_fd=pfd)
        except OSError:
            return LockState(LockMode.ABSENT, None, 0)
        finally:
            os.close(pfd)
        info = os.fstat(fd)
        if (
            not stat.S_ISDIR(info.st_mode)
            or (info.st_uid, info.st_gid) != (self._owner.uid, self._owner.gid)
            or stat.S_IMODE(info.st_mode) != 0o700
        ):
            os.close(fd)
            return LockState(LockMode.ABSENT, None, 0)
        identity = Identity(self._path, ObjectKind.DIR, info.st_dev, info.st_ino, 0o700)
        end = start + deadline_ms
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                self._fd = fd
                return LockState(LockMode.HELD, identity, self._clock.monotonic_ms() - start)
            except InterruptedError:
                continue
            except BlockingIOError:
                pass
            except OSError:
                os.close(fd)
                return LockState(LockMode.DEGRADED, identity, self._clock.monotonic_ms() - start)
            now = self._clock.monotonic_ms()
            if now >= end:
                os.close(fd)
                return LockState(LockMode.DEGRADED, identity, now - start)
            self._clock.sleep_ms(min(self._slice, end - now))

    def release(self) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None


# --- the backstop lock and terminal journal (BS-4) -----------------------------------


class LocalBackstopGuard:
    """``BackstopGuard``: ``<store>/backstop/<activation_id>.journal``.

    The store must be a root-only directory; ``backstop/`` is created ``0755`` in
    it if absent and must then be exactly that; the journal is created or opened
    ``O_APPEND|O_NOFOLLOW`` and must be a regular one-link root ``0644`` file. The
    ``flock`` is taken without blocking: another holder means ``busy``. Any other
    failure is ``unavailable`` and leaves nothing open.
    """

    def __init__(self, store: str, activation_id: str, owner: Owner, io: FileIO | None = None) -> None:
        self._store = store
        self._name = f"{activation_id}.journal"
        self._owner = owner
        self._io = io or FileIO()
        self._fd: int | None = None

    @property
    def path(self) -> str:
        return f"{self._store}/backstop/{self._name}"

    def acquire(self) -> GuardMode:
        try:
            fd = self._open()
        except OSError:
            return GuardMode.UNAVAILABLE
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(fd)
            return GuardMode.BUSY
        except OSError:
            os.close(fd)
            return GuardMode.UNAVAILABLE
        self._fd = fd
        return GuardMode.HELD

    def _open(self) -> int:
        sfd = open_dir(self._store)
        try:
            info = os.fstat(sfd)
            if info.st_uid != self._owner.uid or info.st_mode & 0o022:
                raise PermissionError(errno.EPERM, "store is not root-only")
            try:
                os.mkdir("backstop", 0o755, dir_fd=sfd)
                self._io.fsync(sfd)
            except FileExistsError:
                pass
            dfd = os.open("backstop", _DIR_FLAGS, dir_fd=sfd)
        finally:
            os.close(sfd)
        try:
            dinfo = os.fstat(dfd)
            if (dinfo.st_uid, dinfo.st_gid) != (self._owner.uid, self._owner.gid) or stat.S_IMODE(dinfo.st_mode) != 0o755:
                raise PermissionError(errno.EPERM, "backstop directory is not root 0755")
            fd = os.open(
                self._name,
                os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                0o644,
                dir_fd=dfd,
            )
            try:
                jinfo = os.fstat(fd)
                if (
                    not stat.S_ISREG(jinfo.st_mode)
                    or (jinfo.st_uid, jinfo.st_gid) != (self._owner.uid, self._owner.gid)
                    or stat.S_IMODE(jinfo.st_mode) != 0o644
                    or jinfo.st_nlink != 1
                ):
                    raise PermissionError(errno.EPERM, "terminal journal is not a root 0644 file")
                self._io.fsync(dfd)
            except BaseException:
                os.close(fd)
                raise
        finally:
            os.close(dfd)
        return fd

    def append_terminal(self, fields: dict) -> None:
        if self._fd is None:
            raise EvidenceWriteError("no terminal journal is held")
        line = canonical_bytes(fields)
        try:
            if os.fstat(self._fd).st_size + len(line) > _MAX_TERMINAL_BYTES:
                raise EvidenceWriteError("terminal journal is at its size cap")
            written = self._io.write(self._fd, line)
            if written != len(line):
                raise EvidenceWriteError("short write")
            self._io.fsync(self._fd)
        except OSError as exc:
            raise EvidenceWriteError(str(exc)) from exc

    def release(self) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None


# --- host facts ---------------------------------------------------------------------


class LocalHostFacts:
    def __init__(self, *, boot_id_file: str, mountinfo: str, run: str) -> None:
        self._boot_id_file = boot_id_file
        self._mountinfo = mountinfo
        self._run = run

    def boot_id(self) -> str | None:
        try:
            with open(self._boot_id_file, "rb") as handle:
                text = handle.read(64).decode("ascii").strip()
        except (OSError, UnicodeDecodeError):
            return None
        parts = text.split("-")
        if [len(p) for p in parts] != [8, 4, 4, 4, 12] or not all(
            c in "0123456789abcdef" for c in text.replace("-", "")
        ):
            return None
        return text

    def run_fstype(self) -> str | None:
        try:
            with open(self._mountinfo, "rb") as handle:
                data = handle.read(1 << 20)
        except OSError:
            return None
        fstype = None
        for line in data.decode("utf-8", "replace").splitlines():
            fields = line.split(" ")
            if len(fields) < 10 or "-" not in fields:
                continue
            sep = fields.index("-")
            if fields[4] == self._run and sep + 1 < len(fields):
                fstype = fields[sep + 1]  # the last mount on /run is the visible one
        return fstype

    def utc_now(self) -> str:
        return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
