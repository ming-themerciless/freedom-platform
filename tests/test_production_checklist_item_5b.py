"""The production read-only checklist's item 5b (handback §6) is executable text: it must inspect only the fixed dedicated account,
refuse malformed account facts before any account-context command, never ask the manager for free-form properties, and never let
a failed fact-gathering command look like a complete search."""

from __future__ import annotations

import json
import os
import re
import socket
import stat
import subprocess
import sys
from pathlib import Path

import pytest

HANDBACK = Path(__file__).resolve().parents[1] / "docs/review/route-3-production-readiness-handback.md"
ROOT_RECORD = "root:x:0:0:root:/root:/bin/bash"
DECOY = "DECOY_DESCRIPTION_SHOULD_NOT_PRINT"


def script() -> str:
    text = HANDBACK.read_text()
    match = re.search(r"\n## 6\. Production-specific read-only fact checklist.*?```bash\n(.*?)\n```", text, re.S)
    assert match, "the §6 script is missing"
    return match[1]


def section(start: str, end: str) -> str:
    body = script()
    return body[body.index(start): body.index(end)]


def item_5b() -> str:
    return section("# 5b the dedicated account's own user manager", "# 6  Polkit")


def item_5() -> str:
    return section("# 5  fragments, drop-ins", "# 5b the dedicated")


def prelude() -> str:
    return section("set -u", "# 1  OS, kernel")


def test_the_account_is_a_literal_and_the_environment_cannot_redirect_it():
    block = item_5b()
    assert re.search(r"^ACCOUNT=freedom-executor(\s+#.*)?$", block, re.M)
    assert not re.search(r"\$\{?ACCOUNT:?[-=]", block) and "ACCOUNT:-" not in script()
    assert re.search(r"^RUN_USER_DIR=/run/user(\s+#.*)?$", block, re.M), "the one test seam must stay a literal line"


def test_no_checklist_command_prints_free_form_unit_properties():
    body = script()
    commands = [line for line in body.splitlines() if not line.lstrip().startswith("#")]
    assert not [line for line in commands if "list-units" in line]
    assert not [line for line in commands if re.search(r"systemctl\b.*\b(cat|status)\b", line)]
    shows = [line for line in commands if re.search(r"systemctl( --user)? show ['\w*-]", line) and "user@" not in line]
    for line in shows:  # every show asks only for named properties
        assert re.search(r"\s-p ?[A-Z]\w+", line), line
        assert not re.search(r"-pDescription|-pExecStart|-pEnvironment|--all\b", line), line


def test_no_path_producer_is_followed_by_an_unchecked_copy_or_a_status_masking_pipeline():
    commands = [line for line in script().splitlines() if not line.lstrip().startswith("#")]
    assert not [line for line in commands if re.search(r"\bcp \"?\$OUT/last\.out", line)], "a copy of an unchecked result"
    assert not [line for line in commands if re.search(r"getent[^|]*\|\s*cut", line)], "a pipeline hides the getent status"


def test_the_script_parses():
    assert subprocess.run(["/bin/bash", "-n", "/dev/stdin"], input=script(), text=True, check=False).returncode == 0


def stub(directory: Path, name: str, body: str) -> None:
    path = directory / name
    path.write_text("#!/bin/bash\n" + body)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


RUNUSER = r'''#!%(python)s
import json, sys
cfg = json.load(open(%(cfg)r))
args = sys.argv[1:]
open(%(log)r, "a").write("runuser " + " ".join(args) + "\n")
inner = args[args.index("--") + 1:]
assert inner[:2] == ["env", "-i"], inner
index = 2
while "=" in inner[index]:
    index += 1
cmd = inner[index:]
if cmd[0] == "systemd-analyze":
    sys.stdout.write(cfg["paths_out"])
    sys.stderr.write(cfg["paths_err"])
    sys.exit(cfg["paths_rc"])
assert cmd[0] == "systemctl" and cmd[1] == "--user", cmd
if cmd[2] == "list-unit-files":
    sys.stdout.write(cfg["list_out"])
    sys.exit(cfg["list_rc"])
assert cmd[2] == "show", cmd
requested = [a[2:] for a in cmd if a.startswith("-p")]
for unit in cfg["units"]:  # a real manager prints exactly the requested properties; the stub knows a decoy Description
    for prop in requested:
        print(f"{prop}={unit.get(prop, '')}")
    print()
sys.exit(cfg["show_rc"])
'''


def fake_runtime(root: Path, uid: int, *, bus: bool = True) -> Path:
    runtime = root / str(uid)
    runtime.mkdir(parents=True)
    if bus:
        here = os.getcwd()
        os.chdir(runtime)  # a short relative name keeps the socket path under the AF_UNIX length limit
        try:
            listener = socket.socket(socket.AF_UNIX)
            listener.bind("bus")
            listener.close()
        finally:
            os.chdir(here)
    return root


def run(tmp_path: Path, *, entry: str | None, rc: int = 0, ambient: str | None = "root", root_entry: str | None = ROOT_RECORD,
        root_rc: int = 0, runtime_root: Path | None = None, cfg: dict | None = None, extra_stubs: dict | None = None):
    """Run the real prelude and the real 5b block with stubs for the account database, ``runuser`` and the root-context managers."""
    bin_dir, scratch = tmp_path / "bin", tmp_path / "scratch"
    bin_dir.mkdir()
    scratch.mkdir()
    log = tmp_path / "calls.log"
    log.write_text("")
    (tmp_path / "entry").write_text("" if entry is None else entry + "\n")
    (tmp_path / "root-entry").write_text("" if root_entry is None else root_entry + "\n")
    stub(bin_dir, "getent", f'echo "getent $*" >> {log}\n'
         f'if [ "$1 $2" = "passwd root" ]; then cat {tmp_path / "root-entry"}; exit {root_rc}; fi\n'
         f'if [ "$2" = freedom-executor ]; then cat {tmp_path / "entry"}; exit {rc}; fi\n'
         "exit 2\n")
    for name in ("systemd-analyze", "systemctl"):  # item 5b must never run these in root's own context
        stub(bin_dir, name, f'echo "{name} $*" >> {log}\nexit 0\n')
    config = {"paths_out": "", "paths_err": "", "paths_rc": 0, "list_out": "", "list_rc": 0, "show_rc": 0, "units": []}
    config.update(cfg or {})
    (tmp_path / "cfg.json").write_text(json.dumps(config))
    runuser = bin_dir / "runuser"
    runuser.write_text(RUNUSER % {"python": sys.executable, "cfg": str(tmp_path / "cfg.json"), "log": str(log)})
    runuser.chmod(0o755)
    for name, body in (extra_stubs or {}).items():
        stub(bin_dir, name, body.replace("@LOG@", str(log)))
    runtime = runtime_root if runtime_root is not None else tmp_path / "run-user"
    block, count = re.subn(r"^RUN_USER_DIR=/run/user(?=\s)", f"RUN_USER_DIR={runtime}", item_5b(), count=1, flags=re.M)  # the documented seam
    assert count == 1
    block, count = re.subn(r"^PROBE_PY=/usr/bin/python3\.14(?=\s)", f"PROBE_PY={sys.executable}", block, count=1, flags=re.M)
    assert count == 1
    text = prelude() + block
    (tmp_path / "check.sh").write_text(text)
    env = {"PATH": f"{bin_dir}:/usr/bin:/bin", "LANG": "C", "TMPDIR": str(scratch)}
    if ambient is not None:
        env["ACCOUNT"] = ambient
    done = subprocess.run(["/bin/bash", str(tmp_path / "check.sh")], capture_output=True, text=True, env=env, timeout=30, check=False)
    assert list(scratch.iterdir()) == [], "the scratch directory must not outlive the script, success or failure"
    return done, log.read_text()


def account(tmp_path: Path, *, bus: bool = True):
    """A real home and runtime directory owned by the current uid, so every fact validates without root."""
    home = tmp_path / "home"
    home.mkdir()
    uid = os.getuid()
    entry = f"freedom-executor:x:{uid}:{os.getgid()}::{home}:/usr/sbin/nologin"
    return home, uid, entry, fake_runtime(tmp_path / "ru", uid, bus=bus)


def only_runuser_ran(log: str) -> bool:
    return not [line for line in log.splitlines() if line.startswith(("systemd-analyze", "systemctl"))]


def test_a_conflicting_ambient_account_is_ignored_and_only_the_dedicated_account_is_looked_up(tmp_path):
    done, log = run(tmp_path, entry=None, rc=2, ambient="root")
    assert done.returncode == 0 and "[account absent] DEFERRED" in done.stdout
    assert [line for line in log.splitlines() if line.startswith("getent") and line.split()[2] != "root"] == ["getent passwd freedom-executor"]
    assert "runuser" not in log  # nothing ran in any account's context


@pytest.mark.parametrize("label,entry,expect", [
    ("root uid", "freedom-executor:x:0:0::/home/fe:/usr/sbin/nologin", "uid is not a positive number"),
    ("empty uid", "freedom-executor:x::0::/home/fe:/usr/sbin/nologin", "uid is not a positive number"),
    ("non-numeric uid", "freedom-executor:x:abc:0::/home/fe:/usr/sbin/nologin", "uid is not a positive number"),
    ("another account", "root:x:5:5::/home/fe:/usr/sbin/nologin", "not for freedom-executor"),
    ("slash home", "freedom-executor:x:997:997::/:/usr/sbin/nologin", "home is not a dedicated absolute directory"),
    ("root home", "freedom-executor:x:997:997::/root:/usr/sbin/nologin", "home is not a dedicated absolute directory"),
    ("empty home", "freedom-executor:x:997:997:::/usr/sbin/nologin", "home is not a dedicated absolute directory"),
    ("relative home", "freedom-executor:x:997:997::home/fe:/usr/sbin/nologin", "home is not a dedicated absolute directory"),
    ("dotdot home", "freedom-executor:x:997:997::/home/../root:/usr/sbin/nologin", "home is not a dedicated absolute directory"),
    ("missing home", "freedom-executor:x:997:997::/nonexistent-fe-home:/usr/sbin/nologin", "home is not a directory owned by uid"),
    ("two entries", "freedom-executor:x:997:997::/home/a:/bin/false\nfreedom-executor:x:998:998::/home/b:/bin/false", "more than one"),
    ("too few fields", "freedom-executor:x:997:997::/home/a", "malformed"),
    ("too many fields", "freedom-executor:x:997:997::/home/a:/bin/false:extra", "malformed"),
])
def test_malformed_account_facts_are_refused_before_any_account_context_command(tmp_path, label, entry, expect):
    done, log = run(tmp_path, entry=entry, ambient="root")
    assert done.returncode == 0 and expect in done.stdout and "item 5b not run" in done.stdout, done.stdout
    assert "runuser" not in log and only_runuser_ran(log)
    assert "[rc=0] getent passwd freedom-executor" in done.stdout


def test_an_account_database_failure_is_a_finding_not_a_deferral(tmp_path):
    done, log = run(tmp_path, entry=None, rc=3)
    assert "[rc=3] getent passwd freedom-executor" in done.stdout and "could not be queried" in done.stdout and "DEFERRED" not in done.stdout
    assert "runuser" not in log


@pytest.mark.parametrize("label,root_entry,root_rc,expect", [
    ("lookup failure", None, 1, "root's account record could not be read"),
    ("enumeration unsupported", None, 3, "root's account record could not be read"),
    ("failure that still printed a record", ROOT_RECORD, 2, "root's account record could not be read"),
    ("empty record", None, 0, "malformed"),
    ("duplicate records", ROOT_RECORD + "\n" + ROOT_RECORD, 0, "more than one"),
    ("not root", "daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin", 0, "malformed"),
    ("uid not zero", "root:x:5:0:root:/root:/bin/bash", 0, "malformed"),
    ("relative home", "root:x:0:0:root:root:/bin/bash", 0, "malformed"),
    ("empty home", "root:x:0:0:root::/bin/bash", 0, "malformed"),
    ("too few fields", "root:x:0:0:root:/root", 0, "malformed"),
    ("too many fields", "root:x:0:0:root:/root:/bin/bash:extra", 0, "malformed"),
])
def test_an_unavailable_duplicate_or_malformed_root_record_is_a_finding_and_nothing_runs_in_an_account_context(
        tmp_path, label, root_entry, root_rc, expect):
    home, uid, entry, runtime_root = account(tmp_path)
    done, log = run(tmp_path, entry=entry, root_entry=root_entry, root_rc=root_rc, runtime_root=runtime_root)
    assert expect in done.stdout and "item 5b not run" in done.stdout, done.stdout
    assert f"[rc={root_rc}] getent passwd root" in done.stdout
    assert "runuser" not in log and only_runuser_ran(log)


def test_a_home_equal_to_roots_home_is_refused_even_when_it_looks_dedicated(tmp_path):
    done, log = run(tmp_path, entry="freedom-executor:x:997:997::/srv/shared:/usr/sbin/nologin",
                    root_entry="root:x:0:0:root:/srv/shared:/bin/bash")
    assert "home is not a dedicated absolute directory" in done.stdout and "runuser" not in log


def test_a_nonstandard_root_home_with_a_trailing_slash_still_collides(tmp_path):
    done, log = run(tmp_path, entry="freedom-executor:x:997:997::/srv/shared:/usr/sbin/nologin",
                    root_entry="root:x:0:0:root:/srv/shared/:/bin/bash")
    assert "home is not a dedicated absolute directory" in done.stdout and "runuser" not in log


def test_an_unavailable_account_bus_is_a_finding_and_nothing_runs_in_the_account_context(tmp_path):
    home, uid, entry, runtime_root = account(tmp_path, bus=False)
    done, log = run(tmp_path, entry=entry, runtime_root=runtime_root)
    assert "no runtime directory or bus" in done.stdout and "item 5b not run" in done.stdout
    assert "runuser" not in log


def test_a_missing_runtime_directory_is_a_finding(tmp_path):
    home, uid, entry, _ = account(tmp_path)
    done, log = run(tmp_path, entry=entry, runtime_root=tmp_path / "no-such-run-dir")
    assert "no runtime directory or bus" in done.stdout and "runuser" not in log


GOOD_PATHS = "/etc/systemd/user\n/usr/lib/systemd/user\n"


def good_cfg(home: Path, uid: int, **override):
    config = {"paths_out": f"{GOOD_PATHS}{home}/.config/systemd/user\n/run/user/{uid}/systemd/user\n", "units": []}
    config.update(override)
    return config


def test_a_valid_account_and_a_complete_search_report_every_material_status(tmp_path):
    home, uid, entry, runtime_root = account(tmp_path)
    done, log = run(tmp_path, entry=entry, runtime_root=runtime_root, cfg=good_cfg(home, uid, list_out="freedom-blades-executor-supervisor.service enabled\n"))
    out = done.stdout
    assert done.returncode == 0, done.stderr
    for status in ("[rc=0] getent passwd root", "[rc=0] getent passwd freedom-executor", "[rc=0] asacct systemd-analyze --user unit-paths"):
        assert status in out, out
    assert "user-paths under the account home:" in out and "user-paths under the account runtime dir:" in out
    assert "[rc=0] sort" in out and re.search(r"searched \d+ user-path directories", out)
    assert len(re.findall(r"^\[rc=\d+\] find ", out, re.M)) >= 8  # every effective directory, home and runtime path
    assert "[rc=0] asacct systemctl --user list-unit-files" in out and "[rc=0] asacct systemctl --user show" in out
    assert "[item 5b COMPLETE]" in out and "INCOMPLETE" not in out
    runuser = [line for line in log.splitlines() if line.startswith("runuser")]
    runtime = f"{runtime_root}/{uid}"
    prefix = f"runuser -u freedom-executor -- env -i PATH=/usr/bin:/bin HOME={home} XDG_RUNTIME_DIR={runtime} DBUS_SESSION_BUS_ADDRESS=unix:path={runtime}/bus "
    assert runuser and all(line.startswith(prefix) for line in runuser), runuser  # never another account, home, runtime or bus
    assert only_runuser_ran(log)
    assert len([line for line in runuser if " show " in line]) == 2
    assert not [line for line in runuser if "list-units" in line or " cat " in line or " status " in line]


@pytest.mark.parametrize("label,paths_out", [("empty output", ""), ("partial output", "/etc/systemd/user\n/usr/lib/sys")])
@pytest.mark.parametrize("rc", [1, 127])
def test_a_failed_account_unit_path_discovery_runs_no_search_and_no_unit_query(tmp_path, label, paths_out, rc):
    home, uid, entry, runtime_root = account(tmp_path)
    done, log = run(tmp_path, entry=entry, runtime_root=runtime_root,
                    cfg=good_cfg(home, uid, paths_out=paths_out, paths_err="Failed to connect to bus\n", paths_rc=rc))
    out = done.stdout
    assert f"[rc={rc}] asacct systemd-analyze --user unit-paths" in out and "[item 5b INCOMPLETE]" in out and "COMPLETE]" not in out.replace("INCOMPLETE]", "")
    assert "] find " not in out and "user-paths under" not in out and not re.search(r"searched \d+", out)
    assert "/usr/lib/sys" not in out  # the partial answer is never presented as a path set
    assert len([line for line in log.splitlines() if line.startswith("runuser")]) == 1  # no list-unit-files, no show


def test_a_failure_to_create_the_saved_unit_path_result_runs_nothing_as_if_the_path_set_existed(tmp_path):
    home, uid, entry, runtime_root = account(tmp_path)
    # a scratch directory that already holds a directory where the result file must go: the save itself cannot succeed
    plant = 'd=$(/usr/bin/mktemp -d) || exit 1\n/usr/bin/mkdir "$d/user-paths"\necho "$d"\n'
    done, log = run(tmp_path, entry=entry, runtime_root=runtime_root, cfg=good_cfg(home, uid), extra_stubs={"mktemp": plant})
    out = done.stdout
    assert "[item 5b INCOMPLETE]" in out and "] find " not in out and "user-paths under" not in out
    assert not [line for line in log.splitlines() if line.startswith("runuser") and "unit-paths" not in line]


def test_a_failure_while_normalizing_the_path_set_runs_no_search_and_no_unit_query(tmp_path):
    home, uid, entry, runtime_root = account(tmp_path)
    done, log = run(tmp_path, entry=entry, runtime_root=runtime_root, cfg=good_cfg(home, uid),
                    extra_stubs={"sort": 'echo "sort $*" >> @LOG@\necho "sort: write failed" >&2\nexit 2\n'})
    out = done.stdout
    assert "[rc=2] sort" in out and "[item 5b INCOMPLETE]" in out and "] find " not in out
    assert len([line for line in log.splitlines() if line.startswith("runuser")]) == 1


@pytest.mark.skipif(os.geteuid() == 0, reason="an append to a read-only file succeeds for root")
def test_a_failure_while_appending_the_dynamic_paths_runs_no_search_and_no_unit_query(tmp_path):
    home, uid, entry, runtime_root = account(tmp_path)
    # the saved result is made read-only right after it is shown, so the append that follows cannot succeed
    readonly = 'chmod 444 "$TMPDIR"/tmp.*/user-paths 2>/dev/null\nexec /usr/bin/cat "$@"\n'
    done, log = run(tmp_path, entry=entry, runtime_root=runtime_root, cfg=good_cfg(home, uid), extra_stubs={"cat": readonly})
    out = done.stdout
    assert "[item 5b INCOMPLETE]" in out and "] find " not in out and not re.search(r"searched \d+", out)
    assert len([line for line in log.splitlines() if line.startswith("runuser")]) == 1


def test_a_transient_unit_whose_description_is_a_decoy_reports_identifier_and_allowlisted_state_only(tmp_path):
    home, uid, entry, runtime_root = account(tmp_path)
    unit = {"Id": "freedom-executor-stop-decoy.service", "LoadState": "loaded", "ActiveState": "active", "SubState": "running",
            "FragmentPath": f"/run/user/{uid}/systemd/transient/freedom-executor-stop-decoy.service", "DropInPaths": "",
            "SourcePath": "", "UnitFileState": "transient", "Description": DECOY, "Environment": f"{DECOY}_ENV=secretvalue",
            "ExecStart": f"{DECOY}_ARG"}
    done, log = run(tmp_path, entry=entry, runtime_root=runtime_root, cfg=good_cfg(home, uid, units=[unit]))
    out = done.stdout
    assert "Id=freedom-executor-stop-decoy.service" in out and "ActiveState=active" in out and "SubState=running" in out
    assert "FragmentPath=" in out and "transient" in out
    assert out.count("DECOY") == 0 and "secretvalue" not in out, out  # the decoy appears zero times
    assert "[item 5b COMPLETE]" in out


@pytest.mark.parametrize("rc,out", [(1, ""), (1, "/partial-marker-dir"), (127, "")])
def test_item_5_searches_no_system_directory_when_the_system_path_set_was_not_formed(tmp_path, rc, out):
    bin_dir, scratch = tmp_path / "bin", tmp_path / "scratch"
    bin_dir.mkdir()
    scratch.mkdir()
    stub(bin_dir, "systemd-analyze", f'printf %s {out!r}\nexit {rc}\n')
    for name in ("systemctl", "systemd-delta"):
        stub(bin_dir, name, "exit 0\n")
    (tmp_path / "check.sh").write_text(prelude() + item_5())
    env = {"PATH": f"{bin_dir}:/usr/bin:/bin", "LANG": "C", "TMPDIR": str(scratch)}
    done = subprocess.run(["/bin/bash", str(tmp_path / "check.sh")], capture_output=True, text=True, env=env, timeout=30, check=False)
    assert f"[rc={rc}] systemd-analyze unit-paths" in done.stdout and "item 5 is incomplete" in done.stdout
    assert "] find " not in done.stdout and "/partial-marker-dir" not in done.stdout
    assert list(scratch.iterdir()) == []


def test_item_5_searches_the_system_directories_when_the_path_set_was_formed(tmp_path):
    bin_dir, scratch = tmp_path / "bin", tmp_path / "scratch"
    bin_dir.mkdir()
    scratch.mkdir()
    stub(bin_dir, "systemd-analyze", f"printf '%s\\n' {tmp_path}\nexit 0\n")
    for name in ("systemctl", "systemd-delta"):
        stub(bin_dir, name, "exit 0\n")
    (tmp_path / "check.sh").write_text(prelude() + item_5())
    env = {"PATH": f"{bin_dir}:/usr/bin:/bin", "LANG": "C", "TMPDIR": str(scratch)}
    done = subprocess.run(["/bin/bash", str(tmp_path / "check.sh")], capture_output=True, text=True, env=env, timeout=30, check=False)
    assert "[rc=0] systemd-analyze unit-paths" in done.stdout and "[rc=0] append the fixed override and generator directories" in done.stdout
    assert len(re.findall(r"^\[rc=\d+\] find ", done.stdout, re.M)) == 10 and "item 5 is incomplete" not in done.stdout


def test_a_failed_directory_search_makes_item_5b_incomplete_and_is_never_read_as_absence(tmp_path):
    home, uid, entry, runtime_root = account(tmp_path)
    # find fails on an existing directory (an I/O or permission error): stat succeeds, so absence was not established
    failing = f'echo "find $*" >> @LOG@\ncase "$1" in {home}/.config/systemd/user) echo "find: I/O error" >&2; exit 1;; esac\nexec /usr/bin/find "$@"\n'
    (home / ".config/systemd/user").mkdir(parents=True)
    done, log = run(tmp_path, entry=entry, runtime_root=runtime_root, cfg=good_cfg(home, uid), extra_stubs={"find": failing})
    out = done.stdout
    assert "[item 5b INCOMPLETE]" in out and "COMPLETE]" not in out.replace("INCOMPLETE]", "")
    assert "[FINDING] a user-path search failed and its absence was not established (probe status 0)" in out
    assert "1 failed]" in out and "[rc=1] find" in out and "unit queries" not in out.split("INCOMPLETE]")[0]
    assert not [line for line in log.splitlines() if line.startswith("runuser") and ("list-unit-files" in line or " show " in line)]


def test_a_directory_that_stat_reports_missing_is_absent_and_item_5b_stays_complete(tmp_path):
    home, uid, entry, runtime_root = account(tmp_path)
    done, _ = run(tmp_path, entry=entry, runtime_root=runtime_root, cfg=good_cfg(home, uid))
    assert "[absent] " in done.stdout and " 0 failed]" in done.stdout and "[item 5b COMPLETE]" in done.stdout


@pytest.mark.parametrize("failing", ["list-unit-files", "show"])
def test_a_failed_unit_query_makes_item_5b_incomplete(tmp_path, failing):
    home, uid, entry, runtime_root = account(tmp_path)
    cfg = good_cfg(home, uid, **({"list_rc": 1} if failing == "list-unit-files" else {"show_rc": 1}))
    done, log = run(tmp_path, entry=entry, runtime_root=runtime_root, cfg=cfg)
    out = done.stdout
    assert "[item 5b INCOMPLETE]" in out and "COMPLETE]" not in out.replace("INCOMPLETE]", "")
    assert re.search(rf"\[rc=1\] asacct systemctl --user {failing}", out), out


def test_a_failed_find_followed_by_a_non_enoent_observation_failure_is_incomplete_without_unit_queries(tmp_path):
    home, uid, entry, runtime_root = account(tmp_path)
    failing = f'echo "find $*" >> @LOG@\ncase "$1" in {home}/.config/systemd/user) exit 1;; esac\nexec /usr/bin/find "$@"\n'
    (home / ".config").write_text("a file, not a directory")  # lstat raises ENOTDIR, which is not absence
    done, log = run(tmp_path, entry=entry, runtime_root=runtime_root, cfg=good_cfg(home, uid), extra_stubs={"find": failing})
    out = done.stdout
    assert "[item 5b INCOMPLETE]" in out and "COMPLETE]" not in out.replace("INCOMPLETE]", "")
    assert "(probe status 11)" in out and "1 failed]" in out
    assert not [line for line in log.splitlines() if line.startswith("runuser") and ("list-unit-files" in line or " show " in line)]


def test_absence_is_decided_by_errno_not_by_diagnostic_text(tmp_path):
    home, uid, entry, runtime_root = account(tmp_path)
    uutils = '[ "$1" = -c ] && exec /usr/bin/stat "$@"\necho "stat: cannot stat: No such file or directory (os error 2)" >&2; exit 1\n'  # diagnostics differ per coreutils
    done, _ = run(tmp_path, entry=entry, runtime_root=runtime_root, cfg=good_cfg(home, uid), extra_stubs={"stat": uutils})
    assert "[absent] " in done.stdout and "0 failed]" in done.stdout
