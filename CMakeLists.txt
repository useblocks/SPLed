# cmake project definition
cmake_minimum_required(VERSION 3.24.0)
cmake_policy(VERSION 3.24)

# default build kit is prod (when not specified as command line argument)
set(BUILD_KIT prod CACHE STRING "Target Group to build.")

# Include variant's configuration
include(${CMAKE_SOURCE_DIR}/variants/${VARIANT}/config.cmake)

if(BUILD_KIT STREQUAL prod)
    project(${VARIANT} C ASM)
else()
    # C++ project due to GTest usage
    project(${VARIANT} C ASM CXX)
endif()

# Fetch all external dependencies into modules directory
set(FETCHCONTENT_BASE_DIR ${PROJECT_SOURCE_DIR}/build/modules CACHE INTERNAL "")
set(FETCHCONTENT_QUIET FALSE)
include(FetchContent)

# Find spl-core location dynamically (works on both Windows and Linux)
if(WIN32)
    set(_VENV_PYTHON "${PROJECT_SOURCE_DIR}/.venv/Scripts/python.exe")
else()
    set(_VENV_PYTHON "${PROJECT_SOURCE_DIR}/.venv/bin/python")
endif()
execute_process(
    COMMAND "${_VENV_PYTHON}" -c "import spl_core, os; print(os.path.dirname(spl_core.__file__))"
    OUTPUT_VARIABLE SPL_CORE_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
    RESULT_VARIABLE SPL_CORE_RESULT
)
if(NOT SPL_CORE_RESULT EQUAL 0)
    message(FATAL_ERROR "Could not find spl_core Python package. Make sure the virtual environment is set up.")
endif()
# Export SPL_CORE_DIR so KConfig source statements can use $(SPL_CORE_DIR)
set(ENV{SPL_CORE_DIR} "${SPL_CORE_DIR}")
# Ensure venv python is found first (spl_core's kconfig.cmake invokes bare 'python')
cmake_path(GET _VENV_PYTHON PARENT_PATH _VENV_BIN_DIR)
if(WIN32)
    set(ENV{PATH} "${_VENV_BIN_DIR};$ENV{PATH}")
else()
    set(ENV{PATH} "${_VENV_BIN_DIR}:$ENV{PATH}")
endif()
include("${SPL_CORE_DIR}/spl.cmake")

# Variant data: one generation step, everything downstream declarative.
#
# tools/variant_data.py writes build/variants/<Variant>/<kit>/<target>.json for
# every variant, plus build/autoconf.json as the "current" pointer and a
# `generated` symlink to this build directory. It is invoked here so that
# configuring in the IDE keeps the pointer in step with whatever CMake Tools
# selected -- the same role cmake.copyCompileCommands plays for the compilation
# database.
#
# It is deliberately a standalone script and not CMake code. KConfig is pure
# Python, while the top-level project() call above demands a C toolchain before
# CMake will configure at all, so anything expressed here could only ever run on
# a machine that can build the software. The documentation, its quality gate and
# the IDE must not need a compiler, so the same script has to be runnable on its
# own:
#
#     python tools/variant_data.py --all
#
# Everything a condition in ubproject.toml or an {if} directive may name lives in
# these files -- the complete feature vector including the booleans KConfig omits,
# the variant, the build kit, the build target and the component list. A key that
# only conf.py knew would be invisible to ubCode and every other reader, and their
# view of the project would then silently disagree with the build.
set(_SPLED_VARIANT_DATA_SCRIPT ${CMAKE_SOURCE_DIR}/tools/variant_data.py)
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
    ${_SPLED_VARIANT_DATA_SCRIPT}
    ${CMAKE_SOURCE_DIR}/variants/${VARIANT}/parts.cmake
)
execute_process(
    COMMAND "${_VENV_PYTHON}" ${_SPLED_VARIANT_DATA_SCRIPT}
        --variant ${VARIANT}
        --kit ${BUILD_KIT}
        --target docs
        --current
        --build-dir ${CMAKE_BINARY_DIR}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    RESULT_VARIABLE _spled_variant_data_result
    OUTPUT_VARIABLE _spled_variant_data_output
    ERROR_VARIABLE _spled_variant_data_output
)
if(NOT _spled_variant_data_result EQUAL 0)
    message(FATAL_ERROR "tools/variant_data.py failed:\n${_spled_variant_data_output}")
endif()

# What spl-core's documentation targets need to know about this project. All of
# it has to be set before parts.cmake adds the components, which is where
# spl-core computes the paths it writes for Sphinx.
#
# The variant data file for each build shape. spl-core hands it to sphinx-build
# as `-D needs_variant_data_file=`, so a reports build evaluates its fences
# against the reports cell. `build/autoconf.json`, the pointer ubCode and a bare
# sphinx-build read, always holds the docs cell, so the IDE sees the report
# fences as a clean false.
set(SPL_VARIANT_DATA_FILE_DOCS ${CMAKE_SOURCE_DIR}/build/variants/${VARIANT}/${BUILD_KIT}/docs.json)
set(SPL_VARIANT_DATA_FILE_REPORTS ${CMAKE_SOURCE_DIR}/build/variants/${VARIANT}/${BUILD_KIT}/reports.json)

# Sphinx reaches this build directory through `generated`, the link
# tools/variant_data.py has just pointed at it. The generated report pages are
# therefore named `generated/...` whatever the variant, kit or build type, and
# the report sections name them directly instead of globbing `/build/**`.
# spl-core writes each coverage report next to its page under that name, and
# stops a documentation build whose link has since been re-pointed at another
# build directory.
set(SPL_SPHINX_BINARY_DIR ${CMAKE_SOURCE_DIR}/generated)

# No document is rendered through Jinja, so the source listings clanguru
# generates need no `{% raw %}` armour.
set(SPL_SOURCE_DOCS_JINJA_RAW_TAGS OFF)

# The object_deps_report extension is currently Windows-only: its index.cmake
# hardcodes the runner as "object_deps_report.exe", which does not exist on
# Linux/macOS (the console script is "object_deps_report"). Guard the include to
# Windows until the upstream .exe hardcoding is fixed (tracked upstream in the
# object_deps_report package).
if(BUILD_KIT STREQUAL prod AND WIN32)
    execute_process(
        COMMAND "${_VENV_PYTHON}" -c "import object_deps_report, os; print(os.path.dirname(object_deps_report.__file__))"
        OUTPUT_VARIABLE OBJECT_DEPS_REPORT_DIR
        OUTPUT_STRIP_TRAILING_WHITESPACE
        RESULT_VARIABLE OBJECT_DEPS_REPORT_RESULT
    )
    if(NOT OBJECT_DEPS_REPORT_RESULT EQUAL 0)
        message(FATAL_ERROR "Could not find object_deps_report Python package. Make sure the virtual environment is set up.")
    endif()
    include("${OBJECT_DEPS_REPORT_DIR}/index.cmake")
endif()

# Include variant specific parts/components definitions
include(${PROJECT_SOURCE_DIR}/variants/${VARIANT}/parts.cmake)
