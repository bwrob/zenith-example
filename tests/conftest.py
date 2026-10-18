"""Pytest fixtures and test configuration."""

from __future__ import annotations

import pytest


@pytest.fixture
def sample_name() -> str:
    """Provide a sample name for testing."""
    return "Antigravity"
