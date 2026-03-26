from tests.conftest import make_request


def test_get_game_404(setup_and_teardown, invalid_game_id):
    status, data = make_request("get", f"/games/{invalid_game_id}")

    assert status == 404
    assert data is None


def test_delete_game_404(setup_and_teardown, invalid_game_id):
    status, data = make_request("delete", f"/games/{invalid_game_id}")

    assert status == 404
    assert data is None


def test_get_levels_404(setup_and_teardown, invalid_game_id):
    status, data = make_request("get", f"/games/{invalid_game_id}/levels")

    assert status == 404
    assert data is None


def test_get_level_404(
    setup_and_teardown, game_id, level_id, invalid_game_id, invalid_level_id
):
    status, data = make_request("get", f"/games/{invalid_game_id}/levels/{level_id}")

    assert status == 404
    assert data is None

    status, data = make_request("get", f"/games/{game_id}/levels/{invalid_level_id}")

    assert status == 404
    assert data is None


def test_reset_level_404(
    setup_and_teardown, game_id, level_id, invalid_game_id, invalid_level_id
):
    status, data = make_request(
        "put", f"/games/{invalid_game_id}/levels/{level_id}/reset"
    )

    assert status == 404
    assert data is None

    status, data = make_request(
        "put", f"/games/{game_id}/levels/{invalid_level_id}/reset"
    )

    assert status == 404
    assert data is None


def test_set_started_404(
    setup_and_teardown, game_id, level_id, invalid_game_id, invalid_level_id
):
    status, data = make_request(
        "put", f"/games/{invalid_game_id}/levels/{level_id}/started"
    )

    assert status == 404
    assert data is None

    status, data = make_request(
        "put", f"/games/{game_id}/levels/{invalid_level_id}/started"
    )

    assert status == 404
    assert data is None


def test_set_solved_404(
    setup_and_teardown, game_id, level_id, invalid_game_id, invalid_level_id
):
    status, data = make_request(
        "put", f"/games/{invalid_game_id}/levels/{level_id}/solved"
    )

    assert status == 404
    assert data is None

    status, data = make_request(
        "put", f"/games/{game_id}/levels/{invalid_level_id}/solved"
    )

    assert status == 404
    assert data is None


def test_get_files_404(
    setup_and_teardown, game_id, level_id, invalid_game_id, invalid_level_id
):
    status, data = make_request(
        "get", f"/games/{invalid_game_id}/levels/{level_id}/files"
    )

    assert status == 404
    assert data is None

    status, data = make_request(
        "get", f"/games/{game_id}/levels/{invalid_level_id}/files"
    )

    assert status == 404
    assert data is None


def test_get_file_404(
    setup_and_teardown,
    game_id,
    level_id,
    filename,
    invalid_game_id,
    invalid_level_id,
    invalid_filename,
):
    status, data = make_request(
        "get", f"/games/{invalid_game_id}/levels/{level_id}/files/{filename}"
    )

    assert status == 404
    assert data is None

    status, data = make_request(
        "get", f"/games/{game_id}/levels/{invalid_level_id}/files/{filename}"
    )

    assert status == 404
    assert data is None

    status, data = make_request(
        "get", f"/games/{game_id}/levels/{level_id}/files/{invalid_filename}"
    )

    assert status == 404
    assert data is None


def test_put_file_404(
    setup_and_teardown,
    game_id,
    level_id,
    filename,
    invalid_game_id,
    invalid_level_id,
    invalid_filename,
):
    payload = {"type_": "File", "filename": filename, "content": "content changed"}

    status, data = make_request(
        "put", f"/games/{invalid_game_id}/levels/{level_id}/files/{filename}", payload
    )

    assert status == 404
    assert data is None

    status, data = make_request(
        "put", f"/games/{game_id}/levels/{invalid_level_id}/files/{filename}", payload
    )

    assert status == 404
    assert data is None

    status, data = make_request(
        "put", f"/games/{game_id}/levels/{level_id}/files/{invalid_filename}", payload
    )

    assert status == 404
    assert data is None


def test_post_git_command_404(
    setup_and_teardown, game_id, level_id, invalid_game_id, invalid_level_id
):
    payload = {"type_": "GitCommand", "argv": ["status"]}

    status, data = make_request(
        "post", f"/games/{invalid_game_id}/levels/{level_id}/git-command", payload
    )

    assert status == 404
    assert data is None

    status, data = make_request(
        "post", f"/games/{game_id}/levels/{invalid_level_id}/git-command", payload
    )

    assert status == 404
    assert data is None


def test_post_git_command_403(setup_and_teardown, game_id, level_id):
    payload = {"type_": "GitCommand", "argv": ["add", "/etc"]}

    status, data = make_request(
        "post", f"/games/{game_id}/levels/{level_id}/git-command", payload
    )

    assert status == 403
    assert data is None


def test_post_editor_response_404(
    setup_and_teardown, game_id, level_id, invalid_game_id, invalid_level_id
):
    payload = {
        "type_": "EditorResponse",
        "id": "__DUMMY_ID__",
        "file": {
            "type_": "File",
            "filename": "__DUMMY_FILENAME__",
            "content": "__DUMMY_CONTENT",
        },
        "abort": False,
    }

    status, data = make_request(
        "post", f"/games/{invalid_game_id}/levels/{level_id}/editor-response", payload
    )

    assert status == 404
    assert data is None

    status, data = make_request(
        "post", f"/games/{game_id}/levels/{invalid_level_id}/editor-response", payload
    )

    assert status == 404
    assert data is None
