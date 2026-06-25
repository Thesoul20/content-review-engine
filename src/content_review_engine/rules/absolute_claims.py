from __future__ import annotations

from content_review_engine.core.location import build_source_span
from content_review_engine.core.models import ReviewFinding, ReviewProfile

ABSOLUTE_CLAIMS_RULE_ID = "absolute_claims"
RULE_ID = ABSOLUTE_CLAIMS_RULE_ID
DEFAULT_SUGGESTION = (
    "建议改为更审慎的表述，例如“较强”“表现较好”“在特定条件下有效”，"
    "或补充支撑该结论的证据。"
)


class AbsoluteClaimsRule:
    rule_id = ABSOLUTE_CLAIMS_RULE_ID

    def evaluate(
        self,
        text: str,
        profile: ReviewProfile,
    ) -> list[ReviewFinding]:
        terms: list[str] = []
        seen_terms: set[str] = set()

        for term in profile.absolute_claims_terms:
            normalized_term = term.strip()
            if not normalized_term or normalized_term in seen_terms:
                continue
            seen_terms.add(normalized_term)
            terms.append(normalized_term)

        if not terms:
            return []

        allow_terms = {
            term.strip()
            for term in profile.absolute_claims_allow_terms
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
                    severity=profile.absolute_claims_severity,
                    message=f"发现可能存在绝对化表述：{term}",
                    suggestion=DEFAULT_SUGGESTION,
                    matched_term=term,
                    matched_text=location.matched_text,
                    location=location,
                )
            )

        return findings


DEFAULT_ABSOLUTE_CLAIMS_RULE = AbsoluteClaimsRule()


def check_absolute_claims(
    markdown_text: str,
    profile: ReviewProfile,
) -> list[ReviewFinding]:
    return DEFAULT_ABSOLUTE_CLAIMS_RULE.evaluate(markdown_text, profile)


__all__ = [
    "ABSOLUTE_CLAIMS_RULE_ID",
    "DEFAULT_ABSOLUTE_CLAIMS_RULE",
    "DEFAULT_SUGGESTION",
    "AbsoluteClaimsRule",
    "RULE_ID",
    "check_absolute_claims",
]
