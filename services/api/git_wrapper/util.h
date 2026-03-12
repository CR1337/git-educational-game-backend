#ifndef __UTIL_H__
#define __UTIL_H__

#include <stdint.h>
#include <stdbool.h>

#define UUID_SIZE 37
#define POSIX_ERROR -1

bool parse_uint64(char *string, uint64_t *value);
bool generate_uuid(char *uuid);

#endif