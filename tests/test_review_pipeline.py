from __future__ import annotations

import inspect

from content_review_engine.core.models import ReviewFinding, ReviewProfile
from content_review_engine.review import review_document


def test_review_document_returns_finding_for_forbidden_term() -> None:
    profile = ReviewProfile(
        name="wechat",
        target_platform="wechat",
        forbidden_terms=["保证赚钱", "绝对安全"],
    )

    findings = review_document("这篇文章承诺保证赚钱。", profile)

    assert len(findings) == 1
    finding = findings[0]
    assert isinstance(finding, ReviewFinding)
    assert finding.rule_id == "forbidden_terms"
    assert finding.matched_term == "保证赚钱"
    assert finding.location is not None
    assert finding.location.matched_text == "保证赚钱"


def test_review_document_returns_empty_list_when_no_terms_match() -> None:
    profile = ReviewProfile(
        name="wechat",
        target_platform="wechat",
        forbidden_terms=["保证赚钱", "绝对安全"],
    )

    findings = review_document("这篇文章只是在说明产品特点。", profile)

    assert findings == []


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
