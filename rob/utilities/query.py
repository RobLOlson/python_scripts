import shutil
from textwrap import wrap
from typing import Any

import readchar
import rich

# _SAVE_CURSOR = "\033[s"
# _RESTORE_CURSOR = "\033[u"
_CLEAR_LINE = "\033[2K"
_MOVE_UP = "\033[1A"
_MOVE_DOWN = "\033[1B"
_MOVE_LEFT = "\033[1D"
_CLEAR_RIGHT = "\033[K"


def approve_list(
    target: list[Any],
    repr_func=None,
    maximum: int | None = None,
    preamble: bool | None = None,
    default_yes: bool = False,
) -> list[Any]:
    """Interactively approves items from a list using keyboard input.

    Displays the list in the terminal and allows the user to toggle approval
    for each item.  Navigation and selection are done via keyboard controls.

    Args:
        target: The list of items to be reviewed.
        preamble: Optional introductory text to display above the list.
        repr_func: Optional function to customize the display of each item.
            If provided, this function will be called with each item as input and
            its return value will be displayed.
        maximum: The maximum number of items that can be approved.  If None,
            there is no limit.

    Returns:
        A new list containing only the approved items from the original list.
    """

    if maximum is not None and maximum < 1:
        return []

    if not target:
        return []

    if preamble is None:
        if maximum == 1:
            preamble = False
        else:
            preamble = True

    if default_yes:
        if maximum:
            approved_targets = [(i) % len(target) + 1 for i in range(len(target)) if i < maximum]
        else:
            approved_targets = list(range(1, len(target) + 1))
    else:
        approved_targets = []

    cursor_index = 0

    long_contents = max([len(str(elem)) + 8 for elem in target]) > shutil.get_terminal_size().columns

    if preamble:
        rich.print(
            """\n[green]Toggle approval with number keys.
Move cursor with up/down.
Add/remove approval with left/right.
Press Enter to continue."""
        )

    print("\n" * (len(target)))
    while True:
        if long_contents:
            print("\033[2J")
        else:
            print((_MOVE_UP + _CLEAR_LINE) * (len(target) + 1))
        for index, item in enumerate(target):
            if repr_func:
                display = repr_func(item)
            else:
                display = item

            style = "[green]" if approved_targets.count(index + 1) else "[red]"
            if maximum and maximum == 1:
                style = "[white]"
            if index == cursor_index:
                style = "[yellow]"

            if not maximum or maximum > 1:
                print(f"[{'x' if approved_targets.count(index + 1) else ' '}]", end="")
                prefix = f"{index + 1:02}.) "
            else:
                if index == cursor_index:
                    prefix = " >"
                else:
                    prefix = "  "

            rich.print(rf"{style}{prefix}{display}")

        try:
            choice = readchar.readkey()
        except KeyboardInterrupt:
            print("")
            rich.print("[red]Interrupted by user (Ctrl+C).", end="")
            exit(1)

        match choice:
            case "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9":
                i = int(choice)
                if i > len(target):
                    continue

                if i in approved_targets:
                    approved_targets.remove(i)
                else:
                    approved_targets.append(i)

                if maximum and len(approved_targets) > maximum:
                    approved_targets.pop(0)

            case "d" | "l" | ">" | readchar.key.RIGHT:
                i = cursor_index + 1

                if i not in approved_targets:
                    approved_targets.append(i)
                else:
                    approved_targets = []
                    if maximum:
                        approved_targets = [
                            (i + cursor_index) % len(target) + 1 for i in range(len(target)) if i < maximum
                        ]
                    else:
                        approved_targets = list(range(1, len(target) + 1))
                    # for i, elem in enumerate(target):
                    #     approved_targets.append(i+1)

                while maximum and len(approved_targets) > maximum:
                    approved_targets.pop(0)

            case "a" | "h" | "<" | readchar.key.LEFT:
                i = cursor_index + 1
                try:
                    approved_targets.remove(i)

                except ValueError:
                    approved_targets = []

            case "s" | "j" | readchar.key.DOWN:
                cursor_index += 1
                cursor_index = cursor_index % len(target)

            case "w" | "k" | readchar.key.UP:
                cursor_index -= 1
                cursor_index = cursor_index % len(target)

            case "q" | "\r":
                print("")
                if maximum and maximum == 1:
                    approved_targets = [cursor_index + 1]

                print("")
                break
            case "\x1b":  # ESC
                rich.print("[red]Terminated.", end="")
                exit(1)

    return [elem for i, elem in enumerate(target) if approved_targets.count(i + 1)]


def select(target: list[Any], preamble: bool = False, repr_func=None):
    """Select and return a user-approved element from target list."""

    return approve_list(target, preamble=preamble, repr_func=repr_func, maximum=1)[0]


def approve_dict(
    target: dict[Any, Any], preamble: str = "", repr_func=None, maximum: int | None = None
) -> dict[Any, Any]:
    """Interactively approves entries in a dictionary.

    Displays the dictionary's key-value pairs (or a custom representation)
    and allows the user to select which entries to keep

    Args:
        target: The dictionary to filter.
        preamble: An optional string to display above the dictionary entries.
        repr_func: An optional function to customize the display of each item.
                   It should accept a dictionary key as input and return a string.
        maximum: The maximum number of entries that can be approved. If None,
                 there is no limit.

    Returns:
        A new dictionary containing only the approved entries.  Returns an empty
        dictionary if the input dictionary is empty.
    """
    if maximum is not None and maximum < 1:
        return {}

    if not target:
        return {}

    approved_targets = []

    cursor_index = 0
    rich.print(
        """\n[green]Toggle approval with number keys.
Move cursor with up/down.
Add/remove approval with left/right.
Press Enter to continue."""
    )
    if preamble:
        rich.print("\n" + preamble)

    print("\n" * (len(target)))
    while True:
        print((_MOVE_UP + _CLEAR_LINE) * (len(target) + 1))
        for index, item in enumerate(target):
            style = "[green]" if approved_targets.count(index + 1) else "[red]"
            if index == cursor_index:
                style = "[yellow]"

            if repr_func:
                display = repr_func(item, target[item])
            else:
                display = f"{item} [white] -> {style}{target[item]}"

            print(f"[{'x' if approved_targets.count(index + 1) else ' '}]", end="")
            rich.print(rf" {style}{index + 1:02}.) {display}")

        try:
            choice = readchar.readkey()
        except KeyboardInterrupt:
            print("")
            rich.print("[red]Interrupted by user (Ctrl+C).", end="")
            exit(1)

        match choice:
            case "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9":
                i = int(choice)
                if i > len(target):
                    continue

                if i in approved_targets:
                    approved_targets.remove(i)
                else:
                    approved_targets.append(i)

                if maximum and len(approved_targets) > maximum:
                    approved_targets.pop(0)

            case "d" | "l" | ">" | readchar.key.RIGHT:
                i = cursor_index + 1

                if i not in approved_targets:
                    approved_targets.append(i)
                else:
                    if maximum:
                        approved_targets = [
                            (i + cursor_index) % len(target) + 1 for i in range(len(target)) if i < maximum
                        ]
                    else:
                        approved_targets = list(range(1, len(target) + 1))

                if maximum and len(approved_targets) > maximum:
                    approved_targets.pop(0)
                    # if len(approved_targets) == maximum:
                    #     approved_targets.pop()
                    #     approved_targets.append(i)

            case "a" | "h" | "<" | readchar.key.LEFT:
                i = cursor_index + 1
                try:
                    approved_targets.remove(i)

                except ValueError:
                    approved_targets = []

            case "s" | "j" | readchar.key.DOWN:
                cursor_index += 1
                cursor_index = cursor_index % len(target)

            case "w" | "k" | readchar.key.UP:
                cursor_index -= 1
                cursor_index = cursor_index % len(target)

            case "q" | "\r":
                print("")
                break

            case "\x1b":
                rich.print("[red]Terminated.", end="")
                exit(1)

            case "\x03":
                rich.print("[red]Terminated.", end="")
                exit(1)

    return {elem: target[elem] for i, elem in enumerate(target) if approved_targets.count(i + 1)}


def linearize_complex_object(object: list | dict, depth: int = 0) -> tuple[Any, int, type]:
    linearized = []
    if type(object) == dict:  # noqa: E721
        keys = object.keys()
        linearized.append(("{", depth - 1, None))
        for key in keys:
            if type(object[key]) in [dict, list, set]:
                linearized.append((key, depth, type(key)))
                linearized.append((":", depth, None))
                nested_object = linearize_complex_object(object[key], depth + 1)
                linearized.extend(nested_object)
            else:
                linearized.append((key, depth, type(key)))
                linearized.append((":", depth, None))
                linearized.append((object[key], depth, type(object[key])))
        linearized.append(("}", depth - 1, None))

    elif type(object) in [list, set]:
        linearized.append(("[", depth - 1, None))
        for elem in object:
            if type(elem) in [dict, list, set]:
                nested_object = linearize_complex_object(elem, depth + 1)
                linearized.extend(nested_object)
            else:
                linearized.append((elem, depth, type(elem)))
        linearized.append(("]", depth - 1, None))

    return linearized


def print_linearized_object(linearized_object):
    for line in linearized_object:
        print("  " * (line[1] + 1) + str(line[0]) + (f" ({line[2]})" if line[2] else ""))


def edit_object(
    target: list[Any] | dict[Any, Any],
    preamble: str = "",
    repr_func=None,
    show_brackets: bool = True,
    edit_keys: bool = True,
    dict_inline: bool = False,
) -> list[Any] | dict[Any, Any]:
    target2 = linearize_complex_object(target)

    cursor_index = 0

    while True:
        cursor_index = (cursor_index + 1) % len(target2)
        if not target2[cursor_index][2]:  # [2] is element's type ("brackets" have no type)
            continue
        if not edit_keys and target2[(cursor_index + 1) % len(target2)][0] == ":":  # [0] is contents
            continue
        break

    # rich.print(
    #     "\n[green]Move cursor with up/down. Press right or tab to edit. Press Enter to confirm and commit."
    # )
    # rich.print(preamble)

    long_contents = max(len(str(elem)) for elem in target2) > shutil.get_terminal_size().columns
    end = ""

    if not long_contents:
        print("\n" * len(target2) * 2, end="\n\n\n\n")
        print((_CLEAR_LINE + _MOVE_UP) * len(target2))
    # print("\n" * (len(target2) + 1))
    while True:
        if long_contents or not edit_keys:
            print("\033[2J")  # clear screen
        else:
            print((_MOVE_UP + _CLEAR_LINE) * (len(target2) + 5))

        print(preamble)
        display_string = ""
        for index, item in enumerate(target2):
            if not show_brackets and not item[2] and str(item[0]) in "]}[{":
                continue
            if repr_func:
                display = repr_func(item)
            else:
                display = f"{item[0]}"

            if dict_inline:
                # index ON ':'
                if item[0] == ":" and str(target2[(index + 1) % len(target2)][0]) not in "{}[]":
                    indent = ""
                    end = " "

                # index AFTER ':'
                elif str(target2[(index - 1) % len(target2)][0]) in ":":
                    indent = ""
                    end = "\n"

                # index BEFORE ':'
                elif (
                    target2[(index + 1) % len(target2)][0] == ":"
                    or str(target2[(index - 1) % len(target2)][0]) == "{"
                ):
                    indent = "  " * int(item[1] + 1)
                    # indent = ""
                    end = ""
                else:
                    indent = "  " * int(item[1] + 1)
                    end = "\n"
            else:
                indent = "  " * int(item[1] + 1)
                end = "\n"

            style = "[white]"
            if index == cursor_index:
                if item[2]:
                    style = "[green]"
                else:
                    style = "[red]"

            display_string += rf"{style}{indent}{display}{end}"
            # rich.print(rf"{style}{indent}{display}{end}", end="")

        rich.print(display_string, end="")
        rich.print("\n[green]Press Enter, right, or tab to edit.\nCtrl+Enter or 'q' to save and quit.")
        try:
            choice = readchar.readkey()
        except KeyboardInterrupt:
            print("")
            rich.print("[red]Interrupted by user (Ctrl+C).", end="")
            exit(1)

        match choice:
            case "\t" | "d" | "l" | ">" | readchar.key.RIGHT | "\r":
                if not target2[cursor_index][2]:
                    continue

                modified_text = ""
                if long_contents or not edit_keys:
                    print("\033[2J")
                else:
                    print((_MOVE_UP + _CLEAR_LINE) * (len(target2) + 5))
                display_string = ""
                print(preamble)
                for index, item in enumerate(target2):
                    if not show_brackets and not item[2] and str(item[0]) in "]}[{":
                        continue
                    if repr_func:
                        display = repr_func(item)
                    else:
                        display = f"{item[0]}"

                    if dict_inline:
                        # index ON ':'
                        if item[0] == ":" and str(target2[(index + 1) % len(target2)][0]) not in "{}[]":
                            indent = ""
                            end = " "

                        # index AFTER ':'
                        elif str(target2[(index - 1) % len(target2)][0]) in ":":
                            indent = ""
                            end = "\n"

                        # index BEFORE ':'
                        elif (
                            target2[(index + 1) % len(target2)][0] == ":"
                            or str(target2[(index - 1) % len(target2)][0]) == "{"
                        ):
                            indent = "  " * int(item[1] + 1)
                            # indent = ""
                            end = ""
                        else:
                            indent = "  " * int(item[1] + 1)
                            end = "\n"
                    else:
                        indent = "  " * int(item[1] + 1)
                        end = "\n"

                    style = "[white]"
                    if index == cursor_index:
                        edit_prefix = display_string.split("\n")[-1]
                        edit_line = display_string.count("\n")
                        if item[2]:
                            style = "[green]"
                        else:
                            style = "[red]"

                    display_string += rf"{style}{indent}{display}{end}"
                    # rich.print(rf"{style}{indent}{display}{end}", end="")

                rich.print(display_string, end="")
                rich.print("\n[green]Press enter right or tab to edit.\nCtrl+Enter to save and quit.")

                display_height = display_string.count("\n")
                # Move cursor to target2 line
                # 3 lines for the preamble
                # plus 1 line for each line of the display_string
                print(_MOVE_UP * 3 + _MOVE_UP * (abs(edit_line - display_height)), end="")

                modified_text = "[yellow]" + str(target2[cursor_index][0])

                # Clear target2 line and rewrite
                # print(_CLEAR_RIGHT+ "  "*int(target2[cursor_index][1]+1)+modified_text, end="")

                # Move cursor to start of target2 data
                print(_MOVE_LEFT * len(modified_text), end="")
                print(modified_text, end="")
                print(_MOVE_LEFT * len(modified_text), end="")
                print(_CLEAR_RIGHT, end="")

                if dict_inline:
                    rich.print(f"[yellow]{edit_prefix}", end="")
                    replace = input()

                else:
                    replace = input("  " * int(target2[cursor_index][1] + 1))

                if replace:
                    target2[cursor_index] = (replace, target2[cursor_index][1], target2[cursor_index][2])

                # This line moves the cursor down to its original position after editing, so the display remains consistent.
                print(_MOVE_DOWN * (len(target2) - cursor_index + 1))

            case "s" | "j" | readchar.key.DOWN:
                while True:
                    cursor_index = (cursor_index + 1) % len(target2)
                    if not target2[cursor_index][2]:
                        continue
                    if not edit_keys and target2[(cursor_index + 1) % len(target2)][0] == ":":
                        continue
                    break
                # while not target2[cursor_index][2] and True if edit_keys else target2[(cursor_index + 2) % len(target2)][0] != ':':
                #     cursor_index = (cursor_index + 1) % len(target2)

                # cursor_index = cursor_index % len(target2)

            case "w" | "k" | readchar.key.UP:
                while True:
                    cursor_index = (cursor_index - 1) % len(target2)
                    if not target2[cursor_index][2]:
                        continue
                    if not edit_keys and target2[(cursor_index + 1) % len(target2)][0] == ":":
                        continue
                    break

                # cursor_index = (cursor_index - 1) % len(target2)
                # while not target2[cursor_index][2]:
                #     cursor_index = (cursor_index - 1) % len(target2)

                # cursor_index = cursor_index % len(target2)

            case "q" | readchar.key.CTRL_J | "\r":
                print("")
                break

            case "\x1b":
                rich.print("[red]Terminated.", end="")
                exit(1)

    return reconstitute_object(target2)


def reconstitute_object(linearized_object):
    """Inverse operation of linearize_object function.  Returns original nested list/dict."""

    current_depth = -1
    highest_indeces = []

    for index, line in enumerate(linearized_object):
        # ignore digested lines (undigested lines should still be tuples)
        if type(line) != tuple:  # noqa: E721
            continue
        if not line[2] and line[0] in ["[", "]", "{", "}"] and line[1] > current_depth:
            highest_indeces = []
            current_depth = line[1]
        if not line[2] and line[0] != ":" and line[1] == current_depth:
            highest_indeces.append(index)

    if not highest_indeces:
        return linearized_object[0]

    if linearized_object[highest_indeces[-2]][0] == "[":
        pre_list = linearized_object[: highest_indeces[-2]]
        sub_list = []
        for elem in linearized_object[highest_indeces[-2] : highest_indeces[-1]]:
            if type(elem) == tuple:  # noqa: E721
                if type(elem[0]) == elem[2]:  # noqa: E721
                    sub_list.append(elem[0])
                elif elem[2] == int:  # noqa: E721
                    try:
                        sub_list.append(int(elem[0]))
                    except ValueError:
                        sub_list.append(float(elem[0]))
                elif elem[2] == float:  # noqa: E721
                    sub_list.append(float(elem[0]))
                elif elem[2] == bool:  # noqa: E721
                    sub_list.append(bool(elem[0]))
            else:
                sub_list.append(elem)
        post_list = linearized_object[highest_indeces[-1] + 1 :]

        pre_list.append(sub_list)
        pre_list.extend(post_list)
        composite = pre_list

    elif linearized_object[highest_indeces[-2]][0] == "{":
        pre_list = linearized_object[: highest_indeces[-2]]
        sub_dict = {}
        for i in range(highest_indeces[-2] + 1, highest_indeces[-1] - 1, 3):
            next_key = linearized_object[i]
            next_val = linearized_object[i + 2]

            if type(next_key[0]) == next_key[2]:  # noqa: E721
                next_key = next_key[0]
            elif next_key[2] == int:  # noqa: E721
                try:
                    next_key = int(next_key[0])
                except ValueError:
                    next_key = float(next_key[0])
            elif next_key[2] == float:  # noqa: E721
                next_key = float(next_key[0])
            elif next_key[2] == bool:  # noqa: E721
                next_key = bool(next_key[0])

            if type(next_val) != tuple:  # noqa: E721
                pass
            elif type(next_val[0]) == next_val[2]:  # noqa: E721
                next_val = next_val[0]
            elif next_val[2] == int:  # noqa: E721
                next_val = int(next_val[0])
            elif next_val[2] == float:  # noqa: E721
                next_val = float(next_val[0])
            elif next_val[2] == bool:  # noqa: E721
                if next_val[0].lower() == "true":
                    next_val = True
                elif next_val[0].lower() == "false":
                    next_val = False
                else:
                    next_val = bool(next_val[0])

            sub_dict.update({next_key: next_val})

        post_list = linearized_object[highest_indeces[-1] + 1 :]

        pre_list.append(sub_dict)
        pre_list.extend(post_list)
        composite = pre_list
    else:
        raise Exception("Expected '[' or '{'.")

    return reconstitute_object(composite)


def integer(
    preamble: str = "",
    default: int | None = None,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    """Query for an integer value within a given range."""

    if minimum is not None and maximum is not None and minimum > maximum:
        raise ValueError("minimum must be less than maximum")

    if default is None:
        if minimum is not None:
            target = minimum
        else:
            target = 0
    else:
        target = default

    input_number = ""
    print("\n" * (4 + len(preamble.split("\n"))), end="")
    while True:
        term_width = shutil.get_terminal_size().columns
        preamble_lines = wrap(preamble, term_width)
        if minimum is None and maximum is None:
            instruct1 = wrap("Enter integer or use up/down keys to adjust.", term_width)
        else:
            instruct1 = wrap(
                f"Enter integer or use up/down keys to adjust. [{minimum if minimum is not None else '-inf'}, {maximum if maximum is not None else '+inf'}]",
                term_width,
            )
        instruct2 = wrap("Press Ctrl+Enter to confirm and commit.", term_width)
        print(_MOVE_UP * (1 + len(preamble_lines) + len(instruct1) + len(instruct2)) + _CLEAR_LINE, end="")
        rich.print("\n".join(preamble_lines), end="")
        if input_number:
            rich.print(f"[yellow]{input_number}[/yellow]")
        else:
            rich.print(f"[yellow]{target}[/yellow]")
        rich.print(f"\n[green]{'\n'.join(instruct1)}[/green]")
        rich.print(f"[green]{'\n'.join(instruct2)}[/green]")

        try:
            choice = readchar.readkey()
        except KeyboardInterrupt:
            print("")
            rich.print("[red]Interrupted by user (Ctrl+C).", end="")
            exit(1)

        match choice:
            case "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9":
                input_number += choice
            case "\r":
                continue
            case "k" | readchar.key.UP:
                target = target + 1
                if maximum is not None and target > maximum:
                    if minimum is not None:
                        target = minimum
                    else:
                        target = maximum
                    # target = max(target + 1, maximum)
                input_number = ""
            case "j" | readchar.key.DOWN:
                target = target - 1
                if minimum is not None and target < minimum:
                    if maximum is not None:
                        target = maximum
                    else:
                        target = minimum
                input_number = ""

            case readchar.key.CTRL_J | "\r":
                break
            case "\x08":
                if input_number:
                    input_number = input_number[:-1]
                else:
                    input_number = ""
            case "\x1b":
                rich.print("[red]Terminated.", end="")
                exit(1)
    if input_number:
        target = int(input_number)
        if maximum is not None and target > maximum:
            target = maximum
        elif minimum is not None and target < minimum:
            target = minimum

    return int(target)


def confirm(default: bool = False):
    if default:
        prop = ["Yes", "No"]
    else:
        prop = ["No", "Yes"]

    choice = select(prop)
    if choice == "Yes":
        return True
    else:
        return False


def form_from_dict(target: dict[str, str | int | float | bool], preamble: str = ""):
    return edit_object(
        target=target, show_brackets=False, edit_keys=False, dict_inline=True, preamble=preamble
    )


# print(approve_list([1,2,3,4,5,6,7,8,9,10]))
# print(approve_dict({'settings_1':True, 'settings_2':False, 'settings_3':False, 'settings_4':False, 'settings_5':False}))
# print_linearized_object(linearize_complex_object({'a': [1, 2, {'x':'y', 'z':'w'}]}))
# print_linearized_object(linearize_complex_object([{'settings_1':True, 'settings_2':False}]))
# print(edit_object([reconstitute_object, 'uno', 'dos', {'aba': [1, 2, {'xeno':'y', 'z':'w'}, reconstitute_object]}], show_brackets=False, edit_keys=False, dict_inline=True))
# print(form_from_dict({'a': {1:2, 2:4, 3:6}, 'b':{'option_1': True, 'option_2': False}}))

# print(approve_list(edit_object([False, 'dos', {1:'one', 2:'two', 3:[3.0, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9]}, ['quatro', 'cinco', [1,2,3.5]]])))
