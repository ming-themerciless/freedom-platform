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
* ``UNINSPECTED`` — the object is present but the inspection did not establish
  what it is: a failed ``fstat``, content read or attribute listing leaves
  neither "intact" nor "damaged" nor "foreign" proven. It is never removed and
  never inferred to be damaged or foreign; a later attempt inspects again.
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

UNLISTABLE = "unlistable"  # the extended-attribute names could not be listed
UNREACHABLE_UID = 0xFFFFFFFF  # the owner of an object that could not be looked up at all


class Attribution(str, Enum):
    A1_INTACT = "a1-intact"
    A1_DAMAGED = "a1-damaged"
    A0 = "a0"
    UNINSPECTED = "uninspected"
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


def _unreachable(observed: Observed) -> bool:
    """The placeholder for an object that is present but could not be looked up."""
    return (observed.dev, observed.ino) == (0, 0) and observed.uid == UNREACHABLE_UID


def observation_incomplete(observed: Observed) -> bool:
    """True when a fact that classification needs was not established: the object
    could not be looked up or described, its attribute names could not be listed,
    or a file within the volume cap has no content digest."""
    if _unreachable(observed):
        return True
    if UNLISTABLE in observed.xattr_names:
        return True
    return (
        observed.kind is ObjectKind.FILE
        and observed.size <= MAX_VERIFIED_FILE_BYTES
        and observed.sha256 is None
    )


def _established_difference(identity: Identity, observed: Observed, owner: Owner) -> bool:
    """A recorded fact of a file that the observation positively contradicts."""
    return (
        (observed.uid, observed.gid) != (owner.uid, owner.gid)
        or observed.mode != identity.mode
        or observed.nlink != 1
        or observed.size != identity.size
        or bool(set(observed.xattr_names) & FORBIDDEN_XATTRS)
        or (observed.sha256 is not None and observed.sha256 != identity.sha256)
    )


def classify_file(identity: Identity | None, observed: Observed | None, owner: Owner) -> Attribution:
    """``classify`` for a file, without inferring from a failed inspection.

    An observation that lacks a needed fact is ``UNINSPECTED`` unless the facts it
    does have already establish that the object is damaged or another object."""
    base = classify(identity, observed, owner)
    if observed is None or identity is None or not observation_incomplete(observed):
        return base
    if _unreachable(observed):
        return Attribution.UNINSPECTED
    if base is Attribution.A0:
        return base  # another inode or type was seen: established, not inferred
    if _established_difference(identity, observed, owner):
        return Attribution.A1_DAMAGED
    return Attribution.UNINSPECTED
