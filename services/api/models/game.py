from pydantic import BaseModel
from typing import Dict
from level import LevelIdType


GameIdType = int


class Game(BaseModel):
    game_id: GameIdType


class GameLevelProgress(BaseModel):
    level_id: LevelIdType
    started: bool
    solved: bool


class GameProgress(BaseModel):
    progress: Dict[LevelIdType, GameLevelProgress]