#include "sockets.h"

#include <string.h>

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")
#else
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#endif

int socket_create() {
#ifdef _WIN32
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) 
    {
        return -1;
    }
#endif
    return socket(AF_INET, SOCK_STREAM, 0);
}

int socket_bind(const int sockfd, const uint16_t port)
{
    struct sockaddr_in server_address;
    memset(&server_address, 0, sizeof(server_address));
    server_address.sin_family = AF_INET;
    server_address.sin_addr.s_addr = INADDR_ANY;
    server_address.sin_port = htons(port);
    
    return bind(sockfd, (struct sockaddr*)&server_address, sizeof(server_address));
}

int socket_listen(const int sockfd)
{
    return listen(sockfd, 1);
}

int socket_accept(const int sockfd)
{
    struct sockaddr client_address;
    socklen_t client_address_length = 0;
    return accept(sockfd, &client_address, &client_address_length);
}

int socket_connect(const int sockfd, const char *const server_ip, const uint16_t server_port)
{
    struct sockaddr_in server_address;
    memset(&server_address, 0, sizeof(server_address));
    server_address.sin_family = AF_INET;
    server_address.sin_port = htons(server_port);
    inet_pton(AF_INET, server_ip, &server_address.sin_addr);

    return connect(sockfd, (struct sockaddr*)&server_address, sizeof(server_address));
}

ssize_t socket_send(const int sockfd, const char *const message, const size_t message_length)
{
    return send(sockfd, message, message_length, 0);
}

ssize_t socket_receive(const int sockfd, char *const message, const size_t max_message_length)
{
    return recv(sockfd, message, max_message_length, 0);
}

void socket_close(const int sockfd)
{
    #ifdef _WIN32
    closesocket(sockfd);
    WSACleanup();
#else
    close(sockfd);
#endif
}
