from __future__ import annotations

from dataclasses import dataclass


LLM_FINDING_SOURCE = "llm"
LLM_FINDING_ADVISORY = True
LLM_FINDING_QUALITY_GATE_PARTICIPATION = False
LLM_FINDING_UNKNOWN_SEVERITY = "unknown"
LLM_FINDING_FALLBACK_RULE_ID = "llm.semantic_review"
LLM_FINDING_SEVERITY_ORDER: tuple[str, ...] = (
    "critical",
    "error",
    "warning",
    "info",
    LLM_FINDING_UNKNOWN_SEVERITY,
)
_CONFIDENCE_FIELD_CANDIDATES: tuple[str, ...] = (
    "confidence",
    "confidence_score",
    "score",
)


@dataclass(frozen=True)
class LLMFindingDisplayMetadata:
    source: str
    advisory: str
    participates_in_quality_gate: str
    severity: str
    rule_id: str
    confidence: str


def _normalize_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())


def normalize_llm_finding_severity(value: object) -> str:
    normalized = _normalize_text(value).lower()
    if normalized in {"critical", "error", "warning", "info"}:
        return normalized
    return LLM_FINDING_UNKNOWN_SEVERITY


def normalize_llm_finding_rule_id(value: object) -> str:
    normalized = _normalize_text(value)
    if normalized == "":
        return LLM_FINDING_FALLBACK_RULE_ID
    return normalized


def format_llm_confidence_like_value(finding: object) -> str:
    for field_name in _CONFIDENCE_FIELD_CANDIDATES:
        if not hasattr(finding, field_name):
            continue
        value = getattr(finding, field_name)
        if value is None:
            return "not provided"
        return str(value)
    return "not provided"


def build_llm_finding_display_metadata(finding: object) -> LLMFindingDisplayMetadata:
    return LLMFindingDisplayMetadata(
        source=LLM_FINDING_SOURCE,
        advisory="yes",
        participates_in_quality_gate="no",
        severity=normalize_llm_finding_severity(getattr(finding, "severity", None)),
        rule_id=normalize_llm_finding_rule_id(getattr(finding, "rule_id", None)),
        confidence=format_llm_confidence_like_value(finding),
    )


def render_llm_finding_policy_note() -> str:
    return (
        "LLM findings are advisory semantic review suggestions from the LLM layer. "
        "They do not participate in deterministic finding counts, fail-on, or quality gate."
    )


__all__ = [
    "LLM_FINDING_ADVISORY",
    "LLM_FINDING_FALLBACK_RULE_ID",
    "LLM_FINDING_QUALITY_GATE_PARTICIPATION",
    "LLM_FINDING_SEVERITY_ORDER",
    "LLM_FINDING_SOURCE",
    "LLM_FINDING_UNKNOWN_SEVERITY",
    "LLMFindingDisplayMetadata",
    "build_llm_finding_display_metadata",
    "format_llm_confidence_like_value",
    "normalize_llm_finding_rule_id",
    "normalize_llm_finding_severity",
    "render_llm_finding_policy_note",
]
