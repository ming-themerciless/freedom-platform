"""RT-5 ``attest`` across a real kernel reboot of the disposable host.

Three explicit phases, selected by ``FREEDOM_ATTEST_REBOOT_PHASE``; without it every test
here is skipped (so the whole ``tests/systemd_integration`` suite still runs serially and
reports the reason). The reboot itself is the operator's step between ``prepare`` and
``verify``; only the disposable host is rebooted.

    # 1. build the artifact, install the tmpfiles.d prerequisite, create three synthetic
    #    activations (one with a live grant that only the kernel boot will clear)
    sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_RP11_WHEEL=<wheel> \\
        FREEDOM_ATTEST_REBOOT_PHASE=prepare \\
        /opt/freedom-blades/runtime/venv-web/bin/python -B -m pytest -q -rfEs \\
        tests/systemd_integration/test_route3_attest_reboot_host.py
    # 2. sudo systemctl reboot            (then wait for ssh)
    # 3. attest through the exact ``sudo -n`` vector, in the new boot
    sudo env FREEDOM_SYSTEMD_INTEGRATION=oracle-test FREEDOM_RP11_WHEEL=<wheel> \\
        FREEDOM_ATTEST_REBOOT_PHASE=verify ... (same command)
    # 4. remove everything this proof created
    sudo env ... FREEDOM_ATTEST_REBOOT_PHASE=cleanup ... (same command)

Activation A has the full live object set at the reboot. Activations B and C share its fixed
``/run`` paths, so their objects are removed (as the boot would) before A is created; their
durable ACT evidence stays. After the boot:

* A: ``cleared-by-boot`` for the rule, pass config and directories, ``st1-verified`` only after
  the real CL-4 (Polkit says not authorized) and CL-6 (baseline) checks;
* B: an authorizing rule is planted at the rule path in the new boot. It is an A0 object: kept,
  not removed because the boot changed; Polkit still authorizes the operator, so neither
  ``cleared-by-boot`` nor ``st1-verified`` is claimed for the rule;
* C: its durable identity line is removed, so ``cleared-by-boot`` cannot be claimed and the
  attestation hard-stops (exit 1, ``invalid-journal``), whatever Polkit and the baseline say.

* F, G and H: tree P's intent and link are present and the chain is canonical, but the pass-a.json
  member digest differs (F), an undeclared ``dir-identity`` follows the real one (G), or the top
  directory member is declared twice (H). The same hard-stop, ``st1-not-verified``, never success.

* D and E: the ACT journal is rebuilt canonically with the production serializer (contiguous
  ``seq``, correct ``prev`` chain, structurally valid) but without tree P's ``tree-intent`` (D)
  or its ``tree-linked`` (E). Positive PK/2 and an equal baseline cannot repair it: exit 1,
  ``hard-stop``, tree P ``never-created``, never ``st1-verified``.

A wrong ``/run`` filesystem fact cannot be produced on the real host (the layout is a constant)
and is proved with the engine's injected mount table in ``tests/test_rp11_attest.py``.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PHASE = os.environ.get("FREEDOM_ATTEST_REBOOT_PHASE", "")
if PHASE not in {"prepare", "verify", "cleanup"}:
    pytest.skip(
        "set FREEDOM_ATTEST_REBOOT_PHASE=prepare|verify|cleanup (the real-reboot proof is explicit)",
        allow_module_level=True,
    )

import test_route3_stop_post_host as host  # noqa: E402,F401  (applies the same disposable-host guards)
from test_route3_stop_post_host import (  # noqa: E402
    ARTIFACT_DIR,
    LAYOUT,
    OPERATOR,
    STORE,
    Activation,
    _builder,
    boot_id,
    restart_polkit,
    run,
    show,
    wait_until,
)

from adapters.systemd.manager import ROLE_ARTIFACT, ROLE_INTERPRETER  # noqa: E402
from application.rp11.pk import PkMode, PkOutcome  # noqa: E402
from rp11_fixtures import RULE_BYTES  # noqa: E402
from test_route3_attest_host import attest, attempt_dirs, deact_names  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
STATE = Path("/var/tmp/rp11-attest-reboot-proof.json")
FRAGMENT = Path("/usr/lib/tmpfiles.d/freedom-blades-rp11-polkit-rules.conf")
PROTECTED = sorted(str(p) for p in Path("/var/tmp").glob("p5-r5-rp11-h0*"))
RULES_DIR = Path("/run/polkit-1/rules.d")


def protected_facts() -> dict[str, list]:
    """Name, inode, mode, size and mtime of each protected directory and its direct entries."""
    facts = {}
    for name in PROTECTED:
        base = Path(name)
        entries = sorted(base.iterdir()) if base.is_dir() else []
        facts[name] = [
            [str(p), p.lstat().st_ino, p.lstat().st_mode, p.lstat().st_size, p.lstat().st_mtime_ns]
            for p in [base, *entries]
        ]
    return facts


def tool(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-B", "-m", "tools.polkit_tmpfiles", *args],
                          capture_output=True, text=True, cwd=ROOT)


def wipe_run_objects(act: Activation) -> None:
    """What a boot does to this activation's tmpfs objects (used for B and C only)."""
    for path in (act.paths.rule, act.paths.pass_config, act.paths.grant_id):
        Path(path).unlink(missing_ok=True)
    for path in (act.paths.tree_p, act.paths.lock_dir):
        shutil.rmtree(path, ignore_errors=True)


def rewrite_act(act: Activation, edit) -> None:
    """Rebuild the ACT journal through the production serializer after ``edit`` maps the parsed
    ``[(op, fields)]`` to a new list: contiguous ``seq``, correct ``prev`` chain, structurally valid."""
    from application.rp11.journal import GENESIS, JournalKind, parse_journal, serialize_line

    journal = Path(act.paths.act_dir, "journal")
    parsed = parse_journal(journal.read_bytes(), kind=JournalKind.ACT, run=act.id)
    assert parsed.valid
    out, prev = [], GENESIS
    for op, fields in edit([(line.op, copy.deepcopy(dict(line.fields))) for line in parsed.lines]):
        raw = serialize_line(JournalKind.ACT, seq=len(out) + 1, prev=prev, run=act.id, op=op, fields=fields)
        out.append(raw)
        prev = hashlib.sha256(raw).hexdigest()
    journal.write_bytes(b"".join(out))
    assert parse_journal(journal.read_bytes(), kind=JournalKind.ACT, run=act.id).valid


def _tree_p(lines, op):
    tag, found = None, []
    for i, (name, fields) in enumerate(lines):
        if name == "tree-intent":
            tag = fields["tag"]
        if name == op and tag == "p":
            found.append(i)
    assert len(found) == 1, (op, found)
    return found[0]


def drop_tree_p_line(act: Activation, op: str) -> None:
    """Without tree P's ``op`` line."""

    def edit(lines):
        index = _tree_p(lines, op)
        return lines[:index] + lines[index + 1 :]

    rewrite_act(act, edit)


def _intent_member(change):
    def edit(lines):
        change(lines[_tree_p(lines, "tree-intent")][1]["members"])
        return lines

    return edit


def _extra_identity(lines):
    index = _tree_p(lines, "dir-identity")
    return lines[: index + 1] + [("dir-identity", {"rel": "not-declared", "dev": 1, "ino": 2})] + lines[index + 1 :]


# Canonical, correctly chained, semantically inexact tree-P histories (the lossy-projection cases).
INCONSISTENT = {
    "F": _intent_member(lambda m: m[1].update(sha256="ab" * 32)),
    "G": _extra_identity,
    "H": _intent_member(lambda m: m.insert(1, dict(m[0]))),
}


def act_from(entry: dict) -> Activation:
    act = Activation()
    act.id = entry["id"]
    from application.rp11.paths import ActivationPaths

    act.paths = ActivationPaths(LAYOUT, act.id)
    return act


# ---------------------------------------------------------------------------
# phase 1 — before the reboot
# ---------------------------------------------------------------------------


@pytest.mark.skipif(PHASE != "prepare", reason="phase is not 'prepare'")
def test_prepare_the_activations_and_the_prerequisites():
    assert not STATE.exists() and not STORE.exists(), "a previous proof was not cleaned up"
    assert not os.path.lexists("/run/polkit-1") or FRAGMENT.is_file(), "an unexplained /run/polkit-1"
    assert not list(Path("/var/tmp").glob("rp11-act-*")) and len(PROTECTED) == 6, PROTECTED
    wheel = os.environ.get("FREEDOM_RP11_WHEEL")
    assert wheel, "set FREEDOM_RP11_WHEEL"
    shutil.rmtree(ARTIFACT_DIR, ignore_errors=True)
    _builder().build(Path(wheel), ARTIFACT_DIR)  # persists across the reboot; removed by 'cleanup'
    for path in [ARTIFACT_DIR, *ARTIFACT_DIR.rglob("*")]:
        info = path.lstat()
        assert (info.st_uid, info.st_gid) == (0, 0) and not info.st_mode & 0o022, path
    done = tool("install")
    assert done.returncode == 0, (done.stdout, done.stderr)
    created = run("systemd-tmpfiles", "--create", str(FRAGMENT))
    assert created.returncode == 0, created.stderr
    entries = {}
    for label in ("B", "C", "D", "E", "F", "G", "H", "A"):
        act = Activation()
        act.prepare()  # live grant, positive control with the real PK/2
        if label != "A":
            wipe_run_objects(act)
        if label in {"D", "E"}:  # structurally valid, semantically incomplete tree-P history
            drop_tree_p_line(act, "tree-intent" if label == "D" else "tree-linked")
        if label in INCONSISTENT:  # present and canonical, but not the production tree-P shape
            rewrite_act(act, INCONSISTENT[label])
        entries[label] = {"id": act.id, "a2": act.fx.a2_sha256}
    STATE.write_text(json.dumps({"boot_id": boot_id(), "activations": entries, "protected": protected_facts()}))
    os.chmod(STATE, 0o600)
    live = act_from(entries["A"]).paths
    for path in (live.rule, live.pass_config, live.tree_p, live.grant_id, live.lock_dir):
        assert os.path.lexists(path), path
    assert show("polkit.service", "ActiveState")["ActiveState"] == "active"
    print("PREPARED", json.dumps(entries))


# ---------------------------------------------------------------------------
# phase 2 — after the reboot
# ---------------------------------------------------------------------------


def _doc(act: Activation, k: int) -> dict:
    return act.record(k)


@pytest.fixture
def after_reboot():
    state = json.loads(STATE.read_text())
    assert state["boot_id"] != boot_id(), "the host has not been rebooted since 'prepare'"
    assert protected_facts() == state["protected"], "a protected pre-existing directory changed"
    assert show("polkit.service", "ActiveState")["ActiveState"] == "active"
    assert RULES_DIR.is_dir(), "the tmpfiles.d fragment did not make the rules directory at boot"
    yield state
    assert protected_facts() == state["protected"]


@pytest.mark.skipif(PHASE != "verify", reason="phase is not 'verify'")
def test_the_boot_cleared_the_runtime_objects_and_kept_the_evidence(after_reboot):
    state = after_reboot
    for label, entry in state["activations"].items():
        act = act_from(entry)
        for path in (act.paths.rule, act.paths.pass_config, act.paths.tree_p, act.paths.grant_id, act.paths.lock_dir):
            assert not os.path.lexists(path), (label, path)
        assert Path(act.paths.act_dir, "journal").is_file(), label
        assert (STORE / "activation").is_dir()
    assert deact_names(act_from(state["activations"]["A"])) == []


@pytest.mark.skipif(PHASE != "verify", reason="phase is not 'verify'")
def test_c_without_its_identity_line_cannot_claim_cleared_by_boot(after_reboot):
    """Run first: C's durable identity line is removed, so nothing about its absent objects can
    be proved to have been cleared by the boot (CL-1 condition 3)."""
    entry = after_reboot["activations"]["C"]
    act = act_from(entry)
    shutil.rmtree(act.paths.act_dir)
    done = attest_for(entry)
    assert done.returncode == 1, done.stderr  # hard-stop: never st1-verified, never exit 0
    lines = done.stderr.strip().splitlines()
    assert lines[-1].startswith(f"rp11-cl hard-stop {act.id} k=1 ") and lines[-1].endswith("failure=invalid-journal")
    doc = host_record(act, 1)
    assert doc["trigger"] == "attest" and doc["boot"]["act_boot"] == "absent"
    assert doc["outcome"] == "hard-stop" and doc["st1"]["verified"] is False
    assert doc["failure"]["class"] == "invalid-journal"
    assert "cleared-by-boot" not in json.dumps(doc) and "st1-verified" not in json.dumps(doc["st1"])
    assert doc["active_rule"]["class"] in {"never-linked", "absent-before-removal"}
    assert doc["pk"]["mode"] == "seek-not-authorized"


@pytest.mark.skipif(PHASE != "verify", reason="phase is not 'verify'")
@pytest.mark.parametrize("label", ["D", "E"])
def test_d_e_a_valid_chain_without_tree_p_intent_or_link_is_never_st1_verified(after_reboot, label):
    """The journal parses and chains; only the mandatory tree-P fact is missing. The installed
    ``sudo -n`` vector, a positive PK/2 not-authorized and an equal baseline still hard-stop."""
    from application.rp11.journal import JournalKind, parse_journal

    entry = after_reboot["activations"][label]
    act = act_from(entry)
    assert parse_journal(Path(act.paths.act_dir, "journal").read_bytes(), kind=JournalKind.ACT, run=act.id).valid
    done = attest_for(entry)
    assert done.returncode == 1, done.stderr
    last = done.stderr.strip().splitlines()[-1]
    assert last.startswith(f"rp11-cl hard-stop {act.id} k=1 ") and "st1-verified" not in last
    doc = host_record(act, 1)
    assert doc["outcome"] == "hard-stop" and doc["st1"]["verified"] is False
    assert doc["pk"]["outcome"] == "not-authorized" and doc["st1"]["checks"]["pk-not-authorized"]
    assert doc["st1"]["checks"]["baseline-equal"]
    assert {d["role"]: d["class"] for d in doc["directories"]}["tree-p"] == "never-created"
    assert doc["failure"]["class"] == "st1-not-verified"
    assert "st1-verified" not in json.dumps(doc["st1"]) and doc["outcome"] != "st1-verified"


@pytest.mark.skipif(PHASE != "verify", reason="phase is not 'verify'")
@pytest.mark.parametrize("label", sorted(INCONSISTENT))
def test_f_g_h_a_valid_chain_with_an_inexact_tree_p_history_is_never_st1_verified(after_reboot, label):
    """Intent and link are present and the chain parses; only the exact production member fields or
    identity history differ. Positive PK/2 and an equal baseline cannot repair it."""
    from application.rp11.journal import JournalKind, parse_journal

    entry = after_reboot["activations"][label]
    act = act_from(entry)
    assert parse_journal(Path(act.paths.act_dir, "journal").read_bytes(), kind=JournalKind.ACT, run=act.id).valid
    done = attest_for(entry)
    assert done.returncode == 1, done.stderr
    last = done.stderr.strip().splitlines()[-1]
    assert last.startswith(f"rp11-cl hard-stop {act.id} k=1 ") and "st1-verified" not in last
    doc = host_record(act, 1)
    assert doc["outcome"] == "hard-stop" and doc["st1"]["verified"] is False
    assert doc["pk"]["outcome"] == "not-authorized" and doc["st1"]["checks"]["pk-not-authorized"]
    assert doc["st1"]["checks"]["baseline-equal"]
    assert doc["failure"]["class"] == "st1-not-verified"
    assert "st1-verified" not in json.dumps(doc["st1"]) and doc["outcome"] != "st1-verified"


@pytest.mark.skipif(PHASE != "verify", reason="phase is not 'verify'")
def test_b_a_planted_pathname_is_kept_and_polkit_still_authorizing_is_never_success(after_reboot):
    """CL-1 boot scoping: an object found under ``/run`` from the old activation is A0 and is
    removed by nothing merely because the boot changed; the operator is authorized by it, so the
    real CL-4 series is not 'not authorized'."""
    entry = after_reboot["activations"]["B"]
    act = act_from(entry)
    planted = Path(act.paths.rule)
    planted.write_bytes(RULE_BYTES % b"ubuntu")
    os.chmod(planted, 0o644)
    try:
        assert wait_until(lambda: authorized(entry), 15), "polkitd did not pick up the planted rule"
        before = planted.lstat()
        done = attest_for(entry)
        assert done.returncode == 1, done.stderr
        assert planted.exists() and planted.lstat().st_ino == before.st_ino  # A0: kept, never removed
        doc = host_record(act, 1)
        assert doc["trigger"] == "attest" and doc["outcome"] == "hard-stop" and doc["st1"]["verified"] is False
        assert doc["active_rule"]["class"] == "present-foreign-unremoved"
        assert doc["grant_identity"]["cl_g"] == "identity-unavailable"
        assert doc["pk"]["outcome"] == "unconfirmed" and doc["pk"]["reason"] == "still-authorized"
        assert doc["boot"]["act_boot"] != doc["boot"]["observed_at_start"]
        assert "cleared-by-boot" not in json.dumps(doc["active_rule"])
    finally:
        planted.unlink(missing_ok=True)
    assert wait_until(lambda: not authorized(entry), 15), "polkitd still authorizes after the rule was removed"


@pytest.mark.skipif(PHASE != "verify", reason="phase is not 'verify'")
def test_a_the_exact_sudo_vector_records_cleared_by_boot_and_st1_verified(after_reboot):
    """RT5.PRE.2 / RT5.CL1: a different boot id, ``/run`` observed as tmpfs, a valid old identity
    line and ENOENT; ``st1-verified`` only after the real PK/2 not-authorized and baseline checks."""
    state = after_reboot
    entry = state["activations"]["A"]
    act = act_from(entry)
    polkit_before = show("polkit.service", "MainPID")["MainPID"]
    done = attest_for(entry)
    assert done.returncode == 0, done.stderr
    lines = done.stderr.strip().splitlines()
    assert lines[-1].startswith(f"rp11-cl st1-verified {act.id} k=1 rule=cleared-by-boot pk=not-authorized"), lines
    assert "pass_config=cleared-by-boot" in lines[-1] and "Traceback" not in done.stderr
    doc = host_record(act, 1)
    assert doc["outcome"] == "st1-verified" and doc["trigger"] == "attest" and doc["helper"]["role"] == "attest"
    assert doc["active_rule"]["class"] == "cleared-by-boot" and doc["pass_config"]["class"] == "cleared-by-boot"
    assert doc["boot"]["run_fstype"] == "tmpfs"
    assert doc["boot"]["act_boot"] == state["boot_id"] != doc["boot"]["observed_at_start"] == boot_id()
    assert [d["class"] for d in doc["directories"]] == ["cleared-by-boot", "pre-existing-kept", "cleared-by-boot"] or all(
        d["class"] in {"cleared-by-boot", "pre-existing-kept"} for d in doc["directories"]
    )
    assert doc["pk"]["outcome"] == "not-authorized" and doc["st1"]["checks"]["pk-not-authorized"]
    assert doc["st1"]["checks"]["baseline-equal"] and doc["st1"]["verified"]
    assert doc["children"]["entries"] and all(c["reaped"] for c in doc["children"]["entries"])
    assert show("polkit.service", "MainPID")["MainPID"] == polkit_before
    assert not any(os.path.lexists(p) for p in (act.paths.rule, act.paths.pass_config, act.paths.tree_p))
    assert not authorized(entry)


# ---------------------------------------------------------------------------
# phase 3 — remove everything this proof created
# ---------------------------------------------------------------------------


@pytest.mark.skipif(PHASE != "cleanup", reason="phase is not 'cleanup'")
def test_cleanup_removes_every_proof_artifact():
    state = json.loads(STATE.read_text()) if STATE.exists() else {"activations": {}, "protected": None}
    for entry in state["activations"].values():
        act = act_from(entry)
        for path in (act.paths.tree_p, act.paths.lock_dir):
            shutil.rmtree(path, ignore_errors=True)
        Path(act.paths.rule).unlink(missing_ok=True)
        for leftover in Path("/var/tmp").glob(f"{act.id}-*"):
            shutil.rmtree(leftover, ignore_errors=True)
        for temp in Path("/run").glob(f".rp11-{act.id}-*"):
            shutil.rmtree(temp, ignore_errors=True)
    shutil.rmtree(STORE, ignore_errors=True)
    shutil.rmtree(ARTIFACT_DIR, ignore_errors=True)
    assert not ARTIFACT_DIR.exists() and not list(ARTIFACT_DIR.parent.glob(f".{ARTIFACT_DIR.name}.*"))
    if FRAGMENT.is_file():
        done = tool("remove")
        assert done.returncode == 0, (done.stdout, done.stderr)
    shutil.rmtree("/run/polkit-1", ignore_errors=True)
    restart_polkit()  # harness teardown only, as every Route 3 host fixture does
    STATE.unlink(missing_ok=True)
    assert not FRAGMENT.exists() and not STORE.exists() and not os.path.lexists("/run/polkit-1")
    assert not list(Path("/var/tmp").glob("rp11-act-*")) and not STATE.exists()
    assert host.rp11_processes() == []
    assert run("systemctl", "list-units", "rp11-act-*", "--all", "--no-legend").stdout.strip() == ""
    assert run("systemctl", "is-active", "polkit.service").stdout.strip() == "active"
    info = Path("/var/tmp").lstat()
    assert (info.st_uid, info.st_gid, info.st_mode & 0o7777) == (0, 0, 0o1777)
    if state["protected"] is not None:
        assert protected_facts() == state["protected"]
    assert len(PROTECTED) == 6


# --- helpers needing the state ---------------------------------------------------------------


class _Fx:
    def __init__(self, a2: str) -> None:
        self.a2_sha256 = a2


def attest_for(entry: dict) -> subprocess.CompletedProcess:
    act = act_from(entry)
    act.fx = _Fx(entry["a2"])
    return attest(act)


def host_record(act: Activation, k: int) -> dict:
    return act.record(k)


def authorized(entry: dict) -> bool:
    """The real operator ``start``-authorization probe (PK/2 first-decisive series)."""
    from adapters.rp11.baseline import HostBaseline
    from adapters.rp11.process import SystemClock
    from adapters.rp11.stop_post import StopPostServices
    from adapters.systemd.jeepney_bus import connect_system_bus
    from application.rp11.authority import Operator
    from application.unit_control import UnitVerb
    from test_route3_stop_post_host import PARAMS

    services = StopPostServices(connect_system_bus, SystemClock())
    baseline = HostBaseline(services.units(PARAMS)).recompute()
    operator = Operator.from_baseline(baseline)
    return services.pk(PARAMS).run(operator, UnitVerb.START, PkMode.FIRST_DECISIVE).outcome is PkOutcome.AUTHORIZED
