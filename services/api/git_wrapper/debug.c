#include "debug.h"

#include <stdio.h>
#include <stdarg.h>
#include <errno.h>
#include <string.h>

void print_errno_message(const char *source_filename,
                         int line_number,
                         const char *function_name,
                         const char *format,
                         ...)
{
    fprintf(stderr, "%s:%d (%s): ",
            source_filename,
            line_number,
            function_name);

    perror("");

    if (format != NULL)
    {
        fputs(" (", stderr);
        va_list args;
        va_start(args, format);
        vfprintf(stderr, format, args);
        va_end(args);
        fputs(")", stderr);
    }

    fputs("\n", stderr);
}


void print_debug(const char *source_filename,
                 int line_number,
                 const char *format,
                 ...)
{
    fprintf(stderr, "%s:%d: ",
            source_filename,
            line_number);

    if (format != NULL)
    {
        va_list args;
        va_start(args, format);
        vfprintf(stderr, format, args);
        va_end(args);
    }

    fputs("\n", stderr);
}