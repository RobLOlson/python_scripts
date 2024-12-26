# to do
# git
#   git hooks
# pytest
# justfile
# typer (CLI)
# logger
# poetry / PyPi
# toml config/database
# other database
import logging
import os
import pathlib
import shutil
import string
from enum import Enum
from logging.handlers import RotatingFileHandler
from typing import List

import rich
import toml
import typer
from appdirs import user_config_dir
from jinja2 import Environment, FileSystemLoader
from typing_extensions import Annotated

try:
    from utilities import query
    from utilities import tomlshelve
    from utilities.tomldict import TomlDict
    from utilities import tomlconfig

except ModuleNotFoundError:
    from .utilities import query
    from .utilities import tomlshelve
    from .utilities.tomldict import TomlDict
    from .utilities import tomlconfig

DEBUG = True


class Feature(str, Enum):
    LOGGING = "logging"
    TYPER = "typer"
    GIT = "git"
    GIT_HOOKS = "git_hooks"
    TOML_CONFIG = "toml_config"
    POETRY = "poetry"
    DATABASE = "database"


class Option(str, Enum):
    MULTIPLE_FILES = "multiple_files"


# Logging Set-up vvvvvvvvvvvvvvvvvvvv

log_dir = pathlib.Path(user_config_dir()) / "robolson" / "project" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
LOG_FILE = log_dir / "project.log"

logger = logging.getLogger()

logger.setLevel(logging.INFO)

handler = RotatingFileHandler(filename=LOG_FILE.absolute(), maxBytes=100_000, backupCount=2)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

handler.setFormatter(formatter)
logger.addHandler(handler)

# Logging Set-up ^^^^^^^^^^^^^^^^^^^^

main_app = typer.Typer()
config_app = typer.Typer()
logging_app = typer.Typer()
main_app.add_typer(config_app, name="config", help="Edit config file.")
main_app.add_typer(logging_app, name="log", help="Edit config file.")


_PROMPT = f"rob.{pathlib.Path(__file__).stem}> "
_PROMPT_STYLE = "[white on blue]"
_ERROR_STYLE = "[red on black]"

THIS_FILE = pathlib.Path(__file__)

# Configuration Set-up vvvvvvvvvvvvvvvvvvvv

_BASE_CONFIG_FILE = THIS_FILE.parent / "config" / "project.toml"
_USER_CONFIG_FILE = (
    pathlib.Path(user_config_dir()) / "robolson" / "project" / "config" / "project.toml"
)

CONFIG = tomlconfig.TomlConfig(_BASE_CONFIG_FILE)
# CONFIG = TomlDict.open(_BASE_CONFIG_FILE)

with open(_BASE_CONFIG_FILE, "r") as fp:
    CONFIG = toml.load(fp)

if _USER_CONFIG_FILE.exists():
    with open(_USER_CONFIG_FILE, "r") as fp:
        try:
            USER_SETTINGS = toml.load(fp)
            CONFIG.update(USER_SETTINGS)
        except toml.decoder.TomlDecodeError:
            rich.print(
                "[yellow]WARNING.[/yellow] Config file corrupted (invalid TOML file).  Using default settings."
            )

else:
    _USER_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    _USER_CONFIG_FILE.touch(exist_ok=True)
    with open(_USER_CONFIG_FILE, "w") as fp:
        toml.dump(CONFIG, fp)

FEATURE_DEFAULTS = CONFIG["defaults"]["features"]
OPTION_DEFAULTS = CONFIG["defaults"]["options"]

# Configuration Set-up ^^^^^^^^^^^^^^^^^^^^

TEMPLATES_FOLDER = THIS_FILE.parent / "config" / "project"
PROMPT = "\nrob.project> "

JINJA_ENV = Environment(
    loader=FileSystemLoader(TEMPLATES_FOLDER), trim_blocks=True, lstrip_blocks=True
)


@config_app.callback(invoke_without_command=True)
def config_default(ctx: typer.Context):
    if not ctx.invoked_subcommand:
        os.startfile(_USER_CONFIG_FILE)


@logging_app.callback(invoke_without_command=True)
def log_default(ctx: typer.Context):
    if not ctx.invoked_subcommand:
        os.startfile(LOG_FILE)


def default(
    project_name: str = "my_project",
    directory: str | None = None,
    add_feature: list[Feature] = [],
    remove_feature: list[Feature] = [],
    multiple_files: bool = False,
    interact: bool = True,
):
    if directory:
        os.chdir(pathlib.Path(directory).absolute())

    code_yes = []
    feature_unknown = []
    added_options = []
    option_unknown = []
    option_list = list()

    target_features: list[Feature] = [feature for feature in add_feature]
    excluded_features: list[Feature] = [feature for feature in remove_feature]

    for feature in list(Feature):
        if feature in excluded_features:
            continue
        if interact and feature not in target_features:
            feature_unknown.append(feature)
        else:
            if FEATURE_DEFAULTS[feature]:
                target_features.append(feature)

    for option, value in OPTION_DEFAULTS.items():
        if not interact and value:
            added_options.append(option)
        else:
            option_unknown.append(option)

    if multiple_files and "multiple_files" not in added_options:
        added_options.append(multiple_files)

    if interact and project_name == "my_project":
        rich.print(f"What is the name of the project? [yellow](Default: 'my_project')")
        project_name = input(_PROMPT)
        if not project_name:
            project_name = "my_project"

    if interact:
        rich.print(f"Is this project a single file script or multiple file?")
        choice = query.select(["Single File", "Multiple Files"])
        if choice == "Single File":
            multiple_files = False
        else:
            multiple_files = True

    if feature_unknown:
        rich.print("Which code features to include?")
        approved_features = query.approve_list(
            feature_unknown, preamble=False, repr_func=lambda x: x.value
        )
        target_features.extend(approved_features)

    project_folder = pathlib.Path(project_name)
    if project_folder.exists() and project_folder.glob("*") and not DEBUG:
        raise FileExistsError(f"Folder {project_folder} already exists.")

    if DEBUG and project_folder.exists():
        shutil.rmtree(project_folder)

    project_folder.mkdir(exist_ok=True, parents=True)
    main_file = project_folder / (project_name + ".py")
    template = JINJA_ENV.get_template("jinja_template.txt")
    main_imports = ""
    main_contents = []

    if not multiple_files:
        main_contents = template.render(
            target_features=target_features,
            project_name=project_name,
            multiple_files=multiple_files,
            all_features=target_features,
            main=True,
        ).split("\n")

    else:
        if Feature.LOGGING in target_features:
            main_contents.append("from logger import logger")
            logger_contents = template.render(
                target_features=["logging"], project_name=project_name
            )
            logger_file = project_folder / "logger.py"
            logger_file.touch(exist_ok=True)

            with open(project_folder / "logger.py", "w", encoding="utf-8") as fp:
                fp.write(logger_contents)

        if Feature.TOML_CONFIG in target_features:
            main_contents.append("from toml_config import config")
            logger_contents = template.render(
                target_features=["toml_config"], project_name=project_name
            )
            logger_file = project_folder / "toml_config.py"
            logger_file.touch(exist_ok=True)

            with open(project_folder / "toml_config.py", "w", encoding="utf-8") as fp:
                fp.write(logger_contents)

        if Feature.TYPER in target_features:
            main_contents.append("import typer")
            main_contents.append("from typer_apps import main_app")
            all_features = []
            if Feature.TOML_CONFIG in target_features:
                main_contents.append("from typer_apps import config_app")
                all_features.append("toml_config")
            if Feature.LOGGING in target_features:
                main_contents.append("from typer_apps import logging_app")
                all_features.append("logging")
            typer_contents = template.render(
                target_features=["typer"], project_name=project_name, all_features=all_features
            )
            typer_file = project_folder / "typer_apps.py"
            typer_file.touch(exist_ok=True)

            with open(project_folder / "typer_apps.py", "w", encoding="utf-8") as fp:
                fp.write(typer_contents)

    print(f"Using features: {target_features}\nUsing options: {added_options}")
    with open(main_file, "w", encoding="utf-8") as fp:
        if Feature.TYPER in target_features:
            finale = template.render(
                target_features=[],
                project_name=project_name,
                main=True,
                all_features=target_features,
            ).split("\n")
        else:
            finale = template.render(
                target_features=[],
                project_name=project_name,
                main=True,
                all_features=target_features,
            ).split("\n")

        main_contents.extend(finale)

        fp.write("\n".join(main_contents))


@main_app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    name: str = "my_project",
    directory: str = ".",
    add_feature: Annotated[List[Feature], typer.Option(default=[])] = [],
    remove_feature: Annotated[List[Feature], typer.Option(default=[])] = [],
    multiple_files: bool = False,
    interact: bool = True,
):
    """Create a new Python project."""
    if not ctx.invoked_subcommand:
        default(
            project_name=name,
            directory=directory,
            add_feature=add_feature,
            remove_feature=remove_feature,
            multiple_files=multiple_files,
            interact=interact,
        )
        return

    # default(name=name, yes_all=yes_all)


if __name__ == "__main__":
    main_app()
