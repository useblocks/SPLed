#!/usr/bin/env bash
#
# Build wrapper script for Linux/macOS
# Equivalent to build.ps1 for Unix-like systems
#

set -e  # Exit on error
set -o pipefail  # Exit on pipe failure

# Default values
INSTALL=0
INSTALL_OPTIONAL=0
INSTALL_VSCODE=0
SELFTESTS=0
BUILD=0
DOCS=0
START_VSCODE=0
COMMAND=""
CLEAN=0
BUILD_KIT="prod"
BUILD_TYPE=""
TARGET="all"
VARIANTS=()
FILTER=""
MARKER=""
PYTEST_EXTRA_ARGS=""
NINJA_ARGS=""
RECONFIGURE=0
CONFIGURE_ONLY=0
WAIT_FOR_KEY=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
info() {
    echo -e "${BLUE}Info: $*${NC}"
}

success() {
    echo -e "${GREEN}$*${NC}"
}

error() {
    echo -e "${RED}Error: $*${NC}" >&2
}

warning() {
    echo -e "${YELLOW}Warning: $*${NC}"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --install)
            INSTALL=1
            shift
            ;;
        --install-optional)
            INSTALL_OPTIONAL=1
            shift
            ;;
        --install-vscode)
            INSTALL_VSCODE=1
            shift
            ;;
        --selftests)
            SELFTESTS=1
            shift
            ;;
        --build)
            BUILD=1
            shift
            ;;
        --docs)
            DOCS=1
            shift
            ;;
        --start-vscode)
            START_VSCODE=1
            shift
            ;;
        --command)
            COMMAND="$2"
            shift 2
            ;;
        --clean)
            CLEAN=1
            shift
            ;;
        --build-kit)
            BUILD_KIT="$2"
            shift 2
            ;;
        --build-type)
            BUILD_TYPE="$2"
            shift 2
            ;;
        --target)
            TARGET="$2"
            shift 2
            ;;
        --variants)
            IFS=',' read -ra VARIANTS <<< "$2"
            shift 2
            ;;
        --filter)
            FILTER="$2"
            shift 2
            ;;
        --marker)
            MARKER="$2"
            shift 2
            ;;
        --pytest-extra-args)
            PYTEST_EXTRA_ARGS="$2"
            shift 2
            ;;
        --ninja-args)
            NINJA_ARGS="$2"
            shift 2
            ;;
        --reconfigure)
            RECONFIGURE=1
            shift
            ;;
        --configure-only)
            CONFIGURE_ONLY=1
            shift
            ;;
        --wait-for-key)
            WAIT_FOR_KEY=1
            shift
            ;;
        -h|--help)
            cat << EOF
Usage: $0 [OPTIONS]

Build wrapper for SPLED project (Linux/macOS)

Options:
    --install               Install mandatory dependencies
    --install-optional      Install optional dependencies
    --install-vscode        Install Visual Studio Code
    --build                 Build the project
    --docs                  Build HTML documentation
    --selftests             Run pytest-based integration tests
    --start-vscode          Start Visual Studio Code
    --command <cmd>         Execute custom command
    --clean                 Clean build artifacts
    --build-kit <kit>       Build kit: prod or test (default: prod)
    --build-type <type>     Build type: Debug or Release
    --target <target>       Build target (default: all)
    --variants <v1,v2>      Variants to build (comma-separated or 'all')
    --filter <expr>         Pytest filter expression
    --marker <marker>       Pytest marker
    --pytest-extra-args     Additional pytest arguments
    --ninja-args <args>     Additional Ninja build arguments
    --reconfigure           Delete CMake cache and reconfigure
    --configure-only        Only configure, don't build
    --wait-for-key          Wait for Enter before exiting
    -h, --help              Show this help message

Examples:
    $0 --install
    $0 --build --variants Disco
    $0 --build --variants Disco,Spa --clean
    $0 --selftests --filter "Disco"
    $0 --docs
EOF
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Change to script directory
cd "$(dirname "${BASH_SOURCE[0]}")"
info "Running in $(pwd)"

# Function: Detect package manager
detect_package_manager() {
    if command -v apt-get &> /dev/null; then
        echo "apt"
    elif command -v dnf &> /dev/null; then
        echo "dnf"
    elif command -v yum &> /dev/null; then
        echo "yum"
    elif command -v brew &> /dev/null; then
        echo "brew"
    elif command -v pacman &> /dev/null; then
        echo "pacman"
    else
        echo "unknown"
    fi
}

# Function: Install system dependencies
install_system_dependencies() {
    local pkg_mgr=$(detect_package_manager)

    info "Detected package manager: $pkg_mgr"

    case $pkg_mgr in
        apt)
            info "Installing dependencies via apt..."
            sudo apt-get update
            sudo apt-get install -y python3.13 python3.13-venv python3-pip \
                cmake ninja-build gcc g++ graphviz cppcheck clang-14 \
                || warning "Some packages may not be available"
            ;;
        dnf)
            info "Installing dependencies via dnf..."
            sudo dnf install -y python3.13 python3-pip cmake ninja-build \
                gcc gcc-c++ graphviz cppcheck clang \
                || warning "Some packages may not be available"
            ;;
        yum)
            info "Installing dependencies via yum..."
            sudo yum install -y python3 python3-pip cmake ninja-build \
                gcc gcc-c++ graphviz cppcheck \
                || warning "Some packages may not be available"
            ;;
        brew)
            info "Installing dependencies via Homebrew..."
            brew install python@3.11 cmake ninja graphviz cppcheck llvm \
                || warning "Some packages may not be available"
            ;;
        pacman)
            info "Installing dependencies via pacman..."
            sudo pacman -S --noconfirm python python-pip cmake ninja gcc graphviz cppcheck clang \
                || warning "Some packages may not be available"
            ;;
        *)
            error "Unknown package manager. Please install manually:"
            echo "  - Python 3.11"
            echo "  - CMake, Ninja"
            echo "  - GCC/G++, Clang"
            echo "  - graphviz, cppcheck"
            exit 1
            ;;
    esac
}

# Function: Bootstrap Python environment
invoke_bootstrap() {
    info "Bootstrapping Python environment..."

    # Download bootstrap installer if not present
    if [ ! -d ".bootstrap" ]; then
        info "Downloading bootstrap installer..."
        mkdir -p .bootstrap

        # Download bootstrap installer script
        curl -fsSL https://raw.githubusercontent.com/avengineers/bootstrap-installer/v1.17.2/install.sh -o .bootstrap/install.sh
        chmod +x .bootstrap/install.sh

        # Run bootstrap installer
        bash .bootstrap/install.sh
    fi

    # Execute bootstrap script if it exists
    if [ -f ".bootstrap/bootstrap.sh" ]; then
        info "Running bootstrap script..."
        source .bootstrap/bootstrap.sh
    else
        warning "Bootstrap script not found, proceeding with manual setup..."

        # Check for Python 3.13
        if ! command -v python3.13 &> /dev/null; then
            if ! command -v python3 &> /dev/null; then
                error "Python 3 not found. Please install Python 3.13+"
                exit 1
            fi
            PYTHON_CMD="python3"
            warning "python3.13 not found, using python3 ($(python3 --version))"
        else
            PYTHON_CMD="python3.13"
        fi

        # Create virtual environment if it doesn't exist
        if [ ! -d ".venv" ]; then
            info "Creating Python virtual environment..."
            $PYTHON_CMD -m venv .venv
        fi

        # Activate virtual environment
        source .venv/bin/activate

        # Upgrade pip
        info "Upgrading pip..."
        python -m pip install --upgrade pip

        # Install/upgrade Poetry
        info "Installing/upgrading Poetry..."
        pip install "poetry>=2.1.0"

        # Install Python dependencies via Poetry
        info "Installing Python dependencies..."
        poetry install
    fi

    success "Bootstrap complete!"
}

# Function: Install optional dependencies
install_optional_dependencies() {
    local pkg_mgr=$(detect_package_manager)

    info "Installing optional dependencies..."

    case $pkg_mgr in
        apt)
            sudo apt-get install -y doxygen lcov gcovr || warning "Some optional packages not available"
            ;;
        dnf|yum)
            sudo dnf install -y doxygen lcov || warning "Some optional packages not available"
            ;;
        brew)
            brew install doxygen lcov || warning "Some optional packages not available"
            ;;
        pacman)
            sudo pacman -S --noconfirm doxygen lcov || warning "Some optional packages not available"
            ;;
        *)
            warning "Cannot install optional dependencies with unknown package manager"
            ;;
    esac
}

# Function: Install VS Code
install_vscode() {
    local pkg_mgr=$(detect_package_manager)

    info "Installing Visual Studio Code..."

    case $pkg_mgr in
        apt)
            # Add Microsoft GPG key and repository
            wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
            sudo install -o root -g root -m 644 packages.microsoft.gpg /etc/apt/trusted.gpg.d/
            sudo sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/vscode stable main" > /etc/apt/sources.list.d/vscode.list'
            sudo apt-get update
            sudo apt-get install -y code
            rm packages.microsoft.gpg
            ;;
        dnf)
            sudo rpm --import https://packages.microsoft.com/keys/microsoft.asc
            sudo sh -c 'echo -e "[code]\nname=Visual Studio Code\nbaseurl=https://packages.microsoft.com/yumrepos/vscode\nenabled=1\ngpgcheck=1\ngpgkey=https://packages.microsoft.com/keys/microsoft.asc" > /etc/yum.repos.d/vscode.repo'
            sudo dnf install -y code
            ;;
        brew)
            brew install --cask visual-studio-code
            ;;
        *)
            error "Cannot install VS Code automatically. Please install from: https://code.visualstudio.com/"
            exit 1
            ;;
    esac

    success "VS Code installed!"
}

# Function: Build documentation
build_docs() {
    info "Building documentation..."

    # Ensure virtual environment is activated
    if [ -z "$VIRTUAL_ENV" ]; then
        if [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate
        else
            error "Virtual environment not found. Run --install first."
            exit 1
        fi
    fi

    # Check if sphinx-build is available
    if ! command -v sphinx-build &> /dev/null; then
        error "sphinx-build not found. Please run --install first."
        exit 1
    fi

    # Remove old build
    if [ -d "build/html" ]; then
        info "Removing old documentation build..."
        rm -rf build/html
    fi

    # Build documentation
    info "Running sphinx-build..."
    sphinx-build -b html -j auto . build/html

    success "Documentation built successfully!"
    info "Open build/html/index.html in your browser to view the documentation."
}

# Function: Get release branch pytest filter
get_release_branch_pytest_filter() {
    local CHANGE_ID="${CHANGE_ID:-}"
    local BRANCH_NAME="${BRANCH_NAME:-}"
    local CHANGE_TARGET="${CHANGE_TARGET:-}"

    local target_branch=""

    if [ -z "$CHANGE_ID" ] && [ -n "$BRANCH_NAME" ] && [[ "$BRANCH_NAME" == release/* ]]; then
        target_branch="$BRANCH_NAME"
    fi

    if [ -n "$CHANGE_ID" ] && [ -n "$CHANGE_TARGET" ] && [[ "$CHANGE_TARGET" == release/* ]]; then
        target_branch="$CHANGE_TARGET"
    fi

    local filter=""
    if [ -n "$target_branch" ]; then
        if [[ "$target_branch" =~ release/([^/]+/[^/]+)(.*) ]]; then
            filter="${BASH_REMATCH[1]}"
            filter="${filter//\// and }"
        fi
    fi

    echo "$filter"
}

# Function: Run self tests
run_selftests() {
    info "Running self tests..."

    # Ensure virtual environment is activated
    if [ -z "$VIRTUAL_ENV" ]; then
        if [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate
        else
            error "Virtual environment not found. Run --install first."
            exit 1
        fi
    fi

    # Test result path
    local pytest_junit_xml="test/output/test-report.xml"

    # Delete old pytest result
    rm -f "$pytest_junit_xml"
    mkdir -p "$(dirname "$pytest_junit_xml")"

    # Build pytest arguments
    local pytest_args=(
        "--junitxml=$pytest_junit_xml"
    )

    # Filter pytest test cases
    local release_branch_filter=$(get_release_branch_pytest_filter)
    if [ -n "$release_branch_filter" ]; then
        pytest_args+=("-k" "$release_branch_filter")
    elif [ -n "$FILTER" ]; then
        pytest_args+=("-k" "$FILTER")
    fi

    # Execute marker tests
    if [ -n "$MARKER" ]; then
        pytest_args+=("-m" "$MARKER")
    fi

    # Add extra pytest arguments
    if [ -n "$PYTEST_EXTRA_ARGS" ]; then
        pytest_args+=($PYTEST_EXTRA_ARGS)
    fi

    # Run pytest
    info "Running: pytest ${pytest_args[*]}"
    pytest "${pytest_args[@]}" || warning "Some tests failed. Check $pytest_junit_xml for details."
}

# Function: Build system
build_system() {
    local variants_selected=()

    # Determine variants to build
    if [ ${#VARIANTS[@]} -eq 0 ] || [ "${VARIANTS[0]}" = "all" ]; then
        # Find all variants
        mapfile -t variant_configs < <(find variants -name "config.cmake" -type f)
        local variants_list=()
        for config in "${variant_configs[@]}"; do
            local variant=$(dirname "$config" | sed 's|^variants/||')
            variants_list+=("$variant")
        done

        if [ ${#VARIANTS[@]} -eq 0 ]; then
            # Interactive selection
            info "No '--variants <variant>' was given, please select from list:"
            echo "(0) all variants"
            for i in "${!variants_list[@]}"; do
                echo "($(($i + 1))) ${variants_list[$i]}"
            done
            read -p "Please enter selected variant number: " selection

            if [ "$selection" = "0" ]; then
                variants_selected=("${variants_list[@]}")
            else
                variants_selected=("${variants_list[$(($selection - 1))]}")
            fi
            info "Selected variants: ${variants_selected[*]}"
        else
            # Build all variants
            variants_selected=("${variants_list[@]}")
        fi
    else
        variants_selected=("${VARIANTS[@]}")
    fi

    # Build each variant
    for variant in "${variants_selected[@]}"; do
        local build_folder="build/${variant}/${BUILD_KIT}"
        if [ -n "$BUILD_TYPE" ]; then
            build_folder="build/${variant}/${BUILD_KIT}/${BUILD_TYPE}"
        fi

        # Clean build
        if [ $CLEAN -eq 1 ]; then
            if [ -d "$build_folder" ]; then
                info "Cleaning $build_folder..."
                rm -rf "$build_folder"
            fi
        fi

        # Create build directory
        mkdir -p "$build_folder"

        # Reconfigure
        if [ $RECONFIGURE -eq 1 ] || [ $CONFIGURE_ONLY -eq 1 ]; then
            rm -f "$build_folder/CMakeCache.txt"
            rm -rf "$build_folder/CMakeFiles"
        fi

        if [ $BUILD -eq 1 ]; then
            if [ -z "$BUILD_TYPE" ]; then
                info "Building target '$TARGET' with build kit '$BUILD_KIT' for variant '$variant'..."
            else
                info "Building target '$TARGET' with build kit '$BUILD_KIT' and build type '$BUILD_TYPE' for variant '$variant'..."
            fi

            # CMake configure
            local additional_config="-DBUILD_KIT=$BUILD_KIT"
            if [ -n "$BUILD_TYPE" ]; then
                additional_config="$additional_config -DBUILD_TYPE=$BUILD_TYPE -DCMAKE_BUILD_TYPE=$BUILD_TYPE"
            fi
            if [ "$BUILD_KIT" = "test" ]; then
                additional_config="$additional_config -DCMAKE_TOOLCHAIN_FILE=tools/toolchains/gcc/toolchain.cmake"
            fi

            info "Configuring CMake..."
            cmake -B "$build_folder" -G Ninja -DVARIANT="$variant" $additional_config

            if [ $CONFIGURE_ONLY -eq 0 ]; then
                local cmd="cmake --build $build_folder --target $TARGET"
                if [ -n "$BUILD_TYPE" ]; then
                    cmd="cmake --build $build_folder --config $BUILD_TYPE --target $TARGET"
                fi

                # CMake clean dead artifacts
                info "Cleaning dead artifacts..."
                $cmd -- -t cleandead

                # CMake build
                info "Building..."
                $cmd -- $NINJA_ARGS

                success "Build complete: $build_folder"
            else
                success "Configuration complete: $build_folder"
            fi
        fi
    done
}

# Function: Clean workspace
clean_workspace() {
    if [ $INSTALL -eq 1 ]; then
        if [ -d ".venv" ]; then
            info "Removing .venv..."
            rm -rf .venv
        fi
    fi
    if [ $SELFTESTS -eq 1 ]; then
        if [ -d "build" ]; then
            info "Removing build directory..."
            rm -rf build
        fi
    fi
}

# Function: Interactive menu
show_menu() {
    clear
    cat << EOF
None of the command line options was given:
(1) --install: installation of mandatory dependencies
(2) --install-optional: installation of optional dependencies
(3) --install-vscode: installation of Visual Studio Code
(4) --build: execute CMake build
(5) --docs: build HTML documentation
(6) --start-vscode: start Visual Studio Code
(7) quit: exit script
EOF
    read -p "Please make a selection: " selection
    echo "$selection"
}

# Main execution logic
main() {
    # Show menu if no options provided
    if [ $INSTALL -eq 0 ] && [ $INSTALL_OPTIONAL -eq 0 ] && [ $INSTALL_VSCODE -eq 0 ] && \
       [ $BUILD -eq 0 ] && [ $DOCS -eq 0 ] && [ $START_VSCODE -eq 0 ] && \
       [ -z "$COMMAND" ] && [ $SELFTESTS -eq 0 ]; then

        selection=$(show_menu)
        case $selection in
            1)
                info "Installing mandatory dependencies..."
                INSTALL=1
                ;;
            2)
                info "Installing optional dependencies..."
                INSTALL_OPTIONAL=1
                ;;
            3)
                info "Installing Visual Studio Code..."
                INSTALL_VSCODE=1
                ;;
            4)
                info "Building..."
                BUILD=1
                ;;
            5)
                info "Building documentation..."
                DOCS=1
                ;;
            6)
                info "Starting VS Code..."
                START_VSCODE=1
                ;;
            7)
                info "Exiting..."
                exit 0
                ;;
            *)
                error "Invalid selection"
                exit 1
                ;;
        esac
    fi

    # Execute requested operations
    if [ $INSTALL -eq 1 ]; then
        install_system_dependencies
        invoke_bootstrap
        success "Installation complete! Please restart your terminal for changes to take effect."
    fi

    # Activate virtual environment for subsequent operations
    if [ -f ".venv/bin/activate" ] && [ -z "$VIRTUAL_ENV" ]; then
        source .venv/bin/activate
    fi

    # Clean workspace
    if [ $CLEAN -eq 1 ]; then
        clean_workspace
    fi

    # Run pypeline if not docs-only
    if [ $DOCS -eq 0 ] || [ $BUILD -eq 1 ] || [ $SELFTESTS -eq 1 ]; then
        if command -v pypeline &> /dev/null; then
            # Use Linux-specific pypeline config if it exists
            if [ -f "pypeline_linux.yaml" ]; then
                pypeline run --step CollectPRChanges --config pypeline_linux.yaml 2>/dev/null || true
            else
                pypeline run --step CollectPRChanges 2>/dev/null || true
            fi
        fi
    fi

    # Load environment setup script if available
    if [ -f "build/env_setup.sh" ]; then
        source build/env_setup.sh
    fi

    if [ $INSTALL_OPTIONAL -eq 1 ]; then
        install_optional_dependencies
    fi

    if [ $INSTALL_VSCODE -eq 1 ]; then
        install_vscode
    fi

    if [ $START_VSCODE -eq 1 ]; then
        info "Starting Visual Studio Code..."
        code . || warning "Failed to start VS Code"
    fi

    if [ $BUILD -eq 1 ]; then
        build_system
    fi

    if [ $DOCS -eq 1 ]; then
        build_docs
    fi

    if [ $SELFTESTS -eq 1 ]; then
        run_selftests
    fi

    if [ -n "$COMMAND" ]; then
        info "Executing command: $COMMAND"
        eval "$COMMAND"
    fi

    if [ $WAIT_FOR_KEY -eq 1 ]; then
        read -p "Press Enter to continue..."
    fi
}

# Run main function
main

# Exit with success
exit 0
