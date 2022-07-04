import argparse
import sys

# Create the parser
email_parser = argparse.ArgumentParser(
    prog="py -m rob.email",
    allow_abbrev=True,
    add_help=True,
    description="Shoot a quick email",
    epilog="(C) Rob",
)

# Add the arguments
email_parser.add_argument(
    "target",
    nargs=1,
    action="store",
    default=False,
    type=str,
    help="Email Recipient",
)

email_parser.add_argument(
    "content", nargs="*", action="store", type=str, help="Email Text"
)
