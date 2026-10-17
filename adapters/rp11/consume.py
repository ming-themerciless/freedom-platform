"""Composition root and filesystem adapters of ``consume`` (RT-1).

The role takes no operand. ``run_consume`` builds the adapters for the fixed
production ``Layout`` and runs ``application.rp11.consume.ConsumeProcedure`` once.
It installs no signal handler (SG-8): the default action ends it, PID 1's finite
``TimeoutStartUSec`` is the class-M terminator, and a process that ends that way
never exits 0, so ``ExecStart=`` is not executed.

Output is one bounded ``rp11-consume …`` line of closed tokens; an unexpected
exception is one fixed line naming nothing from the exception, and exits 70.

The claim (CQ-2) is ``<var_tmp>/<id>-consume-evidence``: created ``0700`` with no
replace (the barrier), its journal created exclusively ``0600``, set ``0644``,
then the directory set ``0755``. ``EEXIST`` opens nothing.
"""

from __future__ import annotations

import hashlib
import os
import stat
import sys
from collections.abc import Callable

from adapters.systemd.bus import BusConnection
from application.rp11.attribution import Owner
from application.rp11.canonical import ABSENT
from application.rp11.consume import (
    ActJournalRead,
    Claim,
    ClaimEvidenceFailure,
    ClaimExists,
    ClaimNotMade,
    ConsumePorts,
    ConsumeProcedure,
    PassRead,
)
from application.rp11.journal import JournalKind, consume_run
from application.rp11.paths import ActivationPaths, Layout
from application.rp11.ports import EvidenceSink, EvidenceWriteError

from .fsops import (
    _DIR_FLAGS,
    _FILE_FLAGS,
    FileIO,
    JournalAppender,
    LocalActivationFs,
    LocalHostFacts,
    LocalLock,
    LocalRecordStore,
    _read_capped,
    close_quietly,
    open_dir,
    split,
)
from .holdfs import LocalHoldHost
from .process import SystemClock
from .stop_post import StopPostServices

EX_INTERNAL = 70
TOOL_MAX_BYTES = 1 << 20
_JOURNAL_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_APPEND | os.O_NOFOLLOW | os.O_CLOEXEC


class LocalConsumeHost:
    """``ConsumeHost``: no-follow, descriptor-based reads of the two inputs CQ-0 needs."""

    def __init__(self, owner: Owner) -> None:
        self._owner = owner

    def read_pass_config(self, path: str, *, max_bytes: int) -> PassRead | None:
        parent, name = split(path)
        try:
            pfd = open_dir(parent)
        except OSError:
            return None
        try:
            pinfo = os.fstat(pfd)
            if pinfo.st_uid != self._owner.uid or pinfo.st_mode & 0o022:
                return None
            fd = os.open(name, _FILE_FLAGS, dir_fd=pfd)
            try:
                info = os.fstat(fd)
                if not self._is_root_file(info, 0o644) or info.st_size > max_bytes:
                    return None
                data = _read_capped(fd, info.st_size)
                if len(data) != info.st_size:
                    return None
                return PassRead(data, info.st_dev, info.st_ino)
            finally:
                close_quietly(fd)
        except OSError:
            return None
        finally:
            close_quietly(pfd)

    def read_act_journal(self, directory: str, *, max_bytes: int) -> ActJournalRead | None:
        try:
            dfd = open_dir(directory)
        except OSError:
            return None
        try:
            dinfo = os.fstat(dfd)
            if not stat.S_ISDIR(dinfo.st_mode) or stat.S_IMODE(dinfo.st_mode) != 0o700:
                return None
            fd = os.open("journal", _FILE_FLAGS, dir_fd=dfd)
            try:
                info = os.fstat(fd)
                if not self._is_root_file(info, 0o644) or info.st_size > max_bytes:
                    return None
                data = _read_capped(fd, info.st_size)
                if len(data) != info.st_size:
                    return None
                return ActJournalRead(data, dinfo.st_uid)
            finally:
                close_quietly(fd)
        except OSError:
            return None
        finally:
            close_quietly(dfd)

    def _is_root_file(self, info: os.stat_result, mode: int) -> bool:
        return (
            stat.S_ISREG(info.st_mode)
            and (info.st_uid, info.st_gid) == (self._owner.uid, self._owner.gid)
            and stat.S_IMODE(info.st_mode) == mode
            and info.st_nlink == 1
        )


class _LocalClaim:
    def __init__(self, vfd: int, cfd: int, appender: JournalAppender, identity: tuple[int, int], io: FileIO) -> None:
        self._vfd, self._cfd = vfd, cfd
        self._appender = appender
        self.identity = identity
        self._io = io

    @property
    def sink(self) -> EvidenceSink:
        return self._appender

    def flush_directories(self) -> None:
        """CQ-2 durability point after the journal: the claim directory, then ``/var/tmp``."""
        try:
            self._io.fsync(self._cfd)
            self._io.fsync(self._vfd)
        except OSError as exc:
            raise EvidenceWriteError(str(exc)) from exc

    def close(self) -> None:
        self._appender.close()
        close_quietly(self._cfd)
        close_quietly(self._vfd)


class LocalClaimStore:
    """CQ-2: ``<var_tmp>/<activation_id>-consume-evidence`` and its journal."""

    def __init__(self, *, var_tmp: str, activation_id: str, owner: Owner, io: FileIO | None = None) -> None:
        self._var_tmp = var_tmp
        self._name = f"{activation_id}-consume-evidence"
        self._activation_id = activation_id
        self._owner = owner
        self._io = io or FileIO()

    def create(self) -> Claim:
        try:
            vfd = open_dir(self._var_tmp)
        except OSError:
            raise ClaimNotMade("/var/tmp unreachable") from None
        try:
            vinfo = os.fstat(vfd)
            if (
                not stat.S_ISDIR(vinfo.st_mode)
                or (vinfo.st_uid, vinfo.st_gid) != (self._owner.uid, self._owner.gid)
                or stat.S_IMODE(vinfo.st_mode) != 0o1777
            ):
                raise ClaimNotMade("/var/tmp is not a root 1777 directory")
            try:
                os.mkdir(self._name, 0o700, dir_fd=vfd)  # the barrier: no replace
            except FileExistsError:
                raise ClaimExists(self._name) from None
            except OSError:
                raise ClaimNotMade("claim directory could not be created") from None
        except BaseException:
            close_quietly(vfd)
            raise
        cfd = jfd = None
        try:
            cfd = os.open(self._name, _DIR_FLAGS, dir_fd=vfd)
            info = os.fstat(cfd)
            if (
                not stat.S_ISDIR(info.st_mode)
                or (info.st_uid, info.st_gid) != (self._owner.uid, self._owner.gid)
                or stat.S_IMODE(info.st_mode) != 0o700
                or info.st_nlink != 2
            ):
                raise ClaimEvidenceFailure("claim directory is not a fresh root 0700 directory")
            jfd = os.open("journal", _JOURNAL_FLAGS, 0o600, dir_fd=cfd)
            os.fchmod(jfd, 0o644)
            os.fchmod(cfd, 0o755)  # once the journal exists
        except (OSError, ClaimEvidenceFailure) as exc:
            if jfd is not None:
                close_quietly(jfd)
            if cfd is not None:
                close_quietly(cfd)
            close_quietly(vfd)
            if isinstance(exc, ClaimEvidenceFailure):
                raise
            raise ClaimEvidenceFailure("claim directory or journal could not be made") from None
        appender = JournalAppender(
            jfd, kind=JournalKind.CONSUME, run=consume_run(self._activation_id), io=self._io
        )
        return _LocalClaim(vfd, cfd, appender, (info.st_dev, info.st_ino), self._io)


def build_ports(
    paths: ActivationPaths,
    layout: Layout,
    *,
    services,
    clock,
    consume_host: LocalConsumeHost,
    io: FileIO | None = None,
) -> ConsumePorts:
    fs = LocalActivationFs(layout.owner)
    tool = fs.read_root_file(layout.tool, max_bytes=TOOL_MAX_BYTES, mode=0o644)
    return ConsumePorts(
        fs=fs,
        records=LocalRecordStore(paths.record_dir, layout.owner),
        lock=LocalLock(paths.lock_dir, layout.owner, clock),
        claims=LocalClaimStore(
            var_tmp=layout.var_tmp, activation_id=paths.activation_id, owner=layout.owner, io=io
        ),
        host_fs=LocalHoldHost(layout.owner),
        host=LocalHostFacts(boot_id_file=layout.boot_id_file, mountinfo=layout.mountinfo, run=layout.run),
        consume_host=consume_host,
        services=services,
        tool_sha256=hashlib.sha256(tool).hexdigest() if tool is not None else ABSENT,
    )


def build_consume(
    invocation_id: str,
    *,
    layout: Layout,
    services,
    clock,
    io: FileIO | None = None,
) -> ConsumeProcedure:
    consume_host = LocalConsumeHost(layout.owner)
    return ConsumeProcedure(
        layout,
        invocation_id=invocation_id,
        ports_for=lambda paths: build_ports(
            paths, layout, services=services, clock=clock, consume_host=consume_host, io=io
        ),
        pass_host=consume_host,
    )


def _system_bus() -> BusConnection:
    """Connected on first use, so CQ-0 … CQ-3 never touch the bus."""
    from adapters.systemd.jeepney_bus import connect_system_bus

    return connect_system_bus()


def run_consume(
    *,
    invocation_id: str,
    layout: Layout | None = None,
    connector: Callable[[], BusConnection] | None = None,
    io: FileIO | None = None,
) -> int:
    try:
        connector = connector or _system_bus
        clock = SystemClock()
        procedure = build_consume(
            invocation_id,
            layout=layout or Layout(),
            services=StopPostServices(connector, clock),
            clock=clock,
            io=io,
        )
        outcome = procedure.run()
    except Exception:  # noqa: BLE001 - fail closed with a fixed, value-free line
        print("rp11-consume consume-internal-error", file=sys.stderr)
        return EX_INTERNAL
    print(outcome.line(), file=sys.stderr)
    return outcome.exit_code
