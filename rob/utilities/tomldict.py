import os
import pathlib
import tempfile
import threading

import toml


class TomlDict:
    _lock = threading.Lock()

    def __init__(self, filename: str | pathlib.Path):
        self.filename = filename
        self.data = {}
        self._closed = False
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
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, dir=os.path.dirname(self.filename)
        ) as tf:
            toml.dump(self.data, tf)
        os.replace(tf.name, self.filename)

    @classmethod
    def open(cls, filename):
        return cls(filename)

    def get(self, key, default=None):
        self._check_closed()
        return self.data.get(key, default)

    def items(self):
        self._check_closed()
        return self.data.items()

    def values(self):
        self._check_closed()
        return self.data.values()

    def clear(self):
        self._check_closed()
        self.data.clear()
        self.sync()

    def update(self, target):
        self._check_closed()
        self.data.update(target)
        self.sync()

    def keys(self):
        self._check_closed()
        return self.data.keys()

    def pop(self, key, default=None):
        self._check_closed()
        value = self.data.pop(key, default)
        self.sync()
        return value

    def popitem(self):
        self._check_closed()
        key, value = self.data.popitem()
        self.sync()
        return key, value

    def close(self):
        if not self._closed:
            self.sync()
            self._closed = True

    def sync(self):
        with self._lock:
            self._sync()

    def load(self):
        with self._lock:  # acquire lock before reading
            try:
                with open(self.filename, "r") as f:
                    self.data = toml.load(f)
            except FileNotFoundError:
                print(f"Notice: {self.filename} created.")
