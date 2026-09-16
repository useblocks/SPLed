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

import os
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
    assert result.returncode == 0, result.stdout[-2000:]

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
            text = path.read_text()
            if "{{" in text or "{%" in text:
                offenders.append(str(path.relative_to(PROJECT_ROOT)))
    assert not offenders, f"Jinja constructs in documents: {offenders}"


def test_conf_py_registers_no_source_read_handler() -> None:
    conf = (PROJECT_ROOT / "conf.py").read_text()
    assert "source-read" not in conf, "the global Jinja pass must not come back"
