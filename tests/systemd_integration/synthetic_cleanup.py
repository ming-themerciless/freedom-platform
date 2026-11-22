"""Identity-safe removal of the exact synthetic artifacts a host test created; never a recursive delete.

Every object a fixture creates is recorded **at creation** by ``Ledger`` (``st_dev``/``st_ino`` taken from the open
descriptor, plus the expected bytes of a file). Removal then proves, immediately before each unlink, that the object is still
that exact one: a regular file (never a symlink), a single link, the recorded inode and the expected bytes. A directory is
opened with ``O_NOFOLLOW | O_DIRECTORY``, its identity checked on the descriptor, and its recorded children are unlinked
relative to that descriptor, so a directory swapped in afterwards is never entered. The directory itself is then removed
with ``rmdir`` only, so any unexpected entry makes the removal fail loudly and stays in place.

Every helper raises ``AssertionError`` on foreign, replaced or unexpected state and leaves that state untouched.
"""

from __future__ import annotations

import errno
import os
import stat
from pathlib import Path

Identity = tuple[int, int]


def identity(path: Path) -> Identity:
    """``(st_dev, st_ino)`` of ``path`` itself (a symlink is not followed)."""
    info = os.lstat(path)
    return info.st_dev, info.st_ino


def _open_dir(path: Path | str, *, follow: bool = True) -> int:
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | (0 if follow else os.O_NOFOLLOW)
    return os.open(path, flags)


def _unlink_exact_in(dir_fd: int, name: str, shown: Path, *, inode: Identity | None, content: bytes | None,
                     prefix: bytes | None) -> None:
    """Unlink ``name`` below ``dir_fd`` after proving it is the expected regular, single-link file; absent is fine."""
    try:
        info = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    assert stat.S_ISREG(info.st_mode), f"refusing to remove {shown}: not a regular file"
    assert info.st_nlink == 1, f"refusing to remove {shown}: it has {info.st_nlink} links"
    assert inode is None or (info.st_dev, info.st_ino) == inode, f"refusing to remove {shown}: not the file this fixture created"
    if content is not None or prefix is not None:
        try:
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=dir_fd)
        except OSError as error:
            raise AssertionError(f"refusing to remove {shown}: cannot open it safely ({error})") from error
        try:
            opened = os.fstat(fd)
            assert (opened.st_dev, opened.st_ino) == (info.st_dev, info.st_ino), f"refusing to remove {shown}: it changed while checked"
            with os.fdopen(fd, "rb", closefd=False) as handle:
                data = handle.read()
        finally:
            os.close(fd)
        assert content is None or data == content, f"refusing to remove {shown}: content is not the synthetic stand-in"
        assert prefix is None or data.startswith(prefix), f"refusing to remove {shown}: content is not the synthetic stand-in"
    os.unlink(name, dir_fd=dir_fd)


def remove_file_exact(path: Path, *, inode: Identity | None = None, content: bytes | None = None,
                      prefix: bytes | None = None) -> None:
    """Unlink ``path`` only if it is a single-link regular file (never a symlink) matching the recorded ``inode`` and
    ``content``/``prefix``. At least one of ``inode`` and ``prefix`` is required: a bare path proves nothing."""
    if inode is None and prefix is None:
        raise ValueError("remove_file_exact needs the identity recorded at creation or an exact content prefix")
    try:
        dir_fd = _open_dir(path.parent)
    except FileNotFoundError:
        return
    try:
        _unlink_exact_in(dir_fd, path.name, path, inode=inode, content=content, prefix=prefix)
    finally:
        os.close(dir_fd)


def remove_dir_if_ours(path: Path, expected: Identity, *,
                       files: dict[str, tuple[Identity, bytes | None]] | None = None) -> None:
    """Unlink the named ``files`` (each with its recorded identity and optional exact bytes), then ``rmdir`` ``path``.

    ``path`` must be the directory with identity ``expected``; a replaced directory or a symlink is refused before any
    child is touched. An unnamed entry makes ``rmdir`` fail and survives."""
    try:
        dir_fd = _open_dir(path, follow=False)
    except FileNotFoundError:
        return
    except OSError as error:
        if error.errno in (errno.ELOOP, errno.ENOTDIR):
            raise AssertionError(f"refusing to remove {path}: not the directory this fixture created") from error
        raise
    try:
        opened = os.fstat(dir_fd)
        assert (opened.st_dev, opened.st_ino) == expected, f"refusing to remove {path}: not the directory this fixture created"
        for name, (inode, content) in (files or {}).items():
            _unlink_exact_in(dir_fd, name, path / name, inode=inode, content=content, prefix=None)
        assert identity(path) == expected, f"refusing to remove {path}: not the directory this fixture created"
        try:
            os.rmdir(path)
        except OSError as error:
            raise AssertionError(f"unexpected residue left in {path}: {sorted(os.listdir(dir_fd))}") from error
    finally:
        os.close(dir_fd)


class Ledger:
    """Every directory and file a fixture created, with the identity recorded at the moment of creation."""

    def __init__(self) -> None:
        self._dirs: dict[Path, Identity] = {}
        self._files: dict[Path, tuple[Identity, bytes | None]] = {}

    def __contains__(self, path: Path) -> bool:
        return path in self._dirs or path in self._files

    def mkdir(self, path: Path, mode: int = 0o755) -> Identity:
        """Create exactly one new directory (never ``parents``/``exist_ok``) and record its identity at once."""
        assert path not in self._dirs, f"{path} is already recorded"
        os.mkdir(path, 0o700)
        fd = _open_dir(path, follow=False)
        try:
            info = os.fstat(fd)
            self._dirs[path] = (info.st_dev, info.st_ino)
            os.fchmod(fd, mode)
        finally:
            os.close(fd)
        return self._dirs[path]

    def write(self, path: Path, data: bytes, mode: int = 0o644) -> Identity:
        """Create a new file (``O_EXCL``, no symlink) and record identity and bytes before anything is written."""
        assert path not in self._files, f"{path} is already recorded"
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
        try:
            info = os.fstat(fd)
            self._files[path] = ((info.st_dev, info.st_ino), data)
            view = memoryview(data)
            while view:
                view = view[os.write(fd, view):]
            os.fchmod(fd, mode)
        finally:
            os.close(fd)
        return self._files[path][0]

    def replace(self, path: Path, data: bytes, mode: int = 0o644) -> Identity:
        """Remove the file this ledger recorded at ``path`` (verified), then record a new one."""
        self.remove_file(path)
        return self.write(path, data, mode)

    def remove_file(self, path: Path) -> None:
        recorded = self._files.get(path)
        if recorded is None:
            assert not os.path.lexists(path), f"refusing to remove {path}: not created by this run"
            return
        remove_file_exact(path, inode=recorded[0], content=recorded[1])
        del self._files[path]

    def remove_dir(self, path: Path) -> None:
        expected = self._dirs.get(path)
        if expected is None:
            assert not os.path.lexists(path), f"refusing to remove {path}: not created by this run"
            return
        children = {p.name: rec for p, rec in self._files.items() if p.parent == path}
        remove_dir_if_ours(path, expected, files=children)
        for name in children:
            del self._files[path / name]
        del self._dirs[path]

    def remove_all(self) -> list[str]:
        """Remove everything recorded (loose files, then directories deepest first); return the refusals, never raise."""
        problems: list[str] = []

        def attempt(action, target: Path) -> None:
            try:
                action(target)
            except (AssertionError, OSError) as error:
                problems.append(str(error))

        for path in [p for p in self._files if p.parent not in self._dirs]:
            attempt(self.remove_file, path)
        for path in sorted(self._dirs, key=lambda p: len(p.parts), reverse=True):
            attempt(self.remove_dir, path)
        return problems
