from fastapi import APIRouter

router = APIRouter(prefix="/games/{game_id}/files", tags=["files"])

@router.get("/")
async def get_files(game_id: int):
    return {"message": f"List of files for game {game_id}"}

@router.post("/")
async def upload_file(game_id: int):
    return {"message": f"File uploaded for game {game_id}"}

@router.get("/{filename}")
async def get_file(game_id: int, filename: str):
    return {"message": f"Details for file {filename} in game {game_id}"}

@router.post("/{filename}")
async def update_file(game_id: int, filename: str):
    return {"message": f"File {filename} updated in game {game_id}"}

@router.delete("/{filename}")
async def delete_file(game_id: int, filename: str):
    return {"message": f"File {filename} deleted from game {game_id}"}
