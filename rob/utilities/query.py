import datetime
import shutil
from textwrap import wrap
from typing import Any, Callable

import readchar
import rich

# _SAVE_CURSOR = "\033[s"
# _RESTORE_CURSOR = "\033[u"
_CLEAR_LINE = "\033[2K"
_MOVE_UP = "\033[1A"
_MOVE_DOWN = "\033[1B"
_MOVE_LEFT = "\033[1D"
_MOVE_RIGHT = "\033[1C"
_CLEAR_RIGHT = "\033[K"
_CLEAR_LEFT = "\033[1K"
_CLEAR_SCREEN = "\033[2J"
_SAVE_CURSOR = "\033[s"
_RESTORE_CURSOR = "\033[u"


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

    # Pagination setup based on terminal height
    term_height = shutil.get_terminal_size().lines - 2
    pages: list[list[Any]] = []
    if len(target) > term_height:
        buffer: list[Any] = []
        for index, item in enumerate(target):
            if index % term_height == 0 and index != 0:
                pages.append(buffer)
                buffer = []
            buffer.append(item)
        pages.append(buffer)
    else:
        pages = [target]

    if repr_func:
        long_contents = (
            max([len(repr_func(elem)) + 8 for elem in target]) > shutil.get_terminal_size().columns
        )
    else:
        long_contents = max([len(str(elem)) + 8 for elem in target]) > shutil.get_terminal_size().columns

    if preamble:
        rich.print(
            """\n[green]  Toggle approval with number keys.
  Move cursor with up/down.
  Add/remove approval with left/right.
  Press Enter to continue."""
        )

    print("\n" * (len(pages[0])))
    current_page = 0
    display_index = 0
    while True:
        term_width = shutil.get_terminal_size().columns
        if long_contents:
            print(_CLEAR_SCREEN)
        else:
            print((_MOVE_UP + _CLEAR_LINE) * (len(pages[current_page]) + 1))
        for index, item in enumerate(pages[current_page]):
            if repr_func:
                display = repr_func(item)
            else:
                display = item

            style = "[green]" if approved_targets.count(index + 1 + display_index) else "[red]"
            if maximum and maximum == 1:
                style = "[white]"
            if index == cursor_index:
                style = "[yellow]"

            if not maximum or maximum > 1:
                print(f"[{'x' if approved_targets.count(index + 1 + display_index) else ' '}]", end="")
                prefix = f"{display_index + index + 1:02}.) "
            else:
                if index == cursor_index:
                    prefix = " >"
                else:
                    prefix = "  "

            display_line = rf"{style}{prefix}{display}".replace("\n", " // ")
            rich.print(f"{display_line:<{term_width}}")

        if len(pages) > 1:
            rich.print(f"[green]Page {current_page + 1} of {len(pages)}[/green]", end="")

        try:
            choice = readchar.readkey()
        except KeyboardInterrupt:
            print("")
            rich.print("[red]Interrupted by user (Ctrl+C).", end="")
            exit(1)

        match choice:
            case "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9":
                i = int(choice)
                if i > len(pages[current_page]):
                    continue

                if i + display_index in approved_targets:
                    approved_targets.remove(i + display_index)
                else:
                    approved_targets.append(i + display_index)

                if maximum and len(approved_targets) > maximum:
                    approved_targets.pop(0)

            case "d" | "l" | ">" | readchar.key.RIGHT:
                i = cursor_index + 1

                if i + display_index not in approved_targets:
                    approved_targets.append(i + display_index)
                else:
                    approved_targets = []
                    if maximum:
                        approved_targets = [
                            (i + cursor_index + display_index) % len(pages[current_page]) + display_index + 1
                            for i in range(len(pages[current_page]))
                            if i < maximum
                        ]
                    else:
                        approved_targets = list(
                            range(display_index + 1, display_index + len(pages[current_page]) + 1)
                        )
                    # for i, elem in enumerate(target):
                    #     approved_targets.append(i+1)

                while maximum and len(approved_targets) > maximum:
                    approved_targets.pop(0)

            case "a" | "h" | "<" | readchar.key.LEFT:
                i = cursor_index + 1
                try:
                    approved_targets.remove(i + display_index)

                except ValueError:
                    approved_targets = []

            case "s" | "j" | readchar.key.DOWN:
                cursor_index += 1
                cursor_index = cursor_index % len(pages[current_page])

            case "w" | "k" | readchar.key.UP:
                cursor_index -= 1
                cursor_index = cursor_index % len(pages[current_page])

            case "q" | "\r":
                print("")
                if maximum and maximum == 1:
                    approved_targets = [cursor_index + 1 + display_index]
                    print("")
                    break
                print("")
                if current_page < len(pages) - 1:
                    display_index += len(pages[current_page])
                    current_page += 1
                    print(_CLEAR_SCREEN)
                else:
                    current_page = 0
                    break
            case "\x1b":  # ESC
                if current_page > 0:
                    current_page -= 1
                    display_index -= len(pages[current_page])
                    print(_CLEAR_SCREEN)
                # rich.print("[red]Terminated.", end="")
                # exit(1)

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

    term_height = shutil.get_terminal_size().lines - 2
    pages = []
    if len(target) > term_height:
        buffer = {}
        for index, item in enumerate(target.items()):
            if index % term_height == 0 and index != 0:
                pages.append(buffer)
                buffer = {}
            buffer[item[0]] = item[1]
        pages.append(buffer)
    else:
        pages = [target]

    cursor_index = 0
    rich.print(
        """\n[green]Toggle approval with number keys.
Move cursor with up/down.
Add/remove approval with left/right.
Press Enter to continue."""
    )
    if preamble:
        rich.print("\n" + preamble)

    print("\n" * (len(pages[0])))
    current_page = 0
    display_index = 0
    while True:
        term_width = shutil.get_terminal_size().columns
        print((_MOVE_UP + _CLEAR_LINE) * (len(pages[current_page]) + 1))
        for index, item in enumerate(pages[current_page]):
            style = "[green]" if approved_targets.count(index + 1 + display_index) else "[red]"
            if index == cursor_index:
                style = "[yellow]"

            if repr_func:
                display = repr_func(item, target[item])
            else:
                display = f"{item} [white] -> [/white] {style}{target[item]}"

            print(f"[{'x' if approved_targets.count(index + 1 + display_index) else ' '}]", end="")
            display_line = rf" {style}{display_index + index + 1:02}.) {display}".replace("\n", " // ")
            if len(display_line) - len(style) > term_width:
                display_line = rf" {style}{display_index + index + 1:02}.) {item}[white] -> [/white] {style}...{str(target[item])[len(item.name) + 10 : -len(item.name)]}"
            if len(display_line) - len(style) - 12 > term_width:
                rich.print(f"{display_line[: term_width - 3]}...")
            else:
                rich.print(f"{display_line}")
        if len(pages) > 1:
            rich.print(f"[green]Page {current_page + 1} of {len(pages)}[/green]", end="")
        try:
            choice = readchar.readkey()
        except KeyboardInterrupt:
            print("")
            rich.print("[red]Interrupted by user (Ctrl+C).", end="")
            exit(1)

        match choice:
            case "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9":
                i = int(choice)
                if i > len(pages[current_page]):
                    continue

                if i in approved_targets:
                    approved_targets.remove(i)
                else:
                    approved_targets.append(i)

                if maximum and len(approved_targets) > maximum:
                    approved_targets.pop(0)

            case "d" | "l" | ">" | readchar.key.RIGHT:
                i = cursor_index + 1

                if i + display_index not in approved_targets:
                    approved_targets.append(i + display_index)
                else:
                    if maximum:
                        approved_targets = [
                            (i + cursor_index + display_index) % len(pages[current_page]) + display_index + 1
                            for i in range(len(pages[current_page]))
                            if i < maximum
                        ]
                    else:
                        approved_targets = list(
                            range(display_index + 1, display_index + len(pages[current_page]) + 1)
                        )

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
                cursor_index = cursor_index % len(pages[current_page])

            case "w" | "k" | readchar.key.UP:
                cursor_index -= 1
                cursor_index = cursor_index % len(pages[current_page])

            case "q" | "\r":
                print("")
                if current_page < len(pages) - 1:
                    display_index += len(pages[current_page])
                    current_page += 1
                    print(_CLEAR_SCREEN)
                else:
                    current_page = 0
                    break

            # ESC
            case "\x1b":
                if current_page > 0:
                    current_page -= 1
                    display_index -= len(pages[current_page])
                    print(_CLEAR_SCREEN)
                # rich.print("[red]Terminated.", end="")
                # exit(1)

            # Ctrl+C
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


def _build_display_lines(
    target2,
    cursor_index: int = 0,
    show_brackets: bool = False,
    edit_keys: bool = True,
    repr_func: Callable | None = None,
    preamble: str = "",
) -> list[tuple[str, int]]:
    """Builds a list of display lines and returns a list of tuples containing the line, the index corresponding to the line in the original target, and the length of the indent."""
    display_lines = []
    if preamble:
        display_lines.extend(preamble.split("\n"))

    for index, item in enumerate(target2):
        # skip brackets if not showing them
        indent = "  " * int(item[1] + 1)

        if str(target2[index - 1][0]) == ":" and target2[index - 1][2] is None:
            if not edit_keys:
                indent += f"{target2[index - 2][0]}: "
                del display_lines[-1]
            else:
                display_lines[-2] = (
                    display_lines[-2][0] + ": ",
                    display_lines[-2][1],
                    display_lines[-2][2],
                )
                del display_lines[-1]

        if not show_brackets and item[2] is None and str(item[0]) in "]}[{":
            continue

        if not edit_keys and str(item[0]) in ":" and item[2] is None:
            continue

        if repr_func:
            display = repr_func(item)
        else:
            display = f"{item[0]}"

        style = "[white]"
        if index == cursor_index:
            no_indent = indent.lstrip()
            indent_length = len(indent) - len(no_indent)
            indent = "-" * (indent_length - 1) + ">" + no_indent
            # indent = indent[:-1] + ">"
            # indent = indent.replace(" ", "-")
            if item[2]:
                style = "[green]"
            else:
                style = "[red]"

        display_lines.append((rf"[white]{indent}{style}{display}", index, indent))

    display_lines.append(("", -1, ""))
    display_lines.append(("[green]Press ? for editing controls.[/green]", -1, ""))
    return display_lines


def edit_object(
    target: list[Any] | dict[Any, Any],
    preamble: str = "",
    repr_func: Callable | None = None,
    show_brackets: bool = True,
    edit_keys: bool = True,
) -> list[Any] | dict[Any, Any]:
    """Interactive inline editor for nested lists/dicts."""

    # complex list/dict converted to a list of tuples
    # each tuple contains the element, the depth, and the type
    # type None means the element is a bracket
    original_target = target.copy()

    target2 = linearize_complex_object(target)

    cursor_index = -1
    display_index = -1

    # initialize index to first editable item
    while True:
        cursor_index = (cursor_index + 1) % len(target2)
        display_index += 1
        if not target2[cursor_index][2]:  # [2] is element's type ("brackets" have no type)
            if not show_brackets:
                display_index -= 1
            continue
        if not edit_keys and target2[(cursor_index + 1) % len(target2)][0] == ":":  # [0] is contents
            if not show_brackets:
                display_index -= 1
            continue
        break

    display_lines = _build_display_lines(target2, cursor_index, show_brackets, edit_keys, repr_func, preamble)
    for line in display_lines:
        if line[1] == cursor_index:
            display_index = display_lines.index(line)
            break

    print("\n" * (len(display_lines)))

    while True:
        print((_MOVE_UP + _CLEAR_LINE) * (len(display_lines)), end="")

        display_lines = _build_display_lines(
            target2, cursor_index, show_brackets, edit_keys, repr_func, preamble
        )
        for line in display_lines:
            if line[1] == cursor_index:
                display_index = display_lines.index(line)
                break

        rich.print("\n" + "\n".join(display_line[0] for display_line in display_lines), end="")
        try:
            choice = readchar.readkey()
        except KeyboardInterrupt:
            rich.print("[red]Interrupted by user (Ctrl+C).", end="")
            exit(1)

        match choice:
            case "\t" | "d" | "l" | ">" | readchar.key.RIGHT | "\r":
                if not target2[cursor_index][2]:
                    continue

                if target2[cursor_index][2] == datetime.datetime:
                    print(_SAVE_CURSOR, end="")
                    handle_datetime(
                        target2=target2,
                        cursor_index=cursor_index,
                        repr_func=repr_func,
                        preamble=preamble,
                        display_lines=display_lines,
                        display_index=display_index,
                    )
                    print(_RESTORE_CURSOR, end="")
                    continue
                elif target2[cursor_index][2] == int:  # noqa: E721
                    print(_SAVE_CURSOR, end="")
                    handle_integer(
                        target2,
                        cursor_index,
                        repr_func,
                        preamble,
                        display_lines,
                        display_index,
                    )
                    print(_RESTORE_CURSOR, end="")
                    # print(_MOVE_DOWN * (len(display_lines) + 1), end="")
                    continue
                elif target2[cursor_index][2] == float:  # noqa: E721
                    print(_SAVE_CURSOR, end="")
                    handle_float(
                        target2=target2,
                        cursor_index=cursor_index,
                        repr_func=repr_func,
                        preamble=preamble,
                        display_lines=display_lines,
                        display_index=display_index,
                    )
                    print(_RESTORE_CURSOR, end="")
                    continue
                elif target2[cursor_index][2] == bool:  # noqa: E721
                    print(_SAVE_CURSOR, end="")
                    handle_bool(
                        target2=target2,
                        cursor_index=cursor_index,
                        repr_func=repr_func,
                        preamble=preamble,
                        display_lines=display_lines,
                        display_index=display_index,
                    )
                    print(_RESTORE_CURSOR, end="")
                    continue
                else:
                    handle_string(
                        target2=target2,
                        cursor_index=cursor_index,
                        repr_func=repr_func,
                        preamble=preamble,
                        display_lines=display_lines,
                        display_index=display_index,
                    )

                # modified_text = ""
                # # print((_MOVE_UP + _CLEAR_LINE) * len(display_lines))

                # display_lines = _build_display_lines(
                #     target2=target2,
                #     cursor_index=cursor_index,
                #     show_brackets=show_brackets,
                #     preamble=preamble,
                #     repr_func=repr_func,
                # )
                # rich.print("\n".join(display_lines), end="")
                # print(_MOVE_UP * (len(display_lines) + 3), end="")

                # modified_text = "[yellow]" + str(target2[cursor_index][0])

                # # Move cursor to start of target2 data
                # print(_MOVE_LEFT * len(modified_text), end="")
                # print(modified_text, end="")
                # print(_MOVE_LEFT * len(modified_text), end="")
                # print(_CLEAR_RIGHT, end="")

                # replace = input("  " * int(target2[cursor_index][1] + 1))

                # if replace:
                #     target2[cursor_index] = (replace, target2[cursor_index][1], target2[cursor_index][2])

                # # This line moves the cursor down to its original position after editing, so the display remains consistent.
                # print(_MOVE_DOWN * (len(display_lines) - cursor_index + 1))

            case "s" | "j" | readchar.key.DOWN:
                while True:
                    cursor_index = (cursor_index + 1) % len(target2)
                    display_index = (display_index + 1) % len(display_lines)
                    if not target2[cursor_index][2]:
                        continue
                    if not edit_keys and target2[(cursor_index + 1) % len(target2)][0] == ":":
                        continue
                    break

            case "w" | "k" | readchar.key.UP:
                while True:
                    cursor_index = (cursor_index - 1) % len(target2)
                    display_index = (display_index - 1) % len(display_lines)
                    if not target2[cursor_index][2]:
                        continue
                    if not edit_keys and target2[(cursor_index + 1) % len(target2)][0] == ":":
                        continue
                    break

            case "q" | readchar.key.CTRL_J | "\r" | "\n":
                break

            case "\x1b":
                target = original_target
                rich.print("[red]Terminated.", end="")
                exit(0)

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
        if len(preamble) > term_width:
            preamble_lines = wrap(preamble, term_width)
        else:
            preamble_lines = [preamble]
        if minimum is None and maximum is None:
            instruct1 = wrap("  Enter integer or use up/down keys to adjust.", term_width)
        else:
            instruct1 = wrap(
                f"  Enter integer or use up/down keys to adjust. [{minimum if minimum is not None else '-inf'}, {maximum if maximum is not None else '+inf'}]",
                term_width,
            )
        instruct2 = wrap("  Press Ctrl+Enter to confirm and commit.", term_width)
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
            case "-":
                target = -target
            case "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" | readchar.key.BACKSPACE:
                if choice == readchar.key.BACKSPACE:
                    if len(str(target).replace("-", "")) > 1:
                        target = int(str(target)[:-1])
                    else:
                        target = 0
                else:
                    target = int(str(target) + choice)
            case "\r":
                continue
            case "k" | readchar.key.UP:
                target = target + 1
            case "j" | readchar.key.DOWN:
                target = target - 1
            case readchar.key.CTRL_J | "\r":
                break
        if target > maximum:
            target = maximum
        elif target < minimum:
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
    # return interdict.InterDict(target, show_brackets=False, editable_keys=False).edit()
    return edit_object(target=target, show_brackets=False, edit_keys=False, preamble=preamble)


def handle_string(
    target2: list[tuple[Any, int, type]],
    cursor_index: int,
    show_brackets: bool = True,
    repr_func: Callable | None = None,
    preamble: str = "",
    display_index: int = 0,
    display_lines: list[tuple[str, int]] = [],
) -> None:
    """Handle editing of string objects in place."""

    indent = display_lines[display_index][2]
    original_value = target2[cursor_index][0]

    while True:
        print(_MOVE_UP * (abs(display_index - len(display_lines) + 1)), end="")
        print(_CLEAR_LINE + _MOVE_LEFT * 200, end="")
        # print(_MOVE_LEFT * 200 + _MOVE_RIGHT * len(indent), end="")
        rich.print(f"{indent}[yellow]{target2[cursor_index][0]}[/yellow]", end="")
        try:
            choice = readchar.readkey()
        except KeyboardInterrupt:
            print("")
            rich.print("[red]Interrupted by user (Ctrl+C).", end="")
            exit(1)
        match choice:
            case "\r":
                print(_MOVE_DOWN * (abs(display_index - len(display_lines)) - 1), end="")
                return
            case "\x1b":
                target2[cursor_index] = (original_value, target2[cursor_index][1], target2[cursor_index][2])
                return
            case readchar.key.BACKSPACE:
                if target2[cursor_index][0] is None:
                    target2[cursor_index] = ("", target2[cursor_index][1], str)
                elif len(target2[cursor_index][0]) > 1:
                    target2[cursor_index] = (
                        target2[cursor_index][0][:-1],
                        target2[cursor_index][1],
                        target2[cursor_index][2],
                    )
                else:
                    target2[cursor_index] = ("", target2[cursor_index][1], str)
                print(_MOVE_UP, end="")
            case _:
                target2[cursor_index] = (
                    f"{target2[cursor_index][0]}{choice}",
                    target2[cursor_index][1],
                    target2[cursor_index][2],
                )
                print(_MOVE_UP, end="")
        print(_MOVE_DOWN * abs(display_index - len(display_lines)), end="")


def handle_datetime(
    target2: list[tuple[Any, int, type]],
    cursor_index: int,
    repr_func: Callable | None = None,
    preamble: str = "",
    display_lines: list[tuple[str, int]] = [],
    display_index: int = 0,
) -> None:
    """Handle editing of datetime objects in place."""

    interval = "day"
    indent = "  " * int(target2[cursor_index][1] + 1)
    indent = indent[:-1] + ">"
    indent = indent.replace(" ", "-")
    indent = display_lines[display_index][2]
    original_value = target2[cursor_index][0]

    # display_lines = _build_display_lines(target2, cursor_index, show_brackets, repr_func, preamble)

    # print(_MOVE_UP * (len(display_lines) - cursor_index + 3) + indent, end="")

    print(_MOVE_UP * (len(display_lines) - display_index))
    print(_MOVE_LEFT * 200 + _MOVE_RIGHT * len(display_lines[display_index][2]), end="")

    while True:
        date_str = str(target2[cursor_index][0].date())
        (year, month, day) = date_str.split("-")
        print(_MOVE_LEFT * (2 + len(date_str) + len(indent)), end="")
        if interval == "day":
            day = f"[yellow]{day}[/yellow]"
        elif interval == "month":
            month = f"[yellow]{month}[/yellow]"
        elif interval == "year":
            year = f"[yellow]{year}[/yellow]"
        rich.print(f"{indent}{year}-{month}-{day}", end="")
        try:
            choice = readchar.readkey()
        except KeyboardInterrupt:
            print("")
            rich.print("[red]Interrupted by user (Ctrl+C).", end="")
            exit(1)

        match choice:
            case "\r":
                break
            case "k" | readchar.key.UP:
                match interval:
                    case "day":
                        datetime.datetime
                        target2[cursor_index] = (
                            _adjust_datetime(target2[cursor_index][0], day=1),
                            target2[cursor_index][1],
                            target2[cursor_index][2],
                        )
                    case "month":
                        target2[cursor_index] = (
                            _adjust_datetime(target2[cursor_index][0], month=1),
                            target2[cursor_index][1],
                            target2[cursor_index][2],
                        )
                    case "year":
                        target2[cursor_index] = (
                            _adjust_datetime(target2[cursor_index][0], year=1),
                            target2[cursor_index][1],
                            target2[cursor_index][2],
                        )
            case "j" | readchar.key.DOWN:
                match interval:
                    case "day":
                        target2[cursor_index] = (
                            _adjust_datetime(target2[cursor_index][0], day=-1),
                            target2[cursor_index][1],
                            target2[cursor_index][2],
                        )
                    case "month":
                        target2[cursor_index] = (
                            _adjust_datetime(target2[cursor_index][0], month=-1),
                            target2[cursor_index][1],
                            target2[cursor_index][2],
                        )
                    case "year":
                        target2[cursor_index] = (
                            _adjust_datetime(target2[cursor_index][0], year=-1),
                            target2[cursor_index][1],
                            target2[cursor_index][2],
                        )
            case "h" | readchar.key.LEFT:
                if interval == "day":
                    interval = "month"
                elif interval == "month":
                    interval = "year"
            case "l" | readchar.key.RIGHT:
                if interval == "year":
                    interval = "month"
                elif interval == "month":
                    interval = "day"
            case "\x1b":
                target2[cursor_index] = (original_value, target2[cursor_index][1], target2[cursor_index][2])
                return

    print(_MOVE_UP * abs(display_index - len(display_lines) + 2), end="")


def handle_integer(
    target2: list[tuple[Any, int, type]],
    cursor_index: int,
    repr_func: Callable | None = None,
    preamble: str = "",
    display_lines: list[tuple[str, int]] = [],
    display_index: int = 0,
) -> None:
    """Handle editing of integer objects in place."""
    indent = display_lines[display_index][2]
    original_value = target2[cursor_index][0]

    # print(_MOVE_UP * (len(target2) - cursor_index + 3) + indent, end="")

    while True:
        print(_MOVE_UP * abs(display_index - len(display_lines) + 1), end="")
        print(_MOVE_LEFT * 200 + _CLEAR_LINE, end="")
        # print(_MOVE_UP * (len(display_lines) + display_index))
        # print(_MOVE_UP * (len(display_lines) - display_index))

        rich.print(f"{indent}[yellow]{target2[cursor_index][0]}[/yellow]", end="")

        # print(_MOVE_LEFT * (2 + len(str(target2[cursor_index][0])) + len(indent)), end="")
        # rich.print(
        #     f"{indent}[yellow]{target2[cursor_index][0]}[/yellow]",
        #     end="",
        # )
        # rich.print(f"{indent}{target2[cursor_index][0]:>{base_length}}", end="")
        try:
            choice = readchar.readkey()
        except KeyboardInterrupt:
            print("")
            rich.print("[red]Interrupted by user (Ctrl+C).", end="")
            exit(1)
        match choice:
            case "\r":
                print(_MOVE_UP * (abs(display_index - len(display_lines))), end="")
                break
            case readchar.key.BACKSPACE:
                if len(str(target2[cursor_index][0]).replace("-", "")) > 1:
                    target2[cursor_index] = (
                        int(f"{target2[cursor_index][0]}"[:-1]),
                        target2[cursor_index][1],
                        target2[cursor_index][2],
                    )
                    print(_MOVE_LEFT + _CLEAR_RIGHT, end="")
                else:
                    target2[cursor_index] = (0, target2[cursor_index][1], target2[cursor_index][2])

                    print(_MOVE_LEFT + _CLEAR_RIGHT, end="")
            case "-":
                target2[cursor_index] = (
                    -target2[cursor_index][0],
                    target2[cursor_index][1],
                    target2[cursor_index][2],
                )
                if target2[cursor_index][0] > 0:
                    print(_MOVE_LEFT + _CLEAR_RIGHT, end="")

            case "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" | readchar.key.BACKSPACE:
                target2[cursor_index] = (
                    int(f"{target2[cursor_index][0]}{choice}"),
                    target2[cursor_index][1],
                    target2[cursor_index][2],
                )
            case "k" | readchar.key.UP:
                target2[cursor_index] = (
                    target2[cursor_index][0] + 1,
                    target2[cursor_index][1],
                    target2[cursor_index][2],
                )
                if target2[cursor_index][0] == 0:
                    print(_MOVE_LEFT + _CLEAR_RIGHT, end="")
            case "j" | readchar.key.DOWN:
                target2[cursor_index] = (
                    target2[cursor_index][0] - 1,
                    target2[cursor_index][1],
                    target2[cursor_index][2],
                )
            case "\x1b":
                target2[cursor_index] = (original_value, target2[cursor_index][1], target2[cursor_index][2])
                return
        print(_MOVE_DOWN * (abs(display_index - len(display_lines)) - 1), end="")


def handle_float(
    target2: list[tuple[Any, int, type]],
    cursor_index: int,
    repr_func: Callable | None = None,
    preamble: str = "",
    display_lines: list[tuple[str, int]] = [],
    display_index: int = 0,
) -> None:
    """Handle editing of float objects in place."""
    indent = display_lines[display_index][2]
    original_value = target2[cursor_index][0]

    while True:
        print(_MOVE_UP * abs(display_index - len(display_lines) + 1), end="")
        print(_MOVE_LEFT * 200 + _CLEAR_LINE, end="")
        rich.print(f"{indent}[yellow]{target2[cursor_index][0]}[/yellow]", end="")

        try:
            choice = readchar.readkey()
        except KeyboardInterrupt:
            print("")
            rich.print("[red]Interrupted by user (Ctrl+C).", end="")
            exit(1)

        match choice:
            case "\r":
                target2[cursor_index] = (
                    float(target2[cursor_index][0]),
                    target2[cursor_index][1],
                    target2[cursor_index][2],
                )
                print(_MOVE_UP * (abs(display_index - len(display_lines))), end="")
                break
            case readchar.key.BACKSPACE:
                if len(str(target2[cursor_index][0]).replace("-", "")) > 0:
                    target2[cursor_index] = (
                        f"{target2[cursor_index][0]}"[:-1],
                        target2[cursor_index][1],
                        target2[cursor_index][2],
                    )
                    print(_MOVE_LEFT + _CLEAR_RIGHT, end="")
                else:
                    target2[cursor_index] = (0.0, target2[cursor_index][1], target2[cursor_index][2])

                    print(_MOVE_LEFT + _CLEAR_RIGHT, end="")
            case ".":
                if "." not in str(target2[cursor_index][0]):
                    target2[cursor_index] = (
                        f"{target2[cursor_index][0]}.",
                        target2[cursor_index][1],
                        target2[cursor_index][2],
                    )
                    print(_MOVE_LEFT + _CLEAR_RIGHT, end="")
                else:
                    print(_MOVE_DOWN * (abs(display_index - len(display_lines)) - 1), end="")
                    continue
                    # target2[cursor_index] = (0.0, target2[cursor_index][1], target2[cursor_index][2])

            case "-":
                target2[cursor_index] = (
                    -target2[cursor_index][0],
                    target2[cursor_index][1],
                    target2[cursor_index][2],
                )
                if target2[cursor_index][0] > 0:
                    print(_MOVE_LEFT + _CLEAR_RIGHT, end="")
            case "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" | readchar.key.BACKSPACE:
                target2[cursor_index] = (
                    f"{target2[cursor_index][0]}{choice}",
                    target2[cursor_index][1],
                    target2[cursor_index][2],
                )
            case "k" | readchar.key.UP:
                target2[cursor_index] = (
                    float(target2[cursor_index][0]) + 1.0,
                    target2[cursor_index][1],
                    target2[cursor_index][2],
                )
            case "j" | readchar.key.DOWN:
                target2[cursor_index] = (
                    float(target2[cursor_index][0]) - 1.0,
                    target2[cursor_index][1],
                    target2[cursor_index][2],
                )
            case "\x1b":
                target2[cursor_index] = (original_value, target2[cursor_index][1], target2[cursor_index][2])
                return
        print(_MOVE_DOWN * (abs(display_index - len(display_lines)) - 1), end="")


def handle_bool(
    target2: list[tuple[Any, int, type]],
    cursor_index: int,
    repr_func: Callable | None = None,
    preamble: str = "",
    display_lines: list[tuple[str, int]] = [],
    display_index: int = 0,
) -> None:
    """Handle editing of bool objects in place."""
    indent = display_lines[display_index][2]
    original_value = target2[cursor_index][0]

    while True:
        print(_MOVE_UP * abs(display_index - len(display_lines) + 1), end="")
        print(_MOVE_LEFT * 200 + _CLEAR_LINE, end="")
        rich.print(f"{indent}[yellow]{target2[cursor_index][0]}[/yellow]", end="")
        try:
            choice = readchar.readkey()
        except KeyboardInterrupt:
            print("")
            rich.print("[red]Interrupted by user (Ctrl+C).", end="")
            exit(1)
        match choice:
            case "\r":
                print(_MOVE_UP * (abs(display_index - len(display_lines))), end="")
                break
            case "k" | readchar.key.UP:
                target2[cursor_index] = (
                    not target2[cursor_index][0],
                    target2[cursor_index][1],
                    target2[cursor_index][2],
                )
            case "j" | readchar.key.DOWN:
                target2[cursor_index] = (
                    not target2[cursor_index][0],
                    target2[cursor_index][1],
                    target2[cursor_index][2],
                )
            case "\x1b":
                target2[cursor_index] = (original_value, target2[cursor_index][1], target2[cursor_index][2])
                return
        print(_MOVE_DOWN * (abs(display_index - len(display_lines)) - 1), end="")


def _adjust_datetime(target: datetime.datetime, day: int = 0, month: int = 0, year: int = 0):
    start_year = target.year
    start_month = target.month
    start_day = target.day
    target_year = start_year + year
    target_month = start_month + month
    if target_month > 12:
        target_month = 12
    if target_month < 1:
        target_month = 1
    target_day = start_day + day
    if target_day > 28:
        if target_month == 2:
            target_day = 28

    if target_day > 30:
        if target_month == 4 or target_month == 6 or target_month == 9 or target_month == 11:
            target_day = 30
        else:
            target_day = 31
    if target_day > 31:
        target_day = 31
    if target_day < 1:
        target_day = 1

    return datetime.datetime(
        target_year, target_month, target_day, target.hour, target.minute, target.second, target.microsecond
    )


# print(approve_list([1,2,3,4,5,6,7,8,9,10]))
# print(approve_dict({'settings_1':True, 'settings_2':False, 'settings_3':False, 'settings_4':False, 'settings_5':False}))
# print_linearized_object(linearize_complex_object({'a': [1, 2, {'x':'y', 'z':'w'}]}))
# print_linearized_object(linearize_complex_object([{'settings_1':True, 'settings_2':False}]))
# print(edit_object([reconstitute_object, 'uno', 'dos', {'aba': [1, 2, {'xeno':'y', 'z':'w'}, reconstitute_object]}], show_brackets=False, edit_keys=False, dict_inline=True))
# print(form_from_dict({'a': {1:2, 2:4, 3:6}, 'b':{'option_1': True, 'option_2': False}}))

# print(approve_list(edit_object([False, 'dos', {1:'one', 2:'two', 3:[3.0, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9]}, ['quatro', 'cinco', [1,2,3.5]]])))
