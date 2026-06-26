from pathlib import Path


def test_current_user_facing_docs_do_not_point_to_review_rules_as_primary_reference() -> None:
    paths = [
        Path("README.md"),
        Path("docs/QUICKSTART.md"),
        Path("docs/CLI.md"),
        Path("docs/PROFILES.md"),
        Path("docs/CI.md"),
    ]

    for path in paths:
        content = path.read_text(encoding="utf-8")
        assert "REVIEW_RULES.md" not in content
        assert "canonical" in content
        assert "RULES.md" in content
