import os
from pathlib import Path
from typing import Dict, List, Tuple
from jinja2 import Environment, FileSystemLoader


TEMPLATES_DIRECTORY: Path = Path("./setup/templates")
BIN_DIRECTORY: Path = Path("./bin")
TEMPLATE_TARGET_PAIRS: List[Tuple[Path, Path]] = [
    (Path(".env.jinja2"), Path(".env")),
    (Path("docker-compose.yaml.jinja2"), Path("docker-compose.yaml")),
    (Path("build.jinja2"), Path(BIN_DIRECTORY, "build")),
    (Path("run.jinja2"), Path(BIN_DIRECTORY, "run")),
    (Path("running.jinja2"), Path(BIN_DIRECTORY, "running")),
    (Path("stop.jinja2"), Path(BIN_DIRECTORY, "stop")),
    (Path("test.jinja2"), Path(BIN_DIRECTORY, "test")),
]


def ask_choice(prompt: str, choices: List[str]) -> int:
    print(prompt)
    for idx, choice in enumerate(choices):
        print(f"{idx} - {choice}")
    choice = input(f"(0 - {len(choices) - 1})>")

    success = False
    while not success:
        try:
            choice = int(choice)
        except ValueError:
            continue
        success = 0 <= choice < len(choices)

    assert isinstance(choice, int)
    return choice


def ask_parameters() -> Dict[str, str]:
    container_runtimes = ["docker", "podman"]
    container_runtime = container_runtimes[
        ask_choice("What container runtime do you want to use?", container_runtimes)
    ]

    environments = ["local", "server"]
    environment = environments[
        ask_choice("In what environment is this running?", environments)
    ]

    modes = ["debug", "production"]
    mode = modes[ask_choice("What mode do you want to setup?", modes)]

    parameters = {
        "container_runtime": container_runtime,
        "environment": environment,
        "mode": mode,
    }

    return parameters


def render_templates(parameters: Dict[str, str]) -> None:
    jinja2_env = Environment(loader=FileSystemLoader(TEMPLATES_DIRECTORY))
    jinja2_env.globals.update(int=lambda x: int(x))

    for template_path, target_path in TEMPLATE_TARGET_PAIRS:
        print(f"Creating {target_path} ...")
        template = jinja2_env.get_template(template_path.as_posix())
        string = template.render(parameters)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(string)


def set_execution_permissions() -> None:
    os.system(f"chmod +x {BIN_DIRECTORY.as_posix()}")


def build_containers() -> None:
    os.system(f"bash {Path(BIN_DIRECTORY, 'build').as_posix()}")


def main() -> None:
    parameters = ask_parameters()
    render_templates(parameters)
    set_execution_permissions()
    build_containers()


if __name__ == "__main__":
    main()
