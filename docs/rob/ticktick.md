rob.ticktick — TickTick Open API Client

Summary

Minimal client and managers to interact with TickTick's API. Core types:

- `OAuth2`: handles auth flow and token caching
- `TickTickClient`: high-level client with `focus`, `habit`, `project`, `pomo`, `settings`, `tag`, `task` managers and local `state`

Authentication

```python
from rob.ticktick.oauth2 import OAuth2
from rob.ticktick.api import TickTickClient

oauth = OAuth2(
    client_id="...",
    client_secret="...",
    redirect_uri="https://localhost/callback",
    cache_path=".ticktoken",
)

client = TickTickClient(username="you@example.com", password="your-password", oauth=oauth)
```

Core APIs

- `TickTickClient.sync()` populates `client.state` with `projects`, `project_folders`, `tasks`, `tags`, `user_settings`, `profile`.
- Query helpers:
  - `get_by_fields(search: str | None = None, **kwargs) -> dict | list`
  - `get_by_id(obj_id: str, search: str | None = None) -> dict`
  - `get_by_etag(etag: str, search: str | None = None) -> dict`
  - `delete_from_local_state(search: str | None = None, **kwargs) -> dict`

HTTP helpers

- `http_get`, `http_post`, `http_put`, `http_delete` — thin wrappers around the session; raise on non-200.

Utility parsers

- `parse_id(response: dict) -> str`
- `parse_etag(response: dict, multiple: bool = False) -> str | list[str]`

Examples

List all projects and tasks:

```python
for proj in client.state["projects"]:
    print(proj["name"], proj["id"]) 

for task in client.state["tasks"]:
    print(task["title"], task.get("projectId"))
```

Find a task by title:

```python
todo = client.get_by_fields(title="Buy milk", search="tasks")
print(todo)
```

Notes

- See `OAuth2` docstrings for environment and cache token strategies.
- Managers under `rob.ticktick.managers.*` provide typed operations per domain.

