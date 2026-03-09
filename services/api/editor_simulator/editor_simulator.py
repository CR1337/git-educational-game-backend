#!/usr/bin/env python3

import sys
import pathlib
import requests
from models.filesystem import Filepath, File, FileContent
from models.git import GitEditorSessionIdType, GitEditorSession
from uuid import uuid4
from ipc.ipc import JsonIpcQueue


HOST: str = "localhost"
PORT: int = 8000


def main():
    # Receive the filename from git
    filename: str = sys.argv[-1]

    # open the file and KEEP(!) it open
    f = open(filename, 'r+', encoding='utf-8')

    # Read the content
    content: str = f.read()

    # Create a unique editor session id
    git_editor_session_id: GitEditorSessionIdType = f"{filename}-{uuid4()}"

    # Create a pydantic model editor session
    filepath = Filepath(filepath=pathlib.Path(filename))
    file_content = FileContent(content=content)
    file = File(filepath=filepath, content=file_content)
    git_editor_session = GitEditorSession(
        git_editor_session_id=git_editor_session_id,
        file=file
    )

    # Post the editor back to fastapi
    try:
        response = requests.post(
            url=f"http://{HOST}:{PORT}",
            json=git_editor_session.model_dump_json()
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        ...  # TODO

    # Wait for fastapi to receive the new content
    queue = JsonIpcQueue(git_editor_session_id)
    data = queue.receive()

    # Overwrite the old with the new content
    modified_content: FileContent = FileContent(**data)
    f.seek(0)
    f.write(modified_content.content)
    f.truncate()

    # NOW close the file
    f.close()


if __name__ == "__main__":
    main()
