"""Demonstration and showcase repository instantiated from the Zenith template."""

from __future__ import annotations

from typing import TYPE_CHECKING

from zenith_example._lazy import accessors

if TYPE_CHECKING:
    from zenith_example.cli import app
    from zenith_example.core import get_greeting

__version__ = "0.1.0"
__all__ = ["__version__", "app", "get_greeting"]

_LAZY_MEMBERS: dict[str, str] = {
    "app": ".cli",
    "get_greeting": ".core",
}

__getattr__, __dir__ = accessors(globals(), _LAZY_MEMBERS)
