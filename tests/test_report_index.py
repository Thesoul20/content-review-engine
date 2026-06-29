from __future__ import annotations

from content_review_engine.core.models import (
    BatchReviewResult,
    ReviewDocumentMetadata,
    ReviewFinding,
    ReviewProfileMetadata,
    ReviewResult,
    SourceSpan,
)
from content_review_engine.llm import (
    LLMReviewFinding,
    LLMReviewResult,
    LLMReviewSummary,
    build_llm_sidecar_file_failed,
    build_llm_sidecar_file_success,
    build_llm_sidecar_result,
)
from content_review_engine.reports import (
    render_batch_report_index,
    render_single_file_report_index,
)


def _build_review_result() -> ReviewResult:
    return ReviewResult.from_findings(
        [
            ReviewFinding(
                rule_id="forbidden_terms",
                severity="warning",
                message="Line 1 | risk\nLine 2",
                matched_term="绝对安全",
                suggestion="Rewrite | carefully\nnow",
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
        ],
        document=ReviewDocumentMetadata(path="article|one.md"),
        profile=ReviewProfileMetadata(
            name="default",
            path="profiles/default\nstrict.yml",
        ),
    )


def test_render_single_file_report_index_for_deterministic_only() -> None:
    report = render_single_file_report_index(
        _build_review_result(),
        deterministic_output_path="review.md",
        deterministic_output_format="markdown",
        report_index_path="review.index.md",
        llm_enabled=False,
    )

    assert report.startswith("# Review Output Index\n")
    assert "| Mode | single-file |" in report
    assert r"| File | article\|one.md |" in report
    assert r"| Profile | profiles/default<br>strict.yml |" in report
    assert "| LLM Review | LLM not enabled |" in report
    assert "| LLM Findings | LLM not enabled |" in report
    assert "| Quality Gate Source | deterministic review only |" in report
    assert "| Deterministic Output | review.md | markdown | Human-readable deterministic review report | no |" in report
    assert "| Report Index | review.index.md | markdown | Navigation and interpretation guide across deterministic and LLM outputs | no |" in report
    assert "LLM JSON Sidecar" not in report
    assert "LLM Markdown Report" not in report
    assert "| Total Findings | 1 |" in report
    assert "| Warning Findings | 1 |" in report
    assert "## LLM Review Summary" in report
    assert "| Status | LLM not enabled |" in report


def test_render_single_file_report_index_for_hybrid_review() -> None:
    llm_result = LLMReviewResult(
        provider="mock",
        model="mock-model",
        findings=(
            LLMReviewFinding(
                rule_id="llm.semantic.overclaim",
                severity="warning",
                message="Possible overclaim.",
                suggestion="Use a softer claim.",
            ),
        ),
        summary=LLMReviewSummary(
            overall_risk="medium",
            summary="One semantic issue found.",
            recommended_action="Revise wording.",
        ),
    )

    report = render_single_file_report_index(
        _build_review_result(),
        deterministic_output_path="review.json",
        deterministic_output_format="json",
        report_index_path="review.index.md",
        llm_enabled=True,
        llm_result=llm_result,
        llm_output_path="review.llm.json",
        llm_report_path="review.llm.md",
    )

    assert "| LLM Review | enabled |" in report
    assert "| LLM Findings | 1 |" in report
    assert "| Deterministic Output | review.json | json | Canonical machine-readable deterministic review result | yes |" in report
    assert "| LLM JSON Sidecar | review.llm.json | json | Machine-readable LLM semantic review result | yes, for LLM layer |" in report
    assert "| LLM Markdown Report | review.llm.md | markdown | Human-readable LLM semantic review report | no |" in report
    assert "| Schema Version | llm-review-result.v1 |" in report
    assert "| Provider | mock |" in report
    assert "| Model | mock-model |" in report
    assert "| Overall Risk | medium |" in report
    assert "| Summary | One semantic issue found. |" in report
    assert "| Recommended Action | Revise wording. |" in report


def test_render_single_file_report_index_handles_markdown_escaping() -> None:
    llm_result = LLMReviewResult(
        summary=LLMReviewSummary(
            summary="LLM line 1 | note\nLLM line 2",
        )
    )

    report = render_single_file_report_index(
        _build_review_result(),
        deterministic_output_path=None,
        deterministic_output_format="text",
        report_index_path="review|index.md",
        llm_enabled=True,
        llm_result=llm_result,
        llm_report_path="review.llm\nreport.md",
    )

    assert r"| Deterministic Output | stdout (not written to file) | text | Human-readable deterministic review summary | no |" in report
    assert r"| LLM Markdown Report | review.llm<br>report.md | markdown | Human-readable LLM semantic review report | no |" in report
    assert r"| Report Index | review\|index.md | markdown | Navigation and interpretation guide across deterministic and LLM outputs | no |" in report
    assert r"| Summary | LLM line 1 \| note<br>LLM line 2 |" in report


def _build_batch_result() -> BatchReviewResult:
    results = [
        ReviewResult.from_findings(
            [],
            document=ReviewDocumentMetadata(path="z.md"),
            profile=ReviewProfileMetadata(name="default", path="profiles/default.yml"),
        ),
        ReviewResult.from_findings(
            [
                ReviewFinding(
                    rule_id="forbidden_terms",
                    severity="warning",
                    message="Warning finding.",
                    matched_term="绝对安全",
                )
            ],
            document=ReviewDocumentMetadata(path="a.md"),
            profile=ReviewProfileMetadata(name="default", path="profiles/default.yml"),
        ),
        ReviewResult.from_findings(
            [
                ReviewFinding(
                    rule_id="absolute_claims",
                    severity="error",
                    message="Error finding.",
                    matched_term="全网最强",
                )
            ],
            document=ReviewDocumentMetadata(path="m.md"),
            profile=ReviewProfileMetadata(name="default", path="profiles/default.yml"),
        ),
    ]
    return BatchReviewResult.from_results(results, file_count=3)


def test_render_batch_report_index_for_deterministic_only() -> None:
    report = render_batch_report_index(
        _build_batch_result(),
        input_dir="articles",
        profile_path="profiles/default.yml",
        deterministic_output_path="batch.md",
        deterministic_output_format="markdown",
        report_index_path="batch.index.md",
        llm_enabled=False,
    )

    assert report.startswith("# Review Output Index\n")
    assert "| Mode | batch |" in report
    assert "| Input Directory | articles |" in report
    assert "| Files Reviewed | 3 |" in report
    assert "| Deterministic Findings | 2 |" in report
    assert "| LLM Review | LLM not enabled |" in report
    assert "| LLM Findings | LLM not enabled |" in report
    assert "| Quality Gate Source | deterministic review only |" in report
    assert "| Files Discovered | 3 |" in report
    assert "| Files With Findings | 2 |" in report
    assert "| Warning Findings | 1 |" in report
    assert "| Error Findings | 1 |" in report
    assert "| - | LLM not enabled | - | - |" in report
    assert "## LLM Error Summary" not in report


def test_render_batch_report_index_for_hybrid_review() -> None:
    llm_result = build_llm_sidecar_result(
        [
            build_llm_sidecar_file_success(
                path="z.md",
                review=LLMReviewResult(),
            ),
            build_llm_sidecar_file_success(
                path="a.md",
                review=LLMReviewResult(
                    findings=(
                        LLMReviewFinding(
                            rule_id="llm.semantic.overclaim",
                            severity="warning",
                            message="A finding.",
                        ),
                    )
                ),
            ),
            build_llm_sidecar_file_success(
                path="m.md",
                review=LLMReviewResult(
                    findings=(
                        LLMReviewFinding(
                            rule_id="llm.semantic.risky_advice",
                            severity="error",
                            message="M finding.",
                        ),
                    ),
                ),
            ),
        ],
        llm_provider="mock",
        llm_provider_source="explicit",
    )

    report = render_batch_report_index(
        _build_batch_result(),
        input_dir="articles",
        profile_path="profiles/default.yml",
        deterministic_output_path="batch.json",
        deterministic_output_format="json",
        report_index_path="batch.index.md",
        llm_enabled=True,
        llm_result=llm_result,
        llm_output_path="batch.llm.json",
        llm_report_path="batch.llm.md",
    )

    assert "| LLM Review | enabled |" in report
    assert "| LLM Findings | 2 |" in report
    assert "| Deterministic Output | batch.json | json | Canonical machine-readable deterministic review result | yes |" in report
    assert "| LLM JSON Sidecar | batch.llm.json | json | Machine-readable aggregate LLM semantic review result | yes, for LLM layer |" in report
    assert "| LLM Markdown Report | batch.llm.md | markdown | Human-readable aggregate LLM semantic review report | no |" in report
    assert "| Provider | mock |" in report
    assert "| Provider Source | explicit |" in report
    assert "| Files With LLM Findings | 2 |" in report
    assert "| Files With LLM Errors | 0 |" in report
    assert "| z.md | success | 0 | - |" in report
    assert "| a.md | success | 1 | - |" in report
    assert "| m.md | success | 1 | - |" in report


def test_render_batch_report_index_for_partial_llm_failure() -> None:
    llm_result = build_llm_sidecar_result(
        [
            build_llm_sidecar_file_success(path="z.md", review=LLMReviewResult()),
            build_llm_sidecar_file_failed(
                path="a.md",
                exc=RuntimeError("provider failed"),
            ),
            build_llm_sidecar_file_success(path="m.md", review=LLMReviewResult()),
        ]
    )

    report = render_batch_report_index(
        _build_batch_result(),
        input_dir="articles",
        profile_path="profiles/default.yml",
        deterministic_output_path="batch.md",
        deterministic_output_format="markdown",
        report_index_path="batch.index.md",
        llm_enabled=True,
        llm_result=llm_result,
        llm_output_path="batch.llm.json",
    )

    assert "| Files With LLM Errors | 1 |" in report
    assert "| a.md | failed | 0 | RuntimeError: provider failed |" in report
    assert "## LLM Error Summary" in report
    assert "| a.md | RuntimeError: provider failed |" in report


def test_render_batch_report_index_preserves_stable_ordering() -> None:
    llm_result = build_llm_sidecar_result(
        [
            build_llm_sidecar_file_success(path="z.md", review=LLMReviewResult()),
            build_llm_sidecar_file_failed(path="a.md", exc=RuntimeError("failed")),
            build_llm_sidecar_file_success(path="m.md", review=LLMReviewResult()),
        ]
    )

    report = render_batch_report_index(
        _build_batch_result(),
        input_dir="articles",
        profile_path="profiles/default.yml",
        deterministic_output_path="batch.md",
        deterministic_output_format="markdown",
        report_index_path="batch.index.md",
        llm_enabled=True,
        llm_result=llm_result,
    )

    assert report.index("| z.md | success | 0 | - |") < report.index(
        "| a.md | failed | 0 | RuntimeError: failed |"
    )
    assert report.index("| a.md | failed | 0 | RuntimeError: failed |") < report.index(
        "| m.md | success | 0 | - |"
    )
