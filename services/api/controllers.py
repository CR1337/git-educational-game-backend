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
import debug
from typing import List, Union, Optional, Dict, Any


class RootController:

    @classmethod
    def get_server_config(cls) -> models.ServerConfig:
        return models.ServerConfig(
            debug_mode=debug.in_debug_mode(), local=debug.is_local()
        )


class GameController:

    META_PROTOTYPE: Dict[str, Any] = {"id": None, "player_name": None}

    @classmethod
    def get_games(cls) -> List[models.IdType]:
        return [
            name
            for name in os.listdir(Filesystem.GAMES_PATH)
            if not name.startswith(".")
        ]

    @classmethod
    def new_game(cls, new_game_info: models.NewGameInfo) -> models.Game:
        game_id = str(uuid.uuid1())
        game_directory = Filesystem.get_game_path(game_id, must_exist=False)
        game_directory.mkdir()

        meta_filename = Filesystem.get_game_meta_path(game_id, must_exist=False)
        metadata = deepcopy(cls.META_PROTOTYPE)
        metadata["id"] = game_id
        metadata["player_name"] = new_game_info.player.name
        metadata["levelset_id"] = new_game_info.levelset.id
        with open(meta_filename, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)

        game_levels_directory = Filesystem.get_game_levels_path(
            game_id, must_exist=False
        )
        game_levels_directory.mkdir()

        level_ids = [
            fn
            for fn in os.listdir(Filesystem.get_levels_path(new_game_info.levelset.id))
            if not fn.endswith(".json")
        ]
        for level_id in level_ids:
            LevelController.reset_level(game_id, level_id)

        game = models.Game(
            id=game_id,
            player=new_game_info.player,
            levelset=new_game_info.levelset,
        )
        return game

    @classmethod
    def get_game(cls, game_id: models.IdType) -> models.Game:
        meta_filename = Filesystem.get_game_meta_path(game_id)
        with open(meta_filename, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        game = models.Game(
            id=metadata["id"],
            player=models.Player(name=metadata["player_name"]),
            levelset=models.Levelset(id=metadata["levelset_id"]),
        )
        return game

    @classmethod
    def delete_game(cls, game_id: models.IdType) -> None:
        game_directory = Filesystem.get_game_path(game_id)
        shutil.rmtree(game_directory)


class LevelController:

    META_PROTOTYPE: Dict[str, Any] = {"started": False, "solved": False}
    DEFAULT_LEVELSET_ID: models.IdType = "main"

    @classmethod
    def get_levelsets(cls) -> List[models.Levelset]:
        return [models.Levelset(id=d) for d in os.listdir(Filesystem.LEVELSETS_PATH)]

    @classmethod
    def get_level_graph(cls, game_id: models.IdType) -> models.LevelGraph:
        levelset_id = GameController.get_game(game_id).levelset.id
        level_nodes = {node.id: node for node in cls.get_levels(game_id)}

        with open(
            Filesystem.get_level_graph_path(levelset_id), "r", encoding="utf-8"
        ) as f:
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
        levelset_id = GameController.get_game(game_id).levelset.id
        levels_directory = Filesystem.get_game_levels_path(game_id)
        level_ids = os.listdir(levels_directory)

        level_nodes = []

        for level_id in level_ids:
            level_metadata_filename = Filesystem.get_level_meta_path(
                levelset_id, level_id
            )
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
        levelset_id = GameController.get_game(game_id).levelset.id
        level_metadata_filename = Filesystem.get_level_meta_path(levelset_id, level_id)
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

        map_filename = Filesystem.get_level_map_path(levelset_id, level_id)
        with open(map_filename, "r", encoding="utf-8") as f:
            map_string = f.read().strip()

        map_ = models.Map.parse(map_string, level_id)

        text_filename = Filesystem.get_level_text_path(levelset_id, level_id)
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
        levelset_id = GameController.get_game(game_id).levelset.id
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

        init_filename = Filesystem.get_level_init_path(levelset_id, level_id)
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
                    source_filename = Filesystem.get_level_file_path(
                        levelset_id, level_id, source
                    )
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
        return sorted([fn for fn in os.listdir(repo_path) if not fn.startswith(".")])

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
    ) -> models.GitResult:
        cwd = Filesystem.get_game_level_repo_path(game_id, level_id)
        git_process = subprocess.Popen(
            args=["git"] + argv,
            cwd=cwd,
            env={"GIT_PAGER": ""},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        returncode = git_process.wait()
        stdout, stderr = [x.decode() for x in git_process.communicate()]
        return models.GitResult(
            id="0", returncode=returncode, stdout=stdout, stderr=stderr
        )

    @classmethod
    def handle_editor_response(
        cls,
        game_id: models.IdType,
        level_id: models.IdType,
        editor_response: models.EditorResponse,
    ) -> Union[models.GitResult, None]:
        interface = cls._get_git_interface(game_id, level_id, editor_response.id)
        return interface.send_editor_response(editor_response)

    @staticmethod
    def _split(string: str) -> List[str]:
        result = []
        current = []
        in_quotes = False

        for char in string:
            if char == '"':
                in_quotes = not in_quotes
            elif char == " " and not in_quotes:
                if current:
                    result.append("".join(current))
                    current = []
            else:
                current.append(char)

        if current:
            result.append("".join(current))

        return result

    @classmethod
    def get_git_graph(
        cls, game_id: models.IdType, level_id: models.IdType
    ) -> Union[models.GitGraph, None]:
        nodes: List[str] = []
        children: Dict[str, List[str]] = {}
        parents: Dict[str, List[str]] = {}
        commit_messages: Dict[str, str] = {}

        argv = ["log", "--pretty=format:%H %s %P"]
        result = cls.run_git_command_directly(game_id, level_id, argv)
        if result.returncode != 0:
            return None
        for line in result.stdout.splitlines():
            hash_, message, *parent_hashes = cls._split(line.strip())
            nodes.append(hash_)
            parents[hash_] = []
            for parent in parent_hashes:
                if parent not in children:
                    children[parent] = []
                children[parent].append(hash_)
                parents[hash_].append(parent)
            commit_messages[hash_] = message

        head: str = ""

        argv = ["rev-parse", "HEAD"]
        result = cls.run_git_command_directly(game_id, level_id, argv)
        if result.returncode != 0:
            return None
        head = result.stdout.strip()

        tags: Dict[str, str] = {}

        argv = ["show-ref", "--tags", "-d"]
        result = cls.run_git_command_directly(game_id, level_id, argv)
        if result.returncode > 1:
            return None
        elif result.returncode == 0:
            for line in result.stdout.splitlines():
                hash_, raw_tag = cls._split(line.strip())
                tag = raw_tag.split("/")[-1]
                tags[hash_] = tag

        branch_names: Dict[str, str] = {}

        argv = ["show-ref", "--heads"]
        result = cls.run_git_command_directly(game_id, level_id, argv)
        if result.returncode > 1:
            return None
        elif result.returncode == 0:
            for line in result.stdout.splitlines():
                hash_, raw_branch_name = cls._split(line.strip())
                branch_name = raw_branch_name.split("/")[-1]
                branch_names[hash_] = branch_name

        graph = models.GitGraph(
            nodes=nodes,
            children=children,
            parents=parents,
            head=head,
            tags=tags,
            commit_messages=commit_messages,
            branch_names=branch_names,
        )

        return graph
