import os
import time
from pathlib import Path
import subprocess
from models.game import GameIdType
from models.git import GitCommand, GitCommandResult, GitEditorSession, GitEditorSessionIdType, GitCommandDoneResult, GitResultType
from controllers.redis_controller import RedisController
from controllers.celery_controller import CeleryController
from controllers.filesystem_controller import FileController


class GitController:

    GIT_WAIT_TIME: float = 0.5  # s

    @classmethod
    def _run_command_task_func(cls, game_id: GameIdType, git_command: GitCommand) -> GitCommandDoneResult:
        current_working_directory = FileController.get_current_working_directory(game_id)
        command = (
            ["cd", current_working_directory.as_posix()]
            + ["&&"]
            + ["git"] + git_command.arguments
        )
        env = os.environ.copy()
        env.update({
            "GIT_EDITOR": "/" + str(Path(
                "app", 
                "editor_simulator", 
                "editor_simulator.py"
            ))
        })
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        process.wait()
        stdout, stderr = process.communicate()
        status_code = process.returncode

        git_command_done_result = GitCommandDoneResult(
            command = git_command,
            stdout=stdout,
            stderr=stderr,
            status_code=status_code
        )

        return git_command_done_result


    @classmethod
    def run_command(cls, game_id: GameIdType, git_command: GitCommand) -> GitCommandResult:
        task_id = CeleryController.run_task(
            cls._run_command_task_func,
            (game_id, git_command)
        )

        time.sleep(cls.GIT_WAIT_TIME)

        if CeleryController.task_is_ready(task_id):
            git_command_done_result = CeleryController.get_task_result(task_id)
            git_command_result = GitCommandResult(
                git_result_type=GitResultType.DONE,
                git_result=git_command_done_result
            )
            return git_command_result
        
        else:



    @classmethod
    def start_editor_session(cls, game_id: GameIdType, editor_session: GitEditorSession) -> GitEditorSession:
        key = f"game_id:{game_id}:git_editor_session_id:{editor_session.git_editor_session_id}:git_editor_session"
        RedisController.set_json(
            key,
            editor_session.model_dump()
        )

    @classmethod
    def end_editor_session(cls, game_id: GameIdType, editor_session_id: GitEditorSessionIdType) -> GitCommandResult:
        ...