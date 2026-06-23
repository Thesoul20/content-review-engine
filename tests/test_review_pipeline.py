from __future__ import annotations

import inspect
from pathlib import Path

from content_review_engine.config import load_profile
from content_review_engine.core.models import ReviewFinding, ReviewProfile
from content_review_engine.review import review_document

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
MARKDOWN_FIXTURES_DIR = FIXTURES_DIR / "markdown"
PROFILE_FIXTURES_DIR = FIXTURES_DIR / "profiles"


def test_review_document_returns_finding_for_forbidden_term() -> None:
    markdown_text = (MARKDOWN_FIXTURES_DIR / "forbidden_terms_article.md").read_text(
        encoding="utf-8"
    )
    profile = load_profile(PROFILE_FIXTURES_DIR / "default.yml")

    findings = review_document(markdown_text, profile)

    assert len(findings) == 1
    finding = findings[0]
    assert isinstance(finding, ReviewFinding)
    assert finding.rule_id == "forbidden_terms"
    assert finding.matched_term == "绝对安全"
    assert finding.location is not None
    assert finding.location.matched_text == "绝对安全"
    assert finding.location.start_line == 1
    assert finding.location.start_column == 8


def test_review_document_returns_empty_list_when_no_terms_match() -> None:
    markdown_text = (MARKDOWN_FIXTURES_DIR / "clean_article.md").read_text(encoding="utf-8")
    profile = load_profile(PROFILE_FIXTURES_DIR / "default.yml")

    findings = review_document(markdown_text, profile)

    assert findings == []


def test_review_document_uses_multiline_fixture_positions() -> None:
    markdown_text = (MARKDOWN_FIXTURES_DIR / "multiline_forbidden_terms.md").read_text(
        encoding="utf-8"
    )
    profile = load_profile(PROFILE_FIXTURES_DIR / "strict.yml")

    findings = review_document(markdown_text, profile)

    assert [finding.matched_term for finding in findings] == [
        "绝对安全",
        "保证赚钱",
        "100%有效",
    ]
    assert [finding.location.start_line for finding in findings] == [3, 4, 5]
    assert [finding.location.start_column for finding in findings] == [3, 3, 3]


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

    strict_findings = review_document("这篇文章承诺保证赚钱。", strict_profile)
    relaxed_findings = review_document("这篇文章承诺保证赚钱。", relaxed_profile)

    assert len(strict_findings) == 1
    assert relaxed_findings == []


def test_review_document_accepts_loaded_text_and_profile_not_paths() -> None:
    signature = inspect.signature(review_document)

    assert list(signature.parameters) == ["markdown_text", "profile"]

    profile = ReviewProfile(
        name="wechat",
        target_platform="wechat",
        forbidden_terms=["保证赚钱"],
    )
    markdown_text = "# 标题\n\n这篇文章承诺保证赚钱。"

    findings = review_document(markdown_text, profile)

    assert len(findings) == 1
    assert findings[0].matched_term == "保证赚钱"
