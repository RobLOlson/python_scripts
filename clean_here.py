"""Organizes files in a directory by their extension."""

# Robert Olson
# pylint: disable=line-too-long

import os
import glob
import re
import datetime
import shutil
import pdb
import sys

from pathlib import Path


# Number of files in a folder that prompts more sorting
CROWDED_FOLDER = 24

# Organize each extension group into a shared folder
FILE_TYPES = {
    "media" : ['.jpg', '.png', '.gif', '.mp3', '.bit', '.bmp', '.txt', '.pdf', '.leo', '.ogg', '.mp4', '.tif', '.psd', '.skba', '.lip'],
    "programming" : ['.py', '.ahk', '.json', '.ini', '.csv', '.nb', '.cdf', '.apk'],
    "syslinks" : ['.lnk', '.url'],
    "executables" :[' .exe', '.msi'],
    "zip files" : ['.zip', '.7z', '.tar', '.rar', '.gz'],
}

MONTHS = [None, "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

PROMPT = "(CLN)> "

def handle_files(files, folder="miscellaneous", month=False):
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
            target_folder = os.path.join(target_folder, f"{folder} {last_modified.month} ({f_month}) {f_year}")

        os.makedirs(target_folder, exist_ok=True)

        while choice not in ['y', 'yes', 'n', 'no', 'a', 'all', 'd', 'del']:
            choice = input(f"mv '{file}' '{target_folder}\\{os.path.split(file)[1]}'\n(y)es/(n)o/yes_to_(a)ll/(d)el?\n{PROMPT}")

        if choice in ['y', 'yes']:
            try:
                shutil.move(file, target_folder)

            # File of Same Name Has Already Been Moved To Folder
            except shutil.Error as e:
                print(f"Renamed '{file}' to '{f_month} {f_day} ({datetime.datetime.now().time().microsecond}) COPY {file}'.\n")
                # breakpoint()
                # os.rename(file, target_folder + "\\COPY " + file)
                Path(file).rename(target_folder+f"\\{Path(file).stem} {MONTHS[datetime.datetime.now().month]} {datetime.datetime.now().day} ({int((datetime.datetime.now() - datetime.datetime.min).total_seconds())}) COPY{Path(file).suffix}")
                choice = ''

        elif choice in ['a', 'all']:
            shutil.move(file, target_folder)

        elif choice in ['n', 'no']:
            choice = ''

        elif choice in ['d', 'del']:
            os.makedirs("delete_me", exist_ok=True)
            shutil.move(file, os.path.normpath(f"delete_me/{file}"))
            # os.remove(file)
            choice = ''


def remove_empty_dir(path):
    """Remove empty folder."""

    try:
        os.rmdir(path)
        print(f"Removing empty folder ({path}).")
    except OSError:
        pass

def remove_empty_dirs(path):
    """Recursively remove empty folders."""

    for trunk, dirnames, filenames in os.walk(path, topdown=False):
        for dirname in dirnames:
            remove_empty_dir(os.path.realpath(os.path.join(trunk, dirname)))



# MAIN()
def main():
    root = input(f"Clean current directory ({os.getcwd()})?\nPress Enter to continue or enter a new path to clean.\n{PROMPT}")

    # Allows user to use environment variables to set execution directory
    if root and root[0] == '$':
        root = os.environ[root[1:]]

    root = os.path.normpath(root)

    os.chdir(root)

    all_files = glob.glob("*.*")

    file_groups = {}


    # put all files with same extension group into one list
    # and put that list in the file_groups dictionary
    # FOR EXAMPLE
    # file_groups["media"] will contain a list of all pictures in CWD
    # file_groups["zip files"] contain a list of all compressed archives in CWD
    # etc
    for file_type, extension_list in FILE_TYPES.items():
        extension_pattern = re.compile("("+"|".join(extension_list)+")$")
        file_groups[file_type] = [file_name for file_name in all_files if re.search(extension_pattern, file_name)]
        for file in file_groups[file_type]:
            all_files.remove(file)

        file_groups["misc"] = all_files

    # Do not target THIS file
    if __file__ in file_groups["programming"]:
        file_groups["programming"].remove(__file__)

    # Do not target THIS file
    if os.path.normpath(sys.argv[0]) in file_groups["programming"]:
        file_groups["programming"].remove(os.path.normpath(sys.argv[0]))

    file_count = sum([len(file_group) for file_type, file_group in file_groups.items()])

    print(f"({file_count}) files/folders to move.\n")

    # Handles all files in file_groups
    for file_type, file_group in file_groups.items():
        handle_files(file_group, file_type)

        # Each file-type-folder should have one or more year folders (e.g., 'media/2020')
        year_folders = glob.glob(file_type+"/* ????")

        # Check year folders for crowdedness
        for year in year_folders:
            sorted_files = glob.glob(year+"/*.*")
            pre_sorted_files = glob.glob(year+"/*/*.*")

            if len(sorted_files) and (len(sorted_files) + len(pre_sorted_files) > CROWDED_FOLDER):
                choice = input(f"{year} has {len(sorted_files)} top-level files and {len(pre_sorted_files)} already sorted files.  Sort by month (y/n)?\n{PROMPT}")
                if choice in ['y', 'yes']:
                    handle_files(sorted_files, file_type, month=True)

    # Removes empty folders, except in programming because of git clone
    for target_folder in FILE_TYPES.keys():
        if target_folder != "programming":
            remove_empty_dirs(os.path.join(root, target_folder))

# END OF MAIN()

if __name__ == "__main__":
    main()
