#ifndef __SOCKETS_H__
#define __SOCKETS_H__

#include <stddef.h>
#include <stdint.h>
#include <sys/types.h>

int socket_create();
int socket_bind(const int sockfd, const uint16_t port);
int socket_listen(const int sockfd);
int socket_accept(const int sockfd);
int socket_connect(const int sockfd, const char *const server_ip, const uint16_t server_port);
ssize_t socket_send(const int sockfd, const char *const message, const size_t message_length);
ssize_t socket_receive(const int sockfd, char *const message, const size_t max_message_length);
void socket_close(const int sockfd);

#endif
