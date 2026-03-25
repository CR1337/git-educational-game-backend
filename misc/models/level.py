from pydantic import BaseModel
from pathlib import Path
from typing import List


LevelIdType = int


class Level(BaseModel):
    level_id: LevelIdType
    directory: Path
    # TODO: add more level data


class LevelNode(BaseModel):
    level_id: Level
    successor_level_ids: List[LevelIdType]


class LevelGraph(BaseModel):
    start_level_ids: List[LevelIdType]
    level_nodes: List[LevelNode]
    