import os
from models import Game
from typing import List, Optional

class FileController:

    @classmethod
    def get_filenames(cls, game: Game, filepath: Optional[str]) -> List[str]:
        filepath = filepath or os.path.sep
        ...  # TODO
        return []
    
    @classmethod
    def get_file(cls, game: Game, filepath: str) -> Optional[str]:
        ...  # TODO
    
    @classmethod
    def create_file(cls, game: Game, filepath: str, content: str) -> bool:
        ...  # TODO
        return False
    
    @classmethod
    def update_file(cls, game: Game, filepath: str, content: str) -> bool:
        ...  # TODO
        return False
    
    @classmethod
    def delete_file(cls, game: Game, filepath: str) -> bool:
        ...  # TODO
        return False

    