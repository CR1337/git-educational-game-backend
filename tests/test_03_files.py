from tests.conftest import make_request, ModelAssertions, assert_dict_value


def test_get_files(setup_and_teardown, game_id, level_id, filename):
    status, data = make_request("get", f"/games/{game_id}/levels/{level_id}/files")

    assert status == 200
    assert isinstance(data, list)
    assert all(isinstance(item, str) for item in data)
    assert filename in data


def test_get_file(setup_and_teardown, game_id, level_id, filename):
    status, data = make_request("get", f"/games/{game_id}/levels/{level_id}/files/{filename}")

    assert status == 200
    assert isinstance(data, dict)
    ModelAssertions.assert_file(data)
    filepath = f"/game_data/games/{game_id}/levels/{level_id}/repo/{filename}"
    assert_dict_value(data, "filename", filepath, str)

def test_put_file(setup_and_teardown, game_id, level_id, filename):
    new_content = "wait"
    payload = {
        "type_": "File",
        "filename": filename,
        "content": new_content
    }
    status, data = make_request("put", f"/games/{game_id}/levels/{level_id}/files/{filename}", payload)

    assert status == 200
    assert data is None

    filepath = f"volumes/game_data/games/{game_id}/levels/{level_id}/repo/{filename}"
    with open(filepath, 'r', encoding="utf-8") as f:
        file_content = f.read()

    assert new_content == file_content
