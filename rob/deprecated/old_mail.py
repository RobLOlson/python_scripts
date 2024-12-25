"""Shoot a quick email.

Usage:
  py -m rob.email [--user <user>] <target> <content>...       email a target (specify user)
  py -m rob.email add <name> <email>                          add contact to database
  py -m rob.email contacts                                    list contacts
  py -m rob.email users [--default [user]]                    list users (choose default)
  py -m rob.email [-h | --help]                               Show this screen.

Options:
  -h --help     Show this screen.
  -u --user     Specify user (email sender).
"""

_DOC = """Shoot a quick email.

Usage:
  email.py add <name> <email>
  email.py contacts
  email.py users [--default [<user>]]
  email.py [--user <user>] <target> <content>...
  email.py [-h | --help]

Options:
  -u <user>, --user <user>
  -h --help
"""

import os
import shelve
import sys
from pathlib import Path

import appdirs
from docopt import docopt
from redmail import gmail
from rich.prompt import Prompt

# from .parser.email_parser import contact_parser, email_parser

# _ARGS = email_parser.parse_args()
_ARGS = docopt(_DOC, argv=sys.argv[1:], help=True)


def main(_ARGS: dict[str, str]):

    if len(sys.argv) < 2:
        print(__doc__)
        exit(1)

    _CONTACT_FILE = Path(appdirs.user_data_dir()) / "robolson" / "email" / "contacts.db"
    _USER_FILE = Path(appdirs.user_data_dir()) / "robolson" / "email" / "users.db"

    _PROMPT = "\nrob.email> "

    os.makedirs(_CONTACT_FILE.parent, exist_ok=True)
    os.makedirs(_USER_FILE.parent, exist_ok=True)
    _TARGET = _ARGS["<target>"]
    _CONTENT = " ".join(_ARGS["<content>"])

    if _ARGS["users"]:
        prompt_default = False
        with shelve.open(str(_USER_FILE)) as db:
            # if user passed --default option with valid user
            if _ARGS["--default"]:
                if _ARGS["<user>"] and _ARGS["<user>"] in db.keys():
                    db["default"] = _ARGS["<user>"]
                else:
                    prompt_default = True

            if "default" not in db.keys():
                db["default"] = ""

            keys = list(db.keys())
            keys.remove("default")
            print(
                "Registered sender emails:\n"
                + "\n".join(
                    f"{i+1}.) {elem}" + (" (default)" if elem == db["default"] else "")
                    for i, elem in enumerate(keys)
                )
            )
            if prompt_default:
                choice = Prompt.ask(
                    f"Select new default sender.{_PROMPT}",
                    choices=[f"{e}" for e in range(1, len(keys) + 1)],
                )
                db["default"] = keys[int(choice) - 1]
            exit(1)

    with shelve.open(str(_CONTACT_FILE)) as db:
        if _ARGS["add"]:
            db[_ARGS["<name>"]] = _ARGS["<email>"]
            exit(1)

        if _ARGS["contacts"]:
            print(
                "Quick contacts:\n"
                + "\n".join(
                    f"{i+1}.) {elem} ({db[elem]})" for i, elem in enumerate(db.keys())
                )
            )
            exit(1)

        if _ARGS["<target>"] in db.keys():
            _TARGET = db[_TARGET]

    if not _ARGS["--user"]:
        with shelve.open(str(_USER_FILE)) as db:
            if db["default"]:
                gmail.username = db["default"]
                gmail.password = db[gmail.username]
            else:
                gmail.username = input(f"Enter sender's gmail address.{_PROMPT}")
                gmail.password = input(f"Enter sender's gmail app password.{_PROMPT}")
                choice = input(f"Save credentials? Y/N{_PROMPT}")
                if choice.lower() in ["y", "yes"]:
                    db[gmail.username] = gmail.password

                    choice = input(
                        f"Set {gmail.username} to default sender? Y/N{_PROMPT}"
                    )
                    if choice.lower() in ["y", "yes"]:
                        db["default"] = gmail.username
    else:
        u = _ARGS["--user"]
        with shelve.open(str(_USER_FILE)) as db:
            try:
                gmail.username = u
                gmail.password = db[u]

            except KeyError:
                print(f"Creating new user ({u}).")
                gmail.password = input(
                    f"Enter sender's gmail **APP** password. (Can be found at https://myaccount.google.com/security){_PROMPT}"
                )
                choice = input(f"Save credentials? Y/N{_PROMPT}")
                if choice.lower() in ["y", "yes"]:
                    db[gmail.username] = gmail.password

                choice = input(f"Set {gmail.username} to default sender? Y/N{_PROMPT}")
                if choice.lower() in ["y", "yes"]:
                    db["default"] = gmail.username

    if len(_CONTENT) > 20:
        subject = _CONTENT[:16] + "..."
    else:
        subject = _CONTENT

    gmail.send(subject=subject, receivers=_TARGET, text=_CONTENT)


if __name__ == "__main__":
    main(_ARGS)
