---
description: >-
  Guide for prek Rust-native Git hook runner and pre-commit lifecycle.
  Use when installing, running, configuring, or debugging Git hooks with prek.
  Triggers: prek, pre-commit, git hooks, hooks, .pre-commit-config.yaml, .prek.toml.
name: tool-prek
version: 1.0.0
---

# Prek Git Hook Runner (`tool-prek`)

`prek` is a fast Git hook manager written in Rust. It serves as a drop-in
alternative to Python `pre-commit`, executing hooks configured in
`.pre-commit-config.yaml` or `.prek.toml` at native speeds.

Zenith uses `prek` to run file hygiene checks, secret detection, TOML and YAML
formatting, and local quality gates before every Git commit.

---

## 1. Core CLI Commands

Execute hooks directly using `uv`:

```bash
uv run prek run --all-files           # Execute all hooks across the repository
uv run prek install                   # Install Git shims into .git/hooks/
uv run prek run <hook_id> -a          # Execute a specific hook across all files
uv run prek update                    # Update repository revisions in config
uv run prek validate-config           # Validate configuration syntax
```

Poe tasks integrate `prek` directly:

```bash
uv run poe format-yaml                # Run Prettier YAML formatting via prek
uv run poe format-css                 # Run Prettier CSS formatting via prek
uv run poe fix                        # Run full auto-fix pipeline including prek
```

---

## 2. Configuration (`.pre-commit-config.yaml`)

`prek` reads `.pre-commit-config.yaml` at the project root:

- **File Hygiene**: `trailing-whitespace`, `end-of-file-fixer`, `check-merge-conflict`, `check-case-conflict`, `check-added-large-files`.
- **Secret Detection**: `gitleaks` scans staged files for leaked tokens and credentials.
- **Manifest Validation**: `validate-pyproject` validates `pyproject.toml` schema integrity.
- **Formatters**: `ruff`, `taplo`, `rumdl`, and `prettier` format Python, TOML, Markdown, YAML, and CSS files.
- **Quality Gates**: Local system hooks execute `pyrefly`, `complexipy`, and `tach`.

---

## 3. Direct Invocations vs. Poe Tasks

Local hooks in `.pre-commit-config.yaml` invoke tools directly using `uv run <tool>`
(for example, `uv run pyrefly check` or `uv run tach check`) rather than delegating
to Poe tasks:

1. **Staged File Argument Passing**: `prek` forwards staged file paths to hooks. Direct tool commands process these paths natively. Wrapping commands in task runners can drop or misroute file arguments.
2. **Subprocess Overhead Reduction**: Direct `uv run <tool>` invocations avoid nested task runner layers, keeping Git commit verification fast.
3. **Deterministic Exit Codes**: Direct commands return clean exit codes to Git without intermediate task runner interpretation.

---

## 4. Best Practices & Troubleshooting

- **Install Hooks on Setup**: Run `uv run prek install` after cloning to enable automated pre-commit verification.
- **Pre-PR Verification**: Run `uv run prek run --all-files` before opening a pull request to verify that all files satisfy repository standards.
- **Drop-in Compatibility**: `prek` accepts standard `pre-commit` arguments such as `--all-files` (`-a`), `--show-diff-on-failure`, and `--skip`.
