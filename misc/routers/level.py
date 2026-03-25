from fastapi import APIRouter
from controllers import LevelController
from models.level import LevelGraph, Level, LevelIdType


router = APIRouter(prefix="/levels", tags=["levels"])


@router.get("/", response_model=LevelGraph)
async def get_levels() -> LevelGraph:
    return LevelController.get_level_graph()


@router.get("/{level_id}", response_model=Level)
async def get_level(level_id: LevelIdType) -> Level:
    return LevelController.get_level(level_id)
