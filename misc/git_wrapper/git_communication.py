import time
import json
from uuid import uuid1
import socket as sock
from pathlib import Path
from typing import Optional, Dict, Any

CHUNK_SIZE: int = 1024
BUSY_WAIT_TIME: float = 0.1
INTERACTIVE_TERMINATION_MESSAGE: bytes = "q\n".encode(encoding='utf-8')
GIT_EDITOR_VARIABLE_NAME: str = "GIT_EDITOR"
GIT_EDITOR_SOCKET_VARIABLE_NAME: str = "GIT_EDITOR_SOCKET"
ENCODING: str = "utf-8"
TMP_DIRECTORY: Path = Path("/tmp")


def create_socket(bind: bool = False, path: Optional[Path] = None) -> sock.socket:
    socket = sock.socket(sock.AF_UNIX, sock.SOCK_STREAM)

    if bind:
        assert path is not None
        if path.exists():
            path.unlink()
        socket.bind(path.as_posix())

    return socket


def read_socket_complete(socket: sock.socket) -> bytearray:
    data = bytearray()

    data_chunk = socket.recv(CHUNK_SIZE)
    while data_chunk:
        data += data_chunk
        data_chunk = socket.recv(CHUNK_SIZE)

    return data


def wait_for_listen(socket_path: Path) -> sock.socket:
    socket = create_socket(bind=False)

    socket.setblocking(False)

    while True:
        try:
            socket.connect(socket_path.as_posix())
            break

        except sock.error:
            time.sleep(BUSY_WAIT_TIME)

    socket.setblocking(True)

    return socket


def write_json_socket(socket: sock.socket, obj: Dict[str, Any]):
    data = json.dumps(obj).encode(ENCODING)
    socket.send(data)

def read_json_socket(socket: sock.socket) -> Dict[str, Any]:
    data = read_socket_complete(socket)
    return json.loads(data.decode(ENCODING))

def create_socket_path(prefix: str) -> Path:
    return Path(
        TMP_DIRECTORY,
        f"{prefix}{uuid1()}"
    )
