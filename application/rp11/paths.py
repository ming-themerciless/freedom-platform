"""The fixed activation paths (design §4.2.5-R2 (b), R8 §4.5 LD-1 / GI-1).

``Layout`` holds the few roots; production uses the defaults and nothing else
can change them (no environment, no argument). Tests construct a layout under a
temporary directory with the test user as ``owner``.
"""

from __future__ import annotations

from dataclasses import dataclass

from application.unit_control import validate_activation_id

from .attribution import Owner

RULE_NAME = "50-freedom-blades-rp11.rules"
PASS_NAME = "pass-a.json"
GRANT_ID_NAME = "grant.id"
JOURNAL_NAME = "journal"
MAX_ATTEMPTS = 99


@dataclass(frozen=True)
class Layout:
    run: str = "/run"
    var_tmp: str = "/var/tmp"
    store: str = "/var/lib/freedom-blades-rp11"
    owner: Owner = Owner()
    tool: str = "/usr/local/libexec/freedom-blades-rp11/rp11_h1.py"
    boot_id_file: str = "/proc/sys/kernel/random/boot_id"
    mountinfo: str = "/proc/self/mountinfo"
    etc_config: str = "/etc/freedom-blades-rp11"
    # PO-11 (f): every other rules directory polkitd reads; the rule basename must
    # be absent from each at AM-0 (the run-time one is ``ActivationPaths.rules_dir``).
    other_rules_dirs: tuple[str, ...] = (
        "/etc/polkit-1/rules.d",
        "/usr/local/share/polkit-1/rules.d",
        "/usr/share/polkit-1/rules.d",
    )


@dataclass(frozen=True)
class ActivationPaths:
    layout: Layout
    activation_id: str

    def __post_init__(self) -> None:
        validate_activation_id(self.activation_id)

    # /run objects
    @property
    def rules_dir(self) -> str:
        return f"{self.layout.run}/polkit-1/rules.d"

    @property
    def polkit_run_dir(self) -> str:
        return f"{self.layout.run}/polkit-1"

    @property
    def rule(self) -> str:
        return f"{self.rules_dir}/{RULE_NAME}"

    @property
    def tree_p(self) -> str:
        return f"{self.layout.run}/freedom-blades-rp11"

    @property
    def pass_config(self) -> str:
        return f"{self.tree_p}/{PASS_NAME}"

    @property
    def lock_dir(self) -> str:
        return f"{self.layout.run}/freedom-blades-rp11-lock-{self.activation_id}"

    @property
    def nextroot(self) -> str:
        return f"{self.layout.run}/nextroot"

    @property
    def grant_id(self) -> str:
        return f"{self.lock_dir}/{GRANT_ID_NAME}"

    # evidence (ext4)
    @property
    def act_dir(self) -> str:
        return f"{self.layout.var_tmp}/{self.activation_id}-act-evidence"

    @property
    def consume_dir(self) -> str:
        return f"{self.layout.var_tmp}/{self.activation_id}-consume-evidence"

    @property
    def attempt_prefix(self) -> str:
        return f"{self.activation_id}-deact-"

    def attempt_dir(self, k: int) -> str:
        if type(k) is not int or not 1 <= k <= MAX_ATTEMPTS:
            raise ValueError("attempt number outside 1..99")
        return f"{self.layout.var_tmp}/{self.activation_id}-deact-{k}-evidence"

    # records and authority
    @property
    def record_dir(self) -> str:
        return f"{self.layout.store}/activation"

    @property
    def staged_rule(self) -> str:
        """The staged rule AM-1G reads by the ``(dev, ino)`` A-2 pins (tree L)."""
        return f"{self.layout.store}/staged/{self.activation_id}.rules"

    def a2_file(self, a2_sha256: str) -> str:
        return f"{self.layout.store}/a2/{a2_sha256}.json"

    def h1_file(self, record_id: str) -> str:
        return f"{self.layout.store}/h1/{record_id}.json"

    def act_record_name(self) -> str:
        return f"{self.activation_id}.act.json"

    def deact_record_name(self, k: int) -> str:
        self.attempt_dir(k)
        return f"{self.activation_id}.deact-{k}.json"
