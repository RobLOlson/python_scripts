"""Organizes files in a directory by their extension."""

# Robert Olson
# pylint: disable=line-too-long

import os
import glob
import datetime
import shutil
import sys
import re
import argparse
import appdirs
import shutil

import rich.traceback
import rich
import toml

from pathlib import Path

rich.traceback.install(show_locals=True)

DEBUG = False
HANDLE_MISC = True

THIS_FILE = Path(__file__)

CONFIG_FILE = Path(appdirs.user_config_dir()) / "robolson" / "config" / "clean.toml"

if CONFIG_FILE.exists():
    with (open(CONFIG_FILE, "r")) as fp:
        SETTINGS = toml.load(fp)

else:
    base_config = THIS_FILE.parent / "config" / "clean.toml"
    os.makedirs(CONFIG_FILE.parent, exist_ok=True)
    shutil.copyfile(base_config, CONFIG_FILE)
    with (open(CONFIG_FILE, "r")) as fp:
        SETTINGS = toml.load(fp)

# Number of files in a folder that prompts more sorting
CROWDED_FOLDER = SETTINGS["CROWDED_FOLDER"]


FILE_TYPES = SETTINGS["FILE_TYPES"]

EXCLUSIONS = SETTINGS["EXCLUSIONS"]

MONTHS = SETTINGS["MONTHS"]
MONTHS.insert(0, None)

PROMPT = f"rob.{THIS_FILE.stem}> "


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
        # try:
        #     os.makedirs(target_folder, exist_ok=True)
        # except:
        #     pass

        while choice not in ["y", "yes", "n", "no", "a", "all", "d", "del"]:
            choice = input(
                f"mv '{file}' '{target_folder}\\{os.path.split(file)[1]}'\n(y)es/(n)o/yes_to_(a)ll/(d)el?\n{PROMPT}"
            )

        if choice in ["y", "yes"]:
            try:
                shutil.move(file, target_folder)

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
            shutil.move(file, target_folder)

        elif choice in ["n", "no"]:
            choice = ""

        elif choice in ["d", "del"]:
            os.makedirs("delete_me", exist_ok=True)
            shutil.move(file, os.path.normpath(f"delete_me/{file}"))
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

    # Create the parser
    my_parser = argparse.ArgumentParser(description="Clean up a folder.")

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

    args = my_parser.parse_args()

    CLI_path = args.Path

    if not os.path.isdir(CLI_path):
        rich.print(f"[red on black]The specified path ({CLI_path}) does not exist.")
        exit(1)
        root = input(
            f"Clean current directory ({os.getcwd()})?\nPress Enter to continue or enter a new path to clean.\n{PROMPT}"
        )

    else:
        root = CLI_path

    root = os.path.normpath(root)

    os.chdir(root)

    all_files = glob.glob("*.*")

    for file_name in all_files:
        if file_name in EXCLUSIONS:
            all_files.remove(file_name)

    file_groups = {}

    ARCHIVE_FOLDERS = list(FILE_TYPES.keys())

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
                choice = input(
                    f"{year} has {len(sorted_files)} top-level files and {len(pre_sorted_files)} already sorted files.  Sort by month (y/n)?\n{PROMPT}"
                )
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
        choice = input(
            "\nNon-archive folders detected.\n* {}\nArchive them (y/n)?\n{}".format(
                "\n* ".join(extra_folders), PROMPT
            )
        )
        if choice in ["y", "yes"]:
            move_folders = True

    if move_folders:
        for extra_folder in extra_folders:
            choice = input(f"{Path(extra_folder).resolve()}\nMove (y/n)?\n{PROMPT}")

            if choice in ["y", "yes"]:
                for i, default_folder in enumerate(ARCHIVE_FOLDERS):
                    print(f"\n{i+1}.) {default_folder}")
                target_folder = input(
                    f"\nmv '{extra_folder}' ???\nDestination?\n{PROMPT}"
                )
                try:
                    if int(target_folder) in list(range(1, len(ARCHIVE_FOLDERS) + 1)):
                        target_folder = ARCHIVE_FOLDERS[int(target_folder) - 1]
                except ValueError:
                    pass

                handle_files([extra_folder], folder=target_folder)
                choice = ""

    # Removes empty folders, except in programming because of git clone
    for target_folder in ARCHIVE_FOLDERS:
        remove_empty_dirs(os.path.join(root, target_folder))
        # if target_folder != "programming":
        #     remove_empty_dirs(os.path.join(root, target_folder))
        # else:
        #     remove_empty_dir(target_folder)


# END OF MAIN()

if __name__ == "__main__":
    main()
