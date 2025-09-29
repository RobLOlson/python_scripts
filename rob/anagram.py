import itertools
import pathlib
import re

import typer

from .utilities import cli

_THIS_FILE = pathlib.Path(__file__)
fp = open(file=_THIS_FILE.parent / "data" / "word_list.txt")
_WORDS = fp.readlines()
_WORDS = "".join(_WORDS)
fp.close()

app = typer.Typer()


# @app.command()
@cli.cli()  # pyright: ignore
def anagram(word: str, wilds: int = 0) -> list[str]:
    # def anagram(word: str, wilds: int = typer.Argument(default=0)) -> list[str]:
    """Return all English anagrams of the input word."""

    letters = list(word)
    n = len(word)

    perms = set(itertools.permutations(letters + wilds * ["[a-z]"], n + wilds))

    perms = r"\b|\b".join("".join(elem) for elem in perms)
    perms = rf"\b{perms}\b"
    patt_1 = re.compile(perms)

    result = set(patt_1.findall(_WORDS))

    print("\n".join(elem for elem in result))

    return list(result)


if __name__ == "__main__":
    # app()
    cli.main()
    # main()
