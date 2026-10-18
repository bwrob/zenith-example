"""Command-line interface for the modular STE linter."""

import argparse
import sys
from pathlib import Path
from typing import TextIO

from ste.engine import lint_text
from ste.fixer import fix_text
from ste.model import Finding, Severity
from ste.reporter import format_json, format_text
from ste.rules import ALL_RULES, get_rules


def build_parser() -> argparse.ArgumentParser:
    """Construct the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="ste-lint",
        description=(
            "Deterministic structural linter for ASD-STE100 Simplified Technical English.\n"
            "Checks structural rules in Markdown documents and agent output."
        ),
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Markdown file(s) to lint. If omitted, reads from standard input.",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix common mechanical violations (contractions, Latin abbreviations, unapproved phrases) in-place.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output findings in structured JSON format.",
    )
    parser.add_argument(
        "--baseline",
        type=int,
        default=0,
        help="Tolerate up to N hard violations before exiting with non-zero status (default: 0).",
    )
    parser.add_argument(
        "--disable",
        type=str,
        default="",
        help="Comma-separated list of rule IDs to disable (e.g. 'passive-voice,present-perfect').",
    )
    parser.add_argument(
        "--list-rules",
        action="store_true",
        help="List all available rules and exit.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Execute internal verification test suite and exit.",
    )
    return parser


def run_selftest() -> int:
    """Run internal test suite validating all rules against test cases."""
    # 1. Structural violations
    bad = (
        "The panel is removed; spin up the job. "
        "Perform an analysis of the seamless log. "
        "We have received the report."
    )
    result = lint_text(bad)
    rule_ids = {f.rule for f in result.findings}
    for expected in (
        "semicolon",
        "phrasal-verb",
        "nominalization",
        "marketing-adjective",
        "passive-voice",
        "present-perfect",
    ):
        assert expected in rule_ids, f"Expected rule {expected} in findings: {rule_ids}"

    # 2. Hedges / modality must NEVER be flagged
    hedges = (
        "The request may have failed. It could be a timeout. "
        "The disk might have filled."
    )
    hedge_result = lint_text(hedges)
    assert hedge_result.findings == [], f"Hedges flagged: {hedge_result.findings}"

    # 3. Fenced code blocks must be skipped
    code_block = "```python\nx = a; y = b\n```"
    assert lint_text(code_block).findings == []

    # 4. Tilde code fences skipped
    tilde_block = "~~~text\n- code and\n~~~"
    assert lint_text(tilde_block).findings == []

    # 5. List items with dangling conjunctions
    list_text = (
        "- Confirm the target and\n"
        "* Record the result OR  \n"
        "+ Close the panel\n"
        "1. Start the task and\n"
        "2) Stop the task OR"
    )
    dangling_result = lint_text(list_text)
    dangling = [f for f in dangling_result.findings if f.rule == "dangling-conjunction"]
    assert len(dangling) == 4, f"Expected 4 dangling findings, got {len(dangling)}"
    assert [f.line for f in dangling] == [1, 2, 4, 5]
    assert all(f.severity == Severity.HARD for f in dangling)

    # 6. Valid continuation lines ignored
    valid_continuation = "  - Confirm the target and\n    record the result."
    assert not any(
        f.rule == "dangling-conjunction" for f in lint_text(valid_continuation).findings
    )

    # 7. Inline code spans ignored
    inline_code = "- Use `and` as a label\n- Combine `left` and `right`"
    assert not any(
        f.rule == "dangling-conjunction" for f in lint_text(inline_code).findings
    )

    # 8. Long sentence detection across reflowed lines
    long_prose = ("word " * 30).strip() + "."
    assert any(f.rule == "long-sentence" for f in lint_text(long_prose).findings)

    # 9. Table cells linted separately
    short_cell = " ".join(f"term{i}" for i in range(1, 25)) + "."
    table_text = f"| Label | Detail |\n| --- | --- |\n| Clear | {short_cell} |"
    assert not any(f.rule == "long-sentence" for f in lint_text(table_text).findings)

    long_cell = " ".join(f"term{i}" for i in range(1, 27)) + "."
    long_table = f"| Label | Detail |\n| --- | --- |\n| Clear | {long_cell} |"
    long_table_res = lint_text(long_table)
    assert any(f.rule == "long-sentence" for f in long_table_res.findings)

    # 10. Synonym rotation
    syn_text = "Check the config file. Then verify the output. Verify twice."
    syn_findings = [
        f for f in lint_text(syn_text).findings if f.rule == "synonym-rotation"
    ]
    assert len(syn_findings) == 1, syn_findings
    assert "'verify' and 'check'" in syn_findings[0].message

    # 11. GitHub alert and Zensical admonition handling
    alert_text = "> [!NOTE]\n> Perform an analysis of the log."
    alert_res = lint_text(alert_text)
    assert any(f.rule == "nominalization" for f in alert_res.findings)

    # 12. Frontmatter handling: only description is linted
    fm_text = (
        "---\n"
        "name: my-skill\n"
        "description: Perform an analysis of state.\n"
        "---\n"
        "# Heading\n"
        "Body content."
    )
    fm_res = lint_text(fm_text)
    assert any(f.rule == "nominalization" for f in fm_res.findings)

    # 13. Inline suppressions
    suppressed = (
        "<!-- ste-lint-disable semicolon -->\n"
        "This has; a semicolon.\n"
        "<!-- ste-lint-enable semicolon -->\n"
        "This has; another semicolon."
    )
    sup_res = lint_text(suppressed)
    semi_findings = [f for f in sup_res.findings if f.rule == "semicolon"]
    assert len(semi_findings) == 1 and semi_findings[0].line == 4

    print("selftest OK: all 13 test suites passed successfully.")
    return 0


def main(argv: list[str] | None = None, stdin: TextIO = sys.stdin) -> int:
    """Main CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.selftest:
        return run_selftest()

    if args.list_rules:
        for rule in ALL_RULES:
            print(f"- {rule.id} [{rule.severity.value}]: {rule.description}")
        return 0

    disabled = [r.strip() for r in args.disable.split(",") if r.strip()]
    rules = get_rules(disabled=disabled)

    findings: list[Finding] = []
    words_total = 0

    target_files: list[Path] = []
    if args.files:
        for p in args.files:
            if p.is_dir():
                skipped_dirs = {
                    ".git",
                    ".venv",
                    ".temp",
                    ".ruff_cache",
                    ".pytest_cache",
                    ".rumdl_cache",
                    "node_modules",
                    "site",
                    "dist",
                    "__pycache__",
                }
                for root, dirs, files in p.walk(follow_symlinks=True):
                    dirs[:] = [d for d in dirs if d not in skipped_dirs]
                    if any(part in skipped_dirs for part in root.parts):
                        continue
                    for f in sorted(files):
                        if f.endswith(".md"):
                            target_files.append(root / f)
            elif p.is_file():
                target_files.append(p)
            else:
                print(f"Error reading {p}: file or directory not found", file=sys.stderr)
                return 1

        if args.fix:
            total_fixed = 0
            for file_path in target_files:
                try:
                    content = file_path.read_text(encoding="utf-8")
                except OSError as exc:
                    print(f"Error reading {file_path}: {exc}", file=sys.stderr)
                    return 1
                fixed, count = fix_text(content)
                if count > 0:
                    try:
                        file_path.write_text(fixed, encoding="utf-8")
                        total_fixed += count
                        print(f"Fixed {count} violation(s) in {file_path}")
                    except OSError as exc:
                        print(f"Error writing {file_path}: {exc}", file=sys.stderr)
                        return 1
            print(f"Total violations fixed: {total_fixed}")
            return 0

        for file_path in target_files:
            try:
                content = file_path.read_text(encoding="utf-8")
            except OSError as exc:
                print(f"Error reading {file_path}: {exc}", file=sys.stderr)
                return 1
            result = lint_text(content, filename=str(file_path), rules=rules)
            findings.extend(result.findings)
            words_total += result.words_total
    else:
        content = stdin.read()
        if args.fix:
            fixed, _ = fix_text(content)
            sys.stdout.write(fixed)
            return 0
        result = lint_text(content, filename="<stdin>", rules=rules)
        findings.extend(result.findings)
        words_total += result.words_total

    findings.sort(key=lambda f: (f.file, f.line, f.column, f.rule))
    hard_count = sum(1 for f in findings if f.severity == Severity.HARD)
    files_count = len(target_files) if target_files else 1

    if args.json:
        output = format_json(
            findings, words_total, hard_count, baseline=args.baseline, files_count=files_count
        )
    else:
        output = format_text(
            findings, words_total, hard_count, baseline=args.baseline, files_count=files_count
        )

    print(output)
    return 1 if hard_count > args.baseline else 0


if __name__ == "__main__":
    sys.exit(main())
