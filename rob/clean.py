"""Organizes files in a directory by their extension."""

# Robert Olson
# pylint: disable=line-too-long

import os
import glob
import datetime
import shutil
import re
import argparse
import appdirs
import shutil
import shelve

import rich.traceback
import rich
import toml

from pathlib import Path

rich.traceback.install()


# Create the parser
my_parser = argparse.ArgumentParser(
    description="Clean up a folder.",
    add_help=True,
    epilog="(C) Rob",
)

# Add the arguments
my_parser.add_argument(
    "-p",
    "--path",
    metavar="dir",
    default=".",
    action="store",
    type=str,
    help="the directory to clean",
)

my_parser.add_argument(
    "-y",
    "--yes",
    default=False,
    action="store_true",
    help="skip all interactive prompts by answering 'yes'",
)

alt_mode = my_parser.add_mutually_exclusive_group(required=False)

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
# Created the Parser

_ARGS = my_parser.parse_args()

_CLI_PATH = _ARGS.path

DEBUG = False
HANDLE_MISC = True

THIS_FILE = Path(__file__)

_USER_CONFIG_FILE = (
    Path(appdirs.user_config_dir()) / "robolson" / "clean" / "config" / "clean.toml"
)
_DATA_FILE = Path(appdirs.user_data_dir()) / "robolson" / "clean" / "data" / "undo.db"

if not _DATA_FILE.exists():
    os.makedirs(_DATA_FILE.parent, exist_ok=True)
    db = shelve.open(str(_DATA_FILE))
    db.close()

_BASE_CONFIG_FILE = THIS_FILE.parent / "config" / "clean.toml"
with open(_BASE_CONFIG_FILE, "r") as fp:
    SETTINGS = toml.load(fp)

if _USER_CONFIG_FILE.exists():
    with (open(_USER_CONFIG_FILE, "r")) as fp:
        USER_SETTINGS = toml.load(fp)

SETTINGS.update(USER_SETTINGS)

CROWDED_FOLDER = SETTINGS["CROWDED_FOLDER"]  # number of files that is 'crowded'
FILE_TYPES = SETTINGS["FILE_TYPES"]  # dictionary of (folder, file-types) pairs
ARCHIVE_FOLDERS = list(FILE_TYPES.keys())
EXCLUSIONS = SETTINGS["EXCLUSIONS"]  # list of files to totally ignore
MONTHS = SETTINGS["MONTHS"]  # strings to use when writing names of months
MONTHS.insert(0, None)

PROMPT = f"rob.{THIS_FILE.stem}> "
_COMMANDS = []


def handle_files(files: list, folder: str = "misc", month: bool = False):
    """Organizes files by last modified date."""
    choice = ""

    for file in files:
        last_modified = datetime.datetime.fromtimestamp(os.path.getmtime(file))
        f_day = last_modified.day
        f_month = MONTHS[last_modified.month]

        file_size = os.stat(file).st_size

        f_year = last_modified.year
        if file_size > 150_000_000:
            target_folder = os.path.join("Large_Files", str(f_year))
        else:
            target_folder = os.path.join(folder, f"{folder} {str(f_year)}")

        if month:
            target_folder = os.path.join(
                target_folder, f"{folder} {last_modified.month} ({f_month}) {f_year}"
            )
        os.makedirs(target_folder, exist_ok=True)

        while choice not in ["y", "yes", "n", "no", "a", "all", "d", "del"]:
            rich.print(
                f"[yellow]mv '{file}' '{target_folder}\\{os.path.split(file)[1]}'\n[green](y)es[white] / [red](n)o[white] / [green]yes_to_(a)ll[white] / [red](d)el?"
            )
            choice = input(f"{PROMPT}") if not _ARGS.yes else "y"

        if choice in ["y", "yes"]:
            _COMMANDS.append((f"mv", Path(file), Path(target_folder) / Path(file)))
            try:
                choice = ""
                # shutil.move(file, target_folder)

            # File of Same Name Has Already Been Moved To Folder
            except shutil.Error:
                print(
                    f"Renamed '{file}' to '{f_month} {f_day} ({datetime.datetime.now().time().microsecond}) COPY {file}'.\n"
                )
                # os.rename(file, target_folder + "\\COPY " + file)
                Path(file).rename(
                    target_folder
                    + f"\\{Path(file).stem} {MONTHS[datetime.datetime.now().month]} {datetime.datetime.now().day} ({int((datetime.datetime.now() - datetime.datetime.min).total_seconds())}) COPY{Path(file).suffix}"
                )
                choice = ""

        elif choice in ["a", "all"]:
            _COMMANDS.append((f"mv", Path(file), Path(target_folder) / Path(file)))
            # shutil.move(file, target_folder)

        elif choice in ["n", "no"]:
            choice = ""

        elif choice in ["d", "del"]:
            os.makedirs("delete_me", exist_ok=True)
            _COMMANDS.append((f"mv", Path(file), Path(f"delete_me") / Path(file)))
            # shutil.move(file, os.path.normpath(f"delete_me/{file}"))
            # os.remove(file)
            choice = ""


def remove_empty_dir(path: str | Path):
    """Remove empty folder."""

    try:
        os.rmdir(path)
        print(f"Removing empty folder ({path}).")
    except OSError as e:
        if DEBUG:
            print(f"Could not remove folder: {e}")
        else:
            pass


def remove_empty_dirs(path: str | Path):
    """Recursively remove empty folders."""

    for trunk, dirnames, filenames in os.walk(path, topdown=False):
        for dirname in dirnames:
            remove_empty_dir(os.path.realpath(os.path.join(trunk, dirname)))

    remove_empty_dir(path)


# MAIN()
def main():

    if not os.path.isdir(_CLI_PATH):
        rich.print(f"[red on black]The specified path ({_CLI_PATH}) does not exist.")
        exit(1)
        # root = input(
        #     f"Clean current directory ({os.getcwd()})?\nPress Enter to continue or enter a new path to clean.\n{PROMPT}"
        # )

    else:
        root = _CLI_PATH

    if _ARGS.undo:
        undo()
        clean_up()
        exit(0)

    if _ARGS.config:
        create_config()
        exit(0)

    root = os.path.normpath(root)

    os.chdir(root)

    all_files = glob.glob("*.*")

    for file_name in all_files:
        if file_name in EXCLUSIONS:
            all_files.remove(file_name)

    file_groups = {}

    # put all files with same extension group into one list
    # and put that list in the file_groups dictionary
    # FOR EXAMPLE
    # file_groups["media"] will contain a list of all pictures in CWD
    # file_groups["zip files"] contain a list of all compressed archives in CWD
    # etc

    for file_type, extension_list in FILE_TYPES.items():
        if not extension_list:
            continue

        extension_pattern = re.compile(
            "(" + "|".join(extension_list) + ")$", re.IGNORECASE
        )
        file_groups[file_type] = [
            file_name
            for file_name in all_files
            if re.search(extension_pattern, file_name)
        ]

        for file in file_groups[file_type]:
            all_files.remove(file)

    # Any file-types not explicitly handled are moved to the miscellaneous folder
    if HANDLE_MISC and all_files:
        try:
            file_groups["misc"].extend(all_files)
        except KeyError:
            file_groups["misc"] = all_files
        print(f"moved {all_files}")

    # Do not target THIS file
    if __file__ in file_groups["programming"]:
        file_groups["programming"].remove(__file__)

    # Do not target THIS file
    if THIS_FILE in file_groups["programming"]:
        file_groups["programming"].remove(THIS_FILE)

    file_count = sum([len(file_group) for file_type, file_group in file_groups.items()])

    print(f"({file_count}) files/folders to move.\n")

    # Handles all files in file_groups
    for file_type, file_group in file_groups.items():
        if not file_group:
            continue

        handle_files(file_group, file_type)

        # Each file-type-folder should have one or more year folders (e.g., 'media/2020')
        year_folders = glob.glob(file_type + "/* ????")

        # Check year folders for crowdedness
        for year in year_folders:
            sorted_files = glob.glob(year + "/*.*")
            pre_sorted_files = glob.glob(year + "/*/*.*")

            if sorted_files and (
                len(sorted_files) + len(pre_sorted_files) > CROWDED_FOLDER
            ):
                rich.print(
                    f"{year} has {len(sorted_files)} top-level files and {len(pre_sorted_files)} already sorted files.  Sort by month (y/n)?"
                )
                choice = input(f"{PROMPT}") if not _ARGS.yes else "y"
                if choice in ["y", "yes"]:
                    handle_files(sorted_files, file_type, month=True)

    # Check for extra folders not generated by this program
    extra_folders = [
        elem
        for elem in glob.glob("*")
        if not Path(elem).suffix and elem not in ARCHIVE_FOLDERS
    ]

    move_folders = False
    if extra_folders:
        rich.print(
            "\n[yellow]Non-archive folders detected.[green]\n * {}\n[yellow]Archive them (y/n)?".format(
                " \n * ".join(extra_folders)
            )
        )
        choice = input(f"{PROMPT}") if not _ARGS.yes else "n"

        if choice in ["y", "yes"]:
            move_folders = True

    if move_folders:
        for extra_folder in extra_folders:
            rich.print(f"[yellow]{Path(extra_folder).resolve()}\nMove (y/n)?")
            choice = input(f"{PROMPT}") if not _ARGS.yes else "y"

            if choice in ["y", "yes"]:
                rich.print("[yellow]Archive Folders:")
                for i, default_folder in enumerate(ARCHIVE_FOLDERS):
                    rich.print(f"[green] {i+1}.) {default_folder}")

                rich.print(
                    f"[yellow]mv '{extra_folder}' ???\nDestination (enter number)?"
                )
                target_folder = input(f"{PROMPT}")
                try:
                    if 1 <= int(target_folder) < len(ARCHIVE_FOLDERS) + 1:
                        target_folder = ARCHIVE_FOLDERS[int(target_folder) - 1]

                        # _COMMANDS.append(("mv", [extra_folder], target_folder))
                        handle_files([extra_folder], folder=target_folder)
                        choice = ""
                except ValueError:
                    break

    rich.print("[red]Execute:")
    for command, file, target in _COMMANDS:
        rich.print(f"[yellow]mv {file} {target}")
    rich.print("[red]Are you sure? (y/n)")
    choice = input(f"{PROMPT}") if not _ARGS.yes else "y"
    if choice in ["y", "yes", "Y", "YES"]:
        execute_commands()
        with shelve.open(str(_DATA_FILE)) as db:
            db[_CLI_PATH] = _COMMANDS
            # pickle.dump(_COMMANDS, fp)

    clean_up()
    exit(0)


# END OF MAIN()


def clean_up():
    for target_folder in ARCHIVE_FOLDERS:
        remove_empty_dirs(os.path.join(_CLI_PATH, target_folder))


def undo():
    undo_commands = []

    with shelve.open(str(_DATA_FILE)) as db:
        try:
            old_commands = db[_CLI_PATH]
            for command, source, dest in old_commands:
                # _COMMANDS.append((command, (dest / source).absolute(), source.absolute()))
                undo_commands.append((command, dest, source))
                _COMMANDS.append((command, dest, source))

        except KeyError:
            rich.print(
                f"[red]No recorded commands executed on ({Path(_CLI_PATH).absolute()})."
            )
            exit(1)

    rich.print("[red]Execute:")
    for command, source, dest in undo_commands:
        rich.print(f"[yellow]mv '{source}' '{dest}'")
    rich.print("[red]Are you sure? (y/n)")
    choice = input(f"{PROMPT}") if not _ARGS.yes else "y"
    if choice in ["y", "yes", "Y", "YES"]:
        try:
            execute_commands(undo_commands)

        except Exception as e:
            with shelve.open(str(_DATA_FILE)) as db:
                del db[_CLI_PATH]
            print(e)
            exit(1)
        with shelve.open(str(_DATA_FILE)) as db:
            db[_CLI_PATH] = undo_commands

            # pickle.dump(_COMMANDS, _DATA_FILE)


def execute_commands(commands=_COMMANDS):
    for command, source, dest in commands:
        try:
            os.makedirs(dest.parent.absolute(), exist_ok=True)
            shutil.move(source.absolute(), dest.absolute())

        # File of Same Name Has Already Been Moved To Folder
        except shutil.Error as e:
            print(e)


def create_config():
    os.makedirs(_USER_CONFIG_FILE.parent, exist_ok=True)
    shutil.copyfile(_BASE_CONFIG_FILE, _USER_CONFIG_FILE)
    with open(_USER_CONFIG_FILE, "r") as fp:
        fp.seek(0)
        lines = fp.readlines()
        lines = ["# " + line for line in lines]
    with open(_USER_CONFIG_FILE, "w") as fp:
        fp.write("".join(lines))
    print(f"User config file created at:\n{_USER_CONFIG_FILE}")


if __name__ == "__main__":
    main()
