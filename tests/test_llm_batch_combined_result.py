from __future__ import annotations

import json

from content_review_engine.core.models import (
    BatchReviewResult,
    ReviewDocumentMetadata,
    ReviewFinding,
    ReviewProfileMetadata,
    ReviewResult,
)
from content_review_engine.core.quality_gate import quality_gate_failed
from content_review_engine.core.serialization import batch_review_result_to_dict
from content_review_engine.llm import (
    BATCH_COMBINED_REVIEW_RESULT_SCHEMA_VERSION,
    LLMSidecarError,
    LLMSidecarFile,
    LLMSidecarResult,
    LLMSidecarSummary,
    LLMReviewFinding,
    LLMReviewResult,
    batch_combined_review_result_to_dict,
    build_batch_combined_review_result,
    llm_sidecar_result_to_dict,
)


def _build_review_result(
    path: str,
    *,
    findings: list[ReviewFinding] | None = None,
) -> ReviewResult:
    return ReviewResult.from_findings(
        [] if findings is None else findings,
        document=ReviewDocumentMetadata(path=path),
        profile=ReviewProfileMetadata(name="wechat", path="profile.yml"),
    )


def _build_batch_review_result() -> BatchReviewResult:
    return BatchReviewResult.from_results(
        [
            _build_review_result("z.md"),
            _build_review_result(
                "a.md",
                findings=[
                    ReviewFinding(
                        rule_id="forbidden_terms",
                        severity="warning",
                        message="Contains forbidden term.",
                        matched_term="best",
                    )
                ],
            ),
            _build_review_result(
                "m.md",
                findings=[
                    ReviewFinding(
                        rule_id="absolute_claims",
                        severity="error",
                        message="Contains risky absolute claim.",
                        matched_term="全网最强",
                    )
                ],
            ),
        ],
        file_count=3,
    )


def test_build_batch_combined_review_result_all_succeeded_uses_adapter() -> None:
    batch_review_result = _build_batch_review_result()
    before = batch_review_result_to_dict(batch_review_result)
    sidecar = LLMSidecarResult(
        summary=LLMSidecarSummary(
            file_count=3,
            succeeded_count=3,
            failed_count=0,
            skipped_count=0,
            finding_count=3,
        ),
        files=(
            LLMSidecarFile(
                path="z.md",
                status="success",
                finding_count=1,
                review=LLMReviewResult(
                    findings=(
                        LLMReviewFinding(
                            rule_id="Unsafe Medical Claim",
                            severity="critical",
                            message="Needs human review.",
                        ),
                    )
                ),
            ),
            LLMSidecarFile(
                path="a.md",
                status="success",
                finding_count=1,
                review=LLMReviewResult(
                    findings=(
                        LLMReviewFinding(
                            rule_id="llm.semantic.overclaim",
                            severity="warning",
                            message="Possible overclaim.",
                        ),
                    )
                ),
            ),
            LLMSidecarFile(
                path="m.md",
                status="success",
                finding_count=1,
                review=LLMReviewResult(
                    findings=(
                        LLMReviewFinding(
                            rule_id="custom ambiguity",
                            severity="error",
                            message="Semantic ambiguity detected.",
                        ),
                    )
                ),
            ),
        ),
    )

    combined = build_batch_combined_review_result(
        batch_review_result=batch_review_result,
        batch_llm_result=sidecar,
    )

    assert combined.schema_version == BATCH_COMBINED_REVIEW_RESULT_SCHEMA_VERSION
    assert combined.batch_review_result is batch_review_result
    assert combined.batch_llm_result is sidecar
    assert combined.advisory is True
    assert [item.file for item in combined.files] == ["z.md", "a.md", "m.md"]
    assert all(item.llm_status == "succeeded" for item in combined.files)
    assert all(item.advisory is True for item in combined.files)
    assert combined.files[0].llm_finding_candidates[0].rule_id == "llm.unsafe_medical_claim"
    assert combined.files[1].llm_finding_candidates[0].rule_id == "llm.semantic_overclaim"
    assert combined.files[2].llm_finding_candidates[0].rule_id == "llm.custom_ambiguity"
    assert combined.llm_summary.total_files == 3
    assert combined.llm_summary.succeeded_count == 3
    assert combined.llm_summary.failed_count == 0
    assert combined.llm_summary.advisory_finding_count == 3
    assert combined.llm_summary.files_with_advisory_findings == 3
    assert batch_review_result_to_dict(batch_review_result) == before


def test_build_batch_combined_review_result_partial_failure() -> None:
    batch_review_result = _build_batch_review_result()
    sidecar = LLMSidecarResult(
        summary=LLMSidecarSummary(
            file_count=3,
            succeeded_count=2,
            failed_count=1,
            skipped_count=0,
            finding_count=2,
        ),
        files=(
            LLMSidecarFile(
                path="z.md",
                status="success",
                finding_count=1,
                review=LLMReviewResult(
                    findings=(
                        LLMReviewFinding(
                            rule_id="llm.semantic.overclaim",
                            severity="warning",
                            message="Warning one.",
                        ),
                    )
                ),
            ),
            LLMSidecarFile(
                path="a.md",
                status="success",
                finding_count=1,
                review=LLMReviewResult(
                    findings=(
                        LLMReviewFinding(
                            rule_id="llm.semantic.risky_advice",
                            severity="error",
                            message="Error one.",
                        ),
                    )
                ),
            ),
            LLMSidecarFile(
                path="m.md",
                status="failed",
                finding_count=0,
                error=LLMSidecarError(
                    error_type="LLMProviderError",
                    message="provider unavailable",
                ),
            ),
        ),
    )

    combined = build_batch_combined_review_result(
        batch_review_result=batch_review_result,
        batch_llm_result=sidecar,
    )

    assert [item.llm_status for item in combined.files] == [
        "succeeded",
        "succeeded",
        "failed",
    ]
    assert combined.files[2].llm_error is not None
    assert combined.files[2].llm_error.type == "LLMProviderError"
    assert combined.files[2].llm_finding_candidates == ()
    assert len(combined.files[0].llm_finding_candidates) == 1
    assert len(combined.files[1].llm_finding_candidates) == 1
    assert combined.llm_summary.succeeded_count == 2
    assert combined.llm_summary.failed_count == 1
    assert combined.llm_summary.error_count == 1
    assert combined.llm_summary.advisory_finding_count == 2
    assert combined.batch_review_result.summary.file_count == 3


def test_build_batch_combined_review_result_all_failed() -> None:
    batch_review_result = _build_batch_review_result()
    sidecar = LLMSidecarResult(
        summary=LLMSidecarSummary(
            file_count=3,
            succeeded_count=0,
            failed_count=3,
            skipped_count=0,
            finding_count=0,
        ),
        files=(
            LLMSidecarFile(
                path="z.md",
                status="failed",
                error=LLMSidecarError(error_type="RuntimeError", message="first failed"),
            ),
            LLMSidecarFile(
                path="a.md",
                status="failed",
                error=LLMSidecarError(error_type="RuntimeError", message="second failed"),
            ),
            LLMSidecarFile(
                path="m.md",
                status="failed",
                error=LLMSidecarError(error_type="RuntimeError", message="third failed"),
            ),
        ),
    )

    combined = build_batch_combined_review_result(
        batch_review_result=batch_review_result,
        batch_llm_result=sidecar,
    )

    assert all(item.llm_status == "failed" for item in combined.files)
    assert all(item.llm_finding_candidates == () for item in combined.files)
    assert combined.llm_summary.failed_count == 3
    assert combined.llm_summary.error_count == 3
    assert combined.batch_review_result is batch_review_result
    assert quality_gate_failed(batch_review_result.summary.severity_counts, "error") is True
    assert quality_gate_failed(batch_review_result.summary.severity_counts, "critical") is False


def test_build_batch_combined_review_result_not_run() -> None:
    batch_review_result = _build_batch_review_result()

    combined = build_batch_combined_review_result(
        batch_review_result=batch_review_result,
    )

    assert combined.batch_llm_result is None
    assert all(item.llm_status == "not_run" for item in combined.files)
    assert all(item.llm_error is None for item in combined.files)
    assert all(item.llm_finding_candidates == () for item in combined.files)
    assert combined.llm_summary.not_run_count == 3
    assert combined.llm_summary.skipped_count == 0


def test_build_batch_combined_review_result_skipped() -> None:
    batch_review_result = _build_batch_review_result()

    combined = build_batch_combined_review_result(
        batch_review_result=batch_review_result,
        default_llm_status="skipped",
    )

    assert combined.batch_llm_result is None
    assert all(item.llm_status == "skipped" for item in combined.files)
    assert combined.llm_summary.skipped_count == 3
    assert combined.llm_summary.not_run_count == 0


def test_batch_combined_review_result_serializer_structure_is_stable() -> None:
    payload = batch_combined_review_result_to_dict(
        build_batch_combined_review_result(
            batch_review_result=_build_batch_review_result(),
            batch_llm_result=LLMSidecarResult(
                summary=LLMSidecarSummary(
                    file_count=3,
                    succeeded_count=1,
                    failed_count=1,
                    skipped_count=1,
                    finding_count=1,
                ),
                files=(
                    LLMSidecarFile(
                        path="z.md",
                        status="success",
                        finding_count=1,
                        review=LLMReviewResult(
                            findings=(
                                LLMReviewFinding(
                                    rule_id="Ambiguous Promise",
                                    severity="warning",
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
                    LLMSidecarFile(
                        path="m.md",
                        status="skipped",
                    ),
                ),
            ),
        )
    )

    assert payload["schema_version"] == "batch-combined-review-result.v1"
    assert payload["batch_review_result"]["schema_version"] == "batch-review-result.v1"
    assert payload["llm"]["advisory"] is True
    assert payload["llm"]["summary"]["total_files"] == 3
    assert payload["llm"]["quality_gate"]["enabled"] is False
    assert payload["llm"]["result"]["schema_version"] == "llm-sidecar-result.v2"
    assert payload["llm"]["files"][0]["file"] == "z.md"
    assert payload["llm"]["files"][0]["status"] == "succeeded"
    assert payload["llm"]["files"][0]["advisory"] is True
    assert payload["llm"]["files"][0]["result"]["schema_version"] == "llm-review-result.v1"
    assert payload["llm"]["files"][0]["finding_candidates"][0]["advisory"] is True
    assert payload["llm"]["files"][1]["error"]["type"] == "LLMProviderTimeoutError"
    assert payload["llm"]["files"][2]["status"] == "skipped"


def test_batch_combined_review_result_payload_is_json_serializable() -> None:
    payload = batch_combined_review_result_to_dict(
        build_batch_combined_review_result(
            batch_review_result=_build_batch_review_result(),
        )
    )

    serialized = json.loads(json.dumps(payload, ensure_ascii=False))

    assert serialized["llm"]["summary"]["not_run_count"] == 3
    assert serialized["llm"]["files"][0]["finding_candidates"] == []
    assert serialized["llm"]["quality_gate"]["evaluation_status"] == "disabled"


def test_batch_combined_result_does_not_change_existing_serializers() -> None:
    batch_review_result = _build_batch_review_result()
    sidecar = LLMSidecarResult(
        summary=LLMSidecarSummary(
            file_count=3,
            succeeded_count=1,
            failed_count=1,
            skipped_count=1,
            finding_count=1,
        ),
        files=(
            LLMSidecarFile(
                path="z.md",
                status="success",
                finding_count=1,
                review=LLMReviewResult(
                    findings=(
                        LLMReviewFinding(
                            rule_id="llm.semantic.overclaim",
                            severity="warning",
                            message="Finding.",
                        ),
                    )
                ),
            ),
            LLMSidecarFile(
                path="a.md",
                status="failed",
                error=LLMSidecarError(error_type="RuntimeError", message="failed"),
            ),
            LLMSidecarFile(path="m.md", status="skipped"),
        ),
    )
    batch_before = batch_review_result_to_dict(batch_review_result)
    sidecar_before = llm_sidecar_result_to_dict(sidecar)

    build_batch_combined_review_result(
        batch_review_result=batch_review_result,
        batch_llm_result=sidecar,
    )

    assert batch_review_result_to_dict(batch_review_result) == batch_before
    assert llm_sidecar_result_to_dict(sidecar) == sidecar_before


def test_batch_combined_result_does_not_change_quality_gate_boundary() -> None:
    batch_review_result = _build_batch_review_result()
    combined = build_batch_combined_review_result(
        batch_review_result=batch_review_result,
        batch_llm_result=LLMSidecarResult(
            summary=LLMSidecarSummary(
                file_count=3,
                succeeded_count=3,
                failed_count=0,
                skipped_count=0,
                finding_count=3,
            ),
            files=(
                LLMSidecarFile(
                    path="z.md",
                    status="success",
                    finding_count=1,
                    review=LLMReviewResult(
                        findings=(
                            LLMReviewFinding(
                                rule_id="critical semantic issue",
                                severity="critical",
                                message="Critical advisory finding.",
                            ),
                        )
                    ),
                ),
                LLMSidecarFile(path="a.md", status="success", review=LLMReviewResult()),
                LLMSidecarFile(path="m.md", status="success", review=LLMReviewResult()),
            ),
        ),
    )

    assert combined.llm_summary.advisory_finding_count == 1
    assert batch_review_result.summary.severity_counts == {
        "info": 0,
        "warning": 1,
        "error": 1,
        "critical": 0,
    }
    assert quality_gate_failed(batch_review_result.summary.severity_counts, "error") is True
    assert quality_gate_failed(batch_review_result.summary.severity_counts, "critical") is False


def test_batch_combined_result_keeps_deterministic_file_order_and_ignores_sidecar_extras() -> None:
    combined = build_batch_combined_review_result(
        batch_review_result=_build_batch_review_result(),
        batch_llm_result=LLMSidecarResult(
            summary=LLMSidecarSummary(
                file_count=4,
                succeeded_count=1,
                failed_count=0,
                skipped_count=3,
                finding_count=0,
            ),
            files=(
                LLMSidecarFile(path="extra.md", status="success", review=LLMReviewResult()),
                LLMSidecarFile(path="m.md", status="skipped"),
                LLMSidecarFile(path="z.md", status="skipped"),
                LLMSidecarFile(path="a.md", status="skipped"),
            ),
        ),
        default_llm_status="not_run",
    )

    assert [item.file for item in combined.files] == ["z.md", "a.md", "m.md"]
    assert [item.llm_status for item in combined.files] == ["skipped", "skipped", "skipped"]


def test_batch_combined_result_serializer_redacts_secret_like_error_content() -> None:
    payload = batch_combined_review_result_to_dict(
        build_batch_combined_review_result(
            batch_review_result=_build_batch_review_result(),
            batch_llm_result=LLMSidecarResult(
                summary=LLMSidecarSummary(
                    file_count=3,
                    succeeded_count=0,
                    failed_count=1,
                    skipped_count=2,
                    finding_count=0,
                ),
                files=(
                    LLMSidecarFile(
                        path="z.md",
                        status="failed",
                        error=LLMSidecarError(
                            error_type="RuntimeError",
                            message=(
                                "Traceback (most recent call last):\n"
                                '  File "/tmp/test.py", line 1, in run\n'
                                "api_key=sk-secret-value-12345678 "
                                "environment variable 'OPENAI_API_KEY'"
                            ),
                        ),
                    ),
                    LLMSidecarFile(path="a.md", status="skipped"),
                    LLMSidecarFile(path="m.md", status="skipped"),
                ),
            ),
        )
    )

    error_message = payload["llm"]["files"][0]["error"]["message"]

    assert "sk-secret-value-12345678" not in error_message
    assert "OPENAI_API_KEY" not in error_message
    assert "Traceback" not in error_message
    assert "<redacted>" in error_message
