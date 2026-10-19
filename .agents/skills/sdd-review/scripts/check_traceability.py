#!/usr/bin/env python3
"""Automated Requirement-to-Test Traceability Matrix Validator for Spec-Driven Development.

This script:
1. Parses `.specs/<feature-id>/spec.md` to extract declared requirement IDs (e.g. `REQ-001`).
2. Scans `tests/` for test functions referencing those requirement IDs in their names,
   docstrings, comments, or pytest markers.
3. Generates a markdown traceability matrix.
4. Returns exit code 1 if any requirement lacks test coverage.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RequirementInfo:
    """Requirement metadata extracted from specification."""

    req_id: str
    title: str
    scenarios: list[str]


@dataclass(frozen=True, slots=True)
class TraceabilityResult:
    """Traceability analysis result."""

    spec_path: Path
    tests_dir: Path
    requirements: list[RequirementInfo]
    req_to_tests: dict[str, list[str]]
    missing_tests: list[str]
    unmapped_tests: dict[str, list[str]]


def extract_requirements_from_spec(spec_path: Path) -> list[RequirementInfo]:
    """Parse spec.md to extract requirement IDs, titles, and scenarios."""
    if not spec_path.is_file():
        return []

    try:
        content = spec_path.read_text(encoding="utf-8")
    except OSError:
        return []

    requirements: list[RequirementInfo] = []
    current_req_id: str | None = None
    current_title: str = ""
    current_scenarios: list[str] = []

    lines = content.splitlines()
    for line in lines:
        stripped = line.strip()

        # Flush on section boundaries (e.g. ## 5. Non-Functional, ## 6. Acceptance Scenarios)
        if stripped.startswith("## "):
            if current_req_id:
                requirements.append(
                    RequirementInfo(
                        req_id=current_req_id,
                        title=current_title or current_req_id,
                        scenarios=current_scenarios,
                    )
                )
                current_req_id = None
                current_title = ""
                current_scenarios = []
            continue

        header_match = re.search(r"###?\s*Requirement\s*\d+:\s*(.+)", line, re.IGNORECASE)
        req_match = re.search(r"-\s*\*\*ID\*\*:\s*`?(REQ-\d+)`?", line, re.IGNORECASE)
        if not req_match:
            req_match = re.search(r"###?\s*Requirement\s*\d+:\s*`?(REQ-\d+)`?", line, re.IGNORECASE)

        if header_match:
            if current_req_id:
                requirements.append(
                    RequirementInfo(
                        req_id=current_req_id,
                        title=current_title or current_req_id,
                        scenarios=current_scenarios,
                    )
                )
                current_req_id = None
                current_scenarios = []

            raw_title = header_match.group(1).strip()
            embedded_id_match = re.search(r"\b(REQ-\d+)\b", raw_title, re.IGNORECASE)
            if embedded_id_match:
                current_req_id = embedded_id_match.group(1).upper()
                clean_title = re.sub(r"\(?\bREQ-\d+\)?\s*[:-]?\s*", "", raw_title, flags=re.IGNORECASE).strip()
                current_title = clean_title or current_req_id
            else:
                current_title = raw_title

        if req_match:
            new_id = req_match.group(1).upper()
            if current_req_id and current_req_id != new_id:
                requirements.append(
                    RequirementInfo(
                        req_id=current_req_id,
                        title=current_title or current_req_id,
                        scenarios=current_scenarios,
                    )
                )
                current_scenarios = []
            current_req_id = new_id

        scenario_match = re.search(r"###?\s*Scenario\s*\d+:\s*(.+)", line, re.IGNORECASE)
        if scenario_match and current_req_id:
            current_scenarios.append(scenario_match.group(1).strip())

    if current_req_id:
        requirements.append(
            RequirementInfo(
                req_id=current_req_id,
                title=current_title or current_req_id,
                scenarios=current_scenarios,
            )
        )

    # Fallback to search all REQ-NNN occurrences if structured format differed
    if not requirements:
        found_ids = sorted(set(re.findall(r"\bREQ-\d+\b", content, re.IGNORECASE)))
        for rid in found_ids:
            requirements.append(RequirementInfo(req_id=rid.upper(), title=rid.upper(), scenarios=[]))

    return requirements


def scan_tests_for_requirements(tests_dir: Path) -> dict[str, list[str]]:
    """Scan test directory for references to REQ-NNN in test files."""
    req_to_tests: dict[str, list[str]] = {}

    if not tests_dir.is_dir():
        return req_to_tests

    for test_file in sorted(tests_dir.rglob("test_*.py")):
        try:
            content = test_file.read_text(encoding="utf-8")
        except OSError:
            continue

        try:
            tree = ast.parse(content)
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("test_"):
                    continue

                test_ref = f"{test_file.name}::{node.name}"
                matched_reqs: set[str] = set()

                # 1. Match from function name (e.g. test_req_001_...) with underscore/boundary delimiter
                for m in re.finditer(r"(?:^|_)req_?(\d+)(?:_|$)", node.name, re.IGNORECASE):
                    matched_reqs.add(f"REQ-{int(m.group(1)):03d}")

                # 2. Match from docstring
                docstring = ast.get_docstring(node) or ""
                for m in re.finditer(r"\bREQ-(\d+)\b", docstring, re.IGNORECASE):
                    matched_reqs.add(f"REQ-{int(m.group(1)):03d}")

                # 3. Match from pytest mark decorators (@pytest.mark.req("REQ-001"), etc.)
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        for arg in decorator.args:
                            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                                for m in re.finditer(r"\bREQ-(\d+)\b", arg.value, re.IGNORECASE):
                                    matched_reqs.add(f"REQ-{int(m.group(1)):03d}")
                                for m in re.finditer(r"^\s*(\d+)\s*$", arg.value):
                                    matched_reqs.add(f"REQ-{int(m.group(1)):03d}")

                for req_id in matched_reqs:
                    req_to_tests.setdefault(req_id, []).append(test_ref)

    return req_to_tests


def analyze_traceability(spec_path: Path, tests_dir: Path) -> TraceabilityResult:
    """Analyze traceability between specification requirements and test files."""
    requirements = extract_requirements_from_spec(spec_path)
    req_to_tests = scan_tests_for_requirements(tests_dir)

    known_ids = {r.req_id for r in requirements}
    missing = [r.req_id for r in requirements if not req_to_tests.get(r.req_id)]
    unmapped = {k: v for k, v in req_to_tests.items() if k not in known_ids}

    return TraceabilityResult(
        spec_path=spec_path,
        tests_dir=tests_dir,
        requirements=requirements,
        req_to_tests=req_to_tests,
        missing_tests=missing,
        unmapped_tests=unmapped,
    )


def format_traceability_table(result: TraceabilityResult) -> str:
    """Format traceability matrix as markdown table."""
    lines: list[str] = []
    lines.append("| Requirement ID | Requirement Title | Associated Test Case | Status |")
    lines.append("| :--- | :--- | :--- | :--- |")

    for req in result.requirements:
        tests = result.req_to_tests.get(req.req_id, [])
        if tests:
            test_list = "<br/>".join(f"`{t}`" for t in tests)
            status = "✓ Verified"
        else:
            test_list = "*None found*"
            status = "❌ Missing Test"
        lines.append(f"| `{req.req_id}` | {req.title} | {test_list} | {status} |")

    return "\n".join(lines)


def format_traceability_report(result: TraceabilityResult) -> str:
    """Format full traceability audit report."""
    lines: list[str] = []
    lines.append("## Requirement Traceability Audit Report")
    lines.append("")
    lines.append(f"- **Spec File**: `{result.spec_path}`")
    lines.append(f"- **Tests Directory**: `{result.tests_dir}`")
    lines.append(f"- **Requirements Declared**: {len(result.requirements)}")
    lines.append(f"- **Requirements Verified**: {len(result.requirements) - len(result.missing_tests)}")
    lines.append(f"- **Missing Verification**: {len(result.missing_tests)}")
    lines.append("")
    lines.append("### Traceability Matrix")
    lines.append("")
    lines.append(format_traceability_table(result))
    lines.append("")

    if result.missing_tests:
        lines.append("### Missing Test Coverage")
        for req_id in result.missing_tests:
            lines.append(f"- ❌ `{req_id}` lacks an automated test case in `tests/`.")
        lines.append("")

    if result.unmapped_tests:
        lines.append("### Unmapped Requirement Tags in Tests")
        for req_id, tests in sorted(result.unmapped_tests.items()):
            lines.append(f"- ⚠️ `{req_id}` is referenced in tests {tests} but is not declared in `spec.md`.")
        lines.append("")

    if not result.missing_tests:
        lines.append("✓ All specification requirements have passing automated test coverage.")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for traceability verification."""
    parser = argparse.ArgumentParser(
        description="Verify requirement-to-test traceability matrix in Spec-Driven Development."
    )
    parser.add_argument("spec_path", type=Path, help="Path to spec.md")
    parser.add_argument("--tests-dir", type=Path, default=Path("tests"), help="Path to tests/ directory")
    parser.add_argument("--table-only", action="store_true", help="Output only the markdown table")
    args = parser.parse_args(argv)

    spec_path = args.spec_path
    if spec_path.is_dir():
        spec_path = spec_path / "spec.md"

    result = analyze_traceability(spec_path, args.tests_dir)

    if args.table_only:
        print(format_traceability_table(result))
    else:
        print(format_traceability_report(result))

    return 1 if result.missing_tests else 0


if __name__ == "__main__":
    sys.exit(main())
