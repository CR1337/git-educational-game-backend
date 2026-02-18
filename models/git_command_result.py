from dataclasses import dataclass


@dataclass
class GitCommandResult:
    git_command_result_id: str
    git_command_id: str
    status_code: int
    stdout: str
    stderr: str
    