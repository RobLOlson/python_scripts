rob.night — Night Mode Automation (Windows)

Summary

Automates Windows Night Light, dims screen brightness, and lowers system volume on a schedule.

CLI Usage

```bash
# Start loop with defaults (20:00 -> 08:00)
python -m rob.night

# Run once immediately
python -m rob.night --once

# View logs
python -m rob.night log-file
```

Python API

- `class NightLight`: `enable()`, `disable()`, `toggle()`, `enabled() -> bool`
- `dim_audio_video()` — adjusts brightness and volume, enables Night Light
- `set_loop(start_time: str = "20:00", end_time: str = "08:00")`

Notes

- Requires Windows APIs (`wmi`, `pycaw`, registry access). Not portable to non-Windows OS.
- Logs stored under your OS user data directory.

