"""python interpreter profile
Point your $PYTHONSTARTUP environment variable at this file."""

import os

from functools import reduce

import rich.traceback
from rich import pretty
from rich import inspect

pretty.install()

rich.traceback.install()

dir = inspect

os.environ["PYTHONBREAKPOINT"] = "pdbr.set_trace"


def compose(*functions):
    """Compose multiple unary functions.  E.g., compose(plus_2, times_2, minus_2)"""
    return reduce(lambda f, g: lambda x: g(f(x)), functions)


def transpose(matrix):
    """If matrix is m x n, return its n x m transpose."""
    return list(zip(*matrix))


def chunk(iterable, n, *, incomplete="fill", fillvalue=None):
    "Collect data into non-overlapping fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, fillvalue='x') --> ABC DEF Gxx
    # grouper('ABCDEFG', 3, incomplete='strict') --> ABC DEF ValueError
    # grouper('ABCDEFG', 3, incomplete='ignore') --> ABC DEF
    args = [iter(iterable)] * n
    if incomplete == "fill":
        return zip_longest(*args, fillvalue=fillvalue)
    if incomplete == "strict":
        return zip(*args, strict=True)
    if incomplete == "ignore":
        return zip(*args)
    else:
        raise ValueError("Expected fill, strict, or ignore")


try:
    from ptpython.repl import embed
except ImportError:
    print("ptpython is not available: falling back to standard prompt")
else:
    embed(globals(), locals())
