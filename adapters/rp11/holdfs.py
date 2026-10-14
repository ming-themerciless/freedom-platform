"""Descriptor-relative filesystem work of the holder (RT-2): PF, PT, K, the ACT journal.

As in ``fsops``, every path is resolved one component at a time from ``/`` with
``O_DIRECTORY|O_NOFOLLOW`` and every final object is looked up and opened with
``O_NOFOLLOW`` relative to its parent's descriptor.

* **PF** (H-PF.1 … H-PF.9): nothing at the name; ``file-intent``; an unnamed
  ``O_TMPFILE`` inode whose identity is durable (``file-identity``) before any
  name exists; content, owner and mode with flushes and a re-check; the link
  ``/proc/self/fd/<fd>`` → name, which never replaces (``EEXIST`` ⇒ the object at
  the name is A0 and kept); parent flush; ``file-linked``; re-verification. The
  caller may run steps between PF-5 and PF-6 (``prepare`` then ``link``).
* **PT** (H-PT.1 … H-PT.10): a ``0700`` temporary top built under its run-unique
  name, members created and verified one by one (directories ``dir-identity``,
  files by PF), final owner and modes bottom-up, the seal (every directory lists
  exactly its members, each member re-checked against its identity,
  ``tree-sealed``), then ``renameat2(RENAME_NOREPLACE)`` to the final name,
  parent flush, ``tree-linked`` and verification at the final name.
* **K** (H-LK, LD-1): created exclusively in ``/run``, ``0700``, empty, no
  forbidden extended-attribute name, then ``flock(LOCK_EX|LOCK_NB)`` once.

Python has no ``renameat2`` binding, so the one call is made through ``ctypes``
against the already loaded C library (no other library is loaded and no process
is started). A host without it refuses PT (``rename-unsupported``): there is no
replacing fallback.
"""

from __future__ import annotations

import ctypes
import errno
import fcntl
import hashlib
import os
import stat

from application.rp11.attribution import (
    FORBIDDEN_XATTRS,
    Attribution,
    Identity,
    ObjectKind,
    Owner,
    classify,
)
from application.rp11.canonical import canonical_bytes
from application.rp11.journal import JournalKind
from application.rp11.ports import (
    EvidenceSink,
    EvidenceWriteError,
    GuardMode,
    LockObjectError,
    PublishError,
    TreeMember,
)

from .fsops import _DIR_FLAGS, _FILE_FLAGS, FileIO, JournalAppender, _read_capped, observe_at, open_dir, split

_RENAME_NOREPLACE = 1
_ACL_PREFIX = "system.posix_acl"


def _join(parent: str, name: str) -> str:
    return "/" + name if parent == "/" else f"{parent.rstrip('/')}/{name}"


def _xattr_names(fd: int) -> tuple[str, ...] | None:
    try:
        return tuple(os.listxattr(fd))
    except OSError:
        return None


def _forbidden(names: tuple[str, ...] | None) -> bool:
    return names is None or bool(set(names) & FORBIDDEN_XATTRS) or any(
        n.startswith(_ACL_PREFIX) for n in names
    )


def renameat2_noreplace(old_dir_fd: int, old: str, new_dir_fd: int, new: str) -> None:
    """``renameat2(…, RENAME_NOREPLACE)``; raises ``OSError`` with the call's errno."""
    libc = ctypes.CDLL(None, use_errno=True)
    function = getattr(libc, "renameat2", None)
    if function is None:
        raise OSError(errno.ENOSYS, "renameat2 is not available")
    function.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    function.restype = ctypes.c_int
    if function(old_dir_fd, os.fsencode(old), new_dir_fd, os.fsencode(new), _RENAME_NOREPLACE) != 0:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code))


# --- PF ---------------------------------------------------------------------------


class _Prepared:
    """PF-1 … PF-5 done. Owns a duplicate of the parent descriptor and the inode's."""

    def __init__(self, pfd: int, fd: int, name: str, journal_dir: str, identity: Identity, owner: Owner, io: FileIO) -> None:
        self._pfd = pfd
        self._fd: int | None = fd
        self._name = name
        self._dir = journal_dir
        self.identity = identity
        self._owner = owner
        self._io = io

    def link(self) -> None:
        if self._fd is None:
            raise PublishError("io", "descriptor already discarded")
        try:
            os.link(f"/proc/self/fd/{self._fd}", self._name, dst_dir_fd=self._pfd, follow_symlinks=True)
        except FileExistsError:
            raise PublishError("foreign-rule", "a name appeared before the link") from None
        except OSError as exc:
            raise PublishError("io", exc.strerror or "link") from None

    def commit(self, sink: EvidenceSink) -> None:
        try:
            self._io.fsync(self._pfd)  # PF-7 (on tmpfs possibly a no-op)
        except OSError as exc:
            raise PublishError("io", exc.strerror or "fsync") from None
        sink.append("file-linked", {"dir": self._dir, "name": self._name})  # PF-8
        self.verify()

    def verify(self) -> None:
        """PF-9 through the parent descriptor (the same inode under any parent name)."""
        observed = observe_at(self._pfd, self._name, list_dir=False)
        if classify(self.identity, observed, self._owner) is not Attribution.A1_INTACT:
            raise PublishError("mismatch", "re-verification differs")

    def discard(self) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        if self._pfd >= 0:
            os.close(self._pfd)
            self._pfd = -1


class LocalPublisher:
    """``Publisher`` on the local filesystem (root-owned objects in production)."""

    def __init__(self, owner: Owner, io: FileIO | None = None) -> None:
        self._owner = owner
        self._io = io or FileIO()

    # PF

    def prepare(self, directory: str, name: str, data: bytes, mode: int, *, grant: bool, sink: EvidenceSink) -> _Prepared:
        try:
            pfd = open_dir(directory)
        except OSError as exc:
            raise PublishError("io", exc.strerror or "parent") from None
        try:
            return self._prepare_at(pfd, directory, name, data, mode, grant=grant, sink=sink)
        except BaseException:
            os.close(pfd)
            raise

    def publish(self, directory: str, name: str, data: bytes, mode: int, *, grant: bool, sink: EvidenceSink) -> Identity:
        prepared = self.prepare(directory, name, data, mode, grant=grant, sink=sink)
        try:
            prepared.link()
            prepared.commit(sink)
            return prepared.identity
        finally:
            prepared.discard()

    def _prepare_at(self, pfd: int, journal_dir: str, name: str, data: bytes, mode: int, *, grant: bool, sink: EvidenceSink) -> _Prepared:
        """PF-1 … PF-5 in the directory ``pfd``; takes ownership of ``pfd`` on success."""
        try:
            os.stat(name, dir_fd=pfd, follow_symlinks=False)  # PF-1
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise PublishError("io", exc.strerror or "lookup") from None
        else:
            raise PublishError("preexisting-path", name)
        digest = hashlib.sha256(data).hexdigest()
        sink.append(  # PF-2
            "file-intent",
            {
                "dir": journal_dir,
                "name": name,
                "sha256": digest,
                "size": len(data),
                "uid": self._owner.uid,
                "gid": self._owner.gid,
                "mode": mode,
                "grant": grant,
            },
        )
        try:
            fd = os.open(".", os.O_TMPFILE | os.O_WRONLY | os.O_CLOEXEC, 0o600, dir_fd=pfd)  # PF-3
        except OSError as exc:
            raise PublishError("io", exc.strerror or "tmpfile") from None
        try:
            info = os.fstat(fd)  # PF-4
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 0 or info.st_size != 0:
                raise PublishError("mismatch", "unnamed inode is not fresh")
            sink.append("file-identity", {"dir": journal_dir, "name": name, "dev": info.st_dev, "ino": info.st_ino})
            try:  # PF-5
                view = memoryview(data)
                while view:
                    written = self._io.write(fd, bytes(view))
                    if written <= 0:
                        raise OSError(errno.EIO, "short write")
                    view = view[written:]
                self._io.fsync(fd)
                os.fchown(fd, self._owner.uid, self._owner.gid)
                os.fchmod(fd, mode)
                self._io.fsync(fd)
                after = os.fstat(fd)
            except OSError as exc:
                raise PublishError("io", exc.strerror or "write") from None
            if (after.st_dev, after.st_ino, after.st_size, stat.S_IMODE(after.st_mode), after.st_uid) != (
                info.st_dev,
                info.st_ino,
                len(data),
                mode,
                self._owner.uid,
            ):
                raise PublishError("mismatch", "inode changed before linking")
        except BaseException:
            os.close(fd)
            raise
        identity = Identity(
            path=_join(journal_dir, name),
            kind=ObjectKind.FILE,
            dev=info.st_dev,
            ino=info.st_ino,
            mode=mode,
            sha256=digest,
            size=len(data),
        )
        return _Prepared(pfd, fd, name, journal_dir, identity, self._owner, self._io)

    # PT

    def publish_tree(
        self,
        parent: str,
        top: str,
        temp: str,
        tag: str,
        members: tuple[TreeMember, ...],
        sink: EvidenceSink,
    ) -> tuple[Identity, ...]:
        if not members or members[0].rel != "." or members[0].is_file:
            raise ValueError("a tree's first member is its top directory")
        final_top = _join(parent, top)
        try:
            pfd = open_dir(parent)
        except OSError as exc:
            raise PublishError("io", exc.strerror or "parent") from None
        dirs: dict[str, int] = {}
        try:
            for name in (top, temp):  # PT-1
                try:
                    os.stat(name, dir_fd=pfd, follow_symlinks=False)
                except FileNotFoundError:
                    continue
                except OSError as exc:
                    raise PublishError("io", exc.strerror or "lookup") from None
                raise PublishError("preexisting-path", name)
            sink.append(  # PT-2
                "tree-intent",
                {
                    "parent": parent,
                    "top": top,
                    "temp": temp,
                    "tag": tag,
                    "members": [_member_doc(m) for m in members],
                },
            )
            identities: list[Identity] = []
            for member in members:  # PT-3 (the top), PT-4 (member directories), PT-5 (files)
                rel_parent, _, base = member.rel.rpartition("/")
                if member.rel == ".":
                    container, name, final = pfd, temp, final_top
                else:
                    container, name = dirs[rel_parent or "."], base
                    final = _join(final_top, member.rel)
                if member.is_file:
                    own = os.dup(container)
                    try:
                        prepared = self._prepare_at(
                            own, _join(final_top, rel_parent) if rel_parent else final_top,
                            name, member.data, member.mode, grant=False, sink=sink,
                        )
                    except BaseException:
                        os.close(own)
                        raise
                    try:
                        prepared.link()
                        prepared.commit(sink)
                    finally:
                        prepared.discard()
                    identities.append(prepared.identity)
                    continue
                dirs[member.rel] = self._make_dir(container, name)
                info = os.fstat(dirs[member.rel])
                sink.append("dir-identity", {"rel": member.rel, "dev": info.st_dev, "ino": info.st_ino})
                identities.append(Identity(final, ObjectKind.DIR, info.st_dev, info.st_ino, member.mode))
            for member in reversed(members):  # PT-6, bottom-up
                if member.is_file:
                    continue
                fd = dirs[member.rel]
                try:
                    os.fchown(fd, self._owner.uid, self._owner.gid)
                    os.fchmod(fd, member.mode)
                    self._io.fsync(fd)
                except OSError as exc:
                    raise PublishError("io", exc.strerror or "mode") from None
            self._fsync(pfd)
            sink.append("tree-sealed", {"temp": temp, "inventory_sha256": self._seal(members, dirs, identities)})  # PT-7
            try:  # PT-8
                renameat2_noreplace(pfd, temp, pfd, top)
            except FileExistsError:
                raise PublishError("preexisting-path", top) from None
            except OSError as exc:
                if exc.errno in (errno.EINVAL, errno.ENOSYS):
                    raise PublishError("rename-unsupported", exc.strerror or "renameat2") from None
                raise PublishError("io", exc.strerror or "rename") from None
            self._fsync(pfd)  # PT-9
            sink.append("tree-linked", {"parent": parent, "top": top})
            self._verify_top(pfd, top, identities[0])  # PT-10
            for identity, member in zip(identities, members):
                if member.is_file:
                    container = dirs[member.rel.rpartition("/")[0] or "."]
                    observed = observe_at(container, member.rel.rpartition("/")[2], list_dir=False)
                    if classify(identity, observed, self._owner) is not Attribution.A1_INTACT:
                        raise PublishError("mismatch", "member re-verification differs")
            return tuple(identities)
        finally:
            for fd in dirs.values():
                os.close(fd)
            os.close(pfd)

    def _make_dir(self, container: int, name: str) -> int:
        """Create ``name`` ``0700`` without replacing, open it and check it is fresh."""
        try:
            os.mkdir(name, 0o700, dir_fd=container)
        except FileExistsError:
            raise PublishError("preexisting-path", name) from None
        except OSError as exc:
            raise PublishError("io", exc.strerror or "mkdir") from None
        try:
            fd = os.open(name, _DIR_FLAGS, dir_fd=container)
        except OSError as exc:
            raise PublishError("io", exc.strerror or "open") from None
        info = os.fstat(fd)
        if (
            not stat.S_ISDIR(info.st_mode)
            or info.st_uid != self._owner.uid
            or stat.S_IMODE(info.st_mode) != 0o700
            or info.st_nlink != 2
            or os.listdir(fd)
        ):
            os.close(fd)
            raise PublishError("mismatch", "new directory is not fresh")
        return fd

    def _seal(self, members, dirs: dict[str, int], identities: list[Identity]) -> str:
        """PT-7: each directory lists exactly its members; each member matches its identity."""
        expected: dict[str, set[str]] = {rel: set() for rel in dirs}
        for member in members[1:]:
            parent_rel, _, base = member.rel.rpartition("/")
            expected[parent_rel or "."].add(base)
        inventory = []
        for rel, fd in dirs.items():
            if set(os.listdir(fd)) != expected[rel]:
                raise PublishError("mismatch", "tree listing differs")
        for member, identity in zip(members, identities):
            parent_rel, _, base = member.rel.rpartition("/")
            if member.rel == ".":
                info = os.fstat(dirs["."])
            else:
                info = os.stat(base, dir_fd=dirs[parent_rel or "."], follow_symlinks=False)
            kind_ok = stat.S_ISREG(info.st_mode) if member.is_file else stat.S_ISDIR(info.st_mode)
            if (
                not kind_ok
                or (info.st_dev, info.st_ino) != (identity.dev, identity.ino)
                or stat.S_IMODE(info.st_mode) != member.mode
                or (info.st_uid, info.st_gid) != (self._owner.uid, self._owner.gid)
            ):
                raise PublishError("mismatch", "sealed member differs")
            inventory.append(
                [member.rel, "file" if member.is_file else "dir", identity.dev, identity.ino, member.mode, identity.sha256 or "absent"]
            )
        return hashlib.sha256(canonical_bytes(sorted(inventory))).hexdigest()

    def _verify_top(self, pfd: int, top: str, identity: Identity) -> None:
        try:
            fd = os.open(top, _DIR_FLAGS, dir_fd=pfd)
        except OSError as exc:
            raise PublishError("mismatch", exc.strerror or "top") from None
        try:
            info = os.fstat(fd)
            if (info.st_dev, info.st_ino) != (identity.dev, identity.ino) or stat.S_IMODE(info.st_mode) != identity.mode:
                raise PublishError("mismatch", "top differs after the rename")
        finally:
            os.close(fd)

    def _fsync(self, fd: int) -> None:
        try:
            self._io.fsync(fd)
        except OSError as exc:
            raise PublishError("io", exc.strerror or "fsync") from None


def _member_doc(member: TreeMember) -> dict:
    if member.is_file:
        return {
            "rel": member.rel,
            "kind": "file",
            "mode": member.mode,
            "sha256": hashlib.sha256(member.data).hexdigest(),
            "size": len(member.data),
        }
    return {"rel": member.rel, "kind": "dir", "mode": member.mode}


# --- K ------------------------------------------------------------------------------


class LocalActivationLock:
    """``ActivationLock``: K = ``<run>/freedom-blades-rp11-lock-<id>/``."""

    def __init__(self, path: str, owner: Owner) -> None:
        self._path = path
        self._owner = owner
        self._identity: Identity | None = None
        self._fd: int | None = None

    def create(self) -> Identity:
        parent, name = split(self._path)
        try:
            pfd = open_dir(parent)
        except OSError:
            raise LockObjectError("run is unreachable") from None
        try:
            try:
                os.mkdir(name, 0o700, dir_fd=pfd)
            except OSError:
                raise LockObjectError("K could not be created exclusively") from None
            try:
                fd = os.open(name, _DIR_FLAGS, dir_fd=pfd)
            except OSError:
                raise LockObjectError("K could not be opened") from None
            try:
                os.fsync(pfd)
            except OSError:
                pass  # tmpfs; no claim depends on it
        finally:
            os.close(pfd)
        info = os.fstat(fd)
        if (
            not stat.S_ISDIR(info.st_mode)
            or (info.st_uid, info.st_gid) != (self._owner.uid, self._owner.gid)
            or stat.S_IMODE(info.st_mode) != 0o700
            or info.st_nlink != 2
            or _forbidden(_xattr_names(fd))
        ):
            os.close(fd)
            raise LockObjectError("K is not a fresh root 0700 directory")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(fd)
            raise LockObjectError("K could not be locked") from None
        self._fd = fd
        self._identity = Identity(self._path, ObjectKind.DIR, info.st_dev, info.st_ino, 0o700)
        return self._identity

    def try_once(self) -> GuardMode:
        """OS-5: K with the identity created at AM-0, one non-blocking attempt."""
        if self._fd is not None:
            return GuardMode.HELD
        parent, name = split(self._path)
        try:
            pfd = open_dir(parent)
            try:
                fd = os.open(name, _DIR_FLAGS, dir_fd=pfd)
            finally:
                os.close(pfd)
        except OSError:
            return GuardMode.UNAVAILABLE
        info = os.fstat(fd)
        if (
            self._identity is None
            or (info.st_dev, info.st_ino) != (self._identity.dev, self._identity.ino)
            or (info.st_uid, info.st_gid) != (self._owner.uid, self._owner.gid)
            or stat.S_IMODE(info.st_mode) != 0o700
        ):
            os.close(fd)
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

    def release(self) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None


# --- checks, the staged rule and the ACT journal ------------------------------------------


class LocalHoldHost:
    """``HoldHost`` on the local filesystem."""

    def __init__(self, owner: Owner, io: FileIO | None = None) -> None:
        self._owner = owner
        self._io = io or FileIO()

    def directory_problem(self, path: str) -> str | None:
        parent, name = split(path) if path != "/" else ("/", "")
        try:
            pfd = open_dir(parent)
        except FileNotFoundError:
            return "absent"
        except OSError:
            return "unreachable"
        try:
            if name:
                try:
                    info = os.stat(name, dir_fd=pfd, follow_symlinks=False)
                except FileNotFoundError:
                    return "absent"
                except OSError:
                    return "unreachable"
                if not stat.S_ISDIR(info.st_mode):
                    return "not-directory"
                fd = os.open(name, _DIR_FLAGS, dir_fd=pfd)
            else:
                fd = os.dup(pfd)
        except OSError:
            return "unreachable"
        finally:
            os.close(pfd)
        try:
            info = os.fstat(fd)
            if info.st_uid != self._owner.uid:
                return "owner"
            if info.st_mode & 0o022:
                return "writable"
            if _forbidden(_xattr_names(fd)):
                return "acl"
            return None
        finally:
            os.close(fd)

    def exists(self, path: str) -> bool | None:
        parent, name = split(path)
        try:
            pfd = open_dir(parent)
        except FileNotFoundError:
            return False
        except OSError:
            return None
        try:
            os.stat(name, dir_fd=pfd, follow_symlinks=False)
            return True
        except FileNotFoundError:
            return False
        except OSError:
            return None
        finally:
            os.close(pfd)

    def read_staged(self, path: str, *, dev: int, ino: int, max_bytes: int) -> bytes | None:
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
                    or (info.st_dev, info.st_ino) != (dev, ino)
                    or (info.st_uid, info.st_gid) != (self._owner.uid, self._owner.gid)
                    or info.st_mode & 0o022
                    or info.st_nlink != 1
                    or info.st_size > max_bytes
                ):
                    return None
                data = _read_capped(fd, info.st_size)
                return data if len(data) == info.st_size else None
            finally:
                os.close(fd)
        finally:
            os.close(pfd)

    def create_act_journal(self, directory: str, *, operator_uid: int, run: str) -> EvidenceSink:
        try:
            dfd = open_dir(directory)
        except OSError as exc:
            raise EvidenceWriteError(f"ACT directory: {exc.strerror}") from exc
        try:
            info = os.fstat(dfd)
            if info.st_uid != operator_uid or stat.S_IMODE(info.st_mode) != 0o700:
                raise EvidenceWriteError("ACT directory is not the operator's 0700 directory")
            try:
                jfd = os.open(
                    "journal",
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_APPEND | os.O_NOFOLLOW | os.O_CLOEXEC,
                    0o644,
                    dir_fd=dfd,
                )
            except OSError as exc:
                raise EvidenceWriteError(f"journal: {exc.strerror}") from exc
            try:
                os.fchmod(jfd, 0o644)
                if os.fstat(jfd).st_uid != self._owner.uid:
                    raise EvidenceWriteError("journal has an unexpected owner")
                self._io.fsync(jfd)
                self._io.fsync(dfd)
            except (OSError, EvidenceWriteError) as exc:
                os.close(jfd)
                raise EvidenceWriteError(str(exc)) from exc
        finally:
            os.close(dfd)
        return JournalAppender(jfd, kind=JournalKind.ACT, run=run, io=self._io)
