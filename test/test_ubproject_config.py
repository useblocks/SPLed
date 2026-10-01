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
import re
import runpy
import subprocess
import sys
import tomllib
from importlib.resources import files
from pathlib import Path
from types import SimpleNamespace

import pytest
from sphinx.util.matching import Matcher

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

import variant_data

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


def test_ubproject_extends_the_generated_rules(project_config: dict) -> None:
    """The committed configuration extends exactly the generated rules file.

    ubproject.toml has to keep its `[needs]` table complete for sphinx-needs,
    which does not follow `extend`, but the document rules are generated and
    live in a file of their own. This is the one `extend` left, and it names
    only the file tools/variant_data.py writes.
    """
    assert project_config["extend"] == "ubproject.variants.toml"


def test_the_generated_rules_extend_the_selection() -> None:
    """ubproject.toml -> ubproject.variants.toml -> build/selection.toml."""
    rules = tomllib.loads((PROJECT_ROOT / "ubproject.variants.toml").read_text(encoding="utf-8"))
    assert rules["extend"] == "build/selection.toml"


def test_conf_py_names_both_generated_files_for_sphinx() -> None:
    """sphinx-needs and sphinx-mounts read one TOML file each, no `extend`.

    conf.py hands each the file it needs: the complete needs model and the
    generated rules. The selection it reads at config-inited defaults to
    build/selection.toml, and `-D spl_selection=<file>` names a build's own.
    """
    conf = (PROJECT_ROOT / "conf.py").read_text(encoding="utf-8")
    assert 'needs_from_toml = "ubproject.toml"' in conf
    assert 'sources_from_toml = "ubproject.variants.toml"' in conf
    assert 'app.add_config_value("spl_selection", "build/selection.toml", "env", types=(str,))' in conf


def test_sphinx_reads_this_exact_file() -> None:
    conf = (PROJECT_ROOT / "conf.py").read_text(encoding="utf-8")
    assert 'needs_from_toml = "ubproject.toml"' in conf


# --- the vendored copy has to match what spl-core ships --------------------


def test_every_spl_core_link_type_is_vendored(project_config: dict, spl_core_config: dict) -> None:
    """Modernized from `extra_links` to `[needs.links]` while copying."""
    expected = {link["option"]: {"incoming": link["incoming"], "outgoing": link["outgoing"]} for link in spl_core_config["needs"]["extra_links"]}
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
    """ubCode must not index every variant and kit ever built -- nor hide the selected one.

    spl-core's base config turns `respect_gitignore` off and then includes the
    generated source listings, but excludes nothing else under the build
    directory, so every need ID appeared once per variant built on that machine.
    The document set is the parser includes': the md parser names no path under
    build/, and the rst parser exists only in the selection, naming the one
    build it selects. Excluding build/ as a whole would hide that build's pages
    too; only the fetched dependencies are excluded, because they carry
    documents of their own (googletest's docs/index.md) that `index.md` matches.
    """
    assert project_config["source"]["extend_exclude"] == ["build/modules/**"]
    assert "rst" not in project_config["parse"]["parsers"]
    assert not [pattern for pattern in project_config["parse"]["parsers"]["md"]["include"] if pattern.startswith("build")]


def _removed_by_rules(rules: list[dict], data: dict, path: str) -> bool:
    """Whether a document at `path` is removed for this cell.

    Rules are subtractive: a path is removed when a rule whose condition is FALSE
    has a pattern matching it. Patterns are matched the way both readers match
    them (sphinx-mounts' own dialect): against paths in the project tree, and
    against a mounted build's files, relative to the mounted directory.
    """
    from sphinx_mounts import dialect, variants

    return any(dialect.matches(pattern, path) for rule in rules if not variants.interpret(variants.validate(rule["if"]), data) for pattern in rule["files"])


def test_the_scope_rules_split_variant_and_component_documents(rules: list[dict]) -> None:
    """A variant shows the variant-wide documents and the components it has.

    A component's report shows one component's documentation under
    doc/component_report.md, and none of the variant-wide documents. The two
    facts are two rules over `var.build_config.scope`, evaluated here with
    sphinx-mounts' own interpreter against the real generated cells. Which
    generated pages a report reads is its selection's include, not a rule.
    """
    variant_cell = _variant_data("Disco", "test", "reports")
    component_cell = _component_variant_data("Disco", "test", "reports", "components/light_controller")

    for path in ("index.md", "doc/components/index.md", "components/light_controller/doc/index.md", "build/Disco/test/Debug/reports/coverage.rst"):
        assert not _removed_by_rules(rules, variant_cell, path), f"the variant removes {path}"
    for path in ("doc/component_report.md", "components/auto_off/doc/index.md"):
        assert _removed_by_rules(rules, variant_cell, path), f"the variant keeps {path}"

    # The component cell: exactly the one component, and none of the
    # variant-wide documents. The root index.md is not named by any rule -- a
    # pattern without a slash would match every index.md -- and is an orphan
    # page there, whose toctree entries are all excluded.
    for path in ("doc/component_report.md", "components/light_controller/doc/index.md"):
        assert not _removed_by_rules(rules, component_cell, path), f"the component report removes {path}"
    for path in (
        "doc/components/index.md",
        "doc/sw_requirements/index.md",
        "components/main_control_knob/doc/index.md",
        "components/auto_off/doc/index.md",
    ):
        assert _removed_by_rules(rules, component_cell, path), f"the component report keeps {path}"
    assert not _removed_by_rules(rules, component_cell, "index.md")
    assert "orphan: true" in (PROJECT_ROOT / "index.md").read_text(encoding="utf-8").split("---")[1]


def test_extend_include_is_not_used_because_it_would_be_inert(project_config: dict, spl_core_config: dict) -> None:
    """Configuring parsers puts ubCode in parser mode, where this key is ignored.

    spl-core's base config includes the generated listings with
    `[source] extend_include`, which works only while no parser is configured.
    This project configures parsers, so file discovery comes from their
    `include` lists and `extend_include` does nothing -- silently, apart from
    one config warning. Carrying the key anyway would look like configuration
    and behave like a comment. `ubc check` is what caught this. The generated
    listings are named by the selection's rst parser instead.
    """
    assert spl_core_config["source"]["extend_include"] == ["build/**/__source_docs/**"]
    assert "extend_include" not in project_config["source"]


def test_ubcode_and_sphinx_see_the_same_documents(project_config: dict, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The parser includes have to match conf.py's include_patterns.

    They did not: `include = ["*.md"]` matched every Markdown file in the tree,
    so ubCode parsed AGENTS.md, README.md, CLAUDE.md and three dozen agent skill
    definitions as project documents -- 38 files Sphinx never sees. Two readers
    with different document sets cannot agree about the project, which is the
    whole thing this configuration exists to prevent.

    The generated pages are the selection's rst include, which conf.py adds to
    Sphinx's include_patterns: executed here, against a rendered selection.
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

    build_dir = PROJECT_ROOT / "build" / "Disco" / "test" / "Debug"
    selection_file = tmp_path / "selection.toml"
    selection_file.write_text(variant_data.selection_toml(PROJECT_ROOT, variant_data.cell_path(PROJECT_ROOT, "Disco", "test", "reports"), "reports", build_dir), encoding="utf-8")
    pages = tomllib.loads(selection_file.read_text(encoding="utf-8"))["parse"]["parsers"]["rst"]["include"]

    monkeypatch.setenv("VARIANT", "Disco")
    module = runpy.run_path(str(PROJECT_ROOT / "conf.py"))

    app = SimpleNamespace(confdir=str(PROJECT_ROOT))
    config = SimpleNamespace(
        spl_selection=str(selection_file),
        overrides={},
        include_patterns=list(module["include_patterns"]),
        suppress_warnings=[],
        needs_variant_data_file=None,
        root_doc="index",
    )
    module["_load_selection"](app, config)
    assert config.include_patterns == [*module["include_patterns"], *pages]


# --- what the variant machinery needs --------------------------------------


def test_variant_data_is_named_by_the_selection_not_the_committed_config(project_config: dict) -> None:
    """The committed configuration names no cell; a rendered selection does."""
    assert "variant_data_file" not in project_config.get("needs", {})

    rendered = variant_data.selection_toml(PROJECT_ROOT, PROJECT_ROOT / "build" / "variants" / "Disco" / "test" / "reports.json", "reports", None)
    selection = tomllib.loads(rendered)
    assert selection["needs"]["variant_data_file"].endswith("build/variants/Disco/test/reports.json")
    assert "parse" not in selection


def test_needs_json_is_written(project_config: dict) -> None:
    assert project_config["needs"]["build_json"] is True


# --- the variant rules -----------------------------------------------------
#
# These evaluate the real conditions with sphinx-mounts' own interpreter,
# against the real generated variant data. That is the closest a test can get
# to "ubCode and the build decide the same thing", because it is literally the
# same grammar and the same file.


@pytest.fixture(scope="module")
def rules(generated_variant_data: None) -> list[dict]:
    """The document rules, as tools/variant_data.py writes them with Disco's test build selected."""
    return tomllib.loads(variant_data.rules_toml(PROJECT_ROOT, ("Disco", "test", "build/Disco/test/Debug")))["source"]["variant_sources"]


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


def _component_variant_data(variant: str, kit: str, target: str, component: str) -> dict:
    path = PROJECT_ROOT / "build" / "variants" / variant / kit / component / f"{target}.json"
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def test_every_component_document_is_gated_by_a_rule(rules: list[dict]) -> None:
    """A hand-written component document with no rule is 150% in every variant.

    It would then appear in variants that do not contain the component, and
    every need in it would enter their traceability data. The failure is
    additive and silent, which is why it needs a test rather than a review.
    """
    from sphinx_mounts import dialect

    patterns = [pattern for rule in rules for pattern in rule["files"]]
    for doc_dir in sorted(PROJECT_ROOT.glob("components/**/doc")) + sorted(PROJECT_ROOT.glob("test/*/doc")):
        rel = doc_dir.relative_to(PROJECT_ROOT).as_posix()
        assert any(dialect.matches(pattern, f"{rel}/index.md") for pattern in patterns), f"{rel} is not gated by any generated rule"


def test_no_rule_names_a_variant_by_name(rules: list[dict]) -> None:
    """Membership, never identity -- except for the selected build's own rule.

    Gating on the variant name re-encodes what parts.cmake already says, and
    the two are then free to drift. The integration suite is the case in point:
    it used to be gated on `variant == "Disco"`, which also claimed it for
    Disco's prod kit, where parts.cmake does not add it. The one rule that does
    name a variant gates a build directory's pages on that build's own variant
    and kit: a fact about the build, not about the product.
    """
    known_variants = {"Disco", "Sleep", "Spa", "Base/Dev", "IDEA/Sloemada"}
    build_rules = [rule for rule in rules if rule["files"] == ["build/Disco/test/Debug/**"]]
    assert len(build_rules) == 1
    for rule in rules:
        if rule in build_rules:
            continue
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
        (
            "Disco",
            "test",
            ["components/light_controller/doc/index.md", "test/spled_integration/doc/index.md"],
            ["components/auto_off/doc/index.md", "components/brightness_controller/doc/index.md"],
        ),
        ("Disco", "prod", ["components/light_controller/doc/index.md"], ["test/spled_integration/doc/index.md", "components/auto_off/doc/index.md"]),
        # Sleep: manual brightness and auto-off, no integration suite.
        ("Sleep", "test", ["components/auto_off/doc/index.md", "components/brightness_controller/doc/index.md"], ["test/spled_integration/doc/index.md"]),
        # Spa: brightness but no auto-off.
        ("Spa", "test", ["components/brightness_controller/doc/index.md"], ["components/auto_off/doc/index.md"]),
        # Base/Dev: the example components, none of the product ones.
        ("Base/Dev", "test", ["components/examples/hello_gmock/doc/index.md"], ["components/light_controller/doc/index.md", "components/auto_off/doc/index.md"]),
    ],
)
def test_rules_select_the_expected_documents(rules: list[dict], variant: str, kit: str, expect_present: list[str], expect_absent: list[str]) -> None:
    data = _variant_data(variant, kit, "docs")
    for path in expect_present:
        assert not _removed_by_rules(rules, data, path), f"{variant}/{kit}: expected {path} to be included"
    for path in expect_absent:
        assert _removed_by_rules(rules, data, path), f"{variant}/{kit}: expected {path} to be excluded"


def test_the_selected_build_is_read_only_for_its_own_cell(rules: list[dict]) -> None:
    """The selected build's pages exist for its own variant's and kit's reports only.

    A reader pointed at another variant's data, with the selection still in
    place, then reads none of this build's pages, instead of showing them as
    that variant's. This evaluates the generated rule against the real cells.
    """
    page = "build/Disco/test/Debug/components/light_controller/reports/unit_test_results.rst"
    assert not _removed_by_rules(rules, _variant_data("Disco", "test", "reports"), page)
    assert not _removed_by_rules(rules, _component_variant_data("Disco", "test", "reports", "components/light_controller"), page)
    assert _removed_by_rules(rules, _variant_data("Disco", "test", "docs"), page)
    assert _removed_by_rules(rules, _variant_data("Sleep", "test", "reports"), page)
    assert _removed_by_rules(rules, _variant_data("Disco", "prod", "reports"), page)


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
    """A report toctree names its pages where spl-core writes them, by a glob over build/.

    The selection reads one build's pages, so `/build/**/<component>/reports/<page>`
    resolves to exactly one page. Without the component's own path, an entry
    would collect another component's report; the variant's coverage page needs
    a pattern per depth, because `**` would also match every component's. Both
    are silently wrong -- an entry that resolves to the wrong page still builds.
    """
    documents = sorted(set(PROJECT_ROOT.glob("components/**/doc/**/*.md")) | set(PROJECT_ROOT.glob("test/**/doc/**/*.md")) | {PROJECT_ROOT / "index.md"})

    report_toctrees = 0
    for document in documents:
        component = _component_path(document)
        for options, entries in _toctrees(document.read_text(encoding="utf-8")):
            if not any("/reports/" in entry for entry in entries):
                continue
            report_toctrees += 1
            name = document.relative_to(PROJECT_ROOT)
            assert ":glob:" in options, f"{name}: a report toctree has to be a glob"
            assert not [entry for entry in entries if "generated" in entry], f"{name}: report entries still name generated/"
            if component is not None:
                expected = {f"/build/**/{component}/reports/{page}" for page in REPORT_PAGES}
                expected.add(f"/build/**/{component}/__source_docs/index")
                assert set(entries) == expected, f"{name}: expected {sorted(expected)}, got {sorted(entries)}"
            else:
                assert entries in (["/build/*/*/*/reports/coverage"], ["/build/*/*/*/*/reports/coverage"]), f"{name}: {entries}"

    # Nine component documents (the two examples included) plus index.md's two
    # coverage toctrees, one per depth of a variant's name.
    assert report_toctrees == 11, f"expected 11 report toctrees, found {report_toctrees}"


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


def test_the_generated_pages_are_read_where_spl_core_writes_them(monkeypatch: pytest.MonkeyPatch) -> None:
    """One route to each generated page: its own path, as upstream names it.

    No link, no mount, no stable alias: SPL_SPHINX_BINARY_DIR is gone, and conf.py
    names no generated page itself -- the selection adds the selected build's.
    The Sphinx walk prunes only the directories under build/ that never hold a
    document. This executes conf.py rather than grepping its text, because the
    property is the resulting source set and the resulting matcher.
    """
    monkeypatch.setenv("VARIANT", "Disco")

    module = runpy.run_path(str(PROJECT_ROOT / "conf.py"))

    assert not [pattern for pattern in module["include_patterns"] if pattern.startswith(("build", "generated"))]

    matcher = Matcher(module["exclude_patterns"])
    assert not _excluded(matcher, "build/Disco/test/Debug/components/light_controller/reports/coverage.rst")
    assert not _excluded(matcher, "build/Base/Dev/test/Debug/reports/coverage.rst")
    assert _excluded(matcher, "build/modules/googletest-src/docs/index.md")
    assert _excluded(matcher, "build/Disco/test/Debug/CMakeFiles/x.rst")
    assert _excluded(matcher, "build/Disco/test/Debug/reports/html/index.rst")

    cmake = (PROJECT_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    assert "SPL_SPHINX_BINARY_DIR" not in cmake, "the pages keep the names spl-core gives them"
    assert re.search(
        r"set\(\s*SPL_SPHINX_OPTIONS\s+-D\s+spl_selection=\$\{CMAKE_BINARY_DIR\}/selection/@SHAPE@\.toml\s*\)",
        cmake,
    ), "CMakeLists.txt must point the variant-wide runs at this build's selection"
    assert re.search(
        r"set\(\s*SPL_SPHINX_COMPONENT_OPTIONS\s+-D\s+spl_selection=\$\{CMAKE_BINARY_DIR\}/selection/@COMPONENT_PATH@/@SHAPE@\.toml\s*\)",
        cmake,
    ), "CMakeLists.txt must point the per-component runs at this build's selection"


#: The spl-core settings that decide what spl-core writes for each component.
SPL_CORE_DOCS_SETTINGS = ("SPL_SPHINX_OPTIONS", "SPL_SPHINX_COMPONENT_OPTIONS", "SPL_SOURCE_DOCS_JINJA_RAW_TAGS", "SPL_TEST_RESULTS_AS_NEEDS")


def test_the_spl_core_settings_come_before_the_components() -> None:
    """spl-core computes what it writes for a component while parts.cmake adds it.

    A setting placed after `include(.../parts.cmake)` would apply to no component:
    the reports would be built without it, and every other test of its value would
    still pass.
    """
    lines = (PROJECT_ROOT / "CMakeLists.txt").read_text(encoding="utf-8").splitlines()

    def first(pattern: str) -> int:
        found = [number for number, line in enumerate(lines, start=1) if re.match(pattern, line.strip())]
        assert found, f"CMakeLists.txt has no line matching {pattern!r}"
        return found[0]

    parts = first(r"include\(.*/variants/\$\{VARIANT\}/parts\.cmake\)")
    for setting in SPL_CORE_DOCS_SETTINGS:
        line = first(rf"set\(\s*{setting}\b")
        assert line < parts, f"CMakeLists.txt:{line} sets {setting} after parts.cmake is included (line {parts})"


# --- the same checks, as conf.py runs them ------------------------------------


def test_the_checks_conf_py_runs_find_nothing() -> None:
    """conf.py runs tools/config_checks.py whenever Sphinx reads its configuration.

    The tests above are the detailed form of those checks; this one runs exactly
    what a Sphinx build runs, with the include patterns conf.py really ends up
    with, so a build under -W and this suite cannot disagree about whether the
    configuration is intact.
    """
    import config_checks

    module = runpy.run_path(str(PROJECT_ROOT / "conf.py"))
    assert config_checks.run_all(PROJECT_ROOT, list(module["include_patterns"])) == []


def test_the_checks_notice_a_hand_written_rule(project_config: dict) -> None:
    """A rule in ubproject.toml would replace every generated one: `extend` replaces arrays."""
    import config_checks

    tampered = {**project_config, "source": {**project_config["source"], "variant_sources": [{"if": "True", "files": ["x"]}]}}
    assert any("declares rules" in finding for finding in config_checks.generated_half(tampered))


def test_remote_url_links_in_both_readers(project_config: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    """ubCode links the codelinks URL through a declared field and a rule; Sphinx keeps codelinks' own rule.

    sphinx-codelinks registers `remote-url` and adds its link rule only while
    Sphinx runs, so ubCode needs both declared here. sphinx-needs applies only
    the first rule naming a field, so conf.py drops this one for Sphinx, or it
    would shadow codelinks' rule and leave Sphinx's value unlinked.
    """
    assert "remote-url" in project_config["needs"]["fields"]
    rule = project_config["needs"]["string_links"]["remote_url"]
    assert rule["options"] == ["remote-url"]
    assert re.match(rule["regex"], "https://github.com/avengineers/SPLed/blob/abc123/components/x/src/x.c#L13")

    monkeypatch.setenv("VARIANT", "Disco")
    module = runpy.run_path(str(PROJECT_ROOT / "conf.py"))
    config = SimpleNamespace(needs_string_links={"remote_url": rule, "other": {"options": ["status"]}})
    module["_leave_codelinks_links_to_codelinks"](None, config)
    assert config.needs_string_links == {"other": {"options": ["status"]}}
