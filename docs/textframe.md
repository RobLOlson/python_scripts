textframe — ASCII Framing Helpers

Summary

Utilities for building text-based UI frames, tables, and columns.

Key Types and Functions

- `class Frame`
- `class Panel(hierarchy.Hierarchy)`
- `table(*args)`
- `frame(...)`
- `constrain(text, width)`
- `justify(text, width=-1, height=-1, hJust="left", vJust="top")`
- `columnize(texts=[], width=-1, height=-1, padding=0, frames=True)`
- `parallelize(texts=[], widths=[-1])`

Example

```python
from textframe import frame, table

print(frame("Hello", width=20))
print(table(["A", "B"], [1, 2, 3]))
```

