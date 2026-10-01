#!/usr/bin/env python3
"""Try SPLed's variant documentation end to end, on Linux, macOS or Windows.

Every step says what it is about to do, runs it, and then says what to look at
and what to expect. Nothing is installed outside the repository except uv's
cache (and a uv-managed CPython 3.12 if none is found); the build scripts and
the bootstrap scripts are not used.

    python tools/try_variants.py setup                 # .venv and the variant data
    python tools/try_variants.py docs   [-v Sleep]     # one variant's documents, both readers, no compiler
    python tools/try_variants.py build  [-v Disco]     # a CMake build: reports, test results, listings
    python tools/try_variants.py component light_controller [-v Disco]
    python tools/try_variants.py compare Disco Spa     # what differs between two variants
    python tools/try_variants.py check                 # the tests and the CI documentation gate
    python tools/try_variants.py all                   # setup, docs, build, compare, check

Needs: Python 3.11+ and uv to start with; `ubc` (from the ubCode VS Code
extension) for the ubCode side; CMake, Ninja and a C/C++ compiler for `build`.
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import time
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WINDOWS = platform.system() == "Windows"
VENV_BIN = ROOT / ".venv" / ("Scripts" if WINDOWS else "bin")
PYTHON = VENV_BIN / ("python.exe" if WINDOWS else "python")
OUT = ROOT / "build" / "try"

# --- presentation ---------------------------------------------------------------

sys.stdout.reconfigure(line_buffering=True)  # our lines and the commands' output stay in order
_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
if WINDOWS and _COLOR:
    os.system("")  # enables ANSI escape codes in the Windows console


def _paint(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _COLOR else text


def step(title: str, now: str) -> None:
    print("\n" + _paint("1;36", f"━━ {title} " + "━" * max(0, 70 - len(title))))
    print(_paint("36", "What happens now: ") + now)


def look(*lines: str) -> None:
    print(_paint("1;32", "What to look at:"))
    for line in lines:
        print("  " + _paint("32", "•") + " " + line)


def note(text: str) -> None:
    print(_paint("33", "Note: ") + text)


def fail(text: str) -> None:
    print(_paint("1;31", "Stopped: ") + text)
    sys.exit(1)


def run(*command: str | Path, quiet: bool = False, check: bool = True, env: dict | None = None, shown: str | None = None) -> subprocess.CompletedProcess:
    if shown is None:
        parts = [rel(part) if isinstance(part, Path) else part for part in command]
        shown = " ".join(part if " " not in part else f'"{part}"' for part in parts)
    print(_paint("2", f"  $ {shown}"))
    started = time.perf_counter()
    result = subprocess.run(
        [str(part) for part in command],
        cwd=ROOT,
        env={**os.environ, "PATH": f"{VENV_BIN}{os.pathsep}{os.environ['PATH']}", **(env or {})},
        capture_output=quiet,
        text=True,
        check=False,
    )
    seconds = time.perf_counter() - started
    if check and result.returncode != 0:
        if quiet:
            print((result.stdout or "")[-3000:] + (result.stderr or "")[-3000:])
        fail(f"the command above failed (exit {result.returncode}).")
    print(_paint("2", f"    done in {seconds:.1f} s"))
    return result


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)


# --- tools ------------------------------------------------------------------------


def find_ubc() -> str | None:
    for candidate in (os.environ.get("UBC"), shutil.which("ubc")):
        if candidate and Path(candidate).is_file():
            return candidate
    for extension in sorted((Path.home() / ".vscode" / "extensions").glob("useblocks.ubcode-*"), reverse=True):
        for name in ("ubc.exe", "ubc"):
            if (extension / "server" / "cli" / name).is_file():
                return str(extension / "server" / "cli" / name)
    return None


def need_venv() -> None:
    if not PYTHON.is_file():
        fail("there is no .venv yet. Run `python tools/try_variants.py setup` first.")


def needs_count(needs_json: Path) -> int:
    import json

    data = json.loads(needs_json.read_text(encoding="utf-8"))
    return len(data["versions"][data.get("current_version", "")]["needs"])


def selection_summary() -> str:
    path = ROOT / "build" / "selection.toml"
    if not path.is_file():
        return "nothing selected"
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    cell = Path(data["needs"]["variant_data_file"])
    mounts = data.get("source", {}).get("mounts", [])
    shown = "/".join(cell.parts[cell.parts.index("variants") + 1 :]) if "variants" in cell.parts else str(cell)
    return f"cell {shown}" + (f", build {rel(Path(mounts[0]['dir']))} mounted at generated" if mounts else ", no build mounted")


def build_dir(variant: str, kit: str) -> Path:
    return ROOT / "build" / variant / kit / "Debug"


def have_cmake() -> bool:
    return bool(shutil.which("cmake") and shutil.which("ninja"))


def configure(variant: str, kit: str) -> Path:
    """Configure a cell's build, which selects it, and hand codelinks its compile database."""
    target = build_dir(variant, kit)
    command = ["cmake", "-S", ".", "-B", target, "-G", "Ninja", f"-DVARIANT={variant}", f"-DBUILD_KIT={kit}", "-DCMAKE_BUILD_TYPE=Debug"]
    if kit == "test":
        toolchain = "toolchain.cmake" if WINDOWS else "toolchain_linux.cmake"
        command.append(f"-DCMAKE_TOOLCHAIN_FILE=tools/toolchains/gcc/{toolchain}")
    run(*command, quiet=True)
    run("cmake", "--build", target, "--target", "spled_codelinks_compile_commands", quiet=True)
    return target


# --- the cases --------------------------------------------------------------------


def do_setup(args: argparse.Namespace) -> None:
    step("1. Setup", "a .venv inside the repository with the locked dependencies, then the variant data every reader reads.")
    if not shutil.which("uv"):
        fail("uv is not on PATH. Install it from https://docs.astral.sh/uv/ and run this again.")
    if not PYTHON.is_file():
        run("uv", "venv", "--python", "3.12", ".venv")
    run("uvx", "--from", "poetry==2.4.1", "poetry", "install", "--no-root", "--no-interaction", env={"POETRY_VIRTUALENVS_IN_PROJECT": "true"})
    run(PYTHON, "tools/variant_data.py", "--all", "--current", "--variant", args.variant, "--kit", args.kit, quiet=True)
    look(
        "build/variants/<variant>/<kit>/<target>.json — the variant data, one file per cell (open one: features and components).",
        "ubproject.variants.toml — the document rules, one per component, generated: nothing to maintain by hand.",
        f"build/selection.toml — what the editor and a plain build show now: {selection_summary()}.",
        "Open the folder in VS Code with the ubCode extension: it reads exactly these files.",
    )
    if not find_ubc():
        note("ubc was not found (PATH, $UBC or the ubCode extension folder); the ubCode side of the other steps is skipped.")


def do_docs(args: argparse.Namespace) -> None:
    need_venv()
    cell = ROOT / "build" / "variants" / args.variant / args.kit / "docs.json"
    step(
        f"2. Documents of {args.variant}/{args.kit}, nothing compiled",
        "both readers build the same variant from the same data file: Sphinx, then ubc. CMake only configures the variant, for its compile database: nothing is compiled.",
    )
    if have_cmake():
        configure(args.variant, args.kit)
    else:
        run(PYTHON, "tools/variant_data.py", "--all", "--current", "--variant", args.variant, "--kit", args.kit, quiet=True)
        note("no CMake/Ninja: the one-line needs in the code follow whichever compile database build/compile_commands.json holds, which may be another variant's #ifdef branches.")
    out = OUT / f"docs-{args.variant.replace('/', '-')}-{args.kit}"
    run(PYTHON, "-m", "sphinx", "-q", "-b", "html", "-D", f"needs_variant_data_file={rel(cell)}", "-d", out / "doctrees", ".", out / "sphinx", env={"VARIANT": args.variant})
    ubc = find_ubc()
    if ubc:
        run(ubc, "build", "html", "--no-cache", "--deny", "none", "-o", out / "ubc", "-c", f"needs.variant_data_file = '{rel(cell)}'", quiet=True)
    look(
        f"{rel(out / 'sphinx' / 'index.html')} — the Sphinx build: {needs_count(out / 'sphinx' / 'needs.json')} needs.",
        *(
            [
                (
                    f"{rel(out / 'ubc' / 'index.html')} — the ubc build of the same variant: {needs_count(out / 'ubc' / 'needs.json')} needs "
                    "(the two untitled imports REQ_37/REQ_58 are the only difference)."
                )
            ]
            if ubc
            else []
        ),
        "The components page lists exactly this variant's components (a glob, gated by the generated rules).",
        "Each component page ends with Traceability: its one-line @need comments from the C sources.",
        f"build/selection.toml — your editor now shows this variant too: {selection_summary()}.",
    )


def do_build(args: argparse.Namespace) -> None:
    need_venv()
    for tool in ("cmake", "ninja"):
        if not shutil.which(tool):
            fail(f"{tool} is not on PATH; the build case needs CMake, Ninja and a C/C++ compiler.")
    target = build_dir(args.variant, args.kit)
    step(
        f"3. A CMake build of {args.variant}/{args.kit}",
        "configuring the build SELECTS it (build/selection.toml mounts it at `generated`); building it compiles, "
        "runs the unit tests and writes the report pages, source listings and test results as needs.",
    )
    configure(args.variant, args.kit)
    run("cmake", "--build", target, "--target", "reports" if args.kit == "test" else "docs", quiet=True)
    html = target / ("reports" if args.kit == "test" else "docs") / "html"
    look(
        f"{rel(html / 'index.html')} — the report spl-core built: test results and coverage under each component ({needs_count(html / 'needs.json')} needs).",
        f"build/selection.toml — {selection_summary()}.",
        f"{rel(target / 'selection')}/ — one selection file per documentation run, so two builds never get in each other's way.",
        "build/compile_commands.json — this build's compile database: codelinks takes each #ifdef branch from it.",
        "`sphinx-build -b html . <out>` now shows this build, generated pages included, without any option.",
    )
    note("ubc and the IDE do not show the generated pages yet: ubCode does not mount a directory inside the project.")


def do_component(args: argparse.Namespace) -> None:
    need_venv()
    path = args.component if "/" in args.component else f"components/{args.component}"
    target = build_dir(args.variant, "test")
    selection = target / "selection" / path / "reports.toml"
    if not selection.is_file():
        fail(f"{rel(selection)} does not exist; run `build -v {args.variant}` first, and check that {path} is in {args.variant}.")
    step(f"4. The report of {path} alone", "spl-core's per-component report, from that component's own selection file, in both readers.")
    name = path.replace("/", "_")
    run("cmake", "--build", target, "--target", f"{name}_report", quiet=True)
    html = target / path / "reports" / "html"
    ubc = find_ubc()
    out = OUT / f"component-{name}"
    if ubc:
        run(
            ubc,
            "build",
            "html",
            "--no-cache",
            "--deny",
            "none",
            "-o",
            out,
            "-c",
            selection.read_text(encoding="utf-8"),
            quiet=True,
            shown=f'ubc build html --no-cache --deny none -o {rel(out)} -c "$(cat {rel(selection)})"',
        )
    look(
        f"{rel(html / 'doc' / 'component_report.html')} — Sphinx: {needs_count(html / 'needs.json')} needs, all of this component.",
        *([f"{rel(out / 'doc' / 'component_report.html')} — ubc: {needs_count(out / 'needs.json')} needs (its documents; the generated pages are the known gap)."] if ubc else []),
        f"{rel(selection)} — the file that makes it a component report: its variant data (scope = component) and its root document.",
    )


def do_compare(args: argparse.Namespace) -> None:
    need_venv()
    ubc = find_ubc()
    if not ubc:
        fail("compare needs ubc.")
    a, b = (ROOT / "build" / "variants" / v / args.kit / "docs.json" for v in (args.first, args.second))
    step(
        f"5. {args.first} against {args.second}",
        "ubc builds both variants' needs and lists what is new, removed or changed. "
        "Each variant is configured first, so the needs in the code follow its own #ifdef branches; "
        "your selection is put back afterwards.",
    )
    run(PYTHON, "tools/variant_data.py", "--all", quiet=True)
    OUT.mkdir(parents=True, exist_ok=True)
    saved = {path: path.read_bytes() if path.is_file() else None for path in (ROOT / "build" / "selection.toml", ROOT / "build" / "compile_commands.json")}
    try:
        for variant, cell, name in ((args.first, a, "first"), (args.second, b, "second")):
            if have_cmake():
                configure(variant, args.kit)
            run(ubc, "build", "needs", "--no-cache", "-c", f"needs.variant_data_file = '{rel(cell)}'", "-o", OUT / f"{name}.json", quiet=True)
    finally:
        for path, content in saved.items():
            if content is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(content)
    result = run(ubc, "diff", "--no-cache", "-n", OUT / "first.json", "-n", OUT / "second.json", quiet=True, check=False)
    lines = [line for line in result.stdout.splitlines() if line.startswith(("New need", "Removed need", "Changed need"))]
    print("\n".join(f"    {line}" for line in lines[:30]) + ("\n    …" if len(lines) > 30 else ""))
    look(
        f"{len(lines)} differences: the needs of components and features one variant has and the other has not.",
        'The same comparison for whole builds, reports included: ubc diff -c "$(cat build/<variant>/test/Debug/selection/reports.toml)".',
    )


def do_check(args: argparse.Namespace) -> None:
    need_venv()
    step("6. The checks", "the configuration and generator tests, then the CI documentation gate: every variant and kit, both readers in strict mode, their needs compared.")
    run(PYTHON, "-m", "pytest", "-q", "-p", "no:cacheprovider", "test/test_ubproject_config.py", "test/test_variant_data.py")
    if have_cmake() and find_ubc():
        run(PYTHON, "-m", "pytest", "-q", "-p", "no:cacheprovider", "test/test_docs_gate.py")
        look("Every gate run passes: each variant cell and each component report, Sphinx -W and ubc agreeing need for need.", "The gate restores your selection afterwards.")
    else:
        note("the gate needs CMake, Ninja, a compiler and ubc; skipped.")


def do_all(args: argparse.Namespace) -> None:
    do_setup(args)
    do_docs(argparse.Namespace(variant="Sleep", kit="test"))
    do_build(argparse.Namespace(variant="Disco", kit="test"))
    do_component(argparse.Namespace(variant="Disco", component="light_controller"))
    do_compare(argparse.Namespace(first="Disco", second="Spa", kit="test"))
    do_check(args)
    print("\n" + _paint("1;36", "━━ Done ") + _paint("36", f"Everything under {rel(OUT)}/; your selection: {selection_summary()}."))


class _Parser(argparse.ArgumentParser):
    """On a usage error, the whole help of the case, not just one line."""

    def error(self, message: str) -> None:
        self.print_help(sys.stderr)
        self.exit(2, "\n" + _paint("1;31", "Error: ") + message + "\n")


def variants() -> list[str]:
    return sorted(p.parent.relative_to(ROOT / "variants").as_posix() for p in (ROOT / "variants").glob("**/config.txt"))


def main() -> None:
    known = ", ".join(variants())
    parser = _Parser(
        prog="python tools/try_variants.py",
        description=__doc__.split("\n\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n\n", 1)[1] + f"\nVariants: {known}.",
    )
    cases = parser.add_subparsers(dest="case", metavar="<case>", parser_class=_Parser)

    def add(name: str, function, summary: str, variant: bool = True, kit: bool = True) -> argparse.ArgumentParser:
        case = cases.add_parser(name, help=summary, description=summary, epilog=f"Variants: {known}.")
        if variant:
            case.add_argument("-v", "--variant", default="Disco", metavar="VARIANT", help="default: Disco")
        if kit:
            case.add_argument("-k", "--kit", default="test", choices=("prod", "test"), help="default: test")
        case.set_defaults(function=function)
        return case

    add("setup", do_setup, "create .venv with the locked dependencies and generate the variant data")
    add("docs", do_docs, "build one variant's documents in Sphinx and ubc, compiling nothing")
    add("build", do_build, "configure and build a variant with CMake: reports, test results, listings")
    case = add("component", do_component, "build the report of one component of a built variant", kit=False)
    case.add_argument("component", help="e.g. light_controller, or test/spled_integration")
    case = add("compare", do_compare, "list the needs that differ between two variants (ubc diff)", variant=False)
    case.add_argument("first", metavar="VARIANT_A")
    case.add_argument("second", metavar="VARIANT_B")
    add("check", do_check, "run the configuration tests and the CI documentation gate")
    add("all", do_all, "setup, docs (Sleep), build (Disco), component, compare (Disco/Spa), check")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    args = parser.parse_args()
    if args.case is None:
        parser.print_help()
        sys.exit(0)
    args.function(args)


if __name__ == "__main__":
    main()
