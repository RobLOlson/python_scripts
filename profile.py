# Robert Olson
# python interpreter profile

import os

from functools import reduce

import rich.traceback
from rich import pretty

pretty.install()

rich.traceback.install(show_locals=True)

os.environ["PYTHONBREAKPOINT"] = "pdbr.set_trace"


def compose(*functions):
    """Compose multiple unary functions.  E.g., compose(plus_2, times_2, minus_2)"""
    return reduce(lambda f, g: lambda x: g(f(x)), functions)


try:
    from ptpython.repl import embed
except ImportError:
    print("ptpython is not available: falling back to standard prompt")
else:
    embed(globals(), locals())
