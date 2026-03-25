import os
from controllers.redis_controller import RedisController
import shutil
from models.game import GameIdType
from models.filesystem import FilesystemObject, File, FileList, FilesystemObjectType, Filepath, FileContent
from pathlib import Path
from controllers import GameController
from typing import List


class FileController:

    GAMES_DIRECTORY: str = GameController.GAMES_DIRECTORY
    FILESYSTEM_DIRECTORY_NAME: str = "filesystem"

    @classmethod
    def _get_filesystem_root(cls, game_id: GameIdType) -> Path:
        return Path(
            cls.GAMES_DIRECTORY,
            str(game_id),
            cls.FILESYSTEM_DIRECTORY_NAME
        )
    
    @classmethod
    def _get_full_filepath(cls, game_id: GameIdType, filepath: Path) -> Path:
        return Path(
            cls._get_filesystem_root(game_id),
            cls.get_current_working_directory(game_id),
            filepath
        ) 

    @classmethod
    def get_file(cls, game_id: GameIdType, filepath: Path) -> FilesystemObject:
        full_filepath: Path = cls._get_full_filepath(game_id, filepath)

        if not full_filepath.exists():
            raise FileNotFoundError()
        
        if full_filepath.is_dir():
            filepaths: List[Filepath] = [
                Filepath(filepath=Path(filename))
                for filename in os.listdir(full_filepath)
            ]
            file_list: FileList = FileList(
                filenames=filepaths
            )
            filesystem_object: FilesystemObject = FilesystemObject(
                filesystem_object_type=FilesystemObjectType.FILE_LIST,
                filesystem_object=file_list
            )

        else:
            with open(full_filepath, 'r', encoding='utf-8') as f:
                content: str = f.read()
            file: File = File(
                filepath=Filepath(filepath=full_filepath),
                content=FileContent(content=content)
            )
            filesystem_object: FilesystemObject = FilesystemObject(
                filesystem_object_type=FilesystemObjectType.FILE,
                filesystem_object=file
            )
        
        return filesystem_object

    @classmethod
    def create_file(cls, game_id: GameIdType, filepath: Path, is_directory: bool, content: str) -> FilesystemObject:
        full_filepath: Path = cls._get_full_filepath(game_id, filepath)

        if full_filepath.exists():
            raise FileExistsError()
        
        if is_directory:
            os.mkdir(full_filepath)

        else:
            with open(full_filepath, 'w', encoding='utf-8') as f:
                f.write(content)

        return cls.get_file(game_id, full_filepath)
        
    @classmethod
    def update_file(cls, game_id: GameIdType, filepath: Path, content: str) -> File:
        full_filepath: Path = cls._get_full_filepath(game_id, filepath)

        if not full_filepath.exists:
            raise FileNotFoundError()
        
        if full_filepath.is_dir():
            raise IsADirectoryError()
        
        with open(full_filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        filesystem_object: FilesystemObject = cls.get_file(game_id, full_filepath)
        assert isinstance(filesystem_object, File)
        return filesystem_object

    @classmethod
    def delete_file(cls, game_id: GameIdType, filepath: Path):
        full_filepath: Path = cls._get_full_filepath(game_id, filepath)

        if not full_filepath.exists:
            raise FileNotFoundError()
        
        if full_filepath.is_dir():
            os.rmdir(full_filepath)

        else:
            os.remove(full_filepath)  

    @classmethod
    def delete_game_files(cls, game_id: GameIdType):
        directory: Path = Path(
            cls.GAMES_DIRECTORY,
            str(game_id)
        )

        if not directory.exists:
            raise FileNotFoundError()
        
        os.rmdir(directory)

    @classmethod
    def create_game_files(cls, game_id: GameIdType):
        ...  # TODO

    @classmethod
    def move_file(cls, game_id: GameIdType, source: Path, destination: Path) -> FilesystemObject:
        full_source_filepath: Path = cls._get_full_filepath(game_id, source)
        full_destination_filepath: Path = cls._get_full_filepath(game_id, destination)

        if not full_source_filepath.exists:
            raise FileNotFoundError()
        
        if full_destination_filepath.exists:
            raise FileExistsError()
        
        shutil.move(full_source_filepath, full_destination_filepath)
        
        return cls.get_file(game_id, destination)

    @classmethod
    def copy_file(cls, game_id: GameIdType, source: Path, destination: Path) -> FilesystemObject:
        full_source_filepath: Path = cls._get_full_filepath(game_id, source)
        full_destination_filepath: Path = cls._get_full_filepath(game_id, destination)

        if not full_source_filepath.exists:
            raise FileNotFoundError()
        
        if full_destination_filepath.exists:
            raise FileExistsError()
        
        shutil.copy2(full_source_filepath, full_destination_filepath)
        
        return cls.get_file(game_id, destination)
    
    @classmethod
    def _get_current_working_directory_redis_key(cls, game_id: GameIdType) -> str:
        return f"game_id:{game_id}:current_working_directory"

    @classmethod
    def get_current_working_directory(cls, game_id: GameIdType) -> Path:
        key: str = cls._get_current_working_directory_redis_key(game_id)

        if not RedisController.exists(key):
            RedisController.set(key, "/")

        return Path(str(RedisController.get(key)))
    
    @classmethod
    def set_current_working_directory(cls, game_id: GameIdType, current_working_directory: Path) -> Path:
        key: str = cls._get_current_working_directory_redis_key(game_id) 

        RedisController.set(key, current_working_directory.as_posix())

        return current_working_directory
    