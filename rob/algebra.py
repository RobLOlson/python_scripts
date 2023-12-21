import datetime
import decimal
import itertools
import math
import operator
import pathlib
import random

import appdirs
import toml
import typer

_DEBUG = False

_THIS_FILE = pathlib.Path(__file__)

# LATEX_FILE = pathlib.Path("config/latex_templates.toml")
_LATEX_FILE = _THIS_FILE / "config" / "algebra" / "latex_templates.toml"
_LATEX_FILE.parent.mkdir(exist_ok=True)
_LATEX_FILE.touch()
_LATEX_TEMPLATES = toml.loads(open(_LATEX_FILE.absolute(), "r").read())

_SAVE_FILE = (
    pathlib.Path(appdirs.user_data_dir()) / "robolson" / "algebra" / "config.toml"
)
if not _SAVE_FILE.exists():
    # NEW_SAVE_FILE = pathlib.Path("data/algebra/save.toml")
    NEW_SAVE_FILE = _THIS_FILE / "config" / "algebra" / "config.toml"
    _SAVE_DATA = toml.loads(open(NEW_SAVE_FILE.absolute(), "r").read())
else:
    _SAVE_DATA = toml.loads(open(_SAVE_FILE.absolute(), "r").read())

_WEEKDAYS = _SAVE_DATA["constants"]["weekdays"]
_MONTHS = _SAVE_DATA["constants"]["months"]
_VARIABLES = _SAVE_DATA["constants"]["variables"]

_start = datetime.datetime.today()
_days = [_start + datetime.timedelta(days=i) for i in range(30)]
_DATES = [
    f"{_WEEKDAYS[day.weekday()]} {_MONTHS[day.month]} {day.day}, {day.year}"
    for day in _days
]


def generate_simple_x_expression(rarity: int = 1000) -> tuple[str, str]:
    """Generate an expression in one variable where coefficients and exponents are all integers."""
    difficulty = int(3 - math.log(rarity, 10))
    term_count = random.randint(2, 2 + difficulty)
    # variable = random.choice(["a", "b", "c", "x", "y", "m", "n"])
    variable = random.choice(_VARIABLES)

    problem = "Simplify the following expression."
    terms = []
    for term in range(term_count):
        xs = []
        for i in range(random.randint(1, 3)):
            if random.randint(0, 1):
                xs.append(variable)
            else:
                xs.append(f"{random.randint(2,9)}{variable}")

        if xs:
            x_part = " \\cdot ".join(xs)
            terms.append(x_part)

    expression = f" {'+' if random.randint(0,1) else '-'} ".join(terms)

    return (
        rf"{problem} \\ \\ \({expression}\) \\ \\ \\ \\ \\ \\ \\ \\",
        "Easy to check.",
    )


def generate_expression_evaluation(rarity: int = 1000) -> tuple[str, str]:
    """Generate an expression in one variable where coefficients and exponents are all integers."""

    term_count = random.randint(2, 4)
    # variable = random.choice(["a", "b", "c", "x", "y", "m", "n"])
    variable = random.choice(_VARIABLES)
    constant = random.randint(1, 9)
    solution_terms = []
    factors = []

    problem = f"Evaluate the following expression with \\({variable}\\) = {constant}"
    terms = []
    signs = []
    for term in range(term_count):
        exponent = random.randint(1, 3)
        coefs = random.sample(
            range(1, 10), exponent, counts=[10, 1, 1, 1, 1, 1, 1, 1, 1]
        )

        sign = random.choice([1, -1])
        if not term:
            sign = 1

        solution = 1
        for coef in coefs:
            solution *= coef * constant * sign

        terms.append("\\cdot ".join(f"{coefs[i]}{variable}" for i in range(exponent)))
        solution_terms.append(solution)
        signs.append(sign)

    solution = 0
    for term in solution_terms:
        solution += term

    expression = terms[0]
    for i, term in enumerate(terms[1:]):
        if signs[i + 1] == -1:
            expression += f" - {term}"
        else:
            expression += f" + {term}"

    return (
        rf"{problem} \\ \\ \({expression}\) \\ \\ \\ \\ \\ \\ \\ \\",
        rf"\({list(itertools.accumulate(solution_terms, operator.add))[-1]}\)",
    )


def generate_simple_x_equation(rarity: int = 1000) -> tuple[str, str]:
    # variable = random.choice(["a", "b", "c", "x", "y", "m", "n"])
    variable = random.choice(_VARIABLES)

    # factor1 = random.randint(2, 7)
    # factor2 = random.randint(2, 7)

    dist_coef = random.randint(2, 3)  # distribution coef i.e.,the 2 in '2(x+1)'
    dist_offset = random.randint(1, 9)  # distribution offset i.e., the 1 in '2(x+1)'

    left_c = 0
    right_c = random.randint(-9, 9)
    delta_c = random.randint(-9, 9)
    left_c += delta_c
    right_c += delta_c + dist_coef + dist_offset

    left_x = 1
    right_x = 0
    delta_x = random.randint(-3, 3)
    left_x += delta_x
    right_x += delta_x

    if left_x:
        left_x = f"{dist_coef}({left_x}{variable}+{dist_offset})"
    else:
        left_x = ""

    if right_x:
        right_x = f"{right_x*dist_coef}{variable}"
    else:
        right_x = ""

    left = random.sample([left_x, left_c], 2)
    right = random.sample([right_x, right_c], 2)

    left = [elem for elem in left if elem]
    right = [elem for elem in right if elem]

    left = " + ".join(str(term) for term in left)
    right = " + ".join(str(term) for term in right)

    problem = f"Solve the following equation for \\({variable}\\)"

    if random.randint(0, 1):
        expression = f"{left} = {right}"
    else:
        expression = f"{right} = {left}"

    return (
        rf"{problem} \\ \\ \({expression}\) \\ \\ \\ \\ \\ \\ \\",
        "Solution here.",
    )


def random_decimal(n="0.05"):
    """Return a fractional decimal rounded to the nearest 'n'"""
    target = decimal.Decimal(n) * 100
    return decimal.Decimal(
        target * round(random.randint(1, 100) / target)
    ) / decimal.Decimal(100)


def generate_decimal_x_equation(rarity: int = 1000) -> tuple[str, str]:
    variable = random.choice(["a", "b", "c", "x", "y", "m", "n"])

    left_c = decimal.Decimal(0)
    right_c = decimal.Decimal(random.randint(-9, 9)) + random.randint(
        0, 3
    ) * random_decimal("0.25")
    delta_c = decimal.Decimal(random.randint(-9, 9)) + random.randint(
        0, 3
    ) * random_decimal("0.25")
    left_c += delta_c
    right_c += delta_c

    left_x = random.randint(1, 4) * decimal.Decimal("0.25")
    right_x = decimal.Decimal(0)
    delta_x = decimal.Decimal(random.randint(-3, 3))
    left_x += delta_x
    right_x += delta_x
    left_x = f"{left_x}{variable}"
    right_x = f"{right_x}{variable}"

    left = random.sample([left_x, left_c], 2)
    right = random.sample([right_x, right_c], 2)

    left = f" + ".join(str(term) for term in left)
    right = " + ".join(str(term) for term in right)

    problem = f"Solve the following equation for {variable}"

    if random.randint(0, 1):
        expression = f"{left} = {right}"
    else:
        expression = f"{right} = {left}"

    return (
        rf"{problem} \\ \\ \({expression}\) \\ \\ \\ \\ \\ \\ \\ \\",
        "Solution here.",
    )


def generate_variable_isolation(rarity: int = 1000) -> tuple[str, str]:
    variable = random.choice(["x"])
    unknown = random.choice(["y"])

    term_count = random.randint(1, 3)
    terms = [
        f"{random.choice([-1,-2,-3,1,2,3])}x",
        f"{random.choice([-1,-2,-3,1,2,3])}y",
    ]

    for term in range(term_count):
        choice = random.choice(["variable", "unknown", "constant"])
        match choice:
            case "variable":
                terms.append(f"{random.choice([-1,-2,-3,1,2,3])}x")
            case "unknown":
                terms.append(f"{random.choice([-1,-2,-3,1,2,3])}y")
            case "constant":
                terms.append(f"{random.choice([-1,-2,-3,1,2,3])}")

    left = []
    right = []

    while terms:
        if len(terms) == 1:
            if not left:
                left.append(terms[0])
                del terms[0]
                continue

            if not right:
                right.append(terms[0])
                del terms[0]
                continue

        if random.randint(0, 1):
            left.append(terms[0])
        else:
            right.append(terms[0])
        del terms[0]

    left = " + ".join(f"{term}" for term in left)
    right = " + ".join(f"{term}" for term in right)
    problem = f"Isolate the variable y.  Find the x-intercept and the y-intercept."

    expression = f"{left} = {right}"

    return (
        rf"{problem} \\ \\ \({expression}\) \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\",
        "Solution here.",
    )


WEIGHTS = []
PROBLEM_GENERATORS = [e for e in locals() if "generate" in e]
for generator in PROBLEM_GENERATORS:
    if generator not in _SAVE_DATA["weights"].keys():
        _SAVE_DATA["weights"][generator] = 1000

    WEIGHTS.append(1 + _SAVE_DATA["weights"][generator])

    # if _SAVE_DATA["weights"][generator]:
    #     WEIGHTS.append(_SAVE_DATA["weights"][generator])
    # else:
    #     WEIGHTS.append(1)

for generator in list(_SAVE_DATA["weights"].keys()):
    if generator not in globals().keys():
        del _SAVE_DATA["weights"][generator]

_SAVE_DATA["constants"]["weekdays"] = _WEEKDAYS
_SAVE_DATA["constants"]["months"] = _MONTHS
_SAVE_DATA["constants"]["variables"] = _VARIABLES

toml.dump(o=_SAVE_DATA, f=open(SAVE_FILE.absolute(), "w"))


def render_latex(page_count: int = 1, problem_count: int = 4) -> str:
    """Return a string coding for {page_count} pages of LaTeX algebra problems."""

    pages = []
    solutions = []

    doc_header = _LATEX_TEMPLATES["doc_header"]

    for i in range(page_count):
        solution = rf"{_DATES[i]}\\"
        page_header = _LATEX_TEMPLATES["page_header"]
        parts = page_header.split("INSERT_DATE_HERE")
        page_header = _DATES[i].join(parts)

        problems = ""

        generators = random.sample(PROBLEM_GENERATORS, k=problem_count, counts=WEIGHTS)

        for k, generator in enumerate(generators):
            if k % 3 == 0 and k != 0:
                problems += r"\newpage"

            # call candidate generator function
            candidate = globals()[generator](rarity=WEIGHTS[k])
            _SAVE_DATA["weights"][generator] = int(
                _SAVE_DATA["weights"][generator] * 0.9
            )
            solution += rf"{k+1}: {candidate[1]}\;\;"
            problem = rf"\item {candidate[0]}"
            problems += problem

        page_footer = r"\end{enumerate}"
        # solution += r"\\"
        solutions.append(solution)
        pages.append(page_header + problems + page_footer)

    doc_footer = r"\end{document}"

    return (
        doc_header
        + r"\newpage".join(pages)
        + r"\newpage "
        + r"\\".join(solutions)
        + doc_footer
    )


def main():
    fp = open("Algebra.tex", "w")
    fp.write(render_latex(page_count=7))
    fp.close()

    if not _DEBUG:
        toml.dump(o=_SAVE_DATA, f=open(_SAVE_FILE.absolute(), "w"))


if __name__ == "__main__":
    main()
