import toml

from . import tomldict


def open(filename):
    return tomldict.TomlDict(filename)
