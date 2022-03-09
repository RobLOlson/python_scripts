import glob

from pathlib import Path

import toml, rich


_EXCLUSIONS = ["__init__"]

tom = toml.load(Path(__file__).parent / "pyproject.toml")
version = tom["tool"]["poetry"]["version"]
package_name = tom["tool"]["poetry"]["name"]

rich.print(
    f"[red]Rob's Utility Scripts[/red]\n[green]Version: {version}[/green]\n\nAvailable scripts (pass -h for CLI usage):"
)
print(
    "\n".join(
        [
            Path(elem).stem
            for elem in glob.glob(f"{Path(__file__).parent}/*.py")
            if Path(elem).stem not in _EXCLUSIONS
        ]
    )
)
