# SPLED: Software Product Line Engineering Demo

## Architecture Overview

SPLED is a **Software Product Line (SPL)** demonstrating variant-based configuration management.
Each variant (Disco, Sleep, Spa, etc.) compiles into separate binaries using shared components with different feature configurations.

**Key architectural concepts:**

- **Variants**: Product configurations in `variants/<VariantName>/` containing `config.txt` (KConfig features), `parts.cmake` (component selection), and `config.cmake` (CMake settings)
- **Components**: Modular C code in `components/<name>/` with CMakeLists.txt using SPL-specific macros
- **Build Kits**: `prod` (production C code) vs `test` (C++ with GoogleTest for unit testing)
- **Feature Configuration**: KConfig system (`KConfig` file) drives conditional compilation via CMake variables

## Critical Developer Workflows

### Environment Setup

**Always** run `.\build.ps1 -install` when:

- First cloning the repository
- Switching branches (dependencies may have changed)
- After pulling updates

On **Linux/macOS or inside a devcontainer**, use the peer script `./build.sh --install`. `build.sh` performs the same steps as `build.ps1`, so every build/test workflow below has a `build.sh` equivalent. The flag *vocabulary* is close but not identical (Bash uses `--flag`, PowerShell uses `-flag`):

| `build.ps1` | `build.sh` |
| --- | --- |
| `-install`, `-build`, `-clean`, `-selftests`, `-marker`, `-filter`, `-target`, `-command`, `-reconfigure` | same names, `--` prefixed |
| `-variants <v>` | `--variant <v>` (single variant; default `Disco`) |
| `-buildKit <k>` / `-buildType <t>` | `--build-kit <k>` / `--build-type <t>` |
| `-startVSCode`, `-installVSCode`, `-installOptional`, `-configureOnly`, `-pytestExtraArgs`, `-ninjaArgs`, `-waitForKey` | *no equivalent* |

`./build.sh --help` is authoritative for the Bash side.

On a **bare Linux host (e.g. WSL Ubuntu) that is not a devcontainer**, `build.sh --install` assumes some OS-level prerequisites already exist. Provision them once per machine with the two bootstrap scripts — the devcontainer image runs the same scripts, so this is a single source of truth (see [`doc/devcontainer-and-bootstrap-design.md`](doc/devcontainer-and-bootstrap-design.md)):

```bash
sudo ./bootstrap_ubuntu.sh    # root: apt packages (libc6-dev, build-essential, 7zip, pipx)
./bootstrap_python.sh         # user: uv, CPython 3.12, Poetry (into ~/.local)
# then open a fresh shell (see note below) so ~/.local/bin is on PATH:
./build.sh --install          # user: poetry install + poks toolchain
```

If `poetry` is not found after `bootstrap_python.sh`, open a new shell (or `source ~/.bashrc`) so `~/.local/bin` is on `PATH`, then run `./build.sh --install`. Inside the devcontainer this is automatic: the Dockerfile bakes both `bootstrap_ubuntu.sh` and `bootstrap_python.sh` into the image at build time, and `onCreateCommand` runs `build.sh --install`.

**Always** start VS Code with: `.\build.ps1 -startVSCode` to ensure proper environment variables and Python virtual environment activation (`.venv` with Poetry dependencies).

### Working against a local spl-core checkout

Some changes to this project need a change in `spl-core` first. `CMakeLists.txt`
locates spl-core by importing it from the venv and then includes its
`spl.cmake`, so a single editable install redirects **both** the Python and the
CMake side at a local checkout:

```bash
.venv/bin/python -m pip install -e ../spl-core --no-deps   # point at the checkout
./build.sh --install                                       # ...and back to the pinned version
```

A local path is never committed to `pyproject.toml`: every machine and CI must
resolve the same spl-core, so a local override never silently becomes the
build everyone gets. The override is for the span of one change, not a working
mode.

`pyproject.toml` currently pins a **commit of the useblocks fork** of spl-core
(branch `feat/configurable-docs-pipeline`, based on spl-core 8.9.0). It carries
the documentation changes this project relies on: `SPL_SOURCE_DOCS_JINJA_RAW_TAGS`,
`SPL_VARIANT_DATA_FILE_DOCS` / `_REPORTS`, `SPL_SPHINX_BINARY_DIR` and
`KConfig.declared_boolean_symbols()`. Pinning a commit keeps every build on the
same code. Switch back to a PyPI release once upstream spl-core has released
them.

### VS Code CMake Extension Configuration

VS Code users can build directly using the CMake extension via `.vscode` configuration files:

- **Build Kit selection** (`.vscode/cmake-kits.json`): Choose between `prod` (production C code) and `test` (GTest C++ unit tests)
- **Variant selection** (`.vscode/cmake-variants.json`): Select variant (Disco, Spa, Sleep, Base/Dev, IDEA/Sloemada) and build type (Debug/Release)
- **CMake settings** (`.vscode/settings.json`): Configures build directory pattern `build/${variant}/${buildKit}/${buildType}`, Ninja generator, and passes BUILD_KIT/BUILD_TYPE variables to CMake
- Use CMake extension's status bar to select kit/variant/build type, then build using CMake commands or tasks

### Building Variants

```powershell
# Interactive variant selection
.\build.ps1 -build

# Specific variant
.\build.ps1 -build -variants Disco

# Clean build
.\build.ps1 -build -variants Spa -clean

# Test build (includes unit tests)
.\build.ps1 -build -buildKit test -buildType Debug
```

Build outputs: `build/<VariantName>/<BuildKit>/<BuildType?>/`

### Testing

Tests are **Python-based** using pytest for build validation and report checks:

```powershell
# Run all tests
.\build.ps1 -selftests

# Filtered tests
.\build.ps1 -selftests -filter "Disco"

# Specific markers (see pytest.ini)
.\build.ps1 -selftests -marker "build_debug"
```

Component unit tests: GTest/GMock in `components/*/test/*.cc` files, run via `test` build kit.

View reports: Use tasks "Open variant test report" / "Open variant coverage report" from VS Code.

## Continuous Integration

CI runs on **GitHub Actions** (`.github/workflows/ci.yml`) for every push/PR to `develop` and `release/*`, plus a nightly schedule. **A PR only merges when all checks are green** — branch protection enforces this, so a red build blocks the merge by definition. Don't add manual "remember to check CI" notes to docs or PRs; the gate is automatic.

Jobs:

- `determine-gate` — computes the `gate_*` quality-gate marker once (by event/branch) and shares it with all four jobs via `needs`.
- `documentation` (`ubuntu-24.04`) — the compiler-free gate: a Python and the locked dependencies, then `pytest -m "docs and <gate>"`. It generates the variant data for **every** variant and builds each one's documents, where the build jobs only cover the variants they build. No poks, no scoop, no cross-compiler, so it is also the fastest signal in the workflow.
- `test-on-windows` (`windows-2025`) — `build.ps1 -install` then `-selftests -marker <gate>`.
- `test-on-linux` (`ubuntu-24.04`) — bare-runner path: `bootstrap_ubuntu.sh` + `bootstrap_python.sh`, then `build.sh --install` and `--selftests --marker <gate>`.
- `test-devcontainer` (`ubuntu-24.04`) — builds `.devcontainer/` via `devcontainers/ci` (which runs `onCreateCommand`, i.e. `build.sh --install`) and runs `build.sh --selftests --marker <gate>` inside the container.

CI is a **thin wrapper**: it only sets up the OS and calls the build scripts, so "green in CI" ⇔ "works locally". Runners are pinned to explicit images (never `*-latest`), so an OS/toolchain bump is always a reviewable change rather than a surprise.

## SPL-Specific CMake Patterns

Component `CMakeLists.txt` files use **spl-core macros** (not standard CMake):

```cmake
# Add source files (production code)
spl_add_source(src/my_component.c)

# Add test files (GTest, only in test build kit)
spl_add_test_source(test/test_my_component.cc)

# Declare dependencies on other components
spl_add_required_interface(components/rte)

# Finalize component (must be last)
spl_create_component(LONG_NAME "My Component")
```

**Conditional dependencies** use KConfig variables from `config.txt`:

```cmake
if(AUTO_OFF STREQUAL "True")
    spl_add_required_interface(components/auto_off)
endif()
```

Variant's `parts.cmake` lists components with `spl_add_component(components/<name>)`.

## KConfig Feature System

Features defined in `KConfig` (menuconfig syntax) generate CMake variables via `config.txt`:

- `CONFIG_BLINKING=y` → CMake variable `BLINKING="True"`
- `# CONFIG_AUTO_OFF is not set` → CMake variable `AUTO_OFF="False"`

Edit feature config: `.\build.ps1 -command ".venv\Scripts\poetry run guiconfig"` (requires KCONFIG_CONFIG env var set to variant's config.txt).

Check feature values in source code via generated `autoconf.h` header.

## Variant-Dependent Documentation

Documents never use Jinja. The global `source-read` pass that rendered every
document is gone, and bringing it back is a regression, not a shortcut.

One narrowly scoped `source-read` handler does exist, and it is not that.
spl-core passes `--jinja-raw-tags` to clanguru, so generated source listings
under `__source_docs` wrap their code in `{% raw %}` markers that nothing else
removes. `conf.py` blanks those two lines, for those docnames only: a line
filter, not a template render. It goes away when `pyproject.toml` can pin an
spl-core that lets the flag be turned off -- no released version does yet.

Everything variant-dependent is decided from **one file**: the variant data
that `tools/variant_data.py` writes, exposed as `var.*`. The governing rule:

> **Everything a condition may name has to be IN the variant data file.**

A key that only `conf.py` knows is invisible to ubCode, `ubc` and a reviewer's
editor, so their view of the project silently disagrees with the build —
silently, because a condition a tool cannot evaluate gates content **off**
rather than failing. That is why `conf.py` reads the file and adds nothing to
it.

### The three mechanisms

**Whole documents: `[[source.variant_sources]]` in `ubproject.toml`.** One rule
per component, gated on membership of the variant's component list:

```toml
[[source.variant_sources]]
if = "'components/auto_off' in var.build_config.components"
files = [
    "components/auto_off/doc/**",
    "generated/components/auto_off/reports/**",
    "generated/components/auto_off/__source_docs/**",
]
```

Membership, never identity. The component list comes from that variant's
`parts.cmake`, so the product structure is stated once, in the file that already
states it. **Never gate on the variant name** — that is a second encoding of the
same fact, free to drift.

Rules are *subtractive*: a FALSE rule removes the files it names, a TRUE rule
does nothing. Two rules naming the same file therefore compose as AND, which is
how generated output is gated on both the build shape and the component.

**Blocks inside a document: the `{if}` directive of Sphinx-Needs.** Four-backtick
fence, condition as the argument:

````text
````{if} var.features.BLINKING
...
````
````

Content behind a false condition is never parsed, so its needs never enter the
traceability data.

**External trees: `[[source.mounts]]`.** Currently unused. Everything this
project shows lives in the tree or under `generated/`.

### What the data holds

| Key | |
| --- | --- |
| `var.features.*` | every KConfig symbol, with **every** declared boolean present — including the promptless ones KConfig omits when they are off |
| `var.build_config.variant` | e.g. `Disco`, `Base/Dev` |
| `var.build_config.kit` | `prod` or `test` |
| `var.build_config.target` | `docs` or `reports` |
| `var.build_config.components` | the variant's component list, from `parts.cmake` |

### Two differences between the engines

The `{if}` directive takes a real Python expression, so a bare
`var.features.BLINKING` is enough. A `variant_sources` condition uses a
restricted grammar that needs `== True`. And a condition that cannot be
evaluated **excludes** what it gates, so a typo silently shrinks the document
set rather than failing loudly — which is what `test_ubproject_config.py` is
for.

### Checking with the other reader

The Sphinx build is only half the story: the point of keeping everything in the
variant data file is that a reader which never runs `conf.py` decides the same
things. `ubc` is that reader, and `pytest -m docs -k ubc` proves it — per
variant, it asserts that ubCode removes **exactly** the component documents the
variant's component list omits.

`ubc` ships inside the ubCode VS Code extension and is on neither PyPI nor npm,
so there is no install step this repository can own. The tests find it on
`PATH`, via the `UBC` environment variable, or in the extension directory, and
**skip** when it is absent rather than pretending to cover it:

```bash
export UBC="$HOME/.vscode/extensions/useblocks.ubcode-0.35.0-darwin-arm64/server/cli/ubc"
pytest -m docs -k ubc
```

To look at one variant by hand, override the data file rather than switching
the project:

```bash
ubc check -c "needs.variant_data_file = 'build/variants/Sleep/test/docs.json'"
```

Two things to know about `ubproject.toml` when editing it. Configuring parsers
puts ubCode in **parser mode**, where the document set comes from each
`[parse.parsers.*].include` and `[source] extend_include` is *ignored* — so the
parser includes have to stay in step with `include_patterns` in `conf.py`, or
the two readers are looking at different files. And `[[source.variant_sources]]`
rules are implemented as exclusions, which is why a rule that cannot be
evaluated removes what it gates.

### Adding a component

1. Add it to the variant's `parts.cmake`.
2. Add one `[[source.variant_sources]]` rule in `ubproject.toml`.
3. Add one line to the 150% toctree in `doc/components/index.md`.

Nothing is generated, no loop is edited, and nothing under `build/` is touched.

### Generated output

`build/` and `generated/` are output. **Nobody edits them — not a person, not an
assistant.** The editor is configured to refuse it (`files.readonlyInclude`) and
`build/variants/GENERATED` says so on disk.

`generated/` is the configured variant's build directory, and today **nothing
reads it**. The report toctrees still glob `/build/**`, and `conf.py` narrows
the source set to the configured build so each glob resolves to one page.

That is a deferral, not the end state. A fixed path under `generated/` would be
better, and the configuration for it is already in place -- the rst parser
include and the `generated/...` entries in every variant rule. It cannot be
switched on from this repository: spl-core writes the gcovr tree at
`reports/html/<build-relative page path>/coverage/index.html` and looks its
report artifacts up in the same place, so moving the page that links to it
without moving the tree breaks every coverage link.

When spl-core does write the tree relative to the page, the `build/` forwarding
in `conf.py` and the `generated` entry in its `exclude_patterns` have to go in
the *same* change, or Sphinx discovers every report page under both names.
`test_generated_and_build_discovery_are_never_both_live` fails if only half of
that is done.

Regenerate without a compiler — KConfig is pure Python, and CMake's top-level
`project()` call demands a C toolchain before it will configure at all:

```bash
python tools/variant_data.py --all                     # the whole matrix
python tools/variant_data.py --variant Sleep --kit test # ...and point at one cell
python tools/variant_data.py --all --check             # CI: regenerate and diff
```

Preview a variant by pointing the build at its cell:

```bash
VARIANT_DATA_FILE=build/variants/Sleep/test/docs.json sphinx-build -b html . out
```

## Project-Specific Conventions

1. **No direct CMake invocation**: Always use `build.ps1` wrapper (handles variant selection, environment, Poetry, etc.)
2. **Component isolation**: Each component has own CMakeLists.txt, must declare all dependencies explicitly
3. **Test location**: Python integration tests in `test/<VariantName>/`, C++ unit tests in `components/*/test/`
4. **Dependency management**: Python deps via Poetry (`pyproject.toml`), C/C++ external deps fetched by CMake FetchContent

## Common Integration Points

- **RTE (Runtime Environment)**: `components/rte` - shared interfaces, all components depend on it
- **Main entry**: `components/main/src/main.c` - calls OS scheduler
- **OS abstraction**: `components/os` - simple task scheduler (configurable period via KConfig)
- **Platform types**: `components/platform_types` - standard types (uint8_t, etc.)

Components communicate via RTE signals/runnable interfaces (see `rte.h` for patterns).

## Key Files for Understanding

- [build.ps1](build.ps1) - Entry point for all build/test operations (Windows)
- [build.sh](build.sh) - Peer entry point for Linux/macOS/devcontainer
- [.github/workflows/ci.yml](.github/workflows/ci.yml) - Windows + Linux CI, thin wrapper over the build scripts
- [CMakeLists.txt](CMakeLists.txt#L8) - Includes variant config and spl-core framework
- [KConfig](KConfig) - Feature model definition
- [variants/Disco/parts.cmake](variants/Disco/parts.cmake) - Example component selection
- [components/spled/CMakeLists.txt](components/spled/CMakeLists.txt) - Example conditional dependencies
- [test/Disco/test_Disco.py](test/Disco/test_Disco.py) - Example pytest structure using `SplBuild` helper
