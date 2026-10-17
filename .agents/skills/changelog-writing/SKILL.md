---
description: >
  Authoritative workflow for maintaining, drafting, and updating Keep-a-Changelog
  compliant changelogs and release notes in Zenith projects. Enforces source-checked
  Git commit ranges, Semantic Versioning, PR inspection via gh CLI, and contributor
  attribution. Use when updating docs/changelog.md, preparing releases, drafting
  release notes, or logging user-facing changes.
name: changelog-writing
version: 1.0.0
---

# Changelog & Release Notes Workflow (`changelog-writing`)

This workflow skill establishes the standards and procedures for maintaining
project changelogs and authoring verifiable, source-checked release notes.

Zenith projects track user-facing modifications in `docs/changelog.md` following
the [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) standard and
[Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

---

## 1. Core Principles

1. **Keep a Changelog Categories**: Every notable change belongs to exactly one category:
   - **`Added`**: New user-facing features or capabilities.
   - **`Changed`**: Changes in existing functionality.
   - **`Deprecated`**: Soon-to-be-removed features.
   - **`Removed`**: Now-removed features.
   - **`Fixed`**: Bug fixes.
   - **`Security`**: Vulnerability fixes or security improvements.
2. **Audience-Centric**: Write for *users and downstream consumers*, not maintainers.
   Explain the impact, benefits, and migration steps rather than detailing internal code
   refactors or mechanical edits.
3. **Source-Checked (Zero Hallucination)**: Never summarize git history from commit
   subject lines alone. Always cross-reference the actual PR bodies, code diffs, and
   deprecation markers.
4. **Human Review**: Draft changelog entries for the human maintainer to review. Do not
   publish releases or push tags without explicit instruction.

---

## 2. Standard Structure (`docs/changelog.md`)

Changelogs follow the standard structure defined in [templates/changelog.md](./templates/changelog.md).
Key structural elements:
- Top-level `## [Unreleased]` section with categorized subsections (`Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`).
- Dated release sections (`## [X.Y.Z] - YYYY-MM-DD`).
- Prominent migration guides immediately beneath version headings when breaking changes occur.
- Bottom comparison links mapping tags to Git commit ranges.

---

## 3. Workflow: Updating `[Unreleased]` During Development

When adding features, fixing bugs, or addressing security concerns on a feature branch:

1. Open `docs/changelog.md`.
2. Locate the `## [Unreleased]` section at the top of the version list.
3. Under the appropriate category header (`### Added`, `### Fixed`, etc.), append a
   concise bullet point describing the change.
4. If the section header does not exist under `## [Unreleased]`, create it.
5. Include a link to the relevant issue or PR and author credit if applicable:
   ```markdown
   - Support streaming JSON-lines response format ([#128](https://github.com/user/project/pull/128)) by @contributor.
   ```

---

## 4. Workflow: Drafting a New Release

When preparing a new release (`vX.Y.Z`):

### Step 1: Establish the Exact Git Range

Identify the previous release tag (e.g. `v0.1.0`) and the target commit or branch (`main`):

```bash
# Fetch latest tags and commits
git fetch --quiet origin --tags

# List commits in the release range
git log --format='%H %s' v0.1.0..HEAD

# Inspect summary of changed files
git diff --stat v0.1.0..HEAD
```

### Step 2: Query Pull Requests and Author Handles

Map each commit in the range to its verified GitHub Pull Request:

```bash
# Query PR metadata using gh CLI
gh pr view <PR_NUMBER> --json number,title,body,author,url
```

For direct commits without a PR number:
```bash
git log --format='%H %an <%ae> %s' v0.1.0..HEAD
```

### Step 3: Verify Actual Behavior in Source Code

Do not trust PR titles alone. Verify what the code actually changed:
- **Breaking Changes**: Check for changed function signatures, renamed CLI options,
  removed module exports, or raised exception types.
- **Deprecations**: Check for `warnings.warn(..., DeprecationWarning)` or docstring
  deprecation notices.
- **Dependencies**: Check `pyproject.toml` for raised minimum dependency bounds.

### Step 4: Promote `[Unreleased]` to Version Header

In `docs/changelog.md`:
1. Change `## [Unreleased]` to include the new version and current date:
   ```markdown
   ## [Unreleased]

   ## [0.2.0] - 2026-10-17
   ```
2. Sort category headers in standard order: `Added`, `Changed`, `Deprecated`, `Removed`,
   `Fixed`, `Security`.
3. If breaking changes exist, prominently document migration instructions directly below
   the version heading:
   ```markdown
   #### Migration Guide
   The `Client.connect()` method now requires an explicit `timeout` keyword argument.
   Replace `Client.connect("localhost")` with `Client.connect("localhost", timeout=10.0)`.
   ```
4. Update comparison links at the bottom of the changelog (if maintained):
   ```markdown
   [Unreleased]: https://github.com/org/repo/compare/v0.2.0...HEAD
   [0.2.0]: https://github.com/org/repo/compare/v0.1.0...v0.2.0
   [0.1.0]: https://github.com/org/repo/releases/tag/v0.1.0
   ```

---

## 5. Verification Gate

Before committing changelog updates:
1. Verify Markdown formatting with `uv run rumdl check docs/changelog.md`.
2. Build documentation site with `uv run poe docs-build` to verify navigation and links.
3. Re-read the drafted entries to confirm zero diff-narrative comments, zero passive voice,
   and accurate contributor handles.
