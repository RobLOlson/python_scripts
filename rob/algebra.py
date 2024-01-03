import datetime
import decimal
import itertools
import math
import operator
import pathlib
import random

import appdirs
import survey
import toml
import typer

app = typer.Typer()
list_app = typer.Typer()
app.add_typer(list_app, name="list")

_DEBUG = False

_THIS_FILE = pathlib.Path(__file__)

# LATEX_FILE = pathlib.Path("config/latex_templates.toml")
_LATEX_FILE = _THIS_FILE.parent / "config" / "algebra" / "latex_templates.toml"
_LATEX_FILE.parent.mkdir(exist_ok=True)
_LATEX_FILE.touch()
_LATEX_TEMPLATES = toml.loads(open(_LATEX_FILE.absolute(), "r").read())

_SAVE_FILE = (
    pathlib.Path(appdirs.user_data_dir()) / "robolson" / "algebra" / "config.toml"
)

if not _SAVE_FILE.exists():
    # NEW_SAVE_FILE = pathlib.Path("data/algebra/save.toml")
    NEW_SAVE_FILE = _THIS_FILE.parent / "config" / "algebra" / "config.toml"
    _SAVE_DATA = toml.loads(open(NEW_SAVE_FILE.absolute(), "r").read())
    _SAVE_FILE.parent.mkdir(exist_ok=True)
    _SAVE_FILE.touch()
    toml.dump(o=_SAVE_DATA, f=open(_SAVE_FILE.name, "w"))

else:
    _SAVE_DATA = toml.loads(open(_SAVE_FILE.absolute(), "r").read())

_WEEKDAYS = _SAVE_DATA["constants"]["weekdays"]
_MONTHS = _SAVE_DATA["constants"]["months"]
_VARIABLES = _SAVE_DATA["constants"]["variables"]

_START = datetime.datetime.today()
_days = [_START + datetime.timedelta(days=i) for i in range(30)]
_DATES = [
    f"{_WEEKDAYS[day.weekday()]} {_MONTHS[day.month]} {day.day}, {day.year}"
    for day in _days
]

# To write a new algebra problem generator you must:
# * begin the function name with 'generate'
# * return a 2-tuple of strings ('TeX problem', 'answer')
# * the last line of the doc string should describe or name the problem type


def generate_simple_x_expression(freq_weight: int = 1000) -> tuple[str, str]:
    """Generate an expression in one variable where coefficients and exponents are all integers.
    Problem Description:
    Simplifying Expressions"""

    difficulty = int(3 - math.log(freq_weight, 10))

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


def generate_expression_evaluation(freq_weight: int = 1000) -> tuple[str, str]:
    """Generate an expression in one variable where coefficients and exponents are all integers.
    Problem Description:
    Evaluating Expressions"""

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


def generate_simple_x_equation(freq_weight: int = 1000) -> tuple[str, str]:
    """Generate a single variable equation.
    Problem Description:
    Solving Equations with One Variable"""

    variable = random.choice(_VARIABLES)

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


def generate_decimal_x_equation(freq_weight: int = 1000) -> tuple[str, str]:
    """Generate an equation with decimal coefficients.
    Problem Description:
    Solving Equations with Decimal Coefficients"""

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


def generate_variable_isolation(freq_weight: int = 1000) -> tuple[str, str]:
    """Generate a linear equation with 2 variables.
    Problem Description:
    Isolating Variables in a Linear Equation"""

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


@list_app.command("weights")
def print_weights() -> None:
    """List the frequency weights for each problem type."""

    for problem in _PROBLEM_GENERATORS:
        statement = globals()[problem].__doc__.split("\n")[-1]
        print(f"{statement}: {_SAVE_DATA['weights'][problem]}")


@app.command("render")
def render_latex(
    assignment_count: int = 1, problem_count: int = 4, debug: bool = False
) -> None:
    """Return a string coding for {assignment_count} pages of LaTeX algebra problems."""
    pages = []
    solutions = []

    doc_header = _LATEX_TEMPLATES["doc_header"]

    for i in range(assignment_count):
        solution = rf"{_DATES[i]}\\"
        page_header = _LATEX_TEMPLATES["page_header"]
        parts = page_header.split("INSERT_DATE_HERE")
        page_header = _DATES[i].join(parts)

        problems = ""
        generators = random.sample(_PROBLEM_GENERATORS, k=problem_count, counts=WEIGHTS)

        for k, generator in enumerate(generators):
            if k % 3 == 0 and k != 0:
                problems += r"\newpage"

            # call candidate generator function
            candidate = globals()[generator](freq_weight=WEIGHTS[k])
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

    document = (
        doc_header
        + r"\newpage".join(pages)
        + r"\newpage "
        + r"\\".join(solutions)
        + doc_footer
    )

    document_name = f"Algebra Homework {_MONTHS[datetime.datetime.now().month]} {datetime.datetime.now().day} {datetime.datetime.now().year}.tex"

    print(f"Writing LaTeX document to '{document_name}")

    fp = open(document_name, "w")
    fp.write(document)
    fp.close()

    if not debug:
        toml.dump(o=_SAVE_DATA, f=open(_SAVE_FILE.absolute(), "w"))


@app.command("reset")
def reset_weights(debug: bool = True):
    """Reset problem frequency rates to default."""

    # weights: dict[str, int] = _SAVE_DATA["weights"]
    for key in _SAVE_DATA["weights"].keys():
        _SAVE_DATA["weights"][key] = 1000

    if not debug:
        toml.dump(o=_SAVE_DATA, f=open(_SAVE_FILE.absolute(), "w"))
        print("Frequency weights reset to default (1000).")
    else:
        print("Invoke with --no-debug to save changes.")
    exit(0)


@app.command("config")
def configure_problem_set():
    """Configures the frequency rates of problems."""

    # name_to_description = {
    #     name: globals()[name].__doc__.split("\n")[-1].strip()
    #     for name in _PROBLEM_GENERATORS
    # }
    # description_to_name = {
    #     globals()[name].__doc__.split("\n")[-1].strip(): name
    #     for name in _PROBLEM_GENERATORS
    # }

    form = {
        _NAME_TO_DESCRIPTION[problem_type]: survey.widgets.Count(
            value=_SAVE_DATA["weights"][problem_type]
        )
        for problem_type in _PROBLEM_GENERATORS
    }

    data = survey.routines.form(
        "Frequency Weights (higher -> more frequent): ", form=form
    )

    if not data:
        return

    data = {_DESCRIPTION_TO_NAME[desc]: data[desc] for desc in data.keys()}
    _SAVE_DATA["weights"] = data
    toml.dump(o=_SAVE_DATA, f=open(_SAVE_FILE.absolute(), "w"))
    print(f"\nNew weights saved to {_SAVE_FILE.absolute()}")


@app.callback(invoke_without_command=True)
def default(ctx: typer.Context, debug: bool = False):
    """Invoke the module to create algebra problems in LaTeX."""
    if ctx.invoked_subcommand:
        return

    descriptions = [description for description in _DESCRIPTION_TO_NAME.keys()]

    problem_types = survey.routines.basket(
        "Select problem types to include.", options=descriptions
    )

    start_date = survey.routines.datetime(
        "Select assignment date: ",
        attrs=("month", "day", "year"),
    )
    assignment_count = survey.routines.numeric(
        "How many algebra assignments to generate? ", decimal=False, value=5
    )
    problem_count = survey.routines.numeric(
        "How many problems per assignment? ", decimal=False, value=4
    )
    start = datetime.datetime.today()
    days = [start + datetime.timedelta(days=i) for i in range(30)]

    global _DATES
    _DATES = [
        f"{_WEEKDAYS[day.weekday()]} {_MONTHS[day.month]} {day.day}, {day.year}"
        for day in days
    ]

    render_latex(
        assignment_count=assignment_count, problem_count=problem_count, debug=debug
    )


@list_app.callback(invoke_without_command=True)
def list_default(ctx: typer.Context):
    """List problem types, frequency weights, etc."""
    if ctx.invoked_subcommand:
        return

    print("NO SUBCOMMAND")


def main():
    app()


WEIGHTS = []
_PROBLEM_GENERATORS = [e for e in locals() if "generate" in e]
for generator in _PROBLEM_GENERATORS:
    if generator not in _SAVE_DATA["weights"].keys():
        _SAVE_DATA["weights"][generator] = 1000

    WEIGHTS.append(1 + _SAVE_DATA["weights"][generator])

# mapping of problem function name to problem description
_NAME_TO_DESCRIPTION = {
    name: globals()[name].__doc__.split("\n")[-1].strip()
    for name in _PROBLEM_GENERATORS
}

# mapping of problem description to problem function name
_DESCRIPTION_TO_NAME = {
    globals()[name].__doc__.split("\n")[-1].strip(): name
    for name in _PROBLEM_GENERATORS
}

for generator in list(_SAVE_DATA["weights"].keys()):
    if generator not in globals().keys():
        del _SAVE_DATA["weights"][generator]

_SAVE_DATA["constants"]["weekdays"] = _WEEKDAYS
_SAVE_DATA["constants"]["months"] = _MONTHS
_SAVE_DATA["constants"]["variables"] = _VARIABLES

toml.dump(o=_SAVE_DATA, f=open(_SAVE_FILE.absolute(), "w"))

if __name__ == "__main__":
    main()
