"""Descriptive metadata for built-in rule IDs.

This module does not execute rules or participate directly in the runtime
review pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuleDefinition:
    rule_id: str
    name: str
    description: str
    category: str
    source: str
    supports_suppression: bool


_RULE_DEFINITIONS: tuple[RuleDefinition, ...] = (
    RuleDefinition(
        rule_id="forbidden_terms",
        name="Forbidden Terms",
        description=(
            "Detects configured forbidden or risky literal terms from the active profile."
        ),
        category="terms",
        source="profile-driven",
        supports_suppression=True,
    ),
    RuleDefinition(
        rule_id="absolute_claims",
        name="Absolute Claims",
        description=(
            "Detects configured literal absolute or overconfident language patterns."
        ),
        category="claims",
        source="profile-driven",
        supports_suppression=True,
    ),
    RuleDefinition(
        rule_id="markdown_structure",
        name="Markdown Structure",
        description=(
            "Detects Markdown heading and paragraph structure issues."
        ),
        category="markdown",
        source="built-in",
        supports_suppression=True,
    ),
    RuleDefinition(
        rule_id="markdown_links_images",
        name="Markdown Links And Images",
        description=(
            "Detects Markdown link and image hygiene issues."
        ),
        category="links",
        source="built-in",
        supports_suppression=True,
    ),
)

_RULE_DEFINITION_BY_ID = {
    definition.rule_id: definition for definition in _RULE_DEFINITIONS
}

if len(_RULE_DEFINITION_BY_ID) != len(_RULE_DEFINITIONS):
    raise ValueError("Duplicate rule IDs found in rule definition registry.")


def get_rule_definitions() -> tuple[RuleDefinition, ...]:
    return _RULE_DEFINITIONS


def get_rule_definition(rule_id: str) -> RuleDefinition | None:
    return _RULE_DEFINITION_BY_ID.get(rule_id)


def get_rule_ids() -> tuple[str, ...]:
    return tuple(definition.rule_id for definition in _RULE_DEFINITIONS)


def is_known_rule_id(rule_id: str) -> bool:
    return rule_id in _RULE_DEFINITION_BY_ID


__all__ = [
    "RuleDefinition",
    "get_rule_definition",
    "get_rule_definitions",
    "get_rule_ids",
    "is_known_rule_id",
]
