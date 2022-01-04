# Rob Olson

import praw, os, shelve, argparse, sys, datetime

from pathlib import Path
from dataclasses import dataclass, field

FILE = Path(sys.argv[0])

import argparse

# Create the parser
my_parser = argparse.ArgumentParser(
    prog=sys.argv[0],
    allow_abbrev=True,
    add_help=True,
    description="Archive reddit comments.",
    epilog="(C) Rob",
)

my_parser.add_argument("-t", "--text", action="store_true", help="generate text file")

# Execute the parse_args() method
args = my_parser.parse_args()

# located at https://www.reddit.com/prefs/apps
REDDIT_ID = os.environ["REDDIT_ID"]
REDDIT_SECRET = os.environ["REDDIT_SECRET"]

REDDIT_USERNAME = os.environ["REDDIT_USERNAME"]
REDDIT_PASSWORD = os.environ["REDDIT_PASSWORD"]


reddit = praw.Reddit(
    client_id=REDDIT_ID,
    client_secret=REDDIT_SECRET,
    user_agent="long_comment_aggregator",
    username=REDDIT_USERNAME,
    password=REDDIT_PASSWORD,
)


@dataclass
class Entry:
    e_id: str = field()
    body: str = field()
    link_permalink: str = field()
    parent_body: str = field()


def main():
    me = reddit.user.me()
    new = me.comments.new(limit=None)
    top = me.comments.top(limit=None)
    contro = me.comments.controversial(limit=None)

    with shelve.open(f"{FILE.parent}/db/comments.db") as db:
        prev = db.keys()
        for comment in new:
            if comment.id not in prev and len(comment.body) > 100:
                db[comment.id] = {
                    "id": comment.id,
                    "body": comment.body,
                    "link_permalink": comment.link_permalink,
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
                    "link_permalink": comment.link_permalink,
                    "parent_body": getattr(comment.parent(), "body", None),
                    "created_utc": comment.created_utc,
                    "human_time": datetime.datetime.fromtimestamp(
                        comment.created_utc
                    ).isoformat(),
                }

                # db[comment.id] = f"{comment.parent().body}\n======{comment.link_permalink}======\n{comment.body}"

        for comment in contro:
            if comment.id not in prev and len(comment.body) > 100:
                db[comment.id] = {
                    "id": comment.id,
                    "body": comment.body,
                    "link_permalink": comment.link_permalink,
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
        if args.text:
            now = datetime.datetime.now()
            with open(
                f"reddit_archive__{now.day}_{now.month}_{now.year}.txt",
                "w",
                encoding="utf-8",
            ) as fp:
                for comment in sorted_comments:
                    fp.write(
                        f"""
======
{comment['link_permalink']}
{comment['human_time']}
======
{comment['parent_body']}
======
{comment['body']}
======\n\n"""
                    )


if __name__ == "__main__":
    main()
