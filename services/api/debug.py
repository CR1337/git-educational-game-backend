import os


def is_in_docker() -> bool:
    return os.environ.get("INSIDE_DOCKER") == "1"
