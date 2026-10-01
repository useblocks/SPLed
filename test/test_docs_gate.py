"""The documentation gate: every variant and kit, both readers, strict, the same needs.

For each cell this selects the build CMake configures for it, so codelinks
evaluates that build's `#ifdef` branches with its compile database. Then it builds
the documents with `sphinx-build -W` and with ubc, and compares the two needs.json
files need by need: IDs, types, titles, fields and links. Whatever the two readers
may differ in is listed, with its reason, in docs_exceptions.toml; any other
warning or difference fails.

Two shapes. The design documentation (`docs`) of every variant and kit, and of
every component's report, needs a configure only. The reports of the test kit
(`reports`) carry what the test run produces -- the test specifications, the test
results and the source listings, read where spl-core writes them -- so that
build is compiled and its tests are run first. That shape is where the two readers
once disagreed by 42 needs, every one of them on the verification side.

Both build times go into the job summary on CI (`GITHUB_STEP_SUMMARY`), so the
speed of the second reader is visible next to the first.

The configure needs CMake, Ninja and a C/C++ compiler: on CI the runner's, here
whatever is on PATH. Without them the tests skip, and on CI (`CI` is set) they
fail instead, because a gate that only runs on a developer machine is none.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import time
import tomllib
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

VARIANTS = ["Base/Dev", "Disco", "IDEA/Sloemada", "Sleep", "Spa"]
KITS = ["prod", "test"]

pytestmark = [
    pytest.mark.docs,
    pytest.mark.gate_develop_pr,
    pytest.mark.gate_develop_push,
    pytest.mark.gate_develop_nightly,
    pytest.mark.gate_release_pr,
    pytest.mark.gate_release,
]

EXCEPTIONS = tomllib.loads((PROJECT_ROOT / "test" / "docs_exceptions.toml").read_text(encoding="utf-8"))
EXCEPTED_NEEDS = {entry["id"] for entry in EXCEPTIONS.get("needs", [])}
EXCEPTED_UBC_WARNINGS = {entry["code"]: entry["count"] for entry in EXCEPTIONS.get("ubc_warnings", [])}

#: Build times per cell, for the job summary.
TIMINGS: list[tuple[str, str, float, float, int]] = []


def _find_ubc() -> str | None:
    for candidate in (os.environ.get("UBC"), shutil.which("ubc")):
        if candidate and Path(candidate).is_file():
            return candidate
    for extension in sorted((Path.home() / ".vscode" / "extensions").glob("useblocks.ubcode-*"), reverse=True):
        for name in ("ubc", "ubc.exe"):
            candidate = extension / "server" / "cli" / name
            if candidate.is_file():
                return str(candidate)
    return None


def _require(what: str, available: bool) -> None:
    if available:
        return
    if os.environ.get("CI"):
        pytest.fail(f"{what} is required on CI")
    pytest.skip(f"{what} is not available")


@pytest.fixture(scope="module", autouse=True)
def _restore_the_developers_selection():
    """The gate selects every cell in turn; what the developer had selected comes back."""
    sys.path.insert(0, str(PROJECT_ROOT / "tools"))
    import variant_data

    saved = {}
    for name in variant_data.SELECTION_STATE:
        path = PROJECT_ROOT / name
        saved[path] = path.read_bytes() if path.is_file() else None
    yield
    for path, content in saved.items():
        if content is None:
            path.unlink(missing_ok=True)
        else:
            path.write_bytes(content)
    if os.environ.get("GITHUB_STEP_SUMMARY") and TIMINGS:
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as summary:
            summary.write("### Documentation build time per cell\n\n| Variant | Kit | Sphinx | ubc | Needs |\n| --- | --- | ---: | ---: | ---: |\n")
            summary.writelines(f"| {variant} | {kit} | {sphinx_s:.2f} s | {ubc_s:.2f} s | {needs} |\n" for variant, kit, sphinx_s, ubc_s, needs in TIMINGS)


def _select_build(variant: str, kit: str) -> Path:
    """Configure the cell's build, which selects it, and hand codelinks its database."""
    build_dir = PROJECT_ROOT / "build" / variant / kit / "Debug"
    command = [
        "cmake",
        "-S",
        str(PROJECT_ROOT),
        "-B",
        str(build_dir),
        "-G",
        "Ninja",
        f"-DVARIANT={variant}",
        f"-DBUILD_KIT={kit}",
        "-DCMAKE_BUILD_TYPE=Debug",
    ]
    if kit == "test":
        toolchain = "toolchain.cmake" if platform.system() == "Windows" else "toolchain_linux.cmake"
        command.append(f"-DCMAKE_TOOLCHAIN_FILE={PROJECT_ROOT / 'tools' / 'toolchains' / 'gcc' / toolchain}")
    configured = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    assert configured.returncode == 0, f"configuring {variant}/{kit} failed:\n{configured.stdout[-3000:]}\n{configured.stderr[-3000:]}"
    copied = subprocess.run(
        ["cmake", "--build", str(build_dir), "--target", "spled_codelinks_compile_commands"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert copied.returncode == 0, f"copying the compile database of {variant}/{kit} failed:\n{copied.stdout[-3000:]}"
    return build_dir


def _needs(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["versions"][data.get("current_version", "")]["needs"]


def _compared_fields() -> list[str]:
    config = tomllib.loads((PROJECT_ROOT / "ubproject.toml").read_text(encoding="utf-8"))["needs"]
    return ["type", "title", "status", "tags", *config.get("links", {}), *config.get("fields", {})]


def _normalized(value):
    if value in (None, "", [], {}):
        return None
    return sorted(value) if isinstance(value, list) else value


def _component_reports() -> list[tuple[str, str]]:
    """(variant, component) for every component report spl-core builds: the test kit's."""
    sys.path.insert(0, str(PROJECT_ROOT / "tools"))
    import variant_data

    return [(variant, component) for variant in VARIANTS for component in variant_data.reported_components(PROJECT_ROOT, variant, "test")]


@pytest.mark.parametrize("kit", KITS)
@pytest.mark.parametrize("variant", VARIANTS)
def test_both_readers_build_the_same_documentation_strictly(variant: str, kit: str, tmp_path: Path) -> None:
    _check_one_run(variant, kit, "docs.toml", tmp_path)


@pytest.mark.parametrize(("variant", "component"), _component_reports())
def test_both_readers_build_the_same_component_report_strictly(variant: str, component: str, tmp_path: Path) -> None:
    """spl-core's per-component report, in the docs shape, which upstream tests nowhere."""
    _check_one_run(variant, "test", f"{component}/docs.toml", tmp_path, label=f"{variant}/{component}")


@pytest.mark.parametrize("variant", VARIANTS)
def test_both_readers_build_the_same_reports_strictly(variant: str, tmp_path: Path) -> None:
    """A variant's reports: its documents plus the pages its test run generated."""
    _check_one_run(variant, "test", "reports.toml", tmp_path, label=f"{variant}/test reports", built=True)


@pytest.mark.parametrize(("variant", "component"), _component_reports())
def test_both_readers_build_the_same_component_reports_strictly(variant: str, component: str, tmp_path: Path) -> None:
    """A component's report with its test specification, results and listings."""
    _check_one_run(variant, "test", f"{component}/reports.toml", tmp_path, label=f"{variant}/{component} reports", built=True)


#: The cell selected last. codelinks reads the selected build's compile database,
#: so a run of another cell selects that cell first.
_SELECTED: dict[str, tuple[str, str, Path]] = {}

#: The build directories whose reports have been built in this session.
_BUILT: set[Path] = set()


def _build_reports(build_dir: Path) -> None:
    """Compile the build and run its tests: what generates the pages the reports read."""
    if build_dir in _BUILT:
        return
    built = subprocess.run(["cmake", "--build", str(build_dir), "--target", "reports"], cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    assert built.returncode == 0, f"building the reports of {build_dir} failed:\n{built.stdout[-3000:]}\n{built.stderr[-3000:]}"
    _BUILT.add(build_dir)


def _check_one_run(variant: str, kit: str, selection_name: str, tmp_path: Path, label: str | None = None, built: bool = False) -> None:
    ubc = _find_ubc()
    _require("ubc", ubc is not None)
    _require("CMake and Ninja", bool(shutil.which("cmake") and shutil.which("ninja")))

    current = _SELECTED.get("cell")
    if current is None or current[:2] != (variant, kit):
        _SELECTED["cell"] = (variant, kit, _select_build(variant, kit))
    build_dir = _SELECTED["cell"][2]
    if built:
        _build_reports(build_dir)
    selection = build_dir / "selection" / selection_name
    label = label or f"{variant}/{kit}"

    started = time.perf_counter()
    sphinx = subprocess.run(
        [
            sys.executable,
            "-m",
            "sphinx",
            "-W",
            "--keep-going",
            "-q",
            "-b",
            "html",
            "-D",
            f"spl_selection={selection}",
            "-d",
            str(tmp_path / "doctrees"),
            str(PROJECT_ROOT),
            str(tmp_path / "sphinx"),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env={**os.environ, "VARIANT": variant},
        check=False,
    )
    sphinx_seconds = time.perf_counter() - started
    warnings = [line for line in sphinx.stderr.splitlines() if "WARNING" in line or "ERROR" in line]
    if (PROJECT_ROOT / ".git").is_file():
        # A linked git worktree, where `.git` is a file: sphinx-codelinks does not
        # find the git root there and warns once per source (codelinks.git_ref).
        # A clone, as on CI, does not have the problem, so it is tolerated here only.
        warnings = [line for line in warnings if "[codelinks.git_ref]" not in line]
    tolerated_only = (PROJECT_ROOT / ".git").is_file() and not warnings
    assert (sphinx.returncode == 0 or tolerated_only) and not warnings, f"{label}: Sphinx is not clean in strict mode:\n" + "\n".join(warnings or [sphinx.stderr[-3000:]])

    override = selection.read_text(encoding="utf-8")
    checked = subprocess.run([ubc, "check", "--no-cache", "--output-format", "json", "-c", override], cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    counts: dict[str, int] = {}
    for diagnostic in json.loads(checked.stdout or "{}").get("diagnostics", []):
        if diagnostic["severity"] != "info":
            counts[diagnostic["code"]] = counts.get(diagnostic["code"], 0) + 1
    unexpected = {code: count for code, count in counts.items() if EXCEPTED_UBC_WARNINGS.get(code) != count}
    assert not unexpected, f"{label}: ubc reports findings docs_exceptions.toml does not name: {unexpected}"

    started = time.perf_counter()
    built = subprocess.run(
        [ubc, "build", "html", "--no-cache", "--deny", "none", "-o", str(tmp_path / "ubc"), "-c", override], cwd=PROJECT_ROOT, capture_output=True, text=True, check=False
    )
    ubc_seconds = time.perf_counter() - started
    assert built.returncode == 0, f"{label}: ubc build html failed:\n{built.stdout[-3000:]}\n{built.stderr[-3000:]}"

    sphinx_needs = _needs(tmp_path / "sphinx" / "needs.json")
    ubc_needs = _needs(tmp_path / "ubc" / "needs.json")
    TIMINGS.append((variant, label.split("/", 1)[1] if label != f"{variant}/{kit}" else kit, sphinx_seconds, ubc_seconds, len(sphinx_needs)))

    only_sphinx = sorted(set(sphinx_needs) - set(ubc_needs) - EXCEPTED_NEEDS)
    only_ubc = sorted(set(ubc_needs) - set(sphinx_needs) - EXCEPTED_NEEDS)
    assert not only_sphinx and not only_ubc, f"{label}: needs in one reader only: Sphinx {only_sphinx}, ubc {only_ubc}"

    fields = _compared_fields()
    differences = [
        f"{need_id}.{field}: Sphinx {_normalized(sphinx_needs[need_id].get(field))!r}, ubc {_normalized(ubc_needs[need_id].get(field))!r}"
        for need_id in sorted(set(sphinx_needs) & set(ubc_needs))
        for field in fields
        if _normalized(sphinx_needs[need_id].get(field)) != _normalized(ubc_needs[need_id].get(field))
    ]
    assert not differences, f"{label}: the readers disagree about {len(differences)} values:\n" + "\n".join(differences[:40])
