"""Synthetic RP-11 activations for the cleanup tests (local and disposable host).

Builds, under a ``Layout``, the state a holder would leave: the A-2 and H-1
files, K with ``grant.id``, tree P with ``pass-a.json``, the rules directory
(pre-existing or tree R) with the active rule, and an ``ACT`` journal written
with the production ``JournalAppender`` whose identity lines record the real
``(dev, ino)`` of those objects. No real secret or player data is involved:
every byte is generated here.

Objects are created directly, not by protocols PF/PT; only their journaled
identities matter to cleanup. ``write_authority`` also stages the rule at
``ActivationPaths.staged_rule`` (root ``0444``) so A-2 can pin its ``(dev, ino)``;
the ``hold`` tests start from that state and let the real holder build the rest.

A-2's ``helper.tool_sha256`` is the digest of the installed ``Layout.tool`` when
it exists (the holder verifies it), else a synthetic digest; ``h2_record_sha256``
and ``helper.image_sha256`` are synthetic pins.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path

from adapters.rp11.fsops import FileIO, JournalAppender
from application.rp11.authority import A2_SCHEMA, AUTHORITY_LIMIT, H1_SCHEMA, Params
from application.rp11.baseline import baseline_sha256
from application.rp11.canonical import canonical_bytes
from application.rp11.journal import JournalKind
from application.rp11.paths import ActivationPaths, Layout

RULE_BYTES = b"""// rp11 synthetic test rule
polkit.addRule(function(action, subject) {
    if (action.id == "org.freedesktop.systemd1.manage-units" &&
        action.lookup("unit") == "rp11-capture-pass-a.service" &&
        action.lookup("verb") == "start" &&
        subject.user == "%s") {
        return polkit.Result.YES;
    }
});
"""
PASS_DOC = {"schema": "rp11-pass-a/1", "capture_root": "/var/tmp/rp11-synthetic-capture"}
LEASE = {
    "start_window_s": 60,
    "lease_s": 900,
    "poll_ms": 500,
    "stop_timeout_s": 120,
    "backstop_period_s": 60,
    "bs_runtime_s": 120,
}
H2_RECORD_SHA256 = hashlib.sha256(b"rp11 synthetic H-2 record").hexdigest()
IMAGE_SHA256 = (hashlib.sha256(b"rp11 synthetic interpreter image").hexdigest(),)
SYNTHETIC_TOOL_SHA256 = hashlib.sha256(b"rp11 synthetic tool").hexdigest()


def write_root(path: Path, data: bytes, mode: int) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(fd, data)
        os.fchmod(fd, mode)
    finally:
        os.close(fd)


@dataclass
class ActivationFixture:
    layout: Layout
    activation_id: str
    boot_id: str
    baseline: dict
    operator_user: str = "ubuntu"
    params: Params = field(default_factory=lambda: Params(pk_op_ms=5_000, lock_wait_ms=1_000))
    rules_dir_preexists: bool = True
    a2_sha256: str = ""
    rule_bytes: bytes = b""
    paths: ActivationPaths | None = None
    pass_doc: dict = field(default_factory=lambda: dict(PASS_DOC))

    def __post_init__(self) -> None:
        self.paths = ActivationPaths(self.layout, self.activation_id)
        self.rule_bytes = RULE_BYTES % self.operator_user.encode()
        self.pass_bytes = canonical_bytes(self.pass_doc)

    @property
    def tool_sha256(self) -> str:
        tool = Path(self.layout.tool)
        return hashlib.sha256(tool.read_bytes()).hexdigest() if tool.is_file() else SYNTHETIC_TOOL_SHA256

    def helper(self, role: str | None = None) -> dict:
        doc = {"image_sha256": list(IMAGE_SHA256), "tool_sha256": self.tool_sha256}
        return doc if role is None else {"role": role, **doc}

    # --- authority -----------------------------------------------------------

    def write_authority(self, *, lease: dict | None = None) -> str:
        store = Path(self.layout.store)
        for sub in ("", "a2", "h1", "activation"):
            (store / sub).mkdir(mode=0o755, parents=True, exist_ok=True)
            os.chmod(store / sub, 0o755)
        staged = store / "staged"
        staged.mkdir(mode=0o755, exist_ok=True)
        os.chmod(staged, 0o755)
        staged_rule = Path(self.paths.staged_rule)
        if not staged_rule.exists():
            write_root(staged_rule, self.rule_bytes, 0o444)
        staged_info = os.stat(staged_rule)
        record_id = f"{self.activation_id}-h1"
        h1 = {
            "schema": H1_SCHEMA,
            "record_id": record_id,
            "baseline": self.baseline,
            "baseline_sha256": baseline_sha256(self.baseline),
            "params": self.params.to_doc(),
        }
        h1_bytes = canonical_bytes(h1)
        write_root(store / "h1" / f"{record_id}.json", h1_bytes, 0o444)
        a2 = {
            "schema": A2_SCHEMA,
            "activation_id": self.activation_id,
            "h1_record_id": record_id,
            "h1_record_sha256": hashlib.sha256(h1_bytes).hexdigest(),
            "h2_record_sha256": H2_RECORD_SHA256,
            "helper": self.helper(),
            "boot_id": self.boot_id,
            "pass_config": self.pass_doc,
            "pass_config_sha256": hashlib.sha256(self.pass_bytes).hexdigest(),
            "staged_rule": {"dev": staged_info.st_dev, "ino": staged_info.st_ino},
            "staged_rule_sha256": hashlib.sha256(self.rule_bytes).hexdigest(),
            "lease": lease or dict(LEASE),
            "authority_limit": AUTHORITY_LIMIT,
        }
        a2_bytes = canonical_bytes(a2)
        self.a2_sha256 = hashlib.sha256(a2_bytes).hexdigest()
        write_root(store / "a2" / f"{self.a2_sha256}.json", a2_bytes, 0o444)
        return self.a2_sha256

    # --- activation objects and the ACT journal -----------------------------------

    def activate(
        self,
        *,
        rule: bool = True,
        pass_config: bool = True,
        grant_id: bool = True,
        positive_control: bool = True,
        act_dir_mode: int = 0o700,
        act_dir_uid: int | None = None,
        io: FileIO | None = None,
    ) -> Path:
        """Create the activation and its ACT journal; returns the journal path."""
        p = self.paths
        run = Path(self.layout.run)
        act_dir = Path(p.act_dir)
        act_dir.mkdir(mode=act_dir_mode)
        os.chmod(act_dir, act_dir_mode)
        if act_dir_uid is not None:  # the operator owns the ACT directory (design §4.2.5-R2 (b))
            os.chown(act_dir, act_dir_uid, act_dir_uid)
        jfd = os.open(
            act_dir / "journal", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_APPEND, 0o644
        )
        os.fchmod(jfd, 0o644)
        sink = JournalAppender(jfd, kind=JournalKind.ACT, run=self.activation_id, io=io or FileIO())
        lock_dir = Path(p.lock_dir)
        lock_dir.mkdir(mode=0o700)
        os.chmod(lock_dir, 0o700)
        k = os.stat(lock_dir)
        sink.append(
            "run-start",
            {
                "a2_sha256": self.a2_sha256,
                "h1_record_sha256": self._h1_sha(),
                "h2_record_sha256": H2_RECORD_SHA256,
                "boot_id": self.boot_id,
                "pass_config_sha256": hashlib.sha256(self.pass_bytes).hexdigest(),
                "staged_rule_sha256": hashlib.sha256(self.rule_bytes).hexdigest(),
                "lock": {
                    "object": {"path": str(lock_dir), "dev": k.st_dev, "ino": k.st_ino},
                    "mode": "held",
                    "wait_ms": 0,
                },
                "capture": {
                    "active_state": "inactive",
                    "invocation_id": "absent",
                    "inactive_enter_us": 0,
                    "m_a_us": 1,
                    "bsp_retries": 0,
                },
                "holder_invocation_id": "absent",
                "tool_sha256": self.tool_sha256,
                "helper": self.helper("hold"),
                "lease": dict(LEASE),
                "params": self.params.to_doc(),
            },
        )
        # tree P
        tree_p = Path(p.tree_p)
        sink.append(
            "tree-intent",
            {
                "parent": str(run),
                "top": tree_p.name,
                "temp": f".rp11-{self.activation_id}-p.tmp",
                "tag": "p",
                "members": [
                    {"rel": ".", "kind": "dir", "mode": 0o755},
                    {
                        "rel": "pass-a.json",
                        "kind": "file",
                        "mode": 0o644,
                        "sha256": hashlib.sha256(self.pass_bytes).hexdigest(),
                        "size": len(self.pass_bytes),
                    },
                ],
            },
        )
        tree_p.mkdir(mode=0o755)
        os.chmod(tree_p, 0o755)
        st = os.stat(tree_p)
        sink.append("dir-identity", {"rel": ".", "dev": st.st_dev, "ino": st.st_ino})
        self._publish(sink, tree_p, "pass-a.json", self.pass_bytes, 0o644, grant=False, create=pass_config)
        sink.append("tree-sealed", {"temp": f".rp11-{self.activation_id}-p.tmp", "inventory_sha256": "0" * 64})
        sink.append("tree-linked", {"parent": str(run), "top": tree_p.name})
        # tree R, when the rules directory did not pre-exist
        polkit = Path(p.polkit_run_dir)
        rules = Path(p.rules_dir)
        if self.rules_dir_preexists:
            rules.mkdir(mode=0o755, parents=True, exist_ok=True)
        else:
            top_parent = polkit.parent if not polkit.exists() else polkit
            top = polkit if not polkit.exists() else rules
            members = [{"rel": ".", "kind": "dir", "mode": 0o755}]
            if top == polkit:
                members.append({"rel": "rules.d", "kind": "dir", "mode": 0o755})
            sink.append(
                "tree-intent",
                {
                    "parent": str(top_parent),
                    "top": top.name,
                    "temp": f".rp11-{self.activation_id}-r.tmp",
                    "tag": "r",
                    "members": members,
                },
            )
            top.mkdir(mode=0o755)
            os.chmod(top, 0o755)
            st = os.stat(top)
            sink.append("dir-identity", {"rel": ".", "dev": st.st_dev, "ino": st.st_ino})
            if top == polkit:
                rules.mkdir(mode=0o755)
                os.chmod(rules, 0o755)
                st = os.stat(rules)
                sink.append("dir-identity", {"rel": "rules.d", "dev": st.st_dev, "ino": st.st_ino})
            sink.append("tree-sealed", {"temp": f".rp11-{self.activation_id}-r.tmp", "inventory_sha256": "0" * 64})
            sink.append("tree-linked", {"parent": str(top_parent), "top": top.name})
        # the rule, then grant.id naming its inode (the holder writes grant.id first, AM-1G)
        self._publish(sink, rules, "50-freedom-blades-rp11.rules", self.rule_bytes, 0o644, grant=True, create=rule)
        if grant_id and rule:
            st = os.stat(rules / "50-freedom-blades-rp11.rules")
            identity_line = canonical_bytes(
                {
                    "path": str(rules / "50-freedom-blades-rp11.rules"),
                    "dev": st.st_dev,
                    "ino": st.st_ino,
                    "sha256": hashlib.sha256(self.rule_bytes).hexdigest(),
                    "size": len(self.rule_bytes),
                    "mode": 0o644,
                    "uid": self.layout.owner.uid,
                    "gid": self.layout.owner.gid,
                    "boot_id": self.boot_id,
                }
            )
            self._publish(sink, lock_dir, "grant.id", identity_line, 0o600, grant=False, create=True)
        if positive_control:
            sink.append(
                "grant-check",
                {"verb": "start", "mode": "seek-authorized", "outcome": "authorized", "reason": "decided", "calls": 1},
            )
        sink.append("hold-start", {"capture": {"active_state": "inactive", "inactive_enter_us": 0}})
        sink.append("hold-end", {"reason": "pass-ended", "observation": "absent"})
        sink.close()
        return act_dir / "journal"

    def _publish(self, sink, directory: Path, name: str, data: bytes, mode: int, *, grant: bool, create: bool) -> None:
        sink.append(
            "file-intent",
            {
                "dir": str(directory),
                "name": name,
                "sha256": hashlib.sha256(data).hexdigest(),
                "size": len(data),
                "uid": self.layout.owner.uid,
                "gid": self.layout.owner.gid,
                "mode": mode,
                "grant": grant,
            },
        )
        if not create:
            return
        write_root(directory / name, data, mode)
        st = os.stat(directory / name)
        sink.append("file-identity", {"dir": str(directory), "name": name, "dev": st.st_dev, "ino": st.st_ino})
        sink.append("file-linked", {"dir": str(directory), "name": name})

    def _h1_sha(self) -> str:
        record_id = f"{self.activation_id}-h1"
        return hashlib.sha256((Path(self.layout.store) / "h1" / f"{record_id}.json").read_bytes()).hexdigest()
