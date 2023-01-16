import pathlib
import sys

import pytest
from hypothesis import given, strategies

try:
    from rob.clean import (
        execute_move_commands,
        handle_files,
        main,
        remove_empty_dir,
        undo,
    )
except ImportError:
    from .rob.clean import (
        execute_move_commands,
        handle_files,
        main,
        remove_empty_dir,
        undo,
    )


@strategies.composite
def file_name(draw):
    file_name = draw(strategies.from_regex(r"\A[^/\\:*\"<>|?]+\.[^/\\:*\"<>|?]+$"))
    # pathlib.Path(file_name.strip()).touch()
    return file_name.strip()


@given(file_name=file_name())
def test_handle_files(file_name):
    d = pathlib.Path(__file__).parent / "TMP"
    d.mkdir(exist_ok=True)
    p = d / file_name
    p.touch()

    handle_files([p], yes_all=True)

    assert 1

    p.unlink(missing_ok=True)
    d.rmdir()


@given(file_name=file_name())
def test_remove_empty_dir(file_name):
    d = pathlib.Path(__file__).parent / "TMP"

    d.mkdir(exist_ok=True)

    p = d / pathlib.Path(file_name).stem
    p.mkdir(exist_ok=True)

    remove_empty_dir(p)

    assert not p.exists()

    if p.exists():
        p.rmdir()
    if d.exists():
        d.rmdir()


# @given(file_name=file_name(), source=file_name(), dest=file_name())
def test_execute_commands(file_name="test.txt", source="a", dest="b"):

    d = pathlib.Path(".") / "TMP" / pathlib.Path(source).stem
    if not d.exists():
        d.mkdir(parents=True)

    p1 = d / pathlib.Path(file_name).name
    p1.touch()
    p2 = d / pathlib.Path(dest).stem / pathlib.Path(file_name)

    execute_move_commands(commands={p1: p2})

    p2.unlink(missing_ok=True)
    p2.parent.rmdir()
    p1.parent.rmdir()
    if d.exists():
        d.rmdir()
    if d.parent.exists():
        d.parent.rmdir()
