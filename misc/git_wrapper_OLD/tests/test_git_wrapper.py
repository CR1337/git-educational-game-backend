import os
import time
import shutil
import subprocess
from typing import Any, Generator, List
import pytest
from uuid import uuid4
from ..build import communication as comm


REPO_DIRECTORY: str = "test_repo"
TEST_FILENAME: str = os.path.join(REPO_DIRECTORY, "test.txt")


@pytest.fixture
def setup_and_teardown() -> Generator[None, Any, None]:
    if os.path.exists(REPO_DIRECTORY):
        shutil.rmtree(REPO_DIRECTORY)
    os.mkdir(REPO_DIRECTORY)

    subprocess.run(["git", "init"], cwd=REPO_DIRECTORY)
    
    yield

    if os.path.exists(REPO_DIRECTORY):
        shutil.rmtree(REPO_DIRECTORY)


def get_orchestrator_arguments(git_argv: List[str]) -> List[str]:
    return [
        os.path.join("..", "build", "orchestrator"),
        "/" + os.path.join("tmp", f"fifo_{uuid4()}"),
        "/" + os.path.join("tmp", f"fifo_{uuid4()}"),
        os.path.join("..", "build", "editor_simulator"),
        "/" + os.path.join("usr", "bin", "git"),
        str(len(git_argv))
    ] + git_argv


def test_git_status(setup_and_teardown) -> None:
    # test of simple git command

    arguments = get_orchestrator_arguments(["status"])
    print("ARGS:")
    for arg in arguments:
        print(arg)
    print(flush=True)


    server_in_fifo_name = arguments[1]
    server_out_fifo_name = arguments[2]

    os.mkfifo(server_in_fifo_name, 0o666)
    os.mkfifo(server_out_fifo_name, 0o666)

    process = subprocess.Popen(
        arguments,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=REPO_DIRECTORY
    )


    
    server_out_fifo_fd = os.open(server_out_fifo_name, os.O_RDONLY)


    packet = comm.communication_packet_t()
    packet_ptr = comm.pointer(packet)
    packet_ptr_ptr = comm.pointer(packet_ptr)
    packet_size = comm.c_size_t()
    success = comm.communication_read(server_out_fifo_fd,packet_ptr_ptr,comm.byref(packet_size))

    assert success

    print(f"{packet.magic=}")
    print(f"{packet.size=}")
    print(f"{packet.type=}")
    print(f"{packet.payload_size=}")

    process_stdin = process.stdin
    assert process_stdin
    process_stdin.write("\n\n".encode())
    process_stdin.flush()
    process_stdin.close()

    returncode = process.wait()
    stdout, stderr = [x.decode() for x in process.communicate()]
    print(f"Wrapper-RETURNCODE: {returncode}")
    print(f"Wrapper-STDOUT({len(stdout)}):\n{stdout}\n")
    print(f"Wrapper-STDERR({(len(stderr))}):\n{stderr}\n")

    os.unlink(server_in_fifo_name)
    os.unlink(server_out_fifo_name)
    # assert False


def test_git_clean_i(setup_and_teardown):
    # test of interactive git command

    ...  # TODO



    