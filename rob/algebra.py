from __future__ import annotations

import datetime
import itertools
import math
import operator
import pathlib
import random
import re
from decimal import Decimal
from typing import Callable

import appdirs
import survey
import toml
import typer

app = typer.Typer()
list_app = typer.Typer(no_args_is_help=True)
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
_DAYS = [_START + datetime.timedelta(days=i) for i in range(30)]
_DATES = [
    f"{_WEEKDAYS[day.weekday()]} {_MONTHS[day.month]} {day.day}, {day.year}"
    for day in _DAYS
]


class CoefficientError(Exception):
    pass


class UnlikeTermsError(Exception):
    pass


class ProblemCategory:
    """Represents a category of algebra problem.
    Must supply the logic for generating a problem statement as a valid function.
    Function must include a description of the problem type as the last line of its docstring.
    """

    def __init__(self, logic: Callable, weight: int):
        self.name = logic.__name__
        self.weight = weight
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


class Term:
    """Represents a simple term."""

    # term_pattern = re.compile(r"^(\d+|\d+\.\d+|-)?([a-z])?(?:\^(-?\d+\.?\d*))?$")
    term_pattern = re.compile(r"^(-?\d+\.?\d*|-)?([a-z])?(?:\^(-?\d+\.?\d*))?$")

    integer_pattern = re.compile(r"^\d+$")

    def __init__(
        self,
        coefficient: str | int | float | None = None,
        variable: str | None = None,
        power: int | float | None = None,
    ):
        expression = self.term_pattern.match(str(coefficient))

        if expression and not variable and not power:
            coefficient, self.variable, inline_power = expression.groups()
            if coefficient == "-":
                coefficient = -1
            if coefficient:
                if int(float(coefficient)) - float(coefficient) == 0:
                    self.coefficient = int(float(coefficient))
                else:
                    self.coefficient = float(coefficient)
            else:
                self.coefficient = 1

            if inline_power != None:
                if int(float(inline_power)) - float(inline_power) == 0:
                    self.power = int(inline_power)
                else:
                    self.power = float(inline_power)

                if not self.power:
                    self.variable = None
            else:
                self.power = 1

            # self.power = int(power) if power else 1

            return

        if coefficient:
            if int(float(coefficient)) - float(coefficient) == 0:
                self.coefficient = int(coefficient)
            else:
                self.coefficient = float(coefficient)
        else:
            self.coefficient = 1
            # self.variable = variable
            # self.power = 1
            # return

        # self.coefficient = float(coefficient) if coefficient else 0

        if power is None:
            self.power = 1
            self.variable = variable
        else:
            if float(power) == 0:
                self.variable = None
                self.power = 1
                return
            elif int(float(power)) - float(power) == 0:
                self.power = int(power)
                # self.variable = variable
            else:
                self.power = float(power)
                # self.variable = variable

        self.variable = variable
        # self.power = power if power else 1

    @classmethod
    def random_coef(cls, variable: str | None = None):
        """Generate a first-order Term with a random coefficient in {2..9}."""

        if not variable:
            variable = random.choice(_VARIABLES)
        coefficient = random.randint(1, 9)
        return cls(coefficient=coefficient, variable=variable, power=None)

    def __str__(self):
        if not self.coefficient:
            return "0"

        if self.power == 1:
            power = ""

        else:
            if type(self.power) == float:
                numerator, denominator = self.power.as_integer_ratio()
                power = rf"^\frac{{{numerator}}}{{{denominator}}}"
            else:
                power = rf"^{{{self.power}}}"

        coefficient = self.coefficient if self.coefficient != 1 else ""

        variable = self.variable if self.variable else ""

        return rf"{coefficient}{variable}{power}"

    def __repr__(self):
        return f"Term(coefficient={self.coefficient}, variable={self.variable}, power={self.power})"

    def __add__(self, __value: Term | Binomial) -> Term:
        if type(__value) == Binomial:
            __value = __value.simplify()
            if type(__value) == Binomial:
                raise UnlikeTermsError

        assert type(__value) == Term

        left = self.coefficient if self.coefficient else 1
        right = __value.coefficient if __value.coefficient else 1

        if self.variable != __value.variable or self.power != __value.power:
            raise UnlikeTermsError

        else:
            coefficient = left + right
            if coefficient == 0:
                variable = None
                power = 1
            else:
                variable = self.variable
                power = self.power
            return Term(
                coefficient=coefficient, variable=self.variable, power=self.power
            )

    def __sub__(self, __value: Term) -> Term:
        # left = self.coefficient if self.coefficient else 1
        # right = __value.coefficient if __value.coefficient else 1

        left = self.coefficient
        right = __value.coefficient

        if self.variable != __value.variable or self.power != __value.power:
            raise CoefficientError
        else:
            coefficient = left - right
            if coefficient == 0:
                variable = None
                power = 1
            else:
                variable = self.variable
                power = self.power

            return Term(coefficient=coefficient, variable=variable, power=power)

    def __mul__(self, __value: Term) -> Term:
        if self.variable and __value.variable and self.variable != __value.variable:
            raise CoefficientError

        left_power = self.power if self.variable else 0
        right_power = __value.power if __value.variable else 0

        new_power = left_power + right_power

        if int(new_power) - new_power == 0:
            new_power = int(new_power)

        variable = self.variable if self.variable else __value.variable

        return Term(
            coefficient=round(self.coefficient * __value.coefficient, 2),
            variable=variable,
            power=new_power,
        )

    def __eq__(self, __value: Term) -> bool:
        return (
            self.coefficient == __value.coefficient
            and self.variable == __value.variable
            and self.power == __value.power
        )

    def __truediv__(self, __value: Term) -> Term:
        if self.variable and __value.variable and self.variable != __value.variable:
            raise CoefficientError

        left_power = self.power if self.variable else 0
        right_power = __value.power if __value.variable else 0

        variable = self.variable if self.variable else __value.variable

        return Term(
            coefficient=round(float(self.coefficient) / float(__value.coefficient), 2),
            variable=variable,
            power=left_power - right_power,
        )

    def evaluated_at(self, val: int | float) -> int | float:
        temp = val**self.power
        if int(temp) - temp == 0:
            temp = int(temp)

        return temp * self.coefficient


class Binomial:
    """Represents the sum of two terms (with an optional multiplier)."""

    basic_binomial_pattern = re.compile(
        # r"^(-?\d+\.?\d*|-)?([a-z])?(?:\^(-?\d+\.?\d*))?\s*(\+|\-)\s*(-?\d+\.?\d*|-)?([a-z])?(?:\^(-?\d+\.?\d*))?$"
        # r"^(-?\d+\.?\d*|-)?\*?\((-?\d+\.?\d*|-)?([a-z])?(?:\^(-?\d+\.?\d*))?\s*(\+|\-)\s*(-?\d+\.?\d*|-)?([a-z])?(?:\^(-?\d+\.?\d*))?\)"
        r"^(-?\d+\.?\d*|-)?([a-z])?(?:\^(-?\d+\.?\d*))?\*?\((-?\d+\.?\d*|-)?([a-z])?(?:\^(-?\d+\.?\d*))?\s*(\+|\-)\s*(-?\d+\.?\d*|-)?([a-z])?(?:\^(-?\d+\.?\d*))?\)"
    )

    def __init__(
        self,
        # coefficient: int | float | str | None = None,
        multiplier: str | Term | Binomial | None = None,
        left: Term | Binomial | None = None,
        right: Term | Binomial | None = None,
    ):
        expression = self.basic_binomial_pattern.match(str(multiplier))

        if expression and not left and not right:
            (
                multiplier_coefficient,
                multiplier_variable,
                multiplier_power,
                left_coefficient,
                left_variable,
                left_power,
                sign,
                right_coefficient,
                right_variable,
                right_power,
            ) = expression.groups()

            if not left_power:
                left_power = 1

            if not right_power:
                right_power = 1

            if not multiplier_power:
                multiplier_power = 1

            self.multiplier = Term(
                multiplier_coefficient, multiplier_variable, float(multiplier_power)
            )
            self.left = Term(left_coefficient, left_variable, float(left_power))
            self.right = Term(right_coefficient, right_variable, float(right_power))

            # print(f"{right_coefficient}{right_variable}{right_power}")
            if sign == "-":
                self.right.coefficient *= -1

            # self.coefficient = coefficient if coefficient != None else 1

            # if int(float(self.coefficient)) - float(self.coefficient) == 0:
            #     self.coefficient = int(self.coefficient)
            # else:
            #     self.coefficient = float(self.coefficient)
            return

        # self.coefficient = coefficient if coefficient != None else 1

        # if int(float(self.coefficient)) - float(self.coefficient) == 0:
        #     self.coefficient = int(self.coefficient)
        # else:
        #     self.coefficient = float(self.coefficient)

        self.multiplier = multiplier if multiplier else Term(1)
        self.left = left if left else Term(1)
        self.right = right if right else Term(1)

    def __repr__(self) -> str:
        if self.multiplier == Term(1):
            multiplier = ""
        else:
            multiplier = self.multiplier
        return f"Binomial('{multiplier!s}({self.left!s} + {self.right!s})')"

    def __add__(self, __value: Binomial | Term) -> Binomial | Term:
        self_simple = self.simplify()
        if type(__value) == Binomial:
            other_simple = __value.simplify()
        else:
            other_simple = __value

        if type(other_simple) == Term and type(self_simple) == Term:
            if self_simple.variable == other_simple.variable:
                return self_simple + __value

        if type(other_simple) == Binomial and type(self_simple) == Binomial:
            if (
                self_simple.left == other_simple.left
                and self_simple.right == other_simple.right
            ):
                # breakpoint()
                new_coef = self_simple.coefficient + other_simple.coefficient

                return Binomial(new_coef, self.left, self.right)

            # if self_simple and other_simple:
            #     if self_simple.variable == other_simple.variable:
            #         return self_simple + other_simple

        raise UnlikeTermsError

    def simplify(self) -> Term | Binomial:
        if (
            self.left.variable == self.right.variable
            and self.left.power == self.right.power
        ):
            # print(f"{self.left.variable}{self.right.variable}")
            return Term(self.coefficient) * (self.left + self.right)

        else:
            return self


class Expression:
    """Represents a sum of terms and/or binomials."""

    def __init__(self, terms: list[Term | Binomial] | None = None):
        self.terms = terms


class Equation:
    """Represents a flat equation in one or more variables."""

    def __init__(self, left=list[Term], right=list[Term]):
        pass


class Factor:
    """Represents a multiplicative factor."""

    def __init__(self, terms=list[Term] | Term, coefficient=int | None):
        self.terms = terms


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
                xs.append(f"{random.randint(2,4)}({variable}+{random.randint(2,5)})")
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
    target = Decimal(n) * 100
    return Decimal(target * round(random.randint(1, 100) / target)) / Decimal(100)


def generate_decimal_x_equation(freq_weight: int = 1000) -> tuple[str, str]:
    """Generate an equation with decimal coefficients.
    Problem Description:
    Solving Equations with Decimal Coefficients"""

    variable = random.choice(["a", "b", "c", "x", "y", "m", "n"])

    left_c = Decimal(0)
    right_c = Decimal(random.randint(-9, 9)) + random.randint(0, 3) * random_decimal(
        "0.25"
    )
    delta_c = Decimal(random.randint(-9, 9)) + random.randint(0, 3) * random_decimal(
        "0.25"
    )
    left_c += delta_c
    right_c += delta_c

    left_x = random.randint(1, 4) * Decimal("0.25")
    right_x = Decimal(0)
    delta_x = Decimal(random.randint(-3, 3))
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
    assignment_count: int = 1,
    problem_count: int = 4,
    debug: bool = False,
    threshold: int = 0,
    problem_set=None,  # type: ignore
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
            counts=[problem.weight for problem in problem_set],
        )

        problems: list[Problem] = [problem.generate() for problem in problem_generators]

        for k, problem in enumerate(problems):
            if k % 3 == 0 and k != 0:
                problem_statement += r"\newpage"

            problem_statement += problem.problem
            solution_set += rf"{k+1}: {problem.solution}\;\;"

            _SAVE_DATA["weights"][problem.name] = int(
                _SAVE_DATA["weights"][problem.name] * 0.9
            )

        # for k, generator in enumerate(problem_generators):
        #     if k % 3 == 0 and k != 0:
        #         problem_statement += r"\newpage"

        #     problem, solution = generator.generate()
        #     problem = rf"\item {problem}"
        #     problem_statement += problem
        #     solution_set += rf"{k+1}: {solution}\;\;"

        #     _SAVE_DATA["weights"][generator.name] = int(
        #         _SAVE_DATA["weights"][generator.name] * 0.9
        #     )

        # for k, generator in enumerate(generators):
        #     if k % 3 == 0 and k != 0:
        #         problem_statement += r"\newpage"

        #     # call candidate generator function
        #     candidate = globals()[generator](freq_weight=WEIGHTS[k])
        #     _SAVE_DATA["weights"][generator] = int(
        #         _SAVE_DATA["weights"][generator] * 0.9
        #     )
        #     solution += rf"{k+1}: {candidate[1]}\;\;"
        #     problem = rf"\item {candidate[0]}"
        #     problem_statement += problem

        page_footer = r"\end{enumerate}"
        # solution += r"\\"
        solutions.append(solution_set)
        pages.append(page_header + problem_statement + page_footer)

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

    # long_descriptions = [
    #     f"{description} ({_SAVE_DATA['weights'][_DESCRIPTION_TO_NAME[description]]})"
    #     for name in _PROBLEM_GENERATORS
    # ]

    global _PROBLEM_GENERATORS

    problem_indeces = survey.routines.basket(
        "Select problem types to include.  (Numbers indicate relative frequency rate.)",
        options=[problem.long_description for problem in _ALL_PROBLEMS],
    )

    selected_problems = [_ALL_PROBLEMS[i] for i in problem_indeces]  # type: ignore

    # long_descriptions: dict[str, str] = {
    #     name: f"{_NAME_TO_DESCRIPTION[name]} ({_SAVE_DATA['weights'][name]})"
    #     for name in _PROBLEM_GENERATORS
    # }

    # problem_indeces = survey.routines.basket(
    #     "Select problem types to include.  (Numbers indicate relative frequency rate.)",
    #     options=long_descriptions.values(),
    # )

    # problem_types = [k: f"{_NAME_TO_DESCRIPTION}" for ]

    # if problem_types:
    #     _PROBLEM_GENERATORS = [
    #         k for k, v in long_descriptions.items() if v in [problem_types
    #     ]

    start_date = survey.routines.datetime(
        "Select assignment date: ",
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

    days = [
        start_date + datetime.timedelta(days=i) for i in range(assignment_count + 1)
    ]

    global _DATES
    _DATES = [
        f"{_WEEKDAYS[day.weekday()]} {_MONTHS[day.month]} {day.day}, {day.year}"
        for day in days
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
