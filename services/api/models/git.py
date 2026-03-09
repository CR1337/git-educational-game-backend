from pydantic import BaseModel
from filesystem import File
from typing import List, Union
from enum import Enum


GitEditorSessionIdType = str


class GitResultType(str, Enum):
    DONE = "done"
    EDITOR_OPENED= "editor_opened"


class GitEditorSession(BaseModel):
    git_editor_session_id: GitEditorSessionIdType
    file: File


class GitCommand(BaseModel):
    arguments: List[str]


class GitCommandDoneResult(BaseModel):
    command: GitCommand
    stdout: str
    stderr: str
    status_code: int


class GitCommandEditorOpenedResult(BaseModel):
    git_editor_session: GitEditorSession


class GitCommandResult(BaseModel):
    git_result_type: GitResultType
    git_result: Union[GitCommandDoneResult, GitCommandEditorOpenedResult]
    