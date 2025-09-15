rob.clean — File Organizer CLI

Summary

Organizes files in a directory into archive folders based on configured file type mappings. Provides subcommands for cleaning, isolating large files, uncrowding crowded archives, removing empty directories, and editing configuration.

CLI Usage

- Help:

```bash
python -m rob.clean --help | cat
```

- Organize files in the current directory with interactive approvals:

```bash
python -m rob.clean --target .
```

- Non-interactive full cleanup on a directory:

```bash
python -m rob.clean --yes-all --target /path/to/folder
```

- Subcommands:

```bash
# List available commands
python -m rob.clean --help | cat

# Clean only file placement
python -m rob.clean files --target . --recurse

# Identify and centralize large files
python -m rob.clean archive large --target . --yes-all

# Uncrowd crowded archives by month
python -m rob.clean archive crowded --target . --threshold 30

# Undo last move operations for a directory
python -m rob.clean undo --target .

# Remove empty directories recursively
python -m rob.clean archive empty --target .

# Open log of executed operations
python -m rob.clean log
```

Configuration

- Base config: `rob/config/clean.toml` shipped with the package.
- User config: created at first run under your OS app data directory, typically `~/.local/share/robolson/clean/config/clean.toml`.
- Manage via subcommands:

```bash
# Open user config in default editor
python -m rob.clean config open

# Restore user config from base template
python -m rob.clean config restore

# Add/remove archive categories and extensions
python -m rob.clean config add --new-archive docs
python -m rob.clean config remove --target-archive docs
python -m rob.clean config edit add --target-archive docs --new-extension .pdf
```

Key Functions

- `generate_extension_handler(file_types: dict[str, list[str]]) -> dict[str, str]`
  - Build a mapping of file extensions to archive folder names.

- `associate_files(files: list[Path], root: Path, extension_handler: dict[str, str] | None, default_folder: Path, yes_all: bool) -> dict[Path, Path]`
  - Propose target paths for files based on extension and last-modified date.

- `clean_files(target: Path, recurse: bool, yes_all: bool, exclusions: Path | None) -> None`
  - CLI command. Gathers files and moves them, interactively or non-interactively.

- `identify_large_files(target: Path, yes_all: bool) -> None`
  - CLI command. Locates outliers by size and centralizes them under `large_files`.

- `identify_crowded_archives(target: Path, threshold: int, yes_all: bool) -> None`
  - CLI command. Splits crowded archive folders into monthly subfolders.

Examples

Python API for previewing and executing moves programmatically:

```python
from pathlib import Path
from rob.clean import associate_files, execute_move_commands

files = list(Path('.').glob('*.*'))
targets = associate_files(files=files)
# Preview
for src, dest in targets.items():
    print(f"mv {src} -> {dest}")
# Execute
execute_move_commands(targets, target=Path('.'), yes_all=True)
```

Notes

- Interactive prompts are powered by utilities in `rob.utilities.query`.
- Move operations are logged to an app-data log file and recorded for `undo`.

