---
name: sdd-implement
description: >-
  Executes approved implementation plans using disciplined Test-Driven Development (TDD).
  Runs red-green-refactor loops, verifies quality gates per task, and stops on drift.
  Requires a developer-approved spec.md and plan.md before any code edit.
  Mandatory whenever executing tasks from an SDD plan, even without prompt triggers.
  Triggers: sdd implement, execute plan, run tasks, tdd implementation, sdd coding.
version: 1.2.0
---

# Test-Driven Implementation (`sdd-implement`)

This skill defines the process to execute technical implementation plans in this project.
It enforces sequential task execution, Test-Driven Development (TDD), and per-task verification gates.

---

## 0. Entry Gate

Verify these conditions before any file edit, branch creation, or dependency change:

1. Open `.specs/<feature-id>/spec.md` and `.specs/<feature-id>/plan.md`.
2. Verify that both files exist.
3. Verify that both files show `Status: Approved` and a filled `Approval` field.

If a condition fails, stop and end the turn.
Tell the developer which artifact is missing or not approved.
Recommend `/sdd` for the full lifecycle, or `/sdd-spec` and `/sdd-plan` for the missing phase.

> [!IMPORTANT]
> Do not write, complete, or approve `spec.md` or `plan.md` in this skill.
> A direct invocation of `sdd-implement` does not activate Autonomous Mode.
> Apply the Approval Protocol in the [sdd](../sdd/SKILL.md) skill.

---

## 1. Core Principles & Execution Invariants

1. **Strict Sequential Execution**:
   Execute tasks one at a time in the exact sequence declared in `.specs/<feature-id>/plan.md`.
   Do not batch tasks or jump ahead.
2. **Red-Green-Refactor Cycle**:
   For every task, follow three discrete phases:
   - **Red**: Author failing unit tests that assert the acceptance criteria.
   - **Green**: Write the minimal production code necessary to pass the tests.
   - **Refactor**: Clean up the implementation while preserving passing tests.
3. **Hermetic Task Verification**:
   Execute the verification command defined in the task before marking it complete.
   Never proceed to the next task while current tests fail.
4. **Complexity Reset Rule**:
   If an implementation requires layered workarounds or complex type suppressions, stop immediately.
   Re-evaluate the approach from first principles.
5. **Drift Protocol**:
   If an unhandled requirement emerges, pause code edits.
   Propose the change to `spec.md` and `plan.md`, and set both to `Status: Draft`.
   Stop and obtain developer approval before you write further code.

---

## 2. Subagent Profile: `sdd-implementer`

When operating in multi-agent environments, invoke a dedicated `sdd-implementer` subagent:

- **Role**: Software Engineer and TDD Implementer.
- **Permissions**: Workspace file edits and hermetic command execution (`uv run ...`).
- **Goal**: Implement all tasks from `.specs/<feature-id>/plan.md` with passing tests.

---

## 3. Implementation Procedure

Follow these steps for each task in the plan:

### Step 1: Select the Next Task

Open `.specs/<feature-id>/plan.md`.
Locate the first incomplete checkbox (`- [ ] **Task N: ...**`).
Review the requirement ID, target files, and verification gate.

### Step 2: Write Failing Tests (Red)

Open or create the appropriate unit test file in `tests/test_<module>.py`.
Write tests that assert the expected behavior defined in the specification.
Run the test command to verify that tests fail for the expected reason:

```bash
uv run pytest tests/test_<module>.py
```

### Step 3: Implement Minimal Solution (Green)

Implement the necessary dataclasses, protocols, or functions in `src/`.
Write only the code needed to satisfy the failing tests.
Run the test command again until all tests pass:

```bash
uv run pytest tests/test_<module>.py
```

### Step 4: Refactor and Format

Refactor code to satisfy project standards:
- Ensure cognitive complexity remains at 10 or less.
- Ensure type annotations satisfy Pyrefly strict mode.
- Apply auto-fixers and formatters:

```bash
uv run poe fix
```

### Step 5: Execute Task Verification Gate

Run the full verification command declared in the task:

```bash
uv run poe test
```

### Step 6: Commit and Record Task Progress

After tests pass, commit the code changes and record the commit hash:

1. Stage and commit the implementation code following `workflow-git`:
   ```bash
   git add <modified-files>
   git commit -m "<type>(<scope>): <task summary>"
   ```
2. Obtain the short commit hash:
   ```bash
   git rev-parse --short HEAD
   ```
3. Update `.specs/<feature-id>/plan.md`:
   - Change the task checkbox from `[ ]` to `[x]`.
   - Append the short commit hash in parentheses:
     `- [x] **Task N: [Title]** (<sha>)`
4. Do not commit `plan.md`.
   Git ignores the `.specs/` directory, so the plan stays a local working file.
5. Proceed to the next task in the phase.

### Step 7: Execute Phase Checkpoint Protocol

When you complete the final task in a Phase, do all of these steps before the next task:

1. **Verify Module Test Coverage**:
   Inspect modified files under `src/` since the previous checkpoint:
   ```bash
   git diff --name-only <prev-checkpoint-sha|main> HEAD -- 'src/*'
   ```
   Verify that each modified module has a corresponding unit test file in `tests/`.

2. **Execute Quality Gates**:
   Run the test suite and quality verification:
   ```bash
   uv run poe test
   uv run poe code-quality
   ```
   Fix every gate failure before you continue.

3. **Record Phase Checkpoint**:
   Obtain the latest commit hash (`git rev-parse --short HEAD`).
   Update the phase heading in `.specs/<feature-id>/plan.md` to record the checkpoint:
   `### Phase <N>: [Name] [checkpoint: <sha>]`.

4. **Generate Manual Verification Recipe**:
   Create a step-by-step manual test recipe for developer inspection (for example, a CLI invocation or REPL call with expected output).

5. **Stop for Developer Approval**:
   Present the gate results and the manual verification recipe, then end the turn.
   Start the next phase only after the developer approves.
   Skip this stop only if the developer explicitly requested Autonomous Mode (for example, `--autonomous` or `/goal`).

---

## 4. Verification & Quality Gate

Verify that the implementation satisfies these criteria:

1. The Entry Gate passed before the first code edit.
2. All task checkboxes in `.specs/<feature-id>/plan.md` show complete status.
3. Every phase heading records a checkpoint, and the developer approved each phase.
4. The entire test suite passes with 100% branch coverage.
5. Auto-formatters and linters report zero errors.
