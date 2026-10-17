---
description: >-
  Authoritative workflow for proposing, drafting, reviewing, and updating Architecture Decision Records (ADRs) in Zenith projects.
  Enforces the Michael Nygard MADR standard, numbering sequences, status lifecycles, and architectural invariants.
  Use when proposing new architectural choices, documenting significant design decisions, superseding prior decisions, or updating docs/adr/.
  Triggers: adr, architecture decision record, architectural decision, record decision, create adr, document architecture, new adr.
name: adr
version: 1.0.0
---

# Architecture Decision Records (`adr`)

This workflow skill provides the authoritative process for authoring, numbering,
evaluating, and updating Architecture Decision Records (ADRs) in Zenith projects.

Zenith couples strict architectural boundary enforcement via **Tach** with ADRs
in `docs/adr/` to preserve the *rationale*, *context*, and *trade-offs* behind
architectural invariants.

---

## 1. Lifecycle & Status Model

Every ADR transitions through a defined lifecycle:

| Status | Meaning |
| :--- | :--- |
| **`Proposed`** | Under active design review; consensus not yet finalized. |
| **`Accepted`** | Approved by maintainers; actively governs the codebase and architecture. |
| **`Rejected`** | Evaluated and declined. Kept in the archive to document why an approach was avoided. |
| **`Superseded`** | Replaced by a subsequent decision (e.g., `Superseded by ADR-0004`). |
| **`Deprecated`** | No longer relevant due to architectural, platform, or scope evolution. |

---

## 2. Directory & Naming Conventions

All ADRs are stored under `docs/adr/`:

```text
docs/adr/
├── index.md                              # Chronological registry of all decisions
├── template.md                           # Master ADR authoring template
├── 0001-record-architecture-decisions.md # Baseline foundation
└── 0002-<short-imperative-title>.md      # Sequential decisions
```

- **Numbering**: Sequential 4-digit integers starting from `0001`.
- **Filename**: `000X-<kebab-case-title>.md` (e.g., `0002-enforce-slotted-dataclasses.md`).
- **Title**: Imperative statement of the decision (e.g., *Use Tach for Layer Boundaries*).

---

## 3. ADR Authoring Workflow

Execute the following steps when drafting or modifying an ADR:

### Step 1: Scan Existing Decisions & Determine Numbering

Scan `docs/adr/` to identify the highest existing decision number and check for
related or conflicting decisions:

```bash
ls -1 docs/adr/
```

Determine the next sequential identifier (e.g., `0002`).

### Step 2: Instantiate Template

Copy the external template from [templates/adr.md](./templates/adr.md) to
`docs/adr/000X-<kebab-case-title>.md`.

### Step 3: Populate Decision Sections

1. **Title & Metadata**:
   - Number and concise title.
   - Initial status: `Proposed` (or `Accepted` if agreed upon in issue/PR).
   - Date and deciders.
2. **Context & Problem Statement**:
   - What technical, organizational, or architectural problem requires resolution?
   - What constraints, performance budgets, or external dependencies apply?
3. **Decision Drivers**:
   - Key criteria (e.g., type safety, memory footprint, cold-start latency, developer ergonomics).
4. **Considered Options**:
   - List at least 2–3 alternatives evaluated with pros and cons.
5. **Decision Outcome**:
   - Chosen option with explicit technical justification.
6. **Consequences & Architectural Boundaries**:
   - Positive consequences (benefits gained).
   - Negative consequences (compromises or operational burdens accepted).
   - Impact on **Tach** layer boundaries (`tach.toml`) or **Pyrefly** typing contracts.

### Step 4: Register Decision in Documentation

1. Append the new ADR to the table in `docs/adr/index.md`.
2. Add the document path to `nav` and `project.plugins.llmstxt` in `zensical.toml`.
3. Preview the documentation locally:
   ```bash
   uv run poe docs-serve
   ```

### Step 5: Handling Superseded Decisions

When a new ADR replaces an earlier decision:

1. In the **new ADR**: add a reference in Context (`Supersedes [ADR-0002](0002-...).md`).
2. In the **old ADR**: update status to `Superseded by [ADR-000X](000X-...).md`.
3. Update `docs/adr/index.md` status badges accordingly.
