#include <stdlib.h>
#include <stdio.h>
#include <stdarg.h>
#include <stdbool.h>
#include <limits.h>
#include <unistd.h>

#include "sockets.h"
#include "debug.h"
#include "server_port.h"

#define COLOR COLOR_RED

enum {
    USER_SELECTION_OPEN_EDITOR = 0,
    USER_SELECTION_FAIL = 1
};

static const size_t MAX_FILENME_LENGTH = 1024;
static const char OPEN_EDITOR_COMMAND[] = "nano";
static const int DEFAULT_USER_SELECTION = USER_SELECTION_OPEN_EDITOR;
static const uint8_t SUCCESS_RESPONSE = 0;
static const uint8_t FAILURE_RESPONSE = 1;
static const size_t MAX_PATH_LENGTH = 1024;

static bool repo_initialized = false;
static bool socket_open = false;

int initialize_repo() 
{
    return system("git init");
}

int trigger_open_editor()
{
    char cwd[MAX_PATH_LENGTH];
    char git_editor_env[MAX_PATH_LENGTH + 32];

    if (getcwd(cwd, sizeof(cwd)) == NULL)
    {
        debug_print(COLOR, "Could not get cwd.\n");
        return 1;
    }
    
    snprintf(
        git_editor_env, 
        sizeof(git_editor_env), 
        "GIT_EDITOR=%s/editor-adapter", 
        cwd
    );

    pid_t pid = fork();
    if (pid < 0)
    {
        debug_print(COLOR, "Error forking.\n");
        return 1;
    }
    else if (pid == 0)
    {
        putchar('\n');
        putenv(git_editor_env);
        execlp("git", "git", "commit", "--allow-empty", NULL);

        // if execlp returns an error occurred
        debug_print(COLOR, "Error running git commit.\n");
        return 1;
    }

    return 0;
}

int open_editor(const char *filename) 
{
    size_t buffer_size = MAX_FILENME_LENGTH + sizeof(OPEN_EDITOR_COMMAND); 
    char command_buffer[buffer_size];
    snprintf(
        command_buffer,
        buffer_size,
        "%s %s",
        OPEN_EDITOR_COMMAND,
        filename
    );
    return system(command_buffer);
}

int remove_repo()
{
    return system("rm -rf .git");
}

void cleanup(int server_sockfd) 
{
    if (socket_open)
    {
        socket_close(server_sockfd);
        socket_open = false;
        debug_print(COLOR, "Server socket closed.\n");
    }

    if (repo_initialized)
    {
        errno = 0;
        if (remove_repo() || errno) {
            debug_print(COLOR, "Error removing git repository.\n");
            print_error(COLOR);
            exit(EXIT_FAILURE);
        }
        repo_initialized = false;
        debug_print(COLOR, "Successfully removed git repository.\n");
    }
}

int initialize()
{
    int server_sockfd = 0;

    errno = 0;
    if (initialize_repo() || errno)
    {
        debug_print(COLOR, "Error initializing git repository.\n");
        goto ERROR;
    }
    repo_initialized = true;
    debug_print(COLOR, "Initialized git repository.\n");

    errno = 0;
    if ((server_sockfd = socket_create()) < 0 || errno) 
    {
        debug_print(COLOR, "Error creating socket.\n");
        goto ERROR;
    }
    debug_print(COLOR, "Created socket soccessfully.\n");

    errno = 0;
    if ((socket_bind(server_sockfd, SERVER_PORT)) < 0 || errno)
    {
        debug_print(COLOR, "Error binding socket.\n");
        goto ERROR;
    }
    debug_print(COLOR, "Socket bound successfully.\n");

    errno = 0;
    if ((socket_listen(server_sockfd)) < 0) 
    {
        debug_print(COLOR, "Error listening on socket.\n");
        goto ERROR;
    }
    debug_print(COLOR, "Listened on socket successfully.\n");

    return server_sockfd;
ERROR:
    print_error(COLOR);
    cleanup(server_sockfd);
    exit(EXIT_FAILURE);
}

int user_iteraction()
{
    debug_print(COLOR, "%d - Open Editor (default)\n", USER_SELECTION_OPEN_EDITOR);
    debug_print(COLOR, "%d - Fail\n", USER_SELECTION_FAIL);
    debug_print(COLOR, "\nSelect a option:");
    int selection = DEFAULT_USER_SELECTION;
    int result = scanf("%d", &selection);
    if (result <= 0)
    {
        debug_print(COLOR, "Invalid user input. Using default: opening editor.\n");
        selection = DEFAULT_USER_SELECTION;
    }
    return selection;
}

void communicate(int server_sockfd) 
{
    char filename[MAX_FILENME_LENGTH];

    errno = 0;
    if (trigger_open_editor() || errno)
    {
        debug_print(COLOR, "Error triggering opening editor.\n");
        goto ERROR;
    }
    debug_print(COLOR, "Triggered opening editor successfully.\n");

    int client_sockfd = 0;
    errno = 0;
    if ((client_sockfd = socket_accept(server_sockfd)) < 0 || errno) 
    {
        debug_print(COLOR, "Error accepting connection.\n");
        goto ERROR;
    }
    debug_print(COLOR, "Successfully accepted connection.\n");

    errno = 0;
    if ((socket_receive(client_sockfd, filename, MAX_FILENME_LENGTH)) < 0 || errno) 
    {
        debug_print(COLOR, "Error receiving filename.\n");
        goto ERROR;
    }
    debug_print(COLOR, "Successfully received filename: %s.\n", filename);

    const int user_selection = user_iteraction();
    char response = 0;
    switch (user_selection) 
    {
        case USER_SELECTION_OPEN_EDITOR:
            errno = 0;
            if (open_editor(filename) || errno) 
            {
                debug_print(COLOR, "Error opening editor.\n");
                goto ERROR;
            }
            debug_print(COLOR, "Opened editor successfully.\n");
            response = SUCCESS_RESPONSE;
            break;

        case USER_SELECTION_FAIL:
        default:
            response = FAILURE_RESPONSE;
            debug_print(COLOR, "Simulating editor failure.\n");
            break;
    }

    errno = 0;
    if ((socket_send(client_sockfd, &response, sizeof(uint8_t))) < 0 || errno)
    {
        debug_print(COLOR, "Error sending response: %d.\n", response);
        goto ERROR;
    }
    debug_print(COLOR, "Successfully sent response: %d.\n", response);

    return;
ERROR:
    print_error(COLOR);
    cleanup(server_sockfd);
    exit(EXIT_FAILURE);
}

int main() 
{
    int server_sockfd = initialize();    
    communicate(server_sockfd);
    cleanup(server_sockfd);

    return EXIT_SUCCESS;
}
