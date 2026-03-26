import controllers


def startup() -> None:
    game_ids = controllers.GameController.get_games()
    for game_id in game_ids:
        controllers.GameController.delete_game(game_id)


def shutdown() -> None:
    pass
