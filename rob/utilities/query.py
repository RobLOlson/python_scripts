from typing import Any

import readchar
import rich

_SAVE_CURSOR = "\033[s"
_RESTORE_CURSOR = "\033[u"
_CLEAR_LINE = "\033[2K"
_MOVE_UP = "\033[1A"
_MOVE_DOWN = "\033[1B"
_MOVE_LEFT = "\033[1D"
_CLEAR_RIGHT = "\033[K"


def approve_list(
    target: list[Any], preamble: str = "", repr_func=None, maximum: int | None = None
) -> list[Any]:
    """Allows the user to interactively select a subset of items from a list.

    Displays the list in the terminal and lets the user toggle item selection
    using keyboard input.  For lists with fewer than 10 items, users toggle selection
    by typing the corresponding item number.  For lists with 10 or more items, users
    navigate the list with arrow keys or vim-style keys (h,j,k,l) and toggle selection with left/right arrow keys.

    Args:
        target: The list of items to choose from.
        preamble: An optional introductory message to display above the list.
        repr_func: An optional function to customize how list items are displayed.
                   It should take a list item as input and return a string.
        maximum: An optional limit on the number of items that can be selected.

    Returns:
        A list containing the selected items from the original `target` list.
        Returns an empty list if `target` is empty.

    Raises:
       TypeError: If target is not a list.
    """

    if not target:
        return []

    approved_targets = []

    if len(target) < 10:
        rich.print(
            f"\n[green]Toggle approval by pressing the index number. Press Enter to continue."
        )
        rich.print(preamble)

        print("\n" * (len(target) + 1))
        while True:
            print((_MOVE_UP + _CLEAR_LINE) * (len(target) + 1))
            for index, item in enumerate(target):
                if repr_func:
                    display = repr_func(item)
                else:
                    display = str(item)

                style = "[green]" if approved_targets.count(index+1) else "[red]"

                print(f'[{'x' if approved_targets.count(index+1) else ' '}]', end="")
                rich.print(rf" {style}{index+1}.) {display}")

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

                case '\r':
                    break

        return [elem for i, elem in enumerate(target) if approved_targets.count(i+1)]
    else:
        cursor_index = 0
        rich.print(
            f"\n[green]Move cursor with up/down. Add/remove approval with left/right. Press Enter to continue."
        )
        rich.print(preamble)

        print("\n" * (len(target) + 1))
        while True:
            print((_MOVE_UP + _CLEAR_LINE) * (len(target) + 1))
            for index, item in enumerate(target):
                if repr_func:
                    display = repr_func(item)
                else:
                    display = item

                style = "[green]" if approved_targets.count(index+1) else "[red]"
                if index == cursor_index:
                    style = "[yellow]"

                print(f'[{'x' if approved_targets.count(index+1) else ' '}]', end="")
                rich.print(rf" {style}{index+1:02}.) {display}")

            choice = readchar.readkey()
            match choice:
                case "d"|"l"|">"|readchar.key.RIGHT:
                    i = cursor_index+1

                    if i not in approved_targets:
                        approved_targets.append(i)

                    if maximum and len(approved_targets) > maximum:
                        trash = approved_targets.pop(0)

                case "a"|"h"|"<"|readchar.key.LEFT:
                    i = cursor_index+1
                    try:
                        approved_targets.remove(i)

                    except ValueError:
                        pass

                case "s"|"j"|readchar.key.DOWN:
                    cursor_index += 1
                    cursor_index = cursor_index % len(target)

                case "w"|"k"|readchar.key.UP:
                    cursor_index -= 1
                    cursor_index = cursor_index % len(target)


                case '\r':
                    break

        return [elem for i, elem in enumerate(target) if approved_targets.count(i+1)]



def approve_dict(
    target: dict[Any, Any], preamble: str = "", repr_func=None, maximum: int | None = None
) -> dict[Any, Any]:

    if not target:
        return {}

    approved_targets = []

    if len(target) < 10:
        rich.print(
            f"\n[green]Toggle approval by pressing the index number. Press Enter to continue."
        )
        rich.print(preamble)

        print("\n" * (len(target) + 1))
        while True:
            print((_MOVE_UP + _CLEAR_LINE) * (len(target) + 1))
            for index, item in enumerate(target):
                if repr_func:
                    display = repr_func(item)
                else:
                    display = f"{item} -> {target[item]}"

                style = "[green]" if approved_targets.count(index+1) else "[red]"

                print(f'[{'x' if approved_targets.count(index+1) else ' '}]', end="")
                rich.print(rf" {style}{index+1}.) {display}")

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

                case '\r':
                    break

        return {elem:target[elem] for i, elem in enumerate(target) if approved_targets.count(i+1)}
    else:
        cursor_index = 0
        rich.print(
            f"\n[green]Move cursor with up/down. Add/remove approval with left/right. Press Enter to continue."
        )
        rich.print(preamble)

        print("\n" * (len(target) + 1))
        while True:
            print((_MOVE_UP + _CLEAR_LINE) * (len(target) + 1))
            for index, item in enumerate(target):
                if repr_func:
                    display = repr_func(item)
                else:
                    display = f"{item} -> {target[item]}"

                style = "[green]" if approved_targets.count(index+1) else "[red]"
                if index == cursor_index:
                    style = "[yellow]"

                print(f'[{'x' if approved_targets.count(index+1) else ' '}]', end="")
                rich.print(rf" {style}{index+1:02}.) {display}")

            choice = readchar.readkey()
            match choice:
                case "d"|"l"|">"|readchar.key.RIGHT:
                    i = cursor_index+1

                    if i not in approved_targets:
                        approved_targets.append(i)

                    if maximum and len(approved_targets) > maximum:
                        trash = approved_targets.pop(0)

                case "a"|"h"|"<"|readchar.key.LEFT:
                    i = cursor_index+1
                    try:
                        approved_targets.remove(i)

                    except ValueError:
                        pass

                case "s"|"j"|readchar.key.DOWN:
                    cursor_index += 1
                    cursor_index = cursor_index % len(target)

                case "w"|"k"|readchar.key.UP:
                    cursor_index -= 1
                    cursor_index = cursor_index % len(target)


                case '\r':
                    break

        return {elem:target[elem] for i, elem in enumerate(target) if approved_targets.count(i+1)}


def linearize_complex_object(object, depth:int = 0) -> tuple[list, type, int]:
    simple = 0
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
    target, preamble: str = "", repr_func=None, maximum: int | None = None
) -> None:

    if not target:
        return []

    target = linearize_complex_object(target)

    cursor_index = 0
    rich.print(
        f"\n[green]Move cursor with up/down. Press right or tab to edit. Press Enter to confirm and commit."
    )
    rich.print(preamble)

    print("\n" * (len(target) + 1))
    while True:
        print((_MOVE_UP + _CLEAR_LINE) * (len(target) + 1))
        for index, item in enumerate(target):
            if repr_func:
                display = repr_func(item)
            else:
                display = "  "*int(item[1]+1) + f"{item[0]}"

            style = "[white]"
            if index == cursor_index:
                if item[2]:
                    style = "[green]"
                else:
                    style = "[red]"
            # print(f'[{'x' if approved_targets.count(index+1) else ' '}]', end="")
            rich.print(rf"{style}{display}")

        choice = readchar.readkey()
        match choice:
            case "\t"|"d"|"l"|">"|readchar.key.RIGHT:
                if not target[cursor_index][2]:
                    continue

                modified_text = ""
                print((_MOVE_UP + _CLEAR_LINE) * (len(target) + 1))
                for index, item in enumerate(target):
                    if repr_func:
                        display = repr_func(item)
                    else:
                        display = "  "*int(item[1]+1) + f"{item[0]}"

                    style = "[white]"
                    if index == cursor_index:
                        style = "[green]"
                        # print(_SAVE_CURSOR + _MOVE_UP + _CLEAR_LINE)
                        display = "  "*int(item[1]+1)
                        modified_text = f"{item[0]}"

                    rich.print(rf"{style}{display}")

                # Move cursor to target line
                print(_MOVE_UP*(len(target)-cursor_index), end="")

                modified_text = str(target[cursor_index][0])

                # Clear target line and rewrite
                # print(_CLEAR_RIGHT+ "  "*int(target[cursor_index][1]+1)+modified_text, end="")

                # Move cursor to start of target data
                print(_MOVE_LEFT*len(modified_text), end="")

                replace = input("  "*int(target[cursor_index][1]+1))

                if replace:
                    target[cursor_index] = (replace, target[cursor_index][1], target[cursor_index][2])

                print(_MOVE_DOWN*(len(target)-cursor_index))

            case "s"|"j"|readchar.key.DOWN:
                cursor_index += 1
                cursor_index = cursor_index % len(target)

            case "w"|"k"|readchar.key.UP:
                cursor_index -= 1
                cursor_index = cursor_index % len(target)


            case '\r':
                break

    return reconstitute_object(target)

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
        if not line[2] and line[1] == current_depth:
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

    return reconstitute_object(composite)

print_linearized_object(linearize_complex_object({'a': [1, 2, {'x':'y', 'z':'w'}]}))
print_linearized_object(linearize_complex_object([{'settings_1':True, 'settings_2':False}]))
# print(edit_object([reconstitute_object, 'uno', 'dos', {'aba': [1, 2, {'xeno':'y', 'z':'w'}, reconstitute_object]}]))
print(approve_list(edit_object([False, 'dos', {1:'one', 2:'two'}, ['quatro', 'cinco', [1,2,3.5]]])))
# print(edit_object({'a': {1:2}}))
