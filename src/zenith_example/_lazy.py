"""PEP 562 support for packages that re-export submodules on demand."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping


def _resolve_or_raise(package: str, name: str) -> object:
    # Protocol probes ask for dunders that a package never resolves lazily,
    # and a failed import is not cached, so answering them here would repeat
    # the whole finder walk on every copy, pickle, or introspection call.
    if name.startswith("__") and name.endswith("__"):
        msg = f"module {package!r} has no attribute {name!r}"
        raise AttributeError(msg)

    # Importing a subpackage eagerly used to bind it on its parent, so
    # ``package.subpackage`` resolved without importing it by name first.
    # Resolve it on demand to keep that working, which the import system
    # then caches by binding the submodule on this package.
    submodule = f"{package}.{name}"
    try:
        return importlib.import_module(submodule)
    except ModuleNotFoundError as error:
        if error.name != submodule:
            raise
        msg = f"module {package!r} has no attribute {name!r}"
        raise AttributeError(msg) from None


def lazy_getattr(
    module_globals: dict[str, object],
    members: Mapping[str, str],
) -> Callable[[str], object]:
    """Build a package's ``__getattr__`` for lazy member loading.

    Parameters
    ----------
    module_globals : dict[str, object]
        The calling package's ``globals()``. Resolved members are written
        back into it, so each submodule is imported at most once.
    members : Mapping[str, str]
        Mapping of exported symbol name to its relative module path.

    Returns
    -------
    Callable[[str], object]
        Callable implementing PEP 562 lazy attribute resolution.

    """
    package = str(module_globals["__name__"])

    def module_getattr(name: str) -> object:
        if name in members:
            module = importlib.import_module(members[name], package)
            value = getattr(module, name)
            module_globals[name] = value
            return value

        return _resolve_or_raise(package, name)

    return module_getattr


def lazy_dir(module_globals: dict[str, object]) -> Callable[[], list[str]]:
    """Build a package's ``__dir__`` for lazy member loading.

    Parameters
    ----------
    module_globals : dict[str, object]
        The calling package's ``globals()``.

    Returns
    -------
    Callable[[], list[str]]
        Callable that lists the package's imported members plus ``__all__``.

    """

    def module_dir() -> list[str]:
        all_members = module_globals.get("__all__", ())
        if isinstance(all_members, (list, tuple)):
            names = set(module_globals) | set(all_members)
        else:
            names = set(module_globals)
        return sorted(names)

    return module_dir
