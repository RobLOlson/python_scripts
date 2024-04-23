from __future__ import annotations

import random
import re
from fractions import Fraction


class UnlikeTermsError(Exception):
    pass


class Term:
    """Represents a polynomial term."""

    # term_pattern = re.compile(r"^(\d+|\d+\.\d+|-)?([a-z])?(?:\^(-?\d+\.?\d*))?$")
    term_pattern = re.compile(r"^(-?\d+\.?\d*|-)?([a-z])?(?:\^(-?\d+\.?\d*))?$")

    def __init__(
        self,
        coefficient: str | int | float | None = None,
        variable: str | None = None,
        power: int | float | None = None,
        show_fractions: bool = True,
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

            if inline_power is not None:
                if int(float(inline_power)) - float(inline_power) == 0:
                    self.power = int(inline_power)
                else:
                    self.power = float(inline_power)

                if not self.power:
                    self.variable = None
            else:
                self.power = 1

            if not self.variable:
                self.coefficient = self.coefficient**self.power
                self.power = 1
            # self.power = int(power) if power else 1

            self.show_fractions = show_fractions

            return

        if coefficient is not None:
            if int(float(coefficient)) - float(coefficient) == 0:
                self.coefficient = int(coefficient)
            else:
                self.coefficient = float(coefficient)
        else:
            self.coefficient = 1

        if power is None:
            self.power = 1
            self.variable = variable
        else:
            if float(power) == 0:
                self.variable = None
                self.power = 1
                return

            self.power = int(power) if int(power) == float(power) else float(power)
            # elif int(float(power)) - float(power) == 0:
            #     self.power = int(power)

            # else:
            #     self.power = float(power)

        self.variable = variable
        self.show_fractions = show_fractions
        # self.power = power if power else 1

    @classmethod
    def random_coef(cls, variable: str):
        """Generate a first-order Term with a random coefficient in {1..9}."""

        coefficient = random.randint(1, 9)
        return cls(coefficient=coefficient, variable=variable, power=None)

    def __str__(self):
        if not self.coefficient:
            return "0"

        if self.power == 1:
            power = ""

        else:
            if isinstance(self.power, float) and self.show_fractions:
                # if type(self.power) == float:

                numerator, denominator = (
                    Fraction(self.power).limit_denominator(100).as_integer_ratio()
                )
                power = rf"^\frac{{{numerator}}}{{{denominator}}}"
            else:
                power = rf"^{{{self.power}}}"

        coefficient = self.coefficient if self.coefficient != 1 else ""

        if isinstance(coefficient, float) and self.show_fractions:
            numerator, denominator = (
                Fraction(coefficient).limit_denominator(100).as_integer_ratio()
            )
            coefficient = rf"\frac{{{numerator}}}{{{denominator}}}"

        variable = self.variable if self.variable else ""

        if not variable and self.coefficient == 1:
            coefficient = "1"

        return rf"{coefficient}{variable}{power}"

    def __repr__(self):
        return f"Term(coefficient={self.coefficient}, variable={self.variable}, power={self.power})"

    def __add__(self, __value: Term | Binomial) -> Term | Binomial:
        if type(__value) == Binomial:
            __value = __value.simplify()
            if type(__value) == Binomial:
                return Binomial(left=__value, right=self)
                raise UnlikeTermsError

        assert type(__value) == Term

        if __value == Term(0):
            return self
        if self == Term(0):
            return __value

        left = self.coefficient if self.coefficient else 1
        right = __value.coefficient if __value.coefficient else 1

        if self.variable != __value.variable or self.power != __value.power:
            return Binomial(left=self, right=__value)

        else:
            coefficient = left + right
            if coefficient == 0:
                variable = None
                power = 1
            else:
                variable = self.variable
                power = self.power

        return Term(coefficient=coefficient, variable=variable, power=power)

    def __sub__(self, __value: Term) -> Term:
        # left = self.coefficient if self.coefficient else 1
        # right = __value.coefficient if __value.coefficient else 1

        left = self.coefficient
        right = __value.coefficient

        if self.variable != __value.variable or self.power != __value.power:
            raise UnlikeTermsError
        else:
            coefficient = left - right
            if coefficient == 0:
                variable = None
                power = 1
            else:
                variable = self.variable
                power = self.power
            return Term(coefficient=coefficient, variable=variable, power=power)

    def __mul__(self, __value: Term | Binomial) -> Term | Binomial:
        # multiplication between Term and Binomial is handled in Binomial class
        if isinstance(__value, Binomial):
            return __value * self

        if self.variable and __value.variable and self.variable != __value.variable:
            raise UnlikeTermsError

        # left_power = self.power if self.variable else 1
        # right_power = __value.power if __value.variable else 1

        # new_power = left_power + right_power
        self.coefficient * __value.coefficient
        new_power = self.power + __value.power
        if not self.variable or not __value.variable:
            new_power -= 1

        if int(new_power) - new_power == 0:
            new_power = int(new_power)

        variable = self.variable if self.variable else __value.variable
        if not variable:
            return Term(round(self.coefficient * __value.coefficient, 2))

        return Term(
            coefficient=round(self.coefficient * __value.coefficient, 2),
            variable=variable,
            power=new_power,
        )

    def __eq__(self, __value: Term | Binomial) -> bool:
        simple_value = __value.simplify()
        if isinstance(simple_value, Binomial):
            return False

        assert isinstance(simple_value, Term)

        return (
            self.coefficient == simple_value.coefficient
            and self.variable == simple_value.variable
            and self.power == simple_value.power
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

    def simplify(self) -> Term:
        return self

    def copy(self) -> Term:
        return Term(
            coefficient=self.coefficient, variable=self.variable, power=self.power
        )

    def evaluated_at(self, val: int | float) -> int | float:
        if not self.variable:
            return self.coefficient

        temp = val**self.power
        if isinstance(temp, complex):
            # temp = round(temp.real, 2) + round(temp.imag, 2) * complex()
            temp = complex(round(temp.real, 2), round(temp.imag, 2))
            return temp * self.coefficient

        if int(temp) - temp == 0:
            temp = int(temp)

        return temp * self.coefficient


class Binomial:
    """Represents the sum of two terms (with an optional multiplier)."""

    basic_binomial_pattern = re.compile(
        # r"^(-?\d+\.?\d*|-)?([a-z])?(?:\^(-?\d+\.?\d*))?\s*(\+|\-)\s*(-?\d+\.?\d*|-)?([a-z])?(?:\^(-?\d+\.?\d*))?$"
        # r"^(-?\d+\.?\d*|-)?\*?\((-?\d+\.?\d*|-)?([a-z])?(?:\^(-?\d+\.?\d*))?\s*(\+|\-)\s*(-?\d+\.?\d*|-)?([a-z])?(?:\^(-?\d+\.?\d*))?\)"
        r"^(-?\d+\.?\d*|-)?([a-z])?(?:\^\{?(-?\d+\.?\d*)\}?)?\*?\(?(-?\d+\.?\d*|-)?([a-z])?(?:\^\{?(-?\d+\.?\d*)\}?)?\s*(\+|\-)\s*(-?\d+\.?\d*|-)?([a-z])?(?:\^\{?(-?\d+\.?\d*)\}?)?\)?(?:\^\{?(-?\d+\.?\d*)\}?)?$"
    )

    def __init__(
        self,
        # coefficient: int | float | str | None = None,
        multiplier: str | Term | Binomial | None = None,
        left: Term | Binomial | None = None,
        right: Term | Binomial | None = None,
        power: float | int | None = None,
    ):
        expression = self.basic_binomial_pattern.match(str(multiplier))
        if expression and "(" not in multiplier:
            expression = self.basic_binomial_pattern.match(f"({multiplier})")

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
                power,
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

            self.power = float(power) if power else 1

            # NEXT
            # if self.multiplier

            return

        # self.coefficient = coefficient if coefficient != None else 1

        # if int(float(self.coefficient)) - float(self.coefficient) == 0:
        #     self.coefficient = int(self.coefficient)
        # else:
        #     self.coefficient = float(self.coefficient)

        self.multiplier = multiplier if multiplier else Term(1)
        self.left = left if left else Term(1)
        self.right = right if right else Term(1)
        self.power = power if power else 1

    def __repr__(self) -> str:
        if self.multiplier == Term(1):
            multiplier = ""
        else:
            multiplier = self.multiplier

        if self.power != 1:
            power = rf"^{{{self.power}}}"
        else:
            power = ""
        return f"Binomial('{multiplier!s}({self.left!s} + {self.right!s}){power}')"

    def __str__(self) -> str:
        if self.multiplier == Term(1):
            multiplier = ""
        else:
            multiplier = self.multiplier

        if self.power != 1:
            power = rf"^{{{self.power}}}"
        else:
            power = ""
        return f"{multiplier!s}({self.left!s} + {self.right!s}){power}"

    def __eq__(self, __value: Binomial | Term) -> bool:
        self_simple = self.simplify()
        value_simple = __value.simplify()
        if isinstance(self_simple, Term):
            return self_simple == value_simple

        if isinstance(value_simple, Binomial):
            assert isinstance(self_simple, Binomial)
            assert isinstance(value_simple, Binomial)

            if (
                self_simple.left == value_simple.left
                and self_simple.right == value_simple.right
            ) or (
                self_simple.left == value_simple.right
                and self_simple.right == value_simple.left
            ):
                if (
                    self_simple.multiplier == value_simple.multiplier
                    and self_simple.power == value_simple.power
                ):
                    return True

        return False

    def __add__(self, __value: Binomial | Term) -> Binomial | Term:
        self_simple = self.simplify()

        if type(__value) == Binomial:
            other_simple = __value.simplify()

        else:
            other_simple = __value

        if type(other_simple) == Term and type(self_simple) == Term:
            if self_simple.variable == other_simple.variable:
                return self_simple + __value

        if isinstance(other_simple, Term) and isinstance(self_simple, Binomial):
            new_term = other_simple + self_simple.left
            if isinstance(new_term, Term):
                return Binomial(left=new_term, right=self_simple.right)
            new_term = other_simple + self_simple.right
            if isinstance(new_term, Term):
                return Binomial(left=self_simple.left, right=new_term)
            else:
                # 3 candidate terms
                return Binomial(left=self_simple, right=other_simple)
                # one, two, three = self_simple.left, self_simple.right, other_simple

                # terms_by_power = sorted(
                #     [one, two, three],
                #     key=lambda x: x.power if x.variable else 0,
                #     reverse=True,
                # )

                # return Binomial(
                #     left=Binomial(terms_by_power[0], terms_by_power[1]),
                #     right=terms_by_power[2],
                # )

        if isinstance(other_simple, Binomial) and isinstance(self_simple, Binomial):
            assert isinstance(self_simple, Binomial)
            assert isinstance(other_simple, Binomial)

            one = self_simple.left + other_simple.left
            if other_simple.power == 1 and self_simple.power == 1:
                if isinstance(one, Term):
                    other = self_simple.right + other_simple.right
                    if isinstance(other, Term):
                        return Binomial(left=one, right=other)
                    else:
                        return Binomial(
                            left=one,
                            right=Binomial(
                                left=self_simple.right, right=other_simple.right
                            ),
                        )
                two = self_simple.left + other_simple.right
                if isinstance(two, Term):
                    other = self_simple.right + other_simple.left
                    if isinstance(other, Term):
                        return Binomial(left=two, right=other)
                    else:
                        return Binomial(
                            left=two,
                            right=Binomial(
                                left=self_simple.right, right=other_simple.left
                            ),
                        )

                three = self_simple.right + other_simple.right
                if isinstance(three, Term):
                    other = self_simple.left + other_simple.left
                    if isinstance(other, Term):
                        return Binomial(left=three, right=other)
                    else:
                        return Binomial(
                            left=three,
                            right=Binomial(
                                left=self_simple.left, right=other_simple.left
                            ),
                        )

            same_case = (
                self_simple.left == other_simple.left
                and self_simple.right == other_simple.right
            )
            symmetric_case = (
                self_simple.left == other_simple.right
                and self_simple.right == other_simple.left
            )
            if same_case or symmetric_case:
                new_coef = self_simple.multiplier + other_simple.multiplier

                return Binomial(new_coef, self.left, self.right)

            # if self_simple and other_simple:
            #     if self_simple.variable == other_simple.variable:
            #         return self_simple + other_simple

        return Binomial(left=self_simple, right=other_simple)
        raise UnlikeTermsError

    def __mul__(self, __value: Binomial | Term) -> Binomial | Term:
        simple_self = self.simplify()
        simple_value = __value.simplify()

        if isinstance(simple_self, Term):
            return simple_self * __value

        if isinstance(simple_value, Term):
            assert isinstance(simple_self, Binomial)
            assert isinstance(simple_value, Term)

            try:
                new_left = simple_self.left * simple_value
                new_right = simple_self.right * simple_value
                return Binomial(left=new_left, right=new_right)
            except UnlikeTermsError:
                pass

            new_multiplier = simple_self.multiplier * simple_value
            return Binomial(
                multiplier=new_multiplier,
                left=simple_self.left,
                right=simple_self.right,
                power=simple_self.power,
            )

        else:
            assert isinstance(simple_self, Binomial)
            assert isinstance(simple_value, Binomial)
            # terms inside parentheses are identical
            if Binomial(left=simple_self.left, right=simple_self.right) == Binomial(
                left=simple_value.left, right=simple_value.right
            ):
                return Binomial(
                    multiplier=simple_self.multiplier * simple_value.multiplier,
                    left=simple_self.left,
                    right=simple_self.right,
                    power=simple_self.power + simple_value.power,
                )

            if simple_self.power == 1 and simple_value.power == 1:
                # Four products
                one = simple_self.left * simple_value.left
                two = simple_self.left * simple_value.right
                three = simple_self.right * simple_value.left
                four = simple_self.right * simple_value.right

                return one + two + three + four

    def __truediv__(self, __value: Binomial | Term) -> Binomial | Term:
        reciprocal = __value.copy()
        reciprocal.power *= -1

        return self * reciprocal

    def copy(self) -> Binomial:
        return Binomial(
            multiplier=self.multiplier,
            left=self.left,
            right=self.right,
            power=self.power,
        )

    def simplify(self) -> Term | Binomial:
        combined = self.left + self.right

        try:
            if isinstance(combined, Term):
                return self.multiplier * combined

            if self.power == 1:
                new_left = self.left * self.multiplier
                new_right = self.right * self.multiplier

                return Binomial(left=new_left, right=new_right)

        except UnlikeTermsError:
            return self
        return self

    def evaluated_at(self, n: int | float) -> int | float:
        # assert type(self.multiplier) == (Term | Binomial)
        assert isinstance(self.multiplier, Term | Binomial)
        return (
            self.multiplier.evaluated_at(n)
            * (self.left.evaluated_at(n) + self.right.evaluated_at(n)) ** self.power
        )


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
