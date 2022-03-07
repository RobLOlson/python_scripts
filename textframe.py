"""textframe.py
Provides functions and classes for organizing text to display on a console.
 Convenience Functions:

  frame(...) <-- Creates an ASCII border around text
  table(...) <-- Turns a sequence of sequences into an ASCII table

 Classes:

  Panel(...) <-- Creates a hierarchy of framed text panels
  Frame(...) <-- Creates a Frame object that remembers how to frame text

This module also contains an assortment of niche helper functions.

  justify(...) <-- SAFELY justifies a paragraph of text
  constrain(...) <-- similar to textwrap.wrap(...) but leaves \n's alone
  parallelize(...) <-- Aligns a list of paragraphs side by side.
  columnize(...) <-- Stacks a list of paragraphs on top of each other

TODO:  Finish my Frame class.  Debug my table function.

Rob Olson
"""


import re, operator, math, hierarchy, sys

try:
    from testtextframe import *
except ImportError:
    pass


class PanelError(Exception):
    """Raised when an illegal panel operation is attempted."""


class FrameError(Exception):
    """Indicates an error emanating from the Frame class."""


# --- Frame Class -----------------------------------------------------------
#
# Notes:  This class needs a lot work.  It does the simple cases just fine, but
#         most of the private methods can't handle edge cases because they
#         were vultured from my previous attempts instead of written from
#         scratch.  I should probably just bite the bullet and re-write them.
#         Before I can do that, I need to spend some time planning it out.
#


class Frame(object):
    """Represents a frame into which text can be fed for presentation."""

    MAX_WIDTH = 79
    MAX_HEIGHT = 24

    # --- Special Methods <Frame> -----------------------------------------------

    def __init__(
        self, width=-1, height=-1, padding=0, frames=True, hJust="left", vJust="top"
    ):

        self.width = width
        self.height = height
        self.padding = padding
        self.frames = frames
        self.hJust = hJust
        self.vJust = vJust
        self.background_Char = " "
        self._horizontal = True
        self._vertical = False

    def __call__(self, text, **kwargs):
        if isinstance(text, (list, tuple)):
            if all([isinstance(elem, (list, tuple)) for elem in text]):
                print("TODO: table method.")

            elif self.vertical:
                return self._columnize(text, **kwargs)
            else:
                return self._parallelize(text, **kwargs)

        else:
            return self.render(text, **kwargs)

    def __repr__(self):
        return "Frame({}, {}, {}, {})".format(
            self.width, self.height, self.padding, self.frames
        )

    # ^^^ Special Methods <Frame> ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    #
    # --- Properties <Frame> -----------------------------------------------------
    @property
    def horizontal(self):
        return self._horizontal

    @horizontal.setter
    def horizontal(self, value):
        if value:
            self._horizontal = True
            self._vertical = False
        else:
            self._horizontal = False
            self._vertical = True

    @property
    def vertical(self):
        return self._vertical

    @vertical.setter
    def vertical(self, value):
        if value:
            self._vertical = True
            self._horizontal = False
        else:
            self._vertical = False
            self._horizontal = True

    @property
    def width(self):
        """Value of `width` must fall between -1 and MAX_WIDTH (default: 79)
        When `width` >= 0, Frames is guaranteed to return a string in which every
            line is exactly `width` characters long.
        If `width` == -1, Frames cannot guarantee the width of its output, but does
            guarantee that it will not disturb the pre-formatting of any one line
            of text (although entire lines may be dropped if they exceed `height`.)

        NOTE: If both `width` and `height` are equal to -1, input text is not altered
              in any way, except to wrap a frame around it such that the pre-
              formatting of every line is preserved."""
        return self._width

    @width.setter
    def width(self, value):
        self._width = max(-1, min(value, self.MAX_WIDTH))

    @property
    def height(self):
        """Value of `height` must fall between -1 and MAX_HEIGHT (default: 24)
        When `height` > 0, Frames is guaranteed to return a string with that many
            lines of text.
        If `height` == -1, Frames cannot guarantee the line count of its ouput, but
            does guarantee that every line of input will take up exactly one line
            of output (although the line may be truncated if it exceeds `width`).

        NOTE: If both `width` and `height` are equal to -1, input text is not altered
              in any way, except to wrap a frame around it such that the pre-
              formatting of every line is preserved."""

        return self._height

    @height.setter
    def height(self, value):
        self._height = max(-1, min(value, self.MAX_HEIGHT))

    @property
    def padding(self):
        return self._padding

    @padding.setter
    def padding(self, value):
        self._padding = max(0, value)

    @property
    def frames(self):
        """Returns the status of the Frame's frames.
        If all the frames are on, returns True.
        If all the frames are off, returns False.
        If a mixture of off and on, returns a tuple of 4 bools, 1 for each frame."""
        if self._frames is not None:
            return self._frames
        else:
            return (self._topFrame, self._botFrame, self._leftFrame, self._rightFrame)

    @frames.setter
    def frames(self, value):
        """Sets the status of the Frame's frames.
        If set to True, all frames are activated.
        If set to False, all frames are deactivated.
        If set to a tuple of 4 bools, the specified combination of frames is applied."""
        try:
            self._topFrame = value[0]
            self._botFrame = value[1]
            self._leftFrame = value[2]
            self._rightFrame = value[3]
            self._frames = None

        except TypeError:
            if value:
                self._frames = True
                self._topFrame = True
                self._botFrame = True
                self._leftFrame = True
                self._rightFrame = True

            else:
                self._frames = False
                self._topFrame = False
                self._botFrame = False
                self._leftFrame = False
                self._rightFrame = False

    @property
    def topFrame(self):
        return self._topFrame

    @topFrame.setter
    def topFrame(self, value):
        if self._topFrame != value:
            self._topFrame = not self._topFrame

        if self.topFrame and self.botFrame and self.leftFrame and self.rightFrame:
            self._frames = True
        elif (
            (not self.topFrame)
            and (not self.botFrame)
            and (not self.leftFrame)
            and (not self.rightFrame)
        ):
            self._frames = False
        else:
            self._frames = None

    @property
    def botFrame(self):
        return self._botFrame

    @botFrame.setter
    def botFrame(self, value):
        if self._botFrame != value:
            self._botFrame = not self._botFrame

        if self.topFrame and self.botFrame and self.leftFrame and self.rightFrame:
            self._frames = True
        elif (
            (not self.topFrame)
            and (not self.botFrame)
            and (not self.leftFrame)
            and (not self.rightFrame)
        ):
            self._frames = False
        else:
            self._frames = None

    @property
    def leftFrame(self):
        return self._leftFrame

    @leftFrame.setter
    def leftFrame(self, value):
        if self._leftFrame != value:
            self._leftFrame = not self._leftFrame

        if self.topFrame and self.botFrame and self.leftFrame and self.rightFrame:
            self._frames = True
        elif (
            (not self.topFrame)
            and (not self.botFrame)
            and (not self.leftFrame)
            and (not self.rightFrame)
        ):
            self._frames = False
        else:
            self._frames = None

    @property
    def rightFrame(self):
        return self._rightFrame

    @rightFrame.setter
    def rightFrame(self, value):
        if self._rightFrame != value:
            self._rightFrame = not self._rightFrame

        if self.topFrame and self.botFrame and self.leftFrame and self.rightFrame:
            self._frames = True
        elif (
            (not self.topFrame)
            and (not self.botFrame)
            and (not self.leftFrame)
            and (not self.rightFrame)
        ):
            self._frames = False
        else:
            self._frames = None

    # ^^^ Properties <Frame> ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    #
    # --- Private Methods <Frame> ------------------------------------------
    #
    # --- self._parallelize(...) <Frame private method> --------------------

    def _parallelize(self, texts=[], widths=None, **kwargs):

        if widths == None:
            widths = [self.width]

        # An empty list argument returns an empty string
        # I'm not sure if this is good design or not
        if not texts:
            return ""

        args = texts
        tallest = []
        lengths = []
        copy = []
        pattern = re.compile(r"^.*$", flags=re.M)
        # Matches any line of text

        if len(widths) == len(texts):
            pass
        elif len(widths) == 1:
            widths = widths * len(texts)

        args = [
            (frame(elem, width, padding=-1) if width != -1 else elem)
            for elem, width in zip(args, widths)
        ]

        # Find the tallest string (most lines) -> tallest
        # Find the longest line of each string  -> lengths

        for text in args:
            if text.count("\n") > tallest.count("\n"):
                tallest = text
            textSize = 0
            for line in text.split("\n"):
                if len(line) > textSize:
                    textSize = len(line)
            lengths.append(textSize)

        # Pad strings with blank lines until they are equally tall
        # Width of blank lines is equal to the string's widest line
        for num in range(len(args)):
            copy.append(
                args[num]
                + ("\n" + " " * (lengths[num]))
                * (tallest.count("\n") - args[num].count("\n"))
            )

        copy = [elem.split("\n") for elem in copy]

        # copy[n][m] is an n-by-m matrix
        # n chooses a string
        # m chooses a line-number

        # Print the 1st line of every string in tandem
        # Then print the 2nd line of every string in tandem
        # Etc..

        screen = ""

        for num in range(len(copy[0])):
            output = ""
            for num2 in range(len(copy)):
                output += copy[num2][num] + " " * (lengths[num2] - len(copy[num2][num]))

            # width < 0 means do not artificially restrict the line width
            screen += output + "\n"

        # Remove the last newline
        screen = screen[:-1]

        return screen

    # ^^^ self._parallelize(...) <Frame private method> ^^^^^^^^^^^^^^^^^^^^
    #
    # --- self._columnize(...) <Frame private method> ----------------------
    #

    def _columnize(
        self,
        texts=[],
        width=None,
        height=None,
        padding=None,
        frames=None,
        hJust=None,
        vJust=None,
        **kwargs
    ):

        if width is None:
            width = self.width
        if height is None:
            height = self.height
        if padding is None:
            padding = self.padding
        if hJust is None:
            hJust = self.hJust
        if vJust is None:
            vJust = self.vJust
        if frames is None:
            if self.frames:
                frames = True
            else:
                frames = False
            topFrame = self.topFrame
            botFrame = self.botFrame
            leftFrame = self.leftFrame
            rightFrame = self.rightFrame

        # If no strings were passed, return a blank line of default width
        if not texts:
            return " " * width

        if padding < -1:
            padding = 0

        if height > 0:
            height = height - (len(texts) + 1) * frames
            height = height / len(texts)
            height = height + 2 * frames

        if width < 0:
            biggest = 0
            for elem in texts:
                if len(longest_line(elem)) > biggest:
                    biggest = len(longest_line(elem))
            width = biggest + 2 * frames + 4 * min(0, padding)
        column = frame(
            texts[0],
            width=width,
            height=height,
            padding=padding,
            topFrame=topFrame,
            botFrame=botFrame,
            leftFrame=leftFrame,
            rightFrame=rightFrame,
        )

        for num in range(1, len(texts)):
            column = (
                column
                + "\n"
                + frame(
                    texts[num],
                    width=width,
                    height=height,
                    padding=padding,
                    topFrame=False,
                    botFrame=botFrame,
                    leftFrame=leftFrame,
                    rightFrame=rightFrame,
                )
            )
        return column

    # ^^^ self._columnize(...) <Frame private method> ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    #
    # --- self._apply(...) <Frame private method> --------------------------------
    #

    def _apply(
        self,
        text,
        width=None,
        height=None,
        padding=None,
        background_Char=None,
        hJust=None,
        vJust=None,
        topFrame=None,
        botFrame=None,
        leftFrame=None,
        rightFrame=None,
    ):
        """Frames `text`.  Returns a string."""

        if width is None:
            width = self.width
        if height is None:
            height = self.height
        if padding is None:
            padding = self.padding
        if background_Char is None:
            background_Char = self.background_Char
        if hJust is None:
            hJust = self.hJust
        if vJust is None:
            vJust = self.vJust
        if topFrame is None:
            topFrame = self.topFrame
        if botFrame is None:
            botFrame = self.botFrame
        if leftFrame is None:
            leftFrame = self.leftFrame
        if rightFrame is None:
            rightFrame = self.rightFrame

        _ = background_Char

        # Not sure if this is good design, but a negative padding has
        # side effects (removing the frames)
        if padding < 0:
            padding = 0
            topFrame = False
            botFrame = False
            leftFrame = False
            rightFrame = False

        # This handles simple edge cases
        if width == 0 or height == 0:
            return ""

        # Not sure if this is good design, but an empty input string
        # will not reduce the canvas size below a single character's worth
        if text == "":
            text = _

        # if width < 0, adjust width to accomodate the widest line of text
        # plus any padding or framing characters
        if width < 0:
            widest = 0
            for line in text.split("\n"):
                if len(line) > widest:
                    widest = len(line)
            width = widest + 4 * padding + leftFrame + rightFrame
        ##        if width>80:
        ##            width = 80

        # The canvas does not include the frame or any padding
        canvasWidth = width - padding * 4 - leftFrame - rightFrame

        # trim lines to fit within the width of the canvas
        # NOTE: overflow is moved to the following line(s)
        # NOTE: line breakage occurs only at word boundaries
        text = self._constrain(text, canvasWidth)

        # The minimum # of lines able to contain the entire framed text
        minimumHeight = 1 + text.count("\n") + topFrame + botFrame + padding * 2

        if height < 0:
            height = minimumHeight

        canvasHeight = height - topFrame - botFrame - padding * 2

        # if `text` was empty, fill up the canvas with background
        if text == _:
            text = _ + (_ * (canvasWidth) + "\n") * (canvasHeight)
            text = text[:-1]

        text = self._justify(text, canvasWidth, canvasHeight, hJust, vJust)

        lines = text.split("\n")

        lines = [(elem if elem else " " * canvasWidth) for elem in lines]

        # this whole mess of code is responsible for handling
        # the edge case of a small height argument...
        # ... there has to be a better way...
        if minimumHeight > height:
            dud = (
                ("+" if leftFrame else "")
                + "-" * (width - leftFrame - rightFrame)
                + ("+" if rightFrame else "")
            )

            pdud = (
                ("|" if leftFrame else "")
                + (_ + _) * padding
                + _ * (canvasWidth)
                + (_ + _) * padding
                + ("|" if rightFrame else "")
            )

            diff = height

            if height == 1:
                if topFrame:
                    return dud
                else:
                    dud = (
                        ("|" if leftFrame else "")
                        + (_ + _) * padding
                        + lines[0][: max(0, canvasWidth)]
                        + (_ + _) * padding
                        + ("|" if rightFrame else "")
                    )
                    dud = dud[:width]
                    return dud

            top = [dud] if topFrame else []
            diff -= topFrame
            bot = [dud] if botFrame else []
            diff -= botFrame

            n = 0
            while n < padding and diff > 0:
                top.append(pdud)
                n += 1
                diff -= 1

            top = [elem[:width] for elem in top]

            mid = []

            n = 0
            while n < padding and diff > 0:
                bot.insert(0, pdud)
                n += 1
                diff -= 1

            bot = [elem[:width] for elem in bot]

            count = 0
            while count < diff:
                mid.append(
                    ("|" if leftFrame else "")
                    + (_ + _) * padding
                    + lines[count][: max(0, canvasWidth)]
                    + (_ + _) * padding
                    + ("|" if rightFrame else "")
                )
                mid[-1] = mid[-1][:width]
                count += 1

            if rightFrame:
                top = [elem[:-1] + "|" for elem in top]
                mid = [elem[:-1] + "|" for elem in mid]
                bot = [elem[:-1] + "|" for elem in bot]
                if topFrame:
                    top[0] = top[0][:-1] + "+"
                if botFrame:
                    bot[-1] = bot[-1][:-1] + "+"

            return "\n".join(top + mid + bot)

        # this handles the other stupid edge case...
        # where is the elegant solution?
        if width == 1:
            dud = []
            if leftFrame:
                if topFrame:
                    dud.append("+")
                if botFrame:
                    dud.append("+")
                for n in range(height - leftFrame - rightFrame):
                    dud.insert(1, "|")
                return "\n".join(dud)
            elif padding > 0:
                if topFrame:
                    dud.append("-")
                if botFrame:
                    dud.append("-")
                for n in range(height - leftFrame - rightFrame):
                    dud.insert(1, _)
                return "\n".join(dud)
            else:
                if topFrame:
                    dud.append("-")
                if botFrame:
                    dud.append("-")
                for n in range(height - leftFrame - rightFrame):
                    dud.insert(n + leftFrame + rightFrame, lines[n][0])
                return "\n".join(dud)

        lines = [line[:canvasWidth] for line in lines]

        # Add Top and Bottom Padding
        for n in range(padding):
            lines.insert(0, _ * (canvasWidth))
            lines.append(_ * (canvasWidth))

        # Add Padding and Side Frames
        lines = [
            ("|" if leftFrame else "")
            + (_ + _) * padding
            + line
            + (_ + _) * padding
            + ("|" if rightFrame else "")
            for line in lines
        ]

        if topFrame:
            lines.insert(0, "+" + "-" * (width - 2) + "+")
            lines[0] = lines[0][:width]

        if botFrame:
            lines.append("+" + "-" * (width - 2) + "+")
            lines[-1] = lines[-1][:width]

        return "\n".join(lines)

    # ^^^ self._apply(...) <Frame private method> ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    #
    # --- _constrain(...) <Frame private static method> ----------------------------

    @staticmethod
    def _constrain(text, width=-1):
        """trim lines to a maximum of width characters"""

        longest = 0

        # matches all trailing new lines, if any
        trailing = re.search(r"\n*$", text)

        # hold the trailing new lines; we'll put them back at the end
        last = text[slice(*trailing.span())]

        # `text` is what's left after removing trailing new lines
        text = text[: trailing.span()[0]]

        # Matches any word (contiguous punctuation is considered part of the word)
        pattern = re.compile(r"\b\S+\b")

        for elem in pattern.findall(text):
            if len(elem) > longest:
                longest = len(elem)

        # Matches any line of text that has at least two pipes
        # temp = r"^.*\|.*\|.*$"

        # Nested RE:
        # For every line with pipes pipes:
        #   For every space:
        #       Replace it with a temporary character
        #
        # (This prevents whitespace inside a frame from breaking
        # text = re.sub(temp, lambda m: re.sub(r" ", "`",m.group(0)), text, flags=re.M)

        # Matches the maximum number of characters terminated by a space
        # that will fit in width
        pattern = r"(.{," + str(width) + r"})(\s|(\w--?\w)|$)"

        text = re.sub(
            pattern,
            lambda m: m.group(0)
            if re.match(r"^\+-*\+^", m.group(0))
            else (
                m.group(1) + "\n"
                if len(m.group(2)) < 2
                else m.group(1) + m.group(2)[:-1] + "\n" + m.group(2)[-1:]
            ),
            text,
        )

        # Revert temporary characters to spaces
        text = re.sub("`", " ", text)

        if text[-1] == "\n":
            text = text[:-1]
        text = text + last
        return text

    # ^^^ _constrain(...) <Frame private static method> ----------------------------
    #
    # --- _justify(...) <Frame private static method> ------------------------------

    @staticmethod
    def _justify(text, width=-1, height=-1, hJust="left", vJust="top"):
        """Justifies a paragraph of text.  Guaranteed not to lose any text."""

        hJust = hJust.lower()
        vJust = vJust.lower()

        if hJust == "left" or hJust == "<" or hJust == "l":
            hJust = "left"
        elif hJust == "center" or hJust == "^" or hJust == "c":
            hJust = "center"
        elif hJust == "right" or hJust == ">" or hJust == "r":
            hJust = "right"
        else:
            raise KeyError("Justification specifier ({}) not found.".format(hJust))

        if vJust == "top" or vJust == "^" or vJust == "t":
            vJust = "top"
        elif vJust == "middle" or vJust == "mid" or vJust == "m":
            vJust = "middle"
        elif vJust == "bottom" or vJust == "bot" or vJust == "b":
            vJust = "bottom"
        else:
            raise KeyError("Justification specifier ({}) not found.".format(vJust))

        widest = 0
        pattern = re.compile(r"^.*$", flags=re.M)
        # Matches any line of text
        for elem in pattern.findall(text):
            if len(elem) > widest:
                widest = len(elem)

        lines = text.split("\n")
        justifiedLines = []

        if width < widest:
            width = widest

        if height < 0:
            height = len(lines)

        for line in lines[:]:
            # line = line.strip()

            if hJust == "left":
                line = "{:<{}}".format(line, width)
            if hJust == "center":
                line = "{:^{}}".format(line, width)
            if hJust == "right":
                line = "{:>{}}".format(line, width)

            justifiedLines.append(line)

        if len(justifiedLines) < height:
            heightDiff = height - len(justifiedLines)

            if vJust == "top":
                justifiedLines.extend([""] * heightDiff)
            if vJust == "middle":
                print("adding {} new lines on top!".format(heightDiff // 2))
                justifiedLines = (
                    [""] * (heightDiff // 2)
                    + justifiedLines
                    + [""] * (heightDiff // 2 + heightDiff % 2)
                )
            if vJust == "bottom":
                justifiedLines = [""] * heightDiff + justifiedLines

        return "\n".join(justifiedLines)

    # ^^^ _justify(...) <Frame private static method> ^^^^^^^^^^^^^^^^^^^^^^

    # ^^^ Private Methods <Frame> ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    #
    # --- Public Methods <Frame> -------------------------------------------

    def render(self, text, **kwargs):

        for key in kwargs.keys():
            if key[0] == "_":
                del kwargs[key]

        return self._apply(text, **kwargs)


# ^^^^ Public Methods <Frame> ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# ^^^^ Frame Class ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# ---- Panel Class -----------------------------------------------------
#
# Notes:
#


class Panel(hierarchy.Hierarchy):
    """A panel of text that can be split into smaller sub-panels."""

    DEFAULT_WIDTH = 79
    DEFAULT_HEIGHT = 24

    # --- Special Methods --------------------------------------------------

    def __init__(
        self,
        name,
        width=DEFAULT_WIDTH,
        height=DEFAULT_HEIGHT,
        padding=0,
        topFrame=True,
        botFrame=True,
        leftFrame=True,
        rightFrame=True,
        parent=None,
        vertical=True,
        dynamic=True,
        from_Frame=None,
    ):

        hierarchy.Hierarchy.__init__(self, name)

        self._width = width
        self._height = height

        self._vertical = vertical
        self._horizontal = not vertical

        self._dynamic = dynamic
        self._static = not dynamic

        self._content = ""
        self._contentLines = 0

        self._padding = padding
        self._topFrame = topFrame
        self._botFrame = botFrame
        self._leftFrame = leftFrame
        self._rightFrame = rightFrame

        if self._daughters:
            names = [daughter.name for daughter in self._daughters]

            self.split(len(self._daughters), names)

    # ^^^ self.__init__(...) <Panel method> ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    def __setitem__(self, key, value):
        if isinstance(key, int):
            self.daughters[key].content = value

        if isinstance(value, str):
            self[key].content = value

        else:
            hierarchy.Hierarchy.__setitem__(self, key, value)

    # ^^^ Special Methods <Panel> ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    #
    # --- Properties <Panel> ----------------------------------------------

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, value):
        self._content = str(value)
        if value:
            self._contentLines = str(value).count("\n") + 1
        else:
            self._contentLines = 0

        self.height = self.height

    @property
    def padding(self):
        """Changing padding will affect the shape of child Panels.
        Padding of -1 is special: it additionally disables all frames."""
        return self._padding

    @padding.setter
    def padding(self, value):
        if value == -1:
            self._topFrame = False
            self._botFrame = False
            self._leftFrame = False
            self._rightFrame = False
            self._padding = 0
        self._padding = value
        # print "TODO: 'seal' the Panel"

    @property
    def topFrame(self):
        """Changing topFrame will affect the shape of child Panels."""
        return self._topFrame

    @topFrame.setter
    def topFrame(self, value):
        self._topFrame = value
        # "TODO: 'seal' the Panel"

    @property
    def botFrame(self):
        """Changing botFrame will affect the shape of child Panels."""
        return self._botFrame

    @botFrame.setter
    def botFrame(self, value):
        self._botFrame = value
        # print "TODO: 'seal' the Panel"

    @property
    def leftFrame(self):
        """Changing leftFrame will affect the shape of child Panels."""
        return self._leftFrame

    @leftFrame.setter
    def leftFrame(self, value):
        self._leftFrame = value
        # print "TODO: 'seal' the Panel"

    @property
    def rightFrame(self):
        """Changing rightFrame will affect the shape of child Panels."""
        return self._rightFrame

    @rightFrame.setter
    def rightFrame(self, value):
        self._rightFrame = value
        # print "TODO: 'seal' the Panel"

    @property
    def horizontal(self):
        """Changing self.horizontal to True automatically adjusts self.vertical.
        self.horizontal and self.vertical can never both be True or both be False.

        Note that changing a Panel's direction will unfreeze all descendants."""
        return self._horizontal

    @horizontal.setter
    def horizontal(self, value):
        if value != self._horizontal:
            self.dynamic = True
            self._horizontal = not self._horizontal
            self._vertical = not self._vertical

    @property
    def vertical(self):
        """Changing self.vertical to True automatically adjusts self.horizontal.
        self.vertical and self.horizontal can never both be True or both be False."""
        return self._vertical

    @vertical.setter
    def vertical(self, value):
        if value != self._vertical:
            self.dynamic = True
            self._vertical = not self._vertical
            self._horizontal = not self._horizontal

    @property
    def static(self):
        """Changing self.static to True automatically adjusts self.dynamic.
        self.static and self.dynamic can never both be True or both be False."""
        return self._static

    @static.setter
    def static(self, value):
        if value:
            self._static = True
            self._dynamic = False
        else:
            self._static = False
            self._dynamic = True

    @property
    def dynamic(self):
        """Changing self.dynamic to True automatically adjusts self.static.
        self.dynamic and self.static can never both be True or both be False."""
        return self._dynamic

    @dynamic.setter
    def dynamic(self, value):
        if value:
            self._dynamic = True
            self._static = False
        else:
            self._dynamic = False
            self._static = True

    @property
    def height(self):
        """Changing the Panel height affects dynamic sisters and daughters.
        Panel height cannot exceed Parent height minus static Sister heighths.
        Panel height cannot be reduced below static Daughter heighths.
        Panel heighths < 0 are treated as though they were 0, although it is
        recommended that unused Panels be deleted with the del statement."""
        return self._height

    # --- @height.setter <Panel property> -----------------------------------------

    @height.setter
    def height(self, value):

        staticSisters = [elem for elem in self.sisters if elem.static]
        dynamicSisters = [elem for elem in self.sisters if elem.dynamic]

        # static sisters cannot readjust their height, so they must be
        # accounted for when calculating the effective canvas size
        sistersHeight = sum([elem._height for elem in staticSisters])

        # The new height cannot exceed the parent's canvas height
        # (which is affected by frames, padding, content and daughters)
        if self._sisters:
            if (
                value
                > self._parent._height
                - self._parent._padding * 2
                - self._parent._topFrame
                - self._parent._botFrame
                - sistersHeight
            ):
                raise PanelError("Child Panels cannot exceed their parent's height.")

        if dynamicSisters:
            dynamicSisters = sorted(dynamicSisters, key=lambda x: x._height)

            biggestHeight = float(dynamicSisters[-1]._height)

            sign = 1 if value >= self._height else -1

            if biggestHeight <= 0:
                if sign > 0:
                    raise PanelError("Too many static sisters.")
                else:
                    increments = [(1, 0, elem.name) for elem in dynamicSisters]

            else:
                increments = [
                    (elem._height // biggestHeight, 0, elem.tname)
                    for elem in dynamicSisters
                ]

            deltaHeight = abs(value - self._height)

            while deltaHeight > 0:
                while not any([count > 1 for (inc, count, tname) in increments]):
                    increments = [
                        (inc, count + inc, tname) for (inc, count, tname) in increments
                    ]

                for (inc, count, tname) in increments:
                    if count >= 1 and deltaWidth > 0:
                        target = self._parent._daughters.index(self[tname])
                        self._parent._daughters[target]._height -= sign
                        count -= 1
                        deltaHeight -= 1

        dynamicDaughters = [elem for elem in self._daughters if elem.dynamic]
        staticDaughters = [elem for elem in self._daughters if elem.static]
        dynamicHeight = (
            self._height
            - self._contentLines
            - sum(elem._contentLines for elem in staticDaughters)
        )

        if dynamicDaughters:
            for daughter in dynamicDaughters:
                daughter.height = dynamicHeight // len(dynamicDaughters)

        self._height = value

    # ^^^ @height.setter(...) ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    #
    # --- @width.getter(...) ----------------------------------------------------

    @property
    def width(self):
        """Changing the Panel width affects dynamic sisters and daughters.
        Panel width cannot exceed Parent width minus static Sister widths.
        Panel width cannot be reduced below static Daughter widths.
        Panel widths < 0 are treated as though they were 0, although it is
        recommended that unused Panels be deleted with the del statement."""
        return self._width

    @width.setter
    def width(self, value):

        if self._parent:
            if self._parent._vertical:
                self._width = (
                    self._parent._width
                    - self._parent._padding * 4
                    - self._parent._leftFrame
                    - self._parent._rightFrame
                )
                return

        staticSisters = [elem for elem in self._sisters if elem.static]
        dynamicSisters = [elem for elem in self._sisters if elem.dynamic]

        sistersWidth = sum([elem._width for elem in staticSisters])

        # The new width cannot exceed the parent's canvas width
        # (which is affected by frames, padding and daughters)
        if self._sisters:
            if (
                value
                > self._parent._width
                - self._parent._padding * 4
                - self._parent._leftFrame
                - self._parent._rightFrame
                - sistersWidth
            ):
                raise PanelError("Child Panels cannot exceed their parent's width.")

        if dynamicSisters:
            dynamicSisters = sorted(dynamicSisters, key=lambda x: x._width)

            biggestWidth = float(dynamicSisters[-1]._width)

            sign = 1 if value >= self._width else -1

            if biggestWidth <= 0:
                if sign > 0:
                    raise PanelError("Too many static sisters.")
                else:
                    increments = [(1, 0, elem.name) for elem in dynamicSisters]

            else:
                increments = [
                    (elem._width / biggestWidth, 0, elem.name)
                    for elem in dynamicSisters
                ]

            deltaWidth = math.abs(value - self._width)

            while deltaWidth > 0:
                while not any([count > 1 for (inc, count, name) in increments]):
                    increments = [
                        (inc, count + inc, name) for (inc, count, name) in increments
                    ]

                for (inc, count, name) in increments:
                    if count >= 1 and deltaWidth > 0:
                        target = self._parent._daughters.index(name)
                        self._parent._daughters[target]._width -= sign
                        count -= 1
                        deltaWidth -= 1

        dynamicDaughters = [elem for elem in self._sisters if elem.dynamic]
        staticDaughters = [elem for elem in self._sisters if elem.static]

        if dynamicDaughters:
            pass

        self._width = value

    # ^^^ @width.setter <Panel> ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    # ^^^ Properties <Panel> ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    #
    # --- Public Methods <Panel> ---------------------------------------------

    def split(self, pieces=2, names=[], widths=[], heights=[]):
        """Split a panel into multiple daughter panels.
        NOTE: Previous daughters are abandoned."""
        self._daughters = []

        for count in range(pieces):
            if names:
                name = names[count]
            else:
                name = "Child #{} of {}".format(count + 1, self.name)
            if self._vertical:
                width = (
                    self._width - self.leftFrame - self.rightFrame - self.padding * 2
                )
                if heights:
                    height = heights[count]
                else:
                    height = (
                        self._height - self.topFrame - self.botFrame - self.padding * 4
                    ) // pieces
            else:
                height = self._height - self.topFrame - self.botFrame - self.padding * 4
                if widths:
                    width = widths[count]
                else:
                    width = (
                        self._width
                        - self.leftFrame
                        - self.rightFrame
                        - self.padding * 4
                    ) // pieces

            print("child width=", width, "and child height=", height)
            self.insert(name, width, height)

    def render(self, *args, **kwargs):
        """Prepare a panel (and all its daughters) for printing."""

        if not args and not kwargs:
            if self.content:

                # canvas = "\n" if self._daughters else ""
                canvas = ""
                canvas += frame(
                    self.content,
                    width=self._width,
                    height=self._contentLines,
                    padding=0,
                    topFrame=False,
                    botFrame=False,
                    leftFrame=False,
                    rightFrame=False,
                )
            else:
                canvas = ""

            if self._horizontal:
                return frame(
                    canvas[:-1]
                    + "\n"
                    + parallelize([elem.render() for elem in self._daughters]),
                    width=self.width,
                    height=self.height,
                    padding=self.padding,
                    topFrame=self.topFrame,
                    botFrame=self.botFrame,
                    leftFrame=self.leftFrame,
                    rightFrame=self.rightFrame,
                )

            elif self._vertical:
                return frame(
                    canvas[:-1]
                    + "\n"
                    + columnize(
                        [elem.render() for elem in self._daughters], frames=False
                    ),
                    width=self.width,
                    height=self.height,
                    padding=self.padding,
                    topFrame=self.topFrame,
                    botFrame=self.botFrame,
                    leftFrame=self.leftFrame,
                    rightFrame=self.rightFrame,
                )
        else:
            return hierarchy.Hierarchy.render(self, *args, **kwargs)


# ^^^ Panel Class ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# --- Convenience Functions -------------------------------------------------

# --- table(...) ------------------------------------------------------------
#
# Known Bugs: Every row after the 1st has an extra new line appended to the end.
#


def table(*args):
    """table(["list", "of", 4, "objects"],["list", "of", "strings"],...)

    Takes lists of strings and returns a single string formatted as a table.

    If there is more than one row/column the following assumptions are made:
    - The first column and first row are assumed to be headers
    - Cells do not span multiple rows or columns

    Example:

    ....


    KNOWN BUGS:
    Every Row after the 1st has an extra new line appeneded to the end."""

    columns = []

    # converts the lists of objets in args to lists of strings
    args = [[str(elem2) for elem2 in elem] for elem in args]

    if len(args) == 1:

        # Find the "tallest" string in the list
        # tallest is the number of lines in the string
        tallest = 0
        for line in args[0]:
            if line_height(line) > tallest:
                tallest = line_height(line)

        buildUp = [frame(args[0][0], height=tallest + 2)]

        for elem in args[0][1:]:
            buildUp += [
                frame(
                    elem + ("\n" + " " * len(longest_line(elem))) * tallest,
                    height=tallest + 2,
                    leftFrame=False,
                )
            ]

        return parallelize(buildUp)

    elif len(args) > 1:

        # longest is the number of cells in the table's longest row
        longest = 0
        for row in args:
            if longest < len(row):
                longest = len(row)

        # all rows should have the same # of cells
        # shorter rows are padded with empty strings
        for row in args:
            if len(row) < longest:
                for count in range(longest - len(row)):
                    row.append("")

        # tallest is a list, with one int element for each row in the table
        # the value of the int is the number of lines in the cell
        tallest = []
        count = 0

        # construct tallest
        for row in args:
            tallest.append(0)
            for line in row:
                if line_height(line) > tallest[count]:
                    tallest[count] = line_height(line)
            count += 1

        # cols is a list of the tables columns
        # the first item of cols is the first table of the column
        cols = [
            [args[elem][count] for elem in range(len(args))] for count in range(longest)
        ]

        # widest is a list with one int element for each column of the table
        # the value of the int is the width of the widest cell in that col
        widest = []
        count = 0

        # construct widest
        for col in cols:
            widest.append(0)
            for line in col:
                if len(longest_line(line)) > widest[count]:
                    widest[count] = len(longest_line(line))

            count += 1

        first_row = [frame(args[0][0], width=widest[0] + 2, height=tallest[0] + 2)]

        for count in range(1, longest):
            first_row += [
                frame(
                    args[0][count] + ("\n" + " " * (widest[count])) * (tallest[0]),
                    height=tallest[0] + 2,
                    leftFrame=False,
                )
            ]

        all_rows = []
        all_rows.append(first_row)
        next_row = []

        # count is the row # and count2 is the column #
        for count in range(1, len(args)):
            next_row = [
                frame(
                    args[count][0],
                    width=widest[0] + 2,
                    height=tallest[count] + 2,
                    topFrame=False,
                )
            ]
            for count2 in range(1, longest):
                next_row += [
                    frame(
                        args[count][count2]
                        + ("\n" + " " * (widest[count2])) * tallest[count],
                        height=tallest[count] + 2,
                        width=widest[count2] + 1,
                        leftFrame=False,
                        topFrame=False,
                    )
                ]
            all_rows.append(next_row)

        return columnize([parallelize(elem) for elem in all_rows], frames=False)

    else:
        raise (IndexError, "table() requires at least one argument")


# ^^^ table(...) ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# --- frame(...) ---------------------------------------------------------
#
# Notes:
#


def frame(
    text,
    width=-1,
    height=-1,
    padding=0,
    background_Char=" ",
    hJust="left",
    vJust="top",
    topFrame=True,
    botFrame=True,
    leftFrame=True,
    rightFrame=True,
):

    """Constrains text to fit within a specified width, then adds frame to text.

    NOTE: padding < 0 turns all frames off
    NOTE: width < 0 sets width to the length of the longest line


    EXAMPLES:

    >>> print(frame("Example Text"))
    +------------+
    |Example Text|
    +------------+

    >>> print(frame(frame("Example Text")))
    +--------------+
    |+------------+|
    ||Example Text||
    |+------------+|
    +--------------+

    >>> print(frame("Extra Padding",20,padding=1))
    +------------------+
    |                  |
    |  Extra Padding   |
    |                  |
    +------------------+

    >>> print(frame('''Text that overflows the width
    ... parameter is placed on the next line.''',20))
    +------------------+
    |Text that         |
    |overflows the     |
    |width             |
    |parameter is      |
    |placed on the next|
    |line.             |
    +------------------+

    >>> print(frame('''If a word (e.g., antidisestablishmentarianism)
    ... exceeds the width, the offending word is truncated.''',20))
    +------------------+
    |If a word (e.g.,  |
    |antidisestablishme|
    |exceeds the width,|
    |the offending word|
    |is truncated.     |
    +------------------+

    >>> print(frame('''The ASCII frames can be easily
    ... removed by setting the padding parameter to -1.''', 20, padding=-1))
    The ASCII frames can
    be easily
    removed by setting
    the padding
    parameter to -1.

    >>> print(frame('''Content can be vertically and horizontally
    ... justified with 'vJust' and 'hJust'.  Allowed options are:
    ...
    ... hJust =
    ... (default) 'left', 'l', or '<'
    ... 'center', 'c', '^'
    ... 'right', ''r', '>'
    ...
    ... vJust =
    ... (default) 'top', 't', or '^'
    ... 'middle', 'm', or 'mid'
    ... 'bottom', 'b', or 'bot'
    ... ''', hJust = 'r'))
    +---------------------------------------------------------+
    |               Content can be vertically and horizontally|
    |justified with 'vJust' and 'hJust'.  Allowed options are:|
    |                                                         |
    |                                                  hJust =|
    |                            (default) 'left', 'l', or '<'|
    |                                       'center', 'c', '^'|
    |                                       'right', ''r', '>'|
    |                                                         |
    |                                                  vJust =|
    |                             (default) 'top', 't', or '^'|
    |                                  'middle', 'm', or 'mid'|
    |                                  'bottom', 'b', or 'bot'|
    |                                                         |
    +---------------------------------------------------------+"""

    _ = background_Char

    text = str(text)

    # Not sure if this is good design, but a negative padding has
    # side effects (removing the frames)
    if padding < 0:
        padding = 0
        topFrame = False
        botFrame = False
        leftFrame = False
        rightFrame = False

    # This handles simple edge cases
    if width == 0 or height == 0:
        return ""

    # Not sure if this is good design, but an empty input string
    # will not reduce the canvas size below a single character's worth
    if text == "":
        text = _

    # if width < 0, adjust width to accomodate the widest line of text
    # plus any padding or framing characters
    if width < 0:
        widest = 0
        for line in text.split("\n"):
            if len(line) > widest:
                widest = len(line)
        width = widest + 4 * padding + leftFrame + rightFrame

    # The canvas does not include the frame or any padding
    canvasWidth = width - padding * 4 - leftFrame - rightFrame

    # trim lines to fit within the width of the canvas
    # NOTE: overflow is moved to the following line(s)
    # NOTE: line breakage occurs only at word boundaries
    text = constrain(text, canvasWidth)

    # The minimum # of lines able to contain the entire framed text
    minimumHeight = 1 + text.count("\n") + topFrame + botFrame + padding * 2

    if height < 0:
        height = minimumHeight

    canvasHeight = height - topFrame - botFrame - padding * 2

    # if `text` was empty, fill up the canvas with background
    if text == _:
        text = _ + (_ * (canvasWidth) + "\n") * (canvasHeight)
        text = text[:-1]

    text = justify(text, canvasWidth, canvasHeight, hJust, vJust)

    lines = text.split("\n")

    lines = [(elem if elem else " " * canvasWidth) for elem in lines]

    # this whole mess of code is responsible for handling
    # the edge case of a small height argument...
    # ... there has to be a better way...
    if minimumHeight > height:
        dud = (
            ("+" if leftFrame else "")
            + "-" * (width - leftFrame - rightFrame)
            + ("+" if rightFrame else "")
        )

        pdud = (
            ("|" if leftFrame else "")
            + (_ + _) * padding
            + _ * (canvasWidth)
            + (_ + _) * padding
            + ("|" if rightFrame else "")
        )

        diff = height

        if height == 1:
            if topFrame:
                return dud
            else:
                dud = (
                    ("|" if leftFrame else "")
                    + (_ + _) * padding
                    + lines[0][: max(0, canvasWidth)]
                    + (_ + _) * padding
                    + ("|" if rightFrame else "")
                )
                dud = dud[:width]
                return dud

        top = [dud] if topFrame else []
        diff -= topFrame
        bot = [dud] if botFrame else []
        diff -= botFrame

        n = 0
        while n < padding and diff > 0:
            top.append(pdud)
            n += 1
            diff -= 1

        top = [elem[:width] for elem in top]

        mid = []

        n = 0
        while n < padding and diff > 0:
            bot.insert(0, pdud)
            n += 1
            diff -= 1

        bot = [elem[:width] for elem in bot]

        count = 0
        while count < diff:
            mid.append(
                ("|" if leftFrame else "")
                + (_ + _) * padding
                + lines[count][: max(0, canvasWidth)]
                + (_ + _) * padding
                + ("|" if rightFrame else "")
            )
            mid[-1] = mid[-1][:width]
            count += 1

        if rightFrame:
            top = [elem[:-1] + "|" for elem in top]
            mid = [elem[:-1] + "|" for elem in mid]
            bot = [elem[:-1] + "|" for elem in bot]
            if topFrame:
                top[0] = top[0][:-1] + "+"
            if botFrame:
                bot[-1] = bot[-1][:-1] + "+"

        return "\n".join(top + mid + bot)

    # this handles the other stupid edge case...
    # where is the elegant solution?
    if width == 1:
        dud = []
        if leftFrame:
            if topFrame:
                dud.append("+")
            if botFrame:
                dud.append("+")
            for n in range(height - leftFrame - rightFrame):
                dud.insert(1, "|")
            return "\n".join(dud)
        elif padding > 0:
            if topFrame:
                dud.append("-")
            if botFrame:
                dud.append("-")
            for n in range(height - leftFrame - rightFrame):
                dud.insert(1, _)
            return "\n".join(dud)
        else:
            if topFrame:
                dud.append("-")
            if botFrame:
                dud.append("-")
            for n in range(height - leftFrame - rightFrame):
                dud.insert(n + leftFrame + rightFrame, lines[n][0])
            return "\n".join(dud)

    lines = [line[:canvasWidth] for line in lines]

    # Add Top and Bottom Padding
    for n in range(padding):
        lines.insert(0, _ * (canvasWidth))
        lines.append(_ * (canvasWidth))

    # Add Padding and Side Frames
    lines = [
        ("|" if leftFrame else "")
        + (_ + _) * padding
        + line
        + (_ + _) * padding
        + ("|" if rightFrame else "")
        for line in lines
    ]

    if topFrame:
        lines.insert(0, "+" + "-" * (width - 2) + "+")
        lines[0] = lines[0][:width]

    if botFrame:
        lines.append("+" + "-" * (width - 2) + "+")
        lines[-1] = lines[-1][:width]

    return "\n".join(lines)


# ^^^ frame(...) ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# ^^^ Convenience Functions ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# --- Helper Functions -------------------------------------------------
#
# --- constrain(...) ---------------------------------------------------
#
# Notes:
#


def constrain(text, width):
    """trim lines to a maximum of width characters"""

    # if all lines have fewer characters than width, do nothing
    if all([len(elem) <= width for elem in text.split("\n")]):
        return text

    longest = 0

    # matches all trailing new lines, if any
    trailing = re.search(r"\n*$", text)

    # hold the trailing new lines; we'll put them back at the end
    last = text[slice(*trailing.span())]

    # `text` is what's left after removing trailing new lines
    text = text[: trailing.span()[0]]

    # Matches any word (contiguous punctuation is considered part of the word)
    word_pattern = re.compile(r"\b\S+\b")

    words = []

    for elem in word_pattern.findall(text):
        words.append(elem)

        if len(elem) > longest:
            longest = len(elem)

    # Nested RE:
    # For every line with pipes pipes:
    #   For every space:
    #       Replace it with a temporary character
    #
    # (This prevents whitespace inside a frame from breaking
    # text = re.sub(temp, lambda m: re.sub(r" ", "`",m.group(0)), text, flags=re.M)

    # Matches the maximum number of characters terminated by a space
    # that will fit in width
    # pattern = r"(.{,"+str(width)+r"})(\s|(\w--?\w)|$)"

    # text = re.sub(pattern,
    #         lambda m: m.group(0) if re.match(r"^\+-*\+^", m.group(0)) else (m.group(1)+"\n" if len(m.group(2)) < 2 else m.group(1)+m.group(2)[:-1]+"\n"+m.group(2)[-1:]), text)

    new_line = words[0]
    words.remove(words[0])

    while len(new_line) < width:
        new_line += " " + words[0]
        words.remove(words[0])

    new_text = new_line

    while words:
        new_line = words[0]
        words.remove(words[0])

        while len(new_line) < width:
            new_line += " " + words[0]
            words.remove(words[0])

        new_text += "\n" + new_line

    # Revert temporary characters to spaces
    # text = re.sub("`", " ", text)

    # if text[-1]=='\n':
    #     text = text[:-1]

    text = new_text + last
    return text


# ^^^ constrain(...) ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# --- justify(...) ---------------------------------------------------------
#
# Notes:
#


def justify(text, width=-1, height=-1, hJust="left", vJust="top"):
    """Justifies a paragraph of text.  Guaranteed not to lose any text."""

    hJust = hJust.lower()
    vJust = vJust.lower()

    if hJust == "left" or hJust == "<" or hJust == "l":
        hJust = "left"
    elif hJust == "center" or hJust == "^" or hJust == "c":
        hJust = "center"
    elif hJust == "right" or hJust == ">" or hJust == "r":
        hJust = "right"
    else:
        raise KeyError("Justification specifier ({}) not found.".format(hJust))

    if vJust == "top" or vJust == "^" or vJust == "t":
        vJust = "top"
    elif vJust == "middle" or vJust == "mid" or vJust == "m":
        vJust = "middle"
    elif vJust == "bottom" or vJust == "bot" or vJust == "b":
        vJust = "bottom"
    else:
        raise KeyError("Justification specifier ({}) not found.".format(vJust))

    widest = 0
    pattern = re.compile(r"^.*$", flags=re.M)
    # Matches any line of text
    for elem in pattern.findall(text):
        if len(elem) > widest:
            widest = len(elem)

    lines = text.split("\n")
    justifiedLines = []

    if width < widest:
        width = widest

    if height < 0:
        height = len(lines)

    for line in lines[:]:
        # line = line.strip()

        if hJust == "left":
            line = "{:<{}}".format(line, width)
        if hJust == "center":
            line = "{:^{}}".format(line, width)
        if hJust == "right":
            line = "{:>{}}".format(line, width)

        justifiedLines.append(line)

    if len(justifiedLines) < height:
        heightDiff = height - len(justifiedLines)

        if vJust == "top":
            justifiedLines.extend([""] * int(heightDiff))
        if vJust == "middle":
            print("adding {} new lines on top!".format(heightDiff // 2))
            justifiedLines = (
                [""] * (heightDiff // 2)
                + justifiedLines
                + [""] * (heightDiff // 2 + heightDiff % 2)
            )
        if vJust == "bottom":
            justifiedLines = [""] * heightDiff + justifiedLines

    return "\n".join(justifiedLines)


# ^^^ justify(...) ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# --- columnize(...) -----------------------------------------------------
#
# Notes:
#


def columnize(texts=[], width=-1, height=-1, padding=0, frames=True):
    """columnize(["string1","string2",...],width=-1,padding=0)

    Frames all text into a standard column width and padding

    Example:

    >>> print(columnize(["Example 1", "Example 2"]))
    +---------+
    |Example 1|
    +---------+
    |Example 2|
    +---------+"""
    # If no strings were passed, return a blank line of default width
    if not texts:
        return " " * width

    if padding < -1:
        padding = 0

    if height > 0:
        height = height - (len(texts) + 1) * frames
        height = height / len(texts)
        height = height + 2 * frames

    if width < 0:
        biggest = 0
        for elem in texts:
            if len(longest_line(elem)) > biggest:
                biggest = len(longest_line(elem))
        width = biggest + 2 * frames + 4 * min(0, padding)
    column = frame(
        texts[0],
        width=width,
        height=height,
        padding=padding,
        topFrame=frames,
        botFrame=frames,
        leftFrame=frames,
        rightFrame=frames,
    )

    for num in range(1, len(texts)):
        column = (
            column
            + "\n"
            + frame(
                texts[num],
                width=width,
                height=height,
                padding=padding,
                topFrame=False,
                botFrame=frames,
                leftFrame=frames,
                rightFrame=frames,
            )
        )
    return column


# ^^^ columnize(...) ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# --- parallelize(...) --------------------------------------------------
#
# Notes:
#


def parallelize(texts=[], widths=[-1]):
    r"""Each paragraph of text in `texts` is joined side-by-side.
    If `widths` has one element, that width is imposed on all paragraphs.
    Otherwise, `widths` must have exactly the same length as `texts` and
    the Nth element of `widths` is imposed on the Nth element of `texts`.
    Whenever an element of `widths` equals -1, the length of the longest
    line in the corresponding paragraph is used instead.

    EXAMPLES:

    >>> print(parallelize(['<Example 1>\nA.\nB.','<Example 2>\n1.\n2.\n3.']))
    <Example 1><Example 2>
    A.         1.
    B.         2.
               3.

    >>> print(parallelize(['If you supply the widths argument',
    ...                    'each text stream in the list',
    ...                    'will be laid down in parallel columns',
    ...                    'each of the specified width.'], widths=[14]))
    If you supply each text     will be laid  each of the
    the widths    stream in the down in       specified
    argument      list          parallel      width.
                                columns"""

    # An empty list argument returns an empty string
    # I'm not sure if this is good design or not
    if not texts:
        return ""

    args = texts
    tallest = []
    lengths = []
    copy = []
    pattern = re.compile(r"^.*$", flags=re.M)
    # Matches any line of text

    if len(widths) == len(texts):
        pass
    elif len(widths) == 1:
        widths = widths * len(texts)

    args = [
        (frame(elem, width, padding=-1) if width != -1 else elem)
        for elem, width in zip(args, widths)
    ]

    # Find the tallest string (most lines) -> tallest
    # Find the longest line of each string  -> lengths

    for text in args:
        if text.count("\n") > tallest.count("\n"):
            tallest = text
        textSize = 0
        for line in text.split("\n"):
            if len(line) > textSize:
                textSize = len(line)
        lengths.append(textSize)

    # Pad strings with blank lines until they are equally tall
    # Width of blank lines is equal to the string's widest line
    for num in range(len(args)):
        copy.append(
            args[num]
            + ("\n" + " " * (lengths[num]))
            * (tallest.count("\n") - args[num].count("\n"))
        )

    copy = [elem.split("\n") for elem in copy]

    # copy[n][m] is an n-by-m matrix
    # n chooses a string
    # m chooses a line-number

    # Print the 1st line of every string in tandem
    # Then print the 2nd line of every string in tandem
    # Etc..

    screen = ""

    for num in range(len(copy[0])):
        output = ""
        for num2 in range(len(copy)):
            output += copy[num2][num] + " " * (lengths[num2] - len(copy[num2][num]))

        # width < 0 means do not artificially restrict the line width
        screen += output + "\n"

    # Remove the last newline
    screen = screen[:-1]

    return screen


# ^^^ parallelize(...) ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# --- longest_line(...) --------------------------------------------------
#
# Notes:
#


def longest_line(multi_line_string):
    """longest_line("A\nMulti-line\nString")

    Returns the longest line of a multi-line string."""

    temp = multi_line_string.split("\n")
    longest = 0
    final_string = ""

    for line in temp:
        if len(line) > longest:
            longest = len(line)
            final_string = line

    return final_string


def line_height(multi_line_string):
    """line_height("A\nMulti-line\nString")

    Returns the height (number of lines) in a multi-line string."""

    return len(multi_line_string.split("\n"))


def main():
    import unittest, doctest

    # p= Panel(['r',['t'],['b']])

    args = sys.argv[1:]
    print(frame(" ".join((str(arg) for arg in args))))
    # doctest.testmod()
    # unittest.main()

    # print(frame("hello world"))


# p = Panel("root")
# p.content = "??"
# p.split()

if __name__ == "__main__":
    main()
