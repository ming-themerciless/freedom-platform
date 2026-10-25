"""Executor OS-6 ownership records: durable, descriptor-safe, and blocking on any doubt."""

from __future__ import annotations

import errno
import json
import os

import pytest

from adapters.executor.ownership import (
    ACTIVE_NAME,
    BOUND,
    CLEANUP,
    MAX_ENTRIES,
    PREPARED,
    START_SENT,
    FileOps,
    OwnershipStore,
    Record,
    StoreError,
    decode,
    unit_name,
)

BOOT = "11111111-2222-3333-4444-555555555555"
INVOCATION = "ab" * 16


def cgroup_for(record: Record) -> str:
    return f"/user.slice/user-1.slice/user@1.service/app.slice/{record.unit}"


def bound(record: Record | None = None) -> Record:
    record = record or Record.fresh(BOOT)
    return record.to(BOUND, invocation_id=INVOCATION, cgroup=cgroup_for(record), cgroup_id=77)


@pytest.fixture
def directory(tmp_path):
    path = tmp_path / "state"
    path.mkdir(mode=0o700)
    return path


def store_for(directory, ops=None) -> OwnershipStore:
    return OwnershipStore(str(directory), ops=ops)


# --- format --------------------------------------------------------------------------


def test_a_record_round_trips_in_every_state():
    fresh = Record.fresh(BOOT)
    for record in (fresh, fresh.to(START_SENT), bound(fresh), bound(fresh).to(CLEANUP)):
        assert decode(record.filename, record.encode()) == record
    assert fresh.unit == unit_name(fresh.nonce) and fresh.unit.startswith("freedom-executor-stop-")


@pytest.mark.parametrize(
    "mutate",
    [
        lambda v: v.update(v=2),
        lambda v: v.update(v=True),
        lambda v: v.update(extra=1),
        lambda v: v.pop("boot"),
        lambda v: v.update(boot="not-a-boot-id"),
        lambda v: v.update(nonce="0" * 32),  # name/nonce mismatch
        lambda v: v.update(unit="freedom-executor-stop-other.service"),
        lambda v: v.update(state="done"),
        lambda v: v.update(state=PREPARED, invocation_id=INVOCATION),  # nonterminal-early states carry no binding
        lambda v: v.update(invocation_id="xyz"),
        lambda v: v.update(cgroup="/user.slice/../../etc/freedom-executor-stop-x.service"),
        lambda v: v.update(cgroup="/system.slice/other.service"),  # not our unit's cgroup
        lambda v: v.update(cgroup="/user.slice/other.service", cgroup_id=3),  # basename is not the unit
        lambda v: v.update(cgroup_id=0),  # cgroup without identity
        lambda v: v.update(cgroup_id=-1),
        lambda v: v.update(cgroup_id="7"),
    ],
)
def test_a_damaged_or_foreign_record_is_not_decoded(mutate):
    record = bound()
    value = json.loads(record.encode())
    mutate(value)
    assert decode(record.filename, json.dumps(value).encode()) is None


def test_non_ascii_oversized_and_non_object_content_is_not_decoded():
    record = bound()
    assert decode(record.filename, b"[]") is None
    assert decode(record.filename, b"\xff\xfe") is None
    assert decode(record.filename, record.encode() + b" " * 5000) is None
    assert decode("rec-zz.json", record.encode()) is None


# --- durability -----------------------------------------------------------------------


def test_put_listing_and_remove_round_trip_and_leave_nothing_behind(directory):
    store, record = store_for(directory), Record.fresh(BOOT)
    assert not store.listing().blocking
    store.put(record)
    store.put(record.to(START_SENT))  # replacement
    listing = store.listing()
    assert listing.records == (record.to(START_SENT),) and listing.blocking and not listing.damaged
    store.remove(record)
    store.remove(record)  # idempotent
    assert not store.listing().blocking and os.listdir(directory) == []


def test_every_transition_is_synchronized_file_rename_directory(directory):
    calls = []

    class Spy(FileOps):
        def fsync(self, fd):
            calls.append(("fsync", os.fstat(fd).st_mode & 0o170000))
            super().fsync(fd)

        def rename(self, source, target, dir_fd):
            calls.append(("rename", target))
            super().rename(source, target, dir_fd)

    record = Record.fresh(BOOT)
    store_for(directory, Spy()).put(record)
    assert [c[0] for c in calls] == ["fsync", "rename", "fsync"]
    assert calls[0][1] == 0o100000 and calls[2][1] == 0o040000  # the file, then the directory


def test_a_short_write_is_completed_not_trusted(directory):
    class Short(FileOps):
        def write(self, fd, data):
            return super().write(fd, data[:7])

    record = bound()
    store_for(directory, Short()).put(record)
    assert store_for(directory).listing().records == (record,)


@pytest.mark.parametrize("failing", ["create", "write", "fsync", "rename", "zero-write"])
def test_every_write_path_failure_is_a_store_error_and_leaves_no_record(directory, failing):
    class Broken(FileOps):
        def create(self, name, dir_fd):
            if failing == "create":
                raise OSError(errno.ENOSPC, "full")
            return super().create(name, dir_fd)

        def write(self, fd, data):
            if failing == "write":
                raise OSError(errno.ENOSPC, "full")
            if failing == "zero-write":
                return 0
            return super().write(fd, data)

        def fsync(self, fd):
            if failing == "fsync":
                raise OSError(errno.EIO, "io")
            super().fsync(fd)

        def rename(self, source, target, dir_fd):
            if failing == "rename":
                raise OSError(errno.EIO, "io")
            super().rename(source, target, dir_fd)

    with pytest.raises(StoreError):
        store_for(directory, Broken()).put(Record.fresh(BOOT))
    assert os.listdir(directory) == []  # the temporary is removed too


def test_directory_sync_failure_after_the_rename_is_reported_and_the_record_blocks(directory):
    class DirSync(FileOps):
        def fsync(self, fd):
            if os.fstat(fd).st_mode & 0o170000 == 0o040000:
                raise OSError(errno.EIO, "io")
            super().fsync(fd)

    record = Record.fresh(BOOT)
    with pytest.raises(StoreError):
        store_for(directory, DirSync()).put(record)
    assert store_for(directory).listing().records == (record,)  # possibly durable: so it blocks, never silently absent


def test_a_missing_or_untrusted_directory_is_a_store_error(tmp_path):
    with pytest.raises(StoreError):
        OwnershipStore(str(tmp_path / "absent")).listing()
    loose = tmp_path / "loose"
    loose.mkdir(mode=0o755)
    loose.chmod(0o755)
    with pytest.raises(StoreError):
        OwnershipStore(str(loose)).listing()
    target = tmp_path / "target"
    target.mkdir(mode=0o700)
    link = tmp_path / "link"
    link.symlink_to(target)
    with pytest.raises(StoreError):
        OwnershipStore(str(link)).listing()
    with pytest.raises(StoreError):
        OwnershipStore(str(target), uid=os.getuid() + 1).listing()


def test_check_writable_is_a_real_write_and_leaves_nothing(directory):
    store_for(directory).check_writable()
    assert os.listdir(directory) == []

    class Full(FileOps):
        def write(self, fd, data):
            raise OSError(errno.ENOSPC, "full")

    with pytest.raises(StoreError):
        store_for(directory, Full()).check_writable()
    assert os.listdir(directory) == []


def test_remove_failure_keeps_the_record(directory):
    record = Record.fresh(BOOT)
    store_for(directory).put(record)

    class NoUnlink(FileOps):
        def unlink(self, name, dir_fd):
            raise OSError(errno.EIO, "io")

    with pytest.raises(StoreError):
        store_for(directory, NoUnlink()).remove(record)
    assert store_for(directory).listing().records == (record,)


# --- trust boundary --------------------------------------------------------------------


def plant(directory, name, data=b"{}", mode=0o600):
    path = directory / name
    path.write_bytes(data)
    path.chmod(mode)
    return path


def test_every_entry_that_is_not_a_well_formed_private_record_blocks_and_is_reported(directory):
    record = Record.fresh(BOOT)
    plant(directory, "notes.txt")
    plant(directory, "rec-" + "0" * 32 + ".json", b"garbage")
    plant(directory, record.filename, record.encode(), mode=0o644)  # right bytes, wrong mode
    listing = store_for(directory).listing()
    assert listing.blocking and listing.records == () and sorted(listing.damaged) == sorted(
        ["notes.txt", "rec-" + "0" * 32 + ".json", record.filename])


def test_the_slot_is_one_fixed_name_whatever_the_nonce(directory):
    assert Record.fresh(BOOT).filename == Record.fresh(BOOT).filename == ACTIVE_NAME == "active.json"


def test_links_and_directories_are_never_followed_or_read_as_the_active_slot(directory, tmp_path):
    record = Record.fresh(BOOT)
    outside = tmp_path / "outside.json"
    outside.write_bytes(record.encode())
    outside.chmod(0o600)
    os.symlink(outside, directory / ACTIVE_NAME)
    assert store_for(directory).listing().records == () and store_for(directory).listing().damaged == (ACTIVE_NAME,)
    (directory / ACTIVE_NAME).unlink()
    os.mkdir(directory / ACTIVE_NAME)
    assert store_for(directory).listing().records == () and store_for(directory).listing().damaged == (ACTIVE_NAME,)
    os.rmdir(directory / ACTIVE_NAME)
    plant(directory, ACTIVE_NAME, record.encode())
    os.link(directory / ACTIVE_NAME, tmp_path / "second-link")
    assert store_for(directory).listing().records == () and store_for(directory).listing().damaged == (ACTIVE_NAME,)


def test_a_record_under_any_other_name_is_never_decoded_or_adopted(directory):
    record = bound()
    other = f"rec-{record.nonce}.json"
    plant(directory, other, record.encode())  # the earlier per-nonce layout, or a planted copy
    listing = store_for(directory).listing()
    assert listing.records == () and listing.damaged == (other,) and listing.blocking
    assert decode(other, record.encode()) is None and decode(ACTIVE_NAME, record.encode()) == record


def test_leftover_temporaries_are_not_records_and_only_a_stale_one_is_removed(directory):
    import time

    plant(directory, ".tmp-0123456789abcdef", b"partial")
    plant(directory, ".tmp-fedcba9876543210", b"partial")
    os.utime(directory / ".tmp-0123456789abcdef", (time.time() - 3600, time.time() - 3600))
    store = store_for(directory)
    listing = store.listing()
    assert not listing.blocking and sorted(listing.stray_temporaries) == [".tmp-0123456789abcdef", ".tmp-fedcba9876543210"]
    assert store.remove_stale_temporary(".tmp-fedcba9876543210", time.time()) is False  # young: possibly a write in progress
    assert store.remove_stale_temporary(".tmp-0123456789abcdef", time.time()) is True
    assert store.remove_stale_temporary(ACTIVE_NAME, time.time()) is False  # not a temporary
    assert store.remove_stale_temporary(".tmp-aaaaaaaaaaaaaaaa", time.time()) is False  # absent
    assert os.listdir(directory) == [".tmp-fedcba9876543210"]


def test_only_our_own_regular_files_are_ever_removed_as_temporaries(directory, tmp_path):
    import time

    os.symlink(tmp_path, directory / ".tmp-0000000000000000")
    os.mkdir(directory / ".tmp-1111111111111111")
    store = store_for(directory)
    far_future = time.time() + 10_000_000
    assert store.remove_stale_temporary(".tmp-0000000000000000", far_future) is False
    assert store.remove_stale_temporary(".tmp-1111111111111111", far_future) is False
    assert sorted(os.listdir(directory)) == [".tmp-0000000000000000", ".tmp-1111111111111111"]  # a link and a directory survive
    with pytest.raises(StoreError):
        OwnershipStore(str(directory), uid=os.getuid() + 1).remove_stale_temporary(".tmp-0000000000000000", far_future)  # not our directory


def test_junk_created_before_the_record_cannot_hide_it_and_work_stays_bounded(directory, monkeypatch):
    for index in range(3 * MAX_ENTRIES):  # far past the limit, and created *first*
        plant(directory, f"a-junk-{index:05d}")
    store = store_for(directory)
    record = bound()
    store.put(record)
    opens = []
    real = os.open
    monkeypatch.setattr(os, "open", lambda *a, **k: (opens.append(a[0]), real(*a, **k))[1])
    listing = store.listing()
    assert listing.records == (record,)  # read by name, wherever a scan would have stopped
    assert listing.blocking and "<overflow>" in listing.damaged
    assert len(listing.damaged) <= MAX_ENTRIES + 1  # memory is bounded by the scan limit, not by the directory
    assert opens.count(ACTIVE_NAME) == 1 and len(opens) <= 2  # the directory and the slot: junk is named, never opened


def test_the_slot_is_replaced_in_place_and_removed_without_disturbing_other_entries(directory):
    store = store_for(directory)
    record = Record.fresh(BOOT)
    store.put(record)
    store.put(record.to(START_SENT))
    store.put(bound(record.to(START_SENT)))
    assert os.listdir(directory) == [ACTIVE_NAME]
    plant(directory, "junk")
    store.remove(bound(record))
    assert os.listdir(directory) == ["junk"]
