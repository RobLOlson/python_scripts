rob.project — Project Scaffolding

Summary

Interactive utility to bootstrap a Python project with optional features (logging, typer CLI, git hooks, TOML-based config, etc.).

CLI Usage

```bash
python -m rob.project --name my_project --directory . --interact
```

- Opens prompts to choose features and options.
- Creates a project folder with main module and optional feature files from Jinja templates in `rob/config/project/`.

Python API

- `default(project_name: str = "my_project", directory: str | None = None, add_feature: list[Feature] = [], remove_feature: list[Feature] = [], multiple_files: bool = False, interact: bool = True)`

Enums

- `Feature`: `LOGGING`, `TYPER`, `GIT`, `GIT_HOOKS`, `TOML_CONFIG`, `POETRY`, `DATABASE`
- `Option`: `MULTIPLE_FILES`

Example

```python
from rob.project import default, Feature

default(
  project_name="awesome_tool",
  directory="/tmp",
  add_feature=[Feature.TYPER, Feature.TOML_CONFIG],
  multiple_files=True,
  interact=False,
)
```

