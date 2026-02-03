# Detect platform and set appropriate GCC compiler
if(APPLE)
    # macOS: Use Homebrew GCC (Apple's /usr/bin/gcc is actually Clang)
    set(CMAKE_C_COMPILER /opt/homebrew/bin/gcc-15 CACHE STRING "C Compiler")
    set(CMAKE_CXX_COMPILER /opt/homebrew/bin/g++-15 CACHE STRING "CXX Compiler")
    set(CMAKE_ASM_COMPILER ${CMAKE_C_COMPILER} CACHE STRING "ASM Compiler")
    # No -mbig-obj on macOS
else()
    # Windows/Linux: Use system GCC with big-obj support for Windows
    set(CMAKE_C_COMPILER gcc CACHE STRING "C Compiler")
    set(CMAKE_CXX_COMPILER g++ CACHE STRING "CXX Compiler")
    set(CMAKE_ASM_COMPILER ${CMAKE_C_COMPILER} CACHE STRING "ASM Compiler")

    set(COMPILE_CXX_FLAGS "-Wa,-mbig-obj")
    add_compile_options(
        "$<$<COMPILE_LANGUAGE:CXX>:${COMPILE_CXX_FLAGS}>"
    )
endif()
