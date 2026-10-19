#!/usr/bin/env python3
"""Check public API diffs using Griffe and verify against the implementation plan.

This script:
1. Runs `griffe check` to detect breaking changes against a base git reference.
2. Extracts public symbols from the package and compares them against declared
   interfaces in `.specs/<feature-id>/plan.md`.
3. Reports planned additions, unplanned public symbols (scope creep), and breaking changes.
4. Generates a developer confirmation checklist for the review artifact.
"""

from __future__ import annotations

import argparse
import ast
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ApiDiffResult:
    """Structured result of public API analysis."""

    package_name: str
    base_ref: str
    griffe_available: bool
    breaking_changes: list[str]
    current_public_symbols: list[str]
    base_public_symbols: list[str]
    added_symbols: list[str]
    removed_symbols: list[str]
    planned_symbols: list[str]
    unplanned_symbols: list[str]
    missing_planned_symbols: list[str]


def detect_package_name(cwd: Path) -> str | None:
    """Detect Python package name from src/ directory or pyproject.toml."""
    src_dir = cwd / "src"
    if src_dir.is_dir():
        for child in sorted(src_dir.iterdir()):
            if child.is_dir() and (child / "__init__.py").exists():
                return child.name

    pyproject = cwd / "pyproject.toml"
    if pyproject.is_file():
        content = pyproject.read_text(encoding="utf-8")
        match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1).replace("-", "_")

    return None


def get_default_base_ref() -> str:
    """Determine the default git reference to compare against."""
    for ref in ("origin/main", "main", "origin/master", "master", "HEAD~1"):
        res = subprocess.run(
            ["git", "rev-parse", "--verify", ref],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            return ref
    return "HEAD"


def run_griffe_check(package_name: str, base_ref: str, search_dir: str = "src") -> tuple[bool, list[str]]:
    """Execute griffe check via subprocess and collect breaking change notices."""
    griffe_cmd = shutil.which("griffe") or "griffe"
    cmd = ["uv", "run", "griffe", "check", package_name, "--search", search_dir, "--against", base_ref]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return False, ["uv executable not found"]

    if proc.returncode == 127 or "No such file or directory" in proc.stderr:
        # Griffe is not installed or available
        return False, []

    output = (proc.stdout + "\n" + proc.stderr).strip()
    breaking: list[str] = []
    if proc.returncode != 0 and output:
        for line in output.splitlines():
            line_str = line.strip()
            if line_str and not line_str.startswith("INFO"):
                breaking.append(line_str)

    return True, breaking


def extract_public_symbols_from_ast(code: str) -> list[str]:
    """Extract public classes, functions, and __all__ exports using standard AST."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    symbols: list[str] = []
    has_explicit_all = False

    # Check for __all__
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                symbols.append(elt.value)
                        has_explicit_all = True

    if has_explicit_all:
        return sorted(set(symbols))

    # Fallback to top-level non-underscored classes, functions, and PEP 695 type aliases
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                symbols.append(node.name)
        elif hasattr(ast, "TypeAlias") and isinstance(node, ast.TypeAlias):
            if isinstance(node.name, ast.Name) and not node.name.id.startswith("_"):
                symbols.append(node.name.id)

    return sorted(set(symbols))


def get_package_public_symbols(package_dir: Path) -> list[str]:
    """Scan package directory for public symbols across __init__.py and modules."""
    symbols: list[str] = []
    init_file = package_dir / "__init__.py"
    if init_file.is_file():
        init_symbols = extract_public_symbols_from_ast(init_file.read_text(encoding="utf-8"))
        if init_symbols:
            return sorted(set(init_symbols))

    # Scan python files in package recursively, skipping private modules and __pycache__
    for py_file in sorted(package_dir.rglob("*.py")):
        if py_file.name.startswith("_") or any(p.startswith("_") for p in py_file.parts):
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
            symbols.extend(extract_public_symbols_from_ast(content))
        except OSError:
            continue

    return sorted(set(symbols))


def get_git_file_content(ref: str, rel_path: str) -> str | None:
    """Fetch content of a file at a specific git ref."""
    proc = subprocess.run(
        ["git", "show", f"{ref}:{rel_path}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        return proc.stdout
    return None


def get_base_public_symbols(base_ref: str, package_name: str, search_dir: str = "src") -> list[str]:
    """Extract public symbols from the base git reference."""
    init_path = f"{search_dir}/{package_name}/__init__.py"
    content = get_git_file_content(base_ref, init_path)
    if content:
        symbols = extract_public_symbols_from_ast(content)
        if symbols:
            return symbols

    # List files in git tree for package
    proc = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", base_ref, f"{search_dir}/{package_name}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return []

    symbols: list[str] = []
    for filepath in proc.stdout.splitlines():
        if filepath.endswith(".py") and not Path(filepath).name.startswith("_"):
            mod_content = get_git_file_content(base_ref, filepath)
            if mod_content:
                symbols.extend(extract_public_symbols_from_ast(mod_content))

    return sorted(set(symbols))


def extract_planned_symbols(plan_path: Path) -> list[str]:
    """Parse .specs/<feature-id>/plan.md to extract declared classes, functions, and type aliases."""
    if not plan_path.is_file():
        return []

    try:
        content = plan_path.read_text(encoding="utf-8")
    except OSError:
        return []

    planned: set[str] = set()

    # Prefer parsing inside python code blocks to avoid false positives in prose
    code_blocks = re.findall(r"```(?:python|py)?\n(.*?)\n```", content, re.DOTALL)
    search_texts = code_blocks if code_blocks else [content]

    class_pattern = re.compile(r"\bclass\s+([A-Za-z0-9_]+)")
    # Match only unindented top-level defs to prevent capturing methods of classes/protocols
    func_pattern = re.compile(r"^def\s+([A-Za-z0-9_]+)", re.MULTILINE)
    type_pattern = re.compile(r"^type\s+([A-Za-z0-9_]+)\s*=", re.MULTILINE)

    for text in search_texts:
        for match in class_pattern.finditer(text):
            name = match.group(1)
            if not name.startswith("_"):
                planned.add(name)

        for match in func_pattern.finditer(text):
            name = match.group(1)
            if not name.startswith("_"):
                planned.add(name)

        for match in type_pattern.finditer(text):
            name = match.group(1)
            if not name.startswith("_"):
                planned.add(name)

    return sorted(planned)


def analyze_public_api(
    cwd: Path,
    package_name: str,
    base_ref: str,
    plan_path: Path | None = None,
    search_dir: str = "src",
) -> ApiDiffResult:
    """Analyze public API changes against git base ref and implementation plan."""
    package_dir = cwd / search_dir / package_name
    current_symbols = get_package_public_symbols(package_dir) if package_dir.is_dir() else []
    base_symbols = get_base_public_symbols(base_ref, package_name, search_dir)

    added = [s for s in current_symbols if s not in base_symbols]
    removed = [s for s in base_symbols if s not in current_symbols]

    griffe_ok, breaking = run_griffe_check(package_name, base_ref, search_dir)

    planned: list[str] = []
    unplanned: list[str] = []
    missing_planned: list[str] = []

    if plan_path and plan_path.is_file():
        planned = extract_planned_symbols(plan_path)
        unplanned = [s for s in added if s not in planned]
        missing_planned = [s for s in planned if s not in current_symbols]

    return ApiDiffResult(
        package_name=package_name,
        base_ref=base_ref,
        griffe_available=griffe_ok,
        breaking_changes=breaking,
        current_public_symbols=current_symbols,
        base_public_symbols=base_symbols,
        added_symbols=added,
        removed_symbols=removed,
        planned_symbols=planned,
        unplanned_symbols=unplanned,
        missing_planned_symbols=missing_planned,
    )


def format_report(result: ApiDiffResult) -> str:
    """Format analysis result into a human- and agent-readable markdown report."""
    lines: list[str] = []
    lines.append("## Public API & Griffe Conformance Report")
    lines.append("")
    lines.append(f"- **Package**: `{result.package_name}`")
    lines.append(f"- **Compared Against**: `{result.base_ref}`")
    lines.append(f"- **Griffe Check Available**: {'Yes' if result.griffe_available else 'No (fallback to AST)'}")
    lines.append("")

    lines.append("### 1. Breaking Change Detection")
    if result.breaking_changes:
        lines.append("⚠️ **Breaking changes detected by Griffe:**")
        for change in result.breaking_changes:
            lines.append(f"- {change}")
    else:
        lines.append("✓ No breaking changes detected in public API signatures.")
    lines.append("")

    lines.append("### 2. Public API Symbol Modifications")
    if result.added_symbols:
        lines.append(f"**Added Public Symbols ({len(result.added_symbols)}):**")
        for sym in result.added_symbols:
            lines.append(f"- `{sym}`")
    else:
        lines.append("No new public symbols added.")

    if result.removed_symbols:
        lines.append("")
        lines.append(f"**Removed Public Symbols ({len(result.removed_symbols)}):**")
        for sym in result.removed_symbols:
            lines.append(f"- `{sym}`")
    lines.append("")

    if result.planned_symbols:
        lines.append("### 3. Implementation Plan Conformance")
        if result.unplanned_symbols:
            lines.append("⚠️ **Unplanned Public Symbols (Scope Creep Warning):**")
            lines.append("These symbols appear in the public API but were not declared in the plan:")
            for sym in result.unplanned_symbols:
                lines.append(f"- `{sym}`")
        else:
            lines.append("✓ All added public symbols were declared in the plan.")

        if result.missing_planned_symbols:
            lines.append("")
            lines.append("⚠️ **Missing Planned Symbols:**")
            lines.append("These symbols were specified in the plan but not found in the public API:")
            for sym in result.missing_planned_symbols:
                lines.append(f"- `{sym}`")
        lines.append("")

    lines.append("### 4. Developer Confirmation Checklist")
    lines.append("- [ ] Maintainer confirms the public API diff matches intended feature scope.")
    lines.append("- [ ] Any unplanned public symbols are either intentional or made private.")
    lines.append("- [ ] Breaking changes (if any) are documented and justified.")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for API diff and plan verification."""
    parser = argparse.ArgumentParser(
        description="Verify public API changes with Griffe against git base ref and implementation plan."
    )
    parser.add_argument("--package", type=str, help="Package name (default: auto-detected)")
    parser.add_argument("--against", type=str, help="Base git reference (default: auto-detected main/origin/main)")
    parser.add_argument("--plan", type=Path, help="Path to .specs/<feature-id>/plan.md")
    parser.add_argument("--search", type=str, default="src", help="Search directory (default: src)")
    parser.add_argument("--output", type=Path, help="Write markdown report to file")
    args = parser.parse_args(argv)

    cwd = Path.cwd()
    package_name = args.package or detect_package_name(cwd)
    if not package_name:
        print("❌ Could not detect package name. Pass --package <name>", file=sys.stderr)
        return 1

    base_ref = args.against or get_default_base_ref()

    result = analyze_public_api(
        cwd=cwd,
        package_name=package_name,
        base_ref=base_ref,
        plan_path=args.plan,
        search_dir=args.search,
    )

    report = format_report(result)
    print(report)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report + "\n", encoding="utf-8")
        print(f"\nSaved report to {args.output}")

    if result.breaking_changes or result.unplanned_symbols:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
