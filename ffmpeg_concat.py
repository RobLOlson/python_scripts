import glob
import subprocess
import pathlib
import os
import time
import shlex
import asyncio
import argparse
import logging
import sys
import concurrent.futures

import nest_asyncio

nest_asyncio.apply()

logging.getLogger("asyncio").setLevel(logging.INFO)

# Create the parser
my_parser = argparse.ArgumentParser(
    prog=sys.argv[0],
    allow_abbrev=True,
    add_help=True,
    description="List the content of a folder",
    epilog="(C) Rob",
)

# Add the arguments
my_parser.add_argument(
    "Filetype",
    metavar="type",
    nargs="?",
    default=".mp3",
    action="store",
    type=str,
    help="the path to list",
)

my_parser.add_argument(
    "Path",
    metavar="path",
    nargs="?",
    default=".",
    action="store",
    type=str,
    help="the path to list",
)

# Execute the parse_args() method
args = my_parser.parse_args()

PATH = args.Path
FILETYPE = args.Filetype


async def spin_up(folder):

    print(folder)

    os.chdir(folder)
    mp3s = glob.glob(f"*{FILETYPE}")
    concated = "|".join(mp3s)
    command = [
        "ffmpeg",
        "-i",
        f"concat:{concated}",
        "-movflags",
        "use_metadata_tags",
        "-c:a",
        "aac",
        "-c:v",
        "copy",
        f"{pathlib.Path(mp3s[0]).stem}.m4b",
    ]
    print("Running the following command:\n" + " ".join(command))
    proc = await asyncio.create_subprocess_shell(
        " ".join(command),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    return stdout.decode().strip()
    # subprocess.run(command, shell=True)


async def main():
    folders = set()
    os.chdir(PATH)
    for file in glob.glob(f"**/*{FILETYPE}", recursive=True):
        FILE = pathlib.Path(file).absolute()
        folders.add(FILE.parent)

    folders = sorted(list(folders))

    loop = asyncio.get_running_loop()
    commands = asyncio.gather(*[spin_up(folder) for folder in folders])

    input(
        f"Executing on \n * "
        + "\n * ".join([str(folder) for folder in folders])
        + ". Ok?"
    )

    result = loop.run_until_complete(commands)
    print(f"{result=}")


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
