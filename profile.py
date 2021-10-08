# Robert Olson
# python interpreter profile

import rich.traceback
import os
import sys

from pprint import PrettyPrinter

from functools import reduce
pp = PrettyPrinter(sort_dicts=False, underscore_numbers=True).pprint

# automatically pretty print objects in terminal
sys.displayhook = lambda x: exec(['_=x; pp(x)','pass'][x is None])

rich.traceback.install(show_locals=True)

os.environ["PYTHONBREAKPOINT"] = "ipdb.set_trace"

def compose(*functions):
    """Compose multiple unary functions.  E.g., compose(plus_2, times_2, minus_2)"""
    return reduce(lambda f, g: lambda x: g(f(x)), functions)
