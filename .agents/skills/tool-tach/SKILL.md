---
description: >-
  Guide for Tach modular architecture and layer boundary tool.
  Use when validating module boundaries, preventing circular imports, and defining layer hierarchies.
  Triggers: tach, architecture, layers, boundaries, circular imports, tach.toml.
name: tool-tach
version: 1.0.0
---


# Tach Architecture & Boundary Linter (`tool-tach`)

`tach` is a fast architectural linter and dependency graph visualizer for
Python, written in Rust. It enforces modular boundaries, defines public
module interfaces, and guarantees that low-level domain layers never import
from high-level presentation or CLI layers.

Zenith projects configure `tach` to enforce clean acyclic layer separation and block
circular imports.

---

## 1. Core CLI Commands

Use these commands to check boundaries, show trees, and generate reports.

```bash
uv run tach check                  # Check internal module boundaries
uv run tach check-external         # Check pyproject.toml external deps
uv run tach check --exact          # Fail on unused module dependencies
uv run tach show                   # Print terminal architecture tree
uv run tach show --mermaid         # Export dependency graph in Mermaid
uv run tach sync                   # Sync tach.toml to existing imports
uv run tach report                 # Generate health report
```

---

## 2. Configuration Location

Configure Tach through **`tach.toml`** at the project root:

```toml
# Source roots for Python import resolution
source_roots = ["src"]

# Boundary enforcement rules & ignore governance
exact = true
forbid_circular_dependencies = true
ignore_type_checking_imports = true

[rules]
unused_ignore_directives = "error"
require_ignore_directive_reasons = "error"

# Layer hierarchy (ordered from top to bottom)
# Higher layers can import from lower layers; lower cannot import upward.
layers = [
    "cli",
    "core",
]

# Module definitions and allowed dependencies
[[modules]]
path = "my_app.cli"
depends_on = ["my_app.core"]
layer = "cli"

[[modules]]
path = "my_app.core"
depends_on = []
layer = "core"
```

---

## 3. Common Configuration Changes During Development

Manage architectural layers, module dependencies, public interfaces, and external
`pyproject.toml` dependency hygiene with these patterns.

### A. Adding a New Architectural Layer

To add a new layer (such as `domain`, `adapters`, or `storage`):

1. Define the layer in the `layers` array in order of hierarchy:

   ```toml
   layers = [
       "cli",
       "services",
       "core",
   ]
   ```

2. Any module assigned to `cli` can import from `services` and `core`.
3. Modules in `services` can import from `core`, but never from `cli`.
4. Modules in `core` cannot import from `services` or `cli`.

### B. Adding a New Internal Module

When creating a new package or module inside `src/`:

```toml
[[modules]]
path = "my_app.storage"
depends_on = ["my_app.core"]
layer = "core"
```

### C. Declaring Public Interfaces (`[[modules.interfaces]]`)

To prevent external modules from importing private implementation details:

```toml
[[modules]]
path = "my_app.core"
depends_on = []
layer = "core"

[[modules.interfaces]]
expose = ["my_app.core.get_greeting", "my_app.core.GreetingConfig"]
```

Any attempt to import an unexposed symbol from outside `my_app.core` will
trigger a Tach interface violation error.

### D. Checking External `pyproject.toml` Dependencies (`tach check-external`)

`uv run poe dependencies` runs both `tach check` (internal layer boundaries) and
`tach check-external` (external third-party dependency hygiene). `tach check-external`
automatically catches:

1. **Unused dependencies**: Packages declared in `[project.dependencies]` that the codebase
   never imports in `src/` (controlled by `[rules] unused_external_dependencies = "error"`,
   which is `"error"` by default).
2. **Transitive or dev-only imports**: Importing an undeclared transitive
   dependency (such as `click` via `typer`) or a dev dependency inside `src/`.

A runtime dependency can load dynamically without direct imports in source code.
It can also have non-standard metadata. In these cases, configure `[external]`
in `tach.toml`:

```toml
[external]
# Exclude dynamically loaded runtime packages from unused-dependency errors
exclude = ["psycopg-binary", "uvicorn"]

# Map PyPI distribution names to top-level import names if metadata is missing
rename = ["pillow:PIL", "beautifulsoup4:bs4"]
```

### E. Exporting Mermaid Architecture Diagrams to Documentation

Zenith defines a built-in task in `poe_tasks.toml` to export the current
dependency graph directly as a Mermaid diagram:

```bash
uv run poe dependency-graph
```

This generates `docs/dependency_graph.mmd`, which you can embed in docs.

### F. Suppressing False Positives or Temporary Migration Exceptions

When transitioning legacy code or handling dynamic runtime imports, always provide
an explicit architectural reason (enforced by `require_ignore_directive_reasons = "error"`):

```python
# tach-ignore(legacy-bridge): dynamic runtime import during migration
from my_app.cli import format_output
```

Or ignore a specific module path with reason:

```python
from my_app.cli import (
    format_output,
)  # tach-ignore[my_app.cli](circular-hook): deferred CLI hook
```

---

## 4. Architecture Guidelines

Follow these architecture guidelines:

- **Check boundaries and external dependencies with Poe**: Always run `uv run poe dependencies`
  before merging.
- **Top-Down Only**: Imports must flow downwards through layers (`cli` $\to$
  `services` $\to$ `core`). Never allow `core` to import anything from `cli`.
- **Acyclic Enforcement**: Tach prevents circular dependency
  cycles. If Tach detects a cycle, extract shared interfaces into a lower-level
  protocol module.
