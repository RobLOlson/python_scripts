import argparse
from pathlib import Path

ffmpeg_parser = argparse.ArgumentParser(
    # prog=sys.argv[0],
    prog="py -m rob.ffmpeg",
    allow_abbrev=True,
    add_help=True,
    description="Concatenates audio files to a single .m4b using ffmpeg.",
    epilog="(C) Rob",
)

# Add the arguments
ffmpeg_parser.add_argument(
    "-f",
    "--filetype",
    metavar="filetype",
    nargs="+",
    default=[".mp3", ".m4a", ".ogg"],
    action="store",
    type=str,
    help="the filetype to concatenate (valid options: '.mp3', '.ogg' or '.wav')",
)

ffmpeg_parser.add_argument(
    "-p",
    "--path",
    metavar="path",
    nargs=1,
    default=".",
    action="store",
    type=str,
    help="the path to files to be concatted",
)

ffmpeg_parser.add_argument(
    "-c",
    "--cpus",
    metavar="cpus",
    default=1,
    action="store",
    type=int,
    help="the number of processor cores to utilize",
)

ffmpeg_parser.add_argument(
    "-n",
    "--number",
    metavar="number",
    default=0,
    action="store",
    type=int,
    help="the number of folders to limit execution on",
)

ffmpeg_parser.add_argument(
    "-s",
    "--start",
    metavar="start_number",
    default=0,
    action="store",
    type=int,
    help="start execution on Nth folder (ignoring previous)",
)

ffmpeg_parser.add_argument(
    "--safe",
    action="store_true",
    default=False,
    help="force ffmpeg to ask for overwrite permissions",
)

ffmpeg_parser.add_argument(
    "--command",
    action="store_true",
    help="Only print the corresponding ffmpeg command(s)",
)

ffmpeg_parser.add_argument(
    "-i", "--interact", action="store_true", help="supply arguments manually via prompt"
)
