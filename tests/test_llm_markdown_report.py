from __future__ import annotations

from content_review_engine.llm import (
    LLMSidecarError,
    LLMSidecarFile,
    LLMSidecarResult,
    LLMSidecarSummary,
    LLMReviewFinding,
    LLMReviewResult,
    LLMReviewSummary,
    build_llm_sidecar_file_failed,
    build_llm_sidecar_file_success,
    build_llm_sidecar_result,
)
from content_review_engine.reports import render_llm_sidecar_markdown_report


def test_render_single_file_llm_markdown_report_with_findings() -> None:
    result = build_llm_sidecar_result(
        [
            build_llm_sidecar_file_success(
                path="article.md",
                review=LLMReviewResult(
                    provider="mock",
                    model="mock-model",
                    findings=(
                        LLMReviewFinding(
                            rule_id="llm_semantic_risk",
                            severity="warning",
                            message="Possible unsupported claim.",
                            suggestion="Add evidence.",
                            matched_text="guaranteed",
                            line=3,
                            column=5,
                            end_line=3,
                            end_column=14,
                        ),
                    ),
                    summary=LLMReviewSummary(
                        overall_risk="medium",
                        summary="One semantic issue.",
                        recommended_action="Revise the claim.",
                        confidence=0.8,
                    ),
                ),
            )
        ]
    )

    report = render_llm_sidecar_markdown_report(result)

    assert report.startswith("# LLM Sidecar Review Report\n")
    assert "| Files | 1 |" in report
    assert "| Succeeded | 1 |" in report
    assert "| Failed | 0 |" in report
    assert "| Skipped | 0 |" in report
    assert "| Findings | 1 |" in report
    assert "| article.md | success | 1 | - |" in report
    assert "#### Review Summary" in report
    assert "- Overall Risk: medium" in report
    assert "- Summary: One semantic issue." in report
    assert "- Recommended Action: Revise the claim." in report
    assert "#### Finding 1" in report
    assert "- Rule: `llm_semantic_risk`" in report
    assert "- Suggestion: Add evidence." in report
    assert "- Matched Text: `guaranteed`" in report
    assert "- Location: line 3, column 5 to line 3, column 14" in report


def test_render_single_file_llm_markdown_report_with_no_findings() -> None:
    result = build_llm_sidecar_result(
        [build_llm_sidecar_file_success(path="article.md", review=LLMReviewResult())]
    )

    report = render_llm_sidecar_markdown_report(result)

    assert "| article.md | success | 0 | - |" in report
    assert "No LLM findings." in report


def test_render_single_file_llm_markdown_report_for_failed_file() -> None:
    result = build_llm_sidecar_result(
        [build_llm_sidecar_file_failed(path="article.md", exc=RuntimeError("provider failed"))]
    )

    report = render_llm_sidecar_markdown_report(result)

    assert "| article.md | failed | 0 | RuntimeError: provider failed |" in report
    assert "LLM review failed." in report
    assert "- Error Type: `RuntimeError`" in report
    assert "- Message: provider failed" in report
    assert "Traceback" not in report


def test_render_batch_llm_markdown_report_for_all_success() -> None:
    result = build_llm_sidecar_result(
        [
            build_llm_sidecar_file_success(
                path="a.md",
                review=LLMReviewResult(
                    findings=(
                        LLMReviewFinding(
                            rule_id="llm_a",
                            severity="info",
                            message="First finding.",
                        ),
                    )
                ),
            ),
            build_llm_sidecar_file_success(
                path="b.md",
                review=LLMReviewResult(
                    findings=(
                        LLMReviewFinding(
                            rule_id="llm_b",
                            severity="warning",
                            message="Second finding.",
                        ),
                    )
                ),
            ),
        ]
    )

    report = render_llm_sidecar_markdown_report(result)

    assert report.startswith("# Batch LLM Sidecar Review Report\n")
    assert "| Files | 2 |" in report
    assert "| Succeeded | 2 |" in report
    assert "| Findings | 2 |" in report
    assert "### `a.md`" in report
    assert "### `b.md`" in report
    assert "- Rule: `llm_a`" in report
    assert "- Rule: `llm_b`" in report


def test_render_batch_llm_markdown_report_for_partial_failure() -> None:
    result = build_llm_sidecar_result(
        [
            build_llm_sidecar_file_success(
                path="a.md",
                review=LLMReviewResult(
                    findings=(
                        LLMReviewFinding(
                            rule_id="llm_success",
                            severity="warning",
                            message="Success finding.",
                        ),
                    )
                ),
            ),
            build_llm_sidecar_file_failed(path="b.md", exc=RuntimeError("request failed")),
        ]
    )

    report = render_llm_sidecar_markdown_report(result)

    assert "| Succeeded | 1 |" in report
    assert "| Failed | 1 |" in report
    assert "| a.md | success | 1 | - |" in report
    assert "| b.md | failed | 0 | RuntimeError: request failed |" in report
    assert "### `b.md`" in report
    assert "LLM review failed." in report


def test_render_batch_llm_markdown_report_for_all_failed() -> None:
    result = build_llm_sidecar_result(
        [
            build_llm_sidecar_file_failed(path="a.md", exc=RuntimeError("a failed")),
            build_llm_sidecar_file_failed(path="b.md", exc=RuntimeError("b failed")),
        ]
    )

    report = render_llm_sidecar_markdown_report(result)

    assert "| Succeeded | 0 |" in report
    assert "| Failed | 2 |" in report
    assert "| Findings | 0 |" in report
    assert report.count("LLM review failed.") == 2


def test_render_batch_llm_markdown_report_displays_skipped_entries() -> None:
    result = LLMSidecarResult(
        summary=LLMSidecarSummary(
            file_count=2,
            succeeded_count=0,
            failed_count=0,
            skipped_count=2,
            finding_count=0,
        ),
        files=(
            LLMSidecarFile(path="a.md", status="skipped", finding_count=0),
            LLMSidecarFile(path="b.md", status="skipped", finding_count=0),
        ),
    )

    report = render_llm_sidecar_markdown_report(result)

    assert "| Skipped | 2 |" in report
    assert "| a.md | skipped | 0 | - |" in report
    assert report.count("LLM review skipped.") == 2


def test_render_llm_markdown_report_escapes_markdown_table_cells() -> None:
    result = LLMSidecarResult(
        summary=LLMSidecarSummary(
            file_count=1,
            succeeded_count=0,
            failed_count=1,
            skipped_count=0,
            finding_count=0,
        ),
        files=(
            LLMSidecarFile(
                path="article|one.md",
                status="failed",
                finding_count=0,
                error=LLMSidecarError(
                    error_type="LLM|ProviderError",
                    message="Line 1\nLine 2",
                ),
            ),
        ),
    )

    report = render_llm_sidecar_markdown_report(result)

    assert r"| article\|one.md | failed | 0 | LLM\|ProviderError: Line 1<br>Line 2 |" in report
