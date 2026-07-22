set(CMAKE_C_COMPILER clang CACHE STRING "C Compiler")
set(CMAKE_CXX_COMPILER clang++ CACHE STRING "CXX Compiler")
set(CMAKE_ASM_COMPILER ${CMAKE_C_COMPILER} CACHE STRING "ASM Compiler")

# Link libraries required for POSIX functions like nanosleep
if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
    # On Linux, link with real-time library
    link_libraries(rt pthread)
elseif(APPLE)
    # On macOS, POSIX realtime functions are part of libc, no librt
    link_libraries(pthread)
elseif(WIN32 AND NOT MSVC)
    # On Windows with MinGW/Clang, link with pthread library
    link_libraries(pthread)
endif()
