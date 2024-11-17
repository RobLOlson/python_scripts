from unittest.mock import MagicMock, patch

import pytest
import readchar
import rich

# Import the module under test (assuming it's named query.py)
from ..utilities.query import (
    approve_dict,
    approve_list,
    form_from_dict,
    linearize_complex_object,
    reconstitute_object,
    select,
)


# Test data fixtures
@pytest.fixture
def sample_list():
    return [1, 2, 3, 4, 5]


@pytest.fixture
def sample_dict():
    return {"a": 1, "b": 2, "c": 3}


@pytest.fixture
def complex_object():
    return {"a": [1, 2, {"x": "y", "z": "w"}]}


# Mock terminal size for consistent testing
@pytest.fixture(autouse=True)
def mock_terminal_size():
    with patch("shutil.get_terminal_size") as mock:
        mock.return_value = MagicMock(columns=80, lines=24)
        yield mock


class TestApproveList:
    def test_empty_list(self):
        assert approve_list([]) == []

    def test_maximum_zero(self):
        assert approve_list([1, 2, 3], maximum=0) == []

    @patch("readchar.readkey")
    def test_select_single_item(self, mock_readkey):
        # Simulate pressing '1' then Enter
        mock_readkey.side_effect = ["1", "\r"]
        result = approve_list([1, 2, 3])
        assert result == [1]

    @patch("readchar.readkey")
    def test_select_multiple_items(self, mock_readkey):
        # Simulate pressing '1', '2', then Enter
        mock_readkey.side_effect = ["1", "2", "\r"]
        result = approve_list([1, 2, 3])
        assert result == [1, 2]

    @patch("readchar.readkey")
    def test_maximum_limit(self, mock_readkey):
        # Simulate pressing '1', '2', '3' then Enter with maximum=2
        mock_readkey.side_effect = ["1", "2", "3", "\r"]
        result = approve_list([1, 2, 3, 4], maximum=2)
        assert len(result) <= 2

    @patch("readchar.readkey")
    def test_navigation_keys(self, mock_readkey):
        # Test arrow key navigation and selection
        mock_readkey.side_effect = [
            readchar.key.DOWN,  # Move down
            readchar.key.RIGHT,  # Select
            readchar.key.UP,  # Move up
            readchar.key.LEFT,  # Deselect
            "\r",  # Confirm
        ]
        result = approve_list([1, 2, 3])
        assert isinstance(result, list)


class TestSelect:
    @patch("readchar.readkey")
    def test_select_single_item(self, mock_readkey):
        # Simulate moving cursor and pressing Enter
        mock_readkey.side_effect = ["\r"]
        result = select([1, 2, 3])
        assert isinstance(result, type([1, 2, 3][0]))


class TestApproveDict:
    def test_empty_dict(self):
        assert approve_dict({}) == {}

    def test_maximum_zero(self):
        assert approve_dict({"a": 1}, maximum=0) == {}

    @patch("readchar.readkey")
    def test_select_single_entry(self, mock_readkey):
        # Simulate pressing '1' then Enter
        mock_readkey.side_effect = ["1", "\r"]
        result = approve_dict({"a": 1, "b": 2})
        assert len(result) == 1
        assert list(result.keys())[0] in ["a", "b"]


class TestLinearizeComplexObject:
    def test_simple_dict(self):
        result = linearize_complex_object({"a": 1})
        assert isinstance(result, list)
        assert any(item[0] == "{" for item in result)
        assert any(item[0] == "}" for item in result)

    def test_simple_list(self):
        result = linearize_complex_object([1, 2, 3])
        assert isinstance(result, list)
        assert any(item[0] == "[" for item in result)
        assert any(item[0] == "]" for item in result)

    def test_nested_structure(self, complex_object):
        result = linearize_complex_object(complex_object)
        assert isinstance(result, list)
        # Check for proper nesting indicators
        assert sum(1 for item in result if item[0] == "{") == sum(
            1 for item in result if item[0] == "}"
        )
        assert sum(1 for item in result if item[0] == "[") == sum(
            1 for item in result if item[0] == "]"
        )


class TestReconstituteObject:
    def test_simple_dict(self):
        linearized = linearize_complex_object({"a": 1})
        result = reconstitute_object(linearized)
        assert result == {"a": 1}

    def test_simple_list(self):
        linearized = linearize_complex_object([1, 2, 3])
        result = reconstitute_object(linearized)
        assert result == [1, 2, 3]

    def test_nested_structure(self, complex_object):
        linearized = linearize_complex_object(complex_object)
        result = reconstitute_object(linearized)
        assert result == complex_object

    def test_roundtrip(self, complex_object):
        """Test that linearize followed by reconstitute returns the original object"""
        linearized = linearize_complex_object(complex_object)
        result = reconstitute_object(linearized)
        assert result == complex_object


@patch("readchar.readkey")
class TestFormFromDict:
    def test_simple_form(self, mock_readkey):
        # Simulate pressing Enter to accept defaults
        mock_readkey.side_effect = ["\r"]
        test_dict = {"name": "John", "age": 30}
        result = form_from_dict(test_dict)
        assert isinstance(result, dict)
        assert all(key in result for key in test_dict)

    def test_nested_form(self, mock_readkey):
        # Simulate pressing Enter to accept defaults
        mock_readkey.side_effect = ["\r"]
        test_dict = {"personal": {"name": "John", "age": 30}, "settings": {"dark_mode": True}}
        result = form_from_dict(test_dict)
        assert isinstance(result, dict)
        assert all(key in result for key in test_dict)
