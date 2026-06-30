from __future__ import annotations

import json
from pathlib import Path

import pytest

from content_review_engine.core.models import (
    BatchReviewResult,
    ReviewDocumentMetadata,
    ReviewFinding,
    ReviewProfileMetadata,
    ReviewResult,
)
from content_review_engine.core.serialization import (
    batch_review_result_to_dict,
    review_result_to_dict,
)
from content_review_engine.llm import (
    LLMSidecarError,
    LLMSidecarFile,
    LLMSidecarResult,
    LLMSidecarSummary,
    LLMReviewFinding,
    LLMReviewResult,
    build_batch_combined_review_envelope,
    build_single_file_combined_review_envelope,
    combined_review_envelope_to_dict,
    combined_review_envelope_to_json,
)


SINGLE_EXAMPLE_PATH = Path("examples/llm_review_artifacts/single-file/combined-result.json")
BATCH_EXAMPLE_PATH = Path("examples/llm_review_artifacts/batch/batch-combined-result.json")


def _build_review_result(path: str, *, severity: str = "warning") -> ReviewResult:
    return ReviewResult.from_findings(
        [
            ReviewFinding(
                rule_id="forbidden_terms",
                severity=severity,
                message="Contains forbidden term.",
                matched_term="best",
            )
        ],
        document=ReviewDocumentMetadata(path=path),
        profile=ReviewProfileMetadata(name="wechat", path="profile.yml"),
    )


def _build_batch_review_result() -> BatchReviewResult:
    return BatchReviewResult.from_results(
        [
            _build_review_result("b.md", severity="warning"),
            _build_review_result("a.md", severity="error"),
        ],
        file_count=2,
    )


def test_single_file_combined_envelope_uses_stable_builder_and_serializer() -> None:
    review_result = _build_review_result("article.md")
    llm_result = LLMReviewResult(
        provider="mock",
        findings=(
            LLMReviewFinding(
                rule_id="Unsafe Medical Claim",
                severity="critical",
                message="Needs human review.",
            ),
        ),
    )

    payload = combined_review_envelope_to_dict(
        build_single_file_combined_review_envelope(
            review_result=review_result,
            llm_result=llm_result,
        )
    )

    assert payload["schema_version"] == "single-file-combined-review-result.v1"
    assert payload["review_result"]["schema_version"] == "review-result.v1"
    assert payload["llm"]["status"] == "succeeded"
    assert payload["llm"]["result"]["schema_version"] == "llm-review-result.v1"
    assert payload["llm"]["finding_candidates"][0]["rule_id"] == "llm.unsafe_medical_claim"
    assert review_result_to_dict(review_result)["findings"] == payload["review_result"]["findings"]
    assert payload["review_result"]["summary"]["severity_counts"]["critical"] == 0


def test_batch_combined_envelope_uses_stable_builder_and_serializer() -> None:
    batch_review_result = _build_batch_review_result()
    batch_llm_result = LLMSidecarResult(
        summary=LLMSidecarSummary(
            file_count=2,
            succeeded_count=1,
            failed_count=1,
            skipped_count=0,
            finding_count=1,
        ),
        files=(
            LLMSidecarFile(
                path="b.md",
                status="success",
                finding_count=1,
                review=LLMReviewResult(
                    findings=(
                        LLMReviewFinding(
                            rule_id="Ambiguous Promise",
                            severity="critical",
                            message="Needs evidence.",
                        ),
                    )
                ),
            ),
            LLMSidecarFile(
                path="a.md",
                status="failed",
                error=LLMSidecarError(
                    error_type="LLMProviderTimeoutError",
                    message="Timed out",
                ),
            ),
        ),
    )

    payload = combined_review_envelope_to_dict(
        build_batch_combined_review_envelope(
            batch_review_result=batch_review_result,
            batch_llm_result=batch_llm_result,
        )
    )

    assert payload["schema_version"] == "batch-combined-review-result.v1"
    assert payload["batch_review_result"]["schema_version"] == "batch-review-result.v1"
    assert [item["file"] for item in payload["llm"]["files"]] == ["b.md", "a.md"]
    assert payload["llm"]["summary"]["succeeded_count"] == 1
    assert payload["llm"]["summary"]["failed_count"] == 1
    assert payload["llm"]["summary"]["advisory_finding_count"] == 1
    assert payload["batch_review_result"]["summary"]["severity_counts"]["critical"] == 0
    assert batch_review_result_to_dict(batch_review_result)["summary"] == payload["batch_review_result"]["summary"]


def test_combined_envelope_json_is_json_compatible_for_single_file_and_batch() -> None:
    single_json = combined_review_envelope_to_json(
        build_single_file_combined_review_envelope(review_result=_build_review_result("single.md"))
    )
    batch_json = combined_review_envelope_to_json(
        build_batch_combined_review_envelope(batch_review_result=_build_batch_review_result())
    )

    single_payload = json.loads(single_json)
    batch_payload = json.loads(batch_json)

    assert single_payload["llm"]["status"] == "not_run"
    assert batch_payload["llm"]["summary"]["not_run_count"] == 2


def test_combined_envelope_example_artifacts_keep_same_top_level_shape() -> None:
    single_example = json.loads(SINGLE_EXAMPLE_PATH.read_text(encoding="utf-8"))
    batch_example = json.loads(BATCH_EXAMPLE_PATH.read_text(encoding="utf-8"))

    single_payload = combined_review_envelope_to_dict(
        build_single_file_combined_review_envelope(review_result=_build_review_result("article.md"))
    )
    batch_payload = combined_review_envelope_to_dict(
        build_batch_combined_review_envelope(batch_review_result=_build_batch_review_result())
    )

    assert list(single_payload.keys()) == list(single_example.keys())
    assert list(single_payload["llm"].keys()) == list(single_example["llm"].keys())
    assert list(batch_payload.keys()) == list(batch_example.keys())
    assert list(batch_payload["llm"].keys()) == list(batch_example["llm"].keys())


def test_combined_envelope_serializer_rejects_unknown_types() -> None:
    with pytest.raises(TypeError):
        combined_review_envelope_to_dict(object())  # type: ignore[arg-type]
