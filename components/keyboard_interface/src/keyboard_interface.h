#ifndef KEYBOARD_INTERFACE_H
#define KEYBOARD_INTERFACE_H

/* Include boolean type definition */
#ifdef _WIN32
    #include <windows.h>
#else
    #include <stdint.h>
    typedef unsigned char boolean;
    #define TRUE 1
    #define FALSE 0
#endif

boolean KeyboardInterfaceIsKeyPressed(int key);

#endif /* KEYBOARD_INTERFACE_H */
