from __future__ import annotations

import datetime
import math
import pathlib
import random
import re
from decimal import Decimal
from typing import Callable

import appdirs
import survey
import sympy
import toml
import typer

from .english import app as english_app
from .english import english_default

app = typer.Typer()
algebra_app = typer.Typer()
list_app = typer.Typer(no_args_is_help=True)
app.add_typer(algebra_app, name="algebra")
app.add_typer(
    english_app,
    name="english",
    help="Prepare and generate English homework assignments.",
)
algebra_app.add_typer(list_app, name="list")


_DEBUG = False

_THIS_FILE = pathlib.Path(__file__)

# LATEX_FILE = pathlib.Path("config/latex_templates.toml")
_LATEX_FILE = _THIS_FILE.parent / "config" / "algebra" / "latex_templates.toml"
_LATEX_FILE.parent.mkdir(exist_ok=True)
_LATEX_FILE.touch()
_LATEX_TEMPLATES = toml.loads(open(_LATEX_FILE.absolute(), "r").read())

_SAVE_FILE = pathlib.Path(appdirs.user_data_dir()) / "robolson" / "algebra" / "config.toml"

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
_DAYS = [_START + datetime.timedelta(days=i) for i in range(30)]
_DATES = [f"{_WEEKDAYS[day.weekday()]} {_MONTHS[day.month]} {day.day}, {day.year}" for day in _DAYS]

_CONSTANT_COEF_DOT_PATTERN = re.compile(r"(\d+\s*)\\cdot(\s[a-zA-Z])")


class ProblemCategory:
    """Represents a category of algebra problem.
    Must supply the logic for generating a problem statement as a valid function.
    Function must include a description of the problem type as the last line of its docstring.
    """

    def __init__(self, logic: Callable, weight: int):
        self.name = logic.__name__
        self.weight: int = weight
        self.logic: Callable = logic
        if logic.__doc__:
            self.description = logic.__doc__.split("\n")[-1].strip()
        else:
            print(f"Problem generator requires docstring: {logic.__name__}")
            exit(0)
        self.long_description = f"{self.description} ({self.weight})"

    def generate(self):
        """Return a tuple of strings ('problem statement', 'solution')"""

        # return self.logic(self.weight)

        problem, solution = self.logic(self.weight)
        return Problem(problem, solution, self.name)


class Problem:
    """Represents a specific algebra problem and its solution."""

    def __init__(self, problem: str, solution: str, name: str):
        self.problem = rf"\item {problem}"
        self.solution = solution
        self.name = name


# To write a new algebra problem generator you must:
# * begin the function name with 'generate'
# * return a 2-tuple of strings ('TeX problem', 'answer')
# * the last line of the doc string should describe or name the problem type


def random_factor(
    var, min_coef: int = 1, max_coef: int = 9, min_order: int = 1, max_order: int = 1
):
    return random.randint(min_coef, max_coef) * (var ** random.randint(min_order, max_order))


def generate_simple_x_expression(freq_weight: int = 1000) -> tuple[str, str]:
    """Generate an expression in one variable where coefficients and exponents are all integers.
    Problem Description:
    Simplifying Expressions"""

    difficulty = int(3 - math.log(freq_weight + 1, 10))
    var = random.choice(sympy.symbols("a b c x y z m n"))
    problem = "Simplify the following expression."

    def fac():
        return random_factor(var, max_coef=5, max_order=1 + difficulty)

    expression = f"{fac()} * {fac()} * {fac()} + {fac()} * {fac()} * {fac()}"
    if difficulty > 1:
        expression += f" + {fac()} * {fac()} * {fac()}"

    latex_problem = sympy.latex(sympy.sympify(expression, evaluate=False), mul_symbol="dot")

    latex_problem = _CONSTANT_COEF_DOT_PATTERN.sub(r"\1\2", latex_problem)

    solution = sympy.latex(sympy.sympify(expression))

    return (
        rf"{problem} \\ \\ \({latex_problem}\) \\ \\ \\ \\ \\ \\ \\ \\",
        rf"\({solution}\)",
    )


def generate_expression_evaluation(freq_weight: int = 1000) -> tuple[str, str]:
    """Generate an expression in one variable where coefficients and exponents are all integers.
    Problem Description:
    Evaluating Expressions"""

    difficulty = int(3 - math.log(freq_weight + 1, 10))
    var = random.choice(sympy.symbols("a b c x y z m n"))
    if difficulty > 1:
        constant = random_decimal("0.05") + random.randint(0, 4)
    else:
        constant = random.randint(1, 9)

    def fac():
        return random_factor(var, max_coef=3 + difficulty, max_order=max(1 + difficulty, 2))

    expression = f"{fac()} * {fac()} + {fac()} * {fac()}"
    if difficulty > 1:
        expression += f" + {fac()} * {fac()}"

    latex_expression = sympy.latex(sympy.sympify(expression, evaluate=False), mul_symbol="dot")

    latex_expression = _CONSTANT_COEF_DOT_PATTERN.sub(r"\1\2", latex_expression)

    solution = round(sympy.sympify(expression).evalf(subs={var: constant}))

    prompt = f"Evaluate the following expression with \\({var}\\) = {constant}"

    return (
        rf"{prompt} \\ \\ \({latex_expression}\) \\ \\ \\ \\ \\ \\ \\ \\",
        rf"\({solution!s}\)",
    )


def generate_simple_x_equation(freq_weight: int = 1000) -> tuple[str, str]:
    """Generate a single variable equation.
    Problem Description:
    Solving Equations with One Variable"""

    difficulty = int(3 - math.log(freq_weight + 1, 10))
    var = random.choice(sympy.symbols("a b c x y z m n"))
    if difficulty > 1:
        coef = random_decimal("0.05") + random.randint(-4, 4)
        coef = coef if coef else 1

    else:
        coef = random.randint(-2, 4)
        coef = coef if coef else 1

    left_string = f"{coef} * ({random.randint(1,4)} * {var} + {random.randint(1,9)})"
    right_string = f"{random.randint(1,7)} * {var} + {random.randint(1,9)}"

    left_latex = sympy.latex(sympy.sympify(left_string, evaluate=False), mul_symbol="dot")
    right_latex = sympy.latex(sympy.sympify(right_string, evaluate=False), mul_symbol="dot")

    # left_expression = _CONSTANT_COEF_DOT_PATTERN.sub(r"\1\2", left_latex)
    # right_expression = _CONSTANT_COEF_DOT_PATTERN.sub(r"\1\2", right_latex)

    solution = sympy.solve(sympy.Eq(sympy.sympify(left_string), sympy.sympify(right_string)), var)
    if solution:
        solution = sympy.latex(solution[0])
        # solution = f"{var} = " + ", ".join(str(round(elem, 2)) for elem in solution)
    else:
        solution = "\\text{No solution.}"

    prompt = f"Solve the following equation for \\({var}\\)."

    return (
        rf"{prompt} \\ \\ \({left_latex} = {right_latex}\) \\ \\ \\ \\ \\ \\ \\ \\",
        rf"\({solution!s}\)",
    )


def random_decimal(n="0.05"):
    """Return a fractional decimal rounded to the nearest 'n'"""
    target = Decimal(n) * 100
    return Decimal(target * round(random.randint(1, 100) / target)) / Decimal(100)


def generate_decimal_x_equation(freq_weight: int = 1000) -> tuple[str, str]:
    """Generate an equation with decimal coefficients.
    Problem Description:
    Solving Equations with Decimal Coefficients"""

    difficulty = int(3 - math.log(freq_weight + 1, 10))
    var = random.choice(sympy.symbols("a b c x y z m n"))
    if difficulty > 1:
        denom = random.randint(2, 9)
    else:
        denom = random.randint(2, 5)

    left_string = f"({random.randint(1, 4)} / {denom}) * ({random.randint(1, 4)} * {var} + {random.randint(-4, 4)})"
    right_string = f"{random.randint(1, 7)} * {var} + {random.randint(-9, 9)} / {denom}"

    left_latex = sympy.latex(sympy.sympify(left_string, evaluate=False), mul_symbol="dot")
    right_latex = sympy.latex(sympy.sympify(right_string, evaluate=False), mul_symbol="dot")

    # left_expression = _CONSTANT_COEF_DOT_PATTERN.sub(r"\1\2", left_latex)
    # right_expression = _CONSTANT_COEF_DOT_PATTERN.sub(r"\1\2", right_latex)

    solution = sympy.solve(sympy.Eq(sympy.sympify(left_string), sympy.sympify(right_string)), var)
    if solution:
        solution = sympy.latex(solution[0])
        # solution = f"{var} = " + ", ".join(str(round(elem, 2)) for elem in solution)
    else:
        solution = "\\text{No solution.}"

    prompt = f"Solve the following equation for \\({var}\\)."

    return (
        rf"{prompt} \\ \\ \(\displaystyle {left_latex} = {right_latex}\) \\ \\ \\ \\ \\ \\ \\ \\",
        rf"\({solution!s}\)",
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
    problem = "Isolate the variable y.  Find the x-intercept and the y-intercept."

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


@algebra_app.command("render")
def render_latex(
    assignment_count: int = 1,
    problem_count: int = 4,
    debug: bool = False,
    threshold: int = 0,
    problem_set=None,  # type: ignore Typer
) -> None:
    """Return a string coding for {assignment_count} pages of LaTeX algebra problems."""

    if not problem_set:
        problem_set: list[ProblemCategory] = _ALL_PROBLEMS

    pages = []
    solutions = []

    doc_header = _LATEX_TEMPLATES["doc_header"]

    for i in range(assignment_count):
        solution_set = rf"{_DATES[i]}\\"
        page_header = _LATEX_TEMPLATES["page_header"]
        parts = page_header.split("INSERT_DATE_HERE")
        page_header = _DATES[i].join(parts)

        problem_statement = ""

        # generators = random.sample(_PROBLEM_GENERATORS, k=problem_count, counts=WEIGHTS)

        problem_generators = random.sample(
            problem_set,
            k=problem_count,
            counts=[problem.weight + problem_count + 1 for problem in problem_set],
        )

        problems: list[Problem] = [problem.generate() for problem in problem_generators]

        for k, problem in enumerate(problems):
            if k % 3 == 0 and k != 0:
                problem_statement += r"\newpage"

            problem_statement += problem.problem
            solution_set += rf"{k+1}: {problem.solution}\;\;"

            _SAVE_DATA["weights"][problem.name] = int(_SAVE_DATA["weights"][problem.name] * 0.9)

        page_footer = r"\end{enumerate}"
        # solution += r"\\"
        solutions.append(solution_set)
        pages.append(page_header + problem_statement + page_footer)

    doc_footer = r"\end{document}"

    document = (
        doc_header + r"\newpage".join(pages) + r"\newpage " + r"\\".join(solutions) + doc_footer
    )

    document_name = f"Algebra Homework {_MONTHS[datetime.datetime.now().month]} {datetime.datetime.now().day} {datetime.datetime.now().year}.tex"

    print(f"Writing LaTeX document to '{document_name}")

    fp = open(document_name, "w")
    fp.write(document)
    fp.close()

    if not debug:
        toml.dump(o=_SAVE_DATA, f=open(_SAVE_FILE.absolute(), "w"))


@algebra_app.command("reset")
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


@algebra_app.command("config")
def configure_problem_set():
    """Configures the frequency rates of problems."""

    form = {
        _NAME_TO_DESCRIPTION[problem_type]: survey.widgets.Count(
            value=_SAVE_DATA["weights"][problem_type]
        )
        for problem_type in _PROBLEM_GENERATORS
    }

    data = survey.routines.form("Frequency Weights (higher -> more frequent): ", form=form)

    if not data:
        return

    data = {_DESCRIPTION_TO_NAME[desc]: data[desc] for desc in data.keys()}
    _SAVE_DATA["weights"] = data
    toml.dump(o=_SAVE_DATA, f=open(_SAVE_FILE.absolute(), "w"))
    print(f"\nNew weights saved to {_SAVE_FILE.absolute()}")


@algebra_app.callback(invoke_without_command=True)
def algebra_default(ctx: typer.Context, debug: bool = False):
    """Manage and generate algebra homework assignments."""

    if ctx and ctx.invoked_subcommand:
        return

    global _PROBLEM_GENERATORS

    # descriptions = [description for description in _DESCRIPTION_TO_NAME.keys()]

    problem_indeces = survey.routines.basket(
        "Select problem types to include.  (Numbers indicate relative frequency rate.)",
        options=[problem.long_description for problem in _ALL_PROBLEMS],
    )

    selected_problems = [_ALL_PROBLEMS[i] for i in problem_indeces]  # type: ignore

    start_date = survey.routines.datetime(
        "Select assignment start date: ",
        attrs=("month", "day", "year"),
    )
    if not start_date:
        start_date = datetime.datetime.today()

    assignment_count = survey.routines.numeric(
        "How many algebra assignments to generate? ", decimal=False, value=5
    )

    if not assignment_count:
        assignment_count = 5

    problem_count = survey.routines.numeric(
        "How many problems per assignment? ", decimal=False, value=4
    )

    if not problem_count:
        problem_count = 4

    days = [start_date + datetime.timedelta(days=i) for i in range(assignment_count + 1)]

    global _DATES
    _DATES = [
        f"{_WEEKDAYS[day.weekday()]} {_MONTHS[day.month]} {day.day}, {day.year}" for day in days
    ]

    render_latex(
        assignment_count=assignment_count,
        problem_count=problem_count,
        debug=debug,
        problem_set=selected_problems,
    )


@list_app.callback(invoke_without_command=True)
def list_default(ctx: typer.Context):
    """List problem types, frequency weights, etc."""
    if ctx.invoked_subcommand:
        return

    list_app.rich_help_panel


@app.callback(invoke_without_command=True)
def default_homework(ctx: typer.Context):
    if ctx.invoked_subcommand:
        return

    available_apps = ["algebra", "english"]

    choice = survey.routines.select("Select the homework generation app: ", options=available_apps)

    choice = available_apps[choice]

    match choice:
        case "algebra":
            algebra_default(None)

        case "english":
            english_default(None)


def main():
    app()


WEIGHTS = []
_PROBLEM_GENERATORS = [e for e in locals() if "generate" in e]
for generator in _PROBLEM_GENERATORS:
    if generator not in _SAVE_DATA["weights"].keys():
        _SAVE_DATA["weights"][generator] = 1000

    WEIGHTS.append(1 + _SAVE_DATA["weights"][generator])

_ALL_PROBLEMS = [
    ProblemCategory(logic=v, weight=int(_SAVE_DATA["weights"][k]))
    for k, v in locals().items()
    if "generate" in k
]

# mapping of problem function name to problem description
_NAME_TO_DESCRIPTION = {
    name: globals()[name].__doc__.split("\n")[-1].strip() for name in _PROBLEM_GENERATORS
}

# mapping of problem description to problem function name
_DESCRIPTION_TO_NAME = {
    globals()[name].__doc__.split("\n")[-1].strip(): name for name in _PROBLEM_GENERATORS
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
