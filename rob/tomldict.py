import toml


class TomlDict:
    def __init__(self, filename):
        self.filename = filename
        self.data = {}
        self.load()

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value
        self.sync()

    def __delitem__(self, key):
        del self.data[key]
        self.sync()

    def __contains__(self, key):
        return key in self.data

    def __len__(self):
        return len(self.data)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.sync()

    def keys(self):
        return self.data.keys()

    def sync(self):
        with open(self.filename, "w") as f:
            toml.dump(self.data, f)

    def load(self):
        try:
            with open(self.filename, "r") as f:
                self.data = toml.load(f)
        except FileNotFoundError:
            pass
