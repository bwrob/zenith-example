"""Unit tests for core functionality."""

from unittest.mock import patch

import pytest
from hypothesis import given, strategies as st
from syrupy.assertion import SnapshotAssertion

import zenith_example
from zenith_example import _lazy
from zenith_example.core import get_greeting


def test_get_greeting_default() -> None:
    """Test get_greeting with empty string defaults to World."""
    assert get_greeting("") == "Hello, World!"
    assert get_greeting("   ") == "Hello, World!"


def test_get_greeting_custom(sample_name: str) -> None:
    """Test get_greeting with a specific name."""
    assert get_greeting(sample_name) == f"Hello, {sample_name}!"


def test_get_greeting_snapshot(snapshot: SnapshotAssertion) -> None:
    """Test get_greeting output matches syrupy snapshot."""
    greeting = get_greeting("Zenith")
    assert greeting == snapshot


@given(st.text())
def test_get_greeting_property(name: str) -> None:
    """Property-based test: get_greeting always returns a well-formed greeting."""
    greeting = get_greeting(name)
    assert greeting.startswith("Hello, ")
    assert greeting.endswith("!")
    clean = name.strip()
    expected = clean or "World"
    assert expected in greeting


def test_lazy_accessors_dunder() -> None:
    """Test accessing dunders raises AttributeError directly."""
    with pytest.raises(AttributeError, match="has no attribute '__unknown__'"):
        _ = zenith_example.__unknown__


def test_lazy_accessors_unknown_attr() -> None:
    """Test accessing unknown attributes raises AttributeError."""
    with pytest.raises(AttributeError, match="has no attribute 'nonexistent_symbol'"):
        _ = zenith_example.nonexistent_symbol


def test_lazy_accessors_submodule_import_error() -> None:
    """Test re-raising ModuleNotFoundError when error is from internal dependency."""
    with (
        patch("importlib.import_module", side_effect=ModuleNotFoundError("unrelated")),
        pytest.raises(ModuleNotFoundError, match="unrelated"),
    ):
        _lazy._resolve_or_raise("zenith_example", "some_mod")


def test_lazy_dir_without_all_list() -> None:
    """Test module_dir when __all__ is not a list or tuple."""
    mod_globals: dict[str, object] = {"__name__": "dummy", "__all__": None, "foo": 1}
    _, mod_dir = _lazy.accessors(mod_globals, {})
    assert mod_dir() == ["__all__", "__name__", "foo"]
