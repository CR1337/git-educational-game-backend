#include "communication.h"

#include <string.h>
#include <stdbool.h>
#include <unistd.h>
#include <errno.h>
#include <assert.h>

#include "debug.h"
#include "util.h"


bool communication_alloc_signal(int signal, struct communication_packet_t **packet, size_t *size)
{
    const size_t payload_size = 0;
    *size = sizeof(struct communication_packet_t) + payload_size;

    if (!(*packet = (struct communication_packet_t *)malloc(*size)))
    {
        PRINT_ERRNO_MESSAGE("malloc");
        return false;
    }

    memcpy(&(*packet)->magic, COMMUNICATION_MAGIC, COMMUNICATION_MAGIC_SIZE);
    (*packet)->size = sizeof(struct communication_packet_t) + payload_size;
    (*packet)->type = COMMUNICATION_SIGNAL;
    (*packet)->payload_size = payload_size;

    (*packet)->packet_content.signal.signal = signal;

    return true;
}

bool communication_alloc_git_result(int returncode, size_t stdout_size, size_t stderr_size, char *git_stdout, char *git_stderr, struct communication_packet_t **packet, size_t *size)
{
    const size_t payload_size = stdout_size + stderr_size;
    *size = sizeof(struct communication_packet_t) + payload_size;

    if (!(*packet = (struct communication_packet_t *)malloc(*size)))
    {
        PRINT_ERRNO_MESSAGE("malloc");
        return false;
    }

    memcpy(&(*packet)->magic, COMMUNICATION_MAGIC, COMMUNICATION_MAGIC_SIZE);
    (*packet)->size = sizeof(struct communication_packet_t) + payload_size;
    (*packet)->type = COMMUNICATION_GIT_RESULT;
    (*packet)->payload_size = payload_size;

    (*packet)->packet_content.git_result.returncode = returncode;

    (*packet)->packet_content.git_result.stdout_size = stdout_size;
    (*packet)->packet_content.git_result.stderr_size = stderr_size;

    (*packet)->packet_content.git_result.stdout_offset = 0;
    (*packet)->packet_content.git_result.stderr_offset = stdout_size;

    memcpy((*packet)->payload, git_stdout, stdout_size);
    memcpy((*packet)->payload + stdout_size, git_stderr, stderr_size);
    
    return true;
}

bool communication_alloc_editor_request_1(size_t filename_size, size_t content_size, char *filename, char *content, struct communication_packet_t **packet, size_t *size)
{
    const size_t payload_size = filename_size + content_size;
    *size = sizeof(struct communication_packet_t) + payload_size;

    if (!(*packet = (struct communication_packet_t *)malloc(*size)))
    {
        PRINT_ERRNO_MESSAGE("malloc");
        return false;
    }

    memcpy(&(*packet)->magic, COMMUNICATION_MAGIC, COMMUNICATION_MAGIC_SIZE);
    (*packet)->size = sizeof(struct communication_packet_t) + payload_size;
    (*packet)->type = COMMUNICATION_EDITOR_REQUEST_1;
    (*packet)->payload_size = payload_size;

    (*packet)->packet_content.editor_request_1.filename_size = filename_size;
    (*packet)->packet_content.editor_request_1.content_size = content_size;

    (*packet)->packet_content.editor_request_1.filename_offset = 0;
    (*packet)->packet_content.editor_request_1.content_offset = filename_size;

    memcpy((*packet)->payload, filename, filename_size);
    memcpy((*packet)->payload + filename_size, content, content_size);

    return true;
}

bool communication_alloc_editor_request_2(size_t filename_size, size_t content_size, size_t stdout_size, size_t stderr_size, char *filename, char *content, char *git_stdout, char *git_stderr, struct communication_packet_t **packet, size_t *size)
{
    const size_t payload_size = filename_size + content_size + stdout_size + stderr_size;
    *size = sizeof(struct communication_packet_t) + payload_size;

    if (!(*packet = (struct communication_packet_t *)malloc(*size)))
    {
        PRINT_ERRNO_MESSAGE("malloc");
        return false;
    }

    memcpy(&(*packet)->magic, COMMUNICATION_MAGIC, COMMUNICATION_MAGIC_SIZE);
    (*packet)->size = sizeof(struct communication_packet_t) + payload_size;
    (*packet)->type = COMMUNICATION_EDITOR_REQUEST_2;
    (*packet)->payload_size = payload_size;

    (*packet)->packet_content.editor_request_2.filename_size = filename_size;
    (*packet)->packet_content.editor_request_2.content_size = content_size;
    (*packet)->packet_content.editor_request_2.stdout_size = stdout_size;
    (*packet)->packet_content.editor_request_2.stderr_size = stderr_size;

    (*packet)->packet_content.editor_request_2.filename_offset = 0;
    (*packet)->packet_content.editor_request_2.content_offset = filename_size;
    (*packet)->packet_content.editor_request_2.stdout_offset = filename_size + content_size;
    (*packet)->packet_content.editor_request_2.stderr_offset = filename_size + content_size + stdout_size;

    memcpy((*packet)->payload, filename, filename_size);
    memcpy((*packet)->payload + filename_size, content, content_size);
    memcpy((*packet)->payload + filename_size + content_size, git_stdout, stdout_size);
    memcpy((*packet)->payload + filename_size + content_size + stdout_size, git_stderr, stderr_size);
    
    return true;
}

bool communication_alloc_editor_response(bool abort, size_t content_size, char *content, struct communication_packet_t **packet, size_t *size)
{
    const size_t payload_size = content_size;
    *size = sizeof(struct communication_packet_t) + payload_size;

    if (!(*packet = (struct communication_packet_t *)malloc(*size)))
    {
        PRINT_ERRNO_MESSAGE("malloc");
        return false;
    }
    
    memcpy(&(*packet)->magic, COMMUNICATION_MAGIC, COMMUNICATION_MAGIC_SIZE);
    (*packet)->size = sizeof(struct communication_packet_t) + payload_size;
    (*packet)->type = COMMUNICATION_EDITOR_RESPONSE;
    (*packet)->payload_size = payload_size;

    (*packet)->packet_content.editor_response.abort = abort;
    
    (*packet)->packet_content.editor_response.content_size = content_size;

    (*packet)->packet_content.editor_response.content_offset = 0;

    memcpy((*packet)->payload, content, content_size);

    return true;
}

bool communication_write(int fd, struct communication_packet_t *packet, size_t size)
{
    if (write(fd, packet, size) == -1)
    {
        PRINT_ERRNO_MESSAGE("write");
        return false;
    }
    return true;
}

bool communication_read(int fd, struct communication_packet_t **packet, size_t *size)
{
    return communication_read_raw(fd, (char**)packet, size);
}

bool communication_read_raw(int fd, char **buffer, size_t *size)
{
    size_t growing_buffer_size = BUFFER_SIZE;

    if (!(*buffer = (char*)malloc(growing_buffer_size)))
    {
        PRINT_ERRNO_MESSAGE("malloc");
        return false;
    }

    size_t total_bytes_read = 0;
    ssize_t bytes_read = 0;

    // read magic
    bytes_read = read(fd, *buffer, COMMUNICATION_MAGIC_SIZE);
    if (bytes_read == POSIX_ERROR)
    {
        free(*buffer);
        PRINT_ERRNO_MESSAGE("read");
        return false;
    }
    if (bytes_read < (ssize_t)COMMUNICATION_MAGIC_SIZE)
    {
        *size = bytes_read;
        return true;
    }

    assert(bytes_read == COMMUNICATION_MAGIC_SIZE);
    total_bytes_read += bytes_read;

    if (!memcmp(*buffer, COMMUNICATION_MAGIC, COMMUNICATION_MAGIC_SIZE))
    {
        bytes_read = read(fd, *buffer + COMMUNICATION_MAGIC_SIZE, sizeof(uint64_t));
        if (bytes_read == POSIX_ERROR)
        {
            free(*buffer);
            PRINT_ERRNO_MESSAGE("read");
            return false;
        }
        total_bytes_read += bytes_read;

        uint64_t packet_size = *((uint64_t*)(*buffer + COMMUNICATION_MAGIC_SIZE));
        packet_size -= COMMUNICATION_MAGIC_SIZE + sizeof(uint64_t);

        bytes_read = read(fd, *buffer + COMMUNICATION_MAGIC_SIZE + sizeof(uint64_t), packet_size);
        if (bytes_read == POSIX_ERROR)
        {
            free(*buffer);
            PRINT_ERRNO_MESSAGE("read");
            return false;
        }
        total_bytes_read += bytes_read;

        *size = total_bytes_read;
        return true;
    }

    while ((bytes_read = read(fd, *buffer, BUFFER_SIZE)) > 0)
    {
        if (bytes_read == -1)
        {
            if (errno == EAGAIN || errno == EWOULDBLOCK)
            {
                *size = total_bytes_read;
                return true;
            }
            else
            {
                free(*buffer);
                PRINT_ERRNO_MESSAGE("read");
                return false;
            }
        }

        total_bytes_read += bytes_read;
        growing_buffer_size += BUFFER_SIZE;
        if (!(*buffer = (char*)realloc(*buffer, growing_buffer_size)))
        {
            free(*buffer);
            PRINT_ERRNO_MESSAGE("realloc");
            return false;
        }
    }

    *size = total_bytes_read;

    return true;
}
