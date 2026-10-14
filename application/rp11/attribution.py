"""Attribution of an activation object (H-GR1.1, H-GRR.4).

An object found at an activation path is compared with the identity a journal
line (or ``grant.id``) recorded for it. Only ``A1_INTACT`` may be removed, and
only after an immediate descriptor re-verification gives ``A1_INTACT`` again.

* ``A1_INTACT`` — same type and ``(dev, ino)``, uid and gid root, recorded mode,
  one link; a file also has the recorded size and SHA-256 and no forbidden
  extended-attribute name; a directory is also empty when removal needs that.
* ``A1_DAMAGED`` — same type and ``(dev, ino)`` but some other fact differs.
* ``A0`` — anything else at the path: another inode, another type, a symlink,
  or no valid identity at all. Kept and escalated.
* ``ABSENT`` — nothing at the path.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

FORBIDDEN_XATTRS = frozenset(
    {"security.capability", "system.posix_acl_access", "system.posix_acl_default"}
)

# Volume cap for every file re-verified before removal (H-GR1.2, GRR-3).
MAX_VERIFIED_FILE_BYTES = 65_536


class Attribution(str, Enum):
    A1_INTACT = "a1-intact"
    A1_DAMAGED = "a1-damaged"
    A0 = "a0"
    ABSENT = "absent"


class ObjectKind(str, Enum):
    FILE = "file"
    DIR = "dir"
    SYMLINK = "symlink"
    OTHER = "other"


@dataclass(frozen=True)
class Identity:
    """What a durable line (or ``grant.id``) recorded for an object."""

    path: str
    kind: ObjectKind
    dev: int
    ino: int
    mode: int
    sha256: str | None = None  # files only
    size: int | None = None  # files only


@dataclass(frozen=True)
class Observed:
    """What a no-follow lookup or a descriptor re-verification found.

    ``sha256`` is ``None`` when the content was not read (not a regular file, or
    over the volume cap). ``empty`` is ``None`` for anything but a directory that
    was listed.
    """

    kind: ObjectKind
    dev: int
    ino: int
    uid: int
    gid: int
    mode: int
    nlink: int
    size: int
    sha256: str | None = None
    xattr_names: tuple[str, ...] = ()
    empty: bool | None = None

    def facts(self) -> dict[str, object]:
        """Residual facts for a record: metadata and digest, never content."""
        return {
            "type": self.kind.value,
            "uid": self.uid,
            "gid": self.gid,
            "mode": self.mode,
            "size": self.size,
            "dev": self.dev,
            "ino": self.ino,
            "nlink": self.nlink,
            "xattr_names": sorted(self.xattr_names),
            "sha256": self.sha256 or "unreadable",
        }


@dataclass(frozen=True)
class Owner:
    """The uid/gid an attributable object must have: root in production."""

    uid: int = 0
    gid: int = 0


def classify(
    identity: Identity | None,
    observed: Observed | None,
    owner: Owner,
    *,
    require_empty: bool = False,
) -> Attribution:
    if observed is None:
        return Attribution.ABSENT
    if identity is None:
        return Attribution.A0
    if observed.kind is not identity.kind or (observed.dev, observed.ino) != (
        identity.dev,
        identity.ino,
    ):
        return Attribution.A0
    intact = (
        observed.uid == owner.uid
        and observed.gid == owner.gid
        and observed.mode == identity.mode
        and not (set(observed.xattr_names) & FORBIDDEN_XATTRS)
    )
    if identity.kind is ObjectKind.FILE:
        intact = (
            intact
            and observed.nlink == 1
            and observed.size == identity.size
            and observed.size <= MAX_VERIFIED_FILE_BYTES
            and observed.sha256 is not None
            and observed.sha256 == identity.sha256
        )
    elif require_empty:
        intact = intact and observed.empty is True
    return Attribution.A1_INTACT if intact else Attribution.A1_DAMAGED
