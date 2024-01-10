import sys

import pytest

from ..algebra import Term, UnlikeTermsError


def test_Terms():
    assert Term(1)
    assert Term("2x^2")
    assert Term("a") + Term("a") == Term("2a")
    assert Term("a") * Term("a") == Term("a^2")
    assert Term("a") / Term("a") == Term(1)
    assert Term("a") - Term("a") == Term(0)
    with pytest.raises(UnlikeTermsError):
        Term("x") + Term("y")
