from fastapi import APIRouter
from typing import List
from models.game import Game, GameProgress, GameLevelProgress, GameIdType
from models.level import LevelIdType
from controllers import GameController


router = APIRouter(prefix="/games", tags=["games"])


@router.get("/", response_model=List[Game])
async def get_games() -> List[Game]:
    return GameController.get_games()


@router.get("/{game_id}", response_model=Game)
async def get_game(game_id: GameIdType) -> Game:
    return GameController.get_game(game_id) 


@router.delete("/{game_id}")
async def delete_game(game_id: GameIdType):
    GameController.delete_game(game_id)


@router.post("/new", response_model=Game)
async def create_new_game() -> Game:
    return GameController.create_new_game()


@router.post("/{game_id}/run-tests/{level_id}", response_model=GameLevelProgress)
async def run_tests(game_id: GameIdType, level_id: LevelIdType) -> GameLevelProgress:
    return GameController.run_tests(game_id, level_id)


@router.get("/{game_id}/progress", response_model=GameProgress)
async def get_game_progress(game_id: GameIdType) -> GameProgress:
    return GameController.get_game_progress(game_id)
