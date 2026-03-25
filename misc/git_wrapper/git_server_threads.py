from pathlib import Path
from typing import List

from controllers.celery_controller import CeleryController
from controllers.redis_controller import RedisController

import git_wrapper.git_communication as gc
from git_wrapper.git_worker import git_worker

def server_thread_stage_1(
    game_id: str,
    git_session_id: str,
    git_cwd: Path,
    git_editor_path: Path,
    git_path: Path,
    git_argv: List[str]
):
    server_worker_stage_1_socket_path = gc.create_socket_path("git_server_worker_stage_1_socket_")

    server_worker_stage_1_socket = gc.create_socket(
        bind=True,
        path=server_worker_stage_1_socket_path
    )
    server_worker_stage_1_socket.listen(1)

    worker_id = CeleryController.run_task(
        git_worker,
        server_worker_stage_1_socket_path.as_posix(),
        git_cwd.as_posix(),
        git_editor_path.as_posix(),
        git_path.as_posix(),
        git_argv
    )

    worker_connection, _ = server_worker_stage_1_socket.accept()
    
    data = gc.read_json_socket(worker_connection)

    message_type = data.get("type")

    if message_type == "terminated":
        return CeleryController.get_task_result(worker_id)
    
    if message_type != "editor_request":
        raise RuntimeError(f"Received unexpected data from worker: {data}")
    
    RedisController.set(
        f"game_id:{game_id}:git_session_id:{git_session_id}:worker_id",
        worker_id
    )

    RedisController.set(
        f"game_id:{game_id}:git_session_id:{git_session_id}:server_worker_stage_2_socket_path",
        data["socket_name"]
    )

    server_worker_stage_1_socket.close()
    server_worker_stage_1_socket_path.unlink()

    return data["editor_data"]


def server_thread_stage_2(
    game_id: str,
    git_session_id: str,
    new_content: str,
    abort: bool
):
    worker_id = RedisController.get(
        f"game_id:{game_id}:git_session_id:{git_session_id}:worker_id"
    )

    server_worker_stage_2_socket_path = RedisController.get(
        f"game_id:{game_id}:git_session_id:{git_session_id}:server_worker_stage_2_socket_path"
    )

    server_worker_stage_2_socket = gc.wait_for_listen(server_worker_stage_2_socket_path)

    data = {
        "new_content": new_content,
        "abort": abort
    }

    gc.write_json_socket(server_worker_stage_2_socket, data)

    server_worker_stage_2_socket.close()

    return CeleryController.get_task_result(worker_id)
