import argparse

tick_parser = argparse.ArgumentParser(
    prog="",
    allow_abbrev=True,
    add_help=True,
    # usage="$(prog)s [-h] path",
    description="Run a background process that syncs a local file with ticktick servers.",
    epilog="(C) Rob",
)

tick_parser.add_argument(
    "-t", "--token", action="store_true", help="Force an OAuth Token update."
)

tick_parser.add_argument("-g", "--get", action="store_true", help="Get today's tasks.")

tick_parser.add_argument(
    "-u", "--update", action="store_true", help="Update the task cache."
)
