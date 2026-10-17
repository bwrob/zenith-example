---
description: Authoritative usage guidelines, patterns, and conventions for Zenith Example. Use when writing, refactoring, or reviewing code using Zenith Example.
name: zenith-example
version: 1.0.0
---

# Zenith Example Developer Guidelines

Authoritative engineering guidelines for working with `zenith_example`.

## API Conventions

- Import primary public interfaces directly from `zenith_example`:
  ```python
  from zenith_example import get_greeting
  ```
- Use strict typing across all function boundaries.
- Adhere to the core architectural patterns defined in `AGENTS.md`.

## Integration with AI Coding Assistants

This library bundles official agent skills directly inside its package distribution.
To discover and synchronize skills from this and other installed dependencies in your project:

```bash
uvx library-skills --all -y
```
