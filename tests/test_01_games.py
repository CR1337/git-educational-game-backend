from tests.conftest import make_request, ModelAssertions, assert_dict_value


def test_new_game(setup_and_teardown):
    player_name = "player"
    payload = {"type_": "Player", "name": player_name}
    status, data = make_request("post", "/games/new", payload)

    assert status == 201
    assert isinstance(data, dict)
    ModelAssertions.assert_game(data)
    assert_dict_value(data["player"], "name", player_name, str)


def test_get_games(setup_and_teardown, game_id):
    status, data = make_request("get", "/games")

    assert status == 200
    assert isinstance(data, list)
    assert len(data) == 1
    assert all(isinstance(item, str) for item in data)
    assert data[0] == game_id  # type: ignore


def test_get_game(setup_and_teardown, game_id):
    status, data = make_request("get", f"/games/{game_id}")

    assert status == 200
    assert isinstance(data, dict)
    ModelAssertions.assert_game(data)


def test_delete_game(setup_and_teardown, game_id):
    status, data = make_request("delete", f"/games/{game_id}")

    assert status == 204
    assert data is None
