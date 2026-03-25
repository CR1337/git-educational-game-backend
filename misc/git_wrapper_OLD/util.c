#include "util.h"

#include <stdlib.h>
#include <errno.h>
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>

#include "debug.h"

#define BASE_10 10

bool parse_uint64(char *string, uint64_t *value)
{
    char *endptr;
    errno = 0;

    *value = strtoull(string, &endptr, BASE_10);

    if (errno == ERANGE)
    {
        PRINT_ERRNO_MESSAGE("strtoull");
        return false;
    }

    if (endptr == string) {
        PRINT_ERROR_F("Error: No digits found in input: %s\n", string);
        return false;
    }

    if (*endptr != '\0') {
        PRINT_ERROR_F("Error: Trailing invalid characters in input: %s\n", string);
        return false;
    }

    return true;
}

bool generate_uuid(char *uuid)
{
    const size_t BYTES_SIZE = 16;
    char bytes[BYTES_SIZE];
    int fd = 0;

    if ((fd = open("/dev/urandom", O_RDONLY)) == -1)
    {
        PRINT_ERRNO_MESSAGE("open");
        return false;
    }
    if (read(fd, bytes, BYTES_SIZE) == -1)
    {
        PRINT_ERRNO_MESSAGE("read");
        return false;
    }
    if (close(fd) == -1)
    {
        PRINT_ERRNO_MESSAGE("close");
        return false;
    }

    snprintf(uuid, UUID_SIZE,
        "%02x%02x%02x%02x-"
        "%02x%02x-"
        "%02x%02x-"
        "%02x%02x-"
        "%02x%02x%02x%02x%02x%02x",
        bytes[0], bytes[1], bytes[2], bytes[3],
        bytes[4], bytes[5],
        bytes[6], bytes[7],
        bytes[8], bytes[9],
        bytes[10], bytes[11], bytes[12], bytes[13], bytes[14], bytes[15]
    );
    uuid[36] = '\0';

    return true;
}