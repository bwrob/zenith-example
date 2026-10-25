---
description: >-
  Guide for linting and formatting Python with Astral Ruff.
  Use when linting code, auto-fixing violations, formatting source files, or configuring rules.
  Triggers: ruff, lint, format, ruff.toml, code style.
name: tool-ruff
version: 1.1.0
---


# Ruff Linter & Formatter (`tool-ruff`)

`ruff` is a fast Python linter and code formatter written in Rust by
Astral. It replaces Flake8, Black, isort, pydocstyle, pyupgrade, and autoflake.

Zenith projects configure `ruff` via `ruff.toml` with `select = ["ALL"]`
and targeted exceptions.

---

## 1. Core CLI Commands

Use these commands to lint, format, and inspect code violations across the
codebase.

### Linting & Fixing

```bash
uv run ruff check .                      # Check all files in repository
uv run ruff check path/to/file.py        # Check a specific file or folder
uv run ruff check --fix .                # Automatically apply safe fixes
uv run ruff check --fix --unsafe-fixes . # Apply safe and unsafe fixes
uv run ruff check --diff .               # Show proposed fixes without editing
uv run ruff check --watch .              # Continuous linting on file change
```

### Formatting

```bash
uv run ruff format .                     # Format all files in place
uv run ruff format --check .             # Check formatting without modifying
uv run ruff format --diff .              # Show formatting diffs
uv run ruff format path/to/file.py       # Format a single file
```

### Explaining Rules

```bash
uv run ruff rule E501                    # Display explanation for a rule
```

---

## 2. Configuration Location

Zenith projects configure Ruff via a standalone **`ruff.toml`** at the
repository root:

```toml
# Target Python version
target-version = "py312"

# Line length limit for code and docstrings
line-length = 88
indent-width = 4

# Files and directories to exclude
extend-exclude = [
    ".venv",
    "site",
    "dist",
    "build",
    "__snapshots__",
]

[lint]
# Enable all rules by default (Zenith strict preset)
select = ["ALL"]
future-annotations = true

# Globally ignored rules with explicit rationale
ignore = [
    "D203",   # One-blank-line-before-class (incompatible with D211)
    "D213",   # Multi-line-summary-second-line (incompatible with D212)
    "COM812", # Missing-trailing-comma (conflicts with ruff format)
    "ISC001", # Single-line-implicit-string-concatenation
]

# Allow auto-fixing for all enabled rules
fixable = ["ALL"]
unfixable = []

# Enforce absolute package imports across all files
[lint.flake8-tidy-imports]
ban-relative-imports = "all"

# Preserve runtime typing for dataclasses, attrs, and pydantic models
[lint.flake8-type-checking]
exempt-modules = ["typing", "typing_extensions"]
runtime-evaluated-base-classes = ["pydantic.BaseModel"]
runtime-evaluated-decorators = [
    "attrs.define",
    "attrs.frozen",
    "attrs.mutable",
    "dataclasses.dataclass",
    "pydantic.dataclasses.dataclass",
    "pydantic.validate_call",
]

# Consolidate aliased imports and require future annotations across all files
[lint.isort]
combine-as-imports = true
required-imports = ["from __future__ import annotations"]

# Per-file rule relaxations
[lint.per-file-ignores]
"**/*.pyi" = ["I002", "PYI044"]
"tests/*" = [
    "S101",    # Use of assert detected (standard in pytest)
    "PLR2004", # Magic value used in comparison
    "D",       # Docstring requirements relaxed in tests
]

[lint.pydocstyle]
convention = "numpy"

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
docstring-code-format = true
docstring-code-line-length = 79
```

---

## 3. Common Configuration Changes During Development

Use these patterns to adjust rule selections, relaxations, and exceptions.

### A. Ignoring a Specific Rule Globally

If a rule is noisy or conflicts with domain design:

1. Add the rule code to `lint.ignore` in `ruff.toml`:

   ```toml
   [lint]
   ignore = [
       "ANN401",  # Dynamically typed expressions (typing.Any)
   ]
   ```

### B. Relaxing Rules for Specific Subtrees (`per-file-ignores`)

Tests, benchmarks, documentation scripts, or CLI files often require rule
exceptions. Use negated globs (`"!src/**.py"`) to relax rules across all
auxiliary files in one line. This approach keeps `src/` strictly enforced
while relaxing checks for tests and scripts:

```toml
[lint.per-file-ignores]
# Relax docstring and assert rules everywhere outside production src/
"!src/**.py" = ["D", "S101", "PLR2004"]

# Or scope to specific directories:
"tests/**/*.py" = ["S101", "PLR2004", "D"]

# Allow print statements and typer callbacks in CLI entrypoints
"src/*/cli.py" = ["T201", "FBT001", "FBT002"]

# Relax complexity checks for migration or benchmark scripts
"scripts/*.py" = ["T201", "C901"]
```

### C. Inline Rule Suppression (`# ruff: ignore`)

When you need an exception on a single line rather than an entire file, use a
Ruff suppression directive — **never** a `# noqa` comment:

```python
# Suppress a single rule with the rule's full name
result = evaluate_untrusted_input(payload)  # ruff: ignore[suspicious-eval-usage]

# Suppress multiple rules in one directive
secret_token = fetch_token()  # ruff: ignore[hardcoded-password-default, hardcoded-password-string]
```

> [!WARNING]
> Never use `# noqa` comments (bare or with rule codes). Ruff rules
> `noqa-comments` (noqa instead of `ruff: ignore`) and `RUF106` (rule codes
> instead of rule names) enforce the directive form above. Always specify the
> exact rule by its full name: `# ruff: ignore[rule-name]`.

### D. Changing Docstring Style Convention

To switch between NumPy, Google, or Sphinx docstrings:

```toml
[lint.pydocstyle]
convention = "google"  # Options: "google", "numpy", "pep257"
```

### E. Enabling Unsafe Fixes for Specific Rules

By default, `ruff check --fix` applies only safe fixes. To enable automated
fixes for rules that Ruff marks as unsafe:

```toml
[lint]
extend-safe-fixes = ["UP006", "UP035"]
```

### F. Future Annotations Enforcement

Zenith requires `from __future__ import annotations` in all Python source
files through `lint.isort.required-imports`. Ruff triggers rule `I002` if this
import is missing:

```bash
uv run ruff check --fix .  # Automatically inserts the required import
```

Stub files (`.pyi`) must not include future annotations. Rule `PYI044`
forbids this import in stub files. `ruff.toml` ignores rules `I002` and `PYI044`
for stub files:

```toml
[lint.per-file-ignores]
"**/*.pyi" = ["I002", "PYI044"]
```

---

## 4. Guidelines and Gotchas

Follow these guidelines:

- **Always run check and format together**: A file is clean only when both
  `ruff check` and `ruff format` succeed.
- **Never fight the formatter**: If `ruff format` breaks lines across multiple
  rows, adjust structure or simplify expressions instead.
- **Formatter vs. Linter Conflicts**: Always keep rules `COM812` and `ISC001`
  in `lint.ignore` when you use `ruff format`.
- **Scope fixes to edited code**: Avoid running `--unsafe-fixes` across an
  entire codebase. Inspect diffs with `--diff` first.
