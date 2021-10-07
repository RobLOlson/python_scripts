# Robert Olson
# python interpreter profile

from pprint import PrettyPrinter
import rich.traceback
import os
import sys

pp = PrettyPrinter(sort_dicts=False, underscore_numbers=True).pprint

# automatically pretty print objects in terminal
sys.displayhook = lambda x: exec(['_=x; pp(x)','pass'][x is None])

rich.traceback.install(show_locals=True)

os.environ["PYTHONBREAKPOINT"] = "ipdb.set_trace"
