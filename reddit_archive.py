"""(C) Rob Olson"""
# pylint: disable = C0330
# pylint: disable = multiple-imports
import os, shelve, sys, datetime, argparse

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

_ARGPARSER.add_argument("-t", "--text", action="store_true", help="generate text file")
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


def main():  # pylint: disable=missing-function-docstring
    me = _REDDIT.user.me()  # pylint: disable=invalid-name

    new = me.comments.new(limit=None)
    top = me.comments.top(limit=None)
    contro = me.comments.controversial(limit=None)

    with shelve.open(
        f"{_THIS_FILE.parent}/db/comments.db"
    ) as db:  # pylint: disable=invalid-name
        prev = db.keys()
        for comment in new:
            if comment.id not in prev and len(comment.body) > 100:
                db[comment.id] = {
                    "id": comment.id,
                    "body": comment.body,
                    "ups": comment.ups,
                    "downs": comment.downs,
                    "permalink": comment.permalink,
                    "parent_body": getattr(comment.parent(), "body", None),
                    "created_utc": comment.created_utc,
                    "human_time": datetime.datetime.fromtimestamp(
                        comment.created_utc
                    ).isoformat(),
                }

        for comment in top:
            if comment.id not in prev and len(comment.body) > 100:
                db[comment.id] = {
                    "id": comment.id,
                    "body": comment.body,
                    "ups": comment.ups,
                    "downs": comment.downs,
                    "permalink": comment.permalink,
                    "parent_body": getattr(comment.parent(), "body", None),
                    "created_utc": comment.created_utc,
                    "human_time": datetime.datetime.fromtimestamp(
                        comment.created_utc
                    ).isoformat(),
                }

        for comment in contro:
            if comment.id not in prev and len(comment.body) > 100:
                db[comment.id] = {
                    "id": comment.id,
                    "body": comment.body,
                    "ups": comment.ups,
                    "downs": comment.downs,
                    "permalink": comment.permalink,
                    "parent_body": getattr(comment.parent(), "body", None),
                    "created_utc": comment.created_utc,
                    "human_time": datetime.datetime.fromtimestamp(
                        comment.created_utc
                    ).isoformat(),
                }

        sorted_comments = reversed(
            sorted(
                [v for k, v in dict(db).items()],
                key=lambda x: x["created_utc"],
            )
        )
        if _ARGS.text:
            now = datetime.datetime.now()
            with open(
                f"reddit_archive__{now.day}_{now.month}_{now.year}.txt",
                "w",
                encoding="utf-8",
            ) as fp:  # pylint: disable = invalid-name
                for comment in sorted_comments:
                    fp.write(
                        f"""
======
{comment['permalink']}
{comment['human_time']} ({comment['ups']})
======
{comment['parent_body']}
======
{comment['body']}
======\n\n"""
                    )


if __name__ == "__main__":
    main()
