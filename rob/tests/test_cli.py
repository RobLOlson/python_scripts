import importlib
from pathlib import Path

import pytest
import sys
from types import ModuleType
import pathlib

# Ensure optional dependency 'rich' is available for the CLI module
if "rich" not in sys.modules:
    rich_stub = ModuleType("rich")
    def _rprint(*args, **kwargs):
        print(*args, **kwargs)
    setattr(rich_stub, "print", _rprint)
    sys.modules["rich"] = rich_stub

# Provide a minimal 'appdirs' shim to satisfy CLI imports
if "appdirs" not in sys.modules:
    appdirs_stub = ModuleType("appdirs")
    def _user_config_dir():
        return str(pathlib.Path("/workspace/_appdata/config").absolute())
    def _user_data_dir():
        return str(pathlib.Path("/workspace/_appdata/data").absolute())
    setattr(appdirs_stub, "user_config_dir", _user_config_dir)
    setattr(appdirs_stub, "user_data_dir", _user_data_dir)
    sys.modules["appdirs"] = appdirs_stub

# Support running tests against the local workspace layout
try:
    cli_mod = importlib.import_module("robo.rob.utilities.cli")
except ModuleNotFoundError:
    try:
        cli_mod = importlib.import_module("rob.utilities.cli")
    except ModuleNotFoundError:
        # Construct a temporary package for relative imports to work
        import importlib.util
        import sys
        import pathlib
        # Create pseudo-packages
        if "rob" not in sys.modules:
            rob_pkg = ModuleType("rob")
            rob_pkg.__path__ = ["/workspace/rob"]  # type: ignore[attr-defined]
            sys.modules["rob"] = rob_pkg
        if "rob.utilities" not in sys.modules:
            utilities_pkg = ModuleType("rob.utilities")
            utilities_pkg.__path__ = ["/workspace/rob/utilities"]  # type: ignore[attr-defined]
            sys.modules["rob.utilities"] = utilities_pkg

        # Load tomlconfig first so relative import resolves
        tc_path = pathlib.Path("/workspace/rob/utilities/tomlconfig.py")
        tc_spec = importlib.util.spec_from_file_location("rob.utilities.tomlconfig", tc_path)
        assert tc_spec and tc_spec.loader
        tc_mod = importlib.util.module_from_spec(tc_spec)
        sys.modules["rob.utilities.tomlconfig"] = tc_mod
        # Provide shims required by tomlconfig -> query
        # 1) 'toml' shim
        if "toml" not in sys.modules:
            try:
                import tomllib as _tomllib  # type: ignore
                import types
                toml = types.ModuleType("toml")
                toml.load = _tomllib.load  # type: ignore
                toml.loads = _tomllib.loads  # type: ignore
                def _dump(obj, fp):
                    fp.write("\n".join(f"{k} = {repr(v)}" for k, v in obj.items()))
                toml.dump = _dump  # type: ignore
                sys.modules["toml"] = toml
            except Exception:
                pass
        # 2) 'readchar' stub used by query
        if "readchar" not in sys.modules:
            rc_stub = ModuleType("readchar")
            class _Key:
                UP = "UP"; DOWN = "DOWN"; LEFT = "LEFT"; RIGHT = "RIGHT"; CTRL_J = "CTRL_J"; CTRL_M = "CTRL_M"
            setattr(rc_stub, "key", _Key)
            setattr(rc_stub, "readkey", lambda: "\n")
            sys.modules["readchar"] = rc_stub
        tc_spec.loader.exec_module(tc_mod)  # type: ignore[attr-defined]

        # Now load cli under package name so relative imports succeed
        cli_path = pathlib.Path("/workspace/rob/utilities/cli.py")
        spec = importlib.util.spec_from_file_location("rob.utilities.cli", cli_path)
        assert spec and spec.loader
        cli_mod = importlib.util.module_from_spec(spec)
        sys.modules["rob.utilities.cli"] = cli_mod
        # Ensure readchar stub exists for nested imports (redundant safety)
        if "readchar" not in sys.modules:
            sys.modules["readchar"] = rc_stub
        spec.loader.exec_module(cli_mod)  # type: ignore[attr-defined]


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

    test_folder = Path(cli_mod.__file__).parent

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

    # Call _print_usage with the specific function and its command tokens
    cli_mod._print_usage(test_function, ["test_command"]) 

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
