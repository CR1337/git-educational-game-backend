import re
import json
import pytest
import requests
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List, Union, Type


HOST: str = "127.0.0.1"
PORT: int = 8080

GAMES_BACKUP_PATH: Path = Path("games_backup")
GAMES_PATH: Path = Path("volumes", "game_data", "games")

UUID1_PATTERN: re.Pattern = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-1[0-9a-f]{3}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)


def _backup_games() -> None:
    if GAMES_BACKUP_PATH.exists():
        shutil.rmtree(GAMES_BACKUP_PATH)
    shutil.copytree(GAMES_PATH, GAMES_BACKUP_PATH)
    shutil.rmtree(GAMES_PATH)
    GAMES_PATH.mkdir()


def _restore_games():
    shutil.rmtree(GAMES_PATH)
    shutil.copytree(GAMES_BACKUP_PATH, GAMES_PATH)
    shutil.rmtree(GAMES_BACKUP_PATH)


def make_request(
    method: str, url: str, payload: Optional[Union[Dict[str, Any], List[Any]]] = None
) -> Tuple[int, Optional[Dict[str, Any]]]:
    func = {
        "get": requests.get,
        "post": requests.post,
        "put": requests.put,
        "delete": requests.delete,
    }[method]

    url = f"http://{HOST}:{PORT}/api{url}"
    response = func(url=url, json=payload)

    status = response.status_code
    try:
        data = response.json()
    except json.JSONDecodeError:
        data = None

    return status, data


def _is_uuid1(string: str) -> bool:
    return bool(UUID1_PATTERN.fullmatch(string))


def assert_dict_value(
    dictionary: Dict[str, Any],
    key: str,
    expected_value: Any,
    type_: Type,
    *,
    can_be_none: bool = False,
) -> None:
    assert key in dictionary
    if dictionary[key] is None and can_be_none:
        return
    assert isinstance(dictionary[key], type_)
    assert dictionary[key] == expected_value


def assert_dict_uuid1(
    dictionary: Dict[str, Any], key: str, *, can_be_none: bool = False
) -> None:
    assert key in dictionary
    if dictionary[key] is None and can_be_none:
        return
    assert isinstance(dictionary[key], str)
    assert _is_uuid1(dictionary[key])


def assert_dict_type(
    dictionary: Dict[str, Any], key: str, type_: Type, *, can_be_none: bool = False
) -> None:
    assert key in dictionary
    if dictionary[key] is None and can_be_none:
        return
    assert isinstance(dictionary[key], type_)


class ModelAssertions:

    @classmethod
    def assert_message(cls, data: Dict[str, Any]) -> None:
        assert_dict_value(data, "type_", "Message", str)
        assert_dict_type(data, "message", str)

    @classmethod
    def assert_file(cls, data: Dict[str, Any]) -> None:
        assert_dict_value(data, "type_", "File", str)
        assert_dict_type(data, "filename", str)
        assert_dict_type(data, "content", str)

    @classmethod
    def assert_git_command(cls, data: Dict[str, Any]) -> None:
        assert_dict_value(data, "type_", "GitCommand", str)
        assert_dict_type(data, "argv", list)
        for arg in data["argv"]:
            assert isinstance(arg, str)

    @classmethod
    def assert_git_result(cls, data: Dict[str, Any]) -> None:
        assert_dict_value(data, "type_", "GitResult", str)
        assert_dict_uuid1(data, "id")
        assert_dict_type(data, "returncode", int)
        assert_dict_type(data, "stdout", str)
        assert_dict_type(data, "stderr", str)

    @classmethod
    def assert_editor_request(cls, data: Dict[str, Any]) -> None:
        assert_dict_value(data, "type_", "EditorRequest", str)
        assert_dict_uuid1(data, "id")
        assert_dict_type(data, "file", dict)
        cls.assert_file(data["file"])
        assert_dict_type(data, "stdout", str)
        assert_dict_type(data, "stderr", str)

    @classmethod
    def assert_editor_response(cls, data: Dict[str, Any]) -> None:
        assert_dict_value(data, "type_", "EditorResponse", str)
        assert_dict_uuid1(data, "id")
        assert_dict_type(data, "file", dict)
        cls.assert_file(data["file"])
        assert_dict_type(data, "abort", bool)

    @classmethod
    def assert_map(cls, data: Dict[str, Any]) -> None:
        assert_dict_value(data, "type_", "Map", str)
        assert_dict_type(data, "id", str)
        assert_dict_type(data, "width", int)
        assert_dict_type(data, "height", int)
        assert_dict_type(data, "content", str)
        assert len(data["content"].splitlines()) == data["height"]
        assert all(len(line) == data["width"] for line in data["content"].splitlines())
        assert_dict_type(data, "patches", list)
        for patch in data["patches"]:
            assert isinstance(patch, list)
            assert isinstance(patch[0], int)
            assert isinstance(patch[1], int)
            assert isinstance(patch[2], str)
            assert 0 <= patch[0] < data["width"]
            assert 0 <= patch[1] < data["height"]

    @classmethod
    def assert_level_node(cls, data: Dict[str, Any]) -> None:
        assert_dict_value(data, "type_", "LevelNode", str)
        assert_dict_type(data, "id", str)
        assert_dict_type(data, "name", str)
        assert_dict_type(data, "started", bool)
        assert_dict_type(data, "solved", bool)

    @classmethod
    def assert_level(cls, data: Dict[str, Any]) -> None:
        assert_dict_value(data, "type_", "Level", str)
        assert_dict_type(data, "id", str)
        assert_dict_type(data, "files", list)
        assert len(data["files"]) > 0
        for file in data["files"]:
            assert isinstance(file, dict)
            cls.assert_file(file)
        assert_dict_type(data, "map", dict)
        cls.assert_map(data["map"])
        assert_dict_type(data, "clues", list)
        assert all(isinstance(clue, str) for clue in data["clues"])
        assert_dict_type(data, "intro", str)
        assert_dict_type(data, "outro", str)
        assert_dict_type(data, "level_node", dict)
        cls.assert_level_node(data["level_node"])

    @classmethod
    def assert_level_graph(cls, data: Dict[str, Any]) -> None:
        assert_dict_value(data, "type_", "LevelGraph", str)
        assert_dict_type(data, "start_levels", list)
        assert len(data["start_levels"]) > 0
        for start_level in data["start_levels"]:
            assert isinstance(start_level, dict)
            cls.assert_level_node(start_level)
        assert_dict_type(data, "edges", dict)
        assert all(isinstance(key, str) for key in data["edges"].keys())
        for edge in data["edges"].values():
            assert isinstance(edge, dict)
            cls.assert_level_node(edge)

    @classmethod
    def assert_player(cls, data: Dict[str, Any]) -> None:
        assert_dict_value(data, "type_", "Player", str)
        assert_dict_type(data, "name", str)

    @classmethod
    def assert_game(cls, data: Dict[str, Any]) -> None:
        assert_dict_value(data, "type_", "Game", str)
        assert_dict_uuid1(data, "id")
        assert_dict_type(data, "player", dict)
        cls.assert_player(data["player"])


@pytest.fixture
def setup_and_teardown():
    _backup_games()
    yield
    _restore_games()


@pytest.fixture
def game_id() -> str:
    payload = {"type_": "Player", "name": "player"}
    _, data = make_request("post", "/games/new", payload)
    assert data
    game_id = data["id"]
    return game_id


@pytest.fixture
def level_id() -> str:
    return "1"


@pytest.fixture
def filename() -> str:
    return "bot0.bot"


@pytest.fixture
def invalid_game_id() -> str:
    return "__INVALID_GAME_ID__"


@pytest.fixture
def invalid_level_id() -> str:
    return "__INVALID_LEVEL_ID__"


@pytest.fixture
def invalid_filename() -> str:
    return "__INVALID_FILENAME__"
