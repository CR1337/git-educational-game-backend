from fastapi import APIRouter, Path, Body
from typing import Optional

from controllers import FileController, GameController


router = APIRouter(prefix="/games/{game_id}/files", tags=["files"])

# List files in a directory (root or subdirectory)
@router.get("/{filepath:path}")
async def get_files(game_id: str, filepath: Optional[str] = ""):
    game = GameController.get_game(game_id)
    filenames = FileController.get_filenames(game, filepath)
    return {
        "filenames": filenames
    }


@router.post("/{filepath:path}")
async def upload_file(game_id: str, filepath: str = Path(...), data: dict = Body(...)):
    game = GameController.get_game(game_id)
    success = FileController.create_file(game, filepath, data['content'])
    return {
        "success": success
    }


@router.get("/{filepath:path}")
async def get_file(game_id: str, filepath: str = Path(...)):
    game = GameController.get_game(game_id)
    content = FileController.get_file(game, filepath)
    return {
        "content": content
    }


@router.post("/{filepath:path}")
async def update_file(game_id: str, filepath: str = Path(...), data: dict = Body(...)):
    game = GameController.get_game(game_id)
    success = FileController.update_file(game, filepath, data['content'])
    return {
        "success": success
    }


@router.delete("/{filepath:path}")
async def delete_file(game_id: str, filepath: str = Path(...)):
    game = GameController.get_game(game_id)
    success = FileController.delete_file(game, filepath)
    return {
        "success": success
    }
