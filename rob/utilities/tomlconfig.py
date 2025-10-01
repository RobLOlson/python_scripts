import os
import pathlib

import toml

from . import query
from .tomldict import TomlDict

# import toml


class TomlConfig:
    """Creates a configuration object that reads and writes to a TOML file."""

    def __init__(
        self,
        user_toml_file: str | pathlib.Path,
        default_toml_file: str | pathlib.Path | None = None,
        readonly: bool = False,
    ):
        self.readonly = readonly
        if default_toml_file is not None:
            default_toml_file = pathlib.Path(default_toml_file)
            default_toml_file.parent.mkdir(parents=True, exist_ok=True)
            default_toml_file.touch(exist_ok=True)
            default_dict = toml.load(default_toml_file)
            self.default_config_path = default_toml_file
        else:
            default_dict = {}
            self.default_config_path = None

        user_toml_file = pathlib.Path(user_toml_file)
        self.user_config_path = pathlib.Path(user_toml_file)
        self.user_config_path.parent.mkdir(parents=True, exist_ok=True)
        self.user_config_path.touch(exist_ok=True)
        self.config = TomlDict(self.user_config_path, readonly=readonly)
        default_dict.update(self.config)
        self.config.update(default_dict)

    def __getitem__(self, key):
        return self.config[key]

    def __setitem__(self, key, value):
        if self.readonly:
            raise PermissionError("Cannot edit config: TomlConfig is in readonly mode.")
            return
        self.config.update({key: value})
        # self.config[key] = value

    def __delitem__(self, key):
        if self.readonly:
            raise PermissionError("Cannot edit config: TomlConfig is in readonly mode.")
            return
        del self.config[key]

    def __contains__(self, key):
        return key in self.config

    def __len__(self):
        return len(self.config)

    def __iter__(self):
        return iter(self.config)

    def __repr__(self):
        return f"TomlConfig('{self.user_config_path.name}')"

    def __str__(self):
        return str(self.config)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.config.close()

    def get(self, key, default=None):
        return self.config.get(key, default)

    def items(self):
        return self.config.items()

    def values(self):
        return self.config.values()

    def keys(self):
        return self.config.keys()

    def update(self, target):
        if self.readonly:
            raise PermissionError("Cannot edit config: TomlConfig is in readonly mode.")
            return
        self.config.update(target)

    def clear(self):
        if self.readonly:
            raise PermissionError("Cannot edit config: TomlConfig is in readonly mode.")
            return
        self.config.clear()

    def pop(self, key, default=None):
        if self.readonly:
            raise PermissionError("Cannot edit config: TomlConfig is in readonly mode.")
            return
        return self.config.pop(key, default)

    def sync(self):
        if self.readonly:
            raise PermissionError("Cannot edit config: TomlConfig is in readonly mode.")
            return
        self.config.sync()

    def open_with_editor(self):
        os.startfile(self.user_config_path)

    def edit_in_terminal(self):
        if self.readonly:
            raise PermissionError("Cannot edit config: TomlConfig is in readonly mode.")
            return

        self.config.data = query.edit_object(dict(self.config))
        self.config.sync()
