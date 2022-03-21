import glob

from pathlib import Path

import toml, rich, sys


_EXCLUSIONS = ["__init__", "__main__"]


def main():

    tom = toml.load(Path(__file__).parent / "pyproject.toml")
    version = tom["tool"]["poetry"]["version"]
    package_name = tom["tool"]["poetry"]["name"]

    rich.print(
        f"[red]Rob's Utility Scripts[/red]\n[green]Version: {version}[/green]\n\nAvailable scripts (pass -h for CLI usage):"
    )

    scripts = []
    # breakpoint()
    for elem in glob.glob(f"{Path(__file__).parent}/*.py"):
        if Path(elem).stem not in _EXCLUSIONS:
            scripts.append("rob." + Path(elem).stem)

    print("\n".join(elem for elem in scripts))
    sys.stdout = None
    sys.stderr = None
    # print(
    #     "\n".join(
    #         [
    #             "rob." + Path(elem).stem
    #             for elem in glob.glob(f"{Path(__file__).parent}/*.py")
    #             if Path(elem).stem not in _EXCLUSIONS
    #         ]
    #     )
    # )


if __name__ == "__main__":
    main()
