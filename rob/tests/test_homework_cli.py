import importlib
import sys
from types import ModuleType

import toml


def test_homework_module_exposes_app(monkeypatch):
    survey_stub = ModuleType("survey")
    monkeypatch.setitem(sys.modules, "survey", survey_stub)

    mod = importlib.import_module("rob.homework")
    assert hasattr(mod, "app")


def test_help_shows_user_option(monkeypatch):
    # stub survey to avoid interactive import side-effects
    survey_stub = ModuleType("survey")
    monkeypatch.setitem(sys.modules, "survey", survey_stub)

    mod = importlib.import_module("rob.homework")

    from typer.testing import CliRunner

    runner = CliRunner()

    # Avoid Windows console access under pytest capture
    try:
        import click._winconsole as _wc  # type: ignore

        monkeypatch.setattr(_wc, "get_windows_console_stream", lambda *a, **k: None)
    except Exception:
        pass

    result = runner.invoke(mod.app, ["--help"])
    assert result.exit_code == 0
    assert "--user" in result.output


def test_algebra_list_weights_smoke(monkeypatch):
    # stub survey to avoid interactive import side-effects
    survey_stub = ModuleType("survey")
    monkeypatch.setitem(sys.modules, "survey", survey_stub)

    mod = importlib.import_module("rob.homework")

    import os
    from pathlib import Path

    from typer.testing import CliRunner

    runner = CliRunner()

    # Avoid Windows console access under pytest capture
    try:
        import click._winconsole as _wc  # type: ignore

        monkeypatch.setattr(_wc, "get_windows_console_stream", lambda *a, **k: None)
    except Exception:
        pass

    with runner.isolated_filesystem():
        tmp_dir = Path(os.getcwd()) / "_appdata"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        # Patch the exact attribute as imported in homework.py
        monkeypatch.setattr("appdirs.user_data_dir", lambda: str(tmp_dir))

        result = runner.invoke(mod.app, ["algebra", "list", "weights", "--user", "alice"])
        assert result.exit_code == 0, result.output
        assert "Problems start with 1000 weight" in result.output

        save_file = tmp_dir / "robolson" / "algebra" / "config.toml"
        assert save_file.exists()


def test_weights_persist_for_user(monkeypatch):
    # stub survey to avoid interactive import side-effects
    survey_stub = ModuleType("survey")
    monkeypatch.setitem(sys.modules, "survey", survey_stub)

    mod = importlib.import_module("rob.homework")

    import os
    from pathlib import Path

    from typer.testing import CliRunner

    runner = CliRunner()

    try:
        import click._winconsole as _wc  # type: ignore

        monkeypatch.setattr(_wc, "get_windows_console_stream", lambda *a, **k: None)
    except Exception:
        pass

    with runner.isolated_filesystem():
        tmp_dir = Path(os.getcwd()) / "_appdata"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        # monkeypatch.setattr("robo.rob.homework.appdirs.user_data_dir", lambda: str(tmp_dir))
        monkeypatch.setattr("appdirs.user_data_dir", lambda: str(tmp_dir))

        result = runner.invoke(mod.app, ["algebra", "list", "weights", "--user", "alice"])
        assert result.exit_code == 0, result.output

        save_file = tmp_dir / "robolson" / "algebra" / "config.toml"
        assert save_file.exists()
        data = toml.loads(save_file.read_text())
        assert "weights" in data
        assert "alice" in data["weights"]
        assert isinstance(data["weights"]["alice"], dict)
        assert len(data["weights"]["alice"]) > 0


def test_render_produces_tex(monkeypatch):
    # stub survey to avoid interactive import side-effects
    survey_stub = ModuleType("survey")
    monkeypatch.setitem(sys.modules, "survey", survey_stub)

    mod = importlib.import_module("rob.homework")

    import os
    from pathlib import Path

    from typer.testing import CliRunner

    runner = CliRunner()

    try:
        import click._winconsole as _wc  # type: ignore

        monkeypatch.setattr(_wc, "get_windows_console_stream", lambda *a, **k: None)
    except Exception:
        pass

    with runner.isolated_filesystem():
        tmp_dir = Path(os.getcwd()) / "_appdata"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr("appdirs.user_data_dir", lambda: str(tmp_dir))

        result = runner.invoke(
            mod.app,
            [
                "algebra",
                "render",
                "--user",
                "carol",
                "--assignment-count",
                "1",
                "--problem-count",
                "1",
                "--debug",
            ],
        )
        assert result.exit_code == 0, result.output
        produced = list(Path(".").glob("Algebra Homework *.tex"))
        assert produced, "Expected a LaTeX file to be created"


def test_config_algebra_updates_weights(monkeypatch):
    # stub survey to avoid interactive import side-effects
    survey_stub = ModuleType("survey")
    monkeypatch.setitem(sys.modules, "survey", survey_stub)

    mod = importlib.import_module("rob.homework")

    import os
    from pathlib import Path

    from typer.testing import CliRunner

    runner = CliRunner()

    # Avoid Windows console access under pytest capture
    try:
        import click._winconsole as _wc  # type: ignore

        monkeypatch.setattr(_wc, "get_windows_console_stream", lambda *a, **k: None)
    except Exception:
        pass

    # Stub the interactive form to return fixed values for all entries
    def fake_form_from_dict(form, *args, **kwargs):  # type: ignore
        return {k: 111 for k in form.keys()}

    monkeypatch.setattr("rob.homework.query.form_from_dict", fake_form_from_dict)

    with runner.isolated_filesystem():
        tmp_dir = Path(os.getcwd()) / "_appdata"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr("appdirs.user_data_dir", lambda: str(tmp_dir))

        # Run config algebra to trigger configure_problem_set and save
        result = runner.invoke(
            mod.app,
            [
                "config",
                "algebra",
                "--user",
                "dave",
            ],
        )
        assert result.exit_code == 0, result.output

        save_file = tmp_dir / "robolson" / "algebra" / "config.toml"
        assert save_file.exists()
        data = toml.loads(save_file.read_text())
        assert "weights" in data and "dave" in data["weights"]

        # Ensure every known generator has been written with value 111
        for gen in getattr(mod, "_PROBLEM_GENERATORS", []):
            assert data["weights"]["dave"][gen] == 111
