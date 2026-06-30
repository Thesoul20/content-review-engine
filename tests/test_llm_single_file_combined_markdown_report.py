from __future__ import annotations

from content_review_engine.core.models import (
    ReviewDocumentMetadata,
    ReviewFinding,
    ReviewProfileMetadata,
    ReviewResult,
)
from content_review_engine.llm import (
    LLMReviewFinding,
    LLMReviewResult,
    build_single_file_combined_review_result,
)
from content_review_engine.reports import (
    render_markdown_report,
    render_single_file_combined_markdown_report,
)


def _build_review_result() -> ReviewResult:
    return ReviewResult.from_findings(
        [
            ReviewFinding(
                rule_id="forbidden_terms",
                severity="warning",
                message="Contains forbidden term.",
                matched_term="best",
                suggestion="Replace it with supported wording.",
            )
        ],
        document=ReviewDocumentMetadata(path="article.md"),
        profile=ReviewProfileMetadata(name="wechat", path="profile.yml"),
    )


def test_render_combined_markdown_report_for_succeeded_status() -> None:
    review_result = _build_review_result()
    llm_result = LLMReviewResult(
        provider="mock",
        findings=(
            LLMReviewFinding(
                rule_id="Unsafe Medical Claim",
                severity="warning",
                message="Needs manual confirmation.",
                suggestion="Qualify the wording.",
                line=3,
                column=1,
            ),
        ),
    )

    report = render_single_file_combined_markdown_report(
        build_single_file_combined_review_result(
            review_result=review_result,
            llm_result=llm_result,
        )
    )

    assert report.startswith("# Combined Content Review Report\n")
    assert "| LLM Status | succeeded |" in report
    assert "| LLM Advisory Findings | 1 |" in report
    assert "| LLM Advisory Policy | yes |" in report
    assert "| Quality Gate Scope | deterministic-only |" in report
    assert "## LLM Execution" in report
    assert "LLM findings are advisory semantic review suggestions" in report
    assert "| warning | llm.unsafe_medical_claim | llm | yes | no | not provided | 3:1 | Needs manual confirmation. | Qualify the wording. |" in report
    assert "## Manual Review Workflow" in report
    assert "## Manual Review Checklist" in report
    assert "| LLM-001 | medium | needs_review | pending | no | Unsafe Medical Claim | line 3, column 1 | Needs manual confirmation. | - |" in report


def test_render_combined_markdown_report_for_succeeded_status_with_no_llm_findings() -> None:
    report = render_single_file_combined_markdown_report(
        build_single_file_combined_review_result(
            review_result=_build_review_result(),
            llm_result=LLMReviewResult(provider="mock"),
        )
    )

    assert "| LLM Status | succeeded |" in report
    assert "| LLM Advisory Findings | 0 |" in report
    assert report.count("No LLM advisory findings.") == 1
    assert "No manual review checklist items." in report


def test_render_combined_markdown_report_for_not_run_status() -> None:
    report = render_single_file_combined_markdown_report(
        build_single_file_combined_review_result(review_result=_build_review_result())
    )

    assert "| LLM Status | not_run |" in report
    assert "| Status | not_run |" in report
    assert report.count("No LLM advisory findings.") == 1
    assert "No LLM findings are available in this run" in report
    assert "## LLM Error" not in report
    assert "## Manual Review Checklist" not in report


def test_render_combined_markdown_report_for_skipped_status() -> None:
    report = render_single_file_combined_markdown_report(
        build_single_file_combined_review_result(
            review_result=_build_review_result(),
            llm_status="skipped",
        )
    )

    assert "| LLM Status | skipped |" in report
    assert "| Status | skipped |" in report
    assert report.count("No LLM advisory findings.") == 1
    assert "No LLM findings are available in this run" in report


def test_render_combined_markdown_report_for_failed_status_displays_error() -> None:
    report = render_single_file_combined_markdown_report(
        build_single_file_combined_review_result(
            review_result=_build_review_result(),
            llm_error={
                "type": "LLMProviderTimeoutError",
                "message": "Timed out while waiting for semantic review output.",
                "provider": "pydanticai",
                "retryable": True,
            },
        )
    )

    assert "| LLM Status | failed |" in report
    assert "| LLM Error | LLMProviderTimeoutError: Timed out while waiting for semantic review output. |" in report
    assert "## LLM Error" in report
    assert "| Type | LLMProviderTimeoutError |" in report
    assert "| Message | Timed out while waiting for semantic review output. |" in report
    assert "| Provider | pydanticai |" in report
    assert "| Retryable | true |" in report
    assert "inspect the structured error" in report


def test_render_combined_markdown_report_preserves_deterministic_report_content() -> None:
    review_result = _build_review_result()
    deterministic_report = render_markdown_report(review_result)

    report = render_single_file_combined_markdown_report(
        build_single_file_combined_review_result(review_result=review_result)
    )

    assert "## Deterministic Review\n\n# Content Review Report" in report
    assert deterministic_report in report


def test_render_combined_markdown_report_includes_quality_gate_boundary() -> None:
    report = render_single_file_combined_markdown_report(
        build_single_file_combined_review_result(
            review_result=_build_review_result(),
            llm_result=LLMReviewResult(
                findings=(
                    LLMReviewFinding(
                        rule_id="llm.semantic.risky_advice",
                        severity="critical",
                        message="Critical semantic issue.",
                    ),
                )
            ),
        )
    )

    assert "## Quality Gate Boundary" in report
    assert "Quality gate evaluation remains deterministic-only." in report
    assert "do not participate in severity counts, rule counts, fail-on, quality gate, or exit code." in report


def test_render_combined_markdown_report_escapes_markdown_table_cells() -> None:
    review_result = ReviewResult.from_findings(
        [],
        document=ReviewDocumentMetadata(path="article|one.md"),
        profile=ReviewProfileMetadata(name="wechat", path="profile|one.yml"),
    )
    llm_result = LLMReviewResult(
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
    )

    report = render_single_file_combined_markdown_report(
        build_single_file_combined_review_result(
            review_result=review_result,
            llm_result=llm_result,
        )
    )

    assert r"| File | article\|one.md |" in report
    assert r"| Profile | profile\|one.yml |" in report
    assert r"| warning | llm.unsafe_claim | llm | yes | no | not provided | 4:2 | Line 1 \| claim<br>Line 2 | Rewrite \| carefully<br>now |" in report
