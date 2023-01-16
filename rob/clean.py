"""Organizes files in a directory by their extension."""

# Robert Olson
# pylint: disable=line-too-long

import datetime
import glob
import os
import re
import shelve
import shutil
import statistics
from pathlib import Path

import appdirs
import rich
import rich.traceback
import toml

from .parser.clean_parser import clean_parser

clean_parser.prog = "py -m rob." + Path(__file__).stem

_ARGS = clean_parser.parse_args()

_CLI_PATH = Path(_ARGS.path)

_THIS_FILE = Path(__file__)

_PROMPT = f"rob.{Path(__file__).stem}> "
_PROMPT_STYLE = "[white on blue]"
_ERROR_STYLE = "[red on black]"

_USER_CONFIG_FILE = (
    Path(appdirs.user_config_dir()) / "robolson" / "clean" / "config" / "clean.toml"
)
_UNDO_FILE = Path(appdirs.user_data_dir()) / "robolson" / "clean" / "data" / "undo.db"
_BLACKLIST_FILE = (
    Path(appdirs.user_data_dir()) / "robolson" / "clean" / "data" / "ignore.db"
)

if not _UNDO_FILE.exists():
    os.makedirs(_UNDO_FILE.parent, exist_ok=True)
    db = shelve.open(str(_UNDO_FILE))
    db.close()

_BASE_CONFIG_FILE = _THIS_FILE.parent / "config" / "clean.toml"
with open(_BASE_CONFIG_FILE, "r") as fp:
    _SETTINGS = toml.load(fp)

if _USER_CONFIG_FILE.exists():
    with (open(_USER_CONFIG_FILE, "r")) as fp:
        USER_SETTINGS = toml.load(fp)

_SETTINGS.update(USER_SETTINGS)

# _CROWDED_FOLDER = _SETTINGS["CROWDED_FOLDER"]  # number of files that is 'crowded'
_FILE_TYPES: dict[str, list[str]] = _SETTINGS[
    "FILE_TYPES"
]  # dictionary of (folder, file-types) pairs
ARCHIVE_FOLDERS = list(_FILE_TYPES.keys())
_EXCLUSIONS = _SETTINGS["EXCLUSIONS"]  # list of files to totally ignore
MONTHS = _SETTINGS["MONTHS"]  # strings to use when writing names of months
MONTHS.insert(0, None)

_COMMANDS = []


def generate_extension_handler(file_types: dict[str, list[str]]) -> dict[str, str]:
    """Returns a dictionary that associates extension keys with their assigned file type / folder name."""
    extension_handler: dict[str, str] = {}
    for file_type in file_types.keys():
        for extension in file_types[file_type]:
            extension_handler[extension] = file_type

    return extension_handler


_EXTENSION_HANDLER = generate_extension_handler(_FILE_TYPES)


def isolate_crowded_folders(
    folders: list[Path], crowded_threshold: int = 20
) -> list[Path]:
    """Return a list of directories with many files inside."""

    crowded = []

    for folder in folders:
        if folder.is_file():
            continue

        if len(list(folder.glob("*.*"))) > crowded_threshold:
            crowded.append(folder)

    return crowded


def approve_list(target: list, desc: str = "") -> list:
    """Returns a user-approved subset of target list."""

    if not target:
        return []

    approved_targets = []
    final_choice = False
    invalid = False
    while not final_choice:
        rich.print(desc)
        for count, item in enumerate(target):
            if item in approved_targets:
                rich.print(f" [green]{count+1}.) {item}")
            else:
                rich.print(f" [red]{count+1}.) {item}")

        style = _PROMPT_STYLE if not invalid else _ERROR_STYLE
        rich.print(
            f"\n{style}Toggle items by entering their associated list index, enter 'a' to toggle ALL items, or press Enter to continue."
        )
        choice = input(f"{_PROMPT}")
        invalid = False
        try:
            if not choice:
                final_choice = True

            if choice in ["a", "A", "all", "ALL"]:
                count = 1
                while count <= len(target):
                    if target[count - 1] in approved_targets:
                        approved_targets.remove(target[count - 1])
                    else:
                        approved_targets.insert(count - 1, target[count - 1])

                    count += 1

                continue

            choice = int(choice)
            if 1 <= choice <= len(target):
                if target[choice - 1] in approved_targets:
                    approved_targets.remove(target[choice - 1])
                else:
                    approved_targets.insert(choice - 1, target[choice - 1])
            else:
                invalid = True

        except (SyntaxError, ValueError):
            invalid = True

    return approved_targets


def approve_dict(target: dict, desc: str = "") -> dict:
    """Returns a user-approved subset of target dictionary."""

    if not target:
        return {}

    approved_keys = []
    frozen_keys = list(target.keys())
    final_choice = False
    invalid = False
    while not final_choice:
        rich.print(desc)
        for count, key in enumerate(frozen_keys):
            if key in approved_keys:
                rich.print(f" [green]{count+1}.) {key}[yellow]->[green]{target[key]}")
            else:
                rich.print(f" [red]{count+1}.) {key}[yellow]->[red]{target[key]}")

        style = _PROMPT_STYLE if not invalid else _ERROR_STYLE
        rich.print(
            f"\n{style}Toggle items by entering their associated list index, or enter 'a' to toggle ALL or press Enter to continue."
        )
        choice = input(f"{_PROMPT}")
        invalid = False
        try:
            if not choice:
                final_choice = True

            if choice in ["a", "A", "all", "ALL"]:
                count = 1
                while count <= len(target):
                    if frozen_keys[count - 1] in approved_keys:
                        approved_keys.remove(frozen_keys[count - 1])
                    else:
                        approved_keys.insert(count - 1, frozen_keys[count - 1])

                    count += 1

                continue

            choice = int(choice)
            if 1 <= choice <= len(target):
                if frozen_keys[choice - 1] in approved_keys:
                    approved_keys.remove(frozen_keys[choice - 1])
                else:
                    approved_keys.insert(choice - 1, frozen_keys[choice - 1])
            else:
                invalid = True

        except (SyntaxError, ValueError):
            invalid = True

    return {key: target[key] for key in approved_keys}


def uncrowd_folder(folder: Path, yes_all: bool = False) -> dict[Path, Path]:
    """Return a dictionary that associates crowded files in a folder with a better Path."""

    files = folder.glob("*.*")
    file_targets: dict[Path, Path] = {}
    for file in files:
        last_modified = datetime.datetime.fromtimestamp(
            os.path.getmtime(file.absolute())
        )

        f_month = MONTHS[last_modified.month]
        f_year = last_modified.year

        target_folder = (
            Path(f"{file.parent}")
            / f"{file.parent.parent.name} {last_modified.month} ({f_month}) {f_year}"
        )

        file_targets[file] = target_folder / file.name

    if yes_all:
        return file_targets
    else:
        return approve_dict(
            file_targets, f"Select files in '{folder.absolute()}' to uncrowd:"
        )


def associate_files(
    files: list[Path],
    root: Path = Path("."),
    extension_handler: dict[str, str] | None = None,
    default_folder: Path = Path("misc"),
    yes_all: bool = True,
) -> dict[Path, Path]:
    """Returns a dictionary that associates passed files with their most organized location."""

    if not extension_handler:
        extension_handler = {}

    os.chdir(root.absolute())

    file_targets: dict[Path, Path] = {}

    uncrowded_pattern = re.compile(r"\w+ \d\d? \(\w+\) \d\d\d\d")

    for file in files:
        last_modified = datetime.datetime.fromtimestamp(os.path.getmtime(file))
        file_type_folder = extension_handler.get(file.suffix, default_folder.name)

        f_year: str = str(last_modified.year)
        f_month: str = str(last_modified.month)
        target_folder = Path(f"{file_type_folder}") / f"{file_type_folder} {f_year}"

        sub_folders = [folder for folder in target_folder.glob("*") if folder.is_dir()]

        # if target folder has sub-folders from previous uncrowding, follow the uncrowded naming protocol
        if any(uncrowded_pattern.match(folder.name) for folder in sub_folders):
            target_folder = (
                target_folder
                / f"{file_type_folder} {last_modified.month} ({f_month}) {f_year}"
            )

        if yes_all:
            file_targets[file] = target_folder / file.name

        else:
            choice = ""
            while choice not in ["y", "yes", "n", "no", "a", "all", "d", "del"]:
                rich.print(
                    f"[yellow]mv '{file.name if Path(file.name).exists() else file.absolute()}' '{target_folder / file.name}'\n[green](y)es[white] / [red](n)o[white] / [green]yes_to_(a)ll[white] / [red](d)el?"
                )
                choice = input(f"{_PROMPT}")

            match choice:
                case "y" | "yes":
                    file_targets[file] = target_folder / file.name

                case "a" | "all":
                    file_targets[file] = target_folder / file.name
                    yes_all = True

                case "d" | "del":
                    file_targets[file] = Path("delete_me") / file.name

    return file_targets


def handle_files(
    files: list[str],
    folder: str = "misc",
    month: bool = False,
    yes_all: bool = _ARGS.yes,
) -> None:
    """Organizes files by last modified date."""
    choice = ""

    for file in files:
        last_modified = datetime.datetime.fromtimestamp(os.path.getmtime(file))
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
            choice = input(f"{_PROMPT}") if not yes_all else "y"

        match choice:
            case "y" | "yes":
                _COMMANDS.append((f"mv", Path(file), Path(target_folder) / Path(file)))

            case "a" | "all":
                _COMMANDS.append((f"mv", Path(file), Path(target_folder) / Path(file)))
                yes_all = True

            case "d" | "del":
                os.makedirs("delete_me", exist_ok=True)
                _COMMANDS.append((f"mv", Path(file), Path(f"delete_me") / Path(file)))


#  ^^^^^^^^^^^^^^^^^^^^^^^^^^
#  </ def handle_files()>
#  ^^^^^^^^^^^^^^^^^^^^^^^^^^


def remove_empty_dir(path: str | Path):
    """Remove empty folder."""

    try:
        os.rmdir(path)
        print(f"Removing empty folder ({path}).")
    except OSError as e:
        if _ARGS.debug:
            print(f"Could not remove folder: {e}")
        else:
            pass


def remove_empty_dirs(path: str | Path):
    """Recursively remove empty folders."""

    for trunk, dirnames, _ in os.walk(path, topdown=False):
        for dirname in dirnames:
            remove_empty_dir(os.path.realpath(os.path.join(trunk, dirname)))

    remove_empty_dir(path)


def clean_up() -> None:
    for target_folder in ARCHIVE_FOLDERS:
        remove_empty_dirs(os.path.join(_CLI_PATH, target_folder))


def undo() -> None:
    undo_commands = {}
    breakpoint()
    with shelve.open(str(_UNDO_FILE)) as db:
        try:
            old_commands = db[str(_CLI_PATH.absolute())]
            for source, dest in old_commands.items():
                undo_commands[dest] = _CLI_PATH.absolute() / source
                # undo_commands.append((command, dest, source))
                # _COMMANDS.append((command, dest, source))

        except KeyError:
            rich.print(
                f"[red]No recorded commands executed on ({Path(_CLI_PATH).absolute()})."
            )
            exit(1)

    preview_mvs(undo_commands)

    # rich.print("[red]Execute:")
    # skipped = []
    # for command, source, dest in undo_commands:
    #     if source.exists():
    #         rich.print(f"[yellow]mv '{source}' '{dest}'")
    #     else:
    #         rich.print(f"[red]mv '{source}' '{dest}' (ERROR 404)")
    #         skipped.append((command, source, dest))

    # for skip in skipped:
    #     undo_commands.remove(skip)

    rich.print("[red]Are you sure? (y/n)")
    choice = input(f"{_PROMPT}") if not _ARGS.yes else "y"
    if choice in ["y", "yes", "Y", "YES"]:
        try:
            execute_move_commands(undo_commands)

        except Exception as e:
            with shelve.open(str(_UNDO_FILE)) as db:
                del db[str(_CLI_PATH.absolute())]
            print(e)
            exit(1)
        with shelve.open(str(_UNDO_FILE)) as db:
            db[str(_CLI_PATH.absolute())] = undo_commands

            # pickle.dump(_COMMANDS, _UNDO_FILE)


#  ^^^^^^^^^^^^^^^^^^^^^^^^^^
#  </ def undo()>
#  ^^^^^^^^^^^^^^^^^^^^^^^^^^


def preview_mvs(renames: dict[Path, Path]):
    """Print a list of mv targets."""
    for source, dest in renames.items():
        rich.print(f"mv [green]{source.name} [red]{dest.absolute()}")


def execute_move_commands(commands: dict[Path, Path]):
    """Execute a sequence of file move commands.

    Args:
        commands: A dictionary with source keys and destination values.
    """
    sources = list(commands.keys())
    for source in sources:
        try:
            os.makedirs(commands[source].absolute(), exist_ok=True)
            shutil.move(source.absolute(), commands[source].absolute())

        # File of Same Name Has Already Been Moved To Folder
        except shutil.Error as e:
            print(e)

    with shelve.open(str(_UNDO_FILE)) as db:
        db[str(_CLI_PATH.absolute())] = commands


def create_config():
    """Create a config file in users app data directory that overrides base settings."""

    os.makedirs(_USER_CONFIG_FILE.parent, exist_ok=True)
    shutil.copyfile(_BASE_CONFIG_FILE, _USER_CONFIG_FILE)
    print(f"User config file created at:\n{_USER_CONFIG_FILE}")


def gather_files(
    target: str | Path = Path("."),
    extensions: list[str] | None = None,
    recurse: bool = False,
    recursion_limit: int | None = None,
    exclusions: list[str] | None = None,
) -> list[Path]:
    """Return a list of files in target directory, optionally filtered by file extension(s) and exclusions."""
    glob_query: str = ""

    match (recurse, recursion_limit):
        case (True, None):
            glob_query = "**/." if recurse else "*."
        case (True, x) if x > 0:
            glob_query = "*/" * x + "*."
        case _:
            glob_query = "*."

    if extensions:
        glob_query += "".join({f"[{extension}]" for extension in extensions})
    else:
        glob_query += "*"

    all_files = Path(target).glob(glob_query)

    if all_files and exclusions:
        all_files = [Path(file) for file in all_files if file.name not in exclusions]

    if all_files:
        return list(all_files)

    return []


def clean_files(
    target: Path = Path("."),
    recurse: bool = False,
    yes_all: bool = False,
    extension_handler: dict[str, str] | None = None,
    exclusions: list[Path] | None = None,
) -> None:
    """Clean the files in target root directory using an extension handler that associates extensions to folders."""

    if recurse:
        root_files = target.rglob("*.*")
    else:
        root_files = target.glob("*.*")

    root_files = [file for file in root_files if file.name not in exclusions]

    target_mvs: dict[Path, Path] = associate_files(
        root_files, extension_handler=extension_handler, yes_all=True
    )

    if yes_all:
        approved_mvs = target_mvs
    else:
        approved_mvs = approve_dict(
            target_mvs,
            f"Targeting '{target.absolute()}' for clean up.\n{_PROMPT_STYLE}Select files to archive:",
        )

    if approved_mvs:
        preview_mvs(approved_mvs)
        execute_move_commands(approved_mvs)


def identify_large_files(target: Path = Path("."), yes_all: bool = False) -> None:
    """Find large files in target directory and offer to centralize them."""

    all_files = gather_files(target=target, recurse=True, recursion_limit=3)
    file_sizes = [os.stat(file.absolute()).st_size for file in all_files]
    avg_file_size = sum(file_sizes) / len(file_sizes)
    standard_deviation = statistics.stdev(file_sizes)

    if yes_all:
        choice = "y"
    else:
        rich.print(
            f"Archived files average:\n\n{int(avg_file_size/1_000_000):_} Mbs +/- {int(standard_deviation/1_000_000):_} Mbs\n\n{_PROMPT_STYLE}Isolate large files (default: >150 Mbs)? Y/N? (Enter an integer to specify large file treshold.)",
        )
        choice = input(f"{_PROMPT}")

    large: int = 0

    match choice:
        case ("y" | "Y" | "yes"):
            large = 150_000_000
        case ("n" | "N" | "no"):
            large = 150_000_000_000_000_000
        case x if re.match(r"\d+mbs?", x, re.IGNORECASE):
            large = int(re.match(r"([\d_]+) ?mbs?", x, re.IGNORECASE).group(1))
            large = large * 1_000_000
        case x if re.match(r"\d+kbs?", x, re.IGNORECASE):
            large = int(re.match(r"([\d_]+) ?kbs?", x, re.IGNORECASE).group(1))
            large = large * 1000
        case x if re.match(r"\d+$", x):
            large = int(x) * 1_000_000
        case _:
            large = 150_000_000_000_000_000

    large_files = [
        file for file in all_files if os.stat(file.absolute()).st_size > large
    ]

    if large_files:
        large_mvs = associate_files(
            large_files, default_folder=Path("large_files"), yes_all=_ARGS.yes
        )
        if not yes_all:
            preview_mvs(large_mvs)
            rich.print(
                f"{len(large_mvs)} large files found.\n[black on red]Execute? Y/N\n{_PROMPT}",
                end="",
            )
            choice = input()
            if choice not in ["y", "Y", "yes", "YES"]:
                return

        execute_move_commands(large_mvs)


def identify_crowded_archives(
    target: Path = Path("."), threshold: int = 20, yes_all: bool = False
) -> None:
    """Identify crowded folders and offer to uncrowd them."""

    archive_folders = [Path(f"{key}") for key in _FILE_TYPES.keys()]
    all_folders = []
    for folder in archive_folders:
        all_folders.extend(list(folder.glob(f"{folder} [0-9][0-9][0-9][0-9]/")))

    crowded_folders = isolate_crowded_folders(all_folders, crowded_threshold=5)

    uncrowded_mvs = {}

    if not crowded_folders:
        return

    if yes_all:
        approved_folders = crowded_folders
    else:
        approved_folders = approve_list(
            crowded_folders, f"Choose folders to uncrowd (>{threshold} files):"
        )
    for folder in approved_folders:
        if yes_all:
            approved_mvs = uncrowd_folder(folder, yes_all=True)
        else:
            suggested_mvs = uncrowd_folder(folder)
            approved_mvs = approve_dict(
                suggested_mvs, f"Are you sure you approve all these file movements?"
            )

        uncrowded_mvs.update(approved_mvs)
    if not yes_all:
        preview_mvs(uncrowded_mvs)
        execute_move_commands(uncrowded_mvs)


def main():
    # rich.traceback.install()

    # if not os.path.isdir(_CLI_PATH):
    if not _CLI_PATH.exists():
        rich.print(f"[red on black]The specified path ({_CLI_PATH}) does not exist.")
        exit(1)

    # else:
    #     root = Path(_CLI_PATH)

    if _ARGS.undo:
        undo()
        clean_up()
        exit(0)

    if _ARGS.config:
        create_config()
        exit(0)

    clean_files(
        target=_CLI_PATH,
        recurse=_ARGS.recurse,
        yes_all=_ARGS.yes,
        extension_handler=_EXTENSION_HANDLER,
        exclusions=_EXCLUSIONS,
    )

    identify_large_files(target=_CLI_PATH, yes_all=_ARGS.yes)

    identify_crowded_archives(
        target=_CLI_PATH, threshold=_SETTINGS["CROWDED_FOLDER"], yes_all=_ARGS.yes
    )

    breakpoint()
    return

    # all_files = gather_files(_CLI_PATH, exclusions=_EXCLUSIONS)

    # for file_name in all_files:
    #     if file_name in _EXCLUSIONS:
    #         all_files.remove(file_name)

    file_groups: dict[str, list[Path]] = {}

    # put all files with same extension group into one list
    # and put that list in the file_groups dictionary
    # FOR EXAMPLE
    # file_groups["media"] will contain a list of all pictures in CWD
    # file_groups["zip files"] contain a list of all compressed archives in CWD
    # etc

    for file_type, extension_list in _FILE_TYPES.items():
        if not extension_list:
            continue

        # extension_pattern = re.compile(
        #     "(" + "|".join(extension_list) + ")$", re.IGNORECASE
        # )
        file_groups[file_type] = [
            file_name
            for file_name in all_files
            # if re.search(extension_pattern, str(file_name))
            if file_name.suffix in extension_list
        ]

        for file in file_groups[file_type]:
            all_files.remove(file)

    # Any file-types not explicitly handled are moved to the miscellaneous folder
    if HANDLE_MISC and all_files:
        try:
            file_groups["misc"].extend(all_files)
        except KeyError:
            file_groups["misc"] = all_files
        # print(f"moved {all_files}")

    # Do not target THIS file
    if __file__ in file_groups["programming"]:
        file_groups["programming"].remove(__file__)

    # Do not target THIS file
    if _THIS_FILE in file_groups["programming"]:
        file_groups["programming"].remove(_THIS_FILE)

    file_count = sum([len(file_group) for _, file_group in file_groups.items()])

    print(f"({file_count}) files/folders to move.\n")

    # Handles all files in file_groups
    for file_type, file_group in file_groups.items():
        if not file_group:
            continue

        modified_info = [
            (
                file,
                datetime.datetime.fromtimestamp(os.path.getmtime(file)).year,
                datetime.datetime.fromtimestamp(os.path.getmtime(file)).month,
            )
            for file in file_group
        ]

        organized_info: dict[int, list[tuple[str, int]]] = {}
        for file, year, month in modified_info:
            existing = organized_info.get((year))
            if not existing:
                organized_info[year] = [(file, month)]
            else:
                existing.append((file, month))

        for year in organized_info.keys():
            old_files = glob.glob(str(Path(f"{file_type}/{file_type} {year}")) + "/*")
            new_files = [elem[0] for elem in organized_info[year]]
            if len(old_files) + len(new_files) > _CROWDED_FOLDER:
                handle_files(new_files, file_type, month=True)
            else:
                handle_files(new_files, file_type)

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
        choice = input(f"{_PROMPT}") if not _ARGS.yes else "n"

        if choice in ["y", "yes"]:
            move_folders = True

    if move_folders:
        for extra_folder in extra_folders:
            rich.print(f"[yellow]{Path(extra_folder).resolve()}\nMove (y/n)?")
            choice = input(f"{_PROMPT}") if not _ARGS.yes else "y"

            if choice in ["y", "yes"]:
                rich.print("[yellow]Archive Folders:")
                for i, default_folder in enumerate(ARCHIVE_FOLDERS):
                    rich.print(f"[green] {i+1}.) {default_folder}")

                rich.print(
                    f"[yellow]mv '{extra_folder}' ???\nDestination (enter number)?"
                )
                target_folder = input(f"{_PROMPT}")
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
    choice = input(f"{_PROMPT}") if not _ARGS.yes else "y"
    if choice in ["y", "yes", "Y", "YES"]:
        execute_move_commands()
        with shelve.open(str(_UNDO_FILE)) as db:
            db[_CLI_PATH] = _COMMANDS
            # pickle.dump(_COMMANDS, fp)

    clean_up()
    return


#  ^^^^^^^^^^^^^^^^^^^^^^^^^^
#  </ def main()>
#  ^^^^^^^^^^^^^^^^^^^^^^^^^^

if __name__ == "__main__":
    main()
