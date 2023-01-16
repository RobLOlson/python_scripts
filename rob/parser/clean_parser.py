import argparse

clean_parser = argparse.ArgumentParser(
    description="Clean up a folder.",
    add_help=True,
    epilog="(C) Rob",
)

# Add the arguments
clean_parser.add_argument(
    "-p",
    "--path",
    metavar="dir",
    default=".",
    action="store",
    type=str,
    help="the directory to clean",
)

clean_parser.add_argument(
    "-y",
    "--yes",
    default=False,
    action="store_true",
    help="skip all interactive prompts by answering 'yes'",
)

clean_parser.add_argument(
    "-r",
    "--recurse",
    default=False,
    action="store_true",
    help="Recurse through nested folders.",
)

alt_mode = clean_parser.add_mutually_exclusive_group(required=False)

alt_mode.add_argument(
    "-u",
    "--undo",
    default=False,
    action="store_true",
    help="undo the previous execution in target directory",
)

alt_mode.add_argument(
    "--config",
    default=False,
    action="store_true",
    help="create a config file",
)

alt_mode.add_argument(
    "--debug", default=False, action="store_true", help="run in debug mode"
)
