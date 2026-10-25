"""The executor supervisor package: prerequisites and code trust are verified (never edited), the fragment is installed once,
and removal happens only through the supervisor's drain."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from adapters.executor.protocol import DRAIN_EMPTY, DRAIN_PENDING, DRAIN_REQUEST, GREETING
from tools import executor_supervisor_install as tool
from tools.executor_supervisor_install import (
    ACCOUNT, EXIT_CONFLICT, EXIT_IO, EXIT_OK, EXIT_PENDING, EXIT_REFUSED, EXIT_VERIFY_FAILED, SA2, UNIT, DrainSession, Installer,
    SupervisorAbsent, main,
)

REPO = Path(__file__).resolve().parents[1]
ME = os.getuid()
ACCOUNT_UID = ME + 4000
SUDO_OK = f"User {ACCOUNT} may run the following commands on host:\n    (root) NOPASSWD: {SA2}\n"
PLATFORM = "opt/freedom-blades/platform"
VENV = "opt/freedom-blades/runtime/venv-web"
HOME_BIN = "opt/freedom-blades/runtime/pyhome/bin"


class FakeSession:
    """What the installer needs of a drain connection, scripted by the test."""

    def __init__(self, world):
        self.world, self.closed = world, False

    def request(self):
        self.world.events.append("drain-request")
        if self.world.drain_reply == "garbage":
            raise tool.Failure(EXIT_PENDING, "drain-unconfirmed")
        if self.world.on_drain is not None:
            self.world.on_drain()
        return self.world.drain_reply == "empty"

    def alive(self):
        return self.world.session_alive

    def close(self):
        self.closed = True
        self.world.events.append("drain-close")


class World:
    """A re-rooted filesystem plus a *stateful* model of the system manager: what it has loaded, enabled and is running.

    ``daemon-reload`` makes the manager load whatever is on disk (or nothing); ``show`` reports ``NeedDaemonReload`` from the
    difference, so an install that does not reload (or whose reload fails or is a no-op) cannot look successful.
    """

    def __init__(self, tmp_path):
        self.root = tmp_path / "root"
        self.calls: list[list[str]] = []
        self.events: list[str] = []
        self.sudo = SUDO_OK
        self.units = ""
        self.units_code = 0
        self.manager = "active"
        self.supervisor = "active"
        self.loaded: bytes | None = None  # the fragment the system manager has loaded
        self.dropins = ""
        self.environment, self.user = "PATH=/usr/bin:/bin", ACCOUNT  # what the manager reports as the effective properties
        self.running: bytes | None = None  # the configuration the running supervisor was started from
        self.reload_results: list[int] = []  # scripted exit codes for successive daemon-reloads (default 0)
        self.reload_noop = False  # a reload that exits 0 but loads nothing
        self.enable_fails = False
        self.restart_fails = False  # a restart that leaves the unit not running
        self.after_reload = None  # a hook that runs after each daemon-reload has taken effect (to inject a later fault)
        self.drain_reply, self.session_alive, self.absent, self.on_drain = "empty", True, False, None
        self.after_stop = None  # a hook that runs when the supervisor is stopped (to inject a race)
        self.stop_code = 0
        self.sessions: list[FakeSession] = []
        self.faults: list[tuple[str, int, BaseException]] = []  # (systemctl verb, nth call of that verb, what the runner raises)
        self.verb_calls: dict[str, int] = {}
        for rel in ("etc/systemd/system/multi-user.target.wants", "var/lib/systemd/linger", "home/exec", f"{VENV}/bin", HOME_BIN,
                    f"{VENV}/lib/python3.12/site-packages/jeepney", "opt/freedom-blades/runtime/pyhome/lib/python3.12",
                    f"{PLATFORM}/infra/executor", "proc/4242"):
            (self.root / rel).mkdir(parents=True)
        for rel in tool.CODE_TREES:
            (self.root / PLATFORM / rel).mkdir(parents=True)
            (self.root / PLATFORM / rel / "mod.py").write_text("x")
            (self.root / PLATFORM / rel / "pkg").mkdir()
            (self.root / PLATFORM / rel / "pkg" / "inner.py").write_text("y")
        shutil.copy(REPO / tool.SOURCE_RELATIVE, self.root / PLATFORM / tool.SOURCE_RELATIVE)
        site = self.root / VENV / "lib/python3.12/site-packages"
        (site / "jeepney" / "__init__.py").write_text("")
        (site / "jeepney" / "io.py").write_text("")
        (site / "_virtualenv.pth").write_text("import _virtualenv")
        (self.root / HOME_BIN / "python3.12").write_text("")
        (self.root / VENV / "bin" / "python").symlink_to("../../pyhome/bin/python3.12")
        (self.root / VENV / "pyvenv.cfg").write_text("home = /opt/freedom-blades/runtime/pyhome/bin\nversion_info = 3.12\n")
        (self.root / "var/lib/systemd/linger" / ACCOUNT).write_text("")
        for path in [*self.root.rglob("*"), self.root]:
            if not path.is_symlink():
                path.chmod(0o755 if path.is_dir() else 0o644)
        self.home = self.root / "home/exec"
        self.repo = self.root / PLATFORM

    @property
    def state(self) -> Path:
        return self.root / f"var/lib/{tool.STATE_NAME}/invocations"

    @property
    def fragment(self) -> Path:
        return self.root / "etc/systemd/system" / tool.UNIT

    def disk(self) -> bytes | None:
        return self.fragment.read_bytes() if self.fragment.exists() else None

    def runner(self, argv):
        self.calls.append(list(argv))
        if argv[:2] == ["sudo", "-n"]:
            return 0, self.sudo
        if argv[0] == "systemctl":
            return self._systemctl(argv[1:])
        if "list-units" in argv:
            return self.units_code, self.units
        return 0, ""

    def _systemctl(self, args):
        verb = args[0]
        self.verb_calls[verb] = self.verb_calls.get(verb, 0) + 1
        for fault in self.faults:
            if fault[0] == verb and fault[1] == self.verb_calls[verb]:
                self.faults.remove(fault)
                raise fault[2]
        link = self.root / "etc/systemd/system/multi-user.target.wants" / tool.UNIT
        if verb == "show" and args[1].startswith("user@"):
            return 0, self.manager + "\n"
        if verb == "show":
            on_disk = self.disk()
            values = {"ActiveState": self.supervisor, "MainPID": "4242" if self.supervisor == "active" else "0",
                      "LoadState": "loaded" if self.loaded is not None else "not-found",
                      "FragmentPath": f"{tool.UNIT_DIR}/{tool.UNIT}" if self.loaded is not None else "",
                      "NeedDaemonReload": "no" if on_disk == self.loaded else "yes", "DropInPaths": self.dropins,
                      "User": self.user, "Group": ACCOUNT, "Environment": self.environment}
            wanted = [item[2:] for item in args[2:] if item.startswith("-p")]
            mode = self.state_fault() if wanted == ["ActiveState"] and self.state_fault else None
            if mode == "fail":
                return 1, ""
            if mode in ("empty", "garbage", "missing"):
                return 0, {"empty": "ActiveState=\n", "garbage": "ActiveState=bogus\n", "missing": ""}[mode]
            return 0, "".join(f"{name}={values[name]}\n" for name in wanted)
        if verb == "daemon-reload":
            self.events.append("reload")
            code = self.reload_results.pop(0) if self.reload_results else 0
            if code == 0 and not self.reload_noop:
                self.loaded = self.disk()
            if self.after_reload is not None:
                self.after_reload()
            return code, ""
        if verb == "enable":
            self.events.append("enable")
            if self.enable_fails or not self.fragment.exists():
                return 1, ""
            link.symlink_to(f"{tool.UNIT_DIR}/{tool.UNIT}")
            return (1 if self.enable_fails_after_effect else 0), ""
        if verb == "disable":
            self.events.append("disable")
            if self.disable_fails:
                return 1, ""
            link.unlink(missing_ok=True)
            return (1 if self.disable_fails_after_effect else 0), ""
        if verb == "stop":
            self.events.append("stop")
            if self.stop_code == 0:
                self.supervisor = "inactive"
            if self.after_stop is not None:
                self.after_stop()
            return self.stop_code, ""
        if verb in ("start", "restart"):
            self.events.append(verb)
            if self.restart_fails:
                self.supervisor = "failed"
                return 1, ""
            self.supervisor, self.running = "active", self.loaded
            return 0, ""
        return 0, ""

    disable_fails = False
    enable_fails_after_effect = disable_fails_after_effect = False  # a non-zero result that nevertheless changed the link
    state_fault = None  # callable -> None | "fail" | "empty" | "garbage" | "missing" for each dedicated ActiveState query

    def drain(self, path, uid):
        self.events.append("drain-connect")
        if self.absent:
            raise SupervisorAbsent
        session = FakeSession(self)
        self.sessions.append(session)
        return session


@pytest.fixture
def world(tmp_path):
    return World(tmp_path)


ACCOUNT_ENTRY = SimpleNamespace(pw_uid=ACCOUNT_UID, pw_gid=ACCOUNT_UID, pw_shell="/usr/sbin/nologin", pw_dir="/home/exec")


def installer(world, *, euid=ME, entry=ACCOUNT_ENTRY, group=ACCOUNT_UID, trusted=None, **kw) -> Installer:
    def getpwnam(name):
        if name != ACCOUNT:
            raise KeyError(name)
        return entry

    def getgrnam(name):
        if name != ACCOUNT or group is None:
            raise KeyError(name)
        return SimpleNamespace(gr_gid=group)

    # The home belongs to the account; everything else belongs to the (test-)trusted owner.
    return Installer(world.repo, root=str(world.root), run=world.runner, euid=lambda: euid, getpwnam=getpwnam, getgrnam=getgrnam,
                     trusted=trusted or (ME, os.getgid()), drain=world.drain, **kw)


@pytest.fixture(autouse=True)
def account_owned(monkeypatch):
    """What belongs to the account (its home, the supervisor's process, socket and state) is reported as such without root."""
    real = os.lstat

    def lstat(path, *a, **k):
        info = real(path, *a, **k)
        if str(path).endswith(("/home/exec", "/proc/4242", "supervisor.sock", "/invocations")):
            values = list(info)
            values[4] = ACCOUNT_UID
            return os.stat_result(values)
        return info

    monkeypatch.setattr(os, "lstat", lstat)


def dest(world) -> Path:
    return world.root / "etc/systemd/system" / UNIT


def enabled_link(world) -> Path:
    return world.root / "etc/systemd/system/multi-user.target.wants" / UNIT


# --- install: inactive, and only on a fully trusted tree --------------------------------------------------


def test_install_writes_the_repository_fragment_once_enables_it_in_the_system_manager_and_reloads_it(world):
    tool_ = installer(world)
    assert tool_.install() == "installed"
    assert dest(world).read_bytes() == (REPO / tool.SOURCE_RELATIVE).read_bytes()
    assert oct(dest(world).stat().st_mode & 0o777) == "0o644"
    assert enabled_link(world).is_symlink() and os.readlink(enabled_link(world)) == f"{tool.UNIT_DIR}/{tool.UNIT}"
    assert world.loaded == dest(world).read_bytes()  # the manager demonstrably holds the installed fragment
    assert not any("--user" in c or "start" in c or "restart" in c or "--global" in c for c in world.calls)  # never started; never global
    assert ["systemctl", "daemon-reload"] in world.calls and world.events == ["enable", "reload"]
    assert tool_.install() == "installed"  # idempotent: identical fragment, no rewrite
    assert tool_.verify() == "installed"
    assert not [p for p in (world.root / "etc/systemd/system").iterdir() if p.name.startswith(".")]
    assert not (world.root / "etc/systemd/user").exists()  # nothing at all was placed for any user manager
    assert not (world.home / ".config").exists()
    assert "drain-connect" not in world.events  # install never contacts a supervisor


def damage_case(world, name):
    """Apply one defect; returns the expected refusal word."""
    base, site = world.root / PLATFORM, world.root / VENV / "lib/python3.12/site-packages"
    if name == "sudo-extra":
        world.sudo += "    (root) NOPASSWD: /bin/true\n"
        return "sudoers-not-exact"
    if name == "sudo-none":
        world.sudo = f"User {ACCOUNT} may run the following commands on host:\n"
        return "sudoers-not-exact"
    if name == "sudo-password":
        world.sudo = world.sudo.replace("NOPASSWD: ", "")
        return "sudoers-not-exact"
    if name == "sudo-other-vector":
        world.sudo = world.sudo.replace(" stop", " start")
        return "sudoers-not-exact"
    if name == "sudo-fail":
        world.runner = lambda argv: (1, "")
        return "sudoers-unreadable"
    if name == "no-linger":
        (world.root / "var/lib/systemd/linger" / ACCOUNT).unlink()
        return "linger-off"
    if name == "code-writable":
        base.chmod(0o777)
        return "code-writable"
    if name == "code-group":
        (base / "adapters").chmod(0o775)
        return "code-writable"
    if name == "tree-file-writable":
        (base / "application/mod.py").chmod(0o666)
        return "code-writable"
    if name == "tree-nested-file-writable":
        (base / "adapters/pkg/inner.py").chmod(0o664)
        return "code-writable"
    if name == "tree-nested-dir-writable":
        (base / "application/pkg").chmod(0o777)
        return "code-writable"
    if name == "opt-writable":
        (world.root / "opt").chmod(0o777)
        return "code-writable"
    if name == "root-writable":
        world.root.chmod(0o777)
        return "code-writable"
    if name == "tree-file-symlink":
        (base / "adapters/link.py").symlink_to("mod.py")
        return "code-symlink"
    if name == "tree-nested-symlink-to-writable":
        outside = world.root / "tmp-writable"
        outside.write_text("x")
        outside.chmod(0o666)
        (base / "application/pkg/evil.py").symlink_to(outside)
        return "code-symlink"
    if name == "tree-dir-symlink":
        (base / "adapters/other").symlink_to(base / "application")
        return "code-symlink"
    if name == "tree-root-symlink":
        shutil.rmtree(base / "adapters")
        (base / "adapters").symlink_to(base / "application")
        return "code-symlink"
    if name == "tree-special-file":
        os.mkfifo(base / "adapters/fifo", 0o644)
        return "code-untrusted"
    if name == "interpreter-link-target-writable":
        (world.root / HOME_BIN / "python3.12").chmod(0o777)
        return "code-writable"
    if name == "interpreter-link-loop":
        (world.root / VENV / "bin" / "python").unlink()
        (world.root / VENV / "bin" / "python").symlink_to("python")
        return "code-symlink"
    if name == "interpreter-home-writable":
        (world.root / HOME_BIN).chmod(0o777)
        return "code-writable"
    if name == "interpreter-escape":
        (world.root / VENV / "bin" / "python").unlink()
        (world.root / VENV / "bin" / "python").symlink_to("../../../../../../../../../etc/passwd")
        return "code-untrusted"
    if name == "pyvenv-writable":
        (world.root / VENV / "pyvenv.cfg").chmod(0o666)
        return "code-writable"
    if name == "pyvenv-missing":
        (world.root / VENV / "pyvenv.cfg").unlink()
        return "code-missing"
    if name == "site-writable":
        site.chmod(0o777)
        return "code-writable"
    if name == "site-pth-writable":
        (site / "_virtualenv.pth").chmod(0o666)
        return "code-writable"
    if name == "site-pth-symlink":
        (site / "extra.pth").symlink_to("_virtualenv.pth")
        return "code-symlink"
    if name == "jeepney-file-writable":
        (site / "jeepney/io.py").chmod(0o666)
        return "code-writable"
    if name == "jeepney-dir-writable":
        (site / "jeepney").chmod(0o775)
        return "code-writable"
    if name == "jeepney-symlink":
        (site / "jeepney/evil.py").symlink_to("io.py")
        return "code-symlink"
    if name == "jeepney-missing":
        shutil.rmtree(site / "jeepney")
        return "code-missing"
    if name == "venv-parent-writable":
        (world.root / "opt/freedom-blades/runtime").chmod(0o777)
        return "code-writable"
    if name == "fragment-writable":
        (world.repo / tool.SOURCE_RELATIVE).chmod(0o666)
        return "code-writable"
    if name == "fragment-dir-writable":
        (world.repo / "infra/executor").chmod(0o777)
        return "code-writable"
    if name == "fragment-symlink":
        path = world.repo / tool.SOURCE_RELATIVE
        shutil.copy(path, world.root / "elsewhere")
        path.unlink()
        path.symlink_to(world.root / "elsewhere")
        return "code-symlink"
    if name == "fragment-parent-symlink":
        shutil.move(world.repo / "infra", world.root / "infra-real")
        (world.repo / "infra").symlink_to(world.root / "infra-real")
        return "code-symlink"
    if name == "fragment-hardlinked":
        os.link(world.repo / tool.SOURCE_RELATIVE, world.root / "second-name")
        return "source-invalid"
    if name == "etc-dropin":
        (world.root / "etc/systemd/system" / f"{UNIT}.d").mkdir()
        return "shadowed"
    if name == "usr-lib-shadow":
        (world.root / "usr/lib/systemd/system").mkdir(parents=True)
        (world.root / "usr/lib/systemd/system" / UNIT).write_text("[Service]\n")
        return "shadowed"
    if name == "run-shadow":
        (world.root / "run/systemd/system").mkdir(parents=True)
        (world.root / "run/systemd/system" / UNIT).write_text("[Service]\n")
        return "shadowed"
    if name == "control-shadow":
        (world.root / "etc/systemd/system.control").mkdir(parents=True)
        (world.root / "etc/systemd/system.control" / UNIT).write_text("[Service]\n")
        return "shadowed"
    if name == "control-dropin":
        path = world.root / "run/systemd/system.control" / f"{UNIT}.d"
        path.mkdir(parents=True)
        (path / "50-override.conf").write_text("[Service]\nExecStart=\nExecStart=/bin/false\n")
        return "shadowed"
    if name == "prefix-dropin":
        path = world.root / "usr/local/lib/systemd/system/freedom-blades-.service.d"
        path.mkdir(parents=True)
        (path / "50-override.conf").write_text("[Service]\nUser=root\n")
        return "shadowed"
    if name == "legacy-fragment":
        (world.root / "etc/systemd/user").mkdir(parents=True)
        (world.root / "etc/systemd/user" / UNIT).write_text("[Service]\n")
        return "legacy-user-service"
    if name == "legacy-enabled":
        (world.root / "etc/systemd/user/default.target.wants").mkdir(parents=True)
        (world.root / "etc/systemd/user/default.target.wants" / UNIT).symlink_to(f"/etc/systemd/user/{UNIT}")
        return "legacy-user-service"
    if name == "legacy-dropin":
        (world.root / "etc/systemd/user" / f"{UNIT}.d").mkdir(parents=True)
        return "legacy-user-service"
    raise AssertionError(name)


DAMAGE = [
    "sudo-extra", "sudo-none", "sudo-password", "sudo-other-vector", "sudo-fail", "no-linger", "code-writable", "code-group",
    "tree-file-writable", "tree-nested-file-writable", "tree-nested-dir-writable", "opt-writable", "root-writable",
    "tree-file-symlink", "tree-nested-symlink-to-writable", "tree-dir-symlink", "tree-root-symlink", "tree-special-file",
    "interpreter-link-target-writable", "interpreter-link-loop", "interpreter-home-writable", "interpreter-escape",
    "pyvenv-writable", "pyvenv-missing", "site-writable", "site-pth-writable", "site-pth-symlink", "jeepney-file-writable",
    "jeepney-dir-writable", "jeepney-symlink", "jeepney-missing", "venv-parent-writable", "fragment-writable",
    "fragment-dir-writable", "fragment-symlink", "fragment-parent-symlink", "fragment-hardlinked", "etc-dropin", "usr-lib-shadow",
    "run-shadow", "control-shadow", "control-dropin", "prefix-dropin", "legacy-fragment", "legacy-enabled", "legacy-dropin",
]


@pytest.mark.parametrize("damage", DAMAGE)
def test_every_unmet_prerequisite_refuses_before_anything_is_written(world, damage):
    word = damage_case(world, damage)
    with pytest.raises(tool.Failure) as caught:
        installer(world).install()
    assert caught.value.word == word and not dest(world).exists() and not enabled_link(world).exists()
    assert not any(c[0] == "systemctl" for c in world.calls)  # the service manager was not touched
    assert world.events == [] and world.loaded is None
    assert not [p for p in (world.root / "etc/systemd/system").iterdir() if p.name.startswith(".")]


@pytest.mark.parametrize("damage", [d for d in DAMAGE if d.startswith(("tree", "interp", "pyvenv", "site", "jeepney", "venv", "code", "legacy"))])
def test_verify_after_installation_refuses_the_same_defects(world, damage):
    installer(world).install()
    word = damage_case(world, damage)
    with pytest.raises(tool.Failure) as caught:
        installer(world).verify()
    assert caught.value.word == word


def test_a_fully_trusted_tree_installs_verifies_and_is_ready(world):
    t = installer(world)
    assert t.install() == "installed" and t.verify() == "installed"


def test_the_dependency_tree_is_bounded_and_refuses_rather_than_samples(world, monkeypatch):
    monkeypatch.setattr(tool, "MAX_WALK", 5)  # the trees hold more entries than this
    with pytest.raises(tool.Failure) as caught:
        installer(world).install()
    assert caught.value.word == "code-too-large" and not dest(world).exists()


def test_a_too_deep_tree_refuses(world, monkeypatch):
    monkeypatch.setattr(tool, "MAX_DEPTH", 0)
    with pytest.raises(tool.Failure) as caught:
        installer(world).install()
    assert caught.value.word == "code-too-large"


class Endless:
    """A directory iterator that never ends, counting what was drawn from it (the memory/CPU an unbounded walk would spend)."""

    def __init__(self):
        self.drawn = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def __iter__(self):
        return self

    def __next__(self):
        self.drawn += 1
        return SimpleNamespace(name=f"entry-{self.drawn}")


@pytest.mark.parametrize("level", ["code-tree", "site-packages", "venv-lib", "interpreter-siblings"])
def test_an_oversized_single_directory_refuses_after_a_bounded_draw_from_the_iterator(world, monkeypatch, level):
    """Every trust enumeration is bounded *while it iterates*: one entry past the budget is the last one ever drawn."""
    monkeypatch.setattr(tool, "MAX_WALK", 50)
    site = str(world.root / VENV / "lib/python3.12/site-packages")
    targets = {"code-tree": str(world.root / PLATFORM / "adapters"), "site-packages": site,
               "venv-lib": str(world.root / VENV / "lib"), "interpreter-siblings": str(world.root / "opt/freedom-blades/runtime/pyhome/lib")}
    real, endless = os.scandir, Endless()

    def scandir(source=".", *a, **k):
        if isinstance(source, int):
            source = os.readlink(f"/proc/self/fd/{source}")
        if os.path.realpath(source) == os.path.realpath(targets[level]):
            return endless
        return real(source, *a, **k)

    with monkeypatch.context() as patched:  # undone before fixture teardown: pytest's own tmp cleanup must never see the endless iterator
        patched.setattr(os, "scandir", scandir)
        with pytest.raises(tool.Failure) as caught:
            installer(world).install()
    assert caught.value.word == "code-too-large" and caught.value.code == EXIT_REFUSED
    assert endless.drawn <= 51  # the budget plus the single overflow entry; nothing was gathered, sorted or sampled beyond it
    assert not dest(world).exists() and world.events == []


def test_the_budget_is_shared_so_many_modest_directories_cannot_add_up_to_an_unbounded_walk(world, monkeypatch):
    sizes = sum(len(files) + len(dirs) for _, dirs, files in os.walk(world.root / PLATFORM / "adapters"))
    monkeypatch.setattr(tool, "MAX_WALK", 2 * sizes - 1)  # each tree fits alone; both together do not
    with pytest.raises(tool.Failure) as caught:
        installer(world).install()
    assert caught.value.word == "code-too-large"
    monkeypatch.setattr(tool, "MAX_WALK", 10_000)
    assert installer(world).install() == "installed"


def test_the_walk_never_retains_more_names_than_the_budget(world, monkeypatch):
    kept = []
    real = tool.Installer._names

    def spy(self, source, budget):
        before = budget[0]
        names = real(self, source, budget)
        kept.append((len(names), before))
        return names

    monkeypatch.setattr(tool.Installer, "_names", spy)
    installer(world).install()
    assert kept and all(count <= before for count, before in kept)


def test_the_interpreter_may_be_a_chain_of_trusted_links(world):
    python = world.root / VENV / "bin" / "python"
    mid = world.root / "opt/freedom-blades/runtime/pyhome/bin/mid"
    mid.symlink_to("python3.12")
    python.unlink()
    python.symlink_to("/opt/freedom-blades/runtime/pyhome/bin/mid")  # absolute within the (re-rooted) filesystem
    assert installer(world).install() == "installed"
    (world.root / HOME_BIN / "python3.12").chmod(0o777)  # the final target is writable: refused although the links look the same
    with pytest.raises(tool.Failure) as caught:
        installer(world).verify()
    assert caught.value.word == "code-writable"


def test_the_account_owning_anything_in_the_chain_is_refused_even_when_the_owner_matches(world):
    with pytest.raises(tool.Failure) as caught:
        installer(world, euid=ACCOUNT_UID, trusted=(ACCOUNT_UID, os.getgid())).install()
    assert caught.value.word == "code-writable" and not dest(world).exists()


class ShortIo(tool._Io):
    def __init__(self, *, read=None, write=None):
        self.read_script, self.write_script = read, write

    def read(self, fd, size):
        return self.read_script(fd, size, super().read) if self.read_script else super().read(fd, size)

    def write(self, fd, data):
        return self.write_script(fd, data, super().write) if self.write_script else super().write(fd, data)


def test_short_reads_are_completed_but_a_truncated_or_growing_read_refuses_before_installation(world):
    def one_byte(fd, size, real):
        return real(fd, min(size, 1))  # legitimately short: must be completed, not trusted

    t = installer(world, io=ShortIo(read=one_byte))
    assert t.install() == "installed" and dest(world).read_bytes() == (REPO / tool.SOURCE_RELATIVE).read_bytes()
    fresh = World(world.root.parent / "second")
    for how in ("early-eof", "extra"):
        calls = []

        def script(fd, size, real, how=how, calls=calls):
            calls.append(size)
            if how == "early-eof":
                return b"" if len(calls) > 1 else real(fd, 3)  # EOF long before st_size
            return real(fd, size) if size > 1 else b"extra"  # the file grew past its fstat size

        with pytest.raises(tool.Failure) as caught:
            installer(fresh, io=ShortIo(read=script)).install()
        assert caught.value.word in ("source-invalid", "code-untrusted") and not dest(fresh).exists()
        assert not enabled_link(fresh).exists()


def test_short_writes_are_completed_and_a_stalled_or_failing_write_leaves_nothing_installed(world):
    def two_bytes(fd, data, real):
        return real(fd, data[:2])

    t = installer(world, io=ShortIo(write=two_bytes))
    assert t.install() == "installed" and dest(world).read_bytes() == (REPO / tool.SOURCE_RELATIVE).read_bytes()
    fresh = World(world.root.parent / "second")
    for how in ("zero", "error"):
        def script(fd, data, real, how=how):
            if how == "error":
                raise OSError(28, "no space")
            return 0

        with pytest.raises(tool.Failure) as caught:
            installer(fresh, io=ShortIo(write=script)).install()
        assert caught.value.word == "install-failed" and caught.value.code == EXIT_IO
        assert not dest(fresh).exists() and not enabled_link(fresh).exists()
        assert not [p for p in (fresh.root / "etc/systemd/system").iterdir() if p.name.startswith(".")]


def test_not_root_and_a_missing_or_unsuitable_account_refuse(world):
    with pytest.raises(tool.Failure) as caught:
        installer(world, euid=ME + 1).install()
    assert caught.value.word == "not-root"
    with pytest.raises(tool.Failure) as caught:
        Installer(world.repo, root=str(world.root), run=world.runner, euid=lambda: ME, getpwnam=lambda n: (_ for _ in ()).throw(KeyError(n)),
                  trusted=(ME, os.getgid())).install()
    assert caught.value.word == "account-missing"
    for entry, group in ((SimpleNamespace(pw_uid=0, pw_gid=0, pw_shell="/usr/sbin/nologin", pw_dir="/home/exec"), 0),
                         (SimpleNamespace(pw_uid=ACCOUNT_UID, pw_gid=ACCOUNT_UID, pw_shell="/bin/bash", pw_dir="/home/exec"), ACCOUNT_UID),
                         (ACCOUNT_ENTRY, None),  # no group of that name: ``Group=freedom-executor`` could not start
                         (ACCOUNT_ENTRY, ACCOUNT_UID + 1)):  # the group of that name is not the account's own
        with pytest.raises(tool.Failure) as caught:
            installer(world, entry=entry, group=group).install()
        assert caught.value.word == "account-unsuitable"
    assert world.events == [] and not dest(world).exists()


def test_a_foreign_object_at_the_destination_is_never_overwritten(world):
    dest(world).write_text("someone else's unit")
    with pytest.raises(tool.Failure) as caught:
        installer(world).install()
    assert caught.value.word == "destination-conflict" and dest(world).read_text() == "someone else's unit"
    dest(world).unlink()
    dest(world).symlink_to("/dev/null")
    with pytest.raises(tool.Failure) as caught:
        installer(world).install()
    assert caught.value.code == EXIT_CONFLICT and dest(world).is_symlink()


def test_a_foreign_unlinked_or_unmarked_fragment_is_never_upgraded(world):
    dest(world).write_text("[Service]\nExecStart=/bin/true\n")  # root-owned 0644 but not ours: no marker
    with pytest.raises(tool.Failure) as caught:
        installer(world).install()
    assert caught.value.word == "destination-conflict" and dest(world).read_text() == "[Service]\nExecStart=/bin/true\n"
    assert world.events == [] and not enabled_link(world).exists()
    dest(world).write_bytes(tool.MARKER + b"[Service]\n")
    dest(world).chmod(0o664)  # recognizable but not 0644
    with pytest.raises(tool.Failure) as caught:
        installer(world).install()
    assert caught.value.word == "destination-conflict" and world.events == []


def stale_fragment(world) -> bytes:
    """An earlier revision of our own fragment, loaded and running: the state an upgrade starts from."""
    old = (REPO / tool.SOURCE_RELATIVE).read_bytes().replace(b"Description=Freedom Blades executor supervisor", b"Description=OLD supervisor")
    assert old != (REPO / tool.SOURCE_RELATIVE).read_bytes() and tool.MARKER in old.splitlines(keepends=True)
    dest(world).write_bytes(old)
    dest(world).chmod(0o644)
    enabled_link(world).symlink_to(f"{tool.UNIT_DIR}/{tool.UNIT}")
    world.loaded = world.running = old
    return old


def test_an_upgrade_replaces_the_recognized_fragment_atomically_reloads_it_and_the_restart_uses_it(world):
    old = stale_fragment(world)
    new = (REPO / tool.SOURCE_RELATIVE).read_bytes()
    assert installer(world).install() == "installed"
    assert dest(world).read_bytes() == new and world.loaded == new  # on disk and loaded by the manager
    assert world.running == old  # the running supervisor still has the old configuration until it is restarted
    assert world.events == ["reload"] and not [p for p in (world.root / "etc/systemd/system").iterdir() if p.name.startswith(".")]
    world.runner(["systemctl", "restart", tool.UNIT])
    assert world.running == new  # the new fragment is the configuration used after the restart
    assert installer(world).verify() == "installed"


def test_an_upgrade_that_cannot_be_loaded_restores_the_working_fragment_and_never_reports_success(world):
    old = stale_fragment(world)
    for how in ("exit-code", "no-op"):
        world.events.clear()
        world.reload_results = [1, 0] if how == "exit-code" else []  # the restoring reload is allowed to work
        world.reload_noop = how == "no-op"
        with pytest.raises(tool.Failure) as caught:
            installer(world).install()
        assert caught.value.word == "reload-failed" and caught.value.code == EXIT_IO
        assert dest(world).read_bytes() == old  # a recoverable, root-owned fragment: the one that was working
        assert (dest(world).stat().st_uid, dest(world).stat().st_mode & 0o777) == (ME, 0o644)
        assert not [p for p in (world.root / "etc/systemd/system").iterdir() if p.name.startswith(".")]
        world.reload_noop = False
    assert installer(world).install() == "installed"  # a later attempt completes the upgrade


def test_a_failed_first_reload_is_a_failed_installation_and_a_rerun_completes_it(world):
    world.reload_results = [1]
    with pytest.raises(tool.Failure) as caught:
        installer(world).install()
    assert caught.value.word == "reload-failed" and caught.value.code == EXIT_IO
    assert dest(world).exists() and world.loaded is None  # the manager does not hold it: it was not claimed
    with pytest.raises(tool.Failure) as caught:
        installer(world).verify()
    assert caught.value.word == "manager-stale"
    assert installer(world).install() == "installed" and installer(world).verify() == "installed"


def test_a_loaded_dropin_or_changed_effective_service_property_is_never_accepted_as_the_reviewed_fragment(world):
    t = installer(world)
    t.install()
    for key, value in (("dropins", "/run/systemd/system.control/x.conf"),):
        setattr(world, key, value)
        with pytest.raises(tool.Failure) as caught:
            t.verify()
        assert caught.value.word == "manager-stale"
        setattr(world, key, "")
    original = world.runner

    for expected, wrong in ((f"User={ACCOUNT}", "User=somebody-else"),
                            (f"Group={ACCOUNT}", "Group=somebody-else"),
                            ("Environment=PATH=/usr/bin:/bin", "Environment=PATH=/hostile")):
        def changed(argv, expected=expected, wrong=wrong):
            code, out = original(argv)
            if argv[:2] == ["systemctl", "show"]:
                out = out.replace(expected, wrong)
            return code, out

        world.runner = changed
        with pytest.raises(tool.Failure) as caught:
            installer(world).verify()
        assert caught.value.word == "manager-stale"
        world.runner = original


def test_a_failed_enable_fails_the_installation_before_anything_is_claimed(world):
    world.enable_fails = True
    with pytest.raises(tool.Failure) as caught:
        installer(world).install()
    assert caught.value.word == "enable-failed" and not enabled_link(world).exists() and "reload" not in world.events


def test_verify_reports_each_missing_piece_and_ready_needs_a_running_supervisor(world):
    t = installer(world)
    with pytest.raises(tool.Failure) as caught:
        t.verify()
    assert caught.value.word == "not-installed"
    t.install()
    enabled_link(world).unlink()
    with pytest.raises(tool.Failure) as caught:
        t.verify()
    assert caught.value.word == "not-enabled"
    t.install()
    world.loaded = None  # the manager lost (or never had) the configuration
    with pytest.raises(tool.Failure) as caught:
        t.verify()
    assert caught.value.word == "manager-stale"
    world.loaded = dest(world).read_bytes()
    runtime = world.root / f"run/{tool.STATE_NAME}"
    runtime.mkdir(parents=True)
    world.state.mkdir(parents=True)
    world.state.chmod(0o700)
    for manager, supervisor, word in (("inactive", "active", "manager-not-running"), ("active", "inactive", "supervisor-not-ready"),
                                      ("active", "active", "supervisor-not-ready")):  # last: no socket yet
        world.manager, world.supervisor = manager, supervisor
        with pytest.raises(tool.Failure) as caught:
            t.verify(ready=True)
        assert caught.value.word == word


def test_ready_needs_the_socket_and_a_private_state_directory(world):
    t = installer(world)
    t.install()
    runtime = world.root / f"run/{tool.STATE_NAME}"
    runtime.mkdir(parents=True)
    world.state.mkdir(parents=True)
    short = Path("/tmp") / f"fbi-{os.getpid()}.sock"
    sock = socket.socket(socket.AF_UNIX)
    sock.bind(str(short))
    try:
        shutil.move(short, runtime / "supervisor.sock")
        world.state.chmod(0o755)
        with pytest.raises(tool.Failure) as caught:
            t.verify(ready=True)
        assert caught.value.word == "state-untrusted"
        world.state.chmod(0o700)
        assert t.verify(ready=True) == "ready"
    finally:
        sock.close()


def test_a_supervisor_not_running_as_the_dedicated_uid_is_never_ready(world, monkeypatch):
    t = installer(world)
    t.install()
    (world.root / f"run/{tool.STATE_NAME}").mkdir(parents=True)
    world.state.mkdir(parents=True)
    world.state.chmod(0o700)
    short = Path("/tmp") / f"fbi-uid-{os.getpid()}.sock"
    sock = socket.socket(socket.AF_UNIX)
    sock.bind(str(short))
    try:
        shutil.move(short, world.root / f"run/{tool.STATE_NAME}/supervisor.sock")
        assert t.verify(ready=True) == "ready"
        accounted = os.lstat

        def lstat(path, *a, **k):  # /proc/<pid> is owned by the real (unprivileged test) uid, not by the account
            if str(path).endswith("/proc/4242"):
                return os.stat_result([*accounted(path, *a, **k)][:4] + [0] + [*accounted(path, *a, **k)][5:])
            return accounted(path, *a, **k)

        monkeypatch.setattr(os, "lstat", lstat)
        with pytest.raises(tool.Failure) as caught:
            t.verify(ready=True)
        assert caught.value.word == "supervisor-not-ready"
    finally:
        sock.close()


def test_a_user_unit_of_the_same_name_in_the_accounts_own_configuration_changes_nothing(world):
    """The system fragment is out of the account's reach: its own user-unit directory holds no authority over it."""
    t = installer(world)
    t.install()
    before = (dest(world).read_bytes(), os.readlink(enabled_link(world)), world.loaded, list(world.events))
    mine = world.home / ".config/systemd/user"
    (mine / "default.target.wants").mkdir(parents=True)
    (mine / UNIT).write_text("[Service]\nExecStart=/bin/sh -c evil\n")
    (mine / "default.target.wants" / UNIT).symlink_to(mine / UNIT)
    (mine / f"{UNIT}.d").mkdir()
    assert t.verify() == "installed" and t.install() == "installed"
    assert (dest(world).read_bytes(), os.readlink(enabled_link(world)), world.loaded) == before[:3]
    assert installer(world).remove() == "removed"  # and removal is not obstructed by it
    assert (mine / UNIT).read_text().endswith("evil\n")  # the installer never touches the account's own files


def test_the_system_installation_leaves_no_trace_in_any_user_manager(world):
    installer(world).install()
    traces = [p for p in world.root.rglob("*") if (p.name.startswith(UNIT) or p.name == tool.STATE_NAME) and "platform" not in p.parts]
    assert sorted(str(p.relative_to(world.root)) for p in traces) == [
        f"etc/systemd/system/{UNIT}", f"etc/systemd/system/multi-user.target.wants/{UNIT}"]  # no user wants, no state, no runtime


def test_a_legacy_user_service_cannot_coexist_with_the_system_service(world):
    t = installer(world)
    t.install()
    (world.root / "etc/systemd/user").mkdir(parents=True)
    (world.root / "etc/systemd/user" / UNIT).write_text("[Service]\n")  # an old candidate appears beside the installed system unit
    for action in (t.verify, t.install):
        with pytest.raises(tool.Failure) as caught:
            action()
        assert caught.value.word == "legacy-user-service" and caught.value.code == EXIT_CONFLICT
    assert (world.root / "etc/systemd/user" / UNIT).read_text() == "[Service]\n"  # the legacy configuration is never edited by the tool
    assert "ConditionPathExists=!/etc/systemd/user/" + UNIT in (REPO / tool.SOURCE_RELATIVE).read_text()  # and the unit itself refuses to start beside it


# --- removal: only through the drain ----------------------------------------------------------------------


def installed(world) -> Installer:
    t = installer(world)
    t.install()
    world.events.clear()
    world.calls.clear()
    return t


def intact(world) -> bool:
    """A persistent owner is configured: the fragment is on disk and loaded by the manager, and enabled."""
    return dest(world).exists() and enabled_link(world).is_symlink() and world.loaded == dest(world).read_bytes()


def test_remove_drains_then_stops_then_disables_then_unlinks_in_that_order(world):
    t = installed(world)
    world.state.mkdir(parents=True)
    assert t.remove() == "removed"
    assert world.events == ["drain-connect", "drain-request", "stop", "disable", "reload", "drain-close"]
    assert world.loaded is None  # the manager was reloaded after the unlink: it holds no stale configuration
    assert not dest(world).exists() and not enabled_link(world).exists()
    assert (world.root / "var/lib/systemd/linger" / ACCOUNT).exists()  # the account's linger is left alone
    assert not any("loginctl" in c or "useradd" in c or "visudo" in c for call in world.calls for c in call)
    assert world.sessions[0].closed


def test_a_pending_drain_refuses_and_leaves_the_supervisor_running_again(world):
    t = installed(world)
    world.drain_reply = "pending"
    with pytest.raises(tool.Failure) as caught:
        t.remove()
    assert caught.value.code == EXIT_PENDING and caught.value.word == "invocation-pending"
    assert intact(world) and "stop" not in world.events and "disable" not in world.events
    assert "restart" in world.events and world.sessions[0].closed  # a drained supervisor refuses stops until restarted
    assert world.supervisor == "active"


@pytest.mark.parametrize("fault", ["garbage-reply", "lost-reply"])
def test_a_lost_or_unintelligible_drain_reply_refuses_removal(world, fault):
    t = installed(world)
    world.drain_reply = "garbage"
    with pytest.raises(tool.Failure) as caught:
        t.remove()
    assert caught.value.code == EXIT_PENDING and caught.value.word == "drain-unconfirmed"
    assert intact(world) and "stop" not in world.events and world.supervisor == "active"


def test_a_supervisor_lost_between_the_acknowledgment_and_the_stop_refuses_removal(world):
    t = installed(world)
    world.on_drain = lambda: setattr(world, "session_alive", False)  # the supervisor restarted: its drain state is gone
    with pytest.raises(tool.Failure) as caught:
        t.remove()
    assert caught.value.word == "drain-lost" and caught.value.code == EXIT_PENDING
    assert intact(world) and "stop" not in world.events and "disable" not in world.events
    assert "restart" in world.events


def test_a_request_that_slipped_in_across_the_stop_is_detected_and_the_owner_is_restarted(world):
    t = installed(world)
    world.state.mkdir(parents=True)

    def admitted():  # a restarted, undrained supervisor admitted an invocation in the window
        (world.state / "active.json").write_text("{}")

    world.after_stop = admitted
    with pytest.raises(tool.Failure) as caught:
        t.remove()
    assert caught.value.code == EXIT_PENDING and caught.value.word == "invocation-pending"
    assert intact(world) and world.events.count("restart") == 1 and "disable" not in world.events
    assert world.supervisor == "active"


@pytest.mark.parametrize("boundary", ["drain-acknowledged", "stop-issued"])
def test_a_request_racing_removal_at_a_real_boundary_is_owned_by_the_persistent_supervisor_never_orphaned(world, boundary):
    """Barriers at the real boundaries: the admission lands exactly while removal is between its drain and its stop."""
    t = installed(world)
    world.state.mkdir(parents=True)
    reached, admitted = threading.Event(), threading.Event()

    def at_boundary():
        reached.set()
        assert admitted.wait(10)

    def requester():
        assert reached.wait(10)
        (world.state / "active.json").write_text("{}")  # the admission's durable record, written by the owner as the barrier holds
        admitted.set()

    thread = threading.Thread(target=requester)
    thread.start()
    if boundary == "drain-acknowledged":
        world.on_drain = at_boundary
    else:
        world.after_stop = at_boundary
    try:
        with pytest.raises(tool.Failure) as caught:
            t.remove()
    finally:
        admitted.set()
        thread.join(10)
    assert caught.value.code == EXIT_PENDING and caught.value.word == "invocation-pending"
    assert (world.state / "active.json").exists()  # the record the persistent owner holds is untouched
    assert "disable" not in world.events and owner_left_behind(world)  # and the owner is configured, loaded and running again
    assert dest(world).exists() and enabled_link(world).is_symlink()


def test_a_state_directory_that_cannot_be_read_refuses_removal(world):
    t = installed(world)
    world.state.mkdir(parents=True)
    world.state.chmod(0)
    try:
        with pytest.raises(tool.Failure) as caught:
            t.remove()
    finally:
        world.state.chmod(0o700)
    assert caught.value.word == "invocation-pending" and intact(world) and "stop" not in world.events


@pytest.mark.parametrize("units", [(0, "freedom-executor-stop-0123456789abcdef.service loaded active running x\n"), (1, ""), (1, "freedom-executor-stop-x"),
                                  (0, "garbage\n")])
def test_a_matching_unit_or_an_unobservable_unit_list_refuses_removal(world, units):
    t = installed(world)
    world.units_code, world.units = units
    with pytest.raises(tool.Failure) as caught:
        t.remove()
    assert caught.value.code == EXIT_PENDING and intact(world) and "stop" not in world.events


def test_a_record_in_the_state_directory_refuses_removal_even_if_the_supervisor_acknowledged(world):
    t = installed(world)
    world.state.mkdir(parents=True)
    (world.state / "active.json").write_text("{}")
    with pytest.raises(tool.Failure) as caught:
        t.remove()
    assert caught.value.code == EXIT_PENDING and intact(world) and "stop" not in world.events


def test_with_no_supervisor_running_removal_needs_an_inactive_unit_and_an_empty_state(world):
    t = installed(world)
    world.absent = True
    world.supervisor = "starting"  # not listening yet, but it may be about to admit
    with pytest.raises(tool.Failure) as caught:
        t.remove()
    assert caught.value.word == "drain-unconfirmed" and intact(world)
    world.supervisor = "inactive"
    world.state.mkdir(parents=True)
    (world.state / "active.json").write_text("{}")
    with pytest.raises(tool.Failure) as caught:
        t.remove()
    assert caught.value.word == "invocation-pending" and intact(world)
    (world.state / "active.json").unlink()
    assert t.remove() == "removed" and not dest(world).exists()


def test_with_the_user_manager_down_nothing_can_be_running_and_the_state_still_decides(world):
    t = installed(world)
    world.manager = "inactive"
    world.state.mkdir(parents=True)
    (world.state / "active.json").write_text("{}")
    with pytest.raises(tool.Failure) as caught:
        t.remove()
    assert caught.value.word == "invocation-pending" and intact(world)
    (world.state / "active.json").unlink()
    assert t.remove() == "removed"
    world.manager = "activating"  # neither up nor provably down: not evidence that nothing can be admitting
    with pytest.raises(tool.Failure) as caught:
        installer(world).remove()
    assert caught.value.word == "drain-unconfirmed" and caught.value.code == EXIT_PENDING


def owner_left_behind(world) -> bool:
    """No ownership gap: after a failed removal the configured owner is loaded, enabled and running again."""
    return intact(world) and world.supervisor == "active" and world.running == dest(world).read_bytes()


def test_a_failed_stop_is_not_reported_as_removed_and_leaves_a_running_owner(world):
    t = installed(world)
    world.stop_code = 1
    with pytest.raises(tool.Failure) as caught:
        t.remove()
    assert caught.value.word == "stop-failed" and caught.value.code == EXIT_IO
    assert "restart" in world.events and owner_left_behind(world) and "disable" not in world.events


def test_a_failed_disable_is_not_reported_as_removed_and_leaves_a_running_owner(world):
    t = installed(world)
    world.disable_fails = True
    with pytest.raises(tool.Failure) as caught:
        t.remove()
    assert caught.value.word == "disable-failed" and "restart" in world.events and owner_left_behind(world)


def test_a_failed_unlink_re_enables_and_restarts_the_owner_and_a_later_removal_completes(world):
    t = installed(world)
    real = os.unlink

    def refuse(path, *a, **k):
        if str(path) == str(dest(world)):
            raise PermissionError(1, "no")
        return real(path, *a, **k)

    os.unlink = refuse
    try:
        with pytest.raises(tool.Failure) as caught:
            t.remove()
    finally:
        os.unlink = real
    assert caught.value.word == "remove-failed" and caught.value.code == EXIT_IO
    assert "disable" in world.events and world.events.count("enable") == 1  # it had been disabled: enablement is put back
    assert owner_left_behind(world)
    assert t.remove() == "removed" and not dest(world).exists()  # a later attempt completes the removal


def test_a_failed_reload_after_the_unlink_restores_the_fragment_and_the_owner(world):
    t = installed(world)
    original = dest(world).read_bytes()
    world.reload_results = [1, 0]  # the reload that should drop the unit fails; the recovery reload works
    with pytest.raises(tool.Failure) as caught:
        t.remove()
    assert caught.value.word == "reload-failed" and caught.value.code == EXIT_IO
    assert dest(world).read_bytes() == original and (dest(world).stat().st_uid, dest(world).stat().st_mode & 0o777) == (ME, 0o644)
    assert owner_left_behind(world) and world.events[-4:] == ["enable", "reload", "restart", "drain-close"]  # restored, loaded, restarted
    assert world.sessions[0].closed
    assert t.remove() == "removed"


def test_a_manager_that_exits_zero_but_keeps_the_unit_loaded_is_not_a_removal(world):
    t = installed(world)
    world.reload_noop = True
    with pytest.raises(tool.Failure) as caught:
        t.remove()
    assert caught.value.word == "reload-failed"
    world.reload_noop = False
    assert owner_left_behind(world) and dest(world).exists()


def test_a_failure_with_nothing_drained_or_stopped_does_not_disturb_a_running_owner(world):
    t = installed(world)
    world.supervisor = "inactive"  # nothing runs; the unit is simply not started
    world.absent = True
    world.reload_results = [1]
    with pytest.raises(tool.Failure) as caught:
        t.remove()
    assert caught.value.word == "reload-failed" and intact(world)


def test_removal_is_idempotent_and_judges_the_stop_by_the_managers_state_not_an_exit_code(world):
    t = installed(world)
    assert t.remove() == "removed"
    world.absent = True  # nothing listens any more
    world.stop_code = 5  # `systemctl stop` of a unit that is no longer loaded exits non-zero
    assert t.remove() == "removed" and not dest(world).exists()


def test_remove_leaves_a_foreign_destination_alone_and_never_contacts_the_supervisor(world):
    dest(world).write_text("not ours")
    with pytest.raises(tool.Failure) as caught:
        installer(world).remove()
    assert caught.value.code == EXIT_CONFLICT and dest(world).read_text() == "not ours" and world.events == []


def test_remove_needs_root_and_a_trusted_fragment_source(world):
    with pytest.raises(tool.Failure) as caught:
        installer(world, euid=ME + 1).remove()
    assert caught.value.word == "not-root" and world.events == []
    (world.repo / tool.SOURCE_RELATIVE).chmod(0o666)
    with pytest.raises(tool.Failure) as caught:
        installer(world).remove()
    assert caught.value.word == "code-writable" and world.events == []


def test_entry_prints_one_fixed_line_and_maps_exit_codes(world, capsys):
    t = installer(world)
    assert main(["install"], installer=t) == EXIT_OK and capsys.readouterr().out == "executor-supervisor installed\n"
    assert main(["verify-ready"], installer=t) == EXIT_VERIFY_FAILED
    assert capsys.readouterr().err == "executor-supervisor supervisor-not-ready\n"
    world.drain_reply = "pending"
    assert main(["remove"], installer=t) == EXIT_PENDING
    assert capsys.readouterr().err == "executor-supervisor invocation-pending\n"
    world.sudo = ""
    assert main(["install"], installer=t) == EXIT_REFUSED
    assert main(["bogus"], installer=t) == tool.EXIT_USAGE
    assert main([], installer=t) == tool.EXIT_USAGE


def test_incomplete_recovery_has_its_own_exit_status_and_one_fixed_line(world, capsys):
    stale_fragment(world)
    world.reload_results = [1, 1]
    assert main(["install"], installer=installer(world)) == tool.EXIT_RECOVERY == 15
    assert capsys.readouterr().err == "executor-supervisor recovery-incomplete\n"


# --- the drain connection itself ---------------------------------------------------------------------------


class FakeSupervisor:
    """A one-connection server speaking the supervisor's wire protocol, scripted per test."""

    def __init__(self, tmp_path, script):
        self.path = f"/tmp/fbd-{os.getpid()}-{id(self) & 0xffff}.sock"
        self.script, self.seen = script, []
        self.listener = socket.socket(socket.AF_UNIX)
        self.listener.bind(self.path)
        self.listener.listen(1)
        self.conn = None
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self):
        try:
            self.conn, _ = self.listener.accept()
        except OSError:
            return
        try:
            self.script(self.conn, self.seen)
        except OSError:  # the client hung up on us, or the test closed the connection
            pass

    def close(self):
        for item in (self.conn, self.listener):
            if item is not None:
                item.close()
        try:
            os.unlink(self.path)
        except OSError:
            pass


def serve_with(tmp_path, script):
    return FakeSupervisor(tmp_path, script)


def answer(reply, *, greeting=GREETING):
    def script(conn, seen):
        conn.sendall(greeting)
        seen.append(conn.recv(32))
        if reply is not None:
            conn.sendall(reply)

    return script


@pytest.mark.parametrize("reply,expected", [(DRAIN_EMPTY, True), (DRAIN_PENDING, False)])
def test_the_drain_session_returns_the_exact_answer_and_the_connection_is_held(tmp_path, reply, expected):
    server = serve_with(tmp_path, answer(reply))
    try:
        session = DrainSession(server.path, ME, seconds=5)
        assert session.request() is expected and server.seen == [DRAIN_REQUEST]
        assert session.alive()
        server.conn.close()  # the supervisor goes away
        for _ in range(100):
            if not session.alive():
                break
            threading.Event().wait(0.02)
        assert not session.alive()
        session.close()
        assert not session.alive()
    finally:
        server.close()


@pytest.mark.parametrize("script", [answer(b"drain maybe\n"), answer(b"drain empty"), answer(b"drain emptyX\n"), answer(None), answer(b"", greeting=GREETING)])
def test_a_lost_malformed_or_missing_answer_is_never_read_as_empty(tmp_path, script):
    server = serve_with(tmp_path, script)
    try:
        session = DrainSession(server.path, ME, seconds=0.5)
        with pytest.raises(tool.Failure) as caught:
            session.request()
        assert caught.value.word == "drain-unconfirmed"
    finally:
        server.close()


def test_a_peer_that_does_not_greet_exactly_or_is_the_wrong_uid_or_owner_is_not_the_supervisor(tmp_path, monkeypatch):
    server = serve_with(tmp_path, answer(DRAIN_EMPTY, greeting=b"hello\n"))
    try:
        with pytest.raises(tool.Failure) as caught:
            DrainSession(server.path, ME, seconds=0.5)
        assert caught.value.word == "drain-unconfirmed" and not any(server.seen)  # no request was ever sent to it (an EOF read is not one)
    finally:
        server.close()
    server = serve_with(tmp_path, answer(DRAIN_EMPTY))
    try:
        with pytest.raises(tool.Failure):
            DrainSession(server.path, ME + 1, seconds=0.5)  # the socket is not owned by the account
        monkeypatch.setattr(tool, "peer_uid", lambda conn: ME + 1)  # the listener is a different process owner
        with pytest.raises(tool.Failure):
            DrainSession(server.path, ME, seconds=0.5)
    finally:
        server.close()


def test_no_socket_or_nobody_listening_is_absent_and_a_non_socket_is_unconfirmed(tmp_path):
    with pytest.raises(SupervisorAbsent):
        DrainSession(str(tmp_path / "none.sock"), ME)
    stale = Path("/tmp") / f"fbd-stale-{os.getpid()}.sock"
    sock = socket.socket(socket.AF_UNIX)
    sock.bind(str(stale))
    sock.close()  # a socket file nobody listens on
    try:
        with pytest.raises(SupervisorAbsent):
            DrainSession(str(stale), ME)
    finally:
        stale.unlink()
    plain = tmp_path / "plain"
    plain.write_text("x")
    with pytest.raises(tool.Failure) as caught:
        DrainSession(str(plain), ME)
    assert caught.value.word == "drain-unconfirmed"


def test_root_helpers_are_found_only_in_fixed_directories_never_through_the_callers_path(monkeypatch):
    seen = {}

    def fake(argv, **kwargs):
        seen.update(argv=argv, env=kwargs["env"])
        return SimpleNamespace(returncode=0, stdout="")

    monkeypatch.setattr(tool.subprocess, "run", fake)
    monkeypatch.setenv("PATH", "/tmp/evil")
    assert tool._run(["systemctl", "daemon-reload"]) == (0, "")
    assert seen["argv"][0] in ("/usr/bin/systemctl", "/bin/systemctl", "/usr/sbin/systemctl", "/sbin/systemctl")
    assert seen["env"] == {"PATH": tool.SAFE_PATH, "LANG": "C"}  # a nested lookup (runuser -> env) cannot be redirected either
    with pytest.raises(FileNotFoundError):
        tool._run(["definitely-not-a-real-command"])


# --- sudo: the effective grant is exactly the documented rule -------------------------------------------------


def listing(*lines: str) -> str:
    return f"User {ACCOUNT} may run the following commands on host:\n" + "".join(f"    {line}\n" for line in lines)


@pytest.mark.parametrize("line", [
    f"(root) NOPASSWD: {SA2}",
    f"(root)   NOPASSWD:   {SA2}",
    f"(root : root) NOPASSWD: {SA2}",
    f"(root:root) NOPASSWD: {SA2}",
])
def test_the_exact_documented_grant_is_accepted_in_every_form_the_supported_sudo_prints(world, line):
    world.sudo = listing(line)
    assert installer(world).install() == "installed"


@pytest.mark.parametrize("lines", [
    [f"(ALL) NOPASSWD: {SA2}"],
    [f"(ALL : ALL) NOPASSWD: {SA2}"],
    [f"(ALL:ALL) NOPASSWD: {SA2}"],
    [f"(root : ALL) NOPASSWD: {SA2}"],
    [f"(ALL : root) NOPASSWD: {SA2}"],
    [f"(ubuntu) NOPASSWD: {SA2}"],
    [f"(root : ubuntu) NOPASSWD: {SA2}"],
    [f"(root, ubuntu) NOPASSWD: {SA2}"],
    [f"(#0) NOPASSWD: {SA2}"],
    [f"(%wheel) NOPASSWD: {SA2}"],
    [f"() NOPASSWD: {SA2}"],
    [f"NOPASSWD: {SA2}"],
    [f"(root) {SA2}"],
    [f"(root) PASSWD: {SA2}"],
    [f"(root) NOPASSWD: SETENV: {SA2}"],
    [f"(root) SETENV: NOPASSWD: {SA2}"],
    [f"(root) NOPASSWD: NOEXEC: {SA2}"],
    [f"(root) NOPASSWD: LOG_OUTPUT: {SA2}"],
    [f"(root) NOPASSWD: {SA2} *"],
    [f"(root) NOPASSWD: {SA2.replace(' stop', ' start')}"],
    [f"(root) NOPASSWD: {SA2.replace('-I -S', '-I')}"],
    [f"(root) NOPASSWD: {SA2}, /bin/true"],
    [f"(root) NOPASSWD: ALL"],
    [f"(root) NOPASSWD: {SA2}", "(root) NOPASSWD: /bin/true"],
    [f"(root) NOPASSWD: {SA2}", f"(ALL) NOPASSWD: {SA2}"],
    [f"(root) NOPASSWD: {SA2}", "(ALL : ALL) ALL"],
    [],
])
def test_any_wider_or_different_effective_grant_is_refused_by_install_and_verify(world, lines):
    ok = installer(world)
    ok.install()
    world.calls.clear()
    world.sudo = listing(*lines)
    for action in (ok.verify, installer(world).install):
        with pytest.raises(tool.Failure) as caught:
            action()
        assert (caught.value.word, caught.value.code) == ("sudoers-not-exact", EXIT_REFUSED)


def test_a_wider_run_as_changes_nothing_on_the_host(world):
    world.sudo = listing(f"(ALL) NOPASSWD: {SA2}")
    with pytest.raises(tool.Failure):
        installer(world).install()
    assert not dest(world).exists() and not enabled_link(world).exists() and world.calls == [["sudo", "-n", "-l", "-U", ACCOUNT]]


# --- recovery is verified, never assumed ---------------------------------------------------------------------------


def fail_places(monkeypatch, *, nth: set[int]):
    """Make the n-th (1-based) call of ``Installer._place`` fail the way a full or broken filesystem does."""
    real, count = Installer._place, [0]

    def place(self, data, *, replace):
        count[0] += 1
        if count[0] in nth:
            raise tool.Failure(EXIT_IO, "install-failed")
        return real(self, data, replace=replace)

    monkeypatch.setattr(Installer, "_place", place)
    return lambda: monkeypatch.setattr(Installer, "_place", real)  # stop injecting; the environment patches stay


def incomplete(call):
    with pytest.raises(tool.Failure) as caught:
        call()
    assert (caught.value.word, caught.value.code) == ("recovery-incomplete", tool.EXIT_RECOVERY)


def test_an_upgrade_whose_reload_fails_and_whose_old_bytes_cannot_be_put_back_is_recovery_incomplete(world, monkeypatch):
    old = stale_fragment(world)
    new = (REPO / tool.SOURCE_RELATIVE).read_bytes()
    world.reload_results = [1]
    heal = fail_places(monkeypatch, nth={2})  # the upgrade's own write works; the restoration write does not
    incomplete(installer(world).install)
    assert dest(world).read_bytes() == new and world.loaded == old  # nothing claims otherwise: the new bytes are on disk, unloaded
    heal()
    assert installer(world).install() == "installed"  # a later safe retry completes the upgrade
    assert world.loaded == new and installer(world).verify() == "installed"


def test_a_restored_earlier_revision_may_carry_its_own_environment_but_must_run_as_the_dedicated_account(world):
    old = stale_fragment(world)
    world.environment = "PATH=/usr/bin:/bin FB_FRAGMENT=old"  # an earlier revision's legitimate extra variable
    world.reload_results = [1, 0]
    with pytest.raises(tool.Failure) as caught:
        installer(world).install()
    assert (caught.value.word, caught.value.code) == ("reload-failed", EXIT_IO) and dest(world).read_bytes() == old
    world.user, world.reload_results = "someone-else", [1, 0]  # the restored revision would run as another account
    incomplete(installer(world).install)
    world.user, world.environment = ACCOUNT, "PATH=/usr/bin:/bin"
    assert installer(world).install() == "installed"


def test_the_forward_install_still_judges_the_effective_environment_exactly(world):
    world.environment = "PATH=/usr/bin:/bin FB_FRAGMENT=old"
    with pytest.raises(tool.Failure) as caught:
        installer(world).install()
    assert caught.value.word == "reload-failed"


def test_an_upgrade_restored_on_disk_but_whose_restoring_reload_fails_is_recovery_incomplete(world):
    old = stale_fragment(world)
    new = (REPO / tool.SOURCE_RELATIVE).read_bytes()
    world.reload_results = [1, 1]
    incomplete(installer(world).install)
    assert dest(world).read_bytes() == old and world.loaded == old  # byte-for-byte, root-owned 0644
    assert (dest(world).stat().st_uid, dest(world).stat().st_mode & 0o777) == (ME, 0o644)
    assert world.supervisor == "active" and world.running == old  # the running owner was never touched
    assert installer(world).install() == "installed" and world.loaded == new  # retry from this state


def test_an_upgrade_whose_restoring_reload_loads_an_unexpected_effective_fragment_is_recovery_incomplete(world):
    old = stale_fragment(world)
    world.reload_results = [1]
    world.after_reload = lambda: setattr(world, "dropins", "/etc/systemd/system/x.d/evil.conf")
    incomplete(installer(world).install)
    assert dest(world).read_bytes() == old
    world.after_reload, world.dropins = None, ""
    assert installer(world).install() == "installed"


def test_an_upgrade_whose_restoration_leaves_it_disabled_is_recovery_incomplete(world):
    old = stale_fragment(world)
    world.reload_results = [1]

    def lose_enablement():
        enabled_link(world).unlink(missing_ok=True)
        world.enable_fails = True

    world.after_reload = lose_enablement
    incomplete(installer(world).install)
    assert dest(world).read_bytes() == old
    world.after_reload, world.enable_fails = None, False
    assert installer(world).install() == "installed" and enabled_link(world).is_symlink()


def test_an_upgrade_that_changes_the_unit_state_while_restoring_is_recovery_incomplete(world):
    stale_fragment(world)
    world.reload_results = [1]

    def stop_unit():
        world.supervisor = "inactive"

    world.after_reload = stop_unit
    incomplete(installer(world).install)


def test_a_restoration_never_replaces_a_foreign_object_that_took_the_fragments_place(world):
    stale_fragment(world)
    world.reload_results = [1]

    def swap():
        dest(world).write_bytes(b"[Service]\nExecStart=/bin/false\n")
        dest(world).chmod(0o644)

    world.after_reload = swap
    incomplete(installer(world).install)
    assert dest(world).read_bytes() == b"[Service]\nExecStart=/bin/false\n"


def test_an_upgrade_that_wrote_new_bytes_and_then_failed_to_finish_the_write_is_restored(world, monkeypatch):
    old = stale_fragment(world)
    real = Installer._place

    def place(self, data, *, replace):
        real(self, data, replace=replace)  # the atomic rename happened ...
        if data != old:
            raise tool.Failure(EXIT_IO, "install-failed")  # ... then the directory sync failed

    monkeypatch.setattr(Installer, "_place", place)
    with pytest.raises(tool.Failure) as caught:
        installer(world).install()
    assert (caught.value.word, caught.value.code) == ("install-failed", EXIT_IO)
    assert dest(world).read_bytes() == old and world.loaded == old and world.running == old


def test_an_upgrade_that_failed_before_changing_anything_is_not_reloaded_or_reported_as_restored(world, monkeypatch):
    old = stale_fragment(world)
    fail_places(monkeypatch, nth={1})
    with pytest.raises(tool.Failure) as caught:
        installer(world).install()
    assert caught.value.word == "install-failed" and dest(world).read_bytes() == old and world.events == []


def test_the_successful_recoveries_still_report_the_original_failure(world):
    old = stale_fragment(world)
    world.reload_results = [1, 0]
    with pytest.raises(tool.Failure) as caught:
        installer(world).install()
    assert (caught.value.word, caught.value.code) == ("reload-failed", EXIT_IO)
    assert dest(world).read_bytes() == old and world.loaded == old


def removal_fixture(world):
    t = installed(world)
    world.state.mkdir(parents=True)
    return t, dest(world).read_bytes()


def test_a_removal_whose_reload_fails_and_whose_fragment_cannot_be_put_back_is_recovery_incomplete(world, monkeypatch):
    t, original = removal_fixture(world)
    world.reload_results = [1]
    heal = fail_places(monkeypatch, nth={1})
    incomplete(t.remove)
    assert not dest(world).exists()  # said plainly: the fragment is not there; nothing claims an owner
    assert world.state.is_dir() and not list(world.state.iterdir())
    heal()
    assert t.install() == "installed" and dest(world).read_bytes() == original  # operator response: install again
    assert t.remove() == "removed"


def test_a_removal_whose_fragment_is_back_but_whose_restoring_reload_fails_is_recovery_incomplete(world):
    t, original = removal_fixture(world)
    world.reload_results = [1, 1]
    incomplete(t.remove)
    assert dest(world).read_bytes() == original and (dest(world).stat().st_uid, dest(world).stat().st_mode & 0o777) == (ME, 0o644)
    assert t.remove() == "removed" and not dest(world).exists()


def test_a_removal_whose_restoring_reload_loads_an_unexpected_effective_fragment_is_recovery_incomplete(world):
    t, original = removal_fixture(world)
    world.reload_results = [1]
    world.after_reload = lambda: setattr(world, "dropins", "/etc/systemd/system/x.d/evil.conf")
    incomplete(t.remove)
    world.after_reload, world.dropins = None, ""
    assert t.remove() == "removed"


def test_a_removal_whose_restoration_cannot_enable_the_unit_is_recovery_incomplete(world):
    t, original = removal_fixture(world)
    world.reload_results = [1]
    world.enable_fails = True  # `disable` worked; `enable` cannot put it back
    incomplete(t.remove)
    assert dest(world).read_bytes() == original and not enabled_link(world).exists()
    world.enable_fails = False
    assert t.install() == "installed" and enabled_link(world).is_symlink()


def test_a_removal_whose_restoration_cannot_restart_the_owner_is_recovery_incomplete(world):
    t, original = removal_fixture(world)
    world.reload_results = [1]
    world.restart_fails = True
    incomplete(t.remove)
    assert dest(world).read_bytes() == original and world.supervisor != "active"  # not claimed as a running owner
    world.restart_fails, world.absent, world.supervisor = False, True, "inactive"  # the operator reset the failed unit
    assert t.remove() == "removed"


def test_a_failed_stop_followed_by_a_failed_restart_is_recovery_incomplete_not_stop_failed(world):
    t, _ = removal_fixture(world)
    world.stop_code, world.restart_fails = 1, True
    incomplete(t.remove)


def test_a_drain_refusal_whose_restart_fails_is_recovery_incomplete_not_a_pending_refusal(world):
    t, _ = removal_fixture(world)
    world.drain_reply, world.restart_fails = "pending", True
    incomplete(t.remove)
    assert world.supervisor != "active" and dest(world).exists()


def test_a_removal_restoration_never_replaces_a_foreign_object_that_took_the_fragments_place(world):
    t, _ = removal_fixture(world)
    world.reload_results = [1]
    world.after_reload = None
    real = Installer._place

    def place(self, data, *, replace):
        dest(world).write_bytes(b"[Service]\nExecStart=/bin/false\n")
        return real(self, data, replace=replace)

    Installer._place = place
    try:
        incomplete(t.remove)
    finally:
        Installer._place = real
    assert dest(world).read_bytes() == b"[Service]\nExecStart=/bin/false\n"


def test_incomplete_recovery_never_abandons_an_owned_invocation_and_removal_stays_unavailable(world, monkeypatch):
    t, _ = removal_fixture(world)
    world.reload_results = [1]
    heal = fail_places(monkeypatch, nth={1})
    incomplete(t.remove)
    heal()
    (world.state / "record-1.json").write_text("{}")  # an invocation now owned
    world.supervisor, world.absent = "inactive", True
    with pytest.raises(tool.Failure) as caught:
        installer(world).remove()
    assert (caught.value.word, caught.value.code) == ("invocation-pending", EXIT_PENDING)
    assert (world.state / "record-1.json").read_text() == "{}"
    assert not any(c[:2] == ["systemctl", "stop"] for c in world.calls[-6:])


def test_the_successful_removal_recoveries_still_report_the_original_failure_and_leave_a_running_owner(world):
    t, original = removal_fixture(world)
    world.reload_results = [1, 0]
    with pytest.raises(tool.Failure) as caught:
        t.remove()
    assert (caught.value.word, caught.value.code) == ("reload-failed", EXIT_IO)
    assert dest(world).read_bytes() == original and owner_left_behind(world)


# --- second remediation: manager exceptions, symmetric enablement, removal without a fragment ------------------------


def timeout():
    return subprocess.TimeoutExpired(["systemctl"], 60)


def upgrade_state_is_the_old_one(world, old, *, enabled):
    assert dest(world).read_bytes() == old and world.loaded == old and world.running == old
    assert (dest(world).stat().st_uid, dest(world).stat().st_mode & 0o777) == (ME, 0o644)
    assert enabled_link(world).is_symlink() == enabled and world.supervisor == "active"


@pytest.mark.parametrize("verb,nth,error,enabled", [
    ("daemon-reload", 1, timeout(), True), ("daemon-reload", 1, OSError(5, "io"), True),
    ("show", 2, timeout(), True), ("show", 2, FileNotFoundError("systemctl"), True),
    ("enable", 1, timeout(), False), ("enable", 1, OSError(5, "io"), False),
])
def test_a_manager_exception_during_an_upgrade_restores_the_earlier_fragment_and_reraises_it(world, verb, nth, error, enabled):
    old = stale_fragment(world)
    if not enabled:
        enabled_link(world).unlink()
    world.faults = [(verb, nth, error)]
    with pytest.raises(type(error)):
        installer(world).install()
    upgrade_state_is_the_old_one(world, old, enabled=enabled)
    assert installer(world).install() == "installed" and installer(world).verify() == "installed"  # a later safe retry


def test_a_manager_exception_reaches_the_entry_as_io_error_only_when_the_restoration_was_verified(world, capsys):
    old = stale_fragment(world)
    world.faults = [("daemon-reload", 1, timeout())]
    assert main(["install"], installer=installer(world)) == EXIT_IO == 13
    assert capsys.readouterr().err == "executor-supervisor io-error\n"
    upgrade_state_is_the_old_one(world, old, enabled=True)


@pytest.mark.parametrize("second", [timeout(), OSError(5, "io"), None])
def test_a_manager_exception_whose_restoration_cannot_be_verified_is_recovery_incomplete(world, capsys, second):
    old = stale_fragment(world)
    new = (REPO / tool.SOURCE_RELATIVE).read_bytes()
    world.faults = [("daemon-reload", 1, timeout())] + ([("daemon-reload", 2, second)] if second else [])
    if second is None:  # the restoring reload runs, but the manager then reports an unexpected effective fragment
        world.after_reload = lambda: setattr(world, "dropins", "/etc/systemd/system/x.d/evil.conf")
    assert main(["install"], installer=installer(world)) == tool.EXIT_RECOVERY == 15
    assert capsys.readouterr().err == "executor-supervisor recovery-incomplete\n"
    assert dest(world).read_bytes() == old and world.loaded == old  # the bytes were put back; nothing claims more
    world.after_reload, world.dropins = None, ""
    assert installer(world).install() == "installed" and world.loaded == new


def test_a_manager_exception_with_a_failing_restoration_write_is_recovery_incomplete_and_the_new_bytes_stay_visible(world, monkeypatch):
    old = stale_fragment(world)
    new = (REPO / tool.SOURCE_RELATIVE).read_bytes()
    world.faults = [("daemon-reload", 1, OSError(5, "io"))]
    heal = fail_places(monkeypatch, nth={2})
    incomplete(installer(world).install)
    assert dest(world).read_bytes() == new and world.loaded == old
    heal()
    assert installer(world).install() == "installed" and world.loaded == new


def test_an_interruption_or_programmer_error_during_an_upgrade_still_attempts_recovery_and_is_never_called_a_restoration(world):
    old = stale_fragment(world)
    for error in (KeyboardInterrupt(), ValueError("bug")):
        world.verb_calls.clear()
        world.faults = [("daemon-reload", 1, error)]
        with pytest.raises(type(error)):  # the original error, not a fixed word claiming a safe restoration
            installer(world).install()
        upgrade_state_is_the_old_one(world, old, enabled=True)
    world.verb_calls.clear()
    world.faults = [("daemon-reload", 1, KeyboardInterrupt()), ("daemon-reload", 2, timeout())]
    incomplete(installer(world).install)  # an interruption never hides a restoration that could not be verified
    assert world.loaded == old and dest(world).read_bytes() == old  # the bytes were put back before the failing reload


def test_a_disabled_unit_stays_disabled_when_the_upgrade_fails_after_enabling_it(world, capsys):
    old = stale_fragment(world)
    enabled_link(world).unlink()  # recognized, loaded, running, but disabled
    world.reload_results = [1, 0]
    assert main(["install"], installer=installer(world)) == EXIT_IO
    assert capsys.readouterr().err == "executor-supervisor reload-failed\n"
    assert "enable" in world.events and "disable" in world.events
    upgrade_state_is_the_old_one(world, old, enabled=False)
    assert installer(world).install() == "installed" and enabled_link(world).is_symlink()  # a later safe retry


def test_an_enabled_unit_stays_enabled_when_the_upgrade_fails_and_the_restoration_must_put_the_link_back(world):
    old = stale_fragment(world)
    world.reload_results = [1, 0]
    world.after_reload = lambda: enabled_link(world).unlink(missing_ok=True) if world.reload_results == [0] else None
    with pytest.raises(tool.Failure) as caught:
        installer(world).install()
    assert caught.value.word == "reload-failed"
    upgrade_state_is_the_old_one(world, old, enabled=True)
    world.after_reload = None
    assert installer(world).install() == "installed"


def test_an_original_disabled_state_that_cannot_be_restored_is_recovery_incomplete(world, capsys):
    old = stale_fragment(world)
    enabled_link(world).unlink()
    world.reload_results, world.disable_fails = [1, 0], True
    assert main(["install"], installer=installer(world)) == tool.EXIT_RECOVERY
    assert capsys.readouterr().err == "executor-supervisor recovery-incomplete\n"
    assert dest(world).read_bytes() == old and enabled_link(world).is_symlink()  # said plainly: still enabled
    world.disable_fails = False
    assert installer(world).install() == "installed" and installer(world).verify() == "installed"


def test_a_disable_that_exits_zero_but_leaves_the_link_is_recovery_incomplete(world):
    stale_fragment(world)
    enabled_link(world).unlink()
    world.reload_results = [1, 0]
    real = world._systemctl

    def keep_link(args):
        if args[0] == "disable":
            return 0, ""
        return real(args)

    world._systemctl = keep_link
    incomplete(installer(world).install)


def custom(world, **overrides) -> Installer:
    """The standard test installer with one seam (``run`` or ``drain``) replaced."""
    seams = {"run": world.runner, "drain": world.drain, **overrides}
    return Installer(world.repo, root=str(world.root), euid=lambda: ME, getpwnam=lambda name: ACCOUNT_ENTRY,
                     getgrnam=lambda name: SimpleNamespace(gr_gid=ACCOUNT_UID), trusted=(ME, os.getgid()), **seams)


def orphan(world):
    """The fragment and enablement are gone, but the system manager still holds and runs a copy loaded from them."""
    t = installed(world)
    original = dest(world).read_bytes()
    world.running = original
    dest(world).unlink()
    enabled_link(world).unlink()
    return t, original


def test_removal_refuses_a_running_supervisor_whose_fragment_is_absent_before_changing_anything(world, capsys):
    t, original = orphan(world)
    assert world.loaded == original and world.supervisor == "active"
    assert main(["remove"], installer=t) == EXIT_CONFLICT == 11
    assert capsys.readouterr().err == "executor-supervisor owner-without-fragment\n"
    assert world.events == [] and world.supervisor == "active" and world.running == original  # not drained, stopped or reloaded
    assert not any(c[:2] in (["systemctl", "stop"], ["systemctl", "daemon-reload"]) for c in world.calls)
    assert t.install() == "installed" and dest(world).read_bytes() == original and enabled_link(world).is_symlink()  # operator
    assert world.supervisor == "active" and world.running == original  # install left the running owner alone
    assert t.remove() == "removed" and not dest(world).exists() and world.supervisor == "inactive"  # then a real removal


@pytest.mark.parametrize("state", ["activating", "failed", "deactivating"])
def test_a_unit_that_is_not_inactive_without_a_fragment_refuses_removal(world, state):
    t, _ = orphan(world)
    world.supervisor = state
    with pytest.raises(tool.Failure) as caught:
        t.remove()
    assert (caught.value.word, caught.value.code) == ("owner-without-fragment", EXIT_CONFLICT) and world.events == []


def test_a_listener_with_an_inactive_unit_and_no_fragment_refuses_removal_without_draining_it(world):
    t, _ = orphan(world)
    world.supervisor = "inactive"  # the manager reports nothing running, yet a supervisor answers on the socket
    with pytest.raises(tool.Failure) as caught:
        t.remove()
    assert (caught.value.word, caught.value.code) == ("owner-without-fragment", EXIT_CONFLICT)
    assert "drain-request" not in world.events and "stop" not in world.events and all(s.closed for s in world.sessions)


def test_an_unobservable_unit_state_without_a_fragment_refuses_removal(world):
    t, _ = orphan(world)
    real = world.runner

    def failing(argv):
        if argv[:2] == ["systemctl", "show"] and not argv[2].startswith("user@"):
            return 1, ""
        return real(argv)

    t = custom(world, run=failing)
    with pytest.raises(tool.Failure) as caught:
        t.remove()
    assert (caught.value.word, caught.value.code) == ("drain-unconfirmed", EXIT_PENDING) and "drain-request" not in world.events


def test_a_supervisor_that_appears_after_the_refusal_check_and_cannot_be_recovered_is_recovery_incomplete(world, capsys):
    t, original = orphan(world)
    world.supervisor = "inactive"
    attempts = []

    def late_listener(path, uid):
        attempts.append(path)
        if len(attempts) == 1:  # the refusal check saw nobody listening
            raise SupervisorAbsent
        return FakeSession(world)

    world.reload_results = [1]  # dropping the unit fails after the owner was drained and stopped
    t = custom(world, drain=late_listener)
    assert main(["remove"], installer=t) == tool.EXIT_RECOVERY
    assert capsys.readouterr().err == "executor-supervisor recovery-incomplete\n"  # never a plain reload-failed
    assert not dest(world).exists() and not enabled_link(world).exists()  # said plainly: nothing persistent was left
    assert t.install() == "installed" and dest(world).read_bytes() == original  # operator response: install, then remove
    world.drain_reply = "empty"
    assert installer(world).remove() == "removed"


def test_removal_with_the_fragment_and_the_loaded_unit_both_absent_stays_idempotent(world):
    t, _ = orphan(world)
    world.supervisor, world.absent, world.loaded = "inactive", True, None
    assert t.remove() == "removed" and t.remove() == "removed"


def test_a_manager_exception_during_removal_after_the_owner_was_stopped_is_recovered_or_incomplete(world, capsys):
    t, original = removal_fixture(world)
    world.verb_calls.clear()
    world.faults = [("daemon-reload", 1, timeout())]
    with pytest.raises(subprocess.TimeoutExpired):
        t.remove()
    assert dest(world).read_bytes() == original and owner_left_behind(world)  # verified persistent owner
    world.verb_calls.clear()
    world.faults = [("daemon-reload", 1, timeout()), ("enable", 1, OSError(5, "io"))]
    assert main(["remove"], installer=t) == tool.EXIT_RECOVERY
    assert capsys.readouterr().err == "executor-supervisor recovery-incomplete\n"


# --- an unavailable unit-state observation can never verify itself; enable/disable status is part of the restoration ---

STATE_MODES = ["fail", "empty", "garbage", "missing"]


def untouched(world, old):
    assert dest(world).read_bytes() == old and world.loaded == old and world.running == old
    assert enabled_link(world).is_symlink() and world.supervisor == "active"
    assert world.events == [] and not [c for c in world.calls if c[:2] in (["systemctl", "enable"], ["systemctl", "disable"],
                                                                         ["systemctl", "daemon-reload"])]


@pytest.mark.parametrize("mode", STATE_MODES)
def test_an_unobservable_unit_state_before_an_upgrade_refuses_and_changes_nothing(world, mode, capsys):
    old = stale_fragment(world)
    world.state_fault = lambda: mode
    assert main(["install"], installer=installer(world)) == EXIT_IO
    assert capsys.readouterr().err == "executor-supervisor state-unavailable\n"
    untouched(world, old)
    world.state_fault = None
    assert installer(world).install() == "installed"  # a later safe retry


@pytest.mark.parametrize("mode", STATE_MODES)
def test_an_unobservable_state_while_the_unit_really_stopped_cannot_pass_as_equal(world, mode):
    old = stale_fragment(world)
    world.supervisor = "inactive"
    world.state_fault = lambda: mode
    with pytest.raises(tool.Failure) as caught:
        installer(world).install()
    assert caught.value.word == "state-unavailable" and dest(world).read_bytes() == old and world.events == []


@pytest.mark.parametrize("mode", STATE_MODES)
def test_an_unobservable_state_after_the_fragment_changed_is_recovery_incomplete(world, mode, capsys):
    old = stale_fragment(world)
    world.reload_results = [1]
    world.state_fault = lambda: mode if "reload" in world.events else None  # observable before, not after the upgrade began
    assert main(["install"], installer=installer(world)) == tool.EXIT_RECOVERY == 15
    assert capsys.readouterr().err == "executor-supervisor recovery-incomplete\n"
    assert dest(world).read_bytes() == old and world.loaded == old and enabled_link(world).is_symlink()  # said plainly
    world.state_fault = None
    assert installer(world).install() == "installed" and installer(world).verify() == "installed"


def test_a_failed_final_state_query_cannot_hide_a_state_that_really_changed(world):
    stale_fragment(world)
    world.reload_results = [1]

    def stop_and_hide():
        world.supervisor = "inactive"

    world.after_reload = stop_and_hide
    world.state_fault = lambda: "fail" if "reload" in world.events else None
    incomplete(installer(world).install)
    world.after_reload = world.state_fault = None
    world.supervisor = "active"
    assert installer(world).install() == "installed"


def test_a_verified_restoration_still_reports_the_original_failure_and_allows_a_retry(world):
    old = stale_fragment(world)
    world.reload_results = [1]
    with pytest.raises(tool.Failure) as caught:
        installer(world).install()
    assert (caught.value.word, caught.value.code) == ("reload-failed", EXIT_IO)
    upgrade_state_is_the_old_one(world, old, enabled=True)
    assert installer(world).install() == "installed"


@pytest.mark.parametrize("direction", ["enable", "disable"])
def test_a_restoring_enable_or_disable_that_fails_after_producing_the_link_is_recovery_incomplete(world, direction, capsys):
    old = stale_fragment(world)
    if direction == "disable":
        enabled_link(world).unlink()
        world.reload_results, world.disable_fails_after_effect = [1, 0], True
    else:
        world.reload_results = [1, 0]
        world.after_reload = lambda: enabled_link(world).unlink(missing_ok=True) if world.reload_results == [0] else None
        world.enable_fails_after_effect = True
    assert main(["install"], installer=installer(world)) == tool.EXIT_RECOVERY == 15
    assert capsys.readouterr().err == "executor-supervisor recovery-incomplete\n"
    assert dest(world).read_bytes() == old
    assert enabled_link(world).is_symlink() == (direction == "enable")  # the link does match; the manager's verdict decides
    world.after_reload = None
    world.enable_fails_after_effect = world.disable_fails_after_effect = False
    assert installer(world).install() == "installed" and installer(world).verify() == "installed"


def test_a_restoring_enable_that_exits_zero_without_the_link_is_recovery_incomplete(world):
    stale_fragment(world)
    world.reload_results = [1, 0]
    world.after_reload = lambda: enabled_link(world).unlink(missing_ok=True) if world.reload_results == [0] else None
    real = world._systemctl

    def no_link(args):
        return (0, "") if args[0] == "enable" and world.reload_results == [] and not enabled_link(world).exists() \
            and world.events.count("enable") == 0 else real(args)

    world._systemctl = no_link
    incomplete(installer(world).install)


# --- fourth remediation: enablement is observed strictly at every upgrade boundary --------------------------------------


def wants_fault(monkeypatch, world, *, when=lambda: True, error=None):
    """Make ``readlink`` of the wants link (and only that path) fail while ``when()`` holds."""
    real, target = os.readlink, str(enabled_link(world))

    def readlink(path, *a, **k):
        if str(path) == target and when():
            raise error or OSError(5, "Input/output error")
        return real(path, *a, **k)

    monkeypatch.setattr(os, "readlink", readlink)
    return lambda: monkeypatch.setattr(os, "readlink", real)  # stop injecting; the environment patches stay


def swap_link(world, how):
    """Replace the wants link with an object that is not the expected link."""
    link = enabled_link(world)
    link.unlink(missing_ok=True)
    if how == "file":
        link.write_text("not a link")
    elif how == "foreign-target":
        link.symlink_to("/etc/systemd/system/other.service")
    else:
        link.symlink_to(".")  # a malformed target that is not the unit


def assert_old_and_unmutated(world, old, *, enabled):
    assert dest(world).read_bytes() == old and world.loaded == old and world.running == old
    assert world.events == [] and not [c for c in world.calls if c[:2] in (["systemctl", "enable"], ["systemctl", "disable"],
                                                                         ["systemctl", "daemon-reload"])]
    assert enabled_link(world).is_symlink() == enabled


ERRORS = [OSError(5, "Input/output error"), PermissionError(13, "denied"), OSError(20, "not a directory")]


@pytest.mark.parametrize("enabled", [True, False])
@pytest.mark.parametrize("error", ERRORS)
def test_an_unobservable_wants_link_before_an_upgrade_refuses_with_one_fixed_word_and_changes_nothing(world, monkeypatch, capsys,
                                                                                                   error, enabled):
    old = stale_fragment(world)
    if not enabled:
        enabled_link(world).unlink()
    heal = wants_fault(monkeypatch, world, error=error)
    assert main(["install"], installer=installer(world)) == EXIT_IO == 13
    assert capsys.readouterr().err == "executor-supervisor enablement-unavailable\n"
    assert_old_and_unmutated(world, old, enabled=enabled)
    heal()
    assert installer(world).install() == "installed" and installer(world).verify() == "installed"  # a later safe retry


@pytest.mark.parametrize("how", ["file", "foreign-target", "malformed"])
@pytest.mark.parametrize("enabled", [True, False])
def test_a_wants_object_that_is_not_the_expected_link_before_an_upgrade_refuses_and_is_left_alone(world, capsys, how, enabled):
    old = stale_fragment(world)
    swap_link(world, how)
    before = (enabled_link(world).is_symlink(), os.readlink(enabled_link(world)) if enabled_link(world).is_symlink() else None)
    assert main(["install"], installer=installer(world)) == EXIT_IO
    assert capsys.readouterr().err == "executor-supervisor enablement-unavailable\n"
    assert dest(world).read_bytes() == old and world.loaded == old and world.events == []
    assert not [c for c in world.calls if c[:2] in (["systemctl", "enable"], ["systemctl", "disable"], ["systemctl", "daemon-reload"])]
    assert (enabled_link(world).is_symlink(), os.readlink(enabled_link(world)) if enabled_link(world).is_symlink() else None) == before
    enabled_link(world).unlink()
    assert installer(world).install() == "installed" and enabled_link(world).is_symlink()  # a later safe retry


def test_a_wants_link_that_never_existed_is_the_valid_disabled_state_and_both_expected_forms_are_enabled(world):
    t = installer(world)
    link = enabled_link(world)
    assert t._observed_enabled() is False  # genuine absence
    link.symlink_to(f"{tool.UNIT_DIR}/{UNIT}")
    assert t._observed_enabled() is True
    link.unlink()
    link.symlink_to(f"../{UNIT}")
    assert t._observed_enabled() is True
    shutil.rmtree(link.parent)  # no wants directory at all: still genuinely absent
    assert t._observed_enabled() is False


def test_a_disabled_unit_whose_forward_enable_succeeds_but_whose_later_observations_fail_is_recovery_incomplete(world, monkeypatch,
                                                                                                          capsys):
    old = stale_fragment(world)
    enabled_link(world).unlink()
    heal = wants_fault(monkeypatch, world, when=lambda: "enable" in world.events)
    assert main(["install"], installer=installer(world)) == tool.EXIT_RECOVERY == 15
    assert capsys.readouterr().err == "executor-supervisor recovery-incomplete\n"
    assert enabled_link(world).is_symlink()  # said plainly: the link the forward enable made is still there
    assert dest(world).read_bytes() == old and world.loaded == old  # bytes and loaded configuration were put back
    heal()
    assert installer(world).install() == "installed" and installer(world).verify() == "installed"  # a later safe retry


def test_an_enabled_unit_whose_restoration_time_observation_fails_is_recovery_incomplete(world, monkeypatch, capsys):
    old = stale_fragment(world)
    world.reload_results = [1, 0]
    heal = wants_fault(monkeypatch, world, when=lambda: "reload" in world.events)  # observable before and during the forward path
    assert main(["install"], installer=installer(world)) == tool.EXIT_RECOVERY == 15
    assert capsys.readouterr().err == "executor-supervisor recovery-incomplete\n"
    assert dest(world).read_bytes() == old and world.loaded == old and enabled_link(world).is_symlink()
    heal()
    assert installer(world).install() == "installed" and installer(world).verify() == "installed"


@pytest.mark.parametrize("how", ["file", "foreign-target", "malformed"])
def test_a_wants_object_that_appears_at_the_restoration_boundary_is_recovery_incomplete(world, capsys, how):
    old = stale_fragment(world)
    world.reload_results = [1, 0]
    world.after_reload = lambda: swap_link(world, how) if world.reload_results == [0] else None  # across the restoring reload
    assert main(["install"], installer=installer(world)) == tool.EXIT_RECOVERY
    assert capsys.readouterr().err == "executor-supervisor recovery-incomplete\n"
    assert dest(world).read_bytes() == old and world.loaded == old
    assert enabled_link(world).is_symlink() or enabled_link(world).exists()  # the foreign object was not touched
    world.after_reload = None
    enabled_link(world).unlink()
    assert installer(world).install() == "installed" and installer(world).verify() == "installed"


@pytest.mark.parametrize("how", ["file", "foreign-target"])
def test_a_wants_object_that_the_forward_enable_leaves_behind_is_recovery_incomplete(world, capsys, how):
    old = stale_fragment(world)
    enabled_link(world).unlink()
    real = world._systemctl

    def enable_then_swap(args):
        code, out = real(args)
        if args[0] == "enable":
            swap_link(world, how)  # the manager "enabled" it, but what is there is not the expected link
        return code, out

    world._systemctl = enable_then_swap
    assert main(["install"], installer=installer(world)) == tool.EXIT_RECOVERY
    assert capsys.readouterr().err == "executor-supervisor recovery-incomplete\n"
    assert dest(world).read_bytes() == old and world.loaded == old
    world._systemctl = real
    enabled_link(world).unlink()
    assert installer(world).install() == "installed" and installer(world).verify() == "installed"


def test_the_enablement_unobservable_after_the_upgrade_succeeded_cannot_be_hidden_by_an_equal_looking_restoration(world, monkeypatch):
    old = stale_fragment(world)
    world.reload_results = [1]
    heal = wants_fault(monkeypatch, world, when=lambda: "reload" in world.events)
    incomplete(installer(world).install)
    assert dest(world).read_bytes() == old and world.loaded == old
