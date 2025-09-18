rob.reddit_archive — Reddit CSV Utilities

Summary

Helpers for parsing a Reddit export CSV and generating text output.

Python API

- `parse_csv(csv_file: pathlib.Path)`
- `generate_text()`
- `main()`

Example

```python
from pathlib import Path
from rob.reddit_archive import parse_csv

posts = parse_csv(Path("reddit_export.csv"))
```

