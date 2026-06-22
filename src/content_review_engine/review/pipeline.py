from __future__ import annotations

from content_review_engine.core.models import ReviewFinding, ReviewProfile
from content_review_engine.rules import check_forbidden_terms


def review_document(
    markdown_text: str,
    profile: ReviewProfile,
) -> list[ReviewFinding]:
    findings: list[ReviewFinding] = []
    findings.extend(check_forbidden_terms(markdown_text, profile))
    return findings
