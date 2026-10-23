"""Unit tests for core functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

from hypothesis import given, strategies as st

from zenith_example.core import get_greeting

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion


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
