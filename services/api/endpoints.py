from fastapi import APIRouter, status, Response
import models
import debug
import controllers
from typing import List, Union


if debug.is_in_docker():
    router: APIRouter = APIRouter()
else:
    router: APIRouter = APIRouter(prefix="/api")


# -- root ---------------------------------------------------------------------


@router.get("/", response_model=models.Message, status_code=status.HTTP_200_OK)
async def get_root() -> models.Message:
    return models.Message(message="Hello from the API!")


@router.get(
    "/server-config", response_model=models.ServerConfig, status_code=status.HTTP_200_OK
)
async def get_server_config() -> models.ServerConfig:
    return controllers.RootController.get_server_config()


# -- games --------------------------------------------------------------------


@router.get(
    "/games", response_model=List[models.IdType], status_code=status.HTTP_200_OK
)
@debug.debug_only_endpoint
async def get_games() -> List[models.IdType]:
    return controllers.GameController.get_games()


@router.post(
    "/games/new", response_model=models.Game, status_code=status.HTTP_201_CREATED
)
async def post_new_game(
    new_game_info: models.NewGameInfo,
) -> Union[models.Game, Response]:
    game = controllers.GameController.new_game(new_game_info)
    return game


@router.get(
    "/games/{game_id}", response_model=models.Game, status_code=status.HTTP_200_OK
)
async def get_game(game_id: models.IdType) -> Union[models.Game, Response]:
    try:
        return controllers.GameController.get_game(game_id)

    except FileNotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.delete(
    "/games/{game_id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT
)
@debug.debug_only_endpoint
async def delete_game(game_id: models.IdType) -> Union[None, Response]:
    try:
        controllers.GameController.delete_game(game_id)

    except FileNotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


# -- levels -------------------------------------------------------------------


@router.get(
    "/levelsets", response_model=List[models.Levelset], status_code=status.HTTP_200_OK
)
async def get_levelsets() -> List[models.Levelset]:
    levelsets = controllers.LevelController.get_levelsets()
    print(levelsets)
    return levelsets


@router.get(
    "/games/{game_id}/level-graph",
    response_model=models.LevelGraph,
    status_code=status.HTTP_200_OK,
)
async def get_level_graph(game_id: models.IdType) -> Union[models.LevelGraph, Response]:
    try:
        return controllers.LevelController.get_level_graph(game_id)

    except FileNotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.get(
    "/games/{game_id}/levels",
    response_model=List[models.LevelNode],
    status_code=status.HTTP_200_OK,
)
async def get_levels(game_id: models.IdType) -> Union[List[models.LevelNode], Response]:
    try:
        return controllers.LevelController.get_levels(game_id)

    except FileNotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.get(
    "/games/{game_id}/levels/{level_id}",
    response_model=models.Level,
    status_code=status.HTTP_200_OK,
)
async def get_level(
    game_id: models.IdType, level_id: models.IdType
) -> Union[models.Level, Response]:
    try:
        return controllers.LevelController.get_level(game_id, level_id)

    except FileNotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.put(
    "/games/{game_id}/levels/{level_id}/reset",
    response_model=models.Level,
    status_code=status.HTTP_200_OK,
)
async def put_level_reset(
    game_id: models.IdType, level_id: models.IdType
) -> Union[models.Level, Response]:
    try:
        return controllers.LevelController.reset_level(game_id, level_id)

    except FileNotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.put(
    "/games/{game_id}/levels/{level_id}/started",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
async def put_level_started(
    game_id: models.IdType, level_id: models.IdType
) -> Union[None, Response]:
    try:
        controllers.LevelController.set_started(game_id, level_id)

    except FileNotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.put(
    "/games/{game_id}/levels/{level_id}/solved",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
async def put_level_solved(
    game_id: models.IdType, level_id: models.IdType
) -> Union[None, Response]:
    try:
        controllers.LevelController.set_solved(game_id, level_id)

    except FileNotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


# -- files --------------------------------------------------------------------


@router.get(
    "/games/{game_id}/levels/{level_id}/files",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
)
async def get_files(
    game_id: models.IdType, level_id: models.IdType
) -> Union[List[str], Response]:
    try:
        return controllers.FileController.get_files(game_id, level_id)

    except FileNotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.get(
    "/games/{game_id}/levels/{level_id}/files/{filename}",
    response_model=models.File,
    status_code=status.HTTP_200_OK,
)
async def get_file(
    game_id: models.IdType, level_id: models.IdType, filename: str
) -> Union[models.File, Response]:
    try:
        return controllers.FileController.get_file(game_id, level_id, filename)

    except FileNotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.put(
    "/games/{game_id}/levels/{level_id}/files/{filename}",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
async def put_file(
    game_id: models.IdType, level_id: models.IdType, filename: str, file: models.File
) -> Union[None, Response]:
    try:
        controllers.FileController.put_file(game_id, level_id, filename, file)

    except FileNotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


# -- git ----------------------------------------------------------------------


@router.post(
    "/games/{game_id}/levels/{level_id}/git-command",
    response_model=Union[models.GitResult, models.EditorRequest],
    status_code=status.HTTP_202_ACCEPTED,
)
async def post_git_command(
    game_id: models.IdType, level_id: models.IdType, git_command: models.GitCommand
) -> Union[models.GitResult, models.EditorRequest, Response]:
    try:
        result = controllers.GitController.run_git_command(
            game_id, level_id, git_command
        )

    except FileNotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    except PermissionError:
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    if result is None:
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return result


@router.post(
    "/games/{game_id}/levels/{level_id}/editor-response",
    response_model=models.GitResult,
    status_code=status.HTTP_202_ACCEPTED,
)
async def post_editor_response(
    game_id: models.IdType,
    level_id: models.IdType,
    editor_response: models.EditorResponse,
) -> Union[models.GitResult, Response]:
    try:
        result = controllers.GitController.handle_editor_response(
            game_id, level_id, editor_response
        )

    except FileNotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    if result is None:
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return result


@router.get(
    "/games/{game_id}/levels/{level_id}/git-graph",
    response_model=models.GitGraph,
    status_code=status.HTTP_200_OK,
)
async def get_git_graph(
    game_id: models.IdType, level_id: models.IdType
) -> Union[models.GitGraph, Response]:
    try:
        result = controllers.GitController.get_git_graph(game_id, level_id)

    except FileNotFoundError:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    if result is None:
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return result
