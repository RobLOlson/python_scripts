import importlib

import pytest

cli_mod = importlib.import_module("robo.rob.utilities.cli")


@pytest.fixture(autouse=True)
def clean_registry():
    original = dict(cli_mod._REGISTERED_COMMANDS)
    cli_mod._REGISTERED_COMMANDS.clear()
    try:
        yield
    finally:
        cli_mod._REGISTERED_COMMANDS.clear()
        cli_mod._REGISTERED_COMMANDS.update(original)


def test_cli_decorator_registration():
    @cli_mod.cli("config")
    def configure_problem_set():
        return "Configured"

    assert "config" in cli_mod._REGISTERED_COMMANDS
    assert cli_mod._REGISTERED_COMMANDS["config"] is configure_problem_set


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


def test_print_usage_specific_function(capsys):
    """Test _print_usage function when called with a specific function (lines 149-154)."""

    @cli_mod.cli("test_command")
    def test_function(param1: str, param2: int = 42):
        """This is a test function with parameters."""
        pass

    # Call _print_usage with the specific function
    cli_mod._print_usage(test_function)

    captured = capsys.readouterr()
    output = captured.out

    # Verify the output contains the expected formatted information
    assert "test_command" in output
    assert "This is a test function with parameters." in output
    assert "test_function(param1: str, param2: int = 42)" in output
    assert "param1" in output  # Required parameter should be shown
    assert "--param2=42" in output  # Optional parameter with default should be shown


def test_print_usage_function_without_docstring(capsys):
    """Test _print_usage with a function that has no docstring."""

    @cli_mod.cli("no_doc")
    def no_doc_function():
        pass

    # cli_mod._print_usage(no_doc_function)
    with pytest.raises(SystemExit):
        cli_mod.main(["-h"])

    captured = capsys.readouterr()
    output = captured.out

    # Should show fallback text for missing docstring
    assert "no_doc" in output
    assert "(No description)" in output
