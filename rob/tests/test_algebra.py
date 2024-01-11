import sys

import pytest

from ..algebra import Binomial, Term, UnlikeTermsError


def test_Terms():
    assert Term(1)
    assert Term("2x^2")
    assert Term(2) + Term(2) == Term(4)
    assert Term(3) * Term(3) == Term(9)
    assert Term("4^4") == Term(256)
    assert Term("a") * Term(1) == Term("a")
    assert Term("a") + Term(0) == Term("a")
    assert Term("a") + Term("a") == Term("2a")
    assert Term("a") * Term("a") == Term("a^2")
    assert Term("a^0.5") * Term("a^0.5") == Term("a")
    assert Term("a") / Term("a") == Term(1)
    assert Term("a") - Term("a") == Term(0)

    assert Term("x^0.5").evaluated_at(-1) == complex(0, 1)

    # with pytest.raises(UnlikeTermsError):
    #     Term("x") + Term("y")


def test_Binomials():
    assert Binomial("a+b") + Binomial("b+a") == Binomial("2(a+b)") == Binomial("2(b+a)")
    assert Binomial("x+1") * Binomial("x-1") == Binomial("x^2 - 1")

    assert (Binomial("2(x+1)^2") * Binomial("2(x+1)^0.5")).evaluated_at(0) == 4
