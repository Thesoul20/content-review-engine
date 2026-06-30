from __future__ import annotations

from content_review_engine.core.models import (
    BatchReviewResult,
    ReviewDocumentMetadata,
    ReviewFinding,
    ReviewProfileMetadata,
    ReviewResult,
)
from content_review_engine.llm import (
    LLMSidecarFile,
    LLMSidecarResult,
    LLMSidecarSummary,
    LLMReviewFinding,
    LLMReviewResult,
    build_batch_combined_review_result,
    build_single_file_combined_review_result,
)
from content_review_engine.reports.combined import (
    render_batch_combined_markdown,
    render_combined_markdown_report,
    render_single_file_combined_markdown,
)


def _build_single_review_result() -> ReviewResult:
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


def _build_batch_review_result() -> BatchReviewResult:
    return BatchReviewResult.from_results(
        [
            ReviewResult.from_findings(
                [],
                document=ReviewDocumentMetadata(path="article-a.md"),
                profile=ReviewProfileMetadata(name="wechat", path="profile.yml"),
            ),
            ReviewResult.from_findings(
                [
                    ReviewFinding(
                        rule_id="absolute_claims",
                        severity="error",
                        message="Contains risky absolute claim.",
                        matched_term="全网最强",
                    )
                ],
                document=ReviewDocumentMetadata(path="article-b.md"),
                profile=ReviewProfileMetadata(name="wechat", path="profile.yml"),
            ),
        ],
        file_count=2,
    )


def test_render_combined_markdown_report_dispatches_single_file_shape() -> None:
    combined = build_single_file_combined_review_result(
        review_result=_build_single_review_result(),
        llm_result=LLMReviewResult(
            findings=(
                LLMReviewFinding(
                    rule_id="llm.semantic.overclaim",
                    severity="warning",
                    message="Possible overclaim.",
                ),
            )
        ),
    )

    report = render_combined_markdown_report(combined)

    assert report == render_single_file_combined_markdown(combined)
    assert "## Artifact Boundary" in report
    assert "## Deterministic Review Summary" in report
    assert "## LLM Review Summary" in report
    assert "## Quality Gate Behavior" in report


def test_render_combined_markdown_report_dispatches_batch_shape() -> None:
    combined = build_batch_combined_review_result(
        batch_review_result=_build_batch_review_result(),
        batch_llm_result=LLMSidecarResult(
            summary=LLMSidecarSummary(
                file_count=2,
                succeeded_count=1,
                failed_count=0,
                skipped_count=1,
                finding_count=1,
            ),
            files=(
                LLMSidecarFile(
                    path="article-a.md",
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
                LLMSidecarFile(path="article-b.md", status="skipped"),
            ),
        ),
    )

    report = render_combined_markdown_report(combined)

    assert report == render_batch_combined_markdown(combined)
    assert "## Artifact Boundary" in report
    assert "## Deterministic Batch Summary" in report
    assert "## Combined File Results" in report
    assert "## LLM Findings by File" in report
    assert "## Quality Gate Behavior" in report
