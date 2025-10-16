import copy
import datetime as _dt
import re
import shutil
import sys

# import textwrap
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Literal, Optional, Tuple

import rich
from readchar import key as k
from readchar import readkey

# -----------------------------
# Atom and KeyRef data classes
# -----------------------------

_CLEAR_LINE = "\x1b[K"
_CLEAR_SCREEN = "\x1b[2J"
_MOVE_UP_AND_CLEAR_SCREEN = "\x1b[A\x1b[K"


@dataclass
class KeyRef:
    key: Any


@dataclass
class Atom:
    value: Any
    py_type: type
    depth: int
    role: Literal["key", "value", "marker"]
    editable: bool
    path: Tuple[Any, ...]
    key_ref: Optional[KeyRef] = None
    marker: Optional[str] = None


# -----------------------------
# Editor Registry and Editors
# -----------------------------


class EditorResult:
    def __init__(self, status: Literal["continue", "commit", "cancel"], value: Any = None):
        self.status = status
        self.value = value


class BaseEditor:
    def start(self, value: Any) -> None:
        self._value = value

    def process_key(self, ch: str) -> EditorResult:
        return EditorResult("continue")

    def render_inline(self) -> str:
        return str(self._value)


class StringEditor(BaseEditor):
    def start(self, value: Any) -> None:
        self._buffer = str(value) if value is not None else ""

    def process_key(self, ch: str) -> EditorResult:
        if ch in (k.ENTER, "\r", "\n"):
            return EditorResult("commit", self._buffer)
        if ch in (k.ESC,):
            return EditorResult("cancel")
        if ch in (k.BACKSPACE, "\x7f"):
            if self._buffer:
                self._buffer = self._buffer[:-1]
            return EditorResult("continue")
        # Printable range
        if len(ch) == 1 and (" " <= ch <= "~"):
            self._buffer += ch
            return EditorResult("continue")
        return EditorResult("continue")

    def render_inline(self) -> str:
        return self._buffer


class IntEditor(BaseEditor):
    def start(self, value: Any) -> None:
        try:
            iv = int(value)
        except Exception:
            iv = 0
        self._negative = iv < 0
        self._digits = list(str(abs(iv)))

    def _current(self) -> int:
        s = "".join(self._digits) or "0"
        n = int(s)
        return -n if self._negative and n != 0 else n

    def process_key(self, ch: str) -> EditorResult:
        if ch in (k.ENTER, "\r"):
            return EditorResult("commit", self._current())
        if ch in (k.ESC,):
            return EditorResult("cancel")
        if ch in ("-",):
            # toggle sign
            self._negative = not self._negative
            return EditorResult("continue")
        if ch in (k.BACKSPACE, "\x7f"):
            if self._digits:
                self._digits.pop()
            return EditorResult("continue")
        if ch in (k.UP, "k"):
            n = self._current() + 1
            self.start(n)
            return EditorResult("continue")
        if ch in (k.DOWN, "j"):
            n = self._current() - 1
            self.start(n)
            return EditorResult("continue")
        if len(ch) == 1 and ch.isdigit():
            self._digits.append(ch)
            return EditorResult("continue")
        return EditorResult("continue")

    def render_inline(self) -> str:
        return str(self._current())


class FloatEditor(BaseEditor):
    def start(self, value: Any) -> None:
        try:
            fv = float(value)
        except Exception:
            fv = 0.0
        self._buffer = "%s" % fv
        if "." not in self._buffer:
            self._buffer += ".0"

    def _current(self) -> float:
        try:
            return float(self._buffer)
        except Exception:
            return 0.0

    def process_key(self, ch: str) -> EditorResult:
        if ch in (k.ENTER, "\r", "\n"):
            return EditorResult("commit", self._current())
        if ch in (k.ESC,):
            return EditorResult("cancel")
        if ch in (k.BACKSPACE, "\x7f"):
            if self._buffer:
                self._buffer = self._buffer[:-1]
            return EditorResult("continue")
        if ch in (k.UP, "k"):
            v = self._current() + 1.0
            self.start(v)
            return EditorResult("continue")
        if ch in (k.DOWN, "j"):
            v = self._current() - 1.0
            self.start(v)
            return EditorResult("continue")
        if len(ch) == 1 and (ch.isdigit() or ch in ".-+"):
            # Single dot only
            if ch == "." and "." in self._buffer:
                return EditorResult("continue")
            if ch == "-":
                v = self._current() * -1
                self.start(v)
                return EditorResult("continue")
            self._buffer += ch
            return EditorResult("continue")
        return EditorResult("continue")

    def render_inline(self) -> str:
        return self._buffer


class BoolEditor(BaseEditor):
    def start(self, value: Any) -> None:
        self._value = bool(value)

    def process_key(self, ch: str) -> EditorResult:
        if ch in (k.ENTER, "\r", "\n"):
            return EditorResult("commit", self._value)
        if ch in (k.ESC,):
            return EditorResult("cancel")
        if ch in (" ", "j", "k", k.DOWN, k.UP):
            self._value = not self._value
            return EditorResult("continue")
        if ch.lower() in ("t", "y", "1"):
            self._value = True
            return EditorResult("continue")
        if ch.lower() in ("f", "n", "0"):
            self._value = False
            return EditorResult("continue")
        return EditorResult("continue")

    def render_inline(self) -> str:
        return "True" if self._value else "False"


class DateEditor(BaseEditor):
    def start(self, value: Any) -> None:
        if isinstance(value, _dt.date) and not isinstance(value, _dt.datetime):
            d = value
        else:
            d = _dt.date.today()
        self._y = d.year
        self._m = d.month
        self._d = d.day
        self._field = 0  # 0=year,1=month,2=day

    def _apply(self) -> _dt.date:
        y, m, d = self._y, self._m, self._d
        # clamp day to month length
        while True:
            try:
                return _dt.date(y, m, d)
            except ValueError:
                if d > 28:
                    d -= 1
                else:
                    # fallback
                    return _dt.date(y, m, max(1, min(d, 28)))

    def process_key(self, ch: str) -> EditorResult:
        if ch in (k.ENTER, "\r", "\n"):
            return EditorResult("commit", self._apply())
        if ch in (k.ESC,):
            return EditorResult("cancel")
        if ch in (k.LEFT, "h"):
            self._field = (self._field - 1) % 3
            return EditorResult("continue")
        if ch in (k.RIGHT, "l"):
            self._field = (self._field + 1) % 3
            return EditorResult("continue")
        if ch in (k.UP, "k"):
            if self._field == 0:
                self._y += 1
            elif self._field == 1:
                self._m = 1 + (self._m % 12)
            else:
                self._d += 1
            return EditorResult("continue")
        if ch in (k.DOWN, "j"):
            if self._field == 0:
                self._y -= 1
            elif self._field == 1:
                self._m = 12 if self._m == 1 else self._m - 1
            else:
                self._d -= 1
            return EditorResult("continue")
        return EditorResult("continue")

    def render_inline(self) -> str:
        parts = [f"{self._y:04d}", f"{self._m:02d}", f"{self._d:02d}"]
        # Inline highlight using background color on the focused segment
        parts[self._field] = f"\x1b[30;46m{parts[self._field]}\x1b[0m"
        return "-".join(parts)


class DateTimeEditor(BaseEditor):
    def start(self, value: Any) -> None:
        if isinstance(value, _dt.datetime):
            dt = value
        else:
            now = _dt.datetime.now()
            dt = _dt.datetime(now.year, now.month, now.day, now.hour, now.minute, now.second)
        self._y, self._m, self._d = dt.year, dt.month, dt.day
        self._H, self._M, self._S = dt.hour, dt.minute, dt.second
        self._field = 0  # 0..5

    def _apply(self) -> _dt.datetime:
        y, m, d = self._y, self._m, self._d
        # clamp day to month length
        while True:
            try:
                return _dt.datetime(y, m, d, self._H, self._M, self._S)
            except ValueError:
                if d > 28:
                    d -= 1
                else:
                    return _dt.datetime(y, m, max(1, min(d, 28)), self._H, self._M, self._S)

    def process_key(self, ch: str) -> EditorResult:
        if ch in (k.ENTER, "\r", "\n"):
            return EditorResult("commit", self._apply())
        if ch in (k.ESC,):
            return EditorResult("cancel")
        if ch in (k.LEFT, "h"):
            self._field = max((self._field - 1), 0)
            return EditorResult("continue")
        if ch in (k.RIGHT, "l"):
            self._field = min((self._field + 1), 2)
            return EditorResult("continue")
        if ch in (k.UP, "k"):
            if self._field == 0:
                self._y += 1
                self._y = min((self._y), 9999)
            elif self._field == 1:
                self._m = 1 + (self._m % 12)
                self._m = min((self._m), 12)
            elif self._field == 2:
                self._d += 1
                self._d = min((self._d), 31)
            # elif self._field == 3:
            #     self._H = (self._H + 1) % 24
            # elif self._field == 4:
            #     self._M = (self._M + 1) % 60
            # else:
            #     self._S = (self._S + 1) % 60
            return EditorResult("continue")
        if ch in (k.DOWN, "j"):
            if self._field == 0:
                self._y -= 1
                self._y = max((self._y), 1)
            elif self._field == 1:
                self._m = 12 if self._m == 1 else self._m - 1
                self._m = max((self._m), 1)
            elif self._field == 2:
                self._d -= 1
                self._d = max((self._d), 1)
            # elif self._field == 3:
            #     self._H = (self._H - 1) % 24
            # elif self._field == 4:
            #     self._M = (self._M - 1) % 60
            # else:
            #     self._S = (self._S - 1) % 60
            return EditorResult("continue")
        return EditorResult("continue")

    def render_inline(self) -> str:
        # Render only date portion per requirement
        parts = [f"{self._y:04d}", f"{self._m:02d}", f"{self._d:02d}"]
        # Map overall field index (0..5) to date subindex (0..2) for highlighting; times highlight nothing
        date_idx = self._field if self._field < 3 else None
        if date_idx is not None:
            parts[date_idx] = f"\x1b[30;46m{parts[date_idx]}\x1b[0m"
        return "-".join(parts)


class EditorRegistry:
    def __init__(self) -> None:
        self._registry: Dict[type, BaseEditor] = {}

    def register(self, py_type: type, editor: BaseEditor) -> None:
        self._registry[py_type] = editor

    def get(self, py_type: type) -> BaseEditor:
        # direct match
        if py_type in self._registry:
            # return a fresh copy (stateless or re-created)
            editor = self._registry[py_type].__class__()
            return editor
        # inheritance chain
        for t in self._registry:
            if isinstance(py_type, type) and issubclass(py_type, t):
                return self._registry[t].__class__()
        # fallback
        return StringEditor()


# -----------------------------
# Renderer (minimal ANSI redraw)
# -----------------------------

CSI = "\x1b["


class Renderer:
    def __init__(self) -> None:
        self._last_lines_count = 0  # physical lines occupied in previous render
        self._ansi_re = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

    def _get_cols(self) -> int:
        try:
            cols = shutil.get_terminal_size(fallback=(80, 24)).columns
        except Exception:
            cols = 80
        return max(1, cols)

    def _visible_len(self, s: str) -> int:
        # strip ANSI sequences when measuring
        return len(self._ansi_re.sub("", s))

    def _compute_physical_lines(self, lines: List[str], cols: int) -> int:
        # With truncation, each logical line occupies exactly one physical line
        return len(lines)

    def _alloc_space(self, region_lines: int) -> None:
        if region_lines > self._last_lines_count:
            delta = region_lines - self._last_lines_count
            sys.stdout.write("\n" * (delta + 0))
            sys.stdout.flush()

    def _move_to_top(self) -> None:
        if self._last_lines_count > 0:
            sys.stdout.write(f"{CSI}{self._last_lines_count}A")

    def _truncate_keeping_ansi(self, s: str, cols: int) -> str:
        if cols <= 0:
            return ""
        out: List[str] = []
        visible = 0
        i = 0
        n = len(s)
        while i < n and visible < cols:
            if s[i] == "\x1b":
                m = self._ansi_re.match(s, i)
                if m:
                    out.append(m.group(0))
                    i = m.end()
                    continue
            ch = s[i]
            if ch == "\n" or ch == "\r":
                break
            out.append(ch)
            visible += 1
            i += 1
        # ensure styles do not leak
        out.append("\x1b[0m")
        return "".join(out)

    def render(self, lines: List[str]) -> None:
        cols = self._get_cols()
        physical_needed = self._compute_physical_lines(lines, cols)
        region_height = max(physical_needed, self._last_lines_count)
        self._alloc_space(region_height)
        self._move_to_top()
        # Print all content lines truncated to terminal width
        for idx, content in enumerate(lines):
            truncated = self._truncate_keeping_ansi(content, cols)
            sys.stdout.write(f"{CSI}2K\r{truncated}")
            if idx < len(lines):
                sys.stdout.write("\n")
        # If previous render had more physical lines than we printed now,
        # clear the leftover trailing lines
        if self._last_lines_count > physical_needed:
            extra = self._last_lines_count - physical_needed
            for _ in range(extra):
                sys.stdout.write("\n")
                sys.stdout.write(f"{CSI}2K\r")
        sys.stdout.flush()
        self._last_lines_count = physical_needed


# -----------------------------
# InterDict implementation
# -----------------------------


class InterDict:
    def __init__(self, target: dict, show_brackets: bool = True, editable_keys: bool = False):
        self._original = target
        self._working = copy.deepcopy(target)
        self._show_brackets = show_brackets
        self._editable_keys = editable_keys
        self._atoms: List[Atom] = []
        self._renderer = Renderer()
        self._registry = EditorRegistry()
        self._install_default_editors()
        self._serialize_root()

    @classmethod
    def from_dict(cls, d: dict, *, show_brackets: bool = True, editable_keys: bool = False) -> "InterDict":
        return cls(d, show_brackets=show_brackets, editable_keys=editable_keys)

    # -------------------------
    # Public properties
    # -------------------------
    @property
    def show_brackets(self) -> bool:
        return self._show_brackets

    @show_brackets.setter
    def show_brackets(self, value: bool) -> None:
        self._show_brackets = bool(value)
        self._serialize_root()

    @property
    def editable_keys(self) -> bool:
        return self._editable_keys

    @editable_keys.setter
    def editable_keys(self, value: bool) -> None:
        self._editable_keys = bool(value)
        self._serialize_root()

    # -------------------------
    # Dict-like API
    # -------------------------
    def __getitem__(self, key: Any) -> Any:
        return self._working[key]

    def __setitem__(self, key: Any, value: Any) -> None:
        self._working[key] = value
        self._serialize_root()

    def get(self, key: Any, default: Any = None) -> Any:
        return self._working.get(key, default)

    def keys(self) -> Iterable[Any]:
        return self._working.keys()

    def items(self) -> Iterable[Tuple[Any, Any]]:
        return self._working.items()

    def values(self) -> Iterable[Any]:
        return self._working.values()

    def __iter__(self):
        return iter(self._working)

    def __len__(self) -> int:
        return len(self._working)

    # -------------------------
    # Editor extension API
    # -------------------------
    def register_editor(self, py_type: type, editor: BaseEditor) -> None:
        self._registry.register(py_type, editor)

    # -------------------------
    # Serialization
    # -------------------------
    def _serialize_root(self) -> None:
        self._atoms = []
        self._serialize(self._working, depth=0, path=tuple())

    def _atom_for_marker(self, marker: str, depth: int, path: Tuple[Any, ...]) -> None:
        self._atoms.append(
            Atom(
                value=marker,
                py_type=str,
                depth=depth,
                role="marker",
                editable=False,
                path=path,
                marker=marker,
            )
        )

    def _is_container(self, obj: Any) -> bool:
        return isinstance(obj, (dict, list))

    def _serialize(self, obj: Any, depth: int, path: Tuple[Any, ...]) -> None:
        if isinstance(obj, dict):
            if self._show_brackets:
                self._atom_for_marker("{", depth, path)
            for k_, v in obj.items():
                kr = KeyRef(k_)
                is_container = self._is_container(v)
                # Emit a key line if keys are editable OR the value is a container
                if self._editable_keys or is_container:
                    key_editable = self._editable_keys and self._is_type_editable(type(k_))
                    self._atoms.append(
                        Atom(
                            value=k_,
                            py_type=type(k_),
                            depth=depth + 1,
                            role="key",
                            editable=key_editable,
                            path=path + (kr,),
                            key_ref=kr,
                        )
                    )
                if is_container:
                    # container value – descend
                    self._serialize(v, depth=depth + 2, path=path + (kr,))
                else:
                    # scalar value atom (render inline with key when keys are uneditable)
                    val_editable = self._is_type_editable(type(v))
                    self._atoms.append(
                        Atom(
                            value=v,
                            py_type=type(v),
                            depth=depth + 1,
                            role="value",
                            editable=val_editable,
                            path=path + (kr,),
                            key_ref=kr,
                        )
                    )
            if self._show_brackets:
                self._atom_for_marker("}", depth, path)
            return

        if isinstance(obj, list):
            if self._show_brackets:
                self._atom_for_marker("[", depth, path)
            for idx, v in enumerate(obj):
                if self._is_container(v):
                    self._serialize(v, depth=depth + 1, path=path + (idx,))
                else:
                    val_editable = self._is_type_editable(type(v))
                    self._atoms.append(
                        Atom(
                            value=v,
                            py_type=type(v),
                            depth=depth + 1,
                            role="value",
                            editable=val_editable,
                            path=path + (idx,),
                        )
                    )
            if self._show_brackets:
                self._atom_for_marker("]", depth, path)
            return

        # Fallback scalar
        val_editable = self._is_type_editable(type(obj))
        self._atoms.append(
            Atom(value=obj, py_type=type(obj), depth=depth, role="value", editable=val_editable, path=path)
        )

    def _is_type_editable(self, t: type) -> bool:
        # We consider anything that resolves to an editor editable
        return isinstance(self._registry.get(t), BaseEditor)

    # -------------------------
    # Rendering helpers
    # -------------------------
    def _format_value_for_display(self, value: Any, py_type: type, editing_current: bool) -> str:
        # When editing, editors can return pre-styled strings; prefer them
        if editing_current and isinstance(value, str):
            return value
        # Always render date/datetime as YYYY-MM-DD
        try:
            if isinstance(value, (_dt.date, _dt.datetime)):
                return f"{value.year:04d}-{value.month:02d}-{value.day:02d}"
        except Exception:
            pass
        return repr(value)

    def _line_for_atom(self, atom: Atom, is_current: bool, editing_current: bool) -> str:
        indent = "  " * atom.depth
        style_prefix = ""
        style_suffix = ""
        if is_current:
            if editing_current:
                # Render whole line in yellow while editing
                style_prefix = "\x1b[33m"
                style_suffix = "\x1b[0m"
            else:
                # inverse video when just selected
                style_prefix = "\x1b[7m"
                style_suffix = "\x1b[0m"
        elif not atom.editable and atom.role != "marker":
            style_prefix = "\x1b[2m"  # dim
            style_suffix = "\x1b[0m"

        if atom.role == "marker":
            content = atom.marker or ""
            return f"{indent}{style_prefix}{content}{style_suffix}"

        if atom.role == "key":
            content = repr(atom.value) + ":"
            return f"{indent}{style_prefix}{content}{style_suffix}"

        # value
        # If keys are uneditable and this is a dict value, render inline as `key: value`
        prefix = ""
        if (not self._editable_keys) and atom.key_ref is not None:
            prefix = repr(atom.key_ref.key) + ": "
        content_value = self._format_value_for_display(atom.value, atom.py_type, editing_current)
        content = prefix + content_value
        return f"{indent}{style_prefix}{content}{style_suffix}"

    def _build_screen(
        self,
        cursor_index: int,
        footer: Optional[str] = None,
        editing_hint: Optional[str] = None,
        editing: bool = False,
    ) -> List[str]:
        lines: List[str] = []
        for i, atom in enumerate(self._atoms):
            is_current = i == cursor_index
            lines.append(self._line_for_atom(atom, is_current, editing_current=editing and is_current))
        # footer

        footer_text = footer or "Press '?' to display keyboard controls."
        lines.append("")
        lines.append(footer_text)
        return lines

    # -------------------------
    # Path helpers
    # -------------------------
    def _get_parent_and_token(self, path: Tuple[Any, ...]) -> Tuple[Any, Any]:
        if not path:
            return None, None
        parent_path = path[:-1]
        token = path[-1]
        node = self._working
        for step in parent_path:
            if isinstance(step, KeyRef):
                node = node[step.key]
            else:
                node = node[step]
        return node, token

    def _assign_at_path(self, path: Tuple[Any, ...], new_value: Any) -> None:
        parent, token = self._get_parent_and_token(path)
        if parent is None:
            # assign root
            self._working = new_value
            return
        if isinstance(token, KeyRef):
            parent[token.key] = new_value
        else:
            parent[token] = new_value

    def _rename_key(self, path: Tuple[Any, ...], key_ref: KeyRef, new_key: Any) -> None:
        parent, token = self._get_parent_and_token(path)
        if not isinstance(token, KeyRef):
            return
        old_key = key_ref.key
        try:
            hash(new_key)
        except Exception:
            return
        if new_key == old_key:
            return
        value = parent.pop(old_key)
        parent[new_key] = value
        key_ref.key = new_key

    # -------------------------
    # Interactive loop
    # -------------------------
    def edit(self) -> dict:
        cursor = self._first_editable_index(0)
        renderer = self._renderer
        while True:
            screen = self._build_screen(cursor)
            renderer.render(screen)
            try:
                ch = readkey()
            except KeyboardInterrupt:
                print("")
                rich.print("[red]Interrupted by user (Ctrl+C).", end="")
                exit(1)
            # Ctrl+S to save all changes and exit
            if ch in (k.CTRL_S, "\x13", "\n"):
                # persist working copy back into original reference
                self._original.clear()
                if isinstance(self._original, dict) and isinstance(self._working, dict):
                    self._original.update(self._working)
                else:
                    # if target reference isn't dict, just replace variable semantics are limited here
                    pass
                return self._original
            # Show keyboard controls overlay on '?'
            if ch == "?":
                help_lines = [
                    "Controls:",
                    "  j / Down : Move down",
                    "  k / Up   : Move up",
                    "  Enter    : Edit current",
                    "  Esc      : Cancel current edit",
                    "  Ctrl+S   : Save all and exit",
                    "  Int: digits/backspace; k/UP +1, j/DOWN -1",
                    "  Float: digits, '.', '-', '+'; k/UP +1.0, j/DOWN -1.0",
                    "  Bool: space/j/k toggles",
                    "  Date: h/LEFT,l/RIGHT select; k/UP,j/DOWN change",
                    "  DateTime: same as Date (date-part only)",
                    "Press any key to continue...",
                ]
                cols = self._renderer._get_cols()
                # Wrap each line to terminal width
                wrapped: List[str] = []
                for line in help_lines:
                    wrapped.append(line[0:cols])
                    # wrapped.extend(textwrap.wrap(line, width=cols) or [""])
                # Allocate space and render the overlay
                self._renderer._alloc_space(len(wrapped))
                # self._renderer._move_to_top()
                print(_MOVE_UP_AND_CLEAR_SCREEN * len(wrapped), end="")
                for idx, line in enumerate(wrapped):
                    sys.stdout.write(f"{CSI}2K\r{line}")
                    if idx < len(wrapped) - 1:
                        sys.stdout.write("\n")
                sys.stdout.flush()
                # Wait for any key, then continue main loop which re-renders UI
                try:
                    readkey()
                except KeyboardInterrupt:
                    print("")
                    rich.print("[red]Interrupted by user (Ctrl+C).", end="")
                    exit(1)
                print(_CLEAR_SCREEN)
                print("\n" * len(wrapped))
                continue
            if ch in (k.DOWN, "j"):
                cursor = self._next_editable_index(cursor)
                continue
            if ch in (k.UP, "k"):
                cursor = self._prev_editable_index(cursor)
                continue
            if ch in (k.ENTER, "\r", "\n"):
                # start editing the current atom if editable
                if 0 <= cursor < len(self._atoms):
                    atom = self._atoms[cursor]
                    if not atom.editable:
                        continue
                    # run editor
                    editor = self._registry.get(atom.py_type)
                    editor.start(atom.value)
                    while True:
                        hint = self._editor_hint(editor)
                        # For immediate visual updates, rewrite the atom's display value each cycle
                        preview_value = editor.render_inline()
                        # Store string result for renderer to show inline highlights
                        atom.value = preview_value if isinstance(preview_value, str) else preview_value
                        screen = self._build_screen(cursor, editing_hint=hint, editing=True)
                        renderer.render(screen)
                        try:
                            ch2 = readkey()
                        except KeyboardInterrupt:
                            print("")
                            rich.print("[red]Interrupted by user (Ctrl+C).", end="")
                            exit(1)
                        if ch2 in (k.ESC,):
                            break
                        result = editor.process_key(ch2)
                        if result.status == "continue":
                            continue
                        if result.status == "cancel":
                            # revert visual
                            self._serialize_root()
                            break
                        if result.status == "commit":
                            if atom.role == "key" and atom.key_ref is not None:
                                self._rename_key(atom.path, atom.key_ref, result.value)
                            else:
                                self._assign_at_path(atom.path, result.value)
                            # re-serialize and keep cursor close to prior position
                            self._serialize_root()
                            cursor = self._closest_editable_index(cursor)
                            break
                continue

    def _editor_hint(self, editor: BaseEditor) -> str:
        if isinstance(editor, IntEditor):
            return "0-9: add digits, Backspace: delete, k/UP: +1, j/DOWN: -1, Enter: commit"
        if isinstance(editor, FloatEditor):
            return "0-9 . - +, Backspace, k/UP: +1.0, j/DOWN: -1.0, Enter: commit"
        if isinstance(editor, BoolEditor):
            return "Space: toggle, Enter: commit"
        if isinstance(editor, DateEditor):
            return "h/LEFT,l/RIGHT: select; k/UP,j/DOWN: change; Enter: commit"
        if isinstance(editor, DateTimeEditor):
            return "h/LEFT,l/RIGHT: select; k/UP,j/DOWN: change; Enter: commit"
        return "Type to edit, Backspace to delete, Enter to commit"

    def _first_editable_index(self, start: int) -> int:
        for i in range(start, len(self._atoms)):
            if self._atoms[i].editable:
                return i
        for i in range(0, start):
            if self._atoms[i].editable:
                return i
        return 0

    def _next_editable_index(self, current: int) -> int:
        if not self._atoms:
            return 0
        i = (current + 1) % len(self._atoms)
        start = i
        while True:
            if self._atoms[i].editable:
                return i
            i = (i + 1) % len(self._atoms)
            if i == start:
                return current

    def _prev_editable_index(self, current: int) -> int:
        if not self._atoms:
            return 0
        i = (current - 1) % len(self._atoms)
        start = i
        while True:
            if self._atoms[i].editable:
                return i
            i = (i - 1) % len(self._atoms)
            if i == start:
                return current

    def _closest_editable_index(self, current: int) -> int:
        # Try to keep same index if still editable; otherwise move to next editable
        if 0 <= current < len(self._atoms) and self._atoms[current].editable:
            return current
        return self._next_editable_index(current)

    def get_value(self) -> dict:
        return copy.deepcopy(self._working)

    # -------------------------
    # Default editors
    # -------------------------
    def _install_default_editors(self) -> None:
        self._registry.register(str, StringEditor())
        self._registry.register(int, IntEditor())
        self._registry.register(float, FloatEditor())
        self._registry.register(bool, BoolEditor())
        self._registry.register(_dt.date, DateEditor())
        self._registry.register(_dt.datetime, DateTimeEditor())
