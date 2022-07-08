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
    nargs="?",
    action="store",
    default=False,
    type=str,
    help="Email Recipient",
)

email_parser.add_argument(
    "content", nargs="*", action="store", type=str, help="Email Text"
)

# Add SUBPARSER
subparsers = email_parser.add_subparsers(help="manage contacts", required=False)

# create the SUBPARSER
contact_parser = subparsers.add_parser(
    "add",
    help="Add a {name:email} pair to the quick contact dictionary.",
    exit_on_error=False,
)

add_contact_group = contact_parser.add_argument_group("contact")

add_contact_group.add_argument(
    "name", nargs=1, type=str, help="Contact's name (used as CLI shortcut)"
)
add_contact_group.add_argument("email", nargs=1, type=str, help="Contact's email")

# create the list SUBPARSER
list_parser = subparsers.add_parser("list", help="List all quick contacts.")
# parser_a.add_argument('bar', type=int, help='bar help')
