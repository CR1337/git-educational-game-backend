import json
import socket
import struct
from typing import Dict, Optional, Any


class GitCommunication:

    ORCHESTRATOR_ADDRESS: str = "127.0.0.1"
    ORCHESTRATOR_PORT: int = 12345

    ENVIRONMENT_GIT_EDITOR: str = "GIT_EDITOR"
    ENVIRONMENT_GIT_SESSION_ID: str = "GIT_SESSION_ID"

    ENCODING: str = "utf-8"

    CHUNK_SIZE: int = 1024

    HEADER_FORMAT: str = ">I"
    HEADER_SIZE: int = struct.calcsize(HEADER_FORMAT)

    @classmethod
    def read_json_from_socket(cls, socket_: socket.socket) -> Optional[Dict[str, Any]]:
        try:
            header = socket_.recv(cls.HEADER_SIZE)
            if not header:
                return None
            length = struct.unpack(cls.HEADER_FORMAT, header)[0]

            data = bytearray()
            while len(data) < length:
                chunk = socket_.recv(min(cls.CHUNK_SIZE, length - len(data)))
                if not chunk:
                    return None
                data += chunk

            return json.loads(data.decode(GitCommunication.ENCODING))

        except (
            socket.timeout,
            ConnectionRefusedError,
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ):
            return None

    @classmethod
    def write_json_to_socket(
        cls, socket_: socket.socket, object_: Dict[str, Any]
    ) -> bool:
        data = json.dumps(object_).encode(GitCommunication.ENCODING)
        length = len(data)
        header = struct.pack(cls.HEADER_FORMAT, length)

        try:
            socket_.sendall(header)
            socket_.sendall(data)
            return True

        except (socket.timeout, BrokenPipeError, ConnectionRefusedError, OSError):
            return False
