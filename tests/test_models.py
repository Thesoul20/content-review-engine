import pytest
from pydantic import ValidationError

from content_review_engine.core.models import (
    BatchReviewResult,
    BatchReviewSummary,
    ReviewDocumentMetadata,
    ReviewFinding,
    ReviewIssue,
    ReviewProfile,
    ReviewProfileMetadata,
    ReviewResult,
    ReviewSummary,
    SourceSpan,
)


def test_create_review_issue() -> None:
    issue = ReviewIssue(
        id="WECHAT_TITLE_001",
        severity="medium",
        category="wechat_title",
        title="标题过长",
        description="标题长度超过建议上限。",
        suggestion="建议缩短标题。",
        original_text="这是一个非常长的标题",
        start_line=1,
        end_line=1,
    )

    assert issue.id == "WECHAT_TITLE_001"
    assert issue.severity == "medium"
    assert issue.start_line == 1
    assert issue.end_line == 1


def test_create_review_summary_from_findings() -> None:
    finding = ReviewFinding(
        rule_id="forbidden_terms",
        severity="warning",
        message="发现风险词：绝对安全",
        matched_term="绝对安全",
    )

    summary = ReviewSummary.from_findings([finding])

    assert summary.finding_count == 1
    assert summary.severity_counts == {
        "info": 0,
        "warning": 1,
        "error": 0,
        "critical": 0,
    }


def test_create_review_summary_default_severity_counts_are_zeroed() -> None:
    summary = ReviewSummary(finding_count=0)

    assert summary.severity_counts == {
        "info": 0,
        "warning": 0,
        "error": 0,
        "critical": 0,
    }


def test_create_review_result_with_findings_and_metadata() -> None:
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
        document=ReviewDocumentMetadata(path="article.md"),
        profile=ReviewProfileMetadata(name="wechat", path="profiles/wechat.yml"),
    )

    assert result.schema_version == "review-result.v1"
    assert result.summary.finding_count == 1
    assert result.summary.severity_counts["warning"] == 1
    assert len(result.findings) == 1
    assert result.findings[0] == finding
    assert result.document == ReviewDocumentMetadata(path="article.md")
    assert result.profile == ReviewProfileMetadata(
        name="wechat",
        path="profiles/wechat.yml",
    )


def test_review_summary_counts_non_warning_finding_severity() -> None:
    finding = ReviewFinding(
        rule_id="absolute_claims",
        severity="error",
        message="发现可能存在绝对化表述：全网最强",
        suggestion="建议改为更审慎的表述。",
        matched_term="全网最强",
    )

    summary = ReviewSummary.from_findings([finding])

    assert summary.severity_counts == {
        "info": 0,
        "warning": 0,
        "error": 1,
        "critical": 0,
    }


def test_create_review_profile() -> None:
    profile = ReviewProfile(
        name="wechat",
        target_platform="wechat",
    )

    assert profile.name == "wechat"
    assert profile.target_platform == "wechat"
    assert profile.tone == "clear and professional"
    assert profile.max_title_length == 32
    assert profile.max_paragraph_length == 220
    assert profile.enabled_rules is None


def test_create_review_profile_with_enabled_rules() -> None:
    profile = ReviewProfile(
        name="wechat",
        target_platform="wechat",
        enabled_rules=["forbidden_terms"],
    )

    assert profile.enabled_rules == ["forbidden_terms"]


def test_create_source_span() -> None:
    span = SourceSpan(
        start_line=2,
        start_column=4,
        end_line=2,
        end_column=6,
        start_offset=7,
        end_offset=9,
        matched_text="绝对",
        context="第二行绝对正确",
    )

    assert span.start_line == 2
    assert span.start_column == 4
    assert span.end_offset == 9

    serialized = span.model_dump()
    assert serialized == {
        "start_line": 2,
        "start_column": 4,
        "end_line": 2,
        "end_column": 6,
        "start_offset": 7,
        "end_offset": 9,
        "matched_text": "绝对",
        "context": "第二行绝对正确",
    }


def test_invalid_severity_should_fail() -> None:
    with pytest.raises(ValidationError):
        ReviewIssue(
            id="WECHAT_TITLE_001",
            severity="invalid",
            category="wechat_title",
            title="标题过长",
            description="标题长度超过建议上限。",
            suggestion="建议缩短标题。",
        )


def test_invalid_finding_count_should_fail() -> None:
    with pytest.raises(ValidationError):
        ReviewSummary(finding_count=-1)


def test_create_batch_review_summary_from_results() -> None:
    finding = ReviewFinding(
        rule_id="forbidden_terms",
        severity="warning",
        message="发现风险词：绝对安全",
        matched_term="绝对安全",
    )
    review_result = ReviewResult.from_findings(
        [finding],
        document=ReviewDocumentMetadata(path="article.md"),
        profile=ReviewProfileMetadata(name="wechat"),
    )

    summary = BatchReviewSummary.from_results(file_count=2, results=[review_result])

    assert summary.file_count == 2
    assert summary.reviewed_count == 1
    assert summary.finding_count == 1
    assert summary.files_with_findings == 1
    assert summary.severity_counts == {
        "info": 0,
        "warning": 1,
        "error": 0,
        "critical": 0,
    }


def test_create_batch_review_result_with_results() -> None:
    review_result = ReviewResult.from_findings([])

    batch_result = BatchReviewResult.from_results([review_result], file_count=1)

    assert batch_result.schema_version == "batch-review-result.v1"
    assert batch_result.summary.file_count == 1
    assert batch_result.summary.reviewed_count == 1
    assert batch_result.summary.finding_count == 0
    assert batch_result.results == [review_result]
