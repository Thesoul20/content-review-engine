from __future__ import annotations

from pathlib import Path

from content_review_engine.config import load_profile
from content_review_engine.review import review_document

EXAMPLE_PROFILES_DIR = Path(__file__).resolve().parent.parent / "profiles" / "examples"


def test_load_all_example_profiles() -> None:
    expected = {
        "general-basic.yaml": ("general-basic", "general"),
        "wechat-basic.yaml": ("wechat-basic", "wechat"),
        "wechat-strict.yaml": ("wechat-strict", "wechat"),
    }

    for filename, (name, target_platform) in expected.items():
        profile = load_profile(EXAMPLE_PROFILES_DIR / filename)

        assert profile.name == name
        assert profile.target_platform == target_platform
        assert profile.enabled_rules == ["forbidden_terms", "absolute_claims"]
        assert profile.absolute_claims_terms


def test_review_document_with_wechat_basic_example_profile() -> None:
    markdown_text = "这是一款全网最强的内容审计工具。"
    profile = load_profile(EXAMPLE_PROFILES_DIR / "wechat-basic.yaml")

    result = review_document(markdown_text, profile)

    assert result.summary.finding_count == 1
    assert result.summary.severity_counts == {
        "info": 0,
        "warning": 1,
        "error": 0,
        "critical": 0,
    }
    assert [finding.rule_id for finding in result.findings] == ["absolute_claims"]
    assert result.findings[0].matched_term == "全网最强"
    assert result.findings[0].severity == "warning"
