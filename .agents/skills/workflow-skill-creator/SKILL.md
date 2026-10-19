---
description: >-
  Workflow and standards for creating modular agent skills in Zenith repositories.
  Enforces progressive disclosure, structured directories, external template separation,
  standard prefix taxonomy, and ASD-STE100 writing standards. Use when creating, refactoring, or modularizing agent skills.
  Triggers: create skill, new skill, add skill, author skill, modular skill, skill template.
name: workflow-skill-creator
version: 1.0.0
---

# Agent Skill Creator (`workflow-skill-creator`)

This skill defines the standards, directory conventions, prefix taxonomy, and workflows
to create agent skills in Zenith projects.

Agent skills extend coding assistants with specialized runbooks, workflows,
and tool knowledge. They operate under **progressive disclosure**.
The runner loads only the skill `name` and `description` into initial context.
It reads the full content only when activated.

---

## 1. Skill Prefix Taxonomy & Grouping

Every skill in a Zenith project must belong to one of five standardized prefix groups:

| Prefix | Domain & Scope | Examples |
|---|---|---|
| **`sdd-*`** | **Spec-Driven Development Suite**<br/>End-to-end specification authoring, technical planning, TDD implementation, and quality review. | `sdd`, `sdd-spec`, `sdd-plan`, `sdd-implement`, `sdd-review`. |
| **`tool-*`** | **Tool Mechanics & Syntax**<br/>Runbooks and syntax guides for specific external tools, compilers, linters, or libraries. | `tool-uv`, `tool-ruff`, `tool-pytest`, `tool-tach`, `tool-docker`, `tool-fastapi`. |
| **`workflow-*`** | **Lifecycle & Multi-Step Procedures**<br/>Operational processes, version control, release ceremonies, audits, and checklists. | `workflow-git`, `workflow-code-review`, `workflow-changelog`, `workflow-adr`, `workflow-setup`. |
| **`guide-*`** | **Engineering Conventions & Style**<br/>Invariants, coding paradigms, architecture patterns, and technical writing rules. | `guide-python`, `guide-ste100`, `guide-api-design`. |
| **`domain-*`** | **Reserved: Project Business Logic**<br/>**Reserved exclusively for the author of the instantiated project.** Documents business rules, domain models, and application workflows. | `domain-billing`, `domain-auth`, `domain-data-pipeline`. |

> [!IMPORTANT]
> The `domain-*` prefix is strictly reserved for the end user and project author. The Zenith template includes zero `domain-*` skills out-of-the-box so the application namespace remains completely unpolluted.

---

## 2. Skill Complexity Tiering

Select the structure based on skill complexity:

### Tier A: Simple Skill (Single File)
- **When to Use**: Straightforward procedures, tool guides, or concise workflows
  under 100–150 lines without boilerplate.
- **Structure**: A single `SKILL.md` file at `.agents/skills/<prefix>-<name>/SKILL.md`.
- **Constraint**: Do not create subdirectories for single-page instructions.

### Tier B: Complex Skill (Structured Directory)
- **When to Use**: Workflows with templates, reference manuals, multi-file examples,
  or helper scripts.
- **Structure**: An organized directory following the canonical pattern:
  ```text
  .agents/skills/<prefix>-<name>/
  ├── SKILL.md          # Required: Lean core workflow, decision logic, and frontmatter
  ├── templates/        # Required if templates exist: External templates in separate files
  ├── examples/         # Optional: Multi-file recipes or concrete implementations
  ├── references/       # Optional: Technical manuals, specifications, and cheat-sheets
  └── scripts/          # Optional: Executable automation or validation scripts
  ```

---

## 3. Hard Architectural Rules

### Rule 1: Place Templates in Dedicated Files
- **Never embed large templates inline**: Do not include document skeletons, boilerplate
  code, config files, or report formats directly in `SKILL.md`.
- **Store in `templates/`**: Place each template in a file under `templates/`
  (for example, `templates/changelog.md` or `templates/review_output.md`).
- **Use relative links**: Link to the template file from `SKILL.md` using relative
  Markdown links: `[templates/SKILL_TEMPLATE.md](./templates/SKILL_TEMPLATE.md)`.

### Rule 2: Move Lengthy References and Examples to Subdirectories
- **References (`references/`)**: Split technical manuals, plugin lists, or API
  specifications into separate documents (such as `references/hypothesis.md`).
- **Examples (`examples/`)**: Store complete recipes, sample scripts, or multi-file
  demonstrations in `examples/` instead of inline code blocks.

### Rule 3: Maintain Progressive Disclosure and Lean `SKILL.md`
- Focus `SKILL.md` on triggers, decision paths, and core step-by-step instructions.
- Ensure the model can read `SKILL.md` in one pass. Read sub-files on demand.

### Rule 4: Write in Simplified Technical English (ASD-STE100)
- Follow the [guide-ste100](../guide-ste100/SKILL.md) skill when authoring prose.
- Write short, unambiguous, active-voice sentences.
- Keep procedural sentences under 20 words. Keep descriptive sentences under 25 words.
- Do not use semicolons, phrasal verbs, nominalizations, or marketing adjectives.
- Run the STE linter to verify compliance:
  ```bash
  uv run python .agents/skills/guide-ste100/scripts/ste-lint.py .agents/skills/<name>/SKILL.md
  ```

---

## 4. Skill Creation Workflow

Follow these steps to create a new skill:

### Step 1: Select Prefix Group and Tier
1. Select one of the 4 valid prefixes: `tool-`, `workflow-`, `guide-`, or `domain-`.
2. Select Tier A (single `SKILL.md`) or Tier B (structured directory).
3. If Tier B, initialize the directory layout:
   ```bash
   mkdir -p zenith-example/.agents/skills/<prefix>-<name>/{templates,examples,references,scripts}
   ```

### Step 2: Author Frontmatter and Core Instructions
1. Copy [templates/SKILL_TEMPLATE.md](./templates/SKILL_TEMPLATE.md) to
   `zenith-example/.agents/skills/<prefix>-<name>/SKILL.md`.
2. Craft the YAML frontmatter block:
   - **`name`**: Lowercase, hyphenated with prefix (for example, `workflow-changelog` or `domain-billing`).
   - **`description`**: Summary stating *what* the skill does and *when* to use it,
     including explicit triggers.
3. Write clear, step-by-step instructions following ASD-STE100 standards.

### Step 3: Extract Templates and References
1. Extract file templates into `templates/<filename>`.
2. Extract reference tables or manuals into `references/<filename>`.
3. Extract complete code examples into `examples/<filename>`.
4. Link all extracted assets from `SKILL.md` with relative links.

### Step 4: Synchronize and Register
1. Maintain shared skills in `zenith-example/.agents/skills/<prefix>-<name>/`.
2. Run skill synchronization to create relative symlinks in `.agents/skills/<prefix>-<name>/`:
   ```bash
   uv run poe sync-skills
   ```
3. If the skill is repo-only (such as `workflow-inspect-repo`), create it directly in
   `.agents/skills/<prefix>-<name>/` and omit it from the template.
4. Add the skill to the skills list in `AGENTS.md` and `zenith-example/AGENTS.md`.
5. Add the skill existence assertion to `tests/test_template.py`.

### Step 5: Verify Formatting and Tests
Run the full verification suite:
```bash
uv run python .agents/skills/guide-ste100/scripts/ste-lint.py .agents/skills/<name>/SKILL.md
uv run poe check-skills
uv run poe sync-skills-check
uv run poe code-quality
```
