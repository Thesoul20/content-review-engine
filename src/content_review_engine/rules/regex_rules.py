from __future__ import annotations

import re

from content_review_engine.core.location import build_source_span
from content_review_engine.core.models import RegexRuleConfig, ReviewFinding, ReviewProfile


def _compile_pattern(regex_rule: RegexRuleConfig) -> re.Pattern[str]:
    flags = 0 if regex_rule.case_sensitive else re.IGNORECASE
    return re.compile(regex_rule.pattern, flags)


def run_regex_rules(
    text: str,
    profile: ReviewProfile,
) -> list[ReviewFinding]:
    if not profile.regex_rules:
        return []

    findings: list[ReviewFinding] = []
    compiled_rules = [
        (regex_rule, _compile_pattern(regex_rule))
        for regex_rule in profile.regex_rules
    ]

    lines = text.splitlines(keepends=True)
    offset = 0

    for raw_line in lines:
        line = raw_line.rstrip("\r\n")

        for regex_rule, pattern in compiled_rules:
            for match in pattern.finditer(line):
                start_offset = offset + match.start()
                end_offset = offset + match.end()
                location = build_source_span(text, start_offset, end_offset)
                findings.append(
                    ReviewFinding(
                        rule_id=regex_rule.id,
                        severity=regex_rule.severity,
                        message=regex_rule.message,
                        matched_term=regex_rule.pattern,
                        suggestion=regex_rule.suggestion,
                        matched_text=location.matched_text,
                        location=location,
                    )
                )

        offset += len(raw_line)

    return findings


__all__ = ["run_regex_rules"]
