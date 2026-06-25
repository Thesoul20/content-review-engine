from __future__ import annotations

import re
from dataclasses import dataclass

from content_review_engine.core.models import ReviewFinding

_SUPPRESSION_COMMENT_RE = re.compile(
    r"<!--\s*content-review-(disable-line|disable-next-line)\s+([^<>]*?)\s*-->"
)


@dataclass(frozen=True)
class SuppressionDirective:
    line: int
    rule_ids: tuple[str, ...]


def parse_inline_suppressions(markdown: str) -> list[SuppressionDirective]:
    directives: list[SuppressionDirective] = []

    for line_number, line in enumerate(markdown.splitlines(), start=1):
        for match in _SUPPRESSION_COMMENT_RE.finditer(line):
            action = match.group(1)
            rule_ids = tuple(rule_id for rule_id in match.group(2).split() if rule_id)
            if not rule_ids:
                continue

            target_line = line_number
            if action == "disable-next-line":
                target_line += 1

            directives.append(
                SuppressionDirective(
                    line=target_line,
                    rule_ids=rule_ids,
                )
            )

    return directives


def finding_is_suppressed(
    finding: ReviewFinding,
    directives: list[SuppressionDirective],
) -> bool:
    if finding.location is None:
        return False

    finding_line = finding.location.start_line
    return any(
        directive.line == finding_line and finding.rule_id in directive.rule_ids
        for directive in directives
    )


def filter_suppressed_findings(
    findings: list[ReviewFinding],
    directives: list[SuppressionDirective],
) -> list[ReviewFinding]:
    return [
        finding
        for finding in findings
        if not finding_is_suppressed(finding, directives)
    ]


__all__ = [
    "SuppressionDirective",
    "filter_suppressed_findings",
    "finding_is_suppressed",
    "parse_inline_suppressions",
]
