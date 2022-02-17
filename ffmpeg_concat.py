import glob
import pathlib
import os
import time
import asyncio
import argparse
import logging
import sys
import subprocess
import multiprocessing

from concurrent.futures import ProcessPoolExecutor

import pydub

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
    nargs=1,
    default=".mp3",
    choices=[".mp3", ".wav", ".ogg"],
    action="store",
    type=str,
    help="the filetype to concatenate, e.g., '.mp3'",
)

my_parser.add_argument(
    "-p",
    "--path",
    metavar="path",
    nargs=1,
    default=".",
    action="store",
    type=str,
    help="the path to files to be concatted",
)

my_parser.add_argument('-o',
                       '--overwrite',
                       # metavar="overwrite",
                       action='store_true',
                       help='force ffmpeg to overwrite existing files')

# Execute the parse_args() method
_ARGS = my_parser.parse_args()

_PATH = _ARGS.path
_FILETYPE = _ARGS.filetype
_OVERWRITE = _ARGS.overwrite


def spin_up(folder):
    """Spin up an ffmpeg process in target folder.

    Args:
        folder: path to folder that contains audio files
    """

    os.chdir(folder)
    mp3s = glob.glob(f"*{_FILETYPE}")
    # concated = "|".join(mp3s)

    if _OVERWRITE:
        try:
            os.remove(f"{pathlib.Path(mp3s[0]).stem}.m4b")
        except FileNotFoundError as e:
            pass

    # Merge audio files
    combined = pydub.AudioSegment.empty()

    match _FILETYPE:
        case ".mp3":
            for file in mp3s:
                combined += pydub.AudioSegment.from_mp3(file)

        case ".wav":
            for file in mp3s:
                combined += pydub.AudioSegment.from_wav(file)

        case ".ogg":
            for file in mp3s:
                combined += pydub.AudioSegment.from_ogg(file)

    combined.export(f"{pathlib.Path(mp3s[0]).stem}-full{_FILETYPE}")
    # End of Merge audio files

    # Convert audio files
    command = [
        "ffmpeg",
        "-i",
        # f"concat:{concated}",
        f"{pathlib.Path(mp3s[0]).stem}-full{_FILETYPE}",
        "-movflags",
        "use_metadata_tags",
        "-c:a",
        "aac",
        "-c:v",
        "copy",
        f"{pathlib.Path(mp3s[0]).stem}.m4b",
    ]

    print("Running the following command:\n" + " ".join(command))
    subprocess.run(command, shell=True)
    # End of Convert audio files

    # Clean up temporary files
    os.remove(f"{pathlib.Path(mp3s[0]).stem}-full{_FILETYPE}")


def main():
    folders = set()
    os.chdir(_PATH)
    for file in glob.glob(f"**/*{_FILETYPE}", recursive=True):
        target = pathlib.Path(file).absolute()
        folders.add(target.parent)

    folders = sorted(list(folders))

    input(
        f"Executing on \n * "
        + "\n * ".join([str(folder) for folder in folders])
        + ". \nOk?"
    )

    with multiprocessing.Pool(5) as pool:
        pool.map_async(spin_up, folders).get()

if __name__ == "__main__":
    main()
