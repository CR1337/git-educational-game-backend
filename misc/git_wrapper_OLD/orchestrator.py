import os
import sys
import socket
import subprocess
from uuid import uuid1

from typing import List


def main() -> None:
    # read args
    server_socket_path: str = sys.argv[1]
    editor_simulator_path: str = sys.argv[2]
    git_path: str = sys.argv[3]
    git_argv: List[str] = sys.argv[4:]
    
    # create sockets
    ## create upward server socket
    if os.path.exists(server_socket_path):
        os.unlink(server_socket_path)
    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server_socket.bind(server_socket_path)

    ## create editor socket
    ...  # TODO

    # get cwd
    cwd = ""  # TODO

    # run git
    git_process = subprocess.Popen(
        [git_path] + git_argv,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        env={
            "GIT_EDITOR": editor_simulator_path
        }
    )



    
    


if __name__ == "__main__":
    main()
