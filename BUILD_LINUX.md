# Linux Build Instructions

This document describes how to build and develop SPLED on Linux/macOS systems.

## Quick Start

```bash
# 1. Install dependencies
./build.sh --install
# or
make install

# 2. Build a variant
./build.sh --build --variants Disco
# or
make disco

# 3. Run tests
./build.sh --selftests --filter "Disco"
# or
make test-disco
```

## Installation

### System Dependencies

The `--install` option will automatically install required dependencies using your system's package manager:

**Supported package managers:**
- apt (Debian/Ubuntu)
- dnf/yum (Fedora/RHEL)
- pacman (Arch Linux)
- brew (macOS)

**Required packages:**
- Python 3.13+
- CMake
- Ninja
- GCC/G++
- Graphviz
- Cppcheck
- Clang 14+

### Manual Installation

If automatic installation doesn't work, install manually:

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3.13 python3.13-venv python3-pip \
    cmake ninja-build gcc g++ graphviz cppcheck clang-14
```

**Fedora:**
```bash
sudo dnf install -y python3.13 cmake ninja-build gcc gcc-c++ \
    graphviz cppcheck clang
```

**macOS:**
```bash
brew install python@3.13 cmake ninja graphviz cppcheck llvm
```

### Python Environment

After installing system dependencies, run:
```bash
./build.sh --install
```

This will:
1. Create Python virtual environment (`.venv`)
2. Install Poetry
3. Install all Python dependencies from `pyproject.toml`

## Usage

### Option 1: Bash Script (./build.sh)

Direct equivalent to `build.ps1` with all features:

```bash
# Installation
./build.sh --install                      # Mandatory dependencies
./build.sh --install-optional             # Optional dependencies
./build.sh --install-vscode               # VS Code

# Building
./build.sh --build --variants Disco       # Build Disco variant
./build.sh --build --variants all         # Build all variants
./build.sh --build --variants Disco,Spa   # Build multiple variants
./build.sh --build --variants Disco --clean  # Clean build

# Build options
./build.sh --build --variants Disco \
    --build-kit test \
    --build-type Debug \
    --target all

# Testing
./build.sh --selftests                    # All tests
./build.sh --selftests --filter "Disco"   # Filtered tests
./build.sh --selftests --marker "build_debug"  # By marker

# Documentation
./build.sh --docs                         # Build HTML docs

# Other
./build.sh --start-vscode                 # Start VS Code
./build.sh --command "poetry run pytest"  # Custom command
./build.sh --help                         # Show all options
```

### Option 2: Makefile (make)

Convenient shortcuts for common tasks:

```bash
# Setup
make install                # Install dependencies
make install-optional       # Optional dependencies
make dev-setup              # Complete dev setup

# Building variants
make build VARIANT=Disco    # Build specific variant
make disco                  # Build Disco (shortcut)
make spa                    # Build Spa (shortcut)
make sleep                  # Build Sleep (shortcut)
make all-variants           # Build all variants

# Build configurations
make build VARIANT=Disco BUILD_KIT=test BUILD_TYPE=Debug
make build-clean VARIANT=Disco  # Clean build

# Testing
make test                   # All integration tests
make test-filter FILTER="Disco"  # Filtered tests
make test-disco             # Disco tests only
make test-build VARIANT=Disco    # Build unit tests (GTest)

# Documentation
make docs                   # Build documentation
make docs-open              # Build and open in browser

# Development
make vscode                 # Start VS Code
make check                  # Check installed tools
make env                    # Show environment
make list-variants          # List all variants
make clean                  # Remove build artifacts

# Quick workflows
make quick-disco            # Build + test Disco
make full-test              # Build all + test all

# Help
make help                   # Show all targets
```

## Differences from Windows (build.ps1)

### Not Available on Linux

1. **Scoop package manager**: Windows-specific
   - Alternative: Use system package manager (apt, dnf, brew)

2. **Bootstrap PowerShell script**: Windows-specific
   - Alternative: Direct Python-based setup with Poetry

3. **MinGW/LLVM from Scoop**: Windows-specific
   - Alternative: Use system GCC/Clang packages

### Adapted for Linux

1. **Virtual environment**: `.venv/bin/` instead of `.venv\Scripts\`
2. **Python command**: `python3` or `python3.13` instead of `python`
3. **Path separators**: `/` instead of `\`
4. **Browser opening**: `xdg-open` (Linux) or `open` (macOS)
5. **Package installation**: System package manager instead of Scoop

## Build Structure

Build outputs are organized identically to Windows:

```
build/
├── <Variant>/
│   ├── prod/                    # Production builds
│   │   └── spled_<variant>.elf
│   └── test/
│       └── Debug/               # Unit test builds
│           ├── reports/
│           │   ├── html/        # Test reports
│           │   └── coverage/    # Coverage reports
│           └── <component>/
```

## Environment Variables

The build system respects the following environment variables:

- `BRANCH_NAME`: Current branch (CI)
- `CHANGE_ID`: Pull request ID (CI)
- `CHANGE_TARGET`: Target branch (CI)

These are used for automatic test filtering in CI environments.

## Troubleshooting

### Python 3.13 not found

If `python3.13` is not available, the script will try `python3`. Check version:
```bash
python3 --version  # Should be >= 3.13
```

### CMake/Ninja not found

Install missing tools:
```bash
make check  # Show what's missing
make install  # Install dependencies
```

### Virtual environment issues

Delete and recreate:
```bash
rm -rf .venv
./build.sh --install
```

### Permission denied errors

Make script executable:
```bash
chmod +x build.sh
```

### Graphviz not rendering

Install graphviz:
```bash
sudo apt install graphviz  # Ubuntu/Debian
sudo dnf install graphviz  # Fedora
brew install graphviz      # macOS
```

## VS Code Integration

The project includes VS Code configuration for CMake extension:
- `.vscode/cmake-kits.json`: Build kit selection (prod/test)
- `.vscode/cmake-variants.json`: Variant selection
- `.vscode/settings.json`: CMake settings

Start VS Code with proper environment:
```bash
./build.sh --start-vscode
# or
make vscode
```

## Examples

### Complete setup workflow
```bash
# 1. Install everything
make dev-setup

# 2. Build and test Disco variant
make quick-disco

# 3. Open test report
make test-report VARIANT=Disco

# 4. Build documentation
make docs-open
```

### Development cycle
```bash
# Build specific variant
make disco

# Run its tests
make test-disco

# Check coverage
make coverage-report VARIANT=Disco
```

### CI-like testing
```bash
# Build all variants
make all-variants

# Run all tests
make test

# Or in one command
make full-test
```

## Support

For issues specific to Linux builds, check:
1. Tool availability: `make check`
2. Environment: `make env`
3. Python dependencies: `poetry install`

For general SPLED issues, see [AGENTS.md](AGENTS.md) and [README.md](README.md).
