rob.homework and rob.algebra — Homework Generators

Summary

Generates LaTeX algebra assignments from a library of problem generators in `rob.algebra.problems`. Supports frequency weighting and interactive selection.

CLI Usage

```bash
# Top-level app
python -m rob.homework

# Algebra app
python -m rob.homework algebra

# Configure problem set weights
python -m rob.homework algebra config

# Render a document (non-interactive)
python -m rob.homework algebra render --assignment-count 3 --problem-count 5 --debug

# Reset frequency weights
python -m rob.homework algebra reset --no-debug
```

Key Types

- `class ProblemCategory`
  - Wraps a problem generator (function) and its weight.

- `class Problem`
  - Represents a single problem and solution pair.

Selected APIs

- `render_latex(assignment_count: int = 1, problem_count: int = 4, debug: bool = False, threshold: int = 0, problem_set=None) -> None`
- `configure_problem_set()` — interactive frequency configuration
- `reset_weights(debug: bool = True)`

Examples

Programmatic generation with a subset of problems:

```python
from rob.homework import render_latex, prepare_globals

prepare_globals()
# Choose subset by name from globals that start with 'generate_'
subset = [g for n, g in globals().items() if callable(g) and n.startswith('generate')][:4]
render_latex(assignment_count=2, problem_count=4, debug=True, problem_set=subset)
```

Notes

- Weights are stored in a user config TOML under your app data directory.
- Problem generator docstrings’ last line is treated as the human-readable description.

