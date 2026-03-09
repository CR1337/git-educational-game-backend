#include "debug.h"

#include <stdio.h>

void print_error(const char* source_filename, int line_number, 
                const char* function_name)
{
    fprintf(stderr, "%s:%d: %s: ", source_filename, line_number, function_name);
    perror("");
}