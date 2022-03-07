import glob

from pathlib import Path

breakpoint()

_EXCLUSIONS = ["__init__"]


print("Available scripts (pass -h for CLI usage):")
print(
    "\n".join(
        [
            Path(elem).stem
            for elem in glob.glob("rob/*.py")
            if Path(elem).stem not in _EXCLUSIONS
        ]
    )
)
