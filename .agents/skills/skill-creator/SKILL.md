---
description: >-
  Authoritative workflow and standards for designing, architecting, and creating modular agent skills in Zenith repositories.
  Enforces progressive disclosure, structured directories for complex skills (templates/, examples/, references/, scripts/), external template separation, and lean SKILL.md authoring.
  Use when creating, architecting, refactoring, or modularizing agent skills.
  Triggers: create skill, new skill, add skill, author skill, modular skill, skill template.
name: skill-creator
version: 1.0.0
---


# Agent Skill Creator (`skill-creator`)

This skill establishes the architectural standards, directory conventions, and
authoring workflows for creating high-performance agent skills in Zenith projects.

Agent skills extend coding assistants with specialized runbooks, domain workflows,
and tool knowledge. They operate under **progressive disclosure**: only the skill's
`name` and `description` are loaded into initial context, while the full content is
read only when activated.

---

## 1. Skill Complexity Tiering

Choose the appropriate structural tier based on the skill's complexity:

### Tier A: Simple Skill (Single File)
- **When to Use**: Straightforward procedures, tool cheat-sheets, or concise workflows
  requiring under 100–150 lines of instructions without heavy boilerplate.
- **Structure**: A single `SKILL.md` file located at `.agents/skills/<name>/SKILL.md`.
- **Constraint**: Do not create subdirectories for simple single-page instructions.

### Tier B: Complex Skill (Structured Directory)
- **When to Use**: Workflows involving document/code templates, detailed reference manuals,
  multi-file examples, or automation helper scripts.
- **Structure**: An organized directory following the canonical pattern:
  ```text
  .agents/skills/<name>/
  ├── SKILL.md          # Required: Lean core workflow, decision logic & frontmatter
  ├── templates/        # Required if templates exist: External templates in separate files
  ├── examples/         # Optional: Multi-file code recipes or concrete implementations
  ├── references/       # Optional: Lengthy technical manuals, specifications, cheat-sheets
  └── scripts/          # Optional: Executable automation or validation scripts
  ```

---

## 2. Hard Architectural Rules

### Rule 1: Templates Must Live in Separate Files
- **Never embed large templates inline**: Do not include multi-screen document skeletons,
  boilerplate code templates, config files, or report formats directly inside `SKILL.md`.
- **Place in `templates/`**: Store every template in a dedicated file under `templates/`
  (e.g., `templates/changelog.md`, `templates/review_output.md`).
- **Relative Linking**: Link to the template file from `SKILL.md` using relative Markdown
  links: `[templates/SKILL_TEMPLATE.md](./templates/SKILL_TEMPLATE.md)`.

### Rule 2: Lengthy References & Multi-File Examples in Dedicated Directories
- **References (`references/`)**: Detailed technical manuals, third-party plugin lists,
  or deep API specifications must be split into focused documents (e.g.,
  `references/hypothesis.md`, `references/declarative_primitives.md`).
- **Examples (`examples/`)**: Complete application recipes, sample CLI scripts, or
  multi-file demonstration patterns belong in `examples/<name>.py` rather than inline
  code blocks.

### Rule 3: Progressive Disclosure & Lean `SKILL.md`
- Keep `SKILL.md` focused strictly on **triggers, decision paths, and core step-by-step
  instructions**.
- The model should be able to read `SKILL.md` in a single pass without consuming excess
  context window. Sub-files are read on demand when the specific step requires them.

### Rule 4: Zero Slop & Compressed Writing
- Avoid conversational filler, chatty introductions, or obvious language explanations.
- Use imperative, concise instructions, high-density Markdown tables, and exact shell
  commands.

---

## 3. Skill Creation Workflow

Follow these steps when creating a new skill:

### Step 1: Determine Scope & Tier
1. Identify the workflow's trigger conditions and boundaries.
2. Determine if it is a Tier A (single `SKILL.md`) or Tier B (structured directory).
3. If Tier B, initialize the directory layout:
   ```bash
   mkdir -p .agents/skills/<name>/{templates,examples,references,scripts}
   ```

### Step 2: Author Frontmatter & Core Instructions
1. Copy [templates/SKILL_TEMPLATE.md](./templates/SKILL_TEMPLATE.md) to `.agents/skills/<name>/SKILL.md`.
2. Craft an authoritative YAML frontmatter block:
   - **`name`**: Lowercase, hyphenated (e.g., `changelog-writing`, `git-workflow`).
   - **`description`**: Third-person summary stating *what* the skill does and *when* to
     use it, including explicit keywords and triggers.

### Step 3: Extract Templates and References
1. Extract any file templates into `templates/<filename>`.
2. Extract any deep reference tables or bulky manuals into `references/<filename>`.
3. Extract complete code examples into `examples/<filename>`.
4. Link all extracted assets from `SKILL.md` using relative links.

### Step 4: Synchronize & Register
1. If the skill applies to generated projects:
   - Copy the skill directory to `zenith-example/.agents/skills/<name>/`.
   - Add the skill name to the workflow skills list in `AGENTS.md` and
     `zenith-example/AGENTS.md`.
   - Add the skill existence assertion to `tests/test_template.py`.
2. If the skill is Zenith repo-specific (e.g., `inspect-module-setup`), maintain it only in
   the root `.agents/skills/`.

### Step 5: Verify Formatting & Tests
1. Verify pre-commit hooks and tests:
   ```bash
   uv run pre-commit run --all-files
   uv run pytest tests/test_template.py
   ```
