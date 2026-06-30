from __future__ import annotations

from content_review_engine.core.models import ReviewFinding, ReviewResult
from content_review_engine.core.quality_gate import quality_gate_failed
from content_review_engine.llm import (
    LLMCoreFindingCandidate,
    LLMReviewFinding,
    LLMReviewResult,
    adapt_llm_finding_to_core_finding_candidate,
    adapt_llm_review_result_to_core_finding_candidates,
    build_llm_core_rule_id,
    llm_review_result_to_dict,
    normalize_llm_core_finding_severity,
)


def test_adapter_converts_single_finding_to_core_candidate() -> None:
    finding = LLMReviewFinding(
        rule_id="Unsafe Medical Claim",
        severity="warning",
        message="This wording may imply treatment efficacy without support.",
        suggestion="Qualify the claim and cite evidence.",
        rationale="The wording sounds therapeutic but no source is provided.",
        line=8,
        column=5,
        matched_text="guarantees recovery",
        category="medical-risk",
    )

    candidate = adapt_llm_finding_to_core_finding_candidate(
        finding,
        original_index=3,
    )

    assert candidate == LLMCoreFindingCandidate(
        source="llm",
        advisory=True,
        rule_id="llm.unsafe_medical_claim",
        severity="warning",
        message="This wording may imply treatment efficacy without support.",
        suggestion="Qualify the claim and cite evidence.",
        line=8,
        column=5,
        matched_text="guarantees recovery",
        context="The wording sounds therapeutic but no source is provided.",
        category="medical-risk",
        original_llm_rule_id="Unsafe Medical Claim",
        original_index=3,
    )


def test_adapter_converts_multiple_findings_in_original_order() -> None:
    result = LLMReviewResult(
        findings=(
            LLMReviewFinding(
                rule_id="misleading-claim",
                severity="error",
                message="The claim reads as stronger than the cited evidence.",
            ),
            LLMReviewFinding(
                rule_id="llm.marketing_tone",
                severity="info",
                message="The tone feels too promotional.",
                suggestion="Use more neutral wording.",
            ),
        )
    )

    candidates = adapt_llm_review_result_to_core_finding_candidates(result)

    assert [candidate.rule_id for candidate in candidates] == [
        "llm.misleading_claim",
        "llm.marketing_tone",
    ]
    assert [candidate.severity for candidate in candidates] == ["error", "info"]
    assert [candidate.original_index for candidate in candidates] == [0, 1]
    assert all(candidate.source == "llm" for candidate in candidates)
    assert all(candidate.advisory is True for candidate in candidates)


def test_adapter_returns_empty_list_for_empty_result() -> None:
    assert adapt_llm_review_result_to_core_finding_candidates(LLMReviewResult()) == []


def test_core_severity_normalization_covers_known_aliases_and_fallbacks() -> None:
    assert normalize_llm_core_finding_severity("critical") == "critical"
    assert normalize_llm_core_finding_severity("error") == "error"
    assert normalize_llm_core_finding_severity("warning") == "warning"
    assert normalize_llm_core_finding_severity("info") == "info"
    assert normalize_llm_core_finding_severity("High") == "error"
    assert normalize_llm_core_finding_severity("high") == "error"
    assert normalize_llm_core_finding_severity("Medium") == "warning"
    assert normalize_llm_core_finding_severity("medium") == "warning"
    assert normalize_llm_core_finding_severity("Low") == "info"
    assert normalize_llm_core_finding_severity("low") == "info"
    assert normalize_llm_core_finding_severity("unknown") == "warning"
    assert normalize_llm_core_finding_severity(None) == "warning"
    assert normalize_llm_core_finding_severity("") == "warning"


def test_core_rule_id_normalization_builds_stable_llm_prefix() -> None:
    assert build_llm_core_rule_id("Unsafe Medical Claim") == "llm.unsafe_medical_claim"
    assert build_llm_core_rule_id("misleading-claim") == "llm.misleading_claim"
    assert build_llm_core_rule_id("llm.marketing_tone") == "llm.marketing_tone"
    assert build_llm_core_rule_id(None) == "llm.semantic_review"
    assert build_llm_core_rule_id("") == "llm.semantic_review"


def test_adapter_preserves_result_and_sidecar_serialization_inputs() -> None:
    result = LLMReviewResult(
        findings=(
            LLMReviewFinding(
                rule_id="Unsafe Medical Claim",
                severity="warning",
                message="Possible unsupported treatment claim.",
                suggestion="Add evidence.",
                rationale="The article implies a medical guarantee.",
                line=2,
                column=4,
                matched_text="cures diabetes",
                category="medical-risk",
            ),
        )
    )
    before_dump = result.model_dump()

    candidates = adapt_llm_review_result_to_core_finding_candidates(result)
    after_dump = result.model_dump()
    serialized = llm_review_result_to_dict(result)

    assert len(candidates) == 1
    assert before_dump == after_dump
    assert serialized["findings"][0]["rule_id"] == "Unsafe Medical Claim"
    assert serialized["findings"][0]["severity"] == "warning"


def test_adapter_is_outside_deterministic_quality_gate_behavior() -> None:
    deterministic_result = ReviewResult.from_findings(
        [
            ReviewFinding(
                rule_id="forbidden_terms",
                severity="warning",
                message="Contains forbidden term.",
                matched_term="best",
            )
        ]
    )
    llm_result = LLMReviewResult(
        findings=(
            LLMReviewFinding(
                rule_id="Unsafe Medical Claim",
                severity="critical",
                message="Needs human review.",
            ),
        )
    )

    candidates = adapt_llm_review_result_to_core_finding_candidates(llm_result)

    assert len(candidates) == 1
    assert quality_gate_failed(deterministic_result.summary.severity_counts, "error") is False
    assert quality_gate_failed(deterministic_result.summary.severity_counts, "warning") is True
