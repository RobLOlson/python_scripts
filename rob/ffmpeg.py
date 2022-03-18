import glob
import pathlib
import os
import time
import argparse
import subprocess
import multiprocessing
import time
import appdirs
import random

import pydub
import rich

from rich.progress import track
from rich.console import Console
from pydub.utils import mediainfo

# Create the parser
my_parser = argparse.ArgumentParser(
    # prog=sys.argv[0],
    prog="py -m rob."+pathlib.Path(__file__).stem,
    allow_abbrev=True,
    add_help=True,
    description="Concatenates audio files to m4b using ffmpeg.",
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
    help="the filetype to concatenate (valid options: '.mp3', '.ogg' or '.wav')",
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

my_parser.add_argument(
    "-c",
    "--cpus",
    metavar="cpus",
    default=1,
    action="store",
    type=int,
    help="the number of processor cores to utilize",
)

my_parser.add_argument(
    "-n",
    "--number",
    metavar="number",
    default=0,
    action="store",
    type=int,
    help="the number of folders to limit execution on",
)

my_parser.add_argument(
    "-s",
    "--start",
    metavar="start_number",
    default=0,
    action="store",
    type=int,
    help="start execution on Nth folder (ignoring previous)",
)

my_parser.add_argument('--safe',
                       action='store_true',
                       default=False,
                       help='force ffmpeg to ask for overwrite permissions')

my_parser.add_argument('--command',
                       action='store_true',
                       help='Only print the corresponding ffmpeg command(s)')

my_parser.add_argument('-i',
                       '--interact',
                       action='store_true',
                       help='supply arguments manually via prompt')

my_parser.add_argument('-l',
                       '--local',
                       action='store_true',
                       help='store temporary files on local machine')

# Execute the parse_args() method
_ARGS = my_parser.parse_args()

_PATH = pathlib.Path(_ARGS.path)
_FILETYPE = _ARGS.filetype
_SAFE = _ARGS.safe
_CPUS = _ARGS.cpus
_COMMAND = _ARGS.command

_PROMPT = f"rob.{pathlib.Path(__file__).stem}> "
_PROMPT_STYLE = "white on blue"
_TEMP_FOLDER = pathlib.Path(f"{appdirs.user_data_dir()}") / "robolson" / "ffmpeg" / "temp"
_COMMAND_FILE = pathlib.Path(os.getcwd()) / "ffmpeg_commands.ps1"

def command_only(folder):
    os.chdir(folder)

    console = Console()

    mp3s = glob.glob(f"*{_FILETYPE}")
    mp3s = [pathlib.Path(elem) for elem in mp3s if elem[0] != '~']

    if not mp3s:
        return

    concated = "|".join([str(elem.absolute()) for elem in mp3s])
    command = [
        "ffmpeg",
        "-i",
        f"'concat:{concated}'",
        "-movflags", # Carry metadata over
        "use_metadata_tags",
        "-c:a", # audio cocec
        "aac",
        "-b:a", # bitrate
        "64k",
        "-c:v",
        "copy",
        f"{pathlib.Path(mp3s[0]).stem}.m4b",
        "-y",
    ]

    if _SAFE:
        command.remove("-y")

    with open(_COMMAND_FILE, "a") as fp:
        fp.write(" ".join(command)+"\n")

    console.out(" ".join(command))

    return

def spin_up(folder):
    """Spin up an ffmpeg process in target folder.

    Args:
        folder: path to folder that contains audio files
    """

    os.chdir(folder)

    global _SAFE

    mp3s = glob.glob(f"*{_FILETYPE}")
    mp3s = [pathlib.Path(elem) for elem in mp3s if elem[0] != '~']


    if not mp3s:
        return

    concated = "|".join([str(elem.absolute()) for elem in mp3s])

    salt = ""
    if _ARGS.local:
        salt = "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=10))
        os.makedirs(_TEMP_FOLDER, exist_ok=True)
        _temp_file = _TEMP_FOLDER / f"{salt}~{pathlib.Path(mp3s[0]).stem}-full{_FILETYPE}"
    else:
        _temp_file = f"~{pathlib.Path(mp3s[0]).stem}-full{_FILETYPE}"


    command = [
        "ffmpeg",
        "-i",
        str(_temp_file), # f"~{pathlib.Path(mp3s[0]).stem}-full{_FILETYPE}",
        "-movflags", # Carry metadata over
        "use_metadata_tags",
        "-c:a", # audio cocec
        "aac",
        "-b:a", # bitrate
        "64k",
        "-c:v",
        "copy",
        f"{pathlib.Path(mp3s[0]).stem}.m4b",
        "-y"
    ]

    if _SAFE:
        command.remove('-y')

    bit_rate = mediainfo(mp3s[0])['bit_rate']

    # Merge audio files

    if len(mp3s)==1:
        combined = pydub.AudioSegment.from_mp3(mp3s[0])

    else:
        combined = pydub.AudioSegment.empty()
        match _FILETYPE:
            case ".mp3":
                for file in track(mp3s):
                    combined += pydub.AudioSegment.from_mp3(file)
                    # combined += pydub.AudioSegment.from_file(file, "mp3")

            case ".wav":
                for file in track(mp3s):
                    combined += pydub.AudioSegment.from_wav(file)

            case ".ogg":
                for file in track(mp3s):
                    combined += pydub.AudioSegment.from_ogg(file)

    rich.print(f"[yellow]Writing temp file ({pathlib.Path(_temp_file).absolute()}) to disk.")
    # combined.export(_temp_file, tags={"test":"TEST"}, bitrate=bit_rate)
    combined.export(
    _temp_file,
    format="ipod",
    # bitrate=bit_rate,
    parameters=["-movflags", "use_metadata_tags", "-c:a", "aac", "-c:v", "copy", "-b:a", "64k"],
)

    # End of Merge audio files

    count = 0
    while not pathlib.Path(_temp_file).exists():
        count += 1
        rich.print(f"[red]Merged file not found.[/red]  Retry {count}/5 in 10s.", end="\r", flush=True)
        if count > 6:
            print("Merged file not found.  Exiting...")
            exit(1)
        time.sleep(10)

    rich.print(f"\n[green]Merged file ({pathlib.Path(_temp_file).absolute()}) created.[/green]\n")

    # Convert audio files

    rich.print("\nRunning the following command:\n[yellow]" + " ".join(command) + "[/yellow]\n")
    subprocess.run(command, shell=True)
    # End of Convert audio files

    if salt:
        rich.print(f"[red]Removing temp file ({pathlib.Path(_temp_file).absolute()}).")
        os.remove(_temp_file)

    rich.print(f"[green]Finished {folder}.\n")

    return

def interact():
    global _PATH
    global _FILETYPE
    global _SAFE
    global _CPUS
    global _COMMAND

    final_choice = False
    valid = True
    while not final_choice:
        rich.print(f"[{_PROMPT_STYLE if valid else 'red on red'}]Enter the path to work on.[/{_PROMPT_STYLE if valid else 'red on red'}]\n\[default: {_PATH.parent.absolute()}]")
        choice = input(f"{_PROMPT}")

        if pathlib.Path(choice).exists():
            _PATH = pathlib.Path(choice)
            final_choice = True

        valid = False

    rich.print(f"[yellow]Working on '{_PATH.absolute()}'.\n")

    rich.print(f"[{_PROMPT_STYLE}]Which file type to work on?[/{_PROMPT_STYLE}] \[default: {_FILETYPE}]\n 1.) *.mp3\n 2.) *.wav\n 3.) *.ogg")
    choice = input(f"{_PROMPT}")

    match choice:
        case "1" | "*.mp3" | ".mp3" | "mp3":
            _FILETYPE = ".mp3"

        case "2" | "*.wav" | ".wav" | "wav":
            _FILETYPE = ".wav"

        case "3" | "*.ogg" | ".ogg" | "ogg":
            _FILETYPE = ".ogg"

        case _:
            pass

    rich.print(f"[yellow]Working on {_FILETYPE}'s.\n")

    folders = set()
    os.chdir(_PATH)
    for file in glob.glob(f"**/*{_FILETYPE}", recursive=True):
        if _SAFE:
            try:
                os.remove(pathlib.Path(f"{pathlib.Path(file).parent}/{pathlib.Path(file).stem}.m4b"))
            except FileNotFoundError as e:
                pass
        target = pathlib.Path(file).absolute()
        folders.add(target.parent)

    all_folders = sorted(list(folders))
    folders = all_folders[:]

    final_choice = False
    invalid = False
    while not final_choice:
        rich.print(f"Folders with {_FILETYPE}'s:")
        for count, folder in enumerate(all_folders):
            if folder in folders:
                rich.print(f" [green]{count+1}.) {folder}")
            else:
                rich.print(f" [red]{count+1}.) {folder}")

        rich.print(f"\n[{'red on red' if invalid else _PROMPT_STYLE}]Toggle execution of folders by number or press Enter to continue.")
        choice = input(f"{_PROMPT}")
        invalid = False
        try:
            if not choice:
                final_choice = True

            choice = int(choice)
            if 1 <= choice <= len(all_folders):
                if all_folders[choice-1] in folders:
                    folders.remove(all_folders[choice-1])
                else:
                    folders.insert(choice-1, all_folders[choice-1])
            else:
                invalid = True

        except (SyntaxError, ValueError):
            invalid = True

    rich.print(f"[{_PROMPT_STYLE}]How many CPU cores to use?[/{_PROMPT_STYLE}] \[default: {_CPUS}]")
    choice = input(f"{_PROMPT}")

    while True:
        try:
            if not choice:
                break
            else:
                _CPUS = int(choice)
                break
        except (TypeError, ValueError):
            rich.print(f"[red]Must supply an integer.[/red]\nHow many CPU cores to use \[default: {_CPUS}]?\n")
            choice = input(f"{_PROMPT}")

    rich.print(f"[yellow]Using {_CPUS} core{'s' if _CPUS>1 else ''}.\n")

    rich.print(f"[{_PROMPT_STYLE}](1) Execute commands or \n(2) Generate command file?[/{_PROMPT_STYLE}]\n\[default {'1' if _COMMAND else '1'}]")
    choice = input(f"{_PROMPT}")

    match choice:
        case '1' | 'execute':
            _COMMAND = False
        case '2' | 'generate' | 'file':
            _COMMAND = True
            open(_COMMAND_FILE, "w").close()
        case _:
            pass

    return folders

def main():
    folders = set()

    if _COMMAND:
        open(_COMMAND_FILE, "w").close()

    if _ARGS.interact:
        folders = interact()

    else:
        os.chdir(_PATH)
        for file in glob.glob(f"**/*{_FILETYPE}", recursive=True):
            if not _SAFE:
                try:
                    os.remove(pathlib.Path(f"{pathlib.Path(file).parent}/{pathlib.Path(file).stem}.m4b"))
                except FileNotFoundError as e:
                    pass
            target = pathlib.Path(file).absolute()
            folders.add(target.parent)

        folders = sorted(list(folders))

        # optionally slice the list of folders
        match (bool(_ARGS.number), bool(_ARGS.start)):
            case (True, False):
                folders = folders[0:_ARGS.number]
            case (False, True):
                folders = folders[_ARGS.start-1:]
            case (True, True):
                folders = folders[_ARGS.start-1:_ARGS.start-1+_ARGS.number]
            case _:
                pass

    rich.print(
        f"[{_PROMPT_STYLE}]{'Compiling' if _COMMAND else 'Executing'} on[/{_PROMPT_STYLE}]\n * "
        + "\n * ".join([str(folder) for folder in folders])
        + f". \n[{_PROMPT_STYLE}]Using {_CPUS} core. Ok?"
    )
    input(f"{_PROMPT}")


    if _COMMAND:
        with multiprocessing.Pool(_CPUS) as pool:
            pool.map_async(command_only, folders).get()
    else:
        with multiprocessing.Pool(_CPUS) as pool:
            pool.map_async(spin_up, folders).get()

if __name__ == "__main__":
    main()
