"""What the journals of one activation let cleanup attribute and claim (CL-1).

``ActEvidence`` is derived from the ``ACT`` journal only; ``PriorRemovals`` from
earlier CL attempt journals and the consume journal. Both are monotone: a lost,
torn or invalid line can only shrink what may be removed or claimed (H-JRN.9).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from .attribution import Identity, ObjectKind
from .canonical import ABSENT
from .journal import JournalLine, ParsedJournal


@dataclass(frozen=True)
class TreeEvidence:
    parent: str
    top: str
    temp: str
    tag: str
    linked: bool
    directories: tuple[Identity, ...]  # top first, then members in pre-order

    @property
    def top_path(self) -> str:
        return _join(self.parent, self.top)


@dataclass(frozen=True)
class ActEvidence:
    """Identities and facts the ``ACT`` journal makes durable.

    ``valid`` false means the journal was missing or invalid: nothing at an
    activation path is attributable (every object is A0).
    """

    valid: bool
    boot_id: str = ""
    a2_sha256: str = ""
    pass_config_sha256: str = ""
    staged_rule_sha256: str = ""
    lock: Identity | None = None
    files: dict[str, Identity] = field(default_factory=dict)  # linked or not: by final path
    linked_files: frozenset[str] = frozenset()
    grant_paths: frozenset[str] = frozenset()
    trees: tuple[TreeEvidence, ...] = ()
    igr_removed: bool = False
    positive_control: bool = False
    capture_tau0: int | None = None
    hold_end_reason: str = ABSENT
    holder_invocation_id: str = ABSENT

    def file(self, path: str) -> Identity | None:
        return self.files.get(path) if self.valid else None

    def directory(self, path: str) -> Identity | None:
        if not self.valid:
            return None
        for tree in self.trees:
            if not tree.linked:
                continue
            for identity in tree.directories:
                if identity.path == path:
                    return identity
        return None

    def temp_names(self) -> tuple[tuple[str, str], ...]:
        """``(parent, temporary name)`` of every tree: S0 if found (never removed)."""
        return tuple((tree.parent, tree.temp) for tree in self.trees)


INVALID_ACT = ActEvidence(valid=False)


def _join(parent: str, name: str) -> str:
    return parent.rstrip("/") + "/" + name if parent != "/" else "/" + name


def act_evidence(parsed: ParsedJournal | None) -> ActEvidence:
    if parsed is None or not parsed.valid:
        return INVALID_ACT
    start = parsed.lines[0].fields
    intents: dict[str, dict] = {}
    files: dict[str, Identity] = {}
    linked: set[str] = set()
    grants: set[str] = set()
    trees: list[TreeEvidence] = []
    current: dict | None = None
    igr_removed = False
    positive = False
    hold_end = ABSENT
    for line in parsed.lines[1:]:
        f = line.fields
        if line.op == "file-intent":
            intents[_join(f["dir"], f["name"])] = dict(f)
        elif line.op == "file-identity":
            path = _join(f["dir"], f["name"])
            intent = intents.get(path)
            if intent is not None and path not in files:
                files[path] = Identity(
                    path=path,
                    kind=ObjectKind.FILE,
                    dev=f["dev"],
                    ino=f["ino"],
                    mode=intent["mode"],
                    sha256=intent["sha256"],
                    size=intent["size"],
                )
                if intent["grant"]:
                    grants.add(path)
        elif line.op == "file-linked":
            path = _join(f["dir"], f["name"])
            if path in files:
                linked.add(path)
        elif line.op == "tree-intent":
            if current is not None:
                trees.append(_tree(current))
            modes = {m["rel"]: m["mode"] for m in f["members"] if m["kind"] == "dir"}
            current = {"intent": dict(f), "modes": modes, "dirs": [], "linked": False}
        elif line.op == "dir-identity" and current is not None:
            rel = f["rel"]
            mode = current["modes"].get(rel)
            if mode is not None:
                top = _join(current["intent"]["parent"], current["intent"]["top"])
                path = top if rel == "." else _join(top, rel)
                current["dirs"].append(
                    Identity(path=path, kind=ObjectKind.DIR, dev=f["dev"], ino=f["ino"], mode=mode)
                )
        elif line.op == "tree-linked" and current is not None:
            intent = current["intent"]
            if (f["parent"], f["top"]) == (intent["parent"], intent["top"]):
                current["linked"] = True
        elif line.op == "igr":
            # Only a removal of the very grant this journal identified counts.
            igr_removed = igr_removed or (
                f["outcome"] == "removed" and _is_journaled_grant(f["identity"], files, grants)
            )
        elif line.op == "grant-check":
            if f["verb"] == "start" and f["outcome"] == "authorized":
                positive = True
        elif line.op == "hold-end":
            hold_end = f["reason"]
    if current is not None:
        trees.append(_tree(current))
    lock = start["lock"]["object"]
    return ActEvidence(
        valid=True,
        boot_id=start["boot_id"],
        a2_sha256=start["a2_sha256"],
        pass_config_sha256=start["pass_config_sha256"],
        staged_rule_sha256=start["staged_rule_sha256"],
        lock=Identity(lock["path"], ObjectKind.DIR, lock["dev"], lock["ino"], 0o700),
        files=files,
        linked_files=frozenset(linked),
        grant_paths=frozenset(grants),
        trees=tuple(trees),
        igr_removed=igr_removed,
        positive_control=positive,
        capture_tau0=start["capture"]["inactive_enter_us"],
        hold_end_reason=hold_end,
        holder_invocation_id=start["holder_invocation_id"],
    )


def _is_journaled_grant(identity: object, files: dict[str, Identity], grants: set[str]) -> bool:
    """``igr.identity`` names exactly a grant file whose identity lines precede it."""
    if identity == ABSENT or identity["path"] not in grants:
        return False
    known = files[identity["path"]]
    return (known.dev, known.ino, known.sha256, known.size, known.mode) == (
        identity["dev"],
        identity["ino"],
        identity["sha256"],
        identity["size"],
        identity["mode"],
    )


def _tree(state: dict) -> TreeEvidence:
    intent = state["intent"]
    return TreeEvidence(
        parent=intent["parent"],
        top=intent["top"],
        temp=intent["temp"],
        tag=intent["tag"],
        linked=state["linked"],
        directories=tuple(state["dirs"]),
    )


@dataclass(frozen=True)
class PriorRemovals:
    """Paths an earlier attempt or CP durably journaled as ``removed``."""

    paths: frozenset[str] = frozenset()

    @classmethod
    def from_journals(cls, journals: Iterable[ParsedJournal]) -> PriorRemovals:
        removed: set[str] = set()
        for parsed in journals:
            if parsed.valid:
                removed.update(_removed(parsed.lines))
        return cls(frozenset(removed))


def _removed(lines: Iterable[JournalLine]) -> set[str]:
    return {line.fields["path"] for line in lines if line.op == "removed"}
