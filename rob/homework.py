import datetime
import os
import pathlib
import random
import sys

import appdirs
import PyMultiDictionary
import rich
import survey
import toml

from .problems import algebra
from .utilities import cli, query, tomlconfig

_DEBUG = False


# class ProblemCategory:
#     """Represents a category of algebra problem.
#     Must supply the logic for generating a problem statement as a valid function.
#     Function must include a description of the problem type as the last line of its docstring.
#     """

#     def __init__(self, logic, weight: int):
#         self.name = logic.__name__
#         self.weight: int = weight
#         self.logic = logic
#         if logic.__doc__:
#             self.description = logic.__doc__.split("\n")[-1].strip()
#         else:
#             print(f"Problem generator requires docstring: {logic.__name__}")
#             exit(0)
#         self.long_description = f"{self.description} ({self.weight})"

#     def generate(self):
#         """Return a Problem object"""

#         # return self.logic(self.weight)

#         problem, solution = self.logic(self.weight)
#         return Problem(problem, solution, self.name)


# class Problem:
#     """Represents a homework problem and its solution."""

#     def __init__(self, problem: str, solution: str, name: str):
#         self.problem = rf"\item {problem}"
#         self.solution = solution
#         self.name = name


def render_latex(
    problem_set: list[tuple[str, str]],
    start_date: datetime.datetime | None = None,
    assignment_count: int = 1,
    problem_count: int = 4,
    debug: bool = True,
    subject_name: str | None = None,
    stdout: bool = False,
    user: str | None = None,
):
    """Return a string coding for `assignment_count` pages of LaTeX algebra problems."""

    pages = []
    solutions = []

    if start_date is None:
        start_date = datetime.datetime.today()

    if user is None:
        user = _USERNAME

    doc_header = _LATEX_TEMPLATES["doc_header"]

    for i in range(assignment_count):
        solution_set = rf"{_DATES[i]}\\"

        page_header = _LATEX_TEMPLATES["page_header"]
        parts = page_header.split("INSERT_DATE_HERE")

        # page_header = _DATES[i].join(parts)
        date = start_date + datetime.timedelta(days=i)
        date = f"{_WEEKDAYS[date.weekday()]} {_MONTHS[date.month]} {date.day}, {date.year}"
        page_header = parts[0] + date + parts[1]
        parts = page_header.split("INSERT_STUDENT_HERE")
        page_header = user.capitalize().join(parts)

        # if _USERNAME is not None and _USERNAME != "default":
        #     page_header = _USERNAME.capitalize().join(parts)
        # else:
        #     page_header = parts[0] + parts[1]

        parts = page_header.split("INSERT_SUBJECT_HERE")
        page_header = subject_name.title().join(parts)

        problem_statement = ""

        for k in range(problem_count):
            if k % 3 == 0 and k != 0:
                problem_statement += r"\newpage"

            # WARNING:got a sporadic IndexError here, k not in problem_set
            problem_statement += "\\item " + problem_set[k][0] + "\\\\"
            solution_set += rf"{k + 1}: {problem_set[k][1]}\;\;"

        problem_set = problem_set[k + 1 :]
        page_footer = r"\end{enumerate}"
        solutions.append(solution_set)
        pages.append(page_header + problem_statement + page_footer)

    doc_footer = r"\end{document}"

    document = doc_header + r"\newpage".join(pages) + r"\newpage " + r"\\".join(solutions) + doc_footer

    if stdout:
        print(document)
        return

    document_name = f"{subject_name} Homework {_MONTHS[datetime.datetime.now().month]} {datetime.datetime.now().day} {datetime.datetime.now().year}.tex"

    print(f"Writing LaTeX document to '{document_name}")

    fp = open(document_name, "w")
    fp.write(document)
    fp.close()

    if not debug:
        toml.dump(o=_SAVE_DATA, f=open(_SAVE_FILE.absolute(), "w"))


@cli.cli("reset algebra")
@cli.cli("algebra reset")
def reset_weights(user: str | None = None, debug: bool = True):
    """Reset problem frequency rates to default."""

    rich.print(f"[red]Reset [yellow]{_USERNAME}'s[/yellow] frequency weights to default (1000)?[/red]")
    if query.confirm():
        for key in _CONFIG[_USERNAME]["algebra"]["weights"].keys():
            _CONFIG[_USERNAME]["algebra"]["weights"][key] = _FALLBACK_CONFIG["default"]["algebra"][
                "weights"
            ].get(key, 1000)
        _CONFIG.sync()

    exit(0)


# @config_app.callback(invoke_without_command=True)
@cli.cli("config open")
@cli.cli("config")
def config_default(user: str | None = None):
    """Open configuration file."""

    os.startfile(_SAVE_FILE.absolute())


# @algebra_app.callback(invoke_without_command=True)
@cli.cli("algebra")
def algebra_default(
    user: str | None = None,
    start_date: datetime.datetime | None = None,
    assignment_count: int = 5,
    problem_count: int = 4,
    stdout: bool = False,
    interact: bool = True,
    render: bool = True,
) -> list[tuple[str, str]]:
    """Generate algebra homework assignments.

    Returns a list of tuples of problem statements and solutions."""

    # prepare_globals(user=user)

    if start_date is None:
        start_date = datetime.datetime.today()

    if user:
        user = user.lower()
    else:
        user = _USERNAME

    db = tomlconfig.TomlConfig(_SAVE_FILE)

    # Preserve definition order by iterating over the module dict (insertion-ordered)
    all_problems = [
        obj for name, obj in algebra.__dict__.items() if name.startswith("generate_") and callable(obj)
    ]

    for problem in all_problems:
        try:
            db[user]["algebra"]["weights"][problem.__name__]
        except KeyError:
            db[user] = db.get(user, {})
            db[user]["algebra"] = db.get(user, {}).get("algebra", {})
            db[user]["algebra"]["weights"] = db.get(user, {}).get("algebra", {}).get("weights", {})
            db[user]["algebra"]["weights"][problem.__name__] = 1000
    db.sync()

    if interact:
        approved_problems = query.approve_list(
            all_problems,
            repr_func=lambda p: p.__doc__.split("\n")[-1].strip()
            + f" ({db.get(user, {}).get('algebra', {}).get('weights', {}).get(p.__name__, 1000)})",
        )

        start_date = survey.routines.datetime(
            "Select assignment start date: ",
            attrs=("month", "day", "year"),
        )

        assignment_count = query.integer(
            "How many algebra assignments to generate? ", default=assignment_count, minimum=1, maximum=100
        )

        problem_count = query.integer(
            "How many problems per assignment? ", default=problem_count, minimum=1, maximum=100
        )
    else:
        approved_problems = all_problems
        start_date = datetime.datetime.today()

    days = [start_date + datetime.timedelta(days=i) for i in range(assignment_count + 1)]

    global _DATES
    _DATES = [f"{_WEEKDAYS[day.weekday()]} {_MONTHS[day.month]} {day.day}, {day.year}" for day in days]

    approved_weights = [
        db.get(_USERNAME, {}).get("algebra", {}).get("weights", {}).get(p.__name__, 1000)
        for p in approved_problems
    ]

    used_problems = []
    problem_list = []
    for n in range(assignment_count * problem_count):
        target_weight = random.randint(0, 1000)
        cur_weight = 0
        chosen_problem = None
        for problem in approved_problems:
            if len(used_problems) == len(approved_problems):
                used_problems = []

            cur_weight += approved_weights[approved_problems.index(problem)]
            if cur_weight >= target_weight and problem not in used_problems:
                chosen_problem = problem
                # problem_list.append(problem)
                # used_problems.append(problem)
                break
        if chosen_problem is None:
            problem_list.append(random.choice(approved_problems))
            used_problems.append(problem_list[-1])
        else:
            problem_list.append(chosen_problem)
            used_problems.append(chosen_problem)
            db[_USERNAME]["algebra"]["weights"][chosen_problem.__name__] = int(
                db[_USERNAME]["algebra"]["weights"][chosen_problem.__name__] * 0.8
            )
            approved_weights[approved_problems.index(chosen_problem)] = int(
                approved_weights[approved_problems.index(chosen_problem)] * 0.8
            )

    problem_set = []
    for problem in problem_list:
        problem_set.append(problem(freq_weight=approved_weights[approved_problems.index(problem)]))

    db.sync()

    if render:
        render_latex(
            start_date=start_date,
            assignment_count=assignment_count,
            problem_count=problem_count,
            problem_set=problem_set,
            subject_name="Algebra",
            user=user,
            stdout=stdout,
        )
    return problem_set


@cli.cli("multiple")
def multiple_default(user: str | None = None, assignment_count: int | None = None, interact: bool = True):
    """Launch TUI for multiple subject generation."""

    all_subjects = ["algebra", "vocabulary"]
    approved_subjects = query.approve_list(all_subjects)

    form = {}

    if user:
        user = user.lower()

    form["start_date"] = datetime.datetime.today()
    form["user"] = user
    form["assignment_count"] = 5
    form["problem count"] = {}
    for subject in approved_subjects:
        form["problem count"][f"{subject}"] = 3

    data = query.form_from_dict(form)
    # data = query.edit_object(form, show_brackets=False, edit_keys=False)

    start_date = data["start_date"]
    assignment_count = data["assignment_count"]
    user = data["user"]

    # for subject in approved_subjects:
    #     problem_count[subject] = data["problem count"][f"{subject}"]

    # assignment_count = query.integer("How many assignments to generate? ", default=5)

    problem_set = []
    for subject in approved_subjects:
        problem_count = data["problem count"].get(f"{subject}", 3)
        match subject:
            case "algebra":
                # problem_count = query.integer("How many algebra problems per assignment? ", default=4)
                problem_set.extend(
                    algebra_default(
                        user=user,
                        start_date=start_date,
                        assignment_count=assignment_count,
                        problem_count=problem_count,
                        render=False,
                        interact=False,
                    )
                )
            case "vocabulary":
                # problem_count = query.integer("How many vocabulary problems per assignment? ", default=2)
                problem_set.extend(
                    vocabulary_default(
                        user=user,
                        assignment_count=assignment_count,
                        problem_count=problem_count,
                        render=False,
                        interact=False,
                    )
                )

    # problem_count = query.integer("How many problems per assignment? ", default=6)
    # WARNING: got a sporadic ValueError here, sample larger than population
    try:
        problem_set = random.sample(problem_set, k=max(assignment_count * problem_count, len(problem_set)))
    except ValueError:
        problem_set = random.choices(problem_set, k=max(assignment_count * problem_count, len(problem_set)))

    problem_count = sum(data["problem count"].values())
    if interact:
        rich.print("Rendering LaTeX document...")

    render_latex(
        start_date=start_date,
        assignment_count=assignment_count,
        problem_count=problem_count,
        problem_set=problem_set,
        subject_name="+".join(approved_subjects),
        user=user,
    )


@cli.cli("vocabulary")
def vocabulary_default(
    user: str | None = None,
    assignment_count: int = 5,
    problem_count: int = 3,
    stdout: bool = False,
    interact: bool = True,
    debug: bool = True,
    render: bool = True,
) -> list[tuple[str, str]]:
    """Render a set of vocabulary problems.

    Returns a list of tuples of problem statements and solutions."""

    if interact:
        start_date = survey.routines.datetime(
            "Select assignment start date: ",
            attrs=("month", "day", "year"),
        )
        assignment_count = query.integer(
            preamble="How many vocabulary assignments to generate? ",
            default=assignment_count,
            minimum=1,
            maximum=100,
        )
        problem_count = query.integer(
            preamble="How many problems per assignment? ", default=problem_count, minimum=1, maximum=100
        )
    else:
        start_date = datetime.datetime.today()

    days = [start_date + datetime.timedelta(days=i) for i in range(assignment_count + 1)]

    global _DATES
    _DATES = [f"{_WEEKDAYS[day.weekday()]} {_MONTHS[day.month]} {day.day}, {day.year}" for day in days]

    used_words = []
    selected_problems = []

    for n in range(assignment_count * problem_count):
        proposed_problem = vocab_problem(excludes=used_words)
        used_words.append(proposed_problem[0])
        selected_problems.append(proposed_problem)

    problem_set: list[tuple[str, str]] = [(p[1], p[2]) for p in selected_problems]

    if render:
        render_latex(
            assignment_count=assignment_count,
            problem_count=problem_count,
            start_date=start_date,
            debug=debug,
            problem_set=problem_set,
            subject_name="Vocabulary",
            user=user,
            stdout=stdout,
        )

    return problem_set


def vocab_problem(
    user: str | None = None, excludes: list[str] | None = None, stdout: bool = False
) -> tuple[str, str]:
    """Generate a vocabulary problem."""

    dictionary = PyMultiDictionary.MultiDictionary()

    if excludes is None:
        excludes = []

    # vocab_weights = db.get(_USERNAME, {}).get("vocabulary", {}).get("weights")
    try:
        vocab_weights = _CONFIG[_USERNAME]["vocabulary"]["weights"]
    except KeyError:
        vocab_weights = {}
        _CONFIG[_USERNAME] = {}
        _CONFIG[_USERNAME]["vocabulary"] = {}
        _CONFIG[_USERNAME]["vocabulary"]["weights"] = {}
        _CONFIG.sync()

    vocab_index = random.randint(0, 1000)

    cur_index = 0
    target_word: str | None = None

    for word, weight in vocab_weights.items():
        cur_index += weight
        if cur_index >= vocab_index and word not in excludes:
            target_word = word
            break

    if target_word is None:
        word_pool = set(_VOCABULARY_WORDS) - set(list(vocab_weights.keys()))
        target_word = random.choice(list(word_pool))
        target_weight = 1000
    else:
        target_weight = vocab_weights[target_word]

    # with TomlConfig(_SAVE_FILE) as config:
    #     config["weights"][_USERNAME]["vocabulary"][target_word] = target_weight * 0.75
    # try:
    #     db[_USERNAME]
    #     db[_USERNAME]["vocabulary"]
    #     db[_USERNAME]["vocabulary"]["weights"]
    # except KeyError:
    #     db[_USERNAME] = db.get(_USERNAME, {})
    #     db[_USERNAME]["vocabulary"] = db.get(_USERNAME, {}).get("vocabulary", {})
    #     db[_USERNAME]["vocabulary"]["weights"] = (
    #         db.get(_USERNAME, {}).get("vocabulary", {}).get("weights", {})
    #     )
    with tomlconfig.TomlConfig(_SAVE_FILE) as config:
        config[_USERNAME]["vocabulary"]["weights"][target_word] = int(
            target_weight * (1 - random.random() * random.random())
        )
    # _CONFIG[_USERNAME]["vocabulary"]["weights"][target_word] = int(
    #     target_weight * (1 - random.random() * random.random())
    # )
    # _CONFIG.sync()

    problem = f"What is the definition of \\textit{{{target_word}}}?"
    solution = f"{dictionary.meaning('en', target_word)[1].replace(f'The definition of {target_word} in the dictionary is', '')}".strip().capitalize()
    # db.sync()
    if stdout:
        print(f"('{target_word}','{problem}', '{solution}')")
    else:
        return (target_word, problem, solution)


# @app.callback(invoke_without_command=True)
@cli.cli("")
def homework(user: str | None = None):
    """Launch TUI for homework generation."""

    available_apps = ["multiple", "algebra", "vocabulary"]

    print("Which subject?")
    choice = query.select(available_apps)

    match choice:
        case "multiple":
            multiple_default(user=user)

        case "algebra":
            algebra_default(user=user)

        case "vocabulary":
            vocabulary_default(user=user)


_OPTIONS = cli._parse_options(sys.argv[1:])
_SAVE_FILE = pathlib.Path(appdirs.user_data_dir()) / "robolson" / "homework" / "config.toml"
_FALLBACK_FILE = pathlib.Path(__file__).parent / "config" / "homework" / "config.toml"
_FALLBACK_CONFIG = tomlconfig.TomlConfig(
    user_toml_file=_FALLBACK_FILE, default_toml_file=_FALLBACK_FILE, readonly=True
)
_CONFIG = tomlconfig.TomlConfig(user_toml_file=_SAVE_FILE, default_toml_file=_FALLBACK_FILE)
_USERNAME: str = _OPTIONS.get("user", _CONFIG.get("default_user", "default"))
_LATEX_FILE = pathlib.Path(__file__).parent / "config" / "homework" / "latex_templates.toml"
_LATEX_TEMPLATES = toml.loads(open(_LATEX_FILE.absolute(), "r").read())

_VOCABULARY_FILE = pathlib.Path(__file__).parent / "data" / "sat_words.txt"
_VOCABULARY_WORDS = open(_VOCABULARY_FILE).read().split("\n")


_PROBLEM_GENERATORS = []
_ALL_PROBLEMS = []
_NAME_TO_DESCRIPTION = {}
_DESCRIPTION_TO_NAME = {}
_SAVE_DATA = {}

_WEEKDAYS = _CONFIG.get("constants", {}).get("weekdays")
_MONTHS = _CONFIG.get("constants", {}).get("months")
_VARIABLES = _CONFIG.get("constants", {}).get("variables")

if __name__ == "__main__":
    cli.parse_and_invoke(
        # passed_args=sys.argv[1:],
        use_configs=True,
        default_config_file=pathlib.Path(__file__).parent / "cli" / "homework_config.toml",
    )
