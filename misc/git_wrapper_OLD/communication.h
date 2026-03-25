#ifndef __COMMUNICATION_H__
#define __COMMUNICATION_H__

#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>

typedef uint8_t communication_type_t;
typedef uint32_t communication_magic_t;

#define BUFFER_SIZE 8192 
#define COMMUNICATION_TYPE_SIZE (sizeof(communication_type_t))

#define PIPE_READ_END 0
#define PIPE_WRITE_END 1

#define COMMUNICATION_MAGIC "\1COM"
#define COMMUNICATION_MAGIC_SIZE (sizeof(communication_magic_t))

__attribute__((packed)) struct communication_signal_t {
    int32_t signal;
};

__attribute__((packed)) struct communication_git_result_t {
    int32_t returncode;
    uint64_t stdout_size;
    uint64_t stderr_size;
    uint64_t stdout_offset;
    uint64_t stderr_offset;
};

__attribute__((packed)) struct communication_editor_request_1_t {
    uint64_t filename_size;
    uint64_t content_size;
    uint64_t filename_offset;
    uint64_t content_offset;
};

__attribute__((packed)) struct communication_editor_request_2_t {
    uint64_t filename_size;
    uint64_t content_size;
    uint64_t stdout_size;
    uint64_t stderr_size;
    uint64_t filename_offset;
    uint64_t content_offset;
    uint64_t stdout_offset;
    uint64_t stderr_offset;
};

__attribute__((packed)) struct communication_editor_response_t {
    uint8_t abort;
    uint64_t content_size;
    uint64_t content_offset;
};

enum {
    COMMUNICATION_SIGNAL = 1,
    COMMUNICATION_GIT_RESULT = 2,
    COMMUNICATION_EDITOR_REQUEST_1 = 3,
    COMMUNICATION_EDITOR_REQUEST_2 = 4,
    COMMUNICATION_EDITOR_RESPONSE = 5
};

__attribute__((packed)) struct communication_packet_t {
    communication_magic_t magic;
    uint64_t size;
    communication_type_t type;
    __attribute__((packed)) union {
        struct communication_signal_t signal;
        struct communication_git_result_t git_result;
        struct communication_editor_request_1_t editor_request_1;
        struct communication_editor_request_2_t editor_request_2;
        struct communication_editor_response_t editor_response;
    } packet_content;
    size_t payload_size;
    uint8_t payload[];
};

bool communication_alloc_signal(int signal, struct communication_packet_t **packet, size_t *size);
bool communication_alloc_git_result(int returncode, size_t stdout_size, size_t stderr_size, char *git_stdout, char *git_stderr, struct communication_packet_t **packet, size_t *size);
bool communication_alloc_editor_request_1(size_t filename_size, size_t content_size, char *filename, char *content, struct communication_packet_t **packet, size_t *size);
bool communication_alloc_editor_request_2(size_t filename_size, size_t content_size, size_t stdout_size, size_t stderr_size, char *filename, char *content, char *git_stdout, char *git_stderr, struct communication_packet_t **packet, size_t *size);
bool communication_alloc_editor_response(bool abort, size_t content_size, char *content, struct communication_packet_t **packet, size_t *size);

bool communication_write(int fd, struct communication_packet_t *packet, size_t size);
bool communication_read(int fd, struct communication_packet_t **packet, size_t *size);

bool communication_read_raw(int fd, char **buffer, size_t *size);

#endif