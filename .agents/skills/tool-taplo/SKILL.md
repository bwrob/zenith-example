---
description: >-
  Authoritative guide for Taplo TOML toolkit, formatter, and linter in Rust.
  Use when formatting, linting, checking, or configuring TOML configuration files.
  Triggers: taplo, toml, format-toml, format-check-toml, .taplo.toml.
name: tool-taplo
version: 1.0.0
---

# Taplo TOML Toolkit & Formatter (`tool-taplo`)

`taplo` is an extremely fast TOML toolkit, linter, and code formatter written in Rust.
In Zenith repositories, `taplo` enforces consistent 4-space indentation, aligned key-value
entries, table hierarchy indentation, and alphabetical key ordering across all project
TOML configuration files (`pyproject.toml`, `poe_tasks.toml`, `ruff.toml`, `tach.toml`,
`cosmic-ray.toml`, `zensical.toml`, `typos.toml`, etc.).

---

## 1. Core CLI Commands

Format and check TOML files directly using uv:

```bash
uv run taplo format                     # Format all TOML files in repository
uv run taplo format --check             # Check TOML formatting without modifying files
uv run taplo format path/to/file.toml   # Format a specific TOML file
uv run taplo lint                       # Lint TOML files against schemas
```

In Zenith, task aliases are wired directly into Poe:

```bash
uv run poe format-toml                  # Runs taplo format
uv run poe format-check-toml            # Runs taplo format --check
uv run poe fix                          # Auto-fixes Python, Markdown, typos, and TOML
uv run poe code-quality                 # Full quality pipeline including format-check-toml
```

---

## 2. Configuration (`.taplo.toml`)

`taplo` is configured via **`.taplo.toml`** at the project root:

```toml
exclude = [
    ".agents/skills/**/templates/**",
    ".temp/**",
    ".venv/**",
    "build/**",
    "dist/**",
    "site/**",
]

[formatting]
    align_entries   = true
    compact_arrays  = false
    compact_entries = false
    indent_entries  = true
    indent_string   = "    "
    indent_tables   = true
    reorder_keys    = true
```

### Key Formatting Rules

- **`align_entries = true`**: Aligns `=` signs within a table block for maximum readability.
- **`indent_entries = true`**: Indents table entries with 4 spaces (`indent_string = "    "`).
- **`indent_tables = true`**: Indents nested sub-tables (e.g. `[cosmic-ray.distributor]`).
- **`compact_arrays = false`**: Expands multi-line arrays for clean diff tracking.
- **`reorder_keys = true`**: Sorts keys alphabetically within each table.
- **`exclude`**: Excludes virtual environments (`.venv/`), build artifacts, and skill templates.

---

## 3. Pre-Commit Integration

Taplo is integrated into `.pre-commit-config.yaml` to ensure no unformatted TOML files are committed:

```yaml
  - repo: https://github.com/ComPWA/taplo-pre-commit
    rev: v0.9.3
    hooks:
      - id: taplo-format
        name: "⚙️ taplo · Format TOML files"
```

---

## 4. Common Troubleshooting

### Unformatted TOML in CI or Pre-commit

If CI or pre-commit flags an unformatted TOML file (e.g. `cosmic-ray.toml`):

```bash
uv run poe fix
# Or specifically:
uv run poe format-toml
```

Always verify with `uv run poe format-check-toml`.
