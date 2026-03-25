#include "init.h"

#include <sys/types.h>
#include <sys/stat.h>
#include <string.h>
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>

#include "debug.h"
#include "util.h"

bool init_read_arguments(int argc, char *argv[], struct init_argument_config_t *config, size_t size)
{
    if (argc < (int)size)
    {
        PRINT_ERROR_F("Invalid number of arguments: %d, must be at least %d\n", argc, size);
        return false;
    }

    for (size_t i = 0; i < size; ++i)
    {
        const struct init_argument_config_t *cfg = config + i;
        
        switch (cfg->argument_type)
        {
            case STRING:
                *cfg->string = argv[cfg->offset];
                break;
            
            case STRING_LIST:
                *cfg->string_list = argv + cfg->offset;
                break;

            case NUMBER:
                size_t result = 0;
                if (!parse_uint64(argv[cfg->offset], &result))
                {
                    return false;
                }
                *cfg->number = result;
                break;

            default:
                PRINT_ERROR_F("Unexpected argument type: %d\n", cfg->argument_type);
                return false;
                break;
        }
    }

    return true;
}

bool init_signals(struct init_signal_config_t *config, size_t size)
{
    for (size_t i = 0; i < size; ++i)
    {
        const struct init_signal_config_t *cfg = config + i;

        struct sigaction sa = {
            .sa_handler = cfg->handler,
            .sa_flags = 0,
        };

        if (sigemptyset(&sa.sa_mask) == -1)
        {
            PRINT_ERRNO_MESSAGE("sigemptyset");
            return false;
        }

        if (sigaction(cfg->signal, &sa, NULL) == -1)
        {
            PRINT_ERRNO_MESSAGE("sigaction");
            return false;
        }
    }   

    return true;
}

bool init_fifos(struct init_fifo_config_t *config, size_t size)
{
    for (size_t i = 0; i < size; ++i)
    {
        struct init_fifo_config_t *cfg = config + i;

        if (cfg->generate_name)
        {
            char uuid[UUID_SIZE];
            if (!generate_uuid(uuid))
            {
                return false;
            }

            const char *prefix = "/tmp/fifo_";
            *cfg->name = (char *)malloc(strlen(prefix) + UUID_SIZE + 1);
            sprintf(*cfg->name, "%s%s", prefix, uuid);
        }

        if (!cfg->created_flag)
        {
            if (mkfifo(*cfg->name, cfg->permissions) == -1)
            {
                PRINT_ERRNO_MESSAGE("mkfifo");
                return false;
            }
            cfg->created_flag = true;
        }
    }

    for (size_t i = 0; i < size; ++i)
    {
        const struct init_fifo_config_t *cfg = config + i;
        if ((*cfg->fd = open(*cfg->name, cfg->mode)) == -1)
        {
            PRINT_ERRNO_MESSAGE("open");
            return false;
        }
    }

    return true;
}

bool init_pipes(struct init_pipe_config_t *config, size_t size)
{
    for (size_t i = 0; i < size; ++i)
    {
        const struct init_pipe_config_t *cfg = config + i;
        int fds[2] = { 0 };
        if (pipe(fds) == -1)
        {
            PRINT_ERRNO_MESSAGE("pipe");
            return false;
        }

        int flags = fcntl(fds[0], F_GETFL, 0);
        if (flags == POSIX_ERROR)
        {
            PRINT_ERRNO_MESSAGE("fcntl");
            return false;
        }

        if (fcntl(fds[0], F_SETFL, flags | O_NONBLOCK) == POSIX_ERROR)
        {
            PRINT_ERRNO_MESSAGE("fcntl");
            return false;   
        }

        if (cfg->read_fd)
        {
            *cfg->read_fd = fds[0];
        }
        else 
        {
            if (close(fds[0]) == -1)
            {
                PRINT_ERRNO_MESSAGE("close");
                return false;
            }
        }

        if (cfg->write_fd)
        {
            *cfg->write_fd = fds[1];
        }
        else
        {
            if (close(fds[1]) == -1)
            {
                PRINT_ERRNO_MESSAGE("close");
                return false;
            }
        }
    }

    return true;
}

bool init_set_environment(struct init_environment_config_t *config, size_t size)
{
    for (size_t i = 0; i < size; ++i)
    {
        struct init_environment_config_t *cfg = config + i;
        if (setenv(cfg->key, *cfg->value, true) == -1)
        {
            PRINT_ERRNO_MESSAGE("setenv");
            return false;
        }
    }

    return true;
}

bool init_get_environment(struct init_environment_config_t *config, size_t size)
{
    for (size_t i = 0; i < size; ++i)
    {
        struct init_environment_config_t *cfg = config + i;
        if (!(*cfg->value = getenv(cfg->key)))
        {
            PRINT_ERROR_F("Key not found: %s\n", cfg->key);
            return false;
        }
    }

    return true;
}

bool init_pollfds(struct init_pollfd_config_t *config, size_t size)
{
    for (size_t i = 0; i < size; ++i)
    {
        struct init_pollfd_config_t *cfg = config + i;
        cfg->pollfd->fd = *cfg->fd;
        if (cfg->activated)
        {
            turn_on_pollfd(cfg->pollfd);
        } else 
        {
            turn_off_pollfd(cfg->pollfd);
        }
        cfg->pollfd->events = cfg->pollfd_event_type;
        cfg->pollfd->revents = 0;
    }

    return true;
}

void toggle_pollfd(struct pollfd *pollfd)
{
    pollfd->fd = ~pollfd->fd;
}

void turn_on_pollfd(struct pollfd *pollfd)
{
    if (pollfd->fd < 0)
    {
        toggle_pollfd(pollfd);
    }
}

void turn_off_pollfd(struct pollfd *pollfd)
{
    if (pollfd->fd >= 0)
    {
        toggle_pollfd(pollfd);
    }
}

void cleanup_signals(struct init_signal_config_t *config, size_t size)
{ 
    for (size_t i = 0; i < size; ++i)
    {
        const struct init_signal_config_t *cfg = config + i;
        if (signal(cfg->signal, SIG_DFL) == SIG_ERR)
        {
            PRINT_ERRNO_MESSAGE("signal");
        }
    }
}

void cleanup_fifos(struct init_fifo_config_t *config, size_t size)
{ 
    for (size_t i = 0; i < size; ++i)
    {
        const struct init_fifo_config_t *cfg = config + i;

        if (!cfg->created_flag)
        {
            continue;
        }

        if (close(*cfg->fd) == -1)
        {
            PRINT_ERRNO_MESSAGE("close");
        }
    }

    for (size_t i = 0; i < size; ++i)
    {
        const struct init_fifo_config_t *cfg = config + i;

        if (!cfg->created_flag)
        {
            continue;
        }

        // if (unlink(*cfg->name) == -1)
        // {
        //     PRINT_ERRNO_MESSAGE("unlink");
        // }

        if (cfg->generate_name)
        {
            free(*cfg->name);
        }
    }
}

void cleanup_pipes(struct init_pipe_config_t *config, size_t size)
{ 
    for (size_t i = 0; i < size; ++i)
    {
        const struct init_pipe_config_t *cfg = config + i;

        if (cfg->write_fd)
        {
            if (close(*cfg->write_fd) == -1)
            {
                PRINT_ERRNO_MESSAGE("close");
            }
        }

        if (cfg->read_fd)
        {
            if (close(*cfg->read_fd) == -1)
            {
                PRINT_ERRNO_MESSAGE("close");
            }
        }
    }
}

void cleanup_pollfds(struct init_pollfd_config_t *config, size_t size)
{
    for (size_t i = 0; i < size; ++i)
    {
        struct init_pollfd_config_t *cfg = config + i;
        cfg->pollfd->fd = -1;
        cfg->pollfd->events = 0;
        cfg->pollfd->revents = 0;
    }
}