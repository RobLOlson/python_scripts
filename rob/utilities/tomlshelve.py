try:
    # from . import tomldict
    from tomldict import TomlDict
except ImportError:
    from .tomldict import TomlDict


def open(filename: str) -> TomlDict:
    """Takes a .toml and returns a dictionary that reflects its structure and contents."""

    return TomlDict(filename)
