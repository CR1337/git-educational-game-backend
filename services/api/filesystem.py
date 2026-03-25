from pathlib import Path
import shutil
import models
from typing import List
import debug
import subprocess


class Filesystem:

    GAME_DATA_PATH: Path = (
        Path("/", "game_data")
        if debug.is_in_docker()
        else Path(Path.cwd(), "..", "..", "volumes", "game_data")
    )

    GAMES_PATH: Path = Path(GAME_DATA_PATH, "games")
    LEVELS_PATH: Path = Path(GAME_DATA_PATH, "levels")

    GIT_EDITOR_PATH: Path = (
        Path("/", "app", "git_orchestrator", "git_editor")
        if debug.is_in_docker()
        else Path(Path.cwd(), "git_orchestrator", "git_editor.py")
    )

    GIT_EXECUTABLE_PATH: Path = Path(
        subprocess.check_output(
            ["which", "git"], 
            text=True
        ).strip()
    )

    @classmethod
    def get_path(cls, components: List[str | Path], *, must_exist: bool = True) -> Path:
        path = Path(*components)
        if not path.exists() and must_exist:
            raise FileNotFoundError()
        return path
    
    @classmethod
    def get_level_path(cls, level_id: models.IdType, *, must_exist: bool = True) -> Path:
        return cls.get_path([
            cls.LEVELS_PATH,
            level_id
        ], must_exist=must_exist)
    
    @classmethod
    def get_level_map_path(cls, level_id: models.IdType, *, must_exist: bool = True) -> Path:
        return cls.get_path([
            cls.get_level_path(level_id, must_exist=must_exist),
            "map.txt"
        ], must_exist=must_exist)
    
    @classmethod
    def get_level_text_path(cls, level_id: models.IdType, *, must_exist: bool = True) -> Path:
        return cls.get_path([
            cls.get_level_path(level_id, must_exist=must_exist),
            "text.json"
        ], must_exist=must_exist)
    
    @classmethod
    def get_level_meta_path(cls, level_id: models.IdType, *, must_exist: bool = True) -> Path:
        return cls.get_path([
            cls.get_level_path(level_id, must_exist=must_exist),
            "meta.json"
        ], must_exist=must_exist)
    
    @classmethod
    def get_level_init_path(cls, level_id: models.IdType, *, must_exist: bool = True) -> Path:
        return cls.get_path([
            cls.get_level_path(level_id, must_exist=must_exist),
            "init.lst"
        ], must_exist=must_exist)
    
    @classmethod
    def get_level_files_path(cls, level_id: models.IdType, *, must_exist: bool = True) -> Path:
        return cls.get_path([
            cls.get_level_path(level_id, must_exist=must_exist),
            "files"
        ], must_exist=must_exist)
    
    @classmethod
    def get_level_file_path(cls, level_id: models.IdType, filename: str, *, must_exist: bool = True) -> Path:
        return cls.get_path([
            cls.get_level_files_path(level_id, must_exist=must_exist),
            filename
        ], must_exist=must_exist)
    
    @classmethod
    def get_game_path(cls, game_id: models.IdType, *, must_exist: bool = True) -> Path:
        return cls.get_path([
            cls.GAMES_PATH,
            game_id
        ], must_exist=must_exist)
    
    @classmethod
    def get_game_meta_path(cls, game_id: models.IdType, *, must_exist: bool = True) -> Path:
        return cls.get_path([
            cls.get_game_path(game_id, must_exist=must_exist),
            "meta.json"
        ], must_exist=must_exist)
    
    @classmethod
    def get_game_levels_path(cls, game_id: models.IdType, *, must_exist: bool = True) -> Path:
        return cls.get_path([
            cls.get_game_path(game_id, must_exist=must_exist),
            "levels"
        ], must_exist=must_exist)
    
    @classmethod
    def get_game_level_path(cls, game_id: models.IdType, level_id: models.IdType, *, must_exist: bool = True) -> Path:
        return cls.get_path([
            cls.get_game_levels_path(game_id, must_exist=must_exist),
            level_id
        ], must_exist=must_exist)
    
    @classmethod
    def get_game_level_meta_path(cls, game_id: models.IdType, level_id: models.IdType, *, must_exist: bool = True) -> Path:
        return cls.get_path([
            cls.get_game_level_path(game_id, level_id, must_exist=must_exist),
            "meta.json"
        ], must_exist=must_exist)       

    @classmethod
    def get_game_level_repo_path(cls, game_id: models.IdType, level_id: models.IdType, *, must_exist: bool = True) -> Path:
        return cls.get_path([
            cls.get_game_level_path(game_id, level_id, must_exist=must_exist),
            "repo"
        ], must_exist=must_exist) 

    @classmethod
    def get_game_level_repo_file(cls, game_id: models.IdType, level_id: models.IdType, filename: str, *, must_exist: bool = True) -> Path:
        return cls.get_path([
            cls.get_game_level_repo_path(game_id, level_id, must_exist=must_exist),
            filename
        ], must_exist=must_exist)
    
    @classmethod
    def copy_directory(cls, source: Path, destination: Path) -> None:
        shutil.copytree(source, destination) 
