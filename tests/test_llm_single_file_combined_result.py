from __future__ import annotations

import json

from content_review_engine.core.models import (
    ReviewDocumentMetadata,
    ReviewFinding,
    ReviewProfileMetadata,
    ReviewResult,
)
from content_review_engine.core.quality_gate import quality_gate_failed
from content_review_engine.core.serialization import review_result_to_dict
from content_review_engine.llm import (
    LLMSidecarFile,
    LLMSidecarResult,
    LLMSidecarSummary,
    LLMReviewFinding,
    LLMReviewResult,
    SINGLE_FILE_COMBINED_REVIEW_RESULT_SCHEMA_VERSION,
    build_single_file_combined_review_result,
    llm_review_result_to_dict,
    llm_sidecar_result_to_dict,
    single_file_combined_review_result_to_dict,
)


def _build_review_result() -> ReviewResult:
    return ReviewResult.from_findings(
        [
            ReviewFinding(
                rule_id="forbidden_terms",
                severity="warning",
                message="Contains forbidden term.",
                matched_term="best",
            )
        ],
        document=ReviewDocumentMetadata(path="article.md"),
        profile=ReviewProfileMetadata(name="wechat", path="profile.yml"),
    )


def test_build_single_file_combined_review_result_succeeded_uses_adapter() -> None:
    review_result = _build_review_result()
    llm_result = LLMReviewResult(
        provider="mock",
        findings=(
            LLMReviewFinding(
                rule_id="Unsafe Medical Claim",
                severity="warning",
                message="This wording implies unsupported medical efficacy.",
                suggestion="Qualify the claim and cite evidence.",
                rationale="The sentence sounds therapeutic without support.",
                line=3,
                column=1,
                matched_text="guaranteed recovery",
                category="medical-risk",
            ),
        ),
    )

    combined = build_single_file_combined_review_result(
        review_result=review_result,
        llm_result=llm_result,
    )

    assert combined.schema_version == SINGLE_FILE_COMBINED_REVIEW_RESULT_SCHEMA_VERSION
    assert combined.review_result is review_result
    assert combined.llm_result is llm_result
    assert combined.llm_status == "succeeded"
    assert combined.llm_error is None
    assert combined.advisory is True
    assert combined.llm_quality_gate.enabled is False
    assert len(combined.llm_finding_candidates) == 1
    assert combined.llm_finding_candidates[0].source == "llm"
    assert combined.llm_finding_candidates[0].advisory is True
    assert combined.llm_finding_candidates[0].rule_id == "llm.unsafe_medical_claim"
    assert combined.llm_finding_candidates[0].original_llm_rule_id == "Unsafe Medical Claim"


def test_build_single_file_combined_review_result_not_run_status() -> None:
    combined = build_single_file_combined_review_result(
        review_result=_build_review_result()
    )

    assert combined.llm_status == "not_run"
    assert combined.llm_result is None
    assert combined.llm_error is None
    assert combined.llm_finding_candidates == ()
    assert combined.advisory is True
    assert combined.llm_quality_gate.evaluation_status == "disabled"


def test_build_single_file_combined_review_result_skipped_status() -> None:
    combined = build_single_file_combined_review_result(
        review_result=_build_review_result(),
        llm_status="skipped",
    )

    assert combined.llm_status == "skipped"
    assert combined.llm_result is None
    assert combined.llm_error is None
    assert combined.llm_finding_candidates == ()


def test_build_single_file_combined_review_result_failed_status() -> None:
    combined = build_single_file_combined_review_result(
        review_result=_build_review_result(),
        llm_error={
            "type": "LLMProviderTimeoutError",
            "message": "Timed out while waiting for semantic review output.",
            "provider": "pydanticai",
            "retryable": True,
        },
    )

    assert combined.llm_status == "failed"
    assert combined.llm_result is None
    assert combined.llm_error is not None
    assert combined.llm_error.type == "LLMProviderTimeoutError"
    assert combined.llm_error.provider == "pydanticai"
    assert combined.llm_error.retryable is True
    assert combined.llm_finding_candidates == ()


def test_single_file_combined_review_result_serialization_structure_is_stable() -> None:
    review_result = _build_review_result()
    llm_result = LLMReviewResult(
        provider="mock",
        findings=(
            LLMReviewFinding(
                rule_id="misleading-claim",
                severity="error",
                message="The semantic claim reads stronger than the support.",
                suggestion="Use narrower wording.",
                line=5,
                column=2,
            ),
        ),
    )

    payload = single_file_combined_review_result_to_dict(
        build_single_file_combined_review_result(
            review_result=review_result,
            llm_result=llm_result,
        )
    )

    assert payload["schema_version"] == "single-file-combined-review-result.v1"
    assert payload["review_result"]["schema_version"] == "review-result.v1"
    assert payload["llm"]["status"] == "succeeded"
    assert payload["llm"]["advisory"] is True
    assert payload["llm"]["quality_gate"]["enabled"] is False
    assert payload["llm"]["error"] is None
    assert payload["llm"]["result"]["schema_version"] == "llm-review-result.v1"
    assert payload["llm"]["finding_candidates"][0]["source"] == "llm"
    assert payload["llm"]["finding_candidates"][0]["advisory"] is True
    assert payload["llm"]["finding_candidates"][0]["rule_id"] == "llm.misleading_claim"
    assert payload["llm"]["finding_candidates"][0]["original_index"] == 0


def test_single_file_combined_review_result_payload_is_json_serializable() -> None:
    payload = single_file_combined_review_result_to_dict(
        build_single_file_combined_review_result(
            review_result=_build_review_result(),
            llm_error={
                "type": "LLMSemanticReviewExecutionError",
                "message": "Provider execution failed.",
                "retryable": False,
            },
        )
    )

    serialized = json.loads(json.dumps(payload, ensure_ascii=False))

    assert serialized["llm"]["status"] == "failed"
    assert serialized["llm"]["error"]["type"] == "LLMSemanticReviewExecutionError"
    assert serialized["llm"]["finding_candidates"] == []
    assert serialized["llm"]["quality_gate"]["evaluation_status"] == "disabled"


def test_build_single_file_combined_review_result_does_not_mutate_inputs() -> None:
    review_result = _build_review_result()
    llm_result = LLMReviewResult(
        findings=(
            LLMReviewFinding(
                rule_id="Unsafe Medical Claim",
                severity="critical",
                message="Needs human review.",
            ),
        )
    )
    review_before = review_result_to_dict(review_result)
    llm_before = llm_review_result_to_dict(llm_result)

    build_single_file_combined_review_result(
        review_result=review_result,
        llm_result=llm_result,
    )

    assert review_result_to_dict(review_result) == review_before
    assert llm_review_result_to_dict(llm_result) == llm_before


def test_combined_result_building_does_not_change_sidecar_serialization() -> None:
    llm_result = LLMReviewResult(
        findings=(
            LLMReviewFinding(
                rule_id="llm.semantic.overclaim",
                severity="warning",
                message="Semantic overclaim.",
            ),
        )
    )
    sidecar = LLMSidecarResult(
        summary=LLMSidecarSummary(
            file_count=1,
            succeeded_count=1,
            failed_count=0,
            skipped_count=0,
            finding_count=1,
        ),
        files=(
            LLMSidecarFile(
                path="article.md",
                status="success",
                finding_count=1,
                review=llm_result,
            ),
        ),
    )
    before = llm_sidecar_result_to_dict(sidecar)

    build_single_file_combined_review_result(
        review_result=_build_review_result(),
        llm_result=llm_result,
    )

    assert llm_sidecar_result_to_dict(sidecar) == before


def test_combined_result_does_not_change_quality_gate_boundary() -> None:
    review_result = _build_review_result()
    combined = build_single_file_combined_review_result(
        review_result=review_result,
        llm_result=LLMReviewResult(
            findings=(
                LLMReviewFinding(
                    rule_id="Unsafe Medical Claim",
                    severity="critical",
                    message="Needs human review.",
                ),
            )
        ),
    )

    assert len(combined.llm_finding_candidates) == 1
    assert quality_gate_failed(review_result.summary.severity_counts, "error") is False
    assert quality_gate_failed(review_result.summary.severity_counts, "warning") is True
