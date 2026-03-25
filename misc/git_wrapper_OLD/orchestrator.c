#include <stdlib.h>
#include <stdio.h>
#include <signal.h>
#include <unistd.h>
#include <sys/wait.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <stdbool.h>
#include <poll.h>
#include <limits.h>
#include <stdint.h>
#include <string.h>
#include <pty.h>
#include <termios.h>
#include <errno.h>

#include "debug.h"
#include "init.h"
#include "communication.h"
#include "util.h"

#pragma region STATE 

enum git_state_t { 
    NOT_RUNNING = 0, 
    RUNNING, 
    WAIT_FOR_EDITOR_CONTENT
};
struct state_t {
    // ipc
    char *server_in_fifo_name;
    int server_in_fifo_fd;

    char *server_out_fifo_name;
    int server_out_fifo_fd;

    char *editor_simulator_in_fifo_name;
    int editor_simulator_in_fifo_fd;

    char *editor_simulator_out_fifo_name;
    int editor_simulator_out_fifo_fd;

    int sigterm_pipe_read_fd;
    int sigterm_pipe_write_fd;

    int sigchld_pipe_read_fd;
    int sigchld_pipe_write_fd;

    int git_stdin_fd;
    int git_stdout_fd;
    int git_stderr_fd;

    // poll
    struct pollfd sigterm_pollfd;
    struct pollfd sigchld_pollfd;
    struct pollfd editor_simulator_fifo_pollfd;
    struct pollfd server_fifo_pollfd;

    // git
    char *git_executable;
    size_t git_argc;
    char **git_argv;
    char *git_editor;
    pid_t git_pid;
    enum git_state_t git_state;
    char git_editor_filename[BUFFER_SIZE];
    int git_returncode;
};
static struct state_t state = { 0 };

#pragma endregion

#pragma region CONFIGURATION

#define N_ARGUMENTS 6
static struct init_argument_config_t argument_config[N_ARGUMENTS] = {
    {
        .name = "server_in_fifo_name",
        .argument_type = STRING,
        .offset = 1,
        .string = &state.server_in_fifo_name
    },
    {
        .name = "server_out_fifo_name",
        .argument_type = STRING,
        .offset = 2,
        .string = &state.server_out_fifo_name
    },
    {
        .name = "git_editor",
        .argument_type = STRING,
        .offset = 3,
        .string = &state.git_editor
    },
    {
        .name = "git_executable",
        .argument_type = STRING,
        .offset = 4,
        .string = &state.git_executable
    },
    {
        .name = "git_argc",
        .argument_type = NUMBER,
        .offset = 5,
        .number = &state.git_argc
    },
    {
        .name = "git_argv",
        .argument_type = STRING_LIST,  // There can only be one argument of type string list and it mus be the last one.
        .offset = 6,
        .string_list = &state.git_argv
    }
};

void sigterm_handler(int signum);
void sigchld_handler(int signum);
#define N_SIGNALS 2
static struct init_signal_config_t signal_config[N_SIGNALS] = {
    {
        .signal = SIGTERM,
        .handler = sigterm_handler
    },
    {
        .signal = SIGCHLD,
        .handler = sigchld_handler
    }
};

#define N_FIFOS 4
static struct init_fifo_config_t fifo_config[N_FIFOS] = {
    { 
        .generate_name = false,
        .name = &state.server_in_fifo_name,
        .mode = O_RDWR | O_NONBLOCK,
        .permissions = 0666,
        .created_flag = true,
        .fd = &state.server_in_fifo_fd
    },
    { 
        .generate_name = false,
        .name = &state.server_out_fifo_name,
        .mode = O_RDWR | O_NONBLOCK,
        .permissions = 0666,
        .created_flag = true,
        .fd = &state.server_out_fifo_fd
    },
    { 
        .generate_name = true,
        .name = &state.editor_simulator_in_fifo_name,
        .mode = O_RDWR | O_NONBLOCK,
        .permissions = 0666,
        .created_flag = false,
        .fd = &state.editor_simulator_in_fifo_fd
    },
    { 
        .generate_name = true,
        .name = &state.editor_simulator_out_fifo_name,
        .mode = O_RDWR | O_NONBLOCK,
        .permissions = 0666,
        .created_flag = false,
        .fd = &state.editor_simulator_out_fifo_fd
    }
};

#define N_PIPES 2
static struct init_pipe_config_t pipe_config[N_PIPES] = {
    {
        .read_fd = &state.sigterm_pipe_read_fd,
        .write_fd = &state.sigterm_pipe_write_fd
    },
    {
        .read_fd = &state.sigchld_pipe_read_fd,
        .write_fd = &state.sigchld_pipe_write_fd
    }
};

#define N_VARIABLES 3
static struct init_environment_config_t environment_config[N_VARIABLES] = {
    {
        .key = "GIT_EDITOR",
        .value = &state.git_editor
    },
    {
        .key = "EDITOR_SIMULATOR_IN_FIFO_NAME",
        .value = &state.editor_simulator_in_fifo_name
    },
    {
        .key = "EDITOR_SIMULATOR_OUT_FIFO_NAME",
        .value = &state.editor_simulator_out_fifo_name
    }
};

#define N_POLLFDS 4
static struct init_pollfd_config_t pollfd_config[N_POLLFDS] = {
    {
        .name = "sigterm",
        .activated = true,
        .pollfd = &state.sigterm_pollfd,
        .pollfd_type = POLLFD_SIGTERM,
        .pollfd_event_type = POLLIN,
        .fd = &state.sigterm_pipe_read_fd
    },
    {
        .name = "sigchld",
        .activated = false,
        .pollfd = &state.sigchld_pollfd,
        .pollfd_type = POLLFD_SIGCHLD,
        .pollfd_event_type = POLLIN,
        .fd = &state.sigchld_pipe_read_fd
    },
    {
        .name = "editor_simulator",
        .activated = false,
        .pollfd = &state.editor_simulator_fifo_pollfd,
        .pollfd_type = POLLFD_EDITOR_SIMULATOR,
        .pollfd_event_type = POLLIN,
        .fd = &state.editor_simulator_in_fifo_fd
    },
    {
        .name = "server",
        .activated = false,
        .pollfd = &state.server_fifo_pollfd,
        .pollfd_type = POLLFD_SERVER,
        .pollfd_event_type = POLLIN,
        .fd = &state.server_in_fifo_fd
    }
};

#pragma endregion

# pragma region SIGNAL HANDLERS

void sigterm_handler(int signum)
{
    struct communication_packet_t *packet = NULL;
    size_t size = 0;
    if (!communication_alloc_signal(signum, &packet, &size))
    {
        PRINT_ERROR_F("An error (%d) occurred inside the signal handler for SIGTERM during communication_alloc_signal\n", errno);
    }
    if (!communication_write(state.sigterm_pipe_write_fd, packet, size))
    {
        PRINT_ERROR_F("An error (%d) occurred inside the signal handler for SIGTERM during communication_write\n", errno);
    }
    free(packet);
}

void sigchld_handler(int signum)
{
    int status = 0;
    pid_t child_pid = waitpid(state.git_pid, &status, 0);

    if (child_pid == POSIX_ERROR)
    {
        PRINT_ERRNO_MESSAGE("waitpid");
        PRINT_ERROR_F("An error (%d) occurred inside the signal handler for SIGCHLD during waitpid\n", errno);
    }

    struct communication_packet_t *packet = NULL;
    size_t size = 0;
    state.git_returncode = WEXITSTATUS(status);
    if (!communication_alloc_signal(signum, &packet, &size))
    {
        PRINT_ERROR_F("An error (%d) occurred inside the signal handler for SIGCHLD during communication_alloc_signal\n", errno);
    }
    if (!communication_write(state.sigchld_pipe_write_fd, packet, size))
    {
        PRINT_ERROR_F("An error (%d) occurred inside the signal handler for SIGCHLD during communication_write\n", errno);
    }
    free(packet);
}

#pragma endregion

bool launch_git()
{
    int stdin_pipe[2];
    int stdout_pipe[2];
    int stderr_pipe[2];

    if (pipe(stdin_pipe) == POSIX_ERROR)
    {
        PRINT_ERRNO_MESSAGE("pipe");
        return false;
    }
    if (pipe(stdout_pipe) == POSIX_ERROR)
    {
        PRINT_ERRNO_MESSAGE("pipe");
        return false;
    }
    if (pipe(stderr_pipe) == POSIX_ERROR)
    {
        PRINT_ERRNO_MESSAGE("pipe");
        return false;
    }

    pid_t pid = fork();

    if (pid == POSIX_ERROR)
    {
        PRINT_ERRNO_MESSAGE("fork");
        return false;
    }

    if (pid == 0)
    {
        // child process

        if (close(stdin_pipe[PIPE_WRITE_END]) == POSIX_ERROR)
        {
            PRINT_ERRNO_MESSAGE("close");
            exit(EXIT_FAILURE);
        }
        if (close(stdout_pipe[PIPE_READ_END]) == POSIX_ERROR)
        {
            PRINT_ERRNO_MESSAGE("close");
            exit(EXIT_FAILURE);
        }
        if (close(stderr_pipe[PIPE_READ_END]) == POSIX_ERROR)
        {
            PRINT_ERRNO_MESSAGE("close");
            exit(EXIT_FAILURE);
        }

        if (dup2(stdin_pipe[PIPE_READ_END], STDIN_FILENO) == POSIX_ERROR)
        {
            PRINT_ERRNO_MESSAGE("dup2");
            exit(EXIT_FAILURE);
        }
        if (dup2(stdout_pipe[PIPE_WRITE_END], STDOUT_FILENO) == POSIX_ERROR)
        {
            PRINT_ERRNO_MESSAGE("dup2");
            exit(EXIT_FAILURE);
        }
        if (dup2(stderr_pipe[PIPE_WRITE_END], STDERR_FILENO) == POSIX_ERROR)
        {
            PRINT_ERRNO_MESSAGE("dup2");
            exit(EXIT_FAILURE);
        }

        if (close(stdin_pipe[PIPE_READ_END]) == POSIX_ERROR)
        {
            PRINT_ERRNO_MESSAGE("close");
            exit(EXIT_FAILURE);
        }
        if (close(stdout_pipe[PIPE_WRITE_END]) == POSIX_ERROR)
        {
            PRINT_ERRNO_MESSAGE("close");
            exit(EXIT_FAILURE);
        }
        if (close(stderr_pipe[PIPE_WRITE_END]) == POSIX_ERROR)
        {
            PRINT_ERRNO_MESSAGE("close");
            exit(EXIT_FAILURE);
        }

        char *arguments[state.git_argc + 2];
        arguments[0] = state.git_executable;
        for (size_t i = 0; i < state.git_argc; ++i)
        {
            arguments[i + 1] = state.git_argv[i];
        }
        arguments[state.git_argc + 1] = NULL;

        if (execvp(state.git_executable, arguments) == POSIX_ERROR)
        {
            PRINT_ERRNO_MESSAGE("execvp");
            exit(EXIT_FAILURE);
        }
    }
    else
    {
        // parent process

        if (close(stdin_pipe[PIPE_READ_END]) == POSIX_ERROR)
        {
            PRINT_ERRNO_MESSAGE("close");
            exit(EXIT_FAILURE);
        }
        if (close(stdout_pipe[PIPE_WRITE_END]) == POSIX_ERROR)
        {
            PRINT_ERRNO_MESSAGE("close");
            exit(EXIT_FAILURE);
        }
        if (close(stderr_pipe[PIPE_WRITE_END]) == POSIX_ERROR)
        {
            PRINT_ERRNO_MESSAGE("close");
            exit(EXIT_FAILURE);
        }

        // parent process
        state.git_stdin_fd = stdin_pipe[PIPE_WRITE_END];
        state.git_stdout_fd = stdout_pipe[PIPE_READ_END];
        state.git_stderr_fd = stderr_pipe[PIPE_READ_END];
        state.git_pid = pid;
        state.git_state = RUNNING;

        // terminate interactive git sessions:
        const char termination_message[] = "q\n";
        if (write(state.git_stdin_fd, termination_message, strlen(termination_message)) == POSIX_ERROR)
        {
            PRINT_ERRNO_MESSAGE("write");
            return false;
        }

        turn_on_pollfd(&state.sigchld_pollfd);
        turn_on_pollfd(&state.editor_simulator_fifo_pollfd);

        return true;
    }

    return true;
}

bool read_git_output(char **git_stdout, char **git_stderr, size_t *stdout_size, size_t *stderr_size)
{
    if (!communication_read_raw(state.git_stdout_fd, git_stdout, stdout_size))
    {
        return false;
    }
    if (!communication_read_raw(state.git_stderr_fd, git_stderr, stderr_size))
    {
        return false;
    }
    
    PRINT_DEBUG_F("GIT STDOUT (%d):\n%s\n", *stdout_size, *git_stdout);
    PRINT_DEBUG_F("GIT STDERR (%d):\n%s\n", *stderr_size, *git_stderr);

    return true;
}

bool transfer_git_output()
{
    char *git_stdout = NULL;
    char *git_stderr = NULL;
    size_t stdout_size = 0;
    size_t stderr_size = 0;

    if (!read_git_output(&git_stdout, &git_stderr, &stdout_size, &stderr_size))
    {
        return false;
    }

    struct communication_packet_t *packet;
    size_t packet_size = 0;
    if (!communication_alloc_git_result(state.git_returncode, stdout_size, stderr_size, git_stdout, git_stderr, &packet, &packet_size))
    {
        free(git_stdout);
        free(git_stderr);
        free(packet);
        return false;
    }
    if (!communication_write(state.server_out_fifo_fd, packet, packet_size))
    {
        free(git_stdout);
        free(git_stderr);
        return false;
    }
    
    free(git_stdout);
    free(git_stderr);
    free(packet);
    return true;
}

bool handle_sigterm(struct communication_packet_t *packet)
{
    // deactivate polling on all file descriptors
    turn_off_pollfd(&state.sigterm_pollfd);
    turn_off_pollfd(&state.sigchld_pollfd);
    turn_off_pollfd(&state.editor_simulator_fifo_pollfd);
    turn_off_pollfd(&state.server_fifo_pollfd);

    if (packet->type != COMMUNICATION_SIGNAL)
    {
        PRINT_ERROR_F("Unexpected packet type: %d\n", packet->type);
        return false;
    }

    int signal = packet->packet_content.signal.signal;
    if (signal != SIGTERM)
    {
        PRINT_ERROR_F("Unexpected signal: %d\n", signal);
        return false;
    }
    
    // kill git if it is running
    if (state.git_state != NOT_RUNNING)
    {
        if (kill(state.git_pid, SIGKILL) == POSIX_ERROR)
        {
            PRINT_ERRNO_MESSAGE("kill");
            return false;
        }
    }

    // wait for git to terminate and store its returncode
    int status = 0;
    if (waitpid(state.git_pid, &status, 0) == POSIX_ERROR)
    {
        PRINT_ERRNO_MESSAGE("waitpid");
        return false;
    }
    state.git_returncode = 1;
    
    // read git output 
    if (!transfer_git_output())
    {
        return false;
    }

    state.git_state = NOT_RUNNING;

    return true;
}

bool handle_sigchld(struct communication_packet_t *packet)
{
    turn_off_pollfd(&state.sigchld_pollfd);
    turn_off_pollfd(&state.editor_simulator_fifo_pollfd);
    turn_off_pollfd(&state.server_fifo_pollfd);

    if (packet->type != COMMUNICATION_SIGNAL)
    {
        PRINT_ERROR_F("Unexpected packet type: %d\n", packet->type);
        return false;
    }

    int signal = packet->packet_content.signal.signal;
    if (signal != SIGCHLD)
    {
        PRINT_ERROR_F("Unexpected signal: %d\n", signal);
        return false;
    }

    if (!transfer_git_output())
    {
        return false;
    }

    state.git_state = NOT_RUNNING;

    return true;
}   

bool handle_editor_simulator_request(struct communication_packet_t *packet_1)
{
    turn_off_pollfd(&state.editor_simulator_fifo_pollfd);

    if (state.git_state != RUNNING)
    {
        PRINT_ERROR_F("Unexpected git state: %d\n", state.git_state);
        return false;
    }

    if (packet_1->type != COMMUNICATION_EDITOR_REQUEST_1)
    {
        PRINT_ERROR_F("Unexpected packet type: %d\n", packet_1->type);
        return false;
    }

    memcpy(state.git_editor_filename, packet_1->payload, packet_1->packet_content.editor_request_1.filename_size);
    state.git_editor_filename[packet_1->packet_content.editor_request_1.filename_size] = '\0';

    char *git_stdout = NULL;
    char *git_stderr = NULL;
    size_t stdout_size = 0;
    size_t stderr_size = 0;

    if (!read_git_output(&git_stdout, &git_stderr, &stdout_size, &stderr_size))
    {
        return false;
    }

    struct communication_packet_t *packet_2;
    size_t packet_2_size = 0;
    if (!communication_alloc_editor_request_2(
        packet_1->packet_content.editor_request_1.filename_size,
        packet_1->packet_content.editor_request_1.content_size,
        stdout_size,
        stderr_size,
        (char*)&packet_1->payload[packet_1->packet_content.editor_request_1.filename_offset],
        (char*)&packet_1->payload[packet_1->packet_content.editor_request_1.content_offset],
        git_stdout,
        git_stderr,
        &packet_2,
        &packet_2_size
    ))
    {
        free(git_stdout);
        free(git_stderr);
        return false;
    }

    if (!communication_write(state.server_out_fifo_fd, packet_2, packet_2_size))
    {
        free(git_stdout);
        free(git_stderr);
        free(packet_2);
        return false;
    }

    state.git_state = WAIT_FOR_EDITOR_CONTENT;

    turn_on_pollfd(&state.server_fifo_pollfd);

    return true;
}

bool handle_server_data(struct communication_packet_t *packet, size_t size)
{
    switch (state.git_state)
    {
        default:
        case RUNNING:
        case NOT_RUNNING:
            PRINT_ERROR_F("Unexpected git state: %d\n", state.git_state);
            return false;
            break;

        case WAIT_FOR_EDITOR_CONTENT:
            turn_off_pollfd(&state.server_fifo_pollfd);

            if (packet->type != COMMUNICATION_EDITOR_RESPONSE)
            {
                PRINT_ERROR_F("Unexpected packet type: %d\n", packet->type);
                return false;
            }
            if (!communication_write(state.editor_simulator_out_fifo_fd, packet, size))
            {
                return false;
            }
            break;
    }

    state.git_state = RUNNING;

    return true;
}

bool mainloop(bool *done)
{    
    struct pollfd fds[N_POLLFDS] = {
        *pollfd_config[0].pollfd,
        *pollfd_config[1].pollfd,
        *pollfd_config[2].pollfd,
        *pollfd_config[3].pollfd
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

        struct communication_packet_t *packet = NULL;
        size_t packet_size = 0;

        if (!communication_read(fds[i].fd, &packet, &packet_size))
        {
            return false;
        }

        bool success = false;

        switch (pollfd_config[i].pollfd_type)
        {
            case POLLFD_SIGTERM:
                success = handle_sigterm(packet);
                *done = success;
                break;

            case POLLFD_SIGCHLD:
                success = handle_sigchld(packet);
                *done = success;
                break;

            case POLLFD_EDITOR_SIMULATOR:
                success = handle_editor_simulator_request(packet);
                break;

            case POLLFD_SERVER:
                success = handle_server_data(packet, packet_size);
                break;
        }

        free(packet);

        if (!success)
        {
            return false;
        }
        if (*done)
        {
            return true;
        }
    } 

    return true;
}

bool initialize(int argc, char *argv[])
{
    if (
        !init_read_arguments(argc, argv, argument_config, N_ARGUMENTS)
        || !init_fifos(fifo_config, N_FIFOS)
        || !init_pipes(pipe_config, N_PIPES)
        || !init_signals(signal_config, N_SIGNALS)
        || !init_set_environment(environment_config, N_VARIABLES)
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
    cleanup_signals(signal_config, N_SIGNALS);
    cleanup_pipes(pipe_config, N_PIPES);
    cleanup_fifos(fifo_config, N_FIFOS);
}

int main(int argc, char *argv[])
{
    if (!initialize(argc, argv))
    {
        goto ERROR;
    }

    if (!launch_git())
    {
        goto ERROR;
    }

    bool done = false;
    while (!done)
    {
        if (!mainloop(&done))
        {
            goto ERROR;
        }
    }

    cleanup();
    return EXIT_SUCCESS;

ERROR:
    cleanup();
    return EXIT_FAILURE;
}
