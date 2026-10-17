#!/usr/bin/env python3
"""Validate structural invariants of agent skills in .agents/skills/.

Ensures each skill adheres to the Zenith skill standard:
- Directory contains SKILL.md.
- Valid YAML frontmatter with `name` matching directory and non-empty `description`.
- Internal links to templates/, references/, and examples/ resolve to actual files.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


def parse_frontmatter(content: str) -> dict[str, str]:
    """Parse simple YAML frontmatter between leading `---` markers."""
    if not content.startswith("---"):
        raise ValueError("Missing leading '---' frontmatter boundary")

    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError("Unclosed frontmatter; expected closing '---'")

    raw_yaml = parts[1]
    metadata: dict[str, str] = {}
    current_key: str | None = None
    multiline_buf: list[str] = []

    for line in raw_yaml.splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("#"):
            continue

        if ":" in line and not line.startswith(" ") and not line.startswith("\t"):
            if current_key and multiline_buf:
                metadata[current_key] = " ".join(multiline_buf).strip()
                multiline_buf = []
            key, val = line.split(":", 1)
            current_key = key.strip()
            val_clean = val.strip().strip("'\"")
            if val_clean in (">", ">-", "|", "|-"):
                multiline_buf = []
            elif val_clean:
                metadata[current_key] = val_clean
        elif current_key:
            multiline_buf.append(trimmed)

    if current_key and multiline_buf:
        metadata[current_key] = " ".join(multiline_buf).strip()

    return metadata


def validate_skill(skill_dir: Path) -> list[str]:
    """Validate a single skill directory and return a list of error messages."""
    errors: list[str] = []
    skill_file = skill_dir / "SKILL.md"

    if not skill_file.is_file():
        return [f"Missing required SKILL.md in {skill_dir.name}"]

    try:
        content = skill_file.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"Failed to read {skill_file}: {exc}"]

    try:
        frontmatter = parse_frontmatter(content)
    except (ValueError, KeyError, IndexError) as exc:
        return [f"Invalid frontmatter in {skill_dir.name}/SKILL.md: {exc}"]

    # Validate name
    name = frontmatter.get("name")
    if not name:
        errors.append(f"{skill_dir.name}/SKILL.md: missing 'name' in frontmatter")
    elif name != skill_dir.name:
        errors.append(
            f"{skill_dir.name}/SKILL.md: frontmatter name '{name}' does not match directory '{skill_dir.name}'"
        )

    # Validate description
    desc = frontmatter.get("description")
    if not desc:
        errors.append(f"{skill_dir.name}/SKILL.md: missing 'description' in frontmatter")
    elif len(desc) < 20:
        errors.append(f"{skill_dir.name}/SKILL.md: description is too brief (min 20 chars)")

    # Validate internal file links (e.g. [templates/...](./templates/...))
    link_pattern = re.compile(r"\[([^\]]+)\]\((\./(templates|references|examples)/[^\)]+)\)")
    for match in link_pattern.finditer(content):
        rel_target = match.group(2).lstrip("./")
        target_path = skill_dir / rel_target
        if not target_path.exists():
            errors.append(
                f"{skill_dir.name}/SKILL.md: broken link to missing file: {match.group(2)}"
            )

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate agent skills structural invariants.")
    parser.add_argument(
        "skills_dir",
        nargs="?",
        type=Path,
        default=Path(".agents/skills"),
        help="Path to .agents/skills directory (default: .agents/skills)",
    )
    args = parser.parse_args(argv)

    skills_dir = args.skills_dir.resolve()
    if not skills_dir.is_dir():
        print(f"❌ Skills directory not found: {skills_dir}", file=sys.stderr)
        return 1

    skill_subdirs = sorted(
        [d for d in skills_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
    )

    if not skill_subdirs:
        print(f"⚠️ No skill directories found in {skills_dir}")
        return 0

    total_skills = len(skill_subdirs)
    failed = False

    print(f"🔍 Validating {total_skills} agent skill(s) in {skills_dir}...")
    for s_dir in skill_subdirs:
        errs = validate_skill(s_dir)
        if errs:
            failed = True
            print(f"  ✗ {s_dir.name}:")
            for err in errs:
                print(f"      - {err}", file=sys.stderr)
        else:
            print(f"  ✓ {s_dir.name}")

    if failed:
        print("\n❌ Skill validation failed with errors.", file=sys.stderr)
        return 1

    print(f"\n✅ All {total_skills} skill(s) satisfied structural invariants!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
