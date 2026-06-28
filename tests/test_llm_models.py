import pytest
from pydantic import ValidationError

from content_review_engine.llm import (
    LLMSidecarResult,
    LLMSidecarSummary,
    LLMReviewFinding,
    LLMReviewResult,
    LLMReviewSummary,
    llm_review_result_to_dict,
)


def test_create_llm_review_finding() -> None:
    finding = LLMReviewFinding(
        rule_id="llm_semantic_risk",
        severity="warning",
        message="This paragraph overstates certainty without support.",
        suggestion="Qualify the claim and cite supporting evidence.",
        rationale="The wording implies a guarantee without source support.",
        confidence=0.8,
        line=4,
        column=3,
        end_line=4,
        end_column=18,
        matched_text="This always works",
        category="claims",
    )

    assert finding.rule_id == "llm_semantic_risk"
    assert finding.severity == "warning"
    assert finding.confidence == 0.8
    assert finding.line == 4


def test_llm_review_finding_rejects_empty_rule_id() -> None:
    with pytest.raises(ValidationError):
        LLMReviewFinding(
            rule_id=" ",
            severity="warning",
            message="Possible semantic risk.",
        )


def test_llm_review_finding_rejects_empty_message() -> None:
    with pytest.raises(ValidationError):
        LLMReviewFinding(
            rule_id="llm_semantic_risk",
            severity="warning",
            message=" ",
        )


def test_llm_review_finding_rejects_invalid_severity() -> None:
    with pytest.raises(ValidationError):
        LLMReviewFinding(
            rule_id="llm_semantic_risk",
            severity="medium",
            message="Possible semantic risk.",
        )


def test_llm_review_finding_rejects_confidence_below_zero() -> None:
    with pytest.raises(ValidationError):
        LLMReviewFinding(
            rule_id="llm_semantic_risk",
            severity="warning",
            message="Possible semantic risk.",
            confidence=-0.1,
        )


def test_llm_review_finding_rejects_confidence_above_one() -> None:
    with pytest.raises(ValidationError):
        LLMReviewFinding(
            rule_id="llm_semantic_risk",
            severity="warning",
            message="Possible semantic risk.",
            confidence=1.1,
        )


def test_create_llm_review_summary() -> None:
    summary = LLMReviewSummary(
        overall_risk="medium",
        summary="The article contains several unsupported claims.",
        recommended_action="Add evidence and reduce absolute wording.",
        confidence=0.7,
    )

    assert summary.overall_risk == "medium"
    assert summary.confidence == 0.7


def test_llm_review_summary_rejects_invalid_overall_risk() -> None:
    with pytest.raises(ValidationError):
        LLMReviewSummary(overall_risk="warning")


def test_llm_review_result_defaults_are_stable() -> None:
    result = LLMReviewResult()

    assert result.schema_version == "llm-review-result.v1"
    assert result.findings == ()


def test_llm_review_result_serialization_uses_canonical_shape() -> None:
    result = LLMReviewResult(
        provider="openai-compatible",
        model="future-model",
        prompt_version="draft-1",
        profile_name="semantic-risk",
        findings=(
            LLMReviewFinding(
                rule_id="llm_semantic_risk",
                severity="error",
                message="This claim needs stronger support.",
                confidence=0.9,
            ),
        ),
        summary=LLMReviewSummary(
            overall_risk="high",
            summary="Multiple unsupported claims were detected.",
            confidence=0.9,
        ),
        metadata={"run_mode": "offline-model-shape-only"},
    )

    payload = llm_review_result_to_dict(result)

    assert payload == {
        "schema_version": "llm-review-result.v1",
        "provider": "openai-compatible",
        "model": "future-model",
        "prompt_version": "draft-1",
        "profile_name": "semantic-risk",
        "findings": [
            {
                "rule_id": "llm_semantic_risk",
                "severity": "error",
                "message": "This claim needs stronger support.",
                "confidence": 0.9,
            }
        ],
        "summary": {
            "overall_risk": "high",
            "summary": "Multiple unsupported claims were detected.",
            "confidence": 0.9,
        },
        "metadata": {"run_mode": "offline-model-shape-only"},
    }


def test_llm_sidecar_result_defaults_include_provider_metadata() -> None:
    result = LLMSidecarResult(
        summary=LLMSidecarSummary(
            file_count=0,
            succeeded_count=0,
            failed_count=0,
            skipped_count=0,
            finding_count=0,
        )
    )

    assert result.schema_version == "llm-sidecar-result.v2"
    assert result.llm_provider == "mock"
    assert result.llm_provider_source == "default"
