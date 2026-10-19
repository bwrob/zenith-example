#!/usr/bin/env python3
"""Validate functional specification structural invariants in Spec-Driven Development.

Ensures that `.specs/<feature-id>/spec.md`:
1. Defines explicit In-Scope and Out-of-Scope boundaries.
2. Contains functional requirements written with EARS patterns.
3. Contains testable Given/When/Then acceptance scenarios.
4. Prevents premature implementation leakage (e.g. internal class/function definitions).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SpecValidationResult:
    """Result of specification validation."""

    spec_path: Path
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    requirement_count: int
    scenario_count: int


def validate_spec_content(content: str, spec_path: Path) -> SpecValidationResult:
    """Validate specification content against SDD quality invariants."""
    errors: list[str] = []
    warnings: list[str] = []

    # 1. Boundary Check: In-Scope and Out-of-Scope
    has_in_scope = bool(re.search(r"###?\s*In-Scope", content, re.IGNORECASE))
    has_out_of_scope = bool(re.search(r"###?\s*Out-of-Scope", content, re.IGNORECASE))

    if not has_in_scope:
        errors.append("Missing required 'In-Scope' section.")
    if not has_out_of_scope:
        errors.append("Missing required 'Out-of-Scope' section.")

    # 2. Functional Requirements Check
    req_ids: set[str] = set()
    for m in re.finditer(r"\bREQ-(\d+)\b", content, re.IGNORECASE):
        req_ids.add(f"REQ-{int(m.group(1)):03d}")
    if not req_ids:
        for m in re.finditer(r"###?\s*Requirement\s*(\d+)", content, re.IGNORECASE):
            req_ids.add(f"REQ-{int(m.group(1)):03d}")
    req_count = len(req_ids)

    if req_count == 0:
        errors.append("No functional requirements found (expected 'REQ-001' or 'Requirement N').")

    # Placeholder Check
    placeholder_matches = re.findall(
        r"\[(?:Describe|Short Title|User Story|Happy Path|Error or Edge|Pending|Reason for|Requirement statement|precondition|action occurs|expected observable|expected handled).*?\]",
        content,
    )
    if placeholder_matches:
        warnings.append(
            f"Specification contains {len(placeholder_matches)} unfilled template placeholder marker(s) "
            f"(e.g. '{placeholder_matches[0]}'). Replace them before development."
        )

    # EARS Pattern Check
    ears_patterns = [
        re.compile(r"\bthe system must\b", re.IGNORECASE),
        re.compile(r"\bwhen\b.+\bmust\b", re.IGNORECASE),
        re.compile(r"\bwhile\b.+\bmust\b", re.IGNORECASE),
        re.compile(r"\bif\b.+\bthen\b.+\bmust\b", re.IGNORECASE),
    ]
    has_ears = any(pattern.search(content) for pattern in ears_patterns)
    if not has_ears:
        warnings.append("No standard EARS patterns detected (e.g. 'The system must...', 'When... must...', 'If... then...').")

    # 3. Acceptance Criteria Check (Given / When / Then)
    given_matches = list(re.finditer(r"\bGiven\b", content))
    when_matches = list(re.finditer(r"\bWhen\b", content))
    then_matches = list(re.finditer(r"\bThen\b", content))

    scenario_count = min(len(given_matches), len(when_matches), len(then_matches))
    if scenario_count == 0:
        errors.append("No complete Given/When/Then acceptance scenarios found.")

    # 4. Implementation Leakage Check
    code_blocks = re.findall(r"```(?:python|py)?\n(.*?)\n```", content, re.DOTALL)
    for block in code_blocks:
        if "<!-- allow-code -->" in content:
            continue
        if re.search(r"\b(?:class\s+\w+|def\s+\w+|@dataclass)\b", block):
            if "# example" in block.lower() or "# test input" in block.lower():
                continue
            errors.append(
                "Premature implementation details detected in spec.md: code block contains class/function definitions. "
                "Move technical architecture and code skeletons to plan.md."
            )
            break

    is_valid = len(errors) == 0

    return SpecValidationResult(
        spec_path=spec_path,
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        requirement_count=req_count,
        scenario_count=scenario_count,
    )


def validate_spec_file(spec_path: Path) -> SpecValidationResult:
    """Read and validate a specification file."""
    if not spec_path.is_file():
        return SpecValidationResult(
            spec_path=spec_path,
            is_valid=False,
            errors=[f"Specification file not found: {spec_path}"],
            warnings=[],
            requirement_count=0,
            scenario_count=0,
        )

    try:
        content = spec_path.read_text(encoding="utf-8")
    except OSError as exc:
        return SpecValidationResult(
            spec_path=spec_path,
            is_valid=False,
            errors=[f"Failed to read specification file: {exc}"],
            warnings=[],
            requirement_count=0,
            scenario_count=0,
        )

    return validate_spec_content(content, spec_path)


def format_validation_report(result: SpecValidationResult) -> str:
    """Format validation result into readable report."""
    lines: list[str] = []
    lines.append("## Specification Quality Linter Report")
    lines.append("")
    lines.append(f"- **Target File**: `{result.spec_path}`")
    lines.append(f"- **Status**: {'Passed' if result.is_valid else 'Failed'}")
    lines.append(f"- **Requirements Detected**: {result.requirement_count}")
    lines.append(f"- **Acceptance Scenarios**: {result.scenario_count}")
    lines.append("")

    if result.errors:
        lines.append("### Errors (Must Fix Before Planning):")
        for err in result.errors:
            lines.append(f"- ❌ {err}")
        lines.append("")

    if result.warnings:
        lines.append("### Advisory Warnings:")
        for warn in result.warnings:
            lines.append(f"- ⚠️ {warn}")
        lines.append("")

    if result.is_valid and not result.warnings:
        lines.append("✓ Specification satisfies all SDD structural invariants and is ready for planning.")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for spec quality validation."""
    parser = argparse.ArgumentParser(
        description="Validate functional specification structural invariants in Spec-Driven Development."
    )
    parser.add_argument("spec_path", type=Path, help="Path to spec.md file or feature directory")
    args = parser.parse_args(argv)

    spec_path = args.spec_path
    if spec_path.is_dir():
        spec_path = spec_path / "spec.md"

    result = validate_spec_file(spec_path)
    print(format_validation_report(result))

    return 0 if result.is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
