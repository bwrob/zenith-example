"""Unit tests for the command-line interface."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

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
