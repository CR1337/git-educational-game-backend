from fastapi import APIRouter, status
from models.git import GitCommand, GitCommandResult, GitEditorSession, GitEditorSessionIdType
from models.game import GameIdType
from models.filesystem import Filepath
from controllers.git_controller import GitController

router = APIRouter(prefix="/games/{game_id}/git", tags=["git"])


@router.post(
    "/",
    response_model=GitCommandResult,
    status_code=status.HTTP_200_OK
)
async def git_command(
    game_id: GameIdType,
    git_command: GitCommand
) -> GitCommandResult:
    result: GitCommandResult = GitController.run_command(game_id, git_command)
    return result


@router.post(
    "/editor-session/{editor-session-id}/init",
    response_model=GitEditorSession,
    status_code=status.HTTP_201_CREATED
)
async def create_editor_session(
    game_id: GameIdType,
    editor_session_id: GitEditorSessionIdType,
    filepath: Filepath
) -> GitEditorSession:
    editor_session: GitEditorSession = GitController.create_editor_session(game_id, editor_session_id, filepath)
    return editor_session


@router.post(
    "/editor-session/{editor-session-id}",
    response_model=GitCommandResult,
    status_code=status.HTTP_200_OK
)
async def end_editor_session(
    game_id: GameIdType,
    editor_session_id: GitEditorSessionIdType
) -> GitCommandResult:
    result: GitCommandResult = GitController.end_editor_session(game_id, editor_session_id)
    return result


