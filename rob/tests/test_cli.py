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
	def configure_problem_set():
		print("Configured", cli_mod.options.get("user"))

	cli_mod.main(["config", "--user", "alice"])
	captured = capsys.readouterr()
	assert "Configured alice" in captured.out


def test_main_unknown_command(capsys):
	with pytest.raises(SystemExit) as ei:
		cli_mod.main(["unknown"])
	assert ei.value.code == 1
	captured = capsys.readouterr()
	assert "Unknown command: unknown" in captured.out
	assert "Usage:" in captured.out


def test_main_no_args(capsys):
	with pytest.raises(SystemExit) as ei:
		cli_mod.main([])
	assert ei.value.code == 1
	captured = capsys.readouterr()
	assert "Usage: python" in captured.out


def test_usage_shows_docstring_first_line(capsys):

	@cli_mod.cli("sample")
	def sample_cmd():
		"""Do a sample thing."""
		pass

	with pytest.raises(SystemExit):
		cli_mod.main([])

	captured = capsys.readouterr()
	assert "sample - Do a sample thing." in captured.out


