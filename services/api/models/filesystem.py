from pydantic import BaseModel
from pathlib import Path
from typing import List, Union, Optional
from enum import Enum


class FilesystemObjectType(str, Enum):
    FILE = "file"
    FILE_LIST = "file_list"


class FileContent(BaseModel):
    content: str


class Filepath(BaseModel):
    filepath: Path


class FileCreation(BaseModel):
    is_directory: bool
    content: Optional[str]


class File(BaseModel):
    filepath: Filepath
    content: FileContent


class FileList(BaseModel):
    filenames: List[Filepath]


class FilesystemObject(BaseModel):
    filesystem_object_type: FilesystemObjectType
    filesystem_object: Union[File, FileList]
    