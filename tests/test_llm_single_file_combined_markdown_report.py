from __future__ import annotations

from content_review_engine.core.models import (
    ReviewDocumentMetadata,
    ReviewFinding,
    ReviewProfileMetadata,
    ReviewResult,
)
from content_review_engine.llm import (
    LLMQualityGateResult,
    LLMReviewFinding,
    LLMReviewResult,
    build_single_file_combined_review_result,
)
from content_review_engine.reports import (
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
    assert "## Artifact Boundary" in report
    assert "## Deterministic Review Summary" in report
    assert "## Deterministic Findings" in report
    assert "## LLM Review Summary" in report
    assert "## LLM Findings" in report
    assert "| Status | succeeded |" in report
    assert "| Advisory Findings | 1 |" in report
    assert "| Quality Gate Participation | no |" in report
    assert "| Explicit LLM Gate | disabled |" in report
    assert "| LLM Gate Evaluation | disabled |" in report
    assert "LLM findings are advisory semantic review suggestions" in report
    assert "| warning | llm.unsafe_medical_claim | llm | yes | no | not provided | 3:1 | Needs manual confirmation. | Qualify the wording. |" in report
    assert "## Manual Review Workflow" in report
    assert "## Manual Review Checklist" in report
    assert "| LLM-001 | medium | needs_review | pending | no | Unsafe Medical Claim | line 3, column 1 | Needs manual confirmation. | - |" in report
    assert "## Quality Gate Behavior" in report
    assert "## Artifact Notes" in report


def test_render_combined_markdown_report_for_succeeded_status_with_no_llm_findings() -> None:
    report = render_single_file_combined_markdown_report(
        build_single_file_combined_review_result(
            review_result=_build_review_result(),
            llm_result=LLMReviewResult(provider="mock"),
        )
    )

    assert "| Status | succeeded |" in report
    assert "| Advisory Findings | 0 |" in report
    assert "LLM review succeeded but returned no advisory findings." in report
    assert "No manual review checklist items." in report


def test_render_combined_markdown_report_for_not_run_status() -> None:
    report = render_single_file_combined_markdown_report(
        build_single_file_combined_review_result(review_result=_build_review_result())
    )

    assert "| Status | not_run |" in report
    assert "LLM review was not run. No advisory findings are available in this artifact." in report
    assert "## LLM Error" not in report
    assert "## Manual Review Checklist" in report
    assert "No manual review checklist items." in report


def test_render_combined_markdown_report_for_skipped_status() -> None:
    report = render_single_file_combined_markdown_report(
        build_single_file_combined_review_result(
            review_result=_build_review_result(),
            llm_status="skipped",
        )
    )

    assert "| Status | skipped |" in report
    assert "LLM review was skipped. No advisory findings are available in this artifact." in report


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

    assert "| Status | failed |" in report
    assert "| LLM Error | LLMProviderTimeoutError: Timed out while waiting for semantic review output. |" in report
    assert "## LLM Error" in report
    assert "| Type | LLMProviderTimeoutError |" in report
    assert "| Message | Timed out while waiting for semantic review output. |" in report
    assert "| Provider | pydanticai |" in report
    assert "| Retryable | true |" in report
    assert "inspect the structured error" in report


def test_render_combined_markdown_report_preserves_deterministic_report_content() -> None:
    report = render_single_file_combined_markdown_report(
        build_single_file_combined_review_result(review_result=_build_review_result())
    )

    assert "## Deterministic Findings" in report
    assert "| warning | forbidden_terms | - | - | Contains forbidden term. | Replace it with supported wording. |" in report


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

    assert "## Quality Gate Behavior" in report
    assert "Deterministic quality gate evaluation remains unchanged and still reads deterministic findings only." in report
    assert "When `--llm-fail-on` is set, it is evaluated independently from deterministic `--fail-on` and can also trigger CLI exit code `1`." in report


def test_render_combined_markdown_report_displays_explicit_llm_gate_result() -> None:
    report = render_single_file_combined_markdown_report(
        build_single_file_combined_review_result(
            review_result=_build_review_result(),
            llm_result=LLMReviewResult(
                findings=(
                    LLMReviewFinding(
                        rule_id="llm.semantic.risky_advice",
                        severity="error",
                        message="Error semantic issue.",
                    ),
                )
            ),
            llm_quality_gate=LLMQualityGateResult(
                enabled=True,
                fail_on="error",
                failed=True,
                evaluation_status="evaluated",
                matched_finding_count=1,
                matched_severity_counts={
                    "info": 0,
                    "warning": 0,
                    "error": 1,
                    "critical": 0,
                },
                matched_file_count=1,
            ),
        )
    )

    assert "| Explicit LLM Gate | enabled |" in report
    assert "| LLM Gate Threshold | error |" in report
    assert "| LLM Gate Status | failed |" in report
    assert "| LLM Gate Evaluation | evaluated |" in report
    assert "| LLM Gate Matched Findings | 1 |" in report


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


def test_render_combined_markdown_report_redacts_absolute_paths_in_summary() -> None:
    review_result = ReviewResult.from_findings(
        [],
        document=ReviewDocumentMetadata(path="/Users/example/workspace/article.md"),
        profile=ReviewProfileMetadata(name="wechat", path="/Users/example/workspace/profile.yml"),
    )

    report = render_single_file_combined_markdown_report(
        build_single_file_combined_review_result(review_result=review_result)
    )

    assert "/Users/example/workspace/article.md" not in report
    assert "/Users/example/workspace/profile.yml" not in report
    assert "| File | article.md |" in report
    assert "| Profile | profile.yml |" in report
