import pathlib

import appdirs

from .tomldict import TomlDict

# import rich
# import toml


class TomlConfig:
    """Creates a configuration object that reads and writes to a TOML file."""

    def __init__(self, toml_file: str | pathlib.Path):
        toml_file = pathlib.Path(toml_file)
        if toml_file.suffix != ".toml":
            toml_file = toml_file.with_suffix(".toml")
        if toml_file.is_dir():
            toml_file = toml_file.parent / "config" / f"{toml_file.stem}.toml"
        self.base_config_path = pathlib.Path(toml_file)
        self.base_config_path.touch(exist_ok=True)
        self.user_config_path = (
            pathlib.Path(appdirs.user_config_dir())
            / "configs"
            / pathlib.Path(toml_file).stem
            / f"{toml_file.stem}.toml"
        )
        self.user_config_path.parent.mkdir(parents=True, exist_ok=True)
        self.user_config_path.touch(exist_ok=True)
        self.config = TomlDict(self.base_config_path)

    def __getitem__(self, key):
        return self.config[key]

    def __setitem__(self, key, value):
        self.config[key] = value

    def __delitem__(self, key):
        del self.config[key]

    def __contains__(self, key):
        return key in self.config

    def __len__(self):
        return len(self.config)

    def __iter__(self):
        return iter(self.config)

    def __repr__(self):
        return f"TomlConfig({self.base_config_path.stem})"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.config.close()
