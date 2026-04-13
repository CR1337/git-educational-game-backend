from __future__ import annotations
from pydantic import BaseModel
from pathlib import Path
from typing import List, Tuple, Annotated, Literal, Dict
from pydantic import StringConstraints


IdType = str


class Message(BaseModel):
    type_: Literal["Message"] = "Message"
    message: str


class File(BaseModel):
    type_: Literal["File"] = "File"
    filename: Path
    content: str


class GitCommand(BaseModel):
    type_: Literal["GitCommand"] = "GitCommand"
    argv: List[str]


class GitResult(BaseModel):
    type_: Literal["GitResult"] = "GitResult"
    id: IdType
    returncode: int
    stdout: str
    stderr: str


class EditorRequest(BaseModel):
    type_: Literal["EditorRequest"] = "EditorRequest"
    id: IdType
    file: File
    stdout: str
    stderr: str


class EditorResponse(BaseModel):
    type_: Literal["EditorResponse"] = "EditorResponse"
    id: IdType
    file: File
    abort: bool


class Map(BaseModel):
    type_: Literal["Map"] = "Map"
    id: IdType
    width: int
    height: int
    content: str
    patches: List[
        Tuple[int, int, Annotated[str, StringConstraints(min_length=1, max_length=1)]]
    ]

    @classmethod
    def parse(cls, string: str, id_: IdType) -> Map:
        lines = string.splitlines()

        header = lines[0].strip()
        width, height = [int(s) for s in header.split()]

        content = "\n".join(lines[1 : height + 1])
        patches = [
            (int(x), int(y), tile)
            for line in lines[height + 1 :]
            if len(line.strip()) > 0
            for x, y, tile in [line.strip().split()]
        ]

        return cls(id=id_, width=width, height=height, content=content, patches=patches)


class LevelNode(BaseModel):
    type_: Literal["LevelNode"] = "LevelNode"
    id: IdType
    name: str
    started: bool
    solved: bool


class Level(BaseModel):
    type_: Literal["Level"] = "Level"
    id: IdType
    files: List[File]
    map: Map
    clues: List[str]
    intro: str
    outro: str
    level_node: LevelNode


class LevelGraph(BaseModel):
    type_: Literal["LevelGraph"] = "LevelGraph"
    start_levels: List[LevelNode]
    edges: Dict[IdType, LevelNode]


class Player(BaseModel):
    type_: Literal["Player"] = "Player"
    name: str


class Game(BaseModel):
    type_: Literal["Game"] = "Game"
    id: IdType
    player: Player


class GitGraph(BaseModel):
    type_: Literal["GitGraph"] = "GitGraph"
    nodes: List[str]
    children: Dict[str, List[str]]
    parents: Dict[str, List[str]]
    head: str
    tags: Dict[str, str]
    commit_messages: Dict[str, str]
    branch_names: Dict[str, str]
