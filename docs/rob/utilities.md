rob.utilities — Helpers

Summary

Reusable building blocks for interactive terminal selection/editing and TOML-backed storage/configuration.

`rob.utilities.query`

- `approve_list(target: list[Any], repr_func=None, maximum: int | None = None, preamble: bool | None = None, default_yes: bool = False) -> list[Any]`
  - Interactive list approval. Use number keys, arrows, and Enter. Returns selected items.

- `select(target: list[Any], preamble: bool = False, repr_func=None) -> Any`
  - Single-selection convenience wrapper around `approve_list`.

- `approve_dict(target: dict[Any, Any], preamble: str = "", repr_func=None, maximum: int | None = None) -> dict[Any, Any]`
  - Interactive dictionary approval. Returns filtered dictionary.

- `linearize_complex_object(object: list | dict, depth: int = 0) -> list[tuple[Any, int, type]]`, `reconstitute_object(...)`
  - Convert nested structures to a linear editable form and back.

- `edit_object(target, preamble: str = "", repr_func=None, show_brackets: bool = True, edit_keys: bool = True, dict_inline: bool = False)`
  - Interactive inline editor for nested lists/dicts.

- `confirm(default: bool = False) -> bool`, `form_from_dict(target: dict[str, str | int | float | bool]) -> dict`
  - Simple confirmation and quick forms.

Examples

```python
from rob.utilities import query

choice = query.select(["apples", "bananas", "cherries"])  # returns one string
approved = query.approve_list([1,2,3,4], maximum=2)           # returns subset

data = {"x": 1, "y": 2}
filtered = query.approve_dict(data)                           # subset dict

profile = {"name": "Ada", "age": 30}
edited = query.form_from_dict(profile)                        # inline edit
```

`rob.utilities.tomldict`

- `class TomlDict`
  - TOML-backed dict-like store with file-level locking and atomic writes.
  - Core API: `open`, `get`, `items`, `values`, `keys`, `update`, `clear`, `pop`, `popitem`, `close`, context manager support.

Example

```python
from rob.utilities.tomldict import TomlDict

with TomlDict.open("settings.toml") as db:
    db["theme"] = "dark"
    print(db.get("theme", "light"))
```

`rob.utilities.tomlconfig`

- `class TomlConfig`
  - Manages a base config TOML and a per-user config location. Exposes a dict-like interface via `TomlDict`.

Example

```python
from rob.utilities.tomlconfig import TomlConfig

cfg = TomlConfig("myapp/config.toml")
cfg["ui"] = {"theme": "dark"}
print("ui" in cfg, len(cfg))
```

`rob.utilities.perf_timer`

- `perf_timer(debug: bool = False)`
  - Decorator factory; when `debug=True`, prints elapsed time for the wrapped function.

Example

```python
from rob.utilities.perf_timer import perf_timer

@perf_timer(debug=True)
def compute():
    ...
```

