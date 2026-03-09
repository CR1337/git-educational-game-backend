#ifndef __DEBUG_H
#define __DEBUG_H

#include <errno.h>
#include <string.h>
#include <stdio.h>

#define COLOR_RED "\033[31m"
#define COLOR_GREEN "\033[32m"
#define COLOR_RESET "\033[0m"

#ifdef _DEBUG
void debug_print(const char *color, const char *message, ...)
{
    va_list args;
    va_start(args, message);
    fprintf(stderr, "%s", color);
    vfprintf(stderr, message, args);
    fprintf(stderr, "%s", COLOR_RESET);
    va_end(args);
}

void print_error(const char *color)
{
    if (!errno)
    {
        return;
    }
    
    fprintf(
        stderr,
        "%s\t(%d): %s%s\n",
        color,
        errno,
        strerror(errno),
        COLOR_RESET
    );
}
#else
void debug_print(const char *color, const char *message, ...) {}
void print_error(const char *color) {}
#endif

#endif