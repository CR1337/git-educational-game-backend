#ifndef __COMMUNICATION_H__
#define __COMMUNICATION_H__

#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>

typedef uint8_t communication_type_t;

extern size_t BUFFER_SIZE; 
extern size_t COMMUNICATION_TYPE_SIZE;

__attribute__((packed)) struct communication_signal_t {
    int32_t signal;
};

__attribute__((packed)) struct communication_git_result_t {
    int32_t returncode;
    uint64_t stdout_size;
    uint64_t stderr_size;
    uint8_t stdout_stderr[];
};

__attribute__((packed)) struct communication_stdin_request_t {
    uint64_t stdout_size;
    uint64_t stderr_size;
    uint8_t stdout_stderr[];
};

__attribute__((packed)) struct communication_stdin_response_t {
    uint64_t stdin_size;
    uint8_t stdin_[];
};

__attribute__((packed)) struct communication_editor_request_t {
    uint64_t filename_size;
    uint64_t content_size;
    uint8_t filename_content[];
};

__attribute__((packed)) struct communication_editor_response_t {
    uint8_t abort;
    uint64_t content_size;
    uint8_t content[];
};

enum {
    COMMUNICATION_SIGNAL,
    COMMUNICATION_GIT_RESULT,
    COMMUNICATION_STDIN_REQUEST,
    COMMUNICATION_STDIN_RESPONSE,
    COMMUNICATION_EDITOR_REQUEST,
    COMMUNICATION_EDITOR_RESPONSE
};

__attribute__((packed)) struct communication_packet_t {
    communication_type_t type;
    union {
        struct communication_signal_t signal;
        struct communication_git_result_t git_result;
        struct communication_stdin_request_t stdin_request;
        struct communication_stdin_response_t stdin_response;
        struct communication_editor_request_t editor_request;
        struct communication_editor_response_t editor_response;
    } packet_content;
};

void communication_pack_signal(int signal, struct communication_packet_t *packet, size_t *size);
void communication_pack_git_result(int returncode, size_t stdout_size, size_t stderr_size, char *stdout_, char *stderr_, struct communication_packet_t *packet, size_t *size);
void communication_pack_stdin_request(size_t stdout_size, size_t stderr_size, char *stdout_, char *stderr_, struct communication_packet_t *packet, size_t *size);
void communication_pack_stdin_response(size_t stdin_size, char *stdin_, struct communication_packet_t *packet, size_t *size);
void communication_pack_editor_request(size_t filename_size, size_t content_size, char *filename, char *content, struct communication_packet_t *packet, size_t *size);
void communication_pack_editor_response(bool abort, size_t content_size, char *content, struct communication_packet_t *packet, size_t *size);

bool communication_read_signal(int fd, struct communication_signal_t *signal);
bool communincation_read_git_result(int fd, struct communication_git_result_t *git_result);
bool communincation_read_stdin_request(int fd, struct communication_stdin_request_t *stdin_request);
bool communincation_read_stdin_response(int fd, struct communication_stdin_response_t *stdin_response);
bool communincation_read_editor_request(int fd, struct communication_editor_request_t *editor_request);
bool communincation_read_editor_response(int fd, struct communication_editor_response_t *editor_response);

bool communication_write(int fd, struct communication_packet_t *packet, size_t size);
bool communication_read(int fd, struct communication_packet_t *packet, size_t *size);
bool communication_transfer(int source_df, int destination_fd);

#endif