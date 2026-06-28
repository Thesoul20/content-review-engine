import pytest
from pydantic import ValidationError

from content_review_engine.llm import (
    LLMSidecarFile,
    LLMProviderError,
    LLMReviewFinding,
    LLMReviewResult,
    build_llm_sidecar_file_failed,
    build_llm_sidecar_file_success,
    build_llm_sidecar_result,
    llm_sidecar_result_to_dict,
)


def test_llm_sidecar_serialization_includes_summary_for_success() -> None:
    result = build_llm_sidecar_result(
        [
            build_llm_sidecar_file_success(
                path="article.md",
                review=LLMReviewResult(
                    findings=(
                        LLMReviewFinding(
                            rule_id="llm_semantic_risk",
                            severity="warning",
                            message="Possible unsupported claim.",
                        ),
                    )
                ),
            )
        ]
    )

    payload = llm_sidecar_result_to_dict(result)

    assert payload == {
        "schema_version": "llm-sidecar-result.v1",
        "summary": {
            "file_count": 1,
            "succeeded_count": 1,
            "failed_count": 0,
            "skipped_count": 0,
            "finding_count": 1,
        },
        "files": [
            {
                "path": "article.md",
                "status": "success",
                "finding_count": 1,
                "review": {
                    "schema_version": "llm-review-result.v1",
                    "findings": [
                        {
                            "rule_id": "llm_semantic_risk",
                            "severity": "warning",
                            "message": "Possible unsupported claim.",
                        }
                    ],
                },
            }
        ],
    }


def test_llm_sidecar_serialization_includes_partial_failure_summary() -> None:
    result = build_llm_sidecar_result(
        [
            build_llm_sidecar_file_success(path="a.md", review=LLMReviewResult()),
            build_llm_sidecar_file_failed(
                path="b.md",
                exc=LLMProviderError("provider unavailable"),
            ),
        ]
    )

    payload = llm_sidecar_result_to_dict(result)

    assert payload["summary"] == {
        "file_count": 2,
        "succeeded_count": 1,
        "failed_count": 1,
        "skipped_count": 0,
        "finding_count": 0,
    }
    assert payload["files"][1] == {
        "path": "b.md",
        "status": "failed",
        "finding_count": 0,
        "error": {
            "error_type": "LLMProviderError",
            "message": "provider unavailable",
        },
    }


def test_llm_sidecar_failed_file_requires_error() -> None:
    with pytest.raises(ValidationError):
        LLMSidecarFile(
            path="broken.md",
            status="failed",
            finding_count=0,
        )
