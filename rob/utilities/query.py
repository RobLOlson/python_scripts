import shutil
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
    target: list[Any], repr_func=None, maximum: int | None = None, preamble: bool | None = None , default_yes:bool=False
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

    if maximum != None and maximum < 1:
        return []

    if not target:
        return []

    if preamble == None:
        if maximum == 1:
            preamble = False
        else:
            preamble = True

    if default_yes:
        if maximum:
            approved_targets = [(i) % len(target) + 1 for i in range(len(target)) if i < maximum]
        else:
            approved_targets = list(range(1, len(target)+1))
    else:
        approved_targets = []

    cursor_index = 0

    long_contents = max([len(str(elem))+8 for elem in target]) > shutil.get_terminal_size().columns

    if preamble:
        rich.print(
        f"""\n[green]Toggle approval with number keys.
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

            style = "[green]" if approved_targets.count(index+1) else "[red]"
            if maximum and maximum == 1:
                style = "[white]"
            if index == cursor_index:
                style = "[yellow]"


            if not maximum or maximum > 1:
                print(f'[{'x' if approved_targets.count(index+1) else ' '}]', end="")
                prefix = f"{index+1:02}.) "
            else:
                if index == cursor_index:
                    prefix = " >"
                else:
                    prefix = "  "

            rich.print(rf"{style}{prefix}{display}")

        choice = readchar.readkey()
        match choice:
            case "1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9":
                i = int(choice)
                if i > len(target):
                    continue

                if i in approved_targets:
                    approved_targets.remove(i)
                else:
                    approved_targets.append(i)

                if maximum and len(approved_targets) > maximum:
                    approved_targets.pop(0)

            case "d"|"l"|">"|readchar.key.RIGHT:
                i = cursor_index+1

                if i not in approved_targets:
                    approved_targets.append(i)
                else:
                    approved_targets = []
                    if maximum:
                        approved_targets = [(i+cursor_index) % len(target) + 1 for i in range(len(target)) if i < maximum]
                    else:
                        approved_targets = list(range(1, len(target)+1))
                    # for i, elem in enumerate(target):
                    #     approved_targets.append(i+1)

                while maximum and len(approved_targets) > maximum:
                    approved_targets.pop(0)

            case "a"|"h"|"<"|readchar.key.LEFT:
                i = cursor_index+1
                try:
                    approved_targets.remove(i)

                except ValueError:
                    approved_targets = []

            case "s"|"j"|readchar.key.DOWN:
                cursor_index += 1
                cursor_index = cursor_index % len(target)

            case "w"|"k"|readchar.key.UP:
                cursor_index -= 1
                cursor_index = cursor_index % len(target)

            case '\r':
                print("")
                if maximum and maximum == 1:
                    approved_targets = [cursor_index + 1]

                print("")
                break

            case '\x1b':
                rich.print("[red]Terminated.", end="")
                exit(1)

    return [elem for i, elem in enumerate(target) if approved_targets.count(i+1)]

def select(target: list[Any], preamble: bool=False, repr_func = None):
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
    if maximum != None and maximum < 1:
        return {}

    if not target:
        return {}

    approved_targets = []

    cursor_index = 0
    rich.print(
        f"""\n[green]Toggle approval with number keys.
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
            style = "[green]" if approved_targets.count(index+1) else "[red]"
            if index == cursor_index:
                style = "[yellow]"

            if repr_func:
                display = repr_func(item, target[item])
            else:
                display = f"{item} [white] -> {style}{target[item]}"

            print(f'[{'x' if approved_targets.count(index+1) else ' '}]', end="")
            rich.print(rf" {style}{index+1:02}.) {display}")

        choice = readchar.readkey()
        match choice:
            case "1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9":
                i = int(choice)
                if i > len(target):
                    continue

                if i in approved_targets:
                    approved_targets.remove(i)
                else:
                    approved_targets.append(i)

                if maximum and len(approved_targets) > maximum:
                    trash = approved_targets.pop(0)

            case "d"|"l"|">"|readchar.key.RIGHT:
                i = cursor_index+1

                if i not in approved_targets:
                    approved_targets.append(i)
                else:
                    if maximum:
                        approved_targets = [(i+cursor_index) % len(target) + 1 for i in range(len(target)) if i < maximum]
                    else:
                        approved_targets = list(range(1, len(target)+1))

                if maximum and len(approved_targets) > maximum:
                    approved_targets.pop(0)
                    # if len(approved_targets) == maximum:
                    #     approved_targets.pop()
                    #     approved_targets.append(i)


            case "a"|"h"|"<"|readchar.key.LEFT:
                i = cursor_index+1
                try:
                    approved_targets.remove(i)

                except ValueError:
                    approved_targets = []

            case "s"|"j"|readchar.key.DOWN:
                cursor_index += 1
                cursor_index = cursor_index % len(target)

            case "w"|"k"|readchar.key.UP:
                cursor_index -= 1
                cursor_index = cursor_index % len(target)

            case '\r':
                print("")
                break

            case '\x1b':
                rich.print("[red]Terminated.", end="")
                exit(1)

            case '\x03':
                rich.print("[red]Terminated.", end="")
                exit(1)


    return {elem:target[elem] for i, elem in enumerate(target) if approved_targets.count(i+1)}


def linearize_complex_object(object:list|dict, depth:int = 0) -> tuple[Any, int, type]:
    linearized = []
    if type(object) == dict:
        keys=object.keys()
        linearized.append(('{', depth-1, None))
        for key in keys:
            if type(object[key]) in [dict, list, set]:
                linearized.append((key, depth, type(key)))
                linearized.append((':', depth, None))
                nested_object = linearize_complex_object(object[key], depth+1)
                linearized.extend(nested_object)
            else:
                linearized.append((key, depth, type(key)))
                linearized.append((':', depth, None))
                linearized.append((object[key], depth, type(object[key])))
        linearized.append(('}', depth-1, None))


    elif type(object) in [list, set]:
        linearized.append(('[', depth-1, None))
        for elem in object:
            if type(elem) in [dict, list, set]:
                nested_object = linearize_complex_object(elem, depth+1)
                linearized.extend(nested_object)
            else:
                linearized.append((elem, depth, type(elem)))
        linearized.append((']', depth-1, None))

    return linearized

def print_linearized_object(linearized_object):
    for line in linearized_object:
        print('  '*(line[1]+1) + str(line[0]) + (f" ({line[2]})" if line[2] else ""))

def edit_object(
    target: list[Any]|dict[Any, Any], preamble: str = "", repr_func=None, show_brackets: bool = True, edit_keys:bool = True, dict_inline:bool=False
):

    target2 = linearize_complex_object(target)

    cursor_index = 0

    while True:
        cursor_index = (cursor_index + 1) % len(target2)
        if not target2[cursor_index][2]: # [2] is element's type ("brackets" have no type)
            continue
        if not edit_keys and target2[(cursor_index + 1) % len(target2)][0] == ":": #[0] is contents
            continue
        break

    rich.print(
        f"\n[green]Move cursor with up/down. Press right or tab to edit. Press Enter to confirm and commit."
    )
    rich.print(preamble)

    long_contents = max(len(str(elem)) for elem in target2) > shutil.get_terminal_size().columns
    end = ""

    print("\n" * (len(target2) + 1))
    while True:
        if long_contents or not edit_keys:
            print("\033[2J")
        else:
            print((_MOVE_UP + _CLEAR_LINE) * (len(target2)+1))
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
                if item[0]==':' and str(target2[(index+1) % len(target2)][0]) not in '{}[]':
                    indent = ""
                    end = " "

                # index AFTER ':'
                elif str(target2[(index-1) % len(target2)][0]) in ':':
                    indent = ""
                    end = "\n"

                # index BEFORE ':'
                elif target2[(index+1) % len(target2)][0] == ':' or str(target2[(index-1) % len(target2)][0]) == '{':
                    indent = "  "*int(item[1]+1)
                    # indent = ""
                    end = ""
                else:
                    indent = "  "*int(item[1]+1)
                    end = "\n"
            else:
                indent = "  "*int(item[1]+1)
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

        choice = readchar.readkey()
        match choice:
            case "\t"|"d"|"l"|">"|readchar.key.RIGHT:
                if not target2[cursor_index][2]:
                    continue

                modified_text = ""
                if long_contents or not edit_keys:
                    print("\033[2J")
                else:
                    print((_MOVE_UP + _CLEAR_LINE) * (len(target2)+1))
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
                        if item[0]==':' and str(target2[(index+1) % len(target2)][0]) not in '{}[]':
                            indent = ""
                            end = " "

                        # index AFTER ':'
                        elif str(target2[(index-1) % len(target2)][0]) in ':':
                            indent = ""
                            end = "\n"

                        # index BEFORE ':'
                        elif target2[(index+1) % len(target2)][0] == ':' or str(target2[(index-1) % len(target2)][0]) == '{':
                            indent = "  "*int(item[1]+1)
                            # indent = ""
                            end = ""
                        else:
                            indent = "  "*int(item[1]+1)
                            end = "\n"
                    else:
                        indent = "  "*int(item[1]+1)
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
                display_height=display_string.count("\n")
                # Move cursor to target2 line
                print(_MOVE_UP*(abs(edit_line - display_height)), end="")

                modified_text = str(target2[cursor_index][0])

                # Clear target2 line and rewrite
                # print(_CLEAR_RIGHT+ "  "*int(target2[cursor_index][1]+1)+modified_text, end="")

                # Move cursor to start of target2 data
                print(_MOVE_LEFT*len(modified_text), end="")

                if dict_inline:
                    rich.print(f"{edit_prefix}", end="")
                    replace = input()

                else:
                    replace = input("  "*int(target2[cursor_index][1]+1))

                if replace:
                    target2[cursor_index] = (replace, target2[cursor_index][1], target2[cursor_index][2])

                print(_MOVE_DOWN*(len(target2)-cursor_index))

            case "s"|"j"|readchar.key.DOWN:
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

            case "w"|"k"|readchar.key.UP:
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

            case '\r':
                print("")
                break

            case '\x1b':
                rich.print("[red]Terminated.", end="")
                exit(1)

    return reconstitute_object(target2)

def reconstitute_object(linearized_object):
    """Inverse operation of linearize_object function.  Returns original nested list/dict."""

    current_depth = -1
    highest_indeces = []

    for index, line in enumerate(linearized_object):
        # ignore digested lines (undigested lines should still be tuples)
        if type(line) != tuple:
            continue
        if not line[2] and line[0] in ['[', ']', '{', '}'] and line[1] > current_depth:
            highest_indeces = []
            current_depth = line[1]
        if not line[2] and line[0] != ':' and line[1] == current_depth:
            highest_indeces.append(index)

    if not highest_indeces:
        return linearized_object[0]

    if linearized_object[highest_indeces[-2]][0] == '[':
        pre_list = linearized_object[:highest_indeces[-2]]
        sub_list = []
        for elem in linearized_object[highest_indeces[-2]:highest_indeces[-1]]:
            if type(elem) == tuple:
                if type(elem[0]) == elem[2]:
                    sub_list.append(elem[0])
                elif elem[2] == int:
                    try:
                        sub_list.append(int(elem[0]))
                    except ValueError:
                        sub_list.append(float(elem[0]))
                elif elem[2] == float:
                    sub_list.append(float(elem[0]))
                elif elem[2] == bool:
                    sub_list.append(bool(elem[0]))
            else:
                sub_list.append(elem)
        post_list = linearized_object[highest_indeces[-1]+1:]

        pre_list.append(sub_list)
        pre_list.extend(post_list)
        composite = pre_list

    elif linearized_object[highest_indeces[-2]][0] == '{':
        pre_list = linearized_object[:highest_indeces[-2]]
        sub_dict = {}
        for i in range(highest_indeces[-2]+1, highest_indeces[-1]-1, 3):
            next_key = linearized_object[i]
            next_val = linearized_object[i+2]

            if type(next_key[0]) == next_key[2]:
                next_key = next_key[0]
            elif next_key[2] == int:
                try:
                    next_key = int(next_key[0])
                except ValueError:
                    next_key = float(next_key[0])
            elif next_key[2] == float:
                next_key = float(next_key[0])
            elif next_key[2] == bool:
                next_key = bool(next_key[0])

            if type(next_val) != tuple:
                pass
            elif type(next_val[0]) == next_val[2]:
                next_val = next_val[0]
            elif next_val[2] == int:
                next_val = int(next_val[0])
            elif next_val[2] == float:
                next_val = float(next_val[0])
            elif next_val[2] == bool:
                nextval = bool(next_val[0])

            sub_dict.update({next_key: next_val})

        post_list = linearized_object[highest_indeces[-1]+1:]

        pre_list.append(sub_dict)
        pre_list.extend(post_list)
        composite = pre_list
    else:
        # breakpoint()
        raise Exception("Expected '[' or '{'.")

    return reconstitute_object(composite)

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

def form_from_dict(target:dict[str, str|int|float|bool]):
    return edit_object(target=target, show_brackets=False, edit_keys=False, dict_inline=True)

# print(approve_list([1,2,3,4,5,6,7,8,9,10]))
# print(approve_dict({'settings_1':True, 'settings_2':False, 'settings_3':False, 'settings_4':False, 'settings_5':False}))
# print_linearized_object(linearize_complex_object({'a': [1, 2, {'x':'y', 'z':'w'}]}))
# print_linearized_object(linearize_complex_object([{'settings_1':True, 'settings_2':False}]))
# print(edit_object([reconstitute_object, 'uno', 'dos', {'aba': [1, 2, {'xeno':'y', 'z':'w'}, reconstitute_object]}], show_brackets=False, edit_keys=False, dict_inline=True))
# print(form_from_dict({'a': {1:2, 2:4, 3:6}, 'b':{'option_1': True, 'option_2': False}}))

# print(approve_list(edit_object([False, 'dos', {1:'one', 2:'two', 3:[3.0, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9]}, ['quatro', 'cinco', [1,2,3.5]]])))
