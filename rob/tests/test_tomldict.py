import os

import pytest

# toml is optional; prefer tomllib if toml module not available
try:
    import toml  # type: ignore
except Exception:  # pragma: no cover
    import tomllib as _tomllib  # type: ignore
    import types, sys
    toml = types.ModuleType("toml")  # type: ignore
    def _load(fp):
        return _tomllib.load(fp)
    def _loads(s: str):
        return _tomllib.loads(s)
    def _dump(obj, fp):
        # tomllib has no dump; write bytes via standard library
        import io
        import json
        # naive TOML-less fallback using JSON for tests that only read back via toml.load
        fp.write("\n".join(f"{k} = {repr(v)}" for k, v in obj.items()))
    def _dumps(obj):
        return "\n".join(f"{k} = {repr(v)}" for k, v in obj.items())
    toml.load = _load  # type: ignore
    toml.loads = _loads  # type: ignore
    toml.dump = _dump  # type: ignore
    toml.dumps = _dumps  # type: ignore
    sys.modules["toml"] = toml  # type: ignore

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
    # Use binary mode to satisfy tomllib-backed shim
    with open(TEST_FILENAME, "rb") as f:
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
    except:  # noqa: E722
        pass  # We expect the exception

    # Check file was still closed despite error:
    with pytest.raises(ValueError, match="I/O operation on closed file."):
        d["b"] = 2


# this test "works" but the test itself fails to clean up the temporary file
# TODO: fix this test

# def test_sync_cleanup_on_replace_failure(monkeypatch):
#     initial_data = {"initial": "data"}
#     with open(TEST_FILENAME, "w") as f:
#         toml.dump(initial_data, f)

#     def mock_replace(src, dst):
#         raise PermissionError("Simulated replace failure")

#     def mock_unlink(path):
#         raise OSError("Simulated unlink failure")

#     monkeypatch.setattr(os, "replace", mock_replace)
#     monkeypatch.setattr(os, "unlink", mock_unlink)

#     with pytest.raises(PermissionError, match="Simulated replace failure"):
#         with TomlDict.open(TEST_FILENAME) as d:
#             assert d["initial"] == "data"
#             d["new"] = "value"

#     # Verify file unchanged
#     with open(TEST_FILENAME, "r") as f:
#         loaded = toml.load(f)
#         assert loaded == initial_data
#         assert "new" not in loaded
