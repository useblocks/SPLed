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

import json
import os
import re
import runpy
import subprocess
import sys
import tomllib
from importlib.resources import files
from pathlib import Path

import pytest
from sphinx.util.matching import Matcher

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
    conf = (PROJECT_ROOT / "conf.py").read_text(encoding="utf-8")
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
    assert "build/**" in project_config["source"]["extend_exclude"]


def test_the_per_component_report_root_is_hidden_from_ubcode(project_config: dict) -> None:
    """conf.py excludes it from every variant build, so ubCode must too.

    doc/component_report.md is the root document of spl-core's PER-COMPONENT
    report -- a build shape ubCode never performs. conf.py drops it from the
    variant-wide source set, so Sphinx never sees it; ubCode indexed it anyway
    and reported it as an orphan. Four orphans in one reader and five in the
    other is the two of them disagreeing about the document set, which is the
    one thing this configuration exists to prevent.

    `[parse.parsers.*]` has no `exclude`, but `extend_exclude` is honoured in
    parser mode -- unlike `extend_include` -- so that is where it belongs.
    """
    conf = (PROJECT_ROOT / "conf.py").read_text(encoding="utf-8")
    assert 'exclude_patterns.append("doc/component_report.md")' in conf
    assert "doc/component_report.md" in project_config["source"]["extend_exclude"]


def test_extend_include_is_not_used_because_it_would_be_inert(project_config: dict, spl_core_config: dict) -> None:
    """Configuring parsers puts ubCode in parser mode, where this key is ignored.

    spl-core's base config includes the generated listings with
    `[source] extend_include`, which works only while no parser is configured.
    This project configures both parsers, so file discovery comes from their
    `include` lists and `extend_include` does nothing -- silently, apart from
    one config warning. Carrying the key anyway would look like configuration
    and behave like a comment. `ubc check` is what caught this.
    """
    assert spl_core_config["source"]["extend_include"] == ["build/**/__source_docs/**"]
    assert "extend_include" not in project_config["source"]
    assert project_config["parse"]["parsers"]["rst"]["include"] == ["generated/**/*.rst"]


def test_ubcode_and_sphinx_see_the_same_documents(project_config: dict) -> None:
    """The parser includes have to match conf.py's include_patterns.

    They did not: `include = ["*.md"]` matched every Markdown file in the tree,
    so ubCode parsed AGENTS.md, README.md, CLAUDE.md and three dozen agent skill
    definitions as project documents -- 38 files Sphinx never sees. Two readers
    with different document sets cannot agree about the project, which is the
    whole thing this configuration exists to prevent.
    """
    conf = (PROJECT_ROOT / "conf.py").read_text(encoding="utf-8")
    markdown_includes = project_config["parse"]["parsers"]["md"]["include"]

    assert markdown_includes == [
        "index.md",
        "doc/**/*.md",
        "components/**/doc/**/*.md",
        "test/**/doc/**/*.md",
    ]
    # Every tree the parser reads is a tree conf.py also names.
    for tree in ("index.md", "doc/**", "components/**/doc/**", "test/**/doc/**"):
        assert f'"{tree}"' in conf, f"conf.py does not include {tree}, which the md parser reads"


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


@pytest.fixture(scope="module", autouse=True)
def generated_variant_data() -> None:
    """Generate the matrix before reading it.

    build/ is gitignored, so on a fresh checkout -- which is every CI run --
    these files do not exist yet. Reading them without generating them made
    these tests pass only on a machine that had happened to build already.
    """
    subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "tools" / "variant_data.py"), "--all"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
    )


def _variant_data(variant: str, kit: str, target: str) -> dict:
    with (PROJECT_ROOT / "build" / "variants" / variant / kit / f"{target}.json").open(encoding="utf-8") as handle:
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


#: The report pages spl-core writes per component, and the names a report
#: toctree has to use for them.
REPORT_PAGES = ("unit_test_spec", "unit_test_results", "coverage")


def _toctrees(text: str) -> list[tuple[list[str], list[str]]]:
    """The (options, entries) of every `{toctree}` block in a MyST document."""
    blocks: list[tuple[list[str], list[str]]] = []
    in_block = False
    options: list[str] = []
    entries: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```{toctree}"):
            in_block = True
            options, entries = [], []
            continue
        if in_block and stripped == "```":
            in_block = False
            blocks.append((options, entries))
            continue
        if not in_block or not stripped:
            continue
        (options if stripped.startswith(":") else entries).append(stripped)
    return blocks


def _component_path(document: Path) -> str | None:
    """`components/light_controller/doc/index.md` -> `components/light_controller`."""
    relative = document.relative_to(PROJECT_ROOT)
    if relative.name != "index.md" or relative.parent.name != "doc":
        return None
    if relative.parent.parent == Path("."):
        return None
    return relative.parent.parent.as_posix()


def test_report_sections_name_the_generated_pages() -> None:
    """A report toctree names its pages, and names them through `generated/`.

    The pages spl-core generates are reached through one route: the `generated`
    link, named `SPL_SPHINX_BINARY_DIR` in CMakeLists.txt. A toctree that still
    globbed `/build/**` would need `:glob:` and would search every variant's
    build on the machine; one that pointed at `generated/` without the
    component's own path would collect another component's report. Both are
    silently wrong -- an entry that resolves to the wrong page still builds.
    """
    documents = sorted(
        set(PROJECT_ROOT.glob("components/**/doc/**/*.md"))
        | set(PROJECT_ROOT.glob("test/**/doc/**/*.md"))
        | {PROJECT_ROOT / "index.md"}
    )

    report_documents = 0
    for document in documents:
        component = _component_path(document)
        for options, entries in _toctrees(document.read_text(encoding="utf-8")):
            for entry in entries:
                assert "/build/" not in entry, (
                    f"{document.relative_to(PROJECT_ROOT)}: toctree entry {entry!r} still points into build/"
                )
            if not any("/reports/" in entry for entry in entries):
                continue
            report_documents += 1
            assert ":glob:" not in options, (
                f"{document.relative_to(PROJECT_ROOT)}: report toctree is still a glob"
            )
            for entry in entries:
                assert entry.startswith("/generated/"), (
                    f"{document.relative_to(PROJECT_ROOT)}: report entry {entry!r} does not start with /generated/"
                )
            if component is not None:
                expected = {f"/generated/{component}/reports/{page}" for page in REPORT_PAGES}
                assert set(entries) == expected, (
                    f"{document.relative_to(PROJECT_ROOT)}: expected {sorted(expected)}, got {sorted(entries)}"
                )

    assert report_documents == 8, f"expected 8 report toctrees, found {report_documents}"


def _excluded(matcher: Matcher, path: str) -> bool:
    """Whether Sphinx's walk would exclude `path`, directory pruning included.

    `get_matching_files` tests each directory as it descends and stops there, so
    a file under a pruned directory never reaches the file matcher. A plain
    `Matcher(path)` call misses that, so this checks the path's ancestors too --
    the effective predicate the build uses.
    """
    parts = Path(path).parts
    for depth in range(1, len(parts) + 1):
        if matcher("/".join(parts[:depth])):
            return True
    return False


def test_generated_is_the_only_route_to_the_generated_pages(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, project_config: dict) -> None:
    """With two routes, every generated page exists under two docnames.

    spl-core's include patterns name the build directory both ways in a SPLed
    build: the raw `build/<V>/<kit>/<type>/...` path and the stable
    `generated/...` name. conf.py must forward only the `generated/` one and
    prune the whole `build` tree from the Sphinx walk, or each report page is
    discovered twice -- once per name -- and every link and need in it is
    duplicated. This executes conf.py against a controlled configuration rather
    than grepping its text, because the property is the resulting source set and
    the resulting matcher.
    """
    config = {
        "include_patterns": [
            "components/light_controller/doc/**",
            "build/Disco/test/Debug/components/light_controller/reports/**",
            "generated/components/light_controller/reports/**",
        ],
    }
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config), encoding="utf-8")

    monkeypatch.setenv("SPHINX_BUILD_CONFIGURATION_FILE", str(config_file))
    monkeypatch.setenv("VARIANT", "Disco")

    module = runpy.run_path(str(PROJECT_ROOT / "conf.py"))

    include_patterns = module["include_patterns"]
    assert "generated/components/light_controller/reports/**" in include_patterns
    assert not [pattern for pattern in include_patterns if pattern.startswith("build/")]

    matcher = Matcher(module["exclude_patterns"])
    assert _excluded(matcher, "build/Disco/test/Debug/components/light_controller/reports/coverage.rst"), (
        "the build tree must be pruned from the Sphinx walk"
    )
    assert not _excluded(matcher, "generated/components/light_controller/reports/coverage.rst")
    assert not _excluded(matcher, "generated/reports/coverage.rst")
    assert _excluded(matcher, "generated/CMakeFiles/x.rst")
    assert _excluded(matcher, "generated/reports/html/index.rst")

    cmake = (PROJECT_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    assert re.search(r"set\(\s*SPL_SPHINX_BINARY_DIR\s+\$\{CMAKE_SOURCE_DIR\}/generated\s*\)", cmake), (
        "CMakeLists.txt must name the generated link as SPL_SPHINX_BINARY_DIR"
    )
    assert project_config["parse"]["parsers"]["rst"]["include"] == ["generated/**/*.rst"]
