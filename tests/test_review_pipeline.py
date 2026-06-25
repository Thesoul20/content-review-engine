from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from content_review_engine.config import load_profile
from content_review_engine.core.models import ReviewFinding, ReviewProfile, ReviewResult
from content_review_engine.core.models import SourceSpan
from content_review_engine.review import review_document

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
MARKDOWN_FIXTURES_DIR = FIXTURES_DIR / "markdown"
PROFILE_FIXTURES_DIR = FIXTURES_DIR / "profiles"


def test_review_document_returns_review_result_for_forbidden_term() -> None:
    markdown_text = (MARKDOWN_FIXTURES_DIR / "forbidden_terms_article.md").read_text(
        encoding="utf-8"
    )
    profile = load_profile(PROFILE_FIXTURES_DIR / "default.yml")

    result = review_document(markdown_text, profile)

    assert isinstance(result, ReviewResult)
    assert result.schema_version == "review-result.v1"
    assert result.summary.finding_count == 1
    assert result.summary.severity_counts["warning"] == 1
    assert len(result.findings) == 1
    finding = result.findings[0]
    assert finding.rule_id == "forbidden_terms"
    assert finding.matched_term == "绝对安全"
    assert finding.location is not None
    assert finding.location.matched_text == "绝对安全"
    assert finding.location.start_line == 1
    assert finding.location.start_column == 8
    assert result.document is None
    assert result.profile is not None
    assert result.profile.name == "default"
    assert result.profile.path is None


def test_review_document_returns_empty_result_when_no_terms_match() -> None:
    markdown_text = (MARKDOWN_FIXTURES_DIR / "clean_article.md").read_text(encoding="utf-8")
    profile = load_profile(PROFILE_FIXTURES_DIR / "default.yml")

    result = review_document(markdown_text, profile)

    assert result.summary.finding_count == 0
    assert result.summary.severity_counts == {
        "info": 0,
        "warning": 0,
        "error": 0,
        "critical": 0,
    }
    assert result.findings == []


def test_review_document_uses_multiline_fixture_positions() -> None:
    markdown_text = (MARKDOWN_FIXTURES_DIR / "multiline_forbidden_terms.md").read_text(
        encoding="utf-8"
    )
    profile = load_profile(PROFILE_FIXTURES_DIR / "strict.yml")

    result = review_document(markdown_text, profile)

    assert [finding.matched_term for finding in result.findings] == [
        "绝对安全",
        "保证赚钱",
        "100%有效",
    ]
    assert [finding.location.start_line for finding in result.findings] == [3, 4, 5]
    assert [finding.location.start_column for finding in result.findings] == [3, 3, 3]


def test_review_document_behavior_changes_with_profile() -> None:
    strict_profile = ReviewProfile(
        name="strict",
        target_platform="wechat",
        forbidden_terms=["保证赚钱"],
    )
    relaxed_profile = ReviewProfile(
        name="relaxed",
        target_platform="wechat",
        forbidden_terms=["绝对安全"],
    )

    strict_result = review_document("这篇文章承诺保证赚钱。", strict_profile)
    relaxed_result = review_document("这篇文章承诺保证赚钱。", relaxed_profile)

    assert len(strict_result.findings) == 1
    assert relaxed_result.findings == []


def test_review_document_returns_markdown_structure_findings_when_enabled() -> None:
    markdown_text = (MARKDOWN_FIXTURES_DIR / "markdown_structure_issues.md").read_text(
        encoding="utf-8"
    )
    profile = load_profile(PROFILE_FIXTURES_DIR / "markdown_structure.yml")

    result = review_document(markdown_text, profile)

    assert result.summary.finding_count == 4
    assert result.summary.severity_counts == {
        "info": 0,
        "warning": 4,
        "error": 0,
        "critical": 0,
    }
    assert {finding.rule_id for finding in result.findings} == {
        "markdown_structure"
    }
    assert result.findings[0].message == "Heading level jumps from H1 to H3."
    assert result.findings[1].message == "Empty heading detected."
    assert result.findings[2].message == "Multiple H1 headings detected."
    assert result.findings[3].message.startswith("Paragraph exceeds maximum length (")
    assert result.findings[3].message.endswith(" > 80).")
    assert result.findings[3].location is not None
    assert result.findings[3].location.start_line == 9
    assert [finding.location.start_line for finding in result.findings[:3]] == [
        3,
        5,
        7,
    ]


def test_review_document_does_not_run_markdown_links_images_by_default() -> None:
    markdown_text = (MARKDOWN_FIXTURES_DIR / "markdown_links_images_issues.md").read_text(
        encoding="utf-8"
    )
    profile = load_profile(PROFILE_FIXTURES_DIR / "default.yml")

    result = review_document(markdown_text, profile)

    assert result.summary.finding_count == 0
    assert result.findings == []


def test_review_document_returns_markdown_links_images_findings_when_enabled() -> None:
    markdown_text = (MARKDOWN_FIXTURES_DIR / "markdown_links_images_issues.md").read_text(
        encoding="utf-8"
    )
    profile = load_profile(PROFILE_FIXTURES_DIR / "markdown_links_images.yml")

    result = review_document(markdown_text, profile)

    assert result.summary.finding_count == 6
    assert result.summary.severity_counts == {
        "info": 0,
        "warning": 6,
        "error": 0,
        "critical": 0,
    }
    assert [finding.rule_id for finding in result.findings] == [
        "markdown_links_images",
        "markdown_links_images",
        "markdown_links_images",
        "markdown_links_images",
        "markdown_links_images",
        "markdown_links_images",
    ]
    assert [finding.message for finding in result.findings] == [
        "链接文本为空。",
        "链接目标为空。",
        "链接目标仍是占位符。",
        "图片 alt 文本为空。",
        "图片目标为空。",
        "图片目标仍是占位符。",
    ]
    assert [finding.location.start_line for finding in result.findings] == [
        1,
        2,
        3,
        4,
        5,
        6,
    ]


def test_review_document_accepts_loaded_text_and_profile_not_paths() -> None:
    signature = inspect.signature(review_document)

    assert list(signature.parameters) == [
        "markdown_text",
        "profile",
        "document_path",
        "profile_path",
    ]

    profile = ReviewProfile(
        name="wechat",
        target_platform="wechat",
        forbidden_terms=["保证赚钱"],
    )
    markdown_text = "# 标题\n\n这篇文章承诺保证赚钱。"

    result = review_document(markdown_text, profile)

    assert len(result.findings) == 1
    assert result.findings[0].matched_term == "保证赚钱"


def test_review_document_filters_inline_suppressed_findings() -> None:
    profile = ReviewProfile(
        name="wechat",
        target_platform="wechat",
        forbidden_terms=["全网最强", "绝对安全"],
    )
    markdown_text = "\n".join(
        [
            "这里写着全网最强。 <!-- content-review-disable-line forbidden_terms -->",
            "这里写着绝对安全。",
        ]
    )

    result = review_document(markdown_text, profile)

    assert result.summary.finding_count == 1
    assert result.summary.severity_counts["warning"] == 1
    assert [finding.matched_term for finding in result.findings] == ["绝对安全"]


def test_review_document_uses_rule_runner(monkeypatch: pytest.MonkeyPatch) -> None:
    profile = ReviewProfile(
        name="wechat",
        target_platform="wechat",
    )
    finding = ReviewFinding(
        rule_id="forbidden_terms",
        severity="warning",
        message="runner finding",
        matched_term="token",
        matched_text="token",
        location=SourceSpan(
            start_line=1,
            start_column=1,
            end_line=1,
            end_column=5,
            start_offset=0,
            end_offset=5,
            matched_text="token",
        ),
    )

    def fake_run_rules(text: str, profile_arg: ReviewProfile) -> list[ReviewFinding]:
        assert text == "text from pipeline"
        assert profile_arg is profile
        return [finding]

    monkeypatch.setattr("content_review_engine.review.pipeline.run_rules", fake_run_rules)

    result = review_document("text from pipeline", profile)

    assert isinstance(result, ReviewResult)
    assert result.findings == [finding]
    assert result.summary.finding_count == 1
