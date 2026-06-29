from __future__ import annotations

from dataclasses import dataclass

from content_review_engine.llm import (
    LLMFindingDisplayMetadata,
    build_llm_finding_display_metadata,
    format_llm_confidence_like_value,
    normalize_llm_finding_rule_id,
    normalize_llm_finding_severity,
    render_llm_finding_policy_note,
)
from content_review_engine.llm.models import LLMReviewFinding


@dataclass
class _ScoreOnlyFinding:
    severity: object
    rule_id: object
    score: float | None = None


def test_policy_sets_stable_source_advisory_and_quality_gate_metadata() -> None:
    metadata = build_llm_finding_display_metadata(
        LLMReviewFinding(
            rule_id="llm.semantic.overclaim",
            severity="warning",
            message="Possible overclaim.",
        )
    )

    assert metadata == LLMFindingDisplayMetadata(
        source="llm",
        advisory="yes",
        participates_in_quality_gate="no",
        severity="warning",
        rule_id="llm.semantic.overclaim",
        confidence="not provided",
    )


def test_policy_normalizes_severity_values() -> None:
    assert normalize_llm_finding_severity("Warning") == "warning"
    assert normalize_llm_finding_severity(" critical ") == "critical"
    assert normalize_llm_finding_severity("") == "unknown"
    assert normalize_llm_finding_severity(None) == "unknown"
    assert normalize_llm_finding_severity("severe") == "unknown"


def test_policy_normalizes_rule_id_values() -> None:
    assert normalize_llm_finding_rule_id("llm.semantic.overclaim") == "llm.semantic.overclaim"
    assert normalize_llm_finding_rule_id("llm.semantic.custom\nrule") == "llm.semantic.custom rule"
    assert normalize_llm_finding_rule_id("   ") == "llm.semantic_review"
    assert normalize_llm_finding_rule_id(None) == "llm.semantic_review"


def test_policy_formats_missing_confidence_as_not_provided() -> None:
    finding = LLMReviewFinding(
        rule_id="llm.semantic.overclaim",
        severity="warning",
        message="Possible overclaim.",
    )

    assert format_llm_confidence_like_value(finding) == "not provided"


def test_policy_uses_confidence_like_fields_when_available() -> None:
    finding = _ScoreOnlyFinding(
        severity="warning",
        rule_id="llm.semantic.score_based",
        score=0.77,
    )

    metadata = build_llm_finding_display_metadata(finding)

    assert metadata.confidence == "0.77"


def test_policy_helper_does_not_modify_input_object() -> None:
    finding = _ScoreOnlyFinding(
        severity=" Warning ",
        rule_id="llm.semantic.custom\nrule",
        score=0.77,
    )

    original_state = (finding.severity, finding.rule_id, finding.score)

    metadata = build_llm_finding_display_metadata(finding)

    assert metadata.severity == "warning"
    assert metadata.rule_id == "llm.semantic.custom rule"
    assert (finding.severity, finding.rule_id, finding.score) == original_state


def test_policy_note_mentions_advisory_boundary() -> None:
    note = render_llm_finding_policy_note()

    assert "advisory semantic review suggestions" in note
    assert "do not participate in deterministic finding counts, fail-on, or quality gate" in note
