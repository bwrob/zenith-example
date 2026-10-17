---
name: <skill-name>
description: >-
  <Authoritative description explaining WHAT this skill accomplishes and WHEN the agent
  should use it. Include clear intent triggers (e.g. "Use when the user asks to...")>.
version: 1.0.0
---

# <Skill Title> (`<skill-name>`)

<Brief 1-2 sentence overview of the domain and purpose of this skill.>

---

## 1. Core Principles & Invariants

1. **<Principle 1>**: <Actionable guideline, architectural boundary, or invariant.>
2. **<Principle 2>**: <Actionable guideline, architectural boundary, or invariant.>

---

## 2. Standard Workflow & Procedures

### Step 1: <Initial Phase>
<Actionable instructions, CLI commands, or decision trees.>

```bash
uv run <command>
```

### Step 2: <Execution Phase>
<Actionable instructions. If document, code, or configuration templates are required,
link to external templates in `./templates/` rather than embedding large inline blocks.>

- See template: [templates/<name>.<ext>](./templates/<name>.<ext>)

---

## 3. Verification & Quality Gate

<Mandatory verification commands to confirm the workflow succeeded without regressions.>

```bash
uv run <verification-command>
```
