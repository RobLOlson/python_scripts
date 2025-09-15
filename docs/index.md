Robolson Utilities Documentation

Overview

This repository provides a collection of Python utilities and CLI tools grouped under the package `rob`. Major areas include:

- Cleaning and organizing files (`rob.clean`)
- TickTick API client (`rob.ticktick`)
- FFmpeg helpers for audio workflows (`rob.ffmpeg`)
- English reading assignment generation with LLMs (`rob.english`)
- Algebra homework generators (`rob.homework` and `rob.algebra`)
- Project scaffolding (`rob.project`)
- Terminal approval/edit widgets (`rob.utilities.query`)
- Lightweight TOML-backed key/value store and config helpers (`rob.utilities.tomldict`, `rob.utilities.tomlconfig`)
- Windows night mode automation (`rob.night`)

Installation

- Ensure Python 3.10+ is available.
- From a clone of this repository:

```bash
pip install -r requirements.txt
```

Quickstart

- List available scripts:

```bash
python -m rob
```

- Run any tool as a module, for example cleaning a folder non-interactively:

```bash
python -m rob.clean --yes-all --target .
```

API and CLI Reference

- Cleaning and archiving: see `rob/clean.md`
- Utilities (TOML, configs, terminal UI): see `rob/utilities.md`
- TickTick API client: see `rob/ticktick.md`
- FFmpeg helpers: see `rob/ffmpeg.md`
- English generator: see `rob/english.md`
- Algebra generator: see `rob/homework.md`
- Project scaffolding: see `rob/project.md`
- Windows night automation: see `rob/night.md`
- Text framing helpers: see `textframe.md`
- Misc tools (anagram, reddit archive): see `rob/anagram.md`, `rob/reddit_archive.md`

Conventions

- Deprecated modules in `rob/deprecated/` are not covered here.
- All examples assume the repository root as the working directory.

