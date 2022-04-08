import os
import datetime
import time
import logging
import sys

from pathlib import Path

import appdirs

from .ticktick.oauth2 import OAuth2
from .ticktick.api import TickTickClient

import argparse

from .loggers.tick_logger import log, StreamToLogger
from .parser.tick_parser import tick_parser

tick_parser.prog = "py -m rob." + Path(__file__).stem

# Execute the parse_args() method
args = tick_parser.parse_args()

_BASE_PATH = Path(appdirs.user_data_dir())


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

stderr_logger = logging.getLogger("STDERR")
sl = StreamToLogger(stderr_logger, logging.ERROR)
sys.stderr = sl

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
