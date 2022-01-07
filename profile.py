# Robert Olson
# python interpreter profile

import rich.traceback
import os
import sys

from pprint import PrettyPrinter
from functools import reduce

from rich import pretty

pretty.install()

rich.traceback.install(show_locals=True)

os.environ["PYTHONBREAKPOINT"] = "pdbr.set_trace"


def compose(*functions):
    """Compose multiple unary functions.  E.g., compose(plus_2, times_2, minus_2)"""
    return reduce(lambda f, g: lambda x: g(f(x)), functions)
