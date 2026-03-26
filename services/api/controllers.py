from git_orchestrator.git_orchestrator_interface import (
    GitOrchestratorInterface,
    ForbiddenPathException,
)
from filesystem import Filesystem
import models
import subprocess
import re
from copy import deepcopy
import uuid
import os
import json
import shutil
from typing import List, Union, Optional, Dict, Any


class GameController:

    META_PROTOTYPE: Dict[str, Any] = {"id": None, "player_name": None}

    @classmethod
    def get_games(cls) -> List[models.IdType]:
        return os.listdir(Filesystem.GAMES_PATH)

    @classmethod
    def new_game(cls, player: models.Player) -> models.Game:
        game_id = str(uuid.uuid1())
        game_directory = Filesystem.get_game_path(game_id, must_exist=False)
        game_directory.mkdir()

        meta_filename = Filesystem.get_game_meta_path(game_id, must_exist=False)
        metadata = deepcopy(cls.META_PROTOTYPE)
        metadata["id"] = game_id
        metadata["player_name"] = player.name
        with open(meta_filename, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)

        game_levels_directory = Filesystem.get_game_levels_path(
            game_id, must_exist=False
        )
        game_levels_directory.mkdir()

        level_ids = os.listdir(Filesystem.LEVELS_PATH)
        for level_id in level_ids:
            LevelController.reset_level(game_id, level_id)

        game = models.Game(id=game_id, player=player)
        return game

    @classmethod
    def get_game(cls, game_id: models.IdType) -> models.Game:
        meta_filename = Filesystem.get_game_meta_path(game_id)
        with open(meta_filename, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        game = models.Game(
            id=metadata["id"], player=models.Player(name=metadata["player_name"])
        )
        return game

    @classmethod
    def delete_game(cls, game_id: models.IdType) -> None:
        game_directory = Filesystem.get_game_path(game_id)
        shutil.rmtree(game_directory)


class LevelController:

    META_PROTOTYPE: Dict[str, Any] = {"started": False, "solved": False}

    @classmethod
    def get_level_graph(cls, game_id: models.IdType) -> models.LevelGraph:
        level_nodes = {node.id: node for node in cls.get_levels(game_id)}

        with open(Filesystem.LEVEL_GRAPH_PATH, "r", encoding="utf-8") as f:
            graph_id_data = json.load(f)

        start_levels = [
            level_nodes[level_id] for level_id in graph_id_data["start_levels"]
        ]
        edges = {
            source_id: [
                level_nodes[destination_id] for destination_id in destination_ids
            ]
            for source_id, destination_ids in graph_id_data["edges"].items()
        }

        level_graph = models.LevelGraph(
            start_levels=start_levels, edges=edges  # type: ignore
        )

        return level_graph

    @classmethod
    def get_levels(cls, game_id: models.IdType) -> List[models.LevelNode]:
        levels_directory = Filesystem.get_game_levels_path(game_id)
        level_ids = os.listdir(levels_directory)

        level_nodes = []

        for level_id in level_ids:
            level_metadata_filename = Filesystem.get_level_meta_path(level_id)
            with open(level_metadata_filename, "r", encoding="utf-8") as f:
                level_metadata = json.load(f)

            game_level_metadata_filename = Filesystem.get_game_level_meta_path(
                game_id, level_id
            )
            with open(game_level_metadata_filename, "r", encoding="utf-8") as f:
                game_level_metadata = json.load(f)

            level_node = models.LevelNode(
                id=level_id,
                name=level_metadata["name"],
                started=game_level_metadata["started"],
                solved=game_level_metadata["solved"],
            )

            level_nodes.append(level_node)

        return level_nodes

    @classmethod
    def get_level(cls, game_id: models.IdType, level_id: models.IdType) -> models.Level:
        level_metadata_filename = Filesystem.get_level_meta_path(level_id)
        with open(level_metadata_filename, "r", encoding="utf-8") as f:
            level_metadata = json.load(f)

        game_level_metadata_filename = Filesystem.get_game_level_meta_path(
            game_id, level_id
        )
        with open(game_level_metadata_filename, "r", encoding="utf-8") as f:
            game_level_metadata = json.load(f)

        level_node = models.LevelNode(
            id=level_id,
            name=level_metadata["name"],
            started=game_level_metadata["started"],
            solved=game_level_metadata["solved"],
        )

        files = []
        repo_directory = Filesystem.get_game_level_repo_path(game_id, level_id)
        for basename in os.listdir(repo_directory):
            if basename.startswith("."):
                continue
            filename = Filesystem.get_path([repo_directory, basename])
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()
            file = models.File(filename=filename, content=content)
            files.append(file)

        map_filename = Filesystem.get_level_map_path(level_id)
        with open(map_filename, "r", encoding="utf-8") as f:
            map_string = f.read().strip()

        map_ = models.Map.parse(map_string, level_id)

        text_filename = Filesystem.get_level_text_path(level_id)
        with open(text_filename, "r", encoding="utf-8") as f:
            text_data = json.load(f)

        level = models.Level(
            id=level_id,
            files=files,
            map=map_,
            clues=text_data["clues"],
            intro=text_data["intro"],
            outro=text_data["outro"],
            level_node=level_node,
        )

        return level

    @classmethod
    def reset_level(
        cls, game_id: models.IdType, level_id: models.IdType
    ) -> models.Level:
        game_meta_filename = Filesystem.get_game_meta_path(game_id, must_exist=False)
        with open(game_meta_filename, "r", encoding="utf-8") as f:
            game_metadata = json.load(f)
        player_name = game_metadata["player_name"]

        game_level_directory = Filesystem.get_game_level_path(
            game_id, level_id, must_exist=False
        )
        if game_level_directory.exists():
            shutil.rmtree(game_level_directory)
        game_level_directory.mkdir()

        level_meta_filename = Filesystem.get_game_level_meta_path(
            game_id, level_id, must_exist=False
        )
        level_metadata = deepcopy(LevelController.META_PROTOTYPE)
        level_metadata["started"] = False
        level_metadata["solved"] = False
        with open(level_meta_filename, "w", encoding="utf-8") as f:
            json.dump(level_metadata, f, indent=4)

        game_level_repo_directory = Filesystem.get_game_level_repo_path(
            game_id, level_id, must_exist=False
        )
        game_level_repo_directory.mkdir()

        init_git_command_args = [
            ["init"],
            ["config", "--local", "user.name", player_name],
            ["config", "--local", "user.email", f"{player_name}@game.com"],
        ]

        for args in init_git_command_args:
            GitController.run_git_command_directly(game_id, level_id, args)

        init_filename = Filesystem.get_level_init_path(level_id)
        with open(init_filename, "r", encoding="utf-8") as f:
            init_commands = f.readlines()

        for command in init_commands:
            command = command.strip()
            # replace multiple consecitive whitespaces with a single space
            command = re.sub(r"\s{2,}", " ", command)
            # split by whitespaces but let strings inside quotes intact
            splits = re.findall(
                r"""(?:"[^"\\]*(?:\\.[^"\\]*)*"|'[^'\\]*(?:\\.[^'\\]*)*'|\S+)""",
                command,
            )
            cmd, *args = splits

            match cmd:
                case "git":
                    GitController.run_git_command_directly(game_id, level_id, args)

                case "write":
                    assert len(args) == 2
                    source, destination = args
                    source_filename = Filesystem.get_level_file_path(level_id, source)
                    destination_filename = Filesystem.get_game_level_repo_file(
                        game_id, level_id, destination, must_exist=False
                    )
                    with open(source_filename, "r", encoding="utf-8") as f:
                        content = f.read()
                    with open(destination_filename, "w", encoding="utf-8") as f:
                        f.write(content)

                case "remove":
                    assert len(args) == 1
                    basename = args[0]
                    filename = Filesystem.get_game_level_repo_file(
                        game_id, level_id, basename
                    )
                    os.remove(filename)

                case "create":
                    assert len(args) == 1
                    basename = args[0]
                    filename = Filesystem.get_game_level_repo_file(
                        game_id, level_id, basename, must_exist=False
                    )
                    with open(filename, "w", encoding="utf-8"):
                        pass

                case "#":  # comment
                    pass

                case _:
                    raise ValueError()

        return cls.get_level(game_id, level_id)

    @classmethod
    def set_started(cls, game_id: models.IdType, level_id: models.IdType) -> None:
        meta_filename = Filesystem.get_game_level_meta_path(game_id, level_id)
        with open(meta_filename, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        metadata["started"] = True
        with open(meta_filename, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)

    @classmethod
    def set_solved(cls, game_id: models.IdType, level_id: models.IdType) -> None:
        meta_filename = Filesystem.get_game_level_meta_path(game_id, level_id)
        with open(meta_filename, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        metadata["solved"] = True
        with open(meta_filename, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)


class FileController:

    @classmethod
    def get_files(cls, game_id: models.IdType, level_id: models.IdType) -> List[str]:
        repo_path = Filesystem.get_game_level_repo_path(game_id, level_id)
        return [fn for fn in os.listdir(repo_path) if not fn.startswith(".")]

    @classmethod
    def get_file(
        cls, game_id: models.IdType, level_id: models.IdType, filename: str
    ) -> models.File:
        file_path = Filesystem.get_game_level_repo_file(game_id, level_id, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        file = models.File(filename=file_path, content=content)
        return file

    @classmethod
    def put_file(
        cls,
        game_id: models.IdType,
        level_id: models.IdType,
        filename: str,
        file: models.File,
    ) -> None:
        file_path = Filesystem.get_game_level_repo_file(game_id, level_id, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file.content)


class GitController:

    @classmethod
    def _get_git_interface(
        cls, game_id: models.IdType, level_id: models.IdType, id_: Optional[str] = None
    ) -> GitOrchestratorInterface:
        git_session_id = id_ or str(uuid.uuid1())
        base_directory = Filesystem.get_game_level_repo_path(game_id, level_id)

        interface = GitOrchestratorInterface(git_session_id, base_directory)

        return interface

    @classmethod
    def run_git_command(
        cls,
        game_id: models.IdType,
        level_id: models.IdType,
        git_command: models.GitCommand,
    ) -> Union[models.GitResult, models.EditorRequest, None]:
        interface = cls._get_git_interface(game_id, level_id)

        try:
            result = interface.run_git_command(git_command)
        except ForbiddenPathException:
            raise PermissionError()

        return result

    @classmethod
    def run_git_command_directly(
        cls, game_id: models.IdType, level_id: models.IdType, argv: List[str]
    ) -> bool:
        cwd = Filesystem.get_game_level_repo_path(game_id, level_id)
        git_process = subprocess.Popen(args=["git"] + argv, cwd=cwd)
        returncode = git_process.wait()
        return returncode == 0

    @classmethod
    def handle_editor_response(
        cls,
        game_id: models.IdType,
        level_id: models.IdType,
        editor_response: models.EditorResponse,
    ) -> Union[models.GitResult, None]:
        interface = cls._get_git_interface(game_id, level_id, editor_response.id)
        return interface.send_editor_response(editor_response)
