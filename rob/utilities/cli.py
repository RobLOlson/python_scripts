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
options: Dict[str, str] = {}


def _parse_options(args: list[str]) -> None:
    """Parse CLI options from a list of arguments."""
    global options

    options.clear()
    i = 0
    while i < len(args):
        token = args[i]
        if token.startswith("--"):
            if "=" in token:
                key, value = token[2:].split("=", 1)
                if key:
                    options[key] = value
            else:
                if token[2:4] == "no":
                    no_modifier = True
                    key = token[5:]
                else:
                    no_modifier = False
                    key = token[2:]
                # Support "--key value" form
                if i + 1 < len(args) and not args[i + 1].startswith("-"):
                    options[key] = args[i + 1]
                    i += 1
                else:
                    if no_modifier:
                        options[key] = False
                    else:
                        options[key] = True
        elif token.startswith("-") and len(token) > 1:
            key = token[1:]
            if i + 1 < len(args) and not args[i + 1].startswith("-"):
                options[key] = args[i + 1]
                i += 1
            else:
                options[key] = "true"
        # Ignore additional positional args for this minimal version
        i += 1
    return options


def _print_usage(func: Callable[[], None] | None = None) -> None:
    main_file = Path(sys.modules["__main__"].__file__)
    if func is not None:
        command = func.__name__
    else:
        command = "<command>"
    if main_file.parent == Path.cwd():
        usage = f"python {main_file.name} [yellow]{command}[/yellow]"
    else:
        usage = f"python -m {main_file.stem} [yellow]{command}[/yellow]"
    rich.print(f"Usage: {usage}")

    # Build commands list with first line of docstring when available
    if not _COMMANDS:
        rich.print("Available commands: <none>")
        return
    if func is not None:
        rich.print(f"  [yellow]{func.__name__}[/yellow] - {func.__doc__.strip().split('\n')[0]}")
        return

    rich.print("Available commands:\n")
    for name in sorted(_COMMANDS.keys()):
        func = _COMMANDS[name]
        doc = ""
        if getattr(func, "__doc__", None):
            doc = func.__doc__.strip().split("\n")[0]
        if doc:
            rich.print(f"  [yellow]{name}[/yellow] - {doc}")
        else:
            rich.print(f"  [yellow]{name}[/yellow]")


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

    key = signature.split()[0]

    def _decorator(func: Callable[[], None]) -> Callable[[], None]:
        # Register under the first token only (minimal dispatch)
        _COMMANDS[key] = func
        return func

    return _decorator


def main(argv: list[str] | None = None) -> None:
    """Parse argv and invoke the registered command.

    Only a single positional command is supported in this minimal version.
    """

    args = list(sys.argv[1:] if argv is None else argv)

    if args:
        command = args[0]
    else:
        command = None

    func = _COMMANDS.get(command)

    if "--help" in args:
        _print_usage(func)
        sys.exit(0)

    _parse_options(args)

    if func is None:
        # Run the importing module's main function
        import __main__

        if hasattr(__main__, "main") and callable(__main__.main):
            print("Running main function")
            __main__.main()
            return

        rich.print(f"Unknown command: {command}\n")
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
