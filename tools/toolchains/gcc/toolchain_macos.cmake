# The GCC test/coverage build kit requires the GNU compiler (see
# _spl_set_test_compile_and_link_options in spl-core, which hard-fails on
# anything but "GNU"). On macOS this must be Homebrew's native GCC, NOT the
# poks-provisioned one: poks ships a conda-forge cross-compiled GCC that links
# against Apple's system libc++ but was built against a different libc++
# header/ABI revision, causing "undefined symbol std::__1::__hash_memory"
# (and similar) link errors for any code using std::unordered_map/_set —
# including GoogleTest itself. Homebrew's GCC ships its own libstdc++ and
# does not have this mismatch.
#
# Homebrew installs versioned binaries (gcc-16, g++-16, ...) rather than
# unversioned `gcc`/`g++`, to avoid clashing with Xcode's `/usr/bin/gcc`
# (which is actually clang). Search a range of recent major versions.
find_program(CMAKE_C_COMPILER NAMES gcc-16 gcc-15 gcc-14 gcc-13 REQUIRED)
find_program(CMAKE_CXX_COMPILER NAMES g++-16 g++-15 g++-14 g++-13 REQUIRED)
set(CMAKE_ASM_COMPILER ${CMAKE_C_COMPILER} CACHE STRING "ASM Compiler")

set(COMPILE_CXX_FLAGS "")
add_compile_options(
    "$<$<COMPILE_LANGUAGE:CXX>:${COMPILE_CXX_FLAGS}>"
)
