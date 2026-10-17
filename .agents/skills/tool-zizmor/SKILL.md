---
description: >-
  Authoritative guide for zizmor GitHub Actions security static analyzer.
  Use when auditing CI/CD workflows for security vulnerabilities, secrets leakage, or script injection.
  Triggers: zizmor, security, github actions, workflows, ci security.
name: tool-zizmor
version: 1.0.0
---


# zizmor GitHub Actions Security Static Analyzer (`tool-zizmor`)

`zizmor` is a high-performance static security analysis tool for GitHub Actions
workflows, written in Rust. It audits CI/CD pipelines for critical security
vulnerabilities, including script injection, untrusted code execution, cache
poisoning, credential exposure, and dangerous trigger configurations.

In Zenith projects, `zizmor` guarantees that workflow pipelines adhere to least-privilege
principles and defense-in-depth supply-chain security standards.

---

## 1. Core CLI Commands

Use these commands to audit workflow configurations locally or in CI:

```bash
# Audit all workflows in .github/workflows
uv run zizmor --config .zizmor.yml .github/workflows

# Run via poethepoet task
uv run poe zizmor

# Full code quality pipeline (includes zizmor)
uv run poe code-quality
```

---

## 2. Configuration & Where It Lives

Zizmor is configured via **`.zizmor.yml`** at the project root:

```yaml
rules:
  unpinned-uses:
    disable: true
```

### Key Rules Checked:
- **`dangerous-triggers`**: Flags insecure triggers such as `pull_request_target`.
- **`cache-poisoning`**: Detects enabled caches in release/publish pipelines that could be manipulated.
- **`artipacked`**: Detects missing `persist-credentials: false` in `actions/checkout`.
- **`unpinned-uses`**: Audits whether action references are locked to specific versions or immutable commit SHAs.

---

## 3. Suppression Patterns

When a workflow requires a specific trigger or configuration for legitimate reasons (e.g. metadata-only inspection on `pull_request_target`), use inline comment annotations:

```yaml
on:
  pull_request_target: # zizmor: ignore[dangerous-triggers] -- This workflow only reads context.payload metadata, never checks out PR code
```
