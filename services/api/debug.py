import os
from functools import wraps
from typing import Callable, TypeVar, Any
from fastapi import HTTPException, status


def is_in_docker() -> bool:
    return os.environ.get("INSIDE_DOCKER") == "1"


def in_debug_mode() -> bool:
    print(f"{os.environ.get('DEBUG_MODE')=}")
    return os.environ.get("DEBUG_MODE") == "1"

T = TypeVar("T")

def debug_only_endpoint(endpoint: Callable[..., T]) -> Callable[..., T]:
    @wraps(endpoint)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        if not in_debug_mode():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        return await endpoint(*args, **kwargs)  # type: ignore
    return wrapper  # type: ignore
