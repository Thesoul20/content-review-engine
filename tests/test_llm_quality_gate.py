from __future__ import annotations

from content_review_engine.llm import (
    LLMSidecarFile,
    LLMSidecarResult,
    LLMSidecarSummary,
    LLMReviewFinding,
    LLMReviewResult,
    evaluate_batch_llm_quality_gate,
    evaluate_llm_quality_gate,
)


def test_evaluate_llm_quality_gate_uses_threshold_semantics() -> None:
    result = evaluate_llm_quality_gate(
        LLMReviewResult(
            findings=(
                LLMReviewFinding(
                    rule_id="llm.semantic.overclaim",
                    severity="warning",
                    message="Warning finding.",
                ),
                LLMReviewFinding(
                    rule_id="llm.semantic.risky_advice",
                    severity="error",
                    message="Error finding.",
                ),
            )
        ),
        "error",
    )

    assert result.enabled is True
    assert result.fail_on == "error"
    assert result.failed is True
    assert result.evaluation_status == "evaluated"
    assert result.matched_finding_count == 1
    assert result.matched_severity_counts == {
        "info": 0,
        "warning": 0,
        "error": 1,
        "critical": 0,
    }
    assert result.matched_file_count == 1


def test_evaluate_llm_quality_gate_returns_not_run_without_result() -> None:
    result = evaluate_llm_quality_gate(None, "warning")

    assert result.enabled is True
    assert result.failed is False
    assert result.evaluation_status == "not_run"
    assert result.matched_finding_count == 0


def test_evaluate_llm_quality_gate_returns_disabled_without_threshold() -> None:
    result = evaluate_llm_quality_gate(
        LLMReviewResult(
            findings=(
                LLMReviewFinding(
                    rule_id="llm.semantic.overclaim",
                    severity="critical",
                    message="Critical finding.",
                ),
            )
        ),
        None,
    )

    assert result.enabled is False
    assert result.fail_on is None
    assert result.failed is False
    assert result.evaluation_status == "disabled"


def test_evaluate_batch_llm_quality_gate_tracks_files_and_failures() -> None:
    result = evaluate_batch_llm_quality_gate(
        LLMSidecarResult(
            summary=LLMSidecarSummary(
                file_count=3,
                succeeded_count=2,
                failed_count=1,
                skipped_count=0,
                finding_count=2,
            ),
            files=(
                LLMSidecarFile(
                    path="a.md",
                    status="success",
                    review=LLMReviewResult(
                        findings=(
                            LLMReviewFinding(
                                rule_id="llm.semantic.overclaim",
                                severity="warning",
                                message="Warning finding.",
                            ),
                        )
                    ),
                ),
                LLMSidecarFile(
                    path="b.md",
                    status="success",
                    review=LLMReviewResult(
                        findings=(
                            LLMReviewFinding(
                                rule_id="llm.semantic.risky_advice",
                                severity="critical",
                                message="Critical finding.",
                            ),
                        )
                    ),
                ),
                LLMSidecarFile(
                    path="c.md",
                    status="failed",
                    error={"error_type": "RuntimeError", "message": "failed"},
                ),
            ),
        ),
        "error",
    )

    assert result.enabled is True
    assert result.failed is True
    assert result.evaluation_status == "execution_failed"
    assert result.matched_finding_count == 1
    assert result.matched_file_count == 1
    assert result.matched_files == ("b.md",)
    assert result.matched_severity_counts == {
        "info": 0,
        "warning": 0,
        "error": 0,
        "critical": 1,
    }
