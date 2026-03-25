#!/usr/bin/python3

import os
import sys
import json
from pathlib import Path

import git_communication as gc


def main():
    # read editor socket path from environment
    worker_editor_socket_path_string = os.environ.get("GIT_EDITOR_SIMULATOR_SOCKET")
    if worker_editor_socket_path_string is None:
        exit(1)
    worker_editor_socket_path = Path(worker_editor_socket_path_string)

    # get the filename by git and check it
    filename = Path(sys.argv[1])
    if not filename.exists():
        exit(1)

    # read the file content
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # pack the data for the worker into json
    data = json.dumps({
        "filename": filename.as_posix(),
        "content": content
    }).encode(encoding='utf-8')

    # wait for the worker to listen
    worker_editor_socket = gc.wait_for_listen(worker_editor_socket_path)

    # send the data
    worker_editor_socket.send(data)

    # wait for and read the response by the worker
    worker_data = gc.read_socket_complete(worker_editor_socket)

    worker_editor_socket.close()

    # parse the data as json
    json_data = json.loads(worker_data.decode(encoding='utf-8'))
    new_content = json_data["new_content"]
    abort = json_data["abort"]

    # write the new content if not aborted
    if not abort:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_content)


if __name__ == "__main__":
    main()
