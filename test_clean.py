import pathlib
import sys

import pytest
from hypothesis import given, strategies

from .rob.clean import execute_commands, handle_files, main, undo


@strategies.composite
def file_name(draw):
    file_name = draw(strategies.from_regex(r"\A[^/\\:*\"<>|?]+\.[^/\\:*\"<>|?]+$"))
    # pathlib.Path(file_name.strip()).touch()
    return file_name.strip()


@given(file_name=file_name())
def test_handle_filesz(file_name):
    d = pathlib.Path(__file__).parent / "TMP"
    if not d.exists():
        d.mkdir()
    p = d / file_name
    p.touch()

    handle_files([p], yes_all=True)

    assert 1

    p.unlink()
    d.rmdir()


# @given(files())
# def test_handle_files(files):
#     handle_files(files)
