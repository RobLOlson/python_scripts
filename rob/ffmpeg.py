import glob
import multiprocessing
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List

import rich
import rich.traceback
from pydub.utils import mediainfo
from rich import pretty
from rich.progress import track

from .parser.ffmpeg_parser import ffmpeg_parser

pretty.install()
rich.traceback.install()

_ARGS = ffmpeg_parser.parse_args()

_PATH = Path(_ARGS.path)
_FILETYPES = _ARGS.filetype
# _ARGS.safe = _ARGS.safe
_CPUS = _ARGS.cpus
_COMMAND = _ARGS.command

_PROMPT = f"rob.{Path(__file__).stem}> "
_PROMPT_STYLE = "white on blue"
_ERROR_STYLE = "red on black"
_COMMAND_FILE = Path(os.getcwd()) / "ffmpeg_commands.ps1"


def command_only(folder: Path) -> None:
    """Generate a textfile containing the desired ffmpeg CLI commands."""
    os.chdir(folder)

    mp3s = []
    for filetype in _FILETYPES:
        temp = glob.glob(f"*{filetype}")
        mp3s.extend([Path(elem) for elem in temp if elem[0] != "~"])

    if not mp3s:
        return

    for i, mp3 in enumerate(mp3s):
        for char in str(mp3.stem):
            if ord(char) > 127 or char in "'":  # ascii chars have ord(char) < 128
                shutil.move(mp3, str(mp3).replace(char, ""))
                mp3s[i] = Path(str(mp3).replace(char, ""))
        # if "'" in str(mp3.stem):
        #     shutil.move(mp3, str(mp3).replace("'", ""))
        #     mp3s[i] = Path(str(mp3).replace("'", ""))

    concated = "|".join([str(elem.absolute()) for elem in mp3s])
    command = [
        "ffmpeg",
        "-i",
        f'''"concat:{concated}"''',
        # "-movflags", # Carry metadata over
        # "use_metadata_tags",
        "-map_metadata",
        "0",  # Use metadata from 0th input
        "-c:a",  # audio cocec
        "aac",
        "-b:a",  # bitrate
        "64k",
        "-c:v",
        "copy",
        f"'{Path(mp3s[0]).stem}.m4b'",
        "-y",
    ]

    if _ARGS.safe:
        command.remove("-y")

    with open(_COMMAND_FILE, "a") as fp:
        fp.write(" ".join(command) + "\n")

    print(" ".join(command))

    return


def concat_and_convert(folder: Path) -> None:
    """Spin up an ffmpeg process in target folder."""

    os.chdir(folder)

    # global _ARGS.safe

    mp3s = []
    for filetype in _FILETYPES:
        temp = glob.glob(f"*{filetype}")
        mp3s.extend([Path(elem) for elem in temp if elem[0] != "~"])

    if not mp3s:
        return

    # for i, mp3 in enumerate(mp3s):
    #     if "'" in str(mp3.stem):
    #         shutil.move(mp3, str(mp3).replace("'", ""))
    #         mp3s[i] = Path(str(mp3).replace("'", ""))

    for i, mp3 in enumerate(mp3s):
        for char in str(mp3.stem):
            if ord(char) > 127 or char in "'":  # ascii chars have ord(char) < 128
                shutil.move(mp3, str(mp3).replace(char, ""))
                mp3s[i] = Path(str(mp3).replace(char, ""))

    fp = open("files.txt", "w")
    for file in track(mp3s):
        fp.write(f"file '{file}'\n")

    fp.close()

    bit_rate = mediainfo(mp3s[0])["bit_rate"]

    command = [
        "ffmpeg",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        "files.txt",
        "-map_metadata",
        "0",  # Use metadata from 0th input
        "-movflags",  # Carry metadata over
        "use_metadata_tags",
        "-c:a",  # audio cocec
        "aac",  # audio codec
        "-b:a",  # bitrate
        f"{bit_rate}",
        "-vn",  # no video stream
        "-y",
        f"""{Path(mp3s[0]).stem}.m4b""",
    ]

    if _ARGS.safe:
        command.remove("-y")

    rich.print("[green]Executing:\n[yellow]" + " ".join(command))
    subprocess.run(command, shell=True)

    os.remove("files.txt")

    # <Transfer metadata>
    # inf = taglib.File(f"{mp3s[0]}")
    # outf = taglib.File(f"{Path(mp3s[0]).stem}.m4b")

    outf.tags = inf.tags
    outf.save()
    outf.close()
    inf.close()
    # </Transfer metadata>

    return


def interact() -> List[Path]:
    """Walk the user through configuring an ffmpeg call.

    Returns:
        folders (List[Path]): the list of folders to traverse and modify.
    """
    global _PATH
    global _FILETYPES
    # global _ARGS.safe
    global _CPUS
    global _COMMAND

    final_choice = False
    valid = True
    while not final_choice:
        style = _PROMPT_STYLE if valid else _ERROR_STYLE
        rich.print(
            f"""[{style}]Enter the path to work on.[/{style}]
\[default: {_PATH.parent.absolute()}]"""
        )
        choice = input(f"{_PROMPT}")

        if Path(choice).exists():
            _PATH = Path(choice)
            final_choice = True

        valid = False

    rich.print(f"[yellow]Working on '{_PATH.absolute()}'.\n")

    rich.print(
        f"[{_PROMPT_STYLE}]Which file type to work on?[/{_PROMPT_STYLE}] \[default: {_FILETYPES}]\n 1.) *.mp3\n 2.) *.wav\n 3.) *.ogg"
    )
    choice = input(f"{_PROMPT}")

    match choice:
        case "1" | "*.mp3" | ".mp3" | "mp3":
            _FILETYPES = [".mp3"]

        case "2" | "*.wav" | ".wav" | "wav":
            _FILETYPES = [".wav"]

        case "3" | "*.ogg" | ".ogg" | "ogg":
            _FILETYPES = [".ogg"]

        case _ as x:
            if x:
                _FILETYPES = [choice]

    rich.print(f"[yellow]Working on {_FILETYPES}'s.\n")

    folders = set()
    os.chdir(_PATH)
    for filetype in _FILETYPES:
        for file in glob.glob(f"**/*{filetype}", recursive=True):
            if _ARGS.safe and ".m4b" not in _FILETYPES:
                try:
                    os.remove(Path(f"{Path(file).parent}/{Path(file).stem}.m4b"))
                except FileNotFoundError:
                    pass
            target = Path(file).absolute()
            folders.add(target.parent)

    all_folders = sorted(list(folders))
    folders = all_folders[:]

    final_choice = False
    invalid = False
    while not final_choice:
        rich.print(f"Folders with {_FILETYPES}'s:")
        for count, folder in enumerate(all_folders):
            if folder in folders:
                rich.print(f" [green]{count+1}.) {folder}")
            else:
                rich.print(f" [red]{count+1}.) {folder}")

        style = _PROMPT_STYLE if not invalid else _ERROR_STYLE
        rich.print(
            f"\n[{style}]Toggle execution of folders by number or press Enter to continue."
        )
        choice = input(f"{_PROMPT}")
        invalid = False
        try:
            if not choice:
                final_choice = True

            choice = int(choice)
            if 1 <= choice <= len(all_folders):
                if all_folders[choice - 1] in folders:
                    folders.remove(all_folders[choice - 1])
                else:
                    folders.insert(choice - 1, all_folders[choice - 1])
            else:
                invalid = True

        except (SyntaxError, ValueError):
            invalid = True

    rich.print(
        f"[{_PROMPT_STYLE}]How many CPU cores to use?[/{_PROMPT_STYLE}] \[default: {_CPUS}]"
    )
    choice = input(f"{_PROMPT}")

    while True:
        try:
            if not choice:
                break
            else:
                _CPUS = int(choice)
                break
        except (TypeError, ValueError):
            rich.print(
                f"[red]Must supply an integer.[/red]\nHow many CPU cores to use \[default: {_CPUS}]?\n"
            )
            choice = input(f"{_PROMPT}")

    rich.print(f"[yellow]Using {_CPUS} core{'s' if _CPUS>1 else ''}.\n")

    rich.print(
        f"[{_PROMPT_STYLE}](1) Execute commands or \n(2) Generate command file?[/{_PROMPT_STYLE}]\n\[default {'1' if _COMMAND else '1'}]"
    )
    choice = input(f"{_PROMPT}")

    match choice:
        case "1" | "execute":
            _COMMAND = False
        case "2" | "generate" | "file":
            _COMMAND = True
            open(_COMMAND_FILE, "w").close()
        case _:
            pass

    return folders


def main() -> None:
    folders = set()

    if _COMMAND:
        open(_COMMAND_FILE, "w").close()

    if _ARGS.interact:
        folders = interact()

    else:
        os.chdir(_PATH)
        for filetype in _FILETYPES:
            for file in glob.glob(f"**/*{filetype}", recursive=True):
                if not _ARGS.safe:
                    try:
                        os.remove(Path(f"{Path(file).parent}/{Path(file).stem}.m4b"))
                    except FileNotFoundError:
                        pass
                target = Path(file).absolute()
                folders.add(target.parent)

        folders = sorted(list(folders))

        # optionally slice the list of folders
        match (bool(_ARGS.number), bool(_ARGS.start)):
            case (True, False):
                folders = folders[0 : _ARGS.number]
            case (False, True):
                folders = folders[_ARGS.start - 1 :]
            case (True, True):
                folders = folders[_ARGS.start - 1 : _ARGS.start - 1 + _ARGS.number]
            case _:
                pass

    if not folders:
        rich.print(f"[{_ERROR_STYLE}]No {_FILETYPES}'s found.")
        sys.exit(1)

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
            pool.map_async(concat_and_convert, folders).get()


if __name__ == "__main__":
    main()
