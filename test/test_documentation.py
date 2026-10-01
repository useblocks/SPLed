"""The documentation gate: every variant's documents build, and build right.

**This suite needs no compiler.** KConfig is pure Python and the documents are
text, while CMake's top-level `project()` call demands a C toolchain before it
will configure at all. Keeping the gate independent of that is the point: the
documentation is the part of this product line that most people read and edit,
and it should not take a cross-compiler to check it.

What it proves, per variant:

- the variant data generates at all -- which exercises the KConfig model and the
  parts.cmake grammar for every variant, not just the one someone last built;
- Sphinx builds the variant's documents without error;
- the documents present are exactly the ones the variant's component list says,
  which is the property the whole variant-gating design exists to provide.

And, with `ubc`, that a second reader which never runs conf.py decides the same
document set.
"""

import ast
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

import variant_data

pytestmark = [
    pytest.mark.docs,
    pytest.mark.gate_develop_pr,
    pytest.mark.gate_develop_push,
    pytest.mark.gate_develop_nightly,
    pytest.mark.gate_release_pr,
    pytest.mark.gate_release,
]

VARIANTS = ["Base/Dev", "Disco", "IDEA/Sloemada", "Sleep", "Spa"]

#: Component documents that exist in the tree, with the component each belongs
#: to. The build must contain a page exactly when the variant contains the
#: component -- stated here rather than derived, so that a bug in the derivation
#: cannot make the test agree with it.
COMPONENT_DOCS = {
    "components/light_controller": "components/light_controller/doc/index.html",
    "components/main_control_knob": "components/main_control_knob/doc/index.html",
    "components/power_button": "components/power_button/doc/index.html",
    "components/power_signal_processing": "components/power_signal_processing/doc/index.html",
    "components/brightness_controller": "components/brightness_controller/doc/index.html",
    "components/auto_off": "components/auto_off/doc/index.html",
    "test/spled_integration": "test/spled_integration/doc/index.html",
    "components/examples/hello_gmock": "components/examples/hello_gmock/doc/index.html",
    "components/examples/flight_controller": "components/examples/flight_controller/doc/index.html",
}

#: The toctree globs of doc/components/index.md. ubCode reports a glob that
#: matched only documents a variant excludes, so these are what the parity
#: comparison has to evaluate.
COMPONENT_TOCTREE_GLOBS = (
    "components/*/doc/index",
    "components/examples/*/doc/index",
    "test/*/doc/index",
)


@pytest.fixture(scope="module")
def all_variant_data() -> None:
    """Generate the whole matrix once, the way a developer or CI would."""
    subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "tools" / "variant_data.py"), "--all"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
    )


@pytest.fixture(scope="module", autouse=True)
def selected_cell(all_variant_data: None) -> Iterator[None]:
    """Select one cell for the readers that cannot take one on the command line.

    `ubc` loads the project through ubproject.toml -> ubproject.variants.toml ->
    build/selection.toml, and refuses to load it when that file is missing. The
    developer's own selection -- which points at the build they configured -- is
    put back byte for byte, every file of it, because this test must not repoint
    their IDE at a test selection.
    """
    saved = {PROJECT_ROOT / name: (PROJECT_ROOT / name).read_bytes() if (PROJECT_ROOT / name).is_file() else None for name in variant_data.SELECTION_STATE}

    subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools" / "variant_data.py"),
            "--all",
            "--current",
            "--variant",
            "Disco",
            "--kit",
            "test",
        ],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
    )
    try:
        yield
    finally:
        for path, content in saved.items():
            if content is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(content)


def _select_cell(variant: str, kit: str, target: str) -> list[str]:
    """The sphinx-build option that selects one cell of the matrix.

    A command-line override of `needs_variant_data_file`, which sphinx-needs keeps
    even though conf.py reads a selection. It is what spl-core passes for the
    shape it builds, and the key `ubc check -c` overrides as well.
    """
    return ["-D", f"needs_variant_data_file={PROJECT_ROOT / 'build' / 'variants' / variant / kit / f'{target}.json'}"]


def _build_docs(variant: str, kit: str, target: str, out_dir: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "VARIANT": variant}
    # Deliberately NOT inheriting SPHINX_BUILD_CONFIGURATION_FILE: this gate is
    # the bare build, the one a reader with no CMake in sight performs.
    env.pop("SPHINX_BUILD_CONFIGURATION_FILE", None)
    return subprocess.run(
        [sys.executable, "-m", "sphinx", "-b", "html", *_select_cell(variant, kit, target), str(PROJECT_ROOT), str(out_dir)],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_variant_data_generates_for_every_variant(all_variant_data: None) -> None:
    """`--check` passes right after `--all`, so the two agree by construction."""
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "tools" / "variant_data.py"), "--all", "--check"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("variant", VARIANTS)
def test_variant_documents_build(all_variant_data: None, variant: str, tmp_path: Path) -> None:
    result = _build_docs(variant, "test", "docs", tmp_path / "html")
    assert result.returncode == 0, f"sphinx-build failed for {variant}:\n{result.stdout[-4000:]}\n{result.stderr[-4000:]}"
    assert (tmp_path / "html" / "index.html").is_file()


@pytest.mark.parametrize("variant", VARIANTS)
def test_the_built_documents_are_exactly_the_variants_components(all_variant_data: None, variant: str, tmp_path: Path) -> None:
    """The property the whole design exists to provide.

    A component's document is in the build exactly when the variant's
    parts.cmake adds it. Not when a feature suggests it, and never because the
    variant happens to be called something.
    """
    out = tmp_path / "html"
    result = _build_docs(variant, "test", "docs", out)
    assert result.returncode == 0, (result.stdout + result.stderr)[-2000:]

    components = set(variant_data.components(PROJECT_ROOT, variant, "test"))

    for component, page in COMPONENT_DOCS.items():
        built = (out / page).is_file()
        if component in components:
            assert built, f"{variant} contains {component} but {page} was not built"
        else:
            assert not built, f"{variant} does not contain {component} but {page} was built"


def test_the_integration_suite_follows_the_build_kit(all_variant_data: None, tmp_path: Path) -> None:
    """Disco's parts.cmake adds it for the test kit only.

    This is the case the old `variant == "Disco"` gate got wrong: it claimed the
    suite for Disco's prod kit too. Gating on the component list is what makes
    the document follow the same rule the build does.
    """
    page = COMPONENT_DOCS["test/spled_integration"]

    prod = tmp_path / "prod"
    assert _build_docs("Disco", "prod", "docs", prod).returncode == 0
    assert not (prod / page).is_file(), "the integration suite is not in Disco's prod kit"

    test = tmp_path / "test"
    assert _build_docs("Disco", "test", "docs", test).returncode == 0
    assert (test / page).is_file(), "the integration suite is in Disco's test kit"


def test_no_document_is_rendered_through_jinja(all_variant_data: None, tmp_path: Path) -> None:
    """A Jinja construct in a document would now reach the reader verbatim.

    There is no `source-read` hook any more, so this is not a style rule: an
    accidental `{{ ... }}` is shipped as literal text rather than rendered. The
    check is on the sources, because the built HTML escapes braces anyway.
    """
    offenders = []
    for pattern in ("index.md", "doc/**/*.md", "components/**/doc/*.md", "test/*/doc/*.md"):
        for path in PROJECT_ROOT.glob(pattern):
            text = path.read_text(encoding="utf-8")
            if "{{" in text or "{%" in text:
                offenders.append(str(path.relative_to(PROJECT_ROOT)))
    assert not offenders, f"Jinja constructs in documents: {offenders}"


def test_conf_py_registers_no_source_read_handler() -> None:
    """The global Jinja pass is gone, and its one scoped exception went with it.

    A `source-read` handler runs on every document Sphinx reads, so it is the
    mechanism by which a document could be templated without ubCode knowing.
    The project had exactly one -- a line filter that blanked the `{% raw %}`
    markers spl-core put in generated listings -- and that is gone too:
    `SPL_SOURCE_DOCS_JINJA_RAW_TAGS OFF` makes spl-core invoke clanguru without
    the flag, so there are no markers left to blank. A handler here would only
    reintroduce the divergence this design exists to remove.
    """
    conf = (PROJECT_ROOT / "conf.py").read_text(encoding="utf-8")

    handlers = [
        node
        for node in ast.walk(ast.parse(conf))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "connect"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == "source-read"
    ]
    assert not handlers, "conf.py must not register a source-read handler"

    # The pass that rendered every document is gone and stays gone.
    assert "render_string" not in conf, "the global Jinja pass must not come back"


# --- the cross-reader gate -------------------------------------------------
#
# Everything above proves the Sphinx build behaves. The point of the whole
# design, though, is that a SECOND reader -- one that never runs conf.py --
# decides the same things. That can only be proven by running it.
#
# `ubc` ships inside the ubCode VS Code extension and is on neither PyPI nor
# npm, so there is no install step this repository can own. These tests skip
# when it is absent rather than pretending to cover it; set UBC, or put it on
# PATH, to turn them on. See AGENTS.md.


def _find_ubc() -> str | None:
    if (explicit := os.environ.get("UBC")) and Path(explicit).is_file():
        return explicit
    if found := shutil.which("ubc"):
        return found
    extensions = Path.home() / ".vscode" / "extensions"
    candidates = sorted(extensions.glob("useblocks.ubcode-*/server/cli/ubc"))
    return str(candidates[-1]) if candidates else None


UBC = _find_ubc()
needs_ubc = pytest.mark.skipif(UBC is None, reason="ubc not found; set UBC or put it on PATH")


def test_ubc_is_available_where_it_is_required() -> None:
    """A skipped parity test must not be able to pass the gate by omission.

    The tests below are the only check that the two readers agree, and they
    skip when ubc is absent -- which it is on any machine that has not
    installed it. A check that silently does not run is worse than no check,
    because the green tick claims it did.

    So the CI job that installs ubc sets CI_REQUIRE_UBC, and this turns the
    skip into one clear failure. The other tests still skip rather than
    erroring on a missing binary, so the reason is stated once.
    """
    if not os.environ.get("CI_REQUIRE_UBC"):
        pytest.skip("CI_REQUIRE_UBC is not set; ubc is optional here")

    assert UBC is not None, (
        "CI_REQUIRE_UBC is set but ubc was not found on PATH, in $UBC, or in the "
        "VS Code extension directory. The parity tests would have skipped and the "
        "documentation gate would have passed without checking that ubCode and "
        "Sphinx agree, which is the property it exists for."
    )


def _ubc_check(variant: str, kit: str, target: str) -> list[dict]:
    result = subprocess.run(
        [
            UBC,
            "check",
            "-c",
            f"needs.variant_data_file = 'build/variants/{variant}/{kit}/{target}.json'",
            "--output-format",
            "json",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.stdout, f"ubc check produced no JSON for {variant}:\n{result.stderr[-2000:]}"
    return json.loads(result.stdout).get("diagnostics", [])


@needs_ubc
@pytest.mark.parametrize("variant", VARIANTS)
def test_ubc_reports_no_errors(all_variant_data: None, variant: str) -> None:
    diagnostics = _ubc_check(variant, "test", "docs")
    errors = [d for d in diagnostics if d["severity"] == "error"]
    assert not errors, f"{variant}: " + "; ".join(d["message"] for d in errors)


@needs_ubc
def test_ubc_finds_no_configuration_problem(all_variant_data: None) -> None:
    """A `config` diagnostic means the two readers are configured differently.

    The one informational exception is ubCode noting that a Sphinx build honours
    the variant-gating keys only when sphinx-mounts is installed -- which it is,
    and which the rest of this suite proves.
    """
    diagnostics = _ubc_check("Disco", "test", "docs")
    problems = [d for d in diagnostics if d["code"].startswith("config") and d["code"] != "config.variant_sources_sphinx_unsupported"]
    assert not problems, "; ".join(f"{d['code']}: {d['message']}" for d in problems)


def _glob_matches(pattern: str, document: str) -> bool:
    """A path glob, where `*` does not cross `/` (Sphinx's and ubCode's rule)."""
    regex = re.escape(pattern).replace(r"\*\*", ".*").replace(r"\*", "[^/]*")
    return re.fullmatch(regex, document) is not None


@needs_ubc
@pytest.mark.parametrize("variant", VARIANTS)
def test_ubc_excludes_exactly_what_sphinx_excludes(all_variant_data: None, variant: str) -> None:
    """The property the whole design exists to provide, proven across readers.

    ubCode never runs conf.py. The component list is what gates the documents,
    and doc/components/index.md globs its toctree. ubCode 0.35 reports a glob
    that matched ONLY documents the variant excludes, with one example rather
    than its members -- so the exact property is checked per glob: a glob is
    reported exactly when every component it matches is missing from the
    variant, and the example it names belongs to one of them.
    """
    diagnostics = _ubc_check(variant, "test", "docs")

    reported_globs: set[str] = set()
    for diagnostic in diagnostics:
        if diagnostic["code"] != "toctree.variant_excluded":
            continue
        message = diagnostic["message"]
        glob = re.search(r"glob pattern '([^']+)'", message)
        if glob:
            reported_globs.add(glob.group(1))
            example = re.search(r"example '([^']+)'", message)
            assert example, message
            component = example.group(1).split("/doc/", 1)[0]
            assert component in COMPONENT_DOCS, message
            continue
        entry = re.search(r"toctree entry '([^']+)'", message)
        assert entry, message
        component = entry.group(1).split("/doc/", 1)[0]
        assert component in COMPONENT_DOCS, message

    components = set(variant_data.components(PROJECT_ROOT, variant, "test"))
    covered = {component for glob in COMPONENT_TOCTREE_GLOBS for component in COMPONENT_DOCS if _glob_matches(glob, f"{component}/doc/index")}
    assert covered == set(COMPONENT_DOCS), f"the toctree globs must name every documented component, or the parity check silently skips {sorted(set(COMPONENT_DOCS) - covered)}"

    for glob in COMPONENT_TOCTREE_GLOBS:
        matched = {component for component in COMPONENT_DOCS if _glob_matches(glob, f"{component}/doc/index")}
        assert matched, f"the toctree glob {glob!r} matched no known component"
        all_excluded = all(component not in components for component in matched)
        assert (glob in reported_globs) == all_excluded, f"{variant}: ubCode {'reported' if glob in reported_globs else 'did not report'} {glob!r}, but it matches " + ", ".join(
            sorted(matched)
        )


def test_the_component_toctree_globs_are_the_ones_checked() -> None:
    """The globs the parity test evaluates are the ones the page actually has."""
    page = (PROJECT_ROOT / "doc" / "components" / "index.md").read_text(encoding="utf-8")
    for glob in COMPONENT_TOCTREE_GLOBS:
        assert f"/{glob}" in page, f"doc/components/index.md no longer toctrees {glob}"


# --- the build shape must select its own cell -------------------------------


def _build_with_cell(shape: str, out_dir: Path) -> subprocess.CompletedProcess:
    """Build the way spl-core starts Sphinx: one cell per build shape.

    conf.py reads the `-D needs_variant_data_file` override ahead of any
    selection, and the cell is what the `{if} var.build_config.target` fences
    evaluate against.
    """
    env = {**os.environ, "VARIANT": "Disco"}
    env.pop("SPHINX_BUILD_CONFIGURATION_FILE", None)
    return subprocess.run(
        [sys.executable, "-m", "sphinx", "-b", "html", *_select_cell("Disco", "test", shape), str(PROJECT_ROOT), str(out_dir)],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _cmake_set(cmake: str, variable: str) -> str:
    """The value of a `set(VARIABLE ...)` call, whitespace-tolerant."""
    match = re.search(rf"set\(\s*{re.escape(variable)}\s+(.*?)\s*\)", cmake, flags=re.DOTALL)
    assert match, f"CMakeLists.txt does not set {variable}"
    return match.group(1).strip()


def test_cmake_points_each_documentation_run_at_its_selection() -> None:
    """spl-core hands every run its own build's selection file.

    `-D spl_selection=<build>/selection/<shape>.toml` is what makes a run read
    the cell of its shape (and, for a component, its own component's cell)
    without depending on which build was configured last. This reads the
    `set(...)` calls rather than searching for the variable name, so a stray
    mention in a comment cannot satisfy it.
    """
    cmake = (PROJECT_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    assert _cmake_set(cmake, "SPL_SPHINX_OPTIONS") == ("-D spl_selection=${CMAKE_BINARY_DIR}/selection/@SHAPE@.toml")
    assert _cmake_set(cmake, "SPL_SPHINX_COMPONENT_OPTIONS") == ("-D spl_selection=${CMAKE_BINARY_DIR}/selection/@COMPONENT_PATH@/@SHAPE@.toml")


def test_the_reports_shape_reads_the_reports_cell(all_variant_data: None, tmp_path: Path) -> None:
    """Without this, a reports build quietly reads the docs cell.

    Every `{if} var.build_config.target == "reports"` fence would then evaluate
    false and the reports target would contain no reports -- with no error
    anywhere, and with the reports test still passing, because it asserts that
    the build succeeded and not that it produced anything.

    Checked on the rendered page rather than on a file list, because the fence
    is what is under test: the report sections only appear when the variant data
    says `reports`.
    """
    for shape, expect_verification in (("reports", True), ("docs", False)):
        out = tmp_path / f"{shape}_html"
        result = _build_with_cell(shape, out)
        assert result.returncode == 0, (result.stdout + result.stderr)[-2000:]
        page = (out / "components" / "light_controller" / "doc" / "index.html").read_text(encoding="utf-8")
        assert ("Verification" in page) is expect_verification, f"the {shape} shape {'should' if expect_verification else 'should not'} render the verification section"


# --- the generated report pages, where spl-core writes them ---------------


#: The three pages spl-core writes per component at CONFIGURE time, and lists
#: among its include patterns for BOTH build shapes.
SPL_CORE_REPORT_PAGES = ("unit_test_spec", "unit_test_results", "coverage")


def _fake_spl_core_report_tree(build_dir: Path, component: str) -> None:
    """Write what spl-core's configure step writes into a build directory.

    `component` is a path such as `components/light_controller`, so the pages
    land where spl-core writes them. The component's `__source_docs/index` and
    the variant-wide `reports/coverage` are included because the pages link
    them, and a report toctree that cannot resolve is the failure these tests
    are watching for.
    """
    reports = build_dir / component / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    for page in SPL_CORE_REPORT_PAGES:
        (reports / f"{page}.rst").write_text(
            f"{page}\n{'=' * len(page)}\n\nGenerated by spl-core at configure time.\n",
            encoding="utf-8",
        )

    listings = build_dir / component / "__source_docs"
    listings.mkdir(parents=True, exist_ok=True)
    (listings / "index.rst").write_text(
        "Source Files\n============\n\nNo listing in this fixture.\n",
        encoding="utf-8",
    )

    variant_reports = build_dir / "reports"
    variant_reports.mkdir(parents=True, exist_ok=True)
    (variant_reports / "coverage.rst").write_text(
        "Coverage\n========\n\nVariant-wide coverage.\n",
        encoding="utf-8",
    )


@pytest.fixture
def fake_build_dir() -> Iterator[Path]:
    """A build directory of Disco's test kit that no real build uses.

    The generated pages are read where spl-core writes them, by their paths
    inside the project, so the fixture has to live under build/ as well: at the
    depth of a real one (build/<variant>/<kit>/<build type>), which the report
    toctrees' globs rely on.
    """
    build_dir = PROJECT_ROOT / "build" / "Disco" / "test" / f"Fixture{uuid.uuid4().hex[:8]}"
    yield build_dir
    shutil.rmtree(build_dir, ignore_errors=True)


def _selection_file(tmp_path: Path, build_dir: Path, shape: str) -> Path:
    """A selection naming a fake build, as `tools/variant_data.py` would write it."""
    selection = tmp_path / f"selection-{shape}.toml"
    selection.write_text(
        variant_data.selection_toml(PROJECT_ROOT, variant_data.cell_path(PROJECT_ROOT, "Disco", "test", shape), shape, build_dir),
        encoding="utf-8",
    )
    return selection


def _build_with_selection(selection: Path, out_dir: Path) -> subprocess.CompletedProcess:
    """Build with `-D spl_selection=<file>`, the way a build's own run does."""
    env = {**os.environ, "VARIANT": "Disco"}
    env.pop("SPHINX_BUILD_CONFIGURATION_FILE", None)
    return subprocess.run(
        [sys.executable, "-m", "sphinx", "-b", "html", "-D", f"spl_selection={selection}", str(PROJECT_ROOT), str(out_dir)],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_the_docs_shape_does_not_read_the_generated_report_pages(all_variant_data: None, tmp_path: Path, fake_build_dir: Path) -> None:
    """spl-core writes the report pages for both shapes; a docs build must not read them.

    They exist from configure time, and in a docs build the fences that would
    link them are false -- so reading them yields three documents per component
    that no toctree references. The docs shape's selection names no generated
    page, in the file ubCode reads as well, instead of a Sphinx-only filter.
    """
    build_dir = fake_build_dir
    rel = build_dir.relative_to(PROJECT_ROOT).as_posix()
    _fake_spl_core_report_tree(build_dir, "components/light_controller")
    selection = _selection_file(tmp_path, build_dir, "docs")

    out = tmp_path / "docs_html"
    result = _build_with_selection(selection, out)
    assert result.returncode == 0, (result.stdout + result.stderr)[-2000:]

    # Sphinx writes warnings to stderr, so scanning stdout alone made an
    # earlier version of this test pass with the fix reverted.
    log = result.stdout + result.stderr
    offenders = [line for line in log.splitlines() if rel in line and "WARNING" in line]
    assert not offenders, "the docs shape read the generated report pages:\n" + "\n".join(offenders)

    for page in SPL_CORE_REPORT_PAGES:
        built = out / rel / "components" / "light_controller" / "reports" / f"{page}.html"
        assert not built.is_file(), f"the docs shape built {page}"


def test_the_reports_shape_still_reads_them(all_variant_data: None, tmp_path: Path, fake_build_dir: Path) -> None:
    """The other half: keeping the docs shape clean must not starve the reports one.

    The report toctrees' globs have to match, or Sphinx reports an empty glob
    and the page links nothing at all.
    """
    build_dir = fake_build_dir
    rel = build_dir.relative_to(PROJECT_ROOT).as_posix()
    _fake_spl_core_report_tree(build_dir, "components/light_controller")
    selection = _selection_file(tmp_path, build_dir, "reports")

    out = tmp_path / "reports_html"
    result = _build_with_selection(selection, out)
    assert result.returncode == 0, (result.stdout + result.stderr)[-2000:]

    log = result.stdout + result.stderr
    unresolved = [line for line in log.splitlines() if "light_controller/reports" in line and ("nonexisting document" in line or "match any documents" in line)]
    assert not unresolved, "the report toctree did not resolve:\n" + "\n".join(unresolved)

    for page in SPL_CORE_REPORT_PAGES:
        assert (out / rel / "components" / "light_controller" / "reports" / f"{page}.html").is_file()
    assert (out / rel / "reports" / "coverage.html").is_file(), "the variant's coverage glob did not match"

    document = (out / "components" / "light_controller" / "doc" / "index.html").read_text(encoding="utf-8")
    for page in SPL_CORE_REPORT_PAGES:
        href = f"{rel}/components/light_controller/reports/{page}.html"
        assert href in document, f"the light_controller page does not link {page}"


# --- the generated listings must not show their Jinja armour ----------------


def test_generated_source_listings_carry_no_jinja_markers(all_variant_data: None, tmp_path: Path, fake_build_dir: Path) -> None:
    """spl-core wraps generated listings in `{% raw %}` unless this turns it off.

    The global Jinja pass used to consume those markers. It is gone, so the flag
    is what keeps them out: CMakeLists.txt sets SPL_SOURCE_DOCS_JINJA_RAW_TAGS
    OFF, and spl-core then invokes clanguru without `--jinja-raw-tags`. This
    generates the fixture the same way and builds it where spl-core puts it, so it
    tracks what the build actually emits rather than a hand-written idea of it.
    """
    cmake = (PROJECT_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    assert _cmake_set(cmake, "SPL_SOURCE_DOCS_JINJA_RAW_TAGS") == "OFF", "CMakeLists.txt must turn the raw-tag armour off"

    clanguru = shutil.which("clanguru") or str(Path(sys.executable).parent / "clanguru")
    if not Path(clanguru).exists():
        pytest.skip("clanguru not installed")

    source = tmp_path / "sample.c"
    source.write_text("int add(int a, int b) { return a + b; }\n", encoding="utf-8")

    build_dir = fake_build_dir
    component = "components/light_controller"
    _fake_spl_core_report_tree(build_dir, component)
    listing_dir = build_dir / component / "__source_docs"
    listing = listing_dir / "sample_c.rst"
    subprocess.run(
        [clanguru, "docs", "--source-file", str(source), "--output-file", str(listing), "--format", "rst"],
        check=True,
        capture_output=True,
    )
    assert "{% raw %}" not in listing.read_text(encoding="utf-8"), "this is not what spl-core generates with the raw-tag flag off"
    (listing_dir / "index.rst").write_text(
        "Source Files\n============\n\n.. toctree::\n   :maxdepth: 1\n\n   sample_c\n",
        encoding="utf-8",
    )

    selection = _selection_file(tmp_path, build_dir, "reports")
    out = tmp_path / "html"
    result = _build_with_selection(selection, out)
    assert result.returncode == 0, (result.stdout + result.stderr)[-2000:]

    page = out / build_dir.relative_to(PROJECT_ROOT) / component / "__source_docs" / "sample_c.html"
    assert page.is_file(), "the listing was not built"
    rendered = page.read_text(encoding="utf-8")
    for marker in ("{% raw %}", "{% endraw %}"):
        assert marker not in rendered, f"{marker} reached the reader"

    # Syntax highlighting splits the code across spans, so assert on the text
    # rather than the markup -- checking the raw HTML for a contiguous "int add"
    # is how an earlier version of this test fooled itself.
    text = re.sub(r"<[^>]+>", "", rendered)
    assert "int" in text and "add" in text, "the listing did not contain the code"
