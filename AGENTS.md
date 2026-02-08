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

**Windows:**
- Run `.\build.ps1 -install` to install dependencies
- Start VS Code with `.\build.ps1 -startVSCode`

**Linux/macOS:**
- Run `./build.sh --install` or `make install` to install dependencies
- Start VS Code with `./build.sh --start-vscode` or `make vscode`
- See [BUILD_LINUX.md](BUILD_LINUX.md) for detailed Linux instructions

**When to re-run installation:**
- First cloning the repository
- Switching branches (dependencies may have changed)
- After pulling updates

This ensures proper environment variables and Python virtual environment activation (`.venv` with Poetry dependencies).

### VS Code CMake Extension Configuration

VS Code users can build directly using the CMake extension via `.vscode` configuration files:

- **Build Kit selection** (`.vscode/cmake-kits.json`): Choose between `prod` (production C code) and `test` (GTest C++ unit tests)
- **Variant selection** (`.vscode/cmake-variants.json`): Select variant (Disco, Spa, Sleep, Base/Dev, IDEA/Sloemada) and build type (Debug/Release)
- **CMake settings** (`.vscode/settings.json`): Configures build directory pattern `build/${variant}/${buildKit}/${buildType}`, Ninja generator, and passes BUILD_KIT/BUILD_TYPE variables to CMake
- Use CMake extension's status bar to select kit/variant/build type, then build using CMake commands or tasks

### Building Variants

**Windows (PowerShell):**
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

**Linux/macOS (Bash/Make):**
```bash
# Using bash script (same as PowerShell)
./build.sh --build --variants Disco
./build.sh --build --variants Spa --clean
./build.sh --build --build-kit test --build-type Debug

# Using Makefile (shortcuts)
make disco                           # Build Disco variant
make build VARIANT=Spa               # Build Spa variant
make build-clean VARIANT=Spa         # Clean build
make test-build VARIANT=Disco        # Build with test kit
```

Build outputs: `build/<VariantName>/<BuildKit>/<BuildType?>/`

### Testing

Tests are **Python-based** using pytest for build validation and report checks:

**Windows:**
```powershell
# Run all tests
.\build.ps1 -selftests

# Filtered tests
.\build.ps1 -selftests -filter "Disco"

# Specific markers (see pytest.ini)
.\build.ps1 -selftests -marker "build_debug"
```

**Linux/macOS:**
```bash
# Using bash script
./build.sh --selftests --filter "Disco"

# Using Makefile
make test                            # All tests
make test-disco                      # Disco tests only
make test-filter FILTER="Disco"      # Custom filter
```

Component unit tests: GTest/GMock in `components/*/test/*.cc` files, run via `test` build kit.

View reports: Use tasks "Open variant test report" / "Open variant coverage report" from VS Code.

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

Edit feature config: `.\build.ps1 -command "guiconfig"` (requires KCONFIG_CONFIG env var set to variant's config.txt).

Check feature values in source code via generated `autoconf.h` header.

## Project-Specific Conventions

1. **No direct CMake invocation**: Always use build wrapper (`build.ps1` on Windows, `build.sh` or `make` on Linux) - handles variant selection, environment, Poetry, etc.
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

- [build.ps1](build.ps1) - Windows build/test wrapper
- [build.sh](build.sh) - Linux/macOS build/test wrapper
- [Makefile](Makefile) - Convenient shortcuts for common tasks (Linux/macOS)
- [BUILD_LINUX.md](BUILD_LINUX.md) - Linux-specific build instructions
- [CMakeLists.txt](CMakeLists.txt#L8) - Includes variant config and spl-core framework
- [KConfig](KConfig) - Feature model definition
- [variants/Disco/parts.cmake](variants/Disco/parts.cmake) - Example component selection
- [components/spled/CMakeLists.txt](components/spled/CMakeLists.txt) - Example conditional dependencies
- [test/Disco/test_Disco.py](test/Disco/test_Disco.py) - Example pytest structure using `SplBuild` helper
