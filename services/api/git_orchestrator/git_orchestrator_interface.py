import os
import socket
from pathlib import Path
from typing import Union, Optional

from git_orchestrator.git_communication import GitCommunication
import models
from filesystem import Filesystem


class ForbiddenPathException(Exception):
    pass


class GitArgumentNormalizer:

    @staticmethod
    def normalize(argument: str, base_directory: Path) -> str:
        base_directory = base_directory.resolve(strict=False)

        try:
            path = Path(argument)
        except Exception:
            return argument

        original_cwd = os.getcwd()
        os.chdir(base_directory)
        absolute_path = path.expanduser().resolve(strict=False)
        os.chdir(original_cwd)

        if absolute_path.exists():
            try:
                absolute_path.relative_to(base_directory)
            except ValueError:
                raise ForbiddenPathException()

            return absolute_path.as_posix()

        else:
            return argument


class GitOrchestratorInterface:

    _git_session_id: str
    _base_directory: Path
    _socket: socket.socket

    def __init__(self, git_session_id: str, base_directory: Path) -> None:
        self._git_session_id = git_session_id

        self._base_directory = base_directory

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect(
            (GitCommunication.ORCHESTRATOR_ADDRESS, GitCommunication.ORCHESTRATOR_PORT)
        )

    def __del__(self) -> None:
        self._socket.close()

    def _register_to_orchestrator(self) -> bool:
        to_orchestrator_registration_packet = {
            "type": "api_registration",
            "git_session_id": self._git_session_id,
        }

        if not GitCommunication.write_json_to_socket(
            self._socket, to_orchestrator_registration_packet
        ):
            return False

        return True

    def run_git_command(
        self, git_command: models.GitCommand
    ) -> Optional[Union[models.GitResult, models.EditorRequest]]:
        if not self._register_to_orchestrator():
            return None

        try:
            normalized_argv = [
                GitArgumentNormalizer.normalize(arg, self._base_directory)
                for arg in git_command.argv
            ]
        except ForbiddenPathException:
            raise

        to_orchestrator_packet = {
            "type": "git_command",
            "git_session_id": self._git_session_id,
            "data": {
                "cwd": self._base_directory.as_posix(),
                "git_editor": Filesystem.GIT_EDITOR_PATH.as_posix(),
                "git_executable": Filesystem.GIT_EXECUTABLE_PATH.as_posix(),
                "git_argv": normalized_argv,
            },
        }

        if not GitCommunication.write_json_to_socket(
            self._socket, to_orchestrator_packet
        ):
            return None

        from_orchestrator_packet = GitCommunication.read_json_from_socket(self._socket)
        if from_orchestrator_packet is None:
            return None

        if from_orchestrator_packet["git_session_id"] != self._git_session_id:
            return None

        data = from_orchestrator_packet["data"]

        match from_orchestrator_packet["type"]:
            case "git_terminated":
                git_result = models.GitResult(
                    id=self._git_session_id,
                    returncode=data["returncode"],
                    stdout=data["stdout"],
                    stderr=data["stderr"],
                )
                return git_result

            case "editor_request":
                editor_request = models.EditorRequest(
                    id=self._git_session_id,
                    file=models.File(
                        filename=Path(data["filename"]), content=data["content"]
                    ),
                    stdout=data["stdout"],
                    stderr=data["stderr"],
                )
                return editor_request

            case _:
                return None

    def send_editor_response(
        self, editor_response: models.EditorResponse
    ) -> Optional[models.GitResult]:
        if not self._register_to_orchestrator():
            return None

        to_orchestrator_packet = {
            "type": "editor_response",
            "git_session_id": self._git_session_id,
            "data": {
                "new_content": editor_response.file.content,
                "abort": editor_response.abort,
            },
        }

        if not GitCommunication.write_json_to_socket(
            self._socket, to_orchestrator_packet
        ):
            return None

        from_orchestrator_packet = GitCommunication.read_json_from_socket(self._socket)
        if from_orchestrator_packet is None:
            return None

        if from_orchestrator_packet["git_session_id"] != self._git_session_id:
            return None

        data = from_orchestrator_packet["data"]

        match from_orchestrator_packet["type"]:
            case "git_terminated":
                git_result = models.GitResult(
                    id=self._git_session_id,
                    returncode=data["returncode"],
                    stdout=data["stdout"],
                    stderr=data["stderr"],
                )
                return git_result

            case _:
                return None

    def terminate_orchestrator(self) -> bool:
        to_orchestrator_packet = {
            "type": "termination_request",
            "git_session_id": self._git_session_id,
        }

        if not GitCommunication.write_json_to_socket(
            self._socket, to_orchestrator_packet
        ):
            return False

        return True
