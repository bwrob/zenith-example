"""Sentence length rule."""

import re
from dataclasses import dataclass

from ste.model import Block, Document, Finding, Severity

SENTENCE_DELIMITER = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True, slots=True)
class LongSentenceRule:
    """Rule that checks sentence word counts against STE limits."""

    id: str = "long-sentence"
    severity: Severity = Severity.HARD
    max_words: int = 25
    description: str = "Check for sentences exceeding length limits (max 25 words)."

    def check(self, document: Document) -> list[Finding]:
        """Check all sentences in document blocks for excessive length."""
        findings: list[Finding] = []
        for block in document.blocks:
            text = block.text
            start = 0
            for match in SENTENCE_DELIMITER.finditer(text):
                end = match.start()
                raw_sent = text[start:end]
                lead = len(raw_sent) - len(raw_sent.lstrip())
                sent = raw_sent.strip()
                if sent:
                    self._check_sentence(document, block, start + lead, sent, findings)
                start = match.end()

            # Process the trailing sentence in the block
            raw_trailing = text[start:]
            lead = len(raw_trailing) - len(raw_trailing.lstrip())
            sent = raw_trailing.strip()
            if sent:
                self._check_sentence(document, block, start + lead, sent, findings)

        return findings

    def _check_sentence(
        self,
        document: Document,
        block: Block,
        offset: int,
        sentence: str,
        findings: list[Finding],
    ) -> None:
        words = sentence.split()
        count = len(words)
        if count > self.max_words:
            line, col = block.locate(offset)
            if not document.suppressions.silences(line, self.id):
                findings.append(
                    Finding(
                        file=document.filename,
                        line=line,
                        column=col,
                        rule=self.id,
                        severity=self.severity,
                        match=f"{count} words",
                        message=f"Sentence has {count} words (cap {self.max_words}). Split it.",
                    )
                )


LONG_SENTENCE_RULE = LongSentenceRule()
