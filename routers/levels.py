from fastapi import APIRouter

router = APIRouter(prefix="/levels", tags=["levels"])

@router.get("/")
async def get_levels():
    return {"message": "List of levels"}

@router.get("/{level_id}")
async def get_level(level_id: int):
    return {"message": f"Details for level {level_id}"}
