---
description: >
  Sets up, bootstraps, or repairs a local Zenith Python development environment:
  a uv-managed virtual environment, dependency groups, pre-commit hooks, and
  initial verification runs. Runs only when explicitly requested. Use when asked
  to set up, bootstrap, or repair a development checkout, install project
  dependencies, fix a missing or broken .venv, or prepare a machine for
  contributing. Don't use for routine code editing or individual test runs.
disable-model-invocation: true
name: project-setup
version: 1.0.0
---

# Project Setup & Bootstrap (`project-setup`)

This workflow skill provides the authoritative process for bootstrapping,
configuring, and repairing a local development checkout for a Zenith-based
Python project.

> [!IMPORTANT]
> This skill operates with `disable-model-invocation: true`. Only execute these
> setup commands when explicitly requested by the user to bootstrap or repair the
> environment.

---

## 1. Prerequisites

Before setting up the environment, verify that the required system tools are
installed:

1. **Python 3.12+**:
   ```bash
   python3 --version
   ```

2. **uv (Astral)**:
   ```bash
   uv --version
   ```
   If `uv` is not installed, install it via the official installer:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

---

## 2. Environment Bootstrap Procedure

Execute the following steps sequentially from the repository root:

### Step 1: Synchronize Virtual Environment & Dependencies

Install all declared dependency groups (`dev`, `test`, `lint`, `docs`) inside a
hermetic virtual environment managed by `uv`:

```bash
uv sync
```

This creates `.venv/` and synchronizes all packages defined in `uv.lock`.

### Step 2: Install Pre-Commit Hooks

Activate git pre-commit hooks to automate static verification before commits:

```bash
uv run pre-commit install
```

### Step 3: Run Baseline Quality Verification

Verify that all linters, static type checkers, and complexity limits pass cleanly:

```bash
uv run poe code-quality
```

### Step 4: Run Automated Test Suite

Execute unit tests and coverage thresholds:

```bash
uv run poe test
```

### Step 5: Verify Wheel Artifact Pre-Flight

Verify that distribution packages build cleanly and all package modules import
in an isolated sandbox:

```bash
uv run poe verify-wheel
```

---

## 3. Essential Command Reference

| Workflow | Command | Purpose |
| :--- | :--- | :--- |
| **Sync Environment** | `uv sync` | Synchronize virtual environment with lockfile |
| **Add Runtime Dependency** | `uv add <pkg>` | Add package to `[project.dependencies]` |
| **Add Dev Dependency** | `uv add --group <group> <pkg>` | Add package to specific dependency group |
| **Run Poe Tasks** | `uv run poe <task>` | Run declared development tasks via Poe |
| **Format & Lint** | `uv run poe fix` | Auto-format with Ruff and fix typos |
| **Run Quality Checks** | `uv run poe code-quality` | Run full static verification pipeline |
| **Run Test Suite** | `uv run poe test` | Run pytest with coverage thresholds |
| **Smoke Test Wheel** | `uv run poe verify-wheel` | Verify built wheel in isolated environment |
| **Preview Documentation** | `uv run poe docs-serve` | Launch live Zensical docs server |

---

## 4. Troubleshooting & Recovery

### Missing or Corrupted Virtual Environment

If `.venv/` becomes corrupted or exhibits inconsistent state:

```bash
rm -rf .venv
uv sync
```

### Dependency Cache Desynchronization

If local wheel cache requires refreshing against PyPI:

```bash
uv sync --refresh
```

### Pre-Commit Hook Cache Issues

To reset pre-commit environments:

```bash
uv run pre-commit clean
uv run pre-commit install --install-hooks
```
