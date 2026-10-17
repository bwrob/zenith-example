---
description: >
  Manages git branches, conventional commits, and pull requests in Zenith
  projects. Enforces AI disclosure checklists, testing plans, and clean commit
  hygiene. Use when creating branches, preparing commits, staging files, authoring
  commit messages, or creating pull requests.
name: git-workflow
version: 1.0.0
---

# Git Workflow & Pull Request Standards (`git-workflow`)

This workflow skill establishes the git branch management, conventional commit
formatting, and pull request submission standards for Zenith repositories.

---

## 1. Branch Conventions

Maintain clean, dedicated feature branches for non-trivial tasks:

- **Main Branch**: `main` remains protected and always deployable.
- **Feature Branches**: Prefix with purpose:
  - `feat/<short-description>`: New features or capabilities.
  - `fix/<short-description>`: Bug fixes or issue resolutions.
  - `refactor/<short-description>`: Internal code refactoring.
  - `docs/<short-description>`: Documentation additions or updates.
  - `chore/<short-description>`: Dependency updates, CI, or tool configuration.

---

## 2. Conventional Commit Standards

Every commit message must follow the Conventional Commits specification:

```text
<type>(<scope>): <short imperative summary>

[optional body explaining problem and solution rationale]

[optional footer, e.g. Closes #123]
```

### Commit Types

- **`feat`**: A new user-facing feature or library capability.
- **`fix`**: A bug fix.
- **`docs`**: Documentation changes only.
- **`refactor`**: Code changes that neither fix bugs nor add features.
- **`test`**: Adding or correcting test cases.
- **`chore`**: Maintenance, build system, or dependency updates.

### Rules for Commit Messages

1. **Imperative Mood**: Use imperative present tense in the subject ("add feature",
   not "added feature" or "adds feature").
2. **Lowercase Subject**: Start summary with a lowercase letter and no trailing period.
3. **Say Why, Not Which Lines Moved**: A reviewer reading only the subject line should
   understand the motivation for the change, not merely the mechanical edit:

   | Write (Why the change exists) | Not (Which lines moved) |
   | :--- | :--- |
   | `fix(sessions): prevent duplicate events on resume` | `fix(sessions): check interrupt_id before appending` |
   | `feat(cli): support JSON output for machine parsing` | `feat(cli): add --json flag to main` |

   *Self-check*: Read the subject back and ask whether it explains *why* someone made
   the change. If it only names the edited symbol, rewrite it.

### AI Co-Authorship & Attribution Trailers

When AI coding assistants help generate code or commit diffs, credit them in the commit
footer using standard Git `Co-authored-by` trailers:

```git
feat(auth): add token refresh endpoint

Implement automatic token rotation on expiry with sliding window validation.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## 3. Explicit File Staging (No Blanket Staging)

Always stage files explicitly by path (`git add <file1> <file2>`). **Never** use blanket
staging commands (`git add -A`, `git add .`, or `git commit -am`). The developer's
working tree may contain untracked scratch notes, in-progress experimental edits, or
environment files; blanket staging sweeps these untracked modifications into commits
without human consent.

---

## 4. Pre-Commit Verification Gate

Never commit unverified changes. Execute the verification pipeline locally:

```bash
# Verify static analysis, types, and architecture
uv run poe code-quality

# Verify unit tests and coverage
uv run poe test

# Verify all pre-commit hooks pass
uv run pre-commit run --all-files
```

> [!IMPORTANT]
> **Always Re-Read Files Modified by Hooks**: If `uv run poe fix` or
> `uv run pre-commit run --all-files` reformats or modifies any files on disk,
> always re-read those files before making further edits so shifted line numbers
> do not cause stale-file edit collisions.

---

## 5. Pull Request Preparation & AI Disclosure

When opening a pull request, adhere to the project's `PULL_REQUEST_TEMPLATE.md`
and `AI_POLICY.md`:

> [!IMPORTANT]
> **Unsupervised agentic contributions are not accepted**. Every contribution must be
> reviewed, understood, and tested by a human contributor who can substantively explain
> and defend the changes. See `AI_POLICY.md` for full requirements.

### Pull Request Structure

1. **Problem & Solution**:
   - Provide a concise description of the underlying problem.
   - Summarize the chosen solution and architectural rationale.
2. **Testing Plan**:
   - Report passed `pytest` results and coverage status.
   - Document any manual testing performed.
3. **AI Assistance Disclosure (Mandatory)**:
   - Identify AI coding assistants utilized (e.g., Antigravity, Claude Code, Cursor).
   - Summarize the scope of assistance (e.g., initial draft, refactoring, test
     generation).
   - Confirm human review and full accountability for all submitted changes.
   - Confirm that AI assistants are credited in commit messages via `Co-authored-by`
     trailers.

### Shell-Safe Outbound CLI Calls (`gh` & `git`)

When creating commits, issues, or pull requests whose markdown body contains backticks
(`` `code` ``), `$variables`, or double quotes, **never** pass double-quoted inline
strings (`--body "... `code` ..."`), because bash/zsh evaluates backticks as command
substitution and corrupts the text. Always use `--body-file` (or `-F`) with a file in
`.temp/` or a single-quoted heredoc (`<<'EOF'`):

```bash
gh pr create --title "feat(core): add parser" --body-file - <<'EOF'
### Summary
Updated `parse_token` to handle `$HOME` literals safely.
EOF
```
