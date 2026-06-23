from __future__ import annotations

from content_review_engine.core.models import ReviewFinding, SourceSpan
from content_review_engine.reports import render_markdown_report


def test_render_markdown_report_with_findings_includes_summary_and_details() -> None:
    findings = [
        ReviewFinding(
            rule_id="forbidden_terms",
            severity="warning",
            message="发现风险词：保证赚钱",
            matched_term="保证赚钱",
            matched_text="保证赚钱",
            location=SourceSpan(
                start_line=2,
                start_column=4,
                end_line=2,
                end_column=8,
                start_offset=7,
                end_offset=11,
                matched_text="保证赚钱",
                context="第二行保证赚钱",
            ),
        )
    ]

    report = render_markdown_report(
        findings,
        document_path="article.md",
        profile_name="wechat",
        profile_path="profiles/wechat.yaml",
    )

    assert "# Content Review Report" in report
    assert "- Document: `article.md`" in report
    assert "- Profile: `profiles/wechat.yaml`" in report
    assert "- Findings: 1" in report
    assert "### forbidden_terms" in report
    assert "- Severity: warning" in report
    assert "- Message: 发现风险词：保证赚钱" in report
    assert "- Line: 2" in report
    assert "- Column: 4" in report
    assert "- Matched: `保证赚钱`" in report
    assert "- Context: 第二行保证赚钱" in report


def test_render_markdown_report_handles_zero_findings() -> None:
    report = render_markdown_report([], document_path="article.md", profile_name="wechat")

    assert "- Findings: 0" in report
    assert "No issues found." in report


def test_render_markdown_report_handles_missing_location() -> None:
    findings = [
        ReviewFinding(
            rule_id="forbidden_terms",
            severity="warning",
            message="发现风险词：保证赚钱",
            matched_term="保证赚钱",
            matched_text="保证赚钱",
            location=None,
        )
    ]

    report = render_markdown_report(findings)

    assert "- Location: unavailable" in report
    assert "- Matched: `保证赚钱`" in report
