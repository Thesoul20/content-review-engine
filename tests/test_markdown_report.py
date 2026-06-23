from __future__ import annotations

from pathlib import Path

from content_review_engine.core.models import (
    ReviewDocumentMetadata,
    ReviewFinding,
    ReviewProfileMetadata,
    ReviewResult,
    SourceSpan,
)
from content_review_engine.reports import render_markdown_report

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
EXPECTED_REPORTS_DIR = FIXTURES_DIR / "expected_reports"


def test_render_markdown_report_with_findings_includes_summary_and_details() -> None:
    finding = ReviewFinding(
        rule_id="forbidden_terms",
        severity="warning",
        message="发现风险词：绝对安全",
        matched_term="绝对安全",
        matched_text="绝对安全",
        location=SourceSpan(
            start_line=1,
            start_column=8,
            end_line=1,
            end_column=12,
            start_offset=7,
            end_offset=11,
            matched_text="绝对安全",
            context="# 测试文章 绝对安全",
        ),
    )
    result = ReviewResult.from_findings(
        [finding],
        document=ReviewDocumentMetadata(
            path="tests/fixtures/markdown/forbidden_terms_article.md"
        ),
        profile=ReviewProfileMetadata(
            name="default",
            path="tests/fixtures/profiles/default.yml",
        ),
    )

    report = render_markdown_report(result)
    expected_report = (
        EXPECTED_REPORTS_DIR / "forbidden_terms_report.md"
    ).read_text(encoding="utf-8").rstrip("\n")

    assert report == expected_report


def test_render_markdown_report_handles_zero_findings() -> None:
    result = ReviewResult.from_findings([])

    report = render_markdown_report(result)

    assert "- Findings: 0" in report
    assert "No issues found." in report


def test_render_markdown_report_handles_missing_location() -> None:
    finding = ReviewFinding(
        rule_id="forbidden_terms",
        severity="warning",
        message="发现风险词：保证赚钱",
        matched_term="保证赚钱",
        matched_text="保证赚钱",
        location=None,
    )
    result = ReviewResult.from_findings([finding])

    report = render_markdown_report(result)

    assert "- Location: unavailable" in report
    assert "- Matched: `保证赚钱`" in report
