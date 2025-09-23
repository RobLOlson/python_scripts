import importlib
import os
import sys
from pathlib import Path
from types import ModuleType

import toml
from typer.testing import CliRunner

runner = CliRunner()


def _install_survey_stub(monkeypatch):
    survey_stub = ModuleType("survey")

    class _Routines:
        @staticmethod
        def datetime(prompt: str, attrs=("month", "day", "year")):
            return None

        @staticmethod
        def numeric(prompt: str, decimal=False, value=None):
            return value

    survey_stub.routines = _Routines()
    monkeypatch.setitem(sys.modules, "survey", survey_stub)


def _load_homework(monkeypatch):
    _install_survey_stub(monkeypatch)
    return importlib.import_module("robo.rob.homework")


def _save_file_path(tmp_dir: Path) -> Path:
    # Mirrors homework.py: appdirs.user_data_dir()/"robolson"/"algebra"/"config.toml"
    return tmp_dir / "robolson" / "algebra" / "config.toml"


def test_list_weights_with_user(monkeypatch):
    with runner.isolated_filesystem():
        tmp_dir = Path(os.getcwd()) / "_appdata"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        hw = _load_homework(monkeypatch)
        # Monkeypatch user_data_dir to our isolated path
        monkeypatch.setattr(hw.appdirs, "user_data_dir", lambda: str(tmp_dir))

        result = runner.invoke(hw.app, ["algebra", "list", "weights", "--user", "alice"])
        assert result.exit_code == 0, result.output

        save_file = _save_file_path(tmp_dir)
        assert save_file.exists(), "Expected config file to be created"

        data = toml.loads(save_file.read_text())
        # Ensure per-user weights mapping exists
        assert "weights" in data
        assert "alice" in data["weights"]


def test_list_weights_default_user(monkeypatch):
    with runner.isolated_filesystem():
        tmp_dir = Path(os.getcwd()) / "_appdata"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        hw = _load_homework(monkeypatch)
        monkeypatch.setattr(hw.appdirs, "user_data_dir", lambda: str(tmp_dir))

        result = runner.invoke(hw.app, ["algebra", "list", "weights"])  # no --user
        assert result.exit_code == 0, result.output

        save_file = _save_file_path(tmp_dir)
        assert save_file.exists()

        data = toml.loads(save_file.read_text())
        # Fallback default user from fallback config is "default"
        assert data.get("default_user", "default") == "default"
        # Ensure default weight bucket present
        assert "weights" in data
        assert "default" in data["weights"]


def test_algebra_render_with_user(monkeypatch):
    with runner.isolated_filesystem():
        tmp_dir = Path(os.getcwd()) / "_appdata"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        hw = _load_homework(monkeypatch)
        monkeypatch.setattr(hw.appdirs, "user_data_dir", lambda: str(tmp_dir))

        # Keep the output small and avoid saving weights by using --debug
        result = runner.invoke(
            hw.app,
            [
                "algebra",
                "render",
                "--user",
                "bob",
                "--assignment-count",
                "1",
                "--problem-count",
                "1",
                "--debug",
            ],
        )
        assert result.exit_code == 0, result.output
        # Confirm a .tex file was produced
        produced = list(Path(".").glob("Algebra Homework *.tex"))
        assert produced, "Expected a LaTeX file to be created"


