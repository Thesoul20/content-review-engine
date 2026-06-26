from __future__ import annotations

from pathlib import Path

from content_review_engine.config import (
    get_profile_template,
    list_profile_template_names,
    list_profile_templates,
    validate_profile,
)


EXPECTED_NEW_TEMPLATES = {
    "general-publishing": {
        "path": Path("profiles/examples/general-publishing.yaml"),
        "purpose": "common publishing risks, placeholders, and overconfident wording",
    },
    "wechat-article": {
        "path": Path("profiles/examples/wechat-article.yaml"),
        "purpose": "public-facing WeChat article wording, exaggerated claims, and engagement bait",
    },
    "marketing-copy": {
        "path": Path("profiles/examples/marketing-copy.yaml"),
        "purpose": "marketing pressure tactics, guarantee-like wording, and superlatives",
    },
    "technical-blog": {
        "path": Path("profiles/examples/technical-blog.yaml"),
        "purpose": "draft markers, unresolved examples, and absolute technical claims",
    },
    "health-content": {
        "path": Path("profiles/examples/health-content.yaml"),
        "purpose": "cautious health wording, treatment guarantees, and self-diagnosis risks",
    },
}


def test_new_profile_templates_are_listed_and_discoverable() -> None:
    names = list_profile_template_names()

    for template_name in EXPECTED_NEW_TEMPLATES:
        assert template_name in names

    templates = {template.name: template for template in list_profile_templates()}
    for template_name, expected in EXPECTED_NEW_TEMPLATES.items():
        template = templates[template_name]
        assert template.path.name == expected["path"].name
        assert get_profile_template(template_name) == template


def test_new_profile_templates_validate_successfully() -> None:
    for template_name, expected in EXPECTED_NEW_TEMPLATES.items():
        result = validate_profile(expected["path"])
        assert result.valid is True, template_name
        assert result.profile is not None
        assert result.profile.enabled_rule_count >= 3


def test_new_profile_templates_include_practical_regex_rules() -> None:
    templates = {template.name: template for template in list_profile_templates()}

    for template_name in EXPECTED_NEW_TEMPLATES:
        content = templates[template_name].content

        assert "regex_rules:" in content
        assert "message:" in content
        assert "suggestion:" in content
        assert "case_sensitive: false" in content


def test_new_profile_templates_use_conservative_limitation_language() -> None:
    profiles_doc = Path("docs/PROFILES.md").read_text(encoding="utf-8")
    quickstart_doc = Path("docs/QUICKSTART.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")
    cli_doc = Path("docs/CLI.md").read_text(encoding="utf-8")

    for template_name in EXPECTED_NEW_TEMPLATES:
        assert template_name in profiles_doc

    combined = " ".join(
        [
            profiles_doc,
            quickstart_doc,
            readme,
            cli_doc,
        ]
    ).lower()
    normalized = " ".join(combined.split())

    assert "does not provide legal, medical, advertising, regulatory, or platform compliance advice" in normalized
    assert "this ensures compliance" not in normalized
    assert "guarantees compliance" not in normalized
    assert "guaranteed approval" not in normalized
