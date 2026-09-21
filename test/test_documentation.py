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


def _build_docs(variant: str, kit: str, target: str, out_dir: Path) -> subprocess.CompletedProcess:
    env = {
        **os.environ,
        "VARIANT_DATA_FILE": str(PROJECT_ROOT / "build" / "variants" / variant / kit / f"{target}.json"),
        "VARIANT": variant,
    }
    # Deliberately NOT inheriting SPHINX_BUILD_CONFIGURATION_FILE: this gate is
    # the bare build, the one a reader with no CMake in sight performs.
    env.pop("SPHINX_BUILD_CONFIGURATION_FILE", None)
    return subprocess.run(
        [sys.executable, "-m", "sphinx", "-b", "html", str(PROJECT_ROOT), str(out_dir)],
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


def test_the_only_source_read_handler_is_the_scoped_marker_strip() -> None:
    """The rule is "no templating of documents", not "no handler at all".

    conf.py does register one `source-read` handler: a line filter that blanks
    the `{% raw %}` markers spl-core puts in generated listings, scoped to
    docnames under __source_docs. That is categorically different from the
    global Jinja pass this branch removed -- nothing is evaluated and no
    hand-written document is seen -- so this asserts the shape rather than the
    absence of a string.
    """
    conf = (PROJECT_ROOT / "conf.py").read_text(encoding="utf-8")

    handlers = re.findall(r'app\.connect\(\s*"source-read"\s*,\s*([A-Za-z_][A-Za-z0-9_]*)', conf)
    assert handlers == ["_strip_jinja_raw_markers"], f"unexpected source-read handlers: {handlers}"

    # The pass that rendered every document is gone and stays gone.
    assert "render_string" not in conf, "the global Jinja pass must not come back"
    assert "__source_docs" in conf, "the handler must stay scoped to generated listings"


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
    """Build the way spl-core starts Sphinx: a per-target config.json, no more.

    spl-core only passes VARIANT_DATA_FILE from 8.9; against the version this
    project pins it passes SPHINX_BUILD_CONFIGURATION_FILE, and the directory
    that file sits in is what names the build shape.
    """
    config_dir = tmp_path / "cfg" / shape
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.json").write_text(json.dumps(config or {}), encoding="utf-8")

    env = {**os.environ, "SPHINX_BUILD_CONFIGURATION_FILE": str(config_dir / "config.json"), "VARIANT": "Disco"}
    env.pop("VARIANT_DATA_FILE", None)
    return subprocess.run(
        [sys.executable, "-m", "sphinx", "-b", "html", str(PROJECT_ROOT), str(out_dir)],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


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
    published = {
        "reports": PROJECT_ROOT / "build" / "variant-data-reports.json",
        "docs": PROJECT_ROOT / "build" / "variant-data-docs.json",
    }
    for shape, path in published.items():
        path.write_text((PROJECT_ROOT / "build" / "variants" / "Disco" / "test" / f"{shape}.json").read_text(encoding="utf-8"))

    try:
        for shape, expect_verification in (("reports", True), ("docs", False)):
            out = tmp_path / f"{shape}_html"
            result = _build_with_spl_core_env(shape, out, tmp_path)
            assert result.returncode == 0, (result.stdout + result.stderr)[-2000:]
            page = (out / "components" / "light_controller" / "doc" / "index.html").read_text(encoding="utf-8")
            assert ("Verification" in page) is expect_verification, (
                f"the {shape} shape {'should' if expect_verification else 'should not'} render the verification section"
            )
    finally:
        for path in published.values():
            path.unlink(missing_ok=True)


# --- the generated report pages belong to the reports shape only ------------


#: The three pages spl-core writes per component at CONFIGURE time, and lists
#: among its include patterns for BOTH build shapes.
SPL_CORE_REPORT_PAGES = ("unit_test_spec", "unit_test_results", "coverage")


def _fake_spl_core_report_tree(component: str) -> tuple[Path, str]:
    """Write what spl-core's configure step writes, and the pattern naming it.

    Under build/, so it is gitignored and invisible to every other test.
    """
    rel = Path("build") / "_fake_report_tree" / component / "reports"
    root = PROJECT_ROOT / rel
    root.mkdir(parents=True, exist_ok=True)
    for page in SPL_CORE_REPORT_PAGES:
        (root / f"{page}.rst").write_text(
            f"{page}\n{'=' * len(page)}\n\nGenerated by spl-core at configure time.\n",
            encoding="utf-8",
        )
    return root, f"{rel.as_posix()}/**"


def test_the_docs_shape_does_not_read_the_generated_report_pages(all_variant_data: None, tmp_path: Path) -> None:
    """spl-core lists the report pages for both shapes; only one should read them.

    They exist from configure time, and in a docs build the fences that would
    link them are false -- so reading them yields three documents per component
    that no toctree references. Fifteen orphan warnings on Spa, for pages nobody
    asked to see.

    This needs no compiler: the only thing a CMake build contributes here is the
    config.json, and that is three lines of JSON.
    """
    published = PROJECT_ROOT / "build" / "variant-data-docs.json"
    published.write_text(
        (PROJECT_ROOT / "build" / "variants" / "Disco" / "test" / "docs.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    tree, pattern = _fake_spl_core_report_tree("components/light_controller")

    try:
        out = tmp_path / "docs_html"
        result = _build_with_spl_core_env("docs", out, tmp_path, {"target": "docs", "include_patterns": [pattern]})
        assert result.returncode == 0, (result.stdout + result.stderr)[-2000:]

        # Sphinx writes warnings to stderr, so scanning stdout alone made an
        # earlier version of this test pass with the fix reverted.
        orphaned = [
            line
            for line in (result.stdout + result.stderr).splitlines()
            if "toc.not_included" in line and "_fake_report_tree" in line
        ]
        assert not orphaned, "the docs shape read the generated report pages:\n" + "\n".join(orphaned)
    finally:
        shutil.rmtree(tree.parent.parent, ignore_errors=True)
        published.unlink(missing_ok=True)


def test_the_reports_shape_still_reads_them(all_variant_data: None, tmp_path: Path) -> None:
    """The other half: narrowing the docs shape must not starve the reports one."""
    published = PROJECT_ROOT / "build" / "variant-data-reports.json"
    published.write_text(
        (PROJECT_ROOT / "build" / "variants" / "Disco" / "test" / "reports.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    tree, pattern = _fake_spl_core_report_tree("components/light_controller")

    try:
        out = tmp_path / "reports_html"
        result = _build_with_spl_core_env("reports", out, tmp_path, {"target": "reports", "include_patterns": [pattern]})
        assert result.returncode == 0, (result.stdout + result.stderr)[-2000:]

        built = out / "build" / "_fake_report_tree" / "components" / "light_controller" / "reports"
        for page in SPL_CORE_REPORT_PAGES:
            assert (built / f"{page}.html").is_file(), f"the reports shape did not read {page}"
    finally:
        shutil.rmtree(tree.parent.parent, ignore_errors=True)
        published.unlink(missing_ok=True)


# --- the generated listings must not show their Jinja armour ----------------


def test_generated_source_listings_carry_no_jinja_markers(all_variant_data: None, tmp_path: Path) -> None:
    """spl-core wraps generated listings in `{% raw %}`; nothing else unwraps them.

    The global Jinja pass used to consume those markers. It is gone, and no
    released spl-core lets the flag be turned off, so without the scoped strip
    in conf.py they reach the reader as two literal paragraphs on every listing
    page of a reports build.

    The fixture is produced by clanguru itself rather than hand-written, so this
    tracks what spl-core actually emits instead of what it emitted once.
    """
    clanguru = shutil.which("clanguru") or str(Path(sys.executable).parent / "clanguru")
    if not Path(clanguru).exists():
        pytest.skip("clanguru not installed")

    source = tmp_path / "sample.c"
    source.write_text("int add(int a, int b) { return a + b; }\n", encoding="utf-8")

    listing_dir = PROJECT_ROOT / "build" / "_fake_source_docs" / "components" / "x" / "__source_docs"
    listing_dir.mkdir(parents=True, exist_ok=True)
    listing = listing_dir / "sample_c.rst"
    subprocess.run(
        [clanguru, "docs", "--source-file", str(source), "--output-file", str(listing),
         "--format", "rst", "--jinja-raw-tags"],
        check=True, capture_output=True,
    )
    assert "{% raw %}" in listing.read_text(encoding="utf-8"), "fixture is not representative"

    published = PROJECT_ROOT / "build" / "variant-data-reports.json"
    published.write_text(
        (PROJECT_ROOT / "build" / "variants" / "Disco" / "test" / "reports.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    pattern = "build/_fake_source_docs/components/x/__source_docs/**"

    try:
        out = tmp_path / "html"
        result = _build_with_spl_core_env(
            "reports", out, tmp_path, {"target": "reports", "include_patterns": [pattern]}
        )
        assert result.returncode == 0, (result.stdout + result.stderr)[-2000:]

        page = out / "build" / "_fake_source_docs" / "components" / "x" / "__source_docs" / "sample_c.html"
        assert page.is_file(), "the listing was not built"
        rendered = page.read_text(encoding="utf-8")
        for marker in ("{% raw %}", "{% endraw %}"):
            assert marker not in rendered, f"{marker} reached the reader"

        # Syntax highlighting splits the code across spans, so assert on the
        # text rather than the markup -- checking the raw HTML for a contiguous
        # "int add" is how an earlier version of this test fooled itself.
        text = re.sub(r"<[^>]+>", "", rendered)
        assert "int" in text and "add" in text, "the strip removed more than the markers"
    finally:
        shutil.rmtree(listing_dir.parent.parent.parent, ignore_errors=True)
        published.unlink(missing_ok=True)


def test_the_strip_preserves_line_numbers(all_variant_data: None) -> None:
    """Markers become blank lines, not nothing.

    Removing them would shift every line after them, so a warning about a
    generated page would point at the wrong line -- which is one of the reasons
    the global Jinja pass had to go. Re-creating it in the replacement would be
    missing the point.
    """
    spec = __import__("importlib.util", fromlist=["util"]).spec_from_file_location(
        "spled_conf", PROJECT_ROOT / "conf.py"
    )
    module = __import__("importlib.util", fromlist=["util"]).module_from_spec(spec)
    spec.loader.exec_module(module)

    before = "a\n{% raw %}\n.. code-block:: c\n\n   int x;\n{% endraw %}\n"
    source = [before]
    module._strip_jinja_raw_markers(None, "components/x/__source_docs/y", source)

    assert source[0].count("\n") == before.count("\n"), "line count changed"
    assert "{% raw %}" not in source[0] and "{% endraw %}" not in source[0]
    assert ".. code-block:: c" in source[0] and "int x;" in source[0]

    # A hand-written document is never touched, whatever it contains.
    untouched = ["{% raw %}\nkeep me\n"]
    module._strip_jinja_raw_markers(None, "doc/components/index", untouched)
    assert untouched[0] == "{% raw %}\nkeep me\n"
