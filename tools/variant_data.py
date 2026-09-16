#!/usr/bin/env python3
"""Write the variant data files that every documentation tool reads.

One generation step, one artefact per build shape, and nothing downstream needs
Python to decide anything: `ubproject.toml` conditions and the `{if}` directives
in the documents read these files, and so do `sphinx-build`, `ubc` and the
ubCode language server. The rule that follows from that is the only one worth
remembering here:

    everything a condition may name has to be IN the file.

A key that only `conf.py` knows is invisible to every other reader, and their
view of the project then silently disagrees with the build. That is why this
writes the complete feature vector -- including the booleans KConfig omits --
plus the build shape, rather than leaving any of it to be synthesized later.

Layout::

    build/variants/<Variant>/<kit>/<target>.json    the matrix
    build/variants/GENERATED                        marker; nobody edits generated output
    build/autoconf.json                             the "current" pointer, one cell of the matrix
    generated/                                      symlink to the current cell's build directory

Nothing here needs a compiler. KConfig is pure Python, while CMake's top-level
`project()` call demands a C toolchain before it will even configure -- so with
this script the documentation and its quality gate can be built on a machine
that cannot build the software.

Usage::

    python tools/variant_data.py --all
    python tools/variant_data.py --variant Disco --kit test --target reports --current
    python tools/variant_data.py --all --check      # CI: regenerate and diff
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent

#: Components a variant's `parts.cmake` adds only for the test build kit.
TEST_KIT_GUARD = "BUILD_KIT STREQUAL test"

#: The build shapes spl-core builds. `docs` is the design documentation of a
#: variant; `reports` additionally carries the generated test and coverage
#: output, which is why documents gate report sections on it.
TARGETS = ("docs", "reports")

#: The build kits. `components` differs between them, because a variant's
#: parts.cmake adds its test suites only for `test`.
KITS = ("prod", "test")


def _spl_core_dir() -> Path:
    import spl_core

    return Path(spl_core.__file__).parent


def variant_names(project_root: Path) -> list[str]:
    """Every variant in `variants/`, as the slash-separated name CMake uses.

    A variant is a directory holding a `config.cmake`; it may be one level deep
    (`Disco`) or two (`Base/Dev`), which is why this walks rather than lists.
    """
    variants_dir = project_root / "variants"
    return sorted(
        str(path.parent.relative_to(variants_dir)).replace(os.sep, "/")
        for path in variants_dir.rglob("config.cmake")
    )


def _declared_boolean_symbols(kconfig: Any) -> list[str]:
    """Every boolean the feature model declares, however spl-core lets us ask.

    spl-core grew a public `declared_boolean_symbols()` for exactly this, but
    this project must keep working against the version pinned in
    pyproject.toml -- which is what CI installs and therefore what "works"
    means. Depending on an unreleased accessor would make the build pass only
    on a machine with a local checkout, which is the same class of mistake as
    a configuration only one reader can evaluate.

    So: use the accessor when it is there, and otherwise read the kconfiglib
    instance spl-core holds. Drop the fallback once pyproject.toml pins a
    release that has the method.
    """
    if hasattr(kconfig, "declared_boolean_symbols"):
        return kconfig.declared_boolean_symbols()

    import kconfiglib

    return sorted(
        name
        for name, symbol in kconfig._config.syms.items()  # noqa: SLF001 - see docstring
        if name and symbol.orig_type == kconfiglib.BOOL
    )


def features(project_root: Path, variant: str) -> dict[str, Any]:
    """The variant's complete feature vector.

    Every boolean the feature model declares is present, defaulted to False,
    before the variant's own values are overlaid. KConfig writes a boolean into
    its JSON only when the symbol has a prompt or evaluates to y, so a helper
    symbol such as BRIGHTNESS_ADJUSTMENT_ENABLED is simply absent from the
    variants where it is off -- and a condition naming it would fail to evaluate
    for exactly those variants, which both tools then report as unevaluable and
    gate off rather than cleanly answering False.
    """
    from spl_core.kconfig.kconfig import JsonWriter, KConfig

    os.environ.setdefault("SPL_CORE_DIR", str(_spl_core_dir()))
    os.environ.setdefault("srctree", str(project_root))

    model_file = project_root / "KConfig"
    config_file = project_root / "variants" / variant / "config.txt"

    kconfig = KConfig(
        model_file,
        config_file if config_file.exists() else None,
        project_root,
    )

    # `KConfig.config` only carries the symbols KConfig would write out. The
    # model itself knows every symbol, which is what makes the vector complete.
    defaults = dict.fromkeys(_declared_boolean_symbols(kconfig), False)

    # spl-core's own JSON writer, so the value conversion (tristates to bool,
    # hex, the ${VAR} substitution) is the build's and not a second opinion.
    # `generate_content` is the pure half of it; nothing is written here.
    values = json.loads(JsonWriter(Path(os.devnull)).generate_content(kconfig.config))["features"]
    return {**defaults, **values}


def components(project_root: Path, variant: str, kit: str) -> list[str]:
    """The components the variant's `parts.cmake` adds for this build kit.

    Parsed rather than imported, because the point is to state the product
    structure once, in the file that already states it. The grammar every
    parts.cmake in this project uses is a flat list of `spl_add_component()`
    calls, optionally with one `if(BUILD_KIT STREQUAL test)` / `else()` /
    `endif()` block.

    Anything outside that grammar raises. A parser that shrugged at an `if()`
    it did not understand would treat the guarded body as unconditional and
    hand back a component list that is quietly wrong for some kit -- and since
    this list is what gates the documents, the failure would surface as
    documents silently missing from a variant, which is the hardest kind of
    wrong to notice. Better to stop and make someone either extend the grammar
    or derive the list from CMake.
    """
    parts = project_root / "variants" / variant / "parts.cmake"
    result: list[str] = []
    #: None outside any if-block, else the kit whose branch we are currently in.
    branch_kit: str | None = None
    depth = 0

    for number, raw_line in enumerate(parts.read_text().splitlines(), start=1):
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        lowered = line.lower()
        where = f"{parts.relative_to(project_root)}:{number}"

        if lowered.startswith(("if(", "if ")):
            if depth or TEST_KIT_GUARD.lower() not in lowered:
                raise ValueError(
                    f"{where}: unsupported condition {line!r}. "
                    f"{parts.name} may only use a single, non-nested "
                    f"`if({TEST_KIT_GUARD})` block; extend the grammar in "
                    "tools/variant_data.py (and its test) deliberately."
                )
            depth += 1
            branch_kit = "test"
            continue
        if lowered.startswith(("else(", "else ", "else")) and not lowered.startswith("elseif"):
            if not depth:
                raise ValueError(f"{where}: `else()` outside any `if()`.")
            # The other side of the test-kit guard is every kit that is not test.
            branch_kit = "prod"
            continue
        if lowered.startswith("elseif"):
            raise ValueError(f"{where}: `elseif()` is not supported, see above.")
        if lowered.startswith(("endif(", "endif ", "endif")):
            if not depth:
                raise ValueError(f"{where}: `endif()` without `if()`.")
            depth -= 1
            branch_kit = None
            continue
        if lowered.startswith("spl_add_component("):
            if branch_kit is not None and branch_kit != kit:
                continue
            result.append(line[len("spl_add_component(") : line.rindex(")")].strip())
            continue

        raise ValueError(
            f"{where}: unsupported statement {line!r}. {parts.name} may only "
            "contain `spl_add_component()` calls and the test-kit guard."
        )

    if depth:
        raise ValueError(f"{parts.relative_to(project_root)}: unterminated `if()`.")

    return result


def variant_data(project_root: Path, variant: str, kit: str, target: str) -> dict[str, Any]:
    """One cell of the matrix: everything a condition anywhere may name."""
    return {
        "features": features(project_root, variant),
        "build_config": {
            "variant": variant,
            "kit": kit,
            "target": target,
            "components": components(project_root, variant, kit),
        },
    }


def cell_path(project_root: Path, variant: str, kit: str, target: str) -> Path:
    return project_root / "build" / "variants" / variant / kit / f"{target}.json"


def write_cell(project_root: Path, variant: str, kit: str, target: str, data: dict[str, Any]) -> Path:
    path = cell_path(project_root, variant, kit, target)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    return path


def write_pointer(project_root: Path, data: dict[str, Any], build_dir: Path | None) -> None:
    """Point `build/autoconf.json` and `generated` at one cell.

    `ubproject.toml` names both: the data file as `variant_data_file`, and the
    build directory as the `dir` of the report mount. A mount `dir` is resolved
    relative to the configuration file and cannot name variant data, so the
    indirection has to be on the filesystem.

    The link is called `generated` and sits at the project root rather than
    inside `build/`, and that name is load-bearing twice over. It is the docname
    prefix of every generated page in BOTH tools: sphinx-mounts renames a mount's
    documents to its `mount_at`, while ubCode keeps the path a file is found at,
    so the only way one toctree entry can mean one page in both is for the path
    and the prefix to be the same string. And ubCode's default `exclude` contains
    "build", which would otherwise drop the whole mounted tree.

    KNOWN LIMITATION: a symlink gets this right for Sphinx and wrong for ubCode,
    which does not descend symlinked directories. The generated report pages are
    therefore invisible to the IDE. Materialising them -- copying the .rst files
    into a real `generated/` tree after the reports target has produced them --
    is the fix, and it has to happen after that target runs, not here at
    configure time when they do not exist yet. Pointing `generated` at a real
    directory makes ubCode index them, gated exactly as intended.
    """
    pointer = project_root / "build" / "autoconf.json"
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")

    if build_dir is None:
        return

    current = project_root / "generated"
    if current.is_symlink() or current.is_file():
        current.unlink()
    elif current.is_dir():
        shutil.rmtree(current)
    try:
        current.symlink_to(build_dir.resolve(), target_is_directory=True)
    except OSError:
        # Windows without Developer Mode refuses a symlink. A copy keeps the
        # path stable at the cost of duplicating the tree; the reports target
        # rewrites its output wholesale anyway.
        shutil.copytree(build_dir, current, dirs_exist_ok=True)


#: Dropped into every directory this script owns. `build/` itself gets one too,
#: because that is the directory somebody is most likely to open and edit in.
GENERATED_MARKER = (
    "Written by tools/variant_data.py. Everything under build/ is generated\n"
    "output: nobody edits it, neither a person nor an assistant.\n"
)


def mark_generated(project_root: Path) -> None:
    for directory in (project_root / "build", project_root / "build" / "variants"):
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "GENERATED").write_text(GENERATED_MARKER)


def _check(project_root: Path, selected: list[str]) -> int:
    """Regenerate in memory and report cells that are missing or stale.

    The gate this serves is "the variant data on disk is what the sources say
    it is". It has to be a comparison rather than a regeneration, because a
    regeneration always passes: it would simply overwrite the drift it was
    meant to catch and report success.
    """
    stale: list[str] = []
    for variant in selected:
        for kit in KITS:
            for target in TARGETS:
                expected = json.dumps(variant_data(project_root, variant, kit, target), indent=2, sort_keys=True) + "\n"
                path = cell_path(project_root, variant, kit, target)
                rel = path.relative_to(project_root)
                if not path.exists():
                    stale.append(f"{rel}: missing")
                elif path.read_text() != expected:
                    stale.append(f"{rel}: stale")

    if stale:
        print("variant data is not up to date:", file=sys.stderr)
        for line in stale:
            print(f"  {line}", file=sys.stderr)
        print("\nrun: python tools/variant_data.py --all", file=sys.stderr)
        return 1

    print(f"variant data up to date ({len(selected)} variants x {len(KITS)} kits x {len(TARGETS)} targets)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--all", action="store_true", help="generate the whole matrix")
    parser.add_argument("--variant", help="variant name, e.g. Disco or Base/Dev")
    parser.add_argument("--kit", choices=KITS, default="prod")
    parser.add_argument("--target", choices=TARGETS, default="docs")
    parser.add_argument(
        "--current",
        action="store_true",
        help="also write build/autoconf.json and the `generated` link for the selected cell",
    )
    parser.add_argument(
        "--build-dir",
        type=Path,
        help="CMake binary dir of the selected cell; `generated` points at it",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="do not write: compare what would be generated against what is on disk",
    )
    args = parser.parse_args(argv)

    project_root: Path = args.project_root.resolve()

    if not args.all and not args.variant:
        parser.error("either --all or --variant is required")

    selected = variant_names(project_root) if args.all else [args.variant]

    if args.check:
        return _check(project_root, selected)

    for variant in selected:
        for kit in KITS:
            for target in TARGETS:
                data = variant_data(project_root, variant, kit, target)
                path = write_cell(project_root, variant, kit, target, data)
                print(f"wrote {path.relative_to(project_root)}")

    mark_generated(project_root)

    if args.current or not args.all:
        data = variant_data(project_root, args.variant or selected[0], args.kit, args.target)
        write_pointer(project_root, data, args.build_dir)
        print(f"current -> {args.variant or selected[0]} / {args.kit} / {args.target}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
