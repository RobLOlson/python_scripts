import glob
import pathlib
import os
import time
import asyncio
import argparse
import logging
import sys

import nest_asyncio

# Hack needed to make asyncio loop compatible with other loops that may be running
nest_asyncio.apply()

logging.getLogger("asyncio").setLevel(logging.INFO)

# Create the parser
my_parser = argparse.ArgumentParser(
    prog=sys.argv[0],
    allow_abbrev=True,
    add_help=True,
    description="Concatenates audio files using ffmpeg.",
    epilog="(C) Rob",
)

# Add the arguments
my_parser.add_argument(
    "-f",
    "--filetype",
    metavar="filetype",
    nargs="?",
    default=".mp3",
    action="store",
    type=str,
    help="the filetype to concatenate, e.g., '.mp3'",
)

my_parser.add_argument(
    "-p",
    "--path",
    metavar="path",
    nargs="?",
    default=".",
    action="store",
    type=str,
    help="the path to files to be concatted",
)

# Execute the parse_args() method
args = my_parser.parse_args()

PATH = args.path
FILETYPE = args.filetype


async def spin_up(folder):
    """Spin up an ffmpeg process in target folder.

    Args:
        folder: path to folder that contains audio files
    """

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
        target = pathlib.Path(file).absolute()
        folders.add(target.parent)

    folders = sorted(list(folders))

    loop = asyncio.get_running_loop()
    commands = asyncio.gather(*[spin_up(folder) for folder in folders])

    input(
        f"Executing on \n * "
        + "\n * ".join([str(folder) for folder in folders])
        + ". \nOk?"
    )

    result = loop.run_until_complete(commands)
    print(f"{result=}")


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
