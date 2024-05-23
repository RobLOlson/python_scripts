import math
import random
import re
from decimal import Decimal

_CONSTANT_COEF_DOT_PATTERN = re.compile(r"(\d+\s*)\\cdot(\s[a-zA-Z])")
_VARIABLES = ["x", "y", "z"]


def get_sympy():
    import sympy

    return sympy


def random_factor(
    var, min_coef: int = 1, max_coef: int = 9, min_order: int = 1, max_order: int = 1
):
    return random.randint(min_coef, max_coef) * (var ** random.randint(min_order, max_order))


# To write a new algebra problem generator you must:
# * begin the function name with 'generate'
# * return a 2-tuple of strings ('TeX problem', 'TeX answer')
# * the last line of the doc string should name the problem type


def generate_integer_factorization(freq_weight: int = 1000) -> tuple[str, str]:
    """Generate integer factorization.
    Problem Description:
    Factorize Integers"""

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


def generate_radical_simplification(freq_weight: int = 1000) -> tuple[str, str]:
    """Generate radical simplification.
    Problem Description:
    Simplify Radicals"""

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


def generate_simple_x_expression(freq_weight: int = 1000) -> tuple[str, str]:
    """Generate an expression in one variable where coefficients and exponents are all integers.
    Problem Description:
    Simplifying Expressions"""

    sympy = get_sympy()

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


def generate_function_evaluation(freq_weight: int = 1000) -> tuple[str, str]:
    """Generate a function in one variable where coefficients and exponents are all integers.
    Problem Description:
    Evaluating Functions"""

    sympy = get_sympy()

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


def generate_simple_x_equation(freq_weight: int = 1000) -> tuple[str, str]:
    """Generate a single variable equation.
    Problem Description:
    Solving Equations with One Variable"""

    sympy = get_sympy()

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

    sympy = get_sympy()

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

    # variable = random.choice(["x"])
    # unknown = random.choice(["y"])

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
    problem_statement = "Isolate the variable y.  Find the x-intercept and the y-intercept."

    expression = f"{left} = {right}"

    return (
        rf"{problem_statement} \\ \\ \({expression}\) \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\",
        "Solution here.",
    )


def generate_system_of_equations(freq_weight: int = 1000) -> tuple[str, str]:
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


def generate_arithmetic_sequence(freq_weight: int = 1000) -> tuple[str, str]:
    """Generate an arithmetic sequence.
    Problem Description:
    Arithmetic Sequences"""

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
        f"{init+4*step}",
    )


def generate_arithmetic_sequence_formula(freq_weight: int = 1000) -> tuple[str, str]:
    """Generate an arithmetic sequence formula.
    Problem Description:
    Arithmetic Sequence Formulas"""

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


def generate_geometric_sequence(freq_weight: int = 1000) -> tuple[str, str]:
    """Generate an geometric sequence.
    Problem Description:
    Geometric Sequences"""

    sympy = get_sympy()

    difficulty = int(3 - math.log(freq_weight + 1, 10))

    step = random.choice([2, 3, 4, 5])
    init = random.choice([-10, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 10])

    sequence = [str(init * step**count) for count in range(0, 5)]

    if difficulty > 1:
        denom_step = random.choice(list({2, 3, 4, 5} - {step}))
        sequence = [
            sympy.latex(sympy.sympify(f"{init}*({step}/{denom_step})**{count}"))
            for count in range(0, 5)
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


def generate_geometric_sequence_evaluation(freq_weight: int = 1000) -> tuple[str, str]:
    """Generate geometric sequence formula evaluation.
    Problem Description:
    Evaluate Geometric Sequence Formula"""

    sympy = get_sympy()

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
        answer = sympy.sympify(f"{init} * ({step} / {denom_step}) ** {n-1}")

    problem_statement = f"What is the {evaluate_at} term in the sequence?"

    return (
        rf"{problem_statement} \\ \\ \({formula}\) \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\",
        rf"\({answer}\)",
    )


def generate_power_expression(freq_weight: int = 1000) -> tuple[str, str]:
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


def generate_radical_simplification_with_vars(freq_weight: int = 1000) -> tuple[str, str]:
    """Generate variable radical simplification.
    Problem Description:
    Simplify Radicals With Variables"""

    global _VARIABLES

    sympy = get_sympy()

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

    expression = (
        f"\\sqrt{{{sole_factor * perfect_square * perfect_square}{glyph}^{{{glyph_power}}}}}"
    )

    answer = f"{perfect_square}{glyph if perfect_part else ''}^{{{perfect_part}}}\\sqrt{{{sole_factor}{glyph if radical_part else ''}^{{{radical_part}}}}}"

    if difficulty > 2:
        glyph_power = random.choice(range(1, 8))
        expression_1 = (
            f"sqrt({sole_factor * perfect_square * perfect_square} * {glyph} ** {glyph_power})"
        )

        latex_1 = sympy.latex(sympy.sympify(expression_1, evaluate=False))

        sole_factor_2 = random.choice(primes)
        leftover_primes_2 = set(primes) - {sole_factor_2}
        glyph_power_2 = random.choice(range(1, 8))
        perfect_square_2 = random.choice(list(leftover_primes_2))

        expression_2 = f"sqrt({sole_factor_2 * perfect_square_2 * perfect_square_2} * {glyph} ** {glyph_power_2})"
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


def generate_binomial_product_expansion(freq_weight: int = 1000) -> tuple[str, str]:
    """Generate binomial product expansion.
    Problem Description:
    Binomial Product Expansion"""

    global _VARIABLES

    sympy = get_sympy()

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

    problem_statement = f"Expand the binomial product into a standard form polynomial."

    return (
        rf"{problem_statement} \\ \\ \({expression_latex}\) \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\",
        rf"\({answer_latex}\)",
    )


def generate_multiply_difference_of_squares(freq_weight: int = 1000) -> tuple[str, str]:
    """Generate multiply difference of squares binomial.
    Problem Description:
    Multiply Difference of Squares Binomial"""

    global _VARIABLES

    sympy = get_sympy()

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

    problem_statement = f"Expand the binomial product into a standard form polynomial."

    return (
        rf"{problem_statement} \\ \\ \({expression_latex}\) \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\",
        rf"\({answer_latex}\)",
    )


def generate_multiply_squares_of_binomials(freq_weight: int = 1000) -> tuple[str, str]:
    """Generate multiply squares of binomials.
    Problem Description:
    Multiply Squares of Binomials"""

    global _VARIABLES

    sympy = get_sympy()

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

    problem_statement = f"Expand the binomial product into a standard form polynomial.  (Don't forget to combine like terms.)"

    return (
        rf"{problem_statement} \\ \\ \({expression_latex}\) \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ \\",
        rf"\({answer_latex}\)",
    )
