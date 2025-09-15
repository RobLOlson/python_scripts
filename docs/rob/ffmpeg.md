rob.ffmpeg — Audio Concatenate and Convert

Summary

Walks folders to concatenate audio files and convert to m4b, preserving metadata. Can also generate the underlying ffmpeg command list without executing.

CLI Usage

Arguments are parsed via `rob.parser.ffmpeg_parser`. Typical flow:

```bash
# Interactive mode to choose path, filetypes, folders, CPUs, and action
python -m rob.ffmpeg

# Non-interactive: operate on a path with filetype(s)
python -m rob.ffmpeg --path /audiobooks --filetype .mp3 --cpus 4

# Generate only the command file instead of executing
python -m rob.ffmpeg --path /audiobooks --filetype .mp3 --command
```

Python API

- `command_only(folder: Path) -> None`
- `concat_and_convert(folder: Path) -> None`
- `interact() -> list[Path]`
- `main() -> None`

Example

```python
from pathlib import Path
from rob.ffmpeg import concat_and_convert

concat_and_convert(Path("/audiobooks/Title"))
```

Notes

- Non-ASCII and certain punctuation in filenames are normalized prior to concatenation.
- Bitrate is inferred from the first input file.

