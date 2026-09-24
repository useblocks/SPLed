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
"""

import ast
import contextlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

import variant_data  # noqa: E402

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


@pytest.fixture(scope="module")
def all_variant_data() -> None:
    """Generate the whole matrix once, the way a developer or CI would."""
    subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "tools" / "variant_data.py"), "--all"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
    )


def _select_cell(variant: str, kit: str, target: str) -> list[str]:
    """The sphinx-build option that selects one cell of the matrix.

    A command-line override of `needs_variant_data_file`, which sphinx-needs keeps
    even though needs_from_toml names the pointer. It is what spl-core passes for
    the shape it builds, and the key `ubc check -c` overrides as well.
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
    )


def test_variant_data_generates_for_every_variant(all_variant_data: None) -> None:
    """`--check` passes right after `--all`, so the two agree by construction."""
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "tools" / "variant_data.py"), "--all", "--check"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
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
    problems = [
        d
        for d in diagnostics
        if d["code"].startswith("config") and d["code"] != "config.variant_sources_sphinx_unsupported"
    ]
    assert not problems, "; ".join(f"{d['code']}: {d['message']}" for d in problems)


@needs_ubc
@pytest.mark.parametrize("variant", VARIANTS)
def test_ubc_excludes_exactly_what_sphinx_excludes(all_variant_data: None, variant: str) -> None:
    """The property the whole design exists to provide, proven across readers.

    ubCode never runs conf.py. If it removes exactly the component documents
    that the variant's component list omits -- the same set the Sphinx build
    omits, asserted above -- then both readers are deciding from the same data
    and agreeing. That is the claim; this is the test of it.
    """
    diagnostics = _ubc_check(variant, "test", "docs")

    excluded_by_ubc = set()
    for diagnostic in diagnostics:
        if diagnostic["code"] != "toctree.variant_excluded":
            continue
        match = re.search(r"toctree entry '([^']+)'", diagnostic["message"])
        assert match, diagnostic["message"]
        excluded_by_ubc.add(match.group(1))

    components = set(variant_data.components(PROJECT_ROOT, variant, "test"))
    expected = {
        f"{component}/doc/index" for component in COMPONENT_DOCS if component not in components
    }

    assert excluded_by_ubc == expected, (
        f"{variant}: ubCode and the component list disagree.\n"
        f"  ubCode excluded : {sorted(excluded_by_ubc)}\n"
        f"  expected        : {sorted(expected)}"
    )


# --- the build shape must select its own cell -------------------------------


def _build_with_spl_core_env(shape: str, out_dir: Path, tmp_path: Path, config: dict | None = None) -> subprocess.CompletedProcess:
    """Build the way spl-core starts Sphinx, environment and options.

    spl-core names the per-target config.json in SPHINX_BUILD_CONFIGURATION_FILE
    and selects the variant data cell for the shape with
    `-D needs_variant_data_file=`, which CMakeLists.txt configures through
    SPL_VARIANT_DATA_FILE_DOCS and _REPORTS. The cell is what the
    `{if} var.build_config.target` fences evaluate against.
    """
    config_dir = tmp_path / "cfg" / shape
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.json").write_text(json.dumps(config or {}), encoding="utf-8")

    env = {
        **os.environ,
        "SPHINX_BUILD_CONFIGURATION_FILE": str(config_dir / "config.json"),
        "VARIANT": "Disco",
    }
    return subprocess.run(
        [sys.executable, "-m", "sphinx", "-b", "html", *_select_cell("Disco", "test", shape), str(PROJECT_ROOT), str(out_dir)],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


def _cmake_set(cmake: str, variable: str) -> str:
    """The value of a `set(VARIABLE ...)` call, whitespace-tolerant."""
    match = re.search(rf"set\(\s*{re.escape(variable)}\s+(.*?)\s*\)", cmake, flags=re.DOTALL)
    assert match, f"CMakeLists.txt does not set {variable}"
    return match.group(1).strip()


def test_cmake_passes_spl_core_the_cell_for_each_shape() -> None:
    """The helper mirrors a contract that lives in CMakeLists.txt.

    If the helper and the CMake configuration disagree, the tests would prove
    the behaviour of an environment spl-core never builds in. This reads the
    `set(...)` calls rather than searching for the variable name, so a stray
    mention in a comment cannot satisfy it.
    """
    cmake = (PROJECT_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    expected = {
        "SPL_VARIANT_DATA_FILE_DOCS": "${CMAKE_SOURCE_DIR}/build/variants/${VARIANT}/${BUILD_KIT}/docs.json",
        "SPL_VARIANT_DATA_FILE_REPORTS": "${CMAKE_SOURCE_DIR}/build/variants/${VARIANT}/${BUILD_KIT}/reports.json",
    }
    for variable, value in expected.items():
        assert _cmake_set(cmake, variable) == value, f"CMakeLists.txt must pass {variable}={value}"


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
        result = _build_with_spl_core_env(shape, out, tmp_path)
        assert result.returncode == 0, (result.stdout + result.stderr)[-2000:]
        page = (out / "components" / "light_controller" / "doc" / "index.html").read_text(encoding="utf-8")
        assert ("Verification" in page) is expect_verification, (
            f"the {shape} shape {'should' if expect_verification else 'should not'} render the verification section"
        )


# --- the generated report pages --------------------------------------------


#: The three pages spl-core writes per component at CONFIGURE time, and lists
#: among its include patterns for BOTH build shapes.
SPL_CORE_REPORT_PAGES = ("unit_test_spec", "unit_test_results", "coverage")

#: A fake build directory the `generated` link is pointed at for the duration of
#: a test. It is gitignored and pruned from the Sphinx walk, so the only route
#: to it is `generated` -- which is exactly the route under test.
FAKE_GENERATED_BUILD = PROJECT_ROOT / "build" / "_test_generated_build"


def _link(link: Path, target: Path) -> None:
    """Create `generated` the way tools/variant_data.py does: a symlink, or a junction where Windows refuses one."""
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        variant_data._create_junction(target, link)


@contextlib.contextmanager
def _generated_points_at(fake_build: Path):
    """Point `generated` at a fake build, then point it back where it was.

    Several tests need `generated` to lead somewhere the real build is not, so
    they can assert on pages the real build does not contain. The link is
    restored on the way out whatever happens, because leaving a developer's
    pointer re-pointed at a removed test directory would break their next build
    in a way they did not cause. It never calls variant_data.write_pointer:
    that would overwrite build/autoconf.json, which belongs to the developer.
    """
    generated = PROJECT_ROOT / "generated"
    if generated.is_symlink() or generated.is_junction():
        # A junction's target can come back in the \\?\ form, which a new
        # junction cannot be created from.
        original: tuple[str, str | None] = ("link", os.readlink(generated).removeprefix("\\\\?\\"))
    elif generated.is_dir():
        # A plain directory only ever holds the explanation variant_data.py
        # writes when neither a symlink nor a junction could be created.
        marker = generated / "NO_SYMLINK"
        original = ("directory", marker.read_text(encoding="utf-8") if marker.is_file() else None)
    else:
        original = ("absent", None)

    variant_data._remove_link(generated)
    shutil.rmtree(fake_build, ignore_errors=True)
    fake_build.mkdir(parents=True, exist_ok=True)
    _link(generated, fake_build)

    try:
        yield generated
    finally:
        variant_data._remove_link(generated)
        if original[0] == "link":
            _link(generated, Path(original[1]))
        elif original[0] == "directory":
            generated.mkdir(parents=True, exist_ok=True)
            if original[1] is not None:
                (generated / "NO_SYMLINK").write_text(original[1], encoding="utf-8")
        shutil.rmtree(fake_build, ignore_errors=True)


def _fake_spl_core_report_tree(component: str) -> str:
    """Write what spl-core's configure step writes, and the pattern naming it.

    `component` is a path such as `components/light_controller`, so the pages
    land where spl-core writes them and the returned include pattern is the
    `generated/...` name it now passes for both build shapes.
    """
    root = FAKE_GENERATED_BUILD / component / "reports"
    root.mkdir(parents=True, exist_ok=True)
    for page in SPL_CORE_REPORT_PAGES:
        (root / f"{page}.rst").write_text(
            f"{page}\n{'=' * len(page)}\n\nGenerated by spl-core at configure time.\n",
            encoding="utf-8",
        )
    return f"generated/{component}/reports/**"


def test_the_docs_shape_does_not_read_the_generated_report_pages(all_variant_data: None, tmp_path: Path) -> None:
    """spl-core lists the report pages for both shapes; the variant rule keeps
    them out of a docs build.

    They exist from configure time, and in a docs build the fences that would
    link them are false -- so reading them yields three documents per component
    that no toctree references. The `if = 'var.build_config.target == "reports"'`
    rule over `generated/**` in ubproject.toml is what removes them now, declared
    once where ubCode reads it too, instead of a Sphinx-only filter.

    This needs no compiler: the only thing a CMake build contributes here is the
    config.json, and that is three lines of JSON.
    """
    with _generated_points_at(FAKE_GENERATED_BUILD):
        pattern = _fake_spl_core_report_tree("components/light_controller")
        out = tmp_path / "docs_html"
        result = _build_with_spl_core_env("docs", out, tmp_path, {"target": "docs", "include_patterns": [pattern]})
        assert result.returncode == 0, (result.stdout + result.stderr)[-2000:]

        # Sphinx writes warnings to stderr, so scanning stdout alone made an
        # earlier version of this test pass with the fix reverted.
        log = result.stdout + result.stderr
        offenders = [line for line in log.splitlines() if "generated/" in line and "WARNING" in line]
        assert not offenders, "the docs shape read the generated report pages:\n" + "\n".join(offenders)

        for page in SPL_CORE_REPORT_PAGES:
            built = out / "generated" / "components" / "light_controller" / "reports" / f"{page}.html"
            assert not built.is_file(), f"the docs shape built {page}"


def test_the_reports_shape_still_reads_them(all_variant_data: None, tmp_path: Path) -> None:
    """The other half: keeping the docs shape clean must not starve the reports one.

    The fixed `/generated/...` toctree names have to resolve, or Sphinx reports
    a nonexisting document and the page links nothing at all.
    """
    with _generated_points_at(FAKE_GENERATED_BUILD):
        pattern = _fake_spl_core_report_tree("components/light_controller")
        out = tmp_path / "reports_html"
        result = _build_with_spl_core_env("reports", out, tmp_path, {"target": "reports", "include_patterns": [pattern]})
        assert result.returncode == 0, (result.stdout + result.stderr)[-2000:]

        log = result.stdout + result.stderr
        unresolved = [
            line
            for line in log.splitlines()
            if "nonexisting document" in line and "generated/components/light_controller/reports" in line
        ]
        assert not unresolved, "the report toctree did not resolve:\n" + "\n".join(unresolved)

        for page in SPL_CORE_REPORT_PAGES:
            assert (out / "generated" / "components" / "light_controller" / "reports" / f"{page}.html").is_file()

        document = (out / "components" / "light_controller" / "doc" / "index.html").read_text(encoding="utf-8")
        for page in SPL_CORE_REPORT_PAGES:
            href = f"generated/components/light_controller/reports/{page}.html"
            assert href in document, f"the light_controller page does not link {page}"


# --- the generated listings must not show their Jinja armour ----------------


def test_generated_source_listings_carry_no_jinja_markers(all_variant_data: None, tmp_path: Path) -> None:
    """spl-core wraps generated listings in `{% raw %}` unless this turns it off.

    The global Jinja pass used to consume those markers. It is gone, so the flag
    is what keeps them out: CMakeLists.txt sets SPL_SOURCE_DOCS_JINJA_RAW_TAGS
    OFF, and spl-core then invokes clanguru without `--jinja-raw-tags`. This
    generates the fixture the same way and builds it, so it tracks what the
    build actually emits rather than a hand-written idea of it.
    """
    cmake = (PROJECT_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    assert _cmake_set(cmake, "SPL_SOURCE_DOCS_JINJA_RAW_TAGS") == "OFF", (
        "CMakeLists.txt must turn the raw-tag armour off"
    )

    clanguru = shutil.which("clanguru") or str(Path(sys.executable).parent / "clanguru")
    if not Path(clanguru).exists():
        pytest.skip("clanguru not installed")

    source = tmp_path / "sample.c"
    source.write_text("int add(int a, int b) { return a + b; }\n", encoding="utf-8")

    with _generated_points_at(FAKE_GENERATED_BUILD):
        component = "components/light_controller"
        listing_dir = FAKE_GENERATED_BUILD / component / "__source_docs"
        listing_dir.mkdir(parents=True, exist_ok=True)
        listing = listing_dir / "sample_c.rst"
        subprocess.run(
            [clanguru, "docs", "--source-file", str(source), "--output-file", str(listing), "--format", "rst"],
            check=True,
            capture_output=True,
        )
        assert "{% raw %}" not in listing.read_text(encoding="utf-8"), (
            "this is not what spl-core generates with the raw-tag flag off"
        )
        (listing_dir / "index.rst").write_text(
            "Source Files\n============\n\n.. toctree::\n   :maxdepth: 1\n\n   sample_c\n",
            encoding="utf-8",
        )

        pattern = f"generated/{component}/__source_docs/**"
        out = tmp_path / "html"
        result = _build_with_spl_core_env("reports", out, tmp_path, {"target": "reports", "include_patterns": [pattern]})
        assert result.returncode == 0, (result.stdout + result.stderr)[-2000:]

        page = out / "generated" / component / "__source_docs" / "sample_c.html"
        assert page.is_file(), "the listing was not built"
        rendered = page.read_text(encoding="utf-8")
        for marker in ("{% raw %}", "{% endraw %}"):
            assert marker not in rendered, f"{marker} reached the reader"

        # Syntax highlighting splits the code across spans, so assert on the
        # text rather than the markup -- checking the raw HTML for a contiguous
        # "int add" is how an earlier version of this test fooled itself.
        text = re.sub(r"<[^>]+>", "", rendered)
        assert "int" in text and "add" in text, "the listing did not contain the code"
