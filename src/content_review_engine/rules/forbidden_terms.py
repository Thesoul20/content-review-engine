from __future__ import annotations

from content_review_engine.core.location import build_source_span
from content_review_engine.core.models import ReviewFinding, ReviewProfile

FORBIDDEN_TERMS_RULE_ID = "forbidden_terms"
RULE_ID = FORBIDDEN_TERMS_RULE_ID


class ForbiddenTermsRule:
    rule_id = FORBIDDEN_TERMS_RULE_ID

    def evaluate(
        self,
        text: str,
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

        allow_terms = {
            term.strip()
            for term in profile.forbidden_terms_allow_terms
            if term.strip()
        }
        terms = [term for term in terms if term not in allow_terms]
        if not terms:
            return []

        findings: list[ReviewFinding] = []
        for term in terms:
            start_offset = text.find(term)
            if start_offset == -1:
                continue

            end_offset = start_offset + len(term)
            location = build_source_span(text, start_offset, end_offset)
            findings.append(
                ReviewFinding(
                    rule_id=self.rule_id,
                    severity="warning",
                    message=f"发现风险词：{term}",
                    matched_term=term,
                    matched_text=location.matched_text,
                    location=location,
                )
            )

        return findings


DEFAULT_FORBIDDEN_TERMS_RULE = ForbiddenTermsRule()


def check_forbidden_terms(
    markdown_text: str,
    profile: ReviewProfile,
) -> list[ReviewFinding]:
    return DEFAULT_FORBIDDEN_TERMS_RULE.evaluate(markdown_text, profile)


__all__ = [
    "DEFAULT_FORBIDDEN_TERMS_RULE",
    "FORBIDDEN_TERMS_RULE_ID",
    "ForbiddenTermsRule",
    "RULE_ID",
    "check_forbidden_terms",
]
