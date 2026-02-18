from fastapi import APIRouter

router = APIRouter(prefix="/games", tags=["games"])

@router.get("/")
async def get_games():
    return {"message": "List of games"}

@router.post("/")
async def create_game():
    return {"message": "Game created"}

@router.get("/{game_id}")
async def get_game(game_id: int):
    return {"message": f"Details for game {game_id}"}

@router.delete("/{game_id}")
async def delete_game(game_id: int):
    return {"message": f"Game {game_id} deleted"}

@router.get("/{game_id}/current_working_directory")
async def get_current_working_directory(game_id: int):
    return {"message": f"Current working directory for game {game_id}"}

@router.post("/{game_id}/current_working_directory")
async def set_current_working_directory(game_id: int):
    return {"message": f"Current working directory set for game {game_id}"}