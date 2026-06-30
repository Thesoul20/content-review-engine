from __future__ import annotations

from content_review_engine.core.models import (
    BatchReviewResult,
    ReviewDocumentMetadata,
    ReviewFinding,
    ReviewProfileMetadata,
    ReviewResult,
)
from content_review_engine.llm import (
    LLMSidecarError,
    LLMSidecarFile,
    LLMSidecarResult,
    LLMSidecarSummary,
    LLMReviewFinding,
    LLMReviewResult,
    batch_combined_review_result_to_dict,
    build_batch_combined_review_result,
)
from content_review_engine.reports import (
    render_batch_combined_markdown_report,
    render_batch_markdown_report,
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


def test_render_batch_combined_markdown_report_for_all_succeeded() -> None:
    combined = build_batch_combined_review_result(
        batch_review_result=_build_batch_review_result(),
        batch_llm_result=LLMSidecarResult(
            summary=LLMSidecarSummary(
                file_count=3,
                succeeded_count=3,
                failed_count=0,
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
                                rule_id="Unsafe Medical Claim",
                                severity="warning",
                                message="Needs manual review.",
                                suggestion="Add evidence.",
                                line=3,
                                column=4,
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
                                message="Potentially risky advice.",
                            ),
                        )
                    ),
                ),
                LLMSidecarFile(
                    path="m.md",
                    status="success",
                    finding_count=0,
                    review=LLMReviewResult(),
                ),
            ),
            llm_provider="mock",
            llm_provider_source="explicit",
        ),
    )

    report = render_batch_combined_markdown_report(combined)

    assert report.startswith("# Batch Combined Content Review Report\n")
    assert "| Files Reviewed | 3 |" in report
    assert "| Deterministic Findings | 2 |" in report
    assert "| LLM Batch Status | all_succeeded |" in report
    assert "| LLM Provider | mock |" in report
    assert "| LLM Succeeded | 3 |" in report
    assert "| LLM Failed | 0 |" in report
    assert "| LLM Advisory Findings | 2 |" in report
    assert "| Files With LLM Advisory Findings | 2 |" in report
    assert "| LLM Errors | 0 |" in report
    assert "| z.md | succeeded | 1 | - |" in report
    assert "| a.md | succeeded | 1 | - |" in report
    assert "| m.md | succeeded | 0 | - |" in report
    assert "| z.md | warning | llm.unsafe_medical_claim | llm | yes | no | not provided | 3:4 | Needs manual review. | Add evidence. |" in report
    assert "| a.md | error | llm.semantic_risky_advice | llm | yes | no | not provided | - | Potentially risky advice. | - |" in report
    assert "## LLM Error Summary" in report
    assert "No LLM errors." in report
    assert "## Manual Review Workflow" in report
    assert "## Manual Review Checklist" in report
    assert "| LLM-001 | z.md | medium | needs_review | pending | no | Unsafe Medical Claim | line 3, column 4 | Needs manual review. | - |" in report
    assert "| LLM-002 | a.md | high | needs_review | pending | no | llm.semantic.risky_advice | not provided | Potentially risky advice. | - |" in report
    assert "## Quality Gate Boundary" in report
    assert "Quality gate evaluation remains deterministic-only." in report


def test_render_batch_combined_markdown_report_for_partial_failure() -> None:
    combined = build_batch_combined_review_result(
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
                                rule_id="llm.semantic.overclaim",
                                severity="warning",
                                message="Check the claim.",
                            ),
                        )
                    ),
                ),
                LLMSidecarFile(
                    path="a.md",
                    status="failed",
                    error=LLMSidecarError(
                        error_type="LLMProviderError",
                        message="provider unavailable",
                    ),
                ),
                LLMSidecarFile(path="m.md", status="skipped"),
            ),
        ),
    )

    report = render_batch_combined_markdown_report(combined)

    assert "| LLM Batch Status | partial_failure |" in report
    assert "| LLM Succeeded | 1 |" in report
    assert "| LLM Failed | 1 |" in report
    assert "| LLM Skipped | 1 |" in report
    assert "| LLM Errors | 1 |" in report
    assert "| z.md | succeeded | 1 | - |" in report
    assert "| a.md | failed | 0 | LLMProviderError: provider unavailable |" in report
    assert "| m.md | skipped | 0 | - |" in report
    assert "| a.md | LLMProviderError | provider unavailable | - | - |" in report
    assert "partial LLM failure" in report
    assert "## LLM Execution Review Checklist" in report
    assert "| LLM-ERR-001 | a.md | needs_rerun | rerun_llm_review | LLMProviderError | provider unavailable | - |" in report


def test_render_batch_combined_markdown_report_for_all_failed() -> None:
    combined = build_batch_combined_review_result(
        batch_review_result=_build_batch_review_result(),
        batch_llm_result=LLMSidecarResult(
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
        ),
    )

    report = render_batch_combined_markdown_report(combined)

    assert "| LLM Batch Status | all_failed |" in report
    assert "| LLM Failed | 3 |" in report
    assert report.count("| RuntimeError |") >= 3
    assert "No LLM advisory findings." in report
    assert "All LLM review attempts failed in this batch" in report
    assert "No manual review checklist items." in report
    assert "| LLM-ERR-003 | m.md | needs_rerun | rerun_llm_review | RuntimeError | third failed | - |" in report


def test_render_batch_combined_markdown_report_for_not_run() -> None:
    combined = build_batch_combined_review_result(
        batch_review_result=_build_batch_review_result(),
    )

    report = render_batch_combined_markdown_report(combined)

    assert "| LLM Batch Status | not_run |" in report
    assert "| LLM Not Run | 3 |" in report
    assert "| LLM Provider | - |" in report
    assert report.count("No LLM advisory findings.") == 1
    assert "No LLM review was run for this batch" in report
    assert "No manual review checklist items." in report
    assert "## LLM Execution Review Checklist" not in report


def test_render_batch_combined_markdown_report_for_skipped() -> None:
    combined = build_batch_combined_review_result(
        batch_review_result=_build_batch_review_result(),
        default_llm_status="skipped",
    )

    report = render_batch_combined_markdown_report(combined)

    assert "| LLM Batch Status | skipped |" in report
    assert "| LLM Skipped | 3 |" in report
    assert "LLM review was skipped for this batch" in report
    assert "No LLM advisory findings." in report


def test_render_batch_combined_markdown_report_preserves_deterministic_report_content() -> None:
    batch_review_result = _build_batch_review_result()
    deterministic_report = render_batch_markdown_report(batch_review_result)

    report = render_batch_combined_markdown_report(
        build_batch_combined_review_result(batch_review_result=batch_review_result)
    )

    assert "## Deterministic Review\n\n# Batch Content Review Report" in report
    assert deterministic_report in report


def test_render_batch_combined_markdown_report_escapes_markdown_table_cells() -> None:
    batch_review_result = BatchReviewResult.from_results(
        [
            _build_review_result("article|one.md"),
        ],
        file_count=1,
    )
    combined = build_batch_combined_review_result(
        batch_review_result=batch_review_result,
        batch_llm_result=LLMSidecarResult(
            summary=LLMSidecarSummary(
                file_count=1,
                succeeded_count=1,
                failed_count=0,
                skipped_count=0,
                finding_count=1,
            ),
            files=(
                LLMSidecarFile(
                    path="article|one.md",
                    status="success",
                    finding_count=1,
                    review=LLMReviewResult(
                        findings=(
                            LLMReviewFinding(
                                rule_id="Unsafe | Claim",
                                severity="warning",
                                message="Line 1 | claim\nLine 2",
                                suggestion="Rewrite | carefully\nnow",
                                line=4,
                                column=2,
                            ),
                        )
                    ),
                ),
            ),
        ),
    )

    report = render_batch_combined_markdown_report(combined)

    assert r"| article\|one.md | succeeded | 1 | - |" in report
    assert r"| article\|one.md | warning | llm.unsafe_claim | llm | yes | no | not provided | 4:2 | Line 1 \| claim<br>Line 2 | Rewrite \| carefully<br>now |" in report


def test_render_batch_combined_markdown_report_does_not_change_serializer_output() -> None:
    combined = build_batch_combined_review_result(
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
                    error=LLMSidecarError(
                        error_type="LLMProviderTimeoutError",
                        message="Timed out",
                    ),
                ),
                LLMSidecarFile(path="m.md", status="skipped"),
            ),
        ),
    )
    payload_before = batch_combined_review_result_to_dict(combined)

    report = render_batch_combined_markdown_report(combined)

    assert report.endswith("\n")
    assert batch_combined_review_result_to_dict(combined) == payload_before
