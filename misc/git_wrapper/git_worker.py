import subprocess
import select
from pathlib import Path
from typing import List, Tuple

import git_wrapper.git_communication as gc
from controllers.celery_controller import CeleryController

@CeleryController.app.task
def git_worker(
    server_worker_stage_1_socket_path: str,
    git_cwd: str,
    git_editor_path: str,
    git_path: str,
    git_argv: List[str] 
) -> Tuple[int, str, str]:
    # Create sockets.

    ## Create the socket, to communicate with the editor process. 
    ## This worker will bind it.
    worker_editor_socket_path = gc.create_socket_path("git_worker_editor_socket_")
    worker_editor_socket = gc.create_socket(
        bind=True, 
        path=worker_editor_socket_path
    )

    # Prepare environment for git process.
    environment = {
        gc.GIT_EDITOR_VARIABLE_NAME: git_editor_path,
        gc.GIT_EDITOR_SOCKET_VARIABLE_NAME: worker_editor_socket_path
    }

    # Launch git.
    git_process = subprocess.Popen(
        [git_path] + git_argv,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=git_cwd,
        env=environment
    )

    # Terminate interactive git sessions.
    git_stdin = git_process.stdin
    assert git_stdin
    git_stdin.write(gc.INTERACTIVE_TERMINATION_MESSAGE)
    git_stdin.close()

    # wait for the server thread to listen on the server socket
    server_worker_stage_1_socket = gc.wait_for_listen(Path(server_worker_stage_1_socket_path))

    # check if the editor was opened checking if it wrote something to the socket
    worker_editor_socket.listen(1)
    ready_to_read, _, _ = select.select([worker_editor_socket], [], [], 5.0)
    
    if ready_to_read:
        # the editor wrote something to the socket, now read it
        
        editor_connection, _ = worker_editor_socket.accept()
        editor_data = gc.read_json_socket(editor_connection)

        # prepare an editor_request package to be sent to the server thread
        server_worker_stage_2_socket_path = gc.create_socket_path("git_server_worker_stage_2_socket_")
        data = {
            "type": "editor_request",
            "socket_name": server_worker_stage_2_socket_path,
            "data": editor_data
        }

        # send the data the server thread
        gc.write_json_socket(server_worker_stage_1_socket, data)

        # Create the socket, to communicate with the server thread that 
        # returns the results to the client. This worker will Bind it.
        server_worker_stage_2_socket = gc.create_socket(
            bind=True, 
            path=server_worker_stage_2_socket_path
        )

        # wait for the server thread to respond
        server_worker_stage_2_socket.listen(1)
        server_connection, _ = server_worker_stage_2_socket.accept()

        # read the responce from the server thread
        server_data = gc.read_socket_complete(server_worker_stage_2_socket)

        server_worker_stage_2_socket.close()
        server_worker_stage_2_socket_path.unlink()

        # send the server response to the editor
        worker_editor_socket.send(server_data)

    else:
        # prepare a terminated package to be sent to the server thread
        data = {
            "type": "terminated",
            "data": None
        }

        # send the data the server thread
        gc.write_json_socket(server_worker_stage_1_socket, data)

    server_worker_stage_1_socket.close()

    worker_editor_socket.close()
    worker_editor_socket_path.unlink()

    # wait for git to terminate and read its output
    git_returncode = git_process.wait()
    git_stdout, git_stderr = [
        b.decode() for b in git_process.communicate()
    ]

    return git_returncode, git_stdout, git_stderr
