import os

import pytest
import toml

from ..utilities.tomldict import TomlDict

# Test filename (use a temporary file for testing)
TEST_FILENAME = "test_toml_dict.toml"


@pytest.fixture(autouse=True)
def setup_teardown():
    # Create a clean test file before each test
    if os.path.exists(TEST_FILENAME):
        os.remove(TEST_FILENAME)
    yield  # Run the test
    # Clean up after each test
    if os.path.exists(TEST_FILENAME):
        os.remove(TEST_FILENAME)


def test_basic_operations():
    with TomlDict.open(TEST_FILENAME) as d:
        d["a"] = 1
        d["b"] = "hello"
        assert d["a"] == 1
        assert d["b"] == "hello"
        assert len(d) == 2
        assert "a" in d
        assert "c" not in d


def test_context_manager_and_sync():
    with TomlDict.open(TEST_FILENAME) as d:
        d["x"] = 10

    # Check that data persists after closing
    with open(TEST_FILENAME, "r") as f:
        data = toml.load(f)
        assert data["x"] == 10


def test_update_and_clear():
    with TomlDict.open(TEST_FILENAME) as d:
        d.update({"a": 1, "b": 2})
        assert d["a"] == 1
        assert d["b"] == 2
        d.clear()
        assert len(d) == 0


def test_pop_and_popitem():
    with TomlDict.open(TEST_FILENAME) as d:
        d.update({"a": 1, "b": 2, "c": 3})
        assert d.pop("b") == 2
        assert "b" not in d
        assert d.pop("z", 99) == 99  # Test default value on non-existent key
        key, value = d.popitem()  # Order not guaranteed
        assert key in ("a", "c")
        assert value in (1, 3)


def test_get():
    with TomlDict.open(TEST_FILENAME) as d:
        d["a"] = 100
        assert d.get("a") == 100
        assert d.get("not_exist") is None
        assert d.get("not_exist", 50) == 50


def test_closed_file_operations():
    with TomlDict.open(TEST_FILENAME) as d:
        d["test"] = 1

    with pytest.raises(ValueError, match="I/O operation on closed file."):
        d["test"] = 2


def test_keys_values_items():
    with TomlDict.open(TEST_FILENAME) as d:
        d.update({"a": 1, "b": 2, "c": 3})
        assert sorted(d.keys()) == ["a", "b", "c"]
        assert sorted(d.values()) == [1, 2, 3]
        assert sorted(d.items()) == [("a", 1), ("b", 2), ("c", 3)]


def test_exception_during_context():
    try:
        with TomlDict.open(TEST_FILENAME) as d:
            d["a"] = 1
            raise Exception("Intentional error")
    except:
        pass  # We expect the exception

    # Check file was still closed despite error:
    with pytest.raises(ValueError, match="I/O operation on closed file."):
        d["b"] = 2
