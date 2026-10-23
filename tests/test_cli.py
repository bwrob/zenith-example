"""Unit tests for the command-line interface."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

import zenith_example
from zenith_example import _lazy
from zenith_example.__main__ import main as module_main
from zenith_example.cli import app, main

runner = CliRunner()


def test_cli_help() -> None:
    """Test CLI help flag outputs command information."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.stdout or "Options:" in result.stdout


def test_cli_version() -> None:
    """Test CLI version option outputs version."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "zenith-example" in result.stdout


def test_cli_greet() -> None:
    """Test CLI greet subcommand."""
    result = runner.invoke(app, ["greet", "Developer"])
    assert result.exit_code == 0
    assert "Hello, Developer!" in result.stdout


def test_cli_greet_default() -> None:
    """Test CLI greet subcommand with default argument."""
    result = runner.invoke(app, ["greet"])
    assert result.exit_code == 0
    assert "Hello, World!" in result.stdout


def test_cli_main(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test main entry point invocation."""
    monkeypatch.setattr("sys.argv", ["zenith-example", "--help"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0


def test_cli_module_main(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test module invocation via python -m zenith_example."""
    monkeypatch.setattr("sys.argv", ["zenith-example", "--help"])
    with pytest.raises(SystemExit) as exc_info:
        module_main()
    assert exc_info.value.code == 0


def test_lazy_accessors_dunder() -> None:
    """Test accessing dunders raises AttributeError directly."""
    unknown_attribute = "__unknown__"
    with pytest.raises(AttributeError, match="has no attribute '__unknown__'"):
        _ = getattr(zenith_example, unknown_attribute)


def test_lazy_accessors_unknown_attr() -> None:
    """Test accessing unknown attributes raises AttributeError."""
    unknown_attribute = "nonexistent_symbol"
    with pytest.raises(AttributeError, match="has no attribute 'nonexistent_symbol'"):
        _ = getattr(zenith_example, unknown_attribute)


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
