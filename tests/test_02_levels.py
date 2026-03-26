from tests.conftest import (
    make_request,
    ModelAssertions,
    assert_dict_value,
    assert_dict_type,
)


def test_get_level_graph(setup_and_teardown, game_id):
    status, data = make_request("get", f"/games/{game_id}/level-graph")

    assert status == 200
    assert isinstance(data, dict)
    ModelAssertions.assert_level_graph(data)


def test_get_levels(setup_and_teardown, game_id):
    status, data = make_request("get", f"/games/{game_id}/levels")

    assert status == 200
    assert isinstance(data, list)
    assert len(data) > 0
    for item in data:
        assert isinstance(item, dict)
        ModelAssertions.assert_level_node(item)


def test_get_level(setup_and_teardown, game_id, level_id):
    status, data = make_request("get", f"/games/{game_id}/levels/{level_id}")

    assert status == 200
    assert isinstance(data, dict)
    ModelAssertions.assert_level(data)


def test_set_level_started(setup_and_teardown, game_id, level_id):
    _, level = make_request("get", f"/games/{game_id}/levels/{level_id}")
    assert isinstance(level, dict)
    assert_dict_type(level, "level_node", dict)
    assert_dict_value(level["level_node"], "started", False, bool)

    status, data = make_request("put", f"/games/{game_id}/levels/{level_id}/started")

    assert status == 200
    assert data is None

    _, level = make_request("get", f"/games/{game_id}/levels/{level_id}")
    assert isinstance(level, dict)
    assert_dict_type(level, "level_node", dict)
    assert_dict_value(level["level_node"], "started", True, bool)


def test_set_level_solved(setup_and_teardown, game_id, level_id):
    _, level = make_request("get", f"/games/{game_id}/levels/{level_id}")
    assert isinstance(level, dict)
    assert_dict_type(level, "level_node", dict)
    assert_dict_value(level["level_node"], "solved", False, bool)

    status, data = make_request("put", f"/games/{game_id}/levels/{level_id}/solved")

    assert status == 200
    assert data is None

    _, level = make_request("get", f"/games/{game_id}/levels/{level_id}")
    assert isinstance(level, dict)
    assert_dict_type(level, "level_node", dict)
    assert_dict_value(level["level_node"], "solved", True, bool)


def test_reset_level(setup_and_teardown, game_id, level_id):
    _, _ = make_request("put", f"/games/{game_id}/levels/{level_id}/started")

    status, data = make_request("put", f"/games/{game_id}/levels/{level_id}/reset")

    assert status == 200
    assert isinstance(data, dict)
    ModelAssertions.assert_level(data)
    assert_dict_value(data["level_node"], "solved", False, bool)
