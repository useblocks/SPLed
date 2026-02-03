#include "keyboard_interface.h"

#ifdef _WIN32
    #include <windows.h>
#else
    /* Platform-independent stub for non-Windows systems */
    #define GetAsyncKeyState(key) (0)
#endif

boolean KeyboardInterfaceIsKeyPressed(int key)
{
    #ifdef _WIN32
        return (GetAsyncKeyState(key) & 0x8000) != 0;
    #else
        /* On non-Windows systems, always return false (no key pressed) */
        (void)key; /* Suppress unused parameter warning */
        return 0;
    #endif
}
