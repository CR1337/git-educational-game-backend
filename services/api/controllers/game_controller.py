import os
from pathlib import Path
from typing import List
from models.game import Game, GameProgress, GameLevelProgress, GameIdType
from models.level import LevelIdType
from controllers.redis_controller import RedisController
from controllers.filesystem_controller import FileController


class GameController:

    GAMES_DIRECTORY: str = os.path.join(
        "game_data",
        "games"
    )

    @classmethod
    def get_games(cls) -> List[Game]:
        if not RedisController.exists("games"):
            RedisController.set_json("games", [])

        game_dict_list = RedisController.get_json("games")

        return [Game(**game_dict) for game_dict in game_dict_list]  # type: ignore

    @classmethod
    def get_game(cls, game_id: GameIdType) -> Game:
        key = f"game_id:{game_id}:game"
        if not RedisController.exists(key):
            raise KeyError()
        return Game(**RedisController.get_json(key))  # type: ignore

    @classmethod
    def delete_game(cls, game_id: GameIdType):
        key = f"game_id:{game_id}:game"
        if not RedisController.exists(key):
            raise KeyError()
        game = Game(**RedisController.get_json(key))  # type: ignore
        FileController.delete_game_files(game.game_id)

    @classmethod
    def create_new_game(cls) -> Game:
        ...

    @classmethod
    def run_tests(cls, game_id: GameIdType, level_id: LevelIdType) -> GameLevelProgress:
        ...

    @classmethod
    def get_game_progress(cls, game_id: GameIdType) -> GameProgress:
        ...
