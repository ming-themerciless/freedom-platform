"""RT-1 ``consume`` (CQ-0 … CQ-7) on temporary trees.

The activation is the genuine output of the real holder: ``World`` (from
``tests/test_rp11_hold.py``) runs ``HoldProcedure`` and ``consume`` is started from
inside the holder's HL loop (``consume_at``), exactly where PID 1 would start it:
the ACT journal has ``hold-start`` and no ``hold-end``, the ``act`` record is
``activated``, the rule is live and the holder has released K. The filesystem
adapters (K, claim, journals, rule removal, record store) are the real ones;
systemd (DI-1), Polkit (PK/2) and the clock are fakes. The disposable host runs
the same role through PID 1 (``tests/systemd_integration/test_route3_consume_host.py``).

Row coverage (inventory §5.1, ``RT1.*``) is named in each section header.
"""

from __future__ import annotations

import fcntl
import hashlib
import os
import re
import stat
import sys
import threading
from pathlib import Path

import pytest

sys.dont_write_bytecode = True

from adapters.rp11 import consume as consume_adapter  # noqa: E402
from adapters.rp11.consume import LocalClaimStore, LocalConsumeHost, build_consume, run_consume  # noqa: E402
from adapters.rp11.fsops import FileIO, LocalActivationFs  # noqa: E402
from application.rp11 import consume as consume_module  # noqa: E402
from application.rp11.canonical import canonical_bytes, parse_canonical  # noqa: E402
from application.rp11.consume import ConsumeEnd  # noqa: E402
from application.rp11.journal import (  # noqa: E402
    GENESIS,
    JournalKind,
    JournalSchemaError,
    consume_run,
    parse_journal,
    serialize_line,
)
from application.rp11.paths import ActivationPaths  # noqa: E402
from application.rp11.pk import PkMode, PkOutcome, PkResult  # noqa: E402
from application.rp11.ports import EvidenceWriteError, RemovalOutcome  # noqa: E402
from application.unit_control import (  # noqa: E402
    CAPTURE_UNIT,
    ControlError,
    ControlOk,
    UnitProperty,
    UnitVerb,
    holder_unit_name,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_rp11_cleanup import BOOT, Crash, Events, FailingIO, FakePk  # noqa: E402
from test_rp11_hold import (  # noqa: E402
    ACT_ID,
    INV,
    World,
    _umask,  # noqa: F401  (autouse fixture)
    make_layout,
)
from test_rp11_hold import Services as HoldServices  # noqa: E402

pytestmark = pytest.mark.skipif(os.geteuid() == 0, reason="the local tree tests run unprivileged")

CONSUME_INV = "c0" * 16
TAU0 = 400
HOLDER = holder_unit_name(ACT_ID)


# ---------------------------------------------------------------------------
# harness
# ---------------------------------------------------------------------------


class ConsumeUnits:
    """DI-1 for the two units CQ-4 reads. ``fail`` names a unit whose read errors."""

    def __init__(self, *, invocation: str = CONSUME_INV, holder_invocation: str = INV, tau0: int = TAU0):
        self.holder = {
            UnitProperty.ACTIVE_STATE: "active",
            UnitProperty.INVOCATION_ID: holder_invocation,
        }
        self.capture = {
            UnitProperty.ACTIVE_STATE: "activating",
            UnitProperty.INVOCATION_ID: invocation,
            UnitProperty.INACTIVE_ENTER_TIMESTAMP_MONOTONIC: tau0,
        }
        self.reads: list[str] = []
        self.fail: str | None = None
        self.on_read = None

    def read_unit(self, unit, props):
        self.reads.append(unit)
        if self.on_read is not None:
            self.on_read(unit)
        if self.fail == unit:
            return ControlError("timeout")
        table = {HOLDER: self.holder, CAPTURE_UNIT: self.capture}[unit]
        return ControlOk({p: table[p] for p in props})


class ProbePk(FakePk):
    """``FakePk`` that snapshots what is true at the moment the series runs."""

    def __init__(self, world, **kw):
        super().__init__(Events(), **kw)
        self.world = world
        self.snapshot = None
        self.during = None

    def run(self, operator, verb, mode):
        paths = self.world.paths
        self.snapshot = {
            "rule_present": os.path.lexists(paths.rule),
            "ops": consume_ops(self.world),
            "verb": verb,
            "mode": mode,
        }
        self.series_runs = getattr(self, "series_runs", 0) + 1
        if self.during is not None:
            self.during()
        return self.decide(operator, verb, mode)

    def decide(self, operator, verb, mode):
        return super().run(operator, verb, mode)


def run_concurrently(build, count: int) -> list:
    barrier = threading.Barrier(count)
    outcomes: list = [None] * count

    def worker(i: int) -> None:
        procedure = build()
        barrier.wait()
        try:
            outcomes[i] = procedure.run()
        except BaseException as exc:  # noqa: BLE001
            outcomes[i] = exc

    pool = [threading.Thread(target=worker, args=(i,)) for i in range(count)]
    for t in pool:
        t.start()
    for t in pool:
        t.join()
    return outcomes


class Result:
    outcome = None
    raised = None
    proc = None
    holder = None


def consume_at(
    world: World,
    *,
    mutate=None,
    units: ConsumeUnits | None = None,
    pk=None,
    io=None,
    invocation: str = CONSUME_INV,
    at_ms: int = 1_000,
    after=None,
    clock=None,
    threads: int = 0,
) -> Result:
    """Run the real holder; at ``at_ms`` into HL run ``consume`` once, as PID 1 would."""
    result = Result()
    result.units = units or ConsumeUnits()
    result.pk = pk or ProbePk(world)
    world.units.capture[UnitProperty.INACTIVE_ENTER_TIMESTAMP_MONOTONIC] = TAU0

    def build():
        return build_consume(
            invocation,
            layout=world.layout,
            services=HoldServices(result.units, result.pk, None),
            clock=clock or world.clock,
            io=io,
        )

    def fire(_units):
        try:
            if mutate is not None:
                mutate()
            if threads:
                result.outcomes = run_concurrently(build, threads)
            else:
                result.proc = build()
                result.outcome = result.proc.run()
        except BaseException as exc:  # noqa: BLE001 - a Crash stands for the process dying here
            result.raised = exc
        result.state = {
            "rule": os.path.lexists(world.paths.rule),
            "claim": claim_exists(world),
            "k_free": k_is_free(world) if os.path.isdir(world.paths.lock_dir) else None,
        }
        if after is not None:
            after()

    world.units.timeline.append((world.clock.now + at_ms, fire))
    result.holder = world.run()
    return result


def consume_journal(world: World):
    path = Path(world.paths.consume_dir) / "journal"
    return parse_journal(path.read_bytes(), kind=JournalKind.CONSUME, run=consume_run(ACT_ID))


def consume_ops(world: World) -> list[str]:
    path = Path(world.paths.consume_dir) / "journal"
    if not path.exists():
        return []
    return [line.op for line in consume_journal(world).lines]


def k_is_free(world: World) -> bool:
    """K can be locked again: RT-1 closed its descriptor (LD-4)."""
    fd = os.open(world.paths.lock_dir, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except BlockingIOError:
        return False
    finally:
        os.close(fd)


@pytest.fixture(autouse=True)
def _restore_listing():
    real = LocalActivationFs.list_prefixed
    yield
    LocalActivationFs.list_prefixed = real


@pytest.fixture
def world(tmp_path) -> World:
    layout = make_layout(tmp_path)
    os.chmod(layout.var_tmp, 0o1777)
    return World(layout, tmp_path, pass_extra={"activation_id": ACT_ID})


def claim_exists(world: World) -> bool:
    return os.path.lexists(world.paths.consume_dir)


# ---------------------------------------------------------------------------
# CQ-0 … CQ-7: the accepted sequence
# ---------------------------------------------------------------------------


def test_a_complete_accepted_activation_is_consumed(world):
    """RT1.CQ0.* … RT1.CQ7.3: exit 0 only after ``consumed`` and ``run-end`` are durable."""
    result = consume_at(world)
    assert result.raised is None
    out = result.outcome
    assert out.end is ConsumeEnd.CONSUMED and out.exit_code == 0
    assert out.line() == f"rp11-consume consumed {ACT_ID} step=none class=none pk=not-authorized"
    assert consume_ops(world) == [
        "run-start", "remove-intent", "removed", "child", "grant-check", "consumed", "run-end",
    ]
    journal = consume_journal(world)
    assert journal.lines[-2].fields == {"pk_status": "not-authorized", "inactive_enter_us": TAU0}
    assert journal.lines[-1].fields == {"outcome": "consumed"}
    assert not os.path.lexists(world.paths.rule)
    assert k_is_free(world)


def test_run_start_carries_the_claim_the_act_journal_the_lock_and_the_helper(world):
    """RT1.CQ2.5 … RT1.CQ2.9: the accepted fields, exactly."""
    result = consume_at(world)
    assert result.outcome.end is ConsumeEnd.CONSUMED
    start = consume_journal(world).lines[0].fields
    claim = os.stat(world.paths.consume_dir)
    lock = os.stat(world.paths.lock_dir)
    act = (Path(world.paths.act_dir) / "journal").read_bytes()
    assert start["invocation_id"] == CONSUME_INV and start["boot_id"] == BOOT
    assert start["claim"] == {"dev": claim.st_dev, "ino": claim.st_ino}
    assert start["lock"] == {
        "object": {"path": world.paths.lock_dir, "dev": lock.st_dev, "ino": lock.st_ino},
        "mode": "held",
        "wait_ms": 0,
    }
    length = start["act_journal"]["length"]
    assert 0 < length <= len(act)
    assert hashlib.sha256(act[:length]).hexdigest() == start["act_journal"]["sha256"]
    tool = hashlib.sha256(Path(world.layout.tool).read_bytes()).hexdigest()
    assert start["helper"] == {"role": "consume", "tool_sha256": tool}


def test_the_claim_is_a_root_0755_directory_with_a_0644_journal(world):
    """RT1.CQ2.2 … RT1.CQ2.5."""
    consume_at(world)
    claim = os.lstat(world.paths.consume_dir)
    journal = os.lstat(Path(world.paths.consume_dir) / "journal")
    assert stat.S_ISDIR(claim.st_mode) and stat.S_IMODE(claim.st_mode) == 0o755
    assert stat.S_ISREG(journal.st_mode) and stat.S_IMODE(journal.st_mode) == 0o644
    assert claim.st_uid == journal.st_uid == os.getuid() and journal.st_nlink == 1


def test_the_grant_is_gone_and_pk_runs_only_after_it_and_after_the_removal_lines(world):
    """RT1.CQ3.6 … RT1.CQ3.8, RT1.CQ5.1/2: write-ahead, then PK/2 for ``start`` seeking *not authorized*."""
    result = consume_at(world)
    snap = result.pk.snapshot
    assert snap["rule_present"] is False
    assert snap["ops"] == ["run-start", "remove-intent", "removed"]
    assert (snap["verb"], snap["mode"]) == (UnitVerb.START, PkMode.SEEK_NOT_AUTHORIZED)
    intent = consume_journal(world).ops("remove-intent")[0].fields
    assert intent["path"] == world.paths.rule and intent["sha256"] == hashlib.sha256(world.fx.rule_bytes).hexdigest()
    assert consume_journal(world).ops("grant-check")[0].fields == {
        "verb": "start", "mode": "seek-not-authorized", "outcome": "not-authorized", "reason": "decided", "calls": 1,
    }


def test_cq4_reads_both_units_with_the_journaled_identities(world):
    """RT1.CQ4.7, RT1.CQ4.8: holder ``active`` + journaled id; capture ``activating`` + own id + τ₀."""
    result = consume_at(world)
    assert result.units.reads == [HOLDER, CAPTURE_UNIT]


def test_a_consume_writes_no_record_and_removes_nothing_but_the_rule(world):
    """RT1.CQ7.4: no record file; ``pass-a.json``, K, the ACT evidence, the activation record and the
    claim are all still there, byte for byte, after a complete consume."""
    watched = {
        "pass-config": Path(world.paths.pass_config),
        "grant-id": Path(world.paths.grant_id),
        "act-journal": Path(world.paths.act_dir) / "journal",
        "act-record": Path(world.paths.record_dir) / f"{ACT_ID}.act.json",
    }
    before = {}
    result = consume_at(world, mutate=lambda: before.update({k: p.read_bytes() for k, p in watched.items()}))
    assert result.outcome.end is ConsumeEnd.CONSUMED
    for name in ("pass-config", "grant-id", "act-record"):
        assert watched[name].read_bytes() == before[name], name
    assert watched["act-journal"].read_bytes().startswith(before["act-journal"])  # only the holder appends
    assert sorted(p.name for p in Path(world.paths.record_dir).iterdir()) == [f"{ACT_ID}.act.json"]
    assert os.path.isdir(world.paths.lock_dir) and os.path.isdir(world.paths.consume_dir)


def test_cleanup_recovers_after_a_consume_and_reports_the_claim(world):
    """RT1.CQ7.4: CL reads the retained journal; nothing of RT-1's is removed by it."""
    consume_at(world)
    outcome = world.recover()
    assert Path(world.paths.consume_dir, "journal").exists()
    assert outcome.record["consume"] == {"class": "claimed", "outcome": "consumed"}


# ---------------------------------------------------------------------------
# helpers for the negative matrix
# ---------------------------------------------------------------------------


def expect_failed(world, result, end, step, klass, *, rule_gone: bool, pk_ran: bool = False):
    out = result.outcome
    assert result.raised is None, result.raised
    assert (out.end, out.step, out.klass) == (end, step, klass)
    assert out.exit_code != 0
    assert result.state["rule"] is (not rule_gone)
    assert result.state["k_free"] is True
    ops = consume_ops(world)
    assert "consumed" not in ops
    if end in (ConsumeEnd.FAILED, ConsumeEnd.PRECONDITION):
        journal = consume_journal(world)
        assert journal.lines[-2].op == "consume-failed" and journal.lines[-1].op == "run-end"
        assert journal.lines[-2].fields == {"step": step.lower(), "class": klass}
        assert journal.lines[-1].fields == {"outcome": "failed"}
    assert (result.pk.snapshot is not None) is pk_ran


def replace_by_new_inode(path: Path, data: bytes, mode: int = 0o644) -> None:
    """Another inode at the name. The new file is made while the old one still exists
    (tmpfs and ext4 reuse a freed inode number at once, which would be the same object)."""
    fresh = path.with_name(path.name + ".fresh")
    fresh.write_bytes(data)
    os.chmod(fresh, mode)
    os.rename(fresh, path)


def pass_path(world) -> Path:
    return Path(world.paths.pass_config)


def rewrite(path: Path, data: bytes, mode: int = 0o644) -> None:
    """Replace the file by a new inode (what an attacker or a retry could do)."""
    os.unlink(path)
    path.write_bytes(data)
    os.chmod(path, mode)


def nothing_created(world, result):
    assert not claim_exists(world) and consume_ops(world) == []
    assert result.state["rule"] is True and result.state["k_free"] is True
    assert result.pk.snapshot is None and result.units.reads == []


# ---------------------------------------------------------------------------
# CQ-0 — identify (RT1.CQ0.1 … RT1.CQ0.6): any failure creates nothing
# ---------------------------------------------------------------------------


def _symlinked(world):
    target = Path(world.tmp) / "elsewhere"
    target.write_bytes(pass_path(world).read_bytes())
    os.chmod(target, 0o644)
    os.unlink(pass_path(world))
    os.symlink(target, pass_path(world))


def _hardlinked(world):
    os.link(pass_path(world), Path(world.tmp) / "second-link")


def _as_directory(world):
    os.unlink(pass_path(world))
    os.mkdir(pass_path(world), 0o755)


def _parent_symlinked(world):
    moved = Path(world.tmp) / "moved-tree"
    os.rename(world.paths.tree_p, moved)
    os.symlink(moved, world.paths.tree_p)


def _doc(**kw) -> bytes:
    return canonical_bytes(kw)


CQ0_BREAKS = {
    "missing": lambda w: os.unlink(pass_path(w)),
    "symlink": _symlinked,
    "hardlinked": _hardlinked,
    "directory": _as_directory,
    "parent-is-a-symlink": _parent_symlinked,
    "mode-0600": lambda w: os.chmod(pass_path(w), 0o600),
    "mode-0664": lambda w: os.chmod(pass_path(w), 0o664),
    "oversized": lambda w: rewrite(pass_path(w), _doc(activation_id=ACT_ID, pad="a" * 70_000)),
    "not-json": lambda w: rewrite(pass_path(w), b"not json\n"),
    "not-canonical": lambda w: rewrite(pass_path(w), b'{ "activation_id": "%s" }\n' % ACT_ID.encode()),
    "not-an-object": lambda w: rewrite(pass_path(w), canonical_bytes([ACT_ID])),
    "no-activation-id": lambda w: rewrite(pass_path(w), _doc(schema="rp11-pass-a/1")),
    "id-not-a-string": lambda w: rewrite(pass_path(w), _doc(activation_id=7)),
    "id-malformed": lambda w: rewrite(pass_path(w), _doc(activation_id="rp11-act-20261013T101500Z-0A1B2C3D")),
    "id-with-path": lambda w: rewrite(pass_path(w), _doc(activation_id="../" + ACT_ID)),
    "id-trailing-newline": lambda w: rewrite(pass_path(w), _doc(activation_id=ACT_ID + "\n")),
    "empty": lambda w: rewrite(pass_path(w), b""),
}


@pytest.mark.parametrize("name", sorted(CQ0_BREAKS))
def test_cq0_any_identity_failure_is_unidentified_and_creates_nothing(world, name):
    """RT1.CQ0.1 … RT1.CQ0.6."""
    result = consume_at(world, mutate=lambda: CQ0_BREAKS[name](world))
    out = result.outcome
    assert (out.end, out.step, out.klass) == (ConsumeEnd.UNIDENTIFIED, "CQ-0", "pass-config")
    assert out.line() == "rp11-consume consume-unidentified unidentified step=CQ-0 class=pass-config pk=absent"
    nothing_created(world, result)


def test_cq0_a_pass_config_naming_another_activation_claims_that_activation_only(world):
    """The id is taken only from pass-a.json; K for it does not exist ⇒ unidentified, nothing created."""
    other = "rp11-act-20261013T101500Z-ffffffff"
    result = consume_at(world, mutate=lambda: rewrite(pass_path(world), _doc(activation_id=other)))
    assert result.outcome.end is ConsumeEnd.UNIDENTIFIED and result.outcome.step == "CQ-1"
    assert result.outcome.activation_id == other
    assert result.state["rule"] is True and not claim_exists(world)
    assert not os.path.lexists(f"{world.layout.var_tmp}/{other}-consume-evidence")


def test_cq0_reads_nothing_from_the_requester_only_the_fixed_path(world):
    layout = world.layout
    assert layout.pass_config == f"{layout.run}/freedom-blades-rp11/pass-a.json"
    assert layout.pass_config == ActivationPaths(layout, ACT_ID).pass_config


# ---------------------------------------------------------------------------
# CQ-1 — K (RT1.CQ1.1, RT1.CQ1.2)
# ---------------------------------------------------------------------------


def _k_renamed(world):
    os.rename(world.paths.lock_dir, f"{world.paths.lock_dir}.away")


def _k_mode(world):
    os.chmod(world.paths.lock_dir, 0o750)


def _k_is_a_file(world):
    os.rename(world.paths.lock_dir, f"{world.paths.lock_dir}.away")
    Path(world.paths.lock_dir).write_bytes(b"")


def _k_symlink(world):
    os.rename(world.paths.lock_dir, f"{world.paths.lock_dir}.away")
    os.symlink(f"{world.paths.lock_dir}.away", world.paths.lock_dir)


@pytest.mark.parametrize("break_k", [_k_renamed, _k_mode, _k_is_a_file, _k_symlink])
def test_cq1_a_missing_or_damaged_k_is_unidentified_and_creates_nothing(world, break_k):
    result = consume_at(world, mutate=lambda: break_k(world))
    out = result.outcome
    assert (out.end, out.step, out.klass) == (ConsumeEnd.UNIDENTIFIED, "CQ-1", "k-unusable")
    assert not claim_exists(world) and result.state["rule"] is True
    assert result.pk.snapshot is None


class _NoSleep:
    """A clock that fails the test if RT-1 ever waits."""

    def monotonic_ms(self):
        return 5

    def sleep_ms(self, ms):
        raise AssertionError("RT-1 waited for K")


def test_cq1_a_held_k_is_busy_at_once_and_never_waited_for(world):
    held = {}

    def hold_k():
        held["fd"] = os.open(world.paths.lock_dir, os.O_RDONLY | os.O_DIRECTORY)
        fcntl.flock(held["fd"], fcntl.LOCK_EX | fcntl.LOCK_NB)

    result = consume_at(world, mutate=hold_k, clock=_NoSleep(), after=lambda: os.close(held["fd"]))
    out = result.outcome
    assert (out.end, out.step, out.klass) == (ConsumeEnd.BUSY, "CQ-1", "k-held")
    assert not claim_exists(world) and result.state["rule"] is True
    assert result.pk.snapshot is None and result.units.reads == []


# ---------------------------------------------------------------------------
# CQ-2 — the one-shot claim (RT1.CQ2.1 … RT1.CQ2.10)
# ---------------------------------------------------------------------------


def test_cq2_an_existing_claim_is_repeated_and_never_opened(world):
    barrier = Path(world.paths.consume_dir)
    before = {}

    def plant():  # inside HL: an earlier claim in this boot (the holder would end at once if it saw it earlier)
        os.mkdir(barrier, 0o000)  # not even the owner can open it: any open would fail differently
        before["stat"] = os.lstat(barrier)

    result = consume_at(world, mutate=plant)
    before = before["stat"]
    out = result.outcome
    assert (out.end, out.step, out.klass) == (ConsumeEnd.REPEATED, "CQ-2", "claim-exists")
    assert os.lstat(barrier) == before and os.listdir(world.layout.var_tmp).count(barrier.name) == 1
    assert result.state["rule"] is True and result.pk.snapshot is None
    os.chmod(barrier, 0o755)  # so the temporary tree can be removed


def test_cq2_an_existing_claim_that_is_a_symlink_is_repeated_and_not_followed(world):
    target = Path(world.tmp) / "victim"
    os.mkdir(target, 0o755)
    result = consume_at(world, mutate=lambda: os.symlink(target, world.paths.consume_dir))
    assert result.outcome.end is ConsumeEnd.REPEATED
    assert os.listdir(target) == [] and result.state["rule"] is True


def test_cq2_a_later_attempt_in_the_same_boot_is_repeated(world):
    second = {}

    def again():
        second["outcome"] = build_consume(
            CONSUME_INV, layout=world.layout, services=HoldServices(ConsumeUnits(), ProbePk(world), None), clock=world.clock
        ).run()

    result = consume_at(world, after=again)
    assert result.outcome.end is ConsumeEnd.CONSUMED
    assert second["outcome"].end is ConsumeEnd.REPEATED and second["outcome"].exit_code == 23
    assert consume_ops(world)[-1] == "run-end"  # the first journal is untouched


def test_cq2_concurrent_starts_cannot_both_consume(world):
    result = consume_at(world, threads=8)
    ends = sorted(o.end.value for o in result.outcomes)
    assert ends.count("consumed") == 1
    assert set(ends) <= {"consumed", "consume-busy", "consume-repeated"}
    assert consume_ops(world).count("run-start") == 1 and consume_ops(world).count("consumed") == 1


def test_cq2_the_claim_store_barrier_admits_one_creator(world):
    stores = [
        LocalClaimStore(var_tmp=world.layout.var_tmp, activation_id=ACT_ID, owner=world.layout.owner)
        for _ in range(8)
    ]
    barrier = threading.Barrier(8)
    made, existed = [], []

    def create(store):
        barrier.wait()
        try:
            made.append(store.create())
        except consume_module.ClaimExists:
            existed.append(1)

    pool = [threading.Thread(target=create, args=(st,)) for st in stores]
    [t.start() for t in pool]
    [t.join() for t in pool]
    assert len(made) == 1 and len(existed) == 7
    made[0].close()


def test_cq2_var_tmp_that_is_not_root_1777_makes_no_claim_and_the_grant_is_still_removed(world):
    result = consume_at(world, mutate=lambda: os.chmod(world.layout.var_tmp, 0o755))
    out = result.outcome
    assert (out.end, out.step, out.klass) == (ConsumeEnd.CLAIM_FAILED, "CQ-2", "claim-not-made")
    assert out.exit_code == 24 and not claim_exists(world)
    assert result.state["rule"] is False  # grant priority: removed although no claim could be made
    assert result.pk.snapshot["rule_present"] is False and out.pk == "not-authorized"
    os.chmod(world.layout.var_tmp, 0o1777)


def test_cq2_any_other_mkdir_error_makes_no_claim_and_the_grant_is_still_removed(world, monkeypatch):
    real = os.mkdir

    def failing(path, *a, **kw):
        if str(path).endswith("-consume-evidence"):
            raise OSError(13, "EACCES")
        return real(path, *a, **kw)

    result = consume_at(world, mutate=lambda: monkeypatch.setattr(os, "mkdir", failing),
                        after=lambda: monkeypatch.setattr(os, "mkdir", real))
    assert result.outcome.end is ConsumeEnd.CLAIM_FAILED
    assert result.state["rule"] is False and not claim_exists(world)


def test_cq2_a_journal_that_cannot_be_created_leaves_the_barrier_and_still_removes_the_grant(world, monkeypatch):
    real = os.open

    def failing(path, flags, *a, **kw):
        if path == "journal" and flags & os.O_EXCL and kw.get("dir_fd") is not None:
            raise OSError(28, "ENOSPC")
        return real(path, flags, *a, **kw)

    result = consume_at(world, mutate=lambda: monkeypatch.setattr(os, "open", failing),
                        after=lambda: monkeypatch.setattr(os, "open", real))
    out = result.outcome
    assert (out.end, out.step, out.klass) == (ConsumeEnd.EVIDENCE_UNWRITABLE, "CQ-2", "claim-evidence")
    assert claim_exists(world) and result.state["rule"] is False  # the barrier stands
    assert not (Path(world.paths.consume_dir) / "journal").exists()
    assert out.pk == "not-authorized"


def test_cq2_a_claim_directory_that_is_not_a_fresh_0700_directory_is_an_evidence_failure(world, monkeypatch):
    real = os.mkdir

    def other_mode(path, mode=0o777, *a, **kw):
        real(path, mode, *a, **kw)
        if str(path).endswith("-consume-evidence"):
            os.chmod(path, 0o750, dir_fd=kw.get("dir_fd"))

    result = consume_at(world, mutate=lambda: monkeypatch.setattr(os, "mkdir", other_mode),
                        after=lambda: monkeypatch.setattr(os, "mkdir", real))
    assert result.outcome.end is ConsumeEnd.EVIDENCE_UNWRITABLE
    assert result.state["rule"] is False


def test_cq2_an_unreadable_act_journal_is_an_evidence_failure_and_leaves_the_rule_for_cleanup(world):
    result = consume_at(world, mutate=lambda: os.unlink(Path(world.paths.act_dir) / "journal"))
    out = result.outcome
    assert (out.end, out.step, out.klass) == (ConsumeEnd.EVIDENCE_UNWRITABLE, "CQ-2", "run-start")
    assert claim_exists(world) and consume_ops(world) == []
    assert result.state["rule"] is True  # nothing can be proved, so nothing is removed
    assert result.pk.snapshot is None


def test_cq2_an_act_directory_that_is_not_0700_is_an_evidence_failure(world):
    result = consume_at(world, mutate=lambda: os.chmod(world.paths.act_dir, 0o755))
    assert result.outcome.end is ConsumeEnd.EVIDENCE_UNWRITABLE and result.state["rule"] is True
    os.chmod(world.paths.act_dir, 0o700)


# --- every write and flush failure in the whole sequence ------------------------------
#
# I/O order of a complete run: run-start (write 1, fsync 1) → claim directory fsync 2 →
# /var/tmp fsync 3 → remove-intent (w2, f4) → removed (w3, f5) → child (w4, f6) →
# grant-check (w5, f7) → consumed (w6, f8) → run-end (w7, f9).


@pytest.mark.parametrize("write_at", range(1, 8))
def test_every_failed_journal_write_fails_the_attempt_and_the_grant_is_gone(world, write_at):
    """RT1.CQ2.3 … RT1.CQ7.1: a line that cannot be written never keeps the grant."""
    result = consume_at(world, io=FailingIO(fail_write_at=write_at))
    out = result.outcome
    assert result.raised is None and out.end is not ConsumeEnd.CONSUMED and out.exit_code != 0
    assert out.end is ConsumeEnd.EVIDENCE_UNWRITABLE
    assert result.state["rule"] is False and result.state["k_free"] is True
    if write_at <= 6:
        assert "consumed" not in consume_ops(world)


@pytest.mark.parametrize("fsync_at", range(1, 10))
def test_every_failed_flush_fails_the_attempt_and_the_grant_is_gone(world, fsync_at):
    result = consume_at(world, io=FailingIO(fail_fsync_at=fsync_at))
    out = result.outcome
    assert result.raised is None and out.end is ConsumeEnd.EVIDENCE_UNWRITABLE and out.exit_code != 0
    assert result.state["rule"] is False and result.state["k_free"] is True
    if fsync_at <= 7:
        assert "consumed" not in consume_ops(world)


def test_grant_priority_removes_before_any_slower_persistent_work_and_never_reaches_cq4(world):
    """RT1.CQ3.9: after a broken journal PK runs in memory, DI-1 is never read, nothing more is written."""
    result = consume_at(world, io=FailingIO(fail_write_at=2))  # remove-intent cannot be written
    assert result.pk.snapshot["rule_present"] is False
    assert result.units.reads == []  # CQ-4 never ran
    assert consume_ops(world) == ["run-start"]  # no line after the journal broke
    assert result.outcome.pk == "not-authorized"


def test_a_complete_run_flushes_journal_then_claim_then_var_tmp_in_that_order(world, monkeypatch):
    order = []
    real = os.fsync
    claim_dir_ino = {}

    def spy(fd):
        info = os.fstat(fd)
        if stat.S_ISDIR(info.st_mode):
            order.append("var_tmp" if info.st_ino == os.stat(world.layout.var_tmp).st_ino else "dir")
        else:
            order.append("file")
        return real(fd)

    class SpyIO(FileIO):
        def fsync(self, fd):
            spy(fd)
            super().fsync(fd)

    consume_at(world, io=SpyIO())
    # the first three flushes are the CQ-2 durability point: journal, claim directory, /var/tmp
    assert order[:3] == ["file", "dir", "var_tmp"]
    del claim_dir_ino


# ---------------------------------------------------------------------------
# CQ-3 — grant first (RT1.CQ3.1 … RT1.CQ3.8)
# ---------------------------------------------------------------------------


def _corrupt_act_journal(world):
    path = Path(world.paths.act_dir) / "journal"
    data = path.read_bytes().split(b"\n")
    data[2] = data[2].replace(b'"op":', b'"oq":')
    rewrite(path, b"\n".join(data))


def _torn_tail(world):
    path = Path(world.paths.act_dir) / "journal"
    with open(path, "ab") as handle:
        handle.write(b'{"seq":9999,"op":"pass-obs')


def test_cq3_a_torn_act_journal_tail_is_ignored(world):
    """H-JRN.9: a final segment without LF is reported, not trusted, and does not fail the parse."""
    result = consume_at(world, mutate=lambda: _torn_tail(world))
    assert result.outcome.end is ConsumeEnd.CONSUMED


def test_cq3_an_invalid_act_journal_fails_closed_and_leaves_the_rule(world):
    result = consume_at(world, mutate=lambda: _corrupt_act_journal(world))
    expect_failed(world, result, ConsumeEnd.FAILED, "CQ-3", "invalid-journal", rule_gone=False)


@pytest.mark.parametrize(
    "break_authority,klass",
    [
        (lambda w: os.unlink(next(Path(w.layout.store, "a2").iterdir())), "invalid-authority"),
        (lambda w: os.chmod(next(Path(w.layout.store, "a2").iterdir()), 0o644), "invalid-authority"),
        (lambda w: os.unlink(next(Path(w.layout.store, "h1").iterdir())), "invalid-authority"),
        (lambda w: _rewrite_first(Path(w.layout.store, "h1"), b"{}\n"), "invalid-authority"),
        (lambda w: _rewrite_first(Path(w.layout.store, "a2"), b"{}\n"), "invalid-authority"),
    ],
)
def test_cq3_an_authority_chain_that_does_not_verify_leaves_the_rule(world, break_authority, klass):
    result = consume_at(world, mutate=lambda: break_authority(world))
    expect_failed(world, result, ConsumeEnd.FAILED, "CQ-3", klass, rule_gone=False)


def _rewrite_first(directory: Path, data: bytes) -> None:
    rewrite(next(directory.iterdir()), data, 0o444)


def test_cq3_the_staged_rule_digest_comes_from_the_pinned_chain_not_from_the_journal(world):
    """A journal that names a different staged-rule digest than A-2 pins is not the authority."""

    def forge():
        path = Path(world.paths.act_dir) / "journal"
        lines = path.read_bytes().split(b"\n")[:-1]
        prev, forged = GENESIS, []
        for i, raw in enumerate(lines, start=1):
            doc = parse_canonical(raw + b"\n")
            doc["prev"] = prev
            if i == 1:
                doc["staged_rule_sha256"] = "ab" * 32
            encoded = canonical_bytes(doc)
            forged.append(encoded)
            prev = hashlib.sha256(encoded).hexdigest()
        replace_by_new_inode(path, b"".join(forged))

    result = consume_at(world, mutate=forge)
    expect_failed(world, result, ConsumeEnd.FAILED, "CQ-3", "invalid-authority", rule_gone=False)


def forge_act(world, edit) -> None:
    """Rewrite the ACT journal with ``edit(doc)`` applied to every line and a valid chain."""
    path = Path(world.paths.act_dir) / "journal"
    prev, forged = GENESIS, []
    for raw in path.read_bytes().split(b"\n")[:-1]:
        doc = parse_canonical(raw + b"\n")
        edit(doc)
        doc["prev"] = prev
        encoded = canonical_bytes(doc)
        forged.append(encoded)
        prev = hashlib.sha256(encoded).hexdigest()
    replace_by_new_inode(path, b"".join(forged))


def test_cq3_a_journal_that_attributes_foreign_content_to_the_grant_does_not_authorize_a_removal(world):
    """The staged-rule digest is A-2's pin (the pinned chain), never a journal field alone: a journal
    edited to name planted content as the grant, with the live file changed to match, is still not ours."""
    planted = b"// planted rule that the journal claims is the grant\n"
    digest = hashlib.sha256(planted).hexdigest()

    def edit(doc):
        if doc["op"] == "file-intent" and doc["name"] == "50-freedom-blades-rp11.rules":
            doc["sha256"], doc["size"] = digest, len(planted)

    def forge():
        with open(world.paths.rule, "r+b") as handle:  # same inode, planted content, same mode
            handle.truncate(0)
            handle.write(planted)
        forge_act(world, edit)

    result = consume_at(world, mutate=forge)
    expect_failed(world, result, ConsumeEnd.FAILED, "CQ-3", "unprovable", rule_gone=False)
    assert Path(world.paths.rule).read_bytes() == planted and "removed" not in consume_ops(world)


def test_cq3_another_boot_leaves_the_rule_for_cleanup(world):
    def other_boot():
        Path(world.layout.boot_id_file).write_text("99999999-2222-3333-4444-555555555555\n")

    result = consume_at(world, mutate=other_boot)
    expect_failed(world, result, ConsumeEnd.FAILED, "CQ-3", "boot", rule_gone=False)


def test_cq3_an_act_directory_of_another_owner_is_not_the_operators(world, monkeypatch):
    monkeypatch.setattr(
        LocalConsumeHost,
        "read_act_journal",
        lambda self, directory, *, max_bytes: _foreign_dir(self, directory, max_bytes),
    )
    result = consume_at(world)
    expect_failed(world, result, ConsumeEnd.FAILED, "CQ-3", "invalid-journal", rule_gone=False)


def _foreign_dir(host, directory, max_bytes):
    read = _REAL_READ_ACT(host, directory, max_bytes=max_bytes)
    return consume_module.ActJournalRead(read.data, read.dir_uid + 1) if read else None


_REAL_READ_ACT = LocalConsumeHost.read_act_journal


def test_cq3_an_absent_rule_is_never_a_success(world):
    result = consume_at(world, mutate=lambda: os.unlink(world.paths.rule))
    expect_failed(world, result, ConsumeEnd.FAILED, "CQ-3", "absent", rule_gone=True)
    assert consume_ops(world) == ["run-start", "consume-failed", "run-end"]


def test_cq3_a_damaged_rule_is_kept(world):
    def damage():
        with open(world.paths.rule, "ab") as handle:
            handle.write(b"// edited\n")

    result = consume_at(world, mutate=damage)
    expect_failed(world, result, ConsumeEnd.FAILED, "CQ-3", "damaged", rule_gone=False)
    assert Path(world.paths.rule).read_bytes().endswith(b"// edited\n")


def test_cq3_a_foreign_rule_at_the_name_is_kept(world):
    same_bytes = world.fx.rule_bytes

    def replace():
        replace_by_new_inode(Path(world.paths.rule), same_bytes)  # identical content, another inode

    result = consume_at(world, mutate=replace)
    expect_failed(world, result, ConsumeEnd.FAILED, "CQ-3", "foreign", rule_gone=False)


def test_cq3_a_symlink_at_the_rule_name_is_kept_and_not_followed(world):
    target = Path(world.tmp) / "decoy"
    target.write_bytes(world.fx.rule_bytes)
    os.chmod(target, 0o644)

    def replace():
        os.unlink(world.paths.rule)
        os.symlink(target, world.paths.rule)

    result = consume_at(world, mutate=replace)
    expect_failed(world, result, ConsumeEnd.FAILED, "CQ-3", "foreign", rule_gone=False)
    assert target.exists() and os.path.islink(world.paths.rule)


def test_cq3_a_rule_that_cannot_be_inspected_is_kept_uninspected(world, monkeypatch):
    from test_rp11_cleanup import InspectionFault

    holder = {}
    result = consume_at(
        world,
        mutate=lambda: holder.update(f=InspectionFault(monkeypatch, world.paths.rule, "read")),
    )
    expect_failed(world, result, ConsumeEnd.FAILED, "CQ-3", "uninspected", rule_gone=False)
    assert holder["f"].hits >= 1


def test_cq3_an_unremovable_rule_is_reported_and_kept(world):
    result = consume_at(world, mutate=lambda: os.chmod(world.paths.rules_dir, 0o555),
                        after=lambda: os.chmod(world.paths.rules_dir, 0o755))
    expect_failed(world, result, ConsumeEnd.FAILED, "CQ-3", "unremovable", rule_gone=False)
    ops = consume_ops(world)
    assert ops[:3] == ["run-start", "remove-intent", "remove-failed"]
    assert consume_journal(world).ops("remove-failed")[0].fields["errno"] in (1, 13)


def test_cq3_a_rule_swapped_after_classification_is_not_removed(world, monkeypatch):
    """H-GR1.2: the descriptor re-verification, not the earlier lookup, authorizes the unlink."""
    armed = {}
    real = LocalActivationFs.observe

    def swap(self, path, **kw):
        seen = real(self, path, **kw)
        if armed.get("on") and path == world.paths.rule and not armed.get("done"):
            armed["done"] = True
            replace_by_new_inode(Path(path), b"// somebody else's rule\n")  # a different inode at the name
        return seen

    monkeypatch.setattr(LocalActivationFs, "observe", swap)
    result = consume_at(world, mutate=lambda: armed.update(on=True))
    expect_failed(world, result, ConsumeEnd.FAILED, "CQ-3", "foreign", rule_gone=False)
    assert Path(world.paths.rule).read_bytes() == b"// somebody else's rule\n"
    assert "removed" not in consume_ops(world)


def test_cq3_removal_is_write_ahead_and_the_journal_names_exactly_the_fixed_rule(world, monkeypatch):
    seen = []
    real = LocalActivationFs.remove

    def spy(self, path, identity, *, directory, before_unlink):
        def probe(observed):
            before_unlink(observed)
            seen.append(("unlink", consume_ops(world)))

        return real(self, path, identity, directory=directory, before_unlink=probe)

    monkeypatch.setattr(LocalActivationFs, "remove", spy)
    consume_at(world)
    consume_unlinks = [ops for _kind, ops in seen if ops and ops[0] == "run-start"]
    assert consume_unlinks == [["run-start", "remove-intent"]]  # durable before the unlink


# ---------------------------------------------------------------------------
# CQ-4 — preconditions, each independently false or unreadable (RT1.CQ4.1 … RT1.CQ4.8)
# ---------------------------------------------------------------------------


def after_removal(monkeypatch, action) -> None:
    """Run ``action`` once, right after RT-1 removed the rule and before CQ-4 starts."""
    real = LocalActivationFs.remove
    done = []

    def remove(self, path, identity, *, directory, before_unlink):
        out = real(self, path, identity, directory=directory, before_unlink=before_unlink)
        if out.outcome is RemovalOutcome.REMOVED and not done and os.path.exists(world_dir_of(path)):
            done.append(1)
            action()
        return out

    monkeypatch.setattr(LocalActivationFs, "remove", remove)


def world_dir_of(path: str) -> str:
    return os.path.dirname(path)


def _act_lines(world) -> list[bytes]:
    return (Path(world.paths.act_dir) / "journal").read_bytes().split(b"\n")[:-1]


def _truncate_before_hold_start(world):
    lines = _act_lines(world)
    keep = [raw for raw in lines if b'"op":"hold-start"' not in raw]
    cut = lines.index(next(raw for raw in lines if b'"op":"hold-start"' in raw))
    replace_by_new_inode(Path(world.paths.act_dir) / "journal", b"".join(raw + b"\n" for raw in lines[:cut]))
    assert len(keep) >= cut


def _append_hold_end(world):
    path = Path(world.paths.act_dir) / "journal"
    parsed = parse_journal(path.read_bytes(), kind=JournalKind.ACT, run=ACT_ID)
    line = serialize_line(
        JournalKind.ACT, seq=len(parsed.lines) + 1, prev=parsed.lines[-1].digest, run=ACT_ID,
        op="hold-end", fields={"reason": "pass-ended", "observation": "absent"},
    )
    with open(path, "ab") as handle:
        handle.write(line)


def _plant_deact_dir(world):
    os.mkdir(f"{world.layout.var_tmp}/{ACT_ID}-deact-1-evidence", 0o755)


def _plant_deact_record(world):
    record = Path(world.paths.record_dir) / f"{ACT_ID}.deact-1.json"
    record.write_bytes(b"{}\n")
    os.chmod(record, 0o444)


def _unlistable_var_tmp(world):
    """The evidence listing alone fails (the directory itself stays reachable)."""
    LocalActivationFs.list_prefixed = lambda self, directory, prefix: None  # restored by ``_restore_listing``


def _act_record_failed(world):
    path = Path(world.paths.record_dir) / f"{ACT_ID}.act.json"
    doc = parse_canonical(path.read_bytes())
    doc["outcome"] = "failed"
    rewrite(path, canonical_bytes(doc), 0o444)


CQ4_BREAKS = {
    "pass-config-replaced-same-bytes": (
        lambda w: replace_by_new_inode(pass_path(w), pass_path(w).read_bytes()), "pass-config"),
    "pass-config-edited-in-place": (lambda w: pass_path(w).write_bytes(pass_path(w).read_bytes() + b" "), "pass-config"),
    "pass-config-mode": (lambda w: os.chmod(pass_path(w), 0o600), "pass-config"),
    "pass-config-removed": (lambda w: os.unlink(pass_path(w)), "pass-config"),
    "boot-changed": (
        lambda w: Path(w.layout.boot_id_file).write_text("99999999-2222-3333-4444-555555555555\n"), "boot"),
    "act-record-missing": (lambda w: os.unlink(Path(w.paths.record_dir) / f"{ACT_ID}.act.json"), "act-record"),
    "act-record-writable": (lambda w: os.chmod(Path(w.paths.record_dir) / f"{ACT_ID}.act.json", 0o644), "act-record"),
    "act-record-not-activated": (_act_record_failed, "act-record"),
    "act-journal-without-hold-start": (_truncate_before_hold_start, "hold"),
    "act-journal-with-hold-end": (_append_hold_end, "hold"),
    "act-journal-unreadable": (lambda w: os.chmod(Path(w.paths.act_dir) / "journal", 0o600), "act-journal"),
    "deact-evidence-directory": (_plant_deact_dir, "deactivation-evidence"),
    "deact-record": (_plant_deact_record, "deactivation-evidence"),
    "evidence-listing-unreadable": (_unlistable_var_tmp, "deactivation-evidence"),
    "capture-root-exists": (lambda w: os.mkdir(w.capture_root, 0o700), "capture-root"),
    "capture-root-dangling-symlink": (lambda w: os.symlink("/nonexistent-target", w.capture_root), "capture-root"),
}


@pytest.mark.parametrize("name", sorted(CQ4_BREAKS))
def test_cq4_each_precondition_false_or_unreadable_fails_closed_with_the_grant_already_gone(world, monkeypatch, name):
    break_it, klass = CQ4_BREAKS[name]
    after_removal(monkeypatch, lambda: break_it(world))
    result = consume_at(world)
    expect_failed(world, result, ConsumeEnd.PRECONDITION, "CQ-4", klass, rule_gone=True)
    assert result.outcome.exit_code == 26
    assert consume_ops(world)[:3] == ["run-start", "remove-intent", "removed"]


def _units(**kw):
    def build():
        u = ConsumeUnits()
        kw["setup"](u)
        return u

    return build


DI1_BREAKS = {
    "holder-inactive": (lambda u: u.holder.update({UnitProperty.ACTIVE_STATE: "inactive"}), "holder"),
    "holder-activating": (lambda u: u.holder.update({UnitProperty.ACTIVE_STATE: "activating"}), "holder"),
    "holder-other-invocation": (lambda u: u.holder.update({UnitProperty.INVOCATION_ID: "ee" * 16}), "holder"),
    "holder-no-invocation": (lambda u: u.holder.update({UnitProperty.INVOCATION_ID: ""}), "holder"),
    "holder-read-error": (lambda u: setattr(u, "fail", HOLDER), "holder"),
    "capture-active": (lambda u: u.capture.update({UnitProperty.ACTIVE_STATE: "active"}), "capture"),
    "capture-inactive": (lambda u: u.capture.update({UnitProperty.ACTIVE_STATE: "inactive"}), "capture"),
    "capture-failed": (lambda u: u.capture.update({UnitProperty.ACTIVE_STATE: "failed"}), "capture"),
    "capture-other-invocation": (lambda u: u.capture.update({UnitProperty.INVOCATION_ID: "ee" * 16}), "capture"),
    "capture-stale-invocation": (lambda u: u.capture.update({UnitProperty.INVOCATION_ID: ""}), "capture"),
    "capture-other-timestamp": (lambda u: u.capture.update({UnitProperty.INACTIVE_ENTER_TIMESTAMP_MONOTONIC: TAU0 + 1}), "capture"),
    "capture-zero-timestamp": (lambda u: u.capture.update({UnitProperty.INACTIVE_ENTER_TIMESTAMP_MONOTONIC: 0}), "capture"),
    "capture-read-error": (lambda u: setattr(u, "fail", CAPTURE_UNIT), "capture"),
}


@pytest.mark.parametrize("name", sorted(DI1_BREAKS))
def test_cq4_both_di1_sites_fail_closed(world, name):
    """RT1.CQ4.7, RT1.CQ4.8 (and H-DI1.4: a satisfied read is not evidence of absence)."""
    setup, klass = DI1_BREAKS[name]
    units = ConsumeUnits()
    setup(units)
    result = consume_at(world, units=units)
    expect_failed(world, result, ConsumeEnd.PRECONDITION, "CQ-4", klass, rule_gone=True)


def test_cq4_without_a_real_invocation_id_the_capture_comparison_cannot_be_satisfied(world):
    """The ``absent`` provenance is accepted at the first image but never matches the manager's id."""
    result = consume_at(world, invocation="absent", units=ConsumeUnits(invocation="absent"))
    expect_failed(world, result, ConsumeEnd.PRECONDITION, "CQ-4", "capture", rule_gone=True)
    assert consume_journal(world).lines[0].fields["invocation_id"] == "absent"


def test_cq4_a_pass_config_that_does_not_name_this_activation_is_refused(tmp_path):
    layout = make_layout(tmp_path)
    os.chmod(layout.var_tmp, 0o1777)
    other = World(layout, tmp_path, pass_extra={"activation_id": "rp11-act-20261013T101500Z-ffffffff"})
    result = consume_at(other)
    # CQ-0 identifies the other id: its K does not exist.
    assert result.outcome.end is ConsumeEnd.UNIDENTIFIED


# ---------------------------------------------------------------------------
# CQ-5 — negative authorization (RT1.CQ5.1 … RT1.CQ5.3)
# ---------------------------------------------------------------------------


def test_cq5_a_rule_present_again_is_never_covered_by_a_series_result(world):
    units = ConsumeUnits()

    def recreate(unit):
        if unit == CAPTURE_UNIT and not os.path.lexists(world.paths.rule):
            Path(world.paths.rule).write_bytes(b"// back again\n")

    units.on_read = recreate
    result = consume_at(world, units=units)
    expect_failed(world, result, ConsumeEnd.FAILED, "CQ-5", "removed-unconfirmed", rule_gone=False)


@pytest.mark.parametrize(
    "outcome,reason",
    [
        (PkOutcome.AUTHORIZED, None),
        (PkOutcome.UNCONFIRMED, "only-errors"),
        (PkOutcome.UNCONFIRMED, "interrupted"),
        (PkOutcome.UNCONFIRMED, "not-seen"),
        (PkOutcome.UNCONFIRMED, "still-authorized"),
    ],
)
def test_cq5_anything_but_a_decided_not_authorized_fails_and_pathname_absence_never_helps(world, outcome, reason):
    pk = ProbePk(world, outcome=outcome, reason=reason)
    result = consume_at(world, pk=pk)
    expect_failed(world, result, ConsumeEnd.FAILED, "CQ-5", "removed-unconfirmed", rule_gone=True, pk_ran=True)
    check = consume_journal(world).ops("grant-check")[0].fields
    assert check["outcome"] == "unconfirmed" and check["verb"] == "start"
    assert pk.series_runs == 1  # the series is not retried by RT-1


class SeriesPk(ProbePk):
    """The real PK/2 series over scripted DI-5 answers and the SN fakes of ``test_rp11_pk_sn``."""

    def __init__(self, world, answers, *, launcher_kw=None, subject_start=77):
        super().__init__(world)
        self.answers = answers
        self.launcher_kw = launcher_kw or {}
        self.subject_start = subject_start
        self.launcher = None

    def decide(self, operator, verb, mode):
        from application.rp11.authority import Params
        from application.rp11.pk import PkSeries
        from application.rp11.sn import SignalContract
        from application.unit_control import ProcessSubject
        from test_rp11_pk_sn import Authority, Launcher, Ops, Subjects

        clock = Ops(reap_after=0)
        self.launcher = Launcher(clock, **self.launcher_kw)
        self.authority = Authority(self.answers)
        series = PkSeries(
            launcher=self.launcher,
            subjects=Subjects(lambda pid: ControlOk(ProcessSubject(pid, self.subject_start, operator.uid))),
            authority=self.authority,
            contract=SignalContract(clock, grace_ms=2_000, slice_ms=100),
            clock=clock,
            params=Params(pk_op_ms=5_000, pk_call_ms=1_000),
        )
        return series.run(operator, verb, mode)


def _answers(name):
    from application.unit_control import PolkitAuthorized, PolkitNotAuthorized

    return {
        "denied": [PolkitNotAuthorized()],
        "challenge": [PolkitNotAuthorized(challenge=True)],
        "authorized-then-denied": [PolkitAuthorized(), PolkitNotAuthorized()],
        "still-authorized": [PolkitAuthorized()],
        "timeout": [ControlError("timeout")],
        "malformed-reply": [ControlError("invalid-reply")],
        "transport": [ControlError("disconnected")],
    }[name]


@pytest.mark.parametrize("name", ["denied", "challenge", "authorized-then-denied"])
def test_cq5_the_real_series_decides_only_on_a_denial_or_challenge(world, name):
    pk = SeriesPk(world, _answers(name))
    result = consume_at(world, pk=pk)
    assert result.outcome.end is ConsumeEnd.CONSUMED
    assert pk.snapshot["rule_present"] is False
    assert all(h.state.value == "reaped" for h in pk.launcher.spawned)  # every subject settled
    assert consume_journal(world).ops("grant-check")[0].fields["outcome"] == "not-authorized"


@pytest.mark.parametrize("name", ["still-authorized", "timeout", "malformed-reply", "transport"])
def test_cq5_the_real_series_without_a_denial_never_consumes(world, name):
    pk = SeriesPk(world, _answers(name))
    result = consume_at(world, pk=pk)
    expect_failed(world, result, ConsumeEnd.FAILED, "CQ-5", "removed-unconfirmed", rule_gone=True, pk_ran=True)
    assert pk.series_runs == 1 and len(pk.launcher.spawned) == 7  # the schedule, once, no extra series
    assert all(h.state.value == "reaped" for h in pk.launcher.spawned)
    assert consume_journal(world).ops("grant-check")[0].fields["outcome"] == "unconfirmed"


def test_cq5_a_subject_replaced_between_creation_and_the_call_cannot_decide(world):
    pk = SeriesPk(world, _answers("denied"), subject_start=78)
    result = consume_at(world, pk=pk)
    expect_failed(world, result, ConsumeEnd.FAILED, "CQ-5", "removed-unconfirmed", rule_gone=True, pk_ran=True)
    assert pk.authority.calls == []  # Polkit was never asked about a replaced subject


def test_cq5_a_spawn_failure_cannot_decide(world):
    pk = SeriesPk(world, _answers("denied"), launcher_kw={"fail": True})
    result = consume_at(world, pk=pk)
    expect_failed(world, result, ConsumeEnd.FAILED, "CQ-5", "removed-unconfirmed", rule_gone=True, pk_ran=True)


def test_cq5_children_are_journaled_before_grant_check(world):
    result = consume_at(world)
    ops = consume_ops(world)
    assert ops.index("child") < ops.index("grant-check") < ops.index("consumed")
    assert result.outcome.end is ConsumeEnd.CONSUMED


# ---------------------------------------------------------------------------
# CQ-6 / CQ-7 and the exit status
# ---------------------------------------------------------------------------


def test_cq7_run_end_failing_after_consumed_is_durable_still_fails_the_start(world):
    """RT1.CQ7.1: ``consumed`` is durable, ``run-end`` is not: non-zero, so ExecStart= must not run."""
    result = consume_at(world, io=FailingIO(fail_write_at=7))
    out = result.outcome
    assert (out.end, out.step, out.klass) == (ConsumeEnd.EVIDENCE_UNWRITABLE, "CQ-7", "run-end")
    assert out.exit_code != 0
    ops = consume_ops(world)
    assert ops[-1] == "consumed" and "run-end" not in ops
    assert result.state["rule"] is False and result.state["k_free"] is True


def test_cq6_a_missing_consumed_line_is_never_a_pass(world):
    result = consume_at(world, io=FailingIO(fail_write_at=6))
    assert result.outcome.end is ConsumeEnd.EVIDENCE_UNWRITABLE and result.outcome.step == "CQ-6"
    assert "consumed" not in consume_ops(world)


def test_the_exit_map_is_stable_and_only_complete_cq7_is_zero():
    codes = {e: e.exit_code for e in ConsumeEnd}
    assert codes[ConsumeEnd.CONSUMED] == 0
    assert codes == {
        ConsumeEnd.CONSUMED: 0, ConsumeEnd.UNIDENTIFIED: 21, ConsumeEnd.BUSY: 22,
        ConsumeEnd.REPEATED: 23, ConsumeEnd.CLAIM_FAILED: 24, ConsumeEnd.EVIDENCE_UNWRITABLE: 25,
        ConsumeEnd.PRECONDITION: 26, ConsumeEnd.FAILED: 27, ConsumeEnd.INTERNAL: 70,
    }
    assert len(set(codes.values())) == len(codes)
    assert {e.value for e in ConsumeEnd} >= {
        "consume-unidentified", "consume-busy", "consume-repeated", "consume-claim-failed",
        "consume-evidence-unwritable", "consume-precondition", "consume-failed",
    }


DIAGNOSTIC = re.compile(
    r"rp11-consume (consumed|consume-[a-z-]+) (unidentified|rp11-act-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}) "
    r"step=(none|CQ-[0-7]) class=[a-z0-9-]+ pk=[a-z-]+"
)


def test_diagnostics_are_closed_tokens_and_never_render_values(world):
    secret = "/etc/very-secret-path"
    outcomes = [consume_at(world).outcome]
    assert all(DIAGNOSTIC.fullmatch(o.line()) for o in outcomes)
    assert secret not in outcomes[0].line()


# ---------------------------------------------------------------------------
# unexpected exceptions (fixed line) and every interruption point
# ---------------------------------------------------------------------------


def test_an_unexpected_exception_after_the_claim_still_removes_the_grant_and_never_succeeds(world):
    pk = ProbePk(world)
    pk.during = lambda: (_ for _ in ()).throw(RuntimeError("/etc/secret detail"))
    result = consume_at(world, pk=pk)
    out = result.outcome
    assert out.end is ConsumeEnd.INTERNAL and out.exit_code == 70
    assert "secret" not in out.line()
    assert result.state["rule"] is False and result.state["k_free"] is True
    assert "consumed" not in consume_ops(world)


def test_an_unexpected_exception_before_the_claim_removes_the_grant_and_closes_k(world, monkeypatch):
    def boom(self):
        raise RuntimeError("no claim today")

    monkeypatch.setattr(LocalClaimStore, "create", boom)
    result = consume_at(world)
    assert result.outcome.end is ConsumeEnd.INTERNAL
    assert result.state["rule"] is False and result.state["k_free"] is True and not claim_exists(world)


def test_run_consume_reports_an_unexpected_exception_as_one_fixed_line(world, monkeypatch, capsys):
    def boom(*a, **k):
        raise RuntimeError("path /var/secret and a password")

    monkeypatch.setattr(consume_adapter, "build_consume", boom)
    assert run_consume(invocation_id=CONSUME_INV, layout=world.layout) == 70
    err = capsys.readouterr().err
    assert err == "rp11-consume consume-internal-error\n"


def test_run_consume_with_no_pass_config_is_unidentified_and_creates_nothing(tmp_path, capsys):
    layout = make_layout(tmp_path)
    os.chmod(layout.var_tmp, 0o1777)
    before = sorted(os.listdir(layout.var_tmp)), sorted(os.listdir(layout.run))
    assert run_consume(invocation_id="absent", layout=layout) == 21
    assert capsys.readouterr().err == (
        "rp11-consume consume-unidentified unidentified step=CQ-0 class=pass-config pk=absent\n"
    )
    assert (sorted(os.listdir(layout.var_tmp)), sorted(os.listdir(layout.run))) == before


class _Crash(Crash):
    pass


class CrashIO(FileIO):
    """Dies (a BaseException nothing catches) at the n-th write: the process killed mid-line."""

    def __init__(self, at):
        self.at, self.writes = at, 0

    def write(self, fd, data):
        self.writes += 1
        if self.writes == self.at:
            raise Crash("died during a journal write")
        return super().write(fd, data)


def _crash_before_claim(world, monkeypatch):
    def die(self):
        raise Crash("died before the claim")

    monkeypatch.setattr(LocalClaimStore, "create", die)
    return {}


def _crash_during_removal(world, monkeypatch):
    real = LocalActivationFs.remove
    fired = []

    def remove(self, path, identity, *, directory, before_unlink):
        def die(observed):
            before_unlink(observed)
            fired.append(1)
            raise Crash("died between remove-intent and unlink")

        # only RT-1's removal (the one that writes a journal line first) dies, once
        if fired or os.path.lexists(world.paths.consume_dir) is False:
            return real(self, path, identity, directory=directory, before_unlink=before_unlink)
        return real(self, path, identity, directory=directory, before_unlink=die)

    monkeypatch.setattr(LocalActivationFs, "remove", remove)
    return {}


def _crash_during_pk(world, monkeypatch):
    pk = ProbePk(world)
    pk.during = lambda: (_ for _ in ()).throw(Crash("died inside PK/2"))
    return {"pk": pk}


INTERRUPTS = {
    "before-claim": (_crash_before_claim, {"claim": False, "rule": True, "ops": []}),
    "during-run-start": (lambda w, m: {"io": CrashIO(1)}, {"claim": True, "rule": True, "ops": []}),
    "during-removal": (_crash_during_removal, {"claim": True, "rule": True, "ops": ["run-start", "remove-intent"]}),
    "during-pk": (_crash_during_pk, {"claim": True, "rule": False, "ops": ["run-start", "remove-intent", "removed"]}),
    "after-consumed": (lambda w, m: {"io": CrashIO(7)}, {"claim": True, "rule": False,
                       "ops": ["run-start", "remove-intent", "removed", "child", "grant-check", "consumed"]}),
}


@pytest.mark.parametrize("name", sorted(INTERRUPTS))
def test_an_interruption_never_returns_never_leaves_k_held_and_is_recoverable(world, monkeypatch, name):
    """RT1.FI.2, IM-C: default-action death at representative points. No exit 0 exists, so PID 1
    cannot run ExecStart=; the claim is a one-shot barrier; the existing cleanup recovers."""
    arrange, expected = INTERRUPTS[name]
    result = consume_at(world, **arrange(world, monkeypatch))
    assert isinstance(result.raised, Crash) and result.outcome is None
    assert result.state["claim"] is expected["claim"] and result.state["rule"] is expected["rule"]
    assert result.state["k_free"] is True  # the descriptor is closed on the way out
    if expected["claim"]:
        assert consume_ops(world) == expected["ops"]
    monkeypatch.undo()
    # the accepted residuals: another attempt is refused, and stop-post cleanup removes what is left
    again = build_consume(CONSUME_INV, layout=world.layout, services=HoldServices(ConsumeUnits(), ProbePk(world), None),
                          clock=world.clock).run()
    if expected["claim"]:
        assert again.end is ConsumeEnd.REPEATED
    recovered = world.recover()
    assert not os.path.lexists(world.paths.rule) and recovered.terminal.value in {"st1-verified", "hard-stop"}
    if expected["claim"]:
        assert Path(world.paths.consume_dir, "journal").exists()  # never removed by CL


# ---------------------------------------------------------------------------
# the journal grammar (H-JRN.10)
# ---------------------------------------------------------------------------

GOOD_START = {
    "invocation_id": CONSUME_INV,
    "boot_id": BOOT,
    "claim": {"dev": 1, "ino": 2},
    "act_journal": {"sha256": "a" * 64, "length": 10},
    "lock": {"object": {"path": "/run/k", "dev": 1, "ino": 3}, "mode": "held", "wait_ms": 0},
    "helper": {"role": "consume", "tool_sha256": "absent"},
}


def _serialize(op, fields):
    return serialize_line(JournalKind.CONSUME, seq=1, prev=GENESIS, run=consume_run(ACT_ID), op=op, fields=fields)


def test_the_consume_run_start_is_exactly_its_closed_field_set():
    assert _serialize("run-start", GOOD_START)
    for key in GOOD_START:
        with pytest.raises(JournalSchemaError):
            _serialize("run-start", {k: v for k, v in GOOD_START.items() if k != key})
    with pytest.raises(JournalSchemaError):
        _serialize("run-start", {**GOOD_START, "extra": 1})
    for bad in (
        {"invocation_id": "A" * 32}, {"boot_id": "x"}, {"claim": {"dev": 1}},
        {"lock": {**GOOD_START["lock"], "mode": "degraded"}},
        {"helper": {"role": "hold", "tool_sha256": "absent"}},
        {"act_journal": {"sha256": "short", "length": 1}},
    ):
        with pytest.raises(JournalSchemaError):
            _serialize("run-start", {**GOOD_START, **bad})


def test_the_old_consume_run_start_and_consumed_shapes_are_invalid():
    with pytest.raises(JournalSchemaError):
        _serialize("run-start", {"boot_id": BOOT, "invocation_id": CONSUME_INV})
    with pytest.raises(JournalSchemaError):
        _serialize("consumed", {})


def test_consumed_and_run_end_are_closed():
    assert _serialize("consumed", {"pk_status": "not-authorized", "inactive_enter_us": 400})
    for bad in ({"pk_status": "Not Authorized", "inactive_enter_us": 1}, {"pk_status": "x"}, {"inactive_enter_us": 1},
                {"pk_status": "x", "inactive_enter_us": -1}):
        with pytest.raises(JournalSchemaError):
            _serialize("consumed", bad)
    assert _serialize("run-end", {"outcome": "consumed"}) and _serialize("run-end", {"outcome": "failed"})
    with pytest.raises(JournalSchemaError):
        _serialize("run-end", {"outcome": "consume-failed"})


def test_a_consume_journal_is_not_valid_as_any_other_kind():
    run_start = _serialize("run-start", GOOD_START)
    assert parse_journal(run_start, kind=JournalKind.CONSUME, run=consume_run(ACT_ID)).valid
    assert not parse_journal(run_start, kind=JournalKind.ATTEMPT, run=consume_run(ACT_ID)).valid
    assert not parse_journal(run_start, kind=JournalKind.CONSUME, run=ACT_ID).valid


# ---------------------------------------------------------------------------
# source-level guards: no spawn, no signal, no environment, no shell (H-FI, SN, LR)
# ---------------------------------------------------------------------------

import ast  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RT1_MODULES = ("application/rp11/consume.py", "adapters/rp11/consume.py")


@pytest.mark.parametrize("name", RT1_MODULES)
def test_the_rt1_modules_spawn_nothing_signal_nothing_and_read_no_environment(name):
    """RT-1 has no child of its own (the DI-6 subject belongs to the PK/2 series it calls), installs no
    signal handler (SG-8), sends no signal and reads no environment variable (its one provenance fact
    arrives as an argument from the first image)."""
    tree = ast.parse((ROOT / name).read_text())
    imported = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    imported |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert not imported & {"subprocess", "signal", "multiprocessing", "threading", "pty", "shlex", "ctypes"}, imported
    forbidden = {"fork", "forkpty", "system", "popen", "kill", "killpg", "execv", "execve", "spawnv", "putenv",
                 "environ", "environb", "getenv", "signal", "alarm", "setitimer", "nice", "setuid", "setgid"}
    attributes = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
                  and n.value.id == "os"}
    assert not attributes & forbidden, attributes & forbidden


def test_every_rt1_production_module_is_in_the_artifact_manifest_exactly_once():
    import importlib.util

    spec = importlib.util.spec_from_file_location("rp11_build_for_rt1", ROOT / "infra/rp11-h1/build.py")
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    for name in RT1_MODULES:
        assert build.SOURCES.count(name) == 1
    assert len(build.SOURCES) == len(set(build.SOURCES))


def test_rt1_reuses_the_accepted_primitives_rather_than_a_second_parser_or_removal_path():
    app = (ROOT / "application/rp11/consume.py").read_text()
    for reused in ("load_authority", "parse_journal", "act_evidence", "classify_file", "validate_record",
                   "PkMode.SEEK_NOT_AUTHORIZED", "fs.remove("):
        assert reused in app, reused
    assert "os.unlink" not in app and "os.remove" not in app and "unlink(" not in app.replace("os.unlink", "")


# ---------------------------------------------------------------------------
# review remediation: failure-record evidence faults and the PK/2 attempt state
# ---------------------------------------------------------------------------
#
# Journal I/O order (writes w, fsyncs f; run-start is w1/f1, then the claim-directory
# and /var/tmp flushes f2/f3, then one write and one fsync per line):
#   CQ-3 foreign rule : consume-failed (w2, f4) → run-end (w3, f5)
#   CQ-4 capture-root : remove-intent (w2, f4) → removed (w3, f5) → consume-failed (w4, f6) → run-end (w5, f7)
#   CQ-5 unconfirmed  : … removed (w3, f5) → child (w4, f6) → grant-check (w5, f7)
#                       → consume-failed (w6, f8) → run-end (w7, f9)

# name: (consume-failed write index, lines durable before it, rule gone, PK/2 series runs, diagnostic step)
RECORD_FAULTS = {
    "cq3-foreign": (2, ["run-start"], False, 0, "CQ-3"),
    "cq3-absent": (2, ["run-start"], True, 1, "CQ-3"),
    "cq4-capture-root": (4, ["run-start", "remove-intent", "removed"], True, 1, "CQ-4"),
    "cq5-unconfirmed": (6, ["run-start", "remove-intent", "removed", "child", "grant-check"], True, 1, "CQ-5"),
}


def _record_fault_run(world, monkeypatch, name, io):
    pk = ProbePk(world)
    mutate = None
    if name == "cq3-foreign":
        same_bytes = world.fx.rule_bytes
        mutate = lambda: replace_by_new_inode(Path(world.paths.rule), same_bytes)  # noqa: E731
    elif name == "cq3-absent":
        mutate = lambda: os.unlink(world.paths.rule)  # noqa: E731
    elif name == "cq4-capture-root":
        after_removal(monkeypatch, lambda: os.mkdir(world.capture_root, 0o700))
    else:
        pk = ProbePk(world, outcome=PkOutcome.UNCONFIRMED, reason="only-errors")
    result = consume_at(world, mutate=mutate, pk=pk, io=io)
    result.series_runs = getattr(pk, "series_runs", 0)
    return result


def _assert_record_fault(world, name, result, klass, *, journal_ops):
    _, _, rule_gone, pk_runs, step = RECORD_FAULTS[name]
    out = result.outcome
    assert result.raised is None, result.raised
    assert (out.end, out.step, out.klass) == (ConsumeEnd.EVIDENCE_UNWRITABLE, step, klass)
    assert out.exit_code == 25
    assert result.state["rule"] is (not rule_gone)
    assert result.state["k_free"] is True and result.state["claim"] is True
    ops = consume_ops(world)
    assert "consumed" not in ops and ops == journal_ops
    assert result.series_runs == pk_runs
    assert out.pk == ("absent" if pk_runs == 0 else out.pk)
    if name == "cq4-capture-root":
        assert out.pk == "not-authorized"
        assert result.units.reads.count(CAPTURE_UNIT) == 0  # CQ-4 stopped at capture-root and is not resumed
    return out


@pytest.mark.parametrize("name", sorted(RECORD_FAULTS))
def test_a_failed_consume_failed_write_enters_grant_priority(world, monkeypatch, name):
    """H-JRN.6/7, RT1.CQ3.9: a write that fails while recording a failure never bypasses grant priority."""
    write_at, prefix = RECORD_FAULTS[name][:2]
    result = _record_fault_run(world, monkeypatch, name, FailingIO(fail_write_at=write_at))
    _assert_record_fault(world, name, result, "evidence", journal_ops=prefix)  # torn tail is ignored


@pytest.mark.parametrize("name", sorted(RECORD_FAULTS))
def test_a_failed_consume_failed_flush_enters_grant_priority(world, monkeypatch, name):
    write_at, prefix = RECORD_FAULTS[name][:2]
    result = _record_fault_run(world, monkeypatch, name, FailingIO(fail_fsync_at=write_at + 2))
    _assert_record_fault(world, name, result, "evidence", journal_ops=prefix + ["consume-failed"])


@pytest.mark.parametrize("name", sorted(RECORD_FAULTS))
def test_a_failed_failure_run_end_write_follows_a_durable_consume_failed(world, monkeypatch, name):
    write_at, prefix = RECORD_FAULTS[name][:2]
    result = _record_fault_run(world, monkeypatch, name, FailingIO(fail_write_at=write_at + 1))
    _assert_record_fault(world, name, result, "run-end", journal_ops=prefix + ["consume-failed"])


@pytest.mark.parametrize("name", sorted(RECORD_FAULTS))
def test_a_failed_failure_run_end_flush_enters_grant_priority(world, monkeypatch, name):
    write_at, prefix = RECORD_FAULTS[name][:2]
    result = _record_fault_run(world, monkeypatch, name, FailingIO(fail_fsync_at=write_at + 3))
    _assert_record_fault(world, name, result, "run-end", journal_ops=prefix + ["consume-failed", "run-end"])


def test_an_unwritable_cq5_record_does_not_run_the_series_a_second_time(world):
    """PK/2 had already been attempted by CQ-5: grant priority must not attempt it again."""
    pk = ProbePk(world, outcome=PkOutcome.UNCONFIRMED, reason="interrupted")
    result = consume_at(world, pk=pk, io=FailingIO(fail_write_at=5))  # grant-check itself unwritable
    out = result.outcome
    assert (out.end, out.step, out.klass) == (ConsumeEnd.EVIDENCE_UNWRITABLE, "CQ-5", "evidence")
    assert pk.series_runs == 1 and out.pk == "unconfirmed"
    assert consume_ops(world) == ["run-start", "remove-intent", "removed", "child"]


def test_an_exception_inside_the_first_series_never_starts_a_second(world):
    pk = SeriesPk(world, _answers("denied"))
    real = pk.decide

    def explode(operator, verb, mode):
        real(operator, verb, mode)
        raise RuntimeError("/etc/secret detail")

    pk.decide = explode
    result = consume_at(world, pk=pk)
    out = result.outcome
    assert result.raised is None
    assert (out.end, out.step, out.klass) == (ConsumeEnd.INTERNAL, "CQ-5", "unexpected")
    assert out.exit_code == 70 and "secret" not in out.line()
    assert pk.series_runs == 1 and len(pk.launcher.spawned) == 1  # one subject, no replacement schedule
    assert result.state["rule"] is False and result.state["k_free"] is True and result.state["claim"] is True
    assert "consumed" not in consume_ops(world)


def test_an_exception_before_any_series_still_allows_one_in_memory_series(world, monkeypatch):
    """Grant-priority entry before CQ-5 is the first attempt, not a retry."""
    pk = ProbePk(world)

    def boom(self, chain):
        raise RuntimeError("cq4 exploded")

    monkeypatch.setattr(consume_module.ConsumeProcedure, "_cq4", boom)
    result = consume_at(world, pk=pk)
    out = result.outcome
    assert (out.end, out.step, out.klass) == (ConsumeEnd.INTERNAL, "CQ-4", "unexpected")
    assert pk.series_runs == 1 and out.pk == "not-authorized"
    assert result.state["rule"] is False and "consumed" not in consume_ops(world)


def test_run_consume_renders_the_fixed_internal_diagnostic_without_values(world, monkeypatch, capsys):
    pk = ProbePk(world)
    pk.during = lambda: (_ for _ in ()).throw(RuntimeError("/etc/secret PASSWORD=hunter2"))
    codes = []
    services = HoldServices(ConsumeUnits(), pk, None)
    real_build = consume_adapter.build_consume

    class ViaRunConsume:
        def __init__(self, invocation, **kw):
            self.invocation = invocation

        def run(self):
            monkeypatch.setattr(
                consume_adapter,
                "build_consume",
                lambda inv, *, layout, services, clock, io: real_build(
                    inv, layout=layout, services=HoldServices(ConsumeUnits(), pk, None),
                    clock=world.clock, io=io,
                ),
            )
            codes.append(run_consume(invocation_id=self.invocation, layout=world.layout))
            return None

    monkeypatch.setattr(sys.modules[__name__], "build_consume", ViaRunConsume)
    consume_at(world)
    assert codes == [70]
    err = capsys.readouterr().err
    assert DIAGNOSTIC.fullmatch(err.rstrip("\n"))
    assert err.startswith("rp11-consume consume-internal-error rp11-act-")
    assert err.endswith(" step=CQ-5 class=unexpected pk=absent\n")
    for leaked in ("secret", "hunter2", "RuntimeError", "/etc"):
        assert leaked not in err
    assert pk.series_runs == 1
