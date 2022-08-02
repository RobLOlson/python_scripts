import pathlib
import sys

import pytest
from hypothesis import given, strategies

from .rob.clean import execute_commands, handle_files, main, remove_empty_dir, undo


@strategies.composite
def file_name(draw):
    file_name = draw(strategies.from_regex(r"\A[^/\\:*\"<>|?]+\.[^/\\:*\"<>|?]+$"))
    # pathlib.Path(file_name.strip()).touch()
    return file_name.strip()


@given(file_name=file_name())
def test_handle_files(file_name):
    d = pathlib.Path(__file__).parent / "TMP"
    if not d.exists():
        d.mkdir()
    p = d / file_name
    p.touch()

    handle_files([p], yes_all=True)

    assert 1

    print("CLEANING")

    p.unlink()
    d.rmdir()


@given(file_name=file_name())
def test_remove_empty_dir(file_name):
    d = pathlib.Path(__file__).parent / "TMP"
    if not d.exists():
        d.mkdir()

    p = d / pathlib.Path(file_name).stem
    p.mkdir()

    remove_empty_dir(p)

    assert not p.exists()

    if p.exists():
        p.rmdir()
    if d.exists():
        d.rmdir()


# @given(files())
# def test_handle_files(files):
#     handle_files(files)
