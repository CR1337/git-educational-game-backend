import os
import json
from typing import Any, Dict, List
from models.level import Level, LevelGraph, LevelNode, LevelIdType


class LevelController:

    LEVEL_DIRECTORY: str = os.path.join(
        "game_data",
        "levels"
    )

    LEVEL_GRAPH_FILENAME: str = os.path.join(
        LEVEL_DIRECTORY,
        "level_graph.json"
    )

    @classmethod
    def get_level_graph(cls) -> LevelGraph:
        with open(cls.LEVEL_GRAPH_FILENAME, 'r', encoding='utf-8') as file:
            level_graph_data: Dict[str, Any] = json.load(file)

        start_level_ids: List[LevelIdType] = level_graph_data["start_level_ids"]
        level_nodes: List[LevelNode] = [
            LevelNode(
                level_id=level_node["level_id"],
                successor_level_ids=level_node["successor_level_ids"]
            )
            for level_node in level_graph_data["level_nodes"] 
        ]

        return LevelGraph(
            start_level_ids=start_level_ids,
            level_nodes=level_nodes
        )

    @classmethod
    def get_level(cls, level_id: LevelIdType) -> Level:
        level_filename: str = os.path.join(
            cls.LEVEL_DIRECTORY,
            f"{level_id}.json"
        )

        with open(level_filename, 'r', encoding='utf-8') as file:
            level_data: Dict[str, Any] = json.load(file)

        level = Level(
            level_id=level_id,
            directory=level_data["directory"]
            # TODO: add more level data
        )

        return level