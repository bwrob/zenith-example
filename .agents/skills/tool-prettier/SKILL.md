---
description: >-
  Authoritative guide for Prettier code formatter for YAML manifests and CSS stylesheets.
  Use when formatting, linting, checking, or configuring YAML and CSS files.
  Triggers: prettier, yaml, css, format-yaml, format-css, .prettierrc.yaml.
name: tool-prettier
version: 1.0.0
---

# Prettier Code Formatter (`tool-prettier`)

`prettier` is an opinionated code formatter. In Zenith repositories, Prettier
enforces consistent 2-space indentation, 88-character line length, clean
bracket spacing, and uniform quote styling across all YAML manifests (`.github/workflows/*.yaml`,
`.pre-commit-config.yaml`, etc.) and CSS stylesheets (`docs/stylesheets/*.css`).

---

## 1. Core CLI Commands

Format and check YAML and CSS files via Pre-commit or Poe tasks:

```bash
uv run pre-commit run prettier --all-files      # Format all YAML manifests
uv run pre-commit run prettier-css --all-files  # Format all CSS stylesheets
```

In Zenith, task aliases are wired directly into Poe:

```bash
uv run poe format-yaml       # Runs pre-commit run prettier --all-files
uv run poe format-css        # Runs pre-commit run prettier-css --all-files
uv run poe fix               # Auto-fixes Python, TOML, Markdown, YAML, CSS, and typos
uv run poe code-quality      # Full quality pipeline including YAML and CSS checks
```

---

## 2. Configuration (`.prettierrc.yaml`)

Prettier is configured via **`.prettierrc.yaml`** at the project root:

```yaml
printWidth: 88
tabWidth: 2
useTabs: false
semi: true
singleQuote: false
bracketSpacing: true
proseWrap: "preserve"
```

---

## 3. Best Practices & Troubleshooting

- **Preserve Template Syntax**: When Jinja conditionals appear inside YAML or CSS, ensure comments or quotes protect lines from syntax corruption.
- **Always Run via Poe**: Use `uv run poe fix` or `uv run poe code-quality` to automatically format YAML and CSS without requiring global Node.js or npm dependencies.
- **Pre-commit Integration**: Prettier runs automatically during `git commit` via the `mirrors-prettier` hook in `.pre-commit-config.yaml`.
