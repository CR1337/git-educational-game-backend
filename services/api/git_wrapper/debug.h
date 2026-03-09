#ifndef __DEBUG_H__
#define __DEBUG_H__

void print_error(const char* source_filename, int line_number, 
                const char* function_name);
#define PRINT_ERROR(function_name) print_error(__FILE__, __LINE__, function_name)

#endif