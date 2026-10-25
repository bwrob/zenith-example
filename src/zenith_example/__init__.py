"""Demonstration and showcase repository instantiated from the Zenith template."""

from __future__ import annotations

from typing import TYPE_CHECKING

from zenith_example._lazy import lazy_dir, lazy_getattr

if TYPE_CHECKING:
    from zenith_example.cli import app
    from zenith_example.core import get_greeting

__version__ = "0.1.0"
__all__ = ["__version__", "app", "get_greeting"]

__getattr__ = lazy_getattr(globals(), {"app": ".cli", "get_greeting": ".core"})
__dir__ = lazy_dir(globals())
