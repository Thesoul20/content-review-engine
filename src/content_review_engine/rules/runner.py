from __future__ import annotations

from content_review_engine.core.models import ReviewFinding, ReviewProfile
from content_review_engine.rules.registry import RuleRegistry, build_default_rule_registry


def _resolve_rule_ids(profile: ReviewProfile, registry: RuleRegistry) -> list[str]:
    if profile.enabled_rules is None:
        return registry.list_enabled_rule_ids()
    return list(profile.enabled_rules)


def run_rules(
    text: str,
    profile: ReviewProfile,
    *,
    registry: RuleRegistry | None = None,
) -> list[ReviewFinding]:
    active_registry = registry or build_default_rule_registry()
    findings: list[ReviewFinding] = []

    for rule_id in _resolve_rule_ids(profile, active_registry):
        rule = active_registry.get(rule_id)
        findings.extend(rule.evaluate(text, profile))

    return findings


__all__ = ["run_rules"]
