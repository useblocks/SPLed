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
