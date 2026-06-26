from __future__ import annotations

from pathlib import Path

from content_review_engine.core.models import (
    ReviewDocumentMetadata,
    ReviewFinding,
    ReviewProfileMetadata,
    ReviewResult,
    SourceSpan,
)
from content_review_engine.llm.models import LLMReviewFinding, LLMReviewResult
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

    assert "| Total Findings | 0 |" in report
    assert "| Quality Gate | Not configured |" in report
    assert "| critical | 0 |" in report
    assert "| - | 0 |" in report
    assert report.count("No findings.") == 2


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
    assert "| warning | forbidden_terms | - | - | 发现风险词：保证赚钱 | - |" in report
    assert "- Matched Text: `保证赚钱`" in report


def test_render_markdown_report_includes_quality_gate_summary() -> None:
    finding = ReviewFinding(
        rule_id="absolute_claims",
        severity="error",
        message="发现可能存在绝对化表述：全网最强",
        matched_term="全网最强",
        suggestion="建议改为更审慎的表述，或补充证据支持该结论。",
    )
    result = ReviewResult.from_findings([finding])

    report = render_markdown_report(result, fail_on="error")

    assert "| Quality Gate | Failed |" in report
    assert "| Fail On | `error` |" in report
    assert "| Matched Gate Findings | 1 |" in report


def test_render_markdown_report_with_empty_llm_result_appends_empty_section() -> None:
    finding = ReviewFinding(
        rule_id="forbidden_terms",
        severity="warning",
        message="发现风险词：绝对安全",
        matched_term="绝对安全",
        matched_text="绝对安全",
    )
    result = ReviewResult.from_findings([finding])

    report = render_markdown_report(result, llm_result=LLMReviewResult())

    assert "## LLM Review" in report
    assert "| Schema Version | llm-review-result.v1 |" in report
    assert "| Total Findings | 0 |" in report
    assert "### LLM Findings" in report
    assert "No LLM findings." in report
    assert "| warning | 1 |" in report
    assert "| forbidden_terms | 1 |" in report
    assert "llm_semantic_risk" not in report


def test_render_markdown_report_with_llm_findings_keeps_deterministic_counts_unchanged() -> None:
    finding = ReviewFinding(
        rule_id="forbidden_terms",
        severity="warning",
        message="发现风险词：绝对安全",
        matched_term="绝对安全",
        matched_text="绝对安全",
    )
    result = ReviewResult.from_findings([finding])
    llm_result = LLMReviewResult(
        provider="mock",
        findings=(
            LLMReviewFinding(
                rule_id="llm_semantic_risk",
                severity="critical",
                message="Semantic concern detected.",
                suggestion="Revise the claim.",
                line=12,
                column=3,
                end_line=12,
                end_column=9,
                matched_text="guaranteed",
                rationale="The statement appears unsupported.",
                category="semantic-risk",
                confidence=0.8,
            ),
        ),
    )

    report = render_markdown_report(result, llm_result=llm_result)
    deterministic_section = report.split("## LLM Review", maxsplit=1)[0]

    assert "| warning | 1 |" in report
    assert "| critical | 0 |" in report
    assert "| forbidden_terms | 1 |" in report
    assert "| llm_semantic_risk |" not in deterministic_section
    assert "## LLM Review" in report
    assert "| Provider | mock |" in report
    assert "| Total Findings | 1 |" in report
    assert "| critical | 1 |" in report
    assert "| critical | llm_semantic_risk | Semantic concern detected. | Revise the claim. |" in report
    assert "### LLM Detailed Findings" in report
    assert "- Location: line 12, column 3 to line 12, column 9" in report
    assert "- Matched Text: `guaranteed`" in report
    assert "- Rationale: The statement appears unsupported." in report
    assert "- Confidence: 0.8" in report


def test_render_markdown_report_llm_section_escapes_markdown_table_cells() -> None:
    result = ReviewResult.from_findings([])
    llm_result = LLMReviewResult(
        findings=(
            LLMReviewFinding(
                rule_id="llm|overclaim",
                severity="warning",
                message="A | B",
                suggestion="Line 1\nLine 2",
            ),
        ),
    )

    report = render_markdown_report(result, llm_result=llm_result)

    assert r"| warning | llm\|overclaim | A \| B | Line 1<br>Line 2 |" in report
