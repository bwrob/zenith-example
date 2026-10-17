# Getting Started

This guide explains how to install and develop with **Zenith Example**.

## Prerequisites

Ensure you have Python 3.13 and `uv` installed.

## Installation

Install using `uv`:

```bash
uv add zenith-example
```

## Basic Usage

Import the primary functions into your application:

```python
from zenith_example import get_greeting

message = get_greeting("Developer")
print(message)
```

## CLI Usage

Run commands directly via `uv`:

<div class="termy">

```console
$ uv run zenith-example greet "World"

✨ Hello, World!

// Inspect CLI options and help
$ uv run zenith-example --help

<b>Usage: </b><b>zenith-example [OPTIONS] COMMAND [ARGS]...</b>

╭─ Options ─────────────────────────────────────────╮
│ --version  -v        Show version and exit.       │
│ --help               Show this message and exit.  │
╰───────────────────────────────────────────────────╯
╭─ Commands ────────────────────────────────────────╮
│ greet                Display a personalized       │
│                      greeting.                    │
╰───────────────────────────────────────────────────╯
```

</div>

## Development Workflow

Clone the project and synchronize development dependencies:

```bash
git clone https://github.com/bwrob/zenith-example.git
cd zenith-example
uv sync
```

Run test suites and quality checks with Poe the Poet:

```bash
# Run tests
uv run poe test

# Run quality checks
uv run poe code-quality
```

> [!TIP]
> **Hermetic Task Execution**: Always invoke tasks using `uv run poe <task>`. Tasks
> inherit project environment flags, strict encoding checks (`PYTHONUTF8=1`), and
> hermetic virtual environments.

<details>
<summary>Advanced Testing &amp; Marker Options</summary>

Free arguments can be forwarded directly through Poe to underlying tools using `--`:

```bash
uv run poe test -- -k "test_greeting" -v
```

</details>

### Verification Checklist

- [x] Python 3.13 and `uv` installed
- [x] Project cloned and dependencies locked
- [ ] Run test suite with `uv run poe test`
- [ ] Run code quality checks with `uv run poe code-quality`
- [ ] Preview documentation with `uv run poe docs-serve`

> [!TIP]
> When browsing docs, press ++slash++ or ++cmd+k++ (or ++ctrl+k++ on Linux/Windows) to
> instantly search documentation symbols and pages. Hovering internal links like
> [API Reference](reference.md) activates floating link previews.

### Tested Code Snippets

Code snippets can be embedded directly from verified tests or source files using
`--8<--`:

```markdown
--8<-- "tests/test_core.py:10:14"
```

## Architecture & Diagrams

Mermaid diagrams render natively in documentation. Below are examples illustrating
the project structure, execution sequence, and state lifecycle:

### Component Architecture

```mermaid
flowchart TD
    USER["User / Client"] -->|Input| APP["zenith-example"]
    APP --> CORE["Core Engine"]
    CORE --> OUTPUT["Greeting Output"]
```

### Execution Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor Dev as Developer
    participant App as Application
    participant Core as Core Module
    Dev->>App: Invocation
    App->>Core: get_greeting(name)
    Core-->>App: "Hello, {name}!"
    App-->>Dev: Formatted Result
```

### State Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Standby
    Standby --> Parsing: Receive Input
    Parsing --> DefaultGreeting: Name is Blank
    Parsing --> CustomGreeting: Name Provided
    DefaultGreeting --> Completed: Return "Hello, World!"
    CustomGreeting --> Completed: Return Formatted Name
    Completed --> [*]
```
