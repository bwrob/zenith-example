"""Formatters for lint results (standard console output and JSON)."""

import json
from collections.abc import Sequence

from ste.model import Finding


def compute_compliance_score(
    findings: Sequence[Finding], words_total: int, hard_count: int
) -> float:
    """Compute an STE compliance quality score from 0.0 to 100.0.

    A clean document scores 100.0. Hard violations incur higher deductions,
    scaled relative to text length.
    """
    if words_total == 0:
        return 100.0
    advisory_count = len(findings) - hard_count
    # Density-based deduction: 1 hard violation per 100 words = -15 points; 1 advisory = -5 points
    effective_density = (hard_count * 15.0 + advisory_count * 5.0) * (
        100.0 / max(words_total, 50)
    )
    return max(0.0, round(100.0 - effective_density, 1))


def format_text(
    findings: Sequence[Finding],
    words_total: int,
    hard_count: int,
    baseline: int = 0,
    files_count: int = 1,
) -> str:
    """Format findings in standard compiler/linter terminal format."""
    lines: list[str] = []
    for f in findings:
        lines.append(f"{f.file}:{f.line}:{f.column} {f.rule}: {f.message} [{f.match}]")

    rate = round(len(findings) * 100 / words_total, 1) if words_total else 0.0
    score = compute_compliance_score(findings, words_total, hard_count)
    files_suffix = f" in {files_count} files" if files_count > 1 else ""
    summary = (
        f"\n{len(findings)} violations ({hard_count} hard, baseline {baseline}), "
        f"{words_total} words{files_suffix}, {rate} per 100 words, score: {score}/100\n"
        "Hedges/modality (may, might, could) are never flagged: confidence is content."
    )
    lines.append(summary)
    return "\n".join(lines)


def format_json(
    findings: Sequence[Finding],
    words_total: int,
    hard_count: int,
    baseline: int = 0,
    files_count: int = 1,
) -> str:
    """Format findings as structured JSON."""
    rate = round(len(findings) * 100 / words_total, 1) if words_total else 0.0
    score = compute_compliance_score(findings, words_total, hard_count)
    payload = {
        "violations": [f.to_dict() for f in findings],
        "count": len(findings),
        "hard_count": hard_count,
        "baseline": baseline,
        "words": words_total,
        "files": files_count,
        "per_100_words": rate,
        "score": score,
    }
    return json.dumps(payload, indent=2)

