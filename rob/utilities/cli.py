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

import logging
import os
import shlex
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Callable, Dict

import rich
from appdirs import user_data_dir

log_dir = Path(user_data_dir()) / "robolson" / "cli" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "cli.log"

logger = logging.getLogger()

logger.setLevel(logging.INFO)

handler = RotatingFileHandler(filename=log_file.absolute(), maxBytes=100_000, backupCount=2)
formatter = logging.Formatter("%(message)s")

handler.setFormatter(formatter)
logger.addHandler(handler)

if log_file.stat().st_size > 2 * 1024 * 1024:
    with open(log_file, "r") as fp:
        half_log = fp.readlines()
        half_log = half_log[int(len(half_log) / 2) :]
    with open(log_file, "w") as fp:
        fp.writelines(half_log)

# Global command registry mapping first token -> function
_COMMANDS: Dict[str, Callable[[], None]] = {}

# Parsed CLI options for the last invocation (e.g., {"user": "alice"})
options: Dict[str, str | bool] = {}


def _parse_options(args: list[str]) -> Dict[str, str | bool]:
    """Parse CLI options from a list of arguments."""
    # options.clear()
    i = 0

    while i < len(args):
        token = args[i]
        if token.startswith("--"):
            if "=" in token:
                key, value = token[2:].split("=", 1)
                if key:
                    options[key] = value
            else:
                if token[2:5] == "no-":
                    key = token[5:]
                    options[key] = False
                else:
                    key = token[2:]
                    options[key] = True
        i += 1

    return options


def get_function_signature(func: Callable) -> str:
    """Return a string of the function's Python definition, e.g., 'example(arg1: str, arg2: str)'."""
    import inspect

    sig = inspect.signature(func)
    name = func.__name__
    return f"{name}{sig}"


def _print_usage(func: Callable[[], None] | None = None) -> None:
    main_file = Path(sys.modules["__main__"].__file__)
    help_lines: list[str] = []

    if func is None or func.__name__ == "main":
        command_lengths = [
            len(getattr(target, "signature", "[red]<no command>[/red]")) for target in _COMMANDS.values()
        ]
        if not command_lengths:
            rich.print("[red]No commands found[/red]")
            return

        longest_command = max(command_lengths if command_lengths else [0])
        for command, target in _COMMANDS.items():
            command_example = f"{getattr(target, 'signature', '[red]<no command>[/red]'): <{longest_command}}"
            command_example = command_example.removesuffix("main")
            command_example = command_example.replace("main ", "[red]<no command> [/red]")
            description = f"{target.__doc__.strip().split('\n')[0] if target.__doc__ else '[red](No description)[/red]'}"
            python_signature = f"`{get_function_signature(target)}`"
            help_lines.append(f"{command_example}\n    {description}\n      {python_signature}\n")
        command = "<command>"
        help_lines.sort()
    else:
        command = func.command

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
        command_example = f"{getattr(func, 'signature', '[red]<no command>[/red]')}"
        description = f"{getattr(func, '__doc__', '[red](No description)[/red]').strip().split('\n')[0]}"
        python_signature = f"`{get_function_signature(func)}`"
        rich.print(f"  {command_example}\n    {description}\n      {python_signature}\n")
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


def cli(signature: str) -> Callable[[Callable[[], None]], Callable[[], None]]:
    """Decorator to register a function as a CLI command.

    Parameters
    ----------
    signature: str
                    Command signature string. May contain spaces (e.g. "algebra render"),
                    but only the first word is used for dispatch in this minimal version.
    """

    signature = signature.strip()
    if not signature:
        raise ValueError("cli signature must be a non-empty string")

    # key = signature.split()[0]
    key = " ".join([token for token in shlex.split(signature) if "-" not in token])

    def _decorator(func: Callable[[], None]) -> Callable[[], None]:
        # Register under the first token only (minimal dispatch)
        # func.options = [token.removeprefix("--") for token in shlex.split(signature) if "-" in token]

        func.options = _parse_options(shlex.split(signature)).keys()
        func.command = key
        func.signature = signature
        _COMMANDS[key] = func
        return func

    return _decorator


def main(argv: list[str] | None = None) -> None:
    """Parse argv and invoke the registered command.

    Only a single positional command is supported in this minimal version.
    """

    global options

    if "main" not in _COMMANDS.keys():
        import __main__

        if hasattr(__main__, "main") and callable(__main__.main):
            _COMMANDS["main"] = __main__.main

        if not _COMMANDS:
            _print_usage()
            sys.exit(1)

    args = list(sys.argv[1:] if argv is None else argv)
    if args:
        command = " ".join([token for token in args if "-" not in token])
    else:
        command = "main"

    if not command:
        command = "main"

    func = _COMMANDS.get(command)

    if "--help" in args or "-h" in args:
        _print_usage(func)
        sys.exit(0)
        # if func.__name__ == "main":
        #     _print_usage()
        #     sys.exit(0)
        # else:
        #     _print_usage(func)
        #     sys.exit(0)

    options = _parse_options(args)

    for option in options:
        if func and hasattr(func, "options") and option not in func.options:
            rich.print(f"[red]Unknown option: {option}[/red]\n")
            _print_usage(func)
            sys.exit(1)
    if func is None:
        # Run the importing module's main function

        rich.print(f"[red]Unknown command: {command}[/red]\n")
        _print_usage()
        sys.exit(1)

    # Parse remaining args into options dict.

    # Call registered function (no positional args passed; read from cli.options)
    func()
    logger.info(f"{' '.join(sys.argv)}: {func.__name__}")


if __name__ == "__main__":
    options = _parse_options(sys.argv)
    if options.get("log_file", False):
        os.startfile(log_file)
