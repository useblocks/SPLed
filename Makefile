# Makefile for SPLED project
# Provides convenient shortcuts for common build operations

.PHONY: help install install-optional install-vscode build clean test docs \
        configure reconfigure vscode disco spa sleep base all-variants

# Default target
.DEFAULT_GOAL := help

# Variables
BUILD_KIT ?= prod
BUILD_TYPE ?= Debug
VARIANT ?= Disco
TARGET ?= all
FILTER ?=
MARKER ?=
NINJA_ARGS ?=

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
NC := \033[0m # No Color

##@ General

help: ## Display this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make $(BLUE)<target>$(NC)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(BLUE)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(GREEN)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup & Installation

install: ## Install mandatory dependencies (Python, CMake, GCC, etc.)
	@echo "$(GREEN)Installing mandatory dependencies...$(NC)"
	./build.sh --install

install-optional: ## Install optional dependencies (Doxygen, lcov, etc.)
	@echo "$(GREEN)Installing optional dependencies...$(NC)"
	./build.sh --install-optional

install-vscode: ## Install Visual Studio Code
	@echo "$(GREEN)Installing VS Code...$(NC)"
	./build.sh --install-vscode

##@ Building

build: ## Build variant (use: make build VARIANT=Disco BUILD_KIT=prod BUILD_TYPE=Debug)
	@echo "$(GREEN)Building variant $(VARIANT) with kit $(BUILD_KIT)...$(NC)"
	./build.sh --build --variants $(VARIANT) --build-kit $(BUILD_KIT) \
		$(if $(BUILD_TYPE),--build-type $(BUILD_TYPE),) \
		--target $(TARGET) \
		$(if $(NINJA_ARGS),--ninja-args "$(NINJA_ARGS)",)

build-clean: ## Clean build variant
	@echo "$(GREEN)Clean building variant $(VARIANT)...$(NC)"
	./build.sh --build --variants $(VARIANT) --build-kit $(BUILD_KIT) \
		$(if $(BUILD_TYPE),--build-type $(BUILD_TYPE),) \
		--clean --target $(TARGET)

all-variants: ## Build all variants
	@echo "$(GREEN)Building all variants...$(NC)"
	./build.sh --build --variants all --build-kit $(BUILD_KIT) \
		$(if $(BUILD_TYPE),--build-type $(BUILD_TYPE),)

configure: ## Configure CMake for variant (without building)
	@echo "$(GREEN)Configuring variant $(VARIANT)...$(NC)"
	./build.sh --build --variants $(VARIANT) --build-kit $(BUILD_KIT) \
		$(if $(BUILD_TYPE),--build-type $(BUILD_TYPE),) \
		--configure-only

reconfigure: ## Reconfigure CMake (delete cache and reconfigure)
	@echo "$(GREEN)Reconfiguring variant $(VARIANT)...$(NC)"
	./build.sh --build --variants $(VARIANT) --build-kit $(BUILD_KIT) \
		$(if $(BUILD_TYPE),--build-type $(BUILD_TYPE),) \
		--reconfigure

clean: ## Remove build artifacts
	@echo "$(GREEN)Cleaning build directory...$(NC)"
	rm -rf build/

##@ Variant Shortcuts

disco: ## Build Disco variant
	@$(MAKE) build VARIANT=Disco

spa: ## Build Spa variant
	@$(MAKE) build VARIANT=Spa

sleep: ## Build Sleep variant
	@$(MAKE) build VARIANT=Sleep

base: ## Build Base/Dev variant
	@$(MAKE) build VARIANT=Base/Dev

##@ Testing

test: ## Run all pytest integration tests
	@echo "$(GREEN)Running all tests...$(NC)"
	./build.sh --selftests

test-filter: ## Run filtered tests (use: make test-filter FILTER="Disco")
	@echo "$(GREEN)Running filtered tests: $(FILTER)...$(NC)"
	./build.sh --selftests --filter "$(FILTER)"

test-marker: ## Run tests with marker (use: make test-marker MARKER="build_debug")
	@echo "$(GREEN)Running tests with marker: $(MARKER)...$(NC)"
	./build.sh --selftests --marker "$(MARKER)"

test-disco: ## Run Disco variant tests
	@$(MAKE) test-filter FILTER="Disco"

test-spa: ## Run Spa variant tests
	@$(MAKE) test-filter FILTER="Spa"

test-sleep: ## Run Sleep variant tests
	@$(MAKE) test-filter FILTER="Sleep"

##@ Unit Testing (GTest)

test-build: ## Build test kit for variant
	@echo "$(GREEN)Building test kit for variant $(VARIANT)...$(NC)"
	./build.sh --build --variants $(VARIANT) --build-kit test --build-type Debug

test-build-all: ## Build test kit for all variants
	@echo "$(GREEN)Building test kit for all variants...$(NC)"
	./build.sh --build --variants all --build-kit test --build-type Debug

test-report: ## Open variant test report (use: make test-report VARIANT=Disco)
	@echo "$(GREEN)Opening test report for $(VARIANT)...$(NC)"
	@xdg-open build/$(VARIANT)/test/Debug/reports/html/index.html 2>/dev/null || \
		open build/$(VARIANT)/test/Debug/reports/html/index.html 2>/dev/null || \
		echo "Report: build/$(VARIANT)/test/Debug/reports/html/index.html"

coverage-report: ## Open variant coverage report
	@echo "$(GREEN)Opening coverage report for $(VARIANT)...$(NC)"
	@xdg-open build/$(VARIANT)/test/Debug/reports/coverage/index.html 2>/dev/null || \
		open build/$(VARIANT)/test/Debug/reports/coverage/index.html 2>/dev/null || \
		echo "Report: build/$(VARIANT)/test/Debug/reports/coverage/index.html"

##@ Documentation

docs: ## Build Sphinx HTML documentation
	@echo "$(GREEN)Building documentation...$(NC)"
	./build.sh --docs

docs-open: docs ## Build and open documentation in browser
	@xdg-open build/html/index.html 2>/dev/null || \
		open build/html/index.html 2>/dev/null || \
		echo "Documentation: build/html/index.html"

docs-clean: ## Clean documentation build
	@echo "$(GREEN)Cleaning documentation...$(NC)"
	rm -rf build/html

##@ Development

vscode: ## Start Visual Studio Code
	@echo "$(GREEN)Starting VS Code...$(NC)"
	./build.sh --start-vscode

env: ## Show current environment
	@echo "$(GREEN)Current environment:$(NC)"
	@echo "BUILD_KIT:  $(BUILD_KIT)"
	@echo "BUILD_TYPE: $(BUILD_TYPE)"
	@echo "VARIANT:    $(VARIANT)"
	@echo "TARGET:     $(TARGET)"
	@echo ""
	@echo "Python venv:"
	@if [ -d .venv ]; then echo "  ✓ .venv exists"; else echo "  ✗ .venv missing (run: make install)"; fi
	@echo ""
	@echo "Available variants:"
	@find variants -name "config.cmake" | sed 's|variants/||; s|/config.cmake||' | sed 's/^/  - /'

check: ## Check if all required tools are installed
	@echo "$(GREEN)Checking required tools...$(NC)"
	@command -v python3 >/dev/null 2>&1 && echo "  ✓ python3" || echo "  ✗ python3 (missing)"
	@command -v cmake >/dev/null 2>&1 && echo "  ✓ cmake" || echo "  ✗ cmake (missing)"
	@command -v ninja >/dev/null 2>&1 && echo "  ✓ ninja" || echo "  ✗ ninja (missing)"
	@command -v gcc >/dev/null 2>&1 && echo "  ✓ gcc" || echo "  ✗ gcc (missing)"
	@command -v g++ >/dev/null 2>&1 && echo "  ✓ g++" || echo "  ✗ g++ (missing)"
	@command -v graphviz >/dev/null 2>&1 && echo "  ✓ graphviz" || echo "  ✗ graphviz (optional)"
	@command -v cppcheck >/dev/null 2>&1 && echo "  ✓ cppcheck" || echo "  ✗ cppcheck (optional)"
	@[ -d .venv ] && echo "  ✓ Python venv" || echo "  ✗ Python venv (run: make install)"

##@ Utilities

list-variants: ## List all available variants
	@echo "$(GREEN)Available variants:$(NC)"
	@find variants -name "config.cmake" | sed 's|variants/||; s|/config.cmake||' | sed 's/^/  /'

.PHONY: list-components
list-components: ## List all components
	@echo "$(GREEN)Available components:$(NC)"
	@find components -maxdepth 1 -type d ! -name components | sed 's|components/||' | sed 's/^/  /'

clean-all: clean docs-clean ## Clean everything (build + docs)
	@echo "$(GREEN)Cleaning Python cache...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf .pytest_cache test/output

##@ Quick Workflows

quick-disco: ## Quick build and test Disco variant
	@$(MAKE) disco
	@$(MAKE) test-disco

quick-spa: ## Quick build and test Spa variant
	@$(MAKE) spa
	@$(MAKE) test-spa

full-test: ## Full test cycle (build all + test all)
	@$(MAKE) all-variants
	@$(MAKE) test

# Development workflow targets
dev-setup: install install-optional install-vscode ## Complete development setup
	@echo "$(GREEN)Development environment ready!$(NC)"
	@echo "Run 'make vscode' to start VS Code"

.PHONY: quick
quick: ## Quick build current VARIANT
	@$(MAKE) build VARIANT=$(VARIANT)
