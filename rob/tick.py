import os
import datetime
import time
import logging
import sys
import contextlib

from pathlib import Path

import appdirs

from ticktick.oauth2 import OAuth2
from ticktick.api import TickTickClient

from rich.logging import RichHandler

import argparse

# <Create Parser.
my_parser = argparse.ArgumentParser(
    prog="py -m rob." + Path(__file__).stem,
    allow_abbrev=True,
    add_help=True,
    # usage="$(prog)s [-h] path",
    description="Run a background process that syncs a local file with ticktick servers.",
    epilog="(C) Rob",
)

# Add the arguments
# my_parser.add_argument(
#     "Path",
#     metavar="path",
#     nargs="?",
#     default=".",
#     action="store",
#     type=str,
#     help="the path to list",
# )

my_parser.add_argument(
    "-t", "--token", action="store_true", help="Force an OAuth Token update."
)

my_parser.add_argument("-g", "--get", action="store_true", help="Get today's tasks.")

my_parser.add_argument(
    "-u", "--update", action="store_true", help="Update the task cache."
)

# </Created Parser>

# Execute the parse_args() method
args = my_parser.parse_args()


_BASE_PATH = Path(appdirs.user_data_dir())

_LOG_FILE = _BASE_PATH / "robolson" / "tick" / "LOG.txt"
# _LOG_FILE = Path("C:\\users\\sterl\\OneDrive\\Desktop\\LOG.txt")
if not _LOG_FILE.exists():
    os.makedirs(_LOG_FILE.parent, exist_ok=True)


class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """

    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ""

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s",
    filename=_LOG_FILE,
    filemode="a",
)


FORMAT = "%(message)s"
logging.basicConfig(
    filename=_LOG_FILE,
    level=logging.INFO,
    format=FORMAT,
    datefmt="[%X]",
)

log = logging.getLogger("rich")
log.info("**Hello, World!**")

_CLIENT_ID = os.environ.get("TICKTICK_CLIENT_ID", "")
_CLIENT_SECRET = os.environ.get("TICKTICK_CLIENT_SECRET", "")
_TICKTICK_USERNAME = os.environ.get("TICKTICK_USERNAME", "")
_TICKTICK_PASSWORD = os.environ.get("TICKTICK_PASSWORD", "")

_TOKEN_FILE = _BASE_PATH / "robolson" / "tick" / "cache" / ".token-oauth"

if not _TOKEN_FILE.exists():
    os.makedirs(_TOKEN_FILE.parent, exist_ok=True)

if args.token:
    os.remove(_TOKEN_FILE)

_TASK_FILE = os.environ.get("TICKTICK_TASK_FILE", "")
if not _TASK_FILE:
    _TASK_FILE = _BASE_PATH / "robolson" / "tick" / "tasks.txt"
    if not _TASK_FILE.exists():
        os.makedirs(_TASK_FILE.parent, exist_ok=True)
        open(f"{_TASK_FILE}", "w").close()

if args.get:
    last_modified = datetime.datetime.fromtimestamp(os.path.getmtime(_TASK_FILE))
    if datetime.datetime.today() - last_modified < datetime.timedelta(minutes=60):
        with open(_TASK_FILE, "r") as fp:
            print(", ".join([elem.rstrip() for elem in fp.readlines()]), end="")

    exit(0)

auth_client = OAuth2(
    client_id=_CLIENT_ID,
    client_secret=_CLIENT_SECRET,
    redirect_uri="http://127.0.0.1:8080",
    cache_path=str(_TOKEN_FILE),
    check_cache=True,
)

tick_client = TickTickClient(
    username=_TICKTICK_USERNAME, password=_TICKTICK_PASSWORD, oauth=auth_client
)

# For Debugging, these will redirect standard streams to the logger
# stdout_logger = logging.getLogger("STDOUT")
# sl = StreamToLogger(stdout_logger, logging.INFO)
# sys.stdout = sl

# stderr_logger = logging.getLogger("STDERR")
# sl = StreamToLogger(stderr_logger, logging.ERROR)
# sys.stderr = sl

if args.update:
    today = datetime.datetime.today().isoformat("!")
    today = today.split("!")[0]
    due = [
        elem
        for elem in tick_client.state["tasks"]
        if "dueDate" in elem.keys() and today in elem["dueDate"]
    ]

    with open(f"{_TASK_FILE}", "w") as fp:
        if due:
            fp.write("\n".join([elem["title"] for elem in due]))
        else:
            fp.write("")

    exit(0)


while True:
    today = datetime.datetime.today().isoformat("!")
    today = today.split("!")[0]
    due = [
        elem
        for elem in tick_client.state["tasks"]
        if "dueDate" in elem.keys() and today in elem["dueDate"]
    ]

    with open(f"{_TASK_FILE}", "w") as fp:
        if due:
            fp.write("\n".join([elem["title"] for elem in due]))
        else:
            fp.write("")
    time.sleep(3600)
    tick_client.sync()
