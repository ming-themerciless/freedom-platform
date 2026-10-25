"""The persistent supervisor is a root-controlled *system* service running as the dedicated account.

These tests read the repository unit itself and bind everything else to it: the unit's exact interpreter flags are what the
hostile-environment proof runs, and its directory names are what the client, supervisor and installer agree on.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from adapters.executor import protocol
from adapters.executor.interrupt import SudoStopInvoker
from tools import executor_supervisor_install as tool

REPO = Path(__file__).resolve().parents[1]
UNIT_TEXT = (REPO / tool.SOURCE_RELATIVE).read_text()
INTERPRETER = "/opt/freedom-blades/runtime/venv-web/bin/python"


def section(name: str) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    current = None
    for line in UNIT_TEXT.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        if line.startswith("["):
            current = line.strip("[]")
            continue
        if current == name:
            key, _, value = line.partition("=")
            values.setdefault(key, []).append(value)
    return values


def test_the_fragment_is_a_system_unit_for_the_dedicated_user_and_group_wanted_by_the_system_target_only():
    service, install, unit = section("Service"), section("Install"), section("Unit")
    assert service["User"] == [tool.ACCOUNT] and service["Group"] == [tool.ACCOUNT]
    assert install == {"WantedBy": ["multi-user.target"]}  # never default.target: that is a user-manager target
    assert "default.target" not in UNIT_TEXT.replace("# ", "").split("[Install]")[1]
    assert service["Type"] == ["notify"] and service["Restart"] == ["always"]
    assert unit["StartLimitIntervalSec"] == ["0"]  # keeps retrying (fail-closed) while the user manager or its bus is not ready
    assert unit["ConditionPathExists"] == [f"!/etc/systemd/user/{tool.UNIT}"]  # never beside a legacy user-service candidate
    assert tool.MARKER.decode().strip() in UNIT_TEXT.splitlines()


def test_the_interpreter_is_absolute_and_ignores_every_python_environment_variable_and_user_site():
    (exec_start,) = section("Service")["ExecStart"]
    argv = exec_start.split()
    assert argv == [INTERPRETER, "-E", "-s", "-m", "adapters.executor.supervisor"]
    assert tool.INTERPRETER == INTERPRETER


def test_the_environment_is_deterministic_and_minimal():
    assert section("Service")["Environment"] == ["PATH=/usr/bin:/bin"]  # nothing is inherited from the manager's or the account's
    assert not [line for line in UNIT_TEXT.splitlines() if line.startswith(("PassEnvironment", "EnvironmentFile")) or "PYTHON" in line.split("#")[0]]


def test_directories_client_supervisor_and_installer_agree():
    service = section("Service")
    assert service["StateDirectory"] == [protocol.DIRECTORY_NAME] and service["RuntimeDirectory"] == [protocol.DIRECTORY_NAME]
    assert service["StateDirectoryMode"] == ["0700"] and service["RuntimeDirectoryMode"] == ["0700"]
    assert protocol.RUNTIME_ROOT == f"/run/{protocol.DIRECTORY_NAME}" and protocol.STATE_ROOT == f"/var/lib/{protocol.DIRECTORY_NAME}"
    assert protocol.SOCKET_PATH == f"{protocol.RUNTIME_ROOT}/{protocol.SOCKET_NAME}"
    assert SudoStopInvoker()._path == protocol.SOCKET_PATH  # the executor reaches the system service's socket by default
    assert (tool.RUNTIME_ROOT, tool.STATE_ROOT) == (protocol.RUNTIME_ROOT, protocol.STATE_ROOT)
    assert tool.UNIT_DIR == "/etc/systemd/system" and tool.WANTS_DIR == "/etc/systemd/system/multi-user.target.wants"


def test_the_installer_never_enables_anything_in_a_user_manager():
    source = (REPO / "tools/executor_supervisor_install.py").read_text()
    code = source.split("class Installer")[1]
    assert '"--global"' not in code and '"enable"' in code and '"disable"' in code  # system-manager enable/disable only
    assert "default.target.wants" not in code  # the global user wants directory appears only in the legacy *detection* constants
    assert tool.LEGACY_USER == ("/etc/systemd/user", "/etc/systemd/user/default.target.wants")


# --- the real interpreter, hostile environment ------------------------------------------------------------


IMPORT_THE_SUPERVISOR = textwrap.dedent(
    """
    import sys
    import adapters.executor.supervisor
    try:  # the pinned dependency is absent from some developer venvs; the host proofs always have it
        import adapters.executor.userbus, jeepney
    except ModuleNotFoundError:
        pass
    print("\\n".join(sorted({m.__file__ for m in sys.modules.values() if getattr(m, "__file__", None)})))
    """
)


@pytest.fixture
def decoys(tmp_path):
    """Decoys for every channel an account or manager environment could use; each one records that it ran."""
    mark = tmp_path / "ran"
    code = f"open({str(mark)!r}, 'a').write(__name__ + '\\n')\n"
    path, base = tmp_path / "pythonpath", tmp_path / "userbase"
    (path / "jeepney").mkdir(parents=True)
    (path / "jeepney" / "__init__.py").write_text(code)
    (path / "sitecustomize.py").write_text(code)
    (path / "adapters").mkdir()
    (path / "adapters" / "__init__.py").write_text(code)
    user_site = base / f"lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages"
    user_site.mkdir(parents=True)
    (user_site / "usercustomize.py").write_text(code)
    return mark, {"PYTHONPATH": str(path), "PYTHONUSERBASE": str(base), "PYTHONHOME": "/nonexistent-python-home",
                  "PYTHONSTARTUP": str(path / "sitecustomize.py"), "PYTHONINSPECT": "1", "PYTHONWARNINGS": "error", "PYTHONOPTIMIZE": "2"}


def unit_flags() -> list[str]:
    argv = section("Service")["ExecStart"][0].split()
    return argv[1 : argv.index("-m")]


def run_python(flags, env, cwd=REPO):
    return subprocess.run([sys.executable, *flags, "-c", IMPORT_THE_SUPERVISOR], capture_output=True, text=True, cwd=cwd, env=env,
                          timeout=60, check=False)


def test_the_hostile_environment_really_redirects_a_python_that_honors_it(decoys):
    """The control: without the unit's flags the same environment hijacks the import (so the next test proves something)."""
    mark, hostile = decoys
    assert run_python([], {"PATH": "/usr/bin:/bin", **hostile, "PYTHONHOME": ""}).returncode == 0
    ran = mark.read_text().split() if mark.exists() else []
    assert "jeepney" in ran and "sitecustomize" in ran  # PYTHONPATH decoys ran
    assert run_python([], {"PATH": "/usr/bin:/bin", **hostile}).returncode != 0  # and a bad PYTHONHOME stops the interpreter outright
    mark.unlink()
    assert run_python(["-s"], {"PATH": "/usr/bin:/bin", **hostile, "PYTHONHOME": ""}).returncode == 0  # `-s` alone is not enough: PYTHONPATH still wins
    assert "jeepney" in mark.read_text().split()


def test_with_the_units_flags_no_account_or_manager_controlled_python_setting_changes_what_is_imported(decoys):
    mark, hostile = decoys
    done = run_python(unit_flags(), {"PATH": "/usr/bin:/bin", **hostile})
    assert done.returncode == 0, done.stderr
    assert not mark.exists()  # no decoy ran: not sitecustomize, not usercustomize, not the planted jeepney or adapters
    imported = [Path(name) for name in done.stdout.split()]
    roots = (REPO, Path(sys.prefix), Path(sys.base_prefix), Path(sys.base_exec_prefix))
    assert imported and all(any(root in path.parents for root in roots) for path in imported), imported
    assert not [path for path in imported if str(decoys[1]["PYTHONPATH"]) in str(path) or decoys[1]["PYTHONUSERBASE"] in str(path)]
    assert Path(REPO / "adapters/executor/supervisor.py") in imported  # the validated tree's own supervisor, not a planted copy


def test_the_units_flags_also_ignore_a_planted_module_next_to_an_unrelated_working_directory(decoys, tmp_path):
    """The service's working directory is the root-owned code root; an attacker-writable cwd would not be one."""
    mark, hostile = decoys
    done = run_python(unit_flags(), {"PATH": "/usr/bin:/bin", **hostile}, cwd=REPO)
    assert done.returncode == 0 and not mark.exists()
