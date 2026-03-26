import os


def is_in_docker() -> bool:
    return os.environ.get("INSIDE_DOCKER") == "1"


def in_debug_mode() -> bool:
    return os.environ.get("DEBUG_MODE") == "1"
