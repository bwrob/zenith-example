---
description: >-
  Authoritative guide for Meta Pyrefly static type checker in Python 3.12+.
  Use when type checking, configuring types, fixing type errors, or optimizing generic models.
  Triggers: pyrefly, type check, static typing, pyrefly.toml, types.
name: tool-pyrefly
version: 1.0.0
---


# Pyrefly Static Type Checker (`tool-pyrefly`)

`pyrefly` is Meta's next-generation, high-performance static type checker and
Language Server Protocol (LSP) for Python, written in Rust. It enforces strict
type safety, full generic verification, and zero implicit `Any` types with
exceptional speed.

In Zenith projects, `pyrefly` is configured with the `strict` preset mode to
guarantee complete type coverage across the codebase.

---

## 1. Core CLI Commands

Use these commands to verify static typing across the project or in single
modules.

```bash
uv run pyrefly check                      # Check entire project config
uv run pyrefly check path/to/file.py      # Check a specific file or module
uv run pyrefly check --output-format json # Output machine-readable JSON
uv run pyrefly init                       # Generate pyrefly.toml config
```

---

## 2. Configuration & Where It Lives

Pyrefly is configured through **`pyrefly.toml`** at the project root using
`kebab-case` keys:

```toml
# Only respect explicit # pyrefly: ignore[...] comments (bans bare # type: ignore)
enabled-ignores      = ["pyrefly"]
infer-with-first-use = false

# Preset modes: "strict", "recommended", or "lenient"
preset = "strict"

# Root paths and exclusions for project source code
project-excludes = ["**/.*", "**/site", "**/dist", "**/build", "**/.venv"]
project-includes = ["src", "tests"]

# Target Python version
python-version = "3.13.0"

# Extra module search paths (e.g. src, stubs)
search-path = ["src"]
```

---

## 3. Most Common Configuration Changes During Development

Adjust type checking rules and module search paths using these standard
patterns.

### A. Suppressing Type Errors on a Specific Line

Because `enabled-ignores = ["pyrefly"]` is active, generic `# type: ignore`
comments are ignored. Always use `# pyrefly: ignore[error-code]`:

```python
# Suppress a specific error code
result = untyped_library.call()  # pyrefly: ignore[unknown-attribute]

# Suppress multiple errors
data = legacy_payload.parse()  # pyrefly: ignore[bad-arg, missing-attribute]
```

> [!NOTE]
> Always specify the exact error code inside brackets. Never use bare
> ignores. To automatically strip stale ignore comments across the codebase,
> run `uv run pyrefly check --remove-unused-ignores`.

### B. Handling Untyped or Heavy Third-Party Imports

When a third-party dependency lacks type stubs (`py.typed`) or has broken/slow
internal annotations:

1. **Ignore missing imports** (`ignore-missing-imports`):

   ```toml
   ignore-missing-imports = [
       "untyped_pkg.*",
   ]
   ```

2. **Skip following imports into heavy packages** (`replace-imports-with-any`,
   Pyrefly's equivalent of Mypy's `follow_imports = "skip"`):

   ```toml
   replace-imports-with-any = [
       "heavy_legacy_sdk.*",
   ]
   ```

3. **Provide custom `.pyi` stubs** in `stubs/` and add to `search-path`:

   ```toml
   search-path = ["src", "stubs"]
   ```

### C. Per-Directory Rule Overrides (`[[sub-config]]`)

To relax specific error codes in a subdirectory (such as `tests/**` or thin C
extension wrappers) while keeping `src/**` at full strictness:

```toml
[[sub-config]]
matches = "tests/**"

[sub-config.errors]
bad-return = false
```

### D. Adding a New Directory to Type Checking

When adding a new directory such as `scripts/` or `benchmarks/`:

```toml
project-includes = ["src", "tests", "scripts"]
```

### E. Toggling Presets

While Zenith defaults to `strict`, projects during active prototyping can
adjust the preset level:

- **`strict`**: Requires full type coverage, disallows implicit `Any`,
  enforces exhaustive matching and protocol variance.
- **`recommended`**: Balanced enforcement suitable for general applications.
- **`lenient`**: Minimal barrier to entry, warnings only for overt mismatches.

```toml
preset = "recommended"
```

---

## 4. Modern Python 3.12+ Typing Patterns for Pyrefly

Write idiomatically typed code using modern standard library features.

### Native Generics (PEP 695)

Always use Python 3.12+ type parameter syntax instead of legacy `TypeVar`:

```python
# Correct (PEP 695)
type Matrix[T] = list[list[T]]


def first[T](items: list[T]) -> T | None:
    return items[0] if items else None
```

```python
# Legacy syntax to avoid
from typing import Optional, TypeVar

T = TypeVar("T")
```

### Protocol Contracts over Nominal Inheritance

Define interfaces with structural typing:

```python
from typing import Protocol


class Greeter(Protocol):
    def greet(self, name: str) -> str: ...
```

---

## 5. Best Practices & Troubleshooting

Keep the following tips in mind when type checking code:

- **Check frequently with Poe**: Run `uv run poe type-check` before
  committing code.
- **Avoid `typing.Any`**: Use specific union types, generics, or `object`
  with narrowing (`isinstance`).
- **Missing `py.typed`**: If an installed library warns of missing types,
  install its stub package (e.g., `uv add --dev types-requests`).
