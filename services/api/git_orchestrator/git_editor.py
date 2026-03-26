#!/usr/bin/python3

import os
import sys
import socket
from pathlib import Path

from git_communication import GitCommunication


class GitEditor:

    _filename: Path
    _git_session_id: str
    _socket: socket.socket

    def __init__(self) -> None:
        self._filename = Path(sys.argv[1])

        self._git_session_id = os.environ[GitCommunication.ENVIRONMENT_GIT_SESSION_ID]

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect(
            (GitCommunication.ORCHESTRATOR_ADDRESS, GitCommunication.ORCHESTRATOR_PORT)
        )

    def __del__(self) -> None:
        self._socket.close()

    def run(self):
        with open(self._filename, "r", encoding=GitCommunication.ENCODING) as f:
            content = f.read()

        to_orchestrator_registration_packet = {
            "type": "editor_registration",
            "git_session_id": self._git_session_id,
        }

        if not GitCommunication.write_json_to_socket(
            self._socket, to_orchestrator_registration_packet
        ):
            raise SystemError("Error while writing to orchestrator.")

        to_orchestrator_request_packet = {
            "type": "editor_request",
            "git_session_id": self._git_session_id,
            "data": {"filename": self._filename.as_posix(), "content": content},
        }

        if not GitCommunication.write_json_to_socket(
            self._socket, to_orchestrator_request_packet
        ):
            raise SystemError("Error while writing to orchestrator.")

        from_orchestrator_packet = GitCommunication.read_json_from_socket(self._socket)
        if from_orchestrator_packet is None:
            raise SystemError("Error while reading from orchestrator.")

        assert from_orchestrator_packet["type"] == "editor_response"
        assert from_orchestrator_packet["git_session_id"] == self._git_session_id

        new_content = from_orchestrator_packet["data"]["new_content"]
        abort = from_orchestrator_packet["data"]["abort"]

        if not abort:
            with open(self._filename, "w", encoding=GitCommunication.ENCODING) as f:
                f.write(new_content)


def main() -> None:
    try:
        git_editor = GitEditor()
    except Exception as e:
        print(e, flush=True)
        raise

    try:
        git_editor.run()
    except Exception as e:
        print(e, flush=True)
        raise


if __name__ == "__main__":
    main()
