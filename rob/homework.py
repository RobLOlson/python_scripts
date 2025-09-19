import datetime
import pathlib
import random
import sys
import time

import appdirs
import survey
import toml
import typer

from rob.utilities import query

try:
    from .algebra.problems import *  # noqa: F403
except ImportError:
    from algebra.problems import *  # noqa: F403

_DEBUG = False


app = typer.Typer()
algebra_app = typer.Typer()
list_app = typer.Typer()
config_app = typer.Typer()
app.add_typer(algebra_app, name="algebra")
algebra_app.add_typer(list_app, name="list")
app.add_typer(config_app, name="config")

if "english" in sys.argv:
    try:
        from .english import app as english_app

    except ImportError:
        from english import app as english_app

    app.add_typer(
        english_app,
        name="english",
        help="Prepare and generate English homework assignments.",
    )


def prepare_disk_io():
    """Prepare disk I/O for algebra homework."""

    start = time.perf_counter()
    global _LATEX_FILE, _SAVE_FILE, _SAVE_DATA, _LATEX_TEMPLATES, _WEEKDAYS, _MONTHS, _VARIABLES, _START
    _THIS_FILE = pathlib.Path(__file__)

    _LATEX_FILE = _THIS_FILE.parent / "config" / "algebra" / "latex_templates.toml"
    _LATEX_FILE.parent.mkdir(exist_ok=True)
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
    stop = time.perf_counter()
    if _DEBUG:
        print(f"File i/o boilerplate executed. ({stop - start: .3f} sec)")


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

    missing_problems = set(elem for elem in _PROBLEM_GENERATORS) - set(_SAVE_DATA["weights"].keys())

    for problem_type in missing_problems:
        _SAVE_DATA["weights"][problem_type] = 1000
        
            
    form = {
        _NAME_TO_DESCRIPTION[problem_type]: int(_SAVE_DATA["weights"][problem_type])
        for problem_type in _PROBLEM_GENERATORS
    }


    data = query.form_from_dict(form)

    if not data:
        return

    data = {_DESCRIPTION_TO_NAME[desc]: data[desc] for desc in data.keys()}
    _SAVE_DATA["weights"] = data
    toml.dump(o=_SAVE_DATA, f=open(_SAVE_FILE.absolute(), "w"))
    print(f"\nNew weights saved to {_SAVE_FILE.absolute()}")


@config_app.command("show")
def show_config(module: str = typer.Argument(None, help="Module to show config for (algebra, english, etc.)")):
    """Show configuration for a specific module or all modules."""
    
    prepare_disk_io()
    
    if module:
        if module == "algebra":
            print("=== Algebra Configuration ===")
            print(f"Config file: {_SAVE_FILE}")
            print(f"LaTeX templates: {_LATEX_FILE}")
            print("\nProblem weights:")
            for problem, weight in _SAVE_DATA["weights"].items():
                print(f"  {problem}: {weight}")
        elif module == "english":
            english_config_file = pathlib.Path(__file__).parent / "config" / "english" / "config.toml"
            if english_config_file.exists():
                print("=== English Configuration ===")
                print(f"Config file: {english_config_file}")
                english_data = toml.loads(open(english_config_file.absolute(), "r").read())
                for section, values in english_data.items():
                    print(f"\n[{section}]")
                    for key, value in values.items():
                        print(f"  {key} = {value}")
            else:
                print(f"English config file not found: {english_config_file}")
        else:
            print(f"Unknown module: {module}")
            print("Available modules: algebra, english")
    else:
        print("=== All Configuration Files ===")
        print(f"Algebra config: {_SAVE_FILE}")
        print(f"Algebra LaTeX templates: {_LATEX_FILE}")
        
        english_config_file = pathlib.Path(__file__).parent / "config" / "english" / "config.toml"
        print(f"English config: {english_config_file}")
        
        project_config_file = pathlib.Path(__file__).parent / "config" / "project.toml"
        print(f"Project config: {project_config_file}")


@config_app.command("edit")
def edit_config(module: str = typer.Argument(..., help="Module to edit config for (algebra, english, etc.)")):
    """Edit configuration for a specific module."""
    
    prepare_disk_io()
    
    if module == "algebra":
        print("Opening algebra configuration...")
        print("Use 'algebra config' to configure problem weights interactively")
        print(f"Or edit the config file directly: {_SAVE_FILE}")
        print(f"Or edit LaTeX templates: {_LATEX_FILE}")
    elif module == "english":
        english_config_file = pathlib.Path(__file__).parent / "config" / "english" / "config.toml"
        if english_config_file.exists():
            print(f"Opening English configuration: {english_config_file}")
            print("Edit this file to modify English homework settings")
        else:
            print(f"English config file not found: {english_config_file}")
    else:
        print(f"Unknown module: {module}")
        print("Available modules: algebra, english")


@config_app.command("algebra")
def edit_algebra_config():
    """Edit algebra configuration."""
    
    prepare_disk_io()
    
    configure_problem_set()

@config_app.command("english")
def edit_english_config():
    """Edit algebra configuration."""
    
    prepare_disk_io()
            
    from .english import config_english  # noqa: F401
    config_english()

@config_app.callback(invoke_without_command=True)
def config_default(ctx: typer.Context):
    """Manage configuration for different modules."""
    
    if ctx and ctx.invoked_subcommand:
        return
    
    available_apps = ["algebra", "english", "chemistry"]

    print("Which config?")
    choice = query.select(available_apps)

    match choice:
        case "algebra":
            edit_algebra_config()

        case "english":
            edit_english_config()


@algebra_app.callback(invoke_without_command=True)
def algebra_default(ctx: typer.Context, debug: bool = False):
    """Manage and generate algebra homework assignments."""

    if ctx and ctx.invoked_subcommand:
        return

    prepare_globals()

    selected_problems = query.approve_list(
        _ALL_PROBLEMS, repr_func=lambda p: p.long_description
    )



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

    available_apps = ["algebra", "english", "chemistry"]

    print("Which subject?")
    choice = query.select(available_apps)

    match choice:
        case "algebra":
            algebra_default(ctx=None)

        case "english":
            from .english import english_default

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
