"""Protocols the cleanup procedure depends on. Adapters: ``adapters/rp11``.

Each port is a narrow intention, not a filesystem API: paths are the fixed
activation paths of the ``Layout``; every lookup is descriptor-relative and
never follows a final symbolic link (the adapter's obligation, tested there).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from .attribution import Attribution, Identity, Observed


class EvidenceWriteError(Exception):
    """A journal create/append/flush failed: the journal accepts no further line."""


class EvidenceSink(Protocol):
    """The attempt's own journal (H-JRN.2 … H-JRN.7)."""

    def append(self, op: str, fields: dict) -> None:
        """One write of the whole line, then ``fsync``; raises ``EvidenceWriteError``."""
        ...

    def prefix(self) -> tuple[str, int]:
        """SHA-256 and length of everything durably appended so far."""
        ...


class RemovalOutcome(str, Enum):
    REMOVED = "removed"
    ABSENT = "absent"
    MISMATCH = "mismatch"
    UNREMOVABLE = "unremovable"


@dataclass(frozen=True)
class Removal:
    outcome: RemovalOutcome
    attribution: Attribution | None = None
    observed: Observed | None = None
    errno: int = 0


class ActivationFs(Protocol):
    def observe(self, path: str, *, list_dir: bool = False) -> Observed | None:
        """No-follow lookup; ``None`` if absent. Unreadable content gives ``sha256=None``."""
        ...

    def remove(
        self,
        path: str,
        identity: Identity,
        *,
        directory: bool,
        before_unlink: Callable[[Observed], None],
    ) -> Removal:
        """G-R1: re-verify through a descriptor, call ``before_unlink`` (the write-ahead
        line), ``unlinkat``, flush the parent. Removes only an A1-intact object."""
        ...

    def read_root_file(self, path: str, *, max_bytes: int, mode: int) -> bytes | None:
        """A regular, root-owned, one-link file of exactly ``mode``; ``None`` otherwise."""
        ...

    def list_prefixed(self, directory: str, prefix: str) -> tuple[str, ...] | None:
        """Names in ``directory`` that start with ``prefix``; ``None`` if unlistable."""
        ...


class JournalSource(Protocol):
    def read_journal(
        self, directory: str, *, max_bytes: int, dir_uid: int, dir_mode: int
    ) -> bytes | None:
        """``<directory>/journal`` if the directory has that owner and mode and the
        journal is a root-owned regular file within the cap; else ``None``."""
        ...


class AttemptStore(Protocol):
    def create(self, k: int) -> EvidenceSink:
        """Create ``<id>-deact-<k>-evidence/`` exclusively and its journal.

        Raises ``FileExistsError`` for an existing directory (concurrent attempt)
        and ``EvidenceWriteError`` for any other failure."""
        ...


@dataclass(frozen=True)
class Published:
    sha256: str
    length: int


class RecordStore(Protocol):
    def read(self, name: str) -> bytes | None: ...

    def deact_attempts(self, activation_id: str) -> tuple[int, ...] | None:
        """BS-2: the ``k`` of every exact ``<activation_id>.deact-<k>.json`` name
        (``1 <= k <= 99``) in the record directory, ascending; ``None`` if the
        directory cannot be listed descriptor-relatively within its bound."""
        ...

    def publish(self, name: str, data: bytes, sink: EvidenceSink) -> Published:
        """Protocol PF into the record directory (``0444``, no replace), with its
        journal lines in ``sink``, then re-read (PF-9). Raises ``OSError`` or
        ``EvidenceWriteError`` on any failure."""
        ...


class LockMode(str, Enum):
    HELD = "held"
    DEGRADED = "degraded"
    ABSENT = "absent"


@dataclass(frozen=True)
class LockState:
    mode: LockMode
    object: Identity | None
    wait_ms: int


class LockPort(Protocol):
    def acquire(self, deadline_ms: int) -> LockState: ...

    def release(self) -> None: ...


class HostFacts(Protocol):
    def boot_id(self) -> str | None: ...

    def run_fstype(self) -> str | None: ...

    def utc_now(self) -> str: ...


class BaselineSource(Protocol):
    def recompute(self) -> dict | None:
        """The baseline as observed now (same keys as the H-1 record's)."""
        ...


class GuardMode(str, Enum):
    HELD = "held"  # this firing holds the per-activation backstop lock
    BUSY = "busy"  # another firing holds it
    UNAVAILABLE = "unavailable"  # no root-controlled lock/journal could be opened


class BackstopGuard(Protocol):
    """The per-activation backstop lock and its terminal journal (BS-4).

    One root-only file serves both: ``flock`` on it serializes firings of one
    activation from the bound decision to the end of CL, and the terminal line
    is appended to it."""

    def acquire(self) -> GuardMode: ...

    def append_terminal(self, fields: dict) -> None:
        """One canonical line, one write, then ``fsync``; ``EvidenceWriteError`` on
        any failure (including no held journal or the size cap)."""
        ...

    def release(self) -> None: ...


# --- the holder (RT-2) -------------------------------------------------------------


class PublishError(Exception):
    """Protocol PF or PT stopped. ``kind`` is one token:

    * ``preexisting-path`` — PF-1/PT-1: something is at the final or temporary name;
    * ``foreign-rule`` — PF-6/PT-8 ``EEXIST``: a name appeared; it is A0 and kept;
    * ``mismatch`` — PF-4/PF-5/PT-3/PT-7/PF-9/PT-10 verification differs;
    * ``io`` — any other system-call failure;
    * ``rename-unsupported`` — no no-replace rename on this host (refutes PO-20).
    """

    def __init__(self, kind: str, detail: str = "") -> None:
        super().__init__(f"{kind}: {detail}" if detail else kind)
        self.kind = kind


class PreparedFile(Protocol):
    """PF-1 … PF-5 done: an unnamed inode with durable identity and final content."""

    identity: Identity

    def link(self) -> None:
        """PF-6: link under the final name, never replacing (``PublishError``)."""
        ...

    def commit(self, sink: EvidenceSink) -> None:
        """PF-7 parent flush, PF-8 ``file-linked``, PF-9 re-verification."""
        ...

    def discard(self) -> None:
        """Close the descriptor: an unlinked inode is freed with it."""
        ...


@dataclass(frozen=True)
class TreeMember:
    """One member of a PT tree. ``rel`` ``"."`` is the top; files carry ``data``."""

    rel: str
    mode: int
    data: bytes | None = None

    @property
    def is_file(self) -> bool:
        return self.data is not None


class Publisher(Protocol):
    def prepare(
        self, directory: str, name: str, data: bytes, mode: int, *, grant: bool, sink: EvidenceSink
    ) -> PreparedFile: ...

    def publish(
        self, directory: str, name: str, data: bytes, mode: int, *, grant: bool, sink: EvidenceSink
    ) -> Identity:
        """``prepare`` + ``link`` + ``commit``."""
        ...

    def publish_tree(
        self,
        parent: str,
        top: str,
        temp: str,
        tag: str,
        members: tuple[TreeMember, ...],
        sink: EvidenceSink,
    ) -> tuple[Identity, ...]:
        """Protocol PT; the identities of the top and every member, top first."""
        ...


class LockObjectError(Exception):
    """K could not be created, verified or locked (HARD STOP ``lock-object``)."""


class ActivationLock(Protocol):
    """The holder's side of K (H-LK): AM-0 creates and locks it; HL's OS-5 decision
    tries it once without blocking."""

    def create(self) -> Identity: ...

    def try_once(self) -> GuardMode: ...

    def release(self) -> None: ...


class HoldHost(Protocol):
    def directory_problem(self, path: str) -> str | None:
        """``None`` for a real root-owned directory without group/other write and
        without a POSIX ACL; otherwise a token (``absent`` when nothing is there)."""
        ...

    def exists(self, path: str) -> bool | None:
        """A no-follow name lookup only (never opens or lists the object); ``None``
        when the answer cannot be established (an unreachable parent)."""
        ...

    def read_staged(self, path: str, *, dev: int, ino: int, max_bytes: int) -> bytes | None:
        """The staged rule through a no-follow descriptor whose ``(dev, ino)`` match,
        root-owned, one link, within the cap, read once; ``None`` otherwise."""
        ...

    def create_act_journal(self, directory: str, *, operator_uid: int, run: str) -> EvidenceSink:
        """H-JRN.1 … H-JRN.3 for the ACT directory (operator-owned ``0700``): create
        ``journal`` exclusively, flush it and the directory. ``EvidenceWriteError``."""
        ...
