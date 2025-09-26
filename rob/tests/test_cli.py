import importlib

import pytest

cli_mod = importlib.import_module("robo.rob.utilities.cli")


@pytest.fixture(autouse=True)
def clean_registry():
    original = dict(cli_mod._COMMANDS)
    cli_mod._COMMANDS.clear()
    try:
        yield
    finally:
        cli_mod._COMMANDS.clear()
        cli_mod._COMMANDS.update(original)


def test_cli_decorator_registration():
    @cli_mod.cli("config")
    def configure_problem_set():
        return "Configured"

    assert "config" in cli_mod._COMMANDS
    assert cli_mod._COMMANDS["config"] is configure_problem_set


def test_main_dispatch(capsys):
    @cli_mod.cli("config")
    def configure_problem_set(user: str = "alice"):
        print(f"Configured {user}")

    cli_mod.main(["config", "--user=alice"])
    captured = capsys.readouterr()
    assert "Configured alice" in captured.out


def test_usage_shows_docstring_first_line(capsys):
    @cli_mod.cli("sample")
    def sample_cmd():
        """Do a sample thing."""
        pass

    with pytest.raises(SystemExit):
        cli_mod.main(["-h"])

    captured = capsys.readouterr()
    assert "Do a sample thing." in captured.out
