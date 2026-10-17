---
description: >-
  Run and manage project tasks with poethepoet (poe) in uv projects.
  Use when defining, debugging, executing, or organizing automated tasks.
  Triggers: poe, poethepoet, tasks, task runner, poe_tasks.toml.
name: tool-poethepoet
version: 1.0.0
---


# Poe the Poet Task Runner (`tool-poethepoet`)

Poethepoet (`poe`) is a task runner for Python projects. It defines and
documents project commands inside `pyproject.toml` or standalone config files
such as `poe_tasks.toml`.

## 1. Quick Start and Execution

Run tasks using `uv run poe`. Poe runs each command inside the project
virtual environment automatically without needing manual activation.

```bash
uv run poe                       # List all available tasks with descriptions
uv run poe --help                # Show usage help and options
uv run poe <task>                # Execute a specific task
uv run poe <task> -v             # Execute with verbose output
uv run poe -d <task>             # Dry run: print command without executing
uv run poe <task> -- -x          # Pass free arguments directly to tool
uv run poe -C /path <task>       # Run as if from another directory
```

> [!IMPORTANT]
> Always prefer running poe tasks instead of invoking tools directly.
> Poe tasks inherit project defaults, environment variables, and flags.

## 2. Core Task Types

Poe supports multiple declarative task types defined under `[tasks]` or
`[tool.poe.tasks]`.

### Command Tasks (`cmd`)

Runs a CLI binary or executable command as a subprocess without a shell:

```toml
[tasks.test]
cmd = "pytest tests/"
help = "Run unit and functional test suite"
```

Command tasks support parameter expansion (`${VAR}`, `${VAR:-default}`,
`${VAR:+alt}`), globbing (`*.py`), and free argument forwarding.

### Script Tasks (`script`)

Calls a Python function directly from a project module or standard library:

```toml
[tasks.generate]
script = "scripts.codegen:main"
help = "Run code generator script"

[tasks._clean-dist]
script = "shutil:rmtree('dist', ignore_errors=1)"
```

Arguments can be passed directly in the call expression or forwarded as keyword
arguments when referencing a callable.

### Shell Tasks (`shell`)

Executes POSIX shell pipelines, redirections, or multi-command scripts:

```toml
[tasks.stats]
help = "Show project code line counts"
shell = """
echo "Source lines: $(find src -name '*.py' | xargs wc -l)"
echo "Test lines:   $(find tests -name '*.py' | xargs wc -l)"
"""
```

Only public arguments are exported to shell environments.

### Sequence Tasks (`sequence`)

Executes multiple subtasks in sequential order. Execution stops if any task
fails:

```toml
[tasks.check]
help = "Run linting, type-checking, and tests sequentially"
sequence = ["lint", "type-check", "test"]
```

### Parallel Tasks (`parallel`)

Executes independent subtasks concurrently across threads:

```toml
[tasks.all-checks]
help = "Run independent checks concurrently"
parallel = ["lint", "type-check"]
```

### Expression Tasks (`expr`) & Switch Tasks (`switch`)

`expr` evaluates a Python expression directly and prints the result, while
`switch` conditionally executes steps based on an argument, environment
variable, or platform:

```toml
[tasks.platform]
expr = "sys.platform"
help = "Print current operating system platform"

[tasks.install-deps]
help = "Install platform-specific dependencies"
switch = [
  { if = "sys.platform == 'darwin'", cmd = "brew install libmagic" },
  { if = "sys.platform == 'linux'", cmd = "apt-get install -y libmagic1" },
]
```

> [!CAUTION]
> **Two Silent-Failure Rules for `expr`, `switch.control.expr`, and parens-form
> `script = "mod:fn(arg)"`**:
>
> 1. **Declared args ➔ use bare name, never `${name}`**:
>    Write `expr = "AWS_REGION"` ✅. Writing `expr = "${AWS_REGION}"` ❌ routes
>    through the OS environment and evaluates to **silently empty** for private
>    `_`-prefixed args. (Note: no-parens `script = "mod:fn"` automatically
>    passes declared args as kwargs—never name them in the call.)
> 2. **Environment variables ➔ use unquoted `${VAR}`**:
>    In Python expressions, `${VAR}` compiles to the attribute access
>    `__env.VAR` (not textual string interpolation). Therefore
>    `expr = "${STAGE}"` ✅ yields the variable's value, whereas
>    `expr = "'${STAGE}'"` ❌ yields the literal string `"__env.STAGE"`. Call
>    string methods directly: `expr = "${STAGE}.upper()"`.

## 3. Advanced Task Composition and DAG Dependencies

Compose robust workflows using Poe's directed acyclic graph (DAG) dependency
engine and argument binding.

### Defining Task Dependencies (`deps`)

Declare prerequisite tasks that must finish before the target task runs:

```toml
[tasks.build]
cmd = "uv build"
deps = ["code-quality", "test"]
help = "Build distribution packages after verification"
```

### Capturing Task Output (`uses` and `uses_env`)

Capture stdout from prerequisite tasks as variables or environment maps:

```toml
[tasks._get-version]
script = "scripts.version:get"

[tasks.tag]
cmd = "git tag v${_version}"
help = "Tag git commit with current package version"
uses = { _version = "_get-version" }
```

Use `uses_env` to load multiline environment variables from dotenv-formatted
stdout.

### CLI Arguments and Defaults

Define typed CLI options that users can pass when invoking `uv run poe`:

```toml
[tasks.test]
args = [
  { name = "markers", options = ["-m"], default = "", help = "Marker filter" },
]
cmd = "pytest ${markers}"
help = "Run tests with optional markers"
```

### Forwarding Arguments in Sequences

Use `$POE_EXTRA_ARGS` to forward extra CLI flags to subtasks in a sequence:

```toml
[tasks.check]
help = "Run checks and forward extra flags"
sequence = ["lint $POE_EXTRA_ARGS", "test $POE_EXTRA_ARGS"]
```

### The `_` Prefix Convention for Internal Tasks

Prefix internal tasks, arguments, or environment variables with an underscore
`_` to hide them from the public `uv run poe` listing:

```toml
[tasks._clean-dist]
script = "shutil:rmtree('dist', ignore_errors=1)"

[tasks.clean]
help = "Remove build artifacts and cache directories"
sequence = ["_clean-dist"]
```

Internal `_` tasks cannot be called directly from the CLI and must be invoked
via `sequence`, `parallel`, `deps`, or `uses`.

### Organizing Large Task Sets with `groups`

Categorize related tasks under labeled headings in `uv run poe` output using
`[groups.<name>]` (or `[tool.poe.groups.<name>]` in `pyproject.toml`):

```toml
[groups.qa]
heading = "Quality Assurance"

[groups.qa.tasks.lint]
cmd = "ruff check ."
help = "Lint codebase"
```

### Side-Channel Drift Verification Without Dirtying the Working Tree

When verifying that a generated artifact (such as a JSON Schema or OpenAPI spec)
is up to date, generate it to a gitignored comparison path and diff with
`git diff --no-index` so running the check never mutates tracked files:

```toml
[tasks.schema-check-drift]
env = { _tmp = ".temp/schema-check.json", GIT_PAGER = "cat" }
help = "Verify committed schema matches generator output"
sequence = [
  "schema-build ${_tmp}",
  { cmd = "git diff --no-index docs/schema.json ${_tmp}" },
]
```

## 4. Environment Variables Management

Poe provides environment variable configuration at both the global project level
and the task level.

### Global Environment Variables (`env`)

Configure environment variables exposed to all tasks in `pyproject.toml` or
standalone task files (`poe_tasks.toml`):

```toml
# In pyproject.toml:
[tool.poe.env]
PYTHONUTF8 = "1"
PYTHONWARNDEFAULTENCODING = "1"
APP_ENV = "test"
DATABASE_URL = "postgresql://${DB_USER:-postgres}:${DB_PASSWORD:-secret}@localhost:5432/app"

# In standalone poe_tasks.toml:
[env]
PYTHONUTF8 = "1"
PYTHONWARNDEFAULTENCODING = "1"
APP_ENV = "test"
```

- **POSIX Parameter Expansion**: Global variables support parameter expansion
  (`${VAR}`, `${VAR:-default}`, `${VAR:+alt}`) referencing variables already
  defined in the host environment or referenced env files.
- **Default Fallback (`default`)**: Use `{ default = "fallback" }` or
  `VAR.default = "fallback"` to set a variable only if it is not already
  defined in the host environment:

  ```toml
  [env.PORT]
  default = "8000"
  ```

### Global Env Files (`envfile`)

Load external `.env` files for all tasks in the project:

```toml
# In pyproject.toml:
[tool.poe]
envfile = ".env"

# Or a cascade of multiple files loaded in order:
[tool.poe]
envfile = [".env", ".env.local"]

# In standalone poe_tasks.toml:
envfile = [".env", ".env.local"]
```

### Task-Level Environment Overrides

Individual tasks can extend or override global variables using `env` or
`envfile`:

```toml
[tasks.test]
cmd = "pytest tests/"
env = { APP_ENV = "ci", PYTEST_TIMEOUT = "30" }
envfile = ".env.test"
```

Task-level settings take precedence over global options, providing precise
control per command.

## 5. Declarative Primitives Over Bash Scripting

Before writing a `shell` task, check if a declarative Poe feature expresses the
intent portably. See the full mapping in:
👉 [references/declarative_primitives.md](./references/declarative_primitives.md)

Common declarative equivalents include using `arg` definitions with `default`,
`choices`, and `required`, conditional dispatch with `switch`, capturing task outputs
with `uses`/`uses_env`, and chaining tasks via `sequence` or `parallel`.

## 6. Best Practices and Rules

Follow these engineering conventions when editing poe tasks:

- **Use global `env` for project-wide runtime flags**: Set cross-cutting flags
  (such as `PYTHONUTF8 = "1"` and `PYTHONWARNDEFAULTENCODING = "1"`) under `[env]` (or
  `[tool.poe.env]`) rather than repeating them across multiple individual tasks.
- **Compose, don't recurse**: Use `sequence`, `parallel`, or `deps` to chain
  tasks. Never shell out using `cmd = "poe other-task"`.
- **Always provide `help`**: Every public task must include a concise `help`
  string for self-documentation.
- **Never hand-edit dependencies**: Use `uv add <pkg>` or
  `uv add --group <group> <pkg>` rather than modifying `pyproject.toml`
  manually.
- **Inspect discovery**: Run `uv run poe --help` to confirm tasks parse and
  documentation displays properly.
