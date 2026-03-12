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
    print()

    result = subprocess.run(
        arguments,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=REPO_DIRECTORY
    )

    stdout = result.stdout.decode("utf-8")
    stderr = result.stderr.decode("utf-8")
    returncode = result.returncode

    print(f"STDOUT:\n{stdout}\n")
    print(f"STDERR:\n{stderr}\n")
    print(f"RETURNCODE:\n{returncode}\n")

    assert len(stdout) > 1
    assert len(stderr) == 0
    assert returncode == 0


# def test_git_commit(setup_and_teardown) -> None:
#     # test of git command that opens an editor

#     with open(TEST_FILENAME, 'w') as f:
#         f.write("test")

#     arguments = get_orchestrator_arguments(["commit"])
#     print("ARGS:")
#     for arg in arguments:
#         print(arg)
#     print()

#     server_in_fifo_name = arguments[1]
#     server_out_fifo_name = arguments[2]

#     process = subprocess.Popen(
#         arguments,
#         stdout=subprocess.PIPE,
#         stderr=subprocess.PIPE,
#         cwd=REPO_DIRECTORY
#     )

#     while not os.path.exists(server_out_fifo_name):
#         time.sleep(0.1)

#     server_in_fifo_fd = os.open(server_in_fifo_name, os.O_WRONLY)
#     server_out_fifo_fd = os.open(server_out_fifo_name, os.O_RDONLY)

#     packet = comm.communication_packet_t()
#     packet_size = comm.c_size_t()
#     success = comm.communication_read(
#         server_out_fifo_fd,
#         comm.byref(packet),
#         comm.byref(packet_size)
#     )

#     print("success:", success)
#     print("packet size:", packet_size.value)
#     print("packet type:", packet.type)

#     ...  # TODO


def test_git_clean_i(setup_and_teardown):
    # test of interactive git command

    ...  # TODO



    