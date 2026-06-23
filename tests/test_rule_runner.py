from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from content_review_engine.core.models import ReviewFinding, ReviewProfile
from content_review_engine.rules.registry import RuleRegistry, UnknownRuleError
from content_review_engine.rules.runner import run_rules

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "markdown"


@dataclass
class RunnerRule:
    rule_id: str
    message: str

    def evaluate(
        self,
        text: str,
        profile: ReviewProfile,
    ) -> list[ReviewFinding]:
        return [
            ReviewFinding(
                rule_id=self.rule_id,
                severity="warning",
                message=self.message,
                matched_term=text,
            )
        ]


def test_run_rules_uses_default_registry_for_forbidden_terms() -> None:
    profile = ReviewProfile(
        name="wechat",
        target_platform="wechat",
        forbidden_terms=["保证赚钱", "绝对安全"],
    )

    findings = run_rules("这篇文章承诺保证赚钱。", profile)

    assert len(findings) == 1
    assert findings[0].rule_id == "forbidden_terms"
    assert findings[0].matched_term == "保证赚钱"


def test_run_rules_executes_explicit_markdown_structure_rule() -> None:
    markdown_text = (FIXTURES_DIR / "markdown_structure_issues.md").read_text(
        encoding="utf-8"
    )
    profile = ReviewProfile(
        name="markdown-structure",
        target_platform="wechat",
        enabled_rules=["markdown_structure"],
    )

    findings = run_rules(markdown_text, profile)

    assert findings
    assert {finding.rule_id for finding in findings} == {"markdown_structure"}
    assert any(
        finding.message == "Heading level jumps from H1 to H3."
        for finding in findings
    )


def test_run_rules_executes_explicit_markdown_links_images_rule() -> None:
    markdown_text = "[文档](#)"
    profile = ReviewProfile(
        name="markdown-links-images",
        target_platform="wechat",
        enabled_rules=["markdown_links_images"],
    )

    findings = run_rules(markdown_text, profile)

    assert len(findings) == 1
    assert findings[0].rule_id == "markdown_links_images"
    assert findings[0].message == "链接目标仍是占位符。"


def test_run_rules_does_not_execute_markdown_links_images_when_not_enabled() -> None:
    markdown_text = "[](https://example.com)"
    profile = ReviewProfile(
        name="forbidden-terms",
        target_platform="wechat",
        forbidden_terms=["保证赚钱"],
        enabled_rules=["forbidden_terms"],
    )

    findings = run_rules(markdown_text, profile)

    assert findings == []


def test_run_rules_respects_explicit_enabled_rules_order() -> None:
    registry = RuleRegistry()
    registry.register(RunnerRule(rule_id="rule_a", message="first"))
    registry.register(RunnerRule(rule_id="rule_b", message="second"))
    profile = ReviewProfile(
        name="wechat",
        target_platform="wechat",
        enabled_rules=["rule_b", "rule_a"],
    )

    findings = run_rules("text", profile, registry=registry)

    assert [finding.rule_id for finding in findings] == ["rule_b", "rule_a"]
    assert [finding.message for finding in findings] == ["second", "first"]


def test_run_rules_raises_for_unknown_enabled_rule() -> None:
    registry = RuleRegistry()
    profile = ReviewProfile(
        name="wechat",
        target_platform="wechat",
        enabled_rules=["missing_rule"],
    )

    with pytest.raises(UnknownRuleError, match="Unknown rule ID: missing_rule"):
        run_rules("text", profile, registry=registry)
