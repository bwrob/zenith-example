"""Core linting engine orchestrating parsing and rule execution."""

from collections.abc import Sequence
from dataclasses import dataclass

from ste.markdown import parse
from ste.model import Document, Finding, Severity
from ste.rules import ALL_RULES, Rule


@dataclass(frozen=True, slots=True)
class LintResult:
    """Aggregated lint results for a document or batch of documents."""

    filename: str
    findings: list[Finding]
    words_total: int

    @property
    def hard_count(self) -> int:
        """Count of non-advisory violations that affect exit code."""
        return sum(1 for f in self.findings if f.severity == Severity.HARD)

    @property
    def advisory_count(self) -> int:
        """Count of advisory violations."""
        return sum(1 for f in self.findings if f.severity == Severity.ADVISORY)

    @property
    def violation_rate(self) -> float:
        """Violations per 100 words."""
        if not self.words_total:
            return 0.0
        return round(len(self.findings) * 100 / self.words_total, 1)


def lint_document(
    document: Document,
    rules: Sequence[Rule] | None = None,
) -> LintResult:
    """Lint an already parsed Document against the specified rules."""
    active_rules = rules if rules is not None else ALL_RULES
    findings: list[Finding] = []

    for rule in active_rules:
        findings.extend(rule.check(document))

    findings.sort(key=lambda f: (f.line, f.column, f.rule))
    words_total = sum(len(block.text.split()) for block in document.blocks)

    return LintResult(
        filename=document.filename,
        findings=findings,
        words_total=words_total,
    )


def lint_text(
    text: str,
    filename: str = "<stdin>",
    rules: Sequence[Rule] | None = None,
) -> LintResult:
    """Parse and lint Markdown text."""
    document = parse(text, filename=filename)
    return lint_document(document, rules=rules)
