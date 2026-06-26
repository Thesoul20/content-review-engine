"""Runtime registry for deterministic rule implementations.

This module wires rule objects into the review pipeline and is separate from
the descriptive metadata registry in ``content_review_engine.core.rule_registry``.
"""

from __future__ import annotations

from content_review_engine.rules.absolute_claims import DEFAULT_ABSOLUTE_CLAIMS_RULE
from content_review_engine.rules.base import ReviewRule
from content_review_engine.rules.forbidden_terms import DEFAULT_FORBIDDEN_TERMS_RULE


class DuplicateRuleError(ValueError):
    pass


class UnknownRuleError(ValueError):
    pass


class RuleRegistry:
    def __init__(self) -> None:
        self._rules: dict[str, ReviewRule] = {}
        self._enabled_rule_ids: list[str] = []

    def register(self, rule: ReviewRule, *, enabled_by_default: bool = True) -> None:
        if rule.rule_id in self._rules:
            raise DuplicateRuleError(f"Duplicate rule ID registered: {rule.rule_id}")
        self._rules[rule.rule_id] = rule
        if enabled_by_default:
            self._enabled_rule_ids.append(rule.rule_id)

    def get(self, rule_id: str) -> ReviewRule:
        try:
            return self._rules[rule_id]
        except KeyError as exc:
            raise UnknownRuleError(f"Unknown rule ID: {rule_id}") from exc

    def has(self, rule_id: str) -> bool:
        return rule_id in self._rules

    def list_rule_ids(self) -> list[str]:
        return list(self._rules)

    def list_enabled_rule_ids(self) -> list[str]:
        return list(self._enabled_rule_ids)


def build_default_rule_registry() -> RuleRegistry:
    registry = RuleRegistry()
    registry.register(DEFAULT_FORBIDDEN_TERMS_RULE)
    registry.register(DEFAULT_ABSOLUTE_CLAIMS_RULE, enabled_by_default=False)
    from content_review_engine.rules.markdown_structure import (
        DEFAULT_MARKDOWN_STRUCTURE_RULE,
    )
    from content_review_engine.rules.markdown_links_images import (
        DEFAULT_MARKDOWN_LINKS_IMAGES_RULE,
    )

    registry.register(DEFAULT_MARKDOWN_STRUCTURE_RULE, enabled_by_default=False)
    registry.register(DEFAULT_MARKDOWN_LINKS_IMAGES_RULE, enabled_by_default=False)
    return registry


__all__ = [
    "DuplicateRuleError",
    "RuleRegistry",
    "UnknownRuleError",
    "build_default_rule_registry",
]
