# Robert Olson
# python interpreter profile

from pprint import pprint as pp
import rich.traceback
import os
import sys

# automatically pretty print objects in terminal
sys.displayhook = lambda x: exec(['_=x; pp(x)','pass'][x is None])

rich.traceback.install(show_locals=True)

os.environ["PYTHONBREAKPOINT"] = "ipdb.set_trace"
