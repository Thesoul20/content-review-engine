from pathlib import Path


def test_rules_doc_exists_and_covers_durable_rule_system_concepts() -> None:
    rules_doc_path = Path("docs/RULES.md")

    assert rules_doc_path.exists()

    content = rules_doc_path.read_text(encoding="utf-8")
    normalized = " ".join(content.split())

    assert "# Rule System" in content
    assert "## What Is A Rule?" in content
    assert "## Rule IDs" in content
    assert "## Current Built-in Rules" in content
    assert "`forbidden_terms`" in content
    assert "`absolute_claims`" in content
    assert "`markdown_structure`" in content
    assert "`markdown_links_images`" in content
    assert "rule_id" in content
    assert "matched_term" in content
    assert "matched_text" in content
    assert "location.start_line" in content
    assert "location.start_column" in content
    assert "location.context" in content
    assert "critical > error > warning > info" in normalized
    assert "info < warning < error < critical" in normalized
    assert "--fail-on critical" in content
    assert "--fail-on error" in content
    assert "--fail-on warning" in content
    assert "--fail-on info" in content
    assert "content-review-disable-line absolute_claims" in content
    assert "content-review-disable-next-line forbidden_terms" in content
    assert "batch summary aggregates" in normalized
    assert "Markdown single-file reports include summary rows" in normalized
    assert "deterministic rules only" in normalized
    assert (
        "legal, medical, advertising, regulatory, or platform compliance"
        in normalized
    )


def test_rule_reference_is_linked_from_user_facing_docs() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    quickstart = Path("docs/QUICKSTART.md").read_text(encoding="utf-8")
    cli_doc = Path("docs/CLI.md").read_text(encoding="utf-8")
    profiles_doc = Path("docs/PROFILES.md").read_text(encoding="utf-8")
    ci_doc = Path("docs/CI.md").read_text(encoding="utf-8")

    assert "docs/RULES.md" in readme
    assert "./RULES.md" in quickstart
    assert "./RULES.md" in cli_doc
    assert "./RULES.md" in profiles_doc
    assert "./RULES.md" in ci_doc
