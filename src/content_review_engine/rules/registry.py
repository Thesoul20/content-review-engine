from __future__ import annotations

from content_review_engine.rules.base import ReviewRule
from content_review_engine.rules.forbidden_terms import DEFAULT_FORBIDDEN_TERMS_RULE


class DuplicateRuleError(ValueError):
    pass


class UnknownRuleError(ValueError):
    pass


class RuleRegistry:
    def __init__(self) -> None:
        self._rules: dict[str, ReviewRule] = {}

    def register(self, rule: ReviewRule) -> None:
        if rule.rule_id in self._rules:
            raise DuplicateRuleError(f"Duplicate rule ID registered: {rule.rule_id}")
        self._rules[rule.rule_id] = rule

    def get(self, rule_id: str) -> ReviewRule:
        try:
            return self._rules[rule_id]
        except KeyError as exc:
            raise UnknownRuleError(f"Unknown rule ID: {rule_id}") from exc

    def has(self, rule_id: str) -> bool:
        return rule_id in self._rules

    def list_rule_ids(self) -> list[str]:
        return list(self._rules)


def build_default_rule_registry() -> RuleRegistry:
    registry = RuleRegistry()
    registry.register(DEFAULT_FORBIDDEN_TERMS_RULE)
    return registry


__all__ = [
    "DuplicateRuleError",
    "RuleRegistry",
    "UnknownRuleError",
    "build_default_rule_registry",
]
