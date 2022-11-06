"""(C) Rob Olson"""
import csv
import datetime

# pylint: disable = C0330
# pylint: disable = multiple-imports
import os
import shelve
import subprocess
import sys
from copy import copy
from itertools import chain
from pathlib import Path
from typing import Iterable

import appdirs
import praw

from .parser.reddit_parser import reddit_parser

reddit_parser.prog = "py -m rob." + Path(__file__).stem

_THIS_FILE = Path(sys.argv[0])
_DB_FILE = Path(appdirs.user_data_dir()) / "robolson" / "reddit_archive" / "comments.db"
_USER_FILE = Path(appdirs.user_data_dir()) / "robolson" / "reddit_archive" / "users.db"

_PROMPT = "\nrob.reddit_archive> "

if not _DB_FILE.exists():
    os.makedirs(_DB_FILE.parent, exist_ok=True)

if not _USER_FILE.exists():
    os.makedirs(_USER_FILE.parent, exist_ok=True)

_ARGS = reddit_parser.parse_args()


match (_ARGS.user, _ARGS.password):

    # No Username
    case (None, None) | (None, _):
        try:
            with shelve.open(str(_USER_FILE)) as db:
                _REDDIT_USERNAME = db["default"]
                _REDDIT_CREDS = db[_REDDIT_USERNAME]
                _REDDIT_PASSWORD = _REDDIT_CREDS["reddit_password"]

        except KeyError:
            _REDDIT_USERNAME = input("Enter reddit username: ")
            _REDDIT_PASSWORD = input("Enter reddit password: ")
            choice = input(f"\nSave login info (WARNING: NOT SECURE)? Y/N{_PROMPT}")
            with shelve.open(str(_USER_FILE)) as db:
                db[_REDDIT_USERNAME] = {"reddit_password": _REDDIT_PASSWORD}
                _REDDIT_CREDS = db[_REDDIT_USERNAME]
                choice = input(f"\nMake this default user?{_PROMPT}")
                if choice in ["yes", "YES", "y", "Y"]:
                    db["default"] = _REDDIT_USERNAME

    # Username, but no password
    case (u, None) if u:
        with shelve.open(str(_USER_FILE)) as db:
            try:
                _REDDIT_USERNAME = u[0]
                _REDDIT_PASSWORD = db[_REDDIT_USERNAME]["reddit_password"]
            except KeyError:
                _REDDIT_PASSWORD = input(f"Enter password (user: {u}): ")

    case (u, p) if u and p:
        _REDDIT_USERNAME = u[0]
        _REDDIT_PASSWORD = p[0]
    case _:
        print("DUH")
        exit(1)


try:
    with shelve.open(str(_USER_FILE)) as db:
        _REDDIT_ID = db[_REDDIT_USERNAME]["app_id"]
        _REDDIT_SECRET = db[_REDDIT_USERNAME]["app_secret"]

except KeyError:

    # if _ARGS.config:
    _REDDIT_ID = input(
        f"\nEnter a reddit app ID. (located https://www.reddit.com/prefs/apps/){_PROMPT}"
    )
    _REDDIT_SECRET = input(
        f"\nEnter the reddit secret for this account\n(located at https://www.reddit.com/prefs/apps/){_PROMPT}"
    )
    choice = input(f"Save credentials? Y/N{_PROMPT}")
    if choice in ["yes", "y", "Y"]:
        with shelve.open(str(_USER_FILE)) as db:
            _REDDIT_CREDS = db[_REDDIT_USERNAME]
            _REDDIT_CREDS["app_id"] = _REDDIT_ID
            _REDDIT_CREDS["app_secret"] = _REDDIT_SECRET
            db[_REDDIT_USERNAME] = _REDDIT_CREDS

_REDDIT = praw.Reddit(
    client_id=_REDDIT_ID,
    client_secret=_REDDIT_SECRET,
    user_agent="long_comment_aggregator",
    username=_REDDIT_USERNAME,
    password=_REDDIT_PASSWORD,
)


def generate_text():
    now = datetime.datetime.now()
    with shelve.open(str(_DB_FILE)) as db, open(
        f"reddit_archive_{now.year}_{now.month}_{now.day}.txt",
        "w",
        encoding="utf-8",
    ) as fp:
        sorted_comments = reversed(
            sorted(
                [v for k, v in db.items()],
                key=lambda x: x["created_utc"],
            )
        )
        comments = [comment["body"] for comment in copy(sorted_comments)]

        fp.write(f"total # of comments: {len(comments):,}\n")
        fp.write(
            f"total # of words: {sum(len(comment.split(' ')) for comment in comments):,}\n"
        )

        comment_count = 0
        for comment in sorted_comments:
            comment_count += 1
            try:
                parent_author = comment["parent_author"]
            except KeyError:
                parent_author = "?"
            fp.write(
                f"""
======
http://reddit.com{comment['permalink']}
{comment['human_time']} ({comment['ups']})
======
{parent_author}: {comment['parent_body']}
======
{comment['body']}
======\n\n"""
            )


def parse_csv(csv_file: Path):
    """Take the 'comments.csv' file provided by reddit's data dump and parse into database."""

    with open(str(csv_file), encoding="utf-8") as fp, shelve.open(str(_DB_FILE)) as db:
        data = csv.DictReader(fp, delimiter=",")
        prev: set[str] = set(db.keys())  # previously archived comment IDs

        comment_ids: set[str] = {datum["id"] for datum in data}

        new_comments = comment_ids - prev

        count: int = 0
        for comment_id in new_comments:
            print(count, end="\r", flush=True)
            count += 1

            if comment_id not in prev:
                comment = _REDDIT.comment(comment_id)
                try:
                    body = comment.body
                except praw.exceptions.ClientException:
                    continue
                if len(body) < 100:
                    continue

                parent = comment.parent()
                db[comment.id] = {
                    "id": comment.id,
                    "body": comment.body,
                    "ups": comment.ups,
                    "downs": comment.downs,
                    "permalink": comment.permalink,
                    "parent_author": str(getattr(parent, "author", None)),
                    "parent_body": getattr(parent, "body", None),
                    "created_utc": comment.created_utc,
                    "human_time": datetime.datetime.fromtimestamp(
                        comment.created_utc
                    ).isoformat(),
                }


def main():  # pylint: disable=missing-function-docstring
    if _ARGS.csv:
        parse_csv(Path(_ARGS.csv[0]))
        generate_text()
        exit(0)

    if _ARGS.text:
        generate_text()
        exit(0)

    try:
        me = _REDDIT.user.me()  # pylint: disable=invalid-name
    except BaseException:
        input("Invalid login credentials.")
        exit(1)

    print("Archiving 'new'", end="")
    new = me.comments.new(limit=None)

    if _ARGS.full:
        print(", 'top' and 'controversial", end="")
        top = me.comments.top(limit=None)
        contro = me.comments.controversial(limit=None)

    else:
        top = []
        contro = []

    print("...")

    with shelve.open(str(_DB_FILE)) as db:  # pylint: disable=invalid-name
        prev = db.keys()  # previously archived comment IDs
        count = 0
        for comment in chain(new, top, contro):
            print(count, end="\r", flush=True)
            count += 1
            if _ARGS.overwrite:
                try:
                    del db[comment.id]
                except KeyError:
                    pass

            if comment.id not in prev and len(comment.body) > 100:
                parent = comment.parent()
                db[comment.id] = {
                    "id": comment.id,
                    "body": comment.body,
                    "ups": comment.ups,
                    "downs": comment.downs,
                    "permalink": comment.permalink,
                    "parent_author": str(getattr(parent, "author", None)),
                    "parent_body": getattr(parent, "body", None),
                    "created_utc": comment.created_utc,
                    "human_time": datetime.datetime.fromtimestamp(
                        comment.created_utc
                    ).isoformat(),
                }

    generate_text()


if __name__ == "__main__":
    main()
