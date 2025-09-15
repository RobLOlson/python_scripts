rob.english — Reading Assignment Generator

Summary

Creates LaTeX reading assignments and comprehension questions. Uses OpenAI or Google Gemini for question generation, configurable via user config and environment.

Setup

- Ensure API keys are set:

```bash
export OPENAI_API_KEY=...     # optional
export GOOGLE_AI_KEY=...      # optional
```

- First run will create user config and templates under your app data directory.

CLI Usage

```bash
# Guided setup and generation
python -m rob.english

# Ingest a text file (see docstring for required format)
python -m rob.english ingest book.txt

# Generate pages (debug writes sample LaTeX file)
python -m rob.english generate --target book.txt --n 5 --debug

# Configure provider and prompt
python -m rob.english config model
python -m rob.english config prompt
python -m rob.english config creds

# List data
python -m rob.english list books
python -m rob.english list reviews --book book.txt
```

Python API Highlights

- `ingest_text_file(target: str, chars_per_page: int = 5_000, debug: bool = False)`
- `generate_pages(target: str | None, n: int = 7, debug: bool = True, start_date: datetime, review: bool = True)`
- `fetch_LLM_output(model: str, system_instruction: str, prompt: str) -> list[dict]`

Example

```python
from rob.english import ingest_text_file, generate_pages

ingest_text_file("book.txt")
generate_pages(target="book.txt", n=3, debug=True)
```

Notes

- LaTeX templates and user config live under `~/.local/share/robolson/english/` (platform-specific).
- When `debug=False`, outputs are persisted and progress advances automatically.

