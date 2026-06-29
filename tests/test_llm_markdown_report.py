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
from content_review_engine.reports import render_llm_review_markdown, render_llm_sidecar_markdown


def test_render_single_file_llm_markdown_report_with_no_findings() -> None:
    result = LLMReviewResult()

    report = render_llm_review_markdown(result, file_path="article.md")

    assert report.startswith("# LLM Review Report\n")
    assert "| File | article.md |" in report
    assert "| Total Findings | 0 |" in report
    assert "| Source | llm |" in report
    assert "| Advisory | yes |" in report
    assert "| Quality Gate Participation | no |" in report
    assert "| critical | 0 |" in report
    assert "| error | 0 |" in report
    assert "| warning | 0 |" in report
    assert "| info | 0 |" in report
    assert "| unknown | 0 |" in report
    assert report.count("No LLM findings.") == 2
    assert "## Manual Review Checklist" in report
    assert "No manual review checklist items." in report


def test_render_single_file_llm_markdown_report_with_multiple_findings() -> None:
    result = LLMReviewResult(
        provider="mock",
        model="mock-model",
        prompt_version="llm-semantic-review-prompt.v1",
        profile_name="default",
        findings=(
            LLMReviewFinding(
                rule_id="llm.semantic.overclaim",
                severity="warning",
                message="Possible unsupported claim.",
                suggestion="Add evidence.",
                matched_text="guaranteed",
                line=3,
                column=5,
                end_line=3,
                end_column=14,
            ),
            LLMReviewFinding(
                rule_id="llm.semantic.risky_advice",
                severity="error",
                message="Potentially risky advice.",
                suggestion="Add a safety disclaimer.",
                rationale="Medical advice lacks context.",
                category="safety",
                confidence=0.91,
            ),
        ),
        summary=LLMReviewSummary(
            overall_risk="high",
            summary="Two semantic issues found.",
            recommended_action="Revise before publishing.",
            confidence=0.85,
        ),
    )

    report = render_llm_review_markdown(result, file_path="article.md")

    assert "| Provider | mock |" in report
    assert "| Model | mock-model |" in report
    assert "| Prompt Version | llm-semantic-review-prompt.v1 |" in report
    assert "| Profile Name | default |" in report
    assert "| Overall Risk | high |" in report
    assert "| LLM Summary | Two semantic issues found. |" in report
    assert "| Recommended Action | Revise before publishing. |" in report
    assert "| Confidence | 0.85 |" in report
    assert "LLM advisory severity only" in report
    assert "| warning | 1 |" in report
    assert "| error | 1 |" in report
    assert "| warning | llm.semantic.overclaim | llm | yes | no | not provided | 3 | 5 | Possible unsupported claim. | Add evidence. |" in report
    assert "| error | llm.semantic.risky_advice | llm | yes | no | 0.91 | - | - | Potentially risky advice. | Add a safety disclaimer. |" in report
    assert "## Manual Review Checklist" in report
    assert "| LLM-001 | medium | needs_review | pending | no | llm.semantic.overclaim | line 3, column 5 to line 3, column 14 | Possible unsupported claim. | - |" in report
    assert "| LLM-002 | high | needs_review | pending | no | llm.semantic.risky_advice | not provided | Potentially risky advice. | - |" in report
    assert "### 1. llm.semantic.overclaim" in report
    assert "- Source: llm" in report
    assert "- Advisory: yes" in report
    assert "- Quality Gate Participation: no" in report
    assert "- Confidence: not provided" in report
    assert "- Location: line 3, column 5 to line 3, column 14" in report
    assert "- Matched Text: `guaranteed`" in report
    assert "### 2. llm.semantic.risky_advice" in report
    assert "- Rationale: Medical advice lacks context." in report
    assert "- Category: safety" in report
    assert "- Confidence: 0.91" in report


def test_render_single_file_llm_markdown_report_normalizes_unknown_fields() -> None:
    result = LLMReviewResult.model_construct(
        findings=(
            LLMReviewFinding.model_construct(
                rule_id=" \n ",
                severity=" Warning ",
                message="Normalized finding.",
                suggestion="Rewrite it.",
            ),
            LLMReviewFinding.model_construct(
                rule_id="llm.semantic.custom\nrule",
                severity="SEVERE",
                message="Unknown severity.",
                suggestion="Check manually.",
            ),
        )
    )

    report = render_llm_review_markdown(result, file_path="article.md")

    assert "| warning | llm.semantic_review | llm | yes | no | not provided | - | - | Normalized finding. | Rewrite it. |" in report
    assert "| unknown | llm.semantic.custom rule | llm | yes | no | not provided | - | - | Unknown severity. | Check manually. |" in report


def test_render_single_file_llm_markdown_report_escapes_markdown_table_cells() -> None:
    result = LLMReviewResult(
        findings=(
            LLMReviewFinding(
                rule_id="llm.semantic.overclaim",
                severity="warning",
                message="Line 1 | claim\nLine 2",
                suggestion="Rewrite | carefully\nnow",
            ),
        )
    )

    report = render_llm_review_markdown(result, file_path="article|one.md")

    assert r"| File | article\|one.md |" in report
    assert r"| warning | llm.semantic.overclaim | llm | yes | no | not provided | - | - | Line 1 \| claim<br>Line 2 | Rewrite \| carefully<br>now |" in report


def test_render_batch_llm_markdown_report_for_all_success() -> None:
    result = build_llm_sidecar_result(
        [
            build_llm_sidecar_file_success(
                path="a.md",
                review=LLMReviewResult(
                    findings=(
                        LLMReviewFinding(
                            rule_id="llm.semantic.overclaim",
                            severity="warning",
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
                            rule_id="llm.semantic.risky_advice",
                            severity="error",
                            message="Second finding.",
                        ),
                    ),
                    summary=LLMReviewSummary(
                        overall_risk="medium",
                        summary="One issue in this file.",
                        recommended_action="Revise wording.",
                    ),
                ),
            ),
        ],
        llm_provider="mock",
        llm_provider_source="explicit",
    )

    report = render_llm_sidecar_markdown(result)

    assert report.startswith("# Batch LLM Review Report\n")
    assert "| LLM Provider | mock |" in report
    assert "| LLM Provider Source | explicit |" in report
    assert "| Files Reviewed | 2 |" in report
    assert "| Files With LLM Findings | 2 |" in report
    assert "| Files With LLM Errors | 0 |" in report
    assert "| Total LLM Findings | 2 |" in report
    assert "| Source | llm |" in report
    assert "| Advisory | yes |" in report
    assert "| Quality Gate Participation | no |" in report
    assert "| critical | 0 |" in report
    assert "| error | 1 |" in report
    assert "| warning | 1 |" in report
    assert "| a.md | success | 1 | - |" in report
    assert "| b.md | success | 1 | - |" in report
    assert "## Manual Review Checklist" in report
    assert "| LLM-001 | a.md | medium | needs_review | pending | no | llm.semantic.overclaim | not provided | First finding. | - |" in report
    assert "| LLM-002 | b.md | high | needs_review | pending | no | llm.semantic.risky_advice | not provided | Second finding. | - |" in report
    assert "## LLM Execution Review Checklist" not in report
    assert "### `a.md`" in report
    assert "### `b.md`" in report
    assert "- Overall Risk: medium" in report
    assert "- Summary: One issue in this file." in report
    assert "- Confidence: not provided" in report


def test_render_batch_llm_markdown_report_for_partial_failure() -> None:
    result = build_llm_sidecar_result(
        [
            build_llm_sidecar_file_success(
                path="a.md",
                review=LLMReviewResult(
                    findings=(
                        LLMReviewFinding(
                            rule_id="llm.semantic.overclaim",
                            severity="warning",
                            message="Success finding.",
                        ),
                    )
                ),
            ),
            build_llm_sidecar_file_failed(path="b.md", exc=RuntimeError("request failed")),
        ]
    )

    report = render_llm_sidecar_markdown(result)

    assert "| Files With LLM Findings | 1 |" in report
    assert "| Files With LLM Errors | 1 |" in report
    assert "| a.md | success | 1 | - |" in report
    assert "| b.md | failed | 0 | RuntimeError: request failed |" in report
    assert "| LLM-001 | a.md | medium | needs_review | pending | no | llm.semantic.overclaim | not provided | Success finding. | - |" in report
    assert "## LLM Execution Review Checklist" in report
    assert "| LLM-ERR-001 | b.md | needs_rerun | rerun_llm_review | RuntimeError | request failed | - |" in report
    assert "### `b.md`" in report
    assert "- Error Type: `RuntimeError`" in report
    assert "- Message: request failed" in report


def test_render_batch_llm_markdown_report_for_all_no_findings() -> None:
    result = build_llm_sidecar_result(
        [
            build_llm_sidecar_file_success(path="a.md", review=LLMReviewResult()),
            build_llm_sidecar_file_success(path="b.md", review=LLMReviewResult()),
        ]
    )

    report = render_llm_sidecar_markdown(result)

    assert "| Files With LLM Findings | 0 |" in report
    assert "| Total LLM Findings | 0 |" in report
    assert report.count("No LLM findings.") == 4
    assert "No manual review checklist items." in report


def test_render_batch_llm_markdown_report_preserves_stable_ordering() -> None:
    result = LLMSidecarResult(
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
                            message="Z finding.",
                        ),
                    )
                ),
            ),
            LLMSidecarFile(
                path="a.md",
                status="failed",
                finding_count=0,
                error=LLMSidecarError(
                    error_type="LLMProviderError",
                    message="provider failed",
                ),
            ),
            LLMSidecarFile(
                path="m.md",
                status="success",
                finding_count=1,
                review=LLMReviewResult(
                    findings=(
                        LLMReviewFinding(
                            rule_id="llm.semantic.risky_advice",
                            severity="error",
                            message="M finding.",
                        ),
                    )
                ),
            ),
        ),
    )

    report = render_llm_sidecar_markdown(result)

    assert report.index("| z.md | success | 1 | - |") < report.index("| a.md | failed | 0 | LLMProviderError: provider failed |")
    assert report.index("| a.md | failed | 0 | LLMProviderError: provider failed |") < report.index("| m.md | success | 1 | - |")
    assert report.index("### `z.md`") < report.index("### `a.md`")
    assert report.index("### `a.md`") < report.index("### `m.md`")


def test_render_batch_llm_markdown_report_escapes_markdown_table_cells() -> None:
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

    report = render_llm_sidecar_markdown(result)

    assert r"| article\|one.md | failed | 0 | LLM\|ProviderError: Line 1<br>Line 2 |" in report
