# Robert Olson
# python interpreter profile

import os

from functools import reduce

import rich.traceback
from rich import pretty

from ptpython.repl import embed

pretty.install()

rich.traceback.install(show_locals=True)

os.environ["PYTHONBREAKPOINT"] = "pdbr.set_trace"


def compose(*functions):
    """Compose multiple unary functions.  E.g., compose(plus_2, times_2, minus_2)"""
    return reduce(lambda f, g: lambda x: g(f(x)), functions)


embed(globals(), locals())
