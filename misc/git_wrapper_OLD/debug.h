#ifndef DEBUG_H
#define DEBUG_H

#include <stdio.h>
#include <string.h>

void print_errno_message(const char *source_filename,
                         int line_number,
                         const char *function_name,
                         const char *format,
                         ...);

void print_debug(const char *source_filename,
                 int line_number,
                 const char *format,
                 ...);

/* extract filename without path */
#define __FILENAME__ (strrchr(__FILE__, '/') ? strrchr(__FILE__, '/') + 1 : __FILE__)

#ifdef DEBUG

#define PRINT_ERRNO_MESSAGE_F(function_name, format, ...) \
    print_errno_message(__FILENAME__, __LINE__, function_name, format, ##__VA_ARGS__)

#define PRINT_ERRNO_MESSAGE(function_name) \
    print_errno_message(__FILENAME__, __LINE__, function_name, NULL)

#define PRINT_DEBUG_F(format, ...) \
    print_debug(__FILENAME__, __LINE__, format, ##__VA_ARGS__)
    
#else

#define NOP do {} while (0)

#define PRINT_ERRNO_MESSAGE_F(...) NOP
#define PRINT_ERRNO_MESSAGE(...) NOP
#define PRINT_DEBUG_F(...) NOP

#endif

#define PRINT_ERROR_F(...) PRINT_DEBUG_F(__VA_ARGS__)

#endif