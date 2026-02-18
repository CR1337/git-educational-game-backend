from fastapi import APIRouter

router = APIRouter(prefix="/games/{game_id}/editor", tags=["editor"])

@router.get("/requests")
async def get_editor_requests(game_id: int):
    return {"message": f"Editor requests for game {game_id}"}

@router.post("/response")
async def post_editor_response(game_id: int):
    return {"message": f"Editor response posted for game {game_id}"}
