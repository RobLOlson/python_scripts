import os
import pathlib
import tempfile
import threading
from typing import Any, Self

import toml


class TomlDict:
    _lock = threading.Lock()

    def __init__(self, filename: str | pathlib.Path, readonly: bool = False):
        """
        Initialize a TomlDict object.

        Args:
            filename: The path to the TOML file to load.
        """
        self.filename: pathlib.Path = filename
        self.data: dict[str, Any] = {}
        self._closed: bool = False
        self.readonly: bool = readonly
        self.load()

    def __getitem__(self, key):
        self._check_closed()
        return self.data[key]

    def __setitem__(self, key, value):
        self._check_closed()
        self.data[key] = value
        self.sync()

    def __delitem__(self, key):
        self._check_closed()
        del self.data[key]
        self.sync()

    def __contains__(self, key):
        self._check_closed()
        return key in self.data

    def __len__(self):
        self._check_closed()
        return len(self.data)

    def __repr__(self):
        return f'TomlDict("{self.filename}")'

    def __str__(self):
        return str(self.data)

    def __iter__(self):
        self._check_closed()
        return iter(self.data)

    def __enter__(self):
        self._check_closed()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.close()
        self._closed = True

    def _check_closed(self):
        if self._closed:
            raise ValueError("I/O operation on closed file.")

    def _sync(self):  # Separate writing logic
        if self.readonly:
            return
        temp_file = None
        try:
            # Preserve any existing leading comment header or provide a sensible default
            header_lines: list[str] = []
            try:
                if os.path.exists(self.filename):
                    with open(self.filename, "r", encoding="utf-8") as existing_fp:
                        for line in existing_fp:
                            if line.startswith("#") or line.strip() == "":
                                header_lines.append(line)
                                # stop preserving header once we hit first non-comment content
                            else:
                                break
            except Exception:
                # If anything goes wrong reading old header, ignore and continue
                header_lines = []

            # If no header present, add a default header based on known locations
            if not any(l.strip().startswith("#") for l in header_lines):
                header = self._default_header_for_path(str(self.filename))
                if header:
                    header_lines = [header, "\n"]

            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, dir=os.path.dirname(self.filename)
            ) as tf:
                if header_lines:
                    tf.writelines(header_lines)
                toml.dump(self.data, tf)
                temp_file = tf.name
            os.replace(temp_file, self.filename)
            temp_file = None  # Success, no cleanup needed
        except Exception:
            # Clean up temp file if something went wrong
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except OSError:
                    pass  # Ignore cleanup errors
            raise

    @staticmethod
    def _default_header_for_path(path: str) -> str:
        """Return a default header comment for well-known config files.
        The header will indicate which script(s) use the config.
        """
        p = str(path).replace("\\", "/").lower()
        header: str | None = None
        if "/config/clean.toml" in p or "/robolson/clean/config/clean.toml" in p:
            header = "# Used by: rob.clean"
        elif (
            "/config/english/latex_templates.toml" in p
            or "/robolson/english/config/latex_templates.toml" in p
        ):
            header = "# Used by: rob.english (LaTeX templates)"
        elif "/config/english/config.toml" in p or "/robolson/english/config/config.toml" in p:
            header = "# Used by: rob.english"
        elif "/config/homework/config.toml" in p or "/robolson/homework/config.toml" in p:
            header = "# Used by: rob.homework"
        elif "/config/algebra/config.toml" in p or "/robolson/algebra/config.toml" in p:
            header = "# Used by: rob.homework (algebra)"
        elif "/cli/homework_config.toml" in p:
            header = "# Used by: rob.homework via rob.utilities.cli"
        elif "/cli config/night_config.toml" in p or "/cli/night_config.toml" in p:
            header = "# Used by: rob.night via rob.utilities.cli"
        elif "/config/anagram/cli_config.toml" in p:
            header = "# Used by: rob.anagram via rob.utilities.cli"
        elif "/utilities/config/cli/cli.toml" in p or "/utilities/cli/cli_config.toml" in p:
            header = "# Used by: rob.utilities.cli"
        elif "/config/project.toml" in p or "/robolson/project/config/project.toml" in p:
            header = "# Used by: rob.project"
        elif "/config/algebra/latex_templates.toml" in p:
            header = "# Used by: rob.homework (algebra templates)"

        # Generic fallback for CLI-generated user configs like .../cli/configs/<pkg>_<script>_config.toml
        if (not header) and p.endswith("_config.toml"):
            base = os.path.basename(p)
            stem = os.path.splitext(base)[0]
            # try to get '<pkg>_<script>_config'
            if stem.endswith("_config"):
                parts = stem[:-7].split("_")  # drop '_config'
                if len(parts) >= 2:
                    pkg = parts[-2]
                    script = parts[-1]
                    header = f"# Used by: {pkg}.{script} via rob.utilities.cli"

        return header if header else ""

    @classmethod
    def open(cls, filename: str | pathlib.Path) -> Self:
        return cls(filename)

    def get(self, key, default=None) -> Any | None:
        self._check_closed()
        return self.data.get(key, default)

    def items(self):
        self._check_closed()
        return self.data.items()

    def values(self):
        self._check_closed()
        return self.data.values()

    def clear(self) -> None:
        self._check_closed()
        self.data.clear()
        self.sync()

    def update(self, target) -> None:
        if self._check_closed():
            raise ValueError("I/O operation on closed file.")
            return
        self.data.update(target)
        self.sync()

    def keys(self):
        self._check_closed()
        return self.data.keys()

    def pop(self, key, default=None) -> Any:
        self._check_closed()
        value = self.data.pop(key, default)
        self.sync()
        return value

    def popitem(self) -> tuple[Any, Any]:
        self._check_closed()
        key, value = self.data.popitem()
        self.sync()
        return key, value

    def close(self) -> None:
        if not self._closed:
            self.sync()
            self._closed = True

    def sync(self) -> None:
        with self._lock:
            self._sync()

    def load(self) -> None:
        with self._lock:  # acquire lock before reading
            try:
                with open(self.filename, "r") as f:
                    self.data = toml.load(f)
            except FileNotFoundError:
                print(f"Notice: {self.filename} created.")
