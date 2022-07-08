"""Shoot a quick email.

Usage:
  py -m rob.email <target> <content>...  email a target
  py -m rob.email add <name> <email>     add contact to database
  py -m rob.email list                   list contacts
  py -m rob.email [-h | --help]          Show this screen.

Options:
  -h --help     Show this screen.
"""

_DOC = """Shoot a quick email.

Usage:
  email.py add <name> <email>
  email.py list
  email.py <target> <content>...
  email.py [-h | --help]
"""

import os
import shelve
import sys
from pathlib import Path

import appdirs
from docopt import docopt
from redmail import gmail

from .parser.email_parser import contact_parser, email_parser

if len(sys.argv) < 2:
    print(__doc__)
    exit(1)

# _ARGS = email_parser.parse_args()
_ARGS = docopt(_DOC, argv=sys.argv[1:], help=False)


if _ARGS["--help"] or _ARGS["-h"]:
    print(__doc__)
    exit(1)

_CONTACT_FILE = Path(appdirs.user_data_dir()) / "robolson" / "email" / "contacts.db"

os.makedirs(_CONTACT_FILE.parent, exist_ok=True)

_TARGET = _ARGS["<target>"]
_CONTENT = " ".join(_ARGS["<content>"])

with shelve.open(str(_CONTACT_FILE)) as db:
    if _ARGS["add"]:
        db[_ARGS["<name>"]] = _ARGS["<email>"]
        exit(1)

    if _ARGS["list"]:
        print(
            "Quick Contacts:\n"
            + "\n".join(
                f"{i+1}.) {elem} ({db[elem]})" for i, elem in enumerate(db.keys())
            )
        )
        exit(1)

    if _ARGS["<target>"] in db.keys():
        _TARGET = db[_TARGET]


# If target points at environment variable, replace pointer with contents of variable
# _TARGET = [
#     os.environ.get(elem) if elem in os.environ.keys() else elem for elem in _TARGET
# ]

gmail.username = os.environ.get("GMAIL_ADDRESS")
gmail.password = os.environ.get("GMAIL_APP_PASSWORD")

if len(_CONTENT) > 20:
    subject = _CONTENT[:16] + "..."
else:
    subject = _CONTENT

gmail.send(subject=subject, receivers=_TARGET, text=_CONTENT)
