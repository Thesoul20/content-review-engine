from __future__ import annotations

from dataclasses import dataclass

import pytest

from content_review_engine.core.models import ReviewFinding, ReviewProfile
from content_review_engine.core.rule_registry import (
    get_rule_definition,
    get_rule_definitions,
    get_rule_ids,
    is_known_rule_id,
)
from content_review_engine.rules.registry import (
    DuplicateRuleError,
    RuleRegistry,
    UnknownRuleError,
    build_default_rule_registry,
)


@dataclass
class DummyRule:
    rule_id: str
    message: str = "dummy"

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


def test_rule_registry_registers_and_returns_rules() -> None:
    registry = RuleRegistry()
    rule = DummyRule(rule_id="dummy_rule")

    registry.register(rule)
    registry.register(DummyRule(rule_id="disabled_rule"), enabled_by_default=False)

    assert registry.has("dummy_rule") is True
    assert registry.has("disabled_rule") is True
    assert registry.get("dummy_rule") is rule
    assert registry.list_rule_ids() == ["dummy_rule", "disabled_rule"]
    assert registry.list_enabled_rule_ids() == ["dummy_rule"]


def test_rule_registry_rejects_duplicate_rule_ids() -> None:
    registry = RuleRegistry()

    registry.register(DummyRule(rule_id="duplicate_rule"))

    with pytest.raises(DuplicateRuleError, match="Duplicate rule ID registered"):
        registry.register(DummyRule(rule_id="duplicate_rule"))


def test_rule_registry_raises_for_unknown_rule_id() -> None:
    registry = RuleRegistry()

    with pytest.raises(UnknownRuleError, match="Unknown rule ID: missing_rule"):
        registry.get("missing_rule")


def test_default_rule_registry_contains_forbidden_terms_rule() -> None:
    registry = build_default_rule_registry()

    assert registry.has("forbidden_terms") is True
    assert registry.has("absolute_claims") is True
    assert registry.has("markdown_structure") is True
    assert registry.has("markdown_links_images") is True
    assert registry.list_rule_ids() == [
        "forbidden_terms",
        "absolute_claims",
        "markdown_structure",
        "markdown_links_images",
    ]
    assert registry.list_enabled_rule_ids() == ["forbidden_terms"]


def test_rule_metadata_registry_registers_all_current_rule_ids() -> None:
    assert get_rule_ids() == (
        "forbidden_terms",
        "absolute_claims",
        "markdown_structure",
        "markdown_links_images",
    )


def test_rule_metadata_registry_rule_ids_are_unique() -> None:
    rule_ids = get_rule_ids()

    assert len(rule_ids) == len(set(rule_ids))


def test_rule_metadata_registry_order_is_deterministic() -> None:
    definitions = get_rule_definitions()

    assert tuple(definition.rule_id for definition in definitions) == get_rule_ids()


def test_rule_metadata_registry_returns_definition_for_known_rule() -> None:
    definition = get_rule_definition("absolute_claims")

    assert definition is not None
    assert definition.rule_id == "absolute_claims"
    assert definition.category == "claims"
    assert definition.source == "profile-driven"
    assert definition.supports_suppression is True


def test_rule_metadata_registry_returns_none_for_unknown_rule() -> None:
    assert get_rule_definition("missing_rule") is None


def test_rule_metadata_registry_known_rule_id_check_is_exact() -> None:
    assert is_known_rule_id("forbidden_terms") is True
    assert is_known_rule_id("Forbidden_Terms") is False
    assert is_known_rule_id("missing_rule") is False


def test_rule_metadata_registry_definitions_have_non_empty_metadata() -> None:
    for definition in get_rule_definitions():
        assert definition.name
        assert definition.description
        assert definition.category
        assert definition.source
        assert isinstance(definition.supports_suppression, bool)
