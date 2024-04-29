# from __future__ import annotations

import datetime
import pathlib
import random

import appdirs
import toml
import typer

from .algebra.problems import *

try:
    from .english import app as english_app
    from .english import english_default
except ImportError:
    from english import app as english_app
    from english import english_default


def get_sympy():
    import sympy

    return sympy


def get_survey():
    import survey

    return survey


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


def prepare_disk_io():
    global _LATEX_FILE, _SAVE_FILE, _SAVE_DATA, _LATEX_TEMPLATES, _WEEKDAYS, _MONTHS, _VARIABLES, _START
    _THIS_FILE = pathlib.Path(__file__)

    # LATEX_FILE = pathlib.Path("config/latex_templates.toml")
    _LATEX_FILE = _THIS_FILE.parent / "config" / "algebra" / "latex_templates.toml"
    _LATEX_FILE.parent.mkdir(exist_ok=True)
    # _LATEX_FILE.touch()
    _LATEX_TEMPLATES = toml.loads(open(_LATEX_FILE.absolute(), "r").read())

    _SAVE_FILE = pathlib.Path(appdirs.user_data_dir()) / "robolson" / "algebra" / "config.toml"

    if not _SAVE_FILE.exists():
        # NEW_SAVE_FILE = pathlib.Path("data/algebra/save.toml")
        NEW_SAVE_FILE = _THIS_FILE.parent / "config" / "algebra" / "config.toml"
        _SAVE_DATA = toml.loads(open(NEW_SAVE_FILE.absolute(), "r").read())
        _SAVE_FILE.parent.mkdir(exist_ok=True)
        # _SAVE_FILE.touch()
        toml.dump(o=_SAVE_DATA, f=open(_SAVE_FILE.name, "w"))

    else:
        _SAVE_DATA = toml.loads(open(_SAVE_FILE.absolute(), "r").read())

    _WEEKDAYS = _SAVE_DATA["constants"]["weekdays"]
    _MONTHS = _SAVE_DATA["constants"]["months"]
    _VARIABLES = _SAVE_DATA["constants"]["variables"]

    _START = datetime.datetime.today()
    _DAYS = [_START + datetime.timedelta(days=i) for i in range(30)]
    _DATES = [
        f"{_WEEKDAYS[day.weekday()]} {_MONTHS[day.month]} {day.day}, {day.year}" for day in _DAYS
    ]


class ProblemCategory:
    """Represents a category of algebra problem.
    Must supply the logic for generating a problem statement as a valid function.
    Function must include a description of the problem type as the last line of its docstring.
    """

    def __init__(self, logic, weight: int):
        self.name = logic.__name__
        self.weight: int = weight
        self.logic = logic
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


@list_app.command("weights")
def list_weights() -> None:
    """List the frequency weights for each problem type."""

    prepare_globals()

    print(
        "--------------------------------\nProblems start with 1000 weight.  \nWeight decreases exponentially with use.  \nProblems with smaller weight are less likely to appear in problem sets.  \nSome problem types will increase with difficulty as their weight decreases.  \n--------------------------------"
    )

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

    prepare_globals()
    prepare_disk_io()

    if not problem_set or len(problem_set) == len(_ALL_PROBLEMS):
        problem_set: list[ProblemCategory] = _ALL_PROBLEMS
        problem_mass: int = 1000 * problem_count
        filtered_set: list[ProblemCategory] = []
        while problem_mass > 0 and len(filtered_set) < len(_ALL_PROBLEMS):
            filtered_set.append(problem_set[0])
            problem_set = problem_set[1:]
            problem_mass -= filtered_set[-1].weight

        problem_set = filtered_set

    pages = []
    solutions = []

    doc_header = _LATEX_TEMPLATES["doc_header"]

    for i in range(assignment_count):
        solution_set = rf"{_DATES[i]}\\"
        page_header = _LATEX_TEMPLATES["page_header"]
        parts = page_header.split("INSERT_DATE_HERE")
        page_header = _DATES[i].join(parts)

        problem_statement = ""

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

            # _SAVE_DATA["weights"][problem.name] = int(_SAVE_DATA["weights"][problem.name] * 0.9)
            _SAVE_DATA["weights"][problem.name] = int(
                _SAVE_DATA["weights"].get(problem.name, 1000) * 0.9
            )

        page_footer = r"\end{enumerate}"
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

    prepare_disk_io()

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

    prepare_globals()

    survey = get_survey()

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

    survey = get_survey()

    prepare_globals()

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

    print("???")
    list_app.rich_help_panel


@app.callback(invoke_without_command=True)
def default_homework(ctx: typer.Context):
    if ctx and ctx.invoked_subcommand:
        return

    survey = get_survey()

    available_apps = ["algebra", "english"]

    choice = survey.routines.select("Select the homework generation app: ", options=available_apps)

    choice = available_apps[choice]

    match choice:
        case "algebra":
            algebra_default(ctx=None)

        case "english":
            english_default(ctx=None)


def main():
    # default_homework(None)
    app()


_PROBLEM_GENERATORS = []
_ALL_PROBLEMS = []
_NAME_TO_DESCRIPTION = {}
_DESCRIPTION_TO_NAME = {}


def prepare_globals():
    global _PROBLEM_GENERATORS, _ALL_PROBLEMS, _NAME_TO_DESCRIPTION, _DESCRIPTION_TO_NAME

    prepare_disk_io()

    _problem_dict = {k: v for k, v in globals().items() if k.startswith("generate") and callable(v)}
    _PROBLEM_GENERATORS = [k for k in _problem_dict.keys()]

    _ALL_PROBLEMS = [
        ProblemCategory(logic=logic, weight=int(_SAVE_DATA["weights"].get(name, 1000)))
        for name, logic in _problem_dict.items()
    ]

    for problem in _ALL_PROBLEMS:
        if problem.weight is None:
            problem.weight = 1000
            _SAVE_DATA["weights"][problem.name] = 1000

    # mapping of problem function name to problem description
    _NAME_TO_DESCRIPTION = {
        name: globals()[name].__doc__.split("\n")[-1].strip() for name in _PROBLEM_GENERATORS
    }

    # mapping of problem description to problem function name
    _DESCRIPTION_TO_NAME = {
        globals()[name].__doc__.split("\n")[-1].strip(): name for name in _PROBLEM_GENERATORS
    }

    removed_old_generator = False
    for generator in list(_SAVE_DATA["weights"].keys()):
        if generator not in globals().keys():
            del _SAVE_DATA["weights"][generator]
            removed_old_generator = True

    if removed_old_generator:
        _SAVE_DATA["constants"]["weekdays"] = _WEEKDAYS
        _SAVE_DATA["constants"]["months"] = _MONTHS
        _SAVE_DATA["constants"]["variables"] = _VARIABLES

        toml.dump(o=_SAVE_DATA, f=open(_SAVE_FILE.absolute(), "w"))


# _problem_dict = { =_SAVE_DATA, f=open(_SAVE_FILE.absolute(), "w"))

if __name__ == "__main__":
    main()
