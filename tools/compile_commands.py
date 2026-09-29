#!/usr/bin/env python3
"""Hand codelinks the selected build's compile database.

codelinks evaluates each source file's `#ifdef` branches with the build's compile
database, so a variant's one-line needs are the ones that variant compiles. Both
readers take the database from one fixed path, `build/compile_commands.json`
(ubproject.toml), because the path cannot follow the selection: `extend` and
ubc's `-c` both replace a codelinks project's whole table rather than one key in
it. CMake writes the database only into its build directory, so this copies it
to that path -- for the selected build only, the one `build/selection.toml`
mounts, so building another variant leaves the editor's database alone.

The test kit compiles with `-save-temps`, which libclang cannot load a file with:
codelinks would skip every file, and its needs would disappear. The copy leaves
that option out. Once codelinks drops it itself, the filter can go.

Run by the `spled_codelinks_compile_commands` target (CMakeLists.txt) on every
build, and after a configure without a build:

    cmake --build <build dir> --target spled_codelinks_compile_commands
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent

#: Where codelinks reads the database (ubproject.toml).
TARGET = "build/compile_commands.json"

#: The selection whose build directory is the one to copy from.
SELECTION = "build/selection.toml"

#: `-save-temps` and `-save-temps=obj|cwd`, as a whole token.
_SAVE_TEMPS = re.compile(r"(?<!\S)-save-temps(?:=\S+)?(?:\s+|$)")


def selected_build_dir(project_root: Path) -> Path | None:
    """The build directory the selection mounts, or None if it names no build."""
    path = project_root / SELECTION
    if not path.is_file():
        return None
    mounts = tomllib.loads(path.read_text(encoding="utf-8")).get("source", {}).get("mounts", [])
    return Path(mounts[0]["dir"]).resolve() if mounts else None


def without_save_temps(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for entry in entries:
        entry = dict(entry)
        if "command" in entry:
            entry["command"] = _SAVE_TEMPS.sub("", entry["command"]).rstrip()
        if "arguments" in entry:
            entry["arguments"] = [argument for argument in entry["arguments"] if not _SAVE_TEMPS.fullmatch(argument)]
        result.append(entry)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--build-dir", type=Path, required=True, help="CMake binary dir whose database to copy")
    args = parser.parse_args(argv)

    project_root: Path = args.project_root.resolve()
    build_dir: Path = args.build_dir.resolve()
    if selected_build_dir(project_root) != build_dir:
        print(f"{build_dir} is not the selected build; {TARGET} is left as it is")
        return 0
    source = build_dir / "compile_commands.json"
    if not source.is_file():
        print(f"{source} does not exist yet; {TARGET} is left as it is")
        return 0

    text = json.dumps(without_save_temps(json.loads(source.read_text(encoding="utf-8"))), indent=2) + "\n"
    target = project_root / TARGET
    if not target.is_file() or target.read_text(encoding="utf-8") != text:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        print(f"wrote {TARGET} from {source}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
