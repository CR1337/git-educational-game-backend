from models import Game


class GameController:

    @classmethod
    def get_game(cls, game_id: str) -> Game:
        ...  # TODO