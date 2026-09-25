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
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

import variant_data  # noqa: E402

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
    ],
)
def test_unsupported_grammar_raises(tmp_path: Path, body: str, because: str) -> None:
    root = _write_parts(tmp_path, body)
    with pytest.raises(ValueError):
        variant_data.components(root, "Fake", "test")


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
        "if(BUILD_KIT STREQUAL test)\n"
        "  spl_add_component(test/suite)\n"
        "else()\n"
        "  spl_add_component(components/stub)\n"
        "endif()\n",
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
    assert data["features"]

    # It has to survive the round trip to the file both tools read.
    assert json.loads(json.dumps(data)) == data


# --- the current-variant pointer -------------------------------------------


def test_the_pointer_is_a_symlink_where_the_platform_allows_one(tmp_path: Path) -> None:
    """A symlink is cheap and clear where the OS permits one."""
    build_dir = tmp_path / "build" / "V" / "test" / "Debug"
    build_dir.mkdir(parents=True)
    (build_dir / "payload.txt").write_text("x", encoding="utf-8")

    variant_data.write_pointer(tmp_path, {"features": {}, "build_config": {}}, build_dir)

    generated = tmp_path / "generated"
    assert generated.is_symlink()
    assert (generated / "payload.txt").is_file()


def test_a_refused_symlink_falls_back_to_a_junction(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Windows without Developer Mode refuses a symlink but allows a junction.

    The junction is the fallback that keeps Sphinx able to walk `generated`
    without copying the binary directory. Only Windows takes this path, which is
    why it needs a test rather than the platform nobody develops on finding out.
    """
    build_dir = tmp_path / "build" / "V" / "test" / "Debug"
    (build_dir / "CMakeFiles").mkdir(parents=True)
    (build_dir / "CMakeFiles" / "huge.o").write_text("x" * 1000, encoding="utf-8")

    calls: list[tuple[Path, Path]] = []

    def refuse(*args, **kwargs):
        raise OSError("symlinks not permitted")

    def fake_junction(target: Path, link: Path) -> None:
        calls.append((target, link))
        link.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(Path, "symlink_to", refuse)
    monkeypatch.setattr(variant_data, "_create_junction", fake_junction)

    variant_data.write_pointer(tmp_path, {"features": {}, "build_config": {}}, build_dir)

    generated = tmp_path / "generated"
    assert calls == [(build_dir.resolve(), generated)], "the junction must lead to the resolved build directory"
    assert generated.is_dir() and not generated.is_symlink()
    assert not (generated / "NO_SYMLINK").exists(), "the junction is a real link, not an explanation"
    assert not (generated / "CMakeFiles").exists(), "the fallback copied the binary directory"


def test_neither_link_leaves_an_explained_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """When both link types fail, the path still exists and says why.

    spl-core stops a documentation build whose `generated` does not lead to its
    build directory, so the failure has to be a named one rather than a missing
    path -- and copying the binary directory, as the old fallback did, would
    leak build objects into the source tree without producing the reports.
    """
    build_dir = tmp_path / "build" / "V" / "test" / "Debug"
    (build_dir / "CMakeFiles").mkdir(parents=True)
    (build_dir / "CMakeFiles" / "huge.o").write_text("x" * 1000, encoding="utf-8")

    def refuse(*args, **kwargs):
        raise OSError("no links here")

    monkeypatch.setattr(Path, "symlink_to", refuse)
    monkeypatch.setattr(variant_data, "_create_junction", refuse)

    variant_data.write_pointer(tmp_path, {"features": {}, "build_config": {}}, build_dir)

    generated = tmp_path / "generated"
    assert generated.is_dir() and not generated.is_symlink()
    assert [p.name for p in generated.iterdir()] == ["NO_SYMLINK"]
    assert str(build_dir.resolve()) in (generated / "NO_SYMLINK").read_text(encoding="utf-8")
    assert not (generated / "CMakeFiles").exists(), "the fallback copied the binary directory"


def test_repointing_generated_leaves_the_old_build_untouched(tmp_path: Path) -> None:
    """Re-pointing the link must never touch the directory it used to lead to.

    `_remove_link` removes the link itself, not its target, so switching from
    one configured variant to another does not delete the previous build. A
    `shutil.rmtree` on the resolved target would, silently, on every reconfigure.
    """
    first = tmp_path / "build" / "first"
    second = tmp_path / "build" / "second"
    for build_dir, name in ((first, "first.txt"), (second, "second.txt")):
        build_dir.mkdir(parents=True, exist_ok=True)
        (build_dir / name).write_text(name, encoding="utf-8")

    variant_data.write_pointer(tmp_path, {"features": {}, "build_config": {}}, first)
    generated = tmp_path / "generated"
    assert (generated / "first.txt").is_file()

    variant_data.write_pointer(tmp_path, {"features": {}, "build_config": {}}, second)
    assert generated.resolve() == second.resolve()
    assert (generated / "second.txt").is_file()

    assert first.is_dir(), "the old build directory was removed"
    assert (first / "first.txt").read_text(encoding="utf-8") == "first.txt"
