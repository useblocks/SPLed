"""Tests for ubproject.toml, the one configuration file both readers read.

ubCode and ubc read this file directly; the Sphinx build reads it through
`needs_from_toml` in conf.py. sphinx-needs implements neither ubCode's `extend`
nor any other include mechanism -- it reads exactly one file's `[needs]` table --
so the only way the two readers can agree is for this file to be complete on its
own. spl-core's base needs configuration is therefore vendored into it.

Vendoring is a copy, and a copy rots. These tests are what stops it rotting
quietly: they fail when spl-core changes something this project copied, so the
choice to follow or to deviate is made deliberately, in a reviewable commit,
rather than discovered later as a link type that exists in one reader and not
the other.
"""

import tomllib
from importlib.resources import files
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

pytestmark = [
    pytest.mark.unittests,
    pytest.mark.gate_develop_pr,
    pytest.mark.gate_develop_push,
    pytest.mark.gate_develop_nightly,
    pytest.mark.gate_release_pr,
    pytest.mark.gate_release,
]


@pytest.fixture(scope="module")
def project_config() -> dict:
    with (PROJECT_ROOT / "ubproject.toml").open("rb") as handle:
        return tomllib.load(handle)


@pytest.fixture(scope="module")
def spl_core_config() -> dict:
    """The base configuration spl-core ships, as installed."""
    with files("spl_core.report_generation").joinpath("ubproject.toml").open("rb") as handle:
        return tomllib.load(handle)


# --- the file has to stand on its own --------------------------------------


def test_does_not_extend_anything(project_config: dict) -> None:
    """No `extend`, because only one of the two readers implements it.

    The path it used to name also had the Python minor version baked into it
    and pointed at an interpreter that does not exist, so the base
    configuration silently failed to resolve for ubCode while conf.py resolved
    it a second time through importlib.
    """
    assert "extend" not in project_config


def test_sphinx_reads_this_exact_file() -> None:
    conf = (PROJECT_ROOT / "conf.py").read_text()
    assert 'needs_from_toml = "ubproject.toml"' in conf


# --- the vendored copy has to match what spl-core ships --------------------


def test_every_spl_core_link_type_is_vendored(project_config: dict, spl_core_config: dict) -> None:
    """Modernized from `extra_links` to `[needs.links]` while copying."""
    expected = {
        link["option"]: {"incoming": link["incoming"], "outgoing": link["outgoing"]}
        for link in spl_core_config["needs"]["extra_links"]
    }
    assert project_config["needs"]["links"] == expected


def test_every_spl_core_field_is_vendored(project_config: dict, spl_core_config: dict) -> None:
    """Modernized from `extra_options` to `[needs.fields]` while copying.

    The project declares fields of its own on top, so this is a subset check.
    `integrity` carries an explicit empty-string default because that is what
    the deprecated `extra_options` form implies; defaulting to null instead
    would change the value on every existing need.
    """
    for option in spl_core_config["needs"]["extra_options"]:
        assert option in project_config["needs"]["fields"], f"spl-core declares the field {option!r}, this file does not"

    assert project_config["needs"]["fields"]["integrity"]["default"] == ""


def test_every_spl_core_need_type_is_vendored(project_config: dict, spl_core_config: dict) -> None:
    ours = {t["directive"]: t for t in project_config["needs"]["types"]}
    for need_type in spl_core_config["needs"]["types"]:
        directive = need_type["directive"]
        assert directive in ours, f"spl-core declares the need type {directive!r}, this file does not"
        assert ours[directive] == need_type, f"the {directive!r} need type differs from spl-core's"


def test_source_exclusions_are_vendored(project_config: dict, spl_core_config: dict) -> None:
    assert project_config["source"]["exclude"] == spl_core_config["source"]["exclude"]
    assert project_config["source"]["respect_gitignore"] == spl_core_config["source"]["respect_gitignore"]


# --- the deliberate deviations ---------------------------------------------


def test_build_output_is_not_indexed(project_config: dict) -> None:
    """ubCode must not index every variant and kit ever built.

    spl-core's base config turns `respect_gitignore` off and then includes the
    generated source listings, but excludes nothing else under the build
    directory. The result is every need ID appearing once per variant built on
    that machine, so the IDE cannot agree with any single build about what the
    project contains. Sphinx never saw this because conf.py narrows its source
    set per build shape -- which is exactly the kind of divergence between
    readers this configuration exists to remove.
    """
    assert project_config["source"]["extend_exclude"] == ["build/**"]


def test_generated_listings_are_included_through_the_stable_path(project_config: dict, spl_core_config: dict) -> None:
    """A deliberate deviation from spl-core's `build/**/__source_docs/**`.

    `generated` is the current variant's build directory, maintained by
    tools/variant_data.py. Going through it means one variant's listings are
    indexed -- the configured one -- instead of all of them, and it survives the
    `build/**` exclusion above.
    """
    assert spl_core_config["source"]["extend_include"] == ["build/**/__source_docs/**"]
    assert project_config["source"]["extend_include"] == ["generated/**/__source_docs/**"]


# --- what the variant machinery needs --------------------------------------


def test_variant_data_file_is_the_current_pointer(project_config: dict) -> None:
    """What ubCode reads, and what a bare sphinx-build falls back to."""
    assert project_config["needs"]["variant_data_file"] == "build/autoconf.json"


def test_needs_json_is_written(project_config: dict) -> None:
    assert project_config["needs"]["build_json"] is True


# --- the variant rules -----------------------------------------------------
#
# These evaluate the real conditions with sphinx-mounts' own interpreter,
# against the real generated variant data. That is the closest a test can get
# to "ubCode and the build decide the same thing", because it is literally the
# same grammar and the same file.


@pytest.fixture(scope="module")
def rules(project_config: dict) -> list[dict]:
    return project_config["source"]["variant_sources"]


def _variant_data(variant: str, kit: str, target: str) -> dict:
    import json

    with (PROJECT_ROOT / "build" / "variants" / variant / kit / f"{target}.json").open() as handle:
        return json.load(handle)


def test_every_component_document_is_gated_by_a_rule(rules: list[dict]) -> None:
    """A hand-written component document with no rule is 150% in every variant.

    It would then appear in variants that do not contain the component, and
    every need in it would enter their traceability data. The failure is
    additive and silent, which is why it needs a test rather than a review.
    """
    gated = {pattern for rule in rules for pattern in rule["files"]}
    for doc_dir in sorted(PROJECT_ROOT.glob("components/**/doc")) + sorted(PROJECT_ROOT.glob("test/*/doc")):
        rel = doc_dir.relative_to(PROJECT_ROOT).as_posix()
        assert f"{rel}/**" in gated, f"{rel} is not gated by any [[source.variant_sources]] rule"


def test_no_rule_names_a_variant_by_name(rules: list[dict]) -> None:
    """Membership, never identity.

    Gating on the variant name re-encodes what parts.cmake already says, and
    the two are then free to drift. The integration suite is the case in point:
    it used to be gated on `variant == "Disco"`, which also claimed it for
    Disco's prod kit, where parts.cmake does not add it.
    """
    known_variants = {"Disco", "Sleep", "Spa", "Base/Dev", "IDEA/Sloemada"}
    for rule in rules:
        for variant in known_variants:
            assert f'"{variant}"' not in rule["if"], f"rule {rule['if']!r} names a variant directly"
            assert f"'{variant}'" not in rule["if"], f"rule {rule['if']!r} names a variant directly"


def test_every_rule_condition_is_inside_the_grammar(rules: list[dict]) -> None:
    """A condition outside the grammar is refused rather than evaluated."""
    from sphinx_mounts import variants

    for rule in rules:
        variants.validate(rule["if"])


@pytest.mark.parametrize(
    ("variant", "kit", "expect_present", "expect_absent"),
    [
        # Disco: BLINKING, so no brightness; no auto-off; integration suite in
        # the test kit only.
        ("Disco", "test", ["components/light_controller/doc/**", "test/spled_integration/doc/**"], ["components/auto_off/doc/**", "components/brightness_controller/doc/**"]),
        ("Disco", "prod", ["components/light_controller/doc/**"], ["test/spled_integration/doc/**", "components/auto_off/doc/**"]),
        # Sleep: manual brightness and auto-off, no integration suite.
        ("Sleep", "test", ["components/auto_off/doc/**", "components/brightness_controller/doc/**"], ["test/spled_integration/doc/**"]),
        # Spa: brightness but no auto-off.
        ("Spa", "test", ["components/brightness_controller/doc/**"], ["components/auto_off/doc/**"]),
        # Base/Dev: the example components, none of the product ones.
        ("Base/Dev", "test", ["components/examples/hello_gmock/doc/**"], ["components/light_controller/doc/**", "components/auto_off/doc/**"]),
    ],
)
def test_rules_select_the_expected_documents(rules: list[dict], variant: str, kit: str, expect_present: list[str], expect_absent: list[str]) -> None:
    from sphinx_mounts import variants

    data = _variant_data(variant, kit, "docs")
    included: set[str] = set()
    excluded: set[str] = set()
    for rule in rules:
        ok = variants.interpret(variants.validate(rule["if"]), data)
        (included if ok else excluded).update(rule["files"])

    for pattern in expect_present:
        assert pattern in included, f"{variant}/{kit}: expected {pattern} to be included"
        assert pattern not in excluded, f"{variant}/{kit}: {pattern} is both included and excluded"
    for pattern in expect_absent:
        assert pattern in excluded, f"{variant}/{kit}: expected {pattern} to be excluded"


def test_generated_output_is_gated_on_the_reports_target(rules: list[dict]) -> None:
    """A docs build must not read report pages it will not show.

    Rules are subtractive -- a FALSE rule removes the files it names, a TRUE
    one does nothing -- so this rule and the per-component ones compose as AND.
    """
    from sphinx_mounts import variants

    shape_rule = next(r for r in rules if "target" in r["if"])
    assert shape_rule["files"] == ["generated/**"]

    tree = variants.validate(shape_rule["if"])
    assert variants.interpret(tree, _variant_data("Disco", "test", "reports")) is True
    assert variants.interpret(tree, _variant_data("Disco", "test", "docs")) is False


def test_no_document_globs_the_build_directory() -> None:
    """Toctrees name `generated/`, the configured variant's build directory.

    A `/build/**` glob matched every variant and build type on disk and only
    ever resolved to one page because conf.py narrowed the source set behind
    the scenes -- an invisible gate holding up a visible one.
    """
    for pattern in ("components/*/doc/index.md", "components/*/*/doc/index.md", "test/*/doc/index.md"):
        for path in PROJECT_ROOT.glob(pattern):
            assert "/build/**" not in path.read_text(), f"{path.relative_to(PROJECT_ROOT)} still globs the build directory"
    assert "/build/**" not in (PROJECT_ROOT / "index.md").read_text()
