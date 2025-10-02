"""Minimal decorator-based CLI.

This module provides a very small command registry and dispatcher so that
functions can be exposed as CLI commands via a decorator.

Current scope (intentionally minimal):
- Register commands with a string signature, e.g. "config" or "algebra render".
- Dispatch only on a single word command (argv[0]). If a multi-word signature
  is registered, its first word is used as the key for now.

Example:
    from rob.utilities import cli

    @cli.cli("config")
    def configure_problem_set():
        print("Configuring...")

    if __name__ == "__main__":
        cli.main()
"""

from __future__ import annotations

import inspect
import logging
import os
import shlex
import shutil
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Callable, Dict

import rich
from appdirs import user_config_dir, user_data_dir

try:
    from tomlconfig import TomlConfig
except ImportError:
    from .tomlconfig import TomlConfig

_DEBUG = False
_CONFIG: TomlConfig | None = None
OPTIONS: Dict[str, Any] = {}  # validated options
_HARDCODED_OPTIONS: Dict[str, Any] = {
    "help": False,
    "h": False,
    "capture_output": True,
}


def wrapped(text: str, indent: int = 0, indent_2: int = 18, sep: str = " ") -> str:
    try:
        term_width = shutil.get_terminal_size((80, 20)).columns
    except shutil.GetTerminalSizeError:
        term_width = 80
    final_string = ""
    tokens = text.split(sep)
    line = " " * indent + tokens[0]
    for token in tokens[1:]:
        if len(line) + len(token) + 1 > term_width:
            final_string += line + "\n"
            line = " " * indent_2 + token
        else:
            line += sep + token
    final_string += line
    return final_string


def _print_usage(func: Callable[[], None] | None = None, passed_command: list[str] | None = None) -> None:
    main_file = Path(sys.modules["__main__"].__file__)
    help_lines: list[str] = []

    if not _REGISTERED_COMMANDS:
        rich.print("[red]No commands registered.[/red]")
        return

    # if passed_command == ["<no command>"]:
    #     passed_command = None
    if passed_command is None:
        passed_command = ["<no command>"]

    target_commands: list[tuple[str, Callable[[], None]]] = []

    if func is None or func.__name__ == "main":
        target_commands = list(_REGISTERED_COMMANDS.items())
    else:
        target_commands = [
            (command, target_func)
            for command, target_func in _REGISTERED_COMMANDS.items()
            if " ".join(passed_command) in command
        ]

    for command, target_func in target_commands:
        # if passed_command and not command.startswith(" ".join(passed_command)):
        #     continue
        command_example = getattr(target_func, "help_signature", "<no command>")
        command_example = command_example.replace(target_func.cli_command, command)

        underline = "  " + "-" * len(command_example)
        underline = "\n" + underline if len(target_commands) < 5 else ""

        command_example = command_example.replace("<no command>", "[red]<no command>[/red]")
        description = f"{target_func.__doc__.strip().split('\n')[0] if target_func.__doc__ else '[red](No description)[/red]'}"
        description = wrapped(description, indent=4, indent_2=5, sep=" ")
        description = "\n" + description if len(target_commands) < 15 else ""

        py_signature = f"`{getattr(target_func, 'py_signature', f'{target_func.__name__}(...)')}`"
        py_signature = wrapped(py_signature, indent=6, indent_2=7, sep=" ")
        py_signature = "\n" + py_signature if len(target_commands) < 10 else ""
        help_lines.append(f"{command_example}{underline}{description}{py_signature}\n")
    if len(passed_command) > 1:
        command = passed_command[0]
    else:
        command = "<command>"

    help_lines.sort()
    # else:
    #     command = func.cli_command

    if main_file.parent == Path.cwd():
        usage = f"python {main_file.name} [yellow]{command}[/yellow]"
    else:
        if (main_file.parent / "__init__.py").exists():
            module_path = main_file.parent.name
            usage = f"python -m {module_path}.{main_file.stem} [yellow]{command}[/yellow]"
        else:
            usage = f"python -m {main_file.stem} [yellow]{command}[/yellow]"

    rich.print(f"Usage: {usage}\n")
    if func is None or func.__name__ == "main":
        rich.print("Available commands: \n")
    else:
        rich.print("Available " + " ".join(passed_command) + " subcommands: \n")
        # if passed_command:
        # else:
    for help_line in help_lines:
        rich.print(f"  {help_line}")

    if OPTIONS:
        display_options = [
            option
            for option in sorted(set(_HARDCODED_OPTIONS.keys()) | set(OPTIONS.keys()))
            if len(option) > 1
        ]

    opt_strs = [f"[--{option}]" for option in display_options]
    wrapped_string = wrapped(f"Global options: {' '.join(opt_strs)}", indent=2, indent_2=18, sep=" ")
    rich.print(wrapped_string)


# ^^^^^^^^^^ def _print_usage ^^^^^^^^^^


def _parse_options(raw_args: list[str]) -> Dict[str, str | bool]:
    """Parse CLI options from a list of arguments.

    Parameters
    ----------
    raw_args: list[str]
    List of arguments to parse. Non-option arguments are filtered out.

    Returns
    -------
    opts: Dict[str, str | bool]
    Dictionary of parsed options.
    """
    # options.clear()
    i = 0

    opts: Dict[str, str | bool] = {}

    while i < len(raw_args):
        token = raw_args[i]
        if token.startswith("--"):
            if "=" in token:
                key, value = token[2:].split("=", 1)
                if key:
                    if value.lower() == "true":
                        value = True
                    elif value.lower() == "false":
                        value = False

                    opts[key] = value
            else:
                if token[2:5] == "no-":
                    key = token[5:]
                    opts[key] = False
                else:
                    key = token[2:]
                    opts[key] = True
        elif token.startswith("-"):
            for char in token[1:]:
                opts[char] = True
        i += 1

    return opts


# ^^^^^^^^^^ def _parse_options ^^^^^^^^^^


_REGISTERED_COMMANDS: Dict[str, Callable[[], None]] = {}
_PASSED_OPTIONS: Dict[str, Any] = _parse_options(sys.argv[1:])  # unvalidated options
OPTIONS.update(_PASSED_OPTIONS)

# def _update_options():
#     global OPTIONS

# for option, value in _PASSED_OPTIONS.items():
#     if option in OPTIONS:
#         OPTIONS[option] = value
#     elif option in _HARDCODED_OPTIONS.keys():
#         OPTIONS[option] = value
# else:
#     rich.print(f"[red]Unknown option: {option}[/red]\n")
#     _print_usage()
#     sys.exit(1)
# else:
#     if option not in _HARDCODED_OPTIONS.keys():
#         rich.print(f"[red]Unknown option: {option}[/red]\n")
#         _print_usage()
#         sys.exit(1)
#     else:
#         _CONFIG["options"].get(option, _HARDCODED_OPTIONS[option]) = value

# OPTIONS.update(_PASSED_OPTIONS)


cli_log_dir = Path(user_data_dir()) / "robolson" / "cli" / "logs"
cli_log_dir.mkdir(parents=True, exist_ok=True)
cli_log_file = cli_log_dir / "cli.log"

cli_logger = logging.getLogger()

cli_logger.setLevel(logging.INFO)

handler = RotatingFileHandler(filename=cli_log_file.absolute(), maxBytes=100_000, backupCount=2)
formatter = logging.Formatter("%(message)s")

handler.setFormatter(formatter)
cli_logger.addHandler(handler)

if cli_log_file.stat().st_size > 2 * 1024 * 1024:
    with open(cli_log_file, "r") as fp:
        half_log = fp.readlines()
        half_log = half_log[int(len(half_log) / 2) :]
    with open(cli_log_file, "w") as fp:
        fp.writelines(half_log)


class CollisionError(Exception):
    """Indicates a collision in the command registry."""


def get_function_signature(func: Callable) -> str:
    """Return a string of the function's Python definition, e.g., 'example(arg1: str, arg2: str)'."""

    sig = inspect.signature(func)
    name = func.__name__
    return f"{name}{sig}"


def cli(interface: str | None = None) -> Callable[[Callable[..., None]], Callable[..., None]]:
    """Decorator to register a function as a CLI command.

    Parameters
    ----------
    interface: str
    Command interface string. May contain spaces (e.g. "algebra render"),
    but only the first word is used for dispatch in this minimal version.
    """
    if interface is None:
        interface = ""

    cli_interface = interface.strip()
    if not cli_interface:
        cli_interface = "<no command>"

    key = " ".join(
        [
            token
            for token in shlex.split(cli_interface)
            if "-" not in token and token[0] != "<" and token[-1] != ">"
        ]
    )

    if not key:
        key = "<no command>"

    if key in _REGISTERED_COMMANDS:
        raise CollisionError(
            f"`{interface}` already registered under `{_REGISTERED_COMMANDS[key].help_signature}`"
        )

    def _decorator(func: Callable[[], None]) -> Callable[[], None]:
        func.cli_options: list[str] = _parse_options(shlex.split(cli_interface)).keys()
        func.cli_command: str = key
        func.cli_interface: str = cli_interface
        func.cli_required_params: list[str] = [
            token[1:-1] for token in shlex.split(cli_interface) if token[0] == "<" and token[-1] == ">"
        ]

        func.py_signature = get_function_signature(func)
        func.py_options = {
            param.name: param.default
            for param in inspect.signature(func).parameters.values()
            if param.default is not inspect.Parameter.empty
        }
        func.py_options_annotations = {
            param.name: param.annotation
            for param in inspect.signature(func).parameters.values()
            if param.default is not inspect.Parameter.empty
        }
        params = inspect.signature(func).parameters.values()
        py_required_params = [
            param
            for param in params
            if param.default is inspect.Parameter.empty
            and param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.POSITIONAL_ONLY)
        ]
        func.py_required_params = py_required_params

        func.cli_required_params = (
            " ".join(f"<{param}>" for param in py_required_params) if py_required_params else ""
        )

        func.cli_options = (
            " ".join(f"--{param}={default}" for param, default in func.py_options.items())
            if func.py_options
            else ""
        )

        func.help_signature = f"{func.cli_command if func.cli_command != 'main' else '[red]<no command>[/red]'} {func.cli_options} {func.cli_required_params}".strip()

        _REGISTERED_COMMANDS[key] = func
        return func

    return _decorator


def main(
    passed_args: list[str] | None = None,
    user_config_file: str | Path | None = None,
    default_config_file: str | Path | None = None,
    use_configs: bool = False,
) -> None:
    """
    Parse passed_args and invoke the registered command
    """

    global OPTIONS, _DEBUG, _CONFIG

    main_file = Path(sys.modules["__main__"].__file__)

    new_file_created: bool = False

    if use_configs and default_config_file is None:
        default_config_file = main_file.parent / "cli" / f"{main_file.stem}_config.toml"
        default_config_file.parent.mkdir(parents=True, exist_ok=True)
        default_config_file.touch(exist_ok=True)

    if use_configs and user_config_file is None:
        great_grandparent = (
            f"{main_file.parent.parent.parent.name if main_file.parent.parent.parent.name else 'drive'}"
        )
        grandparent = f"{main_file.parent.parent.name if main_file.parent.parent.name else ''}"

        user_config_file = (
            Path(user_config_dir())
            / "robolson"
            / "cli"
            / "configs"
            / f"{great_grandparent}_{grandparent}_{main_file.parent.name}_{main_file.stem}"
            / f"{main_file.parent.name}_{main_file.stem}_config.toml"
        )
        if not user_config_file.exists():
            rich.print(
                f"[yellow]WARNING:[/yellow] Config file not found ({user_config_file}). Creating new one."
            )
            new_file_created = True

    if use_configs:
        _HARDCODED_OPTIONS.update({"edit_cli_config": False, "open_cli_config": False})

        _CONFIG = TomlConfig(
            user_toml_file=user_config_file, default_toml_file=default_config_file, readonly=True
        )

        if new_file_created:
            with TomlConfig(
                user_toml_file=user_config_file, default_toml_file=default_config_file
            ) as config_writer:
                config_writer["options"] = {}
                config_writer["options"]["capture_output"] = True

        _HARDCODED_OPTIONS.update(_CONFIG.get("options", {}))

    if passed_args is None:
        passed_args = sys.argv[1:]

    passed_command = []
    for token in passed_args:
        if token[0] != "-" and token[0] != "<" and token[-1] != ">":
            passed_command.append(token)
        else:
            break

    if not passed_command:
        passed_command = ["<no command>"]

    func = None
    passed_positionals = []

    while func is None and passed_command:
        func = _REGISTERED_COMMANDS.get(" ".join(passed_command), None)
        if func is None:
            passed_positionals.append(passed_command.pop())

    if func is None:
        func = _REGISTERED_COMMANDS.get("<no command>", None)
        if func is None or not func.py_required_params:
            rich.print(
                f"[red]Unknown command: {passed_command[0] if passed_command else '<no command>'}[/red]\n"
            )
            _print_usage()
            sys.exit(1)

    if OPTIONS.get("help", False) or OPTIONS.get("h", False):
        if passed_command != ["<no command>"]:
            _print_usage(func, passed_command)
        else:
            _print_usage()
        sys.exit(0)

    if use_configs and OPTIONS.get("edit_cli_config", False):
        with TomlConfig(
            user_toml_file=user_config_file, default_toml_file=default_config_file
        ) as config_writer:
            config_writer.edit_in_terminal()
        sys.exit(0)

    if use_configs and OPTIONS.get("open_cli_config", False):
        with TomlConfig(
            user_toml_file=user_config_file, default_toml_file=default_config_file
        ) as config_writer:
            config_writer.open_with_editor()
        sys.exit(0)

    if len(passed_positionals) > len(func.py_required_params):
        if passed_command != ["<no command>"]:
            excess_params = passed_positionals[: len(passed_positionals) - len(func.py_required_params)]
            rich.print(
                f"[red]Too many positional arguments: {f', '.join(excess_param.name for excess_param in excess_params)}[/red]\n"
            )
            _print_usage(func, passed_command)
        else:
            _print_usage()
        sys.exit(1)
    elif len(passed_positionals) < len(func.py_required_params):
        missing_params = list(func.py_required_params)[len(passed_positionals) :]
        rich.print(
            f"[red]Missing required positional arguments: {', '.join(missing_param.name for missing_param in missing_params)}[/red]\n"
        )
        _print_usage(func, passed_command)
        sys.exit(1)
    else:
        for i in range(len(passed_positionals)):
            passed_positionals[i] = func.py_required_params[i]._annotation(passed_positionals[i])

    passed_options = _parse_options(passed_args)
    for option, default in func.py_options.items():
        # if option is None:

        if option not in passed_options and option not in OPTIONS:
            passed_options[option] = default
            # if default is None:
            #     passed_options[option] = str
            # else:
            #     passed_options[option] = default
        else:
            if default is None:
                if "str" in str(func.py_options_annotations[option]):
                    opt_type = str
                elif "int" in str(func.py_options_annotations[option]):
                    opt_type = int
                elif "float" in str(func.py_options_annotations[option]):
                    opt_type = float
                elif "bool" in str(func.py_options_annotations[option]):
                    opt_type = bool
                else:
                    opt_type = lambda x: None
            else:
                opt_type = type(default)

            passed_options[option] = opt_type(passed_options[option])

    removed_options = []
    for option in passed_options:
        if func and hasattr(func, "py_options") and option not in func.py_options:
            if option not in _HARDCODED_OPTIONS:
                rich.print(f"[red]Unknown option: {option}[/red]\n")
                _print_usage(func)
                sys.exit(1)
            else:
                removed_options.append(option)
        else:
            if option in func.py_options:
                opt_type = type(func.py_options[option])
                if opt_type is not type(None):
                    passed_options[option] = opt_type(passed_options[option])

    for option in removed_options:
        del passed_options[option]

    if _DEBUG:
        rich.print(
            f"Calling `{func.py_signature}` with parameters: {passed_positionals} and options: {passed_options} and global options: {OPTIONS}"
        )

    # import contextlib
    # import io

    # if _CONFIG.get("capture_output", False):
    #     buf = io.StringIO()
    #     with contextlib.redirect_stdout(buf):
    #         func(*passed_positionals, **passed_options)
    #     output = buf.getvalue()
    #     if output:
    #         print(output, end="")
    # else:
    # func(*passed_positionals, **passed_options)
    if OPTIONS.get("capture_output", False):
        cli_logger.info(
            f"Command:`{' '.join(sys.argv[1:])}`\nFunction:`{func.__name__}`\nParameters:`{passed_positionals}`\nOptions:`{passed_options}`\nGlobal Options:`{OPTIONS}`"
        )

    func(*passed_positionals, **passed_options)


if __name__ == "__main__":
    os.startfile(filepath=cli_log_file)
    sys.exit(0)
