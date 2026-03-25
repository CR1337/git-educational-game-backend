#ifndef __INIT_H__
#define __INIT_H__

#include <stdlib.h>
#include <stdbool.h>
#ifndef __USE_POSIX
#define __USE_POSIX
#define __USE_POSIX_DEFINED
#endif
#include <signal.h>
#ifdef __USE_POSIX_DEFINED
#undef __USE_POSIX
#undef __USE_POSIX_DEFINED
#endif
#include <poll.h>

enum init_argument_type_t { STRING, NUMBER, STRING_LIST };
struct init_argument_config_t {
    const char *name;
    const enum init_argument_type_t argument_type;
    int offset;
    union {
        char **string;
        size_t *number;
        char ***string_list;
    };
};

struct init_fifo_config_t {
    bool generate_name;
    char **name;
    int mode;
    int permissions;
    bool created_flag;
    int *fd;
};

struct init_pipe_config_t {
    int *read_fd;
    int *write_fd;
};

struct init_signal_config_t {
    const int signal;
    const __sighandler_t handler;
};

struct init_environment_config_t {
    char *key;
    char **value;
};

enum init_pollfd_type_t { 
    POLLFD_SIGTERM, 
    POLLFD_SIGCHLD, 
    POLLFD_EDITOR_SIMULATOR, 
    POLLFD_SERVER 
};
struct init_pollfd_config_t {
    char *name;
    bool activated;
    struct pollfd *pollfd;
    enum init_pollfd_type_t pollfd_type;
    short pollfd_event_type;
    int *fd;
};


bool init_read_arguments(int argc, char *argv[], struct init_argument_config_t *config, size_t size);
bool init_fifos(struct init_fifo_config_t *config, size_t size);
bool init_pipes(struct init_pipe_config_t *config, size_t size);
bool init_signals(struct init_signal_config_t *config, size_t size);
bool init_set_environment(struct init_environment_config_t *config, size_t size);
bool init_get_environment(struct init_environment_config_t *config, size_t size);
bool init_pollfds(struct init_pollfd_config_t *config, size_t size);

void toggle_pollfd(struct pollfd *pollfd);
void turn_on_pollfd(struct pollfd *pollfd);
void turn_off_pollfd(struct pollfd *pollfd);

void cleanup_fifos(struct init_fifo_config_t *config, size_t size);
void cleanup_pipes(struct init_pipe_config_t *config, size_t size);
void cleanup_signals(struct init_signal_config_t *config, size_t size);
void cleanup_pollfds(struct init_pollfd_config_t *config, size_t size);

#endif