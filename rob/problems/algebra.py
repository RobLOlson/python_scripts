import math
import random
import re
from decimal import Decimal
from fractions import Fraction

_CONSTANT_COEF_DOT_PATTERN = re.compile(r"(\d+\s*)\\cdot(\s[a-zA-Z])")
_VARIABLES = ["x", "y", "z"]


def get_sympy():
    import sympy

    return sympy


def random_factor(var, min_coef: int = 1, max_coef: int = 9, min_order: int = 1, max_order: int = 1):
    return random.randint(min_coef, max_coef) * (var ** random.randint(min_order, max_order))


# To write a new algebra problem generator you must:
# * begin the function name with 'generate'
# * return a 2-tuple of strings ('TeX problem', 'TeX answer')
# * the last line of the doc string should name the problem type


def generate_numerical_expression_to_ones(freq_weight: int = 1000, difficulty: int = None) -> tuple[str, str]:
    """Generate numerical expression to ones problems.
    Problem Description:
    Using Ones in Numerical Expressions"""

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))

    base_1: int = random.randint(1, 4)
    base_2: int = random.randint(1, 4)
    power_1: int = random.randint(1, 3) if difficulty > 2 else 1
    power_2: int = random.randint(1, 3) if difficulty > 2 else 1
    operation: str = random.choice(["+", "-", r"\cdot", r"\over"] if difficulty > 2 else ["+", "-"])

    expression = f"{{{base_1}{'^' + str(power_1) if power_1 > 1 else ''} {operation} {base_2}{'^' + str(power_2) if power_2 > 1 else ''} }}"
    answer = f"{{ (1 {'+1' * (base_1 - 1)}) ^ {{(1{'+1' * (power_1 - 1)})}} {operation} (1{'+1' * (base_2 - 1)}) ^ {{(1{'+1' * (power_2 - 1)})}} }}"

    problem_statement = rf"Replace all numbers with ones without changing the value. Fewer ones are better. \\For example, \({expression}={answer}\)."

    base_1: int = random.randint(1, 4)
    base_2: int = random.randint(1, 4)
    power_1: int = random.randint(1, 3)
    power_2: int = random.randint(1, 3)
    operation: str = random.choice(["+", "-", r"\cdot", r"\over"])

    expression = f"{{{base_1}{'^' + str(power_1) if power_1 > 1 else ''} {operation} {base_2}{'^' + str(power_2) if power_2 > 1 else ''} }}"
    answer = rf"{{ (1 {'+1' * (base_1 - 1)}) ^ {{(1{'+1' * (power_1 - 1)})}} {operation} (1{'+1' * (base_2 - 1)}) ^ {{(1{'+1' * (power_2 - 1)})}} }}"

    return (
        rf"{problem_statement} \\ \\ \({expression}\) \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\",
        rf"\({answer}\)",
    )


def generate_fraction_addition(freq_weight: int = 1000, difficulty: int = None) -> tuple[str, str]:
    """Generate fraction addition problems.
    Problem Description:
    Adding Fractions"""

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))

    def lcm(a, b, c=None):
        """Calculate the least common multiple of three numbers."""
        if c is None:
            return abs(a * b) // math.gcd(a, b)
        if c is not None:
            return abs(a * b * c) // math.gcd(a, b, c)
        return abs(a * b) // math.gcd(a, b)

    def simplify_fraction(numerator, denominator):
        """Simplify a fraction to its lowest terms."""
        common_divisor = math.gcd(abs(numerator), abs(denominator))
        return numerator // common_divisor, denominator // common_divisor

    # Generate denominators based on difficulty
    if difficulty <= 1:
        # Easy: denominators 2-5
        denom1 = random.choice([2, 3, 4, 5])
        denom2 = random.choice([2, 3, 4, 5])
    elif difficulty == 2:
        # Medium: denominators 2-8
        denom1 = random.choice([2, 3, 4, 5, 6, 7, 8])
        denom2 = random.choice([2, 3, 4, 5, 6, 7, 8])
    else:
        # Hard: denominators 2-12
        denom1 = random.choice([2, 3, 4, 5, 6])
        denom2 = random.choice([2, 3, 4, 5, 6])
        denom3 = random.choice([2, 3, 4, 5, 6])

    # Generate numerators
    if difficulty <= 1:
        # Easy: numerators 1-5
        num1 = random.randint(1, 5)
        num2 = random.randint(1, 5)
    elif difficulty == 2:
        # Medium: numerators 1-8
        num1 = random.randint(1, 8)
        num2 = random.randint(1, 8)
    else:
        # Hard: numerators 1-12
        num1 = random.randint(1, 6)
        num2 = random.randint(1, 6)
        num3 = random.randint(1, 6)

    # Ensure fractions are proper (numerator < denominator) for easier problems
    if difficulty <= 1:
        num1 = min(num1, denom1 - 1)
        num2 = min(num2, denom2 - 1)

    frac1 = Fraction(num1, denom1)
    frac2 = Fraction(num2, denom2)

    result = frac1 + frac2

    if difficulty > 2:
        frac3 = Fraction(num3, denom3)
        result += frac3

    # Create the problem
    if difficulty > 2:
        problem = (
            f"\\frac{{{num1}}}{{{denom1}}} + \\frac{{{num2}}}{{{denom2}}} + \\frac{{{num3}}}{{{denom3}}}"
        )
    else:
        problem = f"\\frac{{{num1}}}{{{denom1}}} + \\frac{{{num2}}}{{{denom2}}}"

    # Format the answer
    answer = f"\\dfrac{{{result.numerator}}}{{{result.denominator}}}"

    problem_statement = "Add the following fractions and express your answer as a simplified fraction."

    return (
        rf"{problem_statement} \\ \\ \({problem}\) \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\",
        rf"\({answer}\)",
    )


def generate_integer_factorization(freq_weight: int = 1000, difficulty: int = None) -> tuple[str, str]:
    """Generate integer factorization.
    Problem Description:
    Factorize Integers"""

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))

    primes = [2, 3, 5, 7]
    sole_factor = random.choice(primes)
    leftover_primes = set(primes) - {sole_factor}
    perfect_square = random.choice(list(leftover_primes))

    expression = f"{sole_factor * perfect_square * perfect_square}"
    answer = f"{perfect_square}\\cdot{perfect_square}\\cdot{sole_factor}"

    if difficulty > 2:
        square_1, square_2 = random.choices(population=list(leftover_primes), k=2)
        expression = f"{sole_factor * square_1 * square_1 * square_2 * square_2}"
        answer = f"{square_1}\\cdot{square_1}\\cdot{sole_factor}\\cdot{square_2}\\cdot{square_2}"

    problem_statement = "Factor the integer into a product of its primes."

    return (
        rf"{problem_statement} \\ \\ \({expression}\) \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\",
        rf"\({answer}\)",
    )


def generate_compute_average_of_integers(
    freq_weight: int = 1000, difficulty: int | None = None
) -> tuple[str, str]:
    """Generate computing the average of integers.
    Problem Description:
    Average of Integers"""

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))

    # Choose count and range based on difficulty
    if difficulty > 2:
        count = random.choice([3, 4])
        low, high = 1, 20
    elif difficulty == 1:
        count = random.choice([4, 5, 6])
        low, high = -20, 20
    else:
        count = random.choice([5, 6, 7])
        low, high = -50, 50

    numbers: list[int] = [random.randint(low, high) for _ in range(count)]
    total = sum(numbers)
    n = len(numbers)

    # LaTeX for the list of integers: {a, b, c}
    numbers_tex = ", ".join(str(x) for x in numbers)
    expression = rf"\{{{numbers_tex}\}}"

    # Compute simplified average
    if total % n == 0:
        answer_tex = f"{total // n}"
    else:
        frac = Fraction(total, n)
        answer_tex = rf"\dfrac{{{frac.numerator}}}{{{frac.denominator}}}"

    prompt = "Compute the average of the following integers:"

    return (
        rf"{prompt}\({expression}\) \\ \\ \\ \\ \\ \\  ",
        rf"\({answer_tex}\)",
    )


def generate_radical_simplification(freq_weight: int = 1000, difficulty: int = None) -> tuple[str, str]:
    """Generate radical simplification.
    Problem Description:
    Simplify Radicals"""

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))

    primes = [2, 3, 5, 7]
    sole_factor = random.choice(primes)
    leftover_primes = set(primes) - {sole_factor}

    if difficulty > 2:
        squares = random.choices(population=list(leftover_primes), k=2)
        perfect_square = squares[0] * squares[1]
    else:
        perfect_square = random.choice(list(leftover_primes))

    expression = f"\\sqrt{{{sole_factor * perfect_square * perfect_square}}}"
    answer = f"{perfect_square}\\sqrt{{{sole_factor}}}"

    problem_statement = "Remove all perfect squares from inside the square root."

    return (
        rf"{problem_statement} \\ \\ \({expression}\) \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\",
        rf"\({answer}\)",
    )


def generate_simple_x_expression(freq_weight: int = 1000, difficulty: int = None) -> tuple[str, str]:
    """Generate an expression in one variable where coefficients and exponents are all integers.
    Problem Description:
    Simplifying Expressions"""

    sympy = get_sympy()

    if difficulty is None:
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


def generate_function_evaluation(freq_weight: int = 1000, difficulty: int = None) -> tuple[str, str]:
    """Generate a function in one variable where coefficients and exponents are all integers.
    Problem Description:
    Evaluating Functions"""

    sympy = get_sympy()

    if difficulty is None:
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
    prompt = f"Evaluate the function.  \\\\ \\begin{{align*}} f({var}) &= {latex_expression} \\\\ f({constant})&=? \\end{{align*}}"
    return (
        rf"{prompt} \\ \\ \\ \\ \\ \\ \\ \\ \\",
        rf"\({solution!s}\)",
    )


def generate_simple_x_equation(freq_weight: int = 1000, difficulty: int = None) -> tuple[str, str]:
    """Generate a single variable equation.
    Problem Description:
    Solving Equations with One Variable"""

    sympy = get_sympy()

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))
    var = random.choice(sympy.symbols("a b c x y z m n"))
    if difficulty > 1:
        coef = random_decimal("0.05") + random.randint(-4, 4)
        coef = coef if coef else 1

    else:
        coef = random.randint(-2, 4)
        coef = coef if coef else 1

    left_string = f"{coef} * ({random.randint(1, 4)} * {var} + {random.randint(1, 9)})"
    right_string = f"{random.randint(1, 7)} * {var} + {random.randint(1, 9)}"

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


def generate_decimal_x_equation(freq_weight: int = 1000, difficulty: int = None) -> tuple[str, str]:
    """Generate an equation with decimal coefficients.
    Problem Description:
    Solving Equations with Decimal Coefficients"""

    sympy = get_sympy()

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))
    var = random.choice(sympy.symbols("a b c x y z m n"))
    if difficulty > 1:
        denom = random.randint(2, 9)
    else:
        denom = random.randint(2, 5)

    left_string = (
        f"({random.randint(1, 4)} / {denom}) * ({random.randint(1, 4)} * {var} + {random.randint(-4, 4)})"
    )
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


def generate_variable_isolation(freq_weight: int = 1000, difficulty: int = None) -> tuple[str, str]:
    """Generate a linear equation with 2 variables.
    Problem Description:
    Isolating Variables in a Linear Equation"""

    # variable = random.choice(["x"])
    # unknown = random.choice(["y"])

    term_count = random.randint(1, 3)
    terms = [
        f"{random.choice([-1, -2, -3, 1, 2, 3])}x",
        f"{random.choice([-1, -2, -3, 1, 2, 3])}y",
    ]

    for term in range(term_count):
        choice = random.choice(["variable", "unknown", "constant"])
        match choice:
            case "variable":
                terms.append(f"{random.choice([-1, -2, -3, 1, 2, 3])}x")
            case "unknown":
                terms.append(f"{random.choice([-1, -2, -3, 1, 2, 3])}y")
            case "constant":
                terms.append(f"{random.choice([-1, -2, -3, 1, 2, 3])}")

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
    problem_statement = "Isolate the variable y.  Find the x-intercept and the y-intercept."

    expression = f"{left} = {right}"

    return (
        rf"{problem_statement} \\ \\ \({expression}\) \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\",
        "Solution here.",
    )


def generate_system_of_equations(freq_weight: int = 1000, difficulty: int = None) -> tuple[str, str]:
    """Generate a system of equations.
    Problem Description:
    Solving a System of Equations"""

    # a * y - a * a * b * x = a * y_sol - a * a * b * x_sol

    sympy = get_sympy()

    x = sympy.symbols("x")
    y = sympy.symbols("y")

    match freq_weight:
        case freq_weight if freq_weight < 10:
            solution_set = [n / 10 for n in range(-30, 30)]

        case freq_weight if 10 < freq_weight < 100:
            solution_set = [n / 4 for n in range(-12, 12)]

        case _:
            solution_set = list(range(-3, 3))

    x_sol = random.choice(solution_set)
    y_sol = random.choice(solution_set)

    a_1, a_2 = random.sample([-3, -2, -1, 1, 2, 3], 2)
    b_1, b_2 = random.sample([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5], 2)

    # left_1 = sympy.latex(sympy.sympify(f"{a_1} * {y} - {a_1 * a_1 * b_1} * {x}"))
    # right_1 = sympy.latex(sympy.sympify(f"{a_1} * {y_sol} - {a_1 * a_1 * b_1} * {x_sol}"))
    # left_2 = sympy.latex(sympy.sympify(f"{a_2} * {y} - {a_2 * a_2 * b_2} * {x}"))
    # right_2 = sympy.latex(sympy.sympify(f"{a_2} * {y_sol} - {a_2 * a_2 * b_2} * {x_sol}"))

    left_1 = sympy.latex(sympy.sympify(f"{a_1} * {y} - {b_1} * {x}"))
    right_1 = sympy.latex(sympy.sympify(f"{a_1} * {y_sol} - {b_1} * {x_sol}"))
    left_2 = sympy.latex(sympy.sympify(f"{a_2} * {y} - {b_2} * {x}"))
    right_2 = sympy.latex(sympy.sympify(f"{a_2} * {y_sol} - {b_2} * {x_sol}"))

    problem_statement = "Find the solution (x, y) to the system of equations."

    expression = rf"\begin{{align*}}{left_1} &= {right_1} \\ {left_2} &= {right_2}\end{{align*}}"

    return (
        rf"{problem_statement} \\ \\ {expression} \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\",
        f"({x_sol}, {y_sol})",
    )


def generate_arithmetic_sequence(freq_weight: int = 1000, difficulty: int = None) -> tuple[str, str]:
    """Generate an arithmetic sequence.
    Problem Description:
    Arithmetic Sequences"""

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))

    step = random.choice([-4, -3, -2, 2, 3, 4, 5])

    init = random.randint(-9, 9)

    if difficulty > 2:
        step_delta = random.choice([0.1, 0.2, 0.3, 0.4, 0.5])
        step += step_delta

    sequence = ", ".join([str(init + step * count) for count in range(0, 4)])
    sequence += ", ..."

    problem_statement = "What is the next term in the arithmetic sequence?"

    return (
        rf"{problem_statement} \\ \\ {sequence} \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\",
        f"{init + 4 * step}",
    )


def generate_arithmetic_sequence_formula(freq_weight: int = 1000, difficulty: int = None) -> tuple[str, str]:
    """Generate an arithmetic sequence formula.
    Problem Description:
    Arithmetic Sequence Formulas"""

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))

    step = random.choice([-4, -3, -2, 2, 3, 4, 5])

    init = random.randint(-9, 9)

    if difficulty > 2:
        step_delta = random.choice([0.1, 0.2, 0.3, 0.4, 0.5])
        step += step_delta

    sequence = ", ".join([str(init + step * count) for count in range(0, 4)])
    sequence += ", ..."

    problem_statement = (
        f"Find a function that models the arithmetic sequence. Note that f(1) should equal {init}."
    )

    return (
        rf"{problem_statement} \\ \\ {sequence} \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\",
        f"\\(f[x] = {step} \\cdot x + {init}\\)",
    )


def generate_geometric_sequence(freq_weight: int = 1000, difficulty: int = None) -> tuple[str, str]:
    """Generate an geometric sequence.
    Problem Description:
    Geometric Sequences"""

    sympy = get_sympy()

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))

    step = random.choice([2, 3, 4, 5])
    init = random.choice([-10, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 10])

    sequence = [str(init * step**count) for count in range(0, 5)]

    if difficulty > 1:
        denom_step = random.choice(list({2, 3, 4, 5} - {step}))
        sequence = [
            sympy.latex(sympy.sympify(f"{init}*({step}/{denom_step})**{count}")) for count in range(0, 5)
        ]

    if random.random() > 0.5:
        sequence = list(reversed(sequence))

    answer = sequence[-1]
    sequence = sequence[:-1]

    sequence = ", ".join(sequence)
    sequence += ", ..."

    problem_statement = "What is the next term in the geometric sequence?"

    return (
        rf"{problem_statement} \\ \\ \({sequence}\) \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\",
        rf"\({answer}\)",
    )


def generate_geometric_sequence_evaluation(
    freq_weight: int = 1000, difficulty: int = None
) -> tuple[str, str]:
    """Generate geometric sequence formula evaluation.
    Problem Description:
    Evaluate Geometric Sequence Formula"""

    sympy = get_sympy()

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))

    step = random.choice([2, 3, 4, 5])
    init = random.choice([-10, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 10])

    n = random.randint(1, 5)
    match n:
        case 1:
            evaluate_at = "1st"
        case 2:
            evaluate_at = "2nd"
        case 3:
            evaluate_at = "3rd"
        case _:
            evaluate_at = f"{n}th"

    formula = f"f(n)={init} \\cdot ({step})^{{n-1}}"
    answer = init * step ** (n - 1)

    if difficulty > 2:
        denom_step = random.choice(list({2, 3, 4, 5} - {step}))
        formula = f"f(n)={init} \\cdot (\\frac{{{step}}}{{{denom_step}}})^{{n-1}}"
        answer = sympy.sympify(f"{init} * ({step} / {denom_step}) ** {n - 1}")

    problem_statement = f"What is the {evaluate_at} term in the sequence?"

    return (
        rf"{problem_statement} \\ \\ \({formula}\) \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\",
        rf"\({answer}\)",
    )


def generate_power_expression(freq_weight: int = 1000, difficulty: int = None) -> tuple[str, str]:
    """Generate power evaluation.
    Problem Description:
    Evaluate Power Expression"""

    global _VARIABLES

    operation = random.choice(["multiply", "divide"])
    glyph = random.choice(_VARIABLES + ["2", "3", "4", "5", "6", "7", "8", "9"])
    exponent_1 = random.choice(["-7", "-6", "-5", "-4", "-3", "-2", "2", "3", "4", "5", "6", "7"])
    exponent_2 = random.choice(["-7", "-6", "-5", "-4", "-3", "-2", "2", "3", "4", "5", "6", "7"])

    if operation == "multiply":
        expression = f"({glyph}^{{{exponent_1}}})({glyph}^{{{exponent_2}}})"
        answer = f"{glyph}^{{{str(int(exponent_1) + int(exponent_2))}}}"
    else:
        expression = f"\\dfrac{{{glyph}^{{{exponent_1}}}}}{{{glyph}^{{{exponent_2}}}}}"
        answer = f"{glyph}^{{{str(int(exponent_1) - int(exponent_2))}}}"

    problem_statement = f"Rewrite the expression in the form of \\({glyph}^n\\)."

    return (
        rf"{problem_statement} \\ \\ \({expression}\) \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\",
        rf"\({answer}\)",
    )


def generate_radical_simplification_with_vars(
    freq_weight: int = 1000, difficulty: int = None
) -> tuple[str, str]:
    """Generate variable radical simplification.
    Problem Description:
    Simplify Radicals With Variables"""

    global _VARIABLES

    sympy = get_sympy()

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))

    primes = [2, 3, 5, 7]
    sole_factor = random.choice(primes)
    leftover_primes = set(primes) - {sole_factor}
    glyph = random.choice(_VARIABLES)
    glyph_power = random.choice(range(1, 8))

    perfect_square = random.choice(list(leftover_primes))

    perfect_part = glyph_power // 2
    radical_part = glyph_power % 2
    if not radical_part:
        radical_part = ""

    if glyph_power == 1:
        glyph_power = ""

    if perfect_part == 1:
        perfect_part = ""

    expression = f"\\sqrt{{{sole_factor * perfect_square * perfect_square}{glyph}^{{{glyph_power}}}}}"

    answer = f"{perfect_square}{glyph if perfect_part else ''}^{{{perfect_part}}}\\sqrt{{{sole_factor}{glyph if radical_part else ''}^{{{radical_part}}}}}"

    if difficulty > 2:
        glyph_power = random.choice(range(1, 8))
        expression_1 = f"sqrt({sole_factor * perfect_square * perfect_square} * {glyph} ** {glyph_power})"

        latex_1 = sympy.latex(sympy.sympify(expression_1, evaluate=False))

        sole_factor_2 = random.choice(primes)
        leftover_primes_2 = set(primes) - {sole_factor_2}
        glyph_power_2 = random.choice(range(1, 8))
        perfect_square_2 = random.choice(list(leftover_primes_2))

        expression_2 = (
            f"sqrt({sole_factor_2 * perfect_square_2 * perfect_square_2} * {glyph} ** {glyph_power_2})"
        )
        latex_2 = sympy.latex(sympy.sympify(expression_2, evaluate=False))
        expression = f"{latex_1} {latex_2}"
        simplified_expr, val = sympy.posify(sympy.sympify(f"{expression_1} * {expression_2}"))
        answer = sympy.latex(simplified_expr.subs(val))

    problem_statement = (
        f"Remove all perfect squares from inside the square root.  Assume {glyph} is positive."
    )

    return (
        rf"{problem_statement} \\ \\ \({expression}\) \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\",
        rf"\({answer}\)",
    )


def generate_binomial_product_expansion(freq_weight: int = 1000, difficulty: int = None) -> tuple[str, str]:
    """Generate binomial product expansion.
    Problem Description:
    Binomial Product Expansion"""

    global _VARIABLES

    sympy = get_sympy()

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))

    glyph = random.choice(_VARIABLES)
    constant_1 = random.choice(["-6", "-5", "-4", "-3", "-2", "-1", "1", "2", "3", "4", "5", "6"])
    constant_2 = random.choice(["-6", "-5", "-4", "-3", "-2", "-1", "1", "2", "3", "4", "5", "6"])
    coef_1 = random.choice(["-5", "-4", "-3", "-2", "2", "3", "4", "5"])
    coef_2 = random.choice(["-5", "-4", "-3", "-2", "2", "3", "4", "5"])

    match difficulty:
        case difficulty if difficulty <= 1:
            expression = f"({glyph} + {constant_1})*({glyph} + {constant_2})"
        case difficulty if difficulty == 2:
            expression = f"({coef_1}*{glyph} + {constant_1}) * ({glyph} + {constant_2})"
        case difficulty if difficulty > 3:
            left_1 = f"{coef_1}*{glyph}"
            right_1 = constant_1
            if random.random() > 0.5:
                left_1, right_1 = right_1, left_1

            left_2 = f"{coef_2}*{glyph}"
            right_2 = constant_2
            if random.random() > 0.5:
                left_2, right_2 = right_2, left_2

            expression = f"({left_1} + {right_1}) * ({left_2} + {right_2})"
        case _:
            expression = f"({glyph} + {constant_1})*({glyph} + {constant_2})"

    expression_latex = sympy.latex(sympy.sympify(expression, evaluate=False))
    answer_latex = sympy.latex(sympy.expand(expression))

    problem_statement = "Expand the binomial product into a standard form polynomial. (Standard form looks like \\(ax^2 + bx + c\\))."

    return (
        rf"{problem_statement} \\ \\ \({expression_latex}\) \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\",
        rf"\({answer_latex}\)",
    )


def generate_multiply_difference_of_squares(
    freq_weight: int = 1000, difficulty: int = None
) -> tuple[str, str]:
    """Generate multiply difference of squares binomial.
    Problem Description:
    Multiply Difference of Squares Binomial"""

    global _VARIABLES

    sympy = get_sympy()

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))

    glyph = random.choice(_VARIABLES)
    constant = random.choice(["1", "2", "3", "4", "5", "6", "7", "8", "9"])
    coef = random.choice(["2", "3", "4", "5"])

    match difficulty:
        case difficulty if difficulty <= 2:
            expression = f"({glyph} + {constant})*({glyph} - {constant})"
        case difficulty if difficulty > 2:
            expression = f"({coef}*{glyph} + {constant}) * ({coef}*{glyph} - {constant})"
        case _:
            expression = f"({glyph} + {constant})*({glyph} - {constant})"

    expression_latex = sympy.latex(sympy.sympify(expression, evaluate=False))
    answer_latex = sympy.latex(sympy.expand(expression))

    problem_statement = "Expand the binomial product into a standard form polynomial. (Standard form looks like \\(ax^2 + bx + c\\))."

    return (
        rf"{problem_statement} \\ \\ \({expression_latex}\) \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\",
        rf"\({answer_latex}\)",
    )


def generate_multiply_squares_of_binomials(
    freq_weight: int = 1000, difficulty: int = None
) -> tuple[str, str]:
    """Generate multiply squares of binomials.
    Problem Description:
    Multiply Squares of Binomials"""

    global _VARIABLES

    sympy = get_sympy()

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))

    glyph = random.choice(_VARIABLES)
    constant = random.choice(["1", "2", "3", "4", "5", "6", "7", "8", "9"])
    coef = random.choice(["2", "3", "4", "5"])

    match difficulty:
        case difficulty if difficulty <= 1:
            expression = f"({glyph} + {constant})**2"
        case difficulty if difficulty == 2:
            expression = f"({coef}*{glyph} + {constant})**2"
        case difficulty if difficulty > 2:
            left = f"{coef}*{glyph}"
            right = constant
            if random.random() > 0.5:
                left, right = right, left

            expression = f"({left} + {right})**2"
            if random.random() > 0.5:
                expression.replace("+", "-")
        case _:
            expression = f"({glyph} + {constant})*({glyph} - {constant})"

    expression_latex = sympy.latex(sympy.sympify(expression, evaluate=False))
    answer_latex = sympy.latex(sympy.expand(expression))

    problem_statement = "Expand the binomial product into a standard form polynomial.  (Standard form looks like \\(ax^2 + bx + c\\))."

    return (
        rf"{problem_statement} \\ \\ \({expression_latex}\) \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\",
        rf"\({answer_latex}\)",
    )


def generate_average_rate_of_change_of_polynomial(
    freq_weight: int = 1000, difficulty: int = None
) -> tuple[str, str]:
    """Generate average rate of change of a polynomial.
    Problem Description:
    Average Rate of Change of a Polynomial"""

    sympy = get_sympy()
    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))

    # Difficulty controls degree and number complexity
    match difficulty:
        case d if d <= 1:
            deg = 1
            coef_range = (1, 3)
        case 2:
            deg = 2
            coef_range = (1, 5)
        case _:
            deg = 3
            coef_range = (1, 7)

    x = sympy.Symbol(random.choice(_VARIABLES))
    # Generate random coefficients for a degree-1/2/3 polynomial
    coeffs = [random.randint(coef_range[0], coef_range[1])]
    for i in range(deg):
        # Allow negatives for non-leading coefficients, and prevent leading zero
        min_coef = -coef_range[1] if i < deg else 1
        max_coef = coef_range[1]
        coeffs.append(random.randint(min_coef, max_coef))
    # Compose polynomial
    polynomial = sum(coeff * x**power for power, coeff in enumerate(reversed(coeffs)))

    # Pick interval [a, b], a != b, from -5 to 5
    a, b = random.sample(range(-5, 6), 2)
    if a > b:
        a, b = b, a

    # Prepare TeX for the polynomial and interval
    poly_tex = sympy.latex(polynomial)
    interval_tex = rf"[{a},\,{b}]"

    # Compute average rate of change
    fa, fb = polynomial.subs(x, a), polynomial.subs(x, b)
    rate_num = fb - fa
    rate_den = b - a
    # Reduce fraction where possible
    rate = sympy.simplify(rate_num / rate_den)
    answer_tex = sympy.latex(rate)

    problem_statement = rf"What is the average rate of change of \( f(x) = {poly_tex} \) over the interval \( {interval_tex} \)?"

    return (
        rf"{problem_statement} \\ \\ \\ \\ \\ \\ \\",
        rf"\({answer_tex}\)",
    )


def generate_adding_polynomials(freq_weight: int = 1000):
    """
    Generate a problem asking for the difference P - Q, where P and Q are random quadratic polynomials,
    and the answer is expected in standard form.

    Adding/subtracting polynomials."""

    # Difficulty: choose coefficient size by freq_weight (lower freq_weight == harder)
    import random

    import sympy

    difficulty = int(3 - (0 if freq_weight < 10 else int(freq_weight // 400)))
    coef_ranges = {
        1: (-3, 3),
        2: (-7, 7),
        3: (-11, 11),
    }
    coef_range = coef_ranges.get(max(1, min(difficulty, 3)), (-3, 3))

    var = sympy.Symbol(random.choice(["x", "b", "y"]))

    # Helper to generate a random quadratic (degree-2) polynomial
    def rand_quadratic():
        # Leading coefficient: avoid 0. Can be negative.
        a = random.choice([i for i in range(coef_range[0], coef_range[1] + 1) if i != 0])
        b_ = random.randint(coef_range[0], coef_range[1])
        c = random.randint(coef_range[0], coef_range[1])
        return a * var**2 + b_ * var + c, (a, b_, c)

    P, (a1, b1, c1) = rand_quadratic()
    Q, (a2, b2, c2) = rand_quadratic()

    # Sometimes ensure some sign/variety
    if random.random() < 0.5:
        Q = -Q
        a2, b2, c2 = -a2, -b2, -c2

    # Render as TeX
    def poly_tex(expr):
        return sympy.latex(sympy.expand(expr))

    problem_statement = (
        rf"\( P = {poly_tex(P)} \)"
        r"<br>"
        rf"\( Q = {poly_tex(Q)} \)"
        r"<br>"
        rf"\( P - Q =\;\;\) ?"
        r"<br>"
        r"Your answer should be a polynomial in standard form."
    )

    answer_poly = sympy.expand(P - Q)
    answer_tex = poly_tex(answer_poly)

    # Remove <br> for output since not all render HTML; just show as lines
    problem_statement = problem_statement.replace("<br>", r"\\")

    return (
        rf"{problem_statement} \\ \\ \\ \\ \\ \\ \\",
        rf"\({answer_tex}\)",
    )


def generate_monomial_multiplication(
    freq_weight: int = 1000, difficulty: int | None = None
) -> tuple[str, str]:
    """Generate multiplication of two monomials sharing a base variable.
    Problem Description:
    Multiplying Monomials"""

    global _VARIABLES

    sympy = get_sympy()

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))

    var = random.choice(_VARIABLES)

    # Coefficient ranges scale with difficulty
    if difficulty <= 1:
        coef_min, coef_max = 1, 6
        allow_negative = False
        exp_max = 3
    elif difficulty == 2:
        coef_min, coef_max = 1, 8
        allow_negative = True
        exp_max = 4
    else:
        coef_min, coef_max = 1, 9
        allow_negative = True
        exp_max = 5

    def rand_coef() -> int:
        c = random.randint(coef_min, coef_max)
        if allow_negative and random.random() < 0.5:
            c = -c
        return c

    def rand_exp() -> int:
        e = random.randint(1, exp_max)
        # Rarely include a negative exponent for hardest difficulty
        if difficulty > 2 and random.random() < 0.2:
            e = -random.randint(1, max(2, exp_max - 1))
        return e

    c1, c2 = rand_coef(), rand_coef()
    e1, e2 = rand_exp(), rand_exp()

    expr = f"({c1}*{var}**{e1})*({c2}*{var}**{e2})"

    problem_latex = sympy.latex(sympy.sympify(expr, evaluate=False))
    answer_latex = sympy.latex(sympy.simplify(sympy.sympify(expr)))

    prompt = "Multiply. Your answer should be a monomial in standard form."

    return (
        rf"{prompt} \\ \\ \({problem_latex}\) \\ \\ \\ \\ \\ \\ \\ \\ \\",
        rf"\({answer_latex}\)",
    )


def generate_rectangle_area_monomial_times_polynomial(
    freq_weight: int = 1000, difficulty: int | None = None
) -> tuple[str, str]:
    """Generate rectangle area from height (monomial) and width (polynomial).
    Problem Description:
    Area as Monomial Times Polynomial"""

    global _VARIABLES

    sympy = get_sympy()

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))

    x = random.choice(_VARIABLES)

    # Determine scales
    if difficulty <= 1:
        coef_range = (1, 5)
        deg_base = random.randint(2, 3)
        allow_negative = False
    elif difficulty == 2:
        coef_range = (1, 7)
        deg_base = random.randint(3, 4)
        allow_negative = True
    else:
        coef_range = (1, 9)
        deg_base = random.randint(3, 5)
        allow_negative = True

    def rc() -> int:
        c = random.randint(*coef_range)
        if allow_negative and random.random() < 0.4:
            c = -c
        return c

    def _term(coef: int, var: str, exp: int) -> str:
        if exp == 0:
            return f"{coef}"
        if exp == 1:
            return f"{coef}*{var}"
        return f"{coef}*{var}**{exp}"

    height_expr = f"{random.randint(*coef_range)}*{x}**{deg_base}"

    a, b, c = rc(), rc(), rc()
    # Ensure leading coefficient nonzero and positive for nicer shapes
    if a == 0:
        a = 1
    if not allow_negative and a < 0:
        a = abs(a)

    width_expr = " + ".join(
        [
            _term(a, x, deg_base),
            _term(b, x, deg_base - 1),
            _term(c, x, deg_base - 2),
        ]
    )

    area_expr = f"({height_expr})*({width_expr})"

    height_tex = sympy.latex(sympy.sympify(height_expr, evaluate=False))
    width_tex = sympy.latex(sympy.sympify(width_expr, evaluate=False))
    answer_tex = sympy.latex(sympy.expand(sympy.sympify(area_expr)))

    statement = (
        rf"A rectangle has a height of \({height_tex}\) and a width of \({width_tex}\). "
        r"Express the area of the entire rectangle. Your answer should be a polynomial in standard form."
    )

    return (
        rf"{statement}\\ \\ \\ \\ \\ \\ \\ \\ \\",
        rf"\({answer_tex}\)",
    )


def generate_expand_monomial_times_trinomial(
    freq_weight: int = 1000, difficulty: int | None = None
) -> tuple[str, str]:
    """Generate expansion of a monomial times a trinomial.
    Problem Description:
    Expand Monomial Times Trinomial"""

    global _VARIABLES

    sympy = get_sympy()

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))

    v = random.choice(_VARIABLES)

    if difficulty <= 1:
        coef_range = (1, 6)
        allow_negative = False
        base_deg = random.randint(2, 3)
    elif difficulty == 2:
        coef_range = (1, 8)
        allow_negative = True
        base_deg = random.randint(3, 4)
    else:
        coef_range = (1, 9)
        allow_negative = True
        base_deg = random.randint(3, 5)

    def rc() -> int:
        c = random.randint(*coef_range)
        if allow_negative and random.random() < 0.5:
            c = -c
        return c

    def _term(coef: int, var: str, exp: int) -> str:
        if exp == 0:
            return f"{coef}"
        if exp == 1:
            return f"{coef}*{var}"
        return f"{coef}*{var}**{exp}"

    monomial = f"{random.randint(*coef_range)}*{v}**{base_deg}"
    a, b, c = rc(), rc(), rc()
    trinomial = " + ".join(
        [
            _term(a, v, base_deg),
            _term(b, v, base_deg - 1),
            _term(c, v, base_deg - 2),
        ]
    )

    expr = f"({monomial})*({trinomial})"

    problem_tex = sympy.latex(sympy.sympify(expr, evaluate=False))
    answer_tex = sympy.latex(sympy.expand(sympy.sympify(expr)))

    prompt = "Expand. Your answer should be a polynomial in standard form."

    return (
        rf"{prompt} \\ \\ \({problem_tex}\) \\ \\ \\ \\ \\ \\ \\ \\ \\",
        rf"\({answer_tex}\)",
    )


def generate_imaginary_radical(freq_weight: int = 1000, difficulty: int | None = None) -> tuple[str, str]:
    """Generate imaginary radical problems.
    Problem Description:
    Imaginary Radicals"""

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))

    # Square-free options for the remaining factor under the radical
    square_free_choices = [1, 2, 3, 5, 6, 7, 10, 11, 13]

    if difficulty <= 1:
        # Easy: negative perfect square only
        outside = random.randint(2, 12)
        s_factor = 1
    elif difficulty == 2:
        # Medium: one square factor times a square-free factor (not 1)
        outside = random.randint(2, 12)
        s_factor = random.choice(square_free_choices[1:])
    else:
        # Hard: product of two square factors times optional square-free factor (may be 1)
        a = random.randint(2, 9)
        b = random.randint(2, 9)
        outside = a * b
        s_factor = random.choice(square_free_choices)

    radicand = -1 * (outside**2) * s_factor

    # Build the simplified answer ± outside * i * sqrt(s)
    answer_parts: list[str] = []
    if outside != 1:
        answer_parts.append(str(outside))
    answer_parts.append("i")
    if s_factor != 1:
        answer_parts.append(rf"\sqrt{{{s_factor}}}")
    answer_core = " ".join(answer_parts)

    prompt = "Express the radical using the imaginary unit, \\(i\\). Express your answer in simplified form."

    expression = rf"\pm \sqrt{{{radicand}}}"

    return (
        rf"{prompt} \\ \\ \({expression}\) \\ \\ \\ \\ \\ \\ \\ \\  ",
        rf"\(\pm {answer_core}\)",
    )


def generate_power_of_i(freq_weight: int = 1000, difficulty: int | None = None) -> tuple[str, str]:
    """Generate powers of i simplification problems.
    Problem Description:
    Powers of i"""

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))

    if difficulty <= 1:
        n = random.randint(0, 20)
    elif difficulty == 2:
        n = random.randint(21, 1000)
    else:
        n = random.randint(-1000, -1)

    k = n % 4
    value_map = {0: "1", 1: "i", 2: "-1", 3: "-i"}
    simplified = value_map[k]

    prompt = "Simplify the expression. Your answer should be one of \\(1, -1, i, -i\\)."

    return (
        rf"{prompt} \\ \\ \(i^{{{n}}}\) \\ \\ \\ \\ \\ \\ \\ \\  ",
        rf"\({simplified}\)",
    )


def generate_complex_addition_subtraction(
    freq_weight: int = 1000, difficulty: int | None = None
) -> tuple[str, str]:
    """Generate complex addition/subtraction problems.
    Problem Description:
    Complex Number Addition/Subtraction"""

    sympy = get_sympy()

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))

    # Coefficient ranges widen with difficulty
    if difficulty >= 2:
        coef_low, coef_high = -9, 9
    elif difficulty == 1:
        coef_low, coef_high = -15, 15
    else:
        coef_low, coef_high = -25, 25

    a = random.randint(coef_low, coef_high)
    b = random.randint(coef_low, coef_high)
    c = random.randint(coef_low, coef_high)
    d = random.randint(coef_low, coef_high)

    op = random.choice(["+", "-"])

    expr_str_1 = f"({a} + ({b})*I)"
    expr_str_2 = f"({c} + ({d})*I)"
    expr_tex_1 = sympy.latex(sympy.sympify(expr_str_1, evaluate=False))
    expr_tex_2 = sympy.latex(sympy.sympify(expr_str_2, evaluate=False))
    answer_tex = sympy.latex(sympy.simplify(sympy.sympify(f"{expr_str_1} {op} {expr_str_2}")))

    prompt = "Add or subtract. Express your answer in the form \\(a + bi\\)."

    return (
        rf"{prompt} \\ \\ \(({expr_tex_1})\)\({op}\)\(({expr_tex_2})\) \\ \\ \\ \\ \\ \\ ",
        rf"\({answer_tex}\)",
    )


def generate_complex_multiplication_divison(
    freq_weight: int = 1000, difficulty: int | None = None
) -> tuple[str, str]:
    """Generate complex multiplication/division problems.
    Problem Description:
    Complex Number Multiplication/Division"""

    sympy = get_sympy()

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))

    # Coefficient ranges widen with difficulty
    if difficulty <= 1:
        coef_low, coef_high = -6, 6
    elif difficulty == 2:
        coef_low, coef_high = -9, 9
    else:
        coef_low, coef_high = -12, 12

    # Random integer helper
    def rint():
        return random.randint(coef_low, coef_high)

    a, b, c, d = rint(), rint(), rint(), rint()
    # Avoid zero denominator in division
    if c == 0 and d == 0:
        c = 1

    # operation = random.choice(["multiply", "divide"])
    operation = "multiply"

    if operation == "multiply":
        # Occasionally use a pure imaginary scalar times a binomial, e.g., 5i*(5+3i)
        if random.random() < 0.5:
            k = random.choice([n for n in range(coef_low, coef_high + 1) if n != 0])
            expr_str = f"({k}*I) * ({a} + ({b})*I)"
        else:
            expr_str = f"({a} + ({b})*I) \\cdot ({c} + ({d})*I)"
        prompt = "Multiply. Express your answer in the form \\(a + bi\\)."
    else:
        expr_str = f"({a} + ({b})*I) / ({c} + ({d})*I)"
        prompt = "Divide. Express your answer in the form \\(a + bi\\)."

    expr_tex = sympy.latex(sympy.sympify(expr_str.replace("\\cdot", "*"), evaluate=False))
    answer_tex = sympy.latex(sympy.simplify(sympy.sympify(expr_str.replace("\\cdot", "*"))))

    return (
        rf"{prompt} \\ \\ \({expr_tex}\) \\ \\ \\ \\ \\ \\ ",
        rf"\({answer_tex}\)",
    )


def generate_real_quadratic_equation_roots(
    freq_weight: int = 1000, difficulty: int | None = None
) -> tuple[str, str]:
    """Generate a quadratic equation root-finding problem.
    Problem Description:
    Quadratic Formula (Real)"""

    sympy = get_sympy()

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))

    x = sympy.Symbol(random.choice(_VARIABLES))

    # Coefficient ranges scale mildly with difficulty
    if difficulty > 1:
        sol_1 = random.randint(2, 5)
        sol_2 = random.randint(6, 9)
    else:
        sol_1 = random.randint(-9, 4)
        sol_2 = random.randint(5, 9)
        if random.random() > 0.5:
            sol_1 += 0.5

    expression = sympy.latex(sympy.expand(sympy.sympify((x - sympy.Rational(sol_1)) * (x - sol_2))))
    # Build prompt and TeX
    problem_statement = rf"Find the values of \({x}\) for which the expression is equal to zero."
    answer_tex = rf"x = {sol_1}\text{{ or }}{sol_2}"

    return (rf"{problem_statement} \\ \\ \({expression}\) \\ \\ \\ \\ \\ \\ \\", rf"\({answer_tex}\)")


def generate_complex_quadratic_equation_roots(
    freq_weight: int = 1000, difficulty: int | None = None
) -> tuple[str, str]:
    """Generate a quadratic equation root-finding problem.
    Problem Description:
    Quadratic Formula (Complex)"""

    sympy = get_sympy()

    if difficulty is None:
        difficulty = int(3 - math.log(freq_weight + 1, 10))

    x = sympy.Symbol(random.choice(_VARIABLES))

    # Coefficient ranges scale mildly with difficulty
    a = random.randint(1, 2)
    b = random.randint(2, 9)

    c_max = b**2 / (4 * a)
    c = random.randint(math.floor(c_max) - 10, math.floor(c_max))

    expression = sympy.latex(sympy.expand(sympy.sympify(a * (x**2) + b * x + c)))
    solution = sympy.latex(sympy.solve(a * (x**2) + b * x + c))

    # Build prompt and TeX
    problem_statement = rf"Find the values of \({x}\) for which the expression is equal to zero."

    return (rf"{problem_statement} \\ \\ \({expression}\) \\ \\ \\ \\ \\ \\ \\", rf"\({solution}\)")
