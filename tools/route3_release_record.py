"""Route 3 release-record tooling for the pre-installed Python 3.14 baseline.

The former S0.0 assumed ``python3.14`` was absent and proposed an *install* closure from an apt simulation. On the current production baseline the
interpreter is already installed as part of the Ubuntu 26.04 host, so there is nothing to simulate. This module replaces that procedure with
deterministic, read-only attestation and validation. It never installs, removes, holds, refreshes or writes anything on the host it inspects
(``build-archive`` and the reference commands write only below a directory the caller names and refuse to reuse one).

Concepts (runbook part P, "Release-record procedure"):

* the **baseline record**: the canonical text of the installed ``python3.14``/``python3.14-minimal``/``python3.14-venv`` dependency closure
  (name, version, architecture, source package and the archive sources that offer exactly that version) plus the interpreter digest;
* the **pinned set**: closure members built from source package ``python3.14`` - exact version, held later, ``dpkg --verify`` clean;
* the **base set**: every other closure member - attested exactly and re-checked, never held (holding libc6 would block security updates);
* the **payload reference**: for every closure member, the identity of the *signed-archive package* (the ``.deb`` whose SHA-256 the archive's signed index states), obtained off production: a digest of its
  package metadata (control fields, conffile list with packaged md5s, maintainer scripts and ``md5sums``) and a digest of its non-conffile payload (every file's content, mode and owner, every symlink target).
  ``dpkg --verify`` and ``apt-cache madison`` only compare the host with its own, locally installed metadata and with what an archive *offers*; they cannot exclude a same-version package that came from a removed
  or untrusted repository, or was crafted locally with matching metadata. The payload reference can: ``verify-host`` recomputes both digests from the installed files and refuses any difference;
* the **release record**: runbook block F, validated here - no ``UNSET``, well formed, bound to the baseline record by its SHA-256;
* the **release artifacts**: ``code.tar`` and ``MANIFEST.sha256`` reproduced from a reviewed, published commit, and the SA-2 tree digest.

Every command exits 0 (ok), 1 (NO-GO findings, each printed as ``NO-GO: ...``), 2 (usage) or 3 (the environment could not be read).
Standard library only; run as ``/usr/bin/python3.14 -I -S -B`` so no ambient module, environment or bytecode is involved.
"""

from __future__ import annotations

import argparse
import dataclasses
import grp
import hashlib
import io
import lzma
import os
import pwd
import re
import stat
import subprocess
import sys
import tarfile
import tempfile
import zlib
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path

ARCHIVE_PATHSPEC = ("adapters", "application", "tools", "infra/executor", "infra/tmpfiles.d", "infra/rp11-h1")
ROOT_PACKAGES = ("python3.14", "python3.14-minimal", "python3.14-venv")
PIN_SOURCE = "python3.14"
INTERPRETER = "/usr/bin/python3.14"
INTERPRETER_OWNER = "python3.14-minimal"
DPKG_STATUS_PSEUDO_SOURCE = "/var/lib/dpkg/status"
WHEEL_NAME = "jeepney-0.9.0-py3-none-any.whl"
WHEEL_SHA256 = "97e5714520c16fc0a45695e5365a2e11b81ea79bba796e26f9f1d178cb182683"
RECORD_HEADER = "route3-baseline-record 1"
UNSET = "UNSET"
REFERENCE_HEADER = "route3-payload-reference 1"
FIELD_KEYS = (
    "RELEASE_REV", "ARCHIVE_SHA256", "MANIFEST_SHA256", "APT_PACKAGES", "APT_BASE", "APT_ORIGIN", "PY_SHA256", "BASELINE_SHA256", "REFERENCE_SHA256", "SA2_TREE_SHA256", "WHEEL", "WHEEL_SHA256",
)
# the package metadata that dpkg copies from the package's control file into its status database (the closure itself is computed from these)
CONTROL_FIELDS = ("Package", "Source", "Version", "Architecture", "Multi-Arch", "Essential", "Pre-Depends", "Depends", "Provides", "Conflicts", "Breaks", "Replaces")
# the control-archive members dpkg keeps beside the status database as /var/lib/dpkg/info/<package>.<member> ("control" itself lives in the status file)
CONTROL_MEMBERS = ("conffiles", "config", "md5sums", "postinst", "postrm", "preinst", "prerm", "shlibs", "symbols", "templates", "triggers")
USRMERGE_TOP = ("bin", "sbin", "lib", "lib32", "lib64", "libx32")
MAX_DEB_BYTES = 512 << 20
MAX_UNPACKED_BYTES = 1 << 30
# identical to BAD in runbook block D (ROUTE3_STAGE_ENTRY); a test pins the two together
BAD_MEMBER_NAME = (
    r"[.]env.*|[.]git.*|[.]pgpass|__pycache__|id_[a-z0-9]+|.*[.](pem|key|pyc|pyo|p12|pfx)"
    r"|.*(credential|service_account|secret).*[.](json|ya?ml|toml|ini|cfg|conf|txt|b64|asc|gpg)|.*(credential|service_account|secret)[^.]*"
)
SAFE_PATH = re.compile(r"[A-Za-z0-9._+@-]+(/[A-Za-z0-9._+@-]+)*")
SAFE_ABSOLUTE = re.compile(r"/[A-Za-z0-9._+@-]+(/[A-Za-z0-9._+@-]+)*")
SHA256 = re.compile(r"[0-9a-f]{64}")
TOKEN = re.compile(r"[a-z0-9][a-z0-9.+-]*=[A-Za-z0-9.+~:-]+")
ORIGIN = re.compile(r"https?://[^ ,|\t]+ [A-Za-z0-9._-]+/[A-Za-z0-9._-]+")
MAX_ARCHIVE_BYTES = 128 << 20
MAX_MEMBER_BYTES = 8 << 20


class RecordError(Exception):
    """A NO-GO finding: the evidence is incomplete, drifted, ambiguous or not acceptable. The message is the finding."""


class EnvironmentFailure(Exception):
    """The inspected environment could not be read (exit status 3), as opposed to a finding about its content."""


# ---- hashing -------------------------------------------------------------------------------------------------------------------------

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


# ---- dpkg database -------------------------------------------------------------------------------------------------------------------

@dataclasses.dataclass(frozen=True)
class Package:
    """One installed package of the dpkg status database."""

    name: str
    version: str
    arch: str
    source: str
    depends: tuple[tuple[str, ...], ...]
    provides: tuple[str, ...]

    @property
    def token(self) -> str:
        return f"{self.name}={self.version}"


def _names(clause: str) -> tuple[str, ...]:
    out = []
    for alternative in clause.split("|"):
        name = re.sub(r"\s*[(\[<].*$", "", alternative.strip()).split(":")[0].strip()
        if name:
            out.append(name)
    return tuple(out)


def _clauses(value: str) -> tuple[tuple[str, ...], ...]:
    return tuple(c for c in (_names(part) for part in value.split(",")) if c)


def _paragraphs(text: str) -> list[dict[str, str]]:
    """The paragraphs of a dpkg status or control file as {field: value}; a continuation line is joined to its field with a newline."""
    out = []
    for paragraph in re.split(r"\n\s*\n", text.strip("\n")):
        fields: dict[str, str] = {}
        key = None
        for line in paragraph.splitlines():
            if line[:1] in (" ", "\t") and key:
                fields[key] += "\n" + line.strip()
            elif ":" in line:
                key, _, value = line.partition(":")
                fields[key] = value.strip()
        out.append(fields)
    return out


def parse_status(text: str) -> tuple[Package, ...]:
    """The installed packages of a dpkg status file. A package that is not fully installed is a finding, never silently skipped."""
    packages: list[Package] = []
    for fields in _paragraphs(text):
        if "Package" not in fields:
            continue
        name = fields["Package"]
        status = fields.get("Status", "").split()
        if len(status) != 3:
            raise RecordError(f"package {name} has a malformed Status field")
        wanted, flag, state = status
        if state in ("not-installed", "config-files"):
            continue
        if flag != "ok" or state != "installed" or wanted not in ("install", "hold"):
            raise RecordError(f"package {name} is not in a clean installed state ({fields['Status']!r})")
        source = re.sub(r"\s*\(.*$", "", fields.get("Source", "")).strip() or name
        provides = tuple(sorted(_names(fields.get("Provides", "").replace(",", "|"))))
        depends = _clauses(",".join(v for v in (fields.get("Pre-Depends", ""), fields.get("Depends", "")) if v))
        packages.append(Package(name=name, version=fields.get("Version", ""), arch=fields.get("Architecture", ""), source=source, depends=depends, provides=provides))
    names = [p.name for p in packages]
    duplicated = sorted({n for n in names if names.count(n) > 1})
    if duplicated:
        raise RecordError(f"package installed for more than one architecture (multiarch is not attestable): {', '.join(duplicated)}")
    return tuple(packages)


def dependency_closure(packages: Iterable[Package], roots: Sequence[str]) -> tuple[Package, ...]:
    """The transitive Depends/Pre-Depends closure of ``roots`` over the installed packages, sorted by name.

    Each clause is satisfied by the first alternative that is installed (by name, then through ``Provides``); the choice is deterministic and a clause that nothing
    installed satisfies is a finding. Recommends and Suggests are not followed.
    """
    by_name = {p.name: p for p in packages}
    providers: dict[str, list[str]] = {}
    for p in by_name.values():
        for virtual in p.provides:
            providers.setdefault(virtual, []).append(p.name)
    missing = [r for r in roots if r not in by_name]
    if missing:
        raise RecordError(f"root package is not installed: {', '.join(missing)}")
    seen: dict[str, Package] = {}
    queue = list(roots)
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        pkg = by_name[name]
        seen[name] = pkg
        for clause in pkg.depends:
            choice = next((a for a in clause if a in by_name), None) or next((sorted(providers[a])[0] for a in clause if a in providers), None)
            if choice is None:
                raise RecordError(f"{name} depends on {' | '.join(clause)}, which nothing installed satisfies")
            queue.append(choice)
    return tuple(seen[n] for n in sorted(seen))


# ---- host seam -----------------------------------------------------------------------------------------------------------------------

class Host:
    """Everything the attestation reads from the inspected system, behind one seam so tests can supply a synthetic one.

    Only fixed absolute programs run (``dpkg``, ``apt-cache``), with an empty environment and no shell. Nothing here writes. ``root`` is the directory the packaged paths are resolved
    below (``/`` on a real host; a private directory in tests); ``owner_names`` maps a numeric owner to the names a package archive records (``pwd``/``grp`` by default).
    """

    def __init__(self, admindir: Path = Path("/var/lib/dpkg"), bin_dir: Path = Path("/usr/bin"), interpreter: Path = Path(INTERPRETER),
                 os_release: Path = Path("/etc/os-release"), root: Path = Path("/"), owner_names: Callable[[int, int], tuple[str, str]] | None = None) -> None:
        self._admindir, self._bin, self._interpreter, self._os_release, self._root = admindir, bin_dir, interpreter, os_release, root
        self._owner_names = owner_names or self._system_owner_names

    @staticmethod
    def _system_owner_names(uid: int, gid: int) -> tuple[str, str]:
        try:
            user = pwd.getpwuid(uid).pw_name
        except KeyError:
            user = f"#{uid}"
        try:
            group = grp.getgrgid(gid).gr_name
        except KeyError:
            group = f"#{gid}"
        return user, group

    def _run(self, *argv: str) -> tuple[int, str]:
        try:
            done = subprocess.run(argv, capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"}, stdin=subprocess.DEVNULL, check=False, timeout=300)
        except (OSError, subprocess.SubprocessError) as error:
            raise EnvironmentFailure(f"cannot run {argv[0]}: {error}") from error
        return done.returncode, done.stdout

    def _read_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise EnvironmentFailure(f"cannot read {path}: {error}") from error

    def status_text(self) -> str:
        try:
            return (self._admindir / "status").read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise EnvironmentFailure(f"cannot read the dpkg status database: {error}") from error

    def _info_path(self, package: str, arch: str, extension: str) -> Path | None:
        for name in (f"{package}.{extension}", f"{package}:{arch}.{extension}"):
            path = self._admindir / "info" / name
            if path.is_file():
                return path
        return None

    def file_list(self, package: str, arch: str) -> frozenset[str] | None:
        """The paths dpkg records for a package, or None when it has no list file at all."""
        path = self._info_path(package, arch, "list")
        if path is None:
            return None
        return frozenset(self._read_text(path).splitlines())

    def owned_paths(self, package: str, arch: str) -> frozenset[str]:
        return self.file_list(package, arch) or frozenset()

    def control_member(self, package: str, arch: str, member: str) -> bytes | None:
        """A control-archive member dpkg keeps for the package (maintainer script, md5sums, conffiles ...), or None when there is none."""
        path = self._info_path(package, arch, member)
        if path is None:
            return None
        try:
            return path.read_bytes()
        except OSError as error:
            raise EnvironmentFailure(f"cannot read {path}: {error}") from error

    def path_filters(self) -> list[str]:
        """The ``path-exclude``/``path-include`` options of the dpkg configuration: they legitimately change what is unpacked, so a payload comparison cannot be exact under them."""
        found = []
        config = self._root / "etc/dpkg"
        files = [config / "dpkg.cfg"]
        directory = config / "dpkg.cfg.d"
        if directory.is_dir():
            files += sorted(p for p in directory.iterdir() if p.is_file())
        for path in files:
            if not path.is_file():
                continue
            for line in self._read_text(path).splitlines():
                option = line.split("#", 1)[0].strip().lstrip("-")
                if option.startswith(("path-exclude", "path-include")):
                    found.append(f"{path.name}: {option}")
        return found

    def lstat(self, path: str) -> os.stat_result | None:
        try:
            return os.lstat(self._root / path.lstrip("/"))
        except FileNotFoundError:
            return None
        except OSError as error:
            raise EnvironmentFailure(f"cannot stat {path}: {error}") from error

    def read_link(self, path: str) -> str:
        try:
            return os.readlink(self._root / path.lstrip("/"))
        except OSError as error:
            raise EnvironmentFailure(f"cannot read the link {path}: {error}") from error

    def file_sha256(self, path: str) -> str:
        """SHA-256 of a regular file, opened without following a link."""
        digest = hashlib.sha256()
        try:
            descriptor = os.open(self._root / path.lstrip("/"), os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
            with os.fdopen(descriptor, "rb") as handle:
                for chunk in iter(lambda: handle.read(1 << 20), b""):
                    digest.update(chunk)
        except OSError as error:
            raise EnvironmentFailure(f"cannot read {path}: {error}") from error
        return digest.hexdigest()

    def owner_names(self, info: os.stat_result) -> tuple[str, str]:
        return self._owner_names(info.st_uid, info.st_gid)

    def madison(self, package: str) -> str:
        status, out = self._run(str(self._bin / "apt-cache"), "madison", package)
        if status != 0:
            raise EnvironmentFailure(f"apt-cache madison {package} failed (status {status})")
        return out

    def dpkg_verify(self, packages: Sequence[str]) -> tuple[int, str]:
        return self._run(str(self._bin / "dpkg"), "--admindir", str(self._admindir), "--verify", *packages)

    def interpreter(self) -> tuple[str, str, str]:
        """(configured path, real path, SHA-256 of the real file). The real path is reported relative to ``root`` so a private test root names the same packaged path as a real host."""
        try:
            base = Path(os.path.realpath(self._root))
            real = Path(os.path.realpath(base / str(self._interpreter).lstrip("/")))
            shown = real.as_posix() if base == Path("/") else "/" + real.relative_to(base).as_posix()
            return str(self._interpreter), shown, sha256_file(real)
        except (OSError, ValueError) as error:
            raise EnvironmentFailure(f"cannot read the interpreter: {error}") from error

    def os_identity(self) -> tuple[str, str, str]:
        try:
            lines = self._os_release.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as error:
            raise EnvironmentFailure(f"cannot read os-release: {error}") from error
        values = {k: v.strip().strip('"') for k, _, v in (line.partition("=") for line in lines)}
        return values.get("ID", ""), values.get("VERSION_ID", ""), values.get("VERSION_CODENAME", "")


def archive_origins(madison: str, name: str, version: str) -> tuple[str, ...]:
    """The archive sources that offer exactly ``name=version`` (``apt-cache madison`` columns: name | version | url suite/component arch Packages).

    dpkg's own status file appears there as a pseudo-source for an installed version; it is the installed-state marker, not an archive, and is skipped.
    Any other source shape is a finding: provenance cannot be attested from text this tool does not understand.
    """
    found: set[str] = set()
    for line in madison.splitlines():
        columns = [c.strip() for c in line.split("|")]
        if len(columns) != 3 or columns[0] != name or columns[1] != version:
            continue
        source = columns[2]
        if source == DPKG_STATUS_PSEUDO_SOURCE or source.startswith(DPKG_STATUS_PSEUDO_SOURCE + " "):
            continue
        match = re.fullmatch(r"(https?://\S+ [A-Za-z0-9._-]+/[A-Za-z0-9._-]+) \S+ Packages", source)
        if not match:
            raise RecordError(f"{name}={version} is offered by a source of unknown shape: {source!r}")
        found.add(match[1])
    return tuple(sorted(found))


# ---- the baseline record -------------------------------------------------------------------------------------------------------------

@dataclasses.dataclass(frozen=True)
class Member:
    cls: str          # "pin" | "base"
    name: str
    version: str
    arch: str
    source: str
    origins: tuple[str, ...]

    @property
    def token(self) -> str:
        return f"{self.name}={self.version}"


@dataclasses.dataclass(frozen=True)
class Baseline:
    os_id: str
    os_version: str
    codename: str
    interpreter_path: str
    interpreter_real: str
    interpreter_sha256: str
    members: tuple[Member, ...]

    def of(self, cls: str) -> tuple[Member, ...]:
        return tuple(m for m in self.members if m.cls == cls)

    def tokens(self, cls: str) -> str:
        return " ".join(sorted(m.token for m in self.of(cls)))

    def origin_list(self) -> str:
        return ", ".join(sorted({o for m in self.members for o in m.origins}))

    def render(self) -> str:
        rows = [RECORD_HEADER, f"os\t{self.os_id}\t{self.os_version}\t{self.codename}",
                f"interpreter\t{self.interpreter_path}\t{self.interpreter_real}\t{self.interpreter_sha256}"]
        rows += [f"root\t{r}" for r in ROOT_PACKAGES]
        rows += [f"pkg\t{m.cls}\t{m.name}\t{m.version}\t{m.arch}\t{m.source}\t{'|'.join(m.origins)}" for m in sorted(self.members, key=lambda m: m.name)]
        rows.append(f"end\t{len(self.members)}")
        return "\n".join(rows) + "\n"

    @classmethod
    def parse(cls, text: str) -> "Baseline":
        lines = text.split("\n")
        if lines[-1] != "" or lines[0] != RECORD_HEADER:
            raise RecordError("baseline record: wrong header or no final newline")
        lines = lines[:-1]
        if len(lines) < 6 or [l.split("\t") for l in lines[3:3 + len(ROOT_PACKAGES)]] != [["root", r] for r in ROOT_PACKAGES]:
            raise RecordError("baseline record: roots are not exactly the three Python packages")
        os_row, interp, pkgs, end = lines[1].split("\t"), lines[2].split("\t"), [l.split("\t") for l in lines[3 + len(ROOT_PACKAGES):-1]], lines[-1].split("\t")
        if len(os_row) != 4 or os_row[0] != "os" or len(interp) != 4 or interp[0] != "interpreter" or end[0] != "end" or len(end) != 2:
            raise RecordError("baseline record: malformed os, interpreter or end row")
        members = []
        for row in pkgs:
            if len(row) != 7 or row[0] != "pkg" or row[1] not in ("pin", "base"):
                raise RecordError(f"baseline record: malformed package row {row!r}")
            member = Member(row[1], row[2], row[3], row[4], row[5], tuple(o for o in row[6].split("|") if o))
            if not (re.fullmatch(r"[a-z0-9][a-z0-9.+-]*", member.name) and re.fullmatch(r"[A-Za-z0-9.+~:-]+", member.version) and re.fullmatch(r"[a-z0-9][a-z0-9-]*", member.arch)
                    and re.fullmatch(r"[a-z0-9][a-z0-9.+-]*", member.source) and member.origins and all(ORIGIN.fullmatch(o) for o in member.origins)):
                raise RecordError(f"baseline record: package row has a malformed field: {row!r}")
            members.append(member)
        if end[1] != str(len(members)):
            raise RecordError("baseline record: the end count does not match the package rows")
        if not (all(re.fullmatch(r"[A-Za-z0-9._-]*", v) for v in os_row[1:]) and SAFE_ABSOLUTE.fullmatch(interp[1]) and SAFE_ABSOLUTE.fullmatch(interp[2]) and SHA256.fullmatch(interp[3])):
            raise RecordError("baseline record: malformed os or interpreter field")
        baseline = cls(os_row[1], os_row[2], os_row[3], interp[1], interp[2], interp[3], tuple(members))
        if baseline.render() != text:
            raise RecordError("baseline record is not in canonical form (order, spelling or whitespace differ)")
        return baseline


def attest(host: Host, allowed_origins: Sequence[str] = ()) -> Baseline:
    """Read the installed closure of the three Python packages and prove each member's provenance. Read-only; deterministic for an unchanged host."""
    packages = parse_status(host.status_text())
    closure = dependency_closure(packages, ROOT_PACKAGES)
    members = []
    for pkg in closure:
        if not pkg.version or not pkg.arch:
            raise RecordError(f"package {pkg.name} has no version or architecture")
        origins = archive_origins(host.madison(pkg.name), pkg.name, pkg.version)
        if not origins:
            raise RecordError(f"{pkg.token} is offered by no configured archive source (locally installed, or its source is gone): provenance cannot be attested")
        if allowed_origins:
            stray = [o for o in origins if o not in allowed_origins]
            if stray:
                raise RecordError(f"{pkg.token} is offered by an origin that is not allowed: {', '.join(stray)}")
        members.append(Member("pin" if pkg.source == PIN_SOURCE else "base", pkg.name, pkg.version, pkg.arch, pkg.source, origins))
    path, real, digest = host.interpreter()
    owner = next(p for p in closure if p.name == INTERPRETER_OWNER)
    if canon_path(real) not in {canon_path(p) for p in host.owned_paths(owner.name, owner.arch)}:    # the RESOLVED file must be packaged: a packaged name that links elsewhere is not the packaged interpreter
        raise RecordError(f"{path} (real file {real}) is not a file of {INTERPRETER_OWNER}: the interpreter is not the packaged one")
    if not set(ROOT_PACKAGES) <= {m.name for m in members if m.cls == "pin"}:
        raise RecordError("the three Python packages are not all built from source package python3.14")
    os_id, os_version, codename = host.os_identity()
    return Baseline(os_id, os_version, codename, path, real, digest, tuple(members))


def verify_files(host: Host, baseline: Baseline) -> list[str]:
    """``dpkg --verify``: any change to a pinned package's file is a finding; for a base package only non-conffile changes are (a local conffile edit is host policy)."""
    findings = []
    for cls in ("pin", "base"):
        names = [m.name for m in baseline.of(cls)]
        status, out = host.dpkg_verify(names)
        lines = [l for l in out.splitlines() if l.strip()]
        if status not in (0, 1) or (status == 1 and not lines):    # dpkg --verify exits 1 when it reports a discrepancy, so 1 without a report is a failure too
            findings.append(f"dpkg --verify failed for the {cls} set (status {status})")
        if cls == "base":
            lines = [l for l in lines if not re.match(r"^\S{9}\s+c\s", l)]
        findings += [f"dpkg --verify reports a changed packaged file ({cls} set): {l}" for l in lines]
    return findings


def compare(record: Baseline, live: Baseline) -> list[str]:
    """Every difference between the reviewed record and the host, as findings. Empty means the host still is the reviewed baseline."""
    findings = []
    for label, a, b in (("operating system", (record.os_id, record.os_version, record.codename), (live.os_id, live.os_version, live.codename)),
                        ("interpreter path", record.interpreter_path, live.interpreter_path), ("interpreter file", record.interpreter_real, live.interpreter_real),
                        ("interpreter SHA-256", record.interpreter_sha256, live.interpreter_sha256)):
        if a != b:
            findings.append(f"{label} drifted: reviewed {a}, host {b}")
    old, new = {m.name: m for m in record.members}, {m.name: m for m in live.members}
    findings += [f"unexpected closure: {n} is now part of the dependency closure" for n in sorted(new.keys() - old.keys())]
    findings += [f"unexpected closure: {n} is no longer part of the dependency closure" for n in sorted(old.keys() - new.keys())]
    for name in sorted(old.keys() & new.keys()):
        a, b = old[name], new[name]
        for label, x, y in (("version", a.version, b.version), ("architecture", a.arch, b.arch), ("source package", a.source, b.source), ("class", a.cls, b.cls)):
            if x != y:
                findings.append(f"{'base' if a.cls == 'base' else 'pinned'} drift: {name} {label} reviewed {x}, host {y}")
        # the archive sources of each member are compared as exact sets: a member offered by a source that was not reviewed, and a member no longer offered by one that was, are both drift
        if set(a.origins) != set(b.origins) or not b.origins:
            findings.append(f"provenance drift: {b.token} is offered by [{', '.join(sorted(b.origins)) or 'no archive source'}], the reviewed record has [{', '.join(sorted(a.origins))}]")
    return findings


# ---- the signed-archive payload reference ----------------------------------------------------------------------------------------------
#
# What the installed system claims about a package (status database, ``.list``, ``md5sums``, maintainer scripts) is local metadata: a package installed from a repository that has since been removed, or built
# locally with matching metadata, passes ``dpkg --verify`` and appears in ``apt-cache madison`` whenever an allowed archive offers the same name and version. The reference below is computed from the package
# *the archive's signed index describes* and is compared with the installed state, so the installed state has to be byte-for-byte what that package unpacks to (conffiles aside).

def _plain(text: str, what: str) -> str:
    if any(ord(c) < 32 or ord(c) == 127 for c in text):
        raise RecordError(f"{what} holds a control character: {text!r}")
    return text


def canon_path(path: str) -> str:
    """A packaged path with the merged-/usr aliases resolved (``/lib64/x`` is ``/usr/lib64/x``): archive and file list name the same file either way."""
    parts = path.split("/")
    return "/usr" + path if len(parts) > 1 and parts[1] in USRMERGE_TOP else path


def _row_file(path: str, mode: int, owner: tuple[str, str], sha256: str) -> str:
    return f"f\t{path}\t{mode & 0o7777:04o}\t{owner[0]}\t{owner[1]}\t{sha256}"


def _row_link(path: str, target: str) -> str:
    return f"l\t{path}\t{_plain(target, 'a symlink target')}"


def _digest_rows(rows: Iterable[str]) -> str:
    return sha256_bytes(("\n".join(sorted(rows, key=lambda r: r.encode())) + "\n").encode())


def _normal(value: str) -> str:
    return " ".join(value.split())


def _meta_rows(fields: dict[str, str], conffiles: dict[str, str], scripts: dict[str, str]) -> list[str]:
    rows = [f"f\t{key}\t{_normal(fields[key])}" for key in CONTROL_FIELDS if _normal(fields.get(key, ""))]
    rows += [f"c\t{canon_path(path)}\t{md5}" for path, md5 in conffiles.items()]
    rows += [f"s\t{name}\t{sha}" for name, sha in scripts.items()]
    return sorted(rows, key=lambda r: r.encode())


@dataclasses.dataclass(frozen=True)
class DebEntry:
    path: str
    kind: str           # "file" | "dir" | "symlink" | "hardlink"
    mode: int
    owner: tuple[str, str]
    sha256: str
    md5: str
    link: str


@dataclasses.dataclass(frozen=True)
class Deb:
    fields: dict[str, str]
    control: dict[str, bytes]
    entries: tuple[DebEntry, ...]


def _unpack(name: str, body: bytes) -> bytes:
    suffix = name.rpartition(".")[2]
    if suffix not in ("gz", "xz", "zst", "tar"):
        raise RecordError(f"the package member {name} has an unsupported compression")
    try:
        if suffix == "gz":
            out = zlib.decompressobj(31).decompress(body, MAX_UNPACKED_BYTES + 1)
        elif suffix == "xz":
            out = lzma.LZMADecompressor().decompress(body, max_length=MAX_UNPACKED_BYTES + 1)
        elif suffix == "zst":
            from compression import zstd    # standard library since Python 3.14
            out = zstd.ZstdDecompressor().decompress(body, MAX_UNPACKED_BYTES + 1)
        else:
            out = body
    except Exception as error:     # a corrupt or hostile stream (zlib, lzma or zstd error, a missing module) is a finding, never a crash
        raise RecordError(f"the package member {name} cannot be decompressed: {error}") from error
    if len(out) > MAX_UNPACKED_BYTES:
        raise RecordError(f"the package member {name} is too large when unpacked")
    return out


def _ar_members(data: bytes) -> list[tuple[str, bytes]]:
    if data[:8] != b"!<arch>\n" or len(data) > MAX_DEB_BYTES:
        raise RecordError("the package is not an ar archive (or is too large)")
    members, position = [], 8
    while position < len(data):
        header = data[position:position + 60]
        if len(header) < 60 or header[58:60] != b"`\n":
            raise RecordError("the package has a malformed ar header")
        try:
            name, size = header[:16].decode("ascii").strip().rstrip("/"), int(header[48:58].decode("ascii").strip())
        except (UnicodeError, ValueError) as error:
            raise RecordError("the package has a malformed ar header") from error
        body = data[position + 60:position + 60 + size]
        if len(body) != size:
            raise RecordError("the package ar archive is truncated")
        members.append((name, body))
        position += 60 + size + (size & 1)
    return members


def _tar_path(name: str) -> str:
    path = "/" + name.removeprefix("./").strip("/") if name.removeprefix("./").strip("/") else "/"
    if ".." in path.split("/") or "//" in path:
        raise RecordError(f"the package holds an unsafe path: {name!r}")
    return _plain(path, "a packaged path")


def parse_deb(data: bytes) -> Deb:
    """The control fields, control members and data entries of a ``.deb`` (ar archive of ``debian-binary``, ``control.tar.*`` and ``data.tar.*``), read in memory and never extracted."""
    members = _ar_members(data)
    names = [n for n, _ in members]
    controls = [(n, b) for n, b in members if re.fullmatch(r"control\.tar(\.gz|\.xz|\.zst)?", n)]
    datas = [(n, b) for n, b in members if re.fullmatch(r"data\.tar(\.gz|\.xz|\.zst)?", n)]
    if names[:1] != ["debian-binary"] or dict(members)["debian-binary"] != b"2.0\n" or len(controls) != 1 or len(datas) != 1 or len(names) != 3:
        raise RecordError("the package is not a version 2.0 .deb of exactly debian-binary, one control archive and one data archive")
    control: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(_unpack(*controls[0])), mode="r:") as tar:
        for member in tar:
            name = member.name.removeprefix("./").strip("/")
            if not name or member.isdir():
                continue
            if not member.isreg() or "/" in name or name in control:
                raise RecordError(f"the control archive holds an unexpected member: {member.name!r}")
            control[name] = tar.extractfile(member).read()
    if "control" not in control:
        raise RecordError("the package has no control file")
    unknown = sorted(set(control) - {"control", *CONTROL_MEMBERS})
    if unknown:
        raise RecordError(f"the control archive holds members this tool does not bind: {', '.join(unknown)}")
    try:
        fields = _paragraphs(control["control"].decode("utf-8"))[0]
    except (UnicodeError, IndexError) as error:
        raise RecordError("the package control file is unreadable") from error
    entries: list[DebEntry] = []
    seen: set[str] = set()
    with tarfile.open(fileobj=io.BytesIO(_unpack(*datas[0])), mode="r:") as tar:
        for member in tar:
            path = _tar_path(member.name)
            if canon_path(path) in seen and not member.isdir():
                raise RecordError(f"the package holds the path twice: {path}")
            owner = (member.uname or f"#{member.uid}", member.gname or f"#{member.gid}")
            if member.isdir():
                entries.append(DebEntry(path, "dir", member.mode, owner, "", "", ""))
                continue
            seen.add(canon_path(path))
            if member.isreg():
                content = tar.extractfile(member).read()
                entries.append(DebEntry(path, "file", member.mode, owner, sha256_bytes(content), hashlib.md5(content, usedforsecurity=False).hexdigest(), ""))
            elif member.issym():
                entries.append(DebEntry(path, "symlink", member.mode, owner, "", "", _plain(member.linkname, "a symlink target")))
            elif member.islnk():
                entries.append(DebEntry(path, "hardlink", member.mode, owner, "", "", _tar_path(member.linkname)))
            else:
                raise RecordError(f"the package holds a special file (device, fifo or other): {path}")
    return Deb(fields, control, tuple(entries))


def deb_rows(deb: Deb) -> tuple[list[str], list[str]]:
    """(metadata rows, payload rows) of a package as its own archive unpacks it, conffiles excluded from the payload."""
    listed = [canon_path(_tar_path(line)) for line in deb.control.get("conffiles", b"").decode("utf-8", "replace").splitlines() if line.strip()]
    files = {canon_path(e.path): e for e in deb.entries if e.kind == "file"}
    conffiles: dict[str, str] = {}
    for path in listed:
        if path not in files:
            raise RecordError(f"the package lists the conffile {path}, which its data archive does not hold")
        conffiles[path] = files[path].md5
    rows = []
    for entry in deb.entries:
        path = canon_path(entry.path)
        if entry.kind == "dir" or path in conffiles:
            continue
        if entry.kind == "file":
            rows.append(_row_file(path, entry.mode, entry.owner, entry.sha256))
        elif entry.kind == "symlink":
            rows.append(_row_link(path, entry.link))
        else:
            target = files.get(canon_path(entry.link))
            if target is None:
                raise RecordError(f"the hard link {entry.path} points at {entry.link}, which is not a regular file of the package")
            rows.append(_row_file(path, target.mode, target.owner, target.sha256))
    scripts = {name: sha256_bytes(body) for name, body in sorted(deb.control.items()) if name != "control"}
    return _meta_rows(deb.fields, conffiles, scripts), rows


def _identity(rows: tuple[list[str], list[str]]) -> tuple[str, str, int]:
    return _digest_rows(rows[0]), _digest_rows(rows[1]), len(rows[1])


def deb_identity(deb: Deb) -> tuple[str, str, int]:
    """(metadata digest, payload digest, payload file count) of the signed-archive package."""
    return _identity(deb_rows(deb))


def _status_conffiles(value: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in value.splitlines():
        parts = line.split()
        if not parts:
            continue
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-f]{32}", parts[1]):
            raise RecordError(f"the status database holds a conffile entry with an unusual shape: {line!r}")
        out[canon_path(parts[0])] = parts[1]
    return out


def installed_rows(host: Host, package: Package, fields: dict[str, str]) -> tuple[list[str], list[str]]:
    """(metadata rows, payload rows) of an installed package, recomputed from the status database, the kept control members and the files themselves."""
    conffiles = _status_conffiles(fields.get("Conffiles", ""))
    scripts = {}
    for member in CONTROL_MEMBERS:
        body = host.control_member(package.name, package.arch, member)
        if body is not None:
            scripts[member] = sha256_bytes(body)
    listing = host.file_list(package.name, package.arch)
    if listing is None:
        raise RecordError(f"{package.token} has no dpkg file list")
    rows = []
    for raw in sorted(listing):
        if raw in ("", "/."):
            continue
        path = canon_path(_tar_path(raw))
        if path in conffiles:
            continue
        info = host.lstat(path)
        if info is None:
            rows.append(f"m\t{path}")
        elif stat.S_ISDIR(info.st_mode):
            continue
        elif stat.S_ISLNK(info.st_mode):
            rows.append(_row_link(path, host.read_link(path)))
        elif stat.S_ISREG(info.st_mode):
            rows.append(_row_file(path, stat.S_IMODE(info.st_mode), host.owner_names(info), host.file_sha256(path)))
        else:
            raise RecordError(f"{path} of {package.token} is a special file (device, fifo or socket)")
    return _meta_rows(fields, conffiles, scripts), rows


def installed_identity(host: Host, package: Package, fields: dict[str, str]) -> tuple[str, str, int]:
    """(metadata digest, payload digest, payload file count) of the installed package."""
    return _identity(installed_rows(host, package, fields))


@dataclasses.dataclass(frozen=True)
class RefMember:
    name: str
    version: str
    arch: str
    deb_sha256: str     # the SHA-256 the archive's SIGNED index states for exactly this package file
    meta_sha256: str
    payload_sha256: str
    files: int


@dataclasses.dataclass(frozen=True)
class Reference:
    baseline_sha256: str
    members: tuple[RefMember, ...]

    def render(self) -> str:
        rows = [REFERENCE_HEADER, f"baseline\t{self.baseline_sha256}"]
        rows += [f"pkg\t{m.name}\t{m.version}\t{m.arch}\t{m.deb_sha256}\t{m.meta_sha256}\t{m.payload_sha256}\t{m.files}" for m in sorted(self.members, key=lambda m: m.name)]
        rows.append(f"end\t{len(self.members)}")
        return "\n".join(rows) + "\n"

    @classmethod
    def parse(cls, text: str) -> "Reference":
        lines = text.split("\n")
        if lines[-1] != "" or lines[0] != REFERENCE_HEADER or len(lines) < 4:
            raise RecordError("payload reference: wrong header or no final newline")
        lines = lines[:-1]
        base, end = lines[1].split("\t"), lines[-1].split("\t")
        if len(base) != 2 or base[0] != "baseline" or not SHA256.fullmatch(base[1]) or len(end) != 2 or end[0] != "end":
            raise RecordError("payload reference: malformed baseline or end row")
        members = []
        for line in lines[2:-1]:
            row = line.split("\t")
            if len(row) != 8 or row[0] != "pkg" or not (re.fullmatch(r"[a-z0-9][a-z0-9.+-]*", row[1]) and re.fullmatch(r"[A-Za-z0-9.+~:-]+", row[2]) and re.fullmatch(r"[a-z0-9][a-z0-9-]*", row[3])
                                                         and all(SHA256.fullmatch(v) for v in row[4:7]) and re.fullmatch(r"[0-9]+", row[7])):
                raise RecordError(f"payload reference: malformed package row {line!r}")
            members.append(RefMember(row[1], row[2], row[3], row[4], row[5], row[6], int(row[7])))
        if end[1] != str(len(members)):
            raise RecordError("payload reference: the end count does not match the package rows")
        reference = cls(base[1], tuple(members))
        if reference.render() != text:
            raise RecordError("payload reference is not in canonical form (order, spelling or whitespace differ)")
        return reference


def reference_findings(reference: Reference, record: Baseline, record_text: str) -> list[str]:
    """The reference against the baseline record it was derived for: same record digest, same members at the same versions and architectures."""
    findings = []
    if reference.baseline_sha256 != sha256_bytes(record_text.encode()):
        findings.append("the payload reference was derived for another baseline record (its baseline digest differs)")
    ref = {m.name: m for m in reference.members}
    want = {m.name: m for m in record.members}
    findings += [f"the payload reference has no entry for {n}" for n in sorted(want.keys() - ref.keys())]
    findings += [f"the payload reference names {n}, which the baseline record does not" for n in sorted(ref.keys() - want.keys())]
    for name in sorted(want.keys() & ref.keys()):
        if (want[name].version, want[name].arch) != (ref[name].version, ref[name].arch):
            findings.append(f"the payload reference describes {name} {ref[name].version}/{ref[name].arch}, the baseline record has {want[name].version}/{want[name].arch}")
    return findings


def payload_findings(host: Host, live: Baseline, reference: Reference) -> list[str]:
    """Every difference between the installed closure and the signed-archive reference. Empty means each member's installed non-conffile payload and package metadata equal the archive package's.

    A local conffile edit is host policy and is not a difference; every other packaged file (executables and libraries included), every symlink, the maintainer scripts, ``md5sums`` and the
    control fields the closure is computed from are compared exactly.
    """
    filters = host.path_filters()
    if filters:
        return [f"dpkg path filters are configured ({'; '.join(filters)}): the installed payload may legitimately lack packaged files, so it cannot be compared with the archive package exactly"]
    findings = []
    packages = {p.name: p for p in parse_status(host.status_text())}
    fields = {f["Package"]: f for f in _paragraphs(host.status_text()) if "Package" in f}
    ref = {m.name: m for m in reference.members}
    for member in live.members:
        entry = ref.get(member.name)
        if entry is None:
            findings.append(f"{member.token} has no entry in the payload reference")
            continue
        if (entry.version, entry.arch) != (member.version, member.arch):
            findings.append(f"{member.name} is installed as {member.version}/{member.arch}, the payload reference describes {entry.version}/{entry.arch}")
            continue
        try:
            meta, payload, count = installed_identity(host, packages[member.name], fields[member.name])
        except RecordError as error:
            findings.append(f"{member.token}: {error}")
            continue
        if meta != entry.meta_sha256:
            findings.append(f"payload drift: the package metadata of {member.token} (control fields, conffile list, maintainer scripts or md5sums) is not that of the signed-archive package")
        if payload != entry.payload_sha256 or count != entry.files:
            findings.append(f"payload drift: the installed files of {member.token} are not those of the signed-archive package ({count} installed, {entry.files} in the package; digest {payload[:12]} != {entry.payload_sha256[:12]})")
    findings += [f"the payload reference names {n}, which is not part of the installed closure" for n in sorted(ref.keys() - {m.name for m in live.members})]
    return findings


class Archive:
    """Where the reference gets the signed-archive package from: the SHA-256 and origins the signed index states, and the package file itself. Production never uses it."""

    def __init__(self, run: Callable[[Sequence[str], Path], tuple[int, str]] | None = None) -> None:
        self._run = run or self._default

    @staticmethod
    def _default(argv: Sequence[str], cwd: Path) -> tuple[int, str]:
        done = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"}, stdin=subprocess.DEVNULL, check=False, timeout=900)
        return done.returncode, done.stdout

    def index(self, name: str, version: str, arch: str, cwd: Path) -> tuple[str, tuple[str, ...]]:
        status, shown = self._run(["/usr/bin/apt-cache", "show", f"{name}={version}"], cwd)
        stanzas = [f for f in _paragraphs(shown) if f.get("Package") == name and f.get("Version") == version and f.get("Architecture") == arch]
        stated = {f.get("SHA256", "") for f in stanzas}
        if status != 0 or not stanzas or len(stated) != 1 or not SHA256.fullmatch(next(iter(stated))):
            raise RecordError(f"the archive index does not state exactly one SHA-256 for {name}={version} ({arch})")
        status, madison = self._run(["/usr/bin/apt-cache", "madison", name], cwd)
        if status != 0:
            raise RecordError(f"apt-cache madison {name} failed")
        return next(iter(stated)), archive_origins(madison, name, version)

    def fetch(self, name: str, version: str, directory: Path) -> Path:
        status, _ = self._run(["/usr/bin/apt-get", "download", f"{name}={version}"], directory)
        debs = sorted(directory.glob(f"{name}_*.deb"))
        if status != 0 or len(debs) != 1:
            raise RecordError(f"apt-get download did not produce exactly one package file for {name}={version}")
        return debs[0]


def build_reference(record: Baseline, record_text: str, workdir: Path, archive: Archive | None = None) -> Reference:
    """Derive the payload reference of a baseline record from the signed archive. Off production, unprivileged, into an empty directory.

    For every member: the SHA-256 the archive's signed index states for exactly that version is read first; the downloaded package must equal it before it is opened; the archive source
    must be one the record reviewed; and the package's own metadata and payload digests are taken from the package file, never from any installed system.
    """
    archive = archive or Archive()
    if workdir.exists() and any(workdir.iterdir()):
        raise RecordError(f"{workdir} is not empty")
    workdir.mkdir(parents=True, exist_ok=True)
    members = []
    for member in sorted(record.members, key=lambda m: m.name):
        directory = workdir / member.name
        directory.mkdir()
        stated, origins = archive.index(member.name, member.version, member.arch, directory)
        if not set(origins) & set(member.origins):
            raise RecordError(f"{member.token} is offered here by [{', '.join(origins) or 'no archive source'}], none of which the baseline record reviewed")
        deb = archive.fetch(member.name, member.version, directory)
        data = deb.read_bytes()
        if sha256_bytes(data) != stated:
            raise RecordError(f"the downloaded {member.token} differs from the SHA-256 of the archive's signed index")
        parsed = parse_deb(data)
        for key, want in (("Package", member.name), ("Version", member.version), ("Architecture", member.arch)):
            if parsed.fields.get(key) != want:
                raise RecordError(f"the package file for {member.token} states {key} {parsed.fields.get(key)!r}, not {want!r}")
        meta, payload, count = deb_identity(parsed)
        members.append(RefMember(member.name, member.version, member.arch, stated, meta, payload, count))
    return Reference(sha256_bytes(record_text.encode()), tuple(members))


# ---- the release record (runbook block F) --------------------------------------------------------------------------------------------

def read_fields(runbook_text: str) -> dict[str, str]:
    """The assignments of the runbook's block F, strictly: one block, known keys only, each exactly once, plain or double-quoted values."""
    blocks = [b for b in re.findall(r"```bash\n(.*?)\n```", runbook_text, re.S) if b.startswith("ROUTE3_RELEASE_REV=")]
    if len(blocks) != 1:
        raise RecordError(f"expected exactly one release-field block, found {len(blocks)}")
    fields: dict[str, str] = {}
    for line in blocks[0].splitlines():
        match = re.fullmatch(r'ROUTE3_([A-Z0-9_]+)=(?:"([^"\n$`\\]*)"|([^\s"\'$`\\]*))', line)
        if not match:
            raise RecordError(f"release-field line is not a plain assignment: {line!r}")
        key = match[1]
        if key not in FIELD_KEYS or key in fields:
            raise RecordError(f"release field {key} is unknown or repeated")
        fields[key] = match[2] if match[2] is not None else match[3]
    return fields


def validate_fields(fields: dict[str, str], record_text: str | None = None, reference_text: str | None = None) -> list[str]:
    """Every NO-GO finding of a release record; an empty list means the record is complete, well formed and (with ``record_text``) bound to the attested baseline."""
    findings = [f"ROUTE3_{k} is missing" for k in FIELD_KEYS if k not in fields]
    if findings:
        return findings
    for key, value in fields.items():
        if UNSET in value or not value.strip():
            findings.append(f"ROUTE3_{key} is UNSET or empty (supplier: Peter)")
    if findings:
        return findings
    if not re.fullmatch(r"[0-9a-f]{40}", fields["RELEASE_REV"]):
        findings.append("ROUTE3_RELEASE_REV is not a 40-hex commit id")
    for key in ("ARCHIVE_SHA256", "MANIFEST_SHA256", "PY_SHA256", "BASELINE_SHA256", "REFERENCE_SHA256", "SA2_TREE_SHA256", "WHEEL_SHA256"):
        if not SHA256.fullmatch(fields[key]):
            findings.append(f"ROUTE3_{key} is not a SHA-256")
    pinned = fields["APT_PACKAGES"].split(" ")
    base = fields["APT_BASE"].split(" ")
    for label, tokens in (("APT_PACKAGES", pinned), ("APT_BASE", base)):
        if not all(TOKEN.fullmatch(t) for t in tokens):
            findings.append(f"ROUTE3_{label} must be exact name=version tokens separated by single spaces")
        elif len({t.split("=")[0] for t in tokens}) != len(tokens):
            findings.append(f"ROUTE3_{label} names a package twice")
    names = {t.split("=")[0] for t in pinned}
    if not set(ROOT_PACKAGES) <= names:
        findings.append("ROUTE3_APT_PACKAGES must pin python3.14, python3.14-minimal and python3.14-venv")
    if names & {t.split("=")[0] for t in base}:
        findings.append("a package is both pinned (ROUTE3_APT_PACKAGES) and base (ROUTE3_APT_BASE)")
    origins = [o.strip() for o in fields["APT_ORIGIN"].split(",")]
    if not all(ORIGIN.fullmatch(o) for o in origins) or len(set(origins)) != len(origins) or origins != sorted(origins):
        findings.append("ROUTE3_APT_ORIGIN must be sorted, unique '<url> <suite>/<component>' entries separated by ', '")
    if fields["WHEEL"] != WHEEL_NAME or fields["WHEEL_SHA256"] != WHEEL_SHA256:
        findings.append("the wheel is not the accepted pin")
    if findings or record_text is None:
        return findings
    return bind_findings(fields, record_text, reference_text)


BOUND_KEYS = ("APT_PACKAGES", "APT_BASE", "APT_ORIGIN", "PY_SHA256", "BASELINE_SHA256", "REFERENCE_SHA256")


def bind_findings(fields: dict[str, str], record_text: str, reference_text: str | None) -> list[str]:
    """The package fields against the baseline record and the payload reference they claim to come from: both digests, tokens, origin allow-list and interpreter digest."""
    missing = [f"ROUTE3_{k} is missing" for k in BOUND_KEYS if k not in fields]
    if missing:
        return missing
    if sha256_bytes(record_text.encode()) != fields["BASELINE_SHA256"]:
        return ["ROUTE3_BASELINE_SHA256 is not the SHA-256 of the baseline record"]
    try:
        record = Baseline.parse(record_text)
    except RecordError as error:
        return [str(error)]
    findings = []
    if reference_text is None:
        findings.append("the payload reference is required: nothing else binds the installed payload to the signed archive")
    elif sha256_bytes(reference_text.encode()) != fields["REFERENCE_SHA256"]:
        findings.append("ROUTE3_REFERENCE_SHA256 is not the SHA-256 of the payload reference")
    else:
        try:
            findings += reference_findings(Reference.parse(reference_text), record, record_text)
        except RecordError as error:
            findings.append(str(error))
    for key, want in (("APT_PACKAGES", record.tokens("pin")), ("APT_BASE", record.tokens("base")), ("APT_ORIGIN", record.origin_list()), ("PY_SHA256", record.interpreter_sha256)):
        if fields[key] != want:
            findings.append(f"ROUTE3_{key} does not equal the baseline record ({fields[key]!r} != {want!r}); the interpreter field must equal the installed file")
    return findings


# ---- the archive, manifest and SA-2 tree ---------------------------------------------------------------------------------------------

def _git(repo: Path, *argv: str, check: bool = True) -> subprocess.CompletedProcess:
    env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}
    try:
        done = subprocess.run(["/usr/bin/git", "-C", str(repo), "-c", "core.quotepath=off", *argv], capture_output=True, env=env, stdin=subprocess.DEVNULL, check=False, timeout=600)
    except (OSError, subprocess.SubprocessError) as error:
        raise EnvironmentFailure(f"cannot run git: {error}") from error
    if check and done.returncode != 0:
        raise RecordError(f"git {' '.join(argv[:2])} failed: {done.stderr.decode(errors='replace').strip()}")
    return done


def git_archive(repo: Path, rev: str) -> bytes:
    """``code.tar`` exactly as the runbook's recipe builds it, with user and system git configuration neutralised and the tar umask pinned."""
    if not re.fullmatch(r"[0-9a-f]{40}", rev):
        raise RecordError("the revision must be a full 40-hex commit id")
    if _git(repo, "cat-file", "-t", rev).stdout.strip() != b"commit":
        raise RecordError(f"{rev} is not a commit")
    return _git(repo, "-c", "tar.umask=0002", "archive", "--format=tar", rev, "--", *ARCHIVE_PATHSPEC).stdout


def archive_files(data: bytes) -> dict[str, str]:
    """Validate an archive exactly like runbook block D's ``archive`` check and return {path: sha256}. Anything else than regular files and directories is a finding."""
    bad = re.compile(BAD_MEMBER_NAME, re.I)
    files: dict[str, str] = {}
    total = 0
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:") as tar:
        for member in tar:
            name = member.name.rstrip("/")
            parts = name.split("/")
            if not name or name.startswith("/") or any(p in ("", "..", ".") or bad.fullmatch(p) for p in parts) or not SAFE_PATH.fullmatch(name):
                raise RecordError(f"archive member name is not allowed: {name!r}")
            if member.mode & 0o7000:
                raise RecordError(f"archive member has a special mode bit: {name}")
            if member.isdir():
                continue
            if not member.isreg():
                raise RecordError(f"archive member is not a regular file or directory: {name}")
            if name in files:
                raise RecordError(f"archive member is duplicated: {name}")
            total += member.size
            if member.size > MAX_MEMBER_BYTES or total > MAX_ARCHIVE_BYTES:
                raise RecordError("archive is too large")
            handle = tar.extractfile(member)
            files[name] = sha256_bytes(handle.read() if handle else b"")
    if not files:
        raise RecordError("archive holds no file")
    return files


def render_manifest(files: dict[str, str]) -> str:
    """``MANIFEST.sha256``: ``<sha256>  <path>`` per file, bytewise sorted (the ``LC_ALL=C sort -z`` of the recipe), LF terminated."""
    return "".join(f"{files[p]}  {p}\n" for p in sorted(files, key=lambda p: p.encode()))


def sa2_tree_digest(root: Path, require_root_owner: bool = False) -> str:
    """The identity S3.2 computes: SHA-256 of ``find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum`` run inside the artifact directory.

    Links, special files, group/other-writable entries and names that ``sha256sum`` would escape are findings, as is an empty tree.
    """
    listing = []
    for current, dirs, names in os.walk(root, followlinks=False):
        for entry in [*dirs, *names]:
            path = Path(current) / entry
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                raise RecordError(f"SA-2 tree holds a link: {path.relative_to(root)}")
            if info.st_mode & 0o022:
                raise RecordError(f"SA-2 tree entry is group/other-writable: {path.relative_to(root)}")
            if require_root_owner and info.st_uid != 0:
                raise RecordError(f"SA-2 tree entry is not root-owned: {path.relative_to(root)}")
            if not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
                raise RecordError(f"SA-2 tree holds a special file: {path.relative_to(root)}")
            if stat.S_ISREG(info.st_mode):
                relative = "./" + str(path.relative_to(root))
                if not re.fullmatch(r"\./[A-Za-z0-9._+@/-]+", relative):
                    raise RecordError(f"SA-2 tree file name is not plain: {relative!r}")
                listing.append((relative.encode(), sha256_file(path)))
    if not listing:
        raise RecordError("SA-2 tree holds no file")
    return sha256_bytes(b"".join(f"{digest}  {name.decode()}\n".encode() for name, digest in sorted(listing)))


def verify_release(repo: Path, fields: dict[str, str], artifacts: Path, published_ref: str, sa2_dir: Path | None = None) -> list[str]:
    """The release revision, archive, manifest and (optionally) SA-2 tree against the record. Reproduces the archive from the commit instead of trusting a file."""
    findings = []
    rev = fields["RELEASE_REV"]
    try:
        rebuilt = git_archive(repo, rev)
    except RecordError as error:
        return [str(error)]
    if _git(repo, "rev-parse", "--verify", "--quiet", f"{published_ref}^{{commit}}", check=False).returncode != 0:
        return [f"the published reference {published_ref} does not exist"]
    if _git(repo, "merge-base", "--is-ancestor", rev, published_ref, check=False).returncode != 0:
        findings.append(f"{rev} is not published: it is not an ancestor of {published_ref}")
    if _git(repo, "diff", "--quiet", rev, "--", *ARCHIVE_PATHSPEC, check=False).returncode != 0:
        findings.append("the working tree differs from the release revision inside the archive pathspec (mutable or unreviewed tree)")
    untracked = _git(repo, "status", "--porcelain", "--untracked-files=all", "--", *ARCHIVE_PATHSPEC).stdout.strip()
    if untracked:
        findings.append("uncommitted or untracked files exist inside the archive pathspec (mutable or unreviewed tree)")
    try:
        files = archive_files(rebuilt)
    except RecordError as error:
        return [*findings, str(error)]
    manifest = render_manifest(files).encode()
    for label, want, actual in (("archive", fields["ARCHIVE_SHA256"], sha256_bytes(rebuilt)), ("manifest", fields["MANIFEST_SHA256"], sha256_bytes(manifest))):
        if want != actual:
            findings.append(f"ROUTE3_{label.upper()}_SHA256 does not equal the {label} reproduced from {rev} ({want} != {actual})")
    for name, content in (("code.tar", rebuilt), ("MANIFEST.sha256", manifest)):
        path = artifacts / name
        if path.is_symlink() or not path.is_file():
            findings.append(f"{path} is missing or not a regular file")
        elif path.read_bytes() != content:
            findings.append(f"{path} is not byte-identical to the artifact reproduced from {rev}")
    wheel = artifacts / "wheelhouse" / fields["WHEEL"]
    if wheel.is_symlink() or not wheel.is_file() or sha256_file(wheel) != fields["WHEEL_SHA256"]:
        findings.append(f"{wheel} is missing or differs from the pinned wheel digest")
    if sa2_dir is not None:
        try:
            digest = sa2_tree_digest(sa2_dir)
        except RecordError as error:
            findings.append(str(error))
        else:
            if digest != fields["SA2_TREE_SHA256"]:
                findings.append(f"ROUTE3_SA2_TREE_SHA256 does not equal the SA-2 tree ({fields['SA2_TREE_SHA256']} != {digest})")
    return findings


def build_archive(repo: Path, rev: str, out: Path) -> tuple[str, str]:
    """Write ``code.tar`` and ``MANIFEST.sha256`` for a commit into a new directory and return their digests. Refuses an existing destination."""
    data = git_archive(repo, rev)
    manifest = render_manifest(archive_files(data)).encode()
    try:
        out.mkdir(mode=0o700)
    except FileExistsError as error:
        raise RecordError(f"{out} already exists: artifacts are written to a new directory only") from error
    (out / "code.tar").write_bytes(data)
    (out / "MANIFEST.sha256").write_bytes(manifest)
    return sha256_bytes(data), sha256_bytes(manifest)


def sa2_reference(archive: Path, wheel: Path, python: str = INTERPRETER) -> str:
    """Build the SA-2 tree twice from the verified archive and the pinned wheel, exactly as S3.2 does, and return the digest only if both builds agree. Off production."""
    data = archive.read_bytes()
    archive_files(data)
    if sha256_file(wheel) != WHEEL_SHA256:
        raise RecordError("the wheel is not the accepted pin")
    digests = []
    with tempfile.TemporaryDirectory(prefix="route3-sa2-") as scratch:
        code = Path(scratch) / "code"
        code.mkdir()
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:") as tar:
            tar.extractall(code, filter="data")
        for attempt in ("a", "b"):
            dest = Path(scratch) / f"sa2-{attempt}"
            done = subprocess.run([python, "-I", "-S", "-B", str(code / "infra/rp11-h1/build.py"), "--wheel", str(wheel), "--dest", str(dest)],
                                  capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"}, stdin=subprocess.DEVNULL, check=False, timeout=600)
            if done.returncode != 0:
                raise RecordError(f"the SA-2 build failed (status {done.returncode}): {done.stderr.strip()[-400:]}")
            digests.append(sa2_tree_digest(dest))
    if digests[0] != digests[1]:
        raise RecordError(f"the SA-2 build is not reproducible ({digests[0]} != {digests[1]})")
    return digests[0]


def reference_interpreter(version: str, workdir: Path, run: Callable[[Sequence[str], Path], tuple[int, str]] | None = None) -> str:
    """The digest of ``/usr/bin/python3.14`` inside ``python3.14-minimal=<version>`` as the archive ships it. Off production, unprivileged, in an empty directory.

    The downloaded ``.deb`` must match the SHA-256 that the archive's signed index states for exactly that version before anything is extracted.
    """
    if not re.fullmatch(r"[A-Za-z0-9.+~:-]+", version):
        raise RecordError("the version is not a plain Debian version")
    if workdir.exists() and any(workdir.iterdir()):
        raise RecordError(f"{workdir} is not empty")
    workdir.mkdir(parents=True, exist_ok=True)

    def default(argv: Sequence[str], cwd: Path) -> tuple[int, str]:
        done = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"}, stdin=subprocess.DEVNULL, check=False, timeout=900)
        return done.returncode, done.stdout

    run = run or default
    status, shown = run(["/usr/bin/apt-cache", "show", f"python3.14-minimal={version}"], workdir)
    stated = {m[1] for m in re.finditer(r"^SHA256: ([0-9a-f]{64})$", shown, re.M)}
    if status != 0 or len(stated) != 1:
        raise RecordError("the archive index does not state exactly one SHA-256 for that version")
    status, _ = run(["/usr/bin/apt-get", "download", f"python3.14-minimal={version}"], workdir)
    debs = sorted(workdir.glob("python3.14-minimal_*.deb"))
    if status != 0 or len(debs) != 1:
        raise RecordError("apt-get download did not produce exactly one python3.14-minimal package file")
    if sha256_file(debs[0]) != next(iter(stated)):
        raise RecordError("the downloaded package differs from the SHA-256 of the archive's signed index")
    done = subprocess.run(["/usr/bin/dpkg-deb", "--fsys-tarfile", str(debs[0])], capture_output=True, check=False, stdin=subprocess.DEVNULL, timeout=300)
    if done.returncode != 0:
        raise RecordError("dpkg-deb could not read the package")
    with tarfile.open(fileobj=io.BytesIO(done.stdout), mode="r:") as tar:
        member = tar.getmember("./usr/bin/python3.14")
        if not member.isreg():
            raise RecordError("/usr/bin/python3.14 is not a regular file in the package")
        return sha256_bytes(tar.extractfile(member).read())


# ---- command line --------------------------------------------------------------------------------------------------------------------

def _report(findings: Sequence[str]) -> int:
    for finding in findings:
        print(f"NO-GO: {finding}")
    return 1 if findings else 0


def _host(args: argparse.Namespace) -> Host:
    return Host(Path(args.admindir), Path(args.bin_dir), Path(args.interpreter), Path(args.os_release), Path(args.root))


def _read(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise EnvironmentFailure(f"cannot read {path}: {error}") from error


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Route 3 release-record tooling (read-only on the host)")
    sub = parser.add_subparsers(dest="command", required=True)

    def host_options(p: argparse.ArgumentParser) -> None:
        p.add_argument("--admindir", default="/var/lib/dpkg")
        p.add_argument("--bin-dir", default="/usr/bin")
        p.add_argument("--interpreter", default=INTERPRETER)
        p.add_argument("--os-release", default="/etc/os-release")
        p.add_argument("--root", default="/", help="the directory packaged paths are resolved below (a private directory in tests)")

    p = sub.add_parser("attest-host", help="print the baseline record of the installed Python 3.14 closure")
    host_options(p)
    p.add_argument("--allow-origin", action="append", default=[], help="an accepted '<url> <suite>/<component>' (repeatable)")
    p = sub.add_parser("verify-host", help="re-attest the host and reject any drift from a reviewed baseline record or from the signed-archive payload reference")
    host_options(p)
    p.add_argument("--record", required=True)
    p.add_argument("--reference", required=True, help="the payload reference derived from the signed archive (reference-payload)")
    p.add_argument("--field", action="append", default=[], metavar="KEY=VALUE", help="a release field to bind to the record (the five package fields; repeatable)")
    p = sub.add_parser("propose", help="print the block F values a baseline record (and its payload reference) imply, for the supplier's review")
    p.add_argument("--record", required=True)
    p.add_argument("--reference")
    p = sub.add_parser("check-fields", help="validate the runbook's block F (no UNSET, well formed, bound to the baseline record and the payload reference)")
    p.add_argument("--runbook", required=True)
    p.add_argument("--record")
    p.add_argument("--reference")
    p = sub.add_parser("reference-payload", help="derive the payload reference of a baseline record from the signed archive (off production)")
    p.add_argument("--record", required=True)
    p.add_argument("--workdir", required=True)
    p = sub.add_parser("payload-rows", help="diagnostic: the canonical metadata and payload rows of an installed package or of a package file")
    host_options(p)
    p.add_argument("--package", required=True)
    p.add_argument("--deb")
    p = sub.add_parser("build-archive", help="write code.tar and MANIFEST.sha256 for a commit into a new directory")
    p.add_argument("--repo", required=True)
    p.add_argument("--rev", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("verify-release", help="reproduce the archive from the revision and check the artifacts and SA-2 tree against block F")
    p.add_argument("--repo", required=True)
    p.add_argument("--runbook", required=True)
    p.add_argument("--artifacts", required=True)
    p.add_argument("--published-ref", required=True)
    p.add_argument("--sa2-dir")
    p = sub.add_parser("sa2-digest", help="the S3.2 identity of an SA-2 tree")
    p.add_argument("dir")
    p.add_argument("--require-root-owner", action="store_true")
    p = sub.add_parser("sa2-reference", help="build the SA-2 tree twice off production and print the agreed digest")
    p.add_argument("--archive", required=True)
    p.add_argument("--wheel", required=True)
    p = sub.add_parser("reference-interpreter", help="digest of /usr/bin/python3.14 in the archive's python3.14-minimal package (off production)")
    p.add_argument("--version", required=True)
    p.add_argument("--workdir", required=True)
    args = parser.parse_args(argv)

    try:
        if args.command == "attest-host":
            sys.stdout.write(attest(_host(args), args.allow_origin).render())
            return 0
        if args.command == "verify-host":
            text, reference_text = _read(args.record), _read(args.reference)
            record, reference = Baseline.parse(text), Reference.parse(reference_text)
            host = _host(args)
            fields = dict(item.split("=", 1) for item in args.field if "=" in item)
            findings = bind_findings(fields, text, reference_text) if args.field else reference_findings(reference, record, text)
            live = attest(host)
            findings += compare(record, live) + verify_files(host, record) + payload_findings(host, live, reference)
            if not findings:
                print(f"ok: the host still is the reviewed baseline and every member's installed payload and metadata equal the signed-archive package ({len(record.members)} members)")
            return _report(findings)
        if args.command == "propose":
            text = _read(args.record)
            record = Baseline.parse(text)
            values = [("APT_PACKAGES", record.tokens("pin")), ("APT_BASE", record.tokens("base")), ("APT_ORIGIN", record.origin_list()), ("PY_SHA256", record.interpreter_sha256),
                      ("BASELINE_SHA256", sha256_bytes(text.encode()))]
            if args.reference:
                reference_text = _read(args.reference)
                Reference.parse(reference_text)
                values.append(("REFERENCE_SHA256", sha256_bytes(reference_text.encode())))
            for key, value in values:
                print(f'ROUTE3_{key}="{value}"' if " " in value else f"ROUTE3_{key}={value}")
            print("# PY_SHA256 here is the INSTALLED file; the field must be the independent reference-interpreter digest, and the two must be equal")
            return 0
        if args.command == "check-fields":
            fields = read_fields(_read(args.runbook))
            findings = validate_fields(fields, _read(args.record) if args.record else None, _read(args.reference) if args.reference else None)
            if not findings:
                print("ok: the release record is complete" + (" and bound to the baseline record and the payload reference" if args.record else ""))
            return _report(findings)
        if args.command == "reference-payload":
            text = _read(args.record)
            sys.stdout.write(build_reference(Baseline.parse(text), text, Path(args.workdir)).render())
            return 0
        if args.command == "payload-rows":
            if args.deb:
                rows = deb_rows(parse_deb(Path(args.deb).read_bytes()))
            else:
                host = _host(args)
                packages = {p.name: p for p in parse_status(host.status_text())}
                fields = {f["Package"]: f for f in _paragraphs(host.status_text()) if "Package" in f}
                if args.package not in packages:
                    raise RecordError(f"{args.package} is not installed")
                rows = installed_rows(host, packages[args.package], fields[args.package])
            sys.stdout.write("".join(f"meta\t{r}\n" for r in rows[0]) + "".join(f"file\t{r}\n" for r in sorted(rows[1], key=lambda r: r.encode())))
            return 0
        if args.command == "build-archive":
            archive, manifest = build_archive(Path(args.repo), args.rev, Path(args.out))
            print(f"ROUTE3_ARCHIVE_SHA256={archive}\nROUTE3_MANIFEST_SHA256={manifest}")
            return 0
        if args.command == "verify-release":
            fields = read_fields(_read(args.runbook))
            findings = validate_fields(fields)
            if not findings:
                findings = verify_release(Path(args.repo), fields, Path(args.artifacts), args.published_ref, Path(args.sa2_dir) if args.sa2_dir else None)
            if not findings:
                print("ok: revision, archive, manifest" + (" and SA-2 tree" if args.sa2_dir else "") + " match the release record")
            return _report(findings)
        if args.command == "sa2-digest":
            print(sa2_tree_digest(Path(args.dir), args.require_root_owner))
            return 0
        if args.command == "sa2-reference":
            print(sa2_reference(Path(args.archive), Path(args.wheel)))
            return 0
        if args.command == "reference-interpreter":
            print(reference_interpreter(args.version, Path(args.workdir)))
            return 0
    except RecordError as error:
        return _report([str(error)])
    except (EnvironmentFailure, OSError) as error:
        print(f"ENVIRONMENT: {error}", file=sys.stderr)
        return 3
    return 2


if __name__ == "__main__":
    sys.exit(main())
