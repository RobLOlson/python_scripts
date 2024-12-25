import datetime

# for debugging the daemon
import logging
import os
import random
import subprocess
import sys
import time
from pathlib import Path

import appdirs  # type: ignore[import]

from .loggers.tick_logger import StreamToLogger, log
from .parser.tick_parser import tick_parser  # type: ignore[import]
from .ticktick.api import TickTickClient

# Register App with ticktick servers at https://developer.ticktick.com/manage
from .ticktick.oauth2 import OAuth2

_DEBUG = True

tick_parser.prog = "py -m rob." + Path(__file__).stem

# Execute the parse_args() method
args = tick_parser.parse_args()

_BASE_PATH = Path(appdirs.user_data_dir())

_CLIENT_ID = os.environ.get("TICKTICK_CLIENT_ID", "")
_CLIENT_SECRET = os.environ.get("TICKTICK_CLIENT_SECRET", "")

if not _CLIENT_ID or not _CLIENT_SECRET:
    print(
        "Missing environment variables 'TICKTICK_CLIENT_ID' and/or 'TICKTICK_CLIENT_SECRET'\nRegister App with ticktick servers at https://developer.ticktick.com/manage"
    )
    exit(1)


_TICKTICK_USERNAME = os.environ.get("TICKTICK_USERNAME", "")
_TICKTICK_PASSWORD = os.environ.get("TICKTICK_PASSWORD", "")

if not _TICKTICK_USERNAME or not _TICKTICK_USERNAME:
    print(
        "Missing environment variables 'TICKTICK_USERNAME' and/or 'TICKTICK_PASSWORD'"
    )
    exit(1)

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


def get_due(tick_client) -> list[str]:
    today_str = datetime.datetime.today().isoformat("!")
    today_date = today_str
    today_str = today_str.split("!")[0]

    today = datetime.datetime.fromisoformat(today_str)

    due = [
        elem
        for elem in tick_client.state["tasks"]
        if "dueDate" in elem.keys()
        and today + datetime.timedelta(days=1)
        > datetime.datetime.fromisoformat(elem["dueDate"][:-5])
    ]

    return due


def main() -> None:

    global args
    if _DEBUG:
        # For Debugging, these will redirect standard streams to the logger
        stdout_logger = logging.getLogger("STDOUT")
        sl = StreamToLogger(stdout_logger, logging.INFO)
        sys.stdout = sl

        stderr_logger = logging.getLogger("STDERR")
        sl = StreamToLogger(stderr_logger, logging.ERROR)
        sys.stderr = sl

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

    if args.update:
        due = get_due(tick_client)

        with open(f"{_TASK_FILE}", "w") as fp:
            if due:
                fp.write("\n".join([elem["title"] for elem in due]))  # type: ignore[index]
            else:
                fp.write("")

        exit(0)

    if args.daemon:
        subprocess.Popen(["pyw", "-m", "rob.tick"])
        exit(0)

    while True:
        due = get_due(tick_client)

        # Create Overdue Tasks in "me" list for Pavlok
        for task in due:
            # Do not trigger during sleeping hours
            if not 8 < datetime.datetime.now().hour < 20:
                continue

            due_date = datetime.datetime.fromisoformat(task["dueDate"][:-5])
            due_diff = datetime.datetime.now() - due_date

            if due_diff.days > 0 and 0.99**due_diff.days < random.random():

                if task["projectId"] == "54384b29b84562b41688e91a":
                    # If task in Joes List, add to Joes Pavlok List
                    new_projectId = "8999486ebf8fc984f752dd46"

                elif task["projectId"] == "af22459697ae1243ca23f4d9":
                    # If task in Eryns List, add to Eryns Pavlok List
                    new_projectId = "88ba4b50ab907613d84d0cb6"

                else:
                    # Add to Robs Pavlok List
                    new_projectId = "611479cafba2c1d019f96b45"

                new_due = datetime.datetime.fromordinal(
                    datetime.datetime.today().toordinal()
                )
                new_due = new_due + datetime.timedelta(hours=20)
                new_due = new_due.isoformat("T") + "+0000"
                new_task = tick_client.task.builder(
                    title=f"Overdue({due_diff.days}): {task['title']}",
                    dueDate=new_due,
                    content="Created for Pavlok",
                    priority=5,
                    projectId=new_projectId,
                )
                new_task["dueDate"] = new_due
                tick_client.task.create(new_task)

        with open(f"{_TASK_FILE}", "w") as fp:
            if due:
                # write name of due task to file if it is assigned to inbox
                fp.write("\n".join([elem["title"] for elem in due if elem["projectId"] == "inbox115493726"]))  # type: ignore[index]
            else:
                fp.write("")

        # log.info("syncing with ticktick servers")
        tick_client.sync()

        time.sleep(299)


if __name__ == "__main__":
    main()
