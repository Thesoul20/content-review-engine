import pytest
from pydantic import ValidationError

from content_review_engine.core.models import ReviewIssue, ReviewProfile, ReviewResult


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


def test_create_review_result_with_issues() -> None:
    issue = ReviewIssue(
        id="WECHAT_TITLE_001",
        severity="medium",
        category="wechat_title",
        title="标题过长",
        description="标题长度超过建议上限。",
        suggestion="建议缩短标题。",
    )

    result = ReviewResult(
        document_id="doc-001",
        profile_name="wechat",
        overall_score=88,
        summary="发现 1 个问题。",
        issues=[issue],
    )

    assert result.document_id == "doc-001"
    assert result.profile_name == "wechat"
    assert result.overall_score == 88
    assert len(result.issues) == 1
    assert result.issues[0].id == "WECHAT_TITLE_001"


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


def test_score_below_zero_should_fail() -> None:
    with pytest.raises(ValidationError):
        ReviewResult(
            document_id="doc-001",
            profile_name="wechat",
            overall_score=-1,
            summary="Invalid score.",
            issues=[],
        )


def test_score_above_100_should_fail() -> None:
    with pytest.raises(ValidationError):
        ReviewResult(
            document_id="doc-001",
            profile_name="wechat",
            overall_score=101,
            summary="Invalid score.",
            issues=[],
        )
