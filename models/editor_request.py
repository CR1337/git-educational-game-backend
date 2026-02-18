from dataclasses import dataclass


@dataclass
class EditorRequest:
    editor_requerst_id: str
    game_id: str
    filename: str