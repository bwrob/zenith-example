"""List item rules, such as dangling coordinating conjunctions."""

import re
from dataclasses import dataclass

from ste.model import BlockKind, Document, Finding, Severity

CONJUNCTION_END = re.compile(r"\b(?P<word>and|or)\s*$", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class DanglingConjunctionRule:
    """Rule that flags list items ending with coordinating conjunctions ('and', 'or')."""

    id: str = "dangling-conjunction"
    severity: Severity = Severity.HARD
    description: str = "Flag list items ending with 'and' or 'or'."

    def check(self, document: Document) -> list[Finding]:
        """Scan list items in document for dangling conjunctions."""
        findings: list[Finding] = []
        for block in document.blocks:
            if block.kind != BlockKind.LIST_ITEM:
                continue

            match = CONJUNCTION_END.search(block.text)
            if match is None:
                continue

            line, col = block.locate(match.start("word"))
            if document.suppressions.silences(line, self.id):
                continue

            findings.append(
                Finding(
                    file=document.filename,
                    line=line,
                    column=col,
                    rule=self.id,
                    severity=self.severity,
                    match=match.group("word"),
                    message=(
                        "List item ends with a coordinating conjunction. "
                        "Complete the item or join it with the next item."
                    ),
                )
            )

        return findings


DANGLING_CONJUNCTION_RULE = DanglingConjunctionRule()
