"""(C) Rob Olson"""
# pylint: disable = C0330
# pylint: disable = multiple-imports
import os, shelve, sys, datetime, argparse, subprocess

from rich.progress import track

from pathlib import Path

import praw

_THIS_FILE = Path(sys.argv[0])

# Create the parser
_ARGPARSER = argparse.ArgumentParser(
    prog=sys.argv[0],
    allow_abbrev=True,
    add_help=True,
    description="Archive reddit comments.",
    epilog="(C) Rob",
)

_ARGPARSER.add_argument(
    "-t", "--text", action="store_true", help="generate text file ONLY"
)
_ARGPARSER.add_argument(
    "-o", "--overwrite", action="store_true", help="overwrite existing database entries"
)
_ARGPARSER.add_argument(
    "-u",
    "--user",
    metavar="user",
    nargs=1,
    action="store",
    type=str,
    help="specify user",
)

_ARGPARSER.add_argument(
    "-p",
    # "--pwd",
    "--password",
    metavar="pwd",
    nargs=1,
    action="store",
    type=str,
    help="specify password",
)

_ARGPARSER.add_argument(
    "-f",
    "--full",
    action="store_true",
    help="Include 'top' and 'controversial' posts in praw request.",
)

_ARGPARSER.add_argument(
    "-c",
    "--config",
    action="store_true",
    help="Manually configure reddit credentials for this user agent.",
)

_ARGS = _ARGPARSER.parse_args()

if _ARGS.config:
    _REDDIT_ID = input("\nEnter a reddit account ID.\n> ")
    _REDDIT_SECRET = input(
        "\nEnter the reddit secret for this account\n(located at https://www.reddit.com/perfs/apps)\n> "
    )
    choice = input("Save credentials? Y/N\n>")
    if choice in ["yes", "y", "Y"]:
        subprocess.run(["setx", "REDDIT_ID", _REDDIT_ID])
        subprocess.run(["setx", "REDDIT_SECRET", _REDDIT_SECRET])

else:
    # located at https://www.reddit.com/prefs/apps
    _REDDIT_ID = os.environ["REDDIT_ID"]
    _REDDIT_SECRET = os.environ["REDDIT_SECRET"]

match (_ARGS.user, _ARGS.password):
    case (None, None) | (_, None) | (None, _):
        try:
            _REDDIT_USERNAME = os.environ["REDDIT_USERNAME"]
            _REDDIT_PASSWORD = os.environ["REDDIT_PASSWORD"]
        except KeyError:
            _REDDIT_USERNAME = input("Enter reddit username: ")
            _REDDIT_PASSWORD = input("Enter reddit password: ")
            choice = input("\nSave login info (WARNING: NOT SECURE)? Y/N\n> ")
            if choice in ["yes", "YES", "y", "Y"]:
                subprocess.run(["setx", "REDDIT_USERNAME", _REDDIT_USERNAME])
                subprocess.run(["setx", "REDDIT_PASSWORD", _REDDIT_PASSWORD])
    case (u, p) if u and p:
        _REDDIT_USERNAME = u
        _REDDIT_PASSWORD = p
    case _:
        print("DUH")


_REDDIT = praw.Reddit(
    client_id=_REDDIT_ID,
    client_secret=_REDDIT_SECRET,
    user_agent="long_comment_aggregator",
    username=_REDDIT_USERNAME,
    password=_REDDIT_PASSWORD,
)


def generate_text():
    now = datetime.datetime.now()
    with shelve.open(f"{_THIS_FILE.parent}/db/comments.db") as db, open(
        f"reddit_archive_{now.day}_{now.month}_{now.year}.txt",
        "w",
        encoding="utf-8",
    ) as fp:
        sorted_comments = reversed(
            sorted(
                [v for k, v in db.items()],
                key=lambda x: x["created_utc"],
            )
        )

        for comment in sorted_comments:
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


def main():  # pylint: disable=missing-function-docstring
    if _ARGS.text:
        generate_text()
        exit(0)

    try:
        me = _REDDIT.user.me()  # pylint: disable=invalid-name
    except BaseException:
        input("Invalid login credentials.")
        exit(1)

    new = me.comments.new(limit=None)
    top = me.comments.top(limit=None)
    contro = me.comments.controversial(limit=None)

    with shelve.open(
        f"{_THIS_FILE.parent}/db/comments.db"
    ) as db:  # pylint: disable=invalid-name
        prev = db.keys()
        print("Archiving 'new'...")
        count = 0
        for comment in new:
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

        if not _ARGS.full:
            generate_text()
            exit(0)

        print("Archiving 'top'...")
        count = 0
        for comment in top:
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

        print("Archiving 'controversial'...")
        for comment in contro:
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