from tests.conftest import make_request, ModelAssertions, assert_dict_value


def test_post_git_command(setup_and_teardown, game_id, level_id):
    payload = {"type_": "GitCommand", "argv": ["status"]}
    status, data = make_request(
        "post", f"/games/{game_id}/levels/{level_id}/git-command", payload
    )

    assert status == 202
    assert isinstance(data, dict)
    ModelAssertions.assert_git_result(data)
    assert_dict_value(data, "returncode", 0, int)
    assert "On branch" in data["stdout"]
    assert_dict_value(data, "stderr", "", str)


def test_post_editor_response(setup_and_teardown, game_id, level_id, filename):
    payload = {"type_": "File", "filename": filename, "content": "content changed"}
    _, _ = make_request(
        "put", f"/games/{game_id}/levels/{level_id}/files/{filename}", payload
    )

    payload = {"type_": "GitCommand", "argv": ["add", "."]}
    _, _ = make_request(
        "post", f"/games/{game_id}/levels/{level_id}/git-command", payload
    )

    payload = {"type_": "GitCommand", "argv": ["commit"]}
    status, data = make_request(
        "post", f"/games/{game_id}/levels/{level_id}/git-command", payload
    )

    assert status == 202
    assert isinstance(data, dict)
    ModelAssertions.assert_editor_request(data)

    assert data["file"]["filename"].endswith(".git/COMMIT_EDITMSG")
    assert (
        "Please enter the commit message for your changes." in data["file"]["content"]
    )

    new_content = "new_content"
    payload = {
        "type_": "EditorResponse",
        "id": data["id"],
        "file": {
            "type_": "File",
            "filename": data["file"]["filename"],
            "content": new_content,
        },
        "abort": False,
    }
    status, data = make_request(
        "post", f"/games/{game_id}/levels/{level_id}/editor-response", payload
    )

    assert status == 202
    assert isinstance(data, dict)
    ModelAssertions.assert_git_result(data)
    assert_dict_value(data, "returncode", 0, int)
