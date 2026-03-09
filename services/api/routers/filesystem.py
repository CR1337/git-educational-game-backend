from fastapi import APIRouter, Path, HTTPException, status
import pathlib
from models.game import GameIdType
from models.filesystem import FilesystemObject, File, Filepath, FileContent, FileCreation
from controllers.filesystem_controller import FileController


router: APIRouter = APIRouter(prefix="/games/{game_id}/files", tags=["files"])


@router.get(
    "/{filepath:path}", 
    response_model=FilesystemObject,
    status_code=status.HTTP_200_OK
)
async def get_file(
    game_id: GameIdType, 
    filepath: str = Path(...)
) -> FilesystemObject:
    try:
        return FileController.get_file(game_id, pathlib.Path(filepath))
    except FileNotFoundError:
        raise HTTPException(404, detail=f"{filepath} not found")


@router.post(
    "/{filepath:path}", 
    response_model=FilesystemObject,
    status_code=status.HTTP_201_CREATED
)
async def create_file(
    game_id: GameIdType, 
    file_creation: FileCreation,
    filepath: str = Path(...)
) -> FilesystemObject:
    is_directory: bool = file_creation.is_directory
    if not is_directory:
        assert isinstance(file_creation.content, str)
        content: str = file_creation.content
    else:
        content: str = ""

    try:
        return FileController.create_file(game_id, pathlib.Path(filepath), is_directory, content)        
    except FileExistsError:
        raise HTTPException(409, detail=f"{filepath} already exists")
    

@router.put(
    "/{filepath:path}", 
    response_model=File,
    status_code=status.HTTP_201_CREATED
)
async def update_file(
    game_id: GameIdType, 
    content: FileContent,
    filepath: str = Path(...)
) -> File:
    try:
        return FileController.update_file(game_id, pathlib.Path(filepath), content.content)
    except FileNotFoundError:
        raise HTTPException(404, detail=f"{filepath} not found")
    except IsADirectoryError:
        raise HTTPException(409, detail=f"{filepath} is a directory")


@router.delete(
    "/{filepath:path}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_file(
    game_id: GameIdType,
    filepath: str = Path(...)
) -> None:
    try:
        FileController.delete_file(game_id, pathlib.Path(filepath))
    except FileNotFoundError:
        raise HTTPException(404, detail=f"{filepath} not found")
    

@router.post(
    "/{source:path}/move-to/{destination:path}",
    response_model=FilesystemObject,
    status_code=status.HTTP_201_CREATED
)
async def move_file(
    game_id: GameIdType,
    source: str = Path(...),
    destination: str = Path(...)
) -> FilesystemObject:
    try:
        return FileController.move_file(game_id, pathlib.Path(source), pathlib.Path(destination))
    except FileNotFoundError:
        raise HTTPException(404, detail=f"{source} not found")
    except FileExistsError:
        raise HTTPException(409, detail=f"{destination} already exists")
    

@router.post(
    "/{source:path}/copy-to/{destination:path}",
    response_model=FilesystemObject,
    status_code=status.HTTP_201_CREATED
)
async def copy_file(
    game_id: GameIdType,
    source: str = Path(...),
    destination: str = Path(...)
) -> FilesystemObject:
    try:
        return FileController.copy_file(game_id, pathlib.Path(source), pathlib.Path(destination))
    except FileNotFoundError:
        raise HTTPException(404, detail=f"{source} not found")
    except FileExistsError:
        raise HTTPException(409, detail=f"{destination} already exists")
    

@router.get(
    "/current-working-directory",
    response_model=Filepath,
    status_code=status.HTTP_200_OK
)
async def get_current_working_directory(
    game_id: GameIdType
) -> Filepath:
    return Filepath(
        filepath=FileController.get_current_working_directory(
            game_id
        )
    )


@router.put(
    "/current-working-directory",
    response_model=Filepath,
    status_code=status.HTTP_200_OK
)
async def set_current_working_directory(
    game_id: GameIdType,
    current_working_directory: Filepath
) -> Filepath:
    return Filepath(
        filepath=FileController.set_current_working_directory(
            game_id, 
            current_working_directory.filepath
        )
    )
   