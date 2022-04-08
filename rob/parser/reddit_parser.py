import argparse

reddit_parser = argparse.ArgumentParser(
    prog="py -m rob.reddit_archive",
    allow_abbrev=True,
    add_help=True,
    description="Archive reddit comments.",
    epilog="(C) Rob",
)

reddit_parser.add_argument(
    "-t", "--text", action="store_true", help="generate text file ONLY"
)
reddit_parser.add_argument(
    "-o", "--overwrite", action="store_true", help="overwrite existing database entries"
)
reddit_parser.add_argument(
    "-u",
    "--user",
    metavar="user",
    nargs=1,
    action="store",
    type=str,
    help="specify user",
)

reddit_parser.add_argument(
    "-p",
    # "--pwd",
    "--password",
    metavar="pwd",
    nargs=1,
    action="store",
    type=str,
    help="specify password",
)

reddit_parser.add_argument(
    "-f",
    "--full",
    action="store_true",
    help="Include 'top' and 'controversial' posts in praw request.",
)

reddit_parser.add_argument(
    "-c",
    "--config",
    action="store_true",
    help="Manually configure reddit credentials for this user agent.",
)
