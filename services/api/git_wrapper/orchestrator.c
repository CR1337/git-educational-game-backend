#include <stdlib.h>
#include <stdio.h>
#include <signal.h>
#include <unistd.h>
#include <string.h>
#include <sys/wait.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <stdbool.h>
#include <poll.h>
#include <limits.h>
#include <stdint.h>
#include <string.h>

#include "debug.h"
#include "communication.h"

#pragma region STATE 

enum git_state_t { 
    NOT_RUNNING = 0, 
    RUNNING, 
    WAIT_FOR_EDITOR_CONTENT, 
    WAIT_FOR_STDIN 
};
struct state_t {
    // ids
    char *game_id;
    char *git_session_id;

    // ipc
    char *server_in_fifo_name;
    bool server_in_fifo_created;
    int server_in_fifo_fd;

    char *server_out_fifo_name;
    bool server_out_fifo_created;
    int server_out_fifo_fd;

    char *editor_simulator_in_fifo_name;
    bool editor_simulator_in_fifo_created;
    int editor_simulator_in_fifo_fd;

    char *editor_simulator_out_fifo_name;
    bool editor_simulator_out_fifo_created;
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
    struct pollfd git_stdin_pollfd;
    struct pollfd editor_simulator_fifo_pollfd;
    struct pollfd server_fifo_pollfd;

    // git
    size_t git_argc;
    char **git_argv;
    char *git_editor;
    pid_t git_pid;
    enum git_state_t git_state;

};
static struct state_t state = { 0 };

#pragma endregion

# pragma region CONFIGURATION

enum argument_type_t { STRING, NUMBER, STRING_LIST };
struct argument_config_t {
    const char *name;
    const enum argument_type_t argument_type;
    int offset;
    union {
        char **string;
        size_t *number;
        char ***string_list;
    };
};
const static size_t N_ARGUMENTS = 7;
const static struct argument_config_t argument_configs[N_ARGUMENTS] = {
    {
        .name = "game_id",
        .argument_type = STRING,
        .offset = 1,
        .string = &state.game_id
    },
    {
        .name = "git_session_id",
        .argument_type = STRING,
        .offset = 2,
        .string = &state.git_session_id
    },
    {
        .name = "server_in_fifo_name",
        .argument_type = STRING,
        .offset = 3,
        .string = &state.server_in_fifo_name
    },
    {
        .name = "server_out_fifo_name",
        .argument_type = STRING,
        .offset = 4,
        .string = &state.server_out_fifo_name
    },
    {
        .name = "git_editor",
        .argument_type = STRING,
        .offset = 5,
        .number = &state.git_editor
    },
    {
        .name = "git_argc",
        .argument_type = NUMBER,
        .offset = 6,
        .number = &state.git_argc
    },
    {
        .name = "git_argv",
        .argument_type = STRING_LIST,  // There can only be one argument of type string list and it mus be the last one.
        .offset = 7,
        .string_list = &state.git_argv
    }
};

struct signal_config_t {
    const int signal;
    const __sighandler_t handler;
};
const static size_t N_SIGNALS = 2;
const static struct signal_config_t signal_configs[N_SIGNALS] = {
    {
        .signal = SIGTERM,
        .handler = sigterm_handler
    },
    {
        .signal = SIGCHLD,
        .handler = sigchld_handler
    }
};

struct fifo_config_t {
        const char *const *name;
        const int mode;
        const int permissions;
        bool *const created_flag;
        int *const fd;
        struct pollfd *pollfd; 
        short pollfd_event_type;
    };
const static size_t N_FIFOS = 4;
const static struct fifo_config_t fifo_configs[N_FIFOS] = {
    { 
        .name = &state.server_in_fifo_name,
        .mode = O_RDONLY,
        .permissions = 0600,
        .created_flag = &state.server_in_fifo_created,
        .fd = &state.server_in_fifo_fd,
        .pollfd = &state.server_fifo_pollfd,
        .pollfd_event_type = POLLIN
    },
    { 
        .name = &state.server_out_fifo_name,
        .mode = O_WRONLY,
        .permissions = 0600,
        .created_flag = &state.server_out_fifo_created,
        .fd = &state.server_out_fifo_fd,
        .pollfd = NULL,
        .pollfd_event_type = 0
    },
    { 
        .name = &state.editor_simulator_in_fifo_name,
        .mode = O_RDONLY,
        .permissions = 0600,
        .created_flag = &state.editor_simulator_in_fifo_created,
        .fd = &state.editor_simulator_in_fifo_fd,
        .pollfd = &state.editor_simulator_fifo_pollfd,
        .pollfd_event_type = POLLIN
    },
    { 
        .name = &state.editor_simulator_out_fifo_name,
        .mode = O_WRONLY,
        .permissions = 0600,
        .created_flag = &state.editor_simulator_out_fifo_created,
        .fd = &state.editor_simulator_out_fifo_fd,
        .pollfd = NULL,
        .pollfd_event_type = 0
    }
};

struct pipe_config_t {
    int *const read_fd;
    int *const write_fd;
    struct pollfd *pollfd;
    short pollfd_event_type;
};
const static size_t N_PIPES = 5;
const static struct pipe_config_t pipe_configs[N_PIPES] = {
    {
        .read_fd = &state.sigterm_pipe_read_fd,
        .write_fd = &state.sigterm_pipe_write_fd,
        .pollfd = &state.sigterm_pollfd,
        .pollfd_event_type = POLLIN
    },
    {
        .read_fd = &state.sigchld_pipe_read_fd,
        .write_fd = &state.sigchld_pipe_write_fd,
        .pollfd = &state.sigchld_pollfd,
        .pollfd_event_type = POLLIN
    },
    {
        .read_fd = NULL,
        .write_fd = &state.git_stdin_fd,
        .pollfd = &state.git_stdin_pollfd,
        .pollfd_event_type = POLLOUT
    },
    {
        .read_fd = &state.git_stdout_fd,
        .write_fd = NULL,
        .pollfd = NULL,
        .pollfd_event_type = 0
    },
    {
        .read_fd = &state.git_stderr_fd,
        .write_fd = NULL,
        .pollfd = NULL,
        .pollfd_event_type = 0
    }
};

struct environment_config_t {
    const char *const key;
    const char *const *value;
};
const static size_t N_VARIABLES = 3;
const static struct environment_config_t environment_configs[N_VARIABLES] = {
    {
        .key = "GIT_EDITOR",
        .value = &state.git_editor
    },
    {
        .key = "GAME_ID",
        .value = &state.game_id
    },
    {
        .key = "GIT_SESSION_ID",
        .value = &state.git_session_id
    }
};

enum pollfd_type_t { 
    POLLFD_SIGTERM, 
    POLLFD_SIGCHLD, 
    POLLFD_GIT_STDIN, 
    POLLFD_EDITOR_SIMULATOR, 
    POLLFD_SERVER 
};
struct pollfd_config_t {
    char *name;
    struct pollfd *pollfd;
    enum pollfd_type_t pollfd_type;
    short pollfd_event_type;
};
const static size_t N_POLLFDS = 5;
const static struct pollfd_config_t pollfds[N_POLLFDS] = {
    {
        .name = "sigterm",
        .pollfd = &state.sigterm_pollfd,
        .pollfd_type = POLLFD_SIGTERM,
        .pollfd_event_type = POLLIN
    },
    {
        .name = "sigchld",
        .pollfd = &state.sigchld_pollfd,
        .pollfd_type = POLLFD_SIGCHLD,
        .pollfd_event_type = POLLIN
    },
    {
        .name = "git_stdin",
        .pollfd = &state.git_stdin_pollfd,
        .pollfd_type = POLLFD_GIT_STDIN,
        .pollfd_event_type = POLLOUT
    },
    {
        .name = "editor_simulator",
        .pollfd = &state.editor_simulator_fifo_pollfd,
        .pollfd_type = POLLFD_EDITOR_SIMULATOR,
        .pollfd_event_type = POLLIN
    },
    {
        .name = "server",
        .pollfd = &state.server_fifo_pollfd,
        .pollfd_type = POLLFD_SERVER,
        .pollfd_event_type = POLLIN
    }
};

#pragma endregion

# pragma region SIGNAL HANDLERS

void sigterm_handler(int signum)
{
    char *buffer[BUFFER_SIZE];
    size_t size = 0;
    communication_pack_signal(signum, buffer, &size);
    if (!communication_write(state.sigterm_pipe_write_fd, buffer, size))
    {
        // TODO ?
    }
}

void sigchld_handler(int signum)
{
    int status = 0;
    pid_t child_pid = 0;

    while ((child_pid = waitpid(-1, &status, WNOHANG)) > 0) 
    {
        if (child_pid == -1)
        {
            PRINT_ERROR("waitpid");
            // TODO ?
        }
        if (child_pid == state.git_pid)
        {
            char *buffer[BUFFER_SIZE];
            size_t size = 0;
            communication_pack_signal(signum, buffer, &size);
            if (!communication_write(state.sigchld_pipe_write_fd, buffer, size))
            {
                // TODO ?
            }
        }
    }
}

#pragma endregion

# pragma region SETUP

bool read_arguments(int argc, char *argv[])
{
    const int MIN_ARGC = 3;
    const int BASE_10 = 10;

    if (argc < MIN_ARGC)
    {
        fprintf(stderr, "Invalid number of arguments: %d\n", argc);
        return false;
    }

    for (size_t i = 0; i < N_ARGUMENTS; ++i)
    {
        const struct argument_config_t *config = argument_configs + i;
        
        switch (config->argument_type)
        {
            case STRING:
                *config->string = argv[config->offset];
                break;
            
                case STRING_LIST:
                    *config->string_list = argv + config->offset;
                    break;

            case NUMBER:
                char *endptr = NULL;
                size_t result = strtoull(argv[config->offset], &endptr, BASE_10);
                if ((result || *endptr != argv[config->offset]) && !*endptr)
                {
                    break;
                }
                
            default:
                fprintf(stderr, "Error parsing value \"%s\" into %s\n", argv[config->offset], config->name);
                return false;
                break;
        }
    }

    return true;
}

bool register_signals()
{
    for (size_t i = 0; i < N_SIGNALS; ++i)
    {
        const struct signal_config_t *config = signal_configs + i;
        if (signal(config->signal, config->handler) == SIG_ERR)
        {
            PRINT_ERROR("signal");
            return false;
        }
    }   

    return true;
}


bool create_fifos()
{
    for (size_t i = 0; i < N_FIFOS; ++i)
    {
        const struct fifo_config_t *config = fifo_configs + i;
        if (mkfifo(*config->name, config->permissions) == -1)
        {
            PRINT_ERROR("mkfifo");
            return false;
        }
        *config->created_flag = true;
    }

    for (size_t i = 0; i < N_FIFOS; ++i)
    {
        const struct fifo_config_t *config = fifo_configs + i;
        if (*config->fd = open(*config->name, config->mode) == -1)
        {
            PRINT_ERROR("open");
            return false;
        }

        if (config->pollfd){
            config->pollfd->fd = *config->fd;
            config->pollfd->events = config->pollfd_event_type;
            config->pollfd->revents = 0;
        }
    }
}

bool create_pipes()
{
    for (size_t i = 0; i < N_PIPES; ++i)
    {
        const struct pipe_config_t *config = pipe_configs + i;
        int fds[2] = { 0 };
        if (pipe(fds) == -1)
        {
            PRINT_ERROR("pipe");
            return false;
        }

        if (config->read_fd)
        {
            *config->read_fd = fds[0];
        }
        else 
        {
            if (close(fds[0]) == -1)
            {
                PRINT_ERROR("close");
                return false;
            }
        }

        if (config->write_fd)
        {
            *config->write_fd = fds[1];
        }
        else
        {
            if (close(fds[1]) == -1)
            {
                PRINT_ERROR("close");
                return false;
            }
        }

        if (config->pollfd)
        {
            config->pollfd->fd = *config->read_fd;
            config->pollfd->events = config->pollfd_event_type;
            config->pollfd->revents = 0;
        }
    }

    return true;
}

bool create_ipc()
{
    if (!create_fifos())
    {
        return false;
    }    

    if (!create_pipes())
    {
        return false;
    }

    return true;
}

bool set_environment()
{
    for (size_t i = 0; i < N_VARIABLES; ++i)
    {
        struct environment_config_t *config = environment_configs + i;
        if (setenv(config->key, *config->value, true) == -1)
        {
            PRINT_ERROR("setenv");
            return false;
        }
    }

    return true;
}

bool launch_git()
{
    pid_t pid = fork();

    if (pid == -1)
    {
        PRINT_ERROR("fork");
        return false;
    }
    else if (pid == 0)
    {
        // child process
        char *arguments[state.git_argc + 2];
        arguments[0] = "git";
        for (size_t i = 0; i < state.git_argc; ++i)
        {
            strncpy(arguments[i + 1], state.git_argv[i], strlen(state.git_argv[i]));
        }
        arguments[state.git_argc + 2] = NULL;

        if (dup2(state.git_stdin_fd, STDIN_FILENO) == -1)
        {
            PRINT_ERROR("dup2");
            return false;
        }
        if (close(state.git_stdin_fd) == -1)
        {
            PRINT_ERROR("close");
            return false;
        }

        if (dup2(state.git_stdout_fd, STDOUT_FILENO) == -1)
        {
            PRINT_ERROR("dup2");
            return false;
        }
        if (close(state.git_stdout_fd) == -1)
        {
            PRINT_ERROR("close");
            return false;
        }

        if (dup2(state.git_stderr_fd, STDERR_FILENO) == -1)
        {
            PRINT_ERROR("dup2");
            return false;
        }
        if (close(state.git_stderr_fd) == -1)
        {
            PRINT_ERROR("close");
            return false;
        }

        execvp("git", arguments);

        PRINT_ERROR("execvp");
        return false;
    }
    else
    {
        // parent process
        state.git_pid = pid;
        state.git_state = RUNNING;
        return true;
    }
}

#pragma endregion

#pragma region MAINLOOP

bool read_git_stdout_stderr(char *git_stdout, char *git_stderr, size_t *git_stdout_size, size_t *git_stderr_size, int *status)
{
    if (waitpid(state.git_pid, status, 0) == -1)
    {
        PRINT_ERROR("waitpid");
        return false;
    }

    if (*git_stdout_size = read(state.git_stdout_fd, git_stdout, BUFFER_SIZE - 1) == -1)
    {
        PRINT_ERROR("read");
        return false;
    }
    git_stdout[*git_stdout_size] = '\0';

    if (*git_stderr_size = read(state.git_stderr_fd, git_stderr, BUFFER_SIZE - 1) == -1)
    {
        PRINT_ERROR("read");
        return false;
    }
    git_stderr[*git_stderr_size] = '\0';
}

bool transfer_git_output()
{
    char git_stdout[BUFFER_SIZE];
    char git_stderr[BUFFER_SIZE];
    size_t git_stdout_size = 0;
    size_t git_stderr_size = 0;
    int status = 0;

    if (!read_git_stdout_stderr(git_stdout, git_stderr, &git_stdout_size, &git_stderr_size, &status) == -1)
    {
        return false;
    }

    int git_return_code = (WIFEXITED(status))
        ? WEXITSTATUS(status)
        : 1;

    char buffer[BUFFER_SIZE];
    size_t size = 0;
    communication_pack_git_result(git_return_code, git_stdout_size, git_stderr_size, git_stdout, git_stderr, buffer, &size);
    if (!communication_write(state.server_out_fifo_fd, buffer, size))
    {
        return false;
    }
    
    return true;
}

bool handle_sigterm(struct communication_packet_t *packet, size_t size)
{
    if (packet->type != COMMUNICATION_SIGNAL)
    {
        // TODO: error
        return false;
    }

    int signal = packet->packet_content.signal.signal;
    if (signal != SIGTERM)
    {
        fprintf(stderr, "Received %d instead of %d (SIGTERM)\n", signal, SIGTERM);
        return false;
    }

    if (state.git_state != NOT_RUNNING)
    {
        if (kill(state.git_pid, SIGKILL) == -1)
        {
            PRINT_ERROR("kill");
            return false;
        }
    }

    if (!transfer_git_output())
    {
        return false;
    }

    state.git_state = NOT_RUNNING;

    return true;
}

bool handle_sigchld(struct communication_packet_t *packet, size_t size)
{
    if (packet->type != COMMUNICATION_SIGNAL)
    {
        // TODO: error
        return false;
    }

    int signal = packet->packet_content.signal.signal;
    if (signal != SIGCHLD)
    {
        fprintf(stderr, "Received %d instead of %d (SIGCHLD)\n", signal, SIGCHLD);
        return false;
    }

    if (!transfer_git_output())
    {
        return false;
    }

    state.git_state = NOT_RUNNING;

    return true;
}   

bool handle_git_stdin()
{
    char git_stdout[BUFFER_SIZE];
    char git_stderr[BUFFER_SIZE];
    size_t git_stdout_size = 0;
    size_t git_stderr_size = 0;
    int status = 0;

    if (!read_git_stdout_stderr(git_stdout, git_stderr, &git_stdout_size, &git_stderr_size, &status) == -1)
    {
        return false;
    }

    char buffer[BUFFER_SIZE];
    size_t size = 0;
    communication_pack_stdin_request(git_stdout_size, git_stderr_size, git_stdout, git_stderr, buffer, &size);
    if (!communication_write(state.server_out_fifo_fd, buffer, size))
    {
        return false;
    }

    state.git_state = WAIT_FOR_STDIN;

    return true;
}

bool handle_editor_simulator_data(struct communication_packet_t *packet, size_t size)
{
    if (state.git_state != RUNNING)
    {
        // TODO: error
        return false;
    }

    if (packet->type != COMMUNICATION_EDITOR_REQUEST)
    {
        // TODO: error
        return false;
    }

    if (!communication_write(state.server_out_fifo_fd, packet, size))
    {
        return false;
    }

    state.git_state = WAIT_FOR_EDITOR_CONTENT;

    return true;
}

bool handle_server_data(struct communication_packet_t *packet, size_t size)
{
    switch (state.git_state)
    {
        default:
        case RUNNING:
        case NOT_RUNNING:
            // TODO: error
            return false;
            break;

        case WAIT_FOR_STDIN:
            if (packet->type != COMMUNICATION_STDIN_RESPONSE)
            {
                // TODO: error
                return false;
            }
            if (write(state.git_stdin_fd, packet->packet_content.stdin_response.stdin_, packet->packet_content.stdin_response.stdin_size) == -1)
            {
                PRINT_ERROR("write");
                return false;
            }
            break;

        case WAIT_FOR_EDITOR_CONTENT:
            if (packet->type != COMMUNICATION_EDITOR_RESPONSE)
            {
                // TODO: error
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
    /*
    Things to wait on:
    - SIGTERM (this program received a termination request)
    - SIGCHLD (git has terminated)
    - stdin of git (git requires input via stdin)
    - editor_simulator_fifo (git opened the editor simulator)
    - server_fifo (stdin or editor content from server)
    */
     
    const struct pollfd fds[N_POLLFDS] = {
        pollfds[0].pollfd,
        pollfds[1].pollfd,
        pollfds[2].pollfd,
        pollfds[3].pollfd,
        pollfds[4].pollfd
    };
    int poll_result = poll(fds, N_POLLFDS, -1);

    if (poll_result == -1)
    {
        PRINT_ERROR("poll");
        return false;
    }

    for (size_t i = 0; i < N_POLLFDS; ++i)
    {
        if (!pollfds[i].pollfd->revents)
        {
            continue;
        }

        if (pollfds[i].pollfd->revents & (POLLHUP | POLLERR | POLLNVAL))
        {
            fprintf(stderr, "An error (%d) occured during polling %s\n", pollfds[i].pollfd->revents, pollfds[i].name);
            return false;
        }

        if (pollfds[i].pollfd->revents != pollfds[i].pollfd_event_type)
        {
            // TODO: error
        }

        struct communication_packet_t packet;
        size_t packet_size = 0;
        bool success = false;

        if (!communication_read(pollfds[i].pollfd->fd, &packet, &packet_size))
        {
            return false;
        }

        switch (pollfds[i].pollfd_type)
        {
            case POLLFD_SIGTERM:
                success = handle_sigterm(&packet, packet_size);
                *done = success;
                break;

            case POLLFD_SIGCHLD:
                success = handle_sigchld(&packet, packet_size);
                *done = success;
                break;

            case POLLFD_GIT_STDIN:
                success = handle_git_stdin();
                break;

            case POLLFD_EDITOR_SIMULATOR:
                success = handle_editor_simulator_data(&packet, packet_size);
                break;

            case POLLFD_SERVER:
                success = handle_server_data(&packet, packet_size);
                break;
        }

        if (!success)
        {
            return false;
        }
    } 

    return true;
}

#pragma endregion

#pragma region CLEANUP

void cleanup_fifos() 
{
    for (size_t i = 0; i < N_FIFOS; ++i)
    {
        const struct fifo_config_t *config = fifo_configs + i;

        if (close(*config->fd) == -1)
        {
            PRINT_ERROR("close");
        }
    }

    for (size_t i = 0; i < N_FIFOS; ++i)
    {
        const struct fifo_config_t *config = fifo_configs + i;

        if (unlink(*config->name) == -1)
        {
            PRINT_ERROR("unlink");
        }

        config->pollfd->fd = -1;
        config->pollfd->events = 0;
        config->pollfd->revents = 0;
    }
}

void cleanup_pipes()
{
    for (size_t i = 0; i < N_PIPES; ++i)
    {
        const struct pipe_config_t *config = pipe_configs + i;

        if (config->write_fd)
        {
            if (close(*config->write_fd) == -1)
            {
                PRINT_ERROR("close");
            }
        }

        if (config->read_fd)
        {
            if (close(*config->read_fd) == -1)
            {
                PRINT_ERROR("close");
            }
        }

        if (config->pollfd)
        {
            config->pollfd->fd = -1;
            config->pollfd->events = 0;
            config->pollfd->revents = 0;
        }
    }
}

void cleanup_ipc()
{
    cleanup_pipes();
    cleanup_fifos();
}

void cleanup_signals()
{
    for (size_t i = 0; i < N_SIGNALS; ++i)
    {
        const struct signal_config_t *config = signal_configs + i;
        if (signal(config->signal, SIG_DFL) == SIG_ERR)
        {
            PRINT_ERROR("signal");
        }
    }
}

void cleanup()
{
    cleanup_signals();
    cleanup_ipc();
}

#pragma endregion

int main(int argc, char *argv[])
{
    if (
        !read_arguments(argc, argv)
        || !create_ipc()
        || !register_signals()
        || !set_environment()
        || !launch_git()
    )
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
