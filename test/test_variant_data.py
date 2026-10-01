"""Tests for the variant data generator, tools/variant_data.py.

These run without a compiler, a CMake configure or a Sphinx build, which is the
whole point of the generator: the documentation and its gate must be derivable
from the sources alone.

The parts.cmake parser gets the most attention here. It is the one place where
this project reads a CMake file with something other than CMake, and the failure
mode it guards against is silent: a parser that shrugged at a condition it did
not understand would return a component list that is wrong for some kit, and
that list is what gates the documents. The symptom would be documents missing
from a variant's build -- no error, no warning, just less.
"""

import json
import os
import shutil
import sys
import tomllib
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

import variant_data

# The variant data is the input to every documentation gate, and generating it
# is pure Python that costs milliseconds -- so it runs in all of them. A
# regression here does not fail a build; it silently drops documents from a
# variant, which is exactly what a gate has to catch early.
pytestmark = [
    pytest.mark.unittests,
    pytest.mark.gate_develop_pr,
    pytest.mark.gate_develop_push,
    pytest.mark.gate_develop_nightly,
    pytest.mark.gate_release_pr,
    pytest.mark.gate_release,
]


# --- the variant set -------------------------------------------------------


def test_finds_every_variant_including_nested_ones() -> None:
    """A variant is a directory holding config.cmake, one or two levels deep."""
    assert variant_data.variant_names(PROJECT_ROOT) == [
        "Base/Dev",
        "Disco",
        "IDEA/Sloemada",
        "Sleep",
        "Spa",
    ]


# --- parts.cmake: the grammar this project actually uses --------------------


@pytest.mark.parametrize("kit", variant_data.KITS)
def test_flat_parts_file_is_kit_independent(kit: str) -> None:
    """Spa has no guard, so both kits see the same components."""
    assert variant_data.components(PROJECT_ROOT, "Spa", kit) == variant_data.components(PROJECT_ROOT, "Spa", "prod")


def test_test_kit_guard_is_honoured() -> None:
    """Disco adds its integration suite only for the test kit."""
    prod = variant_data.components(PROJECT_ROOT, "Disco", "prod")
    test = variant_data.components(PROJECT_ROOT, "Disco", "test")

    assert "test/spled_integration" not in prod
    assert "test/spled_integration" in test
    assert test[: len(prod)] == prod, "the guard must only ADD, not reorder"


def test_component_order_follows_the_file() -> None:
    """The list is the product structure, so it keeps parts.cmake's order."""
    assert variant_data.components(PROJECT_ROOT, "Disco", "prod")[:3] == [
        "components/platform_types",
        "components/rte",
        "components/main",
    ]


# --- parts.cmake: everything outside the grammar has to raise ---------------


def _write_parts(tmp_path: Path, body: str) -> Path:
    parts_dir = tmp_path / "variants" / "Fake"
    parts_dir.mkdir(parents=True)
    (parts_dir / "parts.cmake").write_text(body, encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize(
    ("body", "because"),
    [
        ("if(SOME_OTHER_CONDITION)\n  spl_add_component(components/a)\nendif()\n", "unknown condition"),
        ("if(BUILD_KIT STREQUAL test)\n  if(X)\n  endif()\nendif()\n", "nested if"),
        ("if(BUILD_KIT STREQUAL test)\nelseif(X)\nendif()\n", "elseif"),
        ("spl_add_component(components/a)\nendif()\n", "endif without if"),
        ("else()\n", "else outside if"),
        ("if(BUILD_KIT STREQUAL test)\n  spl_add_component(components/a)\n", "unterminated if"),
        ("set(SOMETHING on)\n", "statement that is not spl_add_component"),
        ("if(NOT BUILD_KIT STREQUAL test)\n  spl_add_component(components/a)\nendif()\n", "the negated guard"),
        ("if(BUILD_KIT STREQUAL test OR FOO)\n  spl_add_component(components/a)\nendif()\n", "a compound guard"),
        ("if(BUILD_KIT STREQUAL testing)\n  spl_add_component(components/a)\nendif()\n", "another kit name"),
        ("if(BUILD_KIT STREQUAL Test)\n  spl_add_component(components/a)\nendif()\n", "STREQUAL is case-sensitive"),
        ("spl_add_component(\n  components/a)\n", "a call over two lines"),
        ("spl_add_component(components/a components/b)\n", "two arguments"),
        ("if(BUILD_KIT STREQUAL test)\nelse(X)\nendif()\n", "else with an argument"),
    ],
)
def test_unsupported_grammar_raises(tmp_path: Path, body: str, because: str) -> None:
    root = _write_parts(tmp_path, body)
    with pytest.raises(ValueError, match=r"variants[/\\]Fake[/\\]parts\.cmake(:\d+)?: "):
        variant_data.components(root, "Fake", "test")


@pytest.mark.parametrize(
    "body",
    [
        'spl_add_component("components/a")\n',
        "SPL_ADD_COMPONENT( components/a )\n",
        'IF (BUILD_KIT STREQUAL "test")\n  spl_add_component(components/a)\nENDIF()\n',
    ],
)
def test_the_grammar_accepts_its_cmake_spellings(tmp_path: Path, body: str) -> None:
    """Command names in any case, a quoted argument without its quotes, a quoted kit."""
    root = _write_parts(tmp_path, body)
    assert variant_data.components(root, "Fake", "test") == ["components/a"]


def test_comments_and_blank_lines_are_ignored(tmp_path: Path) -> None:
    root = _write_parts(
        tmp_path,
        "# leading comment\n\nspl_add_component(components/a)  # trailing\n\n",
    )
    assert variant_data.components(root, "Fake", "prod") == ["components/a"]


def test_else_branch_belongs_to_the_other_kit(tmp_path: Path) -> None:
    """Not used in this project today, but it must not be silently wrong."""
    root = _write_parts(
        tmp_path,
        "if(BUILD_KIT STREQUAL test)\n  spl_add_component(test/suite)\nelse()\n  spl_add_component(components/stub)\nendif()\n",
    )
    assert variant_data.components(root, "Fake", "test") == ["test/suite"]
    assert variant_data.components(root, "Fake", "prod") == ["components/stub"]


# --- the feature vector ----------------------------------------------------


def test_feature_vector_is_complete() -> None:
    """Every boolean the model declares is present, so no condition is unknown.

    BRIGHTNESS_ADJUSTMENT_ENABLED is the case that motivates this: it is
    promptless, so KConfig omits it from its JSON for exactly the variants
    where it is off. A document or a mount condition naming it would then be
    unevaluable there -- and both tools gate unevaluable content OFF rather
    than answering False, so the content would silently disappear.
    """
    disco = variant_data.features(PROJECT_ROOT, "Disco")
    sleep = variant_data.features(PROJECT_ROOT, "Sleep")

    for name in ("BRIGHTNESS_ADJUSTMENT_ENABLED", "AUTO_OFF", "BLINKING", "COLOR_1_IS_ENABLED"):
        assert name in disco, f"{name} missing from Disco's feature vector"
        assert name in sleep, f"{name} missing from Sleep's feature vector"

    # Disco selects BLINKING, which the brightness choice depends on being off.
    assert disco["BLINKING"] is True
    assert disco["BRIGHTNESS_ADJUSTMENT_ENABLED"] is False
    assert disco["AUTO_OFF"] is False

    # Sleep selects manual brightness and auto-off.
    assert sleep["BLINKING"] is False
    assert sleep["BRIGHTNESS_ADJUSTMENT_ENABLED"] is True
    assert sleep["AUTO_OFF"] is True


def test_non_boolean_values_keep_their_type() -> None:
    disco = variant_data.features(PROJECT_ROOT, "Disco")
    assert disco["CUSTOMER"] == "A"
    assert disco["OS_TASK_PERIOD"] == 10


def test_variant_without_config_txt_uses_model_defaults() -> None:
    """Base/Dev ships no config.txt; the model's own defaults apply."""
    assert not (PROJECT_ROOT / "variants" / "Base" / "Dev" / "config.txt").exists()
    base = variant_data.features(PROJECT_ROOT, "Base/Dev")
    assert base["CUSTOMER"] == "None"
    assert base["BLINKING"] is False


# --- the cell as a whole ---------------------------------------------------


@pytest.mark.parametrize("variant", ["Base/Dev", "Disco", "IDEA/Sloemada", "Sleep", "Spa"])
@pytest.mark.parametrize("kit", variant_data.KITS)
@pytest.mark.parametrize("target", variant_data.TARGETS)
def test_every_cell_carries_the_whole_contract(variant: str, kit: str, target: str) -> None:
    """Everything a condition may name has to be IN the file.

    This is the rule the whole design rests on: a key that only conf.py knows
    is invisible to ubCode and every other reader, and their view of the
    project then silently disagrees with the build.
    """
    data = variant_data.variant_data(PROJECT_ROOT, variant, kit, target)

    assert set(data) == {"features", "build_config"}
    assert data["build_config"]["variant"] == variant
    assert data["build_config"]["kit"] == kit
    assert data["build_config"]["target"] == target
    assert data["build_config"]["components"]
    assert data["build_config"]["scope"] == "variant"
    assert data["build_config"]["component"] == ""
    assert data["features"]

    # It has to survive the round trip to the file both tools read.
    assert json.loads(json.dumps(data)) == data


@pytest.mark.parametrize("variant", ["Base/Dev", "Disco", "IDEA/Sloemada", "Sleep", "Spa"])
@pytest.mark.parametrize("kit", variant_data.KITS)
@pytest.mark.parametrize("target", variant_data.TARGETS)
def test_every_component_cell_carries_the_whole_contract(variant: str, kit: str, target: str) -> None:
    """A component's report gets the same complete contract, one scope deeper.

    The component list stays the variant's, so a block conditioned on another
    component's presence reads the same in a component's report as in the
    variant's documentation; only `scope` and `component` differ.
    """
    documented = variant_data.reported_components(PROJECT_ROOT, variant, kit)
    assert documented, f"{variant}/{kit} has no documented component to report on"

    for component in documented:
        data = variant_data.variant_data(PROJECT_ROOT, variant, kit, target, component)

        assert set(data) == {"features", "build_config"}
        assert data["build_config"]["variant"] == variant
        assert data["build_config"]["kit"] == kit
        assert data["build_config"]["target"] == target
        assert data["build_config"]["scope"] == "component"
        assert data["build_config"]["component"] == component
        assert data["build_config"]["components"] == variant_data.components(PROJECT_ROOT, variant, kit)
        assert data["features"]
        assert json.loads(json.dumps(data)) == data


# --- the rendered selection ------------------------------------------------


def _tmp_project(tmp_path: Path) -> Path:
    """A small project root with a parts.cmake and two documented components."""
    root = tmp_path / "project"
    parts = root / "variants" / "Test"
    parts.mkdir(parents=True)
    (parts / "parts.cmake").write_text(
        "spl_add_component(components/a)\nspl_add_component(test/suite)\n",
        encoding="utf-8",
    )
    for component in ("components/a", "test/suite"):
        doc = root / component / "doc"
        doc.mkdir(parents=True)
        (doc / "index.md").write_text(f"# {component}\n", encoding="utf-8")
    return root


def test_selection_toml_without_a_build_dir_reads_no_generated_page(tmp_path: Path) -> None:
    """Selecting a cell on its own shows its documents and no generated page."""
    cell = variant_data.cell_path(PROJECT_ROOT, "Disco", "test", "reports")
    selection = tomllib.loads(variant_data.selection_toml(PROJECT_ROOT, cell, "reports", None))

    assert selection["needs"]["variant_data_file"] == cell.resolve().as_posix()
    assert "parse" not in selection
    assert "source" not in selection
    assert "project" not in selection


def test_selection_toml_reads_a_builds_pages_by_their_own_paths() -> None:
    """A CMake build's reports read its generated pages where spl-core writes them."""
    build_dir = PROJECT_ROOT / "build" / "Disco" / "test" / "Debug"

    reports = tomllib.loads(variant_data.selection_toml(PROJECT_ROOT, variant_data.cell_path(PROJECT_ROOT, "Disco", "test", "reports"), "reports", build_dir))
    assert reports["parse"]["parsers"]["rst"]["include"] == [f"build/Disco/test/Debug/{pattern}" for pattern in variant_data.GENERATED_PAGES]
    assert "source" not in reports, "no mount, and no rule: `-c` would replace every generated rule"

    docs = tomllib.loads(variant_data.selection_toml(PROJECT_ROOT, variant_data.cell_path(PROJECT_ROOT, "Disco", "test", "docs"), "docs", build_dir))
    assert "parse" not in docs, "the docs shape reads no generated page"


def test_a_build_outside_the_project_is_refused(tmp_path: Path) -> None:
    """Its pages would have no name to be read by."""
    with pytest.raises(ValueError, match="outside"):
        variant_data.selection_toml(PROJECT_ROOT, variant_data.cell_path(PROJECT_ROOT, "Disco", "test", "reports"), "reports", tmp_path)


def test_the_rules_name_the_selected_build_and_survive_regenerating_the_matrix(tmp_path: Path) -> None:
    """Selecting a build writes its rule; `--all` afterwards keeps it."""
    shutil.copytree(PROJECT_ROOT / "variants", tmp_path / "variants")
    shutil.copy(PROJECT_ROOT / "KConfig", tmp_path / "KConfig")
    for top in ("components", "test"):
        for index in (PROJECT_ROOT / top).rglob("doc/index.md"):
            target = tmp_path / index.relative_to(PROJECT_ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("# x\n", encoding="utf-8")
    (tmp_path / "doc").mkdir()
    build_dir = tmp_path / "build" / "Disco" / "test" / "Debug"
    build_dir.mkdir(parents=True)

    assert variant_data.main(["--project-root", str(tmp_path), "--variant", "Disco", "--kit", "test", "--target", "reports", "--current", "--build-dir", str(build_dir)]) == 0
    assert variant_data.selected_build(tmp_path) == ("Disco", "test", "build/Disco/test/Debug")
    rules = (tmp_path / variant_data.RULES_FILE).read_text(encoding="utf-8")
    assert '"build/Disco/test/Debug/**"' in rules

    assert variant_data.main(["--project-root", str(tmp_path), "--all"]) == 0
    assert (tmp_path / variant_data.RULES_FILE).read_text(encoding="utf-8") == rules
    assert variant_data.main(["--project-root", str(tmp_path), "--all", "--check"]) == 0

    # The build's own tooling finds the selected build by the pointer: the copy of
    # its compile database follows the selection, for a docs-shape one as well.
    import compile_commands

    assert compile_commands.selected_build_dir(tmp_path) == build_dir.resolve()
    assert variant_data.main(["--project-root", str(tmp_path), "--variant", "Disco", "--kit", "prod", "--target", "docs", "--current", "--build-dir", str(build_dir)]) == 0
    assert compile_commands.selected_build_dir(tmp_path) == build_dir.resolve()
    assert '"build/Disco/test/Debug/**"' not in (tmp_path / variant_data.RULES_FILE).read_text(encoding="utf-8"), "a docs selection reads no page"
    assert variant_data.main(["--project-root", str(tmp_path), "--variant", "Disco", "--kit", "test", "--target", "docs", "--current"]) == 0
    assert compile_commands.selected_build_dir(tmp_path) is None


def test_selection_toml_can_name_a_component_root_doc() -> None:
    """A per-component report renders under its own root document, and reads only its component's pages."""
    build_dir = PROJECT_ROOT / "build" / "Disco" / "test" / "Debug"
    cell = variant_data.cell_path(PROJECT_ROOT, "Disco", "test", "reports", "components/light_controller")
    selection = tomllib.loads(variant_data.selection_toml(PROJECT_ROOT, cell, "reports", build_dir, variant_data.COMPONENT_ROOT_DOC, "components/light_controller"))
    assert selection["project"]["root_doc"] == variant_data.COMPONENT_ROOT_DOC
    assert selection["parse"]["parsers"]["rst"]["include"] == ["build/Disco/test/Debug/components/light_controller/**/*.rst"]


def test_write_selection_writes_the_project_selection_and_every_run(tmp_path: Path) -> None:
    """A selected build gets one selection file per spl-core documentation run.

    build/selection.toml is what the IDE and a bare run read; every shape and
    every component of the build gets its own file, so two builds' reports can
    be built side by side and each names the cell of its own shape.
    """
    root = _tmp_project(tmp_path)
    build_dir = root / "build" / "Test" / "test" / "Debug"
    build_dir.mkdir(parents=True)

    variant_data.write_selection(root, "Test", "test", "reports", build_dir)

    selection = tomllib.loads((root / variant_data.SELECTION_FILE).read_text(encoding="utf-8"))
    assert selection["needs"]["variant_data_file"] == variant_data.cell_path(root, "Test", "test", "reports").resolve().as_posix()

    for shape in variant_data.TARGETS:
        run = build_dir / "selection" / f"{shape}.toml"
        assert run.is_file(), f"the variant-wide {shape} run has no selection"
        assert tomllib.loads(run.read_text(encoding="utf-8"))["needs"]["variant_data_file"] == (variant_data.cell_path(root, "Test", "test", shape).resolve().as_posix())

    for component in variant_data.reported_components(root, "Test", "test"):
        for shape in variant_data.TARGETS:
            run = build_dir / "selection" / component / f"{shape}.toml"
            assert run.is_file(), f"{component}'s {shape} run has no selection"
            parsed = tomllib.loads(run.read_text(encoding="utf-8"))
            assert parsed["needs"]["variant_data_file"] == (variant_data.cell_path(root, "Test", "test", shape, component).resolve().as_posix())
            assert parsed["project"]["root_doc"] == variant_data.COMPONENT_ROOT_DOC


def test_selecting_removes_an_old_generated_symlink_without_touching_its_target(tmp_path: Path) -> None:
    """The old link is removed; the build it led to is somebody's and stays."""
    root = _tmp_project(tmp_path)
    target = tmp_path / "old_build"
    target.mkdir()
    (target / "keep.txt").write_text("keep", encoding="utf-8")
    generated = root / "generated"
    generated.symlink_to(target, target_is_directory=True)

    variant_data.write_selection(root, "Test", "prod", "docs", None)

    assert not generated.exists(), "the stale link must be removed"
    assert (target / "keep.txt").read_text(encoding="utf-8") == "keep", "the target must survive"


def test_selecting_removes_the_old_autoconf_pointer(tmp_path: Path) -> None:
    """`build/autoconf.json` was the pointer; nothing reads it any more."""
    root = _tmp_project(tmp_path)
    pointer = root / "build" / "autoconf.json"
    pointer.parent.mkdir(parents=True)
    pointer.write_text("{}", encoding="utf-8")

    variant_data.write_selection(root, "Test", "prod", "docs", None)

    assert not pointer.exists()


def test_selecting_removes_a_no_symlink_placeholder(tmp_path: Path) -> None:
    """A directory holding NO_SYMLINK is the old placeholder, and goes."""
    root = _tmp_project(tmp_path)
    generated = root / "generated"
    generated.mkdir()
    (generated / "NO_SYMLINK").write_text("no link here\n", encoding="utf-8")

    variant_data.write_selection(root, "Test", "prod", "docs", None)

    assert not generated.exists()


def test_selecting_leaves_a_plain_generated_directory_alone(tmp_path: Path) -> None:
    """A real directory somebody put there is not ours to remove."""
    root = _tmp_project(tmp_path)
    generated = root / "generated"
    generated.mkdir()
    (generated / "somebody.txt").write_text("mine", encoding="utf-8")

    variant_data.write_selection(root, "Test", "prod", "docs", None)

    assert (generated / "somebody.txt").read_text(encoding="utf-8") == "mine"


# --- the generated rules ---------------------------------------------------


def _parsed_rules(root: Path) -> list[dict]:
    return tomllib.loads(variant_data.rules_toml(root))["source"]["variant_sources"]


def test_rules_toml_covers_every_documented_component_exactly_once(tmp_path: Path) -> None:
    """A hand-written component with no rule is 150% in every variant.

    The failure is additive and silent -- its documents appear in variants that
    do not contain the component -- so each documented component has exactly one
    rule naming it.
    """
    root = _tmp_project(tmp_path)
    rules = _parsed_rules(root)
    documented = variant_data.documented_components(root)
    assert documented == ["components/a", "test/suite"]

    for component in documented:
        matching = [rule for rule in rules if f"'{component}'" in rule["if"]]
        assert len(matching) == 1, f"{component} is gated by {len(matching)} rules"
        # One pattern, matched in the tree and inside a mounted build alike.
        assert matching[0]["files"] == [f"{component}/**"]


def test_every_generated_rule_condition_is_inside_the_grammar(tmp_path: Path) -> None:
    """A condition outside the grammar is refused rather than evaluated."""
    from sphinx_mounts import variants

    for rule in _parsed_rules(_tmp_project(tmp_path)):
        variants.validate(rule["if"])


def test_hand_written_rules_are_appended(tmp_path: Path) -> None:
    """Numbers a component's membership cannot decide come from a hand file."""
    root = _tmp_project(tmp_path)
    (root / "doc").mkdir()
    (root / variant_data.HAND_WRITTEN_RULES).write_text(
        '[[source.variant_sources]]\nif = "var.build_config.scope == \'variant\'"\nfiles = ["extra/**"]\n',
        encoding="utf-8",
    )

    rules = _parsed_rules(root)
    assert rules[-1]["if"] == "var.build_config.scope == 'variant'"
    assert rules[-1]["files"] == ["extra/**"]


def test_write_text_if_changed_does_not_rewrite_identical_content(tmp_path: Path) -> None:
    """A reader's cache stays valid when the content has not changed."""
    path = tmp_path / "file.txt"
    assert variant_data.write_text_if_changed(path, "same") is True

    os.utime(path, (1_000_000, 1_000_000))
    before = path.stat().st_mtime_ns
    assert variant_data.write_text_if_changed(path, "same") is False
    assert path.stat().st_mtime_ns == before, "identical content was rewritten"

    assert variant_data.write_text_if_changed(path, "different") is True
    assert path.read_text(encoding="utf-8") == "different"
