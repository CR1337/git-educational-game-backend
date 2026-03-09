#include "communication.h"

#include <string.h>
#include <stdbool.h>
#include <unistd.h>

#include "debug.h"

const size_t BUFFER_SIZE = 8192;
const size_t COMMUNICATION_TYPE_SIZE = sizeof(communication_type_t);

void communication_pack_signal(int signal, struct communication_packet_t *packet, size_t *size)
{
    packet->type = COMMUNICATION_SIGNAL;
    packet->packet_content.signal.signal = signal;
    *size = COMMUNICATION_TYPE_SIZE + sizeof(struct communication_signal_t);
}

void communication_pack_git_result(int returncode, size_t stdout_size, size_t stderr_size, char *stdout_, char *stderr_, struct communication_packet_t *packet, size_t *size)
{
    packet->type = COMMUNICATION_GIT_RESULT;
    packet->packet_content.git_result.returncode = returncode;
    packet->packet_content.git_result.stdout_size = stdout_size;
    packet->packet_content.git_result.stderr_size = stderr_size;
    memcpy(packet->packet_content.git_result.stdout_stderr, stdout_, stdout_size);
    memcpy(packet->packet_content.git_result.stdout_stderr + stdout_size, stderr_, stderr_size);
    *size = COMMUNICATION_TYPE_SIZE + sizeof(struct communication_git_result_t) + stdout_size + stderr_size;
}

void communication_pack_stdin_request(size_t stdout_size, size_t stderr_size, char *stdout_, char *stderr_, struct communication_packet_t *packet, size_t *size)
{
    packet->type = COMMUNICATION_STDIN_REQUEST;
    packet->packet_content.stdin_request.stdout_size = stdout_size;
    packet->packet_content.stdin_request.stderr_size = stderr_size;
    memcpy(packet->packet_content.stdin_request.stdout_stderr, stdout_, stdout_size);
    memcpy(packet->packet_content.stdin_request.stdout_stderr + stdout_size, stderr_, stderr_size);
    *size = COMMUNICATION_TYPE_SIZE + sizeof(struct communication_stdin_request_t) + stdout_size + stderr_size;
}

void communication_pack_stdin_response(size_t stdin_size, char *stdin_, struct communication_packet_t *packet, size_t *size)
{
    packet->type = COMMUNICATION_STDIN_RESPONSE;
    packet->packet_content.stdin_response.stdin_size = stdin_size;
    memcpy(packet->packet_content.stdin_response.stdin_, stdin_, stdin_size);
    *size = COMMUNICATION_TYPE_SIZE + sizeof(struct communication_stdin_response_t) + stdin_size;
}

void communication_pack_editor_request(size_t filename_size, size_t content_size, char *filename, char *content, struct communication_packet_t *packet, size_t *size)
{
    packet->type = COMMUNICATION_EDITOR_REQUEST;
    packet->packet_content.editor_request.filename_size = filename_size;
    packet->packet_content.editor_request.content_size = content_size;
    memcpy(packet->packet_content.editor_request.filename_content, filename, filename_size);
    memcpy(packet->packet_content.editor_request.filename_content + filename_size, content, content_size);
    *size = COMMUNICATION_TYPE_SIZE + sizeof(struct communication_editor_request_t) + filename_size + content_size;
}

void communication_pack_editor_response(bool abort, size_t content_size, char *content, struct communication_packet_t *packet, size_t *size)
{
    packet->type = COMMUNICATION_EDITOR_RESPONSE;
    packet->packet_content.editor_response.abort = abort;
    packet->packet_content.editor_response.content_size = content_size;
    memcpy(packet->packet_content.editor_response.content, content, content_size);
    *size = COMMUNICATION_TYPE_SIZE + sizeof(struct communication_editor_response_t) + content_size;
}

bool _communication_read_packet_content(int fd, communication_type_t type, char *buffer)
{
    struct communication_packet_t packet;
    size_t size = 0;
    communication_read(fd, &packet, &size);
    if (packet.type != type)
    {
        // TODO: error
        return false;
    }
    memcpy(buffer, &packet.packet_content, size);
    return true;
}

bool communication_read_signal(int fd, struct communication_signal_t *signal)
{
    if (!_communication_read_packet_content(fd, COMMUNICATION_SIGNAL, signal))
    {
        return false;
    }
    return true;
}

bool communincation_read_git_result(int fd, struct communication_git_result_t *git_result)
{
    if (!_communication_read_packet_content(fd, COMMUNICATION_GIT_RESULT, git_result))
    {
        return false;
    }
    return true;
}

bool communincation_read_stdin_request(int fd, struct communication_stdin_request_t *stdin_request)
{
    if (!_communication_read_packet_content(fd, COMMUNICATION_STDIN_REQUEST, stdin_request))
    {
        return false;
    }
    return true;
}

bool communincation_read_stdin_response(int fd, struct communication_stdin_response_t *stdin_response)
{
    if (!_communication_read_packet_content(fd, COMMUNICATION_STDIN_RESPONSE, stdin_response))
    {
        return false;
    }
    return true;
}

bool communincation_read_editor_request(int fd, struct communication_editor_request_t *editor_request)
{
    if (!_communication_read_packet_content(fd, COMMUNICATION_EDITOR_REQUEST, editor_request))
    {
        return false;
    }
    return true;
}

bool communincation_read_editor_response(int fd, struct communication_editor_response_t *editor_response)
{
    if (!_communication_read_packet_content(fd, COMMUNICATION_EDITOR_RESPONSE, editor_response))
    {
        return false;
    }
    return true;
}


bool communication_write(int fd, struct communication_packet_t *packet, size_t size)
{
    if (write(fd, packet, size) == -1)
    {
        PRINT_ERROR("write");
        return false;
    }
    return true;
}

bool communication_read(int fd, struct communication_packet_t *packet, size_t *size)
{
    ssize_t bytes_read = 0;
    if (bytes_read = read(fd, packet, BUFFER_SIZE) == -1)
    {
        PRINT_ERROR("read");
        return false;
    }
    size = bytes_read;
    return true;
}

bool communication_transfer(int source_df, int destination_fd)
{
    struct communication_packet_t packet;
    size_t size = 0;
    if (!communication_read(source_df, &packet, &size))
    {
        return false;
    }
    if (!communication_write(destination_fd, &packet, size))
    {
        return false;
    }
    return true;
}
