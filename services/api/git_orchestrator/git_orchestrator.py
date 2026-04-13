#!/usr/bin/python3

from __future__ import annotations
import errno
import socket
import select
import enum
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Sequence, Iterable

from git_orchestrator.git_communication import GitCommunication


class GitSessionState(str, enum.Enum):
    INITIALIZED = "initialized"
    GIT_RUNNING = "git_running"
    EDITOR_REQUEST = "editor_request"
    GIT_TERMINATED = "git_terminated"
    CLOSED = "closed"
    KILLED = "killed"


class GitSession:
    INTERACTIVE_TERMINATION_SIGNAL: bytes = "q\n".encode()

    _session_id: str

    _api_connection: socket.socket
    _editor_connection: Optional[socket.socket]

    _state: GitSessionState

    _git_process: subprocess.Popen

    _git_returncode: int
    _git_stdout: str
    _git_stderr: str

    @staticmethod
    def find_by_api_socket_fd(
        sessions: Iterable[GitSession], api_socket_fd: int
    ) -> GitSession:
        for session in sessions:
            if session.api_connection.fileno() == api_socket_fd:
                return session
        raise ValueError(f"No GitSession found for api_socket_fd {api_socket_fd}")

    @staticmethod
    def find_by_editor_socket_fd(
        sessions: Iterable[GitSession], editor_socket_fd: int
    ) -> GitSession:
        for session in sessions:
            if session.editor_connection is None:
                continue
            if session.editor_connection.fileno() == editor_socket_fd:
                return session
        raise ValueError(f"No GitSession found for editor_socket_fd {editor_socket_fd}")

    def __init__(self, session_id: str, api_connection: socket.socket) -> None:
        self._session_id = session_id
        self._api_connection = api_connection
        self._editor_connection = None

        self._state = GitSessionState.INITIALIZED

        self._git_returncode = -1
        self._git_stdout = ""
        self._git_stderr = ""

    def __del__(self) -> None:
        self._state = GitSessionState.CLOSED

    def run(
        self, cwd: Path, git_editor: Path, git_executable: Path, git_argv: List[str]
    ) -> None:
        self._git_process = subprocess.Popen(
            args=[git_executable.as_posix()] + git_argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={
                GitCommunication.ENVIRONMENT_GIT_EDITOR: git_editor.as_posix(),
                GitCommunication.ENVIRONMENT_GIT_SESSION_ID: self._session_id,
                "GIT_PAGER": "",
            },
            cwd=cwd,
        )

        git_stdin = self._git_process.stdin
        assert git_stdin is not None
        git_stdin.write(self.INTERACTIVE_TERMINATION_SIGNAL)

        self._state = GitSessionState.GIT_RUNNING

    def update(self) -> None:
        assert self._git_process
        if self._state in (
            GitSessionState.GIT_TERMINATED,
            GitSessionState.CLOSED,
            GitSessionState.KILLED,
        ):
            return

        out = self._git_process.stdout
        assert out
        err = self._git_process.stderr
        assert err

        ready_streams, _, _ = select.select(
            [out, err], [], [], GitOrchestrator.POLL_WAIT_TIME
        )
        for stream in ready_streams:
            if stream == out:
                self._git_stdout += out.read().decode()
            elif stream == err:
                self._git_stderr += err.read().decode()

        git_returncode = self._git_process.poll()
        if git_returncode is None:
            return
        self._git_returncode = git_returncode

        self._git_process.wait()

        self._state = GitSessionState.GIT_TERMINATED

    def kill_git(self) -> None:
        self._git_process.kill()
        self._state = GitSessionState.KILLED

    @property
    def state(self) -> GitSessionState:
        return self._state

    @state.setter
    def state(self, value: GitSessionState) -> None:
        self._state = value

    @property
    def returncode(self) -> int:
        return self._git_returncode

    @property
    def git_stdout(self) -> str:
        return self._git_stdout

    @property
    def git_stderr(self) -> str:
        return self._git_stderr

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def api_connection(self) -> socket.socket:
        return self._api_connection

    @api_connection.setter
    def api_connection(self, value: socket.socket) -> None:
        self._api_connection = value

    @property
    def editor_connection(self) -> Optional[socket.socket]:
        return self._editor_connection

    @editor_connection.setter
    def editor_connection(self, value: socket.socket) -> None:
        self._editor_connection = value


class PollEventType(str, enum.Enum):
    ANONYMOUS = "anonymous"
    SERVER = "server"
    API = "api"
    EDITOR = "editor"
    GIT = "git"


class GitOrchestrator:

    MAX_CONNECTIONS: int = 2048
    POLL_WAIT_TIME: float = 0.05  # s

    _anonymous_connections: Dict[int, socket.socket]
    _api_connections: Dict[int, socket.socket]
    _editor_connections: Dict[int, socket.socket]
    _git_sessions: Dict[str, GitSession]
    _server_socket: socket.socket
    _server_poll: select.poll
    _anonymous_client_poll: select.poll
    _api_client_poll: select.poll
    _editor_client_poll: select.poll
    _termination_requested: bool

    def __init__(self):
        self._anonymous_connections = {}
        self._api_connections = {}
        self._editor_connections = {}
        self._git_sessions = {}

        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(
            (GitCommunication.ORCHESTRATOR_ADDRESS, GitCommunication.ORCHESTRATOR_PORT)
        )
        self._server_socket.listen(self.MAX_CONNECTIONS)

        self._server_poll = select.poll()
        self._anonymous_client_poll = select.poll()
        self._api_client_poll = select.poll()
        self._editor_client_poll = select.poll()

        self._server_poll.register(self._server_socket, select.POLLIN)

        self._termination_requested = False

    def __del__(self):
        self._server_poll.unregister(self._server_socket)
        self._server_socket.close()

        for git_session in self._git_sessions.values():
            git_session.kill_git()

        for connection in self._anonymous_connections.values():
            socket_fd = connection.fileno()
            self._anonymous_client_poll.unregister(socket_fd)
            connection.close()

        for connection in self._api_connections.values():
            socket_fd = connection.fileno()
            self._api_client_poll.unregister(socket_fd)
            connection.close()

        for connection in self._editor_connections.values():
            socket_fd = connection.fileno()
            self._editor_client_poll.unregister(socket_fd)
            connection.close()

    def _mainloop(self):
        for git_session in self._git_sessions.values():
            git_session.update()

        events: Sequence[
            Tuple[Optional[int], Optional[GitSession], int, PollEventType]
        ] = (
            [
                (fd, None, event, PollEventType.SERVER)
                for fd, event in self._server_poll.poll(self.POLL_WAIT_TIME)
            ]
            + [
                (fd, None, event, PollEventType.ANONYMOUS)
                for fd, event in self._anonymous_client_poll.poll(self.POLL_WAIT_TIME)
            ]
            + [
                (fd, None, event, PollEventType.API)
                for fd, event in self._api_client_poll.poll(self.POLL_WAIT_TIME)
            ]
            + [
                (fd, None, event, PollEventType.EDITOR)
                for fd, event in self._editor_client_poll.poll(self.POLL_WAIT_TIME)
            ]
            + [
                (None, git_session, select.POLLIN, PollEventType.GIT)
                for git_session in self._git_sessions.values()
                if git_session.state == GitSessionState.GIT_TERMINATED
            ]
        )

        for fd, git_session, event, event_type in events:

            match event_type:
                case PollEventType.SERVER:
                    socket_ = self._server_socket
                    self._handle_server_event(socket_, event)

                case PollEventType.ANONYMOUS:
                    assert fd is not None
                    socket_ = self._anonymous_connections[fd]
                    self._handle_anonymous_event(socket_, event)

                case PollEventType.API:
                    assert fd is not None
                    socket_ = self._api_connections[fd]
                    self._handle_api_event(socket_, event)

                case PollEventType.EDITOR:
                    assert fd is not None
                    socket_ = self._editor_connections[fd]
                    self._handle_editor_event(socket_, event)

                case PollEventType.GIT:
                    assert git_session is not None
                    self._handle_git_event(git_session, event)

    def _handle_server_event(self, socket_: socket.socket, event: int):
        if event & select.POLLIN:
            connection, _ = socket_.accept()
            connection_fd = connection.fileno()
            self._anonymous_connections[connection_fd] = connection
            self._anonymous_client_poll.register(connection_fd, select.POLLIN)

        elif event & select.POLLERR:
            error = socket_.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            match error:
                case errno.EINTR:
                    pass  # interrupted system call, just try again next iteration
                case errno.EMFILE:
                    pass  # too many open sockets, ignore, client must handle
                case errno.EADDRINUSE:
                    raise SystemError(
                        f"Address {GitCommunication.ORCHESTRATOR_ADDRESS}:{GitCommunication.ORCHESTRATOR_PORT} aleady in use."
                    )
                case errno.EACCES:
                    raise SystemError("Permission denied.")
                case errno.ENFILE:
                    raise SystemError("System-wide file descriptor limit reached.")
                case errno.ENOMEM:
                    raise SystemError("Out of memory.")
                case errno.EBADF:
                    raise SystemError("Invalid file descriptor.")
                case errno.ENOTSOCK:
                    raise SystemError("Not a socket")
                case _:
                    raise SystemError(f"Unexpected error: {error}")

        else:
            raise ValueError("Unexpected event on server socket.")

    def _handle_anonymous_event(self, socket_: socket.socket, event: int):
        socket_fd = socket_.fileno()

        if event & select.POLLIN:
            packet = GitCommunication.read_json_from_socket(socket_)
            if packet is None:
                self._cleanup_anonymous_connection(socket_fd)
                return
            else:
                match packet["type"]:
                    case "api_registration":
                        self._anonymous_client_poll.unregister(socket_fd)
                        self._anonymous_connections.pop(socket_fd)

                        self._api_connections[socket_fd] = socket_
                        self._api_client_poll.register(socket_fd, select.POLLIN)

                    case "editor_registration":
                        self._anonymous_client_poll.unregister(socket_fd)
                        self._anonymous_connections.pop(socket_fd)

                        self._editor_connections[socket_fd] = socket_
                        self._editor_client_poll.register(socket_fd, select.POLLIN)

                    case "termination_request":
                        self._termination_requested = True
                        return

                    case _:
                        self._cleanup_anonymous_connection(socket_fd)
                        return

        elif event & select.POLLHUP:
            self._cleanup_anonymous_connection(socket_fd)
            return

        elif event & select.POLLERR:
            error = socket_.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            match error:
                case errno.EINTR:
                    pass  # interrupted system call, just try again next iteration
                case errno.EBADF:
                    raise SystemError("Invalid file descriptor.")
                case errno.ENOBUFS:
                    raise SystemError("No buffer space available.")
                case errno.ENOMEM:
                    raise SystemError("Out of memory.")
                case _:
                    self._cleanup_anonymous_connection(socket_fd)
                    return

        else:
            raise ValueError("Unexpected event on anonymous socket.")

    def _handle_api_event(self, socket_: socket.socket, event: int):
        socket_fd = socket_.fileno()

        if event & select.POLLIN:
            from_api_packet = GitCommunication.read_json_from_socket(socket_)
            if from_api_packet is None:
                self._cleanup_api_connection(socket_fd)
                return
            else:
                git_session_id = from_api_packet["git_session_id"]
                from_api_data = from_api_packet["data"]

                match from_api_packet["type"]:
                    case "git_command":
                        git_session = GitSession(git_session_id, socket_)
                        assert git_session.state == GitSessionState.INITIALIZED
                        git_session.run(
                            Path(from_api_data["cwd"]),
                            Path(from_api_data["git_editor"]),
                            Path(from_api_data["git_executable"]),
                            from_api_data["git_argv"],
                        )
                        assert git_session.state == GitSessionState.GIT_RUNNING
                        self._git_sessions[git_session_id] = git_session

                    case "editor_response":
                        git_session = self._git_sessions[git_session_id]
                        git_session.api_connection = socket_
                        assert git_session.state == GitSessionState.EDITOR_REQUEST

                        new_content = from_api_data["new_content"]
                        abort = from_api_data["abort"]

                        to_editor_packet = {
                            "type": "editor_response",
                            "git_session_id": git_session_id,
                            "data": {"new_content": new_content, "abort": abort},
                        }

                        assert git_session.editor_connection is not None
                        if not GitCommunication.write_json_to_socket(
                            git_session.editor_connection, to_editor_packet
                        ):
                            self._cleanup_editor_connection(
                                git_session.editor_connection.fileno()
                            )
                            return
                        else:
                            git_session.state = GitSessionState.GIT_RUNNING

                    case _:
                        pass  # ignore

        elif event & select.POLLHUP:
            self._cleanup_api_connection(socket_fd)
            return

        elif event & select.POLLERR:
            error = socket_.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            match error:
                case errno.EINTR:
                    pass  # interrupted system call, just try again next iteration
                case errno.EBADF:
                    raise SystemError("Invalid file descriptor.")
                case errno.ENOBUFS:
                    raise SystemError("No buffer space available.")
                case errno.ENOMEM:
                    raise SystemError("Out of memory.")
                case _:
                    self._cleanup_api_connection(socket_fd)
                    return

        else:
            raise ValueError("Unexpected event on api socket.")

    def _handle_editor_event(self, socket_: socket.socket, event: int):
        socket_fd = socket_.fileno()

        if event & select.POLLIN:
            from_editor_packet = GitCommunication.read_json_from_socket(socket_)
            if from_editor_packet is None:
                return
            else:
                git_session_id = from_editor_packet["git_session_id"]
                from_editor_data = from_editor_packet["data"]

                match from_editor_packet["type"]:
                    case "editor_request":
                        git_session = self._git_sessions[git_session_id]
                        assert git_session.state == GitSessionState.GIT_RUNNING
                        git_session.editor_connection = socket_

                        filename = from_editor_data["filename"]
                        content = from_editor_data["content"]

                        to_api_packet = {
                            "type": "editor_request",
                            "git_session_id": git_session_id,
                            "data": {
                                "filename": filename,
                                "content": content,
                                "stdout": git_session.git_stdout,
                                "stderr": git_session.git_stderr,
                            },
                        }

                        if not GitCommunication.write_json_to_socket(
                            git_session.api_connection, to_api_packet
                        ):
                            self._cleanup_api_connection(
                                git_session.api_connection.fileno()
                            )
                            return
                        else:
                            git_session.state = GitSessionState.EDITOR_REQUEST

                    case _:
                        pass  # ignore

        elif event & select.POLLHUP:
            self._cleanup_editor_connection(socket_fd)
            return

        elif event & select.POLLERR:
            error = socket_.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            match error:
                case errno.EINTR:
                    pass  # interrupted system call, just try again next iteration
                case errno.EBADF:
                    raise SystemError("Invalid file descriptor.")
                case errno.ENOBUFS:
                    raise SystemError("No buffer space available.")
                case errno.ENOMEM:
                    raise SystemError("Out of memory.")
                case _:
                    self._cleanup_editor_connection(socket_fd)
                    return

        else:
            raise ValueError("Unexpected event on editor socket.")

    def _handle_git_event(self, git_session: GitSession, event: int) -> None:
        assert event & select.POLLIN

        if git_session.state == GitSessionState.KILLED:
            return

        to_api_packet = {
            "type": "git_terminated",
            "git_session_id": git_session.session_id,
            "data": {
                "returncode": git_session.returncode,
                "stdout": git_session.git_stdout,
                "stderr": git_session.git_stderr,
            },
        }

        if not GitCommunication.write_json_to_socket(
            git_session.api_connection, to_api_packet
        ):
            self._cleanup_api_connection(git_session.api_connection.fileno())
            return
        else:
            self._cleanup_git_session(git_session)

    def _cleanup_anonymous_connection(self, socket_fd: int) -> None:
        self._anonymous_client_poll.unregister(socket_fd)
        socket = self._anonymous_connections[socket_fd]
        socket.close()
        self._anonymous_connections.pop(socket_fd)

    def _cleanup_api_connection(self, socket_fd: int) -> None:
        self._api_client_poll.unregister(socket_fd)
        socket = self._api_connections[socket_fd]
        socket.close()
        self._api_connections.pop(socket_fd)

    def _cleanup_editor_connection(self, socket_fd: int) -> None:
        self._editor_client_poll.unregister(socket_fd)
        socket = self._api_connections[socket_fd]
        socket.close()
        self._editor_connections.pop(socket_fd)

    def _cleanup_git_session(self, git_session: GitSession) -> None:
        api_connection_fd = git_session.api_connection.fileno()
        git_session.api_connection.close()
        self._api_client_poll.unregister(api_connection_fd)
        self._api_connections.pop(api_connection_fd)

        if git_session.editor_connection:
            editor_connection_fd = git_session.editor_connection.fileno()
            git_session.editor_connection.close()
            self._editor_client_poll.unregister(editor_connection_fd)
            self._editor_connections.pop(editor_connection_fd)

        self._git_sessions.pop(git_session.session_id)

    def run(self) -> None:
        while not self._termination_requested:
            self._mainloop()
