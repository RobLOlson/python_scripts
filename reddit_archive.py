"""(C) Rob Olson"""
# pylint: disable = C0330
# pylint: disable = multiple-imports
import os, shelve, sys, datetime, argparse

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
    "--pwd",
    metavar="pwd",
    nargs=1,
    action="store",
    type=str,
    help="specify password",
)

_ARGS = _ARGPARSER.parse_args()

# located at https://www.reddit.com/prefs/apps
_REDDIT_ID = os.environ["REDDIT_ID"]
_REDDIT_SECRET = os.environ["REDDIT_SECRET"]

if not _ARGS.pwd or not _ARGS.user:
    _REDDIT_USERNAME = os.environ["REDDIT_USERNAME"]
    _REDDIT_PASSWORD = os.environ["REDDIT_PASSWORD"]


_REDDIT = praw.Reddit(
    client_id=_REDDIT_ID,
    client_secret=_REDDIT_SECRET,
    user_agent="long_comment_aggregator",
    username=_REDDIT_USERNAME,
    password=_REDDIT_PASSWORD,
)


def generate_text():
    breakpoint()
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
        exit()

    me = _REDDIT.user.me()  # pylint: disable=invalid-name

    new = me.comments.new(limit=None)
    breakpoint()
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
                breakpoint()
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
