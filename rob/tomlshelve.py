import toml

try:
    from . import tomldict
except:
    import tomldict


def open(filename):
    return tomldict.TomlDict(filename)
