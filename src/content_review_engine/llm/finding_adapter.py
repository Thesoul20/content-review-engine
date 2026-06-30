from __future__ import annotations

from dataclasses import dataclass
import re

from content_review_engine.core.models import FindingSeverity
from content_review_engine.llm.models import LLMReviewFinding, LLMReviewResult
from content_review_engine.llm.policy import (
    LLM_FINDING_ADVISORY,
    LLM_FINDING_FALLBACK_RULE_ID,
    LLM_FINDING_SOURCE,
)

LLM_CORE_FINDING_DEFAULT_RULE_ID = LLM_FINDING_FALLBACK_RULE_ID
LLM_CORE_FINDING_DEFAULT_SEVERITY: FindingSeverity = "warning"
_CANONICAL_SEVERITIES: frozenset[str] = frozenset(
    {"info", "warning", "error", "critical"}
)
_SEVERITY_ALIASES: dict[str, FindingSeverity] = {
    "critical": "critical",
    "error": "error",
    "warning": "warning",
    "info": "info",
    "high": "error",
    "medium": "warning",
    "low": "info",
    "unknown": LLM_CORE_FINDING_DEFAULT_SEVERITY,
}
_RULE_ID_SEPARATOR_PATTERN = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class LLMCoreFindingCandidate:
    source: str
    advisory: bool
    rule_id: str
    severity: FindingSeverity
    message: str
    suggestion: str | None = None
    line: int | None = None
    column: int | None = None
    matched_text: str | None = None
    context: str | None = None
    category: str | None = None
    original_llm_rule_id: str | None = None
    original_index: int | None = None


def _normalize_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())


def normalize_llm_core_finding_severity(value: object) -> FindingSeverity:
    normalized = _normalize_text(value).lower()
    if normalized in _CANONICAL_SEVERITIES:
        return normalized  # type: ignore[return-value]
    return _SEVERITY_ALIASES.get(normalized, LLM_CORE_FINDING_DEFAULT_SEVERITY)


def _slugify_rule_id_component(value: object) -> str:
    normalized = _normalize_text(value).lower()
    if normalized.startswith("llm."):
        normalized = normalized[4:]
    slug = _RULE_ID_SEPARATOR_PATTERN.sub("_", normalized).strip("_")
    return slug


def build_llm_core_rule_id(
    value: object,
    *,
    fallback_value: object | None = None,
) -> str:
    primary_slug = _slugify_rule_id_component(value)
    if primary_slug != "":
        return f"llm.{primary_slug}"

    fallback_slug = _slugify_rule_id_component(fallback_value)
    if fallback_slug != "":
        return f"llm.{fallback_slug}"

    return LLM_CORE_FINDING_DEFAULT_RULE_ID


def adapt_llm_finding_to_core_finding_candidate(
    finding: LLMReviewFinding,
    *,
    original_index: int | None = None,
) -> LLMCoreFindingCandidate:
    if not isinstance(finding, LLMReviewFinding):
        raise TypeError("finding must be an LLMReviewFinding")

    return LLMCoreFindingCandidate(
        source=LLM_FINDING_SOURCE,
        advisory=LLM_FINDING_ADVISORY,
        rule_id=build_llm_core_rule_id(
            finding.rule_id,
            fallback_value=finding.category,
        ),
        severity=normalize_llm_core_finding_severity(finding.severity),
        message=finding.message,
        suggestion=finding.suggestion,
        line=finding.line,
        column=finding.column,
        matched_text=finding.matched_text,
        context=finding.rationale,
        category=finding.category,
        original_llm_rule_id=finding.rule_id,
        original_index=original_index,
    )


def adapt_llm_review_result_to_core_finding_candidates(
    result: LLMReviewResult,
) -> list[LLMCoreFindingCandidate]:
    if not isinstance(result, LLMReviewResult):
        raise TypeError("result must be an LLMReviewResult")

    return [
        adapt_llm_finding_to_core_finding_candidate(finding, original_index=index)
        for index, finding in enumerate(result.findings)
    ]


__all__ = [
    "LLM_CORE_FINDING_DEFAULT_RULE_ID",
    "LLM_CORE_FINDING_DEFAULT_SEVERITY",
    "LLMCoreFindingCandidate",
    "adapt_llm_finding_to_core_finding_candidate",
    "adapt_llm_review_result_to_core_finding_candidates",
    "build_llm_core_rule_id",
    "normalize_llm_core_finding_severity",
]
