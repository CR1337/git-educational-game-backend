#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h> 
#include <string.h>
#include <errno.h>

#include "debug.h"
#include "init.h"
#include "communication.h"
#include "util.h"

#pragma region STATE

struct state_t {
    // ipc
    char *editor_simulator_in_fifo_name;
    bool editor_simulator_in_fifo_created;
    int editor_simulator_in_fifo_fd;

    char *editor_simulator_out_fifo_name;
    bool editor_simulator_out_fifo_created;
    int editor_simulator_out_fifo_fd;

    int sigterm_pipe_read_fd;
    int sigterm_pipe_write_fd;

    // poll
    struct pollfd editor_simulator_poll_fd;
    struct pollfd sigterm_pollfd;

    // git
    char *git_editor_filename;
};
static struct state_t state = { 0 };

#pragma endregion

#pragma region CONFIGURATION

#define N_ARGUMENTS 1
static struct init_argument_config_t argument_config[N_ARGUMENTS] = {
    {
        .name = "git_editor_filename",
        .argument_type = STRING,
        .offset = 1,
        .string = &state.git_editor_filename
    }
};

void sigterm_handler(int signum);
#define N_SIGNALS 1
static struct init_signal_config_t signal_config[N_SIGNALS] = {
    {
        .signal = SIGTERM,
        .handler = sigterm_handler
    }
};

#define N_PIPES 1
static struct init_pipe_config_t pipe_config[N_PIPES] = {
    {
        .read_fd = &state.sigterm_pipe_read_fd,
        .write_fd = &state.sigterm_pipe_write_fd
    }
};

#define N_VARIABLES 2
static struct init_environment_config_t environment_config[N_VARIABLES] = {
    {
        .key = "EDITOR_SIMULATOR_IN_FIFO_NAME",
        .value = &state.editor_simulator_in_fifo_name
    },
    {
        .key = "EDITOR_SIMULATOR_OUT_FIFO_NAME",
        .value = &state.editor_simulator_out_fifo_name
    }
};

#define N_POLLFDS 2
static struct init_pollfd_config_t pollfd_config[N_POLLFDS] = {
    {
        .name = "orchestrator",
        .pollfd = &state.editor_simulator_poll_fd,
        .pollfd_type = POLLFD_EDITOR_SIMULATOR,
        .pollfd_event_type = POLLIN,
        .fd = &state.editor_simulator_out_fifo_fd
    },
    {
        .name = "sigterm",
        .pollfd = &state.sigterm_pollfd,
        .pollfd_type = POLLFD_SIGTERM,
        .pollfd_event_type = POLLIN,
        .fd = &state.sigterm_pipe_read_fd
    }
};

#pragma endregion

void sigterm_handler(int signum)
{
    char buffer[BUFFER_SIZE];
    size_t size = 0;
    communication_alloc_signal(signum, (struct communication_packet_t**)buffer, &size);
    if (!communication_write(state.sigterm_pipe_write_fd, (struct communication_packet_t*)buffer, size))
    {
        PRINT_ERROR_F("An error (%d) occurred inside the signal handler for SIGTERM\n", errno);
    }
}

bool read_file(char *filename, char *file_content, size_t *file_size)
{
    int fd = 0;
    if ((fd = open(filename, O_RDONLY)) == POSIX_ERROR)
    {
        PRINT_ERRNO_MESSAGE("open");
        return false;
    }

    ssize_t bytes_read = 0;
    if ((bytes_read = read(fd, file_content, BUFFER_SIZE)) == POSIX_ERROR)
    {
        PRINT_ERRNO_MESSAGE("read");
        return false;
    }
    *file_size = (size_t)bytes_read;

    if (close(fd) == POSIX_ERROR)
    {
        PRINT_ERRNO_MESSAGE("close");
        return false;
    }

    return true;
}

bool send_request(char *file_content, size_t file_size)
{
   struct communication_packet_t *packet = NULL;
    size_t packet_size = 0;
    if (!communication_alloc_editor_request_1(strlen(state.git_editor_filename), file_size, state.git_editor_filename, file_content, &packet, &packet_size))
    {
        return false;
    }
    if (!communication_write(state.editor_simulator_in_fifo_fd, packet, packet_size))
    {
        free(packet);
        return false;
    }

    free(packet);
    return true;
}

bool handle_sigterm(struct communication_packet_t *packet)
{
    if (packet->type != COMMUNICATION_SIGNAL)
    {
        PRINT_ERROR_F("Unexpected packet type: %d\n", packet->type);
        return false;
    }

    if (remove(state.git_editor_filename) == POSIX_ERROR)
    {
        PRINT_ERRNO_MESSAGE("remove");
        return false;
    }

    return true;
}

bool handle_editor_content(struct communication_packet_t *packet, char *new_file_content, size_t *new_file_size, bool *abort)
{
    if (packet->type != COMMUNICATION_EDITOR_RESPONSE)
    {
        PRINT_ERROR_F("Unexpected packet type: %d\n", packet->type);
        return false;
    }

    *abort = packet->packet_content.editor_response.abort;
    *new_file_size = packet->packet_content.editor_response.content_size;
    memcpy(new_file_content, packet->payload, packet->packet_content.editor_response.content_size);

    return true;
}

bool wait_for_response(char *new_file_content, size_t *new_file_size, bool *abort)
{
    struct pollfd fds[N_POLLFDS] = {
        *pollfd_config[0].pollfd,
        *pollfd_config[1].pollfd
    };

    int poll_result = -1;
    do {
        poll_result = poll(fds, N_POLLFDS, -1);
    } while (poll_result == -1 && errno == EINTR);

    if (poll_result == POSIX_ERROR)
    {
        PRINT_ERRNO_MESSAGE("poll");
        return false;
    }

    bool done = false;
    while (!done)
    {
        for (size_t i = 0; i < N_POLLFDS; ++i)
        {
            if (!fds[i].revents)
            {
                continue;
            }

            if (fds[i].revents & (POLLHUP | POLLERR | POLLNVAL))
            {
                PRINT_ERROR_F("A file descriptor (%d) is in an error state: %x\n", fds[i].fd, fds[i].revents);
                return false;
            }

            if (fds[i].revents != pollfd_config[i].pollfd_event_type)
            {
                PRINT_ERROR_F("Unexpected poll event: %x\n", fds[i].revents);
            }

            char buffer[BUFFER_SIZE];
            struct communication_packet_t *packet = (struct communication_packet_t *)&buffer;
            bool success = false;

            switch (pollfd_config[i].pollfd_type)
            {
                case POLLFD_SIGTERM:
                    success = handle_sigterm(packet);
                    done = success;
                    break;

                case POLLFD_EDITOR_SIMULATOR:
                    success = handle_editor_content(packet, new_file_content, new_file_size, abort);
                    break;

                default:
                    break;
            }

            if (!success)
            {
                return false;
            }
        }
    }

    return true;   
}

bool write_file(char *filename, char *file_content, size_t file_size)
{
    int fd = 0;
    if ((fd = open(filename, O_WRONLY)) == POSIX_ERROR)
    {
        PRINT_ERRNO_MESSAGE("open");
        return false;
    }

    if (write(fd, file_content, file_size) == POSIX_ERROR)
    {
        PRINT_ERRNO_MESSAGE("write");
        return false;
    }

    if (close(fd) == POSIX_ERROR)
    {
        PRINT_ERRNO_MESSAGE("close");
        return false;
    }

    return true;
}

bool initialize(int argc, char *argv[])
{
    if (
        !init_read_arguments(argc, argv, argument_config, N_ARGUMENTS)
        || !init_signals(signal_config, N_SIGNALS)
        || !init_pipes(pipe_config, N_PIPES)
        || !init_get_environment(environment_config, N_VARIABLES)
        || !init_pollfds(pollfd_config, N_POLLFDS)
    )
    {
        return false;
    }

    return true;
}

void cleanup()
{
    cleanup_pollfds(pollfd_config, N_POLLFDS);
}

int main(int argc, char *argv[])
{
    if (!initialize(argc, argv))
    {
        goto ERROR;
    }

    char file_content[BUFFER_SIZE];
    size_t file_size = 0;
    if (!read_file(state.git_editor_filename, file_content, &file_size))
    {
        goto ERROR;
    }

    if (!send_request(file_content, file_size))
    {
        goto ERROR;
    }

    bool abort = false;
    if (!wait_for_response(file_content, &file_size, &abort))
    {
        goto ERROR;
    }
    if (abort)
    {
        goto EXIT;
    }

    if (!write_file(state.git_editor_filename, file_content, file_size))
    {
        goto ERROR;
    }

EXIT:
    cleanup();
    return EXIT_SUCCESS;

ERROR:
    cleanup();
    return EXIT_FAILURE;
}