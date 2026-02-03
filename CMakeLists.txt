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

# Find the correct Python site-packages directory for the venv
if(WIN32)
    set(VENV_SITE_PACKAGES ".venv/Lib/site-packages")
else()
    # macOS and Linux use lib/pythonX.X/site-packages
    file(GLOB_RECURSE SPL_CMAKE_PATH "${PROJECT_SOURCE_DIR}/.venv/lib/*/site-packages/spl_core/spl.cmake")
    if(SPL_CMAKE_PATH)
        get_filename_component(VENV_SITE_PACKAGES "${SPL_CMAKE_PATH}" DIRECTORY)
        get_filename_component(VENV_SITE_PACKAGES "${VENV_SITE_PACKAGES}" DIRECTORY)
    else()
        message(FATAL_ERROR "Could not find spl_core in .venv/lib/*/site-packages/spl_core/spl.cmake")
    endif()
endif()

# Include spl-core
include("${VENV_SITE_PACKAGES}/spl_core/spl.cmake")

# Include variant specific parts/components definitions
include(${CMAKE_SOURCE_DIR}/variants/${VARIANT}/parts.cmake)
