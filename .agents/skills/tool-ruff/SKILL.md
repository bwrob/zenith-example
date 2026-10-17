---
description: >-
  Authoritative guide for linting and formatting Python with Astral Ruff.
  Use when linting code, auto-fixing violations, formatting source files, or configuring rules.
  Triggers: ruff, lint, format, ruff.toml, code style.
name: tool-ruff
version: 1.0.0
---


# Ruff Linter & Formatter (`tool-ruff`)

`ruff` is an extremely fast Python linter and code formatter written in Rust by
Astral. It replaces Flake8, Black, isort, pydocstyle, pyupgrade, and autoflake.

In Zenith projects, `ruff` is configured strictly via `ruff.toml` with
`select = ["ALL"]` and targeted exceptions.

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

## 2. Configuration & Where It Lives

In Zenith projects, Ruff is configured via a standalone **`ruff.toml`** at the
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

# Consolidate aliased imports from the same module
[lint.isort]
combine-as-imports = true


# Per-file rule relaxations
[lint.per-file-ignores]
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

## 3. Most Common Configuration Changes During Development

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
exceptions. You can also use negated globs (`"!src/**.py"`) to relax strict
docstring or typing rules across all auxiliary files (`tests/`, `scripts/`,
`examples/`, `benchmarks/`) in a single rule while keeping `src/` 100% strict:

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

### C. Inline Rule Suppression (`# noqa`)

When an exception is needed on a single line rather than an entire file:

```python
# Suppress a single specific rule with explanation
result = evaluate_untrusted_input(payload)  # noqa: S307

# Suppress multiple rules
secret_token = fetch_token()  # noqa: S105, S106
```

> [!WARNING]
> Never use bare `# noqa`. Always specify the exact rule code
> (`# noqa: XYZ`).

### D. Changing Docstring Style Convention

To switch between NumPy, Google, or Sphinx docstrings:

```toml
[lint.pydocstyle]
convention = "google"  # Options: "google", "numpy", "pep257"
```

### E. Enabling Unsafe Fixes for Specific Rules

By default, `ruff check --fix` only applies *safe* fixes. To enable automated
fixes for rules considered unsafe:

```toml
[lint]
extend-safe-fixes = ["UP006", "UP035"]
```

---

## 4. Best Practices & Common Gotchas

Keep these essential guidelines in mind:

- **Always run check and format together**: A file is only clean when both
  `ruff check` and `ruff format` succeed.
- **Never fight the formatter**: If `ruff format` breaks lines across multiple
  rows, adjust structure or simplify expressions instead.
- **Formatter vs. Linter Conflicts**: Rules `COM812` and `ISC001` should
  always remain in `lint.ignore` when using `ruff format`.
- **Scope fixes to edited code**: Avoid running `--unsafe-fixes` across an
  entire codebase; review diffs carefully with `--diff` first.
