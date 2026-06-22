from __future__ import annotations

from content_review_engine.core.models import ReviewFinding, ReviewProfile

RULE_ID = "forbidden_terms"


def check_forbidden_terms(
    markdown_text: str,
    profile: ReviewProfile,
) -> list[ReviewFinding]:
    terms: list[str] = []
    seen_terms: set[str] = set()

    for term in profile.forbidden_terms:
        normalized_term = term.strip()
        if not normalized_term or normalized_term in seen_terms:
            continue
        seen_terms.add(normalized_term)
        terms.append(normalized_term)

    if not terms:
        return []

    findings: list[ReviewFinding] = []
    for term in terms:
        if term in markdown_text:
            findings.append(
                ReviewFinding(
                    rule_id=RULE_ID,
                    severity="warning",
                    message=f"发现风险词：{term}",
                    matched_term=term,
                    matched_text=term,
                )
            )

    return findings
