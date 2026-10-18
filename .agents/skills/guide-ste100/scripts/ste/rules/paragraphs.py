"""Paragraph length rule enforcing one topic and maximum 6 sentences per paragraph."""

from dataclasses import dataclass

from ste.model import BlockKind, Document, Finding, Severity


@dataclass(frozen=True, slots=True)
class ParagraphLengthRule:
    """Rule that flags paragraphs with more than 6 sentences (Rule 6.6)."""

    id: str = "paragraph-length"
    severity: Severity = Severity.HARD
    description: str = "Enforce maximum 6 sentences per paragraph (Rule 6.6)."
    max_sentences: int = 6

    def check(self, document: Document) -> list[Finding]:
        """Check all paragraph blocks for sentence count violations."""
        findings: list[Finding] = []
        for block in document.blocks:
            if block.kind != BlockKind.PARAGRAPH:
                continue

            # Identify sentences by terminal punctuation (.!?:)
            raw_sents = [s.strip() for s in block.text.replace("?", ".").replace("!", ".").split(".") if len(s.strip().split()) >= 2]
            if len(raw_sents) > self.max_sentences:
                line, col = block.locate(0)
                if document.suppressions.silences(line, self.id):
                    continue
                findings.append(
                    Finding(
                        file=document.filename,
                        line=line,
                        column=col,
                        rule=self.id,
                        severity=self.severity,
                        match=f"{len(raw_sents)} sentences",
                        message=(
                            f"Paragraph has {len(raw_sents)} sentences (cap {self.max_sentences}, Rule 6.6). "
                            "Split into multiple single-topic paragraphs."
                        ),
                    )
                )
        return findings


PARAGRAPH_LENGTH_RULE = ParagraphLengthRule()
