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
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Callable, Dict

import rich
from appdirs import user_data_dir

_DEBUG = False

cli_log_dir = Path(user_data_dir()) / "robolson" / "cli" / "logs"
cli_log_dir.mkdir(parents=True, exist_ok=True)
cli_log_file = cli_log_dir / "cli.log"

logger = logging.getLogger()

logger.setLevel(logging.INFO)

handler = RotatingFileHandler(filename=cli_log_file.absolute(), maxBytes=100_000, backupCount=2)
formatter = logging.Formatter("%(message)s")

handler.setFormatter(formatter)
logger.addHandler(handler)

if cli_log_file.stat().st_size > 2 * 1024 * 1024:
    with open(cli_log_file, "r") as fp:
        half_log = fp.readlines()
        half_log = half_log[int(len(half_log) / 2) :]
    with open(cli_log_file, "w") as fp:
        fp.writelines(half_log)

# Global command registry mapping first token -> function
_COMMANDS: Dict[str, Callable[[], None]] = {}

# Parsed CLI options for the last invocation (e.g., {"user": "alice"})
options: Dict[str, str | bool] = {}
positionals: list[str] = []


class CollisionError(Exception):
    """Indicates a collision in the command registry."""


def _parse_options(raw_args: list[str]) -> Dict[str, str | bool]:
    """Parse CLI options from a list of arguments."""
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
        i += 1

    return opts


def get_function_signature(func: Callable) -> str:
    """Return a string of the function's Python definition, e.g., 'example(arg1: str, arg2: str)'."""

    sig = inspect.signature(func)
    name = func.__name__
    return f"{name}{sig}"


def _print_usage(func: Callable[[], None] | None = None) -> None:
    main_file = Path(sys.modules["__main__"].__file__)
    help_lines: list[str] = []

    if func is None or func.__name__ == "main":
        command_lengths = [
            len(getattr(target_func, "interface", "[red]<no command>[/red]"))
            for target_func in _COMMANDS.values()
        ]
        if not command_lengths:
            rich.print("[red]No commands found[/red]")
            return

        longest_command = max(command_lengths if command_lengths else [0])
        for command, target_func in _COMMANDS.items():
            command_example = (
                f"{getattr(target_func, 'help_signature', '[red]<no command>[/red]'): <{longest_command}}"
            )
            command_example = command_example.removesuffix("main")
            command_example = command_example.replace("main ", "[red]<no command> [/red]")
            description = f"{target_func.__doc__.strip().split('\n')[0] if target_func.__doc__ else '[red](No description)[/red]'}"
            py_signature = f"`{getattr(target_func, 'py_signature', f'{target_func.__name__}(...)')}`"
            help_lines.append(f"{command_example}\n    {description}\n      {py_signature}\n")
        command = "<command>"
        help_lines.sort()
    else:
        command = func.cli_command

    if main_file.parent == Path.cwd():
        usage = f"python {main_file.name} [yellow]{command}[/yellow]"
    else:
        usage = f"python -m {main_file.stem} [yellow]{command}[/yellow]"
    rich.print(f"Usage: {usage}\n")

    if func is None or func.__name__ == "main":
        rich.print("Available commands:\n")
        for help_line in help_lines:
            rich.print(f"  {help_line}")
    else:
        cli_interface = f"{getattr(func, 'help_signature', '[red]<no command>[/red]')}"
        description = f"{getattr(func, '__doc__', '[red](No description)[/red]')}"
        py_signature = f"`{getattr(func, 'py_signature', '[red]<no command>[/red]')}`"

        rich.print(f"  {cli_interface}\n    {description}\n      {py_signature}\n")
        return

    # rich.print("Available commands:\n")
    # for name in sorted(_COMMANDS.keys()):
    #     func = _COMMANDS[name]
    #     doc = ""
    #     if getattr(func, "__doc__", None):
    #         doc = func.__doc__.strip().split("\n")[0]
    #     if doc:
    #         rich.print(f"  [yellow]{name}[/yellow] - {doc}")
    #     else:
    #         rich.print(f"  [yellow]{name}[/yellow]")


def cli(interface: str) -> Callable[[Callable[[], None]], Callable[[], None]]:
    """Decorator to register a function as a CLI command.

    Parameters
    ----------
    interface: str
    Command interface string. May contain spaces (e.g. "algebra render"),
    but only the first word is used for dispatch in this minimal version.
    """

    cli_interface = interface.strip()
    if not cli_interface:
        cli_interface = "main"
        # raise ValueError("cli interface must be a non-empty string")

    # key = cli_interface.split()[0]
    key = " ".join(
        [
            token
            for token in shlex.split(cli_interface)
            if "-" not in token and token[0] != "<" and token[-1] != ">"
        ]
    )

    if not key:
        key = "main"

    if key in _COMMANDS:
        raise CollisionError(f"`{interface}` already registered under `{_COMMANDS[key].help_signature}`")

    def _decorator(func: Callable[[], None]) -> Callable[[], None]:
        # Register under the first token only (minimal dispatch)
        # func.options = [token.removeprefix("--") for token in shlex.split(cli_interface) if "-" in token]

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

        params = inspect.signature(func).parameters.values()
        py_required_params = [
            param.name
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

        _COMMANDS[key] = func
        return func

    return _decorator


def main(passed_args: list[str] | None = None) -> None:
    """Parse passed_args and invoke the registered command.

    If passed_args is not provided, sys.argv[1:] is used.
    """

    global options, _DEBUG

    if passed_args is None:
        passed_args = sys.argv[1:]

    passed_command = []
    for token in passed_args:
        if token[0] != "-" and token[0] != "<" and token[-1] != ">":
            passed_command.append(token)
        else:
            break

        # passed_command = [
        #     token for token in passed_args if "-" not in token and token[0] != "<" and token[-1] != ">"
        # ]

    if not passed_command:
        passed_command = ["main"]

    if "main" in passed_command and "main" not in _COMMANDS.keys():
        import __main__

        if hasattr(__main__, "main") and callable(__main__.main):
            _COMMANDS["main"] = __main__.main

        if not _COMMANDS:
            _print_usage()
            sys.exit(1)

    func = None
    passed_positionals = []

    while func is None and passed_command:
        func = _COMMANDS.get(" ".join(passed_command), None)
        if func is None:
            passed_positionals.append(passed_command.pop())

    if func is None:
        func = _COMMANDS.get("main", None)

    if "--help" in passed_args or "-h" in passed_args:
        _print_usage(func)
        sys.exit(0)

    if len(passed_positionals) > len(func.py_required_params):
        rich.print(f"[red]Too many positional arguments: {', '.join(passed_positionals)}[/red]\n")
        _print_usage(func)
        sys.exit(1)
    elif len(passed_positionals) < len(func.py_required_params):
        rich.print(
            f"[red]Missing required positional arguments: {', '.join(func.cli_required_params)}[/red]\n"
        )
        _print_usage(func)
        sys.exit(1)
    else:
        for i in range(len(passed_positionals)):
            pos_type = type(func.py_required_params[i])
            passed_positionals[i] = pos_type(passed_positionals[i])

    passed_options = _parse_options(passed_args)
    # options = {option: passed_options[option] for option in passed_options}

    #
    if "debug" in passed_options and "debug" not in func.py_options:
        del passed_options["debug"]
        _DEBUG = True

    for option, default in func.py_options.items():
        if option not in passed_options:
            passed_options[option] = default
        else:
            opt_type = type(default)
            passed_options[option] = opt_type(passed_options[option])

    for option in passed_options:
        # if option == "debug" and "debug" not in func.py_options:
        #     del passed_options[option]
        #     continue

        if func and hasattr(func, "py_options") and option not in func.py_options:
            rich.print(f"[red]Unknown option: {option}[/red]\n")
            _print_usage(func)
            sys.exit(1)
        else:
            opt_type = type(func.py_options[option])
            if opt_type is not type(None):
                passed_options[option] = opt_type(passed_options[option])

    if func is None:
        rich.print(f"[red]Unknown command: {passed_args[0]}[/red]\n")
        _print_usage()
        sys.exit(1)

    # Call registered function (no positional args passed; read from cli.options)
    if _DEBUG:
        rich.print(
            f"Calling {func.__name__} with parameters: {passed_positionals} and options: {passed_options}"
        )

    func(*passed_positionals, **passed_options)
    logger.info(f"{' '.join(sys.argv)}: {func.__name__}")


if __name__ == "__main__":
    os.startfile(filepath=cli_log_file)
    sys.exit(0)
