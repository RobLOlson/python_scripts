import sys
from pathlib import Path

import pytest
from click import decorators

# from hypothesis import given, strategies

# try:
#     from rob.clean import execute_move_commands, remove_empty_dir, undo
# except ModuleNotFoundError:
#     from ..rob.clean import execute_move_commands, remove_empty_dir, undo


def test_nothing():
    pass


# @strategies.composite
# def file_name(draw):
#     file_name = draw(strategies.from_regex(r"\A[^/\\:*\"<>|?]+\.[^/\\:*\"<>|?]+$"))
#     # Path(file_name.strip()).touch()
#     return file_name.strip()


# @given(file_name=file_name())
# def test_remove_empty_dir(file_name: str):
#     d = Path(__file__).parent / "TMP"

#     d.mkdir(exist_ok=True)

#     p = d / Path(file_name).stem
#     # p.touch(exist_ok=True)
#     # p.unlink()

#     remove_empty_dir(p)

#     assert not p.exists()

#     if p.exists():
#         p.rmdir()
#     if d.exists():
#         d.rmdir()
